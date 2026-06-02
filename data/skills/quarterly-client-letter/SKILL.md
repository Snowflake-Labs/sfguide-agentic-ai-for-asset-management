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

## Stopping Points

- After Step 1 (template retrieved): confirm the correct portfolio and quarter with user
- After Step 5 (letter drafted): present for review before finalising or generating PDF
