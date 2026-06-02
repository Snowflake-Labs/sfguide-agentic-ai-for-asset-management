"""
Data generation modules for SAM Demo.

Modules:
    structured: Dimension and fact tables (DIM_*, FACT_*)
    market_data: Real market data from SEC and Nasdaq
    unstructured: Document generation orchestration
    transcripts: Real earnings call transcript processing
    pipelines: Snowflake Task orchestration for document processing
"""

from . import structured
from . import market_data
from . import unstructured
from . import transcripts
from . import pipelines

__all__ = [
    'structured',
    'market_data',
    'unstructured',
    'transcripts',
    'pipelines',
]
