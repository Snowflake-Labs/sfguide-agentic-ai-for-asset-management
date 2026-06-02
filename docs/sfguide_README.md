# Agentic AI for Asset Management

Build a complete multi-agent AI system for investment management using Snowflake Intelligence, Cortex Agents, Cortex Analyst, and Cortex Search.

## What You Get

| Component | Count | Description |
|-----------|-------|-------------|
| **Cortex Agents** | 8 | Portfolio, Research, Sales, Executive, Risk, Operations, Credit, Private Equity |
| **Semantic Views** | 10 | Cortex Analyst models for structured data queries |
| **Search Services** | 16 | Document retrieval across broker research, earnings, filings, press |
| **Agent Skills** | 36 | Specialized workflows (backtesting, Monte Carlo, memo generation, etc.) |
| **Data Tables** | 60+ | Real securities from 14,000+ SEC filings + generated portfolios |
| **ML Notebooks** | 3 | Factor discovery, market regime detection, credit risk modelling |

## Quick Start (15-20 minutes)

### Step 1: Run Infrastructure Setup (2 minutes)

Copy [`scripts/setup.sql`](scripts/setup.sql) into a Snowflake worksheet and execute it. This creates:
- `SAM_DEMO` database with all schemas
- `SAM_DEMO_ROLE` with required privileges (including task execution)
- Marketplace data share (Snowflake Public Data - Free)
- Cortex AI enablement and Snowflake Intelligence

### Step 2: Create Git Workspace

1. Navigate to **Projects > Workspaces**
2. Click **+** then **From Git repository**
3. Repository URL: `https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management.git`
4. Authentication: Public repository (no auth needed)
5. Name the workspace (e.g., "SAM Demo")

### Step 3: Run Setup (15-20 minutes)

1. Open `python/workspace_main.py` in the workspace
2. Connect a **notebook service** when prompted:
   - Python version: 3.11
   - Compute pool: any available pool
3. Install packages via the Packages panel:
   - `snowflake-snowpark-python`
   - `pyyaml`
   - `jinja2`
4. Click **Run**

The script builds everything sequentially:
- Dimension and fact tables from real securities data
- Market data from Snowflake Marketplace (SEC filings, prices, segments)
- Document corpus from 70+ templates
- Semantic views, search services, and tools
- All 8 Cortex Agents with skills

### Step 4: Use the Agents

1. Navigate to **AI & ML > Snowflake Intelligence**
2. Select any agent
3. Start asking questions!

## Agents

| Agent | Role | Key Capabilities |
|-------|------|-----------------|
| **Portfolio Copilot** | Portfolio Manager | Holdings, attribution, risk, backtest, Monte Carlo, performance narratives |
| **Research Copilot** | Research Analyst | Equity research reports, earnings intelligence, competitive analysis, investment memos |
| **Sales Advisor** | Client Relations | Meeting briefs, client letters, RFP responses, flow analytics |
| **Executive Command Center** | C-Suite | Firm KPIs, strategy ranking, competitor intelligence, M&A simulation |
| **Risk & Compliance** | Risk Officer | Position limits, mandate breaches, ESG monitoring, regulatory lookup |
| **Operations Copilot** | Middle Office | Settlement tracking, reconciliation, NAV, corporate actions |
| **Private Credit Copilot** | Credit PM | Covenant monitoring, deal pipeline, borrower financials |
| **Private Equity Copilot** | PE PM | Deal sourcing, due diligence, value creation tracking |

## Project Structure

```
python/
├── workspace_main.py       <- Workspace entry point (click Run)
├── main.py                 <- CLI entry point (local development)
├── config.py               <- Central configuration
├── ai/
│   ├── agents/             <- 8 agent definitions
│   ├── tools/              <- UDFs/SPs (backtest, Monte Carlo, PDF, etc.)
│   ├── builder.py          <- AI orchestration
│   ├── cortex_search.py    <- Search service creation
│   └── semantic_views.py   <- Semantic view creation
├── data/
│   ├── structured.py       <- Dimension/fact generation
│   ├── market_data.py      <- Marketplace data integration
│   ├── unstructured.py     <- Document corpus generation
│   └── pipelines.py        <- Stream/task pipeline infrastructure
├── core/                   <- Hydration engine, PDF export
└── utils/                  <- DB helpers, SQL utilities, logging

data/
├── skills/                 <- 36 agent skill definitions
└── reference_data/         <- YAML configurations

content_library/            <- 70+ document templates

notebooks/
├── factor_discovery.ipynb
├── market_regime_detection.ipynb
└── credit_risk_model.ipynb

scripts/
└── setup.sql               <- Infrastructure DDL (run first)
```

## Demo Scenarios

Each agent has documented demo scenarios with step-by-step conversations:

- [Portfolio Manager Scenarios](docs/demo_scenarios_portfolio_manager.md)
- [Research Analyst Scenarios](docs/demo_scenarios_research_analyst.md)
- [Sales Advisor Scenarios](docs/demo_scenarios_sales.md)
- [Executive Scenarios](docs/demo_scenarios_executive.md)
- [Risk & Compliance Scenarios](docs/demo_scenarios_risk_compliance.md)
- [Middle Office Scenarios](docs/demo_scenarios_middle_office.md)

## Cleanup

To remove all demo objects:
```sql
DROP DATABASE IF EXISTS SAM_DEMO;
DROP WAREHOUSE IF EXISTS SAM_DEMO_WH;
DROP ROLE IF EXISTS SAM_DEMO_ROLE;
```

## Requirements

- Snowflake account with Cortex features enabled
- ACCOUNTADMIN role (for initial setup)
- Snowflake Intelligence available
- A compute pool for the workspace notebook service

## License

Apache-2.0 — See [LICENSE](LICENSE) for details.
