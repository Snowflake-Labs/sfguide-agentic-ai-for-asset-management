---
doc_type: report_templates
linkage_level: global
variant_id: risk_committee_compliance_report
word_count_target: 2000
placeholders:
  required: []
---

# Risk Committee Compliance Report

## Executive Summary
Provide a 2-3 sentence overview including:
- Portfolio name(s) and reporting date
- Total number of active breaches and warnings
- Key remediation status (on track, overdue, requires escalation)
- Overall compliance risk assessment (Low/Moderate/High/Critical)

## Compliance Status Overview

### Active Breaches
Present a summary table of all active compliance breaches:

| Portfolio | Security | Breach Type | Current Value | Threshold | Breach Date | Days Outstanding | Severity |
|-----------|----------|-------------|---------------|-----------|-------------|------------------|----------|
| [Fill from FACT_COMPLIANCE_ALERTS where ResolvedDate IS NULL] |

### Warnings Under Monitoring
Present positions in warning status that require monitoring:

| Portfolio | Security | Warning Type | Current Value | Warning Threshold | Breach Threshold | Trend |
|-----------|----------|--------------|---------------|-------------------|------------------|-------|
| [Fill from compliance_analyzer or quantitative_analyzer] |

## Breach Details and Analysis

For each active breach, provide:
### [Security Name] - [Breach Type]
- **Portfolio**: [Portfolio name]
- **Alert Date**: [Date breach was first identified]
- **Current Status**: [Active/Pending Remediation/Overdue]
- **Days Outstanding**: [Number of days since breach]
- **Current Value**: [Current weight/grade] vs **Threshold**: [Policy limit]
- **Excess Exposure**: [Amount/percentage over threshold]
- **Dollar Impact**: [Market value of excess position]
- **Root Cause**: [Why the breach occurred - market movement, position sizing, etc.]

## Remediation Status

### PM Commitments and Actions
Summarise portfolio manager commitments from engagement notes:

| Security | PM Name | Commitment Date | Commitment | Target Date | Status |
|----------|---------|-----------------|------------|-------------|--------|
| [Fill from search_engagement_notes] |

### Execution Progress
For each breach with a remediation plan:
- **Original Commitment**: [What was promised]
- **Current Position**: [Current weight vs committed target]
- **Execution Status**: ✅ On Track / ⚠️ Behind Schedule / ❌ Not Started
- **Remaining Actions**: [What still needs to be done]

## Policy Compliance Summary

### Concentration Risk Policy
Reference key thresholds from Concentration Risk Policy:
- Single position warning threshold: 6.5%
- Single position breach threshold: 7.0%
- Issuer concentration limit: [Per policy]
- Sector concentration limit: [Per policy]
- Remediation timeline: 30 days from breach identification

### ESG Requirements (if applicable)
For ESG-labelled portfolios:
- Minimum ESG grade: BBB
- Exclusion criteria compliance
- Controversy screening status

### Governance Requirements
- Investment Committee notification: Required within 5 business days of breach
- Documentation requirements: Investment Committee Memo
- Escalation path: [Per policy]

## Risk Assessment

### Severity Classification
Classify each breach by severity:

| Severity | Criteria | Current Count |
|----------|----------|---------------|
| 🚨 Critical | >2% over threshold OR >45 days outstanding | [Count] |
| 🔴 High | 1-2% over threshold OR 30-45 days outstanding | [Count] |
| 🟠 Medium | 0.5-1% over threshold OR 15-30 days outstanding | [Count] |
| 🟡 Low | <0.5% over threshold AND <15 days outstanding | [Count] |

### Trend Analysis
- **Improving**: Positions being reduced, on track for remediation
- **Stable**: No change in breach status
- **Deteriorating**: Breach severity increasing, remediation behind schedule

### Overall Risk Rating
Provide overall compliance risk assessment: **[Low/Moderate/High/Critical]**

Rationale: [Explain the rating based on number of breaches, severity distribution, remediation progress, and policy compliance]

## Recommendations

### Immediate Actions (Next 5 Business Days)
List urgent actions required:
1. [Specific action with responsible party and deadline]
2. [Specific action with responsible party and deadline]

### Near-Term Actions (Next 30 Days)
List actions for the coming month:
1. [Specific action with responsible party and deadline]
2. [Specific action with responsible party and deadline]

### Monitoring Items
List positions requiring ongoing monitoring:
1. [Position and monitoring frequency]
2. [Position and monitoring frequency]

## Committee Actions Required

### Approvals Needed
- [ ] Acknowledge breach status and remediation plans
- [ ] Approve remediation timeline extensions (if any)
- [ ] Approve escalation to Board Risk Committee (if required)

### Follow-up Items
- Next compliance review date: [Date]
- PM accountability review: [Date if applicable]
- FCA reporting deadline: [Date if applicable]

---

**Document Classification**: Internal - Risk Committee  
**Report Date**: [Current timestamp]  
**Report Period**: [Reporting period covered]  
**Prepared By**: Compliance Team  
**Next Review**: [Scheduled review date]

---

## Section Requirements

REQUIRED SECTIONS (in order):
1. Executive Summary - High-level compliance status and key findings
2. Compliance Status Overview - Active breaches and warnings tables
3. Breach Details and Analysis - Detailed analysis of each breach
4. Remediation Status - PM commitments and execution progress
5. Policy Compliance Summary - Reference to relevant policy thresholds
6. Risk Assessment - Severity classification and trend analysis
7. Recommendations - Prioritised action items
8. Committee Actions Required - Decisions needed from Risk Committee

## Data Sources

Populate this report using data from:
- `compliance_analyzer` - Breach history, alert dates, severity, resolution status
- `quantitative_analyzer` - Current positions, weights, ESG grades
- `search_policies` - Policy thresholds and remediation requirements
- `search_engagement_notes` - PM commitments and engagement history

## Analysis Instructions

ANALYSIS GUIDELINES:

1. **Accuracy**: All breach data must come from compliance_analyzer or quantitative_analyzer
2. **Policy Alignment**: Reference exact thresholds from search_policies results
3. **Accountability**: Include PM names and specific commitments from engagement notes
4. **Severity-Based Prioritisation**: Order breaches by severity (Critical → Low)
5. **Actionable Recommendations**: Each recommendation must have owner and deadline
6. **Professional Tone**: Risk Committee-appropriate language (formal, factual, objective)

MARKDOWN FORMATTING:
- Use tables for breach and remediation status
- Use status indicators (🚨 🔴 🟠 🟡 ✅ ⚠️ ❌) for quick visual scanning
- Use bold for key metrics and thresholds
- Use bullet points for action items
- Use checkboxes for committee approval items
- Include horizontal rule (---) before footer

## Agent Workflow

AGENT WORKFLOW:

1. Search for this template using: "risk committee compliance report template"
2. Gather compliance data:
   - Use compliance_analyzer for breach history and alerts
   - Use quantitative_analyzer for current positions and weights
   - Use search_policies for policy thresholds
   - Use search_engagement_notes for PM commitments
3. Analyse and classify breaches by severity
4. Assess remediation progress against commitments
5. Synthesize analysis following template structure
6. Generate markdown document with all sections populated
7. Call pdf_generator with:
   - markdown_content: The completed report
   - report_title: "Risk Committee Compliance Report - [Date]"
   - document_audience: "internal"
8. Return the PDF download link to the user

The template provides structure and guidance, but the agent is responsible for:
- Querying all relevant data sources
- Calculating severity classifications
- Comparing current status against PM commitments
- Writing objective, factual compliance assessment
- Ensuring all required sections are included


