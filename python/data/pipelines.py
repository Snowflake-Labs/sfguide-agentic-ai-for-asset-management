"""
Unstructured Data Pipelines for SAM Demo

This module creates production-like Snowflake pipelines for unstructured content:
- PDF file pipelines: Stage (RAW) -> Directory Stream -> Parse/Chunk Task DAG
- Corpus pipelines: RAW table -> Chunked CORPUS table via Task DAG
- Real transcript pipeline: Speaker mapping + corpus build via Task DAG
- SEC filing refresh pipeline: FACT_SEC_FILING_TEXT refresh via Task

All tasks are created SUSPENDED by default and can be:
- Demonstrated in Snowsight (view DAG structure)
- Executed once via EXECUTE TASK for demo setup
- Re-suspended after execution

Usage:
    from create_unstructured_pipelines import create_all_pipelines, run_all_pipelines
    
    # Create all pipeline objects (stages, streams, tables, tasks)
    create_all_pipelines(session)
    
    # Execute all pipelines once and suspend
    run_all_pipelines(session)
"""

import os
import time
import yaml
from snowflake.snowpark import Session
from typing import List, Dict, Any, Optional, Tuple
import config
from utils.logging import log_info, log_detail, log_warning, log_error, log_step, log_substep


# =============================================================================
# CONFIGURATION: Pipeline Definitions
# =============================================================================

# PDF pipeline definitions (split by audience)
PDF_PIPELINES = {
    'internal': {
        'stage_name': 'PDF_INTERNAL_STAGE',
        'stream_name': 'PDF_INTERNAL_STREAM',
        'raw_table': 'PDF_INTERNAL_RAW',
        'corpus_table': 'PDF_INTERNAL_CORPUS',
        'parse_task': 'PDF_INTERNAL_PARSE',
        'chunk_task': 'PDF_INTERNAL_CHUNK',
        'description': 'Internal SAM-branded PDF documents'
    },
    'external': {
        'stage_name': 'PDF_EXTERNAL_STAGE',
        'stream_name': 'PDF_EXTERNAL_STREAM',
        'raw_table': 'PDF_EXTERNAL_RAW',
        'corpus_table': 'PDF_EXTERNAL_CORPUS',
        'parse_task': 'PDF_EXTERNAL_PARSE',
        'chunk_task': 'PDF_EXTERNAL_CHUNK',
        'description': 'External broker/company/NGO PDF documents'
    },
    'regulatory': {
        'stage_name': 'PDF_REGULATORY_STAGE',
        'stream_name': 'PDF_REGULATORY_STREAM',
        'raw_table': 'PDF_REGULATORY_RAW',
        'corpus_table': 'PDF_REGULATORY_CORPUS',
        'parse_task': 'PDF_REGULATORY_PARSE',
        'chunk_task': 'PDF_REGULATORY_CHUNK',
        'lookup_table': 'REGULATION_LOOKUP',
        'description': 'External regulatory documents (EU/UK/US/International)',
        'custom_pipeline': True
    }
}

# Token threshold for chunking (same as real transcripts)
CHUNK_TOKEN_THRESHOLD = 512

# Chunk size in characters for SPLIT_TEXT_RECURSIVE_CHARACTER
# Approximate: 512 tokens ~ 2048 characters (4 chars/token average)
CHUNK_SIZE_CHARS = 2000
CHUNK_OVERLAP_CHARS = 200


# =============================================================================
# PDF PIPELINE CREATION (Simple 2-Task Architecture)
# =============================================================================

def create_pdf_pipeline(session: Session, pipeline_key: str) -> bool:
    """
    Create a PDF ingestion pipeline with simple 2-task architecture.
    
    Architecture:
        PARSE_TASK (stream → RAW table with AI_PARSE_DOCUMENT)
            ↓
        CHUNK_TASK (RAW → CORPUS with chunking)
    
    Args:
        session: Snowpark session
        pipeline_key: 'internal' or 'external'
    
    Returns:
        True if all objects created successfully
    """
    if pipeline_key not in PDF_PIPELINES:
        log_error(f"Unknown PDF pipeline key: {pipeline_key}")
        return False
    
    pipeline = PDF_PIPELINES[pipeline_key]
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    curated_schema = config.DATABASE['schemas']['curated']
    warehouse = config.WAREHOUSES['execution']['name']
    
    log_substep(f"Creating PDF pipeline: {pipeline_key}")
    
    try:
        stage_fqn = f"{database}.{raw_schema}.{pipeline['stage_name']}"
        stream_fqn = f"{database}.{raw_schema}.{pipeline['stream_name']}"
        raw_table_fqn = f"{database}.{raw_schema}.{pipeline['raw_table']}"
        corpus_table_fqn = f"{database}.{curated_schema}.{pipeline['corpus_table']}"
        parse_task_fqn = f"{database}.{raw_schema}.{pipeline['parse_task']}"
        chunk_task_fqn = f"{database}.{raw_schema}.{pipeline['chunk_task']}"
        
        session.sql(f"""
            CREATE STAGE IF NOT EXISTS {stage_fqn}
            ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
            DIRECTORY = (ENABLE = TRUE)
        """).collect()
        log_detail(f"  Created stage: {pipeline['stage_name']}")
        
        session.sql(f"""
            CREATE OR REPLACE STREAM {stream_fqn}
            ON STAGE {stage_fqn}
        """).collect()
        log_detail(f"  Created stream: {pipeline['stream_name']}")
        
        session.sql(f"""
            CREATE OR REPLACE TABLE {raw_table_fqn} (
                FILE_PATH VARCHAR(1000) NOT NULL,
                FILE_NAME VARCHAR(500),
                FILE_SIZE NUMBER,
                LAST_MODIFIED TIMESTAMP_NTZ,
                ETAG VARCHAR(100),
                DOC_TYPE VARCHAR(100),
                PARSE_MODE VARCHAR(20) DEFAULT 'LAYOUT',
                PARSED_JSON VARIANT,
                EXTRACTED_TEXT VARCHAR,
                TOKEN_COUNT NUMBER,
                PARSE_STATUS VARCHAR(50) DEFAULT 'PENDING',
                PARSE_ERROR VARCHAR,
                PARSED_AT TIMESTAMP_NTZ,
                CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """).collect()
        log_detail(f"  Created RAW table: {pipeline['raw_table']}")
        
        session.sql(f"""
            CREATE OR REPLACE TABLE {corpus_table_fqn} (
                DOCUMENT_ID VARCHAR(100) NOT NULL,
                SOURCE_FILE_PATH VARCHAR(1000),
                CHUNK_INDEX NUMBER DEFAULT 0,
                DOCUMENT_TITLE VARCHAR(500),
                DOCUMENT_TYPE VARCHAR(100),
                DOCUMENT_TEXT VARCHAR,
                TOKEN_COUNT NUMBER,
                LANGUAGE VARCHAR(10) DEFAULT 'en',
                PUBLISH_DATE DATE,
                TICKER VARCHAR(20),
                COMPANY_NAME VARCHAR(500),
                GICS_SECTOR VARCHAR(200),
                CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """).collect()
        log_detail(f"  Created CORPUS table: {pipeline['corpus_table']}")
        
        session.sql(f"""
            CREATE OR REPLACE TASK {parse_task_fqn}
            WAREHOUSE = {warehouse}
            SCHEDULE = '5 MINUTE'
            WHEN SYSTEM$STREAM_HAS_DATA('{stream_fqn}')
            AS
            MERGE INTO {raw_table_fqn} tgt
            USING (
                WITH new_files AS (
                    SELECT 
                        RELATIVE_PATH,
                        SIZE,
                        LAST_MODIFIED,
                        ETAG,
                        SPLIT_PART(RELATIVE_PATH, '/', 1) AS DOC_TYPE
                    FROM {stream_fqn}
                    WHERE METADATA$ACTION = 'INSERT'
                      AND LOWER(RELATIVE_PATH) LIKE '%.pdf'
                ),
                parsed_docs AS (
                    SELECT 
                        f.RELATIVE_PATH,
                        f.SIZE,
                        f.LAST_MODIFIED,
                        f.ETAG,
                        f.DOC_TYPE,
                        AI_PARSE_DOCUMENT(
                            TO_FILE('@{stage_fqn}', f.RELATIVE_PATH),
                            OBJECT_CONSTRUCT('mode', 'LAYOUT', 'page_split', TRUE)
                        ) as PARSED_JSON
                    FROM new_files f
                )
                SELECT 
                    RELATIVE_PATH as FILE_PATH,
                    SPLIT_PART(RELATIVE_PATH, '/', -1) as FILE_NAME,
                    SIZE as FILE_SIZE,
                    LAST_MODIFIED::TIMESTAMP_NTZ as LAST_MODIFIED,
                    ETAG,
                    DOC_TYPE,
                    'LAYOUT' as PARSE_MODE,
                    PARSED_JSON,
                    COALESCE(
                        PARSED_JSON:content::VARCHAR,
                        ARRAY_TO_STRING(
                            TRANSFORM(PARSED_JSON:pages, p -> p:content::VARCHAR),
                            '\\n\\n'
                        )
                    ) as EXTRACTED_TEXT,
                    'PARSED' as PARSE_STATUS,
                    CURRENT_TIMESTAMP() as PARSED_AT
                FROM parsed_docs
            ) src
            ON tgt.FILE_PATH = src.FILE_PATH AND tgt.ETAG = src.ETAG
            WHEN NOT MATCHED THEN INSERT (
                FILE_PATH, FILE_NAME, FILE_SIZE, LAST_MODIFIED, ETAG, DOC_TYPE,
                PARSE_MODE, PARSED_JSON, EXTRACTED_TEXT, PARSE_STATUS, PARSED_AT
            ) VALUES (
                src.FILE_PATH, src.FILE_NAME, src.FILE_SIZE, src.LAST_MODIFIED, src.ETAG, src.DOC_TYPE,
                src.PARSE_MODE, src.PARSED_JSON, src.EXTRACTED_TEXT, src.PARSE_STATUS, src.PARSED_AT
            )
        """).collect()
        log_detail(f"  Created parse task: {pipeline['parse_task']}")
        
        session.sql(f"""
            CREATE OR REPLACE TASK {chunk_task_fqn}
            WAREHOUSE = {warehouse}
            AFTER {parse_task_fqn}
            AS
            MERGE INTO {corpus_table_fqn} tgt
            USING (
                WITH parsed_with_tokens AS (
                    SELECT
                        FILE_PATH,
                        FILE_NAME,
                        DOC_TYPE,
                        EXTRACTED_TEXT,
                        AI_COUNT_TOKENS('ai_embed', '{config.AI_EMBEDDING_MODEL}', EXTRACTED_TEXT) as TOKEN_COUNT,
                        PARSED_AT
                    FROM {raw_table_fqn}
                    WHERE PARSE_STATUS = 'PARSED'
                      AND EXTRACTED_TEXT IS NOT NULL
                      AND LENGTH(EXTRACTED_TEXT) > 10
                ),
                enriched AS (
                    SELECT p.*,
                           i.PrimaryTicker as TICKER,
                           i.LegalName as COMPANY_NAME,
                           i.GICS_SECTOR
                    FROM parsed_with_tokens p
                    LEFT JOIN {database}.{curated_schema}.DIM_ISSUER i
                        ON AI_FILTER(PROMPT('Is this document primarily about the company {{1}}? Document: {{0}}', LEFT(p.EXTRACTED_TEXT, 500), i.LegalName))
                ),
                short_docs AS (
                    SELECT
                        MD5(FILE_PATH) as DOCUMENT_ID,
                        FILE_PATH as SOURCE_FILE_PATH,
                        0 as CHUNK_INDEX,
                        FILE_NAME as DOCUMENT_TITLE,
                        DOC_TYPE as DOCUMENT_TYPE,
                        EXTRACTED_TEXT as DOCUMENT_TEXT,
                        TOKEN_COUNT,
                        'en' as LANGUAGE,
                        COALESCE(TRY_TO_DATE(REGEXP_SUBSTR(FILE_NAME, '\\d{{8}}'), 'YYYYMMDD'), DATE(PARSED_AT)) as PUBLISH_DATE,
                        TICKER,
                        COMPANY_NAME,
                        GICS_SECTOR
                    FROM enriched
                    WHERE TOKEN_COUNT <= {CHUNK_TOKEN_THRESHOLD}
                ),
                long_docs_chunked AS (
                    SELECT
                        MD5(CONCAT(e.FILE_PATH, '|', c.index)) as DOCUMENT_ID,
                        e.FILE_PATH as SOURCE_FILE_PATH,
                        c.index as CHUNK_INDEX,
                        CONCAT(e.FILE_NAME, ' (Part ', c.index + 1, ')') as DOCUMENT_TITLE,
                        e.DOC_TYPE as DOCUMENT_TYPE,
                        c.value::VARCHAR as DOCUMENT_TEXT,
                        AI_COUNT_TOKENS('ai_embed', '{config.AI_EMBEDDING_MODEL}', c.value::VARCHAR) as TOKEN_COUNT,
                        'en' as LANGUAGE,
                        COALESCE(TRY_TO_DATE(REGEXP_SUBSTR(e.FILE_NAME, '\\d{{8}}'), 'YYYYMMDD'), DATE(e.PARSED_AT)) as PUBLISH_DATE,
                        e.TICKER,
                        e.COMPANY_NAME,
                        e.GICS_SECTOR
                    FROM enriched e,
                    LATERAL FLATTEN(
                        input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
                            e.EXTRACTED_TEXT, 
                            'markdown', 
                            {CHUNK_SIZE_CHARS},
                            {CHUNK_OVERLAP_CHARS}
                        )
                    ) c
                    WHERE e.TOKEN_COUNT > {CHUNK_TOKEN_THRESHOLD}
                ),
                all_chunks AS (
                    SELECT * FROM short_docs
                    UNION ALL
                    SELECT * FROM long_docs_chunked
                )
                SELECT * FROM all_chunks
            ) src
            ON tgt.DOCUMENT_ID = src.DOCUMENT_ID
            WHEN NOT MATCHED THEN INSERT (
                DOCUMENT_ID, SOURCE_FILE_PATH, CHUNK_INDEX, DOCUMENT_TITLE,
                DOCUMENT_TYPE, DOCUMENT_TEXT, TOKEN_COUNT, LANGUAGE, PUBLISH_DATE,
                TICKER, COMPANY_NAME, GICS_SECTOR
            ) VALUES (
                src.DOCUMENT_ID, src.SOURCE_FILE_PATH, src.CHUNK_INDEX, src.DOCUMENT_TITLE,
                src.DOCUMENT_TYPE, src.DOCUMENT_TEXT, src.TOKEN_COUNT, src.LANGUAGE, src.PUBLISH_DATE,
                src.TICKER, src.COMPANY_NAME, src.GICS_SECTOR
            )
        """).collect()
        log_detail(f"  Created chunk task: {pipeline['chunk_task']}")
        
        return True
        
    except Exception as e:
        log_error(f"Failed to create PDF pipeline {pipeline_key}: {e}")
        return False


def _load_regulation_sources() -> list:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    yaml_path = os.path.join(project_root, 'data', 'reference_data', 'regulation_sources.yaml')
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('regulations', [])


def populate_regulation_lookup(session: Session) -> int:
    pipeline = PDF_PIPELINES['regulatory']
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    lookup_fqn = f"{database}.{raw_schema}.{pipeline['lookup_table']}"

    session.sql(f"""
        CREATE OR REPLACE TABLE {lookup_fqn} (
            REGULATION_ID      VARCHAR(50) NOT NULL,
            TITLE              VARCHAR(500),
            FILE_NAME          VARCHAR(500),
            SOURCE_URL         VARCHAR(1000),
            REGULATORY_BODY    VARCHAR(200),
            REFERENCE          VARCHAR(200),
            JURISDICTION       VARCHAR(50),
            EFFECTIVE_DATE     DATE,
            AM_RELEVANCE       VARCHAR(2000),
            PRIMARY KEY (REGULATION_ID)
        )
    """).collect()

    regulations = _load_regulation_sources()
    if not regulations:
        log_warning("No regulation sources found in YAML")
        return 0

    session.sql(f"TRUNCATE TABLE IF EXISTS {lookup_fqn}").collect()

    values_list = []
    for reg in regulations:
        eff_date = f"'{reg['effective_date']}'" if reg.get('effective_date') else 'NULL'
        values_list.append(
            f"('{reg['id']}', $${reg['title']}$$, '{reg['file']}', "
            f"$${reg.get('source_url', '')}$$, $${reg['regulatory_body']}$$, "
            f"$${reg['reference']}$$, '{reg['jurisdiction']}', {eff_date}, "
            f"$${reg.get('am_relevance', '')}$$)"
        )

    batch_size = 50
    inserted = 0
    for i in range(0, len(values_list), batch_size):
        batch = values_list[i:i+batch_size]
        session.sql(f"""
            INSERT INTO {lookup_fqn}
            (REGULATION_ID, TITLE, FILE_NAME, SOURCE_URL, REGULATORY_BODY, REFERENCE, JURISDICTION, EFFECTIVE_DATE, AM_RELEVANCE)
            VALUES {', '.join(batch)}
        """).collect()
        inserted += len(batch)

    log_detail(f"  Populated {inserted} rows into {pipeline['lookup_table']}")
    return inserted


def create_regulatory_pdf_pipeline(session: Session) -> bool:
    pipeline = PDF_PIPELINES['regulatory']
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    curated_schema = config.DATABASE['schemas']['curated']
    warehouse = config.WAREHOUSES['execution']['name']

    log_substep("Creating PDF pipeline: regulatory")

    try:
        stage_fqn = f"{database}.{raw_schema}.{pipeline['stage_name']}"
        stream_fqn = f"{database}.{raw_schema}.{pipeline['stream_name']}"
        raw_table_fqn = f"{database}.{raw_schema}.{pipeline['raw_table']}"
        corpus_table_fqn = f"{database}.{curated_schema}.{pipeline['corpus_table']}"
        parse_task_fqn = f"{database}.{raw_schema}.{pipeline['parse_task']}"
        chunk_task_fqn = f"{database}.{raw_schema}.{pipeline['chunk_task']}"
        lookup_fqn = f"{database}.{raw_schema}.{pipeline['lookup_table']}"

        session.sql(f"""
            CREATE STAGE IF NOT EXISTS {stage_fqn}
            ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
            DIRECTORY = (ENABLE = TRUE)
        """).collect()
        log_detail(f"  Created stage: {pipeline['stage_name']}")

        session.sql(f"""
            CREATE OR REPLACE STREAM {stream_fqn}
            ON STAGE {stage_fqn}
        """).collect()
        log_detail(f"  Created stream: {pipeline['stream_name']}")

        session.sql(f"""
            CREATE OR REPLACE TABLE {raw_table_fqn} (
                FILE_PATH VARCHAR(1000) NOT NULL,
                FILE_NAME VARCHAR(500),
                FILE_SIZE NUMBER,
                LAST_MODIFIED TIMESTAMP_NTZ,
                ETAG VARCHAR(100),
                DOC_TYPE VARCHAR(100),
                PARSE_MODE VARCHAR(20) DEFAULT 'LAYOUT',
                PARSED_JSON VARIANT,
                EXTRACTED_TEXT VARCHAR,
                TOKEN_COUNT NUMBER,
                PARSE_STATUS VARCHAR(50) DEFAULT 'PENDING',
                PARSE_ERROR VARCHAR,
                PARSED_AT TIMESTAMP_NTZ,
                CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """).collect()
        log_detail(f"  Created RAW table: {pipeline['raw_table']}")

        session.sql(f"""
            CREATE OR REPLACE TABLE {corpus_table_fqn} (
                DOCUMENT_ID        VARCHAR(100) NOT NULL,
                SOURCE_FILE_PATH   VARCHAR(1000),
                CHUNK_INDEX        NUMBER DEFAULT 0,
                DOCUMENT_TITLE     VARCHAR(500),
                DOCUMENT_TYPE      VARCHAR(100),
                DOCUMENT_TEXT      VARCHAR,
                TOKEN_COUNT        NUMBER,
                LANGUAGE           VARCHAR(10) DEFAULT 'en',
                REGULATION_ID      VARCHAR(50),
                REGULATORY_BODY    VARCHAR(200),
                JURISDICTION       VARCHAR(50),
                REFERENCE          VARCHAR(200),
                SOURCE_URL         VARCHAR(1000),
                PUBLISH_DATE       DATE,
                CREATED_AT         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """).collect()
        log_detail(f"  Created CORPUS table: {pipeline['corpus_table']}")

        populate_regulation_lookup(session)

        session.sql(f"""
            CREATE OR REPLACE TASK {parse_task_fqn}
            WAREHOUSE = {warehouse}
            SCHEDULE = '5 MINUTE'
            WHEN SYSTEM$STREAM_HAS_DATA('{stream_fqn}')
            AS
            MERGE INTO {raw_table_fqn} tgt
            USING (
                WITH new_files AS (
                    SELECT 
                        RELATIVE_PATH,
                        SIZE,
                        LAST_MODIFIED,
                        ETAG,
                        'regulatory_docs' AS DOC_TYPE
                    FROM {stream_fqn}
                    WHERE METADATA$ACTION = 'INSERT'
                      AND LOWER(RELATIVE_PATH) LIKE '%.pdf'
                ),
                parsed_docs AS (
                    SELECT 
                        f.RELATIVE_PATH,
                        f.SIZE,
                        f.LAST_MODIFIED,
                        f.ETAG,
                        f.DOC_TYPE,
                        AI_PARSE_DOCUMENT(
                            TO_FILE('@{stage_fqn}', f.RELATIVE_PATH),
                            OBJECT_CONSTRUCT('mode', 'LAYOUT', 'page_split', TRUE)
                        ) as PARSED_JSON
                    FROM new_files f
                )
                SELECT 
                    RELATIVE_PATH as FILE_PATH,
                    SPLIT_PART(RELATIVE_PATH, '/', -1) as FILE_NAME,
                    SIZE as FILE_SIZE,
                    LAST_MODIFIED::TIMESTAMP_NTZ as LAST_MODIFIED,
                    ETAG,
                    DOC_TYPE,
                    'LAYOUT' as PARSE_MODE,
                    PARSED_JSON,
                    COALESCE(
                        PARSED_JSON:content::VARCHAR,
                        ARRAY_TO_STRING(
                            TRANSFORM(PARSED_JSON:pages, p -> p:content::VARCHAR),
                            '\\n\\n'
                        )
                    ) as EXTRACTED_TEXT,
                    'PARSED' as PARSE_STATUS,
                    CURRENT_TIMESTAMP() as PARSED_AT
                FROM parsed_docs
            ) src
            ON tgt.FILE_PATH = src.FILE_PATH AND tgt.ETAG = src.ETAG
            WHEN NOT MATCHED THEN INSERT (
                FILE_PATH, FILE_NAME, FILE_SIZE, LAST_MODIFIED, ETAG, DOC_TYPE,
                PARSE_MODE, PARSED_JSON, EXTRACTED_TEXT, PARSE_STATUS, PARSED_AT
            ) VALUES (
                src.FILE_PATH, src.FILE_NAME, src.FILE_SIZE, src.LAST_MODIFIED, src.ETAG, src.DOC_TYPE,
                src.PARSE_MODE, src.PARSED_JSON, src.EXTRACTED_TEXT, src.PARSE_STATUS, src.PARSED_AT
            )
        """).collect()
        log_detail(f"  Created parse task: {pipeline['parse_task']}")

        session.sql(f"""
            CREATE OR REPLACE TASK {chunk_task_fqn}
            WAREHOUSE = {warehouse}
            AFTER {parse_task_fqn}
            AS
            MERGE INTO {corpus_table_fqn} tgt
            USING (
                WITH parsed_with_tokens AS (
                    SELECT
                        FILE_PATH,
                        FILE_NAME,
                        DOC_TYPE,
                        EXTRACTED_TEXT,
                        AI_COUNT_TOKENS('ai_embed', '{config.AI_EMBEDDING_MODEL}', EXTRACTED_TEXT) as TOKEN_COUNT,
                        PARSED_AT
                    FROM {raw_table_fqn}
                    WHERE PARSE_STATUS = 'PARSED'
                      AND EXTRACTED_TEXT IS NOT NULL
                      AND LENGTH(EXTRACTED_TEXT) > 10
                ),
                enriched AS (
                    SELECT p.*,
                           rl.REGULATION_ID,
                           rl.REGULATORY_BODY,
                           rl.JURISDICTION,
                           rl.REFERENCE,
                           rl.SOURCE_URL,
                           rl.EFFECTIVE_DATE
                    FROM parsed_with_tokens p
                    LEFT JOIN {lookup_fqn} rl
                        ON rl.FILE_NAME = p.FILE_NAME
                ),
                short_docs AS (
                    SELECT
                        MD5(FILE_PATH) as DOCUMENT_ID,
                        FILE_PATH as SOURCE_FILE_PATH,
                        0 as CHUNK_INDEX,
                        COALESCE(REFERENCE || ' - ', '') || REPLACE(REPLACE(FILE_NAME, '.pdf', ''), '_', ' ') as DOCUMENT_TITLE,
                        DOC_TYPE as DOCUMENT_TYPE,
                        EXTRACTED_TEXT as DOCUMENT_TEXT,
                        TOKEN_COUNT,
                        'en' as LANGUAGE,
                        REGULATION_ID,
                        REGULATORY_BODY,
                        JURISDICTION,
                        REFERENCE,
                        SOURCE_URL,
                        EFFECTIVE_DATE as PUBLISH_DATE
                    FROM enriched
                    WHERE TOKEN_COUNT <= {CHUNK_TOKEN_THRESHOLD}
                ),
                long_docs_chunked AS (
                    SELECT
                        MD5(CONCAT(e.FILE_PATH, '|', c.index)) as DOCUMENT_ID,
                        e.FILE_PATH as SOURCE_FILE_PATH,
                        c.index as CHUNK_INDEX,
                        CONCAT(COALESCE(e.REFERENCE || ' - ', ''), REPLACE(REPLACE(e.FILE_NAME, '.pdf', ''), '_', ' '), ' (Part ', c.index + 1, ')') as DOCUMENT_TITLE,
                        e.DOC_TYPE as DOCUMENT_TYPE,
                        c.value::VARCHAR as DOCUMENT_TEXT,
                        AI_COUNT_TOKENS('ai_embed', '{config.AI_EMBEDDING_MODEL}', c.value::VARCHAR) as TOKEN_COUNT,
                        'en' as LANGUAGE,
                        e.REGULATION_ID,
                        e.REGULATORY_BODY,
                        e.JURISDICTION,
                        e.REFERENCE,
                        e.SOURCE_URL,
                        e.EFFECTIVE_DATE as PUBLISH_DATE
                    FROM enriched e,
                    LATERAL FLATTEN(
                        input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
                            e.EXTRACTED_TEXT, 
                            'markdown', 
                            {CHUNK_SIZE_CHARS},
                            {CHUNK_OVERLAP_CHARS}
                        )
                    ) c
                    WHERE e.TOKEN_COUNT > {CHUNK_TOKEN_THRESHOLD}
                ),
                all_chunks AS (
                    SELECT * FROM short_docs
                    UNION ALL
                    SELECT * FROM long_docs_chunked
                )
                SELECT * FROM all_chunks
            ) src
            ON tgt.DOCUMENT_ID = src.DOCUMENT_ID
            WHEN NOT MATCHED THEN INSERT (
                DOCUMENT_ID, SOURCE_FILE_PATH, CHUNK_INDEX, DOCUMENT_TITLE,
                DOCUMENT_TYPE, DOCUMENT_TEXT, TOKEN_COUNT, LANGUAGE,
                REGULATION_ID, REGULATORY_BODY, JURISDICTION, REFERENCE, SOURCE_URL, PUBLISH_DATE
            ) VALUES (
                src.DOCUMENT_ID, src.SOURCE_FILE_PATH, src.CHUNK_INDEX, src.DOCUMENT_TITLE,
                src.DOCUMENT_TYPE, src.DOCUMENT_TEXT, src.TOKEN_COUNT, src.LANGUAGE,
                src.REGULATION_ID, src.REGULATORY_BODY, src.JURISDICTION, src.REFERENCE, src.SOURCE_URL, src.PUBLISH_DATE
            )
        """).collect()
        log_detail(f"  Created chunk task: {pipeline['chunk_task']}")

        return True

    except Exception as e:
        log_error(f"Failed to create regulatory PDF pipeline: {e}")
        return False


def create_all_pdf_pipelines(session: Session) -> Tuple[int, int]:
    """Create all PDF pipelines (internal, external, and regulatory)."""
    success_count = 0
    fail_count = 0
    
    for pipeline_key in PDF_PIPELINES:
        if PDF_PIPELINES[pipeline_key].get('custom_pipeline'):
            if pipeline_key == 'regulatory':
                if create_regulatory_pdf_pipeline(session):
                    success_count += 1
                else:
                    fail_count += 1
        else:
            if create_pdf_pipeline(session, pipeline_key):
                success_count += 1
            else:
                fail_count += 1
    
    return success_count, fail_count


# =============================================================================
# CORPUS PIPELINE CREATION (RAW -> CURATED with chunking)
# =============================================================================

def get_corpus_pipeline_doc_types() -> List[str]:
    """Get list of document types that need corpus pipelines (non-real, non-PDF sources)."""
    return [
        doc_type for doc_type, cfg in config.DOCUMENT_TYPES.items()
        if cfg.get('source') != 'real'
        and config.PDF_DOC_AUDIENCE.get(doc_type, 'skip') not in ('internal', 'external')
    ]


def create_corpus_pipeline_task(session: Session, doc_type: str) -> bool:
    """
    Create a task to build a chunked corpus table from RAW markdown.
    
    Args:
        session: Snowpark session
        doc_type: Document type key from config.DOCUMENT_TYPES
    
    Returns:
        True if task created successfully (or skipped intentionally)
    """
    if doc_type not in config.DOCUMENT_TYPES:
        log_error(f"Unknown document type: {doc_type}")
        return False
    
    doc_config = config.DOCUMENT_TYPES[doc_type]
    if doc_config.get('source') == 'real':
        log_detail(f"  Skipping {doc_type} (real data source)")
        return True
    
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    curated_schema = config.DATABASE['schemas']['curated']
    warehouse = config.WAREHOUSES['execution']['name']
    
    raw_table = doc_config['table_name']
    corpus_table = doc_config['corpus_name']
    linkage_level = doc_config.get('linkage_level', 'global')
    
    task_name = f"CORPUS_{doc_type.upper()}_BUILD"
    task_fqn = f"{database}.{curated_schema}.{task_name}"
    raw_table_fqn = f"{database}.{raw_schema}.{raw_table}"
    corpus_table_fqn = f"{database}.{curated_schema}.{corpus_table}"
    
    # Build column list based on linkage level
    base_select = """
        DOCUMENT_ID as SOURCE_DOCUMENT_ID,
        DOCUMENT_TITLE,
        DOCUMENT_TYPE,
        SecurityID,
        IssuerID,
        PUBLISH_DATE,
        'en' as LANGUAGE,
        RAW_MARKDOWN"""
    
    base_insert_cols = """SOURCE_DOCUMENT_ID, DOCUMENT_ID, CHUNK_INDEX, 
        DOCUMENT_TITLE, DOCUMENT_TYPE, SecurityID, IssuerID, 
        PUBLISH_DATE, LANGUAGE, DOCUMENT_TEXT"""
    
    # Add linkage-specific columns
    extra_select = ""
    extra_insert_cols = ""
    if linkage_level == 'security':
        extra_select = ", TICKER, COMPANY_NAME, SIC_DESCRIPTION"
        extra_insert_cols = ", TICKER, COMPANY_NAME, SIC_DESCRIPTION"
    elif linkage_level == 'issuer':
        extra_select = ", TICKER"
        extra_insert_cols = ", TICKER"
    elif linkage_level == 'portfolio':
        extra_select = ", PortfolioID, PORTFOLIO_NAME"
        extra_insert_cols = ", PortfolioID, PORTFOLIO_NAME"
    
    # Add doc-type specific columns
    if doc_type in ['broker_research', 'internal_research']:
        extra_select += ", BROKER_NAME, RATING"
        extra_insert_cols += ", BROKER_NAME, RATING"
    elif doc_type == 'ngo_reports':
        extra_select += ", NGO_NAME, SEVERITY_LEVEL"
        extra_insert_cols += ", NGO_NAME, SEVERITY_LEVEL"
    elif doc_type == 'engagement_notes':
        extra_select += ", MEETING_TYPE"
        extra_insert_cols += ", MEETING_TYPE"
    
    try:
        # Create corpus task with conditional chunking
        # Schedule required for standalone tasks (we'll execute manually and suspend)
        session.sql(f"""
            CREATE OR REPLACE TASK {task_fqn}
            WAREHOUSE = {warehouse}
            SCHEDULE = '1440 MINUTE'
            AS
            CREATE OR REPLACE TABLE {corpus_table_fqn} AS
            WITH raw_with_tokens AS (
                SELECT 
                    {base_select}{extra_select},
                    AI_COUNT_TOKENS('ai_embed', '{config.AI_EMBEDDING_MODEL}', RAW_MARKDOWN) as TOKEN_COUNT
                FROM {raw_table_fqn}
                WHERE RAW_MARKDOWN IS NOT NULL
            ),
            -- Short docs: single chunk
            short_docs AS (
                SELECT
                    SOURCE_DOCUMENT_ID,
                    SOURCE_DOCUMENT_ID as DOCUMENT_ID,
                    0 as CHUNK_INDEX,
                    DOCUMENT_TITLE,
                    DOCUMENT_TYPE,
                    SecurityID,
                    IssuerID,
                    PUBLISH_DATE,
                    LANGUAGE,
                    RAW_MARKDOWN as DOCUMENT_TEXT
                    {extra_select}
                FROM raw_with_tokens
                WHERE TOKEN_COUNT <= {CHUNK_TOKEN_THRESHOLD}
            ),
            -- Long docs: chunked
            long_docs AS (
                SELECT
                    SOURCE_DOCUMENT_ID,
                    MD5(CONCAT(SOURCE_DOCUMENT_ID, '|', c.index)) as DOCUMENT_ID,
                    c.index as CHUNK_INDEX,
                    CONCAT(DOCUMENT_TITLE, ' (Part ', c.index + 1, ')') as DOCUMENT_TITLE,
                    DOCUMENT_TYPE,
                    SecurityID,
                    IssuerID,
                    PUBLISH_DATE,
                    LANGUAGE,
                    c.value::VARCHAR as DOCUMENT_TEXT
                    {extra_select}
                FROM raw_with_tokens r,
                LATERAL FLATTEN(
                    input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
                        r.RAW_MARKDOWN, 
                        'markdown', 
                        {CHUNK_SIZE_CHARS},
                        {CHUNK_OVERLAP_CHARS}
                    )
                ) c
                WHERE TOKEN_COUNT > {CHUNK_TOKEN_THRESHOLD}
            )
            SELECT * FROM short_docs
            UNION ALL
            SELECT * FROM long_docs
        """).collect()
        
        log_detail(f"  Created corpus task: {task_name} (SUSPENDED)")
        return True
        
    except Exception as e:
        log_error(f"Failed to create corpus task for {doc_type}: {e}")
        return False


def ensure_raw_tables_exist(session: Session) -> int:
    """
    Create empty RAW tables for all non-PDF document types.
    This ensures tables exist before corpus pipeline tasks reference them.
    
    Returns:
        Number of tables created
    """
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    
    tables_created = 0
    
    for doc_type, doc_config in config.DOCUMENT_TYPES.items():
        # Skip real data sources (they have their own table creation)
        if doc_config.get('source') == 'real':
            continue
        
        # Skip PDF doc types (they don't use RAW tables for hydration)
        audience = config.PDF_DOC_AUDIENCE.get(doc_type, 'skip')
        if audience in ('internal', 'external'):
            continue
        
        table_name = doc_config.get('table_name')
        if not table_name:
            continue
        
        table_fqn = f"{database}.{raw_schema}.{table_name}"
        linkage_level = doc_config.get('linkage_level', 'global')
        
        # Build column list based on linkage level
        base_cols = """
            DOCUMENT_ID VARCHAR(100),
            DOCUMENT_TITLE VARCHAR(500),
            DOCUMENT_TYPE VARCHAR(100),
            PUBLISH_DATE DATE,
            LANGUAGE VARCHAR(10),
            RAW_MARKDOWN VARCHAR(16777216)
        """
        
        extra_cols = ""
        if linkage_level == 'security':
            extra_cols = """,
            SecurityID INT,
            IssuerID INT,
            TICKER VARCHAR(16),
            COMPANY_NAME VARCHAR(200),
            SIC_DESCRIPTION VARCHAR(200)"""
        elif linkage_level == 'issuer':
            extra_cols = """,
            IssuerID INT,
            TICKER VARCHAR(16)"""
        elif linkage_level == 'portfolio':
            extra_cols = """,
            PortfolioID INT,
            PORTFOLIO_NAME VARCHAR(200)"""
        
        # Add doc-type specific columns
        if doc_type in ['broker_research', 'internal_research']:
            extra_cols += """,
            BROKER_NAME VARCHAR(200),
            RATING VARCHAR(50)"""
        elif doc_type == 'ngo_reports':
            extra_cols += """,
            NGO_NAME VARCHAR(200),
            SEVERITY_LEVEL VARCHAR(50)"""
        elif doc_type == 'engagement_notes':
            extra_cols += """,
            MEETING_TYPE VARCHAR(100)"""
        
        try:
            session.sql(f"""
                CREATE OR REPLACE TABLE {table_fqn} (
                    {base_cols}{extra_cols}
                )
            """).collect()
            tables_created += 1
        except Exception as e:
            log_warning(f"  Could not create RAW table {table_name}: {e}")
    
    return tables_created


def create_all_corpus_pipelines(session: Session) -> Tuple[int, int]:
    """Create corpus pipeline tasks for all non-real, non-PDF document types."""
    
    # First ensure all RAW tables exist (so tasks can reference them)
    log_substep("Ensuring RAW tables exist")
    tables_created = ensure_raw_tables_exist(session)
    log_detail(f"  Ensured {tables_created} RAW tables exist")
    
    doc_types = get_corpus_pipeline_doc_types()
    success_count = 0
    fail_count = 0
    
    log_substep("Creating corpus pipeline tasks")
    
    for doc_type in doc_types:
        if create_corpus_pipeline_task(session, doc_type):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count


# =============================================================================
# REAL TRANSCRIPTS PIPELINE (stream-triggered from RAW table)
# =============================================================================

def create_transcripts_pipeline(session: Session) -> bool:
    """
    Create task DAG for real company event transcripts pipeline.
    
    Pipeline-only architecture:
    1. TRANSCRIPTS_SPEAKER_STREAM + TRANSCRIPTS_CORPUS_STREAM on COMPANY_EVENT_TRANSCRIPTS_RAW table
    2. ROOT task: WHEN SYSTEM$STREAM_HAS_DATA() triggers on new transcripts
    3. SPEAKER_MAPPING task: AI_COMPLETE for speaker identification
    4. CORPUS_BUILD task: Segment extraction and chunking
    
    Uses actual SQL from generate_real_transcripts.py patterns.
    """
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    curated_schema = config.DATABASE['schemas']['curated']
    warehouse = config.WAREHOUSES['execution']['name']
    
    raw_table = f"{database}.{raw_schema}.COMPANY_EVENT_TRANSCRIPTS_RAW"
    speaker_stream_name = f"{database}.{raw_schema}.TRANSCRIPTS_SPEAKER_STREAM"
    corpus_stream_name = f"{database}.{raw_schema}.TRANSCRIPTS_CORPUS_STREAM"
    speaker_mapping_table = f"{database}.{raw_schema}.COMP_EVENT_SPEAKER_MAPPING"
    corpus_table = f"{database}.{curated_schema}.COMPANY_EVENT_TRANSCRIPTS_CORPUS"
    dim_security_table = f"{database}.{curated_schema}.DIM_SECURITY"
    
    root_task = f"{database}.{raw_schema}.TRANSCRIPTS_PIPELINE_ROOT"
    speaker_task = f"{database}.{raw_schema}.TRANSCRIPTS_SPEAKER_MAPPING"
    corpus_task = f"{database}.{raw_schema}.TRANSCRIPTS_CORPUS_BUILD"
    
    # Token limit for chunking
    token_limit = 490
    
    log_substep("Creating real transcripts pipeline tasks")
    
    try:
        # Create fresh RAW table (ensures no leftover data from previous builds)
        session.sql(f"""
            CREATE OR REPLACE TABLE {raw_table} (
                TRANSCRIPT_ID VARCHAR,
                COMPANY_ID VARCHAR,
                CIK VARCHAR,
                COMPANY_NAME VARCHAR,
                PRIMARY_TICKER VARCHAR(16),
                EVENT_TYPE VARCHAR,
                EVENT_TIMESTAMP TIMESTAMP_NTZ,
                FISCAL_PERIOD VARCHAR,
                FISCAL_YEAR VARCHAR,
                TRANSCRIPT_TYPE VARCHAR,
                TRANSCRIPT_JSON VARIANT,
                IssuerID INT,
                SecurityID INT,
                CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """).collect()
        log_detail(f"  Created table: COMPANY_EVENT_TRANSCRIPTS_RAW")
        
        # Create streams on the fresh table
        session.sql(f"""
            CREATE OR REPLACE STREAM {speaker_stream_name}
            ON TABLE {raw_table}
        """).collect()
        session.sql(f"""
            CREATE OR REPLACE STREAM {corpus_stream_name}
            ON TABLE {raw_table}
        """).collect()
        log_detail(f"  Created streams: TRANSCRIPTS_SPEAKER_STREAM, TRANSCRIPTS_CORPUS_STREAM")
        
        # Root task: Triggered when stream has data
        session.sql(f"""
            CREATE OR REPLACE TASK {root_task}
            WAREHOUSE = {warehouse}
            SCHEDULE = '5 MINUTE'
            WHEN SYSTEM$STREAM_HAS_DATA('{speaker_stream_name}')
            AS
            SELECT 'Transcripts pipeline triggered - processing new transcripts' AS status
        """).collect()
        log_detail(f"  Created root task: TRANSCRIPTS_PIPELINE_ROOT (SUSPENDED)")
        
        # Speaker mapping task: Extract speakers using AI_COMPLETE
        # Note: CORTEX.COMPLETE returns VARCHAR, need TRY_PARSE_JSON to convert to OBJECT
        speaker_sql = f"""
            CREATE OR REPLACE TASK {speaker_task}
            WAREHOUSE = {warehouse}
            USER_TASK_TIMEOUT_MS = 7200000
            AFTER {root_task}
            AS
            INSERT INTO {speaker_mapping_table}
            WITH all_paragraphs AS (
                SELECT 
                    t.TRANSCRIPT_ID,
                    t.COMPANY_ID,
                    t.CIK,
                    t.COMPANY_NAME,
                    t.PRIMARY_TICKER,
                    t.EVENT_TYPE,
                    t.EVENT_TIMESTAMP,
                    t.FISCAL_PERIOD,
                    t.FISCAL_YEAR,
                    t.TRANSCRIPT_TYPE,
                    p.index AS para_index,
                    p.value:speaker::text AS speaker_id,
                    p.value:text::text AS para_text
                FROM {raw_table} t
                INNER JOIN {database}.{curated_schema}.DIM_COVERAGE_UNIVERSE cu ON t.IssuerID = cu.ISSUERID,
                LATERAL FLATTEN(input => t.TRANSCRIPT_JSON:paragraphs) p
                WHERE t.TRANSCRIPT_ID IN (
                    SELECT TRANSCRIPT_ID FROM {speaker_stream_name} WHERE METADATA$ACTION = 'INSERT'
                )
            ),
            first_appearances AS (
                SELECT *
                FROM all_paragraphs
                QUALIFY para_index = MIN(para_index) OVER (PARTITION BY TRANSCRIPT_ID, speaker_id)
            ),
            with_context AS (
                SELECT 
                    fa.*,
                    prev.para_text AS prev_para_text
                FROM first_appearances fa
                LEFT JOIN all_paragraphs prev
                    ON fa.TRANSCRIPT_ID = prev.TRANSCRIPT_ID
                    AND prev.para_index = fa.para_index - 1
            ),
            ai_responses AS (
                SELECT 
                    wc.*,
                    TRY_PARSE_JSON(
                        REGEXP_REPLACE(REGEXP_REPLACE(
                            AI_COMPLETE('{config.AI_SPEAKER_IDENTIFICATION_MODEL}', CONCAT(
                                'Task: Extract the name, role, and company of the person who is about to speak in this ',
                                wc.EVENT_TYPE, ' for ', wc.COMPANY_NAME, ' on ', DATE(wc.EVENT_TIMESTAMP)::VARCHAR, '.\\n\\n',
                                'You have two text excerpts. Follow these steps:\\n',
                                'Step 1: Check INTRODUCTION. If it contains a person''s name (e.g. "next question from Brett Simpson, Arete Research"), that IS the speaker. Extract their name, role, and company directly.\\n',
                                'Step 2: Only if INTRODUCTION does not name anyone, check SPEAKER TEXT for self-identification (e.g. "This is Jeff Su, Director of IR").\\n',
                                'Step 3: If "Thank you, [Name]" appears in SPEAKER TEXT, note that [Name] is the PREVIOUS person, NOT this speaker.\\n\\n',
                                'RULES for the returned values:\\n',
                                '- speaker_name: Full name only (e.g. "Brett Simpson"). No titles, no descriptions.\\n',
                                '- speaker_role: Short job title only (e.g. "CFO", "VP of IR", "Research Analyst"). Max 5 words. Never quote the transcript.\\n',
                                '- speaker_company: Company name only (e.g. "JPMorgan", "TSMC"). No descriptions.\\n',
                                '- If unknown, use empty string "".\\n\\n',
                                CASE WHEN wc.prev_para_text IS NOT NULL
                                     THEN CONCAT('INTRODUCTION: ', LEFT(wc.prev_para_text, 500), '\\n\\n')
                                     ELSE '' END,
                                'SPEAKER TEXT: ', LEFT(wc.para_text, 500), '\\n\\n',
                                'Return ONLY: {{\"speaker_name\": \"...\", \"speaker_role\": \"...\", \"speaker_company\": \"...\"}}' 
                            )),
                            '^```json\\\\s*', ''), '\\\\s*```$', '')
                    ) AS parsed_response
                FROM with_context wc
            )
            SELECT 
                a.COMPANY_ID,
                a.CIK,
                a.COMPANY_NAME,
                a.PRIMARY_TICKER,
                a.EVENT_TYPE,
                a.EVENT_TIMESTAMP,
                a.FISCAL_PERIOD,
                a.FISCAL_YEAR,
                a.TRANSCRIPT_TYPE,
                CONCAT('SPEAKER_', a.speaker_id) AS SPEAKER_ID,
                LEFT(a.parsed_response:speaker_name::STRING, 200) AS SPEAKER_NAME,
                LEFT(a.parsed_response:speaker_role::STRING, 200) AS SPEAKER_ROLE,
                LEFT(a.parsed_response:speaker_company::STRING, 200) AS SPEAKER_COMPANY
            FROM ai_responses a
            WHERE a.parsed_response IS NOT NULL
        """
        session.sql(speaker_sql).collect()
        log_detail(f"  Created speaker task: TRANSCRIPTS_SPEAKER_MAPPING (SUSPENDED)")
        
        # Corpus build task: Extract segments, chunk, and build corpus
        corpus_sql = f"""
            CREATE OR REPLACE TASK {corpus_task}
            WAREHOUSE = {warehouse}
            AFTER {speaker_task}
            AS
            INSERT INTO {corpus_table}
            WITH 
            base AS (
                SELECT 
                    t.TRANSCRIPT_ID,
                    t.COMPANY_ID,
                    t.CIK,
                    t.COMPANY_NAME,
                    t.PRIMARY_TICKER,
                    t.EVENT_TYPE,
                    t.EVENT_TIMESTAMP,
                    t.FISCAL_PERIOD,
                    t.FISCAL_YEAR,
                    t.TRANSCRIPT_TYPE,
                    t.IssuerID,
                    t.SecurityID,
                    p.index AS para_index,
                    p.value:speaker::text AS speaker_id_raw,
                    p.value:text::text AS para_text
                FROM {raw_table} t
                INNER JOIN {database}.{curated_schema}.DIM_COVERAGE_UNIVERSE cu ON t.IssuerID = cu.ISSUERID,
                LATERAL FLATTEN(input => t.TRANSCRIPT_JSON:paragraphs) p
                WHERE t.TRANSCRIPT_ID IN (
                    SELECT TRANSCRIPT_ID FROM {corpus_stream_name} WHERE METADATA$ACTION = 'INSERT'
                )
            ),
            speaker_changes AS (
                SELECT *,
                    CASE WHEN LAG(speaker_id_raw) OVER (PARTITION BY TRANSCRIPT_ID ORDER BY para_index)
                         IS DISTINCT FROM speaker_id_raw THEN 1 ELSE 0 END AS is_new_group
                FROM base
            ),
            speaker_groups AS (
                SELECT *,
                    SUM(is_new_group) OVER (PARTITION BY TRANSCRIPT_ID ORDER BY para_index) AS speaker_group_id
                FROM speaker_changes
            ),
            grouped_turns AS (
                SELECT
                    TRANSCRIPT_ID, COMPANY_ID, CIK, COMPANY_NAME,
                    PRIMARY_TICKER, EVENT_TYPE, EVENT_TIMESTAMP,
                    FISCAL_PERIOD, FISCAL_YEAR, TRANSCRIPT_TYPE,
                    ANY_VALUE(IssuerID) AS IssuerID,
                    ANY_VALUE(SecurityID) AS SecurityID,
                    speaker_group_id,
                    MIN(para_index) AS speaker_order,
                    CONCAT('SPEAKER_', ANY_VALUE(speaker_id_raw)) AS speaker_id,
                    LISTAGG(para_text, '\\n\\n') WITHIN GROUP (ORDER BY para_index) AS segment_text
                FROM speaker_groups
                GROUP BY TRANSCRIPT_ID, COMPANY_ID, CIK, COMPANY_NAME,
                         PRIMARY_TICKER, EVENT_TYPE, EVENT_TIMESTAMP,
                         FISCAL_PERIOD, FISCAL_YEAR, TRANSCRIPT_TYPE,
                         speaker_group_id
            ),
            
            enriched_segments AS (
                SELECT 
                    s.*,
                    COALESCE(NULLIF(m.SPEAKER_NAME, ''), s.speaker_id) AS speaker_name,
                    COALESCE(NULLIF(m.SPEAKER_ROLE, ''), 'Unknown') AS speaker_role,
                    COALESCE(NULLIF(m.SPEAKER_COMPANY, ''), s.COMPANY_NAME) AS speaker_company,
                    SNOWFLAKE.CORTEX.COUNT_TOKENS('snowflake-arctic-embed-m-v1.5', s.segment_text) AS token_count
                FROM grouped_turns s
                LEFT JOIN {speaker_mapping_table} m
                    ON s.COMPANY_ID = m.COMPANY_ID
                    AND s.CIK = m.CIK
                    AND s.EVENT_TYPE = m.EVENT_TYPE
                    AND s.EVENT_TIMESTAMP = m.EVENT_TIMESTAMP
                    AND s.speaker_id = m.SPEAKER_ID
            ),
            
            short_segments AS (
                SELECT *, segment_text AS chunk_text, 0 AS chunk_index
                FROM enriched_segments
                WHERE token_count <= {token_limit}
            ),
            
            chunked_long AS (
                SELECT 
                    ls.*,
                    c.value::STRING AS chunk_text,
                    c.index AS chunk_index
                FROM enriched_segments ls,
                LATERAL FLATTEN(
                    input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(ls.segment_text, 'markdown', {token_limit})
                ) c
                WHERE ls.token_count > {token_limit}
            ),
            
            all_chunks AS (
                SELECT * FROM short_segments
                UNION ALL
                SELECT * FROM chunked_long
            ),
            
            enriched_chunks AS (
                SELECT 
                    ac.*,
                    i.GICS_SECTOR
                FROM all_chunks ac
                LEFT JOIN {database}.{curated_schema}.DIM_ISSUER i
                    ON ac.IssuerID = i.IssuerID
            )
            
            SELECT 
                MD5(CONCAT(CIK, EVENT_TIMESTAMP::VARCHAR, COALESCE(TRANSCRIPT_TYPE, ''), speaker_group_id::VARCHAR, chunk_index::VARCHAR)) AS DOCUMENT_ID,
                CONCAT(COMPANY_NAME, ' ', EVENT_TYPE, ' - ', DATE(EVENT_TIMESTAMP)::VARCHAR) AS DOCUMENT_TITLE,
                'company_event_transcripts' AS DOCUMENT_TYPE,
                SecurityID,
                IssuerID,
                DATE(EVENT_TIMESTAMP) AS PUBLISH_DATE,
                'en' AS LANGUAGE,
                EVENT_TYPE,
                speaker_order AS SEGMENT_INDEX,
                chunk_index AS CHUNK_INDEX,
                CONCAT(speaker_name, ' (', speaker_role, '): ', chunk_text) AS DOCUMENT_TEXT,
                PRIMARY_TICKER AS TICKER,
                COMPANY_NAME,
                GICS_SECTOR,
                LEFT(speaker_name, 500) AS SPEAKER_NAME,
                LEFT(speaker_role, 200) AS SPEAKER_ROLE,
                FISCAL_YEAR,
                FISCAL_PERIOD
            FROM enriched_chunks
        """
        session.sql(corpus_sql).collect()
        log_detail(f"  Created corpus task: TRANSCRIPTS_CORPUS_BUILD (SUSPENDED)")
        
        # Create speaker mapping table if not exists
        session.sql(f"""
            CREATE OR REPLACE TABLE {speaker_mapping_table} (
                COMPANY_ID VARCHAR,
                CIK VARCHAR,
                COMPANY_NAME VARCHAR,
                PRIMARY_TICKER VARCHAR(16),
                EVENT_TYPE VARCHAR,
                EVENT_TIMESTAMP TIMESTAMP_NTZ,
                FISCAL_PERIOD VARCHAR,
                FISCAL_YEAR VARCHAR,
                TRANSCRIPT_TYPE VARCHAR,
                SPEAKER_ID VARCHAR,
                SPEAKER_NAME VARCHAR,
                SPEAKER_ROLE VARCHAR,
                SPEAKER_COMPANY VARCHAR
            )
        """).collect()
        
        # Create corpus table (CREATE OR REPLACE for idempotent rebuilds)
        session.sql(f"""
            CREATE OR REPLACE TABLE {corpus_table} (
                DOCUMENT_ID VARCHAR,
                DOCUMENT_TITLE VARCHAR,
                DOCUMENT_TYPE VARCHAR,
                SecurityID INT,
                IssuerID INT,
                PUBLISH_DATE DATE,
                LANGUAGE VARCHAR(10),
                EVENT_TYPE VARCHAR,
                SEGMENT_INDEX INT,
                CHUNK_INDEX INT,
                DOCUMENT_TEXT VARCHAR(16777216),
                TICKER VARCHAR(20),
                COMPANY_NAME VARCHAR(500),
                GICS_SECTOR VARCHAR(200),
                SPEAKER_NAME VARCHAR(500),
                SPEAKER_ROLE VARCHAR(200),
                FISCAL_YEAR VARCHAR,
                FISCAL_PERIOD VARCHAR
            )
        """).collect()
        
        return True
        
    except Exception as e:
        log_error(f"Failed to create transcripts pipeline: {e}")
        return False


# =============================================================================
# SEC FILING TEXT PIPELINE (stream-triggered from RAW table)
# =============================================================================

def create_sec_filings_pipeline(session: Session) -> bool:
    """
    Create task DAG for SEC filing text pipeline.
    
    Pipeline-only architecture:
    1. SEC_FILINGS_RAW_STREAM on SEC_FILING_TEXT_RAW table
    2. ROOT task: WHEN SYSTEM$STREAM_HAS_DATA() triggers on new filings
    3. CHUNK task: Conditional chunking (>512 tokens) to FACT_SEC_FILING_TEXT
    """
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    market_data_schema = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    warehouse = config.WAREHOUSES['execution']['name']
    
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['sec_filing_text']['table']
    
    raw_table = f"{database}.{raw_schema}.SEC_FILING_TEXT_RAW"
    stream_name = f"{database}.{raw_schema}.SEC_FILINGS_RAW_STREAM"
    target_table = f"{database}.{market_data_schema}.FACT_SEC_FILING_TEXT"
    dim_issuer_table = f"{database}.{curated_schema}.DIM_ISSUER"
    
    root_task = f"{database}.{raw_schema}.SEC_FILINGS_PIPELINE_ROOT"
    chunk_task = f"{database}.{raw_schema}.SEC_FILINGS_CHUNK"
    
    log_substep("Creating SEC filing text pipeline tasks")
    
    try:
        # Create fresh RAW table
        session.sql(f"""
            CREATE OR REPLACE TABLE {raw_table} (
                SEC_DOCUMENT_ID VARCHAR,
                CIK VARCHAR,
                ADSH VARCHAR,
                VARIABLE VARCHAR,
                VARIABLE_NAME VARCHAR,
                PERIOD_END_DATE DATE,
                FILING_TEXT VARCHAR(16777216),
                TEXT_LENGTH INT,
                IssuerID INT,
                CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """).collect()
        
        # Create stream on the fresh table
        session.sql(f"""
            CREATE OR REPLACE STREAM {stream_name}
            ON TABLE {raw_table}
        """).collect()
        log_detail(f"  Created table + stream: SEC_FILINGS_RAW")
        
        # Root task: Triggered when stream has data
        session.sql(f"""
            CREATE OR REPLACE TASK {root_task}
            WAREHOUSE = {warehouse}
            SCHEDULE = '5 MINUTE'
            WHEN SYSTEM$STREAM_HAS_DATA('{stream_name}')
            AS
            SELECT 'SEC filings pipeline triggered - processing new filings' AS status
        """).collect()
        log_detail(f"  Created root task: SEC_FILINGS_PIPELINE_ROOT (SUSPENDED)")
        
        chunk_sql = f"""
            CREATE OR REPLACE TASK {chunk_task}
            WAREHOUSE = {warehouse}
            AFTER {root_task}
            AS
            INSERT INTO {target_table} (
                IssuerID, FILING_TYPE, FISCAL_YEAR, FISCAL_QUARTER, DOCUMENT_TITLE,
                SEC_DOCUMENT_ID, ADSH, CIK, VARIABLE, VARIABLE_NAME,
                PERIOD_END_DATE, FILING_TEXT, TEXT_LENGTH, CHUNK_INDEX, TOTAL_CHUNKS,
                DATA_SOURCE, LOADED_AT
            )
            WITH new_filings AS (
                SELECT 
                    r.SEC_DOCUMENT_ID, r.CIK, r.ADSH, r.VARIABLE, r.VARIABLE_NAME,
                    r.PERIOD_END_DATE, r.FILING_TEXT, r.TEXT_LENGTH, r.IssuerID,
                    di.LegalName, di.PrimaryTicker,
                    CASE 
                        WHEN r.VARIABLE_NAME ILIKE '%10-K%' OR r.VARIABLE_NAME ILIKE '%10K%' THEN '10-K'
                        WHEN r.VARIABLE_NAME ILIKE '%10-Q%' OR r.VARIABLE_NAME ILIKE '%10Q%' THEN '10-Q'
                        WHEN r.VARIABLE_NAME ILIKE '%8-K%' OR r.VARIABLE_NAME ILIKE '%8K%' THEN '8-K'
                        WHEN r.VARIABLE_NAME ILIKE '%DEF 14A%' OR r.VARIABLE_NAME ILIKE '%proxy%' THEN 'DEF 14A'
                        ELSE 'SEC Filing'
                    END AS FILING_TYPE,
                    YEAR(r.PERIOD_END_DATE) AS FISCAL_YEAR,
                    CASE 
                        WHEN MONTH(r.PERIOD_END_DATE) IN (1,2,3) THEN 'Q1'
                        WHEN MONTH(r.PERIOD_END_DATE) IN (4,5,6) THEN 'Q2'
                        WHEN MONTH(r.PERIOD_END_DATE) IN (7,8,9) THEN 'Q3'
                        ELSE 'Q4'
                    END AS FISCAL_QUARTER,
                    SNOWFLAKE.CORTEX.COUNT_TOKENS('snowflake-arctic-embed-m-v1.5', r.FILING_TEXT) AS token_count
                FROM {raw_table} r
                JOIN {dim_issuer_table} di ON r.IssuerID = di.IssuerID
                INNER JOIN {database}.{curated_schema}.DIM_COVERAGE_UNIVERSE cu ON r.IssuerID = cu.ISSUERID
                WHERE r.SEC_DOCUMENT_ID IN (
                    SELECT SEC_DOCUMENT_ID FROM {stream_name} WHERE METADATA$ACTION = 'INSERT'
                )
            ),
            
            short_texts AS (
                SELECT 
                    IssuerID, FILING_TYPE, FISCAL_YEAR, FISCAL_QUARTER,
                    CONCAT(LegalName,
                        CASE WHEN PrimaryTicker IS NOT NULL THEN CONCAT(' (', PrimaryTicker, ')') ELSE '' END,
                        ' - ', FILING_TYPE, ' ', FISCAL_YEAR, ' ', FISCAL_QUARTER,
                        ' - ', VARIABLE_NAME
                    ) AS DOCUMENT_TITLE,
                    SEC_DOCUMENT_ID, ADSH, CIK, VARIABLE, VARIABLE_NAME,
                    PERIOD_END_DATE,
                    FILING_TEXT,
                    TEXT_LENGTH,
                    0 AS CHUNK_INDEX, 1 AS TOTAL_CHUNKS,
                    'PIPELINE' AS DATA_SOURCE, CURRENT_TIMESTAMP() AS LOADED_AT
                FROM new_filings
                WHERE token_count <= {CHUNK_TOKEN_THRESHOLD}
            ),
            
            long_texts_chunked AS (
                SELECT 
                    nf.IssuerID, nf.FILING_TYPE, nf.FISCAL_YEAR, nf.FISCAL_QUARTER,
                    CONCAT(nf.LegalName,
                        CASE WHEN nf.PrimaryTicker IS NOT NULL THEN CONCAT(' (', nf.PrimaryTicker, ')') ELSE '' END,
                        ' - ', nf.FILING_TYPE, ' ', nf.FISCAL_YEAR, ' ', nf.FISCAL_QUARTER,
                        ' - ', nf.VARIABLE_NAME,
                        ' [Part ', c.index + 1, ']'
                    ) AS DOCUMENT_TITLE,
                    CONCAT(nf.SEC_DOCUMENT_ID, '_', c.index) AS SEC_DOCUMENT_ID,
                    nf.ADSH, nf.CIK, nf.VARIABLE, nf.VARIABLE_NAME,
                    nf.PERIOD_END_DATE,
                    c.value::VARCHAR AS FILING_TEXT,
                    LENGTH(c.value::VARCHAR) AS TEXT_LENGTH,
                    c.index AS CHUNK_INDEX,
                    ARRAY_SIZE(SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(nf.FILING_TEXT, 'markdown', {CHUNK_SIZE_CHARS})) AS TOTAL_CHUNKS,
                    'PIPELINE' AS DATA_SOURCE, CURRENT_TIMESTAMP() AS LOADED_AT
                FROM new_filings nf,
                LATERAL FLATTEN(
                    input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(nf.FILING_TEXT, 'markdown', {CHUNK_SIZE_CHARS})
                ) c
                WHERE nf.token_count > {CHUNK_TOKEN_THRESHOLD}
            )
            
            SELECT * FROM short_texts
            UNION ALL
            SELECT * FROM long_texts_chunked
        """
        session.sql(chunk_sql).collect()
        log_detail(f"  Created chunk task: SEC_FILINGS_CHUNK (SUSPENDED)")
        
        session.sql(f"""
            CREATE OR REPLACE TABLE {target_table} (
                FILING_TEXT_ID INT IDENTITY,
                IssuerID INT,
                FILING_TYPE VARCHAR(20),
                FISCAL_YEAR INT,
                FISCAL_QUARTER VARCHAR(5),
                DOCUMENT_TITLE VARCHAR,
                SEC_DOCUMENT_ID VARCHAR,
                ADSH VARCHAR,
                CIK VARCHAR,
                VARIABLE VARCHAR,
                VARIABLE_NAME VARCHAR,
                PERIOD_END_DATE DATE,
                FILING_TEXT VARCHAR(16777216),
                TEXT_LENGTH INT,
                CHUNK_INDEX INT DEFAULT 0,
                TOTAL_CHUNKS INT DEFAULT 1,
                DATA_SOURCE VARCHAR DEFAULT 'PIPELINE',
                LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """).collect()
        
        return True
        
    except Exception as e:
        log_error(f"Failed to create SEC filing pipeline: {e}")
        return False


def load_sec_filings_raw(session: Session, test_mode: bool = False) -> int:
    """
    Load SEC filing text into SEC_FILING_TEXT_RAW table.
    This triggers the SEC_FILINGS_RAW_STREAM for pipeline processing.
    
    Args:
        session: Active Snowpark session
        test_mode: If True, limit records for faster testing
    
    Returns:
        Number of filings loaded
    """
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    curated_schema = config.DATABASE['schemas']['curated']
    
    source_db = config.REAL_DATA_SOURCES['database']
    source_schema = config.REAL_DATA_SOURCES['schema']
    source_table = config.REAL_DATA_SOURCES['tables']['sec_filing_text']['table']
    
    raw_table = f"{database}.{raw_schema}.SEC_FILING_TEXT_RAW"
    dim_issuer_table = f"{database}.{curated_schema}.DIM_ISSUER"
    
    log_substep("Loading SEC filings to RAW table")
    
    # Limit for test mode
    limit_clause = "LIMIT 100" if test_mode else ""
    
    # Load from source into RAW table
    load_sql = f"""
    INSERT INTO {raw_table} (
        SEC_DOCUMENT_ID,
        CIK,
        ADSH,
        VARIABLE,
        VARIABLE_NAME,
        PERIOD_END_DATE,
        FILING_TEXT,
        TEXT_LENGTH,
        IssuerID
    )
    SELECT 
        t.SEC_DOCUMENT_ID,
        t.CIK,
        t.ADSH,
        t.VARIABLE,
        t.VARIABLE_NAME,
        t.PERIOD_END_DATE,
        t.VALUE AS FILING_TEXT,
        LENGTH(t.VALUE) AS TEXT_LENGTH,
        i.IssuerID
    FROM {source_db}.{source_schema}.{source_table} t
    INNER JOIN {dim_issuer_table} i ON t.CIK = i.CIK
    INNER JOIN {database}.{curated_schema}.DIM_COVERAGE_UNIVERSE cu ON i.IssuerID = cu.ISSUERID
    WHERE t.PERIOD_END_DATE >= DATEADD('year', -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
      AND LENGTH(t.VALUE) > 100
    {limit_clause}
    """
    
    try:
        session.sql(load_sql).collect()
        
        # Get count for logging
        count_result = session.sql(f"SELECT COUNT(*) as cnt FROM {raw_table}").collect()
        filing_count = count_result[0]['CNT']
        log_detail(f"  Loaded {filing_count:,} SEC filings to RAW table (stream will trigger pipeline)")
        
        return filing_count
        
    except Exception as e:
        log_error(f"Failed to load SEC filings to RAW table: {e}")
        raise


# =============================================================================
# TASK ORCHESTRATION: Enable, Execute, Wait, Suspend
# =============================================================================

def enable_task_graph(session: Session, root_task_fqn: str) -> bool:
    """
    Enable all tasks in a task graph using SYSTEM$TASK_DEPENDENTS_ENABLE.
    
    Args:
        session: Snowpark session
        root_task_fqn: Fully qualified root task name
    
    Returns:
        True if successful
    """
    try:
        session.sql(f"SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('{root_task_fqn}')").collect()
        log_detail(f"  Enabled task graph: {root_task_fqn}")
        return True
    except Exception as e:
        log_error(f"Failed to enable task graph {root_task_fqn}: {e}")
        return False


def execute_task(session: Session, task_fqn: str) -> bool:
    """
    Execute a task once using EXECUTE TASK.
    
    Args:
        session: Snowpark session
        task_fqn: Fully qualified task name
    
    Returns:
        True if execution started successfully
    """
    try:
        session.sql(f"EXECUTE TASK {task_fqn}").collect()
        log_detail(f"  Executed task: {task_fqn}")
        return True
    except Exception as e:
        log_error(f"Failed to execute task {task_fqn}: {e}")
        return False


def wait_for_task_completion(session: Session, root_task_fqn: str, timeout_seconds: int = 600) -> bool:
    """
    Poll task history until ALL tasks in the graph complete or timeout.
    
    This function checks the entire task DAG (root + children), not just the root task.
    A task graph is considered complete when:
    - All tasks have finished (SUCCEEDED or FAILED/CANCELLED)
    - Any FAILED task causes immediate return with False
    
    Args:
        session: Snowpark session
        root_task_fqn: Fully qualified root task name
        timeout_seconds: Maximum time to wait
    
    Returns:
        True if ALL tasks completed successfully, False if any failed or timed out
    """
    parts = root_task_fqn.split('.')
    if len(parts) != 3:
        log_error(f"Invalid task FQN: {root_task_fqn}")
        return False
    
    database, schema, root_task_name = parts
    
    # Get all tasks in the graph (root + children)
    try:
        all_tasks_result = session.sql(f"""
            SELECT NAME
            FROM TABLE({database}.INFORMATION_SCHEMA.TASK_DEPENDENTS(
                TASK_NAME => '{root_task_fqn}',
                RECURSIVE => TRUE
            ))
        """).collect()
        task_names = [row['NAME'] for row in all_tasks_result]
    except Exception as e:
        log_warning(f"  Could not get task dependents, falling back to root only: {e}")
        task_names = [root_task_name]
    
    log_detail(f"  Monitoring {len(task_names)} tasks: {', '.join(task_names)}")
    
    start_time = time.time()
    poll_interval = 5  # seconds
    execution_start = None  # Track when root task started
    
    while (time.time() - start_time) < timeout_seconds:
        try:
            # Check status of ALL tasks in the graph
            tasks_in_clause = ', '.join([f"'{t}'" for t in task_names])
            result = session.sql(f"""
                SELECT NAME, STATE, ERROR_MESSAGE, SCHEDULED_TIME
                FROM TABLE({database}.INFORMATION_SCHEMA.TASK_HISTORY())
                WHERE NAME IN ({tasks_in_clause})
                  AND SCHEDULED_TIME >= DATEADD('minute', -30, CURRENT_TIMESTAMP())
                QUALIFY ROW_NUMBER() OVER (PARTITION BY NAME ORDER BY SCHEDULED_TIME DESC) = 1
            """).collect()
            
            if not result:
                # No task history yet, keep waiting
                time.sleep(poll_interval)
                continue
            
            # Track execution start from root task
            for row in result:
                if row['NAME'] == root_task_name and execution_start is None:
                    execution_start = row['SCHEDULED_TIME']
            
            # Build status map (Row objects use bracket notation, not .get())
            task_states = {}
            for row in result:
                error_msg = row['ERROR_MESSAGE'] if row['ERROR_MESSAGE'] else ''
                task_states[row['NAME']] = (row['STATE'], error_msg)
            
            # Check for failures first
            for task_name, (state, error_msg) in task_states.items():
                if state == 'FAILED':
                    log_warning(f"  Task FAILED: {task_name} - {error_msg}")
                    return False
                elif state == 'CANCELLED':
                    log_warning(f"  Task CANCELLED: {task_name}")
                    return False
            
            # Check if all tasks completed successfully
            completed_tasks = [t for t, (s, _) in task_states.items() if s == 'SUCCEEDED']
            running_tasks = [t for t, (s, _) in task_states.items() if s in ('SCHEDULED', 'EXECUTING')]
            
            if len(completed_tasks) == len(task_names):
                log_detail(f"  All {len(task_names)} tasks completed successfully")
                return True
            
            # Log progress periodically
            elapsed = int(time.time() - start_time)
            if elapsed % 15 == 0 and elapsed > 0:
                log_detail(f"  Progress: {len(completed_tasks)}/{len(task_names)} tasks complete, {len(running_tasks)} running ({elapsed}s elapsed)")
            
            time.sleep(poll_interval)
            
        except Exception as e:
            log_warning(f"  Error polling task history: {e}")
            time.sleep(poll_interval)
    
    log_warning(f"  Task graph timed out after {timeout_seconds}s: {root_task_fqn}")
    return False


def suspend_task_graph(session: Session, root_task_fqn: str) -> bool:
    """
    Suspend all tasks in a task graph.
    
    Args:
        session: Snowpark session
        root_task_fqn: Fully qualified root task name
    
    Returns:
        True if all tasks suspended successfully
    """
    parts = root_task_fqn.split('.')
    if len(parts) != 3:
        log_error(f"Invalid task FQN: {root_task_fqn}")
        return False
    
    database, schema, task_name = parts
    
    try:
        # Get all tasks in the graph
        tasks = session.sql(f"""
            SELECT DATABASE_NAME, SCHEMA_NAME, NAME
            FROM TABLE({database}.INFORMATION_SCHEMA.TASK_DEPENDENTS(
                TASK_NAME => '{root_task_fqn}',
                RECURSIVE => TRUE
            ))
        """).collect()
        
        # Suspend each task (children first, then root)
        for task in reversed(tasks):
            task_fqn = f"{task['DATABASE_NAME']}.{task['SCHEMA_NAME']}.{task['NAME']}"
            try:
                session.sql(f"ALTER TASK {task_fqn} SUSPEND").collect()
            except Exception:
                pass  # Task might already be suspended
        
        log_detail(f"  Suspended task graph: {root_task_fqn} ({len(tasks)} tasks)")
        return True
        
    except Exception as e:
        log_error(f"Failed to suspend task graph {root_task_fqn}: {e}")
        return False


def run_task_graph_once(session: Session, root_task_fqn: str, timeout_seconds: int = 600) -> bool:
    """
    Enable, execute, wait for completion, and suspend a task graph.
    
    Args:
        session: Snowpark session
        root_task_fqn: Fully qualified root task name
        timeout_seconds: Maximum time to wait for completion
    
    Returns:
        True if pipeline ran successfully
    """
    log_detail(f"Running task graph once: {root_task_fqn}")
    
    # Enable the graph
    if not enable_task_graph(session, root_task_fqn):
        return False
    
    # Execute the root task
    if not execute_task(session, root_task_fqn):
        suspend_task_graph(session, root_task_fqn)
        return False
    
    # Wait for completion
    success = wait_for_task_completion(session, root_task_fqn, timeout_seconds)
    
    # Suspend the graph regardless of success
    suspend_task_graph(session, root_task_fqn)
    
    return success


# =============================================================================
# PDF UPLOAD HELPERS
# =============================================================================

def get_pdf_audience(doc_type: str) -> str:
    """Get PDF audience (internal/external/skip) for a document type."""
    return config.PDF_DOC_AUDIENCE.get(doc_type, 'internal')


def upload_pdfs_to_stages(session: Session, pdf_base_dir: str = None) -> Tuple[int, int]:
    """
    Upload locally generated PDFs to the appropriate RAW stages.
    
    Args:
        session: Snowpark session
        pdf_base_dir: Base directory containing generated PDFs (default: config.UNSTRUCTURED_PDF_OUTPUT_DIR)
    
    Returns:
        Tuple of (uploaded_count, failed_count)
    """
    if pdf_base_dir is None:
        # data/ is inside python/, project root is parent of python/
        python_dir = os.path.dirname(os.path.dirname(__file__))
        project_root = os.path.dirname(python_dir)
        pdf_base_dir = os.path.join(
            project_root,
            config.UNSTRUCTURED_PDF_OUTPUT_DIR
        )
    
    if not os.path.exists(pdf_base_dir):
        log_warning(f"PDF directory not found: {pdf_base_dir}")
        return 0, 0
    
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    
    internal_stage = f"@{database}.{raw_schema}.{PDF_PIPELINES['internal']['stage_name']}"
    external_stage = f"@{database}.{raw_schema}.{PDF_PIPELINES['external']['stage_name']}"
    
    uploaded = 0
    failed = 0
    
    log_substep("Uploading PDFs to RAW stages")
    
    for doc_type in os.listdir(pdf_base_dir):
        doc_type_dir = os.path.join(pdf_base_dir, doc_type)
        if not os.path.isdir(doc_type_dir):
            continue
        
        audience = get_pdf_audience(doc_type)
        if audience == 'skip':
            continue
        
        stage = internal_stage if audience == 'internal' else external_stage
        
        for filename in os.listdir(doc_type_dir):
            if not filename.lower().endswith('.pdf'):
                continue
            
            file_path = os.path.join(doc_type_dir, filename)
            stage_path = f"{stage}/{doc_type}"
            
            try:
                session.file.put(file_path, stage_path, overwrite=True, auto_compress=False)
                uploaded += 1
            except Exception as e:
                log_warning(f"Failed to upload {filename}: {e}")
                failed += 1
    
    log_detail(f"  Uploaded {uploaded} PDFs to RAW stages ({failed} failed)")
    
    reg_uploaded, reg_failed = _upload_regulatory_pdfs(session)
    uploaded += reg_uploaded
    failed += reg_failed
    
    return uploaded, failed


def _upload_regulatory_pdfs(session: Session) -> Tuple[int, int]:
    python_dir = os.path.dirname(os.path.dirname(__file__))
    project_root = os.path.dirname(python_dir)
    source_dir = os.path.join(project_root, 'data', 'source_pdfs', 'am_regulatory')

    if not os.path.exists(source_dir):
        log_detail("  No regulatory source PDFs directory found")
        return 0, 0

    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    stage_fqn = f"@{database}.{raw_schema}.{PDF_PIPELINES['regulatory']['stage_name']}"

    uploaded = 0
    failed = 0

    for filename in os.listdir(source_dir):
        if not filename.lower().endswith('.pdf'):
            continue
        file_path = os.path.join(source_dir, filename)
        try:
            session.file.put(file_path, f"{stage_fqn}/regulatory_docs", overwrite=True, auto_compress=False)
            uploaded += 1
        except Exception as e:
            log_warning(f"Failed to upload regulatory PDF {filename}: {e}")
            failed += 1

    log_detail(f"  Uploaded {uploaded} regulatory PDFs to stage ({failed} failed)")
    return uploaded, failed


def upload_skills_to_stage(session: Session) -> Tuple[int, int]:
    python_dir = os.path.dirname(os.path.dirname(__file__))
    project_root = os.path.dirname(python_dir)
    skills_dir = os.path.join(project_root, 'data', 'skills')

    if not os.path.exists(skills_dir):
        log_detail("  No skills directory found at data/skills/")
        return 0, 0

    database = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    stage_name = "SKILL_STAGE"
    stage_fqn = f"@{database}.{ai_schema}.{stage_name}"

    session.sql(f"""
        CREATE STAGE IF NOT EXISTS {database}.{ai_schema}.{stage_name}
        ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
        DIRECTORY = (ENABLE = TRUE)
        COMMENT = 'Agent skills (SKILL.md + scripts + references)'
    """).collect()

    uploaded = 0
    failed = 0

    for skill_name in sorted(os.listdir(skills_dir)):
        skill_path = os.path.join(skills_dir, skill_name)
        if not os.path.isdir(skill_path):
            continue

        for root, dirs, files in os.walk(skill_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(root, skills_dir)
                stage_path = f"{stage_fqn}/{rel_path}"
                try:
                    session.file.put(file_path, stage_path, overwrite=True, auto_compress=False)
                    uploaded += 1
                except Exception as e:
                    log_warning(f"Failed to upload skill file {rel_path}/{filename}: {e}")
                    failed += 1

    log_detail(f"  Uploaded {uploaded} skill files to {stage_name} ({failed} failed)")
    return uploaded, failed


def refresh_pdf_stages(session: Session) -> bool:
    """
    Refresh directory tables on all PDF stages.
    This makes uploaded files visible to streams.
    """
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    
    log_substep("Refreshing PDF stage directories")
    
    for pipeline_key, pipeline in PDF_PIPELINES.items():
        stage_fqn = f"{database}.{raw_schema}.{pipeline['stage_name']}"
        try:
            session.sql(f"ALTER STAGE {stage_fqn} REFRESH").collect()
            log_detail(f"  Refreshed: {pipeline['stage_name']}")
        except Exception as e:
            log_warning(f"Failed to refresh {pipeline['stage_name']}: {e}")
            return False
    
    return True


# =============================================================================
# PUBLIC API
# =============================================================================

def ensure_execute_task_privilege(session: Session) -> bool:
    """
    Ensure the current role has EXECUTE TASK privilege.
    
    This is required for the task owner role to execute tasks via EXECUTE TASK.
    The privilege must be granted by ACCOUNTADMIN or a role with MANAGE GRANTS.
    
    Returns:
        True if privilege is available or was granted, False otherwise
    """
    try:
        current_role = session.sql("SELECT CURRENT_ROLE()").collect()[0][0]
        
        # Check if we already have the privilege by trying a harmless operation
        # Unfortunately there's no direct way to check EXECUTE TASK privilege
        # We'll try to grant it and handle the error gracefully
        
        try:
            session.sql(f"GRANT EXECUTE TASK ON ACCOUNT TO ROLE {current_role}").collect()
            log_detail(f"  Granted EXECUTE TASK privilege to role {current_role}")
            return True
        except Exception as grant_error:
            error_msg = str(grant_error)
            if "already granted" in error_msg.lower() or "privilege" in error_msg.lower():
                # Privilege may already exist
                log_detail(f"  EXECUTE TASK privilege check for role {current_role}")
                return True
            else:
                log_warning(f"  Cannot grant EXECUTE TASK privilege (requires ACCOUNTADMIN)")
                log_warning(f"  Please run as ACCOUNTADMIN: GRANT EXECUTE TASK ON ACCOUNT TO ROLE {current_role};")
                return False
                
    except Exception as e:
        log_warning(f"  Could not check EXECUTE TASK privilege: {e}")
        return False


def create_all_pipelines(session: Session) -> Dict[str, Tuple[int, int]]:
    """
    Create all unstructured data pipelines (stages, streams, tables, tasks).
    All tasks are created SUSPENDED.
    
    Prerequisites:
    - The current role must have EXECUTE TASK privilege on the account
    - Grant with: GRANT EXECUTE TASK ON ACCOUNT TO ROLE <your_role>;
    
    Returns:
        Dict mapping pipeline category to (success_count, fail_count)
    """
    log_step("Creating unstructured data pipelines")
    
    # Ensure EXECUTE TASK privilege before creating tasks
    ensure_execute_task_privilege(session)
    
    results = {}
    
    # PDF pipelines
    results['pdf'] = create_all_pdf_pipelines(session)
    
    # Corpus pipelines
    results['corpus'] = create_all_corpus_pipelines(session)
    
    # Real transcripts pipeline
    results['transcripts'] = (1, 0) if create_transcripts_pipeline(session) else (0, 1)
    
    # SEC filings pipeline
    results['sec_filings'] = (1, 0) if create_sec_filings_pipeline(session) else (0, 1)
    
    # Summary
    total_success = sum(r[0] for r in results.values())
    total_fail = sum(r[1] for r in results.values())
    log_info(f"Created {total_success} pipeline components ({total_fail} failed)")
    
    if total_fail > 0:
        failed_pipelines = [name for name, (s, f) in results.items() if f > 0]
        raise Exception(
            f"Pipeline creation failed for: {', '.join(failed_pipelines)}. "
            f"{total_fail} component(s) failed. Halting setup to prevent cascading errors."
        )
    
    return results


def run_all_pipelines(session: Session, upload_pdfs: bool = True, timeout_seconds: int = 3600) -> bool:
    """
    Execute all pipelines once and suspend them.
    
    Pipeline-only architecture execution order:
    1. PDF pipelines (parse PDFs from stages)
    2. Corpus pipelines (chunk non-PDF RAW tables)
    3. Transcripts pipeline (speaker mapping + corpus build)
    4. SEC filings pipeline (chunking)
    
    Args:
        session: Snowpark session
        upload_pdfs: Whether to upload locally generated PDFs first
        timeout_seconds: Maximum time to wait for all pipelines (default 60 min)
    
    Returns:
        True if all pipelines completed successfully
    """
    log_step("Executing unstructured data pipelines")
    
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    curated_schema = config.DATABASE['schemas']['curated']
    
    # Upload PDFs if requested
    if upload_pdfs:
        upload_pdfs_to_stages(session)
        refresh_pdf_stages(session)
    
    # Collect all pipelines to run
    pipelines_to_run = []  # List of (name, root_task_fqn)
    
    # Check PDF pipelines
    log_substep("Checking pipelines for data")
    for pipeline_key, pipeline in PDF_PIPELINES.items():
        stream_fqn = f"{database}.{raw_schema}.{pipeline['stream_name']}"
        try:
            has_data = session.sql(f"SELECT SYSTEM$STREAM_HAS_DATA('{stream_fqn}')").collect()[0][0]
            if has_data:
                root_task_fqn = f"{database}.{raw_schema}.{pipeline['parse_task']}"
                pipelines_to_run.append((f"{pipeline_key}_pdf", root_task_fqn))
                log_detail(f"  {pipeline_key} PDF pipeline: has data")
            else:
                log_detail(f"  {pipeline_key} PDF pipeline: no data (skipping)")
        except Exception as e:
            log_warning(f"  Could not check {pipeline_key} PDF stream: {e}")
    
    # Check transcripts pipeline (two separate streams for speaker and corpus consumers)
    transcripts_speaker_stream = f"{database}.{raw_schema}.TRANSCRIPTS_SPEAKER_STREAM"
    transcripts_corpus_stream = f"{database}.{raw_schema}.TRANSCRIPTS_CORPUS_STREAM"
    try:
        speaker_has_data = session.sql(f"SELECT SYSTEM$STREAM_HAS_DATA('{transcripts_speaker_stream}')").collect()[0][0]
        corpus_has_data = session.sql(f"SELECT SYSTEM$STREAM_HAS_DATA('{transcripts_corpus_stream}')").collect()[0][0]
        if speaker_has_data or corpus_has_data:
            root_task_fqn = f"{database}.{raw_schema}.TRANSCRIPTS_PIPELINE_ROOT"
            pipelines_to_run.append(("transcripts", root_task_fqn))
            log_detail(f"  Transcripts pipeline: has data (speaker={speaker_has_data}, corpus={corpus_has_data})")
        else:
            log_detail(f"  Transcripts pipeline: no data (skipping)")
    except Exception as e:
        log_warning(f"  Could not check transcripts streams: {e}")
    
    # Check SEC filings pipeline
    sec_stream = f"{database}.{raw_schema}.SEC_FILINGS_RAW_STREAM"
    try:
        has_data = session.sql(f"SELECT SYSTEM$STREAM_HAS_DATA('{sec_stream}')").collect()[0][0]
        if has_data:
            root_task_fqn = f"{database}.{raw_schema}.SEC_FILINGS_PIPELINE_ROOT"
            pipelines_to_run.append(("sec_filings", root_task_fqn))
            log_detail(f"  SEC filings pipeline: has data")
        else:
            log_detail(f"  SEC filings pipeline: no data (skipping)")
    except Exception as e:
        log_warning(f"  Could not check SEC filings stream: {e}")
    
    if not pipelines_to_run:
        log_info("No pipelines have data to process")
        return True
    
    # Start all pipelines in parallel and record start time
    log_substep(f"Starting {len(pipelines_to_run)} pipelines in parallel")
    started_pipelines = []
    execution_start_time = time.time()
    
    for name, root_task_fqn in pipelines_to_run:
        try:
            if enable_task_graph(session, root_task_fqn):
                if execute_task(session, root_task_fqn):
                    started_pipelines.append((name, root_task_fqn))
                    log_detail(f"  Started: {name}")
                else:
                    log_warning(f"  Failed to execute: {name}")
                    suspend_task_graph(session, root_task_fqn)
            else:
                log_warning(f"  Failed to enable: {name}")
        except Exception as e:
            log_warning(f"  Error starting {name}: {e}")
    
    if not started_pipelines:
        log_warning("No pipelines were started")
        return False
    
    # Wait for all pipelines to complete using COMPLETE_TASK_GRAPHS
    log_substep(f"Waiting for {len(started_pipelines)} pipelines to complete (timeout: {timeout_seconds}s)")
    all_success = True
    completed = set()
    start_time = time.time()
    last_progress_log = 0
    database = config.DATABASE['name']
    
    while len(completed) < len(started_pipelines):
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            log_warning(f"Timeout after {int(elapsed)}s - some pipelines may still be running")
            all_success = False
            break
        
        for name, root_task_fqn in started_pipelines:
            if name in completed:
                continue
            
            try:
                # Extract just the task name (non-qualified) for COMPLETE_TASK_GRAPHS
                root_task_name = root_task_fqn.split('.')[-1]
                
                # First check if task graph is currently running
                running = session.sql(f"""
                    SELECT STATE
                    FROM TABLE({database}.INFORMATION_SCHEMA.CURRENT_TASK_GRAPHS(
                        ROOT_TASK_NAME => '{root_task_name}'
                    ))
                    LIMIT 1
                """).collect()
                
                if running:
                    # Still running - skip to next pipeline
                    continue
                
                # Check COMPLETE_TASK_GRAPHS for final status
                result = session.sql(f"""
                    SELECT ROOT_TASK_NAME, STATE, FIRST_ERROR_TASK_NAME, FIRST_ERROR_MESSAGE, SCHEDULED_TIME
                    FROM TABLE({database}.INFORMATION_SCHEMA.COMPLETE_TASK_GRAPHS(
                        RESULT_LIMIT => 10,
                        ROOT_TASK_NAME => '{root_task_name}'
                    ))
                    ORDER BY SCHEDULED_TIME DESC
                    LIMIT 1
                """).collect()
                
                if result:
                    row = result[0]
                    state = row['STATE']
                    
                    if state == 'SUCCEEDED':
                        log_detail(f"  {name}: completed successfully")
                        completed.add(name)
                        suspend_task_graph(session, root_task_fqn)
                    elif state == 'FAILED':
                        error_task = row['FIRST_ERROR_TASK_NAME'] or 'Unknown'
                        error_msg = row['FIRST_ERROR_MESSAGE'] or 'No message'
                        log_warning(f"  {name}: FAILED")
                        log_warning(f"    {error_task}: {error_msg}")
                        all_success = False
                        completed.add(name)
                        suspend_task_graph(session, root_task_fqn)
                    elif state == 'CANCELLED':
                        log_warning(f"  {name}: CANCELLED")
                        completed.add(name)
                        suspend_task_graph(session, root_task_fqn)
                    # If state is something else (EXECUTING, SCHEDULED), keep waiting
                else:
                    # No record in CURRENT or COMPLETE yet
                    if elapsed > 300:
                        log_warning(f"  {name}: No execution record found after {int(elapsed)}s")
                    
            except Exception as e:
                log_warning(f"  Error checking {name}: {e}")
        
        # Log progress periodically
        if int(elapsed) - last_progress_log >= 30:
            pending = len(started_pipelines) - len(completed)
            if pending > 0:
                log_detail(f"  Progress: {len(completed)}/{len(started_pipelines)} pipelines complete ({int(elapsed)}s elapsed)")
            last_progress_log = int(elapsed)
        
        if len(completed) < len(started_pipelines):
            time.sleep(10)
    
    # Ensure all pipelines are suspended
    for name, root_task_fqn in started_pipelines:
        try:
            suspend_task_graph(session, root_task_fqn)
        except:
            pass
    
    if all_success:
        log_info(f"All {len(started_pipelines)} pipelines completed successfully")
    else:
        log_warning(f"Pipeline execution completed with errors")
    
    return all_success
