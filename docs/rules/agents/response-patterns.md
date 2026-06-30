# Agent Response Patterns

Patterns for structuring agent response instructions with style, presentation, and format guidance.

## Response Instructions Template

```yaml
Style:
- Tone: Professional, data-driven, action-oriented
- Lead With: Direct answer first, then supporting analysis
- Terminology: UK English ('shares' not 'stocks', 'portfolios', 'holdings')
- Precision: Percentages to 1 decimal, currency in millions with £

Presentation:
- Tables: Use for lists (>4 items), comparisons, breakdowns
- Bar Charts: Use for allocations, distributions
- Line Charts: Use for time series, trends
- Data Freshness: Always include "As of DD MMM YYYY market close"
```

## Response Structure Templates

### Holdings Questions
```
Template: "[Count/summary] + [Table] + [Flags] + [Total]"

Example: "Your portfolio has 10 top holdings totalling 65.3%:
| Ticker | Company | Weight | Market Value |
|--------|---------|--------|-------------|
| AAPL   | Apple   | 8.2%   | £41.2M      |

⚠️ CONCENTRATION WARNINGS: 3 positions exceed 6.5%
As of 31 Dec 2024 market close."
```

### Concentration Analysis
```
Template: "[Policy statement] + [Flagged table] + [Severity] + [Recommendations]"

Example: "Per Concentration Risk Policy (6.5% warning, 7.0% breach):
| Position | Weight | Status | Action Required |
|----------|--------|--------|-----------------|
| Apple    | 8.2%   | 🚨 BREACH | Immediate reduction |"
```

### Research Questions
```
Template: "[Summary] + [Quoted excerpts with citations] + [Synthesis]"

Example: "Goldman Sachs (15 Jan 2025): 'Azure AI services growing 150%+ YoY.'"
```

## Flagging Requirements

| Agent Type | Threshold | Flag |
|------------|-----------|------|
| Portfolio | >6.5% | ⚠️ CONCENTRATION WARNING |
| Compliance | >7.0% | 🚨 BREACH |
| Compliance | 6.5-7.0% | ⚠️ WARNING |

## Demo Disclaimer Requirement

All agent responses MUST end with:
```
---
*DEMO DISCLAIMER: This analysis uses synthetic data for demonstration purposes only. Not intended for actual investment decisions.*
```

## UK English Terminology

| US English | UK English |
|------------|------------|
| stocks | shares |
| mutual funds | portfolios |
| 401k | pension |
