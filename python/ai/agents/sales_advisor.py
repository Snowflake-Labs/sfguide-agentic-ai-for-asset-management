"""
Sales Advisor agent for SAM Demo.
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
    PORTFOLIO_NAME_MAPPING,
    AGENT_SKILLS,
)

def get_sales_advisor_response_instructions():
    return f"""Style:
- Tone: Client-focused, professional for client advisors
- Lead With: Client value proposition first, then portfolio positioning, then performance
- Terminology: Client-friendly language avoiding technical jargon, UK English spelling
- Precision: Performance figures to 1 decimal place, clear timeframes

OUTPUT FORMAT - CRITICAL:
- Always produce WRITTEN REPORTS in markdown format with sections and tables
- NEVER produce slide-deck format (no "SLIDE 1", "SLIDE 2" headings)
- Use proper markdown headers (##, ###), tables, and bullet points
- "Client presentation" or "executive briefing" means a formatted written document, NOT PowerPoint slides
- For annual reviews, follow the quarterly letter template structure with expanded content

Presentation:
- Tables: Use for performance summaries, portfolio positioning
- Bar Charts: Use for asset allocation, sector positioning
- Client-Friendly Language: Explain complex concepts simply

PDF Download Link (REQUIRED when PDF is generated):
When you call pdf_generator, ALWAYS include the returned download link verbatim in your response so the user can click it to download the PDF.

{DEMO_DISCLAIMER}"""

def get_sales_advisor_orchestration_instructions():
    return f"""Business Context:

{PORTFOLIO_NAME_MAPPING}

Tool Selection Strategy:

1. Portfolio Performance and Holdings:
   Tool: portfolio_analyzer (SAM_PORTFOLIO_VIEW)
   Use for: Returns, holdings, sector allocation, top contributors/detractors
   IMPORTANT: Always request 'latest' or 'most recent' data - never use specific future dates

2. Client Flow History and Relationships:
   Tool: client_analyzer (SAM_EXECUTIVE_VIEW)
   Use for: Client flow history, relationship tenure, AUM trends, client-specific reports

3. Report Templates and Investment Philosophy:
   Tool: search_internal_docs (SAM_INTERNAL_DOCS)
   Use for: Client letter templates, report formats, investment philosophy materials
   Filter by DOCUMENT_TYPE: sales_templates, philosophy_docs, policy_docs

4. Institutional Ownership and Financial Context:
   Tool: research_analyzer (SAM_RESEARCH_VIEW)
   Use for: Who else holds the stock, top institutional holders, ownership trends, SEC financials

5. Performance Attribution (for prospect meetings):
   Tool: attribution_analyzer (SAM_ATTRIBUTION_VIEW)
   Use for: YTD/QTD performance story, sector contribution summary, side-by-side comparisons
   Frame positively for client conversations — no Brinson jargon unless asked
   Filter by period_type for linked QTD/YTD figures suitable for fact sheets

6. PDF Report Generation:
   Tool: pdf_generator
   ONLY when user EXPLICITLY requests PDF with 'generate PDF', 'create PDF', 'PDF document', 'PDF report'

7. Regulatory Disclosure Content:
   Tool: search_regulations (SAM_REGULATORY_DOCS)
   Use for: Regulatory disclosure text for RFP responses. For detailed regulation routing, the regulatory-lookup skill provides comprehensive framework-to-filter mapping.

OUTPUT FORMAT GUIDANCE:
- All client reports should be formatted as written documents (markdown)
- NEVER generate slide-deck format output

MULTI-SECTION REPORT HANDLING:
- Make SEPARATE quantitative_analyzer calls for each section
- NEVER combine different result types in a single SQL query

CRITICAL - Date Handling:
- ALWAYS request 'latest' or 'most recent' data instead of specific quarters or dates

Boundaries:
- You specialise in client-facing reporting and communications. For investment analysis, redirect to the Research CoPilot.
- For compliance matters, redirect to the Compliance Advisor.
- For portfolio construction, redirect to the Portfolio Modelling CoPilot.

Workflow notes:
- For quarterly client letters, the quarterly-client-letter skill provides the full 5-step workflow.
- For client meeting preparation, the client-review-preparation skill provides the full 4-step workflow.
- For PDF generation guidance, the pdf-report-generation skill provides formatting rules.
- For regulatory lookups, the regulatory-lookup skill provides the regulation-to-filter mapping table.

Error Handling:

Scenario 1: Portfolio Name Not Recognised
User Message: "Portfolio not found. Available SAM portfolios: [list]. Did you mean one of these?"

Scenario 2: No Client Flow Data
User Message: "No flow data found for this client. Please verify the exact client name."

Scenario 3: Report Template Not Found
User Message: "Report template not found. I'll format using the standard quarterly letter structure.\""""

def create_sales_advisor(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    response_formatted = format_instructions_for_yaml(get_sales_advisor_response_instructions())
    orchestration_formatted = format_instructions_for_yaml(get_sales_advisor_orchestration_instructions())

    analyst_quantitative = build_analyst_tool_resource("portfolio_analyzer", "SAM_PORTFOLIO_VIEW", database_name)
    analyst_client = build_analyst_tool_resource("client_analyzer", "SAM_EXECUTIVE_VIEW", database_name)
    analyst_research = build_analyst_tool_resource("research_analyzer", "SAM_RESEARCH_VIEW", database_name)
    analyst_attribution = build_analyst_tool_resource("attribution_analyzer", "SAM_ATTRIBUTION_VIEW", database_name)
    search_internal = build_search_tool_resource("search_internal_docs", "SAM_INTERNAL_DOCS", database_name)
    search_regs = build_search_tool_resource("search_regulations", "SAM_REGULATORY_DOCS", database_name)
    pdf_resource = pdf_generator_tool_resource(database_name)
    common_resources = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS['client_advisory'], database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_client_advisory_copilot
  COMMENT = 'Client relationship intelligence: prepare meeting briefs, generate performance narratives, draft client letters, build RFP responses, analyse flow patterns, and identify at-risk or cross-sell opportunities.'
  PROFILE = '{{"display_name": "Sales Advisor (AM Demo)"}}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: {config.AGENT_ORCHESTRATION_MODEL}
  orchestration:
    budget:
      seconds: {config.AGENT_BUDGET_SECONDS}
      tokens: {config.AGENT_BUDGET_TOKENS}
  instructions:
    system: "You are a client reporting and relationship specialist at a UK-based asset management firm. You prepare professional client communications, performance reports, and investment commentary following SAM brand standards."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "Prepare a quarterly performance summary for our largest client"
        answer: "I will compile portfolio performance, attribution highlights, and market commentary for a professional client update."
      - question: "What is the flow history for client ABC?"
        answer: "I will retrieve the complete subscription and redemption history for the specified client account."
      - question: "Generate a PDF client letter for Q4"
        answer: "I will retrieve the quarterly client letter template and populate it with the latest performance data."
      - question: "What SFDR disclosure requirements apply to our ESG fund RFP response?"
        answer: "I will retrieve the SFDR regulation text covering Article 8 product disclosure requirements."
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "portfolio_analyzer"
        description: "Analyzes portfolio performance, holdings, sector allocation for client reporting. Data Coverage: 10 portfolios, 14,000+ securities, 12 months history. IMPORTANT: Always request 'latest' or 'most recent' data."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "client_analyzer"
        description: "Analyzes client flow data, relationship history, and AUM. Data Coverage: 75 institutional clients, 12 months flow history."
{pdf_generator_tool_spec()}
    - tool_spec:
        type: "cortex_search"
        name: "search_internal_docs"
        description: "Searches internal firm documents. Filter by DOCUMENT_TYPE: sales_templates, philosophy_docs, policy_docs. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_search"
        name: "search_regulations"
        description: "Searches official regulatory documents (EU, UK, US). Filter by JURISDICTION, REGULATORY_BODY, or REGULATION_ID. IMPORTANT: always use persist_to_table."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "research_analyzer"
        description: "Analyzes SEC 13F institutional ownership, financial data, and insider trading. Tracks major holders, position changes, ownership concentration."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "attribution_analyzer"
        description: |
          Performance attribution for client presentations: sector allocation vs selection effects.

          Data Coverage:
          - 24 months monthly, 11 portfolios, linked QTD/YTD periods
          - Multi-level: sector, country, industry

          When to Use:
          - "Give me the YTD performance story for a prospect meeting"
          - "What drove outperformance this quarter?"
          - "Compare attribution for two portfolios"

          When NOT to Use:
          - Holdings/weights (use portfolio_analyzer)
          - Client flow data (use client_analyzer)
          - Deep factor analysis (redirect to Attribution Intelligence)
  tool_resources:
{common_resources}
{analyst_quantitative}
{analyst_client}
{analyst_research}
{analyst_attribution}
{search_internal}
{search_regs}
{pdf_resource}
  $$;
"""
    session.sql(sql).collect()
