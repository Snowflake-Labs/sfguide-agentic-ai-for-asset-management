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
"""Advance the private-markets (PE and private credit) data with the demo.

Everything else in the demo now moves forward one week at a time, but the PE and
private-credit tables were rebuilt only on a full build. That made them the one
static island: run the demo a month after a build and the listed-equity side has
four new vintages of prices, positions and recommendations while every PE board
pack, KPI and compliance certificate is frozen. A presenter saying "this data
refreshes itself" was telling the truth about one half of the demo and not the
other.

This module extends the quarterly and monthly private-markets facts when their
period has elapsed, then lets the existing corpus builders regenerate the
documents that sit on top of them.

All generation is deterministic (MD5/HASH-derived, never RANDOM()) so a rerun
produces identical values, and all writes are set-based MERGEs keyed on the
natural business key so a rerun is idempotent.
"""

from datetime import date
from typing import Any, Dict, Optional

from snowflake.snowpark import Session

import config
from utils.logging import log_detail, log_substep, log_warning


def _db() -> str:
    return config.DATABASE['name']


def _cur() -> str:
    return f"{_db()}.{config.DATABASE['schemas']['curated']}"


def _scalar(session: Session, sql: str):
    rows = session.sql(sql).collect()
    return rows[0][0] if rows else None


def _as_date(value) -> Optional[date]:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


# ---------------------------------------------------------------------------
# Quarterly cadence
# ---------------------------------------------------------------------------

# Quarterly fact tables and how their period column is stored. Each table keeps
# the quarter cycle its own history was built on: credit periods fall on
# Mar/Jun/Sep/Dec 1st, PE KPIs on Jan/Apr/Jul/Oct 1st. The cycle is read from the
# earliest period rather than assumed, so it can never disagree with history.
QUARTERLY_PERIOD_TABLES = (
    ('FACT_PORTFOLIO_COMPANY_KPI', 'KPIDATE', False),
    ('FACT_CREDIT_BORROWER_FINANCIALS', 'REPORTDATE', True),
    ('FACT_CREDIT_COVENANT_TRACKING', 'TESTDATE', True),
)


def _period_expr(column: str, is_text: bool, alias: str = '') -> str:
    qualified = f"{alias}.{column}" if alias else column
    return f"TRY_TO_DATE({qualified})" if is_text else qualified


def _off_cycle_periods_sql(table: str, column: str, is_text: bool) -> str:
    """Periods that break the table's quarterly cycle.

    Two kinds: a period that is not a whole number of quarters from the anchor
    (the 2026-10-01 credit test one month after 2026-09-01), and every on-cycle
    period after the first missing quarter. The second matters for the KPI
    table, which skipped 2026-07-01: keeping 2026-10-01 would leave a permanent
    hole, whereas truncating at the gap lets the extension regenerate both
    quarters from the last good one.
    """
    cur = _cur()
    period = _period_expr(column, is_text)
    return f"""
        WITH periods AS (
            SELECT DISTINCT {period} AS period
            FROM {cur}.{table}
            WHERE {period} IS NOT NULL
        ), bounds AS (
            SELECT MIN(period) AS anchor FROM periods
        ), flagged AS (
            SELECT p.period,
                   DAY(p.period) = DAY(b.anchor)
                   AND MOD(DATEDIFF('month', b.anchor, p.period), 3) = 0 AS on_cycle,
                   DATEDIFF('month', b.anchor, p.period) / 3 AS quarter_index
            FROM periods p CROSS JOIN bounds b
        ), ranked AS (
            SELECT period, quarter_index,
                   ROW_NUMBER() OVER (ORDER BY period) - 1 AS position
            FROM flagged
            WHERE on_cycle
        ), first_gap AS (
            SELECT MIN(period) AS gap_from FROM ranked WHERE quarter_index <> position
        )
        SELECT period FROM flagged WHERE NOT on_cycle
        UNION
        SELECT r.period FROM ranked r CROSS JOIN first_gap g WHERE r.period >= g.gap_from
    """


def enforce_quarterly_cadence(session: Session) -> Dict[str, int]:
    """Delete off-cycle periods from the quarterly private-markets facts.

    Idempotent: on a clean table the period set is empty and nothing is
    deleted. Runs before the extensions so they drift off the last good
    quarter rather than off a stray month.
    """
    cur = _cur()
    removed: Dict[str, int] = {}
    for table, column, is_text in QUARTERLY_PERIOD_TABLES:
        rows = session.sql(f"""
            DELETE FROM {cur}.{table} t
            USING ({_off_cycle_periods_sql(table, column, is_text)}) x
            WHERE {_period_expr(column, is_text, 't')} = x.period
        """).collect()
        removed[table] = rows[0][0] if rows else 0
        if removed[table]:
            log_detail(f"  {table}: removed {removed[table]} off-cycle rows")
    removed.update(_remove_orphaned_credit_scores(session))
    return removed


def _remove_orphaned_credit_scores(session: Session) -> Dict[str, int]:
    """Drop ML credit scores for borrower-quarters that no longer exist.

    Rescoring rewrites both tables wholesale, but it runs in its own step and
    can fail independently, so the cleanup does not rely on it.
    """
    cur = _cur()
    ml = f"{_db()}.{config.DATABASE['schemas']['ml']}"
    removed: Dict[str, int] = {}
    for table in ('FACT_CREDIT_RISK_SCORES', 'FACT_CREDIT_SHAP_EXPLANATIONS'):
        try:
            rows = session.sql(f"""
                DELETE FROM {ml}.{table} s
                WHERE NOT EXISTS (
                    SELECT 1 FROM {cur}.FACT_CREDIT_BORROWER_FINANCIALS f
                    WHERE f.BORROWERID = s.BORROWER_ID
                      AND TRY_TO_DATE(f.REPORTDATE) = s.QUARTER_DATE
                )
            """).collect()
        except Exception as exc:
            log_warning(f"  {table} cleanup skipped: {str(exc)[:160]}")
            continue
        removed[table] = rows[0][0] if rows else 0
        if removed[table]:
            log_detail(f"  {table}: removed {removed[table]} orphaned rows")
    return removed


def align_borrower_leverage(session: Session) -> int:
    """Make borrower TOTALLEVERAGE agree with the covenant-tested leverage.

    The two tables were generated independently, so Orion's financials said
    5.70x while its Max Total Leverage test said 6.33x for the same quarter. The
    covenant test is the figure a credit committee acts on, so financials follow
    it; NETLEVERAGE is rescaled by the same ratio to keep the net/gross spread.
    Idempotent: rows that already agree are untouched.
    """
    cur = _cur()
    rows = session.sql(f"""
        UPDATE {cur}.FACT_CREDIT_BORROWER_FINANCIALS f
        SET NETLEVERAGE = ROUND(f.NETLEVERAGE * c.ACTUALVALUE / NULLIF(f.TOTALLEVERAGE, 0), 2),
            TOTALLEVERAGE = c.ACTUALVALUE
        FROM {cur}.FACT_CREDIT_COVENANT_TRACKING c
        WHERE c.BORROWERID = f.BORROWERID
          AND TRY_TO_DATE(c.TESTDATE) = TRY_TO_DATE(f.REPORTDATE)
          AND c.COVENANTTYPE = 'Max Total Leverage'
          AND c.ACTUALVALUE IS NOT NULL
          AND (f.TOTALLEVERAGE IS NULL OR ABS(f.TOTALLEVERAGE - c.ACTUALVALUE) > 0.005)
    """).collect()
    updated = rows[0][0] if rows else 0
    if updated:
        log_detail(f"  Borrower financials: {updated} leverage figures aligned to covenant tests")
    return updated


def align_borrower_interest_coverage(session: Session) -> int:
    """Make borrower INTERESTCOVERAGE agree with the covenant-tested coverage.

    Same problem as leverage: Nexus showed 2.17x in its financials (below its
    2.49x covenant) while the covenant test recorded a compliant 2.80x, and
    Pinnacle the reverse. FIXEDCHARGECOVERAGE is rescaled by the same ratio.
    Idempotent: rows that already agree are untouched.
    """
    cur = _cur()
    rows = session.sql(f"""
        UPDATE {cur}.FACT_CREDIT_BORROWER_FINANCIALS f
        SET FIXEDCHARGECOVERAGE = ROUND(f.FIXEDCHARGECOVERAGE * c.ACTUALVALUE / NULLIF(f.INTERESTCOVERAGE, 0), 2),
            INTERESTCOVERAGE = c.ACTUALVALUE
        FROM (
            SELECT BORROWERID, TESTDATE, ACTUALVALUE
            FROM {cur}.FACT_CREDIT_COVENANT_TRACKING
            WHERE COVENANTTYPE = 'Min Interest Coverage' AND ACTUALVALUE IS NOT NULL
            QUALIFY ROW_NUMBER() OVER (PARTITION BY BORROWERID, TESTDATE ORDER BY FACILITYID) = 1
        ) c
        WHERE c.BORROWERID = f.BORROWERID
          AND TRY_TO_DATE(c.TESTDATE) = TRY_TO_DATE(f.REPORTDATE)
          AND (f.INTERESTCOVERAGE IS NULL OR ABS(f.INTERESTCOVERAGE - c.ACTUALVALUE) > 0.005)
    """).collect()
    updated = rows[0][0] if rows else 0
    if updated:
        log_detail(f"  Borrower financials: {updated} interest coverage figures aligned to covenant tests")
    return updated


# ---------------------------------------------------------------------------
# Portfolio company KPIs - quarterly
# ---------------------------------------------------------------------------

def extend_portfolio_company_kpis(session: Session, as_of: date) -> int:
    """Add a quarter of KPI observations when a new quarter has completed.

    The original builder wrote a single KPIDate, so every "what is the trend in
    Employee NPS" question was unanswerable - there was nothing to trend. This
    backfills the missing quarters up to as_of and then keeps pace.

    Values drift deterministically from the existing observation rather than
    being redrawn, so a company that is behind budget stays behind budget instead
    of flipping RAG status at random each quarter.
    """
    cur = _cur()
    latest = _as_date(_scalar(
        session, f"SELECT MAX(KPIDATE) FROM {cur}.FACT_PORTFOLIO_COMPANY_KPI"
    ))
    if latest is None:
        log_warning("  FACT_PORTFOLIO_COMPANY_KPI is empty - run the full build first")
        return 0

    # Quarter starts strictly after the latest observation, up to as_of.
    rows = session.sql(f"""
        MERGE INTO {cur}.FACT_PORTFOLIO_COMPANY_KPI AS tgt
        USING (
            WITH quarters AS (
                SELECT DATEADD('month', 3 * ROW_NUMBER() OVER (ORDER BY NULL),
                               '{latest}'::DATE) AS kpi_date
                FROM TABLE(GENERATOR(ROWCOUNT => 40))
            ), due AS (
                SELECT kpi_date FROM quarters
                WHERE kpi_date > '{latest}'::DATE AND kpi_date <= '{as_of}'::DATE
            ), base AS (
                -- One template row per company/KPI, taken from the most recent
                -- observation so drift compounds off real history.
                SELECT PORTFOLIOCOMPANYID, KPINAME, KPICATEGORY, UNIT,
                       ACTUALVALUE, BUDGETVALUE, PRIORYEARVALUE
                FROM (
                    SELECT k.*, ROW_NUMBER() OVER (
                        PARTITION BY PORTFOLIOCOMPANYID, KPINAME
                        ORDER BY KPIDATE DESC) AS rn
                    FROM {cur}.FACT_PORTFOLIO_COMPANY_KPI k
                ) WHERE rn = 1
            ), projected AS (
                SELECT
                    b.PORTFOLIOCOMPANYID, d.kpi_date AS KPIDATE, b.KPINAME,
                    b.KPICATEGORY, b.UNIT, b.BUDGETVALUE,
                    -- +/-6% deterministic drift off the prior actual.
                    ROUND(b.ACTUALVALUE * (1 + ((MOD(ABS(HASH(
                        b.PORTFOLIOCOMPANYID || '|' || b.KPINAME || '|' ||
                        TO_VARCHAR(d.kpi_date))), 1200) / 10000.0) - 0.06)), 2)
                        AS ACTUALVALUE,
                    b.ACTUALVALUE AS PRIORYEARVALUE
                FROM base b CROSS JOIN due d
            )
            SELECT
                PORTFOLIOCOMPANYID, KPIDATE, KPINAME, KPICATEGORY,
                ACTUALVALUE, BUDGETVALUE, PRIORYEARVALUE, UNIT,
                CASE
                    WHEN KPINAME IN ('Employee Turnover', 'Carbon Intensity') THEN
                        CASE WHEN ACTUALVALUE < BUDGETVALUE THEN 'Green'
                             WHEN ACTUALVALUE < BUDGETVALUE * 1.1 THEN 'Amber'
                             ELSE 'Red' END
                    ELSE
                        CASE WHEN ACTUALVALUE >= BUDGETVALUE THEN 'Green'
                             WHEN ACTUALVALUE >= BUDGETVALUE * 0.9 THEN 'Amber'
                             ELSE 'Red' END
                END AS STATUS
            FROM projected
        ) AS src
        ON tgt.PORTFOLIOCOMPANYID = src.PORTFOLIOCOMPANYID
       AND tgt.KPIDATE = src.KPIDATE
       AND tgt.KPINAME = src.KPINAME
        WHEN NOT MATCHED THEN INSERT (
            PORTFOLIOCOMPANYID, KPIDATE, KPINAME, KPICATEGORY,
            ACTUALVALUE, BUDGETVALUE, PRIORYEARVALUE, UNIT, STATUS
        ) VALUES (
            src.PORTFOLIOCOMPANYID, src.KPIDATE, src.KPINAME, src.KPICATEGORY,
            src.ACTUALVALUE, src.BUDGETVALUE, src.PRIORYEARVALUE, src.UNIT, src.STATUS
        )
    """).collect()
    inserted = rows[0][0] if rows else 0
    log_detail(f"  Portfolio company KPIs: +{inserted} observations")
    return inserted


def backfill_portfolio_company_kpis(session: Session, quarters: int = 8) -> int:
    """Give the KPI table the history it never had.

    The original builder wrote a single KPIDate per company, so "how has Employee
    NPS trended" and "which KPIs are deteriorating" had no answer - there was one
    observation and nothing to compare it to. extend_portfolio_company_kpis only
    adds quarters going forward, which does not help a demo being run today.

    This walks backwards from the earliest observation, treating it as the current
    value and deriving prior quarters from it, so the existing row stays exactly
    as it is and only history is added.
    """
    cur = _cur()
    earliest = _as_date(_scalar(
        session, f"SELECT MIN(KPIDATE) FROM {cur}.FACT_PORTFOLIO_COMPANY_KPI"
    ))
    if earliest is None:
        log_warning("  FACT_PORTFOLIO_COMPANY_KPI is empty - run the full build first")
        return 0
    periods = _scalar(
        session, f"SELECT COUNT(DISTINCT KPIDATE) FROM {cur}.FACT_PORTFOLIO_COMPANY_KPI"
    ) or 0
    if periods >= int(quarters):
        return 0

    rows = session.sql(f"""
        MERGE INTO {cur}.FACT_PORTFOLIO_COMPANY_KPI AS tgt
        USING (
            WITH back AS (
                SELECT DATEADD('quarter', -ROW_NUMBER() OVER (ORDER BY NULL),
                               DATE_TRUNC('quarter', '{earliest}'::DATE)) AS kpi_date
                FROM TABLE(GENERATOR(ROWCOUNT => {int(quarters)}))
            ), base AS (
                SELECT PORTFOLIOCOMPANYID, KPINAME, KPICATEGORY, UNIT,
                       ACTUALVALUE, BUDGETVALUE
                FROM {cur}.FACT_PORTFOLIO_COMPANY_KPI
                WHERE KPIDATE = '{earliest}'::DATE
            ), projected AS (
                SELECT
                    b.PORTFOLIOCOMPANYID, k.kpi_date AS KPIDATE, b.KPINAME,
                    b.KPICATEGORY, b.UNIT, b.BUDGETVALUE,
                    ROUND(b.ACTUALVALUE * (1 + ((MOD(ABS(HASH(
                        b.PORTFOLIOCOMPANYID || '|' || b.KPINAME || '|hist|' ||
                        TO_VARCHAR(k.kpi_date))), 1600) / 10000.0) - 0.08)), 2)
                        AS ACTUALVALUE
                FROM base b CROSS JOIN back k
            )
            SELECT
                PORTFOLIOCOMPANYID, KPIDATE, KPINAME, KPICATEGORY, ACTUALVALUE,
                BUDGETVALUE, ACTUALVALUE AS PRIORYEARVALUE, UNIT,
                CASE
                    WHEN KPINAME IN ('Employee Turnover', 'Carbon Intensity') THEN
                        CASE WHEN ACTUALVALUE < BUDGETVALUE THEN 'Green'
                             WHEN ACTUALVALUE < BUDGETVALUE * 1.1 THEN 'Amber'
                             ELSE 'Red' END
                    ELSE
                        CASE WHEN ACTUALVALUE >= BUDGETVALUE THEN 'Green'
                             WHEN ACTUALVALUE >= BUDGETVALUE * 0.9 THEN 'Amber'
                             ELSE 'Red' END
                END AS STATUS
            FROM projected
        ) AS src
        ON tgt.PORTFOLIOCOMPANYID = src.PORTFOLIOCOMPANYID
       AND tgt.KPIDATE = src.KPIDATE
       AND tgt.KPINAME = src.KPINAME
        WHEN NOT MATCHED THEN INSERT (
            PORTFOLIOCOMPANYID, KPIDATE, KPINAME, KPICATEGORY,
            ACTUALVALUE, BUDGETVALUE, PRIORYEARVALUE, UNIT, STATUS
        ) VALUES (
            src.PORTFOLIOCOMPANYID, src.KPIDATE, src.KPINAME, src.KPICATEGORY,
            src.ACTUALVALUE, src.BUDGETVALUE, src.PRIORYEARVALUE, src.UNIT, src.STATUS
        )
    """).collect()
    inserted = rows[0][0] if rows else 0
    log_detail(f"  Portfolio company KPI history: +{inserted} observations")
    return inserted


# ---------------------------------------------------------------------------
# Board pack metrics - monthly
# ---------------------------------------------------------------------------

def extend_board_pack_metrics(session: Session, as_of: date) -> int:
    """Add monthly board-pack metrics for months completed since the last one."""
    cur = _cur()
    latest = _as_date(_scalar(
        session, f"SELECT MAX(REPORTMONTH) FROM {cur}.FACT_BOARD_PACK_METRICS"
    ))
    if latest is None:
        log_warning("  FACT_BOARD_PACK_METRICS is empty - run the full build first")
        return 0

    rows = session.sql(f"""
        MERGE INTO {cur}.FACT_BOARD_PACK_METRICS AS tgt
        USING (
            WITH months AS (
                SELECT DATEADD('month', ROW_NUMBER() OVER (ORDER BY NULL),
                               DATE_TRUNC('month', '{latest}'::DATE)) AS report_month
                FROM TABLE(GENERATOR(ROWCOUNT => 36))
            ), due AS (
                SELECT report_month FROM months
                WHERE report_month > '{latest}'::DATE AND report_month <= '{as_of}'::DATE
            ), base AS (
                SELECT * FROM (
                    SELECT m.*, ROW_NUMBER() OVER (
                        PARTITION BY PORTFOLIOCOMPANYID ORDER BY REPORTMONTH DESC) AS rn
                    FROM {cur}.FACT_BOARD_PACK_METRICS m
                ) WHERE rn = 1
            )
            SELECT
                b.PORTFOLIOCOMPANYID,
                d.report_month AS REPORTMONTH,
                ROUND(b.REVENUE_MM * (1 + drift), 2) AS REVENUE_MM,
                ROUND(b.EBITDA_MM * (1 + drift), 2) AS EBITDA_MM,
                ROUND(b.EBITDAMARGINPCT * (1 + drift * 0.3), 2) AS EBITDAMARGINPCT,
                ROUND(b.NETDEBT_MM * (1 - drift * 0.2), 2) AS NETDEBT_MM,
                ROUND(b.LEVERAGERATIO * (1 - drift * 0.4), 2) AS LEVERAGERATIO,
                GREATEST(1, ROUND(b.HEADCOUNT * (1 + drift * 0.5))) AS HEADCOUNT,
                GREATEST(1, ROUND(b.CUSTOMERCOUNT * (1 + drift * 0.6))) AS CUSTOMERCOUNT,
                ROUND(b.NRR_PCT * (1 + drift * 0.2), 2) AS NRR_PCT,
                ROUND(drift * 100, 2) AS BUDGETVARIANCEPCT,
                ROUND(b.CASHPOSITION_MM * (1 + drift), 2) AS CASHPOSITION_MM,
                ROUND(b.CAPEXACTUAL_MM * (1 + drift * 0.5), 2) AS CAPEXACTUAL_MM,
                b.CAPEXBUDGET_MM
            FROM base b
            CROSS JOIN due d
            CROSS JOIN LATERAL (
                SELECT (MOD(ABS(HASH(b.PORTFOLIOCOMPANYID || '|bp|' ||
                        TO_VARCHAR(d.report_month))), 1600) / 10000.0) - 0.08 AS drift
            )
        ) AS src
        ON tgt.PORTFOLIOCOMPANYID = src.PORTFOLIOCOMPANYID
       AND tgt.REPORTMONTH = src.REPORTMONTH
        WHEN NOT MATCHED THEN INSERT (
            PORTFOLIOCOMPANYID, REPORTMONTH, REVENUE_MM, EBITDA_MM, EBITDAMARGINPCT,
            NETDEBT_MM, LEVERAGERATIO, HEADCOUNT, CUSTOMERCOUNT, NRR_PCT,
            BUDGETVARIANCEPCT, CASHPOSITION_MM, CAPEXACTUAL_MM, CAPEXBUDGET_MM
        ) VALUES (
            src.PORTFOLIOCOMPANYID, src.REPORTMONTH, src.REVENUE_MM, src.EBITDA_MM,
            src.EBITDAMARGINPCT, src.NETDEBT_MM, src.LEVERAGERATIO, src.HEADCOUNT,
            src.CUSTOMERCOUNT, src.NRR_PCT, src.BUDGETVARIANCEPCT,
            src.CASHPOSITION_MM, src.CAPEXACTUAL_MM, src.CAPEXBUDGET_MM
        )
    """).collect()
    inserted = rows[0][0] if rows else 0
    log_detail(f"  Board pack metrics: +{inserted} monthly rows")
    return inserted


# ---------------------------------------------------------------------------
# Credit borrower financials and covenant tests - quarterly
# ---------------------------------------------------------------------------

def extend_credit_financials(session: Session, as_of: date) -> int:
    """Add a quarter of borrower financials when a new quarter has completed."""
    cur = _cur()
    # REPORTDATE is stored as TEXT in this table, so every comparison and
    # DATE_TRUNC has to go through TRY_TO_DATE.
    latest = _as_date(_scalar(
        session,
        f"SELECT MAX(TRY_TO_DATE(REPORTDATE)) FROM {cur}.FACT_CREDIT_BORROWER_FINANCIALS"
    ))
    if latest is None:
        log_warning("  FACT_CREDIT_BORROWER_FINANCIALS is empty - run the full build first")
        return 0

    rows = session.sql(f"""
        MERGE INTO {cur}.FACT_CREDIT_BORROWER_FINANCIALS AS tgt
        USING (
            WITH quarters AS (
                SELECT DATEADD('month', 3 * ROW_NUMBER() OVER (ORDER BY NULL),
                               '{latest}'::DATE) AS report_date
                FROM TABLE(GENERATOR(ROWCOUNT => 40))
            ), due AS (
                SELECT report_date FROM quarters
                WHERE report_date > '{latest}'::DATE AND report_date <= '{as_of}'::DATE
            ), base AS (
                SELECT * FROM (
                    SELECT f.*, ROW_NUMBER() OVER (
                        PARTITION BY BORROWERID
                        ORDER BY TRY_TO_DATE(REPORTDATE) DESC) AS rn
                    FROM {cur}.FACT_CREDIT_BORROWER_FINANCIALS f
                ) WHERE rn = 1
            )
            SELECT
                b.BORROWERID, b.BORROWERNAME,
                TO_VARCHAR(d.report_date, 'YYYY-MM-DD') AS REPORTDATE,
                ROUND(b.REVENUE_MM * (1 + drift), 2) AS REVENUE_MM,
                ROUND(b.EBITDA_MM * (1 + drift), 2) AS EBITDA_MM,
                ROUND(b.EBITDA_MARGIN * (1 + drift * 0.3), 2) AS EBITDA_MARGIN,
                ROUND(b.TOTALLEVERAGE * (1 - drift * 0.5), 2) AS TOTALLEVERAGE,
                ROUND(b.NETLEVERAGE * (1 - drift * 0.5), 2) AS NETLEVERAGE,
                ROUND(b.INTERESTCOVERAGE * (1 + drift * 0.5), 2) AS INTERESTCOVERAGE,
                ROUND(b.FIXEDCHARGECOVERAGE * (1 + drift * 0.4), 2) AS FIXEDCHARGECOVERAGE,
                ROUND(b.FREECASHFLOW_MM * (1 + drift), 2) AS FREECASHFLOW_MM,
                ROUND(b.CAPEX_MM * (1 + drift * 0.5), 2) AS CAPEX_MM,
                ROUND(b.NETDEBT_MM * (1 - drift * 0.2), 2) AS NETDEBT_MM,
                ROUND(b.CASHONHAND_MM * (1 + drift), 2) AS CASHONHAND_MM,
                ROUND(b.REVOLVERAVAILABILITY_MM * (1 + drift * 0.3), 2) AS REVOLVERAVAILABILITY_MM
            FROM base b
            CROSS JOIN due d
            CROSS JOIN LATERAL (
                SELECT (MOD(ABS(HASH(b.BORROWERID || '|cf|' ||
                        TO_VARCHAR(d.report_date))), 1400) / 10000.0) - 0.07 AS drift
            )
        ) AS src
        ON tgt.BORROWERID = src.BORROWERID
       AND TRY_TO_DATE(tgt.REPORTDATE) = TRY_TO_DATE(src.REPORTDATE)
        WHEN NOT MATCHED THEN INSERT (
            BORROWERID, BORROWERNAME, REPORTDATE, REVENUE_MM, EBITDA_MM,
            EBITDA_MARGIN, TOTALLEVERAGE, NETLEVERAGE, INTERESTCOVERAGE,
            FIXEDCHARGECOVERAGE, FREECASHFLOW_MM, CAPEX_MM, NETDEBT_MM,
            CASHONHAND_MM, REVOLVERAVAILABILITY_MM
        ) VALUES (
            src.BORROWERID, src.BORROWERNAME, src.REPORTDATE, src.REVENUE_MM,
            src.EBITDA_MM, src.EBITDA_MARGIN, src.TOTALLEVERAGE, src.NETLEVERAGE,
            src.INTERESTCOVERAGE, src.FIXEDCHARGECOVERAGE, src.FREECASHFLOW_MM,
            src.CAPEX_MM, src.NETDEBT_MM, src.CASHONHAND_MM,
            src.REVOLVERAVAILABILITY_MM
        )
    """).collect()
    inserted = rows[0][0] if rows else 0
    log_detail(f"  Credit borrower financials: +{inserted} quarterly rows")
    return inserted


def extend_covenant_tracking(session: Session, as_of: date) -> int:
    """Add covenant tests for new quarters.

    The new test drifts off the borrower's previous ACTUALVALUE rather than being
    recomputed from the refreshed financials. Recomputing looked more principled
    but threw away the threshold calibration: the existing book runs at a 0.4%
    breach rate with 19% of tests "Tight", and deriving the actual straight from
    drifted leverage pushed a third of the book into breach, which no credit fund
    would be holding. Drifting the prior test keeps each borrower's headroom
    character intact while still moving quarter to quarter.

    STATUS uses the vocabulary already present in the table - Compliant, Tight,
    Breach - and not a new label, so downstream filters keep working.
    """
    cur = _cur()
    # TESTDATE is stored as TEXT here too.
    latest = _as_date(_scalar(
        session,
        f"SELECT MAX(TRY_TO_DATE(TESTDATE)) FROM {cur}.FACT_CREDIT_COVENANT_TRACKING"
    ))
    if latest is None:
        log_warning("  FACT_CREDIT_COVENANT_TRACKING is empty - run the full build first")
        return 0

    rows = session.sql(f"""
        MERGE INTO {cur}.FACT_CREDIT_COVENANT_TRACKING AS tgt
        USING (
            WITH quarters AS (
                SELECT DATEADD('month', 3 * ROW_NUMBER() OVER (ORDER BY NULL),
                               '{latest}'::DATE) AS test_date
                FROM TABLE(GENERATOR(ROWCOUNT => 40))
            ), due AS (
                SELECT test_date FROM quarters
                WHERE test_date > '{latest}'::DATE AND test_date <= '{as_of}'::DATE
            ), base AS (
                SELECT * FROM (
                    SELECT c.*, ROW_NUMBER() OVER (
                        PARTITION BY BORROWERID, COVENANTTYPE
                        ORDER BY TRY_TO_DATE(TESTDATE) DESC) AS rn
                    FROM {cur}.FACT_CREDIT_COVENANT_TRACKING c
                ) WHERE rn = 1
            ), projected AS (
                SELECT
                    b.BORROWERID, b.BORROWERNAME, b.FACILITYID, b.COVENANTTYPE,
                    b.COVENANTTHRESHOLD, b.STATUS AS prior_status, d.test_date,
                    ROUND(b.ACTUALVALUE * (1 + drift), 2) AS actual_value
                FROM base b
                CROSS JOIN due d
                CROSS JOIN LATERAL (
                    SELECT (MOD(ABS(HASH(b.BORROWERID || '|' || b.COVENANTTYPE ||
                            '|cov|' || TO_VARCHAR(d.test_date))), 1000) / 10000.0)
                            - 0.05 AS drift
                )
            )
            SELECT
                BORROWERID, BORROWERNAME, FACILITYID,
                TO_VARCHAR(test_date, 'YYYY-MM-DD') AS TESTDATE, COVENANTTYPE,
                COVENANTTHRESHOLD, actual_value AS ACTUALVALUE, prior_status,
                -- Covenant direction is given by the Max/Min prefix, not by the
                -- metric: "Max CapEx" is a ceiling just as "Max Total Leverage"
                -- is, while "Min Interest Coverage" is a floor. This rule
                -- reproduces every stored HEADROOM_PCT to within rounding.
                ROUND(CASE
                    WHEN COVENANTTYPE ILIKE 'Max%'
                        THEN (COVENANTTHRESHOLD - actual_value) / NULLIF(COVENANTTHRESHOLD, 0) * 100
                    ELSE (actual_value - COVENANTTHRESHOLD) / NULLIF(COVENANTTHRESHOLD, 0) * 100
                END, 2) AS HEADROOM_PCT
            FROM projected
        ) AS src
        ON tgt.BORROWERID = src.BORROWERID
       AND TRY_TO_DATE(tgt.TESTDATE) = TRY_TO_DATE(src.TESTDATE)
       AND tgt.COVENANTTYPE = src.COVENANTTYPE
        WHEN NOT MATCHED THEN INSERT (
            BORROWERID, BORROWERNAME, FACILITYID, TESTDATE, COVENANTTYPE,
            COVENANTTHRESHOLD, ACTUALVALUE, HEADROOM_PCT, STATUS, BREACHFLAG,
            WAIVERREQUESTED, WAIVERGRANTED, EQUITYCUREAVAILABLE, NOTES
        ) VALUES (
            src.BORROWERID, src.BORROWERNAME, src.FACILITYID, src.TESTDATE,
            src.COVENANTTYPE, src.COVENANTTHRESHOLD, src.ACTUALVALUE,
            src.HEADROOM_PCT,
            -- A borrower already under a waiver or equity cure keeps that label
            -- while it stays underwater; only a newly negative test becomes a
            -- raw 'Breach'. Collapsing every negative into 'Breach' would jump
            -- the book's breach count from 2 to 21 overnight.
            CASE
                WHEN src.HEADROOM_PCT < 0 THEN
                    CASE WHEN src.prior_status IN ('Equity Cure', 'Waiver Granted', 'Breach')
                         THEN src.prior_status ELSE 'Breach' END
                WHEN src.HEADROOM_PCT < 12 THEN 'Tight'
                ELSE 'Compliant'
            END,
            CASE WHEN src.HEADROOM_PCT < 0 THEN TRUE ELSE FALSE END,
            CASE WHEN src.HEADROOM_PCT < 0
                  AND src.prior_status IN ('Equity Cure', 'Waiver Granted')
                 THEN TRUE ELSE FALSE END,
            CASE WHEN src.HEADROOM_PCT < 0 AND src.prior_status = 'Waiver Granted'
                 THEN TRUE ELSE FALSE END,
            CASE WHEN src.HEADROOM_PCT < 0 THEN TRUE ELSE FALSE END,
            CASE
                WHEN src.HEADROOM_PCT < 0 THEN
                    'Covenant breached at ' || src.TESTDATE ||
                    '; equity cure available, waiver not yet requested.'
                WHEN src.HEADROOM_PCT < 12 THEN
                    'Headroom under 12% at ' || src.TESTDATE || '; on watch list.'
                ELSE 'Covenant satisfied at ' || src.TESTDATE || '.'
            END
        )
    """).collect()
    inserted = rows[0][0] if rows else 0
    log_detail(f"  Covenant tests: +{inserted} quarterly rows")
    return inserted


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def refresh_private_markets(session: Session, as_of: date) -> Dict[str, Any]:
    """Advance the private-markets facts, then regenerate their documents.

    The corpus builders are only re-invoked when a new fact period actually
    landed. They are relatively expensive (they render document text for every
    borrower and portfolio company) and on ~11 weeks in 12 there is nothing new
    to say, so running them every week would be wasted compute.
    """
    log_substep("Advancing private markets (PE and private credit)")
    cadence_cleanup = enforce_quarterly_cadence(session)
    summary: Dict[str, Any] = {
        # Cheap no-op once the history exists, and it repairs the single-period
        # KPI table on the first run after an older build.
        'kpi_history': backfill_portfolio_company_kpis(session),
        'kpis': extend_portfolio_company_kpis(session, as_of),
        'board_pack_metrics': extend_board_pack_metrics(session, as_of),
        'credit_financials': extend_credit_financials(session, as_of),
    }
    # Covenants depend on the financials existing for the new quarter.
    summary['covenant_tests'] = extend_covenant_tracking(session, as_of)
    summary['leverage_aligned'] = align_borrower_leverage(session)
    summary['coverage_aligned'] = align_borrower_interest_coverage(session)

    new_facts = sum(
        v for v in summary.values() if isinstance(v, int)
    ) + sum(cadence_cleanup.values())
    summary['cadence_cleanup'] = cadence_cleanup
    if not new_facts:
        log_detail("  No new private-markets period - documents unchanged")
        summary['documents_rebuilt'] = False
        return summary

    from data import structured

    # Some corpus builders issue unqualified DDL (e.g. DROP on a temp object),
    # which fails with "This session does not have a current database" when the
    # caller only set role and warehouse. The weekly task runs in exactly that
    # state, so set the database here rather than relying on the caller.
    try:
        session.sql(f"USE DATABASE {_db()}").collect()
        session.sql(f"USE SCHEMA {config.DATABASE['schemas']['curated']}").collect()
    except Exception as exc:
        log_warning(f"  could not set current database/schema: {str(exc)[:120]}")

    rebuilt = []
    # Corpus table -> the Cortex Search service that reads it. The builders use
    # CREATE OR REPLACE, which destroys the table the service is indexing and
    # leaves the service SUSPENDED (serving stale rows, silently missing
    # everything new). Resuming is therefore part of regenerating, not an
    # afterthought - otherwise the weekly run would break search every time it
    # refreshed a corpus.
    services = {
        'pe_board_packs': 'SAM_PE_BOARD_PACKS',
        'compliance_certs': 'SAM_COMPLIANCE_CERTS',
    }
    for name, fn in (
        ('pe_board_packs', 'build_pe_board_packs_corpus'),
        ('compliance_certs', 'build_compliance_certs_corpus'),
    ):
        builder = getattr(structured, fn, None)
        if builder is None:
            log_warning(f"  builder {fn} not found, skipped")
            continue
        try:
            builder(session)
            rebuilt.append(name)
        except Exception as exc:
            log_warning(f"  {name} regeneration failed: {str(exc)[:160]}")
            continue

        service = services.get(name)
        if service:
            try:
                session.sql(
                    f"ALTER CORTEX SEARCH SERVICE {config.DATABASE['name']}."
                    f"{config.DATABASE['schemas']['ai']}.{service} RESUME INDEXING"
                ).collect()
                log_detail(f"  resumed search service {service}")
            except Exception as exc:
                log_warning(
                    f"  could not resume {service}: {str(exc)[:160]}. "
                    "New documents will not be searchable until it is resumed."
                )
    summary['documents_rebuilt'] = rebuilt
    return summary
