"""
SAM Demo - Simulated Asset Management Demo Environment

This package contains all modules for building and managing the SAM demo,
including data generation, AI components, and utilities.

Package Structure:
    python/
    ├── config.py          # Central configuration
    ├── main.py            # Entry point (build_demo)
    ├── utils/             # Consolidated utilities
    │   ├── logging        # Structured logging
    │   ├── sql            # SQL generation helpers
    │   ├── snowflake      # Snowflake I/O utilities
    │   ├── config_helpers # Config accessor functions
    │   └── demo_helpers   # Demo entity lookups
    ├── data/              # Data generation
    │   ├── structured     # Dimension/fact tables
    │   ├── market_data    # Real market data
    │   ├── unstructured   # Document generation
    │   ├── transcripts    # Real transcript loading
    │   └── pipelines      # Task orchestration
    ├── ai/                # AI components
    │   ├── builder        # Main orchestrator
    │   ├── agents         # Snowflake Intelligence agents
    │   ├── semantic_views # Cortex Analyst views
    │   └── cortex_search  # Search services
    ├── core/              # Business logic
    │   ├── hydration_engine
    │   └── pdf_exporter
    └── export/            # Export functionality
        ├── package        # Scenario packaging
        ├── manifest       # Scenario dependencies
        ├── validate       # Pre-export validation
        └── sql_scripts    # SQL script generation

Usage:
    # Run full demo build
    python main.py --connection-name CONNECTION
    
    # Export scenario
    python main.py --connection-name CONNECTION --export portfolio_copilot
"""

__version__ = "1.0.0"

from . import utils
from . import data
from . import ai
from . import core
