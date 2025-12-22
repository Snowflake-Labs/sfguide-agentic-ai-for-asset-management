# SAM Demo - Middle Office Operations Scenarios

Complete demo scenarios for Middle Office Operations role with step-by-step conversations, expected responses, and data flows.

---

## Middle Office Operations

### Middle Office Copilot - NAV Calculation & Settlement Monitoring

#### Business Context Setup

**Persona**: Sarah, Middle Office Operations Manager at Snowcrest Asset Management  
**Business Challenge**: Middle office operations teams must monitor trade settlements, reconciliation breaks, NAV calculations, corporate actions, and cash management across multiple portfolios and custodians. Manual monitoring is time-consuming, error-prone, and fails to provide real-time exception alerts, risking operational failures, NAV errors, and settlement penalties.  
**Value Proposition**: AI-powered operations intelligence that provides real-time monitoring of all middle office processes, automated exception detection and root cause analysis, and intelligent remediation recommendations—transforming reactive operational fire-fighting into proactive exception management.

**Agent**: `middle_office_copilot`  
**Data Available**: 10 portfolios, 3 custodians, daily settlement activity, reconciliation data, NAV calculations, corporate actions, cash positions

#### Demo Flow

**Scene Setting**: It's 4:00 PM GMT and Sarah needs to review today's operational status across all middle office functions before the daily NAV calculation at 6:00 PM. She needs to quickly identify and resolve any settlement failures, reconciliation breaks, or issues that could impact tonight's NAV.

##### Step 1: Settlement Failure Monitoring
**User Input**: 
```
Show me all failed settlements from the past 3 business days and help me understand what's causing them.
```

**Tools Used**:
- `middle_office_analyzer` (Cortex Analyst) - Query FACT_TRADE_SETTLEMENT for Status='Failed' in last 3 days from SAM_MIDDLE_OFFICE_VIEW

**Expected Response**:
- Table showing: Trade ID, Security, Counterparty, Settlement Amount, Days Old, Status, Failure Reason
- Severity flags: 🚨 FAILED (>T+2 days old - critical), ⚠️ PENDING (within T+2 window)
- Root cause analysis for each failure (SSI mismatch, insufficient securities, etc.)
- Specific remediation steps with ETAs and responsible parties
- Total failed settlement value and counterparty breakdown
- Data timestamp: "As of DD MMM YYYY HH:MM"

**Talking Points**:
- **Real-Time Operations Monitoring**: Instant visibility into settlement status across all counterparties
- **Automated Root Cause Analysis**: AI identifies specific failure reasons (SSI mismatch, counterparty issues)
- **Severity Classification**: Critical vs pending settlements based on age and regulatory requirements
- **Actionable Remediation**: Specific steps to resolve each failure with clear ownership

**Key Features Highlighted**: 
- **Operational Intelligence**: Real-time exception detection across all settlement activity
- **Root Cause Identification**: Automated analysis of failure reasons and remediation paths
- **Regulatory Awareness**: T+2 settlement monitoring with escalation for aged failures

##### Step 2: Reconciliation Break Investigation

**Presenter Transition**:
> "Settlement failures are under control with clear remediation paths. But settlement is only one piece of the puzzle—we also need to check for reconciliation breaks that could impact tonight's NAV. Let me review today's reconciliation status across all portfolios..."

*Reasoning: Settlements and reconciliation are interdependent; a settlement failure often causes a reconciliation break. This step ensures we have visibility across all operational risks before NAV calculation.*

**User Input**: 
```
Summarize today's reconciliation breaks for all portfolios and flag any that are critical.
```

**Tools Used**:
- `middle_office_analyzer` (Cortex Analyst) - Query FACT_RECONCILIATION for Status='Open' breaks from SAM_MIDDLE_OFFICE_VIEW, ordered by Difference DESC

**Expected Response**:
- Overall reconciliation status: % matched, break counts by type and severity
- Table of critical breaks: Break Type, Portfolio, Security, Difference Amount, Status, Severity
- Severity classification:
  - 🚨 CRITICAL: Position breaks >£1M or >1% of NAV
  - ⚠️ HIGH: Cash breaks >£100K or >0.1% of NAV
  - Medium: Timing differences <£100K
- Root cause analysis for each critical break (corporate action, trade timing, system issue)
- Resolution timeline and actions required
- Impact on NAV calculation if unresolved

**Talking Points**:
- **Intelligent Break Prioritization**: AI automatically classifies breaks by severity and NAV impact
- **Root Cause Analysis**: Identifies whether breaks are due to corporate actions, timing, or system errors
- **NAV Impact Assessment**: Calculates potential NAV errors if breaks remain unresolved
- **Resolution Guidance**: Specific remediation steps with timeline to resolution

**Key Features Highlighted**: 
- **Break Classification**: Automated severity assessment based on amount and type
- **Corporate Action Detection**: Links breaks to unprocessed corporate actions
- **NAV Protection**: Identifies breaks that could cause NAV calculation errors

##### Step 3: NAV Calculation Status

**Presenter Transition**:
> "Reconciliation breaks are identified and prioritised. With 90 minutes until NAV calculation deadline, let me check the current NAV status across all funds and identify any anomalies that could indicate underlying issues we've missed..."

*Reasoning: NAV calculation is the culmination of all middle office processes. Checking NAV status validates whether settlement and reconciliation issues are impacting valuations.*

**User Input**: 
```
What's the status of today's NAV calculation across all funds? Are there any anomalies I need to investigate?
```

**Tools Used**:
- `middle_office_analyzer` (Cortex Analyst) - Query FACT_NAV_CALCULATION for latest NAV by portfolio from SAM_MIDDLE_OFFICE_VIEW

**Expected Response**:
- NAV calculation summary: Completed funds, pending review, investigating
- Table by fund: Fund Name, NAV, Daily Change %, Status, Anomalies Detected
- Anomaly alerts:
  - ⚠️ ANOMALY DETECTED: >2% NAV change without corresponding market movement
  - Include expected vs actual NAV comparison
- Root cause investigation for flagged anomalies:
  - Unprocessed corporate actions affecting NAV
  - Reconciliation breaks impacting positions
  - Large redemptions or subscriptions
- Approval recommendations: Which NAVs are safe to approve vs which need investigation
- Timeline: Target submission time to fund accountants

**Talking Points**:
- **Automated Anomaly Detection**: AI identifies unusual NAV movements requiring investigation
- **Expected vs Actual Analysis**: Compares NAV change to market index movements
- **Root Cause Intelligence**: Links NAV anomalies to specific operational issues (breaks, corporate actions)
- **Approval Workflow**: Clear recommendations on which NAVs are ready vs need investigation

**Key Features Highlighted**: 
- **NAV Anomaly Detection**: Automated identification of unusual valuation movements
- **Cross-Functional Analysis**: Links NAV issues to reconciliation breaks and corporate actions
- **Approval Intelligence**: Risk-based recommendations for NAV approval

##### Step 4: Corporate Action Processing Status

**Presenter Transition**:
> "Current NAV calculations look clean with anomalies explained. But the best operations teams think ahead—corporate actions due this week could cause tomorrow's issues. Let me review what's coming up and ensure we're prepared..."

*Reasoning: Proactive operations management requires forward-looking visibility. Corporate action review prevents tomorrow's reconciliation breaks and NAV issues.*

**User Input**: 
```
Show me all pending corporate actions for the next 5 business days and highlight any that require immediate processing.
```

**Tools Used**:
- `middle_office_analyzer` (Cortex Analyst) - Query FACT_CORPORATE_ACTIONS for upcoming actions from SAM_MIDDLE_OFFICE_VIEW
- `search_custodian_reports` (Cortex Search) - Get custodian notifications for pending corporate actions

**Expected Response**:
- Table: Security, Action Type, Ex-Date, Payment Date, Impact Value, Status, Priority
- Priority flags:
  - ⏰ DUE TODAY: Ex-date today, must process immediately
  - ⚠️ PENDING: Due within 2 days, preparation required
  - 🔍 RESEARCH NEEDED: Complex action requiring investigation (spin-offs, mergers)
- Processing recommendations for each action:
  - Dividend accruals for NAV calculation
  - Stock split position updates
  - Cash forecasting for payment dates
- Impact on NAV and cash positions
- Coordination requirements (trading desk, portfolio accounting)

**Talking Points**:
- **Proactive Corporate Action Management**: Forward-looking view of all upcoming events
- **Priority-Based Alerts**: Automatic flagging of actions requiring immediate processing
- **NAV Impact Calculation**: Shows how each corporate action affects tonight's NAV
- **Cross-Team Coordination**: Identifies which teams need to be involved for complex actions

**Key Features Highlighted**: 
- **Forward-Looking Monitoring**: 5-day corporate action calendar with priority classification
- **Processing Intelligence**: Automated recommendations for how to handle each action type
- **Impact Analysis**: Calculates NAV and cash impact of all pending actions

#### Scenario Wrap-up

**Business Impact Summary**:
- **Operational Efficiency**: Reduced manual monitoring time by 70% through automated exception detection
- **Risk Reduction**: Proactive identification of settlement failures, reconciliation breaks, and NAV anomalies before they become critical
- **NAV Accuracy**: Prevented NAV errors through automated anomaly detection and corporate action tracking
- **Regulatory Compliance**: Timely settlement monitoring ensures compliance with T+2 regulations and penalty avoidance

**Technical Differentiators**:
- **Real-Time Operations Intelligence**: Continuous monitoring across all middle office functions (settlement, reconciliation, NAV, corporate actions, cash)
- **Automated Root Cause Analysis**: AI-powered investigation of failures, breaks, and anomalies with specific remediation recommendations
- **Cross-Functional Integration**: Links operational issues across settlement, reconciliation, and NAV calculations for comprehensive root cause identification
- **Severity-Based Prioritization**: Intelligent classification of exceptions by business impact and regulatory urgency

---

### Middle Office Copilot - Complete Operational Status (Catch-All)

#### Business Context Setup

**Persona**: Sarah, Middle Office Operations Manager at Snowcrest Asset Management  
**Business Challenge**: Operations managers sometimes need a complete operational status report with a single request when preparing for management calls or responding to urgent escalations—requiring comprehensive visibility across all middle office functions simultaneously.  
**Value Proposition**: The Middle Office Copilot demonstrates complete autonomous orchestration by analysing all operational domains from a single comprehensive question, delivering a full operational picture without step-by-step guidance.

**Agent**: `middle_office_copilot`  
**Data Available**: 10 portfolios, 3 custodians, settlement activity, reconciliation data, NAV calculations, corporate actions, cash positions

#### Demo Flow

**Scene Setting**: Sarah has 5 minutes before the daily operations call with senior management. She needs a complete operational status across all functions immediately.

##### Step 1: Complete Operational Status with PDF (All Functions)

**User Input**: 
```
Give me a complete operational status report covering all settlement failures with root cause analysis, reconciliation breaks with resolution status, NAV calculation anomalies, corporate action processing status, and cash position summary across all portfolios and custodians. Generate a professional PDF for the management call.
```

**Tools Used**:
- `middle_office_analyzer` (Cortex Analyst) - Comprehensive query across FACT_TRADE_SETTLEMENT, FACT_RECONCILIATION, FACT_NAV_DAILY, FACT_CORPORATE_ACTIONS, FACT_CASH_POSITIONS from SAM_MIDDLE_OFFICE_VIEW
- `pdf_generator` (Generic) - Generate branded PDF with `internal` audience

**Expected Response**:
- **Settlement Status**: Failed/pending trades with severity flags and root cause
- **Reconciliation Summary**: Open breaks by portfolio and custodian with ageing
- **NAV Status**: Today's NAV calculations with any anomalies or warnings
- **Corporate Actions**: Pending actions requiring attention before NAV deadline
- **Cash Positions**: Summary by currency and custodian with any funding concerns
- **Priority Matrix**: Consolidated view of all issues by urgency and impact
- **Recommended Actions**: Specific remediation steps with ownership and ETAs
- **PDF Generation**: Professional branded PDF with Snowcrest logo
- **Download Link**: Presigned URL for immediate access

**Talking Points**:
- **Comprehensive Query**: Single question covers all middle office operational domains
- **Cross-Function Analysis**: AI identifies connections between operational issues
- **Management Ready**: Output structured for senior management with professional PDF
- **Professional Deliverable**: Branded PDF ready for management call distribution

**Key Features Highlighted**: 
- **Multi-Domain Analysis**: Complete operational visibility from single query
- **Root Cause Integration**: Connects issues across settlement, reconciliation, and NAV
- **Priority-Based Reporting**: Automatically classifies issues by business impact
- **PDF Generation**: Professional branded documents for operations reporting

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Response**: Complete operational status with PDF available in under 2 minutes
- **Comprehensive View**: All middle office functions visible in single output
- **Management Efficiency**: Hours of status gathering compressed into single query
- **Professional Deliverables**: Branded PDF documents ready for management distribution

**Technical Differentiators**:
- **Cross-Function Intelligence**: Single query spans all operational domains
- **Integrated Analysis**: AI connects related issues across functions
- **Autonomous Operation**: True AI agent capability for operations management
- **PDF Generation**: Professional branded documents for formal operations reporting

