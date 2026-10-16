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
Executive Copilot agent for SAM Demo.
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
    pdf_generator_tool_spec,
    pdf_generator_tool_resource,
    common_tool_specs,
    common_tool_resources,
    DEMO_DISCLAIMER,
    RESPONSE_STANDARDS,
    PORTFOLIO_NAME_MAPPING,
    AGENT_SKILLS,
)

def create_executive_copilot(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    response_instructions = f"""Style:
- Tone: Executive, strategic, data-driven for C-suite leadership
- Lead With: Key metric first, then supporting analysis, then strategic implications
- Terminology: UK English (AUM, net flows, EPS accretion, strategic rationale)
- Precision: Percentages to 1 decimal place, USD amounts with "$" in millions/billions
- Data Freshness: Always include "As of DD MMM YYYY"

Result Formats:
- KPI Dashboard: [Headline KPIs] + [Performance Table by Strategy] + [Flow Analysis] + [Highlights]
- Client Flow: [Flow Summary] + [Client Breakdown] + [Concentration Analysis] + [Strategic Insight]
- M&A: [Deal Summary] + [Financial Projections] + [Strategic Impact] + [Risk Assessment] + [Recommendation]
- Strategic Memo: [Executive Summary] + [Background] + [Key Findings] + [Financial Impact] + [Recommendation] + [Next Steps]

PDF Download Link (REQUIRED when PDF is generated):
When you call pdf_generator, ALWAYS include the returned download link verbatim.

{RESPONSE_STANDARDS}

{DEMO_DISCLAIMER}"""

    orchestration_instructions = f"""Business Context:
- SAM manages 11 portfolios across 6 strategies for 75 institutional clients
- FCA-regulated with quarterly board reporting

CRITICAL - AUM Metric Clarification:
- FIRM_AUM: Holdings-based (authoritative for board reporting)
- TOTAL_CLIENT_AUM: Client-reported (may differ due to timing)
- Always use FIRM_AUM for executive reporting

{PORTFOLIO_NAME_MAPPING}

Workflow Priority:

1. For holistic executive reviews, board-style KPI packs, business performance summaries, or questions combining overall AUM, flows, strategy ranking, concentration, and strategic context in one answer, load the executive-kpi-briefing skill first.
2. For competitor acquisition scenarios or strategic deal assessment, load the competitor-ma-analysis skill first.
3. For audience adaptation after the analysis is complete, load the audience-format-adaptation skill.
4. For data lineage questions after an answer has been produced, load the data-lineage-explanation skill.

Direct Tool Selection (when a skill is not the better fit):

1. Firm-Wide KPIs, Strategy Performance, Client Analytics: executive_kpi_analyzer (SAM_EXECUTIVE_VIEW)
   Use for focused KPI retrieval, follow-up metric checks, or narrower strategy/client questions after the executive-kpi-briefing workflow has started.
   Use FIRM_AUM, STRATEGY_QTD_RETURN, STRATEGY_YTD_RETURN for performance.
2. Portfolio Holdings, Sector Allocation: portfolio_analyzer (SAM_PORTFOLIO_VIEW)
3. SEC Financials, Segments, Competitor Analysis, analyst ratings and rating revisions: research_analyzer (SAM_RESEARCH_VIEW)
   Covers consolidated financials AND geographic/segment breakdowns.
   IMPORTANT: For M&A due diligence on regional divisions, use research_analyzer.
4. Client Mandate Details: implementation_analyzer (SAM_IMPLEMENTATION_VIEW)
5. Performance Attribution (Brinson, factor, multi-level): attribution_analyzer (SAM_ATTRIBUTION_VIEW)
   Use for "why did we outperform/underperform?" questions.
6. Strategic Documents: search_internal_docs (filter: strategy_documents)
7. Market News, Competitor Intel: search_external_docs (filter: press_releases)
8. M&A Financial Modeling: ma_simulation
9. PDF Generation: pdf_generator
10. Data Lineage: explain_data_origin

Tool-to-Semantic-View Mapping (for explain_data_origin):
- executive_kpi_analyzer -> SAM_DEMO.AI.SAM_EXECUTIVE_VIEW
- portfolio_analyzer -> SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
- research_analyzer -> SAM_DEMO.AI.SAM_RESEARCH_VIEW
- attribution_analyzer -> SAM_DEMO.AI.SAM_ATTRIBUTION_VIEW
- implementation_analyzer -> SAM_DEMO.AI.SAM_IMPLEMENTATION_VIEW

Boundaries:
- You cover firm-wide strategic intelligence: AUM and flows, strategy performance, client concentration, competitor intelligence and M&A scenario modelling. You do NOT do security-level or single-portfolio deep dives — redirect to Portfolio Manager Co-Pilot (AM Demo).
- You do NOT cover compliance, mandate breaches or ESG oversight — redirect to Risk & Compliance (AM Demo).
- You do NOT cover operations, settlement or NAV — redirect to Middle Office Co-Pilot (AM Demo).
- You do NOT have access to employee, HR or compensation data, or to confidential strategic plans outside the analytics in your tools. If asked, say so plainly.
- M&A simulation output is an illustrative model, not advice or a valuation. Always label it as such.

Workflow notes:
- Do not answer holistic business performance review questions by jumping straight to executive_kpi_analyzer alone when the question asks for a multi-part executive narrative. Use the executive-kpi-briefing skill first, then use direct tools only as supporting components of that workflow.
- Use direct tools first only when the user asks for a single focused metric, a narrow follow-up, or a specific drill-down rather than a full executive review.
- For competitor M&A analysis, the competitor-ma-analysis skill provides the 5-step workflow.
- For audience-adapted narratives, the audience-format-adaptation skill provides formatting guidance.
- For data lineage queries, the data-lineage-explanation skill provides the tool-to-view mapping and response template.

Error Handling:

Scenario 1: No Flow Data
User Message: "No flow data for that period. Flow and holdings data is month-end only; the latest available period is the most recent month-end."

Scenario 2: Competitor Not in SEC Filings
User Message: "SEC filings not available. Based on press reports, estimated AUM is approximately $X (estimate, not verified)."

Scenario 3: M&A Inputs Missing
User Message: "Running with assumptions: [list]. Would you like to adjust?"

Data Lineage (explain_data_origin):
When user asks how a value is calculated or where data comes from:
1. Identify the semantic field name from the previous query
2. Map the analyst tool to its semantic view using the mapping above
3. Call explain_data_origin with semantic_view_name and business_term
4. Response MUST use ONLY information from tool output - do NOT add facts from other sources"""

    response_formatted = format_instructions_for_yaml(response_instructions)
    orchestration_formatted = format_instructions_for_yaml(orchestration_instructions)

    analyst_exec = build_analyst_tool_resource("executive_kpi_analyzer", "SAM_EXECUTIVE_VIEW", database_name)
    analyst_portfolio = build_analyst_tool_resource("portfolio_analyzer", "SAM_PORTFOLIO_VIEW", database_name)
    analyst_research = build_analyst_tool_resource("research_analyzer", "SAM_RESEARCH_VIEW", database_name)
    analyst_attribution = build_analyst_tool_resource("attribution_analyzer", "SAM_ATTRIBUTION_VIEW", database_name)
    analyst_impl = build_analyst_tool_resource("implementation_analyzer", "SAM_IMPLEMENTATION_VIEW", database_name)
    search_internal = build_search_tool_resource("search_internal_docs", "SAM_INTERNAL_DOCS", database_name)
    search_external = build_search_tool_resource("search_external_docs", "SAM_EXTERNAL_DOCS", database_name)
    ma_resource = build_generic_tool_resource("ma_simulation", "MA_SIMULATION_TOOL", "MA_SIMULATION_TOOL(FLOAT, FLOAT, FLOAT)", database_name, timeout=30, tool_type="function")
    pdf_resource = pdf_generator_tool_resource(database_name)
    lineage_resource = build_generic_tool_resource("explain_data_origin", "EXPLAIN_DATA_ORIGIN", "EXPLAIN_DATA_ORIGIN(VARCHAR, VARCHAR)", database_name, timeout=120)
    common_res = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS['executive_leadership'], database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_executive_leadership_copilot
  COMMENT = 'Firm-wide strategic intelligence: AUM and flow analytics, strategy performance ranking, client concentration analysis, competitor SEC filing intelligence, and M&A scenario simulation.'
  PROFILE = '{{"display_name": "Executive Command Center (AM Demo)"}}'
  COPY GRANTS
  FROM SPECIFICATION
  $$
  models:
    orchestration: {config.AGENT_ORCHESTRATION_MODEL}
  orchestration:
    budget:
      seconds: {config.AGENT_BUDGET_SECONDS}
      tokens: {config.AGENT_BUDGET_TOKENS}
    tool_not_accessible: accept
  instructions:
    system: "You are a senior investment strategist at a UK-based asset management firm. You provide executive-level portfolio insights, firm-wide performance summaries, and strategic perspectives."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "Give me an executive summary of firm-wide performance"
      - question: "What are the key risks across our portfolios?"
      - question: "How are our flagship funds performing versus peers?"
      - question: "Model acquiring a $50B AUM business"
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "executive_kpi_analyzer"
        description: "Firm-wide KPIs, strategy performance, client flows. Key metrics: FIRM_AUM (authoritative), STRATEGY_QTD_RETURN, STRATEGY_YTD_RETURN, net flows, client counts. Use FIRM_AUM (not TOTAL_CLIENT_AUM) for board reporting."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "portfolio_analyzer"
        description: "Portfolio holdings, position weights, sector allocations, mandate compliance. 503 securities, 11 portfolios."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "research_analyzer"
        description: "SEC financials (consolidated and segment/geographic), analyst estimates, insider trading, institutional holdings. Covers both total revenue/EPS AND regional M&A due diligence."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "attribution_analyzer"
        description: |
          Performance attribution: Brinson decomposition (allocation, selection, interaction), factor attribution, hidden factors, rolling analytics, anomaly detection, peer learning, currency attribution.

          Data Coverage:
          - 24 months monthly attribution, 11 portfolios, 11 GICS sectors
          - Multi-level: sector, country, industry with drill-down
          - Linked periods: QTD, YTD, trailing 12M (Frongello base-period adjustment)

          When to Use:
          - "Why did we outperform/underperform this quarter?"
          - "What drove the active return — allocation or selection?"
          - "Show YTD attribution summary by sector"

          When NOT to Use:
          - Individual stock analysis (use portfolio_analyzer)
          - Stress testing or counterfactual analysis (redirect to Portfolio Manager Co-Pilot (AM Demo))
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "implementation_analyzer"
        description: "Client mandate requirements, approval thresholds, ESG constraints."
    - tool_spec:
        type: "cortex_search"
        name: "search_internal_docs"
        description: "Internal strategy documents, board materials, strategic planning. Filter by DOCUMENT_TYPE."
    - tool_spec:
        type: "cortex_search"
        name: "search_external_docs"
        description: "External press releases, competitor news, M&A announcements. Filter by DOCUMENT_TYPE."
    - tool_spec:
        type: "generic"
        name: "ma_simulation"
        description: "M&A financial simulation: EPS accretion, synergies, risk assessment. Inputs: target_aum, target_revenue, cost_synergy_pct."
        input_schema:
          type: "object"
          properties:
            target_aum:
              description: "Target AUM in dollars (e.g. 50000000000 for $50B)"
              type: "number"
            target_revenue:
              description: "Target annual revenue in dollars"
              type: "number"
            cost_synergy_pct:
              description: "Expected cost synergy % (default 0.20)"
              type: "number"
          required:
            - target_aum
            - target_revenue
{pdf_generator_tool_spec()}
    - tool_spec:
        type: "generic"
        name: "explain_data_origin"
        description: "Explains origin, calculation, and full data lineage for any analyst field. Use when user asks how a value is calculated or where data comes from."
        input_schema:
          type: "object"
          properties:
            semantic_view_name:
              type: "string"
              description: "Fully qualified semantic view name (e.g. SAM_DEMO.AI.SAM_EXECUTIVE_VIEW)"
            business_term:
              type: "string"
              description: "Exact semantic field name in UPPERCASE (e.g. FIRM_AUM)"
          required:
            - semantic_view_name
            - business_term
  tool_resources:
{common_res}
{analyst_exec}
{analyst_portfolio}
{analyst_research}
{analyst_attribution}
{analyst_impl}
{ma_resource}
{pdf_resource}
{lineage_resource}
{search_external}
{search_internal}
  $$;
"""
    session.sql(sql).collect()
