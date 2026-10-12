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
AI_SPEAKER_IDENTIFICATION_MODEL = 'openai-gpt-5-nano' # Only AWS alternative claude-haiku-4-5

AI_SIGNAL_EXTRACTION_MODEL = 'openai-gpt-5-nano' # Only AWS alternative claude-haiku-4-5

# Model used for agent orchestration (Snowflake Intelligence agents).
# 'auto' is the Snowflake-recommended setting: Cortex selects the highest-quality
# model available to the account, so agents improve as new models ship instead of
# being frozen on a pinned version. Pin an explicit model name only when you need
# run-to-run reproducibility, e.g. while running agent evaluations.
AGENT_ORCHESTRATION_MODEL = 'auto'

# Budget limits for agent orchestration (prevents runaway costs)
AGENT_BUDGET_SECONDS = 600
AGENT_BUDGET_TOKENS = 120000

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

RBAC = {
    'platform_build_role': 'FSI_DEMO_BUILD_ROLE',
    'demo_runtime_role': 'SAM_DEMO_USER_ROLE',
    'legacy_demo_role': 'SAM_DEMO_ROLE',
    'shared_database': 'FSI_DEMO_CONFIG',
    'shared_schemas': {
        'app': 'APP',
        'spcs': 'SPCS',
    },
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
# WEEKLY REFRESH AUTOMATION (Code Bundle + Task)
# =============================================================================
# The weekly incremental refresh is packaged as a Code Bundle and driven by a
# scheduled task, so the demo keeps itself current with no manual trigger.
#
# Source is a STAGE rather than a workspace live path. A workspace path
# ('snow://workspace/"USER$"."PUBLIC"."<name>"/versions/live') needs the
# workspace name, which cannot be discovered at build time - inside a Workspace
# the cwd is only /workspace/<hash>/. Staging the files works identically from a
# Workspace and from a local checkout, so one code path covers both.

WEEKLY_REFRESH = {
    'bundle_name': 'SAM_WEEKLY_BUNDLE',
    'task_name': 'WEEKLY_REFRESH_TASK',
    'stage_name': 'CODE_BUNDLE_STAGE',
    'entrypoint': 'python/weekly_refresh_main.py',
    'arguments': ['--mode', 'weekly'],
    # Monday 06:00 UTC: after the weekend, before the working day in EMEA.
    'schedule': 'USING CRON 0 6 * * 1 UTC',
    'compute_pool': 'SAM_DEMO_BUNDLE_POOL',
    # Optional notification integration for task failures, wired as the task's
    # ERROR_INTEGRATION. Left None because there is nothing valid to point it at
    # here: tasks require a QUEUE-type integration (AWS SNS, Azure Event Grid or
    # GCP Pub/Sub). This account's EMAIL_INTEGRATION is TYPE = EMAIL and is
    # rejected with "is not a valid notification integration for User Tasks", so
    # do not set it to that. Without this, check health with
    # `weekly_refresh_main.py --mode status`, which exits non-zero when unhealthy.
    'error_integration': None,
    # Paths relative to the repo root, copied to the stage preserving layout.
    # config.py resolves data/ and content_library/ as siblings of python/, so
    # the bundle root must mirror the repo layout or template loading breaks.
    'bundle_paths': [
        'python',
        'content_library',
        'data/reference_data',
        'code_bundle.yml',
        'requirements.txt',
    ],
    # Excluded from the upload: caches and generated artefacts.
    'bundle_exclude_dirs': {'__pycache__', '.ipynb_checkpoints', 'generated_pdfs'},
    'bundle_exclude_suffixes': ('.pyc', '.pyo'),
}

# =============================================================================
# INITIAL BUILD CODE BUNDLE
# =============================================================================
# The full environment build also runs as a Code Bundle, so a Workspace user gets
# declarative package installation and queryable run history instead of the old
# "open the file, pip install in a terminal, click Run" sequence.
#
# Unlike WEEKLY_REFRESH this bundle is sourced from the workspace live path rather
# than a stage, and is created by scripts/workspace_setup.sql rather than by
# Python. That is not an inconsistency - it resolves a bootstrap problem. Staging
# files needs a Python client, but this bundle *is* how the Python runs, so it
# cannot stage its own source. The workspace already holds the files, so the
# workspace path needs no upload at all. The weekly bundle keeps its stage source
# because a scheduled task must not depend on a user's workspace continuing to
# exist.

BUILD_BUNDLE = {
    'bundle_name': 'SAM_BUILD_BUNDLE',
    'entrypoint': 'python/workspace_main.py',
    'compute_pool': 'SAM_DEMO_BUNDLE_POOL',
}

# =============================================================================
# STREAMLIT CONTAINER RUNTIME CONFIGURATION
# =============================================================================

STREAMLIT = {
    'compute_pool': 'FSI_DEMO_STREAMLIT_COMPUTE_POOL',
    # Current-generation x86. GEN_X64_G2_4 is the direct equivalent of the older
    # CPU_X64_S (identical 3 vCPU / 13 GiB) with better price-performance.
    'compute_pool_instance_family': 'GEN_X64_G2_4',
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
    # See STREAMLIT above: current-generation equivalent of CPU_X64_S.
    'compute_pool_instance_family': 'GEN_X64_G2_4',
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
    'production_alias': 'PRODUCTION',
    'feature_view_version': 'BUILD',
    'build_trained_for_scenarios': ['private_credit', 'credit_risk_ml', 'market_regime_ml', 'portfolio_management'],
    'build_version_prefix': 'BUILD_',
    'random_seed': 42,
    'regime_model': {
        'name': 'MARKET_REGIME_GMM',
        'version_prefix': 'v',
        'n_components': 3,
        'n_init': 5,
        'features_view': 'V_REGIME_FEATURES',
        'feature_view': 'REGIME_FEATURES',
        'training_dataset': 'REGIME_TRAINING_DS',
        'entity': ('MARKET', 'MARKET_ID', 'GLOBAL'),
        'features': [
            'VIX_LEVEL', 'VIX_20D_MA', 'REALISED_VOL_20D', 'REALISED_VOL_60D',
            'MOMENTUM_20D', 'MOMENTUM_60D', 'SECTOR_DISPERSION', 'VOL_RISK_PREMIUM',
        ],
        'labels_by_vix': ['RISK_ON', 'TRANSITIONAL', 'RISK_OFF'],
        'benchmark_code': 'SPX',
    },
    'factor_model': {
        'name': 'FACTOR_RETURN_XGBOOST',
        'version_prefix': 'v',
    },
    'credit_risk_model': {
        'name': 'CREDIT_RISK_XGBOOST',
        'version_prefix': 'v',
        'features_view': 'V_CREDIT_RISK_FEATURES',
        'labels_view': 'V_CREDIT_RISK_LABELS',
        'feature_view': 'CREDIT_RISK_FEATURES',
        'training_dataset': 'CREDIT_RISK_TRAINING_DS',
        'entity': ('BORROWER', 'BORROWERID'),
        'label': 'NEXT_QUARTER_STRESS',
        'features': [
            'TOTALLEVERAGE', 'NETLEVERAGE', 'INTERESTCOVERAGE', 'FIXEDCHARGECOVERAGE',
            'EBITDA_MARGIN', 'FCF_MARGIN', 'CAPEX_INTENSITY', 'FREECASHFLOW_MM',
            'CASHONHAND_MM', 'REVOLVERAVAILABILITY_MM', 'AVG_COVENANT_HEADROOM',
            'MIN_COVENANT_HEADROOM', 'BREACH_COUNT', 'RATING_ORDINAL', 'REGIME_ORDINAL',
        ],
        'stress_headroom_pct': 5.0,
        'rating_scale': ['BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'CCC+', 'CCC', 'CCC-'],
        'regime_scale': ['RISK_ON', 'TRANSITIONAL', 'RISK_OFF'],
        'risk_bands': [(0.1, 'LOW_RISK'), (0.2, 'MODERATE'), (0.5, 'ELEVATED'), (1.01, 'HIGH_RISK')],
        'shap_top_n': 5,
        'covenant_metric_map': {
            'Max Total Leverage': ('TOTALLEVERAGE', 'max'),
            'Min Interest Coverage': ('INTERESTCOVERAGE', 'min'),
            'Min Fixed Charge Coverage': ('FIXEDCHARGECOVERAGE', 'min'),
        },
        'xgb_params': {
            'objective': 'binary:logistic', 'eval_metric': 'auc', 'max_depth': 3,
            'learning_rate': 0.05, 'n_estimators': 200, 'subsample': 0.8,
            'colsample_bytree': 0.8, 'min_child_weight': 2,
        },
        'cv_splits': 3,
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
    'database': 'SNOWFLAKE_PUBLIC_DATA_FREE',  # e.g. 'SNOWFLAKE_PUBLIC_DATA_FREE'
    #'database': 'FINANCIALS_ECONOMICS_ENTERPRISE',
    #'schema': 'PUBLIC_DATA_FREE',              # e.g. 'PUBLIC_DATA_FREE'
    'schema': 'PUBLIC_DATA_FREE',
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

# Broker names. Deliberately fictional: the demo generates research opinions,
# ratings and price targets, and attributing invented views to real firms would
# be inappropriate. This is the single broker universe - DIM_BROKER,
# FACT_RECOMMENDATION, FACT_ESTIMATE_DATA and the generated documents all use it,
# so a document joins to its own grounded recommendation row.
BROKER_NAMES = [
    'Ashfield Partners', 'Northgate Analytics', 'Blackstone Ridge Research',
    'Fairmont Capital Insights', 'Kingswell Securities Research',
    'Brookline Advisory Group', 'Harrow Street Markets', 'Marlowe & Co. Research',
    'Crescent Point Analytics', 'Sterling Wharf Intelligence', 'Granite Peak Advisory',
    'Alder & Finch Investments', 'Bluehaven Capital Research', 'Regent Square Analytics',
    'Whitestone Equity Research'
]

# Persistent per-broker valuation tilt, applied to fair value when deriving
# price targets. Gives the same stock a spread of targets across brokers so
# consensus-versus-outlier analysis is meaningful. Positive is structurally
# bullish. Any broker absent here defaults to 0.0.
BROKER_BIAS_PCT = {
    # Structurally bullish houses
    'Ashfield Partners': 0.10,
    'Northgate Analytics': 0.06,
    'Blackstone Ridge Research': 0.04,
    'Fairmont Capital Insights': 0.08,
    'Kingswell Securities Research': 0.02,
    # Broadly neutral
    'Brookline Advisory Group': 0.00,
    'Harrow Street Markets': 0.01,
    'Marlowe & Co. Research': -0.01,
    'Crescent Point Analytics': 0.03,
    'Sterling Wharf Intelligence': -0.02,
    # More cautious house views
    'Granite Peak Advisory': -0.05,
    'Alder & Finch Investments': -0.08,
    'Bluehaven Capital Research': -0.03,
    'Regent Square Analytics': -0.06,
    'Whitestone Equity Research': 0.07,
}

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
            'SAM_EXECUTIVE_VIEW',
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
            'SAM_EXECUTIVE_VIEW', 'SAM_IMPLEMENTATION_VIEW',
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
        'required_tables': ['dimensions', 'credit_tables', 'ml_tables'],
        'data_phases': [],
        'required_views': [
            'SAM_CREDIT_PORTFOLIO_VIEW', 'SAM_CREDIT_RISK_VIEW', 'SAM_RESEARCH_VIEW',
            'SAM_MARKET_VIEW',
        ],
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

# =============================================================================
# NUMERIC BOUNDS (content_library/_rules/numeric_bounds.yaml)
# =============================================================================
# Loaded lazily because CONTENT_LIBRARY_PATH is defined below REF_DATA.

_NUMERIC_BOUNDS_CACHE = None


def get_numeric_bounds() -> dict:
    """Load and cache content_library/_rules/numeric_bounds.yaml."""
    global _NUMERIC_BOUNDS_CACHE
    if _NUMERIC_BOUNDS_CACHE is None:
        bounds_path = os.path.join(CONTENT_LIBRARY_PATH, '_rules', 'numeric_bounds.yaml')
        with open(bounds_path, 'r', encoding='utf-8') as f:
            _NUMERIC_BOUNDS_CACHE = yaml.safe_load(f) or {}
    return _NUMERIC_BOUNDS_CACHE


# GICS sector names in numeric_bounds.yaml that differ from DIM_ISSUER.GICS_SECTOR.
# DIM_ISSUER uses 'Healthcare'; the YAML uses 'Health Care'.
SECTOR_NAME_ALIASES = {
    'Health Care': 'Healthcare',
}

# =============================================================================
# ANALYST RATING SCALE
# =============================================================================
# Canonical 5-point scale. Ratings are derived from implied upside rather than
# drawn at random - see python/data/recommendations.py.

RATING_SCALE = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']

# FACT_ESTIMATE_DATA stores ratings as integer codes (DATA_ITEM_ID 5006).
# Keep this the single source of truth for that encoding so the table agents
# query agrees with the wording in the documents they cite.
RATING_TO_CODE = {
    'Strong Buy': 1,
    'Buy': 2,
    'Hold': 3,
    'Sell': 4,
    'Strong Sell': 5,
}

# Editorial stance implied by a rating. Drives both which template variant is
# selected and the stance-dependent prose inside it.
RATING_TO_STANCE = {
    'Strong Buy': 'bull',
    'Buy': 'bull',
    'Hold': 'neutral',
    'Sell': 'bear',
    'Strong Sell': 'bear',
}

# Stance-conditional prose. Templates used to hard-code bullish language -
# "Our positive view is supported by", "Strong unit economics underpin our
# positive thesis" - which read absurdly on the ~23% of names now rated Sell or
# Strong Sell. Rather than duplicating all 14 templates three times, the
# stance-dependent sentences became placeholders resolved from this bank, so
# every template is stance-correct. Full bull/neutral/bear variant files layer
# on top of this for the highest-volume sectors.
#
# Each entry is a list so the same stance does not produce identical prose
# across documents; selection is deterministic on the document identity.
STANCE_PHRASES = {
    'bull': {
        'THESIS_STANCE': ['positive', 'constructive', 'favourable'],
        'THESIS_VERB': ['supports', 'underpins', 'reinforces'],
        'CONVICTION_PHRASE': [
            'We see an attractive risk/reward skew',
            'We believe the shares are materially undervalued',
            'We view current levels as an attractive entry point',
        ],
        'FUNDAMENTAL_FRAMING': [
            'demonstrates robust fundamentals',
            'continues to compound at an attractive rate',
            'is executing ahead of our expectations',
        ],
        'COMPETITIVE_FRAMING': [
            "The company's competitive moat is widening",
            'Competitive positioning continues to strengthen',
            'We see durable competitive advantage',
        ],
        'UNIT_ECONOMICS_FRAMING': [
            'Strong unit economics underpin our positive thesis',
            'Unit economics remain best-in-class',
            'Unit economics support continued reinvestment',
        ],
        'RISK_FRAMING': [
            'Risks to our thesis are identifiable but contained',
            'We see limited downside from current levels',
            'Key risks appear well understood by the market',
        ],
        'RECOMMENDATION_LANGUAGE': [
            'We recommend accumulating positions',
            'We would be buyers on any weakness',
            'We recommend adding to positions',
        ],
        'CATALYST_FRAMING': [
            'Several near-term catalysts could drive re-rating',
            'We see multiple paths to upside',
        ],
    },
    'neutral': {
        'THESIS_STANCE': ['balanced', 'neutral', 'even-handed'],
        'THESIS_VERB': ['informs', 'shapes', 'frames'],
        'CONVICTION_PHRASE': [
            'We see risk/reward as broadly balanced at current levels',
            'We believe the shares are approximately fairly valued',
            'We await a clearer entry point before becoming more constructive',
        ],
        'FUNDAMENTAL_FRAMING': [
            'shows a mixed fundamental picture',
            'is delivering in line with our expectations',
            'shows steady but unspectacular execution',
        ],
        'COMPETITIVE_FRAMING': [
            'Competitive positioning is stable but not improving',
            'The company holds its ground in a competitive market',
            'We see competitive dynamics as broadly unchanged',
        ],
        'UNIT_ECONOMICS_FRAMING': [
            'Unit economics are adequate but no longer improving',
            'Unit economics sit in line with sector norms',
            'Unit economics are sound, with limited room for further leverage',
        ],
        'RISK_FRAMING': [
            'Upside and downside risks appear broadly symmetric',
            'We see offsetting risks in both directions',
            'The balance of risks keeps us on the sidelines',
        ],
        'RECOMMENDATION_LANGUAGE': [
            'We recommend holding existing positions',
            'We see no urgency to add or reduce',
            'We would await a better entry point',
        ],
        'CATALYST_FRAMING': [
            'We see no near-term catalyst to change the valuation',
            'Catalysts appear balanced between upside and downside',
        ],
    },
    'bear': {
        'THESIS_STANCE': ['cautious', 'negative', 'guarded'],
        'THESIS_VERB': ['drives', 'underlies', 'explains'],
        'CONVICTION_PHRASE': [
            'We see an unfavourable risk/reward skew',
            'We believe consensus estimates remain too high',
            'We see further downside to current levels',
        ],
        'FUNDAMENTAL_FRAMING': [
            'faces mounting fundamental pressure',
            'is tracking behind our expectations',
            'shows deteriorating operating momentum',
        ],
        'COMPETITIVE_FRAMING': [
            "The company's competitive position is eroding",
            'Competitive intensity is compressing returns',
            'We see competitive advantage narrowing',
        ],
        'UNIT_ECONOMICS_FRAMING': [
            'Deteriorating unit economics underpin our cautious thesis',
            'Unit economics are weakening relative to peers',
            'Unit economics leave little margin for error',
        ],
        'RISK_FRAMING': [
            'We see material downside risk to consensus estimates',
            'The risks to our thesis are skewed to the downside',
            'We see limited valuation support if execution slips',
        ],
        'RECOMMENDATION_LANGUAGE': [
            'We recommend reducing exposure',
            'We would use any strength to exit positions',
            'We recommend underweighting the shares',
        ],
        'CATALYST_FRAMING': [
            'We see few catalysts to arrest the de-rating',
            'Near-term catalysts skew negative',
        ],
    },
}

# Lower bound of implied upside (as a fraction) for each rating, most bullish
# first. A stock that rallies into its target therefore drops a band on the next
# vintage, producing genuine rating actions.
RATING_UPSIDE_BANDS = [
    ('Strong Buy', 0.20),
    ('Buy', 0.08),
    ('Hold', -0.08),
    ('Sell', -0.20),
]

# Scenario and sizing inputs for research memos. These used to be sampled from
# generic numeric bounds, which let a memo print a bear case above its bull case
# or a positive "downside". They now derive from the same fair value as the
# rating, so a memo is internally consistent.
MEMO_VALUATION = {
    # Half-width of the bull/bear band around fair value.
    'scenario_spread': 0.18,
    # Notional book size used to turn a position weight into a dollar amount.
    'reference_aum_usd': 2_400_000_000,
    # Position weight by rating - conviction has to show up in the size, or a
    # Strong Sell memo recommends the same weight as a Strong Buy.
    'position_size_by_rating': {
        'Strong Buy': 4.0,
        'Buy': 2.5,
        'Hold': 1.5,
        'Sell': 0.5,
        'Strong Sell': 0.0,
    },
}

# Valuation inputs for fair value = forward_eps * base_pe * quality_adjustment
VALUATION = {
    'quality_adj_min': 0.8,
    'quality_adj_max': 1.3,
    'growth_weight': 0.8,
    'margin_weight': 0.4,
    'default_base_pe': 18.0,
    # Forward EPS growth is derived from real REVENUE_GROWTH_PCT, clamped so a
    # single distorted filing cannot produce an absurd target.
    'eps_growth_min': 0.90,
    'eps_growth_max': 1.30,
    # The raw fundamental fair value spans roughly 0.03x to 15x spot across the
    # universe, because market prices embed growth and non-GAAP adjustments that
    # trailing EPS times a sector PE does not capture. So the fundamental view is
    # used as a *signal* on top of spot rather than as an absolute price.
    #
    # The signal is compressed through TANH rather than hard-clamped: a clamp
    # plateaus (69% of the universe pegged at the cap, so only broker bias
    # differentiated them and ratings went bimodal), whereas TANH is smooth and
    # strictly monotonic, so every name keeps a distinct target and the full
    # fundamental ordering survives.
    #
    #     signal = scale * TANH(raw_signal / softness)
    #
    # scale bounds the fundamental contribution just below the Strong Buy
    # threshold, so reaching Strong Buy or Strong Sell requires the fundamental
    # view *and* a broker leaning the same way - which is what produces a
    # realistic sell-side spread on the same stock.
    'valuation_signal_scale': 0.22,
    'valuation_signal_softness': 0.8,
    # Plausibility clamps on the fundamental inputs. Revenue growth is derived
    # from consecutive annual revenues rather than read from
    # FACT_SEC_FINANCIALS.REVENUE_GROWTH_PCT, which is unreliable (median 82.8%,
    # max 273,736%, ~48% of rows implausible). These caps stop a restatement or a
    # tiny prior-year base from distorting a target or appearing in document text.
    'revenue_growth_cap_pct': 60.0,
    'operating_margin_cap_pct': 60.0,
    # Coverage tiers. Preferred basis is reported diluted EPS; where that is
    # missing or non-positive we fall back in order:
    #   1. reported_eps    - EPS_DILUTED > 0
    #   2. derived_eps     - NET_INCOME / SHARES_OUTSTANDING, when positive
    #   3. sales_multiple  - loss-making but has revenue, valued on an implied
    #                        price/sales derived from the sector PE and the
    #                        sector's real median net margin
    # Without tiers 2 and 3, 139 of 503 covered issuers get no rating at all -
    # including 67 loss-making names that real analysts do cover on sales.
    # Loss-making companies get a haircut: valuing them at the sector's median
    # margin implicitly assumes they reach profitability.
    'unprofitable_discount': 0.75,
    # Floor for the implied price/sales, so a sector whose median net margin is
    # ~0 (Real Estate, 2 issuers) cannot produce a zero fair value.
    'min_price_to_sales': 0.5,
    # Plausibility gate on fundamental fair value versus spot. Outside this
    # band the filing and the price are not on the same basis - almost always a
    # foreign private issuer reporting local currency against a USD listing - so
    # the name is excluded rather than given a confident but meaningless rating.
    # Calibrated on the real distribution: median fair value is 0.83x spot and
    # the 1st/99th percentiles are 0.001x and 18.6x. A ratio beyond 20x or below
    # 0.05x is not a valuation disagreement, it is a unit or currency error, and
    # 44 of 432 securities were silently in that state before this gate existed.
    'fv_ratio_min': 0.05,
    'fv_ratio_max': 20.0,
    # Per-broker jitter half-width applied on top of the persistent broker bias.
    'broker_jitter_pct': 0.06,
    # Tier 4, price_fallback: securities with a price but no usable fundamentals
    # (no clean annual filing, mixed-currency series, or outside the fv_ratio
    # gate). Signal = sector median calibrated signal + weight * trailing price
    # momentum over the lookback, momentum clamped to the min/max band.
    'price_fallback_lookback_days': 182,
    'price_fallback_momentum_weight': 0.5,
    'price_fallback_momentum_min': -0.6,
    'price_fallback_momentum_max': 1.0,
}

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

# Currency & Calendar
BASE_CURRENCY = 'USD'
TRADING_CALENDAR = 'UTC_BUSINESS_DAYS'

# =============================================================================
# CONTENT GENERATION CONFIGURATION
# =============================================================================

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


# =============================================================================
# AGENT EVALUATIONS — loaded from data/reference_data/evaluations.yaml
# =============================================================================
TOOL_SERVICE_MAP = REF_DATA['evaluations']['tool_service_map']
AGENT_EVALUATIONS = REF_DATA['evaluations']['agent_evaluations']

# =============================================================================
# END OF CONFIGURATION
# =============================================================================
