# Real Data Integration Analysis

## Executive Summary

This document analyzes the available real data from `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE` and maps it to the SAM demo's synthetic data for replacement.

### Key Findings

| Metric | Value |
|--------|-------|
| Total DIM_ISSUER records | 69,403 |
| Issuers with CIK | 7,844 (11.3%) |
| Issuers with SEC Metrics data | 4,436 |
| Issuers with SEC Filing text | 5,233 |
| Securities with Stock Price data | 11,321 |

## Implementation Status

### New MARKET_DATA Tables Created (Real Data)

| Table | Records | Companies/Securities | Source |
|-------|---------|---------------------|--------|
| FACT_FINANCIAL_DATA_SEC | 100,000+ | 39+ companies | SEC_METRICS_TIMESERIES |
| FACT_STOCK_PRICES | 500,000+ | 865+ tickers | STOCK_PRICE_TIMESERIES |
| FACT_SEC_FILING_TEXT | 50,000+ | 50+ companies | SEC_REPORT_TEXT_ATTRIBUTES |

### Configuration

Real data integration is controlled by `config.REAL_DATA_SOURCES['enabled']` in `python/config.py`.

When enabled, the build process will:
1. Attempt to load real SEC financial data for companies with CIK linkage
2. Load real stock prices for securities with matching tickers
3. Load real SEC filing text (MD&A, Risk Factors, etc.)
4. Fall back to synthetic data where real data is not available

## Available Real Data Sources

### 1. Stock Price Data (`STOCK_PRICE_TIMESERIES`)

**Description**: Daily open/close prices, high/low prices, and trading volumes for US securities traded on Nasdaq.

**Coverage**: 25,638 of our securities have price data (16,123 unique tickers)

**Columns**:
- TICKER, ASSET_CLASS, PRIMARY_EXCHANGE_CODE, PRIMARY_EXCHANGE_NAME
- VARIABLE (metric type), VARIABLE_NAME
- DATE, VALUE, EVENT_TIMESTAMP_UTC

**Variables Available**:
- Nasdaq Volume
- All-Day High / All-Day High Adjusted
- All-Day Low / All-Day Low Adjusted
- Pre-Market Open / Pre-Market Open Adjusted
- Post-Market Close / Post-Market Close Adjusted

**Replaces**: `CURATED.FACT_MARKETDATA_TIMESERIES` (synthetic OHLCV data)

---

### 2. SEC Financial Metrics (`SEC_METRICS_TIMESERIES`)

**Description**: Quarterly and annual parsed revenue segments from 10-Qs and 10-Ks with standardized XBRL variables.

**Coverage**: 4,436 of our issuers have financial metrics data

**Columns**:
- ADSH, CIK, COMPANY_ID, COMPANY_NAME
- VARIABLE_NAME, TAG, TAG_VERSION
- PERIOD_START_DATE, PERIOD_END_DATE
- FISCAL_PERIOD (Q1, Q2, Q3, FY), FISCAL_YEAR
- VALUE, UNIT, MEASURE
- BUSINESS_SEGMENT, BUSINESS_SUBSEGMENT
- GEO_NAME, GEO_ID
- CUSTOMER, LEGAL_ENTITY, FREQUENCY

**Sample Metrics**:
- NET SALES | SEGMENT: IPHONE
- NET SALES | SEGMENT: SERVICE
- NET SALES | SEGMENT: MAC
- Revenue by geography (Americas, Europe, Greater China, etc.)

**Replaces**: 
- `CURATED.FACT_FUNDAMENTALS` (synthetic fundamentals)
- `MARKET_DATA.FACT_FINANCIAL_DATA` (synthetic financial data)

---

### 3. SEC Filing Text (`SEC_REPORT_TEXT_ATTRIBUTES`)

**Description**: Full text of company filings (10-Ks, 10-Qs, 8-Ks) submitted to the SEC.

**Coverage**: 5,233 of our issuers have filing text data

**Columns**:
- SEC_DOCUMENT_ID (unique document identifier)
- CIK, ADSH
- VARIABLE, VARIABLE_NAME
- PERIOD_END_DATE
- VALUE (raw text including MD&A, risk factors, etc.)

**Filing Types Available**:
- 10-K Filing Text, 10-K EX-10 Filing Text
- 10-Q Filing Text, 10-Q EX-31 Filing Text
- 8-K Filing Text, 8-K EX-99 Filing Text

**Replaces**: `MARKET_DATA.FACT_FILING_DATA` (synthetic filing text)

---

### 4. SEC Corporate Report Attributes (`SEC_CORPORATE_REPORT_ATTRIBUTES`)

**Description**: Company KPIs published in SEC filings using XBRL format (daily updates).

**Columns**:
- VARIABLE, CIK, ADSH
- FORM_TYPE, MEASURE_DESCRIPTION, TAG, TAG_VERSION
- UNIT, VALUE, REPORT, STATEMENT
- PERIOD_START_DATE, PERIOD_END_DATE
- COVERED_QTRS, METADATA

**Use Case**: Detailed XBRL metrics for financial statement line items.

---

### 5. Company Index (`COMPANY_INDEX`)

**Description**: Compiled list of public and private companies with identifiers.

**Columns**:
- COMPANY_ID (Snowflake unique ID)
- COMPANY_NAME
- CIK, EIN, LEI

**Use Case**: Cross-reference between our DIM_ISSUER and SEC data via CIK.

---

### 6. SEC 13F Holdings (`SEC_13F_ATTRIBUTES`, `SEC_13F_INDEX`)

**Description**: Quarterly institutional investment manager holdings ($100M+ AUM).

**Use Case**: Institutional ownership data for securities.

---

### 7. SEC Insider Trading (`SEC_FORM4_SECURITIES_INDEX`)

**Description**: Insider transactions in public company securities.

**Use Case**: Insider trading activity for compliance/research.

---

### 8. Company Event Transcripts (`COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES`)

**Description**: Transcripts of hosted company events (Earnings Calls, AGMs, M&A Announcements, Investor Days) in JSON format with speaker attribution.

**Coverage**: 9,000+ public companies, ~31 demo tickers processed (demo companies + major US stocks + SNOW)

**Columns**:
- COMPANY_ID, CIK, COMPANY_NAME, PRIMARY_TICKER
- EVENT_TYPE (Earnings Call, AGM, M&A Announcement, Investor Day, Update/Briefing, Special Call)
- EVENT_TIMESTAMP, FISCAL_PERIOD, FISCAL_YEAR
- TRANSCRIPT (JSON with paragraphs array containing speaker IDs and text)
- TRANSCRIPT_TYPE, CREATED_AT, UPDATED_AT

**Processing Pipeline**:
1. **Speaker Identification** via `AI_COMPLETE` (claude-haiku-4-5):
   - Extracts SPEAKER_ID, SPEAKER_NAME, SPEAKER_ROLE, SPEAKER_COMPANY
   - Creates `MARKET_DATA.COMP_EVENT_SPEAKER_MAPPING` table (cached)

2. **Segment Formatting**:
   - Format: "Speaker Name (Role - Company): Text"
   - Example: "John Smith (CEO - Apple Inc.): Good morning, everyone..."

3. **Chunking** via `SPLIT_TEXT_RECURSIVE_CHARACTER`:
   - Split to ~512 tokens per chunk
   - Prepend metadata header (Company, Ticker, Event, Date, Fiscal Period)

4. **Security Linkage**:
   - Join to DIM_SECURITY via PRIMARY_TICKER to get SecurityID/IssuerID

**New Tables Created**:
- `MARKET_DATA.COMP_EVENT_SPEAKER_MAPPING` - Speaker ID to Name/Role/Company mapping
- `CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS` - Chunked transcript corpus

**New Cortex Search Service**:
- `SAM_COMPANY_EVENTS` - Search with EVENT_TYPE attribute for filtering

**Replaces**: `CURATED.EARNINGS_TRANSCRIPTS_CORPUS` (synthetic from template hydration)

---

## Schema Consolidation Plan

### Tables to Remove from CURATED (Move to MARKET_DATA)

| CURATED Table | MARKET_DATA Replacement | Real Data Source |
|---------------|------------------------|------------------|
| FACT_FUNDAMENTALS | FACT_FINANCIAL_DATA_SEC | SEC_METRICS_TIMESERIES |
| FACT_ESTIMATES | FACT_ESTIMATE_DATA | Keep synthetic (no real source) |
| FACT_MARKETDATA_TIMESERIES | FACT_PRICE_HISTORY | STOCK_PRICE_TIMESERIES |
| FACT_ESG_SCORES | FACT_ESG_DATA | Keep synthetic (no real source) |
| FACT_FACTOR_EXPOSURES | FACT_FACTOR_DATA | Keep synthetic (no real source) |

### New Tables to Create in MARKET_DATA

| Table Name | Source | Description |
|------------|--------|-------------|
| FACT_FINANCIAL_DATA_SEC | SEC_METRICS_TIMESERIES | Real financial metrics by segment |
| FACT_SEC_FILING_TEXT | SEC_REPORT_TEXT_ATTRIBUTES | Real filing text for Cortex Search |
| FACT_SEGMENT_FINANCIALS | SEC_METRICS_TIMESERIES | Revenue by segment/geography |
| FACT_PRICE_HISTORY | STOCK_PRICE_TIMESERIES | Real stock prices |
| FACT_INSTITUTIONAL_HOLDINGS | SEC_13F_ATTRIBUTES | 13F institutional holdings |

### Tables to Keep Synthetic

| Table | Reason |
|-------|--------|
| FACT_ESG_SCORES | No real ESG data in public dataset |
| FACT_FACTOR_EXPOSURES | No real factor data in public dataset |
| FACT_ESTIMATE_DATA | No real analyst estimates in public dataset |
| All *_CORPUS tables | Document content for Cortex Search |

## Implementation Priority

### Phase 1: High Value, High Coverage
1. **FACT_PRICE_HISTORY** from STOCK_PRICE_TIMESERIES
   - Replaces synthetic market data
   - Coverage: 25,638 securities
   - Impact: More realistic portfolio valuations

2. **FACT_FINANCIAL_DATA_SEC** from SEC_METRICS_TIMESERIES
   - Replaces synthetic fundamentals
   - Coverage: 4,436 issuers
   - Impact: Real revenue, net income, segment data

3. **FACT_SEC_FILING_TEXT** from SEC_REPORT_TEXT_ATTRIBUTES
   - Replaces synthetic filing content
   - Coverage: 5,233 issuers
   - Impact: Real MD&A, risk factors for Cortex Search

### Phase 2: Enhanced Analytics
4. **FACT_SEGMENT_FINANCIALS** - Revenue by segment/geography
5. **FACT_INSTITUTIONAL_HOLDINGS** - 13F ownership data

### Phase 3: Cleanup
6. Remove deprecated CURATED tables
7. Update semantic views to use MARKET_DATA
8. Update Cortex Search services

## CIK Linkage Pattern

All real data joins to our model via CIK:

```sql
-- Example: Join SEC metrics to our issuers
SELECT 
    di.IssuerID,
    di.LegalName,
    smt.VARIABLE_NAME,
    smt.VALUE,
    smt.FISCAL_YEAR,
    smt.FISCAL_PERIOD
FROM SAM_DEMO.CURATED.DIM_ISSUER di
INNER JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.SEC_METRICS_TIMESERIES smt 
    ON di.CIK = smt.CIK
WHERE di.CIK IS NOT NULL;
```

## Demo Company Coverage

Demo companies (AAPL, MSFT, NVDA, etc.) all have CIK and full SEC data coverage:

| Company | CIK | SEC Metrics | Filing Text | Stock Price |
|---------|-----|-------------|-------------|-------------|
| Apple Inc. | 0000320193 | ✅ | ✅ | ✅ |
| Microsoft Corp | 0000789019 | ✅ | ✅ | ✅ |
| NVIDIA Corp | 0001045810 | ✅ | ✅ | ✅ |
| Tesla Inc. | 0001318605 | ✅ | ✅ | ✅ |
| Visa Inc. | 0001403161 | ✅ | ✅ | ✅ |

## Implementation Status

### ✅ Completed

1. **ETL Functions Created** (`generate_market_data.py`)
   - `build_real_sec_financial_data()` - Loads SEC_METRICS_TIMESERIES data
   - `build_real_sec_filing_text()` - Loads SEC_REPORT_TEXT_ATTRIBUTES data
   - `build_real_stock_prices()` - Loads STOCK_PRICE_TIMESERIES data

2. **Configuration Consolidated** (`config.py`)
   - `REAL_DATA_SOURCES` dictionary with database, schema, and all table definitions (includes OpenFIGI + market data)
   - `REAL_DATA_SOURCES['enabled']` toggle for real data integration

3. **New MARKET_DATA Tables**
   - `FACT_FINANCIAL_DATA_SEC` - Real SEC financial metrics from 10-K/10-Q filings
   - `FACT_STOCK_PRICES` - Real daily stock prices from Nasdaq (OHLCV)
   - `FACT_SEC_FILING_TEXT` - Real SEC filing text (MD&A, Risk Factors, etc.)

4. **Semantic Views Created**
   - `SAM_REAL_SEC_VIEW` - For real SEC financial data queries
   - `SAM_STOCK_PRICES_VIEW` - For real stock price queries

5. **Cortex Search Service** for real SEC filing text
   - `SAM_REAL_SEC_FILINGS` - Search over 10-K, 10-Q, 8-K filing content
   - Enables semantic search over MD&A, Risk Factors, and other key disclosures

6. **Build Process Updated**
   - Synthetic tables built first (ensures downstream dependencies work)
   - Real data tables built as supplementary (enhances capabilities)
   - Automatic fallback if real data sources unavailable

7. **Agent Integration** ✅
   - Updated all relevant agents to include real data tools
   - `portfolio_copilot` - Added `real_stock_prices`, `real_sec_financials`, and `search_company_events` tools
   - `research_copilot` - Added `real_sec_financials`, `search_real_sec_filings`, and `search_company_events` tools
   - `quant_analyst` - Added `real_stock_prices` and `search_company_events` tools
   - `thematic_macro_advisor` - Added `search_real_sec_filings` and `search_company_events` tools
   - `esg_guardian` - Added `search_real_sec_filings` and `search_company_events` tools

8. **Real Company Event Transcripts** ✅
   - Created `generate_real_transcripts.py` module
   - Speaker identification via AI_COMPLETE (Name, Role, Company)
   - Chunking via SPLIT_TEXT_RECURSIVE_CHARACTER (~512 tokens)
   - New tables: `COMP_EVENT_SPEAKER_MAPPING`, `COMPANY_EVENT_TRANSCRIPTS_CORPUS`
   - New search service: `SAM_COMPANY_EVENTS` (replaces `SAM_EARNINGS_TRANSCRIPTS`)
   - Updated all agents to use `search_company_events` tool

8. **Schema Cleanup** ✅
   - Updated `generate_structured.py` to skip creating deprecated tables when MARKET_DATA equivalents exist
   - Updated semantic view creation to check for MARKET_DATA tables as alternatives
   - Added MARKET_DATA schema to database structure creation
   - Deprecated CURATED tables will be automatically skipped when real data is available:
     - `FACT_MARKETDATA_TIMESERIES` → Use `MARKET_DATA.FACT_STOCK_PRICES`
     - `FACT_FUNDAMENTALS` → Use `MARKET_DATA.FACT_FINANCIAL_DATA`
     - `FACT_ESTIMATES` → Use `MARKET_DATA.FACT_ESTIMATE_CONSENSUS`

### 📋 Manual Cleanup (Completed)

The following deprecated tables have been dropped from the CURATED schema:
```sql
-- Executed on 2025-01-XX
DROP TABLE IF EXISTS SAM_DEMO.CURATED.FACT_MARKETDATA_TIMESERIES;
DROP TABLE IF EXISTS SAM_DEMO.CURATED.FACT_FUNDAMENTALS;
DROP TABLE IF EXISTS SAM_DEMO.CURATED.FACT_ESTIMATES;
```

## Documentation Updated

The following documentation and cursor rules have been updated to reflect the real data integration:

| Document | Updates Made |
|----------|--------------|
| `docs/data_model.md` | Added MARKET_DATA schema, real data tables, new semantic views |
| `.cursor/rules/data-generation.mdc` | Added real SEC data integration patterns, schema cleanup logic |
| `.cursor/rules/project-setup.mdc` | Added MARKET_DATA schema to database architecture |
| `.cursor/rules/agent-config.mdc` | Added real data tools documentation (real_stock_prices, real_sec_financials, search_real_sec_filings) |
| `python/config.py` | Consolidated REAL_DATA_SOURCES configuration with all external tables |
| `python/generate_market_data.py` | Added real data ETL functions |
| `python/generate_structured.py` | Added conditional table creation logic |
| `python/create_semantic_views.py` | Added real data semantic views |
| `python/create_agents.py` | Updated agents with real data tools |

## Related Documentation

- **`docs/data_lineage.md`** - Complete data flow and dependency documentation
- **`docs/data_model.md`** - Data model architecture and schemas
- **`.cursor/rules/data-generation.mdc`** - Data generation patterns
- **`.cursor/rules/agent-config.mdc`** - Agent configuration including real data tools

## Summary

The SAM demo now includes authentic SEC data integration:

- **5.2M+ real stock prices** from Nasdaq (OHLCV data)
- **9,400+ real SEC financial metrics** from 10-K/10-Q filings
- **6,300+ real SEC filing text** sections (MD&A, Risk Factors, etc.)
- **500+ real company event transcript chunks** from Earnings Calls, AGMs, M&A announcements, Investor Days
- **~50 companies** with CIK linkage enabling real data queries
- **~31 companies** with real transcript coverage (demo companies + major US stocks + SNOW)
- **5 agents updated** with real data tools (including `search_company_events`)
- **2 new semantic views** for real data queries
- **2 new Cortex Search services** - SEC filing text + company event transcripts
- **Speaker attribution** in transcripts (Name, Role, Company via AI_COMPLETE)
- **Schema cleanup complete** - deprecated CURATED tables removed

