---
name: quarterly-client-letter
description: Use this skill when the user asks to "prepare a quarterly client letter", "draft a client update", or create a "quarterly performance summary" for a specific portfolio. Also use when the user mentions preparing client communications that combine performance data with holdings and sector allocation.
---

# Quarterly Client Letter

## When to Activate

Trigger when user asks for: "quarterly client letter", "client letter", "quarterly update for [portfolio]", "draft client update"

## 5-Step Workflow

1. **Get template**: Search `search_internal_docs` for "Quarterly client letter template" (filter DOCUMENT_TYPE = 'sales_templates')
2. **Get performance**: Query `quantitative_analyzer` for "Latest quarter performance for SAM [portfolio]"
3. **Get holdings**: Query `quantitative_analyzer` for "Top 10 holdings for SAM [portfolio]"
4. **Get sectors**: Query `quantitative_analyzer` for "Sector breakdown for SAM [portfolio]"
5. **Synthesise**: Populate template with all sections

## Multi-Section Handling

Make SEPARATE Cortex Analyst calls for each section. Never combine different result types in a single SQL query.

## Date Handling

ALWAYS request "latest" or "most recent" data. Never use specific future dates like "Q4 2025".

## Output Format

- Always produce as a written document in markdown
- "Client presentation" or "annual presentation" = comprehensive written report, NOT slide deck
- NEVER produce slide-deck format (no "SLIDE 1", "SLIDE 2" headings)
- Use proper markdown headers, tables, and bullet points

See [TEMPLATE_STRUCTURE.md](TEMPLATE_STRUCTURE.md) for the standard letter structure.

## Return Figures (mandatory)

- Quote portfolio, benchmark and active (excess) returns exactly as the query returns them; never recompute them yourself (no subtraction, summing or compounding by hand, no bash or code_execution arithmetic). If a figure is missing, query for it.
- For quarters and other multi-month periods use the linked (compounded) figures from attribution data rather than adding monthly numbers.
- When quoting allocation, selection or interaction effects, take all of them and the active return from ONE linked portfolio-total row (the `attribution_analyzer` linked Brinson effects query in bps with its reconciliation check column). Verify the effects sum to the active return before quoting; if not, re-query. Never derive selection by subtraction or from summed sector rows.

## Stopping Points

- After Step 1 (template retrieved): confirm the correct portfolio and quarter with user
- After Step 5 (letter drafted): present for review before finalising or generating PDF
