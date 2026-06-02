---
name: equity-research-report
description: Generates institutional-format equity research reports with 10 sections including recommendation, scenario analysis (Bull/Base/Bear), and monitoring plan. Use when the user asks for an "equity research report", "research report with scenarios", "full research report", or comprehensive company analysis with price target.
---

# Equity Research Report

## When to Activate

Trigger when user asks: "equity research report", "research report", "full research report with scenarios", "internal equity research report", "initiate coverage", "research note on [company]", "write a research report"

## Report Structure (10 Sections)

1. **RECOMMENDATION**: Buy/Hold/Sell rating, price target, upside/downside potential, risk rating, investment timeframe
2. **INVESTMENT THESIS**: Core thesis in 2-3 sentences, 3-5 supporting pillars, variant perception from consensus
3. **FINANCIAL MODEL**: Revenue breakdown by segment, margin analysis (gross/operating/net), EPS trends and estimates, FCF generation, balance sheet strength
4. **SCENARIO ANALYSIS** (Bull/Base/Bear): probability-weighted with price targets and key drivers
5. **INDUSTRY ANALYSIS**: Market size and growth, competitive landscape, regulatory environment
6. **RISK ASSESSMENT**: Risk matrix (impact x probability), key risks ranked, mitigation strategies
7. **CATALYSTS**: Near-term (3-6 months), medium-term (6-18 months), long-term (18+ months)
8. **VALUATION**: DCF summary, relative valuation vs peers, historical valuation context
9. **ESG CONSIDERATIONS**: Material ESG factors, ESG rating assessment
10. **MONITORING PLAN**: KPIs to track, thesis validation signposts, thesis invalidation triggers

## Workflow

### Step 1: Financial Foundation

Tool: `fundamentals_analyzer`
Query: Consensus estimates (high/mean/low), price targets (max/avg/min), analyst ratings, historical financials

Tool: `segment_analyzer` + `sec_financials`
Query: Revenue segments, geographic breakdowns, margins, 3-year annual + 4-quarter trends

Present:
- Company overview: "[Company] ([Ticker]) — [Sector], Market Cap $[X]B"
- Financial snapshot table: Revenue, EPS, margins for latest 4 quarters + 3 years
- Consensus: [X] analysts, [Y]% Buy, avg target $[X] ([+/-X]% upside)
- Segment breakdown: revenue by business line and geography

### STOPPING POINT 1 — Financial Data Gathered

"I've gathered the financial foundation — fundamentals, segments, and consensus estimates. I can:
- **Continue to research phase** (SEC filings, broker research, earnings calls, press releases)
- **Adjust the scope** (focus on specific segments or time periods)
- **Run competitive analysis first** (compare to peers before building the thesis) → loads competitive-intelligence skill
- **Check insider/institutional ownership** (smart money signals) → loads insider-institutional-analysis skill

Which approach works best?"

### Step 2: Research Gathering

Tool: `search_sec_filings`
Query: 10-K risk factors, MD&A narrative, business description, competitive positioning

Tool: `search_external_docs` (filter: broker_research)
Query: Recent analyst views, sector analysis, competitive positioning, price target rationale

Tool: `search_company_events`
Query: Management guidance, strategic commentary, outlook from recent earnings calls

Tool: `search_external_docs` (filter: press_releases)
Query: Recent catalysts, corporate developments, M&A activity, product launches

### STOPPING POINT 2 — All Research Gathered

"Research phase complete. Here's what I found:
- **Financial model**: [1-sentence summary of financial trajectory]
- **Bull case drivers**: [Top 2 catalysts]
- **Bear case risks**: [Top 2 risks from SEC filings]
- **Analyst consensus**: [Bullish / Mixed / Bearish] with [X]% Buy ratings

I can:
- **Generate the full 10-section report** (recommended — compile everything)
- **Review scenario assumptions** (before I map Bull/Base/Bear cases)
- **Deep-dive a specific area** (risk factors, competitive position, or ESG)
- **Generate a shorter executive summary** (2-page version for time-pressed readers)

How would you like to proceed?"

### Step 3: Report Compilation

Synthesise all gathered data into the 10-section format.

For Scenario Analysis (Section 4):
- Map `consensus_high` → Bull, `consensus_mean` → Base, `consensus_low` → Bear
- See [SCENARIO_FRAMEWORK.md](SCENARIO_FRAMEWORK.md) for methodology
- Calculate probability-weighted expected return: Σ(probability × return)

### Step 4: Optional PDF Generation

If user explicitly requests PDF:
Tool: `pdf_generator`
Parameters: report_title = "[Company] ([Ticker]) — Equity Research Report", document_audience = "internal"

## Audience Branching

- **Executive Summary** (CIO/Board — 2 pages): Recommendation + Thesis + Scenario table + Key Risks only (Sections 1, 2, 4, 6)
- **Full Research Report** (PM/Analyst — 8-10 pages): All 10 sections with full detail
- **Client Presentation** (Client/Prospect — 3-4 pages): Sections 1, 2, 4, 7 in plain language, no internal jargon, positive framing

## Output Template

```
# [Company] ([Ticker]) — Equity Research Report

**Rating**: [BUY / HOLD / SELL] | **Price Target**: $[X] ([+/-X]% upside) | **Risk**: [Low / Medium / High]

---

## 1. Recommendation
[2-3 sentences with rating rationale and timeframe]

## 2. Investment Thesis
**Core thesis**: [2-3 sentences]
| Pillar | Evidence | Confidence |
|--------|----------|------------|
| [Pillar 1] | [Data point] | [High/Medium/Low] |

## 3. Financial Model
| Metric | FY[X-2] | FY[X-1] | FY[X]E | FY[X+1]E |
|--------|---------|---------|--------|----------|
| Revenue | [X] | [X] | [X] | [X] |
| EPS | [X] | [X] | [X] | [X] |

## 4. Scenario Analysis
| Scenario | Probability | Price Target | Revenue Growth | EPS | Key Driver |
|----------|-------------|-------------|---------------|-----|-----------|
| Bull | [20-25]% | $[X] | [X]% | $[X] | [Driver] |
| Base | [50-60]% | $[X] | [X]% | $[X] | [Driver] |
| Bear | [20-25]% | $[X] | [X]% | $[X] | [Driver] |

**Probability-Weighted Expected Return**: [X]%

## 5-10. [Remaining sections follow report structure above]
```

## Cross-Skill References

- "Want competitive context first?" → `competitive-intelligence` skill
- "Check ownership signals?" → `insider-institutional-analysis` skill
- "Recent earnings insights?" → `earnings-intelligence` skill
- "Generate PDF?" → `pdf-report-generation` skill
- "Adapt for different audience?" → `audience-adaptive-narrative` skill

## Stopping Points

- After Step 1 (financial foundation): Offer scope adjustment + cross-skill options
- After Step 2 (all research gathered): Offer report generation + review options
- After Step 3 (report compiled): Offer PDF generation + audience adaptation
