# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# =============================================================================
# SCENARIO UTILITIES - Scenario-related helper functions
# =============================================================================
"""
Helper functions for working with demo scenarios.
Centralizes logic that was previously duplicated across modules.
"""

from typing import List
import config


def get_required_document_types(scenarios: List[str]) -> List[str]:
    """
    Get unique list of document types required for the specified scenarios.
    
    Args:
        scenarios: List of scenario names (e.g., ['portfolio_copilot', 'research_copilot'])
    
    Returns:
        List of unique document type names required by those scenarios
    """
    required_types = set()
    for scenario in scenarios:
        if scenario in config.SCENARIO_DATA_REQUIREMENTS:
            required_types.update(config.SCENARIO_DATA_REQUIREMENTS[scenario])
    return list(required_types)

