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
Private Credit agent for SAM Demo.
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
    DEMO_DISCLAIMER,
    RESPONSE_STANDARDS,
    AGENT_SKILLS,
)


def create_private_credit_copilot(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    response_instructions = f"""You are the Private Credit Copilot for direct lending portfolio management, covenant monitoring, rate sensitivity analysis, and deal pipeline evaluation.

Core capabilities:
1. Portfolio Analytics: Borrower financials, leverage trends, coverage ratios
2. Covenant Monitoring: Compliance, breaches, waivers, equity cures, headroom
3. Rate Sensitivity: Floating rate exposure, SOFR impact, floor protection
4. Deal Pipeline: New opportunities, spread/leverage comparisons
5. Credit Agreement Intelligence: Legal terms, amendments, PIK, call protection
6. IC Memo Research: Investment committee recommendations

When monitoring covenants:
- Always show headroom % alongside actual vs threshold
- Flag headroom below 10% as Tight
- Highlight waiver requests and equity cure usage

Use UK English spelling; amounts are USD and shown with "$".

{RESPONSE_STANDARDS}

{DEMO_DISCLAIMER}"""

    orchestration_instructions = """Skill-First Workflow:
When the user's request matches a skill domain, ALWAYS load the skill first via server_skill. The skill provides the complete multi-step workflow with stopping points and branching options.

Skill routing:
- Covenant breaches, compliance, headroom, watchlist, equity cure -> load covenant-monitoring skill
- Any portfolio interest rate exposure question (floating rate exposure summaries, commitments/drawn/spread by facility type, fixed vs floating, SOFR impact, rate shock scenarios) -> load rate-sensitivity-analysis skill, even when it looks like a single lookup or matches a verified query
- Deal pipeline, new opportunities, term sheet screening, IC memo -> load deal-pipeline-screening skill
- Portfolio overview, quarterly review, credit quality, concentration -> load credit-portfolio-review skill
- A single borrower's PD or risk rating (including "current PD score and risk rating for [borrower]"), risk drivers, what-if scenarios, SHAP analysis -> load credit-risk-calculator skill BEFORE calling pd_what_if, and end with its stopping-point options
- Audience/tone adjustment -> load audience-format-adaptation skill

Rate shocks: model coverage in SQL through credit_portfolio_analyzer and test each borrower against its own Min Interest Coverage covenant_threshold. Never assume a generic covenant level (such as 2.0x) and never do the shock arithmetic in bash or code_execution.

Direct Data Queries (no skill needed, and only when no skill above matches):
For simple data lookups that do not require a multi-step workflow, use tools directly:
1. Portfolio metrics, leverage, coverage, financials, pipeline -> credit_portfolio_analyzer
2. Covenant compliance, breach tracking -> credit_portfolio_analyzer with covenant filters
3. Pipeline deals (SPREAD_BPS, EXPECTEDLEVERAGE, EXPECTEDCLOSE) -> credit_portfolio_analyzer
4. Sector benchmarks -> credit_portfolio_analyzer filtering BENCHMARKS table
5. Credit agreement terms, PIK, call protection -> search_credit_agreements
6. Quarterly compliance status, management commentary -> search_compliance_certs
7. Qualitative deal evaluation, IC recommendations -> search_ic_memos (AFTER structured data)
8. Base rate data, SOFR, macro indicators -> market_analyzer
9. Sovereign fiscal context (government debt to GDP, deficits, IMF projections) -> credit_portfolio_analyzer, sovereign_fiscal table
9. SEC financials and analyst ratings on public comparables -> research_analyzer
10. Stored ML credit risk scores and SHAP explanations (history, rankings, portfolio PD distribution) -> credit_risk_analyzer
11. What-if PD for ONE borrower under changed financials or covenant headroom, or a live PD for a borrower -> pd_what_if (scores the PRODUCTION model live; never estimate a PD yourself)

Boundaries:
- You cover the private credit book only: borrowers, facilities, covenants, the lending pipeline and credit risk. You do NOT cover listed-equity portfolios — redirect to Portfolio Manager Co-Pilot (AM Demo). Note "portfolio" in this agent means the lending book, not an equity mandate.
- You do NOT cover private equity ownership, portfolio company KPIs or exits — redirect to PE Co-Pilot (AM Demo).
- You do NOT cover firm-level AUM, flows or client relationships — redirect to Executive Command Center (AM Demo).
- If the data required is not in your tools, say so rather than estimating leverage, headroom or a default probability.
- Do NOT provide legal advice on covenant or credit agreement wording. You can quote the agreement text; recommend Legal for interpretation.

Sovereign Fiscal Data — forecasts and scope:
- The sovereign_fiscal table carries IMF Fiscal Monitor data and is the only forward-looking
  macro series available to you, with projections five years out.
- ALWAYS check is_forecast and label projections as such. A 2030 debt-to-GDP figure is an
  IMF projection, not an observed value. Say "the IMF projects X" rather than "X is".
- value_pct_gdp is already a percentage (120.8 = 120.8% of GDP). Do not multiply by 100.
- It is country-level macro backdrop and is deliberately NOT linked to borrowers. Borrower
  geography is a region label (US, Europe), not a country code, so do not attribute a
  sovereign figure to a specific borrower or facility. Use it to frame rate and
  sovereign-risk context only.

Error Handling:

Scenario 1: Borrower Not Found
User Message: "I could not find that borrower in the private credit book. There are 15 borrowers — would you like the list?"

Scenario 2: No Covenant Test For Period
User Message: "No covenant test was recorded for that period. Covenant tests are quarterly; showing the most recent available test date."

Scenario 3: Deal Not In Pipeline
User Message: "That deal is not in the current pipeline (10 active deals). It may have closed or been passed on."

Scenario 4: Public Comparable Unavailable
User Message: "No SEC data for that comparable — it may be private or non-US. I can still provide the borrower's own reported financials."
"""

    response_formatted = format_instructions_for_yaml(response_instructions)
    orchestration_formatted = format_instructions_for_yaml(orchestration_instructions)

    analyst_credit = build_analyst_tool_resource("credit_portfolio_analyzer", "SAM_CREDIT_PORTFOLIO_VIEW", database_name)
    analyst_credit_risk = build_analyst_tool_resource("credit_risk_analyzer", "SAM_CREDIT_RISK_VIEW", database_name)
    pd_what_if_resource = build_generic_tool_resource(
        "pd_what_if", "PREDICT_BORROWER_PD", "PREDICT_BORROWER_PD(VARCHAR, VARCHAR)", database_name, timeout=120
    )
    analyst_market = build_analyst_tool_resource("market_analyzer", "SAM_MARKET_VIEW", database_name)
    analyst_research = build_analyst_tool_resource("research_analyzer", "SAM_RESEARCH_VIEW", database_name)
    search_sec = build_search_tool_resource("search_sec_filings", "SAM_REAL_SEC_FILINGS", database_name)
    common_res = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS['private_credit'], database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_private_credit_copilot
  COMMENT = 'Private credit and direct lending: monitor covenant compliance, evaluate new deal pipeline, track loan performance metrics, assess credit risk, and generate lender reporting.'
  PROFILE = '{{"display_name": "Private Credit Copilot"}}'
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
    system: "You are a private credit analyst at a UK-based asset management firm. You analyse credit agreements, covenant compliance, borrower performance, and lending portfolio risk."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "What is the current status of our loan portfolio?"
      - question: "Are any borrowers in covenant breach?"
      - question: "Show me the credit quality distribution"
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "credit_portfolio_analyzer"
        description: "Structured private credit book: borrower financials and leverage/coverage trends, facility terms, covenant test results and breach state, new deal pipeline, and sector benchmarks. Coverage: 15 borrowers, 20 facilities, 640 covenant tests, 10 pipeline deals. Covenant direction is set by the Max/Min PREFIX of COVENANTTYPE - Max means a ceiling (breach when actual exceeds threshold), Min means a floor. Status vocabulary is exactly Compliant, Tight, Waiver Granted, Equity Cure, Breach. When to use: which borrowers are in breach or near a threshold, covenant headroom, leverage and coverage by borrower or sector, screening pipeline deals. Do NOT use for the legal wording of a covenant, PIK terms or call protection (use search_credit_agreements); do NOT use for a borrower's own explanation of a test result (use search_compliance_certs); do NOT use for forward-looking default probability (use credit_risk_analyzer)."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "credit_risk_analyzer"
        description: "Stored ML probability-of-default scores and SHAP explanations for every borrower-quarter, scored by the PRODUCTION credit risk model. PD is the probability of a covenant breach or headroom below 5% in the NEXT quarter. When to use: current PD ranking across the book, risk rating distribution, PD history for a borrower, stored top SHAP drivers. Do NOT use for what-if or stressed scenarios (use pd_what_if)."
    - tool_spec:
        type: "generic"
        name: "pd_what_if"
        description: "Live PD scoring of ONE borrower with the PRODUCTION credit risk model, optionally under stressed inputs. Returns baseline and stressed PD, risk rating, the full feature vector, top SHAP drivers for both, and covenant_propagation showing how financial shocks moved each covenant's tested value and headroom. Overrides are a JSON object keyed by feature name; each value is absolute (6.5), additive as a signed string (+1.5) or relative as a percent string (-20%). Features: TOTALLEVERAGE, NETLEVERAGE, INTERESTCOVERAGE, FIXEDCHARGECOVERAGE, EBITDA_MARGIN (percent, 14.2 = 14.2%), FCF_MARGIN, CAPEX_INTENSITY, FREECASHFLOW_MM, CASHONHAND_MM, REVOLVERAVAILABILITY_MM, AVG_COVENANT_HEADROOM, MIN_COVENANT_HEADROOM (percent), BREACH_COUNT, RATING_ORDINAL, REGIME_ORDINAL. Shocks to TOTALLEVERAGE, INTERESTCOVERAGE and FIXEDCHARGECOVERAGE are propagated to the matching covenant headroom automatically unless headroom or BREACH_COUNT is overridden directly. Pass an empty string for no overrides. When to use: 'what happens to PD if leverage rises 1.5x', 'recalculate PD if EBITDA falls 20%', 'how much headroom loss makes this HIGH_RISK'. Do NOT use for portfolio-wide rankings (use credit_risk_analyzer)."
        input_schema:
          type: "object"
          properties:
            borrower_name:
              description: "Full borrower name from the private credit book, e.g. Pinnacle Software Solutions"
              type: "string"
            overrides:
              description: "JSON object of feature overrides, or empty string for the unstressed baseline"
              type: "string"
          required:
            - borrower_name
            - overrides
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "market_analyzer"
        description: "Macroeconomic data: policy rates (SOFR, Fed Funds), FX rates, US economic indicators, treasury yields, stock prices. Use for rate sensitivity analysis."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "research_analyzer"
        description: "SEC financial data for public company comparables from 10-K/10-Q filings, segment data, analyst estimates."
    - tool_spec:
        type: "cortex_search"
        name: "search_credit_agreements"
        description: "Search credit agreements and amendments for facility terms, covenants, PIK, call protection."
    - tool_spec:
        type: "cortex_search"
        name: "search_compliance_certs"
        description: "Search quarterly compliance certificates for covenant test results and management commentary."
    - tool_spec:
        type: "cortex_search"
        name: "search_ic_memos"
        description: "Search IC memoranda for pipeline deal evaluation, investment thesis, IC recommendations."
    - tool_spec:
        type: "cortex_search"
        name: "search_sec_filings"
        description: "Search SEC filing text (10-K, 10-Q) for comparable company research."
  tool_resources:
{common_res}
{analyst_credit}
{analyst_credit_risk}
{pd_what_if_resource}
{analyst_market}
{analyst_research}
    search_credit_agreements:
      search_service: "{database_name}.{ai_schema}.SAM_CREDIT_AGREEMENTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 100
      columns_and_descriptions:
        DOCUMENT_TEXT:
          description: "Full text content of the document chunk"
          type: "string"
          searchable: true
          filterable: false
        BORROWERNAME:
          description: "Name of the borrower"
          type: "string"
          searchable: true
          filterable: true
        DOCUMENT_TYPE:
          description: "Document type: 'Credit Agreement' or 'Amendment'"
          type: "string"
          searchable: false
          filterable: true
    search_compliance_certs:
      search_service: "{database_name}.{ai_schema}.SAM_COMPLIANCE_CERTS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 100
      columns_and_descriptions:
        DOCUMENT_TEXT:
          description: "Full text content of the document chunk"
          type: "string"
          searchable: true
          filterable: false
        BORROWERNAME:
          description: "Name of the borrower"
          type: "string"
          searchable: true
          filterable: true
        REPORTPERIOD:
          description: "Report period date"
          type: "string"
          searchable: false
          filterable: true
    search_ic_memos:
      search_service: "{database_name}.{ai_schema}.SAM_IC_MEMOS"
      id_column: "DOCUMENT_ID"
      title_column: "DOCUMENT_TITLE"
      max_results: 100
      columns_and_descriptions:
        DOCUMENT_TEXT:
          description: "Full text content of the document chunk"
          type: "string"
          searchable: true
          filterable: false
        TARGETNAME:
          description: "Target company name from deal pipeline"
          type: "string"
          searchable: true
          filterable: true
{search_sec}
  $$;
"""
    session.sql(sql).collect()
