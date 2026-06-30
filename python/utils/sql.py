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
SQL generation helpers and utilities.

Provides:
- safe_sql_tuple: Convert list to SQL-safe tuple
- sql_uniform: Generate UNIFORM SQL expression
- SQL CASE builders for sector, country, grade, strategy expressions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from .config_helpers import get_sector_range, get_country_value, get_global_value


def safe_sql_tuple(items: list, default_value: str = "'__NONE__'") -> str:
    """
    Convert a list to a SQL-safe tuple string with proper quoting.
    Returns a tuple with a dummy value if the list is empty to avoid SQL syntax errors.
    """
    if not items or len(items) == 0:
        return f"({default_value})"
    
    quoted_items = [f"'{item}'" for item in items]
    return f"({', '.join(quoted_items)})"


def sql_uniform(min_val, max_val) -> str:
    """Generate UNIFORM(min, max, RANDOM()) SQL."""
    return f"UNIFORM({min_val}, {max_val}, RANDOM())"


def build_sector_case_sql(column: str, path: str, sectors: list = None) -> str:
    """Build SQL CASE WHEN for sector-based UNIFORM ranges."""
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
    """Build SQL CASE WHEN for country-group-based UNIFORM ranges."""
    groups = config.DATA_MODEL['synthetic_distributions']['country_groups']
    
    clauses = []
    for group_name, group_data in groups.items():
        if group_name == '_default':
            continue
        countries = group_data.get('countries', [])
        if not countries:
            continue
        
        result = group_data
        for part in path.split('.'):
            result = result.get(part) if isinstance(result, dict) else None
            if result is None:
                break
        
        if result:
            countries_sql = ', '.join(f"'{c}'" for c in countries)
            clauses.append(f"WHEN {column} IN ({countries_sql}) THEN {sql_uniform(*result)}")
    
    default_group = groups.get('_default', {})
    default_range = default_group
    for part in path.split('.'):
        default_range = default_range.get(part) if isinstance(default_range, dict) else None
        if default_range is None:
            break
    
    default_sql = sql_uniform(*default_range) if default_range else 'NULL'
    
    return f"CASE {' '.join(clauses)} ELSE {default_sql} END"


def build_country_settlement_case_sql(column: str) -> str:
    """Build SQL CASE WHEN for country-based settlement days."""
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
    """Build SQL CASE for ESG grade assignment from score."""
    thresholds = config.COMPLIANCE_RULES['esg']['grade_thresholds']
    default_grade = config.COMPLIANCE_RULES['esg']['default_grade']
    
    clauses = [f"WHEN {score_expr} >= {threshold} THEN '{grade}'" 
               for threshold, grade in thresholds]
    
    return f"CASE {' '.join(clauses)} ELSE '{default_grade}' END"


def build_overall_esg_sql(e_expr: str, s_expr: str, g_expr: str) -> str:
    """Build SQL for weighted overall ESG score."""
    weights = config.COMPLIANCE_RULES['esg'].get('overall_weights', {'E': 1, 'S': 1, 'G': 1})
    total_weight = sum(weights.values())
    
    return f"({weights['E']}*{e_expr} + {weights['S']}*{s_expr} + {weights['G']}*{g_expr}) / {total_weight}"


def build_strategy_case_sql(strategy_column: str, category: str, key: str) -> str:
    """Build SQL CASE for strategy-based values."""
    global_config = config.DATA_MODEL['synthetic_distributions']['global']
    category_config = global_config.get(category, {})
    
    clauses = []
    for strategy, data in category_config.items():
        if strategy == '_default':
            continue
        val = data.get(key)
        if val is not None:
            if isinstance(val, (tuple, list)):
                clauses.append(f"WHEN {strategy_column} = '{strategy}' THEN {sql_uniform(*val)}")
            else:
                clauses.append(f"WHEN {strategy_column} = '{strategy}' THEN {val}")
    
    default_data = category_config.get('_default', {})
    default_val = default_data.get(key)
    if default_val is not None:
        default_sql = sql_uniform(*default_val) if isinstance(default_val, (tuple, list)) else str(default_val)
    else:
        default_sql = 'NULL'
    
    return f"CASE {' '.join(clauses)} ELSE {default_sql} END"


def build_global_uniform_sql(path: str) -> str:
    """Build SQL UNIFORM from a global config range."""
    range_val = get_global_value(path)
    if range_val and isinstance(range_val, (tuple, list)):
        return sql_uniform(*range_val)
    return 'NULL'


def build_factor_case_sql(column: str, factor_name: str) -> str:
    """Build SQL CASE for a specific factor, checking both sector and global config."""
    sector_config = config.DATA_MODEL['synthetic_distributions']['by_sector']
    has_sector_config = any(
        sector_data.get('factors', {}).get(factor_name) is not None
        for sector, sector_data in sector_config.items()
        if sector != '_default'
    )
    
    if has_sector_config:
        return build_sector_case_sql(column, f'factors.{factor_name}')
    
    global_range = get_global_value(f'factor_globals.{factor_name}')
    if global_range:
        return sql_uniform(*global_range)
    
    default_range = get_sector_range('_default', f'factors.{factor_name}')
    if default_range:
        return sql_uniform(*default_range)
    
    return 'NULL'


def get_factor_r_squared(factor_name: str) -> float:
    """Get R² value for a factor from config."""
    return get_global_value(f'factor_r_squared.{factor_name}', 0.5)
