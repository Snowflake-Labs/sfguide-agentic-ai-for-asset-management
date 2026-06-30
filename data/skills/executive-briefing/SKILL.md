---
name: executive-briefing
description: Use this skill when the user asks for a "board briefing", "executive briefing", "firm overview", or mentions preparing for a board meeting or stakeholder presentation. Also use for "comprehensive performance summary" or "how is the firm performing" questions that require multi-tool orchestration across KPIs, flows, and strategy performance.
---

# Executive Briefing

## When to Activate

Trigger when user asks for: "executive briefing", "board briefing", "comprehensive firm overview", "complete executive briefing", or mentions preparing for a board/stakeholder meeting.

## 4-Step Multi-Tool Workflow

### Step 1: Firm KPIs and Strategy Performance

Tool: `executive_kpi_analyzer`

Query: "FIRM_AUM, net flows, client count, and performance by strategy with QTD and YTD returns"

Extract:
- FIRM_AUM (authoritative figure from holdings)
- Net flows (gross inflows, outflows, net)
- Client count
- Strategy performance table (AUM, QTD return, YTD return per strategy)
- Top 5 and bottom 5 performing strategies

### Step 2: Client Flow Analytics

Tool: `executive_kpi_analyzer`

Query: "Client flow breakdown by client type and strategy, concentration analysis"

Extract:
- Flow trends
- Any concentration concerns (single client >10%)
- Client type distribution

### Step 3: Strategic Context

Tool: `search_internal_docs`

Query: "Investment philosophy sustainable investing strategic positioning"

Extract:
- Key positioning statements
- Strategic alignment context

### Step 4: Synthesise Complete Briefing

Use the output template in [BOARD_TEMPLATE.md](BOARD_TEMPLATE.md).

## Key Business Rules

- Use FIRM_AUM (from holdings, authoritative) — NOT TOTAL_CLIENT_AUM (from client flows, directional)
- Flag any strategy with negative YTD flows as "AREA OF CONCERN"
- Note data freshness timestamp in closing line

## Stopping Points

- After Step 2 (KPIs and flow data gathered): present headline numbers for confirmation before full synthesis
- After Step 4 (briefing drafted): present for review before distribution or PDF generation

## Output

A complete executive briefing following the [BOARD_TEMPLATE.md](BOARD_TEMPLATE.md) structure with headline KPIs, strategy performance table, client insights, and key board messages.
