"""
Real Company Event Transcripts Integration for SAM Demo

Extracts and processes real company event transcripts from SNOWFLAKE_PUBLIC_DATA_FREE.
Covers: Earnings Calls, AGMs, M&A Announcements, Investor Days, Special Calls.
Uses AI_COMPLETE for speaker identification and SPLIT_TEXT_RECURSIVE_CHARACTER for chunking.

This module replaces synthetic earnings transcripts with real, chunked, metadata-enriched
company event transcripts suitable for RAG-based search.
"""

from snowflake.snowpark import Session
from typing import List, Optional
import config


def get_target_tickers() -> List[str]:
    """
    Get tickers for real transcript extraction.
    Combines demo companies, major US stocks, and adds Snowflake.
    
    Returns:
        List of ~31 tickers to extract transcripts for
    """
    tickers = set()
    # Demo companies from config
    tickers.update(config.get_demo_company_tickers())
    # Major US stocks from config (tier1 and tier2)
    tickers.update(config.get_major_us_stocks('all'))
    # Add Snowflake
    tickers.add('SNOW')
    return list(tickers)


def build_all(session: Session, test_mode: bool = False):
    """
    Main entry point for real transcript processing.
    
    Args:
        session: Active Snowpark session
        test_mode: If True, limit processing for faster testing
    """
    config.log_step("Real company event transcripts")
    
    # Get target tickers for extraction
    target_tickers = get_target_tickers()
    config.log_detail(f"Target tickers: {len(target_tickers)} companies")
    
    # Step 1: Build speaker mapping (expensive, cached)
    build_speaker_mapping(session, target_tickers, test_mode)
    
    # Step 2: Build chunked transcripts corpus
    build_company_events_corpus(session, target_tickers, test_mode)
    
    config.log_phase_complete(f"Real transcripts: {len(target_tickers)} companies processed")


def build_speaker_mapping(session: Session, target_tickers: List[str], test_mode: bool = False):
    """
    Create speaker mapping table using AI_COMPLETE to identify speakers.
    
    Creates SAM_DEMO.MARKET_DATA.COMP_EVENT_SPEAKER_MAPPING with:
    - SPEAKER_ID: Speaker identifier (SPEAKER_1, SPEAKER_2, etc.)
    - SPEAKER_NAME: Full name of the speaker
    - SPEAKER_ROLE: Role (CEO, CFO, Analyst, Operator, etc.)
    - SPEAKER_COMPANY: Company the speaker represents
    
    This is an expensive operation that uses LLM calls, so results are cached.
    The table is only rebuilt if it doesn't exist or is empty.
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    
    table_path = f"{database_name}.{market_data_schema}.COMP_EVENT_SPEAKER_MAPPING"
    
    # Check if speaker mapping already exists with data (caching)
    try:
        count_result = session.sql(f"SELECT COUNT(*) as cnt FROM {table_path}").collect()
        existing_count = count_result[0]['CNT']
        if existing_count > 0:
            config.log_detail(f"Speaker mapping exists ({existing_count:,} records), skipping AI_COMPLETE extraction...")
            return
    except Exception:
        # Table doesn't exist, proceed with creation
        pass
    
    config.log_detail("Building speaker mapping with AI_COMPLETE (this may take several minutes)...")
    
    # Format tickers for SQL IN clause
    ticker_tuple = config.safe_sql_tuple(target_tickers)
    
    # Limit for test mode
    limit_clause = "LIMIT 50" if test_mode else ""
    
    # Create speaker mapping using AI_COMPLETE
    # The AI extracts speaker_id, speaker_name, speaker_role, and speaker_company
    speaker_mapping_sql = f"""
    CREATE OR REPLACE TABLE {table_path} AS
    SELECT 
        t.company_id,
        t.cik,
        t.company_name,
        t.primary_ticker,
        t.event_type,
        t.EVENT_TIMESTAMP,
        t.fiscal_period,
        t.fiscal_year,
        t.transcript_type,
        f.value:speaker_id::STRING AS SPEAKER_ID,
        f.value:speaker_name::STRING AS SPEAKER_NAME,
        f.value:speaker_role::STRING AS SPEAKER_ROLE,
        f.value:speaker_company::STRING AS SPEAKER_COMPANY
    FROM {source_db}.{source_schema}.{source_table} AS t,
    LATERAL FLATTEN(
        input => SNOWFLAKE.CORTEX.AI_COMPLETE(
            '{config.AI_SPEAKER_IDENTIFICATION_MODEL}',
            CONCAT(
                'Identify all speakers in this company event transcript. ',
                'For each speaker, determine their name, role (e.g., CEO, CFO, Analyst, Operator, Moderator), ',
                'and the company they represent. ',
                'IMPORTANT: If you cannot determine a speaker''s name, use "Unknown Speaker". ',
                'If you cannot determine their role, use "Unknown". ',
                'If you cannot determine their company, use "Unknown". ',
                'Always provide a value for every field - never leave any field empty. ',
                'Return a JSON array where each element has "speaker_id", "speaker_name", "speaker_role", and "speaker_company". ',
                'Transcript: ',
                ARRAY_TO_STRING(t.transcript:paragraphs, '\\n')
            ),
            {{
                'response_format': {{
                    'type': 'json',
                    'schema': {{
                        'type': 'object',
                        'properties': {{
                            'speakers': {{
                                'type': 'array',
                                'items': {{
                                    'type': 'object',
                                    'properties': {{
                                        'speaker_id': {{'type': 'string', 'description': 'Speaker identifier like SPEAKER_1'}},
                                        'speaker_name': {{'type': 'string', 'description': 'Full name of the speaker'}},
                                        'speaker_role': {{'type': 'string', 'description': 'Role such as CEO, CFO, Analyst, Operator'}},
                                        'speaker_company': {{'type': 'string', 'description': 'Company the speaker represents'}}
                                    }},
                                    'required': ['speaker_id', 'speaker_name', 'speaker_role', 'speaker_company']
                                }}
                            }}
                        }},
                        'required': ['speakers']
                    }}
                }}
            }}
        ):speakers
    ) f
    WHERE t.PRIMARY_TICKER IN {ticker_tuple}
      AND (LENGTH(ARRAY_TO_STRING(t.transcript:paragraphs, '\\n')) / 4)::INTEGER <= 199995
    {limit_clause}
    """
    
    try:
        session.sql(speaker_mapping_sql).collect()
        
        # Get count for logging
        count_result = session.sql(f"SELECT COUNT(*) as cnt FROM {table_path}").collect()
        speaker_count = count_result[0]['CNT']
        config.log_detail(f"Created speaker mapping: {speaker_count:,} speaker records")
        
    except Exception as e:
        config.log_error(f"Failed to create speaker mapping: {e}")
        raise


def build_company_events_corpus(session: Session, target_tickers: List[str], test_mode: bool = False):
    """
    Create the company event transcripts corpus with chunked, metadata-enriched content.
    
    Pipeline:
    1. Flatten transcript segments from JSON
    2. Enrich segments with speaker info from mapping table
    3. Format segments as "Speaker (Role - Company): Text"
    4. Aggregate segments into full transcript per event
    5. Chunk using SPLIT_TEXT_RECURSIVE_CHARACTER (~512 tokens)
    6. Prepend metadata header to each chunk
    7. Link to DIM_SECURITY via PRIMARY_TICKER for SecurityID/IssuerID
    
    Creates SAM_DEMO.CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS
    """
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    market_data_schema = config.DATABASE['schemas']['market_data']
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    
    corpus_table = f"{database_name}.{curated_schema}.COMPANY_EVENT_TRANSCRIPTS_CORPUS"
    speaker_mapping_table = f"{database_name}.{market_data_schema}.COMP_EVENT_SPEAKER_MAPPING"
    dim_security_table = f"{database_name}.{curated_schema}.DIM_SECURITY"
    
    config.log_detail("Building company event transcripts corpus with chunking...")
    
    # Format tickers for SQL IN clause
    ticker_tuple = config.safe_sql_tuple(target_tickers)
    
    # Limit for test mode  
    limit_clause = "LIMIT 100" if test_mode else ""
    
    # Main corpus creation SQL with full pipeline
    corpus_sql = f"""
    CREATE OR REPLACE TABLE {corpus_table} AS
    WITH 
    -- Step 1: Flatten transcript segments from JSON
    segments AS (
        SELECT 
            t.company_id,
            t.cik,
            t.company_name,
            t.primary_ticker,
            t.event_type,
            t.EVENT_TIMESTAMP,
            t.fiscal_period,
            t.fiscal_year,
            t.transcript_type,
            a.index AS speaker_order,
            CONCAT('SPEAKER_', a.value:speaker::text) AS speaker_id,
            a.value:text::text AS segment_text
        FROM {source_db}.{source_schema}.{source_table} AS t,
        LATERAL FLATTEN(input => t.TRANSCRIPT:paragraphs) a
        WHERE t.PRIMARY_TICKER IN {ticker_tuple}
        {limit_clause}
    ),
    
    -- Step 2: Enrich with speaker info from mapping table
    enriched_segments AS (
        SELECT 
            s.*,
            COALESCE(m.speaker_name, s.speaker_id) AS speaker_name,
            COALESCE(m.speaker_role, 'Unknown') AS speaker_role,
            COALESCE(m.speaker_company, s.company_name) AS speaker_company,
            -- Format: "John Smith (CEO - Apple Inc.): Good morning..."
            CONCAT(
                COALESCE(m.speaker_name, s.speaker_id), 
                ' (', COALESCE(m.speaker_role, 'Unknown'), ' - ', COALESCE(m.speaker_company, s.company_name), '): ',
                s.segment_text
            ) AS formatted_segment
        FROM segments s
        LEFT JOIN {speaker_mapping_table} m
            ON s.company_id = m.company_id
            AND s.cik = m.cik
            AND s.event_type = m.event_type
            AND s.EVENT_TIMESTAMP = m.EVENT_TIMESTAMP
            AND s.fiscal_period = m.fiscal_period
            AND s.fiscal_year = m.fiscal_year
            AND s.transcript_type = m.transcript_type
            AND s.speaker_id = m.speaker_id
    ),
    
    -- Step 3: Aggregate segments into full transcript per event
    full_transcripts AS (
        SELECT 
            company_id, 
            cik, 
            company_name, 
            primary_ticker,
            event_type, 
            EVENT_TIMESTAMP, 
            fiscal_period, 
            fiscal_year, 
            transcript_type,
            LISTAGG(formatted_segment, '\\n\\n') WITHIN GROUP (ORDER BY speaker_order) AS full_text
        FROM enriched_segments
        GROUP BY company_id, cik, company_name, primary_ticker, event_type, 
                 EVENT_TIMESTAMP, fiscal_period, fiscal_year, transcript_type
    ),
    
    -- Step 4: Chunk using recursive character splitter (~512 tokens ≈ 2000 chars)
    chunked AS (
        SELECT 
            ft.*,
            c.value::STRING AS chunk_text,
            c.index AS chunk_index
        FROM full_transcripts ft,
        LATERAL FLATTEN(
            input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(ft.full_text, 'markdown', 512)
        ) c
    ),
    
    -- Step 5: Join with DIM_SECURITY to get SecurityID and IssuerID
    linked_chunks AS (
        SELECT 
            c.*,
            ds.SecurityID,
            ds.IssuerID
        FROM chunked c
        LEFT JOIN {dim_security_table} ds ON c.primary_ticker = ds.Ticker
    )
    
    -- Step 6: Final output with metadata header prepended to each chunk
    SELECT 
        -- Generate unique DOCUMENT_ID
        MD5(CONCAT(primary_ticker, EVENT_TIMESTAMP::VARCHAR, chunk_index::VARCHAR)) AS DOCUMENT_ID,
        
        -- Title with chunk indicator
        CONCAT(company_name, ' ', event_type, ' - ', 
               DATE(EVENT_TIMESTAMP)::VARCHAR, ' (Part ', chunk_index + 1, ')') AS DOCUMENT_TITLE,
        
        'company_event_transcripts' AS DOCUMENT_TYPE,
        
        -- Security linkage
        SecurityID,
        IssuerID,
        
        DATE(EVENT_TIMESTAMP) AS PUBLISH_DATE,
        'en' AS LANGUAGE,
        
        -- Event type for filtering in search
        event_type AS EVENT_TYPE,
        
        -- Prepend metadata header to chunk for enhanced searchability
        CONCAT(
            'COMPANY: ', company_name, '\\n',
            'TICKER: ', primary_ticker, '\\n',
            'EVENT: ', event_type, '\\n',
            'DATE: ', DATE(EVENT_TIMESTAMP)::VARCHAR, '\\n',
            'FISCAL PERIOD: FY', fiscal_year, ' ', COALESCE(fiscal_period, 'N/A'), '\\n\\n',
            chunk_text
        ) AS DOCUMENT_TEXT
        
    FROM linked_chunks
    WHERE SecurityID IS NOT NULL  -- Only include if we have a matching security
    ORDER BY company_name, EVENT_TIMESTAMP, chunk_index
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
        
        config.log_detail(f"Created corpus: {chunk_count:,} chunks from ~{event_count:,} events")
        
    except Exception as e:
        config.log_error(f"Failed to create company events corpus: {e}")
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
    
    try:
        result = session.sql(f"""
            SELECT COUNT(*) as cnt 
            FROM {source_db}.{source_schema}.{source_table}
            LIMIT 1
        """).collect()
        return True
    except Exception as e:
        config.log_warning(f"Company event transcripts not available: {e}")
        return False


def get_transcript_stats(session: Session, target_tickers: List[str]) -> dict:
    """
    Get statistics about available transcripts for target tickers.
    
    Args:
        session: Active Snowpark session
        target_tickers: List of tickers to check
    
    Returns:
        Dictionary with transcript statistics
    """
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    ticker_tuple = config.safe_sql_tuple(target_tickers)
    
    try:
        result = session.sql(f"""
            SELECT 
                COUNT(*) as total_transcripts,
                COUNT(DISTINCT PRIMARY_TICKER) as companies_with_transcripts,
                COUNT(DISTINCT EVENT_TYPE) as event_types
            FROM {source_db}.{source_schema}.{source_table}
            WHERE PRIMARY_TICKER IN {ticker_tuple}
        """).collect()
        
        if result:
            return {
                'total_transcripts': result[0]['TOTAL_TRANSCRIPTS'],
                'companies_with_transcripts': result[0]['COMPANIES_WITH_TRANSCRIPTS'],
                'event_types': result[0]['EVENT_TYPES']
            }
    except Exception as e:
        config.log_warning(f"Failed to get transcript stats: {e}")
    
    return {'total_transcripts': 0, 'companies_with_transcripts': 0, 'event_types': 0}

