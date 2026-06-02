---
name: attribution-anomaly-scan
description: Use this skill when the user asks about anomalies, risk flags, style drift, attribution drift, concentration alerts, or anything unusual in attribution patterns. Also use proactively when generating reports to check for HIGH severity items before presenting findings.
---

# Attribution Anomaly Scan

## When to Activate

Trigger when user asks: "anomalies", "risk flags", "attribution drift", "any alerts", "style drift", "concentration risk", "anything unusual", "scan portfolios", "risk scan", "what should I be concerned about"

## Detection Rules (9 total)

| Rule | What It Detects | Threshold |
|------|----------------|-----------|
| FACTOR_DRIFT_ALERT | Factor exposure >2sigma from trailing average | z-score > 2.0 |
| CONCENTRATION_ALERT | Single sector >60% of active return | share > 0.6 |
| SINGLE_FACTOR_DOMINANCE | One factor >70% of systematic return | share > 0.7 |
| STYLE_INCONSISTENCY | Strategy name vs actual exposure mismatch | Value fund with Growth tilt |
| ATTRIBUTION_SPIKE | Monthly return >2sigma from trailing | z-score > 2.0 |
| ALLOCATION_DRIFT_ALERT | Sector weight >2sigma from 6M rolling average | z-score > 2.0 |
| SELECTION_REVERSAL_ALERT | Selection effect flips sign vs trailing 3M | sign change + magnitude > 10bps |
| WEIGHT_CONCENTRATION_ALERT | Single sector >40% of portfolio weight | weight > 0.40 |
| CLASSIFICATION_SENSITIVITY_ALERT | Sector vs country attribution diverge significantly | divergence > 2% |

## Workflow

### Step 1: Scan All Portfolios

Tool: `anomaly_detector`
Query: Latest month, all portfolios, ordered by anomaly severity (HIGH first)

### Step 2: Present Findings

Format by severity:

**HIGH** (3+ flags): Full detail with specific flag names, affected sectors/factors, and magnitudes
**MEDIUM** (1-2 flags): Count + most significant flag
**LOW** (0 flags): Count only ("X portfolios have no anomalies")

### STOPPING POINT

"Found [N] HIGH severity items across [M] portfolios. I can:
- **Drill into a specific portfolio** to see what changed in its attribution
- **Show the drift timeline** for the most flagged portfolio
- **Run a stress test** on the flagged portfolio to assess forward risk

Which would be most useful?"

### Step 3a: Drill into Portfolio Attribution (if user chooses)

Tool: `brinson_analyzer`
Query: Recent 3-6 months for the flagged portfolio to show the attribution trend and when things changed

### Step 3b: Drift Timeline (if user chooses)

Tool: `brinson_analyzer` (rolling analytics via the view)
Query: Month-by-month exposure or weight history showing the drift building

### Step 3c: Stress Test (if user chooses)

Tool: `scenario_sensitivity` or `backtest_historical_stress`
Apply relevant stress scenario to the portfolio with drifted exposures

## Output Template

```
## Attribution Anomaly Scan — [Date]

### HIGH Severity ([N] portfolios)

| Portfolio | Flags | Key Detail |
|-----------|-------|-----------|
| [Name] | [Flag1], [Flag2], [Flag3] | [Most actionable detail] |

### MEDIUM Severity ([N] portfolios)
- [Portfolio]: [Primary flag] — [1-line summary]

### LOW Severity ([N] portfolios)
No action required.

### Recommended Actions
1. [Highest priority action for most severe item]
2. [Second priority]
```

## Stopping Points

- After Step 2: Offer drill-down options for flagged portfolios
- After Step 3: "Would you like to scan for a different date or run the full attribution report for this portfolio?"
