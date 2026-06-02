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
Enhanced Structured Data Generation for SAM Demo
Following industry-standard portfolio model with immutable SecurityID and transaction-based holdings.

This module generates:
- Dimension tables: DIM_SECURITY, DIM_ISSUER, DIM_PORTFOLIO, DIM_BENCHMARK, DIM_DATE
- Fact tables: FACT_TRANSACTION, FACT_POSITION_DAILY_ABOR, FACT_MARKETDATA_TIMESERIES
- Security identifier cross-reference table
- Enhanced fundamentals, ESG, and factor data
"""

from snowflake.snowpark import Session
from typing import List
import random
from datetime import datetime, timedelta, date
import config
from utils.logging import log_detail, log_info, log_warning, log_error, log_success, log_phase, log_step, log_substep, log_phase_complete
from data.market_data import build_fact_credit_sector_benchmarks
from utils.snowflake import get_max_price_date
from utils.sql import (
    safe_sql_tuple,
    build_sector_case_sql,
    build_country_group_case_sql,
    build_grade_case_sql,
    build_overall_esg_sql,
    build_strategy_case_sql,
    build_global_uniform_sql,
    build_factor_case_sql,
    get_factor_r_squared,
    build_country_settlement_case_sql
)
from utils.demo_helpers import build_demo_portfolios_sql_mapping, get_demo_portfolio_names, get_demo_clients_sorted, get_demo_company_tickers, get_all_demo_clients_sorted, get_at_risk_client_ids, get_new_client_ids, get_new_demo_clients

_completed_shared_builds = set()

def reset_build_tracking():
    _completed_shared_builds.clear()

def build_all(session: Session, scenarios: List[str], test_mode: bool = False, recreate_database: bool = True):
    """
    Build all structured data using the enhanced data model.
    
    Args:
        session: Active Snowpark session
        scenarios: List of scenario names to build data for
        test_mode: If True, use 10% data volumes for faster testing
        recreate_database: If True, drop and recreate the database. If False, only ensure schemas exist.
    """
    
    # Step 1: Create database and schemas
    create_database_structure(session, recreate_database=recreate_database)
    
    reset_build_tracking()
    
    # Step 2: Build foundation tables in dependency order
    build_foundation_tables(session, test_mode)
    
    # Step 3: Build scenario-specific structured data
    for scenario in scenarios:
        build_scenario_data(session, scenario)
    
    # Step 4: Validate data quality
    validate_data_quality(session)
    

def create_database_structure(session: Session, recreate_database: bool = True):
    """Create database and schema structure.
    
    Args:
        session: Active Snowpark session
        recreate_database: If True, drop and recreate the database (destroys all data).
                          If False, only ensure schemas exist (preserves existing data).
    """
    try:
        if recreate_database:
            # Clean up agents from Snowflake Intelligence before dropping database
            # Agents are registered with SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT which is
            # outside our database, so we need to explicitly unregister them
            try:
                from ai import agents as create_agents
                create_agents.cleanup_all_agents(session)
            except Exception:
                pass  # Suppress any cleanup errors - agents may not exist
            
            # Full recreation - drops everything and starts fresh
            session.sql(f"CREATE OR REPLACE DATABASE {config.DATABASE['name']}").collect()
            session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.RAW").collect()
            session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.CURATED").collect()
            session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.AI").collect()
            session.sql(f"CREATE SCHEMA IF NOT EXISTS {config.DATABASE['name']}.MARKET_DATA").collect()
            session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.ML").collect()
        else:
            # Incremental mode - ensure database and schemas exist but don't drop
            session.sql(f"CREATE DATABASE IF NOT EXISTS {config.DATABASE['name']}").collect()
            session.sql(f"CREATE SCHEMA IF NOT EXISTS {config.DATABASE['name']}.RAW").collect()
            session.sql(f"CREATE SCHEMA IF NOT EXISTS {config.DATABASE['name']}.CURATED").collect()
            session.sql(f"CREATE SCHEMA IF NOT EXISTS {config.DATABASE['name']}.AI").collect()
            session.sql(f"CREATE SCHEMA IF NOT EXISTS {config.DATABASE['name']}.MARKET_DATA").collect()
            session.sql(f"CREATE SCHEMA IF NOT EXISTS {config.DATABASE['name']}.ML").collect()
    except Exception as e:
        log_error(f" Failed to create database structure: {e}")
        raise


def _run_build_step(func, session, *args, **kwargs):
    """Wrapper to run a build function with proper error reporting."""
    func_name = func.__name__
    try:
        log_info(f"→ {func_name}")
        func(session, *args, **kwargs)
    except Exception as e:
        log_error(f"FAILED in {func_name}: {e}")
        raise


def build_dimension_tables(session: Session, test_mode: bool = False):
    """
    Build dimension tables that do NOT depend on max_price_date.
    These must be built BEFORE FACT_STOCK_PRICES is created.
    """
    random.seed(config.RNG_SEED)
    
    # Ensure database context is set at the start
    database_name = config.DATABASE['name']
    session.sql(f"USE DATABASE {database_name}").collect()
    session.sql(f"USE SCHEMA {config.DATABASE['schemas']['curated']}").collect()
    
    # Build dimension tables from DEMO_COMPANIES config
    # DIM_ISSUER is the driver table - all other data flows from it
    _run_build_step(build_dim_issuer, session, test_mode)
    _run_build_step(build_dim_security, session, test_mode)
    _run_build_step(build_dim_portfolio, session)
    _run_build_step(build_dim_portfolio_manager, session)
    _run_build_step(build_dim_benchmark, session)
    _run_build_step(build_dim_portfolio_ips, session)
    _run_build_step(build_dim_supply_chain_relationships, session, test_mode)
    
    # Middle office dimension tables
    _run_build_step(build_dim_counterparty, session)
    _run_build_step(build_dim_custodian, session)


def build_fact_tables(session: Session, test_mode: bool = False):
    """
    Build fact tables that depend on max_price_date.
    Must be called AFTER FACT_STOCK_PRICES exists to anchor date ranges.
    """
    random.seed(config.RNG_SEED)
    
    # Ensure database context is set at the start
    database_name = config.DATABASE['name']
    session.sql(f"USE DATABASE {database_name}").collect()
    session.sql(f"USE SCHEMA {config.DATABASE['schemas']['curated']}").collect()
    
    # Verify max_price_date is available (FACT_STOCK_PRICES must exist)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        log_error("FACT_STOCK_PRICES must be built before fact tables")
        raise RuntimeError("Missing price date anchor - build FACT_STOCK_PRICES first")
    log_detail(f"Using max_price_date anchor: {max_price_date}")
    
    # Build fact tables that depend on max_price_date
    _run_build_step(build_fact_transaction, session, test_mode)
    _run_build_step(build_fact_position_daily_abor, session)
    _run_build_step(build_esg_scores, session)
    _run_build_step(build_v_esg_latest, session)  # Standalone ESG view (no returns dependency)
    # Note: V_HOLDINGS_WITH_ESG is built later in main.py after V_SECURITY_RETURNS exists
    # Note: build_factor_exposures moved to main.py — requires FACT_SEC_FINANCIALS + V_SECURITY_RETURNS + FACT_BENCHMARK_RETURNS (from build_attribution_market_data)
    _run_build_step(build_benchmark_holdings, session)
    _run_build_step(build_transaction_cost_data, session)
    _run_build_step(build_liquidity_data, session)
    _run_build_step(build_risk_budget_data, session)
    _run_build_step(build_trading_calendar_data, session)
    _run_build_step(build_client_mandate_data, session)
    _run_build_step(build_tax_implications_data, session)
    
    # Executive copilot tables (client analytics)
    _run_build_step(build_dim_client, session, test_mode)
    _run_build_step(build_fact_client_flows, session, test_mode)
    _run_build_step(build_fact_fund_flows, session)
    
    # Middle office fact tables
    _run_build_step(build_fact_trade_settlement, session, test_mode)
    _run_build_step(build_fact_reconciliation, session, test_mode)
    _run_build_step(build_fact_nav_calculation, session, test_mode)
    _run_build_step(build_fact_nav_components, session, test_mode)
    _run_build_step(build_fact_corporate_actions, session, test_mode)
    _run_build_step(build_fact_corporate_action_impact, session, test_mode)
    _run_build_step(build_fact_cash_movements, session, test_mode)
    _run_build_step(build_fact_cash_positions, session, test_mode)
    
    # Portfolio modelling tables (backtesting, simulation, risk analysis)
    # Note: Tables that don't depend on V_SECURITY_RETURNS are built here
    # build_fact_covariance_matrix depends on V_SECURITY_RETURNS and is built later in main.py
    _run_build_step(build_dim_model_portfolio, session)
    _run_build_step(build_fact_model_portfolio_weights, session)
    _run_build_step(build_fact_risk_factors, session)
    _run_build_step(build_fact_expected_returns, session)
    _run_build_step(build_fact_backtest_results, session)
    _run_build_step(build_fact_simulation_results, session)


def build_foundation_tables(session: Session, test_mode: bool = False):
    """
    Build all foundation tables in dependency order.
    
    Note: Prefer using build_dimension_tables() + build_fact_tables() separately
    for proper date anchoring. This function will skip fact tables if
    max_price_date is not available.
    """
    random.seed(config.RNG_SEED)
    
    # Ensure database context is set at the start
    database_name = config.DATABASE['name']
    session.sql(f"USE DATABASE {database_name}").collect()
    session.sql(f"USE SCHEMA {config.DATABASE['schemas']['curated']}").collect()
    
    # Always build dimension tables
    build_dimension_tables(session, test_mode)
    
    # Check if FACT_STOCK_PRICES exists for date anchoring
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build fact tables. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Build fact tables with date anchoring
    build_fact_tables(session, test_mode)




def build_dim_issuer(session: Session, test_mode: bool = False):
    """
    Build DIM_ISSUER as the DRIVER TABLE directly from config.DEMO_COMPANIES.
    
    This is the single source of truth for all companies in the demo.
    All other data (DIM_SECURITY, transcripts, market data, documents) 
    flows from DIM_ISSUER.
    
    Columns:
        - IssuerID: Internal ID (auto-generated)
        - ProviderCompanyID: COMPANY_ID from COMPANY_INDEX (for linking to external data)
        - CIK: SEC Central Index Key (for SEC filings and transcripts)
        - PrimaryTicker: Stock ticker symbol
        - LegalName: Company name
        - Sector: Industry sector from DEMO_COMPANIES config
        - CountryOfIncorporation: Country (from COMPANY_INDEX or default 'US')
        - LEI: Legal Entity Identifier (from COMPANY_INDEX or generated)
    """
    
    from snowflake.snowpark.types import StructType, StructField, StringType

    demo_companies = config.DEMO_COMPANIES

    rows = [
        (ticker, d['company_name'], d['provider_company_id'], d['cik'], d['sector'], d['tier'])
        for ticker, d in demo_companies.items()
    ]
    schema = StructType([
        StructField("TICKER", StringType()),
        StructField("COMPANY_NAME", StringType()),
        StructField("PROVIDER_COMPANY_ID", StringType()),
        StructField("CIK", StringType()),
        StructField("SECTOR", StringType()),
        StructField("TIER", StringType()),
    ])
    dc_df = session.create_dataframe(rows, schema=schema)
    dc_df.write.save_as_table(
        f"{config.DATABASE['name']}.CURATED.STG_DEMO_COMPANIES",
        mode="overwrite",
        table_type="temporary",
    )

    db = config.REAL_DATA_SOURCES['database']
    sch = config.REAL_DATA_SOURCES['schema']
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.DIM_ISSUER AS
        WITH enriched AS (
            SELECT 
                dc.TICKER,
                dc.COMPANY_NAME,
                dc.PROVIDER_COMPANY_ID,
                dc.CIK,
                dc.SECTOR,
                dc.TIER,
                ci.LEI,
                MAX(CASE WHEN cc.RELATIONSHIP_TYPE = 'business_address_country' THEN cc.VALUE END) as CountryFromIndex
            FROM {config.DATABASE['name']}.CURATED.STG_DEMO_COMPANIES dc
            INNER JOIN {db}.{sch}.COMPANY_INDEX ci
                ON dc.PROVIDER_COMPANY_ID = ci.COMPANY_ID
            LEFT JOIN {db}.{sch}.COMPANY_CHARACTERISTICS cc
                ON ci.COMPANY_ID = cc.COMPANY_ID
            GROUP BY dc.TICKER, dc.COMPANY_NAME, dc.PROVIDER_COMPANY_ID, dc.CIK, dc.SECTOR, dc.TIER, ci.LEI
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY 
                CASE TIER WHEN 'core' THEN 1 WHEN 'major' THEN 2 ELSE 3 END,
                COMPANY_NAME
            ) as IssuerID,
            NULL as UltimateParentIssuerID,
            PROVIDER_COMPANY_ID as ProviderCompanyID,
            CIK,
            TICKER as PrimaryTicker,
            SUBSTR(TRIM(COMPANY_NAME), 1, 255) as LegalName,
            SECTOR as SIC_DESCRIPTION,
            SECTOR as GICS_SECTOR,
            COALESCE(CountryFromIndex, 'US') as CountryOfIncorporation,
            LEI[0]::VARCHAR as LEI,
            TIER as Tier
        FROM enriched
        ORDER BY IssuerID
    """).collect()
    
    # Validate that all demo companies were matched in real data source
    expected_count = len(demo_companies)
    issuer_count = session.sql(f"SELECT COUNT(*) as cnt FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER").collect()[0]['CNT']
    if issuer_count != expected_count:
        raise RuntimeError(
            f"DIM_ISSUER build failed: expected {expected_count} issuers from DEMO_COMPANIES, "
            f"but only {issuer_count} matched in real data source. "
            f"Check that all DEMO_COMPANIES have valid provider_company_id values in "
            f"{config.REAL_DATA_SOURCES['database']}.{config.REAL_DATA_SOURCES['schema']}.COMPANY_INDEX"
        )
    
    log_success(f"  DIM_ISSUER: {issuer_count} issuers (driver table)")
    
    # Report on data quality
    quality_stats = session.sql(f"""
        SELECT 
            COUNT(*) as total_issuers,
            COUNT(CASE WHEN CIK IS NOT NULL AND CIK != '' THEN 1 END) as issuers_with_cik,
            COUNT(CASE WHEN ProviderCompanyID IS NOT NULL AND ProviderCompanyID != '' THEN 1 END) as issuers_with_provider_id,
            COUNT(CASE WHEN Tier = 'core' THEN 1 END) as core_companies,
            COUNT(CASE WHEN Tier = 'major' THEN 1 END) as major_companies,
            COUNT(CASE WHEN Tier = 'additional' THEN 1 END) as additional_companies
        FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER
    """).collect()[0]
    
    log_info(f"    Core: {quality_stats['CORE_COMPANIES']}, Major: {quality_stats['MAJOR_COMPANIES']}, Additional: {quality_stats['ADDITIONAL_COMPANIES']}")
    log_info(f"    With CIK: {quality_stats['ISSUERS_WITH_CIK']}, With Provider ID: {quality_stats['ISSUERS_WITH_PROVIDER_ID']}")



def build_dim_security(session: Session, test_mode: bool = False):
    """
    Build DIM_SECURITY directly from DIM_ISSUER (one equity security per issuer).
    
    This function derives securities from the DIM_ISSUER driver table:
    - One security per issuer (equities only, no bonds/ETFs)
    - FIGI is a placeholder derived from ticker (no external lookup)
    - Direct 1:1 relationship with DIM_ISSUER
    - All company info comes from DEMO_COMPANIES via DIM_ISSUER
    """
    
    # Build security dimension directly from DIM_ISSUER (no OPENFIGI lookup)
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.DIM_SECURITY AS
        SELECT 
            ROW_NUMBER() OVER (ORDER BY IssuerID) as SecurityID,
            IssuerID,
            PrimaryTicker as Ticker,
            'FIGI_' || PrimaryTicker as FIGI,  -- Placeholder FIGI derived from ticker
            LegalName as Description,
            'Equity' as AssetClass,
            'Common Stock' as SecurityType,
            CountryOfIncorporation as CountryOfRisk,
            DATE('2010-01-01') as IssueDate,
            NULL as MaturityDate,
            NULL as CouponRate,
            CURRENT_TIMESTAMP() as RecordStartDate,
            NULL as RecordEndDate,
            TRUE as IsActive
        FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER
        WHERE PrimaryTicker IS NOT NULL
        ORDER BY SecurityID
    """).collect()
    
    # Get and report counts
    security_count = session.sql(f"""
        SELECT COUNT(*) as total
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY
    """).collect()[0]
    
    log_success(f"  DIM_SECURITY: {security_count['TOTAL']} securities (1 per issuer, derived from DIM_ISSUER)")


def build_dim_portfolio(session: Session):
    """Build portfolio dimension from unified PORTFOLIOS configuration.
    
    Includes BenchmarkID to link each portfolio to its benchmark for
    portfolio vs benchmark performance comparison in semantic views.
    """
    log_detail("  Building DIM_PORTFOLIO...")
    
    # Build benchmark name -> ID mapping from config.BENCHMARKS
    benchmark_name_to_id = {b['name']: i + 1 for i, b in enumerate(config.BENCHMARKS)}
    
    portfolio_data = []
    for i, (portfolio_name, portfolio_config) in enumerate(config.PORTFOLIOS.items()):
        # All portfolio config fields are required
        strategy = portfolio_config['strategy']
        
        # Look up BenchmarkID from the portfolio's benchmark name
        benchmark_name = portfolio_config['benchmark']
        if benchmark_name not in benchmark_name_to_id:
            raise ValueError(
                f"Portfolio '{portfolio_name}' references benchmark '{benchmark_name}' "
                f"which is not defined in config.BENCHMARKS"
            )
        benchmark_id = benchmark_name_to_id[benchmark_name]
            
        portfolio_data.append({
            'PortfolioID': i + 1,
            'PortfolioCode': f"{config.DATA_MODEL['portfolio_code_prefix']}_{i+1:02d}",
            'PortfolioName': portfolio_name,
            'Strategy': strategy,
            'BaseCurrency': portfolio_config['base_currency'],
            'InceptionDate': datetime.strptime(portfolio_config['inception_date'], '%Y-%m-%d').date(),
            'BenchmarkID': benchmark_id
        })
    
    portfolios_df = session.create_dataframe(portfolio_data)
    portfolios_df.write.mode("overwrite").save_as_table(f"{config.DATABASE['name']}.CURATED.DIM_PORTFOLIO")
    

def build_dim_portfolio_manager(session: Session):
    """Build portfolio manager dimension and assignment table from YAML reference data."""
    log_detail("  Building DIM_PORTFOLIO_MANAGER...")
    database_name = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']

    pm_data = config.REF_DATA['portfolio_managers']
    managers = pm_data['managers']
    assignments = pm_data['assignments']

    # Create PM dimension
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{curated}.DIM_PORTFOLIO_MANAGER (
            PM_ID           NUMBER NOT NULL,
            PM_NAME         VARCHAR(200) NOT NULL,
            TITLE           VARCHAR(100),
            TEAM            VARCHAR(100),
            HIRE_DATE       DATE,
            AUM_CAPACITY    NUMBER(18,2),
            EMAIL           VARCHAR(200),
            PRIMARY KEY (PM_ID)
        )
    """).collect()

    esc = lambda s: s.replace("'", "''")
    pm_rows = []
    for m in managers:
        pm_rows.append(
            f"({m['pm_id']}, '{esc(m['name'])}', '{esc(m['title'])}', "
            f"'{esc(m['team'])}', '{m['hire_date']}', {m['aum_capacity']}, '{m['email']}')"
        )

    session.sql(f"""
        INSERT INTO {database_name}.{curated}.DIM_PORTFOLIO_MANAGER
            (PM_ID, PM_NAME, TITLE, TEAM, HIRE_DATE, AUM_CAPACITY, EMAIL)
        VALUES {', '.join(pm_rows)}
    """).collect()

    # Create assignment junction table
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{curated}.FACT_PORTFOLIO_PM_ASSIGNMENT (
            PORTFOLIOID     NUMBER NOT NULL,
            PM_ID           NUMBER NOT NULL,
            ROLE            VARCHAR(50) DEFAULT 'Lead',
            ASSIGNED_DATE   DATE DEFAULT CURRENT_DATE(),
            PRIMARY KEY (PORTFOLIOID, PM_ID)
        )
    """).collect()

    # Insert assignments (resolve portfolio names to IDs)
    assign_rows = []
    for a in assignments:
        assign_rows.append(
            f"('{esc(a['portfolio_name'])}', {a['pm_id']}, '{a['role']}')"
        )

    session.sql(f"""
        INSERT INTO {database_name}.{curated}.FACT_PORTFOLIO_PM_ASSIGNMENT (PORTFOLIOID, PM_ID, ROLE)
        SELECT p.PORTFOLIOID, v.$2, v.$3
        FROM (VALUES {', '.join(assign_rows)}) v
        JOIN {database_name}.{curated}.DIM_PORTFOLIO p ON p.PORTFOLIONAME = v.$1
    """).collect()

    pm_count = session.sql(f"SELECT COUNT(*) AS CNT FROM {database_name}.{curated}.DIM_PORTFOLIO_MANAGER").collect()[0]['CNT']
    assign_count = session.sql(f"SELECT COUNT(*) AS CNT FROM {database_name}.{curated}.FACT_PORTFOLIO_PM_ASSIGNMENT").collect()[0]['CNT']
    log_detail(f"  DIM_PORTFOLIO_MANAGER: {pm_count} PMs, {assign_count} portfolio assignments")


def build_dim_benchmark(session: Session):
    """Build benchmark dimension."""
    log_detail("  Building DIM_BENCHMARK...")
    
    benchmark_data = []
    for i, benchmark in enumerate(config.BENCHMARKS):
        benchmark_data.append({
            'BenchmarkID': i + 1,
            'BenchmarkName': benchmark['name'],
            'Provider': benchmark['provider']
        })
    
    benchmarks_df = session.create_dataframe(benchmark_data)
    benchmarks_df.write.mode("overwrite").save_as_table(f"{config.DATABASE['name']}.CURATED.DIM_BENCHMARK")
    

def build_dim_portfolio_ips(session: Session):
    """Build Investment Policy Statement dimension table with structured constraints.
    
    Maps each portfolio to its IPS risk profile and extracts key constraints:
    - Asset allocation targets and ranges (equity, fixed income, alternatives)
    - Concentration limits (single issuer, sector)
    - Credit quality minimums
    - Prohibited investments
    - ESG requirements (for applicable portfolios)
    - Rebalancing frequency
    
    IPS constraints are used by:
    - FACT_COMPLIANCE_ALERTS for breach detection
    - SAM_IPS_DOCS search service for agent queries
    - Portfolio Copilot for implementation planning
    """
    log_detail("  Building DIM_PORTFOLIO_IPS...")
    database_name = config.DATABASE['name']
    
    ips_config = config.DOCUMENT_TYPES.get('ips', {})
    portfolio_risk_mapping = ips_config.get('portfolio_risk_mapping', {})
    
    ips_constraints = {
        'conservative': {
            'equity_target_pct': 25,
            'equity_min_pct': 15,
            'equity_max_pct': 35,
            'fi_target_pct': 65,
            'fi_min_pct': 55,
            'fi_max_pct': 75,
            'alternatives_target_pct': 5,
            'alternatives_max_pct': 10,
            'cash_min_pct': 2,
            'max_single_issuer_pct': 5,
            'max_sector_pct': 20,
            'min_credit_rating': 'BBB-',
            'prohibited_investments': '["Leveraged ETFs", "Inverse ETFs", "Commodities", "Cryptocurrency", "Private Equity", "Venture Capital", "Below Investment Grade Bonds"]',
            'rebalancing_frequency': 'Quarterly',
            'max_volatility_pct': 9,
            'max_drawdown_pct': 12
        },
        'moderate': {
            'equity_target_pct': 60,
            'equity_min_pct': 50,
            'equity_max_pct': 70,
            'fi_target_pct': 35,
            'fi_min_pct': 25,
            'fi_max_pct': 45,
            'alternatives_target_pct': 5,
            'alternatives_max_pct': 15,
            'cash_min_pct': 2,
            'max_single_issuer_pct': 6,
            'max_sector_pct': 25,
            'min_credit_rating': 'BB',
            'prohibited_investments': '["Leveraged ETFs", "Inverse ETFs", "Cryptocurrency"]',
            'rebalancing_frequency': 'Quarterly',
            'max_volatility_pct': 15,
            'max_drawdown_pct': 20
        },
        'aggressive': {
            'equity_target_pct': 90,
            'equity_min_pct': 80,
            'equity_max_pct': 100,
            'fi_target_pct': 5,
            'fi_min_pct': 0,
            'fi_max_pct': 15,
            'alternatives_target_pct': 5,
            'alternatives_max_pct': 20,
            'cash_min_pct': 0,
            'max_single_issuer_pct': 8,
            'max_sector_pct': 35,
            'min_credit_rating': 'B',
            'prohibited_investments': '["Inverse ETFs"]',
            'rebalancing_frequency': 'Monthly',
            'max_volatility_pct': 25,
            'max_drawdown_pct': 35
        }
    }
    
    ips_data = []
    for portfolio_name, portfolio_config in config.PORTFOLIOS.items():
        risk_profile = portfolio_risk_mapping.get(portfolio_name, 'moderate')
        constraints = ips_constraints[risk_profile]
        
        is_esg_portfolio = 'ESG' in portfolio_name or 'Sustainable' in portfolio_name or 'Climate' in portfolio_name
        esg_requirements = '{"min_esg_rating": "BBB", "exclude_controversies": true, "exclusion_sectors": ["Tobacco", "Weapons", "Thermal Coal"]}' if is_esg_portfolio else None
        
        ips_data.append({
            'PortfolioName': portfolio_name,
            'RiskProfile': risk_profile.capitalize(),
            'EquityTargetPct': constraints['equity_target_pct'],
            'EquityMinPct': constraints['equity_min_pct'],
            'EquityMaxPct': constraints['equity_max_pct'],
            'FixedIncomeTargetPct': constraints['fi_target_pct'],
            'FixedIncomeMinPct': constraints['fi_min_pct'],
            'FixedIncomeMaxPct': constraints['fi_max_pct'],
            'AlternativesTargetPct': constraints['alternatives_target_pct'],
            'AlternativesMaxPct': constraints['alternatives_max_pct'],
            'CashMinPct': constraints['cash_min_pct'],
            'MaxSingleIssuerPct': constraints['max_single_issuer_pct'],
            'MaxSectorPct': constraints['max_sector_pct'],
            'MinCreditRating': constraints['min_credit_rating'],
            'ProhibitedInvestments': constraints['prohibited_investments'],
            'ESGRequirements': esg_requirements,
            'RebalancingFrequency': constraints['rebalancing_frequency'],
            'MaxVolatilityPct': constraints['max_volatility_pct'],
            'MaxDrawdownPct': constraints['max_drawdown_pct'],
            'EffectiveDate': '2024-01-01',
            'ReviewDate': '2025-01-01'
        })
    
    ips_df = session.create_dataframe(ips_data)
    temp_table_name = f"{database_name}.CURATED._TEMP_IPS_DATA"
    ips_df.write.mode("overwrite").save_as_table(temp_table_name)
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.DIM_PORTFOLIO_IPS (
            IPSID INT IDENTITY(1,1),
            PortfolioID INT,
            PortfolioName VARCHAR(100),
            RiskProfile VARCHAR(20),
            EquityTargetPct DECIMAL(5,2),
            EquityMinPct DECIMAL(5,2),
            EquityMaxPct DECIMAL(5,2),
            FixedIncomeTargetPct DECIMAL(5,2),
            FixedIncomeMinPct DECIMAL(5,2),
            FixedIncomeMaxPct DECIMAL(5,2),
            AlternativesTargetPct DECIMAL(5,2),
            AlternativesMaxPct DECIMAL(5,2),
            CashMinPct DECIMAL(5,2),
            MaxSingleIssuerPct DECIMAL(5,2),
            MaxSectorPct DECIMAL(5,2),
            MinCreditRating VARCHAR(10),
            ProhibitedInvestments VARIANT,
            ESGRequirements VARIANT,
            RebalancingFrequency VARCHAR(20),
            MaxVolatilityPct DECIMAL(5,2),
            MaxDrawdownPct DECIMAL(5,2),
            EffectiveDate DATE,
            ReviewDate DATE
        )
    """).collect()
    
    session.sql(f"""
        INSERT INTO {database_name}.CURATED.DIM_PORTFOLIO_IPS (
            PortfolioID, PortfolioName, RiskProfile,
            EquityTargetPct, EquityMinPct, EquityMaxPct,
            FixedIncomeTargetPct, FixedIncomeMinPct, FixedIncomeMaxPct,
            AlternativesTargetPct, AlternativesMaxPct, CashMinPct,
            MaxSingleIssuerPct, MaxSectorPct, MinCreditRating,
            ProhibitedInvestments, ESGRequirements, RebalancingFrequency,
            MaxVolatilityPct, MaxDrawdownPct, EffectiveDate, ReviewDate
        )
        SELECT 
            p.PortfolioID,
            ips.PORTFOLIONAME,
            ips.RISKPROFILE,
            ips.EQUITYTARGETPCT,
            ips.EQUITYMINPCT,
            ips.EQUITYMAXPCT,
            ips.FIXEDINCOMETARGETPCT,
            ips.FIXEDINCOMEMINPCT,
            ips.FIXEDINCOMEMAXPCT,
            ips.ALTERNATIVESTARGETPCT,
            ips.ALTERNATIVESMAXPCT,
            ips.CASHMINPCT,
            ips.MAXSINGLEISSUERPCT,
            ips.MAXSECTORPCT,
            ips.MINCREDITRATING,
            TRY_PARSE_JSON(ips.PROHIBITEDINVESTMENTS),
            TRY_PARSE_JSON(ips.ESGREQUIREMENTS),
            ips.REBALANCINGFREQUENCY,
            ips.MAXVOLATILITYPCT,
            ips.MAXDRAWDOWNPCT,
            ips.EFFECTIVEDATE::DATE,
            ips.REVIEWDATE::DATE
        FROM {temp_table_name} ips
        JOIN {database_name}.CURATED.DIM_PORTFOLIO p ON p.PortfolioName = ips.PORTFOLIONAME
    """).collect()
    
    session.sql(f"DROP TABLE IF EXISTS {temp_table_name}").collect()


def build_dim_supply_chain_relationships(session: Session, test_mode: bool = False):
    """
    Build supply chain relationships dimension table.
    Models issuer-level supply chain dependencies for second-order risk analysis.
    
    Scenario-first generation:
    - Core demo relationships: Taiwan semiconductor → US tech → automotive
    - Industry-specific relationship densities
    - Symmetric relationship handling (supplier/customer pairs)
    """
    
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    
    # Step 1: Create the table structure (without foreign key constraints for simplicity)
    # Foreign key constraints removed to avoid data type mismatches with ROW_NUMBER-generated IssuerIDs
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.DIM_SUPPLY_CHAIN_RELATIONSHIPS (
            RelationshipID BIGINT IDENTITY(1,1) PRIMARY KEY,
            Company_IssuerID NUMBER NOT NULL,
            Counterparty_IssuerID NUMBER NOT NULL,
            RelationshipType VARCHAR(50),
            CostShare DECIMAL(7,4),
            RevenueShare DECIMAL(7,4),
            CriticalityTier VARCHAR(20),
            SourceConfidence DECIMAL(5,2),
            StartDate DATE,
            EndDate DATE,
            Notes VARCHAR(500)
        )
    """).collect()
    
    # Step 2: Get issuer IDs for supply chain companies - derive tickers from config
    # Batched lookup - single query instead of loop (Snowflake I/O best practice)
    supply_chain_tickers = set()
    for rel in config.SUPPLY_CHAIN_DEMO_RELATIONSHIPS:
        supply_chain_tickers.add(rel[0])  # company_ticker
        supply_chain_tickers.add(rel[1])  # counterparty_ticker
    
    tickers_sql = ', '.join(f"'{t}'" for t in supply_chain_tickers)
    issuer_map_rows = session.sql(f"""
        SELECT i.PrimaryTicker, i.IssuerID
        FROM {database_name}.CURATED.DIM_ISSUER i
        WHERE i.PrimaryTicker IN ({tickers_sql})
    """).collect()
    issuer_map = {row['PRIMARYTICKER']: row['ISSUERID'] for row in issuer_map_rows}
    
    # Log any missing tickers
    missing_tickers = supply_chain_tickers - set(issuer_map.keys())
    for ticker in missing_tickers:
        log_warning(f"  Could not find issuer for supply chain ticker: {ticker}")
    
    # Step 3: Create demo relationships from config
    relationships = []
    relationship_id = 1
    
    for company_ticker, counterparty_ticker, rel_type, share, criticality in config.SUPPLY_CHAIN_DEMO_RELATIONSHIPS:
        if company_ticker in issuer_map and counterparty_ticker in issuer_map:
            # Create supplier relationship
            if rel_type == 'Customer':
                # Company is supplier, counterparty is customer
                relationships.append({
                    'RelationshipID': relationship_id,
                    'Company_IssuerID': issuer_map[company_ticker],
                    'Counterparty_IssuerID': issuer_map[counterparty_ticker],
                    'RelationshipType': 'Supplier',  # Company supplies to counterparty
                    'CostShare': None,
                    'RevenueShare': share,  # Share of company's revenue from this customer
                    'CriticalityTier': criticality,
                    'SourceConfidence': 85.0,
                    'StartDate': date(2020, 1, 1),
                    'EndDate': None,
                    'Notes': f'Demo relationship: {company_ticker} supplies to {counterparty_ticker}'
                })
                relationship_id += 1
                
                # Create symmetric customer relationship
                relationships.append({
                    'RelationshipID': relationship_id,
                    'Company_IssuerID': issuer_map[counterparty_ticker],
                    'Counterparty_IssuerID': issuer_map[company_ticker],
                    'RelationshipType': 'Customer',  # Counterparty is customer of company
                    'CostShare': share,  # Share of counterparty's costs from this supplier
                    'RevenueShare': None,
                    'CriticalityTier': criticality,
                    'SourceConfidence': 85.0,
                    'StartDate': date(2020, 1, 1),
                    'EndDate': None,
                    'Notes': f'Demo relationship: {counterparty_ticker} sources from {company_ticker}'
                })
                relationship_id += 1
    
    # Step 4: Add industry-based relationships for realism
    # Get additional issuers by sector
    sectors_with_density = {
        'Information Technology': config.SUPPLY_CHAIN_RELATIONSHIP_STRENGTHS['semiconductors'],
        'Consumer Discretionary': config.SUPPLY_CHAIN_RELATIONSHIP_STRENGTHS['automotive'],
        'Industrials': config.SUPPLY_CHAIN_RELATIONSHIP_STRENGTHS['default']
    }
    
    for sector, density in sectors_with_density.items():
        # Get random issuers from this sector (excluding demo companies)
        sector_issuers = session.sql(f"""
            SELECT DISTINCT i.IssuerID, i.LegalName
            FROM {database_name}.CURATED.DIM_ISSUER i
            WHERE i.SIC_DESCRIPTION = '{sector}'
            AND i.IssuerID NOT IN ({','.join(str(id) for id in issuer_map.values())})
            ORDER BY RANDOM()
            LIMIT {5 if test_mode else 15}
        """).collect()
        
        # Create relationships between sector companies
        for i in range(len(sector_issuers) - 1):
            if random.random() < 0.3:  # 30% chance of relationship
                min_share, max_share = density['critical_suppliers_share']
                share = round(random.uniform(min_share, max_share), 4)
                criticality = 'High' if share > 0.15 else 'Medium' if share > 0.08 else 'Low'
                
                relationships.append({
                    'RelationshipID': relationship_id,
                    'Company_IssuerID': sector_issuers[i]['ISSUERID'],
                    'Counterparty_IssuerID': sector_issuers[i+1]['ISSUERID'],
                    'RelationshipType': 'Supplier',
                    'CostShare': None,
                    'RevenueShare': share,
                    'CriticalityTier': criticality,
                    'SourceConfidence': round(random.uniform(70, 90), 2),
                    'StartDate': date(2020, 1, 1),
                    'EndDate': None,
                    'Notes': f'Industry relationship within {sector}'
                })
                relationship_id += 1
    
    # Step 5: Insert relationships
    if relationships:
        relationships_df = session.create_dataframe(relationships)
        relationships_df.write.mode("overwrite").save_as_table(
            f"{database_name}.CURATED.DIM_SUPPLY_CHAIN_RELATIONSHIPS"
        )
    else:
        log_warning("  No supply chain relationships created")

def build_fact_transaction(session: Session, test_mode: bool = False):
    """Generate synthetic transaction history."""
    
    # Verify DIM_SECURITY table exists and has Ticker column
    try:
        columns = session.sql(f"DESCRIBE TABLE {config.DATABASE['name']}.CURATED.DIM_SECURITY").collect()
        column_names = [col['name'] for col in columns]
        if 'TICKER' not in column_names:
            raise Exception(f"DIM_SECURITY table missing TICKER column. Available columns: {column_names}")
    except Exception as e:
        log_error(f" Table structure verification failed: {e}")
        raise
    
    # Get max price date as upper bound for transactions (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_TRANSACTION. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Get SQL mapping for demo portfolios (eliminates hardcoded company references)
    demo_sql_mapping = build_demo_portfolios_sql_mapping()
    
    # This is a simplified version - in a real implementation, we'd generate
    # realistic transaction patterns that result in the desired end positions
    session.sql(f"""
        -- Generate synthetic transaction history that builds to realistic portfolio positions
        -- This creates a complete audit trail of BUY transactions over the past 12 months
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_TRANSACTION AS
        WITH all_securities AS (
            -- All securities with priority rankings from DIM_ISSUER tier
            -- With DEMO_COMPANIES approach, each issuer has exactly one security (1:1 mapping)
            SELECT 
                s.SecurityID,
                s.IssuerID,
                s.Ticker,
                CASE i.Tier
                    WHEN 'core' THEN 1
                    WHEN 'major' THEN 2
                    WHEN 'additional' THEN 3
                    ELSE 4
                END as priority
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
        ),
        portfolio_securities AS (
            -- Step 2: Assign securities to portfolios with demo-specific logic from config.PORTFOLIOS
            SELECT 
                p.PortfolioID,
                p.PortfolioName,
                s.SecurityID,
                s.Ticker,
                s.priority,
                -- Special prioritization for demo portfolios (fully driven by config.PORTFOLIOS)
                CASE 
                    WHEN p.PortfolioName IN {safe_sql_tuple(get_demo_portfolio_names())} THEN
                        CASE 
                            -- Priority holdings from DEMO_COMPANIES demo_order
                            {demo_sql_mapping['priority_case_when_sql']}
                            -- Filler stocks (from DEMO_COMPANIES tier=major)
                            WHEN s.Ticker IN {safe_sql_tuple(get_demo_company_tickers(tier='major'))} THEN {demo_sql_mapping['additional_priority']}
                            ELSE 999  -- Exclude non-demo companies from demo portfolios
                        END
                    ELSE s.priority  -- Use normal priority for non-demo portfolios
                END as portfolio_priority,
                -- Random ordering within priority groups for portfolio diversification
                ROW_NUMBER() OVER (PARTITION BY p.PortfolioID ORDER BY 
                    CASE 
                        WHEN p.PortfolioName IN {safe_sql_tuple(get_demo_portfolio_names())} THEN
                            CASE 
                                -- Priority ordering from DEMO_COMPANIES demo_order
                                {demo_sql_mapping['priority_case_when_sql']}
                                -- Filler stocks
                                WHEN s.Ticker IN {safe_sql_tuple(get_demo_company_tickers(tier='major'))} THEN {demo_sql_mapping['additional_priority']}
                                ELSE 999
                            END
                        ELSE s.priority
                    END, 
                    RANDOM()
                ) as rn
            FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO p
            CROSS JOIN all_securities s
        ),
        selected_holdings AS (
            -- Step 3: Limit each portfolio to ~45 securities with theme-specific filtering
            SELECT PortfolioID, SecurityID
            FROM portfolio_securities
            WHERE rn <= 45  -- Typical large-cap equity portfolio size
            AND (
                -- For demo portfolios, only include securities with valid priorities (from config.PORTFOLIOS)
                (PortfolioName IN {safe_sql_tuple(get_demo_portfolio_names())} AND portfolio_priority < 999)
                OR 
                -- For non-demo portfolios, use normal selection
                (PortfolioName NOT IN {safe_sql_tuple(get_demo_portfolio_names())})
            )
        ),
        business_days AS (
            -- Step 4a: Generate all business days for transaction history
            -- Creates complete set of Monday-Friday trading days up to max_price_date
            SELECT generated_date as trade_date
            FROM (
                SELECT DATEADD(day, seq4(), DATEADD(month, -{config.DATA_MODEL['transaction_months']}, '{max_price_date}'::DATE)) as generated_date
                FROM TABLE(GENERATOR(rowcount => {365 * config.DATA_MODEL['transaction_months'] // 12}))
            )
            WHERE DAYOFWEEK(generated_date) BETWEEN 1 AND 5
              AND generated_date <= '{max_price_date}'::DATE
        ),
        trading_intensity AS (
            -- Step 4b: Assign realistic trading intensity to each business day
            -- Creates varied activity: some busy days (multiple portfolios), some quiet days (few/none)
            SELECT 
                trade_date,
                CASE 
                    -- Use hash-based approach for deterministic but varied trading patterns
                    -- 15% of days are busy (market events, rebalancing dates)
                    WHEN (HASH(trade_date) % 100) < 15 THEN 0.6
                    -- 25% of days are moderate (regular portfolio activity)  
                    WHEN (HASH(trade_date) % 100) < 40 THEN 0.3
                    -- 35% of days are quiet (minimal trading)
                    WHEN (HASH(trade_date) % 100) < 75 THEN 0.1
                    -- 25% of days are very quiet (no trading)
                    ELSE 0.0
                END as portfolio_trade_probability
            FROM business_days
        ),
        portfolio_trading_days AS (
            -- Step 4c: Determine which portfolios trade on which days
            -- Applies portfolio-specific probability with different trading patterns per portfolio
            SELECT 
                p.PortfolioID,
                ti.trade_date
            FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO p
            CROSS JOIN trading_intensity ti
            WHERE ti.portfolio_trade_probability > 0
            AND (HASH(p.PortfolioID, ti.trade_date) % 100) < (ti.portfolio_trade_probability * 100)
        )
        -- Step 5: Generate final transaction records with realistic attributes
        -- Creates BUY transactions that build up portfolio positions over time
        SELECT 
            -- Unique transaction identifier (sequential numbering)
            ROW_NUMBER() OVER (ORDER BY sh.PortfolioID, sh.SecurityID, ptd.trade_date) as TransactionID,
            -- Transaction and trade dates (same for simplicity)
            ptd.trade_date as TransactionDate,
            ptd.trade_date as TradeDate,
            -- Portfolio and security references
            sh.PortfolioID,
            sh.SecurityID,
            -- Transaction attributes
            'BUY' as TransactionType,  -- Simplified: mostly buys to build positions over time
            DATEADD(day, 2, ptd.trade_date) as SettleDate,  -- Standard T+2 settlement cycle
            -- Strategic position sizing: larger positions for demo portfolio top holdings (from DEMO_COMPANIES)
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s 
                    JOIN {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO p ON sh.PortfolioID = p.PortfolioID
                    WHERE s.SecurityID = sh.SecurityID 
                    AND p.PortfolioName IN {safe_sql_tuple(get_demo_portfolio_names())}  -- Any demo portfolio from config
                    AND s.Ticker IN {demo_sql_mapping['large_position_tickers']}  -- Holdings with position_size='large' in DEMO_COMPANIES
                ) THEN UNIFORM(50000, 100000, RANDOM())  -- Large positions as specified in config
                ELSE UNIFORM(100, 10000, RANDOM())  -- Normal positions for others
            END as Quantity,
            -- Realistic stock prices ($50-$500 range)
            UNIFORM(50, 500, RANDOM()) as Price,
            -- Gross amount calculated as Quantity * Price
            Quantity * Price as GrossAmount_Local,
            -- Realistic commission costs ($5-$50)
            UNIFORM(5, 50, RANDOM()) as Commission_Local,
            -- Standard currency and system identifiers
            'USD' as Currency,
            'ABOR' as SourceSystem,  -- Accounting Book of Record
            -- Source system transaction reference
            CONCAT('TXN_', ROW_NUMBER() OVER (ORDER BY sh.PortfolioID, sh.SecurityID, ptd.trade_date)) as SourceTransactionID
        FROM selected_holdings sh
        JOIN portfolio_trading_days ptd ON sh.PortfolioID = ptd.PortfolioID
        WHERE (HASH(sh.SecurityID, ptd.trade_date) % 100) < 20  -- 20% of portfolio-security-day combinations create transactions
    """).collect()
    

def build_fact_position_daily_abor(session: Session):
    """Build ABOR positions from transaction log."""
    
    # Get max price date as upper bound for positions (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_POSITION_DAILY_ABOR. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR AS
        WITH monthly_dates AS (
            SELECT LAST_DAY(DATEADD(month, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, '{max_price_date}'::DATE))) as position_date
            FROM TABLE(GENERATOR(rowcount => {12 * config.YEARS_OF_HISTORY}))
            WHERE position_date <= '{max_price_date}'::DATE
        ),
        transaction_balances AS (
            SELECT 
                PortfolioID,
                SecurityID,
                SUM(CASE WHEN TransactionType = 'BUY' THEN Quantity ELSE -Quantity END) as TotalQuantity,
                AVG(Price) as AvgPrice
            FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION
            GROUP BY PortfolioID, SecurityID
            HAVING TotalQuantity > 0
        ),
        nearest_price AS (
            SELECT
                md.position_date,
                tb.PortfolioID,
                tb.SecurityID,
                tb.TotalQuantity,
                tb.AvgPrice,
                sp.PRICE_CLOSE,
                ROW_NUMBER() OVER (
                    PARTITION BY md.position_date, tb.PortfolioID, tb.SecurityID
                    ORDER BY sp.PRICE_DATE DESC
                ) AS rn
            FROM monthly_dates md
            CROSS JOIN transaction_balances tb
            JOIN {config.DATABASE['name']}.MARKET_DATA.FACT_STOCK_PRICES sp
                ON tb.SecurityID = sp.SECURITYID
                AND sp.PRICE_DATE <= md.position_date
                AND sp.PRICE_DATE >= DATEADD('day', -5, md.position_date)
        ),
        position_snapshots AS (
            SELECT 
                np.position_date as HoldingDate,
                np.PortfolioID,
                np.SecurityID,
                np.TotalQuantity as Quantity,
                np.TotalQuantity * np.PRICE_CLOSE as MarketValue_Local,
                np.TotalQuantity * np.PRICE_CLOSE as MarketValue_Base,
                np.TotalQuantity * np.AvgPrice as CostBasis_Local,
                np.TotalQuantity * np.AvgPrice as CostBasis_Base,
                0 as AccruedInterest_Local
            FROM nearest_price np
            WHERE np.rn = 1
        ),
        portfolio_totals AS (
            SELECT 
                HoldingDate,
                PortfolioID,
                SUM(MarketValue_Base) as PortfolioTotal
            FROM position_snapshots
            GROUP BY HoldingDate, PortfolioID
        )
        SELECT 
            ps.*,
            ps.MarketValue_Base / pt.PortfolioTotal as PortfolioWeight
        FROM position_snapshots ps
        JOIN portfolio_totals pt ON ps.HoldingDate = pt.HoldingDate AND ps.PortfolioID = pt.PortfolioID
    """).collect()


def build_esg_scores(session: Session):
    """Build ESG scores with SecurityID linkage using config-driven SQL generation.
    
    Uses config-driven SQL builders for:
    - Sector-based Environmental scores (DATA_MODEL['synthetic_distributions']['by_sector'])
    - Country-based Social/Governance scores (DATA_MODEL['synthetic_distributions']['country_groups'])
    - Grade thresholds (COMPLIANCE_RULES['esg']['grade_thresholds'])
    - Overall ESG weights (COMPLIANCE_RULES['esg']['overall_weights'])
    """
    
    database_name = config.DATABASE['name']
    
    # Get max price date as upper bound (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_ESG_SCORES. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Build config-driven SQL expressions
    e_score_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'esg.E')
    s_score_sql = build_country_group_case_sql('es.CountryOfIncorporation', 'esg.S')
    g_score_sql = build_country_group_case_sql('es.CountryOfIncorporation', 'esg.G')
    e_grade_sql = build_grade_case_sql('E_SCORE')
    s_grade_sql = build_grade_case_sql('S_SCORE')
    g_grade_sql = build_grade_case_sql('G_SCORE')
    overall_score_sql = build_overall_esg_sql('E_SCORE', 'S_SCORE', 'G_SCORE')
    overall_grade_sql = build_grade_case_sql(overall_score_sql)
    esg_provider = config.COMPLIANCE_RULES['esg']['default_provider']
    
    session.sql(f"""
        -- Generate synthetic ESG scores with sector-specific characteristics and regional variations
        -- Creates Environmental, Social, Governance scores (0-100) with realistic distributions
        -- Config-driven via DATA_MODEL['synthetic_distributions'] and COMPLIANCE_RULES['esg']
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_ESG_SCORES AS
        WITH equity_securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.SIC_DESCRIPTION,
                i.CountryOfIncorporation
            FROM {database_name}.CURATED.DIM_SECURITY s
            JOIN {database_name}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {database_name}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        scoring_dates AS (
            SELECT DATEADD(quarter, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, '{max_price_date}'::DATE)) as SCORE_DATE
            FROM TABLE(GENERATOR(rowcount => {4 * config.YEARS_OF_HISTORY}))
            WHERE SCORE_DATE <= '{max_price_date}'::DATE
        ),
        base_scores AS (
            SELECT 
                es.SecurityID,
                sd.SCORE_DATE,
                -- Environmental score (sector-specific from config)
                {e_score_sql} as E_SCORE,
                -- Social score (country-group-specific from config)
                {s_score_sql} as S_SCORE,
                -- Governance score (country-group-specific from config)
                {g_score_sql} as G_SCORE
            FROM equity_securities es
            CROSS JOIN scoring_dates sd
        )
        SELECT 
            SecurityID,
            SCORE_DATE,
            'Environmental' as SCORE_TYPE,
            E_SCORE as SCORE_VALUE,
            {e_grade_sql} as SCORE_GRADE,
            '{esg_provider}' as PROVIDER
        FROM base_scores
        UNION ALL
        SELECT SecurityID, SCORE_DATE, 'Social', S_SCORE, 
               {s_grade_sql},
               '{esg_provider}' FROM base_scores
        UNION ALL  
        SELECT SecurityID, SCORE_DATE, 'Governance', G_SCORE,
               {g_grade_sql},
               '{esg_provider}' FROM base_scores
        UNION ALL
        SELECT SecurityID, SCORE_DATE, 'Overall ESG', {overall_score_sql},
               {overall_grade_sql},
               '{esg_provider}' FROM base_scores
    """).collect()
    
    # Apply ESG demo overrides for specific securities (for demo scenarios)
    # This ensures some holdings fall below BBB threshold for breach detection demos
    # Set-based UPDATE - single query instead of loop (Snowflake I/O best practice)
    if config.ESG_DEMO_OVERRIDES:
        override_cases = []
        override_tickers = list(config.ESG_DEMO_OVERRIDES.keys())
        for ticker, override in config.ESG_DEMO_OVERRIDES.items():
            esg_score = override['esg_score']
            esg_grade = override['esg_grade']
            override_cases.append(f"WHEN s.Ticker = '{ticker}' THEN {esg_score}")
        
        score_case_sql = f"CASE {' '.join(override_cases)} END"
        grade_cases = [f"WHEN s.Ticker = '{ticker}' THEN '{override['esg_grade']}'" 
                       for ticker, override in config.ESG_DEMO_OVERRIDES.items()]
        grade_case_sql = f"CASE {' '.join(grade_cases)} END"
        tickers_sql = ', '.join(f"'{t}'" for t in override_tickers)
        
        session.sql(f"""
            UPDATE {database_name}.CURATED.FACT_ESG_SCORES f
            SET SCORE_VALUE = {score_case_sql},
                SCORE_GRADE = {grade_case_sql}
            FROM {database_name}.CURATED.DIM_SECURITY s
            WHERE f.SecurityID = s.SecurityID
              AND s.Ticker IN ({tickers_sql})
              AND f.SCORE_TYPE = 'Overall ESG'
        """).collect()


def build_security_returns_view(session: Session):
    """Create security returns view with calculated performance metrics.
    
    This view calculates returns from MARKET_DATA.FACT_STOCK_PRICES:
    - Daily returns (price change)
    - MTD returns (month-to-date)
    - QTD returns (quarter-to-date)
    - YTD returns (year-to-date)
    
    Used by: SAM_ANALYST_VIEW via V_HOLDINGS_WITH_ESG for portfolio performance queries
    """
    database_name = config.DATABASE['name']
    
    # Check if FACT_STOCK_PRICES exists
    try:
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.MARKET_DATA.FACT_STOCK_PRICES").collect()[0]['CNT']
        if count == 0:
            raise RuntimeError(
                "FACT_STOCK_PRICES is empty - cannot build V_SECURITY_RETURNS. "
                "Run generate_market_data.build_price_anchor() first."
            )
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(
            f"FACT_STOCK_PRICES not found - cannot build V_SECURITY_RETURNS: {e}. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Create V_SECURITY_RETURNS with calculated returns per security per date
    session.sql(f"""
        CREATE OR REPLACE VIEW {database_name}.CURATED.V_SECURITY_RETURNS AS
        WITH price_data AS (
            SELECT 
                SECURITYID,
                PRICE_DATE,
                PRICE_CLOSE,
                LAG(PRICE_CLOSE) OVER (PARTITION BY SECURITYID ORDER BY PRICE_DATE) as PREV_CLOSE,
                FIRST_VALUE(PRICE_CLOSE) OVER (
                    PARTITION BY SECURITYID, DATE_TRUNC('MONTH', PRICE_DATE) 
                    ORDER BY PRICE_DATE
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) as MONTH_START_PRICE,
                FIRST_VALUE(PRICE_CLOSE) OVER (
                    PARTITION BY SECURITYID, DATE_TRUNC('QUARTER', PRICE_DATE) 
                    ORDER BY PRICE_DATE
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) as QUARTER_START_PRICE,
                FIRST_VALUE(PRICE_CLOSE) OVER (
                    PARTITION BY SECURITYID, DATE_TRUNC('YEAR', PRICE_DATE) 
                    ORDER BY PRICE_DATE
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) as YEAR_START_PRICE
            FROM {database_name}.MARKET_DATA.FACT_STOCK_PRICES
            WHERE PRICE_CLOSE > 0
        )
        SELECT 
            SECURITYID,
            PRICE_DATE,
            PRICE_CLOSE,
            -- Daily return
            ROUND((PRICE_CLOSE - PREV_CLOSE) / NULLIF(PREV_CLOSE, 0) * 100, 2) as DAILY_RETURN_PCT,
            -- MTD return
            ROUND((PRICE_CLOSE - MONTH_START_PRICE) / NULLIF(MONTH_START_PRICE, 0) * 100, 2) as MTD_RETURN_PCT,
            -- QTD return
            ROUND((PRICE_CLOSE - QUARTER_START_PRICE) / NULLIF(QUARTER_START_PRICE, 0) * 100, 2) as QTD_RETURN_PCT,
            -- YTD return
            ROUND((PRICE_CLOSE - YEAR_START_PRICE) / NULLIF(YEAR_START_PRICE, 0) * 100, 2) as YTD_RETURN_PCT
        FROM price_data
    """).collect()
    
    # Create V_SECURITY_RETURNS_LATEST with only the latest returns per security
    session.sql(f"""
        CREATE OR REPLACE VIEW {database_name}.CURATED.V_SECURITY_RETURNS_LATEST AS
        SELECT 
            SECURITYID,
            PRICE_DATE as RETURNS_DATE,
            PRICE_CLOSE as LATEST_PRICE,
            DAILY_RETURN_PCT,
            MTD_RETURN_PCT,
            QTD_RETURN_PCT,
            YTD_RETURN_PCT
        FROM {database_name}.CURATED.V_SECURITY_RETURNS
        QUALIFY ROW_NUMBER() OVER (PARTITION BY SECURITYID ORDER BY PRICE_DATE DESC) = 1
    """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.V_SECURITY_RETURNS_LATEST").collect()[0]['CNT']
    log_detail(f"  Created V_SECURITY_RETURNS_LATEST view with {count:,} securities")


def build_portfolio_modelling_views(session: Session):
    """Create portfolio modelling views for backtesting and risk analysis.
    
    Creates:
    - V_SECURITY_LOG_RETURNS: Log returns for multi-period aggregation (additive)
    - V_PORTFOLIO_RISK_METRICS: Aggregated risk metrics per portfolio
    
    Depends on: V_SECURITY_RETURNS, FACT_POSITION_DAILY_ABOR
    """
    database_name = config.DATABASE['name']
    
    # Check if V_SECURITY_RETURNS exists
    try:
        session.sql(f"SELECT 1 FROM {database_name}.CURATED.V_SECURITY_RETURNS LIMIT 1").collect()
    except Exception as e:
        log_warning(f"V_SECURITY_RETURNS not found - skipping portfolio modelling views: {e}")
        return
    
    # V_SECURITY_LOG_RETURNS: Log returns are additive across time periods
    # This is essential for multi-period return aggregation in backtesting
    session.sql(f"""
        CREATE OR REPLACE VIEW {database_name}.CURATED.V_SECURITY_LOG_RETURNS AS
        SELECT 
            SECURITYID,
            PRICE_DATE,
            PRICE_CLOSE,
            DAILY_RETURN_PCT,
            -- Log return = ln(1 + r) where r is decimal return
            CASE 
                WHEN DAILY_RETURN_PCT IS NULL THEN NULL
                WHEN DAILY_RETURN_PCT <= -100 THEN NULL  -- Avoid log of non-positive
                ELSE LN(1 + DAILY_RETURN_PCT / 100.0)
            END as LOG_RETURN_DAILY,
            -- Cumulative log return over trailing windows
            SUM(CASE 
                WHEN DAILY_RETURN_PCT IS NULL THEN 0
                WHEN DAILY_RETURN_PCT <= -100 THEN 0
                ELSE LN(1 + DAILY_RETURN_PCT / 100.0)
            END) OVER (
                PARTITION BY SECURITYID 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
            ) as LOG_RETURN_21D,
            SUM(CASE 
                WHEN DAILY_RETURN_PCT IS NULL THEN 0
                WHEN DAILY_RETURN_PCT <= -100 THEN 0
                ELSE LN(1 + DAILY_RETURN_PCT / 100.0)
            END) OVER (
                PARTITION BY SECURITYID 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN 62 PRECEDING AND CURRENT ROW
            ) as LOG_RETURN_63D,
            SUM(CASE 
                WHEN DAILY_RETURN_PCT IS NULL THEN 0
                WHEN DAILY_RETURN_PCT <= -100 THEN 0
                ELSE LN(1 + DAILY_RETURN_PCT / 100.0)
            END) OVER (
                PARTITION BY SECURITYID 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
            ) as LOG_RETURN_252D
        FROM {database_name}.CURATED.V_SECURITY_RETURNS
    """).collect()
    
    log_detail("Created V_SECURITY_LOG_RETURNS view")
    
    # V_PORTFOLIO_RISK_METRICS: Aggregated risk metrics per portfolio per date
    # Uses position weights and security returns to calculate portfolio-level metrics
    # Note: Uses multiple CTEs to avoid nested window functions (not supported in Snowflake)
    session.sql(f"""
        CREATE OR REPLACE VIEW {database_name}.CURATED.V_PORTFOLIO_RISK_METRICS AS
        WITH portfolio_returns AS (
            SELECT 
                h.PortfolioID,
                h.HoldingDate,
                -- Weight-average daily returns
                SUM(h.PortfolioWeight * COALESCE(r.DAILY_RETURN_PCT, 0)) as PortfolioReturn_Daily,
                -- Weight-average MTD returns
                SUM(h.PortfolioWeight * COALESCE(r.MTD_RETURN_PCT, 0)) as PortfolioReturn_MTD,
                -- Weight-average YTD returns  
                SUM(h.PortfolioWeight * COALESCE(r.YTD_RETURN_PCT, 0)) as PortfolioReturn_YTD,
                -- Position count
                COUNT(DISTINCT h.SecurityID) as PositionCount,
                -- Total market value
                SUM(h.MarketValue_Base) as TotalMarketValue
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR h
            LEFT JOIN {database_name}.CURATED.V_SECURITY_RETURNS r 
                ON h.SecurityID = r.SECURITYID 
                AND r.PRICE_DATE = h.HoldingDate
            GROUP BY h.PortfolioID, h.HoldingDate
        ),
        -- First pass: calculate cumulative return and rolling volatility
        cumulative_calc AS (
            SELECT 
                PortfolioID,
                HoldingDate,
                PortfolioReturn_Daily,
                PortfolioReturn_MTD,
                PortfolioReturn_YTD,
                PositionCount,
                TotalMarketValue,
                -- Rolling volatility (annualized, 21-day window)
                STDDEV(PortfolioReturn_Daily) OVER (
                    PARTITION BY PortfolioID 
                    ORDER BY HoldingDate 
                    ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
                ) * SQRT(252) as Volatility_21D_Ann,
                -- Rolling volatility (annualized, 63-day window)
                STDDEV(PortfolioReturn_Daily) OVER (
                    PARTITION BY PortfolioID 
                    ORDER BY HoldingDate 
                    ROWS BETWEEN 62 PRECEDING AND CURRENT ROW
                ) * SQRT(252) as Volatility_63D_Ann,
                -- Cumulative return (running sum of daily returns)
                SUM(PortfolioReturn_Daily) OVER (
                    PARTITION BY PortfolioID 
                    ORDER BY HoldingDate 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) as CumulativeReturn
            FROM portfolio_returns
        ),
        -- Second pass: calculate max cumulative return for drawdown (avoids nested window function)
        rolling_stats AS (
            SELECT 
                PortfolioID,
                HoldingDate,
                PortfolioReturn_Daily,
                PortfolioReturn_MTD,
                PortfolioReturn_YTD,
                PositionCount,
                TotalMarketValue,
                Volatility_21D_Ann,
                Volatility_63D_Ann,
                CumulativeReturn,
                -- Max cumulative return up to this point (for drawdown calculation)
                MAX(CumulativeReturn) OVER (
                    PARTITION BY PortfolioID 
                    ORDER BY HoldingDate 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) as MaxCumulativeReturn
            FROM cumulative_calc
        )
        SELECT 
            PortfolioID,
            HoldingDate,
            PortfolioReturn_Daily,
            PortfolioReturn_MTD,
            PortfolioReturn_YTD,
            PositionCount,
            TotalMarketValue,
            Volatility_21D_Ann,
            Volatility_63D_Ann,
            CumulativeReturn,
            -- Current drawdown from peak
            CumulativeReturn - MaxCumulativeReturn as CurrentDrawdown,
            -- Approximate Sharpe (assuming 4% risk-free rate, annualized)
            CASE 
                WHEN Volatility_21D_Ann > 0 
                THEN (PortfolioReturn_Daily * 252 - 4.0) / Volatility_21D_Ann
                ELSE NULL
            END as Sharpe_21D_Approx
        FROM rolling_stats
    """).collect()
    
    log_detail("Created V_PORTFOLIO_RISK_METRICS view")


def build_v_esg_latest(session: Session):
    """Create standalone V_ESG_LATEST view with one row per security.
    
    This view provides the latest Overall ESG score for each security. 
    No dependencies on V_SECURITY_RETURNS - can be built early in the pipeline.
    
    Dependencies: FACT_ESG_SCORES
    """
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE VIEW {database_name}.CURATED.V_ESG_LATEST AS
        SELECT 
            SecurityID,
            SCORE_VALUE as ESG_SCORE,
            SCORE_GRADE as ESG_GRADE,
            SCORE_DATE as ESG_SCORE_DATE,
            PROVIDER as ESG_PROVIDER
        FROM {database_name}.CURATED.FACT_ESG_SCORES
        WHERE SCORE_TYPE = 'Overall ESG'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY SecurityID ORDER BY SCORE_DATE DESC) = 1
    """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.V_ESG_LATEST").collect()[0]['CNT']
    log_detail(f"  Created V_ESG_LATEST view with {count:,} securities")


def build_v_holdings_with_esg(session: Session):
    """Create enriched holdings view with ESG data and returns.
    
    This view combines holdings, ESG scores, and security returns for comprehensive
    portfolio analysis. Must be called AFTER V_SECURITY_RETURNS exists.
    
    Dependencies: FACT_POSITION_DAILY_ABOR, V_ESG_LATEST, V_SECURITY_RETURNS
    """
    database_name = config.DATABASE['name']
    
    # Verify V_SECURITY_RETURNS exists (required dependency)
    try:
        session.sql(f"SELECT 1 FROM {database_name}.CURATED.V_SECURITY_RETURNS LIMIT 1").collect()
    except Exception as e:
        raise RuntimeError(
            f"V_SECURITY_RETURNS not found - cannot build V_HOLDINGS_WITH_ESG: {e}. "
            "Run build_security_returns_view() first."
        )
    
    # Create enriched holdings view with ESG data and date-matched returns
    # Join holdings with returns from the closest prior trading date (handles weekends/holidays)
    session.sql(f"""
        CREATE OR REPLACE VIEW {database_name}.CURATED.V_HOLDINGS_WITH_ESG AS
        WITH holdings_with_returns AS (
            SELECT 
                h.PortfolioID,
                h.SecurityID,
                h.HoldingDate,
                h.Quantity,
                h.MarketValue_Base,
                h.MarketValue_Local,
                h.PortfolioWeight,
                h.CostBasis_Base,
                h.CostBasis_Local,
                h.AccruedInterest_Local,
                r.PRICE_CLOSE,
                r.DAILY_RETURN_PCT,
                r.MTD_RETURN_PCT,
                r.QTD_RETURN_PCT,
                r.YTD_RETURN_PCT,
                r.PRICE_DATE as RETURNS_DATE,
                -- Rank to get closest prior trading date
                ROW_NUMBER() OVER (
                    PARTITION BY h.PortfolioID, h.SecurityID, h.HoldingDate 
                    ORDER BY r.PRICE_DATE DESC
                ) as rn
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR h
            LEFT JOIN {database_name}.CURATED.V_SECURITY_RETURNS r 
                ON h.SecurityID = r.SECURITYID 
                AND r.PRICE_DATE <= h.HoldingDate
                AND r.PRICE_DATE >= DATEADD(day, -7, h.HoldingDate)  -- Within 7 days
        )
        SELECT 
            h.PortfolioID,
            h.SecurityID,
            h.HoldingDate,
            h.Quantity,
            h.MarketValue_Base,
            h.MarketValue_Local,
            h.PortfolioWeight,
            h.CostBasis_Base,
            h.CostBasis_Local,
            h.AccruedInterest_Local,
            e.ESG_SCORE,
            e.ESG_GRADE,
            h.PRICE_CLOSE as LATEST_PRICE,
            h.DAILY_RETURN_PCT,
            h.MTD_RETURN_PCT,
            h.QTD_RETURN_PCT,
            h.YTD_RETURN_PCT,
            h.RETURNS_DATE
        FROM holdings_with_returns h
        LEFT JOIN {database_name}.CURATED.V_ESG_LATEST e ON h.SecurityID = e.SecurityID
        WHERE h.rn = 1 OR h.rn IS NULL  -- Get closest match or keep rows with no match
    """).collect()
    
    log_detail(f"  Created V_HOLDINGS_WITH_ESG enriched view (with returns data)")
    

def build_factor_exposures(session: Session):
    """Build factor exposures from real data: prices, returns, and SEC financials.
    
    Calculates 7 factors monthly, cross-sectionally z-scored and winsorized at ±3σ:
    - Market Beta: REGR_SLOPE of security daily returns vs SPY
    - Size: LN(SHARES_OUTSTANDING * PRICE_CLOSE) = LN(Market Cap)
    - Value: composite of earnings yield (EPS/Price) and book-to-market
    - Momentum: 12-1 month price return
    - Growth: composite of revenue growth and earnings growth
    - Quality: composite of ROE, operating margin, and inverse leverage
    - Volatility: 60-day rolling STDDEV of daily returns
    
    Sources: FACT_STOCK_PRICES, V_SECURITY_RETURNS, FACT_SEC_FINANCIALS, FACT_BENCHMARK_RETURNS
    Output schema: SecurityID, EXPOSURE_DATE, FACTOR_NAME, EXPOSURE_VALUE, R_SQUARED
    """
    
    database_name = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{curated}.FACT_FACTOR_EXPOSURES AS
        WITH equity_securities AS (
            SELECT s.SecurityID, s.Ticker, s.IssuerID
            FROM {database_name}.{curated}.DIM_SECURITY s
            WHERE s.AssetClass = 'Equity'
        ),
        monthly_prices AS (
            SELECT
                p.SecurityID,
                DATE_TRUNC('month', p.PRICE_DATE) AS MONTH_END,
                LAST_VALUE(p.PRICE_CLOSE) OVER (
                    PARTITION BY p.SecurityID, DATE_TRUNC('month', p.PRICE_DATE)
                    ORDER BY p.PRICE_DATE
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) AS CLOSE_PRICE,
                AVG(p.VOLUME) AS AVG_VOLUME
            FROM {database_name}.{market_data}.FACT_STOCK_PRICES p
            JOIN equity_securities es ON p.SecurityID = es.SecurityID
            WHERE p.PRICE_DATE >= DATEADD('year', -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
            GROUP BY p.SecurityID, DATE_TRUNC('month', p.PRICE_DATE), p.PRICE_DATE, p.PRICE_CLOSE, p.VOLUME
        ),
        monthly_prices_dedup AS (
            SELECT SecurityID, MONTH_END, CLOSE_PRICE, AVG(AVG_VOLUME) AS AVG_VOLUME
            FROM monthly_prices
            GROUP BY SecurityID, MONTH_END, CLOSE_PRICE
        ),
        monthly_financials AS (
            SELECT
                es.SecurityID,
                f.PERIOD_END_DATE,
                f.EPS_BASIC,
                f.EPS_DILUTED,
                f.TOTAL_EQUITY,
                f.REVENUE,
                f.NET_INCOME,
                f.OPERATING_MARGIN_PCT,
                f.ROE_PCT,
                f.DEBT_TO_EQUITY,
                f.REVENUE_GROWTH_PCT,
                f.SHARES_OUTSTANDING,
                ROW_NUMBER() OVER (PARTITION BY es.SecurityID, DATE_TRUNC('month', f.PERIOD_END_DATE) ORDER BY f.PERIOD_END_DATE DESC) AS RN
            FROM {database_name}.{market_data}.FACT_SEC_FINANCIALS f
            JOIN equity_securities es ON f.IssuerID = es.IssuerID
            WHERE f.PERIOD_END_DATE >= DATEADD('year', -{config.YEARS_OF_HISTORY + 1}, CURRENT_DATE())
        ),
        latest_financials AS (
            SELECT SecurityID, PERIOD_END_DATE, EPS_BASIC, EPS_DILUTED, TOTAL_EQUITY,
                   REVENUE, NET_INCOME, OPERATING_MARGIN_PCT, ROE_PCT, DEBT_TO_EQUITY,
                   REVENUE_GROWTH_PCT, SHARES_OUTSTANDING
            FROM monthly_financials WHERE RN = 1
        ),
        prices_with_lag AS (
            SELECT
                SecurityID, MONTH_END, CLOSE_PRICE,
                LAG(CLOSE_PRICE, 1) OVER (PARTITION BY SecurityID ORDER BY MONTH_END) AS PRICE_LAG_1,
                LAG(CLOSE_PRICE, 12) OVER (PARTITION BY SecurityID ORDER BY MONTH_END) AS PRICE_LAG_12
            FROM monthly_prices_dedup
        ),
        spx_returns AS (
            SELECT DATE AS RET_DATE, DAILY_RETURN AS SPX_RETURN
            FROM {database_name}.{market_data}.FACT_BENCHMARK_RETURNS
            WHERE BENCHMARK_CODE = 'SPX'
        ),
        daily_returns_joined AS (
            SELECT
                sr.SecurityID, sr.PRICE_DATE, sr.DAILY_RETURN_PCT,
                spx.SPX_RETURN,
                DATE_TRUNC('month', sr.PRICE_DATE) AS MONTH_END
            FROM {database_name}.{curated}.V_SECURITY_RETURNS sr
            JOIN spx_returns spx ON sr.PRICE_DATE = spx.RET_DATE
            WHERE sr.PRICE_DATE >= DATEADD('year', -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
        ),
        month_spine AS (
            SELECT DISTINCT SecurityID, MONTH_END FROM monthly_prices_dedup
        ),
        factor_market AS (
            SELECT
                ms.SecurityID,
                ms.MONTH_END AS EXPOSURE_DATE,
                'Market' AS FACTOR_NAME,
                REGR_SLOPE(drj.DAILY_RETURN_PCT, drj.SPX_RETURN) AS RAW_VALUE,
                REGR_R2(drj.DAILY_RETURN_PCT, drj.SPX_RETURN) AS R2_VALUE
            FROM month_spine ms
            JOIN daily_returns_joined drj
                ON drj.SecurityID = ms.SecurityID
                AND drj.PRICE_DATE > DATEADD('day', -252, ms.MONTH_END)
                AND drj.PRICE_DATE <= ms.MONTH_END
            GROUP BY ms.SecurityID, ms.MONTH_END
            HAVING COUNT(*) >= 120
        ),
        factor_size AS (
            SELECT
                mp.SecurityID,
                mp.MONTH_END AS EXPOSURE_DATE,
                'Size' AS FACTOR_NAME,
                LN(lf.SHARES_OUTSTANDING * mp.CLOSE_PRICE) AS RAW_VALUE,
                NULL AS R2_VALUE
            FROM monthly_prices_dedup mp
            JOIN latest_financials lf ON mp.SecurityID = lf.SecurityID
                AND lf.PERIOD_END_DATE <= mp.MONTH_END
                AND lf.PERIOD_END_DATE >= DATEADD('month', -6, mp.MONTH_END)
            WHERE lf.SHARES_OUTSTANDING > 0 AND mp.CLOSE_PRICE > 0
        ),
        factor_value AS (
            SELECT
                mp.SecurityID,
                mp.MONTH_END AS EXPOSURE_DATE,
                'Value' AS FACTOR_NAME,
                (COALESCE(lf.EPS_DILUTED, lf.EPS_BASIC, 0) / NULLIF(mp.CLOSE_PRICE, 0)
                 + COALESCE(lf.TOTAL_EQUITY, 0) / NULLIF(lf.SHARES_OUTSTANDING * mp.CLOSE_PRICE, 0)
                ) / 2.0 AS RAW_VALUE,
                NULL AS R2_VALUE
            FROM monthly_prices_dedup mp
            JOIN latest_financials lf ON mp.SecurityID = lf.SecurityID
                AND lf.PERIOD_END_DATE <= mp.MONTH_END
                AND lf.PERIOD_END_DATE >= DATEADD('month', -6, mp.MONTH_END)
            WHERE mp.CLOSE_PRICE > 0
        ),
        factor_momentum AS (
            SELECT
                SecurityID,
                MONTH_END AS EXPOSURE_DATE,
                'Momentum' AS FACTOR_NAME,
                CASE WHEN PRICE_LAG_12 > 0 AND PRICE_LAG_1 > 0
                     THEN (PRICE_LAG_1 / PRICE_LAG_12) - 1
                     ELSE NULL END AS RAW_VALUE,
                NULL AS R2_VALUE
            FROM prices_with_lag
            WHERE PRICE_LAG_12 IS NOT NULL
        ),
        factor_growth AS (
            SELECT
                mp.SecurityID,
                mp.MONTH_END AS EXPOSURE_DATE,
                'Growth' AS FACTOR_NAME,
                COALESCE(lf.REVENUE_GROWTH_PCT, 0) / 100.0 AS RAW_VALUE,
                NULL AS R2_VALUE
            FROM monthly_prices_dedup mp
            JOIN latest_financials lf ON mp.SecurityID = lf.SecurityID
                AND lf.PERIOD_END_DATE <= mp.MONTH_END
                AND lf.PERIOD_END_DATE >= DATEADD('month', -6, mp.MONTH_END)
        ),
        factor_quality AS (
            SELECT
                mp.SecurityID,
                mp.MONTH_END AS EXPOSURE_DATE,
                'Quality' AS FACTOR_NAME,
                (COALESCE(lf.ROE_PCT, 0) / 100.0
                 + COALESCE(lf.OPERATING_MARGIN_PCT, 0) / 100.0
                 - COALESCE(lf.DEBT_TO_EQUITY, 0)
                ) / 3.0 AS RAW_VALUE,
                NULL AS R2_VALUE
            FROM monthly_prices_dedup mp
            JOIN latest_financials lf ON mp.SecurityID = lf.SecurityID
                AND lf.PERIOD_END_DATE <= mp.MONTH_END
                AND lf.PERIOD_END_DATE >= DATEADD('month', -6, mp.MONTH_END)
        ),
        factor_volatility AS (
            SELECT
                ms.SecurityID,
                ms.MONTH_END AS EXPOSURE_DATE,
                'Volatility' AS FACTOR_NAME,
                STDDEV(drj.DAILY_RETURN_PCT) AS RAW_VALUE,
                NULL AS R2_VALUE
            FROM month_spine ms
            JOIN daily_returns_joined drj
                ON drj.SecurityID = ms.SecurityID
                AND drj.PRICE_DATE > DATEADD('day', -60, ms.MONTH_END)
                AND drj.PRICE_DATE <= ms.MONTH_END
            GROUP BY ms.SecurityID, ms.MONTH_END
            HAVING COUNT(*) >= 30
        ),
        all_factors AS (
            SELECT SecurityID, EXPOSURE_DATE, FACTOR_NAME, RAW_VALUE, R2_VALUE FROM factor_market
            UNION ALL
            SELECT SecurityID, EXPOSURE_DATE, FACTOR_NAME, RAW_VALUE, R2_VALUE FROM factor_size
            UNION ALL
            SELECT SecurityID, EXPOSURE_DATE, FACTOR_NAME, RAW_VALUE, R2_VALUE FROM factor_value
            UNION ALL
            SELECT SecurityID, EXPOSURE_DATE, FACTOR_NAME, RAW_VALUE, R2_VALUE FROM factor_momentum
            UNION ALL
            SELECT SecurityID, EXPOSURE_DATE, FACTOR_NAME, RAW_VALUE, R2_VALUE FROM factor_growth
            UNION ALL
            SELECT SecurityID, EXPOSURE_DATE, FACTOR_NAME, RAW_VALUE, R2_VALUE FROM factor_quality
            UNION ALL
            SELECT SecurityID, EXPOSURE_DATE, FACTOR_NAME, RAW_VALUE, R2_VALUE FROM factor_volatility
        ),
        factor_stats AS (
            SELECT FACTOR_NAME, EXPOSURE_DATE,
                   AVG(RAW_VALUE) AS MEAN_VAL,
                   STDDEV(RAW_VALUE) AS STD_VAL
            FROM all_factors
            WHERE RAW_VALUE IS NOT NULL
            GROUP BY FACTOR_NAME, EXPOSURE_DATE
        ),
        z_scored AS (
            SELECT
                af.SecurityID,
                af.EXPOSURE_DATE,
                af.FACTOR_NAME,
                CASE WHEN fs.STD_VAL > 0
                     THEN GREATEST(-3, LEAST(3, (af.RAW_VALUE - fs.MEAN_VAL) / fs.STD_VAL))
                     ELSE 0 END AS EXPOSURE_VALUE,
                af.R2_VALUE AS R_SQUARED
            FROM all_factors af
            JOIN factor_stats fs ON af.FACTOR_NAME = fs.FACTOR_NAME AND af.EXPOSURE_DATE = fs.EXPOSURE_DATE
            WHERE af.RAW_VALUE IS NOT NULL
        )
        SELECT SecurityID, EXPOSURE_DATE, FACTOR_NAME,
               ROUND(EXPOSURE_VALUE, 6) AS EXPOSURE_VALUE,
               ROUND(R_SQUARED, 4) AS R_SQUARED
        FROM z_scored
    """).collect()
    

def build_benchmark_holdings(session: Session):
    """Build benchmark holdings with SecurityID linkage using config-driven SQL generation.
    
    For S&P 500: Uses real N-PORT weights from Invesco S&P 500 Equal Weight ETF where
    available (matched via ISSUER_LEI → COMPANY_INDEX → PRIMARY_TICKER → DIM_SECURITY),
    falling back to config-driven synthetic weights for unmatched securities.
    
    For other benchmarks: Uses config from BENCHMARKS[*]['holdings_rules'] for:
    - Constituent counts, filters, raw weight ranges, min weight thresholds
    """
    
    database_name = config.DATABASE['name']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_BENCHMARK_HOLDINGS. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    weight_cases = []
    constituent_filter_cases = []
    
    for bm in config.BENCHMARKS:
        bm_name = bm['name']
        rules = bm['holdings_rules']
        filters = rules['filters']
        count = rules['constituent_count']
        min_weight = rules['min_weight']
        
        filter_conds = []
        if 'country' in filters:
            filter_conds.append(f"es.CountryOfIncorporation = '{filters['country']}'")
        if 'sector' in filters:
            filter_conds.append(f"es.SIC_DESCRIPTION = '{filters['sector']}'")
        if 'exclude_sector' in filters:
            filter_conds.append(f"es.SIC_DESCRIPTION != '{filters['exclude_sector']}'")
        
        filter_sql = ' AND '.join(filter_conds) if filter_conds else 'TRUE'
        
        if 'weight_by_country' in rules:
            wbc = rules['weight_by_country']
            weight_subcases = []
            for country, weight_range in wbc.items():
                if country != '_default':
                    weight_subcases.append(f"WHEN es.CountryOfIncorporation = '{country}' THEN UNIFORM({weight_range[0]}, {weight_range[1]}, RANDOM())")
            default_range = wbc['_default']
            weight_sql = f"CASE {' '.join(weight_subcases)} ELSE UNIFORM({default_range[0]}, {default_range[1]}, RANDOM()) END"
        else:
            weight_range = rules['raw_weight_range']
            weight_sql = f"UNIFORM({weight_range[0]}, {weight_range[1]}, RANDOM())"
        
        weight_cases.append(f"WHEN b.BenchmarkName = '{bm_name}' AND {filter_sql} THEN {weight_sql}")
        constituent_filter_cases.append(f"(BenchmarkName = '{bm_name}' AND rn <= {count})")
    
    weight_case_sql = f"CASE {' '.join(weight_cases)} ELSE NULL END"
    constituent_filter_sql = ' OR '.join(constituent_filter_cases)
    
    assumed_mv = config.BENCHMARKS[0]['holdings_rules']['assumed_benchmark_mv_usd']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_BENCHMARK_HOLDINGS AS
        WITH nport_weights AS (
            SELECT 
                ds.SecurityID,
                idx.REPORTED_DATE AS NPORT_DATE,
                inv.PERCENT_OF_FUND_NET_ASSETS AS REAL_WEIGHT
            FROM {real_db}.{real_schema}.SEC_NPORT_FILING_INDEX idx
            JOIN {real_db}.{real_schema}.SEC_NPORT_INVESTMENTS_INDEX inv ON idx.ADSH = inv.ADSH
            JOIN {real_db}.{real_schema}.COMPANY_INDEX ci ON ARRAY_CONTAINS(inv.ISSUER_LEI::VARIANT, ci.LEI)
            JOIN {database_name}.CURATED.DIM_ISSUER di ON ci.COMPANY_ID = di.ProviderCompanyID
            JOIN {database_name}.CURATED.DIM_SECURITY ds ON di.IssuerID = ds.IssuerID AND ds.AssetClass = 'Equity'
            WHERE idx.SERIES_NAME = 'Invesco S&P 500 Equal Weight ETF'
            AND inv.ASSET_TYPE = 'Equity-common'
            AND inv.ISSUER_LEI IS NOT NULL
            AND inv.PERCENT_OF_FUND_NET_ASSETS > 0
            QUALIFY ROW_NUMBER() OVER (PARTITION BY ds.SecurityID, idx.REPORTED_DATE ORDER BY inv.INVESTMENT_VALUE DESC NULLS LAST) = 1
        ),
        equity_securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.SIC_DESCRIPTION,
                i.CountryOfIncorporation
            FROM {database_name}.CURATED.DIM_SECURITY s
            JOIN {database_name}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {database_name}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        benchmarks AS (
            SELECT BenchmarkID, BenchmarkName FROM {database_name}.CURATED.DIM_BENCHMARK
        ),
        monthly_dates AS (
            SELECT LAST_DAY(DATEADD(month, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, '{max_price_date}'::DATE))) as HOLDING_DATE
            FROM TABLE(GENERATOR(rowcount => {12 * config.YEARS_OF_HISTORY}))
            WHERE HOLDING_DATE <= '{max_price_date}'::DATE
        ),
        benchmark_universe AS (
            SELECT 
                b.BenchmarkID,
                b.BenchmarkName,
                es.SecurityID,
                es.TICKER,
                es.SIC_DESCRIPTION,
                es.CountryOfIncorporation,
                md.HOLDING_DATE,
                {weight_case_sql} as RAW_WEIGHT,
                ROW_NUMBER() OVER (PARTITION BY b.BenchmarkID, md.HOLDING_DATE ORDER BY RANDOM()) as rn
            FROM benchmarks b
            CROSS JOIN equity_securities es
            CROSS JOIN monthly_dates md
        ),
        filtered_holdings AS (
            SELECT *
            FROM benchmark_universe
            WHERE RAW_WEIGHT IS NOT NULL
            AND ({constituent_filter_sql})
        ),
        latest_nport AS (
            SELECT 
                fh.SecurityID,
                fh.HOLDING_DATE,
                nw.REAL_WEIGHT,
                nw.NPORT_DATE
            FROM filtered_holdings fh
            JOIN nport_weights nw 
                ON fh.SecurityID = nw.SecurityID
                AND fh.BenchmarkName = 'S&P 500'
                AND nw.NPORT_DATE <= fh.HOLDING_DATE
            QUALIFY ROW_NUMBER() OVER (PARTITION BY fh.SecurityID, fh.HOLDING_DATE ORDER BY nw.NPORT_DATE DESC) = 1
        ),
        with_real_weights AS (
            SELECT 
                fh.*,
                ln.REAL_WEIGHT,
                CASE 
                    WHEN fh.BenchmarkName = 'S&P 500' AND ln.REAL_WEIGHT IS NOT NULL 
                    THEN ln.REAL_WEIGHT
                    ELSE fh.RAW_WEIGHT / SUM(fh.RAW_WEIGHT) OVER (PARTITION BY fh.BenchmarkID, fh.HOLDING_DATE)
                END AS BLENDED_WEIGHT
            FROM filtered_holdings fh
            LEFT JOIN latest_nport ln 
                ON fh.SecurityID = ln.SecurityID
                AND fh.HOLDING_DATE = ln.HOLDING_DATE
                AND fh.BenchmarkName = 'S&P 500'
        ),
        normalized_weights AS (
            SELECT 
                *,
                BLENDED_WEIGHT / SUM(BLENDED_WEIGHT) OVER (PARTITION BY BenchmarkID, HOLDING_DATE) as WEIGHT
            FROM with_real_weights
        )
        SELECT 
            BenchmarkID,
            SecurityID,
            HOLDING_DATE,
            WEIGHT as BENCHMARK_WEIGHT,
            WEIGHT * {assumed_mv} as MARKET_VALUE_USD
        FROM normalized_weights
        WHERE WEIGHT >= 0.0001
    """).collect()
    

def build_fact_benchmark_performance(session: Session):
    """
    Build benchmark-level performance returns (MTD, QTD, YTD) from constituent data.
    
    This table stores aggregated benchmark returns calculated by weighting constituent
    security returns by their benchmark weights. Enables queries like:
    - "What is the Q4 2024 benchmark performance for MSCI ACWI?"
    - "Compare portfolio returns vs benchmark returns"
    
    Used by: SAM_ANALYST_VIEW for benchmark performance comparison
    Grain: One row per benchmark per date
    """
    database_name = config.DATABASE['name']
    
    # Ensure database context is set (required for temp stage creation in complex queries)
    session.sql(f"USE DATABASE {database_name}").collect()
    session.sql(f"USE SCHEMA {config.DATABASE['schemas']['curated']}").collect()
    
    # Check if required source tables exist
    try:
        session.sql(f"SELECT 1 FROM {database_name}.CURATED.FACT_BENCHMARK_HOLDINGS LIMIT 1").collect()
        session.sql(f"SELECT 1 FROM {database_name}.MARKET_DATA.FACT_STOCK_PRICES LIMIT 1").collect()
    except Exception as e:
        raise RuntimeError(
            f"Required tables not found for FACT_BENCHMARK_PERFORMANCE: {e}. "
            "Ensure FACT_BENCHMARK_HOLDINGS and FACT_STOCK_PRICES are built first."
        )
    
    # First check if V_SECURITY_RETURNS exists (needed for accurate period returns)
    try:
        session.sql(f"SELECT 1 FROM {database_name}.CURATED.V_SECURITY_RETURNS LIMIT 1").collect()
    except Exception as e:
        raise RuntimeError(
            f"V_SECURITY_RETURNS not found - cannot build FACT_BENCHMARK_PERFORMANCE: {e}. "
            "Run build_security_returns_view() first."
        )
    
    # Use V_SECURITY_RETURNS which has properly calculated period returns per security
    # Weight-average constituent returns to get benchmark returns
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_BENCHMARK_PERFORMANCE AS
        WITH -- Get benchmark holdings with security linkage and the latest returns per holding date
        -- Note: BenchmarkName available via BenchmarkID -> DIM_BENCHMARK join
        benchmark_constituents AS (
            SELECT 
                bh.BenchmarkID,
                bh.HOLDING_DATE,
                bh.SecurityID,
                bh.BENCHMARK_WEIGHT
            FROM {database_name}.CURATED.FACT_BENCHMARK_HOLDINGS bh
        ),
        -- Join with security returns for the appropriate date
        -- Match security returns to closest available date <= holding date
        constituent_returns AS (
            SELECT 
                bc.BenchmarkID,
                bc.HOLDING_DATE,
                bc.SecurityID,
                bc.BENCHMARK_WEIGHT,
                sr.MTD_RETURN_PCT,
                sr.QTD_RETURN_PCT,
                sr.YTD_RETURN_PCT,
                ROW_NUMBER() OVER (
                    PARTITION BY bc.BenchmarkID, bc.HOLDING_DATE, bc.SecurityID 
                    ORDER BY sr.PRICE_DATE DESC
                ) as rn
            FROM benchmark_constituents bc
            JOIN {database_name}.CURATED.V_SECURITY_RETURNS sr 
                ON bc.SecurityID = sr.SECURITYID
                AND sr.PRICE_DATE <= bc.HOLDING_DATE
                AND sr.PRICE_DATE >= DATEADD(day, -7, bc.HOLDING_DATE)  -- Within 7 days
        ),
        -- Calculate weighted average returns for each benchmark per date
        benchmark_period_returns AS (
            SELECT 
                BenchmarkID,
                HOLDING_DATE as PerformanceDate,
                -- Weighted average MTD return
                SUM(BENCHMARK_WEIGHT * COALESCE(MTD_RETURN_PCT, 0)) as MTD_RETURN_PCT,
                -- Weighted average QTD return
                SUM(BENCHMARK_WEIGHT * COALESCE(QTD_RETURN_PCT, 0)) as QTD_RETURN_PCT,
                -- Weighted average YTD return
                SUM(BENCHMARK_WEIGHT * COALESCE(YTD_RETURN_PCT, 0)) as YTD_RETURN_PCT
            FROM constituent_returns
            WHERE rn = 1  -- Only use the closest matching date per constituent
            GROUP BY BenchmarkID, HOLDING_DATE
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PerformanceDate, BenchmarkID) as BenchmarkPerfID,
            BenchmarkID,
            PerformanceDate,
            ROUND(MTD_RETURN_PCT, 2) as MTD_RETURN_PCT,
            ROUND(QTD_RETURN_PCT, 2) as QTD_RETURN_PCT,
            ROUND(YTD_RETURN_PCT, 2) as YTD_RETURN_PCT,
            -- Annualized return: extrapolate YTD to full year
            ROUND(
                YTD_RETURN_PCT * (365.0 / GREATEST(DATEDIFF('day', DATE_TRUNC('YEAR', PerformanceDate), PerformanceDate), 1)), 
                2
            ) as ANNUALIZED_RETURN_PCT,
            CURRENT_TIMESTAMP() as CREATED_AT
        FROM benchmark_period_returns
        ORDER BY PerformanceDate DESC, BenchmarkID
    """).collect()
    
    # Verify creation
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.FACT_BENCHMARK_PERFORMANCE").collect()[0]['CNT']
    log_detail(f"  Created FACT_BENCHMARK_PERFORMANCE with {count:,} records")


def build_transaction_cost_data(session: Session):
    """Build transaction cost and market microstructure data.
    
    Enhances with real data from FACT_STOCK_PRICES where available:
    - BID_ASK_SPREAD_BPS: real high-low spread proxy ((HIGH-LOW)/CLOSE * 10000)
    - AVG_DAILY_VOLUME_M: real Nasdaq volume (shares / 1,000,000)
    Falls back to config-driven synthetic values for stocks without price data.
    
    Always synthetic:
    - Market impact (sector-based from config)
    - Commission rates (global from config)
    - Settlement days (country-based from config)
    """
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_TRANSACTION_COSTS. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    bid_ask_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'transaction_costs.bid_ask_spread_bps')
    volume_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'transaction_costs.daily_volume_m')
    impact_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'transaction_costs.market_impact_bps_per_1m')
    commission_sql = build_global_uniform_sql('transaction_cost_globals.commission_bps')
    settlement_sql = build_country_settlement_case_sql('es.CountryOfIncorporation')
    
    from utils.config_helpers import get_global_value
    business_days_window = get_global_value('transaction_cost_globals.business_days_window', 66)
    business_months_window = get_global_value('transaction_cost_globals.business_months_window', 3)
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_TRANSACTION_COSTS AS
        WITH equity_securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.SIC_DESCRIPTION,
                i.CountryOfIncorporation
            FROM {database_name}.CURATED.DIM_SECURITY s
            JOIN {database_name}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {database_name}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        business_dates AS (
            SELECT DATEADD(day, seq4(), DATEADD(month, -{business_months_window}, '{max_price_date}'::DATE)) as COST_DATE
            FROM TABLE(GENERATOR(rowcount => {business_days_window}))
            WHERE DAYOFWEEK(COST_DATE) BETWEEN 2 AND 6
              AND COST_DATE <= '{max_price_date}'::DATE
        ),
        real_prices AS (
            SELECT 
                sp.SecurityID,
                sp.PRICE_DATE,
                sp.PRICE_HIGH,
                sp.PRICE_LOW,
                sp.PRICE_CLOSE,
                sp.VOLUME
            FROM {database_name}.{market_data_schema}.FACT_STOCK_PRICES sp
            WHERE sp.PRICE_DATE >= DATEADD(month, -{business_months_window}, '{max_price_date}'::DATE)
        )
        SELECT 
            es.SecurityID,
            bd.COST_DATE,
            COALESCE(
                CASE WHEN rp.PRICE_CLOSE > 0 AND rp.PRICE_LOW > 0
                     THEN ROUND((rp.PRICE_HIGH - rp.PRICE_LOW) / rp.PRICE_CLOSE * 10000, 2)
                     ELSE NULL END,
                {bid_ask_sql}
            ) as BID_ASK_SPREAD_BPS,
            COALESCE(
                CASE WHEN rp.VOLUME IS NOT NULL THEN ROUND(rp.VOLUME / 1000000.0, 3) ELSE NULL END,
                {volume_sql}
            ) as AVG_DAILY_VOLUME_M,
            {impact_sql} as MARKET_IMPACT_BPS_PER_1M,
            {commission_sql} as COMMISSION_BPS,
            {settlement_sql} as SETTLEMENT_DAYS
        FROM equity_securities es
        CROSS JOIN business_dates bd
        LEFT JOIN real_prices rp
            ON es.SecurityID = rp.SecurityID AND bd.COST_DATE = rp.PRICE_DATE
    """).collect()
    

def build_liquidity_data(session: Session):
    """Build liquidity and cash flow data using config-driven SQL generation.
    
    Uses config from DATA_MODEL['synthetic_distributions']['global']:
    - liquidity_by_strategy: Strategy-based liquidity scores and rebalancing frequencies
    - cash: Global cash position and cashflow ranges
    """
    
    database_name = config.DATABASE['name']
    
    # Get max price date as upper bound (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_PORTFOLIO_LIQUIDITY. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Build config-driven SQL expressions
    liquidity_score_sql = build_strategy_case_sql('p.Strategy', 'liquidity_by_strategy', 'liquidity_score')
    rebalancing_sql = build_strategy_case_sql('p.Strategy', 'liquidity_by_strategy', 'rebalancing_days')
    cash_position_sql = build_global_uniform_sql('cash.cash_position_range_usd')
    cashflow_sql = build_global_uniform_sql('cash.net_cashflow_30d_range_usd')
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_PORTFOLIO_LIQUIDITY AS
        WITH portfolios AS (
            SELECT PortfolioID, PortfolioName, Strategy FROM {database_name}.CURATED.DIM_PORTFOLIO
        ),
        monthly_dates AS (
            SELECT DATEADD(month, seq4(), DATEADD(month, -12, '{max_price_date}'::DATE)) as LIQUIDITY_DATE
            FROM TABLE(GENERATOR(rowcount => 12))
            WHERE LIQUIDITY_DATE <= '{max_price_date}'::DATE
        )
        SELECT 
            p.PortfolioID,
            md.LIQUIDITY_DATE,
            -- Available cash position (global from config)
            {cash_position_sql} as CASH_POSITION_USD,
            -- Expected cash flows (global from config)
            {cashflow_sql} as NET_CASHFLOW_30D_USD,
            -- Liquidity score (strategy-specific from config)
            {liquidity_score_sql} as PORTFOLIO_LIQUIDITY_SCORE,
            -- Rebalancing frequency (strategy-specific from config)
            {rebalancing_sql} as REBALANCING_FREQUENCY_DAYS
        FROM portfolios p
        CROSS JOIN monthly_dates md
    """).collect()
    

def build_risk_budget_data(session: Session):
    """Build risk budget and limits data using config-driven SQL generation.
    
    Uses config from DATA_MODEL['synthetic_distributions']['global']:
    - risk_limits_by_strategy: Strategy-based tracking error and sector concentration limits
    - risk_globals: Global risk metrics ranges
    
    Also uses COMPLIANCE_RULES['concentration'] for position limits.
    """
    
    database_name = config.DATABASE['name']
    
    # Get max price date as reference (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_RISK_LIMITS. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Build config-driven SQL expressions
    tracking_error_limit_sql = build_strategy_case_sql('p.Strategy', 'risk_limits_by_strategy', 'tracking_error_limit')
    sector_concentration_sql = build_strategy_case_sql('p.Strategy', 'risk_limits_by_strategy', 'max_sector_concentration')
    current_te_sql = build_global_uniform_sql('risk_globals.current_tracking_error_pct')
    utilization_sql = build_global_uniform_sql('risk_globals.risk_budget_utilization_pct')
    var_sql = build_global_uniform_sql('risk_globals.var_limit_1day_pct')
    
    # Get compliance limits from existing config
    tech_max = config.COMPLIANCE_RULES['concentration']['tech_portfolio_max']
    default_max = config.COMPLIANCE_RULES['concentration']['max_single_issuer']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_RISK_LIMITS AS
        WITH portfolios AS (
            SELECT PortfolioID, PortfolioName, Strategy FROM {database_name}.CURATED.DIM_PORTFOLIO
        )
        SELECT 
            p.PortfolioID,
            '{max_price_date}'::DATE as LIMITS_DATE,
            -- Tracking error limits (strategy-specific from config)
            {tracking_error_limit_sql} as TRACKING_ERROR_LIMIT_PCT,
            -- Current tracking error utilization (global from config)
            {current_te_sql} as CURRENT_TRACKING_ERROR_PCT,
            -- Maximum single position concentration (from COMPLIANCE_RULES)
            CASE 
                WHEN p.PortfolioName LIKE '%Technology%' THEN {tech_max}
                ELSE {default_max}
            END as MAX_SINGLE_POSITION_PCT,
            -- Maximum sector concentration (strategy-specific from config)
            {sector_concentration_sql} as MAX_SECTOR_CONCENTRATION_PCT,
            -- Risk budget utilization (global from config)
            {utilization_sql} as RISK_BUDGET_UTILIZATION_PCT,
            -- VaR limits (global from config)
            {var_sql} as VAR_LIMIT_1DAY_PCT
        FROM portfolios p
    """).collect()
    

def build_trading_calendar_data(session: Session):
    """Build trading calendar with blackout periods and market events using config-driven SQL.
    
    Uses config from DATA_MODEL['synthetic_distributions']['global']['calendar']:
    - earnings_frequency_days: Quarterly earnings announcements
    - monthly_review_frequency_days: Monthly rebalancing frequency
    - weekly_review_frequency_days: Weekly review frequency
    - vix_range: Expected VIX range
    - options_expiration_frequency_days: Options expiration cycle
    """
    
    database_name = config.DATABASE['name']
    
    # Get max price date as reference "today" for future events (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_TRADING_CALENDAR. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Get calendar config values
    from utils.config_helpers import get_global_value
    earnings_freq = get_global_value('calendar.earnings_frequency_days', 90)
    monthly_freq = get_global_value('calendar.monthly_review_frequency_days', 30)
    weekly_freq = get_global_value('calendar.weekly_review_frequency_days', 7)
    vix_range = get_global_value('calendar.vix_range', (12, 35))
    options_freq = get_global_value('calendar.options_expiration_frequency_days', 21)
    
    vix_sql = f"UNIFORM({vix_range[0]}, {vix_range[1]}, RANDOM())"
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_TRADING_CALENDAR AS
        WITH securities AS (
            SELECT s.SecurityID, s.Ticker 
            FROM {database_name}.CURATED.DIM_SECURITY s
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {database_name}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        future_dates AS (
            -- Generate future dates relative to max_price_date (our reference "today")
            SELECT DATEADD(day, seq4(), '{max_price_date}'::DATE) as EVENT_DATE
            FROM TABLE(GENERATOR(rowcount => 90))  -- Next 90 days from reference date
        )
        SELECT 
            s.SecurityID,
            fd.EVENT_DATE,
            -- Earnings announcement dates (quarterly from config)
            CASE 
                WHEN MOD(DATEDIFF(day, '{max_price_date}'::DATE, fd.EVENT_DATE), {earnings_freq}) = 0 THEN 'EARNINGS_ANNOUNCEMENT'
                WHEN MOD(DATEDIFF(day, '{max_price_date}'::DATE, fd.EVENT_DATE), {monthly_freq}) = 0 THEN 'MONTHLY_REBALANCING'
                WHEN MOD(DATEDIFF(day, '{max_price_date}'::DATE, fd.EVENT_DATE), {weekly_freq}) = 0 THEN 'WEEKLY_REVIEW'
                ELSE NULL
            END as EVENT_TYPE,
            -- Blackout period indicator (around earnings)
            CASE 
                WHEN MOD(DATEDIFF(day, '{max_price_date}'::DATE, fd.EVENT_DATE), {earnings_freq}) BETWEEN -2 AND 2 THEN TRUE
                ELSE FALSE
            END as IS_BLACKOUT_PERIOD,
            -- Market volatility forecast (from config)
            {vix_sql} as EXPECTED_VIX_LEVEL,
            -- Options expiration indicator (from config)
            CASE 
                WHEN MOD(DATEDIFF(day, '{max_price_date}'::DATE, fd.EVENT_DATE), {options_freq}) = 0 THEN TRUE
                ELSE FALSE
            END as IS_OPTIONS_EXPIRATION
        FROM securities s
        CROSS JOIN future_dates fd
        WHERE fd.EVENT_DATE IS NOT NULL
    """).collect()
    

def build_client_mandate_data(session: Session):
    """Build client mandate and approval requirements data using config-driven SQL.
    
    Uses config from DATA_MODEL['synthetic_distributions']['global']['client_mandates']:
    - approval_thresholds: Strategy/portfolio-based approval thresholds
    - sector_allocation_defaults: Strategy-based sector allocation ranges
    
    Also uses COMPLIANCE_RULES['esg']['min_overall_rating'] for ESG requirements.
    """
    
    database_name = config.DATABASE['name']
    
    # Get mandate config values - all fields required
    from utils.config_helpers import get_global_value
    mandates_config = get_global_value('client_mandates')  # No default - require it
    approval_thresholds = mandates_config['approval_thresholds']
    sector_allocations = mandates_config['sector_allocation_defaults']
    
    # Build approval threshold CASE SQL
    approval_cases = []
    for key, threshold in approval_thresholds.items():
        if key != '_default':
            approval_cases.append(f"WHEN p.PortfolioName LIKE '%{key}%' THEN {threshold}")
    default_approval = approval_thresholds['_default']
    approval_sql = f"CASE {' '.join(approval_cases)} ELSE {default_approval} END" if approval_cases else str(default_approval)
    
    # Build sector allocation CASE SQL (JSON strings)
    import json
    sector_cases = []
    for key, allocations in sector_allocations.items():
        if key != '_default':
            json_str = json.dumps(allocations).replace('"', '\\"')
            sector_cases.append(f"WHEN p.PortfolioName LIKE '%{key}%' THEN '\"{json_str}\"'")
    default_alloc = json.dumps(sector_allocations['_default']).replace('"', '\\"')
    sector_sql = f"CASE {' '.join(sector_cases)} ELSE '\"{default_alloc}\"' END" if sector_cases else f"'\"{default_alloc}\"'"
    
    # Get ESG minimum rating from COMPLIANCE_RULES
    esg_min_rating = config.COMPLIANCE_RULES['esg']['min_overall_rating']
    
    # Build rebalancing CASE using strategy config
    rebalancing_sql = build_strategy_case_sql('p.Strategy', 'liquidity_by_strategy', 'rebalancing_days')
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.DIM_CLIENT_MANDATES AS
        WITH portfolios AS (
            SELECT PortfolioID, PortfolioName, Strategy FROM {database_name}.CURATED.DIM_PORTFOLIO
        )
        SELECT 
            p.PortfolioID,
            -- Approval thresholds (from config)
            {approval_sql} as POSITION_CHANGE_APPROVAL_THRESHOLD_PCT,
            -- Sector allocation ranges (from config)
            CASE 
                WHEN p.PortfolioName LIKE '%Technology%' THEN '{{"Technology": [0.30, 0.50], "Healthcare": [0.05, 0.15]}}'
                WHEN p.PortfolioName LIKE '%ESG%' THEN '{{"Technology": [0.15, 0.35], "Energy": [0.00, 0.05]}}'
                ELSE '{{"Technology": [0.10, 0.40], "Healthcare": [0.05, 0.20]}}'
            END as SECTOR_ALLOCATION_RANGES_JSON,
            -- ESG requirements (from COMPLIANCE_RULES)
            CASE 
                WHEN p.PortfolioName LIKE '%ESG%' THEN '{esg_min_rating}'
                WHEN p.PortfolioName LIKE '%Climate%' THEN 'BB'
                ELSE NULL
            END as MIN_ESG_RATING,
            -- Exclusion lists (static for now)
            CASE 
                WHEN p.PortfolioName LIKE '%ESG%' THEN '["Tobacco", "Weapons", "Thermal Coal"]'
                WHEN p.PortfolioName LIKE '%Climate%' THEN '["Fossil Fuels", "Thermal Coal"]'
                ELSE '[]'
            END as EXCLUSION_SECTORS_JSON,
            -- Rebalancing requirements (strategy-based from config)
            {rebalancing_sql} as MAX_REBALANCING_FREQUENCY_DAYS
        FROM portfolios p
    """).collect()
    

def build_dim_client(session: Session, test_mode: bool = False):
    """
    Build client dimension table with institutional client entities.
    Links to portfolios via FACT_CLIENT_FLOWS for client flow analytics.
    
    Uses unified DEMO_CLIENTS from config (with category: standard/at_risk/new)
    for demo clients with realistic names, then generates additional clients 
    with generic patterns via set-based SQL.
    
    Config-driven via DATA_MODEL['synthetic_distributions']['global']['client']:
    - total_count / total_count_test_mode
    - aum_range_usd, tenure_days_range
    - demo_tenure_base_days, demo_tenure_multiplier_days
    - primary_contacts, client_types, regions
    
    I/O Pattern: 
    - Demo clients: Build in Python, batch write with write_pandas_overwrite
    - Generated clients: Set-based INSERT...SELECT (no collect-in-loop)
    
    Used by: Executive Copilot for client flow analysis
    Can also be used by: Sales Advisor for client-specific reporting
    """
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Get max price date as reference "today" (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build DIM_CLIENT. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Get client config - all fields required
    from utils.config_helpers import get_global_value
    client_config = get_global_value('client')  # No default - require it
    total_clients = client_config['total_count_test_mode'] if test_mode else client_config['total_count']
    contacts = client_config['primary_contacts']
    tenure_base = client_config['demo_tenure_base_days']
    tenure_multiplier = client_config['demo_tenure_multiplier_days']
    aum_range = client_config['aum_range_usd']
    tenure_range = client_config['tenure_days_range']
    client_types = client_config['client_types']
    regions = client_config['regions']
    
    # Get ALL demo clients from config (standard + at-risk + new, sorted by priority)
    demo_clients = get_all_demo_clients_sorted()
    num_demo_clients = len(demo_clients)
    
    # Total clients: demo clients + generated clients
    num_generated = max(0, total_clients - num_demo_clients)
    
    # Calculate max priority for tenure formula
    max_priority = max((c['priority'] for c in demo_clients), default=14)
    
    # Step 1: Build demo client rows in Python (batched pattern)
    rows = []
    for i, client in enumerate(demo_clients, 1):
        # Calculate middle of AUM range
        aum = (client['aum_range'][0] + client['aum_range'][1]) // 2
        
        # Relationship tenure: new clients have short tenure, others based on priority
        if client['category'] == 'new':
            # New clients: use days_since_onboard from config
            tenure_days = client['days_since_onboard']
        else:
            # Established clients: longer tenure based on priority (from config formula)
            tenure_days = tenure_base + (max_priority + 1 - client['priority']) * tenure_multiplier
        
        contact = contacts[(i - 1) % len(contacts)]
        
        rows.append({
            'CLIENTID': i,
            'CLIENTNAME': client['client_name'],
            'CLIENTTYPE': client['client_type'],
            'REGION': client['region'],
            'AUM_WITH_SAM': aum,
            'RELATIONSHIPSTARTDATE': max_price_date - timedelta(days=tenure_days),
            'PRIMARYCONTACT': contact,
            'ACCOUNTSTATUS': 'Active'
        })
    
    # Step 2: Write demo clients using write_pandas (single batch write)
    import pandas as pd
    from utils.snowflake import cleanup_temp_stages
    cleanup_temp_stages(session)  # Clean up any leftover temp stages
    
    df = pd.DataFrame(rows)
    session.write_pandas(
        df, 'DIM_CLIENT',
        database=database_name, schema='CURATED',
        quote_identifiers=False, overwrite=True, auto_create_table=True
    )
    
    # Step 3: Append generated clients via set-based INSERT...SELECT (no collect-in-loop)
    if num_generated > 0:
        # Get generated name patterns from config
        name_patterns = client_config['generated_name_patterns']
        
        # Build client name CASE from config
        num_patterns = len(name_patterns)
        name_cases = ' '.join([f"WHEN {i} THEN '{p}'" for i, p in enumerate(name_patterns)])
        name_case_sql = f"CASE MOD(cs.ClientID, {num_patterns}) {name_cases} ELSE '{name_patterns[-1]}' END"
        
        # Build client type CASE from config
        num_types = len(client_types)
        type_cases = ' '.join([f"WHEN {i} THEN '{t}'" for i, t in enumerate(client_types)])
        type_case_sql = f"CASE MOD(cs.ClientID, {num_types}) {type_cases} ELSE '{client_types[0]}' END"
        
        # Build region CASE from config
        num_regions = len(regions)
        region_cases = ' '.join([f"WHEN {i} THEN '{r}'" for i, r in enumerate(regions)])
        region_case_sql = f"CASE MOD(cs.ClientID, {num_regions}) {region_cases} ELSE '{regions[0]}' END"
        
        # Build contact CASE from config (escape single quotes)
        num_contacts = min(len(contacts), 8)  # Limit to 8 for MOD simplicity
        contact_cases = ' '.join([f"WHEN {i} THEN '{contacts[i].replace(chr(39), chr(39)+chr(39))}'" for i in range(num_contacts)])
        contact_case_sql = f"CASE MOD(cs.ClientID, {num_contacts}) {contact_cases} ELSE '{contacts[0].replace(chr(39), chr(39)+chr(39))}' END"
        
        session.sql(f"""
            INSERT INTO {database_name}.CURATED.DIM_CLIENT
            -- Generated clients (name patterns from config)
            SELECT 
                cs.ClientID,
                {name_case_sql} || ' ' || LPAD(cs.ClientID::VARCHAR, 3, '0') as ClientName,
                {type_case_sql} as ClientType,
                {region_case_sql} as Region,
                ROUND(UNIFORM({aum_range[0]}, {aum_range[1]}, RANDOM()), -6) as AUM_with_SAM,
                DATEADD('day', -UNIFORM({tenure_range[0]}, {tenure_range[1]}, RANDOM()), '{max_price_date}'::DATE) as RelationshipStartDate,
                {contact_case_sql} as PrimaryContact,
                'Active' as AccountStatus
            FROM (
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY RANDOM()) + {num_demo_clients} as ClientID,
                    seq4() as seed_val
                FROM TABLE(GENERATOR(ROWCOUNT => {num_generated}))
            ) cs
        """).collect()
    
    # Verify creation
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.DIM_CLIENT").collect()[0]['CNT']
    log_detail(f"  Created DIM_CLIENT with {count} clients ({num_demo_clients} demo + {num_generated} generated)")

def build_fact_client_flows(session: Session, test_mode: bool = False):
    """
    Build client flow fact table with subscription/redemption data.
    Links DIM_CLIENT to DIM_PORTFOLIO for flow analytics.
    
    Config-driven via DATA_MODEL['synthetic_distributions']['global']['client_flows']:
    - months_of_history
    - standard_subscription_pct, standard_redemption_pct, at_risk_redemption_pct
    - allocation_weight_range, flow_amount_pct_range
    - esg_recent_inflow_multiplier, growth_volatility_range
    - monthly_flow_probability_pct
    
    Client flow patterns (based on DEMO_CLIENTS 'category' field):
    - category='standard': net positive inflows
    - category='at_risk': net negative (redemptions)
    - category='new': Only recent flow history
    
    Used by: Executive Copilot for analyzing client inflows/outflows
    Supports: "What's driving Sustainable Fixed Income inflows?" queries
    """
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED + 100)  # Different seed for variety
    
    # Get max price date as reference (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_CLIENT_FLOWS. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Get client flow config - all fields required
    from utils.config_helpers import get_global_value
    flow_config = get_global_value('client_flows')  # No default - require it
    months_of_history = flow_config['months_of_history']
    std_sub_pct = flow_config['standard_subscription_pct']
    std_red_pct = flow_config['standard_redemption_pct']
    at_risk_red_pct = flow_config['at_risk_redemption_pct']
    alloc_range = flow_config['allocation_weight_range']
    flow_pct_range = flow_config['flow_amount_pct_range']
    esg_mult = flow_config['esg_recent_inflow_multiplier']
    esg_months = flow_config['esg_recent_months']
    growth_vol_range = flow_config['growth_volatility_range']
    flow_prob = flow_config['monthly_flow_probability_pct']
    
    # Calculate cumulative thresholds for standard flow type assignment
    std_redemption_threshold = std_sub_pct + std_red_pct  # 95 = subscription + redemption, rest is transfer
    
    # Get at-risk and new client IDs for conditional flow generation
    at_risk_ids = get_at_risk_client_ids()
    new_client_ids = get_new_client_ids()
    
    # Build SQL-safe list of at-risk client IDs
    at_risk_ids_sql = f"({','.join(str(id) for id in at_risk_ids)})" if at_risk_ids else "(NULL)"
    new_client_ids_sql = f"({','.join(str(id) for id in new_client_ids)})" if new_client_ids else "(NULL)"
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_CLIENT_FLOWS AS
        WITH 
        -- Get all clients
        clients AS (
            SELECT ClientID, ClientName, ClientType, Region, AUM_with_SAM, RelationshipStartDate
            FROM {database_name}.CURATED.DIM_CLIENT
        ),
        -- Get all portfolios
        portfolios AS (
            SELECT PortfolioID, PortfolioName, Strategy
            FROM {database_name}.CURATED.DIM_PORTFOLIO
        ),
        -- Generate date range (monthly) up to max_price_date
        date_range AS (
            SELECT DATEADD('month', -seq4(), DATE_TRUNC('month', '{max_price_date}'::DATE)) as FlowDate
            FROM TABLE(GENERATOR(ROWCOUNT => {months_of_history}))
        ),
        -- Create client-portfolio assignments (clients invest in 1-3 portfolios)
        -- Distribution based on config: ~20% single, ~30% dual, ~50% triple
        client_portfolio_map AS (
            SELECT 
                c.ClientID,
                p.PortfolioID,
                -- Weight for this client-portfolio pair (for flow sizing) - from config
                UNIFORM({alloc_range[0]}, {alloc_range[1]}, RANDOM()) as AllocationWeight
            FROM clients c
            CROSS JOIN portfolios p
            WHERE 
                CASE 
                    -- ~20% of clients (ClientID mod 5 = 0) get only 1 portfolio
                    WHEN MOD(c.ClientID, 5) = 0 THEN 
                        p.PortfolioID = MOD(c.ClientID, 10) + 1
                    -- ~30% of clients (ClientID mod 5 = 1 or 2) get 2 portfolios
                    WHEN MOD(c.ClientID, 5) IN (1, 2) THEN
                        p.PortfolioID IN (MOD(c.ClientID, 10) + 1, MOD(c.ClientID + 3, 10) + 1)
                    -- ~50% of clients (ClientID mod 5 = 3 or 4) get 3 portfolios
                    ELSE
                        p.PortfolioID IN (MOD(c.ClientID, 10) + 1, MOD(c.ClientID + 3, 10) + 1, MOD(c.ClientID + 6, 10) + 1)
                END
        ),
        -- Generate flows with different patterns for different client types
        flow_data AS (
            SELECT 
                ROW_NUMBER() OVER (ORDER BY d.FlowDate, cpm.ClientID, cpm.PortfolioID) as FlowID,
                d.FlowDate,
                cpm.ClientID,
                cpm.PortfolioID,
                -- Flow type: varies by client type (thresholds from config)
                CASE 
                    -- At-risk clients: high redemptions (inverted pattern)
                    WHEN cpm.ClientID IN {at_risk_ids_sql} THEN
                        CASE 
                            WHEN UNIFORM(0, 100, RANDOM()) < {at_risk_red_pct} THEN 'Redemption'
                            ELSE 'Subscription'
                        END
                    -- Standard clients: subscription/redemption/transfer split from config
                    ELSE
                        CASE 
                            WHEN UNIFORM(0, 100, RANDOM()) < {std_sub_pct} THEN 'Subscription'
                            WHEN UNIFORM(0, 100, RANDOM()) < {std_redemption_threshold} THEN 'Redemption'
                            ELSE 'Transfer'
                        END
                END as FlowType,
                -- Flow amount based on client AUM and allocation (percentages from config)
                ROUND(
                    c.AUM_with_SAM * cpm.AllocationWeight * 
                    UNIFORM({flow_pct_range[0]}, {flow_pct_range[1]}, RANDOM()) *
                    CASE 
                        -- ESG strategies getting more inflows recently (multiplier from config)
                        WHEN p.Strategy = 'ESG' AND d.FlowDate > DATEADD('month', -{esg_months}, '{max_price_date}'::DATE) 
                             AND cpm.ClientID NOT IN {at_risk_ids_sql} THEN {esg_mult}
                        -- Growth strategies volatile (range from config)
                        WHEN p.Strategy = 'Growth' THEN UNIFORM({growth_vol_range[0]}, {growth_vol_range[1]}, RANDOM())
                        ELSE 1.0
                    END,
                    -4  -- Round to nearest 10,000
                ) as FlowAmount
            FROM date_range d
            CROSS JOIN client_portfolio_map cpm
            JOIN clients c ON cpm.ClientID = c.ClientID
            JOIN portfolios p ON cpm.PortfolioID = p.PortfolioID
            WHERE 
                -- Not every client-portfolio has a flow every month (probability from config)
                UNIFORM(0, 100, RANDOM()) < {flow_prob}
                -- New clients: only have flows after their relationship start date
                AND d.FlowDate >= c.RelationshipStartDate
        )
        SELECT 
            FlowID,
            FlowDate,
            ClientID,
            PortfolioID,
            FlowType,
            CASE 
                WHEN FlowType = 'Redemption' THEN -ABS(FlowAmount)
                ELSE ABS(FlowAmount)
            END as FlowAmount,
            -- Add currency
            'USD' as Currency
        FROM flow_data
        WHERE FlowAmount != 0
    """).collect()
    
    # Verify creation
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.FACT_CLIENT_FLOWS").collect()[0]['CNT']
    log_detail(f"  Created FACT_CLIENT_FLOWS with {count} flow records")

def build_fact_fund_flows(session: Session):
    """
    Build aggregated fund flow fact table for executive KPI queries.
    Pre-aggregates FACT_CLIENT_FLOWS by portfolio/strategy for fast queries.
    
    Used by: Executive Copilot for firm-wide KPIs
    Supports: "Key performance highlights month-to-date" queries
    """
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_FUND_FLOWS AS
        WITH flow_aggregates AS (
            -- Note: PortfolioName, Strategy available via PortfolioID -> DIM_PORTFOLIO join
            SELECT 
                cf.FlowDate,
                cf.PortfolioID,
                SUM(CASE WHEN cf.FlowAmount > 0 THEN cf.FlowAmount ELSE 0 END) as GrossInflows,
                SUM(CASE WHEN cf.FlowAmount < 0 THEN ABS(cf.FlowAmount) ELSE 0 END) as GrossOutflows,
                SUM(cf.FlowAmount) as NetFlows,
                COUNT(DISTINCT cf.ClientID) as ClientCount,
                COUNT(*) as TransactionCount
            FROM {database_name}.CURATED.FACT_CLIENT_FLOWS cf
            GROUP BY cf.FlowDate, cf.PortfolioID
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY FlowDate, PortfolioID) as FundFlowID,
            FlowDate,
            PortfolioID,
            GrossInflows,
            GrossOutflows,
            NetFlows,
            ClientCount,
            TransactionCount,
            'USD' as Currency
        FROM flow_aggregates
    """).collect()
    
    # Verify creation
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.FACT_FUND_FLOWS").collect()[0]['CNT']


def build_fact_strategy_performance(session: Session):
    """
    Build aggregated strategy-level performance metrics for executive KPI queries.
    Aggregates portfolio-level returns and AUM by strategy for executive reporting.
    
    Used by: Executive Copilot for strategy performance in executive briefings
    Supports: "Top and bottom performing strategies", "Performance by strategy"
    
    Note: Calculates FIRM_AUM from actual holdings (distinct from client-reported AUM)
    """
    database_name = config.DATABASE['name']
    
    # Check if V_HOLDINGS_WITH_ESG exists with returns data
    try:
        session.sql(f"SELECT QTD_RETURN_PCT FROM {database_name}.CURATED.V_HOLDINGS_WITH_ESG LIMIT 1").collect()
    except Exception as e:
        raise RuntimeError(
            f"V_HOLDINGS_WITH_ESG missing returns columns - cannot build FACT_STRATEGY_PERFORMANCE: {e}. "
            "Run build_esg_latest_view() after build_security_returns_view() first."
        )
    
    # Build strategy performance with returns data
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_STRATEGY_PERFORMANCE AS
        WITH portfolio_performance AS (
            -- Note: PortfolioName, Strategy available via PortfolioID -> DIM_PORTFOLIO join
            SELECT 
                h.HoldingDate,
                h.PortfolioID,
                SUM(h.MarketValue_Base) as Portfolio_AUM,
                -- Weighted average returns (by market value)
                SUM(h.MarketValue_Base * COALESCE(h.MTD_RETURN_PCT, 0)) / NULLIF(SUM(h.MarketValue_Base), 0) as Weighted_MTD_Return,
                SUM(h.MarketValue_Base * COALESCE(h.QTD_RETURN_PCT, 0)) / NULLIF(SUM(h.MarketValue_Base), 0) as Weighted_QTD_Return,
                SUM(h.MarketValue_Base * COALESCE(h.YTD_RETURN_PCT, 0)) / NULLIF(SUM(h.MarketValue_Base), 0) as Weighted_YTD_Return,
                COUNT(DISTINCT h.SecurityID) as Holding_Count
            FROM {database_name}.CURATED.V_HOLDINGS_WITH_ESG h
            GROUP BY h.HoldingDate, h.PortfolioID
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY HoldingDate, PortfolioID) as StrategyPerfID,
            HoldingDate,
            PortfolioID,
            ROUND(Portfolio_AUM, 2) as Strategy_AUM,
            ROUND(Weighted_MTD_Return, 2) as Strategy_MTD_Return,
            ROUND(Weighted_QTD_Return, 2) as Strategy_QTD_Return,
            ROUND(Weighted_YTD_Return, 2) as Strategy_YTD_Return,
            Holding_Count,
            'USD' as Currency
        FROM portfolio_performance
    """).collect()
    
    # Verify creation
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.FACT_STRATEGY_PERFORMANCE").collect()[0]['CNT']
    log_detail(f"  Created FACT_STRATEGY_PERFORMANCE with {count:,} records")


def build_portfolio_benchmark_comparison_view(session: Session):
    """
    Build a pre-joined view that combines portfolio returns with their benchmark returns.
    
    This view is needed for semantic views because HOLDINGS and BENCHMARK_PERFORMANCE
    are independent fact tables with different granularities. Semantic views cannot
    combine metrics from unrelated fact tables, so we pre-join them here.
    
    Grain: One row per portfolio per date
    
    Provides:
    - Portfolio-level aggregated returns (MTD, QTD, YTD)
    - Benchmark returns for the portfolio's assigned benchmark
    - Active returns (portfolio - benchmark)
    
    Used by: SAM_ANALYST_VIEW for "portfolio vs benchmark" comparison queries
    """
    database_name = config.DATABASE['name']
    
    # Check if required source views/tables exist
    try:
        session.sql(f"SELECT 1 FROM {database_name}.CURATED.V_HOLDINGS_WITH_ESG LIMIT 1").collect()
        session.sql(f"SELECT 1 FROM {database_name}.CURATED.FACT_BENCHMARK_PERFORMANCE LIMIT 1").collect()
    except Exception as e:
        raise RuntimeError(
            f"Required tables not found for V_PORTFOLIO_BENCHMARK_COMPARISON: {e}. "
            "Ensure V_HOLDINGS_WITH_ESG and FACT_BENCHMARK_PERFORMANCE are built first."
        )
    
    session.sql(f"""
        CREATE OR REPLACE VIEW {database_name}.CURATED.V_PORTFOLIO_BENCHMARK_COMPARISON AS
        WITH portfolio_returns AS (
            -- Aggregate holding-level returns to portfolio level
            SELECT 
                h.PortfolioID,
                p.PortfolioName,
                p.Strategy,
                p.BenchmarkID,
                h.HoldingDate as PerformanceDate,
                -- Weight-average the holding returns
                SUM(h.PortfolioWeight * COALESCE(h.MTD_RETURN_PCT, 0)) / NULLIF(SUM(h.PortfolioWeight), 0) as PORTFOLIO_MTD_RETURN,
                SUM(h.PortfolioWeight * COALESCE(h.QTD_RETURN_PCT, 0)) / NULLIF(SUM(h.PortfolioWeight), 0) as PORTFOLIO_QTD_RETURN,
                SUM(h.PortfolioWeight * COALESCE(h.YTD_RETURN_PCT, 0)) / NULLIF(SUM(h.PortfolioWeight), 0) as PORTFOLIO_YTD_RETURN,
                COUNT(DISTINCT h.SecurityID) as HOLDING_COUNT,
                SUM(h.MarketValue_Base) as PORTFOLIO_AUM
            FROM {database_name}.CURATED.V_HOLDINGS_WITH_ESG h
            JOIN {database_name}.CURATED.DIM_PORTFOLIO p ON h.PortfolioID = p.PortfolioID
            GROUP BY h.PortfolioID, p.PortfolioName, p.Strategy, p.BenchmarkID, h.HoldingDate
        ),
        benchmark_returns AS (
            -- Get benchmark returns by date
            -- Note: BenchmarkName available via BenchmarkID -> DIM_BENCHMARK join
            SELECT 
                bp.BenchmarkID,
                b.BenchmarkName,
                bp.PerformanceDate,
                bp.MTD_RETURN_PCT as BENCHMARK_MTD_RETURN,
                bp.QTD_RETURN_PCT as BENCHMARK_QTD_RETURN,
                bp.YTD_RETURN_PCT as BENCHMARK_YTD_RETURN
            FROM {database_name}.CURATED.FACT_BENCHMARK_PERFORMANCE bp
            JOIN {database_name}.CURATED.DIM_BENCHMARK b ON bp.BenchmarkID = b.BenchmarkID
        )
        SELECT 
            pr.PortfolioID,
            pr.PortfolioName,
            pr.Strategy,
            pr.BenchmarkID,
            br.BenchmarkName,
            pr.PerformanceDate,
            -- Portfolio returns
            ROUND(pr.PORTFOLIO_MTD_RETURN, 2) as PORTFOLIO_MTD_RETURN,
            ROUND(pr.PORTFOLIO_QTD_RETURN, 2) as PORTFOLIO_QTD_RETURN,
            ROUND(pr.PORTFOLIO_YTD_RETURN, 2) as PORTFOLIO_YTD_RETURN,
            -- Benchmark returns
            ROUND(br.BENCHMARK_MTD_RETURN, 2) as BENCHMARK_MTD_RETURN,
            ROUND(br.BENCHMARK_QTD_RETURN, 2) as BENCHMARK_QTD_RETURN,
            ROUND(br.BENCHMARK_YTD_RETURN, 2) as BENCHMARK_YTD_RETURN,
            -- Active returns (portfolio - benchmark)
            ROUND(pr.PORTFOLIO_MTD_RETURN - COALESCE(br.BENCHMARK_MTD_RETURN, 0), 2) as ACTIVE_MTD_RETURN,
            ROUND(pr.PORTFOLIO_QTD_RETURN - COALESCE(br.BENCHMARK_QTD_RETURN, 0), 2) as ACTIVE_QTD_RETURN,
            ROUND(pr.PORTFOLIO_YTD_RETURN - COALESCE(br.BENCHMARK_YTD_RETURN, 0), 2) as ACTIVE_YTD_RETURN,
            -- Portfolio metadata
            pr.HOLDING_COUNT,
            ROUND(pr.PORTFOLIO_AUM, 2) as PORTFOLIO_AUM
        FROM portfolio_returns pr
        LEFT JOIN benchmark_returns br 
            ON pr.BenchmarkID = br.BenchmarkID 
            AND pr.PerformanceDate = br.PerformanceDate
    """).collect()
    
    log_detail("  Created V_PORTFOLIO_BENCHMARK_COMPARISON view")


def build_tax_implications_data(session: Session):
    """Build tax implications and cost basis data using config-driven SQL.
    
    Uses config from DATA_MODEL['synthetic_distributions']['global']['tax']:
    - cost_basis_multiplier_range: Range for synthetic cost basis calculation
    - holding_period_days_range: Range for holding period
    - long_term_threshold_days: Days threshold for long-term treatment
    - long_term_rate: Long-term capital gains tax rate
    - short_term_rate: Short-term capital gains tax rate
    - tax_loss_harvest_threshold_usd: Threshold for tax loss harvesting opportunity
    """
    
    database_name = config.DATABASE['name']
    
    # Get max price date as reference (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_TAX_IMPLICATIONS. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Get tax config values
    from utils.config_helpers import get_global_value
    cost_basis_range = get_global_value('tax.cost_basis_multiplier_range', (0.70, 1.30))
    holding_range = get_global_value('tax.holding_period_days_range', (30, 1095))
    lt_threshold = get_global_value('tax.long_term_threshold_days', 365)
    lt_rate = get_global_value('tax.long_term_rate', 0.20)
    st_rate = get_global_value('tax.short_term_rate', 0.37)
    tlh_threshold = get_global_value('tax.tax_loss_harvest_threshold_usd', -10000)
    
    cost_basis_sql = f"UNIFORM({cost_basis_range[0]}, {cost_basis_range[1]}, RANDOM())"
    holding_sql = f"UNIFORM({holding_range[0]}, {holding_range[1]}, RANDOM())"
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_TAX_IMPLICATIONS AS
        WITH portfolio_holdings AS (
            SELECT DISTINCT 
                h.PortfolioID,
                h.SecurityID,
                h.MarketValue_Base,
                h.PortfolioWeight
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR h
            WHERE h.HoldingDate = (SELECT MAX(HoldingDate) FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR)
        )
        SELECT 
            ph.PortfolioID,
            ph.SecurityID,
            '{max_price_date}'::DATE as TAX_DATE,
            -- Cost basis (synthetic - based on current market value with multiplier from config)
            ph.MarketValue_Base * {cost_basis_sql} as COST_BASIS_USD,
            -- Unrealized gain/loss
            ph.MarketValue_Base - (ph.MarketValue_Base * {cost_basis_sql}) as UNREALIZED_GAIN_LOSS_USD,
            -- Holding period (days from config)
            {holding_sql} as HOLDING_PERIOD_DAYS,
            -- Tax treatment (based on threshold from config)
            CASE 
                WHEN {holding_sql} > {lt_threshold} THEN 'LONG_TERM'
                ELSE 'SHORT_TERM'
            END as TAX_TREATMENT,
            -- Tax loss harvesting opportunity (threshold from config)
            CASE 
                WHEN ph.MarketValue_Base - (ph.MarketValue_Base * {cost_basis_sql}) < {tlh_threshold} THEN TRUE
                ELSE FALSE
            END as TAX_LOSS_HARVEST_OPPORTUNITY,
            -- Capital gains tax rate (rates from config)
            CASE 
                WHEN {holding_sql} > {lt_threshold} THEN {lt_rate}
                ELSE {st_rate}
            END as TAX_RATE
        FROM portfolio_holdings ph
    """).collect()
    

# =============================================================================
# MANDATE COMPLIANCE DATA (Scenario 3.2)
# =============================================================================

def build_fact_compliance_alerts(session: Session):
    """
    Create FACT_COMPLIANCE_ALERTS table for tracking mandate breaches and warnings.
    Generates alerts for ESG downgrades, concentration breaches, IPS violations, and other compliance issues.
    
    IPS Integration:
    - IPSSection: Which section of IPS was violated (e.g., 'Concentration Limits', 'Asset Allocation')
    - IPSLimitValue: The limit specified in the IPS (e.g., '5%' for max single issuer)
    - IPSCurrentValue: The actual current value that triggered the breach
    """
    database_name = config.DATABASE['name']
    
    # Create the table
    # Note: No foreign key constraints - DIM_PORTFOLIO and DIM_SECURITY are created via DataFrames
    # which don't define primary keys, so foreign key constraints would fail
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_COMPLIANCE_ALERTS (
            AlertID BIGINT IDENTITY(1,1) PRIMARY KEY,
            AlertDate DATE NOT NULL,
            PortfolioID BIGINT NOT NULL,              -- FK to DIM_PORTFOLIO (not enforced)
            SecurityID BIGINT NOT NULL,               -- FK to DIM_SECURITY (not enforced)
            AlertType VARCHAR(50) NOT NULL,           -- 'ESG_DOWNGRADE', 'CONCENTRATION_BREACH', 'IPS_VIOLATION', etc.
            AlertSeverity VARCHAR(20) NOT NULL,       -- 'WARNING', 'BREACH'
            OriginalValue VARCHAR(50),                -- e.g., 'A' (ESG grade before downgrade)
            CurrentValue VARCHAR(50),                 -- e.g., 'BBB' (current ESG grade)
            RequiresAction BOOLEAN NOT NULL,
            ActionDeadline DATE,                      -- Deadline for remediation (typically 30 days)
            AlertDescription TEXT,
            -- IPS Integration columns
            IPSSection VARCHAR(100),                  -- IPS section violated (e.g., 'Section 4.1 - Concentration Limits')
            IPSLimitValue VARCHAR(50),                -- Limit from IPS (e.g., '5%', 'BBB-')
            IPSCurrentValue VARCHAR(50),              -- Current value that triggered breach (e.g., '7.2%')
            -- Resolution tracking
            ResolvedDate DATE,                        -- When alert was resolved (NULL if active)
            ResolvedBy VARCHAR(100),                  -- PM who resolved
            ResolutionNotes TEXT
        )
    """).collect()
    

def build_fact_pre_screened_replacements(session: Session):
    """
    Create FACT_PRE_SCREENED_REPLACEMENTS table for pre-qualified replacement securities.
    Maintains a universe of securities that meet mandate requirements for quick replacement.
    """
    database_name = config.DATABASE['name']
    
    # Create the table
    # Note: No foreign key constraints - DIM_PORTFOLIO and DIM_SECURITY are created via DataFrames
    # which don't define primary keys, so foreign key constraints would fail
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_PRE_SCREENED_REPLACEMENTS (
            ReplacementID BIGINT IDENTITY(1,1) PRIMARY KEY,
            PortfolioID BIGINT NOT NULL,              -- Which portfolio/mandate (FK not enforced)
            SecurityID BIGINT NOT NULL,               -- Candidate security (FK not enforced)
            ScreenDate DATE NOT NULL,                 -- When pre-screened
            IsEligible BOOLEAN NOT NULL,              -- Passes basic criteria
            ReplacementRank INTEGER,                  -- Priority ranking (1=best, lower is better)
            -- Key criteria for mandate compliance
            ESG_Grade VARCHAR(10),                    -- Current ESG letter grade
            AI_Growth_Score DECIMAL(18,4),            -- Proprietary AI/innovation score (0-100)
            MarketCap_B_USD DECIMAL(18,4),            -- Market cap in billions
            LiquidityScore INTEGER,                   -- Liquidity rating (1-10, 10=highest)
            -- Audit trail
            EligibilityReason TEXT,                   -- Why this candidate qualifies
            ScreeningCriteria TEXT,                   -- Criteria applied during screening
            LastUpdated TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """).collect()
    

# Note: Report templates are now generated via unstructured data hydration engine
# following @unstructured-data-generation.mdc patterns. The template files are in
# content_library/global/report_templates/ and processed by hydration_engine.py

def generate_demo_compliance_alert(session: Session):
    """
    Generate the demo compliance alert for META downgrade in SAM AI & Digital Innovation portfolio.
    Uses configuration from config.SCENARIO_3_2_MANDATE_COMPLIANCE.
    """
    database_name = config.DATABASE['name']
    scenario_config = config.SCENARIO_3_2_MANDATE_COMPLIANCE
    non_compliant = scenario_config['non_compliant_holding']
    
    # Get the portfolio ID
    portfolio_name = scenario_config['portfolio']
    portfolio_id_result = session.sql(f"""
        SELECT PortfolioID 
        FROM {database_name}.CURATED.DIM_PORTFOLIO 
        WHERE PortfolioName = '{portfolio_name}'
    """).collect()
    
    if not portfolio_id_result:
        log_warning(f"  Portfolio '{portfolio_name}' not found - skipping demo alert")
        return
    
    portfolio_id = portfolio_id_result[0]['PORTFOLIOID']
    
    # Get the security ID for META (lookup by ticker)
    security_id_result = session.sql(f"""
        SELECT SecurityID 
        FROM {database_name}.CURATED.DIM_SECURITY 
        WHERE Ticker = '{non_compliant['ticker']}'
        LIMIT 1
    """).collect()
    
    if not security_id_result:
        log_warning(f"  Security {non_compliant['ticker']} not found - skipping demo alert")
        return
    
    security_id = security_id_result[0]['SECURITYID']
    
    # Generate the alert
    from datetime import datetime, timedelta
    alert_date = datetime.now().date()
    action_deadline = alert_date + timedelta(days=non_compliant['action_deadline_days'])
    
    session.sql(f"""
        INSERT INTO {database_name}.CURATED.FACT_COMPLIANCE_ALERTS (
            AlertDate, PortfolioID, SecurityID, AlertType, AlertSeverity,
            OriginalValue, CurrentValue, RequiresAction, ActionDeadline, AlertDescription
        )
        VALUES (
            '{alert_date}',
            {portfolio_id},
            {security_id},
            '{non_compliant['issue']}',
            'BREACH',
            '{non_compliant['original_esg_grade']}',
            '{non_compliant['downgraded_esg_grade']}',
            TRUE,
            '{action_deadline}',
            '{non_compliant['reason']}'
        )
    """).collect()
    

def generate_concentration_breach_alerts(session: Session):
    """
    Generate concentration breach alerts by scanning current positions
    against the 7.0% breach threshold and 6.5% warning threshold.
    Creates historical alerts for demo purposes (spread over last 30 days).
    
    Uses batched writes for efficiency per performance-io.mdc.
    """
    from datetime import datetime, timedelta
    from utils import snowflake as snowflake_io_utils
    database_name = config.DATABASE['name']
    
    # Ensure database context is set (required for temp stage creation in complex queries)
    session.sql(f"USE DATABASE {database_name}").collect()
    session.sql(f"USE SCHEMA {config.DATABASE['schemas']['curated']}").collect()
    
    # Clean up any stale Snowpark temp stages from previous failed runs
    try:
        stages = session.sql("SHOW STAGES LIKE 'SNOWPARK_TEMP_STAGE_%'").collect()
        for stage in stages:
            stage_name = stage['name']
            session.sql(f"DROP STAGE IF EXISTS {stage_name}").collect()
    except:
        pass  # Ignore errors - stages may not exist
    
    # Query positions that exceed concentration thresholds from IPS constraints
    # Fall back to global config thresholds if IPS not available
    global_breach_threshold = config.COMPLIANCE_RULES['concentration']['max_single_issuer']  # 0.07 = 7%
    global_warning_threshold = config.COMPLIANCE_RULES['concentration']['warning_threshold']  # 0.065 = 6.5%
    
    # Get positions exceeding warning threshold from latest holdings, joined with IPS limits
    concentration_issues = session.sql(f"""
        WITH latest_holdings AS (
            SELECT 
                h.PortfolioID,
                h.SecurityID,
                h.PortfolioWeight,
                h.MarketValue_Base,
                p.PortfolioName,
                s.Ticker,
                s.Description,
                ROW_NUMBER() OVER (PARTITION BY h.PortfolioID, h.SecurityID ORDER BY h.HoldingDate DESC) as rn
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR h
            JOIN {database_name}.CURATED.DIM_PORTFOLIO p ON h.PortfolioID = p.PortfolioID
            JOIN {database_name}.CURATED.DIM_SECURITY s ON h.SecurityID = s.SecurityID
            WHERE h.PortfolioWeight >= {global_warning_threshold * 0.9}
        )
        SELECT 
            lh.PortfolioID,
            lh.SecurityID,
            lh.PortfolioWeight,
            lh.MarketValue_Base,
            lh.PortfolioName,
            lh.Ticker,
            lh.Description,
            COALESCE(ips.MaxSingleIssuerPct / 100.0, {global_breach_threshold}) as IPS_BREACH_THRESHOLD,
            COALESCE(ips.MaxSingleIssuerPct / 100.0 * 0.95, {global_warning_threshold}) as IPS_WARNING_THRESHOLD,
            ips.RiskProfile as IPS_RISK_PROFILE
        FROM latest_holdings lh
        LEFT JOIN {database_name}.CURATED.DIM_PORTFOLIO_IPS ips ON lh.PortfolioID = ips.PortfolioID
        WHERE lh.rn = 1
          AND lh.PortfolioWeight >= COALESCE(ips.MaxSingleIssuerPct / 100.0 * 0.95, {global_warning_threshold})
        ORDER BY lh.PortfolioWeight DESC
    """).collect()
    
    if not concentration_issues:
        log_detail("  No concentration issues found - skipping breach alerts")
        return
    
    # Generate alerts with dates spread over last 30 days for demo realism
    today = datetime.now().date()
    rows = []
    
    # PM names for resolved breaches (demo data)
    pm_names = ['Anna Chen', 'David Martinez', 'Sarah Thompson', 'Michael Roberts']
    
    for i, issue in enumerate(concentration_issues):
        weight_pct = float(issue['PORTFOLIOWEIGHT']) * 100
        breach_threshold = float(issue['IPS_BREACH_THRESHOLD'])
        warning_threshold = float(issue['IPS_WARNING_THRESHOLD'])
        is_breach = issue['PORTFOLIOWEIGHT'] >= breach_threshold
        
        # Spread alert dates across last 30 days (older alerts for higher concentrations)
        days_ago = min(28, 5 + i * 3)  # First alerts 5-28 days ago
        alert_date = today - timedelta(days=days_ago)
        action_deadline = alert_date + timedelta(days=30)
        
        severity = 'BREACH' if is_breach else 'WARNING'
        threshold_pct = breach_threshold * 100 if is_breach else warning_threshold * 100
        
        risk_profile = issue['IPS_RISK_PROFILE'] or 'N/A'
        ips_source = f" (IPS {risk_profile} profile)" if risk_profile != 'N/A' else ""
        
        description = (
            f"{issue['TICKER']} ({issue['DESCRIPTION']}) position at {weight_pct:.1f}% "
            f"exceeds {threshold_pct:.1f}% {severity.lower()} threshold{ips_source} in {issue['PORTFOLIONAME']}. "
            f"Market value: ${issue['MARKETVALUE_BASE']:,.0f}"
        )
        
        # Determine remediation status for demo purposes:
        # - Older WARNING alerts (>20 days old): mark as resolved
        # - Some older BREACH alerts (>25 days old, every other one): mark as resolved
        # - Recent alerts: leave unresolved to show active breaches
        resolved_date = None
        resolved_by = None
        resolution_notes = None
        
        if not is_breach and days_ago > 20:
            # Older warnings - mark as resolved (position naturally decreased)
            resolved_date = alert_date + timedelta(days=10)
            resolved_by = pm_names[i % len(pm_names)]
            resolution_notes = f"Position weight decreased to below warning threshold through market movement and natural rebalancing."
        elif is_breach and days_ago > 25 and i % 2 == 0:
            # Some older breaches - mark as resolved (PM took action)
            resolved_date = alert_date + timedelta(days=15)
            resolved_by = pm_names[i % len(pm_names)]
            resolution_notes = f"Position reduced to {threshold_pct - 0.5:.1f}% per remediation plan. Executed via TWAP over 3 trading days to minimise market impact."
        
        rows.append({
            'AlertDate': alert_date,
            'PortfolioID': issue['PORTFOLIOID'],
            'SecurityID': issue['SECURITYID'],
            'AlertType': 'CONCENTRATION_BREACH' if is_breach else 'CONCENTRATION_WARNING',
            'AlertSeverity': severity,
            'OriginalValue': f"{threshold_pct:.1f}%",
            'CurrentValue': f"{weight_pct:.1f}%",
            'RequiresAction': is_breach,
            'ActionDeadline': action_deadline if is_breach else None,
            'AlertDescription': description,
            'IPSSection': 'Section 4.1 - Concentration Limits' if risk_profile != 'N/A' else None,
            'IPSLimitValue': f"{breach_threshold * 100:.0f}%" if risk_profile != 'N/A' else None,
            'IPSCurrentValue': f"{weight_pct:.1f}%",
            'ResolvedDate': resolved_date,
            'ResolvedBy': resolved_by,
            'ResolutionNotes': resolution_notes
        })
    
    # Batch insert all alerts using write_pandas
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)
        df.columns = [col.upper() for col in df.columns]
        session.write_pandas(
            df, 'FACT_COMPLIANCE_ALERTS',
            database=database_name, schema='CURATED',
            quote_identifiers=False, overwrite=False, auto_create_table=False
        )
        breach_count = sum(1 for r in rows if r['AlertSeverity'] == 'BREACH')
        warning_count = sum(1 for r in rows if r['AlertSeverity'] == 'WARNING')
        resolved_count = sum(1 for r in rows if r['ResolvedDate'] is not None)
        active_count = len(rows) - resolved_count
        log_detail(f"  Generated {len(rows)} concentration alerts ({breach_count} breaches, {warning_count} warnings, {resolved_count} resolved, {active_count} active)")


def generate_demo_pre_screened_replacements(session: Session):
    """
    Generate pre-screened replacement candidates for the demo scenario.
    Uses configuration from config.SCENARIO_3_2_MANDATE_COMPLIANCE.
    
    Uses batched lookups and writes for efficiency (no per-row SELECTs or INSERTs).
    """
    database_name = config.DATABASE['name']
    scenario_config = config.SCENARIO_3_2_MANDATE_COMPLIANCE
    
    # Get the portfolio ID
    portfolio_name = scenario_config['portfolio']
    portfolio_id_result = session.sql(f"""
        SELECT PortfolioID 
        FROM {database_name}.CURATED.DIM_PORTFOLIO 
        WHERE PortfolioName = '{portfolio_name}'
    """).collect()
    
    if not portfolio_id_result:
        log_warning(f"  Portfolio '{portfolio_name}' not found - skipping pre-screened replacements")
        return
    
    portfolio_id = portfolio_id_result[0]['PORTFOLIOID']
    
    # Batch fetch all SecurityIDs for configured replacements in ONE query
    replacements = scenario_config['pre_screened_replacements']
    tickers = [r['ticker'] for r in replacements]
    ticker_list = ", ".join(f"'{t}'" for t in tickers)
    
    sec_rows = session.sql(f"""
        SELECT SecurityID, Ticker
        FROM {database_name}.CURATED.DIM_SECURITY
        WHERE Ticker IN ({ticker_list})
    """).collect()
    security_map = {row['TICKER']: row['SECURITYID'] for row in sec_rows}
    
    # Build all replacement rows locally
    from datetime import datetime
    screen_date = datetime.now().date()
    screening_criteria = (
        f"AI Growth Score >= {scenario_config['mandate_requirements']['ai_growth_threshold']}, "
        f"ESG Grade >= {scenario_config['mandate_requirements']['min_esg_grade']}, "
        f"Market Cap >= ${scenario_config['mandate_requirements']['min_market_cap_b']}B, "
        f"Liquidity Score >= {scenario_config['mandate_requirements']['min_liquidity_score']}"
    )
    
    rows = []
    for replacement in replacements:
        # Look up SecurityID from batched result (by ticker)
        security_id = security_map.get(replacement['ticker'])
        
        if not security_id:
            log_warning(f"  Security {replacement['ticker']} not found - skipping")
            continue
        
        rows.append({
            'PortfolioID': portfolio_id,
            'SecurityID': security_id,
            'ScreenDate': screen_date,
            'IsEligible': True,
            'ReplacementRank': replacement['rank'],
            'ESG_Grade': replacement['esg_grade'],
            'AI_Growth_Score': replacement['ai_growth_score'],
            'MarketCap_B_USD': replacement['market_cap_b'],
            'LiquidityScore': replacement['liquidity_score'],
            'EligibilityReason': replacement['rationale'],
            'ScreeningCriteria': screening_criteria,
        })
    
    # Write all rows in a single batch
    if rows:
        import pandas as pd
        from utils.snowflake import cleanup_temp_stages
        cleanup_temp_stages(session)
        df = pd.DataFrame(rows)
        df.columns = [col.upper() for col in df.columns]
        session.write_pandas(
            df, 'FACT_PRE_SCREENED_REPLACEMENTS',
            database=database_name, schema='CURATED',
            quote_identifiers=False, overwrite=True, auto_create_table=True
        )
        

# Report template functions removed - now handled by unstructured data hydration engine
# Templates are in content_library/global/report_templates/ following @unstructured-data-generation.mdc patterns

# =============================================================================
# MIDDLE OFFICE TABLES
# =============================================================================

def build_dim_counterparty(session: Session):
    """Build counterparty dimension with settlement characteristics.
    
    Uses batched write_pandas for efficiency (no row-by-row inserts).
    Explicit CounterpartyID 1..20 preserves downstream assumptions in FACT_TRADE_SETTLEMENT.
    """
    from utils import snowflake as snowflake_io_utils
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Define realistic counterparties with settlement profiles
    # Build as list of dicts with explicit IDs (1..N) for downstream consistency
    counterparties = [
        {'CounterpartyID': 1, 'CounterpartyName': 'Goldman Sachs', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.02, 'AverageSettlementTime': 1.8, 'RiskRating': 'A'},
        {'CounterpartyID': 2, 'CounterpartyName': 'Morgan Stanley', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.015, 'AverageSettlementTime': 1.9, 'RiskRating': 'A'},
        {'CounterpartyID': 3, 'CounterpartyName': 'JP Morgan', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.01, 'AverageSettlementTime': 1.7, 'RiskRating': 'AA'},
        {'CounterpartyID': 4, 'CounterpartyName': 'Barclays', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.025, 'AverageSettlementTime': 2.1, 'RiskRating': 'A'},
        {'CounterpartyID': 5, 'CounterpartyName': 'Credit Suisse', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.03, 'AverageSettlementTime': 2.3, 'RiskRating': 'BBB'},
        {'CounterpartyID': 6, 'CounterpartyName': 'Deutsche Bank', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.028, 'AverageSettlementTime': 2.2, 'RiskRating': 'BBB'},
        {'CounterpartyID': 7, 'CounterpartyName': 'BNP Paribas', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.018, 'AverageSettlementTime': 1.9, 'RiskRating': 'A'},
        {'CounterpartyID': 8, 'CounterpartyName': 'UBS', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.012, 'AverageSettlementTime': 1.8, 'RiskRating': 'AA'},
        {'CounterpartyID': 9, 'CounterpartyName': 'Citi', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.015, 'AverageSettlementTime': 1.9, 'RiskRating': 'A'},
        {'CounterpartyID': 10, 'CounterpartyName': 'Bank of America', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.013, 'AverageSettlementTime': 1.8, 'RiskRating': 'A'},
        {'CounterpartyID': 11, 'CounterpartyName': 'BNY Mellon', 'CounterpartyType': 'Custodian', 'HistoricalFailRate': 0.005, 'AverageSettlementTime': 1.5, 'RiskRating': 'AA'},
        {'CounterpartyID': 12, 'CounterpartyName': 'State Street', 'CounterpartyType': 'Custodian', 'HistoricalFailRate': 0.005, 'AverageSettlementTime': 1.5, 'RiskRating': 'AA'},
        {'CounterpartyID': 13, 'CounterpartyName': 'JPM Custody', 'CounterpartyType': 'Custodian', 'HistoricalFailRate': 0.004, 'AverageSettlementTime': 1.5, 'RiskRating': 'AA'},
        {'CounterpartyID': 14, 'CounterpartyName': 'Northern Trust', 'CounterpartyType': 'Custodian', 'HistoricalFailRate': 0.006, 'AverageSettlementTime': 1.6, 'RiskRating': 'AA'},
        {'CounterpartyID': 15, 'CounterpartyName': 'HSBC Custody', 'CounterpartyType': 'Custodian', 'HistoricalFailRate': 0.007, 'AverageSettlementTime': 1.7, 'RiskRating': 'A'},
        {'CounterpartyID': 16, 'CounterpartyName': 'Prime Broker A', 'CounterpartyType': 'Prime', 'HistoricalFailRate': 0.02, 'AverageSettlementTime': 1.9, 'RiskRating': 'A'},
        {'CounterpartyID': 17, 'CounterpartyName': 'Prime Broker B', 'CounterpartyType': 'Prime', 'HistoricalFailRate': 0.022, 'AverageSettlementTime': 2.0, 'RiskRating': 'A'},
        {'CounterpartyID': 18, 'CounterpartyName': 'Clearing Firm A', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.015, 'AverageSettlementTime': 1.8, 'RiskRating': 'A'},
        {'CounterpartyID': 19, 'CounterpartyName': 'Clearing Firm B', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.017, 'AverageSettlementTime': 1.9, 'RiskRating': 'A'},
        {'CounterpartyID': 20, 'CounterpartyName': 'Market Maker A', 'CounterpartyType': 'Broker', 'HistoricalFailRate': 0.02, 'AverageSettlementTime': 2.0, 'RiskRating': 'BBB'},
    ]
    
    # Write using native write_pandas
    import pandas as pd
    from utils.snowflake import cleanup_temp_stages
    cleanup_temp_stages(session)
    df = pd.DataFrame(counterparties)
    df.columns = [col.upper() for col in df.columns]
    session.write_pandas(
        df, 'DIM_COUNTERPARTY',
        database=database_name, schema='CURATED',
        quote_identifiers=False, overwrite=True, auto_create_table=True
    )


def build_dim_custodian(session: Session):
    """Build custodian dimension.
    
    Explicit CustodianID 1..8 preserves downstream assumptions in FACT_TRADE_SETTLEMENT.
    """
    database_name = config.DATABASE['name']
    
    # Define major custodians as list of dicts with explicit IDs (1..N)
    custodians = [
        {'CustodianID': 1, 'CustodianName': 'BNY Mellon', 'CustodianType': 'Global Custodian', 'CoverageRegions': 'Americas, EMEA, APAC', 'ServiceLevel': 'Premium'},
        {'CustodianID': 2, 'CustodianName': 'State Street', 'CustodianType': 'Global Custodian', 'CoverageRegions': 'Americas, EMEA, APAC', 'ServiceLevel': 'Premium'},
        {'CustodianID': 3, 'CustodianName': 'JPMorgan Custody', 'CustodianType': 'Global Custodian', 'CoverageRegions': 'Americas, EMEA, APAC', 'ServiceLevel': 'Premium'},
        {'CustodianID': 4, 'CustodianName': 'Northern Trust', 'CustodianType': 'Regional Custodian', 'CoverageRegions': 'Americas, EMEA', 'ServiceLevel': 'Standard'},
        {'CustodianID': 5, 'CustodianName': 'HSBC Custody', 'CustodianType': 'Global Custodian', 'CoverageRegions': 'EMEA, APAC', 'ServiceLevel': 'Standard'},
        {'CustodianID': 6, 'CustodianName': 'Citi Custody', 'CustodianType': 'Global Custodian', 'CoverageRegions': 'Americas, EMEA, APAC', 'ServiceLevel': 'Premium'},
        {'CustodianID': 7, 'CustodianName': 'Deutsche Bank Custody', 'CustodianType': 'Regional Custodian', 'CoverageRegions': 'EMEA', 'ServiceLevel': 'Standard'},
        {'CustodianID': 8, 'CustodianName': 'BNP Paribas Securities Services', 'CustodianType': 'Regional Custodian', 'CoverageRegions': 'EMEA', 'ServiceLevel': 'Standard'},
    ]
    
    # Write using native write_pandas
    import pandas as pd
    from utils.snowflake import cleanup_temp_stages
    cleanup_temp_stages(session)
    df = pd.DataFrame(custodians)
    df.columns = [col.upper() for col in df.columns]
    session.write_pandas(
        df, 'DIM_CUSTODIAN',
        database=database_name, schema='CURATED',
        quote_identifiers=False, overwrite=True, auto_create_table=True
    )


def build_fact_trade_settlement(session: Session, test_mode: bool = False):
    """Build trade settlement fact table with status tracking.
    
    Uses default settlement days from DATA_MODEL['synthetic_distributions']['country_groups']['_default']['settlement_days'].
    Includes recent window data (last 10 days relative to max_price_date) for demo scenarios.
    """
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Get max_price_date for recent window generation
    max_price_date = get_max_price_date(session)
    
    # Get default settlement days from config
    from utils.config_helpers import get_country_value
    default_settlement_days = get_country_value('US', 'settlement_days') or 2
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    # Includes both historical settlements and recent window settlements for demo
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_TRADE_SETTLEMENT AS
        WITH trade_data AS (
            SELECT 
                t.TransactionID,
                t.TransactionDate,
                DATEADD(day, {default_settlement_days}, t.TransactionDate) as SettlementDate,
                t.PortfolioID,
                t.SecurityID,
                ABS(t.GrossAmount_Local) as SettlementValue,
                t.Currency,
                -- Assign counterparty and custodian with some randomness
                MOD(ABS(HASH(t.TransactionID)), 20) + 1 as CounterpartyID,
                MOD(ABS(HASH(t.TransactionID * 2)), 8) + 1 as CustodianID,
                -- Generate failure flag (2-5% failure rate)
                UNIFORM(0, 100, RANDOM()) as failure_chance
            FROM {database_name}.CURATED.FACT_TRANSACTION t
            WHERE t.TransactionType IN ('BUY', 'SELL')
        ),
        historical_settlements AS (
            SELECT 
                TransactionID as TradeID,
                TransactionDate as TradeDate,
                SettlementDate,
                CASE 
                    WHEN failure_chance <= 3 THEN 'Failed'
                    WHEN failure_chance <= 5 THEN 'Pending'
                    ELSE 'Settled'
                END as Status,
                PortfolioID,
                SecurityID,
                CounterpartyID,
                CustodianID,
                SettlementValue,
                Currency,
                CASE 
                    WHEN failure_chance <= 1 THEN 'SSI mismatch'
                    WHEN failure_chance <= 2 THEN 'Insufficient shares'
                    WHEN failure_chance <= 3 THEN 'Counterparty system issue'
                    ELSE NULL
                END as FailureReason,
                CASE 
                    WHEN failure_chance <= 3 THEN DATEADD(day, UNIFORM(1, 3, RANDOM()), SettlementDate)
                    ELSE NULL
                END as ResolvedDate
            FROM trade_data
        ),
        -- Recent window: Generate settlements for last 10 days relative to max_price_date
        -- This ensures demo queries for "today" or "past N days" find data
        recent_dates AS (
            SELECT DATEADD(day, -seq4(), '{max_price_date}'::DATE) as recent_date
            FROM TABLE(GENERATOR(rowcount => 10))
            WHERE DAYOFWEEK(DATEADD(day, -seq4(), '{max_price_date}'::DATE)) BETWEEN 2 AND 6
        ),
        recent_securities AS (
            SELECT DISTINCT SecurityID, PortfolioID
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR
            WHERE HoldingDate = (SELECT MAX(HoldingDate) FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR)
        ),
        recent_window_settlements AS (
            SELECT 
                -1 * (ROW_NUMBER() OVER (ORDER BY rd.recent_date, rs.SecurityID)) as TradeID,
                DATEADD(day, -{default_settlement_days}, rd.recent_date) as TradeDate,
                rd.recent_date as SettlementDate,
                -- Higher failure/pending rate for demo visibility (15% failed, 10% pending)
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) <= 15 THEN 'Failed'
                    WHEN UNIFORM(0, 100, RANDOM()) <= 25 THEN 'Pending'
                    ELSE 'Settled'
                END as Status,
                rs.PortfolioID,
                rs.SecurityID,
                MOD(ABS(HASH(rs.SecurityID + DATEDIFF(day, '2020-01-01', rd.recent_date))), 20) + 1 as CounterpartyID,
                MOD(ABS(HASH(rs.SecurityID * 2)), 8) + 1 as CustodianID,
                UNIFORM(50000, 500000, RANDOM()) as SettlementValue,
                'USD' as Currency,
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) <= 5 THEN 'SSI mismatch'
                    WHEN UNIFORM(0, 100, RANDOM()) <= 10 THEN 'Insufficient shares'
                    WHEN UNIFORM(0, 100, RANDOM()) <= 15 THEN 'Counterparty system issue'
                    ELSE NULL
                END as FailureReason,
                NULL as ResolvedDate
            FROM recent_dates rd
            CROSS JOIN (SELECT * FROM recent_securities ORDER BY RANDOM() LIMIT 5) rs
        ),
        all_settlements AS (
            SELECT * FROM historical_settlements
            UNION ALL
            SELECT * FROM recent_window_settlements
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY SettlementDate, TradeID) as SettlementID,
            TradeID,
            TradeDate,
            SettlementDate,
            Status,
            PortfolioID,
            SecurityID,
            CounterpartyID,
            CustodianID,
            SettlementValue,
            Currency,
            FailureReason,
            ResolvedDate
        FROM all_settlements
    """).collect()


def build_fact_reconciliation(session: Session, test_mode: bool = False):
    """Build reconciliation fact table tracking breaks and resolutions.
    
    Includes recent window data (last 10 days relative to max_price_date) for demo scenarios.
    """
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Get max_price_date for recent window generation
    max_price_date = get_max_price_date(session)
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    # Includes both historical breaks and recent window breaks for demo
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_RECONCILIATION AS
        WITH position_data AS (
            SELECT 
                p.HoldingDate,
                p.PortfolioID,
                p.SecurityID,
                p.MarketValue_Base,
                p.Quantity,
                -- Generate break flag (1-2% break rate)
                UNIFORM(0, 100, RANDOM()) as break_chance,
                UNIFORM(0, 3, RANDOM()) as break_type_flag
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR p
        ),
        historical_breaks AS (
            SELECT 
                HoldingDate as ReconciliationDate,
                PortfolioID,
                SecurityID,
                CASE 
                    WHEN break_type_flag < 1 THEN 'Position'
                    WHEN break_type_flag < 2 THEN 'Cash'
                    ELSE 'Price'
                END as BreakType,
                MarketValue_Base as InternalValue,
                -- Generate custodian value with small difference
                MarketValue_Base * (1 + UNIFORM(-0.05, 0.05, RANDOM())) as CustodianValue,
                CASE 
                    WHEN break_chance <= 0.5 THEN 'Open'
                    WHEN break_chance <= 1.5 THEN 'Investigating'
                    ELSE 'Resolved'
                END as Status,
                CASE 
                    WHEN break_chance > 0.5 THEN DATEADD(day, UNIFORM(1, 5, RANDOM()), HoldingDate)
                    ELSE NULL
                END as ResolutionDate,
                CASE 
                    WHEN break_chance > 1.5 THEN 'Timing difference - resolved through custodian confirmation'
                    WHEN break_chance > 0.5 THEN 'Under investigation - awaiting custodian response'
                    ELSE NULL
                END as ResolutionNotes
            FROM position_data
            WHERE break_chance <= 2
        ),
        -- Recent window: Generate daily reconciliation breaks for last 10 days relative to max_price_date
        -- This ensures demo queries for "today's breaks" find data
        recent_dates AS (
            SELECT DATEADD(day, -seq4(), '{max_price_date}'::DATE) as recent_date
            FROM TABLE(GENERATOR(rowcount => 10))
            WHERE DAYOFWEEK(DATEADD(day, -seq4(), '{max_price_date}'::DATE)) BETWEEN 2 AND 6
        ),
        recent_portfolios AS (
            SELECT DISTINCT PortfolioID FROM {database_name}.CURATED.DIM_PORTFOLIO
        ),
        recent_securities AS (
            SELECT DISTINCT SecurityID, PortfolioID, MarketValue_Base
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR
            WHERE HoldingDate = (SELECT MAX(HoldingDate) FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR)
        ),
        recent_window_breaks AS (
            SELECT 
                rd.recent_date as ReconciliationDate,
                rs.PortfolioID,
                rs.SecurityID,
                -- Distribute break types evenly
                CASE 
                    WHEN MOD(ABS(HASH(rs.SecurityID + DATEDIFF(day, '2020-01-01', rd.recent_date))), 3) = 0 THEN 'Position'
                    WHEN MOD(ABS(HASH(rs.SecurityID + DATEDIFF(day, '2020-01-01', rd.recent_date))), 3) = 1 THEN 'Cash'
                    ELSE 'Price'
                END as BreakType,
                rs.MarketValue_Base as InternalValue,
                rs.MarketValue_Base * (1 + UNIFORM(-0.03, 0.03, RANDOM())) as CustodianValue,
                -- Mix of statuses for demo: 40% Open, 35% Investigating, 25% Resolved
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) <= 40 THEN 'Open'
                    WHEN UNIFORM(0, 100, RANDOM()) <= 75 THEN 'Investigating'
                    ELSE 'Resolved'
                END as Status,
                NULL as ResolutionDate,
                NULL as ResolutionNotes
            FROM recent_dates rd
            CROSS JOIN (SELECT * FROM recent_securities ORDER BY RANDOM() LIMIT 3) rs
        ),
        all_breaks AS (
            SELECT ReconciliationDate, PortfolioID, SecurityID, BreakType, InternalValue, CustodianValue, Status, ResolutionDate, ResolutionNotes
            FROM historical_breaks
            UNION ALL
            SELECT ReconciliationDate, PortfolioID, SecurityID, BreakType, InternalValue, CustodianValue, Status, ResolutionDate, ResolutionNotes
            FROM recent_window_breaks
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY ReconciliationDate, PortfolioID, SecurityID) as ReconciliationID,
            ReconciliationDate,
            PortfolioID,
            SecurityID,
            BreakType,
            InternalValue,
            CustodianValue,
            ABS(InternalValue - CustodianValue) as Difference,
            Status,
            ResolutionDate,
            ResolutionNotes
        FROM all_breaks
    """).collect()


def build_fact_nav_calculation(session: Session, test_mode: bool = False):
    """Build NAV calculation fact table.
    
    Includes recent window data (last 10 days relative to max_price_date) for demo scenarios.
    """
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Get max_price_date for recent window generation
    max_price_date = get_max_price_date(session)
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    # Includes both historical NAV calculations and recent window for demo
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_NAV_CALCULATION AS
        WITH daily_positions AS (
            SELECT 
                HoldingDate,
                PortfolioID,
                SUM(MarketValue_Base) as TotalAssets
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR
            GROUP BY HoldingDate, PortfolioID
        ),
        historical_nav AS (
            SELECT 
                HoldingDate as CalculationDate,
                PortfolioID,
                TotalAssets,
                TotalAssets * 0.001 as TotalLiabilities,
                TotalAssets * 0.999 as NetAssets,
                100000000.00 as SharesOutstanding,
                (TotalAssets * 0.999) / 100000000.00 as NAVperShare,
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) <= 1 THEN 'Pending Review'
                    ELSE 'Calculated'
                END as CalculationStatus,
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) <= 0.5 THEN 'NAV change >2% from prior day'
                    WHEN UNIFORM(0, 100, RANDOM()) <= 1 THEN 'Missing prices detected'
                    ELSE NULL
                END as AnomaliesDetected,
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) <= 1 THEN 'Pending'
                    ELSE 'Approved'
                END as ApprovalStatus,
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) > 1 THEN 'Operations Manager'
                    ELSE NULL
                END as ApprovedBy,
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) > 1 THEN DATEADD(hour, 2, HoldingDate)
                    ELSE NULL
                END as ApprovalTimestamp
            FROM daily_positions
        ),
        -- Recent window: Generate daily NAV calculations for last 10 days relative to max_price_date
        -- This ensures demo queries for "today's NAV" find data
        recent_dates AS (
            SELECT DATEADD(day, -seq4(), '{max_price_date}'::DATE) as recent_date
            FROM TABLE(GENERATOR(rowcount => 10))
            WHERE DAYOFWEEK(DATEADD(day, -seq4(), '{max_price_date}'::DATE)) BETWEEN 2 AND 6
        ),
        latest_portfolio_values AS (
            SELECT PortfolioID, TotalAssets
            FROM (
                SELECT PortfolioID, SUM(MarketValue_Base) as TotalAssets
                FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR
                WHERE HoldingDate = (SELECT MAX(HoldingDate) FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR)
                GROUP BY PortfolioID
            )
        ),
        recent_window_nav AS (
            SELECT 
                rd.recent_date as CalculationDate,
                lpv.PortfolioID,
                -- Add small daily variation to assets (-0.5% to +0.5%)
                lpv.TotalAssets * (1 + UNIFORM(-0.005, 0.005, RANDOM())) as TotalAssets,
                lpv.TotalAssets * 0.001 as TotalLiabilities,
                lpv.TotalAssets * 0.999 as NetAssets,
                100000000.00 as SharesOutstanding,
                (lpv.TotalAssets * 0.999) / 100000000.00 as NAVperShare,
                -- Most recent NAVs are calculated and approved
                'Calculated' as CalculationStatus,
                -- Small chance of anomaly for demo interest (5%)
                CASE 
                    WHEN UNIFORM(0, 100, RANDOM()) <= 5 THEN 'Zero NAV Movement Anomaly'
                    ELSE NULL
                END as AnomaliesDetected,
                'Approved' as ApprovalStatus,
                'Operations Manager' as ApprovedBy,
                DATEADD(hour, 18, rd.recent_date) as ApprovalTimestamp
            FROM recent_dates rd
            CROSS JOIN latest_portfolio_values lpv
        ),
        all_nav AS (
            SELECT CalculationDate, PortfolioID, TotalAssets, TotalLiabilities, NetAssets, SharesOutstanding, NAVperShare, CalculationStatus, AnomaliesDetected, ApprovalStatus, ApprovedBy, ApprovalTimestamp
            FROM historical_nav
            UNION ALL
            SELECT CalculationDate, PortfolioID, TotalAssets, TotalLiabilities, NetAssets, SharesOutstanding, NAVperShare, CalculationStatus, AnomaliesDetected, ApprovalStatus, ApprovedBy, ApprovalTimestamp
            FROM recent_window_nav
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY CalculationDate, PortfolioID) as NAVID,
            CalculationDate,
            PortfolioID,
            NAVperShare,
            TotalAssets,
            TotalLiabilities,
            NetAssets,
            SharesOutstanding,
            CalculationStatus,
            AnomaliesDetected,
            ApprovalStatus,
            ApprovedBy,
            ApprovalTimestamp
        FROM all_nav
    """).collect()


def build_fact_nav_components(session: Session, test_mode: bool = False):
    """Build NAV component detail table."""
    database_name = config.DATABASE['name']
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_NAV_COMPONENTS AS
        SELECT 
            ROW_NUMBER() OVER (ORDER BY n.NAVID, p.SecurityID) as ComponentID,
            n.NAVID,
            'Securities' as ComponentType,
            p.MarketValue_Base as ComponentValue,
            p.SecurityID,
            p.Quantity,
            p.MarketValue_Base / NULLIF(p.Quantity, 0) as Price,
            NULL as AccrualAmount
        FROM {database_name}.CURATED.FACT_NAV_CALCULATION n
        JOIN {database_name}.CURATED.FACT_POSITION_DAILY_ABOR p
            ON n.CalculationDate = p.HoldingDate
            AND n.PortfolioID = p.PortfolioID
    """).collect()



def build_fact_corporate_actions(session: Session, test_mode: bool = False):
    """Build corporate actions fact table using real dividend data and synthetic splits/mergers.
    
    Dividends are sourced from real SEC filings via MARKET_DATA.FACT_DIVIDENDS.
    Splits and mergers remain synthetic for demo purposes.
    
    Uses config from DATA_MODEL['synthetic_distributions']['global']['corporate_actions']:
    - action_type_weights: Probability weights for non-dividend action types
    - ex_date_offset_days, record_date_offset_days, payment_date_offset_days: Date offsets
    
    Includes pending corporate actions with ExDates in forward window from max_price_date for demo.
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    random.seed(config.RNG_SEED)
    
    # Get max_price_date for forward window generation
    max_price_date = get_max_price_date(session)
    
    # Get corporate action config values
    from utils.config_helpers import get_global_value
    dividend_range = get_global_value('corporate_actions.dividend_range_usd', (0.50, 2.00))
    ex_offset = get_global_value('corporate_actions.ex_date_offset_days', 15)
    record_offset = get_global_value('corporate_actions.record_date_offset_days', 16)
    payment_offset = get_global_value('corporate_actions.payment_date_offset_days', 30)
    
    dividend_sql = f"UNIFORM({dividend_range[0]}, {dividend_range[1]}, RANDOM())"
    
    # Check if real dividend data exists
    dividend_count = session.sql(f"""
        SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_DIVIDENDS
    """).collect()[0]['CNT']
    
    if dividend_count > 0:
        log_detail(f"  Using {dividend_count:,} real dividend records from SEC 8-K filings")
        
        # Build with real dividends + synthetic splits/mergers
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_CORPORATE_ACTIONS AS
            WITH 
            -- Real dividends from SEC 8-K filings (with AI_EXTRACT parsed dates)
            real_dividends AS (
                SELECT 
                    d.SecurityID,
                    d.IssuerID,
                    'Dividend' as ActionType,
                    d.DECLARATION_DATE as AnnouncementDate,
                    d.EX_DATE as ExDate,
                    d.RECORD_DATE as RecordDate,
                    d.PAYMENT_DATE as PaymentDate,
                    d.DIVIDEND_TYPE || ' dividend: $' || ROUND(d.DIVIDEND_PER_SHARE, 2) || ' per share' as ActionDetails,
                    d.DIVIDEND_PER_SHARE as ImpactValue,
                    CASE 
                        WHEN d.EX_DATE <= '{max_price_date}'::DATE THEN 'Processed'
                        ELSE 'Pending'
                    END as ProcessingStatus,
                    UNIFORM(1, 10, RANDOM()) as PortfoliosAffected
                FROM {database_name}.{market_data_schema}.FACT_DIVIDENDS d
                WHERE d.DIVIDEND_PER_SHARE > 0
                  AND d.EX_DATE IS NOT NULL
            ),
            -- Synthetic splits and mergers for demo (no real data source)
            top_securities AS (
                SELECT DISTINCT
                    p.SecurityID,
                    s.IssuerID,
                    p.HoldingDate,
                    ROW_NUMBER() OVER (PARTITION BY p.SecurityID ORDER BY p.HoldingDate) as day_num
                FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR p
                JOIN {database_name}.CURATED.DIM_SECURITY s ON p.SecurityID = s.SecurityID
                WHERE p.SecurityID IN (
                    SELECT TOP 50 SecurityID 
                    FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR
                    GROUP BY SecurityID
                    ORDER BY SUM(MarketValue_Base) DESC
                )
            ),
            synthetic_actions AS (
                SELECT 
                    SecurityID,
                    IssuerID,
                    CASE WHEN UNIFORM(0, 1, RANDOM()) < 0.7 THEN 'Split' ELSE 'Merger' END as ActionType,
                    HoldingDate as AnnouncementDate,
                    DATEADD(day, {ex_offset}, HoldingDate) as ExDate,
                    DATEADD(day, {record_offset}, HoldingDate) as RecordDate,
                    DATEADD(day, {payment_offset}, HoldingDate) as PaymentDate,
                    CASE WHEN UNIFORM(0, 1, RANDOM()) < 0.7 THEN '2-for-1 stock split' ELSE 'Acquisition announcement' END as ActionDetails,
                    CASE WHEN UNIFORM(0, 1, RANDOM()) < 0.7 THEN 2.0 ELSE 0.0 END as ImpactValue,
                    CASE WHEN HoldingDate <= '{max_price_date}'::DATE THEN 'Announced' ELSE 'Pending' END as ProcessingStatus,
                    UNIFORM(1, 10, RANDOM()) as PortfoliosAffected
                FROM top_securities
                WHERE MOD(day_num, 365) = 0  -- ~1 split/merger per security per year
            ),
            -- Forward window: pending actions in next 10 days for demo queries
            forward_dates AS (
                SELECT DATEADD(day, seq4() + 1, '{max_price_date}'::DATE) as future_date
                FROM TABLE(GENERATOR(rowcount => 10))
                WHERE DAYOFWEEK(DATEADD(day, seq4() + 1, '{max_price_date}'::DATE)) BETWEEN 2 AND 6
            ),
            forward_securities AS (
                SELECT DISTINCT s.SecurityID, s.IssuerID
                FROM {database_name}.CURATED.DIM_SECURITY s
                WHERE EXISTS (
                    SELECT 1 FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR p
                    WHERE p.SecurityID = s.SecurityID
                )
                ORDER BY RANDOM()
                LIMIT 10
            ),
            forward_actions AS (
                SELECT 
                    fs.SecurityID,
                    fs.IssuerID,
                    CASE 
                        WHEN UNIFORM(0, 100, RANDOM()) <= 60 THEN 'Dividend'
                        WHEN UNIFORM(0, 100, RANDOM()) <= 85 THEN 'Split'
                        ELSE 'Merger'
                    END as ActionType,
                    DATEADD(day, -5, fd.future_date) as AnnouncementDate,
                    fd.future_date as ExDate,
                    DATEADD(day, 1, fd.future_date) as RecordDate,
                    DATEADD(day, 15, fd.future_date) as PaymentDate,
                    CASE 
                        WHEN UNIFORM(0, 100, RANDOM()) <= 60 THEN 'Quarterly dividend: $' || ROUND({dividend_sql}, 2) || ' per share'
                        WHEN UNIFORM(0, 100, RANDOM()) <= 85 THEN '2-for-1 stock split'
                        ELSE 'Acquisition announcement - pending regulatory approval'
                    END as ActionDetails,
                    CASE 
                        WHEN UNIFORM(0, 100, RANDOM()) <= 60 THEN {dividend_sql}
                        WHEN UNIFORM(0, 100, RANDOM()) <= 85 THEN 2.0
                        ELSE 0.0
                    END as ImpactValue,
                    'Pending' as ProcessingStatus,
                    UNIFORM(3, 8, RANDOM()) as PortfoliosAffected
                FROM forward_dates fd
                CROSS JOIN (SELECT * FROM forward_securities ORDER BY RANDOM() LIMIT 3) fs
            ),
            all_actions AS (
                SELECT * FROM real_dividends
                UNION ALL
                SELECT * FROM synthetic_actions
                UNION ALL
                SELECT * FROM forward_actions
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY AnnouncementDate, SecurityID) as ActionID,
                SecurityID,
                IssuerID,
                ActionType,
                AnnouncementDate,
                ExDate,
                RecordDate,
                PaymentDate,
                ActionDetails,
                ImpactValue,
                ProcessingStatus,
                PortfoliosAffected
            FROM all_actions
        """).collect()
    else:
        # Fallback to fully synthetic if no real dividend data
        log_warning("  No real dividend data found - using fully synthetic corporate actions")
        
        action_weights = get_global_value('corporate_actions.action_type_weights', {'Dividend': 0.90, 'Split': 0.07, 'Merger': 0.03})
        event_freq = get_global_value('corporate_actions.quarterly_event_frequency_days', 90)
        
        total_weight = sum(action_weights.values())
        dividend_threshold = action_weights['Dividend'] / total_weight * 3
        split_threshold = dividend_threshold + action_weights['Split'] / total_weight * 3
        
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_CORPORATE_ACTIONS AS
            WITH top_securities AS (
                SELECT DISTINCT
                    p.SecurityID,
                    s.IssuerID,
                    p.HoldingDate,
                    ROW_NUMBER() OVER (PARTITION BY p.SecurityID ORDER BY p.HoldingDate) as day_num
                FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR p
                JOIN {database_name}.CURATED.DIM_SECURITY s ON p.SecurityID = s.SecurityID
                WHERE p.SecurityID IN (
                    SELECT TOP 100 SecurityID 
                    FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR
                    GROUP BY SecurityID
                    ORDER BY SUM(MarketValue_Base) DESC
                )
            ),
            action_dates AS (
                SELECT 
                    SecurityID,
                    IssuerID,
                    HoldingDate as AnnouncementDate,
                    day_num,
                    UNIFORM(0, 3, RANDOM()) as action_type_flag
                FROM top_securities
                WHERE MOD(day_num, {event_freq}) = 0
            ),
            historical_actions AS (
                SELECT 
                    SecurityID,
                    IssuerID,
                    CASE 
                        WHEN action_type_flag < {dividend_threshold} THEN 'Dividend'
                        WHEN action_type_flag < {split_threshold} THEN 'Split'
                        ELSE 'Merger'
                    END as ActionType,
                    AnnouncementDate,
                    DATEADD(day, {ex_offset}, AnnouncementDate) as ExDate,
                    DATEADD(day, {record_offset}, AnnouncementDate) as RecordDate,
                    DATEADD(day, {payment_offset}, AnnouncementDate) as PaymentDate,
                    CASE 
                        WHEN action_type_flag < {dividend_threshold} THEN 'Quarterly dividend: $' || ROUND({dividend_sql}, 2) || ' per share'
                        WHEN action_type_flag < {split_threshold} THEN '2-for-1 stock split'
                        ELSE 'Acquisition announcement'
                    END as ActionDetails,
                    CASE 
                        WHEN action_type_flag < {dividend_threshold} THEN {dividend_sql}
                        WHEN action_type_flag < {split_threshold} THEN 2.0
                        ELSE 0.0
                    END as ImpactValue,
                    CASE 
                        WHEN action_type_flag < {dividend_threshold} THEN 'Processed'
                        WHEN action_type_flag < {split_threshold} THEN 'Pending'
                        ELSE 'Announced'
                    END as ProcessingStatus,
                    UNIFORM(1, 10, RANDOM()) as PortfoliosAffected
                FROM action_dates
            ),
            forward_dates AS (
                SELECT DATEADD(day, seq4() + 1, '{max_price_date}'::DATE) as future_date
                FROM TABLE(GENERATOR(rowcount => 10))
                WHERE DAYOFWEEK(DATEADD(day, seq4() + 1, '{max_price_date}'::DATE)) BETWEEN 2 AND 6
            ),
            forward_securities AS (
                SELECT DISTINCT s.SecurityID, s.IssuerID
                FROM {database_name}.CURATED.DIM_SECURITY s
                WHERE EXISTS (
                    SELECT 1 FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR p
                    WHERE p.SecurityID = s.SecurityID
                )
                ORDER BY RANDOM()
                LIMIT 15
            ),
            forward_actions AS (
                SELECT 
                    fs.SecurityID,
                    fs.IssuerID,
                    CASE 
                        WHEN UNIFORM(0, 100, RANDOM()) <= 70 THEN 'Dividend'
                        WHEN UNIFORM(0, 100, RANDOM()) <= 90 THEN 'Split'
                        ELSE 'Merger'
                    END as ActionType,
                    DATEADD(day, -5, fd.future_date) as AnnouncementDate,
                    fd.future_date as ExDate,
                    DATEADD(day, 1, fd.future_date) as RecordDate,
                    DATEADD(day, 15, fd.future_date) as PaymentDate,
                    CASE 
                        WHEN UNIFORM(0, 100, RANDOM()) <= 70 THEN 'Quarterly dividend: $' || ROUND({dividend_sql}, 2) || ' per share'
                        WHEN UNIFORM(0, 100, RANDOM()) <= 90 THEN '2-for-1 stock split'
                        ELSE 'Acquisition announcement - pending regulatory approval'
                    END as ActionDetails,
                    CASE 
                        WHEN UNIFORM(0, 100, RANDOM()) <= 70 THEN {dividend_sql}
                        WHEN UNIFORM(0, 100, RANDOM()) <= 90 THEN 2.0
                        ELSE 0.0
                    END as ImpactValue,
                    'Pending' as ProcessingStatus,
                    UNIFORM(3, 8, RANDOM()) as PortfoliosAffected
                FROM forward_dates fd
                CROSS JOIN (SELECT * FROM forward_securities ORDER BY RANDOM() LIMIT 3) fs
            ),
            all_actions AS (
                SELECT SecurityID, IssuerID, ActionType, AnnouncementDate, ExDate, RecordDate, PaymentDate, ActionDetails, ImpactValue, ProcessingStatus, PortfoliosAffected
                FROM historical_actions
                UNION ALL
                SELECT SecurityID, IssuerID, ActionType, AnnouncementDate, ExDate, RecordDate, PaymentDate, ActionDetails, ImpactValue, ProcessingStatus, PortfoliosAffected
                FROM forward_actions
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY AnnouncementDate, SecurityID) as ActionID,
                SecurityID,
                IssuerID,
                ActionType,
                AnnouncementDate,
                ExDate,
                RecordDate,
                PaymentDate,
                ActionDetails,
                ImpactValue,
                ProcessingStatus,
                PortfoliosAffected
            FROM all_actions
        """).collect()


def build_fact_corporate_action_impact(session: Session, test_mode: bool = False):
    """Build corporate action impact on portfolios."""
    database_name = config.DATABASE['name']
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    # Join on the closest holding date on or before the record date
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_CORPORATE_ACTION_IMPACT AS
        WITH latest_positions AS (
            SELECT 
                ca.ActionID,
                ca.SecurityID,
                ca.ActionType,
                ca.ImpactValue,
                ca.PaymentDate,
                ca.ProcessingStatus,
                ca.RecordDate,
                p.PortfolioID,
                p.Quantity,
                p.HoldingDate,
                ROW_NUMBER() OVER (
                    PARTITION BY ca.ActionID, p.PortfolioID 
                    ORDER BY p.HoldingDate DESC
                ) as rn
            FROM {database_name}.CURATED.FACT_CORPORATE_ACTIONS ca
            JOIN {database_name}.CURATED.FACT_POSITION_DAILY_ABOR p
                ON ca.SecurityID = p.SecurityID
                AND p.HoldingDate <= ca.RecordDate
            WHERE ca.ActionType IN ('Dividend', 'Split')
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY ActionID, PortfolioID) as ImpactID,
            ActionID,
            PortfolioID,
            SecurityID,
            Quantity as PositionBefore,
            CASE 
                WHEN ActionType = 'Split' THEN Quantity * ImpactValue
                ELSE Quantity
            END as PositionAfter,
            CASE 
                WHEN ActionType = 'Dividend' THEN Quantity * ImpactValue
                ELSE 0
            END as CashImpact,
            PaymentDate as ProcessedDate,
            'Operations Team' as ProcessedBy,
            CASE 
                WHEN ProcessingStatus = 'Processed' THEN 'Validated'
                ELSE 'Pending'
            END as ValidationStatus
        FROM latest_positions
        WHERE rn = 1
    """).collect()


def build_fact_cash_movements(session: Session, test_mode: bool = False):
    """Build cash movement fact table."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_CASH_MOVEMENTS AS
        WITH all_movements AS (
        -- Trade settlement cash flows
        SELECT 
            t.TransactionDate as MovementDate,
            t.PortfolioID,
            'Trade Settlement' as MovementType,
            t.GrossAmount_Local as Amount,
            t.Currency,
            MOD(ABS(HASH(t.TransactionID)), 20) + 1 as CounterpartyID,
            'Trade #' || t.TransactionID as Reference,
            'Settled' as Status,
            DATEADD(day, 2, t.TransactionDate) as ValueDate
        FROM {database_name}.CURATED.FACT_TRANSACTION t
        WHERE t.TransactionType IN ('BUY', 'SELL')
        
        UNION ALL
        
        -- Dividend cash flows
        SELECT 
            ca.PaymentDate as MovementDate,
            cai.PortfolioID,
            'Dividend' as MovementType,
            cai.CashImpact as Amount,
            'USD' as Currency,
            NULL as CounterpartyID,
            'Corp Action #' || ca.ActionID as Reference,
            'Received' as Status,
            ca.PaymentDate as ValueDate
        FROM {database_name}.CURATED.FACT_CORPORATE_ACTION_IMPACT cai
        JOIN {database_name}.CURATED.FACT_CORPORATE_ACTIONS ca ON cai.ActionID = ca.ActionID
        WHERE ca.ActionType = 'Dividend'
        
        UNION ALL
        
        -- Fee payments
        SELECT 
            n.CalculationDate as MovementDate,
            n.PortfolioID,
            'Fee' as MovementType,
            n.TotalAssets * -0.001 as Amount,
            'USD' as Currency,
            NULL as CounterpartyID,
            'Management Fee' as Reference,
            'Paid' as Status,
            n.CalculationDate as ValueDate
        FROM {database_name}.CURATED.FACT_NAV_CALCULATION n
        WHERE DAY(n.CalculationDate) = 1  -- Monthly fees
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY MovementDate, PortfolioID) as CashMovementID,
            MovementDate,
            PortfolioID,
            MovementType,
            Amount,
            Currency,
            CounterpartyID,
            Reference,
            Status,
            ValueDate
        FROM all_movements
    """).collect()


def build_fact_cash_positions(session: Session, test_mode: bool = False):
    """Build daily cash position snapshots.
    
    Includes recent window data (last 10 days relative to max_price_date) for demo scenarios.
    """
    database_name = config.DATABASE['name']
    
    # Get max_price_date for recent window generation
    max_price_date = get_max_price_date(session)
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    # Includes both historical positions and recent window for demo
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_CASH_POSITIONS AS
        WITH daily_flows AS (
            SELECT 
                MovementDate,
                PortfolioID,
                Currency,
                MOD(ABS(HASH(PortfolioID)), 8) + 1 as CustodianID,
                SUM(CASE WHEN Amount > 0 THEN Amount ELSE 0 END) as Inflows,
                SUM(CASE WHEN Amount < 0 THEN ABS(Amount) ELSE 0 END) as Outflows
            FROM {database_name}.CURATED.FACT_CASH_MOVEMENTS
            GROUP BY MovementDate, PortfolioID, Currency
        ),
        historical_cash AS (
            SELECT 
                MovementDate as PositionDate,
                PortfolioID,
                CustodianID,
                Currency,
                LAG(Inflows - Outflows, 1, 10000000) OVER (PARTITION BY PortfolioID ORDER BY MovementDate) as OpeningBalance,
                Inflows,
                Outflows,
                0 as FXGainLoss,
                Inflows - Outflows as NetChange,
                'Reconciled' as ReconciliationStatus
            FROM daily_flows
        ),
        -- Recent window: Generate daily cash positions for last 10 days relative to max_price_date
        -- This ensures demo queries for "current cash position" find data
        recent_dates AS (
            SELECT DATEADD(day, -seq4(), '{max_price_date}'::DATE) as recent_date
            FROM TABLE(GENERATOR(rowcount => 10))
            WHERE DAYOFWEEK(DATEADD(day, -seq4(), '{max_price_date}'::DATE)) BETWEEN 2 AND 6
        ),
        portfolios AS (
            SELECT DISTINCT PortfolioID FROM {database_name}.CURATED.DIM_PORTFOLIO
        ),
        recent_window_cash AS (
            SELECT 
                rd.recent_date as PositionDate,
                p.PortfolioID,
                MOD(ABS(HASH(p.PortfolioID)), 8) + 1 as CustodianID,
                'USD' as Currency,
                -- Base opening balance around $5-15M per portfolio
                UNIFORM(5000000, 15000000, RANDOM()) as OpeningBalance,
                -- Daily inflows $100K - $500K
                UNIFORM(100000, 500000, RANDOM()) as Inflows,
                -- Daily outflows $80K - $400K  
                UNIFORM(80000, 400000, RANDOM()) as Outflows,
                UNIFORM(-10000, 10000, RANDOM()) as FXGainLoss,
                0 as NetChange,
                'Reconciled' as ReconciliationStatus
            FROM recent_dates rd
            CROSS JOIN portfolios p
        ),
        all_cash AS (
            SELECT PositionDate, PortfolioID, CustodianID, Currency, OpeningBalance, Inflows, Outflows, FXGainLoss, ReconciliationStatus
            FROM historical_cash
            UNION ALL
            SELECT PositionDate, PortfolioID, CustodianID, Currency, OpeningBalance, Inflows, Outflows, FXGainLoss, ReconciliationStatus
            FROM recent_window_cash
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PositionDate, PortfolioID) as CashPositionID,
            PositionDate,
            PortfolioID,
            CustodianID,
            Currency,
            OpeningBalance,
            Inflows,
            Outflows,
            FXGainLoss,
            OpeningBalance + Inflows - Outflows + FXGainLoss as ClosingBalance,
            ReconciliationStatus
        FROM all_cash
    """).collect()


# =============================================================================
# PORTFOLIO MODELLING TABLES
# Tables for backtesting, Monte Carlo simulation, and risk analysis
# =============================================================================

def build_dim_model_portfolio(session: Session):
    """Build DIM_MODEL_PORTFOLIO for user-defined model portfolios.
    
    These are hypothetical portfolios used for what-if analysis and backtesting,
    separate from the actual managed portfolios in DIM_PORTFOLIO.
    """
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.DIM_MODEL_PORTFOLIO (
            ModelPortfolioID BIGINT IDENTITY(1,1) PRIMARY KEY,
            ModelPortfolioName VARCHAR(255) NOT NULL,
            Description VARCHAR(1000),
            Strategy VARCHAR(100),
            BenchmarkID VARCHAR(50),
            BaseCurrency CHAR(3) DEFAULT 'USD',
            RebalanceFrequency VARCHAR(50) DEFAULT 'quarterly',
            CreatedBy VARCHAR(100) DEFAULT 'system',
            CreatedAt TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            IsActive BOOLEAN DEFAULT TRUE,
            COMMENT VARCHAR(500)
        )
        COMMENT = 'User-defined model portfolios for backtesting and what-if analysis'
    """).collect()
    
    # Insert sample model portfolios for demo
    session.sql(f"""
        INSERT INTO {database_name}.CURATED.DIM_MODEL_PORTFOLIO 
            (ModelPortfolioName, Description, Strategy, BenchmarkID, RebalanceFrequency, COMMENT)
        VALUES
            ('60/40 Classic', 'Traditional 60% equity / 40% fixed income allocation', 'Balanced', 'SP500', 'quarterly', 'Classic retirement portfolio'),
            ('80/20 Growth', '80% equity / 20% fixed income for growth-oriented investors', 'Growth', 'SP500', 'quarterly', 'Growth-focused allocation'),
            ('Tech Leaders', 'Concentrated technology sector portfolio', 'Growth', 'NASDAQ100', 'monthly', 'High-growth tech focus'),
            ('ESG Leaders', 'Top ESG-rated companies across sectors', 'ESG', 'MSCI_ACWI', 'quarterly', 'Sustainability-focused'),
            ('Low Volatility', 'Minimum volatility portfolio construction', 'Defensive', 'SP500', 'monthly', 'Risk-managed approach'),
            ('Equal Weight Demo', 'Equal-weighted core demo stocks', 'Core', 'SP500', 'quarterly', 'Demo showcase portfolio')
    """).collect()
    
    log_detail("Created DIM_MODEL_PORTFOLIO with 6 sample model portfolios")


def build_fact_model_portfolio_weights(session: Session):
    """Build FACT_MODEL_PORTFOLIO_WEIGHTS with target weights for model portfolios.
    
    Uses demo companies from DIM_SECURITY to create realistic portfolio compositions.
    """
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_MODEL_PORTFOLIO_WEIGHTS AS
        WITH model_portfolios AS (
            SELECT ModelPortfolioID, ModelPortfolioName, Strategy
            FROM {database_name}.CURATED.DIM_MODEL_PORTFOLIO
        ),
        securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.GICS_Sector as Sector,
                ROW_NUMBER() OVER (ORDER BY s.SecurityID) as sec_rank
            FROM {database_name}.CURATED.DIM_SECURITY s
            JOIN {database_name}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
        ),
        -- Tech Leaders: Top tech stocks
        tech_weights AS (
            SELECT 
                mp.ModelPortfolioID,
                s.SecurityID,
                CASE 
                    WHEN s.Ticker IN ('AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMD', 'AVGO') THEN 0.12
                    WHEN s.Ticker IN ('SNOW', 'ADBE', 'CRM', 'INTC', 'QCOM') THEN 0.056
                    ELSE 0.0
                END as TargetWeight
            FROM model_portfolios mp
            CROSS JOIN securities s
            WHERE mp.ModelPortfolioName = 'Tech Leaders'
              AND s.Sector = 'Information Technology'
        ),
        -- Equal Weight Demo: Core demo stocks equally weighted
        equal_weights AS (
            SELECT 
                mp.ModelPortfolioID,
                s.SecurityID,
                CASE 
                    WHEN s.Ticker IN ('AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSM', 'SNOW', 'JPM', 'AMD', 'INTC', 'AVGO', 'QCOM') THEN ROUND(1.0/12, 4)
                    ELSE 0.0
                END as TargetWeight
            FROM model_portfolios mp
            CROSS JOIN securities s
            WHERE mp.ModelPortfolioName = 'Equal Weight Demo'
        ),
        -- 60/40 and 80/20: Diversified across sectors
        diversified_weights AS (
            SELECT 
                mp.ModelPortfolioID,
                s.SecurityID,
                CASE mp.ModelPortfolioName
                    WHEN '60/40 Classic' THEN 
                        CASE 
                            WHEN s.sec_rank <= 10 THEN 0.06  -- 60% in top 10 stocks
                            ELSE 0.0
                        END
                    WHEN '80/20 Growth' THEN
                        CASE 
                            WHEN s.sec_rank <= 10 THEN 0.08  -- 80% in top 10 stocks
                            ELSE 0.0
                        END
                    ELSE 0.0
                END as TargetWeight
            FROM model_portfolios mp
            CROSS JOIN securities s
            WHERE mp.ModelPortfolioName IN ('60/40 Classic', '80/20 Growth')
        ),
        all_weights AS (
            SELECT * FROM tech_weights WHERE TargetWeight > 0
            UNION ALL
            SELECT * FROM equal_weights WHERE TargetWeight > 0
            UNION ALL
            SELECT * FROM diversified_weights WHERE TargetWeight > 0
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY ModelPortfolioID, SecurityID) as WeightID,
            ModelPortfolioID,
            SecurityID,
            TargetWeight,
            TargetWeight * 0.5 as MinWeight,  -- Allow 50% underweight
            TargetWeight * 1.5 as MaxWeight,  -- Allow 50% overweight
            CURRENT_TIMESTAMP() as EffectiveDate
        FROM all_weights
    """).collect()
    
    log_detail("Created FACT_MODEL_PORTFOLIO_WEIGHTS")


def build_fact_risk_factors(session: Session):
    """Build FACT_RISK_FACTORS with Fama-French style risk factors.
    
    Generates synthetic factor returns based on realistic market dynamics.
    """
    database_name = config.DATABASE['name']
    max_price_date = get_max_price_date(session)
    
    # Generate 5 years of daily factor data
    years_of_history = config.YEARS_OF_HISTORY
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_RISK_FACTORS AS
        WITH date_range AS (
            SELECT DATEADD(day, -seq4(), '{max_price_date}'::DATE) as FactorDate
            FROM TABLE(GENERATOR(rowcount => {years_of_history * 365}))
            WHERE DAYOFWEEK(DATEADD(day, -seq4(), '{max_price_date}'::DATE)) BETWEEN 2 AND 6
        ),
        factor_values AS (
            SELECT 
                FactorDate,
                -- Market excess return (MKT-RF): ~8% annual, 16% vol -> daily ~0.03%, 1% daily vol
                UNIFORM(-0.025, 0.030, RANDOM()) as MKT_RF,
                -- Size factor (SMB): ~2% annual premium
                UNIFORM(-0.008, 0.010, RANDOM()) as SMB,
                -- Value factor (HML): ~3% annual premium  
                UNIFORM(-0.010, 0.012, RANDOM()) as HML,
                -- Momentum factor (MOM): ~4% annual but higher volatility
                UNIFORM(-0.015, 0.018, RANDOM()) as MOM,
                -- Profitability factor (RMW): ~3% annual
                UNIFORM(-0.008, 0.012, RANDOM()) as RMW,
                -- Investment factor (CMA): ~2.5% annual
                UNIFORM(-0.008, 0.010, RANDOM()) as CMA,
                -- Risk-free rate: ~4% annual -> ~0.016% daily
                0.04 / 252 as RF
            FROM date_range
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY FactorDate) as FactorID,
            FactorDate,
            MKT_RF,
            SMB,
            HML,
            MOM,
            RMW,
            CMA,
            RF,
            'Synthetic' as DataSource,
            CURRENT_TIMESTAMP() as LoadTimestamp
        FROM factor_values
        ORDER BY FactorDate
    """).collect()
    
    log_detail(f"Created FACT_RISK_FACTORS with {years_of_history} years of daily factor data")


def build_fact_expected_returns(session: Session):
    """Build FACT_EXPECTED_RETURNS with forward-looking return estimates.
    
    Generates expected returns based on sector, growth characteristics, and analyst consensus.
    Used for mean-variance optimization and Monte Carlo simulations.
    """
    database_name = config.DATABASE['name']
    max_price_date = get_max_price_date(session)
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_EXPECTED_RETURNS AS
        WITH securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.GICS_Sector as Sector
            FROM {database_name}.CURATED.DIM_SECURITY s
            JOIN {database_name}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
        ),
        -- Generate estimates for multiple horizons
        horizons AS (
            SELECT column1 as HorizonMonths, column2 as HorizonLabel
            FROM VALUES 
                (1, '1M'), (3, '3M'), (6, '6M'), (12, '1Y'), (36, '3Y'), (60, '5Y')
        ),
        base_estimates AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                s.Sector,
                h.HorizonMonths,
                h.HorizonLabel,
                -- Base expected return varies by sector
                CASE s.Sector
                    WHEN 'Information Technology' THEN UNIFORM(0.10, 0.18, RANDOM())
                    WHEN 'Healthcare' THEN UNIFORM(0.08, 0.14, RANDOM())
                    WHEN 'Financials' THEN UNIFORM(0.07, 0.12, RANDOM())
                    WHEN 'Consumer Discretionary' THEN UNIFORM(0.08, 0.15, RANDOM())
                    WHEN 'Communication Services' THEN UNIFORM(0.09, 0.14, RANDOM())
                    WHEN 'Industrials' THEN UNIFORM(0.07, 0.11, RANDOM())
                    WHEN 'Materials' THEN UNIFORM(0.06, 0.10, RANDOM())
                    WHEN 'Utilities' THEN UNIFORM(0.04, 0.07, RANDOM())
                    WHEN 'Energy' THEN UNIFORM(0.05, 0.12, RANDOM())
                    ELSE UNIFORM(0.06, 0.10, RANDOM())
                END as BaseAnnualReturn
            FROM securities s
            CROSS JOIN horizons h
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY SecurityID, HorizonMonths) as EstimateID,
            '{max_price_date}'::DATE as AsOfDate,
            SecurityID,
            HorizonMonths,
            HorizonLabel,
            BaseAnnualReturn as ExpectedReturn_Annualized,
            -- Confidence interval (higher uncertainty for longer horizons)
            BaseAnnualReturn - (0.05 * SQRT(HorizonMonths / 12)) as ExpectedReturn_Low,
            BaseAnnualReturn + (0.05 * SQRT(HorizonMonths / 12)) as ExpectedReturn_High,
            'Consensus' as Source,
            CURRENT_TIMESTAMP() as EstimateDate
        FROM base_estimates
    """).collect()
    
    log_detail("Created FACT_EXPECTED_RETURNS with multi-horizon estimates")


def build_fact_covariance_matrix(session: Session):
    """Build FACT_COVARIANCE_MATRIX with rolling covariance estimates.
    
    Uses actual returns from V_SECURITY_RETURNS to calculate realistic covariances.
    Stores only upper triangle to minimize storage (symmetric matrix).
    """
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    max_price_date = get_max_price_date(session)
    
    # First check if V_SECURITY_RETURNS exists (it's in CURATED schema)
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.V_SECURITY_RETURNS LIMIT 1").collect()
        has_returns = True
    except Exception:
        has_returns = False
        log_warning("V_SECURITY_RETURNS not found - creating synthetic covariance matrix")
    
    if has_returns:
        # Use actual returns to build covariance matrix
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_COVARIANCE_MATRIX AS
            WITH security_pairs AS (
                SELECT 
                    s1.SecurityID as SecurityID_Row,
                    s2.SecurityID as SecurityID_Col,
                    s1.Ticker as Ticker_Row,
                    s2.Ticker as Ticker_Col
                FROM {database_name}.CURATED.DIM_SECURITY s1
                CROSS JOIN {database_name}.CURATED.DIM_SECURITY s2
                WHERE s1.SecurityID <= s2.SecurityID  -- Upper triangle only
                  AND s1.AssetClass = 'Equity'
                  AND s2.AssetClass = 'Equity'
            ),
            returns_data AS (
                SELECT 
                    SECURITYID as SecurityID,
                    PRICE_DATE as DATE,
                    DAILY_RETURN_PCT / 100.0 as DailyReturn
                FROM {database_name}.{curated_schema}.V_SECURITY_RETURNS
                WHERE PRICE_DATE >= DATEADD(day, -252, '{max_price_date}'::DATE)
            ),
            paired_returns AS (
                SELECT 
                    sp.SecurityID_Row,
                    sp.SecurityID_Col,
                    r1.DATE,
                    r1.DailyReturn as Return_Row,
                    r2.DailyReturn as Return_Col
                FROM security_pairs sp
                JOIN returns_data r1 ON sp.SecurityID_Row = r1.SecurityID
                JOIN returns_data r2 ON sp.SecurityID_Col = r2.SecurityID AND r1.DATE = r2.DATE
            ),
            covariance_calc AS (
                SELECT 
                    SecurityID_Row,
                    SecurityID_Col,
                    COUNT(*) as NumObs,
                    -- Sample covariance
                    COVAR_SAMP(Return_Row, Return_Col) as Covariance,
                    -- Annualized covariance (multiply by 252)
                    COVAR_SAMP(Return_Row, Return_Col) * 252 as Covariance_Annualized,
                    -- Correlation
                    CORR(Return_Row, Return_Col) as Correlation
                FROM paired_returns
                GROUP BY SecurityID_Row, SecurityID_Col
                HAVING COUNT(*) >= 60  -- Minimum 60 observations
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY SecurityID_Row, SecurityID_Col) as CovarianceID,
                '{max_price_date}'::DATE as AsOfDate,
                SecurityID_Row,
                SecurityID_Col,
                Covariance,
                Covariance_Annualized,
                Correlation,
                NumObs as ObservationCount,
                252 as LookbackDays,
                CURRENT_TIMESTAMP() as CalculationTimestamp
            FROM covariance_calc
        """).collect()
    else:
        # Create synthetic covariance matrix
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_COVARIANCE_MATRIX AS
            WITH security_pairs AS (
                SELECT 
                    s1.SecurityID as SecurityID_Row,
                    s2.SecurityID as SecurityID_Col,
                    s1.Ticker as Ticker_Row,
                    s2.Ticker as Ticker_Col,
                    i1.GICS_Sector as Sector_Row,
                    i2.GICS_Sector as Sector_Col
                FROM {database_name}.CURATED.DIM_SECURITY s1
                JOIN {database_name}.CURATED.DIM_ISSUER i1 ON s1.IssuerID = i1.IssuerID
                CROSS JOIN {database_name}.CURATED.DIM_SECURITY s2
                JOIN {database_name}.CURATED.DIM_ISSUER i2 ON s2.IssuerID = i2.IssuerID
                WHERE s1.SecurityID <= s2.SecurityID
                  AND s1.AssetClass = 'Equity'
                  AND s2.AssetClass = 'Equity'
            ),
            synthetic_cov AS (
                SELECT 
                    SecurityID_Row,
                    SecurityID_Col,
                    -- Variance on diagonal (~20% annual vol -> 0.04 variance)
                    CASE WHEN SecurityID_Row = SecurityID_Col 
                        THEN UNIFORM(0.03, 0.08, RANDOM())  -- 17-28% vol
                        ELSE UNIFORM(0.005, 0.025, RANDOM())  -- Cross-covariance
                    END as Covariance_Annualized,
                    -- Same-sector pairs more correlated
                    CASE 
                        WHEN SecurityID_Row = SecurityID_Col THEN 1.0
                        WHEN Sector_Row = Sector_Col THEN UNIFORM(0.5, 0.8, RANDOM())
                        ELSE UNIFORM(0.2, 0.5, RANDOM())
                    END as Correlation
                FROM security_pairs
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY SecurityID_Row, SecurityID_Col) as CovarianceID,
                '{max_price_date}'::DATE as AsOfDate,
                SecurityID_Row,
                SecurityID_Col,
                Covariance_Annualized / 252 as Covariance,
                Covariance_Annualized,
                Correlation,
                252 as ObservationCount,
                252 as LookbackDays,
                CURRENT_TIMESTAMP() as CalculationTimestamp
            FROM synthetic_cov
        """).collect()
    
    log_detail("Created FACT_COVARIANCE_MATRIX")


def build_fact_backtest_results(session: Session):
    """Build FACT_BACKTEST_RESULTS table structure.
    
    This table stores results from backtest runs. Initially empty - populated
    by the backtesting engine when users run backtests.
    """
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_BACKTEST_RESULTS (
            BacktestID BIGINT IDENTITY(1,1) PRIMARY KEY,
            BacktestName VARCHAR(255),
            ModelPortfolioID BIGINT,
            PortfolioID BIGINT,
            RunTimestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            StartDate DATE NOT NULL,
            EndDate DATE NOT NULL,
            RebalanceFrequency VARCHAR(50),
            InitialInvestment DECIMAL(18,2),
            TransactionCostBps DECIMAL(8,4),
            ManagementFeePct DECIMAL(8,4),
            -- Results populated per date
            ResultDate DATE,
            PortfolioValue DECIMAL(18,2),
            DailyReturn DECIMAL(12,8),
            CumulativeReturn DECIMAL(12,8),
            Drawdown DECIMAL(12,8),
            -- Summary metrics (populated on final row)
            AnnualizedReturn DECIMAL(12,8),
            AnnualizedVolatility DECIMAL(12,8),
            SharpeRatio DECIMAL(10,4),
            SortinoRatio DECIMAL(10,4),
            MaxDrawdown DECIMAL(12,8),
            CalmarRatio DECIMAL(10,4),
            InformationRatio DECIMAL(10,4),
            TrackingError DECIMAL(12,8),
            VaR_95 DECIMAL(12,8),
            CVaR_95 DECIMAL(12,8),
            RunBy VARCHAR(100) DEFAULT 'system',
            COMMENT VARCHAR(1000)
        )
        COMMENT = 'Historical backtest results from portfolio modelling engine'
    """).collect()
    
    log_detail("Created FACT_BACKTEST_RESULTS (empty - populated by backtest engine)")


def build_fact_simulation_results(session: Session):
    """Build FACT_SIMULATION_RESULTS table structure.
    
    This table stores Monte Carlo simulation outputs. Initially empty - populated
    by the simulation engine when users run simulations.
    """
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_SIMULATION_RESULTS (
            SimulationID BIGINT IDENTITY(1,1),
            SimulationRunID BIGINT NOT NULL,  -- Groups paths from same run
            SimulationName VARCHAR(255),
            ModelPortfolioID BIGINT,
            RunTimestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            -- Simulation parameters
            HorizonMonths INT NOT NULL,
            NumSimulations INT NOT NULL,
            BlockSize INT,
            InitialInvestment DECIMAL(18,2),
            MonthlyContribution DECIMAL(18,2),
            MonthlyWithdrawal DECIMAL(18,2),
            -- Path data
            ScenarioPath INT NOT NULL,  -- 1 to NumSimulations
            Timestep INT NOT NULL,  -- 0 to HorizonMonths
            PortfolioValue DECIMAL(18,2),
            CumulativeReturn DECIMAL(12,8),
            -- Summary statistics (populated on summary row per run)
            Percentile_5 DECIMAL(18,2),
            Percentile_25 DECIMAL(18,2),
            Median DECIMAL(18,2),
            Percentile_75 DECIMAL(18,2),
            Percentile_95 DECIMAL(18,2),
            ProbLoss DECIMAL(8,4),
            ProbLoss20Pct DECIMAL(8,4),
            ProbDoubleInvestment DECIMAL(8,4),
            RunBy VARCHAR(100) DEFAULT 'system',
            PRIMARY KEY (SimulationRunID, ScenarioPath, Timestep)
        )
        COMMENT = 'Monte Carlo simulation results from portfolio modelling engine'
    """).collect()
    
    log_detail("Created FACT_SIMULATION_RESULTS (empty - populated by simulation engine)")


# =============================================================================
# PRIVATE EQUITY SCENARIO TABLES
# =============================================================================
# These tables support PE-focused scenarios: Deal Sourcing and Portfolio Monitoring

# PE Portfolio Companies - represents PE-owned companies
PE_PORTFOLIO_COMPANIES = [
    {
        'company_name': 'NordicTech Solutions',
        'sector': 'Technology',
        'sub_sector': 'Enterprise Software',
        'geography': 'Europe',
        'acquisition_date': '2022-03-15',
        'acquisition_price_mm': 450.0,
        'entry_ev_ebitda': 12.5,
        'ownership_pct': 75.0,
        'fund_name': 'EQT IX',
        'deal_team_lead': 'Marcus Lindberg',
        'status': 'Active',
        'thesis_category': 'Digital Transformation'
    },
    {
        'company_name': 'MedDevice Pro',
        'sector': 'Healthcare',
        'sub_sector': 'Medical Devices',
        'geography': 'Europe',
        'acquisition_date': '2021-09-01',
        'acquisition_price_mm': 320.0,
        'entry_ev_ebitda': 14.2,
        'ownership_pct': 85.0,
        'fund_name': 'EQT IX',
        'deal_team_lead': 'Anna Karlsson',
        'status': 'Active',
        'thesis_category': 'Consolidation'
    },
    {
        'company_name': 'GreenEnergy Systems',
        'sector': 'Industrials',
        'sub_sector': 'Renewable Energy Equipment',
        'geography': 'Europe',
        'acquisition_date': '2023-01-20',
        'acquisition_price_mm': 580.0,
        'entry_ev_ebitda': 11.0,
        'ownership_pct': 70.0,
        'fund_name': 'EQT Infrastructure V',
        'deal_team_lead': 'Erik Johansson',
        'status': 'Active',
        'thesis_category': 'Sustainability'
    },
    {
        'company_name': 'LogiFlow DACH',
        'sector': 'Industrials',
        'sub_sector': 'Logistics Technology',
        'geography': 'Europe',
        'acquisition_date': '2020-06-01',
        'acquisition_price_mm': 280.0,
        'entry_ev_ebitda': 9.5,
        'ownership_pct': 90.0,
        'fund_name': 'EQT VIII',
        'deal_team_lead': 'Thomas Mueller',
        'status': 'Active',
        'thesis_category': 'Digital Transformation'
    },
    {
        'company_name': 'ConsumerBrands Nordic',
        'sector': 'Consumer',
        'sub_sector': 'Consumer Products',
        'geography': 'Europe',
        'acquisition_date': '2019-11-15',
        'acquisition_price_mm': 420.0,
        'entry_ev_ebitda': 10.8,
        'ownership_pct': 80.0,
        'fund_name': 'EQT VIII',
        'deal_team_lead': 'Sofia Bergstrom',
        'status': 'Active',
        'thesis_category': 'Consolidation'
    },
    {
        'company_name': 'TelecomInfra AG',
        'sector': 'Technology',
        'sub_sector': 'Telecom Infrastructure',
        'geography': 'Europe',
        'acquisition_date': '2018-04-01',
        'acquisition_price_mm': 750.0,
        'entry_ev_ebitda': 8.5,
        'ownership_pct': 65.0,
        'fund_name': 'EQT Infrastructure IV',
        'deal_team_lead': 'Klaus Schmidt',
        'status': 'Exited',
        'exit_date': '2024-06-30',
        'exit_value_mm': 1650.0,
        'moic': 2.2,
        'irr_pct': 28.5,
        'thesis_category': 'Digital Transformation'
    }
]

# PE Deal Pipeline - active deals for sourcing analysis
PE_DEAL_PIPELINE = [
    {
        'target_company_name': 'CloudSecure Technologies',
        'sector': 'Technology',
        'sub_sector': 'Cybersecurity',
        'geography': 'Europe',
        'deal_stage': 'Due Diligence',
        'deal_type': 'Platform',
        'enterprise_value_mm': 380.0,
        'ev_ebitda_multiple': 14.5,
        'ev_revenue_multiple': 5.2,
        'target_ebitda_mm': 26.2,
        'target_revenue_mm': 73.1,
        'revenue_growth_pct': 25.0,
        'deal_team_lead': 'Marcus Lindberg',
        'ic_date': '2025-02-15',
        'expected_close_date': '2025-04-30',
        'competing_bidders': 3,
        'strategic_rationale': 'Leading Nordic cybersecurity platform with strong enterprise customer base. Opportunity for European consolidation play with identified add-on targets.',
        'key_risks': 'Customer concentration (top 3 = 35% revenue), key person dependency on CTO, pending regulatory changes in EU cyber directive'
    },
    {
        'target_company_name': 'HealthData Analytics',
        'sector': 'Healthcare',
        'sub_sector': 'Healthcare IT',
        'geography': 'Europe',
        'deal_stage': 'Due Diligence',
        'deal_type': 'Growth Capital',
        'enterprise_value_mm': 220.0,
        'ev_ebitda_multiple': 18.0,
        'ev_revenue_multiple': 6.5,
        'target_ebitda_mm': 12.2,
        'target_revenue_mm': 33.8,
        'revenue_growth_pct': 35.0,
        'deal_team_lead': 'Anna Karlsson',
        'ic_date': '2025-02-20',
        'expected_close_date': '2025-05-15',
        'competing_bidders': 2,
        'strategic_rationale': 'AI-powered healthcare analytics platform with GDPR-compliant data infrastructure. Strong growth trajectory with NHS and EU health system contracts.',
        'key_risks': 'Technology platform migration in progress, regulatory approval for AI diagnostics pending, limited US market presence'
    },
    {
        'target_company_name': 'Industrial Automation GmbH',
        'sector': 'Industrials',
        'sub_sector': 'Factory Automation',
        'geography': 'Europe',
        'deal_stage': 'Indicative Offer',
        'deal_type': 'Carve-out',
        'enterprise_value_mm': 520.0,
        'ev_ebitda_multiple': 9.5,
        'ev_revenue_multiple': 1.8,
        'target_ebitda_mm': 54.7,
        'target_revenue_mm': 289.0,
        'revenue_growth_pct': 8.0,
        'deal_team_lead': 'Erik Johansson',
        'ic_date': '2025-03-10',
        'expected_close_date': '2025-07-01',
        'competing_bidders': 4,
        'strategic_rationale': 'Carve-out from Siemens AG - non-core automation division with strong DACH market position. Significant operational improvement potential.',
        'key_risks': 'TSA complexity with parent, shared IT systems requiring separation, union negotiations pending',
        'issuer_id': None
    },
    {
        'target_company_name': 'EcoPackaging Solutions',
        'sector': 'Industrials',
        'sub_sector': 'Sustainable Packaging',
        'geography': 'Europe',
        'deal_stage': 'Screening',
        'deal_type': 'Platform',
        'enterprise_value_mm': 180.0,
        'ev_ebitda_multiple': 11.0,
        'ev_revenue_multiple': 2.0,
        'target_ebitda_mm': 16.4,
        'target_revenue_mm': 90.0,
        'revenue_growth_pct': 15.0,
        'deal_team_lead': 'Sofia Bergstrom',
        'ic_date': None,
        'expected_close_date': '2025-09-01',
        'competing_bidders': 1,
        'strategic_rationale': 'Sustainable packaging leader aligned with EU plastics directive. Platform for European consolidation in fragmented market.',
        'key_risks': 'Raw material price volatility, customer dependency on food & beverage sector, capex requirements for capacity expansion'
    },
    {
        'target_company_name': 'Nordic Fiber Networks',
        'sector': 'Technology',
        'sub_sector': 'Telecom Infrastructure',
        'geography': 'Europe',
        'deal_stage': 'SPA',
        'deal_type': 'Take-Private',
        'enterprise_value_mm': 890.0,
        'ev_ebitda_multiple': 12.0,
        'ev_revenue_multiple': 4.5,
        'target_ebitda_mm': 74.2,
        'target_revenue_mm': 197.8,
        'revenue_growth_pct': 12.0,
        'deal_team_lead': 'Klaus Schmidt',
        'ic_date': '2025-01-15',
        'expected_close_date': '2025-03-15',
        'competing_bidders': 0,
        'strategic_rationale': 'Take-private of listed Nordic fiber operator. Delisting premium 25%. Synergy potential with EQT Infrastructure portfolio companies.',
        'key_risks': 'Regulatory approval for delisting, minority shareholder acceptance, interest rate sensitivity on levered returns'
    },
    {
        'target_company_name': 'FinTech Payments AG',
        'sector': 'Technology',
        'sub_sector': 'Payment Processing',
        'geography': 'Europe',
        'deal_stage': 'Screening',
        'deal_type': 'Growth Capital',
        'enterprise_value_mm': 450.0,
        'ev_ebitda_multiple': 22.0,
        'ev_revenue_multiple': 8.0,
        'target_ebitda_mm': 20.5,
        'target_revenue_mm': 56.3,
        'revenue_growth_pct': 45.0,
        'deal_team_lead': 'Marcus Lindberg',
        'ic_date': None,
        'expected_close_date': '2025-10-01',
        'competing_bidders': 5,
        'strategic_rationale': 'High-growth B2B payments platform with PSD2 infrastructure. Potential add-on for existing FinTech portfolio.',
        'key_risks': 'High valuation in competitive process, regulatory evolution in payments, customer acquisition cost trends'
    },
    {
        'target_company_name': 'BioPharm Services',
        'sector': 'Healthcare',
        'sub_sector': 'Pharma Services',
        'geography': 'Europe',
        'deal_stage': 'Due Diligence',
        'deal_type': 'Add-on',
        'enterprise_value_mm': 145.0,
        'ev_ebitda_multiple': 13.0,
        'ev_revenue_multiple': 2.8,
        'target_ebitda_mm': 11.2,
        'target_revenue_mm': 51.8,
        'revenue_growth_pct': 18.0,
        'deal_team_lead': 'Anna Karlsson',
        'ic_date': '2025-02-25',
        'expected_close_date': '2025-04-15',
        'competing_bidders': 1,
        'strategic_rationale': 'Add-on to MedDevice Pro - clinical trial services with complementary customer base. €8M synergy potential.',
        'key_risks': 'Integration complexity, key scientist retention, ongoing clinical trial obligations'
    },
    {
        'target_company_name': 'DataCenter Nordic',
        'sector': 'Technology',
        'sub_sector': 'Data Centers',
        'geography': 'Europe',
        'deal_stage': 'Indicative Offer',
        'deal_type': 'Platform',
        'enterprise_value_mm': 680.0,
        'ev_ebitda_multiple': 16.0,
        'ev_revenue_multiple': 7.5,
        'target_ebitda_mm': 42.5,
        'target_revenue_mm': 90.7,
        'revenue_growth_pct': 20.0,
        'deal_team_lead': 'Klaus Schmidt',
        'ic_date': '2025-03-20',
        'expected_close_date': '2025-08-01',
        'competing_bidders': 6,
        'strategic_rationale': 'Green data center platform powered by Nordic hydro. AI/cloud demand driver. ESG-aligned infrastructure investment.',
        'key_risks': 'Competitive auction dynamics, power contract renewals 2026, construction cost overruns on expansion'
    },
    {
        'target_company_name': 'RetailTech Solutions',
        'sector': 'Technology',
        'sub_sector': 'Retail Software',
        'geography': 'Europe',
        'deal_stage': 'Screening',
        'deal_type': 'Platform',
        'enterprise_value_mm': 260.0,
        'ev_ebitda_multiple': 15.0,
        'ev_revenue_multiple': 4.2,
        'target_ebitda_mm': 17.3,
        'target_revenue_mm': 61.9,
        'revenue_growth_pct': 12.0,
        'deal_team_lead': 'Sofia Bergstrom',
        'ic_date': None,
        'expected_close_date': '2025-11-01',
        'competing_bidders': 2,
        'strategic_rationale': 'Omnichannel retail platform with strong Nordics presence. Consolidation opportunity in fragmented European market.',
        'key_risks': 'Retail sector cyclicality, customer churn in SME segment, cloud migration costs'
    },
    {
        'target_company_name': 'CleanWater Technologies',
        'sector': 'Industrials',
        'sub_sector': 'Water Treatment',
        'geography': 'Europe',
        'deal_stage': 'Signed',
        'deal_type': 'Platform',
        'enterprise_value_mm': 340.0,
        'ev_ebitda_multiple': 10.5,
        'ev_revenue_multiple': 2.2,
        'target_ebitda_mm': 32.4,
        'target_revenue_mm': 154.5,
        'revenue_growth_pct': 10.0,
        'deal_team_lead': 'Erik Johansson',
        'ic_date': '2024-12-10',
        'expected_close_date': '2025-02-28',
        'competing_bidders': 0,
        'strategic_rationale': 'Water treatment leader with municipal and industrial customer base. Infrastructure investment with regulatory tailwinds.',
        'key_risks': 'Municipal budget cycles, project execution risk, working capital intensity'
    }
]

# Value creation initiatives for portfolio companies
PE_VALUE_CREATION_INITIATIVES = {
    'NordicTech Solutions': [
        {'name': 'SaaS Migration', 'category': 'Revenue Growth', 'metric': 'ARR Growth %', 'baseline': 15, 'target': 35, 'current': 28, 'status': 'On Track', 'ebitda_impact': 12.0},
        {'name': 'Sales Team Expansion', 'category': 'Revenue Growth', 'metric': 'Sales Headcount', 'baseline': 25, 'target': 45, 'current': 38, 'status': 'On Track', 'ebitda_impact': 8.0},
        {'name': 'Cloud Infrastructure Optimization', 'category': 'Cost Optimization', 'metric': 'Infrastructure Cost %', 'baseline': 22, 'target': 15, 'current': 18, 'status': 'At Risk', 'ebitda_impact': 5.5},
        {'name': 'Product-Led Growth', 'category': 'Digital', 'metric': 'Trial-to-Paid %', 'baseline': 8, 'target': 15, 'current': 11, 'status': 'On Track', 'ebitda_impact': 6.0}
    ],
    'MedDevice Pro': [
        {'name': 'FDA 510(k) Clearance', 'category': 'Revenue Growth', 'metric': 'US Revenue €M', 'baseline': 0, 'target': 25, 'current': 0, 'status': 'Behind', 'ebitda_impact': 15.0},
        {'name': 'Manufacturing Consolidation', 'category': 'Cost Optimization', 'metric': 'COGS %', 'baseline': 42, 'target': 35, 'current': 38, 'status': 'On Track', 'ebitda_impact': 8.0},
        {'name': 'Quality Management System', 'category': 'ESG', 'metric': 'Quality Score', 'baseline': 75, 'target': 95, 'current': 88, 'status': 'On Track', 'ebitda_impact': 2.0}
    ],
    'GreenEnergy Systems': [
        {'name': 'European Expansion', 'category': 'Revenue Growth', 'metric': 'New Markets', 'baseline': 3, 'target': 8, 'current': 5, 'status': 'On Track', 'ebitda_impact': 20.0},
        {'name': 'Supply Chain Localization', 'category': 'Cost Optimization', 'metric': 'Local Sourcing %', 'baseline': 30, 'target': 60, 'current': 45, 'status': 'On Track', 'ebitda_impact': 10.0},
        {'name': 'Carbon Neutral Operations', 'category': 'ESG', 'metric': 'CO2 Tonnes', 'baseline': 5000, 'target': 0, 'current': 2500, 'status': 'On Track', 'ebitda_impact': 0.0}
    ],
    'LogiFlow DACH': [
        {'name': 'AI Route Optimization', 'category': 'Digital', 'metric': 'Cost per Delivery €', 'baseline': 4.5, 'target': 3.2, 'current': 3.8, 'status': 'On Track', 'ebitda_impact': 12.0},
        {'name': 'Warehouse Automation', 'category': 'Cost Optimization', 'metric': 'Picks per Hour', 'baseline': 120, 'target': 200, 'current': 165, 'status': 'On Track', 'ebitda_impact': 8.0},
        {'name': 'DACH Region Sales Push', 'category': 'Revenue Growth', 'metric': 'DACH Revenue €M', 'baseline': 45, 'target': 70, 'current': 52, 'status': 'At Risk', 'ebitda_impact': 15.0}
    ],
    'ConsumerBrands Nordic': [
        {'name': 'D2C E-commerce Platform', 'category': 'Revenue Growth', 'metric': 'D2C Revenue %', 'baseline': 5, 'target': 25, 'current': 18, 'status': 'On Track', 'ebitda_impact': 10.0},
        {'name': 'Sustainable Packaging', 'category': 'ESG', 'metric': 'Recyclable %', 'baseline': 40, 'target': 100, 'current': 75, 'status': 'On Track', 'ebitda_impact': -2.0},
        {'name': 'Working Capital Optimization', 'category': 'Working Capital', 'metric': 'NWC Days', 'baseline': 85, 'target': 60, 'current': 72, 'status': 'On Track', 'ebitda_impact': 3.0}
    ]
}


def build_pe_tables(session: Session, test_mode: bool = False):
    """Build all Private Equity scenario tables."""
    log_detail("Building PE scenario tables...")
    
    _run_build_step(build_dim_pe_fund, session, test_mode)
    _run_build_step(build_dim_portfolio_company, session, test_mode)
    _run_build_step(build_dim_deal_pipeline, session, test_mode)
    _run_build_step(build_fact_value_creation_plan, session, test_mode)
    _run_build_step(build_fact_board_pack_metrics, session, test_mode)
    _run_build_step(build_fact_portfolio_company_kpi, session, test_mode)
    
    _run_build_step(build_pe_board_packs_corpus, session, test_mode)
    _run_build_step(build_pe_due_diligence_corpus, session, test_mode)
    _run_build_step(build_pe_expert_network_corpus, session, test_mode)
    
    log_success("PE scenario tables built successfully")


def build_dim_portfolio_company(session: Session, test_mode: bool = False):
    """Build DIM_PORTFOLIO_COMPANY - PE-owned companies dimension."""
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.DIM_PORTFOLIO_COMPANY (
            PortfolioCompanyID INT IDENTITY(1,1) PRIMARY KEY,
            CompanyName VARCHAR(255) NOT NULL,
            Sector VARCHAR(100),
            SubSector VARCHAR(100),
            Geography VARCHAR(50),
            AcquisitionDate DATE,
            AcquisitionPrice_MM DECIMAL(12,2),
            EntryEV_EBITDA DECIMAL(6,2),
            OwnershipPct DECIMAL(5,2),
            FundName VARCHAR(100),
            FundID INT,
            DealTeamLead VARCHAR(100),
            Status VARCHAR(20),
            ExitDate DATE,
            ExitValue_MM DECIMAL(12,2),
            MOIC DECIMAL(6,2),
            IRR_PCT DECIMAL(6,2),
            ThesisCategory VARCHAR(50)
        )
        COMMENT = 'PE portfolio companies for value creation monitoring'
    """).collect()
    
    for pc in PE_PORTFOLIO_COMPANIES:
        exit_date = f"'{pc.get('exit_date')}'" if pc.get('exit_date') else 'NULL'
        exit_value = pc.get('exit_value_mm', 'NULL')
        moic = pc.get('moic', 'NULL')
        irr = pc.get('irr_pct', 'NULL')
        
        session.sql(f"""
            INSERT INTO {database_name}.CURATED.DIM_PORTFOLIO_COMPANY 
            (CompanyName, Sector, SubSector, Geography, AcquisitionDate, AcquisitionPrice_MM, 
             EntryEV_EBITDA, OwnershipPct, FundName, DealTeamLead, Status, ExitDate, 
             ExitValue_MM, MOIC, IRR_PCT, ThesisCategory)
            VALUES (
                '{pc['company_name']}', '{pc['sector']}', '{pc['sub_sector']}', '{pc['geography']}',
                '{pc['acquisition_date']}', {pc['acquisition_price_mm']}, {pc['entry_ev_ebitda']},
                {pc['ownership_pct']}, '{pc['fund_name']}', '{pc['deal_team_lead']}', 
                '{pc['status']}', {exit_date}, {exit_value}, {moic}, {irr}, '{pc['thesis_category']}'
            )
        """).collect()
    
    fund_table = f"{database_name}.CURATED.DIM_PE_FUND"
    session.sql(f"""
        UPDATE {database_name}.CURATED.DIM_PORTFOLIO_COMPANY pc
        SET pc.FundID = f.FundID
        FROM {fund_table} f
        WHERE pc.FundName = f.FundName
    """).collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.DIM_PORTFOLIO_COMPANY").collect()[0]['CNT']
    log_success(f"  DIM_PORTFOLIO_COMPANY: {count} portfolio companies (linked to PE funds)")


def build_dim_deal_pipeline(session: Session, test_mode: bool = False):
    """Build DIM_DEAL_PIPELINE - active deal pipeline dimension."""
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.DIM_DEAL_PIPELINE (
            DealID INT IDENTITY(1,1) PRIMARY KEY,
            TargetCompanyName VARCHAR(255),
            Sector VARCHAR(100),
            SubSector VARCHAR(100),
            Geography VARCHAR(50),
            DealStage VARCHAR(50),
            DealType VARCHAR(50),
            EnterpriseValue_MM DECIMAL(12,2),
            EV_EBITDA_Multiple DECIMAL(6,2),
            EV_Revenue_Multiple DECIMAL(6,2),
            TargetEBITDA_MM DECIMAL(12,2),
            TargetRevenue_MM DECIMAL(12,2),
            RevenueGrowthPct DECIMAL(6,2),
            DealTeamLead VARCHAR(100),
            ICDate DATE,
            ExpectedCloseDate DATE,
            CompetingBidders INT,
            StrategicRationale TEXT,
            KeyRisks TEXT,
            IssuerID INT,
            CreatedAt TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        COMMENT = 'Active PE deal pipeline for sourcing analysis'
    """).collect()
    
    for deal in PE_DEAL_PIPELINE:
        ic_date = f"'{deal['ic_date']}'" if deal.get('ic_date') else 'NULL'
        expected_close = f"'{deal['expected_close_date']}'" if deal.get('expected_close_date') else 'NULL'
        issuer_id = deal.get('issuer_id')
        issuer_id_sql = 'NULL' if issuer_id is None else str(issuer_id)
        strategic_rationale = deal['strategic_rationale'].replace("'", "''")
        key_risks = deal['key_risks'].replace("'", "''")
        
        session.sql(f"""
            INSERT INTO {database_name}.CURATED.DIM_DEAL_PIPELINE
            (TargetCompanyName, Sector, SubSector, Geography, DealStage, DealType, 
             EnterpriseValue_MM, EV_EBITDA_Multiple, EV_Revenue_Multiple, TargetEBITDA_MM,
             TargetRevenue_MM, RevenueGrowthPct, DealTeamLead, ICDate, ExpectedCloseDate,
             CompetingBidders, StrategicRationale, KeyRisks, IssuerID)
            VALUES (
                '{deal['target_company_name']}', '{deal['sector']}', '{deal['sub_sector']}',
                '{deal['geography']}', '{deal['deal_stage']}', '{deal['deal_type']}',
                {deal['enterprise_value_mm']}, {deal['ev_ebitda_multiple']}, {deal['ev_revenue_multiple']},
                {deal['target_ebitda_mm']}, {deal['target_revenue_mm']}, {deal['revenue_growth_pct']},
                '{deal['deal_team_lead']}', {ic_date}, {expected_close},
                {deal['competing_bidders']}, '{strategic_rationale}', '{key_risks}', {issuer_id_sql}
            )
        """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.DIM_DEAL_PIPELINE").collect()[0]['CNT']
    log_success(f"  DIM_DEAL_PIPELINE: {count} deals in pipeline")


def build_fact_value_creation_plan(session: Session, test_mode: bool = False):
    """Build FACT_VALUE_CREATION_PLAN - 100-day plan initiatives."""
    database_name = config.DATABASE['name']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_VALUE_CREATION_PLAN (
            PlanID INT IDENTITY(1,1) PRIMARY KEY,
            PortfolioCompanyID INT,
            InitiativeName VARCHAR(255),
            InitiativeCategory VARCHAR(100),
            TargetMetric VARCHAR(100),
            BaselineValue DECIMAL(15,2),
            TargetValue DECIMAL(15,2),
            CurrentValue DECIMAL(15,2),
            TargetDate DATE,
            StatusDate DATE,
            Status VARCHAR(50),
            ResponsibleExec VARCHAR(100),
            Commentary TEXT,
            ImpactEBITDA_MM DECIMAL(10,2)
        )
        COMMENT = '100-day plan initiatives and value creation tracking'
    """).collect()
    
    company_id_map = {}
    companies = session.sql(f"SELECT PortfolioCompanyID, CompanyName FROM {database_name}.CURATED.DIM_PORTFOLIO_COMPANY").collect()
    for row in companies:
        company_id_map[row['COMPANYNAME']] = row['PORTFOLIOCOMPANYID']
    
    rows = []
    for company_name, initiatives in PE_VALUE_CREATION_INITIATIVES.items():
        if company_name not in company_id_map:
            continue
        company_id = company_id_map[company_name]
        
        for init in initiatives:
            rows.append(
                f"({company_id}, '{init['name']}', '{init['category']}', '{init['metric']}', "
                f"{init['baseline']}, {init['target']}, {init['current']}, "
                f"DATEADD(month, 6, CURRENT_DATE()), CURRENT_DATE(), '{init['status']}', "
                f"'TBD', NULL, {init['ebitda_impact']})"
            )

    if rows:
        session.sql(f"""
            INSERT INTO {database_name}.CURATED.FACT_VALUE_CREATION_PLAN
            (PortfolioCompanyID, InitiativeName, InitiativeCategory, TargetMetric,
             BaselineValue, TargetValue, CurrentValue, TargetDate, StatusDate, Status,
             ResponsibleExec, Commentary, ImpactEBITDA_MM)
            SELECT $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13
            FROM VALUES {', '.join(rows)}
        """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.FACT_VALUE_CREATION_PLAN").collect()[0]['CNT']
    log_success(f"  FACT_VALUE_CREATION_PLAN: {count} initiatives")


def build_fact_board_pack_metrics(session: Session, test_mode: bool = False):
    """Build FACT_BOARD_PACK_METRICS - monthly board pack KPIs."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_BOARD_PACK_METRICS (
            MetricID INT IDENTITY(1,1) PRIMARY KEY,
            PortfolioCompanyID INT,
            ReportMonth DATE,
            Revenue_MM DECIMAL(12,2),
            EBITDA_MM DECIMAL(12,2),
            EBITDAMarginPct DECIMAL(6,2),
            NetDebt_MM DECIMAL(12,2),
            LeverageRatio DECIMAL(6,2),
            Headcount INT,
            CustomerCount INT,
            NRR_PCT DECIMAL(6,2),
            BudgetVariancePct DECIMAL(6,2),
            CashPosition_MM DECIMAL(12,2),
            CapexActual_MM DECIMAL(10,2),
            CapexBudget_MM DECIMAL(10,2)
        )
        COMMENT = 'Monthly board pack KPIs for portfolio monitoring'
    """).collect()
    
    companies = session.sql(f"""
        SELECT PortfolioCompanyID, CompanyName, AcquisitionPrice_MM, EntryEV_EBITDA, Sector
        FROM {database_name}.CURATED.DIM_PORTFOLIO_COMPANY
        WHERE Status = 'Active'
    """).collect()
    
    months_back = 6 if test_mode else 12
    
    for company in companies:
        company_id = company['PORTFOLIOCOMPANYID']
        acq_price = float(company['ACQUISITIONPRICE_MM'])
        entry_multiple = float(company['ENTRYEV_EBITDA'])
        base_ebitda = acq_price / entry_multiple
        base_revenue = base_ebitda * random.uniform(4, 8)
        base_margin = (base_ebitda / base_revenue) * 100
        base_debt = acq_price * random.uniform(0.4, 0.6)
        base_headcount = int(base_revenue * random.uniform(2, 5))
        base_customers = int(base_revenue * random.uniform(10, 50))
        
        for month_offset in range(months_back):
            report_date = date.today().replace(day=1) - timedelta(days=30 * month_offset)
            
            growth_factor = 1 + (months_back - month_offset) * random.uniform(0.005, 0.015)
            variance = random.uniform(-0.08, 0.05)
            
            revenue = base_revenue * growth_factor * (1 + random.uniform(-0.03, 0.05))
            ebitda = revenue * (base_margin / 100) * (1 + random.uniform(-0.05, 0.08))
            margin = (ebitda / revenue) * 100
            net_debt = base_debt * (1 - month_offset * 0.02)
            leverage = net_debt / (ebitda * 12)
            headcount = int(base_headcount * growth_factor)
            customers = int(base_customers * growth_factor)
            nrr = random.uniform(95, 115)
            cash = random.uniform(15, 50)
            capex_budget = base_revenue * 0.08
            capex_actual = capex_budget * (1 + random.uniform(-0.1, 0.15))
            
            session.sql(f"""
                INSERT INTO {database_name}.CURATED.FACT_BOARD_PACK_METRICS
                (PortfolioCompanyID, ReportMonth, Revenue_MM, EBITDA_MM, EBITDAMarginPct,
                 NetDebt_MM, LeverageRatio, Headcount, CustomerCount, NRR_PCT,
                 BudgetVariancePct, CashPosition_MM, CapexActual_MM, CapexBudget_MM)
                VALUES (
                    {company_id}, '{report_date}', {revenue:.2f}, {ebitda:.2f}, {margin:.1f},
                    {net_debt:.2f}, {leverage:.2f}, {headcount}, {customers}, {nrr:.1f},
                    {variance * 100:.1f}, {cash:.2f}, {capex_actual:.2f}, {capex_budget:.2f}
                )
            """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.FACT_BOARD_PACK_METRICS").collect()[0]['CNT']
    log_success(f"  FACT_BOARD_PACK_METRICS: {count} monthly records")


def build_fact_portfolio_company_kpi(session: Session, test_mode: bool = False):
    """Build FACT_PORTFOLIO_COMPANY_KPI - operational KPIs."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_PORTFOLIO_COMPANY_KPI (
            KPIID INT IDENTITY(1,1) PRIMARY KEY,
            PortfolioCompanyID INT,
            KPIDate DATE,
            KPIName VARCHAR(100),
            KPICategory VARCHAR(50),
            ActualValue DECIMAL(15,2),
            BudgetValue DECIMAL(15,2),
            PriorYearValue DECIMAL(15,2),
            Unit VARCHAR(20),
            Status VARCHAR(20)
        )
        COMMENT = 'Operational KPIs for portfolio company monitoring'
    """).collect()
    
    kpi_templates = [
        {'name': 'Employee NPS', 'category': 'ESG', 'unit': 'Score', 'base': 45, 'variance': 15},
        {'name': 'Customer Satisfaction', 'category': 'Customer', 'unit': '%', 'base': 80, 'variance': 10},
        {'name': 'Employee Turnover', 'category': 'Operational', 'unit': '%', 'base': 12, 'variance': 5},
        {'name': 'On-Time Delivery', 'category': 'Operational', 'unit': '%', 'base': 92, 'variance': 5},
        {'name': 'Carbon Intensity', 'category': 'ESG', 'unit': 'tCO2/€M', 'base': 25, 'variance': 10}
    ]
    
    companies = session.sql(f"""
        SELECT PortfolioCompanyID FROM {database_name}.CURATED.DIM_PORTFOLIO_COMPANY WHERE Status = 'Active'
    """).collect()
    
    for company in companies:
        company_id = company['PORTFOLIOCOMPANYID']
        kpi_date = date.today().replace(day=1)
        
        for kpi in kpi_templates:
            actual = kpi['base'] + random.uniform(-kpi['variance'], kpi['variance'])
            budget = kpi['base'] * 1.05
            prior_year = kpi['base'] * random.uniform(0.9, 1.0)
            
            if kpi['name'] in ['Employee Turnover', 'Carbon Intensity']:
                status = 'Green' if actual < budget else ('Amber' if actual < budget * 1.1 else 'Red')
            else:
                status = 'Green' if actual >= budget else ('Amber' if actual >= budget * 0.9 else 'Red')
            
            session.sql(f"""
                INSERT INTO {database_name}.CURATED.FACT_PORTFOLIO_COMPANY_KPI
                (PortfolioCompanyID, KPIDate, KPIName, KPICategory, ActualValue, BudgetValue, 
                 PriorYearValue, Unit, Status)
                VALUES (
                    {company_id}, '{kpi_date}', '{kpi['name']}', '{kpi['category']}',
                    {actual:.2f}, {budget:.2f}, {prior_year:.2f}, '{kpi['unit']}', '{status}'
                )
            """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.FACT_PORTFOLIO_COMPANY_KPI").collect()[0]['CNT']
    log_success(f"  FACT_PORTFOLIO_COMPANY_KPI: {count} KPI records")


def build_pe_board_packs_corpus(session: Session, test_mode: bool = False):
    """Build PE_BOARD_PACKS_CORPUS - monthly board pack documents for portfolio companies."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.PE_BOARD_PACKS_CORPUS (
            DOCUMENT_ID VARCHAR(64) PRIMARY KEY,
            PortfolioCompanyID INT,
            CompanyName VARCHAR(255),
            DOCUMENT_TITLE VARCHAR(500),
            DOCUMENT_TYPE VARCHAR(50),
            DOCUMENT_TEXT VARCHAR(16777216),
            ReportPeriod DATE,
            TOKEN_COUNT INT,
            PUBLISH_DATE DATE
        )
        COMMENT = 'Monthly board packs for PE portfolio company monitoring'
    """).collect()
    
    companies = session.sql(f"""
        SELECT PortfolioCompanyID, CompanyName, Sector, FundName, DealTeamLead
        FROM {database_name}.CURATED.DIM_PORTFOLIO_COMPANY
        WHERE Status = 'Active'
    """).collect()
    
    months_back = 3 if test_mode else 6
    
    for company in companies:
        company_id = company['PORTFOLIOCOMPANYID']
        company_name = company['COMPANYNAME']
        sector = company['SECTOR']
        fund = company['FUNDNAME']
        lead = company['DEALTEAMLEAD']
        
        for month_offset in range(months_back):
            report_date = date.today().replace(day=1) - timedelta(days=30 * month_offset)
            month_name = report_date.strftime('%B %Y')
            doc_id = f"BP_{company_id}_{report_date.strftime('%Y%m')}"
            
            board_pack_text = f"""
# {company_name} - Monthly Board Pack
## {month_name}

### Executive Summary
This report provides the monthly performance update for {company_name}, a {sector} portfolio company held by {fund}. Overall performance continues to track against the value creation plan with key initiatives progressing as expected.

### Financial Performance
**Revenue**: Performance in line with budget (+/- 3% variance). The commercial team continues to execute on the sales pipeline with particular strength in enterprise accounts.

**EBITDA**: Margin expansion initiatives are showing early results. Operating leverage is improving as the business scales.

**Cash Position**: Healthy liquidity position maintained. Working capital management remains a focus area.

### Value Creation Initiatives Update
The 100-day plan initiatives are progressing with the following status:
- Revenue growth initiatives: On track with new customer wins in target segments
- Cost optimization: Early wins from procurement consolidation
- Digital transformation: Technology platform upgrade proceeding to plan

### Key Risks and Mitigations
1. **Market Risk**: Monitoring competitive dynamics closely. Differentiation strategy remains intact.
2. **Execution Risk**: Key hires completed. Team capacity now adequate for growth plans.
3. **Regulatory Risk**: No material changes to regulatory landscape.

### Management Actions Required
- Approve FY budget revision incorporating updated growth assumptions
- Review proposed acquisition target for add-on opportunity
- Confirm attendance at upcoming investor conference

### Next Steps
- Complete Q{(report_date.month - 1) // 3 + 1} business review with management team
- Finalize commercial due diligence on add-on target
- Prepare materials for LP advisory committee meeting

---
Prepared by: {lead}
Fund: {fund}
Report Date: {report_date.strftime('%d %B %Y')}
"""
            
            token_count = len(board_pack_text.split()) * 1.3
            escaped_text = board_pack_text.replace("'", "''")
            
            session.sql(f"""
                INSERT INTO {database_name}.CURATED.PE_BOARD_PACKS_CORPUS
                (DOCUMENT_ID, PortfolioCompanyID, CompanyName, DOCUMENT_TITLE, DOCUMENT_TYPE, 
                 DOCUMENT_TEXT, ReportPeriod, TOKEN_COUNT, PUBLISH_DATE)
                VALUES (
                    '{doc_id}', {company_id}, '{company_name}',
                    '{company_name} Board Pack - {month_name}', 'Monthly Board Pack',
                    '{escaped_text}', '{report_date}', {int(token_count)}, '{report_date}'
                )
            """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.PE_BOARD_PACKS_CORPUS").collect()[0]['CNT']
    log_success(f"  PE_BOARD_PACKS_CORPUS: {count} board packs")


def build_pe_due_diligence_corpus(session: Session, test_mode: bool = False):
    """Build PE_DUE_DILIGENCE_CORPUS - due diligence documents for deals."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.PE_DUE_DILIGENCE_CORPUS (
            DOCUMENT_ID VARCHAR(64) PRIMARY KEY,
            DealID INT,
            TargetCompanyName VARCHAR(255),
            DOCUMENT_TITLE VARCHAR(500),
            DOCUMENT_TYPE VARCHAR(50),
            DOCUMENT_TEXT VARCHAR(16777216),
            TOKEN_COUNT INT,
            PUBLISH_DATE DATE
        )
        COMMENT = 'Due diligence documents for PE deal pipeline'
    """).collect()
    
    deals = session.sql(f"""
        SELECT DealID, TargetCompanyName, Sector, SubSector, Geography, DealType,
               EnterpriseValue_MM, EV_EBITDA_Multiple, TargetRevenue_MM, 
               StrategicRationale, KeyRisks, DealStage
        FROM {database_name}.CURATED.DIM_DEAL_PIPELINE
        WHERE DealStage IN ('Due Diligence', 'SPA', 'Signed', 'Indicative Offer')
    """).collect()
    
    dd_doc_types = [
        ('CIM', 'Confidential Information Memorandum'),
        ('VDD', 'Vendor Due Diligence Report'),
        ('CommDD', 'Commercial Due Diligence Summary'),
        ('MgmtPres', 'Management Presentation')
    ]
    
    for deal in deals:
        deal_id = deal['DEALID']
        target = deal['TARGETCOMPANYNAME']
        sector = deal['SECTOR']
        sub_sector = deal['SUBSECTOR']
        geography = deal['GEOGRAPHY']
        deal_type = deal['DEALTYPE']
        ev = deal['ENTERPRISEVALUE_MM']
        multiple = deal['EV_EBITDA_MULTIPLE']
        revenue = deal['TARGETREVENUE_MM']
        rationale = deal['STRATEGICRATIONALE']
        risks = deal['KEYRISKS']
        
        docs_to_create = dd_doc_types[:2] if test_mode else dd_doc_types
        
        for doc_code, doc_type in docs_to_create:
            doc_id = f"DD_{deal_id}_{doc_code}"
            
            if doc_code == 'CIM':
                dd_text = f"""
# Confidential Information Memorandum
## {target}

### Investment Opportunity Overview
{target} is a leading {sub_sector} company based in {geography}, presenting an attractive {deal_type} opportunity.

**Transaction Summary**
- Enterprise Value: €{ev:.0f}M
- EV/EBITDA Multiple: {multiple:.1f}x
- Revenue Base: €{revenue:.0f}M

### Strategic Rationale
{rationale}

### Business Description
{target} operates in the {sector} sector with focus on {sub_sector}. The company has established a strong market position through:
- Proprietary technology platform
- Long-standing customer relationships
- Experienced management team with track record of execution

### Financial Summary
The company has demonstrated consistent financial performance with:
- Revenue CAGR of 15%+ over the last 3 years
- EBITDA margins expanding through operational leverage
- Strong cash conversion supporting deleveraging

### Growth Opportunities
1. Geographic expansion into adjacent European markets
2. Product line extension leveraging existing customer base
3. Operational efficiency gains through digitalization
4. Add-on M&A to accelerate consolidation

### Key Investment Considerations
{risks}

---
CONFIDENTIAL - For discussion purposes only
"""
            elif doc_code == 'VDD':
                dd_text = f"""
# Vendor Due Diligence Report
## {target}

### Scope of Work
This VDD report covers financial, tax, and operational due diligence on {target} as commissioned by the selling shareholder.

### Key Findings Summary

**Financial Due Diligence**
- Historical EBITDA normalized for one-off items
- Quality of earnings analysis confirms sustainable profitability
- Working capital requirements in line with industry norms
- Capex split between maintenance and growth identified

**Tax Due Diligence**
- No material tax exposures identified
- Transfer pricing documentation in place
- Tax loss carryforwards available for utilization

**Operational Due Diligence**
- IT systems adequate but modernization opportunity exists
- HR and employment matters reviewed without material findings
- Key contracts reviewed - no change of control triggers identified

### Risk Factors
{risks}

### Conclusion
Based on our review, we consider {target} to be a well-managed business with strong fundamentals. The identified risks are manageable within the context of a typical {deal_type} transaction.

---
Prepared by: Big Four Advisory
Date: {date.today().strftime('%B %Y')}
"""
            elif doc_code == 'CommDD':
                dd_text = f"""
# Commercial Due Diligence
## {target} - Market Assessment

### Market Overview
The {sub_sector} market in {geography} is characterized by:
- Growing demand driven by digitalization trends
- Fragmented competitive landscape with consolidation potential
- Regulatory tailwinds supporting market expansion

### Competitive Position
{target} ranks among the top 5 players in its core market with:
- Strong brand recognition
- Differentiated product offering
- Sticky customer relationships

### Customer Analysis
Customer interviews confirm:
- High satisfaction with product and service
- Willingness to expand relationship
- Limited competitive alternatives

### Growth Assessment
The management business plan appears achievable based on:
- Validated market growth assumptions
- Realistic pricing assumptions
- Executable expansion strategy

---
Commercial Due Diligence by Strategy Consultants
"""
            else:
                dd_text = f"""
# Management Presentation
## {target} Investment Opportunity

### Company Overview
{target} - Leading {sub_sector} Platform in {geography}

### Investment Highlights
1. Market leader in attractive niche
2. Strong recurring revenue model
3. Experienced management team
4. Clear path to value creation

### Strategic Rationale
{rationale}

### Financial Overview
- Revenue: €{revenue:.0f}M
- Valuation: €{ev:.0f}M ({multiple:.1f}x EBITDA)

### Why Partner with {target}?
- Ready to scale with right capital partner
- Management committed to growth journey
- Significant value creation opportunity

---
Management Confidential
"""
            
            token_count = len(dd_text.split()) * 1.3
            escaped_text = dd_text.replace("'", "''")
            
            session.sql(f"""
                INSERT INTO {database_name}.CURATED.PE_DUE_DILIGENCE_CORPUS
                (DOCUMENT_ID, DealID, TargetCompanyName, DOCUMENT_TITLE, DOCUMENT_TYPE,
                 DOCUMENT_TEXT, TOKEN_COUNT, PUBLISH_DATE)
                VALUES (
                    '{doc_id}', {deal_id}, '{target}',
                    '{target} - {doc_type}', '{doc_type}',
                    '{escaped_text}', {int(token_count)}, CURRENT_DATE()
                )
            """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.PE_DUE_DILIGENCE_CORPUS").collect()[0]['CNT']
    log_success(f"  PE_DUE_DILIGENCE_CORPUS: {count} DD documents")


def build_pe_expert_network_corpus(session: Session, test_mode: bool = False):
    """Build PE_EXPERT_NETWORK_CORPUS - expert call transcripts."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.PE_EXPERT_NETWORK_CORPUS (
            DOCUMENT_ID VARCHAR(64) PRIMARY KEY,
            DealID INT,
            PortfolioCompanyID INT,
            TargetCompanyName VARCHAR(255),
            DOCUMENT_TITLE VARCHAR(500),
            ExpertRole VARCHAR(100),
            DOCUMENT_TEXT VARCHAR(16777216),
            TOKEN_COUNT INT,
            CallDate DATE
        )
        COMMENT = 'Expert network call transcripts for PE due diligence'
    """).collect()
    
    expert_roles = [
        'Former CEO',
        'Industry Consultant',
        'Former Customer Executive',
        'Supply Chain Expert',
        'Technology Advisor'
    ]
    
    deals = session.sql(f"""
        SELECT DealID, TargetCompanyName, Sector, SubSector, Geography
        FROM {database_name}.CURATED.DIM_DEAL_PIPELINE
        WHERE DealStage IN ('Due Diligence', 'Indicative Offer')
    """).collect()
    
    calls_per_deal = 2 if test_mode else 3
    
    for deal in deals:
        deal_id = deal['DEALID']
        target = deal['TARGETCOMPANYNAME']
        sector = deal['SECTOR']
        sub_sector = deal['SUBSECTOR']
        geography = deal['GEOGRAPHY']
        
        for call_num in range(calls_per_deal):
            expert_role = expert_roles[call_num % len(expert_roles)]
            doc_id = f"EXP_{deal_id}_{call_num + 1}"
            call_date = date.today() - timedelta(days=random.randint(5, 30))
            
            if 'CEO' in expert_role:
                expert_text = f"""
# Expert Network Call Transcript
## {target} - {expert_role} Interview

**Call Date**: {call_date.strftime('%d %B %Y')}
**Expert**: Former CEO of comparable {sub_sector} company
**Duration**: 45 minutes

### Key Discussion Points

**On Market Dynamics**
Expert: "The {sub_sector} market in {geography} has been consolidating for the past 3-4 years. We're seeing larger players acquire smaller specialists to build out capabilities. {target} is well-positioned in this environment given their technology differentiation."

**On Competitive Position**
Expert: "Having competed against {target} for several years, I can say they have a strong reputation in the market. Their customer relationships tend to be sticky - we rarely saw customers switch away from them. The product is solid and their service levels are good."

**On Management**
Expert: "I know the management team professionally. They're experienced operators who understand the market well. The CEO has been there for 8 years and has driven significant improvements. The CFO joined 3 years ago and has professionalized the finance function."

**On Growth Potential**
Expert: "There's definitely room to grow. The {geography} market is still underpenetrated compared to the US. Cross-selling to existing customers is an obvious opportunity. Geographic expansion into adjacent markets would also make sense with the right capital partner."

**On Risks**
Expert: "The main risk I'd flag is technology disruption. There are newer entrants with modern platforms. {target} will need to continue investing in their technology to stay competitive. Also, talent retention in {geography} is always a challenge for tech-enabled businesses."

### Expert Assessment
Overall positive on the business. Would rate it a B+ to A- as an investment opportunity.

---
Call facilitated by Expert Network Provider
"""
            elif 'Customer' in expert_role:
                expert_text = f"""
# Expert Network Call Transcript
## {target} - Customer Perspective

**Call Date**: {call_date.strftime('%d %B %Y')}
**Expert**: Former procurement executive who worked with {target}
**Duration**: 30 minutes

### Key Discussion Points

**On Product/Service Quality**
Expert: "We used {target} for 5 years. The product quality was consistently good - probably 8 out of 10. They were always responsive to issues and their technical support was better than competitors we evaluated."

**On Pricing**
Expert: "Their pricing is mid-market to premium. Not the cheapest but you get what you pay for. We always felt the value was there given the reliability and support."

**On Switching Costs**
Expert: "Switching costs are moderate to high. It took us about 6 months to fully implement their solution. Once you're integrated, there's a lot of training and process investment that makes switching painful."

**On Competition**
Expert: "We evaluated 3-4 alternatives when we went to tender. {target} won on product capability and local support presence. The main alternative was stronger on price but weaker on service."

**On Future of Relationship**
Expert: "If I were still there, I'd continue with {target}. They're investing in their platform and staying current. No reason to switch unless something dramatically changes."

### Expert Assessment
Strong customer endorsement. Product-market fit appears solid.

---
Call facilitated by Expert Network Provider
"""
            else:
                expert_text = f"""
# Expert Network Call Transcript
## {target} - {expert_role} Perspective

**Call Date**: {call_date.strftime('%d %B %Y')}
**Expert**: {expert_role} with 15+ years in {sector}
**Duration**: 40 minutes

### Key Discussion Points

**On Industry Trends**
Expert: "The {sub_sector} space is going through significant transformation. Digitalization is the key theme - companies that don't invest in technology will fall behind. {target} seems to be keeping pace from what I've seen in the market."

**On {geography} Market Specifics**
Expert: "The {geography} market has some unique characteristics. Customers tend to value relationships and local presence. This favors established players like {target} over new entrants trying to break in."

**On Operational Best Practices**
Expert: "Best-in-class operators in this space focus on three things: customer retention, operational efficiency, and talent development. From what I understand, {target} does reasonably well on all three."

**On Value Creation Opportunities**
Expert: "For a new owner, I'd focus on:
1. Accelerating the digital roadmap
2. Expanding the sales team in underpenetrated regions  
3. Looking at tuck-in acquisitions to add capability
4. Professionalizing operations where gaps exist"

**On Risks**
Expert: "Main risks are competitive pressure from well-funded players and the need to continuously invest in technology. Also, the current macro environment in {geography} creates some near-term headwinds."

### Expert Assessment
Solid business with identifiable value creation levers. Typical risks for the sector.

---
Call facilitated by Expert Network Provider
"""
            
            token_count = len(expert_text.split()) * 1.3
            escaped_text = expert_text.replace("'", "''")
            
            session.sql(f"""
                INSERT INTO {database_name}.CURATED.PE_EXPERT_NETWORK_CORPUS
                (DOCUMENT_ID, DealID, PortfolioCompanyID, TargetCompanyName, DOCUMENT_TITLE,
                 ExpertRole, DOCUMENT_TEXT, TOKEN_COUNT, CallDate)
                VALUES (
                    '{doc_id}', {deal_id}, NULL, '{target}',
                    '{target} - {expert_role} Call',
                    '{expert_role}', '{escaped_text}', {int(token_count)}, '{call_date}'
                )
            """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.CURATED.PE_EXPERT_NETWORK_CORPUS").collect()[0]['CNT']
    log_success(f"  PE_EXPERT_NETWORK_CORPUS: {count} expert call transcripts")


CREDIT_FUNDS = [
    {'fund_name': 'SAM Direct Lending Fund III', 'strategy': 'Senior Secured', 'vintage': 2023, 'aum_mm': 2800, 'status': 'Active'},
    {'fund_name': 'SAM Opportunistic Credit Fund', 'strategy': 'Opportunistic', 'vintage': 2022, 'aum_mm': 1900, 'status': 'Active'},
    {'fund_name': 'SAM Structured Credit Fund', 'strategy': 'Structured/Unitranche', 'vintage': 2024, 'aum_mm': 1500, 'status': 'Active'},
]

CREDIT_FUND_ASSIGNMENTS = {
    'SAM Direct Lending Fund III': ['Meridian Healthcare Group', 'Atlas Building Products', 'NovaCare Pharmaceuticals', 'Pacific Food Holdings', 'Sterling Manufacturing Corp', 'Clearview Diagnostics'],
    'SAM Opportunistic Credit Fund': ['Velocity Logistics Holdings', 'Sentinel Security Services', 'Orion Retail Group', 'Redwood Hospitality Group', 'Cascade Environmental'],
    'SAM Structured Credit Fund': ['Pinnacle Software Solutions', 'Vertex Telecom Infrastructure', 'Nexus Data Centres', 'HealthBridge Clinical Services'],
}

PE_FUNDS = [
    {'fund_name': 'EQT IX', 'strategy': 'Growth Equity', 'vintage': 2021, 'aum_mm': 4200, 'status': 'Active'},
    {'fund_name': 'EQT VIII', 'strategy': 'Buyout', 'vintage': 2019, 'aum_mm': 3800, 'status': 'Active'},
    {'fund_name': 'EQT Infrastructure V', 'strategy': 'Infrastructure', 'vintage': 2022, 'aum_mm': 5100, 'status': 'Active'},
    {'fund_name': 'EQT Infrastructure IV', 'strategy': 'Infrastructure', 'vintage': 2017, 'aum_mm': 3200, 'status': 'Harvesting'},
]


def build_dim_credit_fund(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    table_name = f"{database_name}.CURATED.DIM_CREDIT_FUND"

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            FundID INT IDENTITY(1,1) PRIMARY KEY,
            FundName VARCHAR(255) NOT NULL,
            Strategy VARCHAR(100),
            Vintage INT,
            AUM_MM DECIMAL(12,2),
            Status VARCHAR(20)
        )
        COMMENT = 'Private credit fund dimension'
    """).collect()

    values_clause = ", ".join(
        f"('{f['fund_name']}', '{f['strategy']}', {f['vintage']}, {f['aum_mm']}, '{f['status']}')"
        for f in CREDIT_FUNDS
    )
    session.sql(f"""
        INSERT INTO {table_name} (FundName, Strategy, Vintage, AUM_MM, Status)
        VALUES {values_clause}
    """).collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  DIM_CREDIT_FUND: {count} funds")


def build_dim_pe_fund(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    table_name = f"{database_name}.CURATED.DIM_PE_FUND"

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            FundID INT IDENTITY(1,1) PRIMARY KEY,
            FundName VARCHAR(255) NOT NULL,
            Strategy VARCHAR(100),
            Vintage INT,
            AUM_MM DECIMAL(12,2),
            Status VARCHAR(20)
        )
        COMMENT = 'PE fund dimension'
    """).collect()

    values_clause = ", ".join(
        f"('{f['fund_name']}', '{f['strategy']}', {f['vintage']}, {f['aum_mm']}, '{f['status']}')"
        for f in PE_FUNDS
    )
    session.sql(f"""
        INSERT INTO {table_name} (FundName, Strategy, Vintage, AUM_MM, Status)
        VALUES {values_clause}
    """).collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  DIM_PE_FUND: {count} funds")


CREDIT_BORROWERS = [
    {'name': 'Meridian Healthcare Group', 'sector': 'Healthcare', 'sub_sector': 'Hospital Operations', 'geography': 'US', 'sponsor': 'Apollo Global', 'revenue_mm': 2800, 'ebitda_mm': 420, 'employees': 12000, 'rating': 'B+', 'status': 'Active'},
    {'name': 'Velocity Logistics Holdings', 'sector': 'Industrials', 'sub_sector': 'Freight & Logistics', 'geography': 'US', 'sponsor': 'KKR', 'revenue_mm': 1950, 'ebitda_mm': 310, 'employees': 8500, 'rating': 'B', 'status': 'Active'},
    {'name': 'Pinnacle Software Solutions', 'sector': 'Technology', 'sub_sector': 'Enterprise Software', 'geography': 'US', 'sponsor': 'Thoma Bravo', 'revenue_mm': 680, 'ebitda_mm': 215, 'employees': 2200, 'rating': 'B+', 'status': 'Active'},
    {'name': 'Atlas Building Products', 'sector': 'Materials', 'sub_sector': 'Building Materials', 'geography': 'US', 'sponsor': 'Carlyle Group', 'revenue_mm': 1450, 'ebitda_mm': 230, 'employees': 5800, 'rating': 'B', 'status': 'Active'},
    {'name': 'Sentinel Security Services', 'sector': 'Industrials', 'sub_sector': 'Security Services', 'geography': 'US', 'sponsor': 'Blackstone', 'revenue_mm': 920, 'ebitda_mm': 155, 'employees': 15000, 'rating': 'B-', 'status': 'Active'},
    {'name': 'NovaCare Pharmaceuticals', 'sector': 'Healthcare', 'sub_sector': 'Specialty Pharma', 'geography': 'US', 'sponsor': 'Bain Capital', 'revenue_mm': 1100, 'ebitda_mm': 285, 'employees': 3200, 'rating': 'BB-', 'status': 'Active'},
    {'name': 'Orion Retail Group', 'sector': 'Consumer', 'sub_sector': 'Specialty Retail', 'geography': 'US', 'sponsor': 'Ares Management', 'revenue_mm': 2200, 'ebitda_mm': 198, 'employees': 9500, 'rating': 'B-', 'status': 'Watchlist'},
    {'name': 'Cascade Environmental', 'sector': 'Industrials', 'sub_sector': 'Environmental Services', 'geography': 'US', 'sponsor': 'EQT Partners', 'revenue_mm': 780, 'ebitda_mm': 140, 'employees': 3800, 'rating': 'B+', 'status': 'Active'},
    {'name': 'Vertex Telecom Infrastructure', 'sector': 'Technology', 'sub_sector': 'Telecom Infrastructure', 'geography': 'Europe', 'sponsor': 'CVC Capital', 'revenue_mm': 1650, 'ebitda_mm': 495, 'employees': 4200, 'rating': 'BB-', 'status': 'Active'},
    {'name': 'Pacific Food Holdings', 'sector': 'Consumer', 'sub_sector': 'Food & Beverage', 'geography': 'US', 'sponsor': 'TPG Capital', 'revenue_mm': 3100, 'ebitda_mm': 340, 'employees': 11000, 'rating': 'B', 'status': 'Active'},
    {'name': 'HealthBridge Clinical Services', 'sector': 'Healthcare', 'sub_sector': 'Clinical Trials', 'geography': 'US', 'sponsor': 'Welsh Carson', 'revenue_mm': 520, 'ebitda_mm': 125, 'employees': 1800, 'rating': 'B+', 'status': 'Active'},
    {'name': 'Sterling Manufacturing Corp', 'sector': 'Industrials', 'sub_sector': 'Precision Manufacturing', 'geography': 'US', 'sponsor': 'Warburg Pincus', 'revenue_mm': 890, 'ebitda_mm': 160, 'employees': 4500, 'rating': 'B', 'status': 'Active'},
    {'name': 'Nexus Data Centres', 'sector': 'Technology', 'sub_sector': 'Data Centres', 'geography': 'Europe', 'sponsor': 'Brookfield', 'revenue_mm': 1200, 'ebitda_mm': 480, 'employees': 1500, 'rating': 'BB', 'status': 'Active'},
    {'name': 'Redwood Hospitality Group', 'sector': 'Consumer', 'sub_sector': 'Hotels & Leisure', 'geography': 'US', 'sponsor': 'Apollo Global', 'revenue_mm': 1750, 'ebitda_mm': 210, 'employees': 13000, 'rating': 'B-', 'status': 'Watchlist'},
    {'name': 'Clearview Diagnostics', 'sector': 'Healthcare', 'sub_sector': 'Medical Diagnostics', 'geography': 'US', 'sponsor': 'Advent International', 'revenue_mm': 640, 'ebitda_mm': 175, 'employees': 2800, 'rating': 'B+', 'status': 'Active'},
]

CREDIT_FACILITIES = [
    {'borrower': 'Meridian Healthcare Group', 'facility_type': 'Term Loan B', 'commitment_mm': 1800, 'drawn_mm': 1800, 'rate_type': 'SOFR + 425bps', 'spread_bps': 425, 'maturity': '2029-06-15', 'floor_bps': 75, 'origination': '2024-06-15', 'pik_toggle': False, 'call_protection': '101 soft call 12mo'},
    {'borrower': 'Meridian Healthcare Group', 'facility_type': 'Revolver', 'commitment_mm': 250, 'drawn_mm': 50, 'rate_type': 'SOFR + 375bps', 'spread_bps': 375, 'maturity': '2028-06-15', 'floor_bps': 0, 'origination': '2024-06-15', 'pik_toggle': False, 'call_protection': 'None'},
    {'borrower': 'Velocity Logistics Holdings', 'facility_type': 'Term Loan B', 'commitment_mm': 1200, 'drawn_mm': 1200, 'rate_type': 'SOFR + 450bps', 'spread_bps': 450, 'maturity': '2029-03-20', 'floor_bps': 100, 'origination': '2024-03-20', 'pik_toggle': False, 'call_protection': '101 soft call 6mo'},
    {'borrower': 'Pinnacle Software Solutions', 'facility_type': 'Unitranche', 'commitment_mm': 850, 'drawn_mm': 850, 'rate_type': 'SOFR + 550bps', 'spread_bps': 550, 'maturity': '2030-01-10', 'floor_bps': 100, 'origination': '2025-01-10', 'pik_toggle': True, 'call_protection': '102/101 hard call'},
    {'borrower': 'Atlas Building Products', 'facility_type': 'Term Loan B', 'commitment_mm': 950, 'drawn_mm': 950, 'rate_type': 'SOFR + 400bps', 'spread_bps': 400, 'maturity': '2028-09-01', 'floor_bps': 75, 'origination': '2023-09-01', 'pik_toggle': False, 'call_protection': 'None'},
    {'borrower': 'Atlas Building Products', 'facility_type': 'Delayed Draw TL', 'commitment_mm': 200, 'drawn_mm': 120, 'rate_type': 'SOFR + 400bps', 'spread_bps': 400, 'maturity': '2028-09-01', 'floor_bps': 75, 'origination': '2023-09-01', 'pik_toggle': False, 'call_protection': 'None'},
    {'borrower': 'Sentinel Security Services', 'facility_type': 'Term Loan B', 'commitment_mm': 680, 'drawn_mm': 680, 'rate_type': 'SOFR + 500bps', 'spread_bps': 500, 'maturity': '2029-11-15', 'floor_bps': 100, 'origination': '2024-11-15', 'pik_toggle': False, 'call_protection': '101 soft call 6mo'},
    {'borrower': 'NovaCare Pharmaceuticals', 'facility_type': 'Term Loan B', 'commitment_mm': 750, 'drawn_mm': 750, 'rate_type': 'SOFR + 375bps', 'spread_bps': 375, 'maturity': '2030-04-01', 'floor_bps': 50, 'origination': '2025-04-01', 'pik_toggle': False, 'call_protection': '101 soft call 12mo'},
    {'borrower': 'Orion Retail Group', 'facility_type': 'Term Loan B', 'commitment_mm': 1100, 'drawn_mm': 1100, 'rate_type': 'SOFR + 475bps', 'spread_bps': 475, 'maturity': '2028-02-28', 'floor_bps': 100, 'origination': '2023-02-28', 'pik_toggle': True, 'call_protection': 'None'},
    {'borrower': 'Orion Retail Group', 'facility_type': 'Revolver', 'commitment_mm': 150, 'drawn_mm': 130, 'rate_type': 'SOFR + 425bps', 'spread_bps': 425, 'maturity': '2027-02-28', 'floor_bps': 0, 'origination': '2023-02-28', 'pik_toggle': False, 'call_protection': 'None'},
    {'borrower': 'Cascade Environmental', 'facility_type': 'Unitranche', 'commitment_mm': 520, 'drawn_mm': 520, 'rate_type': 'SOFR + 525bps', 'spread_bps': 525, 'maturity': '2030-07-01', 'floor_bps': 100, 'origination': '2025-07-01', 'pik_toggle': False, 'call_protection': '102/101 hard call'},
    {'borrower': 'Vertex Telecom Infrastructure', 'facility_type': 'Term Loan B', 'commitment_mm': 1400, 'drawn_mm': 1400, 'rate_type': 'SOFR + 350bps', 'spread_bps': 350, 'maturity': '2030-08-15', 'floor_bps': 50, 'origination': '2025-08-15', 'pik_toggle': False, 'call_protection': '101 soft call 12mo'},
    {'borrower': 'Pacific Food Holdings', 'facility_type': 'Term Loan B', 'commitment_mm': 1600, 'drawn_mm': 1600, 'rate_type': 'SOFR + 425bps', 'spread_bps': 425, 'maturity': '2029-05-01', 'floor_bps': 75, 'origination': '2024-05-01', 'pik_toggle': False, 'call_protection': '101 soft call 6mo'},
    {'borrower': 'Pacific Food Holdings', 'facility_type': 'Revolver', 'commitment_mm': 200, 'drawn_mm': 0, 'rate_type': 'SOFR + 375bps', 'spread_bps': 375, 'maturity': '2028-05-01', 'floor_bps': 0, 'origination': '2024-05-01', 'pik_toggle': False, 'call_protection': 'None'},
    {'borrower': 'HealthBridge Clinical Services', 'facility_type': 'Unitranche', 'commitment_mm': 380, 'drawn_mm': 380, 'rate_type': 'SOFR + 575bps', 'spread_bps': 575, 'maturity': '2030-10-01', 'floor_bps': 100, 'origination': '2025-10-01', 'pik_toggle': True, 'call_protection': '103/102/101 hard call'},
    {'borrower': 'Sterling Manufacturing Corp', 'facility_type': 'Term Loan B', 'commitment_mm': 600, 'drawn_mm': 600, 'rate_type': 'SOFR + 450bps', 'spread_bps': 450, 'maturity': '2029-01-15', 'floor_bps': 75, 'origination': '2024-01-15', 'pik_toggle': False, 'call_protection': '101 soft call 6mo'},
    {'borrower': 'Nexus Data Centres', 'facility_type': 'Term Loan B', 'commitment_mm': 1000, 'drawn_mm': 1000, 'rate_type': 'SOFR + 350bps', 'spread_bps': 350, 'maturity': '2031-03-01', 'floor_bps': 50, 'origination': '2026-03-01', 'pik_toggle': False, 'call_protection': '101 soft call 12mo'},
    {'borrower': 'Redwood Hospitality Group', 'facility_type': 'Term Loan B', 'commitment_mm': 900, 'drawn_mm': 900, 'rate_type': 'SOFR + 500bps', 'spread_bps': 500, 'maturity': '2028-07-01', 'floor_bps': 100, 'origination': '2023-07-01', 'pik_toggle': True, 'call_protection': 'None'},
    {'borrower': 'Redwood Hospitality Group', 'facility_type': 'Revolver', 'commitment_mm': 100, 'drawn_mm': 85, 'rate_type': 'SOFR + 450bps', 'spread_bps': 450, 'maturity': '2027-07-01', 'floor_bps': 0, 'origination': '2023-07-01', 'pik_toggle': False, 'call_protection': 'None'},
    {'borrower': 'Clearview Diagnostics', 'facility_type': 'Unitranche', 'commitment_mm': 450, 'drawn_mm': 450, 'rate_type': 'SOFR + 500bps', 'spread_bps': 500, 'maturity': '2030-12-01', 'floor_bps': 75, 'origination': '2025-12-01', 'pik_toggle': False, 'call_protection': '102/101 hard call'},
]

CREDIT_DEAL_PIPELINE = [
    {'target': 'Summit IT Managed Services', 'sector': 'Technology', 'sub_sector': 'IT Services', 'sponsor': 'Vista Equity', 'deal_type': 'LBO', 'facility_type': 'Unitranche', 'size_mm': 650, 'spread_bps': 525, 'leverage': 5.8, 'stage': 'Term Sheet', 'expected_close': '2026-05-15'},
    {'target': 'Continental Packaging Inc', 'sector': 'Industrials', 'sub_sector': 'Packaging', 'sponsor': 'Advent International', 'deal_type': 'LBO', 'facility_type': 'Term Loan B', 'size_mm': 1100, 'spread_bps': 400, 'leverage': 4.5, 'stage': 'Due Diligence', 'expected_close': '2026-06-30'},
    {'target': 'BrightPath Education', 'sector': 'Consumer', 'sub_sector': 'Education Services', 'sponsor': 'Providence Equity', 'deal_type': 'Refinancing', 'facility_type': 'Term Loan B', 'size_mm': 800, 'spread_bps': 375, 'leverage': 4.0, 'stage': 'Mandate', 'expected_close': '2026-04-01'},
    {'target': 'Apex Waste Solutions', 'sector': 'Industrials', 'sub_sector': 'Waste Management', 'sponsor': 'GIP', 'deal_type': 'Add-on', 'facility_type': 'Delayed Draw TL', 'size_mm': 350, 'spread_bps': 450, 'leverage': 5.2, 'stage': 'Allocation', 'expected_close': '2026-04-15'},
    {'target': 'Quantum Cyber Security', 'sector': 'Technology', 'sub_sector': 'Cybersecurity', 'sponsor': 'Permira', 'deal_type': 'LBO', 'facility_type': 'Unitranche', 'size_mm': 550, 'spread_bps': 575, 'leverage': 6.2, 'stage': 'Term Sheet', 'expected_close': '2026-08-01'},
    {'target': 'Heritage Senior Living', 'sector': 'Healthcare', 'sub_sector': 'Senior Care', 'sponsor': 'Formation Capital', 'deal_type': 'LBO', 'facility_type': 'Term Loan B', 'size_mm': 750, 'spread_bps': 475, 'leverage': 5.5, 'stage': 'Term Sheet', 'expected_close': '2026-06-01'},
    {'target': 'TrueNorth Distribution', 'sector': 'Industrials', 'sub_sector': 'Distribution', 'sponsor': 'CD&R', 'deal_type': 'Refinancing', 'facility_type': 'Term Loan B', 'size_mm': 900, 'spread_bps': 350, 'leverage': 3.8, 'stage': 'Commitment', 'expected_close': '2026-04-30'},
    {'target': 'Sapphire Dental Partners', 'sector': 'Healthcare', 'sub_sector': 'Dental Services', 'sponsor': 'KKR', 'deal_type': 'Add-on', 'facility_type': 'Incremental TL', 'size_mm': 250, 'spread_bps': 500, 'leverage': 5.0, 'stage': 'Due Diligence', 'expected_close': '2026-05-30'},
    {'target': 'Ember Energy Services', 'sector': 'Energy', 'sub_sector': 'Oilfield Services', 'sponsor': 'Riverstone', 'deal_type': 'LBO', 'facility_type': 'Term Loan B', 'size_mm': 1300, 'spread_bps': 500, 'leverage': 4.8, 'stage': 'Screening', 'expected_close': '2026-09-15'},
    {'target': 'ProVet Animal Health', 'sector': 'Healthcare', 'sub_sector': 'Veterinary Services', 'sponsor': 'BC Partners', 'deal_type': 'LBO', 'facility_type': 'Unitranche', 'size_mm': 480, 'spread_bps': 550, 'leverage': 5.5, 'stage': 'Term Sheet', 'expected_close': '2026-07-01'},
]


def build_dim_credit_borrower(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    table_name = f"{database_name}.CURATED.DIM_CREDIT_BORROWER"

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            BorrowerID INT IDENTITY(1,1) PRIMARY KEY,
            BorrowerName VARCHAR(255) NOT NULL,
            Sector VARCHAR(100),
            SubSector VARCHAR(100),
            Geography VARCHAR(50),
            Sponsor VARCHAR(100),
            Revenue_MM DECIMAL(12,2),
            EBITDA_MM DECIMAL(12,2),
            Employees INT,
            CreditRating VARCHAR(10),
            Status VARCHAR(20),
            FundID INT,
            FundName VARCHAR(255)
        )
        COMMENT = 'Private credit borrower dimension'
    """).collect()

    rows = [
        (b['name'], b['sector'], b['sub_sector'], b['geography'], b['sponsor'],
         b['revenue_mm'], b['ebitda_mm'], b['employees'], b['rating'], b['status'])
        for b in CREDIT_BORROWERS
    ]
    values_clause = ", ".join(
        f"('{r[0]}', '{r[1]}', '{r[2]}', '{r[3]}', '{r[4]}', {r[5]}, {r[6]}, {r[7]}, '{r[8]}', '{r[9]}')"
        for r in rows
    )
    session.sql(f"""
        INSERT INTO {table_name}
        (BorrowerName, Sector, SubSector, Geography, Sponsor, Revenue_MM, EBITDA_MM,
         Employees, CreditRating, Status)
        VALUES {values_clause}
    """).collect()

    fund_table = f"{database_name}.CURATED.DIM_CREDIT_FUND"
    for fund_name, borrowers in CREDIT_FUND_ASSIGNMENTS.items():
        borrower_list = ", ".join(f"'{b}'" for b in borrowers)
        session.sql(f"""
            UPDATE {table_name}
            SET FundID = (SELECT FundID FROM {fund_table} WHERE FundName = '{fund_name}'),
                FundName = '{fund_name}'
            WHERE BorrowerName IN ({borrower_list})
        """).collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  DIM_CREDIT_BORROWER: {count} borrowers (assigned to {len(CREDIT_FUND_ASSIGNMENTS)} funds)")


def build_dim_credit_facility(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    table_name = f"{database_name}.CURATED.DIM_CREDIT_FACILITY"

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            FacilityID INT IDENTITY(1,1) PRIMARY KEY,
            BorrowerID INT,
            BorrowerName VARCHAR(255),
            FacilityType VARCHAR(50),
            Commitment_MM DECIMAL(12,2),
            Drawn_MM DECIMAL(12,2),
            RateType VARCHAR(50),
            Spread_BPS INT,
            Floor_BPS INT,
            MaturityDate DATE,
            OriginationDate DATE,
            PIKToggle BOOLEAN,
            CallProtection VARCHAR(100)
        )
        COMMENT = 'Private credit facility dimension'
    """).collect()

    values_rows = []
    for f in CREDIT_FACILITIES:
        values_rows.append(
            f"('{f['borrower']}', '{f['facility_type']}', {f['commitment_mm']}, {f['drawn_mm']}, "
            f"'{f['rate_type']}', {f['spread_bps']}, {f['floor_bps']}, '{f['maturity']}', "
            f"'{f['origination']}', {f['pik_toggle']}, '{f['call_protection']}')"
        )
    values_clause = ", ".join(values_rows)

    session.sql(f"""
        INSERT INTO {table_name}
        (BorrowerID, BorrowerName, FacilityType, Commitment_MM, Drawn_MM, RateType,
         Spread_BPS, Floor_BPS, MaturityDate, OriginationDate, PIKToggle, CallProtection)
        WITH facility_data AS (
            SELECT column1 AS BorrowerName, column2 AS FacilityType, column3 AS Commitment_MM,
                   column4 AS Drawn_MM, column5 AS RateType, column6 AS Spread_BPS,
                   column7 AS Floor_BPS, column8::DATE AS MaturityDate, column9::DATE AS OriginationDate,
                   column10 AS PIKToggle, column11 AS CallProtection
            FROM VALUES {values_clause}
        )
        SELECT b.BorrowerID, fd.BorrowerName, fd.FacilityType, fd.Commitment_MM, fd.Drawn_MM,
               fd.RateType, fd.Spread_BPS, fd.Floor_BPS, fd.MaturityDate, fd.OriginationDate,
               fd.PIKToggle, fd.CallProtection
        FROM facility_data fd
        LEFT JOIN {database_name}.CURATED.DIM_CREDIT_BORROWER b ON fd.BorrowerName = b.BorrowerName
    """).collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  DIM_CREDIT_FACILITY: {count} facilities")


BORROWER_NARRATIVES = {
    'Orion Retail Group': {
        'growth_trend': [-0.02, -0.01, 0.01, 0.02, 0.03, -0.01, -0.03, -0.05, -0.06, -0.08, -0.09, -0.10],
        'margin_mult': [0.92, 0.93, 0.95, 0.97, 1.0, 0.98, 0.95, 0.92, 0.90, 0.88, 0.86, 0.85],
        'debt_mult': [5.8, 5.6, 5.2, 4.8, 4.5, 4.8, 5.2, 5.5, 5.7, 5.9, 6.0, 6.1],
    },
    'Pinnacle Software Solutions': {
        'growth_trend': [0.03, 0.02, 0.02, 0.01, 0.01, 0.0, -0.01, -0.01, -0.02, -0.02, -0.02, -0.03],
        'margin_mult': [1.02, 1.01, 1.0, 0.99, 0.98, 0.98, 0.97, 0.97, 0.96, 0.96, 0.95, 0.95],
        'debt_mult': [4.0, 4.1, 4.2, 4.3, 4.5, 4.6, 4.7, 4.8, 4.9, 5.0, 5.0, 5.1],
    },
    'Velocity Logistics Holdings': {
        'growth_trend': [0.01, 0.0, -0.01, -0.02, -0.02, -0.03, -0.04, -0.05, -0.06, -0.07, -0.08, -0.09],
        'margin_mult': [0.95, 0.96, 0.97, 0.98, 1.0, 0.98, 0.96, 0.94, 0.92, 0.90, 0.88, 0.87],
        'debt_mult': [4.5, 4.4, 4.3, 4.2, 4.0, 4.3, 4.6, 4.9, 5.1, 5.3, 5.5, 5.7],
    },
    'Meridian Healthcare Group': {
        'growth_trend': [0.02, 0.01, 0.01, 0.0, 0.0, -0.01, -0.02, -0.03, -0.03, -0.04, -0.04, -0.05],
        'margin_mult': [0.97, 0.98, 0.99, 1.0, 1.0, 0.99, 0.97, 0.96, 0.95, 0.94, 0.93, 0.92],
        'debt_mult': [4.2, 4.1, 4.0, 3.9, 3.8, 4.0, 4.3, 4.5, 4.8, 5.0, 5.1, 5.2],
    },
    'Redwood Hospitality Group': {
        'growth_trend': [-0.01, 0.0, 0.01, 0.02, 0.02, 0.0, -0.02, -0.03, -0.04, -0.06, -0.07, -0.08],
        'margin_mult': [0.93, 0.94, 0.96, 0.98, 1.0, 0.98, 0.95, 0.93, 0.91, 0.89, 0.87, 0.86],
        'debt_mult': [5.5, 5.3, 5.0, 4.7, 4.5, 4.8, 5.1, 5.3, 5.5, 5.7, 5.8, 5.9],
    },
}


def build_fact_credit_borrower_financials(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    table_name = f"{database_name}.CURATED.FACT_CREDIT_BORROWER_FINANCIALS"

    borrowers = session.sql(f"""
        SELECT BorrowerID, BorrowerName, Revenue_MM, EBITDA_MM
        FROM {database_name}.CURATED.DIM_CREDIT_BORROWER
    """).collect()

    quarters_back = 4 if test_mode else 12
    rows = []
    for borrower in borrowers:
        b_id = borrower['BORROWERID']
        b_name = borrower['BORROWERNAME']
        base_rev = float(borrower['REVENUE_MM'])
        base_ebitda = float(borrower['EBITDA_MM'])
        narrative = BORROWER_NARRATIVES.get(b_name)

        for q in range(quarters_back):
            report_date = date.today().replace(day=1) - timedelta(days=90 * q)
            report_date = report_date.replace(day=1)

            if narrative:
                idx = min(q, len(narrative['growth_trend']) - 1)
                growth = 1.0 + narrative['growth_trend'][idx] + random.uniform(-0.01, 0.01)
                m_mult = narrative['margin_mult'][idx]
                d_mult = narrative['debt_mult'][idx]
                rev = round(base_rev * growth / 4, 2)
                ebitda = round(base_ebitda * growth * m_mult * random.uniform(0.97, 1.03) / 4, 2)
                margin = round((ebitda / rev) * 100, 2) if rev > 0 else 0
                net_debt = round(base_ebitda * d_mult, 2)
                total_lev = round(net_debt / (base_ebitda * growth), 2) if base_ebitda * growth > 0 else 0
                net_lev = round(total_lev * random.uniform(0.88, 0.93), 2)
                icr = round(ebitda / (net_debt * random.uniform(0.07, 0.09) / 4), 2) if net_debt > 0 else 99.0
                fccr = round(icr * random.uniform(0.75, 0.88), 2)
                fcf = round(ebitda * random.uniform(0.25, 0.50), 2)
                capex = round(rev * random.uniform(0.04, 0.07), 2)
                cash = round(base_rev * random.uniform(0.02, 0.06), 2)
                revolver_avail = round(random.uniform(30, 150), 2)
            else:
                growth = 1.0 + random.uniform(-0.08, 0.06) - (q * 0.002)
                rev = round(base_rev * growth / 4, 2)
                ebitda = round(base_ebitda * growth * random.uniform(0.9, 1.1) / 4, 2)
                margin = round((ebitda / rev) * 100, 2) if rev > 0 else 0
                net_debt = round(base_ebitda * random.uniform(3.5, 6.0), 2)
                total_lev = round(net_debt / (base_ebitda * growth), 2) if base_ebitda * growth > 0 else 0
                net_lev = round(total_lev * random.uniform(0.85, 0.95), 2)
                icr = round(ebitda / (net_debt * random.uniform(0.06, 0.10) / 4), 2) if net_debt > 0 else 99.0
                fccr = round(icr * random.uniform(0.7, 0.9), 2)
                fcf = round(ebitda * random.uniform(0.3, 0.6), 2)
                capex = round(rev * random.uniform(0.03, 0.08), 2)
                cash = round(base_rev * random.uniform(0.02, 0.08), 2)
                revolver_avail = round(random.uniform(50, 250), 2)

            rows.append({
                'BORROWERID': b_id, 'BORROWERNAME': b_name,
                'REPORTDATE': str(report_date), 'REVENUE_MM': rev, 'EBITDA_MM': ebitda,
                'EBITDA_MARGIN': margin, 'NETDEBT_MM': net_debt, 'TOTALLEVERAGE': total_lev,
                'NETLEVERAGE': net_lev, 'INTERESTCOVERAGE': icr, 'FIXEDCHARGECOVERAGE': fccr,
                'FREECASHFLOW_MM': fcf, 'CAPEX_MM': capex, 'CASHONHAND_MM': cash,
                'REVOLVERAVAILABILITY_MM': revolver_avail
            })

    df = session.create_dataframe(rows)
    df.write.mode("overwrite").save_as_table(table_name)
    session.sql(f"ALTER TABLE {table_name} SET COMMENT = 'Quarterly financial metrics for private credit borrowers'").collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  FACT_CREDIT_BORROWER_FINANCIALS: {count} quarterly records")


COVENANT_NARRATIVES = {
    'Orion Retail Group': {
        'Max Total Leverage': {
            'threshold': 5.50,
            'actuals': [6.33, 6.10, 5.82, 5.55, 5.20, 5.10, 5.05, 5.00],
        },
        'Min Interest Coverage': {
            'threshold': 1.80,
            'actuals': [1.52, 1.60, 1.72, 1.82, 1.95, 2.05, 2.10, 2.15],
        },
        'Min Fixed Charge Coverage': {
            'threshold': 1.20,
            'actuals': [1.02, 1.08, 1.15, 1.22, 1.32, 1.38, 1.42, 1.45],
        },
        'Max CapEx': {
            'threshold': 95.0,
            'actuals': [108.5, 103.0, 97.5, 93.0, 88.0, 85.0, 83.0, 80.0],
        },
    },
    'Velocity Logistics Holdings': {
        'Max Total Leverage': {
            'threshold': 5.25,
            'actuals': [5.68, 5.45, 5.20, 5.05, 4.90, 4.85, 4.80, 4.75],
        },
        'Min Interest Coverage': {
            'threshold': 2.00,
            'actuals': [2.05, 2.10, 2.15, 2.25, 2.30, 2.35, 2.40, 2.45],
        },
        'Min Fixed Charge Coverage': {
            'threshold': 1.35,
            'actuals': [1.28, 1.32, 1.38, 1.42, 1.48, 1.50, 1.52, 1.55],
        },
        'Max CapEx': {
            'threshold': 78.0,
            'actuals': [76.0, 74.0, 73.0, 72.0, 71.0, 70.0, 69.0, 68.0],
        },
    },
    'Redwood Hospitality Group': {
        'Min Fixed Charge Coverage': {
            'threshold': 1.15,
            'actuals': [1.11, 1.13, 1.18, 1.22, 1.28, 1.32, 1.35, 1.38],
        },
    },
    'Meridian Healthcare Group': {
        'Max Total Leverage': {
            'threshold': 5.20,
            'actuals': [5.12, 5.05, 4.95, 4.88, 4.80, 4.75, 4.70, 4.65],
        },
        'Min Interest Coverage': {
            'threshold': 1.75,
            'actuals': [1.78, 1.82, 1.88, 1.92, 1.98, 2.02, 2.05, 2.08],
        },
        'Min Fixed Charge Coverage': {
            'threshold': 1.25,
            'actuals': [1.28, 1.30, 1.35, 1.38, 1.42, 1.45, 1.48, 1.50],
        },
        'Max CapEx': {
            'threshold': 85.0,
            'actuals': [80.0, 78.0, 76.0, 74.0, 73.0, 72.0, 71.0, 70.0],
        },
    },
    'Pinnacle Software Solutions': {
        'Min Interest Coverage': {
            'threshold': 2.30,
            'actuals': [2.15, 2.20, 2.35, 2.42, 2.50, 2.55, 2.58, 2.60],
        },
    },
    'Sterling Manufacturing Corp': {
        'Min Fixed Charge Coverage': {
            'threshold': 1.30,
            'actuals': [1.35, 1.38, 1.42, 1.45, 1.48, 1.50, 1.52, 1.55],
        },
    },
}


def build_fact_credit_covenant_tracking(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED + 1)
    table_name = f"{database_name}.CURATED.FACT_CREDIT_COVENANT_TRACKING"

    facilities = session.sql(f"""
        SELECT f.FacilityID, f.BorrowerID, f.BorrowerName, f.FacilityType
        FROM {database_name}.CURATED.DIM_CREDIT_FACILITY f
        WHERE f.FacilityType IN ('Term Loan B', 'Unitranche')
    """).collect()

    covenant_types = [
        ('Max Total Leverage', 5.0, 7.0),
        ('Min Interest Coverage', 1.5, 2.5),
        ('Min Fixed Charge Coverage', 1.0, 1.5),
        ('Max CapEx', 50, 150),
    ]

    quarters_back = 4 if test_mode else 8
    rows = []
    for fac in facilities:
        fac_id = fac['FACILITYID']
        b_id = fac['BORROWERID']
        b_name = fac['BORROWERNAME']
        cov_narrative = COVENANT_NARRATIVES.get(b_name, {})

        for cov_type, cov_min, cov_max in covenant_types:
            cov_override = cov_narrative.get(cov_type)

            if cov_override:
                threshold = cov_override['threshold']
            else:
                threshold = round(random.uniform(cov_min, cov_max), 2)

            for q in range(quarters_back):
                test_date = date.today().replace(day=1) - timedelta(days=90 * q)
                test_date = test_date.replace(day=1)

                if cov_override and q < len(cov_override['actuals']):
                    actual = round(cov_override['actuals'][q] + random.uniform(-0.02, 0.02), 2)
                    if 'Max' in cov_type:
                        headroom = round(((threshold - actual) / threshold) * 100, 2)
                        breach = actual > threshold
                    else:
                        headroom = round(((actual - threshold) / threshold) * 100, 2)
                        breach = actual < threshold
                else:
                    if 'Max' in cov_type:
                        actual = round(threshold * random.uniform(0.75, 0.92), 2)
                        headroom = round(((threshold - actual) / threshold) * 100, 2)
                        breach = actual > threshold
                    else:
                        actual = round(threshold * random.uniform(1.08, 1.30), 2)
                        headroom = round(((actual - threshold) / threshold) * 100, 2)
                        breach = actual < threshold

                waiver_req = breach and random.random() > 0.3
                waiver_granted = waiver_req and random.random() > 0.4
                equity_cure = breach and not waiver_granted and random.random() > 0.5

                if breach:
                    status = 'Breach'
                    if waiver_granted:
                        status = 'Waiver Granted'
                    elif equity_cure:
                        status = 'Equity Cure'
                elif headroom < 10:
                    status = 'Tight'
                else:
                    status = 'Compliant'

                notes = ''
                if breach:
                    notes = f'{cov_type} breach of {round(abs(actual - threshold), 2)} at {test_date}'
                elif headroom < 10:
                    notes = f'{cov_type} headroom narrowing - monitor closely'

                rows.append({
                    'FACILITYID': fac_id, 'BORROWERID': b_id, 'BORROWERNAME': b_name,
                    'COVENANTTYPE': cov_type, 'COVENANTTHRESHOLD': threshold,
                    'ACTUALVALUE': actual, 'HEADROOM_PCT': headroom,
                    'TESTDATE': str(test_date), 'STATUS': status, 'BREACHFLAG': breach,
                    'WAIVERREQUESTED': waiver_req, 'WAIVERGRANTED': waiver_granted,
                    'EQUITYCUREAVAILABLE': equity_cure, 'NOTES': notes
                })

    df = session.create_dataframe(rows)
    df.write.mode("overwrite").save_as_table(table_name)
    session.sql(f"ALTER TABLE {table_name} SET COMMENT = 'Covenant compliance tracking for credit facilities'").collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  FACT_CREDIT_COVENANT_TRACKING: {count} covenant test records")


def build_fact_credit_deal_pipeline(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    table_name = f"{database_name}.CURATED.FACT_CREDIT_DEAL_PIPELINE"

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            DealID INT IDENTITY(1,1) PRIMARY KEY,
            TargetName VARCHAR(255),
            Sector VARCHAR(100),
            SubSector VARCHAR(100),
            Sponsor VARCHAR(100),
            DealType VARCHAR(50),
            FacilityType VARCHAR(50),
            DealSize_MM DECIMAL(12,2),
            Spread_BPS INT,
            ExpectedLeverage DECIMAL(6,2),
            DealStage VARCHAR(50),
            ExpectedClose DATE
        )
        COMMENT = 'Private credit deal pipeline'
    """).collect()

    values_rows = []
    for d in CREDIT_DEAL_PIPELINE:
        values_rows.append(
            f"('{d['target']}', '{d['sector']}', '{d['sub_sector']}', '{d['sponsor']}', "
            f"'{d['deal_type']}', '{d['facility_type']}', {d['size_mm']}, {d['spread_bps']}, "
            f"{d['leverage']}, '{d['stage']}', '{d['expected_close']}')"
        )
    values_clause = ", ".join(values_rows)

    session.sql(f"""
        INSERT INTO {table_name}
        (TargetName, Sector, SubSector, Sponsor, DealType, FacilityType,
         DealSize_MM, Spread_BPS, ExpectedLeverage, DealStage, ExpectedClose)
        VALUES {values_clause}
    """).collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  FACT_CREDIT_DEAL_PIPELINE: {count} pipeline deals")


def build_credit_agreements_corpus(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED + 2)
    table_name = f"{database_name}.CURATED.CREDIT_AGREEMENTS_CORPUS"

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            DOCUMENT_ID VARCHAR(64) PRIMARY KEY,
            FacilityID INT,
            BorrowerName VARCHAR(255),
            DOCUMENT_TITLE VARCHAR(500),
            DOCUMENT_TYPE VARCHAR(50),
            DOCUMENT_TEXT VARCHAR(16777216),
            TOKEN_COUNT INT,
            PUBLISH_DATE DATE
        )
        COMMENT = 'Credit agreement documents and amendments'
    """).collect()

    facilities = session.sql(f"""
        SELECT f.FacilityID, f.BorrowerName, f.FacilityType, f.Commitment_MM,
               f.Spread_BPS, f.Floor_BPS, f.MaturityDate, f.OriginationDate,
               f.PIKToggle, f.CallProtection,
               b.Sector, b.Sponsor, b.CreditRating
        FROM {database_name}.CURATED.DIM_CREDIT_FACILITY f
        JOIN {database_name}.CURATED.DIM_CREDIT_BORROWER b ON f.BorrowerID = b.BorrowerID
        WHERE f.FacilityType IN ('Term Loan B', 'Unitranche')
    """).collect()

    rows = []
    for fac in facilities:
        fac_id = fac['FACILITYID']
        borrower = fac['BORROWERNAME']
        fac_type = fac['FACILITYTYPE']
        commitment = float(fac['COMMITMENT_MM'])
        spread = int(fac['SPREAD_BPS'])
        floor = int(fac['FLOOR_BPS'])
        maturity = fac['MATURITYDATE']
        origination = fac['ORIGINATIONDATE']
        pik = fac['PIKTOGGLE']
        call_prot = fac['CALLPROTECTION']
        sector = fac['SECTOR']
        sponsor = fac['SPONSOR']
        rating = fac['CREDITRATING']

        doc_id = f"CA_{fac_id}"
        pik_section = ""
        if pik:
            pik_section = f"""
### PIK Toggle Provisions
The Borrower may elect to pay interest in kind (PIK) at SOFR + {spread + 200}bps for up to 4 consecutive quarters, subject to:
- Total leverage not exceeding {round(random.uniform(5.5, 7.0), 1)}x at time of election
- No existing Event of Default
- PIK interest compounds quarterly and is added to principal
- Cash pay must resume after 4 consecutive PIK quarters"""

        agreement_text = f"""# Credit Agreement Summary
## {borrower} - {fac_type}

### Parties
- **Borrower**: {borrower}
- **Sponsor**: {sponsor}
- **Administrative Agent**: JPMorgan Chase Bank, N.A.
- **Sector**: {sector}
- **Credit Rating**: {rating}

### Facility Terms
- **Facility Type**: {fac_type}
- **Commitment**: ${commitment}MM
- **Interest Rate**: SOFR + {spread}bps (Floor: {floor}bps)
- **Maturity Date**: {maturity}
- **Origination Date**: {origination}
- **Call Protection**: {call_prot}

### Financial Covenants
1. **Maximum Total Leverage Ratio**: Not to exceed {round(random.uniform(5.0, 6.5), 1)}x, tested quarterly
2. **Minimum Interest Coverage Ratio**: Not less than {round(random.uniform(1.5, 2.5), 1)}x, tested quarterly
3. **Minimum Fixed Charge Coverage Ratio**: Not less than {round(random.uniform(1.0, 1.3), 1)}x, tested quarterly
4. **Maximum Capital Expenditure**: Not to exceed ${round(commitment * random.uniform(0.05, 0.10), 0)}MM per annum

### Equity Cure Provisions
The Sponsor shall have the right to cure financial covenant defaults by contributing equity:
- Maximum {random.randint(2, 4)} cures during the term
- No more than {random.randint(1, 2)} consecutive quarters
- Cure amount added to EBITDA for covenant calculation purposes
- Must be contributed within 15 business days of delivery of compliance certificate
{pik_section}

### Negative Covenants (Key Restrictions)
- **Restricted Payments**: Basket of ${round(commitment * 0.05, 0)}MM plus builder basket
- **Permitted Acquisitions**: Up to ${round(commitment * 0.15, 0)}MM individually, subject to pro forma leverage
- **Asset Dispositions**: Ordinary course sales up to ${round(commitment * 0.03, 0)}MM annually
- **Additional Indebtedness**: Incremental facility of up to ${round(commitment * 0.20, 0)}MM, subject to leverage test

### Events of Default
Standard events of default including payment default, covenant breach (with cure periods), cross-default, change of control, and material adverse effect.

---
Executed: {origination}
"""

        token_count = len(agreement_text.split()) * 1.3
        rows.append({
            'DOCUMENT_ID': doc_id, 'FACILITYID': fac_id, 'BORROWERNAME': borrower,
            'DOCUMENT_TITLE': f'{borrower} - {fac_type} Credit Agreement',
            'DOCUMENT_TYPE': 'Credit Agreement', 'DOCUMENT_TEXT': agreement_text,
            'TOKEN_COUNT': int(token_count), 'PUBLISH_DATE': str(origination)
        })

        if random.random() > 0.5:
            amend_id = f"CA_{fac_id}_A1"
            amend_date = date.today() - timedelta(days=random.randint(30, 365))
            amend_text = f"""# First Amendment to Credit Agreement
## {borrower} - {fac_type}

### Amendment Date: {amend_date.strftime('%d %B %Y')}

### Summary of Amendments
This First Amendment modifies the Credit Agreement dated {origination} between {borrower} (Borrower) and the Administrative Agent.

### Key Modifications
1. **Leverage Covenant Relief**: Maximum Total Leverage Ratio increased to {round(random.uniform(6.0, 7.5), 1)}x for the next {random.randint(2, 4)} quarters
2. **Pricing Grid Adjustment**: Spread increased by {random.randint(25, 75)}bps during covenant relief period
3. **Additional Reporting**: Monthly financial reporting required during amendment period
4. **Amendment Fee**: {random.randint(25, 50)}bps on outstanding commitment

### Conditions Precedent
- Delivery of updated financial projections
- Sponsor support letter confirming continued investment thesis
- Payment of amendment fee

---
Executed: {amend_date}
"""
            amend_token_count = len(amend_text.split()) * 1.3
            rows.append({
                'DOCUMENT_ID': amend_id, 'FACILITYID': fac_id, 'BORROWERNAME': borrower,
                'DOCUMENT_TITLE': f'{borrower} - First Amendment',
                'DOCUMENT_TYPE': 'Amendment', 'DOCUMENT_TEXT': amend_text,
                'TOKEN_COUNT': int(amend_token_count), 'PUBLISH_DATE': str(amend_date)
            })

    df = session.create_dataframe(rows)
    df.write.mode("append").save_as_table(table_name)

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  CREDIT_AGREEMENTS_CORPUS: {count} agreement documents")


COMPLIANCE_CERT_NARRATIVES = {
    'Orion Retail Group': [
        {
            'performance': 'significantly below',
            'commentary': """Revenue declined 5.3% quarter-over-quarter driven by continued softness in brick-and-mortar retail channels and delayed e-commerce integration. EBITDA contracted to 8.3% margin from 8.5% in the prior quarter, reflecting persistent cost pressures despite ongoing restructuring efforts. Total leverage increased further, breaching the covenant threshold for the fourth consecutive quarter.

Management has engaged AlixPartners to conduct a comprehensive operational review. The Board-approved cost reduction program targeting $35MM in annual savings through store rationalization (15-20 closures), corporate headcount reduction (12% of G&A), and supply chain renegotiation has been initiated but savings realization has been slower than projected. Only $8MM of the targeted savings were achieved this quarter.

Ares Management has indicated willingness to provide a further equity cure if needed, but has expressed concern about the pace of operational improvement. Management is targeting a return to covenant compliance by Q3 2026, contingent on the full realization of cost savings and stabilization of same-store sales trends.""",
        },
        {
            'performance': 'below',
            'commentary': """Revenue reflected a 1.8% sequential decline as consumer spending softened. EBITDA margin showed marginal improvement from cost initiatives but leverage deteriorated further against the covenant threshold. Interest coverage remains below the covenant minimum.

Management initiated a cost reduction program in Q3 targeting $25MM in annualized savings. Progress to date includes renegotiation of three key supplier contracts (est. $6MM savings) and a voluntary separation program reducing headcount by 8%. However, these savings have been partially offset by one-time restructuring charges of $4.2MM.

The company requested and received a waiver for the Min Fixed Charge Coverage covenant breach this quarter. Sponsor has confirmed continued support and is evaluating additional equity contribution options.""",
        },
        {
            'performance': 'below',
            'commentary': """Revenue was 0.7% below the prior quarter, with EBITDA margin reflecting compression from input cost inflation and promotional activity to defend market share. Leverage breached the covenant threshold for the second consecutive quarter, though management notes this includes one-time integration costs from the 2024 acquisition.

Management outlined a three-phase operational improvement plan: (1) immediate cost takeout through procurement optimization, (2) store portfolio rationalization targeting underperforming locations, and (3) accelerated e-commerce investment. Phase 1 is expected to deliver $8-10MM in savings by Q1 2026.

An equity cure was exercised for the Min Fixed Charge Coverage test this quarter, utilizing $12MM of the sponsor's committed cure capacity.""",
        },
        {
            'performance': 'in line with revised',
            'commentary': """Revenue was broadly in line with revised (downward) expectations. EBITDA benefited from favorable seasonal mix. However, leverage is trending toward the covenant threshold, and management acknowledges that maintaining compliance will require operational execution in H2 2025.

Same-store sales declined 2.1% as the consumer environment remains challenging. Management is reviewing the store portfolio for optimization opportunities and has engaged consultants to assess the supply chain cost structure.

No covenant breaches this quarter, though headroom on Max Total Leverage has narrowed significantly.""",
        },
        {
            'performance': 'below',
            'commentary': """Revenue represented a 2.7% increase from Q4 2024 but remained below the original budget. EBITDA margin showed improvement from the prior quarter. Leverage provides adequate but narrowing headroom against the covenant threshold.

Management flagged emerging cost pressures from wage inflation and logistics disruptions that may impact margins in coming quarters. The company is exploring procurement efficiencies and has initiated a review of underperforming retail locations.

All covenants remain in compliance with adequate headroom, though the trajectory requires monitoring.""",
        },
        {
            'performance': 'below',
            'commentary': """Revenue was in line with seasonal expectations. Leverage reflects increased borrowing for working capital needs. Management noted seasonal factors and expects improvement in Q1 2025. Cost reduction initiatives are being evaluated.""",
        },
    ],
    'Pinnacle Software Solutions': [
        {
            'performance': 'below',
            'commentary': """Revenue growth decelerated to low single digits as enterprise software spending tightened. EBITDA margins remain healthy above 30% but interest expense has increased materially following the SOFR rate environment. Interest coverage has tightened and breached the covenant minimum this quarter.

Management is actively evaluating the PIK toggle option under the Unitranche facility to preserve cash flow. Thoma Bravo has engaged in discussions with the lending group regarding potential covenant amendment to reflect the current rate environment. The company maintains strong underlying unit economics and a growing ARR base.

The technology sector outlook remains constructive with cybersecurity and AI-driven demand, though near-term macro headwinds are creating budget elongation cycles for enterprise customers.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Revenue was broadly in line with expectations. Margins stable. Interest coverage ratio is tightening as SOFR rates remain elevated, and management is monitoring the trajectory closely.

The company is focused on expanding its cloud-native platform and growing recurring revenue. Customer retention rates remain above 95%. Management is evaluating cost optimization opportunities in non-core operations to improve coverage metrics.

Thoma Bravo has expressed confidence in the medium-term outlook and is supportive of management's strategic direction.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Performance in line with expectations. Revenue growth driven by new logo wins and expansion within existing accounts. EBITDA margin slightly compressed due to investment in sales capacity.

Interest expense remains elevated due to SOFR rates. Management is monitoring the impact on coverage ratios. All covenants remain in compliance. The company is exploring options to optimize the capital structure given the rate environment.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Revenue growth on track. Strong pipeline of enterprise opportunities. EBITDA margins stable. All covenants compliant with adequate headroom. Management focused on operational efficiency and new product development.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Solid quarter with revenue growth and margin stability. All covenants compliant. Leverage trajectory improving. Management executing well on strategic plan.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Revenue and EBITDA in line with budget. All covenants compliant with healthy headroom. Business fundamentals remain strong.""",
        },
    ],
    'Velocity Logistics Holdings': [
        {
            'performance': 'below',
            'commentary': """Revenue declined as supply chain disruption and customer destocking continued to impact volumes. EBITDA margins compressed to 15.5% from cost inflation in fuel and labor. Total leverage has breached the covenant threshold, and FCCR has also deteriorated below the minimum.

KKR has appointed a new COO with extensive logistics turnaround experience. Management has identified $40MM in cost savings through fleet optimization, warehouse consolidation (3 facilities to close), and technology-enabled route optimization. Initial savings of $5MM were realized this quarter.

The sponsor exercised an equity cure for the leverage breach and has received a waiver for the FCCR covenant. A formal operational turnaround plan is being presented to the lending group in April.""",
        },
        {
            'performance': 'below',
            'commentary': """Revenue continued to decline reflecting lower freight volumes and pricing pressure. EBITDA margin compressed further. Leverage and FCCR both breached covenant thresholds for the first time.

Management acknowledged the deterioration is driven by both cyclical and operational factors. The company is conducting a strategic review of its network footprint and has engaged Boston Consulting Group for a cost transformation program. Early findings suggest $30-40MM in addressable savings.

The lending group has been informed of the operational challenges. Waiver discussions for the leverage and FCCR breaches are underway.""",
        },
        {
            'performance': 'below',
            'commentary': """Volumes softened further in Q3 as destocking continued across key verticals. Margins held relatively stable but headroom across all covenants is tight. Management is implementing a fleet efficiency program and renegotiating key customer contracts.

No covenant breaches this quarter, but all metrics are trending in the wrong direction. Management has proactively engaged with the lending group to discuss potential covenant amendments if conditions do not improve.""",
        },
        {
            'performance': 'in line with revised',
            'commentary': """Revenue broadly in line with revised expectations. Margins stable. Covenant headroom is tightening but remains adequate. Management is focused on operational efficiency and customer retention.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Revenue and EBITDA in line with expectations. All covenants compliant. The logistics sector is experiencing some volume softness but management remains confident in the medium-term outlook.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Solid operational performance. Revenue growing moderately. All covenants compliant with adequate headroom. Management executing on strategic plan.""",
        },
    ],
    'Redwood Hospitality Group': [
        {
            'performance': 'below',
            'commentary': """Revenue declined reflecting continued weakness in leisure travel demand and slower-than-expected recovery in group bookings. EBITDA margin compressed. Fixed charge coverage has breached the covenant minimum as interest expense and maintenance CapEx weigh on coverage.

Apollo Global is reviewing options including asset dispositions (2-3 underperforming properties) and a targeted cost reduction program. Management expects seasonal improvement in Q2/Q3 2026 and is focused on revenue management optimization and labor efficiency.

A waiver has been requested and granted for the FCCR covenant breach this quarter.""",
        },
        {
            'performance': 'below',
            'commentary': """Revenue below expectations as business travel recovery stalled. EBITDA margins compressed. FCCR is tight and close to the covenant threshold. Management is implementing revenue management system upgrades and labor scheduling optimization.

No covenant breaches this quarter, but headroom is thin on fixed charge coverage. Management is monitoring the situation closely.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Revenue in line with seasonal expectations. Leisure travel demand solid. Group bookings recovering gradually. All covenants compliant. Management focused on occupancy rates and average daily rate optimization.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Revenue and EBITDA in line with expectations. All covenants compliant. Hospitality sector showing steady recovery. Management investing in property upgrades and digital booking capabilities.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Performance in line with expectations. All covenants compliant. Management executing on growth strategy and property portfolio optimization.""",
        },
        {
            'performance': 'in line with',
            'commentary': """Revenue and EBITDA in line with budget. Covenants compliant. Business fundamentals stable.""",
        },
    ],
}


def build_compliance_certs_corpus(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED + 3)
    table_name = f"{database_name}.CURATED.COMPLIANCE_CERTS_CORPUS"

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            DOCUMENT_ID VARCHAR(64) PRIMARY KEY,
            BorrowerID INT,
            BorrowerName VARCHAR(255),
            DOCUMENT_TITLE VARCHAR(500),
            DOCUMENT_TYPE VARCHAR(50),
            DOCUMENT_TEXT VARCHAR(16777216),
            ReportPeriod DATE,
            TOKEN_COUNT INT,
            PUBLISH_DATE DATE
        )
        COMMENT = 'Quarterly compliance certificates from borrowers'
    """).collect()

    borrowers = session.sql(f"""
        SELECT b.BorrowerID, b.BorrowerName, b.Sector, b.Sponsor, b.CreditRating
        FROM {database_name}.CURATED.DIM_CREDIT_BORROWER b
    """).collect()

    financials = session.sql(f"""
        SELECT BORROWERID, REPORTDATE, REVENUE_MM, EBITDA_MM, EBITDA_MARGIN,
               TOTALLEVERAGE, INTERESTCOVERAGE, FIXEDCHARGECOVERAGE,
               NETDEBT_MM, CASHONHAND_MM, REVOLVERAVAILABILITY_MM
        FROM {database_name}.CURATED.FACT_CREDIT_BORROWER_FINANCIALS
    """).collect()
    fin_lookup = {}
    for f in financials:
        key = (f['BORROWERID'], str(f['REPORTDATE'])[:7])
        fin_lookup[key] = f

    covenants = session.sql(f"""
        SELECT BORROWERID, TESTDATE, COVENANTTYPE, COVENANTTHRESHOLD,
               ACTUALVALUE, HEADROOM_PCT, STATUS
        FROM {database_name}.CURATED.FACT_CREDIT_COVENANT_TRACKING
    """).collect()
    cov_lookup = {}
    for c in covenants:
        key = (c['BORROWERID'], str(c['TESTDATE'])[:7], c['COVENANTTYPE'])
        cov_lookup[key] = c

    quarters_back = 2 if test_mode else 6
    rows = []
    for borrower in borrowers:
        b_id = borrower['BORROWERID']
        b_name = borrower['BORROWERNAME']
        sector = borrower['SECTOR']
        sponsor = borrower['SPONSOR']
        rating = borrower['CREDITRATING']

        for q in range(quarters_back):
            report_date = date.today().replace(day=1) - timedelta(days=90 * q)
            report_date = report_date.replace(day=1)
            quarter_label = f"Q{(report_date.month - 1) // 3 + 1} {report_date.year}"
            doc_id = f"CC_{b_id}_{report_date.strftime('%Y%m')}"
            date_key = report_date.strftime('%Y-%m')

            fin = fin_lookup.get((b_id, date_key))
            if fin:
                revenue = round(float(fin['REVENUE_MM']) * 4, 1)
                ebitda = round(float(fin['EBITDA_MM']) * 4, 1)
                net_debt = round(float(fin['NETDEBT_MM']), 1)
                cash = round(float(fin['CASHONHAND_MM']), 1)
                revolver = round(float(fin['REVOLVERAVAILABILITY_MM']), 1)
                leverage = round(float(fin['TOTALLEVERAGE']), 2)
                icr = round(float(fin['INTERESTCOVERAGE']), 2)
                fccr = round(float(fin['FIXEDCHARGECOVERAGE']), 2)
            else:
                revenue = round(random.uniform(400, 3200), 1)
                ebitda = round(random.uniform(100, 500), 1)
                net_debt = round(random.uniform(300, 2000), 1)
                cash = round(random.uniform(20, 200), 1)
                revolver = round(random.uniform(30, 250), 1)
                leverage = round(random.uniform(3.5, 6.5), 2)
                icr = round(random.uniform(1.5, 3.5), 2)
                fccr = round(random.uniform(1.0, 2.0), 2)

            lev_cov = cov_lookup.get((b_id, date_key, 'Max Total Leverage'))
            icr_cov = cov_lookup.get((b_id, date_key, 'Min Interest Coverage'))
            fccr_cov = cov_lookup.get((b_id, date_key, 'Min Fixed Charge Coverage'))

            if lev_cov:
                lev_threshold = round(float(lev_cov['COVENANTTHRESHOLD']), 1)
                lev_actual = round(float(lev_cov['ACTUALVALUE']), 2)
                lev_headroom = round(float(lev_cov['HEADROOM_PCT']), 1)
                lev_status = str(lev_cov['STATUS']).upper().replace(' ', '_')
                if lev_status not in ('COMPLIANT', 'TIGHT'):
                    lev_status = 'BREACH'
            else:
                lev_threshold = round(leverage * random.uniform(1.10, 1.20), 1)
                lev_actual = leverage
                lev_headroom = round(((lev_threshold - leverage) / lev_threshold) * 100, 1)
                lev_status = 'COMPLIANT' if leverage <= lev_threshold else 'BREACH'

            if icr_cov:
                icr_threshold = round(float(icr_cov['COVENANTTHRESHOLD']), 1)
                icr_actual = round(float(icr_cov['ACTUALVALUE']), 2)
                icr_headroom = round(float(icr_cov['HEADROOM_PCT']), 1)
                icr_status = str(icr_cov['STATUS']).upper().replace(' ', '_')
                if icr_status not in ('COMPLIANT', 'TIGHT'):
                    icr_status = 'BREACH'
            else:
                icr_threshold = round(icr * random.uniform(0.75, 0.90), 1)
                icr_actual = icr
                icr_headroom = round(((icr - icr_threshold) / icr_threshold) * 100, 1)
                icr_status = 'COMPLIANT' if icr >= icr_threshold else 'BREACH'

            if fccr_cov:
                fccr_threshold = round(float(fccr_cov['COVENANTTHRESHOLD']), 1)
                fccr_actual = round(float(fccr_cov['ACTUALVALUE']), 2)
                fccr_headroom = round(float(fccr_cov['HEADROOM_PCT']), 1)
                fccr_status = str(fccr_cov['STATUS']).upper().replace(' ', '_')
                if fccr_status not in ('COMPLIANT', 'TIGHT'):
                    fccr_status = 'BREACH'
            else:
                fccr_threshold = round(fccr * random.uniform(0.75, 0.90), 1)
                fccr_actual = fccr
                fccr_headroom = round(((fccr - fccr_threshold) / fccr_threshold) * 100, 1)
                fccr_status = 'COMPLIANT' if fccr >= fccr_threshold else 'BREACH'

            cert_narrative = COMPLIANCE_CERT_NARRATIVES.get(b_name)
            if cert_narrative and q < len(cert_narrative):
                perf_text = cert_narrative[q]['performance']
                commentary_text = cert_narrative[q]['commentary']
            else:
                avg_headroom = (lev_headroom + icr_headroom + fccr_headroom) / 3
                if avg_headroom > 15:
                    perf_text = 'in line with'
                    commentary_text = f'Business operations continued in line with management expectations during {quarter_label}. Key strategic initiatives remain on track and the company continues to execute against its operating plan. All financial covenants are in compliance with adequate headroom.'
                elif avg_headroom > 5:
                    perf_text = 'broadly in line with'
                    commentary_text = f'Business performance was broadly in line with expectations during {quarter_label}. Management is focused on operational efficiency and monitoring covenant headroom. Cost management initiatives continue and the company maintains adequate liquidity.'
                else:
                    perf_text = 'below'
                    commentary_text = f'Performance during {quarter_label} was below management expectations due to market headwinds. Management is implementing targeted cost reduction measures and operational efficiency improvements. The company is actively monitoring covenant compliance and maintaining dialogue with the lending group.'

            has_breach = any(s == 'BREACH' for s in [lev_status, icr_status, fccr_status])
            default_note = '2. No Event of Default has occurred and is continuing.'
            if has_breach:
                default_note = '2. The Events of Default described below have occurred. Remedial actions are detailed in the Management Commentary section.'

            cert_text = f"""# Compliance Certificate
## {b_name} - {quarter_label}

### Certification
The undersigned, the Chief Financial Officer of {b_name}, hereby certifies to the Administrative Agent and the Lenders that:

1. The financial statements delivered herewith fairly present the financial condition of the Borrower as of the end of {quarter_label}.
{default_note}

### Financial Covenant Compliance

| Covenant | Threshold | Actual | Headroom | Status |
|----------|-----------|--------|----------|--------|
| Max Total Leverage | {lev_threshold}x | {lev_actual}x | {lev_headroom}% | {lev_status} |
| Min Interest Coverage | {icr_threshold}x | {icr_actual}x | {icr_headroom}% | {icr_status} |
| Min Fixed Charge Coverage | {fccr_threshold}x | {fccr_actual}x | {fccr_headroom}% | {fccr_status} |

### Key Financial Metrics
- **Revenue (LTM)**: ${revenue}MM
- **Adjusted EBITDA (LTM)**: ${ebitda}MM
- **Net Debt**: ${net_debt}MM
- **Cash on Hand**: ${cash}MM
- **Revolver Availability**: ${revolver}MM

### Sector Context
- **Sector**: {sector}
- **Sponsor**: {sponsor}
- **Rating**: {rating}

### Management Commentary
Business performance during {quarter_label} was {perf_text} management expectations.

{commentary_text}

---
Certified by: Chief Financial Officer, {b_name}
Date: {(report_date + timedelta(days=45)).strftime('%d %B %Y')}
"""

            token_count = len(cert_text.split()) * 1.3
            rows.append({
                'DOCUMENT_ID': doc_id, 'BORROWERID': b_id, 'BORROWERNAME': b_name,
                'DOCUMENT_TITLE': f'{b_name} Compliance Certificate - {quarter_label}',
                'DOCUMENT_TYPE': 'Compliance Certificate', 'DOCUMENT_TEXT': cert_text,
                'REPORTPERIOD': str(report_date), 'TOKEN_COUNT': int(token_count),
                'PUBLISH_DATE': str(report_date + timedelta(days=45))
            })

    df = session.create_dataframe(rows)
    df.write.mode("append").save_as_table(table_name)

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  COMPLIANCE_CERTS_CORPUS: {count} compliance certificates")


def build_ic_memos_corpus(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED + 4)
    table_name = f"{database_name}.CURATED.IC_MEMOS_CORPUS"

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            DOCUMENT_ID VARCHAR(64) PRIMARY KEY,
            DealID INT,
            TargetName VARCHAR(255),
            DOCUMENT_TITLE VARCHAR(500),
            DOCUMENT_TYPE VARCHAR(50),
            DOCUMENT_TEXT VARCHAR(16777216),
            TOKEN_COUNT INT,
            PUBLISH_DATE DATE
        )
        COMMENT = 'Investment committee memos for credit deal pipeline'
    """).collect()

    deals = session.sql(f"""
        SELECT DealID, TargetName, Sector, SubSector, Sponsor, DealType,
               FacilityType, DealSize_MM, Spread_BPS, ExpectedLeverage,
               DealStage, ExpectedClose
        FROM {database_name}.CURATED.FACT_CREDIT_DEAL_PIPELINE
        WHERE DealStage IN ('Term Sheet', 'Due Diligence', 'Commitment', 'Allocation')
    """).collect()

    rows = []
    for deal in deals:
        deal_id = deal['DEALID']
        target = deal['TARGETNAME']
        sector = deal['SECTOR']
        sub_sector = deal['SUBSECTOR']
        sponsor = deal['SPONSOR']
        deal_type = deal['DEALTYPE']
        fac_type = deal['FACILITYTYPE']
        size = float(deal['DEALSIZE_MM'])
        spread = int(deal['SPREAD_BPS'])
        leverage = float(deal['EXPECTEDLEVERAGE'])
        stage = deal['DEALSTAGE']
        expected_close = deal['EXPECTEDCLOSE']

        doc_id = f"IC_{deal_id}"
        revenue = round(size / leverage * random.uniform(1.5, 2.5), 0)
        ebitda = round(size / leverage, 0)

        ic_text = f"""# Investment Committee Memorandum
## {target} - {fac_type} ({deal_type})

### Deal Summary
| Parameter | Value |
|-----------|-------|
| Target | {target} |
| Sponsor | {sponsor} |
| Sector | {sector} / {sub_sector} |
| Deal Type | {deal_type} |
| Facility | {fac_type} |
| Deal Size | ${size}MM |
| Pricing | SOFR + {spread}bps |
| Expected Leverage | {leverage}x |
| Deal Stage | {stage} |
| Expected Close | {expected_close} |

### Investment Thesis
{target} operates in the {sub_sector} segment of {sector}. The business benefits from {random.choice(['strong recurring revenue', 'long-term contracts', 'high switching costs', 'essential service nature', 'regulatory barriers to entry'])} and {random.choice(['a diversified customer base', 'margin expansion opportunities', 'proven management team', 'attractive unit economics', 'sector tailwinds'])}.

### Sponsor Assessment
{sponsor} has a {"strong" if random.random() > 0.3 else "moderate"} track record in {sector}. The sponsor has committed to a {"conservative" if leverage < 5.0 else "moderate"} capital structure with {leverage}x leverage.

### Financial Overview
- **Revenue (LTM)**: ${revenue}MM
- **EBITDA (LTM)**: ${ebitda}MM
- **EBITDA Margin**: {round((ebitda / revenue) * 100, 1)}%
- **Revenue Growth (3yr CAGR)**: {round(random.uniform(3, 15), 1)}%
- **Free Cash Flow Conversion**: {round(random.uniform(40, 75), 0)}%

### Credit Analysis
**Strengths**:
- {random.choice(['Market leader in niche segment', 'Strong cash flow generation', 'Asset-light business model', 'High barriers to entry'])}
- {random.choice(['Diversified revenue streams', 'Blue-chip customer base', 'Contracted revenue visibility', 'Essential service provider'])}
- {random.choice(['Experienced management team', 'Multiple value creation levers', 'Favourable industry dynamics', 'Strong sponsor support'])}

**Risks**:
- {random.choice(['Customer concentration risk', 'Cyclical demand exposure', 'Integration execution risk', 'Regulatory change risk'])}
- {random.choice(['Margin pressure from competition', 'Working capital volatility', 'Technology disruption risk', 'Key person dependency'])}

### Recommendation
{"APPROVE" if random.random() > 0.2 else "APPROVE WITH CONDITIONS"} - The transaction offers an attractive risk-adjusted return at SOFR + {spread}bps with {leverage}x leverage. {"Covenant package provides adequate downside protection." if leverage < 5.5 else "Recommend enhanced covenant package given elevated leverage."}

---
Prepared by: Credit Research Team
Date: {(date.today() - timedelta(days=random.randint(5, 60))).strftime('%d %B %Y')}
"""

        token_count = len(ic_text.split()) * 1.3
        publish_date = date.today() - timedelta(days=random.randint(5, 60))
        rows.append({
            'DOCUMENT_ID': doc_id, 'DEALID': deal_id, 'TARGETNAME': target,
            'DOCUMENT_TITLE': f'{target} - IC Memo ({deal_type})',
            'DOCUMENT_TYPE': 'IC Memo', 'DOCUMENT_TEXT': ic_text,
            'TOKEN_COUNT': int(token_count), 'PUBLISH_DATE': str(publish_date)
        })

    df = session.create_dataframe(rows)
    df.write.mode("append").save_as_table(table_name)

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]['CNT']
    log_success(f"  IC_MEMOS_CORPUS: {count} IC memos")


def build_credit_tables(session: Session, test_mode: bool = False):
    log_detail("Building Private Credit scenario tables...")

    _run_build_step(build_dim_credit_fund, session, test_mode)
    _run_build_step(build_dim_credit_borrower, session, test_mode)
    _run_build_step(build_dim_credit_facility, session, test_mode)
    _run_build_step(build_fact_credit_borrower_financials, session, test_mode)
    _run_build_step(build_fact_credit_covenant_tracking, session, test_mode)
    _run_build_step(build_fact_credit_deal_pipeline, session, test_mode)
    _run_build_step(build_fact_credit_sector_benchmarks, session, test_mode)

    _run_build_step(build_credit_agreements_corpus, session, test_mode)
    _run_build_step(build_compliance_certs_corpus, session, test_mode)
    _run_build_step(build_ic_memos_corpus, session, test_mode)

    log_success("Private Credit scenario tables built successfully")


TABLE_BUILDERS = {
    'pe_tables': build_pe_tables,
    'credit_tables': build_credit_tables,
    'compliance': lambda session, test_mode=False: (
        _run_build_step(build_fact_compliance_alerts, session),
        _run_build_step(build_fact_pre_screened_replacements, session),
        _run_build_step(generate_demo_compliance_alert, session),
        _run_build_step(generate_concentration_breach_alerts, session),
        _run_build_step(generate_demo_pre_screened_replacements, session),
    ),
    'ml_tables': lambda session, test_mode=False: _build_ml_tables(session),
}


def _build_ml_tables(session):
    """Create ML schema tables (scaffolding for Feature Store / model predictions)."""
    from ai.tools.ml_common import ensure_ml_schema
    from ai.tools.regime_detection import create_regime_prediction_table
    from ai.tools.factor_engine import build_factor_scenario
    from ai.tools.credit_risk import build_credit_risk_scenario
    ensure_ml_schema(session)
    create_regime_prediction_table(session)
    build_factor_scenario(session)
    build_credit_risk_scenario(session)


def build_scenario_data(session: Session, scenario: str):
    """Build scenario-specific tables based on config.SCENARIOS[scenario].required_tables."""
    import config
    scenario_cfg = config.SCENARIOS.get(scenario, {})
    required = scenario_cfg.get('required_tables', [])

    for table_key in required:
        if table_key in ('dimensions', 'fact_tables'):
            continue
        if table_key not in _completed_shared_builds and table_key in TABLE_BUILDERS:
            _run_build_step(TABLE_BUILDERS[table_key], session)
            _completed_shared_builds.add(table_key)

def build_attribution_market_data(session: Session):
    """Build attribution market data foundation tables from Cybersyn.
    
    Must run BEFORE build_factor_exposures (which needs FACT_BENCHMARK_RETURNS).
    
    Creates 5 MARKET_DATA tables:
    - DIM_BENCHMARKS: Benchmark reference data
    - FACT_BENCHMARK_RETURNS: Daily benchmark returns (real ETF prices)
    - FACT_BENCHMARK_SECTOR_WEIGHTS: Benchmark sector allocations
    - FACT_VIX_DAILY: VIX data derived from VIXY ETF prices
    - FACT_SECTOR_RETURNS: Daily sector returns from sector ETFs
    """
    database = config.DATABASE['name']
    market_data = config.DATABASE['schemas']['market_data']
    cybersyn_db = config.REAL_DATA_SOURCES.get('database', 'FINANCIALS_ECONOMICS_ENTERPRISE')
    cybersyn_schema = config.REAL_DATA_SOURCES.get('schema', 'CYBERSYN')
    
    log_detail("Building attribution market data foundation...")
    
    # 1. DIM_BENCHMARKS
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{market_data}.DIM_BENCHMARKS (
        BENCHMARK_ID INT PRIMARY KEY,
        BENCHMARK_NAME VARCHAR(100),
        BENCHMARK_CODE VARCHAR(20),
        DESCRIPTION VARCHAR(500)
    )
    """).collect()
    
    session.sql(f"""
    INSERT INTO {database}.{market_data}.DIM_BENCHMARKS VALUES
        (1, 'S&P 500', 'SPX', 'S&P 500 Index - Primary US large-cap benchmark'),
        (2, 'MSCI ACWI', 'ACWI', 'MSCI All Country World Index - Global benchmark'),
        (3, 'Russell 2000', 'RUT', 'Russell 2000 Index - US small-cap benchmark'),
        (4, 'Nasdaq 100', 'NDX', 'Nasdaq 100 - Technology focused benchmark'),
        (5, 'Bloomberg US Agg', 'AGG', 'Bloomberg US Aggregate Bond Index'),
        (6, 'iBoxx USD HY Corp', 'HYG_IDX', 'High-yield corporate bond benchmark'),
        (7, 'iBoxx USD IG Corp', 'LQD_IDX', 'Investment-grade corporate bond benchmark'),
        (8, 'US Treasury 20Y+', 'TLT_IDX', 'Long-duration US Treasury benchmark'),
        (9, 'Gold Spot', 'GLD_IDX', 'Gold price benchmark'),
        (10, 'MSCI Emerging Markets', 'EEM_IDX', 'Emerging markets equity benchmark')
    """).collect()
    log_detail("  Created: DIM_BENCHMARKS (10 benchmarks)")
    
    # 2. FACT_BENCHMARK_RETURNS - Real daily returns from Cybersyn ETF prices
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{market_data}.FACT_BENCHMARK_RETURNS AS
    WITH etf_mapping AS (
        SELECT COLUMN1 AS BENCHMARK_ID, COLUMN2 AS BENCHMARK_CODE, COLUMN3 AS ETF_TICKER
        FROM VALUES
            (1, 'SPX', 'SPY'), (2, 'ACWI', 'ACWI'), (3, 'RUT', 'IWM'),
            (4, 'NDX', 'QQQ'), (5, 'AGG', 'AGG'), (6, 'HYG_IDX', 'HYG'),
            (7, 'LQD_IDX', 'LQD'), (8, 'TLT_IDX', 'TLT'), (9, 'GLD_IDX', 'GLD'),
            (10, 'EEM_IDX', 'EEM')
    ),
    etf_closes AS (
        SELECT TICKER, DATE, VALUE AS CLOSE_PRICE
        FROM {cybersyn_db}.{cybersyn_schema}.STOCK_PRICE_TIMESERIES
        WHERE TICKER IN ('SPY', 'ACWI', 'IWM', 'QQQ', 'AGG', 'HYG', 'LQD', 'TLT', 'GLD', 'EEM')
          AND VARIABLE = 'post-market_close'
          AND DATE >= DATEADD('year', -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
    ),
    with_returns AS (
        SELECT TICKER, DATE, CLOSE_PRICE,
               (CLOSE_PRICE / LAG(CLOSE_PRICE) OVER (PARTITION BY TICKER ORDER BY DATE)) - 1 AS DAILY_RETURN
        FROM etf_closes
    )
    SELECT r.DATE, m.BENCHMARK_ID, m.BENCHMARK_CODE, ROUND(r.DAILY_RETURN, 6) AS DAILY_RETURN
    FROM with_returns r
    JOIN etf_mapping m ON r.TICKER = m.ETF_TICKER
    WHERE r.DAILY_RETURN IS NOT NULL
    """).collect()
    log_detail("  Created: FACT_BENCHMARK_RETURNS (real ETF returns, 10 benchmarks)")
    
    # 3. FACT_BENCHMARK_SECTOR_WEIGHTS
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{market_data}.FACT_BENCHMARK_SECTOR_WEIGHTS AS
    WITH sectors AS (
        SELECT COLUMN1 AS SECTOR, COLUMN2 AS SPX_WEIGHT, COLUMN3 AS ACWI_WEIGHT FROM VALUES
        ('Information Technology', 0.29, 0.24),
        ('Health Care', 0.13, 0.12),
        ('Financials', 0.13, 0.15),
        ('Consumer Discretionary', 0.10, 0.11),
        ('Communication Services', 0.09, 0.08),
        ('Industrials', 0.08, 0.10),
        ('Consumer Staples', 0.06, 0.07),
        ('Energy', 0.04, 0.05),
        ('Utilities', 0.02, 0.03),
        ('Real Estate', 0.02, 0.02),
        ('Materials', 0.04, 0.03)
    )
    SELECT 
        CURRENT_DATE() AS DATE,
        1 AS BENCHMARK_ID,
        SECTOR,
        SPX_WEIGHT AS BENCHMARK_WEIGHT
    FROM sectors
    UNION ALL
    SELECT 
        CURRENT_DATE() AS DATE,
        2 AS BENCHMARK_ID,
        SECTOR,
        ACWI_WEIGHT AS BENCHMARK_WEIGHT
    FROM sectors
    """).collect()
    log_detail("  Created: FACT_BENCHMARK_SECTOR_WEIGHTS")
    
    # 4. FACT_VIX_DAILY - Real volatility data derived from VIXY ETF prices
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{market_data}.FACT_VIX_DAILY AS
    WITH vixy AS (
        SELECT DATE, VARIABLE, VALUE
        FROM {cybersyn_db}.{cybersyn_schema}.STOCK_PRICE_TIMESERIES
        WHERE TICKER = 'VIXY'
          AND VARIABLE IN ('post-market_close', 'all-day_high', 'all-day_low')
          AND DATE >= DATEADD('year', -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
    ),
    pivoted AS (
        SELECT DATE,
            MAX(CASE WHEN VARIABLE = 'post-market_close' THEN VALUE END) AS VIXY_CLOSE,
            MAX(CASE WHEN VARIABLE = 'all-day_high' THEN VALUE END) AS VIXY_HIGH,
            MAX(CASE WHEN VARIABLE = 'all-day_low' THEN VALUE END) AS VIXY_LOW
        FROM vixy
        GROUP BY DATE
    ),
    scale_factor AS (
        SELECT 20.0 / NULLIF(AVG(VIXY_CLOSE), 0) AS SF FROM pivoted
    )
    SELECT p.DATE,
        ROUND(p.VIXY_CLOSE * s.SF, 2) AS VIX_CLOSE,
        ROUND(p.VIXY_HIGH * s.SF, 2) AS VIX_HIGH,
        ROUND(p.VIXY_LOW * s.SF, 2) AS VIX_LOW
    FROM pivoted p
    CROSS JOIN scale_factor s
    WHERE p.VIXY_CLOSE IS NOT NULL
    """).collect()
    log_detail("  Created: FACT_VIX_DAILY (real VIXY-derived)")
    
    # 5. FACT_SECTOR_RETURNS from Cybersyn sector ETFs
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{market_data}.FACT_SECTOR_RETURNS AS
    WITH sector_etfs AS (
        SELECT COLUMN1 AS TICKER, COLUMN2 AS SECTOR FROM VALUES
        ('XLK', 'Information Technology'),
        ('XLV', 'Health Care'),
        ('XLF', 'Financials'),
        ('XLY', 'Consumer Discretionary'),
        ('XLC', 'Communication Services'),
        ('XLI', 'Industrials'),
        ('XLP', 'Consumer Staples'),
        ('XLE', 'Energy'),
        ('XLU', 'Utilities'),
        ('XLRE', 'Real Estate'),
        ('XLB', 'Materials')
    ),
    etf_prices AS (
        SELECT 
            sp.DATE,
            se.SECTOR,
            sp.VALUE AS CLOSE_PRICE
        FROM {cybersyn_db}.{cybersyn_schema}.STOCK_PRICE_TIMESERIES sp
        JOIN sector_etfs se ON sp.TICKER = se.TICKER
        WHERE sp.VARIABLE = 'post-market_close'
          AND sp.DATE >= DATEADD('year', -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
    ),
    with_lag AS (
        SELECT 
            DATE,
            SECTOR,
            CLOSE_PRICE,
            LAG(CLOSE_PRICE) OVER (PARTITION BY SECTOR ORDER BY DATE) AS PREV_CLOSE
        FROM etf_prices
    )
    SELECT 
        DATE,
        SECTOR,
        ROUND((CLOSE_PRICE - PREV_CLOSE) / NULLIF(PREV_CLOSE, 0), 6) AS SECTOR_RETURN
    FROM with_lag
    WHERE PREV_CLOSE IS NOT NULL
    """).collect()
    log_detail("  Created: FACT_SECTOR_RETURNS (from Cybersyn sector ETFs)")


def build_attribution_tables(session: Session, test_mode: bool = False):
    """Build Attribution Intelligence curated tables.
    
    Requires: build_attribution_market_data() and build_factor_exposures() to have run first.
    
    Creates 7 tables in CURATED schema:
    - FACT_BRINSON_BY_SECTOR: Sector-level Brinson attribution
    - FACT_BRINSON_ATTRIBUTION: Portfolio-level Brinson summary
    - FACT_FACTOR_ATTRIBUTION: Factor contribution analysis (needs FACT_FACTOR_EXPOSURES)
    - V_MACRO_REGIME: Macro regime classification view
    - DIM_STRESS_SCENARIOS: Stress scenario definitions
    - FACT_SCENARIO_SHOCKS: Factor shocks by scenario
    - FACT_HISTORICAL_STRESS_PERIODS: Historical stress period definitions
    
    Note: FACT_HIDDEN_FACTOR_EXPOSURES is built separately by build_hidden_factor_exposures()
    after NLP scoring completes (requires corpus from pipeline execution).
    """
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    
    log_detail("Building Attribution Intelligence curated tables...")
    
    # 6. FACT_BRINSON_BY_SECTOR - Real attribution from actual stock returns
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_BRINSON_BY_SECTOR AS
    WITH month_end_prices AS (
        SELECT SECURITYID, PRICE_DATE, PRICE_CLOSE,
            LAG(PRICE_CLOSE) OVER (PARTITION BY SECURITYID ORDER BY PRICE_DATE) AS PREV_MONTH_CLOSE
        FROM (
            SELECT SECURITYID, PRICE_DATE, PRICE_CLOSE,
                ROW_NUMBER() OVER (PARTITION BY SECURITYID, DATE_TRUNC('month', PRICE_DATE) ORDER BY PRICE_DATE DESC) AS RN
            FROM {database}.MARKET_DATA.FACT_STOCK_PRICES
        )
        WHERE RN = 1
    ),
    stock_monthly_returns AS (
        SELECT SECURITYID, PRICE_DATE,
            (PRICE_CLOSE - PREV_MONTH_CLOSE) / NULLIF(PREV_MONTH_CLOSE, 0) AS STOCK_RETURN
        FROM month_end_prices
        WHERE PREV_MONTH_CLOSE IS NOT NULL
    ),
    position_with_sector AS (
        SELECT
            p.HoldingDate AS DATE,
            p.PortfolioID,
            p.SecurityID,
            p.PortfolioWeight,
            CASE WHEN i.GICS_SECTOR = 'Healthcare' THEN 'Health Care' ELSE i.GICS_SECTOR END AS SECTOR
        FROM {database}.{curated}.FACT_POSITION_DAILY_ABOR p
        JOIN {database}.{curated}.DIM_SECURITY s ON p.SecurityID = s.SecurityID
        JOIN {database}.{curated}.DIM_ISSUER i ON s.IssuerID = i.IssuerID
        WHERE p.HoldingDate >= DATEADD('year', -2, CURRENT_DATE())
    ),
    portfolio_sector_data AS (
        SELECT
            ps.DATE,
            ps.PortfolioID,
            ps.SECTOR,
            SUM(ps.PortfolioWeight) AS PORTFOLIO_WEIGHT,
            SUM(ps.PortfolioWeight * smr.STOCK_RETURN) / NULLIF(SUM(ps.PortfolioWeight), 0) AS PORTFOLIO_SECTOR_RETURN
        FROM position_with_sector ps
        JOIN stock_monthly_returns smr
            ON ps.SecurityID = smr.SECURITYID
            AND DATE_TRUNC('month', ps.DATE) = DATE_TRUNC('month', smr.PRICE_DATE)
        GROUP BY ps.DATE, ps.PortfolioID, ps.SECTOR
    ),
    benchmark_weights AS (
        SELECT bsw.SECTOR, bsw.BENCHMARK_WEIGHT
        FROM {database}.{market_data}.FACT_BENCHMARK_SECTOR_WEIGHTS bsw
        WHERE bsw.BENCHMARK_ID = 1
    ),
    sector_returns AS (
        SELECT DATE, SECTOR, SECTOR_RETURN
        FROM {database}.{market_data}.FACT_SECTOR_RETURNS
    ),
    date_portfolio_spine AS (
        SELECT DISTINCT DATE, PortfolioID FROM portfolio_sector_data
    ),
    nearest_trading_day AS (
        SELECT
            dp.DATE AS POSITION_DATE,
            bw.SECTOR,
            sr.DATE AS TRADING_DATE,
            sr.SECTOR_RETURN,
            ROW_NUMBER() OVER (PARTITION BY dp.DATE, bw.SECTOR ORDER BY sr.DATE DESC) AS RN
        FROM date_portfolio_spine dp
        CROSS JOIN benchmark_weights bw
        JOIN sector_returns sr ON bw.SECTOR = sr.SECTOR AND sr.DATE <= dp.DATE AND sr.DATE >= DATEADD('day', -5, dp.DATE)
    ),
    monthly_sector_etf_returns AS (
        SELECT POSITION_DATE, SECTOR, SECTOR_RETURN
        FROM nearest_trading_day
        WHERE RN = 1
    ),
    all_sector_rows AS (
        SELECT
            dp.DATE,
            dp.PortfolioID,
            bw.SECTOR,
            COALESCE(psd.PORTFOLIO_WEIGHT, 0) AS PORTFOLIO_WEIGHT,
            bw.BENCHMARK_WEIGHT,
            mser.SECTOR_RETURN AS BENCHMARK_SECTOR_RETURN,
            COALESCE(psd.PORTFOLIO_SECTOR_RETURN, mser.SECTOR_RETURN) AS PORTFOLIO_SECTOR_RETURN
        FROM date_portfolio_spine dp
        CROSS JOIN benchmark_weights bw
        LEFT JOIN portfolio_sector_data psd
            ON dp.DATE = psd.DATE AND dp.PortfolioID = psd.PortfolioID AND bw.SECTOR = psd.SECTOR
        JOIN monthly_sector_etf_returns mser ON dp.DATE = mser.POSITION_DATE AND bw.SECTOR = mser.SECTOR
    ),
    benchmark_total AS (
        SELECT DATE, SUM(BENCHMARK_WEIGHT * BENCHMARK_SECTOR_RETURN) AS TOTAL_BM_RETURN
        FROM all_sector_rows
        WHERE PORTFOLIO_WEIGHT >= 0
        GROUP BY DATE
    )
    SELECT
        a.DATE,
        a.PortfolioId,
        a.SECTOR,
        a.PORTFOLIO_WEIGHT,
        a.BENCHMARK_WEIGHT,
        a.PORTFOLIO_SECTOR_RETURN,
        a.BENCHMARK_SECTOR_RETURN,
        ROUND((a.PORTFOLIO_WEIGHT - a.BENCHMARK_WEIGHT) * (a.BENCHMARK_SECTOR_RETURN - bt.TOTAL_BM_RETURN), 10) AS ALLOCATION_EFFECT,
        ROUND(a.BENCHMARK_WEIGHT * (a.PORTFOLIO_SECTOR_RETURN - a.BENCHMARK_SECTOR_RETURN), 10) AS SELECTION_EFFECT,
        ROUND((a.PORTFOLIO_WEIGHT - a.BENCHMARK_WEIGHT) * (a.PORTFOLIO_SECTOR_RETURN - a.BENCHMARK_SECTOR_RETURN), 10) AS INTERACTION_EFFECT
    FROM all_sector_rows a
    JOIN benchmark_total bt ON a.DATE = bt.DATE
    """).collect()
    log_detail("  Created: FACT_BRINSON_BY_SECTOR")
    
    # 7. FACT_BRINSON_ATTRIBUTION - Portfolio-level summary
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_BRINSON_ATTRIBUTION AS
    SELECT 
        DATE,
        PORTFOLIOID,
        SUM(PORTFOLIO_WEIGHT * PORTFOLIO_SECTOR_RETURN) AS TOTAL_PORTFOLIO_RETURN,
        SUM(BENCHMARK_WEIGHT * BENCHMARK_SECTOR_RETURN) AS TOTAL_BENCHMARK_RETURN,
        SUM(PORTFOLIO_WEIGHT * PORTFOLIO_SECTOR_RETURN) - SUM(BENCHMARK_WEIGHT * BENCHMARK_SECTOR_RETURN) AS ACTIVE_RETURN,
        SUM(ALLOCATION_EFFECT) AS ALLOCATION_EFFECT,
        SUM(SELECTION_EFFECT) AS SELECTION_EFFECT,
        SUM(INTERACTION_EFFECT) AS INTERACTION_EFFECT
    FROM {database}.{curated}.FACT_BRINSON_BY_SECTOR
    GROUP BY DATE, PORTFOLIOID
    """).collect()
    log_detail("  Created: FACT_BRINSON_ATTRIBUTION")
    
    # 8. FACT_FACTOR_ATTRIBUTION - Real factor attribution from actual exposures
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_FACTOR_ATTRIBUTION AS
    WITH month_end_prices AS (
        SELECT SECURITYID, PRICE_DATE, PRICE_CLOSE,
            LAG(PRICE_CLOSE) OVER (PARTITION BY SECURITYID ORDER BY PRICE_DATE) AS PREV_MONTH_CLOSE
        FROM (
            SELECT SECURITYID, PRICE_DATE, PRICE_CLOSE,
                ROW_NUMBER() OVER (PARTITION BY SECURITYID, DATE_TRUNC('month', PRICE_DATE) ORDER BY PRICE_DATE DESC) AS RN
            FROM {database}.MARKET_DATA.FACT_STOCK_PRICES
        )
        WHERE RN = 1
    ),
    stock_monthly_returns AS (
        SELECT SECURITYID, PRICE_DATE,
            (PRICE_CLOSE - PREV_MONTH_CLOSE) / NULLIF(PREV_MONTH_CLOSE, 0) AS STOCK_RETURN
        FROM month_end_prices
        WHERE PREV_MONTH_CLOSE IS NOT NULL
    ),
    factor_quintiles AS (
        SELECT
            fe.EXPOSURE_DATE,
            fe.FACTOR_NAME,
            fe.SECURITYID,
            fe.EXPOSURE_VALUE,
            NTILE(5) OVER (PARTITION BY fe.EXPOSURE_DATE, fe.FACTOR_NAME ORDER BY fe.EXPOSURE_VALUE) AS QUINTILE
        FROM {database}.{curated}.FACT_FACTOR_EXPOSURES fe
    ),
    factor_returns AS (
        SELECT
            fq.EXPOSURE_DATE,
            fq.FACTOR_NAME,
            AVG(CASE WHEN fq.QUINTILE = 5 THEN smr.STOCK_RETURN END)
            - AVG(CASE WHEN fq.QUINTILE = 1 THEN smr.STOCK_RETURN END) AS FACTOR_RETURN
        FROM factor_quintiles fq
        JOIN stock_monthly_returns smr
            ON fq.SECURITYID = smr.SECURITYID
            AND DATE_TRUNC('month', fq.EXPOSURE_DATE) = DATE_TRUNC('month', smr.PRICE_DATE)
        GROUP BY fq.EXPOSURE_DATE, fq.FACTOR_NAME
        HAVING FACTOR_RETURN IS NOT NULL
    ),
    position_exposures AS (
        SELECT
            p.HoldingDate AS DATE,
            p.PortfolioID AS PORTFOLIOID,
            fe.FACTOR_NAME,
            SUM(p.PortfolioWeight * fe.EXPOSURE_VALUE) AS PORTFOLIO_FACTOR_EXPOSURE
        FROM {database}.{curated}.FACT_POSITION_DAILY_ABOR p
        JOIN {database}.{curated}.FACT_FACTOR_EXPOSURES fe
            ON p.SecurityID = fe.SECURITYID
            AND DATE_TRUNC('month', p.HoldingDate) = DATE_TRUNC('month', fe.EXPOSURE_DATE)
        WHERE p.HoldingDate >= DATEADD('year', -2, CURRENT_DATE())
        GROUP BY p.HoldingDate, p.PortfolioID, fe.FACTOR_NAME
    )
    SELECT
        pe.DATE,
        pe.PORTFOLIOID,
        pe.FACTOR_NAME,
        ROUND(pe.PORTFOLIO_FACTOR_EXPOSURE, 4) AS PORTFOLIO_FACTOR_EXPOSURE,
        ROUND(fr.FACTOR_RETURN, 6) AS FACTOR_RETURN,
        ROUND(pe.PORTFOLIO_FACTOR_EXPOSURE * fr.FACTOR_RETURN, 6) AS FACTOR_CONTRIBUTION
    FROM position_exposures pe
    JOIN factor_returns fr
        ON DATE_TRUNC('month', pe.DATE) = DATE_TRUNC('month', fr.EXPOSURE_DATE)
        AND pe.FACTOR_NAME = fr.FACTOR_NAME
    """).collect()
    log_detail("  Created: FACT_FACTOR_ATTRIBUTION")
    
    # 9. V_MACRO_REGIME - View for macro regime classification
    session.sql(f"""
    CREATE OR REPLACE VIEW {database}.{curated}.V_MACRO_REGIME AS
    SELECT 
        v.DATE,
        v.VIX_CLOSE,
        br.DAILY_RETURN AS SPX_RETURN,
        LAG(v.VIX_CLOSE, 5) OVER (ORDER BY v.DATE) AS VIX_5D_LAG,
        v.VIX_CLOSE - LAG(v.VIX_CLOSE, 5) OVER (ORDER BY v.DATE) AS VIX_5D_CHANGE,
        CASE 
            WHEN v.VIX_CLOSE < 15 THEN 'LOW_VOL'
            WHEN v.VIX_CLOSE BETWEEN 15 AND 20 THEN 'NORMAL'
            WHEN v.VIX_CLOSE BETWEEN 20 AND 30 THEN 'ELEVATED'
            ELSE 'HIGH_VOL'
        END AS VOLATILITY_REGIME,
        CASE 
            WHEN br.DAILY_RETURN > 0.005 AND v.VIX_CLOSE < 20 THEN 'RISK_ON'
            WHEN br.DAILY_RETURN < -0.005 OR v.VIX_CLOSE > 25 THEN 'RISK_OFF'
            WHEN ABS(v.VIX_CLOSE - LAG(v.VIX_CLOSE, 5) OVER (ORDER BY v.DATE)) > 5 THEN 'TRANSITIONAL'
            ELSE 'NEUTRAL'
        END AS MARKET_REGIME
    FROM {database}.{market_data}.FACT_VIX_DAILY v
    LEFT JOIN {database}.{market_data}.FACT_BENCHMARK_RETURNS br 
        ON v.DATE = br.DATE AND br.BENCHMARK_CODE = 'SPX'
    """).collect()
    log_detail("  Created: V_MACRO_REGIME")
    
    # Note: International macro indicators (policy rates, FX rates, economic indicators) 
    # are built as physical tables in MARKET_DATA schema by market_data.py:
    # - FACT_POLICY_RATES (BIS central bank rates)
    # - FACT_FX_RATES (major currency pairs vs USD)
    # - FACT_ECONOMIC_INDICATORS (FRED US economic data)
    
    # 11. DIM_STRESS_SCENARIOS
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.DIM_STRESS_SCENARIOS (
        SCENARIO_ID INT PRIMARY KEY,
        SCENARIO_NAME VARCHAR(100),
        SCENARIO_TYPE VARCHAR(50),
        DESCRIPTION VARCHAR(500),
        SEVERITY VARCHAR(20),
        HISTORICAL_REFERENCE VARCHAR(200)
    )
    """).collect()
    
    session.sql(f"""
    INSERT INTO {database}.{curated}.DIM_STRESS_SCENARIOS VALUES
        (1, 'Fed Rate Shock +100bp', 'Rate Shock', 'Sudden 100bp increase in Fed Funds rate', 'Moderate', '2022 Fed Tightening'),
        (2, 'Market Crash -20%', 'Market Crash', 'Rapid 20% decline in equity markets', 'Severe', '2020 COVID Crash'),
        (3, 'Credit Spread Widening', 'Credit Crisis', 'Credit spreads widen 200bp across all grades', 'Severe', '2008 Financial Crisis'),
        (4, 'USD Strengthening +15%', 'FX Shock', 'US Dollar strengthens 15% against major currencies', 'Moderate', '2014-2015 USD Rally'),
        (5, 'Stagflation Scenario', 'Macro Stress', 'Combination of high inflation and recession', 'Extreme', '1970s Stagflation'),
        (6, 'Tech Sector Selloff -30%', 'Sector Crash', 'Technology sector declines 30%', 'Severe', '2022 Tech Correction'),
        (7, 'EM Currency Crisis', 'FX Shock', 'Emerging market currencies decline 25%', 'Severe', '1997 Asian Crisis'),
        (8, 'Oil Price Spike +50%', 'Commodity Shock', 'Oil prices increase 50%', 'Moderate', '2022 Energy Crisis'),
        (9, 'Geopolitical Shock', 'Geopolitical', 'Major geopolitical event causing market uncertainty', 'Severe', '2022 Russia-Ukraine'),
        (10, 'Liquidity Crunch', 'Liquidity Crisis', 'Severe reduction in market liquidity', 'Extreme', '2008 Lehman Collapse')
    """).collect()
    log_detail("  Created: DIM_STRESS_SCENARIOS")
    
    # 12. FACT_SCENARIO_SHOCKS
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_SCENARIO_SHOCKS AS
    WITH scenario_factor_shocks AS (
        SELECT * FROM VALUES
        (1, 'Market', -0.05, 0.85),
        (1, 'Value', 0.02, 0.75),
        (1, 'Growth', -0.08, 0.80),
        (1, 'Quality', 0.01, 0.70),
        (1, 'Momentum', -0.03, 0.65),
        (1, 'Size', -0.02, 0.60),
        (1, 'Volatility', 0.15, 0.90),
        (2, 'Market', -0.20, 0.95),
        (2, 'Value', -0.15, 0.80),
        (2, 'Growth', -0.25, 0.85),
        (2, 'Quality', -0.10, 0.75),
        (2, 'Momentum', -0.18, 0.80),
        (2, 'Size', -0.22, 0.85),
        (2, 'Volatility', 0.80, 0.95),
        (3, 'Market', -0.12, 0.85),
        (3, 'Value', -0.18, 0.80),
        (3, 'Quality', 0.05, 0.70),
        (3, 'Volatility', 0.40, 0.90),
        (4, 'Market', -0.03, 0.70),
        (4, 'Value', 0.02, 0.65),
        (4, 'Growth', -0.05, 0.70),
        (5, 'Market', -0.15, 0.85),
        (5, 'Value', 0.08, 0.75),
        (5, 'Growth', -0.20, 0.85),
        (5, 'Quality', 0.05, 0.70),
        (6, 'Market', -0.10, 0.80),
        (6, 'Growth', -0.30, 0.95),
        (6, 'Momentum', -0.15, 0.80),
        (6, 'Volatility', 0.35, 0.85),
        (7, 'Market', -0.08, 0.75),
        (7, 'Value', -0.05, 0.70),
        (8, 'Market', -0.05, 0.70),
        (8, 'Value', 0.10, 0.75),
        (9, 'Market', -0.12, 0.85),
        (9, 'Quality', 0.05, 0.70),
        (9, 'Volatility', 0.50, 0.90),
        (10, 'Market', -0.25, 0.95),
        (10, 'Value', -0.20, 0.85),
        (10, 'Quality', 0.08, 0.75),
        (10, 'Volatility', 1.00, 0.98)
        AS t(SCENARIO_ID, FACTOR_NAME, FACTOR_SHOCK, CONFIDENCE_LEVEL)
    )
    SELECT * FROM scenario_factor_shocks
    """).collect()
    log_detail("  Created: FACT_SCENARIO_SHOCKS")
    
    # 13. FACT_HISTORICAL_STRESS_PERIODS - Historical market stress events for backtesting
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_HISTORICAL_STRESS_PERIODS AS
    SELECT * FROM VALUES
        ('COVID_CRASH', '2020-02-19'::DATE, '2020-03-23'::DATE, 'COVID-19 pandemic market crash', 33, -0.34, 82.69, 2),
        ('GFC', '2008-09-01'::DATE, '2009-03-09'::DATE, 'Global Financial Crisis', 189, -0.57, 80.86, 10),
        ('TAPER_TANTRUM', '2013-05-22'::DATE, '2013-09-05'::DATE, 'Fed taper announcement shock', 106, -0.06, 21.91, 1),
        ('RATE_HIKE_2022', '2022-01-01'::DATE, '2022-10-12'::DATE, 'Fed aggressive rate hikes', 284, -0.25, 36.45, 1),
        ('BANKING_CRISIS_2023', '2023-03-08'::DATE, '2023-05-01'::DATE, 'SVB/regional bank crisis', 54, -0.08, 30.81, 3)
    AS t(PERIOD_ID, START_DATE, END_DATE, DESCRIPTION, DURATION_DAYS, MARKET_RETURN, PEAK_VIX, LINKED_SCENARIO_ID)
    """).collect()
    log_detail("  Created: FACT_HISTORICAL_STRESS_PERIODS")
    
    log_detail("Attribution Intelligence tables complete")


def build_hidden_factor_exposures(session: Session):
    """Build FACT_HIDDEN_FACTOR_EXPOSURES from NLP scores and market data.
    
    Reads pre-computed staging tables: FACT_TRANSCRIPT_NLP_SCORES, FACT_SEC_SEGMENTS,
    FACT_SEC_FINANCIALS, FACT_ESG_SCORES. No AI calls here — all NLP scoring done
    in market_data pipeline via AI_AGG on the corpus table.
    
    Must run AFTER build_transcript_nlp_scores() (needs AI_EXPOSURE_SCORE, GEO_RISK_SCORE).
    """
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    
    log_detail("Building FACT_HIDDEN_FACTOR_EXPOSURES (5 hidden factors from real data)...")
    
    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_HIDDEN_FACTOR_EXPOSURES AS
    WITH security_issuer AS (
        SELECT s.SecurityID, s.IssuerID, i.GICS_SECTOR, i.SIC_DESCRIPTION
        FROM {database}.{curated}.DIM_SECURITY s
        JOIN {database}.{curated}.DIM_ISSUER i ON s.IssuerID = i.IssuerID
        WHERE s.AssetClass = 'Equity'
    ),

    ai_segment_scores AS (
        SELECT
            seg.IssuerID,
            seg.FISCAL_YEAR,
            QUARTER(seg.PERIOD_END_DATE) AS FISCAL_QUARTER,
            COALESCE(
                SUM(CASE WHEN seg.AI_REVENUE_FLAG = TRUE THEN seg.SEGMENT_REVENUE END)
                / NULLIF(SUM(seg.SEGMENT_REVENUE), 0),
                0
            ) AS AI_SEGMENT_SHARE
        FROM {database}.{market_data}.FACT_SEC_SEGMENTS seg
        WHERE seg.BUSINESS_SEGMENT IS NOT NULL
          AND seg.SEGMENT_REVENUE IS NOT NULL
          AND seg.SEGMENT_REVENUE > 0
        GROUP BY seg.IssuerID, seg.FISCAL_YEAR, QUARTER(seg.PERIOD_END_DATE)
    ),

    ai_transcript_scores AS (
        SELECT IssuerID, FISCAL_YEAR, FISCAL_QUARTER,
            AI_EXPOSURE_SCORE / 100.0 AS AI_TRANSCRIPT_SCORE
        FROM {database}.{market_data}.FACT_TRANSCRIPT_NLP_SCORES
        WHERE AI_EXPOSURE_SCORE IS NOT NULL
    ),

    ai_exposure_raw AS (
        SELECT
            si.SecurityID, si.IssuerID,
            COALESCE(seg.FISCAL_YEAR, ts.FISCAL_YEAR) AS FISCAL_YEAR,
            COALESCE(seg.FISCAL_QUARTER, ts.FISCAL_QUARTER) AS FISCAL_QUARTER,
            CASE
                WHEN seg.AI_SEGMENT_SHARE IS NOT NULL AND ts.AI_TRANSCRIPT_SCORE IS NOT NULL
                    THEN 0.6 * seg.AI_SEGMENT_SHARE + 0.4 * ts.AI_TRANSCRIPT_SCORE
                WHEN seg.AI_SEGMENT_SHARE IS NOT NULL
                    THEN seg.AI_SEGMENT_SHARE
                WHEN ts.AI_TRANSCRIPT_SCORE IS NOT NULL
                    THEN ts.AI_TRANSCRIPT_SCORE
                ELSE NULL
            END AS RAW_SCORE
        FROM security_issuer si
        LEFT JOIN ai_segment_scores seg ON si.IssuerID = seg.IssuerID
        LEFT JOIN ai_transcript_scores ts
            ON si.IssuerID = ts.IssuerID
            AND seg.FISCAL_YEAR = ts.FISCAL_YEAR
            AND seg.FISCAL_QUARTER = ts.FISCAL_QUARTER
    ),

    geo_risk_nlp AS (
        SELECT IssuerID, FISCAL_YEAR, FISCAL_QUARTER,
            GEO_RISK_SCORE / 100.0 AS GEO_RISK_NLP
        FROM {database}.{market_data}.FACT_TRANSCRIPT_NLP_SCORES
        WHERE GEO_RISK_SCORE IS NOT NULL
    ),
    geo_risk_sql AS (
        SELECT
            seg.IssuerID,
            seg.FISCAL_YEAR,
            QUARTER(seg.PERIOD_END_DATE) AS FISCAL_QUARTER,
            SUM(CASE
                WHEN UPPER(seg.GEOGRAPHY) RLIKE '.*(CHINA|HONG KONG|TAIWAN|RUSSIA|IRAN|MIDDLE EAST|ISRAEL).*' THEN seg.SEGMENT_REVENUE
                ELSE 0
            END) / NULLIF(SUM(seg.SEGMENT_REVENUE), 0) AS HIGH_RISK_SHARE,
            SUM(CASE
                WHEN UPPER(seg.GEOGRAPHY) RLIKE '.*(ASIA|LATIN|AFRICA|BRAZIL|INDIA|INDONESIA|MEXICO|TURKEY).*'
                     AND UPPER(seg.GEOGRAPHY) NOT RLIKE '.*(CHINA|HONG KONG|TAIWAN|JAPAN|AUSTRALIA|SOUTH KOREA).*'
                THEN seg.SEGMENT_REVENUE ELSE 0
            END) / NULLIF(SUM(seg.SEGMENT_REVENUE), 0) AS MEDIUM_RISK_SHARE
        FROM {database}.{market_data}.FACT_SEC_SEGMENTS seg
        WHERE seg.GEOGRAPHY IS NOT NULL
          AND seg.SEGMENT_REVENUE IS NOT NULL
          AND seg.SEGMENT_REVENUE > 0
        GROUP BY seg.IssuerID, seg.FISCAL_YEAR, QUARTER(seg.PERIOD_END_DATE)
    ),
    geo_risk_raw AS (
        SELECT
            si.SecurityID, si.IssuerID,
            COALESCE(nlp.FISCAL_YEAR, sql_geo.FISCAL_YEAR) AS FISCAL_YEAR,
            COALESCE(nlp.FISCAL_QUARTER, sql_geo.FISCAL_QUARTER) AS FISCAL_QUARTER,
            COALESCE(
                nlp.GEO_RISK_NLP,
                sql_geo.HIGH_RISK_SHARE * 1.0 + sql_geo.MEDIUM_RISK_SHARE * 0.5,
                NULL
            ) AS RAW_SCORE
        FROM security_issuer si
        LEFT JOIN geo_risk_nlp nlp ON si.IssuerID = nlp.IssuerID
        LEFT JOIN geo_risk_sql sql_geo
            ON si.IssuerID = sql_geo.IssuerID
            AND COALESCE(nlp.FISCAL_YEAR, sql_geo.FISCAL_YEAR) = sql_geo.FISCAL_YEAR
            AND COALESCE(nlp.FISCAL_QUARTER, sql_geo.FISCAL_QUARTER) = sql_geo.FISCAL_QUARTER
    ),

    reshoring_raw AS (
        SELECT
            si.SecurityID, si.IssuerID,
            seg.FISCAL_YEAR,
            QUARTER(seg.PERIOD_END_DATE) AS FISCAL_QUARTER,
            (SUM(CASE
                WHEN UPPER(seg.GEOGRAPHY) RLIKE '.*(UNITED STATES|DOMESTIC|NORTH AMERICA|U\\\\.S\\\\.).*'
                THEN seg.SEGMENT_REVENUE ELSE 0
            END) / NULLIF(SUM(seg.SEGMENT_REVENUE), 0))
            * (1.0 + 0.3 * CASE WHEN si.GICS_SECTOR IN ('Industrials', 'Materials') THEN 1 ELSE 0 END)
            AS RAW_SCORE
        FROM security_issuer si
        JOIN {database}.{market_data}.FACT_SEC_SEGMENTS seg ON si.IssuerID = seg.IssuerID
        WHERE seg.GEOGRAPHY IS NOT NULL
          AND seg.SEGMENT_REVENUE IS NOT NULL
          AND seg.SEGMENT_REVENUE > 0
        GROUP BY si.SecurityID, si.IssuerID, si.GICS_SECTOR, seg.FISCAL_YEAR, QUARTER(seg.PERIOD_END_DATE)
    ),

    rate_convexity_latest AS (
        SELECT
            f.IssuerID,
            f.FISCAL_YEAR,
            f.LONG_TERM_DEBT,
            f.TOTAL_EQUITY,
            f.CURRENT_LIABILITIES,
            f.TOTAL_LIABILITIES,
            f.DEBT_TO_EQUITY,
            COALESCE(f.CURRENT_LIABILITIES, 0) / NULLIF(f.TOTAL_LIABILITIES, 0) AS SHORT_TERM_RATIO,
            ROW_NUMBER() OVER (PARTITION BY f.IssuerID, f.FISCAL_YEAR ORDER BY f.PERIOD_END_DATE DESC) AS RN
        FROM {database}.{market_data}.FACT_SEC_FINANCIALS f
        WHERE f.FISCAL_PERIOD != 'FY'
          AND f.TOTAL_EQUITY IS NOT NULL
    ),
    rate_convexity_raw AS (
        SELECT
            si.SecurityID, si.IssuerID,
            rc.FISCAL_YEAR,
            NULL::INT AS FISCAL_QUARTER,
            COALESCE(rc.DEBT_TO_EQUITY, 0) * COALESCE(rc.SHORT_TERM_RATIO, 0) AS RAW_SCORE
        FROM security_issuer si
        JOIN rate_convexity_latest rc ON si.IssuerID = rc.IssuerID AND rc.RN = 1
    ),

    esg_env AS (
        SELECT SecurityID,
            AVG(SCORE_VALUE) AS ENV_SCORE
        FROM {database}.{curated}.FACT_ESG_SCORES
        WHERE SCORE_TYPE = 'Environmental'
        GROUP BY SecurityID
    ),
    climate_raw AS (
        SELECT
            si.SecurityID, si.IssuerID,
            NULL::INT AS FISCAL_YEAR,
            NULL::INT AS FISCAL_QUARTER,
            (CASE
                WHEN si.GICS_SECTOR = 'Energy' THEN -0.8
                WHEN si.GICS_SECTOR = 'Utilities' THEN -0.4
                WHEN si.GICS_SECTOR = 'Materials' THEN -0.3
                WHEN si.GICS_SECTOR = 'Industrials' THEN -0.1
                WHEN si.GICS_SECTOR = 'Information Technology' THEN 0.3
                WHEN si.GICS_SECTOR = 'Healthcare' THEN 0.1
                WHEN si.GICS_SECTOR = 'Financials' THEN 0.0
                WHEN si.GICS_SECTOR = 'Consumer Staples' THEN -0.1
                WHEN si.GICS_SECTOR = 'Consumer Discretionary' THEN 0.0
                WHEN si.GICS_SECTOR = 'Communication Services' THEN 0.1
                WHEN si.GICS_SECTOR = 'Real Estate' THEN -0.2
                ELSE 0.0
            END) * 0.6
            + COALESCE(esg.ENV_SCORE / 100.0 - 0.5, 0) * 0.4 * 2.0
            AS RAW_SCORE
        FROM security_issuer si
        LEFT JOIN esg_env esg ON si.SecurityID = esg.SecurityID
    ),

    all_factors AS (
        SELECT SecurityID, IssuerID, FISCAL_YEAR, FISCAL_QUARTER, 'AI_Exposure' AS FACTOR_NAME,
            'Exposure to companies with significant AI/ML revenue and investment' AS DESCRIPTION,
            RAW_SCORE
        FROM ai_exposure_raw WHERE RAW_SCORE IS NOT NULL
        UNION ALL
        SELECT SecurityID, IssuerID, FISCAL_YEAR, FISCAL_QUARTER, 'Geopolitical_Risk',
            'Revenue concentration in geopolitically sensitive regions',
            RAW_SCORE
        FROM geo_risk_raw WHERE RAW_SCORE IS NOT NULL
        UNION ALL
        SELECT SecurityID, IssuerID, FISCAL_YEAR, FISCAL_QUARTER, 'Reshoring_Benefit',
            'Benefits from domestic manufacturing and reshoring trends',
            RAW_SCORE
        FROM reshoring_raw WHERE RAW_SCORE IS NOT NULL
        UNION ALL
        SELECT SecurityID, IssuerID, FISCAL_YEAR, FISCAL_QUARTER, 'Rate_Convexity',
            'Non-linear sensitivity to interest rate changes from leverage and short-term debt',
            RAW_SCORE
        FROM rate_convexity_raw WHERE RAW_SCORE IS NOT NULL
        UNION ALL
        SELECT SecurityID, IssuerID, FISCAL_YEAR, FISCAL_QUARTER, 'Climate_Transition',
            'Exposure to green energy transition based on industry and ESG environmental score',
            RAW_SCORE
        FROM climate_raw WHERE RAW_SCORE IS NOT NULL
    ),

    factor_stats AS (
        SELECT FACTOR_NAME, FISCAL_YEAR,
            AVG(RAW_SCORE) AS MEAN_SCORE,
            STDDEV(RAW_SCORE) AS STD_SCORE
        FROM all_factors
        GROUP BY FACTOR_NAME, FISCAL_YEAR
        HAVING STDDEV(RAW_SCORE) > 0
    ),
    z_scored AS (
        SELECT
            af.SecurityID,
            af.IssuerID,
            af.FISCAL_YEAR,
            af.FISCAL_QUARTER,
            af.FACTOR_NAME,
            af.DESCRIPTION,
            GREATEST(-3.0, LEAST(3.0,
                (af.RAW_SCORE - fs.MEAN_SCORE) / fs.STD_SCORE
            )) AS Z_SCORE,
            af.RAW_SCORE
        FROM all_factors af
        JOIN factor_stats fs
            ON af.FACTOR_NAME = fs.FACTOR_NAME
            AND COALESCE(af.FISCAL_YEAR, 2025) = COALESCE(fs.FISCAL_YEAR, 2025)
    ),

    position_dates AS (
        SELECT DISTINCT HoldingDate AS DATE, PortfolioID AS PORTFOLIOID
        FROM {database}.{curated}.FACT_POSITION_DAILY_ABOR
        WHERE HoldingDate >= DATEADD('year', -1, CURRENT_DATE())
    ),
    position_weights AS (
        SELECT HoldingDate, PortfolioID, SecurityID, PortfolioWeight
        FROM {database}.{curated}.FACT_POSITION_DAILY_ABOR
        WHERE HoldingDate >= DATEADD('year', -1, CURRENT_DATE())
    ),
    portfolio_factor_exposures AS (
        SELECT
            pw.HoldingDate AS DATE,
            pw.PortfolioID AS PORTFOLIOID,
            zs.FACTOR_NAME,
            zs.DESCRIPTION,
            SUM(pw.PortfolioWeight * zs.Z_SCORE) AS FACTOR_EXPOSURE,
            COUNT(DISTINCT zs.SecurityID) AS SECURITIES_WITH_SCORE,
            SUM(pw.PortfolioWeight) AS TOTAL_WEIGHT_SCORED,
            POWER(CORR(zs.Z_SCORE, pw.PortfolioWeight), 2) AS EXPLANATORY_POWER_RAW
        FROM position_weights pw
        JOIN z_scored zs ON pw.SecurityID = zs.SecurityID
            AND (zs.FISCAL_YEAR = YEAR(pw.HoldingDate)
                 OR (zs.FISCAL_YEAR IS NULL AND YEAR(pw.HoldingDate) >= 2021))
        GROUP BY pw.HoldingDate, pw.PortfolioID, zs.FACTOR_NAME, zs.DESCRIPTION
    )
    SELECT
        DATE,
        PORTFOLIOID,
        FACTOR_NAME,
        DESCRIPTION,
        ROUND(FACTOR_EXPOSURE, 4) AS FACTOR_EXPOSURE,
        ROUND(GREATEST(0.01, LEAST(0.25,
            COALESCE(EXPLANATORY_POWER_RAW, 0.05) * (SECURITIES_WITH_SCORE / GREATEST(TOTAL_WEIGHT_SCORED * 50, 1))
        )), 4) AS EXPLANATORY_POWER
    FROM portfolio_factor_exposures
    """).collect()
    log_detail("  Created: FACT_HIDDEN_FACTOR_EXPOSURES (real calculations from market data)")


def build_advanced_attribution_views(session: Session):
    """Build advanced attribution analytics views for rolling analysis, anomaly detection, and peer learning.
    
    Requires: build_attribution_tables() to have run first (needs FACT_FACTOR_ATTRIBUTION,
    V_MACRO_REGIME, FACT_BRINSON_BY_SECTOR, DIM_PORTFOLIO).
    """
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    
    log_detail("Building advanced attribution analytics views...")
    
    session.sql(f"""
    CREATE OR REPLACE VIEW {database}.{curated}.V_FACTOR_ROLLING_ANALYTICS AS
    WITH monthly_data AS (
        SELECT
            fa.DATE,
            fa.PORTFOLIOID,
            fa.FACTOR_NAME,
            fa.PORTFOLIO_FACTOR_EXPOSURE AS EXPOSURE,
            fa.FACTOR_RETURN,
            fa.FACTOR_CONTRIBUTION AS CONTRIBUTION
        FROM {database}.{curated}.FACT_FACTOR_ATTRIBUTION fa
    ),
    with_rolling AS (
        SELECT
            md.DATE,
            md.PORTFOLIOID,
            md.FACTOR_NAME,
            md.EXPOSURE,
            md.FACTOR_RETURN,
            md.CONTRIBUTION,
            SUM(md.CONTRIBUTION) OVER (
                PARTITION BY md.PORTFOLIOID, md.FACTOR_NAME ORDER BY md.DATE
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS ROLLING_3M_CONTRIBUTION,
            SUM(md.CONTRIBUTION) OVER (
                PARTITION BY md.PORTFOLIOID, md.FACTOR_NAME ORDER BY md.DATE
                ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
            ) AS ROLLING_6M_CONTRIBUTION,
            AVG(md.EXPOSURE) OVER (
                PARTITION BY md.PORTFOLIOID, md.FACTOR_NAME ORDER BY md.DATE
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS EXPOSURE_3M_AVG,
            AVG(md.EXPOSURE) OVER (
                PARTITION BY md.PORTFOLIOID, md.FACTOR_NAME ORDER BY md.DATE
                ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
            ) AS EXPOSURE_6M_AVG,
            STDDEV(md.EXPOSURE) OVER (
                PARTITION BY md.PORTFOLIOID, md.FACTOR_NAME ORDER BY md.DATE
                ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
            ) AS EXPOSURE_6M_STDDEV,
            SUM(md.CONTRIBUTION) OVER (
                PARTITION BY md.PORTFOLIOID, md.FACTOR_NAME ORDER BY md.DATE
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS CUMULATIVE_CONTRIBUTION
        FROM monthly_data md
    ),
    regime_monthly AS (
        SELECT
            DATE_TRUNC('month', DATE) AS MONTH_DATE,
            MODE(VOLATILITY_REGIME) AS VOLATILITY_REGIME,
            MODE(MARKET_REGIME) AS MARKET_REGIME
        FROM {database}.{curated}.V_MACRO_REGIME
        GROUP BY DATE_TRUNC('month', DATE)
    )
    SELECT
        wr.DATE,
        wr.PORTFOLIOID,
        p.PORTFOLIONAME,
        p.STRATEGY,
        wr.FACTOR_NAME,
        ROUND(wr.EXPOSURE, 4) AS EXPOSURE,
        ROUND(wr.FACTOR_RETURN, 6) AS FACTOR_RETURN,
        ROUND(wr.CONTRIBUTION, 6) AS CONTRIBUTION,
        ROUND(wr.ROLLING_3M_CONTRIBUTION, 6) AS ROLLING_3M_CONTRIBUTION,
        ROUND(wr.ROLLING_6M_CONTRIBUTION, 6) AS ROLLING_6M_CONTRIBUTION,
        ROUND(wr.EXPOSURE_3M_AVG, 4) AS EXPOSURE_3M_AVG,
        ROUND(wr.EXPOSURE_6M_AVG, 4) AS EXPOSURE_6M_AVG,
        ROUND(wr.EXPOSURE - wr.EXPOSURE_6M_AVG, 4) AS EXPOSURE_DRIFT,
        ROUND(CASE 
            WHEN wr.EXPOSURE_6M_STDDEV > 0 
            THEN (wr.EXPOSURE - wr.EXPOSURE_6M_AVG) / wr.EXPOSURE_6M_STDDEV 
            ELSE 0 
        END, 2) AS EXPOSURE_DRIFT_ZSCORE,
        ROUND(wr.CUMULATIVE_CONTRIBUTION, 6) AS CUMULATIVE_CONTRIBUTION,
        rm.VOLATILITY_REGIME,
        rm.MARKET_REGIME
    FROM with_rolling wr
    JOIN {database}.{curated}.DIM_PORTFOLIO p ON wr.PORTFOLIOID = p.PORTFOLIOID
    LEFT JOIN regime_monthly rm ON DATE_TRUNC('month', wr.DATE) = rm.MONTH_DATE
    """).collect()
    log_detail("  Created: V_FACTOR_ROLLING_ANALYTICS")
    
    session.sql(f"""
    CREATE OR REPLACE VIEW {database}.{curated}.V_REGIME_TRANSITIONS AS
    WITH daily_regimes AS (
        SELECT
            DATE,
            VOLATILITY_REGIME,
            MARKET_REGIME,
            LAG(VOLATILITY_REGIME) OVER (ORDER BY DATE) AS PREV_VOL_REGIME,
            LAG(MARKET_REGIME) OVER (ORDER BY DATE) AS PREV_MKT_REGIME
        FROM {database}.{curated}.V_MACRO_REGIME
    ),
    transitions AS (
        SELECT
            DATE AS TRANSITION_DATE,
            PREV_VOL_REGIME AS FROM_VOL_REGIME,
            VOLATILITY_REGIME AS TO_VOL_REGIME,
            PREV_MKT_REGIME AS FROM_MKT_REGIME,
            MARKET_REGIME AS TO_MKT_REGIME,
            CASE WHEN VOLATILITY_REGIME != PREV_VOL_REGIME THEN 'VOL_CHANGE'
                 WHEN MARKET_REGIME != PREV_MKT_REGIME THEN 'MKT_CHANGE'
            END AS TRANSITION_TYPE
        FROM daily_regimes
        WHERE VOLATILITY_REGIME != PREV_VOL_REGIME
           OR MARKET_REGIME != PREV_MKT_REGIME
    ),
    with_duration AS (
        SELECT
            t.*,
            DATEDIFF('day', LAG(TRANSITION_DATE) OVER (ORDER BY TRANSITION_DATE), TRANSITION_DATE) AS DAYS_IN_PRIOR_REGIME
        FROM transitions t
    )
    SELECT
        TRANSITION_DATE,
        TRANSITION_TYPE,
        FROM_VOL_REGIME,
        TO_VOL_REGIME,
        FROM_MKT_REGIME,
        TO_MKT_REGIME,
        COALESCE(DAYS_IN_PRIOR_REGIME, 0) AS DAYS_IN_PRIOR_REGIME
    FROM with_duration
    ORDER BY TRANSITION_DATE
    """).collect()
    log_detail("  Created: V_REGIME_TRANSITIONS")
    
    session.sql(f"""
    CREATE OR REPLACE VIEW {database}.{curated}.V_ATTRIBUTION_ANOMALIES AS
    WITH factor_stats AS (
        SELECT
            DATE, PORTFOLIOID, FACTOR_NAME,
            EXPOSURE, EXPOSURE_6M_AVG, EXPOSURE_DRIFT_ZSCORE,
            CONTRIBUTION, ROLLING_6M_CONTRIBUTION
        FROM {database}.{curated}.V_FACTOR_ROLLING_ANALYTICS
    ),
    factor_drift_flags AS (
        SELECT
            DATE, PORTFOLIOID,
            MAX(CASE WHEN ABS(EXPOSURE_DRIFT_ZSCORE) > 2.0 THEN 1 ELSE 0 END) AS HAS_FACTOR_DRIFT,
            MAX(CASE WHEN ABS(EXPOSURE_DRIFT_ZSCORE) > 2.0 THEN FACTOR_NAME END) AS DRIFT_FACTOR,
            MAX(CASE WHEN ABS(EXPOSURE_DRIFT_ZSCORE) > 2.0 THEN ROUND(EXPOSURE_DRIFT_ZSCORE, 2) END) AS DRIFT_MAGNITUDE
        FROM factor_stats
        GROUP BY DATE, PORTFOLIOID
    ),
    factor_dominance AS (
        SELECT
            DATE, PORTFOLIOID,
            FACTOR_NAME AS DOMINANT_FACTOR,
            ABS(CONTRIBUTION) AS ABS_CONTRIBUTION,
            SUM(ABS(CONTRIBUTION)) OVER (PARTITION BY DATE, PORTFOLIOID) AS TOTAL_ABS_CONTRIBUTION,
            ABS(CONTRIBUTION) / NULLIF(SUM(ABS(CONTRIBUTION)) OVER (PARTITION BY DATE, PORTFOLIOID), 0) AS FACTOR_SHARE
        FROM factor_stats
        QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE, PORTFOLIOID ORDER BY ABS(CONTRIBUTION) DESC) = 1
    ),
    brinson_concentration AS (
        SELECT
            DATE, PORTFOLIOID,
            SECTOR AS CONCENTRATED_SECTOR,
            ABS(SELECTION_EFFECT + ALLOCATION_EFFECT + INTERACTION_EFFECT) AS SECTOR_ABS_EFFECT,
            SUM(ABS(SELECTION_EFFECT + ALLOCATION_EFFECT + INTERACTION_EFFECT)) OVER (PARTITION BY DATE, PORTFOLIOID) AS TOTAL_ABS_EFFECT,
            ABS(SELECTION_EFFECT + ALLOCATION_EFFECT + INTERACTION_EFFECT) 
                / NULLIF(SUM(ABS(SELECTION_EFFECT + ALLOCATION_EFFECT + INTERACTION_EFFECT)) OVER (PARTITION BY DATE, PORTFOLIOID), 0) AS SECTOR_SHARE
        FROM {database}.{curated}.FACT_BRINSON_BY_SECTOR
        QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE, PORTFOLIOID ORDER BY ABS(SELECTION_EFFECT + ALLOCATION_EFFECT + INTERACTION_EFFECT) DESC) = 1
    ),
    active_return_stats AS (
        SELECT
            DATE, PORTFOLIOID,
            ACTIVE_RETURN,
            AVG(ACTIVE_RETURN) OVER (PARTITION BY PORTFOLIOID ORDER BY DATE ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS AR_6M_AVG,
            STDDEV(ACTIVE_RETURN) OVER (PARTITION BY PORTFOLIOID ORDER BY DATE ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS AR_6M_STDDEV
        FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION
    ),
    style_check AS (
        SELECT
            fs.DATE, fs.PORTFOLIOID, p.STRATEGY,
            MAX(CASE WHEN fs.FACTOR_NAME = 'Momentum' THEN fs.EXPOSURE END) AS MOMENTUM_EXPOSURE,
            MAX(CASE WHEN fs.FACTOR_NAME = 'Volatility' THEN fs.EXPOSURE END) AS VOLATILITY_EXPOSURE,
            MAX(CASE WHEN fs.FACTOR_NAME = 'Growth' THEN fs.EXPOSURE END) AS GROWTH_EXPOSURE,
            MAX(CASE WHEN fs.FACTOR_NAME = 'Value' THEN fs.EXPOSURE END) AS VALUE_EXPOSURE
        FROM factor_stats fs
        JOIN {database}.{curated}.DIM_PORTFOLIO p ON fs.PORTFOLIOID = p.PORTFOLIOID
        GROUP BY fs.DATE, fs.PORTFOLIOID, p.STRATEGY
    ),
    allocation_drift AS (
        SELECT
            DATE, PortfolioID,
            MAX(CASE WHEN ABS(PortfolioWeight - AVG_WEIGHT) > 2 * NULLIF(STDDEV_WEIGHT, 0) THEN GroupingValue END) AS DRIFT_GROUP,
            MAX(CASE WHEN ABS(PortfolioWeight - AVG_WEIGHT) > 2 * NULLIF(STDDEV_WEIGHT, 0) THEN 1 ELSE 0 END) AS HAS_ALLOCATION_DRIFT
        FROM (
            SELECT
                DATE, PortfolioID, GroupingValue, PortfolioWeight,
                AVG(PortfolioWeight) OVER (PARTITION BY PortfolioID, GroupingValue ORDER BY DATE ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS AVG_WEIGHT,
                STDDEV(PortfolioWeight) OVER (PARTITION BY PortfolioID, GroupingValue ORDER BY DATE ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS STDDEV_WEIGHT
            FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL
            WHERE GroupingDimension = 'SECTOR'
        )
        GROUP BY DATE, PortfolioID
    ),
    selection_reversal AS (
        SELECT
            DATE, PortfolioID,
            MAX(CASE WHEN SIGN(SelectionEffect) != SIGN(AVG_SEL) AND ABS(SelectionEffect) > 0.001 THEN GroupingValue END) AS REVERSAL_SECTOR,
            MAX(CASE WHEN SIGN(SelectionEffect) != SIGN(AVG_SEL) AND ABS(SelectionEffect) > 0.001 THEN 1 ELSE 0 END) AS HAS_SELECTION_REVERSAL
        FROM (
            SELECT
                DATE, PortfolioID, GroupingValue, SelectionEffect,
                AVG(SelectionEffect) OVER (PARTITION BY PortfolioID, GroupingValue ORDER BY DATE ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS AVG_SEL
            FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL
            WHERE GroupingDimension = 'SECTOR'
        )
        GROUP BY DATE, PortfolioID
    ),
    weight_concentration AS (
        SELECT
            DATE, PortfolioID,
            MAX(CASE WHEN PortfolioWeight > 0.40 THEN GroupingValue END) AS HEAVY_WEIGHT_GROUP,
            MAX(CASE WHEN PortfolioWeight > 0.40 THEN 1 ELSE 0 END) AS HAS_WEIGHT_CONCENTRATION
        FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL
        WHERE GroupingDimension = 'SECTOR'
        GROUP BY DATE, PortfolioID
    ),
    classification_sensitivity AS (
        SELECT
            s.DATE, s.PortfolioID,
            ABS(s.SECTOR_TOTAL - c.COUNTRY_TOTAL) AS CLASSIFICATION_DIVERGENCE,
            CASE WHEN ABS(s.SECTOR_TOTAL - c.COUNTRY_TOTAL) > 0.02 THEN 1 ELSE 0 END AS HAS_CLASSIFICATION_SENSITIVITY
        FROM (
            SELECT DATE, PortfolioID, SUM(TotalEffect) AS SECTOR_TOTAL
            FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL
            WHERE GroupingDimension = 'SECTOR'
            GROUP BY DATE, PortfolioID
        ) s
        JOIN (
            SELECT DATE, PortfolioID, SUM(TotalEffect) AS COUNTRY_TOTAL
            FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL
            WHERE GroupingDimension = 'COUNTRY'
            GROUP BY DATE, PortfolioID
        ) c ON s.DATE = c.DATE AND s.PortfolioID = c.PortfolioID
    )
    SELECT
        p.PORTFOLIONAME,
        p.STRATEGY,
        fd.DATE,
        fd.PORTFOLIOID,
        CASE WHEN fd.HAS_FACTOR_DRIFT = 1 THEN TRUE ELSE FALSE END AS FACTOR_DRIFT_ALERT,
        fd.DRIFT_FACTOR,
        fd.DRIFT_MAGNITUDE,
        CASE WHEN bc.SECTOR_SHARE > 0.6 THEN TRUE ELSE FALSE END AS CONCENTRATION_ALERT,
        bc.CONCENTRATED_SECTOR,
        ROUND(bc.SECTOR_SHARE, 2) AS CONCENTRATION_SHARE,
        CASE WHEN fdom.FACTOR_SHARE > 0.7 THEN TRUE ELSE FALSE END AS SINGLE_FACTOR_DOMINANCE,
        fdom.DOMINANT_FACTOR,
        ROUND(fdom.FACTOR_SHARE, 2) AS DOMINANT_FACTOR_SHARE,
        CASE
            WHEN sc.STRATEGY ILIKE '%low%vol%' AND ABS(sc.MOMENTUM_EXPOSURE) > 0.3 THEN TRUE
            WHEN sc.STRATEGY ILIKE '%value%' AND sc.GROWTH_EXPOSURE > sc.VALUE_EXPOSURE THEN TRUE
            WHEN sc.STRATEGY ILIKE '%growth%' AND sc.VALUE_EXPOSURE > sc.GROWTH_EXPOSURE THEN TRUE
            ELSE FALSE
        END AS STYLE_INCONSISTENCY,
        CASE 
            WHEN ars.AR_6M_STDDEV > 0 AND ABS(ars.ACTIVE_RETURN - ars.AR_6M_AVG) / ars.AR_6M_STDDEV > 2.0 THEN TRUE 
            ELSE FALSE 
        END AS ATTRIBUTION_SPIKE,
        CASE WHEN ad.HAS_ALLOCATION_DRIFT = 1 THEN TRUE ELSE FALSE END AS ALLOCATION_DRIFT_ALERT,
        ad.DRIFT_GROUP AS ALLOCATION_DRIFT_GROUP,
        CASE WHEN sr.HAS_SELECTION_REVERSAL = 1 THEN TRUE ELSE FALSE END AS SELECTION_REVERSAL_ALERT,
        sr.REVERSAL_SECTOR,
        CASE WHEN wc.HAS_WEIGHT_CONCENTRATION = 1 THEN TRUE ELSE FALSE END AS WEIGHT_CONCENTRATION_ALERT,
        wc.HEAVY_WEIGHT_GROUP,
        CASE WHEN cs.HAS_CLASSIFICATION_SENSITIVITY = 1 THEN TRUE ELSE FALSE END AS CLASSIFICATION_SENSITIVITY_ALERT,
        ROUND(cs.CLASSIFICATION_DIVERGENCE, 4) AS CLASSIFICATION_DIVERGENCE,
        CASE
            WHEN (CASE WHEN fd.HAS_FACTOR_DRIFT = 1 THEN 1 ELSE 0 END) 
               + (CASE WHEN bc.SECTOR_SHARE > 0.6 THEN 1 ELSE 0 END)
               + (CASE WHEN fdom.FACTOR_SHARE > 0.7 THEN 1 ELSE 0 END)
               + (CASE WHEN sc.STRATEGY ILIKE '%low%vol%' AND ABS(sc.MOMENTUM_EXPOSURE) > 0.3 THEN 1
                       WHEN sc.STRATEGY ILIKE '%value%' AND sc.GROWTH_EXPOSURE > sc.VALUE_EXPOSURE THEN 1
                       WHEN sc.STRATEGY ILIKE '%growth%' AND sc.VALUE_EXPOSURE > sc.GROWTH_EXPOSURE THEN 1 ELSE 0 END)
               + (CASE WHEN ars.AR_6M_STDDEV > 0 AND ABS(ars.ACTIVE_RETURN - ars.AR_6M_AVG) / ars.AR_6M_STDDEV > 2.0 THEN 1 ELSE 0 END)
               + (CASE WHEN ad.HAS_ALLOCATION_DRIFT = 1 THEN 1 ELSE 0 END)
               + (CASE WHEN sr.HAS_SELECTION_REVERSAL = 1 THEN 1 ELSE 0 END)
               + (CASE WHEN wc.HAS_WEIGHT_CONCENTRATION = 1 THEN 1 ELSE 0 END)
               + (CASE WHEN cs.HAS_CLASSIFICATION_SENSITIVITY = 1 THEN 1 ELSE 0 END) >= 3 THEN 'HIGH'
            WHEN (CASE WHEN fd.HAS_FACTOR_DRIFT = 1 THEN 1 ELSE 0 END) 
               + (CASE WHEN bc.SECTOR_SHARE > 0.6 THEN 1 ELSE 0 END)
               + (CASE WHEN fdom.FACTOR_SHARE > 0.7 THEN 1 ELSE 0 END)
               + (CASE WHEN sc.STRATEGY ILIKE '%low%vol%' AND ABS(sc.MOMENTUM_EXPOSURE) > 0.3 THEN 1
                       WHEN sc.STRATEGY ILIKE '%value%' AND sc.GROWTH_EXPOSURE > sc.VALUE_EXPOSURE THEN 1
                       WHEN sc.STRATEGY ILIKE '%growth%' AND sc.VALUE_EXPOSURE > sc.GROWTH_EXPOSURE THEN 1 ELSE 0 END)
               + (CASE WHEN ars.AR_6M_STDDEV > 0 AND ABS(ars.ACTIVE_RETURN - ars.AR_6M_AVG) / ars.AR_6M_STDDEV > 2.0 THEN 1 ELSE 0 END)
               + (CASE WHEN ad.HAS_ALLOCATION_DRIFT = 1 THEN 1 ELSE 0 END)
               + (CASE WHEN sr.HAS_SELECTION_REVERSAL = 1 THEN 1 ELSE 0 END)
               + (CASE WHEN wc.HAS_WEIGHT_CONCENTRATION = 1 THEN 1 ELSE 0 END)
               + (CASE WHEN cs.HAS_CLASSIFICATION_SENSITIVITY = 1 THEN 1 ELSE 0 END) >= 1 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS ANOMALY_SEVERITY
    FROM factor_drift_flags fd
    JOIN {database}.{curated}.DIM_PORTFOLIO p ON fd.PORTFOLIOID = p.PORTFOLIOID
    LEFT JOIN factor_dominance fdom ON fd.DATE = fdom.DATE AND fd.PORTFOLIOID = fdom.PORTFOLIOID
    LEFT JOIN brinson_concentration bc ON fd.DATE = bc.DATE AND fd.PORTFOLIOID = bc.PORTFOLIOID
    LEFT JOIN active_return_stats ars ON fd.DATE = ars.DATE AND fd.PORTFOLIOID = ars.PORTFOLIOID
    LEFT JOIN style_check sc ON fd.DATE = sc.DATE AND fd.PORTFOLIOID = sc.PORTFOLIOID
    LEFT JOIN allocation_drift ad ON fd.DATE = ad.DATE AND fd.PORTFOLIOID = ad.PORTFOLIOID
    LEFT JOIN selection_reversal sr ON fd.DATE = sr.DATE AND fd.PORTFOLIOID = sr.PORTFOLIOID
    LEFT JOIN weight_concentration wc ON fd.DATE = wc.DATE AND fd.PORTFOLIOID = wc.PORTFOLIOID
    LEFT JOIN classification_sensitivity cs ON fd.DATE = cs.DATE AND fd.PORTFOLIOID = cs.PORTFOLIOID
    """).collect()
    log_detail("  Created: V_ATTRIBUTION_ANOMALIES")
    
    session.sql(f"""
    CREATE OR REPLACE VIEW {database}.{curated}.V_CROSS_PORTFOLIO_ANALYTICS AS
    WITH trailing_brinson AS (
        SELECT
            PORTFOLIOID,
            AVG(ALLOCATION_EFFECT) AS AVG_ALLOCATION_EFFECT,
            AVG(SELECTION_EFFECT) AS AVG_SELECTION_EFFECT,
            AVG(ACTIVE_RETURN) AS AVG_ACTIVE_RETURN,
            STDDEV(ALLOCATION_EFFECT) AS ALLOCATION_CONSISTENCY,
            STDDEV(SELECTION_EFFECT) AS SELECTION_CONSISTENCY,
            COUNT(CASE WHEN ACTIVE_RETURN > 0 THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) AS ALPHA_PERSISTENCE,
            COUNT(*) AS MONTHS_ANALYSED
        FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION
        WHERE DATE > DATEADD('month', -12, (SELECT MAX(DATE) FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION))
        GROUP BY PORTFOLIOID
    ),
    trailing_factor AS (
        SELECT
            PORTFOLIOID,
            FACTOR_NAME,
            AVG(FACTOR_CONTRIBUTION) AS AVG_FACTOR_CONTRIBUTION,
            SUM(FACTOR_CONTRIBUTION) AS TOTAL_FACTOR_CONTRIBUTION
        FROM {database}.{curated}.FACT_FACTOR_ATTRIBUTION
        WHERE DATE > DATEADD('month', -12, (SELECT MAX(DATE) FROM {database}.{curated}.FACT_FACTOR_ATTRIBUTION))
        GROUP BY PORTFOLIOID, FACTOR_NAME
    ),
    best_worst_factor AS (
        SELECT
            PORTFOLIOID,
            MAX(CASE WHEN RN_BEST = 1 THEN FACTOR_NAME END) AS BEST_FACTOR_SOURCE,
            MAX(CASE WHEN RN_BEST = 1 THEN ROUND(AVG_FACTOR_CONTRIBUTION, 6) END) AS BEST_FACTOR_AVG_CONTRIBUTION,
            MAX(CASE WHEN RN_WORST = 1 THEN FACTOR_NAME END) AS WORST_FACTOR_SOURCE,
            MAX(CASE WHEN RN_WORST = 1 THEN ROUND(AVG_FACTOR_CONTRIBUTION, 6) END) AS WORST_FACTOR_AVG_CONTRIBUTION
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY PORTFOLIOID ORDER BY AVG_FACTOR_CONTRIBUTION DESC) AS RN_BEST,
                ROW_NUMBER() OVER (PARTITION BY PORTFOLIOID ORDER BY AVG_FACTOR_CONTRIBUTION ASC) AS RN_WORST
            FROM trailing_factor
        )
        WHERE RN_BEST = 1 OR RN_WORST = 1
        GROUP BY PORTFOLIOID
    ),
    sector_alpha AS (
        SELECT
            PORTFOLIOID, SECTOR,
            AVG(SELECTION_EFFECT) AS AVG_SECTOR_SELECTION,
            STDDEV(SELECTION_EFFECT) AS SECTOR_SELECTION_CONSISTENCY
        FROM {database}.{curated}.FACT_BRINSON_BY_SECTOR
        WHERE DATE > DATEADD('month', -12, (SELECT MAX(DATE) FROM {database}.{curated}.FACT_BRINSON_BY_SECTOR))
        GROUP BY PORTFOLIOID, SECTOR
        QUALIFY ROW_NUMBER() OVER (PARTITION BY PORTFOLIOID ORDER BY AVG(SELECTION_EFFECT) DESC) = 1
    )
    SELECT
        p.PORTFOLIOID,
        p.PORTFOLIONAME,
        p.STRATEGY,
        ROUND(tb.AVG_ALLOCATION_EFFECT, 6) AS AVG_ALLOCATION_EFFECT,
        ROUND(tb.AVG_SELECTION_EFFECT, 6) AS AVG_SELECTION_EFFECT,
        ROUND(tb.AVG_ACTIVE_RETURN, 6) AS AVG_ACTIVE_RETURN,
        ROUND(tb.ALLOCATION_CONSISTENCY, 6) AS ALLOCATION_CONSISTENCY,
        ROUND(tb.SELECTION_CONSISTENCY, 6) AS SELECTION_CONSISTENCY,
        ROUND(tb.ALPHA_PERSISTENCE, 2) AS ALPHA_PERSISTENCE,
        tb.MONTHS_ANALYSED,
        bwf.BEST_FACTOR_SOURCE,
        bwf.BEST_FACTOR_AVG_CONTRIBUTION,
        bwf.WORST_FACTOR_SOURCE,
        bwf.WORST_FACTOR_AVG_CONTRIBUTION,
        sa.SECTOR AS BEST_SELECTION_SECTOR,
        ROUND(sa.AVG_SECTOR_SELECTION, 6) AS BEST_SECTOR_SELECTION_AVG
    FROM trailing_brinson tb
    JOIN {database}.{curated}.DIM_PORTFOLIO p ON tb.PORTFOLIOID = p.PORTFOLIOID
    LEFT JOIN best_worst_factor bwf ON tb.PORTFOLIOID = bwf.PORTFOLIOID
    LEFT JOIN sector_alpha sa ON tb.PORTFOLIOID = sa.PORTFOLIOID
    """).collect()
    log_detail("  Created: V_CROSS_PORTFOLIO_ANALYTICS")


def build_multi_level_attribution(session: Session, test_mode: bool = False) -> None:
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']

    log_phase("Multi-Level Attribution")

    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL (
        DATE DATE,
        PortfolioID BIGINT,
        GroupingDimension VARCHAR(30),
        GroupingValue VARCHAR(200),
        ParentGroupingValue VARCHAR(200),
        PortfolioWeight FLOAT,
        BenchmarkWeight FLOAT,
        PortfolioGroupReturn FLOAT,
        BenchmarkGroupReturn FLOAT,
        AllocationEffect FLOAT,
        SelectionEffect FLOAT,
        InteractionEffect FLOAT,
        TotalEffect FLOAT
    )
    """).collect()
    log_step("Created empty FACT_BRINSON_ATTRIBUTION_DETAIL")

    session.sql(f"""
    INSERT INTO {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL
    SELECT
        DATE, PortfolioId AS PortfolioID,
        'SECTOR' AS GroupingDimension,
        SECTOR AS GroupingValue,
        NULL AS ParentGroupingValue,
        PORTFOLIO_WEIGHT AS PortfolioWeight,
        BENCHMARK_WEIGHT AS BenchmarkWeight,
        PORTFOLIO_SECTOR_RETURN AS PortfolioGroupReturn,
        BENCHMARK_SECTOR_RETURN AS BenchmarkGroupReturn,
        ALLOCATION_EFFECT AS AllocationEffect,
        SELECTION_EFFECT AS SelectionEffect,
        INTERACTION_EFFECT AS InteractionEffect,
        ALLOCATION_EFFECT + SELECTION_EFFECT + INTERACTION_EFFECT AS TotalEffect
    FROM {database}.{curated}.FACT_BRINSON_BY_SECTOR
    """).collect()
    log_substep("Inserted SECTOR rows from existing FACT_BRINSON_BY_SECTOR")

    grouping_dimensions = [
        {
            'name': 'COUNTRY',
            'expr': "i.CountryOfIncorporation",
            'parent_expr': 'NULL',
        },
        {
            'name': 'INDUSTRY',
            'expr': "i.SIC_DESCRIPTION",
            'parent_expr': "CASE WHEN i.GICS_SECTOR = 'Healthcare' THEN 'Health Care' ELSE i.GICS_SECTOR END",
        },
        {
            'name': 'ASSET_CLASS',
            'expr': "s.AssetClass",
            'parent_expr': 'NULL',
        },
    ]

    for dim in grouping_dimensions:
        dim_name = dim['name']
        group_expr = dim['expr']
        parent_expr = dim['parent_expr']
        log_substep(f"Computing attribution for {dim_name}...")

        session.sql(f"""
        INSERT INTO {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL
        WITH month_end_prices AS (
            SELECT SECURITYID, PRICE_DATE, PRICE_CLOSE,
                LAG(PRICE_CLOSE) OVER (PARTITION BY SECURITYID ORDER BY PRICE_DATE) AS PREV_MONTH_CLOSE
            FROM (
                SELECT SECURITYID, PRICE_DATE, PRICE_CLOSE,
                    ROW_NUMBER() OVER (PARTITION BY SECURITYID, DATE_TRUNC('month', PRICE_DATE) ORDER BY PRICE_DATE DESC) AS RN
                FROM {database}.MARKET_DATA.FACT_STOCK_PRICES
            )
            WHERE RN = 1
        ),
        stock_monthly_returns AS (
            SELECT SECURITYID, PRICE_DATE,
                (PRICE_CLOSE - PREV_MONTH_CLOSE) / NULLIF(PREV_MONTH_CLOSE, 0) AS STOCK_RETURN
            FROM month_end_prices
            WHERE PREV_MONTH_CLOSE IS NOT NULL
        ),
        position_with_group AS (
            SELECT
                p.HoldingDate AS DATE,
                p.PortfolioID,
                p.SecurityID,
                p.PortfolioWeight,
                {group_expr} AS GROUPING_VALUE,
                {parent_expr} AS PARENT_GROUPING_VALUE
            FROM {database}.{curated}.FACT_POSITION_DAILY_ABOR p
            JOIN {database}.{curated}.DIM_SECURITY s ON p.SecurityID = s.SecurityID
            JOIN {database}.{curated}.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE p.HoldingDate >= DATEADD('year', -2, CURRENT_DATE())
        ),
        portfolio_group_data AS (
            SELECT
                pwg.DATE,
                pwg.PortfolioID,
                pwg.GROUPING_VALUE,
                MAX(pwg.PARENT_GROUPING_VALUE) AS PARENT_GROUPING_VALUE,
                SUM(pwg.PortfolioWeight) AS PORTFOLIO_WEIGHT,
                SUM(pwg.PortfolioWeight * smr.STOCK_RETURN) / NULLIF(SUM(pwg.PortfolioWeight), 0) AS PORTFOLIO_GROUP_RETURN
            FROM position_with_group pwg
            JOIN stock_monthly_returns smr
                ON pwg.SecurityID = smr.SECURITYID
                AND DATE_TRUNC('month', pwg.DATE) = DATE_TRUNC('month', smr.PRICE_DATE)
            GROUP BY pwg.DATE, pwg.PortfolioID, pwg.GROUPING_VALUE
        ),
        universe_group_mapping AS (
            SELECT DISTINCT
                {group_expr} AS GROUPING_VALUE,
                s.SecurityID
            FROM {database}.{curated}.DIM_SECURITY s
            JOIN {database}.{curated}.DIM_ISSUER i ON s.IssuerID = i.IssuerID
        ),
        universe_count AS (
            SELECT COUNT(DISTINCT SecurityID) AS TOTAL FROM universe_group_mapping
        ),
        benchmark_weights AS (
            SELECT
                ugm.GROUPING_VALUE,
                CAST(COUNT(DISTINCT ugm.SecurityID) AS FLOAT) / uc.TOTAL AS BENCHMARK_WEIGHT
            FROM universe_group_mapping ugm
            CROSS JOIN universe_count uc
            GROUP BY ugm.GROUPING_VALUE, uc.TOTAL
        ),
        benchmark_group_returns AS (
            SELECT
                smr.PRICE_DATE AS DATE,
                ugm.GROUPING_VALUE,
                AVG(smr.STOCK_RETURN) AS BENCHMARK_GROUP_RETURN
            FROM universe_group_mapping ugm
            JOIN stock_monthly_returns smr ON ugm.SecurityID = smr.SECURITYID
            GROUP BY smr.PRICE_DATE, ugm.GROUPING_VALUE
        ),
        date_portfolio_spine AS (
            SELECT DISTINCT DATE, PortfolioID FROM portfolio_group_data
        ),
        all_group_rows AS (
            SELECT
                dp.DATE,
                dp.PortfolioID,
                bw.GROUPING_VALUE,
                pgd.PARENT_GROUPING_VALUE,
                COALESCE(pgd.PORTFOLIO_WEIGHT, 0) AS PORTFOLIO_WEIGHT,
                bw.BENCHMARK_WEIGHT,
                COALESCE(pgd.PORTFOLIO_GROUP_RETURN, 0) AS PORTFOLIO_GROUP_RETURN,
                COALESCE(bgr.BENCHMARK_GROUP_RETURN, 0) AS BENCHMARK_GROUP_RETURN
            FROM date_portfolio_spine dp
            CROSS JOIN benchmark_weights bw
            LEFT JOIN portfolio_group_data pgd
                ON dp.DATE = pgd.DATE AND dp.PortfolioID = pgd.PortfolioID AND bw.GROUPING_VALUE = pgd.GROUPING_VALUE
            LEFT JOIN benchmark_group_returns bgr
                ON dp.DATE = bgr.DATE AND bw.GROUPING_VALUE = bgr.GROUPING_VALUE
        ),
        total_bm AS (
            SELECT DATE, SUM(BENCHMARK_WEIGHT * BENCHMARK_GROUP_RETURN) AS TOTAL_BM_RETURN
            FROM all_group_rows
            GROUP BY DATE
        )
        SELECT
            a.DATE,
            a.PortfolioID,
            '{dim_name}' AS GroupingDimension,
            a.GROUPING_VALUE AS GroupingValue,
            a.PARENT_GROUPING_VALUE AS ParentGroupingValue,
            a.PORTFOLIO_WEIGHT AS PortfolioWeight,
            a.BENCHMARK_WEIGHT AS BenchmarkWeight,
            a.PORTFOLIO_GROUP_RETURN AS PortfolioGroupReturn,
            a.BENCHMARK_GROUP_RETURN AS BenchmarkGroupReturn,
            ROUND((a.PORTFOLIO_WEIGHT - a.BENCHMARK_WEIGHT) * (a.BENCHMARK_GROUP_RETURN - tb.TOTAL_BM_RETURN), 10) AS AllocationEffect,
            ROUND(a.BENCHMARK_WEIGHT * (a.PORTFOLIO_GROUP_RETURN - a.BENCHMARK_GROUP_RETURN), 10) AS SelectionEffect,
            ROUND((a.PORTFOLIO_WEIGHT - a.BENCHMARK_WEIGHT) * (a.PORTFOLIO_GROUP_RETURN - a.BENCHMARK_GROUP_RETURN), 10) AS InteractionEffect,
            ROUND((a.PORTFOLIO_WEIGHT - a.BENCHMARK_WEIGHT) * (a.BENCHMARK_GROUP_RETURN - tb.TOTAL_BM_RETURN), 10)
            + ROUND(a.BENCHMARK_WEIGHT * (a.PORTFOLIO_GROUP_RETURN - a.BENCHMARK_GROUP_RETURN), 10)
            + ROUND((a.PORTFOLIO_WEIGHT - a.BENCHMARK_WEIGHT) * (a.PORTFOLIO_GROUP_RETURN - a.BENCHMARK_GROUP_RETURN), 10) AS TotalEffect
        FROM all_group_rows a
        JOIN total_bm tb ON a.DATE = tb.DATE
        """).collect()
        log_substep(f"  Inserted {dim_name} attribution rows")

    row_count = session.sql(f"SELECT COUNT(*) AS CNT FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL").collect()[0]['CNT']
    log_phase_complete(f"Multi-Level Attribution: {row_count} rows across 4 dimensions")


def build_currency_attribution(session: Session, test_mode: bool = False) -> None:
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']

    log_phase("Currency Attribution")

    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_CURRENCY_ATTRIBUTION AS
    WITH country_currency_map AS (
        SELECT 'US' AS COUNTRY, 'USD' AS CURRENCY UNION ALL
        SELECT 'GB', 'GBP' UNION ALL SELECT 'CA', 'CAD' UNION ALL
        SELECT 'CN', 'CNY' UNION ALL SELECT 'JP', 'JPY' UNION ALL
        SELECT 'CH', 'CHF' UNION ALL SELECT 'BR', 'BRL' UNION ALL
        SELECT 'MX', 'MXN' UNION ALL SELECT 'IN', 'INR' UNION ALL
        SELECT 'KR', 'KRW' UNION ALL SELECT 'AU', 'AUD' UNION ALL
        SELECT 'HK', 'USD' UNION ALL SELECT 'SG', 'USD' UNION ALL
        SELECT 'TW', 'USD' UNION ALL SELECT 'IE', 'EUR' UNION ALL
        SELECT 'NL', 'EUR' UNION ALL SELECT 'FR', 'EUR' UNION ALL
        SELECT 'DE', 'EUR' UNION ALL SELECT 'ES', 'EUR' UNION ALL
        SELECT 'FI', 'EUR' UNION ALL SELECT 'SE', 'EUR' UNION ALL
        SELECT 'NO', 'EUR' UNION ALL SELECT 'DK', 'EUR' UNION ALL
        SELECT 'KY', 'USD' UNION ALL SELECT 'BM', 'USD' UNION ALL
        SELECT 'PA', 'USD' UNION ALL SELECT 'ZA', 'USD' UNION ALL
        SELECT 'CT', 'USD' UNION ALL SELECT 'NC', 'USD' UNION ALL
        SELECT 'TX', 'USD'
    ),
    month_end_prices AS (
        SELECT SECURITYID, PRICE_DATE, PRICE_CLOSE,
            LAG(PRICE_CLOSE) OVER (PARTITION BY SECURITYID ORDER BY PRICE_DATE) AS PREV_MONTH_CLOSE
        FROM (
            SELECT SECURITYID, PRICE_DATE, PRICE_CLOSE,
                ROW_NUMBER() OVER (PARTITION BY SECURITYID, DATE_TRUNC('month', PRICE_DATE) ORDER BY PRICE_DATE DESC) AS RN
            FROM {database}.MARKET_DATA.FACT_STOCK_PRICES
        )
        WHERE RN = 1
    ),
    stock_monthly_returns AS (
        SELECT SECURITYID, PRICE_DATE,
            (PRICE_CLOSE - PREV_MONTH_CLOSE) / NULLIF(PREV_MONTH_CLOSE, 0) AS STOCK_RETURN
        FROM month_end_prices
        WHERE PREV_MONTH_CLOSE IS NOT NULL
    ),
    fx_monthly AS (
        SELECT
            QUOTE_CURRENCY_ID AS CURRENCY,
            DATE AS FX_DATE,
            FX_RATE,
            LAG(FX_RATE) OVER (PARTITION BY QUOTE_CURRENCY_ID ORDER BY DATE) AS PREV_FX_RATE,
            (FX_RATE - LAG(FX_RATE) OVER (PARTITION BY QUOTE_CURRENCY_ID ORDER BY DATE))
                / NULLIF(LAG(FX_RATE) OVER (PARTITION BY QUOTE_CURRENCY_ID ORDER BY DATE), 0) AS FX_RETURN
        FROM (
            SELECT QUOTE_CURRENCY_ID, DATE, FX_RATE,
                ROW_NUMBER() OVER (PARTITION BY QUOTE_CURRENCY_ID, DATE_TRUNC('month', DATE) ORDER BY DATE DESC) AS RN
            FROM {database}.{market_data}.FACT_FX_RATES
        )
        WHERE RN = 1
    ),
    position_with_currency AS (
        SELECT
            p.HoldingDate AS DATE,
            p.PortfolioID,
            p.SecurityID,
            p.PortfolioWeight,
            COALESCE(ccm.CURRENCY, 'USD') AS LocalCurrency,
            CASE WHEN p.PortfolioID IN (3, 5) THEN 'EUR' ELSE 'USD' END AS BaseCurrency
        FROM {database}.{curated}.FACT_POSITION_DAILY_ABOR p
        JOIN {database}.{curated}.DIM_SECURITY s ON p.SecurityID = s.SecurityID
        JOIN {database}.{curated}.DIM_ISSUER i ON s.IssuerID = i.IssuerID
        LEFT JOIN country_currency_map ccm ON i.CountryOfIncorporation = ccm.COUNTRY
        WHERE p.HoldingDate >= DATEADD('year', -2, CURRENT_DATE())
    )
    SELECT
        pwc.DATE,
        pwc.PortfolioID,
        pwc.SecurityID,
        smr.STOCK_RETURN AS LocalReturn,
        CASE
            WHEN pwc.LocalCurrency = pwc.BaseCurrency THEN 0
            WHEN pwc.BaseCurrency = 'EUR' AND pwc.LocalCurrency = 'USD' THEN -1 * COALESCE(fm_eur.FX_RETURN, 0)
            WHEN pwc.BaseCurrency = 'EUR' AND pwc.LocalCurrency != 'USD' THEN COALESCE(fm_loc.FX_RETURN, 0) - COALESCE(fm_eur.FX_RETURN, 0)
            ELSE COALESCE(fm_loc.FX_RETURN, 0)
        END AS FXReturn,
        CASE
            WHEN pwc.LocalCurrency = pwc.BaseCurrency THEN 0
            WHEN pwc.BaseCurrency = 'EUR' AND pwc.LocalCurrency = 'USD' THEN smr.STOCK_RETURN * (-1 * COALESCE(fm_eur.FX_RETURN, 0))
            WHEN pwc.BaseCurrency = 'EUR' AND pwc.LocalCurrency != 'USD' THEN smr.STOCK_RETURN * (COALESCE(fm_loc.FX_RETURN, 0) - COALESCE(fm_eur.FX_RETURN, 0))
            ELSE smr.STOCK_RETURN * COALESCE(fm_loc.FX_RETURN, 0)
        END AS AVUReturn,
        smr.STOCK_RETURN
            + CASE
                WHEN pwc.LocalCurrency = pwc.BaseCurrency THEN 0
                WHEN pwc.BaseCurrency = 'EUR' AND pwc.LocalCurrency = 'USD' THEN -1 * COALESCE(fm_eur.FX_RETURN, 0)
                WHEN pwc.BaseCurrency = 'EUR' AND pwc.LocalCurrency != 'USD' THEN COALESCE(fm_loc.FX_RETURN, 0) - COALESCE(fm_eur.FX_RETURN, 0)
                ELSE COALESCE(fm_loc.FX_RETURN, 0)
              END
            + CASE
                WHEN pwc.LocalCurrency = pwc.BaseCurrency THEN 0
                WHEN pwc.BaseCurrency = 'EUR' AND pwc.LocalCurrency = 'USD' THEN smr.STOCK_RETURN * (-1 * COALESCE(fm_eur.FX_RETURN, 0))
                WHEN pwc.BaseCurrency = 'EUR' AND pwc.LocalCurrency != 'USD' THEN smr.STOCK_RETURN * (COALESCE(fm_loc.FX_RETURN, 0) - COALESCE(fm_eur.FX_RETURN, 0))
                ELSE smr.STOCK_RETURN * COALESCE(fm_loc.FX_RETURN, 0)
              END
            AS BaseReturn,
        pwc.LocalCurrency,
        pwc.BaseCurrency
    FROM position_with_currency pwc
    JOIN stock_monthly_returns smr
        ON pwc.SecurityID = smr.SECURITYID
        AND DATE_TRUNC('month', pwc.DATE) = DATE_TRUNC('month', smr.PRICE_DATE)
    LEFT JOIN fx_monthly fm_loc
        ON pwc.LocalCurrency = fm_loc.CURRENCY
        AND DATE_TRUNC('month', pwc.DATE) = DATE_TRUNC('month', fm_loc.FX_DATE)
    LEFT JOIN fx_monthly fm_eur
        ON fm_eur.CURRENCY = 'EUR'
        AND DATE_TRUNC('month', pwc.DATE) = DATE_TRUNC('month', fm_eur.FX_DATE)
    WHERE smr.STOCK_RETURN IS NOT NULL
    """).collect()

    row_count = session.sql(f"SELECT COUNT(*) AS CNT FROM {database}.{curated}.FACT_CURRENCY_ATTRIBUTION").collect()[0]['CNT']
    log_phase_complete(f"Currency Attribution: {row_count} rows")


def build_attribution_linked(session: Session, test_mode: bool = False) -> None:
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']

    log_phase("Multi-Period Linked Attribution")

    session.sql(f"""
    CREATE OR REPLACE TABLE {database}.{curated}.FACT_BRINSON_LINKED AS
    WITH monthly_summary AS (
        SELECT
            DATE,
            PortfolioID,
            GroupingDimension,
            GroupingValue,
            AllocationEffect,
            SelectionEffect,
            InteractionEffect,
            TotalEffect
        FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION_DETAIL
    ),
    portfolio_monthly_return AS (
        SELECT DATE, PORTFOLIOID, ACTIVE_RETURN, TOTAL_PORTFOLIO_RETURN
        FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION
    ),
    period_definitions AS (
        SELECT DATE AS PeriodEnd, 'QTD' AS PeriodType,
            DATE_TRUNC('quarter', DATE) AS PeriodStart
        FROM (SELECT DISTINCT DATE FROM monthly_summary)
        UNION ALL
        SELECT DATE, 'YTD',
            DATE_TRUNC('year', DATE)
        FROM (SELECT DISTINCT DATE FROM monthly_summary)
        UNION ALL
        SELECT DATE, 'TRAILING_12M',
            DATEADD('month', -11, DATE_TRUNC('month', DATE))
        FROM (SELECT DISTINCT DATE FROM monthly_summary)
    ),
    linked_calc AS (
        SELECT
            pd.PeriodEnd,
            pd.PeriodType,
            ms.PortfolioID,
            ms.GroupingDimension,
            ms.GroupingValue,
            ms.DATE AS MonthDate,
            ms.AllocationEffect,
            ms.SelectionEffect,
            ms.InteractionEffect,
            ms.TotalEffect,
            COALESCE(
                EXP(SUM(LN(1 + pmr.TOTAL_PORTFOLIO_RETURN))
                    OVER (PARTITION BY pd.PeriodEnd, pd.PeriodType, ms.PortfolioID, ms.GroupingDimension, ms.GroupingValue
                          ORDER BY ms.DATE
                          ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)) - 1,
                0
            ) AS CUMULATIVE_RETURN_PRIOR
        FROM period_definitions pd
        JOIN monthly_summary ms
            ON ms.DATE >= pd.PeriodStart AND ms.DATE <= pd.PeriodEnd
        JOIN portfolio_monthly_return pmr
            ON ms.PortfolioID = pmr.PORTFOLIOID AND ms.DATE = pmr.DATE
    )
    SELECT
        PeriodEnd,
        PeriodType,
        PortfolioID,
        GroupingDimension,
        GroupingValue,
        SUM(AllocationEffect * (1 + CUMULATIVE_RETURN_PRIOR)) AS LinkedAllocation,
        SUM(SelectionEffect * (1 + CUMULATIVE_RETURN_PRIOR)) AS LinkedSelection,
        SUM(InteractionEffect * (1 + CUMULATIVE_RETURN_PRIOR)) AS LinkedInteraction,
        SUM(TotalEffect * (1 + CUMULATIVE_RETURN_PRIOR)) AS LinkedTotalEffect,
        NULL AS CompoundedPortfolioReturn,
        NULL AS CompoundedBenchmarkReturn,
        NULL AS CompoundedActiveReturn,
        NULL AS ReconciliationGap
    FROM linked_calc
    GROUP BY PeriodEnd, PeriodType, PortfolioID, GroupingDimension, GroupingValue
    """).collect()
    log_step("Created FACT_BRINSON_LINKED")

    session.sql(f"""
    UPDATE {database}.{curated}.FACT_BRINSON_LINKED bl
    SET
        CompoundedPortfolioReturn = pmr.COMP_PORT,
        CompoundedBenchmarkReturn = pmr.COMP_BM,
        CompoundedActiveReturn = pmr.COMP_PORT - pmr.COMP_BM,
        ReconciliationGap = (pmr.COMP_PORT - pmr.COMP_BM) - bl.LinkedTotalEffect
    FROM (
        SELECT
            pd.PeriodEnd,
            pd.PeriodType,
            ba.PORTFOLIOID,
            EXP(SUM(LN(1 + ba.TOTAL_PORTFOLIO_RETURN))) - 1 AS COMP_PORT,
            EXP(SUM(LN(1 + ba.TOTAL_BENCHMARK_RETURN))) - 1 AS COMP_BM
        FROM (
            SELECT DATE AS PeriodEnd, 'QTD' AS PeriodType, DATE_TRUNC('quarter', DATE) AS PeriodStart
            FROM (SELECT DISTINCT DATE FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION)
            UNION ALL
            SELECT DATE, 'YTD', DATE_TRUNC('year', DATE)
            FROM (SELECT DISTINCT DATE FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION)
            UNION ALL
            SELECT DATE, 'TRAILING_12M', DATEADD('month', -11, DATE_TRUNC('month', DATE))
            FROM (SELECT DISTINCT DATE FROM {database}.{curated}.FACT_BRINSON_ATTRIBUTION)
        ) pd
        JOIN {database}.{curated}.FACT_BRINSON_ATTRIBUTION ba
            ON ba.DATE >= pd.PeriodStart AND ba.DATE <= pd.PeriodEnd
        GROUP BY pd.PeriodEnd, pd.PeriodType, ba.PORTFOLIOID
    ) pmr
    WHERE bl.PeriodEnd = pmr.PeriodEnd
        AND bl.PeriodType = pmr.PeriodType
        AND bl.PortfolioID = pmr.PORTFOLIOID
    """).collect()
    log_step("Updated compounded returns and reconciliation gaps")

    row_count = session.sql(f"SELECT COUNT(*) AS CNT FROM {database}.{curated}.FACT_BRINSON_LINKED").collect()[0]['CNT']
    log_phase_complete(f"Multi-Period Linked Attribution: {row_count} rows")


def validate_data_quality(session: Session):
    """Validate data quality of the new model."""
    
    
    # Check portfolio weights sum to 100%
    weight_check = session.sql(f"""
        SELECT 
            PortfolioID,
            SUM(PortfolioWeight) as TotalWeight,
            ABS(SUM(PortfolioWeight) - 1.0) as WeightDeviation
        FROM {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR 
        WHERE HoldingDate = (SELECT MAX(HoldingDate) FROM {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR)
        GROUP BY PortfolioID
        HAVING ABS(SUM(PortfolioWeight) - 1.0) > 0.001
    """).collect()
    
    if weight_check:
        log_warning(f"  Portfolio weight deviations found: {len(weight_check)} portfolios")
    else:
        pass
    
    # Check security identifier integrity (simplified - check ticker column)
    security_check = session.sql(f"""
        SELECT 
            COUNT(*) as total_securities,
            COUNT(CASE WHEN Ticker IS NOT NULL AND LENGTH(Ticker) > 0 THEN 1 END) as securities_with_ticker
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY
    """).collect()
    
    if security_check:
        result = security_check[0]
        total = result['TOTAL_SECURITIES']
        with_ticker = result['SECURITIES_WITH_TICKER']
        
        if with_ticker < total:
            log_warning(f"  {total - with_ticker} securities missing TICKER")
    
