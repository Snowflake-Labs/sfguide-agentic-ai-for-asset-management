---
name: portfolio-optimizer
description: Use this skill when the user wants to optimize portfolio weights, find the efficient frontier, construct a maximum Sharpe or minimum variance portfolio, or rebalance with specific constraints like position caps, sector limits, or ESG minimums. Also use when the user says "what's the optimal allocation" or "rebalance for minimum risk".
---

# Portfolio Optimizer

## When to Activate

Trigger when user asks: "optimize my portfolio", "maximum Sharpe portfolio", "efficient frontier", "optimal allocation with 5% position cap", "rebalance for minimum variance"

## Workflow

### Step 1: Get Input Data

Tool: `quantitative_analyzer` or `portfolio_modelling_analyzer`

Retrieve:
- Expected returns (from factor model or historical)
- Covariance matrix (from historical returns)
- Current weights (if rebalancing)

### Step 2: Parse Constraints

Extract from user request:
- Position limits: "max 5% per stock" -> bounds = (0, 0.05)
- Sector caps: "max 30% in tech" -> linear constraint
- ESG minimum: "minimum BBB average" -> ESG score constraint
- Budget: weights must sum to 1.0
- Long-only: no short selling (bounds >= 0)

### Step 3: Run Optimization via Code Execution

Tool: `code_execution`

You MUST use ONLY the code from `optimize.py`. Copy the relevant function(s) into the code_execution tool and call them with the data from Step 1. Do NOT write custom optimization code, do NOT import libraries other than numpy, and do NOT attempt alternative approaches. If the code fails or the function does not exist for the user's request, STOP and inform the user that this optimization objective is not supported.

Convert expected returns and covariance from Step 1 into numpy arrays, apply constraints from Step 2 as bounds, then call the appropriate function:

| User Intent | Function |
|-------------|----------|
| Maximum Sharpe / best risk-adjusted | `optimize_max_sharpe(expected_returns, cov_matrix, bounds)` |
| Minimum variance / lowest risk | `optimize_min_variance(cov_matrix, bounds)` |
| Risk parity / equal risk contribution | `optimize_risk_parity(cov_matrix, bounds)` |
| Target a specific return level | `optimize_target_return(expected_returns, cov_matrix, target_return, bounds)` |
| Compare risk-return tradeoffs | `efficient_frontier(expected_returns, cov_matrix, n_points)` |

If the user requests an objective not in this table, inform them it is not currently supported.

### Step 4: Present Results

**Optimal Weights**:
| Security | Current Weight | Optimal Weight | Change | Sector |
|----------|---------------|---------------|--------|--------|
| [Ticker] | X.X% | X.X% | +/-X.X% | [Sector] |

**Portfolio Metrics**:
| Metric | Current | Optimal | Improvement |
|--------|---------|---------|------------|
| Expected Return | X.X% | X.X% | +X.Xbps |
| Volatility | X.X% | X.X% | -X.Xbps |
| Sharpe Ratio | X.XX | X.XX | +X.XX |
| Max Position | X.X% | X.X% | |

Use `data_to_chart` for efficient frontier visualization.

## Stopping Points

- After Step 2 (constraints parsed): confirm constraints and objective with user before running optimisation
- After Step 4 (results presented): pause for user to review weights and request adjustments

## Output

Optimal weights table with current vs optimal comparison, portfolio metrics improvement summary, and efficient frontier chart.
