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
Data generation modules for SAM Demo.

Modules:
    automation: Weekly refresh Code Bundle and task installation
    cadence: Document cadence ledger and publication scheduling
    coverage_universe: Analyst coverage universe construction
    incremental: Incremental refresh helpers and watermarks
    market_data: Real market data from SEC and Nasdaq
    middle_office: Middle office operations data (reconciliation, SSI)
    pipelines: Snowflake Task orchestration for document processing
    private_markets: Private equity and private credit data
    recommendations: Broker ratings, price targets and recommendations
    structured: Dimension and fact tables (DIM_*, FACT_*)
    transcripts: Real earnings call transcript processing
    unstructured: Document generation orchestration
    weekly_refresh: Weekly demo data advancement
"""

from . import automation
from . import cadence
from . import coverage_universe
from . import incremental
from . import market_data
from . import middle_office
from . import pipelines
from . import private_markets
from . import recommendations
from . import structured
from . import transcripts
from . import unstructured
from . import weekly_refresh

__all__ = [
    'automation',
    'cadence',
    'coverage_universe',
    'incremental',
    'market_data',
    'middle_office',
    'pipelines',
    'private_markets',
    'recommendations',
    'structured',
    'transcripts',
    'unstructured',
    'weekly_refresh',
]
