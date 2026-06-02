---
name: rate-sensitivity-analysis
description: Use this skill when the user asks about interest rate exposure, floating rate risk, SOFR impact, rate sensitivity, rate shock scenarios, coverage ratio impact from rate changes, PIK triggers, or SOFR floor protection. Also use for "what happens if rates rise", "floating rate exposure", "rate impact on portfolio", or "which borrowers are most vulnerable to rate rises".
---

# Rate Sensitivity Analysis

## When to Activate

Trigger when user asks: "rate sensitivity", "floating rate exposure", "SOFR impact", "rate shock", "what happens if rates rise", "interest rate risk", "coverage impact from rates", "PIK trigger", "SOFR floor", "rate protection", "most vulnerable to rate rises", "rate environment"

## Workflow

### Step 1: Floating Rate Exposure Overview

Tool: `credit_portfolio_analyzer`
Query: Portfolio-level floating vs fixed split, SOFR floor coverage, weighted average spread, weighted average all-in yield

Tool: `macro_data_analyzer`
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

Tool: `credit_portfolio_analyzer`
Query: All borrowers with current DSCR, then model coverage at SOFR +100/+200/+300bp

Present:
- Impact table:

| Borrower | Current DSCR | +100bp | +200bp | +300bp | Breaches At |
|----------|-------------|--------|--------|--------|-------------|
| [Name] | [X]x | [Y]x | [Z]x | [W]x | +[N]bp |

- Portfolio aggregate: "At +200bp, [X] borrowers would breach coverage covenant"
- Most sensitive: "[Borrower] breaches DSCR covenant at just +[X]bp above current rates"

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
