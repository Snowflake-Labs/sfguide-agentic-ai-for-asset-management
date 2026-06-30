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
Scenario manifests - defines what each scenario needs for export.

Maps scenarios to their required tables, semantic views, and search services
based on the tools each agent uses.

TRACEABILITY:
- Each scenario maps to an agent in ai/agents.py
- Each agent's tool_resources section defines which semantic views and search services it uses
- For semantic views, trace to ai/semantic_views.py to find table dependencies
- For views (V_*), trace to data/structured.py to find underlying base tables
- For search services, trace to config.DOCUMENT_TYPES to find corpus tables

Key View Dependencies:
- V_HOLDINGS_WITH_ESG: FACT_POSITION_DAILY_ABOR + V_SECURITY_RETURNS + V_ESG_LATEST
- V_SECURITY_RETURNS: MARKET_DATA.FACT_STOCK_PRICES
- V_ESG_LATEST: FACT_ESG_SCORES
- V_PORTFOLIO_BENCHMARK_COMPARISON: V_HOLDINGS_WITH_ESG + FACT_BENCHMARK_PERFORMANCE
- V_MACRO_REGIME: MARKET_DATA.FACT_VIX_DAILY + MARKET_DATA.FACT_BENCHMARK_RETURNS

Custom Tools (procedures that need deployment):
- GENERATE_PDF_REPORT: Used by portfolio_copilot, research_copilot, esg_guardian, compliance_advisor, 
  sales_advisor, middle_office_copilot, executive_copilot
- MA_SIMULATION_TOOL: Used by executive_copilot
- RUN_BACKTEST_TOOL, RUN_MONTE_CARLO_TOOL, RUN_ATTRIBUTION_TOOL: Used by portfolio_modelling_copilot
- RUN_STRESS_BACKTEST_TOOL: Used by attribution_intelligence
"""

import config

SCENARIO_REQUIREMENTS = {
    # =========================================================================
    # PORTFOLIO_COPILOT
    # Agent: AM_portfolio_copilot (agents.py:1156)
    # Tool Resources:
    #   - quantitative_analyzer -> SAM_ANALYST_VIEW
    #   - financial_analyzer -> SAM_SEC_FINANCIALS_VIEW
    #   - implementation_analyzer -> SAM_IMPLEMENTATION_VIEW
    #   - supply_chain_analyzer -> SAM_SUPPLY_CHAIN_VIEW
    #   - stock_prices -> SAM_STOCK_PRICES_VIEW
    #   - sec_financials -> SAM_SEC_FINANCIALS_VIEW
    #   - search_broker_research -> SAM_BROKER_RESEARCH
    #   - search_company_events -> SAM_COMPANY_EVENTS
    #   - search_press_releases -> SAM_PRESS_RELEASES
    #   - search_macro_events -> SAM_MACRO_EVENTS
    #   - search_policies -> SAM_POLICY_DOCS
    #   - search_report_templates -> SAM_REPORT_TEMPLATES
    #   - search_ips_documents -> SAM_IPS_DOCS
    #   - search_sec_filings -> SAM_REAL_SEC_FILINGS
    #   - pdf_generator -> GENERATE_PDF_REPORT procedure
    # =========================================================================
    'portfolio_copilot': {
        'tables': {
            'CURATED': [
                # SAM_ANALYST_VIEW tables (semantic_views.py:110-148)
                'DIM_PORTFOLIO', 'DIM_SECURITY', 'DIM_ISSUER', 'DIM_BENCHMARK',
                'FACT_FACTOR_EXPOSURES', 'FACT_BENCHMARK_HOLDINGS', 'FACT_BENCHMARK_PERFORMANCE',
                # V_HOLDINGS_WITH_ESG dependencies (structured.py:1440)
                'FACT_POSITION_DAILY_ABOR', 'FACT_ESG_SCORES',
                # V_PORTFOLIO_BENCHMARK_COMPARISON (structured.py:2604)
                'V_HOLDINGS_WITH_ESG', 'V_PORTFOLIO_BENCHMARK_COMPARISON', 
                'V_SECURITY_RETURNS', 'V_ESG_LATEST',
                # SAM_IMPLEMENTATION_VIEW tables (semantic_views.py:271-314)
                'FACT_TRANSACTION_COSTS', 'FACT_PORTFOLIO_LIQUIDITY', 'FACT_RISK_LIMITS',
                'FACT_TRADING_CALENDAR', 'DIM_CLIENT_MANDATES', 'FACT_TAX_IMPLICATIONS',
                'FACT_TRADE_SETTLEMENT',
                # SAM_SUPPLY_CHAIN_VIEW tables (semantic_views.py:400-410)
                'DIM_SUPPLY_CHAIN_RELATIONSHIPS'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # V_SECURITY_RETURNS dependency (structured.py:1188)
                'FACT_STOCK_PRICES',
                # SAM_SEC_FINANCIALS_VIEW tables
                'FACT_SEC_FINANCIALS'
            ]
        },
        'semantic_views': [
            'SAM_ANALYST_VIEW', 'SAM_SEC_FINANCIALS_VIEW', 'SAM_IMPLEMENTATION_VIEW',
            'SAM_SUPPLY_CHAIN_VIEW', 'SAM_STOCK_PRICES_VIEW'
        ],
        'search_services': [
            'SAM_BROKER_RESEARCH', 'SAM_COMPANY_EVENTS', 'SAM_PRESS_RELEASES',
            'SAM_MACRO_EVENTS', 'SAM_POLICY_DOCS', 'SAM_REPORT_TEMPLATES',
            'SAM_IPS_DOCS', 'SAM_REAL_SEC_FILINGS'
        ],
        'corpus_tables': [
            'PDF_EXTERNAL_CORPUS', 'PDF_INTERNAL_CORPUS',
            'COMPANY_EVENT_TRANSCRIPTS_CORPUS'
        ],
        'custom_tools': ['GENERATE_PDF_REPORT']
    },
    
    # =========================================================================
    # RESEARCH_COPILOT
    # Agent: AM_research_copilot (agents.py:1347)
    # Tool Resources:
    #   - financial_analyzer -> SAM_SEC_FINANCIALS_VIEW
    #   - fundamentals_analyzer -> SAM_FUNDAMENTALS_VIEW
    #   - sec_financials -> SAM_SEC_FINANCIALS_VIEW
    #   - search_broker_research -> SAM_BROKER_RESEARCH
    #   - search_company_events -> SAM_COMPANY_EVENTS
    #   - search_press_releases -> SAM_PRESS_RELEASES
    #   - search_sec_filings -> SAM_REAL_SEC_FILINGS
    #   - pdf_generator -> GENERATE_PDF_REPORT procedure
    # =========================================================================
    'research_copilot': {
        'tables': {
            'CURATED': [
                # SAM_SEC_FINANCIALS_VIEW and SAM_FUNDAMENTALS_VIEW tables
                'DIM_ISSUER', 'DIM_SECURITY'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # SAM_SEC_FINANCIALS_VIEW
                'FACT_SEC_FINANCIALS',
                # SAM_FUNDAMENTALS_VIEW (analyst estimates, financials)
                'FACT_ANALYST_ESTIMATES', 'FACT_ANALYST_RATINGS'
            ]
        },
        'semantic_views': [
            'SAM_SEC_FINANCIALS_VIEW', 'SAM_FUNDAMENTALS_VIEW'
        ],
        'search_services': [
            'SAM_BROKER_RESEARCH', 'SAM_COMPANY_EVENTS', 'SAM_PRESS_RELEASES',
            'SAM_REAL_SEC_FILINGS'
        ],
        'corpus_tables': [
            'PDF_EXTERNAL_CORPUS', 'COMPANY_EVENT_TRANSCRIPTS_CORPUS'
        ],
        'custom_tools': ['GENERATE_PDF_REPORT']
    },
    
    # =========================================================================
    # THEMATIC_MACRO_ADVISOR
    # Agent: AM_thematic_macro_advisor (agents.py:1543)
    # Tool Resources:
    #   - quantitative_analyzer -> SAM_ANALYST_VIEW
    #   - search_broker_research -> SAM_BROKER_RESEARCH
    #   - search_company_events -> SAM_COMPANY_EVENTS
    #   - search_press_releases -> SAM_PRESS_RELEASES
    #   - search_macro_events -> SAM_MACRO_EVENTS
    #   - search_sec_filings -> SAM_REAL_SEC_FILINGS
    # =========================================================================
    'thematic_macro_advisor': {
        'tables': {
            'CURATED': [
                # SAM_ANALYST_VIEW tables (semantic_views.py:110-148)
                'DIM_PORTFOLIO', 'DIM_SECURITY', 'DIM_ISSUER', 'DIM_BENCHMARK',
                'FACT_FACTOR_EXPOSURES', 'FACT_BENCHMARK_HOLDINGS', 'FACT_BENCHMARK_PERFORMANCE',
                # V_HOLDINGS_WITH_ESG dependencies
                'FACT_POSITION_DAILY_ABOR', 'FACT_ESG_SCORES',
                'V_HOLDINGS_WITH_ESG', 'V_PORTFOLIO_BENCHMARK_COMPARISON', 
                'V_SECURITY_RETURNS', 'V_ESG_LATEST'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # V_SECURITY_RETURNS dependency
                'FACT_STOCK_PRICES'
            ]
        },
        'semantic_views': ['SAM_ANALYST_VIEW'],
        'search_services': [
            'SAM_BROKER_RESEARCH', 'SAM_COMPANY_EVENTS', 'SAM_PRESS_RELEASES',
            'SAM_MACRO_EVENTS', 'SAM_REAL_SEC_FILINGS'
        ],
        'corpus_tables': [
            'PDF_EXTERNAL_CORPUS', 'PDF_INTERNAL_CORPUS',
            'COMPANY_EVENT_TRANSCRIPTS_CORPUS'
        ],
        'custom_tools': []
    },
    
    # =========================================================================
    # ESG_GUARDIAN
    # Agent: AM_esg_guardian (agents.py:1622)
    # Tool Resources:
    #   - quantitative_analyzer -> SAM_ANALYST_VIEW
    #   - search_ngo_reports -> SAM_NGO_REPORTS
    #   - search_engagement_notes -> SAM_ENGAGEMENT_NOTES
    #   - search_policies -> SAM_POLICY_DOCS
    #   - search_press_releases -> SAM_PRESS_RELEASES
    #   - search_company_events -> SAM_COMPANY_EVENTS
    #   - search_sec_filings -> SAM_REAL_SEC_FILINGS
    #   - search_report_templates -> SAM_REPORT_TEMPLATES
    #   - pdf_generator -> GENERATE_PDF_REPORT procedure
    # =========================================================================
    'esg_guardian': {
        'tables': {
            'CURATED': [
                # SAM_ANALYST_VIEW tables
                'DIM_PORTFOLIO', 'DIM_SECURITY', 'DIM_ISSUER', 'DIM_BENCHMARK',
                'FACT_FACTOR_EXPOSURES', 'FACT_BENCHMARK_HOLDINGS', 'FACT_BENCHMARK_PERFORMANCE',
                # V_HOLDINGS_WITH_ESG dependencies
                'FACT_POSITION_DAILY_ABOR', 'FACT_ESG_SCORES',
                'V_HOLDINGS_WITH_ESG', 'V_PORTFOLIO_BENCHMARK_COMPARISON', 
                'V_SECURITY_RETURNS', 'V_ESG_LATEST'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # V_SECURITY_RETURNS dependency
                'FACT_STOCK_PRICES'
            ]
        },
        'semantic_views': ['SAM_ANALYST_VIEW'],
        'search_services': [
            'SAM_NGO_REPORTS', 'SAM_ENGAGEMENT_NOTES', 'SAM_POLICY_DOCS',
            'SAM_PRESS_RELEASES', 'SAM_COMPANY_EVENTS', 'SAM_REAL_SEC_FILINGS',
            'SAM_REPORT_TEMPLATES'
        ],
        'corpus_tables': [
            'PDF_EXTERNAL_CORPUS', 'PDF_INTERNAL_CORPUS',
            'COMPANY_EVENT_TRANSCRIPTS_CORPUS'
        ],
        'custom_tools': ['GENERATE_PDF_REPORT']
    },
    
    # =========================================================================
    # COMPLIANCE_ADVISOR
    # Agent: AM_compliance_advisor (agents.py:1747)
    # Tool Resources:
    #   - compliance_analyzer -> SAM_COMPLIANCE_VIEW
    #   - quantitative_analyzer -> SAM_ANALYST_VIEW
    #   - search_policies -> SAM_POLICY_DOCS
    #   - search_engagement_notes -> SAM_ENGAGEMENT_NOTES
    #   - search_report_templates -> SAM_REPORT_TEMPLATES
    #   - search_ips_documents -> SAM_IPS_DOCS
    #   - pdf_generator -> GENERATE_PDF_REPORT procedure
    # =========================================================================
    'compliance_advisor': {
        'tables': {
            'CURATED': [
                # SAM_COMPLIANCE_VIEW tables (semantic_views.py:655-670)
                'FACT_COMPLIANCE_ALERTS',
                # SAM_ANALYST_VIEW tables
                'DIM_PORTFOLIO', 'DIM_SECURITY', 'DIM_ISSUER', 'DIM_BENCHMARK',
                'FACT_FACTOR_EXPOSURES', 'FACT_BENCHMARK_HOLDINGS', 'FACT_BENCHMARK_PERFORMANCE',
                # V_HOLDINGS_WITH_ESG dependencies
                'FACT_POSITION_DAILY_ABOR', 'FACT_ESG_SCORES',
                'V_HOLDINGS_WITH_ESG', 'V_PORTFOLIO_BENCHMARK_COMPARISON', 
                'V_SECURITY_RETURNS', 'V_ESG_LATEST'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # V_SECURITY_RETURNS dependency
                'FACT_STOCK_PRICES'
            ]
        },
        'semantic_views': ['SAM_COMPLIANCE_VIEW', 'SAM_ANALYST_VIEW'],
        'search_services': [
            'SAM_POLICY_DOCS', 'SAM_ENGAGEMENT_NOTES', 'SAM_REPORT_TEMPLATES', 'SAM_IPS_DOCS'
        ],
        'corpus_tables': [
            'PDF_INTERNAL_CORPUS'
        ],
        'custom_tools': ['GENERATE_PDF_REPORT']
    },
    
    # =========================================================================
    # SALES_ADVISOR
    # Agent: AM_sales_advisor (agents.py:1855)
    # Tool Resources:
    #   - quantitative_analyzer -> SAM_ANALYST_VIEW
    #   - client_analyzer -> SAM_EXECUTIVE_VIEW
    #   - search_sales_templates -> SAM_SALES_TEMPLATES
    #   - search_philosophy_docs -> SAM_PHILOSOPHY_DOCS
    #   - search_policies -> SAM_POLICY_DOCS
    #   - pdf_generator -> GENERATE_PDF_REPORT procedure
    # =========================================================================
    'sales_advisor': {
        'tables': {
            'CURATED': [
                # SAM_ANALYST_VIEW tables
                'DIM_PORTFOLIO', 'DIM_SECURITY', 'DIM_ISSUER', 'DIM_BENCHMARK',
                'FACT_FACTOR_EXPOSURES', 'FACT_BENCHMARK_HOLDINGS', 'FACT_BENCHMARK_PERFORMANCE',
                # V_HOLDINGS_WITH_ESG dependencies
                'FACT_POSITION_DAILY_ABOR', 'FACT_ESG_SCORES',
                'V_HOLDINGS_WITH_ESG', 'V_PORTFOLIO_BENCHMARK_COMPARISON', 
                'V_SECURITY_RETURNS', 'V_ESG_LATEST',
                # SAM_EXECUTIVE_VIEW tables (semantic_views.py:740-779)
                'DIM_CLIENT', 'FACT_CLIENT_FLOWS', 'FACT_FUND_FLOWS', 'FACT_STRATEGY_PERFORMANCE'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # V_SECURITY_RETURNS dependency
                'FACT_STOCK_PRICES'
            ]
        },
        'semantic_views': ['SAM_ANALYST_VIEW', 'SAM_EXECUTIVE_VIEW'],
        'search_services': [
            'SAM_SALES_TEMPLATES', 'SAM_PHILOSOPHY_DOCS', 'SAM_POLICY_DOCS'
        ],
        'corpus_tables': [
            'PDF_INTERNAL_CORPUS'
        ],
        'custom_tools': ['GENERATE_PDF_REPORT']
    },
    
    # =========================================================================
    # QUANT_ANALYST
    # Agent: AM_quant_analyst (agents.py:1954)
    # Tool Resources:
    #   - quantitative_analyzer -> SAM_ANALYST_VIEW
    #   - financial_analyzer -> SAM_SEC_FINANCIALS_VIEW
    #   - search_broker_research -> SAM_BROKER_RESEARCH
    #   - search_company_events -> SAM_COMPANY_EVENTS
    #   - stock_prices -> SAM_STOCK_PRICES_VIEW
    # =========================================================================
    'quant_analyst': {
        'tables': {
            'CURATED': [
                # SAM_ANALYST_VIEW tables
                'DIM_PORTFOLIO', 'DIM_SECURITY', 'DIM_ISSUER', 'DIM_BENCHMARK',
                'FACT_FACTOR_EXPOSURES', 'FACT_BENCHMARK_HOLDINGS', 'FACT_BENCHMARK_PERFORMANCE',
                # V_HOLDINGS_WITH_ESG dependencies
                'FACT_POSITION_DAILY_ABOR', 'FACT_ESG_SCORES',
                'V_HOLDINGS_WITH_ESG', 'V_PORTFOLIO_BENCHMARK_COMPARISON', 
                'V_SECURITY_RETURNS', 'V_ESG_LATEST'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # V_SECURITY_RETURNS and SAM_STOCK_PRICES_VIEW dependency
                'FACT_STOCK_PRICES',
                # SAM_SEC_FINANCIALS_VIEW
                'FACT_SEC_FINANCIALS'
            ]
        },
        'semantic_views': [
            'SAM_ANALYST_VIEW', 'SAM_SEC_FINANCIALS_VIEW', 'SAM_STOCK_PRICES_VIEW'
        ],
        'search_services': ['SAM_BROKER_RESEARCH', 'SAM_COMPANY_EVENTS'],
        'corpus_tables': ['PDF_EXTERNAL_CORPUS', 'COMPANY_EVENT_TRANSCRIPTS_CORPUS'],
        'custom_tools': []
    },
    
    # =========================================================================
    # MIDDLE_OFFICE_COPILOT
    # Agent: AM_middle_office_copilot (agents.py:2029)
    # Tool Resources:
    #   - middle_office_analyzer -> SAM_MIDDLE_OFFICE_VIEW
    #   - search_custodian_reports -> SAM_CUSTODIAN_REPORTS
    #   - search_reconciliation_notes -> SAM_RECONCILIATION_NOTES
    #   - search_ssi_documents -> SAM_SSI_DOCUMENTS
    #   - search_ops_procedures -> SAM_OPS_PROCEDURES
    #   - pdf_generator -> GENERATE_PDF_REPORT procedure
    # =========================================================================
    'middle_office_copilot': {
        'tables': {
            'CURATED': [
                # SAM_MIDDLE_OFFICE_VIEW tables (semantic_views.py:503-546)
                'DIM_PORTFOLIO', 'DIM_SECURITY', 'DIM_CUSTODIAN', 'DIM_COUNTERPARTY',
                'FACT_TRADE_SETTLEMENT', 'FACT_RECONCILIATION', 'FACT_NAV_CALCULATION',
                'FACT_CORPORATE_ACTIONS', 'FACT_CASH_MOVEMENTS', 'FACT_CASH_POSITIONS'
            ],
            'RAW': [],
            'MARKET_DATA': []
        },
        'semantic_views': ['SAM_MIDDLE_OFFICE_VIEW'],
        'search_services': [
            'SAM_CUSTODIAN_REPORTS', 'SAM_RECONCILIATION_NOTES',
            'SAM_SSI_DOCUMENTS', 'SAM_OPS_PROCEDURES'
        ],
        'corpus_tables': [
            'PDF_INTERNAL_CORPUS'
        ],
        'custom_tools': ['GENERATE_PDF_REPORT']
    },
    
    # =========================================================================
    # EXECUTIVE_COPILOT
    # Agent: AM_executive_copilot (agents.py:2695)
    # Tool Resources:
    #   - executive_kpi_analyzer -> SAM_EXECUTIVE_VIEW
    #   - quantitative_analyzer -> SAM_ANALYST_VIEW
    #   - financial_analyzer -> SAM_SEC_FINANCIALS_VIEW
    #   - sec_segments_analyzer -> SAM_SEC_SEGMENTS_VIEW
    #   - implementation_analyzer -> SAM_IMPLEMENTATION_VIEW
    #   - search_strategy_docs -> SAM_STRATEGY_DOCUMENTS
    #   - search_press_releases -> SAM_PRESS_RELEASES
    #   - ma_simulation -> MA_SIMULATION_TOOL function
    #   - pdf_generator -> GENERATE_PDF_REPORT procedure
    # =========================================================================
    'executive_copilot': {
        'tables': {
            'CURATED': [
                # SAM_EXECUTIVE_VIEW tables (semantic_views.py:740-779)
                'DIM_CLIENT', 'DIM_PORTFOLIO', 'FACT_CLIENT_FLOWS', 'FACT_FUND_FLOWS',
                'FACT_STRATEGY_PERFORMANCE',
                # SAM_ANALYST_VIEW tables
                'DIM_SECURITY', 'DIM_ISSUER', 'DIM_BENCHMARK',
                'FACT_FACTOR_EXPOSURES', 'FACT_BENCHMARK_HOLDINGS', 'FACT_BENCHMARK_PERFORMANCE',
                # V_HOLDINGS_WITH_ESG dependencies
                'FACT_POSITION_DAILY_ABOR', 'FACT_ESG_SCORES',
                'V_HOLDINGS_WITH_ESG', 'V_PORTFOLIO_BENCHMARK_COMPARISON', 
                'V_SECURITY_RETURNS', 'V_ESG_LATEST',
                # SAM_IMPLEMENTATION_VIEW tables
                'FACT_TRANSACTION_COSTS', 'FACT_PORTFOLIO_LIQUIDITY', 'FACT_RISK_LIMITS',
                'FACT_TRADING_CALENDAR', 'DIM_CLIENT_MANDATES', 'FACT_TAX_IMPLICATIONS',
                'FACT_TRADE_SETTLEMENT'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # V_SECURITY_RETURNS dependency
                'FACT_STOCK_PRICES',
                # SAM_SEC_FINANCIALS_VIEW and SAM_SEC_SEGMENTS_VIEW
                'FACT_SEC_FINANCIALS'
            ]
        },
        'semantic_views': [
            'SAM_EXECUTIVE_VIEW', 'SAM_ANALYST_VIEW', 'SAM_SEC_FINANCIALS_VIEW',
            'SAM_SEC_SEGMENTS_VIEW', 'SAM_IMPLEMENTATION_VIEW'
        ],
        'search_services': [
            'SAM_STRATEGY_DOCUMENTS', 'SAM_PRESS_RELEASES'
        ],
        'corpus_tables': [
            'PDF_EXTERNAL_CORPUS', 'PDF_INTERNAL_CORPUS'
        ],
        'custom_tools': ['GENERATE_PDF_REPORT', 'MA_SIMULATION_TOOL']
    },
    
    # =========================================================================
    # PORTFOLIO_MODELLING_COPILOT
    # Agent: AM_portfolio_modelling_copilot (agents.py:3321)
    # Tool Resources:
    #   - portfolio_modelling_analyzer -> SAM_PORTFOLIO_MODELLING_VIEW
    #   - search_methodology_docs -> SAM_METHODOLOGY_DOCS
    #   - run_backtest -> RUN_BACKTEST_TOOL procedure
    #   - run_monte_carlo -> RUN_MONTE_CARLO_TOOL procedure
    #   - run_attribution -> RUN_ATTRIBUTION_TOOL procedure
    # =========================================================================
    'portfolio_modelling_copilot': {
        'tables': {
            'CURATED': [
                # SAM_PORTFOLIO_MODELLING_VIEW tables (semantic_views.py:1238-1273)
                'DIM_MODEL_PORTFOLIO', 'FACT_MODEL_PORTFOLIO_WEIGHTS',
                'DIM_SECURITY', 'DIM_ISSUER',
                'FACT_RISK_FACTORS', 'FACT_EXPECTED_RETURNS',
                'FACT_BACKTEST_RESULTS', 'FACT_SIMULATION_RESULTS'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # For backtesting price data
                'FACT_STOCK_PRICES'
            ]
        },
        'semantic_views': ['SAM_PORTFOLIO_MODELLING_VIEW'],
        'search_services': ['SAM_METHODOLOGY_DOCS'],
        'corpus_tables': ['PDF_INTERNAL_CORPUS'],
        'custom_tools': ['RUN_BACKTEST_TOOL', 'RUN_MONTE_CARLO_TOOL', 'RUN_ATTRIBUTION_TOOL']
    },
    
    # =========================================================================
    # PE_DEAL_SOURCING
    # Agent: AM_pe_deal_sourcing_copilot (agents.py:3802)
    # Tool Resources:
    #   - deal_pipeline_analyzer -> SAM_PE_DEAL_PIPELINE_VIEW
    #   - sec_financials_analyzer -> SAM_SEC_FINANCIALS_VIEW
    #   - search_due_diligence -> SAM_PE_DUE_DILIGENCE
    #   - search_expert_network -> SAM_PE_EXPERT_NETWORK
    #   - search_sec_filings -> SAM_REAL_SEC_FILINGS
    # =========================================================================
    'pe_deal_sourcing': {
        'tables': {
            'CURATED': [
                # SAM_PE_DEAL_PIPELINE_VIEW tables
                'DIM_PE_TARGET_COMPANY', 'FACT_PE_DEAL_PIPELINE',
                'FACT_PE_TARGET_FINANCIALS', 'FACT_PE_VALUE_DRIVERS'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # SAM_SEC_FINANCIALS_VIEW
                'FACT_SEC_FINANCIALS'
            ]
        },
        'semantic_views': ['SAM_PE_DEAL_PIPELINE_VIEW', 'SAM_SEC_FINANCIALS_VIEW'],
        'search_services': [
            'SAM_PE_DUE_DILIGENCE', 'SAM_PE_EXPERT_NETWORK', 'SAM_REAL_SEC_FILINGS'
        ],
        'corpus_tables': [
            'PE_DUE_DILIGENCE_CORPUS', 'PE_EXPERT_NETWORK_CORPUS'
        ],
        'custom_tools': []
    },
    
    # =========================================================================
    # PE_PORTFOLIO_MONITOR
    # Agent: AM_pe_portfolio_monitor (agents.py:3906)
    # Tool Resources:
    #   - value_creation_analyzer -> SAM_PE_VALUE_CREATION_VIEW
    #   - search_board_packs -> SAM_PE_BOARD_PACKS
    #   - search_expert_network -> SAM_PE_EXPERT_NETWORK
    # =========================================================================
    'pe_portfolio_monitor': {
        'tables': {
            'CURATED': [
                # SAM_PE_VALUE_CREATION_VIEW tables
                'DIM_PE_PORTFOLIO_COMPANY', 'FACT_PE_PORTFOLIO_KPI',
                'FACT_PE_VALUE_CREATION', 'FACT_PE_100_DAY_PLAN'
            ],
            'RAW': [],
            'MARKET_DATA': []
        },
        'semantic_views': ['SAM_PE_VALUE_CREATION_VIEW'],
        'search_services': ['SAM_PE_BOARD_PACKS', 'SAM_PE_EXPERT_NETWORK'],
        'corpus_tables': ['PE_BOARD_PACKS_CORPUS', 'PE_EXPERT_NETWORK_CORPUS'],
        'custom_tools': []
    },
    
    # =========================================================================
    # ATTRIBUTION_INTELLIGENCE
    # Agent: AM_attribution_intelligence (agents.py:3996)
    # Tool Resources:
    #   - brinson_analyzer -> SAM_BRINSON_ATTRIBUTION_VIEW
    #   - factor_analyzer -> SAM_FACTOR_ATTRIBUTION_VIEW
    #   - hidden_factor_analyzer -> SAM_HIDDEN_FACTORS_VIEW
    #   - macro_regime_analyzer -> SAM_MACRO_REGIME_VIEW
    #   - stress_scenario_analyzer -> SAM_STRESS_SCENARIOS_VIEW
    #   - historical_stress_analyzer -> SAM_HISTORICAL_STRESS_VIEW
    #   - global_macro_analyzer -> SAM_GLOBAL_MACRO_VIEW
    #   - backtest_historical_stress -> RUN_STRESS_BACKTEST_TOOL procedure
    # =========================================================================
    'attribution_intelligence': {
        'tables': {
            'CURATED': [
                # SAM_BRINSON_ATTRIBUTION_VIEW tables (semantic_views.py:1692-1707)
                'DIM_PORTFOLIO', 'FACT_BRINSON_ATTRIBUTION', 'FACT_BRINSON_BY_SECTOR',
                # SAM_FACTOR_ATTRIBUTION_VIEW tables (semantic_views.py:1738-1752)
                'FACT_FACTOR_ATTRIBUTION',
                # SAM_HIDDEN_FACTORS_VIEW tables (semantic_views.py:1769-1784)
                'FACT_HIDDEN_FACTOR_EXPOSURES',
                # SAM_MACRO_REGIME_VIEW tables (semantic_views.py:1802-1809)
                'V_MACRO_REGIME',
                # SAM_STRESS_SCENARIOS_VIEW tables
                'DIM_STRESS_SCENARIOS', 'FACT_SCENARIO_SHOCKS',
                # SAM_HISTORICAL_STRESS_VIEW tables
                'FACT_HISTORICAL_STRESS_PERIODS'
            ],
            'RAW': [],
            'MARKET_DATA': [
                # V_MACRO_REGIME dependencies (structured.py:6044-6067)
                'FACT_VIX_DAILY', 'FACT_BENCHMARK_RETURNS',
                # SAM_GLOBAL_MACRO_VIEW tables (semantic_views.py)
                'FACT_ECONOMIC_INDICATORS', 'FACT_FX_RATES', 'FACT_POLICY_RATES'
            ]
        },
        'semantic_views': [
            'SAM_BRINSON_ATTRIBUTION_VIEW', 'SAM_FACTOR_ATTRIBUTION_VIEW',
            'SAM_HIDDEN_FACTORS_VIEW', 'SAM_MACRO_REGIME_VIEW', 
            'SAM_STRESS_SCENARIOS_VIEW', 'SAM_HISTORICAL_STRESS_VIEW',
            'SAM_GLOBAL_MACRO_VIEW'
        ],
        'search_services': [],
        'corpus_tables': [],
        'custom_tools': ['RUN_STRESS_BACKTEST_TOOL']
    }
}


def get_requirements(scenario_name):
    """
    Get requirements for a scenario.
    
    Args:
        scenario_name: Name of scenario from config.AVAILABLE_SCENARIOS
        
    Returns:
        Dict with keys: tables, semantic_views, search_services, corpus_tables, custom_tools
        
    Raises:
        ValueError: If scenario is unknown
    """
    if scenario_name not in SCENARIO_REQUIREMENTS:
        available = ', '.join(SCENARIO_REQUIREMENTS.keys())
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {available}")
    return SCENARIO_REQUIREMENTS[scenario_name]


def get_all_scenarios():
    """Get list of all exportable scenarios."""
    return list(SCENARIO_REQUIREMENTS.keys())


def get_custom_tools(scenario_name):
    """Get list of custom tools/procedures needed for a scenario."""
    reqs = get_requirements(scenario_name)
    return reqs.get('custom_tools', [])
