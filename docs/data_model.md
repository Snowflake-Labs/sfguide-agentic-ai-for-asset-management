# SAM Demo - Data Model Documentation (100% Real Assets)

Complete documentation of the data architecture using 14,000+ authentic securities from SEC Filings dataset (OpenFIGI) following industry-standard asset management practices.

## Database Architecture

**Database**: `SAM_DEMO`  
**Schemas**: 
- **RAW**: Provider simulation + raw unstructured documents
- **CURATED**: Industry-standard dimension/fact model ready for analysis
- **MARKET_DATA**: Real and synthetic market data from external sources (NEW)
- **AI**: Semantic views and Cortex Search services

## Implementation Status (100% Real Assets + Real SEC Data)

✅ **14,000+ Real Securities**: All from authentic OpenFIGI dataset (no synthetic securities)  
✅ **3,303 Real Issuers**: Corporate hierarchies from real companies  
✅ **Authentic Identifiers**: TICKER + real Bloomberg FIGI identifiers only  
✅ **Transaction-Based Holdings**: 27,000+ holdings using real securities  
✅ **Real Stock Prices**: 5.2M+ records from SNOWFLAKE_PUBLIC_DATA_FREE (NEW)
✅ **Real SEC Financials**: 9,400+ records from 10-K/10-Q filings (NEW)
✅ **Real SEC Filing Text**: 6,300+ documents with MD&A and Risk Factors (NEW)
✅ **AI Components**: All semantic views and search services operational at scale  
✅ **Implementation Planning**: Trading costs, liquidity, risk limits, and execution data for realistic portfolio management  

## Enhanced Data Model (Industry Standard)

### Core Dimension Tables (CURATED Schema)
```sql
-- Master security dimension with immutable SecurityID (100% Real)
DIM_SECURITY               -- 14,000 real securities from OpenFIGI dataset with direct TICKER and FIGI columns
DIM_ISSUER                 -- 3,303 real issuers with corporate hierarchies
DIM_PORTFOLIO              -- 10 portfolios with enhanced information
DIM_BENCHMARK              -- 3 benchmarks (S&P 500, MSCI ACWI, Nasdaq 100)
```

### Core Fact Tables (CURATED Schema)
```sql
-- Transaction-based model (source of truth)
FACT_TRANSACTION           -- Canonical transaction log with 12 months history
FACT_POSITION_DAILY_ABOR   -- ABOR positions built from transactions

-- Analytics and performance tables
FACT_ESG_SCORES           -- Monthly ESG ratings with sector differentiation
FACT_FACTOR_EXPOSURES     -- Monthly factor scores (Value, Growth, Quality, etc.)
FACT_BENCHMARK_HOLDINGS   -- Benchmark constituent positions

-- Implementation planning tables
FACT_TRANSACTION_COSTS    -- Trading costs, bid-ask spreads, market impact data
FACT_PORTFOLIO_LIQUIDITY  -- Cash positions, cash flows, liquidity scores
FACT_RISK_LIMITS          -- Risk budgets, tracking error limits, concentration limits
FACT_TRADING_CALENDAR     -- Earnings dates, blackout periods, market events
FACT_TAX_IMPLICATIONS     -- Cost basis, unrealized gains, tax loss harvesting
DIM_CLIENT_MANDATES       -- Client approval thresholds, sector ranges, ESG requirements
```

### Market Data Tables (MARKET_DATA Schema) - NEW
```sql
-- Real data from SNOWFLAKE_PUBLIC_DATA_FREE
FACT_STOCK_PRICES          -- 5.2M+ real daily stock prices (OHLCV) from Nasdaq
FACT_FINANCIAL_DATA_SEC    -- 9,400+ real SEC financial metrics from 10-K/10-Q
FACT_SEC_FILING_TEXT       -- 6,300+ real SEC filing text (MD&A, Risk Factors)

-- Synthetic market data (used as fallback)
FACT_FINANCIAL_DATA        -- 90K synthetic quarterly financial metrics
FACT_ESTIMATE_CONSENSUS    -- 24K synthetic analyst estimates
DIM_COMPANY                -- Company master data with CIK linkage

-- Reference data
DIM_ANALYST                -- Broker analyst dimension
FACT_ESTIMATE_DATA         -- Individual analyst estimates
FACT_BROKER_RATING_HISTORY -- Broker rating history
```

## Implementation Planning Data Model (NEW)

### Portfolio Implementation Tables
The enhanced data model includes comprehensive implementation planning data to support realistic trading execution, risk management, and operational workflows:

#### Transaction Cost Analysis
```sql
FACT_TRANSACTION_COSTS (
    SecurityID              BIGINT,
    COST_DATE              DATE,
    BID_ASK_SPREAD_BPS     DECIMAL(18,4),    -- Bid-ask spread in basis points
    AVG_DAILY_VOLUME_M     DECIMAL(18,4),    -- Average daily volume in millions
    MARKET_IMPACT_BPS_PER_1M DECIMAL(18,4),  -- Market impact per $1M traded
    COMMISSION_BPS         DECIMAL(18,4),    -- Commission rate in basis points
    SETTLEMENT_DAYS        INTEGER           -- Settlement period
)
```

#### Liquidity & Cash Management
```sql
FACT_PORTFOLIO_LIQUIDITY (
    PortfolioID            BIGINT,
    LIQUIDITY_DATE         DATE,
    CASH_POSITION_USD      DECIMAL(38,10),   -- Available cash position
    NET_CASHFLOW_30D_USD   DECIMAL(38,10),   -- Expected 30-day cash flow
    PORTFOLIO_LIQUIDITY_SCORE INTEGER,       -- Liquidity rating (1-10)
    REBALANCING_FREQUENCY_DAYS INTEGER       -- Rebalancing frequency
)
```

#### Risk Budget Management
```sql
FACT_RISK_LIMITS (
    PortfolioID            BIGINT,
    LIMITS_DATE            DATE,
    TRACKING_ERROR_LIMIT_PCT DECIMAL(18,8),  -- Maximum tracking error
    CURRENT_TRACKING_ERROR_PCT DECIMAL(18,8), -- Current tracking error
    MAX_SINGLE_POSITION_PCT DECIMAL(18,8),   -- Maximum position size
    MAX_SECTOR_CONCENTRATION_PCT DECIMAL(18,8), -- Maximum sector allocation
    RISK_BUDGET_UTILIZATION_PCT DECIMAL(18,8), -- Risk budget used
    VAR_LIMIT_1DAY_PCT     DECIMAL(18,8)     -- 1-day VaR limit
)
```

#### Trading Calendar & Events
```sql
FACT_TRADING_CALENDAR (
    SecurityID             BIGINT,
    EVENT_DATE             DATE,
    EVENT_TYPE             VARCHAR(50),      -- EARNINGS_ANNOUNCEMENT, etc.
    IS_BLACKOUT_PERIOD     BOOLEAN,          -- Trading restricted
    EXPECTED_VIX_LEVEL     DECIMAL(18,4),    -- Market volatility forecast
    IS_OPTIONS_EXPIRATION  BOOLEAN           -- Options expiration indicator
)
```

#### Tax Optimization
```sql
FACT_TAX_IMPLICATIONS (
    PortfolioID            BIGINT,
    SecurityID             BIGINT,
    TAX_DATE               DATE,
    COST_BASIS_USD         DECIMAL(38,10),   -- Tax cost basis
    UNREALIZED_GAIN_LOSS_USD DECIMAL(38,10), -- Unrealized P&L
    HOLDING_PERIOD_DAYS    INTEGER,          -- Holding period
    TAX_TREATMENT          VARCHAR(20),      -- LONG_TERM/SHORT_TERM
    TAX_LOSS_HARVEST_OPPORTUNITY BOOLEAN,    -- Loss harvesting flag
    TAX_RATE               DECIMAL(18,8)     -- Applicable tax rate
)
```

#### Client Mandates & Compliance
```sql
DIM_CLIENT_MANDATES (
    PortfolioID            BIGINT,
    POSITION_CHANGE_APPROVAL_THRESHOLD_PCT DECIMAL(18,8), -- Approval threshold
    SECTOR_ALLOCATION_RANGES_JSON VARCHAR(1000),          -- Sector limits JSON
    MIN_ESG_RATING         VARCHAR(10),                   -- ESG requirements
    EXCLUSION_SECTORS_JSON VARCHAR(1000),                 -- Exclusion list JSON
    MAX_REBALANCING_FREQUENCY_DAYS INTEGER                -- Rebalancing limits
)
```

### Enhanced Document Integration (CURATED Schema)
```sql
-- Document corpus tables with SecurityID/IssuerID linkage
BROKER_RESEARCH_CORPUS     -- 40 analyst reports with SecurityID linkage
EARNINGS_TRANSCRIPTS_CORPUS -- 35 earnings call summaries with SecurityID linkage
PRESS_RELEASES_CORPUS      -- 35 corporate press releases with SecurityID linkage
```

## Key Architecture Benefits

### Industry-Standard Capabilities
- **Immutable SecurityID**: Corporate action resilience and temporal integrity
- **Transaction Audit Trail**: Complete history for compliance and reconciliation
- **Issuer Hierarchy**: Corporate structure and parent company analysis
- **Enhanced Document Integration**: Stable SecurityID/IssuerID linkage
- **Real Data Integration**: Authentic market data with synthetic fallback

### Enhanced Analytics Support
- **Issuer-Level Risk Analysis**: Total exposure across all securities of an issuer
- **Corporate Action Handling**: Maintain analytical continuity through ticker changes
- **Transaction-Level Analytics**: Complete audit trail for compliance
- **Temporal Consistency**: Proper handling of identifier changes over time

## AI Components (AI Schema)

### Semantic View: `SAM_ANALYST_VIEW`
**Enhanced Capabilities**:
- Portfolio analytics with issuer hierarchy support
- Multi-table relationships (Holdings → Securities → Issuers)
- Enhanced dimensions and metrics for comprehensive analysis
- Direct date column support (no DIM_DATE complexity)

**Key Metrics**:
- `TOTAL_MARKET_VALUE`: Sum of position values in base currency
- `HOLDING_COUNT`: Count of portfolio positions
- `ISSUER_EXPOSURE`: Total exposure to issuer across all securities
- `PORTFOLIO_WEIGHT_PCT`: Portfolio weight as percentage

**Key Dimensions**:
- `PORTFOLIONAME`, `DESCRIPTION`, `TICKER`, `LEGALNAME`, `SIC_DESCRIPTION`

### Enhanced Search Services
- `SAM_BROKER_RESEARCH`: Search analyst reports with SecurityID/IssuerID attributes
- `SAM_EARNINGS_TRANSCRIPTS`: Search earnings summaries with SecurityID/IssuerID attributes
- `SAM_PRESS_RELEASES`: Search corporate announcements with SecurityID/IssuerID attributes

### Real SEC Data Integration (NEW)
**Status**: ✅ Fully implemented and operational

**Data Source**: `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`

| Table | Records | Description |
|-------|---------|-------------|
| `FACT_STOCK_PRICES` | 5.2M+ | Real daily stock prices (OHLCV) from Nasdaq |
| `FACT_FINANCIAL_DATA_SEC` | 9,400+ | Real SEC financial metrics from 10-K/10-Q filings |
| `FACT_SEC_FILING_TEXT` | 6,300+ | Real SEC filing text (MD&A, Risk Factors, etc.) |

**Coverage**: ~50 companies with CIK linkage to demo data
**Integration**: Real data used when available, synthetic data for broader coverage  
**Benefits**: Authentic SEC disclosures, real financial metrics, and real stock prices

### Semantic Views for Real Data (NEW)
- `SAM_REAL_SEC_VIEW`: Query real SEC financial metrics from 10-K/10-Q filings
- `SAM_STOCK_PRICES_VIEW`: Query real daily stock prices with OHLCV data

### Search Services for Real Data (NEW)
- `SAM_REAL_SEC_FILINGS`: Search real SEC filing text (MD&A, Risk Factors, Business Descriptions)  

## Data Quality Standards (Verified)

### Validation Results
✅ **Portfolio Weights**: Sum to 100% (±0.1% tolerance)  
✅ **Transaction Integrity**: Transaction log balances to ABOR positions  
✅ **Security Identifiers**: TICKER and FIGI columns properly populated  
✅ **Price Data**: No negative prices, realistic ranges by asset class  
✅ **Date Consistency**: Business days only, proper date ranges  
✅ **Foreign Key Relationships**: All relationships valid and tested  

### Enhanced Validation Capabilities
✅ **Transaction Balancing**: FACT_TRANSACTION sums to FACT_POSITION_DAILY_ABOR  
✅ **Issuer Hierarchy**: Corporate relationships properly established  
✅ **SecurityID Integrity**: Direct TICKER and FIGI columns validated  
✅ **Document Linkage**: Stable SecurityID/IssuerID linkage validated  

## Sample Data Highlights

### Enhanced Portfolio Examples
- SAM Global Flagship Multi-Asset: $2.5B AUM with multi-asset holdings
- SAM ESG Leaders Global Equity: $1.8B AUM with ESG-focused positions  
- SAM Global Thematic Growth: $1.5B AUM with technology concentration

### Enhanced Securities Examples
- **Real Tickers**: AAPL, MSFT, NVDA, GOOGL, AMZN, META with proper issuer linkage
- **Immutable SecurityID**: Each security has stable identifier surviving corporate actions
- **Issuer Hierarchies**: Corporate structure relationships established
- **Global Coverage**: US (55%), Europe (30%), APAC/EM (15%) with authentic issuers

### Enhanced Content Quality
- **SecurityID Integration**: All documents linked via stable identifiers
- **Issuer-Level Documents**: NGO reports and engagement notes apply to issuer level
- **Professional UK English**: Consistent throughout all generated content
- **Realistic Financial Context**: Sector-specific content with authentic metrics

## Migration Benefits Achieved

### From Simple Model To Industry Standard
- **Before**: Flat security table with TICKER primary key
- **After**: Immutable SecurityID with full symbology spine
- **Before**: Direct position snapshots
- **After**: Transaction-based holdings with audit trail
- **Before**: String-based document linkage
- **After**: Stable SecurityID/IssuerID document relationships

### Enhanced Capabilities Enabled
- **Issuer-level analysis**: "What's our total exposure to Apple across all securities?"
- **Corporate hierarchy queries**: "Show me all holdings in technology conglomerates"
- **Enhanced document search**: "Find ESG reports for all our technology holdings"
- **Transaction analytics**: Complete audit trail for compliance and analysis

The SAM demo now implements a professional, industry-standard asset management data model that provides enhanced analytics capabilities while maintaining all existing functionality.

## Related Documentation

- **`docs/data_lineage.md`** - Complete data flow, dependencies, and impact analysis
- **`docs/real_data_integration_analysis.md`** - Real SEC data integration details
- **`.cursor/rules/data-generation.mdc`** - Data generation patterns and best practices