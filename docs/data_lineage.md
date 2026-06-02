# SAM Demo - Data Lineage and Dependencies

Data flows, object dependencies, and impact analysis for the SAM demo environment.

## Quick Reference

### Tables by Schema

| Schema | Tables | Description |
|--------|--------|-------------|
| **CURATED** | 55 tables, 8 views | Foundation dimensions, facts, corpus tables |
| **MARKET_DATA** | 17 tables | Real market data from Cybersyn |
| **RAW** | 17 tables | Staging for document pipelines |
| **AI** | 16 semantic views, 10 search services, 15 agents | AI components |

### All Semantic Views

| View | Underlying Tables | Used By Agents |
|------|-------------------|----------------|
| SAM_PORTFOLIO_VIEW | DIM_BENCHMARK, FACT_BENCHMARK_HOLDINGS, FACT_BENCHMARK_PERFORMANCE, FACT_FACTOR_EXPOSURES, V_HOLDINGS_WITH_ESG, DIM_ISSUER, DIM_PORTFOLIO, V_PORTFOLIO_BENCHMARK_COMPARISON, DIM_SECURITY, FACT_COMPLIANCE_ALERTS, DIM_SUPPLY_CHAIN_RELATIONSHIPS | pm_cockpit, investment_strategy, risk_compliance, sales_advisor, executive_copilot, pm_cockpit |
| SAM_ATTRIBUTION_VIEW | FACT_BRINSON_BY_SECTOR, FACT_BRINSON_ATTRIBUTION, DIM_PORTFOLIO, FACT_BRINSON_ATTRIBUTION_DETAIL, FACT_BRINSON_LINKED, FACT_FACTOR_ATTRIBUTION, FACT_HIDDEN_FACTOR_EXPOSURES, V_FACTOR_ROLLING_ANALYTICS, V_ATTRIBUTION_ANOMALIES, V_CROSS_PORTFOLIO_ANALYTICS, FACT_CURRENCY_ATTRIBUTION, DIM_SECURITY | pm_cockpit, pm_cockpit, sales_advisor, executive_copilot |
| SAM_MARKET_VIEW | V_MACRO_REGIME, DIM_STRESS_SCENARIOS, FACT_SCENARIO_SHOCKS, FACT_HISTORICAL_STRESS_PERIODS, FACT_TREASURY_YIELDS, DIM_ISSUER, FACT_STOCK_PRICES, DIM_SECURITY, FACT_ECONOMIC_INDICATORS, FACT_FX_RATES, FACT_POLICY_RATES, FACT_COUNTRY_EMISSIONS | pm_cockpit, investment_strategy, risk_compliance, pm_cockpit, private_credit |
| SAM_RESEARCH_VIEW | DIM_ANALYST, FACT_ESTIMATE_DATA, DIM_BROKER, FACT_ESTIMATE_CONSENSUS, FACT_SEC_FINANCIALS, DIM_ISSUER, FACT_SEC_SEGMENTS, FACT_INSIDER_TRANSACTIONS, FACT_INSTITUTIONAL_HOLDINGS | pm_cockpit, research_copilot, risk_compliance, sales_advisor, investment_strategy, executive_copilot, pe_deal_sourcing, private_credit |
| SAM_IMPLEMENTATION_VIEW | DIM_CLIENT_MANDATES, FACT_POSITION_DAILY_ABOR, DIM_PORTFOLIO, FACT_PORTFOLIO_LIQUIDITY, FACT_RISK_LIMITS, DIM_SECURITY, FACT_TAX_IMPLICATIONS, FACT_TRADE_SETTLEMENT, FACT_TRADING_CALENDAR, FACT_TRANSACTION_COSTS | pm_cockpit, sales_advisor |
| SAM_EXECUTIVE_VIEW | DIM_CLIENT, FACT_CLIENT_FLOWS, FACT_FUND_FLOWS, DIM_PORTFOLIO, FACT_STRATEGY_PERFORMANCE | executive_copilot, sales_advisor |
| SAM_MIDDLE_OFFICE_VIEW | FACT_CASH_MOVEMENTS, FACT_CASH_POSITIONS, FACT_CORPORATE_ACTIONS, DIM_COUNTERPARTY, DIM_CUSTODIAN, FACT_NAV_CALCULATION, DIM_PORTFOLIO, FACT_RECONCILIATION, DIM_SECURITY, FACT_TRADE_SETTLEMENT | middle_office_copilot |
| SAM_PORTFOLIO_MODELLING_VIEW | FACT_BACKTEST_RESULTS, FACT_EXPECTED_RETURNS, DIM_ISSUER, DIM_MODEL_PORTFOLIO, FACT_MODEL_PORTFOLIO_WEIGHTS, FACT_RISK_FACTORS, DIM_SECURITY, FACT_SIMULATION_RESULTS, V_SECURITY_RETURNS, FACT_COVARIANCE_MATRIX | portfolio_modelling_copilot |
| SAM_PE_DEAL_PIPELINE_VIEW | DIM_DEAL_PIPELINE | pe_deal_sourcing, pe_portfolio_monitor |
| SAM_PE_VALUE_CREATION_VIEW | DIM_PORTFOLIO_COMPANY, FACT_VALUE_CREATION_PLAN, FACT_PORTFOLIO_COMPANY_KPI, FACT_BOARD_PACK_METRICS | pe_deal_sourcing, pe_portfolio_monitor |
| SAM_PROACTIVE_INSIGHTS_VIEW | FACT_PROACTIVE_INSIGHTS, FACT_PROACTIVE_ALERTS | pm_cockpit, pm_cockpit |
| SAM_CREDIT_PORTFOLIO_VIEW | FACT_CREDIT_SECTOR_BENCHMARKS, DIM_CREDIT_BORROWER, FACT_CREDIT_COVENANT_TRACKING, DIM_CREDIT_FACILITY, FACT_CREDIT_BORROWER_FINANCIALS, FACT_CREDIT_DEAL_PIPELINE | private_credit |
| SAM_TOOL_RESULTS_VIEW | TOOL_BACKTEST_RUNS, TOOL_BACKTEST_TIMESERIES, TOOL_RUN_PORTFOLIOS, TOOL_SIMULATION_PATHS, TOOL_SIMULATION_RUNS, TOOL_SIMULATION_TERMINAL_VALUES | portfolio_modelling_copilot |
| SAM_REGIME_VIEW | FACT_BENCHMARK_RETURNS, FACT_REGIME_PREDICTIONS, FACT_VIX_DAILY | investment_strategy, portfolio_modelling_copilot |
| SAM_FACTOR_MODEL_VIEW | FACT_FACTOR_RETURNS, FACT_FACTOR_SCORES, FACT_ML_FACTOR_PREDICTIONS, FACT_OPTIMAL_PORTFOLIO | investment_strategy |
| SAM_CREDIT_RISK_VIEW | DIM_CREDIT_BORROWER, FACT_CREDIT_RISK_SCORES, FACT_CREDIT_SHAP_EXPLANATIONS | private_credit |

### All Agents with Tools

| Agent | Semantic View Tools | Cortex Search Tools | Generic Tools |
|-------|--------------------|--------------------|---------------|
| **AM_portfolio_manager_copilot** | portfolio_analyzer (PORTFOLIO), attribution_analyzer (ATTRIBUTION), market_analyzer (MARKET), research_analyzer (RESEARCH), implementation_analyzer (IMPLEMENTATION) | search_company_events, search_sec_filings, search_external_docs, search_internal_docs | pdf_generator, explain_data_origin |
| **AM_portfolio_manager_copilot** | attribution_analyzer (ATTRIBUTION), market_analyzer (MARKET) | — | backtest_historical_stress, scenario_sensitivity, run_counterfactual |
| **AM_portfolio_manager_copilot** | portfolio_analyzer (PORTFOLIO), attribution_analyzer (ATTRIBUTION), market_analyzer (MARKET), research_analyzer (RESEARCH), insights_analyzer (PROACTIVE_INSIGHTS) | search_company_events, search_sec_filings, search_external_docs, search_internal_docs | pdf_generator |
| **AM_research_copilot** | research_analyzer (RESEARCH) | search_external_docs, search_company_events, search_sec_filings | pdf_generator |
| **AM_investment_strategy** | portfolio_analyzer (PORTFOLIO), regime_analyzer (REGIME), market_analyzer (MARKET) | search_company_events, search_sec_filings, search_external_docs, search_internal_docs | — |
| **AM_risk_compliance** | portfolio_analyzer (PORTFOLIO), market_analyzer (MARKET) | search_sec_filings, search_regulations, search_external_docs, search_internal_docs, search_company_events | pdf_generator |
| **AM_risk_compliance** | portfolio_analyzer (PORTFOLIO), research_analyzer (RESEARCH), market_analyzer (MARKET) | search_internal_docs, search_regulations | pdf_generator |
| **AM_sales_advisor** | portfolio_analyzer (PORTFOLIO), client_analyzer (EXECUTIVE), research_analyzer (RESEARCH), attribution_analyzer (ATTRIBUTION) | search_internal_docs, search_regulations | pdf_generator |
| **AM_investment_strategy** | portfolio_analyzer (PORTFOLIO), research_analyzer (RESEARCH), factor_model_analyzer (FACTOR_MODEL), market_analyzer (MARKET) | search_company_events, search_external_docs | — |
| **AM_executive_copilot** | executive_kpi_analyzer (EXECUTIVE), portfolio_analyzer (PORTFOLIO), research_analyzer (RESEARCH), attribution_analyzer (ATTRIBUTION), implementation_analyzer (IMPLEMENTATION) | search_internal_docs, search_external_docs | ma_simulation, pdf_generator, explain_data_origin |
| **AM_middle_office_copilot** | middle_office_analyzer (MIDDLE_OFFICE) | search_internal_docs | pdf_generator |
| **AM_portfolio_modelling_copilot** | portfolio_modelling_analyzer (PORTFOLIO_MODELLING), regime_analyzer (REGIME), tool_results_analyzer (TOOL_RESULTS) | search_internal_docs | run_backtest, run_monte_carlo, run_attribution |
| **AM_pe_deal_sourcing_copilot** | deal_pipeline_analyzer (PE_DEAL_PIPELINE), research_analyzer (RESEARCH) | search_due_diligence, search_expert_network, search_sec_filings | — |
| **AM_pe_portfolio_monitor** | value_creation_analyzer (PE_VALUE_CREATION) | search_board_packs, search_expert_network | — |
| **AM_private_credit_copilot** | credit_portfolio_analyzer (CREDIT_PORTFOLIO), credit_risk_analyzer (CREDIT_RISK), market_analyzer (MARKET), research_analyzer (RESEARCH) | search_credit_agreements, search_compliance_certs, search_ic_memos, search_sec_filings | — |

### All Cortex Search Services

All services use **multi-index search** (GA March 12, 2026): TEXT INDEXES for keyword/lexical matching + VECTOR INDEXES for semantic search. PDF-based document types are consolidated into 2 services with agent-side filtering via `filter: {"@eq": {"DOCUMENT_TYPE": "<doc_type>"}}`. Each agent tool scopes to its specific document type at query time.

| Service | Source Corpus | TEXT INDEXES | VECTOR INDEXES | Filterable Attributes | Doc Types |
|---------|---------------|-------------|----------------|----------------------|----------|
| **SAM_INTERNAL_DOCS** | PDF_INTERNAL_CORPUS | DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR | DOCUMENT_TEXT | DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, TICKER, COMPANY_NAME, GICS_SECTOR | 13 types: policy_docs, sales_templates, philosophy_docs, report_templates, macro_events, custodian_reports, reconciliation_notes, ssi_documents, ops_procedures, strategy_documents, methodology_docs, engagement_notes, ips |
| **SAM_EXTERNAL_DOCS** | PDF_EXTERNAL_CORPUS | DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR | DOCUMENT_TEXT | DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE, TICKER, COMPANY_NAME, GICS_SECTOR | 3 types: broker_research, press_releases, ngo_reports |
| SAM_COMPANY_EVENTS | COMPANY_EVENT_TRANSCRIPTS_CORPUS | DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR, EVENT_TYPE, SPEAKER_NAME | DOCUMENT_TEXT | All entity + event cols | - |
| SAM_REAL_SEC_FILINGS | FACT_SEC_FILING_TEXT | DOCUMENT_TITLE, TICKER, COMPANY_NAME, GICS_SECTOR, FILING_TYPE | FILING_TEXT | COMPANY_NAME, TICKER, GICS_SECTOR, FILING_TYPE, FISCAL_YEAR, FISCAL_QUARTER, VARIABLE_NAME, CIK | - |
| SAM_PE_BOARD_PACKS | PE_BOARD_PACKS_CORPUS | DOCUMENT_TITLE, CompanyName | DOCUMENT_TEXT | CompanyName, PortfolioCompanyID, DOCUMENT_TYPE, ReportPeriod | - |
| SAM_PE_DUE_DILIGENCE | PE_DUE_DILIGENCE_CORPUS | DOCUMENT_TITLE, TargetCompanyName | DOCUMENT_TEXT | TargetCompanyName, DealID, DOCUMENT_TYPE | - |
| SAM_PE_EXPERT_NETWORK | PE_EXPERT_NETWORK_CORPUS | DOCUMENT_TITLE, TargetCompanyName, ExpertRole | DOCUMENT_TEXT | TargetCompanyName, ExpertRole, DealID, CallDate | - |
| SAM_CREDIT_AGREEMENTS | CREDIT_AGREEMENTS_CORPUS | DOCUMENT_TITLE, BORROWERNAME | DOCUMENT_TEXT | BORROWERNAME, FACILITYID, DOCUMENT_TYPE | - |
| SAM_COMPLIANCE_CERTS | COMPLIANCE_CERTS_CORPUS | DOCUMENT_TITLE, BORROWERNAME | DOCUMENT_TEXT | BORROWERNAME, BORROWERID, DOCUMENT_TYPE, REPORTPERIOD | - |
| SAM_IC_MEMOS | IC_MEMOS_CORPUS | DOCUMENT_TITLE, TARGETNAME | DOCUMENT_TEXT | TARGETNAME, DEALID, DOCUMENT_TYPE | - |

---

## External Data Sources

### Cybersyn Data (Equivalent Sources)

The project uses Cybersyn financial data available through two equivalent Snowflake Marketplace listings:

| Free Tier | Enterprise Tier |
|-----------|-----------------|
| `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE` | `FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN` |

Both contain identical tables. Configure in `config.py`:
```python
REAL_DATA_SOURCES = {
    'database': 'FINANCIALS_ECONOMICS_ENTERPRISE',  # or 'SNOWFLAKE_PUBLIC_DATA_FREE'
    'schema': 'CYBERSYN',                           # or 'PUBLIC_DATA_FREE'
}
```

### Source Table Mapping

| Cybersyn Source Table | SAM_DEMO Target | Description |
|-----------------------|-----------------|-------------|
| `STOCK_PRICE_TIMESERIES` | `MARKET_DATA.FACT_STOCK_PRICES` | Daily OHLCV prices from Nasdaq |
| `SEC_METRICS_TIMESERIES` | `MARKET_DATA.FACT_SEC_SEGMENTS` | Revenue segments by geography/business |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `MARKET_DATA.FACT_SEC_FILING_TEXT` | Full text of SEC filings |
| `SEC_CORPORATE_REPORT_ATTRIBUTES` | `MARKET_DATA.FACT_SEC_FINANCIALS` | XBRL financial statements |
| `SEC_REPORT_TEXT_ATTRIBUTES` (8-K) | `MARKET_DATA.FACT_DIVIDENDS` | Dividend announcements (AI_EXTRACT) |
| `BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES` | `MARKET_DATA.FACT_POLICY_RATES` | Central bank policy rates |
| `FX_RATES_TIMESERIES` | `MARKET_DATA.FACT_FX_RATES` | Foreign exchange rates |
| `CYBERSYN_FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES` | `MARKET_DATA.FACT_ECONOMIC_INDICATORS` | US economic indicators (FRED) |
| `COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES_V2` | `CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS` | Earnings calls, AGMs, etc. |
| `COMPANY_INDEX` | `CURATED.DIM_ISSUER` (enrichment) | Company master with CIK, EIN, LEI |
| `COMPANY_CHARACTERISTICS` | `CURATED.DIM_ISSUER` (enrichment) | Company attributes |

### Column Mapping: STOCK_PRICE_TIMESERIES → FACT_STOCK_PRICES

| Source Column | Target Column | Transformation |
|---------------|---------------|----------------|
| `TICKER` | `TICKER` | Direct |
| `DATE` | `PRICE_DATE` | Rename |
| `VARIABLE='pre-market_open'` | `PRICE_OPEN` | Pivot |
| `VARIABLE='post-market_close'` | `PRICE_CLOSE` | Pivot |
| `VARIABLE='all-day_high'` | `PRICE_HIGH` | Pivot |
| `VARIABLE='all-day_low'` | `PRICE_LOW` | Pivot |
| `VARIABLE='nasdaq_volume'` | `VOLUME` | Pivot, cast BIGINT |
| - | `SecurityID` | Join via TICKER |
| - | `IssuerID` | Join via TICKER |

### Data Filtering

| Source Table | Filter | Reason |
|--------------|--------|--------|
| `STOCK_PRICE_TIMESERIES` | `DATE >= DATEADD(year, -2, CURRENT_DATE())` | Last 2 years |
| `SEC_METRICS_TIMESERIES` | `FISCAL_YEAR >= YEAR(CURRENT_DATE()) - 5` | Last 5 years |
| `SEC_REPORT_TEXT_ATTRIBUTES` | `LENGTH(VALUE) > 100` | Filter empty texts |

---

## Build Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SAM DEMO BUILD PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. DATABASE STRUCTURE (main.py → structured.create_database_structure)     │
│     └── SAM_DEMO.{RAW, CURATED, MARKET_DATA, AI} schemas                    │
│                                                                             │
│  2. MARKET DATA ANCHOR (market_data.build_price_anchor)                     │
│     └── FACT_STOCK_PRICES (establishes date anchor for all generation)      │
│                                                                             │
│  3. STRUCTURED DATA (structured.build_all)                                  │
│     ├── Foundation: DIM_ISSUER → DIM_SECURITY → DIM_PORTFOLIO               │
│     ├── Positions: FACT_TRANSACTION → FACT_POSITION_DAILY_ABOR              │
│     ├── Analytics: FACT_ESG_SCORES, FACT_FACTOR_EXPOSURES                   │
│     ├── Implementation: FACT_TRANSACTION_COSTS, FACT_PORTFOLIO_LIQUIDITY    │
│     ├── Client: DIM_CLIENT_MANDATES, FACT_CLIENT_FLOWS                      │
│     ├── Middle Office: FACT_TRADE_SETTLEMENT, FACT_NAV_CALCULATION          │
│     ├── Modelling: FACT_COVARIANCE_MATRIX, FACT_BACKTEST_RESULTS            │
│     ├── Attribution: FACT_BRINSON_*, FACT_FACTOR_ATTRIBUTION                │
│     └── Private Equity: DIM_DEAL_PIPELINE, DIM_PORTFOLIO_COMPANY            │
│                                                                             │
│  4. MARKET DATA (market_data.build_all)                                     │
│     ├── Real Data: FACT_SEC_FINANCIALS, FACT_SEC_SEGMENTS                   │
│     └── Estimates: FACT_ESTIMATE_CONSENSUS, FACT_ESTIMATE_DATA              │
│                                                                             │
│  5. UNSTRUCTURED DATA (pipelines module)                                    │
│     ├── Generate: Templates → RAW.*_RAW tables                              │
│     ├── Real Data: Transcripts → COMPANY_EVENT_TRANSCRIPTS_CORPUS           │
│     └── Corpus: RAW → CURATED.*_CORPUS tables                               │
│                                                                             │
│  6. AI COMPONENTS (builder.build_all)                                       │
│     ├── Semantic Views: 16 views over structured data                       │
│     ├── Cortex Search: 10 services over corpus tables                       │
│     └── Agents: 15 agents with tool configurations                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schema Details

### CURATED Schema

#### Foundation Tables

| Table | Description | Key Columns | Source |
|-------|-------------|-------------|--------|
| DIM_ISSUER | Company master (single source of truth) | IssuerID, CIK, LegalName, PrimaryTicker, GICS_SECTOR | config.DEMO_COMPANIES + Cybersyn |
| DIM_SECURITY | Security master | SecurityID, IssuerID, Ticker, AssetClass, CUSIP | Derived from DIM_ISSUER |
| DIM_PORTFOLIO | Portfolio definitions | PortfolioID, PortfolioName, Strategy, BenchmarkID | config.PORTFOLIOS |
| DIM_BENCHMARK | Benchmark definitions | BenchmarkID, BenchmarkName | Synthetic |
| DIM_SUPPLY_CHAIN_RELATIONSHIPS | Supply chain network | CompanyID, CounterpartyID, RelationshipType, CostShare | config.SUPPLY_CHAIN_* |
| DIM_CLIENT_MANDATES | Client mandate rules | MandateID, ClientID, MaxConcentration, MinESGGrade | Synthetic |
| DIM_MODEL_PORTFOLIO | Model portfolio definitions | ModelID, ModelName, Strategy | Synthetic |

#### Position & Transaction Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| FACT_TRANSACTION | Historical transactions | TransactionID, SecurityID, PortfolioID, TransactionType, Quantity |
| FACT_POSITION_DAILY_ABOR | Daily holdings | PositionID, SecurityID, PortfolioID, HoldingDate, Quantity, MarketValue |
| FACT_BENCHMARK_HOLDINGS | Benchmark constituents | BenchmarkID, SecurityID, Weight |
| FACT_BENCHMARK_PERFORMANCE | Benchmark returns | BenchmarkID, Date, DailyReturn |

#### Risk & Analytics Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| FACT_ESG_SCORES | ESG ratings | SecurityID, E_Score, S_Score, G_Score, OverallGrade |
| FACT_FACTOR_EXPOSURES | Factor loadings | SecurityID, FactorName, Exposure, RSquared |
| FACT_TRANSACTION_COSTS | Trading costs | SecurityID, BidAskSpread, MarketImpact, AvgDailyVolume |
| FACT_PORTFOLIO_LIQUIDITY | Portfolio liquidity | PortfolioID, CashPosition, LiquidityScore |
| FACT_RISK_LIMITS | Risk constraints | PortfolioID, TrackingErrorLimit, ConcentrationLimit |
| FACT_TRADING_CALENDAR | Trading calendar | Date, IsBlackout, ExpectedVolatility |
| FACT_TAX_IMPLICATIONS | Tax lot data | PositionID, CostBasis, UnrealizedGain, HoldingPeriod |

#### Compliance Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| FACT_COMPLIANCE_ALERTS | Compliance breaches | AlertID, PortfolioID, AlertType, Severity, Status |
| FACT_PRE_SCREENED_REPLACEMENTS | Pre-approved replacements | SecurityID, ReplacementSecurityID, Rationale |

#### Client & Executive Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| FACT_CLIENT_FLOWS | Client cash flows | FlowID, ClientID, PortfolioID, FlowType, Amount |
| FACT_FUND_FLOWS | Fund-level flows | FundID, Date, NetFlow, AUM |
| FACT_STRATEGY_PERFORMANCE | Strategy returns | StrategyID, Date, Return, Alpha, Beta |

#### Middle Office Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| FACT_TRADE_SETTLEMENT | Settlement tracking | SettlementID, TradeDate, SettlementDate, Status |
| FACT_RECONCILIATION | Position reconciliation | ReconciliationID, BreakType, BreakAmount, Status |
| FACT_NAV_CALCULATION | NAV components | PortfolioID, Date, GrossNAV, NetNAV |
| FACT_NAV_COMPONENTS | NAV breakdown | ComponentID, PortfolioID, ComponentType, Value |
| FACT_CORPORATE_ACTIONS | Corporate actions | ActionID, SecurityID, ActionType, ExDate |
| FACT_CORPORATE_ACTION_IMPACT | CA impact on positions | ImpactID, ActionID, PositionID, Adjustment |
| FACT_CASH_MOVEMENTS | Cash transactions | MovementID, PortfolioID, MovementType, Amount |
| FACT_CASH_POSITIONS | Cash balances | PortfolioID, Currency, Balance, AvailableBalance |

#### Portfolio Modelling Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| FACT_MODEL_PORTFOLIO_WEIGHTS | Model weights | ModelID, SecurityID, TargetWeight |
| FACT_RISK_FACTORS | Risk factor definitions | FactorID, FactorName, FactorReturn |
| FACT_EXPECTED_RETURNS | Expected return estimates | SecurityID, ExpectedReturn, Confidence |
| FACT_COVARIANCE_MATRIX | Return covariances | SecurityID1, SecurityID2, Covariance |
| FACT_BACKTEST_RESULTS | Backtest outputs | BacktestID, PortfolioID, StartDate, EndDate, Return |
| FACT_SIMULATION_RESULTS | Monte Carlo results | SimulationID, PathID, Date, PortfolioValue |

#### Portfolio Manager Co-Pilot Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| FACT_BRINSON_BY_SECTOR | Sector-level Brinson | PortfolioID, Sector, AllocationEffect, SelectionEffect |
| FACT_BRINSON_ATTRIBUTION | Portfolio-level Brinson | PortfolioID, Date, ActiveReturn, AllocationEffect |
| FACT_FACTOR_ATTRIBUTION | Factor contributions | PortfolioID, FactorName, Exposure, Contribution |
| FACT_HIDDEN_FACTOR_EXPOSURES | Hidden factor loadings | PortfolioID, HiddenFactor, Exposure, ExplanatoryPower |
| DIM_STRESS_SCENARIOS | Stress scenario definitions | ScenarioID, ScenarioName, Severity |
| FACT_SCENARIO_SHOCKS | Factor shocks per scenario | ScenarioID, FactorName, Shock, Confidence |
| FACT_HISTORICAL_STRESS_PERIODS | Historical crises | PeriodID, StartDate, EndDate, MarketReturn, PeakVIX |

#### Private Equity Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| DIM_PORTFOLIO_COMPANY | PE portfolio companies | CompanyID, CompanyName, Sector, InvestmentDate |
| DIM_DEAL_PIPELINE | Deal pipeline | DealID, TargetName, Stage, ExpectedClose |
| FACT_VALUE_CREATION_PLAN | Value creation initiatives | PlanID, CompanyID, Initiative, TargetValue |
| FACT_BOARD_PACK_METRICS | Board pack KPIs | MetricID, CompanyID, MetricName, Value |
| FACT_PORTFOLIO_COMPANY_KPI | Company KPIs | KPIID, CompanyID, KPIName, Value, Target |

#### Corpus Tables (for Cortex Search)

| Table | Document Types | Linkage |
|-------|---------------|---------|
| PDF_INTERNAL_CORPUS | 13 types: policy_docs, sales_templates, philosophy_docs, report_templates, macro_events, custodian_reports, reconciliation_notes, ssi_documents, ops_procedures, strategy_documents, methodology_docs, engagement_notes, ips | Global (filtered by DOCUMENT_TYPE) |
| PDF_EXTERNAL_CORPUS | 3 types: broker_research, press_releases, ngo_reports | Global (filtered by DOCUMENT_TYPE) |
| COMPANY_EVENT_TRANSCRIPTS_CORPUS | Company event transcripts | SecurityID (real data) |
| PE_BOARD_PACKS_CORPUS | PE board packs | CompanyID |
| PE_DUE_DILIGENCE_CORPUS | PE due diligence | DealID |
| PE_EXPERT_NETWORK_CORPUS | Expert network notes | DealID |
| CREDIT_AGREEMENTS_CORPUS | Credit agreements | FacilityID |
| COMPLIANCE_CERTS_CORPUS | Compliance certificates | BorrowerID |
| IC_MEMOS_CORPUS | Investment committee memos | DealID |

#### Views

| View | Description | Base Tables |
|------|-------------|-------------|
| V_SECURITY_RETURNS | Daily security returns | FACT_STOCK_PRICES |
| V_SECURITY_RETURNS_LATEST | Latest returns | FACT_STOCK_PRICES |
| V_SECURITY_LOG_RETURNS | Log returns | FACT_STOCK_PRICES |
| V_PORTFOLIO_RISK_METRICS | Portfolio risk summary | Multiple |
| V_ESG_LATEST | Latest ESG scores | FACT_ESG_SCORES |
| V_HOLDINGS_WITH_ESG | Holdings + ESG | FACT_POSITION_DAILY_ABOR, FACT_ESG_SCORES |
| V_PORTFOLIO_BENCHMARK_COMPARISON | Portfolio vs benchmark | Multiple |
| V_MACRO_REGIME | Market regime classification | FACT_VIX_DAILY, FACT_BENCHMARK_RETURNS |

### MARKET_DATA Schema

| Table | Description | Source |
|-------|-------------|--------|
| DIM_BENCHMARKS | Benchmark definitions | Synthetic |
| DIM_ANALYST | Analyst master | Synthetic |
| FACT_STOCK_PRICES | Daily OHLCV prices | Cybersyn STOCK_PRICE_TIMESERIES |
| FACT_SEC_FILING_TEXT | SEC filing text content | Cybersyn SEC_REPORT_TEXT_ATTRIBUTES |
| FACT_SEC_FINANCIALS | XBRL financial statements | Cybersyn SEC_CORPORATE_REPORT_ATTRIBUTES |
| FACT_SEC_SEGMENTS | Revenue segments | Cybersyn SEC_METRICS_TIMESERIES |
| FACT_BENCHMARK_RETURNS | Daily benchmark returns | Synthetic |
| FACT_BENCHMARK_SECTOR_WEIGHTS | Benchmark sector weights | Synthetic |
| FACT_ANALYST_COVERAGE | Analyst coverage | Synthetic |
| FACT_ESTIMATE_CONSENSUS | Consensus estimates | Derived from SEC actuals |
| FACT_ESTIMATE_DATA | Individual estimates | Synthetic |
| FACT_VIX_DAILY | VIX levels | Synthetic |
| FACT_SECTOR_RETURNS | Sector ETF returns | Cybersyn (XLK, XLV, etc.) |
| COMP_EVENT_SPEAKER_MAPPING | Speaker identification | AI_COMPLETE output |
| FACT_DIVIDENDS | Dividend declarations | SEC 8-K via AI_EXTRACT |
| FACT_POLICY_RATES | Central bank policy rates | Cybersyn BIS |
| FACT_FX_RATES | Foreign exchange rates | Cybersyn FX_RATES |
| FACT_ECONOMIC_INDICATORS | US economic indicators | Cybersyn FRED |

### RAW Schema

Document staging tables (pattern: `{DOC_TYPE}_RAW`):

| Table | Document Type |
|-------|---------------|
| BROKER_RESEARCH_RAW | Broker research |
| COMPANY_EVENT_TRANSCRIPTS_RAW | Company events |
| PRESS_RELEASES_RAW | Press releases |
| NGO_REPORTS_RAW | NGO reports |
| ENGAGEMENT_NOTES_RAW | Engagement notes |
| POLICY_DOCS_RAW | Policies |
| SALES_TEMPLATES_RAW | Sales templates |
| PHILOSOPHY_DOCS_RAW | Philosophy docs |
| REPORT_TEMPLATES_RAW | Report templates |
| MACRO_EVENTS_RAW | Macro events |
| CUSTODIAN_REPORTS_RAW | Custodian reports |
| RECONCILIATION_NOTES_RAW | Reconciliation |
| SSI_DOCUMENTS_RAW | SSI documents |
| OPS_PROCEDURES_RAW | Ops procedures |
| STRATEGY_DOCUMENTS_RAW | Strategy docs |
| METHODOLOGY_DOCS_RAW | Methodology |
| PDF_INTERNAL_CORPUS | Chunked internal PDF corpus (13 doc types, CURATED schema) |
| PDF_EXTERNAL_CORPUS | Chunked external PDF corpus (3 doc types, CURATED schema) |

---

## Dependency Graph

### CURATED Schema Dependencies

```
config.DEMO_COMPANIES (source of truth)
│
└──► DIM_ISSUER (IssuerID, CIK)
     │
     ├──► DIM_SECURITY (SecurityID → IssuerID)
     │    │
     │    ├──► FACT_TRANSACTION → FACT_POSITION_DAILY_ABOR
     │    ├──► FACT_ESG_SCORES
     │    ├──► FACT_FACTOR_EXPOSURES
     │    └──► All corpus tables (SecurityID linkage)
     │
     ├──► DIM_SUPPLY_CHAIN_RELATIONSHIPS
     └──► All MARKET_DATA tables (IssuerID/CIK linkage)

DIM_PORTFOLIO (independent)
└──► FACT_TRANSACTION, FACT_POSITION_DAILY_ABOR, client tables

DIM_BENCHMARK (independent)
└──► FACT_BENCHMARK_HOLDINGS, FACT_BENCHMARK_PERFORMANCE
```

### CIK Linkage Map

```
Cybersyn Data                          SAM_DEMO
─────────────────────────────────────────────────────────────────
COMPANY_INDEX.CIK ────────────────────► CURATED.DIM_ISSUER.CIK
     │                                       │
     ├── SEC_METRICS_TIMESERIES.CIK          ├──► FACT_SEC_FINANCIALS
     ├── SEC_REPORT_TEXT_ATTRIBUTES.CIK      ├──► FACT_SEC_FILING_TEXT
     ├── SEC_CORPORATE_REPORT_ATTRS.CIK      ├──► FACT_SEC_SEGMENTS
     └── STOCK_PRICE_TIMESERIES (ticker)     └──► FACT_STOCK_PRICES

Coverage: All 79 companies have CIK linkage (100% SEC data coverage)
```

---

## Impact Analysis Matrix

| Changed Object | Immediate Impact | Must Rebuild |
|----------------|------------------|--------------|
| **config.DEMO_COMPANIES** | All data generation | Full rebuild |
| **DIM_ISSUER** | All FK references break | DIM_SECURITY, all MARKET_DATA, all corpus, all semantic views |
| **DIM_SECURITY** | Holdings break | FACT_TRANSACTION, FACT_POSITION_DAILY_ABOR, FACT_ESG_SCORES, corpus tables |
| **DIM_PORTFOLIO** | Portfolio analytics break | FACT_TRANSACTION, FACT_POSITION_DAILY_ABOR, client tables |
| **FACT_POSITION_DAILY_ABOR** | Holdings views break | V_HOLDINGS_WITH_ESG, SAM_PORTFOLIO_VIEW |
| **FACT_STOCK_PRICES** | Price analytics break | SAM_MARKET_VIEW, V_SECURITY_RETURNS |
| **FACT_SEC_FINANCIALS** | Fundamentals break | FACT_ESTIMATE_CONSENSUS, SAM_RESEARCH_VIEW |
| **Attribution tables** | Attribution analysis breaks | SAM_ATTRIBUTION_VIEW |
| ***_CORPUS tables** | Search breaks | Corresponding SAM_* Cortex Search service |
| **Semantic views** | Agent queries break | Agents using that view as tool resource |

---

## Module Responsibility Matrix

| Module | Creates | Depends On |
|--------|---------|------------|
| `main.py` | Orchestration | All modules |
| `data/structured.py` | CURATED tables, views | config |
| `data/market_data.py` | MARKET_DATA tables | CURATED.DIM_ISSUER, CURATED.DIM_SECURITY, Cybersyn |
| `data/unstructured.py` | RAW/*_RAW tables | CURATED dimensions, hydration_engine |
| `data/transcripts.py` | COMPANY_EVENT_TRANSCRIPTS_CORPUS | Cybersyn, DIM_SECURITY |
| `data/pipelines.py` | Pipeline tasks, stages, streams | RAW tables |
| `ai/semantic_views.py` + `ai/semantic_view_definitions/*.yaml` | AI semantic views (YAML-based) | CURATED + MARKET_DATA tables |
| `ai/cortex_search.py` | Cortex Search services | CURATED corpus tables |
| `ai/agents.py` | AI agents | Semantic views, search services |
| `ai/builder.py` | AI orchestration, procedures | All AI modules |

---

## Pipeline Architecture

### PDF Ingestion Pipeline

```
PDF Upload → PDF_*_STAGE → PDF_*_STREAM
                              │
                              ▼
                    PDF_*_PIPELINE_ROOT (5 min schedule)
                              │
                              ▼
                    PDF_*_PARSE (AI_PARSE_DOCUMENT)
                    ├── DOC_TYPE = SPLIT_PART(RELATIVE_PATH, '/', 1)
                    └── Extracts text, stores in *_RAW with DOC_TYPE
                              │
                              ▼
                    PDF_*_CHUNK (conditional >512 tokens)
                    ├── DOCUMENT_TYPE = DOC_TYPE (from RAW table)
                    └── PUBLISH_DATE = COALESCE(
                          TRY_TO_DATE(REGEXP_SUBSTR(FILE_NAME, '\d{8}'), 'YYYYMMDD'),
                          DATE(PARSED_AT))
                              │
                              ▼
                    PDF_*_CORPUS table (shared by all doc types)
                              │
                              ▼
                    Cortex Search service (SAM_INTERNAL_DOCS / SAM_EXTERNAL_DOCS)
                    └── Agent-side filter: {"@eq": {"DOCUMENT_TYPE": "<doc_type_key>"}}
```

### Corpus Build Pipeline

```
hydration_engine → *_RAW table → CORPUS_*_BUILD task
                                       │
                                       ▼
                         AI_COUNT_TOKENS check
                                       │
                                       ▼
                    SPLIT_TEXT_RECURSIVE_CHARACTER (if >512)
                                       │
                                       ▼
                         *_CORPUS table → Cortex Search
```

### Transcript Pipeline

```
Cybersyn.COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES_V2
                    │
                    ▼
    COMPANY_EVENT_TRANSCRIPTS_RAW
                    │
                    ▼
    AI_COMPLETE (speaker identification)
                    │
                    ▼
    COMP_EVENT_SPEAKER_MAPPING
                    │
                    ▼
    SPLIT_TEXT_RECURSIVE_CHARACTER
                    │
                    ▼
    COMPANY_EVENT_TRANSCRIPTS_CORPUS
                    │
                    ▼
    SAM_COMPANY_EVENTS (Cortex Search)
```

### Dividend Extraction Pipeline (AI_EXTRACT)

```
Cybersyn.SEC_REPORT_TEXT_ATTRIBUTES (8-K filings)
                    │
                    ▼
    Filter: FORM_TYPE = '8-K' AND
            TEXT LIKE '%dividend%declared%per share%record date%'
                    │
                    ▼
    AI_EXTRACT (declaration_date, dividend_per_share, record_date, payment_date)
    ┌─────────────────────────────────────────────────────────────────────┐
    │ Extracts from unstructured 8-K text:                                │
    │   - declaration_date: Date board declared dividend                  │
    │   - dividend_per_share: Dollar amount per share                     │
    │   - record_date: Shareholder eligibility date                       │
    │   - payment_date: Date dividend will be paid                        │
    └─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
    Calculate EX_DATE (1 business day before RECORD_DATE)
    ┌─────────────────────────────────────────────────────────────────────┐
    │ Ex-Date = RECORD_DATE - 1 business day                              │
    │   - If Monday: Ex-Date = Friday (skip weekend)                      │
    │   - If Sunday: Ex-Date = Thursday (skip weekend)                    │
    │   - Otherwise: Ex-Date = RECORD_DATE - 1 day                        │
    └─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
    MARKET_DATA.FACT_DIVIDENDS (real dividend data)
                    │
                    ▼
    CURATED.FACT_CORPORATE_ACTIONS (ACTION_TYPE='DIVIDEND')
```
