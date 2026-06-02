"""
Credit Risk Tools for SAM Demo

Creates empty scoring tables for ML-based credit risk prediction.
The actual Feature Store setup, model training (XGBoost), SHAP
explainability, and scoring are demonstrated interactively in
notebooks/credit_risk_model.ipynb.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_info
from .ml_common import get_ml_schema_ref


def create_credit_risk_tables(session: Session):
    ml_ref = get_ml_schema_ref()

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_CREDIT_RISK_SCORES (
        BORROWER_ID         INT NOT NULL,
        QUARTER_DATE        DATE NOT NULL,
        PD_SCORE            FLOAT,
        RISK_RATING         VARCHAR(20),
        SHAP_TOP_FEATURES   VARIANT,
        MODEL_VERSION       VARCHAR(50),
        SCORED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """).collect()
    log_detail("  Created: FACT_CREDIT_RISK_SCORES")

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_CREDIT_SHAP_EXPLANATIONS (
        BORROWER_ID         INT NOT NULL,
        QUARTER_DATE        DATE NOT NULL,
        FEATURE_NAME        VARCHAR(100),
        SHAP_VALUE          FLOAT,
        FEATURE_VALUE       FLOAT
    )
    """).collect()
    log_detail("  Created: FACT_CREDIT_SHAP_EXPLANATIONS")


def build_credit_risk_scenario(session: Session):
    log_info("Building credit risk scenario scaffolding...")
    create_credit_risk_tables(session)
    log_info("Credit risk scaffolding complete")
