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
Simulated Asset Management (SAM) Demo - Market Data Generation

This module generates market data for the MARKET_DATA schema using
real data from SNOWFLAKE_PUBLIC_DATA_FREE. Includes:
- Company and security master data
- Real SEC financial statements (10-K, 10-Q)
- Real stock prices from Nasdaq
- Analyst estimates and consensus data (derived from real SEC data)

Usage:
    Called by main.py as part of the build process.
    
    IMPORTANT: This module requires access to SNOWFLAKE_PUBLIC_DATA_FREE.
    The build will fail if this data source is not available.
"""

from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit, when, concat, uniform, dateadd, current_timestamp
from datetime import datetime, timedelta
from typing import List, Optional
import random

import config
from logging_utils import log_step, log_substep, log_detail, log_warning, log_error, log_success, log_phase, log_phase_complete
from db_helpers import get_max_price_date, reset_max_price_date, verify_table_access


def build_price_anchor(session: Session, test_mode: bool = False):
    """
    Build FACT_STOCK_PRICES as the date anchor for all data generation.
    
    This must be called BEFORE other fact tables because:
    - get_max_price_date() uses FACT_STOCK_PRICES to determine date bounds
    - All synthetic data generation uses max_price_date as reference
    
    Returns the max_price_date that will be used as anchor.
    """
    if not config.MARKET_DATA['enabled']:
        raise RuntimeError("MARKET_DATA schema disabled in config - cannot build price anchor")
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    # Schema should already exist from setup.sql - skip creation in stored procedure context
    try:
        session.sql(f"CREATE SCHEMA IF NOT EXISTS {database_name}.{schema_name}").collect()
    except Exception:
        pass  # Schema already exists or we don't have permissions (running in stored procedure)
    
    # Reset cached max_price_date before rebuilding
    reset_max_price_date()
    
    log_substep("Building price anchor (FACT_STOCK_PRICES)")
    build_real_stock_prices(session, test_mode)
    
    # Get and log the anchor date
    max_price_date = get_max_price_date(session)
    if max_price_date:
        log_success(f"Price anchor date: {max_price_date}")
    else:
        log_error("Failed to establish price anchor date")
    
    return max_price_date


def build_all(session: Session, test_mode: bool = False):
    """Build all MARKET_DATA schema tables using real SEC data.
    
    IMPORTANT: This function requires access to SNOWFLAKE_PUBLIC_DATA_FREE.
    The build will fail if real data sources are not available.
    
    Note: build_price_anchor() should be called separately BEFORE this
    if you need to anchor other tables to the max_price_date.
    """
    
    if not config.MARKET_DATA['enabled']:
        raise RuntimeError("MARKET_DATA schema disabled in config - cannot build market data tables")
    
    log_phase("Market Data (Real SEC Data)")
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    # Schema should already exist from setup.sql - skip creation in stored procedure context
    try:
        session.sql(f"CREATE SCHEMA IF NOT EXISTS {database_name}.{schema_name}").collect()
    except Exception:
        pass  # Schema already exists or we don't have permissions (running in stored procedure)
    
    # Build tables in dependency order
    log_substep("Reference tables (brokers)")
    build_reference_tables(session, test_mode)
    
    
    # Only build stock prices if not already built (by build_price_anchor)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        log_substep("Real stock prices")
        build_real_stock_prices(session, test_mode)
    else:
        log_detail(f"  FACT_STOCK_PRICES already exists (anchor: {max_price_date})")
    
    log_substep("Real SEC filing text")
    build_real_sec_filing_text(session, test_mode)
    
    log_substep("Real SEC financials (comprehensive with TAM/NRR)")
    build_real_sec_financials(session, test_mode)
    
    log_substep("Real SEC segments (geographic and business)")
    build_sec_segments(session, test_mode)
    
    log_substep("Broker analyst data")
    build_broker_analyst_data(session, test_mode)
    
    log_substep("Estimate data (from real SEC actuals)")
    build_estimate_data(session, test_mode)
    
    log_phase_complete("Market data complete")


# =============================================================================
# REAL DATA INTEGRATION FUNCTIONS
# =============================================================================

def verify_real_data_access(session: Session) -> None:
    """
    Verify access to the configured real data share.
    
    Uses REAL_DATA_SOURCES['access_probe_table_key'] to determine which table
    to probe. This allows the demo to work with different public data shares.
    
    Raises RuntimeError if access is not available.
    """
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    # Get probe table from config (key into REAL_DATA_SOURCES['tables']) - required fields
    probe_key = config.REAL_DATA_SOURCES['access_probe_table_key']
    probe_table_entry = config.REAL_DATA_SOURCES['tables'][probe_key]
    probe_table = probe_table_entry['table']
    
    success, error_msg = verify_table_access(session, real_db, real_schema, probe_table)
    if not success:
        raise RuntimeError(
            f"Cannot access real data source {real_db}.{real_schema}.{probe_table}: {error_msg}. "
            "This demo requires access to SNOWFLAKE_PUBLIC_DATA_FREE. "
            "Please add this database from Snowflake Marketplace and retry."
        )


def build_real_stock_prices(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_STOCK_PRICES from real STOCK_PRICE_TIMESERIES data.
    
    This provides real daily stock prices for securities that match our DIM_SECURITY.
    
    Raises RuntimeError if real data source is not accessible.
    """
    verify_real_data_access(session)  # Raises on failure
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    stock_prices_table = config.REAL_DATA_SOURCES['tables']['stock_prices']['table']
    
    log_detail("Building FACT_STOCK_PRICES from real Nasdaq data...")
    
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
                WHERE spt.DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
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
            -- Note: TICKER available via SecurityID -> DIM_SECURITY.Ticker join
            SELECT 
                ROW_NUMBER() OVER (ORDER BY os.SecurityID, pp.PRICE_DATE) as PRICE_ID,
                os.SecurityID,
                os.IssuerID,
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
        
        log_detail(f" FACT_STOCK_PRICES: {count:,} records for {security_count} securities (REAL DATA)")
        
        if count == 0:
            raise RuntimeError(
                "FACT_STOCK_PRICES has no records - no matching securities found in real data source. "
                "Check that DIM_SECURITY tickers match STOCK_PRICE_TIMESERIES."
            )
        
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error building FACT_STOCK_PRICES: {e}")


def build_real_sec_filing_text(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_SEC_FILING_TEXT from real SEC_REPORT_TEXT_ATTRIBUTES data.
    
    This provides real SEC filing text content (MD&A, Risk Factors, etc.) for companies
    that have CIK linkage in our DIM_ISSUER. Includes enhanced metadata for searchability:
    - COMPANY_NAME, TICKER for filtering by company
    - FILING_TYPE (10-K, 10-Q, 8-K) derived from VARIABLE_NAME patterns
    - FISCAL_YEAR, FISCAL_QUARTER for time-based filtering
    - DOCUMENT_TITLE for human-readable search results
    
    Raises RuntimeError if real data source is not accessible.
    """
    verify_real_data_access(session)  # Raises on failure
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    sec_filing_text_table = config.REAL_DATA_SOURCES['tables']['sec_filing_text']['table']
    
    log_detail("Building FACT_SEC_FILING_TEXT from real SEC filing data...")
    
    # Limit records in test mode
    limit_clause = "LIMIT 50000" if test_mode else ""
    
    try:
        # Create table with real SEC filing text linked to our companies via CIK
        # Enhanced with FILING_TYPE, FISCAL_YEAR, FISCAL_QUARTER, DOCUMENT_TITLE
        # Note: COMPANY_NAME, TICKER available via IssuerID -> DIM_ISSUER join
        # Uses DIM_ISSUER directly (DIM_COMPANY has been eliminated)
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_SEC_FILING_TEXT AS
            WITH our_companies AS (
                -- Get companies from DIM_ISSUER with CIK
                -- Note: COMPANY_NAME, TICKER available via IssuerID -> DIM_ISSUER join
                SELECT 
                    di.IssuerID,
                    di.CIK,
                    di.LegalName,
                    di.PrimaryTicker
                FROM {database_name}.{curated_schema}.DIM_ISSUER di
                WHERE di.CIK IS NOT NULL
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
                    LENGTH(srta.VALUE) as TEXT_LENGTH,
                    -- Derive filing type from VARIABLE_NAME patterns
                    CASE 
                        WHEN srta.VARIABLE_NAME ILIKE '%10-K%' OR srta.VARIABLE_NAME ILIKE '%10K%' THEN '10-K'
                        WHEN srta.VARIABLE_NAME ILIKE '%10-Q%' OR srta.VARIABLE_NAME ILIKE '%10Q%' THEN '10-Q'
                        WHEN srta.VARIABLE_NAME ILIKE '%8-K%' OR srta.VARIABLE_NAME ILIKE '%8K%' THEN '8-K'
                        WHEN srta.VARIABLE_NAME ILIKE '%DEF 14A%' OR srta.VARIABLE_NAME ILIKE '%proxy%' THEN 'DEF 14A'
                        ELSE 'SEC Filing'
                    END as FILING_TYPE,
                    -- Extract fiscal year and quarter
                    YEAR(srta.PERIOD_END_DATE) as FISCAL_YEAR,
                    CASE 
                        WHEN MONTH(srta.PERIOD_END_DATE) IN (1, 2, 3) THEN 'Q1'
                        WHEN MONTH(srta.PERIOD_END_DATE) IN (4, 5, 6) THEN 'Q2'
                        WHEN MONTH(srta.PERIOD_END_DATE) IN (7, 8, 9) THEN 'Q3'
                        WHEN MONTH(srta.PERIOD_END_DATE) IN (10, 11, 12) THEN 'Q4'
                        ELSE 'FY'
                    END as FISCAL_QUARTER
                FROM {real_db}.{real_schema}.{sec_filing_text_table} srta
                WHERE srta.CIK IS NOT NULL
                  AND srta.VALUE IS NOT NULL
                  AND LENGTH(srta.VALUE) > 100  -- Only meaningful text
                  AND srta.PERIOD_END_DATE >= DATEADD(year, -3, CURRENT_DATE())
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY oc.IssuerID, ft.PERIOD_END_DATE, ft.VARIABLE) as FILING_TEXT_ID,
                oc.IssuerID,
                ft.FILING_TYPE,
                ft.FISCAL_YEAR,
                ft.FISCAL_QUARTER,
                -- Human-readable document title (constructed from dimension data at build time)
                CONCAT(
                    oc.LegalName, 
                    CASE WHEN oc.PrimaryTicker IS NOT NULL THEN CONCAT(' (', oc.PrimaryTicker, ')') ELSE '' END,
                    ' - ', ft.FILING_TYPE, ' ', ft.FISCAL_YEAR, ' ', ft.FISCAL_QUARTER,
                    ' - ', ft.VARIABLE_NAME
                ) as DOCUMENT_TITLE,
                -- Original columns
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
        
        issuer_count = session.sql(f"""
            SELECT COUNT(DISTINCT IssuerID) as cnt FROM {database_name}.{schema_name}.FACT_SEC_FILING_TEXT
        """).collect()[0]['CNT']
        
        log_detail(f" FACT_SEC_FILING_TEXT: {count:,} records for {issuer_count} issuers (REAL DATA)")
        
        if count == 0:
            raise RuntimeError(
                "FACT_SEC_FILING_TEXT has no records - no matching issuers with CIK found in real data source. "
                "Check that DIM_ISSUER CIK values match SEC filing data."
            )
        
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error building FACT_SEC_FILING_TEXT: {e}")


def build_real_sec_financials(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_SEC_FINANCIALS from real SEC_CORPORATE_REPORT_ATTRIBUTES data.
    
    This provides comprehensive financial statement data (Income Statement, Balance Sheet,
    Cash Flow) with standardized metrics pivoted from XBRL tags.
    
    Source: SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.SEC_CORPORATE_REPORT_ATTRIBUTES
    - 569M records across 17,258 companies
    - Full financial statements with XBRL tags
    
    Raises RuntimeError if real data source is not accessible.
    """
    verify_real_data_access(session)  # Raises on failure
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    sec_financials_table = config.REAL_DATA_SOURCES['tables']['sec_corporate_financials']['table']
    
    log_detail("Building FACT_SEC_FINANCIALS from real SEC XBRL data...")
    
    # Limit records in test mode
    limit_clause = "LIMIT 500000" if test_mode else ""
    
    try:
        # Create table with real comprehensive financial data
        # Pivot key XBRL tags into standardized columns
        # Uses DIM_ISSUER directly (DIM_COMPANY has been eliminated)
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_SEC_FINANCIALS AS
            WITH our_companies AS (
                -- Get companies from DIM_ISSUER that have CIK
                -- Note: SIC_DESCRIPTION used for TAM/customer count calculations, not persisted
                SELECT 
                    di.IssuerID,
                    di.CIK,
                    di.SIC_DESCRIPTION as INDUSTRY_DESCRIPTION
                FROM {database_name}.{curated_schema}.DIM_ISSUER di
                WHERE di.CIK IS NOT NULL
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
            ),
            -- Calculate YoY revenue growth for NRR estimation
            with_growth AS (
                SELECT 
                    pd.*,
                    LAG(pd.REVENUE) OVER (PARTITION BY pd.CIK ORDER BY pd.FISCAL_YEAR, pd.FISCAL_PERIOD) as PREV_REVENUE,
                    CASE 
                        WHEN LAG(pd.REVENUE) OVER (PARTITION BY pd.CIK ORDER BY pd.FISCAL_YEAR, pd.FISCAL_PERIOD) > 0 
                        THEN (pd.REVENUE - LAG(pd.REVENUE) OVER (PARTITION BY pd.CIK ORDER BY pd.FISCAL_YEAR, pd.FISCAL_PERIOD)) 
                             / LAG(pd.REVENUE) OVER (PARTITION BY pd.CIK ORDER BY pd.FISCAL_YEAR, pd.FISCAL_PERIOD) * 100
                        ELSE NULL 
                    END as REVENUE_GROWTH_PCT
                FROM pivoted_data pd
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY oc.IssuerID, wg.FISCAL_YEAR DESC, wg.FISCAL_PERIOD) as FINANCIAL_ID,
                oc.IssuerID,
                wg.CIK,
                wg.ADSH,
                wg.PERIOD_END_DATE,
                wg.PERIOD_START_DATE,
                wg.FISCAL_PERIOD,
                wg.FISCAL_YEAR,
                wg.COVERED_QTRS,
                wg.CURRENCY,
                
                -- Income Statement
                wg.REVENUE,
                wg.NET_INCOME,
                wg.GROSS_PROFIT,
                wg.OPERATING_INCOME,
                wg.EPS_BASIC,
                wg.EPS_DILUTED,
                wg.RD_EXPENSE,
                wg.INTEREST_EXPENSE,
                wg.INCOME_TAX_EXPENSE,
                
                -- Balance Sheet
                wg.TOTAL_ASSETS,
                wg.TOTAL_LIABILITIES,
                wg.TOTAL_EQUITY,
                wg.CASH_AND_EQUIVALENTS,
                wg.LONG_TERM_DEBT,
                wg.GOODWILL,
                wg.PP_AND_E,
                wg.CURRENT_ASSETS,
                wg.CURRENT_LIABILITIES,
                wg.RETAINED_EARNINGS,
                
                -- Cash Flow
                wg.OPERATING_CASH_FLOW,
                wg.INVESTING_CASH_FLOW,
                wg.FINANCING_CASH_FLOW,
                wg.CAPEX,
                wg.DEPRECIATION_AMORTIZATION,
                wg.STOCK_BASED_COMP,
                
                -- Calculated metrics (existing)
                COALESCE(wg.OPERATING_CASH_FLOW, 0) - ABS(COALESCE(wg.CAPEX, 0)) as FREE_CASH_FLOW,
                CASE WHEN wg.REVENUE > 0 THEN wg.GROSS_PROFIT / wg.REVENUE * 100 END as GROSS_MARGIN_PCT,
                CASE WHEN wg.REVENUE > 0 THEN wg.OPERATING_INCOME / wg.REVENUE * 100 END as OPERATING_MARGIN_PCT,
                CASE WHEN wg.REVENUE > 0 THEN wg.NET_INCOME / wg.REVENUE * 100 END as NET_MARGIN_PCT,
                CASE WHEN wg.TOTAL_EQUITY > 0 THEN wg.NET_INCOME / wg.TOTAL_EQUITY * 100 END as ROE_PCT,
                CASE WHEN wg.TOTAL_ASSETS > 0 THEN wg.NET_INCOME / wg.TOTAL_ASSETS * 100 END as ROA_PCT,
                CASE WHEN wg.TOTAL_EQUITY > 0 THEN wg.LONG_TERM_DEBT / wg.TOTAL_EQUITY END as DEBT_TO_EQUITY,
                CASE WHEN wg.CURRENT_LIABILITIES > 0 THEN wg.CURRENT_ASSETS / wg.CURRENT_LIABILITIES END as CURRENT_RATIO,
                
                -- Revenue growth
                wg.REVENUE_GROWTH_PCT,
                
                -- EBITDA (Operating Income + Depreciation & Amortization)
                COALESCE(wg.OPERATING_INCOME, 0) + COALESCE(wg.DEPRECIATION_AMORTIZATION, 0) as EBITDA,
                
                -- Investment Memo Metrics (heuristically calculated)
                -- TAM: Revenue x Industry Multiplier (15-35x based on industry)
                -- Uses INDUSTRY_DESCRIPTION from our_companies (derived from DIM_ISSUER.SIC_DESCRIPTION)
                CASE 
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%software%' THEN wg.REVENUE * 25
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%semiconductor%' THEN wg.REVENUE * 20
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%technology%' OR oc.INDUSTRY_DESCRIPTION ILIKE '%electronic%' THEN wg.REVENUE * 18
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%pharma%' OR oc.INDUSTRY_DESCRIPTION ILIKE '%biotech%' THEN wg.REVENUE * 22
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%retail%' OR oc.INDUSTRY_DESCRIPTION ILIKE '%consumer%' THEN wg.REVENUE * 12
                    ELSE wg.REVENUE * 15
                END as TAM,
                
                -- Estimated Customer Count: Revenue / ARPC (Average Revenue Per Customer varies by industry)
                CASE 
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%software%' OR oc.INDUSTRY_DESCRIPTION ILIKE '%cloud%' THEN wg.REVENUE / 100000
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%enterprise%' THEN wg.REVENUE / 250000
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%retail%' OR oc.INDUSTRY_DESCRIPTION ILIKE '%consumer%' THEN wg.REVENUE / 500
                    WHEN oc.INDUSTRY_DESCRIPTION ILIKE '%pharma%' OR oc.INDUSTRY_DESCRIPTION ILIKE '%biotech%' THEN wg.REVENUE / 1000000
                    ELSE wg.REVENUE / 50000
                END as ESTIMATED_CUSTOMER_COUNT,
                
                -- Estimated NRR: 100 + Revenue Growth, capped at 90-140%
                LEAST(140, GREATEST(90, 100 + COALESCE(wg.REVENUE_GROWTH_PCT, 10))) as ESTIMATED_NRR_PCT,
                
                -- Metadata
                '{sec_financials_table}' as DATA_SOURCE,
                CURRENT_TIMESTAMP() as LOADED_AT
            FROM our_companies oc
            INNER JOIN with_growth wg ON oc.CIK = wg.CIK
            WHERE wg.REVENUE IS NOT NULL OR wg.TOTAL_ASSETS IS NOT NULL OR wg.OPERATING_CASH_FLOW IS NOT NULL
            {limit_clause}
        """).collect()
        
        count = session.sql(f"""
            SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_SEC_FINANCIALS
        """).collect()[0]['CNT']
        
        issuer_count = session.sql(f"""
            SELECT COUNT(DISTINCT IssuerID) as cnt FROM {database_name}.{schema_name}.FACT_SEC_FINANCIALS
        """).collect()[0]['CNT']
        
        period_count = session.sql(f"""
            SELECT COUNT(DISTINCT CONCAT(CIK, '-', FISCAL_YEAR, '-', FISCAL_PERIOD)) as cnt 
            FROM {database_name}.{schema_name}.FACT_SEC_FINANCIALS
        """).collect()[0]['CNT']
        
        log_detail(f" FACT_SEC_FINANCIALS: {count:,} records for {issuer_count} issuers, {period_count} fiscal periods (REAL DATA)")
        
        if count == 0:
            raise RuntimeError(
                "FACT_SEC_FINANCIALS has no records - no matching issuers with CIK found in real data source. "
                "Check that DIM_ISSUER CIK values match SEC financial data."
            )
        
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error building FACT_SEC_FINANCIALS: {e}")


def build_sec_segments(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_SEC_SEGMENTS from SEC_METRICS_TIMESERIES.
    
    This provides revenue segment breakdowns by:
    - Geography (GEO_NAME): Europe, Americas, Asia Pacific, etc.
    - Business Segment (BUSINESS_SEGMENT): Products, services, brands
    - Business Subsegment (BUSINESS_SUBSEGMENT): Hierarchical sub-segments
    - Customer (CUSTOMER): Major customer breakdowns
    - Legal Entity (LEGAL_ENTITY): Subsidiary breakdowns
    
    Source: SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.SEC_METRICS_TIMESERIES
    - Pre-parsed revenue segments with standardized columns
    - Focuses on revenue data only (not full financial statements)
    
    Join key: COMPANY_ID matches DIM_ISSUER.ProviderCompanyID
    
    Raises RuntimeError if real data source is not accessible.
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    log_detail("Building FACT_SEC_SEGMENTS from SEC_METRICS_TIMESERIES...")
    
    limit_clause = "LIMIT 100000" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_SEC_SEGMENTS AS
            WITH our_companies AS (
                -- Get all demo companies via ProviderCompanyID
                -- Note: COMPANY_NAME available via IssuerID -> DIM_ISSUER join
                SELECT 
                    di.IssuerID,
                    di.ProviderCompanyID
                FROM {database_name}.{curated_schema}.DIM_ISSUER di
                WHERE di.ProviderCompanyID IS NOT NULL
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY oc.IssuerID, smt.FISCAL_YEAR DESC, smt.PERIOD_END_DATE DESC) as SEGMENT_ID,
                oc.IssuerID,
                smt.ADSH,
                
                -- Time dimensions
                smt.PERIOD_START_DATE,
                smt.PERIOD_END_DATE,
                smt.FISCAL_PERIOD,
                CAST(smt.FISCAL_YEAR AS INTEGER) as FISCAL_YEAR,
                smt.FREQUENCY,
                
                -- Metric identification
                smt.VARIABLE_NAME,
                smt.TAG,
                smt.MEASURE,
                
                -- Segment dimensions (the key value of this table)
                NULLIF(TRIM(smt.GEO_NAME), '') as GEOGRAPHY,
                NULLIF(TRIM(smt.BUSINESS_SEGMENT), '') as BUSINESS_SEGMENT,
                NULLIF(TRIM(smt.BUSINESS_SUBSEGMENT), '') as BUSINESS_SUBSEGMENT,
                NULLIF(TRIM(smt.CUSTOMER), '') as CUSTOMER,
                NULLIF(TRIM(smt.LEGAL_ENTITY), '') as LEGAL_ENTITY,
                
                -- The value
                smt.VALUE as SEGMENT_REVENUE,
                UPPER(smt.UNIT) as CURRENCY,
                
                -- Metadata
                'SEC_METRICS_TIMESERIES' as DATA_SOURCE,
                CURRENT_TIMESTAMP() as LOADED_AT
                
            FROM {real_db}.{real_schema}.SEC_METRICS_TIMESERIES smt
            INNER JOIN our_companies oc ON smt.COMPANY_ID = oc.ProviderCompanyID
            WHERE smt.VALUE IS NOT NULL
              AND smt.FISCAL_YEAR >= YEAR(CURRENT_DATE()) - 5
            {limit_clause}
        """).collect()
        
        # Get stats
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS").collect()[0]['CNT']
        issuer_count = session.sql(f"SELECT COUNT(DISTINCT IssuerID) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS").collect()[0]['CNT']
        geo_count = session.sql(f"SELECT COUNT(DISTINCT GEOGRAPHY) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS WHERE GEOGRAPHY IS NOT NULL").collect()[0]['CNT']
        segment_count = session.sql(f"SELECT COUNT(DISTINCT BUSINESS_SEGMENT) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS WHERE BUSINESS_SEGMENT IS NOT NULL").collect()[0]['CNT']
        
        log_detail(f"  FACT_SEC_SEGMENTS: {count:,} records, {issuer_count} issuers, {geo_count} geographies, {segment_count} business segments (REAL DATA)")
        
        if count == 0:
            log_warning("  FACT_SEC_SEGMENTS has no records - check if demo companies have segment data in SEC_METRICS_TIMESERIES")
        
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error building FACT_SEC_SEGMENTS: {e}")


# =============================================================================
# SYNTHETIC DATA GENERATION FUNCTIONS
# =============================================================================

def build_reference_tables(session: Session, test_mode: bool = False):
    """
    Build reference tables for MARKET_DATA schema.
    
    Note: DIM_COMPANY has been eliminated. Use CURATED.DIM_ISSUER directly.
    This function now only builds DIM_BROKER.
    """
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    
    # Verify DIM_ISSUER exists (used as company master for MARKET_DATA)
    issuer_count = session.sql(f"""
        SELECT COUNT(*) as cnt FROM {database_name}.{curated_schema}.DIM_ISSUER
    """).collect()[0]['CNT']
    log_detail(f"Using DIM_ISSUER as company master: {issuer_count} issuers")
    
    # DIM_BROKER - Broker firms
    log_detail("Building DIM_BROKER...")
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
    log_detail(f" DIM_BROKER: {len(brokers)} brokers")


def build_broker_analyst_data(session: Session, test_mode: bool = False):
    """Build broker and analyst coverage data."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    log_detail("Building DIM_ANALYST and FACT_ANALYST_COVERAGE...")
    
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
    log_detail(f" DIM_ANALYST: {analyst_count} analysts")
    
    # Generate analyst coverage (which analysts cover which companies)
    min_brokers, max_brokers = config.MARKET_DATA['generation']['brokers_per_company']
    
    # Get max price date as reference (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_ANALYST_COVERAGE. "
            "Run build_price_anchor() first."
        )
    
    # Use DIM_ISSUER directly (DIM_COMPANY has been eliminated)
    curated_schema = config.DATABASE['schemas']['curated']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_ANALYST_COVERAGE AS
        WITH issuer_broker_pairs AS (
            SELECT 
                i.IssuerID,
                a.ANALYST_ID,
                a.BROKER_ID,
                -- Assign brokers to issuers using HASH for deterministic ordering
                ROW_NUMBER() OVER (PARTITION BY i.IssuerID ORDER BY ABS(HASH(i.IssuerID * 1000 + a.ANALYST_ID))) as BROKER_RANK,
                -- Calculate how many brokers this issuer should have (3-8)
                {min_brokers} + MOD(ABS(HASH(i.IssuerID)), {max_brokers - min_brokers + 1}) as BROKER_COUNT
            FROM {database_name}.{curated_schema}.DIM_ISSUER i
            CROSS JOIN {database_name}.{market_data_schema}.DIM_ANALYST a
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY IssuerID, ANALYST_ID) as COVERAGE_ID,
            IssuerID,
            ANALYST_ID,
            BROKER_ID,
            DATEADD(day, -(30 + MOD(ABS(HASH(IssuerID * 100 + ANALYST_ID)), 335)), '{max_price_date}'::DATE) as COVERAGE_START_DATE,
            NULL as COVERAGE_END_DATE,
            TRUE as IS_ACTIVE
        FROM issuer_broker_pairs
        WHERE BROKER_RANK <= BROKER_COUNT
    """).collect()
    
    coverage_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_ANALYST_COVERAGE").collect()[0]['CNT']
    log_detail(f" FACT_ANALYST_COVERAGE: {coverage_count} coverage records")


def build_estimate_data(session: Session, test_mode: bool = False):
    """Build analyst estimates and consensus data.
    
    Now derives base actuals from FACT_SEC_FINANCIALS (real SEC data)
    instead of synthetic FACT_FINANCIAL_DATA.
    
    Uses max_price_date as the reference "today" for generating future estimates.
    """
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    # Get max price date as reference for "today" (anchor to real market data)
    max_price_date = get_max_price_date(session)
    if max_price_date is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES not found - cannot build FACT_ESTIMATE_CONSENSUS. "
            "Run build_price_anchor() first."
        )
    
    log_detail("Building FACT_ESTIMATE_CONSENSUS from real SEC data...")
    
    forward_years = config.MARKET_DATA['generation']['estimates_forward_years']
    if test_mode:
        forward_years = 1
    
    # Generate consensus estimates for future periods using FACT_SEC_FINANCIALS as base
    # Uses max_price_date as reference "today" for future period calculation
    # Uses DIM_ISSUER directly (DIM_COMPANY has been eliminated)
    curated_schema = config.DATABASE['schemas']['curated']
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_ESTIMATE_CONSENSUS AS
        WITH future_periods AS (
            SELECT 
                i.IssuerID,
                YEAR('{max_price_date}'::DATE) + y.YEAR_OFFSET as ESTIMATE_YEAR,
                q.FISCAL_QUARTER
            FROM {database_name}.{curated_schema}.DIM_ISSUER i
            CROSS JOIN (SELECT SEQ4() as YEAR_OFFSET FROM TABLE(GENERATOR(ROWCOUNT => {forward_years + 1}))) y
            CROSS JOIN (SELECT SEQ4() + 1 as FISCAL_QUARTER FROM TABLE(GENERATOR(ROWCOUNT => 4))) q
            WHERE DATE_FROM_PARTS(YEAR('{max_price_date}'::DATE) + y.YEAR_OFFSET, q.FISCAL_QUARTER * 3, 1) > '{max_price_date}'::DATE
        ),
        -- Get latest actuals from real SEC financials (FACT_SEC_FINANCIALS)
        -- Unpivot key metrics into the DATA_ITEM_ID format for compatibility
        latest_sec_data AS (
            SELECT 
                sf.IssuerID,
                sf.FISCAL_YEAR,
                sf.FISCAL_PERIOD,
                sf.REVENUE,
                sf.NET_INCOME,
                sf.EBITDA,
                sf.TAM,
                sf.ESTIMATED_CUSTOMER_COUNT,
                sf.ESTIMATED_NRR_PCT,
                ROW_NUMBER() OVER (PARTITION BY sf.IssuerID ORDER BY sf.FISCAL_YEAR DESC, sf.PERIOD_END_DATE DESC) as RN
            FROM {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS sf
            WHERE sf.REVENUE IS NOT NULL
        ),
        -- Unpivot to DATA_ITEM_ID format
        latest_actuals AS (
            SELECT IssuerID, 1001 as DATA_ITEM_ID, REVENUE as LATEST_ACTUAL FROM latest_sec_data WHERE RN = 1 AND REVENUE IS NOT NULL
            UNION ALL
            SELECT IssuerID, 1005 as DATA_ITEM_ID, NET_INCOME as LATEST_ACTUAL FROM latest_sec_data WHERE RN = 1 AND NET_INCOME IS NOT NULL
            UNION ALL
            SELECT IssuerID, 1008 as DATA_ITEM_ID, EBITDA as LATEST_ACTUAL FROM latest_sec_data WHERE RN = 1 AND EBITDA IS NOT NULL
            UNION ALL
            SELECT IssuerID, 1011 as DATA_ITEM_ID, TAM as LATEST_ACTUAL FROM latest_sec_data WHERE RN = 1 AND TAM IS NOT NULL
            UNION ALL
            SELECT IssuerID, 1012 as DATA_ITEM_ID, ESTIMATED_CUSTOMER_COUNT as LATEST_ACTUAL FROM latest_sec_data WHERE RN = 1 AND ESTIMATED_CUSTOMER_COUNT IS NOT NULL
            UNION ALL
            SELECT IssuerID, 4009 as DATA_ITEM_ID, ESTIMATED_NRR_PCT as LATEST_ACTUAL FROM latest_sec_data WHERE RN = 1 AND ESTIMATED_NRR_PCT IS NOT NULL
        ),
        base_estimates AS (
            SELECT 
                fp.IssuerID,
                fp.ESTIMATE_YEAR,
                fp.FISCAL_QUARTER,
                la.DATA_ITEM_ID,
                la.LATEST_ACTUAL,
                -- Growth assumptions by year (relative to max_price_date year)
                CASE fp.ESTIMATE_YEAR - YEAR('{max_price_date}'::DATE)
                    WHEN 0 THEN 1.08  -- Current year: 8% growth
                    WHEN 1 THEN 1.15  -- Next year: 15% growth from current
                    ELSE 1.25         -- Year after: 25% growth from current
                END as GROWTH_FACTOR
            FROM future_periods fp
            JOIN latest_actuals la ON fp.IssuerID = la.IssuerID
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY IssuerID, ESTIMATE_YEAR, FISCAL_QUARTER, DATA_ITEM_ID) as CONSENSUS_ID,
            IssuerID,
            ESTIMATE_YEAR,
            FISCAL_QUARTER,
            DATA_ITEM_ID,
            -- Use HASH for deterministic variance
            ROUND(LATEST_ACTUAL * GROWTH_FACTOR * (1 + (ABS(MOD(HASH(IssuerID * 1000 + ESTIMATE_YEAR * 10 + FISCAL_QUARTER), 100)) - 50) / 1000.0), 0) as CONSENSUS_MEAN,
            ROUND(LATEST_ACTUAL * GROWTH_FACTOR * 0.95, 0) as CONSENSUS_LOW,
            ROUND(LATEST_ACTUAL * GROWTH_FACTOR * 1.05, 0) as CONSENSUS_HIGH,
            5 + MOD(ABS(HASH(IssuerID * 7)), 11) as NUM_ESTIMATES,  -- 5-15 estimates
            '{max_price_date}'::DATE as AS_OF_DATE,
            CURRENT_TIMESTAMP() as LAST_UPDATED
        FROM base_estimates
    """).collect()
    
    consensus_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_ESTIMATE_CONSENSUS").collect()[0]['CNT']
    log_detail(f" FACT_ESTIMATE_CONSENSUS: {consensus_count} consensus records")
    
    # Generate price targets and ratings
    log_detail("Building FACT_ESTIMATE_DATA (price targets & ratings)...")
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_ESTIMATE_DATA AS
        WITH analyst_estimates AS (
            SELECT 
                ac.COVERAGE_ID,
                ac.IssuerID,
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
                -- Estimate dates within 90 days before max_price_date
                DATEADD(day, -(1 + MOD(ABS(HASH(ac.COVERAGE_ID * 1003)), 89)), '{max_price_date}'::DATE) as ESTIMATE_DATE
            FROM {database_name}.{market_data_schema}.FACT_ANALYST_COVERAGE ac
            WHERE ac.IS_ACTIVE = TRUE
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY IssuerID, ANALYST_ID) as ESTIMATE_ID,
            IssuerID,
            ANALYST_ID,
            BROKER_ID,
            5005 as DATA_ITEM_ID,  -- Price Target
            PRICE_TARGET as DATA_VALUE,
            ESTIMATE_DATE,
            CURRENT_TIMESTAMP() as LAST_UPDATED
        FROM analyst_estimates
        
        UNION ALL
        
        SELECT 
            ROW_NUMBER() OVER (ORDER BY IssuerID, ANALYST_ID) + 1000000,
            IssuerID,
            ANALYST_ID,
            BROKER_ID,
            5006 as DATA_ITEM_ID,  -- Rating
            RATING_CODE,
            ESTIMATE_DATE,
            CURRENT_TIMESTAMP()
        FROM analyst_estimates
    """).collect()
    
    estimate_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_ESTIMATE_DATA").collect()[0]['CNT']
    log_detail(f" FACT_ESTIMATE_DATA: {estimate_count} estimate records")
