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
    build_skills_yaml,
    common_tool_specs,
    common_tool_resources,
    DEMO_DISCLAIMER,
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

Use UK English spelling.

{DEMO_DISCLAIMER}"""

    orchestration_instructions = """Skill-First Workflow:
When the user's request matches a skill domain, ALWAYS load the skill first via server_skill. The skill provides the complete multi-step workflow with stopping points and branching options.

Skill routing:
- Covenant breaches, compliance, headroom, watchlist, equity cure -> load covenant-monitoring skill
- Floating rate exposure, SOFR impact, rate shock scenarios -> load rate-sensitivity-analysis skill
- Deal pipeline, new opportunities, term sheet screening, IC memo -> load deal-pipeline-screening skill
- Portfolio overview, quarterly review, credit quality, concentration -> load credit-portfolio-review skill
- PD scores, risk drivers, what-if scenarios, SHAP analysis -> load credit-risk-calculator skill
- Audience/tone adjustment -> load audience-adaptive-narrative skill

Direct Data Queries (no skill needed):
For simple data lookups that do not require a multi-step workflow, use tools directly:
1. Portfolio metrics, leverage, coverage, financials, pipeline -> credit_portfolio_analyzer
2. Covenant compliance, breach tracking -> credit_portfolio_analyzer with covenant filters
3. Pipeline deals (SPREAD_BPS, EXPECTEDLEVERAGE, EXPECTEDCLOSE) -> credit_portfolio_analyzer
4. Sector benchmarks -> credit_portfolio_analyzer filtering BENCHMARKS table
5. Credit agreement terms, PIK, call protection -> search_credit_agreements
6. Quarterly compliance status, management commentary -> search_compliance_certs
7. Qualitative deal evaluation, IC recommendations -> search_ic_memos (AFTER structured data)
8. Base rate data, SOFR, macro indicators -> market_analyzer
9. SEC financials on public comparables -> research_analyzer
10. ML credit risk scores and SHAP explanations -> credit_risk_analyzer

Always cross-reference quantitative data with document search for complete picture."""

    response_formatted = format_instructions_for_yaml(response_instructions)
    orchestration_formatted = format_instructions_for_yaml(orchestration_instructions)

    analyst_credit = build_analyst_tool_resource("credit_portfolio_analyzer", "SAM_CREDIT_PORTFOLIO_VIEW", database_name)
    analyst_credit_risk = build_analyst_tool_resource("credit_risk_analyzer", "SAM_CREDIT_RISK_VIEW", database_name)
    analyst_market = build_analyst_tool_resource("market_analyzer", "SAM_MARKET_VIEW", database_name)
    analyst_research = build_analyst_tool_resource("research_analyzer", "SAM_RESEARCH_VIEW", database_name)
    search_sec = build_search_tool_resource("search_sec_filings", "SAM_REAL_SEC_FILINGS", database_name)
    common_res = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS['private_credit'], database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_private_credit_copilot
  COMMENT = 'Private credit and direct lending: monitor covenant compliance, evaluate new deal pipeline, track loan performance metrics, assess credit risk, and generate lender reporting.'
  PROFILE = '{{"display_name": "Private Credit Copilot"}}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: {config.AGENT_ORCHESTRATION_MODEL}
  orchestration:
    budget:
      seconds: {config.AGENT_BUDGET_SECONDS}
      tokens: {config.AGENT_BUDGET_TOKENS}
  instructions:
    system: "You are a private credit analyst at a UK-based asset management firm. You analyse credit agreements, covenant compliance, borrower performance, and lending portfolio risk."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "What is the current status of our loan portfolio?"
        answer: "I will provide an overview of the lending book including commitments, covenant compliance, and credit quality."
      - question: "Are any borrowers in covenant breach?"
        answer: "I will check all active credit facilities for covenant compliance and flag breaches."
      - question: "Show me the credit quality distribution"
        answer: "I will analyse the portfolio by credit rating, LTV ratios, and coverage metrics."
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "credit_portfolio_analyzer"
        description: "Query private credit portfolio: borrower financials, facility terms, covenant compliance, deal pipeline, sector benchmarks. 15 borrowers, 20 facilities, 640 covenant tests, 10 pipeline deals."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "credit_risk_analyzer"
        description: "ML-based credit risk scores and SHAP explainability for borrowers. PD scores, risk ratings, feature-level explanations."
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
        description: "Search credit agreements and amendments for facility terms, covenants, PIK, call protection. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_compliance_certs"
        description: "Search quarterly compliance certificates for covenant test results and management commentary. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_ic_memos"
        description: "Search IC memoranda for pipeline deal evaluation, investment thesis, IC recommendations. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_sec_filings"
        description: "Search SEC filing text (10-K, 10-Q) for comparable company research. IMPORTANT: always use persist_to_table."
  tool_resources:
{common_res}
{analyst_credit}
{analyst_credit_risk}
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
