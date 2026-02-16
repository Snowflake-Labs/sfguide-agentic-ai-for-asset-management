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
SQL CASE/UNIFORM Expression Builders for Config-Driven Data Generation

All functions return SQL strings that can be embedded in f-strings for
dynamic SQL generation in generate_structured.py.

Usage:
    from sql_case_builders import (
        sql_uniform,
        build_sector_case_sql,
        build_country_group_case_sql,
        build_grade_case_sql,
        build_overall_esg_sql,
        build_strategy_case_sql
    )
    
    # Build sector-based CASE WHEN for ESG Environmental scores
    e_score_sql = build_sector_case_sql('es.SIC_DESCRIPTION', 'esg.E')
    # Returns: "CASE WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(60, 95, RANDOM()) ... END"
"""

import config
from config_accessors import get_sector_range, get_country_value, get_global_value


def sql_uniform(min_val, max_val) -> str:
    """
    Generate UNIFORM(min, max, RANDOM()) SQL.
    
    Args:
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        SQL UNIFORM expression
    
    >>> sql_uniform(0.5, 1.5)
    'UNIFORM(0.5, 1.5, RANDOM())'
    >>> sql_uniform(60, 95)
    'UNIFORM(60, 95, RANDOM())'
    """
    return f"UNIFORM({min_val}, {max_val}, RANDOM())"


def build_sector_case_sql(column: str, path: str, sectors: list = None) -> str:
    """
    Build SQL CASE WHEN for sector-based UNIFORM ranges.
    
    Args:
        column: SQL column name (e.g., 'es.SIC_DESCRIPTION')
        path: Config path (e.g., 'factors.Market', 'esg.E')
        sectors: List of sectors to include (None = all configured sectors)
    
    Returns:
        SQL CASE expression
    
    Example:
        build_sector_case_sql('es.SIC_DESCRIPTION', 'esg.E')
        # Returns: "CASE WHEN es.SIC_DESCRIPTION = 'Information Technology' THEN UNIFORM(60, 95, RANDOM()) 
        #          WHEN es.SIC_DESCRIPTION = 'Utilities' THEN UNIFORM(20, 60, RANDOM()) ... ELSE ... END"
    """
    sector_config = config.DATA_MODEL['synthetic_distributions']['by_sector']
    if sectors is None:
        sectors = [s for s in sector_config.keys() if s != '_default']
    
    clauses = []
    for sector in sectors:
        range_val = get_sector_range(sector, path)
        if range_val:
            clauses.append(f"WHEN {column} = '{sector}' THEN {sql_uniform(*range_val)}")
    
    default_range = get_sector_range('_default', path)
    default_sql = sql_uniform(*default_range) if default_range else 'NULL'
    
    return f"CASE {' '.join(clauses)} ELSE {default_sql} END"


def build_country_group_case_sql(column: str, path: str) -> str:
    """
    Build SQL CASE WHEN for country-group-based UNIFORM ranges.
    
    Args:
        column: SQL column name (e.g., 'es.CountryOfIncorporation')
        path: Config path within country group (e.g., 'esg.S', 'esg.G')
    
    Returns:
        SQL CASE expression
    
    Example:
        build_country_group_case_sql('es.CountryOfIncorporation', 'esg.S')
        # Returns: "CASE WHEN es.CountryOfIncorporation IN ('US', 'CA') THEN UNIFORM(50, 85, RANDOM()) 
        #          WHEN ... IN ('GB', 'DE', 'FR', 'SE', 'DK') THEN ... ELSE ... END"
    """
    groups = config.DATA_MODEL['synthetic_distributions']['country_groups']
    
    clauses = []
    for group_name, group_data in groups.items():
        if group_name == '_default':
            continue
        countries = group_data.get('countries', [])
        if not countries:
            continue
        
        # Navigate to the value using the path
        result = group_data
        for part in path.split('.'):
            result = result.get(part) if isinstance(result, dict) else None
            if result is None:
                break
        
        if result:
            countries_sql = ', '.join(f"'{c}'" for c in countries)
            clauses.append(f"WHEN {column} IN ({countries_sql}) THEN {sql_uniform(*result)}")
    
    # Get default range
    default_group = groups.get('_default', {})
    default_range = default_group
    for part in path.split('.'):
        default_range = default_range.get(part) if isinstance(default_range, dict) else None
        if default_range is None:
            break
    
    default_sql = sql_uniform(*default_range) if default_range else 'NULL'
    
    return f"CASE {' '.join(clauses)} ELSE {default_sql} END"


def build_country_settlement_case_sql(column: str) -> str:
    """
    Build SQL CASE WHEN for country-based settlement days.
    
    Args:
        column: SQL column name (e.g., 'es.CountryOfIncorporation')
    
    Returns:
        SQL CASE expression for settlement days (integer, not UNIFORM)
    """
    groups = config.DATA_MODEL['synthetic_distributions']['country_groups']
    
    clauses = []
    for group_name, group_data in groups.items():
        if group_name == '_default':
            continue
        countries = group_data.get('countries', [])
        settlement_days = group_data.get('settlement_days')
        if countries and settlement_days is not None:
            countries_sql = ', '.join(f"'{c}'" for c in countries)
            clauses.append(f"WHEN {column} IN ({countries_sql}) THEN {settlement_days}")
    
    default_days = groups.get('_default', {}).get('settlement_days', 3)
    
    return f"CASE {' '.join(clauses)} ELSE {default_days} END"


def build_grade_case_sql(score_expr: str) -> str:
    """
    Build SQL CASE for ESG grade assignment from score.
    
    Args:
        score_expr: SQL expression for the score (e.g., 'E_SCORE', '(E_SCORE + S_SCORE + G_SCORE)/3')
    
    Returns:
        SQL CASE expression returning grade string
    
    Example:
        build_grade_case_sql('E_SCORE')
        # Returns: "CASE WHEN E_SCORE >= 86 THEN 'AAA' WHEN E_SCORE >= 71 THEN 'AA' ... ELSE 'CCC' END"
    """
    thresholds = config.COMPLIANCE_RULES['esg']['grade_thresholds']
    default_grade = config.COMPLIANCE_RULES['esg']['default_grade']
    
    clauses = [f"WHEN {score_expr} >= {threshold} THEN '{grade}'" 
               for threshold, grade in thresholds]
    
    return f"CASE {' '.join(clauses)} ELSE '{default_grade}' END"


def build_overall_esg_sql(e_expr: str, s_expr: str, g_expr: str) -> str:
    """
    Build SQL for weighted overall ESG score.
    
    Args:
        e_expr: SQL expression for E score
        s_expr: SQL expression for S score
        g_expr: SQL expression for G score
    
    Returns:
        SQL expression for weighted average
    
    Example:
        build_overall_esg_sql('E_SCORE', 'S_SCORE', 'G_SCORE')
        # Returns: "(1.0*E_SCORE + 1.0*S_SCORE + 1.0*G_SCORE) / 3.0"
    """
    weights = config.COMPLIANCE_RULES['esg'].get('overall_weights', {'E': 1, 'S': 1, 'G': 1})
    total_weight = sum(weights.values())
    
    return f"({weights['E']}*{e_expr} + {weights['S']}*{s_expr} + {weights['G']}*{g_expr}) / {total_weight}"


def build_strategy_case_sql(strategy_column: str, category: str, key: str) -> str:
    """
    Build SQL CASE for strategy-based values.
    
    Args:
        strategy_column: SQL column (e.g., 'p.Strategy')
        category: Config category (e.g., 'liquidity_by_strategy', 'risk_limits_by_strategy')
        key: Value key within the category (e.g., 'rebalancing_days', 'tracking_error_limit')
    
    Returns:
        SQL CASE expression (UNIFORM for tuple ranges, literal for scalar values)
    
    Example:
        build_strategy_case_sql('p.Strategy', 'liquidity_by_strategy', 'rebalancing_days')
        # Returns: "CASE WHEN p.Strategy = 'Growth' THEN 90 WHEN ... ELSE 60 END"
        
        build_strategy_case_sql('p.Strategy', 'risk_limits_by_strategy', 'tracking_error_limit')
        # Returns: "CASE WHEN p.Strategy = 'Growth' THEN UNIFORM(4.0, 6.0, RANDOM()) ... END"
    """
    global_config = config.DATA_MODEL['synthetic_distributions']['global']
    category_config = global_config.get(category, {})
    
    clauses = []
    for strategy, data in category_config.items():
        if strategy == '_default':
            continue
        val = data.get(key)
        if val is not None:
            if isinstance(val, tuple):
                clauses.append(f"WHEN {strategy_column} = '{strategy}' THEN {sql_uniform(*val)}")
            else:
                clauses.append(f"WHEN {strategy_column} = '{strategy}' THEN {val}")
    
    default_data = category_config.get('_default', {})
    default_val = default_data.get(key)
    if default_val is not None:
        default_sql = sql_uniform(*default_val) if isinstance(default_val, tuple) else str(default_val)
    else:
        default_sql = 'NULL'
    
    return f"CASE {' '.join(clauses)} ELSE {default_sql} END"


def build_global_uniform_sql(path: str) -> str:
    """
    Build SQL UNIFORM from a global config range.
    
    Args:
        path: Dot-separated path to range (e.g., 'transaction_cost_globals.commission_bps')
    
    Returns:
        SQL UNIFORM expression
    
    Example:
        build_global_uniform_sql('transaction_cost_globals.commission_bps')
        # Returns: "UNIFORM(1, 3, RANDOM())"
    """
    range_val = get_global_value(path)
    if range_val and isinstance(range_val, tuple):
        return sql_uniform(*range_val)
    return 'NULL'


# =============================================================================
# Convenience functions for common patterns
# =============================================================================

def build_factor_case_sql(column: str, factor_name: str) -> str:
    """
    Build SQL CASE for a specific factor, checking both sector and global config.
    
    Args:
        column: SQL column for sector (e.g., 'es.SIC_DESCRIPTION')
        factor_name: Factor name (e.g., 'Market', 'Size', 'Value')
    
    Returns:
        SQL expression (CASE for sector-based, UNIFORM for global-only)
    """
    # Check if this factor has sector-specific ranges
    sector_config = config.DATA_MODEL['synthetic_distributions']['by_sector']
    has_sector_config = any(
        sector_data.get('factors', {}).get(factor_name) is not None
        for sector, sector_data in sector_config.items()
        if sector != '_default'
    )
    
    if has_sector_config:
        return build_sector_case_sql(column, f'factors.{factor_name}')
    
    # Fall back to global factor range
    global_range = get_global_value(f'factor_globals.{factor_name}')
    if global_range:
        return sql_uniform(*global_range)
    
    # Try _default sector config
    default_range = get_sector_range('_default', f'factors.{factor_name}')
    if default_range:
        return sql_uniform(*default_range)
    
    return 'NULL'


def get_factor_r_squared(factor_name: str) -> float:
    """
    Get R² value for a factor from config.
    
    Args:
        factor_name: Factor name (e.g., 'Market', 'Size')
    
    Returns:
        R² value (float) or 0.5 as default
    """
    return get_global_value(f'factor_r_squared.{factor_name}', 0.5)

