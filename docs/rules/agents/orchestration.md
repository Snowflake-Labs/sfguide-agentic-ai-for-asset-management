# Agent Orchestration Patterns

Patterns for writing effective planning and orchestration instructions.

## Business Context Section

Always provide explicit business context before tool selection:

```yaml
Business Context:

Organization:
- Simulated Asset Management (SAM), multi-asset investment firm
- £2.5B AUM across 10 active investment strategies
- FCA-regulated with quarterly compliance reviews
- Data refreshes daily at market close (4 PM ET)

Key Thresholds:
- Concentration: 6.5% warning, 7.0% breach
- ESG: Minimum BBB for ESG portfolios
- Liquidity: Minimum 7-day exit for growth strategies

Strategies:
- Growth: 30-50 holdings, technology focus
- Value: 60-100 holdings, defensive focus
- ESG: Screening + ESG floors
```

## Tool Selection Logic

### Multi-Tool Agent
```
1. Analyze query for sub-questions
2. Classify each:
   - QUANTITATIVE: Numbers, rankings, charts → Analyst tool
   - QUALITATIVE: Opinions, summaries, "why" → Search tool
3. For mixed queries: Analyst first, then Search with context
4. Synthesize outputs into coherent response
```

### Single Analyst Agent
```
1. Identify data requirements from query
2. Use analyst tool for all calculations
3. Break complex queries into sub-questions
4. Generate charts when beneficial
5. State limitations if data unavailable
```

### Search-Only Agent
```
1. Identify document types and search terms
2. Choose appropriate search service(s)
3. For multi-faceted queries, search multiple types
4. Synthesize findings with citations
5. Suggest alternatives if no results
```

## Workflow Examples

### Concentration Risk Check
```yaml
Trigger: "Which positions need attention?"

Steps:
1. Get Thresholds
   Tool: search_policies
   Query: "concentration risk limits"
   Extract: 6.5% warning, 7.0% breach

2. Get Holdings
   Tool: quantitative_analyzer
   Query: "All positions with weights for latest date"

3. Apply Rules
   - 6.5-7.0%: "⚠️ WARNING"
   - >7.0%: "🚨 BREACH"

4. Response Format:
   | Ticker | Weight | Status |
   |--------|--------|--------|
   | AAPL   | 8.2%   | 🚨 BREACH |
   
   Recommendations by severity level
```

### Research Synthesis
```yaml
Trigger: "What's the outlook for Microsoft?"

Steps:
1. Search Research
   Tool: search_broker_research
   Query: "Microsoft outlook growth AI Azure"

2. Search Events
   Tool: search_company_events
   Query: "Microsoft earnings guidance"

3. Synthesize:
   - Analyst consensus (buy/hold/sell count)
   - Key themes across sources
   - Quoted excerpts with citations
```

## Error Handling

### Entity Not Found
```yaml
Detection: No results for specified name
Recovery:
  1. Try with/without "SAM" prefix
  2. Query available entities
  3. Present alternatives
Message: "Couldn't find '[name]'. Did you mean: [alternatives]?"
```

### No Search Results
```yaml
Detection: Relevance < 0.3 for all results
Recovery:
  1. Rephrase with broader terms
  2. Try alternative document types
  3. State limitation
Message: "No research found on [topic]. Try [alternatives]?"
```

### Date Ambiguity
```yaml
Detection: "recent", "current", "latest"
Recovery:
  - "current/latest" → MAX(HoldingDate)
  - "recent" → last 30 days (state assumption)
Message: "Using last 30 days for 'recent' (as of [date])"
```

## Common Pitfalls

### Assumed Context (Bad)
```yaml
Bad: "Check for concentration violations"
Bad: "Flag positions exceeding limits"
```
Agent doesn't know the thresholds!

### Fixed (Good)
```yaml
Good: "Concentration: 6.5% warning, 7.0% breach per policy"
```

### Implicit Workflows (Bad)
```yaml
Bad: "Use appropriate tools"
Bad: "Combine data from sources"
```

### Fixed (Good)
```yaml
Good: "Workflow:
1. Get thresholds from search_policies
2. Get holdings from quantitative_analyzer
3. Apply thresholds, flag positions
4. Format response with citations"
```

## Checklist

- [ ] Business context with specific thresholds
- [ ] Tool selection criteria (quantitative vs qualitative)
- [ ] 2-3 complete workflow examples
- [ ] Error handling for common scenarios
- [ ] Query patterns for tool matching
