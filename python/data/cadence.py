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
"""Document cadence: decide whether a document type owes a new vintage this run.

The weekly refresh must not regenerate every document every week. A quarterly
report that gains a new vintage seven days after the last one is not a realistic
corpus, and it inflates the search index with near-duplicates that make
"what changed" unanswerable. So each document type declares a cadence in
documents.yaml and this module evaluates it:

    weekly        every run
    monthly       last week of a calendar month
    quarterly     last week of a calendar quarter
    semi_annual   last week of June or December
    annual        last week of December
    event_driven  any declared trigger fires

Event triggers are what make the corpus feel real: broker research appears
because the company filed, the stock moved, or the house view changed - not
because a timer elapsed. `rating_threshold_crossed` is why FACT_RECOMMENDATION
must be built *before* cadence is evaluated for a run.

`min_days_between` then suppresses churn on names that trigger repeatedly, by
anti-joining the vintage ledger.

Evaluation is bulk by design: one query per trigger for the whole entity list
rather than one per entity, per the project's I/O rules.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from snowflake.snowpark import Session

import config
from utils.logging import log_detail, log_substep, log_warning

# Reporting lag proxy. FACT_SEC_FINANCIALS carries PERIOD_END_DATE but no filing
# date, so "a filing became available this week" is approximated as the period
# having ended this long ago. 35 days is the typical 10-Q gap and sits inside the
# 21-75 day window the document date generator already assumes.
_FILING_LAG_DAYS = 35

_CALENDAR_PERIODS = {'weekly', 'monthly', 'quarterly', 'semi_annual', 'annual'}

# Ratings whose crossing counts as a material change of view. A move within the
# buy side (Strong Buy -> Buy) is not worth a new document; crossing into or out
# of Hold, or flipping side, is.
_STANCE_OF = config.RATING_TO_STANCE


def _as_date(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ('%Y-%m-%d', '%d %B %Y'):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _is_last_week_of_month(as_of: date) -> bool:
    """True when as_of falls in the final seven days of its calendar month."""
    if as_of.month == 12:
        next_month_start = date(as_of.year + 1, 1, 1)
    else:
        next_month_start = date(as_of.year, as_of.month + 1, 1)
    return (next_month_start - as_of).days <= 7


def is_calendar_period_due(period: str, as_of: date) -> bool:
    """Whether a calendar-driven cadence is due on this run date."""
    if period == 'weekly':
        return True
    if not _is_last_week_of_month(as_of):
        return False
    if period == 'monthly':
        return True
    if period == 'quarterly':
        return as_of.month in (3, 6, 9, 12)
    if period == 'semi_annual':
        return as_of.month in (6, 12)
    if period == 'annual':
        return as_of.month == 12
    return False


def ensure_tables(session: Session) -> None:
    """Create the vintage ledger and refresh watermark if absent.

    IF NOT EXISTS rather than CREATE OR REPLACE: these accumulate history across
    runs, and replacing them would erase the very ledger that makes the refresh
    idempotent.
    """
    database = config.DATABASE['name']
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {database}.RAW.DOCUMENT_VINTAGE_LOG (
            DOC_TYPE VARCHAR NOT NULL,
            ENTITY_ID VARCHAR NOT NULL,
            VINTAGE_DATE DATE NOT NULL,
            DOCUMENT_ID VARCHAR,
            TRIGGER_REASON VARCHAR,
            RATING VARCHAR,
            PRIOR_RATING VARCHAR,
            RATING_ACTION VARCHAR,
            PRICE_TARGET NUMBER(18,2),
            CLOSE_PRICE NUMBER(18,2),
            UPSIDE_PCT NUMBER(9,4),
            GENERATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PRIMARY KEY (DOC_TYPE, ENTITY_ID, VINTAGE_DATE)
        )
        COMMENT = 'One row per document vintage. Doubles as the rating-history table the codebase otherwise lacks, and enforces min_days_between for event-driven cadences.'
    """).collect()

    config_db = config.RBAC['shared_database']
    app_schema = config.RBAC['shared_schemas']['app']
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {config_db}.{app_schema}").collect()
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {config_db}.{app_schema}.REFRESH_STATE (
            REFRESH_KEY VARCHAR PRIMARY KEY,
            LAST_DATE DATE,
            LAST_RUN_AT TIMESTAMP_NTZ,
            STATUS VARCHAR
        )
        COMMENT = 'Watermark per refresh stream, so a rerun resumes rather than reprocessing from the beginning.'
    """).collect()


# ---------------------------------------------------------------------------
# Trigger evaluation (bulk)
# ---------------------------------------------------------------------------

def _securities_with_price_move(
    session: Session, security_ids: List[int], week_start: date, week_end: date,
    threshold_pct: float,
) -> Set[int]:
    """SecurityIDs whose close-to-close move over the window met the threshold."""
    if not security_ids:
        return set()
    id_list = ', '.join(str(int(s)) for s in security_ids)
    rows = session.sql(f"""
        WITH wk AS (
            SELECT SecurityID,
                   FIRST_VALUE(PRICE_CLOSE) OVER (
                       PARTITION BY SecurityID ORDER BY PRICE_DATE
                   ) AS open_px,
                   LAST_VALUE(PRICE_CLOSE) OVER (
                       PARTITION BY SecurityID ORDER BY PRICE_DATE
                       ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                   ) AS close_px
            FROM {config.DATABASE['name']}.MARKET_DATA.FACT_STOCK_PRICES
            WHERE PRICE_DATE BETWEEN '{week_start}'::DATE AND '{week_end}'::DATE
              AND SecurityID IN ({id_list})
        )
        SELECT DISTINCT SecurityID
        FROM wk
        WHERE ABS((close_px - open_px) / NULLIF(open_px, 0)) * 100 >= {threshold_pct}
    """).collect()
    return {row['SECURITYID'] for row in rows}


def _securities_with_new_filing(
    session: Session, security_ids: List[int], week_start: date, week_end: date,
) -> Set[int]:
    """SecurityIDs whose issuer had a filing period become reportable this window.

    Approximated as PERIOD_END_DATE + _FILING_LAG_DAYS landing in the window,
    because the source table has no filing date.
    """
    if not security_ids:
        return set()
    id_list = ', '.join(str(int(s)) for s in security_ids)
    rows = session.sql(f"""
        SELECT DISTINCT ds.SecurityID
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY ds
        JOIN {config.DATABASE['name']}.MARKET_DATA.FACT_SEC_FINANCIALS sf
          ON sf.IssuerID = ds.IssuerID
        WHERE ds.SecurityID IN ({id_list})
          AND sf.PERIOD_TYPE IN ('annual', 'quarterly')
          AND DATEADD('day', {_FILING_LAG_DAYS}, sf.PERIOD_END_DATE)
              BETWEEN '{week_start}'::DATE AND '{week_end}'::DATE
    """).collect()
    return {row['SECURITYID'] for row in rows}


def _securities_with_rating_change(
    session: Session, security_ids: List[int], as_of: date,
) -> Set[int]:
    """SecurityIDs whose latest recommendation vintage changed the house stance.

    Only a stance change counts - crossing into or out of Hold, or flipping
    side. Strong Buy to Buy is a nuance, not news, and treating it as a trigger
    would republish research constantly on volatile names.
    """
    if not security_ids:
        return set()
    id_list = ', '.join(str(int(s)) for s in security_ids)
    rows = session.sql(f"""
        WITH latest AS (
            SELECT SecurityID, Rating, PriorRating,
                   ROW_NUMBER() OVER (
                       PARTITION BY SecurityID ORDER BY VintageDate DESC
                   ) AS rn
            FROM {config.DATABASE['name']}.CURATED.FACT_RECOMMENDATION
            WHERE SecurityID IN ({id_list})
              AND VintageDate <= '{as_of}'::DATE
        )
        SELECT SecurityID, Rating, PriorRating
        FROM latest
        WHERE rn = 1 AND PriorRating IS NOT NULL AND Rating <> PriorRating
    """).collect()

    changed = set()
    for row in rows:
        before = _STANCE_OF.get(row['PRIORRATING'])
        after = _STANCE_OF.get(row['RATING'])
        if before and after and before != after:
            changed.add(row['SECURITYID'])
    return changed


def _last_vintage_by_entity(
    session: Session, doc_type: str,
) -> Dict[str, date]:
    """Most recent logged vintage per entity, for min_days_between."""
    database = config.DATABASE['name']
    exists = session.sql(f"""
        SELECT COUNT(*) AS n
        FROM {database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'RAW' AND TABLE_NAME = 'DOCUMENT_VINTAGE_LOG'
    """).collect()[0]['N']
    if not exists:
        return {}
    rows = session.sql(f"""
        SELECT ENTITY_ID, MAX(VINTAGE_DATE) AS LAST_VINTAGE
        FROM {database}.RAW.DOCUMENT_VINTAGE_LOG
        WHERE DOC_TYPE = '{doc_type}'
        GROUP BY ENTITY_ID
    """).collect()
    return {row['ENTITY_ID']: _as_date(row['LAST_VINTAGE']) for row in rows}


def evaluate_cadence(
    session: Session,
    doc_type: str,
    entities: Iterable[Dict[str, Any]],
    as_of_date: Any,
) -> Dict[Any, Tuple[bool, Optional[date], str]]:
    """Decide, for every entity at once, whether a new vintage is due.

    Returns entity_id -> (should_generate, vintage_date, trigger_reason).
    """
    as_of = _as_date(as_of_date)
    if as_of is None:
        raise ValueError(f"Unusable as_of_date for cadence: {as_of_date!r}")

    entity_list = list(entities)
    cadence = (config.DOCUMENT_TYPES.get(doc_type) or {}).get('cadence') or {}
    period = cadence.get('period')
    if not period:
        log_warning(
            f"  {doc_type} declares no cadence - treating as weekly. Add a "
            "cadence block to documents.yaml."
        )
        period = 'weekly'

    # Calendar cadences are a single decision for the whole doc type: no SQL.
    if period in _CALENDAR_PERIODS:
        due = is_calendar_period_due(period, as_of)
        reason = f'{period}_period_elapsed' if due else f'{period}_not_due'
        return {e['id']: (due, as_of if due else None, reason) for e in entity_list}

    if period != 'event_driven':
        log_warning(f"  {doc_type} has unknown cadence period '{period}' - skipping")
        return {e['id']: (False, None, f'unknown_period_{period}') for e in entity_list}

    # Event-driven: evaluate each declared trigger in bulk.
    triggers = cadence.get('triggers') or []

    # A source: real doc type is ingested from the marketplace rather than
    # generated, so it is never "due" here. Say so explicitly - otherwise it is
    # indistinguishable from a trigger that simply did not fire, and a genuinely
    # misconfigured doc type with no triggers would hide behind the same reason.
    if cadence.get('source') == 'real':
        return {e['id']: (False, None, 'source_real_not_generated') for e in entity_list}
    if not triggers:
        log_warning(
            f"  {doc_type} is event_driven but declares no triggers, so it will "
            "never generate. Add triggers or change the period in documents.yaml."
        )
        return {e['id']: (False, None, 'event_driven_no_triggers') for e in entity_list}
    security_ids = [e['id'] for e in entity_list if isinstance(e.get('id'), int)]
    week_start = as_of - timedelta(days=6)

    fired: Dict[Any, List[str]] = {e['id']: [] for e in entity_list}

    if 'price_move_gt_pct' in triggers:
        threshold = float(cadence.get('price_move_threshold_pct', 7.0))
        for sid in _securities_with_price_move(
            session, security_ids, week_start, as_of, threshold
        ):
            if sid in fired:
                fired[sid].append('price_move_gt_pct')

    if 'new_earnings_filing' in triggers or 'new_sec_filing' in triggers:
        label = 'new_earnings_filing' if 'new_earnings_filing' in triggers else 'new_sec_filing'
        for sid in _securities_with_new_filing(session, security_ids, week_start, as_of):
            if sid in fired:
                fired[sid].append(label)

    if 'rating_threshold_crossed' in triggers:
        for sid in _securities_with_rating_change(session, security_ids, as_of):
            if sid in fired:
                fired[sid].append('rating_threshold_crossed')

    # Triggers with no data source yet. Declared in documents.yaml so the intent
    # is recorded, but they never fire, and saying so beats silently ignoring them.
    unsupported = {'corporate_action', 'counterparty_change', 'mandate_change'}
    declared_unsupported = unsupported.intersection(triggers)
    if declared_unsupported:
        log_detail(
            f"  {doc_type}: triggers {sorted(declared_unsupported)} have no data "
            "source and never fire"
        )

    min_days = cadence.get('min_days_between')
    last_vintage = _last_vintage_by_entity(session, doc_type) if min_days else {}

    result: Dict[Any, Tuple[bool, Optional[date], str]] = {}
    suppressed = 0
    for entity in entity_list:
        entity_id = entity['id']
        reasons = fired.get(entity_id) or []
        if not reasons:
            result[entity_id] = (False, None, 'no_trigger')
            continue
        if min_days:
            previous = last_vintage.get(str(entity_id))
            if previous and (as_of - previous).days < int(min_days):
                result[entity_id] = (
                    False, None,
                    f'suppressed_min_days_between_{min_days}'
                )
                suppressed += 1
                continue
        result[entity_id] = (True, as_of, '+'.join(sorted(reasons)))

    due_count = sum(1 for v in result.values() if v[0])
    log_detail(
        f"  {doc_type}: {due_count}/{len(entity_list)} due"
        + (f", {suppressed} suppressed by min_days_between" if suppressed else "")
    )
    return result


def is_vintage_due(
    session: Session,
    doc_type: str,
    entity: Dict[str, Any],
    as_of_date: Any,
) -> Tuple[bool, Optional[date], str]:
    """Single-entity cadence check.

    Prefer evaluate_cadence for a whole entity list - this issues the same
    queries for one entity, so calling it in a loop is the N+1 pattern the
    project's I/O rules exist to prevent.
    """
    return evaluate_cadence(session, doc_type, [entity], as_of_date)[entity['id']]


def log_vintages(
    session: Session,
    doc_type: str,
    records: List[Dict[str, Any]],
) -> int:
    """Record generated vintages in the ledger, idempotently.

    MERGE rather than INSERT so re-running a vintage updates in place instead of
    duplicating, which is what lets the weekly refresh be safely retried.
    """
    if not records:
        return 0

    database = config.DATABASE['name']
    values = []
    for r in records:
        def _sql_str(key: str) -> str:
            value = r.get(key)
            if value is None:
                return 'NULL'
            return "'" + str(value).replace("'", "''") + "'"

        def _sql_num(key: str) -> str:
            value = r.get(key)
            return 'NULL' if value is None else str(float(value))

        values.append(
            f"('{doc_type}', '{r['entity_id']}', '{r['vintage_date']}'::DATE, "
            f"{_sql_str('document_id')}, {_sql_str('trigger_reason')}, "
            f"{_sql_str('rating')}, {_sql_str('prior_rating')}, "
            f"{_sql_str('rating_action')}, {_sql_num('price_target')}, "
            f"{_sql_num('close_price')}, {_sql_num('upside_pct')})"
        )

    session.sql(f"""
        MERGE INTO {database}.RAW.DOCUMENT_VINTAGE_LOG AS tgt
        USING (
            SELECT * FROM VALUES {', '.join(values)}
            AS v (DOC_TYPE, ENTITY_ID, VINTAGE_DATE, DOCUMENT_ID, TRIGGER_REASON,
                  RATING, PRIOR_RATING, RATING_ACTION, PRICE_TARGET, CLOSE_PRICE,
                  UPSIDE_PCT)
        ) AS src
        ON tgt.DOC_TYPE = src.DOC_TYPE
       AND tgt.ENTITY_ID = src.ENTITY_ID
       AND tgt.VINTAGE_DATE = src.VINTAGE_DATE
        WHEN MATCHED THEN UPDATE SET
            DOCUMENT_ID = src.DOCUMENT_ID,
            TRIGGER_REASON = src.TRIGGER_REASON,
            RATING = src.RATING,
            PRIOR_RATING = src.PRIOR_RATING,
            RATING_ACTION = src.RATING_ACTION,
            PRICE_TARGET = src.PRICE_TARGET,
            CLOSE_PRICE = src.CLOSE_PRICE,
            UPSIDE_PCT = src.UPSIDE_PCT
        WHEN NOT MATCHED THEN INSERT
            (DOC_TYPE, ENTITY_ID, VINTAGE_DATE, DOCUMENT_ID, TRIGGER_REASON,
             RATING, PRIOR_RATING, RATING_ACTION, PRICE_TARGET, CLOSE_PRICE,
             UPSIDE_PCT)
        VALUES
            (src.DOC_TYPE, src.ENTITY_ID, src.VINTAGE_DATE, src.DOCUMENT_ID,
             src.TRIGGER_REASON, src.RATING, src.PRIOR_RATING, src.RATING_ACTION,
             src.PRICE_TARGET, src.CLOSE_PRICE, src.UPSIDE_PCT)
    """).collect()
    return len(records)




def get_watermark(session: Session, refresh_key: str) -> Optional[date]:
    """Last successfully processed date for a refresh stream."""
    config_db = config.RBAC['shared_database']
    app_schema = config.RBAC['shared_schemas']['app']
    rows = session.sql(f"""
        SELECT LAST_DATE FROM {config_db}.{app_schema}.REFRESH_STATE
        WHERE REFRESH_KEY = '{refresh_key}'
    """).collect()
    return _as_date(rows[0]['LAST_DATE']) if rows else None


def set_watermark(
    session: Session, refresh_key: str, last_date: Any, status: str = 'SUCCESS',
) -> None:
    """Advance a refresh watermark."""
    config_db = config.RBAC['shared_database']
    app_schema = config.RBAC['shared_schemas']['app']
    session.sql(f"""
        MERGE INTO {config_db}.{app_schema}.REFRESH_STATE AS tgt
        USING (SELECT '{refresh_key}' AS REFRESH_KEY,
                      '{_as_date(last_date)}'::DATE AS LAST_DATE,
                      '{status}' AS STATUS) AS src
        ON tgt.REFRESH_KEY = src.REFRESH_KEY
        WHEN MATCHED THEN UPDATE SET
            LAST_DATE = src.LAST_DATE,
            LAST_RUN_AT = CURRENT_TIMESTAMP(),
            STATUS = src.STATUS
        WHEN NOT MATCHED THEN INSERT
            (REFRESH_KEY, LAST_DATE, LAST_RUN_AT, STATUS)
        VALUES
            (src.REFRESH_KEY, src.LAST_DATE, CURRENT_TIMESTAMP(), src.STATUS)
    """).collect()
