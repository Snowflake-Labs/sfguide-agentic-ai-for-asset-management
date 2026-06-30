# Market Data Integration

Patterns for building real market data tables from Snowflake Marketplace.

## Schema Overview

| Table | Source | Purpose |
|-------|--------|---------|
| FACT_STOCK_PRICES | STOCK_PRICE_TIMESERIES | Daily OHLCV prices |
| FACT_SEC_FINANCIALS | SEC_CORPORATE_REPORT_ATTRIBUTES | SEC statements + calculated metrics (TAM, NRR) |
| FACT_SEC_SEGMENTS | SEC_CORPORATE_GEO_REVENUE_REPORT_ATTRIBUTES | Geographic and business segment revenue |
| DIM_GEO_RISK_CLASSIFICATION | Derived from FACT_SEC_SEGMENTS geographies | Lookup: 189 geographies → HIGH/MEDIUM/LOW risk tiers |
| FACT_TRANSCRIPT_NLP_SCORES | CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS + FACT_SEC_SEGMENTS | AI exposure (AI_AGG on corpus) + geo risk (SQL calculation) |
| FACT_POLICY_RATES | BIS_TIMESERIES | Central bank policy rates |
| FACT_FX_RATES | BIS_TIMESERIES | Foreign exchange rates |
| FACT_ECONOMIC_INDICATORS | BIS_TIMESERIES | Macroeconomic indicators |
| FACT_TREASURY_YIELDS | US_TREASURY_TIMESERIES | Daily Treasury par yield curve (14 maturities) |
| FACT_COUNTRY_EMISSIONS | CLIMATE_WATCH_TIMESERIES | Annual GHG emissions by country/sector |
| FACT_INSIDER_TRANSACTIONS | SEC_INSIDER_TRADING_SECURITIES_INDEX | SEC Form 4 insider buy/sell |
| FACT_INSTITUTIONAL_HOLDINGS | SEC_HOLDING_FILING_INDEX + ATTRIBUTES | SEC 13F institutional ownership |
| FACT_DIVIDENDS | SEC 8-K filings via AI_EXTRACT | Dividend history |
| FACT_BENCHMARK_RETURNS | STOCK_PRICE_TIMESERIES (ETFs) | Daily benchmark ETF returns |
| FACT_VIX_DAILY | STOCK_PRICE_TIMESERIES (VIXY) | VIX proxy from VIXY ETF |
| FACT_SECTOR_RETURNS | STOCK_PRICE_TIMESERIES (sector ETFs) | Daily sector ETF returns |
| FACT_ESTIMATE_CONSENSUS | Derived from FACT_SEC_FINANCIALS | Analyst estimates |
| FACT_BROKER_RESEARCH | Synthetic + real prices | Broker analyst data |
| DIM_ANALYST | Synthetic | Analyst dimension |
| DIM_BROKER | Synthetic | Broker dimension |

**Note**: Company data from `CURATED.DIM_ISSUER` — no separate `DIM_COMPANY`.

## Data Source

```python
# config.py
REAL_DATA_SOURCES = {
    'database': 'SNOWFLAKE_PUBLIC_DATA_PAID',
    'schema': 'CYBERSYN'
}
```

All Marketplace source tables are catalogued in `data/reference_data/data_sources.yaml`.

## Key Joins

All MARKET_DATA fact tables join to `CURATED.DIM_ISSUER`:

```sql
-- Stock prices: via Ticker
JOIN DIM_SECURITY ds ON sp.TICKER = ds.Ticker

-- SEC data: via CIK
JOIN DIM_ISSUER i ON sec.CIK = i.CIK

-- Corpus transcript data: via IssuerID (already joined in corpus)
WHERE c.IssuerID IS NOT NULL
```

## Build Order

`build_all()` runs in Step 2 (Market Data), without NLP scoring:

```python
def build_all(session, test_mode=False):
    build_reference_tables(session, test_mode)        # DIM_ANALYST, DIM_BROKER
    build_real_stock_prices(session, test_mode)        # FACT_STOCK_PRICES (if not already built)
    build_real_sec_financials(session, test_mode)      # FACT_SEC_FINANCIALS
    build_sec_segments(session, test_mode)             # FACT_SEC_SEGMENTS
    build_geo_risk_classification(session)             # DIM_GEO_RISK_CLASSIFICATION (lookup table)
    build_broker_analyst_data(session, test_mode)      # FACT_BROKER_RESEARCH
    build_estimate_data(session, test_mode)            # FACT_ESTIMATE_CONSENSUS
    build_fact_policy_rates(session, test_mode)        # FACT_POLICY_RATES
    build_fact_fx_rates(session, test_mode)            # FACT_FX_RATES
    build_fact_economic_indicators(session, test_mode) # FACT_ECONOMIC_INDICATORS
    build_fact_treasury_yields(session, test_mode)      # FACT_TREASURY_YIELDS
    build_fact_country_emissions(session, test_mode)    # FACT_COUNTRY_EMISSIONS
    build_fact_insider_transactions(session, test_mode) # FACT_INSIDER_TRANSACTIONS
    build_fact_institutional_holdings(session, test_mode) # FACT_INSTITUTIONAL_HOLDINGS
    build_fact_dividends(session, test_mode)           # FACT_DIVIDENDS (if not already built)
```

`build_transcript_nlp_scores()` runs separately in Step 5 (after pipelines build the corpus table).

## NLP Scoring Pattern (FACT_TRANSCRIPT_NLP_SCORES)

Two scores per company per fiscal quarter, using **different approaches for different data types**:

### AI Exposure Score (AI_AGG — unstructured text needs NLP)

```sql
AI_AGG(
    ct.DOCUMENT_TEXT,
    'Score the company''s exposure to AI/ML on a scale of 0 to 100...'
)
```

- Reads from `CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS` (pre-flattened, speaker-enriched)
- Corpus DOCUMENT_TEXT format: `"Speaker Name (Role): chunk_text"`
- Runs on `SAM_DEMO_CORTEX_WH` (AI workload)
- Must run AFTER pipeline execution (Step 4) builds the corpus table

### Geo Risk Score (SQL calculation — structured data, no AI needed)

```sql
-- Revenue classified via lookup table
SUM(revenue × risk_weight) / total_revenue × 100 + concentration_bonus
```

- Uses `DIM_GEO_RISK_CLASSIFICATION` to map 189 geography values to risk tiers:
  - **HIGH** (weight 1.0): China, Taiwan, Russia, Iran, Middle East, Hong Kong
  - **MEDIUM** (weight 0.5): Other APAC, Latin America, Africa, Eastern Europe
  - **LOW** (weight 0.1): US, Canada, Western Europe, Japan, Australia, South Korea
- Concentration bonus: +15 if single high-risk country >30% revenue, +25 if >50%
- Default score of 10 for companies without geographic segment data
- Pure SQL — deterministic, auditable, instant, no Cortex credits

### Design principle

> Use AI only where data is unstructured. Use SQL math where data is already numeric and structured.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No price data | Check SNOWFLAKE_PUBLIC_DATA_PAID access |
| Missing CIK matches | Verify CIKs in DIM_ISSUER |
| Zero SEC records | Check Marketplace source tables |
| No corpus transcripts | Verify pipeline execution completed (Step 4) and RAW table was loaded |
| AI_AGG timeout | Check cortex warehouse size (needs MEDIUM+) |
| Geo risk all same score | Verify DIM_GEO_RISK_CLASSIFICATION was built before FACT_TRANSCRIPT_NLP_SCORES |
