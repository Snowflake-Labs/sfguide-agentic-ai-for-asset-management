"""
Regime Detection Tools for SAM Demo

Creates empty prediction tables for ML-based market regime detection.
The actual Feature Store setup, model training, and scoring are
demonstrated interactively in notebooks/market_regime_detection.ipynb.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_info
from .ml_common import get_ml_schema_ref


def create_regime_prediction_table(session: Session):
    ml_ref = get_ml_schema_ref()

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_REGIME_PREDICTIONS (
        DATE                DATE NOT NULL,
        REGIME_LABEL        VARCHAR(20),
        REGIME_PROBABILITY  FLOAT,
        CLUSTER_0_PROB      FLOAT,
        CLUSTER_1_PROB      FLOAT,
        CLUSTER_2_PROB      FLOAT,
        VIX_LEVEL           FLOAT,
        MOMENTUM_20D        FLOAT,
        REALISED_VOL_20D    FLOAT,
        MODEL_VERSION       VARCHAR(50),
        SCORED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """).collect()
    log_detail("  Created: FACT_REGIME_PREDICTIONS")


def build_regime_scenario(session: Session):
    log_info("Building regime detection scenario scaffolding...")
    create_regime_prediction_table(session)
    log_info("Regime detection scaffolding complete")
