"""
Semantic Views Builder for SAM Demo

This module creates all Cortex Analyst semantic views for portfolio analytics,
research, quantitative analysis, implementation planning, SEC filings, supply chain, 
and middle office operations.
"""

from snowflake.snowpark import Session
from typing import List
import config

def create_semantic_views(session: Session, scenarios: List[str] = None):
    """Create semantic views required for the specified scenarios."""
    
    # Always create the main analyst view
    try:
        create_analyst_semantic_view(session)
    except Exception as e:
        config.log_error(f" Failed to create SAM_ANALYST_VIEW: {e}")
        raise
    
    # Create scenario-specific semantic views
    if scenarios and 'research_copilot' in scenarios:
        try:
            create_research_semantic_view(session)
        except Exception as e:
            config.log_error(f" CRITICAL FAILURE: Could not create research semantic view: {e}")
            raise Exception(f"Failed to create research semantic view: {e}")
    
    # Create quantitative semantic view for factor analysis
    if scenarios and 'quant_analyst' in scenarios:
        try:
            create_quantitative_semantic_view(session)
        except Exception as e:
            config.log_error(f" CRITICAL FAILURE: Could not create quantitative semantic view: {e}")
            raise Exception(f"Failed to create quantitative semantic view: {e}")
    
    # Create implementation semantic view for portfolio management
    if scenarios and ('portfolio_copilot' in scenarios or 'sales_advisor' in scenarios):
        try:
            create_implementation_semantic_view(session)
        except Exception as e:
            config.log_warning(f"  Warning: Could not create implementation semantic view: {e}")
    
    # Create SEC filings semantic view for financial analysis
    try:
        create_sec_filings_semantic_view(session)
    except Exception as e:
        config.log_warning(f"  Warning: Could not create SEC filings semantic view: {e}")
    
    # Create supply chain semantic view for risk verification
    if scenarios and 'portfolio_copilot' in scenarios:
        try:
            create_supply_chain_semantic_view(session)
        except Exception as e:
            config.log_warning(f"  Warning: Could not create supply chain semantic view: {e}")
    
    # Create middle office semantic view for operations monitoring
    if scenarios and 'middle_office_copilot' in scenarios:
        try:
            create_middle_office_semantic_view(session)
        except Exception as e:
            config.log_warning(f"  Warning: Could not create middle office semantic view: {e}")
    
    # Create executive semantic view for firm-wide KPIs and client analytics
    if scenarios and 'executive_copilot' in scenarios:
        try:
            create_executive_semantic_view(session)
        except Exception as e:
            config.log_warning(f"  Warning: Could not create executive semantic view: {e}")
    
    # Create fundamentals semantic view for MARKET_DATA financial analysis
    if scenarios and 'research_copilot' in scenarios:
        try:
            create_fundamentals_semantic_view(session)
        except Exception as e:
            config.log_warning(f"  Warning: Could not create fundamentals semantic view: {e}")
            config.log_warning(f"Run with --scope structured first to generate MARKET_DATA tables")
    
    # Create real SEC data semantic views (if real data is enabled and available)
    if config.REAL_DATA_SOURCES.get('enabled', False):
        try:
            create_real_sec_semantic_view(session)
        except Exception as e:
            config.log_warning(f"  Warning: Could not create real SEC semantic view: {e}")
        
        try:
            create_real_stock_prices_semantic_view(session)
        except Exception as e:
            config.log_warning(f"  Warning: Could not create real stock prices semantic view: {e}")
        
        try:
            create_sec_financials_semantic_view(session)
        except Exception as e:
            config.log_warning(f"  Warning: Could not create SEC financials semantic view: {e}")

def create_analyst_semantic_view(session: Session):
    """Create main portfolio analytics semantic view (SAM_ANALYST_VIEW)."""
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_ANALYST_VIEW
	TABLES (
		HOLDINGS AS {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR
			PRIMARY KEY (HOLDINGDATE, PORTFOLIOID, SECURITYID) 
			WITH SYNONYMS=('positions','investments','allocations','holdings') 
			COMMENT='Daily portfolio holdings and positions. Each portfolio holding has multiple rows. When no time period is provided always get the latest value by date.',
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
			COMMENT='Issuer and corporate hierarchy data'
	)
	RELATIONSHIPS (
		HOLDINGS_TO_PORTFOLIOS AS HOLDINGS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		HOLDINGS_TO_SECURITIES AS HOLDINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID)
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
		ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry','sector','industry_type','sic_industry','business_type','industry_description','industry_classification') COMMENT='SIC industry classification with granular descriptions (e.g., Semiconductors and related devices, Computer programming services, Motor vehicles and car bodies). Use this for industry-level filtering and analysis.',
		ISSUERS.CountryOfIncorporation AS COUNTRYOFINCORPORATION WITH SYNONYMS=('domicile','country_of_risk','country') COMMENT='Country of incorporation using 2-letter ISO codes (e.g., TW for Taiwan, US for United States, GB for United Kingdom)',
		
		-- Time dimensions
		HOLDINGS.HOLDINGDATE AS HoldingDate WITH SYNONYMS=('position_date','as_of_date','date') COMMENT='Holdings as-of date'
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
		
		-- Mandate compliance metrics (for Scenario 3.2)
		HOLDINGS.AI_GROWTH_SCORE AS AVG(CASE 
			WHEN SECURITIES.Ticker IN ('NVDA', 'MSFT', 'GOOGL', 'META', 'AMZN', 'AAPL') THEN 
				CASE SECURITIES.Ticker
					WHEN 'NVDA' THEN 92
					WHEN 'MSFT' THEN 89
					WHEN 'GOOGL' THEN 85
					WHEN 'META' THEN 82
					WHEN 'AMZN' THEN 88
					WHEN 'AAPL' THEN 87
					ELSE 75
				END
			ELSE 75
		END) WITH SYNONYMS=('ai_score','innovation_score','ai_growth','ai_potential','technology_score') COMMENT='Proprietary AI Growth Score (0-100) measuring AI/ML innovation potential and market positioning. Higher scores indicate stronger AI capabilities, patent portfolios, and growth potential in artificial intelligence.'
	)
	COMMENT='Multi-asset semantic view for portfolio analytics with issuer hierarchy support and mandate compliance metrics'
	WITH EXTENSION (CA='{{"tables":[{{"name":"HOLDINGS","metrics":[{{"name":"AI_GROWTH_SCORE"}},{{"name":"HOLDING_COUNT"}},{{"name":"ISSUER_EXPOSURE"}},{{"name":"MAX_POSITION_WEIGHT"}},{{"name":"PORTFOLIO_WEIGHT"}},{{"name":"PORTFOLIO_WEIGHT_PCT"}},{{"name":"TOTAL_MARKET_VALUE"}}],"time_dimensions":[{{"name":"HoldingDate","expr":"HOLDINGDATE","data_type":"DATE","synonyms":["position_date","as_of_date","portfolio_date","valuation_date"],"description":"The date when portfolio holdings were valued and recorded. Use this for historical analysis and period comparisons."}},{{"name":"holding_month","expr":"DATE_TRUNC(\\'MONTH\\', HOLDINGDATE)","data_type":"DATE","synonyms":["month","monthly","month_end"],"description":"Monthly aggregation of holding dates for trend analysis and month-over-month comparisons."}},{{"name":"holding_quarter","expr":"DATE_TRUNC(\\'QUARTER\\', HOLDINGDATE)","data_type":"DATE","synonyms":["quarter","quarterly","quarter_end"],"description":"Quarterly aggregation for quarterly reporting and period-over-period analysis."}}]}},{{"name":"ISSUERS","dimensions":[{{"name":"COUNTRYOFINCORPORATION"}},{{"name":"SIC_DESCRIPTION"}},{{"name":"LEGALNAME"}}]}},{{"name":"PORTFOLIOS","dimensions":[{{"name":"PortfolioName"}},{{"name":"Strategy"}}]}},{{"name":"SECURITIES","dimensions":[{{"name":"AssetClass"}},{{"name":"Description"}},{{"name":"Ticker"}}]}}],"relationships":[{{"name":"HOLDINGS_TO_PORTFOLIOS"}},{{"name":"HOLDINGS_TO_SECURITIES"}},{{"name":"SECURITIES_TO_ISSUERS"}}],"verified_queries":[{{"name":"top_holdings_by_portfolio","question":"What are the top 10 holdings by market value in the SAM Technology & Infrastructure portfolio?","sql":"SELECT __SECURITIES.DESCRIPTION, __SECURITIES.TICKER, __HOLDINGS.MARKETVALUE_BASE, (__HOLDINGS.MARKETVALUE_BASE / SUM(__HOLDINGS.MARKETVALUE_BASE) OVER (PARTITION BY __HOLDINGS.PORTFOLIOID)) * 100 AS WEIGHT_PCT FROM __HOLDINGS JOIN __SECURITIES ON __HOLDINGS.SECURITYID = __SECURITIES.SECURITYID JOIN __PORTFOLIOS ON __HOLDINGS.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID WHERE __PORTFOLIOS.PORTFOLIONAME = \\'SAM Technology & Infrastructure\\' AND __HOLDINGS.HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM __HOLDINGS) ORDER BY __HOLDINGS.MARKETVALUE_BASE DESC LIMIT 10","use_as_onboarding_question":true}},{{"name":"sector_allocation_by_portfolio","question":"What is the sector allocation for the SAM Technology & Infrastructure portfolio?","sql":"SELECT __ISSUERS.Industry, SUM(__HOLDINGS.MARKETVALUE_BASE) AS SECTOR_VALUE, (SUM(__HOLDINGS.MARKETVALUE_BASE) / SUM(SUM(__HOLDINGS.MARKETVALUE_BASE)) OVER ()) * 100 AS SECTOR_WEIGHT_PCT FROM __HOLDINGS JOIN __SECURITIES ON __HOLDINGS.SECURITYID = __SECURITIES.SECURITYID JOIN __ISSUERS ON __SECURITIES.ISSUERID = __ISSUERS.ISSUERID JOIN __PORTFOLIOS ON __HOLDINGS.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID WHERE __PORTFOLIOS.PORTFOLIONAME = \\'SAM Technology & Infrastructure\\' AND __HOLDINGS.HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM __HOLDINGS) GROUP BY __ISSUERS.Industry ORDER BY SECTOR_VALUE DESC","use_as_onboarding_question":true}},{{"name":"concentration_warnings","question":"Which portfolios have positions above the 6.5% concentration warning threshold?","sql":"WITH position_weights AS (SELECT __HOLDINGS.PORTFOLIOID, __HOLDINGS.SECURITYID, __HOLDINGS.MARKETVALUE_BASE, (__HOLDINGS.MARKETVALUE_BASE / SUM(__HOLDINGS.MARKETVALUE_BASE) OVER (PARTITION BY __HOLDINGS.PORTFOLIOID)) * 100 AS POSITION_WEIGHT_PCT FROM __HOLDINGS WHERE __HOLDINGS.HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM __HOLDINGS)) SELECT __PORTFOLIOS.PORTFOLIONAME, __SECURITIES.DESCRIPTION, __SECURITIES.TICKER, pw.POSITION_WEIGHT_PCT FROM position_weights pw JOIN __SECURITIES ON pw.SECURITYID = __SECURITIES.SECURITYID JOIN __PORTFOLIOS ON pw.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID WHERE pw.POSITION_WEIGHT_PCT > 6.5 ORDER BY pw.POSITION_WEIGHT_PCT DESC","use_as_onboarding_question":false}},{{"name":"issuer_exposure_analysis","question":"What is the total exposure to Apple and Microsoft across all portfolios?","sql":"SELECT __ISSUERS.LegalName, __ISSUERS.Industry, SUM(__HOLDINGS.MARKETVALUE_BASE) AS TOTAL_ISSUER_EXPOSURE, COUNT(DISTINCT __PORTFOLIOS.PORTFOLIOID) AS PORTFOLIOS_EXPOSED FROM __HOLDINGS JOIN __SECURITIES ON __HOLDINGS.SECURITYID = __SECURITIES.SECURITYID JOIN __ISSUERS ON __SECURITIES.ISSUERID = __ISSUERS.ISSUERID JOIN __PORTFOLIOS ON __HOLDINGS.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID WHERE __HOLDINGS.HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM __HOLDINGS) AND __SECURITIES.TICKER IN (\\'AAPL\\', \\'MSFT\\') GROUP BY __ISSUERS.ISSUERID, __ISSUERS.LegalName, __ISSUERS.Industry ORDER BY TOTAL_ISSUER_EXPOSURE DESC","use_as_onboarding_question":false}}],"module_custom_instructions":{{"sql_generation":"For portfolio weight calculations, always multiply by 100 to show percentages. For current holdings queries, automatically filter to the most recent holding date using WHERE HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM HOLDINGS). When calculating issuer exposure, aggregate MARKETVALUE_BASE across all securities of the same issuer. Always round market values to 2 decimal places and portfolio weights to 1 decimal place.","question_categorization":"If users ask about \\'funds\\' or \\'portfolios\\', treat these as the same concept referring to investment portfolios. If users ask about current holdings without specifying a date, assume they want the most recent data."}}}}');
    """).collect()
    

def create_research_semantic_view(session: Session):
    """Create semantic view for research with fundamentals and estimates data."""
    
    # First check if the fundamentals tables exist
    # Prefer MARKET_DATA tables if available (real data), fallback to CURATED (synthetic)
    curated_exists = True
    try:
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_FUNDAMENTALS LIMIT 1").collect()
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_ESTIMATES LIMIT 1").collect()
    except:
        curated_exists = False
    
    # Check if MARKET_DATA has real financial data (which supersedes CURATED)
    market_data_exists = False
    try:
        result = session.sql(f"SELECT COUNT(*) as cnt FROM {config.DATABASE['name']}.MARKET_DATA.FACT_FINANCIAL_DATA").collect()
        market_data_exists = result[0]['CNT'] > 0
    except:
        pass
    
    if not curated_exists and not market_data_exists:
        config.log_warning("  Fundamentals tables not found in CURATED or MARKET_DATA, skipping research view creation")
        return
    
    # Note: SAM_RESEARCH_VIEW uses CURATED tables; for real data use SAM_REAL_SEC_VIEW and SAM_FUNDAMENTALS_VIEW
    
    # Create the research-focused semantic view
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_RESEARCH_VIEW
	TABLES (
		SECURITIES AS {config.DATABASE['name']}.CURATED.DIM_SECURITY
			PRIMARY KEY (SECURITYID) 
			WITH SYNONYMS=('companies','stocks','equities','securities') 
			COMMENT='Security master data',
		ISSUERS AS {config.DATABASE['name']}.CURATED.DIM_ISSUER
			PRIMARY KEY (ISSUERID) 
			WITH SYNONYMS=('issuers','entities','corporates') 
			COMMENT='Issuer and corporate data',
		FUNDAMENTALS AS {config.DATABASE['name']}.CURATED.FACT_FUNDAMENTALS
			PRIMARY KEY (SECURITY_ID, REPORTING_DATE, METRIC_NAME)
			WITH SYNONYMS=('financials','earnings','results','fundamentals')
			COMMENT='Company financial fundamentals',
		ESTIMATES AS {config.DATABASE['name']}.CURATED.FACT_ESTIMATES
			PRIMARY KEY (SECURITY_ID, ESTIMATE_DATE, FISCAL_PERIOD, METRIC_NAME) 
			WITH SYNONYMS=('forecasts','estimates','guidance','consensus') 
			COMMENT='Analyst estimates and guidance'
	)
	RELATIONSHIPS (
		SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID),
		FUNDAMENTALS_TO_SECURITIES AS FUNDAMENTALS(SECURITY_ID) REFERENCES SECURITIES(SECURITYID),
		ESTIMATES_TO_SECURITIES AS ESTIMATES(SECURITY_ID) REFERENCES SECURITIES(SECURITYID)
	)
	DIMENSIONS (
		-- Security dimensions  
		SECURITIES.TICKER AS Ticker WITH SYNONYMS=('ticker','symbol','ticker_symbol') COMMENT='Trading ticker symbol',
		SECURITIES.DESCRIPTION AS Description WITH SYNONYMS=('company','name','security_name') COMMENT='Company name',
		SECURITIES.ASSETCLASS AS AssetClass WITH SYNONYMS=('type','security_type','asset_class') COMMENT='Asset class',
		
		-- Issuer dimensions
		ISSUERS.LegalName AS LEGALNAME WITH SYNONYMS=('issuer','legal_name','entity_name') COMMENT='Legal entity name',
		ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry','sector','industry_type','sic_industry','business_type','industry_description') COMMENT='SIC industry classification with granular descriptions (e.g., Semiconductors and related devices, Computer programming services). Use for industry-level filtering.',
		ISSUERS.CountryOfIncorporation AS COUNTRYOFINCORPORATION WITH SYNONYMS=('domicile','country','headquarters') COMMENT='Country of incorporation using 2-letter ISO codes (e.g., TW for Taiwan, US for United States, GB for United Kingdom)',
		
		-- Fundamentals dimensions
		FUNDAMENTALS.REPORTING_DATE AS REPORTING_DATE WITH SYNONYMS=('report_date','earnings_date','date') COMMENT='Financial reporting date',
		FUNDAMENTALS.FISCAL_QUARTER AS FISCAL_QUARTER WITH SYNONYMS=('quarter','period','fiscal_period') COMMENT='Fiscal quarter',
		FUNDAMENTALS.METRIC_NAME AS METRIC_NAME WITH SYNONYMS=('metric','measure','financial_metric') COMMENT='Financial metric name',
		
		-- Estimates dimensions
		ESTIMATES.FISCAL_PERIOD AS FISCAL_PERIOD WITH SYNONYMS=('forecast_period','estimate_quarter') COMMENT='Estimate fiscal period'
	)
	METRICS (
		-- Actual financial metrics
		FUNDAMENTALS.ACTUAL_VALUE AS SUM(METRIC_VALUE) WITH SYNONYMS=('actual','reported','result') COMMENT='Actual reported value',
		
		-- Estimate metrics
		ESTIMATES.ESTIMATE_VALUE AS SUM(ESTIMATE_VALUE) WITH SYNONYMS=('estimate','forecast','consensus') COMMENT='Consensus estimate value',
		ESTIMATES.GUIDANCE_LOW AS MIN(GUIDANCE_LOW) WITH SYNONYMS=('guidance_low','low_guidance') COMMENT='Low end of guidance',
		ESTIMATES.GUIDANCE_HIGH AS MAX(GUIDANCE_HIGH) WITH SYNONYMS=('guidance_high','high_guidance') COMMENT='High end of guidance',
		
		-- Count metrics
		FUNDAMENTALS.METRIC_COUNT AS COUNT(DISTINCT FUNDAMENTALS.METRIC_NAME) WITH SYNONYMS=('metric_count','measures_count') COMMENT='Count of financial metrics',
		ESTIMATES.ESTIMATE_COUNT AS COUNT(DISTINCT ESTIMATES.METRIC_NAME) WITH SYNONYMS=('estimate_count','forecasts_count') COMMENT='Count of estimate metrics'
	)
	COMMENT='Research semantic view with fundamentals and estimates for earnings analysis';
    """).collect()
    

def create_quantitative_semantic_view(session: Session):
    """Create semantic view for quantitative analysis with factors and attribution."""
    
    # Required tables - check CURATED first, some may be replaced by MARKET_DATA
    required_tables = ['FACT_FACTOR_EXPOSURES', 'FACT_BENCHMARK_HOLDINGS']
    optional_tables = ['FACT_FUNDAMENTALS', 'FACT_ESTIMATES', 'FACT_MARKETDATA_TIMESERIES']  # May be in MARKET_DATA
    
    missing_required = []
    for table in required_tables:
        try:
            session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.{table} LIMIT 1").collect()
        except:
            missing_required.append(table)
    
    if missing_required:
        config.log_warning(f"  Required quantitative tables not found, skipping quant view creation: {missing_required}")
        return
    
    # Check optional tables - may be in CURATED or MARKET_DATA
    missing_optional = []
    for table in optional_tables:
        curated_ok = False
        market_data_ok = False
        try:
            session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.{table} LIMIT 1").collect()
            curated_ok = True
        except:
            pass
        # Check MARKET_DATA equivalents
        market_data_map = {
            'FACT_FUNDAMENTALS': 'FACT_FINANCIAL_DATA',
            'FACT_ESTIMATES': 'FACT_ESTIMATE_CONSENSUS',
            'FACT_MARKETDATA_TIMESERIES': 'FACT_STOCK_PRICES'
        }
        if table in market_data_map:
            try:
                session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.MARKET_DATA.{market_data_map[table]} LIMIT 1").collect()
                market_data_ok = True
            except:
                pass
        if not curated_ok and not market_data_ok:
            missing_optional.append(table)
    
    if missing_optional:
        config.log_warning(f"  Optional quantitative tables not found, quant view may have limited functionality: {missing_optional}")
    
    # Create the quantitative analysis semantic view
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {config.DATABASE['name']}.AI.SAM_QUANT_VIEW
	TABLES (
		HOLDINGS AS {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR
			PRIMARY KEY (HoldingDate, PORTFOLIOID, SECURITYID) 
			WITH SYNONYMS=('quant_positions','factor_holdings','quantitative_holdings','quant_allocations') 
			COMMENT='Portfolio holdings for factor analysis',
		PORTFOLIOS AS {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
			PRIMARY KEY (PORTFOLIOID) 
			WITH SYNONYMS=('quant_funds','factor_strategies','quantitative_mandates','quant_portfolios') 
			COMMENT='Portfolio information',
		SECURITIES AS {config.DATABASE['name']}.CURATED.DIM_SECURITY
			PRIMARY KEY (SECURITYID) 
			WITH SYNONYMS=('factor_companies','quant_stocks','quantitative_instruments','factor_securities') 
			COMMENT='Security reference data',
		ISSUERS AS {config.DATABASE['name']}.CURATED.DIM_ISSUER
			PRIMARY KEY (ISSUERID) 
			WITH SYNONYMS=('factor_issuers','quantitative_entities','quant_corporates') 
			COMMENT='Issuer data',
		FACTOR_EXPOSURES AS {config.DATABASE['name']}.CURATED.FACT_FACTOR_EXPOSURES
			PRIMARY KEY (SECURITYID, EXPOSURE_DATE, FACTOR_NAME)
			WITH SYNONYMS=('factors','loadings','exposures','factor_data')
			COMMENT='Factor exposures and loadings',
		FUNDAMENTALS AS {config.DATABASE['name']}.CURATED.FACT_FUNDAMENTALS
			PRIMARY KEY (SECURITY_ID, REPORTING_DATE, METRIC_NAME)
			WITH SYNONYMS=('financials','earnings','fundamentals','metrics')
			COMMENT='Financial fundamentals data',
		ESTIMATES AS {config.DATABASE['name']}.CURATED.FACT_ESTIMATES
			PRIMARY KEY (SECURITY_ID, ESTIMATE_DATE, FISCAL_PERIOD, METRIC_NAME)
			WITH SYNONYMS=('forecasts','estimates','consensus','guidance')
			COMMENT='Analyst estimates and guidance',
		MARKET_DATA AS {config.DATABASE['name']}.CURATED.FACT_MARKETDATA_TIMESERIES
			PRIMARY KEY (PriceDate, SECURITYID)
			WITH SYNONYMS=('prices','returns','market_data','performance')
			COMMENT='Market data and returns',
		BENCHMARK_HOLDINGS AS {config.DATABASE['name']}.CURATED.FACT_BENCHMARK_HOLDINGS
			PRIMARY KEY (HOLDING_DATE, BENCHMARKID, SECURITYID)
			WITH SYNONYMS=('benchmark_positions','index_holdings','benchmark_weights')
			COMMENT='Benchmark constituent holdings and weights'
	)
	RELATIONSHIPS (
		HOLDINGS_TO_PORTFOLIOS AS HOLDINGS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		HOLDINGS_TO_SECURITIES AS HOLDINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		SECURITIES_TO_ISSUERS AS SECURITIES(ISSUERID) REFERENCES ISSUERS(ISSUERID),
		FACTORS_TO_SECURITIES AS FACTOR_EXPOSURES(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		HOLDINGS_TO_FACTORS AS HOLDINGS(SECURITYID, HOLDINGDATE) REFERENCES FACTOR_EXPOSURES(SECURITYID, ASOF EXPOSURE_DATE),
		FUNDAMENTALS_TO_SECURITIES AS FUNDAMENTALS(SECURITY_ID) REFERENCES SECURITIES(SECURITYID),
		ESTIMATES_TO_SECURITIES AS ESTIMATES(SECURITY_ID) REFERENCES SECURITIES(SECURITYID),
		MARKET_DATA_TO_SECURITIES AS MARKET_DATA(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		BENCHMARK_TO_SECURITIES AS BENCHMARK_HOLDINGS(SECURITYID) REFERENCES SECURITIES(SECURITYID)
	)
	DIMENSIONS (
		-- Portfolio dimensions
		PORTFOLIOS.PORTFOLIONAME AS PortfolioName WITH SYNONYMS=('quant_fund_name','factor_strategy_name','quantitative_portfolio_name') COMMENT='Portfolio or fund name',
		PORTFOLIOS.STRATEGY AS Strategy WITH SYNONYMS=('quant_investment_strategy','factor_portfolio_strategy','value_strategy','growth_strategy','strategy_type') COMMENT='Investment strategy: Value, Growth, ESG, Core, Multi-Asset, Income',
		
		-- Security dimensions  
		SECURITIES.TICKER AS Ticker WITH SYNONYMS=('quant_ticker','factor_symbol','quantitative_ticker_symbol') COMMENT='Trading ticker symbol',
		SECURITIES.DESCRIPTION AS Description WITH SYNONYMS=('factor_company','quant_name','quantitative_security_name') COMMENT='Company name',
		SECURITIES.ASSETCLASS AS AssetClass WITH SYNONYMS=('quant_type','factor_security_type','quantitative_asset_class') COMMENT='Asset class',
		
		-- Issuer dimensions
		ISSUERS.LegalName AS LEGALNAME WITH SYNONYMS=('factor_issuer','quant_legal_name','quantitative_entity_name') COMMENT='Legal entity name',
		ISSUERS.Industry AS SIC_DESCRIPTION WITH SYNONYMS=('industry','sector','factor_sector','quant_industry','business_type','industry_classification') COMMENT='SIC industry classification with granular descriptions. Use for industry-level factor analysis and screening.',
		ISSUERS.CountryOfIncorporation AS COUNTRYOFINCORPORATION WITH SYNONYMS=('factor_domicile','quant_country','quantitative_headquarters') COMMENT='Country of incorporation using 2-letter ISO codes (e.g., TW for Taiwan, US for United States, GB for United Kingdom)',
		
		-- Factor dimensions
		FACTOR_EXPOSURES.FactorName AS FACTOR_NAME WITH SYNONYMS=('factor','factor_type','loading_type') COMMENT='Factor name (Value, Growth, Quality, etc.)',
		FACTOR_EXPOSURES.ExposureDate AS EXPOSURE_DATE WITH SYNONYMS=('factor_date','loading_date','exposure_date') COMMENT='Factor exposure date',
		
		-- Fundamental dimensions
		FUNDAMENTALS.ReportingDate AS REPORTING_DATE WITH SYNONYMS=('quant_report_date','factor_earnings_date','quantitative_fiscal_date') COMMENT='Financial reporting date',
		FUNDAMENTALS.FiscalQuarter AS FISCAL_QUARTER WITH SYNONYMS=('quant_quarter','factor_period','quantitative_fiscal_period') COMMENT='Fiscal quarter',
		FUNDAMENTALS.MetricName AS METRIC_NAME WITH SYNONYMS=('quant_metric','factor_measure','quantitative_financial_metric') COMMENT='Financial metric name',
		
		-- Time dimensions
		HOLDINGS.HoldingDate AS HOLDINGDATE WITH SYNONYMS=('quant_position_date','factor_as_of_date','quantitative_holding_date') COMMENT='Holdings as-of date',
		MARKET_DATA.PriceDate AS PRICEDATE WITH SYNONYMS=('quant_market_date','factor_price_date','quantitative_trading_date') COMMENT='Market data date'
	)
	METRICS (
		-- Portfolio metrics
		HOLDINGS.TOTAL_MARKET_VALUE AS SUM(MarketValue_Base) WITH SYNONYMS=('quant_exposure','factor_total_exposure','quantitative_market_value','quant_position_value') COMMENT='Total market value in base currency',
		HOLDINGS.PORTFOLIO_WEIGHT AS SUM(PortfolioWeight) WITH SYNONYMS=('quant_weight','factor_allocation','quantitative_portfolio_weight') COMMENT='Portfolio weight as decimal',
		HOLDINGS.PORTFOLIO_WEIGHT_PCT AS SUM(PortfolioWeight) * 100 WITH SYNONYMS=('quant_weight_percent','factor_allocation_percent','quantitative_percentage_weight') COMMENT='Portfolio weight as percentage',
		
		-- Factor metrics (enhanced for trend analysis)
		FACTOR_EXPOSURES.FACTOR_EXPOSURE AS SUM(EXPOSURE_VALUE) WITH SYNONYMS=('factor_loading','loading','factor_score','exposure') COMMENT='Factor exposure value',
		FACTOR_EXPOSURES.FACTOR_R_SQUARED AS AVG(R_SQUARED) WITH SYNONYMS=('r_squared','model_fit','factor_rsq') COMMENT='Factor model R-squared',
		FACTOR_EXPOSURES.MOMENTUM_SCORE AS AVG(CASE WHEN FACTOR_NAME = 'Momentum' THEN EXPOSURE_VALUE ELSE NULL END) WITH SYNONYMS=('momentum','momentum_factor','momentum_loading') COMMENT='Momentum factor exposure',
		FACTOR_EXPOSURES.QUALITY_SCORE AS AVG(CASE WHEN FACTOR_NAME = 'Quality' THEN EXPOSURE_VALUE ELSE NULL END) WITH SYNONYMS=('quality','quality_factor','quality_loading') COMMENT='Quality factor exposure',
		FACTOR_EXPOSURES.VALUE_SCORE AS AVG(CASE WHEN FACTOR_NAME = 'Value' THEN EXPOSURE_VALUE ELSE NULL END) WITH SYNONYMS=('value','value_factor','value_loading') COMMENT='Value factor exposure',
		FACTOR_EXPOSURES.GROWTH_SCORE AS AVG(CASE WHEN FACTOR_NAME = 'Growth' THEN EXPOSURE_VALUE ELSE NULL END) WITH SYNONYMS=('growth','growth_factor','growth_loading') COMMENT='Growth factor exposure',
		
		-- Performance metrics
		MARKET_DATA.TOTAL_RETURN AS SUM(TotalReturnFactor_Daily) WITH SYNONYMS=('quant_return','factor_performance','quantitative_total_return') COMMENT='Total return factor',
		MARKET_DATA.PRICE_RETURN AS AVG(Price_Close) WITH SYNONYMS=('quant_price','factor_closing_price','quantitative_market_price') COMMENT='Closing price',
		MARKET_DATA.VOLUME_TRADED AS SUM(Volume) WITH SYNONYMS=('quant_volume','factor_trading_volume','quantitative_daily_volume') COMMENT='Trading volume',
		
		-- Fundamental metrics
		FUNDAMENTALS.FUNDAMENTAL_VALUE AS SUM(METRIC_VALUE) WITH SYNONYMS=('quant_fundamental','factor_financial_value','quantitative_metric_value') COMMENT='Fundamental metric value',
		ESTIMATES.ESTIMATE_VALUE AS AVG(ESTIMATE_VALUE) WITH SYNONYMS=('quant_estimate','factor_forecast','quantitative_consensus') COMMENT='Consensus estimate value',
		
		-- Benchmark metrics
		BENCHMARK_HOLDINGS.BenchmarkWeight AS SUM(BENCHMARK_WEIGHT) WITH SYNONYMS=('quant_benchmark_allocation','factor_index_weight','quantitative_benchmark_percentage') COMMENT='Benchmark constituent weight'
	)
	COMMENT='Quantitative analysis semantic view with factor exposures, performance attribution, and systematic analysis capabilities'
	WITH EXTENSION (CA='{{"tables":[{{"name":"HOLDINGS","metrics":[{{"name":"PORTFOLIO_WEIGHT"}},{{"name":"PORTFOLIO_WEIGHT_PCT"}},{{"name":"TOTAL_MARKET_VALUE"}}],"time_dimensions":[{{"name":"holding_date","expr":"HOLDINGDATE","data_type":"DATE","synonyms":["position_date","holding_date","portfolio_date"],"description":"The date when portfolio holdings were valued. Use for current portfolio factor exposures."}},{{"name":"holding_month","expr":"DATE_TRUNC(\\'MONTH\\', HOLDINGDATE)","data_type":"DATE","synonyms":["month","monthly"],"description":"Monthly aggregation for holdings."}}]}},{{"name":"FACTOR_EXPOSURES","metrics":[{{"name":"FACTOR_EXPOSURE"}},{{"name":"FACTOR_R_SQUARED"}},{{"name":"GROWTH_SCORE"}},{{"name":"MOMENTUM_SCORE"}},{{"name":"QUALITY_SCORE"}},{{"name":"VALUE_SCORE"}}],"time_dimensions":[{{"name":"exposure_date","expr":"EXPOSURE_DATE","data_type":"DATE","synonyms":["factor_date","exposure_date","measurement_date"],"description":"The date when factor exposures were calculated. Use for factor evolution analysis."}},{{"name":"exposure_month","expr":"DATE_TRUNC(\\'MONTH\\', EXPOSURE_DATE)","data_type":"DATE","synonyms":["factor_month"],"description":"Monthly aggregation for factor trend analysis."}}]}},{{"name":"ISSUERS","dimensions":[{{"name":"COUNTRYOFINCORPORATION"}},{{"name":"LEGALNAME"}},{{"name":"SIC_DESCRIPTION"}}]}},{{"name":"PORTFOLIOS","dimensions":[{{"name":"PortfolioName"}},{{"name":"Strategy"}}]}},{{"name":"SECURITIES","dimensions":[{{"name":"AssetClass"}},{{"name":"Description"}},{{"name":"Ticker"}}]}},{{"name":"MARKET_DATA","metrics":[{{"name":"PRICE_RETURN"}},{{"name":"TOTAL_RETURN"}},{{"name":"VOLUME_TRADED"}}]}},{{"name":"FUNDAMENTALS","metrics":[{{"name":"FUNDAMENTAL_VALUE"}}]}},{{"name":"ESTIMATES","metrics":[{{"name":"ESTIMATE_VALUE"}}]}},{{"name":"BENCHMARK_HOLDINGS","metrics":[{{"name":"BenchmarkWeight"}}]}}],"relationships":[{{"name":"HOLDINGS_TO_PORTFOLIOS"}},{{"name":"HOLDINGS_TO_SECURITIES"}},{{"name":"SECURITIES_TO_ISSUERS"}},{{"name":"FACTORS_TO_SECURITIES"}},{{"name":"HOLDINGS_TO_FACTORS"}},{{"name":"FUNDAMENTALS_TO_SECURITIES"}},{{"name":"ESTIMATES_TO_SECURITIES"}},{{"name":"MARKET_DATA_TO_SECURITIES"}},{{"name":"BENCHMARK_TO_SECURITIES"}}],"verified_queries":[{{"name":"portfolio_factor_exposures","question":"Show the most recent factor exposures for Value strategy portfolio","sql":"SELECT __PORTFOLIOS.PortfolioName, __SECURITIES.Ticker, __SECURITIES.Description, __FACTOR_EXPOSURES.FACTOR_NAME, __FACTOR_EXPOSURES.EXPOSURE_VALUE FROM __HOLDINGS JOIN __PORTFOLIOS ON __HOLDINGS.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID JOIN __SECURITIES ON __HOLDINGS.SECURITYID = __SECURITIES.SECURITYID JOIN __FACTOR_EXPOSURES ON __HOLDINGS.SECURITYID = __FACTOR_EXPOSURES.SECURITYID AND __HOLDINGS.HOLDINGDATE >= __FACTOR_EXPOSURES.EXPOSURE_DATE WHERE __PORTFOLIOS.Strategy = \\'Value\\' AND __HOLDINGS.HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM __HOLDINGS) QUALIFY ROW_NUMBER() OVER (PARTITION BY __HOLDINGS.SECURITYID, __FACTOR_EXPOSURES.FACTOR_NAME ORDER BY __FACTOR_EXPOSURES.EXPOSURE_DATE DESC) = 1 ORDER BY __SECURITIES.Ticker, __FACTOR_EXPOSURES.FACTOR_NAME","use_as_onboarding_question":true}},{{"name":"compare_portfolio_factors","question":"Compare factor exposures between Value and Growth strategy portfolios","sql":"WITH latest_factors AS (SELECT __HOLDINGS.PORTFOLIOID, __HOLDINGS.SECURITYID, __FACTOR_EXPOSURES.FACTOR_NAME, __FACTOR_EXPOSURES.EXPOSURE_VALUE FROM __HOLDINGS JOIN __FACTOR_EXPOSURES ON __HOLDINGS.SECURITYID = __FACTOR_EXPOSURES.SECURITYID AND __HOLDINGS.HOLDINGDATE >= __FACTOR_EXPOSURES.EXPOSURE_DATE WHERE __HOLDINGS.HOLDINGDATE = (SELECT MAX(HOLDINGDATE) FROM __HOLDINGS) QUALIFY ROW_NUMBER() OVER (PARTITION BY __HOLDINGS.PORTFOLIOID, __HOLDINGS.SECURITYID, __FACTOR_EXPOSURES.FACTOR_NAME ORDER BY __FACTOR_EXPOSURES.EXPOSURE_DATE DESC) = 1) SELECT __PORTFOLIOS.Strategy, lf.FACTOR_NAME, AVG(lf.EXPOSURE_VALUE) AS AVG_FACTOR_EXPOSURE FROM latest_factors lf JOIN __PORTFOLIOS ON lf.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID WHERE __PORTFOLIOS.Strategy IN (\\'Value\\', \\'Growth\\') GROUP BY __PORTFOLIOS.Strategy, lf.FACTOR_NAME ORDER BY __PORTFOLIOS.Strategy, lf.FACTOR_NAME","use_as_onboarding_question":true}},{{"name":"improving_factor_stocks","question":"Show stocks with improving momentum and quality factors over the last 6 months","sql":"WITH recent_factors AS (SELECT __FACTOR_EXPOSURES.SECURITYID, __FACTOR_EXPOSURES.FACTOR_NAME, AVG(__FACTOR_EXPOSURES.EXPOSURE_VALUE) AS recent_exposure FROM __FACTOR_EXPOSURES WHERE __FACTOR_EXPOSURES.EXPOSURE_DATE >= DATEADD(month, -1, (SELECT MAX(EXPOSURE_DATE) FROM __FACTOR_EXPOSURES)) AND __FACTOR_EXPOSURES.FACTOR_NAME IN (\\'Momentum\\', \\'Quality\\') GROUP BY __FACTOR_EXPOSURES.SECURITYID, __FACTOR_EXPOSURES.FACTOR_NAME), older_factors AS (SELECT __FACTOR_EXPOSURES.SECURITYID, __FACTOR_EXPOSURES.FACTOR_NAME, AVG(__FACTOR_EXPOSURES.EXPOSURE_VALUE) AS older_exposure FROM __FACTOR_EXPOSURES WHERE __FACTOR_EXPOSURES.EXPOSURE_DATE BETWEEN DATEADD(month, -7, (SELECT MAX(EXPOSURE_DATE) FROM __FACTOR_EXPOSURES)) AND DATEADD(month, -6, (SELECT MAX(EXPOSURE_DATE) FROM __FACTOR_EXPOSURES)) AND __FACTOR_EXPOSURES.FACTOR_NAME IN (\\'Momentum\\', \\'Quality\\') GROUP BY __FACTOR_EXPOSURES.SECURITYID, __FACTOR_EXPOSURES.FACTOR_NAME), factor_changes AS (SELECT r.SECURITYID, r.FACTOR_NAME, r.recent_exposure, o.older_exposure, r.recent_exposure - o.older_exposure AS exposure_change FROM recent_factors r JOIN older_factors o ON r.SECURITYID = o.SECURITYID AND r.FACTOR_NAME = o.FACTOR_NAME WHERE r.recent_exposure > o.older_exposure) SELECT __SECURITIES.Ticker, __SECURITIES.Description, fc.FACTOR_NAME, ROUND(fc.older_exposure, 2) AS factor_6mo_ago, ROUND(fc.recent_exposure, 2) AS factor_current, ROUND(fc.exposure_change, 2) AS factor_improvement FROM factor_changes fc JOIN __SECURITIES ON fc.SECURITYID = __SECURITIES.SECURITYID WHERE fc.SECURITYID IN (SELECT SECURITYID FROM factor_changes WHERE FACTOR_NAME = \\'Momentum\\' INTERSECT SELECT SECURITYID FROM factor_changes WHERE FACTOR_NAME = \\'Quality\\') ORDER BY fc.exposure_change DESC, __SECURITIES.Ticker, fc.FACTOR_NAME","use_as_onboarding_question":true}}],"module_custom_instructions":{{"sql_generation":"For portfolio factor exposure queries, use the HOLDINGS_TO_FACTORS ASOF relationship to join current portfolio holdings with their most recent factor exposures. The ASOF join matches each holding to the factor exposure where EXPOSURE_DATE is on or before HOLDINGDATE (closest prior factor data). For current portfolio factor exposures, filter HOLDINGS to most recent HoldingDate, then use ASOF join with QUALIFY to get the most recent factor per security. For factor trend analysis (e.g., improving factors over time), use CTE pattern: create separate CTEs for different time periods, join them on SecurityID and FACTOR_NAME, calculate changes as (recent - older). Use INTERSECT to find securities improving in multiple factors simultaneously. Always show factor exposures with 2 decimal places. When comparing factors across portfolios, use CTE to get latest factors with QUALIFY, then join to portfolios and aggregate."}}}}');
    """).collect()
    

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
            config.log_warning(f"  Implementation table {table} not found, skipping implementation view creation")
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

    #config.log_detail(" Created semantic view: SAM_IMPLEMENTATION_VIEW")

def create_sec_filings_semantic_view(session: Session):
    """Create semantic view for SEC filings using MARKET_DATA schema (S&P Capital IQ pattern)."""
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    
    # Check if new MARKET_DATA filing tables exist
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_FILING_REF LIMIT 1").collect()
    except:
        config.log_detail("  Skipping SAM_FILINGS_VIEW - MARKET_DATA filing tables not found")
        return
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {database_name}.AI.SAM_FILINGS_VIEW
	TABLES (
		FILING_REF AS {database_name}.{market_data_schema}.FACT_FILING_REF
			PRIMARY KEY (FILE_VERSION_ID) 
			WITH SYNONYMS=('filings','sec_filings','company_filings','regulatory_filings') 
			COMMENT='Master filing reference with metadata for all SEC and regulatory filings',
		FILING_DATA AS {database_name}.{market_data_schema}.FACT_FILING_DATA
			PRIMARY KEY (FILE_VERSION_ID, HEADING_ID) 
			WITH SYNONYMS=('filing_content','filing_sections','filing_text','sec_content') 
			COMMENT='Textual content from SEC filings organized by section',
		FILING_TYPES AS {database_name}.{market_data_schema}.REF_FILING_TYPE
			PRIMARY KEY (FILING_TYPE_ID) 
			WITH SYNONYMS=('form_types','sec_forms','filing_forms') 
			COMMENT='Filing type reference (10-K, 10-Q, 8-K, etc.)',
		FILING_SOURCES AS {database_name}.{market_data_schema}.REF_FILING_SOURCE
			PRIMARY KEY (FILING_SOURCE_ID) 
			WITH SYNONYMS=('filing_sources','data_sources') 
			COMMENT='Filing source reference (SEC EDGAR, Company Website, etc.)',
		COMPANIES AS {database_name}.{market_data_schema}.DIM_COMPANY
			PRIMARY KEY (COMPANY_ID) 
			WITH SYNONYMS=('companies','issuers','filers') 
			COMMENT='Company master data'
	)
	RELATIONSHIPS (
		FILING_REF_TO_COMPANIES AS FILING_REF(COMPANY_ID) REFERENCES COMPANIES(COMPANY_ID),
		FILING_REF_TO_TYPES AS FILING_REF(FILING_TYPE_ID) REFERENCES FILING_TYPES(FILING_TYPE_ID),
		FILING_REF_TO_SOURCES AS FILING_REF(FILING_SOURCE_ID) REFERENCES FILING_SOURCES(FILING_SOURCE_ID),
		FILING_DATA_TO_REF AS FILING_DATA(FILE_VERSION_ID) REFERENCES FILING_REF(FILE_VERSION_ID)
	)
	DIMENSIONS (
		-- Company dimensions
		COMPANIES.CompanyName AS COMPANY_NAME WITH SYNONYMS=('company','issuer_name','filer_name','company_name') COMMENT='Company legal name',
		COMPANIES.IndustryDescription AS INDUSTRY_DESCRIPTION WITH SYNONYMS=('industry','sector','business_type') COMMENT='Industry classification',
		COMPANIES.CIK AS CIK WITH SYNONYMS=('cik','sec_cik','company_cik') COMMENT='SEC Central Index Key',
		COMPANIES.CountryCode AS COUNTRY_CODE WITH SYNONYMS=('country','domicile') COMMENT='Country of incorporation',
		
		-- Filing type dimensions
		FILING_TYPES.FilingType AS FILING_TYPE WITH SYNONYMS=('form_type','sec_form','form','filing_form') COMMENT='SEC form type (10-K, 10-Q, 8-K, etc.)',
		FILING_TYPES.FilingTypeDefinition AS FILING_TYPE_DEFINITION WITH SYNONYMS=('form_description','filing_description') COMMENT='Description of the filing type',
		FILING_TYPES.IsAnnual AS IS_ANNUAL WITH SYNONYMS=('annual_filing','yearly_filing') COMMENT='Whether this is an annual filing',
		FILING_TYPES.IsQuarterly AS IS_QUARTERLY WITH SYNONYMS=('quarterly_filing','quarter_filing') COMMENT='Whether this is a quarterly filing',
		
		-- Filing source dimensions
		FILING_SOURCES.FilingSource AS FILING_SOURCE WITH SYNONYMS=('source','data_source') COMMENT='Source of the filing (SEC EDGAR, etc.)',
		
		-- Filing content dimensions
		FILING_DATA.SECTION_HEADING AS HEADING WITH SYNONYMS=('heading','section','item') COMMENT='Section heading from the filing',
		FILING_DATA.STANDARDIZED_SECTION AS STANDARDIZED_HEADING WITH SYNONYMS=('standardized_heading','normalized_section','item_name') COMMENT='Standardized section name (Business, Risk Factors, MD&A, etc.)',
		FILING_DATA.SECTION_CONTENT AS SECTION_TEXT WITH SYNONYMS=('content','text','section_text','filing_text') COMMENT='Full text content of the section',
		
		-- Time dimensions
		FILING_REF.FilingDate AS FILING_DATE WITH SYNONYMS=('filing_date','submission_date','report_date','date') COMMENT='Date the filing was submitted to SEC',
		FILING_REF.PeriodDate AS PERIOD_DATE WITH SYNONYMS=('period_end','period_date','quarter_end') COMMENT='Period end date covered by the filing',
		FILING_REF.FiscalYear AS FISCAL_YEAR WITH SYNONYMS=('year','fiscal_year','fy') COMMENT='Fiscal year of the filing',
		FILING_REF.FiscalQuarter AS FISCAL_QUARTER WITH SYNONYMS=('quarter','q','fiscal_quarter') COMMENT='Fiscal quarter (1-4)',
		FILING_REF.AccessionNumber AS ACCESSION_NUMBER WITH SYNONYMS=('accession','sec_accession','filing_id') COMMENT='SEC accession number (unique filing identifier)'
	)
	METRICS (
		-- Filing count metrics
		FILING_REF.FILING_COUNT AS COUNT(DISTINCT FILE_VERSION_ID) WITH SYNONYMS=('filing_count','number_of_filings','total_filings','count') COMMENT='Count of filings',
		FILING_REF.ANNUAL_FILING_COUNT AS COUNT(DISTINCT CASE WHEN FILING_TYPE_ID = 1 THEN FILE_VERSION_ID END) WITH SYNONYMS=('annual_count','10k_count','yearly_filings') COMMENT='Count of annual (10-K) filings',
		FILING_REF.QUARTERLY_FILING_COUNT AS COUNT(DISTINCT CASE WHEN FILING_TYPE_ID = 2 THEN FILE_VERSION_ID END) WITH SYNONYMS=('quarterly_count','10q_count','quarter_filings') COMMENT='Count of quarterly (10-Q) filings',
		
		-- Section metrics
		FILING_DATA.SECTION_COUNT AS COUNT(DISTINCT HEADING_ID) WITH SYNONYMS=('section_count','number_of_sections') COMMENT='Count of sections in filings',
		FILING_DATA.CONTENT_LENGTH AS SUM(LENGTH(SECTION_TEXT)) WITH SYNONYMS=('text_length','content_size','document_size') COMMENT='Total length of filing content'
	)
	COMMENT='SEC filing semantic view using S&P Capital IQ pattern - includes filing metadata, textual content, and company linkages'
	WITH EXTENSION (CA='{{"tables":[{{"name":"FILING_REF","metrics":[{{"name":"FILING_COUNT"}},{{"name":"ANNUAL_FILING_COUNT"}},{{"name":"QUARTERLY_FILING_COUNT"}}],"time_dimensions":[{{"name":"filing_date","expr":"FILING_DATE","data_type":"DATE","synonyms":["report_date","submission_date"],"description":"Date the filing was submitted to SEC"}},{{"name":"filing_quarter","expr":"DATE_TRUNC(\\'QUARTER\\', FILING_DATE)","data_type":"DATE","synonyms":["quarter","quarterly"],"description":"Quarterly aggregation for filing analysis"}}]}},{{"name":"FILING_DATA","metrics":[{{"name":"SECTION_COUNT"}},{{"name":"CONTENT_LENGTH"}}]}},{{"name":"COMPANIES","dimensions":[{{"name":"COMPANY_NAME"}},{{"name":"CIK"}},{{"name":"INDUSTRY_DESCRIPTION"}}]}},{{"name":"FILING_TYPES","dimensions":[{{"name":"FILING_TYPE"}},{{"name":"IS_ANNUAL"}},{{"name":"IS_QUARTERLY"}}]}}],"relationships":[{{"name":"FILING_REF_TO_COMPANIES"}},{{"name":"FILING_REF_TO_TYPES"}},{{"name":"FILING_DATA_TO_REF"}}],"verified_queries":[{{"name":"recent_10k_filings","question":"Show me recent 10-K annual filings","sql":"SELECT __COMPANIES.COMPANY_NAME, __FILING_REF.FILING_DATE, __FILING_REF.FISCAL_YEAR FROM __FILING_REF JOIN __COMPANIES ON __FILING_REF.COMPANY_ID = __COMPANIES.COMPANY_ID JOIN __FILING_TYPES ON __FILING_REF.FILING_TYPE_ID = __FILING_TYPES.FILING_TYPE_ID WHERE __FILING_TYPES.FILING_TYPE = \\'10-K\\' ORDER BY __FILING_REF.FILING_DATE DESC LIMIT 20","use_as_onboarding_question":true}},{{"name":"company_filings","question":"What filings has a specific company submitted?","sql":"SELECT __FILING_TYPES.FILING_TYPE, __FILING_REF.FILING_DATE, __FILING_REF.FISCAL_YEAR, __FILING_REF.FISCAL_QUARTER FROM __FILING_REF JOIN __FILING_TYPES ON __FILING_REF.FILING_TYPE_ID = __FILING_TYPES.FILING_TYPE_ID JOIN __COMPANIES ON __FILING_REF.COMPANY_ID = __COMPANIES.COMPANY_ID WHERE __COMPANIES.COMPANY_NAME ILIKE \\'%COMPANY_NAME%\\' ORDER BY __FILING_REF.FILING_DATE DESC","use_as_onboarding_question":false}}],"module_custom_instructions":{{"sql_generation":"For filing analysis, default to the most recent fiscal year when not specified. Use FILING_TYPE dimension to filter by form type (10-K for annual, 10-Q for quarterly). Join FILING_DATA for textual content analysis. Use STANDARDIZED_SECTION for consistent section filtering across filings."}}}}');
    """).collect()
    
    config.log_detail(" Created semantic view: SAM_FILINGS_VIEW")

def create_supply_chain_semantic_view(session: Session):
    """Create semantic view for supply chain risk analysis."""
    
    # Check if supply chain tables exist
    try:
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.DIM_SUPPLY_CHAIN_RELATIONSHIPS LIMIT 1").collect()
    except:
        config.log_detail("  Skipping SAM_SUPPLY_CHAIN_VIEW - tables not found")
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
		COMPANY_ISSUERS.CompanyCountry AS COUNTRYOFINCORPORATION WITH SYNONYMS=('company_country','customer_country') COMMENT='US company country of incorporation using 2-letter ISO codes (e.g., US for United States)',
		
		-- Counterparty dimensions (Taiwan suppliers)
		COUNTERPARTY_ISSUERS.CounterpartyName AS LEGALNAME WITH SYNONYMS=('counterparty','supplier','supplier_name','taiwan_supplier','supplier_company') COMMENT='Supplier/counterparty legal name (e.g., Taiwan semiconductor suppliers like TSMC)',
		COUNTERPARTY_ISSUERS.CounterpartyIndustry AS SIC_DESCRIPTION WITH SYNONYMS=('counterparty_industry','supplier_industry','taiwan_industry','semiconductor_industry') COMMENT='Supplier SIC industry classification (e.g., Semiconductors and related devices)',
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
    
    config.log_detail(" Created semantic view: SAM_SUPPLY_CHAIN_VIEW")

def create_middle_office_semantic_view(session: Session):
    """Create semantic view for middle office operations analytics."""
    
    # Check if middle office tables exist
    try:
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_TRADE_SETTLEMENT LIMIT 1").collect()
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_RECONCILIATION LIMIT 1").collect()
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_NAV_CALCULATION LIMIT 1").collect()
    except:
        config.log_detail("  Skipping SAM_MIDDLE_OFFICE_VIEW - tables not found")
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
			COMMENT='Custodian information'
	)
	RELATIONSHIPS (
		SETTLEMENTS_TO_PORTFOLIOS AS SETTLEMENTS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		SETTLEMENTS_TO_SECURITIES AS SETTLEMENTS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		SETTLEMENTS_TO_CUSTODIANS AS SETTLEMENTS(CUSTODIANID) REFERENCES CUSTODIANS(CUSTODIANID),
		RECON_TO_PORTFOLIOS AS RECONCILIATIONS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
		RECON_TO_SECURITIES AS RECONCILIATIONS(SECURITYID) REFERENCES SECURITIES(SECURITYID),
		NAV_TO_PORTFOLIOS AS NAV(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID)
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
		SETTLEMENTS.SettlementStatus AS STATUS WITH SYNONYMS=('status','settlement_status') COMMENT='Settlement status (Settled, Pending, Failed)',
		
		-- Reconciliation dimensions
		RECONCILIATIONS.ReconciliationDate AS RECONCILIATIONDATE WITH SYNONYMS=('recon_date','date') COMMENT='Reconciliation date',
		RECONCILIATIONS.BreakType AS BREAKTYPE WITH SYNONYMS=('break_type','exception_type') COMMENT='Break type',
		RECONCILIATIONS.ReconStatus AS STATUS WITH SYNONYMS=('resolution_status','recon_status') COMMENT='Reconciliation status (Open, Investigating, Resolved)',
		
		-- NAV dimensions
		NAV.CALCULATIONDATE AS CalculationDate WITH SYNONYMS=('nav_date','valuation_date') COMMENT='NAV calculation date'
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
		NAV.TOTAL_ASSETS AS SUM(TotalAssets) WITH SYNONYMS=('assets','total_assets','aum') COMMENT='Total assets'
	)
	COMMENT='Middle office semantic view for operations, reconciliation, and NAV analytics'
	WITH EXTENSION (CA='{{"tables":[{{"name":"SETTLEMENTS","metrics":[{{"name":"FAILED_SETTLEMENT_COUNT"}},{{"name":"SETTLEMENT_COUNT"}},{{"name":"SETTLEMENT_VALUE"}}],"time_dimensions":[{{"name":"settlement_date","expr":"SETTLEMENTDATE","data_type":"DATE","synonyms":["settlement_date","settle_date","trade_settle_date"],"description":"The date when trade settlement occurs (typically T+2 for equities). Use for settlement tracking and analysis."}},{{"name":"settlement_month","expr":"DATE_TRUNC(\\'MONTH\\', SETTLEMENTDATE)","data_type":"DATE","synonyms":["month","monthly","settlement_month"],"description":"Monthly aggregation for settlement trend analysis."}}]}},{{"name":"RECONCILIATIONS","metrics":[{{"name":"BREAK_COUNT"}},{{"name":"BREAK_VALUE"}},{{"name":"UNRESOLVED_BREAKS"}}],"time_dimensions":[{{"name":"reconciliation_date","expr":"RECONCILIATIONDATE","data_type":"DATE","synonyms":["recon_date","reconciliation_date","break_date"],"description":"The date when reconciliation was performed. Use for tracking reconciliation breaks over time."}},{{"name":"recon_month","expr":"DATE_TRUNC(\\'MONTH\\', RECONCILIATIONDATE)","data_type":"DATE","synonyms":["month","monthly","recon_month"],"description":"Monthly aggregation for reconciliation break trends."}}]}},{{"name":"NAV","metrics":[{{"name":"NAV_PER_SHARE"}},{{"name":"TOTAL_ASSETS"}}],"time_dimensions":[{{"name":"calculation_date","expr":"CALCULATIONDATE","data_type":"DATE","synonyms":["nav_date","valuation_date","calc_date"],"description":"The date of NAV calculation (typically end-of-day). Use for NAV history and trend analysis."}},{{"name":"nav_month","expr":"DATE_TRUNC(\\'MONTH\\', CALCULATIONDATE)","data_type":"DATE","synonyms":["month","monthly","nav_month"],"description":"Monthly aggregation for NAV performance trends."}}]}},{{"name":"PORTFOLIOS","dimensions":[{{"name":"PORTFOLIONAME"}}]}},{{"name":"SECURITIES","dimensions":[{{"name":"TICKER"}},{{"name":"DESCRIPTION"}}]}},{{"name":"CUSTODIANS","dimensions":[{{"name":"CUSTODIANNAME"}}]}}],"relationships":[{{"name":"SETTLEMENTS_TO_PORTFOLIOS"}},{{"name":"SETTLEMENTS_TO_SECURITIES"}},{{"name":"SETTLEMENTS_TO_CUSTODIANS"}},{{"name":"RECON_TO_PORTFOLIOS"}},{{"name":"RECON_TO_SECURITIES"}},{{"name":"NAV_TO_PORTFOLIOS"}}],"verified_queries":[{{"name":"failed_settlements","question":"Show me failed settlements in the last 30 days","sql":"SELECT __SETTLEMENTS.SETTLEMENTDATE, __PORTFOLIOS.PORTFOLIONAME, __SECURITIES.TICKER, __SETTLEMENTS.SETTLEMENT_VALUE FROM __SETTLEMENTS JOIN __PORTFOLIOS ON __SETTLEMENTS.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID JOIN __SECURITIES ON __SETTLEMENTS.SECURITYID = __SECURITIES.SECURITYID WHERE __SETTLEMENTS.SETTLEMENTSTATUS = \\'Failed\\' AND __SETTLEMENTS.SETTLEMENTDATE >= DATEADD(day, -30, CURRENT_DATE()) ORDER BY __SETTLEMENTS.SETTLEMENTDATE DESC","use_as_onboarding_question":true}},{{"name":"unresolved_breaks","question":"What are the unresolved reconciliation breaks?","sql":"SELECT __RECONCILIATIONS.RECONCILIATIONDATE, __PORTFOLIOS.PORTFOLIONAME, __RECONCILIATIONS.BREAKTYPE, __RECONCILIATIONS.BREAK_VALUE FROM __RECONCILIATIONS JOIN __PORTFOLIOS ON __RECONCILIATIONS.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID WHERE __RECONCILIATIONS.STATUS = \\'Open\\' ORDER BY __RECONCILIATIONS.BREAK_VALUE DESC","use_as_onboarding_question":true}},{{"name":"nav_calculation","question":"Show me the latest NAV for all portfolios","sql":"SELECT __NAV.CALCULATIONDATE, __PORTFOLIOS.PORTFOLIONAME, __NAV.NAV_PER_SHARE, __NAV.TOTAL_ASSETS FROM __NAV JOIN __PORTFOLIOS ON __NAV.PORTFOLIOID = __PORTFOLIOS.PORTFOLIOID WHERE __NAV.CALCULATIONDATE = (SELECT MAX(__NAV.CALCULATIONDATE) FROM __NAV) ORDER BY __PORTFOLIOS.PORTFOLIONAME","use_as_onboarding_question":false}}],"module_custom_instructions":{{"sql_generation":"For settlement queries, filter to most recent 30 days by default unless specified. When showing reconciliation breaks, always order by difference amount descending to show largest breaks first. For NAV queries, use the most recent calculation date when current NAV is requested. Round settlement values and break differences to 2 decimal places, NAV per share to 4 decimal places. Settlement status values: Settled, Pending, Failed. Reconciliation status values: Open, Investigating, Resolved.","question_categorization":"If users ask about \\'fails\\' or \\'failed trades\\', treat as settlement status queries. If users ask about \\'breaks\\' or \\'exceptions\\', treat as reconciliation queries. If users ask about \\'NAV\\' or \\'unit value\\', treat as NAV calculation queries."}}}}');
    """).collect()
    
    config.log_detail(" Created semantic view: SAM_MIDDLE_OFFICE_VIEW")

def create_executive_semantic_view(session: Session):
    """
    Create semantic view for executive KPIs, client analytics, and firm-wide performance.
    
    Used by: Executive Copilot for C-suite queries
    Supports: Firm-wide AUM, net flows, client flow drill-down, strategy performance
    
    Reuses: DIM_PORTFOLIO (existing), DIM_CLIENT_MANDATES (existing)
    New: DIM_CLIENT, FACT_CLIENT_FLOWS, FACT_FUND_FLOWS
    """
    
    # Check if required tables exist
    required_tables = [
        'DIM_CLIENT',
        'FACT_CLIENT_FLOWS',
        'FACT_FUND_FLOWS',
        'DIM_PORTFOLIO'
    ]
    
    for table in required_tables:
        try:
            session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.CURATED.{table} LIMIT 1").collect()
        except:
            config.log_warning(f" Executive table {table} not found, skipping executive view creation")
            return
    
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
            COMMENT='Investment portfolios and fund information'
    )
    RELATIONSHIPS (
        CLIENT_FLOWS_TO_CLIENTS AS CLIENT_FLOWS(CLIENTID) REFERENCES CLIENTS(CLIENTID),
        CLIENT_FLOWS_TO_PORTFOLIOS AS CLIENT_FLOWS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID),
        FUND_FLOWS_TO_PORTFOLIOS AS FUND_FLOWS(PORTFOLIOID) REFERENCES PORTFOLIOS(PORTFOLIOID)
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
        FUND_FLOWS.FundFlowDate AS FlowDate WITH SYNONYMS=('fund_flow_date','aggregated_date') COMMENT='Date of aggregated fund flows'
    )
    METRICS (
        -- Client AUM metrics
        CLIENTS.TOTAL_CLIENT_AUM AS SUM(AUM_with_SAM) WITH SYNONYMS=('client_aum','total_client_assets','assets_under_management') COMMENT='Total AUM from clients',
        CLIENTS.CLIENT_COUNT AS COUNT(DISTINCT ClientID) WITH SYNONYMS=('number_of_clients','client_count','investor_count') COMMENT='Count of institutional clients',
        CLIENTS.AVG_CLIENT_SIZE AS AVG(AUM_with_SAM) WITH SYNONYMS=('average_client_size','avg_aum','typical_client_size') COMMENT='Average client AUM',
        
        -- Client flow metrics (detailed)
        CLIENT_FLOWS.TOTAL_FLOW_AMOUNT AS SUM(FlowAmount) WITH SYNONYMS=('net_flows','total_flows','flow_amount') COMMENT='Net flow amount (positive = inflow, negative = outflow)',
        CLIENT_FLOWS.GROSS_INFLOWS AS SUM(CASE WHEN FlowAmount > 0 THEN FlowAmount ELSE 0 END) WITH SYNONYMS=('inflows','subscriptions','gross_inflows') COMMENT='Gross subscription inflows',
        CLIENT_FLOWS.GROSS_OUTFLOWS AS SUM(CASE WHEN FlowAmount < 0 THEN ABS(FlowAmount) ELSE 0 END) WITH SYNONYMS=('outflows','redemptions','gross_outflows') COMMENT='Gross redemption outflows',
        CLIENT_FLOWS.FLOW_TRANSACTION_COUNT AS COUNT(FlowID) WITH SYNONYMS=('flow_count','transaction_count','number_of_flows') COMMENT='Number of flow transactions',
        
        -- Fund flow metrics (aggregated for KPIs)
        FUND_FLOWS.FUND_NET_FLOWS AS SUM(NetFlows) WITH SYNONYMS=('net_fund_flows','strategy_net_flows','portfolio_net_flows') COMMENT='Net flows at fund/strategy level',
        FUND_FLOWS.FUND_GROSS_INFLOWS AS SUM(GrossInflows) WITH SYNONYMS=('fund_inflows','strategy_inflows') COMMENT='Gross inflows at fund level',
        FUND_FLOWS.FUND_GROSS_OUTFLOWS AS SUM(GrossOutflows) WITH SYNONYMS=('fund_outflows','strategy_outflows') COMMENT='Gross outflows at fund level',
        FUND_FLOWS.FUND_CLIENT_COUNT AS SUM(ClientCount) WITH SYNONYMS=('active_clients','contributing_clients') COMMENT='Number of clients with flows',
        
        -- Flow concentration metrics
        CLIENT_FLOWS.MAX_SINGLE_CLIENT_FLOW AS MAX(ABS(FlowAmount)) WITH SYNONYMS=('largest_flow','max_flow','biggest_transaction') COMMENT='Largest single client flow'
    )
    COMMENT='Executive semantic view for firm-wide KPIs, client analytics, and flow analysis. Use for C-suite performance reviews and strategic planning.'
    WITH EXTENSION (CA='{{"tables":[{{"name":"CLIENTS","metrics":[{{"name":"AVG_CLIENT_SIZE"}},{{"name":"CLIENT_COUNT"}},{{"name":"TOTAL_CLIENT_AUM"}}]}},{{"name":"CLIENT_FLOWS","metrics":[{{"name":"FLOW_TRANSACTION_COUNT"}},{{"name":"GROSS_INFLOWS"}},{{"name":"GROSS_OUTFLOWS"}},{{"name":"MAX_SINGLE_CLIENT_FLOW"}},{{"name":"TOTAL_FLOW_AMOUNT"}}],"time_dimensions":[{{"name":"ClientFlowDate","expr":"FlowDate","data_type":"DATE","synonyms":["flow_date","transaction_date","subscription_date"],"description":"Date of client flow transaction. Use for flow trend analysis."}},{{"name":"flow_month","expr":"DATE_TRUNC(\\'MONTH\\', FlowDate)","data_type":"DATE","synonyms":["month","monthly","flow_month"],"description":"Monthly aggregation for flow trend analysis."}}]}},{{"name":"FUND_FLOWS","metrics":[{{"name":"FUND_CLIENT_COUNT"}},{{"name":"FUND_GROSS_INFLOWS"}},{{"name":"FUND_GROSS_OUTFLOWS"}},{{"name":"FUND_NET_FLOWS"}}],"time_dimensions":[{{"name":"FundFlowDate","expr":"FlowDate","data_type":"DATE","synonyms":["fund_date","aggregated_date"],"description":"Date of aggregated fund flows."}},{{"name":"fund_flow_month","expr":"DATE_TRUNC(\\'MONTH\\', FlowDate)","data_type":"DATE","synonyms":["month","monthly"],"description":"Monthly aggregation for fund flow trends."}}]}},{{"name":"PORTFOLIOS","dimensions":[{{"name":"PortfolioName"}},{{"name":"Strategy"}}]}}],"relationships":[{{"name":"CLIENT_FLOWS_TO_CLIENTS"}},{{"name":"CLIENT_FLOWS_TO_PORTFOLIOS"}},{{"name":"FUND_FLOWS_TO_PORTFOLIOS"}}],"verified_queries":[{{"name":"firm_kpis_mtd","question":"What are the key performance highlights for the firm month-to-date?","sql":"SELECT SUM(__FUND_FLOWS.NetFlows) as NET_FLOWS_MTD, SUM(__FUND_FLOWS.GrossInflows) as GROSS_INFLOWS_MTD, SUM(__FUND_FLOWS.GrossOutflows) as GROSS_OUTFLOWS_MTD, SUM(__FUND_FLOWS.ClientCount) as ACTIVE_CLIENTS FROM __FUND_FLOWS WHERE __FUND_FLOWS.FlowDate >= DATE_TRUNC(\\'MONTH\\', CURRENT_DATE())","use_as_onboarding_question":true}},{{"name":"flows_by_strategy","question":"Which strategies are seeing the strongest inflows?","sql":"SELECT __FUND_FLOWS.Strategy, SUM(__FUND_FLOWS.NetFlows) as NET_FLOWS, SUM(__FUND_FLOWS.GrossInflows) as GROSS_INFLOWS FROM __FUND_FLOWS WHERE __FUND_FLOWS.FlowDate >= DATE_TRUNC(\\'MONTH\\', CURRENT_DATE()) GROUP BY __FUND_FLOWS.Strategy ORDER BY NET_FLOWS DESC","use_as_onboarding_question":true}},{{"name":"client_flow_drilldown","question":"What clients are driving the inflows for a specific strategy?","sql":"SELECT __CLIENTS.ClientName, __CLIENTS.ClientType, SUM(__CLIENT_FLOWS.FlowAmount) as TOTAL_FLOW FROM __CLIENT_FLOWS JOIN __CLIENTS ON __CLIENT_FLOWS.ClientID = __CLIENTS.ClientID JOIN __PORTFOLIOS ON __CLIENT_FLOWS.PortfolioID = __PORTFOLIOS.PortfolioID WHERE __PORTFOLIOS.Strategy = \\'ESG\\' AND __CLIENT_FLOWS.FlowDate >= DATE_TRUNC(\\'MONTH\\', CURRENT_DATE()) GROUP BY __CLIENTS.ClientName, __CLIENTS.ClientType ORDER BY TOTAL_FLOW DESC","use_as_onboarding_question":false}},{{"name":"client_concentration","question":"Is the flow from one large client or broad-based demand?","sql":"SELECT __CLIENTS.ClientName, __CLIENTS.ClientType, SUM(__CLIENT_FLOWS.FlowAmount) as FLOW_AMOUNT, COUNT(*) as TRANSACTION_COUNT FROM __CLIENT_FLOWS JOIN __CLIENTS ON __CLIENT_FLOWS.ClientID = __CLIENTS.ClientID WHERE __CLIENT_FLOWS.FlowDate >= DATE_TRUNC(\\'MONTH\\', CURRENT_DATE()) AND __CLIENT_FLOWS.FlowAmount > 0 GROUP BY __CLIENTS.ClientName, __CLIENTS.ClientType ORDER BY FLOW_AMOUNT DESC","use_as_onboarding_question":false}}],"module_custom_instructions":{{"sql_generation":"For month-to-date queries, filter to current month using DATE_TRUNC(\\'MONTH\\', CURRENT_DATE()). When showing flows, always display both gross inflows and outflows alongside net flows for context. For client concentration analysis, show the count of distinct clients alongside flow amounts. Round flow amounts to nearest thousand for readability. When asked about \\'driving\\' flows, drill down to client level using CLIENT_FLOWS table.","question_categorization":"If users ask about \\'firm performance\\' or \\'KPIs\\', use FUND_FLOWS for aggregated metrics. If users ask about \\'what\\'s driving\\' or \\'client concentration\\', drill down to CLIENT_FLOWS. If users ask about \\'broad-based\\' demand, count distinct clients."}}}}');
    """).collect()
    
    config.log_detail(" Created semantic view: SAM_EXECUTIVE_VIEW")


def create_fundamentals_semantic_view(session: Session):
    """Create fundamentals semantic view for MARKET_DATA financial analysis (SAM_FUNDAMENTALS_VIEW).
    
    This semantic view provides access to:
    - Company financial statements (revenue, margins, earnings)
    - Analyst estimates and consensus data
    - Price targets and ratings
    - Historical financial trends
    """
    
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas'].get('market_data', 'MARKET_DATA')
    
    # First check if MARKET_DATA tables exist
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.DIM_COMPANY LIMIT 1").collect()
    except Exception as e:
        config.log_warning(f"  MARKET_DATA tables not found, skipping SAM_FUNDAMENTALS_VIEW")
        config.log_warning(f"Run with --scope structured to generate MARKET_DATA tables first")
        return
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {database_name}.AI.SAM_FUNDAMENTALS_VIEW
    TABLES (
        COMPANIES AS {database_name}.{market_data_schema}.DIM_COMPANY
            PRIMARY KEY (COMPANY_ID) 
            WITH SYNONYMS=('companies','firms','corporations','issuers') 
            COMMENT='Company master data from market data provider',
        FINANCIAL_PERIODS AS {database_name}.{market_data_schema}.FACT_FINANCIAL_PERIOD
            PRIMARY KEY (PERIOD_ID)
            WITH SYNONYMS=('periods','quarters','fiscal_periods')
            COMMENT='Fiscal period reference for financial statements',
        FINANCIALS AS {database_name}.{market_data_schema}.FACT_FINANCIAL_DATA
            PRIMARY KEY (FINANCIAL_DATA_ID)
            WITH SYNONYMS=('financial_data','statements','fundamentals')
            COMMENT='Financial statement data including income statement, balance sheet, and cash flow metrics',
        DATA_ITEMS AS {database_name}.{market_data_schema}.REF_DATA_ITEM
            PRIMARY KEY (DATA_ITEM_ID)
            WITH SYNONYMS=('metrics','data_items','financial_metrics')
            COMMENT='Reference table for financial data item definitions',
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
        FINANCIALS_TO_PERIODS AS FINANCIALS(PERIOD_ID) REFERENCES FINANCIAL_PERIODS(PERIOD_ID),
        FINANCIALS_TO_COMPANIES AS FINANCIALS(COMPANY_ID) REFERENCES COMPANIES(COMPANY_ID),
        FINANCIALS_TO_DATA_ITEMS AS FINANCIALS(DATA_ITEM_ID) REFERENCES DATA_ITEMS(DATA_ITEM_ID),
        PERIODS_TO_COMPANIES AS FINANCIAL_PERIODS(COMPANY_ID) REFERENCES COMPANIES(COMPANY_ID),
        CONSENSUS_TO_COMPANIES AS CONSENSUS(COMPANY_ID) REFERENCES COMPANIES(COMPANY_ID),
        ESTIMATES_TO_COMPANIES AS ANALYST_ESTIMATES(COMPANY_ID) REFERENCES COMPANIES(COMPANY_ID),
        ESTIMATES_TO_ANALYSTS AS ANALYST_ESTIMATES(ANALYST_ID) REFERENCES ANALYSTS(ANALYST_ID),
        ESTIMATES_TO_BROKERS AS ANALYST_ESTIMATES(BROKER_ID) REFERENCES BROKERS(BROKER_ID),
        ANALYSTS_TO_BROKERS AS ANALYSTS(BROKER_ID) REFERENCES BROKERS(BROKER_ID)
    )
    DIMENSIONS (
        -- Company dimensions
        COMPANIES.CompanyName AS COMPANY_NAME WITH SYNONYMS=('company_name','firm_name','corporation_name','issuer_name') COMMENT='Company legal name',
        COMPANIES.CountryCode AS COUNTRY_CODE WITH SYNONYMS=('country','domicile','country_of_incorporation') COMMENT='Country of incorporation (2-letter ISO code)',
        COMPANIES.IndustryDescription AS INDUSTRY_DESCRIPTION WITH SYNONYMS=('industry','sector','business_description') COMMENT='Industry classification description',
        COMPANIES.CIK AS CIK WITH SYNONYMS=('cik_number','sec_id','edgar_id') COMMENT='SEC Central Index Key for EDGAR filings',
        
        -- Period dimensions
        FINANCIAL_PERIODS.FiscalYear AS FISCAL_YEAR WITH SYNONYMS=('year','fiscal_year','fy') COMMENT='Fiscal year',
        FINANCIAL_PERIODS.FiscalQuarter AS FISCAL_QUARTER WITH SYNONYMS=('quarter','fiscal_quarter','q') COMMENT='Fiscal quarter (1-4)',
        FINANCIAL_PERIODS.PeriodCode AS PERIOD_CODE WITH SYNONYMS=('period','period_code','fiscal_period') COMMENT='Period code (e.g., 2024Q1)',
        FINANCIAL_PERIODS.PeriodEndDate AS PERIOD_END_DATE WITH SYNONYMS=('period_end','quarter_end','reporting_date') COMMENT='Period end date',
        
        -- Data item dimensions
        DATA_ITEMS.DataItemName AS DATA_ITEM_NAME WITH SYNONYMS=('metric_name','item_name','financial_metric') COMMENT='Name of the financial data item',
        DATA_ITEMS.DataCategory AS CATEGORY WITH SYNONYMS=('category','statement_type','financial_category') COMMENT='Category: income_statement, balance_sheet, cash_flow, ratios',
        
        -- Broker/Analyst dimensions
        BROKERS.BrokerName AS BROKER_NAME WITH SYNONYMS=('broker','research_firm','sell_side_firm') COMMENT='Broker/research firm name',
        ANALYSTS.AnalystName AS ANALYST_NAME WITH SYNONYMS=('analyst','research_analyst') COMMENT='Analyst name',
        ANALYSTS.SectorCoverage AS SECTOR_COVERAGE WITH SYNONYMS=('sector','coverage_sector') COMMENT='Analyst sector coverage'
    )
    METRICS (
        -- Financial statement metrics
        FINANCIALS.FINANCIAL_VALUE AS SUM(DATA_VALUE) WITH SYNONYMS=('value','amount','financial_amount') COMMENT='Financial data value (revenue, earnings, etc.)',
        FINANCIALS.AVG_FINANCIAL_VALUE AS AVG(DATA_VALUE) WITH SYNONYMS=('average_value','avg_amount') COMMENT='Average financial data value',
        FINANCIALS.FINANCIAL_RECORD_COUNT AS COUNT(FINANCIAL_DATA_ID) WITH SYNONYMS=('record_count','data_points') COMMENT='Count of financial data records',
        
        -- Investment memo metrics (TAM, NRR, Customer Count)
        FINANCIALS.TAM_VALUE AS SUM(CASE WHEN DATA_ITEM_ID = 1011 THEN DATA_VALUE END) WITH SYNONYMS=('tam','total_addressable_market','market_size','addressable_market') COMMENT='Total Addressable Market in USD',
        FINANCIALS.CUSTOMER_COUNT AS SUM(CASE WHEN DATA_ITEM_ID = 1012 THEN DATA_VALUE END) WITH SYNONYMS=('customers','total_customers','customer_base','customer_count') COMMENT='Total customer count',
        FINANCIALS.NRR_PCT AS AVG(CASE WHEN DATA_ITEM_ID = 4009 THEN DATA_VALUE END) WITH SYNONYMS=('nrr','net_revenue_retention','dollar_retention','revenue_retention') COMMENT='Net Revenue Retention percentage',
        
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
    COMMENT='Fundamentals semantic view for company financial analysis. Provides access to financial statements, analyst estimates, price targets, and ratings from market data provider.'
    WITH EXTENSION (CA='{{"tables":[{{"name":"COMPANIES","dimensions":[{{"name":"CompanyName"}},{{"name":"CountryCode"}},{{"name":"IndustryDescription"}},{{"name":"CIK"}}]}},{{"name":"FINANCIAL_PERIODS","dimensions":[{{"name":"FiscalYear"}},{{"name":"FiscalQuarter"}},{{"name":"PeriodCode"}},{{"name":"PeriodEndDate"}}]}},{{"name":"FINANCIALS","metrics":[{{"name":"FINANCIAL_VALUE"}},{{"name":"AVG_FINANCIAL_VALUE"}},{{"name":"FINANCIAL_RECORD_COUNT"}},{{"name":"TAM_VALUE"}},{{"name":"CUSTOMER_COUNT"}},{{"name":"NRR_PCT"}}]}},{{"name":"DATA_ITEMS","dimensions":[{{"name":"DataItemName"}},{{"name":"DataCategory"}}]}},{{"name":"CONSENSUS","metrics":[{{"name":"CONSENSUS_MEAN_VALUE"}},{{"name":"CONSENSUS_HIGH_VALUE"}},{{"name":"CONSENSUS_LOW_VALUE"}},{{"name":"AVG_NUM_ESTIMATES"}}]}},{{"name":"ANALYST_ESTIMATES","metrics":[{{"name":"AVG_PRICE_TARGET"}},{{"name":"MAX_PRICE_TARGET"}},{{"name":"MIN_PRICE_TARGET"}},{{"name":"AVG_RATING"}},{{"name":"ESTIMATE_COUNT"}}]}},{{"name":"BROKERS","dimensions":[{{"name":"BrokerName"}}]}},{{"name":"ANALYSTS","dimensions":[{{"name":"AnalystName"}},{{"name":"SectorCoverage"}}]}}],"relationships":[{{"name":"FINANCIALS_TO_PERIODS"}},{{"name":"FINANCIALS_TO_COMPANIES"}},{{"name":"FINANCIALS_TO_DATA_ITEMS"}},{{"name":"CONSENSUS_TO_COMPANIES"}},{{"name":"ESTIMATES_TO_COMPANIES"}},{{"name":"ESTIMATES_TO_ANALYSTS"}},{{"name":"ESTIMATES_TO_BROKERS"}}],"verified_queries":[{{"name":"company_revenue","question":"What is the revenue for a company?","sql":"SELECT __COMPANIES.COMPANY_NAME, __FINANCIAL_PERIODS.FISCAL_YEAR, __FINANCIAL_PERIODS.FISCAL_QUARTER, __FINANCIALS.DATA_VALUE as REVENUE FROM __FINANCIALS JOIN __COMPANIES ON __FINANCIALS.COMPANY_ID = __COMPANIES.COMPANY_ID JOIN __FINANCIAL_PERIODS ON __FINANCIALS.PERIOD_ID = __FINANCIAL_PERIODS.PERIOD_ID JOIN __DATA_ITEMS ON __FINANCIALS.DATA_ITEM_ID = __DATA_ITEMS.DATA_ITEM_ID WHERE __DATA_ITEMS.DATA_ITEM_CODE = \\'REVENUE\\' ORDER BY __FINANCIAL_PERIODS.FISCAL_YEAR DESC, __FINANCIAL_PERIODS.FISCAL_QUARTER DESC","use_as_onboarding_question":true}},{{"name":"analyst_consensus","question":"What is the analyst consensus for a company?","sql":"SELECT __COMPANIES.COMPANY_NAME, __CONSENSUS.ESTIMATE_YEAR, __CONSENSUS.FISCAL_QUARTER, AVG(__CONSENSUS.CONSENSUS_MEAN) as CONSENSUS_ESTIMATE, AVG(__CONSENSUS.NUM_ESTIMATES) as NUM_ANALYSTS FROM __CONSENSUS JOIN __COMPANIES ON __CONSENSUS.COMPANY_ID = __COMPANIES.COMPANY_ID GROUP BY __COMPANIES.COMPANY_NAME, __CONSENSUS.ESTIMATE_YEAR, __CONSENSUS.FISCAL_QUARTER ORDER BY __CONSENSUS.ESTIMATE_YEAR, __CONSENSUS.FISCAL_QUARTER","use_as_onboarding_question":true}},{{"name":"price_targets","question":"What are the analyst price targets for a company?","sql":"SELECT __COMPANIES.COMPANY_NAME, __BROKERS.BROKER_NAME, __ANALYST_ESTIMATES.DATA_VALUE as PRICE_TARGET, __ANALYST_ESTIMATES.ESTIMATE_DATE FROM __ANALYST_ESTIMATES JOIN __COMPANIES ON __ANALYST_ESTIMATES.COMPANY_ID = __COMPANIES.COMPANY_ID JOIN __BROKERS ON __ANALYST_ESTIMATES.BROKER_ID = __BROKERS.BROKER_ID WHERE __ANALYST_ESTIMATES.DATA_ITEM_ID = 5005 ORDER BY __ANALYST_ESTIMATES.ESTIMATE_DATE DESC","use_as_onboarding_question":true}},{{"name":"tam_analysis","question":"What is the total addressable market for a company?","sql":"SELECT __COMPANIES.COMPANY_NAME, __FINANCIAL_PERIODS.FISCAL_YEAR, __FINANCIAL_PERIODS.FISCAL_QUARTER, __FINANCIALS.DATA_VALUE as TAM FROM __FINANCIALS JOIN __COMPANIES ON __FINANCIALS.COMPANY_ID = __COMPANIES.COMPANY_ID JOIN __FINANCIAL_PERIODS ON __FINANCIALS.PERIOD_ID = __FINANCIAL_PERIODS.PERIOD_ID WHERE __FINANCIALS.DATA_ITEM_ID = 1011 ORDER BY __FINANCIAL_PERIODS.FISCAL_YEAR DESC, __FINANCIAL_PERIODS.FISCAL_QUARTER DESC","use_as_onboarding_question":false}},{{"name":"customer_metrics","question":"What is the customer count and retention for a company?","sql":"SELECT __COMPANIES.COMPANY_NAME, __FINANCIAL_PERIODS.FISCAL_YEAR, __FINANCIAL_PERIODS.FISCAL_QUARTER, MAX(CASE WHEN __FINANCIALS.DATA_ITEM_ID = 1012 THEN __FINANCIALS.DATA_VALUE END) as CUSTOMER_COUNT, MAX(CASE WHEN __FINANCIALS.DATA_ITEM_ID = 4009 THEN __FINANCIALS.DATA_VALUE END) as NRR_PCT FROM __FINANCIALS JOIN __COMPANIES ON __FINANCIALS.COMPANY_ID = __COMPANIES.COMPANY_ID JOIN __FINANCIAL_PERIODS ON __FINANCIALS.PERIOD_ID = __FINANCIAL_PERIODS.PERIOD_ID WHERE __FINANCIALS.DATA_ITEM_ID IN (1012, 4009) GROUP BY __COMPANIES.COMPANY_NAME, __FINANCIAL_PERIODS.FISCAL_YEAR, __FINANCIAL_PERIODS.FISCAL_QUARTER ORDER BY __FINANCIAL_PERIODS.FISCAL_YEAR DESC, __FINANCIAL_PERIODS.FISCAL_QUARTER DESC","use_as_onboarding_question":false}}],"module_custom_instructions":{{"sql_generation":"When querying financial data, always join with DATA_ITEMS to get readable metric names. For revenue queries, filter to DATA_ITEM_CODE = \\'REVENUE\\'. For earnings, use \\'NET_INCOME\\' or \\'EPS_DILUTED\\'. For margin analysis, use ratio metrics. For TAM queries, use DATA_ITEM_ID = 1011. For customer count, use DATA_ITEM_ID = 1012. For NRR (Net Revenue Retention), use DATA_ITEM_ID = 4009. Always order by fiscal year and quarter descending to show most recent first. For consensus estimates, show the number of analysts covering alongside the estimate values.","question_categorization":"If users ask about \\'financials\\' or \\'fundamentals\\', use FINANCIALS table with DATA_ITEMS join. If users ask about \\'estimates\\' or \\'consensus\\', use CONSENSUS table. If users ask about \\'price targets\\' or \\'ratings\\', use ANALYST_ESTIMATES table. If users ask about \\'analysts\\' or \\'brokers\\', include ANALYSTS and BROKERS dimensions. If users ask about \\'TAM\\', \\'market size\\', \\'addressable market\\', use TAM_VALUE metric. If users ask about \\'customers\\', \\'customer count\\', use CUSTOMER_COUNT metric. If users ask about \\'retention\\', \\'NRR\\', \\'net revenue retention\\', use NRR_PCT metric."}}}}');
    """).collect()
    
    config.log_detail(" Created semantic view: SAM_FUNDAMENTALS_VIEW")


def create_real_sec_semantic_view(session: Session):
    """
    Create semantic view for REAL SEC financial data from SNOWFLAKE_PUBLIC_DATA_FREE.
    
    This view provides access to:
    - Real SEC financial metrics (revenue, earnings, etc.) from SEC_METRICS_TIMESERIES
    - Real stock prices from STOCK_PRICE_TIMESERIES
    - Real SEC filing text (MD&A, Risk Factors) from SEC_REPORT_TEXT_ATTRIBUTES
    
    All data is linked to our DIM_ISSUER via CIK.
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    
    # Check if real data tables exist
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_FINANCIAL_DATA_SEC LIMIT 1").collect()
    except Exception:
        config.log_warning("  FACT_FINANCIAL_DATA_SEC not found - skipping SAM_REAL_SEC_VIEW creation")
        return
    
    config.log_detail("Creating SAM_REAL_SEC_VIEW for real SEC data...")
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {database_name}.AI.SAM_REAL_SEC_VIEW
    TABLES (
        SEC_FINANCIALS AS {database_name}.{market_data_schema}.FACT_FINANCIAL_DATA_SEC
            PRIMARY KEY (FINANCIAL_DATA_ID)
            WITH SYNONYMS=('sec_financials','real_financials','sec_metrics','financial_data')
            COMMENT='Real SEC financial metrics from 10-K and 10-Q filings.',
        COMPANIES AS {database_name}.{market_data_schema}.DIM_COMPANY
            PRIMARY KEY (COMPANY_ID)
            WITH SYNONYMS=('companies','firms','corporations')
            COMMENT='Company master data with CIK linkage',
        ISSUERS AS {database_name}.{curated_schema}.DIM_ISSUER
            PRIMARY KEY (ISSUERID)
            WITH SYNONYMS=('issuers','entities')
            COMMENT='Issuer dimension with CIK for SEC data linkage'
    )
    RELATIONSHIPS (
        FINANCIALS_TO_COMPANIES AS SEC_FINANCIALS(COMPANY_ID) REFERENCES COMPANIES(COMPANY_ID),
        FINANCIALS_TO_ISSUERS AS SEC_FINANCIALS(ISSUERID) REFERENCES ISSUERS(ISSUERID)
    )
    DIMENSIONS (
        COMPANIES.COMPANY_NAME AS COMPANY_NAME WITH SYNONYMS=('company_name','company','firm_name') COMMENT='Company name',
        SEC_FINANCIALS.SEC_COMPANY_NAME AS SEC_COMPANY_NAME WITH SYNONYMS=('sec_name','edgar_name') COMMENT='Company name as filed with SEC',
        COMPANIES.CIK AS CIK WITH SYNONYMS=('cik_number','sec_id') COMMENT='SEC Central Index Key',
        SEC_FINANCIALS.METRIC_NAME AS VARIABLE_NAME WITH SYNONYMS=('metric','variable','data_item') COMMENT='Name of the financial metric',
        SEC_FINANCIALS.SEGMENT AS BUSINESS_SEGMENT WITH SYNONYMS=('segment','business_segment') COMMENT='Business segment',
        SEC_FINANCIALS.GEOGRAPHY AS GEO_NAME WITH SYNONYMS=('geography','region') COMMENT='Geographic region',
        SEC_FINANCIALS.FISCAL_YEAR AS FISCAL_YEAR WITH SYNONYMS=('year','fy') COMMENT='Fiscal year',
        SEC_FINANCIALS.FISCAL_PERIOD AS FISCAL_PERIOD WITH SYNONYMS=('quarter','period') COMMENT='Fiscal period',
        SEC_FINANCIALS.PERIOD_END AS PERIOD_END_DATE WITH SYNONYMS=('period_end','end_date') COMMENT='Period end date'
    )
    METRICS (
        SEC_FINANCIALS.METRIC_VALUE AS SUM(VALUE) WITH SYNONYMS=('value','amount','total') COMMENT='Financial metric value',
        SEC_FINANCIALS.RECORD_COUNT AS COUNT(FINANCIAL_DATA_ID) WITH SYNONYMS=('count','records') COMMENT='Count of records',
        COMPANIES.COMPANY_COUNT AS COUNT(DISTINCT COMPANY_ID) WITH SYNONYMS=('companies','num_companies') COMMENT='Number of companies'
    )
    COMMENT='Real SEC financial data semantic view from SNOWFLAKE_PUBLIC_DATA_FREE'
    """).collect()
    
    config.log_detail(" Created semantic view: SAM_REAL_SEC_VIEW")


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
        config.log_warning("  FACT_STOCK_PRICES not found - skipping SAM_STOCK_PRICES_VIEW creation")
        return
    
    config.log_detail("Creating SAM_STOCK_PRICES_VIEW for real stock price data...")
    
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
        PRICES.TICKER AS TICKER WITH SYNONYMS=('ticker','symbol','stock_symbol') COMMENT='Stock ticker symbol',
        SECURITIES.DESCRIPTION AS Description WITH SYNONYMS=('security_name','company_name','name') COMMENT='Security/company name',
        SECURITIES.ASSETCLASS AS AssetClass WITH SYNONYMS=('asset_class','type') COMMENT='Asset class',
        ISSUERS.LEGALNAME AS LegalName WITH SYNONYMS=('issuer_name','legal_name') COMMENT='Legal issuer name',
        ISSUERS.INDUSTRY AS SIC_DESCRIPTION WITH SYNONYMS=('industry','sector') COMMENT='Industry classification',
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
    
    config.log_detail(" Created semantic view: SAM_STOCK_PRICES_VIEW")


def create_sec_financials_semantic_view(session: Session):
    """
    Create semantic view for comprehensive SEC financial statements from FACT_SEC_FINANCIALS.
    
    This view provides access to real Income Statement, Balance Sheet, and Cash Flow data
    with standardized metrics pivoted from SEC XBRL filings.
    """
    database_name = config.DATABASE['name']
    market_data_schema = config.DATABASE['schemas']['market_data']
    curated_schema = config.DATABASE['schemas']['curated']
    
    # Check if real data tables exist
    try:
        session.sql(f"SELECT 1 FROM {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS LIMIT 1").collect()
    except Exception:
        config.log_warning("  FACT_SEC_FINANCIALS not found - skipping SAM_SEC_FINANCIALS_VIEW creation")
        return
    
    config.log_detail("Creating SAM_SEC_FINANCIALS_VIEW for comprehensive SEC financial statements...")
    
    session.sql(f"""
CREATE OR REPLACE SEMANTIC VIEW {database_name}.AI.SAM_SEC_FINANCIALS_VIEW
    TABLES (
        FINANCIALS AS {database_name}.{market_data_schema}.FACT_SEC_FINANCIALS
            PRIMARY KEY (FINANCIAL_ID)
            WITH SYNONYMS=('financials','financial_statements','sec_financials','company_financials')
            COMMENT='Comprehensive SEC financial statements including Income Statement, Balance Sheet, and Cash Flow.',
        COMPANIES AS {database_name}.{market_data_schema}.DIM_COMPANY
            PRIMARY KEY (COMPANY_ID)
            WITH SYNONYMS=('companies','firms','corporations')
            COMMENT='Company master data with CIK linkage',
        ISSUERS AS {database_name}.{curated_schema}.DIM_ISSUER
            PRIMARY KEY (ISSUERID)
            WITH SYNONYMS=('issuers','entities')
            COMMENT='Issuer dimension with CIK for SEC data linkage'
    )
    RELATIONSHIPS (
        FINANCIALS_TO_COMPANIES AS FINANCIALS(COMPANY_ID) REFERENCES COMPANIES(COMPANY_ID),
        FINANCIALS_TO_ISSUERS AS FINANCIALS(ISSUERID) REFERENCES ISSUERS(ISSUERID)
    )
    DIMENSIONS (
        -- Company dimensions
        FINANCIALS.COMPANY_NAME AS COMPANY_NAME WITH SYNONYMS=('company','company_name','firm_name') COMMENT='Company name',
        FINANCIALS.CIK AS CIK WITH SYNONYMS=('cik_number','sec_id','central_index_key') COMMENT='SEC Central Index Key',
        COMPANIES.INDUSTRY_DESCRIPTION AS INDUSTRY_DESCRIPTION WITH SYNONYMS=('industry','sector','business_type') COMMENT='Industry classification',
        
        -- Currency dimension
        FINANCIALS.CURRENCY AS CURRENCY WITH SYNONYMS=('reporting_currency','currency_code','unit') COMMENT='Reporting currency (e.g., USD, EUR, CAD). Values are in actual units, not thousands or millions.',
        
        -- Time dimensions
        FINANCIALS.FISCAL_YEAR AS FISCAL_YEAR WITH SYNONYMS=('year','fy','fiscal') COMMENT='Fiscal year',
        FINANCIALS.FISCAL_PERIOD AS FISCAL_PERIOD WITH SYNONYMS=('quarter','period','q') COMMENT='Fiscal period (FY, Q1, Q2, Q3, Q4)',
        FINANCIALS.PERIOD_END_DATE AS PERIOD_END_DATE WITH SYNONYMS=('period_end','end_date','as_of_date') COMMENT='Period end date'
    )
    METRICS (
        -- Income Statement metrics
        FINANCIALS.TOTAL_REVENUE AS SUM(REVENUE) WITH SYNONYMS=('revenue','sales','total_revenue','top_line') COMMENT='Total revenue/sales',
        FINANCIALS.NET_INCOME_TOTAL AS SUM(NET_INCOME) WITH SYNONYMS=('net_income','earnings','profit','bottom_line') COMMENT='Net income',
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
        FINANCIALS.COMPANY_COUNT AS COUNT(DISTINCT COMPANY_ID) WITH SYNONYMS=('companies','num_companies') COMMENT='Number of companies'
    )
    COMMENT='Comprehensive SEC financial statements semantic view with Income Statement, Balance Sheet, and Cash Flow metrics from SEC XBRL filings. All monetary values are in actual units (not thousands or millions). CURRENCY dimension indicates reporting currency.'
    """).collect()
    
    config.log_detail(" Created semantic view: SAM_SEC_FINANCIALS_VIEW")
