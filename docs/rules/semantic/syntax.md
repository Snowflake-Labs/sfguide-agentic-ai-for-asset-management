# Semantic View Syntax

Essential syntax patterns for creating Snowflake semantic views.

## YAML-Based Definitions (Primary Approach)

All 28 semantic views are now defined as YAML files in `python/ai/semantic_view_definitions/`.

### File Structure
```
python/ai/
├── semantic_view_definitions/     # 28 YAML files (source of truth)
│   ├── SAM_PORTFOLIO_VIEW.yaml
│   ├── SAM_PORTFOLIO_VIEW.yaml
│   └── ...
├── yaml_loader.py                 # Template engine + SYSTEM$ caller
└── semantic_views.py              # Scenario → view dispatcher
```

### YAML Template Variables

YAML files use `{{DATABASE}}` placeholders substituted at deploy time:
```yaml
base_table:
  database: "{{DATABASE}}"
  schema: CURATED
  table: FACT_POSITION_DAILY_ABOR
```

### Snowflake YAML Functions

| Function | Purpose |
|----------|---------|
| `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('db.schema', $$yaml$$, verify_only)` | Create/validate view from YAML |
| `SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('db.schema.view')` | Export existing view as YAML |

### YAML Covers Everything

The YAML format includes all features — no supplementary SQL needed:
- `tables` (base_table, primary_key, dimensions, time_dimensions, facts, metrics, filters)
- `relationships` (joins)
- `verified_queries` (replaces WITH EXTENSION CA JSON VQRs)
- `module_custom_instructions` (sql_generation + question_categorization)
- `description` (maps to COMMENT)

### Build Commands
```bash
# Validate all YAML definitions (dry run)
python main.py --connection-name CONNECTION --scope semantic --verify-only

# Deploy all semantic views from YAML
python main.py --connection-name CONNECTION --scope semantic

# Deploy semantic views + agents
python main.py --connection-name CONNECTION --scope ai
```

### YAML Structure

```yaml
name: SAM_EXAMPLE_VIEW
description: "View description (becomes COMMENT on the view)"
tables:
  - name: table_alias
    synonyms:
      - alias1
      - alias2
    description: Table description
    base_table:
      database: "{{DATABASE}}"
      schema: CURATED
      table: PHYSICAL_TABLE_NAME
    primary_key:
      columns:
        - COL1
        - COL2
    dimensions:
      - name: semantic_name
        synonyms:
          - dim_synonym
        description: Dimension description
        expr: ACTUAL_COLUMN
        data_type: VARCHAR(134217728)
    facts:
      - name: fact_name
        expr: ACTUAL_COLUMN
        data_type: FLOAT
        access_modifier: public_access
    metrics:
      - name: total_fact_name
        synonyms:
          - metric_synonym
        description: Metric description
        expr: SUM(fact_name)
        access_modifier: public_access
    time_dimensions:
      - name: trade_date
        synonyms:
          - date_synonym
        description: Date/time column description
        expr: ACTUAL_DATE_COLUMN
        data_type: DATE
relationships:
  - name: relationship_name
    left_table: left_alias
    right_table: right_alias
    relationship_columns:
      - left_column: FK_COLUMN
        right_column: PK_COLUMN
module_custom_instructions:
  sql_generation: "Instructions for SQL generation (maps to AI_SQL_GENERATION)"
  question_categorization: "Instructions for classifying questions (maps to AI_QUESTION_CATEGORIZATION)"
verified_queries:
  - name: query_name
    question: "Natural language question"
    sql: "SELECT * FROM SEMANTIC_VIEW({{DATABASE}}.AI.VIEW_NAME METRICS MetricName)"
    use_as_onboarding_question: true
```

### Adding a New Semantic View

1. Create `python/ai/semantic_view_definitions/SAM_NEW_VIEW.yaml`
2. Use `{{DATABASE}}` for all database references
3. Add the view to `SCENARIO_VIEW_MAP` in `python/ai/semantic_views.py`
4. Validate: `python main.py --scope semantic --verify-only`
5. Deploy: `python main.py --scope semantic`

### Editing Workflow
1. Edit the YAML file in `semantic_view_definitions/`
2. Validate: `--scope semantic --verify-only`
3. Deploy: `--scope semantic`
4. Re-export to verify round-trip: `SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('SAM_DEMO.AI.VIEW_NAME')`

---

## Naming Convention

All semantic names MUST use `lowercase_snake_case`. Names should be self-documenting so readers understand meaning without needing synonyms.

### Rules

1. **lowercase_snake_case** for ALL semantic names: tables, dimensions, time_dimensions, facts, metrics, relationships
2. **Self-documenting names** — a reader should understand what the column represents
3. **Date columns describe WHAT the date is** — `holding_date` not `DATE`, `attribution_date` not `DATE`
4. **Metrics include aggregation prefix** — `average_`, `total_`, `max_`, `min_` (e.g., `average_esg_score`, `total_market_value_base`)
5. **Expand abbreviations** — `benchmark_annualized_return_pct` not `BMANNUALIZEDRETURNPCT`
6. **Remove redundant synonyms** — if the new name matches an existing synonym, remove it
7. **No "TOTAL" doubling** — when the fact is already `total_assets`, the metric is `sum_total_assets` not `total_total_assets`
8. **No "AVG" doubling** — when the fact is already `avg_active_return`, the metric is `average_active_return` not `average_avg_active_return`
9. **Disambiguate generic names** — `DESCRIPTION` becomes `factor_description`, `security_description`, `scenario_description`, etc.

### Examples

```yaml
# Dimension naming
- name: portfolio_name       # not PORTFOLIONAME
  expr: PORTFOLIONAME        # physical column UNCHANGED
- name: country_of_incorporation  # not COUNTRYOFINCORPORATION
  expr: COUNTRYOFINCORPORATION

# Fact naming
- name: market_value_base    # not MARKETVALUEBASE
  expr: MARKETVALUEBASE
- name: esg_score            # not ESGSCORE
  expr: ESGSCORE

# Metric naming (includes aggregation prefix)
- name: total_market_value_base   # SUM → total_
  expr: SUM(market_value_base)    # references renamed fact name
- name: average_esg_score         # AVG → average_
  expr: AVG(esg_score)
- name: max_portfolio_weight      # MAX → max_
  expr: MAX(portfolio_weight)

# Time dimension naming (describes what the date is)
- name: holding_date         # not DATE or HOLDINGDATE
  expr: HOLDINGDATE
- name: attribution_date     # not DATE
  expr: DATE

# Table naming
- name: holdings             # not HOLDINGS
- name: factor_exposures     # not FACTOR_EXPOSURES

# Relationship naming
- name: holdings_to_portfolio    # not HOLDINGS_TO_PORTFOLIO
  left_table: holdings           # matches lowercase table name
  right_table: portfolios
```

---

## The `name`/`expr` Pattern

In YAML, each dimension, fact, and metric uses `name` (semantic name users see) and `expr` (actual database column):

```yaml
dimensions:
  - name: company_name       # What users say
    expr: LEGALNAME          # Actual database column

facts:
  - name: market_value_base  # Semantic name
    expr: MARKETVALUEBASE    # Actual database column

metrics:
  - name: total_market_value # Semantic name
    expr: SUM(market_value_base)  # Aggregation referencing a FACT name
```

**Memory Aid**: "name = what users say (lowercase_snake_case), expr = what the database has (physical column)"

### Example Mapping

If `DIM_ISSUER` has columns: `ISSUERID`, `LEGALNAME`, `SIC_DESCRIPTION`

```yaml
# ✅ CORRECT
dimensions:
  - name: company_name
    expr: LEGALNAME
  - name: industry
    expr: SIC_DESCRIPTION
```

## Classifying Columns: Facts vs Dimensions vs Metrics

Choosing the wrong section causes compilation errors. Use this decision guide:

| Section | What it represents | Question it answers | Aggregated? | Examples |
|---------|-------------------|---------------------|-------------|----------|
| **facts** | Row-level numeric attributes | "How much?" "How many?" | No (raw row values) | Sale amount, covenant threshold, actual leverage, headroom %, quantity |
| **dimensions** | Categorical attributes | "Who?" "What?" "Where?" | No (grouping labels) | Borrower name, sector, status, rating, facility type |
| **time_dimensions** | Date/timestamp columns | "When?" | No (temporal grouping) | Trade date, report date, settlement date, quarter end |
| **metrics** | Aggregated KPIs | "What is the total/average?" | Yes (SUM, AVG, COUNT) | Total revenue, average leverage, breach count, deal count |

**Decision Flowchart**:
1. Is the column a **DATE, TIMESTAMP_NTZ, or TIMESTAMP_LTZ** type? -> **time_dimensions**
2. Is the column used to **group/filter/categorize** data? -> **dimensions**
3. Is the column a **raw numeric value per row** (amount, ratio, percentage)? -> **facts**
4. Is the column an **aggregation across rows** (SUM, AVG, COUNT)? -> **metrics**

**time_dimensions vs dimensions**: Always use `time_dimensions` for DATE and TIMESTAMP columns. This tells Cortex Analyst the column represents temporal data, enabling time-aware query generation (date filtering, trending, period comparison). VARCHAR columns with date-like names (e.g., fiscal_period) should remain as `dimensions`.

**Common Mistake**: Putting row-level numeric columns (like thresholds or actual values) in metrics with AVG() when they should be facts. This causes: `Invalid metric definition: A metric must directly refer to another aggregate-level expression...`

**Facts can also use expressions and aggregates from child tables**:
```yaml
facts:
  - name: covenant_threshold
    expr: COVENANTTHRESHOLD
  - name: line_item_id
    expr: "CONCAT(l_orderkey, '-', l_linenumber)"
  - name: count_line_items
    expr: COUNT(LINEITEM.line_item_id)
```

## Synonym Rules

Each synonym can only be used ONCE across ALL facts, dimensions, and metrics in a view.

```yaml
# ❌ ERROR: 'issuer_name' used twice
dimensions:
  - name: security_description
    synonyms: [issuer_name]
  - name: legal_name
    synonyms: [issuer_name]

# ✅ CORRECT: Unique synonyms
dimensions:
  - name: security_description
    synonyms: [security_name]
  - name: legal_name
    synonyms: [company_name]
```

**Common Conflicts**:
- `company` vs `company_name`
- `weight` vs `weight_percent`
- `exposure` across different contexts
- `date` across different dimensions

## Querying Semantic Views

Use the semantic name (`name` field), not the database column (`expr` field):

```yaml
# Definition:
dimensions:
  - name: industry         # ← use this in queries
    expr: SIC_DESCRIPTION  # ← NOT this
```

```sql
-- ✅ Query uses "industry" (the name):
SELECT * FROM SEMANTIC_VIEW(
    SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
    DIMENSIONS industry
)

-- ❌ Wrong - uses "SIC_DESCRIPTION" (the expr):
SELECT * FROM SEMANTIC_VIEW(
    SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
    DIMENSIONS SIC_DESCRIPTION
)
```

## Custom Instructions (module_custom_instructions)

In YAML, custom instructions are specified in the `module_custom_instructions` section:

```yaml
module_custom_instructions:
  sql_generation: "CRITICAL: Always filter holdings to the latest date unless the user explicitly requests historical data. Round market values to 2 decimal places."
  question_categorization: "If users ask about funds or portfolios, treat these as the same concept. If users ask about today or current, interpret as the maximum available date."
```

These map to `AI_SQL_GENERATION` and `AI_QUESTION_CATEGORIZATION` in the deployed view.

### sql_generation
Instructions for how Cortex Analyst should generate SQL. Use for:
- Date handling rules
- Rounding rules
- Aggregation guidance
- Join patterns

### question_categorization
Instructions for how to classify and interpret user questions. Use for:
- Synonym interpretation
- Default behavior
- Rejection rules

## Verified Queries (verified_queries)

In YAML, verified queries are specified in the `verified_queries` section:

```yaml
verified_queries:
  - name: year_end_performance
    question: "What was the full year performance for the last calendar year?"
    sql: "SELECT __portfolios.portfolio_name, AVG(__holdings.YTD_RETURN_PCT) AS YTD_RETURN FROM __holdings JOIN __portfolios ON (__holdings.PORTFOLIOID = __portfolios.PORTFOLIOID) GROUP BY __portfolios.portfolio_name ORDER BY YTD_RETURN DESC"
    use_as_onboarding_question: false
```

### VQR SQL Syntax (CRITICAL)

Verified queries must use logical table/column names, NOT physical database names or the semantic view name.

The logical table name is the table `name` (alias) prefixed with double underscore (`__`).

**CRITICAL RULES**:
1. **FROM clause**: Use `FROM __table_alias` (the logical table), NOT `FROM SEMANTIC_VIEW_NAME`
2. **JOINs**: Use explicit `JOIN ... ON (...)` with physical FK/PK columns
3. **SELECT columns**: Use `__table_alias.semantic_name` for dimensions
4. **Aggregations**: Use the physical column names with aggregation functions (e.g., `AVG(__holdings.YTD_RETURN_PCT)`)
5. **WHERE/GROUP BY**: Use `__table_alias.semantic_name` or `__table_alias.PHYSICAL_COLUMN`

**Memory Aid**: "Double underscore + lowercase table alias, explicit JOINs, physical columns in aggregates"

```
YAML:        name: holding_date / expr: HOLDINGDATE
VQR usage:   __holdings.holding_date
             ↑↑        ↑
             prefix    semantic name (the 'name' field)

YAML:        name: ytd_return / expr: AVG(YTD_RETURN_PCT)
VQR usage:   AVG(__holdings.YTD_RETURN_PCT)
             ↑   ↑↑        ↑
             agg prefix    physical column name (inside aggregation)
```

### VQR Examples

```sql
-- ✅ CORRECT - Uses __table_alias, explicit JOINs, physical columns in aggregates
"SELECT __portfolios.portfolio_name, AVG(__holdings.YTD_RETURN_PCT) AS YTD_RETURN
FROM __holdings
JOIN __portfolios ON (__holdings.PORTFOLIOID = __portfolios.PORTFOLIOID)
GROUP BY __portfolios.portfolio_name
ORDER BY YTD_RETURN DESC"

-- ❌ WRONG - References semantic view in FROM
"SELECT ... FROM SAM_DEMO.AI.SAM_PORTFOLIO_VIEW"

-- ❌ WRONG - Uses SEMANTIC_VIEW() function (for ad-hoc queries, not VQRs)
"SELECT * FROM SEMANTIC_VIEW(SAM_DEMO.AI.SAM_PORTFOLIO_VIEW METRICS ytd_return)"

-- ❌ WRONG - Missing explicit JOINs
"SELECT __portfolios.portfolio_name FROM __holdings"

-- ❌ WRONG - Uses metric name instead of physical column in aggregate
"SELECT AVG(__holdings.ytd_return) FROM __holdings"
-- Should be: AVG(__holdings.YTD_RETURN_PCT)
```

### Common VQR Mistakes

| Wrong | Correct |
|-------|---------|
| `FROM SAM_DEMO.AI.SEMANTIC_VIEW` | `FROM __holdings` |
| `FROM SEMANTIC_VIEW(...)` | `FROM __holdings JOIN __portfolios ON (...)` |
| `SELECT __portfolios.portfolio_name` (no JOIN) | `... JOIN __portfolios ON (...)` |
| `__holdings.ytd_return` in aggregate | `AVG(__holdings.YTD_RETURN_PCT)` |
| `SUM(__holdings.TOTAL_MARKET_VALUE)` | `SUM(__holdings.MARKETVALUEBASE)` |

### Multi-Table VQR Pattern

For queries spanning multiple tables, follow the relationship chain:
```sql
-- Holdings → Securities → Issuers (for sector analysis)
"SELECT __portfolios.portfolio_name, __issuers.industry AS Sector,
    SUM(__holdings.MARKETVALUEBASE) AS Sector_Value
FROM __holdings
JOIN __portfolios ON (__holdings.PORTFOLIOID = __portfolios.PORTFOLIOID)
JOIN __securities ON (__holdings.SECURITYID = __securities.SECURITYID)
JOIN __issuers ON (__securities.ISSUERID = __issuers.ISSUERID)
WHERE __holdings.holding_date = (SELECT MAX(__holdings.holding_date) FROM __holdings)
GROUP BY __portfolios.portfolio_name, __issuers.industry
ORDER BY Sector_Value DESC"
```

## Prerequisites

Before creating a new view, verify underlying tables exist:

```sql
DESCRIBE TABLE SAM_DEMO.CURATED.DIM_ISSUER;
DESCRIBE TABLE SAM_DEMO.CURATED.DIM_SECURITY;
DESCRIBE TABLE SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR;
```
