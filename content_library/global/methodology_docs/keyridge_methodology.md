---
doc_type: methodology_docs
linkage_level: global
variant_id: keyridge_bootstrapping_methodology
word_count_target: 1500
placeholders:
  required: []
---

# Portfolio Simulation Methodology: Historical Block Bootstrapping

**Document Type**: Quantitative Methodology  
**Topic**: Monte Carlo Simulation Framework  
**Effective Date**: January 2024  
**Classification**: Internal - Quant Research

---

## Executive Summary

This document describes the historical block bootstrapping methodology used in our portfolio simulation framework. Unlike parametric Monte Carlo methods that assume normally distributed returns, our approach samples directly from historical data whilst preserving the statistical properties essential for realistic risk assessment.

The methodology enables investors to project future portfolio outcomes whilst capturing fat tails, volatility clustering, and cross-asset correlations observed in actual market data.

---

## Theoretical Foundation

### Why Block Bootstrapping?

Traditional Monte Carlo simulation assumes returns are independent and identically distributed (IID), often drawn from a normal distribution. This assumption fails to capture several critical features of financial markets:

**Fat Tails (Excess Kurtosis)**: Extreme returns occur more frequently than a normal distribution predicts. The October 1987 crash, 2008 financial crisis, and March 2020 COVID selloff all represented tail events with magnitudes that normal distributions assign near-zero probability.

**Volatility Clustering**: Large returns tend to follow large returns, and small returns follow small returns. This autoregressive conditional heteroskedasticity (ARCH) effect means volatility persistence matters for risk assessment.

**Serial Correlation**: Momentum effects create short-term return persistence that IID sampling ignores.

Block bootstrapping addresses these limitations by:

1. Sampling contiguous blocks of historical returns rather than individual days
2. Preserving within-block autocorrelation and volatility structure
3. Maintaining the empirical distribution's higher moments (skewness, kurtosis)

---

## Methodology Details

### Step 1: Historical Return Preparation

We collect historical daily returns for all assets in the portfolio universe. Returns are calculated as:

**Simple Return**: r_t = (P_t - P_{t-1}) / P_{t-1}

For multi-period aggregation in backtesting, we use log returns:

**Log Return**: ln(1 + r_t) = ln(P_t / P_{t-1})

Log returns are additive across time, simplifying cumulative return calculations.

### Step 2: De-meaning the Return Series

Before bootstrapping, we de-mean historical returns to separate:
- **Signal**: Forward-looking expected returns (provided by investment committee)
- **Noise**: Historical volatility structure (preserved from data)

Residual returns: ε_t = r_t - μ_historical

This separation allows us to combine historical volatility patterns with current forward expectations.

### Step 3: Block Selection

We use stationary block bootstrapping with an average block length of 21 trading days (approximately one month). The block length balances:

- **Preserving volatility clustering**: Longer blocks maintain more autocorrelation
- **Sample diversity**: Shorter blocks provide more unique starting points

Blocks are sampled with replacement from the full historical period (minimum 5 years, approximately 1,260 trading days).

### Step 4: Path Construction

For each simulation path:

1. Randomly select a block starting point
2. Extract the next k residual returns (k = block length)
3. Add forward-looking expected return to each residual
4. Apply to portfolio value: V_{t+1} = V_t × (1 + E[r] + ε_t)
5. Repeat until horizon reached

For a 10-year horizon with 252 trading days per year, each path comprises 2,520 daily returns.

### Step 5: Cash Flow Integration

The simulation incorporates:
- **Contributions**: Added at specified intervals (monthly)
- **Withdrawals**: Subtracted at specified intervals
- **Inflation adjustment**: Optional indexing of withdrawal amounts

---

## Key Parameters

### Simulation Count

We default to 10,000 simulation paths. This provides:
- Stable percentile estimates (< 1% sampling error at 5th/95th percentiles)
- Computational efficiency (< 5 seconds on standard hardware)
- Sufficient resolution for probability calculations

### Block Length

Default: 21 trading days

Research suggests block lengths between 20-60 days effectively preserve volatility clustering in equity returns. Shorter blocks suit less persistent markets; longer blocks suit highly autocorrelated series.

### Lookback Period

Default: 5 years (1,260 trading days)

Minimum: 2 years (required for stable covariance estimation)

Longer lookback periods capture more regimes but may include stale data. Rolling windows can address regime changes.

---

## Output Interpretation

### Fan Chart Visualisation

The simulation produces percentile bands over time:
- **5th percentile**: Worst 1-in-20 outcome (downside planning)
- **25th percentile**: Below-average outcome
- **50th percentile (median)**: Central tendency
- **75th percentile**: Above-average outcome
- **95th percentile**: Best 1-in-20 outcome

The widening fan represents increasing uncertainty at longer horizons.

### Probability Metrics

**Probability of Loss**: P(Terminal Value < Initial Value)
This answers: "What is the chance I end up with less than I started?"

**Shortfall Risk**: P(Terminal Value < Target)
For goal-based investing, this answers: "What is the chance I fail to meet my objective?"

**Probability of Doubling**: P(Terminal Value ≥ 2 × Initial)
This answers: "What is the chance I double my money?"

---

## Limitations and Considerations

### Historical Data Dependence

The simulation assumes future return distributions resemble historical patterns. Structural market changes, regulatory shifts, or unprecedented events may produce outcomes outside historical experience.

### Parameter Sensitivity

Results depend on:
- Expected return assumptions (forward-looking, subject to estimation error)
- Covariance stability (historical correlations may not persist)
- Block length selection (affects volatility persistence capture)

### Non-Stationary Markets

Regime changes (e.g., interest rate environments, volatility regimes) can cause historical sampling to over- or under-weight certain market conditions. Rolling windows and regime-aware sampling can mitigate this limitation.

---

## References

1. Politis, D.N. and Romano, J.P. (1994). "The Stationary Bootstrap." Journal of the American Statistical Association.
2. Efron, B. and Tibshirani, R. (1993). "An Introduction to the Bootstrap."
3. CFA Institute (2024). "Portfolio Management" Level I Curriculum.

---

**Document Control**  
Version: 2.1  
Last Updated: January 2024  
Author: Quantitative Research Team
