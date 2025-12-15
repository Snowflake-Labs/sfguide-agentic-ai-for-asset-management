# SAM Demo - ESG Officer Scenarios

Complete demo scenarios for ESG Officer role with step-by-step conversations, expected responses, and data flows.

---

## ESG Guardian

### ESG Guardian - Comprehensive ESG Risk Review

#### Business Context Setup

**Persona**: Sarah, ESG Officer at Snowcrest Asset Management  
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
- `search_policy_docs` (Cortex Search) - Retrieve ESG policy requirements and thresholds
- `search_engagement_notes` (Cortex Search) - Check stewardship activities and commitments

**Expected Response**:
- **ESG Controversy Scan** (NGO Reports - Last 30 days):
  
  * **🔴 High Severity Controversies** (3 companies):
    
    1. **Company: TechCorp Inc. (Ticker: TECH)**
       - **Controversy**: Environmental violation - Chemical waste spill affecting water supply
       - **Source**: Greenpeace Report "Industrial Pollution in Southeast Asia" (15 Jan 2025)
       - **Details**: 12,000-liter chemical spill from manufacturing facility in Malaysia, contaminating local water sources affecting 50,000 residents. Company response delayed 48 hours.
       - **Impact Assessment**: Regulatory fines £8M, cleanup costs £15M, reputational damage significant
       - **ESG Grade Impact**: Downgraded from BBB to B (below investment-grade equivalent)
    
    2. **Company: GlobalRetail Corp. (Ticker: GRET)**
       - **Controversy**: Social - Labor rights violations in supply chain
       - **Source**: Human Rights Watch "Supply Chain Labor Practices Review" (18 Jan 2025)
       - **Details**: Third-party audit revealed unsafe working conditions and excessive overtime (80+ hours/week) at 3 key supplier facilities in Bangladesh. Child labor allegations under investigation.
       - **Impact Assessment**: Potential supply chain disruption, brand reputation risk, regulatory scrutiny
       - **ESG Grade Impact**: Remains A but under review for potential downgrade
    
    3. **Company: Energy Solutions plc (Ticker: ESOL)**
       - **Controversy**: Governance - Board misconduct and executive compensation issues
       - **Source**: MSCI ESG "Governance Controversy Alert" (22 Jan 2025)
       - **Details**: CEO received £12M compensation despite 15% decline in shareholder value. Board independence concerns with 3 of 7 directors having personal financial ties to CEO.
       - **Impact Assessment**: Shareholder activism likely, potential board changes, governance rating decline
       - **ESG Grade Impact**: Downgraded from AA to BBB (at minimum threshold)
  
  * **🟡 Medium Severity Controversies** (2 companies):
    
    4. **Company: BioPharmaceuticals Inc. (Ticker: BPHR)**
       - **Controversy**: Social - Drug pricing controversy
       - **Source**: Oxfam "Pharmaceutical Access Report" (20 Jan 2025)
       - **Details**: 300% price increase on life-saving medication limiting access in developing markets. Public backlash and regulatory review initiated.
       - **Impact Assessment**: Regulatory risk, pricing pressure, reputational concerns
       - **ESG Grade Impact**: Remains A, monitoring for potential downgrade
    
    5. **Company: IndustrialMetal Co. (Ticker: IMCO)**
       - **Controversy**: Environmental - Emissions reporting discrepancy
       - **Source**: CDP "Carbon Disclosure Audit" (12 Jan 2025)
       - **Details**: Third-party verification found Scope 1 emissions 18% higher than company-reported figures. Disclosure quality concerns.
       - **Impact Assessment**: Credibility impact, potential regulatory scrutiny
       - **ESG Grade Impact**: Remains BBB, under monitoring
  
- **Portfolio Exposure Analysis** (SAM ESG Leaders Global Equity):
  
  | Company | Ticker | Severity | Exposure (£M) | Portfolio % | Position Rank | ESG Grade Status |
  |---------|--------|----------|---------------|-------------|---------------|------------------|
  | TechCorp | TECH | 🔴 High | £8.1 | 1.02% | #37 | B (↓ from BBB) 🚨 |
  | GlobalRetail | GRET | 🔴 High | £6.3 | 0.79% | #52 | A (under review) |
  | Energy Solutions | ESOL | 🔴 High | £4.7 | 0.59% | #68 | BBB (↓ from AA) ⚠️ |
  | BioPharmaceuticals | BPHR | 🟡 Medium | £12.4 | 1.56% | #22 | A (monitoring) |
  | IndustrialMetal | IMCO | 🟡 Medium | £5.8 | 0.73% | #55 | BBB (monitoring) |
  
  * **Total Controversy Exposure**: £37.3M (4.69% of portfolio, 1.49% of firm AUM)
  * **High Severity Exposure**: £19.1M (2.40% of portfolio)
  * **Medium Severity Exposure**: £18.2M (2.29% of portfolio)
  * **ESG Grade Breaches**: 1 company (TechCorp at grade B, below BBB minimum)
  
- **Policy Compliance Verification** (Sustainable Investment Policy):
  
  * **Retrieved Policy Requirements** (§2.3 - ESG Grade Floor, §3.2 - Controversy Tolerance):
    - **Minimum ESG Grade**: BBB (Investment Grade equivalent) for all holdings in ESG-labelled portfolios
    - **High Severity Controversy Tolerance**: 0% of portfolio (zero tolerance policy)
    - **Medium Severity Controversy Tolerance**: <2.0% of portfolio (monitoring threshold)
    - **Grade Breach Remediation**: 30-day grace period for ESG grade improvement, divest if not resolved
    - **High Severity Response**: Investment Committee review within 5 business days, divestment consideration required
    - **Medium Severity Response**: Escalated engagement within 30 days, quarterly monitoring
  
  * **Compliance Status**:
    | Requirement | Policy Threshold | Current Status | Compliance |
    |-------------|-----------------|----------------|------------|
    | ESG Grade ≥BBB | 100% of holdings | 98.98% (TechCorp breach) | 🚨 1 BREACH |
    | High Severity Controversies | 0% tolerance | 2.40% exposure | 🚨 3 BREACHES |
    | Medium Severity Controversies | <2.0% threshold | 2.29% | 🟡 SLIGHTLY OVER |
  
  * **Breach Summary**:
    - **Critical Breach**: TechCorp ESG grade B (below BBB minimum)—violates §2.3
    - **Policy Violation**: 2.40% High severity controversy exposure (3 companies)—violates §3.2 zero tolerance
    - **Monitoring Threshold**: 2.29% Medium severity exposure (slightly above 2.0% threshold)
  
- **Engagement History Review**:
  
  * **TechCorp Inc. (TECH)**:
    - **Last Engagement**: 18 Dec 2024 - Environmental management systems discussion
    - **Status**: No engagement on current controversy (spill occurred 15 Jan 2025)
    - **Recommendation**: Immediate engagement required per policy
  
  * **GlobalRetail Corp. (GRET)**:
    - **Last Engagement**: 22 Nov 2024 - Supply chain audit commitments
    - **Commitment**: Third-party labor audits quarterly, remediation plan by Q1 2025
    - **Status**: Current controversy reveals audit finding issues—engagement commitments insufficient
    - **Recommendation**: Escalate to senior management, request remediation plan with timeline
  
  * **Energy Solutions plc (ESOL)**:
    - **Last Engagement**: No prior engagement records
    - **Status**: Governance issue newly identified
    - **Recommendation**: Initiate governance engagement, request board independence improvement plan
  
  * **BioPharmaceuticals Inc. (BPHR)**:
    - **Last Engagement**: 10 Jan 2025 - Drug pricing and access policies (pre-controversy)
    - **Status**: Recent engagement on related topic, controversy escalates concern
    - **Recommendation**: Follow-up engagement referencing controversy, request pricing policy review
  
  * **IndustrialMetal Co. (IMCO)**:
    - **Last Engagement**: 5 Oct 2024 - Carbon reduction targets
    - **Commitment**: Improve emissions disclosure transparency
    - **Status**: Current controversy reveals disclosure commitment not met
    - **Recommendation**: Escalate engagement, request corrected emissions data and improved reporting
  
- **Comprehensive Remediation Plan**:
  
  * **IMMEDIATE ACTIONS** (Within 5 Business Days - By 24 Jan 2025):
    
    1. **TechCorp Inc. (TECH)** - 🔴 Critical Priority
       - **Issue**: ESG grade breach (B vs BBB minimum) + High severity environmental controversy
       - **Policy Requirement**: Investment Committee review within 5 business days (§3.2)
       - **Action**: Prepare Investment Committee Memo recommending divestment
       - **Rationale**: Dual breach (grade + high severity), 30-day grace period clock starts but environmental incident suggests sustained downgrade
       - **Timeline**: IC review by 24 Jan, decision by 27 Jan, execution by 31 Jan
       - **Documentation**: IC Memo, divestment authorization, trade confirmation, audit trail
       - **Estimated Divestment**: £8.1M (1.02% position)
    
    2. **GlobalRetail Corp. (GRET)** - 🔴 High Priority
       - **Issue**: High severity social controversy (labor violations)
       - **Policy Requirement**: IC review for High severity controversy
       - **Action**: Emergency engagement + IC review for retention vs divestment decision
       - **Engagement**: Contact CEO/CSO within 48 hours, request immediate remediation plan
       - **Escalation**: If no satisfactory response within 10 business days, recommend divestment
       - **Timeline**: Engagement by 23 Jan, IC decision by 31 Jan, execution by 14 Feb (if divest)
       - **Documentation**: Engagement log, IC Memo, retention decision with enhanced monitoring or divestment
    
    3. **Energy Solutions plc (ESOL)** - 🔴 High Priority
       - **Issue**: High severity governance controversy + ESG grade at minimum (BBB)
       - **Policy Requirement**: IC review, zero tolerance for High severity
       - **Action**: Initiate governance engagement + IC review
       - **Engagement**: Request board independence improvement plan within 30 days
       - **IC Decision**: If board fails to commit to improvements, recommend divestment
       - **Timeline**: Engagement by 24 Jan, IC review by 31 Jan, 30-day monitoring, decision by 28 Feb
       - **Documentation**: Governance engagement letter, IC Memo, 30-day monitoring report
  
  * **NEAR-TERM ACTIONS** (Within 30 Days - By 24 Feb 2025):
    
    4. **BioPharmaceuticals Inc. (BPHR)** - 🟡 Medium Priority
       - **Issue**: Medium severity social controversy (drug pricing)
       - **Policy Requirement**: Escalated engagement per §3.2
       - **Action**: Follow-up engagement on pricing policy and access programs
       - **Engagement**: Reference 10 Jan discussion, request pricing review and access policy improvements
       - **Timeline**: Engagement by 31 Jan, response by 28 Feb, quarterly monitoring
       - **Documentation**: Engagement log, pricing policy response, quarterly ESG committee review
    
    5. **IndustrialMetal Co. (IMCO)** - 🟡 Medium Priority
       - **Issue**: Medium severity environmental controversy (disclosure discrepancy)
       - **Policy Requirement**: Escalated engagement per §3.2
       - **Action**: Escalate carbon disclosure engagement, request corrected data
       - **Engagement**: Reference October commitment, request immediate disclosure correction and independent verification
       - **Timeline**: Engagement by 31 Jan, corrected disclosure by 31 Mar, quarterly monitoring
       - **Documentation**: Engagement escalation letter, updated emissions data, verification report
  
  * **GOVERNANCE & OVERSIGHT**:
    
    - **Investment Committee**:
      * Emergency meeting by 24 Jan 2025 to review High severity controversies
      * Agenda: TechCorp divestment recommendation, GlobalRetail engagement/retention decision, Energy Solutions governance engagement approval
      * Documentation: 3 IC Memos (one per High severity company)
    
    - **ESG Committee**:
      * Monthly ESG Risk Committee meeting (30 Jan 2025)
      * Agenda: Full controversy review, Medium severity engagements, quarterly monitoring plan
      * Documentation: ESG Risk Committee Report with full 5-company analysis
    
    - **Compliance**:
      * Breach notification to Compliance Officer by 23 Jan 2025
      * Policy breach log: 1 ESG grade breach, 3 High severity controversy breaches
      * Audit trail: All engagement letters, IC Memos, divestment authorizations
    
    - **Client Reporting**:
      * For ESG Leaders portfolio clients: Notify of ESG grade breach and High severity controversies (if material ≥1% of portfolio)
      * Timeline: After IC decisions (by 31 Jan), include in Q1 ESG reporting
  
  * **MONITORING & FOLLOW-UP**:
    - **Weekly**: Track TechCorp ESG grade for any improvement (30-day grace period)
    - **Bi-Weekly**: GlobalRetail remediation plan progress, Energy Solutions board response
    - **Monthly**: Medium severity companies (BioPharmaceuticals, IndustrialMetal) engagement progress
    - **Quarterly**: All companies review in ESG Committee, update ESG Risk Register
  
  * **TOTAL ESTIMATED DIVESTITURES** (if no resolution):
    - Immediate: £8.1M (TechCorp - highly likely)
    - Potential: £6.3M (GlobalRetail - dependent on engagement), £4.7M (Energy Solutions - dependent on governance improvement)
    - **Maximum**: £19.1M (2.40% of portfolio)
    - **Timeline**: 31 Jan - 28 Feb 2025
  
- **ESG Risk Committee Summary**:
  
  * **Portfolio**: SAM ESG Leaders Global Equity
  * **Review Period**: Last 30 days (15 Dec 2024 - 15 Jan 2025)
  * **Controversies Identified**: 5 companies (3 High severity, 2 Medium severity)
  * **Total Exposure**: £37.3M (4.69% of portfolio)
  * **Policy Breaches**: 4 breaches (1 ESG grade, 3 High severity controversies)
  * **Immediate Actions Required**: 3 companies (TechCorp, GlobalRetail, Energy Solutions)
  * **Investment Committee Review**: Emergency meeting required by 24 Jan 2025
  * **Estimated Divestitures**: £8.1M confirmed (TechCorp), £11.0M potential (GlobalRetail, Energy Solutions)
  * **Compliance Status**: ⚠️ **MULTIPLE BREACHES** - Immediate remediation required
  * **Recommendation**: **APPROVE** comprehensive remediation plan with IC emergency meeting, engagement escalations, and quarterly monitoring

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

#### Scenario Wrap-up

**Business Impact Summary**:
- **Risk Detection Speed**: Comprehensive ESG risk review reduced from 2-3 days to under 10 minutes (99% time savings)
- **Coverage Completeness**: Systematic scan of 200 NGO reports vs manual review of 5-10 key sources
- **Decision Quality**: Policy-integrated analysis with engagement context enables confident, compliant remediation decisions
- **Governance Efficiency**: Audit-ready documentation and committee materials generated automatically

**Technical Differentiators**:
- **Multi-Source ESG Intelligence**: Integration of NGO reports, portfolio analytics, policy documents, and engagement records in unified analysis
- **Severity-Based Orchestration**: AI automatically prioritizes controversies by severity and applies differentiated response protocols
- **Policy-Aware AI**: Sustainable Investment Policy thresholds automatically retrieved and applied to controversy exposure calculations
- **Stewardship Integration**: Engagement history tracking provides critical context unavailable in traditional ESG monitoring systems
- **Governance Workflow Automation**: Complete remediation plans with specific timelines, committee requirements, and documentation needs
- **Real-Time Controversy Detection**: NGO report indexing within 48 hours enables rapid response to emerging ESG risks


