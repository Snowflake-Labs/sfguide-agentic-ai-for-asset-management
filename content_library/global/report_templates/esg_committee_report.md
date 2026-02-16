---
doc_type: report_templates
linkage_level: global
variant_id: esg_committee_report
word_count_target: 2500
placeholders:
  required: []
---

# ESG Committee Report

## Executive Summary
Provide a 3-4 sentence overview including:
- Portfolio name(s) and reporting date
- Total number of ESG controversies identified (by severity: High/Medium/Low)
- Key policy compliance status (breaches, at-risk positions)
- Overall ESG risk assessment (Low/Moderate/High/Critical)
- Primary recommendation (immediate action required vs monitoring)

## Controversy Scan Results

### High Severity Controversies
Present a summary table of High severity ESG issues requiring immediate attention:

| Company | Ticker | Controversy Type | Source | Report Date | Portfolio Exposure | ESG Grade | Required Action |
|---------|--------|------------------|--------|-------------|-------------------|-----------|-----------------|
| [Fill from search_ngo_reports for SEVERITY_LEVEL = High] |

For each High severity controversy, provide:
- **Issue Summary**: Brief description of the controversy
- **Impact Assessment**: Scope and scale of the issue
- **Policy Implication**: Which policy requirements are triggered
- **Timeline**: How long since the issue was reported

### Medium Severity Controversies
Present Medium severity issues requiring monitoring:

| Company | Ticker | Controversy Type | Source | Report Date | Portfolio Exposure | ESG Grade | Monitoring Status |
|---------|--------|------------------|--------|-------------|-------------------|-----------|-------------------|
| [Fill from search_ngo_reports for SEVERITY_LEVEL = Medium] |

### Low Severity Issues
Summary count of Low severity issues with aggregate exposure.

## Portfolio Exposure Analysis

### Exposure by Severity
Summarise total portfolio exposure to ESG controversies:

| Severity | Companies Affected | Total Exposure (£M) | % of Portfolio | Weighted ESG Grade |
|----------|-------------------|---------------------|----------------|-------------------|
| 🔴 High | [Count] | [Amount] | [%] | [Grade] |
| 🟡 Medium | [Count] | [Amount] | [%] | [Grade] |
| 🟢 Low | [Count] | [Amount] | [%] | [Grade] |
| **Total** | [Count] | [Amount] | [%] | - |

### Exposure by Portfolio
For ESG-labelled portfolios, show controversy exposure:

| Portfolio | High Severity Exposure | Medium Severity Exposure | Total Controversy Exposure | % of Portfolio |
|-----------|------------------------|-------------------------|---------------------------|----------------|
| SAM ESG Leaders Global Equity | [Amount] | [Amount] | [Amount] | [%] |
| SAM Renewable & Climate Solutions | [Amount] | [Amount] | [Amount] | [%] |
| SAM Sustainable Global Equity | [Amount] | [Amount] | [Amount] | [%] |

### Top Holdings with Controversies
Ranked list of largest exposures to companies with active controversies:

| Rank | Company | Ticker | Controversy Severity | Portfolio Weight | Market Value | ESG Grade |
|------|---------|--------|---------------------|------------------|--------------|-----------|
| 1 | [Company] | [Ticker] | [Severity] | [%] | [Amount] | [Grade] |
| 2 | [Company] | [Ticker] | [Severity] | [%] | [Amount] | [Grade] |
| ... | | | | | | |

## Policy Compliance Status

### ESG Grade Requirements
From Sustainable Investment Policy:
- Minimum ESG grade for ESG-labelled portfolios: BBB
- High severity controversy threshold: Zero tolerance (requires IC review)
- Medium severity controversy threshold: Escalated engagement required
- Remediation timeline: 90 days for grade breaches, 30 days for High severity controversies

### Compliance Assessment

| Requirement | Status | Details |
|-------------|--------|---------|
| ESG Grade Floor (BBB) | ✅ COMPLIANT / 🚨 BREACH | [Details of any breaches] |
| High Severity Tolerance | ✅ COMPLIANT / 🚨 BREACH | [Count of High severity exposures] |
| Engagement Requirements | ✅ CURRENT / ⚠️ OVERDUE | [Engagement status summary] |

### Policy Breaches Requiring Action
For each policy breach identified:
- **Company**: [Name and ticker]
- **Breach Type**: [ESG grade below BBB / High severity controversy / Engagement overdue]
- **Policy Reference**: [Section of Sustainable Investment Policy]
- **Required Action**: [Per policy requirements]
- **Timeline**: [Days to remediation deadline]

## Engagement History

### Active Engagements
Summary of ongoing ESG engagements with controversy-affected companies:

| Company | Engagement Date | Topic | Commitments Made | Status | Next Steps |
|---------|-----------------|-------|------------------|--------|------------|
| [From search_engagement_notes] |

### Engagement Gaps
Companies with controversies but no recent engagement:
- [Company 1]: No engagement in past 12 months - **REQUIRES IMMEDIATE OUTREACH**
- [Company 2]: Last engagement [X] months ago - **FOLLOW-UP RECOMMENDED**

### Commitment Tracking
For companies with prior ESG commitments:
- **Commitment Met**: [List of companies meeting commitments]
- **Commitment Pending**: [List of companies with commitments still in progress]
- **Commitment Failed**: [List of companies failing to meet commitments - escalation required]

## Remediation Plan

### Immediate Actions (Within 5 Business Days)
For High severity controversies and policy breaches:

| Priority | Company | Action Required | Responsible | Deadline | Escalation Path |
|----------|---------|-----------------|-------------|----------|-----------------|
| 1 | [Company] | [Action] | [Owner] | [Date] | Investment Committee |
| 2 | [Company] | [Action] | [Owner] | [Date] | ESG Committee |

### Near-Term Actions (Within 30 Days)
For Medium severity controversies:

| Priority | Company | Action Required | Responsible | Deadline |
|----------|---------|-----------------|-------------|----------|
| 1 | [Company] | Initiate engagement | ESG Team | [Date] |
| 2 | [Company] | Request remediation plan | ESG Team | [Date] |

### Monitoring Actions (Ongoing)
Positions requiring enhanced monitoring:
- Weekly: [List of High severity positions]
- Bi-Weekly: [List of Medium severity positions]
- Monthly: [List of at-risk positions approaching thresholds]

## ESG Committee Actions Required

### Decisions Needed
- [ ] Acknowledge current ESG risk status and controversy exposures
- [ ] Approve escalation of High severity issues to Investment Committee
- [ ] Approve engagement strategy for Medium severity issues
- [ ] Approve monitoring plan for at-risk positions

### Investment Committee Referrals
If High severity controversies require IC review:
- [ ] Refer [Company] for IC review - High severity [controversy type]
- [ ] Recommend [hold/divest] pending IC decision

### Next Review
- Next ESG Committee meeting: [Date]
- Required updates: [List of items requiring follow-up reporting]

---

**Document Classification**: Internal - ESG Committee  
**Report Date**: [Current timestamp]  
**Report Period**: [Reporting period covered]  
**Prepared By**: ESG Risk Team  
**Next Review**: [Scheduled review date]

---

## Section Requirements

REQUIRED SECTIONS (in order):
1. Executive Summary - High-level ESG risk status and key findings
2. Controversy Scan Results - Detailed controversy analysis by severity
3. Portfolio Exposure Analysis - Quantified exposure to controversy-affected companies
4. Policy Compliance Status - Assessment against Sustainable Investment Policy
5. Engagement History - Prior ESG engagements and commitment tracking
6. Remediation Plan - Prioritised actions with timelines
7. ESG Committee Actions Required - Decisions and approvals needed

## Data Sources

Populate this report using data from:
- `search_ngo_reports` - ESG controversies with severity classifications
- `quantitative_analyzer` - Portfolio exposure, ESG grades, position weights
- `search_policies` - Policy thresholds and remediation requirements
- `search_engagement_notes` - Engagement history and company commitments

## Analysis Instructions

ANALYSIS GUIDELINES:

1. **Severity-Based Prioritisation**: Always present High severity issues first, then Medium, then Low
2. **Quantify Exposure**: All controversy exposures must include £ amounts and % of portfolio
3. **Policy Integration**: Reference exact policy thresholds from Sustainable Investment Policy
4. **Engagement Context**: Include prior engagement history for each controversy-affected company
5. **Actionable Recommendations**: Each finding must have a specific action, owner, and deadline
6. **Severity Indicators**: Use 🔴 for High, 🟡 for Medium, 🟢 for Low severity throughout

MARKDOWN FORMATTING:
- Use tables for controversy lists and exposure summaries
- Use severity indicators (🔴 🟡 🟢) for visual classification
- Use bold for key metrics and policy thresholds
- Use checkboxes for committee action items
- Include horizontal rule (---) before footer

## Agent Workflow

AGENT WORKFLOW:

1. Search for this template using: "ESG committee report template"
2. Gather ESG data:
   - Use search_ngo_reports for controversy scan by severity
   - Use quantitative_analyzer for portfolio exposure and ESG grades
   - Use search_policies for policy thresholds
   - Use search_engagement_notes for engagement history
3. Classify controversies by severity (High/Medium/Low)
4. Calculate portfolio exposure to affected companies
5. Assess policy compliance against retrieved thresholds
6. Review engagement history for each affected company
7. Develop prioritised remediation plan
8. Synthesize analysis following template structure
9. Call pdf_generator with:
   - markdown_content: The completed report
   - report_title: "ESG Committee Report - [Date]"
   - document_audience: "internal"
10. Return the PDF download link to the user

The template provides structure and guidance, but the agent is responsible for:
- Querying all relevant data sources
- Classifying severity levels
- Calculating exposure amounts
- Comparing against policy requirements
- Writing objective, factual ESG risk assessment
- Ensuring all required sections are included


