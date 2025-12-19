"""
Cortex Search Builder for SAM Demo

This module creates all Cortex Search services for document search across
broker research, earnings transcripts, press releases, NGO reports, engagement notes,
policy documents, sales templates, philosophy docs, macro events, and report templates.
"""

from snowflake.snowpark import Session
from typing import List
import config

def create_search_services(session: Session, scenarios: List[str], force_rebuild: bool = False):
    """
    Create Cortex Search services for required document types.
    
    Args:
        session: Snowpark session
        scenarios: List of scenario names or ['all']
        force_rebuild: If True, recreate all services. If False, skip existing services.
    """
    
    # Expand 'all' to all scenario names
    if 'all' in scenarios:
        scenarios = list(config.SCENARIO_DATA_REQUIREMENTS.keys())
        config.log_detail(f"  Expanding 'all' to {len(scenarios)} scenarios")
    
    # Get existing search services to skip if not force_rebuild
    existing_services = set()
    if not force_rebuild:
        try:
            result = session.sql(f"""
                SELECT SERVICE_NAME 
                FROM {config.DATABASE['name']}.INFORMATION_SCHEMA.CORTEX_SEARCH_SERVICES
            """).collect()
            existing_services = {row['SERVICE_NAME'] for row in result}
            if existing_services:
                config.log_detail(f"  Found {len(existing_services)} existing search services (will skip)")
        except Exception:
            pass  # Table might not exist yet
    
    # Determine required document types from scenarios
    required_doc_types = set()
    for scenario in scenarios:
        if scenario in config.SCENARIO_DATA_REQUIREMENTS:
            required_doc_types.update(config.SCENARIO_DATA_REQUIREMENTS[scenario])
    
    
    # Group document types by search service (using CORPUS tables - full documents)
    service_to_corpus_tables = {}
    for doc_type in required_doc_types:
        if doc_type in config.DOCUMENT_TYPES:
            service_name = config.DOCUMENT_TYPES[doc_type]['search_service']
            corpus_table = f"{config.DATABASE['name']}.CURATED.{config.DOCUMENT_TYPES[doc_type]['corpus_name']}"
            
            if service_name not in service_to_corpus_tables:
                service_to_corpus_tables[service_name] = []
            service_to_corpus_tables[service_name].append(corpus_table)
    
    # Create search service for each unique service (combining multiple corpus tables if needed)
    services_created = 0
    services_skipped = 0
    services_failed = 0
    
    for service_name, corpus_tables in service_to_corpus_tables.items():
        # Skip existing services unless force_rebuild
        if service_name in existing_services and not force_rebuild:
            services_skipped += 1
            continue
        
        # Verify corpus table exists before attempting to create search service
        corpus_exists = False
        try:
            session.sql(f"SELECT 1 FROM {corpus_tables[0]} LIMIT 1").collect()
            corpus_exists = True
        except Exception:
            # For SAM_COMPANY_EVENTS, try fallback to synthetic EARNINGS_TRANSCRIPTS_CORPUS
            if service_name == 'SAM_COMPANY_EVENTS':
                fallback_corpus = f"{config.DATABASE['name']}.CURATED.EARNINGS_TRANSCRIPTS_CORPUS"
                try:
                    session.sql(f"SELECT 1 FROM {fallback_corpus} LIMIT 1").collect()
                    config.log_warning(f"  {service_name}: Using fallback corpus EARNINGS_TRANSCRIPTS_CORPUS")
                    corpus_tables = [fallback_corpus]
                    corpus_exists = True
                except Exception:
                    pass
        
        if not corpus_exists:
            config.log_warning(f"  Skipping {service_name}: corpus table not found")
            services_failed += 1
            continue
            
        try:
            # Use dedicated Cortex Search warehouse from structured config
            search_warehouse = config.WAREHOUSES['cortex_search']['name']
            target_lag = config.WAREHOUSES['cortex_search']['target_lag']
            
            # Special handling for SAM_COMPANY_EVENTS which has EVENT_TYPE attribute
            if service_name == 'SAM_COMPANY_EVENTS':
                # Check if EVENT_TYPE column exists
                try:
                    session.sql(f"SELECT EVENT_TYPE FROM {corpus_tables[0]} LIMIT 1").collect()
                    has_event_type = True
                except Exception:
                    has_event_type = False
                    config.log_warning(f"  {service_name}: EVENT_TYPE column not found, using standard schema")
                
                if has_event_type:
                    # Company event transcripts have additional EVENT_TYPE column for filtering
                    session.sql(f"""
                        CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.{service_name}
                            ON DOCUMENT_TEXT
                            ATTRIBUTES DOCUMENT_TITLE, SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, EVENT_TYPE
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
                                EVENT_TYPE
                            FROM {corpus_tables[0]}
                    """).collect()
                else:
                    # Fallback to standard schema without EVENT_TYPE
                    session.sql(f"""
                        CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.{service_name}
                            ON DOCUMENT_TEXT
                            ATTRIBUTES DOCUMENT_TITLE, SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE
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
                                LANGUAGE
                            FROM {corpus_tables[0]}
                    """).collect()
                services_created += 1
                continue
            
            # Build UNION ALL query if multiple corpus tables
            if len(corpus_tables) == 1:
                from_clause = f"FROM {corpus_tables[0]}"
            else:
                union_parts = [f"""
                    SELECT 
                        DOCUMENT_ID,
                        DOCUMENT_TITLE,
                        DOCUMENT_TEXT,
                        SecurityID,
                        IssuerID,
                        DOCUMENT_TYPE,
                        PUBLISH_DATE,
                        LANGUAGE
                    FROM {table}""" for table in corpus_tables]
                from_clause = " UNION ALL ".join(union_parts)
                from_clause = f"FROM ({from_clause})"
            
            # Create enhanced Cortex Search service with SecurityID and IssuerID attributes
            # Using full DOCUMENT_TEXT from CORPUS tables
            session.sql(f"""
                CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.{service_name}
                    ON DOCUMENT_TEXT
                    ATTRIBUTES DOCUMENT_TITLE, SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE
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
                        LANGUAGE
                    {from_clause}
            """).collect()
            
            services_created += 1
            
        except Exception as e:
            # For optional document types (like company_event_transcripts), warn but continue
            if service_name == 'SAM_COMPANY_EVENTS':
                config.log_warning(f"  Could not create {service_name}: {e}")
                services_failed += 1
                continue
            config.log_error(f"CRITICAL: Failed to create search service {service_name}: {e}")
            raise Exception(f"Failed to create required search service {service_name}: {e}")
    
    # Log summary
    summary = f"  Search services: {services_created} created"
    if services_skipped > 0:
        summary += f", {services_skipped} skipped (already exist)"
    if services_failed > 0:
        summary += f", {services_failed} skipped (missing data)"
    config.log_detail(summary)
    
    # Create real SEC filing search service if real data is enabled and available
    if config.REAL_DATA_SOURCES.get('enabled', False):
        try:
            create_real_sec_search_service(session)
        except Exception as e:
            config.log_warning(f" Could not create real SEC filing search service: {e}")


def create_real_sec_search_service(session: Session):
    """
    Create Cortex Search service for real SEC filing text from SNOWFLAKE_PUBLIC_DATA_FREE.
    
    This provides search over authentic 10-K, 10-Q, and 8-K filing content including
    MD&A sections, risk factors, and other key disclosures.
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    search_warehouse = config.WAREHOUSES['cortex_search']['name']
    target_lag = config.WAREHOUSES['cortex_search']['target_lag']
    
    # Check if real data table exists
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_SEC_FILING_TEXT LIMIT 1").collect()
    except Exception:
        config.log_warning("  FACT_SEC_FILING_TEXT not found - skipping SAM_REAL_SEC_FILINGS search service")
        return
    
    config.log_detail("Creating SAM_REAL_SEC_FILINGS search service for real SEC filing text...")
    
    session.sql(f"""
        CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_REAL_SEC_FILINGS
            ON FILING_TEXT
            ATTRIBUTES VARIABLE_NAME, CIK, ADSH, PERIOD_END_DATE
            WAREHOUSE = {search_warehouse}
            TARGET_LAG = '{target_lag}'
            AS 
            SELECT 
                FILING_TEXT_ID as DOCUMENT_ID,
                SEC_DOCUMENT_ID as DOCUMENT_TITLE,
                FILING_TEXT,
                VARIABLE_NAME,
                CIK,
                ADSH,
                PERIOD_END_DATE,
                COMPANY_ID,
                ISSUERID
            FROM {database_name}.{market_data_schema}.FACT_SEC_FILING_TEXT
            WHERE FILING_TEXT IS NOT NULL 
              AND TEXT_LENGTH > 500
    """).collect()
    
    config.log_detail(" Created search service: SAM_REAL_SEC_FILINGS (REAL SEC filing text)")


# =============================================================================
# CUSTOM TOOLS (PDF Generation)
# =============================================================================
