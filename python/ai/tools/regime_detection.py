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
