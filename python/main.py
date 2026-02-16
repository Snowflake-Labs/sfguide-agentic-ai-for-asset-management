#!/usr/bin/env python3
# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Simulated Asset Management (SAM) Demo - Main CLI Orchestrator

This script orchestrates the creation of the complete SAM demo environment,
including structured data generation, unstructured content creation, and AI component setup.

Usage:
    python main.py --connection-name CONNECTION [--scenarios SCENARIO_LIST] [--scope SCOPE]

Examples:
    python main.py --connection-name my_demo                              # Build everything 
    python main.py --connection-name my_demo --scenarios portfolio_copilot # Build foundation + portfolio scenario
    python main.py --connection-name my_demo --scope structured          # Build only structured data (tables)
    python main.py --connection-name my_demo --scope unstructured        # Build only unstructured data (documents)
    python main.py --connection-name my_demo --scope data                # Build structured + unstructured data
    python main.py --connection-name my_demo --scope ai                  # Build only AI components (semantic + search)
    python main.py --connection-name my_demo --test-mode                 # Use test mode
"""

import argparse
import sys
from typing import List, Optional
from datetime import datetime

# Import configuration
import config
from config import (
    DEFAULT_CONNECTION_NAME, 
    AVAILABLE_SCENARIOS,
    SCENARIO_AGENTS,
    DATABASE,
    WAREHOUSES
)
from logging_utils import (
    set_verbosity, log_phase, log_step, log_substep, log_detail, log_error, log_warning, log_phase_complete
)
from scenario_utils import get_required_document_types

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
        choices=['all', 'data', 'structured', 'unstructured', 'ai', 'semantic', 'search', 'agents'],
        default='all',
        help='Scope of build: all=everything, data=structured+unstructured, structured=tables only, unstructured=documents only, ai=semantic+search+agents, semantic=views only, search=services only, agents=agents only'
    )
    
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Use test mode with 10 percent of data for faster development testing (500 securities vs 5,000)'
    )
    
    return parser.parse_args()

def validate_scenarios(scenario_list: List[str]) -> List[str]:
    """Validate and return list of valid scenarios."""
    invalid_scenarios = [s for s in scenario_list if s not in AVAILABLE_SCENARIOS]
    if invalid_scenarios:
        log_error(f"Invalid scenarios: {invalid_scenarios}")
        log_warning(f"Available scenarios: {AVAILABLE_SCENARIOS}")
        sys.exit(1)
    
    return scenario_list

def create_snowpark_session(connection_name: str):
    """Create and validate Snowpark session."""
    try:
        from snowflake.snowpark import Session
        
        session = Session.builder.config("connection_name", connection_name).create()
        
        # Test connection
        result = session.sql("SELECT CURRENT_VERSION()").collect()
        
        # Create dedicated warehouses for the demo
        create_demo_warehouses(session)
        
        return session
        
    except ImportError:
        log_error("snowflake-snowpark-python not installed. Install with: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        log_error(f"Connection failed: {str(e)}")
        log_warning(f"Ensure connection '{connection_name}' exists in ~/.snowflake/connections.toml")
        sys.exit(1)

def validate_real_data_access(session):
    """Validate access to SNOWFLAKE_PUBLIC_DATA_FREE before starting build.
    
    This demo requires access to real SEC financial data from Snowflake Marketplace.
    The build will fail if access is not available.
    """
    from config import REAL_DATA_SOURCES
    from db_helpers import verify_table_access
    
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
        log_error("This demo requires access to SNOWFLAKE_PUBLIC_DATA_FREE.")
        log_error("Please add this database from Snowflake Marketplace and retry.")
        log_detail(f"Error details: {error_msg}")
        raise SystemExit(1)


def create_demo_warehouses(session):
    """Create dedicated warehouses for demo execution and Cortex Search services."""
    try:
        
        
        # Get warehouse configs from structured config
        execution_wh = WAREHOUSES['execution']['name']
        execution_size = WAREHOUSES['execution']['size']
        execution_comment = WAREHOUSES['execution']['comment']
        
        cortex_wh = WAREHOUSES['cortex_search']['name']
        cortex_size = WAREHOUSES['cortex_search']['size']
        cortex_comment = WAREHOUSES['cortex_search']['comment']
        
        # Create execution warehouse for data generation and code execution
        session.sql(f"""
            CREATE OR REPLACE WAREHOUSE {execution_wh}
            WITH WAREHOUSE_SIZE = {execution_size}
            AUTO_SUSPEND = 60
            AUTO_RESUME = TRUE
            COMMENT = '{execution_comment}'
        """).collect()
        
        
        # Create Cortex Search warehouse for search services
        session.sql(f"""
            CREATE OR REPLACE WAREHOUSE {cortex_wh}
            WITH WAREHOUSE_SIZE = {cortex_size}
            AUTO_SUSPEND = 60
            AUTO_RESUME = TRUE
            COMMENT = '{cortex_comment}'
        """).collect()
        
        
        # Set session to use execution warehouse by default
        session.use_warehouse(execution_wh)
        
        
    except Exception as e:
        log_error(f"Failed to create warehouses: {e}")
        log_error("Warehouses are required for all build operations.")
        raise
        

def main():
    """Main execution function."""
    start_time = datetime.now()
    
    # Parse arguments first to set verbosity
    args = parse_arguments()
    
    # Set verbosity based on args (could add --verbose flag later)
    set_verbosity(2)  # Default to minimal output
    
    # Parse and validate scenarios
    if args.scenarios.lower() == 'all':
        scenario_list = AVAILABLE_SCENARIOS
    else:
        scenario_list = [s.strip() for s in args.scenarios.split(',')]
    validated_scenarios = validate_scenarios(scenario_list)
    
    # Print start summary
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
    print(f"{'='*60}")
    
    # Create Snowpark session
    session = create_snowpark_session(args.connection_name)
    
    # Validate access to real data source (required)
    validate_real_data_access(session)
    
    # Determine what to build based on scope
    build_structured = args.scope in ['all', 'data', 'structured']
    build_unstructured = args.scope in ['all', 'data', 'unstructured']
    build_semantic = args.scope in ['all', 'ai', 'semantic'] 
    build_search = args.scope in ['all', 'ai', 'search']
    build_agents = args.scope in ['all', 'ai', 'agents']
    
    try:
        # Step 1: Build structured data (foundation + scenario-specific)
        if build_structured:
            log_phase("Structured Data")
            import generate_structured
            import generate_market_data
            
            # Only recreate database when running full build (scope=all)
            # For data/structured scopes, preserve existing AI components
            recreate_database = (args.scope == 'all')
            
            # Step 1a: Create database structure
            generate_structured.create_database_structure(session, recreate_database=recreate_database)
            
            # Step 1b: Build dimension tables (do not depend on max_price_date)
            log_step("Dimension tables")
            generate_structured.build_dimension_tables(session, args.test_mode)
            
            # Step 1c: Build FACT_STOCK_PRICES as date anchor
            # This MUST happen before fact tables so they can use max_price_date
            log_substep("Price anchor (FACT_STOCK_PRICES)")
            generate_market_data.build_price_anchor(session, args.test_mode)
            
            # Step 1d: Build fact tables (depend on max_price_date from stock prices)
            log_step("Fact tables")
            generate_structured.build_fact_tables(session, args.test_mode)
            
            # Step 1e: Build scenario-specific data
            for scenario in validated_scenarios:
                generate_structured.build_scenario_data(session, scenario)
            
            # Step 1f: Validate data quality
            generate_structured.validate_data_quality(session)
            
            log_phase_complete("Structured data complete")
            
            # Build remaining MARKET_DATA schema tables (SEC filings, financial data, estimates)
            market_data_scenarios = {'research_copilot', 'portfolio_copilot', 'compliance_advisor', 'all'}
            if market_data_scenarios.intersection(set(validated_scenarios)):
                try:
                    generate_market_data.build_all(session, args.test_mode)
                    
                    # Build returns view and update enriched holdings (requires FACT_STOCK_PRICES from market data)
                    log_substep("Security returns and enriched holdings")
                    generate_structured.build_security_returns_view(session)
                    generate_structured.build_esg_latest_view(session)  # Rebuild to include returns
                    
                    # Build strategy performance table (requires V_HOLDINGS_WITH_ESG with returns)
                    log_substep("Strategy performance metrics")
                    generate_structured.build_fact_strategy_performance(session)
                    
                    # Build benchmark performance table (requires FACT_STOCK_PRICES and FACT_BENCHMARK_HOLDINGS)
                    log_substep("Benchmark performance metrics")
                    generate_structured.build_fact_benchmark_performance(session)
                    
                    # Build portfolio vs benchmark comparison view (requires V_HOLDINGS_WITH_ESG and FACT_BENCHMARK_PERFORMANCE)
                    log_substep("Portfolio vs benchmark comparison view")
                    generate_structured.build_portfolio_benchmark_comparison_view(session)
                except Exception as e:
                    log_error(f"MARKET_DATA generation failed: {e}")
                    log_error("Market data is required for performance metrics in semantic views.")
                    raise
            
        # Step 2: Build unstructured data (documents and content)
        if build_unstructured:
            log_phase("Unstructured Data")
            
            # Validate that structured data exists (unstructured depends on it)
            try:
                session.sql(f"SELECT COUNT(*) FROM {DATABASE['name']}.CURATED.DIM_SECURITY LIMIT 1").collect()
            except Exception as e:
                log_error("Unstructured data generation requires structured data to exist first.")
                log_warning("Run with --scope structured first, or use --scope data to build both together.")
                raise
            
            import generate_unstructured
            required_doc_types = get_required_document_types(validated_scenarios)
            generate_unstructured.build_all(session, required_doc_types, args.test_mode)
            
            # Build real company event transcripts (replaces synthetic earnings transcripts)
            # Only run if company_event_transcripts is in required document types
            if 'company_event_transcripts' in required_doc_types:
                try:
                    import generate_real_transcripts
                    if generate_real_transcripts.verify_transcripts_available(session):
                        generate_real_transcripts.build_all(session, args.test_mode)
                    else:
                        log_warning("Real transcripts source not available, skipping...")
                except Exception as e:
                    log_warning(f"Real transcripts generation failed (will use synthetic): {e}")
            
            log_phase_complete("Unstructured data complete")
        
        # Step 3: Build AI components
        if build_semantic or build_search or build_agents:
            log_phase("AI Components")
            import build_ai
            build_ai.build_all(session, validated_scenarios, build_semantic, build_search, build_agents)
            log_phase_complete("AI components complete")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Get list of agents created based on validated scenarios
        agents_created = [
            (SCENARIO_AGENTS[s]['agent_name'], SCENARIO_AGENTS[s]['description']) 
            for s in validated_scenarios 
            if s in SCENARIO_AGENTS
        ]
        
        # Print end summary
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
        print(f"  ❌ BUILD FAILED after {duration}")
        print(f"  Error: {str(e)}")
        print(f"{'='*60}\n")
        sys.exit(1)
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()
