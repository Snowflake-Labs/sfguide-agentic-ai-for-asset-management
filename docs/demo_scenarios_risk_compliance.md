# SAM Demo - Risk & Compliance Scenarios

**Scenario**: `risk_compliance`
**Agent**: `AM_risk_compliance`
**Demo Surfaces**: Snowflake Intelligence

Complete demo scenarios covering mandate compliance monitoring, breach remediation, ESG risk assessment, and stewardship.

---

## Part 1: Compliance Monitoring

## Risk & Compliance

### Risk & Compliance - Daily Concentration Limit Monitoring

#### Business Context Setup

**Persona**: James Chen, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Compliance officers need to perform daily concentration limit checks across all portfolios—the most frequent compliance task. Traditional monitoring requires reviewing multiple reports, manually comparing positions to policy thresholds, and documenting findings.  
**Value Proposition**: AI-powered daily concentration monitoring that quickly scans all portfolios, flags positions above thresholds, and produces concise compliance summaries in minutes.

**Agent**: `risk_compliance`  
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
- **SAM_PORTFOLIO_VIEW**: Complete portfolio coverage for compliance monitoring
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
- `search_internal_docs` (Cortex Search) - Retrieve concentration policy thresholds

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

### Risk & Compliance - Policy Requirements Lookup

#### Business Context Setup

**Persona**: James Chen, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Compliance teams frequently receive questions about policy requirements from portfolio managers, auditors, and new team members. Finding specific policy details traditionally requires searching through multiple documents.  
**Value Proposition**: AI-powered policy Q&A that quickly retrieves specific policy requirements, thresholds, and procedures from the complete policy library.

**Agent**: `risk_compliance`  
**Data Available**: 20+ policy documents including Concentration Risk Policy, Sustainable Investment Policy, Investment Mandates

#### Demo Flow

**Scene Setting**: A new portfolio manager asks James about ESG requirements for ESG-labelled portfolios. James uses the Risk & Compliance agent to quickly retrieve accurate policy information.

##### Step 1: ESG Requirements Query
**User Input**: 
```
What are the ESG requirements for ESG-labelled portfolios? What grades are required and what are the exclusion criteria?
```

**Tools Used**:
- `search_internal_docs` (Cortex Search) - ESG policy requirements

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
- `search_internal_docs` (Cortex Search) - Breach procedures

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

### Risk & Compliance - Breach Remediation Tracking

#### Business Context Setup

**Persona**: James Chen, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Tracking breach remediation requires monitoring the complete lifecycle from alert to resolution—retrieving breach history with resolution status, finding portfolio manager commitments from engagement discussions, comparing current positions against committed targets, and preparing formal accountability reports for the Risk Committee. This information spans compliance alerts, engagement notes, and current portfolio data.  
**Value Proposition**: AI-powered remediation tracking that combines breach history, PM engagement commitments, and current portfolio status to monitor compliance recovery progress and prepare professional Risk Committee reports.

**Agent**: `risk_compliance`  
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
- **SAM_PORTFOLIO_VIEW**: Comprehensive breach history with resolution status
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
- `search_internal_docs` (Cortex Search) - Search for compliance discussion engagement notes

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
- `quantitative_analyzer` (Cortex Analyst) - Query current portfolio weights from SAM_PORTFOLIO_VIEW

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
- **SAM_PORTFOLIO_VIEW**: Real-time position weights for comparison
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
- `search_internal_docs` (Cortex Search) - Retrieve Risk Committee Compliance Report template
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

- **PDF Generation**: Professional branded PDF with SAM logo
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

### Risk & Compliance - Regulatory Requirements Lookup

#### Business Context Setup

**Persona**: James Chen, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Compliance officers frequently need to reference specific regulatory text when responding to regulator queries, preparing for audits, or advising portfolio managers on regulatory obligations. Finding exact regulatory requirements across EU, UK, and US frameworks traditionally requires maintaining separate regulatory libraries and legal counsel consultations.  
**Value Proposition**: AI-powered regulatory lookup that searches across 14 regulatory frameworks (MiFID II, UCITS, AIFMD II, SFDR, EU Taxonomy, DORA, EMIR III, FCA Consumer Duty, FCA SDR, SEC Advisers Act, SEC Marketing Rule, SEC Private Fund Rules, IFRS 9, IFRS 7) to retrieve specific regulatory requirements instantly.

**Agent**: `risk_compliance`  
**Data Available**: 14 regulatory documents covering EU, UK, US, and International frameworks

#### Demo Flow

**Scene Setting**: James receives a query from the FCA about SAM's MiFID II suitability assessment procedures. He needs to reference the exact regulatory requirements to ensure SAM's procedures align with the regulation, then cross-reference with SAM's internal policies.

##### Step 1: Regulatory Text Retrieval
**User Input**: 
```
What does MiFID II require for suitability assessments when providing investment advice to professional clients? Give me the specific regulatory requirements.
```

**Tools Used**:
- `search_regulations` (Cortex Search) - Search MiFID II regulation text, filtered by REGULATION_ID = eu_mifid_ii

**Expected Response**:
- **MiFID II Suitability Requirements**:
  - Article 25: Obligations on firms providing investment advice
  - Knowledge and competence requirements
  - Client classification considerations (professional vs retail)
  - Suitability report requirements
  - Record-keeping obligations
- **Regulation Reference**: Directive 2014/65/EU
- **Jurisdiction**: EU

**Talking Points**:
- **Instant Regulatory Access**: Specific regulation text retrieved in seconds
- **Source Attribution**: Official regulation reference and jurisdiction included
- **Audit Support**: Provides authoritative basis for FCA response

**Key Features Highlighted**: 
- **SAM_REGULATORY_DOCS**: 14 regulatory frameworks searchable by AI
- **REGULATION_ID Filtering**: Targeted search within specific regulations

##### Step 2: Internal Policy Cross-Reference

**Presenter Transition**:
> "Good, I have the MiFID II requirements. Now let me check how our internal suitability procedures compare to ensure full alignment..."

*Reasoning: Regulatory compliance requires demonstrating that internal policies meet or exceed regulatory requirements. Cross-referencing shows alignment.*

**User Input**: 
```
Now compare these MiFID II suitability requirements with our internal investment policy. Are our procedures compliant with the regulatory requirements?
```

**Tools Used**:
- `search_internal_docs` (Cortex Search) - Retrieve internal suitability procedures from SAM policy docs

**Expected Response**:
- **Internal Procedures vs Regulation**:
  - SAM suitability assessment process mapped against MiFID II requirements
  - Areas of compliance confirmed
  - Any gaps or areas requiring enhancement
- **Policy Reference**: Investment Policy sections on client suitability
- **Compliance Assessment**: Overall alignment status

**Talking Points**:
- **Gap Analysis**: AI compares internal procedures against regulation
- **Compliance Mapping**: Clear alignment between policy and regulation
- **Proactive Remediation**: Any gaps identified early

**Key Features Highlighted**: 
- **Multi-Source Comparison**: Regulation text + internal policy combined
- **Compliance Gap Detection**: AI identifies potential alignment issues

##### Step 3: Cross-Jurisdiction Comparison

**Presenter Transition**:
> "The FCA also wants to understand how our approach handles both EU and UK requirements since we operate across jurisdictions..."

*Reasoning: Firms operating across jurisdictions need to ensure compliance with multiple regulatory frameworks. Cross-jurisdiction comparison highlights differences.*

**User Input**: 
```
Compare MiFID II suitability requirements with FCA Consumer Duty obligations. What additional requirements does the UK framework impose beyond MiFID II?
```

**Tools Used**:
- `search_regulations` (Cortex Search) - Search both MiFID II and FCA Consumer Duty, using JURISDICTION filter

**Expected Response**:
- **Cross-Jurisdiction Comparison**:
  - MiFID II suitability requirements (EU framework)
  - FCA Consumer Duty additional obligations (UK framework)
  - Key differences and additional UK requirements
  - Areas where FCA Consumer Duty exceeds MiFID II
- **Practical Implications**: What SAM needs to do to comply with both

**Talking Points**:
- **Multi-Jurisdiction Intelligence**: AI compares regulations across EU and UK
- **Incremental Requirements**: Identifies where UK adds to EU baseline
- **Practical Guidance**: Clear implications for compliance procedures

**Key Features Highlighted**: 
- **JURISDICTION Filtering**: Search regulations by EU, UK, US
- **Cross-Regulation Analysis**: AI synthesises requirements across frameworks
- **Operational Relevance**: Practical compliance implications identified

#### Scenario Wrap-up

**Business Impact Summary**:
- **Response Speed**: Regulatory queries answered in minutes vs hours of manual research
- **Coverage**: 14 regulatory frameworks available instantly
- **Cross-Jurisdiction**: EU, UK, and US regulations compared seamlessly
- **Audit Readiness**: Authoritative regulatory citations for compliance documentation

**Technical Differentiators**:
- **Regulatory Corpus**: 14 regulatory frameworks indexed and searchable
- **Multi-Jurisdiction Search**: Filter by EU, UK, US, International
- **Policy-Regulation Integration**: Internal policies cross-referenced with regulation text
- **AI-Powered Gap Analysis**: Automatic identification of compliance alignment

---

### Risk & Compliance - Complete Compliance Assessment (Catch-All)

#### Business Context Setup

**Persona**: James, Compliance Officer at Simulated Asset Management  
**Business Challenge**: Compliance officers sometimes need a complete compliance assessment with a single request when preparing for urgent regulatory inquiries or audit requests—requiring the AI to autonomously orchestrate all compliance tools across breach history, current positions, policy requirements, engagement commitments, and formal reporting.  
**Value Proposition**: The Risk & Compliance agent demonstrates complete autonomous orchestration by selecting and sequencing all six tools from a single comprehensive question, delivering an audit-ready compliance report with professional PDF output without step-by-step guidance.

**Agent**: `risk_compliance`  
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
5. Relevant MiFID II and FCA regulatory requirements for concentration risk reporting
6. A formal Risk Committee compliance report using the appropriate template
7. Generate a professional PDF for FCA submission
```

**Tools Used**:
- `compliance_analyzer` (Cortex Analyst) - Query breach history with resolution status from SAM_PORTFOLIO_VIEW
- `quantitative_analyzer` (Cortex Analyst) - Check current portfolio positions against concentration limits
- `search_internal_docs` (Cortex Search) - Retrieve Concentration Risk Policy thresholds and remediation requirements
- `search_internal_docs` (Cortex Search) - Find PM commitments from compliance discussion notes
- `search_regulations` (Cortex Search) - Retrieve MiFID II and FCA regulatory requirements for concentration risk
- `search_internal_docs` (Cortex Search) - Retrieve Risk Committee Compliance Report template
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

- **Regulatory Context**:
  - MiFID II concentration risk requirements for portfolio management
  - FCA expectations for breach notification and remediation timelines
  - Regulatory reporting obligations and documentation standards

- **Formal Report**:
  - Template-guided Risk Committee Compliance Report
  - Executive summary, breach details, remediation status, recommendations
  - Committee actions required section with approval checkboxes

- **PDF Generation**:
  - Professional branded PDF with SAM logo
  - External regulatory formatting for FCA submission
  - Presigned download URL

**Talking Points**:
- **Autonomous Orchestration**: AI independently selects and sequences all seven compliance tools
- **Single-Query Capability**: Complete compliance assessment from one comprehensive question
- **Regulatory Ready**: Professional PDF formatted for FCA submission
- **Template-Guided Output**: Standardized Risk Committee report structure
- **Regulatory Context**: Actual regulation text cited alongside internal policy

**Key Features Highlighted**: 
- **Seven-Tool AI Orchestration**: Agent autonomously determines tool sequence across compliance alerts, holdings, policies, engagement notes, regulations, templates, and PDF generation
- **Breach Lifecycle Integration**: Historical alerts with resolution status combined with current positions
- **Policy + Regulation Integration**: Internal thresholds cross-referenced with regulatory requirements
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
- **Seven-Tool Integration**: Demonstrates full Risk & Compliance capability in single autonomous query
- **Breach Lifecycle Tracking**: From alert history through PM commitment to current status
- **Policy + Regulation Awareness**: AI applies both internal thresholds and regulatory requirements
- **Template-Guided Synthesis**: Report templates ensure governance-appropriate output
- **Autonomous Operation**: True AI agent capability for comprehensive compliance management

---

### Risk & Compliance - Insider Trading Surveillance & Interest Rate Risk

#### Business Context Setup

**Persona**: Sarah, Chief Compliance Officer at Simulated Asset Management  
**Business Challenge**: Monitoring insider trading patterns across portfolio companies for potential compliance risks, and assessing interest rate exposure context for duration mandates.  
**Value Proposition**: Automated surveillance of SEC Form 4 insider filings and treasury yield context for comprehensive compliance monitoring.

**Agent**: `risk_compliance`  
**Data Available**: SEC Form 4 insider transactions + US Treasury yield curve (14 maturities)

#### Demo Flow

##### Step 1: Insider Trading Surveillance
**User Input**: 
```
Are there any unusual insider trading patterns across our portfolio companies that might require compliance attention?
```

**Tools Used**:
- `insider_trading_monitor` (Cortex Analyst) - Query Form 4 data across demo companies

**Expected Response**:
- Large insider sells flagged for attention
- Unusual clustering of insider activity before earnings
- Compliance recommendations for monitoring

##### Step 2: Interest Rate Risk Context
**User Input**: 
```
What does the current yield curve look like? Any implications for our duration mandates?
```

**Tools Used**:
- `treasury_yield_analyzer` (Cortex Analyst) - Current yield curve across maturities

**Expected Response**:
- Current yield curve shape and key rates
- Yield curve inversion status
- Duration risk implications for mandate compliance

**Key Features Highlighted**: 
- Real SEC Form 4 data for insider trading surveillance
- US Treasury yield curve for interest rate risk context
- Compliance-focused analysis with actionable recommendations


---

## Part 2: ESG Risk & Stewardship

## Risk & Compliance

### Risk & Compliance - Comprehensive ESG Risk Review

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG officers need to conduct comprehensive portfolio ESG risk reviews that systematically scan for controversies across NGO reports, calculate precise portfolio exposures to affected companies, validate against policy requirements and thresholds, review engagement history for stewardship context, and synthesize into severity-prioritized remediation plans with specific timelines and committee requirements. Traditional ESG monitoring requires days of manual NGO report review, spreadsheet exposure calculations, policy document cross-referencing, and engagement system searches—often missing the integration between controversy severity, portfolio materiality, policy compliance, and stewardship activities that drives effective ESG risk management.  
**Value Proposition**: AI-powered comprehensive ESG risk intelligence that seamlessly integrates controversy detection from NGO sources, portfolio exposure quantification, policy threshold validation, and engagement history tracking—delivering complete, action-ready ESG risk assessments with severity-based remediation plans in minutes instead of days.

**Agent**: `risk_compliance`  
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
- `search_external_docs` (Cortex Search) - Scan for recent ESG controversies by severity
- `quantitative_analyzer` (Cortex Analyst) - Calculate portfolio exposure to affected companies
- `search_internal_docs` (Cortex Search) - Retrieve ESG policy requirements and thresholds
- `search_internal_docs` (Cortex Search) - Check stewardship activities and commitments

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
- `search_internal_docs` (Cortex Search) - Retrieve ESG Committee report format requirements
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

- **PDF Generation**: Professional branded PDF with SAM logo
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

### Risk & Compliance - Daily ESG Controversy Scanning

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG officers need to perform daily scans for new controversies affecting portfolio holdings—the most frequent ESG monitoring task. Traditional monitoring requires reviewing multiple NGO websites, news sources, and ESG data providers, then manually checking exposure.  
**Value Proposition**: AI-powered daily controversy scanning that quickly identifies new ESG issues, calculates portfolio exposure, and produces concise summaries for the ESG risk log.

**Agent**: `risk_compliance`  
**Data Available**: 200 NGO reports, portfolio holdings across 10 strategies, ESG policy documents

#### Demo Flow

**Scene Setting**: Sarah starts each morning with a quick ESG controversy scan to identify any new issues affecting portfolio companies. She needs to flag any problems and prepare a brief summary for the ESG risk meeting.

##### Step 1: Controversy Scan
**User Input**: 
```
Are there any new ESG controversies affecting our ESG-labelled portfolios? Check recent NGO reports for any High or Medium severity issues.
```

**Tools Used**:
- `search_external_docs` (Cortex Search) - Scan for recent ESG controversies
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
- `search_external_docs` (Cortex Search) - Retrieve detailed controversy report

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
- `search_internal_docs` (Cortex Search) - ESG policy thresholds

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
- `search_internal_docs` (Cortex Search) - IC memo format guidance

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

### Risk & Compliance - ESG Rating Monitor

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG-labelled portfolios have minimum ESG grade requirements (BBB minimum). Monitoring grade compliance requires regular review of ESG scores across all holdings and identification of any grade breaches.  
**Value Proposition**: AI-powered ESG grade monitoring that quickly identifies any holdings below required thresholds and surfaces policy remediation requirements.

**Agent**: `risk_compliance`  
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
- **SAM_PORTFOLIO_VIEW**: Complete ESG data integration
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
- `search_internal_docs` (Cortex Search) - ESG policy requirements

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

### Risk & Compliance - Company ESG Response Analysis

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: When ESG controversies are identified, understanding the company's response is critical for engagement and investment decisions. This requires synthesising information from NGO reports, company communications, management commentary, and regulatory filings.  
**Value Proposition**: AI-powered company ESG response analysis that combines multiple sources to assess how companies are addressing ESG concerns.

**Agent**: `risk_compliance`  
**Data Available**: NGO reports, press releases, earnings transcripts, SEC filings

#### Demo Flow

**Scene Setting**: Sarah is preparing an engagement assessment for NVIDIA, which was flagged for a high-severity environmental controversy in the daily scan. She needs to understand what happened and how the company is responding before the engagement meeting.

##### Step 1: Controversy Details
**User Input**: 
```
What ESG controversies have been reported about NVIDIA? Give me the full details from NGO reports.
```

**Tools Used**:
- `search_external_docs` (Cortex Search) - Controversy details

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
- `search_external_docs` (Cortex Search) - Company announcements

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

### Risk & Compliance - Stewardship & Engagement Review

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: Effective stewardship requires tracking engagement history, monitoring company commitments, and assessing whether engagement is driving change. This requires combining engagement notes with current ESG data.  
**Value Proposition**: AI-powered stewardship review that combines engagement history with current ESG status to assess engagement effectiveness and prepare follow-up actions.

**Agent**: `risk_compliance`  
**Data Available**: 150 engagement notes, ESG grades, NGO reports

#### Demo Flow

**Scene Setting**: Sarah is preparing for the quarterly ESG Committee meeting and needs to report on stewardship activities. She wants to review engagement progress with ALPHABET, which was recently flagged for labour practices concerns, and assess whether prior engagements are driving improvement.

##### Step 1: Engagement History
**User Input**: 
```
What ESG engagements have we had with ALPHABET in the past year? Show me the history of our discussions and any commitments they made.
```

**Tools Used**:
- `search_internal_docs` (Cortex Search) - Engagement history

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
- `search_internal_docs` (Cortex Search) - Commitment status
- `search_external_docs` (Cortex Search) - Recent controversies

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

### Risk & Compliance - SFDR & EU Taxonomy Regulatory Framework Review

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG officers must ensure fund classifications and disclosures comply with evolving regulatory frameworks—particularly SFDR (Article 8/9 classification), EU Taxonomy (environmental eligibility), and FCA SDR (anti-greenwashing rules). Understanding the exact regulatory requirements and how they interact requires referencing multiple regulation texts, a task that traditionally involves legal counsel and days of document review.  
**Value Proposition**: AI-powered regulatory framework analysis that retrieves specific regulation text from SFDR, EU Taxonomy, and FCA SDR to support fund classification decisions, disclosure preparation, and cross-jurisdiction comparison.

**Agent**: `risk_compliance`  
**Data Available**: Regulatory documents covering SFDR, EU Taxonomy, FCA SDR, plus portfolio ESG data and internal policies

#### Demo Flow

**Scene Setting**: Sarah is preparing for an annual SFDR disclosure review. She needs to verify that SAM's ESG-labelled funds meet Article 8 requirements, understand EU Taxonomy alignment criteria for environmental claims, and compare with the new FCA SDR anti-greenwashing rules for the UK market.

##### Step 1: SFDR Article 8 Classification Requirements
**User Input**: 
```
What are the SFDR Article 8 disclosure requirements for our ESG-labelled funds? What must we include in pre-contractual and periodic disclosures?
```

**Tools Used**:
- `search_regulations` (Cortex Search) - Search SFDR regulation text, filtered by REGULATION_ID = eu_sfdr

**Expected Response**:
- **SFDR Article 8 Requirements**:
  - Pre-contractual disclosure obligations (Annex II)
  - Periodic reporting requirements (Annex IV)
  - Principal Adverse Impact (PAI) indicator requirements
  - "Do No Significant Harm" (DNSH) criteria
  - Sustainability risk integration in investment decisions
- **Regulation Reference**: Regulation (EU) 2019/2088
- **Key Articles**: Article 8, Article 6, Article 11

**Talking Points**:
- **Regulatory Precision**: Exact SFDR text retrieved, not interpretation
- **Disclosure Checklist**: Clear requirements for pre-contractual and periodic reporting
- **Compliance Foundation**: Authoritative basis for disclosure preparation

**Key Features Highlighted**: 
- **SAM_REGULATORY_DOCS**: SFDR regulation fully indexed and searchable
- **REGULATION_ID Filtering**: Targeted search within specific regulations

##### Step 2: EU Taxonomy Alignment Assessment

**Presenter Transition**:
> "Good, I have the SFDR requirements. Our Article 8 funds make environmental claims, so I need to understand the EU Taxonomy alignment criteria—what qualifies as a 'sustainable investment' under the Taxonomy..."

*Reasoning: SFDR Article 8 funds that promote environmental characteristics must reference EU Taxonomy criteria for any environmental sustainability claims.*

**User Input**: 
```
What are the EU Taxonomy eligibility criteria? Explain the six environmental objectives and the minimum requirements for an activity to be considered Taxonomy-aligned.
```

**Tools Used**:
- `search_regulations` (Cortex Search) - Search EU Taxonomy regulation, filtered by REGULATION_ID = eu_taxonomy

**Expected Response**:
- **Six Environmental Objectives**:
  1. Climate change mitigation
  2. Climate change adaptation
  3. Sustainable use of water and marine resources
  4. Transition to a circular economy
  5. Pollution prevention and control
  6. Protection of biodiversity and ecosystems
- **Alignment Criteria**:
  - Substantial contribution to at least one objective
  - Do No Significant Harm to other objectives
  - Minimum social safeguards compliance
  - Technical screening criteria met
- **Regulation Reference**: Regulation (EU) 2020/852

**Talking Points**:
- **Framework Clarity**: Six objectives and alignment criteria clearly retrieved
- **ESG Product Design**: Helps structure fund eligibility assessments
- **Regulatory Compliance**: Ensures environmental claims are Taxonomy-grounded

**Key Features Highlighted**: 
- **EU Taxonomy Coverage**: Full regulation text searchable by environmental objective
- **Cross-Regulation Context**: Taxonomy criteria directly relevant to SFDR Article 8/9 classification

##### Step 3: FCA SDR Anti-Greenwashing Comparison

**Presenter Transition**:
> "SAM also operates in the UK market, so I need to understand the FCA's Sustainability Disclosure Requirements and anti-greenwashing rules. How do these compare with SFDR..."

*Reasoning: UK-based firms must comply with both EU SFDR (for EU-distributed funds) and FCA SDR (for UK market). Understanding differences is critical for dual-jurisdiction compliance.*

**User Input**: 
```
What does the FCA SDR anti-greenwashing rule require? How do the UK sustainability labelling requirements compare with SFDR Article 8/9 classification?
```

**Tools Used**:
- `search_regulations` (Cortex Search) - Search FCA SDR regulation, filtered by REGULATION_ID = fca_sdr_anti_greenwashing

**Expected Response**:
- **FCA SDR Requirements**:
  - Anti-greenwashing rule (applies to all FCA-regulated firms)
  - Sustainability labels: Sustainability Focus, Sustainability Improvers, Sustainability Impact, Sustainability Mixed Goals
  - Naming and marketing rules for sustainability terms
  - Consumer-facing disclosure requirements
  - Ongoing reporting obligations
- **Comparison with SFDR**:
  - SFDR Article 8 vs FCA Sustainability Focus/Improvers
  - SFDR Article 9 vs FCA Sustainability Impact
  - Key differences in classification criteria and disclosure depth
- **Regulation Reference**: PS23/16, FCA Sustainability Disclosure Requirements

**Talking Points**:
- **Cross-Jurisdiction Intelligence**: AI compares EU and UK frameworks side-by-side
- **Label Mapping**: Clear comparison of SFDR Article 8/9 vs FCA sustainability labels
- **Dual Compliance**: Supports firms operating across EU and UK markets

**Key Features Highlighted**: 
- **JURISDICTION Filtering**: Search EU and UK regulations independently
- **Cross-Regulation Comparison**: AI synthesises requirements across frameworks

##### Step 4: Portfolio Classification Assessment

**Presenter Transition**:
> "Now I understand both frameworks. Let me check our actual ESG-labelled portfolios to assess which SFDR classification and FCA label would apply based on their ESG characteristics..."

*Reasoning: Regulatory classification must be grounded in actual portfolio characteristics. ESG data validates whether fund labelling is appropriate.*

**User Input**: 
```
Show me the ESG characteristics of our ESG-labelled portfolios (ESG Leaders, Renewable & Climate, Sustainable Global Equity). Based on the SFDR and EU Taxonomy requirements we just reviewed, are they appropriately classified?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query ESG characteristics for ESG-labelled portfolios
- `search_regulations` (Cortex Search) - Cross-reference classification criteria

**Expected Response**:
- **Portfolio ESG Profiles**:
  | Portfolio | Avg ESG Grade | % Above BBB | Exclusion Screening | SFDR Classification | FCA Label |
  |-----------|--------------|-------------|--------------------|--------------------|-----------|
  | SAM ESG Leaders Global Equity | A | 92% | Yes | Article 8 | Sustainability Focus |
  | SAM Renewable & Climate Solutions | AA | 95% | Yes | Article 8/9 | Sustainability Impact |
  | SAM Sustainable Global Equity | A | 90% | Yes | Article 8 | Sustainability Improvers |

- **Classification Assessment**: Whether current labelling aligns with regulatory criteria
- **Recommendations**: Any reclassification or disclosure adjustments needed

**Talking Points**:
- **Data-Driven Classification**: ESG metrics validate regulatory labels
- **Dual Framework Assessment**: Both SFDR and FCA classification evaluated
- **Proactive Compliance**: Identifies any misalignment before regulatory review

**Key Features Highlighted**: 
- **Regulation + Analytics Integration**: Regulatory criteria applied to portfolio data
- **Multi-Framework Assessment**: SFDR and FCA SDR evaluated simultaneously
- **Classification Validation**: AI supports fund labelling decisions with evidence

#### Scenario Wrap-up

**Business Impact Summary**:
- **Regulatory Understanding**: Instant access to SFDR, EU Taxonomy, and FCA SDR requirements
- **Classification Confidence**: Data-backed fund labelling decisions
- **Cross-Jurisdiction Compliance**: EU and UK frameworks compared seamlessly
- **Disclosure Preparation**: Clear checklist of regulatory disclosure requirements

**Technical Differentiators**:
- **Regulatory Corpus Integration**: 14 regulations searchable including ESG-specific frameworks
- **Cross-Jurisdiction Analysis**: EU SFDR vs UK FCA SDR compared in single workflow
- **Portfolio + Regulation Synthesis**: ESG data combined with regulatory criteria for classification
- **Disclosure Readiness**: Actionable checklist for SFDR and FCA SDR compliance

---

### Risk & Compliance - Complete ESG Risk Assessment (Catch-All)

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Simulated Asset Management  
**Business Challenge**: ESG officers sometimes need a complete ESG risk assessment with a single request when preparing for urgent ESG Committee meetings or responding to stakeholder inquiries—requiring the AI to autonomously orchestrate all ESG tools.  
**Value Proposition**: The Risk & Compliance agent demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering a committee-ready ESG risk report without step-by-step guidance.

**Agent**: `risk_compliance`  
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
- `search_external_docs` (Cortex Search) - Scan for ESG controversies by severity
- `quantitative_analyzer` (Cortex Analyst) - Calculate portfolio exposure to affected companies
- `search_internal_docs` (Cortex Search) - Retrieve ESG policy requirements and thresholds
- `search_internal_docs` (Cortex Search) - Check stewardship activities and commitments
- `search_internal_docs` (Cortex Search) - Retrieve ESG Committee report format
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
- **Six-Tool Integration**: Demonstrates full Risk & Compliance capability in single query
- **Policy-Aware Analysis**: AI applies exact ESG policy thresholds to exposure data
- **Template-Compliant Reporting**: Formal PDF follows ESG Committee standards
- **Autonomous Operation**: True AI agent capability for ESG risk management

---

### Risk & Compliance - Country Emissions Analysis

#### Business Context Setup

**Persona**: Rachel, Head of ESG at Simulated Asset Management  
**Business Challenge**: Assessing country-level greenhouse gas emissions for ESG country risk scoring and portfolio carbon footprint analysis by country of incorporation.  
**Value Proposition**: Climate Watch emissions data integrated into ESG analysis workflow for country-level environmental baselines.

**Agent**: `risk_compliance`  
**Data Available**: Climate Watch country-level GHG emissions by sector (190+ countries)

#### Demo Flow

##### Step 1: Country Emissions Analysis
**User Input**: 
```
Compare greenhouse gas emissions between the US, China, and the EU. Which sectors contribute most?
```

**Tools Used**:
- `emissions_analyzer` (Cortex Analyst) - Country emissions by sector

**Expected Response**:
- Total GHG emissions comparison across countries
- Sector breakdown (Energy, Agriculture, Industrial Processes, Waste)
- Trends over time and key contributors

##### Step 2: Portfolio Country Exposure
**User Input**: 
```
Given our portfolio is heavily weighted to US and European companies, what are the country-level emission profiles for our main markets?
```

**Tools Used**:
- `emissions_analyzer` (Cortex Analyst) - Emissions for US, UK, Germany, France
- `quantitative_analyzer` (Cortex Analyst) - Portfolio country exposure

**Expected Response**:
- Country emissions profiles for portfolio-relevant markets
- ESG country risk context for investment decisions
- Recommendations for carbon exposure monitoring

**Key Features Highlighted**: 
- Climate Watch real data from Snowflake Public Data
- Country-level GHG emissions for ESG due diligence
- Integration with portfolio analysis for carbon footprint context

