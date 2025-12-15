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

