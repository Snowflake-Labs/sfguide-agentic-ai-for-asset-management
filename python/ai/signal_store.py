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
Signal Store — FACT_SIGNALS table and extraction pipeline.

Three extraction tiers:
- Tier 1: Pure SQL (deterministic, fast, free)
- Tier 2: AI_COMPLETE with structured output (LLM cost per row)
- Tier 3: Agent enrichment via DATA_AGENT_RUN (highest quality)
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_phase, log_step, log_substep, log_detail, log_success, log_warning, log_error


def create_fact_signals(session: Session):
    database_name = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {database_name}.{curated}.FACT_SIGNALS (
        SIGNAL_ID              BIGINT AUTOINCREMENT START 1 INCREMENT 1,
        CREATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
        UPDATED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
        SOURCE_TYPE            VARCHAR(50) NOT NULL,
        SOURCE_TABLE           VARCHAR(200),
        SOURCE_ID              VARCHAR(200),
        ENTITY_TYPE            VARCHAR(50),
        ENTITY_ID              BIGINT,
        ENTITY_NAME            VARCHAR(255),
        PORTFOLIO_IDS          ARRAY,
        PORTFOLIO_NAMES        ARRAY,
        EXPOSED_AUM_USD        FLOAT DEFAULT 0,
        SIGNAL_TYPE            VARCHAR(50) NOT NULL,
        HEADLINE               VARCHAR(500) NOT NULL,
        DETAIL                 VARCHAR(10000),
        EVIDENCE               VARCHAR(5000),
        SUGGESTED_ACTIONS      ARRAY,
        SOURCE_CHAIN           VARCHAR(1000),
        URGENCY                VARCHAR(20) NOT NULL,
        CONFIDENCE             FLOAT,
        IMPACT_ESTIMATE_BPS    FLOAT,
        NOVELTY_SCORE          FLOAT,
        STATUS                 VARCHAR(20) DEFAULT 'new',
        VIEWED_AT              TIMESTAMP_NTZ,
        ACTION_TAKEN           VARCHAR(500),
        PARENT_SIGNAL_ID       BIGINT,
        RELATED_SIGNALS        ARRAY,
        EXTRACTION_TIER        VARCHAR(10),
        PROCESSING_TIME_MS     BIGINT,
        PRIMARY KEY (SIGNAL_ID)
    )
    COMMENT = 'AI-detected portfolio signals with urgency scoring, impact estimates, and provenance'
    """).collect()

    # Ensure EXPOSED_AUM_USD column exists (handles tables created before this column was added)
    try:
        session.sql(f"ALTER TABLE {database_name}.{curated}.FACT_SIGNALS ADD COLUMN IF NOT EXISTS EXPOSED_AUM_USD FLOAT DEFAULT 0").collect()
    except Exception:
        pass  # Column already exists

    log_detail("  FACT_SIGNALS table ensured")


def truncate_signals(session: Session):
    database_name = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    session.sql(f"TRUNCATE TABLE IF EXISTS {database_name}.{curated}.FACT_SIGNALS").collect()


def enrich_signals_with_exposure(session: Session):
    """Post-extraction: populate PORTFOLIO_IDS, PORTFOLIO_NAMES, EXPOSED_AUM_USD
    for all security-level signals that don't already have portfolio linkage."""
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    table = f"{db}.{c}.FACT_SIGNALS"

    session.sql(f"""
        UPDATE {table} s
        SET PORTFOLIO_IDS = p.PIDS,
            PORTFOLIO_NAMES = p.PNAMES,
            EXPOSED_AUM_USD = p.TOTAL_EXPOSURE
        FROM (
            SELECT sig.SIGNAL_ID,
                   ARRAY_AGG(DISTINCT pos.PortfolioID) AS PIDS,
                   ARRAY_AGG(DISTINCT dp.PortfolioName) AS PNAMES,
                   SUM(pos.MarketValue_Base) AS TOTAL_EXPOSURE
            FROM {table} sig
            JOIN {db}.{c}.DIM_SECURITY ds ON sig.ENTITY_ID = ds.SecurityID
            JOIN {db}.{c}.FACT_POSITION_DAILY_ABOR pos
                 ON ds.SecurityID = pos.SecurityID
                 AND pos.HoldingDate = (SELECT MAX(HoldingDate) FROM {db}.{c}.FACT_POSITION_DAILY_ABOR)
            JOIN {db}.{c}.DIM_PORTFOLIO dp ON pos.PortfolioID = dp.PortfolioID
            WHERE sig.PORTFOLIO_IDS IS NULL
              AND sig.ENTITY_TYPE = 'SECURITY'
              AND sig.ENTITY_ID IS NOT NULL
            GROUP BY sig.SIGNAL_ID
        ) p
        WHERE s.SIGNAL_ID = p.SIGNAL_ID
    """).collect()

    enriched = session.sql(f"""
        SELECT COUNT(*) AS CNT FROM {table} WHERE EXPOSED_AUM_USD > 0
    """).collect()[0]['CNT']
    log_detail(f"  Enriched {enriched} signals with portfolio exposure data")


def _insert_signals(session: Session, sql: str, label: str) -> int:
    database_name = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    table = f"{database_name}.{curated}.FACT_SIGNALS"
    session.sql(sql).collect()
    count = session.sql(f"""
        SELECT COUNT(*) AS CNT FROM {table}
        WHERE SOURCE_TYPE = '{label}' AND CREATED_AT > DATEADD('minute', -5, CURRENT_TIMESTAMP())
    """).collect()[0]['CNT']
    return count


# ---------------------------------------------------------------------------
# TIER 1: Pure SQL extractors
# ---------------------------------------------------------------------------

def extract_price_drops(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    md = config.DATABASE['schemas']['market_data']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_ID, ENTITY_NAME,
         PORTFOLIO_IDS, PORTFOLIO_NAMES, SIGNAL_TYPE, HEADLINE, DETAIL,
         URGENCY, CONFIDENCE, IMPACT_ESTIMATE_BPS, EXTRACTION_TIER)
    WITH latest_prices AS (
        SELECT SecurityID, PRICE_DATE, PRICE_CLOSE,
            LAG(PRICE_CLOSE) OVER (PARTITION BY SecurityID ORDER BY PRICE_DATE) AS PREV_CLOSE
        FROM {db}.{md}.FACT_STOCK_PRICES
        QUALIFY PRICE_DATE >= DATEADD('day', -5, (SELECT MAX(PRICE_DATE) FROM {db}.{md}.FACT_STOCK_PRICES))
    ),
    drops AS (
        SELECT lp.SecurityID, lp.PRICE_DATE,
            (lp.PRICE_CLOSE - lp.PREV_CLOSE) / NULLIF(lp.PREV_CLOSE, 0) AS DAILY_RETURN
        FROM latest_prices lp
        WHERE lp.PREV_CLOSE IS NOT NULL
          AND (lp.PRICE_CLOSE - lp.PREV_CLOSE) / NULLIF(lp.PREV_CLOSE, 0) < -0.03
    ),
    with_context AS (
        SELECT d.SecurityID, s.Ticker, s.Description, i.GICS_SECTOR, d.DAILY_RETURN, d.PRICE_DATE,
            ARRAY_AGG(DISTINCT p.PortfolioID) AS PIDS,
            ARRAY_AGG(DISTINCT p.PortfolioName) AS PNAMES,
            SUM(pos.PortfolioWeight * d.DAILY_RETURN) AS WEIGHTED_IMPACT
        FROM drops d
        JOIN {db}.{c}.DIM_SECURITY s ON d.SecurityID = s.SecurityID
        JOIN {db}.{c}.DIM_ISSUER i ON s.IssuerID = i.IssuerID
        JOIN {db}.{c}.FACT_POSITION_DAILY_ABOR pos ON d.SecurityID = pos.SecurityID
            AND pos.HoldingDate = (SELECT MAX(HoldingDate) FROM {db}.{c}.FACT_POSITION_DAILY_ABOR)
        JOIN {db}.{c}.DIM_PORTFOLIO p ON pos.PortfolioID = p.PortfolioID
        GROUP BY d.SecurityID, s.Ticker, s.Description, i.GICS_SECTOR, d.DAILY_RETURN, d.PRICE_DATE
    )
    SELECT
        'price_action', 'FACT_STOCK_PRICES', 'SECURITY', wc.SecurityID, wc.Ticker,
        wc.PIDS, wc.PNAMES,
        'risk_alert',
        wc.Ticker || ' dropped ' || ROUND(wc.DAILY_RETURN * 100, 1) || '% on ' || TO_VARCHAR(wc.PRICE_DATE, 'DD Mon'),
        wc.Description || ' (' || wc.GICS_SECTOR || ') fell ' || ROUND(wc.DAILY_RETURN * 100, 1) || '%. Portfolio impact: ' || ROUND(wc.WEIGHTED_IMPACT * 10000, 0) || 'bps.',
        CASE WHEN wc.DAILY_RETURN < -0.05 THEN 'immediate' WHEN wc.DAILY_RETURN < -0.04 THEN 'today' ELSE 'this_week' END,
        0.95,
        ROUND(wc.WEIGHTED_IMPACT * 10000, 1),
        'sql'
    FROM with_context wc
    """, 'price_action')


def extract_volume_spikes(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    md = config.DATABASE['schemas']['market_data']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_ID, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH vol_stats AS (
        SELECT SecurityID, PRICE_DATE, VOLUME,
            AVG(VOLUME) OVER (PARTITION BY SecurityID ORDER BY PRICE_DATE ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) AS AVG_VOL
        FROM {db}.{md}.FACT_STOCK_PRICES
        QUALIFY PRICE_DATE = (SELECT MAX(PRICE_DATE) FROM {db}.{md}.FACT_STOCK_PRICES)
    ),
    spikes AS (
        SELECT vs.SecurityID, vs.VOLUME, vs.AVG_VOL,
            vs.VOLUME / NULLIF(vs.AVG_VOL, 0) AS VOL_RATIO
        FROM vol_stats vs
        WHERE vs.AVG_VOL > 0 AND vs.VOLUME / vs.AVG_VOL > 3
    )
    SELECT 'volume_spike', 'FACT_STOCK_PRICES', 'SECURITY', sp.SecurityID, s.Ticker,
        'informational',
        s.Ticker || ' volume ' || ROUND(sp.VOL_RATIO, 1) || 'x above 20-day average',
        s.Description || ' traded ' || ROUND(sp.VOL_RATIO, 1) || 'x normal volume (' || ROUND(sp.VOLUME/1e6, 1) || 'M vs avg ' || ROUND(sp.AVG_VOL/1e6, 1) || 'M). Investigate for potential catalyst.',
        'today', 0.85, 'sql'
    FROM spikes sp
    JOIN {db}.{c}.DIM_SECURITY s ON sp.SecurityID = s.SecurityID
    """, 'volume_spike')


def extract_regime_transitions(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH regime_changes AS (
        SELECT DATE, MARKET_REGIME, VIX_CLOSE,
            LAG(MARKET_REGIME) OVER (ORDER BY DATE) AS PREV_REGIME
        FROM {db}.{c}.V_MACRO_REGIME
        WHERE DATE >= DATEADD('day', -30, CURRENT_DATE())
    )
    SELECT 'regime_change', 'V_MACRO_REGIME', 'MARKET', 'VIX / S&P 500',
        CASE WHEN rc.MARKET_REGIME = 'RISK_OFF' THEN 'risk_alert' ELSE 'informational' END,
        'Market regime shift: ' || rc.PREV_REGIME || ' → ' || rc.MARKET_REGIME,
        'VIX at ' || ROUND(rc.VIX_CLOSE, 1) || '. Market moved from ' || rc.PREV_REGIME || ' to ' || rc.MARKET_REGIME || ' on ' || TO_VARCHAR(rc.DATE, 'DD Mon YYYY') || '.',
        CASE WHEN rc.MARKET_REGIME = 'RISK_OFF' THEN 'immediate' WHEN rc.MARKET_REGIME = 'TRANSITIONAL' THEN 'today' ELSE 'this_week' END,
        0.90, 'sql'
    FROM regime_changes rc
    WHERE rc.PREV_REGIME IS NOT NULL AND rc.MARKET_REGIME != rc.PREV_REGIME
    """, 'regime_change')


def extract_yield_curve_inversion(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    md = config.DATABASE['schemas']['market_data']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH latest AS (
        SELECT MATURITY_CODE, YIELD_PCT
        FROM {db}.{md}.FACT_TREASURY_YIELDS
        WHERE DATE = (SELECT MAX(DATE) FROM {db}.{md}.FACT_TREASURY_YIELDS)
    ),
    spread AS (
        SELECT
            (SELECT YIELD_PCT FROM latest WHERE MATURITY_CODE = '2Y') AS Y2,
            (SELECT YIELD_PCT FROM latest WHERE MATURITY_CODE = '10Y') AS Y10
    )
    SELECT 'yield_curve', 'FACT_TREASURY_YIELDS', 'MACRO', 'US Treasury Curve',
        'risk_alert',
        'Yield curve inverted: 2Y (' || ROUND(s.Y2, 2) || '%) > 10Y (' || ROUND(s.Y10, 2) || '%)',
        'The US Treasury yield curve is inverted with the 2-year yield at ' || ROUND(s.Y2, 2) || '% vs 10-year at ' || ROUND(s.Y10, 2) || '%. Spread: ' || ROUND((s.Y10 - s.Y2) * 100, 0) || 'bps. Historically signals recession risk.',
        'today', 0.95, 'sql'
    FROM spread s
    WHERE s.Y2 > s.Y10
    """, 'yield_curve')


def extract_compliance_alerts(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_ID, ENTITY_NAME,
         PORTFOLIO_IDS, PORTFOLIO_NAMES, SIGNAL_TYPE, HEADLINE, DETAIL,
         URGENCY, CONFIDENCE, EXTRACTION_TIER)
    SELECT
        'compliance', 'FACT_COMPLIANCE_ALERTS', 'SECURITY', ca.SecurityID, s.Ticker,
        ARRAY_CONSTRUCT(ca.PortfolioID), ARRAY_CONSTRUCT(p.PortfolioName),
        'compliance',
        ca.AlertType || ': ' || s.Ticker || ' in ' || p.PortfolioName,
        ca.AlertDescription,
        CASE ca.AlertSeverity WHEN 'BREACH' THEN 'immediate' ELSE 'today' END,
        1.0, 'sql'
    FROM {db}.{c}.FACT_COMPLIANCE_ALERTS ca
    JOIN {db}.{c}.DIM_SECURITY s ON ca.SecurityID = s.SecurityID
    JOIN {db}.{c}.DIM_PORTFOLIO p ON ca.PortfolioID = p.PortfolioID
    WHERE ca.ResolvedDate IS NULL
      AND ca.AlertDate >= DATEADD('day', -30, CURRENT_DATE())
    """, 'compliance')


def extract_esg_downgrades(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_ID, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH ranked AS (
        SELECT SecurityID, SCORE_DATE, SCORE_GRADE, SCORE_VALUE,
            LAG(SCORE_GRADE) OVER (PARTITION BY SecurityID ORDER BY SCORE_DATE) AS PREV_GRADE,
            LAG(SCORE_VALUE) OVER (PARTITION BY SecurityID ORDER BY SCORE_DATE) AS PREV_VALUE
        FROM {db}.{c}.FACT_ESG_SCORES
        WHERE SCORE_TYPE = 'Overall ESG'
    )
    SELECT 'esg_downgrade', 'FACT_ESG_SCORES', 'SECURITY', r.SecurityID, s.Ticker,
        CASE WHEN r.SCORE_GRADE IN ('B', 'CCC') THEN 'risk_alert' ELSE 'informational' END,
        s.Ticker || ' ESG downgraded: ' || r.PREV_GRADE || ' → ' || r.SCORE_GRADE,
        s.Description || ' ESG rating changed from ' || r.PREV_GRADE || ' (' || ROUND(r.PREV_VALUE, 0) || ') to ' || r.SCORE_GRADE || ' (' || ROUND(r.SCORE_VALUE, 0) || '). Review for ESG mandate compliance.',
        CASE WHEN r.SCORE_GRADE IN ('B', 'CCC') THEN 'today' ELSE 'this_week' END,
        0.90, 'sql'
    FROM ranked r
    JOIN {db}.{c}.DIM_SECURITY s ON r.SecurityID = s.SecurityID
    WHERE r.PREV_GRADE IS NOT NULL AND r.SCORE_GRADE < r.PREV_GRADE
    """, 'esg_downgrade')


def extract_insider_clusters(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_ID, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH sell_clusters AS (
        SELECT TICKER, SecurityID, TRANSACTION_DATE,
            COUNT(*) OVER (PARTITION BY TICKER ORDER BY TRANSACTION_DATE
                RANGE BETWEEN INTERVAL '30 DAY' PRECEDING AND CURRENT ROW) AS CLUSTER_COUNT
        FROM {db}.{c}.FACT_INSIDER_TRANSACTIONS
        WHERE TRANSACTION_ACTION = 'Disposed'
        QUALIFY CLUSTER_COUNT >= 3
            AND ROW_NUMBER() OVER (PARTITION BY TICKER ORDER BY TRANSACTION_DATE DESC) = 1
    )
    SELECT 'insider_cluster', 'FACT_INSIDER_TRANSACTIONS', 'SECURITY', sc.SecurityID, sc.TICKER,
        'risk_alert',
        sc.TICKER || ': ' || sc.CLUSTER_COUNT || ' insider sells in 30 days',
        sc.CLUSTER_COUNT || ' insiders sold ' || sc.TICKER || ' shares within a 30-day window ending ' || TO_VARCHAR(sc.TRANSACTION_DATE, 'DD Mon YYYY') || '. Cluster selling may signal management concern.',
        CASE WHEN sc.CLUSTER_COUNT >= 5 THEN 'today' ELSE 'this_week' END,
        0.75, 'sql'
    FROM sell_clusters sc
    """, 'insider_cluster')


def extract_institutional_exits(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_ID, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH qoq AS (
        SELECT INSTITUTION_NAME, TICKER, SecurityID,
            REPORTING_PERIOD_YEAR, REPORTING_PERIOD_QUARTER,
            SHARES_HELD,
            LAG(SHARES_HELD) OVER (PARTITION BY INSTITUTION_NAME, TICKER
                ORDER BY REPORTING_PERIOD_YEAR, REPORTING_PERIOD_QUARTER) AS PREV_SHARES
        FROM {db}.{c}.FACT_INSTITUTIONAL_HOLDINGS
    ),
    exits AS (
        SELECT * FROM qoq
        WHERE PREV_SHARES > 0 AND (SHARES_HELD IS NULL OR SHARES_HELD = 0)
        QUALIFY ROW_NUMBER() OVER (PARTITION BY TICKER ORDER BY REPORTING_PERIOD_YEAR DESC, REPORTING_PERIOD_QUARTER DESC) = 1
    )
    SELECT 'institutional_exit', 'FACT_INSTITUTIONAL_HOLDINGS', 'SECURITY', e.SecurityID, e.TICKER,
        'risk_alert',
        e.INSTITUTION_NAME || ' fully exited ' || e.TICKER,
        e.INSTITUTION_NAME || ' sold their entire ' || e.TICKER || ' position (previously held ' || e.PREV_SHARES || ' shares) in Q' || e.REPORTING_PERIOD_QUARTER || ' ' || e.REPORTING_PERIOD_YEAR || '.',
        'this_week', 0.80, 'sql'
    FROM exits e
    LIMIT 20
    """, 'institutional_exit')


def extract_sector_rotation(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    md = config.DATABASE['schemas']['market_data']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH recent AS (
        SELECT SECTOR, DATE, SECTOR_RETURN
        FROM {db}.{md}.FACT_SECTOR_RETURNS
        WHERE DATE >= DATEADD('day', -10, (SELECT MAX(DATE) FROM {db}.{md}.FACT_SECTOR_RETURNS))
    ),
    defensive AS (
        SELECT DATE, AVG(SECTOR_RETURN) AS AVG_RET
        FROM recent WHERE SECTOR IN ('Consumer Staples', 'Utilities', 'Health Care')
        GROUP BY DATE
    ),
    cyclical AS (
        SELECT DATE, AVG(SECTOR_RETURN) AS AVG_RET
        FROM recent WHERE SECTOR IN ('Information Technology', 'Consumer Discretionary', 'Financials')
        GROUP BY DATE
    ),
    comparison AS (
        SELECT d.DATE, d.AVG_RET AS DEF_RET, cy.AVG_RET AS CYC_RET,
            d.AVG_RET - cy.AVG_RET AS SPREAD
        FROM defensive d JOIN cyclical cy ON d.DATE = cy.DATE
        ORDER BY d.DATE DESC
    ),
    streak AS (
        SELECT COUNT(*) AS DAYS_DEFENSIVE_LEADING
        FROM comparison WHERE SPREAD > 0
    )
    SELECT 'sector_rotation', 'FACT_SECTOR_RETURNS', 'MARKET', 'Sector Rotation',
        'informational',
        'Defensive sectors outperforming cyclicals for ' || s.DAYS_DEFENSIVE_LEADING || ' of last 10 days',
        'Defensive sectors (Staples, Utilities, Healthcare) have outperformed cyclicals (Tech, Discretionary, Financials) for ' || s.DAYS_DEFENSIVE_LEADING || ' of the last 10 trading days. This may signal a risk-off rotation.',
        CASE WHEN s.DAYS_DEFENSIVE_LEADING >= 7 THEN 'today' ELSE 'this_week' END,
        0.70, 'sql'
    FROM streak s
    WHERE s.DAYS_DEFENSIVE_LEADING >= 5
    """, 'sector_rotation')


def extract_cross_asset_divergence(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    md = config.DATABASE['schemas']['market_data']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH recent AS (
        SELECT DATE, BENCHMARK_CODE, DAILY_RETURN
        FROM {db}.{md}.FACT_BENCHMARK_RETURNS
        WHERE DATE >= DATEADD('day', -5, (SELECT MAX(DATE) FROM {db}.{md}.FACT_BENCHMARK_RETURNS))
    ),
    cumulative AS (
        SELECT BENCHMARK_CODE,
            SUM(DAILY_RETURN) AS CUM_5D
        FROM recent
        GROUP BY BENCHMARK_CODE
    ),
    divergence AS (
        SELECT
            (SELECT CUM_5D FROM cumulative WHERE BENCHMARK_CODE = 'SPX') AS SPX_5D,
            (SELECT CUM_5D FROM cumulative WHERE BENCHMARK_CODE = 'HYG') AS HYG_5D
    )
    SELECT 'cross_asset', 'FACT_BENCHMARK_RETURNS', 'MARKET', 'Equity/Credit Divergence',
        'risk_alert',
        'Equity/Credit divergence: S&P 500 ' || CASE WHEN d.SPX_5D > 0 THEN '+' ELSE '' END || ROUND(d.SPX_5D * 100, 1) || '% while HY Credit ' || CASE WHEN d.HYG_5D > 0 THEN '+' ELSE '' END || ROUND(d.HYG_5D * 100, 1) || '%',
        'Over the last 5 days, equities (S&P 500: ' || ROUND(d.SPX_5D * 100, 1) || '%) and high yield credit (HYG: ' || ROUND(d.HYG_5D * 100, 1) || '%) are moving in opposite directions. This divergence historically precedes increased volatility.',
        'today', 0.75, 'sql'
    FROM divergence d
    WHERE (d.SPX_5D > 0.01 AND d.HYG_5D < -0.005) OR (d.SPX_5D < -0.01 AND d.HYG_5D > 0.005)
    """, 'cross_asset')


def extract_factor_drift(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_NAME,
         PORTFOLIO_IDS, PORTFOLIO_NAMES, SIGNAL_TYPE, HEADLINE, DETAIL,
         URGENCY, CONFIDENCE, EXTRACTION_TIER)
    SELECT
        'factor_drift', 'V_FACTOR_ROLLING_ANALYTICS', 'PORTFOLIO', p.PortfolioName,
        ARRAY_CONSTRUCT(fra.PORTFOLIOID), ARRAY_CONSTRUCT(p.PortfolioName),
        'risk_alert',
        p.PortfolioName || ': ' || fra.FACTOR_NAME || ' drift ' || ROUND(fra.EXPOSURE_DRIFT_ZSCORE, 1) || ' sigma',
        fra.FACTOR_NAME || ' exposure has drifted ' || ROUND(fra.EXPOSURE_DRIFT_ZSCORE, 1) || ' standard deviations from its 6-month average in ' || p.PortfolioName || '. Current: ' || ROUND(fra.EXPOSURE, 3) || ', 6M avg: ' || ROUND(fra.EXPOSURE_6M_AVG, 3) || '.',
        CASE WHEN ABS(fra.EXPOSURE_DRIFT_ZSCORE) > 2.5 THEN 'today' ELSE 'this_week' END,
        0.85, 'sql'
    FROM {db}.{c}.V_FACTOR_ROLLING_ANALYTICS fra
    JOIN {db}.{c}.DIM_PORTFOLIO p ON fra.PORTFOLIOID = p.PortfolioID
    WHERE ABS(fra.EXPOSURE_DRIFT_ZSCORE) > 2.0
      AND fra.DATE = (SELECT MAX(DATE) FROM {db}.{c}.V_FACTOR_ROLLING_ANALYTICS)
    """, 'factor_drift')


def extract_attribution_anomalies(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_NAME,
         PORTFOLIO_IDS, PORTFOLIO_NAMES, SIGNAL_TYPE, HEADLINE, DETAIL,
         URGENCY, CONFIDENCE, EXTRACTION_TIER)
    SELECT
        'attribution_anomaly', 'V_ATTRIBUTION_ANOMALIES', 'PORTFOLIO', va.PORTFOLIONAME,
        ARRAY_CONSTRUCT(va.PORTFOLIOID), ARRAY_CONSTRUCT(va.PORTFOLIONAME),
        'risk_alert',
        va.PORTFOLIONAME || ': ' || va.ANOMALY_SEVERITY || ' severity — ' || (
            IFF(va.FACTOR_DRIFT_ALERT, 1, 0) + IFF(va.CONCENTRATION_ALERT, 1, 0) +
            IFF(va.STYLE_INCONSISTENCY, 1, 0) + IFF(va.ATTRIBUTION_SPIKE, 1, 0) +
            IFF(va.ALLOCATION_DRIFT_ALERT, 1, 0) + IFF(va.SELECTION_REVERSAL_ALERT, 1, 0) +
            IFF(va.WEIGHT_CONCENTRATION_ALERT, 1, 0) + IFF(va.CLASSIFICATION_SENSITIVITY_ALERT, 1, 0)
        ) || ' anomaly flag(s)',
        'Anomalies detected: '
            || CASE WHEN va.FACTOR_DRIFT_ALERT THEN 'Factor Drift, ' ELSE '' END
            || CASE WHEN va.CONCENTRATION_ALERT THEN 'Concentration, ' ELSE '' END
            || CASE WHEN va.STYLE_INCONSISTENCY THEN 'Style Inconsistency, ' ELSE '' END
            || CASE WHEN va.ATTRIBUTION_SPIKE THEN 'Attribution Spike, ' ELSE '' END
            || CASE WHEN va.ALLOCATION_DRIFT_ALERT THEN 'Allocation Drift, ' ELSE '' END
            || CASE WHEN va.SELECTION_REVERSAL_ALERT THEN 'Selection Reversal, ' ELSE '' END
            || CASE WHEN va.WEIGHT_CONCENTRATION_ALERT THEN 'Weight Concentration, ' ELSE '' END,
        CASE va.ANOMALY_SEVERITY WHEN 'HIGH' THEN 'immediate' WHEN 'MEDIUM' THEN 'today' ELSE 'this_week' END,
        0.90, 'sql'
    FROM {db}.{c}.V_ATTRIBUTION_ANOMALIES va
    WHERE va.ANOMALY_SEVERITY IN ('HIGH', 'MEDIUM')
      AND va.DATE = (SELECT MAX(DATE) FROM {db}.{c}.V_ATTRIBUTION_ANOMALIES)
    """, 'attribution_anomaly')


def extract_thesis_challenges(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_ID, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH active_theses AS (
        SELECT ISSUERID, TICKER, COMPANY_NAME, THESIS_TITLE, HEALTH_STATUS,
               KEY_ASSUMPTIONS,
               ARRAY_SIZE(KEY_ASSUMPTIONS) AS TOTAL_ASSUMPTIONS
        FROM {db}.{c}.FACT_RESEARCH_THESES
        WHERE STAGE = 'ACTIVE' AND HEALTH_STATUS IN ('AMBER', 'RED')
    ),
    challenged AS (
        SELECT t.ISSUERID, t.TICKER, t.COMPANY_NAME, t.THESIS_TITLE, t.HEALTH_STATUS,
               t.TOTAL_ASSUMPTIONS,
               f.value:assumption::VARCHAR AS challenged_assumption,
               f.value:evidence::VARCHAR AS evidence
        FROM active_theses t,
             LATERAL FLATTEN(input => t.KEY_ASSUMPTIONS) f
        WHERE f.value:status::VARCHAR IN ('CHALLENGED', 'INVALIDATED')
    ),
    grouped AS (
        SELECT ISSUERID, TICKER, COMPANY_NAME, THESIS_TITLE,
               MAX(HEALTH_STATUS) AS HEALTH_STATUS,
               MAX(TOTAL_ASSUMPTIONS) AS TOTAL_ASSUMPTIONS,
               COUNT(*) AS CHALLENGED_COUNT,
               LISTAGG('- ' || challenged_assumption || ' [' || evidence || ']', '\\n')
                   WITHIN GROUP (ORDER BY challenged_assumption) AS ALL_CHALLENGES
        FROM challenged
        GROUP BY ISSUERID, TICKER, COMPANY_NAME, THESIS_TITLE
    )
    SELECT
        'thesis_tracker', 'FACT_RESEARCH_THESES', 'SECURITY', g.ISSUERID, g.TICKER,
        'thesis_challenge',
        g.COMPANY_NAME || ': ' || g.CHALLENGED_COUNT || ' of ' || g.TOTAL_ASSUMPTIONS || ' thesis assumptions challenged',
        'Thesis "' || g.THESIS_TITLE || '" — Health: ' || g.HEALTH_STATUS || '\\n\\n' || g.ALL_CHALLENGES,
        CASE g.HEALTH_STATUS WHEN 'RED' THEN 'immediate' ELSE 'today' END,
        0.85, 'sql'
    FROM grouped g
    """, 'thesis_tracker')


# ---------------------------------------------------------------------------
# TIER 2: AI_COMPLETE with structured output
# ---------------------------------------------------------------------------

def extract_transcript_signals(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    model = config.AI_SIGNAL_EXTRACTION_MODEL
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, EVIDENCE, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH ceo_cfo_turns AS (
        SELECT TICKER, COMPANY_NAME, PUBLISH_DATE, FISCAL_YEAR, FISCAL_PERIOD,
            SPEAKER_ROLE,
            LEFT(LISTAGG(DOCUMENT_TEXT, '\\n') WITHIN GROUP (ORDER BY SEGMENT_INDEX, CHUNK_INDEX), 1000000) AS FULL_TEXT
        FROM {db}.{c}.COMPANY_EVENT_TRANSCRIPTS_CORPUS
        WHERE EVENT_TYPE = 'Earnings Call'
          AND SPEAKER_ROLE IN ('CEO', 'CFO', 'Chief Executive Officer', 'Chief Financial Officer')
          AND LENGTH(DOCUMENT_TEXT) > 50
          AND PUBLISH_DATE >= DATEADD('year', -1, CURRENT_DATE())
        GROUP BY TICKER, COMPANY_NAME, PUBLISH_DATE, FISCAL_YEAR, FISCAL_PERIOD, SPEAKER_ROLE
        QUALIFY ROW_NUMBER() OVER (PARTITION BY TICKER, FISCAL_YEAR, FISCAL_PERIOD, SPEAKER_ROLE ORDER BY PUBLISH_DATE DESC) = 1
    ),
    extracted AS (
        SELECT t.*,
            TRY_PARSE_JSON(
                AI_COMPLETE(
                    '{model}',
                    CONCAT(
                        'Analyse this earnings call remarks from the ', t.SPEAKER_ROLE,
                        ' of ', t.COMPANY_NAME, ' (', t.TICKER, '), ', t.FISCAL_PERIOD, ' ', t.FISCAL_YEAR,
                        '. Return JSON with: sentiment (positive/negative/neutral), sentiment_score (-1.0 to 1.0), ',
                        'guidance_direction (raised/lowered/maintained/not_mentioned), management_confidence (high/moderate/low), ',
                        'key_risk_mentioned (primary risk or none), supply_chain_concern (true/false).\\n\\n',
                        'Text:\\n', t.FULL_TEXT
                    )
                )
            ) AS signal_data
        FROM ceo_cfo_turns t
    )
    SELECT
        'transcript_nlp', 'COMPANY_EVENT_TRANSCRIPTS_CORPUS', 'SECURITY', e.TICKER,
        CASE
            WHEN e.signal_data:guidance_direction::STRING = 'lowered' THEN 'thesis_challenge'
            WHEN e.signal_data:sentiment::STRING = 'negative' THEN 'risk_alert'
            WHEN e.signal_data:supply_chain_concern::BOOLEAN = TRUE THEN 'risk_alert'
            ELSE 'informational'
        END,
        e.TICKER || ' ' || e.FISCAL_PERIOD || ' ' || e.FISCAL_YEAR || ': ' ||
            CASE
                WHEN e.signal_data:guidance_direction::STRING = 'lowered' THEN 'Guidance lowered'
                WHEN e.signal_data:sentiment::STRING = 'negative' THEN 'Negative management tone'
                WHEN e.signal_data:supply_chain_concern::BOOLEAN = TRUE THEN 'Supply chain concerns raised'
                ELSE e.signal_data:sentiment::STRING || ' sentiment'
            END,
        e.COMPANY_NAME || ' ' || e.SPEAKER_ROLE || ' (' || e.FISCAL_PERIOD || ' ' || e.FISCAL_YEAR || '): ' ||
            'Sentiment=' || e.signal_data:sentiment::STRING ||
            ', Guidance=' || e.signal_data:guidance_direction::STRING ||
            ', Confidence=' || e.signal_data:management_confidence::STRING ||
            CASE WHEN e.signal_data:key_risk_mentioned::STRING != 'none' THEN ', Key risk: ' || e.signal_data:key_risk_mentioned::STRING ELSE '' END,
        'Source: ' || e.SPEAKER_ROLE || ' — ' || e.COMPANY_NAME || ' earnings call ' || e.FISCAL_PERIOD || ' ' || e.FISCAL_YEAR,
        CASE
            WHEN e.signal_data:guidance_direction::STRING = 'lowered' THEN 'today'
            WHEN e.signal_data:sentiment::STRING = 'negative' THEN 'today'
            ELSE 'this_week'
        END,
        ABS(e.signal_data:sentiment_score::FLOAT),
        'cortex_ai'
    FROM extracted e
    WHERE e.signal_data IS NOT NULL
      AND (e.signal_data:sentiment::STRING = 'negative'
           OR e.signal_data:guidance_direction::STRING = 'lowered'
           OR e.signal_data:supply_chain_concern::BOOLEAN = TRUE)
    """, 'transcript_nlp')


def extract_sec_risk_factor_delta(session: Session) -> int:
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    md = config.DATABASE['schemas']['market_data']
    model = config.AI_SIGNAL_EXTRACTION_MODEL
    return _insert_signals(session, f"""
    INSERT INTO {db}.{c}.FACT_SIGNALS
        (SOURCE_TYPE, SOURCE_TABLE, ENTITY_TYPE, ENTITY_NAME,
         SIGNAL_TYPE, HEADLINE, DETAIL, URGENCY, CONFIDENCE, EXTRACTION_TIER)
    WITH filings AS (
        SELECT f.IssuerID, i.PrimaryTicker AS TICKER, i.LegalName,
            f.FILING_TEXT, f.FISCAL_YEAR,
            ROW_NUMBER() OVER (PARTITION BY f.IssuerID ORDER BY f.FISCAL_YEAR DESC) AS RN
        FROM {db}.{md}.FACT_SEC_FILING_TEXT f
        JOIN {db}.{c}.DIM_ISSUER i ON f.IssuerID = i.IssuerID
        WHERE f.VARIABLE_NAME = 'Risk Factors'
          AND LENGTH(f.FILING_TEXT) > 500
    ),
    paired AS (
        SELECT cy.IssuerID, cy.TICKER, cy.LegalName,
            cy.FILING_TEXT AS CURRENT_TEXT, cy.FISCAL_YEAR AS CY_YEAR,
            py.FILING_TEXT AS PRIOR_TEXT, py.FISCAL_YEAR AS PY_YEAR
        FROM filings cy
        JOIN filings py ON cy.IssuerID = py.IssuerID AND py.RN = cy.RN + 1
        WHERE cy.RN = 1
    ),
    analysed AS (
        SELECT p.*,
            TRY_PARSE_JSON(
                AI_COMPLETE(
                    '{model}',
                    CONCAT(
                        'Compare these Risk Factors sections for ', p.TICKER, '. ',
                        'Return JSON with: overall_risk_change (increased/decreased/stable), ',
                        'highest_concern (single most critical new or changed risk), ',
                        'new_risk_count (integer count of new risks added).\\n\\n',
                        'PRIOR YEAR (', p.PY_YEAR, '):\\n', p.PRIOR_TEXT, '\\n\\n',
                        'CURRENT YEAR (', p.CY_YEAR, '):\\n', p.CURRENT_TEXT
                    )
                )
            ) AS delta
        FROM paired p
    )
    SELECT
        'sec_risk_delta', 'FACT_SEC_FILING_TEXT', 'SECURITY', a.TICKER,
        CASE WHEN a.delta:overall_risk_change::STRING = 'increased' THEN 'risk_alert' ELSE 'informational' END,
        a.TICKER || ' 10-K risk factors: ' || a.delta:overall_risk_change::STRING || ' (FY' || a.PY_YEAR || ' → FY' || a.CY_YEAR || ')',
        a.LegalName || ': Overall risk profile ' || a.delta:overall_risk_change::STRING ||
            '. Highest concern: ' || COALESCE(a.delta:highest_concern::STRING, 'N/A') ||
            '. New risks added: ' || COALESCE(a.delta:new_risk_count::STRING, '0') || '.',
        CASE WHEN a.delta:overall_risk_change::STRING = 'increased' THEN 'today' ELSE 'this_week' END,
        0.80, 'cortex_ai'
    FROM analysed a
    WHERE a.delta IS NOT NULL
      AND a.delta:overall_risk_change::STRING != 'stable'
    """, 'sec_risk_delta')


# ---------------------------------------------------------------------------
# TIER 3: Agent enrichment (DATA_AGENT_RUN)
# ---------------------------------------------------------------------------

def create_signal_agent_tasks(session: Session):
    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    ai = config.DATABASE['schemas']['ai']
    wh = config.WAREHOUSES['execution']['name']

    session.sql(f"""
    CREATE OR REPLACE TASK {db}.{c}.SIGNAL_SUPPLY_CHAIN_CHECK
        WAREHOUSE = {wh}
        SCHEDULE = 'USING CRON 0 8 * * 1-5 UTC'
        COMMENT = 'Weekly supply chain cascade signal extraction'
        AS
        INSERT INTO {db}.{c}.FACT_SIGNALS
            (SOURCE_TYPE, ENTITY_TYPE, ENTITY_NAME, SIGNAL_TYPE, HEADLINE, DETAIL,
             PORTFOLIO_IDS, PORTFOLIO_NAMES, URGENCY, CONFIDENCE, EXTRACTION_TIER)
        WITH portfolios AS (
            SELECT PortfolioID, PortfolioName FROM {db}.{c}.DIM_PORTFOLIO LIMIT 3
        ),
        agent_results AS (
            SELECT p.PortfolioID, p.PortfolioName,
                SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                    '{db}.{ai}.AM_portfolio_manager_copilot',
                    'Analyse supply chain exposure for ' || p.PortfolioName || '. For each Critical/High-tier supplier relationship, check recent developments. Report only material risks with estimated portfolio impact.',
                    '{{}}'
                ) AS resp
            FROM portfolios p
        ),
        parsed AS (
            SELECT ar.PortfolioID, ar.PortfolioName,
                f.value:text::STRING AS response_text
            FROM agent_results ar,
            LATERAL FLATTEN(input => ar.resp:content) f
            WHERE f.value:type::STRING = 'text'
        )
        SELECT 'supply_chain', 'PORTFOLIO', pr.PortfolioName, 'risk_alert',
            'Supply chain risk scan: ' || pr.PortfolioName,
            LEFT(pr.response_text, 10000),
            ARRAY_CONSTRUCT(pr.PortfolioID), ARRAY_CONSTRUCT(pr.PortfolioName),
            'this_week', 0.70, 'agent'
        FROM parsed pr
        WHERE pr.response_text IS NOT NULL AND LENGTH(pr.response_text) > 50
    """).collect()

    session.sql(f"ALTER TASK {db}.{c}.SIGNAL_SUPPLY_CHAIN_CHECK SUSPEND").collect()
    log_detail("  Created task: SIGNAL_SUPPLY_CHAIN_CHECK (SUSPENDED)")

    session.sql(f"""
    CREATE OR REPLACE TASK {db}.{c}.SIGNAL_THESIS_CHALLENGE
        WAREHOUSE = {wh}
        SCHEDULE = 'USING CRON 0 7 * * 1-5 UTC'
        COMMENT = 'Daily thesis challenge signal extraction'
        AS
        INSERT INTO {db}.{c}.FACT_SIGNALS
            (SOURCE_TYPE, ENTITY_TYPE, ENTITY_NAME, SIGNAL_TYPE, HEADLINE, DETAIL,
             PORTFOLIO_IDS, PORTFOLIO_NAMES, URGENCY, CONFIDENCE, EXTRACTION_TIER)
        WITH portfolios AS (
            SELECT PortfolioID, PortfolioName FROM {db}.{c}.DIM_PORTFOLIO LIMIT 3
        ),
        agent_results AS (
            SELECT p.PortfolioID, p.PortfolioName,
                SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                    '{db}.{ai}.AM_portfolio_manager_copilot',
                    'For the top 5 holdings in ' || p.PortfolioName || ', evaluate whether recent earnings, research, or market developments challenge or support the investment thesis. Flag any thesis at risk.',
                    '{{}}'
                ) AS resp
            FROM portfolios p
        ),
        parsed AS (
            SELECT ar.PortfolioID, ar.PortfolioName,
                f.value:text::STRING AS response_text
            FROM agent_results ar,
            LATERAL FLATTEN(input => ar.resp:content) f
            WHERE f.value:type::STRING = 'text'
        )
        SELECT 'thesis_challenge', 'PORTFOLIO', pr.PortfolioName, 'thesis_challenge',
            'Thesis challenge review: ' || pr.PortfolioName,
            LEFT(pr.response_text, 10000),
            ARRAY_CONSTRUCT(pr.PortfolioID), ARRAY_CONSTRUCT(pr.PortfolioName),
            'today', 0.75, 'agent'
        FROM parsed pr
        WHERE pr.response_text IS NOT NULL AND LENGTH(pr.response_text) > 50
    """).collect()

    session.sql(f"ALTER TASK {db}.{c}.SIGNAL_THESIS_CHALLENGE SUSPEND").collect()
    log_detail("  Created task: SIGNAL_THESIS_CHALLENGE (SUSPENDED)")


# ---------------------------------------------------------------------------
# Seeding orchestrator
# ---------------------------------------------------------------------------

def seed_signals(session: Session, test_mode: bool = False, include_tier2: bool = True, include_tier3: bool = False):
    log_phase("Signal Extraction Pipeline")

    create_fact_signals(session)
    truncate_signals(session)

    log_step("Tier 1: Pure SQL signal extraction")
    tier1_extractors = [
        ("Price drops", extract_price_drops),
        ("Volume spikes", extract_volume_spikes),
        ("VIX regime transitions", extract_regime_transitions),
        ("Yield curve inversion", extract_yield_curve_inversion),
        ("Compliance alerts", extract_compliance_alerts),
        ("ESG downgrades", extract_esg_downgrades),
        ("Insider sell clusters", extract_insider_clusters),
        ("Institutional exits", extract_institutional_exits),
        ("Sector rotation", extract_sector_rotation),
        ("Cross-asset divergence", extract_cross_asset_divergence),
        ("Factor drift", extract_factor_drift),
        ("Attribution anomalies", extract_attribution_anomalies),
        ("Thesis challenges", extract_thesis_challenges),
    ]

    tier1_total = 0
    for label, func in tier1_extractors:
        try:
            count = func(session)
            log_substep(f"  {label}: {count} signals")
            tier1_total += count
        except Exception as e:
            log_warning(f"  {label}: FAILED — {e}")

    log_success(f"  Tier 1 complete: {tier1_total} signals from {len(tier1_extractors)} extractors")

    if include_tier2 and not test_mode:
        log_step("Tier 2: AI_COMPLETE structured output extraction")
        try:
            count = extract_transcript_signals(session)
            log_substep(f"  Transcript signals: {count}")
        except Exception as e:
            log_warning(f"  Transcript signals failed: {e}")

        try:
            count = extract_sec_risk_factor_delta(session)
            log_substep(f"  SEC risk factor delta: {count}")
        except Exception as e:
            log_warning(f"  SEC risk factor delta failed: {e}")

    if include_tier3:
        log_step("Tier 3: Agent-enriched signal tasks")
        try:
            create_signal_agent_tasks(session)
        except Exception as e:
            log_warning(f"  Agent signal tasks failed: {e}")

    # Post-extraction: enrich all signals with portfolio exposure
    log_step("Enriching signals with portfolio exposure")
    try:
        enrich_signals_with_exposure(session)
    except Exception as e:
        log_warning(f"  Portfolio exposure enrichment failed: {e}")

    db = config.DATABASE['name']
    c = config.DATABASE['schemas']['curated']
    total = session.sql(f"SELECT COUNT(*) AS CNT FROM {db}.{c}.FACT_SIGNALS").collect()[0]['CNT']
    by_tier = session.sql(f"""
        SELECT EXTRACTION_TIER, COUNT(*) AS CNT
        FROM {db}.{c}.FACT_SIGNALS GROUP BY EXTRACTION_TIER ORDER BY EXTRACTION_TIER
    """).collect()

    tier_summary = ", ".join(f"{r['EXTRACTION_TIER']}={r['CNT']}" for r in by_tier)
    log_success(f"  Signal extraction complete: {total} total signals ({tier_summary})")
