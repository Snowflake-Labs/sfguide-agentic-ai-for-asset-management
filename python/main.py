#!/usr/bin/env python3
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
Simulated Asset Management (SAM) Demo - Main CLI Orchestrator

Build Phases (dependency order, all under --scope data):
  Step 1: FOUNDATION — Dimension tables from Marketplace + config
  Step 2: MARKET DATA — Marketplace fact tables (prices, financials, segments)
  Step 3: CURATED + ANALYTICS — Derived facts, views, attribution
  Step 4: PIPELINES — Create infra, load RAW, generate docs, run pipelines
  Step 5: NLP + HIDDEN FACTORS — AI_AGG on corpus, hidden factor exposures
  AI:     Semantic views, search services, agents (--scope ai)

Scope mapping:
  --scope all        → Steps 1-5 + AI (full rebuild)
  --scope data       → Steps 1-5 (all tables, pipelines, and views)
  --scope ai         → AI components only (semantic + search + agents)
  --scope semantic   → Semantic views only
  --scope search     → Search services only
  --scope agents     → Agents only
  --scope tools      → UDF/procedure deployment only
  --scope streamlit  → Streamlit app deployment only

Usage:
    python main.py --connection-name CONNECTION [--scenarios SCENARIO_LIST] [--scope SCOPE]
    python main.py --connection-name CONNECTION --export SCENARIO [--export-dir DIR]

Examples:
    python main.py --connection-name my_demo                              # Build everything
    python main.py --connection-name my_demo --scenarios portfolio_copilot # Build foundation + portfolio scenario
    python main.py --connection-name my_demo --scope data                 # Build all data (dimensions + market + pipelines + curated)
    python main.py --connection-name my_demo --scope ai                   # Build all AI components
    python main.py --connection-name my_demo --scope agents               # Rebuild agents only
    python main.py --connection-name my_demo --scope tools                # Deploy UDFs/procedures only (fast testing)
    python main.py --connection-name my_demo --test-mode                  # Use test mode (reduced data volumes)
    python main.py --connection-name my_demo --scope data --include-ml    # Data + ML infrastructure
    python main.py --connection-name my_demo --export all                 # Export all scenarios
"""

import argparse
import sys
from typing import List, Optional
from datetime import datetime

import config
from config import (
    DEFAULT_CONNECTION_NAME, 
    AVAILABLE_SCENARIOS,
    SCENARIO_AGENTS,
    DATABASE,
    WAREHOUSES
)
from utils.logging import (
    set_verbosity, log_phase, log_step, log_substep, log_detail, log_error, log_warning, log_phase_complete, Spinner
)
from utils.config_helpers import get_required_document_types

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Build Simulated Asset Management (SAM) AI Demo Environment'
    )
    
    parser.add_argument(
        '--connection-name',
        type=str,
        required=True,
        help='Snowflake connection name from ~/.snowflake/connections.toml (required)'
    )
    
    parser.add_argument(
        '--scenarios',
        type=str,
        default='all',
        help='Comma-separated list of scenarios to build, or "all" for all scenarios (default: all)'
    )
    
    parser.add_argument(
        '--scope',
        type=str,
        choices=['all', 'data', 'ai', 'semantic', 'search', 'agents', 'tools', 'streamlit', 'signals', 'morning-brief', 'thesis', 'earnings-insights', 'cockpit'],
        default='all',
        help='Scope of build: all=everything, data=dimensions+market+pipelines+curated, ai=semantic+search+agents, semantic=views only, search=services only, agents=agents only, tools=UDFs/procedures only, streamlit=deploy app only, signals=extract signals into FACT_SIGNALS'
    )
    
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Use test mode with 10 percent of data for faster development testing (500 securities vs 5,000)'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Validate semantic view YAML definitions without creating views (use with --scope semantic)'
    )
    
    parser.add_argument(
        '--include-eval',
        action='store_true',
        help='Include evaluation dataset generation (combinable with any scope)'
    )
    
    parser.add_argument(
        '--include-ml',
        action='store_true',
        help='Include ML infrastructure build (combinable with any scope)'
    )
    
    parser.add_argument(
        '--skip-pipelines',
        action='store_true',
        help='Skip pipeline execution and NLP scoring (Steps 4-5). Rebuilds only structured data (Steps 1-3).'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed build output (default: compact spinner output)'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        default=None,
        help='Export scenario(s) to deployable package. Use scenario name or "all" for all scenarios.'
    )
    
    parser.add_argument(
        '--export-dir',
        type=str,
        default='./exports',
        help='Output directory for exports (default: ./exports)'
    )
    
    return parser.parse_args()

def validate_scenarios(scenario_list: List[str]) -> List[str]:
    """Validate and return list of valid scenarios (delegates to config)."""
    try:
        return config.validate_scenarios(scenario_list)
    except ValueError as e:
        log_error(str(e))
        sys.exit(1)

def create_snowpark_session(connection_name: str, recreate_warehouses: bool = True):
    """Create and validate Snowpark session."""
    try:
        from snowflake.snowpark import Session
        
        session = Session.builder.config("connection_name", connection_name).create()
        
        result = session.sql("SELECT CURRENT_VERSION()").collect()
        
        create_demo_warehouses(session, recreate=recreate_warehouses)
        
        return session
        
    except ImportError:
        log_error("snowflake-snowpark-python not installed. Install with: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        log_error(f"Connection failed: {str(e)}")
        log_warning(f"Ensure connection '{connection_name}' exists in ~/.snowflake/connections.toml")
        sys.exit(1)

def validate_real_data_access(session):
    """Validate access to Snowflake Marketplace data share before starting build."""
    from config import REAL_DATA_SOURCES
    from utils.snowflake import verify_table_access
    
    database = REAL_DATA_SOURCES['database']
    schema = REAL_DATA_SOURCES['schema']
    probe_key = REAL_DATA_SOURCES['access_probe_table_key']
    probe_table = REAL_DATA_SOURCES['tables'][probe_key]['table']
    
    log_step("Validating access to real data source")
    
    success, error_msg = verify_table_access(session, database, schema, probe_table)
    if success:
        log_detail(f"Validated access to {database}.{schema}")
    else:
        log_error(f"Cannot access real data source: {database}.{schema}.{probe_table}")
        log_error("This demo requires access to Snowflake Marketplace financial data.")
        log_error("Please add this database from Snowflake Marketplace and retry.")
        log_detail(f"Error details: {error_msg}")
        raise SystemExit(1)


def create_demo_warehouses(session, recreate: bool = True):
    """Create dedicated warehouses for demo execution and Cortex Search services."""
    try:
        execution_wh = WAREHOUSES['execution']['name']
        execution_size = WAREHOUSES['execution']['size']
        execution_comment = WAREHOUSES['execution']['comment']
        
        cortex_wh = WAREHOUSES['cortex_search']['name']
        cortex_size = WAREHOUSES['cortex_search']['size']
        cortex_comment = WAREHOUSES['cortex_search']['comment']
        
        ddl = 'CREATE OR REPLACE' if recreate else 'CREATE'
        if_not_exists = '' if recreate else ' IF NOT EXISTS'
        
        session.sql(f"""
            {ddl} WAREHOUSE{if_not_exists} {execution_wh}
            WITH WAREHOUSE_SIZE = {execution_size}
            GENERATION = '2'
            AUTO_SUSPEND = 60
            AUTO_RESUME = TRUE
            COMMENT = '{execution_comment}'
        """).collect()
        
        session.sql(f"""
            {ddl} WAREHOUSE{if_not_exists} {cortex_wh}
            WITH WAREHOUSE_SIZE = {cortex_size}
            GENERATION = '2'
            AUTO_SUSPEND = 60
            AUTO_RESUME = TRUE
            COMMENT = '{cortex_comment}'
        """).collect()
        
        session.use_warehouse(execution_wh)
        
    except Exception as e:
        log_error(f"Failed to create warehouses: {e}")
        log_error("Warehouses are required for all build operations.")
        raise
        

def run_export(session, export_arg, export_dir):
    """Run export mode for scenario(s)."""
    from export.package import export_scenario, list_exportable_scenarios
    
    if export_arg.lower() == 'all':
        scenarios_to_export = list_exportable_scenarios()
    else:
        scenarios_to_export = [s.strip() for s in export_arg.split(',')]
    
    print(f"\n{'='*60}")
    print(f"  SAM Demo Export Mode")
    print(f"{'='*60}")
    print(f"  Scenarios: {', '.join(scenarios_to_export)}")
    print(f"  Output: {export_dir}")
    print(f"{'='*60}\n")
    
    exported_packages = []
    for scenario in scenarios_to_export:
        try:
            zip_path = export_scenario(session, scenario, export_dir)
            exported_packages.append((scenario, zip_path))
        except Exception as e:
            log_error(f"Failed to export {scenario}: {e}")
            raise
    
    print(f"\n{'='*60}")
    print(f"  Export Complete")
    print(f"{'='*60}")
    for scenario, zip_path in exported_packages:
        print(f"  {scenario}: {zip_path}")
    print(f"{'='*60}\n")
    
    return exported_packages


def main():
    """Main execution function."""
    start_time = datetime.now()
    
    args = parse_arguments()
    
    set_verbosity(2 if args.verbose else 0)
    
    recreate_warehouses = (args.scope == 'all') if not args.export else False
    session = create_snowpark_session(args.connection_name, recreate_warehouses=recreate_warehouses)
    
    try:
        if args.export:
            run_export(session, args.export, args.export_dir)
            return
        
        if args.scenarios.lower() == 'all':
            scenario_list = AVAILABLE_SCENARIOS
        else:
            scenario_list = [s.strip() for s in args.scenarios.split(',')]
        validated_scenarios = validate_scenarios(scenario_list)
        
        print(f"\n{'='*60}")
        print(f"  Simulated Asset Management (SAM) Demo Builder")
        print(f"{'='*60}")
        print(f"  Build started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f"  Scenarios: {', '.join(validated_scenarios)}")
        print(f"  Scope: {args.scope}")
        print(f"  Connection: {args.connection_name}")
        if args.test_mode:
            print(f"  Mode: TEST (10% data volumes)")
        if args.include_eval:
            print(f"  Include: Evaluation datasets")
        if args.include_ml:
            print(f"  Include: ML infrastructure")
        print(f"{'='*60}")
        
        # =====================================================================
        # BUILD STEPS — Linear Dependency Order (all under --scope data)
        # =====================================================================
        #
        # Step 1: FOUNDATION (dimensions)
        #   Creates: DIM_ISSUER, DIM_SECURITY, DIM_PORTFOLIO, DIM_BENCHMARK, etc.
        #
        # Step 2: MARKET DATA (Marketplace → MARKET_DATA schema)
        #   Creates: FACT_STOCK_PRICES, FACT_SEC_FINANCIALS, FACT_SEC_SEGMENTS,
        #            DIM_GEO_RISK_CLASSIFICATION, FACT_POLICY_RATES, FACT_FX_RATES,
        #            FACT_ECONOMIC_INDICATORS, FACT_TREASURY_YIELDS,
        #            FACT_COUNTRY_EMISSIONS, FACT_INSIDER_TRANSACTIONS,
        #            FACT_INSTITUTIONAL_HOLDINGS
        #
        # Step 3: CURATED + ANALYTICS (derived from Step 1+2)
        #   Creates: FACT_POSITION_DAILY_ABOR, FACT_ESG_SCORES, scenario data,
        #            V_SECURITY_RETURNS, attribution tables, factor exposures,
        #            portfolio modelling views, performance metrics
        #
        # Step 4: PIPELINES + CORPUS (create infra → load RAW → run → corpus)
        #   Creates: Pipeline infrastructure, RAW tables, PDFs, corpus tables
        #
        # Step 5: NLP SCORING + HIDDEN FACTORS (AI_AGG on corpus → hidden factors)
        #   Creates: FACT_TRANSCRIPT_NLP_SCORES, FACT_HIDDEN_FACTOR_EXPOSURES
        #
        # AI: Semantic views, search services, agents (--scope ai)
        #
        # =====================================================================

        build_data = args.scope in ['all', 'data']
        build_semantic = args.scope in ['all', 'ai', 'semantic']
        build_search = args.scope in ['all', 'ai', 'search']
        build_agents = args.scope in ['all', 'ai', 'agents']
        build_tools = args.scope == 'tools'
        build_streamlit = args.scope == 'streamlit'

        if build_data:
            with Spinner("Validating real data access"):
                validate_real_data_access(session)

        # =================================================================
        # STEP 1: FOUNDATION — Dimension tables
        # =================================================================
        if build_data:
            log_phase("Step 1: Foundation (Dimension Tables)")
            from data import structured as generate_structured
            from data import market_data as generate_market_data

            recreate_database = (args.scope == 'all')
            with Spinner("Database structure"):
                generate_structured.create_database_structure(session, recreate_database=recreate_database)

            with Spinner("Dimension tables"):
                log_step("Dimension tables")
                generate_structured.build_dimension_tables(session, args.test_mode)

            log_phase_complete("Foundation complete")

            # =============================================================
            # STEP 2: MARKET DATA — Marketplace fact tables
            # =============================================================
            log_phase("Step 2: Market Data (Marketplace)")

            data_phases = config.get_data_phases(validated_scenarios)

            with Spinner("Price anchor (FACT_STOCK_PRICES)"):
                log_substep("Price anchor (FACT_STOCK_PRICES)")
                generate_market_data.build_price_anchor(session, args.test_mode)

            with Spinner("Dividend data (FACT_DIVIDENDS)"):
                log_substep("Dividend data (FACT_DIVIDENDS)")
                generate_market_data.build_fact_dividends(session, args.test_mode)

            if 'market_data' in data_phases:
                with Spinner("Extended market data"):
                    generate_market_data.build_all(session, args.test_mode)

            log_phase_complete("Market data complete")

            # =============================================================
            # STEP 3: CURATED + ANALYTICS — Derived facts, views, attribution
            # =============================================================
            log_phase("Step 3: Curated + Analytics")

            with Spinner("Fact tables"):
                log_step("Fact tables")
                generate_structured.build_fact_tables(session, args.test_mode)

            with Spinner("Scenario data"):
                generate_structured.reset_build_tracking()
                for scenario in validated_scenarios:
                    generate_structured.build_scenario_data(session, scenario)

            with Spinner("Data quality validation"):
                generate_structured.validate_data_quality(session)

            if 'market_data' in data_phases:
                with Spinner("Security returns and enriched holdings"):
                    log_substep("Security returns and enriched holdings")
                    generate_structured.build_security_returns_view(session)
                    generate_structured.build_v_holdings_with_esg(session)

                if 'attribution' in data_phases:
                    with Spinner("Attribution market data"):
                        log_substep("Attribution market data (benchmarks, VIX, sector returns)")
                        generate_structured.build_attribution_market_data(session)

                if 'factor_exposures' in data_phases:
                    with Spinner("Factor exposures"):
                        log_substep("Factor exposures (calculated from real data)")
                        generate_structured.build_factor_exposures(session)

                if 'attribution' in data_phases:
                    with Spinner("Attribution tables"):
                        log_substep("Attribution tables (Brinson, factor attribution, stress scenarios)")
                        generate_structured.build_attribution_tables(session)
                    with Spinner("Multi-level attribution"):
                        log_substep("Multi-level attribution (sector, country, industry)")
                        generate_structured.build_multi_level_attribution(session)
                    with Spinner("Currency attribution"):
                        log_substep("Currency attribution (local, FX, AVU decomposition)")
                        generate_structured.build_currency_attribution(session)
                    with Spinner("Linked attribution"):
                        log_substep("Multi-period linked attribution (QTD, YTD, trailing 12M)")
                        generate_structured.build_attribution_linked(session)
                    with Spinner("Advanced attribution views"):
                        log_substep("Advanced attribution views (rolling analytics, anomalies, peer learning)")
                        generate_structured.build_advanced_attribution_views(session)

                if 'portfolio_modelling' in data_phases:
                    with Spinner("Portfolio modelling views"):
                        log_substep("Portfolio modelling views and covariance matrix")
                        generate_structured.build_portfolio_modelling_views(session)
                        generate_structured.build_fact_covariance_matrix(session)

                with Spinner("Strategy performance metrics"):
                    log_substep("Strategy performance metrics")
                    generate_structured.build_fact_strategy_performance(session)

                with Spinner("Benchmark performance metrics"):
                    log_substep("Benchmark performance metrics")
                    generate_structured.build_fact_benchmark_performance(session)

                with Spinner("Portfolio vs benchmark comparison"):
                    log_substep("Portfolio vs benchmark comparison view")
                    generate_structured.build_portfolio_benchmark_comparison_view(session)

            log_phase_complete("Curated + analytics complete")

            # =============================================================
            # STEP 4: PIPELINES + CORPUS — Create infra, load RAW, run
            # =============================================================
            if args.skip_pipelines:
                log_warning("Skipping Steps 4-5 (pipelines + NLP scoring) — use without --skip-pipelines to rebuild corpus")
            else:
                log_phase("Step 4: Pipelines + Corpus")

                with Spinner("Building coverage universe"):
                    log_step("Building DIM_COVERAGE_UNIVERSE (portfolio + key peers)")
                    from data.coverage_universe import build_coverage_universe
                    build_coverage_universe(session)

                from data import pipelines as create_unstructured_pipelines
                with Spinner("Creating pipeline objects"):
                    log_step("Creating pipeline objects (stages, streams, tables, tasks)")
                    create_unstructured_pipelines.create_all_pipelines(session)

                required_doc_types = get_required_document_types(validated_scenarios)

                with Spinner("Loading RAW tables"):
                    log_step("Loading RAW tables (after streams exist)")
                    if 'company_event_transcripts' in required_doc_types:
                        try:
                            from data import transcripts as generate_real_transcripts
                            if generate_real_transcripts.verify_transcripts_available(session):
                                log_substep("Loading real transcripts to RAW table")
                                generate_real_transcripts.load_raw_table(session, args.test_mode)
                            else:
                                log_warning("Real transcripts source not available, skipping...")
                        except Exception as e:
                            log_warning(f"Real transcripts loading failed: {e}")

                    try:
                        log_substep("Loading SEC filings to RAW table")
                        create_unstructured_pipelines.load_sec_filings_raw(session, args.test_mode)
                    except Exception as e:
                        log_warning(f"SEC filings loading failed: {e}")

                with Spinner("Generating documents"):
                    log_step("Generating documents")
                    from data import unstructured as generate_unstructured
                    generate_unstructured.build_all(session, required_doc_types, args.test_mode)

                with Spinner("Executing pipelines"):
                    log_step("Executing pipelines")
                    create_unstructured_pipelines.run_all_pipelines(session, upload_pdfs=True)

                log_phase_complete("Pipelines + corpus complete")

                # =============================================================
                # STEP 5: NLP SCORING + HIDDEN FACTORS
                # =============================================================
                if 'nlp_scoring' in data_phases:
                    log_phase("Step 5: NLP Scoring + Hidden Factors")

                    with Spinner("Transcript NLP scores"):
                        log_step("Transcript NLP scores (AI_COMPLETE on corpus for AI exposure, SQL for geo risk)")
                        generate_market_data.build_transcript_nlp_scores(session, args.test_mode)

                    with Spinner("Hidden factor exposures"):
                        log_step("Hidden factor exposures (from NLP scores + market data)")
                        generate_structured.build_hidden_factor_exposures(session)

                    log_phase_complete("NLP scoring + hidden factors complete")

        # =================================================================
        # AI COMPONENTS — Semantic views, search services, agents
        # =================================================================
        if build_semantic or build_search or build_agents:
            log_phase("AI Components")

            from ai.proactive_insights import create_proactive_insights_tables
            from ai.signal_store import create_fact_signals
            from ai.thesis_tracker import setup_thesis_tracker
            create_proactive_insights_tables(session)
            create_fact_signals(session)
            with Spinner("Setting up thesis tracker (table must exist before semantic view)"):
                setup_thesis_tracker(session)

            from ai import builder as build_ai
            with Spinner("Building AI components"):
                build_ai.build_all(session, validated_scenarios, build_semantic, build_search, build_agents, verify_only=args.verify_only)
            log_phase_complete("AI components complete")

        # =================================================================
        # OPTIONAL: Tools deployment (fast dev shortcut)
        # =================================================================
        if build_tools:
            log_phase("Tools Deployment (UDFs/Procedures)")
            from ai import builder as build_ai
            with Spinner("Deploying tools"):
                build_ai.deploy_tools_only(session)
            log_phase_complete("Tools deployment complete")

        # =================================================================
        # OPTIONAL: Streamlit deployment (fast dev shortcut)
        # =================================================================
        if build_streamlit:
            log_phase("Streamlit Deployment")
            from ai import builder as build_ai
            with Spinner("Deploying Streamlit app"):
                success = build_ai.deploy_streamlit_app(session)
            if success:
                log_phase_complete("Streamlit deployment complete")
            else:
                log_warning("Streamlit deployment skipped due to missing prerequisites")

        # =================================================================
        # OPTIONAL: Cockpit SPCS deployment (--scope cockpit)
        # =================================================================
        if args.scope == 'cockpit':
            log_phase("FSI AI Demo Cockpit — SPCS Deployment")
            from deploy.cockpit import deploy_cockpit
            with Spinner("Deploying cockpit to SPCS"):
                success = deploy_cockpit(session, args.connection_name)
            if success:
                log_phase_complete("Cockpit deployed to SPCS")
            else:
                log_warning("Cockpit deployment failed — check prerequisites above")

        # =================================================================
        # OPTIONAL: Research thesis tracker (standalone, when AI phase didn't run)
        # =================================================================
        if args.scope in ['thesis', 'data'] and not (build_semantic or build_search or build_agents):
            log_phase("Research Thesis Tracker")
            from ai.thesis_tracker import setup_thesis_tracker
            with Spinner("Setting up thesis tracker and seeding data"):
                setup_thesis_tracker(session)
            log_phase_complete("Research thesis tracker complete")

        # =================================================================
        # OPTIONAL: Signal extraction (--scope signals)
        # =================================================================
        if args.scope in ['signals', 'all', 'ai', 'data']:
            log_phase("Signal Extraction Pipeline")
            from ai.signal_store import seed_signals
            with Spinner("Extracting signals into FACT_SIGNALS"):
                seed_signals(session, test_mode=args.test_mode,
                             include_tier2=(args.scope != 'signals' or not args.test_mode),
                             include_tier3=False)
            log_phase_complete("Signal extraction complete")

        # =================================================================
        # Morning briefing seeding (--scope morning-brief, all, data)
        # =================================================================
        if args.scope in ['morning-brief', 'all', 'data']:
            log_phase("Morning Briefing Seeding")
            from ai.proactive_insights import seed_morning_briefings
            with Spinner("Generating morning briefings for all personas"):
                seed_morning_briefings(session, personas=[
                    'equity', 'credit', 'pe', 'executive',
                    'risk-compliance', 'operations',
                ])
            log_phase_complete("Morning briefings seeded")

        # =================================================================
        # OPTIONAL: Batch earnings insights (--scope earnings-insights)
        # =================================================================
        if args.scope in ['earnings-insights', 'all', 'data']:
            log_phase("Batch Earnings Insights")
            from ai.earnings_insights import seed_earnings_insights
            with Spinner("Generating earnings insights via AI_COMPLETE"):
                seed_earnings_insights(session)
            log_phase_complete("Earnings insights complete")

        # =================================================================
        # OPTIONAL FLAGS: --include-eval, --include-ml
        # =================================================================
        if args.include_eval:
            log_phase("Evaluation Datasets")
            from ai import evaluations
            with Spinner("Creating evaluation datasets"):
                evaluations.create_eval_datasets(session, validated_scenarios)
            log_phase_complete("Evaluation datasets complete")

        if args.include_ml:
            log_phase("ML Infrastructure")
            from ai.tools.ml_common import ensure_ml_schema, resolve_ml_build_order
            with Spinner("ML infrastructure"):
                ensure_ml_schema(session)
                ml_scenarios = [s for s in validated_scenarios if s in config.ML_SCENARIOS]
                if ml_scenarios:
                    ordered = resolve_ml_build_order(ml_scenarios)
                    log_step(f"ML scenarios resolved: {ordered}")
            log_phase_complete("ML infrastructure complete")

        end_time = datetime.now()
        duration = end_time - start_time
        
        agents_created = [
            (SCENARIO_AGENTS[s]['agent_name'], SCENARIO_AGENTS[s]['description']) 
            for s in validated_scenarios 
            if s in SCENARIO_AGENTS
        ]
        
        print(f"\n{'='*60}")
        print(f"  SAM Demo Environment Build Complete")
        print(f"{'='*60}")
        print(f"  Build completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Total duration: {duration}")
        print(f"  Database: {DATABASE['name']}")
        print(f"  Scenarios: {', '.join(validated_scenarios)}")
        print()
        if agents_created:
            print(f"  Agents Created:")
            for agent_name, description in agents_created:
                print(f"    - {agent_name}: {description}")
        else:
            print(f"  No agents created (--scope may have excluded AI components)")
        print(f"{'='*60}\n")
        
    except ImportError as e:
        log_error(f"Missing module: {e}")
        sys.exit(1)
    except Exception as e:
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n{'='*60}")
        print(f"  BUILD FAILED after {duration}")
        print(f"  Error: {str(e)}")
        print(f"{'='*60}\n")
        sys.exit(1)
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()
