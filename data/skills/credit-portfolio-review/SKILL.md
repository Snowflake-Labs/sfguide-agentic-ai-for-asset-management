---
name: credit-portfolio-review
description: Use this skill when the user asks for a portfolio overview, credit quality summary, portfolio health check, concentration analysis, vintage analysis, rating migration, watchlist review, or quarterly portfolio report. Also use for "how is the portfolio", "portfolio health", "credit quality trends", "concentration risk", or "quarterly review".
---

# Credit Portfolio Review

## When to Activate

Trigger when user asks: "portfolio review", "portfolio health", "credit quality summary", "concentration analysis", "vintage analysis", "rating migration", "watchlist", "quarterly review", "how is the portfolio", "portfolio overview", "credit quality trends", "exposure summary", "NAV bridge"

## Workflow

### Step 1: Portfolio Health Dashboard

Tool: `credit_portfolio_analyzer`
Query: Portfolio-level KPIs — total AUM/NAV, number of positions, weighted average spread, weighted average leverage, DSCR, default rate, watchlist count, rating distribution

Present:
- Headline: "$[X]M portfolio across [Y] positions, weighted average spread [Z]bps, [W] on watchlist"
- KPI summary:

| Metric | Current | Prior Quarter | Change |
|--------|---------|--------------|--------|
| NAV ($M) | [X] | [Y] | [Z]% |
| Positions | [X] | [Y] | [+/-Z] |
| WA Spread (bps) | [X] | [Y] | [+/-Z] |
| WA Leverage | [X]x | [Y]x | [+/-Z]x |
| WA DSCR | [X]x | [Y]x | [+/-Z]x |
| Non-Accruals | [X] | [Y] | [+/-Z] |
| Watchlist | [X] | [Y] | [+/-Z] |

- Rating distribution: count and % by rating bucket (1-5 or equivalent)
- Quick health verdict: "Portfolio quality is [stable / improving / deteriorating] quarter-over-quarter"

### STOPPING POINT

Present the health dashboard, then offer:
"Here's the portfolio health snapshot. I can:
- **Analyse concentration risk** (sector, sponsor, geography, single-name limits)
- **Review credit migrations** (rating upgrades and downgrades since last quarter)
- **Deep-dive the watchlist** (detailed status on each watchlist name and recommended actions)
- **Generate quarterly portfolio report** (comprehensive IC-ready review with all key metrics)

Which would be most useful?"

### Step 2a: Concentration Analysis (if user chooses)

Tool: `credit_portfolio_analyzer`
Query: Concentration by sector, sponsor, geography, single-name — current vs limits

Present:
- Concentration table:

| Dimension | Top Exposure | Current % | Limit % | Status |
|-----------|-------------|-----------|---------|--------|
| Sector: [X] | [Name] | [X]% | [Y]% | [OK/WATCH] |
| Sponsor: [X] | [Name] | [X]% | [Y]% | [OK/WATCH] |
| Geography: [X] | [Name] | [X]% | [Y]% | [OK/WATCH] |
| Single Name | [Name] | [X]% | [Y]% | [OK/WATCH] |

- HHI (Herfindahl-Hirschman Index) by sector
- Diversification assessment: "Portfolio is [well-diversified / moderately concentrated / concentrated] with HHI of [X]"

### Step 2b: Credit Migration Analysis (if user chooses)

Tool: `credit_portfolio_analyzer`
Query: Rating changes since prior quarter — upgrades, downgrades, and stable names

Present:
- Migration matrix (simplified):

| From \ To | 1 | 2 | 3 | 4 | 5 | NR |
|-----------|---|---|---|---|---|----|
| 1 | [X] | [Y] | | | | |
| 2 | [X] | [Y] | [Z] | | | |

- Upgrade list: borrowers that improved with reasons
- Downgrade list: borrowers that deteriorated with reasons
- Net migration: "[X] upgrades vs [Y] downgrades, net [positive / negative] migration"

### Step 2c: Watchlist Deep-Dive (if user chooses)

Tool: `credit_portfolio_analyzer`
Query: All watchlist names with current status, key metrics, last review date, recommended action

Tool: `search_compliance_certs`
Query: Latest management commentary for each watchlist name

Present:
- Watchlist detail:

| Borrower | Reason | On WL Since | Leverage | DSCR | Status | Next Review |
|----------|--------|-------------|----------|------|--------|-------------|
| [Name] | [Reason] | [Date] | [X]x | [Y]x | [Status] | [Date] |

- For each: one-line management outlook
- Recommended actions: "Increase monitoring / Request equity cure / Begin exit planning"

### Step 2d: Quarterly Portfolio Report (if user chooses)

Synthesise into comprehensive format:

```
## Quarterly Portfolio Review: [Fund Name]

**Period**: [Quarter] | **NAV**: $[X]M | **Positions**: [Y]

### Executive Summary
[3-4 sentence overview of portfolio performance, credit quality trends, and key actions taken]

### Performance
| Metric | Current | QoQ Change | YoY Change |
|--------|---------|------------|------------|
| NAV | $[X]M | [Y]% | [Z]% |
| Yield | [X]% | [+/-Y]bps | [+/-Z]bps |
| Default Rate | [X]% | [+/-Y]bps | [+/-Z]bps |

### Credit Quality
- Upgrades: [X] | Downgrades: [Y] | Net migration: [Direction]
- Rating distribution: [breakdown]
- Watchlist: [X] names, $[Y]M exposure

### Concentration
- Top sector: [Sector] at [X]% (limit [Y]%)
- Top sponsor: [Sponsor] at [X]% (limit [Y]%)
- HHI: [X] ([assessment])

### Key Actions & Outlook
1. [Action taken / recommended for highest priority issue]
2. [Action for next priority]
3. [Forward-looking positioning]
```

## Audience-Specific Presentation

- **Investment Committee**: Full Step 1 + Step 2d quarterly report
- **PM/Analyst**: Full workflow with all branching options
- **Client/Investor**: Step 1 KPI dashboard + simplified performance and quality narrative

## Output Template

```
## Portfolio Review: [Fund Name]

**NAV**: $[X]M | **Positions**: [Y] | **As of**: [Date]
**WA Spread**: [X]bps | **WA Leverage**: [Y]x | **Watchlist**: [Z]

### Health Summary
[2-3 sentence verdict on portfolio health and key trends]

### Top Concerns
1. [Highest priority issue]
2. [Second priority issue]

### Positive Developments
1. [Best development]
2. [Second best]
```

## Cross-Skill References

- For covenant issues on watchlist names → **covenant-monitoring** skill
- For rate impact on portfolio → **rate-sensitivity-analysis** skill
- For pipeline deals and new investment screening → **deal-pipeline-screening** skill
- For individual credit scoring → **credit-risk-calculator** skill

## Stopping Points

- After Step 1 (health dashboard): Offer 4 branching options
- After any Step 2 branch: "Would you like to explore another dimension, or shall I compile the full quarterly report?"
