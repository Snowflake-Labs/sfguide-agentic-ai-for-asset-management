# Agentic AI for Asset Management

## Overview

**Snowcrest Asset Management (SAM)** is a fictional multi-asset investment firm managing £2.5B across 10 strategies (growth, value, ESG, thematic). This comprehensive demo showcases how **Snowflake Intelligence** transforms investment management workflows through AI agents that seamlessly integrate:

- **Structured Data**: 14,000+ real securities, portfolio holdings, factor exposures, ESG scores
- **Unstructured Documents**: 3,400+ broker research reports, earnings transcripts, press releases, policy documents
- **Real-Time Analytics**: Cortex Analyst converts natural language to SQL on semantic views
- **Document Intelligence**: Cortex Search enables RAG-powered document synthesis

### What Makes This Demo Unique

| Capability | Description |
|------------|-------------|
| **100% Real Securities** | All 14,000+ securities are authentic from SEC Filings (OpenFIGI), not synthetic |
| **Multi-Tool Orchestration** | Agents dynamically combine 3-9 tools (Cortex Analyst + Cortex Search) per query |
| **Industry-Standard Model** | Dimension/fact architecture with transaction audit trails and corporate hierarchies |
| **Complete Workflow Coverage** | 9 agents covering front office, middle office, compliance, and executive functions |
| **Template-Based Documents** | 69 curated templates generate realistic research, policies, and client reports |

### Business Context

SAM operates with:
- **10 Investment Strategies**: Technology & Infrastructure, Global Thematic Growth, ESG Leaders, Defensive Value, and more
- **Compliance Framework**: 6.5% concentration warning, 7.0% breach threshold, ESG grade floors
- **Multi-Source Research**: Broker research, earnings transcripts, press releases, NGO reports
- **Regulatory Requirements**: FCA-regulated with quarterly compliance reviews

## Repository Structure

```
sfguide-agentic-ai-for-asset-management/
├── README.md                           # This file
├── scripts/
│   └── setup.sql                       # One-click automated setup (~15-20 min)
├── notebooks/
│   ├── environment.yml                 # Python dependencies
│   └── 0_start_here.ipynb              # Setup notebook (auto-executed via Git)
├── python/                             # am_ai_demo Python modules
│   ├── config.py                       # Configuration settings
│   ├── generate_structured.py          # Data model generation
│   ├── generate_unstructured.py        # Document generation
│   ├── hydration_engine.py             # Template hydration
│   ├── build_ai.py                     # Cortex Search/Analyst builder
│   ├── create_agents.py                # Agent creation
│   ├── create_semantic_views.py        # Semantic view definitions
│   ├── create_cortex_search.py         # Search service definitions
│   └── extract_real_assets.py          # Real asset extraction
├── content_library/                    # 69 document templates
│   ├── security/                       # Broker research, earnings, press releases
│   ├── issuer/                         # NGO reports, engagement notes
│   ├── portfolio/                      # IPS, portfolio reviews
│   ├── global/                         # Policy docs, sales templates
│   └── regulatory/                     # Form ADV, CRS, updates
├── LICENSE
└── LEGAL.md
```

## 9 Cortex Agents

| Agent | Role | Tools | Key Capabilities |
|-------|------|-------|-----------------|
| **Portfolio Copilot** | Portfolio Manager | 14 tools | Holdings analysis, concentration risk, event impact, supply chain exposure, implementation planning, SEC financials |
| **Research Copilot** | Research Analyst | 8 tools | Multi-source research, company analysis, earnings intelligence, investment memos, SEC filings |
| **Thematic Macro Advisor** | Thematic PM | 6 tools | Theme positioning, emerging trends, macro events, strategic allocation optimization |
| **Quant Analyst** | Quantitative Analyst | 5 tools | Factor screening, performance attribution, financial analysis, statistical validation |
| **Sales Advisor** | Client Relations | 6 tools | Client reporting, template formatting, philosophy integration, compliance review |
| **ESG Guardian** | ESG Officer | 9 tools | NGO reports, controversy scanning, engagement tracking, policy review, remediation planning |
| **Compliance Advisor** | Compliance Officer | 6 tools | Mandate monitoring, breach detection, policy lookup, audit documentation |
| **Middle Office Copilot** | Operations Manager | 6 tools | Settlement monitoring, reconciliation breaks, NAV validation, corporate actions, procedures |
| **Executive Command Center** | C-Suite Executive | 9 tools | Firm-wide KPIs, client analytics, competitor intelligence, M&A simulation, strategic docs |

---

## 📚 Demo Scenarios by Audience

> **Important**: Complete demo scenario documentation with step-by-step scripts, talking points, expected responses, and business context is available in the [`docs/`](docs/) folder. Use these to prepare for demos and select the right scenarios for your audience.

### Quick Reference: Which Scenarios for Which Audience?

| Audience | Recommended Scenarios | Agent(s) | Demo Doc |
|----------|----------------------|----------|----------|
| **Portfolio Managers** | Portfolio analysis, event risk, supply chain exposure, mandate compliance | Portfolio Copilot, Thematic Macro Advisor | [Portfolio Manager Scenarios](docs/demo_scenarios_portfolio_manager.md) |
| **Research Analysts** | Multi-source research, earnings analysis, investment memos | Research Copilot | [Research Analyst Scenarios](docs/demo_scenarios_research_analyst.md) |
| **Quant Analysts** | Factor screening, performance attribution, statistical validation | Quant Analyst | [Quant Analyst Scenarios](docs/demo_scenarios_quant_analyst.md) |
| **Client Relations** | Client reporting, RFP responses, onboarding, retention | Sales Advisor | [Client Relations Scenarios](docs/demo_scenarios_client_relations.md) |
| **ESG/Sustainability** | Controversy scanning, engagement tracking, policy compliance | ESG Guardian | [ESG Officer Scenarios](docs/demo_scenarios_esg_officer.md) |
| **Compliance Officers** | Mandate monitoring, breach detection, audit documentation | Compliance Advisor | [Compliance Scenarios](docs/demo_scenarios_compliance_officer.md) |
| **Middle Office/Ops** | Settlement monitoring, reconciliation, NAV, corporate actions | Middle Office Copilot | [Middle Office Scenarios](docs/demo_scenarios_middle_office.md) |
| **C-Suite Executives** | Firm-wide KPIs, competitor intelligence, M&A simulation | Executive Command Center | [Executive Scenarios](docs/demo_scenarios_executive.md) |

### Demo Scenario Index

📄 **[Main Scenario Overview](docs/demo_scenarios.md)** - Start here for a complete overview of all scenarios organized by role.

**Detailed Scenario Documentation:**
- [Portfolio Manager Scenarios](docs/demo_scenarios_portfolio_manager.md) - 5 scenarios including event-driven risk assessment
- [Research Analyst Scenarios](docs/demo_scenarios_research_analyst.md) - 4 scenarios including earnings intelligence
- [Thematic Advisor Scenarios](docs/demo_scenarios_thematic_advisor.md) - AI infrastructure strategy development
- [Quant Analyst Scenarios](docs/demo_scenarios_quant_analyst.md) - Multi-factor screening and validation
- [Client Relations Scenarios](docs/demo_scenarios_client_relations.md) - 6 scenarios including RFP and retention
- [Sales Scenarios](docs/demo_scenarios_sales.md) - Additional Sales Advisor scenarios
- [ESG Officer Scenarios](docs/demo_scenarios_esg_officer.md) - 6 scenarios including daily scanning
- [Compliance Officer Scenarios](docs/demo_scenarios_compliance_officer.md) - 5 scenarios including audit prep
- [Risk & Compliance Scenarios](docs/demo_scenarios_risk_compliance.md) - Combined ESG and Compliance
- [Middle Office Scenarios](docs/demo_scenarios_middle_office.md) - Operations monitoring
- [Executive Scenarios](docs/demo_scenarios_executive.md) - Strategic intelligence and M&A

**Reference Documentation:**
- [Data Model](docs/data_model.md) - Complete data architecture documentation
- [Data Lineage](docs/data_lineage.md) - How data flows through the system
- [Implementation Status](docs/implementation_status.md) - Current feature status

---

## Prerequisites

- Snowflake account with Cortex features enabled
- ACCOUNTADMIN role (for setup)
- Snowflake Intelligence available

### Step 1: Accept Marketplace Terms (One-Time Setup)

Before running the setup script, accept the terms for the Snowflake Public Data dataset:

1. Go to [Snowflake Public Data (Free)](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255)
2. Click **"Get"**
3. Enter your **email** and click **Submit**
4. **Accept the terms and conditions**
5. Click **"Get"** to complete

> ⚠️ This is required only once. The setup script will fail without accepting these terms.

## Getting Started

### Step 2: Run Setup Script

**Copy and paste** [`scripts/setup.sql`](scripts/setup.sql) **into a Snowflake SQL Worksheet and run it!**

This single script automatically:
1. Creates database infrastructure (SAM_DEMO)
2. Connects to Snowflake Public Data (Free) Marketplace dataset
3. Sets up Git integration to this repository
4. Executes Python stored procedures from Git
5. Generates **46 CURATED tables + 5 views** with 14,000+ real securities
6. Creates **15 RAW corpus tables** from 69 document templates
7. Creates **9 MARKET_DATA tables** with real SEC filings and stock prices
8. Creates **16 Cortex Search services** for document intelligence
9. Creates **10 Cortex Analyst semantic views** for structured data
10. Creates **9 Snowflake Intelligence agents** for complete workflow coverage


### Step 3: Access Snowflake Intelligence

Once setup completes:
1. Navigate to **Snowflake Intelligence** in your Snowflake UI
2. Choose an agent (e.g., Portfolio Advisor)
3. Start asking questions!

## Example Prompts by Agent

---

### Portfolio Copilot

> **Persona**: Anna, Senior Portfolio Manager  
> **Challenge**: Portfolio managers need instant access to portfolio analytics, holdings information, research, and risk assessment across multiple systems  
> **Value**: AI-powered portfolio analytics that combines quantitative holdings data with qualitative research insights in seconds

#### Scenario 1: Portfolio Insights & Benchmarking
*Anna is preparing for her weekly portfolio review meeting and needs to quickly assess her Technology & Infrastructure portfolio.*

**Primary - Holdings Analysis**:
```
What are my top 10 holdings by market value in the SAM Technology & Infrastructure portfolio?
```

**Follow-up - Broker Research**:
```
Based on those top holdings you just showed me, what is the latest broker research saying about our three largest positions?
```

**Follow-up - Concentration Risk**:
```
Looking at those top holdings and their research, what's our sector concentration risk in this portfolio, especially for the companies with the largest positions?
```

**Follow-up - Implementation Plan**:
```
Based on our complete analysis, provide me with a specific implementation plan including exact position sizes, timelines, and dollar amounts for the portfolio actions we should take.
```

#### Scenario 2: Real-Time Event Impact & Supply Chain Risk
*Anna receives an external market alert about an earthquake in Taiwan affecting semiconductor production. She needs to understand direct and indirect portfolio exposure.*

**Event Impact - Taiwan Earthquake**:
```
I just received an alert about a major earthquake in Taiwan affecting semiconductor production. Can you verify this event and tell me what sectors are affected?
```

**Event Impact - Direct Exposure**:
```
What is my direct exposure to Taiwan-based semiconductor companies across all portfolios?
```

**Event Impact - Supply Chain**:
```
What is my indirect exposure through supply chain dependencies? Show me which US companies in my portfolio depend on Taiwan semiconductor suppliers.
```

#### Scenario 3: AI-Assisted Mandate Compliance & Security Replacement
*David Chen receives a compliance alert that META has been downgraded to ESG grade CCC due to governance concerns, violating the fund's minimum BBB ESG requirement. He needs to identify a suitable replacement.*

**Mandate Compliance - ESG Breach**:
```
I've received an alert that META has been downgraded to ESG grade CCC. Can you verify this breach for the SAM AI & Digital Innovation portfolio and show me our current exposure?
```

**Mandate Compliance - Replacements**:
```
Based on that breach, what are our pre-screened replacement candidates that meet the mandate requirements and maintain our AI growth focus?
```

**Mandate Compliance - Company Analysis**:
```
Give me a comprehensive analysis of NVDA as a replacement—include financial health, recent analyst views, and earnings guidance
```

**Mandate Compliance - Committee Memo**:
```
Generate an investment committee memo documenting this compliance breach and recommending NVDA as a replacement
```

#### Scenario 4: Comprehensive Company Analysis
*Anna receives an urgent alert that Microsoft has reported earnings that missed analyst expectations. She needs a complete assessment within the hour.*

**Comprehensive Company Analysis** (Multi-Tool):
```
I'm concerned about Microsoft's recent earnings report. Can you analyze their latest financial performance using SEC filings, compare it to what management said in the earnings call, see what external analysts are saying, and show me our current exposure across all portfolios?
```

**Comprehensive Event-Driven Risk Assessment** (9-Tool Orchestration):
```
I just heard about a major earthquake in Taiwan affecting semiconductor production. Can you:
1. Verify this event and identify affected sectors
2. Show my direct exposure to Taiwan-based technology holdings across all portfolios
3. Calculate indirect exposure through supply chain dependencies (especially for companies like Apple, NVIDIA)
4. Check if any positions breach our concentration limits
5. Analyze the financial health of my most exposed companies using SEC data
6. Find what management is saying in recent earnings calls about supply chain resilience
7. See what analysts are recommending about semiconductor exposure
8. Review our firm's policy on geographic concentration and event response
9. Generate an Investment Committee memo documenting this risk assessment with specific portfolio actions and timeline
```

---

### Research Copilot

> **Persona**: David, Research Analyst  
> **Challenge**: Research analysts need to combine quantitative financial analysis with qualitative research synthesis across multiple sources to build comprehensive investment cases  
> **Value**: AI-powered research intelligence that seamlessly combines structured financial analysis with unstructured document insights

#### Scenario 1: Document Research & Analysis
*David is preparing a thematic research report on technology sector opportunities and needs to quickly synthesize insights from multiple document sources.*

**Primary - Multi-Source Research**:
```
What is the latest research saying about AI and cloud computing opportunities in technology companies?
```

**Deep-Dive - Company Analysis**:
```
From those companies mentioned in the AI and cloud research, pick the one with the strongest themes and give me a detailed analysis of their recent performance and strategic positioning
```

**Competitive Intelligence**:
```
How does [the company from previous analysis]'s AI strategy compare to what other technology companies mentioned are doing?
```

#### Scenario 2: Earnings Intelligence
*Sarah is analyzing the latest quarterly earnings for a major technology holding and needs to quickly assess financial performance and sentiment shifts.*

**Earnings Intelligence**:
```
Give me a comprehensive analysis of Microsoft's latest quarterly earnings, including reported financial metrics versus consensus estimates and key management commentary from the earnings call.
```

**Sentiment Analysis**:
```
Compare the sentiment between Microsoft's prepared remarks and the Q&A session. Are there any concerning shifts or defensive language that could indicate management uncertainty?
```

**Strategic Commentary Evolution**:
```
How has Microsoft's commentary on cloud computing and AI strategy evolved over the past three quarters? Are there any shifts in their strategic messaging or capital allocation priorities?
```

**Investment Committee Summary**:
```
Draft a concise investment committee memo summarizing Microsoft's earnings results, highlighting the key financial metrics, sentiment analysis findings, and any strategic shifts that impact our investment thesis.
```

**Investment Thesis Validation**:
```
Based on our analysis of [Step 2 company] and its competitive position, compare what management is saying about AI growth prospects versus what analysts are forecasting for this investment opportunity
```

#### Scenario 3: Investment Memo Generation
*David needs to prepare a comprehensive investment memo for the upcoming investment committee meeting on NVIDIA.*

**Investment Memo Generation**:
```
Generate a comprehensive investment research report for NVIDIA covering financial health, management outlook, analyst views, competitive position, and key risks. Include a Buy/Hold/Sell recommendation.
```

**Competitive Landscape Deep-Dive**:
```
Expand on the competitive landscape section. How does NVIDIA's AI chip market position compare to AMD and Intel? Include market share data if available.
```

**Risk Analysis**:
```
What are the key risks to the investment thesis? For each risk, provide leading indicators we should monitor and potential mitigants.
```

**IC Brief**:
```
Summarise the key points from our analysis into a one-page investment committee brief with clear recommendation and next steps.
```

---

### Thematic Macro Advisor

> **Persona**: Anna, Portfolio Manager (Thematic Focus)  
> **Challenge**: Portfolio managers need to identify and validate investment opportunities across macro trends by combining quantitative portfolio analysis with thematic research  
> **Value**: AI-powered thematic analysis that combines current portfolio positioning with comprehensive research synthesis

#### Scenario: Investment Theme Analysis
*Anna is developing the quarterly thematic investment strategy and needs to assess current positioning against emerging macro trends.*

**Primary - Comprehensive Thematic Strategy**:
```
I'm developing our Q1 2025 thematic investment strategy around artificial intelligence infrastructure. Can you:
1. Analyze our current portfolio exposure to AI and data center themes across all portfolios
2. Find the latest broker research identifying key AI infrastructure sub-themes and investment opportunities
3. Review what major technology company managements are saying in earnings calls about AI spending and data center capacity plans
4. Check recent corporate announcements for AI infrastructure investments and partnerships
5. Synthesize this into a thematic positioning recommendation showing where we're under-positioned relative to the emerging AI infrastructure opportunity
```

**Theme Exposure Analysis**:
```
Analyze our current exposure to AI and technology themes across portfolios
```

**Emerging Opportunities**:
```
Based on our current AI and technology exposure, what are the emerging thematic investment opportunities that could enhance our positioning?
```

**Strategic Positioning Analysis**:
```
From the emerging themes identified, pick the most promising one and analyze how we should position our portfolios, considering our current AI/tech exposure
```

**Integrated Investment Strategy**:
```
Based on our AI/tech positioning and the selected theme, create an integrated investment strategy that optimizes our thematic exposure across portfolios
```

#### Scenario 2: AI Infrastructure Strategy Development (Multi-Tool)
*Anna is preparing the quarterly thematic investment strategy for presentation to the Investment Committee, focusing on artificial intelligence infrastructure.*

**Comprehensive AI Infrastructure Strategy**:
```
I'm developing our upcoming quarterly thematic investment strategy around artificial intelligence infrastructure. Can you:
1. Analyze our current portfolio exposure to AI and data center themes across all portfolios
2. Find the latest broker research identifying key AI infrastructure sub-themes and investment opportunities
3. Review what major technology company managements are saying in earnings calls about AI spending and data center capacity plans
4. Check recent corporate announcements for AI infrastructure investments and partnerships
5. Synthesize this into a thematic positioning recommendation showing where we're under-positioned relative to the emerging AI infrastructure opportunity
```

---

### Quant Analyst

> **Persona**: Dr. James Chen, Quantitative Analyst  
> **Challenge**: Quant analysts need to develop systematic multi-factor strategies with SEC filing validation, analyst research cross-reference, and statistical significance testing  
> **Value**: AI-powered comprehensive quantitative intelligence delivering statistically validated, fundamentally sound investment strategies in minutes

#### Scenario: Multi-Factor Stock Screening Strategy
*Dr. Chen is developing a new multi-factor equity strategy for Q1 2025 focusing on Value, Quality, and improving Momentum characteristics.*

**Primary - Multi-Factor Screening**:
```
I'm building a multi-factor stock screening strategy focusing on Value, Quality, and improving Momentum. Can you:
1. Screen our investment universe for securities with high Quality and Value factor exposures
2. Within those results, identify companies showing improving Momentum factor trends over the last 6 months
3. Validate the financial fundamentals using SEC filing data - confirm revenue growth, margin expansion, and balance sheet quality
4. Cross-reference with analyst research to see if broker recommendations align with our factor signals
5. Check earnings transcripts for management commentary supporting the quality and growth characteristics
6. Provide a ranked list with factor scores, fundamental validation, analyst views, and statistical significance testing (R-squared, p-values) for the systematic investment strategy
```

**Simple Factor Screening**:
```
Screen for stocks with improving momentum and quality factors over the last 6 months.
```

**Factor Comparison**:
```
For the stocks with improving momentum and quality factors, compare their factor loadings against our current Value strategy and Growth strategy portfolios.
```

**Factor Evolution**:
```
Analyze the factor exposure trends of our momentum and quality securities over the last 3 years and show how their factor characteristics have evolved.
```

**Fundamental Validation**:
```
For the securities with the strongest factor evolution trends, what fundamental themes and research support their improving factor characteristics?
```

---

### Sales Advisor

> **Persona**: James Mitchell, Client Relationship Manager  
> **Challenge**: Client relationship managers need to produce professional, compliant client reports integrating performance data with approved messaging templates  
> **Value**: AI-powered client reporting that automatically combines portfolio analytics with approved templates, investment philosophy, and compliance language

#### Scenario: Client Reporting & Template Formatting
*James needs to prepare a monthly client report for a key institutional client, ensuring professional presentation with proper compliance language.*

**Primary - Quarterly Client Presentation**:
```
I need to prepare a quarterly client presentation for our SAM ESG Leaders Global Equity portfolio. Can you:
1. Get Q4 2024 performance data including portfolio returns vs benchmark, top holdings, sector allocation, and ESG metrics
2. Retrieve our quarterly client report template to follow the approved structure and formatting
3. Find our ESG investment philosophy documentation to integrate our differentiated approach and sustainable development beliefs
4. Get the required regulatory disclaimers and risk warnings from compliance policies
5. Generate a professional client-ready quarterly report that combines performance data, investment philosophy, and compliance disclosures in the approved template format
```

**Simple Client Report**:
```
Generate a client report for the SAM Technology & Infrastructure portfolio showing quarterly performance, top holdings, and sector allocation
```

**Template Formatting**:
```
Format this into a professional monthly client report using our approved template structure with proper sections and branding
```

**Philosophy Integration**:
```
Integrate our ESG investment philosophy and technology innovation messaging to align the report with SAM's strategic positioning
```

**Compliance Review**:
```
Complete the compliance review by adding all required regulatory disclosures, risk warnings, and fiduciary language for final client delivery
```

#### Scenario 2: RFP Response Preparation
*James received an RFP from a large pension fund seeking a Global ESG Equity mandate. The response is due in 10 days.*

**Primary - RFP Response**:
```
I need to prepare an RFP response for a Global ESG Equity mandate. Start by gathering our firm capabilities, ESG track record, and available performance history for the SAM ESG Leaders Global Equity strategy.
```

**Investment Process**:
```
Provide our ESG investment process, integration methodology, and active ownership approach for the investment process section of the RFP.
```

**Compliance & Risk**:
```
Gather our compliance framework, risk management policies, and regulatory disclosures for the operational due diligence section of the RFP.
```

**Complete RFP Draft**:
```
Create a complete RFP response draft for the Global ESG Equity mandate combining our track record, investment process, and compliance content in our standard RFP format.
```

#### Scenario 3: Client Onboarding Package
*James just closed a new mandate with Midwest Community Foundation, a foundation client allocating $62 million to SAM ESG Leaders Global Equity.*

**Onboarding Welcome**:
```
I need to prepare an onboarding welcome package for our new client Midwest Community Foundation. They're investing in SAM ESG Leaders Global Equity. Start with their client profile and portfolio overview.
```

**Welcome Structure**:
```
Retrieve our client onboarding welcome template and customize it for Midwest Community Foundation as a foundation client.
```

**Philosophy for New Client**:
```
Include our ESG investment philosophy and sustainable investing approach in the welcome package, emphasizing alignment with foundation values.
```

**Complete Onboarding**:
```
Create the complete onboarding welcome package for Midwest Community Foundation combining their portfolio overview, welcome materials, and ESG philosophy content.
```

#### Scenario 4: At-Risk Client Analysis
*James is reviewing his client book for Q4 planning and wants to identify any relationships showing signs of potential redemption risk.*

**Flow Pattern Analysis**:
```
Analyze client flow patterns to identify any clients showing redemption trends or declining engagement over the past 6 months.
```

**Performance Context**:
```
Show me which portfolios Pacific Coast Pension Fund has invested in historically, including their complete flow history and any remaining positions. Then show the performance of those portfolios.
```

**Retention Strategy**:
```
Retrieve retention strategies and engagement tactics for an at-risk pension fund client concerned about performance.
```

**Retention Action Plan**:
```
Create an action plan for retaining Pacific Coast Pension Fund including talking points, value demonstration, and recommended next steps.
```

#### Scenario 5: Product Cross-Sell Opportunity
*James is preparing for his quarterly business development review and wants to identify cross-sell opportunities across his client book.*

**Single-Product Clients**:
```
Show me clients with single-product relationships who might be good cross-sell opportunities. Include their current SAM product allocation and AUM.
```

**Product Catalog**:
```
Retrieve our SAM product catalog with strategy descriptions, target clients, and suitability criteria for cross-sell analysis.
```

**Client-Product Matching**:
```
For Meridian Capital Partners, who currently holds SAM ESG Leaders, recommend additional SAM products that would complement their portfolio and align with their pension fund objectives.
```

**Cross-Sell Proposal**:
```
Create a cross-sell proposal for Meridian Capital Partners with product recommendations, key messaging, and suggested next steps.
```

#### Scenario 6: Client Segmentation and Prioritisation
*James is planning his Q1 client engagement calendar and wants to prioritise his client outreach based on relationship value and health.*

**Client Book Overview**:
```
Give me an overview of my client book segmented by AUM tier and client type, including total relationship value.
```

**Relationship Health**:
```
Analyze relationship health across my client book based on flow trends over the past 12 months. Identify growing, stable, and declining relationships.
```

**Prioritised Engagement List**:
```
Create a prioritised client engagement list for the upcoming quarter combining AUM value and relationship health, with recommended action for each segment.
```

---

### ESG Guardian

> **Persona**: Sofia, ESG & Risk Officer  
> **Challenge**: ESG officers need proactive monitoring of sustainability risks, policy compliance, and engagement tracking across hundreds of portfolio companies  
> **Value**: AI-powered ESG risk monitoring that automatically scans for controversies, tracks engagement history, and ensures policy compliance

#### Scenario: ESG Risk Monitoring & Policy Compliance
*Sofia has received alerts about potential ESG issues affecting portfolio companies and needs to assess, review engagement history, and prepare a committee report.*

**Primary - Comprehensive ESG Review**:
```
I need a comprehensive ESG risk review for our SAM ESG Leaders Global Equity portfolio. Can you:
1. Scan NGO reports for any recent High or Medium severity ESG controversies affecting our holdings
2. Check our portfolio holdings to calculate exact exposure to companies with these controversies
3. Review our Sustainable Investment Policy to confirm ESG grade requirements and controversy tolerance thresholds
4. Check our engagement history with any flagged companies to see if we've already initiated stewardship activities
5. Provide a complete remediation plan with severity-based timelines, required committee reviews, and documentation requirements
```

**Controversy Scanning**:
```
Scan for any new ESG controversies affecting our portfolio companies in the last 30 days.
```

**Engagement History**:
```
For the companies flagged, do we have any engagement history with these companies regarding the specific ESG issues identified?
```

**Policy Review**:
```
What does our ESG policy say about the specific issues identified, and what's our total exposure to each of the flagged companies?
```

**Committee Summary**:
```
Draft a comprehensive ESG committee summary covering all the companies and issues we've analyzed.
```

#### Scenario 2: Daily ESG Controversy Scanning
*Sarah starts each morning with a quick ESG controversy scan to identify any new issues affecting portfolio companies.*

**Daily Scan**:
```
Are there any new ESG controversies affecting our ESG-labelled portfolios? Check recent NGO reports for any High or Medium severity issues.
```

**Detailed Controversy**:
```
For the NVIDIA high-severity environmental issue, what are the specific details of the controversy and when was it reported? What exactly happened?
```

**Policy Threshold Check**:
```
Check if the NVIDIA high-severity controversy breaches our Sustainable Investment Policy thresholds. What are our requirements for High severity controversies?
```

**IC Escalation Memo**:
```
Given the policy breach identified for NVIDIA's high-severity environmental controversy, prepare an escalation memo for the Investment Committee with the controversy details, portfolio exposure, policy requirements, and recommended actions.
```

#### Scenario 3: ESG Rating Monitor
*Sarah is conducting the weekly ESG grade review for ESG-labelled portfolios to ensure all holdings meet the minimum BBB requirement.*

**Grade Distribution**:
```
Show me the ESG grade distribution for our SAM ESG Leaders Global Equity portfolio. I need to see the breakdown from AAA to CCC.
```

**Grade Breach Identification**:
```
Identify any holdings in the ESG Leaders portfolio that are below the BBB minimum threshold. Show me the specific companies and their ESG grades.
```

**Policy Remediation**:
```
What does our Sustainable Investment Policy require for ESG grade breaches in ESG-labelled portfolios? What's the remediation timeline and process?
```

#### Scenario 4: Company ESG Response Analysis
*Sarah is preparing an engagement assessment for NVIDIA, which was flagged for a high-severity environmental controversy.*

**Full Controversy Details**:
```
What ESG controversies have been reported about NVIDIA? Give me the full details from NGO reports.
```

**Public Response**:
```
How has NVIDIA responded publicly to environmental concerns? Search their press releases for any statements or sustainability announcements.
```

**Management Commentary**:
```
What has NVIDIA management said about environmental issues or sustainability in their earnings calls?
```

**SEC Disclosures**:
```
What does NVIDIA disclose in their SEC filings about environmental risks and climate factors? Check their 10-K filings.
```

**Comprehensive Assessment**:
```
Based on all sources—NGO reports, press releases, earnings calls, and SEC filings—provide an overall assessment of NVIDIA's response to environmental concerns. Is their response adequate for continued investment?
```

#### Scenario 5: Stewardship & Engagement Review
*Sarah is preparing for the quarterly ESG Committee meeting and needs to report on stewardship activities with ALPHABET.*

**Engagement History**:
```
What ESG engagements have we had with ALPHABET in the past year? Show me the history of our discussions and any commitments they made.
```

**Current ESG Status**:
```
What is ALPHABET's current ESG status? Show me their ESG grade and our portfolio exposure.
```

**Commitment Verification**:
```
Has ALPHABET met their engagement commitments? Check for any new controversies that might indicate problems.
```

**Stewardship Report**:
```
Prepare a stewardship report on ALPHABET for the ESG Committee. Include engagement history, current status, commitment tracking, and recommendations for next steps.
```

#### Scenario 6: Complete ESG Risk Assessment (All Tools)
*Sarah receives an urgent request from the CEO for a complete ESG risk briefing on the ESG Leaders portfolio before a media interview.*

**Complete Assessment**:
```
Conduct a complete ESG risk assessment for SAM ESG Leaders Global Equity including scanning NGO reports for any High or Medium severity controversies affecting our holdings, calculating exact portfolio exposure to flagged companies, verifying against our Sustainable Investment Policy thresholds, checking engagement history with any flagged companies, and providing a prioritised remediation plan with severity-based timelines and ESG Committee recommendations. Generate a formal ESG Committee report using our standard template.
```

---

### Compliance Advisor

> **Persona**: Michael, Compliance Officer  
> **Challenge**: Compliance officers need automated monitoring of investment mandates, breach detection, and policy adherence across multiple portfolios  
> **Value**: AI-powered compliance monitoring that automatically detects breaches, provides policy guidance, and generates audit-ready documentation

#### Scenario: Mandate Monitoring & Breach Detection
*Michael is conducting his daily compliance review and needs to check for mandate breaches, investigate limits, and prepare audit documentation.*

**Primary - Comprehensive Compliance Review**:
```
I need a comprehensive compliance review for SAM Technology & Infrastructure portfolio. Can you:
1. Retrieve our Concentration Risk Policy and Investment Mandate to confirm all position limits and requirements
2. Check current portfolio holdings against concentration limits (single position, issuer, sector) 
3. Identify any breaches with exact percentages above thresholds and dollar amounts
4. Review any engagement notes documenting previous concentration discussions with portfolio management
5. Check latest regulatory updates for any new rules affecting technology sector concentration limits
6. Provide a formal compliance report with breach severity, remediation timelines, required committee actions, and audit trail documentation
```

**Breach Detection**:
```
Check all portfolios for active compliance breaches as of today.
```

**Policy Clauses**:
```
For the specific breaches identified, show me the exact policy clauses and concentration limits that are being violated
```

**Remediation Options**:
```
For each breach identified, what are our remediation options and what's the priority order for addressing these violations?
```

**Incident Report**:
```
Generate a comprehensive compliance incident report covering all breaches with our complete remediation plan
```

#### Scenario 2: Daily Concentration Limit Monitoring
*James starts each day with a quick concentration check across all portfolios before the morning risk meeting.*

**Portfolio-Wide Scan**:
```
Run a daily concentration check across all portfolios. Show me any positions above the 6.5% warning threshold, sorted by weight.
```

**Policy Thresholds**:
```
What are the exact concentration thresholds in our Concentration Risk Policy? Confirm warning and breach levels.
```

**Compliance Classification**:
```
Apply these policy thresholds to classify each flagged position as Compliant, Warning, or Breach. Include the exact variance from threshold.
```

**Daily Summary**:
```
Create a brief daily compliance summary I can share with the risk team and file in my compliance log.
```

#### Scenario 3: Policy Requirements Lookup
*A new portfolio manager asks James about ESG requirements for ESG-labelled portfolios.*

**ESG Requirements**:
```
What are the ESG requirements for ESG-labelled portfolios? What grades are required and what are the exclusion criteria?
```

**Breach Procedures**:
```
What happens if we breach a concentration limit? What's the remediation timeline and what committees need to be notified?
```

**Portfolio-Specific Requirements**:
```
Which of our portfolios are ESG-labelled and have these ESG requirements? Show me the list with their specific mandate requirements.
```

#### Scenario 4: Breach Remediation Tracking
*James is preparing for the monthly Risk Committee meeting and needs to report on the status of previously identified concentration breaches.*

**Breach History**:
```
Show me all concentration breaches from the last 30 days. Include which ones have been resolved and which are still active.
```

**PM Commitments**:
```
Search our engagement notes for any compliance discussions or PM commitments regarding Apple and Microsoft concentration breaches.
```

**Position vs Target**:
```
What are the current weights for Apple and Microsoft in the SAM Technology & Infrastructure portfolio? Compare to the committed remediation targets.
```

**Risk Committee Report**:
```
Find the Risk Committee compliance report template and generate a formal PDF report with all our findings on breach status, PM commitments, and remediation recommendations.
```

#### Scenario 5: Complete Compliance Assessment (All Tools)
*James receives an urgent request from the FCA for a compliance status report on SAM Technology & Infrastructure.*

**Complete Assessment**:
```
Conduct a complete compliance assessment for SAM Technology & Infrastructure including:
1. Historical breach alerts showing which have been resolved and which remain active
2. Current portfolio positions checked against concentration limits (single position and issuer)
3. Policy thresholds from our Concentration Risk Policy 
4. Any engagement notes documenting PM commitments for remediation
5. A formal Risk Committee compliance report using the appropriate template
6. Generate a professional PDF for FCA submission
```

---

### Middle Office Copilot

> **Persona**: Sarah, Middle Office Operations Manager  
> **Challenge**: Operations teams must monitor trade settlements, reconciliation breaks, NAV calculations, and corporate actions across multiple portfolios and custodians  
> **Value**: AI-powered operations intelligence providing real-time monitoring, automated exception detection, and intelligent remediation recommendations

#### Scenario: NAV Calculation & Settlement Monitoring
*It's 4:00 PM GMT and Sarah needs to review today's operational status across all middle office functions before the daily NAV calculation.*

**Primary - Settlement Failures**:
```
Show me all failed settlements from the past 3 business days and help me understand what's causing them.
```

**Reconciliation Breaks**:
```
Summarize today's reconciliation breaks for all portfolios and flag any that are critical.
```

**NAV Calculation Status**:
```
What's the status of today's NAV calculation across all funds? Are there any anomalies I need to investigate?
```

**Corporate Actions**:
```
Show me all pending corporate actions for the next 5 business days and highlight any that require immediate processing.
```

---

### Executive Command Center

> **Persona**: Sarah Chen, Head of Asset Management  
> **Challenge**: Executives need a timely "single pane of glass" view across a complex organization, moving from "what happened?" to "what's next?" in real-time  
> **Value**: AI-powered strategic command center providing real-time firm-wide KPIs, dynamic drill-down, competitor intelligence, and M&A simulation capabilities

#### Scenario 1: Holistic Business Performance Review
*Sarah is preparing for the monthly management committee meeting and needs a real-time briefing on firm performance.*

**Primary - Firm-Wide Performance Overview**:
```
Give me the key performance highlights for the firm, month-to-date. I want to see overall AUM, net flows, and our top and bottom 5 performing strategies.
```

**Client Flow Drill-Down**:
```
The inflows for Sustainable Fixed Income look strong. What is driving this? Is it one large client or broad-based demand?
```

**Strategic Document Context**:
```
What does our investment philosophy say about sustainable investing? How are we positioning this to clients?
```

**Executive Summary Synthesis**:
```
Summarize the key points I should highlight in the management committee meeting about our sustainable investing success.
```

#### Scenario 2: Competitor Intelligence & M&A Simulation
*Sarah spots a headline about a major competitor potentially divesting assets and wants to quickly assess the strategic opportunity.*

**Competitor Intelligence - M&A Scenario**:
```
I saw a headline about BlackRock potentially selling their European division. What do we know about the size and performance of that business from their SEC filings?
```

**Strategic Fit Assessment**:
```
How would their European business complement our current geographic presence? What overlaps or gaps would this address?
```

**M&A Financial Simulation**:
```
Let's model this. Run a high-level simulation of us acquiring that $50 billion AUM business. Use the revenue figures you found and apply our firm's standard assumptions for cost synergies. What is the projected impact on our earnings per share in the first year?
```

**Executive Memo Generation**:
```
That's a compelling number. Draft a confidential memo to the Chief Strategy Officer. Title it 'Project Europa: Preliminary Analysis.' Summarize the opportunity, our key findings, the potential EPS accretion, and ask them to prepare a more detailed analysis for us to review next week.
```

## Key Features

- **100% Real Assets**: 14,000+ authentic securities from SEC Filings (OpenFIGI)
- **Realistic Documents**: 3,463 documents from 69 curated templates
- **Industry-Standard Model**: Dimension/fact architecture with transaction audit trail
- **Multi-Tool Intelligence**: Cortex Analyst (SQL) + Cortex Search (documents)
- **Git Integration**: Notebook auto-loaded and executed from repository

## Resources

- **Snowflake Intelligence**: https://docs.snowflake.com/en/user-guide/snowflake-intelligence
- **Cortex Agents**: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents
- **Cortex Search**: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search
- **Cortex Analyst**: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst

## License

Apache 2.0 - Educational purposes. Securities data from public SEC filings via Snowflake Marketplace.
