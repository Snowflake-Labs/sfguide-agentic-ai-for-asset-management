# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Real Company Event Transcripts Integration for SAM Demo

Extracts and processes real company event transcripts from SNOWFLAKE_PUBLIC_DATA_FREE.
Covers: Earnings Calls, AGMs, M&A Announcements, Investor Days, Special Calls.
Uses AI_COMPLETE for speaker identification and SPLIT_TEXT_RECURSIVE_CHARACTER for chunking.

This module replaces synthetic earnings transcripts with real, chunked, metadata-enriched
company event transcripts suitable for RAG-based search.

Filtering:
- Companies: Filtered by joining to DIM_ISSUER on PROVIDER_COMPANY_ID
- Date range: Filtered by YEARS_OF_HISTORY from config
- Transcript type: For Earnings Calls, prefers SPEAKERS_ANNOTATED over RAW to avoid duplicates
"""

from snowflake.snowpark import Session
import config
from logging_utils import log_step, log_substep, log_detail, log_warning, log_error, log_phase_complete
from db_helpers import verify_table_access


def build_all(session: Session, test_mode: bool = False):
    """
    Main entry point for real transcript processing.
    
    Filtering is done by:
    - Joining to DIM_ISSUER on PROVIDER_COMPANY_ID (company matching)
    - EVENT_TIMESTAMP >= YEARS_OF_HISTORY years ago (date filter)
    - For Earnings Calls: TRANSCRIPT_TYPE = 'SPEAKERS_ANNOTATED' (avoid duplicates)
    
    Args:
        session: Active Snowpark session
        test_mode: If True, limit processing for faster testing
    """
    log_substep("Real company event transcripts")
    
    # Step 1: Build speaker mapping (expensive, cached)
    build_speaker_mapping(session, test_mode)
    
    # Step 2: Build chunked transcripts corpus
    build_company_events_corpus(session, test_mode)
    
    log_phase_complete("Real transcripts processed")


def build_speaker_mapping(session: Session, test_mode: bool = False):
    """
    Create speaker mapping table using AI_COMPLETE to identify speakers.
    
    Creates SAM_DEMO.RAW.COMP_EVENT_SPEAKER_MAPPING with:
    - SPEAKER_ID: Speaker identifier (SPEAKER_1, SPEAKER_2, etc.)
    - SPEAKER_NAME: Full name of the speaker
    - SPEAKER_ROLE: Role (CEO, CFO, Analyst, Operator, etc.)
    - SPEAKER_COMPANY: Company the speaker represents
    
    Filtering:
    - Joins directly to DIM_ISSUER on PROVIDER_COMPANY_ID for company matching
    - Filters by YEARS_OF_HISTORY to limit transcript age
    - For Earnings Calls, prefers SPEAKERS_ANNOTATED over RAW to avoid duplicates
    
    This is an expensive operation that uses LLM calls, so results are cached.
    The table is only rebuilt if it doesn't exist or is empty.
    
    NOTE: This is stored in RAW schema as it's an intermediate working table,
    not a final output used in agent responses.
    """
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    raw_schema = config.DATABASE['schemas']['raw']
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    
    table_path = f"{database_name}.{raw_schema}.COMP_EVENT_SPEAKER_MAPPING"
    dim_issuer_table = f"{database_name}.{curated_schema}.DIM_ISSUER"
    years_of_history = config.YEARS_OF_HISTORY
    
    # Check if speaker mapping already exists with data (caching)
    try:
        count_result = session.sql(f"SELECT COUNT(*) as cnt FROM {table_path}").collect()
        existing_count = count_result[0]['CNT']
        if existing_count > 0:
            log_detail(f"Speaker mapping exists ({existing_count:,} records), skipping AI_COMPLETE extraction...")
            return
    except Exception:
        # Table doesn't exist, proceed with creation
        pass
    
    log_detail("Building speaker mapping with AI_COMPLETE (this may take several minutes)...")
    
    # Limit for test mode
    limit_clause = "LIMIT 50" if test_mode else ""
    
    # Create speaker mapping using AI_COMPLETE
    # Join directly to DIM_ISSUER on PROVIDER_COMPANY_ID for company matching
    # Filter by date and transcript type to reduce volume and avoid duplicates
    speaker_mapping_sql = f"""
    CREATE OR REPLACE TABLE {table_path} AS
    -- Sanitize 'None' strings to NULL for fiscal fields (prevents numeric conversion errors)
    SELECT 
        t.company_id,
        t.cik,
        t.company_name,
        t.primary_ticker,
        t.event_type,
        t.EVENT_TIMESTAMP,
        IFF(t.fiscal_period = 'None', NULL, t.fiscal_period) AS fiscal_period,
        IFF(t.fiscal_year = 'None', NULL, t.fiscal_year) AS fiscal_year,
        IFF(t.transcript_type = 'None', NULL, t.transcript_type) AS transcript_type,
        f.value:speaker_id::STRING AS SPEAKER_ID,
        f.value:speaker_name::STRING AS SPEAKER_NAME,
        f.value:speaker_role::STRING AS SPEAKER_ROLE,
        f.value:speaker_company::STRING AS SPEAKER_COMPANY
    FROM {source_db}.{source_schema}.{source_table} AS t
    INNER JOIN {dim_issuer_table} i ON t.COMPANY_ID = i.PROVIDERCOMPANYID,
    LATERAL FLATTEN(
        input => AI_COMPLETE(
            model => '{config.AI_SPEAKER_IDENTIFICATION_MODEL}',
            prompt => CONCAT(
                'Identify all speakers in this company event transcript. ',
                'For each speaker, determine their name, role (e.g., CEO, CFO, Analyst, Operator, Moderator), ',
                'and the company they represent. ',
                'IMPORTANT: If you cannot determine a speaker''s name, use "Unknown Speaker". ',
                'If you cannot determine their role, use "Unknown". ',
                'If you cannot determine their company, use "Unknown". ',
                'Always provide a value for every field - never leave any field empty. ',
                'Return a JSON array where each element has "speaker_id", "speaker_name", "speaker_role", and "speaker_company". ',
                'You MUST always retrun a JSON array with the schema defined below. ',
                '{{"speakers": [{{"speaker_id": "Speaker identifier like SPEAKER_1. Use Unknown if not found.", "speaker_name": "Full name of the speaker. Use Unknown Speaker if not found.", "speaker_role": "Role such as CEO, CFO, Analyst, Operator. Use Unknown if not found.","speaker_company": "Company the speaker represents. Use Unknown if not found."}}]}}',
                'Transcript: ',
                ARRAY_TO_STRING(t.transcript:paragraphs, '\\n')
            ),
            model_parameters => {{'temperature': 0}},
            response_format => {{
                    'type': 'json',
                    'schema': {{
                        'type': 'object',
                        'properties': {{
                            'speakers': {{
                                'type': 'array',
                                'items': {{
                                    'type': 'object',
                                    'properties': {{
                                        'speaker_id': {{'type': 'string', 'description': 'Speaker identifier like SPEAKER_1. Use Unknown if not found.'}},
                                        'speaker_name': {{'type': 'string', 'description': 'Full name of the speaker. Use Unknown Speaker if not found.'}},
                                        'speaker_role': {{'type': 'string', 'description': 'Role such as CEO, CFO, Analyst, Operator. Use Unknown if not found.'}},
                                        'speaker_company': {{'type': 'string', 'description': 'Company the speaker represents. Use Unknown if not found.'}}
                                    }}
                                }}
                            }}
                        }},
                        'required': ['speakers']
                    }}
                }}
        ):speakers
    ) f
    WHERE t.EVENT_TIMESTAMP >= DATEADD('year', -{years_of_history}, CURRENT_DATE())
      AND ((t.EVENT_TYPE = 'Earnings Call' AND t.TRANSCRIPT_TYPE = 'SPEAKERS_ANNOTATED') 
           OR t.EVENT_TYPE != 'Earnings Call')
      AND (LENGTH(ARRAY_TO_STRING(t.transcript:paragraphs, '\\n')) / 4)::INTEGER <= 199990
    {limit_clause}
    """
    
    try:
        session.sql(speaker_mapping_sql).collect()
        
        # Get count for logging
        count_result = session.sql(f"SELECT COUNT(*) as cnt FROM {table_path}").collect()
        speaker_count = count_result[0]['CNT']
        log_detail(f"Created speaker mapping: {speaker_count:,} speaker records")
        
    except Exception as e:
        log_error(f"Failed to create speaker mapping: {e}")
        raise


def build_company_events_corpus(session: Session, test_mode: bool = False):
    """
    Create the company event transcripts corpus with chunked, metadata-enriched content.
    
    Simplified Pipeline (segment-level approach):
    1. Join to DIM_ISSUER on PROVIDER_COMPANY_ID for company matching
    2. Filter by YEARS_OF_HISTORY and transcript_type (prefer SPEAKERS_ANNOTATED for Earnings Calls)
    3. Flatten transcript segments from JSON
    4. Enrich segments with speaker info from mapping table
    5. For segments ≤490 tokens: use directly with metadata header
    6. For segments >490 tokens: chunk and add metadata header to each chunk
    7. Link to DIM_SECURITY for SecurityID
    
    Creates SAM_DEMO.CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS with columns:
    - DOCUMENT_ID: Unique per chunk/segment
    - TRANSCRIPT_ID: Groups all chunks from same event
    - CHUNK_INDEX: 0-based position within segment (0 for short segments)
    - DOCUMENT_TEXT: Chunk content with metadata header including speakers
    """
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    raw_schema = config.DATABASE['schemas']['raw']
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    
    corpus_table = f"{database_name}.{curated_schema}.COMPANY_EVENT_TRANSCRIPTS_CORPUS"
    speaker_mapping_table = f"{database_name}.{raw_schema}.COMP_EVENT_SPEAKER_MAPPING"
    dim_security_table = f"{database_name}.{curated_schema}.DIM_SECURITY"
    dim_issuer_table = f"{database_name}.{curated_schema}.DIM_ISSUER"
    years_of_history = config.YEARS_OF_HISTORY
    
    # Token limit for segments (490 tokens, leaving ~22 tokens for metadata header)
    token_limit = 490
    
    log_detail("Building company event transcripts corpus...")
    
    # Limit for test mode  
    limit_clause = "LIMIT 100" if test_mode else ""
    
    # Simplified corpus creation SQL - work at segment level, only chunk long segments
    # Pipeline: segments -> enrich with speakers -> split short/long -> union -> final output
    corpus_sql = f"""
    CREATE OR REPLACE TABLE {corpus_table} AS
    WITH 
    -- Step 1: Flatten transcript segments from JSON
    -- Join to DIM_ISSUER on PROVIDER_COMPANY_ID for company matching
    -- Filter by date and transcript_type (prefer SPEAKERS_ANNOTATED for Earnings Calls)
    segments AS (
        SELECT 
            t.company_id,
            t.cik,
            t.company_name,
            t.primary_ticker,
            t.event_type,
            t.EVENT_TIMESTAMP,
            IFF(t.fiscal_period = 'None', NULL, t.fiscal_period) AS fiscal_period,
            IFF(t.fiscal_year = 'None', NULL, t.fiscal_year) AS fiscal_year,
            IFF(t.transcript_type = 'None', NULL, t.transcript_type) AS transcript_type,
            a.index AS speaker_order,
            CONCAT('SPEAKER_', a.value:speaker::text) AS speaker_id,
            a.value:text::text AS segment_text,
            i.IssuerID,
            s.SecurityID,
            s.Ticker AS matched_ticker
        FROM {source_db}.{source_schema}.{source_table} AS t
        INNER JOIN {dim_issuer_table} i ON t.COMPANY_ID = i.PROVIDERCOMPANYID
        INNER JOIN {dim_security_table} s ON i.IssuerID = s.IssuerID AND s.AssetClass = 'Equity',
        LATERAL FLATTEN(input => t.TRANSCRIPT:paragraphs) a
        WHERE t.EVENT_TIMESTAMP >= DATEADD('year', -{years_of_history}, CURRENT_DATE())
          AND ((t.EVENT_TYPE = 'Earnings Call' AND t.TRANSCRIPT_TYPE = 'SPEAKERS_ANNOTATED') 
               OR t.EVENT_TYPE != 'Earnings Call')
        {limit_clause}
    ),
    
    -- Step 2: Enrich with speaker info from mapping table
    enriched_segments AS (
        SELECT 
            s.*,
            COALESCE(m.speaker_name, s.speaker_id) AS speaker_name,
            COALESCE(m.speaker_role, 'Unknown') AS speaker_role,
            COALESCE(m.speaker_company, s.company_name) AS speaker_company,
            AI_COUNT_TOKENS('ai_embed', '{config.AI_EMBEDDING_MODEL}', s.segment_text) AS token_count
        FROM segments s
        LEFT JOIN {speaker_mapping_table} m
            ON s.company_id = m.company_id
            AND s.cik = m.cik
            AND s.event_type = m.event_type
            AND s.EVENT_TIMESTAMP = m.EVENT_TIMESTAMP
            AND COALESCE(s.fiscal_period, '') = COALESCE(m.fiscal_period, '')
            AND COALESCE(s.fiscal_year, '') = COALESCE(m.fiscal_year, '')
            AND COALESCE(s.transcript_type, '') = COALESCE(m.transcript_type, '')
            AND s.speaker_id = m.speaker_id
    ),
    
    -- Step 3a: Short segments that fit within token limit - use directly
    short_segments AS (
        SELECT 
            *,
            segment_text AS chunk_text,
            0 AS chunk_index
        FROM enriched_segments
        WHERE token_count <= {token_limit}
    ),
    
    -- Step 3b: Long segments that need chunking
    long_segments AS (
        SELECT *
        FROM enriched_segments
        WHERE token_count > {token_limit}
    ),
    
    -- Step 3c: Chunk the long segments
    chunked_long_segments AS (
        SELECT 
            ls.company_id,
            ls.cik,
            ls.company_name,
            ls.primary_ticker,
            ls.event_type,
            ls.EVENT_TIMESTAMP,
            ls.fiscal_period,
            ls.fiscal_year,
            ls.transcript_type,
            ls.speaker_order,
            ls.speaker_id,
            ls.segment_text,
            ls.IssuerID,
            ls.SecurityID,
            ls.matched_ticker,
            ls.speaker_name,
            ls.speaker_role,
            ls.speaker_company,
            ls.token_count,
            c.value::STRING AS chunk_text,
            c.index AS chunk_index
        FROM long_segments ls,
        LATERAL FLATTEN(
            input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(ls.segment_text, 'markdown', {token_limit})
        ) c
    ),
    
    -- Step 4: Union short segments and chunked long segments
    all_chunks AS (
        SELECT * FROM short_segments
        UNION ALL
        SELECT * FROM chunked_long_segments
    )
    
    -- Step 5: Final output with metadata header prepended to each chunk/segment
    SELECT 
        -- Generate unique DOCUMENT_ID (includes speaker_order and chunk_index for uniqueness)
        MD5(CONCAT(
            cik, 
            EVENT_TIMESTAMP::VARCHAR, 
            COALESCE(transcript_type, ''), 
            speaker_order::VARCHAR,
            chunk_index::VARCHAR
        )) AS DOCUMENT_ID,
        
        -- TRANSCRIPT_ID: Groups all chunks from same event for ordered retrieval
        MD5(CONCAT(cik, EVENT_TIMESTAMP::VARCHAR, COALESCE(transcript_type, ''))) AS TRANSCRIPT_ID,
        
        -- Title with speaker and chunk indicator
        CONCAT(
            company_name, ' ', event_type, 
            CASE WHEN transcript_type IS NOT NULL THEN CONCAT(' (', transcript_type, ')') ELSE '' END,
            ' - ', DATE(EVENT_TIMESTAMP)::VARCHAR,
            ' - ', COALESCE(speaker_name, speaker_id, 'Unknown'),
            CASE WHEN chunk_index > 0 THEN CONCAT(' (Part ', chunk_index + 1, ')') ELSE '' END
        ) AS DOCUMENT_TITLE,
        
        'company_event_transcripts' AS DOCUMENT_TYPE,
        
        SecurityID,
        IssuerID,
        
        DATE(EVENT_TIMESTAMP) AS PUBLISH_DATE,
        'en' AS LANGUAGE,
        
        event_type AS EVENT_TYPE,
        
        speaker_order AS SEGMENT_INDEX,
        chunk_index AS CHUNK_INDEX,
        
        -- Prepend metadata header with speaker context to each chunk/segment
        CONCAT(
            'COMPANY: ', company_name, '\\n',
            'TICKER: ', COALESCE(matched_ticker, primary_ticker), '\\n',
            'EVENT: ', event_type, '\\n',
            'DATE: ', DATE(EVENT_TIMESTAMP)::VARCHAR, '\\n',
            'FISCAL PERIOD: FY', COALESCE(fiscal_year, ''), '\\n',
            'FISCAL QUARTER: ', COALESCE(fiscal_period, 'N/A'), '\\n\\n',
            COALESCE(speaker_name, speaker_id, 'Unknown'), ' (', COALESCE(speaker_role, 'Unknown'), '): ',
            chunk_text
        ) AS DOCUMENT_TEXT
        
    FROM all_chunks
    ORDER BY company_name, EVENT_TIMESTAMP, transcript_type, speaker_order, chunk_index
    """
    
    try:
        session.sql(corpus_sql).collect()
        
        # Get count for logging
        count_result = session.sql(f"SELECT COUNT(*) as cnt FROM {corpus_table}").collect()
        chunk_count = count_result[0]['CNT']
        
        # Get event count
        event_result = session.sql(f"""
            SELECT COUNT(DISTINCT CONCAT(DOCUMENT_TITLE)) as event_cnt 
            FROM {corpus_table}
        """).collect()
        event_count = event_result[0]['EVENT_CNT'] if event_result else 0
        
        log_detail(f"Created corpus: {chunk_count:,} chunks from ~{event_count:,} events")
        
    except Exception as e:
        log_error(f"Failed to create company events corpus: {e}")
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

