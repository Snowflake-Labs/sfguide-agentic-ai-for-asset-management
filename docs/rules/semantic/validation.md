# Semantic View Validation

Testing patterns and troubleshooting for semantic views.

## YAML Validation (Primary Approach)

All semantic views are defined as YAML files in `python/ai/semantic_view_definitions/`.

### Validate All YAML Definitions (Dry Run)
```bash
python main.py --connection-name CONNECTION --scope semantic --verify-only
```
This calls `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML` with `verify_only=TRUE` for each YAML file.

### Validate a Single View
```sql
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
  'SAM_DEMO.AI',
  $$<yaml_content_with_SAM_DEMO_substituted>$$,
  TRUE
);
-- Returns: "YAML file is valid for creating a semantic view. No object has been created yet."
```

### Export an Existing View as YAML (for comparison)
```sql
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('SAM_DEMO.AI.SAM_PORTFOLIO_VIEW');
```

### Round-Trip Validation
After deploying from YAML, export the view and compare:
1. Deploy: `python main.py --scope semantic`
2. Export: `SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('SAM_DEMO.AI.VIEW_NAME')`
3. Compare: Exported YAML should match the source file (with `{{DATABASE}}` → `SAM_DEMO`)

---

## Basic Validation

```sql
-- 1. Verify view was created
DESCRIBE SEMANTIC VIEW SAM_DEMO.AI.SAM_PORTFOLIO_VIEW;

-- 2. List all views
SHOW SEMANTIC VIEWS IN SAM_DEMO.AI;
```

## Test Queries

### Testing Strategy
1. **Single Metric + Dimension**: Verify basic functionality
2. **Multiple Metrics + Dimensions**: Test complex queries
3. **Cross-Table Queries**: Test relationships
4. **Business Scenarios**: Test real agent queries

### Query Examples

```sql
-- Basic functionality
SELECT * FROM SEMANTIC_VIEW(
    SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
    METRICS total_market_value_base
    DIMENSIONS portfolio_name
) LIMIT 5;

-- Multiple dimensions
SELECT * FROM SEMANTIC_VIEW(
    SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
    METRICS total_market_value_base, HOLDING_COUNT
    DIMENSIONS portfolio_name, industry, asset_class
) LIMIT 10;

-- Cross-table (holdings + issuers)
SELECT * FROM SEMANTIC_VIEW(
    SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
    METRICS total_market_value_base
    DIMENSIONS company_name, industry
) LIMIT 10;
```

## Validation Checklist

- [ ] `DESCRIBE SEMANTIC VIEW` returns structure
- [ ] Basic metric query returns data
- [ ] Holdings analysis works
- [ ] Sector breakdown works
- [ ] Issuer aggregation works
- [ ] All synonyms function
- [ ] No duplicate synonym errors (across facts, dimensions, and metrics)

## Common Errors and Solutions

### "invalid identifier 'TABLE.COLUMN'"

**Cause**: Column name doesn't exist or wrong case

**Fix**:
```sql
-- Check exact column names
DESCRIBE TABLE SAM_DEMO.CURATED.DIM_ISSUER;
-- Use exact names from result
```

### "duplicate synonym"

**Cause**: Same synonym in multiple facts/dimensions/metrics

**Fix**:
```yaml
# ❌ Both use 'company_name'
dimensions:
  - name: Description
    synonyms: [company_name]
  - name: LegalName
    synonyms: [company_name]

# ✅ Different synonyms
dimensions:
  - name: Description
    synonyms: [security_name]
  - name: LegalName
    synonyms: [company_name]
```

### "cannot resolve reference"

**Cause**: Foreign key relationship doesn't exist

**Fix**:
```sql
-- Verify JOIN works
SELECT COUNT(*) FROM DIM_SECURITY s
JOIN DIM_ISSUER i ON s.IssuerID = i.IssuerID;
```

### "Multi-path relationship between X and Y is not supported"

**Cause**: Two or more join paths exist between two tables in the `relationships` section.

**Example**: COVENANTS connects to BORROWERS both directly (BORROWERID) and indirectly through FACILITIES (FACILITYID -> BORROWERID).

**Fix**: Remove one relationship to leave a single unambiguous path. Keep the normalized chain.

```yaml
# ❌ Two paths from COVENANTS to BORROWERS
relationships:
  - name: FACILITIES_TO_BORROWERS
    left_table: FACILITIES
    right_table: BORROWERS
    relationship_columns:
      - left_column: BORROWERID
        right_column: BORROWERID
  - name: COVENANTS_TO_FACILITIES
    left_table: COVENANTS
    right_table: FACILITIES
    relationship_columns:
      - left_column: FACILITYID
        right_column: FACILITYID
  - name: COVENANTS_TO_BORROWERS  # ❌ Creates multi-path
    left_table: COVENANTS
    right_table: BORROWERS
    relationship_columns:
      - left_column: BORROWERID
        right_column: BORROWERID

# ✅ Single path: COVENANTS -> FACILITIES -> BORROWERS
relationships:
  - name: FACILITIES_TO_BORROWERS
    left_table: FACILITIES
    right_table: BORROWERS
    relationship_columns:
      - left_column: BORROWERID
        right_column: BORROWERID
  - name: COVENANTS_TO_FACILITIES
    left_table: COVENANTS
    right_table: FACILITIES
    relationship_columns:
      - left_column: FACILITYID
        right_column: FACILITYID
```

### "Invalid metric definition: A metric must directly refer to another aggregate-level expression"

**Cause**: A numeric row-level column was placed in METRICS with an aggregate function (e.g., AVG) when it should be in FACTS. Facts are row-level "how much" values; metrics are aggregated KPIs.

**Fix**: Move the column from `metrics` to `facts` without the aggregate:

```yaml
# ❌ Row-level value incorrectly in metrics
metrics:
  - name: CovenantThreshold
    expr: AVG(COVENANTTHRESHOLD)

# ✅ Row-level value correctly in facts
facts:
  - name: CovenantThreshold
    expr: COVENANTTHRESHOLD
    data_type: FLOAT
```

See `syntax.md` > "Classifying Columns: Facts vs Dimensions vs Metrics" for the full decision guide.

## Verified Query (VQR) Validation

### VQR Syntax Errors

**Error**: VQR SQL fails to compile or returns wrong results

**Common Causes**:

1. **Wrong FROM clause** - referencing semantic view instead of logical table
2. **Missing JOINs** - using columns from multiple tables without explicit JOINs
3. **Wrong column names in aggregates** - using metric names instead of physical columns

**Validation Checklist**:
```
✅ FROM clause uses __table_alias (e.g., FROM __holdings)
✅ NOT FROM SEMANTIC_VIEW_NAME or SEMANTIC_VIEW() function
✅ All cross-table references have explicit JOIN ... ON (...)
✅ Aggregations use physical column names (e.g., AVG(__holdings.YTD_RETURN_PCT))
✅ Non-aggregated columns use semantic names (e.g., __portfolios.portfolio_name)
```

**Example - Correct vs Wrong**:
```sql
-- ❌ WRONG - References semantic view in FROM
"sql": "SELECT __portfolios.portfolio_name FROM SAM_DEMO.AI.SAM_PORTFOLIO_VIEW"

-- ❌ WRONG - Uses SEMANTIC_VIEW() function  
"sql": "SELECT * FROM SEMANTIC_VIEW(SAM_DEMO.AI.SAM_PORTFOLIO_VIEW METRICS ytd_return)"

-- ❌ WRONG - Missing JOIN for PORTFOLIOS table
"sql": "SELECT __portfolios.portfolio_name, __holdings.holding_date FROM __holdings"

-- ❌ WRONG - Uses metric name in aggregate instead of physical column
"sql": "SELECT AVG(__holdings.ytd_return) FROM __holdings"

-- ✅ CORRECT
"sql": "SELECT __portfolios.portfolio_name, __holdings.holding_date, AVG(__holdings.YTD_RETURN_PCT) AS YTD_RETURN FROM __holdings JOIN __portfolios ON (__holdings.PORTFOLIOID = __portfolios.PORTFOLIOID) GROUP BY __portfolios.portfolio_name, __holdings.holding_date"
```

### VQR Column Reference Guide

| YAML Definition | VQR Usage |
|-----------------|-----------|
| `name: portfolio_name` / `expr: PORTFOLIONAME` (dimension) | `__portfolios.portfolio_name` |
| `name: ytd_return` / `expr: AVG(YTD_RETURN_PCT)` (metric) | `AVG(__holdings.YTD_RETURN_PCT)` (physical column in aggregate) |
| `name: total_market_value_base` / `expr: SUM(MARKETVALUEBASE)` (metric) | `SUM(__holdings.MARKETVALUEBASE)` (physical column in aggregate) |
| `name: holding_date` / `expr: HOLDINGDATE` (time dimension) | `__holdings.holding_date` |

### VQR JOIN Pattern

For multi-table queries, use the RELATIONSHIPS defined in the semantic view:
```sql
-- Relationship: holdings_to_portfolios AS holdings(PORTFOLIOID) REFERENCES portfolios(PORTFOLIOID)
-- VQR JOIN: JOIN __portfolios ON (__holdings.PORTFOLIOID = __portfolios.PORTFOLIOID)

-- Relationship: holdings_to_securities AS holdings(SECURITYID) REFERENCES securities(SECURITYID)
-- VQR JOIN: JOIN __securities ON (__holdings.SECURITYID = __securities.SECURITYID)

-- Relationship: securities_to_issuers AS securities(ISSUERID) REFERENCES issuers(ISSUERID)
-- VQR JOIN: JOIN __issuers ON (__securities.ISSUERID = __issuers.ISSUERID)
```

## Prerequisites Check

```python
def verify_tables(session, tables):
    for table in tables:
        try:
            session.sql(f"SELECT 1 FROM {table} LIMIT 1").collect()
            cols = session.sql(f"DESCRIBE TABLE {table}").collect()
            print(f"✅ {table}: {len(cols)} columns")
        except Exception as e:
            print(f"❌ {table}: {e}")
            return False
    return True

# Required tables
tables = [
    'SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR',
    'SAM_DEMO.CURATED.DIM_PORTFOLIO',
    'SAM_DEMO.CURATED.DIM_SECURITY',
    'SAM_DEMO.CURATED.DIM_ISSUER'
]
verify_tables(session, tables)
```

## Synonym Uniqueness Check

Synonyms must be unique across ALL facts, dimensions, and metrics.

```python
def validate_synonyms(dimensions_and_metrics):
    all_synonyms = set()
    duplicates = set()
    
    for name, synonyms in dimensions_and_metrics.items():
        for syn in synonyms:
            if syn in all_synonyms:
                duplicates.add(syn)
            all_synonyms.add(syn)
    
    if duplicates:
        print(f"❌ Duplicates: {duplicates}")
        return False
    print("✅ All synonyms unique")
    return True
```

## Performance Guidelines

- Start with 2 tables, add incrementally
- Keep relationships simple (avoid circular)
- Test with realistic data volumes
- Monitor query response times
- Consider multiple focused views vs one large view
