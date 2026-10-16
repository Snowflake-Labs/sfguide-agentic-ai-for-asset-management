---
name: credit-risk-calculator
description: Use this skill for ANY question about a single borrower's PD, e.g. "show me the current PD score and risk rating for [borrower]", "what is [borrower]'s probability of default", along with its key financials. Load it before calling pd_what_if, even for a plain lookup, so the stopping-point options are offered. Also use when the user asks about a borrower's default probability, credit risk drivers, PD scores, risk ratings, or wants to run what-if scenarios on credit metrics like "what if leverage rises 1.5x", "what if EBITDA falls 20%" or "recalculate PD with adjusted inputs". Also use when explaining why a borrower received a particular risk rating, SHAP analysis, or comparing risk across borrowers.
---

# Credit Risk Calculator

## When to Activate

Trigger when user asks: "what's the default probability for [borrower]?", "current PD score and risk rating for [borrower]", "PD for [borrower] with key financial metrics", "what if leverage rises 1x?", "recalculate PD with adjusted inputs", "explain the credit risk drivers", "SHAP waterfall", "risk score", "PD sensitivity", "which borrowers are highest risk", "what drives the risk rating", "how much headroom loss makes this HIGH_RISK"

## What the PD Means

PD is the model's probability that the borrower has a covenant breach, or covenant headroom below 5%, in the NEXT quarter. It comes from the `CREDIT_RISK_XGBOOST` model in the Snowflake Model Registry (PRODUCTION alias). State this definition the first time you quote a PD. Never estimate or calculate a PD yourself; every PD you quote must come from `credit_risk_analyzer` or `pd_what_if`.

## Workflow

### Step 1: Current Profile

- **One borrower**: call `pd_what_if` with the full borrower name and an empty `overrides` string. It returns the live PD, risk rating, the 15 input features and the top SHAP drivers.
- **Whole book / ranking / history**: use `credit_risk_analyzer` (stored scores for every borrower-quarter).

### Step 2: Present Baseline Profile

Present:
- Headline: "[Borrower] PD: [X.X]% ([RISK_RATING])" plus the prior-quarter PD from `credit_risk_analyzer` if a trend is useful
- Feature summary table built from the returned `features`:

| Feature | Value |
|---------|-------|
| Total leverage | [TOTALLEVERAGE]x |
| Interest coverage | [INTERESTCOVERAGE]x |
| EBITDA margin | [EBITDA_MARGIN]% |
| Minimum covenant headroom | [MIN_COVENANT_HEADROOM]% |
| Covenant breaches this quarter | [BREACH_COUNT] |

### STOPPING POINT

Always end the baseline answer with these options, even when the user only asked for the current PD. Present the baseline, then offer:
"I've pulled [Borrower]'s current risk profile from the production PD model. I can:
- **Model a stress scenario** (leverage increase, EBITDA or coverage decline, headroom erosion)
- **Compare multiple scenarios side by side** (e.g. +0.5x / +1.0x / +1.5x leverage)
- **Explain key risk drivers** (SHAP contributions behind the PD)
- **Find the tipping point** (how far a metric can move before the borrower becomes HIGH_RISK)

Which would be most useful?"

### Step 3a: Stress Scenario

Tool: `pd_what_if`, passing an overrides JSON object. Map the user's scenario to features:

| User scenario | Override |
|---------------|----------|
| "Leverage rises 1.5x" | TOTALLEVERAGE "+1.5" (and NETLEVERAGE "+1.5") |
| "EBITDA falls 20%" | EBITDA_MARGIN "-20%", TOTALLEVERAGE "+25%" (debt / 0.8 EBITDA), INTERESTCOVERAGE "-20%", FIXEDCHARGECOVERAGE "-20%" |
| "Rates rise 200bps" | INTERESTCOVERAGE and FIXEDCHARGECOVERAGE down by the interest-cost increase, e.g. "-15%" |
| "Headroom falls to 3%" | MIN_COVENANT_HEADROOM 3 |
| "Covenant breach" | BREACH_COUNT "+1" and MIN_COVENANT_HEADROOM below 0 |

Values are absolute (6.5), additive as signed strings ("+1.5") or relative ("-20%"). Say which overrides you used.

Shocks to TOTALLEVERAGE, INTERESTCOVERAGE and FIXEDCHARGECOVERAGE are propagated by the tool to the matching covenant's tested value and headroom. Report `covenant_propagation`: which covenant moved, its headroom before and after, and whether it would breach. Overriding headroom or BREACH_COUNT directly switches propagation off.

Present:
| Metric | Current | Scenario | Change |
|--------|---------|----------|--------|
| PD | X.X% | Y.Y% | +Z.Z pts |
| Risk rating | [Current] | [New] | [Upgrade/Downgrade] |
| Min covenant headroom | X.X% | Y.Y% | |

### Step 3b: Multi-Scenario Comparison

Call `pd_what_if` once per scenario and tabulate:

| Scenario | Leverage | Min headroom | PD | Risk rating |
|----------|----------|--------------|----|-------------|
| Current | X.Xx | X.X% | X.X% | [Rating] |
| +0.5x | X.Xx | X.X% | X.X% | [Rating] |
| +1.0x | X.Xx | X.X% | X.X% | [Rating] |
| +1.5x | X.Xx | X.X% | X.X% | [Rating] |

For a tipping point, step the metric and report the first step that reaches HIGH_RISK. Only report a threshold you actually scored.

### Step 3c: Risk Drivers (SHAP)

Use `top_drivers` from `pd_what_if` (baseline or stressed). SHAP values are in log-odds: positive increases default risk, negative reduces it.

| Feature | Value | SHAP | Direction |
|---------|-------|------|-----------|
| [Feature] | X.XX | +X.XX | Increases risk |
| [Feature] | X.XX | -X.XX | Decreases risk |

## Interpreting Results Honestly

- The model is trained on 15 borrowers and ~120 labelled quarters. Covenant headroom dominates it, so PD moves in steps rather than smoothly. Say so if a large financial shock produces little change because headroom stays comfortable.
- PDs near 0% or 100% mean the model is confident on this data, not that default is impossible or certain.

## Rating Boundaries

| PD Range | Risk Rating |
|----------|------------|
| < 10% | LOW_RISK |
| 10-20% | MODERATE |
| 20-50% | ELEVATED |
| > 50% | HIGH_RISK |

## Audience-Specific Presentation

- **Risk Committee**: Headline PD + rating + top 3 SHAP drivers (concise)
- **PM/Analyst**: Drivers + multi-scenario comparison + tipping point
- **Client/Investor**: Plain language — "This borrower's credit quality is [strong/adequate/under pressure] with key risks from [factor]"

## Output Template

```
## Credit Risk Assessment: [Borrower]

**PD**: [X.X]% | **Risk Rating**: [RATING] | Model: CREDIT_RISK_XGBOOST (PRODUCTION)

### Key Risk Drivers (SHAP)
| Feature | Value | Impact | Direction |
|---------|-------|--------|-----------|

### Scenario Sensitivity
| Scenario | PD | Rating | Min headroom |
|----------|-----|--------|--------------|
```

## Cross-Skill References

- For covenant status of the borrower → **covenant-monitoring** skill
- For rate sensitivity impact on coverage → **rate-sensitivity-analysis** skill
- For portfolio-wide risk overview → **credit-portfolio-review** skill

## Stopping Points

- After Step 2 (baseline profile): offer the 4 options
- After any Step 3 branch: "Would you like to run another scenario, or shall I compile the full risk assessment?"
