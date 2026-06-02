---
doc_type: methodology_docs
linkage_level: global
variant_id: modern_portfolio_theory_primer
word_count_target: 1200
placeholders:
  required: []
---

# Modern Portfolio Theory: Foundations for Portfolio Construction

**Document Type**: Quantitative Methodology  
**Topic**: Mean-Variance Optimisation and Portfolio Theory  
**Effective Date**: January 2024  
**Classification**: Internal - Investment Education

---

## Introduction

Modern Portfolio Theory (MPT), developed by Harry Markowitz in 1952, provides the theoretical framework for constructing portfolios that optimise expected return for a given level of risk. This primer explains the core concepts that underpin our portfolio construction and risk management processes.

---

## Core Concepts

### Expected Return

A portfolio's expected return is the weighted average of individual asset expected returns:

E[R_p] = Σ w_i × E[R_i]

Where:
- w_i = weight of asset i in the portfolio
- E[R_i] = expected return of asset i
- Weights sum to 1.0 (fully invested constraint)

Expected returns are forward-looking estimates derived from:
- Historical return analysis
- Fundamental valuation models
- Economic forecasts
- Analyst consensus

### Portfolio Variance

Portfolio risk, measured by variance, depends not only on individual asset volatilities but also on correlations between assets:

σ²_p = Σ Σ w_i × w_j × σ_i × σ_j × ρ_{ij}

Where:
- σ_i = standard deviation of asset i
- ρ_{ij} = correlation between assets i and j

This relationship creates the diversification benefit: combining imperfectly correlated assets reduces portfolio risk below the weighted average of individual risks.

### The Efficient Frontier

The efficient frontier represents the set of portfolios offering:
- Maximum expected return for a given risk level, OR
- Minimum risk for a given expected return

Portfolios below the efficient frontier are suboptimal—an investor can achieve higher return at the same risk, or equal return at lower risk.

---

## Mean-Variance Optimisation

### The Optimisation Problem

Mean-variance optimisation finds portfolio weights that maximise:

U = E[R_p] - (λ/2) × σ²_p

Where λ represents investor risk aversion. Higher λ values penalise variance more heavily, producing more conservative portfolios.

Subject to constraints:
- Σ w_i = 1 (fully invested)
- w_i ≥ 0 (no short selling, if constrained)
- Other mandate-specific constraints

### Input Requirements

Optimisation requires three inputs:
1. **Expected returns vector**: E[R] for each asset
2. **Covariance matrix**: σ × σ × ρ relationships between all asset pairs
3. **Constraints**: Investment guidelines and limits

### Practical Considerations

**Estimation Error**: Small changes in expected return estimates can dramatically alter optimal weights. Robust optimisation techniques or Black-Litterman approaches help stabilise solutions.

**Concentration Risk**: Unconstrained optimisation often produces extreme weights. Position limits prevent excessive concentration.

**Rebalancing Costs**: Optimal weights change continuously, but trading costs make continuous rebalancing impractical. Rebalancing triggers or periodic reviews balance optimality against costs.

---

## Risk Decomposition

### Systematic vs Idiosyncratic Risk

**Systematic (Market) Risk**: Risk affecting all securities, driven by macroeconomic factors. Cannot be eliminated through diversification. Captured by market beta (β).

**Idiosyncratic (Specific) Risk**: Risk unique to individual securities, driven by company-specific factors. Diversifiable through portfolio construction.

As portfolio holdings increase, idiosyncratic risk approaches zero whilst systematic risk remains.

### Factor-Based Decomposition

Risk can be decomposed into factor exposures:

R_p = α + β_market × R_market + β_value × R_value + β_size × R_size + ε

Common factors include:
- **Market**: Overall equity market return
- **Value**: High book-to-market vs low book-to-market
- **Size**: Small cap vs large cap
- **Momentum**: Recent winners vs recent losers
- **Quality**: Profitable, stable vs unprofitable, volatile

Understanding factor exposures enables intentional risk-taking and unintended risk identification.

---

## The Capital Asset Pricing Model (CAPM)

### Equilibrium Pricing

CAPM extends portfolio theory to asset pricing:

E[R_i] = R_f + β_i × (E[R_market] - R_f)

Where:
- R_f = risk-free rate
- β_i = asset i's sensitivity to market returns
- E[R_market] - R_f = market risk premium

Implications:
- Expected return depends only on systematic risk (beta)
- Idiosyncratic risk earns no premium (it's diversifiable)
- Higher beta assets should offer higher expected returns

### Limitations

CAPM's single-factor model oversimplifies reality:
- Multiple risk factors explain returns
- Beta varies over time
- Market portfolio is unobservable

Multi-factor models (Fama-French, Carhart) extend CAPM to capture additional return drivers.

---

## Practical Applications

### Asset Allocation

Strategic asset allocation applies MPT principles:
1. Define investable universe (asset classes)
2. Estimate expected returns and covariances
3. Specify risk tolerance and constraints
4. Optimise to find efficient portfolios
5. Select portfolio matching investor objectives

### Performance Attribution

Decomposing returns into allocation and selection effects reveals value-added sources:
- **Allocation Effect**: Value from asset class weight differences vs benchmark
- **Selection Effect**: Value from security selection within asset classes
- **Interaction Effect**: Combined allocation and selection contribution

### Risk Budgeting

Allocating risk rather than capital:
- Define total portfolio risk budget
- Allocate risk to strategies or managers
- Monitor actual vs budgeted risk consumption

---

## Key Takeaways

1. **Diversification is valuable**: Combining imperfectly correlated assets reduces risk without proportionally reducing return.

2. **Risk and return are related**: Higher expected returns require accepting higher risk in equilibrium.

3. **Not all risk is rewarded**: Only systematic risk earns a premium; idiosyncratic risk should be diversified away.

4. **Inputs matter**: Optimisation quality depends on expected return and covariance estimation accuracy.

5. **Constraints are necessary**: Practical portfolios require limits on concentration, liquidity, and other factors.

---

## References

1. Markowitz, H. (1952). "Portfolio Selection." The Journal of Finance.
2. Sharpe, W. (1964). "Capital Asset Prices." The Journal of Finance.
3. CFA Institute (2024). "Portfolio Management" Level II Curriculum.

---

**Document Control**  
Version: 1.3  
Last Updated: January 2024  
Author: Investment Strategy Team
