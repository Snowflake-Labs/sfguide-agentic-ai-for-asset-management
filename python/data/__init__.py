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
    structured: Dimension and fact tables (DIM_*, FACT_*)
    market_data: Real market data from SEC and Nasdaq
    unstructured: Document generation orchestration
    transcripts: Real earnings call transcript processing
    pipelines: Snowflake Task orchestration for document processing
"""

from . import structured
from . import market_data
from . import unstructured
from . import transcripts
from . import pipelines

__all__ = [
    'structured',
    'market_data',
    'unstructured',
    'transcripts',
    'pipelines',
]
