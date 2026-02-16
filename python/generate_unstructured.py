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
Unstructured Data Generation for SAM Demo

This module generates realistic unstructured documents using pre-generated templates
with the hydration engine for deterministic, high-quality content.

Document types include:
- Broker research reports
- Earnings transcripts and summaries  
- Press releases
- NGO reports and ESG controversies
- Internal engagement notes
- Policy documents and sales templates
"""

from snowflake.snowpark import Session
from typing import List
import config
import hydration_engine
from logging_utils import log_warning, log_error, log_success

def build_all(session: Session, document_types: List[str], test_mode: bool = False):
    """
    Build all unstructured data for the specified document types using template hydration.
    
    Args:
        session: Active Snowpark session
        document_types: List of document types to generate (use ['all'] for all types)
        test_mode: If True, use reduced document counts for faster development
    """
    
    # Expand 'all' to actual document types from config
    if document_types == ['all'] or 'all' in document_types:
        document_types = list(config.DOCUMENT_TYPES.keys())
    
    # Ensure database context is set
    try:
        session.sql(f"USE DATABASE {config.DATABASE['name']}").collect()
        session.sql(f"USE SCHEMA {config.DATABASE['schemas']['raw']}").collect()
    except Exception as e:
        log_warning(f" Could not set database context: {e}")
    
    # Generate documents using template hydration
    for doc_type in document_types:
        # Skip real data sources - handled by separate modules (e.g., generate_real_transcripts.py)
        doc_config = config.DOCUMENT_TYPES.get(doc_type, {})
        if doc_config.get('source') == 'real':
            log_success(f" Skipping {doc_type} (real data source - handled separately)")
            continue
        
        try:
            count = hydration_engine.hydrate_documents(session, doc_type, test_mode=test_mode)
        except Exception as e:
            log_error(f" Failed to hydrate {doc_type}: {e}")
            # Continue with other document types
            continue
    
    # Create corpus tables for Cortex Search
    create_corpus_tables(session, document_types)
    

def create_corpus_tables(session: Session, document_types: List[str]):
    """
    Create normalized corpus tables for Cortex Search indexing.
    
    Includes enhanced metadata for better searchability:
    - Security-level docs: TICKER, COMPANY_NAME, SIC_DESCRIPTION
    - Broker research: BROKER_NAME, RATING
    - NGO reports: NGO_NAME, SEVERITY_LEVEL
    - Portfolio docs: PORTFOLIO_NAME
    """
    
    for doc_type in document_types:
        # Skip real data sources - corpus created by separate modules
        doc_config = config.DOCUMENT_TYPES.get(doc_type, {})
        if doc_config.get('source') == 'real':
            continue
        
        raw_table = f"{config.DATABASE['name']}.RAW.{config.DOCUMENT_TYPES[doc_type]['table_name']}"
        corpus_table = f"{config.DATABASE['name']}.CURATED.{config.DOCUMENT_TYPES[doc_type]['corpus_name']}"
        linkage_level = doc_config.get('linkage_level', 'global')
        
        # Build column list based on document type and linkage level
        base_columns = """
                DOCUMENT_ID,
                DOCUMENT_TITLE,
                DOCUMENT_TYPE,
                SecurityID,
                IssuerID,
                PUBLISH_DATE,
                'en' as LANGUAGE,
                RAW_MARKDOWN as DOCUMENT_TEXT"""
        
        # Add linkage-level specific columns
        if linkage_level == 'security':
            # Security-level docs have TICKER, COMPANY_NAME, SIC_DESCRIPTION
            extra_columns = """,
                TICKER,
                COMPANY_NAME,
                SIC_DESCRIPTION"""
        elif linkage_level == 'issuer':
            # Issuer-level docs have TICKER
            extra_columns = """,
                TICKER"""
        elif linkage_level == 'portfolio':
            # Portfolio-level docs have PORTFOLIO_NAME
            extra_columns = """,
                PORTFOLIO_NAME"""
        else:
            extra_columns = ""
        
        # Add document-type specific columns
        if doc_type in ['broker_research', 'internal_research']:
            extra_columns += """,
                BROKER_NAME,
                RATING"""
        elif doc_type == 'ngo_reports':
            extra_columns += """,
                NGO_NAME,
                SEVERITY_LEVEL"""
        elif doc_type == 'engagement_notes':
            extra_columns += """,
                MEETING_TYPE"""
        
        # Create corpus table with enhanced metadata
        session.sql(f"""
            CREATE OR REPLACE TABLE {corpus_table} AS
            SELECT {base_columns}{extra_columns}
            FROM {raw_table}
        """).collect()
