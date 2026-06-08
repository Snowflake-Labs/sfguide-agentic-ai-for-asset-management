# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Created by Mats Stellwall, Snowflake, and Snowflake CoCo

"""
Simulated Asset Management (SAM) Demo Configuration
All configuration constants for the SAM AI demo using CAPS naming convention.
"""

import os
import pathlib
import sys
import yaml

# Detect workspace execution mode
IN_WORKSPACE = os.environ.get('SNOWFLAKE_NOTEBOOK_RUNTIME') is not None

# Path resolution: __file__ is not available in Snowflake Workspaces
try:
    _CONFIG_FILE_DIR = pathlib.Path(__file__).resolve().parent
except NameError:
    # Workspace mode: working directory is workspace root, this file is in python/
    _CONFIG_FILE_DIR = pathlib.Path(os.getcwd()) / 'python'
    if not _CONFIG_FILE_DIR.exists():
        _CONFIG_FILE_DIR = pathlib.Path(os.getcwd())

_REF_DIR = _CONFIG_FILE_DIR.parent / "data" / "reference_data"

def _load_ref(name: str) -> dict:
    with open(_REF_DIR / f"{name}.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

REF_DATA = {
    "companies": _load_ref("companies"),
    "clients": _load_ref("clients"),
    "scenarios": _load_ref("scenarios"),
    "data_sources": _load_ref("data_sources"),
    "distributions": _load_ref("distributions"),
    "documents": _load_ref("documents"),
    "evaluations": _load_ref("evaluations"),
    "drill_down_questions": _load_ref("drill_down_questions"),
    "research_theses": _load_ref("research_theses"),
    "portfolio_managers": _load_ref("portfolio_managers"),
}

# #############################################################################
#
#                       USER-EDITABLE SETTINGS
#
#  The settings below are the most commonly changed by users. Modify these
#  first when customizing the demo for your environment.
#
# #############################################################################

# =============================================================================
# CONNECTION & CORE BUILD SETTINGS
# =============================================================================

# Snowflake connection name (from ~/.snowflake/connections.toml)
DEFAULT_CONNECTION_NAME = 'sfseeurope-mstellwall-aws-us-west3'

# Seed for reproducible random generation (change to get different deterministic output)
RNG_SEED = 42

# Historical data range (years of position/transaction history to generate)
YEARS_OF_HISTORY = 5

# Test mode multiplier - scales down data volumes for faster dev builds (e.g. 0.1 = 10%)
TEST_MODE_MULTIPLIER = 0.1

# =============================================================================
# AI MODEL CONFIGURATION
# =============================================================================

# Model used for speaker identification in transcript processing (AI_COMPLETE)
# Options: 'claude-haiku-4-5', 'claude-sonnet-4', 'llama3.1-8b', etc.
AI_SPEAKER_IDENTIFICATION_MODEL = 'openai-gpt-5-nano'

AI_SIGNAL_EXTRACTION_MODEL = 'openai-gpt-5-nano'

# Model used for agent orchestration (Snowflake Intelligence agents)
AGENT_ORCHESTRATION_MODEL = 'claude-opus-4-7'

# Budget limits for agent orchestration (prevents runaway costs)
AGENT_BUDGET_SECONDS = 300
AGENT_BUDGET_TOKENS = 32000

# Model used for text embeddings (Cortex Search, token counting)
AI_EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'

# =============================================================================
# DATABASE & WAREHOUSE CONFIGURATION
# =============================================================================

DATABASE = {
    'name': 'SAM_DEMO',
    'schemas': {
        'raw': 'RAW',
        'curated': 'CURATED',
        'ai': 'AI',
        'market_data': 'MARKET_DATA',  # External provider data (financial statements, estimates, filings)
        'ml': 'ML'  # Machine learning: Feature Store, Model Registry, ML Observability
    }
}

WAREHOUSES = {
    'execution': {
        'name': 'SAM_DEMO_EXECUTION_WH',
        'size': 'LARGE',
        'comment': 'Warehouse for SAM demo data generation and execution'
    },
    'cortex_search': {
        'name': 'SAM_DEMO_CORTEX_WH',
        'size': 'MEDIUM',
        'target_lag': '5 minutes',
        'comment': 'Warehouse for SAM demo Cortex Search services'
    }
}

# =============================================================================
# STREAMLIT CONTAINER RUNTIME CONFIGURATION
# =============================================================================

STREAMLIT = {
    'compute_pool': 'FSI_DEMO_STREAMLIT_COMPUTE_POOL',
    'compute_pool_instance_family': 'CPU_X64_S',
    'compute_pool_min_nodes': 1,
    'compute_pool_max_nodes': 3,
    'external_access_integration': 'FSI_DEMO_PYPI_ACCESS',
    'auto_create_resources': False,
    'comment': 'Container Runtime settings for Streamlit apps'
}

# =============================================================================
# COCKPIT SPCS DEPLOYMENT CONFIGURATION
# =============================================================================

COCKPIT = {
    'compute_pool': 'FSI_DEMO_APP_COMPUTE_POOL',
    'compute_pool_instance_family': 'CPU_X64_S',
    'compute_pool_min_nodes': 1,
    'compute_pool_max_nodes': 2,
    'image_repo': 'FSI_DEMO_CONFIG.SPCS.FSI_DEMO_REPOSITORY',
    'service_fqn': 'FSI_DEMO_CONFIG.SPCS.FSI_AI_DEMO_COCKPIT',
    'image_name': 'fsi-ai-demo-cockpit',
    'port': 8080,
    'min_instances': 1,
    'max_instances': 1,
    'auto_create_resources': False,
    'external_access_integration': 'FSI_DEMO_SNOWFLAKE_API_ACCESS',
    'app_dir': 'fsi-ai-demo-cockpit',
    # Shared application state (cross-demo tables read by the cockpit)
    'app_database': 'FSI_DEMO_CONFIG',
    'app_schema': 'APP',
    'demo_id': 'emea_am_ai_demo',
}

# =============================================================================
# MACHINE LEARNING CONFIGURATION
# =============================================================================

ML_CONFIG = {
    'feature_store_name': 'ML',
    'feature_store_warehouse': 'SAM_DEMO_EXECUTION_WH',
    'model_registry_database': 'SAM_DEMO',
    'model_registry_schema': 'ML',
    'refresh_freq': '1 day',
    'regime_model': {
        'name': 'MARKET_REGIME_GMM',
        'version_prefix': 'v',
        'n_components': 3,
        'features': ['VIX_LEVEL', 'YIELD_SPREAD', 'CREDIT_SPREAD', 'MOMENTUM_20D'],
    },
    'factor_model': {
        'name': 'FACTOR_RETURN_XGBOOST',
        'version_prefix': 'v',
    },
    'credit_risk_model': {
        'name': 'CREDIT_RISK_XGBOOST',
        'version_prefix': 'v',
    },
    'default_target_platforms': ['WAREHOUSE'],
    'monitor_refresh_interval': '1 day',
    'monitor_aggregation_window': '1 day',
}



# =============================================================================
# REAL DATA SOURCES (external public data shares)
# =============================================================================
#
# Point these to your public data share. The tables dict is defined later in
# REAL_DATA_SOURCES_TABLES and attached to this dict after the file loads.
#
REAL_DATA_SOURCES = {
    # -------------------------------------------------------------------------
    # Change these two values to match your Snowflake Marketplace data share
    # -------------------------------------------------------------------------
    'database': 'SNOWFLAKE_PUBLIC_DATA_FREE', # 'SNOWFLAKE_PUBLIC_DATA_PAID', 
    #'database': 'FINANCIALS_ECONOMICS_ENTERPRISE',
    #'schema': 'PUBLIC_DATA_FREE',              # e.g. 'PUBLIC_DATA_FREE'
    'schema': 'CYBERSYN',
    # Key into REAL_DATA_SOURCES['tables'] to probe for share access (must exist in share)
    # IMPORTANT: This data source is REQUIRED. The build will fail if not accessible.
    'access_probe_table_key': 'sec_metrics'
}

# =============================================================================
# DEMO COMPANIES - Single Source of Truth for Company Data
# =============================================================================
#
# Loaded from data/reference_data/companies.yaml
# See that file for structure documentation, tier definitions, and totals.
#
DEMO_COMPANIES = {
    entry['ticker']: {k: v for k, v in entry.items() if k != 'ticker'}
    for entry in REF_DATA['companies']['companies']
}


# Helper functions for DEMO_COMPANIES (moved to demo_helpers.py)
# Re-exported at end of file for backward compatibility

# =============================================================================
# DATE RANGE HELPERS (functions moved to db_helpers.py)
# =============================================================================
# Re-exported at end of file for backward compatibility

# =============================================================================
# DEMO CLIENTS — loaded from data/reference_data/clients.yaml
# =============================================================================
DEMO_CLIENTS = REF_DATA['clients']['clients']

# #############################################################################
#
#                       END OF USER-EDITABLE SETTINGS
#
#  Settings below are advanced / internal. Only modify if you know what you
#  are doing.
#
# #############################################################################

# =============================================================================
# LOGGING & OUTPUT CONTROL (functions moved to logging_utils.py)
# =============================================================================
# Re-exported at end of file for backward compatibility


# =============================================================================
# MARKET_DATA SCHEMA CONFIGURATION
# =============================================================================

# Controls MARKET_DATA schema generation and synthetic data parameters
# Note: Table definitions are in REAL_DATA_SOURCES_TABLES (Cybersyn source catalog)
MARKET_DATA = {
    'enabled': True,
    'synthetic_dividends': True,
    'generation': {
        'years_of_history': YEARS_OF_HISTORY,
        'quarters_per_year': 4,
        'estimates_forward_years': 2,
        'brokers_per_company': (3, 8),  # Min/max broker coverage
        'revision_frequency': 0.3  # 30% of estimates get revised
    }
}

# Broker names for synthetic data
BROKER_NAMES = [
    'Goldman Sachs', 'Morgan Stanley', 'JPMorgan', 'Bank of America', 'Citigroup',
    'Barclays', 'Deutsche Bank', 'UBS', 'Credit Suisse', 'Wells Fargo',
    'RBC Capital', 'Jefferies', 'Piper Sandler', 'Baird', 'Stifel',
    'Raymond James', 'Cowen', 'Needham', 'Wedbush', 'Loop Capital'
]

# =============================================================================
# HELPER FUNCTIONS FOR DATABASE PATHS (moved to db_helpers.py)
# =============================================================================
# Re-exported at end of file for backward compatibility

# =============================================================================
# DATA MODEL CONFIGURATION
# =============================================================================

# Enhanced data model settings
DATA_MODEL = {
    'use_transaction_based': True,
    'generate_corporate_hierarchies': True,
    'issuer_hierarchy_depth': 2,
    'transaction_months': 12,
    'transaction_types': ['BUY', 'SELL', 'DIVIDEND', 'CORPORATE_ACTION'],
    'avg_monthly_transactions_per_security': 2.5,
    'portfolio_code_prefix': 'SAM',
    
    'synthetic_distributions': REF_DATA['distributions']
}

# =============================================================================
# REAL DATA SOURCES — loaded from data/reference_data/data_sources.yaml
# =============================================================================
REAL_DATA_SOURCES_TABLES = REF_DATA['data_sources']['tables']

REAL_DATA_SOURCES['tables'] = REAL_DATA_SOURCES_TABLES

# =============================================================================
# COMPLIANCE & RISK CONFIGURATION
# =============================================================================

COMPLIANCE_RULES = {
    'concentration': {
        'max_single_issuer': 0.07,     # 7%
        'warning_threshold': 0.065,    # 6.5%
        'tech_portfolio_max': 0.065    # 6.5% for technology portfolios
    },
    'fi_guardrails': {
        'min_investment_grade': 0.75,  # 75%
        'max_ccc_below': 0.05,         # 5%
        'duration_tolerance': 1.0      # ±1.0 years vs benchmark
    },
    'esg': {
        'min_overall_rating': 'BBB',
        'exclude_high_controversy': True,
        'applicable_portfolios': ['SAM ESG Leaders Global Equity', 'SAM Renewable & Climate Solutions'],
        'grade_thresholds': [(86, 'AAA'), (71, 'AA'), (57, 'A'), (43, 'BBB'), (29, 'BB'), (14, 'B')],
        'default_grade': 'CCC',
        'default_provider': 'MSCI',
        'overall_weights': {'E': 1.0, 'S': 1.0, 'G': 1.0}
    }
}

# =============================================================================
# PORTFOLIO CONFIGURATION
# =============================================================================

# Demo portfolios that get special document coverage
DEMO_PORTFOLIOS_WITH_DOCS = [
    'SAM Technology & Infrastructure',
    'SAM Global Thematic Growth',
    'SAM Multi-Asset Income',
    'SAM ESG Leaders Global Equity'
]

# Default demo portfolio for examples
DEFAULT_DEMO_PORTFOLIO = 'SAM Technology & Infrastructure'

PORTFOLIOS = {
    'SAM Technology & Infrastructure': {
        'benchmark': 'Nasdaq 100',
        'aum_usd': 1.5e9,
        'strategy': 'Growth',
        'inception_date': '2019-01-01',
        'base_currency': 'USD',
        'is_demo_portfolio': True,
        # Priority holdings and position sizes now defined in DEMO_COMPANIES (demo_order, position_size)
        'filler_holdings': 'tech_stocks',
        'target_position_count': 45
    },
    'SAM Global Flagship Multi-Asset': {
        'benchmark': 'MSCI ACWI',
        'aum_usd': 2.5e9,
        'strategy': 'Multi-Asset',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM ESG Leaders Global Equity': {
        'benchmark': 'MSCI ACWI',
        'aum_usd': 1.8e9,
        'strategy': 'ESG',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM US Core Equity': {
        'benchmark': 'S&P 500',
        'aum_usd': 1.2e9,
        'strategy': 'Core',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Renewable & Climate Solutions': {
        'benchmark': 'Nasdaq 100',
        'aum_usd': 1.0e9,
        'strategy': 'ESG',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Sustainable Global Equity': {
        'benchmark': 'MSCI ACWI',
        'aum_usd': 1.1e9,
        'strategy': 'ESG',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM AI & Digital Innovation': {
        'benchmark': 'Nasdaq 100',
        'aum_usd': 0.9e9,
        'strategy': 'Growth',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Global Balanced 60/40': {
        'benchmark': 'MSCI ACWI',
        'aum_usd': 0.8e9,
        'strategy': 'Multi-Asset',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Tech Disruptors Equity': {
        'benchmark': 'Nasdaq 100',
        'aum_usd': 0.7e9,
        'strategy': 'Growth',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM US Value Equity': {
        'benchmark': 'S&P 500',
        'aum_usd': 0.6e9,
        'strategy': 'Value',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Multi-Asset Income': {
        'benchmark': 'S&P 500',
        'aum_usd': 0.5e9,
        'strategy': 'Income',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    }
}

# =============================================================================
# SCENARIO SEED DATA — loaded from data/reference_data/scenarios.yaml
# =============================================================================
SCENARIO_3_2_MANDATE_COMPLIANCE = REF_DATA['scenarios']['mandate_compliance']
ESG_DEMO_OVERRIDES = REF_DATA['scenarios']['esg_overrides']
SUPPLY_CHAIN_DEMO_RELATIONSHIPS = REF_DATA['scenarios']['supply_chain_relationships']
SUPPLY_CHAIN_RELATIONSHIP_STRENGTHS = REF_DATA['scenarios']['supply_chain_strengths']

# =============================================================================
# SCENARIO & AGENT CONFIGURATION — Single Source of Truth
# =============================================================================
# Each scenario maps to its full set of dependencies: agent, data, tables,
# views, search services, tools. Subsystems resolve what to build from here.
#
# Scenario types:
#   "agent" — Demoed via Snowflake Intelligence or the Cockpit (has a Cortex Agent)
#   "ml"    — Demoed via notebooks (ML model training/inference, no agent)
# =============================================================================

SCENARIOS = {
    # ─── AGENT SCENARIOS ───────────────────────────────────────────────────────
    'portfolio_management': {
        'type': 'agent',
        'name': 'Portfolio Management',
        'description': 'Unified portfolio management — holdings, implementation, attribution, stress testing, risk, market context, and proactive insights',
        'agent': {
            'name': 'AM_portfolio_management_copilot',
            'display_name': 'Portfolio Management Copilot',
        },
        'required_data': [
            'broker_research', 'company_event_transcripts', 'press_releases',
            'macro_events', 'report_templates', 'policy_docs', 'ips', 'methodology_docs',
        ],
        'required_tables': ['dimensions', 'fact_tables', 'compliance', 'ml_tables'],
        'data_phases': [
            'market_data', 'attribution', 'factor_exposures',
            'portfolio_modelling', 'nlp_scoring',
        ],
        'required_views': [
            'SAM_PORTFOLIO_VIEW', 'SAM_IMPLEMENTATION_VIEW', 'SAM_ATTRIBUTION_VIEW',
            'SAM_MARKET_VIEW', 'SAM_RESEARCH_VIEW', 'SAM_PROACTIVE_INSIGHTS_VIEW',
            'SAM_SIGNALS_VIEW', 'SAM_PORTFOLIO_MODELLING_VIEW', 'SAM_TOOL_RESULTS_VIEW',
            'SAM_REGIME_VIEW', 'SAM_FACTOR_MODEL_VIEW',
        ],
        'required_services': ['sec_filings'],
        'required_tools': ['portfolio_modelling', 'pdf_report', 'data_origin', 'ma_simulation'],
    },
    'research': {
        'type': 'agent',
        'name': 'Research',
        'description': 'Document research and analysis',
        'agent': {
            'name': 'AM_research_copilot',
            'display_name': 'Research Copilot',
        },
        'required_data': ['broker_research', 'company_event_transcripts', 'press_releases'],
        'required_tables': ['dimensions', 'fact_tables'],
        'data_phases': ['market_data'],
        'required_views': ['SAM_RESEARCH_VIEW'],
        'required_services': ['sec_filings'],
        'required_tools': ['pdf_report', 'data_origin'],
    },
    'risk_compliance': {
        'type': 'agent',
        'name': 'Risk & Compliance',
        'description': 'ESG risk monitoring, mandate compliance, regulatory oversight, and stewardship',
        'agent': {
            'name': 'AM_risk_compliance_copilot',
            'display_name': 'Risk & Compliance Copilot',
        },
        'required_data': [
            'ngo_reports', 'engagement_notes', 'policy_docs', 'press_releases',
            'report_templates', 'regulatory_docs', 'ips',
        ],
        'required_tables': ['dimensions', 'fact_tables', 'compliance'],
        'data_phases': ['market_data'],
        'required_views': ['SAM_PORTFOLIO_VIEW', 'SAM_RESEARCH_VIEW', 'SAM_MARKET_VIEW'],
        'required_services': ['sec_filings'],
        'required_tools': ['pdf_report', 'data_origin'],
    },
    'client_advisory': {
        'type': 'agent',
        'name': 'Client Advisory',
        'description': 'Client reporting, presentation preparation, and relationship management',
        'agent': {
            'name': 'AM_client_advisory_copilot',
            'display_name': 'Client Advisory Copilot',
        },
        'required_data': ['sales_templates', 'philosophy_docs', 'policy_docs', 'regulatory_docs'],
        'required_tables': ['dimensions', 'fact_tables'],
        'data_phases': [],
        'required_views': [
            'SAM_PORTFOLIO_VIEW', 'SAM_RESEARCH_VIEW', 'SAM_ATTRIBUTION_VIEW',
            'SAM_IMPLEMENTATION_VIEW',
        ],
        'required_services': [],
        'required_tools': ['pdf_report', 'data_origin'],
    },
    'operations': {
        'type': 'agent',
        'name': 'Operations',
        'description': 'Middle office operations monitoring and NAV calculation',
        'agent': {
            'name': 'AM_operations_copilot',
            'display_name': 'Operations Copilot',
        },
        'required_data': ['custodian_reports', 'reconciliation_notes', 'ssi_documents', 'ops_procedures'],
        'required_tables': ['dimensions', 'fact_tables'],
        'data_phases': [],
        'required_views': ['SAM_MIDDLE_OFFICE_VIEW'],
        'required_services': [],
        'required_tools': ['data_origin'],
    },
    'executive_leadership': {
        'type': 'agent',
        'name': 'Executive Leadership',
        'description': 'Firm-wide KPIs, client analytics, and strategic M&A analysis',
        'agent': {
            'name': 'AM_executive_leadership_copilot',
            'display_name': 'Executive Leadership Copilot',
        },
        'required_data': ['strategy_documents', 'press_releases', 'broker_research'],
        'required_tables': ['dimensions', 'fact_tables'],
        'data_phases': ['market_data'],
        'required_views': [
            'SAM_PORTFOLIO_VIEW', 'SAM_RESEARCH_VIEW', 'SAM_ATTRIBUTION_VIEW',
            'SAM_EXECUTIVE_VIEW',
        ],
        'required_services': ['sec_filings'],
        'required_tools': ['pdf_report', 'data_origin', 'ma_simulation'],
    },
    'private_equity': {
        'type': 'agent',
        'name': 'Private Equity',
        'description': 'Deal sourcing, due diligence, portfolio monitoring, and value creation tracking',
        'agent': {
            'name': 'AM_private_equity_copilot',
            'display_name': 'Private Equity Copilot',
        },
        'required_data': [],
        'required_tables': ['dimensions', 'pe_tables'],
        'data_phases': [],
        'required_views': [
            'SAM_PE_DEAL_PIPELINE_VIEW', 'SAM_PE_VALUE_CREATION_VIEW', 'SAM_RESEARCH_VIEW',
        ],
        'required_services': ['sec_filings', 'pe_search'],
        'required_tools': ['pdf_report', 'data_origin'],
    },
    'private_credit': {
        'type': 'agent',
        'name': 'Private Credit',
        'description': 'Credit portfolio monitoring, covenant tracking, rate sensitivity analysis, deal pipeline management, and ML credit risk scoring',
        'agent': {
            'name': 'AM_private_credit_copilot',
            'display_name': 'Private Credit Copilot',
        },
        'required_data': [],
        'required_tables': ['dimensions', 'credit_tables'],
        'data_phases': [],
        'required_views': ['SAM_CREDIT_PORTFOLIO_VIEW', 'SAM_RESEARCH_VIEW', 'SAM_MARKET_VIEW'],
        'required_services': ['sec_filings', 'credit_search'],
        'required_tools': ['pdf_report', 'data_origin'],
    },

    # ─── ML SCENARIOS ──────────────────────────────────────────────────────────
    'market_regime_ml': {
        'type': 'ml',
        'name': 'Market Regime Detection',
        'description': 'ML regime detection via Feature Store + notebooks',
        'agent': None,
        'required_data': [],
        'required_tables': ['dimensions', 'ml_tables'],
        'data_phases': ['market_data', 'factor_exposures'],
        'required_views': ['SAM_REGIME_VIEW'],
        'required_services': [],
        'required_tools': [],
    },
    'factor_workflow_ml': {
        'type': 'ml',
        'name': 'Factor Model Workflow',
        'description': 'ML factor models via Feature Store + notebooks',
        'agent': None,
        'required_data': [],
        'required_tables': ['dimensions', 'ml_tables'],
        'data_phases': ['market_data', 'factor_exposures'],
        'required_views': ['SAM_FACTOR_MODEL_VIEW'],
        'required_services': [],
        'required_tools': [],
    },
    'credit_risk_ml': {
        'type': 'ml',
        'name': 'Credit Risk Scoring',
        'description': 'ML credit risk scoring via Feature Store + notebooks',
        'agent': None,
        'required_data': [],
        'required_tables': ['dimensions', 'credit_tables', 'ml_tables'],
        'data_phases': [],
        'required_views': ['SAM_CREDIT_RISK_VIEW'],
        'required_services': [],
        'required_tools': [],
    },
}


# ─── Derived constants (backward compatibility) ───────────────────────────────

AVAILABLE_SCENARIOS = list(SCENARIOS.keys())

ML_SCENARIOS = [s for s, cfg in SCENARIOS.items() if cfg['type'] == 'ml']

SCENARIO_AGENTS = {
    s: {
        'agent_name': cfg['agent']['name'],
        'display_name': cfg['agent']['display_name'],
        'description': cfg['description'],
    }
    for s, cfg in SCENARIOS.items() if cfg.get('agent')
}

SCENARIO_DATA_REQUIREMENTS = {
    s: cfg.get('required_data', []) for s, cfg in SCENARIOS.items()
}


# ─── Helper functions ─────────────────────────────────────────────────────────

def get_all_scenarios():
    """Get list of all available scenario keys."""
    return list(SCENARIOS.keys())


def get_agent_scenarios():
    """Get list of scenarios that have an agent."""
    return [s for s, cfg in SCENARIOS.items() if cfg.get('agent')]


def get_ml_scenarios():
    """Get list of ML scenarios (no agent, notebook-based)."""
    return [s for s, cfg in SCENARIOS.items() if cfg['type'] == 'ml']


def get_scenario_config(scenario):
    """Get full configuration for a specific scenario."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Invalid scenario '{scenario}'. Valid: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario]


def validate_scenarios(scenarios):
    """Validate and return list of scenarios. 'all' returns everything."""
    if not scenarios or scenarios == ['all']:
        return get_all_scenarios()
    invalid = [s for s in scenarios if s not in SCENARIOS]
    if invalid:
        raise ValueError(f"Invalid scenarios: {invalid}. Valid: {list(SCENARIOS.keys())}")
    return scenarios


def get_required_views(scenarios):
    """Get ordered, deduplicated list of semantic views needed for scenarios."""
    seen = set()
    ordered = []
    for s in scenarios:
        for v in SCENARIOS.get(s, {}).get('required_views', []):
            if v not in seen:
                seen.add(v)
                ordered.append(v)
    return ordered


def get_required_services(scenarios):
    """Get set of search service keys needed for scenarios."""
    services = set()
    for s in scenarios:
        services.update(SCENARIOS.get(s, {}).get('required_services', []))
    return services


def get_required_tools(scenarios):
    """Get set of tool group keys needed for scenarios."""
    tools = set()
    for s in scenarios:
        tools.update(SCENARIOS.get(s, {}).get('required_tools', []))
    return tools


def get_data_phases(scenarios):
    """Get set of data build phases needed for scenarios."""
    phases = set()
    for s in scenarios:
        phases.update(SCENARIOS.get(s, {}).get('data_phases', []))
    return phases


def get_required_tables(scenarios):
    """Get set of table group keys needed for scenarios."""
    tables = set()
    for s in scenarios:
        tables.update(SCENARIOS.get(s, {}).get('required_tables', []))
    return tables


def get_scenario_agents(scenarios):
    """Get dict of scenario→agent config for given scenarios (excludes ML)."""
    return {
        s: SCENARIOS[s]['agent']
        for s in scenarios
        if s in SCENARIOS and SCENARIOS[s].get('agent')
    }

# =============================================================================
# DOCUMENT GENERATION CONFIGURATION
# =============================================================================

# Paths
try:
    CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Workspace mode
    CONFIG_DIR = os.path.join(os.getcwd(), 'python')
    if not os.path.isdir(CONFIG_DIR):
        CONFIG_DIR = os.getcwd()
PROJECT_ROOT = os.path.dirname(CONFIG_DIR)
CONTENT_LIBRARY_PATH = os.path.join(PROJECT_ROOT, 'content_library')
CONTENT_VERSION = '1.0'

# =============================================================================
# SECTOR MAPPING CONFIGURATION (for template selection)
# =============================================================================

# Map SIC industry descriptions to GICS sectors for template matching
SIC_TO_GICS_MAPPING = {
    'Information Technology': [
        'software', 'computer programming', 'prepackaged software', 'data processing',
        'computer systems design', 'information retrieval', 'computer facilities',
        'semiconductors', 'electronic computers', 'computer peripheral',
        'computer integrated systems', 'computer storage devices', 'computer terminals'
    ],
    'Health Care': [
        'pharmaceutical', 'drugs', 'medicinal', 'biological', 'medical',
        'hospital', 'health', 'diagnostic', 'surgical', 'dental',
        'biotechnology', 'medical instruments', 'medical laboratories'
    ],
    'Consumer Discretionary': [
        'retail', 'automobile', 'motor vehicle', 'apparel', 'restaurant',
        'hotel', 'broadcasting', 'cable', 'media', 'entertainment', 'leisure',
        'department store', 'specialty retail', 'home furnishing'
    ],
    'Financials': [
        'bank', 'insurance', 'investment', 'securities', 'credit',
        'finance', 'real estate', 'mortgage', 'savings institution',
        'asset management', 'capital markets'
    ],
    'Energy': [
        'oil', 'gas', 'petroleum', 'crude', 'coal', 'energy',
        'exploration', 'drilling', 'refining', 'pipeline'
    ],
    'Industrials': [
        'aerospace', 'defense', 'construction', 'machinery', 'equipment',
        'transportation', 'airline', 'railroad', 'trucking', 'freight',
        'engineering', 'electrical equipment', 'industrial machinery'
    ],
    'Consumer Staples': [
        'food', 'beverage', 'tobacco', 'household products', 'personal products',
        'grocery', 'packaged foods', 'soft drinks'
    ],
    'Materials': [
        'chemicals', 'metals', 'mining', 'paper', 'packaging',
        'steel', 'aluminum', 'gold', 'silver', 'construction materials'
    ],
    'Utilities': [
        'electric', 'water', 'natural gas utility', 'power generation',
        'electric services', 'water supply'
    ],
    'Communication Services': [
        'telecommunications', 'wireless', 'internet services', 'social media',
        'telephone communications', 'cable television'
    ],
    'Real Estate': [
        'reit', 'real estate investment', 'property management',
        'real estate operating', 'real estate development'
    ]
}

# =============================================================================
# ADDING A NEW PDF DOCUMENT TYPE
# =============================================================================
# DOCUMENT TYPES — loaded from data/reference_data/documents.yaml
# =============================================================================
DOCUMENT_TYPES = REF_DATA['documents']['document_types']

# =============================================================================
# MARKET & REFERENCE DATA CONFIGURATION
# =============================================================================

BENCHMARKS = [
    {
        'id': 'SP500',
        'name': 'S&P 500',
        'currency': 'USD',
        'provider': 'PLM',
        'holdings_rules': {
            'constituent_count': 500,
            'filters': {'country': 'US'},
            'raw_weight_range': (0.001, 0.07),
            'min_weight': 0.0001,
            'assumed_benchmark_mv_usd': 1_000_000_000
        }
    },
    {
        'id': 'MSCI_ACWI',
        'name': 'MSCI ACWI',
        'currency': 'USD',
        'provider': 'NSD',
        'holdings_rules': {
            'constituent_count': 800,
            'filters': {'all': True},  # No country filter
            'weight_by_country': {     # Country-differentiated weights
                'US': (0.001, 0.05),
                '_default': (0.0001, 0.01)
            },
            'min_weight': 0.0001,
            'assumed_benchmark_mv_usd': 1_000_000_000
        }
    },
    {
        'id': 'NASDAQ100',
        'name': 'Nasdaq 100',
        'currency': 'USD',
        'provider': 'PLM',
        'holdings_rules': {
            'constituent_count': 100,
            'filters': {'exclude_sector': 'Financials'},
            'raw_weight_range': (0.005, 0.12),
            'min_weight': 0.0001,
            'assumed_benchmark_mv_usd': 1_000_000_000
        }
    }
]

# Data distribution
DATA_DISTRIBUTION = {
    'regions': {'US': 0.55, 'Europe': 0.30, 'APAC_EM': 0.15},
    'asset_classes': {'equities': 1.0},  # Equities only with new DEMO_COMPANIES approach
}

# Currency & Calendar
BASE_CURRENCY = 'USD'
SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP']
FX_HEDGING = 'FULLY_HEDGED'
TRADING_CALENDAR = 'UTC_BUSINESS_DAYS'
RETURNS_FREQUENCY = 'MONTHLY'

# =============================================================================
# CONTENT GENERATION CONFIGURATION
# =============================================================================

# ESG Controversy Keywords
ESG_CONTROVERSY_KEYWORDS = {
    'environmental': {
        'high': ['toxic spill', 'environmental disaster', 'illegal dumping', 'major pollution'],
        'medium': ['environmental violation', 'emissions breach', 'waste management'],
        'low': ['environmental concern', 'sustainability question']
    },
    'social': {
        'high': ['forced labor', 'child labor', 'human rights violation', 'workplace fatality'],
        'medium': ['labor dispute', 'workplace injury', 'discrimination allegation'],
        'low': ['employee concern', 'workplace issue']
    },
    'governance': {
        'high': ['fraud investigation', 'criminal charges', 'regulatory sanction'],
        'medium': ['accounting irregularity', 'governance breach', 'compliance violation'],
        'low': ['governance concern', 'board dispute']
    }
}

# Fictional provider names
FICTIONAL_BROKER_NAMES = [
    'Ashfield Partners', 'Northgate Analytics', 'Blackstone Ridge Research',
    'Fairmont Capital Insights', 'Kingswell Securities Research',
    'Brookline Advisory Group', 'Harrow Street Markets', 'Marlowe & Co. Research',
    'Crescent Point Analytics', 'Sterling Wharf Intelligence', 'Granite Peak Advisory',
    'Alder & Finch Investments', 'Bluehaven Capital Research', 'Regent Square Analytics',
    'Whitestone Equity Research'
]

FICTIONAL_NGO_NAMES = {
    'environmental': [
        'Global Sustainability Watch', 'Environmental Justice Initiative',
        'Climate Action Network', 'Green Future Alliance'
    ],
    'social': [
        'Human Rights Monitor', 'Labour Rights Observatory',
        'Ethical Investment Coalition', 'Fair Workplace Institute'
    ],
    'governance': [
        'Corporate Accountability Forum', 'Transparency Advocacy Group',
        'Corporate Responsibility Institute', 'Ethical Governance Council'
    ]
}

# =============================================================================
# PDF EXPORT CONFIGURATION
# =============================================================================

# Enable local PDF export of generated documents (set to False to skip PDF export)
PDF_EXPORT_ENABLED = True

# Root folder for PDF output (relative to project root if not absolute)
UNSTRUCTURED_PDF_OUTPUT_DIR = 'generated_pdfs'

# Default audience mapping for PDF headers/footers by document type
# 'internal' uses SAM (Simulated Asset Management) branding
# 'external' uses source-specific branding (broker/company/NGO)
PDF_DOC_AUDIENCE = {
    # Internal documents (SAM logo and letterhead)
    'internal_research': 'internal',
    'investment_memo': 'internal',
    'policy_docs': 'internal',
    'philosophy_docs': 'internal',
    'report_templates': 'internal',
    'ops_procedures': 'internal',
    'reconciliation_notes': 'internal',
    'ssi_documents': 'internal',
    'custodian_reports': 'internal',
    'strategy_documents': 'internal',
    'macro_events': 'internal',
    'engagement_notes': 'internal',
    'methodology_docs': 'internal',  # Portfolio modelling methodology docs
    'ips': 'internal',  # Investment Policy Statements
    # External documents (broker/company/NGO branding)
    'broker_research': 'external',
    'press_releases': 'external',
    'ngo_reports': 'external',
    'sales_templates': 'internal',  # SAM outgoing so uses internal branding
    # Real data types (skip PDF export by default)
    'company_event_transcripts': 'skip',
    # Regulatory documents (dedicated pipeline)
    'regulatory_docs': 'regulatory',
}


def get_internal_pdf_doc_types():
    """Get list of document types that use the internal PDF pipeline."""
    return [doc_type for doc_type, audience in PDF_DOC_AUDIENCE.items() 
            if audience == 'internal']


def get_external_pdf_doc_types():
    """Get list of document types that use the external PDF pipeline."""
    return [doc_type for doc_type, audience in PDF_DOC_AUDIENCE.items() 
            if audience == 'external']


# =============================================================================
# AGENT EVALUATIONS — loaded from data/reference_data/evaluations.yaml
# =============================================================================
TOOL_SERVICE_MAP = REF_DATA['evaluations']['tool_service_map']
AGENT_EVALUATIONS = REF_DATA['evaluations']['agent_evaluations']

# =============================================================================
# END OF CONFIGURATION
# =============================================================================
