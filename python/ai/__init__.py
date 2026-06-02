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
AI component builders for SAM Demo.

Modules:
    builder: Main orchestrator (build_all function)
    agents: Snowflake Intelligence agent creation
    semantic_views: Cortex Analyst semantic view creation
    cortex_search: Cortex Search service creation
"""

from . import builder
from . import agents
from . import semantic_views
from . import cortex_search

__all__ = [
    'builder',
    'agents',
    'semantic_views',
    'cortex_search',
]
