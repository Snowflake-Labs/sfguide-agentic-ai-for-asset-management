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
Simulated Asset Management (SAM) Demo — Snowflake Workspace Runner

This file is the entry point for setting up the SAM demo environment
when running inside a Snowflake Workspace. It supports two invocation modes:

1. As a Code Bundle (recommended). Packages are installed declaratively from
   code_bundle.yml, so there is no manual pip step:

     EXECUTE CODE BUNDLE SAM_DEMO.AI.SAM_BUILD_BUNDLE
       ENTRYPOINT = 'python/workspace_main.py';

   Pass arguments to narrow the build:

     EXECUTE CODE BUNDLE SAM_DEMO.AI.SAM_BUILD_BUNDLE
       ENTRYPOINT = 'python/workspace_main.py'
       ARGUMENTS  = ('--scope', 'agents');

   scripts/workspace_setup.sql creates the bundle and runs it for you.

2. Interactively, by opening this file in the Workspace and clicking "Run".
   Useful for iterating, because a Code Bundle version is an immutable snapshot
   and needs ALTER CODE BUNDLE ... ADD VERSION after every edit. In this mode
   install the packages first, from the Workspace terminal:

     pip install -r "$PWD/requirements-workspace.txt"

   then restart the kernel. Clicking "Run" passes no arguments, which is
   equivalent to --scope all and performs the full build.

Prerequisites:
  1. Run scripts/workspace_setup.sql in a Snowflake worksheet (creates the
     database, roles, grants, warehouses, compute pools and the build bundle)
  2. Create a Git Workspace from this repository

What a full build creates:
  - CURATED tables (dimensions, facts, views) from 503 real securities
  - MARKET_DATA tables (real SEC financials, prices, segments)
  - RAW document tables + corpus tables
  - Semantic Views (Cortex Analyst)
  - Cortex Search services
  - Cortex Agents (portfolio, research, sales, executive, risk, ops, credit, PE)
  - Agent skills uploaded to SKILL_STAGE
  - Tools: backtest, Monte Carlo, PDF generator, M&A simulation
  - The weekly refresh Code Bundle and task, unless --skip-automation
"""

import argparse
import os
import sys
from datetime import datetime

# Mark as workspace runtime so Streamlit/SPCS deployment is skipped.
# This MUST happen before `import config`: config.IN_WORKSPACE is evaluated at
# import time, and it is what suppresses those deployment paths.
os.environ['SNOWFLAKE_NOTEBOOK_RUNTIME'] = '1'

# Ensure the python/ directory is on the path for imports.
# Note: in a Snowflake Workspace notebook __file__ is not defined and the working
# directory is the workspace root. In a Code Bundle __file__ IS defined and the
# working directory is the bundle root, which mirrors the repo layout. Anchoring
# on os.getcwd() works for both.
_python_dir = os.path.join(os.getcwd(), 'python')
if not os.path.isdir(_python_dir):
    # If already inside python/ directory
    _python_dir = os.getcwd()
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

from snowflake.snowpark.context import get_active_session

import config
from utils.logging import (
    log_phase, log_step, log_substep, log_detail,
    log_warning, log_phase_complete, set_verbosity
)


def parse_arguments():
    """Parse arguments, tolerating none.

    Every argument is optional so that clicking "Run" in a Workspace - which
    passes no arguments at all - behaves exactly as this script did before, a
    full build. parse_known_args rather than parse_args because a notebook
    runtime may put values in sys.argv that are not ours to interpret, and
    argparse would otherwise abort the run.

    Scope names and semantics deliberately mirror python/main.py so that the
    same scope means the same thing whichever entry point is used.
    """
    parser = argparse.ArgumentParser(
        description='Build the SAM AI demo environment from a Snowflake Workspace'
    )
    parser.add_argument(
        '--scope',
        type=str,
        choices=['all', 'data', 'ml', 'ai', 'semantic', 'search', 'agents',
                 'signals', 'morning-brief', 'earnings-insights', 'automation'],
        default='all',
        help='Scope of build: all=everything (default), '
             'data=dimensions+market+curated+pipelines+ml, ml=train/register/score ML models only, '
             'ai=semantic+search+agents, '
             'semantic=views only, search=services only, agents=agents only, '
             'signals=signal extraction only, morning-brief=briefings only, '
             'earnings-insights=earnings insights only, '
             'automation=install the weekly refresh Code Bundle and task only'
    )
    parser.add_argument(
        '--scenarios',
        type=str,
        default='all',
        help='Comma-separated list of scenarios to build, or "all" (default: all)'
    )
    parser.add_argument(
        '--skip-automation',
        action='store_true',
        help='Do not install the weekly refresh Code Bundle and scheduled task. '
             'Without the automation the demo data stops advancing.'
    )
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Build reduced data volumes for a faster smoke test'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=True,
        help='Verbose output (default in a Workspace, where progress needs to be visible)'
    )
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"  Ignoring unrecognised arguments: {' '.join(unknown)}")
    return args


def main():
    """Run the SAM demo setup inside a Snowflake Workspace or Code Bundle."""
    start_time = datetime.now()
    args = parse_arguments()
    set_verbosity(2)  # Verbose output for workspace visibility

    if args.scenarios.lower() == 'all':
        scenarios = config.AVAILABLE_SCENARIOS
    else:
        # Validate rather than trusting the input: an unrecognised scenario name
        # would otherwise surface much later as confusing missing data.
        scenarios = config.validate_scenarios(
            [s.strip() for s in args.scenarios.split(',')]
        )

    test_mode = args.test_mode

    # Scope booleans, matching python/main.py:450-455 so the two entry points
    # agree on what each scope means.
    build_data = args.scope in ['all', 'data']
    build_ml = args.scope in ['all', 'data', 'ml'] and any(
        s in scenarios for s in config.ML_CONFIG['build_trained_for_scenarios']
    )
    build_semantic = args.scope in ['all', 'ai', 'semantic']
    build_search = args.scope in ['all', 'ai', 'search']
    build_agents = args.scope in ['all', 'ai', 'agents']
    build_signals = args.scope in ['all', 'signals']
    build_briefings = args.scope in ['all', 'morning-brief']
    build_earnings = args.scope in ['all', 'earnings-insights']
    build_automation = (
        args.scope in ['all', 'data', 'automation'] and not args.skip_automation
    )

    session = get_active_session()

    print("=" * 60)
    print("  Simulated Asset Management (SAM) Demo")
    print("  Workspace Setup")
    print("=" * 60)
    print(f"  Database: {config.DATABASE['name']}")
    print(f"  Warehouse: {config.WAREHOUSES['execution']['name']}")
    print(f"  Scope: {args.scope}")
    print(f"  Scenarios: {', '.join(scenarios)}")
    if test_mode:
        print("  Mode: TEST (reduced data volumes)")
    if args.skip_automation:
        print("  Weekly refresh automation: SKIPPED (--skip-automation)")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Ensure correct context. The roles, warehouses and databases come from
    # scripts/workspace_setup.sql, so check they are there before touching them -
    # a missing prerequisite is otherwise a bare "does not exist or not
    # authorized" from the USE statements below.
    from utils.snowflake import verify_prerequisites
    verify_prerequisites(session)

    db_name = config.DATABASE['name']
    session.sql(f"USE ROLE {config.RBAC['platform_build_role']}").collect()
    session.sql(f"USE DATABASE {db_name}").collect()
    session.sql(f"USE WAREHOUSE {config.WAREHOUSES['execution']['name']}").collect()

    data_phases = config.get_data_phases(scenarios)

    # =========================================================================
    # STEP 1: FOUNDATION — Dimension tables
    # =========================================================================
    if build_data:
        log_phase("Step 1: Foundation (Dimension Tables)")

        from data import structured as generate_structured
        from data import market_data as generate_market_data

        generate_structured.create_database_structure(session, recreate_database=False)
        generate_structured.build_dimension_tables(session, test_mode=test_mode)

        log_phase_complete("Foundation complete")

        # =====================================================================
        # STEP 2: MARKET DATA — Real data from Marketplace
        # =====================================================================
        log_phase("Step 2: Market Data (Marketplace)")

        generate_market_data.build_price_anchor(session, test_mode=test_mode)
        generate_market_data.build_fact_dividends(session, test_mode=test_mode)
        generate_market_data.build_all(session, test_mode=test_mode)

        log_phase_complete("Market data complete")

        # =====================================================================
        # STEP 3: CURATED + ANALYTICS — Derived facts, views, attribution
        # =====================================================================
        log_phase("Step 3: Curated + Analytics")

        generate_structured.build_fact_tables(session, test_mode=test_mode)

        generate_structured.reset_build_tracking()
        for scenario in scenarios:
            generate_structured.build_scenario_data(session, scenario)

        generate_structured.validate_data_quality(session)

        # Performance views and analytics
        generate_structured.build_security_returns_view(session)
        generate_structured.build_v_holdings_with_esg(session)

        if 'attribution' in data_phases:
            log_substep("Attribution market data")
            generate_structured.build_attribution_market_data(session)

        if 'factor_exposures' in data_phases:
            log_substep("Factor exposures")
            generate_structured.build_factor_exposures(session)

        if 'attribution' in data_phases:
            log_substep("Attribution tables")
            generate_structured.build_attribution_tables(session)
            generate_structured.build_multi_level_attribution(session)
            generate_structured.build_currency_attribution(session)
            generate_structured.build_attribution_linked(session)
            generate_structured.build_advanced_attribution_views(session)

        if 'portfolio_modelling' in data_phases:
            log_substep("Portfolio modelling views")
            generate_structured.build_portfolio_modelling_views(session)
            generate_structured.build_fact_covariance_matrix(session)

        generate_structured.build_fact_strategy_performance(session)
        generate_structured.build_fact_benchmark_performance(session)
        generate_structured.build_portfolio_benchmark_comparison_view(session)

        log_phase_complete("Curated + analytics complete")

        # =====================================================================
        # STEP 4: PIPELINES + CORPUS — Documents, transcripts, PDFs
        # =====================================================================
        log_phase("Step 4: Pipelines + Corpus")

        from data.coverage_universe import build_coverage_universe
        from data import pipelines as create_unstructured_pipelines
        from utils.config_helpers import get_required_document_types

        build_coverage_universe(session)
        create_unstructured_pipelines.create_all_pipelines(session)

        required_doc_types = get_required_document_types(scenarios)

        # Load real transcripts if available
        if 'company_event_transcripts' in required_doc_types:
            try:
                from data import transcripts as generate_real_transcripts
                if generate_real_transcripts.verify_transcripts_available(session):
                    log_substep("Loading real transcripts")
                    generate_real_transcripts.load_raw_table(session, test_mode=test_mode)
            except Exception as e:
                log_warning(f"Real transcripts: {e}")

        # Load SEC filings
        try:
            log_substep("Loading SEC filings")
            create_unstructured_pipelines.load_sec_filings_raw(session, test_mode=test_mode)
        except Exception as e:
            log_warning(f"SEC filings: {e}")

        # Generate documents from templates
        log_substep("Generating documents from templates")
        from data import unstructured as generate_unstructured
        generate_unstructured.build_all(session, required_doc_types, test_mode=test_mode)

        # Run pipelines (streams → corpus tables)
        log_substep("Executing pipelines")
        create_unstructured_pipelines.run_all_pipelines(session, upload_pdfs=True)
        generate_structured.build_fact_esg_controversy(session)

        log_phase_complete("Pipelines + corpus complete")

        # =====================================================================
        # STEP 5: NLP SCORING + HIDDEN FACTORS (depends on the corpus)
        # =====================================================================
        if 'nlp_scoring' in data_phases:
            log_phase("Step 5: NLP Scoring + Hidden Factors")

            log_substep("Transcript NLP scores")
            generate_market_data.build_transcript_nlp_scores(session, test_mode=test_mode)

            log_substep("Hidden factor exposures")
            generate_structured.build_hidden_factor_exposures(session)

            log_phase_complete("NLP scoring complete")

    # =========================================================================
    # STEP 5b: ML MODELS — train, register (PRODUCTION alias) and batch-score
    # =========================================================================
    if build_ml:
        from ai.tools.ml_models import build_ml_models
        build_ml_models(session)

    # =========================================================================
    # STEP 6: AI COMPONENTS — Semantic views, search services, tools, agents
    # =========================================================================
    if build_semantic or build_search or build_agents:
        log_phase("Step 6: AI Components")

        from ai.proactive_insights import create_proactive_insights_tables
        from ai.signal_store import create_fact_signals
        from ai.thesis_tracker import setup_thesis_tracker
        from ai import builder as build_ai

        # Create infrastructure tables
        create_proactive_insights_tables(session)
        create_fact_signals(session)
        setup_thesis_tracker(session)

        # Builds semantic views, search services, custom tools, agents, agent
        # skills and the agent evaluation datasets.
        build_ai.build_all(
            session,
            scenarios,
            build_semantic=build_semantic,
            build_search=build_search,
            build_agents=build_agents,
            verify_only=False
        )

        log_phase_complete("AI components complete")

    # =========================================================================
    # STEP 7: SIGNAL EXTRACTION + MORNING BRIEFINGS
    # =========================================================================
    if build_signals or build_briefings:
        log_phase("Step 7: Signals + Briefings")

        if build_signals:
            from ai.signal_store import seed_signals
            log_substep("Extracting signals")
            seed_signals(session, test_mode=test_mode, include_tier2=True, include_tier3=False)

        if build_briefings:
            from ai.proactive_insights import (
                DEFAULT_BRIEFING_PERSONAS,
                seed_morning_briefings,
            )
            log_substep("Generating morning briefings")
            seed_morning_briefings(session, personas=DEFAULT_BRIEFING_PERSONAS)

            from ai.proactive_insights import run_proactive_pipeline_once
            log_substep("Running proactive briefing -> alert check -> promote")
            run_proactive_pipeline_once(session)

        log_phase_complete("Signals + briefings complete")

    # =========================================================================
    # STEP 8: EARNINGS INSIGHTS
    # =========================================================================
    if build_earnings:
        log_phase("Step 8: Earnings Insights")

        from ai.earnings_insights import seed_earnings_insights
        seed_earnings_insights(session)

        log_phase_complete("Earnings insights complete")

    # =========================================================================
    # STEP 9: WEEKLY REFRESH AUTOMATION
    # =========================================================================
    # Installed last, against finished tables. From here the demo maintains
    # itself: a task runs the refresh every Monday with nothing to trigger.
    if build_automation:
        log_phase("Step 9: Weekly Refresh Automation")

        from data import automation
        automation_result = automation.setup_weekly_refresh(session, resume=True)
        log_substep(
            f"Weekly refresh scheduled: {automation_result['schedule']} "
            f"({automation_result['uploaded']} source files staged)"
        )

        log_phase_complete("Weekly refresh automation installed")

    # =========================================================================
    # COMPLETE
    # =========================================================================
    end_time = datetime.now()
    duration = end_time - start_time

    agents_created = [
        (config.SCENARIO_AGENTS[s]['agent_name'], config.SCENARIO_AGENTS[s]['description'])
        for s in scenarios
        if s in config.SCENARIO_AGENTS
    ] if build_agents else []

    print()
    print("=" * 60)
    print("  SAM Demo — Setup Complete")
    print("=" * 60)
    print(f"  Duration: {duration}")
    print(f"  Database: {db_name}")
    print(f"  Scope: {args.scope}")
    print()
    if agents_created:
        print("  Agents Ready:")
        for agent_name, description in agents_created:
            print(f"    - {agent_name}")
        print()
        print("  Next Steps:")
        print("    1. Open Snowflake CoWork")
        print("    2. Select any of the agents above")
        print("    3. Start asking questions!")
    print("=" * 60)


if __name__ == "__main__":
    main()
