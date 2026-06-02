"""
Generate SQL scripts for deployment.

Creates 6 SQL scripts for deploying a scenario package:
1. 01_create_objects.sql - Database, schemas, stages, tables
2. 02_load_data.sql - PUT + COPY INTO statements
3. 03_semantic_views.sql - CREATE SEMANTIC VIEW statements
4. 04_search_services.sql - CREATE CORTEX SEARCH SERVICE statements
5. 05_custom_tools.sql - CREATE PROCEDURE statements for custom tools
6. 06_create_agents.sql - CREATE AGENT statement
"""

from pathlib import Path
from snowflake.snowpark import Session
import config
from utils.logging import log_detail


def generate_all_scripts(session, scenario_name, requirements, table_schemas, output_dir):
    """
    Generate all SQL scripts for the scenario.
    
    Args:
        session: Active Snowpark session
        scenario_name: Name of scenario
        requirements: Dict from manifest.get_requirements()
        table_schemas: Dict from to_csv.get_all_table_schemas()
        output_dir: Path to output directory
    """
    log_detail("Generating 01_create_objects.sql...")
    generate_01_create_objects(scenario_name, requirements, table_schemas, output_dir)
    
    log_detail("Generating 02_load_data.sql...")
    generate_02_load_data(requirements, output_dir)
    
    log_detail("Generating 03_semantic_views.sql...")
    generate_03_semantic_views(session, requirements, output_dir)
    
    log_detail("Generating 04_search_services.sql...")
    generate_04_search_services(session, requirements, output_dir)
    
    log_detail("Generating 05_custom_tools.sql...")
    generate_05_custom_tools(session, requirements, output_dir)
    
    log_detail("Generating 06_create_agents.sql...")
    generate_06_agents(session, scenario_name, output_dir)


def generate_01_create_objects(scenario_name, requirements, table_schemas, output_dir):
    """Generate CREATE DATABASE/SCHEMA/TABLE statements."""
    agent_info = config.SCENARIO_AGENTS.get(scenario_name, {})
    display_name = agent_info.get('display_name', scenario_name)
    
    db_name = config.DATABASE['name']
    
    lines = [
        "-- ============================================",
        f"-- SAM AI Demo - {display_name}",
        "-- Script 1: Create Database Objects",
        "-- Execute: snow sql -f 01_create_objects.sql",
        f"-- NOTE: Find/replace '{db_name}' to change target database",
        "-- ============================================",
        "",
        "-- Configuration",
        "USE WAREHOUSE COMPUTE_WH;  -- Change as needed",
        "",
        "-- Create database and schemas",
        f"CREATE DATABASE IF NOT EXISTS {db_name};",
        f"CREATE SCHEMA IF NOT EXISTS {db_name}.RAW;",
        f"CREATE SCHEMA IF NOT EXISTS {db_name}.CURATED;",
        f"CREATE SCHEMA IF NOT EXISTS {db_name}.AI;",
        f"CREATE SCHEMA IF NOT EXISTS {db_name}.MARKET_DATA;",
        "",
        "-- Create internal stage for CSV loading",
        f"CREATE STAGE IF NOT EXISTS {db_name}.RAW.SETUP_STAGE",
        "    FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '\"' SKIP_HEADER = 1);",
        "",
    ]
    
    for (schema, table_name), columns in table_schemas.items():
        if not columns:
            continue
        
        lines.append(f"-- Table: {schema}.{table_name}")
        lines.append(f"CREATE TABLE IF NOT EXISTS {db_name}.{schema}.{table_name} (")
        
        col_defs = []
        for col_name, col_type in columns:
            col_defs.append(f"    {col_name} {col_type}")
        
        lines.append(",\n".join(col_defs))
        lines.append(");")
        lines.append("")
    
    script_path = Path(output_dir) / "01_create_objects.sql"
    script_path.write_text("\n".join(lines))


def generate_02_load_data(requirements, output_dir):
    """Generate PUT + COPY INTO statements."""
    db_name = config.DATABASE['name']
    
    lines = [
        "-- ============================================",
        "-- Script 2: Load CSV Data",
        "-- Execute: snow sql -f 02_load_data.sql",
        "-- NOTE: Run this from the package directory",
        f"-- NOTE: Find/replace '{db_name}' to change target database",
        "-- ============================================",
        "",
        "USE WAREHOUSE COMPUTE_WH;  -- Change as needed",
        f"USE DATABASE {db_name};",
        "",
    ]
    
    all_tables = []
    for schema, tables in requirements['tables'].items():
        for table_name in tables:
            all_tables.append((schema, table_name))
    
    for table_name in requirements.get('corpus_tables', []):
        all_tables.append(('CURATED', table_name))
    
    for schema, table_name in all_tables:
        csv_file = f"data/{table_name.lower()}.csv"
        stage_path = f"@{db_name}.RAW.SETUP_STAGE/{table_name.lower()}"
        
        lines.extend([
            f"-- Load {table_name}",
            f"PUT file://{csv_file} {stage_path}/ AUTO_COMPRESS=TRUE OVERWRITE=TRUE;",
            f"COPY INTO {db_name}.{schema}.{table_name}",
            f"    FROM {stage_path}/",
            "    FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '\"' SKIP_HEADER = 1 NULL_IF = (''))",
            "    ON_ERROR = 'CONTINUE';",
            "",
        ])
    
    script_path = Path(output_dir) / "02_load_data.sql"
    script_path.write_text("\n".join(lines))


def generate_03_semantic_views(session, requirements, output_dir):
    """Extract semantic view YAML definitions and generate CREATE statements."""
    db_name = config.DATABASE['name']
    semantic_views = requirements.get('semantic_views', [])
    
    # Create semantic_views subdirectory for YAML files (for reference)
    yaml_dir = Path(output_dir) / "semantic_views"
    yaml_dir.mkdir(exist_ok=True)
    
    lines = [
        "-- ============================================",
        "-- Script 3: Create Semantic Views",
        "-- Execute: snow sql -f 03_semantic_views.sql",
        f"-- NOTE: Find/replace '{db_name}' to change target database",
        "-- YAML files are also saved in semantic_views/ for reference",
        "-- ============================================",
        "",
        "USE WAREHOUSE COMPUTE_WH;  -- Change as needed",
        f"USE DATABASE {db_name};",
        f"USE SCHEMA {db_name}.AI;",
        "",
    ]
    
    if not semantic_views:
        lines.append("-- No semantic views required for this scenario")
    
    for view_name in semantic_views:
        full_name = f"{db_name}.AI.{view_name}"
        yaml_filename = f"{view_name.lower()}.yaml"
        
        try:
            # Extract YAML using SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW
            result = session.sql(f"SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('{full_name}') AS YAML").collect()
            if result:
                yaml_content = result[0]['YAML']
                
                # Save YAML to file for reference
                yaml_path = yaml_dir / yaml_filename
                yaml_path.write_text(yaml_content)
                
                # Embed YAML inline in SQL using $$ delimiters
                # First param is schema path (database.schema), view name comes from YAML
                lines.extend([
                    f"-- Semantic View: {view_name}",
                    f"CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('{db_name}.AI',",
                    "$$",
                    yaml_content,
                    "$$);",
                    "",
                ])
        except Exception as e:
            lines.extend([
                f"-- Semantic View: {view_name}",
                f"-- ERROR: Could not extract YAML - {str(e)[:100]}",
                f"-- Manual creation required from ai/semantic_views.py",
                "",
            ])
    
    script_path = Path(output_dir) / "03_semantic_views.sql"
    script_path.write_text("\n".join(lines))


def generate_04_search_services(session, requirements, output_dir):
    """Generate CREATE CORTEX SEARCH SERVICE statements."""
    db_name = config.DATABASE['name']
    search_warehouse = config.WAREHOUSES['cortex_search']['name']
    
    lines = [
        "-- ============================================",
        "-- Script 4: Create Cortex Search Services",
        "-- Execute: snow sql -f 04_search_services.sql",
        f"-- NOTE: Find/replace '{db_name}' to change target database",
        "-- ============================================",
        "",
        "USE WAREHOUSE COMPUTE_WH;  -- Change as needed",
        f"USE DATABASE {db_name};",
        f"USE SCHEMA {db_name}.AI;",
        "",
    ]
    target_lag = config.WAREHOUSES['cortex_search']['target_lag']
    
    for service_name in requirements.get('search_services', []):
        full_name = f"{db_name}.AI.{service_name}"
        
        try:
            result = session.sql(f"SELECT GET_DDL('CORTEX SEARCH SERVICE', '{full_name}') AS DDL").collect()
            if result:
                ddl = result[0]['DDL']
                
                lines.extend([
                    f"-- Search Service: {service_name}",
                    ddl,
                    "",
                ])
        except Exception as e:
            corpus_table = _get_corpus_for_service(service_name)
            lines.extend([
                f"-- Search Service: {service_name}",
                f"-- NOTE: Could not extract DDL - creating basic service",
                f"CREATE OR REPLACE CORTEX SEARCH SERVICE {db_name}.AI.{service_name}",
                "    ON DOCUMENT_TEXT",
                "    ATTRIBUTES DOCUMENT_TITLE, DOCUMENT_TYPE, PUBLISH_DATE",
                f"    WAREHOUSE = {search_warehouse}",
                f"    TARGET_LAG = '{target_lag}'",
                f"    AS SELECT * FROM {db_name}.CURATED.{corpus_table};",
                "",
            ])
    
    script_path = Path(output_dir) / "04_search_services.sql"
    script_path.write_text("\n".join(lines))


def generate_05_custom_tools(session, requirements, output_dir):
    """Extract custom tool/procedure definitions."""
    db_name = config.DATABASE['name']
    
    lines = [
        "-- ============================================",
        "-- Script 5: Create Custom Tools (Procedures)",
        "-- Execute: snow sql -f 05_custom_tools.sql",
        f"-- NOTE: Find/replace '{db_name}' to change target database",
        "-- ============================================",
        "",
        "USE WAREHOUSE COMPUTE_WH;  -- Change as needed",
        f"USE DATABASE {db_name};",
        f"USE SCHEMA {db_name}.AI;",
        "",
    ]
    custom_tools = requirements.get('custom_tools', [])
    
    if not custom_tools:
        lines.append("-- No custom tools required for this scenario")
    else:
        for tool_name in custom_tools:
            full_name = f"{db_name}.AI.{tool_name}"
            
            # Try to get DDL from Snowflake first (try PROCEDURE then FUNCTION)
            ddl = None
            try:
                result = session.sql(f"SELECT GET_DDL('PROCEDURE', '{full_name}') AS DDL").collect()
                if result:
                    ddl = result[0]['DDL']
            except Exception:
                pass
            
            if not ddl:
                try:
                    result = session.sql(f"SELECT GET_DDL('FUNCTION', '{full_name}') AS DDL").collect()
                    if result:
                        ddl = result[0]['DDL']
                except Exception:
                    pass
            
            if ddl:
                lines.extend([
                    f"-- Custom Tool: {tool_name}",
                    ddl,
                    "",
                ])
            else:
                # Fall back to embedded procedure definitions
                fallback_ddl = _get_fallback_procedure_ddl(tool_name, db_name)
                if fallback_ddl:
                    lines.extend([
                        f"-- Custom Tool: {tool_name}",
                        f"-- (Generated from builder.py - procedure not found in Snowflake)",
                        fallback_ddl,
                        "",
                    ])
                else:
                    lines.extend([
                        f"-- Custom Tool: {tool_name}",
                        f"-- ERROR: Procedure not found in Snowflake and no fallback available",
                        f"-- Run the demo setup first to create this procedure, or check ai/builder.py",
                        "",
                    ])
    
    script_path = Path(output_dir) / "05_custom_tools.sql"
    script_path.write_text("\n".join(lines))


def _get_fallback_procedure_ddl(tool_name, db_name):
    """Get fallback DDL for procedures that don't exist in Snowflake yet."""
    
    # These are extracted from ai/builder.py
    procedures = {
        'RUN_STRESS_BACKTEST_TOOL': f'''CREATE OR REPLACE PROCEDURE {db_name}.AI.RUN_STRESS_BACKTEST_TOOL(
    portfolio_id INTEGER,
    stress_period_id VARCHAR
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_stress_backtest'
EXECUTE AS CALLER
AS
$$
def run_stress_backtest(session, portfolio_id, stress_period_id):
    \'\'\'Calculate portfolio performance during historical stress period.\'\'\'
    
    # Get stress period details
    period = session.sql(f\'\'\'
        SELECT PERIOD_ID, START_DATE, END_DATE, DESCRIPTION, 
               DURATION_DAYS, MARKET_RETURN, PEAK_VIX, LINKED_SCENARIO_ID
        FROM {db_name}.CURATED.FACT_HISTORICAL_STRESS_PERIODS
        WHERE PERIOD_ID = '{{stress_period_id}}'
    \'\'\').collect()
    
    if not period:
        return {{"error": f"Stress period '{{stress_period_id}}' not found. Valid periods: COVID_CRASH, GFC, TAPER_TANTRUM, RATE_HIKE_2022, BANKING_CRISIS_2023"}}
    
    p = period[0]
    
    # Get factor exposures for portfolio
    exposures = session.sql(f\'\'\'
        SELECT FACTOR_NAME, AVG(PORTFOLIO_FACTOR_EXPOSURE) as AVG_EXPOSURE
        FROM {db_name}.CURATED.FACT_FACTOR_ATTRIBUTION
        WHERE PORTFOLIOID = {{portfolio_id}}
        GROUP BY FACTOR_NAME
    \'\'\').collect()
    
    if not exposures:
        return {{"error": f"No factor exposures found for portfolio {{portfolio_id}}"}}
    
    # Get scenario shocks for linked scenario
    shocks = session.sql(f\'\'\'
        SELECT FACTOR_NAME, FACTOR_SHOCK, CONFIDENCE_LEVEL
        FROM {db_name}.CURATED.FACT_SCENARIO_SHOCKS
        WHERE SCENARIO_ID = {{p['LINKED_SCENARIO_ID']}}
    \'\'\').collect()
    
    # Calculate estimated portfolio impact
    shock_map = {{s['FACTOR_NAME']: (float(s['FACTOR_SHOCK']), float(s['CONFIDENCE_LEVEL'])) for s in shocks}}
    
    total_impact = 0
    weighted_confidence = 0
    total_weight = 0
    factor_impacts = {{}}
    
    for exp in exposures:
        factor = exp['FACTOR_NAME']
        exposure = float(exp['AVG_EXPOSURE'] or 0)
        if factor in shock_map:
            shock, confidence = shock_map[factor]
            impact = exposure * shock
            factor_impacts[factor] = {{
                "exposure": round(exposure, 3),
                "shock_pct": round(shock * 100, 1),
                "impact_pct": round(impact * 100, 2),
                "confidence": round(confidence, 2)
            }}
            total_impact += impact
            weighted_confidence += confidence * abs(impact)
            total_weight += abs(impact)
        else:
            factor_impacts[factor] = {{
                "exposure": round(exposure, 3),
                "shock_pct": 0,
                "impact_pct": 0,
                "confidence": 0,
                "note": "No shock defined for this factor in scenario"
            }}
    
    avg_confidence = weighted_confidence / total_weight if total_weight > 0 else 0
    market_return = float(p['MARKET_RETURN'])
    
    return {{
        "stress_period": {{
            "id": p['PERIOD_ID'],
            "description": p['DESCRIPTION'],
            "start_date": str(p['START_DATE']),
            "end_date": str(p['END_DATE']),
            "duration_days": int(p['DURATION_DAYS']),
            "market_return_pct": round(market_return * 100, 1),
            "peak_vix": float(p['PEAK_VIX'])
        }},
        "portfolio_analysis": {{
            "portfolio_id": portfolio_id,
            "estimated_return_pct": round(total_impact * 100, 2),
            "vs_market_pct": round((total_impact - market_return) * 100, 2),
            "outperforms_market": total_impact > market_return,
            "analysis_confidence": round(avg_confidence, 2)
        }},
        "factor_contributions": factor_impacts,
        "interpretation": f"Portfolio {{portfolio_id}} estimated to return {{round(total_impact * 100, 1)}}% during {{p['DESCRIPTION']}} (market: {{round(market_return * 100, 1)}}%). " +
                         ("Portfolio would outperform market by " if total_impact > market_return else "Portfolio would underperform market by ") +
                         f"{{abs(round((total_impact - market_return) * 100, 1))}}%."
    }}
$$;''',
        
        'RUN_BACKTEST_TOOL': f'''CREATE OR REPLACE PROCEDURE {db_name}.AI.RUN_BACKTEST_TOOL(
    model_portfolio_id INTEGER,
    start_date DATE,
    end_date DATE
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_backtest'
EXECUTE AS CALLER
AS
$$
def run_backtest(session, model_portfolio_id, start_date, end_date):
    \'\'\'Run backtest for a model portfolio over specified period.\'\'\'
    result = session.sql(f\'\'\'
        SELECT AVG(TOTAL_RETURN) as avg_return, 
               STDDEV(TOTAL_RETURN) as volatility,
               MIN(TOTAL_RETURN) as max_drawdown
        FROM {db_name}.CURATED.FACT_BACKTEST_RESULTS 
        WHERE MODEL_PORTFOLIO_ID = {{model_portfolio_id}}
        AND DATE BETWEEN '{{start_date}}' AND '{{end_date}}'
    \'\'\').collect()
    
    if not result or result[0]['AVG_RETURN'] is None:
        return {{"error": f"No backtest data for model portfolio {{model_portfolio_id}}"}}
    
    r = result[0]
    return {{
        "model_portfolio_id": model_portfolio_id,
        "period": {{"start": str(start_date), "end": str(end_date)}},
        "average_return_pct": round(float(r['AVG_RETURN'] or 0) * 100, 2),
        "volatility_pct": round(float(r['VOLATILITY'] or 0) * 100, 2),
        "max_drawdown_pct": round(float(r['MAX_DRAWDOWN'] or 0) * 100, 2)
    }}
$$;''',

        'RUN_MONTE_CARLO_TOOL': f'''CREATE OR REPLACE PROCEDURE {db_name}.AI.RUN_MONTE_CARLO_TOOL(
    model_portfolio_id INTEGER,
    num_simulations INTEGER
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_monte_carlo'
EXECUTE AS CALLER
AS
$$
def run_monte_carlo(session, model_portfolio_id, num_simulations):
    \'\'\'Run Monte Carlo simulation for a model portfolio.\'\'\'
    result = session.sql(f\'\'\'
        SELECT PERCENTILE_5, PERCENTILE_25, PERCENTILE_50, PERCENTILE_75, PERCENTILE_95,
               EXPECTED_RETURN, VAR_95, CVAR_95
        FROM {db_name}.CURATED.FACT_SIMULATION_RESULTS 
        WHERE MODEL_PORTFOLIO_ID = {{model_portfolio_id}}
        ORDER BY SIMULATION_DATE DESC LIMIT 1
    \'\'\').collect()
    
    if not result:
        return {{"error": f"No simulation data for model portfolio {{model_portfolio_id}}"}}
    
    r = result[0]
    return {{
        "model_portfolio_id": model_portfolio_id,
        "simulations": num_simulations,
        "percentiles": {{
            "p5": round(float(r['PERCENTILE_5'] or 0) * 100, 2),
            "p25": round(float(r['PERCENTILE_25'] or 0) * 100, 2),
            "p50": round(float(r['PERCENTILE_50'] or 0) * 100, 2),
            "p75": round(float(r['PERCENTILE_75'] or 0) * 100, 2),
            "p95": round(float(r['PERCENTILE_95'] or 0) * 100, 2)
        }},
        "expected_return_pct": round(float(r['EXPECTED_RETURN'] or 0) * 100, 2),
        "var_95_pct": round(float(r['VAR_95'] or 0) * 100, 2),
        "cvar_95_pct": round(float(r['CVAR_95'] or 0) * 100, 2)
    }}
$$;''',

        'RUN_ATTRIBUTION_TOOL': f'''CREATE OR REPLACE PROCEDURE {db_name}.AI.RUN_ATTRIBUTION_TOOL(
    portfolio_id INTEGER,
    start_date DATE,
    end_date DATE
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_attribution'
EXECUTE AS CALLER
AS
$$
def run_attribution(session, portfolio_id, start_date, end_date):
    \'\'\'Run attribution analysis for a portfolio.\'\'\'
    result = session.sql(f\'\'\'
        SELECT SUM(ALLOCATION_EFFECT) as allocation,
               SUM(SELECTION_EFFECT) as selection,
               SUM(INTERACTION_EFFECT) as interaction,
               SUM(ACTIVE_RETURN) as active_return
        FROM {db_name}.CURATED.FACT_BRINSON_ATTRIBUTION 
        WHERE PORTFOLIOID = {{portfolio_id}}
        AND DATE BETWEEN '{{start_date}}' AND '{{end_date}}'
    \'\'\').collect()
    
    if not result or result[0]['ACTIVE_RETURN'] is None:
        return {{"error": f"No attribution data for portfolio {{portfolio_id}}"}}
    
    r = result[0]
    return {{
        "portfolio_id": portfolio_id,
        "period": {{"start": str(start_date), "end": str(end_date)}},
        "allocation_effect_pct": round(float(r['ALLOCATION'] or 0) * 100, 2),
        "selection_effect_pct": round(float(r['SELECTION'] or 0) * 100, 2),
        "interaction_effect_pct": round(float(r['INTERACTION'] or 0) * 100, 2),
        "active_return_pct": round(float(r['ACTIVE_RETURN'] or 0) * 100, 2)
    }}
$$;'''
    }
    
    return procedures.get(tool_name)


def generate_06_agents(session, scenario_name, output_dir):
    """Extract agent definition and generate CREATE AGENT statement."""
    db_name = config.DATABASE['name']
    agent_info = config.SCENARIO_AGENTS.get(scenario_name, {})
    agent_name = agent_info.get('agent_name', f'AM_{scenario_name}')
    full_name = f"{db_name}.AI.{agent_name}"
    
    lines = [
        "-- ============================================",
        "-- Script 6: Create Agent",
        "-- Execute: snow sql -f 06_create_agents.sql",
        f"-- NOTE: Find/replace '{db_name}' to change target database",
        "-- ============================================",
        "",
        "USE WAREHOUSE COMPUTE_WH;  -- Change as needed",
        f"USE DATABASE {db_name};",
        f"USE SCHEMA {db_name}.AI;",
        "",
    ]
    
    # Try to get DDL from Snowflake first
    ddl = None
    ddl_is_valid = False
    try:
        result = session.sql(f"SELECT GET_DDL('CORTEX_AGENT', '{full_name}') AS DDL").collect()
        if result:
            ddl = result[0]['DDL']
            # Check if DDL is corrupted - GET_DDL sometimes mangles the YAML specification:
            # 1. Newlines in strings become literal 'n' (nnStyle, nn1., etc.)
            # 2. Uses YAML line continuation with backslash which may not parse correctly
            # Look for these patterns to detect corruption
            if ddl:
                has_broken_newlines = ('nnStyle' in ddl or 'nn1.' in ddl or 'nn2.' in ddl or 'nn-' in ddl)
                has_yaml_continuation = ('\\\n' in ddl or '\\ ' in ddl)
                if not has_broken_newlines and not has_yaml_continuation:
                    ddl_is_valid = True
                else:
                    log_detail(f"  GET_DDL returned reformatted agent spec, using fallback")
    except Exception:
        pass
    
    if ddl and ddl_is_valid:
        # Comment out any ALTER SNOWFLAKE INTELLIGENCE statements that may be in the DDL
        # GET_DDL may return these as part of the agent definition
        ddl_lines = ddl.split('\n')
        cleaned_ddl_lines = []
        skip_next = False
        for line in ddl_lines:
            upper_line = line.upper().strip()
            # Check for ALTER SNOWFLAKE INTELLIGENCE (may span multiple lines)
            if 'ALTER SNOWFLAKE INTELLIGENCE' in upper_line:
                cleaned_ddl_lines.append(f"-- {line}")
                skip_next = True  # The ADD AGENT line usually follows
            elif skip_next and ('ADD AGENT' in upper_line or upper_line.startswith('ADD ')):
                cleaned_ddl_lines.append(f"-- {line}")
                skip_next = False
            elif 'ADD AGENT' in upper_line and 'ALTER' not in upper_line:
                # Standalone ADD AGENT line
                cleaned_ddl_lines.append(f"-- {line}")
            else:
                cleaned_ddl_lines.append(line)
                skip_next = False
        ddl = '\n'.join(cleaned_ddl_lines)
        
        lines.extend([
            f"-- Agent: {agent_name}",
            ddl,
            "",
        ])
        
        # Don't add duplicate ALTER statement since DDL may already contain it
        lines.extend([
            "",
            "-- Register agent with Snowflake Intelligence (optional, uncomment if needed)",
            f"-- ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT",
            f"--     ADD AGENT {db_name}.AI.{agent_name};",
        ])
    else:
        # Fall back to generating from agents.py
        fallback_sql = _get_fallback_agent_sql(scenario_name, db_name)
        if fallback_sql:
            lines.extend([
                f"-- Agent: {agent_name}",
                f"-- (Generated from agents.py - agent not found in Snowflake)",
                fallback_sql,
                "",
            ])
        else:
            lines.extend([
                f"-- Agent: {agent_name}",
                f"-- ERROR: Agent not found in Snowflake and no fallback available",
                f"-- Run the demo setup first to create this agent, or check ai/agents.py",
                "",
            ])
        
        # Add ALTER statement (commented) for non-DDL cases
        lines.extend([
            "",
            "-- Register agent with Snowflake Intelligence (optional)",
            f"-- ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT",
            f"--     ADD AGENT {db_name}.AI.{agent_name};",
        ])
    
    script_path = Path(output_dir) / "06_create_agents.sql"
    script_path.write_text("\n".join(lines))


def _get_fallback_agent_sql(scenario_name, db_name):
    """
    Get fallback CREATE AGENT SQL from agents.py for scenarios where the agent doesn't exist.
    
    This imports the agent module and extracts the SQL template along with instructions,
    then properly formats and substitutes all placeholders.
    """
    try:
        from ai import agents as agent_module
        from ai.agents import format_instructions_for_yaml
        
        # Map scenario names to agent creation functions
        function_map = {
            'portfolio_copilot': 'create_portfolio_copilot',
            'research_copilot': 'create_research_copilot',
            'thematic_macro_advisor': 'create_thematic_macro_advisor',
            'esg_guardian': 'create_esg_guardian',
            'compliance_advisor': 'create_compliance_advisor',
            'sales_advisor': 'create_sales_advisor',
            'quant_analyst': 'create_quant_analyst',
            'middle_office_copilot': 'create_middle_office_copilot',
            'executive_copilot': 'create_executive_copilot',
            'portfolio_modelling_copilot': 'create_portfolio_modelling_copilot',
            'pe_deal_sourcing': 'create_pe_deal_sourcing',
            'pe_portfolio_monitor': 'create_pe_portfolio_monitor',
            'attribution_intelligence': 'create_attribution_intelligence',
        }
        
        func_name = function_map.get(scenario_name)
        if not func_name:
            return None
        
        create_func = getattr(agent_module, func_name, None)
        if not create_func:
            return None
        
        # Get the function source to extract the SQL template and instructions
        import inspect
        source = inspect.getsource(create_func)
        
        import re
        
        # Find all triple-quoted strings in order
        # We need to find: response_instructions, orchestration_instructions, sql
        triple_quoted = list(re.finditer(r'(\w+)\s*=\s*f?"""(.*?)"""', source, re.DOTALL))
        
        response_instructions = ""
        orchestration_instructions = ""
        sql_template = ""
        
        for match in triple_quoted:
            var_name = match.group(1)
            content = match.group(2)
            if var_name == 'response_instructions':
                response_instructions = content
            elif var_name == 'orchestration_instructions':
                orchestration_instructions = content
            elif var_name == 'sql':
                sql_template = content
        
        if not sql_template:
            return None
        
        # Format instructions for YAML embedding
        response_formatted = format_instructions_for_yaml(response_instructions) if response_instructions else ""
        orchestration_formatted = format_instructions_for_yaml(orchestration_instructions) if orchestration_instructions else ""
        
        # Substitute config values
        ai_schema = config.DATABASE['schemas']['ai']
        execution_wh = config.WAREHOUSES['execution']['name']
        cortex_wh = config.WAREHOUSES.get('cortex_search', {}).get('name', execution_wh)
        orchestration_model = config.AGENT_ORCHESTRATION_MODEL
        
        # Replace common placeholders
        sql = sql_template
        
        # Convert Python f-string escapes to literal braces (for PROFILE JSON)
        sql = sql.replace('{{', '{').replace('}}', '}')
        
        # Convert Python escaped backslashes in source to single backslashes
        # In source code \\n appears as literal backslash-backslash-n, should become backslash-n
        sql = sql.replace('\\\\n', '\\n')
        sql = sql.replace('\\\\"', '\\"')
        sql = sql.replace("\\\\'", "\\'")
        
        # Replace database/schema placeholders
        sql = sql.replace('{database_name}', db_name)
        sql = sql.replace('{ai_schema}', ai_schema)
        sql = sql.replace("{config.WAREHOUSES['execution']['name']}", execution_wh)
        sql = sql.replace("{config.WAREHOUSES['cortex_search']['name']}", cortex_wh)
        sql = sql.replace('{config.AGENT_ORCHESTRATION_MODEL}', orchestration_model)
        
        # Replace formatted instruction placeholders
        sql = sql.replace('{response_formatted}', response_formatted)
        sql = sql.replace('{orchestration_formatted}', orchestration_formatted)
        
        return sql.strip()
        
    except Exception as e:
        log_detail(f"  Fallback agent generation failed: {e}")
        return None


def _get_corpus_for_service(service_name):
    """Map search service name to corpus table name."""
    service_to_corpus = {
        'SAM_BROKER_RESEARCH': 'BROKER_RESEARCH_CORPUS',
        'SAM_COMPANY_EVENTS': 'COMPANY_EVENT_TRANSCRIPTS_CORPUS',
        'SAM_PRESS_RELEASES': 'PRESS_RELEASES_CORPUS',
        'SAM_NGO_REPORTS': 'NGO_REPORTS_CORPUS',
        'SAM_ENGAGEMENT_NOTES': 'ENGAGEMENT_NOTES_CORPUS',
        'SAM_POLICY_DOCS': 'POLICY_DOCS_CORPUS',
        'SAM_SALES_TEMPLATES': 'SALES_TEMPLATES_CORPUS',
        'SAM_PHILOSOPHY_DOCS': 'PHILOSOPHY_DOCS_CORPUS',
        'SAM_REPORT_TEMPLATES': 'REPORT_TEMPLATES_CORPUS',
        'SAM_MACRO_EVENTS': 'MACRO_EVENTS_CORPUS',
        'SAM_CUSTODIAN_REPORTS': 'CUSTODIAN_REPORTS_CORPUS',
        'SAM_RECONCILIATION_NOTES': 'RECONCILIATION_NOTES_CORPUS',
        'SAM_SSI_DOCUMENTS': 'SSI_DOCUMENTS_CORPUS',
        'SAM_OPS_PROCEDURES': 'OPS_PROCEDURES_CORPUS',
        'SAM_STRATEGY_DOCUMENTS': 'STRATEGY_DOCUMENTS_CORPUS',
        'SAM_METHODOLOGY_DOCS': 'METHODOLOGY_DOCS_CORPUS',
        'SAM_IPS_DOCS': 'IPS_DOCS_CORPUS',
        'SAM_REAL_SEC_FILINGS': 'SEC_FILINGS_CORPUS',
        'SAM_PE_DUE_DILIGENCE': 'PE_DUE_DILIGENCE_CORPUS',
        'SAM_PE_EXPERT_NETWORK': 'PE_EXPERT_NETWORK_CORPUS',
        'SAM_PE_BOARD_PACKS': 'PE_BOARD_PACKS_CORPUS',
    }
    return service_to_corpus.get(service_name, 'UNKNOWN_CORPUS')
