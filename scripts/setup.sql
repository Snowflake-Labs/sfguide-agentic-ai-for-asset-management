-- ============================================================================
--             SNOWCREST ASSET MANAGEMENT (SAM) AI DEMO - COMPLETE SETUP
-- ============================================================================
--
-- This script contains EVERYTHING needed for the SAM Asset Management AI Demo.
-- Just run this entire script - it handles prerequisites automatically!
--
-- PREREQUISITES:
--   1. Snowflake account with Cortex enabled
--   2. ACCOUNTADMIN role
--   3. That's it! The script will install required data automatically.
--
-- WHAT THIS CREATES:
--   - Installs Snowflake Public Data (Free) with SEC Filings + OpenFIGI
--   - 2 Warehouses: EXECUTION (MEDIUM), CORTEX_SEARCH (LARGE)
--   - 8 Snowflake Intelligence Agents
--   - 14,000+ real securities from SEC Filings (OpenFIGI)
--   - 10 portfolios with 27,000+ holdings
--   - 7 Semantic Views for Cortex Analyst
--   - 16 Cortex Search Services
--   - 85+ AI-generated documents 
-- ============================================================================

-- Set query tag for tracking
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"sam_ai_demo","version":{"major":1,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

-- ============================================================================
-- SECTION 0: INSTALL REQUIRED DATA (Snowflake Public Data - Free)
-- ============================================================================
--
-- This installs the free Snowflake Public Data listing which includes:
--   - 90,000+ real securities from OpenFIGI
--   - SEC filing data for all US public companies
--   - Company information and financial data
--
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Request the Snowflake Public Data (Free) listing
CALL SYSTEM$REQUEST_LISTING_AND_WAIT('GZTSZ290BV255');

-- Accept legal terms for the listing
CALL SYSTEM$ACCEPT_LEGAL_TERMS('DATA_EXCHANGE_LISTING', 'GZTSZ290BV255');

-- Create database from the listing (IF NOT EXISTS - safe to run multiple times)
CREATE DATABASE IF NOT EXISTS MARKETPLACE_CYBERSYN
  FROM LISTING 'GZTSZ290BV255';

-- Verify installation
SELECT '✅ Snowflake Public Data installed successfully!' as status,
       'Database: MARKETPLACE_CYBERSYN' as database_name,
       'Schema: PUBLIC_DATA_FREE' as schema_name;

-- ============================================================================
-- SECTION 1: INFRASTRUCTURE SETUP
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ----------------------------------------------------------------------------
-- Step 1.1: Create Role
-- ----------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS SAM_DEMO_ROLE;
GRANT ROLE SAM_DEMO_ROLE TO ROLE ACCOUNTADMIN;

-- Grant Cortex access
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE ACCOUNTADMIN;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE SAM_DEMO_ROLE;

-- Enable cross-region inference for Cortex models
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- ----------------------------------------------------------------------------
-- Step 1.2: Create Database and Schemas
-- ----------------------------------------------------------------------------
CREATE OR REPLACE DATABASE SAM_DEMO;

-- Create schemas
CREATE OR REPLACE SCHEMA SAM_DEMO.RAW;
CREATE OR REPLACE SCHEMA SAM_DEMO.CURATED;
CREATE OR REPLACE SCHEMA SAM_DEMO.AI;

-- ----------------------------------------------------------------------------
-- Step 1.3: Create Warehouses
-- ----------------------------------------------------------------------------
CREATE OR REPLACE WAREHOUSE SAM_DEMO_EXECUTION_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    COMMENT = 'Warehouse for demo setup and agent execution';

CREATE OR REPLACE WAREHOUSE SAM_DEMO_CORTEX_WH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    COMMENT = 'Dedicated warehouse for Cortex Search services';

-- ----------------------------------------------------------------------------
-- Step 1.4: Grant Privileges
-- ----------------------------------------------------------------------------
-- Grant database and schema access
GRANT USAGE ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- Grant warehouse access
GRANT USAGE ON WAREHOUSE SAM_DEMO_EXECUTION_WH TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON WAREHOUSE SAM_DEMO_CORTEX_WH TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on all current and future objects
GRANT ALL ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

GRANT ALL ON ALL TABLES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

GRANT ALL ON FUTURE TABLES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

GRANT ALL ON ALL VIEWS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON FUTURE VIEWS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;

GRANT ALL ON ALL PROCEDURES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON FUTURE PROCEDURES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

GRANT ALL ON ALL FUNCTIONS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL ON FUTURE FUNCTIONS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- ----------------------------------------------------------------------------
-- Step 1.5: Snowflake Intelligence Setup
-- ----------------------------------------------------------------------------
CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;
GRANT CREATE SNOWFLAKE INTELLIGENCE ON ACCOUNT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE PUBLIC;
GRANT CREATE AGENT ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- Set context for remaining operations
USE WAREHOUSE SAM_DEMO_EXECUTION_WH;
USE SCHEMA SAM_DEMO.CURATED;

-- ============================================================================
-- SECTION 2: REAL ASSETS VIEW (From SEC Filings OpenFIGI Data)
-- ============================================================================

-- Create view to extract real securities from SEC Filings dataset
CREATE OR REPLACE VIEW SAM_DEMO.CURATED.V_REAL_ASSETS AS
WITH raw_assets AS (
    -- Extract unique securities from SEC filings with OpenFIGI identifiers
    SELECT DISTINCT
        f.TOP_LEVEL_OPENFIGI_ID as FIGI,
        f.OPENFIGI_COMPOSITE_ID as COMPOSITE_FIGI,
        f.OPENFIGI_SHARE_CLASS_ID as SHARE_CLASS_FIGI,
        f.PRIMARY_TICKER as Ticker,
        f.SECURITY_NAME as SecurityName,
        f.EXCHANGE_CODES as ExchangeCode,
        f.ASSET_CLASS as MarketSector,
        f.SECURITY_TYPE as SecurityType,
        f.SECURITY_SUBTYPE as SecurityType2,
        i.CIK as CIK,
        i.COMPANY_NAME as CompanyName,
        i.SIC_CODE_DESCRIPTION as SIC_DESCRIPTION
    FROM MARKETPLACE_CYBERSYN.PUBLIC_DATA_FREE.OPENFIGI_SECURITY_INDEX f
    JOIN MARKETPLACE_CYBERSYN.PUBLIC_DATA_FREE.COMPANY_SECURITY_RELATIONSHIPS csr
        ON f.TOP_LEVEL_OPENFIGI_ID = csr.SECURITY_ID
    JOIN MARKETPLACE_CYBERSYN.PUBLIC_DATA_FREE.SEC_CIK_INDEX i 
        ON csr.COMPANY_ID = i.COMPANY_ID
    JOIN MARKETPLACE_CYBERSYN.PUBLIC_DATA_FREE.SEC_CORPORATE_REPORT_ATTRIBUTES sra 
        ON i.CIK = sra.CIK
    WHERE f.ASSET_CLASS = 'Equity'
        AND f.PRIMARY_TICKER IS NOT NULL
        AND LENGTH(f.PRIMARY_TICKER) BETWEEN 1 AND 5
        AND i.COMPANY_ID IS NOT NULL
),
deduplicated AS (
    -- Deduplicate by FIGI, preferring securities with more complete data
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY FIGI 
            ORDER BY 
                CASE WHEN CompanyName IS NOT NULL THEN 0 ELSE 1 END,
                CASE WHEN SIC_DESCRIPTION IS NOT NULL THEN 0 ELSE 1 END,
                SecurityName
        ) as rn
    FROM raw_assets
)
SELECT 
    FIGI,
    COMPOSITE_FIGI,
    SHARE_CLASS_FIGI,
    Ticker,
    SecurityName,
    ExchangeCode,
    MarketSector,
    SecurityType,
    SecurityType2,
    CIK,
    CompanyName,
    SIC_DESCRIPTION,
    -- Derive asset class
    CASE 
        WHEN MarketSector = 'Equity' THEN 'Equity'
        WHEN MarketSector = 'Corp' THEN 'Corporate Bond'
        ELSE 'Other'
    END as AssetClass,
    -- Derive country (all US for NYSE/NASDAQ)
    'US' as CountryOfRisk
FROM deduplicated
WHERE rn = 1;

-- ============================================================================
-- SECTION 3: DIMENSION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Step 3.1: DIM_ISSUER - Issuer/Company Dimension
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.DIM_ISSUER AS
WITH raw_issuers AS (
    SELECT DISTINCT
        CIK,
        CompanyName as LegalName,
        SIC_DESCRIPTION,
        CountryOfRisk as CountryOfIncorporation,
        Ticker as PrimaryTicker
    FROM SAM_DEMO.CURATED.V_REAL_ASSETS
    WHERE CompanyName IS NOT NULL
),
ranked_issuers AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY CIK 
            ORDER BY 
                CASE WHEN SIC_DESCRIPTION IS NOT NULL THEN 0 ELSE 1 END,
                LegalName
        ) as rn
    FROM raw_issuers
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY CIK) as IssuerID,
    NULL as UltimateParentIssuerID,
    LegalName,
    'LEI_' || LPAD(ROW_NUMBER() OVER (ORDER BY CIK)::VARCHAR, 18, '0') as LEI,
    CountryOfIncorporation,
    COALESCE(SIC_DESCRIPTION, 'Diversified') as SIC_DESCRIPTION,
    CIK,
    PrimaryTicker
FROM ranked_issuers
WHERE rn = 1;

-- ----------------------------------------------------------------------------
-- Step 3.2: DIM_SECURITY - Security Master Dimension
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.DIM_SECURITY AS
WITH security_base AS (
    SELECT 
        v.FIGI,
        v.COMPOSITE_FIGI,
        v.SHARE_CLASS_FIGI,
        v.Ticker,
        v.SecurityName as Description,
        v.ExchangeCode,
        v.AssetClass,
        v.CountryOfRisk,
        v.CIK,
        i.IssuerID,
        -- Parse coupon rate for bonds (default 5.0 if not parseable)
        CASE 
            WHEN v.AssetClass = 'Corporate Bond' 
            THEN COALESCE(
                TRY_CAST(REGEXP_SUBSTR(v.SecurityName, '([0-9]+\\.?[0-9]*)%') AS DECIMAL(5,2)),
                5.0
            )
            ELSE NULL
        END as CouponRate,
        -- Parse maturity date for bonds (default 2030-01-01 if not parseable)
        CASE 
            WHEN v.AssetClass = 'Corporate Bond' 
            THEN COALESCE(
                TRY_TO_DATE(REGEXP_SUBSTR(v.SecurityName, '\\d{2}/\\d{2}/\\d{4}'), 'MM/DD/YYYY'),
                DATE('2030-01-01')
            )
            ELSE NULL
        END as MaturityDate,
        -- Match method for data lineage
        CASE 
            WHEN i.CIK IS NOT NULL THEN 'CIK'
            WHEN i.LegalName = v.CompanyName THEN 'SECURITY_NAME'
            ELSE 'SYNTHETIC_FROM_SECURITY'
        END as match_method
    FROM SAM_DEMO.CURATED.V_REAL_ASSETS v
    LEFT JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON v.CIK = i.CIK
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY FIGI) as SecurityID,
    FIGI,
    COMPOSITE_FIGI,
    SHARE_CLASS_FIGI,
    Ticker,
    Description,
    ExchangeCode,
    AssetClass,
    CountryOfRisk,
    COALESCE(IssuerID, 1) as IssuerID,
    CouponRate,
    MaturityDate,
    match_method
FROM security_base;

-- ----------------------------------------------------------------------------
-- Step 3.3: DIM_PORTFOLIO - Portfolio Dimension
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.DIM_PORTFOLIO (
    PortfolioID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PortfolioCode VARCHAR(50) NOT NULL,
    PortfolioName VARCHAR(255) NOT NULL,
    Strategy VARCHAR(100),
    BaseCurrency VARCHAR(3) DEFAULT 'USD',
    InceptionDate DATE
);

INSERT INTO SAM_DEMO.CURATED.DIM_PORTFOLIO (PortfolioCode, PortfolioName, Strategy, BaseCurrency, InceptionDate)
VALUES
    ('SAM_01', 'SAM Technology & Infrastructure', 'Active Equity', 'USD', '2019-01-15'),
    ('SAM_02', 'SAM Global Thematic Growth', 'Active Equity', 'USD', '2019-03-01'),
    ('SAM_03', 'SAM AI & Digital Innovation', 'Active Equity', 'USD', '2020-06-01'),
    ('SAM_04', 'SAM Sustainable Leaders ESG', 'ESG Integration', 'USD', '2019-09-01'),
    ('SAM_05', 'SAM Climate Transition Fund', 'ESG Integration', 'USD', '2021-01-01'),
    ('SAM_06', 'SAM Multi-Asset Balanced', 'Multi-Asset', 'USD', '2018-01-01'),
    ('SAM_07', 'SAM Global Income Plus', 'Fixed Income', 'USD', '2019-06-01'),
    ('SAM_08', 'SAM Emerging Markets Growth', 'Active Equity', 'USD', '2020-03-01'),
    ('SAM_09', 'SAM US Core Equity', 'Active Equity', 'USD', '2018-06-01'),
    ('SAM_10', 'SAM Flagship Growth Fund', 'Active Equity', 'USD', '2017-01-01');

-- ----------------------------------------------------------------------------
-- Step 3.4: DIM_BENCHMARK - Benchmark Dimension
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.DIM_BENCHMARK (
    BenchmarkID BIGINT IDENTITY(1,1) PRIMARY KEY,
    BenchmarkName VARCHAR(255) NOT NULL,
    Provider VARCHAR(100)
);

INSERT INTO SAM_DEMO.CURATED.DIM_BENCHMARK (BenchmarkName, Provider)
VALUES
    ('S&P 500', 'S&P Global'),
    ('MSCI ACWI', 'MSCI'),
    ('Nasdaq 100', 'Nasdaq'),
    ('Bloomberg US Aggregate', 'Bloomberg'),
    ('MSCI World ESG Leaders', 'MSCI'),
    ('Russell 2000', 'FTSE Russell');

-- ----------------------------------------------------------------------------
-- Step 3.5: DIM_COUNTERPARTY - Counterparty Dimension
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.DIM_COUNTERPARTY (
    CounterpartyID BIGINT IDENTITY(1,1) PRIMARY KEY,
    CounterpartyName VARCHAR(255) NOT NULL,
    CounterpartyType VARCHAR(50),
    HistoricalFailRate DECIMAL(5,4),
    AverageSettlementTime DECIMAL(5,2),
    RiskRating VARCHAR(10)
);

INSERT INTO SAM_DEMO.CURATED.DIM_COUNTERPARTY (CounterpartyName, CounterpartyType, HistoricalFailRate, AverageSettlementTime, RiskRating)
VALUES
    ('Goldman Sachs', 'Broker', 0.02, 1.8, 'A'),
    ('Morgan Stanley', 'Broker', 0.015, 1.9, 'A'),
    ('JP Morgan', 'Broker', 0.01, 1.7, 'AA'),
    ('Barclays', 'Broker', 0.025, 2.1, 'A'),
    ('Credit Suisse', 'Broker', 0.03, 2.3, 'BBB'),
    ('Deutsche Bank', 'Broker', 0.028, 2.2, 'BBB'),
    ('BNP Paribas', 'Broker', 0.018, 1.9, 'A'),
    ('UBS', 'Broker', 0.012, 1.8, 'AA'),
    ('Citi', 'Broker', 0.015, 1.9, 'A'),
    ('Bank of America', 'Broker', 0.013, 1.8, 'A'),
    ('BNY Mellon', 'Custodian', 0.005, 1.5, 'AA'),
    ('State Street', 'Custodian', 0.005, 1.5, 'AA'),
    ('JPM Custody', 'Custodian', 0.004, 1.5, 'AA'),
    ('Northern Trust', 'Custodian', 0.006, 1.6, 'AA'),
    ('HSBC Custody', 'Custodian', 0.007, 1.7, 'A'),
    ('Prime Broker A', 'Prime', 0.02, 1.9, 'A'),
    ('Prime Broker B', 'Prime', 0.022, 2.0, 'A'),
    ('Clearing Firm A', 'Broker', 0.015, 1.8, 'A'),
    ('Clearing Firm B', 'Broker', 0.017, 1.9, 'A'),
    ('Market Maker A', 'Broker', 0.02, 2.0, 'BBB');

-- ----------------------------------------------------------------------------
-- Step 3.6: DIM_CUSTODIAN - Custodian Dimension
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.DIM_CUSTODIAN (
    CustodianID BIGINT IDENTITY(1,1) PRIMARY KEY,
    CustodianName VARCHAR(255) NOT NULL,
    CustodianType VARCHAR(100),
    CoverageRegions VARCHAR(255),
    ServiceLevel VARCHAR(50)
);

INSERT INTO SAM_DEMO.CURATED.DIM_CUSTODIAN (CustodianName, CustodianType, CoverageRegions, ServiceLevel)
VALUES
    ('BNY Mellon', 'Global Custodian', 'Americas, EMEA, APAC', 'Premium'),
    ('State Street', 'Global Custodian', 'Americas, EMEA, APAC', 'Premium'),
    ('JPMorgan Custody', 'Global Custodian', 'Americas, EMEA, APAC', 'Premium'),
    ('Northern Trust', 'Regional Custodian', 'Americas, EMEA', 'Standard'),
    ('HSBC Custody', 'Global Custodian', 'EMEA, APAC', 'Standard'),
    ('Citi Custody', 'Global Custodian', 'Americas, EMEA, APAC', 'Premium'),
    ('Deutsche Bank Custody', 'Regional Custodian', 'EMEA', 'Standard'),
    ('BNP Paribas Securities Services', 'Regional Custodian', 'EMEA', 'Standard');

-- ============================================================================
-- SECTION 4: FACT TABLES - TRANSACTION AND POSITION DATA
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Step 4.1: FACT_TRANSACTION - Transaction History
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_TRANSACTION AS
WITH all_us_securities AS (
    SELECT 
        s.SecurityID,
        s.IssuerID,
        s.Ticker,
        s.FIGI,
        CASE 
            -- Priority 1-4: Demo companies (NVDA, AAPL, MSFT, GOOGL, TSM, AMD)
            WHEN s.Ticker = 'NVDA' THEN 1
            WHEN s.Ticker = 'AAPL' THEN 2
            WHEN s.Ticker = 'MSFT' THEN 3
            WHEN s.Ticker = 'GOOGL' THEN 4
            WHEN s.Ticker = 'TSM' THEN 4
            WHEN s.Ticker = 'AMD' THEN 4
            -- Priority 5: Other major US stocks
            WHEN s.Ticker IN ('AMZN', 'META', 'TSLA', 'JPM', 'V', 'MA', 'HD', 'PG', 'JNJ', 'UNH', 'XOM', 'CVX', 'BAC', 'WMT', 'DIS', 'NFLX', 'CRM', 'ADBE', 'INTC', 'CSCO')
                 AND i.CountryOfIncorporation = 'US' THEN 5
            -- Priority 6: All other US equities
            WHEN i.CountryOfIncorporation = 'US' AND s.AssetClass = 'Equity' THEN 6
            -- Priority 7: Non-US equities
            WHEN s.AssetClass = 'Equity' THEN 7
            -- Priority 8: All other asset types
            ELSE 8
        END as priority,
        ROW_NUMBER() OVER (PARTITION BY s.IssuerID ORDER BY 
            CASE 
                WHEN s.Ticker IN ('NVDA', 'AAPL', 'MSFT', 'GOOGL', 'TSM', 'AMD') THEN 1
                WHEN s.AssetClass = 'Equity' THEN 10
                ELSE 20
            END,
            LENGTH(s.Ticker),
            s.SecurityID
        ) as issuer_rank
    FROM SAM_DEMO.CURATED.DIM_SECURITY s
    JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
    WHERE s.AssetClass = 'Equity'
),
major_us_securities AS (
    SELECT 
        SecurityID,
        Ticker,
        FIGI,
        priority
    FROM all_us_securities
    WHERE issuer_rank = 1
),
portfolio_securities AS (
    SELECT 
        p.PortfolioID,
        p.PortfolioName,
        s.SecurityID,
        s.Ticker,
        s.priority,
        s.priority as portfolio_priority,
        ROW_NUMBER() OVER (PARTITION BY p.PortfolioID ORDER BY s.priority, RANDOM()) as rn
    FROM SAM_DEMO.CURATED.DIM_PORTFOLIO p
    CROSS JOIN major_us_securities s
),
selected_holdings AS (
    SELECT PortfolioID, SecurityID
    FROM portfolio_securities
    WHERE rn <= 45
),
business_days AS (
    SELECT DATEADD(day, seq4(), DATEADD(month, -12, CURRENT_DATE())) as trade_date
    FROM TABLE(GENERATOR(rowcount => 365))
    WHERE DAYOFWEEK(trade_date) BETWEEN 1 AND 5
),
trading_intensity AS (
    SELECT 
        trade_date,
        CASE 
            WHEN (HASH(trade_date) % 100) < 15 THEN 0.6
            WHEN (HASH(trade_date) % 100) < 40 THEN 0.3
            WHEN (HASH(trade_date) % 100) < 75 THEN 0.1
            ELSE 0.0
        END as portfolio_trade_probability
    FROM business_days
),
portfolio_trading_days AS (
    SELECT 
        p.PortfolioID,
        ti.trade_date
    FROM SAM_DEMO.CURATED.DIM_PORTFOLIO p
    CROSS JOIN trading_intensity ti
    WHERE ti.portfolio_trade_probability > 0
    AND (HASH(p.PortfolioID, ti.trade_date) % 100) < (ti.portfolio_trade_probability * 100)
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY sh.PortfolioID, sh.SecurityID, ptd.trade_date) as TransactionID,
    ptd.trade_date as TransactionDate,
    ptd.trade_date as TradeDate,
    sh.PortfolioID,
    sh.SecurityID,
    'BUY' as TransactionType,
    DATEADD(day, 2, ptd.trade_date) as SettleDate,
    UNIFORM(100, 10000, RANDOM()) as Quantity,
    UNIFORM(50, 500, RANDOM()) as Price,
    Quantity * Price as GrossAmount_Local,
    UNIFORM(5, 50, RANDOM()) as Commission_Local,
    'USD' as Currency,
    'ABOR' as SourceSystem,
    CONCAT('TXN_', ROW_NUMBER() OVER (ORDER BY sh.PortfolioID, sh.SecurityID, ptd.trade_date)) as SourceTransactionID
FROM selected_holdings sh
JOIN portfolio_trading_days ptd ON sh.PortfolioID = ptd.PortfolioID
WHERE (HASH(sh.SecurityID, ptd.trade_date) % 100) < 20;

-- ----------------------------------------------------------------------------
-- Step 4.2: FACT_POSITION_DAILY_ABOR - Daily Position Snapshots
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR AS
WITH monthly_dates AS (
    SELECT LAST_DAY(DATEADD(month, seq4(), DATEADD(year, -5, CURRENT_DATE()))) as position_date
    FROM TABLE(GENERATOR(rowcount => 60))
),
transaction_balances AS (
    SELECT 
        PortfolioID,
        SecurityID,
        SUM(CASE WHEN TransactionType = 'BUY' THEN Quantity ELSE -Quantity END) as TotalQuantity,
        AVG(Price) as AvgPrice
    FROM SAM_DEMO.CURATED.FACT_TRANSACTION
    GROUP BY PortfolioID, SecurityID
    HAVING TotalQuantity > 0
),
position_snapshots AS (
    SELECT 
        md.position_date as HoldingDate,
        tb.PortfolioID,
        tb.SecurityID,
        tb.TotalQuantity as Quantity,
        tb.TotalQuantity * tb.AvgPrice as MarketValue_Local,
        tb.TotalQuantity * tb.AvgPrice as MarketValue_Base,
        tb.TotalQuantity * tb.AvgPrice * 0.95 as CostBasis_Local,
        tb.TotalQuantity * tb.AvgPrice * 0.95 as CostBasis_Base,
        0 as AccruedInterest_Local
    FROM monthly_dates md
    CROSS JOIN transaction_balances tb
),
portfolio_totals AS (
    SELECT 
        HoldingDate,
        PortfolioID,
        SUM(MarketValue_Base) as PortfolioTotal
    FROM position_snapshots
    GROUP BY HoldingDate, PortfolioID
)
SELECT 
    ps.*,
    ps.MarketValue_Base / pt.PortfolioTotal as PortfolioWeight
FROM position_snapshots ps
JOIN portfolio_totals pt ON ps.HoldingDate = pt.HoldingDate AND ps.PortfolioID = pt.PortfolioID;

-- ============================================================================
-- SECTION 5: MARKET DATA AND ANALYTICS FACT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Step 5.1: FACT_MARKETDATA_TIMESERIES - Historical Price Data
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_MARKETDATA_TIMESERIES AS
WITH business_dates AS (
    SELECT DATEADD(day, seq4(), DATEADD(year, -5, CURRENT_DATE())) as price_date
    FROM TABLE(GENERATOR(rowcount => 1825))
    WHERE DAYOFWEEK(price_date) BETWEEN 1 AND 5
),
portfolio_securities AS (
    SELECT DISTINCT 
        s.SecurityID,
        s.AssetClass
    FROM SAM_DEMO.CURATED.DIM_SECURITY s
    WHERE EXISTS (
        SELECT 1 FROM SAM_DEMO.CURATED.FACT_TRANSACTION t 
        WHERE t.SecurityID = s.SecurityID
    )
),
securities_dates AS (
    SELECT 
        ps.SecurityID,
        ps.AssetClass,
        bd.price_date as PriceDate
    FROM portfolio_securities ps
    CROSS JOIN business_dates bd
)
SELECT 
    PriceDate,
    SecurityID,
    CASE 
        WHEN AssetClass = 'Equity' THEN UNIFORM(50, 850, RANDOM())
        WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(90, 110, RANDOM())
        ELSE UNIFORM(50, 450, RANDOM())
    END * (1 + (UNIFORM(-0.02, 0.02, RANDOM()))) as Price_Open,
    CASE 
        WHEN AssetClass = 'Equity' THEN UNIFORM(50, 850, RANDOM())
        WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(90, 110, RANDOM())
        ELSE UNIFORM(50, 450, RANDOM())
    END * (1 + UNIFORM(0, 0.03, RANDOM())) as Price_High,
    CASE 
        WHEN AssetClass = 'Equity' THEN UNIFORM(50, 850, RANDOM())
        WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(90, 110, RANDOM())
        ELSE UNIFORM(50, 450, RANDOM())
    END * (1 - UNIFORM(0, 0.03, RANDOM())) as Price_Low,
    CASE 
        WHEN AssetClass = 'Equity' THEN UNIFORM(50, 850, RANDOM())
        WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(90, 110, RANDOM())
        ELSE UNIFORM(50, 450, RANDOM())
    END as Price_Close,
    CASE 
        WHEN AssetClass = 'Equity' THEN UNIFORM(100000, 10000000, RANDOM())::int
        WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(10000, 1000000, RANDOM())::int
        ELSE UNIFORM(50000, 5000000, RANDOM())::int
    END as Volume,
    1.0 as TotalReturnFactor_Daily
FROM securities_dates;

-- ----------------------------------------------------------------------------
-- Step 5.2: FACT_ESG_SCORES - ESG Rating Data
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_ESG_SCORES AS
WITH equity_securities AS (
    SELECT 
        s.SecurityID,
        s.Ticker,
        i.SIC_DESCRIPTION,
        i.CountryOfIncorporation
    FROM SAM_DEMO.CURATED.DIM_SECURITY s
    JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
    WHERE s.AssetClass = 'Equity'
    AND EXISTS (
        SELECT 1 FROM SAM_DEMO.CURATED.FACT_TRANSACTION t 
        WHERE t.SecurityID = s.SecurityID
    )
),
scoring_dates AS (
    SELECT DATEADD(quarter, seq4(), DATEADD(year, -5, CURRENT_DATE())) as SCORE_DATE
    FROM TABLE(GENERATOR(rowcount => 20))
),
base_scores AS (
    SELECT 
        es.SecurityID,
        sd.SCORE_DATE,
        CASE 
            WHEN es.SIC_DESCRIPTION LIKE '%Utilities%' THEN UNIFORM(20, 60, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Energy%' THEN UNIFORM(15, 50, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Technology%' THEN UNIFORM(60, 95, RANDOM())
            ELSE UNIFORM(40, 80, RANDOM())
        END as E_SCORE,
        CASE 
            WHEN es.CountryOfIncorporation IN ('US', 'CA') THEN UNIFORM(50, 85, RANDOM())
            WHEN es.CountryOfIncorporation IN ('DE', 'FR', 'SE', 'DK') THEN UNIFORM(60, 90, RANDOM())
            ELSE UNIFORM(45, 75, RANDOM())
        END as S_SCORE,
        CASE 
            WHEN es.CountryOfIncorporation IN ('US', 'CA', 'GB', 'DE', 'FR', 'SE', 'DK') THEN UNIFORM(65, 95, RANDOM())
            ELSE UNIFORM(40, 70, RANDOM())
        END as G_SCORE
    FROM equity_securities es
    CROSS JOIN scoring_dates sd
)
SELECT 
    SecurityID,
    SCORE_DATE,
    'Environmental' as SCORE_TYPE,
    E_SCORE as SCORE_VALUE,
    CASE 
        WHEN E_SCORE >= 80 THEN 'A'
        WHEN E_SCORE >= 60 THEN 'B' 
        WHEN E_SCORE >= 40 THEN 'C'
        ELSE 'D'
    END as SCORE_GRADE,
    'MSCI' as PROVIDER
FROM base_scores
UNION ALL
SELECT SecurityID, SCORE_DATE, 'Social', S_SCORE, 
       CASE WHEN S_SCORE >= 80 THEN 'A' WHEN S_SCORE >= 60 THEN 'B' WHEN S_SCORE >= 40 THEN 'C' ELSE 'D' END,
       'MSCI' FROM base_scores
UNION ALL  
SELECT SecurityID, SCORE_DATE, 'Governance', G_SCORE,
       CASE WHEN G_SCORE >= 80 THEN 'A' WHEN G_SCORE >= 60 THEN 'B' WHEN G_SCORE >= 40 THEN 'C' ELSE 'D' END,
       'MSCI' FROM base_scores
UNION ALL
SELECT SecurityID, SCORE_DATE, 'Overall ESG', (E_SCORE + S_SCORE + G_SCORE) / 3,
       CASE WHEN (E_SCORE + S_SCORE + G_SCORE) / 3 >= 80 THEN 'A' 
            WHEN (E_SCORE + S_SCORE + G_SCORE) / 3 >= 60 THEN 'B' 
            WHEN (E_SCORE + S_SCORE + G_SCORE) / 3 >= 40 THEN 'C' 
            ELSE 'D' END,
       'MSCI' FROM base_scores;

-- ----------------------------------------------------------------------------
-- Step 5.3: FACT_FACTOR_EXPOSURES - Factor Loading Data
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_FACTOR_EXPOSURES AS
WITH equity_securities AS (
    SELECT 
        s.SecurityID,
        s.Ticker,
        i.SIC_DESCRIPTION,
        i.CountryOfIncorporation
    FROM SAM_DEMO.CURATED.DIM_SECURITY s
    JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
    WHERE s.AssetClass = 'Equity'
    AND EXISTS (
        SELECT 1 FROM SAM_DEMO.CURATED.FACT_TRANSACTION t 
        WHERE t.SecurityID = s.SecurityID
    )
),
monthly_dates AS (
    SELECT DATEADD(month, seq4(), DATEADD(year, -5, CURRENT_DATE())) as EXPOSURE_DATE
    FROM TABLE(GENERATOR(rowcount => 60))
),
base_exposures AS (
    SELECT 
        es.SecurityID,
        md.EXPOSURE_DATE,
        CASE 
            WHEN es.SIC_DESCRIPTION LIKE '%Utilities%' THEN UNIFORM(0.4, 0.8, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Technology%' THEN UNIFORM(0.9, 1.4, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Health%' THEN UNIFORM(0.6, 1.1, RANDOM())
            ELSE UNIFORM(0.7, 1.2, RANDOM())
        END as MARKET_BETA,
        UNIFORM(-0.5, 0.8, RANDOM()) as SIZE_FACTOR,
        CASE 
            WHEN es.SIC_DESCRIPTION LIKE '%Technology%' THEN UNIFORM(-0.3, 0.2, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Energy%' THEN UNIFORM(0.1, 0.6, RANDOM())
            ELSE UNIFORM(-0.2, 0.4, RANDOM())
        END as VALUE_FACTOR,
        UNIFORM(-0.4, 0.4, RANDOM()) as MOMENTUM_FACTOR,
        CASE 
            WHEN es.SIC_DESCRIPTION LIKE '%Technology%' THEN UNIFORM(0.3, 0.8, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Health%' THEN UNIFORM(0.1, 0.6, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Energy%' THEN UNIFORM(-0.4, 0.1, RANDOM())
            ELSE UNIFORM(-0.3, 0.4, RANDOM())
        END as GROWTH_FACTOR,
        CASE 
            WHEN es.SIC_DESCRIPTION LIKE '%Technology%' THEN UNIFORM(0.2, 0.7, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Health%' THEN UNIFORM(0.1, 0.5, RANDOM())
            ELSE UNIFORM(-0.2, 0.3, RANDOM())
        END as QUALITY_FACTOR,
        CASE 
            WHEN es.SIC_DESCRIPTION LIKE '%Utilities%' THEN UNIFORM(-0.3, 0.1, RANDOM())
            WHEN es.SIC_DESCRIPTION LIKE '%Technology%' THEN UNIFORM(-0.1, 0.4, RANDOM())
            ELSE UNIFORM(-0.2, 0.2, RANDOM())
        END as VOLATILITY_FACTOR
    FROM equity_securities es
    CROSS JOIN monthly_dates md
)
SELECT SecurityID, EXPOSURE_DATE, 'Market' as FACTOR_NAME, MARKET_BETA as EXPOSURE_VALUE, 0.95 as R_SQUARED FROM base_exposures
UNION ALL
SELECT SecurityID, EXPOSURE_DATE, 'Size', SIZE_FACTOR, 0.75 FROM base_exposures
UNION ALL
SELECT SecurityID, EXPOSURE_DATE, 'Value', VALUE_FACTOR, 0.65 FROM base_exposures
UNION ALL
SELECT SecurityID, EXPOSURE_DATE, 'Growth', GROWTH_FACTOR, 0.60 FROM base_exposures
UNION ALL
SELECT SecurityID, EXPOSURE_DATE, 'Momentum', MOMENTUM_FACTOR, 0.45 FROM base_exposures
UNION ALL
SELECT SecurityID, EXPOSURE_DATE, 'Quality', QUALITY_FACTOR, 0.55 FROM base_exposures
UNION ALL
SELECT SecurityID, EXPOSURE_DATE, 'Volatility', VOLATILITY_FACTOR, 0.35 FROM base_exposures;

-- ============================================================================
-- SECTION 6: SEC FILINGS DATA
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Step 6.1: FACT_SEC_FILINGS - Real SEC Filing Data
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_SEC_FILINGS (
    FilingID BIGINT IDENTITY(1,1) PRIMARY KEY,
    SecurityID BIGINT NOT NULL,
    IssuerID BIGINT NOT NULL,
    CIK VARCHAR(20) NOT NULL,
    CompanyName VARCHAR(255),
    FiscalYear INTEGER NOT NULL,
    FiscalPeriod VARCHAR(10) NOT NULL,
    FormType VARCHAR(10) NOT NULL,
    FilingDate DATE NOT NULL,
    PeriodStartDate DATE,
    PeriodEndDate DATE,
    ReportingDate DATE NOT NULL,
    TAG VARCHAR(200) NOT NULL,
    MeasureDescription VARCHAR(500),
    MeasureValue DECIMAL(38, 2),
    UnitOfMeasure VARCHAR(50),
    Statement VARCHAR(100),
    DataSource VARCHAR(50) DEFAULT 'SEC_FILINGS_CYBERSYN',
    LoadTimestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Load real SEC filing data
INSERT INTO SAM_DEMO.CURATED.FACT_SEC_FILINGS 
SELECT 
    ROW_NUMBER() OVER (ORDER BY i.IssuerID, sri.FISCAL_YEAR, sri.FISCAL_PERIOD, sra.TAG) as FilingID,
    s.SecurityID,
    i.IssuerID,
    sra.CIK,
    i.LegalName as CompanyName,
    sri.FISCAL_YEAR as FiscalYear,
    sri.FISCAL_PERIOD as FiscalPeriod,
    sri.FORM_TYPE as FormType,
    sri.FILED_DATE as FilingDate,
    sra.PERIOD_START_DATE as PeriodStartDate,
    sra.PERIOD_END_DATE as PeriodEndDate,
    sri.FILED_DATE as ReportingDate,
    sra.TAG,
    sra.MEASURE_DESCRIPTION as MeasureDescription,
    sra.VALUE as MeasureValue,
    sra.UNIT as UnitOfMeasure,
    sra.STATEMENT,
    'SEC_FILINGS_CYBERSYN' as DataSource,
    CURRENT_TIMESTAMP() as LoadTimestamp
FROM SAM_DEMO.CURATED.DIM_ISSUER i
JOIN SAM_DEMO.CURATED.DIM_SECURITY s 
    ON s.IssuerID = i.IssuerID 
    AND s.Ticker = i.PrimaryTicker
JOIN MARKETPLACE_CYBERSYN.PUBLIC_DATA_FREE.SEC_CORPORATE_REPORT_ATTRIBUTES sra ON i.CIK = sra.CIK
JOIN MARKETPLACE_CYBERSYN.PUBLIC_DATA_FREE.SEC_CORPORATE_REPORT_INDEX sri ON sra.ADSH = sri.ADSH AND sra.CIK = sri.CIK
WHERE s.AssetClass = 'Equity'
    AND sri.FISCAL_YEAR >= YEAR(CURRENT_DATE) - 5
    AND sri.FORM_TYPE IN ('10-K', '10-Q')
    AND sra.TAG IN (
        'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
        'NetIncomeLoss', 'GrossProfit', 'OperatingIncomeLoss',
        'InterestExpense', 'GeneralAndAdministrativeExpense', 'OperatingExpenses',
        'EarningsPerShareBasic', 'EarningsPerShareDiluted',
        'Assets', 'AssetsCurrent', 'StockholdersEquity', 
        'Liabilities', 'LiabilitiesCurrent', 'Goodwill',
        'CashAndCashEquivalentsAtCarryingValue', 'AccountsPayableCurrent',
        'RetainedEarningsAccumulatedDeficit',
        'NetCashProvidedByUsedInOperatingActivities',
        'NetCashProvidedByUsedInInvestingActivities', 
        'NetCashProvidedByUsedInFinancingActivities',
        'DepreciationDepletionAndAmortization', 'ShareBasedCompensation'
    )
    AND sra.VALUE IS NOT NULL;

-- ============================================================================
-- SECTION 7: SUPPLY CHAIN RELATIONSHIPS
-- ============================================================================

CREATE OR REPLACE TABLE SAM_DEMO.CURATED.DIM_SUPPLY_CHAIN_RELATIONSHIPS (
    RelationshipID BIGINT IDENTITY(1,1) PRIMARY KEY,
    Company_IssuerID NUMBER NOT NULL,
    Counterparty_IssuerID NUMBER NOT NULL,
    RelationshipType VARCHAR(50),
    CostShare DECIMAL(7,4),
    RevenueShare DECIMAL(7,4),
    CriticalityTier VARCHAR(20),
    SourceConfidence DECIMAL(5,2),
    StartDate DATE,
    EndDate DATE,
    Notes VARCHAR(500)
);

-- Insert demo supply chain relationships (Taiwan semiconductor -> US tech -> automotive)
-- This creates the second-order risk analysis scenario
INSERT INTO SAM_DEMO.CURATED.DIM_SUPPLY_CHAIN_RELATIONSHIPS 
(Company_IssuerID, Counterparty_IssuerID, RelationshipType, CostShare, RevenueShare, CriticalityTier, SourceConfidence, StartDate, Notes)
SELECT 
    i1.IssuerID as Company_IssuerID,
    i2.IssuerID as Counterparty_IssuerID,
    'Supplier' as RelationshipType,
    UNIFORM(0.05, 0.25, RANDOM()) as CostShare,
    NULL as RevenueShare,
    CASE WHEN UNIFORM(0, 1, RANDOM()) > 0.7 THEN 'Critical' ELSE 'High' END as CriticalityTier,
    UNIFORM(75, 95, RANDOM()) as SourceConfidence,
    '2020-01-01' as StartDate,
    'Demo semiconductor supply chain relationship' as Notes
FROM SAM_DEMO.CURATED.DIM_ISSUER i1
JOIN SAM_DEMO.CURATED.DIM_ISSUER i2 ON i1.IssuerID != i2.IssuerID
WHERE i1.SIC_DESCRIPTION LIKE '%Semiconductor%'
    AND i2.SIC_DESCRIPTION LIKE '%Technology%'
LIMIT 50;

-- ============================================================================
-- SECTION 8: MIDDLE OFFICE FACT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Step 8.1: FACT_TRADE_SETTLEMENT
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_TRADE_SETTLEMENT AS
WITH trade_data AS (
    SELECT 
        t.TransactionID,
        t.TransactionDate,
        DATEADD(day, 2, t.TransactionDate) as SettlementDate,
        t.PortfolioID,
        t.SecurityID,
        ABS(t.GrossAmount_Local) as SettlementValue,
        t.Currency,
        MOD(ABS(HASH(t.TransactionID)), 20) + 1 as CounterpartyID,
        MOD(ABS(HASH(t.TransactionID * 2)), 8) + 1 as CustodianID,
        UNIFORM(0, 100, RANDOM()) as failure_chance
    FROM SAM_DEMO.CURATED.FACT_TRANSACTION t
    WHERE t.TransactionType IN ('BUY', 'SELL')
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY TransactionID) as SettlementID,
    TransactionID as TradeID,
    TransactionDate as TradeDate,
    SettlementDate,
    CASE 
        WHEN failure_chance <= 3 THEN 'Failed'
        WHEN failure_chance <= 5 THEN 'Pending'
        ELSE 'Settled'
    END as Status,
    PortfolioID,
    SecurityID,
    CounterpartyID,
    CustodianID,
    SettlementValue,
    Currency,
    CASE 
        WHEN failure_chance <= 1 THEN 'SSI mismatch'
        WHEN failure_chance <= 2 THEN 'Insufficient shares'
        WHEN failure_chance <= 3 THEN 'Counterparty system issue'
        ELSE NULL
    END as FailureReason,
    CASE 
        WHEN failure_chance <= 3 THEN DATEADD(day, UNIFORM(1, 3, RANDOM()), SettlementDate)
        ELSE NULL
    END as ResolvedDate
FROM trade_data;

-- ----------------------------------------------------------------------------
-- Step 8.2: FACT_RECONCILIATION
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_RECONCILIATION AS
WITH position_data AS (
    SELECT 
        p.HoldingDate,
        p.PortfolioID,
        p.SecurityID,
        p.MarketValue_Base,
        p.Quantity,
        UNIFORM(0, 100, RANDOM()) as break_chance,
        UNIFORM(0, 3, RANDOM()) as break_type_flag
    FROM SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR p
),
breaks AS (
    SELECT 
        HoldingDate as ReconciliationDate,
        PortfolioID,
        SecurityID,
        CASE 
            WHEN break_type_flag < 1 THEN 'Position'
            WHEN break_type_flag < 2 THEN 'Cash'
            ELSE 'Price'
        END as BreakType,
        MarketValue_Base as InternalValue,
        MarketValue_Base * (1 + UNIFORM(-0.05, 0.05, RANDOM())) as CustodianValue,
        break_chance
    FROM position_data
    WHERE break_chance <= 2
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY ReconciliationDate, PortfolioID, SecurityID) as ReconciliationID,
    ReconciliationDate,
    PortfolioID,
    SecurityID,
    BreakType,
    InternalValue,
    CustodianValue,
    ABS(InternalValue - CustodianValue) as Difference,
    CASE 
        WHEN break_chance <= 0.5 THEN 'Open'
        WHEN break_chance <= 1.5 THEN 'Investigating'
        ELSE 'Resolved'
    END as Status,
    CASE 
        WHEN break_chance > 0.5 THEN DATEADD(day, UNIFORM(1, 5, RANDOM()), ReconciliationDate)
        ELSE NULL
    END as ResolutionDate,
    CASE 
        WHEN break_chance > 1.5 THEN 'Timing difference - resolved through custodian confirmation'
        WHEN break_chance > 0.5 THEN 'Under investigation - awaiting custodian response'
        ELSE NULL
    END as ResolutionNotes
FROM breaks;

-- ----------------------------------------------------------------------------
-- Step 8.3: FACT_NAV_CALCULATION
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_NAV_CALCULATION AS
WITH daily_positions AS (
    SELECT 
        HoldingDate,
        PortfolioID,
        SUM(MarketValue_Base) as TotalAssets
    FROM SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR
    GROUP BY HoldingDate, PortfolioID
),
nav_calc AS (
    SELECT 
        HoldingDate as CalculationDate,
        PortfolioID,
        TotalAssets,
        TotalAssets / 1000000 as NAVPerShare,
        UNIFORM(0, 100, RANDOM()) as anomaly_chance
    FROM daily_positions
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY CalculationDate, PortfolioID) as NAVID,
    CalculationDate,
    PortfolioID,
    TotalAssets,
    NAVPerShare,
    CASE 
        WHEN anomaly_chance <= 1 THEN 'Anomaly Detected'
        WHEN anomaly_chance <= 3 THEN 'Pending Review'
        ELSE 'Approved'
    END as CalculationStatus,
    CASE 
        WHEN anomaly_chance <= 1 THEN 'Unusual NAV movement detected - requires investigation'
        ELSE NULL
    END as AnomaliesDetected
FROM nav_calc;

-- ============================================================================
-- SECTION 9: COMPLIANCE AND MANDATE TABLES
-- ============================================================================

CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_COMPLIANCE_ALERTS (
    AlertID BIGINT IDENTITY(1,1) PRIMARY KEY,
    AlertDate DATE NOT NULL,
    PortfolioID BIGINT NOT NULL,
    SecurityID BIGINT NOT NULL,
    AlertType VARCHAR(50) NOT NULL,
    AlertSeverity VARCHAR(20) NOT NULL,
    OriginalValue VARCHAR(50),
    CurrentValue VARCHAR(50),
    RequiresAction BOOLEAN NOT NULL,
    ActionDeadline DATE,
    AlertDescription TEXT,
    ResolvedDate DATE,
    ResolvedBy VARCHAR(100),
    ResolutionNotes TEXT
);

CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_PRE_SCREENED_REPLACEMENTS (
    ReplacementID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PortfolioID BIGINT NOT NULL,
    SecurityID BIGINT NOT NULL,
    ScreenDate DATE NOT NULL,
    IsEligible BOOLEAN NOT NULL,
    ReplacementRank INTEGER,
    ESG_Grade VARCHAR(10),
    AI_Growth_Score DECIMAL(18,4),
    MarketCap_B_USD DECIMAL(18,4),
    LiquidityScore INTEGER,
    EligibilityReason TEXT,
    ScreeningCriteria TEXT,
    LastUpdated TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- SECTION 10: DOCUMENT CORPUS TABLES (For Cortex Search)
-- ============================================================================

-- Create RAW document tables for each document type
CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_BROKER_RESEARCH (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    SECURITY_ID BIGINT,
    ISSUER_ID BIGINT,
    TICKER VARCHAR(20),
    COMPANY_NAME VARCHAR(255),
    SECTOR VARCHAR(100),
    PUBLISH_DATE DATE,
    ANALYST_NAME VARCHAR(100),
    BROKER_FIRM VARCHAR(100),
    RATING VARCHAR(20),
    PRICE_TARGET DECIMAL(18,2),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_EARNINGS_TRANSCRIPTS (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    SECURITY_ID BIGINT,
    ISSUER_ID BIGINT,
    TICKER VARCHAR(20),
    COMPANY_NAME VARCHAR(255),
    FISCAL_QUARTER VARCHAR(10),
    FISCAL_YEAR INTEGER,
    CALL_DATE DATE,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_PRESS_RELEASES (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    SECURITY_ID BIGINT,
    ISSUER_ID BIGINT,
    TICKER VARCHAR(20),
    COMPANY_NAME VARCHAR(255),
    RELEASE_DATE DATE,
    RELEASE_TYPE VARCHAR(50),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_MACRO_EVENTS (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    EVENT_TYPE VARCHAR(100),
    EVENT_DATE DATE,
    REGION VARCHAR(100),
    SEVERITY VARCHAR(20),
    AFFECTED_SECTORS TEXT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_POLICY_DOCS (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    POLICY_TYPE VARCHAR(100),
    EFFECTIVE_DATE DATE,
    VERSION VARCHAR(20),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_NGO_REPORTS (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    ISSUER_ID BIGINT,
    COMPANY_NAME VARCHAR(255),
    NGO_NAME VARCHAR(100),
    REPORT_DATE DATE,
    CONTROVERSY_TYPE VARCHAR(100),
    SEVERITY VARCHAR(20),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_ENGAGEMENT_NOTES (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    ISSUER_ID BIGINT,
    COMPANY_NAME VARCHAR(255),
    MEETING_DATE DATE,
    MEETING_TYPE VARCHAR(50),
    ATTENDEES TEXT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_SALES_TEMPLATES (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    TEMPLATE_TYPE VARCHAR(100),
    VERSION VARCHAR(20),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_PHILOSOPHY_DOCS (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    PHILOSOPHY_TYPE VARCHAR(100),
    VERSION VARCHAR(20),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_REPORT_TEMPLATES (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    TEMPLATE_TYPE VARCHAR(100),
    VERSION VARCHAR(20),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Middle Office document tables
CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_CUSTODIAN_REPORTS (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    CUSTODIAN_NAME VARCHAR(100),
    REPORT_DATE DATE,
    REPORT_TYPE VARCHAR(50),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_RECONCILIATION_NOTES (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    PORTFOLIO_NAME VARCHAR(255),
    RECON_DATE DATE,
    BREAK_TYPE VARCHAR(50),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_SSI_DOCUMENTS (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    COUNTERPARTY_NAME VARCHAR(100),
    ASSET_CLASS VARCHAR(50),
    CURRENCY VARCHAR(10),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SAM_DEMO.RAW.RAW_OPS_PROCEDURES (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    CONTENT TEXT,
    PROCEDURE_TYPE VARCHAR(100),
    VERSION VARCHAR(20),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- SECTION 11: PYTHON STORED PROCEDURE FOR DOCUMENT GENERATION
-- ============================================================================

-- This procedure generates rich, realistic documents using embedded templates
-- from the content_library with proper placeholder hydration
CREATE OR REPLACE PROCEDURE SAM_DEMO.AI.GENERATE_SAMPLE_DOCUMENTS()
RETURNS VARCHAR(16777216)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'generate_documents'
EXECUTE AS CALLER
AS $$
import random
from datetime import datetime, timedelta
from snowflake.snowpark import Session

# =============================================================================
# FICTIONAL PROVIDERS (from content_library/_rules/fictional_providers.yaml)
# =============================================================================
FICTIONAL_BROKERS = [
    'Ashfield Partners', 'Northgate Analytics', 'Blackstone Ridge Research',
    'Fairmont Capital Insights', 'Kingswell Securities Research', 'Brookline Advisory Group',
    'Harrow Street Markets', 'Marlowe & Co. Research', 'Crescent Point Analytics',
    'Sterling Wharf Intelligence', 'Granite Peak Advisory', 'Alder & Finch Investments',
    'Bluehaven Capital Research', 'Regent Square Analytics', 'Whitestone Equity Research'
]

FICTIONAL_NGOS = {
    'environmental': ['Global Sustainability Watch', 'Environmental Justice Initiative', 'Climate Action Network', 'Green Future Alliance'],
    'social': ['Human Rights Monitor', 'Labour Rights Observatory', 'Ethical Investment Coalition', 'Fair Workplace Institute'],
    'governance': ['Corporate Accountability Forum', 'Transparency Advocacy Group', 'Corporate Responsibility Institute', 'Ethical Governance Council']
}

RATINGS = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
RATING_WEIGHTS = [0.10, 0.25, 0.45, 0.15, 0.05]

# =============================================================================
# NUMERIC BOUNDS (from content_library/_rules/numeric_bounds.yaml)
# =============================================================================
SECTOR_BOUNDS = {
    'Information Technology': {'revenue_growth': (8, 25), 'ebit_margin': (12, 28), 'pe_ratio': (15, 35), 'price_target': (80, 450)},
    'Health Care': {'revenue_growth': (5, 18), 'ebit_margin': (15, 35), 'pe_ratio': (18, 40), 'price_target': (60, 350)},
    'Financials': {'revenue_growth': (3, 15), 'ebit_margin': (20, 40), 'pe_ratio': (8, 18), 'price_target': (50, 300)},
    'Consumer Discretionary': {'revenue_growth': (4, 20), 'ebit_margin': (8, 18), 'pe_ratio': (12, 30), 'price_target': (40, 400)},
    'Industrials': {'revenue_growth': (3, 15), 'ebit_margin': (8, 18), 'pe_ratio': (12, 25), 'price_target': (50, 280)},
    'default': {'revenue_growth': (3, 15), 'ebit_margin': (10, 25), 'pe_ratio': (12, 25), 'price_target': (50, 300)}
}

def get_bounds(sector, metric):
    bounds = SECTOR_BOUNDS.get(sector, SECTOR_BOUNDS['default'])
    return bounds.get(metric, (10, 50))

def sample_value(bounds):
    return round(random.uniform(bounds[0], bounds[1]), 1)

# =============================================================================
# RICH BROKER RESEARCH TEMPLATE
# =============================================================================
BROKER_RESEARCH_TEMPLATE = '''# {COMPANY_NAME} ({TICKER}) — {RATING} — ${PRICE_TARGET} Target

**{BROKER_NAME}** | Analyst: {ANALYST_NAME} | {PUBLISH_DATE}

## Executive Summary

We initiate coverage on {COMPANY_NAME} with a **{RATING}** rating and 12-month price target of ${PRICE_TARGET}. As a leading player in the {SECTOR} sector, the company demonstrates robust fundamentals with revenue growth of {REVENUE_GROWTH}% year-over-year and strong EBIT margins of {EBIT_MARGIN}%. Our positive view is supported by the company''s competitive positioning, technology innovation pipeline, and sustained market share gains in key growth segments.

## Investment Highlights

**Strong Market Position**: {COMPANY_NAME} maintains a leadership position in the {SECTOR} industry, benefiting from significant scale advantages and an established customer base. The company''s comprehensive product portfolio and brand strength provide meaningful competitive moats that support pricing power and customer retention.

**Growth Drivers**: We identify three primary catalysts for continued revenue expansion. First, ongoing digital transformation initiatives across enterprise customers are driving sustained demand for the company''s core offerings. Second, emerging opportunities in cloud computing and artificial intelligence are creating new revenue streams with attractive margins. Third, international market expansion, particularly in high-growth Asia-Pacific regions, represents a significant untapped opportunity.

**Financial Strength**: The company''s balance sheet remains robust with modest leverage and strong cash flow generation. EBIT margins of {EBIT_MARGIN}% reflect operational excellence and disciplined cost management. We expect continued margin expansion as the company realises economies of scale and shifts mix toward higher-margin software and services revenue.

## Key Risks

**Competitive Intensity**: The {SECTOR} sector remains highly competitive with rapid technological change and evolving customer preferences. New entrants and established competitors continue to invest aggressively in product development and market share acquisition, which could pressure pricing and margins.

**Execution Risk**: The company''s growth strategy requires successful new product launches and effective go-to-market execution. Any delays in product development cycles or market adoption could negatively impact our revenue and earnings forecasts.

**Regulatory Headwinds**: Increasing regulatory scrutiny around data privacy, cybersecurity, and antitrust matters presents potential challenges. While the company has invested substantially in compliance infrastructure, regulatory developments remain a key risk to monitor.

## Valuation and Price Target

Our ${PRICE_TARGET} price target is derived from a discounted cash flow analysis assuming a weighted average cost of capital of 8.5% and terminal growth rate of 3.5%. This valuation implies a forward P/E ratio of approximately {PE_RATIO}x, representing a modest premium to sector peers but justified by the company''s superior growth profile and market position.

On a relative valuation basis, {COMPANY_NAME} trades at {PE_RATIO}x forward earnings, compared to the {SECTOR} sector median of 22x. We believe this valuation appropriately reflects the company''s quality and growth characteristics.

## Recommendation

We rate {COMPANY_NAME} as **{RATING}** based on the company''s strong competitive position, solid execution track record, and favourable industry tailwinds. The combination of consistent revenue growth, margin expansion potential, and disciplined capital allocation supports our constructive investment view. We recommend accumulating positions on any near-term weakness and view the current entry point as attractive for long-term investors seeking quality exposure to the {SECTOR} sector.

---

**Important Disclosures**: This research report is provided for informational purposes only and does not constitute investment advice. {BROKER_NAME} may have a business relationship with companies mentioned in this report. Past performance is not indicative of future results.

*Snowcrest Asset Management demonstration purposes only. {BROKER_NAME} is a fictional entity.*
'''

# =============================================================================
# RICH EARNINGS TRANSCRIPT TEMPLATE
# =============================================================================
EARNINGS_TRANSCRIPT_TEMPLATE = '''# {COMPANY_NAME} {FISCAL_QUARTER} {FISCAL_YEAR} Earnings Call Transcript

**Date**: {PUBLISH_DATE}  
**Participants**: {CEO_NAME} (CEO), {CFO_NAME} (CFO), Investor Relations Team

---

## Operator

Good afternoon, and welcome to {COMPANY_NAME}''s {FISCAL_QUARTER} {FISCAL_YEAR} earnings conference call. Today''s call is being recorded. At this time, all participants are in a listen-only mode. Following management''s prepared remarks, we will conduct a question-and-answer session.

I would now like to turn the call over to Sarah Thompson, Vice President of Investor Relations. Please go ahead.

## Sarah Thompson, VP Investor Relations

Thank you, operator, and good afternoon, everyone. Welcome to {COMPANY_NAME}''s {FISCAL_QUARTER} {FISCAL_YEAR} earnings call. Joining me today are {CEO_NAME}, our Chief Executive Officer, and {CFO_NAME}, our Chief Financial Officer.

Before we begin, I''d like to remind you that this call will contain forward-looking statements regarding our business outlook, future financial and operating results, and overall business environment. These statements are subject to risks and uncertainties that could cause actual results to differ materially from our current expectations.

With that, I''ll turn the call over to {CEO_NAME}.

## {CEO_NAME}, Chief Executive Officer — Prepared Remarks

Thank you, Sarah, and thank you all for joining us today. I''m pleased to report another strong quarter for {COMPANY_NAME}, with results that demonstrate the strength of our technology platform, the quality of our execution, and the significant opportunities ahead of us.

Let me start with our {FISCAL_QUARTER} financial highlights. Revenue reached ${QUARTERLY_REVENUE} billion, representing {YOY_GROWTH}% growth year-over-year. Earnings per share came in at ${QUARTERLY_EPS}, exceeding consensus expectations. These results reflect strong performance across all business segments and continued momentum in our strategic growth initiatives.

Our cloud computing platform continues to be the primary driver of our growth story. Cloud revenue grew significantly this quarter, with increasing adoption from both new customers and expansion within our existing installed base. We''re seeing particularly strong traction in enterprise accounts, where customers are consolidating workloads onto our platform for its security, reliability, and comprehensive capabilities.

Artificial intelligence and machine learning capabilities are becoming increasingly central to our customer value proposition. The AI features we''ve integrated across our product portfolio are driving higher engagement, improved customer outcomes, and expanded use cases. Customer feedback on our AI-powered tools has been exceptionally positive, and we''re investing aggressively to maintain our leadership position in this critical area.

## {CFO_NAME}, Chief Financial Officer — Financial Review

Thank you, {CEO_NAME}, and good afternoon, everyone. I''ll provide more detail on our {FISCAL_QUARTER} financial results.

Total revenue for the quarter was ${QUARTERLY_REVENUE} billion, up {YOY_GROWTH}% year-over-year and ahead of our guidance range. This strong performance was driven by cloud platform revenue growth, software subscription revenue growth, and services revenue growth.

From a profitability perspective, gross profit margin was {GROSS_MARGIN}%, consistent with our expectations and slightly ahead of the prior year period. Operating margin came in at {OPERATING_MARGIN}%, demonstrating our ability to balance growth investments with profitability.

Looking at the balance sheet and cash flow, we ended the quarter with strong cash and marketable securities. Our strong cash generation supports both organic growth investments and capital return to shareholders.

## Question and Answer Session

**Operator**: Thank you. We''ll now begin the question-and-answer session. Our first question comes from Michael Chen with Northgate Analytics.

**Michael Chen, Northgate Analytics**: Good afternoon, and congratulations on the strong results. My question is on the cloud platform segment. Can you provide more colour on what''s driving the acceleration we''re seeing?

**{CEO_NAME}**: Thanks, Michael. Great question. The cloud acceleration is really being driven by both new customer acquisition and existing customer expansion. Companies are consolidating workloads from multiple cloud providers onto our platform because of the comprehensive capabilities, security features, and cost efficiency we provide.

**Operator**: Our next question comes from Jennifer Martinez with Fairmont Capital Insights.

**Jennifer Martinez, Fairmont Capital Insights**: Hi, thank you. I wanted to ask about the AI initiatives you mentioned. Can you quantify how much AI is contributing to growth?

**{CEO_NAME}**: Jennifer, AI is becoming embedded across essentially everything we do. What I can tell you is that products with AI features have significantly higher adoption rates and customer engagement metrics. We''re seeing strong enterprise customer adoption of our AI-powered tools.

**{CFO_NAME}**: To add to that, whilst we don''t break out AI revenue separately, products launched in the past 18 months with significant AI components are growing revenue at roughly 2x the rate of our legacy products.

## {CEO_NAME} — Closing Remarks

Before we close, I want to reiterate a few key points. First, {COMPANY_NAME} delivered another quarter of strong financial performance and strategic progress. Second, the long-term growth opportunities in front of us are substantial and expanding. Third, we have the right strategy, team, and financial resources to capitalize on these opportunities whilst delivering value to shareholders.

Thank you all for your time today and your continued interest in {COMPANY_NAME}. We look forward to updating you on our progress next quarter.

**Operator**: This concludes today''s {COMPANY_NAME} {FISCAL_QUARTER} {FISCAL_YEAR} earnings conference call. Thank you for participating.

---

*SAM Demo Content. Company details and figures are illustrative for demonstration purposes.*
'''

# =============================================================================
# RICH CONCENTRATION RISK POLICY TEMPLATE
# =============================================================================
CONCENTRATION_POLICY_TEMPLATE = '''# Concentration Risk Management Policy

**Snowcrest Asset Management**  
**Policy Owner**: Chief Investment Officer  
**Version**: 2.1 | **Effective Date**: 1 January 2024  
**Review Cycle**: Annual | **Next Review**: January 2025

---

## 1. Policy Statement

Snowcrest Asset Management implements comprehensive concentration risk limits to protect client portfolios from excessive exposure to individual issuers, sectors, geographies, and asset classes. This policy establishes mandatory concentration thresholds that trigger monitoring, review, and remediation actions.

**Purpose**: Ensure prudent diversification, limit downside risk from single-name exposures, and maintain compliance with regulatory requirements and client mandates.

**Scope**: All discretionary investment portfolios managed by Snowcrest Asset Management.

---

## 2. Issuer Concentration Limits

### 2.1 Single Issuer Exposure Limits

**Hard Limit — Breach Level**:
- **Maximum 7.0%** of portfolio market value in any single issuer
- **Status**: Regulatory breach requiring immediate remediation
- **Action**: Mandatory reduction within 10 business days
- **Escalation**: Chief Investment Officer and Compliance Officer notification
- **Client Impact**: Written notification required, potential regulatory filing

**Early Warning Threshold**:
- **6.5%** of portfolio market value in any single issuer
- **Status**: Concentration warning — heightened monitoring required
- **Action**: Portfolio Manager review, consider rebalancing at next opportunity
- **Monitoring**: Daily position tracking, inclusion in concentration report
- **Rationale**: Provides buffer before breach, allows proactive management

**Normal Range**:
- **Below 6.5%** considered within acceptable concentration parameters
- **Best Practice**: Most positions maintained between 1-5% for optimal diversification
- **Monitoring**: Weekly portfolio composition review

### 2.2 Calculation Methodology

**Market Value Basis**:
- Concentration calculated as: (Position Market Value / Total Portfolio Market Value) × 100
- Uses most recent end-of-day market values
- Includes all securities issued by the same legal entity (consolidated issuer view)
- Parent-subsidiary consolidation required where material ownership exists

**Frequency**:
- Calculated daily after market close
- Alerts triggered automatically via portfolio management system
- Weekly concentration report distributed to Portfolio Managers and CIO
- Monthly Board reporting on all positions exceeding 5.0%

---

## 3. Sector Concentration Limits

### 3.1 GICS Sector Limits

**General Portfolios**:
- **Maximum 25%** in any single GICS Level 1 sector
- **Early Warning**: 22% sector concentration triggers review
- **Technology Exception**: Technology-focused mandates may exceed with documented approval

**Diversified/Balanced Portfolios**:
- **Maximum 20%** in any single GICS Level 1 sector
- **Stricter Standard**: Reflects commitment to broad diversification

---

## 4. Fixed Income Quality Standards

**Investment Grade Requirements**:
- **Minimum 75%** of fixed income allocation must be Investment Grade (BBB-/Baa3 or higher)
- **High Yield Limit**: Maximum 25% in sub-investment grade securities
- **CCC and Below**: Maximum 5% in securities rated CCC+ or lower
- **Defaulted Securities**: Not permitted without specific client approval

---

## 5. Monitoring and Compliance

### 5.1 Daily Monitoring Process

**Automated Alerts**:
- Real-time concentration monitoring via portfolio management system
- Email alerts to Portfolio Managers when positions exceed 6.0%
- Escalation alerts to CIO and Compliance when positions exceed 6.5%
- Automatic reporting in morning portfolio summary reports

**Concentration Dashboard**:
- Updated daily with current position sizes
- Historical trending of top 10 positions
- Colour-coded indicators: Green (<5%), Amber (5-6.5%), Red (>6.5%)
- Accessible to all Portfolio Managers and investment team

---

## 6. Breach Resolution Process

### 6.1 Immediate Actions (Breach >7.0%)

1. **Day 0**: Automated alert to Portfolio Manager, CIO, and Compliance
2. **Day 1**: Portfolio Manager provides written remediation plan
3. **Day 1-10**: Execute rebalancing trades to bring position below 7.0%
4. **Day 10**: Client notification if breach persists beyond 10 business days
5. **Day 15**: Regulatory filing if required and breach remains unresolved

### 6.2 Warning Threshold Management (6.5-7.0%)

1. **Notification**: Portfolio Manager notified of concentration warning
2. **Review**: Assessment of position outlook and portfolio impact
3. **Action Plan**: Document rationale to hold or plan to reduce
4. **Monitoring**: Enhanced daily tracking until resolved below 6.5%
5. **Opportunistic Reduction**: Reduce position at favourable market conditions

---

**Document Control**  
**Classification**: Internal Use — Investment Team  
**Distribution**: All Portfolio Managers, Investment Committee, Compliance  
**Approval**: Chief Investment Officer | Compliance Officer

*This policy represents Snowcrest Asset Management''s commitment to prudent concentration risk management.*
'''

# =============================================================================
# RICH TAIWAN EARTHQUAKE MACRO EVENT TEMPLATE
# =============================================================================
TAIWAN_EARTHQUAKE_TEMPLATE = '''# Major Earthquake Disrupts Taiwan Semiconductor Production

**Event Date**: {EVENT_DATE}  
**Region**: Taiwan (TW)  
**Event Type**: Natural Disaster  
**Severity**: Critical  
**Source**: Global Risk Monitor

## Executive Summary

A magnitude 7.2 earthquake struck central Taiwan, causing significant disruption to semiconductor manufacturing facilities across the island. The earthquake''s epicentre was located approximately 15 kilometres from major fabrication plants operated by Taiwan Semiconductor Manufacturing Company (TSMC) and other key players in the global semiconductor supply chain.

Initial assessments indicate production halts expected to last 2-4 weeks across affected facilities, with potential downstream supply chain impacts extending to global technology and automotive sectors. This event poses significant second-order risks to companies dependent on Taiwanese semiconductor production.

## Impact Assessment

### Direct Impact: Semiconductor Manufacturing

- **TSMC Facilities**: Multiple advanced fabrication plants (7nm, 5nm, and 3nm nodes) have initiated emergency shutdown procedures
- **Production Capacity**: Approximately 40-50% of global advanced semiconductor production capacity affected
- **Recovery Timeline**: Initial estimates suggest 2-4 weeks for full production resumption, pending structural assessments
- **Economic Impact**: Estimated production losses of $2-3 billion during shutdown period

### Affected Sectors

**Information Technology** (High Impact)
- Graphics processing units (GPUs) for AI and gaming applications
- Mobile phone processors and system-on-chip (SoC) components
- High-performance computing chips
- Data centre processors

**Consumer Discretionary** (Medium-High Impact)
- Automotive semiconductor components
- Consumer electronics chips
- Electric vehicle (EV) power management systems
- Advanced driver assistance systems (ADAS) chips

### Second-Order Dependencies

Industries and companies dependent on first-order suppliers:
- Automotive manufacturers requiring semiconductor components
- Consumer electronics brands
- Cloud computing service providers
- Telecommunications equipment suppliers

## Risk Implications

### Supply Chain Disruption Risk
- **Timeline**: 2-4 weeks production halt, with potential 6-8 weeks for full supply chain normalisation
- **Inventory**: Most technology companies maintain 4-8 weeks of semiconductor inventory
- **Critical Period**: Weeks 6-12 post-event represent highest supply constraint risk

### Financial Impact Estimates
- **Revenue Impact**: Potential $10-15 billion in delayed or lost revenue across technology sector
- **Margin Pressure**: Alternative sourcing at premium pricing could compress margins 2-3%
- **Capital Allocation**: Accelerated diversification investments into alternative semiconductor regions

## Recommended Actions

### Immediate Assessment (Days 1-7)
1. **Exposure Quantification**: Calculate direct and indirect exposure to affected facilities
2. **Inventory Analysis**: Assess current semiconductor inventory levels across portfolio companies
3. **Supply Chain Mapping**: Identify multi-hop dependencies through supply chain relationships
4. **Communication**: Engage with portfolio company management to understand specific impacts

### Short-Term Monitoring (Weeks 2-8)
1. **Production Updates**: Track facility restoration progress and revised production schedules
2. **Alternative Sourcing**: Monitor companies securing alternative semiconductor supply
3. **Financial Guidance**: Watch for earnings guidance revisions from affected companies
4. **Sector Rotation**: Consider tactical allocation adjustments based on differential impacts

---

**Document Classification**: Market Risk Alert  
**Distribution**: Portfolio Managers, Risk Committee, Investment Committee  
**Next Update**: 48 hours or upon material developments
'''

# =============================================================================
# NGO REPORT TEMPLATE
# =============================================================================
NGO_REPORT_TEMPLATE = '''# ESG Controversy Alert: {COMPANY_NAME}

**Report Date**: {PUBLISH_DATE}  
**Company**: {COMPANY_NAME} ({TICKER})  
**Severity Level**: {SEVERITY}  
**Category**: {CATEGORY}  
**Source**: {NGO_NAME}

---

## Summary

{NGO_NAME} has published a report highlighting {CATEGORY} concerns regarding {COMPANY_NAME}. This alert summarises the key findings and potential implications for investment portfolios holding this security.

## Key Findings

### Issue Description

The report identifies significant concerns in the company''s {CATEGORY} practices, including:

- Inadequate disclosure of environmental impact metrics
- Gaps in supply chain oversight and monitoring
- Insufficient stakeholder engagement processes
- Potential regulatory compliance concerns

### Evidence and Documentation

{NGO_NAME} has compiled evidence from:
- Public regulatory filings and disclosures
- Whistleblower testimonies and employee accounts
- Third-party audits and assessments
- Media investigations and journalistic sources

## ESG Impact Assessment

### Rating Implications

**Current ESG Rating Impact**:
- Potential downgrade risk if issues are not addressed
- Increased scrutiny from ESG rating agencies expected
- May affect inclusion in ESG-focused indices

### Portfolio Considerations

For ESG-mandated portfolios:
- Review holding against ESG policy requirements
- Assess engagement opportunities with company management
- Consider position sizing relative to controversy severity
- Document investment rationale if position maintained

## Recommended Actions

1. **Immediate Review**: Assess current portfolio exposure to {COMPANY_NAME}
2. **Engagement**: Consider direct engagement with company management
3. **Monitoring**: Track company response and remediation efforts
4. **Documentation**: Record investment committee discussion and decisions

---

**Classification**: ESG Risk Alert  
**Distribution**: ESG Committee, Portfolio Managers, Compliance
'''

# =============================================================================
# DOCUMENT GENERATION FUNCTION
# =============================================================================
def generate_documents(session):
    """Generate rich, realistic documents using embedded templates."""
    
    random.seed(42)  # Deterministic generation
    
    # Get sample securities for document generation
    securities = session.sql("""
        SELECT s.SecurityID, s.Ticker, s.Description as CompanyName, i.IssuerID, i.SIC_DESCRIPTION,
               CASE 
                   WHEN i.SIC_DESCRIPTION LIKE '%software%' OR i.SIC_DESCRIPTION LIKE '%computer%' OR i.SIC_DESCRIPTION LIKE '%semiconductor%' THEN 'Information Technology'
                   WHEN i.SIC_DESCRIPTION LIKE '%pharma%' OR i.SIC_DESCRIPTION LIKE '%medical%' OR i.SIC_DESCRIPTION LIKE '%health%' THEN 'Health Care'
                   WHEN i.SIC_DESCRIPTION LIKE '%bank%' OR i.SIC_DESCRIPTION LIKE '%insurance%' OR i.SIC_DESCRIPTION LIKE '%financ%' THEN 'Financials'
                   WHEN i.SIC_DESCRIPTION LIKE '%retail%' OR i.SIC_DESCRIPTION LIKE '%auto%' OR i.SIC_DESCRIPTION LIKE '%hotel%' THEN 'Consumer Discretionary'
                   ELSE 'Industrials'
               END as GICS_SECTOR
        FROM SAM_DEMO.CURATED.DIM_SECURITY s
        JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
        WHERE s.AssetClass = 'Equity'
        ORDER BY RANDOM()
        LIMIT 50
    """).collect()
    
    doc_count = 0
    today = datetime.now().strftime('%Y-%m-%d')
    
    # ==========================================================================
    # Generate BROKER RESEARCH documents (rich templates)
    # ==========================================================================
    for i, sec in enumerate(securities[:20]):
        sector = sec['GICS_SECTOR']
        bounds = SECTOR_BOUNDS.get(sector, SECTOR_BOUNDS['default'])
        
        rating = random.choices(RATINGS, weights=RATING_WEIGHTS)[0]
        broker = random.choice(FICTIONAL_BROKERS)
        analyst = f"Analyst_{random.randint(100, 999)}"
        
        content = BROKER_RESEARCH_TEMPLATE.format(
            COMPANY_NAME=sec['COMPANYNAME'],
            TICKER=sec['TICKER'],
            SECTOR=sector,
            RATING=rating,
            PRICE_TARGET=int(sample_value(bounds['price_target'])),
            BROKER_NAME=broker,
            ANALYST_NAME=analyst,
            PUBLISH_DATE=today,
            REVENUE_GROWTH=sample_value(bounds['revenue_growth']),
            EBIT_MARGIN=sample_value(bounds['ebit_margin']),
            PE_RATIO=sample_value(bounds['pe_ratio'])
        )
        
        doc_id = f"BR_{sec['TICKER']}_{i+1}"
        title = f"{sec['COMPANYNAME']} ({sec['TICKER']}) — {rating} — Equity Research"
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_BROKER_RESEARCH 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, SECURITY_ID, ISSUER_ID, TICKER, COMPANY_NAME, SECTOR, PUBLISH_DATE, ANALYST_NAME, BROKER_FIRM, RATING)
            VALUES ('{doc_id}', '{title.replace("'", "''")}', 'broker_research', '{content.replace("'", "''")}', 
                    {sec['SECURITYID']}, {sec['ISSUERID']}, '{sec['TICKER']}', '{sec['COMPANYNAME'].replace("'", "''")}',
                    '{sector.replace("'", "''")}', CURRENT_DATE(), '{analyst}', '{broker}', '{rating}')
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate EARNINGS TRANSCRIPTS (rich templates)
    # ==========================================================================
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    for i, sec in enumerate(securities[:15]):
        sector = sec['GICS_SECTOR']
        bounds = SECTOR_BOUNDS.get(sector, SECTOR_BOUNDS['default'])
        quarter = quarters[i % 4]
        
        content = EARNINGS_TRANSCRIPT_TEMPLATE.format(
            COMPANY_NAME=sec['COMPANYNAME'],
            TICKER=sec['TICKER'],
            FISCAL_QUARTER=quarter,
            FISCAL_YEAR='2024',
            PUBLISH_DATE=today,
            CEO_NAME=f"CEO_{sec['TICKER']}",
            CFO_NAME=f"CFO_{sec['TICKER']}",
            QUARTERLY_REVENUE=round(random.uniform(5, 50), 1),
            YOY_GROWTH=sample_value(bounds['revenue_growth']),
            QUARTERLY_EPS=round(random.uniform(1.0, 5.0), 2),
            GROSS_MARGIN=round(random.uniform(55, 75), 1),
            OPERATING_MARGIN=sample_value(bounds['ebit_margin'])
        )
        
        doc_id = f"ET_{sec['TICKER']}_{quarter}"
        title = f"{sec['COMPANYNAME']} {quarter} 2024 Earnings Call Transcript"
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_EARNINGS_TRANSCRIPTS 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, SECURITY_ID, ISSUER_ID, TICKER, COMPANY_NAME, FISCAL_QUARTER, FISCAL_YEAR, CALL_DATE)
            VALUES ('{doc_id}', '{title.replace("'", "''")}', 'earnings_transcript', '{content.replace("'", "''")}', 
                    {sec['SECURITYID']}, {sec['ISSUERID']}, '{sec['TICKER']}', '{sec['COMPANYNAME'].replace("'", "''")}',
                    '{quarter}', 2024, CURRENT_DATE())
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate POLICY DOCUMENTS (rich templates)
    # ==========================================================================
    session.sql(f"""
        INSERT INTO SAM_DEMO.RAW.RAW_POLICY_DOCS 
        (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, POLICY_TYPE, EFFECTIVE_DATE, VERSION)
        VALUES ('POL_CONCENTRATION', 'Concentration Risk Management Policy', 'policy', 
                '{CONCENTRATION_POLICY_TEMPLATE.replace("'", "''")}', 'concentration', CURRENT_DATE(), '2.1')
    """).collect()
    doc_count += 1
    
    # ==========================================================================
    # Generate MACRO EVENT documents (rich templates)
    # ==========================================================================
    taiwan_content = TAIWAN_EARTHQUAKE_TEMPLATE.format(EVENT_DATE=today)
    session.sql(f"""
        INSERT INTO SAM_DEMO.RAW.RAW_MACRO_EVENTS 
        (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, EVENT_TYPE, EVENT_DATE, REGION, SEVERITY, AFFECTED_SECTORS)
        VALUES ('ME_TAIWAN_EQ', 'Major Earthquake Disrupts Taiwan Semiconductor Production', 'macro_event', 
                '{taiwan_content.replace("'", "''")}', 'natural_disaster', CURRENT_DATE(), 'Taiwan', 'Critical', 'Information Technology, Consumer Discretionary')
    """).collect()
    doc_count += 1
    
    # ==========================================================================
    # Generate NGO REPORTS (ESG controversy alerts)
    # ==========================================================================
    categories = ['environmental', 'social', 'governance']
    severities = ['High', 'Medium', 'Low']
    for i, sec in enumerate(securities[20:28]):
        category = categories[i % 3]
        severity = severities[i % 3]
        ngo = random.choice(FICTIONAL_NGOS[category])
        
        content = NGO_REPORT_TEMPLATE.format(
            COMPANY_NAME=sec['COMPANYNAME'],
            TICKER=sec['TICKER'],
            PUBLISH_DATE=today,
            SEVERITY=severity,
            CATEGORY=category.capitalize(),
            NGO_NAME=ngo
        )
        
        doc_id = f"NGO_{sec['TICKER']}_{category[:3].upper()}"
        title = f"ESG Alert: {sec['COMPANYNAME']} - {category.capitalize()} Concerns"
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_NGO_REPORTS 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, ISSUER_ID, COMPANY_NAME, CONTROVERSY_TYPE, SEVERITY, NGO_NAME, REPORT_DATE)
            VALUES ('{doc_id}', '{title.replace("'", "''")}', 'ngo_report', '{content.replace("'", "''")}', 
                    {sec['ISSUERID']}, '{sec['COMPANYNAME'].replace("'", "''")}', '{category}', '{severity}', '{ngo}', CURRENT_DATE())
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate PRESS RELEASES
    # ==========================================================================
    PRESS_RELEASE_TEMPLATE = '''# {COMPANY_NAME} Announces Strong Quarterly Results Driven by Cloud and AI Growth

**{PUBLISH_DATE}** — {COMPANY_NAME} ({TICKER}), a leading {SIC_DESCRIPTION} company, today announced financial results for its fiscal quarter ended {QUARTER_END_DATE}, reporting revenue of ${QUARTERLY_REVENUE} billion, representing {YOY_GROWTH}% growth year-over-year, and diluted earnings per share of ${QUARTERLY_EPS}.

## Financial Highlights

- **Revenue**: ${QUARTERLY_REVENUE} billion, up {YOY_GROWTH}% year-over-year
- **Earnings Per Share**: ${QUARTERLY_EPS}, exceeding analyst consensus estimates
- **Cloud Platform Revenue**: Grew {CLOUD_GROWTH}% year-over-year, demonstrating strong enterprise adoption
- **Operating Cash Flow**: Strong cash generation for the quarter

"Our results this quarter reflect the strength of our technology platform and the significant opportunities we see in cloud computing and artificial intelligence," said CEO of {COMPANY_NAME}. "Enterprise customers continue to accelerate their digital transformation initiatives, and our comprehensive solutions are helping them innovate faster and operate more efficiently."

## Business Highlights

The company''s cloud computing platform continues to gain traction with enterprise customers, with several Fortune 500 companies expanding their deployments during the quarter. New AI-powered features launched this quarter have been well-received, with adoption rates exceeding internal projections.

{COMPANY_NAME} also announced strategic partnerships with leading system integrators to accelerate enterprise customer deployment of its cloud and AI solutions.

## Outlook and Guidance

For the coming quarter, {COMPANY_NAME} expects continued strong performance in its cloud platform business and growing contribution from AI-related products and services.

"Looking ahead, we see substantial opportunities across our business," said CFO of {COMPANY_NAME}. "Our innovation pipeline is robust, customer demand remains healthy, and we''re making strategic investments that position us for long-term growth."

---

*SAM Demo Content. Company details are illustrative for demonstration purposes.*
'''
    
    for i, sec in enumerate(securities[:15]):
        sector = sec['GICS_SECTOR']
        bounds = SECTOR_BOUNDS.get(sector, SECTOR_BOUNDS['default'])
        
        content = PRESS_RELEASE_TEMPLATE.format(
            COMPANY_NAME=sec['COMPANYNAME'],
            TICKER=sec['TICKER'],
            SIC_DESCRIPTION=sec['SIC_DESCRIPTION'] if sec['SIC_DESCRIPTION'] else sector,
            PUBLISH_DATE=today,
            QUARTER_END_DATE=today,
            QUARTERLY_REVENUE=round(random.uniform(5, 50), 1),
            YOY_GROWTH=sample_value(bounds['revenue_growth']),
            QUARTERLY_EPS=round(random.uniform(1.0, 5.0), 2),
            CLOUD_GROWTH=round(random.uniform(20, 80), 0)
        )
        
        doc_id = f"PR_{sec['TICKER']}_{i+1}"
        title = f"{sec['COMPANYNAME']} Announces Quarterly Results"
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_PRESS_RELEASES 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, SECURITY_ID, ISSUER_ID, TICKER, COMPANY_NAME, RELEASE_DATE, RELEASE_TYPE)
            VALUES ('{doc_id}', '{title.replace("'", "''")}', 'press_release', '{content.replace("'", "''")}', 
                    {sec['SECURITYID']}, {sec['ISSUERID']}, '{sec['TICKER']}', '{sec['COMPANYNAME'].replace("'", "''")}',
                    CURRENT_DATE(), 'earnings')
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate ENGAGEMENT NOTES
    # ==========================================================================
    ENGAGEMENT_NOTE_TEMPLATE = '''# ESG Engagement Log: {ISSUER_NAME} Management Meeting

**Date**: {PUBLISH_DATE}  
**Meeting Type**: Management Meeting  
**Companies**: {ISSUER_NAME} ({TICKER})  
**SAM Participants**: ESG Team, Portfolio Management  
**Company Participants**: Head of Sustainability, Investor Relations

---

## Meeting Overview

Snowcrest Asset Management''s ESG team conducted a management meeting with {ISSUER_NAME} to discuss the company''s environmental strategy, social initiatives, and governance practices.

The meeting focused on three primary areas: climate transition planning and emissions reduction targets, diversity and inclusion initiatives, and board composition and independence considerations.

---

## Key Discussion Points

**Environmental Strategy**: {ISSUER_NAME} provided updates on progress toward emissions reduction targets. Management acknowledged that Scope 3 measurement requires improvement and committed to publishing comprehensive Scope 3 inventory in the next sustainability report.

**Social Initiatives**: Discussion covered workforce diversity metrics, with management sharing data on gender and ethnic diversity across management levels. The company has implemented unconscious bias training and enhanced recruitment practices.

**Governance Matters**: Board composition was discussed, including plans for upcoming director elections. Management indicated openness to adding directors with relevant ESG expertise.

---

## Management Commitments and Next Steps

**Company Commitments**:
1. Publish Scope 3 emissions inventory in next annual sustainability report
2. Evaluate science-based emissions targets and provide update within 12 months
3. Enhance disclosure of diversity metrics by end of fiscal year
4. Consider ESG expertise in next board nomination process

**SAM Follow-up Actions**:
1. Monitor progress on Scope 3 disclosure commitment
2. Review science-based target evaluation in follow-up engagement
3. Assess diversity disclosure enhancements in annual reporting

**Next Engagement**: Scheduled follow-up meeting in 12 months to review progress.

---

## SAM Assessment

Management demonstrated genuine engagement with ESG topics and awareness of investor expectations. The commitments made are specific and measurable. We will continue monitoring the company''s ESG performance.

---

**Engagement Type**: Proactive | **Follow-up Required**: Yes

*Confidential - Snowcrest Asset Management Internal Use Only*
'''
    
    for i, sec in enumerate(securities[28:36]):
        content = ENGAGEMENT_NOTE_TEMPLATE.format(
            ISSUER_NAME=sec['COMPANYNAME'],
            TICKER=sec['TICKER'],
            PUBLISH_DATE=today
        )
        
        doc_id = f"ENG_{sec['TICKER']}_{i+1}"
        title = f"ESG Engagement: {sec['COMPANYNAME']} Management Meeting"
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_ENGAGEMENT_NOTES 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, ISSUER_ID, COMPANY_NAME, MEETING_TYPE, MEETING_DATE, ATTENDEES)
            VALUES ('{doc_id}', '{title.replace("'", "''")}', 'engagement', '{content.replace("'", "''")}', 
                    {sec['ISSUERID']}, '{sec['COMPANYNAME'].replace("'", "''")}', 'management_meeting', CURRENT_DATE(), 'ESG Team, Portfolio Management')
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate REPORT TEMPLATES
    # ==========================================================================
    report_template_content = '''# Investment Committee Decision: Mandate Compliance Action

## Executive Summary
This report documents the Investment Committee''s decision regarding mandate compliance actions for portfolio positions that have triggered compliance alerts.

## Compliance Alert Details

### Trigger Event
Detail the specific compliance violation:
- Security and position details
- Type of violation (ESG downgrade, concentration breach, etc.)
- Original vs current compliance metrics
- Action deadline

## Replacement Analysis

### Screening Process
Description of the candidate screening methodology:
- Number of candidates evaluated from pre-screened universe
- Mandate requirements applied (ESG grade, AI growth score, market cap, liquidity)
- Filtering criteria and thresholds

### Top Candidates Evaluated
Present a comparison table of the top candidates with key metrics.

## Recommended Security

### Investment Rationale
Detailed reasoning based on:
- AI growth potential
- ESG performance and governance
- Financial strength
- Strategic fit with portfolio thesis

### Quantitative Metrics
Present the key metrics showing mandate compliance with actual values.

## Decision Audit Trail

### Data Sources Referenced
List all data sources used:
- Compliance alerts table
- Pre-screened replacements table
- Broker research documents
- Earnings transcripts
- Semantic view queries

## Implementation Plan

### Execution Details
Outline the implementation:
- Actions to take
- Expected trade date
- Portfolio impact assessment

---

**Document Classification**: Internal - Investment Committee  
**Generated By**: Snowflake Intelligence - Portfolio Co-Pilot
'''
    
    session.sql(f"""
        INSERT INTO SAM_DEMO.RAW.RAW_REPORT_TEMPLATES 
        (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, TEMPLATE_TYPE, VERSION)
        VALUES ('TMPL_MANDATE', 'Mandate Compliance Investment Committee Report', 'template', 
                '{report_template_content.replace("'", "''")}', 'mandate_compliance', '1.0')
    """).collect()
    doc_count += 1
    
    # ==========================================================================
    # Generate CUSTODIAN REPORTS
    # ==========================================================================
    CUSTODIAN_REPORT_TEMPLATE = '''# Daily Holdings Report

**Custodian:** BNY Mellon  
**Portfolio:** SAM Technology & Infrastructure  
**Report Date:** {REPORT_DATE}  
**Valuation Date:** {REPORT_DATE}

## Executive Summary

This report provides a comprehensive summary of holdings positions for SAM Technology & Infrastructure as of {REPORT_DATE}. All positions have been reconciled against our internal records.

### Portfolio Overview
- **Total Asset Value:** £502.3M
- **Number of Positions:** 42
- **Cash Balance:** £8.5M
- **Pending Settlements:** 2

## Holdings Breakdown by Asset Class

### Equity Holdings
Total equity exposure represents 83% of the portfolio, comprising 35 positions across US, EU, and APAC regions.

### Fixed Income Holdings
Fixed income holdings account for 15% of total assets, with an average credit quality of A+ and weighted average maturity of 7.2 years.

## Settlement Activity

### Recent Settlements
- **Settled Purchases:** £13.4M purchases settled
- **Settled Sales:** £9.1M sales settled
- **Net Cash Impact:** Net positive cash flow

### Pending Settlements
- **Pending Purchases:** 1 equity purchase £1.8M
- **Pending Sales:** 1 equity sale £1.4M

## Corporate Actions
5 dividends processed, 2 stock splits, 1 rights issue

## Reconciliation Status
All positions have been successfully reconciled with our internal accounting system.

---

**Report Generated:** {REPORT_DATE} 18:00 GMT  
**Custodian Reference:** BNY-REF-2024-Q4-156  
**Operations Contact:** operations@snowcrestam.com
'''
    
    custodians = ['BNY Mellon', 'State Street', 'Northern Trust']
    for i, custodian in enumerate(custodians):
        content = CUSTODIAN_REPORT_TEMPLATE.format(
            REPORT_DATE=today
        )
        
        doc_id = f"CUST_{custodian.replace(' ', '_')}_{i+1}"
        title = f"Daily Holdings Report - {custodian}"
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_CUSTODIAN_REPORTS 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, CUSTODIAN_NAME, REPORT_DATE, REPORT_TYPE)
            VALUES ('{doc_id}', '{title}', 'custodian_report', '{content.replace("'", "''")}', 
                    '{custodian}', CURRENT_DATE(), 'daily_holdings')
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate RECONCILIATION NOTES
    # ==========================================================================
    RECON_NOTE_TEMPLATE = '''# Position Break Investigation

**Break ID:** RECON-2024-12-{BREAK_NUM}  
**Investigation Date:** {INVESTIGATION_DATE}  
**Portfolio:** {PORTFOLIO_NAME}  
**Security:** {SECURITY_NAME} ({TICKER})  
**Custodian:** BNY Mellon

## Break Details
- **Break Type:** Position Quantity Mismatch
- **Detection Date:** {INVESTIGATION_DATE}
- **Severity:** {SEVERITY}
- **Status:** {STATUS}

## Discrepancy
- **Internal Position:** {INTERNAL_QTY} shares
- **Custodian Position:** {CUSTODIAN_QTY} shares
- **Variance:** {VARIANCE} shares
- **Monetary Impact:** £{MONETARY_IMPACT} variance

## Root Cause Analysis
{ROOT_CAUSE}

## Investigation Findings
{FINDINGS}

## Resolution Actions
1. Verify trade booking status with middle office
2. Confirm settlement instructions with custodian
3. Reconcile position with updated custodian feed

## Timeline
- **Break Identified:** {INVESTIGATION_DATE}
- **Investigation Started:** {INVESTIGATION_DATE} 09:30
- **Root Cause Determined:** {INVESTIGATION_DATE}
- **Resolution Completed:** Expected within 2 business days

## Preventive Measures
Automated validation checks implemented to prevent similar occurrences.

---

**Investigated By:** Sarah Mitchell, Operations Manager  
**Approved By:** Chief Operating Officer  
**Reference:** RECON-2024-12-{BREAK_NUM}
'''
    
    break_types = [
        ('Position', 'High', 'Under Investigation', 'Late trade booking', 'Trade booking timing difference'),
        ('Cash', 'Medium', 'Investigating', 'Settlement timing mismatch', 'Custodian cash sweep timing'),
        ('Price', 'Low', 'Resolved', 'Pricing source difference', 'Price updated after reconciliation')
    ]
    
    for i, (break_type, severity, status, root_cause, findings) in enumerate(break_types):
        content = RECON_NOTE_TEMPLATE.format(
            BREAK_NUM=f"{156+i}",
            INVESTIGATION_DATE=today,
            PORTFOLIO_NAME='SAM Technology & Infrastructure',
            SECURITY_NAME='Apple Inc.',
            TICKER='AAPL',
            SEVERITY=severity,
            STATUS=status,
            INTERNAL_QTY='50,100',
            CUSTODIAN_QTY='50,000',
            VARIANCE='100',
            MONETARY_IMPACT='250,000',
            ROOT_CAUSE=root_cause,
            FINDINGS=findings
        )
        
        doc_id = f"RECON_{break_type.upper()}_{i+1}"
        title = f"{break_type} Break Investigation"
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_RECONCILIATION_NOTES 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, PORTFOLIO_NAME, RECON_DATE, BREAK_TYPE)
            VALUES ('{doc_id}', '{title}', 'reconciliation', '{content.replace("'", "''")}', 
                    'SAM Technology & Infrastructure', CURRENT_DATE(), '{break_type}')
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate SSI DOCUMENTS
    # ==========================================================================
    SSI_TEMPLATE = '''# Standard Settlement Instructions - {ASSET_CLASS}

**Document Type:** SSI Master Document  
**Asset Class:** {ASSET_CLASS}  
**Effective Date:** 01 January 2024  
**Version:** 3.2

## Overview
This document outlines the standard settlement instructions (SSI) for {ASSET_CLASS} transactions executed on behalf of Snowcrest Asset Management portfolios.

## Primary Custodian Details

### BNY Mellon - Global Securities
**Account Name:** SAM Technology & Infrastructure  
**Account Number:** SAM-TECH-001  
**BIC/SWIFT:** IRVTGB2X  
**LEI:** 213800D1EI4B9WTWWD28

## Settlement Instructions by Market

### United States
- **Depository:** The Depository Trust Company (DTC)
- **DTC Participant Number:** 0901
- **Settlement Cycle:** T+2
- **Special Instructions:** Settlement via DTC, T+2 standard

### United Kingdom
- **Depository:** Euroclear UK & International (CREST)
- **CREST Participant ID:** CRST-SAM-001
- **Settlement Cycle:** T+2

### European Union Markets
- **Depository:** Euroclear Bank S.A./N.V.
- **Euroclear Account:** ECL-SAM-001
- **Settlement Cycle:** T+2

## Delivery vs Payment (DVP) Requirements
All securities settlements must be conducted on a Delivery vs Payment (DVP) basis unless otherwise approved.

## Settlement Failures Protocol
Notify counterparty T+1, escalate T+3, buy-in T+5

## Contact Information
**Operations Desk:** ops.desk@snowcrestam.com  
**Settlements Team:** settlements@snowcrestam.com

---

**Document Owner:** Middle Office Operations  
**Approval Authority:** Chief Operating Officer  
**SSI Reference:** SSI-SAM-TECH-{ASSET_CLASS_CODE}-001
'''
    
    asset_classes = [
        ('Listed Equities', 'EQUITY'),
        ('Corporate Bonds', 'BOND'),
        ('Foreign Exchange', 'FX')
    ]
    
    for asset_class, code in asset_classes:
        content = SSI_TEMPLATE.format(
            ASSET_CLASS=asset_class,
            ASSET_CLASS_CODE=code
        )
        
        doc_id = f"SSI_{code}"
        title = f"Standard Settlement Instructions - {asset_class}"
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_SSI_DOCUMENTS 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, COUNTERPARTY_NAME, ASSET_CLASS, CURRENCY)
            VALUES ('{doc_id}', '{title}', 'ssi', '{content.replace("'", "''")}', 
                    'BNY Mellon', '{asset_class}', 'USD')
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate OPS PROCEDURES
    # ==========================================================================
    OPS_PROCEDURE_TEMPLATE = '''# {PROCEDURE_TITLE}

**Document Type:** Standard Operating Procedure  
**Procedure ID:** SOP-MO-{PROC_ID}  
**Version:** 3.2  
**Effective Date:** 01 January 2024  
**Owner:** Middle Office Operations

## Purpose
This procedure defines the standard process for {PURPOSE} for all Snowcrest Asset Management portfolios.

## Scope
This procedure applies to all {SCOPE} processed through our custodian network.

## Roles and Responsibilities

### Operations Analyst
- Monitor daily reports and systems
- Identify and log all issues
- Initiate investigation process
- Update tracking system

### Middle Office Manager
- Review all escalated issues
- Approve resolution actions
- Coordinate with Risk and Compliance
- Sign off on completed actions

## Procedure Steps

### Step 1: Detection and Logging (Daily, 09:00)
1. Access relevant systems and reports
2. Export data for analysis
3. Categorize issues by type and severity
4. Log findings in tracking system

### Step 2: Investigation (Same Day, Before 12:00)
1. Review details and context
2. Contact custodian or counterparties as needed
3. Document investigation notes
4. Determine root cause

### Step 3: Resolution Actions (Same Day)
1. Execute corrective actions
2. Verify resolution
3. Document outcome
4. Update tracking system

### Step 4: Monitoring and Follow-up (Daily Until Resolved)
1. Check status of pending items
2. Escalate if no progress
3. Update stakeholders

## Reporting Requirements
- Daily status reports
- Weekly summary reports
- Monthly performance metrics

## Key Performance Indicators (KPIs)
- Issue resolution rate
- Average resolution time
- Escalation frequency

## Contact Information
**Operations Desk:** Middle Office Operations Desk  
**Middle Office Manager:** Sarah Mitchell

---

**Document Reference:** SAM-MO-SOP-{PROC_ID}-v3.2
'''
    
    procedures = [
        ('Settlement Failure Resolution', '001', 'identifying, investigating, and resolving settlement failures', 'settlement failures across equity and fixed income'),
        ('NAV Calculation Process', '002', 'calculating daily Net Asset Values', 'NAV calculations for all portfolios'),
        ('Reconciliation Workflow', '003', 'reconciling positions and cash balances', 'reconciliation breaks and discrepancies')
    ]
    
    for title, proc_id, purpose, scope in procedures:
        content = OPS_PROCEDURE_TEMPLATE.format(
            PROCEDURE_TITLE=title,
            PROC_ID=proc_id,
            PURPOSE=purpose,
            SCOPE=scope
        )
        
        doc_id = f"OPS_{proc_id}"
        proc_title = title
        
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_OPS_PROCEDURES 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, PROCEDURE_TYPE, VERSION)
            VALUES ('{doc_id}', '{proc_title}', 'procedure', '{content.replace("'", "''")}', 
                    '{title.lower().replace(' ', '_')}', '3.2')
        """).collect()
        doc_count += 1
    
    # ==========================================================================
    # Generate remaining document types with simplified but professional content
    # ==========================================================================
    
    # Philosophy documents
    philosophy_docs = [
        ('PHIL_ESG', 'SAM ESG Investment Philosophy', 'esg', '''# SAM ESG Investment Philosophy

## Our Commitment to Sustainable Investing

At Snowcrest Asset Management, we believe that integrating environmental, social, and governance (ESG) factors into our investment process creates long-term value for our clients whilst contributing to positive societal outcomes.

## Core Principles

**Integration**: ESG analysis is embedded throughout our investment process, from initial screening through ongoing monitoring. We consider ESG factors alongside traditional financial metrics to build a comprehensive view of investment opportunities and risks.

**Engagement**: We actively engage with portfolio companies to encourage improved ESG practices. Our engagement focuses on material issues that affect long-term value creation and risk management.

**Stewardship**: We exercise our voting rights responsibly, supporting resolutions that promote good governance, environmental sustainability, and social responsibility.

## Implementation

Our ESG integration framework applies to all asset classes and investment strategies. We utilise proprietary ESG scoring alongside third-party data to ensure comprehensive coverage.

*This philosophy guides our commitment to responsible investing for the benefit of our clients and society.*'''),
        ('PHIL_RISK', 'SAM Risk Management Philosophy', 'risk', '''# SAM Risk Management Philosophy

## Risk-Aware Investment Approach

At Snowcrest Asset Management, we believe that superior risk management is fundamental to delivering consistent, long-term investment returns.

## Core Principles

**Risk-Adjusted Returns**: We focus on risk-adjusted returns rather than absolute performance. Every investment decision considers the risk taken to achieve expected returns.

**Diversification**: We maintain diversified portfolios across securities, sectors, geographies, and asset classes. Concentration risk is actively monitored and managed.

**Transparency**: We provide clear, comprehensive risk reporting to clients and stakeholders. Our risk metrics and methodologies are fully documented and regularly reviewed.

## Implementation

Our risk management framework includes daily monitoring, stress testing, and scenario analysis across all portfolios.

*This philosophy reflects our commitment to protecting client capital whilst pursuing investment objectives.*''')
    ]
    
    for doc_id, title, phil_type, content in philosophy_docs:
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_PHILOSOPHY_DOCS 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, PHILOSOPHY_TYPE, VERSION)
            VALUES ('{doc_id}', '{title}', 'philosophy', '{content.replace("'", "''")}', '{phil_type}', '1.0')
        """).collect()
        doc_count += 1
    
    # Sales templates
    sales_templates = [
        ('TMPL_QUARTERLY', 'Quarterly Client Letter Template', 'quarterly_letter', '''# Quarterly Investment Report

**Portfolio**: [Portfolio Name]  
**Period**: [Quarter] [Year]  
**Prepared For**: [Client Name]

---

## Performance Summary

| Metric | Portfolio | Benchmark | Relative |
|--------|-----------|-----------|----------|
| Quarter | X.XX% | X.XX% | +X.XX% |
| Year-to-Date | X.XX% | X.XX% | +X.XX% |
| Since Inception | X.XX% | X.XX% | +X.XX% |

## Market Commentary

[Market overview and key developments during the quarter]

## Portfolio Positioning

[Discussion of key allocation decisions and rationale]

## Outlook

[Forward-looking commentary on market expectations and portfolio strategy]

---

*This report is prepared by Snowcrest Asset Management for client information purposes.*'''),
        ('TMPL_MONTHLY', 'Monthly Performance Report Template', 'monthly_report', '''# Monthly Performance Summary

**Portfolio**: [Portfolio Name]  
**As of**: [Date]

## Performance

| Period | Return | Benchmark | Active |
|--------|--------|-----------|--------|
| MTD | X.XX% | X.XX% | +X.XX% |
| YTD | X.XX% | X.XX% | +X.XX% |

## Top Contributors
1. [Security 1] - +X.XX%
2. [Security 2] - +X.XX%

## Top Detractors
1. [Security 1] - -X.XX%
2. [Security 2] - -X.XX%

---

*Snowcrest Asset Management*''')
    ]
    
    for doc_id, title, tmpl_type, content in sales_templates:
        session.sql(f"""
            INSERT INTO SAM_DEMO.RAW.RAW_SALES_TEMPLATES 
            (DOCUMENT_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT, TEMPLATE_TYPE, VERSION)
            VALUES ('{doc_id}', '{title}', 'template', '{content.replace("'", "''")}', '{tmpl_type}', '1.0')
        """).collect()
        doc_count += 1
    
    return f"Generated {doc_count} rich documents successfully using embedded templates"
$$;

-- Execute document generation
CALL SAM_DEMO.AI.GENERATE_SAMPLE_DOCUMENTS();

-- ============================================================================
-- SECTION 12: CORTEX SEARCH SERVICES
-- ============================================================================

USE SCHEMA SAM_DEMO.AI;

-- Create Cortex Search service for broker research
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_BROKER_RESEARCH
    ON CONTENT
    ATTRIBUTES TICKER, COMPANY_NAME, SECTOR, RATING
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            TICKER,
            COMPANY_NAME,
            SECTOR,
            RATING,
            PUBLISH_DATE
        FROM SAM_DEMO.RAW.RAW_BROKER_RESEARCH
    );

-- Create Cortex Search service for earnings transcripts
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_EARNINGS_TRANSCRIPTS
    ON CONTENT
    ATTRIBUTES TICKER, COMPANY_NAME, FISCAL_QUARTER, FISCAL_YEAR
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            TICKER,
            COMPANY_NAME,
            FISCAL_QUARTER,
            FISCAL_YEAR,
            CALL_DATE
        FROM SAM_DEMO.RAW.RAW_EARNINGS_TRANSCRIPTS
    );

-- Create Cortex Search service for press releases
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_PRESS_RELEASES
    ON CONTENT
    ATTRIBUTES TICKER, COMPANY_NAME, RELEASE_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            TICKER,
            COMPANY_NAME,
            RELEASE_TYPE,
            RELEASE_DATE
        FROM SAM_DEMO.RAW.RAW_PRESS_RELEASES
    );

-- Create Cortex Search service for macro events
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_MACRO_EVENTS
    ON CONTENT
    ATTRIBUTES EVENT_TYPE, REGION, SEVERITY, AFFECTED_SECTORS
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            EVENT_TYPE,
            REGION,
            SEVERITY,
            AFFECTED_SECTORS,
            EVENT_DATE
        FROM SAM_DEMO.RAW.RAW_MACRO_EVENTS
    );

-- Create Cortex Search service for policy documents
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_POLICY_DOCS
    ON CONTENT
    ATTRIBUTES POLICY_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            POLICY_TYPE,
            EFFECTIVE_DATE,
            VERSION
        FROM SAM_DEMO.RAW.RAW_POLICY_DOCS
    );

-- Create Cortex Search service for NGO reports
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_NGO_REPORTS
    ON CONTENT
    ATTRIBUTES COMPANY_NAME, NGO_NAME, CONTROVERSY_TYPE, SEVERITY
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            COMPANY_NAME,
            NGO_NAME,
            CONTROVERSY_TYPE,
            SEVERITY,
            REPORT_DATE
        FROM SAM_DEMO.RAW.RAW_NGO_REPORTS
    );

-- Create Cortex Search service for engagement notes
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_ENGAGEMENT_NOTES
    ON CONTENT
    ATTRIBUTES COMPANY_NAME, MEETING_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            COMPANY_NAME,
            MEETING_TYPE,
            MEETING_DATE,
            ATTENDEES
        FROM SAM_DEMO.RAW.RAW_ENGAGEMENT_NOTES
    );

-- Create Cortex Search service for sales templates
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_SALES_TEMPLATES
    ON CONTENT
    ATTRIBUTES TEMPLATE_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            TEMPLATE_TYPE,
            VERSION
        FROM SAM_DEMO.RAW.RAW_SALES_TEMPLATES
    );

-- Create Cortex Search service for philosophy documents
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_PHILOSOPHY_DOCS
    ON CONTENT
    ATTRIBUTES PHILOSOPHY_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            PHILOSOPHY_TYPE,
            VERSION
        FROM SAM_DEMO.RAW.RAW_PHILOSOPHY_DOCS
    );

-- Create Cortex Search service for report templates
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_REPORT_TEMPLATES
    ON CONTENT
    ATTRIBUTES TEMPLATE_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            TEMPLATE_TYPE,
            VERSION
        FROM SAM_DEMO.RAW.RAW_REPORT_TEMPLATES
    );

-- Create Cortex Search service for internal research (reuses broker research with filter)
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_INTERNAL_RESEARCH
    ON CONTENT
    ATTRIBUTES TICKER, COMPANY_NAME, SECTOR, ANALYST_NAME
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            TICKER,
            COMPANY_NAME,
            SECTOR,
            ANALYST_NAME,
            PUBLISH_DATE
        FROM SAM_DEMO.RAW.RAW_BROKER_RESEARCH
    );

-- Create Cortex Search service for investment memos (reuses broker research with filter)
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_INVESTMENT_MEMOS
    ON CONTENT
    ATTRIBUTES TICKER, COMPANY_NAME, SECTOR
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            TICKER,
            COMPANY_NAME,
            SECTOR,
            PUBLISH_DATE
        FROM SAM_DEMO.RAW.RAW_BROKER_RESEARCH
    );

-- Middle Office Search Services
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_CUSTODIAN_REPORTS
    ON CONTENT
    ATTRIBUTES CUSTODIAN_NAME, REPORT_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            CUSTODIAN_NAME,
            REPORT_TYPE,
            REPORT_DATE
        FROM SAM_DEMO.RAW.RAW_CUSTODIAN_REPORTS
    );

CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_RECONCILIATION_NOTES
    ON CONTENT
    ATTRIBUTES PORTFOLIO_NAME, BREAK_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            PORTFOLIO_NAME,
            BREAK_TYPE,
            RECON_DATE
        FROM SAM_DEMO.RAW.RAW_RECONCILIATION_NOTES
    );

CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_SSI_DOCUMENTS
    ON CONTENT
    ATTRIBUTES COUNTERPARTY_NAME, ASSET_CLASS, CURRENCY
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            COUNTERPARTY_NAME,
            ASSET_CLASS,
            CURRENCY
        FROM SAM_DEMO.RAW.RAW_SSI_DOCUMENTS
    );

CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_OPS_PROCEDURES
    ON CONTENT
    ATTRIBUTES PROCEDURE_TYPE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TITLE,
            CONTENT,
            PROCEDURE_TYPE,
            VERSION
        FROM SAM_DEMO.RAW.RAW_OPS_PROCEDURES
    );

-- ============================================================================
-- SECTION 13: SEMANTIC VIEWS FOR CORTEX ANALYST
-- ============================================================================

-- SAM_ANALYST_VIEW - Main portfolio analytics semantic view
CREATE OR REPLACE SEMANTIC VIEW SAM_DEMO.AI.SAM_ANALYST_VIEW
    TABLES (
        HOLDINGS AS SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR
            PRIMARY KEY (HOLDINGDATE, PORTFOLIOID, SECURITYID) 
            WITH SYNONYMS=('positions','holdings','portfolio_holdings') 
            COMMENT='Daily position snapshots for portfolio analysis',
        SECURITIES AS SAM_DEMO.CURATED.DIM_SECURITY
            PRIMARY KEY (SECURITYID) 
            WITH SYNONYMS=('securities','stocks','instruments') 
            COMMENT='Security master data',
        PORTFOLIOS AS SAM_DEMO.CURATED.DIM_PORTFOLIO
            PRIMARY KEY (PORTFOLIOID) 
            WITH SYNONYMS=('portfolios','funds','strategies') 
            COMMENT='Portfolio information',
        ISSUERS AS SAM_DEMO.CURATED.DIM_ISSUER
            PRIMARY KEY (ISSUERID) 
            WITH SYNONYMS=('issuers','corporates','issuer_entities') 
            COMMENT='Issuer and corporate data'
    )
    RELATIONSHIPS (
        HOLDINGS_TO_SECURITIES AS HOLDINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
        HOLDINGS_TO_PORTFOLIOS AS HOLDINGS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
        SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID)
    )
    DIMENSIONS (
        PORTFOLIOS.PortfolioName AS PORTFOLIONAME WITH SYNONYMS=('portfolio','fund_name') COMMENT='Portfolio name',
        PORTFOLIOS.InvestmentStrategy AS STRATEGY WITH SYNONYMS=('strategy','investment_style') COMMENT='Investment strategy',
        SECURITIES.TickerSymbol AS TICKER WITH SYNONYMS=('ticker','symbol') COMMENT='Trading ticker symbol',
        SECURITIES.SecurityName AS DESCRIPTION WITH SYNONYMS=('security_name','company_name') COMMENT='Security description',
        SECURITIES.AssetClass AS ASSETCLASS WITH SYNONYMS=('asset_class','security_type') COMMENT='Asset classification',
        ISSUERS.Company_Legal_Name AS LEGALNAME WITH SYNONYMS=('issuer','company','issuer_name','legal_name') COMMENT='Issuer legal name',
        ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('sector','industry_sector','gics_sector') COMMENT='Industry sector',
        ISSUERS.CountryOfIncorporation AS COUNTRYOFINCORPORATION WITH SYNONYMS=('country','domicile','region') COMMENT='Country of incorporation',
        HOLDINGS.HoldingDate AS HOLDINGDATE WITH SYNONYMS=('date','position_date','as_of_date') COMMENT='Position date'
    )
    METRICS (
        HOLDINGS.TOTAL_MARKET_VALUE AS SUM(MARKETVALUE_BASE) WITH SYNONYMS=('market_value','value','aum') COMMENT='Total market value in base currency',
        HOLDINGS.PORTFOLIO_WEIGHT AS SUM(PORTFOLIOWEIGHT) * 100 WITH SYNONYMS=('weight','allocation','percentage') COMMENT='Portfolio weight as percentage',
        HOLDINGS.HOLDING_COUNT AS COUNT(DISTINCT SECURITYID) WITH SYNONYMS=('count','number_of_holdings') COMMENT='Number of distinct holdings',
        HOLDINGS.ISSUER_EXPOSURE AS SUM(MARKETVALUE_BASE) WITH SYNONYMS=('issuer_exposure','company_exposure') COMMENT='Exposure to issuer',
        HOLDINGS.MAX_POSITION_WEIGHT AS MAX(PORTFOLIOWEIGHT) * 100 WITH SYNONYMS=('max_weight','largest_position') COMMENT='Maximum single position weight'
    )
    COMMENT='Portfolio analytics semantic view for holdings analysis and concentration monitoring';

-- SAM_SEC_FILINGS_VIEW - SEC filings semantic view for fundamental analysis
CREATE OR REPLACE SEMANTIC VIEW SAM_DEMO.AI.SAM_SEC_FILINGS_VIEW
    TABLES (
        SEC_FILINGS AS SAM_DEMO.CURATED.FACT_SEC_FILINGS
            PRIMARY KEY (FILINGID) 
            WITH SYNONYMS=('filings','sec_data','financials') 
            COMMENT='SEC filing financial data',
        SECURITIES AS SAM_DEMO.CURATED.DIM_SECURITY
            PRIMARY KEY (SECURITYID) 
            WITH SYNONYMS=('securities','stocks') 
            COMMENT='Security master data',
        ISSUERS AS SAM_DEMO.CURATED.DIM_ISSUER
            PRIMARY KEY (ISSUERID) 
            WITH SYNONYMS=('issuers','filing_issuers') 
            COMMENT='Issuer data'
    )
    RELATIONSHIPS (
        SEC_FILINGS_TO_SECURITIES AS SEC_FILINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
        SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID)
    )
    DIMENSIONS (
        ISSUERS.CompanyName AS LEGALNAME WITH SYNONYMS=('company','issuer_name') COMMENT='Company legal name',
        ISSUERS.TickerSymbol AS PRIMARYTICKER WITH SYNONYMS=('ticker','symbol') COMMENT='Primary ticker symbol',
        ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry','sector') COMMENT='Industry classification',
        SEC_FILINGS.CIK AS CIK WITH SYNONYMS=('cik','sec_id') COMMENT='SEC Central Index Key',
        SEC_FILINGS.FormType AS FORMTYPE WITH SYNONYMS=('form','filing_type') COMMENT='SEC form type',
        SEC_FILINGS.MetricName AS TAG WITH SYNONYMS=('metric','measure') COMMENT='Financial metric name',
        SEC_FILINGS.FilingDate AS FILINGDATE WITH SYNONYMS=('date','report_date') COMMENT='Filing date',
        SEC_FILINGS.FiscalPeriod AS FISCALPERIOD WITH SYNONYMS=('quarter','period') COMMENT='Fiscal period',
        SEC_FILINGS.FiscalYear AS FISCALYEAR WITH SYNONYMS=('year') COMMENT='Fiscal year'
    )
    METRICS (
        SEC_FILINGS.MEASURE_VALUE AS SUM(MEASUREVALUE) WITH SYNONYMS=('value','amount') COMMENT='Financial metric value',
        SEC_FILINGS.TOTAL_REVENUE AS SUM(CASE WHEN TAG IN ('Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax') THEN MEASUREVALUE END) WITH SYNONYMS=('revenue','sales') COMMENT='Total revenue',
        SEC_FILINGS.NET_INCOME AS SUM(CASE WHEN TAG = 'NetIncomeLoss' THEN MEASUREVALUE END) WITH SYNONYMS=('profit','earnings') COMMENT='Net income',
        SEC_FILINGS.TOTAL_ASSETS AS SUM(CASE WHEN TAG = 'Assets' THEN MEASUREVALUE END) WITH SYNONYMS=('assets') COMMENT='Total assets',
        SEC_FILINGS.TOTAL_EQUITY AS SUM(CASE WHEN TAG = 'StockholdersEquity' THEN MEASUREVALUE END) WITH SYNONYMS=('equity') COMMENT='Shareholders equity'
    )
    COMMENT='SEC filing data semantic view for financial analysis';

-- SAM_RESEARCH_VIEW - Research analysis semantic view (reuses SEC filings data)
CREATE OR REPLACE SEMANTIC VIEW SAM_DEMO.AI.SAM_RESEARCH_VIEW
    TABLES (
        SEC_FILINGS AS SAM_DEMO.CURATED.FACT_SEC_FILINGS
            PRIMARY KEY (FILINGID) 
            WITH SYNONYMS=('filings','sec_data','financials','fundamentals') 
            COMMENT='SEC filing financial data for research',
        SECURITIES AS SAM_DEMO.CURATED.DIM_SECURITY
            PRIMARY KEY (SECURITYID) 
            WITH SYNONYMS=('securities','stocks','instruments') 
            COMMENT='Security master data',
        ISSUERS AS SAM_DEMO.CURATED.DIM_ISSUER
            PRIMARY KEY (ISSUERID) 
            WITH SYNONYMS=('issuers','corporates','entities') 
            COMMENT='Issuer data',
        MARKET_DATA AS SAM_DEMO.CURATED.FACT_MARKETDATA_TIMESERIES
            PRIMARY KEY (PRICEDATE, SECURITYID)
            WITH SYNONYMS=('prices','market_data','price_data')
            COMMENT='Historical market prices'
    )
    RELATIONSHIPS (
        SEC_FILINGS_TO_SECURITIES AS SEC_FILINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
        SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID),
        MARKET_DATA_TO_SECURITIES AS MARKET_DATA(SECURITYID) REFERENCES SECURITIES(SECURITYID)
    )
    DIMENSIONS (
        ISSUERS.CompanyName AS LEGALNAME WITH SYNONYMS=('company','issuer_name','legal_name') COMMENT='Company legal name',
        SECURITIES.TickerSymbol AS TICKER WITH SYNONYMS=('ticker','symbol','stock_symbol') COMMENT='Primary ticker symbol',
        ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry','sector','gics_sector') COMMENT='Industry classification',
        SEC_FILINGS.CIK AS CIK WITH SYNONYMS=('cik','sec_id') COMMENT='SEC Central Index Key',
        SEC_FILINGS.FormType AS FORMTYPE WITH SYNONYMS=('form','filing_type') COMMENT='SEC form type (10-K, 10-Q)',
        SEC_FILINGS.MetricName AS TAG WITH SYNONYMS=('metric','measure','financial_metric') COMMENT='Financial metric name',
        SEC_FILINGS.FilingDate AS FILINGDATE WITH SYNONYMS=('date','report_date','filing_date') COMMENT='Filing date',
        SEC_FILINGS.FiscalPeriod AS FISCALPERIOD WITH SYNONYMS=('quarter','period','fiscal_quarter') COMMENT='Fiscal period (Q1, Q2, Q3, Q4)',
        SEC_FILINGS.FiscalYear AS FISCALYEAR WITH SYNONYMS=('year','fiscal_year') COMMENT='Fiscal year',
        MARKET_DATA.PriceDate AS PRICEDATE WITH SYNONYMS=('date','price_date','trading_date') COMMENT='Price date'
    )
    METRICS (
        SEC_FILINGS.MEASURE_VALUE AS SUM(MEASUREVALUE) WITH SYNONYMS=('value','amount','metric_value') COMMENT='Financial metric value',
        SEC_FILINGS.TOTAL_REVENUE AS SUM(CASE WHEN TAG IN ('Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax') THEN MEASUREVALUE END) WITH SYNONYMS=('revenue','sales','top_line') COMMENT='Total revenue',
        SEC_FILINGS.NET_INCOME AS SUM(CASE WHEN TAG = 'NetIncomeLoss' THEN MEASUREVALUE END) WITH SYNONYMS=('profit','earnings','net_income','bottom_line') COMMENT='Net income',
        SEC_FILINGS.GROSS_PROFIT AS SUM(CASE WHEN TAG = 'GrossProfit' THEN MEASUREVALUE END) WITH SYNONYMS=('gross_profit','gross_margin_dollars') COMMENT='Gross profit',
        SEC_FILINGS.OPERATING_INCOME AS SUM(CASE WHEN TAG = 'OperatingIncomeLoss' THEN MEASUREVALUE END) WITH SYNONYMS=('operating_income','ebit','operating_profit') COMMENT='Operating income',
        SEC_FILINGS.TOTAL_ASSETS AS SUM(CASE WHEN TAG = 'Assets' THEN MEASUREVALUE END) WITH SYNONYMS=('assets','total_assets') COMMENT='Total assets',
        SEC_FILINGS.TOTAL_EQUITY AS SUM(CASE WHEN TAG = 'StockholdersEquity' THEN MEASUREVALUE END) WITH SYNONYMS=('equity','shareholders_equity','book_value') COMMENT='Shareholders equity',
        SEC_FILINGS.TOTAL_LIABILITIES AS SUM(CASE WHEN TAG IN ('Liabilities', 'LiabilitiesCurrent') THEN MEASUREVALUE END) WITH SYNONYMS=('liabilities','total_liabilities','debt') COMMENT='Total liabilities',
        SEC_FILINGS.CASH_AND_EQUIVALENTS AS SUM(CASE WHEN TAG = 'CashAndCashEquivalentsAtCarryingValue' THEN MEASUREVALUE END) WITH SYNONYMS=('cash','cash_position') COMMENT='Cash and cash equivalents',
        MARKET_DATA.CLOSING_PRICE AS AVG(PRICE_CLOSE) WITH SYNONYMS=('price','stock_price','close_price') COMMENT='Average closing price',
        MARKET_DATA.TRADING_VOLUME AS SUM(VOLUME) WITH SYNONYMS=('volume','shares_traded') COMMENT='Trading volume'
    )
    COMMENT='Research analysis semantic view combining SEC filings and market data for fundamental research';

-- SAM_QUANT_VIEW - Quantitative factor analysis semantic view
CREATE OR REPLACE SEMANTIC VIEW SAM_DEMO.AI.SAM_QUANT_VIEW
    TABLES (
        FACTOR_EXPOSURES AS SAM_DEMO.CURATED.FACT_FACTOR_EXPOSURES
            PRIMARY KEY (SECURITYID, EXPOSURE_DATE, FACTOR_NAME) 
            WITH SYNONYMS=('factors','exposures','loadings') 
            COMMENT='Factor exposure data',
        SECURITIES AS SAM_DEMO.CURATED.DIM_SECURITY
            PRIMARY KEY (SECURITYID) 
            WITH SYNONYMS=('securities','stocks') 
            COMMENT='Security master data',
        ISSUERS AS SAM_DEMO.CURATED.DIM_ISSUER
            PRIMARY KEY (ISSUERID) 
            WITH SYNONYMS=('issuers','quant_issuers') 
            COMMENT='Issuer data'
    )
    RELATIONSHIPS (
        FACTORS_TO_SECURITIES AS FACTOR_EXPOSURES(SECURITYID) REFERENCES SECURITIES(SECURITYID),
        SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID)
    )
    DIMENSIONS (
        SECURITIES.TickerSymbol AS TICKER WITH SYNONYMS=('ticker','symbol') COMMENT='Trading ticker',
        SECURITIES.SecurityName AS DESCRIPTION WITH SYNONYMS=('security_name','company') COMMENT='Security name',
        ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('sector','industry_sector') COMMENT='Industry sector',
        FACTOR_EXPOSURES.FactorName AS FACTOR_NAME WITH SYNONYMS=('factor','style') COMMENT='Factor name',
        FACTOR_EXPOSURES.ExposureDate AS EXPOSURE_DATE WITH SYNONYMS=('date') COMMENT='Exposure date'
    )
    METRICS (
        FACTOR_EXPOSURES.EXPOSURE_VALUE AS AVG(EXPOSURE_VALUE) WITH SYNONYMS=('exposure','loading','beta') COMMENT='Factor exposure value',
        FACTOR_EXPOSURES.R_SQUARED AS AVG(R_SQUARED) WITH SYNONYMS=('r_squared','fit') COMMENT='R-squared of factor model'
    )
    COMMENT='Quantitative factor analysis semantic view';

-- SAM_IMPLEMENTATION_VIEW - Implementation and trading semantic view
CREATE OR REPLACE SEMANTIC VIEW SAM_DEMO.AI.SAM_IMPLEMENTATION_VIEW
    TABLES (
        TRANSACTIONS AS SAM_DEMO.CURATED.FACT_TRANSACTION
            PRIMARY KEY (TRANSACTIONID) 
            WITH SYNONYMS=('trades','transactions','orders') 
            COMMENT='Transaction history',
        SECURITIES AS SAM_DEMO.CURATED.DIM_SECURITY
            PRIMARY KEY (SECURITYID) 
            WITH SYNONYMS=('securities','stocks') 
            COMMENT='Security master data',
        PORTFOLIOS AS SAM_DEMO.CURATED.DIM_PORTFOLIO
            PRIMARY KEY (PORTFOLIOID) 
            WITH SYNONYMS=('portfolios','funds') 
            COMMENT='Portfolio information'
    )
    RELATIONSHIPS (
        TRANSACTIONS_TO_SECURITIES AS TRANSACTIONS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
        TRANSACTIONS_TO_PORTFOLIOS AS TRANSACTIONS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID)
    )
    DIMENSIONS (
        PORTFOLIOS.PortfolioName AS PORTFOLIONAME WITH SYNONYMS=('portfolio','fund') COMMENT='Portfolio name',
        SECURITIES.TickerSymbol AS TICKER WITH SYNONYMS=('ticker','symbol') COMMENT='Trading ticker',
        TRANSACTIONS.TransactionType AS TRANSACTIONTYPE WITH SYNONYMS=('type','side') COMMENT='Buy or Sell',
        TRANSACTIONS.TradeDate AS TRANSACTIONDATE WITH SYNONYMS=('date','trade_date') COMMENT='Transaction date'
    )
    METRICS (
        TRANSACTIONS.TRADE_VALUE AS SUM(GROSSAMOUNT_LOCAL) WITH SYNONYMS=('value','amount','notional') COMMENT='Trade value',
        TRANSACTIONS.TRADE_COUNT AS COUNT(TRANSACTIONID) WITH SYNONYMS=('count','number_of_trades') COMMENT='Number of trades',
        TRANSACTIONS.TOTAL_COMMISSION AS SUM(COMMISSION_LOCAL) WITH SYNONYMS=('commission','costs') COMMENT='Total commission'
    )
    COMMENT='Implementation and trading analytics semantic view';

-- SAM_SUPPLY_CHAIN_VIEW - Supply chain risk semantic view
CREATE OR REPLACE SEMANTIC VIEW SAM_DEMO.AI.SAM_SUPPLY_CHAIN_VIEW
    TABLES (
        SUPPLY_CHAIN AS SAM_DEMO.CURATED.DIM_SUPPLY_CHAIN_RELATIONSHIPS
            PRIMARY KEY (RELATIONSHIPID) 
            WITH SYNONYMS=('supply_chain','dependencies','relationships') 
            COMMENT='Supply chain relationships',
        COMPANY_ISSUERS AS SAM_DEMO.CURATED.DIM_ISSUER
            PRIMARY KEY (ISSUERID) 
            WITH SYNONYMS=('primary_companies','customers') 
            COMMENT='Company issuer information',
        COUNTERPARTY_ISSUERS AS SAM_DEMO.CURATED.DIM_ISSUER
            PRIMARY KEY (ISSUERID) 
            WITH SYNONYMS=('counterparties','suppliers') 
            COMMENT='Counterparty issuer information'
    )
    RELATIONSHIPS (
        SUPPLY_CHAIN_TO_COMPANY AS SUPPLY_CHAIN(COMPANY_ISSUERID) REFERENCES COMPANY_ISSUERS(ISSUERID),
        SUPPLY_CHAIN_TO_COUNTERPARTY AS SUPPLY_CHAIN(COUNTERPARTY_ISSUERID) REFERENCES COUNTERPARTY_ISSUERS(ISSUERID)
    )
    DIMENSIONS (
        COMPANY_ISSUERS.CompanyName AS LEGALNAME WITH SYNONYMS=('company','customer') COMMENT='Company name',
        COUNTERPARTY_ISSUERS.SupplierName AS LEGALNAME WITH SYNONYMS=('supplier','counterparty') COMMENT='Supplier name',
        SUPPLY_CHAIN.RelationshipType AS RELATIONSHIPTYPE WITH SYNONYMS=('type','relationship') COMMENT='Relationship type',
        SUPPLY_CHAIN.CriticalityTier AS CRITICALITYTIER WITH SYNONYMS=('criticality','importance') COMMENT='Criticality tier'
    )
    METRICS (
        SUPPLY_CHAIN.COST_SHARE AS SUM(COSTSHARE) WITH SYNONYMS=('cost_share','upstream_exposure') COMMENT='Cost share exposure',
        SUPPLY_CHAIN.REVENUE_SHARE AS SUM(REVENUESHARE) WITH SYNONYMS=('revenue_share','downstream_exposure') COMMENT='Revenue share exposure',
        SUPPLY_CHAIN.RELATIONSHIP_COUNT AS COUNT(RELATIONSHIPID) WITH SYNONYMS=('count','connections') COMMENT='Number of relationships'
    )
    COMMENT='Supply chain risk analysis semantic view';

-- SAM_MIDDLE_OFFICE_VIEW - Middle office operations semantic view
CREATE OR REPLACE SEMANTIC VIEW SAM_DEMO.AI.SAM_MIDDLE_OFFICE_VIEW
    TABLES (
        SETTLEMENTS AS SAM_DEMO.CURATED.FACT_TRADE_SETTLEMENT
            PRIMARY KEY (SETTLEMENTID)
            WITH SYNONYMS=('settlements','trades')
            COMMENT='Trade settlement tracking',
        RECONCILIATIONS AS SAM_DEMO.CURATED.FACT_RECONCILIATION
            PRIMARY KEY (RECONCILIATIONID)
            WITH SYNONYMS=('recon','breaks')
            COMMENT='Reconciliation breaks',
        NAV AS SAM_DEMO.CURATED.FACT_NAV_CALCULATION
            PRIMARY KEY (NAVID)
            WITH SYNONYMS=('nav','valuations')
            COMMENT='NAV calculations',
        PORTFOLIOS AS SAM_DEMO.CURATED.DIM_PORTFOLIO
            PRIMARY KEY (PORTFOLIOID)
            WITH SYNONYMS=('funds','portfolios')
            COMMENT='Portfolio information'
    )
    RELATIONSHIPS (
        SETTLEMENTS_TO_PORTFOLIOS AS SETTLEMENTS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
        RECON_TO_PORTFOLIOS AS RECONCILIATIONS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
        NAV_TO_PORTFOLIOS AS NAV(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID)
    )
    DIMENSIONS (
        PORTFOLIOS.PortfolioName AS PORTFOLIONAME WITH SYNONYMS=('fund_name','portfolio') COMMENT='Portfolio name',
        SETTLEMENTS.SettlementStatus AS STATUS WITH SYNONYMS=('settlement_state','trade_status','settlement_status') COMMENT='Settlement status',
        RECONCILIATIONS.BreakType AS BREAKTYPE WITH SYNONYMS=('break_type') COMMENT='Break type',
        RECONCILIATIONS.ReconciliationStatus AS STATUS WITH SYNONYMS=('resolution_status','recon_state','recon_status') COMMENT='Reconciliation status'
    )
    METRICS (
        SETTLEMENTS.SETTLEMENT_VALUE AS SUM(SETTLEMENTVALUE) WITH SYNONYMS=('value') COMMENT='Settlement value',
        SETTLEMENTS.FAILED_COUNT AS COUNT(CASE WHEN STATUS = 'Failed' THEN 1 END) WITH SYNONYMS=('fails','failures') COMMENT='Failed settlements',
        RECONCILIATIONS.BREAK_VALUE AS SUM(DIFFERENCE) WITH SYNONYMS=('break_amount') COMMENT='Break value',
        NAV.NAV_PER_SHARE AS AVG(NAVPERSHARE) WITH SYNONYMS=('nav','unit_value') COMMENT='NAV per share'
    )
    COMMENT='Middle office operations semantic view';

-- ============================================================================
-- SECTION 14: SNOWFLAKE INTELLIGENCE AGENTS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Agent 1: Portfolio Copilot
-- ----------------------------------------------------------------------------
CREATE OR REPLACE AGENT SAM_DEMO.AI.AM_portfolio_copilot
  COMMENT = 'Expert AI assistant for portfolio managers providing instant access to portfolio analytics, holdings analysis, benchmark comparisons, and supporting research.'
  PROFILE = '{"display_name": "Portfolio Co-Pilot (AM Demo)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: "Style: Professional, data-driven, action-oriented for portfolio managers. Lead with portfolio metrics first, then analysis, then recommendations. Use UK English spelling. Format percentages to 1 decimal place, currency to 2 decimal places."
    orchestration: "Tool Selection: Use quantitative_analyzer for portfolio holdings and concentration analysis. Use financial_analyzer for company fundamentals. Use search_broker_research for analyst views. Use search_policies for mandate requirements. Always retrieve policy thresholds before flagging concentration issues."
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "quantitative_analyzer"
        description: "Analyzes portfolio holdings, position weights, sector allocations, and mandate compliance for SAM investment portfolios. Data Coverage: 14,000+ securities, 10 portfolios, 27,000+ holdings. When to Use: Portfolio holdings, weights, concentration analysis, sector allocation."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "financial_analyzer"
        description: "Analyzes company financial health using SEC filing data including revenue, profitability, leverage ratios. When to Use: Company fundamentals, balance sheet analysis, financial metrics."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "implementation_analyzer"
        description: "Analyzes trading costs, market impact, liquidity for execution planning. When to Use: Implementation planning, trading cost analysis."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "supply_chain_analyzer"
        description: "Analyzes supply chain dependencies and indirect portfolio exposures. When to Use: Supply chain risk, second-order effects."
    - tool_spec:
        type: "cortex_search"
        name: "search_broker_research"
        description: "Searches broker research reports for analyst views, ratings, price targets."
    - tool_spec:
        type: "cortex_search"
        name: "search_earnings_transcripts"
        description: "Searches earnings call transcripts for management commentary and guidance."
    - tool_spec:
        type: "cortex_search"
        name: "search_press_releases"
        description: "Searches company press releases for announcements and developments."
    - tool_spec:
        type: "cortex_search"
        name: "search_macro_events"
        description: "Searches macro-economic events and market-moving developments."
    - tool_spec:
        type: "cortex_search"
        name: "search_policies"
        description: "Searches firm investment policies and risk management frameworks."
    - tool_spec:
        type: "cortex_search"
        name: "search_report_templates"
        description: "Searches report templates for investment committee memos."
  tool_resources:
    quantitative_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_ANALYST_VIEW"
    financial_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_SEC_FILINGS_VIEW"
    implementation_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_IMPLEMENTATION_VIEW"
    supply_chain_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_SUPPLY_CHAIN_VIEW"
    search_broker_research:
      search_service: "SAM_DEMO.AI.SAM_BROKER_RESEARCH"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_earnings_transcripts:
      search_service: "SAM_DEMO.AI.SAM_EARNINGS_TRANSCRIPTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_press_releases:
      search_service: "SAM_DEMO.AI.SAM_PRESS_RELEASES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_macro_events:
      search_service: "SAM_DEMO.AI.SAM_MACRO_EVENTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_policies:
      search_service: "SAM_DEMO.AI.SAM_POLICY_DOCS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_report_templates:
      search_service: "SAM_DEMO.AI.SAM_REPORT_TEMPLATES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
  $$;

-- ----------------------------------------------------------------------------
-- Agent 2: Research Copilot
-- ----------------------------------------------------------------------------
CREATE OR REPLACE AGENT SAM_DEMO.AI.AM_research_copilot
  COMMENT = 'Expert research assistant specializing in document analysis, investment research synthesis, and market intelligence.'
  PROFILE = '{"display_name": "Research Co-Pilot (AM Demo)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: "Style: Technical, detail-rich, analytical for research analysts. Lead with financial data first, then qualitative context, then synthesis. Use US financial reporting terms with UK English spelling."
    orchestration: "Tool Selection: Use financial_analyzer for quantitative financial data. Use search_broker_research for analyst views. Use search_earnings_transcripts for management commentary. Use search_press_releases for corporate developments."
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "financial_analyzer"
        description: "Analyzes company financial health using SEC filing data. Data Coverage: 28.7M SEC filing records, 10+ years history."
    - tool_spec:
        type: "cortex_search"
        name: "search_broker_research"
        description: "Searches broker research reports for investment opinions and ratings."
    - tool_spec:
        type: "cortex_search"
        name: "search_earnings_transcripts"
        description: "Searches earnings call transcripts for management guidance."
    - tool_spec:
        type: "cortex_search"
        name: "search_press_releases"
        description: "Searches company press releases for corporate developments."
  tool_resources:
    financial_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_SEC_FILINGS_VIEW"
    search_broker_research:
      search_service: "SAM_DEMO.AI.SAM_BROKER_RESEARCH"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_earnings_transcripts:
      search_service: "SAM_DEMO.AI.SAM_EARNINGS_TRANSCRIPTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_press_releases:
      search_service: "SAM_DEMO.AI.SAM_PRESS_RELEASES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
  $$;

-- ----------------------------------------------------------------------------
-- Agent 3: Thematic Macro Advisor
-- ----------------------------------------------------------------------------
CREATE OR REPLACE AGENT SAM_DEMO.AI.AM_thematic_macro_advisor
  COMMENT = 'Expert thematic investment strategist specializing in macro-economic trends, sectoral themes, and strategic asset allocation.'
  PROFILE = '{"display_name": "Thematic Macro Advisor (AM Demo)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: "Style: Strategic, synthesis-driven, forward-looking for thematic strategists. Lead with thematic thesis first, then validation, then positioning recommendations."
    orchestration: "Tool Selection: Use quantitative_analyzer for portfolio positioning. Use search_broker_research for thematic research. Use search_macro_events for event-driven analysis."
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "quantitative_analyzer"
        description: "Analyzes portfolio positioning and sector exposures for thematic strategy development."
    - tool_spec:
        type: "cortex_search"
        name: "search_broker_research"
        description: "Searches broker research for thematic investment ideas and sector trends."
    - tool_spec:
        type: "cortex_search"
        name: "search_earnings_transcripts"
        description: "Searches earnings transcripts for management commentary on strategic themes."
    - tool_spec:
        type: "cortex_search"
        name: "search_press_releases"
        description: "Searches press releases for strategic initiatives aligned with themes."
    - tool_spec:
        type: "cortex_search"
        name: "search_macro_events"
        description: "Searches macro-economic events that create thematic investment opportunities."
  tool_resources:
    quantitative_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_ANALYST_VIEW"
    search_broker_research:
      search_service: "SAM_DEMO.AI.SAM_BROKER_RESEARCH"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_earnings_transcripts:
      search_service: "SAM_DEMO.AI.SAM_EARNINGS_TRANSCRIPTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_press_releases:
      search_service: "SAM_DEMO.AI.SAM_PRESS_RELEASES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_macro_events:
      search_service: "SAM_DEMO.AI.SAM_MACRO_EVENTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
  $$;

-- ----------------------------------------------------------------------------
-- Agent 4: ESG Guardian
-- ----------------------------------------------------------------------------
CREATE OR REPLACE AGENT SAM_DEMO.AI.AM_esg_guardian
  COMMENT = 'ESG risk monitoring specialist providing comprehensive analysis of environmental, social, and governance factors across portfolio holdings.'
  PROFILE = '{"display_name": "ESG Guardian (AM Demo)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: "Style: Compliance-focused, risk-aware, proactive for ESG oversight. Lead with risk assessment first, then policy validation, then remediation recommendations. Flag controversies with High/Medium/Low severity levels."
    orchestration: "Tool Selection: Use quantitative_analyzer for ESG ratings and portfolio compliance. Use search_ngo_reports for ESG controversies. Use search_engagement_notes for engagement tracking. Use search_policies for ESG requirements."
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "quantitative_analyzer"
        description: "Analyzes portfolio ESG ratings, mandate compliance, and ESG grade distributions."
    - tool_spec:
        type: "cortex_search"
        name: "search_ngo_reports"
        description: "Searches NGO reports for ESG controversies and environmental incidents."
    - tool_spec:
        type: "cortex_search"
        name: "search_engagement_notes"
        description: "Searches ESG engagement meeting notes for stewardship activity."
    - tool_spec:
        type: "cortex_search"
        name: "search_policies"
        description: "Searches firm ESG policies and sustainable investment criteria."
    - tool_spec:
        type: "cortex_search"
        name: "search_press_releases"
        description: "Searches company press releases for ESG announcements."
    - tool_spec:
        type: "cortex_search"
        name: "search_earnings_transcripts"
        description: "Searches earnings transcripts for management ESG commentary."
  tool_resources:
    quantitative_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_ANALYST_VIEW"
    search_ngo_reports:
      search_service: "SAM_DEMO.AI.SAM_NGO_REPORTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_engagement_notes:
      search_service: "SAM_DEMO.AI.SAM_ENGAGEMENT_NOTES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_policies:
      search_service: "SAM_DEMO.AI.SAM_POLICY_DOCS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_press_releases:
      search_service: "SAM_DEMO.AI.SAM_PRESS_RELEASES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_earnings_transcripts:
      search_service: "SAM_DEMO.AI.SAM_EARNINGS_TRANSCRIPTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
  $$;

-- ----------------------------------------------------------------------------
-- Agent 5: Compliance Advisor
-- ----------------------------------------------------------------------------
CREATE OR REPLACE AGENT SAM_DEMO.AI.AM_compliance_advisor
  COMMENT = 'Compliance monitoring specialist ensuring portfolio mandate adherence and regulatory compliance.'
  PROFILE = '{"display_name": "Compliance Advisor (AM Demo)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: "Style: Regulatory-focused, precise, action-oriented for compliance teams. Lead with compliance status first, then breach details, then remediation requirements. Flag breaches >7% with BREACH and warnings >6.5% with WARNING."
    orchestration: "Tool Selection: Use quantitative_analyzer for compliance checks. Use search_policies for policy limits. Use search_engagement_notes for engagement tracking."
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "quantitative_analyzer"
        description: "Analyzes portfolio mandate compliance including concentration limits and ESG requirements."
    - tool_spec:
        type: "cortex_search"
        name: "search_policies"
        description: "Searches investment policy documents for mandate requirements and thresholds."
    - tool_spec:
        type: "cortex_search"
        name: "search_engagement_notes"
        description: "Searches engagement notes for compliance breach remediation tracking."
  tool_resources:
    quantitative_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_ANALYST_VIEW"
    search_policies:
      search_service: "SAM_DEMO.AI.SAM_POLICY_DOCS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_engagement_notes:
      search_service: "SAM_DEMO.AI.SAM_ENGAGEMENT_NOTES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
  $$;

-- ----------------------------------------------------------------------------
-- Agent 6: Sales Advisor
-- ----------------------------------------------------------------------------
CREATE OR REPLACE AGENT SAM_DEMO.AI.AM_sales_advisor
  COMMENT = 'Client reporting specialist creating professional investment reports and communications.'
  PROFILE = '{"display_name": "Sales Advisor (AM Demo)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: "Style: Client-friendly, professional, accessible language for investors. Lead with performance summary first, then attribution, then market commentary. Follow SAM brand guidelines."
    orchestration: "Tool Selection: Use quantitative_analyzer for performance data. Use search_sales_templates for report templates. Use search_philosophy_docs for investment philosophy. Use search_policies for policy explanations."
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "quantitative_analyzer"
        description: "Analyzes portfolio performance, holdings, and sector allocation for client reporting."
    - tool_spec:
        type: "cortex_search"
        name: "search_sales_templates"
        description: "Searches client report templates and formatting guidelines."
    - tool_spec:
        type: "cortex_search"
        name: "search_philosophy_docs"
        description: "Searches investment philosophy documents for client education."
    - tool_spec:
        type: "cortex_search"
        name: "search_policies"
        description: "Searches investment policies for client-facing explanations."
  tool_resources:
    quantitative_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_ANALYST_VIEW"
    search_sales_templates:
      search_service: "SAM_DEMO.AI.SAM_SALES_TEMPLATES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_philosophy_docs:
      search_service: "SAM_DEMO.AI.SAM_PHILOSOPHY_DOCS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_policies:
      search_service: "SAM_DEMO.AI.SAM_POLICY_DOCS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
  $$;

-- ----------------------------------------------------------------------------
-- Agent 7: Quant Analyst
-- ----------------------------------------------------------------------------
CREATE OR REPLACE AGENT SAM_DEMO.AI.AM_quant_analyst
  COMMENT = 'Quantitative analysis specialist providing advanced portfolio analytics including factor exposures, performance attribution, and risk decomposition.'
  PROFILE = '{"display_name": "Quant Analyst (AM Demo)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: "Style: Technical, quantitative, precise for quantitative analysts. Lead with statistical metrics first, then factor analysis, then risk decomposition. Include confidence intervals and factor loadings to 3 decimal places."
    orchestration: "Tool Selection: Use quantitative_analyzer for factor exposures and portfolio analytics. Use financial_analyzer for fundamental validation. Use search_broker_research for factor regime context."
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "quantitative_analyzer"
        description: "Analyzes portfolio factor exposures using 7 systematic factors (Market, Size, Value, Growth, Momentum, Quality, Volatility). Data Coverage: 14,000+ securities, 5 years monthly factor data."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "financial_analyzer"
        description: "Validates factor-based selections using SEC filing financial data."
    - tool_spec:
        type: "cortex_search"
        name: "search_broker_research"
        description: "Searches broker research for analyst views on systematic factor strategies."
    - tool_spec:
        type: "cortex_search"
        name: "search_earnings_transcripts"
        description: "Searches earnings transcripts for management commentary supporting factor analysis."
  tool_resources:
    quantitative_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_QUANT_VIEW"
    financial_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_SEC_FILINGS_VIEW"
    search_broker_research:
      search_service: "SAM_DEMO.AI.SAM_BROKER_RESEARCH"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_earnings_transcripts:
      search_service: "SAM_DEMO.AI.SAM_EARNINGS_TRANSCRIPTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
  $$;

-- ----------------------------------------------------------------------------
-- Agent 8: Middle Office Copilot
-- ----------------------------------------------------------------------------
CREATE OR REPLACE AGENT SAM_DEMO.AI.AM_middle_office_copilot
  COMMENT = 'Middle office operations specialist monitoring trade settlements, reconciliations, NAV calculations, and cash management.'
  PROFILE = '{"display_name": "Middle Office Co-Pilot (AM Demo)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: "Style: Operational, precise, action-oriented for middle office operations. Lead with exception status first, then root cause analysis, then remediation actions. Use status flags: FAILED, PENDING, SETTLED, INVESTIGATING."
    orchestration: "Tool Selection: Use middle_office_analyzer for settlement status, reconciliation breaks, NAV calculations. Use search_custodian_reports for custodian communications. Use search_reconciliation_notes for past break resolutions. Use search_ssi_documents for settlement instructions. Use search_ops_procedures for operational procedures."
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "middle_office_analyzer"
        description: "Analyzes middle office operations data including trade settlements, reconciliation breaks, NAV calculations, and cash management."
    - tool_spec:
        type: "cortex_search"
        name: "search_custodian_reports"
        description: "Searches custodian reports for operational issues and settlement delays."
    - tool_spec:
        type: "cortex_search"
        name: "search_reconciliation_notes"
        description: "Searches historical reconciliation investigation notes and break resolutions."
    - tool_spec:
        type: "cortex_search"
        name: "search_ssi_documents"
        description: "Searches Standard Settlement Instructions database for counterparty settlement details."
    - tool_spec:
        type: "cortex_search"
        name: "search_ops_procedures"
        description: "Searches middle office operational procedures and escalation protocols."
  tool_resources:
    middle_office_analyzer:
      execution_environment:
        query_timeout: 30
        type: "warehouse"
        warehouse: "SAM_DEMO_EXECUTION_WH"
      semantic_view: "SAM_DEMO.AI.SAM_MIDDLE_OFFICE_VIEW"
    search_custodian_reports:
      search_service: "SAM_DEMO.AI.SAM_CUSTODIAN_REPORTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_reconciliation_notes:
      search_service: "SAM_DEMO.AI.SAM_RECONCILIATION_NOTES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_ssi_documents:
      search_service: "SAM_DEMO.AI.SAM_SSI_DOCUMENTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
    search_ops_procedures:
      search_service: "SAM_DEMO.AI.SAM_OPS_PROCEDURES"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 4
  $$;

-- ============================================================================
-- SECTION 15: REGISTER AGENTS WITH SNOWFLAKE INTELLIGENCE
-- ============================================================================

-- Register all agents with Snowflake Intelligence
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT SAM_DEMO.AI.AM_portfolio_copilot;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT SAM_DEMO.AI.AM_research_copilot;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT SAM_DEMO.AI.AM_thematic_macro_advisor;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT SAM_DEMO.AI.AM_esg_guardian;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT SAM_DEMO.AI.AM_compliance_advisor;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT SAM_DEMO.AI.AM_sales_advisor;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT SAM_DEMO.AI.AM_quant_analyst;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT SAM_DEMO.AI.AM_middle_office_copilot;

-- ============================================================================
-- SECTION 16: FINAL GRANTS AND VERIFICATION
-- ============================================================================

-- Grant access to all agents
GRANT USAGE ON AGENT SAM_DEMO.AI.AM_portfolio_copilot TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON AGENT SAM_DEMO.AI.AM_research_copilot TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON AGENT SAM_DEMO.AI.AM_thematic_macro_advisor TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON AGENT SAM_DEMO.AI.AM_esg_guardian TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON AGENT SAM_DEMO.AI.AM_compliance_advisor TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON AGENT SAM_DEMO.AI.AM_sales_advisor TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON AGENT SAM_DEMO.AI.AM_quant_analyst TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON AGENT SAM_DEMO.AI.AM_middle_office_copilot TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SETUP COMPLETE!
-- ============================================================================
--
-- COMPONENTS CREATED:
--   ✅ 8 AI Agents (AM_portfolio_copilot, AM_research_copilot, AM_thematic_macro_advisor,
--                   AM_esg_guardian, AM_compliance_advisor, AM_sales_advisor, 
--                   AM_quant_analyst, AM_middle_office_copilot)
--   ✅ 7 Semantic Views (SAM_ANALYST_VIEW, SAM_SEC_FILINGS_VIEW, SAM_RESEARCH_VIEW,
--                        SAM_QUANT_VIEW, SAM_IMPLEMENTATION_VIEW, SAM_SUPPLY_CHAIN_VIEW,
--                        SAM_MIDDLE_OFFICE_VIEW)
--   ✅ 16 Cortex Search Services (SAM_BROKER_RESEARCH, SAM_EARNINGS_TRANSCRIPTS, 
--                                 SAM_PRESS_RELEASES, SAM_MACRO_EVENTS, SAM_POLICY_DOCS,
--                                 SAM_NGO_REPORTS, SAM_ENGAGEMENT_NOTES, SAM_SALES_TEMPLATES,
--                                 SAM_PHILOSOPHY_DOCS, SAM_REPORT_TEMPLATES, SAM_INTERNAL_RESEARCH,
--                                 SAM_INVESTMENT_MEMOS, SAM_CUSTODIAN_REPORTS, 
--                                 SAM_RECONCILIATION_NOTES, SAM_SSI_DOCUMENTS, SAM_OPS_PROCEDURES)
--
-- NEXT STEPS:
--   1. Open Snowflake UI
--   2. Navigate to "Snowflake Intelligence"
--   3. Select any of the 8 agents
--   4. Try your first query: "What are my top 10 holdings in SAM Technology & Infrastructure?"
--
-- ============================================================================
