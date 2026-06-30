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
