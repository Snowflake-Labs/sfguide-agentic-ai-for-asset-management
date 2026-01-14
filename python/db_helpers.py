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
# DATABASE HELPERS - Date utilities and table access verification
# =============================================================================
"""
Helper functions for managing date anchors and verifying table access.
"""

import config
from logging_utils import log_detail, log_warning


# =============================================================================
# DATE RANGE HELPERS (anchor all data to stock price availability)
# =============================================================================

_MAX_PRICE_DATE = None


def get_max_price_date(session) -> str:
    """
    Get the latest date available in FACT_STOCK_PRICES.
    
    This date serves as the anchor point for all data generation:
    - Historical data (positions, transactions, benchmarks) uses this as upper bound
    - Future data (estimates, forecasts) uses this as the reference "today"
    
    Must be called AFTER FACT_STOCK_PRICES has been built.
    
    Returns:
        Date string in 'YYYY-MM-DD' format
    """
    global _MAX_PRICE_DATE
    if _MAX_PRICE_DATE is None:
        result = session.sql(f"""
            SELECT MAX(PRICE_DATE) as max_date 
            FROM {config.DATABASE['name']}.MARKET_DATA.FACT_STOCK_PRICES
        """).collect()
        _MAX_PRICE_DATE = result[0]['MAX_DATE']
        if _MAX_PRICE_DATE:
            log_detail(f"  Max price date anchor: {_MAX_PRICE_DATE}")
    return _MAX_PRICE_DATE


def reset_max_price_date():
    """Reset the cached max price date (call before rebuilding FACT_STOCK_PRICES)."""
    global _MAX_PRICE_DATE
    _MAX_PRICE_DATE = None


# =============================================================================
# TABLE ACCESS VERIFICATION
# =============================================================================

def verify_table_access(session, database: str, schema: str, table: str) -> tuple:
    """
    Check if a table is accessible.
    
    Args:
        session: Active Snowpark session
        database: Database name
        schema: Schema name
        table: Table name
    
    Returns:
        Tuple of (success: bool, error_message: str | None)
    """
    try:
        session.sql(f"SELECT 1 FROM {database}.{schema}.{table} LIMIT 1").collect()
        return (True, None)
    except Exception as e:
        error_msg = f"Cannot access {database}.{schema}.{table}: {e}"
        log_warning(error_msg)
        return (False, error_msg)
