---
name: implementation-planning
description: Use this skill when the user explicitly requests an "implementation plan", "execution plan", "trading plan", or asks for specific costs and timelines for portfolio changes. Creates detailed trade plans with dollar amounts, trading costs, execution strategies, and settlement timelines.
---

# Implementation Planning

## When to Activate

Trigger when user explicitly requests: "implementation plan with specific dollar amounts and timelines", "trading costs and execution strategy", "detailed execution plan with market impact estimates"

Do NOT trigger for general portfolio recommendations — those use concentration-risk-assessment instead.

## 5-Step Workflow

### Step 1: Current Holdings

Tool: `quantitative_analyzer`

Get current positions (market value, weight) for target securities.

### Step 2: Liquidity Analysis

Tool: `implementation_analyzer`

Query trading costs and liquidity metrics:
- Bid-ask spreads
- Market impact estimates
- Average daily volume for each security
- Use TICKER dimension to filter by specific securities

### Step 3: Settlement Timing

Tool: `implementation_analyzer`

Query settlement data:
- Historical settlement patterns by portfolio
- T+ settlement days for execution planning

### Step 4: Calculate Implementation Details

Apply these formulas:

- **Dollar amount to trade** = Current Value × (Current Weight - Target Weight)
- **Trading costs** = Notional × (Spread + Market Impact Estimate)
- **Execution timeline** = Based on volume constraints and urgency
- **Volume participation**: Target < 20% of ADV per day to minimise impact

### Step 5: Synthesise Plan

| Security | Action | Notional ($) | Est. Cost ($) | Cost (bps) | Strategy | Timeline |
|----------|--------|-------------|--------------|-----------|----------|----------|
| [Ticker] | Buy/Sell | $X,XXX,XXX | $X,XXX | X.X bps | VWAP/TWAP/Block | T+X |

**Total implementation cost**: $[sum] ([weighted avg] bps)

**Execution Strategy Recommendations**:
- VWAP: For liquid names where urgency is moderate
- TWAP: For less liquid names to spread market impact
- Block: For large positions where a single cross is available

**Settlement Timeline**: All trades settle on T+2 standard settlement cycle.

## Stopping Points

- After Step 2 (liquidity data gathered): present estimated costs and confirm trade parameters with user
- After Step 5 (plan synthesised): present the full implementation plan for approval before execution

## Output

A detailed implementation plan with trade table, cost estimates, execution strategy recommendations, and settlement timeline.
