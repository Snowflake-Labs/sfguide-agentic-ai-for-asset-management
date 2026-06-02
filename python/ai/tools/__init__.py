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
Tools Package for SAM Demo

This package contains modular tool creation functions extracted from builder.py.

Modules:
- pdf_report: PDF report generation with SAM branding
- ma_simulation: M&A financial impact simulation
- monte_carlo: Monte Carlo simulation with block bootstrapping
- backtest: Historical portfolio backtesting
- attribution: Brinson-Fachler attribution and stress testing
- streamlit_deploy: Streamlit Container Runtime deployment
- suggestion_tables: Portfolio suggestion storage tables
"""

from .pdf_report import create_pdf_report_stage, create_pdf_report_tool
from .ma_simulation import create_ma_simulation_tool
from .monte_carlo import create_monte_carlo_udfs, create_monte_carlo_tool
from .backtest import create_backtest_tool
from .attribution import create_attribution_tool, create_stress_backtest_tool, create_scenario_sensitivity_tool
from .streamlit_deploy import (
    validate_streamlit_prerequisites,
    create_container_runtime_resources,
    deploy_streamlit_app
)
from .suggestion_tables import create_suggestion_tables
from .tool_run_tables import create_tool_run_tables
from .data_origin import create_data_origin_tool
from .ml_common import (
    get_ml_schema_ref,
    get_ml_date_range,
    ensure_ml_schema,
    get_feature_store,
    register_entity,
    register_feature_view,
    log_model,
    get_model_version,
    get_experiment_tracker,
    create_xgboost_callback,
    create_model_monitor,
    get_model_inference_sql,
    validate_ml_date_filter,
    resolve_ml_build_order,
)
from .regime_detection import build_regime_scenario
from .credit_risk import build_credit_risk_scenario
from .factor_engine import build_factor_scenario

__all__ = [
    'create_pdf_report_stage',
    'create_pdf_report_tool',
    'create_ma_simulation_tool',
    'create_monte_carlo_udfs',
    'create_monte_carlo_tool',
    'create_backtest_tool',
    'create_attribution_tool',
    'create_stress_backtest_tool',
    'create_scenario_sensitivity_tool',
    'validate_streamlit_prerequisites',
    'create_container_runtime_resources',
    'deploy_streamlit_app',
    'create_suggestion_tables',
    'create_tool_run_tables',
    'create_data_origin_tool',
    'get_ml_schema_ref',
    'get_ml_date_range',
    'ensure_ml_schema',
    'get_feature_store',
    'register_entity',
    'register_feature_view',
    'log_model',
    'get_model_version',
    'get_experiment_tracker',
    'create_xgboost_callback',
    'create_model_monitor',
    'get_model_inference_sql',
    'validate_ml_date_filter',
    'resolve_ml_build_order',
    'build_regime_scenario',
    'build_credit_risk_scenario',
    'build_factor_scenario',
]
