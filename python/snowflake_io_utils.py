"""
Snowflake I/O Utilities for Batched Writes and Reads

This module provides efficient patterns for interacting with Snowflake:
- Batched writes using SQL INSERT (no row-by-row inserts, no temp stages)
- Batched reads with local mapping (no collect-in-loop patterns)

Performance Guidelines:
- Use write_pandas_overwrite() for small/moderate dimension tables
- Use fetch_as_map() for lookup data needed in loops
- Keep large dataset operations as pure SQL (CREATE TABLE AS SELECT)

Note: Uses SQL INSERT with batched VALUES instead of write_pandas/create_dataframe
to avoid temporary stage conflicts in stored procedures.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union, Tuple
from snowflake.snowpark import Session


def _sql_value(val: Any) -> str:
    """Convert a Python value to SQL literal for INSERT statement."""
    if val is None:
        return "NULL"
    elif isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    elif isinstance(val, (int, float, Decimal)):
        return str(val)
    elif isinstance(val, (datetime, date)):
        return f"'{val.isoformat()}'"
    elif isinstance(val, (dict, list)):
        # JSON types - use PARSE_JSON
        json_str = json.dumps(val).replace("'", "''")
        return f"PARSE_JSON('{json_str}')"
    else:
        # String - escape single quotes
        escaped = str(val).replace("'", "''")
        return f"'{escaped}'"


def _infer_sql_type(val: Any) -> str:
    """Infer SQL type from Python value for CREATE TABLE."""
    if val is None:
        return "VARCHAR"
    elif isinstance(val, bool):
        return "BOOLEAN"
    elif isinstance(val, int):
        return "INTEGER"
    elif isinstance(val, float):
        return "FLOAT"
    elif isinstance(val, Decimal):
        return "NUMBER(38,10)"
    elif isinstance(val, datetime):
        return "TIMESTAMP"
    elif isinstance(val, date):
        return "DATE"
    elif isinstance(val, (dict, list)):
        return "VARIANT"
    else:
        return "VARCHAR"


def write_pandas_overwrite(
    session: Session,
    table_fqn: str,
    rows: List[Dict[str, Any]],
    create_table: bool = True
) -> int:
    """
    Write rows to a Snowflake table using batched SQL INSERT.
    
    This is the preferred method for small/moderate dimension tables.
    Avoids row-by-row INSERT loops and temp stage issues.
    
    Uses SQL CREATE TABLE + INSERT VALUES instead of write_pandas
    to avoid temporary stage conflicts in stored procedures.
    
    Args:
        session: Active Snowpark session
        table_fqn: Fully-qualified table name (e.g., 'SAM_DEMO.CURATED.DIM_COUNTERPARTY')
        rows: List of dicts representing rows to write
        create_table: If True, creates/replaces table; if False, truncates existing
    
    Returns:
        Number of rows written
    
    Example:
        rows = [
            {'CounterpartyID': 1, 'CounterpartyName': 'Goldman Sachs', 'RiskRating': 'A'},
            {'CounterpartyID': 2, 'CounterpartyName': 'Morgan Stanley', 'RiskRating': 'A'},
        ]
        write_pandas_overwrite(session, 'SAM_DEMO.CURATED.DIM_COUNTERPARTY', rows)
    """
    if not rows:
        return 0
    
    # Get column names from first row, uppercase for Snowflake
    columns = [col.upper() for col in rows[0].keys()]
    
    if create_table:
        # Infer types from first row
        first_row = rows[0]
        col_defs = []
        for col in rows[0].keys():
            col_upper = col.upper()
            sql_type = _infer_sql_type(first_row[col])
            col_defs.append(f"{col_upper} {sql_type}")
        
        # Create or replace table
        create_sql = f"CREATE OR REPLACE TABLE {table_fqn} ({', '.join(col_defs)})"
        session.sql(create_sql).collect()
    else:
        # Truncate existing table
        session.sql(f"TRUNCATE TABLE {table_fqn}").collect()
    
    # Insert in batches to avoid SQL length limits
    batch_size = 1000
    total_inserted = 0
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        
        # Build VALUES clause
        value_rows = []
        for row in batch:
            values = [_sql_value(row.get(col, row.get(col.lower()))) 
                      for col in columns]
            value_rows.append(f"({', '.join(values)})")
        
        insert_sql = f"INSERT INTO {table_fqn} ({', '.join(columns)}) VALUES {', '.join(value_rows)}"
        session.sql(insert_sql).collect()
        total_inserted += len(batch)
    
    return total_inserted


def write_pandas_append(
    session: Session,
    table_fqn: str,
    rows: List[Dict[str, Any]]
) -> int:
    """
    Append rows to an existing Snowflake table using batched SQL INSERT.
    
    Uses SQL INSERT VALUES instead of write_pandas to avoid
    temporary stage conflicts in stored procedures.
    
    Args:
        session: Active Snowpark session
        table_fqn: Fully-qualified table name
        rows: List of dicts representing rows to append
    
    Returns:
        Number of rows written
    """
    if not rows:
        return 0
    
    # Get column names from first row, uppercase for Snowflake
    columns = [col.upper() for col in rows[0].keys()]
    
    # Insert in batches to avoid SQL length limits
    batch_size = 1000
    total_inserted = 0
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        
        # Build VALUES clause
        value_rows = []
        for row in batch:
            values = [_sql_value(row.get(col, row.get(col.lower()))) 
                      for col in columns]
            value_rows.append(f"({', '.join(values)})")
        
        insert_sql = f"INSERT INTO {table_fqn} ({', '.join(columns)}) VALUES {', '.join(value_rows)}"
        session.sql(insert_sql).collect()
        total_inserted += len(batch)
    
    return total_inserted


def fetch_as_map(
    session: Session,
    sql: str,
    key_column: str,
    value_columns: Optional[Union[str, List[str]]] = None
) -> Dict[Any, Any]:
    """
    Execute a query and return results as a dictionary for fast local lookups.
    
    This is the preferred pattern for lookup data needed in loops.
    Avoids per-iteration SELECT queries which are inefficient.
    
    Args:
        session: Active Snowpark session
        sql: SQL query to execute
        key_column: Column name to use as dictionary key
        value_columns: Column(s) to use as dictionary value
            - If None: entire row dict is the value
            - If str: single column value
            - If List[str]: dict of specified columns
    
    Returns:
        Dictionary mapping key_column values to row data
    
    Example:
        # Fetch SecurityID -> full row mapping
        sql = "SELECT SecurityID, Ticker, FIGI FROM DIM_SECURITY WHERE Ticker IN ('AAPL', 'MSFT')"
        sec_map = fetch_as_map(session, sql, 'SECURITYID')
        # sec_map = {123: {'SECURITYID': 123, 'TICKER': 'AAPL', 'FIGI': 'BBG...'}, ...}
        
        # Fetch Ticker -> SecurityID mapping
        sec_ids = fetch_as_map(session, sql, 'TICKER', 'SECURITYID')
        # sec_ids = {'AAPL': 123, 'MSFT': 456}
    """
    rows = session.sql(sql).collect()
    
    if not rows:
        return {}
    
    result = {}
    key_col_upper = key_column.upper()
    
    for row in rows:
        row_dict = row.as_dict()
        key = row_dict.get(key_col_upper)
        
        if key is None:
            continue
        
        if value_columns is None:
            # Return entire row as value
            result[key] = row_dict
        elif isinstance(value_columns, str):
            # Return single column value
            result[key] = row_dict.get(value_columns.upper())
        else:
            # Return dict of specified columns
            result[key] = {
                col.upper(): row_dict.get(col.upper())
                for col in value_columns
            }
    
    return result


def fetch_as_list_map(
    session: Session,
    sql: str,
    key_column: str,
    value_columns: Optional[Union[str, List[str]]] = None
) -> Dict[Any, List[Any]]:
    """
    Execute a query and return results as a dictionary of lists for one-to-many lookups.
    
    Useful when a single key maps to multiple rows (e.g., CIK -> multiple fiscal periods).
    
    Args:
        session: Active Snowpark session
        sql: SQL query to execute
        key_column: Column name to use as dictionary key
        value_columns: Column(s) to use as dictionary value (same semantics as fetch_as_map)
    
    Returns:
        Dictionary mapping key_column values to lists of row data
    
    Example:
        # Fetch CIK -> list of fiscal periods
        sql = "SELECT CIK, FISCAL_PERIOD, FISCAL_YEAR FROM SEC_FISCAL_CALENDARS WHERE CIK IN (...)"
        fiscal_map = fetch_as_list_map(session, sql, 'CIK')
        # fiscal_map = {'0001234': [{'CIK': '0001234', 'FISCAL_PERIOD': 'Q1', ...}, ...], ...}
    """
    rows = session.sql(sql).collect()
    
    if not rows:
        return {}
    
    result: Dict[Any, List[Any]] = {}
    key_col_upper = key_column.upper()
    
    for row in rows:
        row_dict = row.as_dict()
        key = row_dict.get(key_col_upper)
        
        if key is None:
            continue
        
        if value_columns is None:
            value = row_dict
        elif isinstance(value_columns, str):
            value = row_dict.get(value_columns.upper())
        else:
            value = {
                col.upper(): row_dict.get(col.upper())
                for col in value_columns
            }
        
        if key not in result:
            result[key] = []
        result[key].append(value)
    
    return result


def batch_lookup_security_ids(
    session: Session,
    database_name: str,
    tickers: Optional[List[str]] = None,
    figis: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Batch lookup SecurityIDs for multiple tickers/FIGIs in a single query.
    
    Returns a mapping that can be looked up by either ticker or FIGI.
    
    Args:
        session: Active Snowpark session
        database_name: Database name (e.g., 'SAM_DEMO')
        tickers: List of ticker symbols to look up
        figis: List of FIGI identifiers to look up
    
    Returns:
        Dict mapping ticker/FIGI to SecurityID
    
    Example:
        sec_map = batch_lookup_security_ids(
            session, 'SAM_DEMO',
            tickers=['AAPL', 'MSFT'],
            figis=['BBG001S5N8V8']
        )
        apple_id = sec_map.get('AAPL') or sec_map.get('BBG001S5N8V8')
    """
    conditions = []
    
    if tickers:
        ticker_list = ", ".join(f"'{t}'" for t in tickers)
        conditions.append(f"Ticker IN ({ticker_list})")
    
    if figis:
        figi_list = ", ".join(f"'{f}'" for f in figis)
        conditions.append(f"FIGI IN ({figi_list})")
    
    if not conditions:
        return {}
    
    where_clause = " OR ".join(conditions)
    
    sql = f"""
        SELECT SecurityID, Ticker, FIGI
        FROM {database_name}.CURATED.DIM_SECURITY
        WHERE {where_clause}
    """
    
    rows = session.sql(sql).collect()
    
    result = {}
    for row in rows:
        row_dict = row.as_dict()
        sec_id = row_dict['SECURITYID']
        
        # Map both ticker and FIGI to the SecurityID
        if row_dict.get('TICKER'):
            result[row_dict['TICKER']] = sec_id
        if row_dict.get('FIGI'):
            result[row_dict['FIGI']] = sec_id
    
    return result


def prefetch_security_contexts(
    session: Session,
    database_name: str,
    security_ids: List[int]
) -> Dict[int, Dict[str, Any]]:
    """
    Prefetch security context data for multiple SecurityIDs in a single query.
    
    This replaces per-entity SELECT queries in hydration loops.
    
    Args:
        session: Active Snowpark session
        database_name: Database name
        security_ids: List of SecurityIDs to prefetch
    
    Returns:
        Dict mapping SecurityID to context data
    """
    if not security_ids:
        return {}
    
    id_list = ", ".join(str(sid) for sid in security_ids)
    
    sql = f"""
        SELECT 
            ds.SecurityID,
            ds.Ticker,
            ds.Description as COMPANY_NAME,
            ds.AssetClass,
            di.IssuerID,
            di.LegalName as ISSUER_NAME,
            di.SIC_DESCRIPTION,
            di.CountryOfIncorporation,
            di.CIK
        FROM {database_name}.CURATED.DIM_SECURITY ds
        JOIN {database_name}.CURATED.DIM_ISSUER di ON ds.IssuerID = di.IssuerID
        WHERE ds.SecurityID IN ({id_list})
    """
    
    return fetch_as_map(session, sql, 'SECURITYID')


def prefetch_issuer_contexts(
    session: Session,
    database_name: str,
    issuer_ids: List[int]
) -> Dict[int, Dict[str, Any]]:
    """
    Prefetch issuer context data for multiple IssuerIDs in a single query.
    
    This replaces per-entity SELECT queries in hydration loops.
    
    Args:
        session: Active Snowpark session
        database_name: Database name
        issuer_ids: List of IssuerIDs to prefetch
    
    Returns:
        Dict mapping IssuerID to context data
    """
    if not issuer_ids:
        return {}
    
    id_list = ", ".join(str(iid) for iid in issuer_ids)
    
    sql = f"""
        SELECT 
            di.IssuerID,
            di.LegalName as ISSUER_NAME,
            di.SIC_DESCRIPTION,
            di.CountryOfIncorporation,
            di.CIK,
            ds.Ticker
        FROM {database_name}.CURATED.DIM_ISSUER di
        LEFT JOIN {database_name}.CURATED.DIM_SECURITY ds ON di.IssuerID = ds.IssuerID
        WHERE di.IssuerID IN ({id_list})
    """
    
    # Use fetch_as_map but handle potential duplicate issuers with multiple securities
    rows = session.sql(sql).collect()
    
    result = {}
    for row in rows:
        row_dict = row.as_dict()
        issuer_id = row_dict['ISSUERID']
        
        # Only keep first ticker per issuer
        if issuer_id not in result:
            result[issuer_id] = row_dict
    
    return result


def prefetch_portfolio_contexts(
    session: Session,
    database_name: str,
    portfolio_ids: List[int]
) -> Dict[int, Dict[str, Any]]:
    """
    Prefetch portfolio context data for multiple PortfolioIDs in a single query.
    
    Args:
        session: Active Snowpark session
        database_name: Database name
        portfolio_ids: List of PortfolioIDs to prefetch
    
    Returns:
        Dict mapping PortfolioID to context data
    """
    if not portfolio_ids:
        return {}
    
    id_list = ", ".join(str(pid) for pid in portfolio_ids)
    
    sql = f"""
        SELECT 
            PortfolioID,
            PortfolioName,
            Strategy,
            BaseCurrency,
            InceptionDate
        FROM {database_name}.CURATED.DIM_PORTFOLIO
        WHERE PortfolioID IN ({id_list})
    """
    
    return fetch_as_map(session, sql, 'PORTFOLIOID')


def prefetch_fiscal_calendars(
    session: Session,
    real_data_database: str,
    real_data_schema: str,
    ciks: List[str],
    num_periods: int = 4
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Prefetch fiscal calendar data for multiple CIKs in a single query.
    
    This replaces per-CIK fiscal calendar queries in hydration loops.
    
    Args:
        session: Active Snowpark session
        real_data_database: Database containing SEC data
        real_data_schema: Schema containing SEC data
        ciks: List of CIK identifiers to prefetch
        num_periods: Number of recent periods per CIK
    
    Returns:
        Dict mapping CIK to list of fiscal period dicts (most recent first)
    """
    if not ciks:
        return {}
    
    # Filter out None/empty CIKs
    valid_ciks = [c for c in ciks if c]
    if not valid_ciks:
        return {}
    
    cik_list = ", ".join(f"'{c}'" for c in valid_ciks)
    
    try:
        sql = f"""
            SELECT 
                CIK,
                COMPANY_NAME,
                FISCAL_PERIOD,
                FISCAL_YEAR,
                PERIOD_END_DATE,
                PERIOD_START_DATE,
                DAYS_IN_PERIOD,
                ROW_NUMBER() OVER (PARTITION BY CIK ORDER BY PERIOD_END_DATE DESC) as rn
            FROM {real_data_database}.{real_data_schema}.SEC_FISCAL_CALENDARS
            WHERE CIK IN ({cik_list})
                AND FISCAL_PERIOD IN ('Q1', 'Q2', 'Q3', 'Q4')
                AND PERIOD_END_DATE IS NOT NULL
            QUALIFY rn <= {num_periods}
            ORDER BY CIK, PERIOD_END_DATE DESC
        """
        
        return fetch_as_list_map(session, sql, 'CIK')
    except Exception:
        # If SEC_FISCAL_CALENDARS is not accessible, return empty dict
        return {}


def prefetch_sec_financials(
    session: Session,
    database_name: str,
    ciks: List[str],
    num_periods: int = 8
) -> Dict[str, Dict[Tuple[int, str], Dict[str, Any]]]:
    """
    Prefetch SEC financial metrics for multiple CIKs in a single query.
    
    Returns data keyed by CIK then by (fiscal_year, fiscal_period) tuple,
    enabling efficient lookup when hydrating documents for a specific quarter.
    
    Pre-computes YoY revenue growth using LAG window over 4 periods.
    
    Args:
        session: Active Snowpark session
        database_name: Database containing MARKET_DATA.FACT_SEC_FINANCIALS
        ciks: List of CIK identifiers to prefetch
        num_periods: Number of recent periods per CIK (default 8 for YoY calc)
    
    Returns:
        Nested dict: financials[cik][(fiscal_year, fiscal_period)] = {metrics...}
        
    Example:
        financials = prefetch_sec_financials(session, 'SAM_DEMO', ['0000789019', '0000320193'])
        msft_q3_2024 = financials.get('0000789019', {}).get((2024, 'Q3'), {})
        revenue = msft_q3_2024.get('REVENUE')
    """
    if not ciks:
        return {}
    
    # Filter out None/empty CIKs
    valid_ciks = [c for c in ciks if c]
    if not valid_ciks:
        return {}
    
    cik_list = ", ".join(f"'{c}'" for c in valid_ciks)
    
    try:
        sql = f"""
            WITH ranked_financials AS (
                SELECT 
                    CIK,
                    FISCAL_YEAR,
                    FISCAL_PERIOD,
                    PERIOD_END_DATE,
                    REVENUE,
                    NET_INCOME,
                    GROSS_PROFIT,
                    OPERATING_INCOME,
                    EPS_BASIC,
                    EPS_DILUTED,
                    GROSS_MARGIN_PCT,
                    OPERATING_MARGIN_PCT,
                    NET_MARGIN_PCT,
                    ROE_PCT,
                    ROA_PCT,
                    TOTAL_ASSETS,
                    TOTAL_LIABILITIES,
                    TOTAL_EQUITY,
                    CASH_AND_EQUIVALENTS,
                    LONG_TERM_DEBT,
                    OPERATING_CASH_FLOW,
                    FREE_CASH_FLOW,
                    DEBT_TO_EQUITY,
                    CURRENT_RATIO,
                    -- Compute YoY revenue growth (comparing to same quarter previous year)
                    LAG(REVENUE, 4) OVER (PARTITION BY CIK ORDER BY PERIOD_END_DATE) as REVENUE_PRIOR_YEAR,
                    ROW_NUMBER() OVER (PARTITION BY CIK ORDER BY PERIOD_END_DATE DESC) as rn
                FROM {database_name}.MARKET_DATA.FACT_SEC_FINANCIALS
                WHERE CIK IN ({cik_list})
                  AND FISCAL_PERIOD IN ('Q1', 'Q2', 'Q3', 'Q4')
            )
            SELECT 
                *,
                CASE 
                    WHEN REVENUE_PRIOR_YEAR > 0 AND REVENUE IS NOT NULL 
                    THEN ROUND((REVENUE - REVENUE_PRIOR_YEAR) / REVENUE_PRIOR_YEAR * 100, 1)
                    ELSE NULL 
                END as YOY_REVENUE_GROWTH_PCT
            FROM ranked_financials
            WHERE rn <= {num_periods}
            ORDER BY CIK, PERIOD_END_DATE DESC
        """
        
        rows = session.sql(sql).collect()
        
        # Build nested dict: cik -> (year, period) -> metrics
        result: Dict[str, Dict[Tuple[int, str], Dict[str, Any]]] = {}
        
        for row in rows:
            cik = row['CIK']
            fiscal_year = int(row['FISCAL_YEAR']) if row['FISCAL_YEAR'] else None
            fiscal_period = row['FISCAL_PERIOD']
            
            if not cik or not fiscal_year or not fiscal_period:
                continue
            
            if cik not in result:
                result[cik] = {}
            
            key = (fiscal_year, fiscal_period)
            result[cik][key] = {
                'REVENUE': row['REVENUE'],
                'NET_INCOME': row['NET_INCOME'],
                'GROSS_PROFIT': row['GROSS_PROFIT'],
                'OPERATING_INCOME': row['OPERATING_INCOME'],
                'EPS_BASIC': row['EPS_BASIC'],
                'EPS_DILUTED': row['EPS_DILUTED'],
                'GROSS_MARGIN_PCT': row['GROSS_MARGIN_PCT'],
                'OPERATING_MARGIN_PCT': row['OPERATING_MARGIN_PCT'],
                'NET_MARGIN_PCT': row['NET_MARGIN_PCT'],
                'ROE_PCT': row['ROE_PCT'],
                'ROA_PCT': row['ROA_PCT'],
                'TOTAL_ASSETS': row['TOTAL_ASSETS'],
                'TOTAL_LIABILITIES': row['TOTAL_LIABILITIES'],
                'TOTAL_EQUITY': row['TOTAL_EQUITY'],
                'CASH_AND_EQUIVALENTS': row['CASH_AND_EQUIVALENTS'],
                'LONG_TERM_DEBT': row['LONG_TERM_DEBT'],
                'OPERATING_CASH_FLOW': row['OPERATING_CASH_FLOW'],
                'FREE_CASH_FLOW': row['FREE_CASH_FLOW'],
                'DEBT_TO_EQUITY': row['DEBT_TO_EQUITY'],
                'CURRENT_RATIO': row['CURRENT_RATIO'],
                'YOY_REVENUE_GROWTH_PCT': row['YOY_REVENUE_GROWTH_PCT'],
                'PERIOD_END_DATE': row['PERIOD_END_DATE'],
            }
        
        return result
        
    except Exception:
        # If FACT_SEC_FINANCIALS is not accessible, return empty dict
        # This allows fallback to synthetic numeric generation
        return {}

