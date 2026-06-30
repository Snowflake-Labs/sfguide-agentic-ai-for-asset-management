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
Snowflake I/O utilities for SAM Demo.

Provides:
- cleanup_temp_objects: Clean up Snowpark temp stages/formats
- prefetch_* functions: Batch data lookups for hydration
- Date anchor management (max price date)
- Table access verification
"""

from typing import Dict, List, Any, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from snowflake.snowpark import Session

from .logging import log_detail, log_warning
import config


_MAX_PRICE_DATE = None


def get_max_price_date(session, database_name: str = None) -> str:
    """
    Get the latest date available in FACT_STOCK_PRICES.
    
    This date serves as the anchor point for all data generation.
    Must be called AFTER FACT_STOCK_PRICES has been built.
    
    Returns:
        Date string in 'YYYY-MM-DD' format
    """
    global _MAX_PRICE_DATE
    if database_name is None:
        database_name = config.DATABASE['name']
    if _MAX_PRICE_DATE is None:
        result = session.sql(f"""
            SELECT MAX(PRICE_DATE) as max_date 
            FROM {database_name}.MARKET_DATA.FACT_STOCK_PRICES
        """).collect()
        _MAX_PRICE_DATE = result[0]['MAX_DATE']
        if _MAX_PRICE_DATE:
            log_detail(f"  Max price date anchor: {_MAX_PRICE_DATE}")
    return _MAX_PRICE_DATE


def reset_max_price_date():
    """Reset the cached max price date (call before rebuilding FACT_STOCK_PRICES)."""
    global _MAX_PRICE_DATE
    _MAX_PRICE_DATE = None


def verify_table_access(session, database: str, schema: str, table: str) -> tuple:
    """
    Check if a table is accessible.
    
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


def cleanup_temp_objects(session: Session) -> None:
    """
    Clean up any leftover Snowpark temp objects that may cause conflicts.
    
    write_pandas creates temporary objects with patterns:
    - SNOWPARK_TEMP_STAGE_*
    - SNOWPARK_TEMP_FILE_FORMAT_*
    """
    try:
        stages = session.sql("SHOW STAGES LIKE 'SNOWPARK_TEMP_STAGE_%'").collect()
        for stage in stages:
            try:
                session.sql(f"DROP STAGE IF EXISTS {stage['name']}").collect()
            except Exception:
                pass
    except Exception:
        pass
    
    try:
        formats = session.sql("SHOW FILE FORMATS LIKE 'SNOWPARK_TEMP_FILE_FORMAT_%'").collect()
        for fmt in formats:
            try:
                session.sql(f"DROP FILE FORMAT IF EXISTS {fmt['name']}").collect()
            except Exception:
                pass
    except Exception:
        pass


cleanup_temp_stages = cleanup_temp_objects


def prefetch_security_contexts(
    session: Session,
    database_name: str,
    security_ids: List[int]
) -> Dict[int, Dict[str, Any]]:
    """Prefetch security context data for multiple SecurityIDs in a single query."""
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
    """Prefetch issuer context data for multiple IssuerIDs in a single query."""
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
    """Prefetch portfolio context data for multiple PortfolioIDs in a single query."""
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
    """Prefetch fiscal calendar data for multiple CIKs in a single query."""
    if not ciks:
        return {}
    
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
        
        result: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            cik = row['CIK']
            if cik not in result:
                result[cik] = []
            result[cik].append(row.as_dict())
        
        return result
    except Exception:
        return {}


def prefetch_sec_financials(
    session: Session,
    database_name: str,
    ciks: List[str],
    num_periods: int = 8
) -> Dict[str, Dict[Tuple[int, str], Dict[str, Any]]]:
    """Prefetch SEC financial metrics for multiple CIKs in a single query."""
    if not ciks:
        return {}
    
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
        return {}
