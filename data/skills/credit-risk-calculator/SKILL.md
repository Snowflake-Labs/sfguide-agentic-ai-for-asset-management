---
name: credit-risk-calculator
description: Use this skill when the user asks about a borrower's default probability, credit risk drivers, PD scores, risk ratings, or wants to run what-if scenarios on credit metrics like "what if revenue drops 20%" or "recalculate PD with adjusted inputs". Also use when explaining why a borrower received a particular risk rating, SHAP analysis, or comparing risk across borrowers.
---

# Credit Risk Calculator

## When to Activate

Trigger when user asks: "what's the default probability for [borrower]?", "what if revenue drops 20%?", "recalculate PD with adjusted inputs", "explain the credit risk drivers", "SHAP waterfall", "risk score", "PD sensitivity", "which borrowers are highest risk", "what drives the risk rating"

## Workflow

### Step 1: Get Current Features

Tool: `credit_risk_analyzer` or `credit_portfolio_analyzer`

Query: "Current credit features for borrower [name]"

Extract: All model input features (financial ratios, covenant metrics, ESG scores, macro indicators)

### Step 2: Present Baseline Profile

Present:
- Headline: "[Borrower] PD: [X.X]% ([RISK_RATING]), [trend] from prior quarter"
- Feature summary table:

| Feature | Value | Portfolio Avg | vs Avg |
|---------|-------|--------------|--------|
| Leverage | [X]x | [Y]x | [Above/Below] |
| EBITDA Margin | [X]% | [Y]% | [Above/Below] |
| Interest Coverage | [X]x | [Y]x | [Above/Below] |
| Revenue Growth | [X]% | [Y]% | [Above/Below] |

### STOPPING POINT

Present the baseline, then offer:
"I've pulled [Borrower]'s current risk profile. I can:
- **Run baseline PD calculation** (recalculate probability of default from current features)
- **Model a stress scenario** (specify revenue drop, leverage increase, rate rise, or covenant breach)
- **Compare multiple scenarios side by side** (e.g., +0.5x / +1.0x / +1.5x leverage)
- **Explain key risk drivers** (SHAP waterfall showing exactly what drives the PD score)

Which would be most useful?"

### Step 3a: Baseline PD Calculation (if user chooses)

Tool: `code_execution`

You MUST use ONLY the code from `pd_model.py`. Copy the relevant function(s) into the code_execution tool and call them with the data from Step 1. Do NOT write custom scoring code, do NOT import libraries other than numpy and pandas, and do NOT attempt alternative approaches.

Convert borrower features from Step 1 into a pandas DataFrame, then call `predict_pd(model, features)`.

Present:
- **PD Score**: X.X% (Risk Rating: [LOW_RISK / MODERATE / ELEVATED / HIGH_RISK])
- Comparison to prior quarter PD

### Step 3b: Stress Scenario (if user specifies a what-if)

Apply user scenario adjustments:
- "Revenue drops 20%" → adjust REVENUE and derived ratios
- "Interest rates rise 200bps" → adjust INTEREST_COVERAGE, DSCR
- "Leverage increases 1x" → adjust LEVERAGE_RATIO
- "Covenant breach" → set BREACH_COUNT += 1, adjust headroom

Tool: `code_execution` with `apply_scenario(features, adjustments)` then `predict_pd`

Present:
| Metric | Current | Scenario | Change |
|--------|---------|----------|--------|
| PD Score | X.X% | Y.Y% | +Z.Z% |
| Risk Rating | [Current] | [New] | [Upgrade/Downgrade] |

### Step 3c: Multi-Scenario Comparison (if user chooses)

Run multiple scenarios side by side using `code_execution`:

| Scenario | Leverage | PD Score | Risk Rating | Change |
|----------|----------|----------|-------------|--------|
| Current | X.Xx | X.X% | [Rating] | — |
| +0.5x | X.Xx | X.X% | [Rating] | +X.X% |
| +1.0x | X.Xx | X.X% | [Rating] | +X.X% |
| +1.5x | X.Xx | X.X% | [Rating] | +X.X% |

Include: "Threshold analysis: [Borrower] crosses into HIGH_RISK at [X.X]x leverage"

### Step 3d: SHAP Waterfall (if user chooses risk drivers)

Tool: `code_execution` with `explain_with_shap(model, features, feature_names)`

Present:
| Feature | Value | SHAP Impact | Direction |
|---------|-------|-------------|-----------|
| [Feature] | X.XX | +X.XX | Increases risk |
| [Feature] | X.XX | -X.XX | Decreases risk |

- Base PD: [X]% → Final PD: [Y]% after all feature contributions
- Key insight: "[Feature] is the single largest risk driver, contributing [X]% to PD"

## Rating Boundaries

| PD Range | Risk Rating |
|----------|------------|
| < 10% | LOW_RISK |
| 10-20% | MODERATE |
| 20-50% | ELEVATED |
| > 50% | HIGH_RISK |

## Audience-Specific Presentation

- **Risk Committee**: Headline PD + rating + top 3 SHAP drivers (concise)
- **PM/Analyst**: Full SHAP waterfall + multi-scenario comparison + threshold analysis
- **Client/Investor**: Plain language — "This borrower's credit quality is [strong/adequate/under pressure] with key risks from [factor]"

## Output Template

```
## Credit Risk Assessment: [Borrower]

**PD Score**: [X.X]% | **Risk Rating**: [RATING] | **Trend**: [Direction]

### Key Risk Drivers (SHAP)
| Feature | Value | Impact | Direction |
|---------|-------|--------|-----------|
| [Top driver] | [Value] | [Impact] | [Direction] |

### Scenario Sensitivity
| Scenario | PD | Rating | Change |
|----------|-----|--------|--------|
| Current | [X]% | [Rating] | — |
| [Stress] | [Y]% | [Rating] | [Change] |
```

## Cross-Skill References

- For covenant status of the borrower → **covenant-monitoring** skill
- For rate sensitivity impact on coverage → **rate-sensitivity-analysis** skill
- For portfolio-wide risk overview → **credit-portfolio-review** skill

## Stopping Points

- After Step 2 (baseline profile): Offer 4 branching options
- After any Step 3 branch: "Would you like to run another scenario, or shall I compile the full risk assessment?"
