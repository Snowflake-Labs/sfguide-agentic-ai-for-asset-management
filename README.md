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
├── README.md                # Setup guide
├── scripts/setup.sql        # Automated setup (15-20 min)
├── LICENSE
└── LEGAL.md
```

## Prerequisites

- Snowflake account with Cortex features enabled
- ACCOUNTADMIN role (for setup)
- Snowflake Intelligence available
- SEC Filings dataset (Cybersyn) access

## Getting Started

### 1. Run Setup Script

Execute [`scripts/setup.sql`](scripts/setup.sql) in Snowsight (15-20 minutes)

Creates:
- `SAM_DEMO` database (14,000+ real securities, 30+ tables, 3,463 documents)
- 7 semantic views for Cortex Analyst
- 16 Cortex Search services
- 8 AI agents registered with Snowflake Intelligence

### 2. Open Snowflake Intelligence

1. Navigate to Snowflake Intelligence
2. Select `SAM_DEMO` database
3. Choose an agent
4. Start asking questions (see example prompts below)

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
├── RAW (Source data from SEC Filings)
├── CURATED (Business-ready data)
│   ├── Dimensions: Issuers (3,303), Securities (14,000+), Portfolios (10)
│   ├── Facts: Transactions, Holdings (27,000+), Market Data (4M+)
│   └── Documents: 3,463 across 19 types
└── AI (Snowflake Intelligence)
    ├── 7 Semantic Views
    ├── 16 Cortex Search Services
    └── 8 AI Agents
```

## Key Features

- **100% Real Assets**: 14,000+ authentic securities from SEC Filings (OpenFIGI)
- **Realistic Documents**: 3,463 documents from 50+ curated templates
- **Industry-Standard Model**: Dimension/fact architecture with transaction audit trail
- **Multi-Tool Intelligence**: Cortex Analyst (SQL) + Cortex Search (documents)

## Troubleshooting

**"SEC_FILINGS database not found"**  
→ Request SEC Filings dataset access in Snowflake Marketplace

**"Snowflake Intelligence not found"**  
→ Run `CREATE SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;`

**"Cortex Search service creation failed"**  
→ Verify Cortex features enabled in your account/region

**"Semantic view compilation error"**  
→ Check column names match exactly (case-sensitive)

## Resources

- **Snowflake Intelligence**: https://docs.snowflake.com/en/user-guide/snowflake-intelligence
- **Cortex Agents**: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents
- **Cortex Search**: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search
- **Cortex Analyst**: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst

## License

Apache 2.0 - Educational purposes. Securities data from public SEC filings via Snowflake Marketplace.

