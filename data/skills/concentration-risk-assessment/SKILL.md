---
name: concentration-risk-assessment
description: Use this skill when the user asks about "concentration risk", "which positions need attention", or "position limit breaches". Retrieves thresholds from internal policy documents and applies them to portfolio positions.
---

# Concentration Risk Assessment

## When to Activate

Trigger when user asks about: "concentration risk", "position limits", "which positions need attention", "concentration breach", "portfolio concentration"

## Policy-Driven 2-Phase Approach

### Phase 1: Retrieve Policy Thresholds

Tool: `search_internal_docs`

Query: "concentration risk limits", "issuer concentration", "position limits"

Extract from policy:
- Warning threshold: typically 6.5%
- Breach threshold: typically 7.0%
- Any sector-specific limits

### Phase 2: Apply to Portfolio Data

Tool: `quantitative_analyzer`

Query: "Current position weights for SAM [portfolio]"

Calculate: Position weight = Market Value / Total Portfolio Value

### Flagging Rules

Apply policy thresholds to flag positions:

- **Warning** (6.5-7.0%): "CONCENTRATION WARNING — Per Concentration Risk Policy"
- **Breach** (>7.0%): "BREACH — Immediate remediation required per policy"
- **Within limits** (<6.5%): No flag needed

### Output Format

| Position | Weight | Status | Policy Reference |
|----------|--------|--------|-----------------|
| [Ticker] | X.X% | BREACH / WARNING / OK | Concentration Risk Policy §X |

**Total flagged exposure**: [sum of warning + breach positions]

### Recommendations

- **Breach positions**: Immediate Investment Committee review required. Recommend reducing to below 6.5% within [timeframe from policy]
- **Warning positions**: Monitor daily. Place on watch list. Prepare contingency reduction plan
- **Multiple flags**: Prioritise by breach severity and liquidity

Cite specific policy sections for all threshold references.

## Stopping Points

- After Phase 1 (policy thresholds retrieved): confirm thresholds with user before applying
- After Phase 2 (positions flagged): present flagged positions for review before recommending actions

## Output

A concentration risk report with flagged positions table, severity classifications, and policy-aligned recommendations.
