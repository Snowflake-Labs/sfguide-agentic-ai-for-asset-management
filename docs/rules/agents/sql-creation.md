# Agent SQL Creation Patterns

Patterns for creating Snowflake Intelligence agents using `CREATE AGENT` SQL statements.

## Basic Structure

```python
def create_agent(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    sql = f"""
    CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_agent_name
      COMMENT = 'Agent description'
      PROFILE = '{{"display_name": "Agent Display Name"}}'
      FROM SPECIFICATION $$
      models:
        orchestration: claude-sonnet-4-5
      instructions:
        response: "Response instructions here"
        orchestration: "Planning instructions here"
      tools:
        - tool_spec:
            type: "cortex_analyst_text_to_sql"
            name: "tool_name"
            description: "Tool description"
      tool_resources:
        tool_name:
          semantic_view: "{database_name}.AI.SAM_VIEW"
          execution_environment:
            type: "warehouse"
            warehouse: "{config.WAREHOUSES['execution']['name']}"
      $$;
    """
    session.sql(sql).collect()
```

## YAML Escaping (Critical)

Multi-line instructions must be escaped for YAML within SQL:

```python
def format_instructions_for_yaml(text: str) -> str:
    """Format multi-line instructions for YAML within SQL."""
    formatted = text.replace('\n', '\\n')      # Line breaks
    formatted = formatted.replace('"', '\\"')  # Double quotes
    formatted = formatted.replace("'", "''")   # Single quotes (SQL escaping)
    return formatted
```

**Example transformation**:
```python
# Input
"""Style:
- Tone: Professional
- Example: "This is a quote"
"""

# Output
"Style:\\n- Tone: Professional\\n- Example: \\\"This is a quote\\\""
```

## Tool Spec Types

### Cortex Analyst (Structured Data)

```yaml
tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "quantitative_analyzer"
      description: |
        Analyzes portfolio holdings using 14,000+ real securities.
        
        Data Coverage:
        - Historical: 12 months position history
        - Refresh: Daily at 4 PM ET
        
        When to Use:
        - Portfolio holdings and weights
        - Sector allocation analysis
        - Concentration analysis
        
        When NOT to Use:
        - Real-time intraday positions
        - Document content questions

tool_resources:
  quantitative_analyzer:
    semantic_view: "SAM_DEMO.AI.SAM_PORTFOLIO_VIEW"
    execution_environment:
      query_timeout: 30
      type: "warehouse"
      warehouse: "SAM_DEMO_EXECUTION_WH"
```

### Cortex Search (Document Search)

```yaml
tools:
  - tool_spec:
      type: "cortex_search"
      name: "search_broker_research"
      description: |
        Searches broker research reports for analyst opinions and ratings.
        
        When to Use:
        - Analyst views and price targets
        - Investment thesis research
        
        When NOT to Use:
        - Portfolio holdings (use quantitative_analyzer)
        - Financial statements (use sec_financials)

tool_resources:
  search_broker_research:
    search_service: "SAM_DEMO.AI.SAM_BROKER_RESEARCH"
    id_column: "DOCUMENT_ID"
    title_column: "DOCUMENT_TITLE"
    max_results: 4
```

### Custom Tool (Python UDF/Procedure)

```yaml
tools:
  - tool_spec:
      type: "generic"                    # NOT "snowflake_function"
      name: "ma_simulation"
      description: "Runs M&A financial simulation"
      input_schema:
        type: "object"
        properties:
          target_aum:
            description: "Target company AUM in billions"
            type: "number"
          acquisition_premium:
            description: "Premium percentage (e.g., 0.25 for 25%)"
            type: "number"
        required:
          - target_aum

tool_resources:
  ma_simulation:
    execution_environment:
      query_timeout: 30
      type: "warehouse"
      warehouse: "SAM_DEMO_EXECUTION_WH"
    identifier: "SAM_DEMO.AI.MA_SIMULATION_TOOL"
    name: "MA_SIMULATION_TOOL(FLOAT, FLOAT)"    # Full signature required
    type: "function"                             # or "procedure"
```

## Agent Registration

After creation, register with Snowflake Intelligence:

```sql
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT 
ADD AGENT SAM_DEMO.AI.AM_portfolio_manager_copilot;
```

This is automated in `create_agents.py`.

## Multi-Tool Agent Example

```python
def create_portfolio_copilot(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    warehouse = config.WAREHOUSES['execution']['name']
    
    response_instructions = format_instructions_for_yaml("""
Style:
- Professional, data-driven tone
- UK English terminology
- Tables for >4 items

Format:
- Lead with direct answer
- Include data freshness date
- Flag concentrations >6.5%
""")
    
    orchestration_instructions = format_instructions_for_yaml("""
Tool Selection:
1. Holdings/weights/allocations → quantitative_analyzer
2. Research/analyst views → search_broker_research
3. Mixed questions → analyst first, then search

Workflows:
- Concentration check: Get holdings, apply 6.5% threshold, flag
- Research synthesis: Search documents, cite sources
""")
    
    sql = f"""
    CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_portfolio_manager_copilot
      COMMENT = 'Portfolio analytics with research integration'
      PROFILE = '{{"display_name": "Portfolio Manager Co-Pilot"}}'
      FROM SPECIFICATION $$
      models:
        orchestration: claude-sonnet-4-5
      instructions:
        response: "{response_instructions}"
        orchestration: "{orchestration_instructions}"
      tools:
        - tool_spec:
            type: "cortex_analyst_text_to_sql"
            name: "quantitative_analyzer"
            description: "Analyzes portfolio holdings..."
        - tool_spec:
            type: "cortex_search"
            name: "search_broker_research"
            description: "Searches broker research..."
      tool_resources:
        quantitative_analyzer:
          semantic_view: "{database_name}.AI.SAM_PORTFOLIO_VIEW"
          execution_environment:
            type: "warehouse"
            warehouse: "{warehouse}"
        search_broker_research:
          search_service: "{database_name}.AI.SAM_BROKER_RESEARCH"
          max_results: 4
      $$;
    """
    session.sql(sql).collect()
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid JSON` | Unescaped quotes in YAML | Use `format_instructions_for_yaml()` |
| `agent not found` | Not registered | Run `ALTER SNOWFLAKE INTELLIGENCE ADD AGENT` |
| `semantic view not found` | Wrong path | Use `{database}.{schema}.{view_name}` |
| `tool_spec type invalid` | Wrong type for custom tool | Use `"generic"` not `"snowflake_function"` |

## Adding New Agents

1. Create function in `create_agents.py`:
   ```python
   def create_new_agent(session: Session):
       # ... agent creation logic
   ```

2. Add to `get_agent_instructions()`:
   ```python
   'new_agent': {
       'response': get_new_agent_response_instructions(),
       'orchestration': get_new_agent_orchestration_instructions()
   }
   ```

3. Add to `create_all_agents()`:
   ```python
   agents_to_create = {
       'pm_cockpit': create_pm_cockpit,
       'new_agent': create_new_agent,  # Add here
   }
   ```
