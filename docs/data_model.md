# SAM Demo - Data Model Documentation

Data architecture documentation for Simulated Asset Management (SAM) demo using 79 real companies from `DEMO_COMPANIES` configuration with industry-standard asset management data practices. All companies have CIK identifiers enabling full SEC data integration.

**Pipeline-Only Architecture**: All unstructured data flows exclusively through Snowflake pipelines (no direct SQL corpus creation). PDF documents are parsed via `AI_PARSE_DOCUMENT`, real data triggers stream-based task DAGs, and all corpus tables are populated by pipeline tasks.

**Real Data Sourcing**: Market data, SEC filings, and macroeconomic indicators are sourced from Cybersyn (Snowflake Marketplace). Dividend data is extracted from SEC 8-K filings using `AI_EXTRACT`. Historical data range is controlled by `config.YEARS_OF_HISTORY` (default: 5 years).

## Database Architecture

**Database**: `SAM_DEMO`

**Schemas**:
| Schema | Objects | Description |
|--------|---------|-------------|
| **RAW** | 17 tables, stages, streams, tasks | Provider simulation, raw unstructured documents, pipeline objects |
| **CURATED** | 55 tables, 8 views | Industry-standard dimension/fact model ready for analysis |
| **MARKET_DATA** | 17+ tables | Real market data from Snowflake Marketplace + AI-extracted dividends + NLP scores |
| **AI** | 28 semantic views (YAML-based), search services, agents | AI components |

**Warehouses**:
| Warehouse | Size | Purpose |
|-----------|------|---------|
| `SAM_DEMO_EXECUTION_WH` | MEDIUM | Data generation and execution |
| `SAM_DEMO_CORTEX_WH` | MEDIUM | Cortex Search services (5-minute target lag) |

---

## CURATED Schema

### Dimension Tables

| Table | Description | Key Columns | Source |
|-------|-------------|-------------|--------|
| `DIM_ISSUER` | 79 real issuers - single source of truth for company data | IssuerID, CIK, LegalName, PrimaryTicker, GICS_SECTOR | config.DEMO_COMPANIES + Cybersyn |
| `DIM_SECURITY` | Securities derived from DIM_ISSUER (1:1 with issuers) | SecurityID, IssuerID, Ticker, AssetClass, CUSIP | Derived from DIM_ISSUER |
| `DIM_PORTFOLIO` | 11 portfolios with strategy, currency, and inception date | PortfolioID, PortfolioName, Strategy, BenchmarkID | config.PORTFOLIOS |
| `DIM_BENCHMARK` | 3 benchmarks: S&P 500, MSCI ACWI, Nasdaq 100 | BenchmarkID, BenchmarkName | Synthetic |
| `DIM_SUPPLY_CHAIN_RELATIONSHIPS` | Supply chain network between issuers | CompanyID, CounterpartyID, RelationshipType, CostShare | config.SUPPLY_CHAIN_* |
| `DIM_CLIENT` | Institutional clients with flow patterns | ClientID, ClientName, ClientType, Region, AUM | config.DEMO_CLIENTS + synthetic |
| `DIM_CLIENT_MANDATES` | Client mandate constraints and requirements | MandateID, ClientID, MaxConcentration, MinESGGrade | Synthetic |
| `DIM_COUNTERPARTY` | Trading counterparty reference data | CounterpartyID, CounterpartyName, CounterpartyType | Synthetic |
| `DIM_CUSTODIAN` | Custodian reference data | CustodianID, CustodianName | Synthetic |
| `DIM_MODEL_PORTFOLIO` | User-defined model portfolios for backtesting | ModelID, ModelName, Strategy | Synthetic |
| `DIM_DEAL_PIPELINE` | Active PE deal pipeline for sourcing analysis | DealID, TargetName, Stage, ExpectedClose | Synthetic |
| `DIM_PORTFOLIO_COMPANY` | PE portfolio companies for value creation monitoring | CompanyID, CompanyName, Sector, InvestmentDate | Synthetic |
| `DIM_STRESS_SCENARIOS` | Stress scenario definitions (10 scenarios) | ScenarioID, ScenarioName, Severity | Synthetic |
| `DIM_PORTFOLIO_IPS` | Investment Policy Statements with risk profile constraints | IPSID, PortfolioID, RiskProfile, MaxSingleIssuerPct | config.DOCUMENT_TYPES['ips'] |

### Core Fact Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `FACT_TRANSACTION` | Canonical transaction log (YEARS_OF_HISTORY) | TransactionID, SecurityID, PortfolioID, TransactionType, Quantity |
| `FACT_POSITION_DAILY_ABOR` | Daily ABOR positions derived from transactions | PositionID, SecurityID, PortfolioID, HoldingDate, Quantity, MarketValue |
| `FACT_ESG_SCORES` | Monthly ESG ratings with sector differentiation | SecurityID, E_Score, S_Score, G_Score, OverallGrade |
| `FACT_FACTOR_EXPOSURES` | Monthly factor scores (Value, Growth, Quality, etc.) | SecurityID, FactorName, Exposure, RSquared |
| `FACT_BENCHMARK_HOLDINGS` | Benchmark constituent positions | BenchmarkID, SecurityID, Weight |
| `FACT_BENCHMARK_PERFORMANCE` | Benchmark-level returns (MTD, QTD, YTD) | BenchmarkID, Date, DailyReturn |
| `FACT_INSIDER_TRANSACTIONS` | SEC Form 4 insider trading for demo companies | InsiderTxID, CIK, Ticker, TransactionType, TransactionShares |
| `FACT_INSTITUTIONAL_HOLDINGS` | SEC 13F institutional ownership | HoldingID, Ticker, InstitutionName, MarketValueUSD, SharesHeld |

### Implementation Planning Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `FACT_TRANSACTION_COSTS` | Trading costs, bid-ask spreads, market impact | SecurityID, BidAskSpread, MarketImpact, AvgDailyVolume |
| `FACT_PORTFOLIO_LIQUIDITY` | Cash positions, cash flows, liquidity scores | PortfolioID, CashPosition, LiquidityScore |
| `FACT_RISK_LIMITS` | Risk budgets, tracking error limits | PortfolioID, TrackingErrorLimit, ConcentrationLimit |
| `FACT_TRADING_CALENDAR` | Earnings dates, blackout periods, market events | Date, IsBlackout, ExpectedVolatility |
| `FACT_TAX_IMPLICATIONS` | Cost basis, unrealized gains, tax lot data | PositionID, CostBasis, UnrealizedGain, HoldingPeriod |

### Executive and Client Analytics Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `FACT_CLIENT_FLOWS` | Client subscription/redemption flows | FlowID, ClientID, PortfolioID, FlowType, Amount |
| `FACT_FUND_FLOWS` | Aggregate fund-level flow data | FundID, Date, NetFlow, AUM |
| `FACT_STRATEGY_PERFORMANCE` | Strategy-level performance metrics | StrategyID, Date, Return, Alpha, Beta |
| `FACT_COMPLIANCE_ALERTS` | Compliance alert history with IPS references | AlertID, PortfolioID, AlertType, Severity, IPSSection, IPSLimitValue |
| `FACT_PRE_SCREENED_REPLACEMENTS` | Pre-approved security replacements | SecurityID, ReplacementSecurityID, Rationale |

### Middle Office Operations Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `FACT_TRADE_SETTLEMENT` | Trade settlement status and history | SettlementID, TradeDate, SettlementDate, Status |
| `FACT_RECONCILIATION` | Position and cash reconciliation data | ReconciliationID, BreakType, BreakAmount, Status |
| `FACT_NAV_CALCULATION` | NAV calculation results | PortfolioID, Date, GrossNAV, NetNAV |
| `FACT_NAV_COMPONENTS` | NAV component breakdown | ComponentID, PortfolioID, ComponentType, Value |
| `FACT_CORPORATE_ACTIONS` | Corporate action events (uses real dividends from MARKET_DATA.FACT_DIVIDENDS) | ActionID, SecurityID, ActionType, ExDate, RecordDate, PaymentDate |
| `FACT_CORPORATE_ACTION_IMPACT` | Corporate action portfolio impact | ImpactID, ActionID, PositionID, Adjustment |
| `FACT_CASH_MOVEMENTS` | Cash movement transactions | MovementID, PortfolioID, MovementType, Amount |
| `FACT_CASH_POSITIONS` | Daily cash position snapshots | PortfolioID, Currency, Balance, AvailableBalance |

### Portfolio Modelling Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `FACT_MODEL_PORTFOLIO_WEIGHTS` | Target weights for model portfolios | ModelID, SecurityID, TargetWeight |
| `FACT_RISK_FACTORS` | Risk factor definitions and loadings | FactorID, FactorName, FactorReturn |
| `FACT_EXPECTED_RETURNS` | Forward-looking return expectations | SecurityID, ExpectedReturn, Confidence |
| `FACT_COVARIANCE_MATRIX` | Security return covariance for risk | SecurityID1, SecurityID2, Covariance |
| `FACT_BACKTEST_RESULTS` | Historical backtest results | BacktestID, PortfolioID, StartDate, EndDate, Return |
| `FACT_SIMULATION_RESULTS` | Monte Carlo simulation results | SimulationID, PathID, Date, PortfolioValue |

### Portfolio Manager Co-Pilot Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `FACT_BRINSON_ATTRIBUTION` | Portfolio-level Brinson decomposition | PortfolioID, Date, ActiveReturn, AllocationEffect, SelectionEffect |
| `FACT_BRINSON_BY_SECTOR` | Sector-level Brinson attribution | PortfolioID, Sector, AllocationEffect, SelectionEffect |
| `FACT_FACTOR_ATTRIBUTION` | Factor-based performance attribution | PortfolioID, FactorName, Exposure, Contribution |
| `FACT_HIDDEN_FACTOR_EXPOSURES` | AI-detected hidden factors (AI_Exposure, Reshoring_Benefit, etc.) | PortfolioID, HiddenFactor, Exposure, ExplanatoryPower |
| `FACT_SCENARIO_SHOCKS` | Factor shocks per stress scenario | ScenarioID, FactorName, Shock, Confidence |
| `FACT_HISTORICAL_STRESS_PERIODS` | Historical crises | PeriodID, StartDate, EndDate, MarketReturn, PeakVIX |

### Private Equity Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `FACT_VALUE_CREATION_PLAN` | Value creation initiatives | PlanID, CompanyID, Initiative, TargetValue |
| `FACT_BOARD_PACK_METRICS` | Monthly board pack KPIs | MetricID, CompanyID, MetricName, Value |
| `FACT_PORTFOLIO_COMPANY_KPI` | Operational KPIs | KPIID, CompanyID, KPIName, Value, Target |

### Views

| View | Description | Base Tables |
|------|-------------|-------------|
| `V_SECURITY_RETURNS` | Daily security returns | FACT_STOCK_PRICES |
| `V_SECURITY_RETURNS_LATEST` | Latest returns | FACT_STOCK_PRICES |
| `V_SECURITY_LOG_RETURNS` | Log returns | FACT_STOCK_PRICES |
| `V_PORTFOLIO_RISK_METRICS` | Portfolio risk summary | Multiple |
| `V_ESG_LATEST` | Latest ESG scores | FACT_ESG_SCORES |
| `V_HOLDINGS_WITH_ESG` | Holdings + ESG | FACT_POSITION_DAILY_ABOR, FACT_ESG_SCORES |
| `V_PORTFOLIO_BENCHMARK_COMPARISON` | Portfolio vs benchmark | Multiple |
| `V_MACRO_REGIME` | Market regime classification (RISK_ON, RISK_OFF, etc.) | FACT_VIX_DAILY, FACT_BENCHMARK_RETURNS |

### Document Corpus Tables (for Cortex Search)

PDF-based document types are consolidated into 2 shared corpus tables. Agent-side filtering via `filter: {"@eq": {"DOCUMENT_TYPE": "<doc_type>"}}` scopes each search tool to its document type.

| Corpus Table | Search Service | Doc Types / Linkage |
|--------------|----------------|--------------------|
| `PDF_INTERNAL_CORPUS` | `SAM_INTERNAL_DOCS` | 13 types: policy_docs, sales_templates, philosophy_docs, report_templates, macro_events, custodian_reports, reconciliation_notes, ssi_documents, ops_procedures, strategy_documents, methodology_docs, engagement_notes, ips. Filtered by DOCUMENT_TYPE. |
| `PDF_EXTERNAL_CORPUS` | `SAM_EXTERNAL_DOCS` | 3 types: broker_research, press_releases, ngo_reports. Filtered by DOCUMENT_TYPE. |
| `COMPANY_EVENT_TRANSCRIPTS_CORPUS` | `SAM_COMPANY_EVENTS` | Security (real data) |
| `FACT_SEC_FILING_TEXT` | `SAM_REAL_SEC_FILINGS` | Security (real data) |
| `PE_BOARD_PACKS_CORPUS` | `SAM_PE_BOARD_PACKS` | Portfolio Company |
| `PE_DUE_DILIGENCE_CORPUS` | `SAM_PE_DUE_DILIGENCE` | Deal |
| `PE_EXPERT_NETWORK_CORPUS` | `SAM_PE_EXPERT_NETWORK` | Deal |
| `CREDIT_AGREEMENTS_CORPUS` | `SAM_CREDIT_AGREEMENTS` | Facility |
| `COMPLIANCE_CERTS_CORPUS` | `SAM_COMPLIANCE_CERTS` | Borrower |
| `IC_MEMOS_CORPUS` | `SAM_IC_MEMOS` | Deal |

---

## MARKET_DATA Schema

All real data is sourced from Snowflake Marketplace. Historical range controlled by `config.YEARS_OF_HISTORY` (default: 5 years).

### Reference Tables

| Table | Description | Source |
|-------|-------------|--------|
| `DIM_ANALYST` | Broker analyst dimension | Synthetic |
| `DIM_BENCHMARKS` | Benchmark reference (SPY, IVV, QQQ, IWM, EFA) | Synthetic |

### Real SEC Data (Primary Source)

| Table | Cybersyn Source | Description |
|-------|-----------------|-------------|
| `FACT_STOCK_PRICES` | `STOCK_PRICE_TIMESERIES` | Daily OHLCV prices from Nasdaq |
| `FACT_SEC_FILING_TEXT` | `SEC_REPORT_TEXT_ATTRIBUTES` | SEC filing text (MD&A, Risk Factors, 10-K, 10-Q, 8-K) |
| `FACT_SEC_FINANCIALS` | `SEC_CORPORATE_REPORT_ATTRIBUTES` | Complete XBRL financial statements with calculated ratios and Investment Memo metrics (TAM, NRR, Customer Count) |
| `FACT_SEC_SEGMENTS` | `SEC_METRICS_TIMESERIES` | Revenue segments by geography, business unit, customer, legal entity |
| `COMP_EVENT_SPEAKER_MAPPING` | AI-processed | Speaker identification from transcripts |

### Dividend Data (AI-Extracted from SEC 8-K)

| Table | Source | Description |
|-------|--------|-------------|
| `FACT_DIVIDENDS` | `SEC_REPORT_TEXT_ATTRIBUTES` (8-K filings) + **AI_EXTRACT** | Dividend declarations with AI-extracted dates |

**AI_EXTRACT Pipeline**:
```
SEC 8-K Filing Text → AI_EXTRACT → Structured Dividend Data
                      
Extracts:
- DECLARATION_DATE: Date board declared the dividend
- DIVIDEND_PER_SHARE: Dollar amount per share
- RECORD_DATE: Shareholder eligibility date  
- PAYMENT_DATE: Date dividend will be paid

Calculates:
- EX_DATE: 1 business day before RECORD_DATE (SEC T+1 rule)
  - If Monday: Ex-Date = Friday (skip weekend)
  - If Sunday: Ex-Date = Thursday (skip weekend)
```

### Macroeconomic Data (Real from Cybersyn)

| Table | Cybersyn Source | Description |
|-------|-----------------|-------------|
| `FACT_POLICY_RATES` | `BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES` | Central bank policy rates (Fed, ECB, BOE, BOJ, etc.) |
| `FACT_FX_RATES` | `FX_RATES_TIMESERIES` | Foreign exchange rates (EURUSD, GBPUSD, USDJPY, etc.) |
| `FACT_ECONOMIC_INDICATORS` | `CYBERSYN_FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES` | US economic indicators from FRED (GDP, CPI, unemployment) |
| `FACT_TREASURY_YIELDS` | `US_TREASURY_PAR_YIELD_CURVE_RATES` | US Treasury yield curve rates (14 maturities, 1M-30Y) |
| `FACT_COUNTRY_EMISSIONS` | `CLIMATE_WATCH_GHG_EMISSIONS_TIMESERIES` | Country-level greenhouse gas emissions by sector (190+ countries) |

### Portfolio Manager Co-Pilot Market Data

| Table | Description | Source |
|-------|-------------|--------|
| `FACT_BENCHMARK_RETURNS` | Daily benchmark returns | Synthetic |
| `FACT_BENCHMARK_SECTOR_WEIGHTS` | Benchmark sector allocations | Synthetic |
| `FACT_VIX_DAILY` | VIX data for macro regime classification | Synthetic |
| `FACT_SECTOR_RETURNS` | Sector ETF returns (XLK, XLV, XLF, etc.) | Marketplace |

### Hidden Factor Scoring (NLP + Deterministic)

| Table | Description | Source |
|-------|-------------|--------|
| `DIM_GEO_RISK_CLASSIFICATION` | Lookup table: 189 geographies → risk tier (HIGH/MEDIUM/LOW) + weight (1.0/0.5/0.1) | Derived from FACT_SEC_SEGMENTS distinct geographies |
| `FACT_TRANSCRIPT_NLP_SCORES` | Per-company per-quarter AI exposure + geo risk scores | Marketplace transcripts (AI_AGG) + FACT_SEC_SEGMENTS (SQL) |

**Scoring approaches — use AI only where data is unstructured**:

| Score | Method | Why |
|-------|--------|-----|
| `AI_EXPOSURE_SCORE` (0-100) | `AI_AGG` on earnings call transcript paragraphs | Unstructured text needs NLP |
| `GEO_RISK_SCORE` (0-100) | Weighted revenue share from `DIM_GEO_RISK_CLASSIFICATION` | Structured numeric data — deterministic SQL |

**Geo risk formula**: `(SUM(revenue × risk_weight) / total_revenue) × 100 + concentration_bonus`
- Concentration: +15 if single high-risk country >30%, +25 if >50%
- Default 10 for companies without geographic segment data

### Analyst Estimates

| Table | Description | Source |
|-------|-------------|--------|
| `FACT_ESTIMATE_CONSENSUS` | Analyst consensus **derived from real SEC actuals** | FACT_SEC_FINANCIALS |
| `FACT_ESTIMATE_DATA` | Individual analyst estimates | Synthetic |
| `FACT_ANALYST_COVERAGE` | Analyst coverage mapping | Synthetic |

### Investment Memo Metrics (Calculated from Real SEC Data)

Available in `FACT_SEC_FINANCIALS`:

| Metric | Calculation | Rationale |
|--------|-------------|-----------|
| `TAM` | Revenue × Industry Multiplier (15-35x) | Standard market sizing approach |
| `ESTIMATED_CUSTOMER_COUNT` | Revenue / ARPC (varies by industry) | Implied customer base |
| `ESTIMATED_NRR_PCT` | 100 + Revenue Growth %, capped 90-140% | SaaS-style NRR correlation |

---

## AI Schema

### Semantic Views (20 views)

| Semantic View | Description | Key Tables |
|---------------|-------------|------------|
| `SAM_PORTFOLIO_VIEW` | Portfolio analytics with holdings, ESG, factors, benchmark comparison | V_HOLDINGS_WITH_ESG, DIM_PORTFOLIO, DIM_SECURITY, FACT_FACTOR_EXPOSURES, FACT_BENCHMARK_HOLDINGS |
| `SAM_IMPLEMENTATION_VIEW` | Trading implementation planning | FACT_TRANSACTION_COSTS, FACT_PORTFOLIO_LIQUIDITY, FACT_RISK_LIMITS, FACT_TRADING_CALENDAR, FACT_TAX_IMPLICATIONS |
| `SAM_PORTFOLIO_VIEW` | Supply chain risk analysis | DIM_SUPPLY_CHAIN_RELATIONSHIPS, DIM_ISSUER |
| `SAM_MIDDLE_OFFICE_VIEW` | Operations monitoring | FACT_TRADE_SETTLEMENT, FACT_RECONCILIATION, FACT_NAV_CALCULATION, FACT_CORPORATE_ACTIONS, FACT_CASH_POSITIONS |
| `SAM_PORTFOLIO_VIEW` | Compliance breach tracking | FACT_COMPLIANCE_ALERTS, FACT_RISK_LIMITS |
| `SAM_EXECUTIVE_VIEW` | Firm-wide KPIs | DIM_CLIENT, FACT_CLIENT_FLOWS, FACT_FUND_FLOWS, FACT_STRATEGY_PERFORMANCE |
| `SAM_RESEARCH_VIEW` | Financial analysis (real SEC data) | FACT_SEC_FINANCIALS, FACT_ESTIMATE_CONSENSUS, DIM_ISSUER |
| `SAM_MARKET_VIEW` | Real stock prices | FACT_STOCK_PRICES, DIM_SECURITY, DIM_ISSUER |
| `SAM_RESEARCH_VIEW` | Comprehensive SEC financials | FACT_SEC_FINANCIALS, DIM_ISSUER |
| `SAM_RESEARCH_VIEW` | SEC revenue segments | FACT_SEC_SEGMENTS, DIM_ISSUER |
| `SAM_PORTFOLIO_MODELLING_VIEW` | Portfolio modelling analytics | FACT_COVARIANCE_MATRIX, FACT_EXPECTED_RETURNS, FACT_BACKTEST_RESULTS, FACT_SIMULATION_RESULTS |
| `SAM_ATTRIBUTION_VIEW` | Brinson attribution analysis | FACT_BRINSON_ATTRIBUTION, FACT_BRINSON_BY_SECTOR, DIM_BENCHMARKS |
| `SAM_ATTRIBUTION_VIEW` | Factor contribution analysis | FACT_FACTOR_ATTRIBUTION, FACT_FACTOR_EXPOSURES |
| `SAM_ATTRIBUTION_VIEW` | Hidden/alternative factor detection | FACT_HIDDEN_FACTOR_EXPOSURES |
| `SAM_MARKET_VIEW` | Market regime classification | V_MACRO_REGIME, FACT_VIX_DAILY |
| `SAM_MARKET_VIEW` | Stress test scenarios | DIM_STRESS_SCENARIOS, FACT_SCENARIO_SHOCKS |
| `SAM_MARKET_VIEW` | Historical crisis periods | FACT_HISTORICAL_STRESS_PERIODS |
| `SAM_MARKET_VIEW` | Global macroeconomic indicators and emissions | FACT_POLICY_RATES, FACT_FX_RATES, FACT_ECONOMIC_INDICATORS, FACT_COUNTRY_EMISSIONS |
| `SAM_MARKET_VIEW` | US Treasury yield curve rates | FACT_TREASURY_YIELDS |
| `SAM_RESEARCH_VIEW` | SEC Form 4 insider transactions | FACT_INSIDER_TRANSACTIONS |
| `SAM_RESEARCH_VIEW` | SEC 13F institutional ownership | FACT_INSTITUTIONAL_HOLDINGS |
| `SAM_PE_DEAL_PIPELINE_VIEW` | PE deal sourcing and screening | DIM_DEAL_PIPELINE |
| `SAM_PE_VALUE_CREATION_VIEW` | PE portfolio company monitoring | DIM_PORTFOLIO_COMPANY, FACT_BOARD_PACK_METRICS, FACT_VALUE_CREATION_PLAN |

### Cortex Search Services (10 services)

All services use **multi-index search** (GA March 12, 2026): TEXT INDEXES for keyword/lexical matching on names, tickers, categories + VECTOR INDEXES for semantic search on document body. PDF-based document types are consolidated into 2 services with agent-side filtering via `filter: {"@eq": {"DOCUMENT_TYPE": "<doc_type>"}}` at query time.

| Search Service | Corpus Table | TEXT INDEXES | VECTOR INDEXES | Filterable Attributes | Doc Types |
|----------------|--------------|-------------|----------------|----------------------|----------|
| **`SAM_INTERNAL_DOCS`** | PDF_INTERNAL_CORPUS | DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR | DOCUMENT_TEXT | DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, TICKER, COMPANY_NAME, GICS_SECTOR | 13 types: policy_docs, sales_templates, philosophy_docs, report_templates, macro_events, custodian_reports, reconciliation_notes, ssi_documents, ops_procedures, strategy_documents, methodology_docs, engagement_notes, ips |
| **`SAM_EXTERNAL_DOCS`** | PDF_EXTERNAL_CORPUS | DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR | DOCUMENT_TEXT | DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, TICKER, COMPANY_NAME, GICS_SECTOR | 3 types: broker_research, press_releases, ngo_reports |
| `SAM_COMPANY_EVENTS` | COMPANY_EVENT_TRANSCRIPTS_CORPUS | DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR, EVENT_TYPE, SPEAKER_NAME | DOCUMENT_TEXT | SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, EVENT_TYPE, TICKER, COMPANY_NAME, GICS_SECTOR, SPEAKER_NAME, SPEAKER_ROLE | - |
| `SAM_REAL_SEC_FILINGS` | FACT_SEC_FILING_TEXT | DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR, FILING_TYPE | FILING_TEXT | COMPANY_NAME, TICKER, GICS_SECTOR, FILING_TYPE, FISCAL_YEAR, FISCAL_QUARTER, VARIABLE_NAME, CIK | - |
| `SAM_PE_BOARD_PACKS` | PE_BOARD_PACKS_CORPUS | DOCUMENT_TITLE, CompanyName | DOCUMENT_TEXT | CompanyName, PortfolioCompanyID, DOCUMENT_TYPE, ReportPeriod | - |
| `SAM_PE_DUE_DILIGENCE` | PE_DUE_DILIGENCE_CORPUS | DOCUMENT_TITLE, TargetCompanyName | DOCUMENT_TEXT | TargetCompanyName, DealID, DOCUMENT_TYPE | - |
| `SAM_PE_EXPERT_NETWORK` | PE_EXPERT_NETWORK_CORPUS | DOCUMENT_TITLE, TargetCompanyName, ExpertRole | DOCUMENT_TEXT | TargetCompanyName, ExpertRole, DealID, PortfolioCompanyID, CallDate | - |
| `SAM_CREDIT_AGREEMENTS` | CREDIT_AGREEMENTS_CORPUS | DOCUMENT_TITLE, BORROWERNAME | DOCUMENT_TEXT | BORROWERNAME, FACILITYID, DOCUMENT_TYPE | - |
| `SAM_COMPLIANCE_CERTS` | COMPLIANCE_CERTS_CORPUS | DOCUMENT_TITLE, BORROWERNAME | DOCUMENT_TEXT | BORROWERNAME, BORROWERID, DOCUMENT_TYPE, REPORTPERIOD | - |
| `SAM_IC_MEMOS` | IC_MEMOS_CORPUS | DOCUMENT_TITLE, TARGETNAME | DOCUMENT_TEXT | TARGETNAME, DEALID, DOCUMENT_TYPE | - |

### Agents (13 agents)

| Agent | Display Name | Key Tools |
|-------|--------------|-----------|
| `AM_portfolio_manager_copilot` | Portfolio Manager Co-Pilot | quantitative_analyzer (SAM_PORTFOLIO_VIEW), stock_prices, sec_financials, supply_chain_analyzer, implementation_analyzer, search_broker_research, search_press_releases, search_macro_events, search_policies, search_report_templates, search_ips_documents, search_company_events, search_sec_filings, pdf_generator |
| `AM_research_copilot` | Research Analyst | fundamentals_analyzer (SAM_RESEARCH_VIEW), sec_financials, search_broker_research, search_press_releases, search_company_events, search_sec_filings |
| `AM_investment_strategy` | Investment Strategy | quantitative_analyzer, search_broker_research, search_press_releases, search_macro_events, search_sec_filings |
| `AM_risk_compliance` | Risk & Compliance | quantitative_analyzer, search_ngo_reports, search_engagement_notes, search_policies, search_press_releases, search_report_templates, search_sec_filings |
| `AM_risk_compliance` | Risk & Compliance | compliance_analyzer (SAM_PORTFOLIO_VIEW), search_policies, search_engagement_notes, search_report_templates, search_ips_documents, pdf_generator |
| `AM_sales_advisor` | Sales Advisor | quantitative_analyzer, search_sales_templates, search_philosophy_docs, search_policies, pdf_generator |
| `AM_investment_strategy` | Investment Strategy | quantitative_analyzer, stock_prices, search_broker_research |
| `AM_middle_office_copilot` | Middle Office Co-Pilot | middle_office_analyzer (SAM_MIDDLE_OFFICE_VIEW), search_custodian_reports, search_reconciliation_notes, search_ssi_documents, search_ops_procedures |
| `AM_executive_copilot` | Executive Co-Pilot | executive_analyzer (SAM_EXECUTIVE_VIEW), search_strategy_docs, search_press_releases, search_broker_research |
| `AM_portfolio_modelling_copilot` | Portfolio Modelling Copilot | portfolio_modelling_analyzer, search_methodology_docs, run_backtest, run_simulation |
| `AM_portfolio_manager_copilot` | Portfolio Manager Co-Pilot | brinson_analyzer, factor_analyzer, hidden_factor_analyzer, macro_regime_analyzer, stress_scenario_analyzer, historical_stress_analyzer, global_macro_analyzer, backtest_historical_stress |
| `AM_pe_deal_sourcing_copilot` | PE Deal Sourcing Copilot | deal_pipeline_analyzer, search_due_diligence, search_expert_network |
| `AM_pe_portfolio_monitor` | PE Portfolio Monitor | value_creation_analyzer, search_board_packs |

---

## RAW Schema - Pipeline Objects

### Stages (PDF Ingestion)

| Stage | Description |
|-------|-------------|
| `PDF_INTERNAL_STAGE` | Internal SAM-branded PDF documents (policies, procedures, memos) |
| `PDF_EXTERNAL_STAGE` | External PDF documents (broker research, NGO reports, press releases) |

### Streams (Pipeline Triggers)

| Stream | On Object | Description |
|--------|-----------|-------------|
| `PDF_INTERNAL_STREAM` | `PDF_INTERNAL_STAGE` | Tracks new internal PDF uploads |
| `PDF_EXTERNAL_STREAM` | `PDF_EXTERNAL_STAGE` | Tracks new external PDF uploads |
| `TRANSCRIPTS_SPEAKER_STREAM` | `COMPANY_EVENT_TRANSCRIPTS_RAW` | Tracks new transcripts for speaker mapping task |
| `TRANSCRIPTS_CORPUS_STREAM` | `COMPANY_EVENT_TRANSCRIPTS_RAW` | Tracks new transcripts for corpus build task |
| `SEC_FILINGS_RAW_STREAM` | `SEC_FILING_TEXT_RAW` | Tracks new SEC filing inserts |

### Tasks (Pipeline DAGs)

| Task | Schedule/Trigger | Description |
|------|------------------|-------------|
| `PDF_INTERNAL_PIPELINE_ROOT` | Stream trigger | Root task for internal PDF pipeline |
| `PDF_INTERNAL_PARSE` | After root | Parse PDFs with AI_PARSE_DOCUMENT |
| `PDF_INTERNAL_CHUNK` | After parse | Conditional chunking (>512 tokens) |
| `PDF_EXTERNAL_PIPELINE_ROOT` | Stream trigger | Root task for external PDF pipeline |
| `PDF_EXTERNAL_PARSE` | After root | Parse PDFs with AI_PARSE_DOCUMENT |
| `PDF_EXTERNAL_CHUNK` | After parse | Conditional chunking (>512 tokens) |
| `TRANSCRIPTS_PIPELINE_ROOT` | Stream trigger | Real transcripts pipeline root |
| `TRANSCRIPTS_SPEAKER_MAPPING` | After root | AI-based speaker identification |
| `TRANSCRIPTS_CORPUS_BUILD` | After mapping | Chunked corpus with speaker context |
| `SEC_FILINGS_PIPELINE_ROOT` | Stream trigger | SEC filings pipeline root |
| `SEC_FILINGS_CHUNK` | After root | Conditional chunking (>512 tokens) |

### Pipeline RAW Tables

| Table | Description |
|-------|-------------|
| `PDF_INTERNAL_RAW` | Parsed internal PDF content |
| `PDF_EXTERNAL_RAW` | Parsed external PDF content |
| `COMPANY_EVENT_TRANSCRIPTS_RAW` | Real transcripts from Cybersyn |
| `SEC_FILING_TEXT_RAW` | SEC filing text from Cybersyn |

### Pipeline CURATED Tables

| Table | Description |
|-------|-------------|
| `PDF_INTERNAL_CORPUS` | Chunked internal PDF corpus for Cortex Search |
| `PDF_EXTERNAL_CORPUS` | Chunked external PDF corpus for Cortex Search |

---

## External Data Sources

### Cybersyn Data (Snowflake Marketplace)

The project uses Cybersyn financial data available through Snowflake Marketplace:

| Configuration | Value |
|---------------|-------|
| Database | `FINANCIALS_ECONOMICS_ENTERPRISE` (or `SNOWFLAKE_PUBLIC_DATA_FREE`) |
| Schema | `CYBERSYN` (or `PUBLIC_DATA_FREE`) |

Configure in `config.py`:
```python
REAL_DATA_SOURCES = {
    'database': 'FINANCIALS_ECONOMICS_ENTERPRISE',
    'schema': 'CYBERSYN',
}
```

### Source Table Mapping

| Cybersyn Source Table | SAM_DEMO Target | Description |
|-----------------------|-----------------|-------------|
| `STOCK_PRICE_TIMESERIES` | `MARKET_DATA.FACT_STOCK_PRICES` | Daily OHLCV prices from Nasdaq |
| `SEC_CORPORATE_REPORT_ATTRIBUTES` | `MARKET_DATA.FACT_SEC_FINANCIALS` | XBRL financial statements |
| `SEC_METRICS_TIMESERIES` | `MARKET_DATA.FACT_SEC_SEGMENTS` | Revenue segments by geography/business |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `MARKET_DATA.FACT_SEC_FILING_TEXT` | Full text of SEC filings |
| `SEC_REPORT_TEXT_ATTRIBUTES` (8-K) | `MARKET_DATA.FACT_DIVIDENDS` | Dividend data via AI_EXTRACT |
| `BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES` | `MARKET_DATA.FACT_POLICY_RATES` | Central bank policy rates |
| `FX_RATES_TIMESERIES` | `MARKET_DATA.FACT_FX_RATES` | Foreign exchange rates |
| `CYBERSYN_FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES` | `MARKET_DATA.FACT_ECONOMIC_INDICATORS` | US economic indicators (FRED) |
| `COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES_V2` | `CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS` | Earnings calls, AGMs, etc. |
| `COMPANY_INDEX` | `CURATED.DIM_ISSUER` (enrichment) | Company master with CIK, EIN, LEI |
| `US_TREASURY_PAR_YIELD_CURVE_RATES` | `MARKET_DATA.FACT_TREASURY_YIELDS` | Treasury yield curve (14 maturities) |
| `CLIMATE_WATCH_GHG_EMISSIONS_TIMESERIES` | `MARKET_DATA.FACT_COUNTRY_EMISSIONS` | Country GHG emissions by sector |
| `SEC_CIK_INDEX` + `SEC_INSIDER_TRANSACTIONS` | `CURATED.FACT_INSIDER_TRANSACTIONS` | Form 4 insider trading |
| `SEC_CIK_INDEX` + `SEC_INSTITUTIONAL_HOLDINGS` | `CURATED.FACT_INSTITUTIONAL_HOLDINGS` | 13F institutional holdings |
| `NPORT_FUND_CHARACTERISTICS` + `NPORT_PORTFOLIO_HOLDINGS` | `CURATED.FACT_BENCHMARK_HOLDINGS` | N-PORT real benchmark weights |

---

## Data Quality Standards

### Validation Rules

- **Portfolio Weights**: Sum to 100% (±0.1% tolerance)
- **Transaction Integrity**: Transaction log balances to ABOR positions
- **Security Identifiers**: Ticker columns properly populated
- **Price Data**: No negative prices, realistic ranges by asset class
- **Date Consistency**: Business days only, proper date ranges
- **Foreign Key Relationships**: All relationships valid
- **Historical Range**: All data limited to `config.YEARS_OF_HISTORY` (5 years default)

---

## Sample Data Characteristics

### Portfolios (11 total)
- SAM Global Flagship Multi-Asset
- SAM ESG Leaders Global Equity
- SAM Global Thematic Growth
- SAM Technology & Infrastructure
- SAM US Core Equity
- SAM Renewable & Climate Solutions
- SAM Sustainable Global Equity
- SAM AI & Digital Innovation
- SAM Global Balanced 60/40
- SAM Tech Disruptors Equity
- SAM US Value Equity

### Companies (79 total, all with CIK)
- **Core Demo Companies** (8): AAPL, MSFT, NVDA, GOOGL, TSM, SNOW, CMC, RBBN
- **Major US Stocks** (~40): AMZN, META, TSLA, AMD, INTC, etc.
- **Additional Companies** (~31): Sector diversity

### Demo Clients (15 named clients)
- **Standard** (8): Meridian Capital Partners, Yale University Endowment, Gates Foundation Trust, etc.
- **At-Risk** (3): Pacific Coast Pension Fund, Alpine University Endowment, Metropolitan Insurance Group
- **New** (2): Midwest Community Foundation, Nordic Heritage Family Office

### Geographic Coverage
- US: ~55%
- Europe: ~30%
- APAC/EM: ~15%

---

## Related Documentation

- [`docs/data_lineage.md`](data_lineage.md) - Data flow, dependencies, and impact analysis
- [`docs/production_pipelines_demo.md`](production_pipelines_demo.md) - Pipeline demo runbook
- [`docs/DATA_SOURCING_STRATEGY.md`](DATA_SOURCING_STRATEGY.md) - Real vs synthetic data strategy
- [`.cursor/rules/data-index.mdc`](../.cursor/rules/data-index.mdc) - Data generation patterns
- [`.cursor/rules/pipelines.mdc`](../.cursor/rules/pipelines.mdc) - Pipeline development patterns
