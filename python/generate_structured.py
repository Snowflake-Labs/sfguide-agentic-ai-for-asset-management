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
import pandas as pd
import os

def build_all(session: Session, scenarios: List[str], test_mode: bool = False):
    """
    Build all structured data using the enhanced data model.
    
    Args:
        session: Active Snowpark session
        scenarios: List of scenario names to build data for
        test_mode: If True, use 10% data volumes for faster testing
    """
    # print("Building structured data...")
    
    # Step 1: Create database and schemas
    create_database_structure(session)
    
    # Step 2: Build foundation tables in dependency order
    build_foundation_tables(session, test_mode)
    
    # Step 3: Build scenario-specific structured data
    for scenario in scenarios:
        build_scenario_data(session, scenario)
    
    # Step 4: Validate data quality
    validate_data_quality(session)
    
    # print("Structured data generation complete")

def create_database_structure(session: Session):
    """Create database and schema structure."""
    try:
        session.sql(f"CREATE OR REPLACE DATABASE {config.DATABASE['name']}").collect()
        session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.RAW").collect()
        session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.CURATED").collect()
        session.sql(f"CREATE OR REPLACE SCHEMA {config.DATABASE['name']}.AI").collect()
        # print(f" Database structure created: {config.DATABASE['name']}")
    except Exception as e:
        print(f"ERROR: Failed to create database structure: {e}")
        raise

def build_foundation_tables(session: Session, test_mode: bool = False):
    """Build all foundation tables in dependency order."""
    random.seed(config.RNG_SEED)
    
    # Create real assets view first (required for issuer and security dimensions)
    try:
        from extract_real_assets import create_real_assets_view
        create_real_assets_view(session)
    except Exception as e:
        print(f"ERROR: Real assets view creation failed: {e}")
        raise  # Don't continue without the view
    
    # Build all foundation tables (suppress detailed output)
    build_dim_issuer(session, test_mode)
    build_dim_security(session, test_mode)
    build_dim_portfolio(session)
    build_dim_benchmark(session)
    build_dim_supply_chain_relationships(session, test_mode)
    build_fact_transaction(session, test_mode)
    build_fact_position_daily_abor(session)
    build_fact_marketdata_timeseries(session, test_mode)
    build_sec_filings_and_fundamentals(session)
    build_fundamentals_and_estimates(session)
    build_esg_scores(session)
    build_factor_exposures(session)
    build_benchmark_holdings(session)
    build_transaction_cost_data(session)
    build_liquidity_data(session)
    build_risk_budget_data(session)
    build_trading_calendar_data(session)
    build_client_mandate_data(session)
    build_tax_implications_data(session)
    
    # Middle office tables
    build_dim_counterparty(session)
    build_dim_custodian(session)
    build_fact_trade_settlement(session, test_mode)
    build_fact_reconciliation(session, test_mode)
    build_fact_nav_calculation(session, test_mode)
    build_fact_nav_components(session, test_mode)
    build_fact_corporate_actions(session, test_mode)
    build_fact_corporate_action_impact(session, test_mode)
    build_fact_cash_movements(session, test_mode)
    build_fact_cash_positions(session, test_mode)




def build_dim_issuer(session: Session, test_mode: bool = False):
    """Build issuer dimension from COMPANY_INDEX with proper deduplication."""
    
    # print(" Building issuer dimension from SEC Filings COMPANY_INDEX")
    
    # Verify SEC Filings access (view depends on it)
    try:
        from extract_real_assets import verify_sec_filings_access
        verify_sec_filings_access(session)
    except Exception as e:
        print(f"ERROR: Error: {e}")
        raise
    
    # Build issuer dimension using COMPANY_INDEX as the authoritative source
    # This ensures one row per company, avoiding duplicates from multiple securities
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.DIM_ISSUER AS
        WITH company_data AS (
            -- Start with distinct companies from COMPANY_INDEX
            SELECT DISTINCT
                ci.COMPANY_NAME,
                ci.CIK,
                ci.PRIMARY_TICKER,
                ci.LEI,  -- LEI array from COMPANY_INDEX
                -- Get country from company characteristics
                MAX(CASE WHEN cc.RELATIONSHIP_TYPE = 'business_address_country' THEN cc.VALUE END) as COUNTRY_OF_DOMICILE,
                -- Get industry from SIC description (prefer this over NULL values)
                MAX(CASE WHEN cc.RELATIONSHIP_TYPE = 'sic_description' THEN cc.VALUE END) as INDUSTRY_SECTOR
            FROM {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.COMPANY_INDEX ci
            LEFT JOIN {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.COMPANY_CHARACTERISTICS cc
                ON ci.COMPANY_ID = cc.COMPANY_ID
            WHERE ci.COMPANY_NAME IS NOT NULL
                AND ci.COMPANY_NAME != 'Unknown'
                -- Only include companies that have securities in our V_REAL_ASSETS view
                AND EXISTS (
                    SELECT 1 
                    FROM {config.DATABASE['name']}.{config.DATABASE['schemas']['RAW'.lower()]}.V_REAL_ASSETS ra
                    WHERE ra.CIK = ci.CIK
                )
            GROUP BY ci.COMPANY_NAME, ci.CIK, ci.PRIMARY_TICKER, ci.LEI
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY COMPANY_NAME) as IssuerID,
            NULL as UltimateParentIssuerID,
            SUBSTR(TRIM(COMPANY_NAME), 1, 255) as LegalName,
            COALESCE(LEI[0]::VARCHAR, 'LEI' || LPAD(ABS(HASH(COMPANY_NAME)) % 1000000, 6, '0')) as LEI,
            COALESCE(COUNTRY_OF_DOMICILE, 'US') as CountryOfIncorporation,
            COALESCE(INDUSTRY_SECTOR, 'Diversified') as SIC_DESCRIPTION,
            CIK,
            PRIMARY_TICKER as PrimaryTicker
        FROM company_data
        WHERE COMPANY_NAME IS NOT NULL
        ORDER BY COMPANY_NAME
    """).collect()
    
    # Get count for reporting
    issuer_count = session.sql(f"SELECT COUNT(*) as cnt FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER").collect()[0]['CNT']
    # print(f" Created {issuer_count:,} distinct issuers from COMPANY_INDEX")
    
    # Report on data quality
    quality_stats = session.sql(f"""
        SELECT 
            COUNT(*) as total_issuers,
            COUNT(CASE WHEN CIK IS NOT NULL THEN 1 END) as issuers_with_cik,
            COUNT(CASE WHEN SIC_DESCRIPTION != 'Diversified' THEN 1 END) as issuers_with_industry,
            COUNT(CASE WHEN LEI NOT LIKE 'LEI%' OR LENGTH(LEI) > 20 THEN 1 END) as issuers_with_real_lei
        FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER
    """).collect()[0]
    
    # Suppressed: print(f"    With CIK: {quality_stats['ISSUERS_WITH_CIK']:,}")
    # Suppressed: print(f"    With Industry: {quality_stats['ISSUERS_WITH_INDUSTRY']:,}")
    # Suppressed: print(f"    With Real LEI: {quality_stats['ISSUERS_WITH_REAL_LEI']:,}")



def build_dim_security(session: Session, test_mode: bool = False):
    """Build securities from V_REAL_ASSETS view with proper issuer linkage via CIK."""
    
    # Use test mode counts if specified (for reporting only)
    securities_count = config.get_securities_count(test_mode)
    
    # print(" Building securities from real asset data")
    
    # Verify V_REAL_ASSETS view exists (should have been created during foundation build)
    try:
        from extract_real_assets import verify_real_assets_view_exists
        verify_real_assets_view_exists(session)
    except Exception as e:
        print(f"ERROR: Error: {e}")
        raise
    
    # Build security dimension using multi-strategy issuer linkage
    # Strategy 1: CIK matching (most accurate)
    # Strategy 2: SECURITY_NAME matching via COMPANY_SECURITY_RELATIONSHIPS
    # Strategy 3: Create synthetic issuer for remaining securities
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.DIM_SECURITY AS
        WITH parsed_securities AS (
            -- Parse bond ticker information (rate and maturity date)
            -- Examples: "DDD 5.5 12/15/16", "AAPL 2.3 05/11/22", "ONEM 3 06/15/25", "F 3.5 12/20/22 NOTZ"
            SELECT 
                ra.TOP_LEVEL_OPENFIGI_ID,
                ra.PRIMARY_TICKER,
                ra.SECURITY_NAME,
                ra.ASSET_CATEGORY,
                ra.COUNTRY_OF_DOMICILE,
                ra.CIK,
                -- Parse coupon rate from ticker (2nd space-separated token)
                -- "EXPE 5.95 08/15/20" -> SPLIT_PART 2 = "5.95"
                TRY_TO_DECIMAL(
                    SPLIT_PART(ra.PRIMARY_TICKER, ' ', 2),
                    10, 4
                ) as parsed_coupon_rate,
                -- Parse maturity date from ticker (3rd space-separated token in MM/DD/YY format)
                -- "EXPE 5.95 08/15/20" -> SPLIT_PART 3 = "08/15/20"
                TRY_TO_DATE(
                    SPLIT_PART(ra.PRIMARY_TICKER, ' ', 3),
                    'MM/DD/YY'
                ) as parsed_maturity_date
            FROM {config.DATABASE['name']}.{config.DATABASE['schemas']['RAW'.lower()]}.V_REAL_ASSETS ra
            WHERE ra.PRIMARY_TICKER IS NOT NULL
                AND ra.TOP_LEVEL_OPENFIGI_ID IS NOT NULL
                AND (
                    -- Corporate bonds can have longer tickers
                    (ra.ASSET_CATEGORY = 'Corporate Bond' AND LENGTH(ra.PRIMARY_TICKER) <= 50) OR
                    -- Equity and ETF have shorter tickers
                    (ra.ASSET_CATEGORY IN ('Equity', 'ETF') AND LENGTH(ra.PRIMARY_TICKER) <= 15)
                )
        ),
        filtered_securities AS (
            -- Filter out bonds that matured before our historical data period
            SELECT 
                ps.TOP_LEVEL_OPENFIGI_ID,
                ps.PRIMARY_TICKER,
                ps.SECURITY_NAME,
                ps.ASSET_CATEGORY,
                ps.COUNTRY_OF_DOMICILE,
                ps.CIK,
                ps.parsed_coupon_rate,
                ps.parsed_maturity_date
            FROM parsed_securities ps
            WHERE (
                -- Keep all non-bonds
                ps.ASSET_CATEGORY != 'Corporate Bond'
                OR
                -- For bonds, only keep those that mature after our data start date
                (ps.ASSET_CATEGORY = 'Corporate Bond' AND (
                    ps.parsed_maturity_date IS NULL OR  -- Keep if we can't parse date
                    ps.parsed_maturity_date >= DATE('2020-01-01')  -- Filter out pre-2020 maturities
                ))
            )
        ),
        issuer_matches_via_cik AS (
            -- Strategy 1: Match via CIK (most accurate, ~15K securities)
            SELECT 
                fs.TOP_LEVEL_OPENFIGI_ID,
                i.IssuerID,
                'CIK' as match_method
            FROM filtered_securities fs
            INNER JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i
                ON fs.CIK = i.CIK
        ),
        company_cik_mapping AS (
            -- Map COMPANY_ID to CIK for name-based matching
            SELECT DISTINCT
                ci.COMPANY_ID,
                ci.CIK
            FROM {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.COMPANY_INDEX ci
            WHERE ci.CIK IS NOT NULL
        ),
        issuer_matches_via_name AS (
            -- Strategy 2: Match via SECURITY_NAME for securities without CIK (~3.7K additional)
            SELECT DISTINCT
                fs.TOP_LEVEL_OPENFIGI_ID,
                i.IssuerID,
                'SECURITY_NAME' as match_method
            FROM filtered_securities fs
            LEFT JOIN issuer_matches_via_cik cik_match
                ON fs.TOP_LEVEL_OPENFIGI_ID = cik_match.TOP_LEVEL_OPENFIGI_ID
            INNER JOIN {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.COMPANY_SECURITY_RELATIONSHIPS csr
                ON fs.SECURITY_NAME = csr.SECURITY_NAME
            INNER JOIN company_cik_mapping ccm
                ON csr.COMPANY_ID = ccm.COMPANY_ID
            INNER JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i
                ON ccm.CIK = i.CIK
            WHERE cik_match.TOP_LEVEL_OPENFIGI_ID IS NULL  -- Only unmatched securities
        ),
        all_issuer_matches AS (
            -- Combine both matching strategies
            SELECT * FROM issuer_matches_via_cik
            UNION ALL
            SELECT * FROM issuer_matches_via_name
        ),
        unmatched_securities AS (
            -- Find securities that still have no issuer match
            SELECT DISTINCT
                fs.SECURITY_NAME,
                fs.COUNTRY_OF_DOMICILE
            FROM filtered_securities fs
            LEFT JOIN all_issuer_matches im
                ON fs.TOP_LEVEL_OPENFIGI_ID = im.TOP_LEVEL_OPENFIGI_ID
            WHERE im.IssuerID IS NULL
        ),
        synthetic_issuers AS (
            -- Strategy 3: Create synthetic issuers from SECURITY_NAME for remaining unmatched securities
            -- Assign IssuerIDs starting after the max existing IssuerID to avoid conflicts
            SELECT 
                us.SECURITY_NAME,
                (SELECT MAX(IssuerID) FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER) + ROW_NUMBER() OVER (ORDER BY us.SECURITY_NAME) as IssuerID,
                us.COUNTRY_OF_DOMICILE,
                'SYNTHETIC_FROM_SECURITY' as match_method
            FROM unmatched_securities us
        ),
        issuer_matches_via_synthetic AS (
            -- Strategy 3: Match via synthetic issuers created from SECURITY_NAME
            SELECT 
                fs.TOP_LEVEL_OPENFIGI_ID,
                si.IssuerID,
                'SYNTHETIC_FROM_SECURITY' as match_method
            FROM filtered_securities fs
            LEFT JOIN all_issuer_matches im
                ON fs.TOP_LEVEL_OPENFIGI_ID = im.TOP_LEVEL_OPENFIGI_ID
            INNER JOIN synthetic_issuers si
                ON fs.SECURITY_NAME = si.SECURITY_NAME
            WHERE im.IssuerID IS NULL  -- Only unmatched securities
        ),
        all_issuer_matches_with_synthetic AS (
            -- Combine all three matching strategies
            SELECT * FROM issuer_matches_via_cik
            UNION ALL
            SELECT * FROM issuer_matches_via_name
            UNION ALL
            SELECT * FROM issuer_matches_via_synthetic
        ),
        security_data AS (
            -- Join securities with matched issuers (including synthetic)
            SELECT 
                fs.TOP_LEVEL_OPENFIGI_ID,
                fs.PRIMARY_TICKER,
                fs.SECURITY_NAME,
                fs.ASSET_CATEGORY,
                fs.COUNTRY_OF_DOMICILE,
                fs.parsed_coupon_rate,
                fs.parsed_maturity_date,
                COALESCE(im.IssuerID, 1) as IssuerID,  -- Fallback to IssuerID=1 only if all strategies fail
                im.match_method
            FROM filtered_securities fs
            LEFT JOIN all_issuer_matches_with_synthetic im
                ON fs.TOP_LEVEL_OPENFIGI_ID = im.TOP_LEVEL_OPENFIGI_ID
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY ASSET_CATEGORY, PRIMARY_TICKER) as SecurityID,
            COALESCE(IssuerID, 1) as IssuerID,
            PRIMARY_TICKER as Ticker,
            TOP_LEVEL_OPENFIGI_ID as FIGI,
            SUBSTR(SECURITY_NAME, 1, 255) as Description,
            ASSET_CATEGORY as AssetClass,
            CASE 
                WHEN ASSET_CATEGORY = 'Equity' THEN 'Common Stock'
                WHEN ASSET_CATEGORY = 'Corporate Bond' THEN 'Corporate Bond'
                WHEN ASSET_CATEGORY = 'ETF' THEN 'Exchange Traded Fund'
                ELSE 'Other'
            END as SecurityType,
            COALESCE(COUNTRY_OF_DOMICILE, 'US') as CountryOfRisk,
            DATE('2010-01-01') as IssueDate,
            -- Use parsed maturity date for bonds, or default to 2030
            CASE 
                WHEN ASSET_CATEGORY = 'Corporate Bond' THEN COALESCE(parsed_maturity_date, DATE('2030-01-01'))
                ELSE NULL
            END as MaturityDate,
            -- Use parsed coupon rate for bonds, or default to 5.0
            CASE 
                WHEN ASSET_CATEGORY = 'Corporate Bond' THEN COALESCE(parsed_coupon_rate, 5.0)
                ELSE NULL
            END as CouponRate,
            CURRENT_TIMESTAMP() as RecordStartDate,
            NULL as RecordEndDate,
            TRUE as IsActive,
            match_method  -- Track which matching strategy was used for reporting
        FROM security_data
        ORDER BY SecurityID
    """).collect()
    
    # Insert synthetic issuers into DIM_ISSUER table for securities that needed synthetic matching
    # This ensures referential integrity and enables proper issuer-level analysis
    session.sql(f"""
        INSERT INTO {config.DATABASE['name']}.CURATED.DIM_ISSUER (
            IssuerID,
            UltimateParentIssuerID,
            LegalName,
            LEI,
            CountryOfIncorporation,
            SIC_DESCRIPTION,
            CIK
        )
        SELECT DISTINCT
            s.IssuerID,
            NULL as UltimateParentIssuerID,
            s.Description as LegalName,
            'SYNTHETIC' || LPAD(s.IssuerID, 10, '0') as LEI,
            s.CountryOfRisk as CountryOfIncorporation,
            'Diversified' as SIC_DESCRIPTION,
            NULL as CIK
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
        WHERE s.match_method = 'SYNTHETIC_FROM_SECURITY'
            AND NOT EXISTS (
                SELECT 1 FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER i
                WHERE i.IssuerID = s.IssuerID
            )
    """).collect()
    
    # Get and report counts
    count_by_class = session.sql(f"""
        SELECT AssetClass, COUNT(*) as cnt 
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY 
        GROUP BY AssetClass
        ORDER BY AssetClass
    """).collect()
    
    total_securities = sum(row['CNT'] for row in count_by_class)
    # print(f" Created {total_securities:,} securities from real asset data")
    
    for row in count_by_class:
        pass
        # print(f"    {row['ASSETCLASS']}: {row['CNT']:,} securities")
    
    # Validate issuer linkage quality with detailed breakdown
    linkage_stats = session.sql(f"""
        SELECT 
            COUNT(DISTINCT IssuerID) as distinct_issuers_linked,
            COUNT(CASE WHEN IssuerID = 1 THEN 1 END) as securities_without_issuer,
            SUM(CASE WHEN match_method = 'CIK' THEN 1 ELSE 0 END) as matched_via_cik,
            SUM(CASE WHEN match_method = 'SECURITY_NAME' THEN 1 ELSE 0 END) as matched_via_name,
            SUM(CASE WHEN match_method = 'SYNTHETIC_FROM_SECURITY' THEN 1 ELSE 0 END) as matched_via_synthetic,
            SUM(CASE WHEN match_method IS NULL THEN 1 ELSE 0 END) as unmatched
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY
    """).collect()[0]
    
    # Suppressed: print(f"    Issuer linkage results:")
    # Suppressed: print(f"      • Matched via CIK: {linkage_stats['MATCHED_VIA_CIK']:,} securities")
    # Suppressed: print(f"      • Matched via SECURITY_NAME: {linkage_stats['MATCHED_VIA_NAME']:,} securities")
    # Suppressed: print(f"      • Matched via synthetic issuer: {linkage_stats['MATCHED_VIA_SYNTHETIC']:,} securities")
    # Suppressed: print(f"      • Unmatched (using default): {linkage_stats['UNMATCHED']:,} securities")
    # Suppressed: print(f"    Linked to {linkage_stats['DISTINCT_ISSUERS_LINKED']:,} distinct issuers")
    
    total_matched = linkage_stats['MATCHED_VIA_CIK'] + linkage_stats['MATCHED_VIA_NAME'] + linkage_stats['MATCHED_VIA_SYNTHETIC']
    pct_matched = 100.0 * total_matched / total_securities
    # Suppressed: print(f"   ✅ {pct_matched:.1f}% of securities have issuer linkage")
    
    if linkage_stats['UNMATCHED'] > 0:
        pct_unmatched = 100.0 * linkage_stats['UNMATCHED'] / total_securities
        # print(f"   ℹ️  {pct_unmatched:.1f}% securities without issuer match (edge cases only)")
    
    # Report on bond parsing success
    bond_stats = session.sql(f"""
        SELECT 
            COUNT(*) as total_bonds,
            COUNT(CASE WHEN CouponRate != 5.0 THEN 1 END) as bonds_with_parsed_rate,
            COUNT(CASE WHEN MaturityDate != DATE('2030-01-01') THEN 1 END) as bonds_with_parsed_maturity,
            MIN(MaturityDate) as earliest_maturity,
            MAX(MaturityDate) as latest_maturity
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY
        WHERE AssetClass = 'Corporate Bond'
    """).collect()
    
    if bond_stats and bond_stats[0]['TOTAL_BONDS'] > 0:
        pass
        # print(f"    Bond parsing results:")
        # print(f"      • Bonds with parsed coupon rate: {bond_stats[0]['BONDS_WITH_PARSED_RATE']:,} of {bond_stats[0]['TOTAL_BONDS']:,}")
        # print(f"      • Bonds with parsed maturity: {bond_stats[0]['BONDS_WITH_PARSED_MATURITY']:,} of {bond_stats[0]['TOTAL_BONDS']:,}")
        # print(f"      • Maturity range: {bond_stats[0]['EARLIEST_MATURITY']} to {bond_stats[0]['LATEST_MATURITY']}")


def build_dim_portfolio(session: Session):
    """Build portfolio dimension from unified PORTFOLIOS configuration."""
    
    portfolio_data = []
    for i, (portfolio_name, portfolio_config) in enumerate(config.PORTFOLIOS.items()):
        # Use strategy from config, with intelligent fallback
        strategy = portfolio_config.get('strategy', 'Equity')
            
        portfolio_data.append({
            'PortfolioID': i + 1,
            'PortfolioCode': f"{config.DATA_MODEL['portfolio_code_prefix']}_{i+1:02d}",
            'PortfolioName': portfolio_name,
            'Strategy': strategy,
            'BaseCurrency': portfolio_config.get('base_currency', 'USD'),
            'InceptionDate': datetime.strptime(portfolio_config.get('inception_date', '2019-01-01'), '%Y-%m-%d').date()
        })
    
    portfolios_df = session.create_dataframe(portfolio_data)
    portfolios_df.write.mode("overwrite").save_as_table(f"{config.DATABASE['name']}.CURATED.DIM_PORTFOLIO")
    
    # print(f" Created {len(portfolio_data)} portfolios from unified config")

def build_dim_benchmark(session: Session):
    """Build benchmark dimension."""
    
    benchmark_data = []
    for i, benchmark in enumerate(config.BENCHMARKS):
        benchmark_data.append({
            'BenchmarkID': i + 1,
            'BenchmarkName': benchmark['name'],
            'Provider': benchmark['provider']
        })
    
    benchmarks_df = session.create_dataframe(benchmark_data)
    benchmarks_df.write.mode("overwrite").save_as_table(f"{config.DATABASE['name']}.CURATED.DIM_BENCHMARK")
    
    # print(f" Created {len(benchmark_data)} benchmarks")

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
    
    # print("🔗 Building supply chain relationships...")
    
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
    
    # Step 2: Get issuer IDs for demo companies
    issuer_map = {}
    for ticker, company_info in config.SUPPLY_CHAIN_DEMO_COMPANIES.items():
        try:
            # Try with both ticker and FIGI first
            result = session.sql(f"""
                SELECT i.IssuerID, i.LegalName
                FROM {database_name}.CURATED.DIM_ISSUER i
                JOIN {database_name}.CURATED.DIM_SECURITY s ON i.IssuerID = s.IssuerID
                WHERE s.Ticker = '{ticker}' AND s.FIGI = '{company_info['openfigi_id']}'
                LIMIT 1
            """).collect()
            
            # If not found, try with just ticker (for non-US companies like TSM)
            if not result:
                result = session.sql(f"""
                    SELECT i.IssuerID, i.LegalName
                    FROM {database_name}.CURATED.DIM_ISSUER i
                    JOIN {database_name}.CURATED.DIM_SECURITY s ON i.IssuerID = s.IssuerID
                    WHERE s.Ticker = '{ticker}'
                    LIMIT 1
                """).collect()
            
            if result:
                issuer_map[ticker] = result[0]['ISSUERID']
            else:
                print(f"WARNING: Could not find issuer for {ticker}")
        except Exception as e:
            pass
            # print(f"     Error looking up {ticker}: {e}")
    
    # Step 3: Create demo relationships from config
    relationships = []
    relationship_id = 1
    
    if not issuer_map:
        pass
        # print(f"     No demo companies found in DIM_ISSUER")
        # print(f"   Available tickers in database:")
        available_tickers = session.sql(f"""
            SELECT DISTINCT s.Ticker 
            FROM {database_name}.CURATED.DIM_SECURITY s
            WHERE s.Ticker IN ('TSM', 'NVDA', 'AMD', 'AAPL', 'GM', 'F')
            ORDER BY s.Ticker
        """).collect()
        for row in available_tickers:
            pass
            # print(f"      - {row['TICKER']}")
    
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
        # print(f" Created {len(relationships)} supply chain relationships")
        # print(f"   - {len([r for r in relationships if 'Demo' in r.get('Notes', '')])} demo relationships")
        # print(f"   - {len([r for r in relationships if 'Industry' in r.get('Notes', '')])} industry relationships")
    else:
        print("WARNING:  No supply chain relationships created")

def build_fact_transaction(session: Session, test_mode: bool = False):
    """Generate synthetic transaction history."""
    
    # Verify DIM_SECURITY table has FIGI column before proceeding
    try:
        columns = session.sql(f"DESCRIBE TABLE {config.DATABASE['name']}.CURATED.DIM_SECURITY").collect()
        column_names = [col['name'] for col in columns]
        if 'FIGI' not in column_names:
            raise Exception(f"DIM_SECURITY table missing FIGI column. Available columns: {column_names}")
        # print(" Verified DIM_SECURITY table has FIGI column")
    except Exception as e:
        print(f"ERROR: Table structure verification failed: {e}")
        raise
    
    # Generate transactions for the last 12 months that build up to current positions
    # print("💱 Generating synthetic transaction history...")
    
    # Get SQL mapping for demo portfolios (eliminates hardcoded company references)
    demo_sql_mapping = config.build_demo_portfolios_sql_mapping()
    
    # This is a simplified version - in a real implementation, we'd generate
    # realistic transaction patterns that result in the desired end positions
    session.sql(f"""
        -- Generate synthetic transaction history that builds to realistic portfolio positions
        -- This creates a complete audit trail of BUY transactions over the past 12 months
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_TRANSACTION AS
        WITH all_us_securities AS (
            -- Step 1a: Identify all equity securities with priority rankings
            -- Creates a priority ranking system to ensure portfolios hold recognizable securities
            SELECT 
                s.SecurityID,
                s.IssuerID,
                s.Ticker,
                s.FIGI,
                CASE 
                    -- Priority 1-4: Demo companies with their configured priorities from config.DEMO_COMPANIES
                    {config.get_demo_company_priority_sql()}
                    -- Priority 5: Other major US stocks from config.MAJOR_US_STOCKS
                    WHEN s.Ticker IN {config.safe_sql_tuple(config.get_major_us_stocks('tier1'))} 
                         AND i.CountryOfIncorporation = 'US' THEN 5
                    -- Priority 6: All other US equities (using data model columns)
                    WHEN i.CountryOfIncorporation = 'US' AND s.AssetClass = 'Equity' THEN 6
                    -- Priority 7: Non-US equities
                    WHEN s.AssetClass = 'Equity' THEN 7
                    -- Priority 8: All other asset types
                    ELSE 8
                END as priority,
                -- Rank securities within each issuer to select only one per issuer
                ROW_NUMBER() OVER (PARTITION BY s.IssuerID ORDER BY 
                    CASE 
                        -- Prioritize demo companies using config priorities
                        {config.get_demo_company_priority_sql()}
                        -- Then prefer Equity over other asset classes
                        WHEN s.AssetClass = 'Equity' THEN 10
                        -- Then other asset types
                        ELSE 20
                    END,
                    LENGTH(s.Ticker),  -- Prefer shorter tickers (common stock over ADRs)
                    s.SecurityID  -- Deterministic tiebreaker
                ) as issuer_rank
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'  -- Focus on equities for transaction generation
        ),
        major_us_securities AS (
            -- Step 1b: Select only one security per issuer to avoid duplicates like "Commercial Metals Co" appearing twice
            SELECT 
                SecurityID,
                Ticker,
                FIGI,
                priority
            FROM all_us_securities
            WHERE issuer_rank = 1  -- Only the primary security for each issuer
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
                    WHEN p.PortfolioName IN {config.safe_sql_tuple(config.get_demo_portfolio_names())} THEN
                        CASE 
                            -- Guaranteed top holdings (order from config)
                            {demo_sql_mapping['guaranteed_case_when_sql']}
                            -- Additional demo holdings
                            WHEN s.FIGI IN {demo_sql_mapping['additional_figis']} THEN {demo_sql_mapping['additional_priority']}
                            -- Filler stocks (from config.MAJOR_US_STOCKS)
                            WHEN s.Ticker IN {config.safe_sql_tuple(config.get_major_us_stocks('all'))} THEN {demo_sql_mapping['additional_priority'] + 1}
                            ELSE 999  -- Exclude non-demo companies from demo portfolios
                        END
                    ELSE s.priority  -- Use normal priority for non-demo portfolios
                END as portfolio_priority,
                -- Random ordering within priority groups for portfolio diversification
                ROW_NUMBER() OVER (PARTITION BY p.PortfolioID ORDER BY 
                    CASE 
                        WHEN p.PortfolioName IN {config.safe_sql_tuple(config.get_demo_portfolio_names())} THEN
                            CASE 
                                -- Use OpenFIGI IDs for precise ordering (from config.PORTFOLIOS)
                                {demo_sql_mapping['guaranteed_case_when_sql']}
                                -- Additional holdings
                                WHEN s.FIGI IN {demo_sql_mapping['additional_figis']} THEN {demo_sql_mapping['additional_priority']}
                                -- Filler stocks
                                WHEN s.Ticker IN {config.safe_sql_tuple(config.get_major_us_stocks('all'))} THEN {demo_sql_mapping['additional_priority'] + 1}
                                ELSE 999
                            END
                        ELSE s.priority
                    END, 
                    RANDOM()
                ) as rn
            FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO p
            CROSS JOIN major_us_securities s
        ),
        selected_holdings AS (
            -- Step 3: Limit each portfolio to ~45 securities with theme-specific filtering
            SELECT PortfolioID, SecurityID
            FROM portfolio_securities
            WHERE rn <= 45  -- Typical large-cap equity portfolio size
            AND (
                -- For demo portfolios, only include securities with valid priorities (from config.PORTFOLIOS)
                (PortfolioName IN {config.safe_sql_tuple(config.get_demo_portfolio_names())} AND portfolio_priority < 999)
                OR 
                -- For non-demo portfolios, use normal selection
                (PortfolioName NOT IN {config.safe_sql_tuple(config.get_demo_portfolio_names())})
            )
        ),
        business_days AS (
            -- Step 4a: Generate all business days over the past 12 months
            -- Creates complete set of Monday-Friday trading days
            SELECT generated_date as trade_date
            FROM (
                SELECT DATEADD(day, seq4(), DATEADD(month, -{config.DATA_MODEL['transaction_months']}, CURRENT_DATE())) as generated_date
                FROM TABLE(GENERATOR(rowcount => {365 * config.DATA_MODEL['transaction_months'] // 12}))
            )
            WHERE DAYOFWEEK(generated_date) BETWEEN 1 AND 5
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
            -- Strategic position sizing: larger positions for demo portfolio top holdings (fully from config.PORTFOLIOS)
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s 
                    JOIN {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO p ON sh.PortfolioID = p.PortfolioID
                    WHERE s.SecurityID = sh.SecurityID 
                    AND p.PortfolioName IN {config.safe_sql_tuple(config.get_demo_portfolio_names())}  -- Any demo portfolio from config
                    AND s.FIGI IN {demo_sql_mapping['large_position_figis']}  -- Holdings marked as 'large' in config.PORTFOLIOS
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
    
    # print(" Created transaction history")

def build_fact_position_daily_abor(session: Session):
    """Build ABOR positions from transaction log."""
    
    # print("📋 Building ABOR positions from transactions...")
    
    session.sql(f"""
        -- Build ABOR (Accounting Book of Record) positions from transaction history
        -- This creates monthly position snapshots by aggregating transaction data
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR AS
        WITH monthly_dates AS (
            -- Step 1: Generate month-end dates for position snapshots over 5 years of history
            -- Uses LAST_DAY to ensure consistent month-end reporting dates
            SELECT LAST_DAY(DATEADD(month, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE()))) as position_date
            FROM TABLE(GENERATOR(rowcount => {12 * config.YEARS_OF_HISTORY}))  -- 60 month-end dates
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
    
    # print(" Created ABOR positions")

def build_fact_marketdata_timeseries(session: Session, test_mode: bool = False):
    """Build synthetic market data for all securities."""
    
    # print("📝 Generating synthetic market data for portfolio securities only")
    build_marketdata_synthetic(session)

def build_marketdata_synthetic(session: Session):
    """Build synthetic market data."""
    
    session.sql(f"""
        -- Generate synthetic market data (OHLCV) for all securities over 5 years
        -- Creates realistic price movements and trading volumes for demo purposes
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_MARKETDATA_TIMESERIES AS
        WITH business_dates AS (
            -- Step 1: Generate business days (Monday-Friday) over 5 years of history
            -- Excludes weekends to match real market trading calendar
            SELECT DATEADD(day, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())) as price_date
            FROM TABLE(GENERATOR(rowcount => {365 * config.YEARS_OF_HISTORY}))  -- ~1,825 days total
            WHERE DAYOFWEEK(price_date) BETWEEN 1 AND 5  -- Monday=1 to Friday=5 only
        ),
        portfolio_securities AS (
            -- Step 2: Get only securities that are held in portfolios
            SELECT DISTINCT 
                s.SecurityID,
                s.AssetClass
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            WHERE EXISTS (
                SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        securities_dates AS (
            -- Step 3: Create cartesian product of portfolio securities with business dates
            -- This ensures every portfolio security has price data for every trading day
            SELECT 
                ps.SecurityID,
                ps.AssetClass,  -- Used for asset-class-specific price ranges
                bd.price_date as PriceDate
            FROM portfolio_securities ps
            CROSS JOIN business_dates bd
        )
        -- Step 3: Generate realistic OHLCV data with asset-class-appropriate price ranges
        SELECT 
            PriceDate,
            SecurityID,
            -- Opening prices with asset-class-specific ranges and daily volatility
            CASE 
                WHEN AssetClass = 'Equity' THEN UNIFORM(50, 850, RANDOM())        -- Equity: $50-$850
                WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(90, 110, RANDOM()) -- Bonds: $90-$110 (near par)
                ELSE UNIFORM(50, 450, RANDOM())                                   -- ETFs/Other: $50-$450
            END * (1 + (UNIFORM(-0.02, 0.02, RANDOM()))) as Price_Open,  -- ±2% daily variation
            
            -- High prices (always above base price)
            CASE 
                WHEN AssetClass = 'Equity' THEN UNIFORM(50, 850, RANDOM())
                WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(90, 110, RANDOM())
                ELSE UNIFORM(50, 450, RANDOM())
            END * (1 + UNIFORM(0, 0.03, RANDOM())) as Price_High,  -- 0-3% above base
            
            -- Low prices (always below base price)
            CASE 
                WHEN AssetClass = 'Equity' THEN UNIFORM(50, 850, RANDOM())
                WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(90, 110, RANDOM())
                ELSE UNIFORM(50, 450, RANDOM())
            END * (1 - UNIFORM(0, 0.03, RANDOM())) as Price_Low,   -- 0-3% below base
            
            -- Closing prices (base price without additional variation)
            CASE 
                WHEN AssetClass = 'Equity' THEN UNIFORM(50, 850, RANDOM())
                WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(90, 110, RANDOM())
                ELSE UNIFORM(50, 450, RANDOM())
            END as Price_Close,
            
            -- Trading volumes with asset-class-appropriate ranges
            CASE 
                WHEN AssetClass = 'Equity' THEN UNIFORM(100000, 10000000, RANDOM())::int      -- High equity volumes
                WHEN AssetClass = 'Corporate Bond' THEN UNIFORM(10000, 1000000, RANDOM())::int -- Lower bond volumes
                ELSE UNIFORM(50000, 5000000, RANDOM())::int                                   -- Moderate ETF volumes
            END as Volume,
            
            -- Total return factor (simplified to 1.0 for now - could include dividends/interest)
            1.0 as TotalReturnFactor_Daily
        FROM securities_dates
    """).collect()
    
    # print(" Created synthetic market data")

# Placeholder functions for remaining tables (to be implemented)
def build_fundamentals_and_estimates(session: Session):
    """Build fundamentals and estimates tables with SecurityID linkage."""
    
    # Build fundamentals table with realistic financial data
    session.sql(f"""
        -- Generate synthetic fundamental data (revenue, earnings, ratios) for equity securities
        -- Creates quarterly financial metrics with sector-appropriate ranges for 5 years
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_FUNDAMENTALS AS
        WITH equity_securities AS (
            SELECT 
                s.SecurityID as SECURITY_ID,
                s.Ticker,
                i.SIC_DESCRIPTION
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        quarters AS (
            SELECT 
                DATEADD(quarter, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())) as REPORTING_DATE,
                'Q' || QUARTER(DATEADD(quarter, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE()))) || 
                ' ' || YEAR(DATEADD(quarter, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE()))) as FISCAL_QUARTER
            FROM TABLE(GENERATOR(rowcount => {4 * config.YEARS_OF_HISTORY}))
        ),
        base_metrics AS (
            SELECT 
                es.SECURITY_ID,
                q.REPORTING_DATE,
                q.FISCAL_QUARTER,
                -- Base financial metrics scaled by sector
                CASE 
                    WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(1000000000, 100000000000, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Health Care' THEN UNIFORM(5000000000, 50000000000, RANDOM())
                    ELSE UNIFORM(500000000, 20000000000, RANDOM())
                END as BASE_REVENUE,
                CASE 
                    WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(0.15, 0.35, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Health Care' THEN UNIFORM(0.20, 0.40, RANDOM())
                    ELSE UNIFORM(0.05, 0.25, RANDOM())
                END as NET_MARGIN
            FROM equity_securities es
            CROSS JOIN quarters q
        )
        SELECT SECURITY_ID, REPORTING_DATE, FISCAL_QUARTER, 'Total Revenue' as METRIC_NAME, BASE_REVENUE as METRIC_VALUE, 'USD' as CURRENCY FROM base_metrics
        UNION ALL
        SELECT SECURITY_ID, REPORTING_DATE, FISCAL_QUARTER, 'Net Income' as METRIC_NAME, BASE_REVENUE * NET_MARGIN as METRIC_VALUE, 'USD' as CURRENCY FROM base_metrics
        UNION ALL  
        SELECT SECURITY_ID, REPORTING_DATE, FISCAL_QUARTER, 'EPS' as METRIC_NAME, (BASE_REVENUE * NET_MARGIN) / UNIFORM(1000000000, 10000000000, RANDOM()) as METRIC_VALUE, 'USD' as CURRENCY FROM base_metrics
        UNION ALL
        SELECT SECURITY_ID, REPORTING_DATE, FISCAL_QUARTER, 'Trailing P/E' as METRIC_NAME, UNIFORM(10, 40, RANDOM()) as METRIC_VALUE, 'USD' as CURRENCY FROM base_metrics
        UNION ALL
        SELECT SECURITY_ID, REPORTING_DATE, FISCAL_QUARTER, 'Revenue Growth' as METRIC_NAME, UNIFORM(-0.1, 0.3, RANDOM()) as METRIC_VALUE, 'USD' as CURRENCY FROM base_metrics
    """).collect()
    
    # Build estimates table with guidance
    session.sql(f"""
        -- Generate synthetic analyst estimates and guidance based on fundamental data
        -- Creates forward-looking revenue and earnings estimates with realistic consensus ranges
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_ESTIMATES AS
        WITH estimate_base AS (
            SELECT 
                f.SECURITY_ID,
                f.REPORTING_DATE as ESTIMATE_DATE,
                CASE 
                    WHEN QUARTER(f.REPORTING_DATE) = 4 THEN 'Q1 ' || (YEAR(f.REPORTING_DATE) + 1)
                    ELSE 'Q' || (QUARTER(f.REPORTING_DATE) + 1) || ' ' || YEAR(f.REPORTING_DATE)
                END as FISCAL_PERIOD,
                f.METRIC_VALUE
            FROM {config.DATABASE['name']}.CURATED.FACT_FUNDAMENTALS f
            WHERE f.METRIC_NAME IN ('Total Revenue', 'EPS')
        )
        SELECT 
            SECURITY_ID,
            ESTIMATE_DATE,
            FISCAL_PERIOD,
            CASE WHEN METRIC_VALUE > 1000000 THEN 'Revenue Estimate' ELSE 'EPS Estimate' END as METRIC_NAME,
            METRIC_VALUE * (1 + UNIFORM(-0.1, 0.1, RANDOM())) as ESTIMATE_VALUE,
            METRIC_VALUE * (1 + UNIFORM(-0.15, -0.05, RANDOM())) as GUIDANCE_LOW,
            METRIC_VALUE * (1 + UNIFORM(0.05, 0.15, RANDOM())) as GUIDANCE_HIGH,
            'USD' as CURRENCY
        FROM estimate_base
    """).collect()
    
    # print(" Created fundamentals and estimates with realistic relationships")

def build_sec_filings_and_fundamentals(session: Session):
    """Build SEC filings table and synthetic fundamentals as fallback."""
    
    # First, create the FACT_SEC_FILINGS table structure
    # print("🏗️  Creating FACT_SEC_FILINGS table structure...")
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_SEC_FILINGS (
            FilingID BIGINT IDENTITY(1,1) PRIMARY KEY,
            SecurityID BIGINT NOT NULL,
            IssuerID BIGINT NOT NULL,
            CIK VARCHAR(20) NOT NULL,
            CompanyName VARCHAR(255),
            FiscalYear INTEGER NOT NULL,
            FiscalPeriod VARCHAR(10) NOT NULL,           -- 'Q1', 'Q2', 'Q3', 'Q4', 'FY'
            FormType VARCHAR(10) NOT NULL,               -- '10-K', '10-Q', '8-K'
            FilingDate DATE NOT NULL,
            PeriodStartDate DATE,                        -- From SEC_REPORT_ATTRIBUTES.PERIOD_START_DATE
            PeriodEndDate DATE,                          -- From SEC_REPORT_ATTRIBUTES.PERIOD_END_DATE
            ReportingDate DATE NOT NULL,                 -- Standardized reporting date
            -- SEC measures (preserving original measure names and descriptions)
            TAG VARCHAR(200) NOT NULL,
            MeasureDescription VARCHAR(500),
            MeasureValue DECIMAL(38, 2),
            UnitOfMeasure VARCHAR(50),
            Statement VARCHAR(100),                      -- Financial statement: Income Statement, Balance Sheet, Cash Flow
            -- Data lineage
            DataSource VARCHAR(50) DEFAULT 'SEC_FILINGS_CYBERSYN',
            LoadTimestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """).collect()
    
    # Try to load real SEC filing data, fallback to synthetic fundamentals if not available
    try:
        pass
        # print("📄 Attempting to load real SEC filing data...")
        
        # Test SEC_FILINGS database access
        test_result = session.sql(f"SELECT COUNT(*) as cnt FROM {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.SEC_REPORT_ATTRIBUTES LIMIT 1").collect()
        # print(" SEC_FILINGS database accessible")
        
        # Load SEC filing data using our enhanced view approach
        session.sql(f"""
            INSERT INTO {config.DATABASE['name']}.CURATED.FACT_SEC_FILINGS 
            SELECT 
                ROW_NUMBER() OVER (ORDER BY i.IssuerID, sri.FISCAL_YEAR, sri.FISCAL_PERIOD, sra.TAG) as FilingID,
                s.SecurityID,
                i.IssuerID,
                sra.CIK,
                i.LegalName as CompanyName,
                sri.FISCAL_YEAR as FiscalYear,
                sri.FISCAL_PERIOD as FiscalPeriod,
                sri.FORM_TYPE as FormType,
                sri.FILED_DATE as FilingDate,
                sra.PERIOD_START_DATE as PeriodStartDate,
                sra.PERIOD_END_DATE as PeriodEndDate,
                sri.FILED_DATE as ReportingDate,  -- Use filing date as reporting date (actual submission date)
                sra.TAG,
                sra.MEASURE_DESCRIPTION as MeasureDescription,
                sra.VALUE as MeasureValue,
                sra.UNIT_OF_MEASURE as UnitOfMeasure,
                sra.STATEMENT,
                'SEC_FILINGS_CYBERSYN' as DataSource,
                CURRENT_TIMESTAMP() as LoadTimestamp
            FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER i
            JOIN {config.DATABASE['name']}.CURATED.DIM_SECURITY s 
                ON s.IssuerID = i.IssuerID 
                AND s.Ticker = i.PrimaryTicker
            JOIN {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.SEC_REPORT_ATTRIBUTES sra ON i.CIK = sra.CIK
            JOIN {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.SEC_REPORT_INDEX sri ON sra.ADSH = sri.ADSH AND sra.CIK = sri.CIK
            WHERE s.AssetClass = 'Equity'
                AND sri.FISCAL_YEAR >= YEAR(CURRENT_DATE) - {config.YEARS_OF_HISTORY}
                AND sri.FORM_TYPE IN ('10-K', '10-Q')
                AND sra.TAG IN (
                    -- Income Statement
                    'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
                    'NetIncomeLoss', 'GrossProfit', 'OperatingIncomeLoss',
                    'InterestExpense', 'GeneralAndAdministrativeExpense', 'OperatingExpenses',
                    'EarningsPerShareBasic', 'EarningsPerShareDiluted',
                    -- Balance Sheet
                    'Assets', 'AssetsCurrent', 'StockholdersEquity', 
                    'Liabilities', 'LiabilitiesCurrent', 'Goodwill',
                    'CashAndCashEquivalentsAtCarryingValue', 'AccountsPayableCurrent',
                    'RetainedEarningsAccumulatedDeficit',
                    -- Cash Flow
                    'NetCashProvidedByUsedInOperatingActivities',
                    'NetCashProvidedByUsedInInvestingActivities', 
                    'NetCashProvidedByUsedInFinancingActivities',
                    'DepreciationDepletionAndAmortization', 'ShareBasedCompensation'
                )
                AND sra.VALUE IS NOT NULL
        """).collect()
        
        # Get count of loaded records
        sec_count = session.sql(f"SELECT COUNT(*) as cnt FROM {config.DATABASE['name']}.CURATED.FACT_SEC_FILINGS").collect()[0]['CNT']
        # print(f" Loaded {sec_count:,} SEC filing records from real data")
        
    except Exception as e:
        print(f"WARNING:  SEC filing data not available: {e}")
        # print(" Falling back to synthetic fundamentals generation...")
        
        # Call the existing fundamentals function as fallback
        build_fundamentals_and_estimates(session)
    
    # print(" SEC filings and fundamentals data ready")

def build_esg_scores(session: Session):
    """Build ESG scores with SecurityID linkage using efficient SQL generation."""
    
    session.sql(f"""
        -- Generate synthetic ESG scores with sector-specific characteristics and regional variations
        -- Creates Environmental, Social, Governance scores (0-100) with realistic distributions
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_ESG_SCORES AS
        WITH equity_securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.SIC_DESCRIPTION,
                i.CountryOfIncorporation
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        scoring_dates AS (
            SELECT DATEADD(quarter, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())) as SCORE_DATE
            FROM TABLE(GENERATOR(rowcount => {4 * config.YEARS_OF_HISTORY}))
        ),
        base_scores AS (
            SELECT 
                es.SecurityID,
                sd.SCORE_DATE,
                -- Environmental score (sector-specific)
                CASE 
                    WHEN es.SIC_DESCRIPTION = 'Utilities' THEN UNIFORM(20, 60, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Energy' THEN UNIFORM(15, 50, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(60, 95, RANDOM())
                    ELSE UNIFORM(40, 80, RANDOM())
                END as E_SCORE,
                -- Social score (region-specific bias)
                CASE 
                    WHEN es.CountryOfIncorporation IN ('US', 'CA') THEN UNIFORM(50, 85, RANDOM())
                    WHEN es.CountryOfIncorporation IN ('DE', 'FR', 'SE', 'DK') THEN UNIFORM(60, 90, RANDOM())
                    ELSE UNIFORM(45, 75, RANDOM())
                END as S_SCORE,
                -- Governance score (generally high for developed markets)
                CASE 
                    WHEN es.CountryOfIncorporation IN ('US', 'CA', 'GB', 'DE', 'FR', 'SE', 'DK') THEN UNIFORM(65, 95, RANDOM())
                    ELSE UNIFORM(40, 70, RANDOM())
                END as G_SCORE
            FROM equity_securities es
            CROSS JOIN scoring_dates sd
        )
        SELECT 
            SecurityID,
            SCORE_DATE,
            'Environmental' as SCORE_TYPE,
            E_SCORE as SCORE_VALUE,
            CASE 
                WHEN E_SCORE >= 80 THEN 'A'
                WHEN E_SCORE >= 60 THEN 'B' 
                WHEN E_SCORE >= 40 THEN 'C'
                ELSE 'D'
            END as SCORE_GRADE,
            'MSCI' as PROVIDER
        FROM base_scores
        UNION ALL
        SELECT SecurityID, SCORE_DATE, 'Social', S_SCORE, 
               CASE WHEN S_SCORE >= 80 THEN 'A' WHEN S_SCORE >= 60 THEN 'B' WHEN S_SCORE >= 40 THEN 'C' ELSE 'D' END,
               'MSCI' FROM base_scores
        UNION ALL  
        SELECT SecurityID, SCORE_DATE, 'Governance', G_SCORE,
               CASE WHEN G_SCORE >= 80 THEN 'A' WHEN G_SCORE >= 60 THEN 'B' WHEN G_SCORE >= 40 THEN 'C' ELSE 'D' END,
               'MSCI' FROM base_scores
        UNION ALL
        SELECT SecurityID, SCORE_DATE, 'Overall ESG', (E_SCORE + S_SCORE + G_SCORE) / 3,
               CASE WHEN (E_SCORE + S_SCORE + G_SCORE) / 3 >= 80 THEN 'A' 
                    WHEN (E_SCORE + S_SCORE + G_SCORE) / 3 >= 60 THEN 'B' 
                    WHEN (E_SCORE + S_SCORE + G_SCORE) / 3 >= 40 THEN 'C' 
                    ELSE 'D' END,
               'MSCI' FROM base_scores
    """).collect()
    
    # print(" Created ESG scores with sector and regional differentiation")

def build_factor_exposures(session: Session):
    """Build factor exposures with SecurityID linkage using efficient SQL generation."""
    
    session.sql(f"""
        -- Generate synthetic factor exposures (Value, Growth, Quality, etc.) for equity securities
        -- Creates factor loadings with sector-specific characteristics and realistic correlations
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_FACTOR_EXPOSURES AS
        WITH equity_securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.SIC_DESCRIPTION,
                i.CountryOfIncorporation
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        monthly_dates AS (
            SELECT DATEADD(month, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())) as EXPOSURE_DATE
            FROM TABLE(GENERATOR(rowcount => {12 * config.YEARS_OF_HISTORY}))
        ),
        base_exposures AS (
            SELECT 
                es.SecurityID,
                md.EXPOSURE_DATE,
                -- Market beta (sector-specific)
                CASE 
                    WHEN es.SIC_DESCRIPTION = 'Utilities' THEN UNIFORM(0.4, 0.8, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(0.9, 1.4, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Health Care' THEN UNIFORM(0.6, 1.1, RANDOM())
                    ELSE UNIFORM(0.7, 1.2, RANDOM())
                END as MARKET_BETA,
                -- Size factor (small vs large cap)
                UNIFORM(-0.5, 0.8, RANDOM()) as SIZE_FACTOR,
                -- Value factor (sector-specific)
                CASE 
                    WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(-0.3, 0.2, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Energy' THEN UNIFORM(0.1, 0.6, RANDOM())
                    ELSE UNIFORM(-0.2, 0.4, RANDOM())
                END as VALUE_FACTOR,
                -- Momentum factor
                UNIFORM(-0.4, 0.4, RANDOM()) as MOMENTUM_FACTOR,
                -- Growth factor (inverse of value factor for most tech stocks)
                CASE 
                    WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(0.3, 0.8, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Health Care' THEN UNIFORM(0.1, 0.6, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Energy' THEN UNIFORM(-0.4, 0.1, RANDOM())
                    ELSE UNIFORM(-0.3, 0.4, RANDOM())
                END as GROWTH_FACTOR,
                -- Quality factor
                CASE 
                    WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(0.2, 0.7, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Health Care' THEN UNIFORM(0.1, 0.5, RANDOM())
                    ELSE UNIFORM(-0.2, 0.3, RANDOM())
                END as QUALITY_FACTOR,
                -- Volatility factor
                CASE 
                    WHEN es.SIC_DESCRIPTION = 'Utilities' THEN UNIFORM(-0.3, 0.1, RANDOM())
                    WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(-0.1, 0.4, RANDOM())
                    ELSE UNIFORM(-0.2, 0.2, RANDOM())
                END as VOLATILITY_FACTOR
            FROM equity_securities es
            CROSS JOIN monthly_dates md
        )
        SELECT SecurityID, EXPOSURE_DATE, 'Market' as FACTOR_NAME, MARKET_BETA as EXPOSURE_VALUE, 0.95 as R_SQUARED FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Size', SIZE_FACTOR, 0.75 FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Value', VALUE_FACTOR, 0.65 FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Growth', GROWTH_FACTOR, 0.60 FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Momentum', MOMENTUM_FACTOR, 0.45 FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Quality', QUALITY_FACTOR, 0.55 FROM base_exposures
        UNION ALL
        SELECT SecurityID, EXPOSURE_DATE, 'Volatility', VOLATILITY_FACTOR, 0.35 FROM base_exposures
    """).collect()
    
    # print(" Created factor exposures with sector-specific characteristics")

def build_benchmark_holdings(session: Session):
    """Build benchmark holdings with SecurityID linkage using efficient SQL generation."""
    
    session.sql(f"""
        -- Generate synthetic benchmark holdings for major indices (S&P 500, MSCI ACWI, Nasdaq 100)
        -- Creates realistic index compositions with market-cap weighted allocations
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_BENCHMARK_HOLDINGS AS
        WITH equity_securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.SIC_DESCRIPTION,
                i.CountryOfIncorporation
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        benchmarks AS (
            SELECT BenchmarkID, BenchmarkName FROM {config.DATABASE['name']}.CURATED.DIM_BENCHMARK
        ),
        monthly_dates AS (
            SELECT LAST_DAY(DATEADD(month, seq4(), DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE()))) as HOLDING_DATE
            FROM TABLE(GENERATOR(rowcount => {12 * config.YEARS_OF_HISTORY}))
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
                -- Weight logic based on benchmark type
                CASE 
                    WHEN b.BenchmarkName = 'S&P 500' AND es.CountryOfIncorporation = 'US' THEN UNIFORM(0.001, 0.07, RANDOM())
                    WHEN b.BenchmarkName = 'MSCI ACWI' THEN 
                        CASE 
                            WHEN es.CountryOfIncorporation = 'US' THEN UNIFORM(0.001, 0.05, RANDOM())
                            ELSE UNIFORM(0.0001, 0.01, RANDOM())
                        END
                    WHEN b.BenchmarkName = 'Nasdaq 100' AND es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(0.005, 0.12, RANDOM())
                    ELSE NULL
                END as RAW_WEIGHT,
                ROW_NUMBER() OVER (PARTITION BY b.BenchmarkID, md.HOLDING_DATE ORDER BY RANDOM()) as rn
            FROM benchmarks b
            CROSS JOIN equity_securities es
            CROSS JOIN monthly_dates md
        ),
        filtered_holdings AS (
            SELECT *
            FROM benchmark_universe
            WHERE RAW_WEIGHT IS NOT NULL
            AND (
                (BenchmarkName = 'S&P 500' AND rn <= 500) OR
                (BenchmarkName = 'MSCI ACWI' AND rn <= 800) OR
                (BenchmarkName = 'Nasdaq 100' AND rn <= 100)
            )
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
            WEIGHT * 1000000000 as MARKET_VALUE_USD  -- Assume $1B benchmark size
        FROM normalized_weights
        WHERE WEIGHT >= 0.0001  -- Minimum 0.01% weight
    """).collect()
    
    # print(" Created benchmark holdings with realistic index compositions")

def build_transaction_cost_data(session: Session):
    """Build transaction cost and market microstructure data for realistic execution planning."""
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_TRANSACTION_COSTS AS
        WITH equity_securities AS (
            SELECT 
                s.SecurityID,
                s.Ticker,
                i.SIC_DESCRIPTION,
                i.CountryOfIncorporation
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        business_dates AS (
            SELECT DATEADD(day, seq4(), DATEADD(month, -3, CURRENT_DATE())) as COST_DATE
            FROM TABLE(GENERATOR(rowcount => 66))  -- ~3 months of business days
            WHERE DAYOFWEEK(COST_DATE) BETWEEN 2 AND 6
        )
        SELECT 
            es.SecurityID,
            bd.COST_DATE,
            -- Bid-ask spread (bps) - varies by market cap and sector
            CASE 
                WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(3, 8, RANDOM())
                WHEN es.SIC_DESCRIPTION = 'Utilities' THEN UNIFORM(5, 12, RANDOM())
                WHEN es.SIC_DESCRIPTION = 'Energy' THEN UNIFORM(4, 10, RANDOM())
                ELSE UNIFORM(4, 9, RANDOM())
            END as BID_ASK_SPREAD_BPS,
            -- Average daily volume (shares in millions)
            CASE 
                WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(2.0, 15.0, RANDOM())
                ELSE UNIFORM(0.5, 8.0, RANDOM())
            END as AVG_DAILY_VOLUME_M,
            -- Market impact per $1M traded (bps)
            CASE 
                WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(2, 6, RANDOM())
                ELSE UNIFORM(3, 8, RANDOM())
            END as MARKET_IMPACT_BPS_PER_1M,
            -- Commission rate (bps)
            UNIFORM(1, 3, RANDOM()) as COMMISSION_BPS,
            -- Settlement period (days)
            CASE 
                WHEN es.CountryOfIncorporation = 'US' THEN 2
                WHEN es.CountryOfIncorporation IN ('GB', 'DE', 'FR') THEN 2
                ELSE 3
            END as SETTLEMENT_DAYS
        FROM equity_securities es
        CROSS JOIN business_dates bd
    """).collect()
    
    # print(" Created transaction cost and market microstructure data")

def build_liquidity_data(session: Session):
    """Build liquidity and cash flow data for portfolio implementation planning."""
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_PORTFOLIO_LIQUIDITY AS
        WITH portfolios AS (
            SELECT PortfolioID, PortfolioName FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
        ),
        monthly_dates AS (
            SELECT DATEADD(month, seq4(), DATEADD(month, -12, CURRENT_DATE())) as LIQUIDITY_DATE
            FROM TABLE(GENERATOR(rowcount => 12))
        )
        SELECT 
            p.PortfolioID,
            md.LIQUIDITY_DATE,
            -- Available cash position
            UNIFORM(1000000, 25000000, RANDOM()) as CASH_POSITION_USD,
            -- Expected cash flows (subscriptions - redemptions)
            UNIFORM(-5000000, 10000000, RANDOM()) as NET_CASHFLOW_30D_USD,
            -- Liquidity score (1-10, 10 = most liquid)
            CASE 
                WHEN p.PortfolioName LIKE '%Technology%' THEN UNIFORM(7, 9, RANDOM())
                WHEN p.PortfolioName LIKE '%ESG%' THEN UNIFORM(6, 8, RANDOM())
                ELSE UNIFORM(5, 8, RANDOM())
            END as PORTFOLIO_LIQUIDITY_SCORE,
            -- Rebalancing frequency (days)
            CASE 
                WHEN p.PortfolioName LIKE '%Multi-Asset%' THEN 30
                WHEN p.PortfolioName LIKE '%Balanced%' THEN 60
                ELSE 90
            END as REBALANCING_FREQUENCY_DAYS
        FROM portfolios p
        CROSS JOIN monthly_dates md
    """).collect()
    
    # print(" Created portfolio liquidity and cash flow data")

def build_risk_budget_data(session: Session):
    """Build risk budget and limits data for professional risk management."""
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_RISK_LIMITS AS
        WITH portfolios AS (
            SELECT PortfolioID, PortfolioName, Strategy FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
        )
        SELECT 
            p.PortfolioID,
            CURRENT_DATE() as LIMITS_DATE,
            -- Tracking error limits
            CASE 
                WHEN p.Strategy = 'Active Equity' THEN UNIFORM(4.0, 6.0, RANDOM())
                WHEN p.Strategy = 'Multi-Asset' THEN UNIFORM(3.0, 5.0, RANDOM())
                ELSE UNIFORM(2.0, 4.0, RANDOM())
            END as TRACKING_ERROR_LIMIT_PCT,
            -- Current tracking error utilization
            UNIFORM(2.5, 4.8, RANDOM()) as CURRENT_TRACKING_ERROR_PCT,
            -- Maximum single position concentration
            CASE 
                WHEN p.PortfolioName LIKE '%Technology%' THEN {config.COMPLIANCE_RULES['concentration']['tech_portfolio_max']}
                ELSE {config.COMPLIANCE_RULES['concentration']['max_single_issuer']}
            END as MAX_SINGLE_POSITION_PCT,
            -- Maximum sector concentration
            CASE 
                WHEN p.PortfolioName LIKE '%Technology%' THEN 0.50  -- 50%
                WHEN p.PortfolioName LIKE '%Multi-Asset%' THEN 0.35  -- 35%
                ELSE 0.40  -- 40%
            END as MAX_SECTOR_CONCENTRATION_PCT,
            -- Risk budget utilization
            UNIFORM(65, 85, RANDOM()) as RISK_BUDGET_UTILIZATION_PCT,
            -- VaR limits
            UNIFORM(1.5, 3.0, RANDOM()) as VAR_LIMIT_1DAY_PCT
        FROM portfolios p
    """).collect()
    
    # print(" Created risk budget and limits data")

def build_trading_calendar_data(session: Session):
    """Build trading calendar with blackout periods and market events."""
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_TRADING_CALENDAR AS
        WITH securities AS (
            SELECT s.SecurityID, s.Ticker 
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            WHERE s.AssetClass = 'Equity'
            AND EXISTS (
                SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRANSACTION t 
                WHERE t.SecurityID = s.SecurityID
            )
        ),
        future_dates AS (
            SELECT DATEADD(day, seq4(), CURRENT_DATE()) as EVENT_DATE
            FROM TABLE(GENERATOR(rowcount => 90))  -- Next 90 days
        )
        SELECT 
            s.SecurityID,
            fd.EVENT_DATE,
            -- Earnings announcement dates (quarterly)
            CASE 
                WHEN MOD(DATEDIFF(day, CURRENT_DATE(), fd.EVENT_DATE), 90) = 0 THEN 'EARNINGS_ANNOUNCEMENT'
                WHEN MOD(DATEDIFF(day, CURRENT_DATE(), fd.EVENT_DATE), 30) = 0 THEN 'MONTHLY_REBALANCING'
                WHEN MOD(DATEDIFF(day, CURRENT_DATE(), fd.EVENT_DATE), 7) = 0 THEN 'WEEKLY_REVIEW'
                ELSE NULL
            END as EVENT_TYPE,
            -- Blackout period indicator
            CASE 
                WHEN MOD(DATEDIFF(day, CURRENT_DATE(), fd.EVENT_DATE), 90) BETWEEN -2 AND 2 THEN TRUE
                ELSE FALSE
            END as IS_BLACKOUT_PERIOD,
            -- Market volatility forecast
            UNIFORM(12, 35, RANDOM()) as EXPECTED_VIX_LEVEL,
            -- Options expiration indicator
            CASE 
                WHEN MOD(DATEDIFF(day, CURRENT_DATE(), fd.EVENT_DATE), 21) = 0 THEN TRUE
                ELSE FALSE
            END as IS_OPTIONS_EXPIRATION
        FROM securities s
        CROSS JOIN future_dates fd
        WHERE fd.EVENT_DATE IS NOT NULL
    """).collect()
    
    # print(" Created trading calendar with blackout periods and events")

def build_client_mandate_data(session: Session):
    """Build client mandate and approval requirements data."""
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.DIM_CLIENT_MANDATES AS
        WITH portfolios AS (
            SELECT PortfolioID, PortfolioName, Strategy FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
        )
        SELECT 
            p.PortfolioID,
            -- Approval thresholds
            CASE 
                WHEN p.PortfolioName LIKE '%Flagship%' THEN 0.03  -- 3% for flagship
                WHEN p.PortfolioName LIKE '%ESG%' THEN 0.04  -- 4% for ESG
                ELSE 0.05  -- 5% for others
            END as POSITION_CHANGE_APPROVAL_THRESHOLD_PCT,
            -- Sector allocation ranges
            CASE 
                WHEN p.PortfolioName LIKE '%Technology%' THEN '{{"Technology": [0.30, 0.50], "Healthcare": [0.05, 0.15]}}'
                WHEN p.PortfolioName LIKE '%ESG%' THEN '{{"Technology": [0.15, 0.35], "Energy": [0.00, 0.05]}}'
                ELSE '{{"Technology": [0.10, 0.40], "Healthcare": [0.05, 0.20]}}'
            END as SECTOR_ALLOCATION_RANGES_JSON,
            -- ESG requirements
            CASE 
                WHEN p.PortfolioName LIKE '%ESG%' THEN 'BBB'
                WHEN p.PortfolioName LIKE '%Climate%' THEN 'BB'
                ELSE NULL
            END as MIN_ESG_RATING,
            -- Exclusion lists
            CASE 
                WHEN p.PortfolioName LIKE '%ESG%' THEN '["Tobacco", "Weapons", "Thermal Coal"]'
                WHEN p.PortfolioName LIKE '%Climate%' THEN '["Fossil Fuels", "Thermal Coal"]'
                ELSE '[]'
            END as EXCLUSION_SECTORS_JSON,
            -- Rebalancing requirements
            CASE 
                WHEN p.Strategy = 'Multi-Asset' THEN 30
                WHEN p.Strategy = 'Active Equity' THEN 90
                ELSE 60
            END as MAX_REBALANCING_FREQUENCY_DAYS
        FROM portfolios p
    """).collect()
    
    # print(" Created client mandate and approval requirements data")

def build_tax_implications_data(session: Session):
    """Build tax implications and cost basis data for tax-efficient execution."""
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {config.DATABASE['name']}.CURATED.FACT_TAX_IMPLICATIONS AS
        WITH portfolio_holdings AS (
            SELECT DISTINCT 
                h.PortfolioID,
                h.SecurityID,
                h.MarketValue_Base,
                h.PortfolioWeight
            FROM {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR h
            WHERE h.HoldingDate = (SELECT MAX(HoldingDate) FROM {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR)
        )
        SELECT 
            ph.PortfolioID,
            ph.SecurityID,
            CURRENT_DATE() as TAX_DATE,
            -- Cost basis (synthetic - based on current market value with gain/loss)
            ph.MarketValue_Base * UNIFORM(0.70, 1.30, RANDOM()) as COST_BASIS_USD,
            -- Unrealized gain/loss
            ph.MarketValue_Base - (ph.MarketValue_Base * UNIFORM(0.70, 1.30, RANDOM())) as UNREALIZED_GAIN_LOSS_USD,
            -- Holding period (days)
            UNIFORM(30, 1095, RANDOM()) as HOLDING_PERIOD_DAYS,
            -- Tax treatment
            CASE 
                WHEN UNIFORM(30, 1095, RANDOM()) > 365 THEN 'LONG_TERM'
                ELSE 'SHORT_TERM'
            END as TAX_TREATMENT,
            -- Tax loss harvesting opportunity
            CASE 
                WHEN ph.MarketValue_Base - (ph.MarketValue_Base * UNIFORM(0.70, 1.30, RANDOM())) < -10000 THEN TRUE
                ELSE FALSE
            END as TAX_LOSS_HARVEST_OPPORTUNITY,
            -- Capital gains tax rate
            CASE 
                WHEN UNIFORM(30, 1095, RANDOM()) > 365 THEN 0.20  -- Long-term rate
                ELSE 0.37  -- Short-term rate
            END as TAX_RATE
        FROM portfolio_holdings ph
    """).collect()
    
    # print(" Created tax implications and cost basis data")

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
    
    # print(" Created FACT_COMPLIANCE_ALERTS table")

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
    
    # print(" Created FACT_PRE_SCREENED_REPLACEMENTS table")

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
        print(f"WARNING:  Portfolio '{portfolio_name}' not found - skipping demo alert")
        return
    
    portfolio_id = portfolio_id_result[0]['PORTFOLIOID']
    
    # Get the security ID for META
    security_id_result = session.sql(f"""
        SELECT SecurityID 
        FROM {database_name}.CURATED.DIM_SECURITY 
        WHERE FIGI = '{non_compliant['openfigi_id']}'
        OR Ticker = '{non_compliant['ticker']}'
        LIMIT 1
    """).collect()
    
    if not security_id_result:
        print(f"WARNING:  Security {non_compliant['ticker']} not found - skipping demo alert")
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
    
    # print(f" Generated demo compliance alert: {non_compliant['ticker']} ESG downgrade from {non_compliant['original_esg_grade']} to {non_compliant['downgraded_esg_grade']}")

def generate_demo_pre_screened_replacements(session: Session):
    """
    Generate pre-screened replacement candidates for the demo scenario.
    Uses configuration from config.SCENARIO_3_2_MANDATE_COMPLIANCE.
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
        print(f"WARNING:  Portfolio '{portfolio_name}' not found - skipping pre-screened replacements")
        return
    
    portfolio_id = portfolio_id_result[0]['PORTFOLIOID']
    
    # Insert each pre-screened replacement
    from datetime import datetime
    screen_date = datetime.now().date()
    
    for replacement in scenario_config['pre_screened_replacements']:
        # Get the security ID
        security_id_result = session.sql(f"""
            SELECT SecurityID 
            FROM {database_name}.CURATED.DIM_SECURITY 
            WHERE FIGI = '{replacement['openfigi_id']}'
            OR Ticker = '{replacement['ticker']}'
            LIMIT 1
        """).collect()
        
        if not security_id_result:
            print(f"WARNING:  Security {replacement['ticker']} not found - skipping")
            continue
        
        security_id = security_id_result[0]['SECURITYID']
        
        # Insert the pre-screened replacement
        session.sql(f"""
            INSERT INTO {database_name}.CURATED.FACT_PRE_SCREENED_REPLACEMENTS (
                PortfolioID, SecurityID, ScreenDate, IsEligible, ReplacementRank,
                ESG_Grade, AI_Growth_Score, MarketCap_B_USD, LiquidityScore,
                EligibilityReason, ScreeningCriteria
            )
            VALUES (
                {portfolio_id},
                {security_id},
                '{screen_date}',
                TRUE,
                {replacement['rank']},
                '{replacement['esg_grade']}',
                {replacement['ai_growth_score']},
                {replacement['market_cap_b']},
                {replacement['liquidity_score']},
                '{replacement['rationale']}',
                'AI Growth Score >= {scenario_config['mandate_requirements']['ai_growth_threshold']}, ESG Grade >= {scenario_config['mandate_requirements']['min_esg_grade']}, Market Cap >= ${scenario_config['mandate_requirements']['min_market_cap_b']}B, Liquidity Score >= {scenario_config['mandate_requirements']['min_liquidity_score']}'
            )
        """).collect()
        
        # print(f" Added pre-screened replacement: {replacement['ticker']} (Rank {replacement['rank']}, AI Score: {replacement['ai_growth_score']})")

# Report template functions removed - now handled by unstructured data hydration engine
# Templates are in content_library/global/report_templates/ following @unstructured-data-generation.mdc patterns

# =============================================================================
# MIDDLE OFFICE TABLES
# =============================================================================

def build_dim_counterparty(session: Session):
    """Build counterparty dimension with settlement characteristics."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Define realistic counterparties with settlement profiles
    counterparties = [
        ('Goldman Sachs', 'Broker', 0.02, 1.8, 'A'),
        ('Morgan Stanley', 'Broker', 0.015, 1.9, 'A'),
        ('JP Morgan', 'Broker', 0.01, 1.7, 'AA'),
        ('Barclays', 'Broker', 0.025, 2.1, 'A'),
        ('Credit Suisse', 'Broker', 0.03, 2.3, 'BBB'),
        ('Deutsche Bank', 'Broker', 0.028, 2.2, 'BBB'),
        ('BNP Paribas', 'Broker', 0.018, 1.9, 'A'),
        ('UBS', 'Broker', 0.012, 1.8, 'AA'),
        ('Citi', 'Broker', 0.015, 1.9, 'A'),
        ('Bank of America', 'Broker', 0.013, 1.8, 'A'),
        ('BNY Mellon', 'Custodian', 0.005, 1.5, 'AA'),
        ('State Street', 'Custodian', 0.005, 1.5, 'AA'),
        ('JPM Custody', 'Custodian', 0.004, 1.5, 'AA'),
        ('Northern Trust', 'Custodian', 0.006, 1.6, 'AA'),
        ('HSBC Custody', 'Custodian', 0.007, 1.7, 'A'),
        ('Prime Broker A', 'Prime', 0.02, 1.9, 'A'),
        ('Prime Broker B', 'Prime', 0.022, 2.0, 'A'),
        ('Clearing Firm A', 'Broker', 0.015, 1.8, 'A'),
        ('Clearing Firm B', 'Broker', 0.017, 1.9, 'A'),
        ('Market Maker A', 'Broker', 0.02, 2.0, 'BBB')
    ]
    
    # Create table
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.DIM_COUNTERPARTY (
            CounterpartyID BIGINT IDENTITY(1,1) PRIMARY KEY,
            CounterpartyName VARCHAR(255) NOT NULL,
            CounterpartyType VARCHAR(50),
            HistoricalFailRate DECIMAL(5,4),
            AverageSettlementTime DECIMAL(5,2),
            RiskRating VARCHAR(10)
        )
    """).collect()
    
    # Insert counterparties
    for name, ctype, fail_rate, avg_time, rating in counterparties:
        session.sql(f"""
            INSERT INTO {database_name}.CURATED.DIM_COUNTERPARTY 
            (CounterpartyName, CounterpartyType, HistoricalFailRate, AverageSettlementTime, RiskRating)
            VALUES ('{name}', '{ctype}', {fail_rate}, {avg_time}, '{rating}')
        """).collect()


def build_dim_custodian(session: Session):
    """Build custodian dimension."""
    database_name = config.DATABASE['name']
    
    # Define major custodians
    custodians = [
        ('BNY Mellon', 'Global Custodian', 'Americas, EMEA, APAC', 'Premium'),
        ('State Street', 'Global Custodian', 'Americas, EMEA, APAC', 'Premium'),
        ('JPMorgan Custody', 'Global Custodian', 'Americas, EMEA, APAC', 'Premium'),
        ('Northern Trust', 'Regional Custodian', 'Americas, EMEA', 'Standard'),
        ('HSBC Custody', 'Global Custodian', 'EMEA, APAC', 'Standard'),
        ('Citi Custody', 'Global Custodian', 'Americas, EMEA, APAC', 'Premium'),
        ('Deutsche Bank Custody', 'Regional Custodian', 'EMEA', 'Standard'),
        ('BNP Paribas Securities Services', 'Regional Custodian', 'EMEA', 'Standard')
    ]
    
    # Create table
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.DIM_CUSTODIAN (
            CustodianID BIGINT IDENTITY(1,1) PRIMARY KEY,
            CustodianName VARCHAR(255) NOT NULL,
            CustodianType VARCHAR(100),
            CoverageRegions VARCHAR(255),
            ServiceLevel VARCHAR(50)
        )
    """).collect()
    
    # Insert custodians
    for name, ctype, regions, service in custodians:
        session.sql(f"""
            INSERT INTO {database_name}.CURATED.DIM_CUSTODIAN 
            (CustodianName, CustodianType, CoverageRegions, ServiceLevel)
            VALUES ('{name}', '{ctype}', '{regions}', '{service}')
        """).collect()


def build_fact_trade_settlement(session: Session, test_mode: bool = False):
    """Build trade settlement fact table with status tracking."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.CURATED.FACT_TRADE_SETTLEMENT AS
        WITH trade_data AS (
            SELECT 
                t.TransactionID,
                t.TransactionDate,
                DATEADD(day, 2, t.TransactionDate) as SettlementDate,
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
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY TransactionID) as SettlementID,
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
    """).collect()


def build_fact_reconciliation(session: Session, test_mode: bool = False):
    """Build reconciliation fact table tracking breaks and resolutions."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
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
        breaks AS (
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
                break_chance
            FROM position_data
            WHERE break_chance <= 2
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
            CASE 
                WHEN break_chance <= 0.5 THEN 'Open'
                WHEN break_chance <= 1.5 THEN 'Investigating'
                ELSE 'Resolved'
            END as Status,
            CASE 
                WHEN break_chance > 0.5 THEN DATEADD(day, UNIFORM(1, 5, RANDOM()), ReconciliationDate)
                ELSE NULL
            END as ResolutionDate,
            CASE 
                WHEN break_chance > 1.5 THEN 'Timing difference - resolved through custodian confirmation'
                WHEN break_chance > 0.5 THEN 'Under investigation - awaiting custodian response'
                ELSE NULL
            END as ResolutionNotes
        FROM breaks
    """).collect()


def build_fact_nav_calculation(session: Session, test_mode: bool = False):
    """Build NAV calculation fact table."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
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
        nav_calc AS (
            SELECT 
                HoldingDate as CalculationDate,
                PortfolioID,
                TotalAssets,
                TotalAssets * 0.001 as TotalLiabilities,  -- 0.1% liabilities
                TotalAssets * 0.999 as NetAssets,
                100000000.00 as SharesOutstanding,  -- Fixed 100M shares
                (TotalAssets * 0.999) / 100000000.00 as NAVperShare,
                UNIFORM(0, 100, RANDOM()) as anomaly_chance
            FROM daily_positions
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
            CASE 
                WHEN anomaly_chance <= 1 THEN 'Pending Review'
                ELSE 'Calculated'
            END as CalculationStatus,
            CASE 
                WHEN anomaly_chance <= 0.5 THEN 'NAV change >2% from prior day'
                WHEN anomaly_chance <= 1 THEN 'Missing prices detected'
                ELSE NULL
            END as AnomaliesDetected,
            CASE 
                WHEN anomaly_chance <= 1 THEN 'Pending'
                ELSE 'Approved'
            END as ApprovalStatus,
            CASE 
                WHEN anomaly_chance > 1 THEN 'Operations Manager'
                ELSE NULL
            END as ApprovedBy,
            CASE 
                WHEN anomaly_chance > 1 THEN DATEADD(hour, 2, CalculationDate)
                ELSE NULL
            END as ApprovalTimestamp
        FROM nav_calc
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
    """Build corporate actions fact table."""
    database_name = config.DATABASE['name']
    random.seed(config.RNG_SEED)
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
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
            WHERE MOD(day_num, 90) = 0  -- Quarterly events
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY AnnouncementDate, SecurityID) as ActionID,
            SecurityID,
            IssuerID,
            CASE 
                WHEN action_type_flag < 2.7 THEN 'Dividend'
                WHEN action_type_flag < 2.9 THEN 'Split'
                ELSE 'Merger'
            END as ActionType,
            AnnouncementDate,
            DATEADD(day, 15, AnnouncementDate) as ExDate,
            DATEADD(day, 16, AnnouncementDate) as RecordDate,
            DATEADD(day, 30, AnnouncementDate) as PaymentDate,
            CASE 
                WHEN action_type_flag < 2.7 THEN 'Quarterly dividend: $' || ROUND(UNIFORM(0.50, 2.00, RANDOM()), 2) || ' per share'
                WHEN action_type_flag < 2.9 THEN '2-for-1 stock split'
                ELSE 'Acquisition announcement'
            END as ActionDetails,
            CASE 
                WHEN action_type_flag < 2.7 THEN UNIFORM(0.50, 2.00, RANDOM())
                WHEN action_type_flag < 2.9 THEN 2.0
                ELSE 0.0
            END as ImpactValue,
            CASE 
                WHEN action_type_flag < 2.7 THEN 'Processed'
                WHEN action_type_flag < 2.9 THEN 'Pending'
                ELSE 'Announced'
            END as ProcessingStatus,
            UNIFORM(1, 10, RANDOM()) as PortfoliosAffected
        FROM action_dates
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
    """Build daily cash position snapshots."""
    database_name = config.DATABASE['name']
    
    # Create table using CREATE TABLE AS SELECT pattern (no foreign keys)
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
        cumulative_cash AS (
            SELECT 
                MovementDate as PositionDate,
                PortfolioID,
                CustodianID,
                Currency,
                LAG(Inflows - Outflows, 1, 10000000) OVER (PARTITION BY PortfolioID ORDER BY MovementDate) as OpeningBalance,
                Inflows,
                Outflows,
                0 as FXGainLoss,
                Inflows - Outflows as NetChange
            FROM daily_flows
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
            'Reconciled' as ReconciliationStatus
        FROM cumulative_cash
    """).collect()


def build_scenario_data(session: Session, scenario: str):
    """Build scenario-specific data."""
    
    if scenario == 'mandate_compliance' or scenario == 'portfolio_copilot':
        pass
        # print(f" Building Scenario 3.2: Mandate Compliance data...")
        
        # Create tables
        build_fact_compliance_alerts(session)
        build_fact_pre_screened_replacements(session)
        
        # Generate demo data
        generate_demo_compliance_alert(session)
        generate_demo_pre_screened_replacements(session)
        
        # Note: Report templates are generated via unstructured data hydration engine
        # They will be processed through generate_unstructured.py following the
        # template-based generation pattern defined in @unstructured-data-generation.mdc
        
        # print(" Scenario 3.2: Mandate Compliance data complete")
        # print("   Note: Report templates will be generated via unstructured data pipeline")
    else:
        pass
        # print(f"⏭️  Scenario data for {scenario} - not implemented yet")

def validate_data_quality(session: Session):
    """Validate data quality of the new model."""
    
    # print("🔍 Running data quality checks...")
    
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
        print(f"WARNING:  Portfolio weight deviations found: {len(weight_check)} portfolios")
    else:
        pass
        # print(" Portfolio weights sum to 100%")
    
    # Check security identifier integrity (simplified - check direct columns)
    security_check = session.sql(f"""
        SELECT 
            COUNT(*) as total_securities,
            COUNT(CASE WHEN Ticker IS NOT NULL AND LENGTH(Ticker) > 0 THEN 1 END) as securities_with_ticker,
            COUNT(CASE WHEN FIGI IS NOT NULL AND LENGTH(FIGI) > 0 THEN 1 END) as securities_with_figi
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY
    """).collect()
    
    if security_check:
        result = security_check[0]
        total = result['TOTAL_SECURITIES']
        with_ticker = result['SECURITIES_WITH_TICKER']
        with_figi = result['SECURITIES_WITH_FIGI']
        
        # print(f" Security identifier validation: {total} securities total")
        # print(f" Identifier coverage: {with_ticker} with TICKER ({with_ticker/total*100:.1f}%), {with_figi} with FIGI ({with_figi/total*100:.1f}%)")
        
        if with_ticker < total:
            print(f"WARNING:  {total - with_ticker} securities missing TICKER")
        if with_figi < total:
            print(f"WARNING:  {total - with_figi} securities missing FIGI")
    
    # print(" Data quality validation complete")
