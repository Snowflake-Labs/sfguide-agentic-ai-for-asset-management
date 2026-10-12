---
name: multi-level-attribution
description: Use this skill when the user asks for a performance attribution breakdown, what drove portfolio performance versus a benchmark, allocation versus selection effects, or Brinson analysis. Also use for prompts like "break down the performance attribution", "what drove our performance", "most recent quarter attribution", "why did we outperform/underperform", "break down excess return", or requests for attribution by country, sector, or industry. Also use for client and prospect phrasing such as "performance story", "what drove returns", "what's driven the returns", "explain performance to a prospect/client", "how did the fund do for the client" - present it in the Client/Prospect style. This is the default interactive attribution workflow with drill-down stopping points.
---

# Multi-Level Performance Attribution

## When to Activate

Trigger when user asks: "performance attribution", "break down the performance attribution", "what drove our performance", "what drove returns", "allocation vs selection", "Brinson", "portfolio versus benchmark attribution", "most recent quarter attribution", "why did we outperform/underperform", "break down excess return", "attribution by country/sector/industry", "what's driving my portfolio", "performance story", "YTD performance story", "what's driven the returns", "explain performance to a prospect", "explain performance to a client", "how has the fund performed for the client"

## Return Figures (mandatory)

- Quote active return, portfolio return and benchmark return exactly as the query returns them. Never recompute them (no portfolio minus benchmark, no summing monthly effects, no compounding by hand, no bash or code_execution arithmetic). If a figure is not in the result, query for it rather than derive it.
- For any period longer than one month (QTD, a full quarter, YTD, trailing 12M, or a named multi-month range) use the `linked_attribution` table with the matching `period_type` and quote `compounded_active_return` and the linked effects. Single-month Brinson rows must not be added together to make a multi-month figure.
- If the effects do not sum exactly to the reported active return, report both as returned and note the residual is interaction/linking; do not adjust either.

## Effect Figures (mandatory)

- Take allocation, selection, interaction and active return from ONE `linked_attribution` portfolio-total row: ask `attribution_analyzer` for "linked Brinson effects in bps for [portfolio], period_type [QTD/YTD/TRAILING_12M], period_end [date]". The verified query returns all four effects in bps plus a reconciliation check column (effects sum minus active return).
- Before quoting, verify allocation + selection + interaction equals active return (reconciliation check within 1 bp). If it does not, re-query with the same period_type, period_end and a single linked_grouping_dimension; never quote unreconciled effects.
- Never derive selection (or any effect) by subtracting other effects from the active return, and never build portfolio totals by summing sector rows yourself. Sector rows are for the contributor table only.

## Workflow

### Step 1: Identify Scope

- Portfolio: Use portfolio-name-resolution skill if name is ambiguous
- Period: Default to most recent quarter unless user specifies. A quarter or any multi-month period uses `linked_attribution` (period_type QTD, YTD or TRAILING_12M) for the headline and effects; use the monthly Brinson tables (attribution_date filter) only for single-month questions
- Audience: Detect from keywords (board/CIO → executive; PM/detail → analyst; client/prospect → client)

### Step 2: Sector Attribution (Default Entry Point)

Tool: `attribution_analyzer`
Query: Sector-level attribution for the identified portfolio and period. Multi-month period: `linked_attribution` with linked_grouping_dimension = 'SECTOR' and the matching period_type. Single month: grouping_dimension = 'SECTOR' from multi_level_detail, or brinson_sector

Present:
- Active return headline: "[+/-X]bps active return in [period]", with portfolio and benchmark returns quoted from the query result
- Decomposition: Allocation [X]bps + Selection [X]bps + Interaction [X]bps, all from the single linked portfolio-total row (reconciled to active, see Effect Figures)
- Top 3 sector contributors ranked by absolute total effect
- Table format with Portfolio Weight, Benchmark Weight, Active Weight, and effects

### STOPPING POINT

Present the sector summary, then offer:
"Here's the sector-level picture. I can:
- **Drill into a specific sector** (industry-level breakdown)
- **Pivot to country attribution** (geographic decomposition)
- **Show linked QTD/YTD figures** (compounding-adjusted for formal reporting)
- **Cross-reference with factor attribution** (systematic factor explanation)

Which would be most useful?"

### Period Continuity for Drill-Downs (mandatory)

Every Step 3 drill-down (industry, country, linked or factor) uses EXACTLY the same period as the answer it follows. If Step 2 reported a quarter, QTD, YTD or trailing 12M, the drill-down queries `linked_attribution` with the same period_type and period_end (linked_grouping_dimension = 'INDUSTRY' or 'COUNTRY'); never switch to the single last month from `multi_level_detail`. Use `multi_level_detail` only when the prior answer was itself a single month. Restate the period label and date range in the drill-down headline, and only change period if the user explicitly asks.

### Step 3a: Industry Drill-Down (if user chooses sector drill)

Tool: `attribution_analyzer`
Query: same period as Step 2. Multi-month: `linked_attribution` with linked_grouping_dimension = 'INDUSTRY', the same period_type and period_end, restricted to industries in the selected sector. Single month: grouping_dimension = 'INDUSTRY' AND parent_grouping_value = '[selected sector]'

Present industry breakdown within the chosen sector, showing which sub-industries drove the sector effect.

### Step 3b: Country Attribution (if user chooses geographic)

Tool: `attribution_analyzer`
Query: same period as Step 2. Multi-month: `linked_attribution` with linked_grouping_dimension = 'COUNTRY' and the same period_type and period_end. Single month: grouping_dimension = 'COUNTRY'

Present country-level attribution. Key insight to synthesise: "The [X]bps from [Sector] (sector view) is concentrated in [Country] holdings (country view), suggesting [regional/global] exposure."

### Step 3c: Linked Period View (if user chooses multi-period)

Tool: `attribution_analyzer`
Query: linked_attribution table with period_type = 'YTD' or 'QTD', linked_grouping_dimension = 'SECTOR'

Present linked effects. Note: "These linked figures use Frongello base-period adjustment and account for compounding — suitable for fact sheets and formal client reporting."

### Step 3d: Factor Cross-Reference / Intelligent Driver Discovery (if user chooses factor)

Tool: `attribution_analyzer`
Workflow:
1. Get factor contributions for the same period
2. Compare factor-explained returns vs Brinson selection effect
3. True alpha = Selection effect (from the reconciled linked row) - factor-explained portion

Narrative template: "Of the [+/-X]bps excess return, [Y]bps is explained by factor tilts ([factor1] [+/-Z]bps, [factor2] [+/-W]bps). Estimated true alpha from security selection: [remaining]bps."

## Audience-Specific Presentation

- **CIO/Board**: Step 2 only — summary table + headline, then a one-line offer of the country (or sector) drill-down
- **PM/Analyst**: Steps 2 + stopping point + whichever branch they choose (full detail)
- **Client/Prospect**: Step 2 with plain language — say "stock picking" not "selection effect", frame positively

## Output Template

```
## Attribution Summary: [Portfolio] — [Period]

**Active Return**: [+/-X]bps (Portfolio [Y]% vs Benchmark [Z]%)

| Effect | Contribution |
|--------|-------------|
| Allocation (sector weight decisions) | [+/-X]bps |
| Selection (stock picking within sectors) | [+/-X]bps |
| Interaction (combined) | [+/-X]bps |

### Top Contributors
1. **[Sector]**: [+/-X]bps — [1-line explanation]
2. **[Sector]**: [+/-X]bps — [1-line explanation]
3. **[Sector]**: [+/-X]bps — [1-line explanation]

### Key Insight
[Cross-dimension or factor synthesis]
```

## Stopping Points

- After Step 2 (sector attribution presented): Offer drill-down options, always including country attribution
- After any Step 3 branch: "Would you like to explore another dimension, or shall I synthesise the full picture?"
