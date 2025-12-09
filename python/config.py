"""
Snowcrest Asset Management (SAM) Demo Configuration
All configuration constants for the SAM AI demo using CAPS naming convention.
"""

import os

# =============================================================================
# CORE SETTINGS
# =============================================================================

# Connection and execution
DEFAULT_CONNECTION_NAME = 'sfseeurope-mstellwall-aws-us-west3'
RNG_SEED = 42
YEARS_OF_HISTORY = 5
TEST_MODE_MULTIPLIER = 0.1

# =============================================================================
# DATABASE & WAREHOUSE CONFIGURATION
# =============================================================================

DATABASE = {
    'name': 'SAM_DEMO',
    'schemas': {
        'raw': 'RAW',
        'curated': 'CURATED',
        'ai': 'AI'
    }
}

# Helper function for table references
def get_table_path(schema: str, table: str) -> str:
    """Get fully qualified table path."""
    return f"{DATABASE['name']}.{DATABASE['schemas'][schema]}.{table}"

WAREHOUSES = {
    'execution': {
        'name': 'SAM_DEMO_WH',
        'size': 'MEDIUM',
        'comment': 'Warehouse for SAM demo operations'
    },
    'cortex_search': {
        'name': 'SAM_DEMO_WH',
        'size': 'MEDIUM',
        'target_lag': '5 minutes',
        'comment': 'Warehouse for SAM demo operations'
    }
}


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
    'portfolio_code_prefix': 'SAM'
}

# Securities configuration
SECURITIES = {
    'counts': {
        'equities': 10000,
        'bonds': 3000,
        'etfs': 1000
    },
    'real_assets_view': 'V_REAL_ASSETS',
    'sec_filings_database': 'MARKETPLACE_CYBERSYN',  # Created from Marketplace listing
    'sec_filings_schema': 'CYBERSYN'
}

# Helper function for test mode counts
def get_securities_count(test_mode: bool = False) -> dict:
    """Get securities count based on mode."""
    if test_mode:
        return {k: int(v * TEST_MODE_MULTIPLIER) for k, v in SECURITIES['counts'].items()}
    return SECURITIES['counts']

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
        'applicable_portfolios': ['SAM ESG Leaders Global Equity', 'SAM Renewable & Climate Solutions']
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
        'guaranteed_top_holdings': [
            {'ticker': 'AAPL', 'openfigi_id': 'BBG001S5N8V8', 'order': 1, 'position_size': 'large'},
            {'ticker': 'CMC', 'openfigi_id': 'BBG001S5PXG8', 'order': 2, 'position_size': 'large'},
            {'ticker': 'RBBN', 'openfigi_id': 'BBG00HW4CSH5', 'order': 3, 'position_size': 'large'}
        ],
        'additional_holdings': [
            {'ticker': 'MSFT', 'openfigi_id': 'BBG001S5TD05'},
            {'ticker': 'NVDA', 'openfigi_id': 'BBG001S5TZJ6'},
            {'ticker': 'GOOGL', 'openfigi_id': 'BBG009S39JY5'}
        ],
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
# DEMO SCENARIO CONFIGURATION
# =============================================================================

DEMO_COMPANIES = {
    'AAPL': {
        'openfigi_id': 'BBG001S5N8V8',
        'ticker': 'AAPL',
        'company_name': 'Apple Inc.',
        'country': 'US',
        'sector': 'Information Technology',
        'priority': 1
    },
    'CMC': {
        'openfigi_id': 'BBG001S5PXG8',
        'ticker': 'CMC',
        'company_name': 'Commercial Metals Co',
        'country': 'US',
        'sector': 'Materials',
        'priority': 2
    },
    'RBBN': {
        'openfigi_id': 'BBG00HW4CSH5',
        'ticker': 'RBBN',
        'company_name': 'Ribbon Communications Inc.',
        'country': 'US',
        'sector': 'Information Technology',
        'priority': 3
    },
    'MSFT': {
        'openfigi_id': 'BBG001S5TD05',
        'ticker': 'MSFT',
        'company_name': 'Microsoft Corp',
        'country': 'US',
        'sector': 'Information Technology',
        'priority': 4
    },
    'NVDA': {
        'openfigi_id': 'BBG001S5TZJ6',
        'ticker': 'NVDA',
        'company_name': 'NVIDIA Corp',
        'country': 'US',
        'sector': 'Information Technology',
        'priority': 4
    },
    'GOOGL': {
        'openfigi_id': 'BBG009S39JY5',
        'ticker': 'GOOGL',
        'company_name': 'Alphabet Inc.',
        'country': 'US',
        'sector': 'Communication Services',
        'priority': 4
    },
    'TSM': {
        'openfigi_id': 'BBG001S5WWW4',  # Taiwan Semiconductor ADR
        'ticker': 'TSM',
        'company_name': 'Taiwan Semiconductor Manufacturing Company Ltd',
        'country': 'TW',
        'sector': 'Information Technology',
        'priority': 4  # Same priority as NVDA/MSFT for demo scenarios
    }
}

MAJOR_US_STOCKS = {
    'tier1': ['AMZN', 'TSLA', 'META', 'NFLX', 'CRM', 'ORCL'],
    'tier2': ['CSCO', 'IBM', 'INTC', 'AMD', 'ADBE', 'NOW', 'INTU', 'MU', 'QCOM', 'AVGO', 'TXN', 'LRCX', 'KLAC', 'AMAT', 'MRVL']
}

# =============================================================================
# MANDATE COMPLIANCE CONFIGURATION (for Scenario 3.2)
# =============================================================================

# Mandate compliance demo scenario configuration
SCENARIO_3_2_MANDATE_COMPLIANCE = {
    'portfolio': 'SAM AI & Digital Innovation',
    'non_compliant_holding': {
        'ticker': 'META',
        'openfigi_id': 'BBG00DQ6WPS6',  # Meta Platforms Inc. (Facebook)
        'issue': 'ESG_DOWNGRADE',
        'original_esg_grade': 'A',
        'downgraded_esg_grade': 'BBB',
        'reason': 'Governance concerns related to data privacy practices',
        'action_deadline_days': 30  # Days from alert to resolution deadline
    },
    'pre_screened_replacements': [
        {
            'ticker': 'NVDA',
            'openfigi_id': 'BBG001S5TZJ6',
            'rank': 1,
            'ai_growth_score': 92,
            'esg_grade': 'A',
            'market_cap_b': 1200,
            'liquidity_score': 10,
            'rationale': 'Leader in AI compute infrastructure with dominant data center GPU market share, strong ESG governance, and robust patent portfolio in machine learning accelerators'
        },
        {
            'ticker': 'MSFT',
            'openfigi_id': 'BBG001S5TD05',
            'rank': 2,
            'ai_growth_score': 89,
            'esg_grade': 'A',
            'market_cap_b': 2800,
            'liquidity_score': 10,
            'rationale': 'Azure AI platform leader with OpenAI partnership, excellent ESG track record, and significant investment in responsible AI development'
        },
        {
            'ticker': 'GOOGL',
            'openfigi_id': 'BBG009S39JY5',
            'rank': 3,
            'ai_growth_score': 85,
            'esg_grade': 'A',
            'market_cap_b': 1700,
            'liquidity_score': 10,
            'rationale': 'AI research leader with DeepMind and Google Brain, solid ESG performance though some historical privacy concerns addressed'
        }
    ],
    'mandate_requirements': {
        'min_esg_grade': 'A',
        'max_concentration': 0.065,  # 6.5% for this portfolio
        'required_sector': 'Information Technology',
        'ai_growth_threshold': 80,
        'min_market_cap_b': 50,
        'min_liquidity_score': 7
    }
}

# =============================================================================
# SUPPLY CHAIN CONFIGURATION (for Risk Verification scenario)
# =============================================================================

# Supply chain demo companies for Taiwan earthquake scenario
SUPPLY_CHAIN_DEMO_COMPANIES = {
    # Taiwan semiconductor supplier (critical upstream)
    'TSM': {
        'openfigi_id': 'BBG001S5WWW4',  # Taiwan Semiconductor ADR (correct FIGI from real data)
        'ticker': 'TSM',
        'company_name': 'Taiwan Semiconductor Manufacturing Company Ltd',
        'country': 'TW',
        'sector': 'Information Technology',
        'relationship_type': 'supplier',  # upstream supplier
        'priority': 1
    },
    # US tech companies (downstream customers)
    'NVDA': {
        'openfigi_id': 'BBG001S5TZJ6',
        'ticker': 'NVDA',
        'company_name': 'NVIDIA Corp',
        'country': 'US',
        'sector': 'Information Technology',
        'relationship_type': 'customer',  # downstream customer of TSM
        'priority': 2
    },
    'AMD': {
        'openfigi_id': 'BBG000BBQCY0',
        'ticker': 'AMD',
        'company_name': 'Advanced Micro Devices Inc',
        'country': 'US',
        'sector': 'Information Technology',
        'relationship_type': 'customer',  # downstream customer of TSM
        'priority': 2
    },
    'AAPL': {
        'openfigi_id': 'BBG001S5N8V8',
        'ticker': 'AAPL',
        'company_name': 'Apple Inc.',
        'country': 'US',
        'sector': 'Information Technology',
        'relationship_type': 'customer',  # downstream customer of TSM
        'priority': 2
    },
    # Automotive companies (second-order downstream)
    'GM': {
        'openfigi_id': 'BBG000NDYB67',
        'ticker': 'GM',
        'company_name': 'General Motors Co',
        'country': 'US',
        'sector': 'Consumer Discretionary',
        'relationship_type': 'customer',  # downstream customer of chip makers
        'priority': 3
    },
    'F': {
        'openfigi_id': 'BBG000BQPC32',
        'ticker': 'F',
        'company_name': 'Ford Motor Co',
        'country': 'US',
        'sector': 'Consumer Discretionary',
        'relationship_type': 'customer',  # downstream customer of chip makers
        'priority': 3
    }
}

# Supply chain relationship patterns for demo scenario
# Format: (Company, Counterparty, RelationshipType, CostShare/RevenueShare, CriticalityTier)
SUPPLY_CHAIN_DEMO_RELATIONSHIPS = [
    # Taiwan semiconductor → US tech companies (high dependency)
    ('TSM', 'NVDA', 'Customer', 0.25, 'High'),      # NVDA gets 25% revenue from TSM
    ('TSM', 'AMD', 'Customer', 0.18, 'High'),       # AMD gets 18% revenue from TSM
    ('TSM', 'AAPL', 'Customer', 0.30, 'High'),      # AAPL gets 30% revenue from TSM
    
    # US tech companies → automotive (medium dependency)
    ('NVDA', 'GM', 'Customer', 0.08, 'Medium'),     # GM gets 8% chips from NVDA
    ('NVDA', 'F', 'Customer', 0.06, 'Medium'),      # Ford gets 6% chips from NVDA
    ('AMD', 'GM', 'Customer', 0.05, 'Medium'),      # GM gets 5% chips from AMD
]

# Relationship strength ranges by industry
SUPPLY_CHAIN_RELATIONSHIP_STRENGTHS = {
    'semiconductors': {
        'critical_suppliers_share': (0.20, 0.40),   # 20-40% per critical supplier
        'major_customers_share': (0.15, 0.30),      # 15-30% per major customer
        'relationship_count_range': (5, 10)          # 5-10 relationships per company
    },
    'automotive': {
        'critical_suppliers_share': (0.10, 0.20),
        'major_customers_share': (0.08, 0.15),
        'relationship_count_range': (3, 5)
    },
    'technology': {
        'critical_suppliers_share': (0.15, 0.30),
        'major_customers_share': (0.10, 0.25),
        'relationship_count_range': (4, 8)
    },
    'default': {
        'critical_suppliers_share': (0.05, 0.15),
        'major_customers_share': (0.05, 0.12),
        'relationship_count_range': (1, 3)
    }
}

# Traversal settings for multi-hop exposure calculation
SUPPLY_CHAIN_TRAVERSAL = {
    'decay_rate': 0.50,        # 50% decay per hop
    'max_depth': 2,            # Maximum 2 hops
    'min_display_threshold': 0.05,  # Display if ≥5% post-decay exposure
    'high_dependency_threshold': 0.20  # Flag as High if ≥20% post-decay exposure
}

# =============================================================================
# SCENARIO & AGENT CONFIGURATION
# =============================================================================

AVAILABLE_SCENARIOS = [
    'portfolio_copilot',
    'research_copilot',
    'thematic_macro_advisor',
    'esg_guardian',
    'sales_advisor',
    'quant_analyst',
    'compliance_advisor',
    'middle_office_copilot'
]

# Scenario to agent mapping with descriptions
SCENARIO_AGENTS = {
    'portfolio_copilot': {
        'agent_name': 'AM_portfolio_copilot',
        'display_name': 'Portfolio Co-Pilot',
        'description': 'Portfolio analytics and benchmarking'
    },
    'research_copilot': {
        'agent_name': 'AM_research_copilot',
        'display_name': 'Research Co-Pilot',
        'description': 'Document research and analysis'
    },
    'thematic_macro_advisor': {
        'agent_name': 'AM_thematic_macro_advisor',
        'display_name': 'Thematic Macro Advisor',
        'description': 'Thematic investment strategy'
    },
    'esg_guardian': {
        'agent_name': 'AM_esg_guardian',
        'display_name': 'ESG Guardian',
        'description': 'ESG risk monitoring'
    },
    'compliance_advisor': {
        'agent_name': 'AM_compliance_advisor',
        'display_name': 'Compliance Advisor',
        'description': 'Mandate monitoring'
    },
    'sales_advisor': {
        'agent_name': 'AM_sales_advisor',
        'display_name': 'Sales Advisor',
        'description': 'Client reporting'
    },
    'quant_analyst': {
        'agent_name': 'AM_quant_analyst',
        'display_name': 'Quant Analyst',
        'description': 'Factor analysis'
    },
    'middle_office_copilot': {
        'agent_name': 'AM_middle_office_copilot',
        'display_name': 'Middle Office Co-Pilot',
        'description': 'Operations monitoring and NAV calculation'
    }
}

SCENARIO_DATA_REQUIREMENTS = {
    'portfolio_copilot': ['broker_research', 'earnings_transcripts', 'press_releases', 'macro_events', 'report_templates'],
    'research_copilot': ['broker_research', 'earnings_transcripts'],
    'thematic_macro_advisor': ['broker_research', 'press_releases'],
    'esg_guardian': ['ngo_reports', 'engagement_notes', 'policy_docs'],
    'sales_advisor': ['sales_templates', 'philosophy_docs', 'policy_docs'],
    'quant_analyst': ['broker_research', 'earnings_transcripts'],
    'compliance_advisor': ['policy_docs', 'engagement_notes', 'form_adv', 'form_crs', 'regulatory_updates'],
    'middle_office_copilot': ['custodian_reports', 'reconciliation_notes', 'ssi_documents', 'ops_procedures'],
    'mandate_compliance': ['report_templates']  # Alias for portfolio_copilot mandate compliance mode
}

# =============================================================================
# DOCUMENT GENERATION CONFIGURATION
# =============================================================================

# Paths
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
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
# EXECUTIVE NAMES CONFIGURATION (for earnings transcripts)
# =============================================================================

# Realistic executive names for deterministic generation in earnings transcripts
EXECUTIVE_NAMES = {
    'ceo': {
        'first_names': [
            'Satya', 'Tim', 'Sundar', 'Lisa', 'Pat', 'Amy', 'Jensen', 'Mark', 'Andy', 'Mary',
            'Brian', 'Shantanu', 'Arvind', 'Thomas', 'Daniel', 'Sarah', 'Michael', 'Karen', 'David', 'Jennifer',
            'Robert', 'Susan', 'James', 'Patricia', 'John', 'Linda', 'William', 'Barbara', 'Richard', 'Elizabeth'
        ],
        'last_names': [
            'Nadella', 'Cook', 'Pichai', 'Su', 'Gelsinger', 'Hood', 'Huang', 'Zuckerberg', 'Jassy', 'Barra',
            'Chesky', 'Narayen', 'Krishna', 'Kurian', 'Ek', 'Friar', 'Rapino', 'Lynch', 'Solomon', 'Morgan',
            'Anderson', 'Thompson', 'Martinez', 'Garcia', 'Rodriguez', 'Wilson', 'Taylor', 'Moore', 'Jackson', 'White'
        ]
    },
    'cfo': {
        'first_names': [
            'Amy', 'Luca', 'Ruth', 'Dave', 'Safra', 'Brian', 'Colette', 'David', 'Kelly', 'Jason',
            'Melissa', 'Peter', 'Christine', 'James', 'Rebecca', 'Frank', 'Kathleen', 'Martin', 'Susan', 'Robert',
            'Matthew', 'Nancy', 'Christopher', 'Betty', 'Daniel', 'Helen', 'Paul', 'Sandra', 'Mark', 'Donna'
        ],
        'last_names': [
            'Hood', 'Maestri', 'Porat', 'Wehner', 'Catz', 'Olsavsky', 'Kress', 'Bozeman', 'Kramer', 'Child',
            'Fisher', 'Zaffino', 'McCarthy', 'Bell', 'Benzschawel', 'Milligan', 'Osberg', 'Whitehurst', 'Mahoney', 'Shanks',
            'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott'
        ]
    }
}

# Document generation volumes
DOCUMENT_GENERATION = {
    'security_level': {
        'demo_companies': 8,
        'docs_per_company': {
            'broker_research': 6,
            'internal_research': 1,
            'investment_memo': 1,
            'earnings_transcripts': {'demo': 8, 'additional': 6},
            'press_releases': 4
        }
    },
    'issuer_level': {
        'coverage': 8,
        'docs_per_issuer': {
            'ngo_reports': 2,
            'engagement_notes': 1
        }
    },
    'portfolio_level': {
        'portfolios': DEMO_PORTFOLIOS_WITH_DOCS,
        'docs_per_portfolio': {
            'ips': 1,
            'portfolio_review': 2
        }
    },
    'global': {
        'market_data': 1,
        'policy_docs': 3,
        'sales_templates': 2,
        'philosophy_docs': 3,
        'compliance_manual': 1,
        'risk_framework': 1,
        'form_adv': 1,
        'form_crs': 1,
        'regulatory_updates': 5,
        'macro_events': 1
    }
}

# Helper function for test mode document counts
def get_document_count(doc_type: str, category: str, test_mode: bool = False) -> int:
    """Get document count based on type and mode."""
    if category == 'security_level':
        base_count = DOCUMENT_GENERATION[category]['docs_per_company'].get(doc_type, 1)
        if isinstance(base_count, dict):
            base_count = base_count.get('demo', base_count.get('additional', 1))
    elif category == 'issuer_level':
        base_count = DOCUMENT_GENERATION[category]['docs_per_issuer'].get(doc_type, 1)
    elif category == 'portfolio_level':
        base_count = DOCUMENT_GENERATION[category]['docs_per_portfolio'].get(doc_type, 1)
    else:  # global
        base_count = DOCUMENT_GENERATION[category].get(doc_type, 1)
    
    if test_mode and base_count > 1:
        return max(1, int(base_count * TEST_MODE_MULTIPLIER))
    return base_count

DOCUMENT_TYPES = {
    'broker_research': {
        'table_name': 'BROKER_RESEARCH_RAW',
        'corpus_name': 'BROKER_RESEARCH_CORPUS',
        'search_service': 'SAM_BROKER_RESEARCH',
        'word_count_range': (700, 1200),
        'applies_to': 'securities',
        'linkage_level': 'security',
        'template_dir': 'security/broker_research',
        'variants_per_sector': 3,
        'coverage_count': 8
    },
    'internal_research': {
        'table_name': 'INTERNAL_RESEARCH_RAW',
        'corpus_name': 'INTERNAL_RESEARCH_CORPUS',
        'search_service': 'SAM_INTERNAL_RESEARCH',
        'word_count_range': (1500, 2500),
        'applies_to': 'securities',
        'linkage_level': 'security',
        'template_dir': 'security/internal_research',
        'variants_per_sector': 2,
        'coverage_count': 8
    },
    'investment_memo': {
        'table_name': 'INVESTMENT_MEMO_RAW',
        'corpus_name': 'INVESTMENT_MEMO_CORPUS',
        'search_service': 'SAM_INVESTMENT_MEMOS',
        'word_count_range': (1000, 1800),
        'applies_to': 'securities',
        'linkage_level': 'security',
        'template_dir': 'security/investment_memo',
        'variants_per_sector': 2,
        'coverage_count': 8
    },
    'earnings_transcripts': {
        'table_name': 'EARNINGS_TRANSCRIPTS_RAW',
        'corpus_name': 'EARNINGS_TRANSCRIPTS_CORPUS',
        'search_service': 'SAM_EARNINGS_TRANSCRIPTS',
        'word_count_range': (6000, 10000),
        'applies_to': 'securities',
        'linkage_level': 'security',
        'template_dir': 'security/earnings_transcripts',
        'masters_per_sector': 10,
        'coverage_count': 8,
        'transcripts_per_demo_company': 8,
        'transcripts_per_additional_company': 6
    },
    'press_releases': {
        'table_name': 'PRESS_RELEASES_RAW',
        'corpus_name': 'PRESS_RELEASES_CORPUS',
        'search_service': 'SAM_PRESS_RELEASES',
        'word_count_range': (250, 400),
        'applies_to': 'securities',
        'linkage_level': 'security',
        'template_dir': 'security/press_releases',
        'variants_per_sector': 3,
        'coverage_count': 8,
        'releases_per_company': 4
    },
    'ngo_reports': {
        'table_name': 'NGO_REPORTS_RAW',
        'corpus_name': 'NGO_REPORTS_CORPUS',
        'search_service': 'SAM_NGO_REPORTS',
        'word_count_range': (400, 800),
        'applies_to': 'issuers',
        'linkage_level': 'issuer',
        'template_dir': 'issuer/ngo_reports',
        'categories': ['environmental', 'social', 'governance'],
        'severity_levels': ['high', 'medium', 'low'],
        'coverage_count': 8,
        'reports_per_company': 2
    },
    'engagement_notes': {
        'table_name': 'ENGAGEMENT_NOTES_RAW',
        'corpus_name': 'ENGAGEMENT_NOTES_CORPUS',
        'search_service': 'SAM_ENGAGEMENT_NOTES',
        'word_count_range': (150, 300),
        'applies_to': 'issuers',
        'linkage_level': 'issuer',
        'template_dir': 'issuer/engagement_notes',
        'meeting_types': ['management_meeting', 'shareholder_call', 'site_visit'],
        'coverage_count': 8,
        'notes_per_company': 1
    },
    'ips': {
        'table_name': 'IPS_RAW',
        'corpus_name': 'IPS_CORPUS',
        'search_service': 'SAM_IPS_DOCUMENTS',
        'word_count_range': (1500, 2500),
        'applies_to': 'portfolios',
        'linkage_level': 'portfolio',
        'template_dir': 'portfolio/ips',
        'variants': ['conservative', 'moderate', 'aggressive'],
        'portfolios': DEMO_PORTFOLIOS_WITH_DOCS,
        'docs_per_portfolio': 1
    },
    'portfolio_review': {
        'table_name': 'PORTFOLIO_REVIEW_RAW',
        'corpus_name': 'PORTFOLIO_REVIEW_CORPUS',
        'search_service': 'SAM_PORTFOLIO_REVIEWS',
        'word_count_range': (1200, 2000),
        'applies_to': 'portfolios',
        'linkage_level': 'portfolio',
        'template_dir': 'portfolio/portfolio_review',
        'variants': ['positive_performance', 'negative_performance', 'mixed_performance'],
        'portfolios': DEMO_PORTFOLIOS_WITH_DOCS,
        'docs_per_portfolio': 2
    },
    'policy_docs': {
        'table_name': 'POLICY_DOCS_RAW',
        'corpus_name': 'POLICY_DOCS_CORPUS',
        'search_service': 'SAM_POLICY_DOCS',
        'word_count_range': (800, 1500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/policy_docs',
        'policy_types': [
            'concentration_risk_policy',
            'sustainable_investment_policy',
            'investment_management_agreement'
        ],
        'docs_total': 3
    },
    'sales_templates': {
        'table_name': 'SALES_TEMPLATES_RAW',
        'corpus_name': 'SALES_TEMPLATES_CORPUS',
        'search_service': 'SAM_SALES_TEMPLATES',
        'word_count_range': (800, 1500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/sales_templates',
        'template_types': ['monthly_client_report', 'quarterly_client_letter'],
        'docs_total': 2
    },
    'philosophy_docs': {
        'table_name': 'PHILOSOPHY_DOCS_RAW',
        'corpus_name': 'PHILOSOPHY_DOCS_CORPUS',
        'search_service': 'SAM_PHILOSOPHY_DOCS',
        'word_count_range': (800, 1500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/philosophy_docs',
        'philosophy_types': ['esg_philosophy', 'risk_philosophy', 'brand_guidelines'],
        'docs_total': 3
    },
    'report_templates': {
        'table_name': 'REPORT_TEMPLATES_RAW',
        'corpus_name': 'REPORT_TEMPLATES_CORPUS',
        'search_service': 'SAM_REPORT_TEMPLATES',
        'word_count_range': (1500, 2500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/report_templates',
        'template_types': ['mandate_compliance', 'investment_decision', 'risk_assessment'],
        'docs_total': 1  # Start with just mandate compliance template
    },
    'market_data': {
        'table_name': 'MARKET_DATA_RAW',
        'corpus_name': 'MARKET_DATA_CORPUS',
        'search_service': 'SAM_MARKET_DATA',
        'word_count_range': (800, 1200),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/market_data',
        'regimes': ['risk_on', 'risk_off', 'mixed'],
        'docs_total': 1
    },
    'compliance_manual': {
        'table_name': 'COMPLIANCE_MANUAL_RAW',
        'corpus_name': 'COMPLIANCE_MANUAL_CORPUS',
        'search_service': 'SAM_COMPLIANCE_DOCS',
        'word_count_range': (3000, 5000),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/compliance_manual',
        'docs_total': 1
    },
    'risk_framework': {
        'table_name': 'RISK_FRAMEWORK_RAW',
        'corpus_name': 'RISK_FRAMEWORK_CORPUS',
        'search_service': 'SAM_RISK_DOCS',
        'word_count_range': (2000, 3500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/risk_framework',
        'docs_total': 1
    },
    'form_adv': {
        'table_name': 'FORM_ADV_RAW',
        'corpus_name': 'FORM_ADV_CORPUS',
        'search_service': 'SAM_REGULATORY_DOCS',
        'word_count_range': (3000, 6000),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'regulatory/form_adv',
        'docs_total': 1
    },
    'form_crs': {
        'table_name': 'FORM_CRS_RAW',
        'corpus_name': 'FORM_CRS_CORPUS',
        'search_service': 'SAM_REGULATORY_DOCS',
        'word_count_range': (500, 800),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'regulatory/form_crs',
        'docs_total': 1
    },
    'regulatory_updates': {
        'table_name': 'REGULATORY_UPDATES_RAW',
        'corpus_name': 'REGULATORY_UPDATES_CORPUS',
        'search_service': 'SAM_REGULATORY_DOCS',
        'word_count_range': (600, 1000),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'regulatory/regulatory_updates',
        'authorities': ['SEC', 'ESMA', 'FCA', 'IOSCO', 'MiFID_II'],
        'docs_total': 5
    },
    'macro_events': {
        'table_name': 'MACRO_EVENTS_RAW',
        'corpus_name': 'MACRO_EVENTS_CORPUS',
        'search_service': 'SAM_MACRO_EVENTS',
        'word_count_range': (400, 800),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/macro_events',
        'event_types': ['NaturalDisaster', 'Geopolitical', 'RegulatoryShock', 'CyberIncident', 'SupplyDisruption'],
        'regions': ['TW', 'US', 'CN', 'EU', 'JP'],
        'severity_levels': ['Low', 'Medium', 'High', 'Critical'],
        'affected_sectors': ['Information Technology', 'Consumer Discretionary', 'Industrials', 'Materials'],
        'docs_total': 1,  # Single Taiwan earthquake event for demo
        'demo_event': {
            'event_type': 'NaturalDisaster',
            'region': 'TW',
            'severity': 'Critical',
            'affected_sectors': ['Information Technology', 'Consumer Discretionary'],
            'title': 'Major Earthquake Disrupts Taiwan Semiconductor Production',
            'impact_description': 'A 7.2 magnitude earthquake has struck central Taiwan, affecting major semiconductor manufacturing facilities including TSMC fabs. Production halts expected for 2-4 weeks with downstream supply chain impacts on global technology and automotive sectors.'
        }
    },
    'custodian_reports': {
        'table_name': 'CUSTODIAN_REPORTS_RAW',
        'corpus_name': 'CUSTODIAN_REPORTS_CORPUS',
        'search_service': 'SAM_CUSTODIAN_REPORTS',
        'word_count_range': (500, 800),
        'applies_to': 'portfolios',
        'linkage_level': 'portfolio',
        'template_dir': 'portfolio/custodian_reports',
        'report_types': ['daily_holdings', 'cash_statement', 'transaction_summary'],
        'portfolios': DEMO_PORTFOLIOS_WITH_DOCS,
        'docs_per_portfolio': 3
    },
    'reconciliation_notes': {
        'table_name': 'RECONCILIATION_NOTES_RAW',
        'corpus_name': 'RECONCILIATION_NOTES_CORPUS',
        'search_service': 'SAM_RECONCILIATION_NOTES',
        'word_count_range': (200, 400),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/reconciliation_notes',
        'break_types': ['position_break', 'cash_break', 'price_break', 'corporate_action_break'],
        'docs_total': 8
    },
    'ssi_documents': {
        'table_name': 'SSI_DOCUMENTS_RAW',
        'corpus_name': 'SSI_DOCUMENTS_CORPUS',
        'search_service': 'SAM_SSI_DOCUMENTS',
        'word_count_range': (300, 600),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/ssi_documents',
        'instruction_types': ['equity_settlement', 'fx_settlement', 'bond_settlement'],
        'docs_total': 6
    },
    'ops_procedures': {
        'table_name': 'OPS_PROCEDURES_RAW',
        'corpus_name': 'OPS_PROCEDURES_CORPUS',
        'search_service': 'SAM_OPS_PROCEDURES',
        'word_count_range': (800, 1500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/ops_procedures',
        'procedure_types': ['settlement_failure_resolution', 'nav_calculation_process', 'reconciliation_workflow'],
        'docs_total': 3
    }
}

# =============================================================================
# MARKET & REFERENCE DATA CONFIGURATION
# =============================================================================

BENCHMARKS = [
    {'id': 'SP500', 'name': 'S&P 500', 'currency': 'USD', 'provider': 'PLM'},
    {'id': 'MSCI_ACWI', 'name': 'MSCI ACWI', 'currency': 'USD', 'provider': 'NSD'},
    {'id': 'NASDAQ100', 'name': 'Nasdaq 100', 'currency': 'USD', 'provider': 'PLM'}
]

# Provider configuration
PROVIDERS = ['NSD', 'PLM']  # NorthStar Data, PolarMetrics
PROVIDER_MIX = {'NSD': 0.5, 'PLM': 0.5}

# Factor definitions
EQUITY_FACTORS = ['Value', 'Quality', 'Momentum', 'Size', 'Low_Volatility', 'Growth']
FI_FACTORS = ['Duration', 'Credit_Spread', 'Carry']

# Data distribution
DATA_DISTRIBUTION = {
    'regions': {'US': 0.55, 'Europe': 0.30, 'APAC_EM': 0.15},
    'asset_classes': {'equities': 0.70, 'bonds': 0.20, 'etfs': 0.10},
    'bond_ratings': {'IG': 0.75, 'HY': 0.25},
    'bond_maturity': {'1-3y': 0.25, '3-7y': 0.45, '7-12y': 0.25, '12y+': 0.05}
}

# Currency & Calendar
BASE_CURRENCY = 'USD'
SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP']
FX_HEDGING = 'FULLY_HEDGED'
TRADING_CALENDAR = 'UTC_BUSINESS_DAYS'
RETURNS_FREQUENCY = 'MONTHLY'

# Language & Locale
CONTENT_LANGUAGE = 'en'
CONTENT_LOCALE = 'UK'

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

# Numeric tier by document type
NUMERIC_TIER_BY_DOC_TYPE = {
    'broker_research': 'tier1',
    'internal_research': 'tier1',
    'investment_memo': 'tier1',
    'earnings_transcripts': 'tier1',
    'press_releases': 'tier1',
    'ips': 'tier0',
    'portfolio_review': 'tier2',
    'ngo_reports': 'tier0',
    'engagement_notes': 'tier0',
    'market_data': 'tier1',
    'policy_docs': 'tier0',
    'sales_templates': 'tier0',
    'philosophy_docs': 'tier0',
    'compliance_manual': 'tier0',
    'risk_framework': 'tier0',
    'form_adv': 'tier0',
    'form_crs': 'tier0',
    'regulatory_updates': 'tier0'
}

# =============================================================================
# THEME CONFIGURATION
# =============================================================================

THEMES = ['On-Device AI', 'Renewable Energy Transition', 'Cybersecurity']

# =============================================================================
# SIMPLIFIED HELPER FUNCTIONS
# =============================================================================

def safe_sql_tuple(items: list, default_value: str = "'__NONE__'") -> str:
    """
    Convert a list to a SQL-safe tuple string with proper quoting.
    Returns a tuple with a dummy value if the list is empty to avoid SQL syntax errors.
    
    Args:
        items: List of items to convert to tuple
        default_value: Default value to use if list is empty (should be a SQL literal)
    
    Returns:
        String representation of tuple for SQL IN clause
    """
    if not items or len(items) == 0:
        return f"({default_value})"
    
    # Format items with SQL quotes
    quoted_items = [f"'{item}'" for item in items]
    # SQL doesn't use trailing comma for single items (unlike Python)
    return f"({', '.join(quoted_items)})"

def get_demo_company_figis(priority_group: str = 'all') -> list:
    """Get list of OpenFIGI IDs for demo scenario companies."""
    if priority_group == 'top3':
        companies = [c for c in DEMO_COMPANIES.values() if c['priority'] <= 3]
    elif priority_group == 'additional':
        companies = [c for c in DEMO_COMPANIES.values() if c['priority'] == 4]
    else:  # 'all'
        companies = DEMO_COMPANIES.values()
    return [company['openfigi_id'] for company in companies]

def get_demo_company_tickers(priority_group: str = 'all') -> list:
    """Get list of tickers for demo scenario companies."""
    if priority_group == 'top3':
        return [ticker for ticker, data in DEMO_COMPANIES.items() if data['priority'] <= 3]
    elif priority_group == 'additional':
        return [ticker for ticker, data in DEMO_COMPANIES.items() if data['priority'] == 4]
    else:  # 'all'
        return list(DEMO_COMPANIES.keys())

def get_major_us_stocks(tier: str = 'all') -> list:
    """Get list of major US stock tickers for portfolio diversification."""
    if tier == 'tier1':
        return MAJOR_US_STOCKS['tier1']
    elif tier == 'tier2':
        return MAJOR_US_STOCKS['tier2']
    else:  # 'all'
        return MAJOR_US_STOCKS['tier1'] + MAJOR_US_STOCKS['tier2']

def is_demo_portfolio(portfolio_name: str) -> bool:
    """Check if a portfolio is configured as a demo portfolio."""
    return portfolio_name in PORTFOLIOS and PORTFOLIOS[portfolio_name].get('is_demo_portfolio', False)

def get_demo_portfolio_names() -> list:
    """Get list of demo portfolio names only."""
    return [name for name, config in PORTFOLIOS.items() if config.get('is_demo_portfolio', False)]

def get_portfolio_holding_figis(portfolio_name: str, holding_type: str = 'all') -> list:
    """Get list of FIGIs for a portfolio's holdings."""
    portfolio_config = PORTFOLIOS.get(portfolio_name, {})
    if not portfolio_config.get('is_demo_portfolio', False):
        return []
    
    if holding_type == 'guaranteed':
        return [h['openfigi_id'] for h in portfolio_config.get('guaranteed_top_holdings', [])]
    elif holding_type == 'additional':
        return [h['openfigi_id'] for h in portfolio_config.get('additional_holdings', [])]
    else:  # 'all'
        guaranteed = [h['openfigi_id'] for h in portfolio_config.get('guaranteed_top_holdings', [])]
        additional = [h['openfigi_id'] for h in portfolio_config.get('additional_holdings', [])]
        return guaranteed + additional

def get_demo_company_priority_sql() -> str:
    """
    Generate SQL CASE statement for demo company priorities from DEMO_COMPANIES config.
    Returns SQL fragment that maps FIGI to priority value from config.
    """
    case_when_lines = []
    
    # Sort by priority to ensure consistent ordering
    sorted_companies = sorted(DEMO_COMPANIES.items(), key=lambda x: x[1]['priority'])
    
    for ticker, company_data in sorted_companies:
        figi = company_data['openfigi_id']
        priority = company_data['priority']
        case_when_lines.append(f"WHEN s.FIGI = '{figi}' THEN {priority}")
    
    if not case_when_lines:
        return "WHEN 1=0 THEN 999"  # Fallback if no demo companies
    
    return " ".join(case_when_lines)

def build_demo_portfolios_sql_mapping() -> dict:
    """Build SQL fragments for all demo portfolios from configuration."""
    all_guaranteed_figis = []
    all_additional_figis = []
    guaranteed_figis_to_order = {}
    
    for portfolio_name in get_demo_portfolio_names():
        portfolio_config = PORTFOLIOS[portfolio_name]
        
        for holding in portfolio_config.get('guaranteed_top_holdings', []):
            openfigi_id = holding['openfigi_id']
            order = holding['order']
            all_guaranteed_figis.append(openfigi_id)
            guaranteed_figis_to_order[openfigi_id] = order
        
        for holding in portfolio_config.get('additional_holdings', []):
            all_additional_figis.append(holding['openfigi_id'])
    
    guaranteed_case_when = []
    for figi, order in sorted(guaranteed_figis_to_order.items(), key=lambda x: x[1]):
        guaranteed_case_when.append(f"WHEN s.FIGI = '{figi}' THEN {order}")
    
    max_guaranteed_order = max(guaranteed_figis_to_order.values()) if guaranteed_figis_to_order else 0
    additional_priority = max_guaranteed_order + 1
    
    # Build SQL-safe tuple strings
    large_pos_figis = [
        h['openfigi_id'] 
        for name in get_demo_portfolio_names() 
        for h in PORTFOLIOS[name].get('guaranteed_top_holdings', [])
        if h.get('position_size') == 'large'
    ]
    
    return {
        'guaranteed_figis': safe_sql_tuple(list(set(all_guaranteed_figis))),
        'additional_figis': safe_sql_tuple(list(set(all_additional_figis))),
        'guaranteed_case_when_sql': " ".join(guaranteed_case_when) if guaranteed_case_when else "WHEN 1=0 THEN 1",
        'additional_priority': additional_priority,
        'large_position_figis': safe_sql_tuple(large_pos_figis)
    }

# =============================================================================
# END OF CONFIGURATION
# =============================================================================
