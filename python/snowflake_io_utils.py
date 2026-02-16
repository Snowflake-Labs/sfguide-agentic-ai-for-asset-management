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
Snowflake I/O Utilities

This module provides:
- cleanup_temp_stages(): Clean up leftover Snowpark temp stages
- prefetch_* functions: Batch data lookups for hydration (avoid per-entity queries)

For writes, use native session.write_pandas() directly.
For simple lookups, use session.sql().collect() with dict comprehension.
"""

from typing import Dict, List, Any, Tuple
from snowflake.snowpark import Session


def cleanup_temp_objects(session: Session) -> None:
    """
    Clean up any leftover Snowpark temp objects that may cause conflicts.
    
    write_pandas creates temporary objects with patterns:
    - SNOWPARK_TEMP_STAGE_*
    - SNOWPARK_TEMP_FILE_FORMAT_*
    
    If a previous run was interrupted, these may persist and cause
    'Object already exists' errors on subsequent runs.
    
    Safe to call before session.write_pandas().
    """
    # Clean up temp stages
    try:
        stages = session.sql("SHOW STAGES LIKE 'SNOWPARK_TEMP_STAGE_%'").collect()
        for stage in stages:
            try:
                session.sql(f"DROP STAGE IF EXISTS {stage['name']}").collect()
            except Exception:
                pass
    except Exception:
        pass
    
    # Clean up temp file formats
    try:
        formats = session.sql("SHOW FILE FORMATS LIKE 'SNOWPARK_TEMP_FILE_FORMAT_%'").collect()
        for fmt in formats:
            try:
                session.sql(f"DROP FILE FORMAT IF EXISTS {fmt['name']}").collect()
            except Exception:
                pass
    except Exception:
        pass


# Keep old name for backward compatibility
cleanup_temp_stages = cleanup_temp_objects


# =============================================================================
# PREFETCH FUNCTIONS - For hydration engine batch lookups
# =============================================================================


def prefetch_security_contexts(
    session: Session,
    database_name: str,
    security_ids: List[int]
) -> Dict[int, Dict[str, Any]]:
    """
    Prefetch security context data for multiple SecurityIDs in a single query.
    
    Used by hydration engine to avoid per-entity SELECT queries.
    
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
    
    rows = session.sql(f"""
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
    """).collect()
    
    return {row['SECURITYID']: row.as_dict() for row in rows}


def prefetch_issuer_contexts(
    session: Session,
    database_name: str,
    issuer_ids: List[int]
) -> Dict[int, Dict[str, Any]]:
    """
    Prefetch issuer context data for multiple IssuerIDs in a single query.
    
    Used by hydration engine to avoid per-entity SELECT queries.
    
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
    
    rows = session.sql(f"""
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
    """).collect()
    
    # Handle potential duplicate issuers with multiple securities (keep first)
    result = {}
    for row in rows:
        issuer_id = row['ISSUERID']
        if issuer_id not in result:
            result[issuer_id] = row.as_dict()
    
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
    
    rows = session.sql(f"""
        SELECT 
            PortfolioID,
            PortfolioName,
            Strategy,
            BaseCurrency,
            InceptionDate
        FROM {database_name}.CURATED.DIM_PORTFOLIO
        WHERE PortfolioID IN ({id_list})
    """).collect()
    
    return {row['PORTFOLIOID']: row.as_dict() for row in rows}


def prefetch_fiscal_calendars(
    session: Session,
    real_data_database: str,
    real_data_schema: str,
    ciks: List[str],
    num_periods: int = 4
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Prefetch fiscal calendar data for multiple CIKs in a single query.
    
    Used by hydration engine for fiscal period lookups.
    
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
        rows = session.sql(f"""
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
        """).collect()
        
        # Build dict of lists
        result: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            cik = row['CIK']
            if cik not in result:
                result[cik] = []
            result[cik].append(row.as_dict())
        
        return result
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
    """
    if not ciks:
        return {}
    
    # Filter out None/empty CIKs
    valid_ciks = [c for c in ciks if c]
    if not valid_ciks:
        return {}
    
    cik_list = ", ".join(f"'{c}'" for c in valid_ciks)
    
    try:
        rows = session.sql(f"""
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
        """).collect()
        
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
        return {}
