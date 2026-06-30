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
M&A Simulation Tool for SAM Demo

Models the financial impact of potential acquisitions using
firm-specific assumptions for cost synergies and integration costs.

Used by: Executive Copilot for strategic M&A analysis
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_error


def create_ma_simulation_tool(session: Session):
    """
    Create M&A simulation tool for executive scenario.
    
    This tool models the financial impact of potential acquisitions using
    firm-specific assumptions for cost synergies and integration costs.
    
    Used by: Executive Copilot for strategic M&A analysis
    Inputs: Target AUM, target revenue, cost synergy percentage
    Outputs: EPS accretion, synergy value, timeline, risk factors
    """
    ma_simulation_sql = f"""
CREATE OR REPLACE FUNCTION {config.DATABASE['name']}.AI.MA_SIMULATION_TOOL(
    target_aum FLOAT,
    target_revenue FLOAT,
    cost_synergy_pct FLOAT DEFAULT 0.20
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'simulate_acquisition'
AS
$$
def simulate_acquisition(target_aum: float, target_revenue: float, cost_synergy_pct: float = 0.20) -> dict:
    \"\"\"
    Simulate the financial impact of an acquisition on Simulated Asset Management.
    
    This model uses SAM's standard acquisition assumptions:
    - Integration costs: $30M one-time (standard for mid-sized deals)
    - Operating margin: 35% (SAM's current margin)
    - Cost synergy realization: 70% in Year 1, 100% by Year 2
    - Revenue synergy: Conservative 2% cross-sell uplift
    - SAM baseline EPS: $2.50 (illustrative)
    - SAM shares outstanding: 50M (illustrative)
    
    Args:
        target_aum: Target company AUM in USD (e.g., 50000000000 for $50B)
        target_revenue: Target company annual revenue in USD
        cost_synergy_pct: Expected cost synergy as decimal (default 0.20 = 20%)
    
    Returns:
        Dict with simulation results including EPS accretion, synergy value, timeline
    \"\"\"
    
    # SAM baseline assumptions (illustrative for demo)
    sam_baseline_eps = 2.50  # Current EPS
    sam_shares_outstanding = 50_000_000  # 50M shares
    sam_current_aum = 12_500_000_000  # $12.5B AUM
    sam_operating_margin = 0.35  # 35% operating margin
    
    # Integration assumptions
    integration_cost_one_time = 30_000_000  # $30M one-time
    year1_synergy_realization = 0.70  # 70% of synergies realized in Year 1
    revenue_synergy_pct = 0.02  # 2% cross-sell uplift
    
    # Calculate target operating income
    target_operating_income = target_revenue * sam_operating_margin
    
    # Calculate synergies
    cost_synergies_full = target_revenue * cost_synergy_pct
    cost_synergies_year1 = cost_synergies_full * year1_synergy_realization
    revenue_synergies = target_revenue * revenue_synergy_pct
    
    # Year 1 contribution (after integration costs)
    year1_contribution = (
        target_operating_income +
        cost_synergies_year1 +
        (revenue_synergies * sam_operating_margin) -
        integration_cost_one_time
    )
    
    # Year 2 contribution (full synergies, no integration costs)
    year2_contribution = (
        target_operating_income +
        cost_synergies_full +
        (revenue_synergies * sam_operating_margin)
    )
    
    # EPS impact (assuming cash deal, no share dilution)
    eps_impact_year1 = year1_contribution / sam_shares_outstanding
    eps_impact_year2 = year2_contribution / sam_shares_outstanding
    
    # EPS accretion percentage
    eps_accretion_year1_pct = (eps_impact_year1 / sam_baseline_eps) * 100
    eps_accretion_year2_pct = (eps_impact_year2 / sam_baseline_eps) * 100
    
    # Combined AUM
    combined_aum = sam_current_aum + target_aum
    aum_growth_pct = (target_aum / sam_current_aum) * 100
    
    # Risk factors based on deal size
    risk_level = "Low" if target_aum < 5_000_000_000 else "Medium" if target_aum < 20_000_000_000 else "High"
    
    return {{
        "simulation_summary": {{
            "target_aum_billions": round(target_aum / 1_000_000_000, 1),
            "target_revenue_millions": round(target_revenue / 1_000_000, 1),
            "cost_synergy_assumption_pct": cost_synergy_pct * 100
        }},
        "year1_projection": {{
            "eps_accretion_pct": round(eps_accretion_year1_pct, 1),
            "eps_impact_usd": round(eps_impact_year1, 2),
            "synergies_realized_millions": round(cost_synergies_year1 / 1_000_000, 1),
            "integration_costs_millions": round(integration_cost_one_time / 1_000_000, 1),
            "net_contribution_millions": round(year1_contribution / 1_000_000, 1)
        }},
        "year2_projection": {{
            "eps_accretion_pct": round(eps_accretion_year2_pct, 1),
            "eps_impact_usd": round(eps_impact_year2, 2),
            "full_synergies_millions": round(cost_synergies_full / 1_000_000, 1),
            "net_contribution_millions": round(year2_contribution / 1_000_000, 1)
        }},
        "strategic_impact": {{
            "combined_aum_billions": round(combined_aum / 1_000_000_000, 1),
            "aum_growth_pct": round(aum_growth_pct, 1),
            "revenue_synergies_millions": round(revenue_synergies / 1_000_000, 1)
        }},
        "risk_assessment": {{
            "integration_risk_level": risk_level,
            "key_risks": [
                "Client retention during transition",
                "Key personnel retention",
                "System integration complexity",
                "Regulatory approval timeline"
            ],
            "timeline_months": 12 if risk_level == "Low" else 18 if risk_level == "Medium" else 24
        }},
        "recommendation": f"Based on {{round(eps_accretion_year1_pct, 1)}}% Year 1 EPS accretion, this acquisition appears financially attractive. Recommend detailed due diligence focusing on client retention and integration planning."
    }}
$$;
    """
    try:
        session.sql(ma_simulation_sql).collect()
    except Exception as e:
        log_error(f" M&A simulation tool creation failed: {e}")
