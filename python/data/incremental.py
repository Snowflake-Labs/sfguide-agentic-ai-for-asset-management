# Copyright (c) 2025 Snowflake Inc.
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
"""Incremental structured-data builders for the weekly refresh.

The full builders in structured.py all use CREATE OR REPLACE over the whole
history, which is right for an initial build but wrong for a weekly one: it
rewrites five years of positions to add one week, and because the originals draw
on unseeded RANDOM() the rewrite silently changes history that a user may already
have looked at.

So each function here extends rather than rebuilds:

    FACT_TRANSACTION          append business days after the last trade date
    FACT_POSITION_DAILY_ABOR  add month-end snapshots that have become due
    FACT_FACTOR_EXPOSURES     recompute only when a new month has appeared
    ESG scores, benchmark holdings, client mandates   untouched by design

Everything is idempotent - reruns MERGE on a stable business key - so a failed
weekly run can simply be run again.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from snowflake.snowpark import Session

import config
from utils.logging import log_detail, log_substep, log_warning

# Trading intensity thresholds, matching the full builder so an appended week is
# indistinguishable in shape from the backfilled history.
# NOTE the ABS(). Snowflake's HASH returns a *signed* integer, so `HASH(x) % 100`
# yields negatives, and `< 15` is true for every one of them. The full builder in
# structured.py omitted ABS, which made 52.9% of days "busy" against an intended
# 15% (119 of 138 busy days were just negative hashes). Both modules now use ABS
# so an appended week has the same character as the backfilled history.
_TRADE_PROBABILITY_SQL = """
    CASE
        WHEN (ABS(HASH(trade_date)) % 100) < 15 THEN 0.6
        WHEN (ABS(HASH(trade_date)) % 100) < 40 THEN 0.3
        WHEN (ABS(HASH(trade_date)) % 100) < 75 THEN 0.1
        ELSE 0.0
    END
"""


def _as_date(value: Union[str, date, datetime, None]) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%d').date()
    return None


def _scalar(session: Session, sql: str) -> Any:
    rows = session.sql(sql).collect()
    return rows[0][0] if rows else None


def get_source_max_price_date(session: Session) -> Optional[date]:
    """Latest price date in the Marketplace share, i.e. the furthest the refresh can advance."""
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    prices_table = config.REAL_DATA_SOURCES['tables']['stock_prices']['table']
    return _as_date(_scalar(
        session, f"SELECT MAX(DATE) FROM {real_db}.{real_schema}.{prices_table}"
    ))


def append_stock_prices(
    session: Session,
    start_date: Union[str, date],
    end_date: Union[str, date],
) -> int:
    """Append new marketplace prices into FACT_STOCK_PRICES for a date window.

    This is the root of the weekly refresh: recommendations, transaction pricing,
    position revaluation and factor exposures all key off FACT_STOCK_PRICES, so
    nothing else can move until fresh prices land.

    Reads the share with an explicit date window. Change streams on the shared
    tables were tried and removed: a stream only reports changes since it was
    created so it can never supply the demo's history, and most of them went stale
    within a day, well inside a weekly cadence. A windowed read is the only
    reliable path.

    MERGE on (SecurityID, PRICE_DATE) keeps a rerun idempotent.
    """
    database = config.DATABASE['name']
    market_data = config.DATABASE['schemas']['market_data']
    curated = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    prices_table = config.REAL_DATA_SOURCES['tables']['stock_prices']['table']

    window_start = _as_date(start_date)
    window_end = _as_date(end_date)
    if window_start > window_end:
        log_detail("  FACT_STOCK_PRICES: window empty, nothing to append")
        return 0

    before = _scalar(
        session, f"SELECT COUNT(*) FROM {database}.{market_data}.FACT_STOCK_PRICES"
    ) or 0
    max_id = _scalar(
        session, f"SELECT COALESCE(MAX(PRICE_ID), 0) FROM {database}.{market_data}.FACT_STOCK_PRICES"
    ) or 0

    session.sql(f"""
        MERGE INTO {database}.{market_data}.FACT_STOCK_PRICES AS tgt
        USING (
            WITH our_securities AS (
                SELECT DISTINCT ds.SecurityID, ds.Ticker, ds.IssuerID
                FROM {database}.{curated}.DIM_SECURITY ds
                WHERE ds.Ticker IS NOT NULL AND ds.AssetClass = 'Equity'
            ),
            price_data AS (
                SELECT spt.TICKER, spt.ASSET_CLASS, spt.PRIMARY_EXCHANGE_CODE,
                       spt.PRIMARY_EXCHANGE_NAME, spt.DATE AS PRICE_DATE,
                       spt.VARIABLE, spt.VALUE
                FROM {real_db}.{real_schema}.{prices_table} spt
                WHERE spt.DATE BETWEEN '{window_start}'::DATE AND '{window_end}'::DATE
            ),
            pivoted AS (
                SELECT TICKER, ASSET_CLASS, PRIMARY_EXCHANGE_CODE,
                       PRIMARY_EXCHANGE_NAME, PRICE_DATE,
                       MAX(CASE WHEN VARIABLE = 'pre-market_open' THEN VALUE END) AS PRICE_OPEN,
                       MAX(CASE WHEN VARIABLE = 'post-market_close' THEN VALUE END) AS PRICE_CLOSE,
                       MAX(CASE WHEN VARIABLE = 'all-day_high' THEN VALUE END) AS PRICE_HIGH,
                       MAX(CASE WHEN VARIABLE = 'all-day_low' THEN VALUE END) AS PRICE_LOW,
                       MAX(CASE WHEN VARIABLE = 'nasdaq_volume' THEN VALUE END) AS VOLUME
                FROM price_data
                GROUP BY TICKER, ASSET_CLASS, PRIMARY_EXCHANGE_CODE,
                         PRIMARY_EXCHANGE_NAME, PRICE_DATE
            )
            SELECT
                {max_id} + ROW_NUMBER() OVER (ORDER BY os.SecurityID, pp.PRICE_DATE) AS PRICE_ID,
                os.SecurityID, os.IssuerID, pp.PRICE_DATE,
                pp.PRICE_OPEN, pp.PRICE_HIGH, pp.PRICE_LOW, pp.PRICE_CLOSE,
                pp.VOLUME::BIGINT AS VOLUME, pp.ASSET_CLASS,
                pp.PRIMARY_EXCHANGE_CODE, pp.PRIMARY_EXCHANGE_NAME,
                '{prices_table}' AS DATA_SOURCE
            FROM our_securities os
            INNER JOIN pivoted pp ON os.Ticker = pp.TICKER
            WHERE pp.PRICE_CLOSE IS NOT NULL
        ) AS src
        ON tgt.SecurityID = src.SecurityID AND tgt.PRICE_DATE = src.PRICE_DATE
        WHEN MATCHED THEN UPDATE SET
            PRICE_OPEN = src.PRICE_OPEN, PRICE_HIGH = src.PRICE_HIGH,
            PRICE_LOW = src.PRICE_LOW, PRICE_CLOSE = src.PRICE_CLOSE,
            VOLUME = src.VOLUME, LOADED_AT = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN INSERT (
            PRICE_ID, SecurityID, IssuerID, PRICE_DATE, PRICE_OPEN, PRICE_HIGH,
            PRICE_LOW, PRICE_CLOSE, VOLUME, ASSET_CLASS, PRIMARY_EXCHANGE_CODE,
            PRIMARY_EXCHANGE_NAME, DATA_SOURCE, LOADED_AT
        ) VALUES (
            src.PRICE_ID, src.SecurityID, src.IssuerID, src.PRICE_DATE,
            src.PRICE_OPEN, src.PRICE_HIGH, src.PRICE_LOW, src.PRICE_CLOSE,
            src.VOLUME, src.ASSET_CLASS, src.PRIMARY_EXCHANGE_CODE,
            src.PRIMARY_EXCHANGE_NAME, src.DATA_SOURCE, CURRENT_TIMESTAMP()
        )
    """).collect()

    after = _scalar(
        session, f"SELECT COUNT(*) FROM {database}.{market_data}.FACT_STOCK_PRICES"
    ) or 0
    added = after - before
    log_detail(
        f"  FACT_STOCK_PRICES: +{added} rows for {window_start}..{window_end}"
    )
    return added


def append_transactions(
    session: Session,
    as_of: Union[str, date],
    max_days: int = 7,
) -> int:
    """Append trades for business days between the last trade date and as_of.

    Two things are deliberately different from the full builder in
    structured.py:

    1. **Price comes from FACT_STOCK_PRICES, not `UNIFORM(50, 500, RANDOM())`.**
       The full builder invents a price unrelated to the security, so a trade in
       a $200 stock could be booked at $63 - the same class of defect as the
       ungrounded price targets. Appended trades use the real close on the trade
       date, which also makes position market values reconcile.

    2. **Quantities are HASH-derived, not RANDOM().** `UNIFORM(..., RANDOM())`
       re-rolls on every call, so the full builder cannot be re-run without
       changing history. A stable hash keeps the same spread and makes the append
       reproducible.

    Only securities a portfolio already trades are eligible, which is what makes
    this a carry-forward rather than a fresh allocation.

    Returns the number of transactions appended.
    """
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    as_of_date = _as_date(as_of)

    last_trade = _as_date(_scalar(
        session, f"SELECT MAX(TransactionDate) FROM {database}.{curated}.FACT_TRANSACTION"
    ))
    if last_trade is None:
        log_warning("  FACT_TRANSACTION is empty - run the full build first")
        return 0

    window_start = last_trade + timedelta(days=1)
    if window_start > as_of_date:
        log_detail(f"  FACT_TRANSACTION already current through {last_trade}")
        return 0
    # Bound the window so a long idle period cannot generate a huge burst of
    # trades in one run.
    window_end = min(as_of_date, window_start + timedelta(days=max_days - 1))

    # Guard the legacy schema. The original builder derived PRICE from
    # UNIFORM(50, 500, RANDOM()), so CTAS inferred NUMBER(3,0): integer-only and
    # unable to hold anything over 999. Writing a real close into it silently
    # rounds 894.32 to 894 and would overflow on a four-figure stock. Snowflake
    # cannot widen a NUMBER's scale with ALTER ("changing the scale of a number is
    # not supported"), so the only fix is a rebuild with the corrected builder.
    # Fail loudly rather than book wrong prices.
    price_scale = _scalar(session, f"""
        SELECT NUMERIC_SCALE FROM {database}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{curated}' AND TABLE_NAME = 'FACT_TRANSACTION'
          AND COLUMN_NAME = 'PRICE'
    """)
    if price_scale is not None and int(price_scale) < 2:
        raise RuntimeError(
            "FACT_TRANSACTION.PRICE is NUMBER(...,0) from the legacy builder, so "
            "real prices would be truncated to whole dollars and prices above 999 "
            "would overflow. Snowflake cannot widen a NUMBER scale in place - "
            "rebuild the table with the corrected builder "
            "(structured.build_fact_transaction) before appending."
        )

    max_id = _scalar(
        session, f"SELECT COALESCE(MAX(TransactionID), 0) FROM {database}.{curated}.FACT_TRANSACTION"
    ) or 0

    session.sql(f"""
        MERGE INTO {database}.{curated}.FACT_TRANSACTION AS tgt
        USING (
            WITH business_days AS (
                SELECT generated_date AS trade_date
                FROM (
                    SELECT DATEADD(day, seq4(), '{window_start}'::DATE) AS generated_date
                    FROM TABLE(GENERATOR(rowcount => {max_days}))
                )
                WHERE DAYOFWEEK(generated_date) BETWEEN 1 AND 5
                  AND generated_date BETWEEN '{window_start}'::DATE AND '{window_end}'::DATE
            ),
            trading_intensity AS (
                SELECT trade_date, {_TRADE_PROBABILITY_SQL} AS portfolio_trade_probability
                FROM business_days
            ),
            -- Only portfolio/security pairs that already trade, so a weekly
            -- append extends existing books instead of inventing new holdings.
            existing_pairs AS (
                SELECT DISTINCT PortfolioID, SecurityID
                FROM {database}.{curated}.FACT_TRANSACTION
            ),
            portfolio_trading_days AS (
                SELECT ep.PortfolioID, ep.SecurityID, ti.trade_date
                FROM existing_pairs ep
                CROSS JOIN trading_intensity ti
                WHERE ti.portfolio_trade_probability > 0
                  AND (ABS(HASH(ep.PortfolioID, ti.trade_date)) % 100)
                      < (ti.portfolio_trade_probability * 100)
                  AND (ABS(HASH(ep.SecurityID, ti.trade_date)) % 100) < 20
            ),
            -- Real close on or before the trade date, so a non-trading day still
            -- resolves and the booked price is the security's actual price.
            priced AS (
                SELECT ptd.PortfolioID, ptd.SecurityID, ptd.trade_date,
                       sp.PRICE_CLOSE,
                       ROW_NUMBER() OVER (
                           PARTITION BY ptd.PortfolioID, ptd.SecurityID, ptd.trade_date
                           ORDER BY sp.PRICE_DATE DESC
                       ) AS rn
                FROM portfolio_trading_days ptd
                JOIN {database}.{market_data}.FACT_STOCK_PRICES sp
                  ON sp.SecurityID = ptd.SecurityID
                 AND sp.PRICE_DATE <= ptd.trade_date
                 AND sp.PRICE_DATE >= DATEADD('day', -10, ptd.trade_date)
            ),
            -- Quantity scaled to the size this portfolio already trades in this
            -- security, so an appended week does not look different from history.
            typical_size AS (
                SELECT PortfolioID, SecurityID,
                       GREATEST(ROUND(AVG(Quantity)), 100) AS avg_qty
                FROM {database}.{curated}.FACT_TRANSACTION
                GROUP BY PortfolioID, SecurityID
            ),
            new_trades AS (
                SELECT
                    p.PortfolioID,
                    p.SecurityID,
                    p.trade_date,
                    p.PRICE_CLOSE,
                    -- Deterministic 70%-130% of the pair's typical size.
                    GREATEST(ROUND(
                        ts.avg_qty *
                        (0.7 + (ABS(HASH(p.PortfolioID, p.SecurityID, p.trade_date)) % 61) / 100.0)
                    ), 1)::NUMBER(18,0) AS Quantity
                FROM priced p
                JOIN typical_size ts
                  ON ts.PortfolioID = p.PortfolioID AND ts.SecurityID = p.SecurityID
                WHERE p.rn = 1 AND p.PRICE_CLOSE > 0
            )
            SELECT
                {max_id} + ROW_NUMBER() OVER (
                    ORDER BY PortfolioID, SecurityID, trade_date
                ) AS TransactionID,
                trade_date AS TransactionDate,
                trade_date AS TradeDate,
                PortfolioID,
                SecurityID,
                -- A small share of sells, so the book is not monotonically
                -- accumulating and position changes can go both ways.
                IFF((ABS(HASH(PortfolioID, SecurityID, trade_date)) % 100) < 25,
                    'SELL', 'BUY')::VARCHAR(16) AS TransactionType,
                DATEADD(day, 2, trade_date) AS SettleDate,
                Quantity,
                ROUND(PRICE_CLOSE, 4)::NUMBER(18,4) AS Price,
                ROUND(Quantity * PRICE_CLOSE, 2)::NUMBER(20,2) AS GrossAmount_Local,
                ROUND(5 + (ABS(HASH(PortfolioID, SecurityID, trade_date)) % 46), 2)::NUMBER(12,2)
                    AS Commission_Local,
                'USD' AS Currency,
                'ABOR' AS SourceSystem,
                -- Stable business key: derived from identity, not a row number,
                -- so a rerun matches the same row instead of inserting a copy.
                CONCAT('TXN_', MD5(CONCAT_WS('|', PortfolioID::VARCHAR,
                       SecurityID::VARCHAR, trade_date::VARCHAR))) AS SourceTransactionID
            FROM new_trades
        ) AS src
        ON tgt.SourceTransactionID = src.SourceTransactionID
        WHEN NOT MATCHED THEN INSERT (
            TransactionID, TransactionDate, TradeDate, PortfolioID, SecurityID,
            TransactionType, SettleDate, Quantity, Price, GrossAmount_Local,
            Commission_Local, Currency, SourceSystem, SourceTransactionID
        ) VALUES (
            src.TransactionID, src.TransactionDate, src.TradeDate, src.PortfolioID,
            src.SecurityID, src.TransactionType, src.SettleDate, src.Quantity,
            src.Price, src.GrossAmount_Local, src.Commission_Local, src.Currency,
            src.SourceSystem, src.SourceTransactionID
        )
    """).collect()

    appended = _scalar(session, f"""
        SELECT COUNT(*) FROM {database}.{curated}.FACT_TRANSACTION
        WHERE TransactionDate BETWEEN '{window_start}'::DATE AND '{window_end}'::DATE
    """) or 0
    log_detail(
        f"  FACT_TRANSACTION: {appended} trades for {window_start}..{window_end}"
    )
    return appended


def _pinned_weights_values_sql() -> str:
    """VALUES rows of (PortfolioName, Ticker, TargetWeight) for every pinned name.

    Same source as the full build's get_portfolio_target_weights_sql, but across
    every portfolio rather than one, so a portfolio that gains targets in
    config is pinned without a code change here.
    """
    from utils.demo_helpers import get_portfolio_target_weights

    rows = []
    for portfolio_name in config.PORTFOLIOS:
        for ticker, weight in get_portfolio_target_weights(portfolio_name).items():
            safe_name = portfolio_name.replace("'", "''")
            safe_ticker = ticker.replace("'", "''")
            rows.append(f"('{safe_name}', '{safe_ticker}', {float(weight)})")
    if not rows:
        return "SELECT NULL::VARCHAR AS PortfolioName, NULL::VARCHAR AS Ticker, NULL::FLOAT AS TargetWeight WHERE FALSE"
    return (
        "SELECT COLUMN1 AS PortfolioName, COLUMN2 AS Ticker, COLUMN3::FLOAT AS TargetWeight "
        f"FROM VALUES {', '.join(rows)}"
    )


def _position_snapshot_sql(position_date: date, prior_date: date) -> str:
    """SELECT producing one month-end snapshot, carried forward from the prior one.

    Non-pinned holdings carry their prior market value forward, revalued by the
    price move and scaled by any quantity change from trades in the month. A
    security with no prior row (a new buy) is valued at quantity x price.
    Pinned demo names are then set to their target weight exactly as the full
    build does it: the free names keep their relative values and the pinned
    names take the remainder in proportion to their targets, so the weights
    still sum to one.
    """
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    positions = f"{database}.{curated}.FACT_POSITION_DAILY_ABOR"
    prices = f"{database}.{market_data}.FACT_STOCK_PRICES"
    return f"""
        WITH pinned_config AS (
            {_pinned_weights_values_sql()}
        ),
        pinned AS (
            SELECT p.PortfolioID, s.SecurityID, MAX(c.TargetWeight) AS TargetWeight
            FROM pinned_config c
            JOIN {database}.{curated}.DIM_PORTFOLIO p ON p.PortfolioName = c.PortfolioName
            JOIN {database}.{curated}.DIM_SECURITY s ON s.Ticker = c.Ticker
            GROUP BY p.PortfolioID, s.SecurityID
        ),
        balances AS (
            SELECT PortfolioID, SecurityID,
                   SUM(IFF(TransactionType = 'BUY', Quantity, -Quantity)) AS TotalQuantity,
                   AVG(Price) AS AvgPrice
            FROM {database}.{curated}.FACT_TRANSACTION
            WHERE TransactionDate <= '{position_date}'::DATE
            GROUP BY PortfolioID, SecurityID
            HAVING TotalQuantity > 0
        ),
        current_price AS (
            SELECT SecurityID, PRICE_CLOSE
            FROM {prices}
            WHERE PRICE_DATE BETWEEN DATEADD('day', -10, '{position_date}'::DATE)
                                 AND '{position_date}'::DATE
              AND PRICE_CLOSE > 0
            QUALIFY ROW_NUMBER() OVER (PARTITION BY SecurityID ORDER BY PRICE_DATE DESC) = 1
        ),
        prior_price AS (
            SELECT SecurityID, PRICE_CLOSE
            FROM {prices}
            WHERE PRICE_DATE BETWEEN DATEADD('day', -10, '{prior_date}'::DATE)
                                 AND '{prior_date}'::DATE
              AND PRICE_CLOSE > 0
            QUALIFY ROW_NUMBER() OVER (PARTITION BY SecurityID ORDER BY PRICE_DATE DESC) = 1
        ),
        prior AS (
            SELECT PortfolioID, SecurityID, Quantity AS PriorQuantity,
                   MarketValue_Base AS PriorMarketValue
            FROM {positions}
            WHERE HoldingDate = '{prior_date}'::DATE
        ),
        valued AS (
            SELECT b.PortfolioID, b.SecurityID, b.TotalQuantity, b.AvgPrice,
                   pn.TargetWeight,
                   CASE
                       WHEN cp.PRICE_CLOSE IS NOT NULL AND pr.PriorMarketValue > 0
                            AND pr.PriorQuantity > 0 AND pp.PRICE_CLOSE IS NOT NULL
                           THEN pr.PriorMarketValue * (cp.PRICE_CLOSE / pp.PRICE_CLOSE)
                                * (b.TotalQuantity / pr.PriorQuantity)
                       WHEN cp.PRICE_CLOSE IS NOT NULL
                           THEN b.TotalQuantity * cp.PRICE_CLOSE
                       WHEN pr.PriorMarketValue > 0 AND pr.PriorQuantity > 0
                           THEN pr.PriorMarketValue * (b.TotalQuantity / pr.PriorQuantity)
                   END AS RawMarketValue
            FROM balances b
            LEFT JOIN current_price cp ON cp.SecurityID = b.SecurityID
            LEFT JOIN prior_price pp ON pp.SecurityID = b.SecurityID
            LEFT JOIN prior pr
              ON pr.PortfolioID = b.PortfolioID AND pr.SecurityID = b.SecurityID
            LEFT JOIN pinned pn
              ON pn.PortfolioID = b.PortfolioID AND pn.SecurityID = b.SecurityID
        ),
        totals AS (
            SELECT PortfolioID,
                   SUM(IFF(TargetWeight IS NULL, RawMarketValue, 0)) AS FreeMarketValue,
                   SUM(COALESCE(TargetWeight, 0)) AS PinnedWeight
            FROM valued
            WHERE RawMarketValue > 0
            GROUP BY PortfolioID
        ),
        snapshot AS (
            SELECT v.PortfolioID, v.SecurityID, v.TotalQuantity, v.AvgPrice,
                   CASE
                       WHEN v.TargetWeight IS NOT NULL AND t.PinnedWeight < 1 AND t.FreeMarketValue > 0
                           THEN t.FreeMarketValue / (1 - t.PinnedWeight) * v.TargetWeight
                       ELSE v.RawMarketValue
                   END AS MarketValue
            FROM valued v
            JOIN totals t ON t.PortfolioID = v.PortfolioID
            WHERE v.RawMarketValue > 0
        )
        SELECT
            '{position_date}'::DATE AS HoldingDate,
            PortfolioID,
            SecurityID,
            TotalQuantity AS Quantity,
            MarketValue AS MarketValue_Local,
            MarketValue AS MarketValue_Base,
            TotalQuantity * AvgPrice AS CostBasis_Local,
            TotalQuantity * AvgPrice AS CostBasis_Base,
            0 AS AccruedInterest_Local,
            MarketValue / NULLIF(SUM(MarketValue) OVER (PARTITION BY PortfolioID), 0) AS PortfolioWeight
        FROM snapshot
    """


def extend_positions(session: Session, as_of: Union[str, date]) -> int:
    """Write month-end position snapshots that have become due.

    FACT_POSITION_DAILY_ABOR is a monthly snapshot despite its name. Each run
    rewrites the latest existing month-end as well as adding any newly elapsed
    one, so a snapshot written by older code (the 2026-09-30 one that valued
    the pinned demo names at quantity x price and put AAPL at 28%) is replaced
    on the next run. The rewrite is a DELETE and INSERT per date inside one
    transaction, so a rerun yields the same rows and a security no longer held
    does not linger.

    The full build pins demo names to config target weights; a snapshot that
    ignores the pins makes the demo's headline holdings jump every month. See
    _position_snapshot_sql for how they are carried forward.

    Returns the number of rows written for month-ends that did not exist before.
    """
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    positions = f"{database}.{curated}.FACT_POSITION_DAILY_ABOR"
    as_of_date = _as_date(as_of)

    holding_dates = [
        _as_date(r[0]) for r in session.sql(f"""
            SELECT DISTINCT HoldingDate FROM {positions}
            ORDER BY HoldingDate DESC LIMIT 2
        """).collect()
    ]
    if not holding_dates:
        log_warning("  FACT_POSITION_DAILY_ABOR is empty - run the full build first")
        return 0
    last_holding = holding_dates[0]
    if len(holding_dates) < 2:
        log_warning("  FACT_POSITION_DAILY_ABOR has one snapshot - nothing to carry forward from")
        return 0

    due_dates = [last_holding]
    candidate = last_holding
    while True:
        candidate = _month_end(candidate + timedelta(days=1))
        if candidate > as_of_date:
            break
        due_dates.append(candidate)

    prior_date = holding_dates[1]
    added = 0
    for position_date in due_dates:
        is_new = position_date != last_holding
        session.sql("BEGIN").collect()
        try:
            session.sql(
                f"DELETE FROM {positions} WHERE HoldingDate = '{position_date}'::DATE"
            ).collect()
            rows = session.sql(f"""
                INSERT INTO {positions} (
                    HoldingDate, PortfolioID, SecurityID, Quantity, MarketValue_Local,
                    MarketValue_Base, CostBasis_Local, CostBasis_Base,
                    AccruedInterest_Local, PortfolioWeight
                )
                {_position_snapshot_sql(position_date, prior_date)}
            """).collect()
            session.sql("COMMIT").collect()
        except Exception:
            session.sql("ROLLBACK").collect()
            raise
        written = rows[0][0] if rows else 0
        if is_new:
            added += written
        log_detail(
            f"  FACT_POSITION_DAILY_ABOR: {position_date} "
            f"{'added' if is_new else 'rewritten'} ({written} rows, carried from {prior_date})"
        )
        prior_date = position_date
    return added


def _month_end(value: date) -> date:
    next_month = (value.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def extend_factor_exposures(session: Session, as_of: Union[str, date]) -> int:
    """Recompute factor exposures when a new month has appeared.

    Exposures are cross-sectionally z-scored *within* each month, so a month
    cannot be computed from one security at a time - it needs that month's whole
    cross-section. Rather than re-parameterising the large factor SQL and risking
    a subtly different z-score for appended months than backfilled ones, this
    gates the existing builder on whether a new month exists at all. On the three
    weeks out of four when it does not, the cost is one COUNT query.

    Returns the number of exposure rows for the newly added month, or 0 if none.
    """
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    as_of_date = _as_date(as_of)

    last_exposure = _as_date(_scalar(
        session, f"SELECT MAX(EXPOSURE_DATE) FROM {database}.{curated}.FACT_FACTOR_EXPOSURES"
    ))
    latest_price_month = _as_date(_scalar(session, f"""
        SELECT DATE_TRUNC('month', MAX(PRICE_DATE))
        FROM {database}.{market_data}.FACT_STOCK_PRICES
        WHERE PRICE_DATE <= '{as_of_date}'::DATE
    """))

    if last_exposure is None or latest_price_month is None:
        log_warning("  Cannot determine factor exposure window - skipping")
        return 0
    if latest_price_month <= last_exposure:
        log_detail(f"  FACT_FACTOR_EXPOSURES: current through {last_exposure}")
        return 0

    log_detail(
        f"  FACT_FACTOR_EXPOSURES: new month {latest_price_month} - recomputing "
        "cross-section"
    )
    from data import structured
    structured.build_factor_exposures(session)

    return _scalar(session, f"""
        SELECT COUNT(*) FROM {database}.{curated}.FACT_FACTOR_EXPOSURES
        WHERE EXPOSURE_DATE = '{latest_price_month}'::DATE
    """) or 0


def refresh_structured(session: Session, as_of: Union[str, date]) -> Dict[str, Any]:
    """Extend the structured tables that should move with a new week of prices.

    ESG scores, benchmark holdings, client mandates and the dimensions are left
    alone: they are reference data that does not change weekly, and rewriting
    them would churn the demo for no gain.
    """
    log_substep("Extending structured data...")
    summary = {
        'transactions': append_transactions(session, as_of),
        'positions': extend_positions(session, as_of),
        'market_reference': refresh_market_reference_data(session),
        'factor_exposures': extend_factor_exposures(session, as_of),
    }
    # NAV and reconciliation follow the positions, so they have to run after
    # extend_positions - a NAV can only be struck for a date that has holdings.
    try:
        from data import middle_office
        summary.update(middle_office.refresh_middle_office(session, as_of))
    except Exception as exc:
        log_warning(f"  Middle office refresh failed: {str(exc)[:200]}")
    summary['derived_analytics'] = refresh_derived_analytics(session)
    return summary


def _max_date(session: Session, table: str, column: str) -> Optional[date]:
    try:
        return _as_date(_scalar(session, f"SELECT MAX({column}) FROM {table}"))
    except Exception as exc:
        log_warning(f"  Could not read MAX({column}) from {table}: {str(exc)[:120]}")
        return None


def _is_behind(current: Optional[date], target: Optional[date]) -> bool:
    return target is not None and (current is None or current < target)


def refresh_market_reference_data(session: Session) -> int:
    """Rebuild the VIX, benchmark and sector return series when prices have moved.

    These come from the same Marketplace share as the stock prices but were only
    built by the full build, so they froze at build day. That stalled more than
    themselves: the regime model scores from FACT_VIX_DAILY and
    FACT_BENCHMARK_RETURNS, so ML.FACT_REGIME_PREDICTIONS stopped at the same
    date however often it was rescored, and the Brinson builders need a
    FACT_SECTOR_RETURNS row within five days of each month-end, so every
    snapshot after build day dropped out of attribution.

    The builder is a full CREATE OR REPLACE from the share, which is cheap at
    this size and keeps the derived VIX scaling identical to the build's.
    Returns 1 when rebuilt, 0 when already current.
    """
    database = config.DATABASE['name']
    market_data = config.DATABASE['schemas']['market_data']
    latest_price = _max_date(session, f"{database}.{market_data}.FACT_STOCK_PRICES", 'PRICE_DATE')
    stalest = min(
        (d for d in (
            _max_date(session, f"{database}.{market_data}.{t}", 'DATE')
            for t in ('FACT_VIX_DAILY', 'FACT_BENCHMARK_RETURNS', 'FACT_SECTOR_RETURNS')
        ) if d is not None),
        default=None,
    )
    if not _is_behind(stalest, latest_price):
        log_detail(f"  Market reference series: current through {stalest}")
        return 0
    from data import structured
    structured.build_attribution_market_data(session)
    log_detail(f"  Market reference series: rebuilt ({stalest} -> {latest_price})")
    return 1


def refresh_derived_analytics(session: Session) -> Dict[str, Any]:
    """Rebuild the analytics tables that only the full build used to write.

    Each is rebuilt with its existing builder only when it has fallen behind
    the data it derives from, so a week with no new month-end costs a handful
    of MAX() queries:

        Brinson chain, FACT_STRATEGY_PERFORMANCE   behind the latest position date
        FACT_COVARIANCE_MATRIX                    behind the latest price date
        FACT_TRADE_SETTLEMENT                     behind the latest price date
        FACT_CORPORATE_ACTIONS (+ impact)         forward ex-dates exhausted by the latest price date

    Failures are logged and reported, not raised: a stale attribution table is
    a worse demo, not a reason to hold the watermark.
    """
    from data import structured

    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    cur = f"{database}.{curated}"
    latest_position = _max_date(session, f"{cur}.FACT_POSITION_DAILY_ABOR", 'HoldingDate')
    latest_price = _max_date(session, f"{database}.{market_data}.FACT_STOCK_PRICES", 'PRICE_DATE')

    plan = [
        (
            'attribution',
            min(
                (d for d in (
                    _max_date(session, f"{cur}.FACT_BRINSON_ATTRIBUTION", 'DATE'),
                    _max_date(session, f"{cur}.FACT_BRINSON_ATTRIBUTION_DETAIL", 'DATE'),
                    _max_date(session, f"{cur}.FACT_BRINSON_LINKED", 'PERIODEND'),
                ) if d is not None),
                default=None,
            ),
            latest_position,
            (
                structured.build_attribution_tables,
                structured.build_multi_level_attribution,
                structured.build_currency_attribution,
                structured.build_attribution_linked,
                structured.build_advanced_attribution_views,
            ),
        ),
        (
            'strategy_performance',
            _max_date(session, f"{cur}.FACT_STRATEGY_PERFORMANCE", 'HOLDINGDATE'),
            latest_position,
            (structured.build_fact_strategy_performance,),
        ),
        (
            'covariance_matrix',
            _max_date(session, f"{cur}.FACT_COVARIANCE_MATRIX", 'ASOFDATE'),
            latest_price,
            (structured.build_fact_covariance_matrix,),
        ),
        (
            'trade_settlement',
            _max_date(session, f"{cur}.FACT_TRADE_SETTLEMENT", 'SETTLEMENTDATE'),
            latest_price,
            (structured.build_fact_trade_settlement,),
        ),
        (
            'corporate_actions',
            _max_date(session, f"{cur}.FACT_CORPORATE_ACTIONS", 'EXDATE'),
            latest_price,
            (structured.build_fact_corporate_actions, structured.build_fact_corporate_action_impact),
        ),
    ]

    summary: Dict[str, Any] = {}
    for name, current, target, builders in plan:
        if not _is_behind(current, target):
            summary[name] = 'CURRENT'
            continue
        try:
            for builder in builders:
                builder(session)
            summary[name] = 'REBUILT'
            log_detail(f"  {name}: rebuilt ({current} -> {target})")
        except Exception as exc:
            summary[name] = {'error': str(exc)[:200]}
            log_warning(f"  {name} rebuild failed: {str(exc)[:200]}")
    return summary


_PINNED_WEIGHT_TOLERANCE = 0.0025
_WEIGHT_SUM_TOLERANCE = 0.005


def _freshness_checks() -> List[tuple]:
    """(label, table, column, reference, tolerance_days) for the freshness check.

    reference is 'position' (must reach the latest month-end snapshot),
    'position_month' (monthly tables stamped on the first of the month) or
    'price' (must reach the positions date and sit within tolerance of the
    latest price).
    """
    database = config.DATABASE['name']
    cur = f"{database}.{config.DATABASE['schemas']['curated']}"
    md = f"{database}.{config.DATABASE['schemas']['market_data']}"
    ml = f"{database}.{config.DATABASE['schemas']['ml']}"
    return [
        ('FACT_BRINSON_ATTRIBUTION', f"{cur}.FACT_BRINSON_ATTRIBUTION", 'DATE', 'position', 0),
        ('FACT_BRINSON_BY_SECTOR', f"{cur}.FACT_BRINSON_BY_SECTOR", 'DATE', 'position', 0),
        ('FACT_BRINSON_ATTRIBUTION_DETAIL', f"{cur}.FACT_BRINSON_ATTRIBUTION_DETAIL", 'DATE', 'position', 0),
        ('FACT_BRINSON_LINKED', f"{cur}.FACT_BRINSON_LINKED", 'PERIODEND', 'position', 0),
        ('FACT_STRATEGY_PERFORMANCE', f"{cur}.FACT_STRATEGY_PERFORMANCE", 'HOLDINGDATE', 'position', 0),
        ('FACT_FACTOR_EXPOSURES', f"{cur}.FACT_FACTOR_EXPOSURES", 'EXPOSURE_DATE', 'position_month', 0),
        ('FACT_COVARIANCE_MATRIX', f"{cur}.FACT_COVARIANCE_MATRIX", 'ASOFDATE', 'price', 5),
        ('FACT_TRADE_SETTLEMENT', f"{cur}.FACT_TRADE_SETTLEMENT", 'SETTLEMENTDATE', 'price', 5),
        ('FACT_CORPORATE_ACTIONS', f"{cur}.FACT_CORPORATE_ACTIONS", 'EXDATE', 'price', 7),
        ('FACT_VIX_DAILY', f"{md}.FACT_VIX_DAILY", 'DATE', 'price', 5),
        ('FACT_SECTOR_RETURNS', f"{md}.FACT_SECTOR_RETURNS", 'DATE', 'price', 5),
        ('ML.FACT_REGIME_PREDICTIONS', f"{ml}.FACT_REGIME_PREDICTIONS", 'DATE', 'price', 5),
    ]


def _check_freshness(session: Session, latest_position: date, latest_price: Optional[date]) -> List[str]:
    notes = []
    for label, table, column, reference, tolerance in _freshness_checks():
        current = _max_date(session, table, column)
        if current is None:
            notes.append(f"{label}: no rows or unreadable")
            continue
        floor = latest_position
        if reference == 'position_month':
            floor = latest_position.replace(day=1)
        if current < floor:
            notes.append(f"{label}: max {column} {current} is behind positions date {latest_position}")
        elif reference == 'price' and latest_price and current < latest_price - timedelta(days=tolerance):
            notes.append(f"{label}: max {column} {current} lags latest price {latest_price} by more than {tolerance} days")
    return notes


def _check_private_markets_cadence(session: Session) -> List[str]:
    from data import private_markets

    database = config.DATABASE['name']
    cur = f"{database}.{config.DATABASE['schemas']['curated']}"
    ml = f"{database}.{config.DATABASE['schemas']['ml']}"
    notes = []
    for table, column, is_text in private_markets.QUARTERLY_PERIOD_TABLES:
        bad = session.sql(
            f"SELECT LISTAGG(TO_VARCHAR(period), ', ') WITHIN GROUP (ORDER BY period), COUNT(*) "
            f"FROM ({private_markets._off_cycle_periods_sql(table, column, is_text)})"
        ).collect()[0]
        if bad[1]:
            notes.append(f"{table}: {bad[1]} off-cycle or post-gap period(s): {bad[0]}")
    orphans = _scalar(session, f"""
        SELECT COUNT(DISTINCT s.QUARTER_DATE)
        FROM {ml}.FACT_CREDIT_RISK_SCORES s
        WHERE NOT EXISTS (
            SELECT 1 FROM {cur}.FACT_CREDIT_BORROWER_FINANCIALS f
            WHERE f.BORROWERID = s.BORROWER_ID AND TRY_TO_DATE(f.REPORTDATE) = s.QUARTER_DATE
        )
    """) or 0
    if orphans:
        notes.append(f"ML.FACT_CREDIT_RISK_SCORES: {orphans} scored quarter(s) with no borrower financials")
    mismatched = _scalar(session, f"""
        SELECT COUNT(*)
        FROM {cur}.FACT_CREDIT_BORROWER_FINANCIALS f
        JOIN {cur}.FACT_CREDIT_COVENANT_TRACKING c
          ON c.BORROWERID = f.BORROWERID
         AND TRY_TO_DATE(c.TESTDATE) = TRY_TO_DATE(f.REPORTDATE)
         AND c.COVENANTTYPE = 'Max Total Leverage'
        WHERE ABS(f.TOTALLEVERAGE - c.ACTUALVALUE) > 0.005
    """) or 0
    if mismatched:
        notes.append(
            f"FACT_CREDIT_BORROWER_FINANCIALS: {mismatched} borrower-quarter(s) where TOTALLEVERAGE "
            "disagrees with the Max Total Leverage covenant test"
        )
    return notes


def _check_position_weights(session: Session, latest_position: date) -> List[str]:
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    cur = f"{database}.{curated}"
    notes = []
    for row in session.sql(f"""
        SELECT p.PortfolioName, SUM(f.PortfolioWeight) AS TotalWeight
        FROM {cur}.FACT_POSITION_DAILY_ABOR f
        JOIN {cur}.DIM_PORTFOLIO p ON p.PortfolioID = f.PortfolioID
        WHERE f.HoldingDate = '{latest_position}'::DATE
        GROUP BY p.PortfolioName
        HAVING ABS(SUM(f.PortfolioWeight) - 1) > {_WEIGHT_SUM_TOLERANCE}
    """).collect():
        notes.append(f"{row[0]}: weights sum to {row[1]:.4f} at {latest_position}")
    for row in session.sql(f"""
        WITH pinned_config AS (
            {_pinned_weights_values_sql()}
        )
        SELECT c.PortfolioName, c.Ticker, c.TargetWeight, COALESCE(SUM(f.PortfolioWeight), 0) AS ActualWeight
        FROM pinned_config c
        JOIN {cur}.DIM_PORTFOLIO p ON p.PortfolioName = c.PortfolioName
        LEFT JOIN {cur}.DIM_SECURITY s ON s.Ticker = c.Ticker
        LEFT JOIN {cur}.FACT_POSITION_DAILY_ABOR f
          ON f.PortfolioID = p.PortfolioID AND f.SecurityID = s.SecurityID
         AND f.HoldingDate = '{latest_position}'::DATE
        GROUP BY c.PortfolioName, c.Ticker, c.TargetWeight
        HAVING ABS(COALESCE(SUM(f.PortfolioWeight), 0) - c.TargetWeight) > {_PINNED_WEIGHT_TOLERANCE}
    """).collect():
        notes.append(
            f"{row[0]} {row[1]}: weight {row[3]:.2%} vs pinned target {row[2]:.2%} at {latest_position}"
        )
    return notes


def _check_coverage(session: Session) -> List[str]:
    """Every top-N holding of each scenario portfolio has the required
    document types in its corpus and, if configured, a recommendation."""
    from core import hydration_engine

    database = config.DATABASE['name']
    cur = f"{database}.{config.DATABASE['schemas']['curated']}"
    settings = hydration_engine.get_coverage_settings()
    required = [t for t in settings['required_doc_types'] if t in config.DOCUMENT_TYPES]
    checks = [
        f"""IFF(EXISTS (
                SELECT 1 FROM {cur}.{config.DOCUMENT_TYPES[t]['corpus_name']} c
                WHERE c.TICKER = h.Ticker AND c.DOCUMENT_TYPE = '{t}'
            ), NULL, '{t}')"""
        for t in required
    ]
    if settings['require_recommendation']:
        checks.append(f"""IFF(EXISTS (
                SELECT 1 FROM {cur}.FACT_RECOMMENDATION r WHERE r.SecurityID = h.SecurityID
            ), NULL, 'recommendation')""")
    if not checks:
        return []
    missing_expr = "ARRAY_TO_STRING(ARRAY_CONSTRUCT_COMPACT(" + ", ".join(checks) + "), ', ')"
    notes = []
    for row in session.sql(f"""
        WITH top_holdings AS ({hydration_engine.get_scenario_top_holdings_sql()}),
        universe AS ({hydration_engine.get_coverage_universe_sql()}),
        holdings AS (
            SELECT u.SecurityID, u.Ticker,
                   COALESCE(t.PortfolioName, 'core or pinned anchor') AS PortfolioName
            FROM universe u
            LEFT JOIN top_holdings t ON t.SecurityID = u.SecurityID
        ),
        gaps AS (
            SELECT h.Ticker, h.PortfolioName, {missing_expr} AS Missing
            FROM holdings h
        )
        SELECT Ticker, Missing,
               LISTAGG(DISTINCT PortfolioName, '; ') WITHIN GROUP (ORDER BY PortfolioName) AS Portfolios
        FROM gaps
        WHERE Missing <> ''
        GROUP BY Ticker, Missing
        ORDER BY Ticker
    """).collect():
        notes.append(f"coverage gap {row[0]}: missing {row[1]} (coverage universe via {row[2]})")
    return notes


def data_health(session: Session) -> Dict[str, Any]:
    """Data-side health for --mode status.

    Covers what the refresh is supposed to keep true and has previously broken
    silently: fact tables advancing with the positions, quarterly private
    markets periods on cycle, and portfolio weights (including the pinned demo
    names) intact. Each failing check adds a note; any note makes it unhealthy.
    """
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    latest_position = _max_date(session, f"{database}.{curated}.FACT_POSITION_DAILY_ABOR", 'HoldingDate')
    latest_price = _max_date(session, f"{database}.{market_data}.FACT_STOCK_PRICES", 'PRICE_DATE')
    if latest_position is None:
        return {
            'healthy': False,
            'health_notes': ['FACT_POSITION_DAILY_ABOR is empty'],
        }

    notes: List[str] = []
    for check in (
        lambda: _check_freshness(session, latest_position, latest_price),
        lambda: _check_private_markets_cadence(session),
        lambda: _check_position_weights(session, latest_position),
        lambda: _check_coverage(session),
    ):
        try:
            notes.extend(check())
        except Exception as exc:
            notes.append(f"health check failed to run: {str(exc)[:200]}")
    return {
        'healthy': not notes,
        'positions_date': str(latest_position),
        'latest_price_date': str(latest_price) if latest_price else None,
        'health_notes': notes,
    }
