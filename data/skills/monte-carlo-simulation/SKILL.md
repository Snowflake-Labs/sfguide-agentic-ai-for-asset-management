---
name: monte-carlo-simulation
description: Use this skill when the user asks for a "Monte Carlo" simulation, wants to know the probability of reaching a financial target, or needs forward-looking risk analysis. Also use for retirement planning questions, DCA analysis, or any query about probabilistic portfolio outcomes like "what are the odds of reaching $2M" or "how risky is this allocation".
---

# Monte Carlo Simulation

## When to Activate

Trigger when user asks: "run Monte Carlo", "probability of reaching $X", "forward-looking risk", "simulation for retirement", "what are the odds of..."

## Workflow

### Step 1: Parse Parameters

| Parameter | Default | User Override |
|-----------|---------|--------------|
| Number of paths | 10,000 | "run 50,000 simulations" |
| Horizon | 5 years (or from IPS) | "10-year horizon" |
| Initial value | From portfolio or $1M | User-specified |
| Target value | None | "reaching $2M" |
| Contributions | None (lump sum) | "adding $5,000/month" |
| Confidence level | 95% | "99% VaR" |

### Step 2: Execute Simulation

Tool: `run_monte_carlo`

Pass portfolio weights, horizon, paths, and optional DCA parameters.

### Step 3: Present Results

**Probabilistic Outcomes**:
| Percentile | Ending Value | Annualised Return |
|-----------|-------------|------------------|
| 5th (worst case) | $X | X.X% |
| 25th | $X | X.X% |
| 50th (median) | $X | X.X% |
| 75th | $X | X.X% |
| 95th (best case) | $X | X.X% |

**Risk Metrics**:
- Value at Risk (95%): $X loss over [horizon]
- Probability of loss: X%
- Probability of reaching target: X% (if target specified)
- Expected shortfall (CVaR 95%): $X

Use `data_to_chart` for:
- Distribution of ending values (histogram)
- Fan chart showing percentile bands over time

## DCA (Dollar Cost Averaging) Support

When user specifies regular contributions:
- Model monthly/quarterly additions at specified amounts
- Show how DCA reduces sequence-of-returns risk
- Compare to lump-sum scenario if helpful

## Stopping Points

- After Step 1 (parameters confirmed): verify portfolio, horizon, and any DCA settings with user before running simulation
- After Step 3 (results presented): pause for user questions or parameter adjustments

## Output

Terminal value distribution table (5th/25th/50th/75th/95th percentiles), probability metrics (loss, double, triple), and methodology note.
