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
from datetime import date, timedelta

def run_attribution(session, portfolio_name_or_id, benchmark_id, start_date, end_date):
    '''Run Brinson-Fachler sector attribution for a portfolio against a benchmark over a period.'''
    
    # Exact match on ID or full name ("SAM " prefix optional); the value is bound, never pasted into SQL.
    lookup_value = str(portfolio_name_or_id or '').strip()
    portfolio_lookup = session.sql('''
        SELECT PORTFOLIOID, PORTFOLIONAME
        FROM SAM_DEMO.CURATED.DIM_PORTFOLIO
        WHERE PORTFOLIOID = TRY_CAST(? AS INTEGER)
           OR UPPER(PORTFOLIONAME) = UPPER(?)
           OR UPPER(PORTFOLIONAME) = UPPER('SAM ' || ?)
        ORDER BY IFF(PORTFOLIOID = TRY_CAST(? AS INTEGER), 0, 1)
        LIMIT 1
    ''', params=[lookup_value] * 4).collect()
    
    if not portfolio_lookup:
        available = session.sql("SELECT PORTFOLIOID || ': ' || PORTFOLIONAME AS P FROM SAM_DEMO.CURATED.DIM_PORTFOLIO ORDER BY PORTFOLIOID").collect()
        portfolio_list = ', '.join(r['P'] for r in available)
        return {{"error": f"Portfolio '{{portfolio_name_or_id}}' not found. Pass the full portfolio name or ID exactly. Available portfolios: {{portfolio_list}}"}}
    
    portfolio_id = int(portfolio_lookup[0]['PORTFOLIOID'])
    portfolio_name = portfolio_lookup[0]['PORTFOLIONAME']
    
    # Benchmark: ID, exact name, or the name as a code without spaces or punctuation
    # (S&P 500 = SP500, MSCI ACWI = MSCI_ACWI). Omitted = the portfolio's own benchmark.
    benchmarks = session.sql("SELECT BENCHMARKID, BENCHMARKNAME FROM SAM_DEMO.CURATED.DIM_BENCHMARK ORDER BY BENCHMARKID").collect()
    benchmark_value = str(benchmark_id or '').strip()
    if benchmark_value:
        code = ''.join(ch for ch in benchmark_value.upper() if ch.isalnum())
        match = [b for b in benchmarks
                 if str(b['BENCHMARKID']) == benchmark_value
                 or ''.join(ch for ch in b['BENCHMARKNAME'].upper() if ch.isalnum()) == code]
        if not match:
            listing = ', '.join(f"{{b['BENCHMARKID']}}: {{b['BENCHMARKNAME']}}" for b in benchmarks)
            return {{"error": f"Benchmark '{{benchmark_id}}' not found. Available benchmarks: {{listing}}"}}
        bm_id, bm_name = int(match[0]['BENCHMARKID']), match[0]['BENCHMARKNAME']
    else:
        own = session.sql('''
            SELECT b.BENCHMARKID, b.BENCHMARKNAME
            FROM SAM_DEMO.CURATED.DIM_PORTFOLIO p
            JOIN SAM_DEMO.CURATED.DIM_BENCHMARK b ON b.BENCHMARKID = p.BENCHMARKID
            WHERE p.PORTFOLIOID = ?
        ''', params=[portfolio_id]).collect()
        if not own:
            return {{"error": f"{{portfolio_name}} has no benchmark assigned; pass benchmark_id"}}
        bm_id, bm_name = int(own[0]['BENCHMARKID']), own[0]['BENCHMARKNAME']

    # Period: defaults to the 3 months up to the latest price date.
    latest = session.sql("SELECT MAX(PRICE_DATE) AS D FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES").collect()[0]['D']
    try:
        end = date.fromisoformat(str(end_date).strip()) if end_date else latest
        start = date.fromisoformat(str(start_date).strip()) if start_date else end - timedelta(days=91)
    except ValueError:
        return {{"error": f"Dates must be YYYY-MM-DD; got start_date={{start_date!r}}, end_date={{end_date!r}}"}}
    if start >= end:
        return {{"error": f"start_date {{start}} must be before end_date {{end}}"}}

    # Holdings are month-end snapshots whose weights sum to 1 per date, so weights come from the
    # snapshot at the start of the period rather than a sum across dates. Returns are each
    # security's price return over the period (last close on or before each date, within 10 days).
    attribution_sql = '''
        WITH pf_snapshot AS (
            SELECT MAX(HOLDINGDATE) AS D FROM SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR
            WHERE PORTFOLIOID = ? AND HOLDINGDATE <= ?::DATE
        ),
        bm_snapshot AS (
            SELECT MAX(HOLDING_DATE) AS D FROM SAM_DEMO.CURATED.FACT_BENCHMARK_HOLDINGS
            WHERE BENCHMARKID = ? AND HOLDING_DATE <= ?::DATE
        ),
        weights AS (
            SELECT 'P' AS SIDE, h.SECURITYID, h.PORTFOLIOWEIGHT AS W
            FROM SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR h JOIN pf_snapshot s ON h.HOLDINGDATE = s.D
            WHERE h.PORTFOLIOID = ?
            UNION ALL
            SELECT 'B', bh.SECURITYID, bh.BENCHMARK_WEIGHT
            FROM SAM_DEMO.CURATED.FACT_BENCHMARK_HOLDINGS bh JOIN bm_snapshot s ON bh.HOLDING_DATE = s.D
            WHERE bh.BENCHMARKID = ?
        ),
        start_px AS (
            SELECT SECURITYID, MAX_BY(PRICE_CLOSE, PRICE_DATE) AS PX
            FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES
            WHERE PRICE_DATE <= ?::DATE AND PRICE_DATE > DATEADD(day, -10, ?::DATE) AND PRICE_CLOSE > 0
              AND SECURITYID IN (SELECT SECURITYID FROM weights)
            GROUP BY SECURITYID
        ),
        end_px AS (
            SELECT SECURITYID, MAX_BY(PRICE_CLOSE, PRICE_DATE) AS PX
            FROM SAM_DEMO.MARKET_DATA.FACT_STOCK_PRICES
            WHERE PRICE_DATE <= ?::DATE AND PRICE_DATE > DATEADD(day, -10, ?::DATE) AND PRICE_CLOSE > 0
              AND SECURITYID IN (SELECT SECURITYID FROM weights)
            GROUP BY SECURITYID
        ),
        sec AS (
            SELECT w.SIDE, i.GICS_SECTOR AS SECTOR, w.W, e.PX / NULLIF(st.PX, 0) - 1 AS R,
                   ps.D AS PF_DATE, bs.D AS BM_DATE
            FROM weights w
            JOIN SAM_DEMO.CURATED.DIM_SECURITY s ON s.SECURITYID = w.SECURITYID
            JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON i.ISSUERID = s.ISSUERID
            LEFT JOIN start_px st ON st.SECURITYID = w.SECURITYID
            LEFT JOIN end_px e ON e.SECURITYID = w.SECURITYID
            CROSS JOIN pf_snapshot ps
            CROSS JOIN bm_snapshot bs
        )
        SELECT
            SECTOR,
            SUM(IFF(SIDE = 'P', W, 0)) AS WP,
            SUM(IFF(SIDE = 'B', W, 0)) AS WB,
            SUM(IFF(SIDE = 'P' AND R IS NOT NULL, W * R, 0)) / NULLIF(SUM(IFF(SIDE = 'P' AND R IS NOT NULL, W, 0)), 0) AS RP,
            SUM(IFF(SIDE = 'B' AND R IS NOT NULL, W * R, 0)) / NULLIF(SUM(IFF(SIDE = 'B' AND R IS NOT NULL, W, 0)), 0) AS RB,
            SUM(IFF(SIDE = 'P' AND R IS NOT NULL, W, 0)) AS WP_PRICED,
            ANY_VALUE(PF_DATE) AS PF_DATE,
            ANY_VALUE(BM_DATE) AS BM_DATE
        FROM sec
        GROUP BY SECTOR
        ORDER BY SECTOR
    '''
    s_iso, e_iso = start.isoformat(), end.isoformat()
    results = session.sql(attribution_sql, params=[
        portfolio_id, s_iso, bm_id, s_iso, portfolio_id, bm_id, s_iso, s_iso, e_iso, e_iso]).collect()

    if not results or not any(float(r['WP'] or 0) for r in results):
        return {{"error": f"No holdings for {{portfolio_name}} on or before {{start}}; holdings are month-end snapshots starting 2021-09-30"}}
    if not any(float(r['WB'] or 0) for r in results):
        return {{"error": f"No {{bm_name}} holdings on or before {{start}}"}}

    # Brinson-Fachler. A sector one side does not hold takes the other side's return, so it
    # carries no selection effect: allocation explains it.
    rows = []
    for r in results:
        wp, wb = float(r['WP'] or 0), float(r['WB'] or 0)
        rp = r['RP'] if r['RP'] is not None else r['RB']
        rb = r['RB'] if r['RB'] is not None else r['RP']
        rows.append((r['SECTOR'], wp, wb, float(rp or 0), float(rb or 0)))
    portfolio_return = sum(wp * rp for _, wp, _, rp, _ in rows)
    benchmark_return = sum(wb * rb for _, _, wb, _, rb in rows)
    active_return = portfolio_return - benchmark_return

    sector_attribution = {{}}
    total_allocation = total_selection = total_interaction = 0.0
    for sector, wp, wb, rp, rb in rows:
        allocation = (wp - wb) * (rb - benchmark_return)
        selection = wb * (rp - rb)
        interaction = (wp - wb) * (rp - rb)
        total_allocation += allocation
        total_selection += selection
        total_interaction += interaction
        if sector:
            sector_attribution[sector] = {{
                "portfolio_weight_pct": round(wp * 100, 1),
                "benchmark_weight_pct": round(wb * 100, 1),
                "portfolio_return_pct": round(rp * 100, 2),
                "benchmark_return_pct": round(rb * 100, 2),
                "allocation_effect_pct": round(allocation * 100, 3),
                "selection_effect_pct": round(selection * 100, 3),
                "interaction_effect_pct": round(interaction * 100, 3)
            }}
    priced = sum(float(r['WP_PRICED'] or 0) for r in results) / max(sum(float(r['WP'] or 0) for r in results), 1e-9)

    return {{
        "parameters": {{
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio_name,
            "benchmark_id": bm_id,
            "benchmark_name": bm_name,
            "start_date": s_iso,
            "end_date": e_iso,
            "weights_as_of": str(results[0]['PF_DATE']),
            "benchmark_weights_as_of": str(results[0]['BM_DATE']),
            "priced_weight_pct": round(priced * 100, 1)
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
    
    # Exact match on ID or full name ("SAM " prefix optional); the value is bound, never pasted into SQL.
    lookup_value = str(portfolio_name_or_id or '').strip()
    portfolio_lookup = session.sql('''
        SELECT PORTFOLIOID, PORTFOLIONAME
        FROM SAM_DEMO.CURATED.DIM_PORTFOLIO
        WHERE PORTFOLIOID = TRY_CAST(? AS INTEGER)
           OR UPPER(PORTFOLIONAME) = UPPER(?)
           OR UPPER(PORTFOLIONAME) = UPPER('SAM ' || ?)
        ORDER BY IFF(PORTFOLIOID = TRY_CAST(? AS INTEGER), 0, 1)
        LIMIT 1
    ''', params=[lookup_value] * 4).collect()
    
    if not portfolio_lookup:
        available = session.sql("SELECT PORTFOLIOID || ': ' || PORTFOLIONAME AS P FROM SAM_DEMO.CURATED.DIM_PORTFOLIO ORDER BY PORTFOLIOID").collect()
        portfolio_list = ', '.join(r['P'] for r in available)
        return {{"error": f"Portfolio '{{portfolio_name_or_id}}' not found. Pass the full portfolio name or ID exactly. Available portfolios: {{portfolio_list}}"}}
    
    portfolio_id = int(portfolio_lookup[0]['PORTFOLIOID'])
    portfolio_name = portfolio_lookup[0]['PORTFOLIONAME']
    
    # Get stress period details
    period = session.sql('''
        SELECT PERIOD_ID, START_DATE, END_DATE, DESCRIPTION, 
               DURATION_DAYS, MARKET_RETURN, PEAK_VIX, LINKED_SCENARIO_ID
        FROM SAM_DEMO.CURATED.FACT_HISTORICAL_STRESS_PERIODS
        WHERE PERIOD_ID = UPPER(TRIM(?))
    ''', params=[str(stress_period_id or '')]).collect()
    
    if not period:
        return {{"error": f"Stress period '{{stress_period_id}}' not found. Valid periods: COVID_CRASH, GFC, TAPER_TANTRUM, RATE_HIKE_2022, BANKING_CRISIS_2023"}}
    
    p = period[0]
    
    # Get factor exposures for portfolio
    exposures = session.sql('''
        SELECT FACTOR_NAME, PORTFOLIO_FACTOR_EXPOSURE AS AVG_EXPOSURE
        FROM SAM_DEMO.CURATED.FACT_FACTOR_ATTRIBUTION
        WHERE PORTFOLIOID = ?
        QUALIFY DATE = MAX(DATE) OVER ()
    ''', params=[portfolio_id]).collect()
    
    if not exposures:
        return {{"error": f"No factor exposures found for portfolio {{portfolio_id}}"}}
    
    # Get scenario shocks for linked scenario
    shocks = session.sql('''
        SELECT FACTOR_NAME, FACTOR_SHOCK, CONFIDENCE_LEVEL
        FROM SAM_DEMO.CURATED.FACT_SCENARIO_SHOCKS
        WHERE SCENARIO_ID = ?
    ''', params=[p['LINKED_SCENARIO_ID']]).collect()
    
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
    loss_floor_warning = None
    if total_impact < -1.0:
        loss_floor_warning = f"Raw factor model estimate of {{round(total_impact * 100, 1)}}% exceeds a total loss; result floored at -100%. Treat factor exposures for this portfolio with caution."
        total_impact = -1.0
    
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
        "warning": loss_floor_warning,
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
    
    # Exact match on ID or full name ("SAM " prefix optional); the value is bound, never pasted into SQL.
    lookup_value = str(portfolio_name_or_id or '').strip()
    portfolio_lookup = session.sql('''
        SELECT PORTFOLIOID, PORTFOLIONAME
        FROM SAM_DEMO.CURATED.DIM_PORTFOLIO
        WHERE PORTFOLIOID = TRY_CAST(? AS INTEGER)
           OR UPPER(PORTFOLIONAME) = UPPER(?)
           OR UPPER(PORTFOLIONAME) = UPPER('SAM ' || ?)
        ORDER BY IFF(PORTFOLIOID = TRY_CAST(? AS INTEGER), 0, 1)
        LIMIT 1
    ''', params=[lookup_value] * 4).collect()
    
    if not portfolio_lookup:
        available = session.sql("SELECT PORTFOLIOID || ': ' || PORTFOLIONAME AS P FROM SAM_DEMO.CURATED.DIM_PORTFOLIO ORDER BY PORTFOLIOID").collect()
        portfolio_list = ', '.join(r['P'] for r in available)
        return {{"error": f"Portfolio '{{portfolio_name_or_id}}' not found. Pass the full portfolio name or ID exactly. Available portfolios: {{portfolio_list}}"}}
    
    portfolio_id = int(portfolio_lookup[0]['PORTFOLIOID'])
    portfolio_name = portfolio_lookup[0]['PORTFOLIONAME']
    
    exposures = session.sql('''
        SELECT FACTOR_NAME, PORTFOLIO_FACTOR_EXPOSURE AS AVG_EXPOSURE
        FROM SAM_DEMO.CURATED.FACT_FACTOR_ATTRIBUTION
        WHERE PORTFOLIOID = ?
        QUALIFY DATE = MAX(DATE) OVER ()
    ''', params=[portfolio_id]).collect()
    
    if not exposures:
        return {{"error": f"No factor exposures found for portfolio {{portfolio_id}}"}}
    
    exposure_map = {{e['FACTOR_NAME']: float(e['AVG_EXPOSURE'] or 0) for e in exposures}}
    
    shock_vectors = {{
        'RATE_SHOCK': {{'Market': -0.05, 'Value': 0.010, 'Growth': -0.015, 'Momentum': -0.005, 'Quality': 0.005, 'Size': 0.003, 'Volatility': -0.010}},
        'VOL_SPIKE': {{'Market': -0.15, 'Value': -0.005, 'Growth': -0.015, 'Momentum': -0.010, 'Quality': 0.015, 'Size': 0.010, 'Volatility': -0.035}},
        'GROWTH_SELLOFF': {{'Market': -0.08, 'Value': 0.020, 'Growth': -0.035, 'Momentum': -0.015, 'Quality': 0.005, 'Size': 0.0, 'Volatility': -0.020}},
        'BROAD_MARKET': {{'Market': -0.20, 'Value': -0.010, 'Growth': -0.020, 'Momentum': -0.020, 'Quality': 0.015, 'Size': 0.010, 'Volatility': -0.030}}
    }}
    
    st = shock_type.upper() if shock_type else 'BROAD_MARKET'
    if st == 'CUSTOM':
        base_shocks = {{'Market': -0.10, 'Value': 0.0, 'Growth': -0.010, 'Momentum': -0.010, 'Quality': 0.0, 'Size': 0.0, 'Volatility': -0.015}}
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
    
    loss_floor_warning = None
    if total_impact < -1.0:
        loss_floor_warning = f"Raw factor model estimate of {{round(total_impact * 100, 1)}}% exceeds a total loss; result floored at -100%. Treat factor exposures for this portfolio with caution."
        total_impact = -1.0
    
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
    
    floored_scenarios = [k for k, v in scenario_impacts.items() if v < -1.0]
    if floored_scenarios:
        scenario_warning = f"Scenarios floored at -100% loss: {{', '.join(floored_scenarios)}}."
        loss_floor_warning = f"{{loss_floor_warning}} {{scenario_warning}}" if loss_floor_warning else scenario_warning
    scenario_returns = {{k: round(max(v, -1.0) * 100, 2) for k, v in scenario_impacts.items()}}
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
        "warning": loss_floor_warning,
        "interpretation": f"Under a {{st}} scenario ({{shock_magnitude}}x magnitude), {{portfolio_name}} estimated impact is {{round(total_impact * 100, 1)}}%. Most sensitive factor: {{most_sensitive}}. Across all 10 stress scenarios, estimated returns range from {{robustness['min_return_pct']}}% to {{robustness['max_return_pct']}}%."
    }}
$$;
    """
    
    try:
        session.sql(sensitivity_sql).collect()
        log_detail("  Created RUN_SCENARIO_SENSITIVITY_TOOL")
    except Exception as e:
        log_error(f" RUN_SCENARIO_SENSITIVITY_TOOL creation failed: {e}")
