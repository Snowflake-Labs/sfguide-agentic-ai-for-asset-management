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
        config.log_warning("MARKET_DATA schema disabled in config, skipping...")
        return
    
    config.log_phase("Market Data (External Provider)")
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    # Create schema if not exists
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {database_name}.{schema_name}").collect()
    
    # Build tables in dependency order
    config.log_step("Reference tables")
    build_reference_tables(session, test_mode)
    
    config.log_step("Company master")
    build_company_master(session, test_mode)
    
    config.log_step("Financial periods")
    build_financial_periods(session, test_mode)
    
    # Check if real data integration is enabled
    use_real_data = config.REAL_DATA_SOURCES.get('enabled', False)
    
    # Always build synthetic financial data first (required for downstream dependencies)
    config.log_step("Financial data (synthetic)")
    build_financial_data(session, test_mode)
    
    config.log_step("Filing reference tables")
    build_filing_reference_tables(session, test_mode)
    
    config.log_step("Filing data")
    build_filing_data(session, test_mode)
    
    # If real data is enabled, also build supplementary real data tables
    if use_real_data:
        config.log_step("Real SEC financial data")
        try:
            build_real_financial_data(session, test_mode)
        except Exception as e:
            config.log_warning(f"Error building real financial data: {e}")
        
        config.log_step("Real stock prices")
        try:
            build_real_stock_prices(session, test_mode)
        except Exception as e:
            config.log_warning(f"Error building real stock prices: {e}")
        
        config.log_step("Real SEC filing text")
        try:
            build_real_sec_filing_text(session, test_mode)
        except Exception as e:
            config.log_warning(f"Error building real filing text: {e}")
        
        config.log_step("Real SEC financials (comprehensive)")
        try:
            build_real_sec_financials(session, test_mode)
        except Exception as e:
            config.log_warning(f"Error building real SEC financials: {e}")
    
    config.log_step("Broker analyst data")
    build_broker_analyst_data(session, test_mode)
    
    config.log_step("Estimate data")
    build_estimate_data(session, test_mode)
    
    config.log_phase_complete("Market data complete")


# =============================================================================
# REAL DATA INTEGRATION FUNCTIONS
# =============================================================================

def verify_real_data_access(session: Session) -> bool:
    """
    Verify access to the configured real data share.
    
    Uses REAL_DATA_SOURCES['access_probe_table_key'] to determine which table
    to probe. This allows the demo to work with different public data shares.
    """
    try:
        real_db = config.REAL_DATA_SOURCES['database']
        real_schema = config.REAL_DATA_SOURCES['schema']
        
        # Get probe table from config (key into REAL_DATA_SOURCES['tables'])
        probe_key = config.REAL_DATA_SOURCES.get('access_probe_table_key', 'sec_metrics')
        probe_table_entry = config.REAL_DATA_SOURCES.get('tables', {}).get(probe_key, {})
        probe_table = probe_table_entry.get('table', 'SEC_METRICS_TIMESERIES')
        
        # Test access to the configured probe table
        result = session.sql(f"""
            SELECT 1 FROM {real_db}.{real_schema}.{probe_table} LIMIT 1
        """).collect()
        return True
    except Exception as e:
        config.log_warning(f"  Cannot access {real_db}.{real_schema} (probe table: {probe_table}): {e}")
        return False


def build_real_financial_data(session: Session, test_mode: bool = False) -> bool:
    """
    Build FACT_FINANCIAL_DATA_SEC from real SEC_METRICS_TIMESERIES data.
    
    This replaces synthetic financial data with real SEC filing data for companies
    that have CIK linkage in our DIM_ISSUER.
    """
    if not verify_real_data_access(session):
        return False
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    sec_metrics_table = config.REAL_DATA_SOURCES['tables']['sec_metrics']['table']
    
    config.log_detail("Building FACT_FINANCIAL_DATA_SEC from real SEC data...")
    
    # Limit records in test mode
    limit_clause = "LIMIT 100000" if test_mode else ""
    
    try:
        # Create table with real SEC metrics linked to our companies via CIK
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_FINANCIAL_DATA_SEC AS
            WITH our_companies AS (
                -- Get companies from DIM_COMPANY that have CIK
                SELECT 
                    dc.COMPANY_ID,
                    dc.COMPANY_NAME,
                    dc.CIK,
                    di.IssuerID
                FROM {database_name}.{schema_name}.DIM_COMPANY dc
                LEFT JOIN {database_name}.{curated_schema}.DIM_ISSUER di ON dc.CIK = di.CIK
                WHERE dc.CIK IS NOT NULL
            ),
            sec_data AS (
                SELECT 
                    smt.ADSH,
                    smt.CIK,
                    smt.COMPANY_NAME as SEC_COMPANY_NAME,
                    smt.VARIABLE_NAME,
                    smt.TAG,
                    smt.TAG_VERSION,
                    smt.PERIOD_START_DATE,
                    smt.PERIOD_END_DATE,
                    smt.FISCAL_PERIOD,
                    smt.FISCAL_YEAR,
                    smt.VALUE,
                    smt.UNIT,
                    smt.MEASURE,
                    smt.BUSINESS_SEGMENT,
                    smt.BUSINESS_SUBSEGMENT,
                    smt.GEO_NAME,
                    smt.CUSTOMER,
                    smt.FREQUENCY
                FROM {real_db}.{real_schema}.{sec_metrics_table} smt
                WHERE smt.CIK IS NOT NULL
                  AND smt.VALUE IS NOT NULL
                  AND smt.FISCAL_YEAR >= YEAR(CURRENT_DATE()) - 5
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY oc.COMPANY_ID, sd.FISCAL_YEAR, sd.FISCAL_PERIOD, sd.VARIABLE_NAME) as FINANCIAL_DATA_ID,
                oc.COMPANY_ID,
                oc.IssuerID,
                sd.ADSH,
                sd.CIK,
                sd.SEC_COMPANY_NAME,
                sd.VARIABLE_NAME,
                sd.TAG,
                sd.TAG_VERSION,
                sd.PERIOD_START_DATE,
                sd.PERIOD_END_DATE,
                sd.FISCAL_PERIOD,
                sd.FISCAL_YEAR,
                sd.VALUE,
                sd.UNIT,
                sd.MEASURE,
                sd.BUSINESS_SEGMENT,
                sd.BUSINESS_SUBSEGMENT,
                sd.GEO_NAME,
                sd.CUSTOMER,
                sd.FREQUENCY,
                '{sec_metrics_table}' as DATA_SOURCE,
                CURRENT_TIMESTAMP() as LOADED_AT
            FROM our_companies oc
            INNER JOIN sec_data sd ON oc.CIK = sd.CIK
            {limit_clause}
        """).collect()
        
        count = session.sql(f"""
            SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_FINANCIAL_DATA_SEC
        """).collect()[0]['CNT']
        
        company_count = session.sql(f"""
            SELECT COUNT(DISTINCT COMPANY_ID) as cnt FROM {database_name}.{schema_name}.FACT_FINANCIAL_DATA_SEC
        """).collect()[0]['CNT']
        
        config.log_detail(f" FACT_FINANCIAL_DATA_SEC: {count:,} records for {company_count} companies (REAL DATA)")
        return count > 0
        
    except Exception as e:
        config.log_error(f" Error building FACT_FINANCIAL_DATA_SEC: {e}")
        return False


def build_real_stock_prices(session: Session, test_mode: bool = False) -> bool:
    """
    Build FACT_STOCK_PRICES from real STOCK_PRICE_TIMESERIES data.
    
    This provides real daily stock prices for securities that match our DIM_SECURITY.
    """
    if not verify_real_data_access(session):
        return False
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    stock_prices_table = config.REAL_DATA_SOURCES['tables']['stock_prices']['table']
    
    config.log_detail("Building FACT_STOCK_PRICES from real Nasdaq data...")
    
    # Limit records in test mode
    limit_clause = "LIMIT 500000" if test_mode else ""
    
    try:
        # Create table with real stock prices linked to our securities via ticker
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_STOCK_PRICES AS
            WITH our_securities AS (
                -- Get securities from DIM_SECURITY with tickers
                SELECT DISTINCT
                    ds.SecurityID,
                    ds.Ticker,
                    ds.Description,
                    ds.IssuerID
                FROM {database_name}.{curated_schema}.DIM_SECURITY ds
                WHERE ds.Ticker IS NOT NULL
                  AND ds.AssetClass = 'Equity'
            ),
            price_data AS (
                SELECT 
                    spt.TICKER,
                    spt.ASSET_CLASS,
                    spt.PRIMARY_EXCHANGE_CODE,
                    spt.PRIMARY_EXCHANGE_NAME,
                    spt.DATE as PRICE_DATE,
                    spt.VARIABLE,
                    spt.VALUE
                FROM {real_db}.{real_schema}.{stock_prices_table} spt
                WHERE spt.DATE >= DATEADD(year, -2, CURRENT_DATE())
            ),
            pivoted_prices AS (
                -- Pivot the long format to wide format
                -- Variable names: pre-market_open, post-market_close, all-day_high, all-day_low, nasdaq_volume
                SELECT 
                    TICKER,
                    ASSET_CLASS,
                    PRIMARY_EXCHANGE_CODE,
                    PRIMARY_EXCHANGE_NAME,
                    PRICE_DATE,
                    MAX(CASE WHEN VARIABLE = 'pre-market_open' THEN VALUE END) as PRICE_OPEN,
                    MAX(CASE WHEN VARIABLE = 'post-market_close' THEN VALUE END) as PRICE_CLOSE,
                    MAX(CASE WHEN VARIABLE = 'all-day_high' THEN VALUE END) as PRICE_HIGH,
                    MAX(CASE WHEN VARIABLE = 'all-day_low' THEN VALUE END) as PRICE_LOW,
                    MAX(CASE WHEN VARIABLE = 'nasdaq_volume' THEN VALUE END) as VOLUME
                FROM price_data
                GROUP BY TICKER, ASSET_CLASS, PRIMARY_EXCHANGE_CODE, PRIMARY_EXCHANGE_NAME, PRICE_DATE
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY os.SecurityID, pp.PRICE_DATE) as PRICE_ID,
                os.SecurityID,
                os.IssuerID,
                pp.TICKER,
                pp.PRICE_DATE,
                pp.PRICE_OPEN,
                pp.PRICE_HIGH,
                pp.PRICE_LOW,
                pp.PRICE_CLOSE,
                pp.VOLUME::BIGINT as VOLUME,
                pp.ASSET_CLASS,
                pp.PRIMARY_EXCHANGE_CODE,
                pp.PRIMARY_EXCHANGE_NAME,
                '{stock_prices_table}' as DATA_SOURCE,
                CURRENT_TIMESTAMP() as LOADED_AT
            FROM our_securities os
            INNER JOIN pivoted_prices pp ON os.Ticker = pp.TICKER
            WHERE pp.PRICE_CLOSE IS NOT NULL
            {limit_clause}
        """).collect()
        
        count = session.sql(f"""
            SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_STOCK_PRICES
        """).collect()[0]['CNT']
        
        security_count = session.sql(f"""
            SELECT COUNT(DISTINCT SecurityID) as cnt FROM {database_name}.{schema_name}.FACT_STOCK_PRICES
        """).collect()[0]['CNT']
        
        config.log_detail(f" FACT_STOCK_PRICES: {count:,} records for {security_count} securities (REAL DATA)")
        return count > 0
        
    except Exception as e:
        config.log_error(f" Error building FACT_STOCK_PRICES: {e}")
        return False


def build_real_sec_filing_text(session: Session, test_mode: bool = False) -> bool:
    """
    Build FACT_SEC_FILING_TEXT from real SEC_REPORT_TEXT_ATTRIBUTES data.
    
    This provides real SEC filing text content (MD&A, Risk Factors, etc.) for companies
    that have CIK linkage in our DIM_ISSUER.
    """
    if not verify_real_data_access(session):
        return False
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    sec_filing_text_table = config.REAL_DATA_SOURCES['tables']['sec_filing_text']['table']
    
    config.log_detail("Building FACT_SEC_FILING_TEXT from real SEC filing data...")
    
    # Limit records in test mode
    limit_clause = "LIMIT 50000" if test_mode else ""
    
    try:
        # Create table with real SEC filing text linked to our companies via CIK
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_SEC_FILING_TEXT AS
            WITH our_companies AS (
                -- Get companies from DIM_COMPANY that have CIK
                SELECT 
                    dc.COMPANY_ID,
                    dc.COMPANY_NAME,
                    dc.CIK,
                    di.IssuerID
                FROM {database_name}.{schema_name}.DIM_COMPANY dc
                LEFT JOIN {database_name}.{curated_schema}.DIM_ISSUER di ON dc.CIK = di.CIK
                WHERE dc.CIK IS NOT NULL
            ),
            filing_text AS (
                SELECT 
                    srta.SEC_DOCUMENT_ID,
                    srta.CIK,
                    srta.ADSH,
                    srta.VARIABLE,
                    srta.VARIABLE_NAME,
                    srta.PERIOD_END_DATE,
                    srta.VALUE as FILING_TEXT,
                    LENGTH(srta.VALUE) as TEXT_LENGTH
                FROM {real_db}.{real_schema}.{sec_filing_text_table} srta
                WHERE srta.CIK IS NOT NULL
                  AND srta.VALUE IS NOT NULL
                  AND LENGTH(srta.VALUE) > 100  -- Only meaningful text
                  AND srta.PERIOD_END_DATE >= DATEADD(year, -3, CURRENT_DATE())
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY oc.COMPANY_ID, ft.PERIOD_END_DATE, ft.VARIABLE) as FILING_TEXT_ID,
                oc.COMPANY_ID,
                oc.IssuerID,
                ft.SEC_DOCUMENT_ID,
                ft.ADSH,
                ft.CIK,
                ft.VARIABLE,
                ft.VARIABLE_NAME,
                ft.PERIOD_END_DATE,
                ft.FILING_TEXT,
                ft.TEXT_LENGTH,
                '{sec_filing_text_table}' as DATA_SOURCE,
                CURRENT_TIMESTAMP() as LOADED_AT
            FROM our_companies oc
            INNER JOIN filing_text ft ON oc.CIK = ft.CIK
            {limit_clause}
        """).collect()
        
        count = session.sql(f"""
            SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_SEC_FILING_TEXT
        """).collect()[0]['CNT']
        
        company_count = session.sql(f"""
            SELECT COUNT(DISTINCT COMPANY_ID) as cnt FROM {database_name}.{schema_name}.FACT_SEC_FILING_TEXT
        """).collect()[0]['CNT']
        
        config.log_detail(f" FACT_SEC_FILING_TEXT: {count:,} records for {company_count} companies (REAL DATA)")
        return count > 0
        
    except Exception as e:
        config.log_error(f" Error building FACT_SEC_FILING_TEXT: {e}")
        return False


def build_real_segment_financials(session: Session, test_mode: bool = False) -> bool:
    """
    Build FACT_SEGMENT_FINANCIALS_SEC from real SEC segment data.
    
    This provides detailed segment-level financial data from SEC filings.
    """
    if not verify_real_data_access(session):
        return False
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    sec_metrics_table = config.REAL_DATA_SOURCES['tables']['sec_metrics']['table']
    
    config.log_detail("Building FACT_SEGMENT_FINANCIALS_SEC from real SEC segment data...")
    
    # Limit records in test mode
    limit_clause = "LIMIT 100000" if test_mode else ""
    
    try:
        # Create table with real segment-level financial data
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_SEGMENT_FINANCIALS_SEC AS
            WITH our_companies AS (
                SELECT 
                    dc.COMPANY_ID,
                    dc.COMPANY_NAME,
                    dc.CIK,
                    di.IssuerID
                FROM {database_name}.{schema_name}.DIM_COMPANY dc
                LEFT JOIN {database_name}.{curated_schema}.DIM_ISSUER di ON dc.CIK = di.CIK
                WHERE dc.CIK IS NOT NULL
            ),
            segment_data AS (
                SELECT 
                    smt.ADSH,
                    smt.CIK,
                    smt.COMPANY_NAME as SEC_COMPANY_NAME,
                    smt.VARIABLE_NAME,
                    smt.PERIOD_END_DATE,
                    smt.FISCAL_PERIOD,
                    smt.FISCAL_YEAR,
                    smt.VALUE,
                    smt.UNIT,
                    smt.BUSINESS_SEGMENT,
                    smt.BUSINESS_SUBSEGMENT,
                    smt.GEO_NAME,
                    smt.GEO_ID
                FROM {real_db}.{real_schema}.{sec_metrics_table} smt
                WHERE smt.CIK IS NOT NULL
                  AND smt.VALUE IS NOT NULL
                  AND smt.FISCAL_YEAR >= YEAR(CURRENT_DATE()) - 5
                  AND (smt.BUSINESS_SEGMENT IS NOT NULL OR smt.GEO_NAME IS NOT NULL)
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY oc.COMPANY_ID, sd.FISCAL_YEAR, sd.FISCAL_PERIOD, sd.BUSINESS_SEGMENT) as SEGMENT_DATA_ID,
                oc.COMPANY_ID,
                oc.IssuerID,
                sd.ADSH,
                sd.CIK,
                sd.SEC_COMPANY_NAME,
                sd.VARIABLE_NAME,
                sd.PERIOD_END_DATE,
                sd.FISCAL_PERIOD,
                sd.FISCAL_YEAR,
                sd.VALUE,
                sd.UNIT,
                sd.BUSINESS_SEGMENT,
                sd.BUSINESS_SUBSEGMENT,
                sd.GEO_NAME,
                sd.GEO_ID,
                '{sec_metrics_table}' as DATA_SOURCE,
                CURRENT_TIMESTAMP() as LOADED_AT
            FROM our_companies oc
            INNER JOIN segment_data sd ON oc.CIK = sd.CIK
            {limit_clause}
        """).collect()
        
        count = session.sql(f"""
            SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_SEGMENT_FINANCIALS_SEC
        """).collect()[0]['CNT']
        
        config.log_detail(f" FACT_SEGMENT_FINANCIALS_SEC: {count:,} segment records (REAL DATA)")
        return count > 0
        
    except Exception as e:
        config.log_error(f" Error building FACT_SEGMENT_FINANCIALS_SEC: {e}")
        return False


def build_real_sec_financials(session: Session, test_mode: bool = False) -> bool:
    """
    Build FACT_SEC_FINANCIALS from real SEC_CORPORATE_REPORT_ATTRIBUTES data.
    
    This provides comprehensive financial statement data (Income Statement, Balance Sheet,
    Cash Flow) with standardized metrics pivoted from XBRL tags.
    
    Source: SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.SEC_CORPORATE_REPORT_ATTRIBUTES
    - 569M records across 17,258 companies
    - Full financial statements with XBRL tags
    """
    if not verify_real_data_access(session):
        return False
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    sec_financials_table = config.REAL_DATA_SOURCES['tables']['sec_corporate_financials']['table']
    
    config.log_detail("Building FACT_SEC_FINANCIALS from real SEC XBRL data...")
    
    # Limit records in test mode
    limit_clause = "LIMIT 500000" if test_mode else ""
    
    try:
        # Create table with real comprehensive financial data
        # Pivot key XBRL tags into standardized columns
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_SEC_FINANCIALS AS
            WITH our_companies AS (
                -- Get companies from DIM_COMPANY that have CIK
                SELECT 
                    dc.COMPANY_ID,
                    dc.COMPANY_NAME,
                    dc.CIK,
                    di.IssuerID
                FROM {database_name}.{schema_name}.DIM_COMPANY dc
                LEFT JOIN {database_name}.{curated_schema}.DIM_ISSUER di ON dc.CIK = di.CIK
                WHERE dc.CIK IS NOT NULL
            ),
            -- Filter to relevant tags and recent data
            -- Note: Many companies have STATEMENT=None, so we filter by TAG names instead
            sec_data AS (
                SELECT 
                    scra.CIK,
                    scra.ADSH,
                    scra.STATEMENT,
                    scra.TAG,
                    scra.MEASURE_DESCRIPTION,
                    scra.PERIOD_END_DATE,
                    scra.PERIOD_START_DATE,
                    scra.COVERED_QTRS,
                    TRY_CAST(scra.VALUE AS FLOAT) as VALUE_NUM,
                    scra.UNIT
                FROM {real_db}.{real_schema}.{sec_financials_table} scra
                WHERE scra.CIK IS NOT NULL
                  AND scra.PERIOD_END_DATE >= DATEADD(year, -5, CURRENT_DATE())
                  AND scra.VALUE IS NOT NULL
                  AND TRY_CAST(scra.VALUE AS FLOAT) IS NOT NULL
                  -- Filter to key financial tags we're interested in
                  AND scra.TAG IN (
                      -- Income Statement tags
                      'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenue', 'SalesRevenueNet',
                      'NetIncomeLoss', 'ProfitLoss',
                      'GrossProfit',
                      'OperatingIncomeLoss', 'OperatingIncome',
                      'EarningsPerShareBasic', 'EarningsPerShareDiluted',
                      'ResearchAndDevelopmentExpense',
                      'InterestExpense',
                      'IncomeTaxExpenseBenefit',
                      -- Balance Sheet tags
                      'Assets',
                      'Liabilities',
                      'StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', 'Equity',
                      'CashAndCashEquivalentsAtCarryingValue',
                      'LongTermDebt', 'LongTermDebtNoncurrent',
                      'Goodwill',
                      'PropertyPlantAndEquipmentNet', 'PropertyPlantAndEquipment',
                      'AssetsCurrent',
                      'LiabilitiesCurrent',
                      'RetainedEarningsAccumulatedDeficit',
                      -- Cash Flow tags
                      'NetCashProvidedByUsedInOperatingActivities',
                      'NetCashProvidedByUsedInInvestingActivities',
                      'NetCashProvidedByUsedInFinancingActivities',
                      'PaymentsToAcquirePropertyPlantAndEquipment',
                      'DepreciationDepletionAndAmortization', 'DepreciationAndAmortization',
                      'ShareBasedCompensation'
                  )
            ),
            -- Aggregate by company/period/statement to get one row per filing period
            pivoted_data AS (
                SELECT 
                    sd.CIK,
                    sd.ADSH,
                    sd.PERIOD_END_DATE,
                    sd.PERIOD_START_DATE,
                    sd.COVERED_QTRS,
                    -- Derive fiscal period from covered quarters
                    CASE 
                        WHEN sd.COVERED_QTRS = 4 THEN 'FY'
                        WHEN sd.COVERED_QTRS = 1 THEN 'Q' || QUARTER(sd.PERIOD_END_DATE)
                        ELSE 'Q' || sd.COVERED_QTRS
                    END as FISCAL_PERIOD,
                    YEAR(sd.PERIOD_END_DATE) as FISCAL_YEAR,
                    -- Currency - use most common UNIT for this filing (normalized to uppercase)
                    MODE(UPPER(sd.UNIT)) as CURRENCY,
                    
                    -- Income Statement metrics (TAG-based, works with STATEMENT=None)
                    MAX(CASE WHEN sd.TAG IN ('Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenue', 'SalesRevenueNet') 
                             THEN sd.VALUE_NUM END) as REVENUE,
                    MAX(CASE WHEN sd.TAG IN ('NetIncomeLoss', 'ProfitLoss') 
                             THEN sd.VALUE_NUM END) as NET_INCOME,
                    MAX(CASE WHEN sd.TAG = 'GrossProfit' 
                             THEN sd.VALUE_NUM END) as GROSS_PROFIT,
                    MAX(CASE WHEN sd.TAG IN ('OperatingIncomeLoss', 'OperatingIncome') 
                             THEN sd.VALUE_NUM END) as OPERATING_INCOME,
                    MAX(CASE WHEN sd.TAG = 'EarningsPerShareBasic' 
                             THEN sd.VALUE_NUM END) as EPS_BASIC,
                    MAX(CASE WHEN sd.TAG = 'EarningsPerShareDiluted' 
                             THEN sd.VALUE_NUM END) as EPS_DILUTED,
                    MAX(CASE WHEN sd.TAG = 'ResearchAndDevelopmentExpense' 
                             THEN sd.VALUE_NUM END) as RD_EXPENSE,
                    MAX(CASE WHEN sd.TAG = 'InterestExpense' 
                             THEN sd.VALUE_NUM END) as INTEREST_EXPENSE,
                    MAX(CASE WHEN sd.TAG = 'IncomeTaxExpenseBenefit' 
                             THEN sd.VALUE_NUM END) as INCOME_TAX_EXPENSE,
                    
                    -- Balance Sheet metrics
                    MAX(CASE WHEN sd.TAG = 'Assets' 
                             THEN sd.VALUE_NUM END) as TOTAL_ASSETS,
                    MAX(CASE WHEN sd.TAG = 'Liabilities' 
                             THEN sd.VALUE_NUM END) as TOTAL_LIABILITIES,
                    MAX(CASE WHEN sd.TAG IN ('StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', 'Equity') 
                             THEN sd.VALUE_NUM END) as TOTAL_EQUITY,
                    MAX(CASE WHEN sd.TAG = 'CashAndCashEquivalentsAtCarryingValue' 
                             THEN sd.VALUE_NUM END) as CASH_AND_EQUIVALENTS,
                    MAX(CASE WHEN sd.TAG IN ('LongTermDebt', 'LongTermDebtNoncurrent') 
                             THEN sd.VALUE_NUM END) as LONG_TERM_DEBT,
                    MAX(CASE WHEN sd.TAG = 'Goodwill' 
                             THEN sd.VALUE_NUM END) as GOODWILL,
                    MAX(CASE WHEN sd.TAG IN ('PropertyPlantAndEquipmentNet', 'PropertyPlantAndEquipment') 
                             THEN sd.VALUE_NUM END) as PP_AND_E,
                    MAX(CASE WHEN sd.TAG = 'AssetsCurrent' 
                             THEN sd.VALUE_NUM END) as CURRENT_ASSETS,
                    MAX(CASE WHEN sd.TAG = 'LiabilitiesCurrent' 
                             THEN sd.VALUE_NUM END) as CURRENT_LIABILITIES,
                    MAX(CASE WHEN sd.TAG = 'RetainedEarningsAccumulatedDeficit' 
                             THEN sd.VALUE_NUM END) as RETAINED_EARNINGS,
                    
                    -- Cash Flow metrics
                    MAX(CASE WHEN sd.TAG = 'NetCashProvidedByUsedInOperatingActivities' 
                             THEN sd.VALUE_NUM END) as OPERATING_CASH_FLOW,
                    MAX(CASE WHEN sd.TAG = 'NetCashProvidedByUsedInInvestingActivities' 
                             THEN sd.VALUE_NUM END) as INVESTING_CASH_FLOW,
                    MAX(CASE WHEN sd.TAG = 'NetCashProvidedByUsedInFinancingActivities' 
                             THEN sd.VALUE_NUM END) as FINANCING_CASH_FLOW,
                    MAX(CASE WHEN sd.TAG = 'PaymentsToAcquirePropertyPlantAndEquipment' 
                             THEN sd.VALUE_NUM END) as CAPEX,
                    MAX(CASE WHEN sd.TAG IN ('DepreciationDepletionAndAmortization', 'DepreciationAndAmortization') 
                             THEN sd.VALUE_NUM END) as DEPRECIATION_AMORTIZATION,
                    MAX(CASE WHEN sd.TAG = 'ShareBasedCompensation' 
                             THEN sd.VALUE_NUM END) as STOCK_BASED_COMP
                    
                FROM sec_data sd
                GROUP BY sd.CIK, sd.ADSH, sd.PERIOD_END_DATE, sd.PERIOD_START_DATE, sd.COVERED_QTRS
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY oc.COMPANY_ID, pd.FISCAL_YEAR DESC, pd.FISCAL_PERIOD) as FINANCIAL_ID,
                oc.COMPANY_ID,
                oc.IssuerID,
                oc.COMPANY_NAME,
                pd.CIK,
                pd.ADSH,
                pd.PERIOD_END_DATE,
                pd.PERIOD_START_DATE,
                pd.FISCAL_PERIOD,
                pd.FISCAL_YEAR,
                pd.COVERED_QTRS,
                pd.CURRENCY,
                
                -- Income Statement
                pd.REVENUE,
                pd.NET_INCOME,
                pd.GROSS_PROFIT,
                pd.OPERATING_INCOME,
                pd.EPS_BASIC,
                pd.EPS_DILUTED,
                pd.RD_EXPENSE,
                pd.INTEREST_EXPENSE,
                pd.INCOME_TAX_EXPENSE,
                
                -- Balance Sheet
                pd.TOTAL_ASSETS,
                pd.TOTAL_LIABILITIES,
                pd.TOTAL_EQUITY,
                pd.CASH_AND_EQUIVALENTS,
                pd.LONG_TERM_DEBT,
                pd.GOODWILL,
                pd.PP_AND_E,
                pd.CURRENT_ASSETS,
                pd.CURRENT_LIABILITIES,
                pd.RETAINED_EARNINGS,
                
                -- Cash Flow
                pd.OPERATING_CASH_FLOW,
                pd.INVESTING_CASH_FLOW,
                pd.FINANCING_CASH_FLOW,
                pd.CAPEX,
                pd.DEPRECIATION_AMORTIZATION,
                pd.STOCK_BASED_COMP,
                
                -- Calculated metrics
                COALESCE(pd.OPERATING_CASH_FLOW, 0) - ABS(COALESCE(pd.CAPEX, 0)) as FREE_CASH_FLOW,
                CASE WHEN pd.REVENUE > 0 THEN pd.GROSS_PROFIT / pd.REVENUE * 100 END as GROSS_MARGIN_PCT,
                CASE WHEN pd.REVENUE > 0 THEN pd.OPERATING_INCOME / pd.REVENUE * 100 END as OPERATING_MARGIN_PCT,
                CASE WHEN pd.REVENUE > 0 THEN pd.NET_INCOME / pd.REVENUE * 100 END as NET_MARGIN_PCT,
                CASE WHEN pd.TOTAL_EQUITY > 0 THEN pd.NET_INCOME / pd.TOTAL_EQUITY * 100 END as ROE_PCT,
                CASE WHEN pd.TOTAL_ASSETS > 0 THEN pd.NET_INCOME / pd.TOTAL_ASSETS * 100 END as ROA_PCT,
                CASE WHEN pd.TOTAL_EQUITY > 0 THEN pd.LONG_TERM_DEBT / pd.TOTAL_EQUITY END as DEBT_TO_EQUITY,
                CASE WHEN pd.CURRENT_LIABILITIES > 0 THEN pd.CURRENT_ASSETS / pd.CURRENT_LIABILITIES END as CURRENT_RATIO,
                
                -- Metadata
                '{sec_financials_table}' as DATA_SOURCE,
                CURRENT_TIMESTAMP() as LOADED_AT
            FROM our_companies oc
            INNER JOIN pivoted_data pd ON oc.CIK = pd.CIK
            WHERE pd.REVENUE IS NOT NULL OR pd.TOTAL_ASSETS IS NOT NULL OR pd.OPERATING_CASH_FLOW IS NOT NULL
            {limit_clause}
        """).collect()
        
        count = session.sql(f"""
            SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_SEC_FINANCIALS
        """).collect()[0]['CNT']
        
        company_count = session.sql(f"""
            SELECT COUNT(DISTINCT COMPANY_ID) as cnt FROM {database_name}.{schema_name}.FACT_SEC_FINANCIALS
        """).collect()[0]['CNT']
        
        period_count = session.sql(f"""
            SELECT COUNT(DISTINCT CONCAT(CIK, '-', FISCAL_YEAR, '-', FISCAL_PERIOD)) as cnt 
            FROM {database_name}.{schema_name}.FACT_SEC_FINANCIALS
        """).collect()[0]['CNT']
        
        config.log_detail(f" FACT_SEC_FINANCIALS: {count:,} records for {company_count} companies, {period_count} fiscal periods (REAL DATA)")
        return count > 0
        
    except Exception as e:
        config.log_error(f" Error building FACT_SEC_FINANCIALS: {e}")
        return False


# =============================================================================
# SYNTHETIC DATA GENERATION FUNCTIONS
# =============================================================================

def build_reference_tables(session: Session, test_mode: bool = False):
    """Build reference/lookup tables."""
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    # REF_DATA_ITEM - Financial data item definitions
    config.log_detail("Building REF_DATA_ITEM...")
    
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
    config.log_detail(f" REF_DATA_ITEM: {len(data_items)} items")
    
    # REF_EXCHANGE - Exchange reference
    config.log_detail("Building REF_EXCHANGE...")
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
    config.log_detail(f" REF_EXCHANGE: {len(exchanges)} exchanges")
    
    # REF_CURRENCY
    config.log_detail("Building REF_CURRENCY...")
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
    config.log_detail(f" REF_CURRENCY: {len(currencies)} currencies")


def build_company_master(session: Session, test_mode: bool = False):
    """Build company master data from existing DIM_ISSUER."""
    
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    config.log_detail("Building DIM_COMPANY from DIM_ISSUER...")
    
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
    config.log_detail(f" DIM_COMPANY: {count} companies")
    
    # DIM_BROKER - Broker firms
    config.log_detail("Building DIM_BROKER...")
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
    config.log_detail(f" DIM_BROKER: {len(brokers)} brokers")


def build_financial_periods(session: Session, test_mode: bool = False):
    """Build financial period reference data."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    config.log_detail("Building FACT_FINANCIAL_PERIOD...")
    
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
    config.log_detail(f" FACT_FINANCIAL_PERIOD: {count} periods")


def build_financial_data(session: Session, test_mode: bool = False):
    """Build financial statement data with realistic values."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    config.log_detail("Building FACT_FINANCIAL_DATA...")
    
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
        
        UNION ALL
        
        -- TAM (Total Addressable Market) - Investment Memo Metric
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) + 6000000,
            PERIOD_ID,
            COMPANY_ID,
            1011 as DATA_ITEM_ID,  -- TAM
            ROUND(REVENUE * (15 + MOD(ABS(HASH(COMPANY_ID * 1003)), 20)), 0),  -- TAM is 15-35x revenue
            'USD',
            CURRENT_TIMESTAMP()
        FROM calculated_financials
        
        UNION ALL
        
        -- Customer Count - Investment Memo Metric
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) + 7000000,
            PERIOD_ID,
            COMPANY_ID,
            1012 as DATA_ITEM_ID,  -- CUSTOMER_COUNT
            ROUND(POWER(10, 2 + MOD(ABS(HASH(COMPANY_ID * 1004)), 4)) * (1 + FISCAL_QUARTER * 0.02), 0),  -- 100 to 100K customers with growth
            NULL,  -- No currency for count
            CURRENT_TIMESTAMP()
        FROM calculated_financials
        
        UNION ALL
        
        -- NRR (Net Revenue Retention %) - Investment Memo Metric
        SELECT 
            ROW_NUMBER() OVER (ORDER BY PERIOD_ID, COMPANY_ID) + 8000000,
            PERIOD_ID,
            COMPANY_ID,
            4009 as DATA_ITEM_ID,  -- NRR
            100 + MOD(ABS(HASH(PERIOD_ID * 1005 + COMPANY_ID)), 35),  -- NRR 100-135%
            'PCT',
            CURRENT_TIMESTAMP()
        FROM calculated_financials
    """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_FINANCIAL_DATA").collect()[0]['CNT']
    config.log_detail(f" FACT_FINANCIAL_DATA: {count} data points")


def build_broker_analyst_data(session: Session, test_mode: bool = False):
    """Build broker and analyst coverage data."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    config.log_detail("Building DIM_ANALYST and FACT_ANALYST_COVERAGE...")
    
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
    config.log_detail(f" DIM_ANALYST: {analyst_count} analysts")
    
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
    config.log_detail(f" FACT_ANALYST_COVERAGE: {coverage_count} coverage records")


def build_estimate_data(session: Session, test_mode: bool = False):
    """Build analyst estimates and consensus data."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    config.log_detail("Building FACT_ESTIMATE_CONSENSUS...")
    
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
            WHERE fd.DATA_ITEM_ID IN (1001, 1005, 1008, 1011, 1012, 4009)  -- Revenue, Net Income, EBITDA, TAM, Customer Count, NRR
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
    config.log_detail(f" FACT_ESTIMATE_CONSENSUS: {consensus_count} consensus records")
    
    # Generate price targets and ratings
    config.log_detail("Building FACT_ESTIMATE_DATA (price targets & ratings)...")
    
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
    config.log_detail(f" FACT_ESTIMATE_DATA: {estimate_count} estimate records")


def build_filing_reference_tables(session: Session, test_mode: bool = False):
    """Build filing reference tables following S&P Capital IQ pattern."""
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    config.log_detail("Building Filing Reference Tables...")
    
    # REF_FILING_TYPE - Filing type definitions
    config.log_detail("Building REF_FILING_TYPE...")
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
    config.log_detail(f" REF_FILING_TYPE: {len(filing_types)} types")
    
    # REF_FILING_SOURCE - Filing source definitions
    config.log_detail("Building REF_FILING_SOURCE...")
    filing_sources = []
    for fs in config.FILING_SOURCES:
        filing_sources.append({
            'FILING_SOURCE_ID': fs['id'],
            'FILING_SOURCE': fs['source'],
            'FILING_SOURCE_DESC': fs['description']
        })
    
    df = session.create_dataframe(filing_sources)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_FILING_SOURCE")
    config.log_detail(f" REF_FILING_SOURCE: {len(filing_sources)} sources")
    
    # REF_FILING_LANGUAGE - Language definitions
    config.log_detail("Building REF_FILING_LANGUAGE...")
    filing_languages = []
    for fl in config.FILING_LANGUAGES:
        filing_languages.append({
            'FILING_LANGUAGE_ID': fl['id'],
            'FILING_LANGUAGE': fl['language'],
            'LANGUAGE_CODE': fl['code']
        })
    
    df = session.create_dataframe(filing_languages)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_FILING_LANGUAGE")
    config.log_detail(f" REF_FILING_LANGUAGE: {len(filing_languages)} languages")
    
    # REF_FILING_INSTITUTION_REL_TYPE - Institution relationship types
    config.log_detail("Building REF_FILING_INSTITUTION_REL_TYPE...")
    rel_types = []
    for rt in config.FILING_INSTITUTION_REL_TYPES:
        rel_types.append({
            'REL_TYPE_ID': rt['id'],
            'REL_TYPE': rt['type'],
            'REL_TYPE_DESC': rt['description']
        })
    
    df = session.create_dataframe(rel_types)
    df.write.mode("overwrite").save_as_table(f"{database_name}.{schema_name}.REF_FILING_INSTITUTION_REL_TYPE")
    config.log_detail(f" REF_FILING_INSTITUTION_REL_TYPE: {len(rel_types)} types")


def build_filing_data(session: Session, test_mode: bool = False):
    """Build filing data tables following S&P Capital IQ pattern."""
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    
    years_of_history = config.MARKET_DATA['generation']['years_of_history']
    if test_mode:
        years_of_history = 2
    
    config.log_detail("Building Filing Data Tables...")
    
    # FACT_FILING_REF - Master filing reference (one row per filing)
    config.log_detail("Building FACT_FILING_REF...")
    
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
    config.log_detail(f" FACT_FILING_REF: {filing_ref_count} filings")
    
    # FACT_FILING_INSTITUTION_REL - Company-to-filing relationships
    config.log_detail("Building FACT_FILING_INSTITUTION_REL...")
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_FILING_INSTITUTION_REL AS
        SELECT 
            fr.FILE_VERSION_ID,
            fr.COMPANY_ID as INSTITUTION_ID,
            1 as REL_TYPE_ID  -- FILER
        FROM {database_name}.{schema_name}.FACT_FILING_REF fr
    """).collect()
    
    rel_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_FILING_INSTITUTION_REL").collect()[0]['CNT']
    config.log_detail(f" FACT_FILING_INSTITUTION_REL: {rel_count} relationships")
    
    # FACT_FILING_DATA - Textual filing content (SEC filings with parsed sections)
    config.log_detail("Building FACT_FILING_DATA...")
    
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
    config.log_detail(f" FACT_FILING_DATA: {filing_data_count} sections")
    
    # Create empty tables for non-SEC and ESG filings (for future expansion)
    config.log_detail("Building FACT_FILING_DATA_NON_SEC (placeholder)...")
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
    config.log_detail(f" FACT_FILING_DATA_NON_SEC: 0 sections (placeholder)")
    
    config.log_detail("Building FACT_FILING_DATA_ESG (placeholder)...")
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
    config.log_detail(f" FACT_FILING_DATA_ESG: 0 sections (placeholder)")


if __name__ == "__main__":
    # For testing - create session and run
    from snowflake.snowpark import Session
    
    session = Session.builder.config("connection_name", config.DEFAULT_CONNECTION_NAME).create()
    
    try:
        build_all(session, test_mode=True)
    finally:
        session.close()

