---
name: insider-institutional-analysis
description: Use this skill when the user asks about insider trading, institutional ownership, Form 4 filings, 13F holdings, smart money activity, insider buying/selling, top shareholders, or ownership changes. Also use for "who owns this stock", "insider activity", "institutional holders", "smart money", or "ownership concentration".
---

# Insider & Institutional Ownership Analysis

## When to Activate

Trigger when user asks: "insider trading", "insider buying/selling", "Form 4", "institutional ownership", "13F", "top shareholders", "who owns this stock", "smart money", "ownership changes", "insider activity", "institutional holders", "ownership concentration", "hedge fund positions"

## Workflow

### Step 1: Insider Trading Scan

Tool: `insider_trading_analyzer`
Query: Recent insider transactions for the specified company — buys, sells, option exercises, net insider sentiment

Present:
- Headline: "[Company]: Net insider [buying / selling / neutral] over trailing [period]"
- Summary table:

| Transaction Type | Count | Total Value | Notable Insiders |
|-----------------|-------|-------------|-----------------|
| Buys | [X] | $[X]M | [Names + Titles] |
| Sells | [X] | $[X]M | [Names + Titles] |
| Option Exercises | [X] | $[X]M | — |

- Cluster analysis: "Insider buying clustered around [date range], suggesting [interpretation]"
- Largest individual transaction: "[Name], [Title] [bought/sold] [X] shares ($[X]M) on [date]"

### Step 2: Institutional Ownership

Tool: `institutional_holdings_analyzer`
Query: Current institutional ownership — top holders, quarterly changes, concentration metrics

Present:
- Ownership summary: "[X]% institutionally owned, [Y] institutions reporting positions"
- Top 10 holders table:

| Rank | Institution | Shares | Value | % Outstanding | Change vs Prior Q |
|------|------------|--------|-------|---------------|-------------------|
| 1 | [Name] | [X]M | $[X]M | [X]% | [+/-X]% |

- Concentration: "Top 5 holders control [X]% of institutional ownership"
- Net quarterly flow: "Institutions were net [buyers / sellers] of [X]M shares in Q[X]"
- Notable changes: Highlight any large new positions or complete exits

### STOPPING POINT

Present the ownership picture, then offer:
"Here's the complete insider and institutional ownership picture. I can:
- **Cross-reference with price action** (correlate insider trades with stock price movements)
- **Compare to sector peers** (ownership concentration vs industry norms)
- **Generate ownership summary for IC** (structured Investment Committee format)

Which would be most useful?"

### Step 3a: Price Action Cross-Reference (if user chooses)

Tool: `insider_trading_analyzer`
Query: Insider trade dates and directions

Tool: `fundamentals_analyzer`
Query: Stock price around insider trade dates

Present:
- Insider timing analysis: "Insiders who bought in [period] saw [+/-X]% return since purchase"
- Signal assessment: "Insider buying has been a [reliable / unreliable] indicator for [Company] historically"

### Step 3b: Peer Comparison (if user chooses)

Tool: `institutional_holdings_analyzer`
Query: Ownership metrics for 3-5 peer companies

Present:
- Comparison table: institutional ownership %, insider ownership %, top holder concentration
- Relative positioning: "Institutional ownership is [above / below / in line with] sector average of [X]%"

### Step 3c: IC Ownership Summary (if user chooses)

Synthesise all data into IC format:

```
## Ownership Intelligence: [Company]

### Insider Sentiment: [Bullish / Neutral / Bearish]
- Net insider activity: [buying / selling] $[X]M over [period]
- Key signal: [1-sentence interpretation]

### Institutional Conviction: [High / Medium / Low]
- [X]% institutionally owned ([Y] institutions)
- Net quarterly flow: [buyers / sellers] of [X]M shares
- Top holder: [Name] at [X]%

### Smart Money Signal
[1-2 sentences combining insider + institutional signals into an actionable insight]
```

## Audience-Specific Presentation

- **CIO/Board**: Steps 1 + 2 headlines only + Step 3c IC summary
- **PM/Analyst**: Full workflow with stopping point and all branches
- **Client/Prospect**: Simplified — "The company's shares are widely held by major institutions, and recent insider activity suggests [confidence / caution]"

## Output Template

```
## Ownership Analysis: [Company]

**Insider Sentiment**: [Bullish / Neutral / Bearish] | **Institutional Ownership**: [X]%

### Insider Activity (Trailing [Period])
| Type | Count | Value | Key Insiders |
|------|-------|-------|-------------|
| Buys | [X] | $[X]M | [Names] |
| Sells | [X] | $[X]M | [Names] |

### Top Institutional Holders
| Institution | % Outstanding | Quarterly Change |
|------------|---------------|-----------------|
| [Name] | [X]% | [+/-X]% |

### Key Insight
[ANALYSIS] [Synthesis of insider + institutional signals]
```

## Stopping Points

- After Step 2 (full ownership picture): Offer 3 branching options
- After any Step 3 branch: "Would you like to explore another angle, or shall I generate the IC ownership summary?"
