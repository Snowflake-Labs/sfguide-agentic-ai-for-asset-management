# SAM Demo - Data Model Documentation

Data architecture documentation for Snowcrest Asset Management (SAM) demo using 79 real companies from `DEMO_COMPANIES` configuration with industry-standard asset management data practices. All companies have CIK identifiers enabling full SEC data integration.

## Database Architecture

**Database**: `SAM_DEMO`

**Schemas**:
- **RAW**: Provider simulation and raw unstructured documents
- **CURATED**: Industry-standard dimension/fact model ready for analysis
- **MARKET_DATA**: Real market data from SNOWFLAKE_PUBLIC_DATA_FREE
- **AI**: Semantic views and Cortex Search services

## CURATED Schema

### Dimension Tables

| Table | Description |
|-------|-------------|
| `DIM_ISSUER` | 79 real issuers from DEMO_COMPANIES, all with CIK identifiers for SEC data linkage |
| `DIM_SECURITY` | Securities derived from DIM_ISSUER with ticker identifiers (1:1 with issuers) |
| `DIM_PORTFOLIO` | 10 portfolios with strategy, currency, and inception date |
| `DIM_BENCHMARK` | 3 benchmarks: S&P 500, MSCI ACWI, Nasdaq 100 |
| `DIM_SUPPLY_CHAIN_RELATIONSHIPS` | Supply chain relationships between issuers |
| `DIM_CLIENT` | Client dimension with flow pattern indicators (at-risk clients with declining flows, new clients with onboarding tracking) |
| `DIM_CLIENT_MANDATES` | Client mandate constraints and requirements |
| `DIM_COUNTERPARTY` | Trading counterparty reference data |
| `DIM_CUSTODIAN` | Custodian reference data |

### Core Fact Tables

| Table | Description |
|-------|-------------|
| `FACT_TRANSACTION` | Canonical transaction log with 12 months history |
| `FACT_POSITION_DAILY_ABOR` | Daily ABOR positions derived from transactions |
| `FACT_ESG_SCORES` | Monthly ESG ratings with sector differentiation |
| `FACT_FACTOR_EXPOSURES` | Monthly factor scores (Value, Growth, Quality, etc.) |
| `FACT_BENCHMARK_HOLDINGS` | Benchmark constituent positions |
| `FACT_BENCHMARK_PERFORMANCE` | Benchmark-level returns (MTD, QTD, YTD) for portfolio vs benchmark comparison |

### Implementation Planning Tables

| Table | Description |
|-------|-------------|
| `FACT_TRANSACTION_COSTS` | Trading costs, bid-ask spreads, market impact data |
| `FACT_PORTFOLIO_LIQUIDITY` | Cash positions, cash flows, liquidity scores |
| `FACT_RISK_LIMITS` | Risk budgets, tracking error limits, concentration limits |
| `FACT_TRADING_CALENDAR` | Earnings dates, blackout periods, market events |
| `FACT_TAX_IMPLICATIONS` | Cost basis, unrealized gains, tax loss harvesting |

### Executive and Client Analytics Tables

| Table | Description |
|-------|-------------|
| `FACT_CLIENT_FLOWS` | Client subscription and redemption flows with differentiated patterns (at-risk clients show declining/redemption trends, new clients have short flow history) |
| `FACT_FUND_FLOWS` | Aggregate fund-level flow data |
| `FACT_STRATEGY_PERFORMANCE` | Strategy-level performance metrics |
| `FACT_COMPLIANCE_ALERTS` | Compliance alert history |
| `FACT_PRE_SCREENED_REPLACEMENTS` | Pre-approved security replacements |

### Middle Office Operations Tables

| Table | Description |
|-------|-------------|
| `FACT_TRADE_SETTLEMENT` | Trade settlement status and history |
| `FACT_RECONCILIATION` | Position and cash reconciliation data |
| `FACT_NAV_CALCULATION` | NAV calculation results |
| `FACT_NAV_COMPONENTS` | NAV component breakdown |
| `FACT_CORPORATE_ACTIONS` | Corporate action events |
| `FACT_CORPORATE_ACTION_IMPACT` | Corporate action portfolio impact |
| `FACT_CASH_MOVEMENTS` | Cash movement transactions |
| `FACT_CASH_POSITIONS` | Daily cash position snapshots |

### Views

| View | Description |
|------|-------------|
| `V_HOLDINGS_WITH_ESG` | Holdings enriched with latest ESG scores |
| `V_SECURITY_RETURNS` | Securities with calculated returns from price data |

### Document Corpus Tables

| Corpus Table | Search Service | Linkage Level |
|--------------|----------------|---------------|
| `BROKER_RESEARCH_CORPUS` | `SAM_BROKER_RESEARCH` | Security |
| `COMPANY_EVENT_TRANSCRIPTS_CORPUS` | `SAM_COMPANY_EVENTS` | Security (real data) |
| `PRESS_RELEASES_CORPUS` | `SAM_PRESS_RELEASES` | Security |
| `NGO_REPORTS_CORPUS` | `SAM_NGO_REPORTS` | Issuer |
| `ENGAGEMENT_NOTES_CORPUS` | `SAM_ENGAGEMENT_NOTES` | Issuer |
| `POLICY_DOCS_CORPUS` | `SAM_POLICY_DOCS` | Global |
| `SALES_TEMPLATES_CORPUS` | `SAM_SALES_TEMPLATES` | Global |
| `PHILOSOPHY_DOCS_CORPUS` | `SAM_PHILOSOPHY_DOCS` | Global |
| `REPORT_TEMPLATES_CORPUS` | `SAM_REPORT_TEMPLATES` | Global |
| `MACRO_EVENTS_CORPUS` | `SAM_MACRO_EVENTS` | Global |
| `CUSTODIAN_REPORTS_CORPUS` | `SAM_CUSTODIAN_REPORTS` | Portfolio |
| `RECONCILIATION_NOTES_CORPUS` | `SAM_RECONCILIATION_NOTES` | Global |
| `SSI_DOCUMENTS_CORPUS` | `SAM_SSI_DOCUMENTS` | Global |
| `OPS_PROCEDURES_CORPUS` | `SAM_OPS_PROCEDURES` | Global |
| `STRATEGY_DOCUMENTS_CORPUS` | `SAM_STRATEGY_DOCUMENTS` | Global |

## MARKET_DATA Schema

### Reference Tables

| Table | Description |
|-------|-------------|
| `DIM_ANALYST` | Broker analyst dimension |
| `DIM_BROKER` | Broker/research firm dimension |

**Note**: Company master data is provided by `CURATED.DIM_ISSUER` - there is no separate `DIM_COMPANY` table. `DIM_ISSUER` is the single source of truth for all company/issuer information.

### Real SEC Data (Primary Source)

Data sourced from `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`. All 79 companies have CIK identifiers enabling full SEC data linkage. **This is now the primary source for financial data.**

| Table | Source Table | Description |
|-------|--------------|-------------|
| `FACT_SEC_FINANCIALS` | `SEC_CORPORATE_REPORT_ATTRIBUTES` | **Primary financial data table**. Comprehensive financial statements with XBRL tags including Income Statement, Balance Sheet, Cash Flow, calculated ratios (margins, ROE, ROA), and heuristically calculated Investment Memo Metrics (TAM, Customer Count, NRR). Powers `SAM_FUNDAMENTALS_VIEW` and provides base actuals for `FACT_ESTIMATE_CONSENSUS`. |
| `FACT_SEC_SEGMENTS` | `SEC_METRICS_TIMESERIES` | **Revenue segment breakdowns** by geography (Europe, Americas, Asia Pacific), business segment, customer, and legal entity. Enables competitor regional analysis (e.g., BlackRock European revenue ~$6B). Used by `SAM_SEC_FINANCIALS_VIEW` for geographic and divisional revenue queries. |
| `FACT_STOCK_PRICES` | `STOCK_PRICE_TIMESERIES` | Real daily stock prices (OHLCV) from Nasdaq |
| `FACT_SEC_FILING_TEXT` | `SEC_REPORT_TEXT_ATTRIBUTES` | SEC filing text (MD&A, Risk Factors) |
| `COMP_EVENT_SPEAKER_MAPPING` | AI-processed | Speaker identification from transcripts |

### Investment Memo Metrics (Calculated from Real SEC Data)

The following metrics are calculated heuristically from real SEC data in `FACT_SEC_FINANCIALS`:

| Metric | Calculation | Rationale |
|--------|-------------|-----------|
| `TAM` | Revenue × Industry Multiplier (15-35x) | Standard market sizing approach based on industry |
| `ESTIMATED_CUSTOMER_COUNT` | Revenue / ARPC (varies by industry) | Implied customer base from revenue |
| `ESTIMATED_NRR_PCT` | 100 + Revenue Growth %, capped at 90-140% | SaaS-style NRR correlates with revenue growth |

### Analyst Data

| Table | Description |
|-------|-------------|
| `FACT_ESTIMATE_CONSENSUS` | Analyst estimate consensus **derived from real SEC actuals** in `FACT_SEC_FINANCIALS` |
| `FACT_ESTIMATE_DATA` | Individual analyst estimates |
| `FACT_ANALYST_COVERAGE` | Analyst coverage mapping |

## AI Schema

### Semantic Views

| Semantic View | Description | Key Tables |
|---------------|-------------|------------|
| `SAM_ANALYST_VIEW` | Portfolio analytics with factor analysis | `V_HOLDINGS_WITH_ESG`, `DIM_PORTFOLIO`, `DIM_SECURITY`, `DIM_ISSUER`, `FACT_FACTOR_EXPOSURES`, `FACT_BENCHMARK_HOLDINGS` |
| `SAM_FUNDAMENTALS_VIEW` | Financial analysis | `FACT_SEC_FINANCIALS`, `FACT_ESTIMATE_CONSENSUS`, `DIM_ISSUER` (uses real SEC data with calculated TAM/NRR) |
| `SAM_IMPLEMENTATION_VIEW` | Trading implementation | `FACT_TRANSACTION_COSTS`, `FACT_PORTFOLIO_LIQUIDITY`, `FACT_RISK_LIMITS` |
| `SAM_SUPPLY_CHAIN_VIEW` | Supply chain risk | `DIM_SUPPLY_CHAIN_RELATIONSHIPS`, `DIM_ISSUER` |
| `SAM_MIDDLE_OFFICE_VIEW` | Operations monitoring | `FACT_TRADE_SETTLEMENT`, `FACT_RECONCILIATION`, `FACT_NAV_CALCULATION`, `FACT_CORPORATE_ACTIONS`, `FACT_CASH_MOVEMENTS`, `FACT_CASH_POSITIONS`, `DIM_COUNTERPARTY` |
| `SAM_COMPLIANCE_VIEW` | Breach tracking | `FACT_COMPLIANCE_ALERTS`, `FACT_RISK_LIMITS` |
| `SAM_EXECUTIVE_VIEW` | Firm-wide KPIs | `FACT_CLIENT_FLOWS`, `FACT_FUND_FLOWS`, `FACT_STRATEGY_PERFORMANCE` |
| `SAM_STOCK_PRICES_VIEW` | Real stock prices | `FACT_STOCK_PRICES`, `DIM_SECURITY`, `DIM_ISSUER` |
| `SAM_SEC_FINANCIALS_VIEW` | Comprehensive SEC data | `FACT_SEC_FINANCIALS`, `DIM_ISSUER` |

### Cortex Search Services

| Search Service | Corpus Table | Description |
|----------------|--------------|-------------|
| `SAM_BROKER_RESEARCH` | `BROKER_RESEARCH_CORPUS` | Analyst reports |
| `SAM_COMPANY_EVENTS` | `COMPANY_EVENT_TRANSCRIPTS_CORPUS` | Real company event transcripts |
| `SAM_PRESS_RELEASES` | `PRESS_RELEASES_CORPUS` | Corporate announcements |
| `SAM_NGO_REPORTS` | `NGO_REPORTS_CORPUS` | ESG controversy reports |
| `SAM_ENGAGEMENT_NOTES` | `ENGAGEMENT_NOTES_CORPUS` | Corporate engagement notes |
| `SAM_POLICY_DOCS` | `POLICY_DOCS_CORPUS` | Investment policies |
| `SAM_SALES_TEMPLATES` | `SALES_TEMPLATES_CORPUS` | Client materials |
| `SAM_PHILOSOPHY_DOCS` | `PHILOSOPHY_DOCS_CORPUS` | Investment philosophy |
| `SAM_REPORT_TEMPLATES` | `REPORT_TEMPLATES_CORPUS` | Report templates |
| `SAM_MACRO_EVENTS` | `MACRO_EVENTS_CORPUS` | Macro event notifications |
| `SAM_CUSTODIAN_REPORTS` | `CUSTODIAN_REPORTS_CORPUS` | Custodian reports |
| `SAM_RECONCILIATION_NOTES` | `RECONCILIATION_NOTES_CORPUS` | Reconciliation notes |
| `SAM_SSI_DOCUMENTS` | `SSI_DOCUMENTS_CORPUS` | Settlement instructions |
| `SAM_OPS_PROCEDURES` | `OPS_PROCEDURES_CORPUS` | Operations procedures |
| `SAM_STRATEGY_DOCUMENTS` | `STRATEGY_DOCUMENTS_CORPUS` | Strategy documents |
| `SAM_REAL_SEC_FILINGS` | `FACT_SEC_FILING_TEXT` | Real SEC filing text |

### Agents

| Agent | Display Name | Key Tools |
|-------|--------------|-----------|
| `AM_portfolio_copilot` | Portfolio Co-Pilot | quantitative_analyzer, stock_prices, sec_financials, search services |
| `AM_research_copilot` | Research Analyst | fundamentals_analyzer, sec_financials, search services |
| `AM_thematic_macro_advisor` | Thematic Macro Advisor | quantitative_analyzer, search services |
| `AM_esg_guardian` | ESG Guardian | quantitative_analyzer, search_sec_filings |
| `AM_compliance_advisor` | Compliance Advisor | compliance tools, policy search |
| `AM_sales_advisor` | Sales Advisor | quantitative_analyzer, search services |
| `AM_quant_analyst` | Quant Analyst | quantitative_analyzer, stock_prices, search services |
| `AM_middle_office_copilot` | Middle Office Co-Pilot | middle office tools, operations search |
| `AM_executive_copilot` | Executive Co-Pilot | executive analytics, strategy search |

## Data Quality Standards

### Validation Rules

- **Portfolio Weights**: Sum to 100% (±0.1% tolerance)
- **Transaction Integrity**: Transaction log balances to ABOR positions
- **Security Identifiers**: Ticker columns properly populated
- **Price Data**: No negative prices, realistic ranges by asset class
- **Date Consistency**: Business days only, proper date ranges
- **Foreign Key Relationships**: All relationships valid

## Sample Data Characteristics

### Portfolios
- SAM Global Flagship Multi-Asset
- SAM ESG Leaders Global Equity
- SAM Global Thematic Growth
- SAM Technology & Infrastructure
- And 6 additional strategies

### Companies (79 total, all with CIK)
- **Core Demo Companies** (8): AAPL, MSFT, NVDA, GOOGL, TSM, SNOW, CMC, RBBN
- **Major US Stocks** (~40): AMZN, META, TSLA, AMD, INTC, etc.
- **Additional Companies** (~31): Sector diversity

### Coverage
- US: ~55%
- Europe: ~30%
- APAC/EM: ~15%

## Related Documentation

- [`docs/data_lineage.md`](data_lineage.md) - Data flow, dependencies, and impact analysis
- [`.cursor/rules/data-index.mdc`](../.cursor/rules/data-index.mdc) - Data generation patterns (index to related rules)
