# Real Data Patterns

Real asset implementation and external data access patterns for SAM demo.

## DEMO_COMPANIES Configuration

Single source of truth in `python/config.py`:

```python
DEMO_COMPANIES = {
    'AAPL': {
        'company_name': 'APPLE INC.',
        'provider_company_id': 'a1823f6c7cd49c0be0bb8c43bcf49060',
        'cik': '0000320193',
        'sector': 'Information Technology',
        'tier': 'core'  # 'core', 'major', or 'additional'
    },
    # ... ~76 companies total
}
```

## Tier Structure

| Tier | Count | Purpose |
|------|-------|---------|
| core | 8 | Primary demo companies |
| major | 36 | Well-known companies |
| additional | 32 | Portfolio diversity |

## Helper Functions

```python
config.get_demo_company_tickers()              # All tickers
config.get_demo_company_tickers(tier='core')   # 8 core companies
config.get_demo_company_ciks()                 # CIKs for SEC data
config.get_all_target_tickers()                # ~76 tickers
```

## External Data Sources

```python
REAL_DATA_SOURCES = {
    'database': 'SNOWFLAKE_PUBLIC_DATA_PAID',
    'schema': 'CYBERSYN',
    'tables': {
        'stock_prices': {'table': 'STOCK_PRICE_TIMESERIES'},
        'sec_metrics': {'table': 'SEC_METRICS_TIMESERIES'},
        'company_events': {'table': 'COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES'},
        'treasury_yields': {'table': 'US_TREASURY_TIMESERIES'},
        'sec_insider_trading': {'table': 'SEC_INSIDER_TRADING_SECURITIES_INDEX'},
        'sec_13f': {'table': 'SEC_HOLDING_FILING_ATTRIBUTES'},
        'climate_watch': {'table': 'CLIMATE_WATCH_TIMESERIES'},
    }
}
```

## Critical: CIK-Based Filtering

**Always filter by CIK when sourcing external data** - tickers can collide across markets.

```sql
WITH target_ciks AS (
    SELECT DISTINCT i.CIK
    FROM DIM_SECURITY s
    JOIN DIM_ISSUER i ON s.IssuerID = i.IssuerID
    WHERE s.Ticker IN (...)
      AND i.CIK IS NOT NULL
)
SELECT *
FROM SNOWFLAKE_PUBLIC_DATA_PAID.CYBERSYN.SEC_METRICS_TIMESERIES
WHERE CIK IN (SELECT CIK FROM target_ciks)
```

## ID Hierarchy (Reliability)

1. **CIK** - SEC-assigned, unique per legal entity
2. **provider_company_id** - Snowflake Public Data internal ID
3. **Ticker** - Exchange-assigned, used for display only

## Ticker Collision Example

The ticker `CMC` represents 5 different companies across markets:
- Commercial Metals Co (USA) - Demo company
- Chaoprayamahanakorn PCL (Thailand)
- Cielo Waste Solutions Corp (Canada)
- CMC Investment JSC (Vietnam)
- Comeco SA (Poland)
