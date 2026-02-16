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

"""
Config Accessor Functions for Synthetic Data Generation

Helper functions to simplify access to deeply nested config in DATA_MODEL['synthetic_distributions'].
Provides fallback logic to '_default' keys when specific sector/country/strategy not found.

Usage:
    from config_accessors import get_sector_range, get_country_value, get_strategy_value, get_global_value
    
    # Get sector-specific factor range with _default fallback
    market_beta_range = get_sector_range('Information Technology', 'factors.Market')
    # Returns: (0.9, 1.4)
    
    # Get country-based ESG score range
    social_range = get_country_value('US', 'esg.S')
    # Returns: (50, 85)
"""

import config
from typing import Any, Optional


def get_sector_range(sector: str, path: str, default: Any = None) -> Any:
    """
    Get a range from sector config with fallback to _default.
    
    Args:
        sector: Sector name (e.g., 'Information Technology', 'Energy')
        path: Dot-separated path to value (e.g., 'factors.Market', 'esg.E')
        default: Value to return if path not found in sector or _default
    
    Returns:
        The config value (typically a tuple range) or default
    
    Example:
        get_sector_range('Information Technology', 'factors.Market')
        # Returns: (0.9, 1.4)
    """
    parts = path.split('.')
    sector_config = config.DATA_MODEL['synthetic_distributions']['by_sector']
    
    # Try specific sector first
    result = sector_config.get(sector, {})
    for part in parts:
        result = result.get(part) if isinstance(result, dict) else None
        if result is None:
            break
    
    if result is not None:
        return result
    
    # Fall back to _default
    result = sector_config.get('_default', {})
    for part in parts:
        result = result.get(part) if isinstance(result, dict) else None
        if result is None:
            break
    
    return result if result is not None else default


def get_country_group_for(country_code: str) -> str:
    """
    Get the country group name for a given country code.
    
    Args:
        country_code: ISO 2-letter country code (e.g., 'US', 'GB', 'DE')
    
    Returns:
        Country group name (e.g., 'developed_americas') or '_default'
    
    Example:
        get_country_group_for('US')
        # Returns: 'developed_americas'
    """
    groups = config.DATA_MODEL['synthetic_distributions']['country_groups']
    for group_name, group_data in groups.items():
        if group_name != '_default' and country_code in group_data.get('countries', []):
            return group_name
    return '_default'


def get_country_value(country_code: str, path: str, default: Any = None) -> Any:
    """
    Get a value from country group config.
    
    Args:
        country_code: ISO 2-letter country code
        path: Dot-separated path to value (e.g., 'esg.S', 'settlement_days')
        default: Value to return if path not found
    
    Returns:
        The config value or default
    
    Example:
        get_country_value('US', 'esg.S')
        # Returns: (50, 85)
    """
    group = get_country_group_for(country_code)
    groups = config.DATA_MODEL['synthetic_distributions']['country_groups']
    
    result = groups.get(group, groups.get('_default', {}))
    for part in path.split('.'):
        result = result.get(part) if isinstance(result, dict) else None
        if result is None:
            break
    
    return result if result is not None else default


def get_strategy_value(strategy: str, category: str, key: str, default: Any = None) -> Any:
    """
    Get strategy-based value with _default fallback.
    
    Args:
        strategy: Strategy name (e.g., 'Growth', 'ESG', 'Multi-Asset')
        category: Config category (e.g., 'liquidity_by_strategy', 'risk_limits_by_strategy')
        key: Value key within the category (e.g., 'rebalancing_days', 'tracking_error_limit')
        default: Value to return if not found
    
    Returns:
        The config value or default
    
    Example:
        get_strategy_value('Growth', 'liquidity_by_strategy', 'rebalancing_days')
        # Returns: 90
    """
    global_config = config.DATA_MODEL['synthetic_distributions']['global']
    category_config = global_config.get(category, {})
    
    strategy_data = category_config.get(strategy, category_config.get('_default', {}))
    return strategy_data.get(key, default)


def get_global_value(path: str, default: Any = None) -> Any:
    """
    Get a global config value.
    
    Args:
        path: Dot-separated path to value (e.g., 'tax.long_term_rate', 'factor_r_squared.Market')
        default: Value to return if path not found
    
    Returns:
        The config value or default
    
    Example:
        get_global_value('tax.long_term_rate')
        # Returns: 0.20
    """
    result = config.DATA_MODEL['synthetic_distributions']['global']
    for part in path.split('.'):
        result = result.get(part) if isinstance(result, dict) else None
        if result is None:
            break
    return result if result is not None else default


def get_all_configured_sectors() -> list:
    """
    Get list of all explicitly configured sectors (excluding _default).
    
    Returns:
        List of sector names
    """
    sector_config = config.DATA_MODEL['synthetic_distributions']['by_sector']
    return [s for s in sector_config.keys() if s != '_default']


def get_all_country_groups() -> dict:
    """
    Get all country groups with their member countries.
    
    Returns:
        Dict mapping group name to list of countries
    """
    groups = config.DATA_MODEL['synthetic_distributions']['country_groups']
    return {
        group_name: group_data.get('countries', [])
        for group_name, group_data in groups.items()
        if group_name != '_default'
    }

