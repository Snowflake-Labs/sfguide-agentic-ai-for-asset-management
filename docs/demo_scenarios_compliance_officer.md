# SAM Demo - Compliance Officer Scenarios

Complete demo scenarios for Compliance Officer role with step-by-step conversations, expected responses, and data flows.

---

## Compliance Advisor

### Compliance Advisor - Daily Concentration Limit Monitoring

#### Business Context Setup

**Persona**: James Chen, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Compliance officers need to perform daily concentration limit checks across all portfolios—the most frequent compliance task. Traditional monitoring requires reviewing multiple reports, manually comparing positions to policy thresholds, and documenting findings.  
**Value Proposition**: AI-powered daily concentration monitoring that quickly scans all portfolios, flags positions above thresholds, and produces concise compliance summaries in minutes.

**Agent**: `compliance_advisor`  
**Data Available**: Portfolio holdings across 10 strategies, concentration policy documents with specific thresholds

#### Demo Flow

**Scene Setting**: James starts each day with a quick concentration check across all portfolios before the morning risk meeting. He needs to identify any positions approaching or exceeding limits and prepare a brief summary for the risk team.

##### Step 1: Portfolio-Wide Concentration Scan
**User Input**: 
```
Run a daily concentration check across all portfolios. Show me any positions above the 6.5% warning threshold, sorted by weight.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Scan all portfolios for concentration

**Expected Response**:
- **Flagged Positions Table**: All positions >6.5% across portfolios
  - Portfolio name, Security, Ticker, Weight %, Market Value
- **Severity Classification**: 
  - ⚠️ WARNING (6.5-7.0%)
  - 🚨 BREACH (>7.0%)
- **Portfolio Summary**: Count of warnings/breaches per portfolio
- **Total Exposure**: Aggregate flagged exposure

**Talking Points**:
- **Portfolio-Wide Scan**: Single query checks all 10 portfolios simultaneously
- **Threshold-Based Flagging**: Automatic classification by severity level
- **Daily Efficiency**: Complete concentration check in seconds

**Key Features Highlighted**: 
- **SAM_ANALYST_VIEW**: Complete portfolio coverage for compliance monitoring
- **Automated Classification**: AI applies compliance thresholds automatically

##### Step 2: Policy Threshold Confirmation

**Presenter Transition**:
> "I see several flagged positions. Before I report these, let me confirm the exact policy thresholds to ensure I'm applying the correct limits..."

*Reasoning: Policy thresholds may vary by portfolio type or have been updated. Confirming from source policy ensures accurate compliance assessment.*

**User Input**: 
```
What are the exact concentration thresholds in our Concentration Risk Policy? Confirm warning and breach levels.
```

**Tools Used**:
- `search_policies` (Cortex Search) - Retrieve concentration policy thresholds

**Expected Response**:
- **Policy Thresholds Retrieved**:
  - Warning and breach threshold percentages from policy
  - Remediation timeline requirements
  - Reporting and escalation requirements
  - Policy section references for documentation

**Talking Points**:
- **Policy Verification**: Confirms thresholds from authoritative source
- **Audit Trail**: Documents policy basis for compliance decisions
- **Current Information**: Always retrieves latest policy version

**Key Features Highlighted**: 
- **SAM_POLICY_DOCS**: Complete policy library with concentration requirements
- **Authoritative Source**: Policy retrieval ensures accuracy

##### Step 3: Compliance Status Classification

**Presenter Transition**:
> "Good, thresholds confirmed. Now let me apply these exactly to our flagged positions to produce the official compliance status..."

*Reasoning: Formal compliance status requires precise application of policy thresholds to portfolio data, with proper classification and documentation.*

**User Input**: 
```
Apply these policy thresholds to classify each flagged position as Compliant, Warning, or Breach. Include the exact variance from threshold.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Detailed position analysis

**Expected Response**:
- **Compliance Status Classification**:
  - Status table with positions classified against thresholds
    | Column | Description |
    |--------|-------------|
    | Portfolio | Portfolio name |
    | Security | Position identifier |
    | Weight | Current portfolio weight |
    | Status | Compliant/Warning/Breach classification |
    | Variance | Distance from threshold |
- **Summary Counts**: Total breaches and warnings requiring action

**Talking Points**:
- **Precise Classification**: Exact variance from policy thresholds
- **Actionable Output**: Clear indication of required responses
- **Documentation Ready**: Formatted for compliance records

**Key Features Highlighted**: 
- **Threshold Application**: AI precisely applies policy limits
- **Variance Calculation**: Exact measurement of compliance status

##### Step 4: Daily Compliance Summary

**Presenter Transition**:
> "I have all the detail. Let me create a concise summary for the morning risk meeting and my end-of-day compliance log..."

*Reasoning: Daily compliance monitoring requires documented summaries for internal records and team communication.*

**User Input**: 
```
Create a brief daily compliance summary I can share with the risk team and file in my compliance log.
```

**Tools Used**:
- Synthesis of previous queries

**Expected Response**:
- **Daily Compliance Summary** (Date)
- **Overall Status**: ⚠️ 2 Breaches, 1 Warning
- **Immediate Actions**: List positions requiring action
- **Monitoring Items**: Positions to watch
- **Next Steps**: Required follow-ups
- **Compliance Officer**: Sign-off line

**Talking Points**:
- **Concise Reporting**: Summary format for efficient communication
- **Action-Oriented**: Clear next steps identified
- **Audit Ready**: Documented daily compliance review

**Key Features Highlighted**: 
- **Summary Generation**: AI creates concise compliance reports
- **Daily Documentation**: Supports compliance audit trail

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: Daily concentration check reduced from 30+ minutes to 5 minutes
- **Coverage**: Complete portfolio coverage vs selective sampling
- **Consistency**: Same thorough check every day
- **Documentation**: Automatic compliance log entries

**Technical Differentiators**:
- **Portfolio-Wide Scanning**: Single query checks all portfolios simultaneously
- **Policy Integration**: Thresholds retrieved from authoritative policy documents
- **Precise Classification**: Exact variance calculations with severity levels
- **Daily Efficiency**: Designed for high-frequency compliance tasks

---

### Compliance Advisor - Policy Requirements Lookup

#### Business Context Setup

**Persona**: James Chen, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Compliance teams frequently receive questions about policy requirements from portfolio managers, auditors, and new team members. Finding specific policy details traditionally requires searching through multiple documents.  
**Value Proposition**: AI-powered policy Q&A that quickly retrieves specific policy requirements, thresholds, and procedures from the complete policy library.

**Agent**: `compliance_advisor`  
**Data Available**: 20+ policy documents including Concentration Risk Policy, Sustainable Investment Policy, Investment Mandates

#### Demo Flow

**Scene Setting**: A new portfolio manager asks James about ESG requirements for ESG-labelled portfolios. James uses the Compliance Advisor to quickly retrieve accurate policy information.

##### Step 1: ESG Requirements Query
**User Input**: 
```
What are the ESG requirements for ESG-labelled portfolios? What grades are required and what are the exclusion criteria?
```

**Tools Used**:
- `search_policies` (Cortex Search) - ESG policy requirements

**Expected Response**:
- **ESG Grade Floor**: Minimum BBB rating for all holdings
- **Exclusion Criteria**: Industries and activities excluded
- **Controversy Policy**: How controversies affect eligibility
- **Review Frequency**: How often ESG grades are assessed
- **Policy Reference**: Sustainable Investment Policy sections

**Talking Points**:
- **Quick Retrieval**: Specific policy details in seconds
- **Comprehensive Answer**: Multiple ESG requirements covered
- **Source Attribution**: Policy section references included

**Key Features Highlighted**: 
- **SAM_POLICY_DOCS**: Complete policy library searchable by AI
- **Natural Language**: Ask questions in plain language

##### Step 2: Breach Procedures

**Presenter Transition**:
> "The PM also wants to know what happens if they breach a limit. Let me explain the remediation procedures..."

*Reasoning: Understanding consequences and procedures is essential for policy compliance. Proactive explanation prevents violations.*

**User Input**: 
```
What happens if we breach a concentration limit? What's the remediation timeline and what committees need to be notified?
```

**Tools Used**:
- `search_policies` (Cortex Search) - Breach procedures

**Expected Response**:
- **Notification Requirements**: Investment Committee within 5 business days
- **Documentation**: Investment Committee Memo required
- **Remediation Timeline**: 30 days for position concentration breaches
- **Escalation Path**: Who is notified at each stage
- **Governance Actions**: Required committee reviews

**Talking Points**:
- **Procedural Clarity**: Step-by-step breach response
- **Timeline Specifics**: Exact days and deadlines
- **Governance Integration**: Committee requirements explained

**Key Features Highlighted**: 
- **Procedure Retrieval**: AI finds process and timeline details
- **Governance Awareness**: Committee requirements automatically included

##### Step 3: Portfolio-Specific Requirements

**Presenter Transition**:
> "Now the PM wants to know which of their portfolios actually have ESG requirements. Let me check the portfolio data..."

*Reasoning: Policy requirements apply differently across portfolios. Identifying which portfolios are ESG-labelled helps focus compliance efforts.*

**User Input**: 
```
Which of our portfolios are ESG-labelled and have these ESG requirements? Show me the list with their specific mandate requirements.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Portfolio ESG classification

**Expected Response**:
- **ESG-Labelled Portfolios**:
  - SAM ESG Leaders Global Equity
  - SAM Renewable & Climate Solutions
- **Requirements per Portfolio**: Specific mandate rules
- **Non-ESG Portfolios**: Confirmation of which don't have ESG mandates
- **Comparison**: Differences in requirements if any

**Talking Points**:
- **Portfolio Identification**: Clear list of affected portfolios
- **Mandate Specifics**: Individual portfolio requirements shown
- **Complete Picture**: ESG and non-ESG portfolios distinguished

**Key Features Highlighted**: 
- **Portfolio Classification**: AI identifies ESG-labelled funds
- **Mandate Integration**: Specific requirements per portfolio

#### Scenario Wrap-up

**Business Impact Summary**:
- **Response Time**: Policy questions answered in minutes vs hours of document searching
- **Accuracy**: Direct retrieval from authoritative policy sources
- **Training Efficiency**: New team members get accurate answers quickly
- **Consistency**: Same answers regardless of who asks

**Technical Differentiators**:
- **Natural Language Query**: Ask questions in plain English
- **Multi-Document Search**: AI searches across all policy documents
- **Context Integration**: Combines policy details with portfolio specifics

---

### Compliance Advisor - Breach Remediation Tracking

#### Business Context Setup

**Persona**: James Chen, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Tracking breach remediation requires monitoring the complete lifecycle from alert to resolution—retrieving breach history with resolution status, finding portfolio manager commitments from engagement discussions, comparing current positions against committed targets, and preparing formal accountability reports for the Risk Committee. This information spans compliance alerts, engagement notes, and current portfolio data.  
**Value Proposition**: AI-powered remediation tracking that combines breach history, PM engagement commitments, and current portfolio status to monitor compliance recovery progress and prepare professional Risk Committee reports.

**Agent**: `compliance_advisor`  
**Data Available**: Compliance breach alerts with resolution status, engagement notes with PM commitments, current portfolio holdings, report templates

#### Demo Flow

**Scene Setting**: James is preparing for the monthly Risk Committee meeting and needs to report on the status of previously identified concentration breaches. He needs to retrieve the breach history showing which have been resolved and which remain active, find the PM commitments made during engagement discussions, verify whether those commitments have been executed by checking current positions, and prepare a formal Risk Committee report with the findings.

##### Step 1: Retrieve Breach History and Resolution Status
**User Input**: 
```
Show me all concentration breaches from the last 30 days. Include which ones have been resolved and which are still active.
```

**Tools Used**:
- `compliance_analyzer` (Cortex Analyst) - Query FACT_COMPLIANCE_ALERTS for breach history with ResolvedDate, ResolvedBy, ResolutionNotes

**Expected Response**:
- **Active Breaches** (unresolved):
  | Security | Portfolio | Alert Date | Current Value | Threshold | Days Outstanding | Severity |
  |----------|-----------|------------|---------------|-----------|------------------|----------|
  | Apple (AAPL) | SAM Technology & Infrastructure | [Date] | 8.2% | 7.0% | 12 days | 🚨 BREACH |
  | Microsoft (MSFT) | SAM Technology & Infrastructure | [Date] | 7.4% | 7.0% | 8 days | 🚨 BREACH |

- **Resolved Breaches**:
  | Security | Portfolio | Alert Date | Resolved Date | Resolved By | Resolution Notes |
  |----------|-----------|------------|---------------|-------------|------------------|
  | NVIDIA (NVDA) | SAM Technology & Infrastructure | [Date] | [Date] | Anna Chen | Position reduced to 6.5% via TWAP over 3 trading days |

- **Summary**: 2 active breaches requiring remediation, 1 resolved in past 30 days

**Talking Points**:
- **Complete Lifecycle View**: AI retrieves both active and resolved breaches from compliance database
- **Resolution Tracking**: Clear documentation of who resolved each breach and how
- **Duration Monitoring**: Days outstanding for accountability tracking

**Key Features Highlighted**: 
- **SAM_COMPLIANCE_VIEW**: Comprehensive breach history with resolution status
- **Compliance Analyzer**: Queries structured compliance alert data

##### Step 2: Retrieve PM Commitments from Engagement Notes

**Presenter Transition**:
> "Good, I can see we have 2 active breaches requiring attention. Now let me search our engagement notes to find what commitments portfolio managers made during remediation discussions..."

*Reasoning: Engagement notes document PM commitments made during compliance discussions. These commitments establish accountability and expected remediation actions.*

**User Input**: 
```
Search our engagement notes for any compliance discussions or PM commitments regarding Apple and Microsoft concentration breaches.
```

**Tools Used**:
- `search_engagement_notes` (Cortex Search) - Search for compliance discussion engagement notes

**Expected Response**:
- **Apple Engagement** (from compliance_discussion note):
  - Date: [Recent date]
  - PM: Anna Chen, Senior Portfolio Manager
  - Commitment: Reduce position to below 7.0% within 20 trading days
  - Target Weight: 6.5% post-remediation
  - Execution Approach: TWAP orders to minimise market impact
  - Status Update: Weekly updates to Compliance

- **Microsoft**: 
  - No compliance engagement note found
  - Status: 🟡 REQUIRES ENGAGEMENT - Schedule remediation discussion

**Talking Points**:
- **Commitment Retrieval**: AI finds specific PM commitments from engagement notes
- **Gap Identification**: Highlights securities without documented remediation plans
- **Accountability Context**: Meeting dates, attendees, and specific promises documented

**Key Features Highlighted**: 
- **SAM_ENGAGEMENT_NOTES**: Searchable engagement history including compliance discussions
- **Compliance Discussion Templates**: Structured notes with PM commitments and timelines

##### Step 3: Compare Current Positions Against Committed Targets

**Presenter Transition**:
> "I have the PM commitments. Now the key accountability question—have they actually executed? Let me check current positions against those committed targets..."

*Reasoning: Accountability requires comparing commitments to current reality. Portfolio data reveals whether promised reductions have been executed.*

**User Input**: 
```
What are the current weights for Apple and Microsoft in the SAM Technology & Infrastructure portfolio? Compare to the committed remediation targets.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query current portfolio weights from SAM_ANALYST_VIEW

**Expected Response**:
- **Position Comparison**:
  | Security | Committed Target | Current Weight | Status | Action Required |
  |----------|------------------|----------------|--------|-----------------|
  | Apple (AAPL) | 6.5% | 8.2% | ❌ NOT EXECUTED | 1.7% reduction needed |
  | Microsoft (MSFT) | N/A (no commitment) | 7.4% | 🟡 NO PLAN | Schedule engagement |

- **Remediation Gap Analysis**:
  - Apple: Commitment made but not yet executed (check if within timeline)
  - Microsoft: No remediation plan documented - escalation required

**Talking Points**:
- **Promise vs Reality**: Clear comparison of commitments against actual positions
- **Accountability Gap**: Identifies unfulfilled commitments with specific shortfalls
- **Escalation Triggers**: Highlights positions requiring management attention

**Key Features Highlighted**: 
- **SAM_ANALYST_VIEW**: Real-time position weights for comparison
- **Accountability Tracking**: AI synthesizes commitments with current data

##### Step 4: Generate Risk Committee Report with PDF

**Presenter Transition**:
> "I have the complete picture—breach status, PM commitments, and execution gaps. Let me retrieve the report template and generate a formal Risk Committee report..."

*Reasoning: Risk Committee oversight requires formal reporting with standardized structure. The report template ensures all required sections are included.*

**User Input**: 
```
Find the Risk Committee compliance report template and generate a formal PDF report with all our findings on breach status, PM commitments, and remediation recommendations.
```

**Tools Used**:
- `search_report_templates` (Cortex Search) - Retrieve Risk Committee Compliance Report template
- `pdf_generator` (Generic) - Generate branded PDF with `internal` audience

**Expected Response**:
- **Template Retrieved**: Risk Committee Compliance Report template with required sections
- **Report Generated**:
  - Executive Summary: 2 active breaches, 1 unfulfilled commitment, 1 missing remediation plan
  - Compliance Status Overview: Active breaches table with severity
  - Remediation Status: PM commitments and execution progress
  - Risk Assessment: Severity classification and trend analysis
  - Recommendations: 
    1. Escalate Apple remediation - commitment timeline expired
    2. Schedule Microsoft engagement - no remediation plan documented
  - Committee Actions Required: Approval checkboxes for escalation

- **PDF Generation**: Professional branded PDF with Simulated logo
- **Download Link**: Presigned URL for Risk Committee distribution

**Talking Points**:
- **Template-Guided Structure**: Report follows approved Risk Committee format
- **Comprehensive Coverage**: All required sections populated from analysis
- **Professional Deliverable**: Branded PDF ready for committee circulation
- **Audit Trail**: Complete documentation from breach to recommendation

**Key Features Highlighted**: 
- **SAM_REPORT_TEMPLATES**: Standardized report templates ensure consistency
- **Template + Data Synthesis**: AI combines template guidance with analytical findings
- **PDF Generation**: Professional branded documents for governance reporting

#### Scenario Wrap-up

**Business Impact Summary**:
- **Tracking Efficiency**: Complete remediation lifecycle in single workflow
- **Accountability**: Clear documentation of commitments vs execution
- **Committee Preparation**: Template-guided reports with professional PDF output
- **Gap Identification**: Automatic flagging of missing remediation plans
- **Audit Trail**: End-to-end documentation from breach to committee action

**Technical Differentiators**:
- **Three-Tool Integration**: Compliance alerts + engagement notes + portfolio data combined
- **Lifecycle Tracking**: From breach detection through PM commitment to execution verification
- **Template-Guided Reporting**: Standardized Risk Committee report structure
- **PDF Generation**: Professional branded documents for formal governance reporting

---

### Compliance Advisor - Complete Compliance Assessment (Catch-All)

#### Business Context Setup

**Persona**: James, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Compliance officers sometimes need a complete compliance assessment with a single request when preparing for urgent regulatory inquiries or audit requests—requiring the AI to autonomously orchestrate all compliance tools across breach history, current positions, policy requirements, engagement commitments, and formal reporting.  
**Value Proposition**: The Compliance Advisor demonstrates complete autonomous orchestration by selecting and sequencing all six tools from a single comprehensive question, delivering an audit-ready compliance report with professional PDF output without step-by-step guidance.

**Agent**: `compliance_advisor`  
**Data Available**: Compliance breach alerts with resolution status, portfolio holdings across 10 strategies, policy documents, engagement records with PM commitments, report templates

#### Demo Flow

**Scene Setting**: James receives an urgent request from the FCA for a compliance status report on SAM Technology & Infrastructure. He has 30 minutes to prepare a complete assessment including breach history, current positions, policy thresholds, PM commitments, and a formal Risk Committee report with PDF.

##### Step 1: Complete Compliance Assessment (All Tools)

**User Input**: 
```
Conduct a complete compliance assessment for SAM Technology & Infrastructure including:
1. Historical breach alerts showing which have been resolved and which remain active
2. Current portfolio positions checked against concentration limits (single position and issuer)
3. Policy thresholds from our Concentration Risk Policy 
4. Any engagement notes documenting PM commitments for remediation
5. A formal Risk Committee compliance report using the appropriate template
6. Generate a professional PDF for FCA submission
```

**Tools Used**:
- `compliance_analyzer` (Cortex Analyst) - Query breach history with resolution status from SAM_COMPLIANCE_VIEW
- `quantitative_analyzer` (Cortex Analyst) - Check current portfolio positions against concentration limits
- `search_policies` (Cortex Search) - Retrieve Concentration Risk Policy thresholds and remediation requirements
- `search_engagement_notes` (Cortex Search) - Find PM commitments from compliance discussion notes
- `search_report_templates` (Cortex Search) - Retrieve Risk Committee Compliance Report template
- `pdf_generator` (Generic) - Generate branded PDF with `external_regulatory` audience

**Expected Response**:
- **Breach History**:
  - Active breaches: Apple (8.2%), Microsoft (7.4%) in SAM Technology & Infrastructure
  - Resolved breaches: NVIDIA (reduced to 6.5% by Anna Chen)
  - Days outstanding and severity classification for each

- **Current Position Analysis**:
  - All positions checked against 6.5% warning and 7.0% breach thresholds
  - Industry breakdown by SIC classification (Semiconductors, Software, Hardware)
  - Concentration risk summary with flagged positions

- **Policy Requirements**:
  - Single position concentration: 6.5% warning, 7.0% breach
  - Remediation timeline: 30 days from breach identification
  - Committee notification: Within 5 business days
  - FCA reporting requirements

- **PM Commitments**:
  - Apple: Commitment to reduce to 6.5% within 20 trading days (Anna Chen)
  - Microsoft: No engagement documented - requires scheduling
  - Execution status for each commitment

- **Formal Report**:
  - Template-guided Risk Committee Compliance Report
  - Executive summary, breach details, remediation status, recommendations
  - Committee actions required section with approval checkboxes

- **PDF Generation**:
  - Professional branded PDF with Simulated logo
  - External regulatory formatting for FCA submission
  - Presigned download URL

**Talking Points**:
- **Autonomous Orchestration**: AI independently selects and sequences all six compliance tools
- **Single-Query Capability**: Complete compliance assessment from one comprehensive question
- **Regulatory Ready**: Professional PDF formatted for FCA submission
- **Template-Guided Output**: Standardized Risk Committee report structure

**Key Features Highlighted**: 
- **Six-Tool AI Orchestration**: Agent autonomously determines tool sequence across compliance alerts, holdings, policies, engagement notes, templates, and PDF generation
- **Breach Lifecycle Integration**: Historical alerts with resolution status combined with current positions
- **Policy + Holdings Integration**: Thresholds merged with position data for breach detection
- **Engagement Context**: PM commitments provide accountability context for remediation tracking
- **Template-Guided Reporting**: Standardized report structure ensures consistency and completeness
- **Professional Documentation**: Branded PDF ready for regulatory submission

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Response**: Complete compliance assessment with formal PDF in under 10 minutes
- **Regulatory Ready**: Professional output suitable for FCA or auditor submission
- **Comprehensive Coverage**: Combines breach history, current positions, policy, engagement, and formal reporting
- **Audit Trail**: End-to-end documentation from breach detection to regulatory submission

**Technical Differentiators**:
- **Six-Tool Integration**: Demonstrates full Compliance Advisor capability in single autonomous query
- **Breach Lifecycle Tracking**: From alert history through PM commitment to current status
- **Policy-Aware Analysis**: AI applies exact policy thresholds to holdings data
- **Template-Guided Synthesis**: Report templates ensure governance-appropriate output
- **Autonomous Operation**: True AI agent capability for comprehensive compliance management

