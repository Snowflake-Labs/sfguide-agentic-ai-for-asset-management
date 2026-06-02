---
name: event-driven-risk-verification
description: Use this skill when the user provides an external event alert or asks about the impact of a specific event on portfolio holdings. Verifies events, calculates direct and indirect exposure through supply chains, and synthesises risk assessments.
---

# Event-Driven Risk Verification

## When to Activate

Trigger when user mentions: event impact on portfolio, supply chain disruption, geopolitical event, natural disaster affecting holdings, regulatory change impact, "what's our exposure to [event]?"

## 5-Step Workflow

### Step 1: Verify Event

Tool: `search_internal_docs`

Confirm event details: EventType, Region, Severity, AffectedSectors

### Step 2: Calculate Direct Exposure

Tool: `quantitative_analyzer`

Filter by affected region and sectors from Step 1. Get position weights for directly affected securities.

### Step 3: Calculate Indirect Exposure (Supply Chain)

Tool: `supply_chain_analyzer`

Apply multi-hop supply chain analysis:
- **Decay**: 50% per hop (direct suppliers = 100%, tier-2 = 50%, tier-3 = 25%)
- **Max depth**: 2 hops
- **Display threshold**: Only show exposures >= 5% post-decay
- **High dependency flag**: >= 20% post-decay
- Calculate both upstream (CostShare) and downstream (RevenueShare) impacts

### Step 4: Corroborate

Tool: `search_external_docs`

Search for company statements about supply chain exposure to the event region/sector. Validate or refine indirect exposure estimates.

### Step 5: Synthesise Risk Assessment

Present comprehensive assessment:

| Exposure Type | Security | Weight | Dependency | Source |
|--------------|----------|--------|-----------|--------|
| Direct | [Ticker] | X.X% | N/A | Holdings data |
| Indirect (Tier 1) | [Ticker] | X.X% | XX% (supplier) | Supply chain |
| Indirect (Tier 2) | [Ticker] | X.X% | XX% (supplier) | Supply chain |

**Total portfolio exposure**: [sum direct + adjusted indirect]

**Recommendations**:
- Immediate: [actions for high-dependency positions]
- Monitor: [positions to watch]
- Research: [areas needing further investigation]

## Stopping Points

- After Step 2 (direct exposure calculated): present direct exposure findings before running supply chain analysis
- After Step 4 (corroboration complete): present full risk assessment for review before issuing recommendations

## Output

A comprehensive risk assessment with direct exposure, indirect supply chain exposure (with decay), corroborating evidence, and prioritised recommendations.
