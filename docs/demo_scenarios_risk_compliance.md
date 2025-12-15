# SAM Demo - Risk & Compliance Officer Scenarios

Complete demo scenarios for Risk & Compliance Officer role with step-by-step conversations, expected responses, and data flows.

---

## Risk & Compliance Officer

### ESG Guardian - ESG Risk Monitoring & Policy Compliance

#### Business Context Setup

**Persona**: Sofia, ESG & Risk Officer at Snowcrest Asset Management  
**Business Challenge**: ESG officers need proactive monitoring of sustainability risks, policy compliance, and engagement tracking to maintain ESG leadership and avoid reputational damage. Manual monitoring of ESG controversies across hundreds of portfolio companies is time-consuming and risks missing critical issues.  
**Value Proposition**: AI-powered ESG risk monitoring that automatically scans for controversies, tracks engagement history, and ensures policy compliance, enabling proactive risk management and comprehensive ESG governance.

**Agent**: `esg_guardian`  
**Data Available**: 500 NGO reports, 150 engagement notes, 8 policy documents

#### Demo Flow

**Scene Setting**: Sofia has received alerts about potential ESG issues affecting portfolio companies and needs to quickly assess the situation, review engagement history, check policy compliance, and prepare a comprehensive report for the ESG committee.

##### Step 1: Proactive Controversy Scanning
**User Input**: 
```
Scan for any new ESG controversies affecting our portfolio companies in the last 30 days.
```

**Tools Used**:
- `search_ngo_reports` (Cortex Search) - Search "ESG controversies environmental violations labor disputes"
- `quantitative_analyzer` (Cortex Analyst) - Get portfolio exposure to flagged companies

**Expected Response**:
- List of flagged controversies with severity levels (High/Medium/Low)
- Affected portfolio companies and exposure amounts
- Source citations with NGO names and publication dates

**Talking Points**:
- Automated ESG controversy detection across all portfolio holdings
- Risk severity assessment and prioritization for immediate action
- Comprehensive source attribution for credibility and follow-up

**Key Features Highlighted**: 
- Proactive ESG risk monitoring and automatic flagging
- Portfolio exposure analysis for risk quantification
- Multi-source NGO report analysis and synthesis

##### Step 2: Internal Context Retrieval
**User Input**: 
```
For the companies flagged in Step 1, do we have any engagement history with these companies regarding the specific ESG issues identified?
```

**Tools Used**:
- `search_engagement_notes` (Cortex Search) - Search for engagement history with flagged companies on specific ESG issues

**Expected Response**:
- Summary of previous engagement meetings and topics for each flagged company from Step 1
- Key commitments made by management specific to the ESG issues from Step 1
- Follow-up actions and timelines from engagement logs that relate to the Step 1 controversies
- Gap analysis: which flagged companies have no prior engagement history

**Talking Points**:
- **Contextual Engagement Review**: Focuses on the specific companies and issues from Step 1
- **Issue-Specific History**: Reviews engagement records that directly relate to the identified controversies
- **Strategic Gap Identification**: Highlights companies requiring new engagement based on Step 1 findings

**Key Features Highlighted**: 
- **Context-Aware Search**: Engagement search specifically targets Step 1 flagged companies and issues
- **Issue-Specific Intelligence**: Historical context directly relevant to current controversies
- **Strategic Planning Support**: Identifies engagement gaps based on current risk assessment

##### Step 3: Policy Compliance Assessment
**User Input**: 
```
What does our ESG policy say about the specific issues identified in Step 1, and what's our total exposure to each of the flagged companies?
```

**Tools Used**:
- `search_policies` (Cortex Search) - Get "ESG policy environmental violations labor disputes exclusion"
- `quantitative_analyzer` (Cortex Analyst) - Calculate total exposure to flagged companies

**Expected Response**:
- Relevant policy clauses with exact text and section references for each ESG issue type from Step 1
- Current total AUM exposure across all funds for each company flagged in Step 1
- Policy-mandated actions specific to each issue type (review, exclusion, engagement requirements)
- Compliance assessment: which flagged situations require immediate action vs monitoring
- Integration with Step 2 findings: where existing engagement supports policy compliance

**Talking Points**:
- **Issue-Specific Policy Guidance**: Policy assessment directly addresses the controversies from Step 1
- **Comprehensive Exposure Analysis**: Total firm exposure to each specific flagged company
- **Integrated Compliance Framework**: Combines policy requirements with engagement history from Step 2

**Key Features Highlighted**: 
- **Context-Specific Policy Search**: Policy analysis tailored to Step 1 ESG issues
- **Multi-Company Risk Aggregation**: Total exposure analysis for all Step 1 flagged companies
- **Integrated Compliance Assessment**: Policy requirements viewed alongside engagement history

##### Step 4: Committee Reporting
**User Input**: 
```
Draft a comprehensive ESG committee summary covering all the companies and issues we've analyzed in Steps 1-3.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Get exposure calculations for all flagged companies
- `search_ngo_reports` (Cortex Search) - Reference controversy details
- `search_policies` (Cortex Search) - Get escalation procedures

**Expected Response**:
- Executive summary covering all controversies identified in Step 1 with severity prioritization
- Portfolio impact assessment with exposure calculations for each flagged company
- Engagement status review for each company based on Step 2 findings
- Policy compliance analysis for each issue type from Step 3
- Recommended actions with timelines, prioritization, and policy references
- Integration of all previous analysis into comprehensive ESG governance report

**Talking Points**:
- **Complete ESG Governance Report**: Synthesizes all findings from the 3-step analysis process
- **Executive Decision Support**: Provides prioritized action plan based on comprehensive assessment
- **Audit-Ready Documentation**: Creates complete record of ESG risk assessment and response

**Key Features Highlighted**: 
- **Multi-Step Synthesis**: Integrates controversy detection, engagement review, and policy analysis
- **Executive Reporting**: Complete ESG governance report ready for committee decision-making
- **Comprehensive Documentation**: Full audit trail of ESG risk assessment and recommended actions

#### Scenario Wrap-up

**Business Impact Summary**:
- **Risk Mitigation**: Proactive identification and management of ESG controversies
- **Governance Excellence**: Comprehensive ESG committee reporting and decision support
- **Compliance Assurance**: Automated policy compliance checking and guidance
- **Operational Efficiency**: Reduced manual monitoring and reporting time from days to minutes

**Technical Differentiators**:
- **Proactive Monitoring**: AI-powered controversy detection across multiple NGO sources
- **Historical Context**: Comprehensive engagement tracking and commitment monitoring
- **Policy Integration**: Automated compliance checking with policy-based action guidance
- **Executive Reporting**: Multi-source synthesis for comprehensive ESG governance

### Compliance Advisor - Mandate Monitoring & Breach Detection

#### Business Context Setup

**Persona**: Michael, Compliance Officer at Snowcrest Asset Management  
**Business Challenge**: Compliance officers need automated monitoring of investment mandates, breach detection, and policy adherence to ensure regulatory compliance and fiduciary responsibility. Manual compliance monitoring across multiple portfolios is error-prone and time-consuming, risking regulatory violations and client mandate breaches.  
**Value Proposition**: AI-powered compliance monitoring that automatically detects breaches, provides policy guidance, and generates audit-ready documentation, ensuring continuous compliance and reducing regulatory risk.

**Agent**: `compliance_advisor`  
**Data Available**: 8 policy documents, 150 engagement logs, portfolio holdings

#### Demo Flow

**Scene Setting**: Michael is conducting his daily compliance review and needs to check for any mandate breaches, investigate specific concentration limits, plan remediation actions, and prepare documentation for audit purposes.

##### Step 1: Compliance Breach Detection
**User Input**: 
```
Check all portfolios for active compliance breaches as of today.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query all portfolios for positions >7.0% (breach) or >6.5% (warning) from SAM_ANALYST_VIEW

**Expected Response**:
- List of breaches by portfolio and rule type
- Severity assessment (breach vs warning thresholds)
- Affected positions with amounts and percentages

**Talking Points**:
- Automated daily compliance monitoring across all portfolios
- Real-time breach detection with severity assessment
- Comprehensive coverage of all mandate and regulatory requirements

**Key Features Highlighted**: 
- Automated compliance monitoring and breach detection
- Real-time portfolio analysis against mandate requirements
- Risk prioritization with severity assessment

##### Step 2: Rule Documentation
**User Input**: 
```
For the specific breaches identified in Step 1, show me the exact policy clauses and concentration limits that are being violated
```

**Tools Used**:
- `search_policies` (Cortex Search) - Get "concentration risk limits position limits investment policy"

**Expected Response**:
- Exact policy text with section references for each breach type from Step 1
- Specific concentration limits and thresholds that apply to each flagged position
- Applicable portfolios and any exceptions for each breach
- Historical context and rationale for each rule being violated
- Severity assessment: which breaches are hard limits vs warnings

**Talking Points**:
- **Context-Specific Policy Research**: Policy lookup directly addresses the breaches from Step 1
- **Breach-Specific Documentation**: Exact clauses and limits for each identified violation
- **Compliance Severity Assessment**: Understanding which violations require immediate action

**Key Features Highlighted**: 
- **Contextual Policy Search**: Policy research specifically targets Step 1 breach types
- **Violation-Specific Intelligence**: Exact clauses and limits for each identified compliance issue
- **Severity Classification**: Understanding of breach vs warning thresholds for prioritization

##### Step 3: Remediation Planning
**User Input**: 
```
For each breach identified in Steps 1-2, what are our remediation options and what's the priority order for addressing these violations?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Calculate reduction amounts needed to bring positions under 6.5%
- `search_policies` (Cortex Search) - Get "breach remediation procedures timeline requirements"

**Expected Response**:
- Remediation options for each specific breach from Step 1, considering the policy requirements from Step 2
- Calculation of excess exposure amounts above limits for each violation
- Multiple reduction scenarios with market impact considerations for each breach
- Priority ranking based on severity assessment from Step 2 (hard breaches vs warnings)
- Timeline recommendations for compliance restoration with sequencing based on priority
- Resource allocation: which breaches can be addressed simultaneously vs requiring sequential action

**Talking Points**:
- **Comprehensive Remediation Strategy**: Addresses all breaches identified in Steps 1-2 with integrated planning
- **Priority-Based Approach**: Sequences remediation based on severity and policy requirements
- **Resource Optimization**: Efficient remediation plan considering market impact and operational capacity

**Key Features Highlighted**: 
- **Multi-Breach Remediation Planning**: Integrated approach to addressing all compliance issues simultaneously
- **Priority-Based Sequencing**: Remediation order based on severity assessment from Step 2
- **Market Impact Optimization**: Remediation plans that minimize trading costs and market disruption

##### Step 4: Audit Trail Documentation
**User Input**: 
```
Generate a comprehensive compliance incident report covering all breaches identified in Steps 1-3 with our complete remediation plan
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Get complete breach details with dates and amounts
- `search_policies` (Cortex Search) - Get audit trail and documentation requirements
- `search_report_templates` (Cortex Search) - Get compliance breach report template

**Expected Response**:
- Formal incident documentation covering all breaches from Step 1 with timeline
- Policy references and breach calculations for each violation identified in Step 2
- Complete remediation plan from Step 3 with milestones, priorities, and responsibilities
- Executive summary of compliance status and remediation strategy
- Regulatory documentation ready for audit review
- Integration of all analysis from Steps 1-3 into comprehensive compliance record

**Talking Points**:
- **Comprehensive Compliance Documentation**: Complete audit trail covering all breaches and remediation plans
- **Regulatory-Ready Reporting**: Full documentation meeting all audit and regulatory requirements
- **Integrated Compliance Management**: Single report covering detection, analysis, and remediation strategy

**Key Features Highlighted**: 
- **Multi-Step Documentation Synthesis**: Integrates breach detection, policy analysis, and remediation planning
- **Regulatory Compliance Reporting**: Audit-ready documentation with complete compliance workflow
- **Comprehensive Audit Trail**: Full record of compliance assessment and response for regulatory review

#### Scenario Wrap-up

**Business Impact Summary**:
- **Regulatory Compliance**: Automated monitoring ensures continuous compliance with all mandates
- **Risk Reduction**: Proactive breach detection prevents regulatory violations and client issues
- **Operational Efficiency**: Reduced manual compliance monitoring time by 80%
- **Audit Readiness**: Comprehensive documentation and audit trails for regulatory reviews

**Technical Differentiators**:
- **Real-time Monitoring**: Continuous compliance assessment across all portfolios and mandates
- **Policy Intelligence**: AI-powered policy search and interpretation with exact clause retrieval
- **Impact Analysis**: Sophisticated remediation planning with market impact considerations
- **Audit Documentation**: Automated generation of regulatory-ready compliance reports

