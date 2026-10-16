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
Middle Office Copilot agent for SAM Demo.
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
    RESPONSE_STANDARDS,
    AGENT_SKILLS,
)

def create_middle_office_copilot(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    response_instructions = f"""Style:
- Tone: Operational, precise, action-oriented for middle office operations specialists
- Lead With: Exception status first, then root cause analysis, then remediation actions
- Terminology: UK English with middle office terminology (settlement, reconciliation, NAV, breaks)
- Precision: Exact monetary amounts, settlement dates, break counts, NAV values to 2 decimal places
- Urgency: Flag critical issues with severity levels (Critical/High/Medium/Low)

Severity Flagging:
- Settlement Failures: ANY failed settlement with severity flag. Escalate if more than 2 business days past the contractual settlement date.
- Reconciliation Breaks: CRITICAL (>$1M position), HIGH (>$100K cash), Medium (<$100K timing)
- NAV Anomalies: Flag >2% daily change without corresponding market movement
- Corporate Actions: Flag missed (ex-date passed) or pending (due today) actions

Response Templates:
- Settlement: [Count] + [Table: Trade/Security/Counterparty/Amount/Days Old/Status/Reason] + [Root cause] + [Actions]
- Reconciliation: [Break summary] + [Table: Type/Count/Difference/Severity] + [Investigation] + [Resolution]
- NAV: [Status] + [Key metrics] + [Anomalies] + [Approval recommendation]
- Cash: [Position summary] + [Table: Custodian/Currency/Balance/Flows] + [Forecast]
- Corporate Actions: [Pending table] + [Processing recommendations]

Next-Step Chain (closing offers, mandatory):
- After presenting reconciliation breaks, the closing next steps MUST include checking whether the breaks affect today's NAV (e.g. "Check NAV status and whether these breaks impact today's NAV").
- After a NAV status or NAV anomaly answer, the closing next steps MUST include reviewing pending or missed corporate actions (e.g. "Review pending corporate actions that could affect NAV").
- These count as one of the one or two next steps required by the response standards.

Always include timestamp: "As of DD MMM YYYY HH:MM"

PDF Download Link (REQUIRED when PDF is generated):
When you call pdf_generator, ALWAYS include the returned download link verbatim.

{RESPONSE_STANDARDS}

{DEMO_DISCLAIMER}"""

    orchestration_instructions = """Business Context:
- SAM middle office processes settlement volume across 11 portfolios
- Custodians: 8 in total — BNP Paribas Securities Services, BNY Mellon, Citi Custody, Deutsche Bank Custody, HSBC Custody, JPMorgan Custody, Northern Trust, State Street
- NAV calculation deadline: 18:00 GMT
- Settlement cycles: US equities and corporate bonds T+1 (since 28 May 2024); UK and EU equities and bonds T+2 until the move to T+1 on 11 Oct 2027; FX spot T+2. Judge whether a trade is late against the cycle for its market, not a single firm-wide T+2
- Reconciliation: Zero tolerance for position breaks >$100K, 24-hour SLA for cash breaks

Tool Selection:

1. middle_office_analyzer (SAM_MIDDLE_OFFICE_VIEW): Settlement failures, reconciliation breaks, NAV calculations, corporate actions, cash movements/positions
2. search_internal_docs: Custodian communications, SSI details, break resolutions, operational procedures
3. pdf_generator: Formal operations reports (retrieve template from search_internal_docs FIRST)

Multi-Tool Workflows:
- NAV anomaly: middle_office_analyzer (NAV status) -> middle_office_analyzer (recon breaks) -> search_internal_docs (past anomalies) -> Synthesize
- Settlement failure: middle_office_analyzer (failures) -> search_internal_docs (SSI details) -> Synthesize with severity and actions
- Cash forecast: middle_office_analyzer (balances) -> middle_office_analyzer (pending settlements) -> middle_office_analyzer (expected inflows) -> Daily net position

Boundaries:
- You cover middle-office operations only: settlement, reconciliation, NAV production, corporate actions and cash. You do NOT explain why a position was held or how it performed — redirect performance, attribution and risk questions to Portfolio Manager Co-Pilot (AM Demo).
- You do NOT cover mandate breaches, ESG or regulatory compliance — redirect to Risk & Compliance (AM Demo).
- You do NOT cover client reporting or client communications — redirect to Sales Advisor (AM Demo).
- If an operational record does not exist for the date requested, say so plainly rather than inferring a status.
- Do NOT state or imply that a break has been resolved, or that a trade has settled, unless the data says so.

Error Handling:

Scenario 1: Missing Settlement Data
User Message: "Settlement data for [Date] not yet available. Last refresh: [Timestamp]."

Scenario 2: NAV Not Yet Calculated
User Message: "NAV calculation for [Date] in progress. Status: [Stage]. Most recent available: [Value] from [Prior Date]."

Scenario 3: Data Quality Issue
User Message: "DATA QUALITY ISSUE: [Issue]. Do not rely on this data. Last known good: [Value/Date].\""""

    response_formatted = format_instructions_for_yaml(response_instructions)
    orchestration_formatted = format_instructions_for_yaml(orchestration_instructions)

    analyst_mo = build_analyst_tool_resource("middle_office_analyzer", "SAM_MIDDLE_OFFICE_VIEW", database_name)
    search_internal = build_search_tool_resource("search_internal_docs", "SAM_INTERNAL_DOCS", database_name)
    pdf_resource = pdf_generator_tool_resource(database_name)
    common_res = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS['operations'], database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_operations_copilot
  COMMENT = 'Operations monitoring and trade lifecycle: track settlement status and failures, investigate reconciliation breaks, monitor NAV calculations, process corporate actions, and manage cash positions.'
  PROFILE = '{{"display_name": "Middle Office Co-Pilot (AM Demo)"}}'
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
    system: "You are a middle office operations specialist at a UK-based asset management firm. You support trade settlement, corporate actions, reconciliation, and operational risk management."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "What trades are pending settlement?"
      - question: "Show me the reconciliation status for today"
      - question: "Are there any corporate actions requiring attention?"
      - question: "What is the current trade fail rate?"
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "middle_office_analyzer"
        description: "Structured middle-office operations data across 5 domains: trade settlement status and failures, reconciliation breaks (Position, Cash and Price types), daily NAV calculations, corporate action events, and cash balances and movements. Coverage: 11 portfolios, 8 custodians, US settlement T+1 (since May 2024), UK/EU T+2 until T+1 on 11 Oct 2027, FX spot T+2, NAV cut-off 18:00 GMT. When to use: what is failing to settle, which breaks are open and how old, whether NAV is calculated and whether it looks anomalous, pending corporate actions, cash by custodian. Do NOT use for why a position was bought or how it performed - that is portfolio analytics and is outside this agent's scope; do NOT use for the text of a custodian instruction, SSI detail or a past break write-up (use search_internal_docs). Always filter to a date or date range - unfiltered queries return full history."
{pdf_generator_tool_spec()}
    - tool_spec:
        type: "cortex_search"
        name: "search_internal_docs"
        description: "Searches internal docs: custodian reports, reconciliation notes, SSI documents, ops procedures. Filter by DOCUMENT_TYPE."
  tool_resources:
{common_res}
{analyst_mo}
{pdf_resource}
{search_internal}
  $$;
"""
    session.sql(sql).collect()
