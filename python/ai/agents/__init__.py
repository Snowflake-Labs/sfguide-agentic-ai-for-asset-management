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
Snowflake CoWork agent creation package for SAM Demo.

Split into one file per agent for maintainability.
"""

from snowflake.snowpark import Session
from typing import List, Dict
import config
from utils.logging import log_detail, log_warning, log_error, log_phase_complete
from ai.agents._common import (
    warn_if_cowork_object_exists,
    escape_sql_string,
    format_instructions_for_yaml,
)

from ai.agents.research_copilot import create_research_copilot
from ai.agents.risk_compliance import create_risk_compliance
from ai.agents.sales_advisor import create_sales_advisor
from ai.agents.middle_office_copilot import create_middle_office_copilot
from ai.agents.executive_copilot import create_executive_copilot
from ai.agents.pe_copilot import create_pe_copilot
from ai.agents.private_credit import create_private_credit_copilot
from ai.agents.pm_cockpit import create_pm_cockpit_agent

from ai.agents.research_copilot import get_research_copilot_response_instructions
from ai.agents.research_copilot import get_research_copilot_orchestration_instructions
from ai.agents.sales_advisor import get_sales_advisor_response_instructions
from ai.agents.sales_advisor import get_sales_advisor_orchestration_instructions


AGENT_CREATORS = {
    'portfolio_management': create_pm_cockpit_agent,
    'research': create_research_copilot,
    'risk_compliance': create_risk_compliance,
    'client_advisory': create_sales_advisor,
    'operations': create_middle_office_copilot,
    'executive_leadership': create_executive_copilot,
    'private_equity': create_pe_copilot,
    'private_credit': create_private_credit_copilot,
}


def create_all_agents(session: Session, scenarios: List[str] = None):
    """
    Create Snowflake CoWork agents for the specified scenarios.
    
    Only creates agents for scenarios that have an agent defined in config.SCENARIOS.
    """
    log_detail("Creating Snowflake CoWork agents...")
    
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    agent_scenarios = [
        s for s in (scenarios or config.get_agent_scenarios())
        if s in AGENT_CREATORS and config.SCENARIOS.get(s, {}).get('agent')
    ]
    
    if not agent_scenarios:
        log_detail("  No agents to create for the specified scenarios")
        return 0, 0
    
    created = []
    failed = []
    
    for scenario_key in agent_scenarios:
        try:
            AGENT_CREATORS[scenario_key](session)
            full_agent_name = config.SCENARIOS[scenario_key]['agent']['name']
            created.append(scenario_key)
            log_detail(f"Created agent: {full_agent_name}")
                
        except Exception as e:
            failed.append((scenario_key, str(e)))
            log_error(f" Failed to create agent {scenario_key}: {e}")
    
    log_phase_complete(f"Agents: {len(created)} created" + (f", {len(failed)} failed" if failed else ""))
    if failed:
        for agent_name, error in failed:
            log_error(f"{agent_name}: {error[:100]}...")

    if created:
        warn_if_cowork_object_exists(session)
    
    return len(created), len(failed)

