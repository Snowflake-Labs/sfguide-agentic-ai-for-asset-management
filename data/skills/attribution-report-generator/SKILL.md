---
name: attribution-report-generator
description: Use this skill when the user asks to "generate an attribution report", "prepare attribution for the board", "write up quarterly performance", or wants a comprehensive multi-section attribution narrative. Orchestrates multiple tools into a complete report with audience-appropriate depth.
---

# Attribution Report Generator

## When to Activate

Trigger when user asks: "generate attribution report", "quarterly attribution report", "prepare attribution for the board", "write up performance", "comprehensive attribution", "performance report with attribution", "attribution briefing"

## 5-Step Multi-Tool Workflow

### Step 1: Gather Sector Attribution

Tool: `brinson_analyzer`
Query: Sector-level attribution + linked QTD/YTD for the specified portfolio and period

Extract: Active return, allocation/selection/interaction totals, top/bottom sectors

### Step 2: Gather Country Attribution

Tool: `brinson_analyzer`
Query: grouping_dimension = 'COUNTRY' for same portfolio and period

Extract: Geographic decomposition, identify if sector effects are country-concentrated

### STOPPING POINT

"I've gathered multi-level attribution data (sector + country). Shall I proceed to check for anomalies and generate the full narrative?"

### Step 3: Check Anomalies

Tool: `anomaly_detector`
Query: Latest month for the portfolio — any HIGH or MEDIUM severity flags?

Extract: Any active flags, drift details, concentration warnings

### Step 4: Factor Context

Tool: `factor_analyzer`
Query: Factor contributions for the same period

Extract: Which systematic factors (Market, Value, Growth, Momentum, Quality, Size, Volatility) contributed most

### Step 5: Generate Narrative

Synthesise all gathered data into a structured report following the detected audience tier.

## Audience Branching

### Executive/Board

Trigger words: "board", "CIO", "executive", "briefing", "summary"

Use Steps 1 + 3 + 5 only (skip country detail). Output:
```
## [Portfolio] — [Period] Attribution Summary

[1-sentence headline: outperformed/underperformed by X]

**Key Drivers**:
- [Top driver with magnitude]
- [Second driver]
- [Third driver]

**Risk Flags**: [Any HIGH severity items, or "No critical flags"]
```

### PM/Analyst

Trigger words: "PM", "detailed", "deep dive", "full analysis"

Use all 5 steps. Output: Full tables for sector + country, factor contribution breakdown, anomaly flags with detail, true alpha assessment.

### Client/Investor

Trigger words: "client", "prospect", "investor", "plain English"

Use Steps 1 + 5. Output:
```
Your portfolio [gained/lost] [X]% this [period], [ahead of/behind] the benchmark by [Y]%.

The key contributors to performance were:
- [Plain language explanation of top driver]
- [Plain language explanation of second driver]

Looking ahead, [1-sentence outlook based on current positioning].
```

## Stopping Points

- After Step 2: Confirm before anomaly check and full synthesis
- After Step 5: Present draft — "Would you like me to adjust the audience level, add currency analysis, generate a PDF, or run a counterfactual?"

## Output

Complete attribution report at the appropriate audience depth, ready for distribution or PDF generation.
