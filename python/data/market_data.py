#!/usr/bin/env python3
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
from utils.logging import log_step, log_substep, log_detail, log_warning, log_error, log_success, log_phase, log_phase_complete
from utils.snowflake import get_max_price_date, reset_max_price_date, verify_table_access


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
    
    # Create schema if not exists
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {database_name}.{schema_name}").collect()
    
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
    
    # Create schema if not exists
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {database_name}.{schema_name}").collect()
    
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
    
    log_substep("Real SEC financials (comprehensive with TAM/NRR)")
    build_real_sec_financials(session, test_mode)
    
    log_substep("Real SEC segments (geographic and business)")
    build_sec_segments(session, test_mode)
    
    log_substep("Geographic risk classification lookup")
    build_geo_risk_classification(session)
    
    log_substep("Broker analyst data")
    build_broker_analyst_data(session, test_mode)
    
    log_substep("Estimate data (from real SEC actuals)")
    build_estimate_data(session, test_mode)
    
    log_substep("Macroeconomic data (policy rates, FX, economic indicators)")
    build_fact_policy_rates(session, test_mode)
    build_fact_fx_rates(session, test_mode)
    build_fact_economic_indicators(session, test_mode)
    
    log_substep("Treasury yield curve (daily, 14 maturities)")
    build_fact_treasury_yields(session, test_mode)
    
    log_substep("Country emissions (Climate Watch GHG)")
    build_fact_country_emissions(session, test_mode)
    
    log_substep("SEC insider transactions (Form 4)")
    build_fact_insider_transactions(session, test_mode)
    
    log_substep("Institutional holdings (SEC 13F)")
    build_fact_institutional_holdings(session, test_mode)
    
    try:
        dividend_count = session.sql(f"""
            SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_DIVIDENDS
        """).collect()[0]['CNT']
        if dividend_count > 0:
            log_detail(f"  FACT_DIVIDENDS already exists ({dividend_count:,} records)")
        else:
            dividend_mode = "synthetic" if config.MARKET_DATA.get('synthetic_dividends', False) else "SEC filings + AI_EXTRACT"
            log_substep(f"Dividend data ({dividend_mode})")
            build_fact_dividends(session, test_mode)
    except Exception:
        dividend_mode = "synthetic" if config.MARKET_DATA.get('synthetic_dividends', False) else "SEC filings + AI_EXTRACT"
        log_substep(f"Dividend data ({dividend_mode})")
        build_fact_dividends(session, test_mode)
    
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
                  AND scra.PERIOD_END_DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
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
                      'ShareBasedCompensation',
                      -- Shares Outstanding tags
                      'EntityCommonStockSharesOutstanding',
                      'CommonStockSharesOutstanding',
                      'WeightedAverageNumberOfSharesOutstandingBasic',
                      'WeightedAverageNumberOfDilutedSharesOutstanding'
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
                        WHEN sd.COVERED_QTRS = 0 THEN 'Q0'
                        WHEN sd.COVERED_QTRS = 1 THEN 'Q' || QUARTER(sd.PERIOD_END_DATE)
                        ELSE 'Q' || sd.COVERED_QTRS || '_YTD'
                    END as FISCAL_PERIOD,
                    CASE 
                        WHEN sd.COVERED_QTRS = 4 THEN 'annual'
                        WHEN sd.COVERED_QTRS = 0 THEN 'balance_sheet_only'
                        WHEN sd.COVERED_QTRS = 1 THEN 'quarterly'
                        ELSE 'cumulative_ytd'
                    END as PERIOD_TYPE,
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
                             THEN sd.VALUE_NUM END) as STOCK_BASED_COMP,
                    
                    -- Shares Outstanding
                    MAX(CASE WHEN sd.TAG = 'EntityCommonStockSharesOutstanding' 
                             THEN sd.VALUE_NUM END) as ENTITY_SHARES_OUTSTANDING,
                    MAX(CASE WHEN sd.TAG = 'CommonStockSharesOutstanding' 
                             THEN sd.VALUE_NUM END) as COMMON_SHARES_OUTSTANDING,
                    MAX(CASE WHEN sd.TAG = 'WeightedAverageNumberOfSharesOutstandingBasic' 
                             THEN sd.VALUE_NUM END) as WEIGHTED_AVG_SHARES_BASIC,
                    MAX(CASE WHEN sd.TAG = 'WeightedAverageNumberOfDilutedSharesOutstanding' 
                             THEN sd.VALUE_NUM END) as WEIGHTED_AVG_SHARES_DILUTED
                    
                FROM sec_data sd
                GROUP BY sd.CIK, sd.ADSH, sd.PERIOD_END_DATE, sd.PERIOD_START_DATE, sd.COVERED_QTRS
            ),
            deduped AS (
                SELECT pd.*
                FROM (
                    SELECT pd2.*,
                           ROW_NUMBER() OVER (
                               PARTITION BY pd2.CIK, pd2.FISCAL_YEAR, pd2.FISCAL_PERIOD
                               ORDER BY (CASE WHEN pd2.REVENUE IS NOT NULL THEN 0 ELSE 1 END),
                                        pd2.ADSH DESC
                           ) as rn
                    FROM pivoted_data pd2
                ) pd
                WHERE pd.rn = 1
            ),
            bs_snapshot AS (
                SELECT
                    CIK, PERIOD_END_DATE,
                    TOTAL_ASSETS        AS BS_TOTAL_ASSETS,
                    TOTAL_LIABILITIES   AS BS_TOTAL_LIABILITIES,
                    TOTAL_EQUITY        AS BS_TOTAL_EQUITY,
                    CASH_AND_EQUIVALENTS AS BS_CASH_AND_EQUIVALENTS,
                    LONG_TERM_DEBT      AS BS_LONG_TERM_DEBT,
                    GOODWILL            AS BS_GOODWILL,
                    PP_AND_E            AS BS_PP_AND_E,
                    CURRENT_ASSETS      AS BS_CURRENT_ASSETS,
                    CURRENT_LIABILITIES AS BS_CURRENT_LIABILITIES,
                    RETAINED_EARNINGS   AS BS_RETAINED_EARNINGS
                FROM deduped
                WHERE COVERED_QTRS = 0
            ),
            enriched AS (
                SELECT
                    d.*,
                    COALESCE(d.TOTAL_ASSETS, bs.BS_TOTAL_ASSETS)               AS MERGED_TOTAL_ASSETS,
                    COALESCE(d.TOTAL_LIABILITIES, bs.BS_TOTAL_LIABILITIES)     AS MERGED_TOTAL_LIABILITIES,
                    COALESCE(d.TOTAL_EQUITY, bs.BS_TOTAL_EQUITY)               AS MERGED_TOTAL_EQUITY,
                    COALESCE(d.CASH_AND_EQUIVALENTS, bs.BS_CASH_AND_EQUIVALENTS) AS MERGED_CASH_AND_EQUIVALENTS,
                    COALESCE(d.LONG_TERM_DEBT, bs.BS_LONG_TERM_DEBT)           AS MERGED_LONG_TERM_DEBT,
                    COALESCE(d.CURRENT_ASSETS, bs.BS_CURRENT_ASSETS)           AS MERGED_CURRENT_ASSETS,
                    COALESCE(d.CURRENT_LIABILITIES, bs.BS_CURRENT_LIABILITIES) AS MERGED_CURRENT_LIABILITIES
                FROM deduped d
                LEFT JOIN bs_snapshot bs
                    ON d.CIK = bs.CIK AND d.PERIOD_END_DATE = bs.PERIOD_END_DATE
            ),
            with_growth AS (
                SELECT 
                    dd.*,
                    LAG(dd.REVENUE) OVER (PARTITION BY dd.CIK ORDER BY dd.FISCAL_YEAR, dd.FISCAL_PERIOD) as PREV_REVENUE,
                    CASE 
                        WHEN LAG(dd.REVENUE) OVER (PARTITION BY dd.CIK ORDER BY dd.FISCAL_YEAR, dd.FISCAL_PERIOD) > 0 
                        THEN (dd.REVENUE - LAG(dd.REVENUE) OVER (PARTITION BY dd.CIK ORDER BY dd.FISCAL_YEAR, dd.FISCAL_PERIOD)) 
                             / LAG(dd.REVENUE) OVER (PARTITION BY dd.CIK ORDER BY dd.FISCAL_YEAR, dd.FISCAL_PERIOD) * 100
                        ELSE NULL 
                    END as REVENUE_GROWTH_PCT
                FROM enriched dd
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
                wg.PERIOD_TYPE,
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
                CASE WHEN wg.MERGED_TOTAL_EQUITY > 0 THEN wg.NET_INCOME / wg.MERGED_TOTAL_EQUITY * 100 END as ROE_PCT,
                CASE WHEN wg.MERGED_TOTAL_ASSETS > 0 THEN wg.NET_INCOME / wg.MERGED_TOTAL_ASSETS * 100 END as ROA_PCT,
                CASE WHEN wg.MERGED_TOTAL_EQUITY > 0 THEN wg.MERGED_LONG_TERM_DEBT / wg.MERGED_TOTAL_EQUITY END as DEBT_TO_EQUITY,
                CASE WHEN wg.MERGED_CURRENT_LIABILITIES > 0 THEN wg.MERGED_CURRENT_ASSETS / wg.MERGED_CURRENT_LIABILITIES END as CURRENT_RATIO,
                
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
                
                -- Shares Outstanding (coalesced for best coverage)
                COALESCE(wg.COMMON_SHARES_OUTSTANDING, wg.ENTITY_SHARES_OUTSTANDING, wg.WEIGHTED_AVG_SHARES_BASIC, wg.WEIGHTED_AVG_SHARES_DILUTED) as SHARES_OUTSTANDING,
                wg.WEIGHTED_AVG_SHARES_BASIC,
                wg.WEIGHTED_AVG_SHARES_DILUTED,
                
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
                SELECT 
                    di.IssuerID,
                    di.ProviderCompanyID
                FROM {database_name}.{curated_schema}.DIM_ISSUER di
                WHERE di.ProviderCompanyID IS NOT NULL
            ),
            latest_adsh AS (
                SELECT COMPANY_ID, FISCAL_YEAR, FISCAL_PERIOD, MAX(ADSH) as ADSH
                FROM {real_db}.{real_schema}.SEC_METRICS_TIMESERIES
                WHERE VALUE IS NOT NULL
                  AND FISCAL_YEAR >= YEAR(CURRENT_DATE()) - {config.YEARS_OF_HISTORY}
                GROUP BY COMPANY_ID, FISCAL_YEAR, FISCAL_PERIOD
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY oc.IssuerID, smt.FISCAL_YEAR DESC, smt.PERIOD_END_DATE DESC) as SEGMENT_ID,
                oc.IssuerID,
                smt.ADSH,
                
                smt.PERIOD_START_DATE,
                smt.PERIOD_END_DATE,
                smt.FISCAL_PERIOD,
                CAST(smt.FISCAL_YEAR AS INTEGER) as FISCAL_YEAR,
                smt.FREQUENCY,
                
                smt.VARIABLE_NAME,
                smt.TAG,
                smt.MEASURE,
                
                NULLIF(TRIM(smt.GEO_NAME), '') as GEOGRAPHY,
                NULLIF(TRIM(smt.BUSINESS_SEGMENT), '') as BUSINESS_SEGMENT,
                NULLIF(TRIM(smt.BUSINESS_SUBSEGMENT), '') as BUSINESS_SUBSEGMENT,
                NULLIF(TRIM(smt.CUSTOMER), '') as CUSTOMER,
                NULLIF(TRIM(smt.LEGAL_ENTITY), '') as LEGAL_ENTITY,
                
                smt.VALUE as SEGMENT_REVENUE,
                UPPER(smt.UNIT) as CURRENCY,
                
                CASE WHEN UPPER(COALESCE(TRIM(smt.BUSINESS_SEGMENT), '') || ' ' || COALESCE(TRIM(smt.BUSINESS_SUBSEGMENT), ''))
                     RLIKE '.*(\\\\bAI\\\\b|ARTIFICIAL INTELLIGENCE|MACHINE LEARNING|\\\\bCLOUD\\\\b|DATA CENTER|\\\\bGPU\\\\b|INTELLIGENT|GENERATIVE|DEEP LEARNING|NEURAL).*'
                     THEN TRUE ELSE FALSE END AS AI_REVENUE_FLAG,
                
                'SEC_METRICS_TIMESERIES' as DATA_SOURCE,
                CURRENT_TIMESTAMP() as LOADED_AT
                
            FROM {real_db}.{real_schema}.SEC_METRICS_TIMESERIES smt
            INNER JOIN our_companies oc ON smt.COMPANY_ID = oc.ProviderCompanyID
            INNER JOIN latest_adsh la ON smt.COMPANY_ID = la.COMPANY_ID
                AND smt.FISCAL_YEAR = la.FISCAL_YEAR
                AND smt.FISCAL_PERIOD = la.FISCAL_PERIOD
                AND smt.ADSH = la.ADSH
            WHERE smt.VALUE IS NOT NULL
              AND smt.FISCAL_YEAR >= YEAR(CURRENT_DATE()) - {config.YEARS_OF_HISTORY}
            {limit_clause}
        """).collect()
        
        # Get stats
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS").collect()[0]['CNT']
        issuer_count = session.sql(f"SELECT COUNT(DISTINCT IssuerID) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS").collect()[0]['CNT']
        geo_count = session.sql(f"SELECT COUNT(DISTINCT GEOGRAPHY) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS WHERE GEOGRAPHY IS NOT NULL").collect()[0]['CNT']
        segment_count = session.sql(f"SELECT COUNT(DISTINCT BUSINESS_SEGMENT) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS WHERE BUSINESS_SEGMENT IS NOT NULL").collect()[0]['CNT']
        ai_flag_count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS WHERE AI_REVENUE_FLAG = TRUE").collect()[0]['CNT']
        
        log_detail(f"  FACT_SEC_SEGMENTS: {count:,} records, {issuer_count} issuers, {geo_count} geographies, {segment_count} business segments, {ai_flag_count} AI-flagged rows (REAL DATA)")
        
        if count == 0:
            log_warning("  FACT_SEC_SEGMENTS has no records - check if demo companies have segment data in SEC_METRICS_TIMESERIES")
        
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error building FACT_SEC_SEGMENTS: {e}")


def build_geo_risk_classification(session: Session) -> None:
    """
    Build DIM_GEO_RISK_CLASSIFICATION lookup table mapping geography names to risk tiers.
    
    Uses pattern matching against the 189+ distinct GEOGRAPHY values in FACT_SEC_SEGMENTS.
    Risk tiers:
    - HIGH (weight 1.0): China, Taiwan, Russia, Iran, Middle East, Hong Kong
    - MEDIUM (weight 0.5): Other Asia Pacific, Latin America, Africa, Eastern Europe
    - LOW (weight 0.1): US, Canada, Western Europe, Japan, Australia, South Korea
    
    Composite/ambiguous regions get the highest-risk component's tier.
    """
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    
    log_detail("Building DIM_GEO_RISK_CLASSIFICATION lookup table...")
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{schema_name}.DIM_GEO_RISK_CLASSIFICATION AS
        WITH geo_values AS (
            SELECT DISTINCT GEOGRAPHY
            FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS
            WHERE GEOGRAPHY IS NOT NULL
        )
        SELECT
            GEOGRAPHY,
            CASE
                WHEN GEOGRAPHY IN ('CHINA', 'CHINA MAINLAND', 'GREATER CHINA', 'CHINA AND HONG KONG')
                    THEN 'HIGH'
                WHEN GEOGRAPHY IN ('TAIWAN', 'HONG KONG', 'HONG KONG SARTAIWAN AND MACAU SAR')
                    THEN 'HIGH'
                WHEN GEOGRAPHY LIKE '%RUSSIA%' OR GEOGRAPHY LIKE '%IRAN%'
                    THEN 'HIGH'
                WHEN GEOGRAPHY IN ('MIDDLE EAST', 'MIDDLE EAST AND AFRICA', 'MIDDLE EAST AND NORTHERN AFRICA',
                                   'MIDDLE EAST AND NORTH AFRICA MEMBER', 'MIDDLE EAST AND ASIA',
                                   'MIDDLE EAST AFRICA AND SOUTH ASIA',
                                   'SOUTH ASIA MIDDLE EAST AND NORTH AFRICA')
                    THEN 'HIGH'
                WHEN GEOGRAPHY LIKE '%MIDDLE EAST%' AND GEOGRAPHY LIKE '%AFRICA%'
                    THEN 'HIGH'

                WHEN GEOGRAPHY IN ('ASIA PACIFIC', 'ASIA PACIFIC AND OTHER', 'ASIA PACIFIC AND JAPAN',
                                   'ASIA PACIFIC INCLUDING AUSTRALIA AND NEW ZEALAND',
                                   'ASIA PACIFIC MIDDLE EAST AND AFRICA',
                                   'ASIA PACIFIC OTHER THAN CHINA',
                                   'ASIA PACIFIC EXCLUDING CHINA AND HONG KONG',
                                   'ASIA PACIFIC EXCLUDING GREATER CHINA',
                                   'ASIA EXCLUDING CHINA', 'OTHER ASIA', 'OTHER ASIA PACIFIC',
                                   'EAST ASIA AND AUSTRALIA', 'EAST ASIA AND OCEANIA',
                                   'SOUTH AND SOUTHEAST ASIA', 'SOUTH EAST ASIA', 'ASIAS')
                    THEN 'MEDIUM'
                WHEN GEOGRAPHY IN ('LATIN AMERICA', 'LATIN AMERICA AND CANADA',
                                   'LATIN AMERICA AND CARIBBEAN EXCLUDING BRAZIL',
                                   'LATIN AMERICA AND THE CARIBBEAN', 'SOUTH AMERICA',
                                   'SOUTH AND CENTRAL AMERICA', 'CARIBBEAN AND LATIN AMERICA',
                                   'REST OF NORTH AND SOUTH AMERICA', 'OTHER NORTH AND SOUTH AMERICA',
                                   'BRAZIL', 'MEXICO', 'MEXICO CENTRAL AMERICA', 'CHILE',
                                   'DOMINICAN REPUBLIC', 'EL SALVADOR', 'HONDURAS', 'PARAGUAY',
                                   'TRINIDAD AND TOBAGO', 'GUYANA')
                    THEN 'MEDIUM'
                WHEN GEOGRAPHY IN ('AFRICA', 'SOUTH AFRICA', 'ANGOLA', 'EGYPT', 'GHANA',
                                   'EQUATORIAL GUINEA', 'LIBYA', 'MOZAMBIQUE', 'MAURITANIA SENEGAL',
                                   'AFRICA AND EUROPE', 'AFRICA, CIS AND EUROPE')
                    THEN 'MEDIUM'
                WHEN GEOGRAPHY IN ('EASTERN EUROPE', 'CENTRAL EUROPE AND COMMONWEALTH OF INDEPENDENT STATES',
                                   'CIS AND EUROPE', 'CIS, EUROPE AND RUSSIA',
                                   'CIS, EUROPE AND SUB SAHARAN AFRICA', 'EUROPE CISAND SUB SAHARAN AFRICA',
                                   'EUROPE RUSSIA CENTRAL ASIA', 'HUNGARY', 'BULGARIA', 'POLAND')
                    THEN 'MEDIUM'
                WHEN GEOGRAPHY IN ('EMERGING MARKETS', 'GROWTH MARKETS',
                                   'INTERNATIONAL EMERGING MARKETS', 'PHILIPPINES', 'VIETNAM',
                                   'THAILAND', 'MALAYSIA', 'SINGAPORE', 'INDIA',
                                   'UNITED ARAB EMIRATES', 'SAUDI ARABIA', 'JORDAN')
                    THEN 'MEDIUM'
                WHEN GEOGRAPHY LIKE 'IN' OR GEOGRAPHY LIKE 'ID'
                    THEN 'MEDIUM'

                WHEN GEOGRAPHY IN ('UNITED STATES', 'UNITED STATES AND CANADA',
                                   'UNITED STATES EXCLUDING OTHER NET SALES',
                                   'UNITED STATES EXPORTS', 'UNITED STATES GULF OF MEXICO',
                                   'NORTH AMERICA', 'NORTH AMERICA OTHER THAN UNITED STATES',
                                   'CANADA', 'CANADA AND MEXICO', 'OTHER NORTH AMERICA',
                                   'AMERICAS', 'AMERICAS EXCLUDING UNITED STATES',
                                   'AMERICAS EXCLUDING UNITED STATES AND MEXICO',
                                   'AMERICAS OTHER THAN UNITED STATES', 'OTHER AMERICAS')
                    THEN 'LOW'
                WHEN GEOGRAPHY IN ('EUROPE', 'WESTERN EUROPE', 'DEVELOPED EUROPE',
                                   'EUROPE AND REST OF WORLD', 'EUROPE AND CENTRAL ASIA',
                                   'EUROPE OTHER THAN NETHERLANDS', 'EUROPE OTHER THAN UNITED KINGDOM',
                                   'EUROPEAN UNION', 'EMEA', 'EMEA AND INDIA',
                                   'EMEA OTHER THAN UNITED KINGDOM',
                                   'OTHER EUROPE MIDDLE EAST AND AFRICA',
                                   'EUROPE AFRICA CIS')
                    THEN 'LOW'
                WHEN GEOGRAPHY IN ('UNITED KINGDOM', 'FRANCE', 'GERMANY', 'ITALY', 'SPAIN',
                                   'NETHERLANDS', 'BELGIUM', 'SWITZERLAND', 'SWEDEN', 'NORWAY',
                                   'FINLAND', 'IRELAND', 'PORTUGAL', 'ICELAND', 'AUSTRIA',
                                   'DENMARK', 'LUXEMBOURG')
                    THEN 'LOW'
                WHEN GEOGRAPHY IN ('DE', 'NL', 'SK')
                    THEN 'LOW'
                WHEN GEOGRAPHY IN ('JAPAN', 'AUSTRALIA', 'AUSTRALIA AND ASIA',
                                   'AUSTRALASIA AND OTHER', 'OCEANIA', 'SOUTH KOREA', 'SOUTH KOREA1',
                                   'JAPAN AUSTRALIA NEW ZEALAND KOREA CANADAAND WESTERN EUROPE',
                                   'DEVELOPED INTERNATIONAL', 'INTERNATIONAL DEVELOPED MARKETS')
                    THEN 'LOW'

                WHEN GEOGRAPHY IN ('INTERNATIONAL', 'OTHER INTERNATIONAL',
                                   'COUNTRIES OTHER THAN NORTH AMERICA',
                                   'COUNTRIES OTHER THAN UNITED STATES AND CHINA',
                                   'COUNTRIES OTHER THAN UNITED STATES AND UNITED KINGDOM',
                                   'OTHER EXCLUDING NORTH AMERICA', 'NON USOTHER',
                                   'OTHER GEOGRAPHIES', 'WORLDWIDE', 'TOTAL',
                                   'TOTAL OTHER COUNTRIES EXCLUDING IRELAND',
                                   'TOTAL OTHER COUNTRIES EXCLUDING UNITED STATES AND IRELAND',
                                   'GEOGRAPHICAL OTHER THAN NORTH AMERICA EUROPE MIDDLE EAST AFRICA AND ASIA PACIFIC',
                                   'ASIA AFRICA AUSTRALIA NEW ZEALAND AND MIDDLE EAST',
                                   'ASIA AFRICA OCEANIA AND MIDDLE EAST',
                                   'ASIA PACIFIC AFRICA',
                                   'WESTERN HEMISPHERE EXCLUDING US',
                                   'CORPORATE AND OTHER', 'CORPORATE AND REGIONAL',
                                   'OTHER PROPERTY', 'OTHER STATES', 'OTHER US')
                    THEN 'MEDIUM'

                ELSE 'MEDIUM'
            END AS RISK_TIER,
            CASE
                WHEN GEOGRAPHY IN ('CHINA', 'CHINA MAINLAND', 'GREATER CHINA', 'CHINA AND HONG KONG')
                    THEN 1.0
                WHEN GEOGRAPHY IN ('TAIWAN', 'HONG KONG', 'HONG KONG SARTAIWAN AND MACAU SAR')
                    THEN 1.0
                WHEN GEOGRAPHY LIKE '%RUSSIA%' OR GEOGRAPHY LIKE '%IRAN%'
                    THEN 1.0
                WHEN GEOGRAPHY IN ('MIDDLE EAST', 'MIDDLE EAST AND AFRICA', 'MIDDLE EAST AND NORTHERN AFRICA',
                                   'MIDDLE EAST AND NORTH AFRICA MEMBER', 'MIDDLE EAST AND ASIA',
                                   'MIDDLE EAST AFRICA AND SOUTH ASIA',
                                   'SOUTH ASIA MIDDLE EAST AND NORTH AFRICA')
                    THEN 1.0
                WHEN GEOGRAPHY LIKE '%MIDDLE EAST%' AND GEOGRAPHY LIKE '%AFRICA%'
                    THEN 1.0
                WHEN GEOGRAPHY IN ('UNITED STATES', 'UNITED STATES AND CANADA',
                                   'UNITED STATES EXCLUDING OTHER NET SALES',
                                   'UNITED STATES EXPORTS', 'UNITED STATES GULF OF MEXICO',
                                   'NORTH AMERICA', 'NORTH AMERICA OTHER THAN UNITED STATES',
                                   'CANADA', 'CANADA AND MEXICO', 'OTHER NORTH AMERICA',
                                   'AMERICAS', 'AMERICAS EXCLUDING UNITED STATES',
                                   'AMERICAS EXCLUDING UNITED STATES AND MEXICO',
                                   'AMERICAS OTHER THAN UNITED STATES', 'OTHER AMERICAS',
                                   'EUROPE', 'WESTERN EUROPE', 'DEVELOPED EUROPE',
                                   'EUROPE AND REST OF WORLD', 'EUROPE AND CENTRAL ASIA',
                                   'EUROPE OTHER THAN NETHERLANDS', 'EUROPE OTHER THAN UNITED KINGDOM',
                                   'EUROPEAN UNION', 'EMEA', 'EMEA AND INDIA',
                                   'EMEA OTHER THAN UNITED KINGDOM',
                                   'OTHER EUROPE MIDDLE EAST AND AFRICA', 'EUROPE AFRICA CIS',
                                   'UNITED KINGDOM', 'FRANCE', 'GERMANY', 'ITALY', 'SPAIN',
                                   'NETHERLANDS', 'BELGIUM', 'SWITZERLAND', 'SWEDEN', 'NORWAY',
                                   'FINLAND', 'IRELAND', 'PORTUGAL', 'ICELAND',
                                   'DE', 'NL', 'SK',
                                   'JAPAN', 'AUSTRALIA', 'AUSTRALIA AND ASIA',
                                   'AUSTRALASIA AND OTHER', 'OCEANIA', 'SOUTH KOREA', 'SOUTH KOREA1',
                                   'JAPAN AUSTRALIA NEW ZEALAND KOREA CANADAAND WESTERN EUROPE',
                                   'DEVELOPED INTERNATIONAL', 'INTERNATIONAL DEVELOPED MARKETS')
                    THEN 0.1
                ELSE 0.5
            END AS RISK_WEIGHT
        FROM geo_values
    """).collect()
    
    classified = session.sql(f"""
        SELECT RISK_TIER, COUNT(*) AS cnt 
        FROM {database_name}.{schema_name}.DIM_GEO_RISK_CLASSIFICATION 
        GROUP BY RISK_TIER ORDER BY RISK_TIER
    """).collect()
    tier_summary = ", ".join([f"{r['RISK_TIER']}={r['CNT']}" for r in classified])
    log_detail(f"  DIM_GEO_RISK_CLASSIFICATION: {tier_summary}")


def build_transcript_nlp_scores(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_TRANSCRIPT_NLP_SCORES with AI exposure (AI_COMPLETE) and geo risk (SQL calculation).
    
    Two scoring approaches:
    - AI_EXPOSURE_SCORE: AI_COMPLETE on LISTAGG'd corpus transcript text
    - GEO_RISK_SCORE: Deterministic calculation from FACT_SEC_SEGMENTS geographic revenue,
      classified via DIM_GEO_RISK_CLASSIFICATION lookup table. Score = weighted high-risk
      revenue share * 100, with concentration bonus for single-country dominance.
    
    Sources:
    - Transcript text: CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS (pre-flattened, speaker-enriched)
    - Geographic revenue: FACT_SEC_SEGMENTS + DIM_GEO_RISK_CLASSIFICATION
    
    Must run AFTER pipeline execution (Phase 4) since corpus table is built by pipelines.
    Runs AI_COMPLETE on SAM_DEMO_CORTEX_WH, geo scoring on execution warehouse.
    """
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    cortex_wh = config.WAREHOUSES.get('cortex_search', config.WAREHOUSES['execution'])['name']
    years_of_history = config.YEARS_OF_HISTORY
    corpus_table = f"{database_name}.{curated_schema}.COMPANY_EVENT_TRANSCRIPTS_CORPUS"
    model = config.AI_SIGNAL_EXTRACTION_MODEL
    
    log_detail(f"Building FACT_TRANSCRIPT_NLP_SCORES using AI_COMPLETE ({model}) on corpus...")
    
    limit_clause = "LIMIT 5" if test_mode else ""
    
    try:
        transcript_count = session.sql(f"""
            SELECT COUNT(*) as cnt
            FROM {corpus_table}
            WHERE EVENT_TYPE = 'Earnings Call'
              AND PUBLISH_DATE >= DATEADD('year', -{years_of_history}, CURRENT_DATE())
        """).collect()[0]['CNT']
        
        if transcript_count == 0:
            log_warning("  No corpus transcripts found - creating empty FACT_TRANSCRIPT_NLP_SCORES")
            session.sql(f"""
                CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_TRANSCRIPT_NLP_SCORES (
                    IssuerID INT,
                    SecurityID INT,
                    PRIMARY_TICKER VARCHAR(16),
                    FISCAL_YEAR INT,
                    FISCAL_QUARTER INT,
                    EVENT_TIMESTAMP TIMESTAMP_NTZ,
                    AI_EXPOSURE_SCORE INT,
                    GEO_RISK_SCORE INT,
                    LOADED_AT TIMESTAMP_NTZ
                )
            """).collect()
            return
        
        session.sql(f"USE WAREHOUSE {cortex_wh}").collect()
        
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_TRANSCRIPT_NLP_SCORES AS
            WITH corpus_transcripts AS (
                SELECT
                    c.IssuerID,
                    c.SecurityID,
                    c.TICKER AS PRIMARY_TICKER,
                    c.PUBLISH_DATE,
                    YEAR(c.PUBLISH_DATE) AS FISCAL_YEAR,
                    QUARTER(c.PUBLISH_DATE) AS FISCAL_QUARTER,
                    c.DOCUMENT_TEXT,
                    c.SEGMENT_INDEX,
                    c.CHUNK_INDEX
                FROM {corpus_table} c
                INNER JOIN (
                    SELECT DISTINCT s.ISSUERID
                    FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR pos
                    JOIN {database_name}.CURATED.DIM_SECURITY s ON pos.SECURITYID = s.SECURITYID
                    WHERE pos.HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM {database_name}.CURATED.FACT_POSITION_DAILY_ABOR)
                      AND s.ISSUERID IS NOT NULL
                ) pi ON c.IssuerID = pi.ISSUERID
                WHERE c.EVENT_TYPE = 'Earnings Call'
                  AND c.SPEAKER_ROLE IN ('CEO', 'CFO', 'Chief Executive Officer', 'Chief Financial Officer', 'Unknown')
                  AND c.PUBLISH_DATE >= DATEADD('year', -{years_of_history}, CURRENT_DATE())
                  AND c.DOCUMENT_TEXT IS NOT NULL
                  AND LENGTH(c.DOCUMENT_TEXT) > 20
            ),
            aggregated_text AS (
                SELECT
                    ct.IssuerID,
                    ct.SecurityID,
                    ct.PRIMARY_TICKER,
                    ct.FISCAL_YEAR,
                    ct.FISCAL_QUARTER,
                    MAX(ct.PUBLISH_DATE)::TIMESTAMP_NTZ AS EVENT_TIMESTAMP,
                    LEFT(LISTAGG(ct.DOCUMENT_TEXT, ' ') WITHIN GROUP (ORDER BY ct.PUBLISH_DATE, ct.SEGMENT_INDEX, ct.CHUNK_INDEX), 1000000) AS FULL_TRANSCRIPT
                FROM corpus_transcripts ct
                GROUP BY ct.IssuerID, ct.SecurityID, ct.PRIMARY_TICKER, ct.FISCAL_YEAR, ct.FISCAL_QUARTER
            ),
            ai_scores AS (
                SELECT
                    a.IssuerID,
                    a.SecurityID,
                    a.PRIMARY_TICKER,
                    a.FISCAL_YEAR,
                    a.FISCAL_QUARTER,
                    a.EVENT_TIMESTAMP,
                    TRY_CAST(
                        REGEXP_SUBSTR(
                            SNOWFLAKE.CORTEX.COMPLETE(
                                '{model}',
                                'You are a financial analyst specializing in AI/ML exposure scoring. Analyze this earnings call transcript for a single company. Score the company''s exposure to artificial intelligence and machine learning on a scale of 0 to 100. Consider: AI/ML product revenue, AI R&D investment, AI chip/GPU sales, cloud AI services, generative AI initiatives, AI partnerships, and AI-driven business transformation. 100 = pure AI company like NVIDIA. 50 = significant AI exposure like Microsoft/Google. 10 = minimal AI mentions. 0 = no AI relevance at all. Return ONLY a single integer between 0 and 100, nothing else. Transcript: ' || a.FULL_TRANSCRIPT
                            ),
                            '\\d+'
                        ) AS INT
                    ) AS AI_EXPOSURE_SCORE
                FROM aggregated_text a
                {limit_clause}
            ),
            geo_classified AS (
                SELECT
                    seg.IssuerID,
                    seg.FISCAL_YEAR,
                    QUARTER(seg.PERIOD_END_DATE) AS FISCAL_QUARTER,
                    seg.SEGMENT_REVENUE,
                    COALESCE(gc.RISK_WEIGHT, 0.5) AS RISK_WEIGHT,
                    COALESCE(gc.RISK_TIER, 'MEDIUM') AS RISK_TIER
                FROM {database_name}.{schema_name}.FACT_SEC_SEGMENTS seg
                LEFT JOIN {database_name}.{schema_name}.DIM_GEO_RISK_CLASSIFICATION gc
                    ON seg.GEOGRAPHY = gc.GEOGRAPHY
                WHERE seg.GEOGRAPHY IS NOT NULL
                  AND seg.SEGMENT_REVENUE IS NOT NULL
                  AND seg.SEGMENT_REVENUE > 0
            ),
            geo_scores AS (
                SELECT
                    IssuerID,
                    FISCAL_YEAR,
                    FISCAL_QUARTER,
                    SUM(SEGMENT_REVENUE) AS TOTAL_REVENUE,
                    SUM(CASE WHEN RISK_TIER = 'HIGH' THEN SEGMENT_REVENUE ELSE 0 END) AS HIGH_RISK_REVENUE,
                    SUM(CASE WHEN RISK_TIER = 'MEDIUM' THEN SEGMENT_REVENUE ELSE 0 END) AS MEDIUM_RISK_REVENUE,
                    SUM(SEGMENT_REVENUE * RISK_WEIGHT) / NULLIF(SUM(SEGMENT_REVENUE), 0) AS WEIGHTED_RISK_RATIO,
                    MAX(CASE WHEN RISK_TIER = 'HIGH' THEN SEGMENT_REVENUE ELSE 0 END) / NULLIF(SUM(SEGMENT_REVENUE), 0) AS MAX_HIGH_RISK_CONCENTRATION
                FROM geo_classified
                GROUP BY IssuerID, FISCAL_YEAR, FISCAL_QUARTER
            ),
            geo_final AS (
                SELECT
                    IssuerID,
                    FISCAL_YEAR,
                    FISCAL_QUARTER,
                    LEAST(100, GREATEST(0, ROUND(
                        WEIGHTED_RISK_RATIO * 100
                        + CASE WHEN MAX_HIGH_RISK_CONCENTRATION > 0.3 THEN 15 ELSE 0 END
                        + CASE WHEN MAX_HIGH_RISK_CONCENTRATION > 0.5 THEN 10 ELSE 0 END
                    ))) AS GEO_RISK_SCORE
                FROM geo_scores
            )
            SELECT
                a.IssuerID,
                a.SecurityID,
                a.PRIMARY_TICKER,
                a.FISCAL_YEAR,
                a.FISCAL_QUARTER,
                a.EVENT_TIMESTAMP,
                LEAST(100, GREATEST(0, COALESCE(a.AI_EXPOSURE_SCORE, 0))) AS AI_EXPOSURE_SCORE,
                COALESCE(g.GEO_RISK_SCORE, 10) AS GEO_RISK_SCORE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM ai_scores a
            LEFT JOIN geo_final g
                ON a.IssuerID = g.IssuerID
                AND a.FISCAL_YEAR = g.FISCAL_YEAR
                AND a.FISCAL_QUARTER = g.FISCAL_QUARTER
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_TRANSCRIPT_NLP_SCORES").collect()[0]['CNT']
        issuer_count = session.sql(f"SELECT COUNT(DISTINCT IssuerID) as cnt FROM {database_name}.{schema_name}.FACT_TRANSCRIPT_NLP_SCORES").collect()[0]['CNT']
        avg_ai = session.sql(f"SELECT ROUND(AVG(AI_EXPOSURE_SCORE), 1) as avg FROM {database_name}.{schema_name}.FACT_TRANSCRIPT_NLP_SCORES").collect()[0]['AVG']
        avg_geo = session.sql(f"SELECT ROUND(AVG(GEO_RISK_SCORE), 1) as avg FROM {database_name}.{schema_name}.FACT_TRANSCRIPT_NLP_SCORES").collect()[0]['AVG']
        
        log_detail(f"  FACT_TRANSCRIPT_NLP_SCORES: {count:,} records, {issuer_count} issuers, avg AI={avg_ai}, avg Geo={avg_geo} (AI_COMPLETE)")
        
        exec_wh = config.WAREHOUSES['execution']['name']
        session.sql(f"USE WAREHOUSE {exec_wh}").collect()
        
    except RuntimeError:
        raise
    except Exception as e:
        exec_wh = config.WAREHOUSES['execution']['name']
        try:
            session.sql(f"USE WAREHOUSE {exec_wh}").collect()
        except Exception:
            pass
        raise RuntimeError(f"Error building FACT_TRANSCRIPT_NLP_SCORES: {e}")


def build_fact_policy_rates(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_POLICY_RATES from BIS central bank policy rate data.
    
    Creates a physical table with central bank policy rates from the
    Bank for International Settlements data in Cybersyn.
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    log_detail("Building FACT_POLICY_RATES from BIS data...")
    
    limit_clause = "LIMIT 50000" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_POLICY_RATES AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY t.DATE, a.GEO_NAME) AS RATE_ID,
                t.DATE,
                a.GEO_NAME AS COUNTRY,
                a.VARIABLE_NAME,
                t.VALUE AS POLICY_RATE,
                a.UNIT,
                a.FREQUENCY,
                'BANK_FOR_INTERNATIONAL_SETTLEMENTS' AS DATA_SOURCE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM {real_db}.{real_schema}.BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES t
            JOIN {real_db}.{real_schema}.BANK_FOR_INTERNATIONAL_SETTLEMENTS_ATTRIBUTES a
                ON t.VARIABLE = a.VARIABLE
            WHERE UPPER(a.VARIABLE_NAME) LIKE '%POLICY%RATE%'
            AND t.DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
            AND t.VALUE IS NOT NULL
            {limit_clause}
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_POLICY_RATES").collect()[0]['CNT']
        country_count = session.sql(f"SELECT COUNT(DISTINCT COUNTRY) as cnt FROM {database_name}.{schema_name}.FACT_POLICY_RATES").collect()[0]['CNT']
        
        log_detail(f"  FACT_POLICY_RATES: {count:,} records, {country_count} countries (REAL DATA)")
        
    except Exception as e:
        raise RuntimeError(f"Error building FACT_POLICY_RATES: {e}")


def build_fact_fx_rates(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_FX_RATES from Cybersyn FX rate data.
    
    Creates a physical table with foreign exchange rates for major currencies vs USD.
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    fx_rates_table = config.REAL_DATA_SOURCES['tables']['fx_rates']['table']
    
    log_detail("Building FACT_FX_RATES from Cybersyn data...")
    
    limit_clause = "LIMIT 50000" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_FX_RATES AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY DATE, QUOTE_CURRENCY_ID) AS FX_RATE_ID,
                DATE,
                BASE_CURRENCY_ID,
                QUOTE_CURRENCY_ID,
                VALUE AS FX_RATE,
                '{fx_rates_table}' AS DATA_SOURCE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM {real_db}.{real_schema}.{fx_rates_table}
            WHERE BASE_CURRENCY_ID = 'USD'
            AND QUOTE_CURRENCY_ID IN ('EUR', 'GBP', 'JPY', 'CHF', 'CNY', 'MXN', 'BRL', 'AUD', 'CAD', 'KRW', 'INR')
            AND DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
            AND VALUE IS NOT NULL
            {limit_clause}
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_FX_RATES").collect()[0]['CNT']
        currency_count = session.sql(f"SELECT COUNT(DISTINCT QUOTE_CURRENCY_ID) as cnt FROM {database_name}.{schema_name}.FACT_FX_RATES").collect()[0]['CNT']
        
        log_detail(f"  FACT_FX_RATES: {count:,} records, {currency_count} currencies (REAL DATA)")
        
    except Exception as e:
        raise RuntimeError(f"Error building FACT_FX_RATES: {e}")


def build_fact_economic_indicators(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_ECONOMIC_INDICATORS from FRED economic data via Cybersyn.
    
    Creates a physical table with US economic indicators (GDP, CPI, unemployment).
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    economic_indicators_table = config.REAL_DATA_SOURCES['tables']['fred_economic_indicators']['table']
    economic_indicators_attrs = config.REAL_DATA_SOURCES['tables']['fred_economic_indicators']['attributes_table']
    
    log_detail("Building FACT_ECONOMIC_INDICATORS from FRED data...")
    
    limit_clause = "LIMIT 100000" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_ECONOMIC_INDICATORS AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY t.DATE, a.VARIABLE_NAME) AS INDICATOR_ID,
                t.DATE,
                'US' AS COUNTRY,
                a.VARIABLE_NAME AS INDICATOR_NAME,
                a.MEASURE,
                a.UNIT,
                t.VALUE,
                a.RELEASE_SOURCE,
                a.SEASONALLY_ADJUSTED,
                CASE 
                    WHEN UPPER(a.VARIABLE_NAME) LIKE '%GDP%' OR UPPER(a.MEASURE) LIKE '%GDP%' THEN 'GDP'
                    WHEN UPPER(a.VARIABLE_NAME) LIKE '%INFLATION%' OR UPPER(a.VARIABLE_NAME) LIKE '%CPI%' 
                         OR UPPER(a.MEASURE) LIKE '%CONSUMER PRICE%' THEN 'INFLATION'
                    WHEN UPPER(a.VARIABLE_NAME) LIKE '%UNEMPLOYMENT%' OR UPPER(a.MEASURE) LIKE '%UNEMPLOYMENT%' THEN 'UNEMPLOYMENT'
                    WHEN UPPER(a.VARIABLE_NAME) LIKE '%INTEREST%' OR UPPER(a.VARIABLE_NAME) LIKE '%FED FUND%' THEN 'INTEREST_RATE'
                    WHEN UPPER(a.VARIABLE_NAME) LIKE '%EMPLOYMENT%' OR UPPER(a.MEASURE) LIKE '%PAYROLL%' THEN 'EMPLOYMENT'
                    ELSE 'OTHER'
                END AS INDICATOR_TYPE,
                'CYBERSYN_FINANCIAL_ECONOMIC_INDICATORS' AS DATA_SOURCE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM {real_db}.{real_schema}.{economic_indicators_table} t
            JOIN {real_db}.{real_schema}.{economic_indicators_attrs} a
                ON t.VARIABLE = a.VARIABLE
            WHERE t.DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
            AND t.VALUE IS NOT NULL
            AND (
                UPPER(a.VARIABLE_NAME) LIKE '%GDP%'
                OR UPPER(a.VARIABLE_NAME) LIKE '%INFLATION%'
                OR UPPER(a.VARIABLE_NAME) LIKE '%CPI%'
                OR UPPER(a.VARIABLE_NAME) LIKE '%UNEMPLOYMENT%'
                OR UPPER(a.VARIABLE_NAME) LIKE '%FED FUND%'
                OR UPPER(a.MEASURE) LIKE '%CONSUMER PRICE%'
                OR UPPER(a.MEASURE) LIKE '%GROSS DOMESTIC PRODUCT%'
            )
            {limit_clause}
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_ECONOMIC_INDICATORS").collect()[0]['CNT']
        type_count = session.sql(f"SELECT COUNT(DISTINCT INDICATOR_TYPE) as cnt FROM {database_name}.{schema_name}.FACT_ECONOMIC_INDICATORS").collect()[0]['CNT']
        
        log_detail(f"  FACT_ECONOMIC_INDICATORS: {count:,} records, {type_count} indicator types (REAL DATA)")
        
    except Exception as e:
        raise RuntimeError(f"Error building FACT_ECONOMIC_INDICATORS: {e}")


def build_fact_treasury_yields(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_TREASURY_YIELDS from US Treasury par yield curve data.
    
    Creates a physical table with daily Treasury par yield curve rates across
    14 maturities (1-month to 30-year). Sourced from US_TREASURY_TIMESERIES.
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    log_detail("Building FACT_TREASURY_YIELDS from US Treasury data...")
    
    limit_clause = "LIMIT 50000" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_TREASURY_YIELDS AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY t.DATE, a.VARIABLE_NAME) AS YIELD_ID,
                t.DATE,
                a.VARIABLE_NAME AS MATURITY_LABEL,
                CASE
                    WHEN a.VARIABLE_NAME LIKE '%1-MO%' THEN '1M'
                    WHEN a.VARIABLE_NAME LIKE '%1.5-MO%' THEN '1.5M'
                    WHEN a.VARIABLE_NAME LIKE '%2-MO%' THEN '2M'
                    WHEN a.VARIABLE_NAME LIKE '%3-MO%' THEN '3M'
                    WHEN a.VARIABLE_NAME LIKE '%4-MO%' THEN '4M'
                    WHEN a.VARIABLE_NAME LIKE '%6-MO%' THEN '6M'
                    WHEN a.VARIABLE_NAME LIKE '%1-YR%' THEN '1Y'
                    WHEN a.VARIABLE_NAME LIKE '%2-YR%' THEN '2Y'
                    WHEN a.VARIABLE_NAME LIKE '%3-YR%' THEN '3Y'
                    WHEN a.VARIABLE_NAME LIKE '%5-YR%' THEN '5Y'
                    WHEN a.VARIABLE_NAME LIKE '%7-YR%' THEN '7Y'
                    WHEN a.VARIABLE_NAME LIKE '%10-YR%' THEN '10Y'
                    WHEN a.VARIABLE_NAME LIKE '%20-YR%' THEN '20Y'
                    WHEN a.VARIABLE_NAME LIKE '%30-YR%' THEN '30Y'
                    ELSE 'OTHER'
                END AS MATURITY_CODE,
                CASE
                    WHEN a.VARIABLE_NAME LIKE '%1-MO%' THEN 0.083
                    WHEN a.VARIABLE_NAME LIKE '%1.5-MO%' THEN 0.125
                    WHEN a.VARIABLE_NAME LIKE '%2-MO%' THEN 0.167
                    WHEN a.VARIABLE_NAME LIKE '%3-MO%' THEN 0.25
                    WHEN a.VARIABLE_NAME LIKE '%4-MO%' THEN 0.333
                    WHEN a.VARIABLE_NAME LIKE '%6-MO%' THEN 0.5
                    WHEN a.VARIABLE_NAME LIKE '%1-YR%' THEN 1.0
                    WHEN a.VARIABLE_NAME LIKE '%2-YR%' THEN 2.0
                    WHEN a.VARIABLE_NAME LIKE '%3-YR%' THEN 3.0
                    WHEN a.VARIABLE_NAME LIKE '%5-YR%' THEN 5.0
                    WHEN a.VARIABLE_NAME LIKE '%7-YR%' THEN 7.0
                    WHEN a.VARIABLE_NAME LIKE '%10-YR%' THEN 10.0
                    WHEN a.VARIABLE_NAME LIKE '%20-YR%' THEN 20.0
                    WHEN a.VARIABLE_NAME LIKE '%30-YR%' THEN 30.0
                    ELSE NULL
                END AS MATURITY_YEARS,
                t.VALUE AS YIELD_PCT,
                'US_TREASURY' AS DATA_SOURCE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM {real_db}.{real_schema}.US_TREASURY_TIMESERIES t
            JOIN {real_db}.{real_schema}.US_TREASURY_ATTRIBUTES a
                ON t.VARIABLE = a.VARIABLE
            WHERE a.VARIABLE_NAME LIKE 'Treasury Par Yield Curve Rate%'
            AND t.DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
            AND t.VALUE IS NOT NULL
            {limit_clause}
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_TREASURY_YIELDS").collect()[0]['CNT']
        maturity_count = session.sql(f"SELECT COUNT(DISTINCT MATURITY_CODE) as cnt FROM {database_name}.{schema_name}.FACT_TREASURY_YIELDS").collect()[0]['CNT']
        
        log_detail(f"  FACT_TREASURY_YIELDS: {count:,} records, {maturity_count} maturities (REAL DATA)")
        
    except Exception as e:
        raise RuntimeError(f"Error building FACT_TREASURY_YIELDS: {e}")


def build_fact_country_emissions(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_COUNTRY_EMISSIONS from Climate Watch GHG emissions data.
    
    Creates a physical table with annual greenhouse gas emissions by country and sector.
    Provides real environmental data backdrop for ESG analysis scenarios.
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    log_detail("Building FACT_COUNTRY_EMISSIONS from Climate Watch data...")
    
    limit_clause = "LIMIT 50000" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_COUNTRY_EMISSIONS AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY t.DATE DESC, t.GEO_ID, a.SECTOR) AS EMISSION_ID,
                t.GEO_ID,
                REPLACE(t.GEO_ID, 'country/', '') AS COUNTRY_ISO3,
                t.DATE AS YEAR_DATE,
                YEAR(t.DATE) AS EMISSION_YEAR,
                a.EMISSION_TYPE,
                a.SECTOR,
                t.VALUE AS EMISSIONS_TCO2E,
                ROUND(t.VALUE / 1000000, 2) AS EMISSIONS_MT_CO2E,
                t.UNIT,
                a.SOURCE AS DATA_SOURCE_NAME,
                'CLIMATE_WATCH' AS DATA_SOURCE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM {real_db}.{real_schema}.CLIMATE_WATCH_TIMESERIES t
            JOIN {real_db}.{real_schema}.CLIMATE_WATCH_ATTRIBUTES a ON t.VARIABLE = a.VARIABLE
            WHERE a.SOURCE = 'Climate Watch'
            AND a.SCENARIO IS NULL
            AND t.GEO_ID LIKE 'country/%'
            AND t.DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY + 5}, CURRENT_DATE())
            AND t.VALUE IS NOT NULL
            {limit_clause}
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_COUNTRY_EMISSIONS").collect()[0]['CNT']
        country_count = session.sql(f"SELECT COUNT(DISTINCT COUNTRY_ISO3) as cnt FROM {database_name}.{schema_name}.FACT_COUNTRY_EMISSIONS").collect()[0]['CNT']
        
        log_detail(f"  FACT_COUNTRY_EMISSIONS: {count:,} records, {country_count} countries (REAL DATA)")
        
    except Exception as e:
        raise RuntimeError(f"Error building FACT_COUNTRY_EMISSIONS: {e}")


def build_fact_insider_transactions(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_INSIDER_TRANSACTIONS from SEC Form 4 insider trading data.
    
    Creates a physical table with insider buy/sell transactions for demo companies.
    Sourced from SEC_INSIDER_TRADING_SECURITIES_INDEX.
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    log_detail("Building FACT_INSIDER_TRANSACTIONS from SEC Form 4 data...")
    
    from utils.demo_helpers import get_demo_company_ciks
    from utils.sql import safe_sql_tuple
    cik_tuple = safe_sql_tuple(get_demo_company_ciks())
    
    limit_clause = "LIMIT 10000" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{curated_schema}.FACT_INSIDER_TRANSACTIONS AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY sit.TRANSACTION_DATE DESC, sit.ISSUER_NAME) AS INSIDER_TX_ID,
                sit.ISSUER_CIK AS CIK,
                sit.ISSUER_NAME,
                sit.ISSUER_TRADING_SYMBOL AS TICKER,
                sit.FORM_TYPE,
                sit.TRANSACTION_DATE,
                sit.SECURITY_TYPE,
                sit.SECURITY_TITLE,
                sit.TRANSACTION_TYPE,
                sit.TRANSACTION_ACTION,
                sit.TRANSACTION_SHARES,
                sit.TRANSACTION_PRICE_PER_SHARE,
                sit.POST_TRANSACTION_SHARES_OWNED,
                sit.OWNERSHIP,
                ds.SecurityID,
                'SEC_INSIDER_TRADING' AS DATA_SOURCE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM {real_db}.{real_schema}.SEC_INSIDER_TRADING_SECURITIES_INDEX sit
            LEFT JOIN {database_name}.{curated_schema}.DIM_ISSUER di
                ON sit.ISSUER_CIK = di.CIK
            LEFT JOIN {database_name}.{curated_schema}.DIM_SECURITY ds
                ON di.IssuerID = ds.IssuerID
            WHERE sit.ISSUER_CIK IN {cik_tuple}
            AND sit.TRANSACTION_DATE IS NOT NULL
            AND sit.TRANSACTION_DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
            {limit_clause}
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{curated_schema}.FACT_INSIDER_TRANSACTIONS").collect()[0]['CNT']
        company_count = session.sql(f"SELECT COUNT(DISTINCT ISSUER_NAME) as cnt FROM {database_name}.{curated_schema}.FACT_INSIDER_TRANSACTIONS").collect()[0]['CNT']
        
        log_detail(f"  FACT_INSIDER_TRANSACTIONS: {count:,} records, {company_count} companies (REAL DATA)")
        
    except Exception as e:
        raise RuntimeError(f"Error building FACT_INSIDER_TRANSACTIONS: {e}")


def build_fact_institutional_holdings(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_INSTITUTIONAL_HOLDINGS from SEC 13F institutional filings.
    
    Creates a physical table tracking institutional ownership of demo companies.
    Sourced from SEC_HOLDING_FILING_INDEX + SEC_HOLDING_FILING_ATTRIBUTES.
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    curated_schema = config.DATABASE['schemas']['curated']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    log_detail("Building FACT_INSTITUTIONAL_HOLDINGS from SEC 13F data...")
    
    from utils.demo_helpers import get_demo_company_tickers
    from utils.sql import safe_sql_tuple
    ticker_tuple = safe_sql_tuple(get_demo_company_tickers())
    
    limit_clause = "LIMIT 50000" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{curated_schema}.FACT_INSTITUTIONAL_HOLDINGS AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY idx.FILING_DATE DESC, idx.FILING_MANAGER_NAME, att.PRIMARY_TICKER) AS HOLDING_ID,
                idx.FILING_MANAGER_NAME AS INSTITUTION_NAME,
                idx.FILING_DATE,
                idx.REPORTING_PERIOD_QUARTER,
                idx.REPORTING_PERIOD_YEAR,
                att.PRIMARY_TICKER AS TICKER,
                att.SECURITY_NAME,
                att.MARKET_VALUE AS MARKET_VALUE_USD,
                att.NUMBER_OF_SHARES AS SHARES_HELD,
                att.PUTCALL AS PUT_CALL,
                att.INVESTMENT_DISCRETION,
                att.ASSET_CLASS,
                ds.SecurityID,
                'SEC_13F' AS DATA_SOURCE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM {real_db}.{real_schema}.SEC_HOLDING_FILING_INDEX idx
            JOIN {real_db}.{real_schema}.SEC_HOLDING_FILING_ATTRIBUTES att
                ON idx.ADSH = att.ADSH
            LEFT JOIN {database_name}.{curated_schema}.DIM_SECURITY ds
                ON att.PRIMARY_TICKER = ds.Ticker
            WHERE idx.FILING_DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
            AND att.PRIMARY_TICKER IN {ticker_tuple}
            {limit_clause}
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{curated_schema}.FACT_INSTITUTIONAL_HOLDINGS").collect()[0]['CNT']
        institution_count = session.sql(f"SELECT COUNT(DISTINCT INSTITUTION_NAME) as cnt FROM {database_name}.{curated_schema}.FACT_INSTITUTIONAL_HOLDINGS").collect()[0]['CNT']
        
        log_detail(f"  FACT_INSTITUTIONAL_HOLDINGS: {count:,} records, {institution_count} institutions (REAL DATA)")
        
    except Exception as e:
        raise RuntimeError(f"Error building FACT_INSTITUTIONAL_HOLDINGS: {e}")


def build_fact_dividends(session: Session, test_mode: bool = False) -> None:
    """
    Build FACT_DIVIDENDS from real SEC 8-K dividend announcements or synthetic data.
    
    When config.MARKET_DATA['synthetic_dividends'] is True, skips the AI_EXTRACT
    step and generates synthetic dividends directly for known dividend-paying companies.
    
    When False, uses AI_EXTRACT to parse cash dividend details from 8-K filing text.
    Falls back to synthetic dividends if no real 8-K cash dividend filings are found.
    """
    verify_real_data_access(session)
    
    database_name = config.DATABASE['name']
    schema_name = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    
    if config.MARKET_DATA.get('synthetic_dividends', False):
        log_detail("Building FACT_DIVIDENDS (synthetic mode - skipping AI_EXTRACT)")
        _generate_synthetic_dividends(session, database_name, schema_name, curated_schema)
        return
    
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    
    sec_filing_text_table = config.REAL_DATA_SOURCES['tables']['sec_filing_text']['table']
    
    log_detail("Building FACT_DIVIDENDS from SEC 8-K filings using AI_EXTRACT...")
    
    limit_clause = "LIMIT 100" if test_mode else ""
    
    try:
        session.sql(f"""
            CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_DIVIDENDS AS
            WITH our_companies AS (
                SELECT 
                    di.IssuerID,
                    di.CIK,
                    di.LegalName,
                    ds.SecurityID
                FROM {database_name}.{curated_schema}.DIM_ISSUER di
                JOIN {database_name}.{curated_schema}.DIM_SECURITY ds 
                    ON di.IssuerID = ds.IssuerID
                WHERE di.CIK IS NOT NULL
                  AND ds.AssetClass = 'Equity'
            ),
            dividend_filings AS (
                SELECT 
                    srt.CIK,
                    srt.PERIOD_END_DATE AS FILING_DATE,
                    srt.VALUE AS FILING_TEXT
                FROM {real_db}.{real_schema}.{sec_filing_text_table} srt
                WHERE srt.VARIABLE_NAME = '8-K Filing Text'
                  AND UPPER(srt.VALUE) LIKE '%DIVIDEND%'
                  AND srt.PERIOD_END_DATE >= DATEADD(year, -{config.YEARS_OF_HISTORY}, CURRENT_DATE())
                  AND srt.CIK IN (SELECT CIK FROM our_companies)
                {limit_clause}
            ),
            extracted_dividends AS (
                SELECT 
                    oc.IssuerID,
                    oc.SecurityID,
                    oc.LegalName,
                    df.CIK,
                    df.FILING_DATE,
                    AI_EXTRACT(
                        df.FILING_TEXT,
                        OBJECT_CONSTRUCT(
                            'dividend_per_share', 'Extract ONLY if this announces a regular CASH dividend (money paid per share). Return as a decimal dollar amount (e.g., 0.25 for 25 cents, 0.90 for 90 cents, 1.50 for $1.50). Always convert cents to dollars. Return null if this is a stock split, spin-off, stock dividend, or special distribution of shares.',
                            'record_date', 'The record date for the cash dividend in ISO format YYYY-MM-DD. If only a quarter is mentioned (e.g., "Q3 2023"), use the last day of that quarter (03-31, 06-30, 09-30, 12-31). Return null if no cash dividend.',
                            'payment_date', 'The payment date for the cash dividend in ISO format YYYY-MM-DD. If only a quarter is mentioned, use the last day of that quarter. Return null if no cash dividend.',
                            'declaration_date', 'The date the cash dividend was declared in ISO format YYYY-MM-DD. If only a quarter is mentioned, use the last day of that quarter. Return null if no cash dividend.',
                            'dividend_type', 'Return "quarterly" for regular quarterly dividend, "annual" for annual dividend, "special" for one-time special cash dividend. Return null if not a cash dividend.'
                        )
                    ) AS EXTRACTED
                FROM dividend_filings df
                JOIN our_companies oc ON oc.CIK = df.CIK
            ),
            typed_dividends AS (
                SELECT 
                    IssuerID,
                    SecurityID,
                    CIK,
                    TRY_TO_DATE(EXTRACTED:response:declaration_date::STRING) AS DECLARATION_DATE,
                    TRY_CAST(EXTRACTED:response:dividend_per_share::STRING AS FLOAT) AS DIVIDEND_PER_SHARE,
                    TRY_TO_DATE(EXTRACTED:response:record_date::STRING) AS RECORD_DATE,
                    TRY_TO_DATE(EXTRACTED:response:payment_date::STRING) AS PAYMENT_DATE,
                    UPPER(EXTRACTED:response:dividend_type::STRING) AS DIVIDEND_TYPE,
                    FILING_DATE
                FROM extracted_dividends
                WHERE EXTRACTED:error IS NULL
                  AND EXTRACTED:response:dividend_per_share IS NOT NULL
                  AND EXTRACTED:response:dividend_per_share::STRING NOT IN ('null', 'None', 'N/A', '')
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY IssuerID, COALESCE(DECLARATION_DATE, FILING_DATE)) AS DIVIDEND_ID,
                IssuerID,
                SecurityID,
                CIK,
                COALESCE(DECLARATION_DATE, FILING_DATE) AS DECLARATION_DATE,
                DIVIDEND_PER_SHARE,
                CASE 
                    WHEN DAYOFWEEK(DATEADD(day, -1, RECORD_DATE)) = 1 THEN DATEADD(day, -3, RECORD_DATE)
                    WHEN DAYOFWEEK(DATEADD(day, -1, RECORD_DATE)) = 7 THEN DATEADD(day, -2, RECORD_DATE)
                    ELSE DATEADD(day, -1, RECORD_DATE)
                END AS EX_DATE,
                RECORD_DATE,
                PAYMENT_DATE,
                'USD' AS CURRENCY,
                COALESCE(DIVIDEND_TYPE, 'QUARTERLY') AS DIVIDEND_TYPE,
                'SEC_8K_AI_EXTRACT' AS DATA_SOURCE,
                CURRENT_TIMESTAMP() AS LOADED_AT
            FROM typed_dividends
            WHERE DIVIDEND_PER_SHARE > 0
              AND DIVIDEND_PER_SHARE < 50
              AND RECORD_DATE IS NOT NULL
        """).collect()
        
        count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_DIVIDENDS").collect()[0]['CNT']
        issuer_count = session.sql(f"SELECT COUNT(DISTINCT IssuerID) as cnt FROM {database_name}.{schema_name}.FACT_DIVIDENDS").collect()[0]['CNT']
        
        log_detail(f"  FACT_DIVIDENDS: {count:,} records for {issuer_count} issuers (from 8-K + AI_EXTRACT)")
        
        if count == 0:
            log_warning("  No 8-K cash dividend filings found - generating synthetic dividends")
            _generate_synthetic_dividends(session, database_name, schema_name, curated_schema)
        
    except Exception as e:
        raise RuntimeError(f"Error building FACT_DIVIDENDS: {e}")


def _generate_synthetic_dividends(session: Session, database_name: str, schema_name: str, curated_schema: str) -> None:
    """Generate synthetic dividend data for known dividend-paying companies."""
    dividend_payers = {
        'AAPL': 0.24, 'MSFT': 0.75, 'JNJ': 1.24, 'PG': 0.94, 'KO': 0.46,
        'PEP': 1.27, 'MO': 0.98, 'T': 0.28, 'VZ': 0.67, 'IBM': 1.67,
        'INTC': 0.13, 'CSCO': 0.39, 'CMCSA': 0.31, 'AXP': 0.60, 'GE': 0.08,
        'HON': 1.08, 'RTX': 0.59, 'CAT': 1.30, 'MMM': 1.51, 'ABT': 0.55,
        'MRK': 0.77, 'PFE': 0.42, 'UNH': 1.88, 'HD': 2.09, 'MCD': 1.67,
        'NKE': 0.37, 'WMT': 0.21, 'JPM': 1.15, 'BAC': 0.24, 'WFC': 0.35,
        'C': 0.53, 'GS': 2.75, 'MS': 0.85, 'BLK': 5.00, 'SBUX': 0.57,
        'CVX': 1.51, 'XOM': 0.95,
    }
    
    ticker_list = "', '".join(dividend_payers.keys())
    case_statements = ' '.join([f"WHEN '{t}' THEN {a}" for t, a in dividend_payers.items() if a > 0])
    
    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{schema_name}.FACT_DIVIDENDS AS
        WITH dividend_payers AS (
            SELECT ds.SecurityID, di.IssuerID, di.CIK, ds.Ticker,
                CASE ds.Ticker {case_statements} ELSE 0.25 END AS QUARTERLY_DIVIDEND
            FROM {database_name}.{curated_schema}.DIM_SECURITY ds
            JOIN {database_name}.{curated_schema}.DIM_ISSUER di ON ds.IssuerID = di.IssuerID
            WHERE ds.Ticker IN ('{ticker_list}') AND ds.AssetClass = 'Equity'
        ),
        quarters AS (
            SELECT DATEADD(quarter, -ROW_NUMBER() OVER (ORDER BY SEQ4()), CURRENT_DATE()) AS quarter_end
            FROM TABLE(GENERATOR(ROWCOUNT => 20))
        ),
        dividend_events AS (
            SELECT dp.*, q.quarter_end,
                DATEADD(day, -45, q.quarter_end) AS declaration_date,
                DATEADD(day, -14, q.quarter_end) AS record_date,
                q.quarter_end AS payment_date
            FROM dividend_payers dp CROSS JOIN quarters q
            WHERE dp.QUARTERLY_DIVIDEND > 0
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY IssuerID, declaration_date) AS DIVIDEND_ID,
            IssuerID, SecurityID, CIK,
            declaration_date AS DECLARATION_DATE,
            QUARTERLY_DIVIDEND AS DIVIDEND_PER_SHARE,
            CASE 
                WHEN DAYOFWEEK(DATEADD(day, -1, record_date)) = 1 THEN DATEADD(day, -3, record_date)
                WHEN DAYOFWEEK(DATEADD(day, -1, record_date)) = 7 THEN DATEADD(day, -2, record_date)
                ELSE DATEADD(day, -1, record_date)
            END AS EX_DATE,
            record_date AS RECORD_DATE,
            payment_date AS PAYMENT_DATE,
            'USD' AS CURRENCY,
            'QUARTERLY' AS DIVIDEND_TYPE,
            'SYNTHETIC' AS DATA_SOURCE,
            CURRENT_TIMESTAMP() AS LOADED_AT
        FROM dividend_events
    """).collect()
    
    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{schema_name}.FACT_DIVIDENDS").collect()[0]['CNT']
    issuer_count = session.sql(f"SELECT COUNT(DISTINCT IssuerID) as cnt FROM {database_name}.{schema_name}.FACT_DIVIDENDS").collect()[0]['CNT']
    log_detail(f"  FACT_DIVIDENDS: {count:,} synthetic records for {issuer_count} issuers")


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
            CASE DATA_ITEM_ID
                WHEN 1001 THEN 'Revenue'
                WHEN 1005 THEN 'Net Income'
                WHEN 1008 THEN 'EBITDA'
                WHEN 1011 THEN 'TAM'
                WHEN 1012 THEN 'Customer Count'
                WHEN 4009 THEN 'NRR'
            END as ESTIMATE_TYPE,
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


def build_fact_credit_sector_benchmarks(session: Session, test_mode: bool = False):
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    random.seed(config.RNG_SEED + 10)

    sectors = ['Healthcare', 'Technology', 'Industrials', 'Consumer', 'Energy', 'Materials']
    sources = ['PitchBook LCD', 'Bloomberg', 'S&P Capital IQ']
    base_spreads = {'Healthcare': 425, 'Technology': 475, 'Industrials': 400, 'Consumer': 450, 'Energy': 500, 'Materials': 410}
    base_leverages = {'Healthcare': 5.2, 'Technology': 5.8, 'Industrials': 4.5, 'Consumer': 5.0, 'Energy': 4.2, 'Materials': 4.3}

    quarters_back = 4 if test_mode else 16
    rows = []
    for sector in sectors:
        for q in range(quarters_back):
            report_date = datetime.now().replace(day=1) - timedelta(days=90 * q)
            report_date = report_date.replace(day=1).date() if hasattr(report_date, 'date') else report_date

            spread = base_spreads[sector] + random.randint(-50, 75) + (q * random.randint(0, 5))
            leverage = round(base_leverages[sector] + random.uniform(-0.5, 0.5), 2)
            default_rate = round(random.uniform(0.5, 3.5) + (q * 0.05), 2)
            recovery = round(random.uniform(55, 75), 2)
            icr = round(random.uniform(1.8, 3.5), 2)
            issuance = round(random.uniform(5, 25), 2)
            repricing = round(random.uniform(2, 15), 2)
            source = random.choice(sources)
            rows.append(f"('{sector}', '{report_date}', {spread}, {leverage}, {default_rate}, {recovery}, {icr}, {issuance}, {repricing}, '{source}')")

    session.sql(f"""
        CREATE OR REPLACE TABLE {database_name}.{market_data_schema}.FACT_CREDIT_SECTOR_BENCHMARKS AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY 1) AS BenchmarkID,
            t.$1 AS Sector, t.$2::DATE AS ReportDate, t.$3::INT AS AvgSpread_BPS,
            t.$4::DECIMAL(6,2) AS MedianLeverage, t.$5::DECIMAL(6,2) AS DefaultRate_PCT,
            t.$6::DECIMAL(6,2) AS RecoveryRate_PCT, t.$7::DECIMAL(6,2) AS AvgInterestCoverage,
            t.$8::DECIMAL(12,2) AS NewIssuanceVolume_BN, t.$9::DECIMAL(12,2) AS RepricingVolume_BN,
            t.$10 AS Source
        FROM VALUES {', '.join(rows)} AS t
    """).collect()

    count = session.sql(f"SELECT COUNT(*) as cnt FROM {database_name}.{market_data_schema}.FACT_CREDIT_SECTOR_BENCHMARKS").collect()[0]['CNT']
    log_success(f"  FACT_CREDIT_SECTOR_BENCHMARKS: {count} sector benchmark records")
