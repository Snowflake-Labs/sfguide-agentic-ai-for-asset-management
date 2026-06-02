---
name: stress-scenario-analysis
description: Use this skill when the user asks for a "stress test", "scenario analysis", or wants to know how the portfolio would perform in a crisis. Also use for what-if questions like "what if rates rise 200bps", "impact of a COVID-like event", or "how bad could it get in a recession". Covers both historical scenario replay and custom shock construction.
---

# Stress Scenario Analysis

## When to Activate

Trigger when user asks: "stress test the portfolio", "what happens in a crash", "scenario analysis", "what if rates rise 200bps", "how would we perform in a COVID-like event"

## Pre-Defined Historical Scenarios

| Scenario | Period | Key Characteristics |
|----------|--------|-------------------|
| COVID-19 Crash | Feb-Mar 2020 | -34% S&P 500, extreme vol |
| Global Financial Crisis | Sep 2008 - Mar 2009 | -57% from peak, credit freeze |
| Taper Tantrum | May-Sep 2013 | Rates spike, EM selloff |
| Tech Bubble Burst | Mar 2000 - Oct 2002 | -78% Nasdaq |
| Flash Crash | May 2010 | Intraday -9%, liquidity evaporation |
| European Debt Crisis | Apr-Jun 2010 | Sovereign risk, EUR weakness |
| China Deval / VIX Spike | Aug 2015 | CNY deval, -12% S&P 500 |
| Fed Tightening 2022 | Jan-Oct 2022 | +400bps rates, -25% S&P 500 |
| SVB / Banking Crisis | Mar 2023 | Regional bank failure, rates vol |
| Volmageddon | Feb 2018 | Short-vol unwind, -10% S&P 500 |

## Workflow

### Historical Stress Backtest

Tool: `backtest_historical_stress` or `stress_scenario_analyzer`

1. Select scenario (or let user specify custom)
2. Apply historical shocks to current portfolio positions
3. Calculate portfolio-level impact

### Custom Scenario Construction

Tool: `scenario_sensitivity`

Parameters:
- Shock type: "rates", "equity", "credit", "fx", "volatility"
- Magnitude: "+200bps", "-20%", "+100bps spread"
- Duration: "instantaneous", "over 3 months"

### Result Presentation

| Scenario | Portfolio Impact | Worst Sector | Best Sector | Recovery Time |
|----------|-----------------|-------------|------------|--------------|
| [Name] | -X.X% | [Sector] (-XX%) | [Sector] (+XX%) | X months |

**Impact Waterfall**: Show contribution by sector/position to total portfolio loss.

**Narrative Template**: "In a [scenario name]-like event, the portfolio would experience an estimated [X.X]% drawdown, driven primarily by [sector/factor] exposure. The [largest position] accounts for [X]% of the total impact. Recovery to pre-stress levels would take approximately [X] months based on historical precedent."

## Stopping Points

- After scenario selection: confirm scenario and portfolio with user before running analysis
- After results presented: pause for follow-up questions or custom scenario requests

## Output

Stress test results with scenario summary table, impact waterfall, and narrative explanation following the template above.
