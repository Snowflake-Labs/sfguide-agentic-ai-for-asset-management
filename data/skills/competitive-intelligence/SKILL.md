---
name: competitive-intelligence
description: Use this skill when the user asks to compare companies, analyse competitive positioning, peer analysis, market share, competitive landscape, or competitive moat. Also use for "compare X to Y", "who are the competitors", "peer group analysis", "industry positioning", or "competitive advantage".
---

# Competitive Intelligence

## When to Activate

Trigger when user asks: "compare companies", "competitive analysis", "peer analysis", "market share", "competitive landscape", "compare X to Y", "competitors", "industry positioning", "competitive moat", "peer group", "how does X stack up against", "who competes with"

## Workflow

### Step 1: Identify Competitive Set

Tool: `segment_analyzer`
Query: Revenue by segment and geography for the primary company — identify which markets they compete in

Tool: `search_external_docs`
Query: Broker research mentioning the company + "competitors" or "peer group" or "market share"

Present:
- Primary company profile: key segments, geographic mix, total revenue
- Identified peer set: 3-5 competitors from broker research and segment overlap
- Market context: industry size and growth rate (if available from research)

### Step 2: Financial Comparison

Tool: `fundamentals_analyzer`
Query: Key financial metrics for primary company + each identified peer — revenue growth, gross margin, operating margin, P/E, EV/Revenue

Tool: `sec_financials`
Query: Trailing 4-quarter financials for comparison if fundamentals view lacks depth

Present:
- Comparison table:

| Metric | [Company] | [Peer 1] | [Peer 2] | [Peer 3] | Industry Avg |
|--------|-----------|----------|----------|----------|-------------|
| Revenue Growth | [X]% | [X]% | [X]% | [X]% | [X]% |
| Gross Margin | [X]% | [X]% | [X]% | [X]% | [X]% |
| Operating Margin | [X]% | [X]% | [X]% | [X]% | [X]% |
| P/E Ratio | [X] | [X] | [X] | [X] | [X] |

- Ranking: Where the primary company sits on each metric
- Key differentiators: "Outperforms peers on [metric], underperforms on [metric]"

### STOPPING POINT

Present the competitive landscape, then offer:
"Here's the competitive picture with financials. I can:
- **Deep-dive a specific competitor** (full analysis of a selected peer)
- **Analyse market share trends** (segment-level revenue comparison over time)
- **Assess competitive moat** (risk factors, barriers to entry from SEC filings)
- **Generate competitive positioning summary** (IC-ready format)

Which would be most useful?"

### Step 3a: Competitor Deep-Dive (if user selects a peer)

Use full tool suite (fundamentals_analyzer + sec_financials + search_sec_filings + search_company_events + search_external_docs) on the selected peer company. Present in the same format as a standard company analysis, then compare back to the primary company.

### Step 3b: Market Share Analysis (if user chooses market share)

Tool: `segment_analyzer`
Query: Multi-year segment revenue for the primary company and key peers

Present:
- Revenue by segment over 3 years for each company
- Relative growth rates: "Company X is gaining share in [segment] at [Y]% vs industry [Z]%"
- Geographic shifts: market share changes by region

### Step 3c: Competitive Moat Assessment (if user chooses moat)

Tool: `search_sec_filings`
Query: Risk factors and competitive advantages from 10-K filings

Tool: `search_external_docs`
Query: Broker research on competitive positioning, barriers to entry

Present:
- Moat assessment: [Wide / Narrow / None]
- Sources of advantage: brand, scale, network effects, switching costs, patents, regulatory
- Key risks to competitive position (from 10-K risk factors)
- Analyst consensus on competitive durability

### Step 3d: IC Positioning Summary (if user chooses summary)

Synthesise into IC-ready competitive positioning summary.

## Audience-Specific Presentation

- **CIO/Board**: Step 1 + Step 2 comparison table + 1-sentence positioning verdict
- **PM/Analyst**: Full workflow with all branching options
- **Client/Prospect**: Simplified comparison — "Here's how [Company] compares to its main competitors on the metrics that matter most"

## Output Template

```
## Competitive Intelligence: [Company] vs Peers

**Competitive Set**: [Peer 1], [Peer 2], [Peer 3]
**Primary Market**: [Industry/Segment]

| Metric | [Company] | [Peer 1] | [Peer 2] | [Peer 3] |
|--------|-----------|----------|----------|----------|
| Revenue | [X] | [X] | [X] | [X] |
| Revenue Growth | [X]% | [X]% | [X]% | [X]% |
| Gross Margin | [X]% | [X]% | [X]% | [X]% |
| Operating Margin | [X]% | [X]% | [X]% | [X]% |

### Positioning Verdict
[1-2 sentences on where the company stands competitively]

### Key Differentiators
1. **[Advantage]**: [Evidence]
2. **[Advantage]**: [Evidence]

### Watch Points
- [Competitive risk 1]
- [Competitive risk 2]
```

## Stopping Points

- After Step 2 (financial comparison): Offer 4 branching options
- After any Step 3 branch: "Would you like to explore another angle, or shall I compile a competitive positioning summary?"
