---
name: historical-backtest
description: Use this skill when the user asks to "backtest" a portfolio, test historical performance of a portfolio allocation, or run a "historical simulation". Also use when comparing two portfolio candidates over a historical period, or when the user provides weights like "60/40 AAPL/MSFT" and wants to see how it would have performed.
---

# Historical Backtest

## When to Activate

Trigger when user asks: "backtest this portfolio", "historical performance of 60/40 AAPL/MSFT", "test portfolio over 3 years", "run a backtest"

## Workflow

### Step 1: Parse Portfolio Weights

Extract weights from natural language:
- "60% AAPL, 40% MSFT" -> {"AAPL": 0.60, "MSFT": 0.40}
- "Equal weight tech stocks" -> equal split across mentioned tickers
- "60/40 equity/bond split" -> map to appropriate tickers/ETFs
- Validate: weights must sum to 1.0, no negative weights

### Step 2: Determine Parameters

| Parameter | Default | User Override |
|-----------|---------|--------------|
| Benchmark | S&P 500 (SPY) | User-specified |
| Date range | 3 years | "over 5 years", "since 2020" |
| Rebalance frequency | Monthly | "quarterly", "annual" |
| Initial investment | $1,000,000 | User-specified |

### Step 3: Execute Backtest

Tool: `run_backtest`

Pass parsed weights, benchmark, date range, and rebalance frequency.

### Step 4: Present Results

**Summary Metrics**:
| Metric | Portfolio | Benchmark | Difference |
|--------|-----------|-----------|-----------|
| Cumulative Return | | | |
| Annualised Return | | | |
| Annualised Volatility | | | |
| Sharpe Ratio | | | |
| Max Drawdown | | | |
| Calmar Ratio | | | |

Use `data_to_chart` for:
- Cumulative return chart (portfolio vs benchmark)
- Rolling 12-month return
- Drawdown chart

## IPS Comparison Workflow

If comparing two candidates (e.g., for IPS compliance):
1. Backtest Candidate A
2. Backtest Candidate B
3. Present side-by-side comparison table
4. Follow with Monte Carlo for forward-looking validation

## Stopping Points

- After Step 1 (weights parsed): confirm portfolio composition and parameters with user before running backtest
- After Step 3 (results presented): pause for user questions before proceeding to IPS comparison or Monte Carlo

## Output

A backtest summary table with key metrics (annualised return, volatility, Sharpe, max drawdown, VaR, CVaR) plus methodology note.
