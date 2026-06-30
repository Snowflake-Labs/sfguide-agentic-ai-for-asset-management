---
name: brinson-attribution
description: "Legacy skill — superseded by multi-level-attribution. This skill redirects to multi-level-attribution which provides full sector/country/industry drill-down, linked period attribution (QTD/YTD/12M), factor cross-reference, and interactive stopping points."
---

# Brinson Attribution (Legacy — Use multi-level-attribution Instead)

This skill has been superseded by `multi-level-attribution` which provides:

- Multi-level drill-down (sector, country, industry, asset class)
- Linked QTD/YTD/12M periods (Frongello base-period adjustment)
- Factor cross-reference for true alpha assessment
- Interactive stopping points for drill-down choices
- Audience-adaptive presentation (CIO/PM/Client)

## When This Skill Activates

Load the `multi-level-attribution` skill instead and follow its workflow.

## Quick Reference (for backward compatibility)

If the `multi-level-attribution` skill is unavailable, use this simplified workflow:

### Tool: `brinson_analyzer`

1. Query sector-level attribution (grouping_dimension = 'SECTOR')
2. Present active return = allocation + selection + interaction
3. Show top 3 sector contributors
4. Offer to drill into country or factor analysis
