# Agentic AI for Asset Management

Demonstration of Snowflake Intelligence for asset management with 8 specialized AI agents combining structured analytics and unstructured document intelligence.

## Overview

**Snowcrest Asset Management (SAM)** - A fictional investment firm managing £2.5B across 10 strategies. This guide shows how Snowflake Intelligence transforms workflows through AI agents that integrate portfolio data, research documents, and compliance monitoring in natural language.

## 8 AI Agents

| Agent | Role | Key Capabilities |
|-------|------|-----------------|
| **Portfolio Copilot** | Portfolio Manager | Analytics, concentration risk, event impact, implementation |
| **Research Copilot** | Research Analyst | Document research, company analysis, earnings intelligence |
| **Thematic Macro Advisor** | Thematic Strategist | Theme positioning, emerging trends, strategic allocation |
| **Quant Analyst** | Quantitative Analyst | Factor screening, performance attribution, factor evolution |
| **Sales Advisor** | Client Relations | Client reporting, template formatting, compliance review |
| **ESG Guardian** | ESG Officer | ESG monitoring, controversy detection, remediation planning |
| **Compliance Advisor** | Compliance Officer | Mandate monitoring, breach detection, regulatory tracking |
| **Middle Office Copilot** | Operations | Settlement monitoring, reconciliation, NAV validation |

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

## Prerequisites

- Snowflake account with Cortex features enabled
- ACCOUNTADMIN role (for setup)
- Snowflake Intelligence available
- [Snowflake Public Data (Free)](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255/snowflake-public-data-products-snowflake-public-data-free) Marketplace dataset

## Getting Started (One-Click Setup!)

### Run Setup Script

**Simply copy and paste** [`scripts/setup.sql`](scripts/setup.sql) **into a Snowflake SQL Worksheet and run it!**

This single script automatically:
1. Creates database infrastructure (SAM_DEMO)
2. Connects to Snowflake Public Data (Free) Marketplace dataset
3. Sets up Git integration to this repository
4. Loads and executes the setup notebook from Git
5. Generates 14,000+ real securities and 24 CURATED tables
6. Creates 3,463 documents from 69 templates (24 RAW tables)
7. Creates 22 Cortex Search services
8. Creates 7 Cortex Analyst semantic views
9. Creates 8 Snowflake Intelligence agents


### Access Agents

Once setup completes:
1. Navigate to **Snowflake Intelligence** in your Snowflake UI
2. Select **SAM_DEMO** database
3. Choose an agent (e.g., Portfolio Copilot)
4. Start asking questions!

## Example Prompts

**Portfolio Copilot**:
```
What are my top 10 holdings by market value in the SAM Technology & Infrastructure portfolio?
```

**Research Copilot**:
```
What is the latest research saying about AI and cloud computing opportunities in technology companies?
```

**ESG Guardian**:
```
I need a comprehensive ESG risk review for our SAM ESG Leaders Global Equity portfolio. Can you:
1. Scan NGO reports for High or Medium severity ESG controversies
2. Calculate exact exposure to companies with these controversies
3. Review our Sustainable Investment Policy requirements
4. Check engagement history with flagged companies
5. Provide a remediation plan with timelines and committee reviews
```

## Data Architecture

```
SAM_DEMO
├── RAW (Source data from SEC Filings + Generated documents)
├── CURATED (Business-ready data)
│   ├── Dimensions: Issuers (3,303), Securities (14,000+), Portfolios (10)
│   ├── Facts: Transactions, Holdings (27,000+), Market Data (4M+)
│   └── Document Corpus: 3,463 across 19 types
└── AI (Snowflake Intelligence)
    ├── 7 Semantic Views (Cortex Analyst)
    ├── 22 Cortex Search Services
    └── 8 AI Agents
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
