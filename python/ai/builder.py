# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Created by Mats Stellwall, Snowflake, and Snowflake CoCo

"""
AI Components Builder for SAM Demo

This module orchestrates the creation of AI components including:
- Semantic views for Cortex Analyst (via create_semantic_views.py)
- Cortex Search services for document types (via create_cortex_search.py)
- Custom tools (PDF generation, M&A simulation, portfolio modelling)
- Streamlit application deployment
- Validation and testing of AI components

Tool implementations are modularized in the tools/ package for maintainability.
"""

from snowflake.snowpark import Session
from typing import List
import config
from .semantic_views import create_semantic_views, create_ml_semantic_views
from .yaml_loader import verify_all_views
from .cortex_search import create_search_services
from utils.logging import log_error, log_warning, log_detail, log_info, log_step

from .tools import (
    create_pdf_report_stage,
    create_pdf_report_tool,
    create_ma_simulation_tool,
    create_monte_carlo_udfs,
    create_monte_carlo_tool,
    create_backtest_tool,
    create_attribution_tool,
    create_stress_backtest_tool,
    create_stress_backtest_tool,
    create_scenario_sensitivity_tool,
    validate_streamlit_prerequisites,
    deploy_streamlit_app,
    create_suggestion_tables,
    create_tool_run_tables,
    create_data_origin_tool,
    ensure_ml_schema,
    resolve_ml_build_order,
)


def seed_drill_down_questions(session: Session):
    """Seed drill-down questions into the shared app table (FSI_DEMO_CONFIG.APP).

    Uses DEMO_ID scoping: only replaces rows belonging to this project,
    leaving other demos' rows untouched.
    """
    app_db = config.COCKPIT['app_database']
    app_schema = config.COCKPIT['app_schema']
    demo_id = config.COCKPIT['demo_id']
    table = f"{app_db}.{app_schema}.DRILL_DOWN_QUESTIONS"

    # Ensure shared schema exists
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {app_db}.{app_schema}").collect()

    # Create table if it doesn't exist (preserves other demos' data)
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            DEMO_ID         VARCHAR(100) NOT NULL,
            ENTITY_TYPE     VARCHAR(50) NOT NULL,
            SORT_ORDER      NUMBER(3,0) NOT NULL,
            LABEL           VARCHAR(200) NOT NULL,
            HEADLINE        VARCHAR(200),
            PROMPT_TEMPLATE VARCHAR(2000) NOT NULL,
            ICON            VARCHAR(50),
            IS_ACTIVE       BOOLEAN DEFAULT TRUE,
            CREATED_AT      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            UPDATED_AT      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PRIMARY KEY (DEMO_ID, ENTITY_TYPE, SORT_ORDER)
        )
    """).collect()

    # Remove only this project's rows (idempotent)
    session.sql(f"DELETE FROM {table} WHERE DEMO_ID = '{demo_id}'").collect()

    # Insert this project's questions
    questions = config.REF_DATA['drill_down_questions']['questions']
    esc = lambda s: s.replace("'", "''")
    rows = []
    for q in questions:
        rows.append(
            f"('{demo_id}', '{q['entity_type']}', {q['sort_order']}, '{esc(q['label'])}', "
            f"'{esc(q['headline'])}', '{esc(q['prompt_template'])}', '{q['icon']}', "
            f"TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())"
        )

    session.sql(f"""
        INSERT INTO {table}
            (DEMO_ID, ENTITY_TYPE, SORT_ORDER, LABEL, HEADLINE, PROMPT_TEMPLATE, ICON, IS_ACTIVE, CREATED_AT, UPDATED_AT)
        SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
        FROM VALUES {', '.join(rows)}
    """).collect()

    entity_types = set(q['entity_type'] for q in questions)
    count = session.sql(f"SELECT COUNT(*) AS CNT FROM {table} WHERE DEMO_ID = '{demo_id}'").collect()[0]['CNT']
    log_detail(f"  DRILL_DOWN_QUESTIONS: {count} questions across {len(entity_types)} entity types (demo_id={demo_id})")


def deploy_tools_only(session: Session):
    """
    Deploy only UDFs and stored procedures (tools) without semantic views, search services, or agents.
    This is a fast path for testing tool changes.
    """
    log_step("Deploying Monte Carlo UDFs")
    create_monte_carlo_udfs(session)
    
    log_step("Creating tool run tables")
    create_tool_run_tables(session)
    
    log_step("Deploying portfolio modelling tools")
    create_portfolio_modelling_tools(session)
    
    log_detail("  Tools deployed: NORM_PPF, SIMULATE_PATH, RUN_BACKTEST_TOOL, RUN_MONTE_CARLO_TOOL, RUN_ATTRIBUTION_TOOL, RUN_STRESS_BACKTEST_TOOL")


def create_portfolio_modelling_tools(session: Session):
    """
    Create Python UDF tools for portfolio modelling agent.
    
    Tools created:
    - RUN_BACKTEST_TOOL: Historical portfolio backtesting
    - RUN_MONTE_CARLO_TOOL: Monte Carlo simulation with block bootstrapping (using UDTF)
    - RUN_ATTRIBUTION_TOOL: Brinson-Fachler performance attribution
    - RUN_STRESS_BACKTEST_TOOL: Historical stress period analysis
    
    Tables created:
    - PORTFOLIO_SUGGESTION* tables for saving suggestions
    """
    create_monte_carlo_udfs(session)
    create_tool_run_tables(session)
    create_monte_carlo_tool(session)
    create_backtest_tool(session)
    create_attribution_tool(session)
    create_stress_backtest_tool(session)
    create_scenario_sensitivity_tool(session)
    from ai.tools.counterfactual import create_counterfactual_tool
    create_counterfactual_tool(session)
    create_suggestion_tables(session)


def build_all(session: Session, scenarios: List[str], build_semantic: bool = True, build_search: bool = True, build_agents: bool = True, verify_only: bool = False):
    """
    Build AI components for the specified scenarios.
    
    Args:
        session: Active Snowpark session
        scenarios: List of scenario names
        build_semantic: Whether to build semantic views
        build_search: Whether to build search services
        build_agents: Whether to create Snowflake Intelligence agents
        verify_only: If True, validate YAML definitions without creating views
    """
    
    if verify_only:
        log_step("Validating semantic view YAML definitions (verify-only mode)")
        results = verify_all_views(session)
        passed = len(results['passed'])
        failed = len(results['failed'])
        log_info(f"  Validation: {passed} passed, {failed} failed out of {passed + failed} views")
        if results['failed']:
            for name, err in results['failed']:
                log_error(f"  FAILED: {name}: {err}")
            raise Exception(f"YAML validation failed for {failed} views")
        return
    
    try:
        create_tool_run_tables(session)
    except Exception as e:
        log_warning(f"  Tool run tables creation failed: {e}")

    if build_semantic:
        try:
            create_semantic_views(session, scenarios)
        except Exception as e:
            log_error(f"CRITICAL: Semantic view creation failed: {e}")
            raise
    
    if build_search:
        try:
            create_search_services(session, scenarios)
        except Exception as e:
            log_error(f"CRITICAL: Search service creation failed: {e}")
            raise
    
    try:
        create_pdf_report_stage(session)
        create_pdf_report_tool(session)
    except Exception as e:
        log_warning(f" PDF tool creation failed: {e}")
    
    try:
        create_data_origin_tool(session)
    except Exception as e:
        log_warning(f" Data origin tool creation failed: {e}")

    required_tools = config.get_required_tools(scenarios)

    if 'ma_simulation' in required_tools:
        try:
            create_ma_simulation_tool(session)
        except Exception as e:
            log_warning(f" M&A simulation tool creation failed: {e}")
    
    if 'portfolio_modelling' in required_tools:
        try:
            create_portfolio_modelling_tools(session)
        except Exception as e:
            log_warning(f" Portfolio modelling tools creation failed: {e}")
        
        if build_agents and not config.IN_WORKSPACE:
            valid, missing = validate_streamlit_prerequisites(session)
            if valid:
                try:
                    deploy_streamlit_app(session, skip_validation=True)
                except Exception as e:
                    log_warning(f" Streamlit app deployment failed: {e}")
            else:
                log_warning(" Skipping Streamlit deployment - missing prerequisites:")
                for item in missing:
                    log_warning(f"   - {item}")
    
    if build_agents:
        try:
            from data.pipelines import upload_skills_to_stage
            uploaded, skill_failed = upload_skills_to_stage(session)
            log_detail(f"  Skills: {uploaded} files uploaded to SKILL_STAGE ({skill_failed} failed)")
        except Exception as e:
            log_warning(f" Skill upload failed: {e}")

        try:
            from . import agents as create_agents
            created, failed = create_agents.create_all_agents(session, scenarios)
            if failed > 0:
                log_warning(f" {failed} agents failed to create")
        except Exception as e:
            log_warning(f" Agent creation failed: {e}")

        try:
            from . import evaluations
            evaluations.create_eval_datasets(session, scenarios)
        except Exception as e:
            log_warning(f" Evaluation dataset creation failed: {e}")

        if 'portfolio_management' in scenarios:
            try:
                from .proactive_insights import create_all_proactive_infrastructure
                create_all_proactive_infrastructure(session)
            except Exception as e:
                log_warning(f" Proactive insights infrastructure failed: {e}")

    # Seed drill-down questions (cockpit-specific, skip in workspace/quickstart mode)
    if not config.IN_WORKSPACE:
        try:
            seed_drill_down_questions(session)
        except Exception as e:
            log_warning(f" Drill-down question seeding failed: {e}")

    try:
        validate_components(session, build_semantic, build_search, scenarios)
    except Exception as e:
        log_error(f"CRITICAL: AI component validation failed: {e}")
        raise


def validate_components(session: Session, semantic_built: bool, search_built: bool, scenarios: List[str] = None):
    """Validate that AI components are working correctly."""
    
    validation_passed = True
    
    analyst_view_scenarios = {'portfolio_management', 'risk_compliance',
                              'client_advisory', 'executive_leadership',
                              'research'}
    if semantic_built and scenarios and analyst_view_scenarios.intersection(scenarios):
        try:
            result = session.sql(f"""
                SELECT * FROM SEMANTIC_VIEW(
                    {config.DATABASE['name']}.AI.SAM_PORTFOLIO_VIEW
                    METRICS total_market_value_base
                    DIMENSIONS portfolio_name
                ) LIMIT 1
            """).collect()
            
            if len(result) == 0:
                log_error(" SAM_PORTFOLIO_VIEW validation failed - no results returned")
                validation_passed = False
                
        except Exception as e:
            log_error(f" SAM_PORTFOLIO_VIEW validation failed: {e}")
            validation_passed = False
    
    if search_built:
        try:
            services = session.sql(f"""
                SHOW CORTEX SEARCH SERVICES IN {config.DATABASE['name']}.AI
            """).collect()
            
            if len(services) == 0:
                log_error(" No Cortex Search services found")
                validation_passed = False
            else:
                service_name = services[0]['name']
                try:
                    test_result = session.sql(f"""
                        SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                            '{config.DATABASE['name']}.AI.{service_name}',
                            '{{"query": "test", "limit": 1}}'
                        )
                    """).collect()
                except Exception as e:
                    log_error(f" Search service {service_name} validation failed: {e}")
                    validation_passed = False
                    
        except Exception as e:
            log_error(f" Search service validation failed: {e}")
            validation_passed = False
    
    if not validation_passed:
        raise Exception("AI component validation failed")
