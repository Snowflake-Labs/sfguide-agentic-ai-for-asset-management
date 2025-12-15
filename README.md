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
| **Portfolio Copilot** | Portfolio Manager | 6 tools | Holdings analysis, concentration risk, event impact, supply chain exposure, implementation planning |
| **Research Copilot** | Research Analyst | 4 tools | Multi-source research, company analysis, earnings intelligence, investment memos |
| **Thematic Macro Advisor** | Thematic PM | 3 tools | Theme positioning, emerging trends, strategic allocation optimization |
| **Quant Analyst** | Quantitative Analyst | 4 tools | Factor screening, performance attribution, statistical validation |
| **Sales Advisor** | Client Relations | 4 tools | Client reporting, template formatting, philosophy integration, compliance review |
| **ESG Guardian** | ESG Officer | 3 tools | Controversy scanning, engagement tracking, remediation planning |
| **Compliance Advisor** | Compliance Officer | 3 tools | Mandate monitoring, breach detection, audit documentation |
| **Middle Office Copilot** | Operations Manager | 2 tools | Settlement monitoring, reconciliation breaks, NAV validation, corporate actions |
| **Executive Command Center** | C-Suite Executive | 7 tools | Firm-wide KPIs, client analytics, competitor intelligence, M&A simulation |

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
4. Loads and executes the setup notebook from Git
5. Generates 14,000+ real securities and 24 CURATED tables
6. Creates 3,463 documents from 69 templates (24 RAW tables)
7. Creates 17 Cortex Search services
8. Creates 7 Cortex Analyst semantic views
9. Creates 9 Snowflake Intelligence agents


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
*David Chen receives a compliance alert that META has been downgraded to ESG grade D, violating the fund's minimum BBB ESG requirement. He needs to identify a suitable replacement.*

**Mandate Compliance - ESG Breach**:
```
I've received an alert that META has been downgraded to ESG grade D. Can you verify this breach for the SAM AI & Digital Innovation portfolio and show me our current exposure?
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
