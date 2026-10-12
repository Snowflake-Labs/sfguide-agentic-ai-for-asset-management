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
Demo helpers for company, portfolio, and client utilities.

Helper functions for working with demo companies, portfolios, and clients.
These functions access config data structures to provide convenient lookups.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_demo_company_tickers(tier: str = None) -> list:
    """Get list of tickers, optionally filtered by tier."""
    if tier:
        return [k for k, v in config.DEMO_COMPANIES.items() if v.get('tier') == tier]
    return list(config.DEMO_COMPANIES.keys())


def get_demo_company_ciks() -> list:
    """Get list of CIKs for all demo companies."""
    return [v['cik'] for v in config.DEMO_COMPANIES.values() if v.get('cik')]




def get_demo_company_priority_sql() -> str:
    """Generate SQL CASE statement for demo company priorities from DEMO_COMPANIES config.
    
    Priority encoding: tier_priority + (demo_order / 100) so that within a tier,
    companies with lower demo_order sort first. Companies without demo_order get
    tier_priority + 0.99 (sort last within their tier).
    """
    tier_to_priority = {'core': 1, 'major': 2, 'additional': 3}
    case_when_lines = []
    
    sorted_companies = sorted(
        config.DEMO_COMPANIES.items(), 
        key=lambda x: tier_to_priority.get(x[1].get('tier', 'additional'), 3)
    )
    
    for ticker, company_data in sorted_companies:
        base_priority = tier_to_priority.get(company_data.get('tier', 'additional'), 3)
        demo_order = company_data.get('demo_order')
        if demo_order is not None:
            priority = base_priority + (demo_order / 100.0)
        else:
            priority = base_priority + 0.99
        case_when_lines.append(f"WHEN s.Ticker = '{ticker}' THEN {priority}")
    
    if not case_when_lines:
        return "WHEN 1=0 THEN 999"
    
    return " ".join(case_when_lines)


def is_demo_portfolio(portfolio_name: str) -> bool:
    """Check if a portfolio is configured as a demo portfolio."""
    return portfolio_name in config.PORTFOLIOS and config.PORTFOLIOS[portfolio_name].get('is_demo_portfolio', False)


def get_demo_portfolio_names() -> list:
    """Get list of demo portfolio names only."""
    return [name for name, cfg in config.PORTFOLIOS.items() if cfg.get('is_demo_portfolio', False)]




def get_large_position_tickers() -> list:
    """Get list of tickers with position_size='large'."""
    return [
        ticker for ticker, data in config.DEMO_COMPANIES.items()
        if data.get('position_size') == 'large'
    ]


def get_portfolio_target_weights(portfolio_name: str) -> dict:
    """Get reference-data-driven target weights for a portfolio, keyed by ticker."""
    target_weights = {}
    for ticker, data in config.DEMO_COMPANIES.items():
        portfolio_targets = data.get('portfolio_targets', {})
        portfolio_target = portfolio_targets.get(portfolio_name)
        if portfolio_target and portfolio_target.get('target_weight') is not None:
            target_weights[ticker] = portfolio_target['target_weight']
    return target_weights


def get_portfolio_target_weights_sql(portfolio_name: str, portfolio_col: str = "p.PortfolioName", ticker_col: str = "s.Ticker") -> str:
    """Generate SQL CASE statement for portfolio target weights from reference data."""
    target_weights = get_portfolio_target_weights(portfolio_name)
    if not target_weights:
        return "NULL"

    case_lines = [
        f"WHEN {portfolio_col} = '{portfolio_name}' AND {ticker_col} = '{ticker}' THEN {weight}"
        for ticker, weight in target_weights.items()
    ]
    return "CASE " + " ".join(case_lines) + " ELSE NULL END"


def get_pinned_portfolio_names() -> list:
    """Portfolios with at least one reference-data target weight, in config order."""
    return [name for name in config.PORTFOLIOS if get_portfolio_target_weights(name)]


def _sql_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def get_all_portfolio_target_weights_sql(portfolio_col: str = "p.PortfolioName", ticker_col: str = "s.Ticker") -> str:
    """SQL CASE returning the target weight of every pinned (portfolio, ticker) pair."""
    case_lines = [
        f"WHEN {portfolio_col} = {_sql_literal(portfolio_name)} AND {ticker_col} = {_sql_literal(ticker)} THEN {float(weight)}"
        for portfolio_name in get_pinned_portfolio_names()
        for ticker, weight in get_portfolio_target_weights(portfolio_name).items()
    ]
    if not case_lines:
        return "NULL"
    return "CASE " + " ".join(case_lines) + " ELSE NULL END"


def get_portfolio_exclusions() -> list:
    """(portfolio, ticker) pairs that reference data says must never be held."""
    return [
        (portfolio_name, ticker)
        for ticker, data in config.DEMO_COMPANIES.items()
        for portfolio_name, target in (data.get('portfolio_targets') or {}).items()
        if target and target.get('exclude')
    ]


def _pairs_condition_sql(pairs: list, portfolio_col: str, ticker_col: str) -> str:
    if not pairs:
        return "FALSE"
    return "(" + " OR ".join(
        f"({portfolio_col} = {_sql_literal(p)} AND {ticker_col} = {_sql_literal(t)})"
        for p, t in pairs
    ) + ")"


def get_pinned_pairs_condition_sql(portfolio_col: str = "p.PortfolioName", ticker_col: str = "s.Ticker") -> str:
    """Boolean SQL that is TRUE for every pinned (portfolio, ticker) pair."""
    pairs = [
        (portfolio_name, ticker)
        for portfolio_name in get_pinned_portfolio_names()
        for ticker in get_portfolio_target_weights(portfolio_name)
    ]
    return _pairs_condition_sql(pairs, portfolio_col, ticker_col)


def get_excluded_pairs_condition_sql(portfolio_col: str = "p.PortfolioName", ticker_col: str = "s.Ticker") -> str:
    """Boolean SQL that is TRUE for every excluded (portfolio, ticker) pair."""
    return _pairs_condition_sql(get_portfolio_exclusions(), portfolio_col, ticker_col)




def get_demo_clients_by_category(category: str) -> list:
    """Get demo clients filtered by category (standard/at_risk/new)."""
    return sorted(
        [c for c in config.DEMO_CLIENTS.values() if c.get('category') == category],
        key=lambda x: x['priority']
    )


def get_demo_clients_sorted() -> list:
    """Get standard demo clients sorted by priority."""
    return get_demo_clients_by_category('standard')


def get_at_risk_demo_clients() -> list:
    """Get at-risk demo clients."""
    return get_demo_clients_by_category('at_risk')


def get_new_demo_clients() -> list:
    """Get new demo clients."""
    return get_demo_clients_by_category('new')


def get_all_demo_clients_sorted() -> list:
    """Get all demo clients sorted by priority."""
    return sorted(config.DEMO_CLIENTS.values(), key=lambda x: x['priority'])


def get_at_risk_client_ids() -> list:
    """Get the ClientIDs for at-risk clients."""
    return [c['priority'] for c in get_at_risk_demo_clients()]


def get_new_client_ids() -> list:
    """Get the ClientIDs for new clients."""
    return [c['priority'] for c in get_new_demo_clients()]


def build_demo_portfolios_sql_mapping() -> dict:
    """Build SQL fragments for demo portfolio construction from DEMO_COMPANIES config."""
    from .sql import safe_sql_tuple
    
    priority_case_when = []
    ordered_tickers = []
    max_order = 0
    
    for ticker, data in config.DEMO_COMPANIES.items():
        if 'demo_order' in data:
            order = data['demo_order']
            priority_case_when.append(f"WHEN s.Ticker = '{ticker}' THEN {order}")
            ordered_tickers.append(ticker)
            max_order = max(max_order, order)
    
    large_tickers = get_large_position_tickers()
    
    return {
        'priority_tickers': safe_sql_tuple(ordered_tickers) if ordered_tickers else "('')",
        'priority_case_when_sql': " ".join(priority_case_when) if priority_case_when else "WHEN 1=0 THEN 1",
        'additional_priority': max_order + 1,
        'large_position_tickers': safe_sql_tuple(large_tickers) if large_tickers else "('')"
    }
