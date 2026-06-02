"""
Attribution Tools for SAM Demo

Creates stored procedures for portfolio attribution analysis:
- RUN_ATTRIBUTION_TOOL: Brinson-Fachler performance attribution
- RUN_STRESS_BACKTEST_TOOL: Historical stress period analysis
- RUN_SCENARIO_SENSITIVITY_TOOL: Parameterised scenario sensitivity analysis
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_error


def create_attribution_tool(session: Session):
    """Create the RUN_ATTRIBUTION_TOOL stored procedure."""
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    attribution_sql = f"""
CREATE OR REPLACE PROCEDURE {database_name}.{ai_schema}.RUN_ATTRIBUTION_TOOL(
    portfolio_name_or_id VARCHAR,
    benchmark_id VARCHAR,
    start_date VARCHAR,
    end_date VARCHAR
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_attribution'
EXECUTE AS CALLER
AS
$$
def run_attribution(session, portfolio_name_or_id, benchmark_id, start_date, end_date):
    '''Run Brinson-Fachler performance attribution.'''
    
    portfolio_lookup = session.sql(f'''
        SELECT PORTFOLIOID, PORTFOLIONAME
        FROM SAM_DEMO.CURATED.DIM_PORTFOLIO
        WHERE PORTFOLIOID = TRY_CAST('{{portfolio_name_or_id}}' AS INTEGER)
           OR UPPER(PORTFOLIONAME) ILIKE '%' || UPPER('{{portfolio_name_or_id}}') || '%'
        ORDER BY CASE WHEN PORTFOLIOID = TRY_CAST('{{portfolio_name_or_id}}' AS INTEGER) THEN 0 ELSE LEN(PORTFOLIONAME) END
        LIMIT 1
    ''').collect()
    
    if not portfolio_lookup:
        available = session.sql("SELECT PORTFOLIOID || ': ' || PORTFOLIONAME AS P FROM SAM_DEMO.CURATED.DIM_PORTFOLIO ORDER BY PORTFOLIOID").collect()
        portfolio_list = ', '.join(r['P'] for r in available)
        return {{"error": f"Portfolio '{{portfolio_name_or_id}}' not found. Available portfolios: {{portfolio_list}}"}}
    
    portfolio_id = int(portfolio_lookup[0]['PORTFOLIOID'])
    portfolio_name = portfolio_lookup[0]['PORTFOLIONAME']
    
    # Query for attribution data
    attribution_sql = f'''
        WITH portfolio_sector_data AS (
            SELECT 
                i.GICS_Sector as Sector,
                SUM(h.PortfolioWeight) as PortfolioWeight,
                SUM(h.PortfolioWeight * COALESCE(r.YTD_RETURN_PCT, 0)) / NULLIF(SUM(h.PortfolioWeight), 0) as PortfolioReturn
            FROM SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR h
            JOIN SAM_DEMO.CURATED.DIM_SECURITY s ON h.SecurityID = s.SecurityID
            JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            LEFT JOIN SAM_DEMO.CURATED.V_SECURITY_RETURNS r 
                ON h.SecurityID = r.SECURITYID AND r.PRICE_DATE = h.HoldingDate
            WHERE h.PortfolioID = {{portfolio_id}}
              AND h.HoldingDate BETWEEN '{{start_date}}' AND '{{end_date}}'
            GROUP BY i.GICS_Sector
        ),
        benchmark_sector_data AS (
            SELECT 
                i.GICS_Sector as Sector,
                SUM(bh.Weight) as BenchmarkWeight,
                SUM(bh.Weight * COALESCE(r.YTD_RETURN_PCT, 0)) / NULLIF(SUM(bh.Weight), 0) as BenchmarkReturn
            FROM SAM_DEMO.CURATED.FACT_BENCHMARK_HOLDINGS bh
            JOIN SAM_DEMO.CURATED.DIM_SECURITY s ON bh.SecurityID = s.SecurityID
            JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            LEFT JOIN SAM_DEMO.CURATED.V_SECURITY_RETURNS r 
                ON bh.SecurityID = r.SECURITYID AND r.PRICE_DATE = bh.HoldingDate
            WHERE bh.BenchmarkID = '{{benchmark_id}}'
              AND bh.HoldingDate BETWEEN '{{start_date}}' AND '{{end_date}}'
            GROUP BY i.GICS_Sector
        ),
        combined AS (
            SELECT 
                COALESCE(p.Sector, b.Sector) as Sector,
                COALESCE(p.PortfolioWeight, 0) as Wp,
                COALESCE(b.BenchmarkWeight, 0) as Wb,
                COALESCE(p.PortfolioReturn, 0) / 100.0 as Rp,
                COALESCE(b.BenchmarkReturn, 0) / 100.0 as Rb
            FROM portfolio_sector_data p
            FULL OUTER JOIN benchmark_sector_data b ON p.Sector = b.Sector
        ),
        totals AS (
            SELECT 
                SUM(Wp * Rp) as TotalPortfolioReturn,
                SUM(Wb * Rb) as TotalBenchmarkReturn
            FROM combined
        )
        SELECT 
            c.Sector,
            c.Wp as PortfolioWeight,
            c.Wb as BenchmarkWeight,
            c.Rp as PortfolioReturn,
            c.Rb as BenchmarkReturn,
            (c.Wp - c.Wb) * (c.Rb - t.TotalBenchmarkReturn) as AllocationEffect,
            c.Wb * (c.Rp - c.Rb) as SelectionEffect,
            (c.Wp - c.Wb) * (c.Rp - c.Rb) as InteractionEffect,
            t.TotalPortfolioReturn,
            t.TotalBenchmarkReturn
        FROM combined c
        CROSS JOIN totals t
        ORDER BY c.Sector
    '''
    
    results = session.sql(attribution_sql).collect()
    
    if not results:
        return {{"error": "No data found for attribution analysis"}}
    
    # Aggregate effects
    total_allocation = sum(float(r['ALLOCATIONEFFECT'] or 0) for r in results)
    total_selection = sum(float(r['SELECTIONEFFECT'] or 0) for r in results)
    total_interaction = sum(float(r['INTERACTIONEFFECT'] or 0) for r in results)
    
    portfolio_return = float(results[0]['TOTALPORTFOLIORETURN'] or 0)
    benchmark_return = float(results[0]['TOTALBENCHMARKRETURN'] or 0)
    active_return = portfolio_return - benchmark_return
    
    # Sector breakdown
    sector_attribution = {{}}
    for r in results:
        if r['SECTOR']:
            sector_attribution[r['SECTOR']] = {{
                "portfolio_weight_pct": round(float(r['PORTFOLIOWEIGHT'] or 0) * 100, 1),
                "benchmark_weight_pct": round(float(r['BENCHMARKWEIGHT'] or 0) * 100, 1),
                "portfolio_return_pct": round(float(r['PORTFOLIORETURN'] or 0) * 100, 2),
                "benchmark_return_pct": round(float(r['BENCHMARKRETURN'] or 0) * 100, 2),
                "allocation_effect_pct": round(float(r['ALLOCATIONEFFECT'] or 0) * 100, 3),
                "selection_effect_pct": round(float(r['SELECTIONEFFECT'] or 0) * 100, 3),
                "interaction_effect_pct": round(float(r['INTERACTIONEFFECT'] or 0) * 100, 3)
            }}
    
    return {{
        "parameters": {{
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio_name,
            "benchmark_id": benchmark_id,
            "start_date": start_date,
            "end_date": end_date
        }},
        "returns": {{
            "portfolio_return_pct": round(portfolio_return * 100, 2),
            "benchmark_return_pct": round(benchmark_return * 100, 2),
            "active_return_pct": round(active_return * 100, 2)
        }},
        "attribution": {{
            "allocation_effect_pct": round(total_allocation * 100, 3),
            "selection_effect_pct": round(total_selection * 100, 3),
            "interaction_effect_pct": round(total_interaction * 100, 3),
            "total_attribution_pct": round((total_allocation + total_selection + total_interaction) * 100, 3)
        }},
        "sector_attribution": sector_attribution
    }}
$$;
    """
    
    try:
        session.sql(attribution_sql).collect()
        log_detail("  Created RUN_ATTRIBUTION_TOOL")
    except Exception as e:
        log_error(f" RUN_ATTRIBUTION_TOOL creation failed: {e}")


def create_stress_backtest_tool(session: Session):
    """Create the RUN_STRESS_BACKTEST_TOOL stored procedure."""
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    stress_backtest_sql = f"""
CREATE OR REPLACE PROCEDURE {database_name}.{ai_schema}.RUN_STRESS_BACKTEST_TOOL(
    portfolio_name_or_id VARCHAR,
    stress_period_id VARCHAR
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_stress_backtest'
EXECUTE AS CALLER
AS
$$
def run_stress_backtest(session, portfolio_name_or_id, stress_period_id):
    '''Calculate portfolio performance during historical stress period.'''
    
    portfolio_lookup = session.sql(f'''
        SELECT PORTFOLIOID, PORTFOLIONAME
        FROM SAM_DEMO.CURATED.DIM_PORTFOLIO
        WHERE PORTFOLIOID = TRY_CAST('{{portfolio_name_or_id}}' AS INTEGER)
           OR UPPER(PORTFOLIONAME) ILIKE '%' || UPPER('{{portfolio_name_or_id}}') || '%'
        ORDER BY CASE WHEN PORTFOLIOID = TRY_CAST('{{portfolio_name_or_id}}' AS INTEGER) THEN 0 ELSE LEN(PORTFOLIONAME) END
        LIMIT 1
    ''').collect()
    
    if not portfolio_lookup:
        available = session.sql("SELECT PORTFOLIOID || ': ' || PORTFOLIONAME AS P FROM SAM_DEMO.CURATED.DIM_PORTFOLIO ORDER BY PORTFOLIOID").collect()
        portfolio_list = ', '.join(r['P'] for r in available)
        return {{"error": f"Portfolio '{{portfolio_name_or_id}}' not found. Available portfolios: {{portfolio_list}}"}}
    
    portfolio_id = int(portfolio_lookup[0]['PORTFOLIOID'])
    portfolio_name = portfolio_lookup[0]['PORTFOLIONAME']
    
    # Get stress period details
    period = session.sql(f'''
        SELECT PERIOD_ID, START_DATE, END_DATE, DESCRIPTION, 
               DURATION_DAYS, MARKET_RETURN, PEAK_VIX, LINKED_SCENARIO_ID
        FROM SAM_DEMO.CURATED.FACT_HISTORICAL_STRESS_PERIODS
        WHERE PERIOD_ID = '{{stress_period_id}}'
    ''').collect()
    
    if not period:
        return {{"error": f"Stress period '{{stress_period_id}}' not found. Valid periods: COVID_CRASH, GFC, TAPER_TANTRUM, RATE_HIKE_2022, BANKING_CRISIS_2023"}}
    
    p = period[0]
    
    # Get factor exposures for portfolio
    exposures = session.sql(f'''
        SELECT FACTOR_NAME, AVG(PORTFOLIO_FACTOR_EXPOSURE) as AVG_EXPOSURE
        FROM SAM_DEMO.CURATED.FACT_FACTOR_ATTRIBUTION
        WHERE PORTFOLIOID = {{portfolio_id}}
        GROUP BY FACTOR_NAME
    ''').collect()
    
    if not exposures:
        return {{"error": f"No factor exposures found for portfolio {{portfolio_id}}"}}
    
    # Get scenario shocks for linked scenario
    shocks = session.sql(f'''
        SELECT FACTOR_NAME, FACTOR_SHOCK, CONFIDENCE_LEVEL
        FROM SAM_DEMO.CURATED.FACT_SCENARIO_SHOCKS
        WHERE SCENARIO_ID = {{p['LINKED_SCENARIO_ID']}}
    ''').collect()
    
    # Calculate estimated portfolio impact
    shock_map = {{s['FACTOR_NAME']: (float(s['FACTOR_SHOCK']), float(s['CONFIDENCE_LEVEL'])) for s in shocks}}
    
    total_impact = 0
    weighted_confidence = 0
    total_weight = 0
    factor_impacts = {{}}
    
    for exp in exposures:
        factor = exp['FACTOR_NAME']
        exposure = float(exp['AVG_EXPOSURE'] or 0)
        if factor in shock_map:
            shock, confidence = shock_map[factor]
            impact = exposure * shock
            factor_impacts[factor] = {{
                "exposure": round(exposure, 3),
                "shock_pct": round(shock * 100, 1),
                "impact_pct": round(impact * 100, 2),
                "confidence": round(confidence, 2)
            }}
            total_impact += impact
            weighted_confidence += confidence * abs(impact)
            total_weight += abs(impact)
        else:
            factor_impacts[factor] = {{
                "exposure": round(exposure, 3),
                "shock_pct": 0,
                "impact_pct": 0,
                "confidence": 0,
                "note": "No shock defined for this factor in scenario"
            }}
    
    avg_confidence = weighted_confidence / total_weight if total_weight > 0 else 0
    market_return = float(p['MARKET_RETURN'])
    
    return {{
        "stress_period": {{
            "id": p['PERIOD_ID'],
            "description": p['DESCRIPTION'],
            "start_date": str(p['START_DATE']),
            "end_date": str(p['END_DATE']),
            "duration_days": int(p['DURATION_DAYS']),
            "market_return_pct": round(market_return * 100, 1),
            "peak_vix": float(p['PEAK_VIX'])
        }},
        "portfolio_analysis": {{
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio_name,
            "estimated_return_pct": round(total_impact * 100, 2),
            "vs_market_pct": round((total_impact - market_return) * 100, 2),
            "outperforms_market": total_impact > market_return,
            "analysis_confidence": round(avg_confidence, 2)
        }},
        "factor_contributions": factor_impacts,
        "interpretation": f"{{portfolio_name}} (portfolio {{portfolio_id}}) estimated to return {{round(total_impact * 100, 1)}}% during {{p['DESCRIPTION']}} (market: {{round(market_return * 100, 1)}}%). " +
                         ("Portfolio would outperform market by " if total_impact > market_return else "Portfolio would underperform market by ") +
                         f"{{abs(round((total_impact - market_return) * 100, 1))}}%."
    }}
$$;
    """
    
    try:
        session.sql(stress_backtest_sql).collect()
        log_detail("  Created RUN_STRESS_BACKTEST_TOOL")
    except Exception as e:
        log_error(f" RUN_STRESS_BACKTEST_TOOL creation failed: {e}")


def create_scenario_sensitivity_tool(session: Session):
    """Create the RUN_SCENARIO_SENSITIVITY_TOOL stored procedure."""
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    sensitivity_sql = f"""
CREATE OR REPLACE PROCEDURE {database_name}.{ai_schema}.RUN_SCENARIO_SENSITIVITY_TOOL(
    portfolio_name_or_id VARCHAR,
    shock_type VARCHAR,
    shock_magnitude FLOAT
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_scenario_sensitivity'
EXECUTE AS CALLER
AS
$$
def run_scenario_sensitivity(session, portfolio_name_or_id, shock_type, shock_magnitude):
    '''Compute factor sensitivity ranking and alpha robustness for parameterised shocks.'''
    
    if shock_magnitude is None or shock_magnitude == 0:
        shock_magnitude = 1.0
    
    portfolio_lookup = session.sql(f'''
        SELECT PORTFOLIOID, PORTFOLIONAME
        FROM SAM_DEMO.CURATED.DIM_PORTFOLIO
        WHERE PORTFOLIOID = TRY_CAST('{{portfolio_name_or_id}}' AS INTEGER)
           OR UPPER(PORTFOLIONAME) ILIKE '%' || UPPER('{{portfolio_name_or_id}}') || '%'
        ORDER BY CASE WHEN PORTFOLIOID = TRY_CAST('{{portfolio_name_or_id}}' AS INTEGER) THEN 0 ELSE LEN(PORTFOLIONAME) END
        LIMIT 1
    ''').collect()
    
    if not portfolio_lookup:
        available = session.sql("SELECT PORTFOLIOID || ': ' || PORTFOLIONAME AS P FROM SAM_DEMO.CURATED.DIM_PORTFOLIO ORDER BY PORTFOLIOID").collect()
        portfolio_list = ', '.join(r['P'] for r in available)
        return {{"error": f"Portfolio '{{portfolio_name_or_id}}' not found. Available: {{portfolio_list}}"}}
    
    portfolio_id = int(portfolio_lookup[0]['PORTFOLIOID'])
    portfolio_name = portfolio_lookup[0]['PORTFOLIONAME']
    
    exposures = session.sql(f'''
        SELECT FACTOR_NAME, AVG(PORTFOLIO_FACTOR_EXPOSURE) AS AVG_EXPOSURE
        FROM SAM_DEMO.CURATED.FACT_FACTOR_ATTRIBUTION
        WHERE PORTFOLIOID = {{portfolio_id}}
        GROUP BY FACTOR_NAME
    ''').collect()
    
    if not exposures:
        return {{"error": f"No factor exposures found for portfolio {{portfolio_id}}"}}
    
    exposure_map = {{e['FACTOR_NAME']: float(e['AVG_EXPOSURE'] or 0) for e in exposures}}
    
    shock_vectors = {{
        'RATE_SHOCK': {{'Market': -0.05, 'Value': 0.03, 'Growth': -0.10, 'Momentum': -0.02, 'Quality': 0.01, 'Size': -0.03, 'Volatility': 0.15}},
        'VOL_SPIKE': {{'Market': -0.15, 'Value': -0.05, 'Growth': -0.12, 'Momentum': -0.08, 'Quality': 0.05, 'Size': -0.10, 'Volatility': 0.40}},
        'GROWTH_SELLOFF': {{'Market': -0.08, 'Value': 0.05, 'Growth': -0.25, 'Momentum': -0.10, 'Quality': 0.03, 'Size': -0.05, 'Volatility': 0.20}},
        'BROAD_MARKET': {{'Market': -0.20, 'Value': -0.05, 'Growth': -0.15, 'Momentum': -0.05, 'Quality': -0.02, 'Size': -0.08, 'Volatility': 0.30}}
    }}
    
    st = shock_type.upper() if shock_type else 'BROAD_MARKET'
    if st == 'CUSTOM':
        base_shocks = {{'Market': -0.10, 'Value': 0.0, 'Growth': -0.10, 'Momentum': -0.05, 'Quality': 0.0, 'Size': -0.05, 'Volatility': 0.15}}
    elif st in shock_vectors:
        base_shocks = shock_vectors[st]
    else:
        return {{"error": f"Unknown shock_type '{{shock_type}}'. Valid: RATE_SHOCK, VOL_SPIKE, GROWTH_SELLOFF, BROAD_MARKET, CUSTOM"}}
    
    scaled_shocks = {{f: s * shock_magnitude for f, s in base_shocks.items()}}
    
    factor_impacts = {{}}
    total_impact = 0
    for factor, exposure in exposure_map.items():
        shock = scaled_shocks.get(factor, 0)
        impact = exposure * shock
        factor_impacts[factor] = {{
            "exposure": round(exposure, 4),
            "shock_pct": round(shock * 100, 1),
            "impact_pct": round(impact * 100, 2),
            "sensitivity_rank": 0
        }}
        total_impact += impact
    
    sorted_factors = sorted(factor_impacts.items(), key=lambda x: abs(x[1]['impact_pct']), reverse=True)
    for rank, (factor, data) in enumerate(sorted_factors, 1):
        factor_impacts[factor]['sensitivity_rank'] = rank
    
    all_scenarios = session.sql('''
        SELECT ss.SCENARIO_ID, ss.SCENARIO_NAME, fs.FACTOR_NAME, fs.FACTOR_SHOCK
        FROM SAM_DEMO.CURATED.DIM_STRESS_SCENARIOS ss
        JOIN SAM_DEMO.CURATED.FACT_SCENARIO_SHOCKS fs ON ss.SCENARIO_ID = fs.SCENARIO_ID
    ''').collect()
    
    scenario_impacts = {{}}
    for row in all_scenarios:
        sid = row['SCENARIO_NAME']
        factor = row['FACTOR_NAME']
        shock = float(row['FACTOR_SHOCK'])
        if sid not in scenario_impacts:
            scenario_impacts[sid] = 0
        exposure = exposure_map.get(factor, 0)
        scenario_impacts[sid] += exposure * shock
    
    scenario_returns = {{k: round(v * 100, 2) for k, v in scenario_impacts.items()}}
    returns_list = list(scenario_returns.values())
    
    robustness = {{
        "scenario_returns": scenario_returns,
        "min_return_pct": min(returns_list) if returns_list else 0,
        "max_return_pct": max(returns_list) if returns_list else 0,
        "median_return_pct": round(sorted(returns_list)[len(returns_list)//2], 2) if returns_list else 0,
        "worst_scenario": min(scenario_returns, key=scenario_returns.get) if scenario_returns else "N/A",
        "best_scenario": max(scenario_returns, key=scenario_returns.get) if scenario_returns else "N/A"
    }}
    
    most_sensitive = sorted_factors[0][0] if sorted_factors else "N/A"
    least_sensitive = sorted_factors[-1][0] if sorted_factors else "N/A"
    
    return {{
        "portfolio": {{"id": portfolio_id, "name": portfolio_name}},
        "scenario": {{"shock_type": st, "magnitude": shock_magnitude}},
        "total_estimated_impact_pct": round(total_impact * 100, 2),
        "most_sensitive_factor": most_sensitive,
        "least_sensitive_factor": least_sensitive,
        "factor_sensitivity": factor_impacts,
        "robustness_assessment": robustness,
        "interpretation": f"Under a {{st}} scenario ({{shock_magnitude}}x magnitude), {{portfolio_name}} estimated impact is {{round(total_impact * 100, 1)}}%. Most sensitive factor: {{most_sensitive}}. Across all 10 stress scenarios, estimated returns range from {{robustness['min_return_pct']}}% to {{robustness['max_return_pct']}}%."
    }}
$$;
    """
    
    try:
        session.sql(sensitivity_sql).collect()
        log_detail("  Created RUN_SCENARIO_SENSITIVITY_TOOL")
    except Exception as e:
        log_error(f" RUN_SCENARIO_SENSITIVITY_TOOL creation failed: {e}")
