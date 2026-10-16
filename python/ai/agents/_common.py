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

RESPONSE_STANDARDS = (
    "Response Standards (apply to every answer):\n"
    "- Currency: the base currency is USD. Show monetary amounts with \"$\" (e.g. $4.95M, $1.2bn). "
    "UK English applies to spelling only - never write £ or GBP for USD amounts, and only use another "
    "currency symbol when the data itself is denominated in that currency.\n"
    "- Charts: if a chart helps, call data_to_chart straight after the query whose results it plots and "
    "before writing the narrative that discusses it. Never mention, correct or apologise for a chart in the "
    "text, never say a chart was mislinked or not generated, and never call data_to_chart again after the "
    "answer is written. If no chart was produced, simply do not refer to one.\n"
    "- Close: end every answer with one or two brief, specific next steps you can do (e.g. a drill-down, "
    "a related check or a report), placed immediately before the demo disclaimer."
)

ORG_CONTEXT = (
    "Organization Context:\n"
    "- Simulated Asset Management (SAM) is a multi-asset investment firm\n"
    "- Manages $7.4bn AUM across 11 portfolios spanning 6 investment strategies (Value, Growth, Core, ESG, Multi-Asset, Income)\n"
    "- FCA-regulated with quarterly compliance reviews and daily risk monitoring\n"
    "- DATA GRAIN: holdings and positions are MONTH-END, not daily. The most recent holding date is the "
    "latest month-end, which is normally the month before today. Market prices, rates and FX are daily. "
    "Never assume a mid-month position date exists — if a holdings query returns nothing, fall back to the "
    "latest available month-end rather than reporting no data."
)

# Shared data-grain reminder for per-agent error-handling blocks, so the monthly
# position grain is stated identically everywhere instead of three conflicting
# "refreshes daily at N PM ET" claims.
POSITION_GRAIN_NOTE = (
    "Holdings and positions are month-end only; the latest available date is the most recent month-end. "
    "Retry with the latest month-end before concluding there is no data."
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
        'comprehensive-client-briefing',
        'quarterly-client-letter', 'client-review-preparation',
        'rfp-response-preparation', 'regulatory-lookup',
        'audience-format-adaptation', 'multi-level-attribution',
    ],
    'risk_compliance': [
        'pdf-report-generation', 'regulatory-lookup',
        'esg-mandate-compliance', 'concentration-risk-assessment',
        'event-driven-risk-verification',
        'audience-format-adaptation',
    ],
    'research': [
        'pdf-report-generation', 'investment-memo-generation',
        'equity-research-report', 'audience-format-adaptation',
        'earnings-intelligence', 'competitive-intelligence',
        'insider-institutional-analysis',
    ],
    'operations': [
        'pdf-report-generation', 'audience-format-adaptation',
    ],
    'executive_leadership': [
        'pdf-report-generation', 'portfolio-name-resolution',
        'executive-kpi-briefing', 'competitor-ma-analysis',
        'data-lineage-explanation', 'audience-format-adaptation',
        'attribution-report-generator',
    ],
    'private_equity': [
        'audience-format-adaptation',
    ],
    'private_credit': [
        'credit-risk-calculator', 'audience-format-adaptation',
        'covenant-monitoring', 'rate-sensitivity-analysis',
        'deal-pipeline-screening', 'credit-portfolio-review',
    ],
    'portfolio_management': [
        'portfolio-name-resolution', 'multi-level-attribution',
        'attribution-report-generator', 'counterfactual-analysis',
        'attribution-anomaly-scan', 'stress-scenario-analysis',
        'concentration-risk-assessment', 'implementation-planning',
        'audience-format-adaptation', 'pdf-report-generation',
        'data-lineage-explanation',
        'multi-factor-screening-strategy',
        'portfolio-construction', 'historical-backtest',
        'monte-carlo-simulation', 'portfolio-optimizer',
        'factor-model-explorer',
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
          type: "datetime"
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
          searchable: false
          filterable: true
        COMPANY_NAME:
          description: "Company name as spelled by the transcript provider, often several spellings per company (NVIDIA CORP and NVIDIA CORPORATION, ELI LILLY & CO and ELI LILLY AND COMPANY), so filtering on it misses events. Filter by TICKER instead; use this column for display only."
          type: "string"
          searchable: true
          filterable: true
        GICS_SECTOR:
          description: "GICS sector classification (e.g. Information Technology, Health Care)"
          type: "string"
          searchable: false
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
          type: "datetime"
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
          description: "Company legal name exactly as stored, e.g. NVIDIA CORP, MICROSOFT CORP, ELI LILLY & CO; informal names such as Nvidia or Lilly do not match. Prefer filtering by TICKER; filter on this column only with the exact stored legal name."
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
          type: "datetime"
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
          description: "Company legal name exactly as stored, e.g. NVIDIA CORP, MICROSOFT CORP, ELI LILLY & CO; informal names such as Nvidia or Lilly do not match. Prefer filtering by TICKER; filter on this column only with the exact stored legal name."
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
          type: "datetime"
          searchable: false
          filterable: true
        LANGUAGE:
          description: "Document language code"
          type: "string"
          searchable: false
          filterable: true"""
    },
    "SAM_PE_DUE_DILIGENCE": {
        "columns": """
        DOCUMENT_TEXT:
          description: "Full text content of the due diligence document chunk"
          type: "string"
          searchable: true
          filterable: false
        DOCUMENT_TITLE:
          description: "Document title"
          type: "string"
          searchable: true
          filterable: true
        TARGETCOMPANYNAME:
          description: "Name of the deal target company"
          type: "string"
          searchable: true
          filterable: true
        DEALID:
          description: "Numeric deal identifier (e.g. 101, 201), matching DealID in the deal pipeline view"
          type: "string"
          searchable: false
          filterable: true
        DOCUMENT_TYPE:
          description: "Document type: Confidential Information Memorandum, Vendor Due Diligence Report, Management Presentation, Commercial Due Diligence Summary"
          type: "string"
          searchable: false
          filterable: true"""
    },
    "SAM_PE_BOARD_PACKS": {
        "columns": """
        DOCUMENT_TEXT:
          description: "Full text content of the board pack chunk"
          type: "string"
          searchable: true
          filterable: false
        DOCUMENT_TITLE:
          description: "Document title"
          type: "string"
          searchable: true
          filterable: true
        COMPANYNAME:
          description: "Name of the portfolio company"
          type: "string"
          searchable: true
          filterable: true
        PORTFOLIOCOMPANYID:
          description: "Numeric portfolio company identifier, matching PortfolioCompanyID in the PE views"
          type: "string"
          searchable: false
          filterable: true
        DOCUMENT_TYPE:
          description: "Document type (Monthly Board Pack)"
          type: "string"
          searchable: false
          filterable: true
        REPORTPERIOD:
          description: "Month the board pack reports on"
          type: "datetime"
          searchable: false
          filterable: true"""
    },
    "SAM_PE_EXPERT_NETWORK": {
        "columns": """
        DOCUMENT_TEXT:
          description: "Full text content of the expert call transcript chunk"
          type: "string"
          searchable: true
          filterable: false
        DOCUMENT_TITLE:
          description: "Document title"
          type: "string"
          searchable: true
          filterable: true
        TARGETCOMPANYNAME:
          description: "Company discussed on the expert call"
          type: "string"
          searchable: true
          filterable: true
        EXPERTROLE:
          description: "Expert's background: Former CEO, Industry Consultant, Former Customer Executive"
          type: "string"
          searchable: true
          filterable: true
        DEALID:
          description: "Numeric deal identifier the call relates to, if any"
          type: "string"
          searchable: false
          filterable: true
        PORTFOLIOCOMPANYID:
          description: "Numeric portfolio company identifier the call relates to, if any"
          type: "string"
          searchable: false
          filterable: true
        CALLDATE:
          description: "Date the expert call took place"
          type: "datetime"
          searchable: false
          filterable: true"""
    },
}


PDF_SOURCE_STAGES = {
    "SAM_INTERNAL_DOCS": "PDF_INTERNAL_STAGE",
    "SAM_EXTERNAL_DOCS": "PDF_EXTERNAL_STAGE",
    "SAM_REGULATORY_DOCS": "PDF_REGULATORY_STAGE",
}


def build_search_tool_resource(tool_name, service_key, database_name, max_results=100):
    cfg = SEARCH_COLUMN_CONFIGS[service_key]
    source = ""
    if service_key in PDF_SOURCE_STAGES:
        raw_schema = config.DATABASE['schemas']['raw']
        source = f"""
      stage_path: "@{database_name}.{raw_schema}.{PDF_SOURCE_STAGES[service_key]}"
      relative_path_column: "SOURCE_FILE_PATH\""""
    return f"""    {tool_name}:
      search_service: "{database_name}.AI.{service_key}"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"{source}
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
        description: "Generates professional branded PDF reports from markdown content. Use ONLY when user EXPLICITLY requests PDF output, or asks to generate or create an IC (investment committee) memo."
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


def warn_if_cowork_object_exists(session: Session) -> None:
    """
    Warn when the account has a Snowflake CoWork object.

    Without one, CoWork lists every agent the user's role can use, which is how the
    demo controls visibility. Once an object exists, CoWork lists only the agents added
    to it, so the demo agents stay hidden until someone adds them.
    """
    try:
        rows = session.sql("SHOW SNOWFLAKE INTELLIGENCES").collect()
    except Exception as e:
        log_warning(f"  Could not check for a Snowflake CoWork object: {e}")
        return
    if not rows:
        return
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    for row in rows:
        name = row['name']
        log_warning(
            f"  This account has a Snowflake CoWork object ({name}). CoWork only shows the "
            f"agents added to it, so the demo agents are not visible until you add them:"
        )
        log_warning(f"    ALTER SNOWFLAKE INTELLIGENCE {name} ADD AGENT {database_name}.{ai_schema}.<agent_name>;")


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


