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
Counterfactual attribution analysis tool for SAM Demo.
Recalculates Brinson attribution under alternative scenarios.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail


def create_counterfactual_tool(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    session.sql(
        f"DROP PROCEDURE IF EXISTS {database_name}.{ai_schema}.RUN_COUNTERFACTUAL_ANALYSIS(VARCHAR, VARCHAR, VARCHAR, VARCHAR)"
    ).collect()

    tool_sql = f"""
CREATE OR REPLACE PROCEDURE {database_name}.{ai_schema}.RUN_COUNTERFACTUAL_ANALYSIS(
    PORTFOLIO_NAME_OR_ID VARCHAR,
    START_DATE VARCHAR,
    END_DATE VARCHAR,
    SCENARIO_TYPE VARCHAR,
    CAP_PCT FLOAT DEFAULT NULL
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_counterfactual'
AS
$$
import json
from datetime import date

def run_counterfactual(session, portfolio_name_or_id, start_date, end_date, scenario_type, cap_pct=None):
    database = '{database_name}'
    curated = 'CURATED'

    # Exact match on ID or full name ("SAM " prefix optional); the value is bound, never pasted into SQL.
    lookup_value = str(portfolio_name_or_id or '').strip()
    portfolio_row = session.sql(f\"\"\"
        SELECT PORTFOLIOID, PORTFOLIONAME
        FROM {{database}}.{{curated}}.DIM_PORTFOLIO
        WHERE PORTFOLIOID = TRY_CAST(? AS INTEGER)
           OR UPPER(PORTFOLIONAME) = UPPER(?)
           OR UPPER(PORTFOLIONAME) = UPPER('SAM ' || ?)
        ORDER BY IFF(PORTFOLIOID = TRY_CAST(? AS INTEGER), 0, 1)
        LIMIT 1
    \"\"\", params=[lookup_value] * 4).collect()

    if not portfolio_row:
        available = session.sql(f"SELECT PORTFOLIOID || ': ' || PORTFOLIONAME AS P FROM {{database}}.{{curated}}.DIM_PORTFOLIO ORDER BY PORTFOLIOID").collect()
        portfolio_list = ', '.join(r['P'] for r in available)
        return {{"error": f"Portfolio '{{portfolio_name_or_id}}' not found. Pass the full portfolio name or ID exactly. Available portfolios: {{portfolio_list}}"}}

    pid = portfolio_row[0]['PORTFOLIOID']
    pname = portfolio_row[0]['PORTFOLIONAME']

    try:
        start_date = date.fromisoformat(str(start_date).strip()).isoformat()
        end_date = date.fromisoformat(str(end_date).strip()).isoformat()
    except ValueError:
        return {{"error": f"Dates must be YYYY-MM-DD; got start_date={{start_date!r}}, end_date={{end_date!r}}"}}

    original = session.sql(f\"\"\"
        SELECT
            GroupingDimension,
            GroupingValue,
            SUM(PortfolioWeight) / COUNT(DISTINCT DATE) AS AVG_PORT_WEIGHT,
            SUM(BenchmarkWeight) / COUNT(DISTINCT DATE) AS AVG_BM_WEIGHT,
            SUM(AllocationEffect) AS TOTAL_ALLOCATION,
            SUM(SelectionEffect) AS TOTAL_SELECTION,
            SUM(InteractionEffect) AS TOTAL_INTERACTION,
            SUM(TotalEffect) AS TOTAL_EFFECT
        FROM {{database}}.{{curated}}.FACT_BRINSON_ATTRIBUTION_DETAIL
        WHERE PortfolioID = ?
            AND GroupingDimension = 'SECTOR'
            AND DATE >= ?::DATE
            AND DATE <= ?::DATE
        GROUP BY GroupingDimension, GroupingValue
        ORDER BY ABS(SUM(TotalEffect)) DESC
    \"\"\", params=[pid, start_date, end_date]).collect()

    if not original:
        return {{"error": "No attribution data found for the specified period"}}

    original_total = sum(r['TOTAL_EFFECT'] for r in original)
    cap_binding = None

    if scenario_type.upper() == 'BENCHMARK_WEIGHTS':
        counterfactual_total = 0
        details = []
        for row in original:
            new_alloc = 0
            new_selection = row['AVG_BM_WEIGHT'] * (row['TOTAL_SELECTION'] / max(row['AVG_BM_WEIGHT'], 0.001))
            new_interaction = 0
            new_total = new_alloc + new_selection + new_interaction
            counterfactual_total += new_total
            details.append({{
                "group": row['GROUPINGVALUE'],
                "original_effect": round(row['TOTAL_EFFECT'], 6),
                "counterfactual_effect": round(new_total, 6),
                "difference": round(new_total - row['TOTAL_EFFECT'], 6)
            }})
        scenario_desc = "What if we held benchmark weights in all sectors (zero allocation effect)"

    elif scenario_type.upper() == 'CAP_WEIGHT':
        cap = 0.25 if cap_pct is None else float(cap_pct)
        if cap > 1:
            cap = cap / 100.0
        if not 0 < cap < 1:
            return {{"error": f"cap_pct must be between 0 and 100 percent; got {{cap_pct!r}}"}}
        excess = []
        under = []
        for row in original:
            if row['AVG_PORT_WEIGHT'] > cap:
                excess.append(row)
            else:
                under.append(row)

        if not excess:
            return {{
                "portfolio": pname,
                "period": f"{{start_date}} to {{end_date}}",
                "scenario": f"What if no sector exceeded {{cap*100:g}}% weight (capped and redistributed)",
                "cap_pct": round(cap * 100, 2),
                "cap_binding": False,
                "note": f"No sector averaged above {{cap*100:g}}% weight, so the cap does not bind and the result is unchanged",
                "original_active_return": round(original_total, 6),
                "counterfactual_active_return": round(original_total, 6),
                "difference": 0.0,
                "sector_details": [
                    {{
                        "group": r['GROUPINGVALUE'],
                        "original_weight": round(r['AVG_PORT_WEIGHT'], 4),
                        "new_weight": round(r['AVG_PORT_WEIGHT'], 4),
                        "original_effect": round(r['TOTAL_EFFECT'], 6),
                        "counterfactual_effect": round(r['TOTAL_EFFECT'], 6)
                    }}
                    for r in original
                ]
            }}

        total_excess = sum(r['AVG_PORT_WEIGHT'] - cap for r in excess)
        total_under_weight = sum(r['AVG_PORT_WEIGHT'] for r in under)

        details = []
        counterfactual_total = 0
        for row in original:
            if row['AVG_PORT_WEIGHT'] > cap:
                new_weight = cap
            elif total_under_weight > 0:
                share = row['AVG_PORT_WEIGHT'] / total_under_weight
                new_weight = row['AVG_PORT_WEIGHT'] + total_excess * share
            else:
                new_weight = row['AVG_PORT_WEIGHT']
            weight_diff = new_weight - row['AVG_BM_WEIGHT']
            new_total = row['TOTAL_EFFECT'] * (new_weight / max(row['AVG_PORT_WEIGHT'], 0.001))
            counterfactual_total += new_total
            details.append({{
                "group": row['GROUPINGVALUE'],
                "original_weight": round(row['AVG_PORT_WEIGHT'], 4),
                "new_weight": round(new_weight, 4),
                "original_effect": round(row['TOTAL_EFFECT'], 6),
                "counterfactual_effect": round(new_total, 6)
            }})
        scenario_desc = f"What if no sector exceeded {{cap*100:g}}% weight (capped and redistributed)"
        cap_binding = True

    elif scenario_type.upper() == 'EXCLUDE_GROUP':
        exclude_group = end_date if start_date == end_date else 'Information Technology'
        excluded = [r for r in original if r['GROUPINGVALUE'] == exclude_group]
        remaining = [r for r in original if r['GROUPINGVALUE'] != exclude_group]

        if not excluded:
            return {{"error": f"Group '{{exclude_group}}' not found in attribution data"}}

        excluded_weight = sum(r['AVG_PORT_WEIGHT'] for r in excluded)
        remaining_total_weight = sum(r['AVG_PORT_WEIGHT'] for r in remaining)

        details = []
        counterfactual_total = 0
        for row in remaining:
            if remaining_total_weight > 0:
                new_weight = row['AVG_PORT_WEIGHT'] / remaining_total_weight
            else:
                new_weight = row['AVG_PORT_WEIGHT']
            new_total = row['TOTAL_EFFECT'] * (new_weight / max(row['AVG_PORT_WEIGHT'], 0.001))
            counterfactual_total += new_total
            details.append({{
                "group": row['GROUPINGVALUE'],
                "original_weight": round(row['AVG_PORT_WEIGHT'], 4),
                "new_weight": round(new_weight, 4),
                "original_effect": round(row['TOTAL_EFFECT'], 6),
                "counterfactual_effect": round(new_total, 6)
            }})
        scenario_desc = f"What if we excluded {{exclude_group}} and redistributed pro-rata"

    elif scenario_type.upper() == 'SWAP_CLASSIFICATION':
        country_data = session.sql(f\"\"\"
            SELECT
                GroupingValue,
                SUM(AllocationEffect) AS TOTAL_ALLOCATION,
                SUM(SelectionEffect) AS TOTAL_SELECTION,
                SUM(InteractionEffect) AS TOTAL_INTERACTION,
                SUM(TotalEffect) AS TOTAL_EFFECT
            FROM {{database}}.{{curated}}.FACT_BRINSON_ATTRIBUTION_DETAIL
            WHERE PortfolioID = ?
                AND GroupingDimension = 'COUNTRY'
                AND DATE >= ?::DATE
                AND DATE <= ?::DATE
            GROUP BY GroupingValue
            ORDER BY ABS(SUM(TotalEffect)) DESC
        \"\"\", params=[pid, start_date, end_date]).collect()

        sector_total = sum(r['TOTAL_EFFECT'] for r in original)
        country_total = sum(r['TOTAL_EFFECT'] for r in country_data)

        details = []
        for row in country_data[:10]:
            details.append({{
                "country": row['GROUPINGVALUE'],
                "allocation": round(row['TOTAL_ALLOCATION'], 6),
                "selection": round(row['TOTAL_SELECTION'], 6),
                "total_effect": round(row['TOTAL_EFFECT'], 6)
            }})

        counterfactual_total = country_total
        scenario_desc = "Classification swap: Country attribution vs Sector attribution"
        return {{
            "portfolio": pname,
            "period": f"{{start_date}} to {{end_date}}",
            "scenario": scenario_desc,
            "sector_active_return": round(sector_total, 6),
            "country_active_return": round(country_total, 6),
            "classification_divergence": round(abs(sector_total - country_total), 6),
            "country_details": details
        }}

    else:
        return {{"error": f"Unknown scenario_type: {{scenario_type}}. Use BENCHMARK_WEIGHTS, CAP_WEIGHT, EXCLUDE_GROUP, or SWAP_CLASSIFICATION."}}

    result = {{
        "portfolio": pname,
        "period": f"{{start_date}} to {{end_date}}",
        "scenario": scenario_desc,
        "original_active_return": round(original_total, 6),
        "counterfactual_active_return": round(counterfactual_total, 6),
        "difference": round(counterfactual_total - original_total, 6),
        "sector_details": details
    }}
    if cap_binding is not None:
        result["cap_binding"] = cap_binding
        result["cap_pct"] = round(cap * 100, 2)
    return result
$$;
"""
    session.sql(tool_sql).collect()
    log_detail("  Created: RUN_COUNTERFACTUAL_ANALYSIS")
