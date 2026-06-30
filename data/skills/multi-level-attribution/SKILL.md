---
name: multi-level-attribution
description: Use this skill when the user asks about performance attribution, what drove returns, allocation vs selection effects, or Brinson analysis. Also use for "why did we outperform/underperform", "break down excess return", or requests for attribution by country, sector, or industry. This provides full multi-level drill-down with stopping points for interactive exploration.
---

# Multi-Level Performance Attribution

## When to Activate

Trigger when user asks: "performance attribution", "what drove returns", "allocation vs selection", "Brinson", "why did we outperform/underperform", "break down excess return", "attribution by country/sector/industry", "what's driving my portfolio"

## Workflow

### Step 1: Identify Scope

- Portfolio: Use portfolio-name-resolution skill if name is ambiguous
- Period: Default to most recent quarter unless user specifies (use attribution_date filter)
- Audience: Detect from keywords (board/CIO → executive; PM/detail → analyst; client/prospect → client)

### Step 2: Sector Attribution (Default Entry Point)

Tool: `brinson_analyzer`
Query: Sector-level attribution for the identified portfolio and period (use grouping_dimension = 'SECTOR' from the multi_level_detail table, or use the brinson_sector table directly)

Present:
- Active return headline: "[+/-X]bps active return in [period]"
- Decomposition: Allocation [X]bps + Selection [X]bps + Interaction [X]bps
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

### Step 3a: Industry Drill-Down (if user chooses sector drill)

Tool: `brinson_analyzer`
Query: grouping_dimension = 'INDUSTRY' AND parent_grouping_value = '[selected sector]'

Present industry breakdown within the chosen sector, showing which sub-industries drove the sector effect.

### Step 3b: Country Attribution (if user chooses geographic)

Tool: `brinson_analyzer`
Query: grouping_dimension = 'COUNTRY'

Present country-level attribution. Key insight to synthesise: "The [X]bps from [Sector] (sector view) is concentrated in [Country] holdings (country view), suggesting [regional/global] exposure."

### Step 3c: Linked Period View (if user chooses multi-period)

Tool: `brinson_analyzer`
Query: linked_attribution table with period_type = 'YTD' or 'QTD', linked_grouping_dimension = 'SECTOR'

Present linked effects. Note: "These linked figures use Frongello base-period adjustment and account for compounding — suitable for fact sheets and formal client reporting."

### Step 3d: Factor Cross-Reference / Intelligent Driver Discovery (if user chooses factor)

Tool: `factor_analyzer`
Workflow:
1. Get factor contributions for the same period
2. Compare factor-explained returns vs Brinson selection effect
3. True alpha = Selection effect - factor-explained portion

Narrative template: "Of the [+/-X]bps excess return, [Y]bps is explained by factor tilts ([factor1] [+/-Z]bps, [factor2] [+/-W]bps). Estimated true alpha from security selection: [remaining]bps."

## Audience-Specific Presentation

- **CIO/Board**: Step 2 only — summary table + headline, no drill-down offered unless asked
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

- After Step 2 (sector attribution presented): Offer drill-down options
- After any Step 3 branch: "Would you like to explore another dimension, or shall I synthesise the full picture?"
