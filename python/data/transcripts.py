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

Covers: Earnings Calls, AGMs, M&A Announcements, Investor Days, Special Calls.
Uses AI_COMPLETE for speaker identification and SPLIT_TEXT_RECURSIVE_CHARACTER for chunking.

Filtering:
- Companies: Filtered by joining to DIM_ISSUER on PROVIDER_COMPANY_ID
- Date range: Filtered by YEARS_OF_HISTORY from config
- Transcript type: For Earnings Calls, prefers SPEAKERS_ANNOTATED over RAW to avoid duplicates
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_step, log_substep, log_detail, log_warning, log_error, log_phase_complete
from utils.snowflake import verify_table_access


def load_raw_table(session: Session, test_mode: bool = False) -> int:
    """
    Load real transcripts into COMPANY_EVENT_TRANSCRIPTS_RAW table.
    This triggers the TRANSCRIPTS_SPEAKER_STREAM and TRANSCRIPTS_CORPUS_STREAM for pipeline processing.
    
    Pipeline-only architecture: This function ONLY loads to RAW table.
    The pipeline DAG handles speaker mapping and corpus build.
    
    Args:
        session: Active Snowpark session
        test_mode: If True, limit records for faster testing
    
    Returns:
        Number of transcripts loaded
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
    
    # Table and streams already exist from create_transcripts_pipeline().
    # Simple INSERT — the stream captures these as new rows for the pipeline.
    dim_security_table = f"{database_name}.{curated_schema}.DIM_SECURITY"
    
    load_sql = f"""
    INSERT INTO {raw_table} (
        TRANSCRIPT_ID, COMPANY_ID, CIK, COMPANY_NAME, PRIMARY_TICKER,
        EVENT_TYPE, EVENT_TIMESTAMP, FISCAL_PERIOD, FISCAL_YEAR,
        TRANSCRIPT_TYPE, TRANSCRIPT_JSON, IssuerID, SecurityID
    )
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
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY t.COMPANY_ID, t.EVENT_TIMESTAMP
        ORDER BY ARRAY_SIZE(t.TRANSCRIPT:paragraphs) DESC
    ) = 1
    {limit_clause}
    """
    
    try:
        session.sql(load_sql).collect()
        
        # Get count for logging
        count_result = session.sql(f"SELECT COUNT(*) as cnt FROM {raw_table}").collect()
        transcript_count = count_result[0]['CNT']
        log_detail(f"Loaded {transcript_count:,} transcripts to RAW table")
        
        return transcript_count
        
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


def get_transcript_stats(session: Session) -> dict:
    """
    Get statistics about available transcripts for companies in DIM_ISSUER.
    
    Args:
        session: Active Snowpark session
    
    Returns:
        Dictionary with transcript statistics
    """
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    dim_issuer_table = f"{database_name}.{curated_schema}.DIM_ISSUER"
    years_of_history = config.YEARS_OF_HISTORY
    
    try:
        result = session.sql(f"""
            SELECT 
                COUNT(*) as total_transcripts,
                COUNT(DISTINCT t.PRIMARY_TICKER) as companies_with_transcripts,
                COUNT(DISTINCT t.EVENT_TYPE) as event_types
            FROM {source_db}.{source_schema}.{source_table} t
            INNER JOIN {dim_issuer_table} i ON t.COMPANY_ID = i.PROVIDERCOMPANYID
            WHERE t.EVENT_TIMESTAMP >= DATEADD('year', -{years_of_history}, CURRENT_DATE())
              AND ((t.EVENT_TYPE = 'Earnings Call' AND t.TRANSCRIPT_TYPE = 'SPEAKERS_ANNOTATED') 
                   OR t.EVENT_TYPE != 'Earnings Call')
        """).collect()
        
        if result:
            return {
                'total_transcripts': result[0]['TOTAL_TRANSCRIPTS'],
                'companies_with_transcripts': result[0]['COMPANIES_WITH_TRANSCRIPTS'],
                'event_types': result[0]['EVENT_TYPES']
            }
    except Exception as e:
        log_warning(f"Failed to get transcript stats: {e}")
    
    return {'total_transcripts': 0, 'companies_with_transcripts': 0, 'event_types': 0}

