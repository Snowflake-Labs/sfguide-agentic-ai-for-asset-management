#!/usr/bin/env python3
# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Created by Mats Stellwall, Snowflake, and Snowflake CoCo

"""
Simulated Asset Management (SAM) Demo - Grounded Analyst Recommendations

Derives analyst ratings and price targets from real market and fundamental data
instead of drawing them at random. The chain is:

    fair_value  = forward_eps * sector_base_pe * quality_adjustment
    price_target = fair_value * (1 + broker_bias + vintage_jitter)
    upside       = price_target / close_price - 1
    rating       = band(upside)

Because the rating is a function of the arithmetic rather than an independent
draw, rating, target and upside are always mutually consistent, and a stock that
rallies into its target is downgraded on the next vintage automatically.

Point-in-time correctness: every input is taken as of the requested vintage date
(latest annual filing on or before it, latest close on or before it), so the same
code produces a historically grounded backfill and a forward weekly increment.

Usage:
    Called by the build (historical vintages) and by the weekly refresh.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Union

from snowflake.snowpark import Session

import config
from utils.logging import log_detail, log_substep, log_warning


def _sector_base_pe() -> dict:
    """Midpoint PE_RATIO per GICS sector from numeric_bounds.yaml.

    Sector names are normalised to the DIM_ISSUER spelling - the YAML says
    'Health Care' where DIM_ISSUER says 'Healthcare', which would otherwise
    silently leave 65 issuers without a multiple.
    """
    bounds = config.get_numeric_bounds()
    sector_bounds = bounds.get('security', {}).get('broker_research', {})

    base_pe = {}
    for yaml_sector, placeholders in sector_bounds.items():
        pe = placeholders.get('PE_RATIO')
        if not pe:
            continue
        sector = config.SECTOR_NAME_ALIASES.get(yaml_sector, yaml_sector)
        base_pe[sector] = round((pe['min'] + pe['max']) / 2.0, 2)

    return base_pe


def build_dim_sector_valuation(session: Session) -> None:
    """Build DIM_SECTOR_VALUATION - the sector PE multiples used for fair value."""
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']

    base_pe = _sector_base_pe()
    if not base_pe:
        raise RuntimeError(
            "No PE_RATIO bounds found in numeric_bounds.yaml - cannot build "
            "DIM_SECTOR_VALUATION. Check content_library/_rules/numeric_bounds.yaml."
        )

    rows = [
        {'GICS_SECTOR': sector, 'BasePE': pe, 'DefaultPE': config.VALUATION['default_base_pe']}
        for sector, pe in sorted(base_pe.items())
    ]

    df = session.create_dataframe(rows)
    df.write.mode("overwrite").save_as_table(
        f"{database_name}.{curated_schema}.DIM_SECTOR_VALUATION"
    )
    log_detail(f" DIM_SECTOR_VALUATION: {len(rows)} sectors")

    # Any sector present in DIM_ISSUER but missing a multiple falls back to
    # default_base_pe in the join. Warn so the gap is visible rather than silent.
    unmatched = session.sql(f"""
        SELECT i.GICS_SECTOR, COUNT(*) AS issuers
        FROM {database_name}.{curated_schema}.DIM_ISSUER i
        LEFT JOIN {database_name}.{curated_schema}.DIM_SECTOR_VALUATION v
            ON v.GICS_SECTOR = i.GICS_SECTOR
        WHERE v.GICS_SECTOR IS NULL AND i.GICS_SECTOR IS NOT NULL
        GROUP BY 1
    """).collect()
    for row in unmatched:
        log_warning(
            f"Sector '{row['GICS_SECTOR']}' ({row['ISSUERS']} issuers) has no PE_RATIO "
            f"in numeric_bounds.yaml - using default PE "
            f"{config.VALUATION['default_base_pe']}"
        )


def build_dim_broker_bias(session: Session) -> None:
    """Build DIM_BROKER_BIAS - the persistent per-broker valuation tilt."""
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']

    rows = [
        {
            'BrokerName': broker_name,
            'BiasPct': config.BROKER_BIAS_PCT.get(broker_name, 0.0),
            'JitterHalfWidthPct': config.VALUATION['broker_jitter_pct'],
        }
        for broker_name in config.BROKER_NAMES
    ]

    df = session.create_dataframe(rows)
    df.write.mode("overwrite").save_as_table(
        f"{database_name}.{curated_schema}.DIM_BROKER_BIAS"
    )

    missing = [b for b in config.BROKER_NAMES if b not in config.BROKER_BIAS_PCT]
    if missing:
        log_warning(
            f"{len(missing)} broker(s) have no BROKER_BIAS_PCT entry and default to "
            f"0.0 tilt: {', '.join(missing)}"
        )
    log_detail(f" DIM_BROKER_BIAS: {len(rows)} brokers")


def _rating_case_sql(upside_expr: str) -> str:
    """Render the rating band CASE expression from config.RATING_UPSIDE_BANDS."""
    whens = '\n'.join(
        f"                WHEN {upside_expr} > {threshold} THEN '{rating}'"
        for rating, threshold in config.RATING_UPSIDE_BANDS
    )
    most_bearish = config.RATING_SCALE[-1]
    return f"            CASE\n{whens}\n                ELSE '{most_bearish}'\n            END"


# Columns written by build_fact_recommendation. apply_rating_actions derives
# PriorRating, PriorPriceTarget and RatingAction on top of these, so it must
# select this list explicitly rather than `*` - otherwise a second run finds the
# derived columns already present and the LAG collides with them.
_BASE_COLUMNS = [
    'RecommendationID', 'VintageDate', 'IssuerID', 'SecurityID', 'Ticker',
    'CompanyName', 'GICS_SECTOR', 'BrokerName', 'LeadAnalystID', 'ClosePrice',
    'TrailingEPS', 'ForwardEPS', 'BasePE', 'ValuationBasis', 'QualityAdj',
    'FairValue', 'RawSignalPct', 'CalibratedSignalPct',
    'ValuationSignalPct', 'BrokerBiasPct',
    'JitterPct', 'PriceTarget', 'UpsidePct', 'Rating', 'FundamentalsAsOf',
    'DriverSummary', 'GeneratedAt',
]


def build_fact_recommendation(
    session: Session,
    vintage_date: Union[str, date],
    append: bool = False,
) -> int:
    """Build (or append to) FACT_RECOMMENDATION for a single vintage date.

    Args:
        session: Snowpark session.
        vintage_date: The as-of date. All inputs are taken point-in-time on or
            before this date, so historical vintages are genuinely historical.
        append: When False the table is replaced. When True the vintage is
            merged in, which is what the weekly refresh and a multi-vintage
            backfill need.

    Returns:
        Number of rows written for this vintage.
    """
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    market_data_schema = config.DATABASE['schemas']['market_data']

    vintage = vintage_date.isoformat() if isinstance(vintage_date, date) else vintage_date

    valuation = config.VALUATION
    default_pe = valuation['default_base_pe']
    q_min, q_max = valuation['quality_adj_min'], valuation['quality_adj_max']
    growth_w, margin_w = valuation['growth_weight'], valuation['margin_weight']
    eps_g_min, eps_g_max = valuation['eps_growth_min'], valuation['eps_growth_max']
    signal_scale = valuation['valuation_signal_scale']
    signal_softness = valuation['valuation_signal_softness']
    growth_cap = valuation['revenue_growth_cap_pct']
    margin_cap = valuation['operating_margin_cap_pct']
    unprofitable_discount = valuation['unprofitable_discount']
    min_ps = valuation['min_price_to_sales']
    fv_ratio_min = valuation['fv_ratio_min']
    fv_ratio_max = valuation['fv_ratio_max']
    jitter = valuation['broker_jitter_pct']
    fb_lookback = valuation['price_fallback_lookback_days']
    fb_weight = valuation['price_fallback_momentum_weight']
    fb_mom_min = valuation['price_fallback_momentum_min']
    fb_mom_max = valuation['price_fallback_momentum_max']
    jitter_span = int(round(jitter * 2 * 10000))

    fqn = f"{database_name}.{curated_schema}.FACT_RECOMMENDATION"

    # Latest annual filing on or before the vintage. PERIOD_TYPE='annual' with
    # COVERED_QTRS=4 is the only clean full-year series in FACT_SEC_FINANCIALS;
    # the cumulative_ytd and quarterly rows would double count.
    select_sql = f"""
        -- Share count carried across period types. 41 of 503 covered issuers
        -- report annual revenue but leave SHARES_OUTSTANDING null on the annual
        -- row, which blocked both the derived_eps and sales_multiple tiers and
        -- dropped them entirely. 22 of them do report a share count on some
        -- other period, and share count moves slowly, so the most recent
        -- positive value at or before the vintage is a sound substitute.
        WITH mixed_currency_issuers AS (
            SELECT DISTINCT sf.IssuerID
            FROM {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS sf
            WHERE sf.PERIOD_TYPE = 'annual'
              AND sf.COVERED_QTRS = 4
              AND sf.REVENUE > 0
              AND sf.NET_INCOME > sf.REVENUE
        ),
        shares_fallback AS (
            SELECT IssuerID, SHARES_OUTSTANDING AS FallbackShares
            FROM (
                SELECT sf.IssuerID, sf.SHARES_OUTSTANDING,
                       ROW_NUMBER() OVER (
                           PARTITION BY sf.IssuerID
                           ORDER BY sf.PERIOD_END_DATE DESC
                       ) AS rn
                FROM {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS sf
                WHERE sf.SHARES_OUTSTANDING > 0
                  AND sf.PERIOD_END_DATE <= '{vintage}'::DATE
            )
            WHERE rn = 1
        ),
        annual AS (
            SELECT
                sf.IssuerID,
                sf.EPS_DILUTED,
                sf.NET_INCOME,
                sf.SHARES_OUTSTANDING,
                COALESCE(sf.SHARES_OUTSTANDING, shf.FallbackShares) AS EffectiveShares,
                sf.REVENUE,
                sf.OPERATING_MARGIN_PCT,
                sf.PERIOD_END_DATE,
                -- FACT_SEC_FINANCIALS.REVENUE_GROWTH_PCT is not trustworthy:
                -- median 82.8% and max 273,736% across the annual series, with
                -- ~48% of rows implausible, which suggests mismatched period
                -- comparisons upstream. Derive year-on-year growth from
                -- consecutive annual REVENUE instead, which is reliable and
                -- genuinely point-in-time.
                LAG(sf.REVENUE) OVER (
                    PARTITION BY sf.IssuerID ORDER BY sf.PERIOD_END_DATE
                ) AS PriorRevenue,
                ROW_NUMBER() OVER (
                    PARTITION BY sf.IssuerID
                    ORDER BY sf.PERIOD_END_DATE DESC
                ) AS rn
            FROM {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS sf
            LEFT JOIN shares_fallback shf ON shf.IssuerID = sf.IssuerID
            WHERE sf.PERIOD_TYPE = 'annual'
              AND sf.COVERED_QTRS = 4
              AND sf.PERIOD_END_DATE <= '{vintage}'::DATE
              -- Exclude issuers whose filings are not denominated consistently
              -- with their listing. Net income above revenue is impossible for an
              -- operating company, so it marks the issuer's series as mis-tagged
              -- or reported in a different currency - TSMC files TWD against a
              -- USD quote, giving an EPS ~32x too high and a confident but
              -- meaningless rating.
              --
              -- This has to be an issuer-level exclusion, not a row-level one.
              -- Filtering only the offending rows leaves TSMC rated off the two
              -- years where the TWD revenue happened to exceed TWD net income,
              -- which are just as mis-denominated. The fair-value ratio gate does
              -- not catch it either: TSMC lands at 5x, inside the legitimate
              -- range where the 99th percentile is 18.6x.
              AND sf.IssuerID NOT IN (SELECT IssuerID FROM mixed_currency_issuers)
        ),
        -- Sector median net margin from real filings, used to turn the sector PE
        -- into an implied price/sales for loss-making companies.
        sector_margin AS (
            SELECT i.GICS_SECTOR,
                   MEDIAN(sf.NET_MARGIN_PCT) AS MedianNetMarginPct
            FROM {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS sf
            JOIN {database_name}.{curated_schema}.DIM_ISSUER i
                ON i.IssuerID = sf.IssuerID
            WHERE sf.PERIOD_TYPE = 'annual'
              AND sf.COVERED_QTRS = 4
              AND sf.NET_MARGIN_PCT IS NOT NULL
              AND sf.PERIOD_END_DATE <= '{vintage}'::DATE
            GROUP BY i.GICS_SECTOR
        ),
        fundamentals AS (
            SELECT
                a.IssuerID,
                a.PERIOD_END_DATE,
                a.rn,
                a.REVENUE,
                a.SHARES_OUTSTANDING,
                a.OPERATING_MARGIN_PCT,
                -- Coverage tiers: reported EPS, then EPS derived from net income
                -- and share count, then a sales multiple for loss-makers. Without
                -- the fallbacks, 139 of 503 covered issuers get no rating at all.
                CASE
                    WHEN a.EPS_DILUTED > 0 THEN a.EPS_DILUTED
                    WHEN a.NET_INCOME > 0 AND a.EffectiveShares > 0
                        THEN a.NET_INCOME / a.EffectiveShares
                    ELSE NULL
                END AS EffectiveEPS,
                CASE
                    WHEN a.EPS_DILUTED > 0 THEN 'reported_eps'
                    WHEN a.NET_INCOME > 0 AND a.EffectiveShares > 0 THEN 'derived_eps'
                    WHEN a.REVENUE > 0 AND a.EffectiveShares > 0 THEN 'sales_multiple'
                    ELSE NULL
                END AS ValuationBasis,
                CASE
                    WHEN a.REVENUE > 0 AND a.EffectiveShares > 0
                        THEN a.REVENUE / a.EffectiveShares
                    ELSE NULL
                END AS RevenuePerShare,
                -- Clamped to a plausible corporate range so a restatement or a
                -- tiny prior-year base cannot distort the valuation or appear in
                -- document text.
                LEAST({growth_cap}, GREATEST(-{growth_cap},
                    CASE
                        WHEN a.PriorRevenue IS NULL OR a.PriorRevenue <= 0 THEN NULL
                        ELSE ((a.REVENUE / a.PriorRevenue) - 1) * 100
                    END
                )) AS REVENUE_GROWTH_PCT
            FROM annual a
        ),
        -- Latest close on or before the vintage, so a non-trading vintage date
        -- still resolves to a real price.
        prices AS (
            SELECT
                p.SecurityID,
                p.PRICE_CLOSE,
                ROW_NUMBER() OVER (
                    PARTITION BY p.SecurityID
                    ORDER BY p.PRICE_DATE DESC
                ) AS rn
            FROM {database_name}.{market_data_schema}.FACT_STOCK_PRICES p
            WHERE p.PRICE_DATE <= '{vintage}'::DATE
              AND p.PRICE_CLOSE > 0
        ),
        fair_value AS (
            SELECT
                f.IssuerID,
                s.SecurityID,
                s.Ticker,
                i.LegalName,
                i.GICS_SECTOR,
                pr.PRICE_CLOSE AS ClosePrice,
                COALESCE(v.BasePE, {default_pe}) AS BasePE,
                f.EffectiveEPS AS TrailingEPS,
                f.ValuationBasis,
                f.RevenuePerShare,
                -- Implied price/sales for the sales_multiple tier: the sector PE
                -- applied to the sector's real median net margin, floored so a
                -- sector with ~zero median margin cannot value a name at zero.
                GREATEST(
                    COALESCE(v.BasePE, {default_pe})
                        * COALESCE(sm.MedianNetMarginPct, 0) / 100.0,
                    {min_ps}
                ) AS ImpliedPS,
                f.REVENUE_GROWTH_PCT,
                LEAST({margin_cap}, GREATEST(-{margin_cap},
                    f.OPERATING_MARGIN_PCT
                )) AS OPERATING_MARGIN_PCT,
                f.PERIOD_END_DATE AS FundamentalsAsOf,
                -- Forward growth from real revenue growth, clamped so one
                -- distorted filing cannot produce an absurd target.
                LEAST({eps_g_max}, GREATEST({eps_g_min},
                    1.0 + COALESCE(f.REVENUE_GROWTH_PCT, 0) / 100.0
                )) AS EPSGrowthFactor,
                -- Quality adjustment from real growth and margin.
                LEAST({q_max}, GREATEST({q_min},
                    1.0 + COALESCE(f.REVENUE_GROWTH_PCT, 0) / 100.0 * {growth_w}
                        + COALESCE(LEAST({margin_cap}, GREATEST(-{margin_cap},
                              f.OPERATING_MARGIN_PCT)), 0) / 100.0 * {margin_w}
                )) AS QualityAdj
            FROM fundamentals f
            JOIN {database_name}.{curated_schema}.DIM_SECURITY s
                ON s.IssuerID = f.IssuerID AND s.AssetClass = 'Equity'
            JOIN {database_name}.{curated_schema}.DIM_ISSUER i
                ON i.IssuerID = f.IssuerID
            JOIN prices pr
                ON pr.SecurityID = s.SecurityID AND pr.rn = 1
            LEFT JOIN {database_name}.{curated_schema}.DIM_SECTOR_VALUATION v
                ON v.GICS_SECTOR = i.GICS_SECTOR
            LEFT JOIN sector_margin sm
                ON sm.GICS_SECTOR = i.GICS_SECTOR
            WHERE f.rn = 1
              AND f.ValuationBasis IS NOT NULL
        ),
        valued AS (
            SELECT
                fv.*,
                fv.TrailingEPS * fv.EPSGrowthFactor AS ForwardEPS,
                CASE
                    WHEN fv.ValuationBasis = 'sales_multiple'
                        -- Loss-making: valued on forward sales at the implied
                        -- multiple, with a haircut because the sector median
                        -- margin assumes profitability they have not reached.
                        THEN fv.RevenuePerShare * fv.EPSGrowthFactor * fv.ImpliedPS
                             * fv.QualityAdj * {unprofitable_discount}
                    ELSE fv.TrailingEPS * fv.EPSGrowthFactor * fv.BasePE * fv.QualityAdj
                END AS FairValue
            FROM fair_value fv
        ),
        -- Plausibility gate. A fair value hundreds of times spot means the
        -- filing and the price are not on the same basis - typically a foreign
        -- private issuer reporting in its local currency against a USD listing
        -- (TSMC reports TWD and shows net income above revenue). Because the
        -- fundamental view is compressed through TANH, such a name would not
        -- produce an absurd target, it would silently peg at maximum bullish or
        -- bearish - a confident rating derived from meaningless input, which is
        -- worse than no rating. Excluding them is the honest outcome.
        plausible AS (
            SELECT v.*
            FROM valued v
            WHERE v.FairValue IS NOT NULL
              AND v.ClosePrice > 0
              AND v.FairValue / v.ClosePrice BETWEEN {fv_ratio_min} AND {fv_ratio_max}
        ),
        raw_signal AS (
            SELECT
                v.*,
                -- Raw fundamental over/undervaluation versus spot.
                (v.FairValue / v.ClosePrice) - 1 AS RawSignalPct
            FROM plausible v
        ),
        calibrated AS (
            SELECT
                rs.*,
                -- Each valuation basis carries its own systematic bias: measured
                -- per vintage, the median raw signal is about -0.05 for
                -- reported_eps but -0.80 for derived_eps and sales_multiple,
                -- because an earnings-style multiple structurally undervalues
                -- marginally profitable and loss-making companies that the market
                -- prices on future growth. Left uncorrected those tiers came out
                -- ~60% Sell, which is not how analysts cover such names.
                --
                -- So each basis is re-centred on the well-calibrated reported_eps
                -- tier. This removes the bias *between* methodologies while fully
                -- preserving the cross-sectional ordering *within* each, so a
                -- cheap loss-maker still ranks above an expensive one. Medians are
                -- per vintage, so every vintage self-calibrates.
                rs.RawSignalPct
                    - MEDIAN(rs.RawSignalPct) OVER (PARTITION BY rs.ValuationBasis)
                    + COALESCE(MEDIAN(
                          CASE WHEN rs.ValuationBasis = 'reported_eps'
                               THEN rs.RawSignalPct END
                      ) OVER (), 0) AS CalibratedSignalPct
            FROM raw_signal rs
        ),
        -- Price fallback for securities that have a price but no usable
        -- fundamentals: no clean annual filing (GS, CMC), a mixed-currency
        -- series (TSMC), or a fair value outside the plausibility gate. Without
        -- it those names carry no rating at all. The signal is the sector's
        -- median calibrated view plus damped trailing price momentum, the drift
        -- a sell-side desk applies to a name it cannot model. It is already
        -- on the calibrated scale, so it is not re-centred again, and
        -- ValuationBasis = 'price_fallback' flags it in every downstream row.
        momentum_base AS (
            SELECT
                p.SecurityID,
                p.PRICE_CLOSE AS PriorClose,
                ROW_NUMBER() OVER (
                    PARTITION BY p.SecurityID
                    ORDER BY p.PRICE_DATE DESC
                ) AS rn
            FROM {database_name}.{market_data_schema}.FACT_STOCK_PRICES p
            WHERE p.PRICE_DATE <= DATEADD(DAY, -{fb_lookback}, '{vintage}'::DATE)
              AND p.PRICE_CLOSE > 0
        ),
        sector_signal AS (
            SELECT GICS_SECTOR, MEDIAN(CalibratedSignalPct) AS SectorSignalPct
            FROM calibrated
            GROUP BY GICS_SECTOR
        ),
        fallback AS (
            SELECT
                s.IssuerID,
                s.SecurityID,
                s.Ticker,
                i.LegalName,
                i.GICS_SECTOR,
                pr.PRICE_CLOSE AS ClosePrice,
                COALESCE(v.BasePE, {default_pe}) AS BasePE,
                LEAST({fb_mom_max}, GREATEST({fb_mom_min},
                    COALESCE(pr.PRICE_CLOSE / NULLIF(mb.PriorClose, 0) - 1, 0)
                )) AS MomentumPct,
                COALESCE(ss.SectorSignalPct,
                         (SELECT MEDIAN(CalibratedSignalPct) FROM calibrated), 0)
                    AS SectorSignalPct
            FROM {database_name}.{curated_schema}.DIM_SECURITY s
            JOIN {database_name}.{curated_schema}.DIM_ISSUER i
                ON i.IssuerID = s.IssuerID
            JOIN prices pr
                ON pr.SecurityID = s.SecurityID AND pr.rn = 1
            LEFT JOIN momentum_base mb
                ON mb.SecurityID = s.SecurityID AND mb.rn = 1
            LEFT JOIN {database_name}.{curated_schema}.DIM_SECTOR_VALUATION v
                ON v.GICS_SECTOR = i.GICS_SECTOR
            LEFT JOIN sector_signal ss
                ON ss.GICS_SECTOR = i.GICS_SECTOR
            WHERE s.AssetClass = 'Equity'
              AND s.SecurityID NOT IN (SELECT SecurityID FROM calibrated)
        ),
        calibrated_all AS (
            SELECT IssuerID, SecurityID, Ticker, LegalName, GICS_SECTOR, ClosePrice,
                   BasePE, TrailingEPS, ValuationBasis, ImpliedPS, REVENUE_GROWTH_PCT,
                   OPERATING_MARGIN_PCT, FundamentalsAsOf, QualityAdj, ForwardEPS,
                   FairValue, RawSignalPct, CalibratedSignalPct,
                   NULL::FLOAT AS MomentumPct
            FROM calibrated
            UNION ALL
            SELECT IssuerID, SecurityID, Ticker, LegalName, GICS_SECTOR, ClosePrice,
                   BasePE, NULL, 'price_fallback', NULL, NULL,
                   NULL, NULL, 1.0, NULL,
                   ClosePrice * (1 + SectorSignalPct + {fb_weight} * MomentumPct),
                   SectorSignalPct + {fb_weight} * MomentumPct,
                   SectorSignalPct + {fb_weight} * MomentumPct,
                   MomentumPct
            FROM fallback
        ),
        signalled AS (
            SELECT
                c.*,
                -- Smoothly compressed into the range real analyst targets
                -- occupy. TANH is monotonic, so ordering is fully preserved and
                -- no name plateaus at a cap.
                {signal_scale} * TANH(c.CalibratedSignalPct / {signal_softness})
                    AS ValuationSignalPct
            FROM calibrated_all c
        ),
        -- A broker publishes one house view per stock, but
        -- FACT_ANALYST_COVERAGE is keyed per analyst and a broker can have
        -- several analysts covering the same issuer. Collapse to one lead
        -- analyst per broker/issuer, otherwise RecommendationID collides.
        broker_coverage AS (
            SELECT IssuerID, BROKER_ID, ANALYST_ID
            FROM (
                SELECT ac.IssuerID, ac.BROKER_ID, ac.ANALYST_ID,
                       ROW_NUMBER() OVER (
                           PARTITION BY ac.IssuerID, ac.BROKER_ID
                           ORDER BY ac.ANALYST_ID
                       ) AS rn
                FROM {database_name}.{market_data_schema}.FACT_ANALYST_COVERAGE ac
                WHERE ac.IS_ACTIVE = TRUE
            )
            WHERE rn = 1
        ),
        targets AS (
            SELECT
                s.*,
                b.BrokerName,
                bc.ANALYST_ID AS LeadAnalystID,
                b.BiasPct,
                -- Seeded on broker, ticker and the vintage *month*, not the exact
                -- vintage. A broker's idiosyncratic view should drift slowly, not
                -- re-roll weekly: reseeding every vintage added +-6% of random
                -- churn on top of price moves and drove ratings to oscillate.
                -- Monthly seeding means within a month only real price action
                -- moves the target, while across months the view still drifts.
                (MOD(ABS(HASH(b.BrokerName || '|' || s.Ticker || '|'
                             || TO_VARCHAR('{vintage}'::DATE, 'YYYY-MM'))),
                     {jitter_span}) / 10000.0) - {jitter} AS JitterPct
            FROM signalled s
            JOIN broker_coverage bc
                ON bc.IssuerID = s.IssuerID
            JOIN {database_name}.{market_data_schema}.DIM_BROKER br
                ON br.BROKER_ID = bc.BROKER_ID
            JOIN {database_name}.{curated_schema}.DIM_BROKER_BIAS b
                ON b.BrokerName = br.BROKER_NAME
        ),
        priced AS (
            SELECT
                t.*,
                ROUND(GREATEST(
                    t.ClosePrice * (1 + t.ValuationSignalPct + t.BiasPct + t.JitterPct),
                    0.01
                ), 2) AS PriceTarget
            FROM targets t
        ),
        with_upside AS (
            SELECT p.*, (p.PriceTarget / p.ClosePrice) - 1 AS UpsidePct
            FROM priced p
        )
        SELECT
            MD5(w.Ticker || '|' || w.BrokerName || '|' || '{vintage}') AS RecommendationID,
            '{vintage}'::DATE AS VintageDate,
            w.IssuerID,
            w.SecurityID,
            w.Ticker,
            w.LegalName AS CompanyName,
            w.GICS_SECTOR,
            w.BrokerName,
            w.LeadAnalystID,
            w.ClosePrice,
            w.TrailingEPS,
            w.ForwardEPS,
            w.BasePE,
            w.ValuationBasis,
            w.QualityAdj,
            w.FairValue,
            w.RawSignalPct,
            w.CalibratedSignalPct,
            w.ValuationSignalPct,
            w.BiasPct AS BrokerBiasPct,
            w.JitterPct,
            w.PriceTarget,
            w.UpsidePct,
{_rating_case_sql('w.UpsidePct')} AS Rating,
            w.FundamentalsAsOf,
            -- Human-readable driver chain for {{{{VALUATION_DRIVERS}}}} in templates.
            -- Loss-making names are described on a sales multiple, so the text
            -- never quotes an earnings multiple for a company with no earnings.
            CASE
                WHEN w.ValuationBasis = 'price_fallback'
                    THEN 'no usable reported fundamentals, price-based view: '
                         || ROUND(w.MomentumPct * 100, 1) || '% trailing price momentum'
                         || ', sector PE ' || ROUND(w.BasePE, 1) || 'x'
                         || ', fair value $' || ROUND(w.FairValue, 2)
                ELSE
            'revenue growth ' || ROUND(COALESCE(w.REVENUE_GROWTH_PCT, 0), 1) || '%'
                || ', operating margin ' || ROUND(COALESCE(w.OPERATING_MARGIN_PCT, 0), 1) || '%'
                || CASE
                       WHEN w.ValuationBasis = 'sales_multiple'
                           THEN ', not yet profitable, valued on '
                                || ROUND(w.ImpliedPS, 1) || 'x sales'
                       ELSE ', sector PE ' || ROUND(w.BasePE, 1) || 'x'
                   END
                || ', fair value $' || ROUND(w.FairValue, 2)
            END AS DriverSummary,
            CURRENT_TIMESTAMP() AS GeneratedAt
        FROM with_upside w
    """

    if append:
        # Column lists are generated from _BASE_COLUMNS so adding a column to the
        # SELECT can never silently drift out of sync with the MERGE.
        insert_cols = ', '.join(_BASE_COLUMNS)
        insert_vals = ', '.join(f"src.{c}" for c in _BASE_COLUMNS)
        session.sql(f"""
            MERGE INTO {fqn} tgt
            USING ({select_sql}) src
            ON tgt.RecommendationID = src.RecommendationID
            WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
        """).collect()
    else:
        session.sql(f"CREATE OR REPLACE TABLE {fqn} AS {select_sql}").collect()

    written = session.sql(
        f"SELECT COUNT(*) AS cnt FROM {fqn} WHERE VintageDate = '{vintage}'::DATE"
    ).collect()[0]['CNT']
    log_detail(f" FACT_RECOMMENDATION @ {vintage}: {written} broker/security recommendations")
    return written


def apply_rating_actions(session: Session) -> None:
    """Populate PriorRating and RatingAction by comparing consecutive vintages.

    Run after all vintages exist. A broker's previous rating on the same ticker
    is whatever it published at its own previous vintage, which is what lets a
    note open with "we downgrade to Buy from Strong Buy".
    """
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    fqn = f"{database_name}.{curated_schema}.FACT_RECOMMENDATION"

    rank_case = '\n'.join(
        f"        WHEN '{rating}' THEN {idx}"
        for idx, rating in enumerate(config.RATING_SCALE)
    )
    base_cols = ',\n                   '.join(f"r.{c}" for c in _BASE_COLUMNS)
    ranked_cols = ',\n               '.join(_BASE_COLUMNS)

    session.sql(f"""
        CREATE OR REPLACE TABLE {fqn} AS
        WITH ranked AS (
            SELECT {base_cols},
                   LAG(r.Rating) OVER (
                       PARTITION BY r.Ticker, r.BrokerName ORDER BY r.VintageDate
                   ) AS PriorRating,
                   LAG(r.PriceTarget) OVER (
                       PARTITION BY r.Ticker, r.BrokerName ORDER BY r.VintageDate
                   ) AS PriorPriceTarget
            FROM {fqn} r
        )
        SELECT {ranked_cols},
               PriorRating,
               PriorPriceTarget,
               CASE
                   WHEN PriorRating IS NULL THEN 'initiate'
                   WHEN PriorRating = Rating THEN 'reiterate'
                   -- Lower index is more bullish, so a smaller index is an upgrade.
                   WHEN CASE Rating
{rank_case}
                        END
                      < CASE PriorRating
{rank_case}
                        END
                       THEN 'upgrade'
                   ELSE 'downgrade'
               END AS RatingAction
        FROM ranked
    """).collect()

    summary = session.sql(f"""
        SELECT RatingAction, COUNT(*) AS n
        FROM {fqn} GROUP BY 1 ORDER BY n DESC
    """).collect()
    detail = ', '.join(f"{row['RATINGACTION']}={row['N']}" for row in summary)
    log_detail(f" Rating actions: {detail}")


def build_vintage_history(
    session: Session,
    anchor_date: Union[str, date],
    monthly_months: int = 24,
    weekly_weeks: int = 13,
) -> int:
    """Backfill FACT_RECOMMENDATION across history, then recent weeks.

    Documents are dated across roughly 8 months of history (broker research is
    aligned to fiscal periods, engagement notes span 180 days), and each one
    resolves its rating as-of its own publish date. With only a few recent
    vintages every older document would fall back to the oldest available view,
    so the history has to be wide enough to cover them.

    Monthly vintages give that breadth cheaply; weekly vintages over the recent
    period give the fine-grained recency the weekly refresh then extends. Both
    use the same point-in-time SQL, which is what lets the initial build double
    as the historical backfill.

    Returns the total number of rows written.
    """
    anchor = (
        datetime.strptime(anchor_date, '%Y-%m-%d').date()
        if isinstance(anchor_date, str) else anchor_date
    )

    vintages = set()
    for m in range(monthly_months, 0, -1):
        # Approximate month steps; exact calendar alignment is not needed because
        # resolution is "newest vintage on or before the document date".
        vintages.add(anchor - timedelta(days=30 * m))
    for w in range(weekly_weeks, -1, -1):
        vintages.add(anchor - timedelta(weeks=w))

    ordered = sorted(vintages)
    log_substep(
        f"Backfilling FACT_RECOMMENDATION across {len(ordered)} vintages "
        f"({ordered[0]} to {ordered[-1]})..."
    )

    build_dim_sector_valuation(session)
    build_dim_broker_bias(session)

    total = 0
    for idx, vintage in enumerate(ordered):
        total += build_fact_recommendation(session, vintage, append=(idx > 0))
    apply_rating_actions(session)

    log_detail(f" FACT_RECOMMENDATION: {total} rows across {len(ordered)} vintages")
    return total


def ensure_vintage(session: Session, vintage_date: Union[str, date]) -> int:
    """Ensure the valuation dimensions and one vintage of FACT_RECOMMENDATION exist.

    Safe to call repeatedly and safe to call when earlier vintages have already
    been backfilled: the vintage is merged rather than replacing the table, so a
    rebuild of downstream estimates never destroys rating history.
    """
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']

    build_dim_sector_valuation(session)
    build_dim_broker_bias(session)

    exists = session.sql(f"""
        SELECT COUNT(*) AS cnt
        FROM {database_name}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{curated_schema}' AND TABLE_NAME = 'FACT_RECOMMENDATION'
    """).collect()[0]['CNT']

    written = build_fact_recommendation(session, vintage_date, append=bool(exists))
    apply_rating_actions(session)
    return written


def build_all(session: Session, vintage_date: Union[str, date]) -> None:
    """Build the valuation dimensions and backfill FACT_RECOMMENDATION history.

    The backfill is not optional extra data: documents resolve their rating
    as-of their own publish date, so without history every older note would
    quote today's view. build_vintage_history covers the document date range.
    """
    log_substep("Building grounded recommendation tables...")
    build_vintage_history(session, vintage_date)
