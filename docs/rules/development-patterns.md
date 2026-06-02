# SAM Demo - Development Patterns Guide

Self-contained patterns for extending the SAM demo with new tables, semantic views, agents, and scenarios without requiring chat history.

## Logging and Output Standards

### CRITICAL: Never Use Raw print() Statements

All Python code MUST use the logging utilities from `logging_utils.py`. Raw `print()` statements break verbosity control.

### Logging Functions Reference

| Function | Verbosity | Use Case |
|----------|-----------|----------|
| `log_phase(name)` | Always (0+) | Major phases: "Structured Data", "AI Components" |
| `log_step(name)` | Level 0+ | High-level steps: "Dimension tables", "Fact tables" |
| `log_substep(name)` | Level 1+ | Detailed sub-steps: individual table builds, component creation |
| `log_info(msg)` | Level 1+ | Informational messages during processing |
| `log_detail(msg)` | Level 2+ | Verbose debugging details |
| `log_success(msg)` | Level 1+ | Success confirmations (✅ prefix) |
| `log_warning(msg)` | Always (0+) | Warnings - non-fatal issues (⚠️ prefix) |
| `log_error(msg)` | Always (0+) | Errors - fatal issues (❌ prefix) |
| `log_phase_complete(msg)` | Always (0+) | Phase completion summary |

### Usage Rules

1. **Import from logging_utils**: `from logging_utils import log_step, log_substep, log_detail, ...`
2. **Use `log_step()` sparingly**: Only for top-level progress visible at verbosity 0
3. **Use `log_substep()` for detailed progress**: Individual table builds, component creation
4. **Use `log_detail()` for verbose output**: Only shown at verbosity 2
5. **Warnings and errors always show**: Use `log_warning()` and `log_error()` for issues

### Example Usage

```python
from logging_utils import log_phase, log_step, log_substep, log_detail, log_phase_complete

def build_data(session: Session):
    log_phase("Structured Data")           # Always shown
    
    log_step("Dimension tables")           # Shown at level 0 (minimal)
    log_substep("DIM_SECURITY")            # Only shown at level 1+
    log_substep("DIM_PORTFOLIO")           # Only shown at level 1+
    
    log_step("Fact tables")                # Shown at level 0 (minimal)
    log_substep("FACT_TRANSACTION")        # Only shown at level 1+
    log_detail("Created 10,000 records")   # Only shown at level 2+
    
    log_phase_complete("Structured data complete")  # Always shown
```

### Output at Different Verbosity Levels

**Level 0 (Minimal - default):**
```
============================================================
  Structured Data
============================================================
  → Dimension tables...
  → Fact tables...
  ✅ Structured data complete
```

**Level 1 (Normal):**
```
============================================================
  Structured Data
============================================================
  [1] Dimension tables
    → DIM_SECURITY...
    → DIM_PORTFOLIO...
  [2] Fact tables
    → FACT_TRANSACTION...
  ✅ Structured data complete
```

---

## Adding New Data Tables

### Pattern 1: Dimension Tables
```sql
-- Template for new dimension tables
CREATE OR REPLACE TABLE {DATABASE_NAME}.CURATED.DIM_{ENTITY_NAME} (
    {Entity}ID BIGINT IDENTITY(1,1) PRIMARY KEY,
    {ParentEntity}ID BIGINT,                     -- FK to parent if hierarchical
    {Entity}Name VARCHAR(255) NOT NULL,
    {Entity}Code VARCHAR(100),
    {Attribute1} VARCHAR(100),
    {Attribute2} DATE,
    RecordStartDate TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    RecordEndDate TIMESTAMP_NTZ,
    IsActive BOOLEAN DEFAULT TRUE
);
```

### Pattern 2: Fact Tables
```sql
-- Template for new fact tables
CREATE OR REPLACE TABLE {DATABASE_NAME}.CURATED.FACT_{EVENT_NAME} (
    {Event}ID BIGINT IDENTITY(1,1) PRIMARY KEY,
    {Event}Date DATE NOT NULL,
    PortfolioID BIGINT,                          -- FK to DIM_PORTFOLIO
    SecurityID BIGINT,                           -- FK to DIM_SECURITY
    {MeasureColumn1} DECIMAL(38,10),
    {MeasureColumn2} DECIMAL(18,8),
    {CategoryColumn} VARCHAR(100),
    Currency CHAR(3) DEFAULT 'USD',
    SourceSystem VARCHAR(50),
    FOREIGN KEY (PortfolioID) REFERENCES DIM_PORTFOLIO(PortfolioID),
    FOREIGN KEY (SecurityID) REFERENCES DIM_SECURITY(SecurityID)
);
```

### Data Generation Function Template
```python
def build_{table_name}(session: Session, test_mode: bool = False):
    """Build {description} table using efficient SQL generation."""
    
    # CRITICAL: Extract config values before using in f-strings to avoid nested bracket issues
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.{TABLE_NAME} AS
        WITH base_data AS (
            SELECT 
                -- Base selection from existing tables
                {existing_table_joins}
        ),
        calculated_metrics AS (
            SELECT 
                *,
                -- Business logic calculations
                {calculated_fields}
            FROM base_data
        )
        SELECT * FROM calculated_metrics
    """).collect()
    
    log_detail(f"Created {table_name} with {specific_characteristics}")
```

### SQL Generation Best Practices

**CRITICAL RULES:**
1. **Never hardcode config values in SQL** - Use `config.get_demo_company_priority_sql()` and other helper functions
2. **Use data model columns** - Leverage `AssetClass`, `CountryOfIncorporation` instead of regex patterns
3. **Safe tuple generation** - Always use `config.safe_sql_tuple()` for IN clauses (handles empty lists)
4. **Extract config values** - Get dictionary values before f-string to avoid nested bracket syntax errors
5. **Use SQL case builders** - For numeric distributions, use `sql_case_builders.py` functions

```python
# ✅ CORRECT: Config-driven SQL with helper functions
CASE 
    {config.get_demo_company_priority_sql()}  -- Dynamic CASE from config
    WHEN s.Ticker IN {config.safe_sql_tuple(config.get_major_us_stocks('tier1'))} THEN 5
    WHEN i.CountryOfIncorporation = 'US' AND s.AssetClass = 'Equity' THEN 6
    ELSE 7
END

# ❌ WRONG: Hardcoded values and unsafe tuple generation
CASE 
    WHEN s.Ticker = 'AAPL' THEN 1  -- ❌ Hardcoded in SQL!
    WHEN s.Ticker IN {tuple(['MSFT', 'AAPL'])} THEN 5  -- ❌ Unsafe for empty lists!
    WHEN s.Ticker RLIKE '^[A-Z]{1,5}$' THEN 6  -- ❌ Use AssetClass instead!
    ELSE 7
END
```

### Config-Driven Numeric Distributions

For any function that generates synthetic data with sector/country/strategy-specific numeric ranges,
use `sql_case_builders.py` to generate CASE WHEN statements from config:

```python
from sql_case_builders import (
    build_sector_case_sql,
    build_country_group_case_sql,
    build_strategy_case_sql,
    build_grade_case_sql,
    build_global_uniform_sql
)

# ✅ CORRECT: Config-driven CASE WHEN
e_score_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'esg.E')
# → "CASE WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(60, 95, RANDOM()) ..."

# ✅ CORRECT: Config-driven strategy selection
rebalancing_sql = build_strategy_case_sql('p.Strategy', 'liquidity_by_strategy', 'rebalancing_days')
# → "CASE WHEN p.Strategy = 'Growth' THEN 90 ..."

# ❌ WRONG: Hardcoded numeric ranges
CASE 
    WHEN SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(60, 95, RANDOM())
    ELSE UNIFORM(40, 80, RANDOM())
END  # ❌ Hardcoded in SQL - should use config!
```

The config structure is defined in `config.DATA_MODEL['synthetic_distributions']`:
- `by_sector`: Sector-specific ranges (ESG, factors, transaction costs)
- `country_groups`: Country-group-specific ranges (ESG, settlement days)
- `global`: Strategy-based and global parameters (liquidity, risk, tax, calendar)

See @data-structured-build.mdc for full documentation.

### Batched I/O: Inserts and Lookups

**MANDATORY**: Never use loop-based INSERT statements. This is the #1 performance anti-pattern.

**ABSOLUTE RULE: No INSERT inside a for-loop. This applies to ALL data types — dimension tables, fact tables, corpus/document tables, and any other table. Every loop-based INSERT is a separate Snowflake query execution, making it orders of magnitude slower than batch alternatives.**

**Preferred patterns (in order of preference):**

1. **`session.create_dataframe(list_of_dicts).write.mode("append").save_as_table()`** — Best for Python-generated data with random/computed values per row. Build the full list in Python, then write once.
2. **Single SQL `INSERT INTO ... VALUES (...), (...), (...)`** — Best for small static config data (< 100 rows) from Python constants.
3. **Single SQL `INSERT INTO ... WITH cte AS (SELECT ... FROM VALUES ...) SELECT ... FROM cte JOIN ...`** — Best when you need to join config data with existing tables (e.g., resolving foreign keys).
4. **`CREATE OR REPLACE TABLE ... AS SELECT`** with CTEs, GENERATOR, CROSS JOIN — Best for pure SQL synthetic data generation (> 10K rows).

**Quick Reference:**
```python
# ✅ Pattern 1: Python-generated data with create_dataframe
rows = []
for item in items:
    rows.append({'COL1': computed_value, 'COL2': random.uniform(1, 10)})
df = session.create_dataframe(rows)
df.write.mode("append").save_as_table("DB.SCHEMA.TABLE")

# ✅ Pattern 2: Static config data with single VALUES INSERT
values_clause = ", ".join(f"('{r[0]}', {r[1]})" for r in config_list)
session.sql(f"INSERT INTO DB.SCHEMA.TABLE (Col1, Col2) VALUES {values_clause}").collect()

# ✅ Pattern 3: Config data needing FK resolution via JOIN
values_clause = ", ".join(f"('{name}', {val})" for name, val in items)
session.sql(f"""
    INSERT INTO DB.SCHEMA.CHILD_TABLE (ParentID, Name, Value)
    WITH src AS (SELECT column1 AS Name, column2 AS Value FROM VALUES {values_clause})
    SELECT p.ParentID, s.Name, s.Value
    FROM src s LEFT JOIN DB.SCHEMA.PARENT_TABLE p ON s.Name = p.Name
""").collect()

# ❌ NEVER do this — each iteration is a separate Snowflake query
for item in items:
    session.sql(f"INSERT INTO TABLE VALUES ('{item['name']}', {item['value']})").collect()
```

## Adding New Semantic Views

### YAML-Based Approach (Current)

All 28 semantic views are defined as YAML files in `python/ai/semantic_view_definitions/`. To add a new one:

**Step 1**: Create `python/ai/semantic_view_definitions/SAM_NEW_VIEW.yaml`:
```yaml
name: SAM_NEW_VIEW
description: "Description (becomes COMMENT on the view)"
tables:
  - name: TABLE_ALIAS
    description: Table description
    base_table:
      database: "{{DATABASE}}"
      schema: CURATED
      table: PHYSICAL_TABLE_NAME
    primary_key:
      columns:
        - PRIMARY_KEY_COL
    dimensions:
      - name: SemanticName
        expr: ACTUAL_COLUMN
        data_type: VARCHAR(134217728)
    facts:
      - name: FactName
        expr: ACTUAL_COLUMN
        data_type: FLOAT
        access_modifier: public_access
    metrics:
      - name: MetricName
        expr: SUM(FactName)
        access_modifier: public_access
```

**Step 2**: Add the view to `SCENARIO_VIEW_MAP` in `python/ai/semantic_views.py`:
```python
SCENARIO_VIEW_MAP = {
    'your_scenario': ['SAM_NEW_VIEW'],
    ...
}
```

**Step 3**: Validate and deploy:
```bash
# Validate YAML (dry run)
python main.py --connection-name CONNECTION --scope semantic --verify-only

# Deploy
python main.py --connection-name CONNECTION --scope semantic
```

**Step 4**: Export from an existing view (if migrating):
```sql
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('SAM_DEMO.AI.EXISTING_VIEW');
```
Save output as `.yaml`, replace `SAM_DEMO` with `{{DATABASE}}`.

### Semantic View Validation Template
```python
def validate_{view_name}_semantic_view(session: Session):
    """Validate semantic view functionality."""
    
    test_result = session.sql(f"""
        SELECT * FROM SEMANTIC_VIEW(
            {config.DATABASE['name']}.AI.{VIEW_NAME}
            METRICS {primary_metric}
            DIMENSIONS {primary_dimension}
        ) LIMIT 5
    """).collect()
    
    if len(test_result) > 0:
        log_detail(f"Semantic view {VIEW_NAME} validation passed")
    else:
        raise Exception(f"Semantic view {VIEW_NAME} validation failed")
```

## Adding New Cortex Search Services

### Search Service Creation Pattern
```python
def create_{service_name}_search_service(session: Session):
    """Create Cortex Search service for {document_type}."""
    
    service_sql = f"""
        CREATE OR REPLACE CORTEX SEARCH SERVICE {config.DATABASE['name']}.AI.SAM_{SERVICE_NAME}
            ON DOCUMENT_TEXT
            ATTRIBUTES DOCUMENT_TITLE, SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE
            WAREHOUSE = {config.WAREHOUSES['cortex_search']['name']}
            TARGET_LAG = '5 minutes'
            AS 
            SELECT 
                DOCUMENT_ID,
                DOCUMENT_TITLE,
                DOCUMENT_TEXT,
                SecurityID,
                IssuerID,
                DOCUMENT_TYPE,
                PUBLISH_DATE,
                LANGUAGE
            FROM {config.DATABASE['name']}.CURATED.{CORPUS_TABLE_NAME}
    """
    
    session.sql(service_sql).collect()
    log_detail(f"Created search service: SAM_{SERVICE_NAME}")
```

### Document Corpus Creation Pattern
```python
def create_{document_type}_corpus(session: Session, documents: List[dict]):
    """Create document corpus for {document_type}."""
    
    corpus_data = []
    for doc in documents:
        corpus_data.append({
            'DOCUMENT_ID': doc['id'],
            'DOCUMENT_TITLE': doc['title'],
            'DOCUMENT_TYPE': '{DOCUMENT_TYPE}',
            'SecurityID': doc.get('security_id'),
            'IssuerID': doc.get('issuer_id'), 
            'PUBLISH_DATE': doc['date'],
            'LANGUAGE': 'en',
            'DOCUMENT_TEXT': doc['content']
        })
    
    corpus_df = session.create_dataframe(corpus_data)
    corpus_df.write.mode("overwrite").save_as_table(
        f"{config.DATABASE['name']}.CURATED.{DOCUMENT_TYPE}_CORPUS"
    )
    
    log_detail(f"Created corpus table: {DOCUMENT_TYPE}_CORPUS")
```

## Adding New Agent Scenarios

### Architecture: config.py as Single Source of Truth

All scenario dependencies are declared in `python/config.py` in the `SCENARIOS` dict. **Never** hardcode scenario names, table lists, or agent names in other files. The subsystems (data builders, semantic views, search services, agents) all resolve what to build from config.

### Build Order (Guaranteed by main.py)

```
1. Tables     → all required tables for all scenarios (via TABLE_BUILDERS registry)
2. Views      → all required SQL views (security returns, attribution, etc.)
3. AI Objects → semantic views, search services, custom tools, agents
4. Apps       → Cockpit, Streamlit, notebooks
```

This order means: if a semantic view references a table, that table must be listed in `required_tables` for the scenario. The build pipeline guarantees tables exist before views are created.

### Adding a New Scenario: Step-by-Step

**1. Add entry to `config.py` SCENARIOS dict:**

```python
SCENARIOS = {
    ...
    'new_scenario': {
        'type': 'agent',                    # or 'ml' for notebook-based
        'name': 'New Scenario',
        'description': 'What this scenario does',
        'agent': {
            'name': 'AM_new_scenario_copilot',
            'display_name': 'New Scenario Copilot',
        },
        'required_data': ['doc_type_1', 'doc_type_2'],    # Document types for unstructured pipeline
        'required_tables': ['dimensions', 'fact_tables', 'new_tables'],  # Table group keys
        'data_phases': ['market_data'],                    # Data build phases needed
        'required_views': ['SAM_NEW_VIEW'],                # Semantic views
        'required_services': ['sec_filings'],              # Search service keys
        'required_tools': ['pdf_report', 'data_origin'],   # Tool group keys
    },
}
```

**2. If new tables are needed, add a builder to `data/structured.py`:**

```python
TABLE_BUILDERS = {
    ...
    'new_tables': build_new_scenario_tables,   # Add key matching required_tables entry
}
```

**3. Create the agent file in `ai/agents/new_scenario.py`**

**4. Register in `ai/agents/__init__.py`:**

```python
AGENT_CREATORS = {
    ...
    'new_scenario': create_new_scenario_agent,
}
```

**5. Create semantic view YAML in `ai/semantic_view_definitions/`**

**6. Add demo scenario documentation in `docs/demo_scenarios_new_scenario.md`**

That's it. No changes needed to `main.py`, `builder.py`, `semantic_views.py`, or `cortex_search.py` — they all read from config.

### Naming Convention

| Type | Pattern | Example |
|------|---------|---------|
| Scenario key | `{domain}` (lowercase, underscores) | `portfolio_management` |
| Agent name | `AM_{domain}_copilot` | `AM_portfolio_management_copilot` |
| Doc file | `demo_scenarios_{scenario_key}.md` | `demo_scenarios_portfolio_management.md` |
| ML scenario | `{domain}_ml` suffix | `market_regime_ml` |

### Rules

1. **config.py is the ONLY place** to declare scenario dependencies — no hardcoded scenario names in other files
2. **TABLE_BUILDERS registry** in `structured.py` is the ONLY place to map table group keys to builder functions
3. **AGENT_CREATORS** in `agents/__init__.py` is the ONLY place to map scenarios to agent creator functions
4. **Build order is tables -> views -> AI objects** — never create semantic views before their underlying tables
5. **No special-case `if scenario == 'x'` checks** in builder code — use config lookups instead

## Adding New Document Types

### Document Generation Pattern

**For complete unstructured data generation patterns, see @unstructured-data-generation.mdc**

The dedicated unstructured data generation rule provides:
- Standardized patterns for all 7 document types
- Content quality requirements and validation
- Proper SecurityID/IssuerID linkage patterns
- Agent-specific content alignment guidelines

## Performance and Testing Patterns

### Data Quality Validation Template
```python
def validate_{component}_data_quality(session: Session):
    """Validate data quality for {component}."""
    
    # Test 1: Check record counts
    count_check = session.sql(f"""
        SELECT COUNT(*) as record_count 
        FROM {table_name}
    """).collect()[0]['RECORD_COUNT']
    
    assert count_check > 0, f"No records found in {table_name}"
    
    # Test 2: Check data integrity
    integrity_check = session.sql(f"""
        SELECT COUNT(*) as issues
        FROM {table_name}
        WHERE {integrity_conditions}
    """).collect()[0]['ISSUES']
    
    assert integrity_check == 0, f"Data integrity issues found: {integrity_check}"
    
    log_detail(f"Data quality validation passed for {component}")
```

### Component Testing Template  
```python
def test_{component}_functionality(session: Session):
    """Test {component} end-to-end functionality."""
    
    try:
        # Test basic functionality
        result = session.sql(f"""
            {test_query}
        """).collect()
        
        assert len(result) > 0, "No results returned"
        
        # Test specific business logic
        {specific_tests}
        
        log_detail(f"{component} functionality test passed")
        return True
        
    except Exception as e:
        log_error(f"{component} functionality test failed: {e}")
        return False
```

## Configuration Management Patterns

### Adding New Configuration Options
```python
# In config.py - add new configuration constants
{NEW_FEATURE}_ENABLED = True
{NEW_FEATURE}_CONFIG = {
    'setting1': 'value1',
    'setting2': 'value2'
}

# Document pattern in docstring
"""
{NEW_FEATURE} Configuration:
- {NEW_FEATURE}_ENABLED: Enable/disable the feature
- {NEW_FEATURE}_CONFIG: Feature-specific settings
"""
```

### CLI Integration Pattern
```python
# In main.py - add new CLI arguments
parser.add_argument(
    '--{new-flag}',
    action='store_true',
    help='{Description of what this flag does}'
)

# Handle the flag in main logic
if args.{new_flag}:
    log_step("{Action description}")
    result = {function_call}(session)
    if result:
        log_phase_complete("{Success message}")
    else:
        log_error("{Failure message}")
        return
```

This patterns guide provides complete templates for extending any aspect of the SAM demo without requiring chat history context.

**Related Documentation**:
- Agent Setup: `docs/agents_setup.md` - Complete agent configurations for all phases
- Demo Scripts: `docs/demo_scenarios.md` - Step-by-step demo conversation flows
- Troubleshooting: @troubleshooting.mdc - Issue resolution guide
- Pipelines: @pipelines.mdc - Production-like pipeline patterns and Streamlit deployment
- Production Pipelines Demo: `docs/production_pipelines_demo.md` - Pipeline demo runbook