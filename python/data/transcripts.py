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
Real Company Event Transcripts Integration for SAM Demo

Pipeline-only architecture:
1. load_raw_table() loads transcripts from REAL_DATA_SOURCES into COMPANY_EVENT_TRANSCRIPTS_RAW
2. Stream on RAW table triggers pipeline task DAG
3. Pipeline executes speaker mapping and corpus build tasks

The load is idempotent — a MERGE that inserts only transcripts not already present — so the
same function serves both the initial build and the weekly refresh.

Covers: Earnings Calls, AGMs, M&A Announcements, Investor Days, Special Calls.
Uses AI_COMPLETE for speaker identification and SPLIT_TEXT_RECURSIVE_CHARACTER for chunking.

Filtering:
- Companies: Filtered by joining to DIM_ISSUER on PROVIDER_COMPANY_ID
- Date range: Filtered by YEARS_OF_HISTORY from config
- Transcript type: Prefers SPEAKERS_ANNOTATED over RAW to avoid loading the same event
  twice. For Earnings Calls this is enforced in the WHERE clause; for other event types both
  versions exist in the source with identical paragraph counts, so the preference is applied
  in the row-ranking instead.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_step, log_substep, log_detail, log_warning, log_error, log_phase_complete
from utils.snowflake import verify_table_access


def load_raw_table(session: Session, test_mode: bool = False, since: str = None) -> int:
    """
    Load real transcripts into COMPANY_EVENT_TRANSCRIPTS_RAW table.
    This triggers the TRANSCRIPTS_SPEAKER_STREAM and TRANSCRIPTS_CORPUS_STREAM for pipeline processing.

    Pipeline-only architecture: This function ONLY loads to RAW table.
    The pipeline DAG handles speaker mapping and corpus build.

    Safe to call repeatedly. The load is a MERGE keyed on the event itself — company plus
    event timestamp — so running it again adds only events that are not already present and
    leaves existing ones untouched. That is what lets the weekly refresh reuse the same
    loader as the initial build.

    The match is on the event rather than on TRANSCRIPT_ID deliberately. TRANSCRIPT_ID is a
    surrogate built from CIK, event timestamp AND transcript type, so it changes when a
    different type is selected for the same event. Matching on it would make the loader
    re-insert an event it already holds simply because the type preference picked the other
    version, which is how the same call ended up in the table twice.

    Existing rows are deliberately never updated. The downstream pipeline tasks read
    TRANSCRIPT_IDs from the stream and INSERT into the speaker-mapping and corpus tables
    with no matching delete, so touching a row that has already been processed would
    duplicate its paragraphs and chunks downstream rather than replace them. Revised
    transcripts are therefore not re-ingested; picking those up would need the downstream
    tasks to replace rather than append.

    Args:
        session: Active Snowpark session
        test_mode: If True, limit records for faster testing
        since: Optional 'YYYY-MM-DD'. Narrows the source scan to transcripts created or
            revised on or after this date, using the source UPDATED_AT column. This is a
            performance optimisation for the weekly refresh, not a correctness boundary -
            leaving it None scans the full YEARS_OF_HISTORY window, which is the safe
            default for an initial build.

    Returns:
        Number of transcripts actually inserted by this call (0 when already up to date)
    """
    database_name = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    curated_schema = config.DATABASE['schemas']['curated']
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    
    raw_table = f"{database_name}.{raw_schema}.COMPANY_EVENT_TRANSCRIPTS_RAW"
    dim_issuer_table = f"{database_name}.{curated_schema}.DIM_ISSUER"
    years_of_history = config.YEARS_OF_HISTORY
    
    log_substep("Loading real transcripts to RAW table")

    # Limit for test mode
    limit_clause = "LIMIT 50" if test_mode else ""

    # Optional incremental narrowing. UPDATED_AT covers both newly published transcripts
    # and revisions to existing ones.
    since_clause = f"AND t.UPDATED_AT >= '{since}'::TIMESTAMP_NTZ" if since else ""

    # Table and streams already exist from create_transcripts_pipeline().
    # MERGE rather than INSERT so the loader is idempotent — see the docstring for why
    # there is no WHEN MATCHED branch.
    dim_security_table = f"{database_name}.{curated_schema}.DIM_SECURITY"

    load_sql = f"""
    MERGE INTO {raw_table} AS tgt
    USING (
        WITH candidates AS (
            SELECT
                MD5(CONCAT(t.CIK, t.EVENT_TIMESTAMP::VARCHAR, COALESCE(t.TRANSCRIPT_TYPE, ''))) AS TRANSCRIPT_ID,
                t.COMPANY_ID,
                t.CIK,
                t.COMPANY_NAME,
                t.PRIMARY_TICKER,
                t.EVENT_TYPE,
                t.EVENT_TIMESTAMP,
                IFF(t.FISCAL_PERIOD = 'None', NULL, t.FISCAL_PERIOD) AS FISCAL_PERIOD,
                IFF(t.FISCAL_YEAR = 'None', NULL, t.FISCAL_YEAR) AS FISCAL_YEAR,
                IFF(t.TRANSCRIPT_TYPE = 'None', NULL, t.TRANSCRIPT_TYPE) AS TRANSCRIPT_TYPE,
                t.TRANSCRIPT AS TRANSCRIPT_JSON,
                i.IssuerID,
                s.SecurityID
            FROM {source_db}.{source_schema}.{source_table} AS t
            INNER JOIN {dim_issuer_table} i ON t.COMPANY_ID = i.PROVIDERCOMPANYID
            INNER JOIN {dim_security_table} s ON i.IssuerID = s.IssuerID AND s.AssetClass = 'Equity'
            WHERE t.EVENT_TIMESTAMP >= DATEADD('year', -{years_of_history}, CURRENT_DATE())
              AND ((t.EVENT_TYPE = 'Earnings Call' AND t.TRANSCRIPT_TYPE = 'SPEAKERS_ANNOTATED')
                   OR t.EVENT_TYPE != 'Earnings Call')
              {since_clause}
            -- One row per event. The ordering must be deterministic, because TRANSCRIPT_ID
            -- is built from TRANSCRIPT_TYPE: a tie broken arbitrarily yields a different ID
            -- on every run, and the MERGE would then treat the same event as new each time.
            -- Non-earnings events publish RAW and SPEAKERS_ANNOTATED with identical
            -- paragraph counts, so paragraph count alone is a tie for ~940 events. Prefer
            -- SPEAKERS_ANNOTATED throughout, which is the same preference already applied
            -- to earnings calls in the filter above.
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY t.COMPANY_ID, t.EVENT_TIMESTAMP
                ORDER BY IFF(t.TRANSCRIPT_TYPE = 'SPEAKERS_ANNOTATED', 0, 1),
                         ARRAY_SIZE(t.TRANSCRIPT:paragraphs) DESC,
                         COALESCE(t.TRANSCRIPT_TYPE, '')
            ) = 1
        )
        -- A MERGE fails outright on a duplicate key in the source. The partition above is
        -- on company and timestamp, while the key is built from CIK, so guard the key
        -- itself: an issuer carrying two equity lines would otherwise break the load.
        SELECT * FROM candidates
        QUALIFY ROW_NUMBER() OVER (PARTITION BY TRANSCRIPT_ID ORDER BY EVENT_TIMESTAMP) = 1
        {limit_clause}
    ) AS src
    ON tgt.COMPANY_ID = src.COMPANY_ID AND tgt.EVENT_TIMESTAMP = src.EVENT_TIMESTAMP
    WHEN NOT MATCHED THEN INSERT (
        TRANSCRIPT_ID, COMPANY_ID, CIK, COMPANY_NAME, PRIMARY_TICKER,
        EVENT_TYPE, EVENT_TIMESTAMP, FISCAL_PERIOD, FISCAL_YEAR,
        TRANSCRIPT_TYPE, TRANSCRIPT_JSON, IssuerID, SecurityID
    ) VALUES (
        src.TRANSCRIPT_ID, src.COMPANY_ID, src.CIK, src.COMPANY_NAME, src.PRIMARY_TICKER,
        src.EVENT_TYPE, src.EVENT_TIMESTAMP, src.FISCAL_PERIOD, src.FISCAL_YEAR,
        src.TRANSCRIPT_TYPE, src.TRANSCRIPT_JSON, src.IssuerID, src.SecurityID
    )
    """

    try:
        merge_result = session.sql(load_sql).collect()
        inserted = merge_result[0][0] if merge_result else 0

        total = session.sql(f"SELECT COUNT(*) as cnt FROM {raw_table}").collect()[0]['CNT']
        if inserted:
            log_detail(f"Inserted {inserted:,} new transcripts ({total:,} total in RAW table)")
        else:
            log_detail(f"No new transcripts ({total:,} already in RAW table)")

        return inserted

    except Exception as e:
        log_error(f"Failed to load transcripts to RAW table: {e}")
        raise


def verify_transcripts_available(session: Session) -> bool:
    """
    Verify that the source transcript data is available.
    
    Returns:
        True if transcripts are available, False otherwise
    """
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    
    success, _ = verify_table_access(session, source_db, source_schema, source_table)
    return success



