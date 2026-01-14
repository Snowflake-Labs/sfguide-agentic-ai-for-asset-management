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
# DEMO HELPERS - Company, Portfolio, and Client utilities
# =============================================================================
"""
Helper functions for working with demo companies, portfolios, and clients.
These functions access config data structures to provide convenient lookups.
"""

import config


def get_demo_company_tickers(tier: str = None) -> list:
    """Get list of tickers, optionally filtered by tier."""
    if tier:
        return [k for k, v in config.DEMO_COMPANIES.items() if v.get('tier') == tier]
    return list(config.DEMO_COMPANIES.keys())


def get_demo_company_ciks() -> list:
    """Get list of CIKs for all demo companies."""
    return [v['cik'] for v in config.DEMO_COMPANIES.values() if v.get('cik')]


def get_demo_company_by_ticker(ticker: str) -> dict:
    """Get company info by ticker."""
    return config.DEMO_COMPANIES.get(ticker, {})


def get_demo_company_priority_sql() -> str:
    """
    Generate SQL CASE statement for demo company priorities from DEMO_COMPANIES config.
    Returns SQL fragment that maps Ticker to priority value based on tier.
    
    Tiers: core=1, major=2, additional=3
    """
    tier_to_priority = {'core': 1, 'major': 2, 'additional': 3}
    case_when_lines = []
    
    # Sort by tier priority to ensure consistent ordering
    sorted_companies = sorted(
        config.DEMO_COMPANIES.items(), 
        key=lambda x: tier_to_priority.get(x[1].get('tier', 'additional'), 3)
    )
    
    for ticker, company_data in sorted_companies:
        priority = tier_to_priority.get(company_data.get('tier', 'additional'), 3)
        case_when_lines.append(f"WHEN s.Ticker = '{ticker}' THEN {priority}")
    
    if not case_when_lines:
        return "WHEN 1=0 THEN 999"  # Fallback if no demo companies
    
    return " ".join(case_when_lines)


def is_demo_portfolio(portfolio_name: str) -> bool:
    """Check if a portfolio is configured as a demo portfolio."""
    return portfolio_name in config.PORTFOLIOS and config.PORTFOLIOS[portfolio_name].get('is_demo_portfolio', False)


def get_demo_portfolio_names() -> list:
    """Get list of demo portfolio names only."""
    return [name for name, cfg in config.PORTFOLIOS.items() if cfg.get('is_demo_portfolio', False)]


def get_demo_order_tickers() -> list:
    """
    Get list of tickers with demo_order defined (for portfolio prioritization).
    Returns tickers sorted by demo_order.
    """
    ordered = [
        (ticker, data.get('demo_order'))
        for ticker, data in config.DEMO_COMPANIES.items()
        if data.get('demo_order') is not None
    ]
    return [ticker for ticker, _ in sorted(ordered, key=lambda x: x[1])]


def get_large_position_tickers() -> list:
    """Get list of tickers with position_size='large' (for larger portfolio weights)."""
    return [
        ticker for ticker, data in config.DEMO_COMPANIES.items()
        if data.get('position_size') == 'large'
    ]


def get_demo_client_names() -> list:
    """Get list of demo client names for data generation."""
    return [client['client_name'] for client in config.DEMO_CLIENTS.values()]


def get_demo_client_by_type(client_type: str) -> dict:
    """Get a demo client by type (Pension, Endowment, Foundation, Insurance, Corporate, Family Office)."""
    for client in config.DEMO_CLIENTS.values():
        if client['client_type'] == client_type:
            return client
    return None


def get_demo_clients_by_category(category: str) -> list:
    """
    Get demo clients filtered by category (standard/at_risk/new).
    Returns list sorted by priority.
    """
    return sorted(
        [c for c in config.DEMO_CLIENTS.values() if c.get('category') == category],
        key=lambda x: x['priority']
    )


def get_demo_clients_sorted() -> list:
    """Get standard demo clients sorted by priority."""
    return get_demo_clients_by_category('standard')


def get_at_risk_demo_clients() -> list:
    """Get at-risk demo clients (those with declining flow patterns)."""
    return get_demo_clients_by_category('at_risk')


def get_new_demo_clients() -> list:
    """Get new demo clients (recently onboarded)."""
    return get_demo_clients_by_category('new')


def get_all_demo_clients_sorted() -> list:
    """
    Get all demo clients (standard + at-risk + new) sorted by priority.
    Used by build_dim_client to include all client types.
    """
    return sorted(config.DEMO_CLIENTS.values(), key=lambda x: x['priority'])


def get_at_risk_client_ids() -> list:
    """
    Get the ClientIDs for at-risk clients (for flow generation).
    Returns list of priority values which map to ClientIDs.
    """
    return [c['priority'] for c in get_at_risk_demo_clients()]


def get_new_client_ids() -> list:
    """
    Get the ClientIDs for new clients (for flow generation).
    Returns list of priority values which map to ClientIDs.
    """
    return [c['priority'] for c in get_new_demo_clients()]


def build_demo_portfolios_sql_mapping() -> dict:
    """
    Build SQL fragments for demo portfolio construction from DEMO_COMPANIES config.
    Uses ticker-based logic (no FIGI dependency).
    """
    from sql_utils import safe_sql_tuple
    
    # Build priority SQL from DEMO_COMPANIES demo_order
    priority_case_when = []
    ordered_tickers = []
    max_order = 0
    
    for ticker, data in config.DEMO_COMPANIES.items():
        if 'demo_order' in data:
            order = data['demo_order']
            priority_case_when.append(f"WHEN s.Ticker = '{ticker}' THEN {order}")
            ordered_tickers.append(ticker)
            max_order = max(max_order, order)
    
    # Get large position tickers from DEMO_COMPANIES
    large_tickers = get_large_position_tickers()
    
    return {
        'priority_tickers': safe_sql_tuple(ordered_tickers) if ordered_tickers else "('')",
        'priority_case_when_sql': " ".join(priority_case_when) if priority_case_when else "WHEN 1=0 THEN 1",
        'additional_priority': max_order + 1,
        'large_position_tickers': safe_sql_tuple(large_tickers) if large_tickers else "('')"
    }

