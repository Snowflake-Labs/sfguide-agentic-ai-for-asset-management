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
"""Keep the middle office moving with the rest of the demo.

NAV calculations and custodian reconciliations were produced only by the full
build, so the operations scenario drifted out of step: positions and trades
advanced every week while the NAV struck for those positions stayed where the
last build left it. Within a month an operations analyst would be looking at a
NAV that predated the holdings it was supposed to value.

The full builders cannot simply be re-run weekly - they are CREATE OR REPLACE and
seeded with RANDOM(), so every run would rewrite five years of history with
different anomalies and break flags. These extensions append only the periods
that are genuinely missing, deriving values from the positions actually held and
using HASH-based selection so a rerun is idempotent.
"""

from datetime import date
from typing import Any, Dict, Optional

from snowflake.snowpark import Session

import config
from utils.logging import log_detail, log_substep, log_warning


def _cur() -> str:
    return f"{config.DATABASE['name']}.{config.DATABASE['schemas']['curated']}"


def _scalar(session: Session, sql: str):
    rows = session.sql(sql).collect()
    return rows[0][0] if rows else None


def _as_date(value) -> Optional[date]:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def extend_nav_calculations(session: Session, as_of: date) -> int:
    """Strike a NAV for every position date that does not have one yet.

    NAV is derived from the positions held on that date - total assets less a
    0.1% liability accrual, over a fixed 100m shares - which is the same
    relationship the full builder uses, so the extended rows are continuous with
    the history rather than a different series bolted on the end.
    """
    cur = _cur()
    latest = _as_date(_scalar(
        session, f"SELECT MAX(CALCULATIONDATE) FROM {cur}.FACT_NAV_CALCULATION"
    ))
    if latest is None:
        log_warning("  FACT_NAV_CALCULATION is empty - run the full build first")
        return 0

    next_id = _scalar(session, f"SELECT COALESCE(MAX(NAVID), 0) FROM {cur}.FACT_NAV_CALCULATION")

    rows = session.sql(f"""
        MERGE INTO {cur}.FACT_NAV_CALCULATION AS tgt
        USING (
            WITH due AS (
                SELECT HOLDINGDATE, PORTFOLIOID, SUM(MARKETVALUE_BASE) AS total_assets
                FROM {cur}.FACT_POSITION_DAILY_ABOR
                WHERE HOLDINGDATE > '{latest}'::DATE
                  AND HOLDINGDATE <= '{as_of}'::DATE
                GROUP BY HOLDINGDATE, PORTFOLIOID
            )
            SELECT
                {int(next_id)} + ROW_NUMBER() OVER (ORDER BY HOLDINGDATE, PORTFOLIOID) AS NAVID,
                HOLDINGDATE AS CALCULATIONDATE,
                PORTFOLIOID,
                total_assets AS TOTALASSETS,
                total_assets * 0.001 AS TOTALLIABILITIES,
                total_assets * 0.999 AS NETASSETS,
                100000000 AS SHARESOUTSTANDING,
                (total_assets * 0.999) / 100000000.0 AS NAVPERSHARE,
                -- Roughly 1 in 30 strikes lands in review, picked by hash so the
                -- same date always produces the same outcome.
                CASE WHEN MOD(ABS(HASH(PORTFOLIOID || '|nav|' ||
                        TO_VARCHAR(HOLDINGDATE))), 30) = 0
                     THEN 'Pending Review' ELSE 'Calculated' END AS CALCULATIONSTATUS,
                CASE WHEN MOD(ABS(HASH(PORTFOLIOID || '|anom|' ||
                        TO_VARCHAR(HOLDINGDATE))), 50) = 0
                     THEN 'NAV change >2% from prior period' END AS ANOMALIESDETECTED,
                CASE WHEN MOD(ABS(HASH(PORTFOLIOID || '|nav|' ||
                        TO_VARCHAR(HOLDINGDATE))), 30) = 0
                     THEN 'Pending' ELSE 'Approved' END AS APPROVALSTATUS,
                CASE WHEN MOD(ABS(HASH(PORTFOLIOID || '|nav|' ||
                        TO_VARCHAR(HOLDINGDATE))), 30) = 0
                     THEN NULL ELSE 'Operations Manager' END AS APPROVEDBY
            FROM due
        ) AS src
        ON tgt.CALCULATIONDATE = src.CALCULATIONDATE
       AND tgt.PORTFOLIOID = src.PORTFOLIOID
        WHEN NOT MATCHED THEN INSERT (
            NAVID, CALCULATIONDATE, PORTFOLIOID, NAVPERSHARE, TOTALASSETS,
            TOTALLIABILITIES, NETASSETS, SHARESOUTSTANDING, CALCULATIONSTATUS,
            ANOMALIESDETECTED, APPROVALSTATUS, APPROVEDBY
        ) VALUES (
            src.NAVID, src.CALCULATIONDATE, src.PORTFOLIOID, src.NAVPERSHARE,
            src.TOTALASSETS, src.TOTALLIABILITIES, src.NETASSETS,
            src.SHARESOUTSTANDING, src.CALCULATIONSTATUS, src.ANOMALIESDETECTED,
            src.APPROVALSTATUS, src.APPROVEDBY
        )
    """).collect()
    inserted = rows[0][0] if rows else 0
    log_detail(f"  NAV calculations: +{inserted} strikes")
    return inserted


def extend_reconciliation(session: Session, as_of: date) -> int:
    """Raise custodian reconciliation breaks for new position dates.

    Breaks are rare and are drawn from positions actually held, so the securities
    named in a break are ones the portfolio owns - which is what makes the
    operations scenario's "investigate this break" line of questioning work.
    """
    cur = _cur()
    latest = _as_date(_scalar(
        session, f"SELECT MAX(RECONCILIATIONDATE) FROM {cur}.FACT_RECONCILIATION"
    ))
    if latest is None:
        log_warning("  FACT_RECONCILIATION is empty - run the full build first")
        return 0

    next_id = _scalar(session, f"SELECT COALESCE(MAX(RECONCILIATIONID), 0) FROM {cur}.FACT_RECONCILIATION")

    rows = session.sql(f"""
        MERGE INTO {cur}.FACT_RECONCILIATION AS tgt
        USING (
            WITH candidates AS (
                SELECT HOLDINGDATE, PORTFOLIOID, SECURITYID, MARKETVALUE_BASE
                FROM {cur}.FACT_POSITION_DAILY_ABOR
                WHERE HOLDINGDATE > '{latest}'::DATE
                  AND HOLDINGDATE <= '{as_of}'::DATE
            ), breaks AS (
                -- About 1 position in 40 breaks, chosen deterministically.
                SELECT c.*,
                       MOD(ABS(HASH(c.PORTFOLIOID || '|' || c.SECURITYID || '|rec|' ||
                           TO_VARCHAR(c.HOLDINGDATE))), 40) AS pick,
                       MOD(ABS(HASH(c.SECURITYID || '|brk|' ||
                           TO_VARCHAR(c.HOLDINGDATE))), 3) AS kind,
                       (MOD(ABS(HASH(c.PORTFOLIOID || '|diff|' || c.SECURITYID)), 400)
                           / 10000.0) + 0.0005 AS diff_frac
                FROM candidates c
            )
            SELECT
                {int(next_id)} + ROW_NUMBER() OVER (
                    ORDER BY HOLDINGDATE, PORTFOLIOID, SECURITYID) AS RECONCILIATIONID,
                HOLDINGDATE AS RECONCILIATIONDATE, PORTFOLIOID, SECURITYID,
                -- The table already uses a terse three-value vocabulary
                -- (Position / Cash / Price) in an 8-character column, so use
                -- exactly those rather than inventing longer labels.
                CASE kind WHEN 0 THEN 'Price'
                          WHEN 1 THEN 'Position'
                          ELSE 'Cash' END AS BREAKTYPE,
                MARKETVALUE_BASE AS INTERNALVALUE,
                MARKETVALUE_BASE * (1 - diff_frac) AS CUSTODIANVALUE,
                MARKETVALUE_BASE * diff_frac AS DIFFERENCE,
                CASE MOD(ABS(HASH(PORTFOLIOID || '|st|' || SECURITYID ||
                        TO_VARCHAR(HOLDINGDATE))), 3)
                     WHEN 0 THEN 'Open' WHEN 1 THEN 'Investigating'
                     ELSE 'Resolved' END AS STATUS
            FROM breaks
            WHERE pick = 0
        ) AS src
        ON tgt.RECONCILIATIONDATE = src.RECONCILIATIONDATE
       AND tgt.PORTFOLIOID = src.PORTFOLIOID
       AND tgt.SECURITYID = src.SECURITYID
        WHEN NOT MATCHED THEN INSERT (
            RECONCILIATIONID, RECONCILIATIONDATE, PORTFOLIOID, SECURITYID,
            BREAKTYPE, INTERNALVALUE, CUSTODIANVALUE, DIFFERENCE, STATUS,
            RESOLUTIONDATE, RESOLUTIONNOTES
        ) VALUES (
            src.RECONCILIATIONID, src.RECONCILIATIONDATE, src.PORTFOLIOID,
            src.SECURITYID, src.BREAKTYPE, src.INTERNALVALUE, src.CUSTODIANVALUE,
            src.DIFFERENCE, src.STATUS,
            CASE WHEN src.STATUS = 'Resolved'
                 THEN DATEADD('day', 2, src.RECONCILIATIONDATE) END,
            CASE WHEN src.STATUS = 'Resolved'
                 THEN 'Agreed with custodian; internal record adjusted.' END
        )
    """).collect()
    inserted = rows[0][0] if rows else 0
    log_detail(f"  Reconciliation breaks: +{inserted} rows")
    return inserted


def refresh_middle_office(session: Session, as_of: date) -> Dict[str, Any]:
    """Advance NAV and reconciliation to match the latest positions."""
    log_substep("Extending middle office...")
    return {
        'nav_calculations': extend_nav_calculations(session, as_of),
        'reconciliation_breaks': extend_reconciliation(session, as_of),
    }
