# Agentic AI for Asset Management

Build a complete multi-agent AI system for investment management using Snowflake CoWork, Cortex Agents, Cortex Analyst, and Cortex Search.

> This README describes the layout of the published sfguide repository, not this source repository. `scripts/sync_to_sfguide.sh` copies `scripts/workspace_setup.sql` to `scripts/setup.sql` and this file to `README.md` in that repository, so the paths below are correct for the destination.

## What You Get

| Component | Count | Description |
|-----------|-------|-------------|
| **Cortex Agents** | 8 | Portfolio Management, Research, Client Advisory, Executive Leadership, Risk & Compliance, Operations, Private Credit, Private Equity |
| **Semantic Views** | 17 | Cortex Analyst models for structured data queries |
| **Search Services** | 11 | Document retrieval across broker research, earnings, filings, press |
| **Agent Skills** | 36 | Specialized workflows (backtesting, Monte Carlo, memo generation, etc.) |
| **Data Tables** | 60+ | 503 real securities with SEC filings + generated portfolios |
| **ML Notebooks** | 3 | Factor discovery, market regime detection, credit risk modelling |

## Quick Start (about an hour)

### Step 1: Create Git Workspace

1. Navigate to **Projects > Workspaces**
2. Click **+** then **From Git repository**
3. Repository URL: `https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management.git`
4. Authentication: Public repository (no auth needed)
5. Name the workspace (e.g., "SAM Demo")

### Step 2: Run Setup (45-60 minutes)

Open [`scripts/setup.sql`](scripts/setup.sql) in the workspace.

**Set `$ws_name` in Section 0, at the top of the script, to the name of the workspace you
created in Step 1.** Run `SHOW WORKSPACES IN ACCOUNT` if you need to check the name.
That is the only value you need to edit.

Then execute the whole script, as `ACCOUNTADMIN`. Sections 1-8 create the
infrastructure:
- `SAM_DEMO` database with all schemas
- `SAM_DEMO_EXECUTION_WH` and `SAM_DEMO_CORTEX_WH` warehouses
- `FSI_DEMO_BUILD_ROLE` (build) and `SAM_DEMO_USER_ROLE` (demo consumption) with required privileges
- Compute pools, including `SAM_DEMO_ML_POOL` for the ML notebooks
- Marketplace data share (Snowflake Public Data - Free)
- Cortex AI enablement and Snowflake Intelligence

Section 9 then creates a Code Bundle from your workspace and runs the build, which
builds everything sequentially:
- Dimension and fact tables from real securities data
- Market data from Snowflake Marketplace (SEC filings, prices, segments)
- Document corpus from 70+ templates
- Semantic views, search services, and tools
- All 8 Cortex Agents with skills

There is no `pip install`, no kernel restart and no "click Run" step — packages are
installed declaratively from `code_bundle.yml`.

The build runs with `--skip-automation`, so the demo data stays frozen at the build
date and no scheduled task is left running. To keep the demo current, install the
weekly refresh task afterwards, which advances prices, documents and briefings every
Monday:

```sql
EXECUTE CODE BUNDLE SAM_DEMO.AI.SAM_BUILD_BUNDLE
    ENTRYPOINT = 'python/workspace_main.py'
    ARGUMENTS  = ('--scope', 'automation');
```

> If the `CREATE OR REPLACE CODE BUNDLE` result says *"source directory ... does not
> exist or contains no files"*, `$ws_name` does not match your workspace. Fix it and
> re-run that statement before continuing — it is only a warning, not an error, so
> the build would otherwise fail later with a missing entrypoint.

### Step 3: Use the Agents

1. Navigate to **AI & ML > Snowflake CoWork**
2. Select any agent
3. Start asking questions!

## Agents

| Agent | Role | Key Capabilities |
|-------|------|-----------------|
| **Portfolio Management Copilot** | Portfolio Manager | Holdings, attribution, risk, backtest, Monte Carlo, performance narratives |
| **Research Copilot** | Research Analyst | Equity research reports, earnings intelligence, competitive analysis, investment memos |
| **Client Advisory Copilot** | Client Relations | Meeting briefs, client letters, RFP responses, flow analytics |
| **Executive Leadership Copilot** | C-Suite | Firm KPIs, strategy ranking, competitor intelligence, M&A simulation |
| **Risk & Compliance Copilot** | Risk Officer | Position limits, mandate breaches, ESG monitoring, regulatory lookup |
| **Operations Copilot** | Middle Office | Settlement tracking, reconciliation, NAV, corporate actions |
| **Private Credit Copilot** | Credit PM | Covenant monitoring, deal pipeline, borrower financials |
| **Private Equity Copilot** | PE PM | Deal sourcing, due diligence, value creation tracking |

## Project Structure

```
python/
├── workspace_main.py       <- Build entry point (run by the Code Bundle in setup.sql)
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

Select the agent in Snowflake CoWork and start with the opening prompt, then follow the
agent's suggested next steps:

| Agent | Scenario | Opening prompt |
|-------|----------|----------------|
| Portfolio Management | Portfolio insights and benchmarking | *What are my top 10 holdings by market value in the SAM Technology & Infrastructure portfolio?* |
| Portfolio Management | Performance decomposition | *Break down the performance attribution for SAM Global Flagship portfolio versus S&P 500 for the most recent quarter. What drove our performance?* |
| Research | Investment memo (NVDA) | *What is the latest research saying about AI and cloud computing opportunities in technology companies?* |
| Risk & Compliance | Concentration breach, remediation and verification | *Run a concentration check across all portfolios using the latest month-end holdings. Show me any positions above the 6.5% warning threshold, sorted by weight.* |
| Client Advisory | RFP response | *I need to prepare an RFP response for a pension fund that wants an ESG equity mandate.* |
| Operations | NAV and settlement monitoring | *Show me all failed settlements from the past 3 business days and help me understand what's causing them.* |
| Executive Leadership | Complete executive briefing | *Prepare a complete executive briefing for the board covering firm-wide AUM and performance across all strategies, client flow analysis with any concentration concerns, our top and bottom performing strategies with context, and relevant investment philosophy positioning that explains our current strategic direction. Generate a professional PDF for board distribution.* |
| Private Equity | Portfolio company performance and value creation | *Give me an overview of our portfolio company performance. Which companies are on track and which need attention?* |
| Private Credit | Covenant breach investigation | *Check for covenant breaches across the portfolio. Show me any borrowers with breaches or headroom below 10%.* |

The demo date is the latest price date available in the Snowflake Public Data share at
build time, and positions are month-end, so "current" means the latest month-end.
Agents answer from that live data, so figures move as the data does.

## Cleanup

To remove all demo objects (run as `ACCOUNTADMIN`):
```sql
DROP DATABASE IF EXISTS SAM_DEMO;
DROP WAREHOUSE IF EXISTS SAM_DEMO_EXECUTION_WH;
DROP WAREHOUSE IF EXISTS SAM_DEMO_CORTEX_WH;
DROP COMPUTE POOL IF EXISTS SAM_DEMO_BUNDLE_POOL;
DROP COMPUTE POOL IF EXISTS SAM_DEMO_ML_POOL;
DROP ROLE IF EXISTS SAM_DEMO_USER_ROLE;
```

`FSI_DEMO_BUILD_ROLE`, the `FSI_DEMO_CONFIG` database, the `FSI_DEMO_PYPI_ACCESS`
integration and `FSI_DEMO_STREAMLIT_COMPUTE_POOL` are shared with other FSI demos. Drop
them as well only if no other FSI demo uses this account.

## Requirements

- Snowflake account with Cortex features enabled
- ACCOUNTADMIN role (for initial setup)
- Snowflake Intelligence available
- A Snowflake Workspace created from this Git repository (Step 1)

## License

Apache-2.0 — See [LICENSE](LICENSE) for details.
