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
from logging_utils import log_detail, log_info, log_warning, log_error, log_success
from db_helpers import get_max_price_date
from sql_utils import safe_sql_tuple
from demo_helpers import build_demo_portfolios_sql_mapping, get_demo_portfolio_names, get_demo_clients_sorted, get_demo_company_tickers, get_all_demo_clients_sorted, get_at_risk_client_ids, get_new_client_ids, get_new_demo_clients
from sql_case_builders import (
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

def build_all(session: Session, scenarios: List[str], test_mode: bool = False, recreate_database: bool = True):
    """
    Build all structured data using the enhanced data model.
    
    Args:
        session: Active Snowpark session
        scenarios: List of scenario names to build data for (use ['all'] for all scenarios)
        test_mode: If True, use 10% data volumes for faster testing
        recreate_database: If True, drop and recreate the database. If False, only ensure schemas exist.
    """
    
    # Expand 'all' to actual scenarios from config
    if scenarios == ['all'] or 'all' in scenarios:
        scenarios = config.AVAILABLE_SCENARIOS
    
    # Step 1: Create database and schemas
    create_database_structure(session, recreate_database=recreate_database)
    
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
                import create_agents
                create_agents.cleanup_all_agents(session)
            except Exception:
                pass  # Suppress any cleanup errors - agents may not exist
            
            # Full recreation - drops everything and starts fresh
            session.sql(f"CREATE OR REPLACE DATABASE {config.DATABASE['name']}").collect()
            session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.RAW").collect()
            session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.CURATED").collect()
            session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.AI").collect()
            session.sql(f"CREATE SCHEMA IF NOT EXISTS {config.DATABASE['name']}.MARKET_DATA").collect()
        else:
            # Incremental mode - skip database creation (assumes setup.sql already created it)
            # This is needed when running from a stored procedure inside the database
            log_info("Skipping database/schema creation (incremental mode - assuming already exists)")
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
    _run_build_step(build_dim_benchmark, session)
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
    _run_build_step(build_esg_latest_view, session)  # Enriched view with ESG (returns added later after market data)
    _run_build_step(build_factor_exposures, session)
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
    
    # Build list of demo companies for SQL
    demo_companies = config.DEMO_COMPANIES
    
    # Create VALUES clause for demo companies - all fields are required
    values_rows = []
    for idx, (ticker, data) in enumerate(demo_companies.items(), start=1):
        company_name = data['company_name'].replace("'", "''")  # Escape single quotes
        provider_id = data['provider_company_id']
        cik = data['cik']
        sector = data['sector']
        tier = data['tier']
        values_rows.append(
            f"('{ticker}', '{company_name}', '{provider_id}', '{cik}', '{sector}', '{tier}')"
        )
    
    values_clause = ",\n            ".join(values_rows)
    
    # Build DIM_ISSUER by joining demo companies with COMPANY_INDEX for additional metadata
    # INNER JOIN ensures all companies must exist in real data source
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.DIM_ISSUER AS
        WITH demo_companies AS (
            SELECT * FROM (VALUES
            {values_clause}
            ) AS t(Ticker, CompanyName, ProviderCompanyID, CIK, Sector, Tier)
        ),
        enriched AS (
            -- Enrich demo companies with COMPANY_INDEX data (INNER JOIN - require match)
            SELECT 
                dc.Ticker,
                dc.CompanyName,
                dc.ProviderCompanyID,
                dc.CIK,
                dc.Sector,
                dc.Tier,
                ci.LEI,
                -- Get country from company characteristics
                MAX(CASE WHEN cc.RELATIONSHIP_TYPE = 'business_address_country' THEN cc.VALUE END) as CountryFromIndex
            FROM demo_companies dc
            INNER JOIN {config.REAL_DATA_SOURCES['database']}.{config.REAL_DATA_SOURCES['schema']}.COMPANY_INDEX ci
                ON dc.ProviderCompanyID = ci.COMPANY_ID
            INNER JOIN {config.REAL_DATA_SOURCES['database']}.{config.REAL_DATA_SOURCES['schema']}.COMPANY_CHARACTERISTICS cc
                ON ci.COMPANY_ID = cc.COMPANY_ID
            GROUP BY dc.Ticker, dc.CompanyName, dc.ProviderCompanyID, dc.CIK, dc.Sector, dc.Tier, ci.LEI
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY 
                CASE Tier WHEN 'core' THEN 1 WHEN 'major' THEN 2 ELSE 3 END,
                CompanyName
            ) as IssuerID,
            NULL as UltimateParentIssuerID,
            ProviderCompanyID,
            CIK,
            Ticker as PrimaryTicker,
            SUBSTR(TRIM(CompanyName), 1, 255) as LegalName,
            Sector as SIC_DESCRIPTION,
            Sector as GICS_SECTOR,
            CountryFromIndex as CountryOfIncorporation,
            LEI[0]::VARCHAR as LEI,
            Tier
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
        -- Build ABOR (Accounting Book of Record) positions from transaction history
        -- This creates monthly position snapshots by aggregating transaction data
        -- Upper bound is max_price_date to ensure all positions have available price/return data
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR AS
        WITH monthly_dates AS (
            -- Step 1: Generate month-end dates for position snapshots over {config.YEARS_OF_HISTORY} years of history
            -- Uses LAST_DAY to ensure consistent month-end reporting dates
            -- Upper bound is max available price date to ensure return data exists
            SELECT LAST_DAY(DATEADD(month, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, '{max_price_date}'::DATE))) as position_date
            FROM TABLE(GENERATOR(rowcount => {12 * config.YEARS_OF_HISTORY}))
            WHERE position_date <= '{max_price_date}'::DATE
        ),
        transaction_balances AS (
            -- Step 2: Calculate net position quantities and average cost basis from transactions
            -- Aggregates all BUY/SELL transactions to determine current holdings
            SELECT 
                PortfolioID,
                SecurityID,
                -- Net quantity: BUY transactions add, SELL transactions subtract
                SUM(CASE WHEN TransactionType = 'BUY' THEN Quantity ELSE -Quantity END) as TotalQuantity,
                -- Average transaction price for cost basis calculation
                AVG(Price) as AvgPrice
            FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION
            GROUP BY PortfolioID, SecurityID
            HAVING TotalQuantity > 0  -- Only include positions with positive holdings
        ),
        position_snapshots AS (
            -- Step 3: Create position snapshots for each month-end date
            -- Cross-joins transaction balances with monthly dates to create time series
            SELECT 
                md.position_date as HoldingDate,
                tb.PortfolioID,
                tb.SecurityID,
                tb.TotalQuantity as Quantity,
                -- Market value calculations (using average transaction price as proxy)
                tb.TotalQuantity * tb.AvgPrice as MarketValue_Local,
                tb.TotalQuantity * tb.AvgPrice as MarketValue_Base,  -- Assume all USD for simplicity
                -- Cost basis calculations (slightly below market value for realistic P&L)
                tb.TotalQuantity * tb.AvgPrice * 0.95 as CostBasis_Local,  -- 5% unrealized gain
                tb.TotalQuantity * tb.AvgPrice * 0.95 as CostBasis_Base,
                0 as AccruedInterest_Local  -- Simplified
            FROM monthly_dates md
            CROSS JOIN transaction_balances tb
        ),
        portfolio_totals AS (
            -- Step 4: Calculate total portfolio values for weight calculations
            -- Sums all position values by portfolio and date for percentage calculations
            SELECT 
                HoldingDate,
                PortfolioID,
                SUM(MarketValue_Base) as PortfolioTotal  -- Total AUM per portfolio per date
            FROM position_snapshots
            GROUP BY HoldingDate, PortfolioID
        )
        -- Step 5: Final position records with calculated portfolio weights
        -- Joins position data with portfolio totals to calculate percentage allocations
        SELECT 
            ps.*,  -- All position snapshot columns
            -- Calculate portfolio weight as percentage of total portfolio value
            ps.MarketValue_Base / pt.PortfolioTotal as PortfolioWeight  -- Decimal weight (0.05 = 5%)
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


def build_esg_latest_view(session: Session):
    """Create flattened ESG view with one row per security for semantic view integration.
    
    This view provides the latest Overall ESG score for each security. It can be used
    for ESG analysis in agents via direct queries or through Cortex Analyst.
    """
    database_name = config.DATABASE['name']
    
    # Create standalone V_ESG_LATEST for direct queries
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
    
    # Check if returns view exists
    has_returns_view = False
    try:
        session.sql(f"SELECT 1 FROM {database_name}.CURATED.V_SECURITY_RETURNS LIMIT 1").collect()
        has_returns_view = True
        log_detail(f"  Including returns data in enriched holdings view (date-matched)")
    except:
        log_detail(f"  Returns view not available, creating holdings view without returns")
    
    # Create enriched holdings view with ESG data and date-matched returns
    # Join holdings with returns from the closest prior trading date (handles weekends/holidays)
    if has_returns_view:
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
    else:
        session.sql(f"""
            CREATE OR REPLACE VIEW {database_name}.CURATED.V_HOLDINGS_WITH_ESG AS
            SELECT 
                h.*,
                e.ESG_SCORE,
                e.ESG_GRADE,
                NULL as LATEST_PRICE,
                NULL as DAILY_RETURN_PCT,
                NULL as MTD_RETURN_PCT,
                NULL as QTD_RETURN_PCT,
                NULL as YTD_RETURN_PCT,
                NULL as RETURNS_DATE
            FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR h
            LEFT JOIN {database_name}.CURATED.V_ESG_LATEST e ON h.SecurityID = e.SecurityID
        """).collect()
    
    log_detail(f"  Created V_HOLDINGS_WITH_ESG enriched view")
    

def build_factor_exposures(session: Session):
    """Build factor exposures with SecurityID linkage using config-driven SQL generation.
    
    Uses config-driven SQL builders for:
    - Sector-based factor loadings (DATA_MODEL['synthetic_distributions']['by_sector'][*]['factors'])
    - Global factors like Size, Momentum (DATA_MODEL['synthetic_distributions']['global']['factor_globals'])
    - R² values (DATA_MODEL['synthetic_distributions']['global']['factor_r_squared'])
    """
    
    database_name = config.DATABASE['name']
    
    # Get max price date as upper bound (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_FACTOR_EXPOSURES. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Build config-driven SQL expressions for each factor
    market_beta_sql = build_factor_case_sql('es.SIC_DESCRIPTION', 'Market')
    size_factor_sql = build_global_uniform_sql('factor_globals.Size')
    value_factor_sql = build_factor_case_sql('es.SIC_DESCRIPTION', 'Value')
    momentum_factor_sql = build_global_uniform_sql('factor_globals.Momentum')
    growth_factor_sql = build_factor_case_sql('es.SIC_DESCRIPTION', 'Growth')
    quality_factor_sql = build_factor_case_sql('es.SIC_DESCRIPTION', 'Quality')
    volatility_factor_sql = build_factor_case_sql('es.SIC_DESCRIPTION', 'Volatility')
    
    # Get R² values from config
    r2_market = get_factor_r_squared('Market')
    r2_size = get_factor_r_squared('Size')
    r2_value = get_factor_r_squared('Value')
    r2_growth = get_factor_r_squared('Growth')
    r2_momentum = get_factor_r_squared('Momentum')
    r2_quality = get_factor_r_squared('Quality')
    r2_volatility = get_factor_r_squared('Volatility')
    
    session.sql(f"""
        -- Generate synthetic factor exposures (Value, Growth, Quality, etc.) for equity securities
        -- Creates factor loadings with sector-specific characteristics and realistic correlations
        -- Config-driven via DATA_MODEL['synthetic_distributions']
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_FACTOR_EXPOSURES AS
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
        monthly_dates AS (
            SELECT DATEADD(month, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, '{max_price_date}'::DATE)) as EXPOSURE_DATE
            FROM TABLE(GENERATOR(rowcount => {12 * config.YEARS_OF_HISTORY}))
            WHERE EXPOSURE_DATE <= '{max_price_date}'::DATE
        ),
        base_exposures AS (
            SELECT 
                es.SecurityID,
                md.EXPOSURE_DATE,
                -- Market beta (sector-specific from config)
                {market_beta_sql} as MARKET_BETA,
                -- Size factor (global from config)
                {size_factor_sql} as SIZE_FACTOR,
                -- Value factor (sector-specific from config)
                {value_factor_sql} as VALUE_FACTOR,
                -- Momentum factor (global from config)
                {momentum_factor_sql} as MOMENTUM_FACTOR,
                -- Growth factor (sector-specific from config)
                {growth_factor_sql} as GROWTH_FACTOR,
                -- Quality factor (sector-specific from config)
                {quality_factor_sql} as QUALITY_FACTOR,
                -- Volatility factor (sector-specific from config)
                {volatility_factor_sql} as VOLATILITY_FACTOR
            FROM equity_securities es
            CROSS JOIN monthly_dates md
        )
        SELECT SecurityID, EXPOSURE_DATE, 'Market' as FACTOR_NAME, MARKET_BETA as EXPOSURE_VALUE, {r2_market} as R_SQUARED FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Size', SIZE_FACTOR, {r2_size} FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Value', VALUE_FACTOR, {r2_value} FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Growth', GROWTH_FACTOR, {r2_growth} FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Momentum', MOMENTUM_FACTOR, {r2_momentum} FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Quality', QUALITY_FACTOR, {r2_quality} FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Volatility', VOLATILITY_FACTOR, {r2_volatility} FROM base_exposures
    """).collect()
    

def build_benchmark_holdings(session: Session):
    """Build benchmark holdings with SecurityID linkage using config-driven SQL generation.
    
    Uses config from BENCHMARKS[*]['holdings_rules'] for:
    - Constituent counts (e.g., 500 for S&P 500)
    - Filters (country, sector, or 'all')
    - Raw weight ranges (simple or country-differentiated)
    - Min weight thresholds
    - Assumed benchmark market value
    """
    
    database_name = config.DATABASE['name']
    
    # Get max price date as upper bound for benchmark holdings (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_BENCHMARK_HOLDINGS. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Build config-driven SQL for weight assignment and filtering
    # Generate CASE WHEN clauses from config
    weight_cases = []
    constituent_filter_cases = []
    
    for bm in config.BENCHMARKS:
        bm_name = bm['name']
        rules = bm['holdings_rules']  # Required field
        filters = rules['filters']  # Required field
        count = rules['constituent_count']  # Required field
        min_weight = rules['min_weight']  # Required field
        
        # Build filter condition
        filter_conds = []
        if 'country' in filters:
            filter_conds.append(f"es.CountryOfIncorporation = '{filters['country']}'")
        if 'sector' in filters:
            filter_conds.append(f"es.SIC_DESCRIPTION = '{filters['sector']}'")
        # 'all': True means no additional filter
        
        filter_sql = ' AND '.join(filter_conds) if filter_conds else 'TRUE'
        
        # Build weight expression
        if 'weight_by_country' in rules:
            # Country-differentiated weights (e.g., MSCI ACWI)
            wbc = rules['weight_by_country']
            weight_subcases = []
            for country, weight_range in wbc.items():
                if country != '_default':
                    weight_subcases.append(f"WHEN es.CountryOfIncorporation = '{country}' THEN UNIFORM({weight_range[0]}, {weight_range[1]}, RANDOM())")
            default_range = wbc['_default']  # Required default entry
            weight_sql = f"CASE {' '.join(weight_subcases)} ELSE UNIFORM({default_range[0]}, {default_range[1]}, RANDOM()) END"
        else:
            # Simple weight range - required field
            weight_range = rules['raw_weight_range']
            weight_sql = f"UNIFORM({weight_range[0]}, {weight_range[1]}, RANDOM())"
        
        # Weight case (applies filter for eligibility)
        weight_cases.append(f"WHEN b.BenchmarkName = '{bm_name}' AND {filter_sql} THEN {weight_sql}")
        
        # Constituent count filter
        constituent_filter_cases.append(f"(BenchmarkName = '{bm_name}' AND rn <= {count})")
    
    weight_case_sql = f"CASE {' '.join(weight_cases)} ELSE NULL END"
    constituent_filter_sql = ' OR '.join(constituent_filter_cases)
    
    # Get assumed benchmark MV from first benchmark's holdings_rules
    assumed_mv = config.BENCHMARKS[0]['holdings_rules']['assumed_benchmark_mv_usd']
    
    session.sql(f"""
        -- Generate synthetic benchmark holdings for major indices
        -- Creates realistic index compositions with market-cap weighted allocations
        -- Config-driven via BENCHMARKS[*]['holdings_rules']
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_BENCHMARK_HOLDINGS AS
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
                -- Weight logic from config
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
        normalized_weights AS (
            SELECT 
                *,
                RAW_WEIGHT / SUM(RAW_WEIGHT) OVER (PARTITION BY BenchmarkID, HOLDING_DATE) as WEIGHT
            FROM filtered_holdings
        )
        SELECT 
            BenchmarkID,
            SecurityID,
            HOLDING_DATE,
            WEIGHT as BENCHMARK_WEIGHT,
            WEIGHT * {assumed_mv} as MARKET_VALUE_USD
        FROM normalized_weights
        WHERE WEIGHT >= 0.0001  -- Minimum 0.01% weight
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
    """Build transaction cost and market microstructure data using config-driven SQL generation.
    
    Uses config-driven SQL builders for:
    - Sector-based bid-ask spreads, volume, market impact (DATA_MODEL['synthetic_distributions']['by_sector'][*]['transaction_costs'])
    - Country-based settlement days (DATA_MODEL['synthetic_distributions']['country_groups'][*]['settlement_days'])
    - Global commission rates (DATA_MODEL['synthetic_distributions']['global']['transaction_cost_globals'])
    """
    
    database_name = config.DATABASE['name']
    
    # Get max price date as upper bound (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_TRANSACTION_COSTS. "
            "Run generate_market_data.build_price_anchor() first."
        )
    
    # Build config-driven SQL expressions
    bid_ask_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'transaction_costs.bid_ask_spread_bps')
    volume_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'transaction_costs.daily_volume_m')
    impact_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'transaction_costs.market_impact_bps_per_1m')
    commission_sql = build_global_uniform_sql('transaction_cost_globals.commission_bps')
    settlement_sql = build_country_settlement_case_sql('es.CountryOfIncorporation')
    
    # Get window size from config
    from config_accessors import get_global_value
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
            FROM TABLE(GENERATOR(rowcount => {business_days_window}))  -- ~{business_months_window} months of business days
            WHERE DAYOFWEEK(COST_DATE) BETWEEN 2 AND 6
              AND COST_DATE <= '{max_price_date}'::DATE
        )
        SELECT 
            es.SecurityID,
            bd.COST_DATE,
            -- Bid-ask spread (bps) - sector-specific from config
            {bid_ask_sql} as BID_ASK_SPREAD_BPS,
            -- Average daily volume (shares in millions) - sector-specific from config
            {volume_sql} as AVG_DAILY_VOLUME_M,
            -- Market impact per $1M traded (bps) - sector-specific from config
            {impact_sql} as MARKET_IMPACT_BPS_PER_1M,
            -- Commission rate (bps) - global from config
            {commission_sql} as COMMISSION_BPS,
            -- Settlement period (days) - country-group-specific from config
            {settlement_sql} as SETTLEMENT_DAYS
        FROM equity_securities es
        CROSS JOIN business_dates bd
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
    from config_accessors import get_global_value
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
    from config_accessors import get_global_value
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
    from config_accessors import get_global_value
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
    from snowflake_io_utils import cleanup_temp_stages
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
    from config_accessors import get_global_value
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
    from config_accessors import get_global_value
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
    Generates alerts for ESG downgrades, concentration breaches, and other compliance issues.
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
            AlertType VARCHAR(50) NOT NULL,           -- 'ESG_DOWNGRADE', 'CONCENTRATION_BREACH', etc.
            AlertSeverity VARCHAR(20) NOT NULL,       -- 'WARNING', 'BREACH'
            OriginalValue VARCHAR(50),                -- e.g., 'A' (ESG grade before downgrade)
            CurrentValue VARCHAR(50),                 -- e.g., 'BBB' (current ESG grade)
            RequiresAction BOOLEAN NOT NULL,
            ActionDeadline DATE,                      -- Deadline for remediation (typically 30 days)
            AlertDescription TEXT,
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
    import snowflake_io_utils
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
    
    # Query positions that exceed concentration thresholds
    # Focus on SAM Technology & Infrastructure (per demo scenario)
    breach_threshold = config.COMPLIANCE_RULES['concentration']['max_single_issuer']  # 0.07 = 7%
    warning_threshold = config.COMPLIANCE_RULES['concentration']['warning_threshold']  # 0.065 = 6.5%
    
    # Get positions exceeding warning threshold from latest holdings
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
            WHERE h.PortfolioWeight >= {warning_threshold}
        )
        SELECT 
            PortfolioID,
            SecurityID,
            PortfolioWeight,
            MarketValue_Base,
            PortfolioName,
            Ticker,
            Description
        FROM latest_holdings
        WHERE rn = 1
        ORDER BY PortfolioWeight DESC
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
        is_breach = issue['PORTFOLIOWEIGHT'] >= breach_threshold
        
        # Spread alert dates across last 30 days (older alerts for higher concentrations)
        days_ago = min(28, 5 + i * 3)  # First alerts 5-28 days ago
        alert_date = today - timedelta(days=days_ago)
        action_deadline = alert_date + timedelta(days=30)
        
        severity = 'BREACH' if is_breach else 'WARNING'
        threshold_pct = breach_threshold * 100 if is_breach else warning_threshold * 100
        
        description = (
            f"{issue['TICKER']} ({issue['DESCRIPTION']}) position at {weight_pct:.1f}% "
            f"exceeds {threshold_pct:.1f}% {severity.lower()} threshold in {issue['PORTFOLIONAME']}. "
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
        from snowflake_io_utils import cleanup_temp_stages
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
    import snowflake_io_utils
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
    from snowflake_io_utils import cleanup_temp_stages
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
    from snowflake_io_utils import cleanup_temp_stages
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
    from config_accessors import get_country_value
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
    """Build corporate actions fact table using config-driven SQL.
    
    Uses config from DATA_MODEL['synthetic_distributions']['global']['corporate_actions']:
    - dividend_range_usd: Range for dividend amount per share
    - action_type_weights: Probability weights for action types
    - quarterly_event_frequency_days: Days between quarterly events
    - ex_date_offset_days, record_date_offset_days, payment_date_offset_days: Date offsets
    
    Includes pending corporate actions with ExDates in forward window from max_price_date for demo.
    """
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Get max_price_date for forward window generation
    max_price_date = get_max_price_date(session)
    
    # Get corporate action config values
    from config_accessors import get_global_value
    dividend_range = get_global_value('corporate_actions.dividend_range_usd', (0.50, 2.00))
    action_weights = get_global_value('corporate_actions.action_type_weights', {'Dividend': 0.90, 'Split': 0.07, 'Merger': 0.03})
    event_freq = get_global_value('corporate_actions.quarterly_event_frequency_days', 90)
    ex_offset = get_global_value('corporate_actions.ex_date_offset_days', 15)
    record_offset = get_global_value('corporate_actions.record_date_offset_days', 16)
    payment_offset = get_global_value('corporate_actions.payment_date_offset_days', 30)
    
    # Calculate action type thresholds from weights (cumulative)
    total_weight = sum(action_weights.values())
    dividend_threshold = action_weights['Dividend'] / total_weight * 3
    split_threshold = dividend_threshold + action_weights['Split'] / total_weight * 3
    
    dividend_sql = f"UNIFORM({dividend_range[0]}, {dividend_range[1]}, RANDOM())"
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    # Includes both historical actions and forward window pending actions for demo
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
        -- Forward window: Generate pending corporate actions with ExDates in next 10 days from max_price_date
        -- This ensures demo queries for "pending corporate actions in next 5 days" find data
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
                -- Mix of action types: 70% dividends, 20% splits, 10% mergers for demo
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
                -- All forward actions are pending for demo
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


def build_scenario_data(session: Session, scenario: str):
    """Build scenario-specific data."""
    
    if scenario == 'mandate_compliance' or scenario == 'portfolio_copilot':
        pass
        
        # Create tables
        _run_build_step(build_fact_compliance_alerts, session)
        _run_build_step(build_fact_pre_screened_replacements, session)
        
        # Generate demo data
        _run_build_step(generate_demo_compliance_alert, session)
        _run_build_step(generate_concentration_breach_alerts, session)
        _run_build_step(generate_demo_pre_screened_replacements, session)
        
        # Note: Report templates are generated via unstructured data hydration engine
        # They will be processed through generate_unstructured.py following the
        # template-based generation pattern defined in @unstructured-data-generation.mdc
        
    else:
        pass

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
    
