---
name: counterfactual-analysis
description: Use this skill when the user asks "what if", "what would have happened if", "counterfactual", "had we held benchmark weights", "exclude a sector", "cap weight at", or "compare sector vs country classification". Maps natural language what-if questions to the RUN_COUNTERFACTUAL_ANALYSIS procedure.
---

# Counterfactual Attribution Analysis

## When to Activate

Trigger when user asks: "what if", "what would have happened", "counterfactual", "benchmark weights", "exclude [sector]", "cap weight", "what if no sector exceeded", "compare sector vs country", "was active management worth it"

## Scenario Mapping

Map user intent to scenario_type parameter:

| User Language | Scenario Type | What It Does |
|---------------|--------------|--------------|
| "What if we held benchmark weights" | BENCHMARK_WEIGHTS | Sets all sector weights = benchmark (zero allocation effect) |
| "What if no sector exceeded 25%" | CAP_WEIGHT | Caps overweight sectors, redistributes pro-rata |
| "What if we excluded [sector]" | EXCLUDE_GROUP | Removes sector, redistributes weight |
| "Compare sector vs country attribution" | SWAP_CLASSIFICATION | Shows same data through different grouping lens |

## Workflow

### Step 1: Identify Parameters

- Portfolio: Resolve name (default: 'Flagship')
- Period: Parse start_date and end_date (default: last quarter — use most recent 3 months of attribution data)
- Scenario: Map user language to one of 4 types above
- For EXCLUDE_GROUP: identify the group to exclude from user's question

### Step 2: Run Counterfactual

Tool: `run_counterfactual`
Parameters: portfolio_name_or_id, start_date, end_date, scenario_type

### Step 3: Present Comparison

| Metric | Original | Counterfactual | Impact |
|--------|----------|---------------|--------|
| Active Return | [X]bps | [Y]bps | [+/-Z]bps |

Top 3 sectors most affected by the scenario change.

### Interpretation Guide

- BENCHMARK_WEIGHTS: If counterfactual is worse → active management added value. If better → allocation detracted.
- CAP_WEIGHT: Quantifies the cost/benefit of concentration limits.
- EXCLUDE_GROUP: Shows dependency on a single sector.
- SWAP_CLASSIFICATION: Reveals whether the attribution story changes under different classification.

### STOPPING POINT

"The counterfactual shows [summary]. Would you like to:
- Try a different scenario?
- See the full sector-by-sector breakdown?
- Run the standard attribution for comparison?"

## Output Template

```
## Counterfactual: [Scenario Description]

**Portfolio**: [Name] | **Period**: [dates]

| | Original | Counterfactual | Difference |
|---|----------|---------------|-----------|
| Active Return | [X]bps | [Y]bps | [+/-Z]bps |

### Interpretation
[Was active management worth it? Did the concentration help or hurt?]

### Most Affected Sectors
1. [Sector]: [original] → [counterfactual] ([+/-] impact)
2. ...
3. ...
```

## Stopping Points

- After Step 3: Offer alternative scenarios or deeper analysis
