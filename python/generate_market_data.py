#!/usr/bin/env python3
"""
Snowcrest Asset Management (SAM) Demo - Market Data Generation

This module generates synthetic financial data for the MARKET_DATA schema,
simulating data as received from a market data provider. Includes:
- Company and security master data
- Financial statements (income statement, balance sheet, cash flow)
- Analyst estimates and consensus data
- Price targets and ratings

Usage:
    Called by main.py as part of the build process when MARKET_DATA is enabled.
"""

from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit, when, concat, uniform, dateadd, current_timestamp
from snowflake.snowpark.types import StructType, StructField, StringType, IntegerType, FloatType, DateType, TimestampType
from datetime import datetime, timedelta
from typing import List, Optional
import random

import config


def build_all(session: Session, test_mode: bool = False):
    """Build all MARKET_DATA schema tables."""
    
    if not config.MARKET_DATA.get('enabled', True):
        print("⏭️  MARKET_DATA schema disabled in config, skipping...")
        return
    
    print("\n" + "=" * 60)
    print("Building MARKET_DATA Schema (External Provider Data)")
    print("=" * 60)
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    # Create schema if not exists
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {database_name}.{schema_name}").collect()
    print(f"✅ Schema: {database_name}.{schema_name}")
    
    # Build tables in dependency order
    build_reference_tables(session, test_mode)
    build_company_master(session, test_mode)
    build_financial_periods(session, test_mode)
    build_financial_data(session, test_mode)
    build_broker_analyst_data(session, test_mode)
    build_estimate_data(session, test_mode)
    
    # Build filing tables (S&P Capital IQ pattern)
    build_filing_reference_tables(session, test_mode)
    build_filing_data(session, test_mode)
    
    print("\n✅ MARKET_DATA schema build complete")


def build_reference_tables(session: Session, test_mode: bool = False):
    """Build reference/lookup tables."""
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    # REF_DATA_ITEM - Financial data item definitions
    print("  Building REF_DATA_ITEM...")
    
    data_items = []
    for key, item in config.FINANCIAL_DATA_ITEMS.items():
        data_items.append({
            'DATA_ITEM_ID': item['id'],
            'DATA_ITEM_CODE': key.upper(),
            'DATA_ITEM_NAME': item['name'],
            'CATEGORY': item['category'],
            'UNIT_TYPE': item['unit']
        })
    
    for key, item in config.ESTIMATE_DATA_ITEMS.items():
        data_items.append({
            'DATA_ITEM_ID': item['id'],
            'DATA_ITEM_CODE': key.upper(),
            'DATA_ITEM_NAME': item['name'],
            'CATEGORY': item['category'],
            'UNIT_TYPE': item['unit']
        })
    
    df = session.create_dataframe(data_items)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_DATA_ITEM")
    print(f"    ✅ REF_DATA_ITEM: {len(data_items)} items")
    
    # REF_EXCHANGE - Exchange reference
    print("  Building REF_EXCHANGE...")
    exchanges = [
        {'EXCHANGE_ID': 1, 'EXCHANGE_CODE': 'NYSE', 'EXCHANGE_NAME': 'New York Stock Exchange', 'COUNTRY': 'US'},
        {'EXCHANGE_ID': 2, 'EXCHANGE_CODE': 'NASDAQ', 'EXCHANGE_NAME': 'NASDAQ Stock Market', 'COUNTRY': 'US'},
        {'EXCHANGE_ID': 3, 'EXCHANGE_CODE': 'LSE', 'EXCHANGE_NAME': 'London Stock Exchange', 'COUNTRY': 'GB'},
        {'EXCHANGE_ID': 4, 'EXCHANGE_CODE': 'TSE', 'EXCHANGE_NAME': 'Tokyo Stock Exchange', 'COUNTRY': 'JP'},
        {'EXCHANGE_ID': 5, 'EXCHANGE_CODE': 'HKEX', 'EXCHANGE_NAME': 'Hong Kong Stock Exchange', 'COUNTRY': 'HK'},
        {'EXCHANGE_ID': 6, 'EXCHANGE_CODE': 'XETRA', 'EXCHANGE_NAME': 'Deutsche Börse Xetra', 'COUNTRY': 'DE'},
        {'EXCHANGE_ID': 7, 'EXCHANGE_CODE': 'EURONEXT', 'EXCHANGE_NAME': 'Euronext', 'COUNTRY': 'EU'},
        {'EXCHANGE_ID': 8, 'EXCHANGE_CODE': 'TSX', 'EXCHANGE_NAME': 'Toronto Stock Exchange', 'COUNTRY': 'CA'}
    ]
    df = session.create_dataframe(exchanges)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_EXCHANGE")
    print(f"    ✅ REF_EXCHANGE: {len(exchanges)} exchanges")
    
    # REF_CURRENCY
    print("  Building REF_CURRENCY...")
    currencies = [
        {'CURRENCY_ID': 1, 'CURRENCY_CODE': 'USD', 'CURRENCY_NAME': 'US Dollar'},
        {'CURRENCY_ID': 2, 'CURRENCY_CODE': 'EUR', 'CURRENCY_NAME': 'Euro'},
        {'CURRENCY_ID': 3, 'CURRENCY_CODE': 'GBP', 'CURRENCY_NAME': 'British Pound'},
        {'CURRENCY_ID': 4, 'CURRENCY_CODE': 'JPY', 'CURRENCY_NAME': 'Japanese Yen'},
        {'CURRENCY_ID': 5, 'CURRENCY_CODE': 'CHF', 'CURRENCY_NAME': 'Swiss Franc'},
        {'CURRENCY_ID': 6, 'CURRENCY_CODE': 'CAD', 'CURRENCY_NAME': 'Canadian Dollar'},
        {'CURRENCY_ID': 7, 'CURRENCY_CODE': 'AUD', 'CURRENCY_NAME': 'Australian Dollar'},
        {'CURRENCY_ID': 8, 'CURRENCY_CODE': 'HKD', 'CURRENCY_NAME': 'Hong Kong Dollar'}
    ]
    df = session.create_dataframe(currencies)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_CURRENCY")
    print(f"    ✅ REF_CURRENCY: {len(currencies)} currencies")


def build_company_master(session: Session, test_mode: bool = False):
    """Build company master data from existing DIM_ISSUER."""
    
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    print("  Building DIM_COMPANY from DIM_ISSUER...")
    
    # Get company limit based on test mode
    company_limit = 100 if test_mode else 500
    
    # Create DIM_COMPANY from existing issuer data with priority for demo companies
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.DIM_COMPANY AS
        WITH prioritized_issuers AS (
            SELECT 
                i.ISSUERID,
                i.LEGALNAME,
                i.COUNTRYOFINCORPORATION,
                i.SIC_DESCRIPTION,
                i.CIK,
                CASE 
                    WHEN i.LEGALNAME ILIKE '%APPLE%' THEN 1
                    WHEN i.LEGALNAME ILIKE '%MICROSOFT%' THEN 2
                    WHEN i.LEGALNAME ILIKE '%NVIDIA%' THEN 3
                    WHEN i.LEGALNAME ILIKE '%ALPHABET%' OR i.LEGALNAME ILIKE '%GOOGLE%' THEN 4
                    WHEN i.LEGALNAME ILIKE '%AMAZON%' THEN 5
                    WHEN i.LEGALNAME ILIKE '%META%' OR i.LEGALNAME ILIKE '%FACEBOOK%' THEN 6
                    WHEN i.LEGALNAME ILIKE '%TESLA%' THEN 7
                    WHEN i.LEGALNAME ILIKE '%TAIWAN SEMICONDUCTOR%' THEN 8
                    WHEN i.LEGALNAME ILIKE '%AMD%' OR i.LEGALNAME ILIKE '%ADVANCED MICRO%' THEN 9
                    WHEN i.LEGALNAME ILIKE '%INTEL%' THEN 10
                    ELSE 100
                END as PRIORITY
            FROM {database_name}.{curated_schema}.DIM_ISSUER i
            WHERE i.LEGALNAME IS NOT NULL
              AND i.LEGALNAME != 'Unknown'
              AND i.COUNTRYOFINCORPORATION = 'US'  -- Focus on US companies for financial data
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PRIORITY, LEGALNAME) as COMPANY_ID,
            ISSUERID as PROVIDER_COMPANY_ID,
            LEGALNAME as COMPANY_NAME,
            COUNTRYOFINCORPORATION as COUNTRY_CODE,
            SIC_DESCRIPTION as INDUSTRY_DESCRIPTION,
            CIK,
            CASE 
                WHEN LEGALNAME ILIKE '%INC%' OR LEGALNAME ILIKE '%CORP%' THEN 'PUBLIC'
                ELSE 'PUBLIC'
            END as COMPANY_TYPE,
            'USD' as REPORTING_CURRENCY,
            CURRENT_TIMESTAMP() as LAST_UPDATED
        FROM prioritized_issuers
        ORDER BY PRIORITY, LEGALNAME
        LIMIT {company_limit}
    """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.DIM_COMPANY").collect()[0]['CNT']
    print(f"    ✅ DIM_COMPANY: {count} companies")
    
    # DIM_BROKER - Broker firms
    print("  Building DIM_BROKER...")
    brokers = []
    for i, broker_name in enumerate(config.BROKER_NAMES, 1):
        brokers.append({
            'BROKER_ID': i,
            'BROKER_NAME': broker_name,
            'BROKER_TYPE': 'SELL_SIDE',
            'IS_ACTIVE': True
        })
    
    df = session.create_dataframe(brokers)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{market_data_schema}.DIM_BROKER")
    print(f"    ✅ DIM_BROKER: {len(brokers)} brokers")


def build_financial_periods(session: Session, test_mode: bool = False):
    """Build financial period reference data."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    print("  Building FACT_FINANCIAL_PERIOD...")
    
    years_of_history = config.MARKET_DATA['generation']['years_of_history']
    if test_mode:
        years_of_history = 2
    
    # Generate fiscal periods for each company
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_FINANCIAL_PERIOD AS
        WITH companies AS (
            SELECT COMPANY_ID FROM {database_name}.{market_data_schema}.DIM_COMPANY
        ),
        years AS (
            SELECT SEQ4() + 1 as YEAR_OFFSET
            FROM TABLE(GENERATOR(ROWCOUNT => {years_of_history}))
        ),
        quarters AS (
            SELECT SEQ4() + 1 as FISCAL_QUARTER
            FROM TABLE(GENERATOR(ROWCOUNT => 4))
        ),
        periods AS (
            SELECT 
                c.COMPANY_ID,
                YEAR(CURRENT_DATE()) - y.YEAR_OFFSET as FISCAL_YEAR,
                q.FISCAL_QUARTER,
                DATE_FROM_PARTS(YEAR(CURRENT_DATE()) - y.YEAR_OFFSET, q.FISCAL_QUARTER * 3, 
                    CASE q.FISCAL_QUARTER 
                        WHEN 1 THEN 31 
                        WHEN 2 THEN 30 
                        WHEN 3 THEN 30 
                        WHEN 4 THEN 31 
                    END) as PERIOD_END_DATE
            FROM companies c
            CROSS JOIN years y
            CROSS JOIN quarters q
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY COMPANY_ID, FISCAL_YEAR, FISCAL_QUARTER) as PERIOD_ID,
            COMPANY_ID,
            FISCAL_YEAR,
            FISCAL_QUARTER,
            CONCAT(FISCAL_YEAR::VARCHAR, 'Q', FISCAL_QUARTER::VARCHAR) as PERIOD_CODE,
            PERIOD_END_DATE,
            DATEADD(day, 45, PERIOD_END_DATE) as FILING_DATE,  -- ~45 days after period end
            'QUARTERLY' as PERIOD_TYPE,
            CURRENT_TIMESTAMP() as LAST_UPDATED
        FROM periods
        WHERE PERIOD_END_DATE <= CURRENT_DATE()
        ORDER BY COMPANY_ID, FISCAL_YEAR, FISCAL_QUARTER
    """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_FINANCIAL_PERIOD").collect()[0]['CNT']
    print(f"    ✅ FACT_FINANCIAL_PERIOD: {count} periods")


def build_financial_data(session: Session, test_mode: bool = False):
    """Build financial statement data with realistic values."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    print("  Building FACT_FINANCIAL_DATA...")
    
    # Generate financial data for each company/period combination
    # Using SQL for efficient generation with realistic patterns
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_FINANCIAL_DATA AS
        WITH base_financials AS (
            SELECT 
                fp.PERIOD_ID,
                fp.COMPANY_ID,
                fp.FISCAL_YEAR,
                fp.FISCAL_QUARTER,
                c.COMPANY_NAME,
                c.INDUSTRY_DESCRIPTION,
                -- Base revenue varies by company size (using HASH for deterministic randomness)
                POWER(10, 8 + MOD(c.COMPANY_ID, 4)) * (1 + ABS(MOD(HASH(c.COMPANY_ID), 100)) / 200.0) as BASE_REVENUE,
                -- Growth rate varies by industry
                CASE 
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%software%' OR c.INDUSTRY_DESCRIPTION ILIKE '%semiconductor%' THEN 0.15
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%technology%' THEN 0.12
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%health%' OR c.INDUSTRY_DESCRIPTION ILIKE '%pharma%' THEN 0.08
                    ELSE 0.05
                END as ANNUAL_GROWTH_RATE,
                -- Margin profiles by industry
                CASE 
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%software%' THEN 0.75
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%semiconductor%' THEN 0.55
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%technology%' THEN 0.45
                    ELSE 0.35
                END as GROSS_MARGIN_BASE,
                CASE 
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%software%' THEN 0.25
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%semiconductor%' THEN 0.30
                    WHEN c.INDUSTRY_DESCRIPTION ILIKE '%technology%' THEN 0.20
                    ELSE 0.12
                END as OPERATING_MARGIN_BASE
            FROM {database_name}.{market_data_schema}.FACT_FINANCIAL_PERIOD fp
            JOIN {database_name}.{market_data_schema}.DIM_COMPANY c ON fp.COMPANY_ID = c.COMPANY_ID
        ),
        calculated_financials AS (
            SELECT 
                PERIOD_ID,
                COMPANY_ID,
                FISCAL_YEAR,
                FISCAL_QUARTER,
                -- Calculate revenue with growth and seasonality (using HASH for deterministic variance)
                BASE_REVENUE * 
                    POWER(1 + ANNUAL_GROWTH_RATE, (YEAR(CURRENT_DATE()) - FISCAL_YEAR)) *
                    (1 + (FISCAL_QUARTER - 2.5) * 0.05) *  -- Q4 tends to be higher
                    (1 + (ABS(MOD(HASH(PERIOD_ID * 1000 + COMPANY_ID), 100)) - 50) / 1000.0) as REVENUE,
                GROSS_MARGIN_BASE * (1 + (ABS(MOD(HASH(PERIOD_ID * 1001 + COMPANY_ID), 100)) - 50) / 1666.0) as GROSS_MARGIN,
                OPERATING_MARGIN_BASE * (1 + (ABS(MOD(HASH(PERIOD_ID * 1002 + COMPANY_ID), 100)) - 50) / 1000.0) as OPERATING_MARGIN
            FROM base_financials
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) as FINANCIAL_DATA_ID,
            PERIOD_ID,
            COMPANY_ID,
            -- Revenue
            1001 as DATA_ITEM_ID,  -- REVENUE
            ROUND(REVENUE, 0) as DATA_VALUE,
            'USD' as CURRENCY_CODE,
            CURRENT_TIMESTAMP() as LAST_UPDATED
        FROM calculated_financials
        
        UNION ALL
        
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) + 1000000,
            PERIOD_ID,
            COMPANY_ID,
            1003 as DATA_ITEM_ID,  -- GROSS_PROFIT
            ROUND(REVENUE * GROSS_MARGIN, 0),
            'USD',
            CURRENT_TIMESTAMP()
        FROM calculated_financials
        
        UNION ALL
        
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) + 2000000,
            PERIOD_ID,
            COMPANY_ID,
            1004 as DATA_ITEM_ID,  -- OPERATING_INCOME
            ROUND(REVENUE * OPERATING_MARGIN, 0),
            'USD',
            CURRENT_TIMESTAMP()
        FROM calculated_financials
        
        UNION ALL
        
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) + 3000000,
            PERIOD_ID,
            COMPANY_ID,
            1005 as DATA_ITEM_ID,  -- NET_INCOME
            ROUND(REVENUE * OPERATING_MARGIN * 0.78, 0),  -- ~22% effective tax rate
            'USD',
            CURRENT_TIMESTAMP()
        FROM calculated_financials
        
        UNION ALL
        
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) + 4000000,
            PERIOD_ID,
            COMPANY_ID,
            1008 as DATA_ITEM_ID,  -- EBITDA
            ROUND(REVENUE * OPERATING_MARGIN * 1.15, 0),  -- EBITDA ~15% higher than operating income
            'USD',
            CURRENT_TIMESTAMP()
        FROM calculated_financials
        
        UNION ALL
        
        -- Free Cash Flow
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) + 5000000,
            PERIOD_ID,
            COMPANY_ID,
            3003 as DATA_ITEM_ID,  -- FREE_CASH_FLOW
            ROUND(REVENUE * OPERATING_MARGIN * 0.65, 0),  -- FCF ~65% of operating income
            'USD',
            CURRENT_TIMESTAMP()
        FROM calculated_financials
    """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_FINANCIAL_DATA").collect()[0]['CNT']
    print(f"    ✅ FACT_FINANCIAL_DATA: {count} data points")


def build_broker_analyst_data(session: Session, test_mode: bool = False):
    """Build broker and analyst coverage data."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    print("  Building DIM_ANALYST and FACT_ANALYST_COVERAGE...")
    
    # Generate analysts (multiple per broker)
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.DIM_ANALYST AS
        WITH analyst_names AS (
            SELECT 
                b.BROKER_ID,
                b.BROKER_NAME,
                a.ANALYST_NUM,
                CASE MOD(b.BROKER_ID * 10 + a.ANALYST_NUM, 20)
                    WHEN 0 THEN 'Michael Chen'
                    WHEN 1 THEN 'Sarah Johnson'
                    WHEN 2 THEN 'David Williams'
                    WHEN 3 THEN 'Jennifer Martinez'
                    WHEN 4 THEN 'Robert Taylor'
                    WHEN 5 THEN 'Lisa Anderson'
                    WHEN 6 THEN 'James Wilson'
                    WHEN 7 THEN 'Emily Brown'
                    WHEN 8 THEN 'Christopher Davis'
                    WHEN 9 THEN 'Amanda Miller'
                    WHEN 10 THEN 'Daniel Garcia'
                    WHEN 11 THEN 'Rachel Thompson'
                    WHEN 12 THEN 'Matthew Robinson'
                    WHEN 13 THEN 'Jessica Lee'
                    WHEN 14 THEN 'Andrew Clark'
                    WHEN 15 THEN 'Stephanie White'
                    WHEN 16 THEN 'Kevin Harris'
                    WHEN 17 THEN 'Nicole Lewis'
                    WHEN 18 THEN 'Brian Walker'
                    ELSE 'Catherine Hall'
                END as ANALYST_NAME
            FROM {database_name}.{market_data_schema}.DIM_BROKER b
            CROSS JOIN (SELECT SEQ4() + 1 as ANALYST_NUM FROM TABLE(GENERATOR(ROWCOUNT => 5))) a
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY BROKER_ID, ANALYST_NUM) as ANALYST_ID,
            BROKER_ID,
            ANALYST_NAME,
            CASE MOD(BROKER_ID + ANALYST_NUM, 5)
                WHEN 0 THEN 'Technology'
                WHEN 1 THEN 'Healthcare'
                WHEN 2 THEN 'Consumer'
                WHEN 3 THEN 'Financials'
                ELSE 'Industrials'
            END as SECTOR_COVERAGE,
            TRUE as IS_ACTIVE
        FROM analyst_names
    """).collect()
    
    analyst_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.DIM_ANALYST").collect()[0]['CNT']
    print(f"    ✅ DIM_ANALYST: {analyst_count} analysts")
    
    # Generate analyst coverage (which analysts cover which companies)
    min_brokers, max_brokers = config.MARKET_DATA['generation']['brokers_per_company']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_ANALYST_COVERAGE AS
        WITH company_broker_pairs AS (
            SELECT 
                c.COMPANY_ID,
                a.ANALYST_ID,
                a.BROKER_ID,
                -- Assign brokers to companies using HASH for deterministic ordering
                ROW_NUMBER() OVER (PARTITION BY c.COMPANY_ID ORDER BY ABS(HASH(c.COMPANY_ID * 1000 + a.ANALYST_ID))) as BROKER_RANK,
                -- Calculate how many brokers this company should have (3-8)
                {min_brokers} + MOD(ABS(HASH(c.COMPANY_ID)), {max_brokers - min_brokers + 1}) as BROKER_COUNT
            FROM {database_name}.{market_data_schema}.DIM_COMPANY c
            CROSS JOIN {database_name}.{market_data_schema}.DIM_ANALYST a
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY COMPANY_ID, ANALYST_ID) as COVERAGE_ID,
            COMPANY_ID,
            ANALYST_ID,
            BROKER_ID,
            DATEADD(day, -(30 + MOD(ABS(HASH(COMPANY_ID * 100 + ANALYST_ID)), 335)), CURRENT_DATE()) as COVERAGE_START_DATE,
            NULL as COVERAGE_END_DATE,
            TRUE as IS_ACTIVE
        FROM company_broker_pairs
        WHERE BROKER_RANK <= BROKER_COUNT
    """).collect()
    
    coverage_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_ANALYST_COVERAGE").collect()[0]['CNT']
    print(f"    ✅ FACT_ANALYST_COVERAGE: {coverage_count} coverage records")


def build_estimate_data(session: Session, test_mode: bool = False):
    """Build analyst estimates and consensus data."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    print("  Building FACT_ESTIMATE_CONSENSUS...")
    
    forward_years = config.MARKET_DATA['generation']['estimates_forward_years']
    if test_mode:
        forward_years = 1
    
    # Generate consensus estimates for future periods
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_ESTIMATE_CONSENSUS AS
        WITH future_periods AS (
            SELECT 
                c.COMPANY_ID,
                YEAR(CURRENT_DATE()) + y.YEAR_OFFSET as ESTIMATE_YEAR,
                q.FISCAL_QUARTER
            FROM {database_name}.{market_data_schema}.DIM_COMPANY c
            CROSS JOIN (SELECT SEQ4() as YEAR_OFFSET FROM TABLE(GENERATOR(ROWCOUNT => {forward_years + 1}))) y
            CROSS JOIN (SELECT SEQ4() + 1 as FISCAL_QUARTER FROM TABLE(GENERATOR(ROWCOUNT => 4))) q
            WHERE DATE_FROM_PARTS(YEAR(CURRENT_DATE()) + y.YEAR_OFFSET, q.FISCAL_QUARTER * 3, 1) > CURRENT_DATE()
        ),
        latest_actuals AS (
            SELECT 
                fd.COMPANY_ID,
                fd.DATA_ITEM_ID,
                fd.DATA_VALUE as LATEST_ACTUAL,
                ROW_NUMBER() OVER (PARTITION BY fd.COMPANY_ID, fd.DATA_ITEM_ID ORDER BY fp.FISCAL_YEAR DESC, fp.FISCAL_QUARTER DESC) as RN
            FROM {database_name}.{market_data_schema}.FACT_FINANCIAL_DATA fd
            JOIN {database_name}.{market_data_schema}.FACT_FINANCIAL_PERIOD fp ON fd.PERIOD_ID = fp.PERIOD_ID
            WHERE fd.DATA_ITEM_ID IN (1001, 1005, 1008)  -- Revenue, Net Income, EBITDA
        ),
        base_estimates AS (
            SELECT 
                fp.COMPANY_ID,
                fp.ESTIMATE_YEAR,
                fp.FISCAL_QUARTER,
                la.DATA_ITEM_ID,
                la.LATEST_ACTUAL,
                -- Growth assumptions by year
                CASE fp.ESTIMATE_YEAR - YEAR(CURRENT_DATE())
                    WHEN 0 THEN 1.08  -- Current year: 8% growth
                    WHEN 1 THEN 1.15  -- Next year: 15% growth from current
                    ELSE 1.25         -- Year after: 25% growth from current
                END as GROWTH_FACTOR
            FROM future_periods fp
            JOIN latest_actuals la ON fp.COMPANY_ID = la.COMPANY_ID AND la.RN = 1
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY COMPANY_ID, ESTIMATE_YEAR, FISCAL_QUARTER, DATA_ITEM_ID) as CONSENSUS_ID,
            COMPANY_ID,
            ESTIMATE_YEAR,
            FISCAL_QUARTER,
            DATA_ITEM_ID,
            -- Use HASH for deterministic variance
            ROUND(LATEST_ACTUAL * GROWTH_FACTOR * (1 + (ABS(MOD(HASH(COMPANY_ID * 1000 + ESTIMATE_YEAR * 10 + FISCAL_QUARTER), 100)) - 50) / 1000.0), 0) as CONSENSUS_MEAN,
            ROUND(LATEST_ACTUAL * GROWTH_FACTOR * 0.95, 0) as CONSENSUS_LOW,
            ROUND(LATEST_ACTUAL * GROWTH_FACTOR * 1.05, 0) as CONSENSUS_HIGH,
            5 + MOD(ABS(HASH(COMPANY_ID * 7)), 11) as NUM_ESTIMATES,  -- 5-15 estimates
            CURRENT_DATE() as AS_OF_DATE,
            CURRENT_TIMESTAMP() as LAST_UPDATED
        FROM base_estimates
    """).collect()
    
    consensus_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_ESTIMATE_CONSENSUS").collect()[0]['CNT']
    print(f"    ✅ FACT_ESTIMATE_CONSENSUS: {consensus_count} consensus records")
    
    # Generate price targets and ratings
    print("  Building FACT_ESTIMATE_DATA (price targets & ratings)...")
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_ESTIMATE_DATA AS
        WITH analyst_estimates AS (
            SELECT 
                ac.COVERAGE_ID,
                ac.COMPANY_ID,
                ac.ANALYST_ID,
                ac.BROKER_ID,
                -- Generate price target using HASH for deterministic values (50-500 range with variance)
                ROUND(50 + (ABS(MOD(HASH(ac.COVERAGE_ID * 1000), 450))) * 
                    (0.8 + ABS(MOD(HASH(ac.COVERAGE_ID * 1001), 50)) / 100.0), 2) as PRICE_TARGET,
                -- Generate rating (1=Buy, 2=Outperform, 3=Hold, 4=Underperform, 5=Sell)
                -- Using HASH to get deterministic distribution
                CASE 
                    WHEN MOD(ABS(HASH(ac.COVERAGE_ID * 1002)), 100) < 35 THEN 1  -- 35% Buy
                    WHEN MOD(ABS(HASH(ac.COVERAGE_ID * 1002)), 100) < 55 THEN 2  -- 20% Outperform
                    WHEN MOD(ABS(HASH(ac.COVERAGE_ID * 1002)), 100) < 85 THEN 3  -- 30% Hold
                    WHEN MOD(ABS(HASH(ac.COVERAGE_ID * 1002)), 100) < 95 THEN 4  -- 10% Underperform
                    ELSE 5  -- 5% Sell
                END as RATING_CODE,
                DATEADD(day, -(1 + MOD(ABS(HASH(ac.COVERAGE_ID * 1003)), 89)), CURRENT_DATE()) as ESTIMATE_DATE
            FROM {database_name}.{market_data_schema}.FACT_ANALYST_COVERAGE ac
            WHERE ac.IS_ACTIVE = TRUE
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY COMPANY_ID, ANALYST_ID) as ESTIMATE_ID,
            COMPANY_ID,
            ANALYST_ID,
            BROKER_ID,
            5005 as DATA_ITEM_ID,  -- Price Target
            PRICE_TARGET as DATA_VALUE,
            ESTIMATE_DATE,
            CURRENT_TIMESTAMP() as LAST_UPDATED
        FROM analyst_estimates
        
        UNION ALL
        
        SELECT 
            ROW_NUMBER() OVER (ORDER BY COMPANY_ID, ANALYST_ID) + 1000000,
            COMPANY_ID,
            ANALYST_ID,
            BROKER_ID,
            5006 as DATA_ITEM_ID,  -- Rating
            RATING_CODE,
            ESTIMATE_DATE,
            CURRENT_TIMESTAMP()
        FROM analyst_estimates
    """).collect()
    
    estimate_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_ESTIMATE_DATA").collect()[0]['CNT']
    print(f"    ✅ FACT_ESTIMATE_DATA: {estimate_count} estimate records")


def build_filing_reference_tables(session: Session, test_mode: bool = False):
    """Build filing reference tables following S&P Capital IQ pattern."""
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    print("  Building Filing Reference Tables...")
    
    # REF_FILING_TYPE - Filing type definitions
    print("    Building REF_FILING_TYPE...")
    filing_types = []
    for ft in config.FILING_TYPES:
        filing_types.append({
            'FILING_TYPE_ID': ft['id'],
            'FILING_TYPE': ft['type'],
            'FILING_TYPE_DEFINITION': ft['definition'],
            'IS_ANNUAL': ft['is_annual'],
            'IS_QUARTERLY': ft['is_quarterly']
        })
    
    df = session.create_dataframe(filing_types)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_FILING_TYPE")
    print(f"      ✅ REF_FILING_TYPE: {len(filing_types)} types")
    
    # REF_FILING_SOURCE - Filing source definitions
    print("    Building REF_FILING_SOURCE...")
    filing_sources = []
    for fs in config.FILING_SOURCES:
        filing_sources.append({
            'FILING_SOURCE_ID': fs['id'],
            'FILING_SOURCE': fs['source'],
            'FILING_SOURCE_DESC': fs['description']
        })
    
    df = session.create_dataframe(filing_sources)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_FILING_SOURCE")
    print(f"      ✅ REF_FILING_SOURCE: {len(filing_sources)} sources")
    
    # REF_FILING_LANGUAGE - Language definitions
    print("    Building REF_FILING_LANGUAGE...")
    filing_languages = []
    for fl in config.FILING_LANGUAGES:
        filing_languages.append({
            'FILING_LANGUAGE_ID': fl['id'],
            'FILING_LANGUAGE': fl['language'],
            'LANGUAGE_CODE': fl['code']
        })
    
    df = session.create_dataframe(filing_languages)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_FILING_LANGUAGE")
    print(f"      ✅ REF_FILING_LANGUAGE: {len(filing_languages)} languages")
    
    # REF_FILING_INSTITUTION_REL_TYPE - Institution relationship types
    print("    Building REF_FILING_INSTITUTION_REL_TYPE...")
    rel_types = []
    for rt in config.FILING_INSTITUTION_REL_TYPES:
        rel_types.append({
            'REL_TYPE_ID': rt['id'],
            'REL_TYPE': rt['type'],
            'REL_TYPE_DESC': rt['description']
        })
    
    df = session.create_dataframe(rel_types)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_FILING_INSTITUTION_REL_TYPE")
    print(f"      ✅ REF_FILING_INSTITUTION_REL_TYPE: {len(rel_types)} types")


def build_filing_data(session: Session, test_mode: bool = False):
    """Build filing data tables following S&P Capital IQ pattern."""
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    
    years_of_history = config.MARKET_DATA['generation']['years_of_history']
    if test_mode:
        years_of_history = 2
    
    print("  Building Filing Data Tables...")
    
    # FACT_FILING_REF - Master filing reference (one row per filing)
    print("    Building FACT_FILING_REF...")
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_FILING_REF AS
        WITH company_filings AS (
            SELECT 
                c.COMPANY_ID,
                c.COMPANY_NAME,
                c.CIK,
                y.YEAR_NUM as FISCAL_YEAR,
                -- Generate quarterly filings (10-Q)
                q.QUARTER_NUM as FISCAL_QUARTER,
                CASE q.QUARTER_NUM
                    WHEN 1 THEN 2  -- 10-Q
                    WHEN 2 THEN 2  -- 10-Q
                    WHEN 3 THEN 2  -- 10-Q
                    WHEN 4 THEN 1  -- 10-K for Q4
                END as FILING_TYPE_ID,
                DATE_FROM_PARTS(y.YEAR_NUM, q.QUARTER_NUM * 3, 
                    CASE q.QUARTER_NUM 
                        WHEN 1 THEN 31 
                        WHEN 2 THEN 30 
                        WHEN 3 THEN 30 
                        WHEN 4 THEN 31 
                    END) as PERIOD_END_DATE
            FROM {database_name}.{schema_name}.DIM_COMPANY c
            CROSS JOIN (
                SELECT YEAR(CURRENT_DATE()) - SEQ4() as YEAR_NUM
                FROM TABLE(GENERATOR(ROWCOUNT => {years_of_history}))
            ) y
            CROSS JOIN (
                SELECT SEQ4() + 1 as QUARTER_NUM
                FROM TABLE(GENERATOR(ROWCOUNT => 4))
            ) q
            WHERE DATE_FROM_PARTS(y.YEAR_NUM, q.QUARTER_NUM * 3, 1) <= CURRENT_DATE()
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY COMPANY_ID, FISCAL_YEAR, FISCAL_QUARTER) as FILE_VERSION_ID,
            ROW_NUMBER() OVER (ORDER BY COMPANY_ID, FISCAL_YEAR, FISCAL_QUARTER) as FILING_ID,
            COMPANY_ID,
            CIK,
            PERIOD_END_DATE as PERIOD_DATE,
            FISCAL_YEAR,
            FISCAL_QUARTER,
            FILING_TYPE_ID,
            1 as FILING_SOURCE_ID,  -- SEC_EDGAR
            1 as FILING_LANGUAGE_ID,  -- English
            DATEADD(day, 45 + MOD(ABS(HASH(COMPANY_ID * 1000 + FISCAL_YEAR * 10 + FISCAL_QUARTER)), 15), PERIOD_END_DATE) as FILING_DATE,
            CONCAT(LPAD(CIK, 10, '0'), '-', FISCAL_YEAR::VARCHAR, '-', 
                   LPAD((COMPANY_ID * 100 + FISCAL_QUARTER)::VARCHAR, 6, '0')) as ACCESSION_NUMBER,
            CONCAT('https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=', CIK) as DOCUMENT_URL,
            FALSE as FILE_TRANSLATED,
            DATEADD(day, 46 + MOD(ABS(HASH(COMPANY_ID * 1001 + FISCAL_YEAR)), 10), PERIOD_END_DATE) as FILING_FIRST_AVAILABLE,
            CURRENT_TIMESTAMP() as LAST_UPDATED
        FROM company_filings
        ORDER BY COMPANY_ID, FISCAL_YEAR, FISCAL_QUARTER
    """).collect()
    
    filing_ref_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_FILING_REF").collect()[0]['CNT']
    print(f"      ✅ FACT_FILING_REF: {filing_ref_count} filings")
    
    # FACT_FILING_INSTITUTION_REL - Company-to-filing relationships
    print("    Building FACT_FILING_INSTITUTION_REL...")
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_FILING_INSTITUTION_REL AS
        SELECT 
            fr.FILE_VERSION_ID,
            fr.COMPANY_ID as INSTITUTION_ID,
            1 as REL_TYPE_ID  -- FILER
        FROM {database_name}.{schema_name}.FACT_FILING_REF fr
    """).collect()
    
    rel_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_FILING_INSTITUTION_REL").collect()[0]['CNT']
    print(f"      ✅ FACT_FILING_INSTITUTION_REL: {rel_count} relationships")
    
    # FACT_FILING_DATA - Textual filing content (SEC filings with parsed sections)
    print("    Building FACT_FILING_DATA...")
    
    # Build section content for 10-K and 10-Q filings
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_FILING_DATA AS
        WITH filing_sections AS (
            SELECT 
                fr.FILE_VERSION_ID,
                fr.COMPANY_ID,
                fr.FILING_TYPE_ID,
                c.COMPANY_NAME,
                c.INDUSTRY_DESCRIPTION,
                fr.FISCAL_YEAR,
                fr.FISCAL_QUARTER
            FROM {database_name}.{schema_name}.FACT_FILING_REF fr
            JOIN {database_name}.{schema_name}.DIM_COMPANY c ON fr.COMPANY_ID = c.COMPANY_ID
        ),
        -- Generate 10-K sections
        ten_k_sections AS (
            SELECT 
                fs.FILE_VERSION_ID,
                s.HEADING_ID,
                NULL as PARENT_HEADING_ID,
                s.HEADING,
                s.STANDARDIZED_HEADING,
                CASE s.HEADING_ID
                    WHEN 1 THEN CONCAT(
                        fs.COMPANY_NAME, ' is a leading company in the ', COALESCE(fs.INDUSTRY_DESCRIPTION, 'technology'), ' industry. ',
                        'The company operates through multiple business segments and serves customers worldwide. ',
                        'Our products and services include innovative solutions that address key market needs. ',
                        'We have a strong track record of growth and continue to invest in research and development ',
                        'to maintain our competitive position in the market.'
                    )
                    WHEN 2 THEN CONCAT(
                        'Investing in our securities involves a high degree of risk. You should carefully consider the following risks ',
                        'before making an investment decision. Our business, financial condition, and results of operations could be ',
                        'materially and adversely affected by any of these risks. Key risks include: ',
                        '(1) Competition in our industry is intense; ',
                        '(2) We depend on key personnel; ',
                        '(3) Economic conditions may adversely affect our business; ',
                        '(4) Cybersecurity threats could harm our operations; ',
                        '(5) Regulatory changes may impact our business model.'
                    )
                    WHEN 9 THEN CONCAT(
                        'Management''s Discussion and Analysis of Financial Condition and Results of Operations for ', 
                        fs.COMPANY_NAME, '. ',
                        'During fiscal year ', fs.FISCAL_YEAR::VARCHAR, ', we achieved significant milestones in our strategic initiatives. ',
                        'Revenue growth was driven by strong demand for our products and services. ',
                        'We continued to invest in innovation while maintaining operational efficiency. ',
                        'Our balance sheet remains strong with adequate liquidity to fund operations and strategic investments.'
                    )
                    WHEN 11 THEN CONCAT(
                        'The consolidated financial statements include the accounts of ', fs.COMPANY_NAME, 
                        ' and its subsidiaries. All significant intercompany transactions have been eliminated. ',
                        'Revenue is recognized when control of promised goods or services is transferred to customers. ',
                        'We use estimates and assumptions that affect reported amounts of assets, liabilities, revenues, and expenses.'
                    )
                    WHEN 14 THEN CONCAT(
                        'Our Board of Directors consists of experienced professionals with diverse backgrounds in technology, ',
                        'finance, and business operations. The executive team has deep industry expertise and a proven track record ',
                        'of delivering shareholder value. Our corporate governance practices meet or exceed industry standards.'
                    )
                    WHEN 15 THEN CONCAT(
                        'Executive compensation is designed to attract and retain top talent while aligning management interests ',
                        'with those of shareholders. Our compensation program includes base salary, annual incentive bonuses, ',
                        'and long-term equity awards. Performance metrics are tied to financial and operational objectives.'
                    )
                    ELSE CONCAT(
                        'This section contains information about ', s.STANDARDIZED_HEADING, ' for ', fs.COMPANY_NAME, '. ',
                        'Please refer to our SEC filings for complete details and disclosures.'
                    )
                END as SECTION_TEXT
            FROM filing_sections fs
            CROSS JOIN (
                SELECT 1 as HEADING_ID, 'Item 1' as HEADING, 'Business' as STANDARDIZED_HEADING UNION ALL
                SELECT 2, 'Item 1A', 'Risk Factors' UNION ALL
                SELECT 9, 'Item 7', 'MD&A' UNION ALL
                SELECT 11, 'Item 8', 'Financial Statements and Supplementary Data' UNION ALL
                SELECT 14, 'Item 10', 'Directors and Executive Officers' UNION ALL
                SELECT 15, 'Item 11', 'Executive Compensation'
            ) s
            WHERE fs.FILING_TYPE_ID = 1  -- 10-K only
        ),
        -- Generate 10-Q sections
        ten_q_sections AS (
            SELECT 
                fs.FILE_VERSION_ID,
                s.HEADING_ID,
                NULL as PARENT_HEADING_ID,
                s.HEADING,
                s.STANDARDIZED_HEADING,
                CASE s.HEADING_ID
                    WHEN 101 THEN CONCAT(
                        'Condensed consolidated financial statements for ', fs.COMPANY_NAME, ' for Q', fs.FISCAL_QUARTER::VARCHAR, ' ', fs.FISCAL_YEAR::VARCHAR, '. ',
                        'These unaudited financial statements have been prepared in accordance with U.S. GAAP for interim financial reporting.'
                    )
                    WHEN 102 THEN CONCAT(
                        'Management''s Discussion and Analysis for Q', fs.FISCAL_QUARTER::VARCHAR, ' ', fs.FISCAL_YEAR::VARCHAR, '. ',
                        'During this quarter, ', fs.COMPANY_NAME, ' continued to execute on its strategic priorities. ',
                        'We saw positive trends in key operating metrics and maintained our focus on profitable growth.'
                    )
                    WHEN 106 THEN CONCAT(
                        'The risk factors disclosed in our Annual Report on Form 10-K remain applicable. ',
                        'There have been no material changes to our risk factors during the quarter ended Q', 
                        fs.FISCAL_QUARTER::VARCHAR, ' ', fs.FISCAL_YEAR::VARCHAR, '.'
                    )
                    ELSE CONCAT(
                        'Quarterly disclosure for ', s.STANDARDIZED_HEADING, '. ',
                        'Please refer to our complete SEC filings for additional details.'
                    )
                END as SECTION_TEXT
            FROM filing_sections fs
            CROSS JOIN (
                SELECT 101 as HEADING_ID, 'Part I Item 1' as HEADING, 'Financial Statements' as STANDARDIZED_HEADING UNION ALL
                SELECT 102, 'Part I Item 2', 'MD&A' UNION ALL
                SELECT 106, 'Part II Item 1A', 'Risk Factors'
            ) s
            WHERE fs.FILING_TYPE_ID = 2  -- 10-Q only
        )
        SELECT * FROM ten_k_sections
        UNION ALL
        SELECT * FROM ten_q_sections
        ORDER BY FILE_VERSION_ID, HEADING_ID
    """).collect()
    
    filing_data_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_FILING_DATA").collect()[0]['CNT']
    print(f"      ✅ FACT_FILING_DATA: {filing_data_count} sections")
    
    # Create empty tables for non-SEC and ESG filings (for future expansion)
    print("    Building FACT_FILING_DATA_NON_SEC (placeholder)...")
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_FILING_DATA_NON_SEC (
            FILE_VERSION_ID INTEGER,
            HEADING_ID INTEGER,
            PARENT_HEADING_ID INTEGER,
            HEADING VARCHAR(1000),
            STANDARDIZED_HEADING VARCHAR(1000),
            SECTION_TEXT TEXT,
            PRIMARY KEY (FILE_VERSION_ID, HEADING_ID)
        )
    """).collect()
    print(f"      ✅ FACT_FILING_DATA_NON_SEC: 0 sections (placeholder)")
    
    print("    Building FACT_FILING_DATA_ESG (placeholder)...")
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_FILING_DATA_ESG (
            FILE_VERSION_ID INTEGER,
            HEADING_ID INTEGER,
            PARENT_HEADING_ID INTEGER,
            HEADING VARCHAR(1000),
            STANDARDIZED_HEADING VARCHAR(1000),
            SECTION_TEXT TEXT,
            PRIMARY KEY (FILE_VERSION_ID, HEADING_ID)
        )
    """).collect()
    print(f"      ✅ FACT_FILING_DATA_ESG: 0 sections (placeholder)")


if __name__ == "__main__":
    # For testing - create session and run
    from snowflake.snowpark import Session
    
    session = Session.builder.config("connection_name", config.DEFAULT_CONNECTION_NAME).create()
    
    try:
        build_all(session, test_mode=True)
    finally:
        session.close()

