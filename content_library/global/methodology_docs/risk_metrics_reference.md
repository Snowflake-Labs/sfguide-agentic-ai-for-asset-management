---
doc_type: methodology_docs
linkage_level: global
variant_id: risk_metrics_reference_guide
word_count_target: 1400
placeholders:
  required: []
---

# Risk Metrics Reference Guide

**Document Type**: Quantitative Methodology  
**Topic**: Risk and Performance Measurement  
**Effective Date**: January 2024  
**Classification**: Internal - Risk Management

---

## Overview

This reference guide defines the risk and performance metrics used in our portfolio modelling and risk management systems. Understanding these metrics enables informed investment decisions and effective risk communication.

---

## Return-Based Metrics

### Annualised Return

The geometric average annual return, accounting for compounding:

Annualised Return = (1 + Total Return)^(1/n) - 1

Where n = number of years

This metric enables comparison across different holding periods. A portfolio with 50% total return over 3 years has an annualised return of approximately 14.5%.

### Sharpe Ratio

The risk-adjusted return measure developed by William Sharpe:

Sharpe Ratio = (R_p - R_f) / σ_p

Where:
- R_p = portfolio return (annualised)
- R_f = risk-free rate (annualised)
- σ_p = portfolio standard deviation (annualised)

**Interpretation**:
- Sharpe > 1.0: Good risk-adjusted performance
- Sharpe > 2.0: Excellent risk-adjusted performance
- Sharpe < 0: Underperforming risk-free rate

**Limitations**: Sharpe penalises upside volatility equally to downside volatility. For portfolios with positive skewness, this understates risk-adjusted value.

### Sortino Ratio

A modification of Sharpe that considers only downside risk:

Sortino Ratio = (R_p - MAR) / σ_downside

Where:
- MAR = Minimum Acceptable Return (often 0% or risk-free rate)
- σ_downside = Standard deviation of returns below MAR

**Interpretation**: Sortino addresses Sharpe's limitation by only penalising harmful volatility. A portfolio with high upside volatility but limited downside will have a higher Sortino than Sharpe.

**When to prefer Sortino**: 
- Evaluating strategies with asymmetric return distributions
- Goal-based investing where failing to meet a target is the primary concern
- Comparing strategies with different skewness profiles

---

## Drawdown Metrics

### Maximum Drawdown

The largest peak-to-trough decline during a period:

Maximum Drawdown = (Trough Value - Peak Value) / Peak Value

Expressed as a positive percentage (e.g., 25% maximum drawdown means the portfolio fell 25% from its high).

**Interpretation**: Maximum drawdown captures the worst-case loss experience, critical for:
- Assessing investor staying power requirements
- Understanding potential emotional impact on clients
- Regulatory stress testing

### Calmar Ratio

Return per unit of maximum drawdown:

Calmar Ratio = Annualised Return / Maximum Drawdown

**Interpretation**: Higher Calmar indicates more efficient generation of returns relative to the largest loss experienced. Unlike Sharpe, Calmar focuses on tail risk rather than volatility.

**Typical values**:
- Calmar > 1.0: Return exceeds worst drawdown
- Calmar > 2.0: Strong risk-adjusted performance
- Calmar < 0.5: Concerning risk-return profile

---

## Tail Risk Metrics

### Value at Risk (VaR)

The loss threshold exceeded with a specified probability:

VaR(α) = -Percentile(Returns, 1-α)

For 95% VaR (α = 0.95), we calculate the 5th percentile of returns.

**Interpretation**: "With 95% confidence, daily losses will not exceed X%."

**Methods**:
- **Historical VaR**: Percentile of actual historical returns
- **Parametric VaR**: Assumes normal distribution (less accurate for fat tails)
- **Monte Carlo VaR**: Simulated distribution percentile

We use Historical VaR for its simplicity and accuracy in capturing fat tails.

### Conditional VaR (CVaR / Expected Shortfall)

The expected loss given that the loss exceeds VaR:

CVaR(α) = E[Loss | Loss > VaR(α)]

CVaR averages all losses beyond the VaR threshold, providing a more complete picture of tail risk.

**Interpretation**: "When losses exceed VaR, the average loss is Y%."

**Advantages over VaR**:
- **Coherent risk measure**: Satisfies subadditivity (diversification reduces risk)
- **Captures tail magnitude**: VaR only identifies the threshold; CVaR measures what happens beyond it
- **Preferred by regulators**: Basel III and FRTB emphasise Expected Shortfall

---

## Relative Performance Metrics

### Tracking Error

The standard deviation of active returns (portfolio minus benchmark):

Tracking Error = σ(R_p - R_b)

**Interpretation**: Measures how closely a portfolio follows its benchmark. Lower tracking error indicates more benchmark-like behaviour.

**Typical values**:
- Index funds: < 0.5% annualised
- Enhanced indexing: 0.5% - 2%
- Active management: 2% - 6%
- Concentrated strategies: > 6%

### Information Ratio

Active return per unit of tracking error:

Information Ratio = (R_p - R_b) / Tracking Error

**Interpretation**: Measures skill in generating active returns relative to active risk taken.

**Benchmarks**:
- IR > 0.5: Good active management
- IR > 1.0: Excellent active management (top quartile)
- IR < 0: Negative value-added from active decisions

### Alpha and Beta

From regression of portfolio returns on benchmark returns:

R_p = α + β × R_b + ε

**Beta**: Systematic risk exposure (sensitivity to benchmark)
- β = 1.0: Moves 1-for-1 with benchmark
- β > 1.0: Amplified benchmark movements
- β < 1.0: Dampened benchmark movements

**Alpha**: Return unexplained by benchmark exposure
- α > 0: Outperformance after adjusting for beta
- Often the primary measure of active manager skill

---

## Performance Attribution

### Brinson-Fachler Attribution

Decomposes active return into three effects:

**Allocation Effect**: Value from different sector weights
= Σ (W_p,s - W_b,s) × (R_b,s - R_b)

**Selection Effect**: Value from security selection
= Σ W_b,s × (R_p,s - R_b,s)

**Interaction Effect**: Combined allocation and selection
= Σ (W_p,s - W_b,s) × (R_p,s - R_b,s)

Where:
- W_p,s = portfolio weight in sector s
- W_b,s = benchmark weight in sector s
- R_p,s = portfolio return in sector s
- R_b,s = benchmark return in sector s
- R_b = total benchmark return

**Interpretation**: Attribution reveals whether outperformance came from being in the right sectors (allocation) or picking the right securities (selection).

---

## Liquidity Metrics

### Average Daily Volume (ADV)

The average number of shares (or value) traded daily. Position sizes relative to ADV indicate liquidation difficulty.

**Rule of thumb**: Position should not exceed 10-25% of ADV to avoid market impact.

### Days to Liquidate

Position value divided by comfortable daily trading volume:

Days to Liquidate = Position Value / (ADV × Participation Rate)

Where participation rate is typically 10-25% of daily volume.

---

## Summary Table

| Metric | What It Measures | Higher Is | Key Limitation |
|--------|-----------------|-----------|----------------|
| Sharpe Ratio | Risk-adjusted return | Better | Penalises upside volatility |
| Sortino Ratio | Downside risk-adjusted return | Better | Requires MAR selection |
| Maximum Drawdown | Worst peak-to-trough loss | Worse | Single event, not frequency |
| Calmar Ratio | Return vs worst loss | Better | Based on single drawdown |
| VaR (95%) | 5th percentile loss | Worse | Ignores tail magnitude |
| CVaR (95%) | Average loss beyond VaR | Worse | More conservative |
| Tracking Error | Active risk | Neutral | Context-dependent |
| Information Ratio | Active return per unit risk | Better | Depends on benchmark choice |

---

**Document Control**  
Version: 2.0  
Last Updated: January 2024  
Author: Risk Management Team
