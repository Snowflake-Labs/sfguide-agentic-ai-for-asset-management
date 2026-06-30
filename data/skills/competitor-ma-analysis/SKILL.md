---
name: competitor-ma-analysis
description: Use this skill when the user asks about competitor acquisition opportunities, divisional sales, or strategic M&A. Also use for "model acquiring [target]", "EPS accretion analysis", or any question about evaluating an M&A target that requires combining news, geographic segment data, and financial simulation.
---

# Competitor M&A Analysis

## When to Activate

Trigger when user asks about: competitor acquisition opportunity, "BlackRock European division", divisional sale, strategic M&A, "model acquiring [target]"

## 5-Step Workflow

### Step 1: Search for News

Tool: `search_external_docs`

Query: "[Competitor] [division] sale acquisition"

Extract: News context, timing, reported details

### Step 2: Get Geographic/Segment Revenue Data

Tool: `sec_segments_analyzer` (CRITICAL: NOT financial_analyzer)

Query: "[Competitor] revenue by geography" or "[Competitor] European revenue by year"

Extract: Regional revenue, breakdown, trend over years

NOTE: This is the primary tool for divisional/regional financial data. financial_analyzer only has consolidated totals.

### Step 3: Get Total Company Context

Tool: `financial_analyzer`

Query: "[Competitor] total revenue net income"

Extract: Overall company size for context

### Step 4: Run M&A Simulation

Tool: `ma_simulation`

Inputs: target_aum (estimate from segment data), target_revenue (from sec_segments_analyzer), cost_synergy_pct

Extract: EPS accretion, synergies, risk assessment

### Step 5: Synthesise

- Summarise opportunity (from news)
- Present REGIONAL financial metrics (from sec_segments_analyzer)
- Compare to total company size (from financial_analyzer)
- Show M&A simulation results
- Provide strategic recommendation

## Strategic Memo Format

If user requests a memo:
1. Executive Summary (key finding)
2. Background (context)
3. Key Findings (data points)
4. Financial Impact (simulation results)
5. Recommendation
6. Next Steps

## Stopping Points

- After Step 2 (segment data gathered): confirm target division and financial scope with user
- After Step 4 (M&A simulation complete): present deal summary for approval before drafting memo

## Output

A strategic M&A analysis memo following the Strategic Memo Format above, with simulation results and recommendation.
