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
Research Copilot agent for SAM Demo.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_warning, log_error
from ai.agents._common import (
    format_instructions_for_yaml,
    build_search_tool_resource,
    build_analyst_tool_resource,
    build_generic_tool_resource,
    build_skills_yaml,
    common_tool_specs,
    common_tool_resources,
    pdf_generator_tool_spec,
    pdf_generator_tool_resource,
    DEMO_DISCLAIMER,
    AGENT_SKILLS,
)


def get_research_copilot_response_instructions():
    return f"""Style:
- Tone: Technical, detail-rich, analytical for research analysts
- Lead With: Financial data first, then qualitative context, then synthesis
- Terminology: US financial reporting terms (GAAP, SEC filings, 10-K/10-Q) with UK English spelling
- Precision: Financial metrics to 2 decimal places, percentages to 1 decimal, exact fiscal periods
- Limitations: Clearly state if company is non-US or private (SEC data unavailable)
- Scope Boundary: Company-level analysis ONLY - redirect portfolio questions to Portfolio Copilot

Formatting Rules:
- Label paragraphs as [FACT], [ANALYSIS], or [INFERENCE]
- Use precise dates (not 'recently' or 'current')
- Quantify claims with sources
- Note uncertainty and missing data explicitly

PDF Output (ONLY when explicitly requested):
Do NOT generate PDFs automatically. Only when user says 'generate a PDF', 'create a PDF report', etc.

PDF Download Link (REQUIRED when PDF is generated):
When you call pdf_generator, ALWAYS include the returned download link verbatim.

{DEMO_DISCLAIMER}"""


def get_research_copilot_orchestration_instructions():
    return """Business Context:
- Research analysts conducting fundamental company analysis
- Focus on US public companies with SEC filing data (14,000+ securities)
- Research supports investment decisions but does NOT include portfolio position data

Workflow Orchestration (handled by skills — load via server_skill):
- Equity research reports (10-section institutional format): Load equity-research-report skill
- Investment memos (7-section thesis + risk + catalysts): Load investment-memo-generation skill
- Earnings analysis (quarterly deep-dive with sentiment): Load earnings-intelligence skill
- Competitive analysis (peer comparison + moat): Load competitive-intelligence skill
- Insider/institutional ownership analysis: Load insider-institutional-analysis skill
- Audience adaptation (CIO/PM/Client formatting): Load audience-adaptive-narrative skill
- PDF generation (branded export): Load pdf-report-generation skill

Tool Selection (which tool for which data — skills handle the workflow sequence):
1. ALL structured financial data (SEC financials, segments, fundamentals, analyst estimates, insider trading, institutional holdings): research_analyzer
2. SEC FILING TEXT (10-K, 10-Q, 8-K): search_sec_filings
3. Analyst research opinions: search_external_docs (filter: broker_research)
4. Management commentary: search_company_events
5. Corporate developments: search_external_docs (filter: press_releases)
6. Redirect portfolio questions to Portfolio Copilot

Default Lookback: 3 years annual + 4 quarters quarterly unless user specifies otherwise.

Error Handling:

Scenario 1: Company Not in SEC Database
User Message: "SEC filing data not available. May be non-US or private company."

Scenario 2: No Analyst Coverage
User Message: "No analyst estimates found. I can provide SEC filing fundamentals."

Scenario 3: Stale Data
User Message: "Most recent SEC filing is from [date]. More recent data may be available in earnings transcripts.\""""


def create_research_copilot(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    response_formatted = format_instructions_for_yaml(get_research_copilot_response_instructions())
    orchestration_formatted = format_instructions_for_yaml(get_research_copilot_orchestration_instructions())

    analyst_research = build_analyst_tool_resource("research_analyzer", "SAM_RESEARCH_VIEW", database_name)
    search_external = build_search_tool_resource("search_external_docs", "SAM_EXTERNAL_DOCS", database_name, max_results=150)
    search_events = build_search_tool_resource("search_company_events", "SAM_COMPANY_EVENTS", database_name, max_results=150)
    search_sec = build_search_tool_resource("search_sec_filings", "SAM_REAL_SEC_FILINGS", database_name, max_results=150)
    pdf_resource = pdf_generator_tool_resource(database_name)
    thesis_resource = build_generic_tool_resource(
        "thesis_manager", "SP_UPSERT_RESEARCH_THESIS",
        "SP_UPSERT_RESEARCH_THESIS(NUMBER, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, NUMBER, NUMBER, NUMBER)",
        database_name, timeout=30
    )
    common_resources = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS['research'], database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_research_copilot
  COMMENT = 'Equity research and company analysis: synthesise earnings calls, SEC filings, broker research, consensus estimates, institutional ownership, and generate investment memos with thesis tracking.'
  PROFILE = '{{"display_name": "Research Co-Pilot (AM Demo)"}}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: {config.AGENT_ORCHESTRATION_MODEL}
  orchestration:
    budget:
      seconds: {config.AGENT_BUDGET_SECONDS}
      tokens: {config.AGENT_BUDGET_TOKENS}
  instructions:
    system: "You are an expert investment research analyst at a UK-based asset management firm. You conduct comprehensive company analysis combining fundamental data, SEC filings, analyst research, and management commentary."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "Give me a comprehensive research overview of NVIDIA"
        answer: "I will analyse NVIDIA across fundamentals, SEC filings, analyst research, and earnings commentary."
      - question: "What are the key risks for Apple according to SEC filings?"
        answer: "I will search Apple 10-K risk factors and MD&A disclosures."
      - question: "Show me NVIDIA revenue by segment over the last 3 years"
        answer: "I will use the segment analyzer to query SEC-filed segment revenue data."
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "research_analyzer"
        description: "All structured company research data: SEC financials (revenue, EPS, margins from 10-K/10-Q), segment/geographic revenue, analyst estimates and consensus, insider trading (Form 4), institutional holdings (13F). 500+ US public companies, 5 years data, 2 years forward estimates."
    - tool_spec:
        type: "cortex_search"
        name: "search_external_docs"
        description: "Broker research and press releases. Filter by DOCUMENT_TYPE: broker_research, press_releases. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_company_events"
        description: "Earnings call transcripts with speaker attribution. Filter by EVENT_TYPE, SPEAKER_ROLE. IMPORTANT: always use persist_to_table."

    - tool_spec:
        type: "cortex_search"
        name: "search_sec_filings"
        description: "SEC filing text (10-K, 10-Q, 8-K): MD&A, risk factors, disclosures. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "generic"
        name: "thesis_manager"
        description: "Create or update an investment thesis. Use when analyst explicitly asks to save, create, or update a thesis. Parameters: issuerid (number), ticker, company_name, thesis_title, thesis_summary, recommendation (BUY/HOLD/SELL), conviction (HIGH/MEDIUM/LOW), key_assumptions (JSON array of objects with assumption/status/evidence), stage (SCREENING/RESEARCH/THESIS_DRAFT/ACTIVE), health_status (GREEN/AMBER/RED), entry_price, target_price, stop_loss."
        input_schema:
          type: "object"
          properties:
            p_issuerid:
              description: "Company ISSUERID from DIM_ISSUER"
              type: "number"
            p_ticker:
              description: "Stock ticker symbol"
              type: "string"
            p_company_name:
              description: "Full company name"
              type: "string"
            p_thesis_title:
              description: "Concise thesis title"
              type: "string"
            p_thesis_summary:
              description: "Thesis summary (500 words max)"
              type: "string"
            p_recommendation:
              description: "BUY, HOLD, or SELL"
              type: "string"
            p_conviction:
              description: "HIGH, MEDIUM, or LOW"
              type: "string"
            p_key_assumptions:
              description: "JSON array of key assumptions"
              type: "string"
            p_stage:
              description: "Pipeline stage: SCREENING, RESEARCH, THESIS_DRAFT, ACTIVE"
              type: "string"
            p_health_status:
              description: "GREEN, AMBER, or RED"
              type: "string"
            p_entry_price:
              description: "Entry price target"
              type: "number"
            p_target_price:
              description: "Target price"
              type: "number"
            p_stop_loss:
              description: "Stop loss price"
              type: "number"
          required:
            - p_issuerid
            - p_ticker
            - p_company_name
            - p_thesis_title
            - p_thesis_summary
{pdf_generator_tool_spec()}

  tool_resources:
{common_resources}
{analyst_research}
{search_external}
{search_events}
{search_sec}
{pdf_resource}
{thesis_resource}
  $$;
"""
    session.sql(sql).collect()
