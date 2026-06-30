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
Config accessor functions for synthetic data generation and scenario management.

Provides fallback logic to '_default' keys when specific sector/country/strategy not found.
"""

from typing import Any, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_sector_range(sector: str, path: str, default: Any = None) -> Any:
    """
    Get a range from sector config with fallback to _default.
    
    Args:
        sector: Sector name (e.g., 'Information Technology', 'Energy')
        path: Dot-separated path to value (e.g., 'factors.Market', 'esg.E')
        default: Value to return if path not found in sector or _default
    
    Returns:
        The config value (typically a tuple range) or default
    """
    parts = path.split('.')
    sector_config = config.DATA_MODEL['synthetic_distributions']['by_sector']
    
    result = sector_config.get(sector, {})
    for part in parts:
        result = result.get(part) if isinstance(result, dict) else None
        if result is None:
            break
    
    if result is not None:
        return result
    
    result = sector_config.get('_default', {})
    for part in parts:
        result = result.get(part) if isinstance(result, dict) else None
        if result is None:
            break
    
    return result if result is not None else default


def get_country_group_for(country_code: str) -> str:
    """Get the country group name for a given country code."""
    groups = config.DATA_MODEL['synthetic_distributions']['country_groups']
    for group_name, group_data in groups.items():
        if group_name != '_default' and country_code in group_data.get('countries', []):
            return group_name
    return '_default'


def get_country_value(country_code: str, path: str, default: Any = None) -> Any:
    """Get a value from country group config."""
    group = get_country_group_for(country_code)
    groups = config.DATA_MODEL['synthetic_distributions']['country_groups']
    
    result = groups.get(group, groups.get('_default', {}))
    for part in path.split('.'):
        result = result.get(part) if isinstance(result, dict) else None
        if result is None:
            break
    
    return result if result is not None else default


def get_strategy_value(strategy: str, category: str, key: str, default: Any = None) -> Any:
    """Get strategy-based value with _default fallback."""
    global_config = config.DATA_MODEL['synthetic_distributions']['global']
    category_config = global_config.get(category, {})
    
    strategy_data = category_config.get(strategy, category_config.get('_default', {}))
    return strategy_data.get(key, default)


def get_global_value(path: str, default: Any = None) -> Any:
    """Get a global config value."""
    result = config.DATA_MODEL['synthetic_distributions']['global']
    for part in path.split('.'):
        result = result.get(part) if isinstance(result, dict) else None
        if result is None:
            break
    return result if result is not None else default


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
