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

def build_all(session: Session, document_types: List[str], test_mode: bool = False):
    """
    Build all unstructured data for the specified document types using template hydration.
    
    Args:
        session: Active Snowpark session
        document_types: List of document types to generate (use ['all'] for all types)
        test_mode: If True, use reduced document counts for faster development
    """
    
    # Expand 'all' to all document types
    if 'all' in document_types:
        document_types = list(config.DOCUMENT_TYPES.keys())
        config.log_detail(f"  Expanding 'all' to {len(document_types)} document types")
    
    # Ensure database context is set
    try:
        session.sql(f"USE DATABASE {config.DATABASE['name']}").collect()
        session.sql(f"USE SCHEMA RAW").collect()
    except Exception as e:
        config.log_warning(f" Could not set database context: {e}")
    
    # Generate documents using template hydration
    for doc_type in document_types:
        # Skip real data sources - handled by separate modules (e.g., generate_real_transcripts.py)
        doc_config = config.DOCUMENT_TYPES.get(doc_type, {})
        if doc_config.get('source') == 'real':
            config.log_success(f" Skipping {doc_type} (real data source - handled separately)")
            continue
        
        try:
            count = hydration_engine.hydrate_documents(session, doc_type, test_mode=test_mode)
        except Exception as e:
            config.log_error(f" Failed to hydrate {doc_type}: {e}")
            # Continue with other document types
            continue
    
    # Create corpus tables for Cortex Search
    create_corpus_tables(session, document_types)
    

def create_corpus_tables(session: Session, document_types: List[str]):
    """Create normalized corpus tables for Cortex Search indexing."""
    
    for doc_type in document_types:
        # Skip real data sources - corpus created by separate modules
        doc_config = config.DOCUMENT_TYPES.get(doc_type, {})
        if doc_config.get('source') == 'real':
            continue
        
        raw_table = f"{config.DATABASE['name']}.RAW.{config.DOCUMENT_TYPES[doc_type]['table_name']}"
        corpus_table = f"{config.DATABASE['name']}.CURATED.{config.DOCUMENT_TYPES[doc_type]['corpus_name']}"
        
        # Create standardized corpus table with SecurityID and IssuerID
        session.sql(f"""
            CREATE OR REPLACE TABLE {corpus_table} AS
            SELECT 
                DOCUMENT_ID,
                DOCUMENT_TITLE,
                DOCUMENT_TYPE,
                SecurityID,
                IssuerID,
                PUBLISH_DATE,
                'en' as LANGUAGE,
                RAW_MARKDOWN as DOCUMENT_TEXT
            FROM {raw_table}
        """).collect()
