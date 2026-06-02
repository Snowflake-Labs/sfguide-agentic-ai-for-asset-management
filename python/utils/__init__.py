"""
Consolidated utilities for SAM Demo.

Modules:
    logging: Structured logging functions
    sql: SQL generation helpers and case builders
    snowflake: Snowflake I/O utilities (prefetch, cleanup, table access)
    config_helpers: Config accessor functions
    demo_helpers: Demo company/portfolio lookup functions
"""

from .logging import (
    set_verbosity,
    log_phase,
    log_step,
    log_substep,
    log_detail,
    log_info,
    log_success,
    log_warning,
    log_error,
    log_phase_complete,
)

from .sql import (
    safe_sql_tuple,
    sql_uniform,
    build_sector_case_sql,
    build_country_group_case_sql,
    build_country_settlement_case_sql,
    build_grade_case_sql,
    build_overall_esg_sql,
    build_strategy_case_sql,
    build_global_uniform_sql,
    build_factor_case_sql,
    get_factor_r_squared,
)

from .snowflake import (
    get_max_price_date,
    reset_max_price_date,
    verify_table_access,
    cleanup_temp_objects,
    cleanup_temp_stages,
    prefetch_security_contexts,
    prefetch_issuer_contexts,
    prefetch_portfolio_contexts,
    prefetch_fiscal_calendars,
    prefetch_sec_financials,
)

from .config_helpers import (
    get_sector_range,
    get_country_group_for,
    get_country_value,
    get_strategy_value,
    get_global_value,
    get_required_document_types,
)

from .demo_helpers import (
    get_demo_company_tickers,
    get_demo_company_ciks,
    get_demo_company_by_ticker,
    get_demo_company_priority_sql,
    is_demo_portfolio,
    get_demo_portfolio_names,
    get_demo_order_tickers,
    get_large_position_tickers,
    get_demo_client_names,
    get_demo_client_by_type,
    get_demo_clients_by_category,
    get_demo_clients_sorted,
    get_at_risk_demo_clients,
    get_new_demo_clients,
    get_all_demo_clients_sorted,
    get_at_risk_client_ids,
    get_new_client_ids,
    build_demo_portfolios_sql_mapping,
)

__all__ = [
    # Logging
    'set_verbosity', 'log_phase', 'log_step', 'log_substep', 'log_detail',
    'log_info', 'log_success', 'log_warning', 'log_error', 'log_phase_complete',
    # SQL
    'safe_sql_tuple', 'sql_uniform', 'build_sector_case_sql', 
    'build_country_group_case_sql', 'build_country_settlement_case_sql',
    'build_grade_case_sql', 'build_overall_esg_sql', 'build_strategy_case_sql',
    'build_global_uniform_sql', 'build_factor_case_sql', 'get_factor_r_squared',
    # Snowflake
    'get_max_price_date', 'reset_max_price_date', 'verify_table_access',
    'cleanup_temp_objects', 'cleanup_temp_stages', 'prefetch_security_contexts',
    'prefetch_issuer_contexts', 'prefetch_portfolio_contexts',
    'prefetch_fiscal_calendars', 'prefetch_sec_financials',
    # Config helpers
    'get_sector_range', 'get_country_group_for', 'get_country_value',
    'get_strategy_value', 'get_global_value', 'get_required_document_types',
    # Demo helpers
    'get_demo_company_tickers', 'get_demo_company_ciks', 'get_demo_company_by_ticker',
    'get_demo_company_priority_sql', 'is_demo_portfolio', 'get_demo_portfolio_names',
    'get_demo_order_tickers', 'get_large_position_tickers', 'get_demo_client_names',
    'get_demo_client_by_type', 'get_demo_clients_by_category', 'get_demo_clients_sorted',
    'get_at_risk_demo_clients', 'get_new_demo_clients', 'get_all_demo_clients_sorted',
    'get_at_risk_client_ids', 'get_new_client_ids', 'build_demo_portfolios_sql_mapping',
]
