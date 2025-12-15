# SAM Demo - Compliance Officer Scenarios

Complete demo scenarios for Compliance Officer role with step-by-step conversations, expected responses, and data flows.

---

## Compliance Advisor

### Compliance Advisor - Portfolio Compliance Audit

#### Business Context Setup

**Persona**: James, Compliance Officer at Snowcrest Asset Management  
**Business Challenge**: Compliance officers need to conduct systematic portfolio compliance audits that retrieve all relevant policy requirements and thresholds, check current holdings against multiple compliance dimensions (concentration, issuer limits, sector limits, ESG grades), identify breaches with exact calculations, review engagement history for remediation context, check regulatory updates for new requirements, and synthesize into formal compliance reports with severity-based remediation timelines and audit trail documentation. Traditional compliance monitoring requires days of manual policy review, spreadsheet breach calculations, engagement system searches, regulatory tracking, and report compilation—often missing the integration between policy requirements, portfolio violations, engagement activities, and regulatory changes that drives effective compliance management.  
**Value Proposition**: AI-powered comprehensive compliance intelligence that seamlessly integrates policy retrieval, multi-dimensional breach detection, engagement history tracking, and regulatory update monitoring—delivering complete, audit-ready compliance assessments with prioritized remediation plans in minutes instead of days.

**Agent**: `compliance_advisor`  
**Data Available**: Portfolio holdings across 10 strategies, 20 policy documents (Concentration Risk Policy, Investment Mandates, Risk Framework), 150 engagement records, regulatory guidance updates

#### Demo Flow

**Scene Setting**: James is conducting the monthly compliance audit for the SAM Technology & Infrastructure portfolio ahead of tomorrow's Risk Committee meeting. The committee requires a complete assessment of all mandate compliance dimensions, concentration breach identification with exact thresholds from policy, engagement status for any previous breach discussions, recent regulatory updates affecting technology sector limits, and formal recommendations with remediation timelines. James needs to retrieve current policy limits, check all portfolio positions against multiple compliance criteria, quantify breaches with dollar amounts and percentages, review engagement history, check regulatory developments, and prepare the formal compliance report—all within today to allow time for portfolio management review before the committee meeting.

##### Step 1: Comprehensive Compliance Assessment
**User Input**: 
```
I need a comprehensive compliance review for SAM Technology & Infrastructure portfolio. Can you:
1. Retrieve our Concentration Risk Policy and Investment Mandate to confirm all position limits and requirements
2. Check current portfolio holdings against concentration limits (single position, issuer, sector) 
3. Identify any breaches with exact percentages above thresholds and dollar amounts
4. Review any engagement notes documenting previous concentration discussions with portfolio management
5. Check latest regulatory updates for any new rules affecting technology sector concentration limits
6. Provide a formal compliance report with breach severity, remediation timelines, required committee actions, and audit trail documentation
```

**Tools Used**:
- `search_policy_docs` (Cortex Search) - Retrieve Concentration Risk Policy and mandate requirements
- `quantitative_analyzer` (Cortex Analyst) - Check portfolio holdings against all compliance criteria
- `search_engagement_notes` (Cortex Search) - Review previous breach discussions
- `search_regulatory_docs` (Cortex Search) - Check recent regulatory updates

**Expected Response**:
- **Policy Requirements Retrieved** (Concentration Risk Policy §2.1, Technology & Infrastructure Mandate §4.2):
  
  * **Single Position Limits** (Concentration Risk Policy §2.1.1):
    - **Warning Threshold**: 6.5% of portfolio NAV (monitoring required, no breach)
    - **Breach Threshold**: 7.0% of portfolio NAV (policy violation, immediate action required)
    - **Remediation Timeline**: Within 30 days of breach detection or next rebalance, whichever is sooner
  
  * **Issuer Concentration Limits** (Concentration Risk Policy §2.1.2):
    - **Warning Threshold**: 9.0% aggregate exposure to single issuer across all securities
    - **Breach Threshold**: 10.0% aggregate issuer exposure
    - **Remediation Timeline**: Within 60 days of breach detection
  
  * **Sector Concentration Limits** (Concentration Risk Policy §2.1.3):
    - **Warning Threshold**: 28.0% exposure to single GICS sector
    - **Breach Threshold**: 30.0% sector concentration
    - **Remediation Timeline**: Quarterly rebalancing to reduce concentration
  
  * **Technology Sector Mandate Requirements** (Investment Mandate §4.2):
    - **Technology Sector Range**: 35-45% of portfolio (below 35% or above 45% is breach)
    - **ESG Grade Floor**: No specific requirement for Technology & Infrastructure (non-ESG strategy)
    - **Benchmark Deviation**: Active share 20-40% vs MSCI ACWI Information Technology Index
  
  * **Governance Requirements** (Concentration Risk Policy §5.1):
    - **Committee Notification**: Investment Committee within 5 business days of breach detection
    - **Breach Documentation**: Investment Committee Memo required for all breaches
    - **Remediation Plan**: Must specify exact reduction amounts, timeline, and responsible parties
    - **Quarterly Review**: Risk Committee review of all concentration positions >6.5%
  
- **Portfolio Holdings Compliance Check** (SAM Technology & Infrastructure - As of 31 Jan 2025):
  
  | Compliance Check | Policy Threshold | Current Status | Variance | Assessment |
  |-----------------|------------------|----------------|----------|------------|
  | **Single Position Limits** |
  | Position >7.0% (Breach) | 0 positions | 2 positions | +2 | 🚨 BREACH |
  | Position 6.5-7.0% (Warning) | 0 positions | 1 position | +1 | ⚠️ WARNING |
  | **Issuer Concentration** |
  | Issuer >10.0% (Breach) | 0 issuers | 0 issuers | 0 | ✅ COMPLIANT |
  | Issuer 9.0-10.0% (Warning) | 0 issuers | 0 issuers | 0 | ✅ COMPLIANT |
  | **Sector Concentration** |
  | Sector >30.0% (Breach) | 0 sectors | 0 sectors | 0 | ✅ COMPLIANT |
  | Sector 28-30% (Warning) | 0 sectors | 0 sectors | 0 | ✅ COMPLIANT |
  | **Mandate Compliance** |
  | Technology Sector (35-45%) | Within range | 42.3% | ✅ | ✅ COMPLIANT |
  | Active Share (20-40%) | Within range | 28.7% | ✅ | ✅ COMPLIANT |
  
  * **Compliance Summary**: 
    - Total Checks: 8 compliance dimensions
    - Compliant: 5 dimensions
    - Warnings: 1 dimension (1 position)
    - Breaches: 2 dimensions (2 positions)
    - **Overall Status**: 🚨 **NON-COMPLIANT** (2 breaches require immediate action)
  
- **Identified Breaches** (Detailed Analysis):
  
  * **BREACH 1: Apple Inc. (AAPL)** - 🚨 Critical
    - **Current Weight**: 8.2% of portfolio (£41.2M market value)
    - **Policy Threshold**: 7.0% maximum (Concentration Risk Policy §2.1.1)
    - **Excess Amount**: 1.2% over limit (£6.0M excess exposure)
    - **Breach Duration**: 23 days (breach detected 8 Jan 2025)
    - **Prior Status**: In warning zone (6.5-7.0%) for 3 months before breach
    - **Position Rank**: #1 largest holding
    - **Severity**: **HIGH** - Largest position, breach duration >20 days, no remediation initiated
  
  * **BREACH 2: Microsoft Corp. (MSFT)** - 🚨 High Priority
    - **Current Weight**: 7.4% of portfolio (£37.1M market value)
    - **Policy Threshold**: 7.0% maximum (Concentration Risk Policy §2.1.1)
    - **Excess Amount**: 0.4% over limit (£2.0M excess exposure)
    - **Breach Duration**: 12 days (breach detected 19 Jan 2025)
    - **Prior Status**: Recent appreciation pushed above 7.0% threshold
    - **Position Rank**: #2 largest holding
    - **Severity**: **MEDIUM** - Smaller excess, recent breach, manageable reduction
  
  * **WARNING: NVIDIA Corp. (NVDA)** - ⚠️ Monitor
    - **Current Weight**: 6.8% of portfolio (£34.1M market value)
    - **Warning Threshold**: 6.5% monitoring level (Concentration Risk Policy §2.1.1)
    - **Distance from Breach**: 0.2% below 7.0% breach (£1.0M buffer)
    - **Position Rank**: #3 largest holding
    - **Trend**: Increasing concentration over last 30 days (+0.3%)
    - **Severity**: **LOW** - Monitoring only, no breach, but trending toward breach threshold
    - **Recommendation**: Include in quarterly Risk Committee review, consider trim if approaches 7.0%
  
  * **Total Breach Exposure**: £78.3M (15.6% of portfolio)
  * **Total Excess Over Limit**: £8.0M (combined AAPL £6.0M + MSFT £2.0M)
  
- **Engagement History Review**:
  
  * **Apple Inc. (AAPL) - Concentration Discussions**:
    - **15 Dec 2024**: Meeting with PM - Anna (Senior Portfolio Manager)
      * Topic: Q4 portfolio review, concentration warnings discussed
      * Commitment: "Monitor Apple position through year-end, plan reduction in Q1 if exceeds 7.0%"
      * Status: Position exceeded 7.0% on 8 Jan 2025 (23 days ago) - **commitment not executed**
    - **22 Oct 2024**: Quarterly Risk Committee
      * Topic: Technology sector concentration review
      * Committee Decision: "Apple position at 6.9% acceptable given strong fundamentals, authorize up to 7.5% near-term with rebalance by Q1"
      * Status: Position now 8.2%, exceeds even extended authorization
    - **Engagement Assessment**: Multiple discussions documented, commitments made but not executed, breach duration concerning
  
  * **Microsoft Corp. (MSFT) - No Prior Discussions**:
    - **Search Result**: No engagement notes found for MSFT concentration
    - **Assessment**: Recent breach (12 days), no prior warning discussions
    - **Recommendation**: Immediate PM engagement required
  
  * **NVIDIA Corp. (NVDA) - Recent Discussion**:
    - **28 Jan 2025**: Email exchange with PM - Anna
      * Topic: NVIDIA appreciation pushing toward warning threshold
      * PM Response: "Monitoring NVIDIA closely, strong Q4 earnings support holding but aware of concentration. Will trim if reaches 7.0%"
      * Status: Currently 6.8%, no action required yet but active monitoring confirmed
  
- **Regulatory Update Review** (Last 90 Days):
  
  * **FCA Policy Statement PS24/12** (15 Dec 2024):
    - **Topic**: "Concentration Risk Management in Asset Management"
    - **Effective Date**: 1 April 2025
    - **Key Change**: Enhanced documentation requirements for concentration breaches
    - **Impact**: SAM policies compliant, but breach documentation must include:
      1. Root cause analysis (why breach occurred)
      2. Remediation timeline with specific milestones
      3. Controls to prevent recurrence
      4. Quarterly reporting to Risk Committee
    - **Action Required**: Update breach memo template to include new documentation requirements
  
  * **ESMA Guidelines Update** (8 Jan 2025):
    - **Topic**: "Risk Management and Governance for UCITS"
    - **Effective Date**: 1 July 2025 (consultation period through March)
    - **Key Change**: Enhanced liquidity risk management for concentrated positions
    - **Impact**: Technology sector concentration may face additional liquidity assessment requirements
    - **Action Required**: Monitor consultation, prepare liquidity analysis for concentrated positions
  
  * **No Immediate Regulatory Breaches**: Current policy limits exceed regulatory minimums, enhanced documentation requirement applies to existing processes
  
- **Formal Compliance Report**:
  
  * **PORTFOLIO**: SAM Technology & Infrastructure
  * **REVIEW DATE**: 31 January 2025
  * **REVIEW PERIOD**: Monthly compliance audit (January 2025)
  * **COMPLIANCE STATUS**: 🚨 **NON-COMPLIANT** - 2 position concentration breaches
  
  * **EXECUTIVE SUMMARY**:
    - 2 positions breach concentration limit (7.0%): Apple 8.2%, Microsoft 7.4%
    - Combined excess exposure: £8.0M (1.6% of portfolio)
    - Breach duration: Apple 23 days, Microsoft 12 days
    - Engagement history: Apple breach despite documented PM commitment; Microsoft no prior discussion
    - Regulatory context: New FCA documentation requirements effective 1 April 2025
    - **Immediate Action Required**: Investment Committee notification, breach remediation plan, portfolio manager engagement
  
  * **DETAILED BREACH ANALYSIS**:
    
    **Breach 1: Apple Inc. (AAPL)**
    | Attribute | Value |
    |-----------|-------|
    | Current Weight | 8.2% (£41.2M) |
    | Policy Limit | 7.0% per §2.1.1 |
    | Excess | 1.2% (£6.0M over limit) |
    | Breach Duration | 23 days (detected 8 Jan 2025) |
    | Breach Severity | 🚨 HIGH |
    | Prior Engagement | 15 Dec commitment not executed |
    | Root Cause | Position appreciation + PM execution delay |
    | **Required Reduction** | **£6.0M to reach 7.0%, or £7.5M to reach 6.5% (recommended)** |
    
    **Breach 2: Microsoft Corp. (MSFT)**
    | Attribute | Value |
    |-----------|-------|
    | Current Weight | 7.4% (£37.1M) |
    | Policy Limit | 7.0% per §2.1.1 |
    | Excess | 0.4% (£2.0M over limit) |
    | Breach Duration | 12 days (detected 19 Jan 2025) |
    | Breach Severity | 🟡 MEDIUM |
    | Prior Engagement | None documented |
    | Root Cause | Recent position appreciation |
    | **Required Reduction** | **£2.0M to reach 7.0%, or £4.5M to reach 6.5% (recommended)** |
    
    **Warning: NVIDIA Corp. (NVDA)**
    | Attribute | Value |
    |-----------|-------|
    | Current Weight | 6.8% (£34.1M) |
    | Warning Threshold | 6.5% per §2.1.1 |
    | Buffer to Breach | 0.2% (£1.0M to 7.0% limit) |
    | Trend | Increasing (+0.3% last 30 days) |
    | Monitoring Status | ⚠️ ACTIVE |
    | **Action** | **Quarterly Risk Committee review, consider trim if approaches 7.0%** |
  
  * **REMEDIATION PLAN** (Per Concentration Risk Policy §2.1.1):
    
    **Phase 1: Immediate Actions (Within 5 Business Days - By 7 Feb 2025)**
    1. Investment Committee Notification (by 3 Feb 2025)
       - Formal breach notification per §5.1
       - Distribution: IC Chair, CIO, Risk Committee Chair, CCO
       - Include: This compliance report, breach details, remediation timeline
    
    2. Portfolio Manager Engagement (by 5 Feb 2025)
       - Meeting with Anna (Senior Portfolio Manager)
       - Discuss: Apple commitment execution failure, Microsoft breach, immediate remediation
       - Document: Meeting minutes with specific commitments and timeline
    
    3. Investment Committee Memo Preparation (by 7 Feb 2025)
       - Document: Breach details, root cause analysis, remediation plan, controls
       - Include: New FCA documentation requirements (PS24/12 effective 1 April)
       - Routing: IC review and approval required
    
    **Phase 2: Breach Remediation (Within 30 Days - By 3 Mar 2025)**
    1. Apple Inc. (AAPL) Reduction
       - **Target**: Reduce to 6.5% (£7.5M sale) - below breach and warning thresholds
       - **Method**: Systematic TWAP execution over 5 trading days
       - **Timeline**: Execution 10-14 Feb 2025, settlement T+2
       - **Milestone**: Confirm compliance by 17 Feb 2025
    
    2. Microsoft Corp. (MSFT) Reduction
       - **Target**: Reduce to 6.5% (£4.5M sale) - below breach and warning thresholds
       - **Method**: Systematic TWAP execution over 3 trading days
       - **Timeline**: Execution 10-12 Feb 2025, settlement T+2
       - **Milestone**: Confirm compliance by 14 Feb 2025
    
    3. Documentation & Controls
       - Trade confirmations and compliance verification
       - Update concentration monitoring system with enhanced alerts at 6.0% (earlier warning)
       - Portfolio manager training on breach remediation commitments
    
    **Phase 3: Ongoing Monitoring (Quarterly)**
    1. Risk Committee Review (Next meeting: 28 Feb 2025)
       - Present: Breach remediation results, NVIDIA monitoring status
       - Review: All positions >6.5%, sector concentration trends
       - Document: Committee minutes with oversight decisions
    
    2. Enhanced Monitoring Controls
       - Daily concentration dashboard for positions >6.0%
       - Weekly breach risk report to PM and Compliance Officer
       - Monthly compliance testing with breach drill-down
    
    3. FCA Documentation Compliance (effective 1 April 2025)
       - Implement root cause analysis template
       - Enhanced remediation timeline tracking
       - Quarterly reporting format for Risk Committee
  
  * **REQUIRED COMMITTEE ACTIONS**:
    - **Investment Committee** (Emergency Review - By 7 Feb 2025):
      * Approve remediation plan (£7.5M Apple, £4.5M Microsoft sales)
      * Review PM execution of prior commitments (Apple 15 Dec discussion)
      * Authorize enhanced concentration monitoring controls
    
    - **Risk Committee** (Quarterly Meeting - 28 Feb 2025):
      * Review breach remediation results
      * Oversight of NVIDIA warning position
      * Approve enhanced monitoring framework per FCA PS24/12
  
  * **AUDIT TRAIL DOCUMENTATION**:
    1. Breach Detection: Compliance monitoring system alert (8 Jan - AAPL, 19 Jan - MSFT)
    2. Engagement History: 15 Dec PM commitment, 28 Jan NVDA discussion
    3. Policy References: Concentration Risk Policy §2.1.1, §5.1; Mandate §4.2
    4. Regulatory Context: FCA PS24/12 (15 Dec 2024), ESMA Guidelines (8 Jan 2025)
    5. Committee Notifications: IC notification (by 3 Feb), IC Memo (by 7 Feb)
    6. Remediation Execution: Trade confirmations (10-14 Feb), compliance verification (17 Feb)
    7. Ongoing Oversight: Risk Committee review (28 Feb), quarterly monitoring
  
  * **COMPLIANCE OFFICER CERTIFICATION**:
    - Report Prepared By: James Chen, Compliance Officer
    - Review Date: 31 January 2025
    - Certification: "This compliance report accurately reflects the current compliance status of SAM Technology & Infrastructure portfolio per Concentration Risk Policy and Investment Mandate. Immediate remediation required for 2 position concentration breaches. Enhanced documentation per FCA PS24/12 incorporated."
    - Next Review: 28 February 2025 (Monthly compliance audit + breach remediation verification)

**Talking Points**:
- **Comprehensive Compliance Coverage**: Single query orchestrates 4 tools across policy documents, portfolio holdings, engagement history, and regulatory updates
- **Policy-Integrated Analysis**: All thresholds, timelines, and requirements automatically retrieved from firm policies—no hardcoded assumptions
- **Multi-Dimensional Checks**: Systematic review across single position, issuer, sector limits plus mandate-specific requirements
- **Engagement Context**: Prior discussions and commitments provide critical context for breach assessment and PM accountability
- **Regulatory Currency**: Recent updates (FCA PS24/12, ESMA Guidelines) automatically incorporated into compliance framework
- **Audit-Ready Output**: Complete formal report with breach details, remediation plan, committee actions, and documentation trail

**Key Features Highlighted**: 
- **Policy Intelligence Engine**: Cortex Search retrieves concentration limits, mandate requirements, governance procedures from 20+ policy documents
- **Multi-Dimensional Compliance Checking**: Cortex Analyst systematically checks portfolio against single position, issuer, sector, and mandate criteria
- **Engagement Continuity**: Historical discussions and commitments tracked through engagement notes for accountability and context
- **Regulatory Monitoring**: Recent regulatory updates automatically surfaced and assessed for impact on current compliance framework
- **Audit Trail Automation**: Complete documentation roadmap from breach detection through remediation to committee oversight
- **Breach Quantification**: Precise calculations of excess exposure (£8.0M), required reductions (specific dollar amounts), and timelines (30-day remediation)

#### Scenario Wrap-up

**Business Impact Summary**:
- **Audit Speed**: Comprehensive compliance review reduced from 2-3 days to under 12 minutes (99% time savings)
- **Coverage Completeness**: Systematic multi-dimensional checks (8 compliance criteria) vs manual 2-3 key metric review
- **Decision Quality**: Policy-integrated analysis with engagement context and regulatory currency enables confident remediation decisions
- **Governance Efficiency**: Audit-ready formal report with committee materials and documentation trail generated automatically

**Technical Differentiators**:
- **Policy-Aware AI**: Concentration thresholds, mandate requirements, and governance procedures automatically retrieved from policy documents
- **Multi-Dimensional Compliance Engine**: Systematic checking across position, issuer, sector, and mandate dimensions in single analysis
- **Engagement History Integration**: Prior discussions and commitments provide accountability context unavailable in traditional compliance systems
- **Regulatory Currency**: Recent FCA and ESMA updates automatically incorporated into compliance framework and documentation requirements
- **Breach Quantification Precision**: Exact calculations of excess exposure, required reductions, and timeline compliance down to dollar and day
- **Audit Trail Automation**: Complete documentation sequence from detection through remediation to oversight with regulatory compliance built-in


