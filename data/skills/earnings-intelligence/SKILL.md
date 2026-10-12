---
name: earnings-intelligence
description: Use this skill when the user asks about earnings analysis, quarterly results, management commentary, earnings call insights, guidance changes, sentiment analysis of earnings, or investment committee earnings summaries. Also use for "what did management say", "earnings surprises", "guidance raised/lowered", "tone of the call", or "red flags in earnings".
---

# Earnings Intelligence

## When to Activate

Trigger when user asks: "earnings analysis", "quarterly results", "earnings call", "management commentary", "guidance", "what did management say", "earnings surprise", "beat/miss", "tone of the call", "red flags", "sentiment analysis", "IC earnings summary", "earnings deep-dive"

## Identifying the Latest Quarter (mandatory)

"Latest" means the most recent call by date, not the first search hit. Fiscal years differ from calendar years (Microsoft's Q4 FY26 call was dated 2026-07-29, after its Q3 FY26 call):
1. Search `search_company_events` with a TICKER filter and EVENT_TYPE = 'Earnings Call', and compare the returned FISCAL_YEAR, FISCAL_PERIOD and PUBLISH_DATE values. Pick the call with the latest PUBLISH_DATE; Q4 / FY results are a valid quarter.
2. If needed, run a second search filtered to the expected next FISCAL_PERIOD (e.g. Q4 after Q3) or to PUBLISH_DATE after the call you found, to confirm nothing newer exists.
3. State the quarter and call date you used, e.g. "Q4 FY26 (call of 29 Jul 2026)". Use the same fiscal period for the `research_analyzer` financials.

## Workflow

### Step 1: Integrated Earnings Snapshot

Tool: `research_analyzer`
Query: Latest quarterly financials for the specified company — revenue, EPS, margins, year-over-year growth, beat/miss vs estimates

Tool: `search_company_events`
Query: Most recent earnings call transcript, selected per "Identifying the Latest Quarter" — key management quotes on guidance, strategy, and outlook

Present:
- Headline: "[Company] Q[X] [Year]: Revenue [beat/missed] by [X]%, EPS [beat/missed] by [X]%"
- Financial summary table: Revenue, EPS, Gross Margin, Operating Margin (actual vs estimate vs prior quarter)
- Top 3 management quotes with speaker attribution
- Guidance summary: raised / maintained / lowered vs prior quarter

### STOPPING POINT

Present the earnings snapshot, then offer:
"Here's the earnings snapshot with financials and key management commentary. I can:
- **Analyse sentiment and red flags** (tone shifts, hedging language, non-answers)
- **Track strategic commentary evolution** (how key themes changed vs prior quarters)
- **Generate an Investment Committee summary** (structured IC-ready format with conviction rating)
- **Cross-reference with analyst reactions** (broker research post-earnings)

Which would be most useful?"

### Step 2a: Sentiment & Red Flags (if user chooses sentiment)

Tool: `search_company_events`
Query: Full earnings transcript — analyse language patterns, hedging, qualifiers

Present:
- Sentiment score: Positive / Neutral / Cautious / Negative
- Red flags identified (if any): guidance qualifications, unusual language, topic avoidance
- Tone comparison: "Management tone was [more cautious / more confident / unchanged] vs Q[X-1]"
- Key hedging phrases: direct quotes with context

### Step 2b: Strategic Commentary Evolution (if user chooses evolution)

Tool: `search_company_events`
Query: Current AND prior quarter transcripts — compare commentary on key themes (growth strategy, margins, capital allocation, competitive position)

Tool: `research_analyzer`
Query: Prior quarter financials for comparison

Present:
- Theme-by-theme comparison table: [Theme] | Q[X-1] Commentary | Q[X] Commentary | Direction
- Identify narrative shifts: "Management shifted from [prior stance] to [current stance] on [topic]"
- Financial validation: "This narrative shift is [supported / contradicted] by the numbers: [evidence]"

### Step 2c: Investment Committee Summary (if user chooses IC)

Synthesise all data gathered into IC-ready format:

```
## [Company] — Earnings Intelligence Summary
**Quarter**: Q[X] [Year] | **Recommendation Impact**: [Unchanged / Upgrade / Downgrade]

### Beat/Miss Summary
| Metric | Actual | Estimate | Surprise |
|--------|--------|----------|----------|
| Revenue | [X] | [X] | [+/-X]% |
| EPS | [X] | [X] | [+/-X]% |

### Key Takeaways
1. [FACT] [Most important financial data point]
2. [ANALYSIS] [What the numbers imply about trajectory]
3. [INFERENCE] [What management commentary suggests about future quarters]

### Conviction Assessment
- **Bull case strengthened/weakened**: [1-sentence reason]
- **Key monitoring point**: [What to watch next quarter]
```

### Step 2d: Analyst Reactions (if user chooses cross-reference)

Tool: `search_external_docs` (filter: broker_research; also press_releases for company-reported reaction)
Query: Broker research mentioning [company] published within 7 days of earnings. Always use this tool for analyst reactions; do not infer reactions from rating changes in `research_analyzer` alone

Present:
- Analyst reactions summary: upgrades, downgrades, target price changes
- Consensus shift: "Post-earnings consensus moved from [X] to [Y]"
- Contrarian views: any analysts with meaningfully different takes

## Audience-Specific Presentation

- **CIO/Board**: Step 1 headline + beat/miss table + Step 2c IC summary (no stopping point, go straight to IC format)
- **PM/Analyst**: Full workflow with stopping point + whichever branch they choose
- **Client/Prospect**: Step 1 with plain language — "The company reported better-than-expected results" not "beat consensus by 3.2%"

## Output Template

```
## Earnings Intelligence: [Company] — Q[X] [Year]

**Headline**: [Revenue/EPS beat/miss summary in one sentence]

| Metric | Actual | Estimate | Prior Q | YoY Change |
|--------|--------|----------|---------|------------|
| Revenue | [X] | [X] | [X] | [+/-X]% |
| EPS | [X] | [X] | [X] | [+/-X]% |
| Gross Margin | [X]% | — | [X]% | [+/-X]pp |

### Management Highlights
1. "[Key quote]" — [Speaker], [Title]
2. "[Key quote]" — [Speaker], [Title]

### Guidance
[Raised / Maintained / Lowered]: [specific guidance details]

### Key Insight
[ANALYSIS] [Synthesis connecting financials to management commentary]
```

## Stopping Points

- After Step 1 (earnings snapshot): Offer 4 branching options
- After any Step 2 branch: "Would you like to explore another angle, or shall I compile everything into an IC summary?"
