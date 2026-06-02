---
name: audience-adaptive-narrative
description: Use this skill to adapt response depth, formatting, and language to the target audience. Activate when the user specifies an audience like "board memo", "client letter", "PM deep-dive", or when generating reports for different stakeholders, even if they don't explicitly name an audience tier.
---

# Audience-Adaptive Narrative

## When to Activate

Trigger when:
- User mentions "board memo", "board briefing", "board presentation"
- User mentions "client letter", "client report", "investor update"
- User mentions "PM deep-dive", "portfolio manager analysis", "detailed factor analysis"
- User specifies an audience for a report or analysis

## Audience Tiers

### Tier 1: CIO / Board / Executive

**Trigger words**: "board", "CIO", "executive", "C-suite", "stakeholder", "senior leadership"

**Format**:
- Executive summary: 3-5 bullet points maximum
- Lead with conclusion and recommendation
- One summary table only (no raw data tables)
- No jargon — plain business English
- Charts: 1-2 high-level (pie chart for allocation, line for performance)
- Length: 1-2 pages equivalent

**Tone**: Authoritative, decisive, action-oriented

### Tier 2: Portfolio Manager / Analyst

**Trigger words**: "PM", "portfolio manager", "analyst", "deep-dive", "detailed", "factor-level"

**Format**:
- Full detail with supporting evidence
- Multiple data tables (factor returns, IC scores, risk metrics)
- Statistical measures (t-stats, p-values, confidence intervals)
- Technical terminology acceptable
- Charts: Multiple (scatter plots, heatmaps, time series)
- Length: 3-10 pages equivalent

**Tone**: Technical, evidence-based, nuanced

### Tier 3: Client / Investor

**Trigger words**: "client", "investor", "external", "prospect", "RFP"

**Format**:
- Context-heavy with educational framing
- Explain what metrics mean, not just what they are
- Avoid acronyms or define them on first use
- Comparative benchmarks always included
- Charts: Clean, labelled, with annotations explaining significance
- Length: 2-4 pages equivalent
- Include regulatory disclosures where applicable

**Tone**: Professional, reassuring, transparent

## Workflow

1. Detect audience from user request using trigger words above
2. If no explicit audience, apply default: Tier 2 for analytical queries, Tier 3 for reports
3. Apply the corresponding format, tone, and length constraints to the response
4. If generating for multiple audiences (e.g., "board summary and detailed appendix"), produce sections at different tiers

## Default Behaviour

If no audience is specified, default to Tier 2 (PM/Analyst) for analytical queries and Tier 3 (Client) for report generation queries.

## Stopping Points

- This is a modifier skill applied during response generation. No standalone stopping points.
- Inherit stopping points from the calling workflow.

## Output

Response formatted according to the detected audience tier's format, tone, and length constraints.
