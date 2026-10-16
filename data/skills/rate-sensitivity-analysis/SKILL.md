---
name: rate-sensitivity-analysis
description: Use this skill for ANY question about the credit portfolio's interest rate exposure, including simple summaries such as "what is our floating rate exposure", "summary of floating rate exposure - commitments, drawn amounts, weighted average spread, breakdown by facility type", or fixed vs floating split. Load it even when the question looks like a single lookup or matches a verified query. Also covers floating rate risk, SOFR impact, rate sensitivity, rate shock scenarios, coverage ratio impact from rate changes, PIK triggers, or SOFR floor protection. Also use for "what happens if rates rise", "floating rate exposure", "rate impact on portfolio", or "which borrowers are most vulnerable to rate rises".
---

# Rate Sensitivity Analysis

## When to Activate

Trigger when user asks: "rate sensitivity", "floating rate exposure", "summary of floating rate exposure", "commitments and drawn amounts by facility type", "weighted average spread", "fixed vs floating", "SOFR impact", "rate shock", "what happens if rates rise", "interest rate risk", "coverage impact from rates", "PIK trigger", "SOFR floor", "rate protection", "most vulnerable to rate rises", "rate environment"

## Workflow

### Step 1: Floating Rate Exposure Overview

Tool: `credit_portfolio_analyzer`
Query: Portfolio-level floating vs fixed split, SOFR floor coverage, weighted average spread, weighted average all-in yield

Tool: `market_analyzer`
Query: Current SOFR rate, recent trajectory, forward curve expectations

Present:
- Headline: "[X]% of portfolio is floating rate, current SOFR [Y]%, weighted average spread [Z]bps"
- Exposure summary:

| Metric | Value |
|--------|-------|
| Floating Rate % | [X]% |
| Fixed Rate % | [Y]% |
| With SOFR Floor | [X]% (floor at [Y]%) |
| Weighted Avg Spread | [X]bps |
| Weighted Avg All-In | [X]% |
| Current SOFR | [X]% |

- Rate environment context: "SOFR is currently [X]%, [up/down] [Y]bps over last [period]"

### STOPPING POINT

Present the exposure picture, then offer:
"Here's the rate exposure overview. I can:
- **Model rate shock scenarios** (+100bp / +200bp / +300bp impact on DSCR and coverage ratios)
- **Identify most vulnerable borrowers** (lowest DSCR at current rates, most exposed to rate rises)
- **Review PIK and rate protection terms** (SOFR floors, PIK triggers, call protection from credit agreements)
- **Compare to sector benchmarks** (spread and leverage vs direct lending market averages)

Which would be most useful?"

### Step 2a: Rate Shock Modelling (if user chooses)

Tool: `credit_portfolio_analyzer` (one query, all arithmetic in SQL)
Query: For every borrower, the latest **Min Interest Coverage** covenant test (`covenant_type` = 'Min Interest Coverage': `actual_value`, `covenant_threshold`, `headroom`, `covenant_status`, `breach_flag`, `test_date`) plus drawn amount and floating/fixed terms, with coverage shocked at SOFR +100/+200/+300bp in the same query.

Base coverage (mandatory): the starting ICR is the covenant-tested `actual_value` (ACTUALVALUE) from the latest test, not interest coverage recomputed from EBITDA / interest expense. Apply the shock to that tested figure (scale the tested ICR by current interest cost / shocked interest cost on the floating drawn balance). Recompute from EBITDA only for a borrower with no ICR covenant test, and label it "recomputed - no tested ICR".

Covenant thresholds are borrower-specific (e.g. 2.3x for one borrower, 1.75x for another). ALWAYS use each borrower's actual `covenant_threshold` from `credit_portfolio_analyzer`. NEVER assume a generic or "typical" floor such as 2.0x, and never compute the shock in bash or code_execution. A borrower with no interest-coverage covenant is shown as "No ICR covenant", not tested against an assumed level. Note where SOFR floors or fixed-rate facilities mute the shock.

Present:
- Impact table:

| Borrower | Covenant Min ICR | Current ICR | +100bp | +200bp | +300bp | Breaches At |
|----------|------------------|-------------|--------|--------|--------|-------------|
| [Name] | [T]x | [X]x | [Y]x | [Z]x | [W]x | +[N]bp |

- Portfolio aggregate: "At +200bp, [X] borrowers would breach coverage covenant"
- Most sensitive: "[Borrower] breaches its [T]x interest coverage covenant at just +[X]bp above current rates"

### Resilience Cross-Check (mandatory before calling any borrower resilient, safe or well-protected)

Tool: `credit_portfolio_analyzer`
Query: Current covenant status for the borrower across ALL covenant types at the latest test date (`covenant_status`, `breach_flag`, `headroom`, waiver flags).

Tool: `credit_risk_analyzer`
Query: Latest `pd_score` for the borrower (latest QUARTER_DATE).

Only describe a borrower as resilient if it has no current breach, waiver or watch status on any covenant AND its latest PD is not elevated. Otherwise say, e.g., "survives +300bp on interest coverage, but is currently in breach of its leverage covenant (PD 34%)". Always quote the covenant status and PD alongside a resilience claim.

### Step 2b: Vulnerable Borrower Deep-Dive (if user chooses)

Tool: `credit_portfolio_analyzer`
Query: Borrowers ranked by DSCR (lowest first), including leverage, revenue trend, sector

Tool: `search_compliance_certs`
Query: Latest compliance commentary for the most vulnerable borrower

Present:
- Vulnerability ranking table (top 5 most exposed)
- Deep-dive on #1: financial trends, management outlook, covenant headroom
- Context: "This borrower's DSCR has declined from [X]x to [Y]x over [Z] quarters"

### Step 2c: Rate Protection Review (if user chooses)

Tool: `search_credit_agreements`
Query: SOFR floor provisions, PIK triggers, call protection, rate reset terms

Present:
- Floor protection summary: "[X]% of floating portfolio has SOFR floors (average floor [Y]%)"
- PIK triggers: "PIK activates for [Borrower] if leverage exceeds [X]x"
- Call protection: upcoming call dates and make-whole provisions
- Assessment: "Current floor protection provides [limited / substantial] cushion against further rate rises"

### Step 2d: Sector Benchmark Comparison (if user chooses)

Tool: `credit_portfolio_analyzer`
Query: Portfolio metrics vs sector benchmarks — spread, leverage, coverage by sector

Present:
- Comparison table: portfolio weighted average vs market median for each metric
- Positioning: "Portfolio spread of [X]bps is [above / below / in line with] direct lending market average of [Y]bps"
- Relative value assessment

## Audience-Specific Presentation

- **Credit Committee**: Step 1 + Step 2a rate shock table + highlight borrowers breaching at reasonable rate scenarios
- **PM/Analyst**: Full workflow with all branching options
- **Client/Investor**: Step 1 summary — "The portfolio is well-positioned for the current rate environment with [X]% floor protection"

## Output Template

```
## Rate Sensitivity Analysis

**Portfolio**: [Fund Name] | **As of**: [Date]
**Current SOFR**: [X]% | **Floating Rate Exposure**: [Y]%

| Scenario | Avg DSCR | Borrowers Below 1.0x | Coverage Covenant Breaches |
|----------|---------|---------------------|---------------------------|
| Base (current) | [X]x | [Y] | [Z] |
| +100bp | [X]x | [Y] | [Z] |
| +200bp | [X]x | [Y] | [Z] |
| +300bp | [X]x | [Y] | [Z] |

### Most Vulnerable
1. **[Borrower]**: DSCR [X]x, breaches at +[Y]bp
2. **[Borrower]**: DSCR [X]x, breaches at +[Y]bp

### Key Insight
[Rate sensitivity assessment in 2-3 sentences]
```

## Stopping Points

- After Step 1 (exposure overview): Offer 4 branching options
- After any Step 2 branch: "Would you like to explore another angle, or shall I compile the full rate sensitivity report?"
