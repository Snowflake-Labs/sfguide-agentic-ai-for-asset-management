# Simulated Asset Management (SAM) Demo - Project Setup Rules

Project structure, configuration management, and setup procedures for the SAM AI demo.

## Project Overview

**Company**: Simulated Asset Management (SAM)  
**Purpose**: Demonstrate Snowflake Intelligence capabilities for asset management customers  
**Architecture**: Multi-asset investment management firm with 10 portfolios across growth, value, ESG, and thematic strategies

## Project Structure

```
/
├── .cursor/rules/              # Cursor AI development rules
│   ├── agent-config.mdc       # Agent configuration guide
│   ├── cortex-search.mdc      # Cortex Search creation guide
│   ├── data-generation.mdc    # Enhanced data generation patterns
│   ├── pipelines.mdc          # Production-like pipelines and Streamlit deployment
│   ├── project-setup.mdc      # Project setup and configuration
│   ├── semantic-views.mdc     # Semantic view creation guide (LEGACY - see docs/rules/semantic/)
│   ├── unstructured-data-generation.mdc # Document generation patterns
│   └── [other rules...]       # Additional development rules
├── content_library/            # Pre-generated content templates (50+ templates)
│   ├── _rules/                # Template configuration (placeholders, bounds, providers)
│   ├── security/              # Security-level document templates
│   ├── issuer/                # Issuer-level document templates
│   ├── portfolio/             # Portfolio-level document templates
│   ├── global/                # Global document templates
│   └── regulatory/            # Regulatory document templates
├── docs/                      # Documentation
│   ├── agents_setup.md       # Agent configuration instructions
│   ├── data_model.md         # Data model documentation
│   ├── data_lineage.md       # Data flow, dependencies, and impact analysis
│   ├── real_data_integration_analysis.md # Real SEC data integration
│   ├── demo_scenarios.md     # Demo conversation scripts
│   └── runbooks.md           # Operational procedures
├── python/                    # Python implementation
│   ├── config.py             # Configuration constants (CAPS naming)
│   ├── main.py               # CLI orchestrator
│   ├── generate_structured.py # Enhanced structured data generation (SecurityID model)
│   ├── generate_unstructured.py # Template-based document generation
│   ├── hydration_engine.py   # Template hydration engine
│   ├── build_ai.py           # AI orchestrator (builder.py)
│   ├── create_unstructured_pipelines.py # Production-like pipeline creation
│   └── portfolio_modelling.py # Portfolio modelling engines (backtest, simulation)
├── sql/                       # SQL artifacts for demo display
│   └── pipelines/            # Pipeline SQL scripts (viewable in Snowsight)
├── streamlit_app/            # Streamlit application (Container runtime)
│   ├── app.py               # Main app entry point
│   ├── environment.yml      # Dependencies
│   └── pages/               # Multi-page app pages
├── research/                  # Research documents and analysis
│   └── [research files...]   # Industry research and model documentation
├── .gitignore                # Git ignore patterns
└── README.md                 # Quick setup guide
```

## Configuration Management

### Primary Configuration: `python/config.py`
All configuration uses structured objects following clean architecture principles:

```python
# Core settings
DEFAULT_CONNECTION_NAME = 'sfseeurope-mstellwall-aws-us-west3'
RNG_SEED = 42
YEARS_OF_HISTORY = 5

# Database configuration
DATABASE = {
    'name': 'SAM_DEMO',
    'schemas': {'raw': 'RAW', 'curated': 'CURATED', 'market_data': 'MARKET_DATA', 'ai': 'AI'}
}

# Warehouse configuration  
WAREHOUSES = {
    'execution': {
        'name': 'SAM_DEMO_EXECUTION_WH',
        'size': 'MEDIUM'
    },
    'cortex_search': {
        'name': 'SAM_DEMO_CORTEX_WH',
        'size': 'MEDIUM',
        'target_lag': '5 minutes'
    }
}

# Data model configuration
DATA_MODEL = {
    'use_transaction_based': True,
    'generate_corporate_hierarchies': True,
    'issuer_hierarchy_depth': 2,
    'transaction_months': 12,
    'transaction_types': ['BUY', 'SELL', 'DIVIDEND', 'CORPORATE_ACTION'],
    'avg_monthly_transactions_per_security': 2.5,
    'portfolio_code_prefix': 'SAM'
}

# DEMO_COMPANIES - Single source of truth for company data (~76 companies)
DEMO_COMPANIES = {
    'AAPL': {'company_name': 'APPLE INC.', 'cik': '0000320193', 'tier': 'core'},
    'MSFT': {'company_name': 'MICROSOFT CORP', 'cik': '0000789019', 'tier': 'core'},
    # ... 8 core + 36 major + 32 additional companies
}

# External data sources
REAL_DATA_SOURCES = {
    'database': 'SNOWFLAKE_PUBLIC_DATA_FREE',
    'schema': 'PUBLIC_DATA_FREE'
}

# Usage examples:
# config.DATABASE['name'] instead of config.DATABASE_NAME
# config.WAREHOUSES['execution']['name'] instead of config.EXECUTION_WAREHOUSE
# config.get_demo_company_tickers(tier='core') for demo company access
```

### Connection Management
- Uses system default `~/.snowflake/connections.toml`
- Connection name configurable via CLI `--connection-name`
- Default connection: `sfseeurope-mstellwall-aws-us-west3`

### Warehouse Management
- **Execution Warehouse**: Accessed via `config.WAREHOUSES['execution']['name']`
- **Cortex Search Warehouse**: Accessed via `config.WAREHOUSES['cortex_search']['name']`
- **Size**: Configured in `config.WAREHOUSES[warehouse]['size']`
- **Auto-Management**: Both warehouses auto-suspend after 60 seconds, auto-resume when needed

## CLI Interface

### Main Command: `python/main.py`

**Core Parameters**:
- `--connection-name` (optional): Snowflake connection name
- `--scenarios` (optional): Comma-separated list of scenarios to build
- `--scope` (optional): `all|data|ai|semantic|search|agents|tools|streamlit` (default: `all`)
- `--verify-only` (optional): Validate semantic view YAML definitions without creating views
- `--extract-real-assets` (optional): Extract real asset data to CSV from SEC Filings dataset
- `--test-mode` (optional): Use 10% data volumes for faster development testing
- `--pipeline-setup` (default: True): Create production-like pipelines for unstructured data
- `--no-pipeline-setup` (optional): Skip pipeline creation

**Examples**:
```bash
# Build everything with defaults
python main.py

# Build all scenarios (same as above)
python main.py --scenarios all

# Build specific scenario (automatically includes all dependencies)
python main.py --scenarios portfolio_management

# Build multiple scenarios
python main.py --scenarios portfolio_management,research,private_equity

# Test mode: Build all scenarios with 10% data for faster development testing
python main.py --test-mode

# Build only semantic views
python main.py --scope semantic

# Validate YAML definitions without deploying
python main.py --scope semantic --verify-only

# Rebuild agents only
python main.py --scope agents
```

### Scenario Architecture

Scenarios are declared in `config.py` in the `SCENARIOS` dict — the single source of truth for all dependencies. Each scenario declares what tables, views, services, and tools it needs. The build pipeline resolves the union and builds in the correct order.

**Build order**: Tables -> SQL Views -> AI Objects (semantic views, search, tools, agents) -> Apps

**Available scenarios** (domain-based naming):
- Agent scenarios: `portfolio_management`, `research`, `risk_compliance`, `client_advisory`, `operations`, `executive_leadership`, `private_equity`, `private_credit`
- ML scenarios: `market_regime_ml`, `factor_workflow_ml`, `credit_risk_ml`

See `docs/rules/development-patterns.md` for the full guide on adding new scenarios.

### Test Mode for Development
**Purpose**: Faster builds during development and testing
**Usage**: `--test-mode` flag
**Data Reduction**: 10% of full data volumes (1,400 vs 14,000 securities, 205 vs 3,463 documents)
**Use Cases**: Code development, testing changes, validating functionality
**Performance**: Significantly faster build times while maintaining all functionality

## Database Architecture

**Database**: `SAM_DEMO`  
**Schemas**:
- `RAW`: External provider data simulation + raw unstructured documents
- `CURATED`: Industry-standard dimension/fact model ready for analysis
- `MARKET_DATA`: Real market data from SNOWFLAKE_PUBLIC_DATA_FREE
- `AI`: Semantic views and Cortex Search services

### Enhanced Data Model (Industry Standard)
```sql
-- Core Dimension Tables (CURATED)
DIM_ISSUER                    -- Corporate hierarchies and issuer relationships (with CIK linkage)
DIM_SECURITY                  -- Immutable SecurityID with TICKER column (derived from DIM_ISSUER)
DIM_PORTFOLIO                 -- Enhanced portfolio information
DIM_BENCHMARK                 -- Benchmark reference data

-- Core Fact Tables (CURATED)
FACT_TRANSACTION              -- Canonical transaction log (source of truth)
FACT_POSITION_DAILY_ABOR      -- ABOR positions built from transactions
FACT_ESG_SCORES              -- Monthly ESG ratings with sector differentiation
FACT_FACTOR_EXPOSURES        -- Monthly factor scores (Value, Growth, Quality, etc.)

-- Real Data Tables (MARKET_DATA) - NEW
FACT_STOCK_PRICES            -- 5.2M+ real daily stock prices from Nasdaq
FACT_FINANCIAL_DATA_SEC      -- 9,400+ real SEC financial metrics from 10-K/10-Q
FACT_SEC_FILING_TEXT         -- 6,300+ real SEC filing text (MD&A, Risk Factors)
FACT_SEC_FINANCIALS          -- Real SEC financials with calculated TAM/NRR metrics
FACT_ESTIMATE_CONSENSUS      -- Analyst estimates derived from real SEC actuals

-- Note: Company master is CURATED.DIM_ISSUER (no separate DIM_COMPANY table)

-- Enhanced Document Integration (CURATED)
{DOCUMENT_TYPE}_CORPUS        -- Documents linked via SecurityID and IssuerID
```

### Enhanced Capabilities (DEMO_COMPANIES Driven)
- **DEMO_COMPANIES as Single Source of Truth**: All 79 companies defined in `config.DEMO_COMPANIES` with tickers, CIKs, and tiers
- **Ticker-Based Identification**: Securities identified by TICKER (no external FIGI lookup dependency)
- **Immutable SecurityID**: Corporate action resilience and temporal integrity
- **Transaction Audit Trail**: Complete history for compliance and reconciliation
- **Issuer Hierarchies**: Real issuers with corporate structure relationships from DEMO_COMPANIES
- **Enhanced Document Integration**: Stable SecurityID/IssuerID linkage via DEMO_COMPANIES
- **Real SEC Data Integration**: Stock prices, financial metrics, and filing text from SNOWFLAKE_PUBLIC_DATA_FREE
- **Industry-Standard Architecture**: Professional asset management data model at scale

## Development Phases and Progress Tracking

### Current Implementation Status (Updated 2025-01-15)

#### ✅ **All 9 Agents: Automated SQL Creation Complete**
**Status**: All agents automatically created via `python/create_agents.py` using SQL `CREATE AGENT` statements
- ✅ **Automated Creation**: Agents created during `python main.py` build process
- ✅ **Agent Location**: Created in `{DATABASE['name']}.{DATABASE['schemas']['ai']}` schema (e.g., SAM_DEMO.AI)
- ✅ **Auto-Registration**: Automatically registered with Snowflake Intelligence after creation
- ✅ **Proper Formatting**: All instructions use YAML escaping (`\n`, `\"`, `''`)
- ✅ **Full Instructions**: Portfolio Manager Co-Pilot, Research Copilot, Investment Strategy use complete docs
- ✅ **Comprehensive Instructions**: Risk & Compliance, Sales Advisor, Investment Strategy, Middle Office Copilot, Executive Copilot fully specified
- ✅ **Immediate Availability**: Agents appear in Snowflake Intelligence UI after registration

#### ✅ **Phase 1: Foundation Complete** (portfolio_copilot) - **DEMO_COMPANIES Driven**
**Status**: Fully implemented and operational with 79 demo companies
- ✅ **DEMO_COMPANIES**: 79 companies defined in config with tickers, CIKs, sectors, and tiers
- ✅ **Ticker-Based Identification**: Securities derived from DIM_ISSUER using TICKER
- ✅ **Priority Holdings**: demo_order and position_size fields control portfolio construction
- ✅ Transaction-based holdings with config-driven prioritization (core/major/additional tiers)
- ✅ 15 Cortex Search services (broker_research, company_events, press_releases, etc.)
- ✅ 9 Semantic views (SAM_PORTFOLIO_VIEW, SAM_RESEARCH_VIEW, SAM_MARKET_VIEW, SAM_RESEARCH_VIEW, etc.)
- ✅ ESG scores with sector/regional differentiation (scaled to 14K securities)
- ✅ Factor exposures with sector-specific characteristics
- ✅ Benchmark holdings with realistic index compositions
- ✅ Real market data integration (4M+ records from SNOWFLAKE_PUBLIC_DATA_FREE)
- ✅ Demo flow alignment (portfolio holdings match research coverage)

#### ✅ **Phase 2: Research & Analytics** (COMPLETED - Agents Created)
**Status**: `research_copilot`, `investment_strategy` - Automatically created via SQL
- ✅ **research_copilot**: Full instructions from docs, uses broker research, earnings, fundamentals data
- ✅ **investment_strategy**: Full instructions from docs, uses broker research, press releases

#### ✅ **Phase 3: Risk & Compliance** (COMPLETED - Agents Created)
**Status**: `risk_compliance` - Automatically created via SQL
- ✅ **risk_compliance**: Comprehensive instructions, ESG-focused with severity flagging and mandate monitoring
- 🔄 **Document Enhancement** (Optional): Can add `ngo_reports`, `engagement_notes`, `policy_docs` for richer content

#### ✅ **Phase 4: Client & Quantitative** (COMPLETED - Agents Created)
**Status**: `sales_advisor`, `investment_strategy` - Automatically created via SQL
- ✅ **sales_advisor**: Comprehensive instructions, client-focused communication
- ✅ **investment_strategy**: Comprehensive instructions, factor analysis and attribution
- 🔄 **Document Enhancement** (Optional): Can add `sales_templates`, `philosophy_docs` for richer content

### Available Scenarios by Implementation Status

```python
SCENARIO_STATUS = {
    # All agents now automatically created via SQL
    'pm_cockpit': {
        'status': 'IMPLEMENTED',
        'agent_created': 'SQL_AUTO',
        'components': ['semantic_views', 'search_services', 'real_assets', 'transactions', 'esg', 'factors'],
        'agent_types': ['multi_tool_hybrid'],
        'last_tested': '2025-01-15'
    },
    
    'research_copilot': {
        'status': 'IMPLEMENTED',
        'agent_created': 'SQL_AUTO',
        'components': ['broker_research', 'company_event_transcripts', 'financial_analyzer'],
        'agent_types': ['search_focused', 'research_analyst'],
        'last_tested': '2025-01-15'
    },
    
    'investment_strategy': {
        'status': 'IMPLEMENTED',
        'agent_created': 'SQL_AUTO', 
        'components': ['broker_research', 'press_releases', 'quantitative_analyzer'],
        'agent_types': ['multi_search', 'thematic_analyst'],
        'last_tested': '2025-01-15'
    },
    
    'risk_compliance': {
        'status': 'IMPLEMENTED',
        'agent_created': 'SQL_AUTO',
        'components': ['quantitative_analyzer', 'esg_data'],
        'agent_types': ['compliance_focused', 'esg_analyst'],
        'enhancement_opportunities': ['ngo_reports', 'engagement_notes', 'policy_docs'],
        'last_tested': '2025-01-15'
    },
    
    'risk_compliance_compliance': {
        'status': 'IMPLEMENTED',
        'agent_created': 'SQL_AUTO',
        'components': ['quantitative_analyzer', 'policy_search'],
        'agent_types': ['compliance_engine', 'rule_validator'],
        'last_tested': '2025-01-15'
    },
    
    'sales_advisor': {
        'status': 'IMPLEMENTED',
        'agent_created': 'SQL_AUTO',
        'components': ['quantitative_analyzer', 'broker_research'],
        'agent_types': ['client_focused', 'presentation_builder'],
        'enhancement_opportunities': ['sales_templates', 'philosophy_docs'],
        'last_tested': '2025-01-15'
    },
    
    'investment_strategy_quant': {
        'status': 'IMPLEMENTED',
        'agent_created': 'SQL_AUTO',
        'components': ['quantitative_analyzer', 'factors', 'broker_research'],
        'agent_types': ['quantitative_analyst', 'model_explainer'],
        'last_tested': '2025-01-15'
    }
}
```

### Next Development Priorities

#### ✅ **All Agents Complete** - Focus on Enhancements

**Current State:**
- ✅ All 9 agents automatically created via SQL
- ✅ Full instructions for Portfolio Manager Co-Pilot, Research Copilot, Investment Strategy
- ✅ Comprehensive instructions for Risk & Compliance, Sales Advisor, Investment Strategy, Middle Office Copilot, Executive Copilot

**Optional Enhancements (Future Phases):**

1. **Document Enrichment** (Expand content coverage)
   - Add `ngo_reports` corpus for Risk & Compliance controversy monitoring
   - Add `engagement_notes` corpus for corporate engagement tracking
   - Add `policy_docs` corpus for compliance policy search
   - Add `sales_templates` corpus for client presentation materials
   - Add `philosophy_docs` corpus for investment philosophy explanations

2. **Semantic View Enhancements** (Additional analytics)
   - Create `SAM_RISK_VIEW` for dedicated risk analysis
   - Create `SAM_PERFORMANCE_VIEW` for attribution analysis
   - Expand `SAM_PORTFOLIO_VIEW` with additional risk metrics

3. **Demo Scenario Development** (Testing and refinement)
   - Test all 7 agents with realistic queries
   - Document successful query patterns
   - Create demo conversation scripts for each agent
   - Validate agent responses match expected behavior

## Prerequisites

### Required Setup
1. **Snowflake Account**: With Cortex features enabled and cross-region access
2. **Connection Configuration**: `~/.snowflake/connections.toml` properly configured
3. **Python Environment**: `snowflake-snowpark-python` installed

### Connection Configuration Template
```toml
[connections.sfseeurope-mstellwall-aws-us-west3]
account = "your-account"
user = "your-username"
password = "your-password"
warehouse = "your-warehouse"
database = "SAM_DEMO"
schema = "CURATED"
```

## Naming Standards and Reserved Keywords

### Reserved Keyword Compliance (VALIDATED)
Following [Snowflake reserved keywords](https://docs.snowflake.com/en/sql-reference/reserved-keywords):

**✅ All Object Names Verified Safe:**
- **Table Names**: DIM_SECURITY, DIM_ISSUER, FACT_POSITION_DAILY_ABOR, FACT_TRANSACTION, etc.
- **Column Names**: SecurityID, IssuerID, PRIMARYTICKER, LEGALNAME, GICS_SECTOR, etc.
- **Warehouse Names**: SAM_DEMO_EXECUTION_WH, SAM_DEMO_CORTEX_WH
- **AI Objects**: SAM_PORTFOLIO_VIEW, SAM_BROKER_RESEARCH, etc.

**Naming Conventions Used:**
- Underscore separation (PORTFOLIO_HOLDINGS not PORTFOLIO-HOLDINGS)
- Descriptive prefixes (SAM_DEMO_, SAM_)
- No reserved words as primary identifiers
- Consistent casing (UPPER_CASE for database objects)

### Reserved Keywords to Avoid
Critical keywords that cause issues:
- **Table/Column context**: TABLE, COLUMN, VIEW, SCHEMA, DATABASE
- **Query context**: SELECT, FROM, WHERE, ORDER, GROUP, SET
- **Expression context**: CASE, WHEN, TRUE, FALSE, NULL
- **Join context**: JOIN, LEFT, RIGHT, INNER, OUTER, CROSS

## Error Handling Standards

### Basic Error Management
- Try/catch blocks for all Snowflake operations
- Connection failure handling with clear error messages
- Missing data graceful handling (log warnings, continue processing)
- Validation checks before creating dependent objects

### Data Quality Checks
- Portfolio weights sum to 100% (±0.1% tolerance)
- Transaction log balances to position snapshots
- Security identifier integrity (TICKER column populated for all securities)
- Issuer hierarchy relationships valid
- No negative prices or market values
- Date ranges are consistent and logical
- All foreign key relationships exist

## Validation Standards

### Demo Readiness Checklist
- [ ] All enhanced foundation tables created successfully (DIM_SECURITY, FACT_TRANSACTION, etc.)
- [ ] Security identifier integrity validated (TICKER columns populated)
- [ ] Transaction log balances to ABOR positions
- [ ] Issuer hierarchies established with corporate relationships
- [ ] Semantic view responds to test queries with issuer-level support
- [ ] Cortex Search services return relevant results with SecurityID/IssuerID attributes
- [ ] Enhanced data quality checks pass
- [ ] Performance acceptable for demo purposes

### Required Test Queries
```sql
-- Test enhanced semantic view with issuer support
DESCRIBE SEMANTIC VIEW SAM_DEMO.AI.SAM_PORTFOLIO_VIEW;

-- Test basic portfolio analytics
SELECT * FROM SEMANTIC_VIEW(
    SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
    METRICS TOTAL_MARKET_VALUE, HOLDING_COUNT
    DIMENSIONS PORTFOLIONAME, DESCRIPTION
) LIMIT 5;

-- Test issuer-level analysis (enhanced capability)
SELECT * FROM SEMANTIC_VIEW(
    SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
    METRICS ISSUER_EXPOSURE
    DIMENSIONS LEGALNAME, GICS_SECTOR
) LIMIT 5;

-- Test enhanced search services with SecurityID attributes
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'SAM_DEMO.AI.SAM_BROKER_RESEARCH',
    '{"query": "technology investment", "limit": 2}'
);

-- Validate transaction-based model integrity
SELECT 
    COUNT(*) as transaction_count,
    COUNT(DISTINCT PortfolioID) as portfolios_with_transactions,
    COUNT(DISTINCT SecurityID) as securities_with_transactions
FROM SAM_DEMO.CURATED.FACT_TRANSACTION;
```

## Business Configuration Standards

### Benchmarks and Portfolio Rules
- **Benchmarks**: S&P 500, MSCI ACWI, Nasdaq 100
- **ESG Rules Apply To**: SAM ESG Leaders Global Equity; SAM Renewable & Climate Solutions
- **Compliance Rules**: 
  - Concentration: 7% cap, 6.5% warning threshold
  - Fixed Income: ≥75% Investment Grade, ≤5% CCC & below
  - ESG Floor: Minimum BBB rating for ESG-labelled portfolios

### Determinism and Analytics Standards
- **RNG Seed**: `RNG_SEED = 42` (configurable for consistent regeneration)
- **Base Currency**: USD for all analytics and reports
- **FX Hedging**: Fully hedged to USD for portfolios and benchmarks
- **Trading Calendar**: UTC with Mon-Fri business days
- **Returns Frequency**: Monthly for 5-year comparisons
- **Language**: UK English throughout generated content and agent responses

### Data Generation Defaults
- **Document Coverage**: Issuer-level for NGO/engagement, security-level for research
- **Identifier Management**: Deterministic hashing for stable IDs across runs
- **Overwrite Policy**: `CREATE OR REPLACE` for SQL objects, overwrite mode for DataFrames
- **Naming Standards**: Uppercase, unquoted identifiers compatible with Snowflake rules