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
# SQL UTILITIES - SQL generation helpers
# =============================================================================
"""
Helper functions for generating SQL fragments and queries.
"""


def safe_sql_tuple(items: list, default_value: str = "'__NONE__'") -> str:
    """
    Convert a list to a SQL-safe tuple string with proper quoting.
    Returns a tuple with a dummy value if the list is empty to avoid SQL syntax errors.
    
    Args:
        items: List of items to convert to tuple
        default_value: Default value to use if list is empty (should be a SQL literal)
    
    Returns:
        String representation of tuple for SQL IN clause
    """
    if not items or len(items) == 0:
        return f"({default_value})"
    
    # Format items with SQL quotes
    quoted_items = [f"'{item}'" for item in items]
    # SQL doesn't use trailing comma for single items (unlike Python)
    return f"({', '.join(quoted_items)})"
