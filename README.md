# Agentic AI for Asset Management

## Overview

**Snowcrest Asset Management (SAM)** - A fictional investment firm managing £2.5B across 10 strategies. This guide shows how Snowflake Intelligence transforms workflows through AI agents that integrate portfolio data, research documents, and compliance monitoring in natural language.

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

| Agent | Key Capabilities |
|-------|-----------------|
| **Portfolio Advisor** | Analytics, concentration risk, event impact, implementation planning |
| **Research Advisor** | Document research, company analysis, earnings intelligence |
| **Thematic Macro Advisor** | Theme positioning, emerging trends, strategic allocation |
| **Quant Analyst** | Factor screening, performance attribution, factor evolution |
| **Sales Advisor** | Client reporting, template formatting, compliance review |
| **ESG Guardian** | ESG monitoring, controversy detection, remediation planning |
| **Compliance Advisor** | Mandate monitoring, breach detection, regulatory tracking |
| **Middle Office Advisor** | Settlement monitoring, reconciliation, NAV validation |
| **Executive Command Center** | Firm-wide KPIs, client analytics, competitor intelligence, M&A simulation |

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
7. Creates 22 Cortex Search services
8. Creates 7 Cortex Analyst semantic views
9. Creates 9 Snowflake Intelligence agents


### Step 3: Access Snowflake Intelligence

Once setup completes:
1. Navigate to **Snowflake Intelligence** in your Snowflake UI
2. Choose an agent (e.g., Portfolio Advisor)
3. Start asking questions!

## Example Prompts by Agent

### Portfolio Advisor

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

---

### Research Advisor

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

**Earnings Intelligence**:
```
Give me a comprehensive analysis of Microsoft's latest quarterly earnings, including reported financial metrics versus consensus estimates and key management commentary from the earnings call.
```

**Sentiment Analysis**:
```
Compare the sentiment between Microsoft's prepared remarks and the Q&A session. Are there any concerning shifts or defensive language that could indicate management uncertainty?
```

---

### Thematic Macro Advisor

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

---

### Quant Analyst

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

### Middle Office Advisor

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
