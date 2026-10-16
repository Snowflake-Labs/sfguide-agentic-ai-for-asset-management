---
name: executive-kpi-briefing
description: Use this skill for KPI review and business performance questions, especially when the user asks for firm-wide performance highlights, overall AUM, net flows, gross inflows/outflows, and the strongest or weakest strategies in one answer. Also use for board briefings, executive briefings, comprehensive firm overviews, stakeholder presentations, and holistic business performance reviews.
---

# Executive Briefing

Purpose: help a senior executive at a large asset management firm run a holistic business performance review that combines firm KPIs, strategy performance, client flow quality, concentration risks, and strategic context into a board-ready narrative.

## When to Activate

Trigger when user asks for: "executive briefing", "board briefing", "comprehensive firm overview", "complete executive briefing", "holistic business performance review", or mentions preparing for a board/stakeholder meeting.

Also trigger when the intent is an executive KPI review even without the words "briefing" or "board", for example requests that ask for:
- overall or firm-wide AUM
- net flows together with gross inflows/outflows
- top and bottom performing strategies
- latest business performance highlights across the firm
- a single answer that combines KPIs, flows, and strategy ranking

## 5-Step Multi-Tool Workflow

### Step 1: Firm KPIs and Strategy Performance

Tool: `executive_kpi_analyzer`

Query: "Give me the latest available firm-wide KPIs including FIRM_AUM, gross inflows, gross outflows, net flows, active client count, and strategy performance by AUM, QTD return, and YTD return"

Extract:
- FIRM_AUM (authoritative figure from holdings)
- Gross inflows, gross outflows, and net flows
- Client count
- Strategy performance table (AUM, QTD return, YTD return per strategy)
- Top and bottom strategy cohort sized appropriately for the strategy universe, typically top 3 and bottom 3 for this demo
- Latest available data date used for the review

Then, in the same step:

Tool: `executive_kpi_analyzer`

Query: "Gross inflows, gross outflows and net flows by strategy for the same period, with the ESG strategies grouped together versus all other strategies"

Present a short "Flows by strategy family" table (ESG vs all other strategies: gross inflows, gross outflows, net flows, share of firm net flows), and a one-line note on which family is leading. This is mandatory in every KPI briefing: it is the anchor for follow-ups such as "the ESG inflows look strong - is that broad-based?", so the ESG flow figures must already be on the page. Quote the figures as returned; do not derive one family by subtracting from the firm total unless the query only returns the total.

### Step 2: Client Flow Quality and Concentration

Tool: `executive_kpi_analyzer`

Query: "Client flow breakdown by client type and strategy, concentration analysis, broad-based demand versus single-client dependence"

Extract:
- Flow trends
- Any concentration concerns (single client >10% of flows or dominant client dependence)
- Client type distribution
- Whether flows are broad-based or concentrated
- Which client segments are driving inflows and outflows

### Step 3: Performance Interpretation

Use the results from Steps 1 and 2 to identify:
- Whether business momentum is supported by both performance and flows
- Whether strong returns are paired with weak flows, or vice versa
- Whether any top-performing strategies still represent areas of commercial concern because of redemptions or concentration risk
- Whether any underperforming strategies remain strategically important because of resilient client demand

### Step 4: Strategic Context

Tool: `search_internal_docs`

Query: "Investment philosophy sustainable investing strategic positioning"

Extract:
- Key positioning statements
- Strategic alignment context
- Approved client-facing messaging themes and intended audience segments
- Any tension between strategic-plan targets and the latest operating data that an executive should treat as a planning or narrative caveat

### Step 5: Synthesise Complete Briefing

Use the output template in [BOARD_TEMPLATE.md](BOARD_TEMPLATE.md).

## Return Figures (mandatory)

- Quote portfolio, benchmark and active (excess) returns exactly as the query returns them; never recompute them yourself (no subtraction, summing or compounding by hand, no bash or code_execution arithmetic). If a figure is missing, query for it.
- For quarters and other multi-month periods use the linked (compounded) figures from attribution data rather than adding monthly numbers.
- When quoting allocation, selection or interaction effects, take all of them and the active return from ONE linked portfolio-total row (the `attribution_analyzer` linked Brinson effects query in bps with its reconciliation check column). Verify the effects sum to the active return before quoting; if not, re-query. Never derive selection by subtraction or from summed sector rows.

## Key Business Rules

- Use FIRM_AUM (from holdings, authoritative) — NOT TOTAL_CLIENT_AUM (from client flows, directional)
- Flag any strategy with negative YTD flows as "AREA OF CONCERN"
- If latest flows and latest performance are from different timestamps, say so explicitly
- Always distinguish performance leadership from commercial momentum
- Lead with the latest available data, not static business-context figures
- End with 3 board-level implications: growth, risk, and action required
- When connecting strategy documents to live performance, prefer "alignment" or "tension" framing over absolute claims if the latest synthetic operating data appears inconsistent with older strategic-plan targets or baselines

## Stopping Points

- After Step 2 (KPIs and flow quality gathered): present headline numbers for confirmation before full synthesis
- After Step 5 (briefing drafted): present for review before distribution or PDF generation, and offer an attribution drill-down (country or sector) for the strongest and weakest strategies

## Output

A complete executive briefing following the [BOARD_TEMPLATE.md](BOARD_TEMPLATE.md) structure with headline KPIs, strategy performance, client flow quality, concentration signals, strategic context, and board-level implications.

For Step 1 style answers, do not conclude that flows are broad-based unless the client concentration analysis has actually been run. Instead, if strong flows are observed in a strategy such as ESG, end by recommending the natural next question: whether demand is diversified across the client base or driven by a small number of mandates.
