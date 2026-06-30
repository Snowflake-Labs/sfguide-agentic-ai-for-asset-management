---
name: factor-model-explorer
description: Use this skill when the user asks which factors are driving returns, wants to compare factor performance across periods, or requests ad-hoc factor exploration like "which factors are working this quarter", "compare momentum vs value", or "factor correlations". Also use when the user needs analysis beyond what pre-computed factor views provide.
---

# Factor Model Explorer

## When to Activate

Trigger when user asks: "which factors are driving returns?", "factor performance this quarter", "compare momentum vs value", "custom factor analysis", "factor correlations"

## Workflow

### Step 1: Retrieve Factor Data

Tool: `factor_model_analyzer` (Cortex Analyst)

Query: "Monthly factor returns for all factors" or "Factor exposures for [portfolio]"

### Step 2: Run Analysis via Code Execution

Tool: `code_execution`

You MUST use ONLY the code from `factor_analysis.py`. Copy the relevant function(s) into the code_execution tool and call them with the data from Step 1. Do NOT write custom analysis code, do NOT import libraries other than numpy and pandas, and do NOT attempt alternative approaches. If the code fails or the function does not exist for the user's request, STOP and inform the user that this analysis is not supported.

Convert the Cortex Analyst results from Step 1 into a pandas DataFrame, then call the appropriate function:

| User Intent | Function |
|-------------|----------|
| Factor predictiveness / signal quality | `compute_cross_sectional_ic(df, factor_cols, return_col)` |
| Factor overlap / redundancy check | `compute_factor_correlations(df, factor_cols)` |
| Factor momentum / trend | `compute_rolling_sharpe(df, factor_cols, window)` |
| Custom factor blend performance | `test_factor_combination(df, weights)` |

If the user requests an analysis not in this table, inform them it is not currently supported.

### Step 3: Present Results

Use `data_to_chart` for:
- Factor IC bar chart with significance stars
- Correlation heatmap
- Rolling Sharpe time series
- Factor return comparison chart

## Factors Available

12 standard factors: MOMENTUM, VALUE, QUALITY, GROWTH, SIZE, VOLATILITY, LEVERAGE, PROFITABILITY, EARNINGS_REVISION, DIVIDEND_YIELD, SENTIMENT, HIDDEN (AI_EXPOSURE, RESHORING, RATE_CONVEXITY, CLIMATE, GEOPOLITICAL)

## Analysis Templates

**"Which factors are working?"**: Run cross-sectional IC for the latest quarter, rank by absolute IC, flag factors with |IC| > 0.02 as "STRONG", 0.01-0.02 as "MODERATE", < 0.01 as "WEAK".

**"Factor regime analysis"**: Cross-reference factor returns with market regime (RISK_ON / TRANSITIONAL / RISK_OFF) to identify regime-dependent factors.

## Stopping Points

- After Step 1 (data retrieved): confirm factor set and time period with user before running analysis
- After Step 2 (analysis complete): present results for review before generating charts

## Output

Factor analysis results with IC scores, correlation matrices, rolling Sharpe ratios, or custom blend performance, visualised via `data_to_chart`.
