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
Semantic Views Builder for SAM Demo

Creates Cortex Analyst semantic views from YAML template files stored in
semantic_view_definitions/. Uses SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML for
creation and template variable substitution for config values.

Views are resolved from config.SCENARIOS — each scenario declares its required_views.
Build order guarantee: all required tables are created before this runs.
"""

from snowflake.snowpark import Session
from typing import List
import config
from .yaml_loader import create_semantic_view, get_all_view_names
from utils.logging import log_detail, log_warning, log_error, log_step

CRITICAL_VIEWS = {'SAM_PORTFOLIO_VIEW'}


def create_semantic_views(session: Session, scenarios: List[str] = None):
    """Create all semantic views for the given scenarios."""
    if not scenarios:
        return

    views = config.get_required_views(scenarios)
    if not views:
        return

    log_step(f"Creating {len(views)} semantic views from YAML definitions")

    for view_name in views:
        try:
            msg = create_semantic_view(session, view_name)
            log_detail(f"  OK  {view_name}")
        except Exception as e:
            if view_name in CRITICAL_VIEWS:
                log_error(f" Failed to create {view_name}: {e}")
                raise
            else:
                log_warning(f"  Warning: Could not create {view_name}: {e}")


def create_ml_semantic_views(session: Session, scenarios: List[str] = None):
    """No-op — ML views are now created in the main create_semantic_views pass."""
    pass
