# Agentic AI for Asset Management

## Overview

**Simulated Asset Management (SAM)** is a fictional multi-asset investment firm managing multiple strategies. This guide showcases how **Snowflake Intelligence** transforms investment management through AI agents that seamlessly orchestrate:

- **Structured Data**: Real securities from SEC filings, portfolio holdings, factor exposures, ESG scores
- **Unstructured Documents**: Broker research reports, earnings transcripts, press releases, policy documents
- **Real-Time Analytics**: Cortex Analyst converts natural language to SQL
- **Document Intelligence**: Cortex Search enables RAG-powered document synthesis

### What Makes This Guide Unique

| Capability | Description |
|------------|-------------|
| **Real Securities** | All securities are authentic from SEC Filings (OpenFIGI) |
| **Multi-Tool Orchestration** | Agents dynamically combine 3-14 tools per query |
| **Industry-Standard Model** | Dimension/fact architecture with audit trails |
| **Complete Workflow Coverage** | Agents covering front, middle, back office |

---

## What You'll Learn

By exploring this guide, you'll understand how to:

1. **Build Multi-Tool AI Agents** - Combine Cortex Analyst (structured data) with Cortex Search (documents) in a single conversational interface

2. **Design Semantic Views** - Create business-friendly data models that translate natural language to SQL automatically

3. **Implement RAG at Scale** - Index thousands of documents across multiple corpus types with Cortex Search

4. **Create Industry-Specific Agents** - Configure agents with role-specific instructions, tool access, and business context

5. **Generate Realistic Demo Data** - Use template-based document generation with placeholder hydration for authentic content

6. **Integrate Real Data Sources** - Leverage Snowflake Marketplace for SEC filings, stock prices, and financial data

---

## Repository Structure

```
sfguide-agentic-ai-for-asset-management/
├── scripts/
│   ├── setup.sql                    # Automated setup (~15-20 min)
│   └── teardown.sql                 # Complete cleanup script
├── python/                          # Python modules
│   ├── config.py                    # Central configuration
│   ├── generate_structured.py       # Dimension/fact table generation
│   ├── generate_unstructured.py     # Document generation
│   ├── generate_market_data.py      # Real market data
│   ├── create_agents.py             # Agent definitions
│   ├── create_semantic_views.py     # Semantic view definitions
│   ├── create_cortex_search.py      # Search service definitions
│   └── ...
├── content_library/                 # Document templates
│   ├── _rules/                      # YAML config
│   ├── security/                    # Broker research, press releases
│   ├── issuer/                      # NGO reports, engagement notes
│   ├── portfolio/                   # IPS, portfolio reviews
│   └── global/                      # Policy docs, procedures
└── docs/                            # Demo scenario documentation
```

---

## Getting Started

### Prerequisites
- Snowflake account with Cortex features enabled
- ACCOUNTADMIN role (for setup)
- Snowflake Intelligence available

### Step 1: Get Marketplace Data (One-Time)

1. Log in to your Snowflake account
2. Go to [Snowflake Public Data (Free)](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255)
3. Click **"Get"** button (top right)
4. If prompted, enter your **Email** and click **"Save"** to complete your profile
5. In the "Get it for Free" dialog:
   - **Database name**: Keep default `Snowflake_Public_Data_Free`
   - **Which roles can access**: Select `ACCOUNTADMIN` (or your demo role)
6. Click **"Get"** to install the data share

> **Note**: This creates a shared database `SNOWFLAKE_PUBLIC_DATA_FREE` with 90+ sources of public domain data including SEC filings and financial data. 

### Step 2: Run Setup Script

**Copy and paste** [`scripts/setup.sql`](scripts/setup.sql) into a Snowflake SQL Worksheet and run it.

This automatically creates:
- CURATED dimension/fact tables and views
- RAW corpus tables from document templates
- MARKET_DATA tables with real SEC filings
- Cortex Search services for document retrieval
- Cortex Analyst semantic views for structured queries
- Snowflake Intelligence agents for each business role

### Step 3: Access Snowflake Intelligence

Navigate to **Snowflake Intelligence** → Choose an agent → Start asking questions!

---

## Cortex Agents

| Agent | Role | Tools | Key Capabilities |
|-------|------|-------|-----------------|
| **Portfolio Copilot** | Portfolio Manager | 14 | Holdings, risk, event impact, supply chain, SEC financials |
| **Research Copilot** | Research Analyst | 8 | Multi-source research, earnings, investment memos |
| **Thematic Macro Advisor** | Thematic PM | 6 | Theme positioning, macro events, allocation |
| **Quant Analyst** | Quantitative Analyst | 5 | Factor screening, attribution, validation |
| **Sales Advisor** | Client Relations | 6 | Client reporting, RFP, onboarding |
| **ESG Guardian** | ESG Officer | 9 | NGO reports, controversies, engagement |
| **Compliance Advisor** | Compliance Officer | 6 | Mandate monitoring, breach detection |
| **Middle Office Copilot** | Operations Manager | 6 | Settlement, reconciliation, NAV, corporate actions |
| **Executive Command Center** | C-Suite | 9 | Firm KPIs, competitor intel, M&A simulation |

---

## Multi-Tool Demo Prompts

These signature prompts showcase each agent's full orchestration capabilities. For complete step-by-step scenarios with talking points and expected responses, see the linked documentation.

---

### Portfolio Copilot
> **Anna, Senior PM** | 14 tools | [Full Scenarios →](docs/demo_scenarios_portfolio_manager.md)

**Event-Driven Risk Assessment** (9-Tool Orchestration):
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
> **David, Research Analyst** | 8 tools | [Full Scenarios →](docs/demo_scenarios_research_analyst.md)

**Investment Memo Generation**:
```
Generate a comprehensive investment research report for NVIDIA covering financial health, management outlook, analyst views, competitive position, and key risks. Include a Buy/Hold/Sell recommendation.
```

---

### Thematic Macro Advisor
> **Anna, Thematic PM** | 6 tools | [Full Scenarios →](docs/demo_scenarios_thematic_advisor.md)

**AI Infrastructure Strategy Development**:
```
I'm developing our Q1 2025 thematic investment strategy around artificial intelligence infrastructure. Can you:
1. Analyze our current portfolio exposure to AI and data center themes across all portfolios
2. Find the latest broker research identifying key AI infrastructure sub-themes and investment opportunities
3. Review what major technology company managements are saying in earnings calls about AI spending and data center capacity plans
4. Check recent corporate announcements for AI infrastructure investments and partnerships
5. Synthesize this into a thematic positioning recommendation showing where we're under-positioned relative to the emerging AI infrastructure opportunity
```

---

### Quant Analyst
> **Dr. James Chen, Quant** | 5 tools | [Full Scenarios →](docs/demo_scenarios_quant_analyst.md)

**Multi-Factor Screening Strategy**:
```
I'm building a multi-factor stock screening strategy focusing on Value, Quality, and improving Momentum. Can you:
1. Screen our investment universe for securities with high Quality and Value factor exposures
2. Within those results, identify companies showing improving Momentum factor trends over the last 6 months
3. Validate the financial fundamentals using SEC filing data - confirm revenue growth, margin expansion, and balance sheet quality
4. Cross-reference with analyst research to see if broker recommendations align with our factor signals
5. Check earnings transcripts for management commentary supporting the quality and growth characteristics
6. Provide a ranked list with factor scores, fundamental validation, analyst views, and statistical significance testing (R-squared, p-values) for the systematic investment strategy
```

---

### Sales Advisor
> **James Mitchell, Client Manager** | 6 tools | [Full Scenarios →](docs/demo_scenarios_client_relations.md)

**Quarterly Client Presentation**:
```
I need to prepare a quarterly client presentation for our SAM ESG Leaders Global Equity portfolio. Can you:
1. Get Q4 2024 performance data including portfolio returns vs benchmark, top holdings, sector allocation, and ESG metrics
2. Retrieve our quarterly client report template to follow the approved structure and formatting
3. Find our ESG investment philosophy documentation to integrate our differentiated approach and sustainable development beliefs
4. Get the required regulatory disclaimers and risk warnings from compliance policies
5. Generate a professional client-ready quarterly report that combines performance data, investment philosophy, and compliance disclosures in the approved template format
```

---

### ESG Guardian
> **Sofia, ESG Officer** | 9 tools | [Full Scenarios →](docs/demo_scenarios_esg_officer.md)

**Complete ESG Risk Assessment**:
```
Conduct a complete ESG risk assessment for SAM ESG Leaders Global Equity including scanning NGO reports for any High or Medium severity controversies affecting our holdings, calculating exact portfolio exposure to flagged companies, verifying against our Sustainable Investment Policy thresholds, checking engagement history with any flagged companies, and providing a prioritised remediation plan with severity-based timelines and ESG Committee recommendations. Generate a formal ESG Committee report using our standard template.
```

---

### Compliance Advisor
> **Michael, Compliance Officer** | 6 tools | [Full Scenarios →](docs/demo_scenarios_compliance_officer.md)

**Complete Compliance Assessment**:
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
> **Sarah, Operations Manager** | 6 tools | [Full Scenarios →](docs/demo_scenarios_middle_office.md)

**End-of-Day Operations Review**:
```
Show me all failed settlements from the past 3 business days and help me understand what's causing them.
```

```
Summarize today's reconciliation breaks for all portfolios and flag any that are critical.
```

```
What's the status of today's NAV calculation across all funds? Are there any anomalies I need to investigate?
```

```
Show me all pending corporate actions for the next 5 business days and highlight any that require immediate processing.
```

---

### Executive Command Center
> **Sarah Chen, Head of AM** | 9 tools | [Full Scenarios →](docs/demo_scenarios_executive.md)

**Complete Board Briefing with PDF**:
```
Prepare a complete executive briefing for the board covering firm-wide AUM and performance across all strategies, client flow analysis with any concentration concerns, our top and bottom performing strategies with context, and relevant investment philosophy positioning that explains our current strategic direction. Generate a professional PDF for board distribution.
```

**M&A Simulation**:
```
Let's model this. Run a high-level simulation of us acquiring that $50 billion AUM business. Use the revenue figures you found and apply our firm's standard assumptions for cost synergies. What is the projected impact on our earnings per share in the first year?
```

---

## Detailed Scenario Documentation

For presenters preparing demos, each role has comprehensive documentation with step-by-step conversation flows, expected responses, talking points, and business value articulation.

| Role | Documentation |
|------|---------------|
| Portfolio Manager | [demo_scenarios_portfolio_manager.md](docs/demo_scenarios_portfolio_manager.md) |
| Research Analyst | [demo_scenarios_research_analyst.md](docs/demo_scenarios_research_analyst.md) |
| Thematic Advisor | [demo_scenarios_thematic_advisor.md](docs/demo_scenarios_thematic_advisor.md) |
| Quant Analyst | [demo_scenarios_quant_analyst.md](docs/demo_scenarios_quant_analyst.md) |
| Client Relations | [demo_scenarios_client_relations.md](docs/demo_scenarios_client_relations.md) |
| ESG Officer | [demo_scenarios_esg_officer.md](docs/demo_scenarios_esg_officer.md) |
| Compliance Officer | [demo_scenarios_compliance_officer.md](docs/demo_scenarios_compliance_officer.md) |
| Middle Office | [demo_scenarios_middle_office.md](docs/demo_scenarios_middle_office.md) |
| Executive | [demo_scenarios_executive.md](docs/demo_scenarios_executive.md) |
| Risk & Compliance | [demo_scenarios_risk_compliance.md](docs/demo_scenarios_risk_compliance.md) |

**Reference Documentation:**
- [Data Model](docs/data_model.md) - Complete data architecture
- [Data Lineage](docs/data_lineage.md) - Data flow documentation
- [Scenario Overview](docs/demo_scenarios.md) - All scenarios by role

---

## Conclusion

This guide represents **the future of enterprise AI in financial services**: a unified intelligence layer where every role—from portfolio managers to compliance officers to executives—can access both quantitative analytics and qualitative insights through natural conversation.

**For Asset Managers**: Imagine a world where your investment professionals spend zero time hunting for data across systems, manually compiling reports, or waiting for Data team to build dashboards. Every question gets an immediate, comprehensive answer that combines portfolio analytics with research, risk metrics with policy guidance, and performance data with client context.

**For Snowflake Practitioners**: This guide provides a complete blueprint for building production-grade AI agents:
- How to structure semantic views for complex financial data
- How to design corpus tables for multi-document RAG
- How to configure agent instructions for different personas
- How to orchestrate multiple tools in a single conversation

**The Vision**: When AI can seamlessly bridge structured and unstructured data, understand business context, and generate professional outputs—investment teams move from reactive to proactive, from data gathering to insight generation, from manual compliance to automated governance.

---

## Resources

- [Snowflake Intelligence Documentation](https://docs.snowflake.com/en/user-guide/snowflake-intelligence)
- [Cortex Agents Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)

---

## License

Copyright (c) Snowflake Inc. All rights reserved.

Licensed under the Apache 2.0 license.