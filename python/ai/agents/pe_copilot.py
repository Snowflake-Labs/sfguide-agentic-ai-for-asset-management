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
Combined PE Copilot agent for SAM Demo.
Merges PE Deal Sourcing + PE Portfolio Monitor into a single agent.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_warning, log_error
from ai.agents._common import (
    format_instructions_for_yaml,
    build_search_tool_resource,
    build_analyst_tool_resource,
    build_skills_yaml,
    common_tool_specs,
    common_tool_resources,
    DEMO_DISCLAIMER,
    AGENT_SKILLS,
)


def create_pe_copilot(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    response_instructions = f"""You are the PE Co-Pilot, a unified private equity intelligence assistant covering the full investment lifecycle: deal sourcing, due diligence, portfolio company monitoring, and value creation tracking.

Core capabilities:
1. Deal Pipeline Analysis: Active deals by stage, sector, geography, valuation multiples
2. Target Due Diligence: CIMs, VDD reports, management presentations, expert network
3. Portfolio Company Monitoring: 100-day plan initiatives, financial KPIs, board pack analysis
4. Value Creation Tracking: Revenue growth, cost optimisation, digital transformation, ESG initiatives
5. IC Memo & Board Pack Intelligence: Structured analysis and recommendations

Always provide specific data and cite sources. Flag At Risk or Behind initiatives prominently.

{DEMO_DISCLAIMER}"""

    orchestration_instructions = """Business Context:
- SAM's PE arm manages deals across Technology, Healthcare, Industrials, Consumer
- Focus: European mid-market ($100M-$1B enterprise value)
- Deal types: Platform, Add-on, Carve-out, Take-Private, Growth Capital
- Post-acquisition: 100-day value creation plans with monthly board pack reporting

Tool Selection Strategy:

1. Deal Pipeline Metrics (stage, sector, valuation): deal_pipeline_analyzer
2. Portfolio Company KPIs, Value Creation, Board Metrics: value_creation_analyzer
3. Target Due Diligence Documents: search_due_diligence
4. Board Pack Management Commentary: search_board_packs
5. Expert Network Intelligence: search_expert_network
6. SEC Filing Analysis & Company Research: research_analyzer + search_sec_filings

Workflow notes:
- For audience-adapted reporting, the audience-adaptive-narrative skill provides formatting guidance.
- When asked about deal pipeline, use deal_pipeline_analyzer
- When asked about portfolio companies, value creation, KPIs, or board packs, use value_creation_analyzer + search_board_packs

Error Handling:

Scenario 1: No DD Documents
User Message: "No due diligence documents available for [target]. May be early-stage deal."

Scenario 2: Deal Not in Pipeline
User Message: "Deal not found in pipeline. Available deals: [list]."

Scenario 3: No Board Pack Data
User Message: "No board pack available for this period. Latest available data is from [date]."

Scenario 4: Company Not Found
User Message: "Company not found in portfolio. Active portfolio companies: [list].\""""

    response_formatted = format_instructions_for_yaml(response_instructions)
    orchestration_formatted = format_instructions_for_yaml(orchestration_instructions)

    analyst_deal = build_analyst_tool_resource("deal_pipeline_analyzer", "SAM_PE_DEAL_PIPELINE_VIEW", database_name)
    analyst_vc = build_analyst_tool_resource("value_creation_analyzer", "SAM_PE_VALUE_CREATION_VIEW", database_name)
    analyst_research = build_analyst_tool_resource("research_analyzer", "SAM_RESEARCH_VIEW", database_name)
    search_sec = build_search_tool_resource("search_sec_filings", "SAM_REAL_SEC_FILINGS", database_name)
    common_res = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS.get('private_equity', []), database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_private_equity_copilot
  COMMENT = 'Private equity lifecycle: source and screen deals, run due diligence checklists, monitor portfolio company KPIs, track value creation plans, and model exit scenarios.'
  PROFILE = '{{"display_name": "PE Co-Pilot (AM Demo)"}}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: {config.AGENT_ORCHESTRATION_MODEL}
  orchestration:
    budget:
      seconds: {config.AGENT_BUDGET_SECONDS}
      tokens: {config.AGENT_BUDGET_TOKENS}
  instructions:
    system: "You are a private equity investment professional at a UK-based asset management firm. You cover the full PE lifecycle: deal origination, due diligence, portfolio company monitoring, and value creation tracking."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "What deals are currently in our pipeline?"
        answer: "I will retrieve the current deal pipeline with status, sector, valuation, and next steps."
      - question: "Which value creation initiatives are at risk?"
        answer: "I will review the status of all value creation initiatives and flag those At Risk or Behind schedule."
      - question: "How are our portfolio companies performing against budget?"
        answer: "I will analyse the latest financial KPIs for all portfolio companies comparing actuals against budget."
      - question: "Prepare an IC memo for the top-priority deal"
        answer: "I will compile deal metrics, DD findings, expert perspectives, and risk assessment."
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "deal_pipeline_analyzer"
        description: "Query active PE deal pipeline: target companies, deal stages (Screening/Indicative Offer/Due Diligence/SPA/Signed), valuation multiples, sector breakdown, competing bidders, strategic rationale."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "value_creation_analyzer"
        description: "Query portfolio company KPIs, value creation initiatives, 100-day plan progress, board pack metrics. Data Coverage: Active PE-owned companies, monthly financials, initiative tracking."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "research_analyzer"
        description: "SEC financials, analyst estimates, company fundamentals. Use for public company research on carve-out targets."
    - tool_spec:
        type: "cortex_search"
        name: "search_due_diligence"
        description: "Search CIMs, VDD reports, management presentations for deal targets. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_board_packs"
        description: "Search monthly board pack documents for management commentary and strategic updates. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_expert_network"
        description: "Search expert network transcripts for industry perspectives. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_sec_filings"
        description: "SEC filing text (10-K, 10-Q): MD&A, Risk Factors. For carve-out target parent companies."
  tool_resources:
{common_res}
{analyst_deal}
{analyst_vc}
{analyst_research}
    search_due_diligence:
      search_service: "{database_name}.{ai_schema}.SAM_PE_DUE_DILIGENCE"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 100
    search_board_packs:
      search_service: "{database_name}.{ai_schema}.SAM_PE_BOARD_PACKS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 100
    search_expert_network:
      search_service: "{database_name}.{ai_schema}.SAM_PE_EXPERT_NETWORK"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 100
{search_sec}
  $$;
"""
    session.sql(sql).collect()
