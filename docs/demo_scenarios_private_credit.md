# SAM Demo - Private Credit Scenario Scripts

> **Agent**: `AM_private_credit_copilot`  
> **Skills**: `covenant-monitoring`, `rate-sensitivity-analysis`, `deal-pipeline-screening`, `credit-portfolio-review`, `credit-risk-calculator`, `audience-adaptive-narrative`  
> **Common Tools**: `server_skill`, `code_execution`, `data_to_chart`

## Available Scenarios by Role

### Head of Credit
**Agent: AM_private_credit_copilot**
- Rate Sensitivity & Portfolio Impact ✅ **IMPLEMENTED** — *Skill: `rate-sensitivity-analysis`*
- Covenant Breach Investigation & Resolution ✅ **IMPLEMENTED** — *Skill: `covenant-monitoring`*
- Deal Pipeline Screening & Evaluation ✅ **IMPLEMENTED** — *Skill: `deal-pipeline-screening`*
- **Complete Credit Portfolio Review** ✅ **IMPLEMENTED** — *Skill: `credit-portfolio-review`*
- **ML-Powered Credit Risk Assessment** ✅ **IMPLEMENTED** — *Skill: `credit-risk-calculator`*
- **What-If PD Sensitivity Analysis** ✅ **IMPLEMENTED** — *Skill: `credit-risk-calculator`*

---

## Head of Credit

### Head of Credit - Rate Sensitivity & Portfolio Impact

#### Business Context Setup

**Persona**: Sarah, Head of Private Credit at Simulated Asset Management. She manages 3 credit funds (SAM Direct Lending Fund III, SAM Opportunistic Credit Fund, SAM Structured Credit Fund) with 15 borrowers across ~$6.2B AUM.
**Business Challenge**: Private credit portfolios with floating rate exposure require constant monitoring of base rate movements and their impact on borrower interest expense, coverage ratios, and covenant headroom. Traditional spreadsheet-based analysis across 15+ borrowers with different SOFR spreads, floors, and PIK toggles is time-consuming and error-prone, risking missed early warning signals on deteriorating credits.
**Value Proposition**: AI-powered rate sensitivity analysis instantly calculates portfolio-wide impact of rate scenarios, identifies borrowers most at risk from rate changes, and cross-references with covenant headroom and compliance certificate commentary for a complete picture.

**Agent**: `AM_private_credit_copilot`
**Skill**: `rate-sensitivity-analysis`
**Data Available**: 3 funds, 15 borrowers, 20 credit facilities, quarterly financials, covenant tracking, sector benchmarks, policy rate history, credit agreements, compliance certificates

#### Demo Flow

**Scene Setting**: The Federal Reserve has signalled a potential 50bps rate cut at the next meeting. Sarah needs to quickly assess the impact on her portfolio's interest income, identify borrowers where rate floors provide protection, and flag any credits where reduced interest expense might not prevent covenant deterioration.

##### Step 1: Rate Exposure Overview (Skill Step 1)

**User Input**:
```
Give me a summary of our credit portfolio's floating rate exposure - total commitments, drawn amounts, weighted average spread, and breakdown by facility type.
```

**What Happens**:
- Agent loads `rate-sensitivity-analysis` skill via `server_skill`
- Skill Step 1 executes: `credit_portfolio_analyzer` for facility terms + `macro_data_analyzer` for current SOFR

**Expected Response**:
- Portfolio floating vs fixed split, SOFR floor coverage, weighted average spread
- Rate environment context with current SOFR
- **STOPPING POINT**: Agent offers 4 options:
  1. **Model rate shock scenarios** (+100bp / +200bp / +300bp impact on DSCR)
  2. **Identify most vulnerable borrowers** (lowest DSCR at current rates)
  3. **Review PIK and rate protection terms** (credit agreement provisions)
  4. **Compare to sector benchmarks** (spread and leverage vs peers)

**Talking Points**:
- Skill-driven workflow ensures consistent, comprehensive analysis
- Agent pauses to let user direct the investigation
- Multi-tool orchestration (portfolio + macro data) happens automatically

##### Step 2: Follow User's Choice (Skill Step 2a-d)

**Presenter picks one option** (recommended: "Model rate shock scenarios" for maximum impact):

**User Input** (example for rate shock):
```
Model rate shock scenarios - what happens at +100, +200, and +300bp
```

**What Happens**:
- Skill Step 2a: `credit_portfolio_analyzer` models coverage at each rate scenario

**Expected Response**:
- Impact table showing current vs stressed DSCR for each borrower
- "At +200bp, [X] borrowers would breach coverage covenant"
- Most sensitive borrower highlighted

##### Step 3: Deep Dive on Pinnacle Software Solutions

**Presenter Transition**:
> "Pinnacle Software Solutions stands out as most vulnerable. Let's understand why."

**User Input**:
```
Deep-dive Pinnacle Software Solutions - what is their rate protection and PIK situation?
```

**What Happens**:
- Agent may load additional skill branches or use tools directly for the deep-dive
- `credit_portfolio_analyzer` for financials + `search_credit_agreements` for PIK provisions

**Expected Response**:
- Pinnacle's financial profile, SOFR floor, PIK toggle terms
- Covenant headroom under stress
- Management commentary from compliance certificates

##### Step 4: Sector Context

**User Input**:
```
How does Pinnacle's pricing compare to Technology sector benchmarks?
```

**Expected Response**:
- Relative value assessment vs sector medians
- Portfolio positioning conclusions

#### Scenario Wrap-up

**Business Impact Summary**:
- **Decision Speed**: Rate sensitivity analysis completed in minutes vs hours
- **Skill-Guided Workflow**: Consistent analytical framework with stopping points for user direction
- **Cross-Reference**: Quantitative data + document intelligence in single workflow

**Technical Differentiators**:
- **Skill-Driven**: `rate-sensitivity-analysis` skill provides structured workflow with STOPPING POINT
- **Multi-Tool Orchestration**: Agent seamlessly combines Cortex Analyst + Cortex Search
- **Scenario Analysis**: Real-time rate sensitivity using actual facility terms

---

### Head of Credit - Covenant Breach Investigation & Resolution

#### Business Context Setup

**Persona**: Sarah, Head of Private Credit at Simulated Asset Management
**Business Challenge**: When covenant breaches are flagged, the credit team must rapidly assess severity, review cure provisions, examine compliance certificates, and prepare committee recommendations.
**Value Proposition**: AI-driven covenant breach investigation consolidates quantitative data, legal provisions, and compliance history into a single skill-guided workflow.

**Agent**: `AM_private_credit_copilot`
**Skill**: `covenant-monitoring`
**Data Available**: Covenant tracking with breach/waiver/cure history, credit agreements, compliance certificates, borrower financials

#### Demo Flow

**Scene Setting**: Quarterly compliance certificates have arrived and the monitoring system has flagged covenant breaches. Sarah needs to investigate before the weekly credit committee meeting.

##### Step 1: Covenant Breach Detection (Skill Step 1)

**User Input**:
```
Check for covenant breaches across the portfolio. Show me any borrowers with breaches or headroom below 10%.
```

**What Happens**:
- Agent loads `covenant-monitoring` skill via `server_skill`
- Skill Step 1: `credit_portfolio_analyzer` queries all covenant breaches and tight headroom

**Expected Response**:
- Breach summary table: Borrower | Covenant | Threshold | Actual | Headroom | Status
- Borrowers with <10% headroom flagged as "TIGHT"
- **STOPPING POINT**: Agent offers 4 options:
  1. **Deep-dive a specific borrower** (full covenant history + financials)
  2. **Review cure provisions** (credit agreement equity cure, waiver terms)
  3. **Check management commentary** (compliance certificate narrative)
  4. **Generate credit committee summary** (structured severity + recommendation)

**Talking Points**:
- Skill-driven stopping point lets user direct the investigation naturally
- Portfolio-wide screening identifies all issues in one pass
- Headroom calculation and breach detection automated

##### Step 2: Borrower Deep-Dive (Skill Step 2a)

**Presenter picks**: "Deep-dive Orion Retail Group" (known watchlist borrower)

**User Input**:
```
Deep-dive Orion Retail Group - show me covenant trajectory over the last 4 quarters
```

**Expected Response**:
- Quarterly covenant performance with trend (improving/deteriorating)
- Waiver and equity cure history

##### Step 3: Cure Provisions (Skill Step 2b)

**User Input**:
```
Review the cure provisions in Orion's credit agreement
```

**What Happens**:
- `search_credit_agreements` retrieves equity cure provisions, events of default, PIK terms

**Expected Response**:
- Cure mechanism details, waiver terms, amendment provisions
- Remaining cure capacity

##### Step 4: Management Commentary (Skill Step 2c)

**User Input**:
```
What is management saying about the deterioration? Check the compliance certificates.
```

**Expected Response**:
- Management's explanation, remediation plans, forward outlook
- Comparison to prior quarter narrative

##### Step 5: Credit Committee Summary (Skill Step 2d)

**User Input**:
```
Generate the credit committee summary for Orion
```

**Expected Response**:
- Structured recommendation: Severity | Trend | Root Cause | Available Remedies | Recommended Action
- Supporting evidence from all prior steps

#### Scenario Wrap-up

**Business Impact Summary**:
- **Response Time**: Covenant investigation reduced from days to minutes
- **Completeness**: Every relevant document and data point surfaced automatically
- **Governance**: Documented analytical trail with structured stopping points

**Technical Differentiators**:
- **Skill-Driven**: `covenant-monitoring` skill with STOPPING POINT after breach detection
- **Document + Data Fusion**: Structured data + credit agreements + compliance certificates
- **Synthesis**: Agent combines multiple tool outputs into committee-ready recommendations

---

### Head of Credit - Deal Pipeline Screening & Evaluation

#### Business Context Setup

**Persona**: Sarah, Head of Private Credit at Simulated Asset Management
**Business Challenge**: Evaluating pipeline deals against portfolio limits, pricing benchmarks, and IC analysis requires pulling data from multiple systems.
**Value Proposition**: AI-powered deal screening evaluates pipeline opportunities against portfolio and market context in a single skill-guided workflow.

**Agent**: `AM_private_credit_copilot`
**Skill**: `deal-pipeline-screening`
**Data Available**: Deal pipeline (10 active), portfolio facilities, sector benchmarks, IC memos, credit agreements

#### Demo Flow

**Scene Setting**: Weekly deal committee in two hours. Quantum Cyber Security at 6.2x leverage needs assessment.

##### Step 1: Pipeline Overview (Skill Step 1)

**User Input**:
```
Show me the current deal pipeline with stage, sector, size, spread, and expected leverage
```

**What Happens**:
- Agent loads `deal-pipeline-screening` skill via `server_skill`
- Skill Step 1: `credit_portfolio_analyzer` queries pipeline data with scoring

**Expected Response**:
- Pipeline table with A/B/C scoring per deal
- Portfolio fit assessment (concentration impact)
- **STOPPING POINT**: Agent offers 4 options:
  1. **Deep-dive a specific deal** (full credit assessment + covenant structure)
  2. **Run comparable analysis** (similar deals in portfolio + market)
  3. **Check portfolio fit** (concentration limits, sector exposure)
  4. **Generate IC screening memo** (structured recommendation with scoring matrix)

##### Step 2: Deal Deep-Dive (Skill Step 2a)

**User Input**:
```
Deep-dive Quantum Cyber Security - compare to our existing tech borrowers
```

**Expected Response**:
- Full financial profile + covenant package assessment
- Comparison to Pinnacle Software Solutions and Vertex Telecom Infrastructure

##### Step 3: IC Memo Review

**User Input**:
```
What does the IC team's analysis say about Quantum?
```

**What Happens**:
- `search_ic_memos` retrieves investment committee memorandum

**Expected Response**:
- Investment thesis, key risks, sponsor assessment, IC recommendation

##### Step 4: IC Screening Memo (Skill Step 2d)

**User Input**:
```
Generate the IC screening memo for Quantum
```

**Expected Response**:
- Scoring matrix (Credit Quality, Pricing, Covenants, Portfolio Fit, Sponsor — each 1-5)
- Recommendation: PROCEED / CONDITIONAL / PASS
- Key considerations (For/Against) and recommended term modifications

#### Scenario Wrap-up

**Technical Differentiators**:
- **Skill-Driven**: `deal-pipeline-screening` skill with scoring matrix and STOPPING POINT
- **Cross-Skill**: References `covenant-monitoring` and `rate-sensitivity-analysis` for deeper analysis
- **IC Document Intelligence**: Structured extraction from investment committee memoranda

---

### Head of Credit - Complete Credit Portfolio Review

#### Business Context Setup

**Persona**: Sarah, Head of Private Credit at Simulated Asset Management
**Business Challenge**: Quarterly board review requires comprehensive portfolio assessment covering composition, quality, covenants, rates, pipeline, and market positioning.
**Value Proposition**: AI-powered portfolio review generates a comprehensive assessment with skill-guided branching for deep-dives on any dimension.

**Agent**: `AM_private_credit_copilot`
**Skill**: `credit-portfolio-review`
**Data Available**: Complete credit portfolio data, covenant tracking, deal pipeline, benchmarks, credit agreements, compliance certificates, IC memos, policy rates

#### Demo Flow

**Scene Setting**: Quarterly board meeting next week. Sarah needs a comprehensive review.

##### Step 1: Portfolio Health Dashboard (Skill Step 1)

**User Input**:
```
Give me a comprehensive overview of our private credit portfolio for the quarterly board review
```

**What Happens**:
- Agent loads `credit-portfolio-review` skill via `server_skill`
- Skill Step 1: `credit_portfolio_analyzer` for all KPIs — NAV, positions, spreads, leverage, DSCR, watchlist

**Expected Response**:
- KPI summary table (current vs prior quarter with changes)
- Rating distribution, health verdict
- **STOPPING POINT**: Agent offers 4 options:
  1. **Analyse concentration risk** (sector, sponsor, geography, single-name limits)
  2. **Review credit migrations** (rating upgrades and downgrades)
  3. **Deep-dive the watchlist** (detailed status on flagged names)
  4. **Generate quarterly portfolio report** (IC-ready comprehensive format)

##### Step 2: User-Directed Deep-Dives

**Presenter picks multiple branches** to show the workflow flexibility:

**User Input** (concentration):
```
Show me concentration risk - are we within limits?
```

**Expected Response**:
- Concentration table by sector, sponsor, geography with current vs limits
- HHI assessment

**User Input** (quarterly report):
```
Generate the quarterly portfolio report
```

**Expected Response**:
- Executive summary, performance metrics, credit quality assessment
- Concentration analysis, key actions, and forward outlook
- IC-ready format

#### Scenario Wrap-up

**Technical Differentiators**:
- **Skill-Driven**: `credit-portfolio-review` skill with comprehensive health dashboard
- **Cross-Skill**: References `covenant-monitoring`, `rate-sensitivity-analysis`, `deal-pipeline-screening` for deeper analysis
- **Board-Ready**: Structured output suitable for quarterly board presentation

---

## ML-Powered Credit Risk Assessment

### Business Context Setup

**Persona**: Sarah, Head of Private Credit at Simulated Asset Management
**Business Challenge**: Covenant monitoring catches problems after they happen. Sarah needs forward-looking risk assessment that predicts which borrowers are most likely to deteriorate.
**Value Proposition**: ML-based probability of default with SHAP explainability, guided by the `credit-risk-calculator` skill workflow.

**Agent**: `AM_private_credit_copilot`
**Skill**: `credit-risk-calculator`
**Data Available**: ML credit risk scores (`FACT_CREDIT_RISK_SCORES`), SHAP explanations (`FACT_CREDIT_SHAP_EXPLANATIONS`)

**Prerequisites**: Run `notebooks/credit_risk_model.ipynb` first to populate prediction and explanation tables.

### Demo Flow

#### Step 1: Portfolio Risk Overview

**User Input**:
```
Show me the current credit risk scores for all borrowers, sorted by probability of default. Which borrowers are in the high-risk category?
```

**Expected Response**:
- Risk rating distribution (HIGH_RISK, ELEVATED, MODERATE, LOW_RISK)
- Top borrowers by PD score with key financial metrics

#### Step 2: Individual Borrower Deep Dive (Skill Activates)

**User Input**:
```
Explain why [highest-risk borrower] has the highest risk score. What are the top factors driving their probability of default?
```

**What Happens**:
- Agent loads `credit-risk-calculator` skill via `server_skill`
- Skill Step 1: `credit_risk_analyzer` retrieves current features
- Skill Step 2: Presents baseline profile
- **STOPPING POINT**: Agent offers 4 options:
  1. **Run baseline PD calculation**
  2. **Model a stress scenario**
  3. **Compare multiple scenarios side by side**
  4. **Explain key risk drivers** (SHAP waterfall)

**Expected Response**:
- Borrower's PD score, risk rating, feature comparison to portfolio average
- STOPPING POINT with branching options

#### Step 3: SHAP Analysis (Skill Step 3d)

**User Input**:
```
Show me the SHAP waterfall - what exactly drives the PD score?
```

**Expected Response**:
- SHAP feature importance table with direction (increases/decreases risk)
- Base PD → Final PD attribution
- Key insight on primary risk driver

#### Step 4: Early Warning

**User Input**:
```
Which borrowers have shown the largest increase in risk score over the last two quarters?
```

**Expected Response**:
- Borrowers with largest PD increases
- Key features driving deterioration
- Cross-reference to covenant headroom (→ `covenant-monitoring` skill)

### Scenario Wrap-up

**Technical Differentiators**:
- **Skill-Driven**: `credit-risk-calculator` skill with STOPPING POINT after baseline profile
- **SHAP Explainability**: Model-agnostic feature importance computed on demand
- **Cross-Skill**: References `covenant-monitoring` for covenant context on high-risk borrowers

---

## What-If PD Sensitivity Analysis

### Business Context Setup

**Persona**: Sarah, Head of Private Credit at Simulated Asset Management
**Business Challenge**: When a borrower's financials deteriorate, Sarah needs to understand how much the probability of default changes under different stress scenarios.
**Value Proposition**: The `code_execution` tool lets the agent run PD model recalculations in-conversation, guided by the `credit-risk-calculator` skill.

**Agent**: `AM_private_credit_copilot`
**Skill**: `credit-risk-calculator`
**Data Available**: ML credit risk scores, SHAP explanations, borrower financials

**Prerequisites**: Run `notebooks/credit_risk_model.ipynb` first.

### Demo Flow

**Scene Setting**: Credit committee meeting. Pinnacle Software Solutions has deteriorating margins — the committee wants leverage sensitivity analysis and SHAP explanation.

#### Step 1: Baseline Risk Profile (Skill Step 1-2)

**User Input**:
```
Show me the current PD score and risk rating for Pinnacle Software Solutions, along with their key financial metrics
```

**What Happens**:
- Agent loads `credit-risk-calculator` skill
- Presents baseline profile with feature comparison
- **STOPPING POINT**: Agent offers 4 options

**Expected Response**:
- PD score, risk rating, key metrics vs portfolio average
- Stopping point with branching options

#### Step 2: Leverage Sensitivity (Skill Step 3c)

**User Input**:
```
Compare multiple scenarios: what happens at +0.5x, +1.0x, and +1.5x leverage?
```

**What Happens**:
- Skill Step 3c: `code_execution` runs multi-scenario PD calculation

**Expected Response**:
- Scenario table: Leverage | PD | Rating | Change for each increment
- Threshold analysis: "Pinnacle crosses into HIGH_RISK at [X.X]x leverage"
- Comparison to covenant leverage limits

#### Step 3: SHAP Waterfall (Skill Step 3d)

**User Input**:
```
Show me the SHAP waterfall for Pinnacle. What are the top 5 features driving their PD score?
```

**What Happens**:
- `code_execution` runs SHAP analysis with `explain_with_shap`

**Expected Response**:
- SHAP feature table with impact and direction
- Base PD → Final PD attribution
- Key insight: which specific levers would reduce PD

### Scenario Wrap-up

**Business Impact Summary**:
- **Proactive Risk Management**: Sensitivity analysis before covenant breaches
- **Transparency**: SHAP explanations satisfy credit committee governance
- **Speed**: What-if scenarios that took a data science sprint now take minutes

**Technical Differentiators**:
- **Skill-Driven**: `credit-risk-calculator` skill with STOPPING POINT and 4 branches
- **Code Execution**: PD model recalculation with modified inputs in real-time
- **SHAP Explainability**: Model-agnostic feature importance computed on demand
- **Cross-Skill**: References `covenant-monitoring` and `rate-sensitivity-analysis` for holistic view
