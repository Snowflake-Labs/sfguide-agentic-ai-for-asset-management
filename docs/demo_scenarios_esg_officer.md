# SAM Demo - ESG Officer Scenarios

Complete demo scenarios for ESG Officer role with step-by-step conversations, expected responses, and data flows.

---

## ESG Guardian

### ESG Guardian - Comprehensive ESG Risk Review

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG officers need to conduct comprehensive portfolio ESG risk reviews that systematically scan for controversies across NGO reports, calculate precise portfolio exposures to affected companies, validate against policy requirements and thresholds, review engagement history for stewardship context, and synthesize into severity-prioritized remediation plans with specific timelines and committee requirements. Traditional ESG monitoring requires days of manual NGO report review, spreadsheet exposure calculations, policy document cross-referencing, and engagement system searches—often missing the integration between controversy severity, portfolio materiality, policy compliance, and stewardship activities that drives effective ESG risk management.  
**Value Proposition**: AI-powered comprehensive ESG risk intelligence that seamlessly integrates controversy detection from NGO sources, portfolio exposure quantification, policy threshold validation, and engagement history tracking—delivering complete, action-ready ESG risk assessments with severity-based remediation plans in minutes instead of days.

**Agent**: `esg_guardian`  
**Data Available**: 200 NGO reports covering ESG controversies, portfolio holdings across 10 strategies (including 3 ESG-labelled), Sustainable Investment Policy, 150 engagement records

#### Demo Flow

**Scene Setting**: Sarah is preparing the monthly ESG Risk Committee report and needs to conduct a comprehensive risk review of the SAM ESG Leaders Global Equity portfolio. The committee meets in 2 days and requires a complete assessment of current ESG controversies, affected portfolio holdings with exact exposures, policy compliance verification, engagement status, and prioritized remediation recommendations. Sarah needs to scan recent NGO reports for High and Medium severity issues, quantify portfolio impact, verify against policy thresholds, check engagement history, and prepare formal recommendations—all before tomorrow's internal review meeting.

##### Step 1: Comprehensive ESG Risk Assessment
**User Input**: 
```
I need a comprehensive ESG risk review for our SAM ESG Leaders Global Equity portfolio. Can you:
1. Scan NGO reports for any recent High or Medium severity ESG controversies affecting our holdings
2. Check our portfolio holdings to calculate exact exposure to companies with these controversies
3. Review our Sustainable Investment Policy to confirm ESG grade requirements and controversy tolerance thresholds
4. Check our engagement history with any flagged companies to see if we've already initiated stewardship activities
5. Provide a complete remediation plan with severity-based timelines, required committee reviews, and documentation requirements
```

**Tools Used**:
- `search_ngo_reports` (Cortex Search) - Scan for recent ESG controversies by severity
- `quantitative_analyzer` (Cortex Analyst) - Calculate portfolio exposure to affected companies
- `search_policies` (Cortex Search) - Retrieve ESG policy requirements and thresholds
- `search_engagement_notes` (Cortex Search) - Check stewardship activities and commitments

**Expected Response**:
- **ESG Controversy Scan**:
  - High and Medium severity controversies from NGO reports:
  
  | Company | Ticker | Controversy Type | Severity | Source | ESG Grade |
  |---------|--------|------------------|----------|--------|-----------|
  | NVIDIA CORP | NVDA | Environmental | 🔴 High | Human Rights Monitor | A |
  | ALPHABET INC. | GOOGL | Labour Practices | 🟡 Medium | Climate Action Network | A |
  | RIBBON COMMUNICATIONS | RBBN | Labour Practices | 🟡 Medium | Global Sustainability Watch | AA |

- **Portfolio Exposure Analysis**:
  - Exposure by company with controversy severity:
  
  | Company | Severity | Weight | Exposure | ESG Grade |
  |---------|----------|--------|----------|-----------|
  | NVIDIA CORP | High | ~6% | ~$500M | A |
  | ALPHABET INC. | Medium | ~5% | ~$450M | A |
  | RIBBON COMMUNICATIONS | Medium | ~5% | ~$480M | AA |
  
  - Total controversy exposure: ~$1.4B (~16% of ESG portfolios)

- **Policy Compliance Verification**:
  - ESG Grade Floor: BBB minimum ✅ All holdings compliant
  - High Severity Controversy: NVIDIA requires IC review per §3.1 🚨 BREACH
  - Medium Severity: ALPHABET and RIBBON require escalated engagement per §3.2

- **Engagement History Review**:
  - NVIDIA: Prior engagement on environmental governance (3 months ago)
  - ALPHABET: Supply chain discussion (2 months ago) - commitments pending
  - RIBBON: No recent engagement - NEW ISSUE requiring outreach

- **Comprehensive Remediation Plan**:

  * **IMMEDIATE ACTIONS** (Within 5 Business Days):
    
    1. **NVIDIA CORP (NVDA)** - 🔴 High Priority
       - **Issue**: High severity environmental controversy (emissions increase, regulatory violations)
       - **Policy Requirement**: IC approval required to maintain position (§3.1)
       - **Action**: Convene Investment Committee review
       - **Engagement**: Reference prior environmental discussion, request updated remediation plan
       - **Timeline**: IC review within 5 business days, decision within 10 business days
       - **Documentation**: IC Memo, engagement letter, monitoring plan
       - **Exposure**: ~$500M across ESG portfolios
  
  * **NEAR-TERM ACTIONS** (Within 30 Days):
    
    2. **ALPHABET INC. (GOOGL)** - 🟡 Medium Priority
       - **Issue**: Medium severity labour practices controversy (supply chain gaps)
       - **Policy Requirement**: Escalated engagement per §3.2
       - **Action**: Follow-up on prior supply chain commitments
       - **Engagement**: Request progress report on worker grievance mechanisms
       - **Timeline**: Engagement within 15 business days, quarterly monitoring
       - **Documentation**: Engagement log, commitment tracking
    
    3. **RIBBON COMMUNICATIONS (RBBN)** - 🟡 Medium Priority
       - **Issue**: Medium severity labour practices controversy (overtime violations)
       - **Policy Requirement**: Escalated engagement per §3.2
       - **Action**: Initiate new engagement on labour practices
       - **Engagement**: Contact management, request labour policy improvements
       - **Timeline**: Engagement within 15 business days, quarterly monitoring
       - **Documentation**: Engagement initiation letter, response tracking
  
  * **GOVERNANCE & OVERSIGHT**:
    
    - **Investment Committee**:
      * Emergency meeting within 5 business days for NVIDIA high-severity review
      * Agenda: NVIDIA retention/divestment decision, engagement approval
      * Documentation: IC Memo with recommendation
    
    - **ESG Committee**:
      * Monthly ESG Risk Committee meeting
      * Agenda: Full controversy review, Medium severity engagements, quarterly monitoring
      * Documentation: ESG Risk Committee Report with 3-company analysis
    
    - **Compliance**:
      * Policy breach notification for NVIDIA high-severity controversy
      * Audit trail: Engagement letters, IC Memos, monitoring reports
  
  * **MONITORING & FOLLOW-UP**:
    - **Weekly**: NVIDIA engagement response and IC preparation
    - **Bi-Weekly**: ALPHABET supply chain commitment progress
    - **Monthly**: RIBBON labour practices engagement progress
    - **Quarterly**: All companies review in ESG Committee

- **ESG Risk Committee Summary**:
  
  * **Portfolio**: SAM ESG Leaders Global Equity
  * **Review Period**: Last 60 days
  * **Controversies Identified**: 3 companies (1 High severity, 2 Medium severity)
  * **Total Exposure**: ~$1.4B (~16% across ESG portfolios)
  * **Policy Breaches**: 1 breach (NVIDIA high-severity requires IC review)
  * **Immediate Actions Required**: 1 company (NVIDIA)
  * **Investment Committee Review**: Required within 5 business days
  * **Compliance Status**: ⚠️ **HIGH SEVERITY BREACH** - IC review required
  * **Recommendation**: **APPROVE** remediation plan with IC review, engagement escalations, and quarterly monitoring

**Talking Points**:
- **Comprehensive Risk Coverage**: Single query orchestrates 4 tools across NGO reports, portfolio holdings, policy requirements, and engagement history
- **Severity-Based Prioritization**: Automatic classification (High/Medium) with policy-driven remediation timelines
- **Policy-Integrated Analysis**: Controversy exposure automatically compared against Sustainable Investment Policy thresholds
- **Stewardship Context**: Engagement history provides critical context for remediation decisions (existing commitments vs new issues)
- **Actionable Remediation Plans**: Specific timelines, committee requirements, engagement actions, and documentation needs
- **Governance Ready**: Complete analysis suitable for Investment Committee and ESG Committee formal review

**Key Features Highlighted**: 
- **NGO Intelligence Network**: Cortex Search across 200 NGO reports identifies ESG controversies with severity classification
- **Portfolio Impact Quantification**: Cortex Analyst calculates precise exposure to affected companies with position ranking
- **Policy Compliance Engine**: Automatic threshold checking against Sustainable Investment Policy requirements
- **Stewardship Tracking**: Engagement history integration provides continuity and informs escalation decisions
- **Multi-Severity Framework**: Differentiated response protocols for High vs Medium severity with specific timelines
- **Audit Trail Generation**: Complete documentation roadmap for regulatory compliance and client reporting

##### Step 2: Generate ESG Committee Report PDF

**Presenter Transition**:
> "The analysis is complete with the comprehensive remediation plan. Now let me generate a formal PDF report for the ESG Committee meeting using our standard report format..."

*Reasoning: Formal ESG committee documentation requires professional PDF output following the standard ESG Committee report template for consistency and governance compliance.*

**User Input**: 
```
Generate a formal ESG Committee report PDF with all the findings, controversy details, and remediation recommendations. Use our standard ESG Committee report template.
```

**Tools Used**:
- `search_report_templates` (Cortex Search) - Retrieve ESG Committee report format requirements
- `pdf_generator` (Generic) - Generate branded PDF with `internal` audience

**Expected Response**:
- **Template Retrieved**: ESG Committee Report template with required sections:
  - Executive Summary
  - Controversy Scan Results (by severity)
  - Portfolio Exposure Analysis
  - Policy Compliance Status
  - Engagement History
  - Remediation Plan
  - Committee Actions Required

- **PDF Generation**: Professional branded PDF with Simulated logo
- **Template-Compliant Structure**: Report follows ESG Committee standard format
- **Internal Document Styling**: INTERNAL DOCUMENT badge, appropriate headers/footers
- **Download Link**: Presigned URL for immediate access

**Talking Points**:
- **Template-Guided Output**: Report follows standardized ESG Committee format
- **Professional Deliverable**: Formal PDF ready for ESG Committee circulation
- **Audit Trail**: Branded documentation suitable for ESG records
- **Governance Ready**: Consistent report structure across all ESG Committee meetings

**Key Features Highlighted**: 
- **SAM_REPORT_TEMPLATES**: Standardized report templates for consistent governance documentation
- **GENERATE_PDF_REPORT**: Branded PDF generation for ESG documentation
- **Complete Workflow**: From ESG risk analysis to formal, template-compliant PDF in single session

#### Scenario Wrap-up

**Business Impact Summary**:
- **Risk Detection Speed**: Comprehensive ESG risk review reduced from 2-3 days to under 10 minutes (99% time savings)
- **Coverage Completeness**: Systematic scan of 200 NGO reports vs manual review of 5-10 key sources
- **Decision Quality**: Policy-integrated analysis with engagement context enables confident, compliant remediation decisions
- **Governance Efficiency**: Audit-ready documentation and committee materials generated automatically
- **Professional Deliverables**: Branded PDF reports ready for ESG Committee and governance records

**Technical Differentiators**:
- **Multi-Source ESG Intelligence**: Integration of NGO reports, portfolio analytics, policy documents, and engagement records in unified analysis
- **Severity-Based Orchestration**: AI automatically prioritizes controversies by severity and applies differentiated response protocols
- **Policy-Aware AI**: Sustainable Investment Policy thresholds automatically retrieved and applied to controversy exposure calculations
- **Stewardship Integration**: Engagement history tracking provides critical context unavailable in traditional ESG monitoring systems
- **Governance Workflow Automation**: Complete remediation plans with specific timelines, committee requirements, and documentation needs
- **Real-Time Controversy Detection**: NGO report indexing within 48 hours enables rapid response to emerging ESG risks
- **PDF Generation**: Professional branded documents for formal ESG committee reporting

---

### ESG Guardian - Daily ESG Controversy Scanning

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG officers need to perform daily scans for new controversies affecting portfolio holdings—the most frequent ESG monitoring task. Traditional monitoring requires reviewing multiple NGO websites, news sources, and ESG data providers, then manually checking exposure.  
**Value Proposition**: AI-powered daily controversy scanning that quickly identifies new ESG issues, calculates portfolio exposure, and produces concise summaries for the ESG risk log.

**Agent**: `esg_guardian`  
**Data Available**: 200 NGO reports, portfolio holdings across 10 strategies, ESG policy documents

#### Demo Flow

**Scene Setting**: Sarah starts each morning with a quick ESG controversy scan to identify any new issues affecting portfolio companies. She needs to flag any problems and prepare a brief summary for the ESG risk meeting.

##### Step 1: Controversy Scan
**User Input**: 
```
Are there any new ESG controversies affecting our ESG-labelled portfolios? Check recent NGO reports for any High or Medium severity issues.
```

**Tools Used**:
- `search_ngo_reports` (Cortex Search) - Scan for recent ESG controversies
- `quantitative_analyzer` (Cortex Analyst) - Calculate portfolio exposure

**Expected Response**:
- **🔴 High Severity Issue**:
  - **NVIDIA CORP (NVDA)** - Environmental Concerns
  - Source: [NGO Organization] (recent date)
  - Portfolio Exposure: ~$500M across all ESG portfolios
  - Key Issues: Emissions increase, regulatory violations, governance gaps
  
- **🟡 Medium Severity Issues**:
  - **ALPHABET INC. (GOOGL)** - Labour Practices
    - Source: [NGO Organization] (recent date)
    - Portfolio Exposure: ~$450M across ESG portfolios
    - Key Issues: Supply chain labour gaps, worker grievance mechanisms
  - **RIBBON COMMUNICATIONS INC. (RBBN)** - Labour Practices
    - Source: [NGO Organization] (recent date)
    - Portfolio Exposure: ~$480M across ESG portfolios
    - Key Issues: Supply chain labour concerns, overtime violations

- **Policy Compliance Note**: All holdings currently meet ESG grade requirements (BBB minimum), but High severity controversy at NVIDIA requires IC review per policy

**Talking Points**:
- **Rapid Scanning**: AI searches across 200 NGO reports in seconds
- **Automatic Exposure Calculation**: Controversy scan includes portfolio impact assessment
- **Severity Classification**: Immediate prioritization by impact level

**Key Features Highlighted**: 
- **SAM_NGO_REPORTS**: Comprehensive NGO report library for controversy monitoring
- **Multi-Tool Orchestration**: Agent automatically calculates exposure alongside controversy scan

##### Step 2: Detailed Controversy Analysis

**Presenter Transition**:
> "The scan identified NVIDIA with a high-severity environmental controversy. The exposure numbers are helpful, but I need to understand the details of this issue before escalating..."

*Reasoning: The initial scan provides summary exposure data. Understanding the specific controversy details is essential for proper escalation and engagement planning.*

**User Input**: 
```
For the NVIDIA high-severity environmental issue, what are the specific details of the controversy and when was it reported? What exactly happened?
```

**Tools Used**:
- `search_ngo_reports` (Cortex Search) - Retrieve detailed controversy report

**Expected Response**:
- **Controversy Details**:
  - **Company**: NVIDIA CORP (NVDA)
  - **Severity**: 🔴 HIGH
  - **Category**: Environmental
  - **Source**: [NGO Organization Name]
  - **Report Date**: [Recent date within last 60 days]
- **Issue Summary**:
  - Specific environmental violations documented
  - Emissions data and regulatory concerns
  - Board oversight gaps identified
- **Impact Assessment**: Scale and scope of the environmental issue
- **Previous Commitments**: Any prior company statements on the issue

**Talking Points**:
- **Deep-Dive Capability**: AI retrieves full controversy context, not just summary
- **Source Attribution**: Clear provenance from NGO report
- **Escalation Context**: Detailed information supports IC review documentation

**Key Features Highlighted**: 
- **SAM_NGO_REPORTS**: Full controversy reports with detailed findings
- **Targeted Search**: Query specific company and issue type

##### Step 3: Policy Threshold Check

**Presenter Transition**:
> "Now I understand the issue. Let me check if this breach triggers any policy thresholds requiring escalation..."

*Reasoning: Policy compliance determines required actions. High severity controversies trigger specific escalation protocols.*

**User Input**: 
```
Check if the NVIDIA high-severity controversy breaches our Sustainable Investment Policy thresholds. What are our requirements for High severity controversies?
```

**Tools Used**:
- `search_policies` (Cortex Search) - ESG policy thresholds

**Expected Response**:
- **Policy Requirements** (from Sustainable Investment Policy):
  - High Severity Controversies: Zero tolerance - requires Investment Committee approval to maintain position
  - ESG Grade Floor: Minimum BBB for ESG-labelled funds
  - Remediation Timeline: 30 days for High severity, IC review within 5 business days
- **Breach Analysis**:
  - NVIDIA (NVDA): High severity environmental controversy 🚨 **POLICY BREACH**
  - Required Action: Investment Committee approval required to maintain position
  - Timeline: IC review within 5 business days
- **Policy Reference**: Sustainable Investment Policy §3.1 - High Severity Controversy Protocol

**Talking Points**:
- **Policy Integration**: Thresholds retrieved from authoritative Sustainable Investment Policy
- **Clear Escalation Path**: Policy specifies exactly what action is required
- **Audit Trail**: Policy reference documented for compliance records

**Key Features Highlighted**: 
- **SAM_POLICY_DOCS**: Complete policy requirements with section references
- **Breach Detection**: AI applies policy thresholds to controversy findings

##### Step 4: Investment Committee Escalation Memo

**Presenter Transition**:
> "There's a clear policy breach requiring IC review. Let me prepare an escalation memo for the Investment Committee with the recommended actions..."

*Reasoning: High severity policy breach requires formal IC escalation. The memo documents the issue, exposure, policy requirement, and recommended action.*

**User Input**: 
```
Given the policy breach identified for NVIDIA's high-severity environmental controversy, prepare an escalation memo for the Investment Committee with the controversy details, portfolio exposure, policy requirements, and recommended actions.
```

**Tools Used**:
- Synthesis of previous queries
- `search_report_templates` (Cortex Search) - IC memo format guidance

**Expected Response**:
- **INVESTMENT COMMITTEE ESCALATION MEMO**
- **Date**: [Current date]
- **Subject**: High Severity ESG Controversy - NVIDIA CORP (NVDA)
- **Priority**: 🔴 URGENT - Policy Breach Requiring IC Review
  
- **Issue Summary**:
  - Company: NVIDIA CORP (NVDA)
  - Severity: HIGH (Environmental)
  - Source: [NGO report reference]
  - Portfolio Exposure: ~$500M across ESG-labelled portfolios
  
- **Policy Requirement**:
  - Per Sustainable Investment Policy §3.1: High severity controversies require IC approval to maintain position
  - Timeline: IC decision required within 5 business days
  
- **Recommended Actions**:
  1. Convene IC review within 5 business days
  2. Options: (a) Divest position, (b) Approve retention with enhanced monitoring, (c) Initiate company engagement
  3. If retention approved: 30-day enhanced monitoring with bi-weekly ESG risk updates
  
- **ESG Officer Recommendation**: Initiate engagement with NVIDIA management requesting remediation plan before IC meeting

**Talking Points**:
- **Escalation Workflow**: Complete IC memo generated from controversy findings
- **Decision Framework**: Clear options presented with policy context
- **Actionable Output**: Ready for circulation to Investment Committee

**Key Features Highlighted**: 
- **Multi-Tool Synthesis**: Controversy + exposure + policy combined into decision memo
- **Governance Integration**: Output formatted for IC decision process

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: Daily ESG scan with escalation memo reduced from 45+ minutes to 10 minutes
- **Coverage**: Complete NGO report scan vs selective sampling
- **Consistency**: Same thorough check every day with policy-compliant escalation
- **Governance Ready**: IC-ready escalation memos generated automatically

**Technical Differentiators**:
- **NGO Report Scanning**: AI searches comprehensive NGO report library
- **Exposure Quantification**: Portfolio impact calculated automatically with controversy scan
- **Policy Integration**: Thresholds applied and breach escalation triggered automatically
- **Decision Documentation**: Complete escalation memos ready for Investment Committee

---

### ESG Guardian - ESG Rating Monitor

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG-labelled portfolios have minimum ESG grade requirements (BBB minimum). Monitoring grade compliance requires regular review of ESG scores across all holdings and identification of any grade breaches.  
**Value Proposition**: AI-powered ESG grade monitoring that quickly identifies any holdings below required thresholds and surfaces policy remediation requirements.

**Agent**: `esg_guardian`  
**Data Available**: ESG grades for 14,000+ securities, Sustainable Investment Policy

#### Demo Flow

**Scene Setting**: Sarah is conducting the weekly ESG grade review for ESG-labelled portfolios to ensure all holdings meet the minimum BBB requirement.

##### Step 1: ESG Grade Distribution
**User Input**: 
```
Show me the ESG grade distribution for our SAM ESG Leaders Global Equity portfolio. I need to see the breakdown from AAA to CCC.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - ESG grade analysis

**Expected Response**:
- **Grade Distribution**:
  | Grade | Count | Weight | Value (£M) |
  |---|---|---|---|
  | AAA | 12 | 18.5% | £92.5M |
  | AA | 28 | 32.1% | £160.5M |
  | A | 35 | 28.4% | £142.0M |
  | BBB | 15 | 12.8% | £64.0M |
  | BB | 3 | 5.2% | £26.0M |
  | B | 2 | 3.0% | £15.0M |
- **Investment Grade %**: 91.8%
- **Below Threshold**: 8.2%

**Talking Points**:
- **Complete Distribution**: Full ESG grade breakdown
- **Weight Analysis**: Not just counts but portfolio impact
- **Quick Assessment**: Overall ESG quality at a glance

**Key Features Highlighted**: 
- **SAM_ANALYST_VIEW**: Complete ESG data integration
- **Grade Aggregation**: AI summarizes ESG quality

##### Step 2: Grade Breach Identification

**Presenter Transition**:
> "I can see some holdings below investment grade. Let me identify exactly which holdings are below our BBB minimum threshold..."

*Reasoning: Grade distribution shows overall picture, but specific breach identification enables targeted action.*

**User Input**: 
```
Identify any holdings in the ESG Leaders portfolio that are below the BBB minimum threshold. Show me the specific companies and their ESG grades.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Breach identification

**Expected Response**:
- **Holdings Below BBB**:
  | Company | Ticker | ESG Grade | Weight | Value | Issue |
  |---|---|---|---|---|---|
  | [Company if any] | [Ticker] | [Grade] | [Weight] | [Value] | [Issue Type] |
  
  > **Note**: With current demo data, all ESG Leaders holdings are typically above BBB minimum. If no breaches are found, the agent will confirm compliance: "All holdings in SAM ESG Leaders Global Equity meet the minimum BBB threshold."

- **Compliance Summary**: Portfolio meets ESG grade requirements
- **Monitoring Items**: Any holdings at BBB (minimum threshold) flagged for monitoring

**Talking Points**:
- **Specific Identification**: AI identifies any holdings below threshold
- **Compliance Confirmation**: Clear statement when portfolio is compliant
- **Monitoring Focus**: Holdings at threshold boundary highlighted

**Key Features Highlighted**: 
- **Threshold Detection**: AI identifies breaches or confirms compliance
- **Proactive Monitoring**: At-threshold holdings flagged for attention

##### Step 3: Policy Remediation Requirements

**Presenter Transition**:
> "I've identified the breaches. Now I need to know exactly what the policy requires for ESG grade breaches—what's the timeline and process?..."

*Reasoning: Policy compliance requires following specific remediation procedures. AI retrieves exact requirements.*

**User Input**: 
```
What does our Sustainable Investment Policy require for ESG grade breaches in ESG-labelled portfolios? What's the remediation timeline and process?
```

**Tools Used**:
- `search_policies` (Cortex Search) - ESG policy requirements

**Expected Response**:
- **ESG Grade Breach Requirements**:
  - 30-day grace period for grade improvement
  - Escalated engagement required
  - Divestment if no improvement within grace period
- **Committee Notification**: ESG Committee within 5 business days
- **Documentation**: Engagement letter, monitoring report required
- **Policy Reference**: Sustainable Investment Policy §2.3

**Talking Points**:
- **Clear Requirements**: Specific timeline and process
- **Governance Integration**: Committee notification requirements
- **Audit Trail**: Documentation requirements specified

**Key Features Highlighted**: 
- **SAM_POLICY_DOCS**: Complete policy requirements
- **Procedure Retrieval**: Exact remediation process

#### Scenario Wrap-up

**Business Impact Summary**:
- **Monitoring Efficiency**: ESG grade review completed in minutes
- **Breach Detection**: Automatic identification of policy violations
- **Compliance Assurance**: Clear remediation procedures

**Technical Differentiators**:
- **Grade Distribution Analysis**: Complete ESG profile
- **Threshold Detection**: Automatic breach identification
- **Policy Integration**: Remediation requirements retrieved automatically

---

### ESG Guardian - Company ESG Response Analysis

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: When ESG controversies are identified, understanding the company's response is critical for engagement and investment decisions. This requires synthesising information from NGO reports, company communications, management commentary, and regulatory filings.  
**Value Proposition**: AI-powered company ESG response analysis that combines multiple sources to assess how companies are addressing ESG concerns.

**Agent**: `esg_guardian`  
**Data Available**: NGO reports, press releases, earnings transcripts, SEC filings

#### Demo Flow

**Scene Setting**: Sarah is preparing an engagement assessment for NVIDIA, which was flagged for a high-severity environmental controversy in the daily scan. She needs to understand what happened and how the company is responding before the engagement meeting.

##### Step 1: Controversy Details
**User Input**: 
```
What ESG controversies have been reported about NVIDIA? Give me the full details from NGO reports.
```

**Tools Used**:
- `search_ngo_reports` (Cortex Search) - Controversy details

**Expected Response**:
- **Controversy**: Environmental governance concerns
- **Source**: Human Rights Monitor (recent date)
- **Details**: 19% emissions increase, regulatory violations
- **Issues Identified**: Inadequate environmental governance, insufficient board oversight
- **Severity**: 🔴 High

**Talking Points**:
- **Detailed Information**: Full controversy context
- **Source Attribution**: NGO report cited
- **Impact Assessment**: Scale of issue documented

**Key Features Highlighted**: 
- **SAM_NGO_REPORTS**: Comprehensive controversy details
- **Natural Language**: AI extracts key facts

##### Step 2: Company Public Response

**Presenter Transition**:
> "I understand the controversy. Now let me see how NVIDIA has responded publicly—what have they announced?..."

*Reasoning: Company response indicates management's approach to the issue. Press releases show official position.*

**User Input**: 
```
How has NVIDIA responded publicly to environmental concerns? Search their press releases for any statements or sustainability announcements.
```

**Tools Used**:
- `search_press_releases` (Cortex Search) - Company announcements

**Expected Response**:
- **Press Release**: "NVIDIA Sustainability Initiatives"
  - Carbon reduction commitments
  - Renewable energy targets
  - Supply chain environmental standards
- **Recent Announcements**: Environmental governance improvements
- **Assessment**: Company has made sustainability statements

**Talking Points**:
- **Official Position**: Company's stated commitments
- **Timeline**: Sequence of sustainability announcements
- **Commitment Assessment**: What they've promised publicly

**Key Features Highlighted**: 
- **SAM_PRESS_RELEASES**: Company communication archive
- **Response Tracking**: Sequence of announcements

##### Step 3: Management Commentary

**Presenter Transition**:
> "Good to see public statements. But what has management said to investors? Earnings calls often reveal more candid assessments..."

*Reasoning: Management commentary in earnings calls often provides more detail and candour than press releases.*

**User Input**: 
```
What has NVIDIA management said about environmental issues or sustainability in their earnings calls?
```

**Tools Used**:
- `search_company_events` (Cortex Search) - Earnings transcripts

**Expected Response**:
- **Recent Earnings Call**:
  - CEO commentary on sustainability
  - Environmental investments mentioned
  - Long-term carbon goals discussed
- **Analyst Q&A**: ESG-related questions addressed
- **Tone Assessment**: Commitment level varies by topic

**Talking Points**:
- **Investor Context**: What management told shareholders
- **Financial Impact**: Investment guidance provided
- **Commitment Level**: Tone and specifics of response

**Key Features Highlighted**: 
- **SAM_COMPANY_EVENTS**: Earnings transcript search
- **Management Assessment**: AI evaluates response quality

##### Step 4: SEC Disclosures

**Presenter Transition**:
> "Press releases and earnings calls are helpful, but what have they formally disclosed to regulators? Let me check their SEC filings..."

*Reasoning: SEC filings contain legally required disclosures. Environmental liabilities and risk factors must be disclosed.*

**User Input**: 
```
What does NVIDIA disclose in their SEC filings about environmental risks and climate factors? Check their 10-K filings.
```

**Tools Used**:
- `search_sec_filings` (Cortex Search) - SEC filing disclosures

**Expected Response**:
- **10-K Risk Factors**:
  - Climate-related risks disclosed
  - Supply chain environmental factors mentioned
  - Regulatory compliance considerations
- **Environmental Disclosures**:
  - Sustainability reporting references
  - Energy consumption metrics
- **Disclosure Assessment**: Standard disclosure level for technology sector

**Talking Points**:
- **Regulatory Disclosure**: Formal SEC statements
- **Risk Factors**: Environmental exposure noted
- **Compliance Context**: Regulatory considerations

**Key Features Highlighted**: 
- **SAM_REAL_SEC_FILINGS**: Actual SEC filing text search
- **Disclosure Analysis**: AI identifies relevant disclosures

##### Step 5: Comprehensive Response Assessment

**Presenter Transition**:
> "I now have the complete picture from four sources. Let me synthesise this into an overall assessment of NVIDIA's ESG response..."

*Reasoning: Effective ESG analysis requires synthesising multiple sources into a cohesive assessment.*

**User Input**: 
```
Based on all sources—NGO reports, press releases, earnings calls, and SEC filings—provide an overall assessment of NVIDIA's response to environmental concerns. Is their response adequate for continued investment?
```

**Tools Used**:
- Synthesis of previous queries

**Expected Response**:
- **Response Assessment**:
  - **Public Communication**: Has made sustainability statements ⚠️
  - **SEC Disclosure**: Standard technology sector disclosure ✅
  - **Management Commentary**: Discusses sustainability initiatives ✅
  - **Controversy Response**: Limited direct response to NGO findings ⚠️
- **Concerns**:
  - 19% emissions increase flagged by NGO
  - Governance gaps identified
  - Direct response to controversy not clearly documented
- **Recommendation**: Initiate engagement before IC review
- **Engagement Focus**: Request emissions reduction plan and governance improvements

**Talking Points**:
- **Multi-Source Synthesis**: Four sources combined
- **Balanced Assessment**: Positives and concerns weighed
- **Actionable Recommendation**: Clear engagement priorities

**Key Features Highlighted**: 
- **Five-Tool Integration**: Complete ESG intelligence synthesis
- **Investment Decision Support**: Recommendation with rationale

#### Scenario Wrap-up

**Business Impact Summary**:
- **Analysis Depth**: Comprehensive multi-source company assessment
- **Time Savings**: Analysis completed in 15 minutes vs half-day
- **Decision Quality**: Evidence-based engagement recommendations

**Technical Differentiators**:
- **Five-Source Integration**: NGO + Press + Earnings + SEC + Synthesis
- **Response Assessment**: AI evaluates company ESG response quality
- **Investment Guidance**: Recommendations with supporting evidence

---

### ESG Guardian - Stewardship & Engagement Review

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: Effective stewardship requires tracking engagement history, monitoring company commitments, and assessing whether engagement is driving change. This requires combining engagement notes with current ESG data.  
**Value Proposition**: AI-powered stewardship review that combines engagement history with current ESG status to assess engagement effectiveness and prepare follow-up actions.

**Agent**: `esg_guardian`  
**Data Available**: 150 engagement notes, ESG grades, NGO reports

#### Demo Flow

**Scene Setting**: Sarah is preparing for the quarterly ESG Committee meeting and needs to report on stewardship activities. She wants to review engagement progress with ALPHABET, which was recently flagged for labour practices concerns, and assess whether prior engagements are driving improvement.

##### Step 1: Engagement History
**User Input**: 
```
What ESG engagements have we had with ALPHABET in the past year? Show me the history of our discussions and any commitments they made.
```

**Tools Used**:
- `search_engagement_notes` (Cortex Search) - Engagement history

**Expected Response**:
- **Engagement History**:
  - **Recent**: Supply chain labour discussion
    - Topic: Worker grievance mechanisms
    - Commitment: Enhanced supplier monitoring
    - Timeline: Quarterly progress updates
  - **Prior Engagement**: ESG governance discussion
    - Topics: Environmental, Social priorities
    - Outcome: Sustainability roadmap shared
- **Total Engagements**: [Number] in past 12 months
- **Open Commitments**: Supply chain improvements pending

**Talking Points**:
- **Complete History**: Full engagement timeline
- **Commitment Tracking**: What company promised
- **Progress Status**: Implementation tracking

**Key Features Highlighted**: 
- **SAM_ENGAGEMENT_NOTES**: Complete engagement history
- **Commitment Extraction**: AI identifies specific promises

##### Step 2: Current ESG Status

**Presenter Transition**:
> "Good engagement history. Now let me check ALPHABET's current ESG status—have our engagements driven any improvement?..."

*Reasoning: Engagement effectiveness is measured by ESG improvement. Current status reveals whether engagement is working.*

**User Input**: 
```
What is ALPHABET's current ESG status? Show me their ESG grade and our portfolio exposure.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Current ESG status

**Expected Response**:
- **ESG Grade**: A (above BBB minimum threshold)
- **Portfolio Exposure**:
  - SAM ESG Leaders: ~$150M
  - SAM Renewable & Climate: ~$160M
  - SAM Sustainable Global Equity: ~$135M
  - Total ESG exposure: ~$445M
- **ESG Trend**: Stable, currently compliant

**Talking Points**:
- **Current Status**: ESG grade and compliance
- **Material Exposure**: Significant position across ESG portfolios
- **Compliance Context**: Above policy minimum

**Key Features Highlighted**: 
- **ESG Analytics**: Complete ESG status
- **Cross-Portfolio View**: Exposure across all ESG funds

##### Step 3: Commitment Verification

**Presenter Transition**:
> "They're at Grade A—compliant with policy. But let me verify if they've met their specific engagement commitments, and check for any new controversies..."

*Reasoning: Stewardship accountability requires verifying specific commitments and checking for setbacks.*

**User Input**: 
```
Has ALPHABET met their engagement commitments? Check for any new controversies that might indicate problems.
```

**Tools Used**:
- `search_engagement_notes` (Cortex Search) - Commitment status
- `search_ngo_reports` (Cortex Search) - Recent controversies

**Expected Response**:
- **Commitment Status**:
  - Enhanced supplier monitoring: 🟡 In progress
  - Quarterly updates: 🟡 First update pending
- **Recent Controversies**:
  - Medium severity: Labour practices flagged by Climate Action Network
  - Issue: Supply chain worker grievance mechanisms
  - Status: Aligns with prior engagement concerns
- **Assessment**: Mixed - company is engaged but new controversy emerged in area of prior discussion

**Talking Points**:
- **Commitment Tracking**: Progress on prior commitments
- **Controversy Check**: New issue in known area of concern
- **Honest Assessment**: Engagement active but challenges remain

**Key Features Highlighted**: 
- **Multi-Source Verification**: Engagement + NGO combined
- **Accountability Tracking**: Promises vs reality

##### Step 4: Stewardship Report

**Presenter Transition**:
> "I have the complete picture—engagement history, current status, and commitment verification. Let me prepare a stewardship report for the ESG Committee..."

*Reasoning: Committee oversight requires formal reporting on stewardship activities and effectiveness.*

**User Input**: 
```
Prepare a stewardship report on ALPHABET for the ESG Committee. Include engagement history, current status, commitment tracking, and recommendations for next steps.
```

**Tools Used**:
- Synthesis of previous queries

**Expected Response**:
- **Stewardship Report: ALPHABET INC. (GOOGL)**
- **ESG Grade**: A (compliant with BBB minimum)
- **Portfolio Exposure**: ~$445M across ESG portfolios
- **Engagement Summary**: [Number] engagements in 12 months
- **Progress Assessment**: 
  - Company engaged on supply chain issues
  - Enhanced monitoring commitments made
- **Concerns**:
  - Medium severity labour controversy emerged
  - Commitments still in implementation phase
- **Effectiveness Rating**: 🟡 Engagement Active, Monitoring Required
- **Recommendations**:
  - Escalate engagement to address new controversy
  - Request accelerated timeline on supply chain commitments
  - Quarterly monitoring with ESG Committee updates
  - Consider IC notification if issues persist

**Talking Points**:
- **Comprehensive Report**: Full stewardship assessment
- **Balanced View**: Progress and concerns documented
- **Clear Recommendations**: Specific next steps

**Key Features Highlighted**: 
- **Stewardship Synthesis**: Complete engagement assessment
- **Committee Ready**: Formal report format

#### Scenario Wrap-up

**Business Impact Summary**:
- **Stewardship Tracking**: Complete engagement history accessible
- **Effectiveness Assessment**: Evidence-based evaluation
- **Committee Preparation**: Formal reports generated automatically

**Technical Differentiators**:
- **Engagement + Analytics Integration**: Notes combined with ESG data
- **Commitment Verification**: Specific promises tracked
- **Multi-Source Assessment**: Comprehensive stewardship evaluation

---

### ESG Guardian - Complete ESG Risk Assessment (Catch-All)

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG officers sometimes need a complete ESG risk assessment with a single request when preparing for urgent ESG Committee meetings or responding to stakeholder inquiries—requiring the AI to autonomously orchestrate all ESG tools.  
**Value Proposition**: The ESG Guardian demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering a committee-ready ESG risk report without step-by-step guidance.

**Agent**: `esg_guardian`  
**Data Available**: 200 NGO reports, portfolio holdings across 10 strategies, Sustainable Investment Policy, 150 engagement records

> **Presenter Note**: This scenario requires freshly generated data. If unexpected companies appear (e.g., non-DEMO_COMPANIES securities), run `python main.py --connection-name [your_connection] --scope data` to regenerate the data with proper company filtering.

#### Demo Flow

**Scene Setting**: Sarah receives an urgent request from the CEO for a complete ESG risk briefing on the ESG Leaders portfolio before a media interview. She has 15 minutes to prepare.

##### Step 1: Complete ESG Risk Assessment (All Tools)

**User Input**: 
```
Conduct a complete ESG risk assessment for SAM ESG Leaders Global Equity including scanning NGO reports for any High or Medium severity controversies affecting our holdings, calculating exact portfolio exposure to flagged companies, verifying against our Sustainable Investment Policy thresholds, checking engagement history with any flagged companies, and providing a prioritised remediation plan with severity-based timelines and ESG Committee recommendations. Generate a formal ESG Committee report using our standard template.
```

**Tools Used**:
- `search_ngo_reports` (Cortex Search) - Scan for ESG controversies by severity
- `quantitative_analyzer` (Cortex Analyst) - Calculate portfolio exposure to affected companies
- `search_policies` (Cortex Search) - Retrieve ESG policy requirements and thresholds
- `search_engagement_notes` (Cortex Search) - Check stewardship activities and commitments
- `search_report_templates` (Cortex Search) - Retrieve ESG Committee report format
- `pdf_generator` (Generic) - Generate formal committee report

**Expected Response**:
- **Controversy Scan**:
  - 🔴 High: NVIDIA (NVDA) - Environmental concerns
  - 🟡 Medium: ALPHABET (GOOGL) - Labour practices
  - 🟡 Medium: RIBBON COMMUNICATIONS (RBBN) - Labour practices
  
- **Exposure Analysis**:
  | Company | Severity | Exposure | ESG Grade |
  |---------|----------|----------|-----------|
  | NVIDIA | High | ~$500M | A |
  | ALPHABET | Medium | ~$450M | A |
  | RIBBON | Medium | ~$480M | AA |
  
- **Policy Verification**:
  - ESG Grade Floor (BBB): ✅ All compliant
  - High Severity Protocol: NVIDIA requires IC review per §3.1
  - Medium Severity: Escalated engagement required per §3.2
  
- **Engagement Status**:
  - NVIDIA: Prior environmental engagement (commitments pending)
  - ALPHABET: Supply chain discussion (monitoring)
  - RIBBON: No recent engagement - outreach required
  
- **Remediation Plan**:
  - Immediate: NVIDIA IC review within 5 business days
  - Near-term: ALPHABET and RIBBON engagement escalation
  - Monitoring: Quarterly ESG Committee updates
  
- **ESG Committee Report**: Template-compliant PDF generated with download link

**Talking Points**:
- **Autonomous Orchestration**: AI independently selects and sequences all six ESG tools
- **Single-Query Capability**: Complete ESG assessment from one comprehensive question
- **Template-Guided Output**: Report follows standardized ESG Committee format
- **PDF Delivery**: Professional branded report ready for distribution

**Key Features Highlighted**: 
- **Six-Tool AI Orchestration**: Agent autonomously determines tool sequence and synthesis
- **Controversy + Holdings Integration**: NGO findings merged with portfolio exposure data
- **Stewardship Context**: Includes engagement history for complete ESG picture
- **Report Template Integration**: Standardized committee report format

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Response**: Complete ESG assessment with formal PDF available in under 5 minutes
- **Stakeholder Ready**: Output suitable for CEO briefing, ESG Committee, or media preparation
- **Comprehensive Coverage**: Combines controversies, exposure, policy, engagement, and formal reporting

**Technical Differentiators**:
- **Six-Tool Integration**: Demonstrates full ESG Guardian capability in single query
- **Policy-Aware Analysis**: AI applies exact ESG policy thresholds to exposure data
- **Template-Compliant Reporting**: Formal PDF follows ESG Committee standards
- **Autonomous Operation**: True AI agent capability for ESG risk management

