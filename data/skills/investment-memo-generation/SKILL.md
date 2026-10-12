---
name: investment-memo-generation
description: Generates structured investment memos with thesis framing, financial analysis, risk assessment, and catalyst identification. Use when the user asks for an "investment memo", "investment thesis", or "comprehensive company analysis". Requires multi-tool orchestration across SEC data, analyst estimates, and qualitative research.
---

# Investment Memo Generation

## When to Activate

Trigger when user asks: "investment memo", "investment thesis", "comprehensive analysis of [company]", "research overview of [company]", "IC memo", "build a case for [company]", "write up [company]"

## Memo Structure (7 Sections)

1. **THESIS FRAMING**: Core investment question, 3-5 thesis pillars, disconfirming evidence to monitor
2. **FINANCIAL PROFILE**: Revenue mix, growth rates, margin trends, Rule of 40 (for software), FCF generation
3. **COMPETITIVE LANDSCAPE**: Direct/indirect competitors, market position, competitive moat assessment
4. **MANAGEMENT OUTLOOK**: Forward guidance, strategic priorities, capital allocation
5. **ANALYST PERSPECTIVES**: Consensus views, price targets, rating distribution
6. **RISK ASSESSMENT**: Macro, regulatory, competitive, operational risks with leading indicators
7. **CATALYSTS**: 12-24 month bear/base/bull scenarios with probability weights

## Labelling Convention

Label every paragraph as:
- **[FACT]**: Sourced directly from SEC filings, financial data, or official company statements
- **[ANALYSIS]**: Derived from quantitative comparison or trend analysis
- **[INFERENCE]**: Qualitative judgment or forward-looking assessment

## Presentation Rules (every step)

- **Show only the figures you discuss.** Name the company in the title rather than in a
  column, and leave out any figure that is empty for this company.
- **Visualise whenever the data can be visualised.** Use `data_to_chart` for trends over
  time, mixes and comparisons. Each step lists the charts the analyst expects to see; add
  others where they help.

Rounding and period filters are handled by the semantic view's SQL instructions.

## Workflow

This workflow has two mandatory stopping points. They are the point of the skill: the
analyst controls scope and depth before committing to a full memo. Do NOT run the whole
workflow in one response, and do NOT gather qualitative research "in parallel" with the
financial foundation to save time.

### Step 1: Financial Foundation

Use `research_analyzer` to retrieve:

1. **Financial profile** — the last four fiscal years of annual figures (the view's
   `annual_figures` filter): revenue, revenue growth, gross, operating and net margin,
   diluted earnings per share, and free cash flow
2. **Revenue by geography** — the latest fiscal year, following the view's
   `GEOGRAPHIC_REVENUE_BREAKDOWN` verified query: each region's revenue and share of total
   revenue, and how much of total revenue the regions cover
3. **Street view** — following the view's `STREET_VIEW` verified query: the latest analyst
   ratings, price targets (low, average, high) and upside to the current share price; plus
   the consensus estimates of revenue, net income and EBITDA (the view's
   `financial_estimates_usd` filter)

Do not call `search_sec_filings`, `search_external_docs` or `search_company_events` in this
step — they belong to Step 2, which the analyst has not yet authorised.

Charts, via `data_to_chart`:
- Revenue by fiscal year — bar chart
- Revenue by geography — pie chart when the regions cover 98–102% of total revenue;
  otherwise a bar chart, stating the coverage in one line. If the company reports no
  geography, say so in one line

Present:
- Company identification: "[Company] ([Ticker]) — [Sector]"
- Financial snapshot: Revenue, EPS, margins for latest period
- Analyst consensus: [X] analysts, average target $[X]
- Both charts

### STOPPING POINT 1 — Financial Data Gathered

End your response here and wait for the analyst. Do not continue to Step 2 in the same
response, even if the original request named every section of the memo: a request for a
"comprehensive memo covering financials, management outlook, analyst views, competitive
position and risks" is the trigger for this workflow, NOT permission to skip its stopping
points.

Reply with the financial snapshot followed verbatim by these options:

"I've pulled the financial foundation. Here's a quick snapshot:
- Revenue: $[X]B ([+/-X]% YoY)
- EPS: $[X] (consensus: $[X])
- Margins: Gross [X]%, Operating [X]%

I can:
- **Continue to qualitative research** (SEC filings, broker research, earnings calls, press releases)
- **Adjust the scope** (different time period, specific segments to focus on)
- **Run earnings intelligence first** (deep-dive recent quarter) → loads earnings-intelligence skill
- **Check competitive positioning** (peer comparison before thesis) → loads competitive-intelligence skill

How would you like to proceed?"

### Step 2: Qualitative Research

Run this step only after the analyst has asked to continue.

Tool: `search_sec_filings`
Query: Risk factors, MD&A narrative, competitive advantages from 10-K

Tool: `search_external_docs` (filter: broker_research)
Query: Analyst views, competitive positioning, sector analysis

Tool: `search_company_events`
Query: Management guidance, strategic commentary from earnings calls

Tool: `search_external_docs` (filter: press_releases)
Query: Recent catalysts, corporate developments

Name the direct competitors explicitly in the competitive material you gather — a
"Competitive Landscape" section that never names a rival gives the analyst nothing to
follow up on.

### STOPPING POINT 2 — All Research Gathered

End your response here again. Present the findings summary and wait for the analyst to
choose a format before compiling the memo.

"Research complete. Key findings:
- **Thesis direction**: [Bullish / Cautious / Mixed] based on data gathered
- **Top catalyst**: [1-sentence catalyst]
- **Top risk**: [1-sentence risk from SEC filings]
- **Management tone**: [Confident / Cautious / Defensive] based on earnings commentary

I can:
- **Generate the full 7-section memo** (recommended)
- **Review findings before synthesis** (I'll present raw data for each section)
- **Focus the memo** (emphasise specific sections — e.g., risk-heavy or catalyst-focused)
- **Generate IC-ready quick thesis** (1-page version with recommendation)

What format works best?"

### Step 3: Memo Compilation

Run this step only after the analyst has chosen a format at Stopping Point 2.

Synthesise all data into 7-section format with [FACT]/[ANALYSIS]/[INFERENCE] labelling throughout.

Charts, via `data_to_chart`:
- Financial Profile: gross, operating and net margin by fiscal year — line chart (retrieve
  the Step 1 financial profile again if it is no longer available)

Scenario probabilities and other figures you derive in the text are not query results, so
`data_to_chart` cannot plot them — present those as tables.

See [SECTION_TEMPLATES.md](SECTION_TEMPLATES.md) for detailed section templates.

### Step 4: Optional Outputs

- **PDF Generation**: If user requests, call `pdf_generator` with report_title = "[Company] — Investment Memo", document_audience = "internal"
- **Audience Adaptation**: If user specifies audience, adapt per branching below

## Audience Branching

- **IC Memo** (Investment Committee — full detail): All 7 sections with [FACT]/[ANALYSIS]/[INFERENCE] labelling, 4-6 pages
- **Quick Thesis** (PM/CIO — action-oriented): Thesis Framing + Financial Profile + Catalysts only, 1-2 pages, recommendation-first
- **Client Summary** (Client/Prospect — educational): Thesis Framing + Financial Profile in plain language, no internal jargon, balanced tone, 2-3 pages

## Output Template

```
# Investment Memo: [Company] ([Ticker])

**Recommendation**: [BUY / HOLD / SELL] | **Conviction**: [High / Medium / Low]
**Date**: [Date] | **Analyst**: AI Research Co-Pilot

---

## Executive Summary
- [FACT] [Key financial metric]
- [ANALYSIS] [Key trend observation]
- [INFERENCE] [Forward-looking thesis statement]
- Recommendation: [BUY/HOLD/SELL] with [X]% upside to $[target]

## 1. Thesis Framing
**Core question**: [The key investment question this memo answers]

| Thesis Pillar | Evidence | Confidence |
|---------------|----------|------------|
| [Pillar 1] | [FACT: data point] | [High/Medium/Low] |
| [Pillar 2] | [FACT: data point] | [High/Medium/Low] |

**Disconfirming evidence to monitor**: [What would invalidate this thesis]

## 2. Financial Profile
[Chart: gross / operating / net margin (%) by fiscal year]

| Metric | FY[X-2] | FY[X-1] | FY[X] | Trend |
|--------|---------|---------|-------|-------|
| Revenue | [X] | [X] | [X] | [direction] |
| EPS | [X] | [X] | [X] | [direction] |

## 3-7. [Remaining sections follow structure above]
```

## Cross-Skill References

- "Deep-dive recent earnings?" → `earnings-intelligence` skill
- "Compare to competitors?" → `competitive-intelligence` skill
- "Check insider/institutional signals?" → `insider-institutional-analysis` skill
- "Generate PDF?" → `pdf-report-generation` skill
- "Adapt for different audience?" → `audience-format-adaptation` skill

## Stopping Points

Both are mandatory. Each ends the response and waits for the analyst.

- After Step 1 (financial data): revenue and geography charts, then scope adjustment + cross-skill options
- After Step 2 (all research gathered): offer memo generation + format options
- After Step 3 (memo compiled): offer PDF generation + audience adaptation
