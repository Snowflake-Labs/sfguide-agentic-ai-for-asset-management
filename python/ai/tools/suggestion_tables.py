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
Portfolio Suggestion Tables

Creates the normalized tables for storing portfolio suggestions
with backtest and simulation results.
"""

from snowflake.snowpark import Session
import config


def create_suggestion_tables(session: Session):
    """
    Create normalized tables for portfolio suggestions.
    
    Tables created:
    - PORTFOLIO_SUGGESTIONS: Main suggestion metadata
    - PORTFOLIO_SUGGESTION_HOLDINGS: Ticker weights per variant
    - PORTFOLIO_SUGGESTION_BACKTEST: Backtest metrics per variant
    - PORTFOLIO_SUGGESTION_BACKTEST_TIMESERIES: Daily values
    - PORTFOLIO_SUGGESTION_SIMULATION: Simulation metrics per variant
    - PORTFOLIO_SUGGESTION_SIMULATION_PATHS: Percentile paths per year
    """
    ai_schema = f"{config.DATABASE['name']}.{config.DATABASE['schemas']['ai']}"
    
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.PORTFOLIO_SUGGESTIONS (
            SUGGESTION_ID NUMBER IDENTITY PRIMARY KEY,
            SUGGESTION_NAME VARCHAR(255) NOT NULL,
            DESCRIPTION VARCHAR(2000),
            SOURCE_PORTFOLIO VARCHAR(255),
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            CREATED_BY VARCHAR(255) DEFAULT CURRENT_USER(),
            STATUS VARCHAR(50) DEFAULT 'DRAFT'
        )
    """).collect()
    
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.PORTFOLIO_SUGGESTION_HOLDINGS (
            HOLDING_ID NUMBER IDENTITY PRIMARY KEY,
            SUGGESTION_ID NUMBER NOT NULL,
            VARIANT_INDEX NUMBER NOT NULL,
            TICKER VARCHAR(20) NOT NULL,
            WEIGHT FLOAT NOT NULL,
            FOREIGN KEY (SUGGESTION_ID) REFERENCES {ai_schema}.PORTFOLIO_SUGGESTIONS(SUGGESTION_ID)
        )
    """).collect()
    
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.PORTFOLIO_SUGGESTION_BACKTEST (
            BACKTEST_ID NUMBER IDENTITY PRIMARY KEY,
            SUGGESTION_ID NUMBER NOT NULL,
            VARIANT_INDEX NUMBER NOT NULL,
            START_DATE DATE NOT NULL,
            END_DATE DATE NOT NULL,
            REBALANCE_FREQUENCY VARCHAR(20),
            INITIAL_INVESTMENT FLOAT,
            TOTAL_RETURN_PCT FLOAT,
            ANNUALIZED_RETURN_PCT FLOAT,
            ANNUALIZED_VOLATILITY_PCT FLOAT,
            FINAL_VALUE FLOAT,
            SHARPE_RATIO FLOAT,
            SORTINO_RATIO FLOAT,
            CALMAR_RATIO FLOAT,
            MAX_DRAWDOWN_PCT FLOAT,
            VAR_95_DAILY_PCT FLOAT,
            CVAR_95_DAILY_PCT FLOAT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            FOREIGN KEY (SUGGESTION_ID) REFERENCES {ai_schema}.PORTFOLIO_SUGGESTIONS(SUGGESTION_ID)
        )
    """).collect()
    
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.PORTFOLIO_SUGGESTION_BACKTEST_TIMESERIES (
            TIMESERIES_ID NUMBER IDENTITY PRIMARY KEY,
            BACKTEST_ID NUMBER NOT NULL,
            AS_OF_DATE DATE NOT NULL,
            PORTFOLIO_VALUE FLOAT,
            DAILY_RETURN FLOAT,
            DRAWDOWN FLOAT,
            FOREIGN KEY (BACKTEST_ID) REFERENCES {ai_schema}.PORTFOLIO_SUGGESTION_BACKTEST(BACKTEST_ID)
        )
    """).collect()
    
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.PORTFOLIO_SUGGESTION_SIMULATION (
            SIMULATION_ID NUMBER IDENTITY PRIMARY KEY,
            SUGGESTION_ID NUMBER NOT NULL,
            VARIANT_INDEX NUMBER NOT NULL,
            HORIZON_YEARS NUMBER,
            NUM_SIMULATIONS NUMBER,
            INITIAL_INVESTMENT FLOAT,
            MONTHLY_CONTRIBUTION FLOAT,
            EXPECTED_RETURN_OVERRIDE FLOAT,
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
            PROB_DOUBLE_PCT FLOAT,
            EXPECTED_ANNUAL_RETURN_PCT FLOAT,
            ANNUAL_VOLATILITY_PCT FLOAT,
            SHARPE_RATIO FLOAT,
            MAX_DRAWDOWN_90_PCTL_PCT FLOAT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            FOREIGN KEY (SUGGESTION_ID) REFERENCES {ai_schema}.PORTFOLIO_SUGGESTIONS(SUGGESTION_ID)
        )
    """).collect()
    
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {ai_schema}.PORTFOLIO_SUGGESTION_SIMULATION_PATHS (
            PATH_ID NUMBER IDENTITY PRIMARY KEY,
            SIMULATION_ID NUMBER NOT NULL,
            YEAR_INDEX NUMBER NOT NULL,
            PERCENTILE_5 FLOAT,
            PERCENTILE_25 FLOAT,
            MEDIAN FLOAT,
            PERCENTILE_75 FLOAT,
            PERCENTILE_95 FLOAT,
            FOREIGN KEY (SIMULATION_ID) REFERENCES {ai_schema}.PORTFOLIO_SUGGESTION_SIMULATION(SIMULATION_ID)
        )
    """).collect()
