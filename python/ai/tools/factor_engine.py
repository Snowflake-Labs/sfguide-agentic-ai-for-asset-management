"""
Factor Engine Tools for SAM Demo

Creates empty output tables for ML-based quant factor workflow.
The actual Feature Store setup, Fama-MacBeth UDTF, XGBoost factor
discovery, and portfolio optimisation are demonstrated interactively
in notebooks/factor_discovery.ipynb.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_info
from .ml_common import get_ml_schema_ref


def create_factor_tables(session: Session):
    ml_ref = get_ml_schema_ref()

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_FACTOR_SCORES (
        TICKER              VARCHAR(20) NOT NULL,
        MONTH_DATE          DATE NOT NULL,
        MOMENTUM_SCORE      FLOAT,
        VALUE_SCORE         FLOAT,
        QUALITY_SCORE       FLOAT,
        GROWTH_SCORE        FLOAT,
        SIZE_SCORE          FLOAT,
        VOLATILITY_SCORE    FLOAT,
        PROFITABILITY_SCORE FLOAT,
        LEVERAGE_SCORE       FLOAT,
        EARNINGS_REVISION   FLOAT,
        DIVIDEND_YIELD_SCORE FLOAT,
        BETA_SCORE          FLOAT,
        LIQUIDITY_SCORE     FLOAT
    )
    """).collect()
    log_detail("  Created: FACT_FACTOR_SCORES")

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_FACTOR_RETURNS (
        MONTH_DATE          DATE NOT NULL,
        MOMENTUM_RETURN     FLOAT,
        VALUE_RETURN        FLOAT,
        QUALITY_RETURN      FLOAT,
        GROWTH_RETURN       FLOAT,
        SIZE_RETURN         FLOAT,
        VOLATILITY_RETURN   FLOAT,
        MOMENTUM_TSTAT      FLOAT,
        VALUE_TSTAT         FLOAT,
        QUALITY_TSTAT       FLOAT,
        GROWTH_TSTAT        FLOAT,
        SIZE_TSTAT          FLOAT,
        VOLATILITY_TSTAT    FLOAT,
        R_SQUARED           FLOAT
    )
    """).collect()
    log_detail("  Created: FACT_FACTOR_RETURNS")

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_ML_FACTOR_PREDICTIONS (
        TICKER              VARCHAR(20) NOT NULL,
        MONTH_DATE          DATE NOT NULL,
        PREDICTED_RETURN    FLOAT,
        SHAP_TOP_FEATURE    VARCHAR(50),
        SHAP_TOP_VALUE      FLOAT,
        MODEL_VERSION       VARCHAR(50),
        SCORED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """).collect()
    log_detail("  Created: FACT_ML_FACTOR_PREDICTIONS")

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_OPTIMAL_PORTFOLIO (
        TICKER              VARCHAR(20) NOT NULL,
        MONTH_DATE          DATE NOT NULL,
        WEIGHT              FLOAT,
        EXPECTED_RETURN     FLOAT,
        RISK_CONTRIBUTION   FLOAT
    )
    """).collect()
    log_detail("  Created: FACT_OPTIMAL_PORTFOLIO")


def build_factor_scenario(session: Session):
    log_info("Building factor workflow scenario scaffolding...")
    create_factor_tables(session)
    log_info("Factor workflow scaffolding complete")
