# SAM Demo - Data Lineage and Dependencies

Complete documentation of data flows, object dependencies, and impact analysis for the SAM demo environment.

## Overview

This document maps all dependencies between objects in the SAM demo to help understand the impact of changes. Use this guide when modifying any component to understand what else may be affected.

## Build Order (High-Level)

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
│         ├── V_REAL_ASSETS (view) ─────────────────┐                         │
│         ├── DIM_ISSUER ◄──────────────────────────┤                         │
│         ├── DIM_SECURITY ◄────────────────────────┘                         │
│         ├── DIM_PORTFOLIO                                                    │
│         ├── DIM_BENCHMARK                                                    │
│         ├── DIM_SUPPLY_CHAIN_RELATIONSHIPS                                   │
│         ├── FACT_TRANSACTION                                                 │
│         ├── FACT_POSITION_DAILY_ABOR                                         │
│         ├── FACT_ESG_SCORES                                                  │
│         └── FACT_FACTOR_EXPOSURES                                            │
│                                                                              │
│  3. MARKET DATA (generate_market_data.py)                                    │
│     ├── Synthetic Data (always built)                                        │
│     │   ├── DIM_COMPANY                                                      │
│     │   ├── FACT_FINANCIAL_DATA                                              │
│     │   └── FACT_ESTIMATE_CONSENSUS                                          │
│     └── Real Data (when enabled)                                             │
    │         ├── FACT_STOCK_PRICES                                                │
    │         ├── FACT_FINANCIAL_DATA_SEC                                          │
    │         ├── FACT_SEC_FILING_TEXT                                             │
    │         └── FACT_SEC_FINANCIALS (NEW - comprehensive financial statements)  │
│                                                                              │
│  4. UNSTRUCTURED DATA (generate_unstructured.py)                             │
│     └── Document Types (parallel)                                            │
│         ├── RAW.*_RAW tables ──► CURATED.*_CORPUS tables                    │
│         │   ├── BROKER_RESEARCH_CORPUS                                       │
│         │   ├── EARNINGS_TRANSCRIPTS_CORPUS                                  │
│         │   └── PRESS_RELEASES_CORPUS                                        │
│                                                                              │
│  5. AI COMPONENTS (build_ai.py)                                              │
│     ├── Semantic Views (create_semantic_views.py)                            │
    │     │   ├── SAM_ANALYST_VIEW                                                 │
    │     │   ├── SAM_RESEARCH_VIEW                                                │
    │     │   ├── SAM_REAL_SEC_VIEW                                                │
    │     │   ├── SAM_STOCK_PRICES_VIEW                                            │
    │     │   └── SAM_SEC_FINANCIALS_VIEW (NEW - comprehensive financials)        │
│     ├── Cortex Search Services (create_cortex_search.py)                     │
│     │   ├── SAM_BROKER_RESEARCH                                              │
│     │   ├── SAM_EARNINGS_TRANSCRIPTS                                         │
│     │   ├── SAM_PRESS_RELEASES                                               │
│     │   └── SAM_REAL_SEC_FILINGS                                             │
│     └── Agents (create_agents.py)                                            │
│         ├── portfolio_copilot                                                │
│         ├── research_copilot                                                 │
│         └── [other agents...]                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## External Data Source Mapping

### SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE → SAM_DEMO Mapping

| Source Table | Target Table | Description | Records | Join Key |
|--------------|--------------|-------------|---------|----------|
| `STOCK_PRICE_TIMESERIES` | `MARKET_DATA.FACT_STOCK_PRICES` | Daily OHLCV stock prices from Nasdaq | 5.2M+ | TICKER |
| `SEC_METRICS_TIMESERIES` | `MARKET_DATA.FACT_FINANCIAL_DATA_SEC` | Revenue segments, financial metrics from 10-K/10-Q | 9,400+ | CIK |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `MARKET_DATA.FACT_SEC_FILING_TEXT` | Full text of SEC filings (MD&A, Risk Factors) | 6,300+ | CIK |
| `SEC_CORPORATE_REPORT_ATTRIBUTES` | `MARKET_DATA.FACT_SEC_FINANCIALS` | **NEW** Full financial statements (Income Statement, Balance Sheet, Cash Flow) with XBRL tags | 4,400+ | CIK |
| `COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES` | `CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS` | Real company event transcripts (Earnings Calls, AGMs, M&A, Investor Days) with speaker attribution | ~500+ chunks | PRIMARY_TICKER |

### Additional SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE Tables → SAM_DEMO Mapping

The following tables are also used from the same `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE` database for the real assets view:

| Source Table | Target Table | Description | Records | Join Key |
|--------------|--------------|-------------|---------|----------|
| `OPENFIGI_SECURITY_INDEX` | `RAW.V_REAL_ASSETS` (view) | Security master data with tickers and FIGI | 90K+ | FIGI |
| `COMPANY_SECURITY_RELATIONSHIPS` | `RAW.V_REAL_ASSETS` (view) | Company-security linkages | - | COMPANY_ID |
| `COMPANY_INDEX` | `RAW.V_REAL_ASSETS` (view) | Company CIK and identifiers | - | CIK |
| `COMPANY_CHARACTERISTICS` | `RAW.V_REAL_ASSETS` (view) | Company attributes and metadata | - | COMPANY_ID |

> **Note**: All external data sources are configured in `config.REAL_DATA_SOURCES` dictionary.

### Detailed Source-to-Target Column Mapping

#### STOCK_PRICE_TIMESERIES → FACT_STOCK_PRICES

| Source Column | Target Column | Transformation |
|---------------|---------------|----------------|
| `TICKER` | `TICKER` | Direct mapping |
| `DATE` | `PRICE_DATE` | Rename |
| `VARIABLE='pre-market_open'` | `PRICE_OPEN` | Pivot on VARIABLE |
| `VARIABLE='post-market_close'` | `PRICE_CLOSE` | Pivot on VARIABLE |
| `VARIABLE='all-day_high'` | `PRICE_HIGH` | Pivot on VARIABLE |
| `VARIABLE='all-day_low'` | `PRICE_LOW` | Pivot on VARIABLE |
| `VARIABLE='nasdaq_volume'` | `VOLUME` | Pivot on VARIABLE, cast to BIGINT |
| `ASSET_CLASS` | `ASSET_CLASS` | Direct mapping |
| `PRIMARY_EXCHANGE_CODE` | `PRIMARY_EXCHANGE_CODE` | Direct mapping |
| `PRIMARY_EXCHANGE_NAME` | `PRIMARY_EXCHANGE_NAME` | Direct mapping |
| - | `SecurityID` | Joined from DIM_SECURITY via TICKER |
| - | `IssuerID` | Joined from DIM_SECURITY via TICKER |
| - | `PRICE_ID` | Generated (ROW_NUMBER) |
| - | `DATA_SOURCE` | Constant: 'STOCK_PRICE_TIMESERIES' |
| - | `LOADED_AT` | CURRENT_TIMESTAMP() |

#### SEC_METRICS_TIMESERIES → FACT_FINANCIAL_DATA_SEC

| Source Column | Target Column | Transformation |
|---------------|---------------|----------------|
| `ADSH` | `ADSH` | Direct mapping |
| `CIK` | `CIK` | Direct mapping |
| `COMPANY_NAME` | `SEC_COMPANY_NAME` | Rename |
| `VARIABLE_NAME` | `VARIABLE_NAME` | Direct mapping |
| `TAG` | `TAG` | Direct mapping |
| `TAG_VERSION` | `TAG_VERSION` | Direct mapping |
| `PERIOD_START_DATE` | `PERIOD_START_DATE` | Direct mapping |
| `PERIOD_END_DATE` | `PERIOD_END_DATE` | Direct mapping |
| `FISCAL_PERIOD` | `FISCAL_PERIOD` | Direct mapping |
| `FISCAL_YEAR` | `FISCAL_YEAR` | Direct mapping |
| `VALUE` | `VALUE` | Direct mapping |
| `UNIT` | `UNIT` | Direct mapping |
| `MEASURE` | `MEASURE` | Direct mapping |
| `BUSINESS_SEGMENT` | `BUSINESS_SEGMENT` | Direct mapping |
| `BUSINESS_SUBSEGMENT` | `BUSINESS_SUBSEGMENT` | Direct mapping |
| `GEO_NAME` | `GEO_NAME` | Direct mapping |
| `CUSTOMER` | `CUSTOMER` | Direct mapping |
| `FREQUENCY` | `FREQUENCY` | Direct mapping |
| - | `FINANCIAL_DATA_ID` | Generated (ROW_NUMBER) |
| - | `COMPANY_ID` | Joined from DIM_COMPANY via CIK |
| - | `IssuerID` | Joined from DIM_ISSUER via CIK |
| - | `DATA_SOURCE` | Constant: 'SEC_METRICS_TIMESERIES' |
| - | `LOADED_AT` | CURRENT_TIMESTAMP() |

#### SEC_REPORT_TEXT_ATTRIBUTES → FACT_SEC_FILING_TEXT

| Source Column | Target Column | Transformation |
|---------------|---------------|----------------|
| `SEC_DOCUMENT_ID` | `SEC_DOCUMENT_ID` | Direct mapping |
| `CIK` | `CIK` | Direct mapping |
| `ADSH` | `ADSH` | Direct mapping |
| `VARIABLE` | `VARIABLE` | Direct mapping |
| `VARIABLE_NAME` | `VARIABLE_NAME` | Direct mapping |
| `PERIOD_END_DATE` | `PERIOD_END_DATE` | Direct mapping |
| `VALUE` | `FILING_TEXT` | Rename (contains raw text) |
| - | `TEXT_LENGTH` | Calculated: LENGTH(VALUE) |
| - | `FILING_TEXT_ID` | Generated (ROW_NUMBER) |
| - | `COMPANY_ID` | Joined from DIM_COMPANY via CIK |
| - | `IssuerID` | Joined from DIM_ISSUER via CIK |
| - | `DATA_SOURCE` | Constant: 'SEC_REPORT_TEXT_ATTRIBUTES' |
| - | `LOADED_AT` | CURRENT_TIMESTAMP() |

### Data Filtering Applied

| Source Table | Filter Criteria | Reason |
|--------------|-----------------|--------|
| `STOCK_PRICE_TIMESERIES` | `DATE >= DATEADD(year, -2, CURRENT_DATE())` | Last 2 years of prices |
| `SEC_METRICS_TIMESERIES` | `FISCAL_YEAR >= YEAR(CURRENT_DATE()) - 5` | Last 5 years of filings |
| `SEC_METRICS_TIMESERIES` | `CIK IS NOT NULL AND VALUE IS NOT NULL` | Valid records only |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `LENGTH(VALUE) > 100` | Filter empty/short texts |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `PERIOD_END_DATE >= DATEADD(year, -3, CURRENT_DATE())` | Last 3 years of filings |

### Coverage Summary

| Data Type | Coverage | Notes |
|-----------|----------|-------|
| Stock Prices | ~865 tickers linked to DIM_SECURITY | Matches by ticker symbol |
| SEC Financials | ~39 companies with CIK linkage | Requires CIK in DIM_ISSUER |
| SEC Filing Text | ~50 companies with CIK linkage | Requires CIK in DIM_ISSUER |

## Detailed Dependency Graph

### External Data Sources

```
┌───────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE                      │
│  (All external data via config.REAL_DATA_SOURCES)                 │
│                                                                   │
│  Security Master Data (for V_REAL_ASSETS):                        │
│  ├── OPENFIGI_SECURITY_INDEX ──────► V_REAL_ASSETS (view)        │
│  ├── COMPANY_SECURITY_RELATIONSHIPS ─┘                            │
│  ├── COMPANY_INDEX ──────────────────┘                            │
│  └── COMPANY_CHARACTERISTICS ────────┘                            │
│                                                                   │
│  Market Data (for MARKET_DATA schema):                            │
│  ├── STOCK_PRICE_TIMESERIES ─────────► FACT_STOCK_PRICES         │
│  ├── SEC_METRICS_TIMESERIES ─────────► FACT_FINANCIAL_DATA_SEC   │
│  ├── SEC_REPORT_TEXT_ATTRIBUTES ─────► FACT_SEC_FILING_TEXT      │
│  └── COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES ──► COMPANY_EVENT_TRANSCRIPTS_CORPUS │
│       ├── AI_COMPLETE (speaker ID) ───► COMP_EVENT_SPEAKER_MAPPING │
│       └── SPLIT_TEXT_RECURSIVE_CHARACTER (chunking)              │
│                                                                   │
│  content_library/ (templates)                                     │
│  └── [markdown templates] ───────────► *_CORPUS tables           │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### CURATED Schema Dependencies

```
┌───────────────────────────────────────────────────────────────────┐
│                    CURATED SCHEMA DEPENDENCIES                    │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  V_REAL_ASSETS (RAW view)                                         │
│  │                                                                │
│  ├──► DIM_ISSUER                                                  │
│  │    ├── CIK (links to SEC data)                                │
│  │    ├── IssuerID (PK)                                          │
│  │    │                                                           │
│  │    └──► DIM_SECURITY                                          │
│  │         ├── IssuerID (FK to DIM_ISSUER)                       │
│  │         ├── SecurityID (PK)                                    │
│  │         │                                                      │
│  │         ├──► FACT_TRANSACTION                                 │
│  │         │    ├── SecurityID (FK)                              │
│  │         │    ├── PortfolioID (FK to DIM_PORTFOLIO)            │
│  │         │    │                                                 │
│  │         │    └──► FACT_POSITION_DAILY_ABOR                    │
│  │         │         ├── Derived from FACT_TRANSACTION           │
│  │         │         ├── SecurityID (FK)                         │
│  │         │         └── PortfolioID (FK)                        │
│  │         │                                                      │
│  │         ├──► FACT_ESG_SCORES                                  │
│  │         │    └── SecurityID (FK)                              │
│  │         │                                                      │
│  │         └──► FACT_FACTOR_EXPOSURES                            │
│  │              └── SecurityID (FK)                              │
│  │                                                                │
│  └──► DIM_SUPPLY_CHAIN_RELATIONSHIPS                             │
│       └── Uses IssuerID from DIM_ISSUER                          │
│                                                                   │
│  DIM_PORTFOLIO (independent)                                      │
│  └── PortfolioID (PK)                                            │
│       ├──► FACT_TRANSACTION                                      │
│       └──► FACT_POSITION_DAILY_ABOR                              │
│                                                                   │
│  DIM_BENCHMARK (independent)                                      │
│  └── BenchmarkID (PK)                                            │
│       └──► FACT_BENCHMARK_HOLDINGS                               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### MARKET_DATA Schema Dependencies

```
┌───────────────────────────────────────────────────────────────────┐
│                   MARKET_DATA SCHEMA DEPENDENCIES                 │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  DIM_COMPANY                                                      │
│  ├── COMPANY_ID (PK)                                             │
│  ├── CIK (links to SEC data and DIM_ISSUER)                      │
│  │                                                                │
│  ├──► FACT_FINANCIAL_DATA (synthetic)                            │
│  │    └── COMPANY_ID (FK)                                        │
│  │                                                                │
│  ├──► FACT_FINANCIAL_DATA_SEC (real)                             │
│  │    ├── COMPANY_ID (FK)                                        │
│  │    ├── CIK (join to external data)                            │
│  │    └── IssuerID (FK to DIM_ISSUER)                            │
│  │                                                                │
│  └──► FACT_SEC_FILING_TEXT (real)                                │
│       ├── COMPANY_ID (FK)                                        │
│       └── IssuerID (FK to DIM_ISSUER)                            │
│                                                                   │
│  FACT_STOCK_PRICES (real)                                         │
│  ├── SecurityID (FK to DIM_SECURITY via ticker match)            │
│  ├── IssuerID (FK to DIM_ISSUER)                                 │
│  └── TICKER (join key to DIM_SECURITY)                           │
│                                                                   │
│  FACT_ESTIMATE_CONSENSUS                                          │
│  ├── COMPANY_ID (FK to DIM_COMPANY)                              │
│  └── Depends on: FACT_FINANCIAL_DATA (for base metrics)          │
│                                                                   │
│  Build Order:                                                     │
│  1. DIM_COMPANY                                                   │
│  2. FACT_FINANCIAL_DATA (synthetic) ← Always built first         │
│  3. FACT_ESTIMATE_CONSENSUS ← Depends on FACT_FINANCIAL_DATA     │
│  4. FACT_STOCK_PRICES (real) ← Supplementary                     │
│  5. FACT_FINANCIAL_DATA_SEC (real) ← Supplementary               │
│  6. FACT_SEC_FILING_TEXT (real) ← Supplementary                  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Document Corpus Dependencies

```
┌───────────────────────────────────────────────────────────────────┐
│                   DOCUMENT CORPUS DEPENDENCIES                    │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  content_library/security/*.md (templates)                        │
│  │                                                                │
│  └──► hydration_engine.py                                        │
│       ├── Reads DIM_SECURITY (for security data)                 │
│       ├── Reads DIM_ISSUER (for issuer data)                     │
│       │                                                           │
│       └──► RAW.*_RAW tables                                      │
│            ├── RAW.BROKER_RESEARCH_RAW                           │
│            │   └──► CURATED.BROKER_RESEARCH_CORPUS               │
│            │        └──► AI.SAM_BROKER_RESEARCH (search)         │
│            │                                                      │
│            └── RAW.PRESS_RELEASES_RAW                            │
│                └──► CURATED.PRESS_RELEASES_CORPUS                │
│                     └──► AI.SAM_PRESS_RELEASES (search)          │
│                                                                   │
│  REAL COMPANY EVENT TRANSCRIPTS (replaces synthetic earnings):   │
│  │                                                                │
│  SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE                      │
│  └── COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES                         │
│       │                                                           │
│       ├──► AI_COMPLETE (speaker identification)                  │
│       │    └──► MARKET_DATA.COMP_EVENT_SPEAKER_MAPPING           │
│       │         (SPEAKER_ID, SPEAKER_NAME, SPEAKER_ROLE,         │
│       │          SPEAKER_COMPANY)                                 │
│       │                                                           │
│       └──► SPLIT_TEXT_RECURSIVE_CHARACTER (chunking)             │
│            └──► CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS         │
│                 ├── DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TEXT   │
│                 ├── SecurityID, IssuerID (via ticker lookup)     │
│                 ├── EVENT_TYPE (Earnings Call, AGM, M&A, etc.)   │
│                 └──► AI.SAM_COMPANY_EVENTS (search)              │
│                                                                   │
│  Document Linkage:                                                │
│  - Security-level: SecurityID + IssuerID                         │
│  - Issuer-level: IssuerID only                                   │
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
│  ├── SAM_ANALYST_VIEW                                            │
│  │   ├── CURATED.FACT_POSITION_DAILY_ABOR                        │
│  │   ├── CURATED.DIM_PORTFOLIO                                   │
│  │   ├── CURATED.DIM_SECURITY                                    │
│  │   └── CURATED.DIM_ISSUER                                      │
│  │                                                                │
│  ├── SAM_RESEARCH_VIEW                                           │
│  │   ├── CURATED.DIM_SECURITY                                    │
│  │   ├── CURATED.DIM_ISSUER                                      │
│  │   └── MARKET_DATA.FACT_FINANCIAL_DATA (or FACT_ESTIMATE_...)  │
│  │                                                                │
│  ├── SAM_REAL_SEC_VIEW                                           │
│  │   ├── MARKET_DATA.FACT_FINANCIAL_DATA_SEC                     │
│  │   ├── MARKET_DATA.DIM_COMPANY                                 │
│  │   └── CURATED.DIM_ISSUER                                      │
│  │                                                                │
│  └── SAM_STOCK_PRICES_VIEW                                       │
│      ├── MARKET_DATA.FACT_STOCK_PRICES                           │
│      ├── CURATED.DIM_SECURITY                                    │
│      └── MARKET_DATA.DIM_COMPANY                                 │
│                                                                   │
│  CORTEX SEARCH SERVICES (AI Schema)                               │
│  │                                                                │
│  ├── SAM_BROKER_RESEARCH                                         │
│  │   └── CURATED.BROKER_RESEARCH_CORPUS                          │
│  │                                                                │
│  ├── SAM_COMPANY_EVENTS (replaces SAM_EARNINGS_TRANSCRIPTS)      │
│  │   └── CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS                │
│  │       (Real transcripts with EVENT_TYPE attribute)            │
│  │                                                                │
│  ├── SAM_PRESS_RELEASES                                          │
│  │   └── CURATED.PRESS_RELEASES_CORPUS                           │
│  │                                                                │
│  └── SAM_REAL_SEC_FILINGS                                        │
│      └── MARKET_DATA.FACT_SEC_FILING_TEXT                        │
│                                                                   │
│  AGENTS (AI Schema)                                               │
│  │                                                                │
│  ├── portfolio_copilot                                           │
│  │   ├── Tool: quantitative_analyzer ──► SAM_ANALYST_VIEW       │
│  │   ├── Tool: real_stock_prices ─────► SAM_STOCK_PRICES_VIEW   │
│  │   ├── Tool: real_sec_financials ───► SAM_REAL_SEC_VIEW       │
│  │   ├── Tool: search_broker_research ► SAM_BROKER_RESEARCH     │
│  │   ├── Tool: search_company_events ─► SAM_COMPANY_EVENTS      │
│  │   └── Tool: search_press_releases ─► SAM_PRESS_RELEASES      │
│  │                                                                │
│  ├── research_copilot                                            │
│  │   ├── Tool: fundamentals_analyzer ─► SAM_RESEARCH_VIEW       │
│  │   ├── Tool: real_sec_financials ───► SAM_REAL_SEC_VIEW       │
│  │   ├── Tool: search_broker_research ► SAM_BROKER_RESEARCH     │
│  │   ├── Tool: search_company_events ─► SAM_COMPANY_EVENTS      │
│  │   └── Tool: search_real_sec_filings ► SAM_REAL_SEC_FILINGS   │
│  │                                                                │
│  ├── quant_analyst                                               │
│  │   ├── Tool: quantitative_analyzer ─► SAM_ANALYST_VIEW        │
│  │   ├── Tool: real_stock_prices ─────► SAM_STOCK_PRICES_VIEW   │
│  │   └── Tool: search_broker_research ► SAM_BROKER_RESEARCH     │
│  │                                                                │
│  ├── thematic_macro_advisor                                      │
│  │   ├── Tool: quantitative_analyzer ─► SAM_ANALYST_VIEW        │
│  │   ├── Tool: search_broker_research ► SAM_BROKER_RESEARCH     │
│  │   ├── Tool: search_press_releases ─► SAM_PRESS_RELEASES      │
│  │   └── Tool: search_real_sec_filings ► SAM_REAL_SEC_FILINGS   │
│  │                                                                │
│  └── esg_guardian                                                │
│      ├── Tool: quantitative_analyzer ─► SAM_ANALYST_VIEW        │
│      └── Tool: search_real_sec_filings ► SAM_REAL_SEC_FILINGS   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Impact Analysis Matrix

### If You Change... Then You Must...

| Changed Object | Immediate Impact | Must Rebuild/Update |
|----------------|------------------|---------------------|
| **V_REAL_ASSETS** | DIM_ISSUER, DIM_SECURITY break | All downstream tables, all semantic views, all agents |
| **DIM_ISSUER** | All FK references break | DIM_SECURITY, DIM_SUPPLY_CHAIN, all MARKET_DATA tables with IssuerID, all corpus tables, all semantic views |
| **DIM_SECURITY** | Holdings, transactions break | FACT_TRANSACTION, FACT_POSITION_DAILY_ABOR, FACT_ESG_SCORES, FACT_FACTOR_EXPOSURES, FACT_STOCK_PRICES, all corpus tables |
| **DIM_PORTFOLIO** | Holdings, transactions break | FACT_TRANSACTION, FACT_POSITION_DAILY_ABOR |
| **FACT_POSITION_DAILY_ABOR** | Portfolio analytics break | SAM_ANALYST_VIEW, portfolio_copilot |
| **FACT_STOCK_PRICES** | Price analytics break | SAM_STOCK_PRICES_VIEW, agents using real_stock_prices tool |
| **FACT_FINANCIAL_DATA** | Estimate generation breaks | FACT_ESTIMATE_CONSENSUS |
| **FACT_FINANCIAL_DATA_SEC** | SEC analysis breaks | SAM_REAL_SEC_VIEW, agents using real_sec_financials tool |
| **FACT_SEC_FILING_TEXT** | SEC search breaks | SAM_REAL_SEC_FILINGS, agents using search_real_sec_filings tool |
| ***_CORPUS tables** | Document search breaks | Corresponding SAM_* Cortex Search service |
| **SAM_ANALYST_VIEW** | Portfolio queries break | portfolio_copilot, quant_analyst, thematic_macro_advisor, esg_guardian |
| **SAM_REAL_SEC_VIEW** | SEC queries break | research_copilot, portfolio_copilot (real_sec_financials tool) |
| **SAM_STOCK_PRICES_VIEW** | Price queries break | portfolio_copilot, quant_analyst (real_stock_prices tool) |
| **SAM_BROKER_RESEARCH** | Research search breaks | portfolio_copilot, research_copilot, quant_analyst, thematic_macro_advisor |
| **SAM_REAL_SEC_FILINGS** | SEC search breaks | research_copilot, thematic_macro_advisor, esg_guardian |
| **content_library templates** | Document quality changes | Regenerate corpus tables, rebuild search services |
| **config.py DEMO_COMPANIES** | Priority companies change | Transaction generation, document generation, semantic views |

## Module Responsibility Matrix

| Module | Creates | Depends On |
|--------|---------|------------|
| `main.py` | Orchestration | All modules |
| `generate_structured.py` | CURATED dimension/fact tables | extract_real_assets, config |
| `generate_market_data.py` | MARKET_DATA tables | CURATED.DIM_ISSUER, CURATED.DIM_SECURITY, config |
| `generate_unstructured.py` | RAW/*_RAW, CURATED/*_CORPUS | CURATED.DIM_SECURITY, CURATED.DIM_ISSUER, hydration_engine |
| `generate_real_transcripts.py` | COMP_EVENT_SPEAKER_MAPPING, COMPANY_EVENT_TRANSCRIPTS_CORPUS | SNOWFLAKE_PUBLIC_DATA_FREE, CURATED.DIM_SECURITY |
| `hydration_engine.py` | Document content | content_library templates, CURATED dimensions |
| `extract_real_assets.py` | RAW.V_REAL_ASSETS view | REAL_DATA_SOURCES (SNOWFLAKE_PUBLIC_DATA_FREE) |
| `build_ai.py` | AI orchestration | create_semantic_views, create_cortex_search, create_agents |
| `create_semantic_views.py` | AI semantic views | CURATED tables, MARKET_DATA tables |
| `create_cortex_search.py` | AI search services | CURATED corpus tables, MARKET_DATA.FACT_SEC_FILING_TEXT |
| `create_agents.py` | AI agents | Semantic views, search services |

## CIK Linkage Map

The CIK (SEC Central Index Key) is the critical link between internal data and real SEC data:

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
│  └── STOCK_PRICE_TIMESERIES (via ticker, not CIK) ────────────────┤         │
│                                                                    │         │
│                                                                    ▼         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CURATED.DIM_ISSUER.CIK ◄──────────────────────────────────────────┤    │
│  │  │                                                                   │    │
│  │  ├──► MARKET_DATA.DIM_COMPANY.CIK                                   │    │
│  │  │    ├──► FACT_FINANCIAL_DATA_SEC.CIK                              │    │
│  │  │    └──► FACT_SEC_FILING_TEXT.CIK                                 │    │
│  │  │                                                                   │    │
│  │  └──► Enables joins between:                                        │    │
│  │       - Internal holdings (DIM_SECURITY → DIM_ISSUER)               │    │
│  │       - Real SEC financials (FACT_FINANCIAL_DATA_SEC)               │    │
│  │       - Real SEC filings (FACT_SEC_FILING_TEXT)                     │    │
│  │       - Real stock prices (FACT_STOCK_PRICES via ticker)            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Coverage: ~50 companies with CIK linkage (demo companies + major stocks)   │
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
| Market data only | (manual) | MARKET_DATA tables |
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
| `DEMO_COMPANIES` | Priority in transactions, documents |
| `SECURITIES['counts']` | DIM_SECURITY scale |
| `REAL_DATA_SOURCES['enabled']` | Whether real data is loaded |
| `REAL_DATA_SOURCES['tables']` | Real data table references and metadata |
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
| "CIK linkage returns 0 records" | DIM_ISSUER missing CIK | Check V_REAL_ASSETS view, verify SEC_FILINGS access |
| "FACT_ESTIMATE_CONSENSUS fails" | FACT_FINANCIAL_DATA not built | Ensure synthetic data builds before estimates |

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

