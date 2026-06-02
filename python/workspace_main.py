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
when running inside a Snowflake Git Workspace.

Prerequisites:
  1. Run scripts/workspace_setup.sql in a Snowflake worksheet (creates DB, roles, grants)
  2. Create a Git Workspace from this repository
  3. Connect a notebook service (Python 3.11+, any compute pool)
  4. Install packages: snowflake-snowpark-python, pyyaml, jinja2

Usage:
  Open this file in the workspace and click "Run"

What it builds:
  - 48+ CURATED tables (dimensions, facts, views) from 14,000+ real securities
  - 9 MARKET_DATA tables (real SEC financials, prices, segments)
  - 15 RAW document tables + corpus tables
  - 10 Semantic Views (Cortex Analyst)
  - 16 Cortex Search services
  - 8 Cortex Agents (portfolio, research, sales, executive, risk, ops, credit, PE)
  - 36 Agent skills uploaded to SKILL_STAGE
  - Tools: backtest, Monte Carlo, PDF generator, M&A simulation
"""

import os
import sys
from datetime import datetime

# Ensure the python/ directory is on the path for imports
# Note: In Snowflake Workspaces, __file__ is not defined.
# The working directory is /workspace/<hash>/ (the workspace root).
# Python files reference other files by relative path from the workspace root.
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


def main():
    """Run the complete SAM demo setup inside a Snowflake Workspace."""
    start_time = datetime.now()
    set_verbosity(2)  # Verbose output for workspace visibility

    session = get_active_session()

    print("=" * 60)
    print("  Simulated Asset Management (SAM) Demo")
    print("  Workspace Setup")
    print("=" * 60)
    print(f"  Database: {session.get_current_database() or config.DATABASE['name']}")
    print(f"  Warehouse: {session.get_current_warehouse() or 'SAM_DEMO_WH'}")
    print(f"  Scenarios: {', '.join(config.AVAILABLE_SCENARIOS)}")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Ensure correct context
    db_name = config.DATABASE['name']
    session.sql(f"USE DATABASE {db_name}").collect()
    session.sql(f"USE WAREHOUSE SAM_DEMO_WH").collect()

    # =========================================================================
    # STEP 1: FOUNDATION — Dimension tables
    # =========================================================================
    log_phase("Step 1: Foundation (Dimension Tables)")

    from data import structured as generate_structured
    from data import market_data as generate_market_data

    generate_structured.create_database_structure(session, recreate_database=False)
    generate_structured.build_dimension_tables(session, test_mode=False)

    log_phase_complete("Foundation complete")

    # =========================================================================
    # STEP 2: MARKET DATA — Real data from Marketplace
    # =========================================================================
    log_phase("Step 2: Market Data (Marketplace)")

    generate_market_data.build_price_anchor(session, test_mode=False)
    generate_market_data.build_fact_dividends(session, test_mode=False)
    generate_market_data.build_all(session, test_mode=False)

    log_phase_complete("Market data complete")

    # =========================================================================
    # STEP 3: CURATED + ANALYTICS — Derived facts, views, attribution
    # =========================================================================
    log_phase("Step 3: Curated + Analytics")

    generate_structured.build_fact_tables(session, test_mode=False)

    generate_structured.reset_build_tracking()
    for scenario in config.AVAILABLE_SCENARIOS:
        generate_structured.build_scenario_data(session, scenario)

    generate_structured.validate_data_quality(session)

    # Performance views and analytics
    generate_structured.build_security_returns_view(session)
    generate_structured.build_v_holdings_with_esg(session)

    data_phases = config.get_data_phases(config.AVAILABLE_SCENARIOS)

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

    # =========================================================================
    # STEP 4: PIPELINES + CORPUS — Documents, transcripts, PDFs
    # =========================================================================
    log_phase("Step 4: Pipelines + Corpus")

    from data.coverage_universe import build_coverage_universe
    from data import pipelines as create_unstructured_pipelines
    from utils.config_helpers import get_required_document_types

    build_coverage_universe(session)
    create_unstructured_pipelines.create_all_pipelines(session)

    required_doc_types = get_required_document_types(config.AVAILABLE_SCENARIOS)

    # Load real transcripts if available
    if 'company_event_transcripts' in required_doc_types:
        try:
            from data import transcripts as generate_real_transcripts
            if generate_real_transcripts.verify_transcripts_available(session):
                log_substep("Loading real transcripts")
                generate_real_transcripts.load_raw_table(session, test_mode=False)
        except Exception as e:
            log_warning(f"Real transcripts: {e}")

    # Load SEC filings
    try:
        log_substep("Loading SEC filings")
        create_unstructured_pipelines.load_sec_filings_raw(session, test_mode=False)
    except Exception as e:
        log_warning(f"SEC filings: {e}")

    # Generate documents from templates
    log_substep("Generating documents from templates")
    from data import unstructured as generate_unstructured
    generate_unstructured.build_all(session, required_doc_types, test_mode=False)

    # Run pipelines (streams → corpus tables)
    log_substep("Executing pipelines")
    create_unstructured_pipelines.run_all_pipelines(session, upload_pdfs=True)

    log_phase_complete("Pipelines + corpus complete")

    # =========================================================================
    # STEP 5: NLP SCORING + HIDDEN FACTORS (optional, depends on data phases)
    # =========================================================================
    if 'nlp_scoring' in data_phases:
        log_phase("Step 5: NLP Scoring + Hidden Factors")

        log_substep("Transcript NLP scores")
        generate_market_data.build_transcript_nlp_scores(session, test_mode=False)

        log_substep("Hidden factor exposures")
        generate_structured.build_hidden_factor_exposures(session)

        log_phase_complete("NLP scoring complete")

    # =========================================================================
    # STEP 6: AI COMPONENTS — Semantic views, search services, tools, agents
    # =========================================================================
    log_phase("Step 6: AI Components")

    from ai.proactive_insights import create_proactive_insights_tables
    from ai.signal_store import create_fact_signals
    from ai.thesis_tracker import setup_thesis_tracker
    from ai import builder as build_ai

    # Create infrastructure tables
    create_proactive_insights_tables(session)
    create_fact_signals(session)
    setup_thesis_tracker(session)

    # Build all AI components (semantic views + search + agents + tools + skills)
    build_ai.build_all(
        session,
        config.AVAILABLE_SCENARIOS,
        build_semantic=True,
        build_search=True,
        build_agents=True,
        verify_only=False
    )

    log_phase_complete("AI components complete")

    # =========================================================================
    # STEP 7: SIGNAL EXTRACTION + MORNING BRIEFINGS
    # =========================================================================
    log_phase("Step 7: Signals + Briefings")

    from ai.signal_store import seed_signals
    log_substep("Extracting signals")
    seed_signals(session, test_mode=False, include_tier2=True, include_tier3=False)

    from ai.proactive_insights import seed_morning_briefings
    log_substep("Generating morning briefings")
    seed_morning_briefings(session, personas=[
        'equity', 'credit', 'pe', 'executive',
        'risk-compliance', 'operations',
    ])

    log_phase_complete("Signals + briefings complete")

    # =========================================================================
    # STEP 8: EARNINGS INSIGHTS
    # =========================================================================
    log_phase("Step 8: Earnings Insights")

    from ai.earnings_insights import seed_earnings_insights
    seed_earnings_insights(session)

    log_phase_complete("Earnings insights complete")

    # =========================================================================
    # COMPLETE
    # =========================================================================
    end_time = datetime.now()
    duration = end_time - start_time

    agents_created = [
        (config.SCENARIO_AGENTS[s]['agent_name'], config.SCENARIO_AGENTS[s]['description'])
        for s in config.AVAILABLE_SCENARIOS
        if s in config.SCENARIO_AGENTS
    ]

    print()
    print("=" * 60)
    print("  SAM Demo — Setup Complete")
    print("=" * 60)
    print(f"  Duration: {duration}")
    print(f"  Database: {db_name}")
    print()
    if agents_created:
        print("  Agents Ready:")
        for agent_name, description in agents_created:
            print(f"    - {agent_name}")
    print()
    print("  Next Steps:")
    print("    1. Open Snowflake Intelligence")
    print("    2. Select any of the agents above")
    print("    3. Start asking questions!")
    print("=" * 60)


if __name__ == "__main__":
    main()
