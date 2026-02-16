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
from logging_utils import log_detail, log_warning, log_error
from scenario_utils import get_required_document_types

def create_search_services(session: Session, scenarios: List[str]):
    """
    Create Cortex Search services for required document types.
    
    Enhanced with document-type-specific searchable attributes:
    - Security-level docs: TICKER, COMPANY_NAME, SIC_DESCRIPTION
    - Broker research: BROKER_NAME, RATING
    - NGO reports: NGO_NAME, SEVERITY_LEVEL
    - Portfolio docs: PORTFOLIO_NAME
    """
    # Determine required document types from scenarios
    required_doc_types = set(get_required_document_types(scenarios))
    
    
    # Group document types by search service (some services combine multiple corpus tables)
    # Also track the document types for each service to determine attributes
    service_to_corpus_tables = {}
    service_to_doc_types = {}
    for doc_type in required_doc_types:
        if doc_type in config.DOCUMENT_TYPES:
            service_name = config.DOCUMENT_TYPES[doc_type]['search_service']
            corpus_table = f"{config.DATABASE['name']}.CURATED.{config.DOCUMENT_TYPES[doc_type]['corpus_name']}"
            
            if service_name not in service_to_corpus_tables:
                service_to_corpus_tables[service_name] = []
                service_to_doc_types[service_name] = []
            service_to_corpus_tables[service_name].append(corpus_table)
            service_to_doc_types[service_name].append(doc_type)
    
    # Create search service for each unique service (combining multiple corpus tables if needed)
    for service_name, corpus_tables in service_to_corpus_tables.items():
        try:
            # Use dedicated Cortex Search warehouse from structured config
            search_warehouse = config.WAREHOUSES['cortex_search']['name']
            target_lag = config.WAREHOUSES['cortex_search']['target_lag']
            doc_types = service_to_doc_types[service_name]
            
            # Special handling for SAM_COMPANY_EVENTS which has EVENT_TYPE attribute
            if service_name == 'SAM_COMPANY_EVENTS':
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
                log_detail(f"  Created search service: {service_name}")
                continue
            
            # Determine linkage level and extra columns based on document types
            primary_doc_type = doc_types[0] if doc_types else None
            doc_config = config.DOCUMENT_TYPES.get(primary_doc_type, {})
            linkage_level = doc_config.get('linkage_level', 'global')
            
            # Build attributes and columns based on document type
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
            
            # Add linkage-level specific attributes
            if linkage_level == 'security':
                extra_attributes = ", TICKER, COMPANY_NAME"
                extra_columns = """,
                            TICKER,
                            COMPANY_NAME"""
            elif linkage_level == 'portfolio':
                extra_attributes = ", PORTFOLIO_NAME"
                extra_columns = """,
                            PORTFOLIO_NAME"""
            
            # Add document-type specific attributes
            if primary_doc_type in ['broker_research', 'internal_research']:
                extra_attributes += ", BROKER_NAME, RATING"
                extra_columns += """,
                            BROKER_NAME,
                            RATING"""
            elif primary_doc_type == 'ngo_reports':
                extra_attributes += ", NGO_NAME, SEVERITY_LEVEL"
                extra_columns += """,
                            NGO_NAME,
                            SEVERITY_LEVEL"""
            elif primary_doc_type == 'engagement_notes':
                extra_attributes += ", MEETING_TYPE"
                extra_columns += """,
                            MEETING_TYPE"""
            
            # Build UNION ALL query if multiple corpus tables (use base columns only for UNION)
            if len(corpus_tables) == 1:
                from_clause = f"FROM {corpus_tables[0]}"
                select_columns = base_columns + extra_columns
            else:
                # For UNION, we need common columns only
                union_parts = [f"""
                    SELECT 
                        {base_columns}
                    FROM {table}""" for table in corpus_tables]
                from_clause = " UNION ALL ".join(union_parts)
                from_clause = f"FROM ({from_clause})"
                select_columns = base_columns
                extra_attributes = ""  # No extra attributes for UNION queries
            
            # Create enhanced Cortex Search service
            session.sql(f"""
                CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.{service_name}
                    ON DOCUMENT_TEXT
                    ATTRIBUTES {base_attributes}{extra_attributes}
                    WAREHOUSE = {search_warehouse}
                    TARGET_LAG = '{target_lag}'
                    AS 
                    SELECT 
                        {select_columns}
                    {from_clause}
            """).collect()
            
            log_detail(f"  Created search service: {service_name}")
            
        except Exception as e:
            log_error(f"CRITICAL: Failed to create search service {service_name}: {e}")
            raise Exception(f"Failed to create required search service {service_name}: {e}")
    
    # Create real SEC filing search service (required)
    try:
        create_real_sec_search_service(session)
    except Exception as e:
        log_warning(f" Could not create real SEC filing search service: {e}")


def create_real_sec_search_service(session: Session):
    """
    Create Cortex Search service for real SEC filing text from SNOWFLAKE_PUBLIC_DATA_FREE.
    
    This provides search over authentic 10-K, 10-Q, and 8-K filing content including
    MD&A sections, risk factors, and other key disclosures.
    
    Enhanced searchable attributes:
    - COMPANY_NAME, TICKER: Filter by company (e.g., "Microsoft risk factors")
    - FILING_TYPE: Filter by filing type (10-K, 10-Q, 8-K)
    - FISCAL_YEAR, FISCAL_QUARTER: Filter by time period
    - VARIABLE_NAME: Filter by section type (Risk Factors, MD&A, etc.)
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    search_warehouse = config.WAREHOUSES['cortex_search']['name']
    target_lag = config.WAREHOUSES['cortex_search']['target_lag']
    
    # Check if real data table exists
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_SEC_FILING_TEXT LIMIT 1").collect()
    except Exception:
        log_warning("  FACT_SEC_FILING_TEXT not found - skipping SAM_REAL_SEC_FILINGS search service")
        return
    
    log_detail("Creating SAM_REAL_SEC_FILINGS search service for real SEC filing text...")
    
    curated_schema = config.DATABASE['schemas']['curated']
    
    # JOIN to DIM_ISSUER to get COMPANY_NAME and TICKER (not stored in fact table)
    session.sql(f"""
        CREATE OR REPLACE CORTEX SEARCH SERVICE {database_name}.AI.SAM_REAL_SEC_FILINGS
            ON FILING_TEXT
            ATTRIBUTES DOCUMENT_TITLE, COMPANY_NAME, TICKER, FILING_TYPE, FISCAL_YEAR, FISCAL_QUARTER, VARIABLE_NAME, CIK
            WAREHOUSE = {search_warehouse}
            TARGET_LAG = '{target_lag}'
            AS 
            SELECT 
                f.FILING_TEXT_ID as DOCUMENT_ID,
                f.DOCUMENT_TITLE,
                f.FILING_TEXT,
                i.LegalName as COMPANY_NAME,
                i.PrimaryTicker as TICKER,
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
    """).collect()
    
    log_detail(" Created search service: SAM_REAL_SEC_FILINGS (REAL SEC filing text with enhanced metadata)")


# =============================================================================
# CUSTOM TOOLS (PDF Generation)
# =============================================================================

