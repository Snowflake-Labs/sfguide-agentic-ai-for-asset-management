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
Shared utilities and tool builders for agent creation.

Provides reusable YAML fragments for Cortex Search, Cortex Analyst, and common
tools (server_skill, data_to_chart, pdf_generator, explain_data_origin) to
eliminate duplication across the 14 agent modules.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_warning, log_error


DEMO_DISCLAIMER = (
    "Demo Disclaimer (REQUIRED at end of every response):\n"
    "---\n"
    "*DEMO DISCLAIMER: This analysis uses synthetic data for demonstration purposes only. "
    "Not intended for actual investment decisions.*"
)

ORG_CONTEXT = (
    "Organization Context:\n"
    "- Simulated Asset Management (SAM) is a multi-asset investment firm\n"
    "- Manages £2.5B AUM across 10 active investment strategies (growth, value, ESG, thematic)\n"
    "- FCA-regulated with quarterly compliance reviews and daily risk monitoring\n"
    "- Data refreshes daily at market close (4 PM ET) with 2-hour processing lag"
)

PORTFOLIO_NAME_MAPPING = (
    "CRITICAL - Portfolio Name Handling:\n"
    "All portfolio names start with \"SAM \" prefix. When the user mentions a portfolio by name or alias, "
    "ALWAYS use the FULL name (with SAM prefix) in your question to Cortex Analyst tools.\n\n"
    "Portfolio name mapping:\n"
    "- \"Tech\", \"Technology\", \"Technology & Infrastructure\" -> SAM Technology & Infrastructure\n"
    "- \"ESG\", \"ESG Leaders\" -> SAM ESG Leaders Global Equity\n"
    "- \"Flagship\", \"Global Flagship\" -> SAM Global Flagship Multi-Asset\n"
    "- \"Core\", \"US Core\" -> SAM US Core Equity\n"
    "- \"Climate\", \"Renewable\" -> SAM Renewable & Climate Solutions\n"
    "- \"Sustainable\" -> SAM Sustainable Global Equity\n"
    "- \"AI\", \"Digital\", \"Digital Innovation\" -> SAM AI & Digital Innovation\n"
    "- \"Balanced\", \"60/40\" -> SAM Global Balanced 60/40\n"
    "- \"Tech Disruptors\" -> SAM Tech Disruptors Equity\n"
    "- \"Value\", \"US Value\" -> SAM US Value Equity\n"
    "- \"Income\", \"Multi-Asset Income\" -> SAM Multi-Asset Income"
)

AGENT_SKILLS = {
    'client_advisory': [
        'pdf-report-generation', 'portfolio-name-resolution',
        'quarterly-client-letter', 'client-review-preparation',
        'rfp-response-preparation', 'regulatory-lookup',
        'audience-adaptive-narrative', 'multi-level-attribution',
    ],
    'risk_compliance': [
        'pdf-report-generation', 'regulatory-lookup',
        'esg-mandate-compliance', 'concentration-risk-assessment',
        'audience-adaptive-narrative',
    ],
    'research': [
        'pdf-report-generation', 'investment-memo-generation',
        'equity-research-report', 'audience-adaptive-narrative',
        'earnings-intelligence', 'competitive-intelligence',
        'insider-institutional-analysis',
    ],
    'investment_strategy': [
        'factor-model-explorer', 'regulatory-lookup',
        'audience-adaptive-narrative',
    ],
    'operations': [
        'pdf-report-generation', 'audience-adaptive-narrative',
    ],
    'executive_leadership': [
        'pdf-report-generation', 'portfolio-name-resolution',
        'executive-briefing', 'competitor-ma-analysis',
        'data-lineage-explanation', 'audience-adaptive-narrative',
        'attribution-report-generator',
    ],
    'portfolio_modelling_copilot': [
        'historical-backtest', 'monte-carlo-simulation',
        'multi-level-attribution', 'counterfactual-analysis',
        'portfolio-optimizer', 'audience-adaptive-narrative',
    ],
    'private_equity': [
        'audience-adaptive-narrative',
    ],
    'pe_deal_sourcing': [
        'audience-adaptive-narrative',
    ],
    'pe_portfolio_monitor': [
        'audience-adaptive-narrative',
    ],
    'private_credit': [
        'credit-risk-calculator', 'audience-adaptive-narrative',
        'covenant-monitoring', 'rate-sensitivity-analysis',
        'deal-pipeline-screening', 'credit-portfolio-review',
    ],
    'portfolio_management': [
        'portfolio-name-resolution', 'multi-level-attribution',
        'attribution-report-generator', 'counterfactual-analysis',
        'attribution-anomaly-scan', 'stress-scenario-analysis',
        'concentration-risk-assessment', 'implementation-planning',
        'audience-adaptive-narrative', 'pdf-report-generation',
        'data-lineage-explanation',
        'portfolio-construction', 'historical-backtest',
        'monte-carlo-simulation', 'portfolio-optimizer',
    ],
}


SEARCH_COLUMN_CONFIGS = {
    "SAM_COMPANY_EVENTS": {
        "columns": """
        DOCUMENT_TEXT:
          description: "Full text content of the document chunk"
          type: "string"
          searchable: true
          filterable: false
        PUBLISH_DATE:
          description: "Date the event occurred"
          type: "date"
          searchable: false
          filterable: true
        EVENT_TYPE:
          description: "Type of company event (Earnings Call, AGM, Investor Day, Capital Markets Day, etc.)"
          type: "string"
          searchable: true
          filterable: true
        TICKER:
          description: "Stock ticker symbol, use to filter by company (e.g. NVDA, MSFT, AAPL)"
          type: "string"
          searchable: true
          filterable: true
        COMPANY_NAME:
          description: "Company name, use to filter by company (e.g. NVIDIA, Microsoft, Apple)"
          type: "string"
          searchable: true
          filterable: true
        GICS_SECTOR:
          description: "GICS sector classification (e.g. Information Technology, Health Care)"
          type: "string"
          searchable: true
          filterable: true
        SPEAKER_NAME:
          description: "Name of the speaker in the event transcript"
          type: "string"
          searchable: true
          filterable: true
        SPEAKER_ROLE:
          description: "Role of the speaker (CEO, CFO, Analyst, etc.)"
          type: "string"
          searchable: false
          filterable: true
        FISCAL_YEAR:
          description: "Fiscal year of the event (e.g. 2024, 2025)"
          type: "string"
          searchable: false
          filterable: true
        FISCAL_PERIOD:
          description: "Fiscal period of the event (e.g. Q1, Q2, Q3, Q4, FY, H1, H2)"
          type: "string"
          searchable: false
          filterable: true"""
    },
    "SAM_EXTERNAL_DOCS": {
        "columns": """
        DOCUMENT_TEXT:
          description: "Full text content of the document chunk"
          type: "string"
          searchable: true
          filterable: false
        DOCUMENT_TYPE:
          description: "Document category, used for filtering (e.g. broker_research, press_releases)"
          type: "string"
          searchable: false
          filterable: true
        PUBLISH_DATE:
          description: "Date the document was published"
          type: "date"
          searchable: false
          filterable: true
        LANGUAGE:
          description: "Document language code"
          type: "string"
          searchable: false
          filterable: true
        TICKER:
          description: "Stock ticker symbol, use to filter by company (e.g. NVDA, MSFT, AAPL)"
          type: "string"
          searchable: true
          filterable: true
        COMPANY_NAME:
          description: "Company name, use to filter by company (e.g. NVIDIA, Microsoft, Apple)"
          type: "string"
          searchable: true
          filterable: true
        GICS_SECTOR:
          description: "GICS sector classification (e.g. Information Technology, Health Care)"
          type: "string"
          searchable: true
          filterable: true"""
    },
    "SAM_INTERNAL_DOCS": {
        "columns": """
        DOCUMENT_TEXT:
          description: "Full text content of the document chunk"
          type: "string"
          searchable: true
          filterable: false
        DOCUMENT_TYPE:
          description: "Document category, used for filtering (e.g. policy_docs, report_templates, macro_events, ips)"
          type: "string"
          searchable: false
          filterable: true
        PUBLISH_DATE:
          description: "Date the document was published"
          type: "date"
          searchable: false
          filterable: true
        LANGUAGE:
          description: "Document language code"
          type: "string"
          searchable: false
          filterable: true
        TICKER:
          description: "Stock ticker symbol, use to filter by company (e.g. NVDA, MSFT, AAPL)"
          type: "string"
          searchable: true
          filterable: true
        COMPANY_NAME:
          description: "Company name, use to filter by company (e.g. NVIDIA, Microsoft, Apple)"
          type: "string"
          searchable: true
          filterable: true
        GICS_SECTOR:
          description: "GICS sector classification (e.g. Information Technology, Health Care)"
          type: "string"
          searchable: true
          filterable: true"""
    },
    "SAM_REAL_SEC_FILINGS": {
        "columns": """
        FILING_TEXT:
          description: "Full text content of the SEC filing section"
          type: "string"
          searchable: true
          filterable: false
        DOCUMENT_TITLE:
          description: "Human-readable title combining company, ticker, filing type, fiscal period, and section"
          type: "string"
          searchable: true
          filterable: false
        COMPANY_NAME:
          description: "Legal name of the filing company"
          type: "string"
          searchable: true
          filterable: true
        TICKER:
          description: "Stock ticker symbol"
          type: "string"
          searchable: true
          filterable: true
        GICS_SECTOR:
          description: "GICS sector classification"
          type: "string"
          searchable: true
          filterable: true
        FILING_TYPE:
          description: "SEC filing type (10-K, 10-Q, 8-K, DEF 14A, SEC Filing)"
          type: "string"
          searchable: true
          filterable: true
        FISCAL_YEAR:
          description: "Fiscal year of the filing period"
          type: "string"
          searchable: false
          filterable: true
        FISCAL_QUARTER:
          description: "Fiscal quarter (Q1, Q2, Q3, Q4)"
          type: "string"
          searchable: false
          filterable: true
        VARIABLE_NAME:
          description: "SEC filing section name (e.g. Risk Factors, MD&A, Business Description)"
          type: "string"
          searchable: false
          filterable: true"""
    },
    "SAM_REGULATORY_DOCS": {
        "columns": """
        DOCUMENT_TEXT:
          description: "Full text content of the regulation chunk"
          type: "string"
          searchable: true
          filterable: false
        DOCUMENT_TYPE:
          description: "Document category (regulatory_docs)"
          type: "string"
          searchable: false
          filterable: true
        REGULATION_ID:
          description: "Unique regulation identifier (e.g. eu_sfdr, eu_mifid_ii, fca_consumer_duty)"
          type: "string"
          searchable: false
          filterable: true
        REGULATORY_BODY:
          description: "Issuing authority (e.g. European Parliament, Financial Conduct Authority)"
          type: "string"
          searchable: true
          filterable: true
        JURISDICTION:
          description: "Regulatory jurisdiction (EU, UK, US, International)"
          type: "string"
          searchable: false
          filterable: true
        REFERENCE:
          description: "Official regulation reference"
          type: "string"
          searchable: true
          filterable: true
        SOURCE_URL:
          description: "URL to original regulation source"
          type: "string"
          searchable: false
          filterable: false
        PUBLISH_DATE:
          description: "Effective date of the regulation"
          type: "date"
          searchable: false
          filterable: true
        LANGUAGE:
          description: "Document language code"
          type: "string"
          searchable: false
          filterable: true"""
    },
}


def build_search_tool_resource(tool_name, service_key, database_name, max_results=100):
    cfg = SEARCH_COLUMN_CONFIGS[service_key]
    return f"""    {tool_name}:
      search_service: "{database_name}.AI.{service_key}"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      is_multi_index: true
      max_results: {max_results}
      columns_and_descriptions:{cfg['columns']}"""


def build_analyst_tool_resource(tool_name, view_name, database_name, timeout=30):
    exec_wh = config.WAREHOUSES['execution']['name']
    return f"""    {tool_name}:
      execution_environment:
        query_timeout: {timeout}
        type: "warehouse"
        warehouse: "{exec_wh}"
      semantic_view: "{database_name}.AI.{view_name}\""""


def build_generic_tool_resource(tool_name, proc_identifier, proc_signature, database_name, timeout=30, tool_type="procedure"):
    exec_wh = config.WAREHOUSES['execution']['name']
    return f"""    {tool_name}:
      execution_environment:
        query_timeout: {timeout}
        type: "warehouse"
        warehouse: "{exec_wh}"
      identifier: "{database_name}.AI.{proc_identifier}"
      name: "{proc_signature}"
      type: "{tool_type}\""""


def common_tool_specs():
    return """    - tool_spec:
        type: "server_skill"
        name: "server_skill"
        description: "Load and execute a server-side skill to get specialized instructions and knowledge"
    - tool_spec:
        type: code_execution
        name: code_execution
    - tool_spec:
        type: "data_to_chart"
        name: "data_to_chart"
        description: "Generates visualizations from data\""""


def common_tool_resources():
    return """    server_skill:
      enabled_skills: ["system_unstructured_analytics_instructions"]
    code_execution:"""


def pdf_generator_tool_spec():
    return """    - tool_spec:
        type: "generic"
        name: "pdf_generator"
        description: "Generates professional branded PDF reports from markdown content. Use ONLY when user EXPLICITLY requests PDF output."
        input_schema:
          type: "object"
          properties:
            markdown_content:
              description: "Complete markdown document with all sections"
              type: "string"
            report_title:
              description: "Title for the document header"
              type: "string"
            document_audience:
              description: "'external_client' for client-facing, 'internal' for internal documents"
              type: "string"
          required:
            - markdown_content
            - report_title
            - document_audience"""


def pdf_generator_tool_resource(database_name):
    return build_generic_tool_resource(
        "pdf_generator", "GENERATE_PDF_REPORT",
        "GENERATE_PDF_REPORT(VARCHAR, VARCHAR, VARCHAR)",
        database_name, timeout=60
    )


def build_skills_yaml(skill_names, database_name):
    ai_schema = config.DATABASE['schemas']['ai']
    lines = ["  skills:"]
    for name in skill_names:
        lines.append(f'    - name: "{name}"')
        lines.append(f'      source:')
        lines.append(f'        type: "STAGE"')
        lines.append(f'        path: "@{database_name}.{ai_schema}.SKILL_STAGE/{name}"')
    return "\n".join(lines)


def verify_snowflake_intelligence(session: Session) -> bool:
    """
    Verify that Snowflake Intelligence exists.
    
    Returns:
        True if Snowflake Intelligence exists, False otherwise
    """
    try:
        result = session.sql("SHOW SNOWFLAKE INTELLIGENCES").collect()
        if len(result) == 0:
            log_error("No Snowflake Intelligence found")
            log_warning("Before creating agents, you must first create a Snowflake Intelligence object.")
            log_warning("Run: CREATE SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;")
            log_warning("See: https://docs.snowflake.com/en/user-guide/snowflake-intelligence")
            return False
        return True
    except Exception as e:
        log_error(f" Failed to check for Snowflake Intelligence: {e}")
        return False


def register_agent_with_intelligence(session: Session, database_name: str, ai_schema: str, agent_name: str) -> bool:
    """
    Register an agent with Snowflake Intelligence.
    First attempts to drop the agent (if it exists from previous run), then adds it.
    
    Args:
        session: Snowpark session
        database_name: Database name where agent was created
        ai_schema: AI schema name where agent was created
        agent_name: Name of the agent (e.g., 'AM_portfolio_copilot')
    
    Returns:
        True if registration succeeded, False otherwise
    """
    full_agent_path = f"{database_name}.{ai_schema}.{agent_name}"
    
    # Step 1: Try to drop the agent from Intelligence (suppress error if not found)
    try:
        session.sql(f"""
            ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT 
            DROP AGENT {full_agent_path}
        """).collect()
        # Agent was previously registered, successfully dropped
    except Exception as e:
        # Agent not found in Intelligence - this is OK, means first time registration
        error_msg = str(e).lower()
        if "was not found" not in error_msg and "does not exist" not in error_msg:
            # Some other error occurred - log it but continue
            log_warning(f"  Note: Could not drop agent {agent_name} from Intelligence: {e}")
    
    # Step 2: Add the agent to Intelligence
    try:
        session.sql(f"""
            ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT 
            ADD AGENT {full_agent_path}
        """).collect()
        return True
    except Exception as e:
        log_warning(f"  Warning: Failed to register agent {agent_name} with Snowflake Intelligence: {e}")
        return False


def escape_sql_string(text: str) -> str:
    """
    Escape single quotes in text for SQL string literals.
    Replace single quote (') with two single quotes ('').
    """
    return text.replace("'", "''")


def format_instructions_for_yaml(text: str) -> str:
    """
    Format multi-line instructions for YAML specification within SQL.
    - Replace tab characters with spaces
    - Replace actual line breaks with \\n
    - Escape double quotes with \\"
    Note: Single quotes do NOT need escaping because the spec is inside $$ delimiters.
    """
    formatted = text.replace('\t', '  ')
    formatted = formatted.replace('\n', '\\n')
    formatted = formatted.replace('"', '\\"')
    return formatted


