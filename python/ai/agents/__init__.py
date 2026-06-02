"""
Snowflake Intelligence agent creation package for SAM Demo.

Split into one file per agent for maintainability.
"""

from snowflake.snowpark import Session
from typing import List, Dict
import config
from utils.logging import log_detail, log_warning, log_error, log_phase_complete
from ai.agents._common import (
    verify_snowflake_intelligence,
    register_agent_with_intelligence,
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
    Create Snowflake Intelligence agents for the specified scenarios.
    
    Only creates agents for scenarios that have an agent defined in config.SCENARIOS.
    """
    log_detail("Creating Snowflake Intelligence agents...")
    
    if not verify_snowflake_intelligence(session):
        raise Exception("Snowflake Intelligence not found. Cannot create agents.")
    
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
            
            if register_agent_with_intelligence(session, database_name, ai_schema, full_agent_name):
                created.append(scenario_key)
                log_detail(f"Created and registered agent: {full_agent_name}")
            else:
                created.append(scenario_key)
                log_warning(f"  Agent created but registration failed: {full_agent_name}")
                
        except Exception as e:
            failed.append((scenario_key, str(e)))
            log_error(f" Failed to create agent {scenario_key}: {e}")
    
    log_phase_complete(f"Agents: {len(created)} created" + (f", {len(failed)} failed" if failed else ""))
    if failed:
        for agent_name, error in failed:
            log_error(f"{agent_name}: {error[:100]}...")
    
    return len(created), len(failed)


def cleanup_all_agents(session: Session):
    """
    Remove all SAM agents from Snowflake Intelligence before database drop.
    
    This function should be called before DROP DATABASE or CREATE OR REPLACE DATABASE
    to cleanly unregister agents from SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT.
    
    Errors are suppressed since agents may not exist (first-time setup or already removed).
    """
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    log_detail("Cleaning up agents from Snowflake Intelligence...")
    
    removed_count = 0
    for scenario_key, agent_info in config.SCENARIO_AGENTS.items():
        agent_name = agent_info['agent_name']
        full_agent_path = f"{database_name}.{ai_schema}.{agent_name}"
        
        try:
            session.sql(f"""
                ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT 
                DROP AGENT {full_agent_path}
            """).collect()
            log_detail(f"  Removed agent: {agent_name}")
            removed_count += 1
        except Exception:
            # Agent doesn't exist or already removed - continue silently
            pass
    
    if removed_count > 0:
        log_detail(f"  Cleaned up {removed_count} agents")

