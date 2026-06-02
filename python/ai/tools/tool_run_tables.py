"""
Tool Run Result Tables

Persistent tables for storing tool run output.
Stored procedures INSERT detailed data here with a unique run_id,
returning only summary metrics to the caller. This keeps agent
token budgets lean while making detailed data queryable.

Tables:
- TOOL_RUN_PORTFOLIOS: Portfolio weights per run (ticker-level rows)
- TOOL_BACKTEST_RUNS: Backtest run parameters + summary metrics
- TOOL_BACKTEST_TIMESERIES: Daily portfolio values per backtest run
- TOOL_SIMULATION_RUNS: Simulation run parameters + distribution metrics
- TOOL_SIMULATION_PATHS: Fan chart percentile paths per simulation run
- TOOL_SIMULATION_TERMINAL_VALUES: Terminal value samples for histogram
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail


def create_tool_run_tables(session: Session):
    ai_schema = f"{config.DATABASE['name']}.{config.DATABASE['schemas']['ai']}"

    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.TOOL_RUN_PORTFOLIOS (
            RUN_ID VARCHAR(36) NOT NULL,
            PORTFOLIO_IDX NUMBER NOT NULL,
            TICKER VARCHAR(20) NOT NULL,
            WEIGHT FLOAT NOT NULL,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PRIMARY KEY (RUN_ID, PORTFOLIO_IDX, TICKER)
        )
    """).collect()
    log_detail("  Created TOOL_RUN_PORTFOLIOS table")

    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.TOOL_BACKTEST_RUNS (
            RUN_ID VARCHAR(36) NOT NULL,
            PORTFOLIO_IDX NUMBER NOT NULL,
            START_DATE DATE NOT NULL,
            END_DATE DATE NOT NULL,
            REBALANCE_FREQ VARCHAR(20),
            TRADING_DAYS NUMBER,
            TOTAL_RETURN_PCT FLOAT,
            ANNUALIZED_RETURN_PCT FLOAT,
            ANNUALIZED_VOLATILITY_PCT FLOAT,
            SHARPE_RATIO FLOAT,
            SORTINO_RATIO FLOAT,
            CALMAR_RATIO FLOAT,
            MAX_DRAWDOWN_PCT FLOAT,
            VAR_95_DAILY_PCT FLOAT,
            CVAR_95_DAILY_PCT FLOAT,
            FINAL_VALUE FLOAT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PRIMARY KEY (RUN_ID, PORTFOLIO_IDX)
        )
    """).collect()
    log_detail("  Created TOOL_BACKTEST_RUNS table")

    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.TOOL_BACKTEST_TIMESERIES (
            RUN_ID VARCHAR(36) NOT NULL,
            PORTFOLIO_IDX NUMBER NOT NULL,
            AS_OF_DATE DATE NOT NULL,
            PORTFOLIO_VALUE FLOAT,
            DAILY_RETURN_PCT FLOAT,
            DRAWDOWN_PCT FLOAT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PRIMARY KEY (RUN_ID, PORTFOLIO_IDX, AS_OF_DATE)
        )
    """).collect()
    log_detail("  Created TOOL_BACKTEST_TIMESERIES table")

    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.TOOL_SIMULATION_RUNS (
            RUN_ID VARCHAR(36) NOT NULL,
            PORTFOLIO_IDX NUMBER NOT NULL,
            HORIZON_YEARS NUMBER,
            NUM_SIMULATIONS NUMBER,
            INITIAL_INVESTMENT FLOAT,
            MONTHLY_CONTRIBUTION FLOAT,
            CONTRIBUTION_GROWTH_PCT FLOAT,
            EXPECTED_RETURN_OVERRIDE_PCT FLOAT,
            TOTAL_CONTRIBUTED FLOAT,
            HISTORICAL_DAYS_USED NUMBER,
            PERCENTILE_5 FLOAT,
            PERCENTILE_25 FLOAT,
            MEDIAN FLOAT,
            PERCENTILE_75 FLOAT,
            PERCENTILE_95 FLOAT,
            MEAN_VALUE FLOAT,
            PROB_LOSS_PCT FLOAT,
            PROB_GAIN_5_PCT FLOAT,
            PROB_GAIN_10_PCT FLOAT,
            PROB_GAIN_20_PCT FLOAT,
            PROB_GAIN_50_PCT FLOAT,
            PROB_GAIN_100_PCT FLOAT,
            EXPECTED_ANNUAL_RETURN_PCT FLOAT,
            ANNUAL_VOLATILITY_PCT FLOAT,
            SHARPE_RATIO FLOAT,
            MAX_DRAWDOWN_90_PCTL_PCT FLOAT,
            MEDIAN_MULTIPLE FLOAT,
            UPSIDE_CASE_MULTIPLE FLOAT,
            DOWNSIDE_CASE_MULTIPLE FLOAT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PRIMARY KEY (RUN_ID, PORTFOLIO_IDX)
        )
    """).collect()
    log_detail("  Created TOOL_SIMULATION_RUNS table")

    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.TOOL_SIMULATION_PATHS (
            RUN_ID VARCHAR(36) NOT NULL,
            PORTFOLIO_IDX NUMBER NOT NULL,
            DAY_INDEX NUMBER NOT NULL,
            PERCENTILE_5 FLOAT,
            PERCENTILE_25 FLOAT,
            MEDIAN FLOAT,
            PERCENTILE_75 FLOAT,
            PERCENTILE_95 FLOAT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PRIMARY KEY (RUN_ID, PORTFOLIO_IDX, DAY_INDEX)
        )
    """).collect()
    log_detail("  Created TOOL_SIMULATION_PATHS table")

    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.TOOL_SIMULATION_TERMINAL_VALUES (
            RUN_ID VARCHAR(36) NOT NULL,
            PORTFOLIO_IDX NUMBER NOT NULL,
            SAMPLE_INDEX NUMBER NOT NULL,
            TERMINAL_VALUE FLOAT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PRIMARY KEY (RUN_ID, PORTFOLIO_IDX, SAMPLE_INDEX)
        )
    """).collect()
    log_detail("  Created TOOL_SIMULATION_TERMINAL_VALUES table")
