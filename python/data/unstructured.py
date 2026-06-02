"""
Unstructured Data Generation for SAM Demo

This module generates unstructured documents using pipeline-only architecture:

- PDF doc types: Generate PDFs only (no DB write) - pipeline parses from stage
- Non-PDF doc types: Write to RAW tables - pipeline stream triggers corpus build
- Real data types: Skipped (handled by generate_real_transcripts.py)

All corpus creation is handled by pipeline tasks, not direct SQL.

Document types include:
- Broker research reports (PDF)
- Press releases (PDF)
- NGO reports and ESG controversies (PDF)
- Internal engagement notes (PDF)
- Policy documents and sales templates (PDF)
- Custodian reports (non-PDF)
- Reconciliation notes (non-PDF)
"""

from snowflake.snowpark import Session
from typing import List
import config
from core import hydration_engine
from utils.logging import log_warning, log_error, log_success, log_step, log_info


def build_all(session: Session, document_types: List[str], test_mode: bool = False):
    """
    Build all unstructured data using pipeline-only architecture.
    
    - PDF doc types: generate PDFs (uploaded to stages by create_unstructured_pipelines)
    - Non-PDF doc types: write to RAW tables (streams trigger corpus tasks)
    - Real data types: skipped (handled by separate load functions)
    
    NOTE: No corpus tables are created here - pipelines handle all corpus creation.
    
    Args:
        session: Active Snowpark session
        document_types: List of document types to generate
        test_mode: If True, use reduced document counts for faster development
    """
    
    # Ensure database context is set
    try:
        session.sql(f"USE DATABASE {config.DATABASE['name']}").collect()
        session.sql(f"USE SCHEMA {config.DATABASE['schemas']['raw']}").collect()
    except Exception as e:
        log_warning(f" Could not set database context: {e}")
    
    pdf_count = 0
    raw_count = 0
    
    # Generate documents using template hydration
    for doc_type in document_types:
        # Skip real data sources - handled by separate modules (e.g., generate_real_transcripts.py)
        doc_config = config.DOCUMENT_TYPES.get(doc_type, {})
        if doc_config.get('source') == 'real':
            log_success(f" Skipping {doc_type} (real data source - handled separately)")
            continue
        
        try:
            count = hydration_engine.hydrate_documents(session, doc_type, test_mode=test_mode)
            
            # Track output type for summary
            audience = config.PDF_DOC_AUDIENCE.get(doc_type, 'skip')
            if audience in ('internal', 'external'):
                pdf_count += count
                if count > 0:
                    log_info(f"  {doc_type}: {count} PDFs generated")
            else:
                raw_count += count
                if count > 0:
                    log_info(f"  {doc_type}: {count} documents written to RAW")
                
        except Exception as e:
            log_error(f" Failed to hydrate {doc_type}: {e}")
            # Continue with other document types
            continue
    
    # Summary logging
    if pdf_count > 0:
        log_step(f"Generated {pdf_count} PDF documents (will be uploaded to stages)")
    if raw_count > 0:
        log_step(f"Wrote {raw_count} documents to RAW tables (streams will trigger corpus tasks)")
    
    # NOTE: No create_corpus_tables() call - pipelines handle all corpus creation
