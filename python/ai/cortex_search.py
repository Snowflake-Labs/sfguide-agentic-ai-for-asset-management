"""
Cortex Search Builder for SAM Demo

This module creates all Cortex Search services for document search across
broker research, company event transcripts, press releases, NGO reports, engagement notes,
policy documents, sales templates, philosophy docs, macro events, and report templates.

Note: company_event_transcripts replaces earnings_transcripts and uses real data from
SNOWFLAKE_PUBLIC_DATA_FREE.
"""

from snowflake.snowpark import Session
from typing import List
import config
from utils.logging import log_detail, log_warning, log_error
from utils.config_helpers import get_required_document_types


def _await_search_services(async_jobs, fatal=True):
    """Wait for all async search service creation jobs to complete.
    
    Args:
        async_jobs: List of (service_name, AsyncJob) tuples
        fatal: If True, raise on first failure. If False, log warning and continue.
    
    Returns:
        List of service names that failed (empty if all succeeded or fatal=True)
    """
    failed = []
    for service_name, job in async_jobs:
        try:
            job.result()
            log_detail(f"  Created search service: {service_name}")
        except Exception as e:
            if fatal:
                log_error(f"CRITICAL: Failed to create search service {service_name}: {e}")
                raise Exception(f"Failed to create required search service {service_name}: {e}")
            else:
                log_warning(f"  Could not create {service_name}: {e}")
                failed.append(service_name)
    return failed


def get_corpus_source_for_doc_type(doc_type: str) -> tuple:
    """
    Determine the corpus table and filter for a document type.
    
    PDF document types use shared PDF_INTERNAL_CORPUS or PDF_EXTERNAL_CORPUS
    with a DOC_TYPE filter. Non-PDF types use their own dedicated corpus table.
    
    Returns:
        tuple: (corpus_table_name, doc_type_filter or None)
    """
    pdf_audience = config.PDF_DOC_AUDIENCE.get(doc_type, 'skip')
    database_name = config.DATABASE['name']
    
    if pdf_audience == 'internal':
        return (f"{database_name}.CURATED.PDF_INTERNAL_CORPUS", doc_type)
    elif pdf_audience == 'external':
        return (f"{database_name}.CURATED.PDF_EXTERNAL_CORPUS", doc_type)
    else:
        corpus_name = config.DOCUMENT_TYPES[doc_type]['corpus_name']
        return (f"{database_name}.CURATED.{corpus_name}", None)


def create_search_services(session: Session, scenarios: List[str]):
    """
    Create Cortex Search services for required document types.
    
    PDF document types use the shared PDF_INTERNAL_CORPUS or PDF_EXTERNAL_CORPUS
    tables with DOC_TYPE filters. Non-PDF types use their dedicated corpus tables.
    
    Enhanced with document-type-specific searchable attributes:
    - Security-level docs: TICKER, COMPANY_NAME, SIC_DESCRIPTION
    - Broker research: BROKER_NAME, RATING
    - NGO reports: NGO_NAME, SEVERITY_LEVEL
    - Portfolio docs: PORTFOLIO_NAME
    """
    
    # Determine required document types from scenarios
    required_doc_types = set(get_required_document_types(scenarios))
    
    
    # Group document types by search service
    # Track corpus source (table + optional filter) for each service
    service_to_corpus_info = {}  # {service_name: [(corpus_table, doc_type_filter), ...]}
    service_to_doc_types = {}
    for doc_type in required_doc_types:
        if doc_type in config.DOCUMENT_TYPES:
            service_name = config.DOCUMENT_TYPES[doc_type]['search_service']
            corpus_table, doc_type_filter = get_corpus_source_for_doc_type(doc_type)
            
            if service_name not in service_to_corpus_info:
                service_to_corpus_info[service_name] = []
                service_to_doc_types[service_name] = []
            service_to_corpus_info[service_name].append((corpus_table, doc_type_filter))
            service_to_doc_types[service_name].append(doc_type)
    
    # Phase 1: Submit all search service creation DDLs asynchronously
    # Required services (fatal on failure)
    async_jobs = []
    # Optional services (log warning on failure)
    optional_jobs = []

    for service_name, corpus_info_list in service_to_corpus_info.items():
        try:
            search_warehouse = config.WAREHOUSES['cortex_search']['name']
            target_lag = config.WAREHOUSES['cortex_search']['target_lag']
            doc_types = service_to_doc_types[service_name]
            primary_doc_type = doc_types[0] if doc_types else None
            
            pdf_audience = config.PDF_DOC_AUDIENCE.get(primary_doc_type, 'skip')
            is_pdf_service = pdf_audience in ('internal', 'external')
            
            if service_name == 'SAM_COMPANY_EVENTS':
                corpus_table = corpus_info_list[0][0]
                job = session.sql(f"""
                    CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.{service_name}
                        TEXT INDEXES DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR, EVENT_TYPE, SPEAKER_NAME
                        VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                        ATTRIBUTES DOCUMENT_TITLE, SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, EVENT_TYPE, TICKER, COMPANY_NAME, GICS_SECTOR, SPEAKER_NAME, SPEAKER_ROLE, FISCAL_YEAR, FISCAL_PERIOD
                        WAREHOUSE = {search_warehouse}
                        TARGET_LAG = '{target_lag}'
                        AS 
                        SELECT 
                            DOCUMENT_ID,
                            DOCUMENT_TITLE,
                            DOCUMENT_TEXT,
                            SecurityID,
                            IssuerID,
                            DOCUMENT_TYPE,
                            PUBLISH_DATE,
                            LANGUAGE,
                            EVENT_TYPE,
                            TICKER,
                            COMPANY_NAME,
                            GICS_SECTOR,
                            SPEAKER_NAME,
                            SPEAKER_ROLE,
                            FISCAL_YEAR,
                            FISCAL_PERIOD
                        FROM {corpus_table}
                """).collect_nowait()
                async_jobs.append((service_name, job))
                continue
            
            if service_name == 'SAM_REGULATORY_DOCS':
                corpus_table = corpus_info_list[0][0]
                job = session.sql(f"""
                    CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.{service_name}
                        TEXT INDEXES DOCUMENT_TITLE, REGULATORY_BODY, JURISDICTION, REFERENCE
                        VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                        ATTRIBUTES DOCUMENT_TITLE, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, REGULATION_ID, REGULATORY_BODY, JURISDICTION, REFERENCE, SOURCE_URL
                        WAREHOUSE = {search_warehouse}
                        TARGET_LAG = '{target_lag}'
                        AS 
                        SELECT 
                            DOCUMENT_ID,
                            DOCUMENT_TITLE,
                            DOCUMENT_TEXT,
                            DOCUMENT_TYPE,
                            PUBLISH_DATE,
                            LANGUAGE,
                            REGULATION_ID,
                            REGULATORY_BODY,
                            JURISDICTION,
                            REFERENCE,
                            SOURCE_URL
                        FROM {corpus_table}
                """).collect_nowait()
                async_jobs.append((service_name, job))
                continue
            
            if is_pdf_service:
                corpus_table = corpus_info_list[0][0]
                
                job = session.sql(f"""
                    CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.{service_name}
                        TEXT INDEXES DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR
                        VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                        ATTRIBUTES DOCUMENT_TITLE, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, TICKER, COMPANY_NAME, GICS_SECTOR
                        WAREHOUSE = {search_warehouse}
                        TARGET_LAG = '{target_lag}'
                        AS 
                        SELECT 
                            DOCUMENT_ID,
                            DOCUMENT_TITLE,
                            DOCUMENT_TEXT,
                            DOCUMENT_TYPE,
                            PUBLISH_DATE,
                            LANGUAGE,
                            TICKER,
                            COMPANY_NAME,
                            GICS_SECTOR
                        FROM {corpus_table}
                """).collect_nowait()
                async_jobs.append((service_name, job))
                continue
            
            doc_config = config.DOCUMENT_TYPES.get(primary_doc_type, {})
            linkage_level = doc_config.get('linkage_level', 'global')
            
            base_attributes = "DOCUMENT_TITLE, SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE"
            base_columns = """DOCUMENT_ID,
                            DOCUMENT_TITLE,
                            DOCUMENT_TEXT,
                            SecurityID,
                            IssuerID,
                            DOCUMENT_TYPE,
                            PUBLISH_DATE,
                            LANGUAGE"""
            
            extra_attributes = ""
            extra_columns = ""
            extra_text_indexes = ""
            
            if linkage_level == 'security':
                extra_attributes = ", TICKER, COMPANY_NAME"
                extra_columns = """,
                            TICKER,
                            COMPANY_NAME"""
                extra_text_indexes = ", TICKER, COMPANY_NAME"
            elif linkage_level == 'portfolio':
                extra_attributes = ", PORTFOLIO_NAME"
                extra_columns = """,
                            PORTFOLIO_NAME"""
                extra_text_indexes = ", PORTFOLIO_NAME"
            
            if primary_doc_type in ['broker_research', 'internal_research']:
                extra_attributes += ", BROKER_NAME, RATING"
                extra_columns += """,
                            BROKER_NAME,
                            RATING"""
                extra_text_indexes += ", BROKER_NAME"
            elif primary_doc_type == 'ngo_reports':
                extra_attributes += ", NGO_NAME, SEVERITY_LEVEL"
                extra_columns += """,
                            NGO_NAME,
                            SEVERITY_LEVEL"""
                extra_text_indexes += ", NGO_NAME, SEVERITY_LEVEL"
            elif primary_doc_type == 'engagement_notes':
                extra_attributes += ", MEETING_TYPE"
                extra_columns += """,
                            MEETING_TYPE"""
                extra_text_indexes += ", MEETING_TYPE"
            elif primary_doc_type == 'ips':
                extra_attributes += ", RISK_PROFILE"
                extra_columns += """,
                            RISK_PROFILE"""
                extra_text_indexes += ", RISK_PROFILE"
            
            corpus_tables = [info[0] for info in corpus_info_list]
            if len(corpus_tables) == 1:
                from_clause = f"FROM {corpus_tables[0]}"
                select_columns = base_columns + extra_columns
            else:
                union_parts = [f"""
                    SELECT 
                        {base_columns}
                    FROM {table}""" for table in corpus_tables]
                from_clause = " UNION ALL ".join(union_parts)
                from_clause = f"FROM ({from_clause})"
                select_columns = base_columns
                extra_attributes = ""
                extra_text_indexes = ""
            
            job = session.sql(f"""
                CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.{service_name}
                    TEXT INDEXES DOCUMENT_TITLE{extra_text_indexes}
                    VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                    ATTRIBUTES {base_attributes}{extra_attributes}
                    WAREHOUSE = {search_warehouse}
                    TARGET_LAG = '{target_lag}'
                    AS 
                    SELECT 
                        {select_columns}
                    {from_clause}
            """).collect_nowait()
            async_jobs.append((service_name, job))
            
        except Exception as e:
            log_error(f"CRITICAL: Failed to build SQL for search service {service_name}: {e}")
            raise Exception(f"Failed to create required search service {service_name}: {e}")
    
    # Submit scenario-specific search services based on config
    required_services = config.get_required_services(scenarios)

    if 'sec_filings' in required_services:
        try:
            sec_job = _submit_sec_search_service(session)
            if sec_job:
                optional_jobs.append(sec_job)
        except Exception as e:
            log_warning(f" Could not prepare SEC filing search service: {e}")
    
    if 'pe_search' in required_services:
        try:
            pe_jobs = _submit_pe_search_services(session)
            optional_jobs.extend(pe_jobs)
        except Exception as e:
            log_warning(f" Could not prepare PE search services: {e}")

    if 'credit_search' in required_services:
        try:
            credit_jobs = _submit_credit_search_services(session)
            optional_jobs.extend(credit_jobs)
        except Exception as e:
            log_warning(f" Could not prepare credit search services: {e}")

    # Phase 2: Await all services
    _await_search_services(async_jobs, fatal=True)
    _await_search_services(optional_jobs, fatal=False)


def _submit_sec_search_service(session: Session):
    """
    Submit async creation of Cortex Search service for real SEC filing text.
    
    Returns:
        Tuple of (service_name, AsyncJob) or None if source table doesn't exist.
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    search_warehouse = config.WAREHOUSES['cortex_search']['name']
    target_lag = config.WAREHOUSES['cortex_search']['target_lag']
    
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_SEC_FILING_TEXT LIMIT 1").collect()
    except Exception:
        log_warning("  FACT_SEC_FILING_TEXT not found - skipping SAM_REAL_SEC_FILINGS search service")
        return None
    
    curated_schema = config.DATABASE['schemas']['curated']
    
    job = session.sql(f"""
        CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_REAL_SEC_FILINGS
            TEXT INDEXES DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR, FILING_TYPE
            VECTOR INDEXES FILING_TEXT (model='{config.AI_EMBEDDING_MODEL}')
            ATTRIBUTES DOCUMENT_TITLE, COMPANY_NAME, TICKER, GICS_SECTOR, FILING_TYPE, FISCAL_YEAR, FISCAL_QUARTER, VARIABLE_NAME, CIK
            WAREHOUSE = {search_warehouse}
            TARGET_LAG = '{target_lag}'
            AS 
            SELECT 
                f.FILING_TEXT_ID as DOCUMENT_ID,
                f.DOCUMENT_TITLE,
                f.FILING_TEXT,
                i.LegalName as COMPANY_NAME,
                i.PrimaryTicker as TICKER,
                i.GICS_SECTOR,
                f.FILING_TYPE,
                f.FISCAL_YEAR,
                f.FISCAL_QUARTER,
                f.VARIABLE_NAME,
                f.CIK,
                f.ISSUERID
            FROM {database_name}.{market_data_schema}.FACT_SEC_FILING_TEXT f
            JOIN {database_name}.{curated_schema}.DIM_ISSUER i ON f.IssuerID = i.IssuerID
            WHERE f.FILING_TEXT IS NOT NULL 
              AND f.TEXT_LENGTH > 50
    """).collect_nowait()
    
    return ('SAM_REAL_SEC_FILINGS', job)


def _submit_pe_search_services(session: Session) -> list:
    """
    Submit async creation of PE Cortex Search services.
    
    Table-existence checks are synchronous (fast). DDLs are submitted asynchronously.
    
    Returns:
        List of (service_name, AsyncJob) tuples for services that were submitted.
    """
    database_name = config.DATABASE['name']
    search_warehouse = config.WAREHOUSES['cortex_search']['name']
    target_lag = config.WAREHOUSES['cortex_search']['target_lag']
    curated_schema = config.DATABASE['schemas']['curated']
    
    async_jobs = []
    
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.PE_BOARD_PACKS_CORPUS LIMIT 1").collect()
        
        job = session.sql(f"""
            CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_PE_BOARD_PACKS
                TEXT INDEXES DOCUMENT_TITLE, CompanyName
                VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                ATTRIBUTES DOCUMENT_TITLE, CompanyName, PortfolioCompanyID, DOCUMENT_TYPE, ReportPeriod
                WAREHOUSE = {search_warehouse}
                TARGET_LAG = '{target_lag}'
                AS 
                SELECT 
                    DOCUMENT_ID,
                    DOCUMENT_TITLE,
                    DOCUMENT_TEXT,
                    CompanyName,
                    PortfolioCompanyID,
                    DOCUMENT_TYPE,
                    ReportPeriod
                FROM {database_name}.{curated_schema}.PE_BOARD_PACKS_CORPUS
        """).collect_nowait()
        async_jobs.append(('SAM_PE_BOARD_PACKS', job))
    except Exception as e:
        log_warning(f"  Could not prepare SAM_PE_BOARD_PACKS: {e}")
    
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.PE_DUE_DILIGENCE_CORPUS LIMIT 1").collect()
        
        job = session.sql(f"""
            CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_PE_DUE_DILIGENCE
                TEXT INDEXES DOCUMENT_TITLE, TargetCompanyName
                VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                ATTRIBUTES DOCUMENT_TITLE, TargetCompanyName, DealID, DOCUMENT_TYPE
                WAREHOUSE = {search_warehouse}
                TARGET_LAG = '{target_lag}'
                AS 
                SELECT 
                    DOCUMENT_ID,
                    DOCUMENT_TITLE,
                    DOCUMENT_TEXT,
                    TargetCompanyName,
                    DealID,
                    DOCUMENT_TYPE
                FROM {database_name}.{curated_schema}.PE_DUE_DILIGENCE_CORPUS
        """).collect_nowait()
        async_jobs.append(('SAM_PE_DUE_DILIGENCE', job))
    except Exception as e:
        log_warning(f"  Could not prepare SAM_PE_DUE_DILIGENCE: {e}")
    
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.PE_EXPERT_NETWORK_CORPUS LIMIT 1").collect()
        
        job = session.sql(f"""
            CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_PE_EXPERT_NETWORK
                TEXT INDEXES DOCUMENT_TITLE, TargetCompanyName, ExpertRole
                VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                ATTRIBUTES DOCUMENT_TITLE, TargetCompanyName, ExpertRole, DealID, PortfolioCompanyID, CallDate
                WAREHOUSE = {search_warehouse}
                TARGET_LAG = '{target_lag}'
                AS 
                SELECT 
                    DOCUMENT_ID,
                    DOCUMENT_TITLE,
                    DOCUMENT_TEXT,
                    TargetCompanyName,
                    ExpertRole,
                    DealID,
                    PortfolioCompanyID,
                    CallDate
                FROM {database_name}.{curated_schema}.PE_EXPERT_NETWORK_CORPUS
        """).collect_nowait()
        async_jobs.append(('SAM_PE_EXPERT_NETWORK', job))
    except Exception as e:
        log_warning(f"  Could not prepare SAM_PE_EXPERT_NETWORK: {e}")
    
    return async_jobs


def _submit_credit_search_services(session: Session) -> list:
    """
    Submit async creation of Private Credit Cortex Search services.
    
    Table-existence checks are synchronous (fast). DDLs are submitted asynchronously.
    
    Returns:
        List of (service_name, AsyncJob) tuples for services that were submitted.
    """
    database_name = config.DATABASE['name']
    search_warehouse = config.WAREHOUSES['cortex_search']['name']
    target_lag = config.WAREHOUSES['cortex_search']['target_lag']
    curated_schema = config.DATABASE['schemas']['curated']

    async_jobs = []

    try:
        session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.CREDIT_AGREEMENTS_CORPUS LIMIT 1").collect()

        job = session.sql(f"""
            CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_CREDIT_AGREEMENTS
                TEXT INDEXES DOCUMENT_TITLE, BORROWERNAME
                VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                ATTRIBUTES DOCUMENT_TITLE, BORROWERNAME, FACILITYID, DOCUMENT_TYPE
                WAREHOUSE = {search_warehouse}
                TARGET_LAG = '{target_lag}'
                AS
                SELECT
                    DOCUMENT_ID,
                    DOCUMENT_TITLE,
                    DOCUMENT_TEXT,
                    BORROWERNAME,
                    FACILITYID,
                    DOCUMENT_TYPE
                FROM {database_name}.{curated_schema}.CREDIT_AGREEMENTS_CORPUS
        """).collect_nowait()
        async_jobs.append(('SAM_CREDIT_AGREEMENTS', job))
    except Exception as e:
        log_warning(f"  Could not prepare SAM_CREDIT_AGREEMENTS: {e}")

    try:
        session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.COMPLIANCE_CERTS_CORPUS LIMIT 1").collect()

        job = session.sql(f"""
            CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_COMPLIANCE_CERTS
                TEXT INDEXES DOCUMENT_TITLE, BORROWERNAME
                VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                ATTRIBUTES DOCUMENT_TITLE, BORROWERNAME, BORROWERID, DOCUMENT_TYPE, REPORTPERIOD
                WAREHOUSE = {search_warehouse}
                TARGET_LAG = '{target_lag}'
                AS
                SELECT
                    DOCUMENT_ID,
                    DOCUMENT_TITLE,
                    DOCUMENT_TEXT,
                    BORROWERNAME,
                    BORROWERID,
                    DOCUMENT_TYPE,
                    REPORTPERIOD
                FROM {database_name}.{curated_schema}.COMPLIANCE_CERTS_CORPUS
        """).collect_nowait()
        async_jobs.append(('SAM_COMPLIANCE_CERTS', job))
    except Exception as e:
        log_warning(f"  Could not prepare SAM_COMPLIANCE_CERTS: {e}")

    try:
        session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.IC_MEMOS_CORPUS LIMIT 1").collect()

        job = session.sql(f"""
            CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_IC_MEMOS
                TEXT INDEXES DOCUMENT_TITLE, TARGETNAME
                VECTOR INDEXES DOCUMENT_TEXT (model='{config.AI_EMBEDDING_MODEL}')
                ATTRIBUTES DOCUMENT_TITLE, TARGETNAME, DEALID, DOCUMENT_TYPE
                WAREHOUSE = {search_warehouse}
                TARGET_LAG = '{target_lag}'
                AS
                SELECT
                    DOCUMENT_ID,
                    DOCUMENT_TITLE,
                    DOCUMENT_TEXT,
                    TARGETNAME,
                    DEALID,
                    DOCUMENT_TYPE
                FROM {database_name}.{curated_schema}.IC_MEMOS_CORPUS
        """).collect_nowait()
        async_jobs.append(('SAM_IC_MEMOS', job))
    except Exception as e:
        log_warning(f"  Could not prepare SAM_IC_MEMOS: {e}")

    return async_jobs


# =============================================================================
# CUSTOM TOOLS (PDF Generation)
# =============================================================================

