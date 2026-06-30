---
name: portfolio-construction
description: Use this skill when the user asks to "build a portfolio", "construct an allocation", "create a proposal", or requests a portfolio with specific constraints (max volatility, minimum fixed income, target return, goal probability). Also use for "conservative portfolio", "aggressive growth portfolio", "balanced allocation", "60/40 split", or any request that requires selecting securities and assigning weights from scratch.
---

# Portfolio Construction

## CRITICAL: Investable Universe Constraint

**You MUST ONLY use tickers that exist in SAM_DEMO.CURATED.DIM_SECURITY.**

NEVER use ETF tickers (SPY, AGG, TLT, QQQ, VTI, IWM, GLD, etc.) or any ticker from your general training knowledge unless you have FIRST verified it exists in our database by querying the portfolio_modelling_analyzer tool.

Our universe is **equity-only** (~500 securities). If the user requests asset classes not in our universe:
- **Bonds / Fixed Income**: We do not have bond securities. Suggest lower-volatility equity sectors as proxies: Utilities (XLU sector stocks), Consumer Staples, Healthcare, REITs. Explain the limitation transparently.
- **ETFs**: We do not have ETF data. Use the underlying equity constituents instead.
- **Commodities / Gold**: Not available. Suggest defensive equity positions as alternatives.

Always be transparent: "Our investable universe consists of ~500 US equities. I'll construct this from our available securities."

## When to Activate

Trigger when user asks:
- "Build me a conservative portfolio"
- "Create a portfolio with max 12% volatility"
- "Construct a balanced allocation"
- "Generate a portfolio proposal"
- "60/40 equity split" (interpret as 60% growth / 40% defensive equities)
- "What allocation gives me 80% goal probability?"
- Any request combining security selection + weight assignment + constraints

## Workflow

### Step 1: Query Available Universe

Tool: `portfolio_modelling_analyzer`

Query: "Show me available model portfolios with their strategy type and weights"

This gives you the starting templates from DIM_MODEL_PORTFOLIO:
- **60/40 Classic** (Balanced) — lower risk
- **Low Volatility** (Defensive) — minimum risk
- **ESG Leaders** (ESG) — sustainability focus
- **Equal Weight Demo** (Core) — diversified
- **80/20 Growth** (Growth) — higher return
- **Tech Leaders** (Growth) — concentrated growth

### Step 2: Map User Constraints to a Starting Template

| User Request | Starting Template | Modification |
|---|---|---|
| Conservative / low risk / max 12% vol | Low Volatility or 60/40 Classic | Increase defensive sector weight |
| Balanced / moderate | 60/40 Classic | Standard weights |
| Aggressive / growth / max return | 80/20 Growth or Tech Leaders | Increase growth exposure |
| ESG / sustainable | ESG Leaders | Focus on high-ESG securities |
| Custom constraints | Closest template | Apply specific constraints |

### Step 3: Retrieve Template Weights

Tool: `portfolio_modelling_analyzer`

Query: "Show the ticker weights for the [selected model] portfolio"

This returns actual tickers and weights from FACT_MODEL_PORTFOLIO_WEIGHTS. These are verified to be in our universe.

### Step 4: Apply User Constraints

Adjust the template weights based on user requirements:

| Constraint | Action |
|---|---|
| Max volatility X% | Shift weight toward low-beta sectors (Utilities, Staples, Healthcare) |
| Min "fixed income" Y% | Interpret as Y% in defensive/low-vol equities; explain bond proxy approach |
| Max single position Z% | Cap any ticker at Z%, redistribute excess equally |
| Sector caps | Reduce overweight sectors, add to underweight |
| ESG minimum | Remove lowest-ESG tickers, replace with higher-rated alternatives from same sector |
| Target return X% | Adjust growth vs defensive split to target the return level |

Present the proposed portfolio BEFORE running tools:
- Show ticker, sector, weight, rationale for each position
- Confirm total weights sum to 100%
- Note any constraint trade-offs

### Step 5: Run Historical Backtest

Tool: `run_backtest`

Parameters:
- Portfolio weights (from Step 4)
- Start date: 5 years ago (default) or user-specified
- End date: yesterday
- Rebalance: quarterly (default)

Present results: Return, Volatility, Sharpe, Max Drawdown, Calmar Ratio

### Step 6: Run Monte Carlo Simulation

Tool: `run_monte_carlo`

Parameters:
- Same portfolio weights
- Horizon: from user (default 10 years)
- Initial investment: from user (default $1,000,000)
- Simulations: 10,000

Present results:
- Median outcome
- 5th percentile (downside)
- 95th percentile (upside)
- Probability of reaching goal (if specified)
- Probability of loss

### Step 7: Present Complete Proposal

Format as a structured proposal:

**Portfolio Proposal: [Name based on strategy]**

| # | Ticker | Company | Sector | Weight | Rationale |
|---|--------|---------|--------|--------|-----------|
| 1 | AAPL | Apple Inc | Technology | 8.0% | Core large-cap, low beta for tech |
| ... | | | | | |

**Constraint Compliance:**
| Constraint | Target | Achieved | Status |
|---|---|---|---|
| Max Volatility | 12% | 11.3% | PASS |
| Min Defensive | 40% | 42% | PASS |
| Max Single Position | 10% | 8% | PASS |

**Historical Performance (5Y Backtest):**
| Metric | Value |
|---|---|
| Annualised Return | X.X% |
| Volatility | X.X% |
| Sharpe Ratio | X.XX |
| Max Drawdown | -X.X% |

**Forward Projection (10Y Monte Carlo):**
| Outcome | Value |
|---|---|
| Median | $X.XM |
| 5th Percentile | $X.XM |
| P(Goal) | XX% |
| P(Loss) | XX% |

## Stopping Points

- After Step 4 (weights proposed): Confirm proposed allocation with user before running backtest/MC
- After Step 7 (full proposal): Pause for user to review, adjust, or approve

## Error Handling

- If a user-provided ticker is NOT in DIM_SECURITY: Inform them and suggest an alternative from the same sector
- If constraints are impossible (e.g., max 5% vol with 100% equities): Explain the trade-off and propose the closest achievable portfolio
- If backtest returns unexpected results: Note the limitations and suggest the user check with different parameters

## Output

A complete portfolio construction proposal with:
1. Security selection rationale (all from verified universe)
2. Weight allocation with constraint compliance table
3. Historical validation (backtest metrics)
4. Forward validation (Monte Carlo probabilities)
5. Clear next steps (approve, modify, or reject)
