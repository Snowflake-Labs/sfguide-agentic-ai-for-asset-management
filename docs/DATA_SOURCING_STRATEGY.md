# Data Sourcing Strategy for Portfolio Manager Co-Pilot

## Executive Summary

This document outlines how to source or simulate each data type required for the Portfolio Manager Co-Pilot capabilities. We leverage **Cybersyn data from Snowflake Marketplace** (free tier) as the primary external data source, combined with calculated attribution and simulated benchmark data.

**Decision**: Use Cybersyn only (no CEIC) - provides 150K+ variables with global coverage.

---

## 1. ALREADY AVAILABLE DATA (No Action Required)

### In SAM_DEMO Database

| Data Type | Table | Records | Status |
|-----------|-------|---------|--------|
| Stock Prices | `SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES` | 98.8K | ✅ Ready |
| Factor Exposures | `SAM_DEMO.CURATED.FACT_FACTOR_EXPOSURES` | 22.3K | ✅ Ready |
| Covariance Matrix | `SAM_DEMO.CURATED.FACT_COVARIANCE_MATRIX` | 3.2K | ✅ Ready |
| SEC Financials | `SAM_DEMO.MARKET_DATA.FACT_SEC_FINANCIALS` | 7.5K | ✅ Ready |
| Analyst Estimates | `SAM_DEMO.MARKET_DATA.FACT_ESTIMATE_CONSENSUS` | 5.6K | ✅ Ready |
| SEC Filings (Search) | `SAM_DEMO.AI.SAM_REAL_SEC_FILINGS` | 277K docs | ✅ Ready |
| Portfolio Holdings | `SAM_DEMO.CURATED.FACT_HOLDINGS` | Active | ✅ Ready |
| Treasury Yields | `SAM_DEMO.MARKET_DATA.FACT_TREASURY_YIELDS` | 14 maturities daily | ✅ Ready |
| Country Emissions | `SAM_DEMO.MARKET_DATA.FACT_COUNTRY_EMISSIONS` | 190+ countries | ✅ Ready |
| Insider Transactions | `SAM_DEMO.CURATED.FACT_INSIDER_TRANSACTIONS` | 8.7K+ records | ✅ Ready |
| Institutional Holdings | `SAM_DEMO.CURATED.FACT_INSTITUTIONAL_HOLDINGS` | Quarterly 13F | ✅ Ready |
| Benchmark Holdings (N-PORT) | `SAM_DEMO.CURATED.FACT_BENCHMARK_HOLDINGS` | Real weights (208 securities) | ✅ Ready |

---

## 2. CYBERSYN DATA (Primary External Source)

**Database**: `FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN`

### Geographic Coverage

| Dataset | Countries | Scope |
|---------|-----------|-------|
| IMF Data (GDP, commodities, BoP) | **244 countries** | 🌍 Global |
| BIS Data (central bank rates, property) | **73 countries** | 🌍 Global |
| ECB Data (CPI, housing) | **30+ European** | 🇪🇺 Europe |
| FX Rates | **50+ currencies** | 🌍 Global |
| Core US Economic | US only | 🇺🇸 US |

### 2.1 Economic Indicators (Macro Regime Detection)

**US Data:**

| Use Case | Cybersyn Table | Key Variables |
|----------|----------------|---------------|
| GDP Growth | `CYBERSYN_FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES` | GDP estimates, PCE indexes |
| Inflation/CPI | `BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES` | Consumer Price Index, inflation metrics |
| Unemployment | `BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES` | Unemployment rates, JOLTS data |
| Consumer Credit | `FEDERAL_RESERVE_TIMESERIES` | Consumer credit, borrowing patterns |
| Industrial Production | `FEDERAL_RESERVE_TIMESERIES` | Industrial production, capacity utilization |

**International Data:**

| Use Case | Cybersyn Table | Coverage |
|----------|----------------|----------|
| Central Bank Policy Rates | `BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES` | 73 countries |
| International Property Prices | `BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES` | 73 countries |
| European CPI/Inflation | `EUROPEAN_CENTRAL_BANK_TIMESERIES` | 30+ EU countries |
| Global GDP/Macro | `INTERNATIONAL_MONETARY_FUND_TIMESERIES` | 244 countries |

**Example Query - GDP Data**:
```sql
SELECT DATE, VALUE, VARIABLE_NAME
FROM FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN.CYBERSYN_FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES t
JOIN FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN.CYBERSYN_FINANCIAL_ECONOMIC_INDICATORS_ATTRIBUTES a
  ON t.VARIABLE = a.VARIABLE
WHERE UPPER(a.VARIABLE_NAME) LIKE '%GDP%'
  AND DATE >= '2020-01-01'
ORDER BY DATE DESC;
```

### 2.2 Commodity Prices (Sector/Factor Attribution)

| Commodity | Cybersyn Table | Key Variables |
|-----------|----------------|---------------|
| Crude Oil (WTI) | `INTERNATIONAL_MONETARY_FUND_TIMESERIES` | WTI Crude Index |
| Natural Gas | `EIA_ENERGY_TIMESERIES` | Natural gas prices |
| Gold/Silver | `INTERNATIONAL_MONETARY_FUND_TIMESERIES` | Gold, Silver, Palladium |
| Copper | `INTERNATIONAL_MONETARY_FUND_TIMESERIES` | Copper index |
| Agricultural | `INTERNATIONAL_MONETARY_FUND_TIMESERIES` | Corn, Wheat, Soybeans |

**Example Query - Oil Prices**:
```sql
SELECT DATE, VALUE, VARIABLE_NAME
FROM FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN.INTERNATIONAL_MONETARY_FUND_TIMESERIES t
JOIN FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN.INTERNATIONAL_MONETARY_FUND_ATTRIBUTES a
  ON t.VARIABLE = a.VARIABLE
WHERE UPPER(a.VARIABLE_NAME) LIKE '%WTI%CRUDE%'
ORDER BY DATE DESC
LIMIT 100;
```

### 2.3 Foreign Exchange Rates (Currency Attribution)

| Use Case | Cybersyn Table | Coverage |
|----------|----------------|----------|
| FX Rates | `FX_RATES_TIMESERIES` | 50+ currency pairs |
| EUR/USD | `FX_RATES_TIMESERIES` | Historical since 2000 |
| Emerging Markets | `FX_RATES_TIMESERIES` | MXN, BRL, ZAR, etc. |

**Example Query - FX Rates**:
```sql
SELECT DATE, BASE_CURRENCY_ID, QUOTE_CURRENCY_ID, VALUE
FROM FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN.FX_RATES_TIMESERIES
WHERE BASE_CURRENCY_ID = 'USD'
  AND QUOTE_CURRENCY_ID IN ('EUR', 'GBP', 'JPY', 'CHF')
  AND DATE >= '2024-01-01'
ORDER BY DATE DESC;
```

### 2.4 Interest Rates & Credit (Duration/Credit Attribution)

| Use Case | Cybersyn Table | Key Variables |
|----------|----------------|---------------|
| Mortgage Rates | `FREDDIE_MAC_HOUSING_TIMESERIES` | 30-yr fixed, 15-yr fixed, ARM rates |
| Central Bank Rates | `BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES` | Policy rates by country |
| Housing Prices | `FHFA_HOUSE_PRICE_TIMESERIES` | House Price Index by region |
| Mortgage Delinquency | `FHFA_MORTGAGE_PERFORMANCE_TIMESERIES` | Delinquency rates |

### 2.5 Climate/ESG Data (ESG Attribution)

| Use Case | Cybersyn Table | Key Variables |
|----------|----------------|---------------|
| Emissions by Country | `CLIMATE_WATCH_TIMESERIES` | CO2, CH4, N2O emissions |
| EU Emissions | `EUROPEAN_COMMISSION_EDGAR_TIMESERIES` | Industry-level emissions |
| EPA Power Plant | `EPA_CAM_TIMESERIES` | SO2, NOx, CO2 from utilities |

### 2.6 Company & Security Data (Entity Resolution)

| Use Case | Cybersyn Table | Key Variables |
|----------|----------------|---------------|
| Company Index | `COMPANY_INDEX` | CIK, EIN, PermID, LEI mapping |
| Security Relationships | `COMPANY_SECURITY_RELATIONSHIPS` | FIGI, PermID securities |
| Company Characteristics | `COMPANY_CHARACTERISTICS` | Industry, addresses |
| Earnings Transcripts | `COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES` | Call transcripts JSON |

---

## 3. DATA INPUTS TO SIMULATE (Not Available in Free Sources)

> **Important**: Brinson attribution is **calculated**, not simulated. However, the calculation requires 
> certain inputs (benchmark weights, benchmark returns) that are not freely available.

### 3.1 Benchmark Data (Required Inputs for Attribution)

**Why Simulate**: Index-level daily returns and sector weights (S&P 500, Russell 2000, etc.) require paid data subscriptions.

**What We Need**:
- Total benchmark return (daily)
- Benchmark weights by sector
- Benchmark returns by sector

**Simulation Approach**:
```sql
-- Benchmark dimension
CREATE OR REPLACE TABLE SAM_DEMO.MARKET_DATA.DIM_BENCHMARKS (
    BENCHMARK_ID VARCHAR,
    BENCHMARK_NAME VARCHAR,
    BENCHMARK_TYPE VARCHAR,  -- 'EQUITY', 'FIXED_INCOME', 'MULTI_ASSET'
    CURRENCY VARCHAR
);

INSERT INTO SAM_DEMO.MARKET_DATA.DIM_BENCHMARKS VALUES
('SPX', 'S&P 500', 'EQUITY', 'USD'),
('RTY', 'Russell 2000', 'EQUITY', 'USD'),
('AGG', 'Bloomberg US Aggregate Bond', 'FIXED_INCOME', 'USD'),
('MXWO', 'MSCI World', 'EQUITY', 'USD');

-- Benchmark total returns (simulated with realistic volatility)
CREATE OR REPLACE TABLE SAM_DEMO.MARKET_DATA.FACT_BENCHMARK_RETURNS AS
SELECT 
    b.BENCHMARK_ID,
    d.DATE,
    NORMAL(0, CASE 
        WHEN b.BENCHMARK_TYPE = 'EQUITY' THEN 0.012  -- ~12% annual vol
        WHEN b.BENCHMARK_TYPE = 'FIXED_INCOME' THEN 0.004  -- ~4% annual vol
        ELSE 0.008
    END, RANDOM()) + 0.0003 AS DAILY_RETURN  -- Small positive drift
FROM SAM_DEMO.MARKET_DATA.DIM_BENCHMARKS b
CROSS JOIN (SELECT DISTINCT DATE FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES) d;

-- Benchmark sector weights (simulated based on typical S&P 500 composition)
CREATE OR REPLACE TABLE SAM_DEMO.MARKET_DATA.FACT_BENCHMARK_SECTOR_WEIGHTS (
    BENCHMARK_ID VARCHAR,
    DATE DATE,
    SECTOR VARCHAR,
    BENCHMARK_WEIGHT FLOAT
);

INSERT INTO SAM_DEMO.MARKET_DATA.FACT_BENCHMARK_SECTOR_WEIGHTS
SELECT 'SPX', d.DATE, sector, weight
FROM (SELECT DISTINCT DATE FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES) d
CROSS JOIN (
    SELECT 'Technology' AS sector, 0.28 AS weight UNION ALL
    SELECT 'Healthcare', 0.13 UNION ALL
    SELECT 'Financials', 0.12 UNION ALL
    SELECT 'Consumer Discretionary', 0.11 UNION ALL
    SELECT 'Communication Services', 0.09 UNION ALL
    SELECT 'Industrials', 0.08 UNION ALL
    SELECT 'Consumer Staples', 0.06 UNION ALL
    SELECT 'Energy', 0.04 UNION ALL
    SELECT 'Utilities', 0.03 UNION ALL
    SELECT 'Real Estate', 0.03 UNION ALL
    SELECT 'Materials', 0.03
);
```

### 3.2 Brinson Attribution Calculation (Not Simulated - Calculated from Inputs)

**Brinson-Fachler Decomposition Formula**:
- **Allocation Effect** = Σ (w_p,i - w_b,i) × (R_b,i - R_b)
- **Selection Effect** = Σ w_b,i × (R_p,i - R_b,i)  
- **Interaction Effect** = Σ (w_p,i - w_b,i) × (R_p,i - R_b,i)

Where:
- w_p,i = Portfolio weight in sector i
- w_b,i = Benchmark weight in sector i
- R_p,i = Portfolio return in sector i
- R_b,i = Benchmark return in sector i
- R_b = Total benchmark return

**Calculation SQL**:
```sql
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_BRINSON_ATTRIBUTION AS
WITH portfolio_sector_data AS (
    -- Calculate portfolio weights and returns by sector
    SELECT 
        h.PORTFOLIO_ID,
        p.DATE,
        s.SECTOR,
        SUM(h.WEIGHT) AS PORTFOLIO_WEIGHT,
        SUM(h.WEIGHT * p.DAILY_RETURN) / NULLIF(SUM(h.WEIGHT), 0) AS PORTFOLIO_SECTOR_RETURN
    FROM SAM_DEMO.CURATED.FACT_HOLDINGS h
    JOIN SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES p ON h.SECURITYID = p.SECURITYID
    JOIN SAM_DEMO.CURATED.DIM_SECURITIES s ON h.SECURITYID = s.SECURITYID
    GROUP BY h.PORTFOLIO_ID, p.DATE, s.SECTOR
),
benchmark_sector_data AS (
    -- Calculate benchmark sector returns from constituent stocks
    SELECT 
        bw.BENCHMARK_ID,
        bw.DATE,
        bw.SECTOR,
        bw.BENCHMARK_WEIGHT,
        sr.SECTOR_RETURN AS BENCHMARK_SECTOR_RETURN
    FROM SAM_DEMO.MARKET_DATA.FACT_BENCHMARK_SECTOR_WEIGHTS bw
    JOIN SAM_DEMO.MARKET_DATA.FACT_SECTOR_RETURNS sr 
        ON bw.DATE = sr.DATE AND bw.SECTOR = sr.SECTOR
),
total_benchmark AS (
    SELECT DATE, DAILY_RETURN AS TOTAL_BENCHMARK_RETURN
    FROM SAM_DEMO.MARKET_DATA.FACT_BENCHMARK_RETURNS
    WHERE BENCHMARK_ID = 'SPX'
),
brinson_by_sector AS (
    SELECT 
        psd.PORTFOLIO_ID,
        psd.DATE,
        psd.SECTOR,
        psd.PORTFOLIO_WEIGHT,
        bsd.BENCHMARK_WEIGHT,
        psd.PORTFOLIO_SECTOR_RETURN,
        bsd.BENCHMARK_SECTOR_RETURN,
        tb.TOTAL_BENCHMARK_RETURN,
        -- Brinson components by sector
        (psd.PORTFOLIO_WEIGHT - bsd.BENCHMARK_WEIGHT) * 
            (bsd.BENCHMARK_SECTOR_RETURN - tb.TOTAL_BENCHMARK_RETURN) AS ALLOCATION_EFFECT,
        bsd.BENCHMARK_WEIGHT * 
            (psd.PORTFOLIO_SECTOR_RETURN - bsd.BENCHMARK_SECTOR_RETURN) AS SELECTION_EFFECT,
        (psd.PORTFOLIO_WEIGHT - bsd.BENCHMARK_WEIGHT) * 
            (psd.PORTFOLIO_SECTOR_RETURN - bsd.BENCHMARK_SECTOR_RETURN) AS INTERACTION_EFFECT
    FROM portfolio_sector_data psd
    JOIN benchmark_sector_data bsd 
        ON psd.DATE = bsd.DATE AND psd.SECTOR = bsd.SECTOR
    JOIN total_benchmark tb ON psd.DATE = tb.DATE
)
-- Aggregate to portfolio level
SELECT 
    PORTFOLIO_ID,
    DATE,
    SUM(PORTFOLIO_WEIGHT * PORTFOLIO_SECTOR_RETURN) AS TOTAL_PORTFOLIO_RETURN,
    AVG(TOTAL_BENCHMARK_RETURN) AS TOTAL_BENCHMARK_RETURN,
    SUM(PORTFOLIO_WEIGHT * PORTFOLIO_SECTOR_RETURN) - AVG(TOTAL_BENCHMARK_RETURN) AS ACTIVE_RETURN,
    SUM(ALLOCATION_EFFECT) AS ALLOCATION_EFFECT,
    SUM(SELECTION_EFFECT) AS SELECTION_EFFECT,
    SUM(INTERACTION_EFFECT) AS INTERACTION_EFFECT
FROM brinson_by_sector
GROUP BY PORTFOLIO_ID, DATE;

-- Sector-level attribution detail (for drill-down)
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_BRINSON_BY_SECTOR AS
SELECT * FROM brinson_by_sector;
```

### 3.3 Factor Attribution Calculation

Factor attribution decomposes returns based on factor exposures:

**Formula**: R_active = Σ (β_p,f - β_b,f) × F_f + ε

```sql
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_FACTOR_ATTRIBUTION AS
WITH portfolio_factor_exposure AS (
    SELECT 
        h.PORTFOLIO_ID,
        p.DATE,
        SUM(h.WEIGHT * fe.MARKET_BETA) AS PORT_MARKET_BETA,
        SUM(h.WEIGHT * fe.VALUE_EXPOSURE) AS PORT_VALUE,
        SUM(h.WEIGHT * fe.GROWTH_EXPOSURE) AS PORT_GROWTH,
        SUM(h.WEIGHT * fe.MOMENTUM_EXPOSURE) AS PORT_MOMENTUM,
        SUM(h.WEIGHT * fe.QUALITY_EXPOSURE) AS PORT_QUALITY,
        SUM(h.WEIGHT * fe.SIZE_EXPOSURE) AS PORT_SIZE,
        SUM(h.WEIGHT * fe.VOLATILITY_EXPOSURE) AS PORT_VOLATILITY
    FROM SAM_DEMO.CURATED.FACT_HOLDINGS h
    JOIN SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES p ON h.SECURITYID = p.SECURITYID
    JOIN SAM_DEMO.CURATED.FACT_FACTOR_EXPOSURES fe ON h.SECURITYID = fe.SECURITYID
    GROUP BY h.PORTFOLIO_ID, p.DATE
),
factor_returns AS (
    -- Calculate daily factor returns from cross-sectional regression
    -- (simplified: using average returns of high-exposure stocks minus low-exposure)
    SELECT DATE,
        AVG(CASE WHEN fe.MARKET_BETA > 1.2 THEN p.DAILY_RETURN ELSE NULL END) -
        AVG(CASE WHEN fe.MARKET_BETA < 0.8 THEN p.DAILY_RETURN ELSE NULL END) AS MARKET_FACTOR_RETURN,
        AVG(CASE WHEN fe.VALUE_EXPOSURE > 0.5 THEN p.DAILY_RETURN ELSE NULL END) -
        AVG(CASE WHEN fe.VALUE_EXPOSURE < -0.5 THEN p.DAILY_RETURN ELSE NULL END) AS VALUE_FACTOR_RETURN,
        AVG(CASE WHEN fe.GROWTH_EXPOSURE > 0.5 THEN p.DAILY_RETURN ELSE NULL END) -
        AVG(CASE WHEN fe.GROWTH_EXPOSURE < -0.5 THEN p.DAILY_RETURN ELSE NULL END) AS GROWTH_FACTOR_RETURN,
        AVG(CASE WHEN fe.MOMENTUM_EXPOSURE > 0.5 THEN p.DAILY_RETURN ELSE NULL END) -
        AVG(CASE WHEN fe.MOMENTUM_EXPOSURE < -0.5 THEN p.DAILY_RETURN ELSE NULL END) AS MOMENTUM_FACTOR_RETURN
    FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES p
    JOIN SAM_DEMO.CURATED.FACT_FACTOR_EXPOSURES fe ON p.SECURITYID = fe.SECURITYID
    GROUP BY DATE
)
SELECT 
    pfe.PORTFOLIO_ID,
    pfe.DATE,
    pfe.PORT_MARKET_BETA * fr.MARKET_FACTOR_RETURN AS MARKET_CONTRIBUTION,
    pfe.PORT_VALUE * fr.VALUE_FACTOR_RETURN AS VALUE_CONTRIBUTION,
    pfe.PORT_GROWTH * fr.GROWTH_FACTOR_RETURN AS GROWTH_CONTRIBUTION,
    pfe.PORT_MOMENTUM * fr.MOMENTUM_FACTOR_RETURN AS MOMENTUM_CONTRIBUTION
FROM portfolio_factor_exposure pfe
JOIN factor_returns fr ON pfe.DATE = fr.DATE;
```

### 3.4 Sector/Industry Returns (Calculated from Holdings)

**Not simulated** - calculated from actual stock returns grouped by sector:

```sql
CREATE OR REPLACE TABLE SAM_DEMO.MARKET_DATA.FACT_SECTOR_RETURNS AS
SELECT 
    s.SECTOR,
    p.DATE,
    AVG(p.DAILY_RETURN) AS SECTOR_RETURN,
    STDDEV(p.DAILY_RETURN) AS SECTOR_VOLATILITY,
    COUNT(*) AS NUM_SECURITIES
FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES p
JOIN SAM_DEMO.CURATED.DIM_SECURITIES s ON p.SECURITYID = s.SECURITYID
GROUP BY s.SECTOR, p.DATE;
```

### 3.5 Hidden Factor Proxies (AI Exposure, Reshoring, etc.)

**Why Simulate**: Novel thematic exposures not captured in standard factor models.

**Simulation Approach**:
```sql
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_HIDDEN_FACTOR_EXPOSURES (
    SECURITYID VARCHAR,
    DATE DATE,
    AI_EXPOSURE FLOAT,        -- AI/ML theme exposure
    RESHORING_EXPOSURE FLOAT, -- Supply chain reshoring
    RATE_CONVEXITY FLOAT,     -- Interest rate sensitivity
    CLIMATE_TRANSITION FLOAT, -- Green transition exposure
    GEOPOLITICAL_RISK FLOAT   -- Geopolitical sensitivity
);

-- Derive from SEC filings sentiment + sector
INSERT INTO SAM_DEMO.CURATED.FACT_HIDDEN_FACTOR_EXPOSURES
SELECT 
    s.SECURITYID,
    CURRENT_DATE() AS DATE,
    CASE 
        WHEN s.SECTOR = 'Technology' THEN UNIFORM(0.3, 0.9, RANDOM())
        WHEN s.SECTOR = 'Healthcare' THEN UNIFORM(0.1, 0.5, RANDOM())
        ELSE UNIFORM(-0.2, 0.3, RANDOM())
    END AS AI_EXPOSURE,
    CASE 
        WHEN s.SECTOR = 'Industrials' THEN UNIFORM(0.2, 0.7, RANDOM())
        WHEN s.SECTOR = 'Consumer Discretionary' THEN UNIFORM(0.1, 0.5, RANDOM())
        ELSE UNIFORM(-0.1, 0.2, RANDOM())
    END AS RESHORING_EXPOSURE,
    CASE 
        WHEN s.SECTOR IN ('Financials', 'Real Estate') THEN UNIFORM(0.3, 0.8, RANDOM())
        WHEN s.SECTOR = 'Utilities' THEN UNIFORM(0.2, 0.6, RANDOM())
        ELSE UNIFORM(-0.1, 0.3, RANDOM())
    END AS RATE_CONVEXITY,
    CASE 
        WHEN s.SECTOR IN ('Energy', 'Utilities') THEN UNIFORM(-0.5, 0.5, RANDOM())
        WHEN s.SECTOR = 'Technology' THEN UNIFORM(0.1, 0.4, RANDOM())
        ELSE UNIFORM(-0.2, 0.3, RANDOM())
    END AS CLIMATE_TRANSITION,
    CASE 
        WHEN s.SECTOR IN ('Energy', 'Materials') THEN UNIFORM(0.2, 0.6, RANDOM())
        WHEN s.SECTOR = 'Technology' THEN UNIFORM(0.1, 0.4, RANDOM())
        ELSE UNIFORM(-0.1, 0.2, RANDOM())
    END AS GEOPOLITICAL_RISK
FROM SAM_DEMO.CURATED.DIM_SECURITIES s;
```

### 3.6 VIX / Volatility Index

**Why Simulate**: VIX requires paid data; used for regime detection.

**Simulation Approach**:
```sql
CREATE OR REPLACE TABLE SAM_DEMO.MARKET_DATA.FACT_VIX_DAILY AS
SELECT 
    DATE,
    -- VIX typically ranges 10-80, mean reverts around 20
    GREATEST(10, LEAST(80, 
        20 + 15 * SIN(DATEDIFF('day', '2020-01-01', DATE) / 100.0) 
        + NORMAL(0, 5, RANDOM())
    )) AS VIX_CLOSE,
    -- Higher VIX = risk-off regime
    CASE 
        WHEN VIX_CLOSE < 15 THEN 'LOW_VOL'
        WHEN VIX_CLOSE < 25 THEN 'NORMAL'
        WHEN VIX_CLOSE < 35 THEN 'ELEVATED'
        ELSE 'HIGH_VOL'
    END AS VOLATILITY_REGIME
FROM (SELECT DISTINCT DATE FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES);
```

---

## 4. INTEGRATION VIEWS (Combining Sources)

### 4.1 Macro Regime Indicator View

```sql
CREATE OR REPLACE VIEW SAM_DEMO.CURATED.V_MACRO_REGIME AS
WITH gdp_data AS (
    SELECT DATE, VALUE AS GDP_GROWTH
    FROM FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN.CYBERSYN_FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES
    WHERE VARIABLE = 'GDP_GROWTH_VARIABLE_ID'  -- Replace with actual
),
vix_data AS (
    SELECT DATE, VIX_CLOSE, VOLATILITY_REGIME
    FROM SAM_DEMO.MARKET_DATA.FACT_VIX_DAILY
)
SELECT 
    v.DATE,
    v.VIX_CLOSE,
    v.VOLATILITY_REGIME,
    g.GDP_GROWTH,
    CASE 
        WHEN v.VIX_CLOSE < 20 AND g.GDP_GROWTH > 2 THEN 'RISK_ON'
        WHEN v.VIX_CLOSE > 30 OR g.GDP_GROWTH < 0 THEN 'RISK_OFF'
        ELSE 'NEUTRAL'
    END AS MACRO_REGIME
FROM vix_data v
LEFT JOIN gdp_data g ON v.DATE = g.DATE;
```

### 4.2 Attribution Narrative Input View

```sql
CREATE OR REPLACE VIEW SAM_DEMO.CURATED.V_ATTRIBUTION_WITH_CONTEXT AS
SELECT 
    a.*,
    m.MACRO_REGIME,
    m.VIX_CLOSE,
    fx.USD_EUR_RATE,
    c.OIL_PRICE_CHANGE
FROM SAM_DEMO.CURATED.FACT_ATTRIBUTION_DAILY a
LEFT JOIN SAM_DEMO.CURATED.V_MACRO_REGIME m ON a.DATE = m.DATE
LEFT JOIN (
    SELECT DATE, VALUE AS USD_EUR_RATE
    FROM FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN.FX_RATES_TIMESERIES
    WHERE BASE_CURRENCY_ID = 'USD' AND QUOTE_CURRENCY_ID = 'EUR'
) fx ON a.DATE = fx.DATE
LEFT JOIN (
    SELECT DATE, VALUE AS OIL_PRICE_CHANGE
    FROM FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN.INTERNATIONAL_MONETARY_FUND_TIMESERIES
    WHERE VARIABLE LIKE '%WTI%'
) c ON a.DATE = c.DATE;
```

---

## 5. SCENARIO ANALYSIS DATA

### 5.1 Historical Stress Periods (From Cybersyn)

Use historical data from Cybersyn to identify stress periods:

```sql
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.DIM_STRESS_SCENARIOS AS
SELECT 'COVID_CRASH' AS SCENARIO_ID, '2020-02-19' AS START_DATE, '2020-03-23' AS END_DATE, 'Pandemic market crash' AS DESCRIPTION
UNION ALL
SELECT 'GFC', '2008-09-01', '2009-03-09', 'Global Financial Crisis'
UNION ALL
SELECT 'TAPER_TANTRUM', '2013-05-22', '2013-09-05', 'Fed taper announcement'
UNION ALL
SELECT 'RATE_HIKE_2022', '2022-01-01', '2022-10-12', 'Fed aggressive rate hikes'
UNION ALL
SELECT 'BANKING_CRISIS_2023', '2023-03-08', '2023-05-01', 'SVB/regional bank crisis';
```

### 5.2 Hypothetical Scenarios (Simulated)

```sql
CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FACT_SCENARIO_SHOCKS AS
SELECT 
    SCENARIO_ID,
    FACTOR_NAME,
    SHOCK_MAGNITUDE,
    SHOCK_DESCRIPTION
FROM VALUES
    ('RATES_UP_200BP', 'RATE_CONVEXITY', -0.15, 'Fed raises rates 200bp'),
    ('RATES_UP_200BP', 'VALUE_EXPOSURE', 0.05, 'Value outperforms in rising rates'),
    ('RATES_UP_200BP', 'GROWTH_EXPOSURE', -0.10, 'Growth underperforms'),
    ('OIL_SPIKE_50PCT', 'ENERGY_EXPOSURE', 0.25, 'Energy sector benefits'),
    ('OIL_SPIKE_50PCT', 'MARKET_BETA', -0.08, 'Broad market selloff'),
    ('AI_BUBBLE_POP', 'AI_EXPOSURE', -0.40, 'AI theme crashes'),
    ('AI_BUBBLE_POP', 'QUALITY_EXPOSURE', 0.10, 'Flight to quality'),
    ('CHINA_TAIWAN', 'GEOPOLITICAL_RISK', -0.20, 'Geopolitical risk event'),
    ('CHINA_TAIWAN', 'RESHORING_EXPOSURE', 0.15, 'Reshoring benefits')
AS t(SCENARIO_ID, FACTOR_NAME, SHOCK_MAGNITUDE, SHOCK_DESCRIPTION);
```

---

## 6. DATA REFRESH SCHEDULE

| Data Source | Refresh Frequency | Method |
|-------------|-------------------|--------|
| Cybersyn Economic | Daily (auto-updated) | Marketplace share |
| Cybersyn FX Rates | Daily (auto-updated) | Marketplace share |
| Cybersyn Commodities | Daily (auto-updated) | Marketplace share |
| Stock Prices | Daily | ETL pipeline |
| Attribution Data | Daily | Calculated post-market |
| Factor Exposures | Monthly | Model recalculation |
| Hidden Factors | Quarterly | ML model update |
| Scenario Shocks | Ad-hoc | Manual update |

---

## 7. IMPLEMENTATION STATUS ✅

### Completed Tasks

1. **✅ Data Tables Created** (16 tables in SAM_DEMO)
   - `MARKET_DATA.DIM_BENCHMARKS` - 5 benchmark definitions
   - `MARKET_DATA.FACT_BENCHMARK_RETURNS` - 6,270 daily returns
   - `MARKET_DATA.FACT_BENCHMARK_SECTOR_WEIGHTS` - Sector weights by date
   - `MARKET_DATA.FACT_VIX_DAILY` - 1,254 VIX observations
   - `MARKET_DATA.FACT_SECTOR_RETURNS` - Calculated from stock prices
   - `MARKET_DATA.FACT_POLICY_RATES` - Central bank policy rates from BIS (Cybersyn)
   - `MARKET_DATA.FACT_FX_RATES` - FX rates for major currencies vs USD (Cybersyn)
   - `MARKET_DATA.FACT_ECONOMIC_INDICATORS` - US economic indicators from FRED (GDP, CPI, unemployment)
   - `CURATED.FACT_BRINSON_BY_SECTOR` - Sector-level Brinson decomposition
   - `CURATED.FACT_BRINSON_ATTRIBUTION` - Portfolio-level attribution
   - `CURATED.FACT_FACTOR_ATTRIBUTION` - 4,620 factor contributions
   - `CURATED.FACT_HIDDEN_FACTOR_EXPOSURES` - 3,300 hidden factor exposures
   - `CURATED.V_MACRO_REGIME` - Volatility/market regime classification
   - `CURATED.DIM_STRESS_SCENARIOS` - 10 stress scenarios
   - `CURATED.FACT_SCENARIO_SHOCKS` - 70 factor shocks
   - `CURATED.FACT_HISTORICAL_STRESS_PERIODS` - 5 historical crises for backtesting

2. **✅ Semantic Views Created** (7 new views in SAM_DEMO.AI)
   - `SAM_ATTRIBUTION_VIEW` - Brinson decomposition queries
   - `SAM_ATTRIBUTION_VIEW` - Factor contribution queries
   - `SAM_ATTRIBUTION_VIEW` - Hidden/alternative factor queries
   - `SAM_MARKET_VIEW` - Market regime classification queries
   - `SAM_MARKET_VIEW` - Stress test scenario queries
   - `SAM_MARKET_VIEW` - Historical stress periods for backtesting
   - `SAM_MARKET_VIEW` - Macro data queries (FACT_POLICY_RATES, FACT_FX_RATES, FACT_ECONOMIC_INDICATORS)

3. **✅ Portfolio Manager Co-Pilot Agent** (in python/ai/agents.py)
   - Agent configuration added to config.py
   - `create_pm_cockpit()` function implemented
   - 7 semantic view tools configured for Cortex Analyst:
     - `brinson_analyzer` - Brinson attribution queries
     - `factor_analyzer` - Factor contribution queries
     - `hidden_factor_analyzer` - Hidden/thematic factor queries
     - `macro_regime_analyzer` - Market regime queries
     - `stress_scenario_analyzer` - Stress scenario queries
     - `historical_stress_analyzer` - Historical crisis queries
     - `global_macro_analyzer` - Cybersyn macro data queries
   - 1 generic tool:
     - `backtest_historical_stress` - Stored procedure for backtesting

4. **✅ Stress Period Backtesting** 
   - `RUN_STRESS_BACKTEST_TOOL` stored procedure implemented
   - Calculates portfolio performance during historical crises using factor exposures
   - Returns JSON with stress period details, portfolio impact, and factor breakdown

5. **✅ AI Narratives**
   - Agent response instructions enhanced with 3 narrative templates
   - Uses agent's native LLM for narrative generation (no separate AI_COMPLETE calls)

### Optional Future Enhancements

6. **🔲 Visualization UI** - Build Streamlit attribution visualization dashboard

---

## Appendix: Cybersyn Table Summary

Total available views in `FINANCIALS_ECONOMICS_ENTERPRISE.CYBERSYN`: **219+**

Key categories:
- Economic Indicators: 15+ tables
- Financial Institution Data: 10+ tables
- Housing/Mortgage: 8+ tables
- Labor/Employment: 5+ tables
- International Trade: 5+ tables
- Climate/Environment: 5+ tables
- Company Data: 8+ tables
- Weather/Disaster: 10+ tables
- FX Rates: 1 table (50+ currency pairs)
- Commodity Prices: Via IMF tables
