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
Monte Carlo Simulation Tools for SAM Demo

Creates UDFs and stored procedures for Monte Carlo simulation:
- NORM_PPF: Normal distribution quantile function
- SIMULATE_PATH: Single path simulation UDTF
- SIMULATE_PATH_BATCH: Batch path simulation UDTF
- RUN_MONTE_CARLO_TOOL: Main Monte Carlo procedure with block bootstrapping
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_error


def create_monte_carlo_udfs(session: Session):
    """Create UDFs required by Monte Carlo simulation for parallel execution."""
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    norm_ppf_sql = f"""
CREATE OR REPLACE FUNCTION {database_name}.{ai_schema}.NORM_PPF(probability FLOAT)
RETURNS FLOAT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('scipy')
HANDLER = 'norm_ppf'
AS $$
from scipy.stats import norm
def norm_ppf(p):
    if p is None or p <= 0 or p >= 1:
        return 0.0
    return float(norm.ppf(p))
$$;
"""
    try:
        session.sql(norm_ppf_sql).collect()
        log_detail("  Created NORM_PPF UDF")
    except Exception as e:
        log_error(f" NORM_PPF UDF creation failed: {e}")
    
    simulate_path_sql = f"""
CREATE OR REPLACE FUNCTION {database_name}.{ai_schema}.SIMULATE_PATH(
    residuals VARIANT,
    drift FLOAT,
    horizon_days INT,
    block_size INT,
    initial_value FLOAT,
    monthly_contribution FLOAT,
    contribution_growth_rate FLOAT,
    seed INT
)
RETURNS TABLE (
    day_id INT,
    portfolio_value FLOAT,
    total_contributed FLOAT,
    drawdown FLOAT
)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('numpy')
HANDLER = 'SimulatePath'
AS $$
import numpy as np

class SimulatePath:
    def process(self, residuals, drift, horizon_days, block_size, 
                initial_value, monthly_contribution, contribution_growth_rate, seed):
        np.random.seed(int(seed) % (2**31))
        if residuals is None:
            residuals = [0.0]
        elif isinstance(residuals, str):
            import json
            residuals = json.loads(residuals)
        residuals = np.array([float(r) for r in residuals])
        max_start = max(0, len(residuals) - block_size)
        
        value = float(initial_value)
        total_contributed = float(initial_value)
        peak_value = value
        
        block_start = np.random.randint(0, max_start + 1) if max_start > 0 else 0
        
        for day in range(int(horizon_days)):
            if day > 0 and day % block_size == 0:
                block_start = np.random.randint(0, max_start + 1) if max_start > 0 else 0
            
            idx = min(block_start + (day % block_size), len(residuals) - 1)
            daily_return = float(drift) + residuals[idx]
            value *= (1 + daily_return)
            
            if monthly_contribution > 0 and day > 0 and day % 21 == 0:
                months = day // 21
                years = months / 12.0
                contrib = float(monthly_contribution) * ((1 + float(contribution_growth_rate)) ** years)
                value += contrib
                total_contributed += contrib
            
            if value > peak_value:
                peak_value = value
            drawdown = (value - peak_value) / peak_value if peak_value > 0 else 0
            
            if day % 21 == 0 or day == int(horizon_days) - 1:
                yield (day, float(value), float(total_contributed), float(drawdown))
$$;
"""
    try:
        session.sql(simulate_path_sql).collect()
        log_detail("  Created SIMULATE_PATH UDTF")
    except Exception as e:
        log_error(f" SIMULATE_PATH UDTF creation failed: {e}")
    
    simulate_path_batch_sql = f"""
CREATE OR REPLACE FUNCTION {database_name}.{ai_schema}.SIMULATE_PATH_BATCH(
    portfolio_residuals ARRAY,
    drift FLOAT,
    horizon_days INT,
    block_size INT,
    initial_value FLOAT,
    monthly_contribution FLOAT,
    contribution_growth_rate FLOAT,
    seed INT
)
RETURNS TABLE (
    day_id INT,
    portfolio_value FLOAT,
    total_contributed FLOAT,
    drawdown FLOAT
)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('numpy')
HANDLER = 'SimulatePathBatch'
AS $$
import numpy as np

class SimulatePathBatch:
    def process(self, portfolio_residuals, drift, horizon_days, block_size, 
                initial_value, monthly_contribution, contribution_growth_rate, seed):
        np.random.seed(int(seed) % (2**31))
        
        residuals = [float(r) for r in portfolio_residuals] if portfolio_residuals else [0.0]
        num_days = len(residuals)
        max_start = max(0, num_days - block_size)
        
        value = float(initial_value)
        total_contributed = float(initial_value)
        peak_value = value
        
        block_start = np.random.randint(0, max_start + 1) if max_start > 0 else 0
        
        for day in range(int(horizon_days)):
            if day > 0 and day % block_size == 0:
                block_start = np.random.randint(0, max_start + 1) if max_start > 0 else 0
            
            idx = min(block_start + (day % block_size), num_days - 1)
            daily_return = float(drift) + residuals[idx]
            value *= (1 + daily_return)
            
            if monthly_contribution > 0 and day > 0 and day % 21 == 0:
                months = day // 21
                years = months / 12.0
                contrib = float(monthly_contribution) * ((1 + float(contribution_growth_rate)) ** years)
                value += contrib
                total_contributed += contrib
            
            if value > peak_value:
                peak_value = value
            drawdown = (value - peak_value) / peak_value if peak_value > 0 else 0
            
            if day % 21 == 0 or day == int(horizon_days) - 1:
                yield (day, float(value), float(total_contributed), float(drawdown))
$$;
"""
    try:
        session.sql(simulate_path_batch_sql).collect()
        log_detail("  Created SIMULATE_PATH_BATCH UDTF")
    except Exception as e:
        log_error(f" SIMULATE_PATH_BATCH UDTF creation failed: {e}")


def create_monte_carlo_tool(session: Session):
    """Create the RUN_MONTE_CARLO_TOOL stored procedure."""
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    monte_carlo_sql = f"""
CREATE OR REPLACE PROCEDURE {database_name}.{ai_schema}.RUN_MONTE_CARLO_TOOL(
    portfolios VARCHAR,
    horizon_years FLOAT,
    num_simulations FLOAT,
    initial_investment FLOAT,
    expected_return_pct FLOAT DEFAULT NULL,
    monthly_contribution FLOAT DEFAULT 0,
    contribution_growth_pct FLOAT DEFAULT 0
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
DECLARE
    num_sims INT := COALESCE(num_simulations::INT, 10000);
    horizon INT := COALESCE(horizon_years::INT, 10);
    initial FLOAT := COALESCE(initial_investment, 1000000);
    monthly_contrib FLOAT := COALESCE(monthly_contribution, 0);
    contrib_growth FLOAT := COALESCE(contribution_growth_pct, 0) / 100.0;
    horizon_days INT := horizon * 252;
    block_size INT := 21;
    drift_override FLOAT := CASE WHEN expected_return_pct IS NOT NULL THEN expected_return_pct / 100.0 / 252.0 ELSE NULL END;
    portfolios_array VARIANT := PARSE_JSON(portfolios);
    run_id VARCHAR;
    result VARIANT;
BEGIN
    run_id := UUID_STRING();

    INSERT INTO {database_name}.{ai_schema}.TOOL_RUN_PORTFOLIOS (RUN_ID, PORTFOLIO_IDX, TICKER, WEIGHT)
    WITH 
    portfolios_parsed AS (
        SELECT 
            p.index::INT as portfolio_id,
            f.key::VARCHAR as ticker,
            f.value::FLOAT as weight
        FROM TABLE(FLATTEN(input => :portfolios_array)) p,
             TABLE(FLATTEN(input => p.value)) f
    ),
    portfolios_normalized AS (
        SELECT 
            portfolio_id,
            ticker,
            weight / SUM(weight) OVER (PARTITION BY portfolio_id) as weight
        FROM portfolios_parsed
    )
    SELECT :run_id, portfolio_id, ticker, weight
    FROM portfolios_normalized;

    CREATE OR REPLACE TEMPORARY TABLE {database_name}.{ai_schema}._MC_SIM_PATHS AS
    WITH 
    portfolios_parsed AS (
        SELECT 
            p.index::INT as portfolio_id,
            f.key::VARCHAR as ticker,
            f.value::FLOAT as weight
        FROM TABLE(FLATTEN(input => :portfolios_array)) p,
             TABLE(FLATTEN(input => p.value)) f
    ),
    portfolios_normalized AS (
        SELECT 
            portfolio_id,
            ticker,
            weight / SUM(weight) OVER (PARTITION BY portfolio_id) as weight
        FROM portfolios_parsed
    ),
    all_tickers AS (
        SELECT DISTINCT ticker FROM portfolios_normalized
    ),
    ticker_returns AS (
        SELECT 
            s.Ticker,
            sr.PRICE_DATE,
            sr.DAILY_RETURN_PCT / 100.0 as daily_return
        FROM {database_name}.CURATED.V_SECURITY_RETURNS sr
        JOIN {database_name}.CURATED.DIM_SECURITY s ON sr.SECURITYID = s.SecurityID
        WHERE s.Ticker IN (SELECT ticker FROM all_tickers)
    ),
    portfolio_daily_returns AS (
        SELECT 
            p.portfolio_id,
            tr.PRICE_DATE,
            SUM(p.weight * tr.daily_return) as daily_return
        FROM portfolios_normalized p
        JOIN ticker_returns tr ON p.ticker = tr.Ticker
        GROUP BY p.portfolio_id, tr.PRICE_DATE
        HAVING COUNT(DISTINCT p.ticker) = (SELECT COUNT(DISTINCT ticker) FROM portfolios_normalized WHERE portfolio_id = p.portfolio_id)
    ),
    portfolio_stats AS (
        SELECT 
            portfolio_id,
            AVG(daily_return) as hist_mean,
            STDDEV(daily_return) as hist_std,
            COUNT(*) as num_days,
            ARRAY_AGG(daily_return) WITHIN GROUP (ORDER BY PRICE_DATE) as returns_array
        FROM portfolio_daily_returns
        GROUP BY portfolio_id
    ),
    portfolio_residuals AS (
        SELECT 
            ps.portfolio_id,
            ps.hist_mean,
            ps.hist_std,
            ps.num_days,
            ARRAY_AGG(pdr.daily_return - ps.hist_mean) WITHIN GROUP (ORDER BY pdr.PRICE_DATE) as residuals_array
        FROM portfolio_stats ps
        JOIN portfolio_daily_returns pdr ON ps.portfolio_id = pdr.portfolio_id
        GROUP BY ps.portfolio_id, ps.hist_mean, ps.hist_std, ps.num_days
    ),
    sims AS (
        SELECT 
            ROW_NUMBER() OVER (ORDER BY SEQ4()) as sim_id,
            ABS(MOD(HASH(SEQ4()), 2147483647)) as seed
        FROM TABLE(GENERATOR(ROWCOUNT => :num_sims))
    ),
    sim_paths AS (
        SELECT 
            pr.portfolio_id,
            s.sim_id,
            sp.DAY_ID,
            sp.PORTFOLIO_VALUE,
            sp.TOTAL_CONTRIBUTED,
            sp.DRAWDOWN
        FROM portfolio_residuals pr
        CROSS JOIN sims s,
        TABLE({database_name}.{ai_schema}.SIMULATE_PATH_BATCH(
            pr.residuals_array,
            COALESCE(:drift_override, pr.hist_mean),
            :horizon_days,
            :block_size,
            :initial,
            :monthly_contrib,
            :contrib_growth,
            s.seed
        )) sp
        WHERE pr.num_days >= 42
    )
    SELECT portfolio_id, sim_id, DAY_ID, PORTFOLIO_VALUE, TOTAL_CONTRIBUTED, DRAWDOWN
    FROM sim_paths;

    INSERT INTO {database_name}.{ai_schema}.TOOL_SIMULATION_PATHS (RUN_ID, PORTFOLIO_IDX, DAY_INDEX, PERCENTILE_5, PERCENTILE_25, MEDIAN, PERCENTILE_75, PERCENTILE_95)
    SELECT 
        :run_id,
        portfolio_id,
        DAY_ID,
        ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY PORTFOLIO_VALUE), 2),
        ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY PORTFOLIO_VALUE), 2),
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY PORTFOLIO_VALUE), 2),
        ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY PORTFOLIO_VALUE), 2),
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY PORTFOLIO_VALUE), 2)
    FROM {database_name}.{ai_schema}._MC_SIM_PATHS
    GROUP BY portfolio_id, DAY_ID;

    INSERT INTO {database_name}.{ai_schema}.TOOL_SIMULATION_TERMINAL_VALUES (RUN_ID, PORTFOLIO_IDX, SAMPLE_INDEX, TERMINAL_VALUE)
    SELECT 
        :run_id,
        portfolio_id,
        ROW_NUMBER() OVER (PARTITION BY portfolio_id ORDER BY RANDOM()),
        PORTFOLIO_VALUE
    FROM (
        SELECT portfolio_id, PORTFOLIO_VALUE,
               ROW_NUMBER() OVER (PARTITION BY portfolio_id ORDER BY RANDOM()) as rn
        FROM {database_name}.{ai_schema}._MC_SIM_PATHS
        WHERE DAY_ID = (SELECT MAX(DAY_ID) FROM {database_name}.{ai_schema}._MC_SIM_PATHS)
    )
    WHERE rn <= 500;

    INSERT INTO {database_name}.{ai_schema}.TOOL_SIMULATION_RUNS (
        RUN_ID, PORTFOLIO_IDX, HORIZON_YEARS, NUM_SIMULATIONS,
        INITIAL_INVESTMENT, MONTHLY_CONTRIBUTION, CONTRIBUTION_GROWTH_PCT,
        EXPECTED_RETURN_OVERRIDE_PCT, TOTAL_CONTRIBUTED, HISTORICAL_DAYS_USED,
        PERCENTILE_5, PERCENTILE_25, MEDIAN, PERCENTILE_75, PERCENTILE_95,
        MEAN_VALUE, PROB_LOSS_PCT, PROB_GAIN_5_PCT, PROB_GAIN_10_PCT,
        PROB_GAIN_20_PCT, PROB_GAIN_50_PCT, PROB_GAIN_100_PCT,
        EXPECTED_ANNUAL_RETURN_PCT, ANNUAL_VOLATILITY_PCT, SHARPE_RATIO,
        MAX_DRAWDOWN_90_PCTL_PCT, MEDIAN_MULTIPLE, UPSIDE_CASE_MULTIPLE, DOWNSIDE_CASE_MULTIPLE
    )
    WITH 
    max_day AS (
        SELECT MAX(DAY_ID) as max_day_id FROM {database_name}.{ai_schema}._MC_SIM_PATHS
    ),
    terminal_values AS (
        SELECT sp.portfolio_id, sp.sim_id, sp.PORTFOLIO_VALUE, sp.TOTAL_CONTRIBUTED, sp.DRAWDOWN
        FROM {database_name}.{ai_schema}._MC_SIM_PATHS sp
        CROSS JOIN max_day md
        WHERE sp.DAY_ID = md.max_day_id
    ),
    portfolio_hist AS (
        SELECT 
            portfolio_id,
            COUNT(DISTINCT sim_id) as num_days_proxy
        FROM {database_name}.{ai_schema}._MC_SIM_PATHS
        WHERE DAY_ID = 0
        GROUP BY portfolio_id
    ),
    terminal_stats AS (
        SELECT
            tv.portfolio_id,
            PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY tv.PORTFOLIO_VALUE) as p5,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY tv.PORTFOLIO_VALUE) as p25,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY tv.PORTFOLIO_VALUE) as p50,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY tv.PORTFOLIO_VALUE) as p75,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY tv.PORTFOLIO_VALUE) as p95,
            AVG(tv.PORTFOLIO_VALUE) as mean_val,
            STDDEV(tv.PORTFOLIO_VALUE) as stddev_val,
            AVG(tv.TOTAL_CONTRIBUTED) as avg_contributed,
            SUM(CASE WHEN tv.PORTFOLIO_VALUE < tv.TOTAL_CONTRIBUTED THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as prob_loss,
            SUM(CASE WHEN tv.PORTFOLIO_VALUE >= tv.TOTAL_CONTRIBUTED * 1.05 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as prob_gain_5,
            SUM(CASE WHEN tv.PORTFOLIO_VALUE >= tv.TOTAL_CONTRIBUTED * 1.10 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as prob_gain_10,
            SUM(CASE WHEN tv.PORTFOLIO_VALUE >= tv.TOTAL_CONTRIBUTED * 1.20 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as prob_gain_20,
            SUM(CASE WHEN tv.PORTFOLIO_VALUE >= tv.TOTAL_CONTRIBUTED * 1.50 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as prob_gain_50,
            SUM(CASE WHEN tv.PORTFOLIO_VALUE >= tv.TOTAL_CONTRIBUTED * 2.00 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as prob_gain_100,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY tv.DRAWDOWN) as max_dd_90
        FROM terminal_values tv
        GROUP BY tv.portfolio_id
    )
    SELECT 
        :run_id,
        ts.portfolio_id,
        :horizon,
        :num_sims,
        :initial,
        :monthly_contrib,
        :contribution_growth_pct,
        :expected_return_pct,
        ROUND(ts.avg_contributed, 0),
        ph.num_days_proxy,
        ROUND(ts.p5, 0),
        ROUND(ts.p25, 0),
        ROUND(ts.p50, 0),
        ROUND(ts.p75, 0),
        ROUND(ts.p95, 0),
        ROUND(ts.mean_val, 0),
        ROUND(ts.prob_loss, 1),
        ROUND(ts.prob_gain_5, 1),
        ROUND(ts.prob_gain_10, 1),
        ROUND(ts.prob_gain_20, 1),
        ROUND(ts.prob_gain_50, 1),
        ROUND(ts.prob_gain_100, 1),
        ROUND((POWER(ts.p50 / :initial, 1.0 / :horizon) - 1) * 100, 2),
        ROUND(ts.stddev_val / NULLIF(ts.mean_val, 0) * 100, 2),
        ROUND((POWER(ts.p50 / :initial, 1.0 / :horizon) - 1) / NULLIF(ts.stddev_val / NULLIF(ts.mean_val, 0), 0), 2),
        ROUND(ts.max_dd_90 * 100, 2),
        ROUND(ts.p50 / :initial, 2),
        ROUND(ts.p95 / :initial, 2),
        ROUND(ts.p5 / :initial, 2)
    FROM terminal_stats ts
    JOIN portfolio_hist ph ON ts.portfolio_id = ph.portfolio_id;

    SELECT ARRAY_AGG(
        OBJECT_CONSTRUCT(
            'run_id', RUN_ID,
            'portfolio_idx', PORTFOLIO_IDX,
            'parameters', OBJECT_CONSTRUCT(
                'horizon_years', HORIZON_YEARS,
                'num_simulations', NUM_SIMULATIONS,
                'initial_investment', INITIAL_INVESTMENT,
                'monthly_contribution', MONTHLY_CONTRIBUTION,
                'contribution_growth_pct', CONTRIBUTION_GROWTH_PCT,
                'expected_return_pct', EXPECTED_RETURN_OVERRIDE_PCT,
                'total_contributed', TOTAL_CONTRIBUTED,
                'historical_days_used', HISTORICAL_DAYS_USED
            ),
            'distribution', OBJECT_CONSTRUCT(
                'percentile_5', PERCENTILE_5,
                'percentile_25', PERCENTILE_25,
                'median', MEDIAN,
                'percentile_75', PERCENTILE_75,
                'percentile_95', PERCENTILE_95,
                'mean', MEAN_VALUE
            ),
            'probabilities', OBJECT_CONSTRUCT(
                'prob_loss_pct', PROB_LOSS_PCT,
                'prob_gain_5_pct', PROB_GAIN_5_PCT,
                'prob_gain_10_pct', PROB_GAIN_10_PCT,
                'prob_gain_20_pct', PROB_GAIN_20_PCT,
                'prob_gain_50_pct', PROB_GAIN_50_PCT,
                'prob_gain_100_pct', PROB_GAIN_100_PCT
            ),
            'risk_metrics', OBJECT_CONSTRUCT(
                'expected_annual_return_pct', EXPECTED_ANNUAL_RETURN_PCT,
                'annual_volatility_pct', ANNUAL_VOLATILITY_PCT,
                'sharpe_ratio', SHARPE_RATIO,
                'max_drawdown_90_pctl_pct', MAX_DRAWDOWN_90_PCTL_PCT
            ),
            'interpretation', OBJECT_CONSTRUCT(
                'median_multiple', MEDIAN_MULTIPLE,
                'upside_case_multiple', UPSIDE_CASE_MULTIPLE,
                'downside_case_multiple', DOWNSIDE_CASE_MULTIPLE
            )
        )
    ) INTO :result
    FROM {database_name}.{ai_schema}.TOOL_SIMULATION_RUNS
    WHERE RUN_ID = :run_id
    ORDER BY PORTFOLIO_IDX;

    DROP TABLE IF EXISTS {database_name}.{ai_schema}._MC_SIM_PATHS;

    RETURN result;
END;
    """
    
    try:
        session.sql(monte_carlo_sql).collect()
        log_detail("  Created RUN_MONTE_CARLO_TOOL")
    except Exception as e:
        log_error(f" RUN_MONTE_CARLO_TOOL creation failed: {e}")
