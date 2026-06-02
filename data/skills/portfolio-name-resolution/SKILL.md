---
name: portfolio-name-resolution
description: Use this skill to resolve portfolio short names and aliases to their full SAM portfolio names. Activate whenever the user mentions a portfolio by informal name, abbreviation, or alias like "Tech", "ESG Leaders", "Flagship", or "60/40". All Cortex Analyst queries require the full "SAM" prefix, and this skill provides the mapping.
---

# Portfolio Name Resolution

## Critical Rule

All portfolio names start with "SAM " prefix. When a user mentions a portfolio by name or alias, ALWAYS use the FULL name (with SAM prefix) in questions to Cortex Analyst tools. NEVER drop the "SAM " prefix.

## Alias Mapping

| User Says | Full Portfolio Name | Strategy |
|-----------|-------------------|----------|
| "Tech", "Technology", "Technology & Infrastructure" | SAM Technology & Infrastructure | Growth |
| "ESG", "ESG Leaders" | SAM ESG Leaders Global Equity | ESG |
| "Flagship", "Global Flagship" | SAM Global Flagship Multi-Asset | Multi-Asset |
| "Core", "US Core" | SAM US Core Equity | Core |
| "Climate", "Renewable" | SAM Renewable & Climate Solutions | ESG |
| "Sustainable" | SAM Sustainable Global Equity | ESG |
| "AI", "Digital", "Digital Innovation" | SAM AI & Digital Innovation | Thematic |
| "Balanced", "60/40" | SAM Global Balanced 60/40 | Multi-Asset |
| "Tech Disruptors" | SAM Tech Disruptors Equity | Thematic |
| "Value", "US Value" | SAM US Value Equity | Value |
| "Income", "Multi-Asset Income" | SAM Multi-Asset Income | Income |

## Workflow

1. Match user input against the alias table (case-insensitive)
2. If exact match found, use the full portfolio name
3. If ambiguous (e.g., "equity" could match multiple), ask for clarification listing the candidates
4. If no match found, respond: "Portfolio not found. Available SAM portfolios: [list]. Did you mean one of these?"

## Benchmark Associations

- Growth strategies: S&P 500 or MSCI ACWI
- ESG strategies: MSCI World ESG Leaders
- Multi-Asset: 60% MSCI ACWI / 40% Bloomberg Global Agg
- Value: Russell 1000 Value
- Income: Bloomberg Global Aggregate

## Stopping Points

- This is a utility skill. No stopping points — resolution is instantaneous.
- If ambiguous match, pause and ask user for clarification before proceeding.

## Output

The full "SAM "-prefixed portfolio name to use in all Cortex Analyst queries.
