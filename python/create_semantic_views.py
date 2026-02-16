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
Semantic Views Builder for SAM Demo

This module creates all Cortex Analyst semantic views for portfolio analytics,
research, quantitative analysis, implementation planning, SEC filings, supply chain, 
and middle office operations.
"""

from snowflake.snowpark import Session
from typing import List
import config
from logging_utils import log_detail, log_warning, log_error

def create_semantic_views(session: Session, scenarios: List[str] = None):
    """Create semantic views required for the specified scenarios."""
    
    # Always create the main analyst view
    try:
        create_analyst_semantic_view(session)
    except Exception as e:
        log_error(f" Failed to create SAM_ANALYST_VIEW: {e}")
        raise
    
    # Create implementation semantic view for portfolio management
    if scenarios and ('portfolio_copilot' in scenarios or 'sales_advisor' in scenarios):
        try:
            create_implementation_semantic_view(session)
        except Exception as e:
            log_warning(f"  Warning: Could not create implementation semantic view: {e}")
    
    # Create supply chain semantic view for risk verification
    if scenarios and 'portfolio_copilot' in scenarios:
        try:
            create_supply_chain_semantic_view(session)
        except Exception as e:
            log_warning(f"  Warning: Could not create supply chain semantic view: {e}")
    
    # Create middle office semantic view for operations monitoring
    if scenarios and 'middle_office_copilot' in scenarios:
        try:
            create_middle_office_semantic_view(session)
        except Exception as e:
            log_warning(f"  Warning: Could not create middle office semantic view: {e}")
    
    # Create compliance semantic view for breach tracking and monitoring
    if scenarios and 'compliance_advisor' in scenarios:
        try:
            create_compliance_semantic_view(session)
        except Exception as e:
            log_warning(f"  Warning: Could not create compliance semantic view: {e}")
    
    # Create executive semantic view for firm-wide KPIs and client analytics
    if scenarios and 'executive_copilot' in scenarios:
        try:
            create_executive_semantic_view(session)
        except Exception as e:
            log_warning(f"  Warning: Could not create executive semantic view: {e}")
    
    # Create fundamentals semantic view for MARKET_DATA financial analysis
    if scenarios and 'research_copilot' in scenarios:
        try:
            create_fundamentals_semantic_view(session)
        except Exception as e:
            log_warning(f"  Warning: Could not create fundamentals semantic view: {e}")
            log_warning(f"Run with --scope structured first to generate MARKET_DATA tables")
    
    # Create real SEC data semantic views (required)
    try:
        create_real_stock_prices_semantic_view(session)
    except Exception as e:
        log_warning(f"  Warning: Could not create real stock prices semantic view: {e}")
    
    try:
        create_sec_financials_semantic_view(session)
    except Exception as e:
        log_warning(f"  Warning: Could not create SEC financials semantic view: {e}")

def create_analyst_semantic_view(session: Session):
    """Create main portfolio analytics semantic view (SAM_ANALYST_VIEW).
    
    This is the primary semantic view for portfolio analytics, now including:
    - Portfolio holdings with ESG scores and performance returns
    - Factor exposures (Value, Growth, Quality, Momentum, etc.) - consolidated from SAM_QUANT_VIEW
    - Benchmark holdings - consolidated from SAM_QUANT_VIEW
    - Benchmark performance returns (MTD, QTD, YTD) for portfolio vs benchmark comparison
    """
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_ANALYST_VIEW
	TABLES (
		HOLDINGS AS {config.DATABASE['name']}.CURATED.V_HOLDINGS_WITH_ESG
			PRIMARY KEY (HOLDINGDATE, PORTFOLIOID, SECURITYID) 
			WITH SYNONYMS=('positions','investments','allocations','holdings') 
			COMMENT='Daily portfolio holdings with ESG scores. Each holding includes latest Overall ESG grade and score. When no time period is provided always get the latest value by date.',
		PORTFOLIOS AS {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
			PRIMARY KEY (PORTFOLIOID) 
			WITH SYNONYMS=('funds','strategies','mandates','portfolios') 
			COMMENT='Investment portfolios and fund information',
		SECURITIES AS {config.DATABASE['name']}.CURATED.DIM_SECURITY
			PRIMARY KEY (SECURITYID) 
			WITH SYNONYMS=('companies','stocks','bonds','instruments','securities') 
			COMMENT='Master security reference data',
		ISSUERS AS {config.DATABASE['name']}.CURATED.DIM_ISSUER
			PRIMARY KEY (ISSUERID) 
			WITH SYNONYMS=('issuers','entities','corporates') 
			COMMENT='Issuer and corporate hierarchy data',
		FACTOR_EXPOSURES AS {config.DATABASE['name']}.CURATED.FACT_FACTOR_EXPOSURES
			PRIMARY KEY (SECURITYID, EXPOSURE_DATE, FACTOR_NAME)
			WITH SYNONYMS=('factors','loadings','exposures','factor_data')
			COMMENT='Factor exposures and loadings (Value, Growth, Quality, Momentum, etc.)',
		BENCHMARK_HOLDINGS AS {config.DATABASE['name']}.CURATED.FACT_BENCHMARK_HOLDINGS
			PRIMARY KEY (HOLDING_DATE, BENCHMARKID, SECURITYID)
			WITH SYNONYMS=('benchmark_positions','index_holdings','benchmark_weights')
			COMMENT='Benchmark constituent holdings and weights',
		BENCHMARK_PERFORMANCE AS {config.DATABASE['name']}.CURATED.FACT_BENCHMARK_PERFORMANCE
			PRIMARY KEY (BENCHMARKPERFID)
			WITH SYNONYMS=('benchmark_returns','benchmark_performance','index_returns','index_performance')
			COMMENT='Benchmark-level performance returns (MTD, QTD, YTD) for comparison with portfolio returns',
		BENCHMARKS AS {config.DATABASE['name']}.CURATED.DIM_BENCHMARK
			PRIMARY KEY (BENCHMARKID)
			WITH SYNONYMS=('indices','indexes','benchmark_master')
			COMMENT='Benchmark/index master data',
		PORTFOLIO_BENCHMARK AS {config.DATABASE['name']}.CURATED.V_PORTFOLIO_BENCHMARK_COMPARISON
			PRIMARY KEY (PORTFOLIOID, PERFORMANCEDATE)
			WITH SYNONYMS=('portfolio_vs_benchmark','performance_comparison','relative_performance','active_returns')
			COMMENT='Pre-joined portfolio returns with benchmark returns for side-by-side comparison. Includes active returns (portfolio - benchmark).'
	)
	RELATIONSHIPS (
		HOLDINGS_TO_PORTFOLIOS AS HOLDINGS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		HOLDINGS_TO_SECURITIES AS HOLDINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID),
		FACTORS_TO_SECURITIES AS FACTOR_EXPOSURES(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		BENCHMARK_TO_SECURITIES AS BENCHMARK_HOLDINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		BENCHMARK_PERF_TO_BENCHMARKS AS BENCHMARK_PERFORMANCE(BENCHMARKID) REFERENCES BENCHMARKS(BENCHMARKID),
		PORTFOLIOS_TO_BENCHMARKS AS PORTFOLIOS(BENCHMARKID) REFERENCES BENCHMARKS(BENCHMARKID)
	)
	DIMENSIONS (
		-- Portfolio dimensions
		PORTFOLIOS.PORTFOLIONAME AS PortfolioName WITH SYNONYMS=('fund_name','strategy_name','portfolio_name') COMMENT='Portfolio or fund name',
		PORTFOLIOS.STRATEGY AS Strategy WITH SYNONYMS=('investment_strategy','portfolio_strategy','strategy_type','value_strategy','growth_strategy') COMMENT='Investment strategy: Value, Growth, ESG, Core, Multi-Asset, Income',
		
		-- Security dimensions  
		SECURITIES.DESCRIPTION AS Description WITH SYNONYMS=('company','security_name','description') COMMENT='Security description or company name',
		SECURITIES.TICKER AS Ticker WITH SYNONYMS=('ticker_symbol','symbol','primary_ticker') COMMENT='Primary trading symbol',
		SECURITIES.ASSETCLASS AS AssetClass WITH SYNONYMS=('instrument_type','security_type','asset_class') COMMENT='Asset class: Equity, Corporate Bond, ETF',
		
		-- Issuer dimensions (for enhanced analysis)
		ISSUERS.LegalName AS LEGALNAME WITH SYNONYMS=('issuer_name','legal_name','company_name') COMMENT='Legal issuer name',
		ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry','industry_type','sic_industry','business_type','industry_description','industry_classification') COMMENT='SIC industry classification with granular descriptions (e.g., Semiconductors and related devices, Computer programming services, Motor vehicles and car bodies). Use this for industry-level filtering and analysis.',
		ISSUERS.GICS_Sector AS GICS_SECTOR WITH SYNONYMS=('gics','gics_sector','sector','sector_classification','sector_allocation') COMMENT='GICS Level 1 sector classification (e.g., Information Technology, Health Care, Financials, Consumer Discretionary). Use for sector allocation analysis and concentration risk.',
		ISSUERS.CountryOfIncorporation AS COUNTRYOFINCORPORATION WITH SYNONYMS=('domicile','country_of_risk','country') COMMENT='Country of incorporation using 2-letter ISO codes (e.g., TW for Taiwan, US for United States, GB for United Kingdom)',
		
		-- Time dimensions
		HOLDINGS.HOLDINGDATE AS HoldingDate WITH SYNONYMS=('position_date','as_of_date','date') COMMENT='Holdings as-of date',
		HOLDINGS.HOLDING_MONTH AS DATE_TRUNC('MONTH', HOLDINGDATE) WITH SYNONYMS=('month','monthly','month_end') COMMENT='Monthly aggregation of holding dates for trend analysis',
		HOLDINGS.HOLDING_QUARTER AS DATE_TRUNC('QUARTER', HOLDINGDATE) WITH SYNONYMS=('quarter','quarterly','quarter_end') COMMENT='Quarterly aggregation for quarterly reporting',
		
		-- ESG dimension (from enriched holdings view)
		HOLDINGS.ESGGrade AS ESG_GRADE WITH SYNONYMS=('esg_rating','sustainability_grade','esg_grade','overall_esg_grade') COMMENT='Overall ESG grade on MSCI scale: AAA/AA/A (leader), BBB/BB/B (average), CCC (laggard). ESG-labelled portfolios require minimum BBB.',
		
		-- Factor dimensions (consolidated from SAM_QUANT_VIEW)
		FACTOR_EXPOSURES.FactorName AS FACTOR_NAME WITH SYNONYMS=('factor','factor_type','loading_type') COMMENT='Factor name: Market, Size, Value, Momentum, Growth, Quality, Volatility',
		FACTOR_EXPOSURES.ExposureDate AS EXPOSURE_DATE WITH SYNONYMS=('factor_date','loading_date','exposure_date') COMMENT='Factor exposure measurement date',
		
		-- Benchmark dimensions
		BENCHMARKS.BenchmarkName AS BENCHMARKNAME WITH SYNONYMS=('benchmark','index_name','index','benchmark_name') COMMENT='Benchmark/index name: S&P 500, MSCI ACWI, Nasdaq 100',
		BENCHMARK_PERFORMANCE.BENCHMARK_PERF_DATE AS PerformanceDate WITH SYNONYMS=('benchmark_date','index_date','benchmark_performance_date') COMMENT='Benchmark performance measurement date',
		
		-- Portfolio vs Benchmark comparison dimensions (from pre-joined view)
		PORTFOLIO_BENCHMARK.COMPARISON_PORTFOLIO AS PortfolioName WITH SYNONYMS=('compared_portfolio','performance_portfolio') COMMENT='Portfolio name in comparison view',
		PORTFOLIO_BENCHMARK.COMPARISON_BENCHMARK AS BenchmarkName WITH SYNONYMS=('compared_benchmark','performance_benchmark') COMMENT='Benchmark name in comparison view',
		PORTFOLIO_BENCHMARK.COMPARISON_DATE AS PerformanceDate WITH SYNONYMS=('comparison_date','performance_date') COMMENT='Date for portfolio vs benchmark comparison'
	)
	METRICS (
		-- Core position metrics
		HOLDINGS.TOTAL_MARKET_VALUE AS SUM(MarketValue_Base) WITH SYNONYMS=('exposure','total_exposure','aum','market_value','position_value') COMMENT='Total market value in base currency',
		HOLDINGS.HOLDING_COUNT AS COUNT(SecurityID) WITH SYNONYMS=('position_count','number_of_holdings','holding_count','count') COMMENT='Count of portfolio positions',
		
		-- Portfolio weight metrics  
		HOLDINGS.PORTFOLIO_WEIGHT AS SUM(PortfolioWeight) WITH SYNONYMS=('weight','allocation','portfolio_weight') COMMENT='Portfolio weight as decimal',
		HOLDINGS.PORTFOLIO_WEIGHT_PCT AS SUM(PortfolioWeight) * 100 WITH SYNONYMS=('weight_percent','allocation_percent','percentage_weight') COMMENT='Portfolio weight as percentage',
		
		-- Issuer-level metrics (enhanced capability)
		HOLDINGS.ISSUER_EXPOSURE AS SUM(MarketValue_Base) WITH SYNONYMS=('issuer_total','issuer_value','issuer_exposure') COMMENT='Total exposure to issuer across all securities',
		
		-- Concentration metrics
		HOLDINGS.MAX_POSITION_WEIGHT AS MAX(PortfolioWeight) WITH SYNONYMS=('largest_position','max_weight','concentration') COMMENT='Largest single position weight',
		
		-- ESG metric (from enriched holdings view)
		HOLDINGS.ESG_SCORE AS AVG(ESG_SCORE) WITH SYNONYMS=('esg_score','sustainability_score','esg_rating_value','overall_esg_score') COMMENT='Overall ESG score (0-100 scale)',
		
		-- Performance metrics (from enriched holdings view with returns)
		HOLDINGS.QTD_RETURN AS AVG(QTD_RETURN_PCT) WITH SYNONYMS=('quarterly_return','qtd_performance','quarter_to_date_return','quarterly_performance') COMMENT='Quarter-to-date return percentage for positions',
		HOLDINGS.YTD_RETURN AS AVG(YTD_RETURN_PCT) WITH SYNONYMS=('ytd_return','ytd_performance','year_to_date_return','annual_performance') COMMENT='Year-to-date return percentage for positions',
		HOLDINGS.MTD_RETURN AS AVG(MTD_RETURN_PCT) WITH SYNONYMS=('monthly_return','mtd_performance','month_to_date_return','monthly_performance') COMMENT='Month-to-date return percentage for positions',
		
		-- Factor metrics (consolidated from SAM_QUANT_VIEW)
		FACTOR_EXPOSURES.FACTOR_EXPOSURE AS SUM(EXPOSURE_VALUE) WITH SYNONYMS=('factor_loading','loading','factor_score') COMMENT='Factor exposure value',
		FACTOR_EXPOSURES.FACTOR_R_SQUARED AS AVG(R_SQUARED) WITH SYNONYMS=('r_squared','model_fit','factor_rsq') COMMENT='Factor model R-squared',
		FACTOR_EXPOSURES.MOMENTUM_SCORE AS AVG(CASE WHEN FACTOR_NAME = 'Momentum' THEN EXPOSURE_VALUE ELSE NULL END) WITH SYNONYMS=('momentum','momentum_factor','momentum_loading') COMMENT='Momentum factor exposure',
		FACTOR_EXPOSURES.QUALITY_SCORE AS AVG(CASE WHEN FACTOR_NAME = 'Quality' THEN EXPOSURE_VALUE ELSE NULL END) WITH SYNONYMS=('quality','quality_factor','quality_loading') COMMENT='Quality factor exposure',
		FACTOR_EXPOSURES.VALUE_SCORE AS AVG(CASE WHEN FACTOR_NAME = 'Value' THEN EXPOSURE_VALUE ELSE NULL END) WITH SYNONYMS=('value','value_factor','value_loading') COMMENT='Value factor exposure',
		FACTOR_EXPOSURES.GROWTH_SCORE AS AVG(CASE WHEN FACTOR_NAME = 'Growth' THEN EXPOSURE_VALUE ELSE NULL END) WITH SYNONYMS=('growth','growth_factor','growth_loading') COMMENT='Growth factor exposure',
		
		-- Benchmark metrics (consolidated from SAM_QUANT_VIEW)
		BENCHMARK_HOLDINGS.BenchmarkWeight AS SUM(BENCHMARK_WEIGHT) WITH SYNONYMS=('benchmark_allocation','index_weight','benchmark_percentage') COMMENT='Benchmark constituent weight',
		
		-- Benchmark performance metrics (for portfolio vs benchmark comparison)
		BENCHMARK_PERFORMANCE.BENCHMARK_MTD_RETURN AS AVG(MTD_RETURN_PCT) WITH SYNONYMS=('benchmark_mtd','index_mtd','benchmark_monthly_return','index_monthly_return') COMMENT='Benchmark month-to-date return percentage',
		BENCHMARK_PERFORMANCE.BENCHMARK_QTD_RETURN AS AVG(QTD_RETURN_PCT) WITH SYNONYMS=('benchmark_qtd','index_qtd','benchmark_quarterly_return','index_quarterly_return') COMMENT='Benchmark quarter-to-date return percentage',
		BENCHMARK_PERFORMANCE.BENCHMARK_YTD_RETURN AS AVG(YTD_RETURN_PCT) WITH SYNONYMS=('benchmark_ytd','index_ytd','benchmark_annual_return','index_annual_return') COMMENT='Benchmark year-to-date return percentage',
		BENCHMARK_PERFORMANCE.BENCHMARK_ANNUALIZED_RETURN AS AVG(ANNUALIZED_RETURN_PCT) WITH SYNONYMS=('benchmark_annualized','index_annualized','benchmark_1y_return') COMMENT='Benchmark annualized return percentage',
		
		-- Portfolio vs Benchmark comparison metrics (from pre-joined view - all in one row)
		PORTFOLIO_BENCHMARK.COMPARISON_PORTFOLIO_QTD AS AVG(PORTFOLIO_QTD_RETURN) WITH SYNONYMS=('portfolio_qtd_vs_benchmark','compared_portfolio_qtd') COMMENT='Portfolio QTD return in comparison view',
		PORTFOLIO_BENCHMARK.COMPARISON_PORTFOLIO_YTD AS AVG(PORTFOLIO_YTD_RETURN) WITH SYNONYMS=('portfolio_ytd_vs_benchmark','compared_portfolio_ytd') COMMENT='Portfolio YTD return in comparison view',
		PORTFOLIO_BENCHMARK.COMPARISON_BENCHMARK_QTD AS AVG(BENCHMARK_QTD_RETURN) WITH SYNONYMS=('benchmark_qtd_vs_portfolio','compared_benchmark_qtd') COMMENT='Benchmark QTD return in comparison view',
		PORTFOLIO_BENCHMARK.COMPARISON_BENCHMARK_YTD AS AVG(BENCHMARK_YTD_RETURN) WITH SYNONYMS=('benchmark_ytd_vs_portfolio','compared_benchmark_ytd') COMMENT='Benchmark YTD return in comparison view',
		PORTFOLIO_BENCHMARK.ACTIVE_QTD AS AVG(ACTIVE_QTD_RETURN) WITH SYNONYMS=('active_qtd_return','relative_qtd','outperformance_qtd','alpha_qtd') COMMENT='Active QTD return (portfolio - benchmark)',
		PORTFOLIO_BENCHMARK.ACTIVE_YTD AS AVG(ACTIVE_YTD_RETURN) WITH SYNONYMS=('active_ytd_return','relative_ytd','outperformance_ytd','alpha_ytd') COMMENT='Active YTD return (portfolio - benchmark)',
		PORTFOLIO_BENCHMARK.COMPARISON_AUM AS SUM(PORTFOLIO_AUM) WITH SYNONYMS=('compared_aum','performance_aum') COMMENT='Portfolio AUM in comparison view'
	)
	COMMENT='Multi-asset semantic view for portfolio analytics with issuer hierarchy, ESG scores, performance returns, factor exposures, benchmark weights, and benchmark performance returns for portfolio vs benchmark comparison'
	WITH EXTENSION (CA='{{"tables":[{{"name":"HOLDINGS","dimensions":[{{"name":"ESGGrade"}}],"metrics":[{{"name":"ESG_SCORE"}},{{"name":"HOLDING_COUNT"}},{{"name":"ISSUER_EXPOSURE"}},{{"name":"MAX_POSITION_WEIGHT"}},{{"name":"PORTFOLIO_WEIGHT"}},{{"name":"PORTFOLIO_WEIGHT_PCT"}},{{"name":"TOTAL_MARKET_VALUE"}},{{"name":"QTD_RETURN"}},{{"name":"YTD_RETURN"}},{{"name":"MTD_RETURN"}}],"time_dimensions":[{{"name":"HOLDINGDATE"}},{{"name":"HOLDING_MONTH"}},{{"name":"HOLDING_QUARTER"}}]}},{{"name":"ISSUERS","dimensions":[{{"name":"CountryOfIncorporation"}},{{"name":"Industry"}},{{"name":"LegalName"}}]}},{{"name":"PORTFOLIOS","dimensions":[{{"name":"PORTFOLIONAME"}},{{"name":"STRATEGY"}}]}},{{"name":"SECURITIES","dimensions":[{{"name":"ASSETCLASS"}},{{"name":"DESCRIPTION"}},{{"name":"TICKER"}}]}},{{"name":"FACTOR_EXPOSURES","dimensions":[{{"name":"FactorName"}},{{"name":"ExposureDate"}}],"metrics":[{{"name":"FACTOR_EXPOSURE"}},{{"name":"FACTOR_R_SQUARED"}},{{"name":"MOMENTUM_SCORE"}},{{"name":"QUALITY_SCORE"}},{{"name":"VALUE_SCORE"}},{{"name":"GROWTH_SCORE"}}],"time_dimensions":[{{"name":"ExposureDate"}}]}},{{"name":"BENCHMARK_HOLDINGS","metrics":[{{"name":"BenchmarkWeight"}}]}},{{"name":"BENCHMARK_PERFORMANCE","dimensions":[{{"name":"BenchmarkDate"}}],"metrics":[{{"name":"BENCHMARK_MTD_RETURN"}},{{"name":"BENCHMARK_QTD_RETURN"}},{{"name":"BENCHMARK_YTD_RETURN"}},{{"name":"BENCHMARK_ANNUALIZED_RETURN"}}],"time_dimensions":[{{"name":"BenchmarkDate"}}]}},{{"name":"BENCHMARKS","dimensions":[{{"name":"BenchmarkName"}}]}},{{"name":"PORTFOLIO_BENCHMARK","dimensions":[{{"name":"COMPARISON_PORTFOLIO"}},{{"name":"COMPARISON_BENCHMARK"}}],"metrics":[{{"name":"COMPARISON_PORTFOLIO_QTD"}},{{"name":"COMPARISON_PORTFOLIO_YTD"}},{{"name":"COMPARISON_BENCHMARK_QTD"}},{{"name":"COMPARISON_BENCHMARK_YTD"}},{{"name":"ACTIVE_QTD"}},{{"name":"ACTIVE_YTD"}},{{"name":"COMPARISON_AUM"}}],"time_dimensions":[{{"name":"COMPARISON_DATE"}}]}}],"relationships":[{{"name":"HOLDINGS_TO_PORTFOLIOS"}},{{"name":"HOLDINGS_TO_SECURITIES"}},{{"name":"SECURITIES_TO_ISSUERS"}},{{"name":"FACTORS_TO_SECURITIES"}},{{"name":"BENCHMARK_TO_SECURITIES"}},{{"name":"BENCHMARK_PERF_TO_BENCHMARKS"}},{{"name":"PORTFOLIOS_TO_BENCHMARKS"}}],"verified_queries":[{{"name":"portfolio_holdings","question":"What are the portfolio holdings?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_ANALYST_VIEW METRICS TOTAL_MARKET_VALUE, PORTFOLIO_WEIGHT_PCT, HOLDING_COUNT)","use_as_onboarding_question":true}},{{"name":"esg_scores","question":"What are the ESG scores?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_ANALYST_VIEW METRICS ESG_SCORE DIMENSIONS ESGGrade)","use_as_onboarding_question":true}},{{"name":"portfolio_returns","question":"What are the portfolio returns?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_ANALYST_VIEW METRICS QTD_RETURN, YTD_RETURN, MTD_RETURN)","use_as_onboarding_question":false}},{{"name":"factor_exposures","question":"What are the factor exposures?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_ANALYST_VIEW METRICS VALUE_SCORE, GROWTH_SCORE, MOMENTUM_SCORE, QUALITY_SCORE DIMENSIONS FactorName)","use_as_onboarding_question":false}},{{"name":"benchmark_performance","question":"What is the benchmark performance?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_ANALYST_VIEW METRICS BENCHMARK_QTD_RETURN, BENCHMARK_YTD_RETURN DIMENSIONS BenchmarkName)","use_as_onboarding_question":true}},{{"name":"portfolio_vs_benchmark","question":"How does portfolio performance compare to benchmark?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_ANALYST_VIEW METRICS COMPARISON_PORTFOLIO_QTD, COMPARISON_PORTFOLIO_YTD, COMPARISON_BENCHMARK_QTD, COMPARISON_BENCHMARK_YTD, ACTIVE_QTD, ACTIVE_YTD DIMENSIONS COMPARISON_PORTFOLIO, COMPARISON_BENCHMARK)","use_as_onboarding_question":true}}],"module_custom_instructions":{{"sql_generation":"CRITICAL: Always filter holdings to the latest date unless the user explicitly requests historical data or trends. Use WHERE HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM HOLDINGS) in EVERY query that does not have an explicit date filter or date dimension. This prevents aggregation across multiple months which causes incorrect totals. For portfolio weight calculations, always multiply by 100 to show percentages. When calculating issuer exposure, aggregate MARKETVALUE_BASE across all securities of the same issuer. Always round market values to 2 decimal places and portfolio weights to 1 decimal place. ESG_SCORE and ESG_GRADE columns are directly available on the HOLDINGS table for each position. Performance metrics (QTD_RETURN_PCT, YTD_RETURN_PCT, MTD_RETURN_PCT) are also directly available on HOLDINGS for return calculations. NEVER use UNION ALL to combine different report sections with different columns - this causes type mismatch errors. For multi-section reports like client reports, pick ONE primary section (e.g., top holdings) as the main result set. For factor analysis, use the FACTOR_EXPOSURES table with FACTOR_NAME dimension to filter specific factors. For portfolio factor exposure queries, join current portfolio holdings with their most recent factor exposures using WHERE EXPOSURE_DATE = (SELECT MAX(EXPOSURE_DATE) FROM FACTOR_EXPOSURES). For benchmark performance queries, use BENCHMARK_PERFORMANCE table with BENCHMARK_QTD_RETURN, BENCHMARK_YTD_RETURN, BENCHMARK_MTD_RETURN metrics. Filter by BenchmarkName dimension for specific benchmarks (S&P 500, MSCI ACWI, Nasdaq 100). For portfolio vs benchmark comparison, use the PORTFOLIO_BENCHMARK table which has pre-joined portfolio and benchmark returns in the same row. Use COMPARISON_PORTFOLIO_QTD, COMPARISON_BENCHMARK_QTD, ACTIVE_QTD metrics with COMPARISON_PORTFOLIO and COMPARISON_BENCHMARK dimensions.","question_categorization":"IMPORTANT: Unless the user explicitly asks for historical trends or time series data, always assume they want current holdings (latest date only). If users ask about \\'funds\\' or \\'portfolios\\', treat these as the same concept referring to investment portfolios. ESG data and performance returns are included directly in holdings. For performance questions, use the QTD_RETURN, YTD_RETURN, or MTD_RETURN metrics. For multi-section report requests, focus on the most important section (typically top holdings with performance metrics) rather than trying to combine incompatible result sets. For factor analysis questions (value, growth, momentum, quality), use the FACTOR_EXPOSURES metrics. Factor data is available for all equity securities. For benchmark performance questions (benchmark returns, index performance, how did the benchmark do), use BENCHMARK_QTD_RETURN, BENCHMARK_YTD_RETURN, BENCHMARK_MTD_RETURN metrics from BENCHMARK_PERFORMANCE table. For portfolio vs benchmark comparison questions, use the PORTFOLIO_BENCHMARK table metrics: COMPARISON_PORTFOLIO_QTD, COMPARISON_PORTFOLIO_YTD, COMPARISON_BENCHMARK_QTD, COMPARISON_BENCHMARK_YTD, ACTIVE_QTD, ACTIVE_YTD. These provide side-by-side comparison in a single row with active return calculation."}}}}');
    """).collect()
    
    log_detail(" Created semantic view: SAM_ANALYST_VIEW")


def create_implementation_semantic_view(session: Session):
    """Create semantic view for portfolio implementation with trading, risk, and execution data."""
    # Check if implementation tables exist
    required_tables = [
        'FACT_TRANSACTION_COSTS',
        'FACT_PORTFOLIO_LIQUIDITY',
        'FACT_RISK_LIMITS',
        'FACT_TRADING_CALENDAR',
        'DIM_CLIENT_MANDATES',
        'FACT_TAX_IMPLICATIONS',
        'FACT_TRADE_SETTLEMENT'
    ]

    for table in required_tables:
        try:
            session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.{table} LIMIT 1").collect()
        except:
            log_warning(f"  Implementation table {table} not found, skipping implementation view creation")
            return
    # Create the implementation-focused semantic view
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_IMPLEMENTATION_VIEW
	TABLES (
		HOLDINGS AS {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR
			PRIMARY KEY (HOLDINGDATE, PORTFOLIOID, SECURITYID) 
			WITH SYNONYMS=('positions','investments','allocations','holdings') 
			COMMENT='Current portfolio holdings for implementation planning',
		PORTFOLIOS AS {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
			PRIMARY KEY (PORTFOLIOID) 
			WITH SYNONYMS=('funds','strategies','mandates','portfolios') 
			COMMENT='Portfolio information',
		SECURITIES AS {config.DATABASE['name']}.CURATED.DIM_SECURITY
			PRIMARY KEY (SECURITYID) 
			WITH SYNONYMS=('companies','stocks','instruments','securities') 
			COMMENT='Security reference data',
		TRANSACTION_COSTS AS {config.DATABASE['name']}.CURATED.FACT_TRANSACTION_COSTS
			PRIMARY KEY (SECURITYID, COST_DATE)
			WITH SYNONYMS=('trading_costs','execution_costs','cost_data','transaction_costs')
			COMMENT='Transaction costs and market microstructure data',
		PORTFOLIO_LIQUIDITY AS {config.DATABASE['name']}.CURATED.FACT_PORTFOLIO_LIQUIDITY
			PRIMARY KEY (PORTFOLIOID, LIQUIDITY_DATE)
			WITH SYNONYMS=('liquidity_info','liquidity','cash_position','liquidity_data')
			COMMENT='Portfolio cash and liquidity information',
		RISK_LIMITS AS {config.DATABASE['name']}.CURATED.FACT_RISK_LIMITS
			PRIMARY KEY (PORTFOLIOID, LIMITS_DATE)
			WITH SYNONYMS=('risk_budget','limits','constraints','risk_limits')
			COMMENT='Risk limits and budget utilization',
		TRADING_CALENDAR AS {config.DATABASE['name']}.CURATED.FACT_TRADING_CALENDAR
			PRIMARY KEY (SECURITYID, EVENT_DATE)
			WITH SYNONYMS=('calendar','events','blackouts','earnings_dates','trading_calendar')
			COMMENT='Trading calendar with blackout periods and events',
		CLIENT_MANDATES AS {config.DATABASE['name']}.CURATED.DIM_CLIENT_MANDATES
			PRIMARY KEY (PORTFOLIOID)
			WITH SYNONYMS=('client_constraints','approvals','client_rules','client_mandates')
			COMMENT='Client mandate requirements and approval thresholds',
		TAX_IMPLICATIONS AS {config.DATABASE['name']}.CURATED.FACT_TAX_IMPLICATIONS
			PRIMARY KEY (PORTFOLIOID, SECURITYID, TAX_DATE)
			WITH SYNONYMS=('tax_data','tax_records','gains_losses','tax_implications')
			COMMENT='Tax implications and cost basis data',
		TRADE_SETTLEMENT AS {config.DATABASE['name']}.CURATED.FACT_TRADE_SETTLEMENT
			PRIMARY KEY (SETTLEMENTID)
			WITH SYNONYMS=('settlement','settlement_data','trade_settlements','settlement_history')
			COMMENT='Trade settlement history with dates and status tracking'
	)
	RELATIONSHIPS (
		HOLDINGS_TO_PORTFOLIOS AS HOLDINGS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		HOLDINGS_TO_SECURITIES AS HOLDINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		TRANSACTION_COSTS_TO_SECURITIES AS TRANSACTION_COSTS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		PORTFOLIO_LIQUIDITY_TO_PORTFOLIOS AS PORTFOLIO_LIQUIDITY(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		RISK_LIMITS_TO_PORTFOLIOS AS RISK_LIMITS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		TRADING_CALENDAR_TO_SECURITIES AS TRADING_CALENDAR(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		CLIENT_MANDATES_TO_PORTFOLIOS AS CLIENT_MANDATES(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		TAX_IMPLICATIONS_TO_PORTFOLIOS AS TAX_IMPLICATIONS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		TAX_IMPLICATIONS_TO_SECURITIES AS TAX_IMPLICATIONS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		TRADE_SETTLEMENT_TO_PORTFOLIOS AS TRADE_SETTLEMENT(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		TRADE_SETTLEMENT_TO_SECURITIES AS TRADE_SETTLEMENT(SECURITYID) REFERENCES SECURITIES(SECURITYID)
	)
	DIMENSIONS (
		-- Portfolio dimensions
		PORTFOLIOS.PORTFOLIONAME AS PORTFOLIONAME WITH SYNONYMS=('fund_name','strategy_name','portfolio_name') COMMENT='Portfolio name',
		PORTFOLIOS.STRATEGY AS STRATEGY WITH SYNONYMS=('investment_strategy','portfolio_strategy') COMMENT='Investment strategy',
		
		-- Security dimensions  
		SECURITIES.DESCRIPTION AS DESCRIPTION WITH SYNONYMS=('security_name','security_description','name') COMMENT='Security description',
		SECURITIES.TICKER AS TICKER WITH SYNONYMS=('ticker_symbol','symbol','primary_ticker') COMMENT='Trading ticker symbol',
		
		-- Trading calendar dimensions
		TRADING_CALENDAR.EventType AS EVENT_TYPE WITH SYNONYMS=('event','calendar_event','trading_event') COMMENT='Trading calendar event type',
		TRADING_CALENDAR.IsBlackoutPeriod AS IS_BLACKOUT_PERIOD WITH SYNONYMS=('blackout','restricted','no_trading') COMMENT='Blackout period indicator',
		
		-- Tax dimensions
		TAX_IMPLICATIONS.TaxTreatment AS TAX_TREATMENT WITH SYNONYMS=('tax_type','treatment','tax_treatment') COMMENT='Tax treatment classification',
		TAX_IMPLICATIONS.TaxLossHarvestOpportunity AS TAX_LOSS_HARVEST_OPPORTUNITY WITH SYNONYMS=('tax_loss','harvest_opportunity','harvest_flag') COMMENT='Tax loss harvesting opportunity',
		
		-- Settlement dimensions (SemanticName AS DatabaseColumn)
		TRADE_SETTLEMENT.SETTLEMENT_STATUS AS STATUS WITH SYNONYMS=('settlement_status','trade_status') COMMENT='Settlement status (Settled, Pending, Failed)',
		TRADE_SETTLEMENT.EXECUTION_DATE AS TRADEDATE WITH SYNONYMS=('trade_date','order_date') COMMENT='Trade execution date',
		TRADE_SETTLEMENT.VALUE_DATE AS SETTLEMENTDATE WITH SYNONYMS=('settle_date','settlement_date') COMMENT='Settlement date (T+2 from trade date)'
	)
	METRICS (
		-- Position metrics
		HOLDINGS.TOTAL_MARKET_VALUE AS SUM(MarketValue_Base) WITH SYNONYMS=('market_value','position_value','exposure') COMMENT='Total market value of positions',
		HOLDINGS.PORTFOLIO_WEIGHT_PCT AS SUM(PortfolioWeight) * 100 WITH SYNONYMS=('weight_percent','allocation_percent','percentage_weight') COMMENT='Portfolio weight as percentage',
		
		-- Transaction cost metrics
		TRANSACTION_COSTS.AVG_BID_ASK_SPREAD AS AVG(BID_ASK_SPREAD_BPS) WITH SYNONYMS=('bid_ask_spread','spread','trading_spread') COMMENT='Average bid-ask spread in basis points',
		TRANSACTION_COSTS.AVG_MARKET_IMPACT AS AVG(MARKET_IMPACT_BPS_PER_1M) WITH SYNONYMS=('market_impact','trading_impact','execution_cost') COMMENT='Average market impact per $1M traded',
		TRANSACTION_COSTS.AVG_DAILY_VOLUME AS AVG(AVG_DAILY_VOLUME_M) WITH SYNONYMS=('daily_volume','trading_volume','volume') COMMENT='Average daily trading volume in millions',
		
		-- Liquidity metrics
		PORTFOLIO_LIQUIDITY.TOTAL_CASH_POSITION AS SUM(CASH_POSITION_USD) WITH SYNONYMS=('cash_available','available_cash','total_cash') COMMENT='Total available cash position',
		PORTFOLIO_LIQUIDITY.NET_CASH_FLOW AS SUM(NET_CASHFLOW_30D_USD) WITH SYNONYMS=('cash_flow','net_flow','expected_flow') COMMENT='Expected net cash flow over 30 days',
		PORTFOLIO_LIQUIDITY.AVG_LIQUIDITY_SCORE AS AVG(PORTFOLIO_LIQUIDITY_SCORE) WITH SYNONYMS=('liquidity_score','liquidity_rating','portfolio_liquidity') COMMENT='Portfolio liquidity score (1-10)',
		
		-- Risk metrics
		RISK_LIMITS.TRACKING_ERROR_UTILIZATION AS AVG(CURRENT_TRACKING_ERROR_PCT / TRACKING_ERROR_LIMIT_PCT) * 100 WITH SYNONYMS=('risk_utilization','tracking_error_usage','risk_budget_used') COMMENT='Tracking error budget utilization percentage',
		RISK_LIMITS.MAX_POSITION_LIMIT AS MAX(MAX_SINGLE_POSITION_PCT) * 100 WITH SYNONYMS=('concentration_limit','position_limit','max_weight_limit') COMMENT='Maximum single position limit as percentage',
		RISK_LIMITS.CURRENT_TRACKING_ERROR AS AVG(CURRENT_TRACKING_ERROR_PCT) WITH SYNONYMS=('current_risk','tracking_error','portfolio_risk') COMMENT='Current tracking error percentage',
		
		-- Tax metrics
		TAX_IMPLICATIONS.TOTAL_UNREALIZED_GAINS AS SUM(UNREALIZED_GAIN_LOSS_USD) WITH SYNONYMS=('unrealized_gains','capital_gains','unrealized_pnl') COMMENT='Total unrealized gains/losses',
		TAX_IMPLICATIONS.TOTAL_COST_BASIS AS SUM(COST_BASIS_USD) WITH SYNONYMS=('cost_basis','original_cost','tax_basis') COMMENT='Total cost basis for tax calculations',
		TAX_IMPLICATIONS.TAX_LOSS_HARVEST_VALUE AS SUM(CASE WHEN TAX_LOSS_HARVEST_OPPORTUNITY THEN ABS(UNREALIZED_GAIN_LOSS_USD) ELSE 0 END) WITH SYNONYMS=('harvest_value','tax_loss_value','loss_harvest_amount') COMMENT='Total value available for tax loss harvesting',
		
		-- Calendar metrics  
		TRADING_CALENDAR.BLACKOUT_DAYS AS COUNT(CASE WHEN IS_BLACKOUT_PERIOD THEN 1 END) WITH SYNONYMS=('blackout_count','restricted_days','no_trading_days') COMMENT='Count of blackout period days',
		TRADING_CALENDAR.AVG_VIX_FORECAST AS AVG(EXPECTED_VIX_LEVEL) WITH SYNONYMS=('volatility_forecast','vix_forecast','market_volatility') COMMENT='Average expected VIX volatility level',
		
		-- Settlement metrics
		TRADE_SETTLEMENT.TOTAL_SETTLEMENT_VALUE AS SUM(SETTLEMENTVALUE) WITH SYNONYMS=('settlement_amount','total_settlement','settlement_value') COMMENT='Total settlement value in USD',
		TRADE_SETTLEMENT.AVG_SETTLEMENT_DAYS AS AVG(DATEDIFF(day, TRADEDATE, SETTLEMENTDATE)) WITH SYNONYMS=('settlement_cycle','days_to_settle','settlement_days') COMMENT='Average days from trade to settlement (typically T+2)',
		TRADE_SETTLEMENT.PENDING_SETTLEMENTS AS COUNT(CASE WHEN STATUS = 'Pending' THEN 1 END) WITH SYNONYMS=('pending_count','unsettled_trades','pending_trades') COMMENT='Count of pending settlements',
		TRADE_SETTLEMENT.FAILED_SETTLEMENTS AS COUNT(CASE WHEN STATUS = 'Failed' THEN 1 END) WITH SYNONYMS=('failed_count','failed_trades','settlement_failures') COMMENT='Count of failed settlements'
	)
	COMMENT='Implementation semantic view with trading costs, liquidity, risk limits, settlement, and execution planning data';
    """).collect()

    log_detail(" Created semantic view: SAM_IMPLEMENTATION_VIEW")

def create_supply_chain_semantic_view(session: Session):
    """Create semantic view for supply chain risk analysis."""
    
    # Check if supply chain tables exist
    try:
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.DIM_SUPPLY_CHAIN_RELATIONSHIPS LIMIT 1").collect()
    except:
        log_detail("  Skipping SAM_SUPPLY_CHAIN_VIEW - tables not found")
        return
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_SUPPLY_CHAIN_VIEW
	TABLES (
		SUPPLY_CHAIN AS {config.DATABASE['name']}.CURATED.DIM_SUPPLY_CHAIN_RELATIONSHIPS
			PRIMARY KEY (RELATIONSHIPID) 
			WITH SYNONYMS=('supply_chain','dependencies','relationships','supplier_customer') 
			COMMENT='Supply chain relationships between issuers for risk analysis',
		COMPANY_ISSUERS AS {config.DATABASE['name']}.CURATED.DIM_ISSUER
			PRIMARY KEY (ISSUERID) 
			WITH SYNONYMS=('companies','company_issuers','primary_entities') 
			COMMENT='Company issuer information',
		COUNTERPARTY_ISSUERS AS {config.DATABASE['name']}.CURATED.DIM_ISSUER
			PRIMARY KEY (ISSUERID) 
			WITH SYNONYMS=('counterparties','suppliers','customers','trading_partners') 
			COMMENT='Counterparty issuer information',
		SECURITIES AS {config.DATABASE['name']}.CURATED.DIM_SECURITY
			PRIMARY KEY (SECURITYID) 
			WITH SYNONYMS=('securities','stocks') 
			COMMENT='Security master data',
		HOLDINGS AS {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR
			PRIMARY KEY (HOLDINGDATE, PORTFOLIOID, SECURITYID) 
			WITH SYNONYMS=('positions','holdings','portfolio_holdings') 
			COMMENT='Portfolio holdings for exposure calculation',
		PORTFOLIOS AS {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
			PRIMARY KEY (PORTFOLIOID) 
			WITH SYNONYMS=('portfolios','funds') 
			COMMENT='Portfolio information'
	)
	RELATIONSHIPS (
		SUPPLY_CHAIN_TO_COMPANY AS SUPPLY_CHAIN(COMPANY_ISSUERID) REFERENCES COMPANY_ISSUERS(ISSUERID),
		SUPPLY_CHAIN_TO_COUNTERPARTY AS SUPPLY_CHAIN(COUNTERPARTY_ISSUERID) REFERENCES COUNTERPARTY_ISSUERS(ISSUERID),
		SECURITIES_TO_COMPANY AS SECURITIES(ISSUERID) REFERENCES COMPANY_ISSUERS(ISSUERID),
		HOLDINGS_TO_SECURITIES AS HOLDINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		HOLDINGS_TO_PORTFOLIOS AS HOLDINGS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID)
	)
	DIMENSIONS (
		-- Company dimensions (US companies in portfolio)
		COMPANY_ISSUERS.CompanyName AS LEGALNAME WITH SYNONYMS=('company','company_name','us_company','portfolio_company','customer_company') COMMENT='US company legal name (the company with portfolio holdings)',
		COMPANY_ISSUERS.CompanyIndustry AS SIC_DESCRIPTION WITH SYNONYMS=('company_industry','customer_industry','us_industry') COMMENT='US company SIC industry classification',
		COMPANY_ISSUERS.CompanySector AS GICS_SECTOR WITH SYNONYMS=('company_sector','customer_sector','us_sector') COMMENT='US company GICS sector classification',
		COMPANY_ISSUERS.CompanyCountry AS COUNTRYOFINCORPORATION WITH SYNONYMS=('company_country','customer_country') COMMENT='US company country of incorporation using 2-letter ISO codes (e.g., US for United States)',
		
		-- Counterparty dimensions (Taiwan suppliers)
		COUNTERPARTY_ISSUERS.CounterpartyName AS LEGALNAME WITH SYNONYMS=('counterparty','supplier','supplier_name','taiwan_supplier','supplier_company') COMMENT='Supplier/counterparty legal name (e.g., Taiwan semiconductor suppliers like TSMC)',
		COUNTERPARTY_ISSUERS.CounterpartyIndustry AS SIC_DESCRIPTION WITH SYNONYMS=('counterparty_industry','supplier_industry','taiwan_industry','semiconductor_industry') COMMENT='Supplier SIC industry classification (e.g., Semiconductors and related devices)',
		COUNTERPARTY_ISSUERS.CounterpartySector AS GICS_SECTOR WITH SYNONYMS=('counterparty_sector','supplier_sector','taiwan_sector') COMMENT='Supplier GICS sector classification',
		COUNTERPARTY_ISSUERS.CounterpartyCountry AS COUNTRYOFINCORPORATION WITH SYNONYMS=('counterparty_country','supplier_country','taiwan') COMMENT='Supplier country of incorporation using 2-letter ISO codes (use TW for Taiwan, not Taiwan)',
		
		-- Relationship dimensions
		SUPPLY_CHAIN.RelationshipType AS RELATIONSHIPTYPE WITH SYNONYMS=('relationship','relationship_type','supplier_or_customer','dependency_type') COMMENT='Relationship type: Supplier (for upstream dependencies) or Customer (for downstream)',
		SUPPLY_CHAIN.CriticalityTier AS CRITICALITYTIER WITH SYNONYMS=('criticality','importance','tier','priority') COMMENT='Criticality tier indicating importance: Low, Medium, High, Critical',
		
		-- Portfolio dimensions
		PORTFOLIOS.PortfolioName AS PORTFOLIONAME WITH SYNONYMS=('portfolio','fund','portfolio_name') COMMENT='Portfolio name for exposure calculation',
		
		-- Time dimensions
		HOLDINGS.HoldingDate AS HOLDINGDATE WITH SYNONYMS=('date','position_date','as_of_date') COMMENT='Holdings date for current positions',
		SUPPLY_CHAIN.RelationshipStartDate AS STARTDATE WITH SYNONYMS=('start_date','effective_date','from_date','relationship_date') COMMENT='Start date of the supply chain relationship (use for filtering current relationships)'
	)
	METRICS (
		-- Relationship strength metrics (CostShare and RevenueShare are decimal values 0.0-1.0)
		SUPPLY_CHAIN.UPSTREAM_EXPOSURE AS SUM(COSTSHARE) WITH SYNONYMS=('upstream','cost_share','supplier_dependency','supplier_exposure') COMMENT='Upstream exposure as cost share from suppliers (0.0-1.0, represents percentage of costs from this supplier)',
		SUPPLY_CHAIN.DOWNSTREAM_EXPOSURE AS SUM(REVENUESHARE) WITH SYNONYMS=('downstream','revenue_share','customer_dependency','customer_exposure') COMMENT='Downstream exposure as revenue share to customers (0.0-1.0, represents percentage of revenue to this customer)',
		SUPPLY_CHAIN.MAX_DEPENDENCY AS MAX(GREATEST(COALESCE(COSTSHARE, 0), COALESCE(REVENUESHARE, 0))) WITH SYNONYMS=('max_dependency','largest_dependency','peak_exposure','max_share') COMMENT='Maximum single dependency (largest of cost or revenue share)',
		SUPPLY_CHAIN.AVG_DEPENDENCY AS AVG(GREATEST(COALESCE(COSTSHARE, 0), COALESCE(REVENUESHARE, 0))) WITH SYNONYMS=('avg_dependency','average_dependency','typical_exposure') COMMENT='Average dependency strength across relationships',
		
		-- First-order exposure (no decay - raw cost/revenue share for direct dependencies)
		SUPPLY_CHAIN.FIRST_ORDER_UPSTREAM AS SUM(COSTSHARE) WITH SYNONYMS=('first_order_cost','direct_supplier_exposure','hop1_upstream') COMMENT='First-order (direct) upstream exposure from suppliers - no decay applied',
		SUPPLY_CHAIN.FIRST_ORDER_DOWNSTREAM AS SUM(REVENUESHARE) WITH SYNONYMS=('first_order_revenue','direct_customer_exposure','hop1_downstream') COMMENT='First-order (direct) downstream exposure to customers - no decay applied',
		
		-- Second-order exposure (50% decay applied for indirect dependencies)
		SUPPLY_CHAIN.SECOND_ORDER_UPSTREAM AS SUM(COSTSHARE * 0.5) WITH SYNONYMS=('second_order_cost','indirect_supplier_exposure','hop2_upstream','decay_adjusted_upstream') COMMENT='Second-order upstream exposure with 50% decay factor applied (for hop 2 relationships)',
		SUPPLY_CHAIN.SECOND_ORDER_DOWNSTREAM AS SUM(REVENUESHARE * 0.5) WITH SYNONYMS=('second_order_revenue','indirect_customer_exposure','hop2_downstream','decay_adjusted_downstream') COMMENT='Second-order downstream exposure with 50% decay factor applied (for hop 2 relationships)',
		
		-- Portfolio exposure metrics (for second-order risk calculation)
		HOLDINGS.DIRECT_EXPOSURE AS SUM(MARKETVALUE_BASE) WITH SYNONYMS=('direct_exposure','direct_position','position_value','market_value') COMMENT='Direct portfolio exposure to US companies in base currency (USD)',
		HOLDINGS.PORTFOLIO_WEIGHT_PCT AS SUM(PORTFOLIOWEIGHT) * 100 WITH SYNONYMS=('weight','portfolio_weight','allocation_percent','weight_percent') COMMENT='Portfolio weight as percentage (0-100)',
		
		-- Relationship counts (for analysis)
		SUPPLY_CHAIN.RELATIONSHIP_COUNT AS COUNT(RELATIONSHIPID) WITH SYNONYMS=('relationship_count','dependency_count','connection_count','supplier_count','customer_count') COMMENT='Count of supply chain relationships (can filter by RelationshipType for suppliers vs customers)',
		SUPPLY_CHAIN.DISTINCT_COMPANIES AS COUNT(DISTINCT COMPANY_ISSUERID) WITH SYNONYMS=('company_count','us_company_count','affected_companies') COMMENT='Count of distinct US companies with dependencies',
		SUPPLY_CHAIN.DISTINCT_SUPPLIERS AS COUNT(DISTINCT COUNTERPARTY_ISSUERID) WITH SYNONYMS=('supplier_count','unique_suppliers','taiwan_supplier_count') COMMENT='Count of distinct suppliers/counterparties',
		
		-- Source confidence and data quality
		SUPPLY_CHAIN.AVG_CONFIDENCE AS AVG(SOURCECONFIDENCE) WITH SYNONYMS=('confidence','average_confidence','data_quality','reliability') COMMENT='Average source confidence score (0-100, higher is better)'
	)
	COMMENT='Supply chain semantic view for multi-hop dependency and second-order risk analysis';
    """).collect()
    
    log_detail(" Created semantic view: SAM_SUPPLY_CHAIN_VIEW")

def create_middle_office_semantic_view(session: Session):
    """Create semantic view for middle office operations analytics."""
    
    # Check if middle office tables exist
    try:
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRADE_SETTLEMENT LIMIT 1").collect()
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_RECONCILIATION LIMIT 1").collect()
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_NAV_CALCULATION LIMIT 1").collect()
    except:
        log_detail("  Skipping SAM_MIDDLE_OFFICE_VIEW - tables not found")
        return
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_MIDDLE_OFFICE_VIEW
	TABLES (
		SETTLEMENTS AS {config.DATABASE['name']}.CURATED.FACT_TRADE_SETTLEMENT
			PRIMARY KEY (SETTLEMENTID)
			WITH SYNONYMS=('settlements','trades','transactions')
			COMMENT='Trade settlement tracking',
		RECONCILIATIONS AS {config.DATABASE['name']}.CURATED.FACT_RECONCILIATION
			PRIMARY KEY (RECONCILIATIONID)
			WITH SYNONYMS=('recon','breaks','reconciliations')
			COMMENT='Reconciliation breaks and resolutions',
		NAV AS {config.DATABASE['name']}.CURATED.FACT_NAV_CALCULATION
			PRIMARY KEY (NAVID)
			WITH SYNONYMS=('nav','net_asset_value','valuations')
			COMMENT='NAV calculations',
		PORTFOLIOS AS {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
			PRIMARY KEY (PORTFOLIOID)
			WITH SYNONYMS=('funds','portfolios','strategies')
			COMMENT='Portfolio information',
		SECURITIES AS {config.DATABASE['name']}.CURATED.DIM_SECURITY
			PRIMARY KEY (SECURITYID)
			WITH SYNONYMS=('securities','stocks','instruments')
			COMMENT='Security master data',
		CUSTODIANS AS {config.DATABASE['name']}.CURATED.DIM_CUSTODIAN
			PRIMARY KEY (CUSTODIANID)
			WITH SYNONYMS=('custodians','banks','depositories')
			COMMENT='Custodian information',
		COUNTERPARTIES AS {config.DATABASE['name']}.CURATED.DIM_COUNTERPARTY
			PRIMARY KEY (COUNTERPARTYID)
			WITH SYNONYMS=('counterparties','brokers','trading_partners')
			COMMENT='Counterparty information for settlements',
		CORPORATE_ACTIONS AS {config.DATABASE['name']}.CURATED.FACT_CORPORATE_ACTIONS
			PRIMARY KEY (ACTIONID)
			WITH SYNONYMS=('corporate_actions','dividends','splits','mergers')
			COMMENT='Corporate action events',
		CASH_MOVEMENTS AS {config.DATABASE['name']}.CURATED.FACT_CASH_MOVEMENTS
			PRIMARY KEY (CASHMOVEMENTID)
			WITH SYNONYMS=('cash_flows','cash_movements','payments')
			COMMENT='Cash movement transactions',
		CASH_POSITIONS AS {config.DATABASE['name']}.CURATED.FACT_CASH_POSITIONS
			PRIMARY KEY (CASHPOSITIONID)
			WITH SYNONYMS=('cash_balances','cash_positions','liquidity')
			COMMENT='Daily cash position snapshots'
	)
	RELATIONSHIPS (
		SETTLEMENTS_TO_PORTFOLIOS AS SETTLEMENTS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		SETTLEMENTS_TO_SECURITIES AS SETTLEMENTS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		SETTLEMENTS_TO_CUSTODIANS AS SETTLEMENTS(CUSTODIANID) REFERENCES CUSTODIANS(CUSTODIANID),
		RECON_TO_PORTFOLIOS AS RECONCILIATIONS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		RECON_TO_SECURITIES AS RECONCILIATIONS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		NAV_TO_PORTFOLIOS AS NAV(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		SETTLEMENTS_TO_COUNTERPARTIES AS SETTLEMENTS(COUNTERPARTYID) REFERENCES COUNTERPARTIES(COUNTERPARTYID),
		CORPORATE_ACTIONS_TO_SECURITIES AS CORPORATE_ACTIONS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		CASH_MOVEMENTS_TO_PORTFOLIOS AS CASH_MOVEMENTS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		CASH_MOVEMENTS_TO_COUNTERPARTIES AS CASH_MOVEMENTS(COUNTERPARTYID) REFERENCES COUNTERPARTIES(COUNTERPARTYID),
		CASH_POSITIONS_TO_PORTFOLIOS AS CASH_POSITIONS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		CASH_POSITIONS_TO_CUSTODIANS AS CASH_POSITIONS(CUSTODIANID) REFERENCES CUSTODIANS(CUSTODIANID)
	)
	DIMENSIONS (
		-- Portfolio dimensions
		PORTFOLIOS.PORTFOLIONAME AS PortfolioName WITH SYNONYMS=('fund_name','portfolio_name') COMMENT='Portfolio name',
		
		-- Security dimensions
		SECURITIES.TICKER AS Ticker WITH SYNONYMS=('ticker_symbol','symbol') COMMENT='Trading ticker',
		SECURITIES.DESCRIPTION AS Description WITH SYNONYMS=('company_name','security_name') COMMENT='Company name',
		
		-- Custodian dimensions
		CUSTODIANS.CUSTODIANNAME AS CustodianName WITH SYNONYMS=('custodian','bank','depository') COMMENT='Custodian name',
		
		-- Settlement dimensions
		SETTLEMENTS.SettlementDate AS SETTLEMENTDATE WITH SYNONYMS=('settlement_date','date') COMMENT='Settlement date',
		SETTLEMENTS.SETTLEMENT_MONTH AS DATE_TRUNC('MONTH', SETTLEMENTDATE) WITH SYNONYMS=('settlement_month','monthly') COMMENT='Monthly aggregation for settlement trend analysis',
		SETTLEMENTS.SettlementStatus AS STATUS WITH SYNONYMS=('status','settlement_status') COMMENT='Settlement status (Settled, Pending, Failed)',
		
		-- Reconciliation dimensions
		RECONCILIATIONS.ReconciliationDate AS RECONCILIATIONDATE WITH SYNONYMS=('recon_date','date') COMMENT='Reconciliation date',
		RECONCILIATIONS.RECON_MONTH AS DATE_TRUNC('MONTH', RECONCILIATIONDATE) WITH SYNONYMS=('recon_month','monthly') COMMENT='Monthly aggregation for reconciliation break trends',
		RECONCILIATIONS.BreakType AS BREAKTYPE WITH SYNONYMS=('break_type','exception_type') COMMENT='Break type',
		RECONCILIATIONS.ReconStatus AS STATUS WITH SYNONYMS=('resolution_status','recon_status') COMMENT='Reconciliation status (Open, Investigating, Resolved)',
		
		-- NAV dimensions
		NAV.CALCULATIONDATE AS CalculationDate WITH SYNONYMS=('nav_date','valuation_date') COMMENT='NAV calculation date',
		NAV.NAV_MONTH AS DATE_TRUNC('MONTH', CALCULATIONDATE) WITH SYNONYMS=('nav_month','monthly') COMMENT='Monthly aggregation for NAV performance trends',
		
		-- Counterparty dimensions
		COUNTERPARTIES.COUNTERPARTYNAME AS CounterpartyName WITH SYNONYMS=('broker_name','trading_partner') COMMENT='Counterparty name',
		COUNTERPARTIES.COUNTERPARTYTYPE AS CounterpartyType WITH SYNONYMS=('broker_type','partner_type') COMMENT='Counterparty type (Broker, Custodian, Prime)',
		COUNTERPARTIES.RISKRATING AS RiskRating WITH SYNONYMS=('rating','credit_rating') COMMENT='Counterparty risk rating',
		
		-- Corporate action dimensions
		CORPORATE_ACTIONS.ACTIONTYPE AS ActionType WITH SYNONYMS=('action_type','event_type') COMMENT='Corporate action type (Dividend, Split, Merger)',
		CORPORATE_ACTIONS.EXDATE AS ExDate WITH SYNONYMS=('ex_date','ex_dividend_date') COMMENT='Ex-dividend/action date',
		CORPORATE_ACTIONS.PAYMENTDATE AS PaymentDate WITH SYNONYMS=('payment_date','pay_date') COMMENT='Payment date',
		
		-- Cash movement dimensions
		CASH_MOVEMENTS.MOVEMENTTYPE AS MovementType WITH SYNONYMS=('cash_type','flow_type') COMMENT='Cash movement type (Trade Settlement, Dividend, Fee)',
		CASH_MOVEMENTS.MOVEMENTDATE AS MovementDate WITH SYNONYMS=('cash_date','flow_date') COMMENT='Cash movement date',
		CASH_MOVEMENTS.MOVEMENTCURRENCY AS CURRENCY WITH SYNONYMS=('ccy','currency_code') COMMENT='Cash movement currency',
		
		-- Cash position dimensions
		CASH_POSITIONS.POSITIONDATE AS PositionDate WITH SYNONYMS=('balance_date','position_balance_date') COMMENT='Cash position date',
		CASH_POSITIONS.POSITIONCURRENCY AS CURRENCY WITH SYNONYMS=('cash_currency','balance_currency') COMMENT='Cash position currency'
	)
	METRICS (
		-- Settlement metrics
		SETTLEMENTS.SETTLEMENT_VALUE AS SUM(SettlementValue) WITH SYNONYMS=('value','settlement_value','trade_value') COMMENT='Settlement value',
		SETTLEMENTS.SETTLEMENT_COUNT AS COUNT(DISTINCT SETTLEMENTID) WITH SYNONYMS=('count','settlement_count') COMMENT='Settlement count',
		SETTLEMENTS.FAILED_SETTLEMENT_COUNT AS COUNT(CASE WHEN Status = 'Failed' THEN 1 END) WITH SYNONYMS=('fails','failed_trades','settlement_fails') COMMENT='Failed settlement count',
		
		-- Reconciliation metrics
		RECONCILIATIONS.BREAK_COUNT AS COUNT(DISTINCT RECONCILIATIONID) WITH SYNONYMS=('breaks','exceptions','break_count') COMMENT='Reconciliation break count',
		RECONCILIATIONS.BREAK_VALUE AS SUM(Difference) WITH SYNONYMS=('break_value','exception_value','difference_amount') COMMENT='Total break value (difference between internal and custodian values)',
		RECONCILIATIONS.UNRESOLVED_BREAKS AS COUNT(CASE WHEN Status = 'Open' THEN 1 END) WITH SYNONYMS=('unresolved','open_breaks','open_count') COMMENT='Open/unresolved break count',
		
		-- NAV metrics
		NAV.NAV_PER_SHARE AS AVG(NAVPerShare) WITH SYNONYMS=('nav','nav_per_share','unit_nav') COMMENT='NAV per share',
		NAV.TOTAL_ASSETS AS SUM(TotalAssets) WITH SYNONYMS=('assets','total_assets','aum') COMMENT='Total assets',
		
		-- Corporate action metrics
		CORPORATE_ACTIONS.ACTION_COUNT AS COUNT(DISTINCT ACTIONID) WITH SYNONYMS=('actions','event_count') COMMENT='Corporate action count',
		
		-- Cash movement metrics
		CASH_MOVEMENTS.CASH_INFLOW AS SUM(CASE WHEN Amount > 0 THEN Amount ELSE 0 END) WITH SYNONYMS=('inflows','receipts') COMMENT='Total cash inflows',
		CASH_MOVEMENTS.CASH_OUTFLOW AS SUM(CASE WHEN Amount < 0 THEN ABS(Amount) ELSE 0 END) WITH SYNONYMS=('outflows','payments') COMMENT='Total cash outflows',
		CASH_MOVEMENTS.NET_CASH_FLOW AS SUM(Amount) WITH SYNONYMS=('net_flow','net_cash') COMMENT='Net cash flow',
		
		-- Cash position metrics
		CASH_POSITIONS.CLOSING_BALANCE AS SUM(ClosingBalance) WITH SYNONYMS=('cash_balance','ending_balance') COMMENT='Closing cash balance',
		CASH_POSITIONS.OPENING_BALANCE AS SUM(OpeningBalance) WITH SYNONYMS=('starting_balance','beginning_balance') COMMENT='Opening cash balance'
	)
	COMMENT='Middle office semantic view for operations, reconciliation, NAV, corporate actions, and cash management'
	WITH EXTENSION (CA='{{"tables":[{{"name":"SETTLEMENTS","metrics":[{{"name":"FAILED_SETTLEMENT_COUNT"}},{{"name":"SETTLEMENT_COUNT"}},{{"name":"SETTLEMENT_VALUE"}}],"time_dimensions":[{{"name":"SettlementDate"}},{{"name":"SETTLEMENT_MONTH"}}]}},{{"name":"RECONCILIATIONS","metrics":[{{"name":"BREAK_COUNT"}},{{"name":"BREAK_VALUE"}},{{"name":"UNRESOLVED_BREAKS"}}],"time_dimensions":[{{"name":"ReconciliationDate"}},{{"name":"RECON_MONTH"}}]}},{{"name":"NAV","metrics":[{{"name":"NAV_PER_SHARE"}},{{"name":"TOTAL_ASSETS"}}],"time_dimensions":[{{"name":"CALCULATIONDATE"}},{{"name":"NAV_MONTH"}}]}},{{"name":"PORTFOLIOS","dimensions":[{{"name":"PORTFOLIONAME"}}]}},{{"name":"SECURITIES","dimensions":[{{"name":"TICKER"}},{{"name":"DESCRIPTION"}}]}},{{"name":"CUSTODIANS","dimensions":[{{"name":"CUSTODIANNAME"}}]}},{{"name":"COUNTERPARTIES","dimensions":[{{"name":"COUNTERPARTYNAME"}},{{"name":"COUNTERPARTYTYPE"}},{{"name":"RISKRATING"}}]}},{{"name":"CORPORATE_ACTIONS","metrics":[{{"name":"ACTION_COUNT"}}],"time_dimensions":[{{"name":"EXDATE"}},{{"name":"PAYMENTDATE"}}],"dimensions":[{{"name":"ACTIONTYPE"}}]}},{{"name":"CASH_MOVEMENTS","metrics":[{{"name":"CASH_INFLOW"}},{{"name":"CASH_OUTFLOW"}},{{"name":"NET_CASH_FLOW"}}],"time_dimensions":[{{"name":"MOVEMENTDATE"}}],"dimensions":[{{"name":"MOVEMENTTYPE"}},{{"name":"MOVEMENTCURRENCY"}}]}},{{"name":"CASH_POSITIONS","metrics":[{{"name":"CLOSING_BALANCE"}},{{"name":"OPENING_BALANCE"}}],"time_dimensions":[{{"name":"POSITIONDATE"}}],"dimensions":[{{"name":"POSITIONCURRENCY"}}]}}],"relationships":[{{"name":"SETTLEMENTS_TO_PORTFOLIOS"}},{{"name":"SETTLEMENTS_TO_SECURITIES"}},{{"name":"SETTLEMENTS_TO_CUSTODIANS"}},{{"name":"RECON_TO_PORTFOLIOS"}},{{"name":"RECON_TO_SECURITIES"}},{{"name":"NAV_TO_PORTFOLIOS"}},{{"name":"SETTLEMENTS_TO_COUNTERPARTIES"}},{{"name":"CORPORATE_ACTIONS_TO_SECURITIES"}},{{"name":"CASH_MOVEMENTS_TO_PORTFOLIOS"}},{{"name":"CASH_MOVEMENTS_TO_COUNTERPARTIES"}},{{"name":"CASH_POSITIONS_TO_PORTFOLIOS"}},{{"name":"CASH_POSITIONS_TO_CUSTODIANS"}}],"verified_queries":[{{"name":"settlement_summary","question":"What is the settlement summary?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_MIDDLE_OFFICE_VIEW METRICS SETTLEMENT_COUNT, SETTLEMENT_VALUE, FAILED_SETTLEMENT_COUNT)","use_as_onboarding_question":true}},{{"name":"break_summary","question":"What are the reconciliation breaks?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_MIDDLE_OFFICE_VIEW METRICS BREAK_COUNT, BREAK_VALUE, UNRESOLVED_BREAKS)","use_as_onboarding_question":true}},{{"name":"nav_summary","question":"What is the NAV?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_MIDDLE_OFFICE_VIEW METRICS NAV_PER_SHARE, TOTAL_ASSETS)","use_as_onboarding_question":false}},{{"name":"cash_summary","question":"What is the current cash position?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_MIDDLE_OFFICE_VIEW METRICS CLOSING_BALANCE)","use_as_onboarding_question":true}},{{"name":"corporate_actions","question":"What corporate actions are pending?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_MIDDLE_OFFICE_VIEW METRICS ACTION_COUNT DIMENSIONS ACTIONTYPE)","use_as_onboarding_question":false}}],"module_custom_instructions":{{"sql_generation":"IMPORTANT DATE HANDLING: The data is anchored to the latest available market data date, NOT CURRENT_DATE. When users ask about today, current, or recent data, use the maximum available date in each table as the reference point. For past N days queries, calculate relative to the maximum date: e.g., for settlements use (SELECT MAX(SettlementDate) FROM SETTLEMENTS) as the anchor, then filter SettlementDate >= DATEADD(day, -N, anchor_date). For future or upcoming queries (like pending corporate actions), filter where ExDate > (SELECT MAX(SettlementDate) FROM SETTLEMENTS). Never use CURRENT_DATE() directly - always derive dates from the data. For settlement queries, filter to most recent 30 days relative to MAX(SettlementDate) by default. When showing reconciliation breaks, always order by difference amount descending to show largest breaks first. For NAV queries, use the most recent calculation date when current NAV is requested. Round settlement values and break differences to 2 decimal places, NAV per share to 4 decimal places. Settlement status values: Settled, Pending, Failed. Reconciliation status values: Open, Investigating, Resolved. For cash queries, show closing balance by default using MAX(PositionDate). For corporate actions, filter ExDate > MAX(SettlementDate) from settlements when asking about pending/upcoming actions.","question_categorization":"If users ask about \\'fails\\' or \\'failed trades\\', treat as settlement status queries. If users ask about \\'breaks\\' or \\'exceptions\\', treat as reconciliation queries. If users ask about \\'NAV\\' or \\'unit value\\', treat as NAV calculation queries. If users ask about \\'cash\\' or \\'liquidity\\', treat as cash position queries. If users ask about \\'dividends\\', \\'splits\\', or \\'corporate actions\\', treat as corporate action queries. If users ask about \\'counterparty\\' or \\'broker\\', include counterparty dimension in response. When users say \\'today\\' or \\'current\\', interpret as the maximum available date in the relevant table, not the actual current date."}}}}');
    """).collect()
    
    log_detail(" Created semantic view: SAM_MIDDLE_OFFICE_VIEW")


def create_compliance_semantic_view(session: Session):
    """
    Create semantic view for compliance monitoring and breach tracking.
    
    Used by: Compliance Advisor for breach queries and remediation tracking
    Supports: Concentration breaches, ESG violations, alert history, remediation status
    """
    
    # Check if compliance alerts table exists
    try:
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_COMPLIANCE_ALERTS LIMIT 1").collect()
    except:
        log_detail("  Skipping SAM_COMPLIANCE_VIEW - FACT_COMPLIANCE_ALERTS table not found")
        return
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_COMPLIANCE_VIEW
    TABLES (
        ALERTS AS {config.DATABASE['name']}.CURATED.FACT_COMPLIANCE_ALERTS
            PRIMARY KEY (ALERTID)
            WITH SYNONYMS=('breaches','violations','compliance_alerts','warnings','alerts')
            COMMENT='Compliance alerts including concentration breaches, ESG violations, and mandate compliance issues',
        PORTFOLIOS AS {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
            PRIMARY KEY (PORTFOLIOID)
            WITH SYNONYMS=('funds','portfolios','strategies')
            COMMENT='Portfolio information',
        SECURITIES AS {config.DATABASE['name']}.CURATED.DIM_SECURITY
            PRIMARY KEY (SECURITYID)
            WITH SYNONYMS=('securities','stocks','instruments','holdings')
            COMMENT='Security master data'
    )
    RELATIONSHIPS (
        ALERTS_TO_PORTFOLIOS AS ALERTS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
        ALERTS_TO_SECURITIES AS ALERTS(SECURITYID) REFERENCES SECURITIES(SECURITYID)
    )
    DIMENSIONS (
        -- Portfolio dimensions (SemanticName AS DatabaseColumn)
        PORTFOLIOS.PortfolioName AS PORTFOLIONAME WITH SYNONYMS=('fund_name','portfolio_name','fund') COMMENT='Portfolio name',
        PORTFOLIOS.Strategy AS STRATEGY WITH SYNONYMS=('investment_strategy','portfolio_strategy') COMMENT='Investment strategy',
        
        -- Security dimensions (SemanticName AS DatabaseColumn)
        SECURITIES.Ticker AS TICKER WITH SYNONYMS=('ticker_symbol','symbol','stock') COMMENT='Trading ticker',
        SECURITIES.SecurityName AS DESCRIPTION WITH SYNONYMS=('company_name','security_name','company') COMMENT='Security/company name',
        
        -- Alert dimensions (SemanticName AS DatabaseColumn)
        ALERTS.AlertDate AS ALERTDATE WITH SYNONYMS=('breach_date','violation_date','detection_date','date') COMMENT='Date the alert/breach was detected',
        ALERTS.ALERT_MONTH AS DATE_TRUNC('MONTH', ALERTDATE) WITH SYNONYMS=('month','monthly') COMMENT='Monthly aggregation for breach trend analysis',
        ALERTS.AlertType AS ALERTTYPE WITH SYNONYMS=('breach_type','violation_type','issue_type') COMMENT='Type of compliance alert: CONCENTRATION_BREACH, CONCENTRATION_WARNING, ESG_DOWNGRADE',
        ALERTS.Severity AS ALERTSEVERITY WITH SYNONYMS=('alert_severity','breach_severity','priority','level') COMMENT='Alert severity: WARNING or BREACH',
        ALERTS.ThresholdValue AS ORIGINALVALUE WITH SYNONYMS=('limit','threshold','original_value','limit_value') COMMENT='The policy threshold or original value that was breached',
        ALERTS.CurrentValue AS CURRENTVALUE WITH SYNONYMS=('actual_value','current_level','position_weight') COMMENT='The current value that triggered the breach',
        ALERTS.RequiresAction AS REQUIRESACTION WITH SYNONYMS=('needs_action','action_required','pending_action') COMMENT='Whether this alert requires remediation action',
        ALERTS.ActionDeadline AS ACTIONDEADLINE WITH SYNONYMS=('deadline','due_date','remediation_deadline') COMMENT='Deadline for remediation action (typically 30 days from alert)',
        ALERTS.Description AS ALERTDESCRIPTION WITH SYNONYMS=('alert_description','breach_description','details') COMMENT='Detailed description of the compliance alert',
        ALERTS.ResolvedDate AS RESOLVEDDATE WITH SYNONYMS=('resolution_date','closed_date','remediated_date') COMMENT='Date the alert was resolved (NULL if still active)',
        ALERTS.ResolvedBy AS RESOLVEDBY WITH SYNONYMS=('resolved_by','remediated_by','closed_by') COMMENT='Person who resolved the alert',
        ALERTS.ResolutionNotes AS RESOLUTIONNOTES WITH SYNONYMS=('resolution_notes','remediation_notes','action_taken') COMMENT='Notes on how the alert was resolved'
    )
    METRICS (
        -- Alert counts
        ALERTS.TOTAL_ALERTS AS COUNT(DISTINCT ALERTID) WITH SYNONYMS=('alert_count','total_breaches','issue_count') COMMENT='Total count of compliance alerts',
        ALERTS.ACTIVE_ALERTS AS COUNT(CASE WHEN RESOLVEDDATE IS NULL THEN 1 END) WITH SYNONYMS=('open_alerts','unresolved_alerts','active_breaches','pending_alerts') COMMENT='Count of active/unresolved alerts',
        ALERTS.RESOLVED_ALERTS AS COUNT(CASE WHEN RESOLVEDDATE IS NOT NULL THEN 1 END) WITH SYNONYMS=('closed_alerts','resolved_breaches','remediated_alerts') COMMENT='Count of resolved alerts',
        ALERTS.BREACH_COUNT AS COUNT(CASE WHEN ALERTSEVERITY = 'BREACH' THEN 1 END) WITH SYNONYMS=('breaches','breach_count','violations') COMMENT='Count of breaches (severity = BREACH)',
        ALERTS.WARNING_COUNT AS COUNT(CASE WHEN ALERTSEVERITY = 'WARNING' THEN 1 END) WITH SYNONYMS=('warnings','warning_count') COMMENT='Count of warnings (severity = WARNING)',
        
        -- Concentration-specific metrics
        ALERTS.CONCENTRATION_BREACHES AS COUNT(CASE WHEN ALERTTYPE = 'CONCENTRATION_BREACH' THEN 1 END) WITH SYNONYMS=('position_breaches','concentration_violations') COMMENT='Count of concentration breach alerts',
        ALERTS.CONCENTRATION_WARNINGS AS COUNT(CASE WHEN ALERTTYPE = 'CONCENTRATION_WARNING' THEN 1 END) WITH SYNONYMS=('position_warnings') COMMENT='Count of concentration warning alerts',
        
        -- ESG-specific metrics  
        ALERTS.ESG_VIOLATIONS AS COUNT(CASE WHEN ALERTTYPE = 'ESG_DOWNGRADE' THEN 1 END) WITH SYNONYMS=('esg_breaches','esg_downgrades') COMMENT='Count of ESG-related violations',
        
        -- Time-based metrics
        ALERTS.DAYS_SINCE_ALERT AS DATEDIFF(day, MIN(ALERTDATE), CURRENT_DATE()) WITH SYNONYMS=('alert_age','days_outstanding','time_open') COMMENT='Days since earliest alert in selection',
        ALERTS.DAYS_TO_DEADLINE AS DATEDIFF(day, CURRENT_DATE(), MIN(ACTIONDEADLINE)) WITH SYNONYMS=('days_remaining','time_to_deadline') COMMENT='Days until earliest action deadline'
    )
    COMMENT='Compliance semantic view for monitoring concentration breaches, ESG violations, and mandate compliance tracking'
    WITH EXTENSION (CA='{{"tables":[{{"name":"ALERTS","metrics":[{{"name":"TOTAL_ALERTS"}},{{"name":"ACTIVE_ALERTS"}},{{"name":"BREACH_COUNT"}},{{"name":"WARNING_COUNT"}}],"time_dimensions":[{{"name":"AlertDate"}},{{"name":"ALERT_MONTH"}}]}},{{"name":"PORTFOLIOS","dimensions":[{{"name":"PortfolioName"}},{{"name":"Strategy"}}]}},{{"name":"SECURITIES","dimensions":[{{"name":"Ticker"}},{{"name":"SecurityName"}}]}}],"relationships":[{{"name":"ALERTS_TO_PORTFOLIOS"}},{{"name":"ALERTS_TO_SECURITIES"}}],"verified_queries":[{{"name":"alert_summary","question":"What are the compliance alerts?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_COMPLIANCE_VIEW METRICS TOTAL_ALERTS, ACTIVE_ALERTS, BREACH_COUNT, WARNING_COUNT)","use_as_onboarding_question":true}}],"module_custom_instructions":{{"sql_generation":"For breach queries, filter to last 30 days by default unless a specific time period is requested. Always show both active and resolved breaches unless the user specifically asks for one. When showing breaches, include the threshold value and current value to show the extent of the breach. Order by alert date descending (most recent first) unless otherwise specified. Alert severity values: WARNING, BREACH. Alert types: CONCENTRATION_BREACH, CONCENTRATION_WARNING, ESG_DOWNGRADE. Active alerts have RESOLVEDDATE IS NULL.","question_categorization":"If users ask about \\'breaches\\' or \\'violations\\', treat as compliance alert queries. If users mention \\'concentration\\', filter to CONCENTRATION_BREACH or CONCENTRATION_WARNING alert types. If users mention \\'ESG\\', filter to ESG_DOWNGRADE alert type. If users ask about \\'active\\' or \\'pending\\' alerts, filter where RESOLVEDDATE IS NULL."}}}}');
    """).collect()
    
    log_detail(" Created semantic view: SAM_COMPLIANCE_VIEW")


def create_executive_semantic_view(session: Session):
    """
    Create semantic view for executive KPIs, client analytics, strategy performance, and firm-wide metrics.
    
    Used by: Executive Copilot for C-suite queries
    Supports: Firm-wide AUM (from holdings), net flows, client flow drill-down, strategy performance (QTD/YTD)
    
    Key Distinction:
    - FIRM_AUM: Calculated from actual portfolio holdings (authoritative for board reporting)
    - TOTAL_CLIENT_AUM: Sum of client-reported AUM (may differ due to reporting timing)
    
    Reuses: DIM_PORTFOLIO (existing), DIM_CLIENT_MANDATES (existing)
    New: DIM_CLIENT, FACT_CLIENT_FLOWS, FACT_FUND_FLOWS, FACT_STRATEGY_PERFORMANCE
    """
    
    # Check if required tables exist
    required_tables = [
        'DIM_CLIENT',
        'FACT_CLIENT_FLOWS',
        'FACT_FUND_FLOWS',
        'DIM_PORTFOLIO',
        'FACT_STRATEGY_PERFORMANCE'
    ]
    
    for table in required_tables:
        try:
            session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.{table} LIMIT 1").collect()
        except:
            log_warning(f" Executive table {table} not found, skipping executive view creation")
            return
    
    # Build the semantic view using the same inline f-string pattern as other views
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_EXECUTIVE_VIEW
    TABLES (
        CLIENTS AS {config.DATABASE['name']}.CURATED.DIM_CLIENT
            PRIMARY KEY (CLIENTID) 
            WITH SYNONYMS=('clients','investors','accounts','institutional_clients') 
            COMMENT='Institutional client dimension with client types, regions, and AUM',
        CLIENT_FLOWS AS {config.DATABASE['name']}.CURATED.FACT_CLIENT_FLOWS
            PRIMARY KEY (FLOWID)
            WITH SYNONYMS=('flows','subscriptions','redemptions','client_flows')
            COMMENT='Client-level flow transactions including subscriptions, redemptions, and transfers',
        FUND_FLOWS AS {config.DATABASE['name']}.CURATED.FACT_FUND_FLOWS
            PRIMARY KEY (FUNDFLOWID)
            WITH SYNONYMS=('fund_flows','strategy_flows','portfolio_flows','aggregated_flows')
            COMMENT='Aggregated fund-level flows by portfolio and strategy for executive KPIs',
        PORTFOLIOS AS {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
            PRIMARY KEY (PORTFOLIOID) 
            WITH SYNONYMS=('funds','strategies','mandates','portfolios') 
            COMMENT='Investment portfolios and fund information',
        STRATEGY_PERF AS {config.DATABASE['name']}.CURATED.FACT_STRATEGY_PERFORMANCE
            PRIMARY KEY (STRATEGYPERFID)
            WITH SYNONYMS=('strategy_performance','performance','returns','strategy_returns')
            COMMENT='Strategy-level performance metrics including AUM, MTD/QTD/YTD returns calculated from portfolio holdings'
    )
    RELATIONSHIPS (
        CLIENT_FLOWS_TO_CLIENTS AS CLIENT_FLOWS(CLIENTID) REFERENCES CLIENTS(CLIENTID),
        CLIENT_FLOWS_TO_PORTFOLIOS AS CLIENT_FLOWS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
        FUND_FLOWS_TO_PORTFOLIOS AS FUND_FLOWS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
        STRATEGY_PERF_TO_PORTFOLIOS AS STRATEGY_PERF(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID)
    )
    DIMENSIONS (
        -- Client dimensions
        CLIENTS.ClientName AS ClientName WITH SYNONYMS=('client_name','investor_name','account_name') COMMENT='Institutional client name',
        CLIENTS.ClientType AS ClientType WITH SYNONYMS=('client_type','investor_type','account_type') COMMENT='Client type: Pension, Endowment, Foundation, Insurance, Corporate, Family Office',
        CLIENTS.Region AS Region WITH SYNONYMS=('client_region','geography','location') COMMENT='Client geographic region',
        CLIENTS.PrimaryContact AS PrimaryContact WITH SYNONYMS=('contact','relationship_manager','rm') COMMENT='Primary relationship manager contact',
        
        -- Portfolio dimensions
        PORTFOLIOS.PortfolioName AS PortfolioName WITH SYNONYMS=('fund_name','strategy_name','portfolio_name') COMMENT='Portfolio or fund name',
        PORTFOLIOS.Strategy AS Strategy WITH SYNONYMS=('investment_strategy','portfolio_strategy','strategy_type') COMMENT='Investment strategy: Value, Growth, ESG, Core, Multi-Asset, Income',
        
        -- Flow dimensions
        CLIENT_FLOWS.FlowType AS FlowType WITH SYNONYMS=('flow_type','transaction_type') COMMENT='Flow type: Subscription, Redemption, Transfer',
        
        -- Time dimensions
        CLIENT_FLOWS.ClientFlowDate AS FlowDate WITH SYNONYMS=('flow_date','transaction_date') COMMENT='Date of client flow transaction',
        CLIENT_FLOWS.FLOW_MONTH AS DATE_TRUNC('MONTH', FlowDate) WITH SYNONYMS=('monthly','flow_month') COMMENT='Monthly aggregation for flow trend analysis',
        FUND_FLOWS.FundFlowDate AS FlowDate WITH SYNONYMS=('fund_flow_date','aggregated_date') COMMENT='Date of aggregated fund flows',
        FUND_FLOWS.FUND_FLOW_MONTH AS DATE_TRUNC('MONTH', FlowDate) WITH SYNONYMS=('fund_month','monthly') COMMENT='Monthly aggregation for fund flow trends',
        STRATEGY_PERF.PerformanceDate AS HoldingDate WITH SYNONYMS=('performance_date','valuation_date','as_of_date') COMMENT='Date of strategy performance valuation',
        STRATEGY_PERF.PERF_MONTH AS DATE_TRUNC('MONTH', HoldingDate) WITH SYNONYMS=('perf_month','monthly') COMMENT='Monthly aggregation for performance trends'
    )
    METRICS (
        -- Client AUM metrics
        CLIENTS.TOTAL_CLIENT_AUM AS SUM(AUM_with_SAM) WITH SYNONYMS=('client_aum','total_client_assets','reported_aum') COMMENT='Total AUM from client reports. Note: Use FIRM_AUM for authoritative holdings-based AUM.',
        CLIENTS.CLIENT_COUNT AS COUNT(DISTINCT ClientID) WITH SYNONYMS=('number_of_clients','client_count','investor_count') COMMENT='Count of institutional clients',
        CLIENTS.AVG_CLIENT_SIZE AS AVG(AUM_with_SAM) WITH SYNONYMS=('average_client_size','avg_client_aum','typical_client_size') COMMENT='Average client AUM',
        
        -- Client flow metrics
        CLIENT_FLOWS.TOTAL_FLOW_AMOUNT AS SUM(FlowAmount) WITH SYNONYMS=('net_flows','total_flows','flow_amount','position','position_value','invested_amount','cumulative_position','allocation','client_allocation') COMMENT='Net flow amount representing cumulative client position (positive = inflow/position, negative = outflow)',
        CLIENT_FLOWS.GROSS_INFLOWS AS SUM(CASE WHEN FlowAmount > 0 THEN FlowAmount ELSE 0 END) WITH SYNONYMS=('inflows','subscriptions','gross_inflows') COMMENT='Gross subscription inflows',
        CLIENT_FLOWS.GROSS_OUTFLOWS AS SUM(CASE WHEN FlowAmount < 0 THEN ABS(FlowAmount) ELSE 0 END) WITH SYNONYMS=('outflows','redemptions','gross_outflows') COMMENT='Gross redemption outflows',
        CLIENT_FLOWS.FLOW_TRANSACTION_COUNT AS COUNT(FlowID) WITH SYNONYMS=('flow_count','transaction_count','number_of_flows') COMMENT='Number of flow transactions',
        CLIENT_FLOWS.MAX_SINGLE_CLIENT_FLOW AS MAX(ABS(FlowAmount)) WITH SYNONYMS=('largest_flow','max_flow','biggest_transaction') COMMENT='Largest single client flow',
        
        -- Fund flow metrics
        FUND_FLOWS.FUND_NET_FLOWS AS SUM(NetFlows) WITH SYNONYMS=('net_fund_flows','strategy_net_flows','portfolio_net_flows') COMMENT='Net flows at fund/strategy level',
        FUND_FLOWS.FUND_GROSS_INFLOWS AS SUM(GrossInflows) WITH SYNONYMS=('fund_inflows','strategy_inflows') COMMENT='Gross inflows at fund level',
        FUND_FLOWS.FUND_GROSS_OUTFLOWS AS SUM(GrossOutflows) WITH SYNONYMS=('fund_outflows','strategy_outflows') COMMENT='Gross outflows at fund level',
        FUND_FLOWS.FUND_CLIENT_COUNT AS SUM(ClientCount) WITH SYNONYMS=('active_clients','contributing_clients') COMMENT='Number of clients with flows',
        
        -- Strategy AUM metrics
        STRATEGY_PERF.STRATEGY_AUM AS SUM(Strategy_AUM) WITH SYNONYMS=('strategy_aum','portfolio_aum','fund_aum','strategy_assets','firm_aum','total_aum','assets_under_management','firm_assets','aum') COMMENT='AUM by strategy/portfolio calculated from holdings. When not grouped by strategy, gives total firm AUM.',
        STRATEGY_PERF.STRATEGY_MTD_RETURN AS AVG(Strategy_MTD_Return) WITH SYNONYMS=('mtd_return','monthly_return','month_to_date_return','mtd_performance') COMMENT='Strategy month-to-date return percentage (weighted average from holdings)',
        STRATEGY_PERF.STRATEGY_QTD_RETURN AS AVG(Strategy_QTD_Return) WITH SYNONYMS=('qtd_return','quarterly_return','quarter_to_date_return','qtd_performance') COMMENT='Strategy quarter-to-date return percentage (weighted average from holdings)',
        STRATEGY_PERF.STRATEGY_YTD_RETURN AS AVG(Strategy_YTD_Return) WITH SYNONYMS=('ytd_return','annual_return','year_to_date_return','ytd_performance') COMMENT='Strategy year-to-date return percentage (weighted average from holdings)',
        STRATEGY_PERF.STRATEGY_HOLDING_COUNT AS SUM(Holding_Count) WITH SYNONYMS=('holdings','position_count','number_of_holdings') COMMENT='Total holdings count by strategy'
    )
    COMMENT='Executive semantic view for firm-wide KPIs, client analytics, strategy performance, and flow analysis. Use for C-suite performance reviews and board reporting. FIRM_AUM is the authoritative AUM from holdings; TOTAL_CLIENT_AUM is client-reported.'
    WITH EXTENSION (CA='{{"tables":[{{"name":"CLIENTS","metrics":[{{"name":"AVG_CLIENT_SIZE"}},{{"name":"CLIENT_COUNT"}},{{"name":"TOTAL_CLIENT_AUM"}}]}},{{"name":"CLIENT_FLOWS","metrics":[{{"name":"FLOW_TRANSACTION_COUNT"}},{{"name":"GROSS_INFLOWS"}},{{"name":"GROSS_OUTFLOWS"}},{{"name":"MAX_SINGLE_CLIENT_FLOW"}},{{"name":"TOTAL_FLOW_AMOUNT"}}],"time_dimensions":[{{"name":"ClientFlowDate"}},{{"name":"FLOW_MONTH"}}]}},{{"name":"FUND_FLOWS","metrics":[{{"name":"FUND_CLIENT_COUNT"}},{{"name":"FUND_GROSS_INFLOWS"}},{{"name":"FUND_GROSS_OUTFLOWS"}},{{"name":"FUND_NET_FLOWS"}}],"time_dimensions":[{{"name":"FundFlowDate"}},{{"name":"FUND_FLOW_MONTH"}}]}},{{"name":"PORTFOLIOS","dimensions":[{{"name":"PortfolioName"}},{{"name":"Strategy"}}]}},{{"name":"STRATEGY_PERF","metrics":[{{"name":"STRATEGY_AUM"}},{{"name":"STRATEGY_MTD_RETURN"}},{{"name":"STRATEGY_QTD_RETURN"}},{{"name":"STRATEGY_YTD_RETURN"}},{{"name":"STRATEGY_HOLDING_COUNT"}}],"time_dimensions":[{{"name":"PerformanceDate"}},{{"name":"PERF_MONTH"}}]}}],"relationships":[{{"name":"CLIENT_FLOWS_TO_CLIENTS"}},{{"name":"CLIENT_FLOWS_TO_PORTFOLIOS"}},{{"name":"FUND_FLOWS_TO_PORTFOLIOS"}},{{"name":"STRATEGY_PERF_TO_PORTFOLIOS"}}],"verified_queries":[{{"name":"total_fund_flows","question":"What are the total fund flows?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_EXECUTIVE_VIEW METRICS FUND_NET_FLOWS, FUND_GROSS_INFLOWS, FUND_GROSS_OUTFLOWS)","use_as_onboarding_question":true}},{{"name":"client_aum","question":"What is the total client AUM?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_EXECUTIVE_VIEW METRICS TOTAL_CLIENT_AUM, CLIENT_COUNT)","use_as_onboarding_question":true}},{{"name":"client_flows","question":"What are the client flow totals?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_EXECUTIVE_VIEW METRICS TOTAL_FLOW_AMOUNT, GROSS_INFLOWS, GROSS_OUTFLOWS)","use_as_onboarding_question":false}},{{"name":"firm_aum","question":"What is the firm AUM?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_EXECUTIVE_VIEW METRICS STRATEGY_AUM DIMENSIONS Strategy)","use_as_onboarding_question":true}},{{"name":"strategy_performance","question":"What is the performance by strategy?","sql":"SELECT * FROM SEMANTIC_VIEW({config.DATABASE['name']}.AI.SAM_EXECUTIVE_VIEW METRICS STRATEGY_AUM, STRATEGY_QTD_RETURN, STRATEGY_YTD_RETURN DIMENSIONS Strategy)","use_as_onboarding_question":true}}],"module_custom_instructions":{{"sql_generation":"For month-to-date queries, filter to current month using DATE_TRUNC(\\'MONTH\\', CURRENT_DATE()). When showing flows, always display both gross inflows and outflows alongside net flows for context. For client concentration analysis, show the count of distinct clients alongside flow amounts. Round flow amounts to nearest thousand for readability. When asked about \\'driving\\' flows, drill down to client level using CLIENT_FLOWS table. For client allocation or position questions, TOTAL_FLOW_AMOUNT represents the client invested position in each portfolio. Group by PortfolioName to show which portfolios a client invests in. For current holdings queries, filter to positive positions (TOTAL_FLOW_AMOUNT > 0). EXCEPTION for at-risk clients or redemption analysis: When analyzing clients with redemption patterns, declining flows, or at-risk status, do NOT filter to positive positions - show full flow history including zero or negative cumulative positions, as these clients may have fully or partially redeemed. Include GROSS_INFLOWS and GROSS_OUTFLOWS to show complete transaction history. IMPORTANT AUM DISTINCTION: STRATEGY_AUM (from STRATEGY_PERF) when summed across all strategies gives the authoritative firm AUM calculated from actual portfolio holdings - use this for board and executive reporting. TOTAL_CLIENT_AUM (from CLIENTS) is the sum of client-reported AUM which may differ due to reporting timing. For strategy performance queries, filter STRATEGY_PERF to the latest HoldingDate. When asked about top/bottom performing strategies, order by STRATEGY_QTD_RETURN or STRATEGY_YTD_RETURN.","question_categorization":"If users ask about \\'firm performance\\' or \\'KPIs\\', use FUND_FLOWS for aggregated metrics. If users ask about \\'what is driving\\' or \\'client concentration\\', drill down to CLIENT_FLOWS. If users ask about \\'broad-based\\' demand, count distinct clients. If users ask about client allocation, portfolio distribution, or which portfolios a client invests in, use CLIENT_FLOWS grouped by portfolio with positive position filter. For \\'firm AUM\\' or \\'total AUM\\' questions, use STRATEGY_AUM from STRATEGY_PERF summed across all strategies (not TOTAL_CLIENT_AUM). For \\'strategy performance\\', \\'top performing\\', or \\'returns by strategy\\' questions, use STRATEGY_QTD_RETURN and STRATEGY_YTD_RETURN from STRATEGY_PERF."}}}}');
        """).collect()
    
    log_detail(" Created semantic view: SAM_EXECUTIVE_VIEW")


def create_fundamentals_semantic_view(session: Session):
    """Create fundamentals semantic view for MARKET_DATA financial analysis (SAM_FUNDAMENTALS_VIEW).
    
    This semantic view provides access to:
    - Real SEC company financial statements (revenue, margins, earnings) from FACT_SEC_FINANCIALS
    - Analyst estimates and consensus data
    - Price targets and ratings
    - Historical financial trends
    - Investment memo metrics (TAM, Customer Count, NRR) calculated heuristically from real data
    
    NOTE: Now uses FACT_SEC_FINANCIALS (real SEC data) instead of synthetic FACT_FINANCIAL_DATA.
    """
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas'].get('market_data', 'MARKET_DATA')
    
    curated_schema = config.DATABASE['schemas'].get('curated', 'CURATED')
    
    # First check if DIM_ISSUER exists (used as company master)
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.DIM_ISSUER LIMIT 1").collect()
    except Exception as e:
        log_warning(f"  DIM_ISSUER not found, skipping SAM_FUNDAMENTALS_VIEW")
        log_warning(f"Run with --scope structured to generate CURATED tables first")
        return
    
    # Check if FACT_SEC_FINANCIALS exists (required for this view)
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS LIMIT 1").collect()
    except Exception as e:
        log_warning(f"  FACT_SEC_FINANCIALS not found, skipping SAM_FUNDAMENTALS_VIEW")
        log_warning(f"Run with --scope real-data to generate real SEC data first")
        return
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {database_name}.AI.SAM_FUNDAMENTALS_VIEW
    TABLES (
        ISSUERS AS {database_name}.{curated_schema}.DIM_ISSUER
            PRIMARY KEY (IssuerID) 
            WITH SYNONYMS=('companies','firms','corporations','issuers') 
            COMMENT='Company/issuer master data (single source of truth for company information)',
        FINANCIALS AS {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS
            PRIMARY KEY (FINANCIAL_ID)
            WITH SYNONYMS=('financial_data','statements','fundamentals','sec_financials')
            COMMENT='Real SEC financial statement data from 10-K and 10-Q filings including income statement, balance sheet, and cash flow metrics',
        CONSENSUS AS {database_name}.{market_data_schema}.FACT_ESTIMATE_CONSENSUS
            PRIMARY KEY (CONSENSUS_ID)
            WITH SYNONYMS=('estimates','consensus','forecasts')
            COMMENT='Analyst consensus estimates for future periods',
        ANALYST_ESTIMATES AS {database_name}.{market_data_schema}.FACT_ESTIMATE_DATA
            PRIMARY KEY (ESTIMATE_ID)
            WITH SYNONYMS=('analyst_data','price_targets','ratings')
            COMMENT='Individual analyst estimates including price targets and ratings',
        ANALYSTS AS {database_name}.{market_data_schema}.DIM_ANALYST
            PRIMARY KEY (ANALYST_ID)
            WITH SYNONYMS=('analysts','research_analysts')
            COMMENT='Analyst information',
        BROKERS AS {database_name}.{market_data_schema}.DIM_BROKER
            PRIMARY KEY (BROKER_ID)
            WITH SYNONYMS=('brokers','sell_side','research_firms')
            COMMENT='Broker/research firm information'
    )
    RELATIONSHIPS (
        FINANCIALS_TO_ISSUERS AS FINANCIALS(IssuerID) REFERENCES ISSUERS(IssuerID),
        CONSENSUS_TO_ISSUERS AS CONSENSUS(IssuerID) REFERENCES ISSUERS(IssuerID),
        ESTIMATES_TO_ISSUERS AS ANALYST_ESTIMATES(IssuerID) REFERENCES ISSUERS(IssuerID),
        ESTIMATES_TO_ANALYSTS AS ANALYST_ESTIMATES(ANALYST_ID) REFERENCES ANALYSTS(ANALYST_ID),
        ESTIMATES_TO_BROKERS AS ANALYST_ESTIMATES(BROKER_ID) REFERENCES BROKERS(BROKER_ID),
        ANALYSTS_TO_BROKERS AS ANALYSTS(BROKER_ID) REFERENCES BROKERS(BROKER_ID)
    )
    DIMENSIONS (
        -- Company/Issuer dimensions (using DIM_ISSUER as single source of truth)
        -- Syntax: <semantic_name> AS <database_column> - "Call it X, it's really Y"
        ISSUERS.CompanyName AS LegalName WITH SYNONYMS=('company','company_name','firm_name','corporation','issuer','entity','name') COMMENT='Company legal name for filtering (e.g., MICROSOFT CORP, APPLE INC., NVIDIA CORP)',
        ISSUERS.Ticker AS PrimaryTicker WITH SYNONYMS=('ticker','symbol','stock_symbol','stock') COMMENT='Stock ticker symbol for filtering (e.g., MSFT, AAPL, NVDA)',
        ISSUERS.Country AS CountryOfIncorporation WITH SYNONYMS=('country','domicile','country_of_incorporation') COMMENT='Country of incorporation (2-letter ISO code)',
        ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry','business_description') COMMENT='Industry classification description (SIC)',
        ISSUERS.Sector AS GICS_SECTOR WITH SYNONYMS=('gics','gics_sector','sector','sector_classification') COMMENT='GICS Level 1 sector classification (e.g., Information Technology, Health Care, Financials)',
        ISSUERS.CIK AS CIK WITH SYNONYMS=('cik_number','sec_id','edgar_id') COMMENT='SEC Central Index Key for EDGAR filings',
        
        -- Period dimensions (from FINANCIALS - real SEC data, columns are UPPER_CASE)
        FINANCIALS.FiscalYear AS FISCAL_YEAR WITH SYNONYMS=('year','fiscal_year','fy') COMMENT='Fiscal year from SEC filing',
        FINANCIALS.FiscalPeriod AS FISCAL_PERIOD WITH SYNONYMS=('quarter','fiscal_quarter','period','q') COMMENT='Fiscal period (FY, Q1, Q2, Q3, Q4)',
        FINANCIALS.PeriodEndDate AS PERIOD_END_DATE WITH SYNONYMS=('period_end','quarter_end','reporting_date') COMMENT='Period end date from SEC filing',
        FINANCIALS.Currency AS CURRENCY WITH SYNONYMS=('reporting_currency','currency_code') COMMENT='Reporting currency',
        
        -- Broker/Analyst dimensions (columns are UPPER_CASE in DIM_BROKER/DIM_ANALYST)
        BROKERS.BrokerName AS BROKER_NAME WITH SYNONYMS=('broker','research_firm','sell_side_firm') COMMENT='Broker/research firm name',
        ANALYSTS.AnalystName AS ANALYST_NAME WITH SYNONYMS=('analyst','research_analyst') COMMENT='Analyst name',
        ANALYSTS.SectorCoverage AS SECTOR_COVERAGE WITH SYNONYMS=('sector','coverage_sector') COMMENT='Analyst sector coverage'
    )
    METRICS (
        -- Income Statement metrics (direct from real SEC data)
        FINANCIALS.TOTAL_REVENUE AS SUM(REVENUE) WITH SYNONYMS=('revenue','sales','top_line','total_revenue') COMMENT='Total revenue from SEC filings',
        FINANCIALS.TOTAL_NET_INCOME AS SUM(NET_INCOME) WITH SYNONYMS=('net_income','earnings','profit','bottom_line') COMMENT='Net income from SEC filings',
        FINANCIALS.BASIC_EPS AS AVG(EPS_BASIC) WITH SYNONYMS=('eps','earnings_per_share','eps_basic') COMMENT='Basic earnings per share from SEC filings',
        FINANCIALS.DILUTED_EPS AS AVG(EPS_DILUTED) WITH SYNONYMS=('diluted_eps','eps_diluted') COMMENT='Diluted earnings per share from SEC filings',
        FINANCIALS.TOTAL_GROSS_PROFIT AS SUM(GROSS_PROFIT) WITH SYNONYMS=('gross_profit','gross_margin_dollars') COMMENT='Gross profit from SEC filings',
        FINANCIALS.TOTAL_OPERATING_INCOME AS SUM(OPERATING_INCOME) WITH SYNONYMS=('operating_income','ebit','operating_profit') COMMENT='Operating income from SEC filings',
        FINANCIALS.TOTAL_EBITDA AS SUM(EBITDA) WITH SYNONYMS=('ebitda','operating_ebitda') COMMENT='EBITDA (Operating Income + D&A)',
        FINANCIALS.TOTAL_RD_EXPENSE AS SUM(RD_EXPENSE) WITH SYNONYMS=('rd','research_development','rd_expense') COMMENT='R&D expense from SEC filings',
        
        -- Balance Sheet metrics
        FINANCIALS.TOTAL_ASSETS_AMT AS SUM(TOTAL_ASSETS) WITH SYNONYMS=('total_assets','assets') COMMENT='Total assets from SEC filings',
        FINANCIALS.TOTAL_LIABILITIES_AMT AS SUM(TOTAL_LIABILITIES) WITH SYNONYMS=('total_liabilities','liabilities') COMMENT='Total liabilities from SEC filings',
        FINANCIALS.TOTAL_EQUITY_AMT AS SUM(TOTAL_EQUITY) WITH SYNONYMS=('stockholders_equity','equity','book_value') COMMENT='Total stockholders equity from SEC filings',
        FINANCIALS.TOTAL_CASH AS SUM(CASH_AND_EQUIVALENTS) WITH SYNONYMS=('cash','cash_equivalents','liquidity') COMMENT='Cash and cash equivalents from SEC filings',
        FINANCIALS.TOTAL_DEBT AS SUM(LONG_TERM_DEBT) WITH SYNONYMS=('long_term_debt','debt') COMMENT='Long-term debt from SEC filings',
        
        -- Cash Flow metrics
        FINANCIALS.TOTAL_OPERATING_CF AS SUM(OPERATING_CASH_FLOW) WITH SYNONYMS=('operating_cash_flow','cfo','ocf') COMMENT='Cash from operations from SEC filings',
        FINANCIALS.TOTAL_FCF AS SUM(FREE_CASH_FLOW) WITH SYNONYMS=('free_cash_flow','fcf') COMMENT='Free cash flow (OCF - CapEx)',
        FINANCIALS.TOTAL_CAPEX AS SUM(CAPEX) WITH SYNONYMS=('capital_expenditure','capex') COMMENT='Capital expenditure from SEC filings',
        
        -- Profitability ratios
        FINANCIALS.AVG_GROSS_MARGIN AS AVG(GROSS_MARGIN_PCT) WITH SYNONYMS=('gross_margin','gross_margin_pct') COMMENT='Gross margin percentage',
        FINANCIALS.AVG_OPERATING_MARGIN AS AVG(OPERATING_MARGIN_PCT) WITH SYNONYMS=('operating_margin','op_margin') COMMENT='Operating margin percentage',
        FINANCIALS.AVG_NET_MARGIN AS AVG(NET_MARGIN_PCT) WITH SYNONYMS=('net_margin','profit_margin') COMMENT='Net profit margin percentage',
        FINANCIALS.AVG_ROE AS AVG(ROE_PCT) WITH SYNONYMS=('roe','return_on_equity') COMMENT='Return on equity percentage',
        FINANCIALS.AVG_ROA AS AVG(ROA_PCT) WITH SYNONYMS=('roa','return_on_assets') COMMENT='Return on assets percentage',
        
        -- Financial health ratios
        FINANCIALS.AVG_DEBT_EQUITY AS AVG(DEBT_TO_EQUITY) WITH SYNONYMS=('debt_to_equity','leverage','d_e_ratio') COMMENT='Debt to equity ratio',
        FINANCIALS.AVG_CURRENT_RATIO AS AVG(CURRENT_RATIO) WITH SYNONYMS=('current_ratio','liquidity_ratio') COMMENT='Current ratio',
        
        -- Growth metric
        FINANCIALS.AVG_REVENUE_GROWTH AS AVG(REVENUE_GROWTH_PCT) WITH SYNONYMS=('revenue_growth','growth_rate','yoy_growth') COMMENT='Year-over-year revenue growth percentage',
        
        -- Investment memo metrics (heuristically calculated from real data)
        FINANCIALS.TAM_VALUE AS SUM(TAM) WITH SYNONYMS=('tam','total_addressable_market','market_size','addressable_market') COMMENT='Total Addressable Market (estimated as Revenue x Industry Multiplier)',
        FINANCIALS.CUSTOMER_COUNT AS SUM(ESTIMATED_CUSTOMER_COUNT) WITH SYNONYMS=('customers','total_customers','customer_base','customer_count') COMMENT='Estimated customer count (Revenue / Average Revenue Per Customer by industry)',
        FINANCIALS.NRR_PCT AS AVG(ESTIMATED_NRR_PCT) WITH SYNONYMS=('nrr','net_revenue_retention','dollar_retention','revenue_retention') COMMENT='Estimated Net Revenue Retention percentage (based on revenue growth)',
        
        -- Record counts
        FINANCIALS.PERIOD_COUNT AS COUNT(DISTINCT FINANCIAL_ID) WITH SYNONYMS=('periods','fiscal_periods','record_count') COMMENT='Number of fiscal periods',
        FINANCIALS.ISSUER_COUNT AS COUNT(DISTINCT IssuerID) WITH SYNONYMS=('issuers','companies','num_companies') COMMENT='Number of issuers/companies',
        
        -- Consensus estimate metrics
        CONSENSUS.CONSENSUS_MEAN_VALUE AS AVG(CONSENSUS_MEAN) WITH SYNONYMS=('consensus','mean_estimate','average_estimate') COMMENT='Consensus mean estimate value',
        CONSENSUS.CONSENSUS_HIGH_VALUE AS MAX(CONSENSUS_HIGH) WITH SYNONYMS=('high_estimate','bull_case','optimistic_estimate') COMMENT='Highest consensus estimate',
        CONSENSUS.CONSENSUS_LOW_VALUE AS MIN(CONSENSUS_LOW) WITH SYNONYMS=('low_estimate','bear_case','pessimistic_estimate') COMMENT='Lowest consensus estimate',
        CONSENSUS.AVG_NUM_ESTIMATES AS AVG(NUM_ESTIMATES) WITH SYNONYMS=('analyst_coverage','coverage_count','number_of_analysts') COMMENT='Average number of analyst estimates',
        
        -- Price target and rating metrics
        ANALYST_ESTIMATES.AVG_PRICE_TARGET AS AVG(CASE WHEN DATA_ITEM_ID = 5005 THEN DATA_VALUE END) WITH SYNONYMS=('price_target','target_price','pt') COMMENT='Average analyst price target',
        ANALYST_ESTIMATES.MAX_PRICE_TARGET AS MAX(CASE WHEN DATA_ITEM_ID = 5005 THEN DATA_VALUE END) WITH SYNONYMS=('high_price_target','bull_target') COMMENT='Highest analyst price target',
        ANALYST_ESTIMATES.MIN_PRICE_TARGET AS MIN(CASE WHEN DATA_ITEM_ID = 5005 THEN DATA_VALUE END) WITH SYNONYMS=('low_price_target','bear_target') COMMENT='Lowest analyst price target',
        ANALYST_ESTIMATES.AVG_RATING AS AVG(CASE WHEN DATA_ITEM_ID = 5006 THEN DATA_VALUE END) WITH SYNONYMS=('rating','analyst_rating','average_rating') COMMENT='Average analyst rating (1=Buy, 2=Outperform, 3=Hold, 4=Underperform, 5=Sell)',
        ANALYST_ESTIMATES.ESTIMATE_COUNT AS COUNT(ESTIMATE_ID) WITH SYNONYMS=('estimate_count','analyst_count') COMMENT='Count of analyst estimates'
    )
    COMMENT='Fundamentals semantic view for company financial analysis. Provides access to real SEC financial statements (FACT_SEC_FINANCIALS), analyst estimates, price targets, and ratings. Financial data sourced from SEC 10-K and 10-Q filings via SNOWFLAKE_PUBLIC_DATA_FREE. Investment memo metrics (TAM, Customer Count, NRR) are calculated heuristically from real revenue data.'
    WITH EXTENSION (CA='{{"tables":[{{"name":"COMPANIES","dimensions":[{{"name":"CompanyName"}},{{"name":"CountryCode"}},{{"name":"IndustryDescription"}},{{"name":"CIK"}}]}},{{"name":"FINANCIALS","dimensions":[{{"name":"FiscalYear"}},{{"name":"FiscalPeriod"}},{{"name":"PeriodEndDate"}},{{"name":"Currency"}}],"metrics":[{{"name":"TOTAL_REVENUE"}},{{"name":"TOTAL_NET_INCOME"}},{{"name":"TOTAL_GROSS_PROFIT"}},{{"name":"TOTAL_OPERATING_INCOME"}},{{"name":"TOTAL_EBITDA"}},{{"name":"TOTAL_RD_EXPENSE"}},{{"name":"TOTAL_ASSETS_AMT"}},{{"name":"TOTAL_LIABILITIES_AMT"}},{{"name":"TOTAL_EQUITY_AMT"}},{{"name":"TOTAL_CASH"}},{{"name":"TOTAL_DEBT"}},{{"name":"TOTAL_OPERATING_CF"}},{{"name":"TOTAL_FCF"}},{{"name":"TOTAL_CAPEX"}},{{"name":"AVG_GROSS_MARGIN"}},{{"name":"AVG_OPERATING_MARGIN"}},{{"name":"AVG_NET_MARGIN"}},{{"name":"AVG_ROE"}},{{"name":"AVG_ROA"}},{{"name":"AVG_DEBT_EQUITY"}},{{"name":"AVG_CURRENT_RATIO"}},{{"name":"AVG_REVENUE_GROWTH"}},{{"name":"TAM_VALUE"}},{{"name":"CUSTOMER_COUNT"}},{{"name":"NRR_PCT"}},{{"name":"PERIOD_COUNT"}},{{"name":"COMPANY_COUNT"}}]}},{{"name":"CONSENSUS","metrics":[{{"name":"CONSENSUS_MEAN_VALUE"}},{{"name":"CONSENSUS_HIGH_VALUE"}},{{"name":"CONSENSUS_LOW_VALUE"}},{{"name":"AVG_NUM_ESTIMATES"}}]}},{{"name":"ANALYST_ESTIMATES","metrics":[{{"name":"AVG_PRICE_TARGET"}},{{"name":"MAX_PRICE_TARGET"}},{{"name":"MIN_PRICE_TARGET"}},{{"name":"AVG_RATING"}},{{"name":"ESTIMATE_COUNT"}}]}},{{"name":"BROKERS","dimensions":[{{"name":"BrokerName"}}]}},{{"name":"ANALYSTS","dimensions":[{{"name":"AnalystName"}},{{"name":"SectorCoverage"}}]}}],"relationships":[{{"name":"FINANCIALS_TO_COMPANIES"}},{{"name":"CONSENSUS_TO_COMPANIES"}},{{"name":"ESTIMATES_TO_COMPANIES"}},{{"name":"ESTIMATES_TO_ANALYSTS"}},{{"name":"ESTIMATES_TO_BROKERS"}}],"verified_queries":[{{"name":"revenue_summary","question":"What is the revenue for each company?","sql":"SELECT * FROM SEMANTIC_VIEW({database_name}.AI.SAM_FUNDAMENTALS_VIEW METRICS TOTAL_REVENUE, TOTAL_NET_INCOME, AVG_GROSS_MARGIN DIMENSIONS CompanyName, FiscalYear)","use_as_onboarding_question":true}},{{"name":"profitability_analysis","question":"What are the profitability margins?","sql":"SELECT * FROM SEMANTIC_VIEW({database_name}.AI.SAM_FUNDAMENTALS_VIEW METRICS AVG_GROSS_MARGIN, AVG_OPERATING_MARGIN, AVG_NET_MARGIN, AVG_ROE DIMENSIONS CompanyName)","use_as_onboarding_question":true}},{{"name":"investment_memo_metrics","question":"What is the TAM and customer count?","sql":"SELECT * FROM SEMANTIC_VIEW({database_name}.AI.SAM_FUNDAMENTALS_VIEW METRICS TAM_VALUE, CUSTOMER_COUNT, NRR_PCT, AVG_REVENUE_GROWTH DIMENSIONS CompanyName)","use_as_onboarding_question":true}},{{"name":"consensus_summary","question":"What is the analyst consensus?","sql":"SELECT * FROM SEMANTIC_VIEW({database_name}.AI.SAM_FUNDAMENTALS_VIEW METRICS CONSENSUS_MEAN_VALUE, CONSENSUS_HIGH_VALUE, CONSENSUS_LOW_VALUE, AVG_NUM_ESTIMATES)","use_as_onboarding_question":true}},{{"name":"price_targets","question":"What are the analyst price targets?","sql":"SELECT * FROM SEMANTIC_VIEW({database_name}.AI.SAM_FUNDAMENTALS_VIEW METRICS AVG_PRICE_TARGET, MAX_PRICE_TARGET, MIN_PRICE_TARGET, AVG_RATING)","use_as_onboarding_question":false}}],"module_custom_instructions":{{"sql_generation":"This view uses real SEC financial data from FACT_SEC_FINANCIALS. Use TOTAL_REVENUE for revenue queries. Use TOTAL_NET_INCOME for earnings. Use AVG_GROSS_MARGIN, AVG_OPERATING_MARGIN, AVG_NET_MARGIN for margin analysis. Use TOTAL_EBITDA for EBITDA queries. Use TAM_VALUE for TAM/market size queries. Use CUSTOMER_COUNT for customer count (note: estimated from revenue). Use NRR_PCT for Net Revenue Retention (note: estimated from revenue growth). Use AVG_REVENUE_GROWTH for growth analysis. Always order by FiscalYear descending to show most recent first. Currency dimension shows reporting currency. For consensus estimates, show the number of analysts covering alongside the estimate values.","question_categorization":"If users ask about \\'financials\\', \\'fundamentals\\', \\'revenue\\', \\'earnings\\', \\'margins\\', use FINANCIALS metrics. If users ask about \\'estimates\\' or \\'consensus\\', use CONSENSUS table. If users ask about \\'price targets\\' or \\'ratings\\', use ANALYST_ESTIMATES table. If users ask about \\'analysts\\' or \\'brokers\\', include ANALYSTS and BROKERS dimensions. If users ask about \\'TAM\\', \\'market size\\', \\'addressable market\\', use TAM_VALUE metric (note: estimated). If users ask about \\'customers\\', \\'customer count\\', use CUSTOMER_COUNT metric (note: estimated from revenue). If users ask about \\'retention\\', \\'NRR\\', \\'net revenue retention\\', use NRR_PCT metric (note: estimated from growth)."}}}}');
    """).collect()
    
    log_detail(" Created semantic view: SAM_FUNDAMENTALS_VIEW (using real SEC data)")


def create_real_stock_prices_semantic_view(session: Session):
    """
    Create semantic view for REAL stock price data from SNOWFLAKE_PUBLIC_DATA_FREE.
    
    This view provides access to real daily stock prices from Nasdaq.
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    
    # Check if real data tables exist
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_STOCK_PRICES LIMIT 1").collect()
    except Exception:
        log_warning("  FACT_STOCK_PRICES not found - skipping SAM_STOCK_PRICES_VIEW creation")
        return
    
    log_detail("Creating SAM_STOCK_PRICES_VIEW for real stock price data...")
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {database_name}.AI.SAM_STOCK_PRICES_VIEW
    TABLES (
        PRICES AS {database_name}.{market_data_schema}.FACT_STOCK_PRICES
            PRIMARY KEY (PRICE_ID)
            WITH SYNONYMS=('prices','stock_prices','market_prices','daily_prices')
            COMMENT='Real daily stock prices from Nasdaq.',
        SECURITIES AS {database_name}.{curated_schema}.DIM_SECURITY
            PRIMARY KEY (SECURITYID)
            WITH SYNONYMS=('securities','stocks','equities')
            COMMENT='Security master data',
        ISSUERS AS {database_name}.{curated_schema}.DIM_ISSUER
            PRIMARY KEY (ISSUERID)
            WITH SYNONYMS=('issuers','companies')
            COMMENT='Issuer dimension'
    )
    RELATIONSHIPS (
        PRICES_TO_SECURITIES AS PRICES(SECURITYID) REFERENCES SECURITIES(SECURITYID),
        PRICES_TO_ISSUERS AS PRICES(ISSUERID) REFERENCES ISSUERS(ISSUERID),
        SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID)
    )
    DIMENSIONS (
        -- Syntax: <semantic_name> AS <database_column> - "Call it X, it's really Y"
        -- Note: TICKER available via PRICES(SecurityID) -> SECURITIES(SecurityID) relationship
        SECURITIES.Ticker AS Ticker WITH SYNONYMS=('ticker','symbol','stock_symbol') COMMENT='Stock ticker symbol (from DIM_SECURITY)',
        SECURITIES.Description AS Description WITH SYNONYMS=('security_name','company_name','name') COMMENT='Security/company name',
        SECURITIES.ASSETCLASS AS AssetClass WITH SYNONYMS=('asset_class','type') COMMENT='Asset class',
        ISSUERS.LegalName AS LegalName WITH SYNONYMS=('issuer_name','legal_name') COMMENT='Legal issuer name',
        ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry') COMMENT='Industry classification (SIC)',
        ISSUERS.GICS_Sector AS GICS_SECTOR WITH SYNONYMS=('gics','gics_sector','sector','sector_classification') COMMENT='GICS Level 1 sector classification',
        PRICES.EXCHANGE AS PRIMARY_EXCHANGE_CODE WITH SYNONYMS=('exchange','exchange_code') COMMENT='Primary exchange code',
        PRICES.TRADE_DATE AS PRICE_DATE WITH SYNONYMS=('date','trading_date','as_of_date') COMMENT='Trading date'
    )
    METRICS (
        PRICES.CLOSE_PRICE AS AVG(PRICE_CLOSE) WITH SYNONYMS=('close','closing_price','price','last_price') COMMENT='Closing price',
        PRICES.OPEN_PRICE AS AVG(PRICE_OPEN) WITH SYNONYMS=('open','opening_price') COMMENT='Opening price',
        PRICES.HIGH_PRICE AS MAX(PRICE_HIGH) WITH SYNONYMS=('high','daily_high') COMMENT='Daily high price',
        PRICES.LOW_PRICE AS MIN(PRICE_LOW) WITH SYNONYMS=('low','daily_low') COMMENT='Daily low price',
        PRICES.TOTAL_VOLUME AS SUM(VOLUME) WITH SYNONYMS=('volume','trading_volume') COMMENT='Trading volume',
        PRICES.TRADING_DAYS AS COUNT(DISTINCT PRICE_DATE) WITH SYNONYMS=('trading_days','days') COMMENT='Number of trading days'
    )
    COMMENT='Real stock price semantic view from SNOWFLAKE_PUBLIC_DATA_FREE'
    """).collect()
    
    log_detail(" Created semantic view: SAM_STOCK_PRICES_VIEW")


def create_sec_financials_semantic_view(session: Session):
    """
    Create semantic view for comprehensive SEC financial statements from FACT_SEC_FINANCIALS
    and revenue segment breakdowns from FACT_SEC_SEGMENTS.
    
    This view provides access to:
    - Real Income Statement, Balance Sheet, and Cash Flow data (FACT_SEC_FINANCIALS)
    - Revenue segments by geography, business unit, customer, legal entity (FACT_SEC_SEGMENTS)
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    
    # Check if real data tables exist
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS LIMIT 1").collect()
    except Exception:
        log_warning("  FACT_SEC_FINANCIALS not found - skipping SAM_SEC_FINANCIALS_VIEW creation")
        return
    
    # Check if segments table exists (optional - view works without it)
    segments_table_exists = False
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_SEC_SEGMENTS LIMIT 1").collect()
        segments_table_exists = True
        log_detail("  FACT_SEC_SEGMENTS found - including segment dimensions")
    except Exception:
        log_warning("  FACT_SEC_SEGMENTS not found - creating view without segment data")
    
    log_detail("Creating SAM_SEC_FINANCIALS_VIEW for comprehensive SEC financial statements...")
    
    # Always create SAM_SEC_FINANCIALS_VIEW for consolidated financials
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {database_name}.AI.SAM_SEC_FINANCIALS_VIEW
    TABLES (
        FINANCIALS AS {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS
            PRIMARY KEY (FINANCIAL_ID)
            WITH SYNONYMS=('financials','financial_statements','sec_financials','company_financials')
            COMMENT='Comprehensive SEC financial statements including Income Statement, Balance Sheet, and Cash Flow.',
        ISSUERS AS {database_name}.{curated_schema}.DIM_ISSUER
            PRIMARY KEY (IssuerID)
            WITH SYNONYMS=('issuers','companies','firms','corporations','entities')
            COMMENT='Company/issuer master data (single source of truth for company information)'
    )
    RELATIONSHIPS (
        FINANCIALS_TO_ISSUERS AS FINANCIALS(IssuerID) REFERENCES ISSUERS(IssuerID)
    )
    DIMENSIONS (
        -- Company dimensions (using DIM_ISSUER as single source of truth via FK relationship)
        ISSUERS.CompanyName AS LEGALNAME WITH SYNONYMS=('company','company_name','firm_name','corporation','issuer','entity','name') COMMENT='Company legal name for filtering (e.g., MICROSOFT CORP, APPLE INC., NVIDIA CORP)',
        ISSUERS.Ticker AS PrimaryTicker WITH SYNONYMS=('ticker','symbol','stock_symbol','stock') COMMENT='Stock ticker symbol for filtering (e.g., MSFT, AAPL, NVDA)',
        ISSUERS.CIK AS CIK WITH SYNONYMS=('cik_number','sec_id','central_index_key') COMMENT='SEC Central Index Key (from DIM_ISSUER)',
        ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry','business_type') COMMENT='Industry classification (SIC)',
        ISSUERS.GICS_Sector AS GICS_SECTOR WITH SYNONYMS=('gics','gics_sector','sector','sector_classification') COMMENT='GICS Level 1 sector classification',
        
        -- Currency dimension
        FINANCIALS.Currency AS CURRENCY WITH SYNONYMS=('reporting_currency','currency_code','unit') COMMENT='Reporting currency (e.g., USD, EUR, CAD). Values are in actual units, not thousands or millions.',
        
        -- Time dimensions
        FINANCIALS.FiscalYear AS FISCAL_YEAR WITH SYNONYMS=('year','fy','fiscal') COMMENT='Fiscal year',
        FINANCIALS.FiscalPeriod AS FISCAL_PERIOD WITH SYNONYMS=('quarter','period','q') COMMENT='Fiscal period (FY, Q1, Q2, Q3, Q4)',
        FINANCIALS.PeriodEndDate AS PERIOD_END_DATE WITH SYNONYMS=('period_end','end_date','as_of_date') COMMENT='Period end date'
    )
    METRICS (
        -- Income Statement metrics
        FINANCIALS.TOTAL_REVENUE AS SUM(REVENUE) WITH SYNONYMS=('revenue','sales','total_revenue','top_line') COMMENT='Total revenue/sales',
        FINANCIALS.NET_INCOME_TOTAL AS SUM(NET_INCOME) WITH SYNONYMS=('net_income','earnings','profit','bottom_line') COMMENT='Net income',
        FINANCIALS.BASIC_EPS AS AVG(EPS_BASIC) WITH SYNONYMS=('eps','earnings_per_share','eps_basic') COMMENT='Basic earnings per share',
        FINANCIALS.DILUTED_EPS AS AVG(EPS_DILUTED) WITH SYNONYMS=('diluted_eps','eps_diluted') COMMENT='Diluted earnings per share',
        FINANCIALS.GROSS_PROFIT_TOTAL AS SUM(GROSS_PROFIT) WITH SYNONYMS=('gross_profit','gross_margin_dollars') COMMENT='Gross profit',
        FINANCIALS.OPERATING_INCOME_TOTAL AS SUM(OPERATING_INCOME) WITH SYNONYMS=('operating_income','ebit','operating_profit') COMMENT='Operating income',
        FINANCIALS.RD_EXPENSE_TOTAL AS SUM(RD_EXPENSE) WITH SYNONYMS=('rd','research_development','rd_expense') COMMENT='Research and development expense',
        
        -- Balance Sheet metrics
        FINANCIALS.ASSETS_TOTAL AS SUM(TOTAL_ASSETS) WITH SYNONYMS=('total_assets','assets') COMMENT='Total assets',
        FINANCIALS.LIABILITIES_TOTAL AS SUM(TOTAL_LIABILITIES) WITH SYNONYMS=('total_liabilities','liabilities') COMMENT='Total liabilities',
        FINANCIALS.EQUITY_TOTAL AS SUM(TOTAL_EQUITY) WITH SYNONYMS=('stockholders_equity','equity','book_value') COMMENT='Total stockholders equity',
        FINANCIALS.CASH_TOTAL AS SUM(CASH_AND_EQUIVALENTS) WITH SYNONYMS=('cash','cash_equivalents','liquidity') COMMENT='Cash and cash equivalents',
        FINANCIALS.DEBT_TOTAL AS SUM(LONG_TERM_DEBT) WITH SYNONYMS=('long_term_debt','debt') COMMENT='Long-term debt',
        
        -- Cash Flow metrics
        FINANCIALS.OPERATING_CF_TOTAL AS SUM(OPERATING_CASH_FLOW) WITH SYNONYMS=('operating_cash_flow','cfo','ocf') COMMENT='Cash from operations',
        FINANCIALS.INVESTING_CF_TOTAL AS SUM(INVESTING_CASH_FLOW) WITH SYNONYMS=('investing_cash_flow','cfi') COMMENT='Cash from investing',
        FINANCIALS.FINANCING_CF_TOTAL AS SUM(FINANCING_CASH_FLOW) WITH SYNONYMS=('financing_cash_flow','cff') COMMENT='Cash from financing',
        FINANCIALS.FCF_TOTAL AS SUM(FREE_CASH_FLOW) WITH SYNONYMS=('free_cash_flow','fcf') COMMENT='Free cash flow (OCF - CapEx)',
        FINANCIALS.CAPEX_TOTAL AS SUM(CAPEX) WITH SYNONYMS=('capital_expenditure','capex','pp_and_e_spending') COMMENT='Capital expenditure',
        
        -- Profitability ratios (averages)
        FINANCIALS.AVG_GROSS_MARGIN AS AVG(GROSS_MARGIN_PCT) WITH SYNONYMS=('gross_margin','gross_margin_pct') COMMENT='Gross margin percentage',
        FINANCIALS.AVG_OPERATING_MARGIN AS AVG(OPERATING_MARGIN_PCT) WITH SYNONYMS=('operating_margin','op_margin') COMMENT='Operating margin percentage',
        FINANCIALS.AVG_NET_MARGIN AS AVG(NET_MARGIN_PCT) WITH SYNONYMS=('net_margin','profit_margin') COMMENT='Net profit margin percentage',
        FINANCIALS.AVG_ROE AS AVG(ROE_PCT) WITH SYNONYMS=('roe','return_on_equity') COMMENT='Return on equity percentage',
        FINANCIALS.AVG_ROA AS AVG(ROA_PCT) WITH SYNONYMS=('roa','return_on_assets') COMMENT='Return on assets percentage',
        
        -- Financial health ratios
        FINANCIALS.AVG_DEBT_EQUITY AS AVG(DEBT_TO_EQUITY) WITH SYNONYMS=('debt_to_equity','leverage','d_e_ratio') COMMENT='Debt to equity ratio',
        FINANCIALS.AVG_CURRENT_RATIO AS AVG(CURRENT_RATIO) WITH SYNONYMS=('current_ratio','liquidity_ratio') COMMENT='Current ratio',
        
        -- Counts
        FINANCIALS.PERIOD_COUNT AS COUNT(DISTINCT CONCAT(CIK, '-', FISCAL_YEAR, '-', FISCAL_PERIOD)) WITH SYNONYMS=('periods','fiscal_periods') COMMENT='Number of fiscal periods',
        FINANCIALS.ISSUER_COUNT AS COUNT(DISTINCT IssuerID) WITH SYNONYMS=('issuers','companies','num_companies') COMMENT='Number of issuers/companies'
    )
    COMMENT='Comprehensive SEC financial statements semantic view with Income Statement, Balance Sheet, and Cash Flow metrics from SEC XBRL filings. All monetary values are in actual units (not thousands or millions). For geographic/segment revenue breakdowns, use SAM_SEC_SEGMENTS_VIEW.'
    """).collect()
    log_detail("  Created semantic view: SAM_SEC_FINANCIALS_VIEW (consolidated financials)")
    
    # Create separate SAM_SEC_SEGMENTS_VIEW if segments table exists
    if segments_table_exists:
        session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {database_name}.AI.SAM_SEC_SEGMENTS_VIEW
    TABLES (
        SEGMENTS AS {database_name}.{market_data_schema}.FACT_SEC_SEGMENTS
            PRIMARY KEY (SEGMENT_ID)
            WITH SYNONYMS=('segments','revenue_segments','geographic_segments','business_segments','regional_revenue')
            COMMENT='Revenue segment breakdowns by geography, business unit, customer, and legal entity from SEC filings',
        ISSUERS AS {database_name}.{curated_schema}.DIM_ISSUER
            PRIMARY KEY (IssuerID)
            WITH SYNONYMS=('issuers','companies','firms','corporations','entities')
            COMMENT='Company/issuer master data'
    )
    RELATIONSHIPS (
        SEGMENTS_TO_ISSUERS AS SEGMENTS(IssuerID) REFERENCES ISSUERS(IssuerID)
    )
    DIMENSIONS (
        -- Company dimensions
        ISSUERS.CompanyName AS LEGALNAME WITH SYNONYMS=('company','company_name','firm_name') COMMENT='Company name',
        ISSUERS.CIK AS CIK WITH SYNONYMS=('cik_number','sec_id') COMMENT='SEC Central Index Key',
        ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry') COMMENT='Industry classification (SIC)',
        ISSUERS.GICS_Sector AS GICS_SECTOR WITH SYNONYMS=('gics','gics_sector','sector','sector_classification') COMMENT='GICS Level 1 sector classification',
        
        -- Time dimensions
        SEGMENTS.FiscalYear AS FISCAL_YEAR WITH SYNONYMS=('year','fy','fiscal') COMMENT='Fiscal year',
        SEGMENTS.FiscalPeriod AS FISCAL_PERIOD WITH SYNONYMS=('quarter','period','q') COMMENT='Fiscal period (FY, Q1, Q2, Q3, Q4)',
        SEGMENTS.PeriodEndDate AS PERIOD_END_DATE WITH SYNONYMS=('period_end','end_date') COMMENT='Period end date',
        
        -- Segment dimensions
        SEGMENTS.Geography AS GEOGRAPHY WITH SYNONYMS=('geography','region','geo','location','geographic_region','europe','americas','asia') COMMENT='Geographic segment (Europe, Americas, Asia Pacific, etc.)',
        SEGMENTS.BusinessSegment AS BUSINESS_SEGMENT WITH SYNONYMS=('segment','business_unit','division','product_line') COMMENT='Business segment (product, service, brand)',
        SEGMENTS.BusinessSubsegment AS BUSINESS_SUBSEGMENT WITH SYNONYMS=('subsegment','sub_segment') COMMENT='Business sub-segment',
        SEGMENTS.Customer AS CUSTOMER WITH SYNONYMS=('major_customer','key_customer') COMMENT='Major customer name if reported',
        SEGMENTS.LegalEntity AS LEGAL_ENTITY WITH SYNONYMS=('subsidiary','legal_entity') COMMENT='Legal entity or subsidiary'
    )
    METRICS (
        -- Segment revenue
        SEGMENTS.SEGMENT_REVENUE_TOTAL AS SUM(SEGMENT_REVENUE) WITH SYNONYMS=('segment_revenue','geographic_revenue','regional_revenue','division_revenue','european_revenue','americas_revenue') COMMENT='Revenue by segment (geography, business unit, etc.)',
        SEGMENTS.SEGMENT_COUNT AS COUNT(DISTINCT SEGMENT_ID) WITH SYNONYMS=('segment_count','number_of_segments') COMMENT='Number of segment records'
    )
    COMMENT='SEC revenue segment breakdowns by geography (Europe, Americas, Asia Pacific), business unit, customer, and legal entity. Use GEOGRAPHY dimension to analyze regional revenue (e.g., BlackRock European division revenue). Use CompanyName to filter by company.'
        """).collect()
        log_detail("  Created semantic view: SAM_SEC_SEGMENTS_VIEW (geographic/business segments)")
