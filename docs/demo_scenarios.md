# SAM Demo - Scenario Scripts

Reference: See `docs/implementation_plan.md` for the build order and implementation details referenced by these scenarios.

Complete demo scenarios organized by role and agent, with step-by-step conversations, expected responses, and data flows.

## Demo Scenarios by Role

This documentation is organized by business role, with each role having dedicated scenario documentation:

### [Portfolio Manager Scenarios](demo_scenarios_portfolio_manager.md)
**Agents**: Portfolio Copilot, Thematic Macro Advisor

**Scenarios**:
- **Portfolio Copilot - Portfolio Insights & Benchmarking**: Complete portfolio analysis workflow from holdings review to actionable investment decisions with integrated risk management
- **Portfolio Copilot - Real-Time Event Impact & Second-Order Risk Verification**: Event-driven risk assessment combining direct exposure with multi-hop supply chain dependency analysis
- **Portfolio Copilot - AI-Assisted Mandate Compliance & Security Replacement**: Automated compliance workflow from breach detection to replacement analysis and committee documentation
- **Thematic Macro Advisor - Investment Theme Analysis**: Cross-portfolio thematic positioning with emerging opportunity identification and integrated investment strategy development

**Key Capabilities**: Multi-tool hybrid analysis combining quantitative portfolio data with qualitative research, real-time event impact assessment, mandate compliance automation, and thematic investment strategy development.

---

### [Research Analyst Scenarios](demo_scenarios_research_analyst.md)
**Agent**: Research Copilot

**Scenarios**:
- **Research Copilot - Document Research & Analysis**: Multi-source research synthesis combining financial analysis with broker research, earnings transcripts, and press releases for complete investment thesis development
- **Research Copilot - Earnings Intelligence Extensions**: Automated earnings analysis integrating financial metrics with sentiment analysis and strategic commentary evolution tracking

**Key Capabilities**: Hybrid analytics platform combining Cortex Analyst structured data analysis with Cortex Search document intelligence, comprehensive data integration across financial fundamentals and research documents, intelligent financial analysis with earnings surprises and ratio comparisons.

---

### [Quantitative Analyst Scenarios](demo_scenarios_quant_analyst.md)
**Agent**: Quant Analyst

**Scenarios**:
- **Quant Analyst - Factor Analysis & Performance Attribution**: Systematic factor screening, portfolio impact analysis, factor evolution tracking, and fundamental validation for complete quantitative investment process

**Key Capabilities**: Pre-built factor metrics for instant analysis, 5 years of monthly factor exposure data for time-series analysis, complete 7-factor model (Market, Size, Value, Growth, Momentum, Quality, Volatility), research integration combining quantitative factor models with fundamental validation.

---

### [Client Relations Scenarios](demo_scenarios_client_relations.md)
**Agent**: Sales Advisor

**Scenarios**:
- **Sales Advisor - Client Reporting & Template Formatting**: Automated client report generation combining portfolio analytics with approved templates, investment philosophy, and compliance language for professional relationship-building communications

**Key Capabilities**: Multi-source integration of portfolio data with templates and philosophy, template intelligence for automated formatting and brand consistency, compliance automation ensuring regulatory standards, brand integration weaving investment philosophy into performance narratives.

---

### [Risk & Compliance Officer Scenarios](demo_scenarios_risk_compliance.md)
**Agents**: ESG Guardian, Compliance Advisor

**Scenarios**:
- **ESG Guardian - ESG Risk Monitoring & Policy Compliance**: Proactive controversy scanning with engagement history review and policy compliance assessment for comprehensive ESG governance
- **Compliance Advisor - Mandate Monitoring & Breach Detection**: Automated breach detection with policy documentation, remediation planning, and audit-ready documentation for continuous compliance

**Key Capabilities**: Proactive ESG risk monitoring across multiple NGO sources, comprehensive engagement tracking and commitment monitoring, automated compliance checking with policy-based action guidance, real-time monitoring across all portfolios and mandates, sophisticated remediation planning with market impact considerations.

---

### [Middle Office Operations Scenarios](demo_scenarios_middle_office.md)
**Agent**: Middle Office Copilot

**Scenarios**:
- **Middle Office Copilot - NAV Calculation & Settlement Monitoring**: Real-time operations intelligence across settlement monitoring, reconciliation break investigation, NAV calculation status, and corporate action processing

**Key Capabilities**: Continuous monitoring across all middle office functions (settlement, reconciliation, NAV, corporate actions, cash), automated root cause analysis with specific remediation recommendations, cross-functional integration linking operational issues for comprehensive root cause identification, severity-based prioritization by business impact and regulatory urgency.

---

### [Executive Leadership Scenarios](demo_scenarios_executive.md)
**Agent**: Executive Copilot (Executive Command Center)

**Scenarios**:
- **Executive Copilot - Holistic Business Performance Review**: Real-time firm-wide KPI dashboard with client flow drill-down, strategic document context, and executive summary synthesis for management committee preparation
- **Executive Copilot - Strategic Competitor Analysis & M&A Simulation**: Competitor intelligence gathering from SEC filings, M&A financial modeling with firm-specific assumptions, and executive memo generation for strategic opportunities

**Key Capabilities**: Single pane of glass view across firm-wide KPIs, client analytics, and strategic documents. Real-time competitor intelligence from SEC filings. M&A simulation tool with automatic EPS accretion modeling. Executive memo generation with professional formatting. Connects operational data to strategic priorities for C-suite decision-making.

---

## Using This Documentation

### For Demonstrations
1. Review the persona and business challenge to set context
2. Follow the step-by-step demo flow with exact user inputs
3. Use talking points to emphasize key capabilities
4. Reference scenario wrap-ups for business impact and technical differentiators

### For Development
- Each scenario documents required tools and data sources
- Expected responses provide validation criteria for agent behavior
- Technical differentiators highlight unique Snowflake capabilities
- Tools Used sections map to agent tool configurations

### For Training
- Business context setup provides realistic user scenarios
- Multi-step workflows demonstrate complete business processes
- Scenario wrap-ups emphasize business outcomes and competitive advantages
- Key features highlighted sections focus on demonstrable capabilities
