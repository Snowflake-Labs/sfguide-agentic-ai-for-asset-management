# SAM Demo - Scenario Scripts

Complete demo scenarios organized by scenario (matching `config.SCENARIOS`), with step-by-step conversations, expected responses, and data flows.

---

## Scenarios Overview

| Scenario | Agent | Demo Surface | Doc |
|----------|-------|--------------|-----|
| `portfolio_management` | `AM_portfolio_management_copilot` | Cockpit + SI | [Portfolio Management](demo_scenarios_portfolio_management.md) |
| `research` | `AM_research_copilot` | SI | [Research](demo_scenarios_research.md) |
| `risk_compliance` | `AM_risk_compliance_copilot` | SI | [Risk & Compliance](demo_scenarios_risk_compliance.md) |
| `client_advisory` | `AM_client_advisory_copilot` | SI | [Client Advisory](demo_scenarios_client_advisory.md) |
| `operations` | `AM_operations_copilot` | SI | [Operations](demo_scenarios_operations.md) |
| `executive_leadership` | `AM_executive_leadership_copilot` | SI | [Executive Leadership](demo_scenarios_executive_leadership.md) |
| `private_equity` | `AM_private_equity_copilot` | Cockpit + SI | [Private Equity](demo_scenarios_private_equity.md) |
| `private_credit` | `AM_private_credit_copilot` | Cockpit + SI | [Private Credit](demo_scenarios_private_credit.md) |
| `market_regime_ml` | *(ML notebook)* | Notebook | [ML Scenarios](demo_scenarios_ml.md#market-regime-detection) |
| `factor_workflow_ml` | *(ML notebook)* | Notebook | [ML Scenarios](demo_scenarios_ml.md#factor-model-workflow) |
| `credit_risk_ml` | *(ML notebook)* | Notebook | [ML Scenarios](demo_scenarios_ml.md#credit-risk-scoring) |

**SI** = Snowflake Intelligence, **Cockpit** = PM Cockpit (SPCS app)

---

## Agent Scenarios (8 agents)

### [Portfolio Management](demo_scenarios_portfolio_management.md)
**Agent**: `AM_portfolio_management_copilot`

The primary demo agent — covers portfolio management, attribution analysis, factor/quant strategy, thematic investing, and portfolio modelling. Demonstrated via the PM Cockpit SPCS app or Snowflake Intelligence directly.

| Part | Coverage |
|------|----------|
| Portfolio Management | Holdings review, company analysis, event-driven risk, mandate compliance |
| Attribution & Risk Decomposition | Brinson deep dive, macro regime, sector attribution, hidden factors, stress tests |
| Quantitative / Factor Analysis | Multi-factor screening, factor strategy, ad-hoc regression |
| Thematic Strategy | AI infrastructure, yield curve, thematic catch-all |
| Portfolio Modelling | IPS-driven construction, retirement planning, Monte Carlo, optimisation |

---

### [Research](demo_scenarios_research.md)
**Agent**: `AM_research_copilot`

Document research and analysis — broker research synthesis, earnings intelligence, investment memos, insider/institutional ownership.

---

### [Risk & Compliance](demo_scenarios_risk_compliance.md)
**Agent**: `AM_risk_compliance_copilot`

Mandate compliance monitoring, ESG risk assessment, breach remediation, stewardship, and regulatory reporting.

| Part | Coverage |
|------|----------|
| Compliance Monitoring | Concentration limits, policy lookup, breach tracking, insider surveillance |
| ESG Risk & Stewardship | ESG reviews, controversy scanning, rating monitoring, engagement, SFDR/taxonomy |

---

### [Client Advisory](demo_scenarios_client_advisory.md)
**Agent**: `AM_client_advisory_copilot`

Client relationship management — strategy Q&A, performance stories, RFP responses, onboarding, at-risk analysis, segmentation.

---

### [Operations](demo_scenarios_operations.md)
**Agent**: `AM_operations_copilot`

Middle office operations monitoring — NAV calculation, settlement failures, reconciliation breaks, corporate actions.

---

### [Executive Leadership](demo_scenarios_executive_leadership.md)
**Agent**: `AM_executive_leadership_copilot`

Firm-wide KPIs, strategic M&A analysis, competitor intelligence, board-ready briefings.

---

### [Private Equity](demo_scenarios_private_equity.md)
**Agent**: `AM_private_equity_copilot`

Private equity deal sourcing, due diligence, portfolio company monitoring, value creation tracking, and fund-level reporting.

---

### [Private Credit](demo_scenarios_private_credit.md)
**Agent**: `AM_private_credit_copilot`

Credit portfolio monitoring, covenant tracking, rate sensitivity, deal pipeline screening, and ML credit risk scoring.

---

## ML Scenarios (3 notebooks)

### [ML Development](demo_scenarios_ml.md)

Notebook-based ML workflows — no agent, demoed via Snowflake Notebooks.

| Scenario | Notebook | Description |
|----------|----------|-------------|
| `market_regime_ml` | Market Regime Detection | GMM regime classification via Feature Store |
| `factor_workflow_ml` | Factor Model Workflow | XGBoost factor return prediction |
| `credit_risk_ml` | Credit Risk Scoring | XGBoost PD model with SHAP explainability |
