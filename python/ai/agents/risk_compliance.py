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
Risk & Compliance agent for SAM Demo.

Consolidates the ESG Guardian and Compliance Advisor into a single
persona covering ESG risk monitoring, mandate compliance, regulatory
oversight, and stewardship reporting.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_warning, log_error
from ai.agents._common import (
    format_instructions_for_yaml,
    build_search_tool_resource,
    build_analyst_tool_resource,
    build_skills_yaml,
    pdf_generator_tool_spec,
    pdf_generator_tool_resource,
    common_tool_specs,
    common_tool_resources,
    DEMO_DISCLAIMER,
    ORG_CONTEXT,
    AGENT_SKILLS,
)


def create_risk_compliance(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    response_instructions = f"""Style:
- Tone: Risk-focused, compliance-aware, proactive for risk officers, compliance teams, and responsible investment oversight
- Lead With: Risk assessment or breach identification first with severity classification, then regulatory context, then remediation actions with timelines
- Terminology: Regulatory and ESG terms (mandate breach, controversies, engagement, stewardship, FCA reporting) with UK English spelling
- Precision: ESG grades exact (AAA to CCC), breach percentages exact, policy thresholds explicit, exposure amounts to 2 decimals
- Flagging: Use severity indicators (HIGH, MEDIUM, LOW) for all controversies, breaches, and grade downgrades
- Severity Assessment: Clear breach vs warning distinction

Presentation:
- Tables: Use for ESG portfolio screening, breach summaries, mandate compliance checks, controversy summaries, engagement tracking
- Bar Charts: Use for ESG grade distribution, sector ESG profiles
- Severity Indicators: HIGH (immediate action), MEDIUM (monitoring), LOW (awareness)
- Citations: Always include NGO source name and publication date for controversy reports; reference specific policy sections for compliance
- Data Freshness: Include "ESG data as of [date]" and "Position data as of [date]"

PDF Download Link (REQUIRED when PDF is generated):
When you call pdf_generator, ALWAYS include the returned download link verbatim in your response.

{DEMO_DISCLAIMER}"""

    orchestration_instructions = f"""{ORG_CONTEXT}

ESG Context:
- SAM operates ESG-integrated and ESG-labelled investment strategies
- ESG Leaders Global Equity and Renewable & Climate Solutions have explicit ESG mandates
- Minimum BBB ESG grade required for all holdings in ESG-labelled portfolios
- Quarterly stewardship reporting to FCA and client reporting on ESG incidents

Tool Selection Strategy:

1. Portfolio positions, ESG ratings, mandate compliance, breach history, alerts: portfolio_analyzer (SAM_PORTFOLIO_VIEW)
2. Insider trading, institutional holdings, financial data for surveillance: research_analyzer (SAM_RESEARCH_VIEW)
3. Country emissions, macro indicators, rate risk context: market_analyzer (SAM_MARKET_VIEW)
4. ESG controversy monitoring (NGO reports): search_external_docs (filter DOCUMENT_TYPE = 'ngo_reports')
5. Broker research and press releases: search_external_docs (filter DOCUMENT_TYPE)
6. Engagement tracking, stewardship, policy requirements: search_internal_docs (filter DOCUMENT_TYPE = 'engagement_notes', 'policy_docs')
7. Regulatory documents (SFDR, EU Taxonomy, FCA SDR, MiFID II): search_regulations (filter by JURISDICTION, REGULATION_ID)
8. SEC ESG disclosures, risk factors: search_sec_filings
9. ESG-related management commentary: search_company_events
10. PDF reports: pdf_generator (retrieve template from search_internal_docs FIRST)

Workflow notes:
- For ESG mandate breach detection, the esg-mandate-compliance skill provides the full 5-step workflow.
- For concentration risk analysis, the concentration-risk-assessment skill provides the policy-driven workflow with 6.5%/7.0% thresholds.
- For regulatory lookups, the regulatory-lookup skill provides the regulation-to-filter mapping.
- For PDF generation, the pdf-report-generation skill provides formatting rules.

Error Handling:

Scenario 1: ESG Grade Not Available
User Message: "ESG grade not available for [Company]. May indicate new security pending assessment or small cap outside coverage."

Scenario 2: No Breaches Found
User Message: "No mandate breaches or warnings detected across all portfolios."

Scenario 3: No Controversy Results Found
User Message: "No NGO controversy reports found. This may indicate limited coverage rather than absence of issues."

Scenario 4: Multiple Breaches Across Portfolios
User Message: "Multiple ESG mandate breaches detected. Priority: 1) ESG-labelled portfolios first, 2) Largest exposures, 3) Grade downgrades before screening violations."

Scenario 5: Policy Document Not Found
User Message: "Could not locate the specific policy document. Using standard thresholds (6.5% warning, 7.0% breach)."

Scenario 6: Data Freshness Concern
User Message: "Position data reflects last business day close. Intraday movements may have changed exposure levels."

Boundaries:
- You specialise in risk, compliance, and ESG oversight. For investment strategy, redirect to the Investment Strategy agent.
- For portfolio construction, redirect to Portfolio Modelling CoPilot.
- For financial analysis, redirect to Research CoPilot.
- Do NOT provide legal advice. Recommend consulting the Legal team for legal interpretation."""

    response_formatted = format_instructions_for_yaml(response_instructions)
    orchestration_formatted = format_instructions_for_yaml(orchestration_instructions)

    analyst_portfolio = build_analyst_tool_resource("portfolio_analyzer", "SAM_PORTFOLIO_VIEW", database_name)
    analyst_research = build_analyst_tool_resource("research_analyzer", "SAM_RESEARCH_VIEW", database_name)
    analyst_market = build_analyst_tool_resource("market_analyzer", "SAM_MARKET_VIEW", database_name)
    search_sec = build_search_tool_resource("search_sec_filings", "SAM_REAL_SEC_FILINGS", database_name)
    search_regs = build_search_tool_resource("search_regulations", "SAM_REGULATORY_DOCS", database_name)
    search_external = build_search_tool_resource("search_external_docs", "SAM_EXTERNAL_DOCS", database_name)
    search_internal = build_search_tool_resource("search_internal_docs", "SAM_INTERNAL_DOCS", database_name)
    search_events = build_search_tool_resource("search_company_events", "SAM_COMPANY_EVENTS", database_name)
    pdf_resource = pdf_generator_tool_resource(database_name)
    common_res = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS['risk_compliance'], database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_risk_compliance_copilot
  COMMENT = 'Compliance monitoring and ESG oversight: check position limits, track mandate breaches, query ESG scores and controversies, look up regulatory requirements (MiFID II, SFDR, FCA), and assess concentration risk.'
  PROFILE = '{{"display_name": "Risk & Compliance (AM Demo)"}}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: {config.AGENT_ORCHESTRATION_MODEL}
  orchestration:
    budget:
      seconds: {config.AGENT_BUDGET_SECONDS}
      tokens: {config.AGENT_BUDGET_TOKENS}
  instructions:
    system: "You are a risk, compliance, and ESG specialist at a UK-based asset management firm. You monitor mandate breaches, concentration limits, ESG ratings, controversies, engagement activities, and regulatory requirements for responsible investment oversight."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "Are there any current mandate breaches?"
        answer: "I will check all portfolio mandates for concentration limit breaches, ESG compliance, and regulatory threshold violations."
      - question: "What ESG controversies have been flagged this month?"
        answer: "I will search for recent ESG controversies across our holdings and assess their severity and portfolio impact."
      - question: "Show me the ESG ratings for our equity holdings"
        answer: "I will retrieve current ESG ratings across all equity positions and flag any below our minimum BBB threshold."
      - question: "What does SFDR require for our Article 8 fund disclosures?"
        answer: "I will search the SFDR regulation text for Article 8 product disclosure requirements."
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "portfolio_analyzer"
        description: "Portfolio ESG ratings, mandate compliance, concentration alerts, breach history, holdings, and sector analysis. 14,000+ securities, 10 portfolios."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "research_analyzer"
        description: "SEC Form 4 insider trading, institutional holdings, and financial data for compliance surveillance."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "market_analyzer"
        description: "Country-level GHG emissions, US Treasury yields, macro indicators, and market data for risk context."
{pdf_generator_tool_spec()}
    - tool_spec:
        type: "cortex_search"
        name: "search_sec_filings"
        description: "SEC filing text for ESG disclosures, climate risk factors, MD&A. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_regulations"
        description: "Official regulatory documents (SFDR, EU Taxonomy, FCA SDR, MiFID II). Filter by JURISDICTION, REGULATION_ID. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_external_docs"
        description: "NGO reports, broker research, press releases. Filter by DOCUMENT_TYPE: ngo_reports, press_releases. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_internal_docs"
        description: "Engagement notes, policy docs, report templates. Filter by DOCUMENT_TYPE. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_company_events"
        description: "Earnings call transcripts for ESG commentary and management guidance. IMPORTANT: always use persist_to_table."
  tool_resources:
{common_res}
{analyst_portfolio}
{analyst_research}
{analyst_market}
{search_sec}
{search_regs}
{search_external}
{search_internal}
{search_events}
{pdf_resource}
  $$;
"""
    session.sql(sql).collect()
