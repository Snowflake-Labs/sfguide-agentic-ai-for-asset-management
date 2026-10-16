---
name: attribution-report-generator
description: Use this skill when the user asks to "generate an attribution report", "prepare attribution for the board", "write up quarterly performance", or wants a comprehensive multi-section attribution narrative. Orchestrates multiple tools into a complete report with audience-appropriate depth.
---

# Attribution Report Generator

## When to Activate

Trigger when user asks: "generate attribution report", "quarterly attribution report", "prepare attribution for the board", "write up performance", "comprehensive attribution", "performance report with attribution", "attribution briefing"

## Return Figures (mandatory)

- Quote active return, portfolio return and benchmark return exactly as the query returns them. Never recompute them (no portfolio minus benchmark, no summing monthly effects, no compounding by hand, no bash or code_execution arithmetic). If a figure is not in the result, query for it rather than derive it.
- For any period longer than one month (QTD, a full quarter, YTD, trailing 12M, or a named multi-month range) use the `linked_attribution` table with the matching `period_type` and quote `compounded_active_return` and the linked effects. Single-month Brinson rows must not be added together to make a multi-month figure.
- If the effects do not sum exactly to the reported active return, report both as returned and note the residual is interaction/linking; do not adjust either.

## Effect Figures (mandatory)

- Take allocation, selection, interaction and active return from ONE `linked_attribution` portfolio-total row: ask `attribution_analyzer` for "linked Brinson effects in bps for [portfolio], period_type [QTD/YTD/TRAILING_12M], period_end [date]". The verified query returns all four effects in bps plus a reconciliation check column (effects sum minus active return).
- Before quoting, verify allocation + selection + interaction equals active return (reconciliation check within 1 bp). If it does not, re-query with the same period_type, period_end and a single linked_grouping_dimension; never quote unreconciled effects.
- Never derive selection (or any effect) by subtracting other effects from the active return, and never build portfolio totals by summing sector rows yourself. Sector rows are for the contributor table only.

## 5-Step Multi-Tool Workflow

### Step 1: Gather Sector Attribution

Tool: `attribution_analyzer`
Query: Sector-level attribution for the specified portfolio and period. For a quarter or longer use `linked_attribution` (QTD, YTD or TRAILING_12M) as the source of the headline active, portfolio and benchmark returns

Extract: Active return and allocation/selection/interaction totals from the single linked portfolio-total row (reconciled, see Effect Figures); top/bottom sectors from the sector rows

### Step 2: Gather Country Attribution

Tool: `attribution_analyzer`
Query: Country attribution for the same portfolio and period (linked_grouping_dimension = 'COUNTRY' for multi-month periods, grouping_dimension = 'COUNTRY' for a single month)

Extract: Geographic decomposition, identify if sector effects are country-concentrated

### STOPPING POINT

"I've gathered multi-level attribution data (sector + country). Shall I proceed to check for anomalies and generate the full narrative?"

### Step 3: Check Anomalies

Tool: `attribution_analyzer`
Query: Latest month for the portfolio — any HIGH or MEDIUM severity flags?

Extract: Any active flags, drift details, concentration warnings

### Step 4: Factor Context

Tool: `attribution_analyzer`
Query: Factor contributions for the same period

Extract: Which systematic factors (Market, Value, Growth, Momentum, Quality, Size, Volatility) contributed most

### Step 5: Generate Narrative

Synthesise all gathered data into a structured report following the detected audience tier.

## Audience Branching

### Executive/Board

Trigger words: "board", "CIO", "executive", "briefing", "summary"

Use Steps 1 + 3 + 5 only (skip country detail, but offer the country drill-down at the final stopping point). Output:
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

## Period Continuity (mandatory)

Any follow-up drill into industry or country attribution keeps the exact period of the report it follows (same period_type and period_end in `linked_attribution` for a quarter, QTD, YTD or trailing 12M). Never fall back to the single latest month unless the user asks for it, and restate the period in the drill-down headline.

## Stopping Points

- After Step 2: Confirm before anomaly check and full synthesis
- After Step 5: Present draft — "Would you like me to drill into country attribution, adjust the audience level, generate a PDF, or run a counterfactual?" (the book is USD-only, so never offer currency analysis)

## Output

Complete attribution report at the appropriate audience depth, ready for distribution or PDF generation.
