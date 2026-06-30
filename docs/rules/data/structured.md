# Structured Data Generation

Patterns for building dimension and fact tables in the SAM demo.

## Config Helper Functions

```python
from demo_helpers import get_demo_company_priority_sql, build_demo_portfolios_sql_mapping
from sql_utils import safe_sql_tuple

# Generate SQL CASE for demo company priority
get_demo_company_priority_sql()
# → "WHEN s.Ticker = 'AAPL' THEN 1 WHEN s.Ticker = 'CMC' THEN 1 ..."

# Safe SQL tuple (handles empty lists)
safe_sql_tuple(items)
# Empty: "('__NONE__')" | Single: "('ITEM')" | Multiple: "('A', 'B')"

# Get demo company tickers by tier
from demo_helpers import get_demo_company_tickers
get_demo_company_tickers()              # All tickers
get_demo_company_tickers(tier='core')   # Core tier only
```

## Config Access Pattern

```python
# ✅ CORRECT: Extract values before f-string
database_name = config.DATABASE['name']
warehouse_name = config.WAREHOUSES['execution']['name']
sql = f"CREATE TABLE {database_name}.CURATED.TABLE_NAME ..."

# ❌ WRONG: Nested brackets cause syntax errors
sql = f"CREATE TABLE {config.DATABASE['name']}.CURATED.TABLE_NAME ..."
```

## Core Tables Build Order

1. **DIM_ISSUER** - From DEMO_COMPANIES config
2. **DIM_SECURITY** - Derived from issuers
3. **DIM_PORTFOLIO** - Portfolio definitions
4. **DIM_BENCHMARK** - Benchmark indices
5. **FACT_TRANSACTION** - Transaction log (source of truth)
6. **FACT_POSITION_DAILY_ABOR** - Daily positions (derived)
7. **FACT_ESG_SCORES** - ESG ratings
8. **FACT_FACTOR_EXPOSURES** - Factor scores

## Dimension Table Pattern

```python
def build_dim_issuer(session, test_mode=False):
    """Build issuer dimension from DEMO_COMPANIES config."""
    database_name = config.DATABASE['name']
    
    issuers = []
    for i, (ticker, company) in enumerate(config.DEMO_COMPANIES.items(), 1):
        issuers.append({
            'IssuerID': i,
            'LegalName': company['company_name'],
            'CIK': company['cik'],
            'GICS_Sector': company['sector'],
            'Ticker': ticker,
            'Tier': company['tier']
        })
    
    df = session.create_dataframe(issuers)
    df.write.mode("overwrite").save_as_table(
        f"{database_name}.CURATED.DIM_ISSUER"
    )
```

## Fact Table Pattern

```python
def build_positions(session, test_mode=False):
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_POSITION_DAILY_ABOR AS
        WITH prioritized_securities AS (
            SELECT s.*, i.LegalName,
                CASE 
                    {config.get_demo_company_priority_sql()}
                    ELSE 10
                END as priority
            FROM {database_name}.CURATED.DIM_SECURITY s
            JOIN {database_name}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE priority <= 7
        )
        SELECT ...
    """).collect()
```

## Config-Driven Generation

Use SQL case builders for ranges (no hardcoded values):

```python
from sql_case_builders import build_sector_case_sql, build_grade_case_sql

# Sector-based UNIFORM ranges
e_score_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'esg.E')
# → "CASE WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(60, 95, RANDOM()) ..."

# ESG grade from score
grade_sql = build_grade_case_sql('E_SCORE')
# → "CASE WHEN E_SCORE >= 86 THEN 'AAA' WHEN E_SCORE >= 71 THEN 'AA' ... END"
```

## Validation Pattern

```python
def validate_portfolio_weights(session, database_name):
    """Portfolio weights must sum to ~100%."""
    result = session.sql(f"""
        SELECT PortfolioID, HoldingDate, SUM(PortfolioWeight) as TotalWeight
        FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR
        GROUP BY 1, 2
        HAVING ABS(TotalWeight - 1.0) > 0.001
    """).collect()
    
    if len(result) > 0:
        print(f"❌ Weight validation failed: {len(result)} portfolios")
        return False
    print("✅ Portfolio weights validated")
    return True
```

## Common Pitfalls

| Bad | Good |
|-----|------|
| Hardcoded tickers in SQL | `get_demo_company_priority_sql()` |
| Hardcoded numeric ranges | `build_sector_case_sql()` |
| Regex for asset filtering | `WHERE AssetClass = 'Equity'` |
| `tuple(tickers)` | `safe_sql_tuple(tickers)` |
