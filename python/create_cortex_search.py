"""
Cortex Search Builder for SAM Demo

This module creates all Cortex Search services for document search across
broker research, earnings transcripts, press releases, NGO reports, engagement notes,
policy documents, sales templates, philosophy docs, macro events, and report templates.
"""

from snowflake.snowpark import Session
from typing import List
import config

def create_search_services(session: Session, scenarios: List[str]):
    """Create Cortex Search services for required document types."""
    
    # Determine required document types from scenarios
    required_doc_types = set()
    for scenario in scenarios:
        if scenario in config.SCENARIO_DATA_REQUIREMENTS:
            required_doc_types.update(config.SCENARIO_DATA_REQUIREMENTS[scenario])
    
    # print(f"   📑 Document types: {', '.join(required_doc_types)}")
    
    # Group document types by search service (some services combine multiple corpus tables)
    service_to_corpus_tables = {}
    for doc_type in required_doc_types:
        if doc_type in config.DOCUMENT_TYPES:
            service_name = config.DOCUMENT_TYPES[doc_type]['search_service']
            corpus_table = f"{config.DATABASE['name']}.CURATED.{config.DOCUMENT_TYPES[doc_type]['corpus_name']}"
            
            if service_name not in service_to_corpus_tables:
                service_to_corpus_tables[service_name] = []
            service_to_corpus_tables[service_name].append(corpus_table)
    
    # Create search service for each unique service (combining multiple corpus tables if needed)
    for service_name, corpus_tables in service_to_corpus_tables.items():
        try:
            # Use dedicated Cortex Search warehouse from structured config
            search_warehouse = config.WAREHOUSES['cortex_search']['name']
            target_lag = config.WAREHOUSES['cortex_search']['target_lag']
            
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
            # Using configurable TARGET_LAG for demo environments to see changes quickly
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
            
            # print(f"   ✅ Created search service: {service_name} from {len(corpus_tables)} corpus table(s)")
            
        except Exception as e:
            print(f"ERROR: CRITICAL FAILURE: Failed to create search service {service_name}: {e}")
            # print(f"   This search service is required for document types using {service_name}")
            raise Exception(f"Failed to create required search service {service_name}: {e}")

# =============================================================================
# CUSTOM TOOLS (PDF Generation)
# =============================================================================

