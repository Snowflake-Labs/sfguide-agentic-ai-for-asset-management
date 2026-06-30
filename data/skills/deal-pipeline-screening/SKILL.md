---
name: deal-pipeline-screening
description: Use this skill when the user asks about new deal screening, pipeline opportunities, deal flow, new investment candidates, term sheet analysis, comparable deals, or preliminary credit assessment for incoming opportunities. Also use for "what's in the pipeline", "screen this deal", "comparable transactions", or "should we bid on this".
---

# Deal Pipeline Screening

## When to Activate

Trigger when user asks: "deal pipeline", "new deal", "screen this opportunity", "term sheet", "comparable deals", "should we bid", "deal flow", "incoming opportunities", "preliminary credit assessment", "new investment", "pipeline review", "deal scoring", "comparable transactions"

## Workflow

### Step 1: Pipeline Overview & Initial Scoring

Tool: `credit_portfolio_analyzer`
Query: Current pipeline deals with key metrics — borrower, sector, deal size, leverage, spread, DSCR, sponsor

Present:
- Headline: "[X] deals in pipeline, total commitment $[Y]M, weighted average spread [Z]bps"
- Pipeline summary table:

| Borrower | Sector | Size ($M) | Leverage | Spread (bps) | DSCR | Sponsor | Score |
|----------|--------|-----------|----------|-------------|------|---------|-------|
| [Name] | [Sector] | [X] | [X]x | [X] | [X]x | [Sponsor] | [A/B/C] |

- Quick scoring: A = strong fit, B = conditional, C = does not meet criteria
- Portfolio fit: "Adding [Deal] would increase sector concentration in [X] to [Y]%"

### STOPPING POINT

Present the pipeline overview, then offer:
"I've scored [X] pipeline opportunities. I can:
- **Deep-dive a specific deal** (full credit assessment, financial projections, covenant structure)
- **Run comparable analysis** (similar deals in portfolio and recent market transactions)
- **Check portfolio fit** (concentration limits, sector exposure, vintage diversification impact)
- **Generate IC screening memo** (structured recommendation with scoring matrix for investment committee)

Which would be most useful?"

### Step 2a: Deal Deep-Dive (if user selects a deal)

Tool: `credit_portfolio_analyzer`
Query: Full financial profile for the selected deal — revenue, EBITDA, margins, growth, capex, FCF

Tool: `search_credit_agreements`
Query: Term sheet or credit agreement — covenant package, pricing grid, call protection, PIK terms

Present:
- Financial profile table (historical + projected)
- Covenant package assessment: "Leverage covenant at [X]x provides [Y]% headroom above base case"
- Pricing assessment: "Spread of [X]bps is [tight / fair / wide] vs market for [leverage/sector]"
- Key risks: top 3 risk factors
- Key strengths: top 3 positive factors

### Step 2b: Comparable Analysis (if user chooses)

Tool: `credit_portfolio_analyzer`
Query: Existing portfolio holdings in same sector, similar leverage profile

Tool: `macro_data_analyzer`
Query: Recent market transaction data for comparable leverage/sector

Present:
- Comparables table:

| Deal | Type | Leverage | Spread | DSCR | Vintage |
|------|------|----------|--------|------|---------|
| [Pipeline deal] | New | [X]x | [X]bps | [X]x | New |
| [Portfolio comp 1] | Portfolio | [X]x | [X]bps | [X]x | [Year] |
| [Portfolio comp 2] | Portfolio | [X]x | [X]bps | [X]x | [Year] |
| Market median | Market | [X]x | [X]bps | [X]x | - |

- Assessment: "Deal pricing is [X]bps [tight / wide] vs portfolio comparables"

### Step 2c: Portfolio Fit Assessment (if user chooses)

Tool: `credit_portfolio_analyzer`
Query: Current portfolio concentrations — by sector, by sponsor, by vintage, by rating

Present:
- Concentration impact table:

| Dimension | Current | Pro-Forma | Limit | Status |
|-----------|---------|-----------|-------|--------|
| [Sector] | [X]% | [Y]% | [Z]% | [OK/WATCH/BREACH] |
| [Sponsor] | [X]% | [Y]% | [Z]% | [OK/WATCH/BREACH] |
| Single name | [X]% | [Y]% | [Z]% | [OK/WATCH/BREACH] |

- Diversification impact: "Adding this deal [improves / reduces] HHI from [X] to [Y]"
- Vintage bucket: "This would bring 2024 vintage to [X]% of portfolio"

### Step 2d: IC Screening Memo (if user chooses)

Synthesise into structured IC format:

```
## Investment Committee Screening: [Borrower]

**Recommendation**: [PROCEED / CONDITIONAL / PASS]
**Deal Size**: $[X]M | **Spread**: [X]bps | **Leverage**: [X]x

### Scoring Matrix
| Criterion | Score (1-5) | Commentary |
|-----------|-------------|------------|
| Credit Quality | [X] | [One-liner] |
| Pricing | [X] | [One-liner] |
| Covenant Package | [X] | [One-liner] |
| Portfolio Fit | [X] | [One-liner] |
| Sponsor Quality | [X] | [One-liner] |
| **Composite** | **[X.X]** | |

### Key Considerations
**For**: [Top 3 reasons to invest]
**Against**: [Top 3 risk factors]

### Recommended Terms
[Any modifications to proposed terms, e.g., tighter covenants, higher spread]
```

## Audience-Specific Presentation

- **Investment Committee**: Step 1 pipeline + Step 2d IC memo for shortlisted deals
- **PM/Analyst**: Full workflow with all branching options
- **Origination/Marketing**: Step 1 pipeline summary + concentration check

## Output Template

```
## Deal Pipeline Screening

**Pipeline**: [X] deals | **Total Commitment**: $[Y]M | **As of**: [Date]

### Top Opportunities
| Rank | Borrower | Sector | Spread | Score | Recommendation |
|------|----------|--------|--------|-------|----------------|
| 1 | [Name] | [Sector] | [X]bps | [X.X] | PROCEED |
| 2 | [Name] | [Sector] | [X]bps | [X.X] | CONDITIONAL |

### Portfolio Impact
- Largest sector exposure change: [Sector] [X]% → [Y]%
- Weighted average spread impact: [X]bps → [Y]bps

### Key Insight
[Pipeline quality assessment in 2-3 sentences]
```

## Cross-Skill References

- For covenant structure detail on a deal → **covenant-monitoring** skill
- For rate sensitivity of a new floating-rate deal → **rate-sensitivity-analysis** skill
- For full credit risk scoring → **credit-risk-calculator** skill

## Stopping Points

- After Step 1 (pipeline overview): Offer 4 branching options
- After any Step 2 branch: "Would you like to screen another deal, or shall I compile the full pipeline report?"
