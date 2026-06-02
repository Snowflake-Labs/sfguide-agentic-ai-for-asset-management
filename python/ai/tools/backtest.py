"""
Backtest Tool for SAM Demo

Creates the RUN_BACKTEST_TOOL stored procedure for historical portfolio analysis:
- Calculates daily portfolio returns
- Computes performance metrics (total return, annualized return, volatility)
- Calculates risk-adjusted ratios (Sharpe, Sortino, Calmar)
- Measures tail risk (VaR, CVaR at 95%)
- Tracks drawdowns
- Persists portfolio weights to TOOL_RUN_PORTFOLIOS
- Persists daily timeseries to TOOL_BACKTEST_TIMESERIES
- Persists summary metrics to TOOL_BACKTEST_RUNS
- Returns compact summary metrics + run_id (no timeseries in payload)
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_error


def create_backtest_tool(session: Session):
    """Create the RUN_BACKTEST_TOOL stored procedure."""
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    backtest_sql = f"""
CREATE OR REPLACE PROCEDURE {database_name}.{ai_schema}.RUN_BACKTEST_TOOL(
    portfolios VARCHAR,
    start_date VARCHAR,
    end_date VARCHAR,
    rebalance_freq VARCHAR
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
DECLARE
    rf_daily FLOAT := 0.04 / 252;
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

    INSERT INTO {database_name}.{ai_schema}.TOOL_BACKTEST_TIMESERIES (RUN_ID, PORTFOLIO_IDX, AS_OF_DATE, PORTFOLIO_VALUE, DAILY_RETURN_PCT, DRAWDOWN_PCT)
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
          AND sr.PRICE_DATE BETWEEN :start_date AND :end_date
    ),
    portfolio_daily_returns AS (
        SELECT 
            p.portfolio_id,
            tr.PRICE_DATE,
            SUM(p.weight * tr.daily_return) as daily_return
        FROM portfolios_normalized p
        JOIN ticker_returns tr ON p.ticker = tr.Ticker
        GROUP BY p.portfolio_id, tr.PRICE_DATE
    ),
    portfolio_cumulative AS (
        SELECT 
            portfolio_id,
            PRICE_DATE,
            daily_return,
            EXP(SUM(LN(1 + daily_return)) OVER (
                PARTITION BY portfolio_id 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )) as cumulative_value,
            ROW_NUMBER() OVER (PARTITION BY portfolio_id ORDER BY PRICE_DATE) as day_num
        FROM portfolio_daily_returns
    ),
    portfolio_drawdown AS (
        SELECT 
            portfolio_id,
            PRICE_DATE,
            daily_return,
            cumulative_value,
            day_num,
            MAX(cumulative_value) OVER (
                PARTITION BY portfolio_id 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) as peak_value,
            (MAX(cumulative_value) OVER (
                PARTITION BY portfolio_id 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) - cumulative_value) / NULLIF(MAX(cumulative_value) OVER (
                PARTITION BY portfolio_id 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ), 0) as drawdown
        FROM portfolio_cumulative
    )
    SELECT 
        :run_id,
        portfolio_id,
        PRICE_DATE,
        ROUND(cumulative_value * 1000000, 2),
        ROUND(daily_return * 100, 4),
        ROUND(-drawdown * 100, 4)
    FROM portfolio_drawdown;

    INSERT INTO {database_name}.{ai_schema}.TOOL_BACKTEST_RUNS (
        RUN_ID, PORTFOLIO_IDX, START_DATE, END_DATE, REBALANCE_FREQ,
        TRADING_DAYS, TOTAL_RETURN_PCT, ANNUALIZED_RETURN_PCT, ANNUALIZED_VOLATILITY_PCT,
        SHARPE_RATIO, SORTINO_RATIO, CALMAR_RATIO, MAX_DRAWDOWN_PCT,
        VAR_95_DAILY_PCT, CVAR_95_DAILY_PCT, FINAL_VALUE
    )
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
          AND sr.PRICE_DATE BETWEEN :start_date AND :end_date
    ),
    portfolio_daily_returns AS (
        SELECT 
            p.portfolio_id,
            tr.PRICE_DATE,
            SUM(p.weight * tr.daily_return) as daily_return
        FROM portfolios_normalized p
        JOIN ticker_returns tr ON p.ticker = tr.Ticker
        GROUP BY p.portfolio_id, tr.PRICE_DATE
    ),
    portfolio_cumulative AS (
        SELECT 
            portfolio_id,
            PRICE_DATE,
            daily_return,
            EXP(SUM(LN(1 + daily_return)) OVER (
                PARTITION BY portfolio_id 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )) as cumulative_value,
            ROW_NUMBER() OVER (PARTITION BY portfolio_id ORDER BY PRICE_DATE) as day_num
        FROM portfolio_daily_returns
    ),
    portfolio_drawdown AS (
        SELECT 
            portfolio_id,
            PRICE_DATE,
            daily_return,
            cumulative_value,
            day_num,
            (MAX(cumulative_value) OVER (
                PARTITION BY portfolio_id 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) - cumulative_value) / NULLIF(MAX(cumulative_value) OVER (
                PARTITION BY portfolio_id 
                ORDER BY PRICE_DATE 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ), 0) as drawdown
        FROM portfolio_cumulative
    ),
    portfolio_stats AS (
        SELECT 
            portfolio_id,
            COUNT(*) as trading_days,
            COUNT(*) / 252.0 as num_years,
            MAX(cumulative_value) as final_cumulative,
            MAX(cumulative_value) - 1 as total_return,
            AVG(daily_return) as mean_return,
            STDDEV(daily_return) as daily_std,
            STDDEV(daily_return) * SQRT(252) as annualized_vol,
            MAX(drawdown) as max_drawdown,
            AVG(daily_return - :rf_daily) as excess_return_avg,
            SQRT(AVG(CASE WHEN daily_return < :rf_daily THEN POWER(daily_return - :rf_daily, 2) ELSE 0 END)) * SQRT(252) as downside_dev,
            PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY daily_return) as var_95_quantile
        FROM portfolio_drawdown
        GROUP BY portfolio_id
    ),
    portfolio_cvar AS (
        SELECT 
            pd.portfolio_id,
            AVG(pd.daily_return) as cvar_95
        FROM portfolio_drawdown pd
        JOIN portfolio_stats ps ON pd.portfolio_id = ps.portfolio_id
        WHERE pd.daily_return <= ps.var_95_quantile
        GROUP BY pd.portfolio_id
    )
    SELECT 
        :run_id,
        ps.portfolio_id,
        :start_date::DATE,
        :end_date::DATE,
        :rebalance_freq,
        ps.trading_days,
        ROUND((ps.total_return) * 100, 2),
        ROUND((POWER(1 + ps.total_return, 1.0 / NULLIF(ps.num_years, 0)) - 1) * 100, 2),
        ROUND(ps.annualized_vol * 100, 2),
        ROUND(ps.excess_return_avg * 252 / NULLIF(ps.annualized_vol, 0), 3),
        ROUND((POWER(1 + ps.total_return, 1.0 / NULLIF(ps.num_years, 0)) - 1 - 0.04) / NULLIF(ps.downside_dev, 0), 3),
        ROUND((POWER(1 + ps.total_return, 1.0 / NULLIF(ps.num_years, 0)) - 1) / NULLIF(ps.max_drawdown, 0), 3),
        ROUND(ps.max_drawdown * 100, 2),
        ROUND(-ps.var_95_quantile * 100, 2),
        ROUND(-pc.cvar_95 * 100, 2),
        ROUND(ps.final_cumulative * 1000000, 2)
    FROM portfolio_stats ps
    JOIN portfolio_cvar pc ON ps.portfolio_id = pc.portfolio_id;

    SELECT ARRAY_AGG(
        OBJECT_CONSTRUCT(
            'run_id', RUN_ID,
            'portfolio_idx', PORTFOLIO_IDX,
            'parameters', OBJECT_CONSTRUCT(
                'start_date', TO_VARCHAR(START_DATE, 'YYYY-MM-DD'),
                'end_date', TO_VARCHAR(END_DATE, 'YYYY-MM-DD'),
                'rebalance_freq', REBALANCE_FREQ,
                'trading_days', TRADING_DAYS
            ),
            'performance', OBJECT_CONSTRUCT(
                'total_return_pct', TOTAL_RETURN_PCT,
                'annualized_return_pct', ANNUALIZED_RETURN_PCT,
                'annualized_volatility_pct', ANNUALIZED_VOLATILITY_PCT
            ),
            'risk_adjusted', OBJECT_CONSTRUCT(
                'sharpe_ratio', SHARPE_RATIO,
                'sortino_ratio', SORTINO_RATIO,
                'calmar_ratio', CALMAR_RATIO
            ),
            'risk_metrics', OBJECT_CONSTRUCT(
                'max_drawdown_pct', MAX_DRAWDOWN_PCT,
                'var_95_daily_pct', VAR_95_DAILY_PCT,
                'cvar_95_daily_pct', CVAR_95_DAILY_PCT
            ),
            'final_value', FINAL_VALUE
        )
    ) INTO :result
    FROM {database_name}.{ai_schema}.TOOL_BACKTEST_RUNS
    WHERE RUN_ID = :run_id
    ORDER BY PORTFOLIO_IDX;

    RETURN result;
END;
    """
    
    try:
        session.sql(backtest_sql).collect()
        log_detail("  Created RUN_BACKTEST_TOOL")
    except Exception as e:
        log_error(f" RUN_BACKTEST_TOOL creation failed: {e}")
