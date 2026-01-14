# SAM Demo - Data Lineage and Dependencies

Data flows, object dependencies, and impact analysis for the SAM demo environment.

## Overview

This document maps dependencies between objects in the SAM demo to understand the impact of changes. Use this guide when modifying any component to understand downstream effects.

## Build Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SAM DEMO BUILD PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. DATABASE STRUCTURE                                                       │
│     └── main.py                                                              │
│         └── generate_structured.create_database_structure()                  │
│             ├── SAM_DEMO.RAW (schema)                                        │
│             ├── SAM_DEMO.CURATED (schema)                                    │
│             ├── SAM_DEMO.MARKET_DATA (schema)                                │
│             └── SAM_DEMO.AI (schema)                                         │
│                                                                              │
│  2. STRUCTURED DATA (generate_structured.py)                                 │
│     └── Foundation Tables (dependency order)                                 │
│         ├── DIM_ISSUER (from DEMO_COMPANIES config)                         │
│         ├── DIM_SECURITY                                                     │
│         ├── DIM_PORTFOLIO                                                    │
│         ├── DIM_BENCHMARK                                                    │
│         ├── DIM_SUPPLY_CHAIN_RELATIONSHIPS                                   │
│         ├── FACT_TRANSACTION                                                 │
│         ├── FACT_POSITION_DAILY_ABOR                                         │
│         ├── FACT_ESG_SCORES                                                  │
│         ├── FACT_FACTOR_EXPOSURES                                            │
│         ├── FACT_BENCHMARK_HOLDINGS                                          │
│         ├── Implementation Tables (transaction costs, liquidity, risk)       │
│         ├── Client/Executive Tables (DIM_CLIENT, flows, performance)         │
│         └── Middle Office Tables (settlement, reconciliation, NAV, cash)     │
│                                                                              │
│  3. MARKET DATA (generate_market_data.py)                                    │
│     ├── Reference Tables (always built)                                      │
│     │   ├── DIM_ANALYST                                                      │
│     │   ├── DIM_BROKER                                                       │
│     │   └── (Uses CURATED.DIM_ISSUER as company master - no DIM_COMPANY)     │
│     ├── Real Data (PRIMARY when REAL_DATA_SOURCES enabled)                   │
│     │   ├── FACT_SEC_FINANCIALS (with TAM, Customer Count, NRR)              │
│     │   ├── FACT_STOCK_PRICES                                                │
│     │   ├── FACT_FINANCIAL_DATA_SEC                                          │
│     │   └── FACT_SEC_FILING_TEXT                                             │
│     └── Derived Data (from FACT_SEC_FINANCIALS)                              │
│         ├── FACT_ESTIMATE_CONSENSUS (uses real SEC actuals)                  │
│         └── FACT_ESTIMATE_DATA                                               │
│                                                                              │
│  4. UNSTRUCTURED DATA (generate_unstructured.py)                             │
│     └── Document Types (parallel)                                            │
│         ├── RAW.*_RAW tables ──► CURATED.*_CORPUS tables                    │
│         │   ├── BROKER_RESEARCH_CORPUS                                       │
│         │   ├── PRESS_RELEASES_CORPUS                                        │
│         │   ├── NGO_REPORTS_CORPUS                                           │
│         │   ├── ENGAGEMENT_NOTES_CORPUS                                      │
│         │   ├── POLICY_DOCS_CORPUS                                           │
│         │   ├── SALES_TEMPLATES_CORPUS                                       │
│         │   ├── PHILOSOPHY_DOCS_CORPUS                                       │
│         │   ├── REPORT_TEMPLATES_CORPUS                                      │
│         │   ├── MACRO_EVENTS_CORPUS                                          │
│         │   ├── CUSTODIAN_REPORTS_CORPUS                                     │
│         │   ├── RECONCILIATION_NOTES_CORPUS                                  │
│         │   ├── SSI_DOCUMENTS_CORPUS                                         │
│         │   ├── OPS_PROCEDURES_CORPUS                                        │
│         │   └── STRATEGY_DOCUMENTS_CORPUS                                    │
│         └── Real Transcripts (generate_real_transcripts.py)                  │
│             └── COMPANY_EVENT_TRANSCRIPTS_CORPUS                             │
│                                                                              │
│  5. AI COMPONENTS (build_ai.py)                                              │
│     ├── Semantic Views (create_semantic_views.py)                            │
│     │   ├── SAM_ANALYST_VIEW (includes factor exposures and benchmarks)      │
│     │   ├── SAM_FUNDAMENTALS_VIEW                                            │
│     │   ├── SAM_IMPLEMENTATION_VIEW                                          │
│     │   ├── SAM_SUPPLY_CHAIN_VIEW                                            │
│     │   ├── SAM_MIDDLE_OFFICE_VIEW (includes corporate actions, cash)        │
│     │   ├── SAM_COMPLIANCE_VIEW                                              │
│     │   ├── SAM_EXECUTIVE_VIEW                                               │
│     │   ├── SAM_STOCK_PRICES_VIEW                                            │
│     │   └── SAM_SEC_FINANCIALS_VIEW                                          │
│     ├── Cortex Search Services (create_cortex_search.py)                     │
│     │   ├── SAM_BROKER_RESEARCH                                              │
│     │   ├── SAM_COMPANY_EVENTS                                               │
│     │   ├── SAM_PRESS_RELEASES                                               │
│     │   ├── SAM_NGO_REPORTS                                                  │
│     │   ├── SAM_ENGAGEMENT_NOTES                                             │
│     │   ├── SAM_POLICY_DOCS                                                  │
│     │   ├── SAM_SALES_TEMPLATES                                              │
│     │   ├── SAM_PHILOSOPHY_DOCS                                              │
│     │   ├── SAM_REPORT_TEMPLATES                                             │
│     │   ├── SAM_MACRO_EVENTS                                                 │
│     │   ├── SAM_CUSTODIAN_REPORTS                                            │
│     │   ├── SAM_RECONCILIATION_NOTES                                         │
│     │   ├── SAM_SSI_DOCUMENTS                                                │
│     │   ├── SAM_OPS_PROCEDURES                                               │
│     │   ├── SAM_STRATEGY_DOCUMENTS                                           │
│     │   └── SAM_REAL_SEC_FILINGS                                             │
│     └── Agents (create_agents.py)                                            │
│         ├── AM_portfolio_copilot                                             │
│         ├── AM_research_copilot                                              │
│         ├── AM_thematic_macro_advisor                                        │
│         ├── AM_esg_guardian                                                  │
│         ├── AM_compliance_advisor                                            │
│         ├── AM_sales_advisor                                                 │
│         ├── AM_quant_analyst                                                 │
│         ├── AM_middle_office_copilot                                         │
│         └── AM_executive_copilot                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## External Data Source Mapping

### SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE to SAM_DEMO Mapping

| Source Table | Target Table | Description | Join Key |
|--------------|--------------|-------------|----------|
| `STOCK_PRICE_TIMESERIES` | `MARKET_DATA.FACT_STOCK_PRICES` | Daily OHLCV stock prices from Nasdaq | TICKER |
| `SEC_METRICS_TIMESERIES` | `MARKET_DATA.FACT_SEC_SEGMENTS` | Revenue segments by geography, business unit, customer, legal entity | COMPANY_ID → ProviderCompanyID |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `MARKET_DATA.FACT_SEC_FILING_TEXT` | Full text of SEC filings (MD&A, Risk Factors) | CIK |
| `SEC_CORPORATE_REPORT_ATTRIBUTES` | `MARKET_DATA.FACT_SEC_FINANCIALS` | Full financial statements with XBRL tags | CIK |
| `COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES` | `CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS` | Real company event transcripts with speaker attribution | PRIMARY_TICKER |

### Source-to-Target Column Mapping

#### STOCK_PRICE_TIMESERIES to FACT_STOCK_PRICES

| Source Column | Target Column | Transformation |
|---------------|---------------|----------------|
| `TICKER` | `TICKER` | Direct mapping |
| `DATE` | `PRICE_DATE` | Rename |
| `VARIABLE='pre-market_open'` | `PRICE_OPEN` | Pivot on VARIABLE |
| `VARIABLE='post-market_close'` | `PRICE_CLOSE` | Pivot on VARIABLE |
| `VARIABLE='all-day_high'` | `PRICE_HIGH` | Pivot on VARIABLE |
| `VARIABLE='all-day_low'` | `PRICE_LOW` | Pivot on VARIABLE |
| `VARIABLE='nasdaq_volume'` | `VOLUME` | Pivot on VARIABLE, cast to BIGINT |
| - | `SecurityID` | Joined from DIM_SECURITY via TICKER |
| - | `IssuerID` | Joined from DIM_SECURITY via TICKER |

#### SEC_METRICS_TIMESERIES to FACT_SEC_SEGMENTS

| Source Column | Target Column | Transformation |
|---------------|---------------|----------------|
| `COMPANY_ID` | - | Join key to DIM_ISSUER.ProviderCompanyID |
| - | `IssuerID` | Joined from DIM_ISSUER via COMPANY_ID (FK to dimension) |
| `CIK` | - | Available via IssuerID -> DIM_ISSUER.CIK join |
| `ADSH` | `ADSH` | Direct mapping |
| `PERIOD_START_DATE` | `PERIOD_START_DATE` | Direct mapping |
| `PERIOD_END_DATE` | `PERIOD_END_DATE` | Direct mapping |
| `FISCAL_PERIOD` | `FISCAL_PERIOD` | Direct mapping |
| `FISCAL_YEAR` | `FISCAL_YEAR` | Cast to INTEGER |
| `FREQUENCY` | `FREQUENCY` | Direct mapping |
| `VARIABLE_NAME` | `VARIABLE_NAME` | Direct mapping |
| `TAG` | `TAG` | Direct mapping |
| `MEASURE` | `MEASURE` | Direct mapping |
| `GEO_NAME` | `GEOGRAPHY` | Trim and NULLIF empty |
| `BUSINESS_SEGMENT` | `BUSINESS_SEGMENT` | Trim and NULLIF empty |
| `BUSINESS_SUBSEGMENT` | `BUSINESS_SUBSEGMENT` | Trim and NULLIF empty |
| `CUSTOMER` | `CUSTOMER` | Trim and NULLIF empty |
| `LEGAL_ENTITY` | `LEGAL_ENTITY` | Trim and NULLIF empty |
| `VALUE` | `SEGMENT_REVENUE` | Direct mapping |
| `UNIT` | `CURRENCY` | UPPER() |
| `FISCAL_PERIOD` | `FISCAL_PERIOD` | Direct mapping |
| `FISCAL_YEAR` | `FISCAL_YEAR` | Direct mapping |
| `VALUE` | `VALUE` | Direct mapping |
| - | `IssuerID` | Joined from DIM_ISSUER via CIK (single source of truth) |

#### SEC_REPORT_TEXT_ATTRIBUTES to FACT_SEC_FILING_TEXT

| Source Column | Target Column | Transformation |
|---------------|---------------|----------------|
| `SEC_DOCUMENT_ID` | `SEC_DOCUMENT_ID` | Direct mapping |
| `CIK` | `CIK` | Direct mapping |
| `ADSH` | `ADSH` | Direct mapping |
| `VARIABLE` | `VARIABLE` | Direct mapping |
| `VARIABLE_NAME` | `VARIABLE_NAME` | Direct mapping |
| `PERIOD_END_DATE` | `PERIOD_END_DATE` | Direct mapping |
| `VALUE` | `FILING_TEXT` | Rename |
| - | `TEXT_LENGTH` | Calculated: LENGTH(VALUE) |
| - | `IssuerID` | Joined from DIM_ISSUER via CIK (single source of truth) |

### Data Filtering Applied

| Source Table | Filter Criteria | Reason |
|--------------|-----------------|--------|
| `STOCK_PRICE_TIMESERIES` | `DATE >= DATEADD(year, -2, CURRENT_DATE())` | Last 2 years of prices |
| `SEC_METRICS_TIMESERIES` | `FISCAL_YEAR >= YEAR(CURRENT_DATE()) - 5` | Last 5 years of filings |
| `SEC_METRICS_TIMESERIES` | `CIK IS NOT NULL AND VALUE IS NOT NULL` | Valid records only |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `LENGTH(VALUE) > 100` | Filter empty/short texts |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `PERIOD_END_DATE >= DATEADD(year, -3, CURRENT_DATE())` | Last 3 years of filings |

## Dependency Graph

### CURATED Schema Dependencies

```
┌───────────────────────────────────────────────────────────────────┐
│                    CURATED SCHEMA DEPENDENCIES                    │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  config.DEMO_COMPANIES (source of truth)                          │
│  │                                                                │
│  └──► DIM_ISSUER                                                  │
│       ├── CIK (links to SEC data)                                │
│       ├── IssuerID (PK)                                          │
│       │                                                           │
│       └──► DIM_SECURITY                                          │
│            ├── IssuerID (FK to DIM_ISSUER)                       │
│            ├── SecurityID (PK)                                    │
│            │                                                      │
│            ├──► FACT_TRANSACTION                                 │
│            │    ├── SecurityID (FK)                              │
│            │    ├── PortfolioID (FK to DIM_PORTFOLIO)            │
│            │    │                                                 │
│            │    └──► FACT_POSITION_DAILY_ABOR                    │
│            │         ├── Derived from FACT_TRANSACTION           │
│            │         └──► V_HOLDINGS_WITH_ESG (view)             │
│            │                                                      │
│            ├──► FACT_ESG_SCORES                                  │
│            │    └── SecurityID (FK)                              │
│            │                                                      │
│            ├──► FACT_FACTOR_EXPOSURES                            │
│            │    └── SecurityID (FK)                              │
│            │                                                      │
│            └──► Implementation/Operations tables                 │
│                 ├── FACT_TRANSACTION_COSTS                       │
│                 ├── FACT_TRADING_CALENDAR                        │
│                 ├── FACT_TAX_IMPLICATIONS                        │
│                 └── Middle office tables                         │
│                                                                   │
│  DIM_SUPPLY_CHAIN_RELATIONSHIPS                                   │
│  └── Uses IssuerID from DIM_ISSUER                               │
│                                                                   │
│  DIM_PORTFOLIO (independent)                                      │
│  └── PortfolioID (PK)                                            │
│       ├──► FACT_TRANSACTION                                      │
│       ├──► FACT_POSITION_DAILY_ABOR                              │
│       ├──► FACT_PORTFOLIO_LIQUIDITY                              │
│       ├──► FACT_RISK_LIMITS                                      │
│       └──► DIM_CLIENT_MANDATES                                   │
│                                                                   │
│  DIM_BENCHMARK (independent)                                      │
│  └── BenchmarkID (PK)                                            │
│       └──► FACT_BENCHMARK_HOLDINGS                               │
│                                                                   │
│  DIM_CLIENT (independent)                                         │
│  └── ClientID (PK)                                               │
│       └──► FACT_CLIENT_FLOWS                                     │
│                                                                   │
│  DIM_COUNTERPARTY (independent)                                   │
│  └── CounterpartyID (PK)                                         │
│       └──► FACT_TRADE_SETTLEMENT                                 │
│                                                                   │
│  DIM_CUSTODIAN (independent)                                      │
│  └── CustodianID (PK)                                            │
│       └──► Middle office tables                                  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### MARKET_DATA Schema Dependencies

```
┌───────────────────────────────────────────────────────────────────┐
│                   MARKET_DATA SCHEMA DEPENDENCIES                 │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  NOTE: DIM_COMPANY has been eliminated. Use CURATED.DIM_ISSUER    │
│  as the single source of truth for company/issuer data.          │
│                                                                   │
│  CURATED.DIM_ISSUER (Company Master - Single Source of Truth)    │
│  ├── IssuerID (PK)                                               │
│  ├── CIK (links to SEC data)                                     │
│  ├── LegalName, PrimaryTicker, SIC_DESCRIPTION                   │
│  │                                                                │
│  └──► FACT_SEC_FINANCIALS (PRIMARY - real SEC data)              │
│       ├── IssuerID (FK to DIM_ISSUER)                            │
│       ├── CIK (join to external SEC_CORPORATE_REPORT_ATTRS)      │
│       ├── Financial Statements (Income, Balance, Cash Flow)      │
│       ├── Calculated Ratios (margins, ROE, ROA)                  │
│       ├── TAM (heuristic: Revenue x Industry Multiplier)         │
│       ├── ESTIMATED_CUSTOMER_COUNT (Revenue / ARPC)              │
│       ├── ESTIMATED_NRR_PCT (100 + Revenue Growth %)             │
│       │                                                           │
│       └──► FACT_ESTIMATE_CONSENSUS                               │
│            ├── IssuerID (FK)                                     │
│            └── Uses FACT_SEC_FINANCIALS for base actuals         │
│                                                                   │
│  FACT_FINANCIAL_DATA_SEC (real - additional SEC metrics)          │
│  ├── CIK (join to SEC_METRICS_TIMESERIES)                        │
│  └── IssuerID (FK to DIM_ISSUER)                                 │
│                                                                   │
│  FACT_SEC_FILING_TEXT (real)                                      │
│  └── IssuerID (FK to DIM_ISSUER)                                 │
│                                                                   │
│  FACT_STOCK_PRICES                                                │
│  ├── SecurityID (FK to DIM_SECURITY via ticker match)            │
│  ├── IssuerID (FK to DIM_ISSUER)                                 │
│  └── TICKER (join key to DIM_SECURITY)                           │
│                                                                   │
│  DIM_ANALYST                                                      │
│  └── ANALYST_ID (PK)                                             │
│       └──► FACT_ANALYST_COVERAGE                                 │
│       └──► FACT_ESTIMATE_DATA                                    │
│                                                                   │
│  Build Order:                                                     │
│  1. DIM_ANALYST, DIM_BROKER (DIM_ISSUER already exists in CURATED)│
│  2. FACT_STOCK_PRICES                                             │
│  3. FACT_FINANCIAL_DATA_SEC                                       │
│  4. FACT_SEC_FILING_TEXT                                          │
│  5. FACT_SEC_FINANCIALS (includes calculated TAM/NRR)             │
│  6. Broker/Analyst data                                           │
│  7. FACT_ESTIMATE_CONSENSUS (uses FACT_SEC_FINANCIALS actuals)    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Document Corpus Dependencies

```
┌───────────────────────────────────────────────────────────────────┐
│                   DOCUMENT CORPUS DEPENDENCIES                    │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  content_library/*.md (templates)                                 │
│  │                                                                │
│  └──► hydration_engine.py                                        │
│       ├── Reads DIM_SECURITY (for security data)                 │
│       ├── Reads DIM_ISSUER (for issuer data)                     │
│       ├── Reads DIM_PORTFOLIO (for portfolio data)               │
│       │                                                           │
│       └──► RAW.*_RAW tables                                      │
│            └──► CURATED.*_CORPUS tables                          │
│                 └──► AI.SAM_* (search services)                  │
│                                                                   │
│  Real Company Event Transcripts:                                  │
│  │                                                                │
│  SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE                      │
│  └── COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES                         │
│       │                                                           │
│       ├──► AI_COMPLETE (speaker identification)                  │
│       │    └──► MARKET_DATA.COMP_EVENT_SPEAKER_MAPPING           │
│       │                                                           │
│       └──► SPLIT_TEXT_RECURSIVE_CHARACTER (chunking)             │
│            └──► CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS         │
│                 └──► AI.SAM_COMPANY_EVENTS (search)              │
│                                                                   │
│  Document Linkage Levels:                                         │
│  - Security-level: SecurityID + IssuerID                         │
│  - Issuer-level: IssuerID only                                   │
│  - Portfolio-level: PortfolioID                                  │
│  - Global: No linkage                                            │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### AI Component Dependencies

```
┌───────────────────────────────────────────────────────────────────┐
│                    AI COMPONENT DEPENDENCIES                      │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SEMANTIC VIEWS (AI Schema)                                       │
│  │                                                                │
│  ├── SAM_ANALYST_VIEW (consolidated with factor analysis)        │
│  │   ├── CURATED.V_HOLDINGS_WITH_ESG                             │
│  │   ├── CURATED.DIM_PORTFOLIO                                   │
│  │   ├── CURATED.DIM_SECURITY                                    │
│  │   ├── CURATED.DIM_ISSUER                                      │
│  │   ├── CURATED.FACT_FACTOR_EXPOSURES                           │
│  │   └── CURATED.FACT_BENCHMARK_HOLDINGS                         │
│  │                                                                │
│  ├── SAM_FUNDAMENTALS_VIEW                                       │
│  │   ├── MARKET_DATA.FACT_SEC_FINANCIALS (real SEC + TAM/NRR)    │
│  │   ├── MARKET_DATA.FACT_ESTIMATE_CONSENSUS                     │
│  │   ├── CURATED.DIM_ISSUER (single source of truth)             │
│  │   ├── MARKET_DATA.DIM_ANALYST                                 │
│  │   └── MARKET_DATA.DIM_BROKER                                  │
│  │                                                                │
│  ├── SAM_IMPLEMENTATION_VIEW                                     │
│  │   ├── CURATED.FACT_TRANSACTION_COSTS                          │
│  │   ├── CURATED.FACT_PORTFOLIO_LIQUIDITY                        │
│  │   └── CURATED.FACT_RISK_LIMITS                                │
│  │                                                                │
│  ├── SAM_STOCK_PRICES_VIEW                                       │
│  │   ├── MARKET_DATA.FACT_STOCK_PRICES                           │
│  │   ├── CURATED.DIM_SECURITY                                    │
│  │   └── CURATED.DIM_ISSUER (single source of truth)             │
│  │                                                                │
│  └── Additional views: SUPPLY_CHAIN, MIDDLE_OFFICE, COMPLIANCE,  │
│      EXECUTIVE, SEC_FINANCIALS                                    │
│                                                                   │
│  CORTEX SEARCH SERVICES (AI Schema)                               │
│  │                                                                │
│  ├── SAM_BROKER_RESEARCH ─────► CURATED.BROKER_RESEARCH_CORPUS   │
│  ├── SAM_COMPANY_EVENTS ──────► CURATED.COMPANY_EVENT_TRANSCRIPTS│
│  ├── SAM_PRESS_RELEASES ──────► CURATED.PRESS_RELEASES_CORPUS    │
│  ├── SAM_NGO_REPORTS ─────────► CURATED.NGO_REPORTS_CORPUS       │
│  ├── SAM_ENGAGEMENT_NOTES ────► CURATED.ENGAGEMENT_NOTES_CORPUS  │
│  ├── SAM_POLICY_DOCS ─────────► CURATED.POLICY_DOCS_CORPUS       │
│  ├── SAM_REAL_SEC_FILINGS ────► MARKET_DATA.FACT_SEC_FILING_TEXT │
│  └── [additional services for ops, sales, strategy documents]    │
│                                                                   │
│  AGENTS (AI Schema)                                               │
│  │                                                                │
│  ├── AM_portfolio_copilot                                        │
│  │   ├── Tool: quantitative_analyzer ──► SAM_ANALYST_VIEW       │
│  │   ├── Tool: stock_prices ─────────► SAM_STOCK_PRICES_VIEW   │
│  │   ├── Tool: sec_financials ───────► SAM_SEC_FINANCIALS_VIEW │
│  │   ├── Tool: search_broker_research ► SAM_BROKER_RESEARCH     │
│  │   ├── Tool: search_company_events ─► SAM_COMPANY_EVENTS      │
│  │   └── Tool: search_press_releases ─► SAM_PRESS_RELEASES      │
│  │                                                                │
│  ├── AM_research_copilot                                         │
│  │   ├── Tool: fundamentals_analyzer ─► SAM_FUNDAMENTALS_VIEW  │
│  │   ├── Tool: sec_financials ───────► SAM_SEC_FINANCIALS_VIEW │
│  │   ├── Tool: search_broker_research ► SAM_BROKER_RESEARCH     │
│  │   ├── Tool: search_company_events ─► SAM_COMPANY_EVENTS      │
│  │   └── Tool: search_sec_filings ────► SAM_REAL_SEC_FILINGS   │
│  │                                                                │
│  ├── AM_quant_analyst                                            │
│  │   ├── Tool: quantitative_analyzer ─► SAM_ANALYST_VIEW        │
│  │   ├── Tool: stock_prices ─────────► SAM_STOCK_PRICES_VIEW   │
│  │   └── Tool: search_broker_research ► SAM_BROKER_RESEARCH     │
│  │                                                                │
│  ├── AM_thematic_macro_advisor                                   │
│  │   ├── Tool: quantitative_analyzer ─► SAM_ANALYST_VIEW        │
│  │   ├── Tool: search_broker_research ► SAM_BROKER_RESEARCH     │
│  │   ├── Tool: search_press_releases ─► SAM_PRESS_RELEASES      │
│  │   └── Tool: search_sec_filings ────► SAM_REAL_SEC_FILINGS   │
│  │                                                                │
│  ├── AM_esg_guardian                                             │
│  │   ├── Tool: quantitative_analyzer ─► SAM_ANALYST_VIEW        │
│  │   └── Tool: search_sec_filings ────► SAM_REAL_SEC_FILINGS   │
│  │                                                                │
│  ├── AM_compliance_advisor                                       │
│  │   └── Uses: SAM_COMPLIANCE_VIEW, SAM_POLICY_DOCS             │
│  │                                                                │
│  ├── AM_sales_advisor                                            │
│  │   └── Uses: SAM_ANALYST_VIEW, SAM_SALES_TEMPLATES            │
│  │                                                                │
│  ├── AM_middle_office_copilot                                    │
│  │   └── Uses: SAM_MIDDLE_OFFICE_VIEW, ops search services      │
│  │                                                                │
│  └── AM_executive_copilot                                        │
│      └── Uses: SAM_EXECUTIVE_VIEW, SAM_STRATEGY_DOCUMENTS       │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Impact Analysis Matrix

### If You Change... Then You Must...

| Changed Object | Immediate Impact | Must Rebuild/Update |
|----------------|------------------|---------------------|
| **config.DEMO_COMPANIES** | All data generation changes | Full rebuild recommended |
| **DIM_ISSUER** | All FK references break | DIM_SECURITY, DIM_SUPPLY_CHAIN, all MARKET_DATA tables with IssuerID, all corpus tables, all semantic views |
| **DIM_SECURITY** | Holdings, transactions break | FACT_TRANSACTION, FACT_POSITION_DAILY_ABOR, FACT_ESG_SCORES, FACT_FACTOR_EXPOSURES, FACT_STOCK_PRICES, all corpus tables |
| **DIM_PORTFOLIO** | Holdings, transactions break | FACT_TRANSACTION, FACT_POSITION_DAILY_ABOR, client/executive tables |
| **FACT_POSITION_DAILY_ABOR** | Portfolio analytics break | V_HOLDINGS_WITH_ESG, SAM_ANALYST_VIEW, portfolio_copilot |
| **FACT_STOCK_PRICES** | Price analytics break | SAM_STOCK_PRICES_VIEW, V_SECURITY_RETURNS, agents using stock_prices tool |
| **FACT_SEC_FINANCIALS** | Estimate generation and fundamentals view break | FACT_ESTIMATE_CONSENSUS, SAM_FUNDAMENTALS_VIEW |
| **FACT_FINANCIAL_DATA_SEC** | SEC analysis breaks | SAM_SEC_FINANCIALS_VIEW, agents using sec_financials tool |
| **FACT_SEC_FILING_TEXT** | SEC search breaks | SAM_REAL_SEC_FILINGS, agents using search_sec_filings tool |
| ***_CORPUS tables** | Document search breaks | Corresponding SAM_* Cortex Search service |
| **SAM_ANALYST_VIEW** | Portfolio queries break | portfolio_copilot, quant_analyst, thematic_macro_advisor, esg_guardian |
| **SAM_SEC_FINANCIALS_VIEW** | SEC queries break | research_copilot, portfolio_copilot (sec_financials tool) |
| **SAM_STOCK_PRICES_VIEW** | Price queries break | portfolio_copilot, quant_analyst (stock_prices tool) |
| **SAM_BROKER_RESEARCH** | Research search breaks | portfolio_copilot, research_copilot, quant_analyst, thematic_macro_advisor |
| **SAM_REAL_SEC_FILINGS** | SEC search breaks | research_copilot, thematic_macro_advisor, esg_guardian |
| **content_library templates** | Document quality changes | Regenerate corpus tables, rebuild search services |

## Module Responsibility Matrix

| Module | Creates | Depends On |
|--------|---------|------------|
| `main.py` | Orchestration | All modules |
| `generate_structured.py` | CURATED dimension/fact tables | config |
| `generate_market_data.py` | MARKET_DATA tables | CURATED.DIM_ISSUER, CURATED.DIM_SECURITY, config |
| `generate_unstructured.py` | RAW/*_RAW, CURATED/*_CORPUS | CURATED.DIM_SECURITY, CURATED.DIM_ISSUER, hydration_engine |
| `generate_real_transcripts.py` | COMP_EVENT_SPEAKER_MAPPING, COMPANY_EVENT_TRANSCRIPTS_CORPUS | SNOWFLAKE_PUBLIC_DATA_FREE, CURATED.DIM_SECURITY |
| `hydration_engine.py` | Document content | content_library templates, CURATED dimensions |
| `build_ai.py` | AI orchestration | create_semantic_views, create_cortex_search, create_agents |
| `create_semantic_views.py` | AI semantic views | CURATED tables, MARKET_DATA tables |
| `create_cortex_search.py` | AI search services | CURATED corpus tables, MARKET_DATA.FACT_SEC_FILING_TEXT |
| `create_agents.py` | AI agents | Semantic views, search services |

## CIK Linkage Map

The CIK (SEC Central Index Key) links internal data to real SEC data:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CIK LINKAGE MAP                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE                                 │
│  (via config.REAL_DATA_SOURCES)                                              │
│                                                                              │
│  COMPANY_INDEX.CIK ─────────────────────────────────────────────┐           │
│  ├── SEC_METRICS_TIMESERIES.CIK ──────────────────────────────────┤         │
│  ├── SEC_REPORT_TEXT_ATTRIBUTES.CIK ──────────────────────────────┤         │
│  ├── SEC_CORPORATE_REPORT_ATTRIBUTES.CIK ─────────────────────────┤         │
│  └── STOCK_PRICE_TIMESERIES (via ticker, not CIK) ────────────────┤         │
│                                                                    │         │
│                                                                    ▼         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CURATED.DIM_ISSUER.CIK (Single Source of Truth)                    │    │
│  │  │                                                                   │    │
│  │  ├──► FACT_FINANCIAL_DATA_SEC.CIK (direct join)                     │    │
│  │  ├──► FACT_SEC_FILING_TEXT.IssuerID                                 │    │
│  │  ├──► FACT_SEC_FINANCIALS.IssuerID                                  │    │
│  │  │                                                                   │    │
│  │  └──► Enables joins between:                                        │    │
│  │       - Internal holdings (DIM_SECURITY → DIM_ISSUER)               │    │
│  │       - Real SEC financials (FACT_SEC_FINANCIALS)                   │    │
│  │       - Real SEC filings (FACT_SEC_FILING_TEXT)                     │    │
│  │       - Real stock prices (FACT_STOCK_PRICES via ticker)            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Coverage: All 79 companies have CIK linkage (100% SEC data coverage)       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Rebuild Procedures

### Full Rebuild
```bash
python main.py --connection-name CONNECTION --scenarios all
```
Rebuilds everything in correct dependency order.

### Partial Rebuilds

| Scope | Command | What It Rebuilds |
|-------|---------|------------------|
| Structured only | `--scope structured` | CURATED dimension/fact tables |
| Unstructured only | `--scope unstructured` | RAW/*_RAW, CURATED/*_CORPUS |
| Market data only | (included in structured) | MARKET_DATA tables |
| AI only | `--scope ai` | Semantic views, search services, agents |
| Semantic views only | `--scope semantic` | AI semantic views |
| Search services only | `--scope search` | AI Cortex Search services |
| Agents only | `--scope agents` | AI agents |

### After Changing Specific Objects

| Changed | Minimum Rebuild |
|---------|----------------|
| DIM_ISSUER | `--scope structured` then `--scope ai` |
| DIM_SECURITY | `--scope structured` then `--scope ai` |
| content_library templates | `--scope unstructured` then `--scope search` |
| config.DEMO_COMPANIES | Full rebuild recommended |
| Semantic view definition | `--scope semantic` |
| Agent configuration | `--scope agents` |

## Configuration Dependencies

### config.py Critical Settings

| Setting | Affects |
|---------|---------|
| `DATABASE['name']` | All SQL references |
| `DATABASE['schemas']` | Schema creation, table locations |
| `WAREHOUSES` | Semantic views, search services |
| `DEMO_COMPANIES` | All data generation |
| `REAL_DATA_SOURCES['enabled']` | Whether real data is loaded |
| `REAL_DATA_SOURCES['tables']` | Real data table references |
| `DOCUMENT_TYPES` | Corpus table names, search service names |
| `SCENARIO_DATA_REQUIREMENTS` | Which documents are generated |

## Troubleshooting Dependency Issues

### Common Errors

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| "Object does not exist" in semantic view | Underlying table not created | Rebuild with `--scope structured` |
| "Invalid identifier" in semantic view | Column name mismatch | Check `DESCRIBE TABLE` for actual column names |
| "No results" from search service | Corpus table empty | Rebuild with `--scope unstructured` |
| "Agent tool not found" | Semantic view or search service missing | Rebuild with `--scope ai` |
| "CIK linkage returns 0 records" | DIM_ISSUER missing CIK | Check DEMO_COMPANIES configuration |
| "FACT_ESTIMATE_CONSENSUS fails" | FACT_SEC_FINANCIALS not built | Ensure real SEC data builds before estimates (requires REAL_DATA_SOURCES enabled) |
| "SAM_FUNDAMENTALS_VIEW creation fails" | FACT_SEC_FINANCIALS not found | Build real SEC data first with `--scope real-data` |

### Validation Queries

```sql
-- Check CIK coverage
SELECT COUNT(*) as total, COUNT(CIK) as with_cik FROM SAM_DEMO.CURATED.DIM_ISSUER;

-- Check real data integration
SELECT COUNT(*) FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES;
SELECT COUNT(*) FROM SAM_DEMO.MARKET_DATA.FACT_FINANCIAL_DATA_SEC;
SELECT COUNT(*) FROM SAM_DEMO.MARKET_DATA.FACT_SEC_FILING_TEXT;

-- Check semantic views
SHOW SEMANTIC VIEWS IN SAM_DEMO.AI;

-- Check search services
SHOW CORTEX SEARCH SERVICES IN SAM_DEMO.AI;

-- Check agents
SHOW AGENTS IN SAM_DEMO.AI;
```
