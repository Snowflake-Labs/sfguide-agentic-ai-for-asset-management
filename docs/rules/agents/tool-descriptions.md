# Agent Tool Descriptions

Best practices for writing effective tool descriptions that guide accurate tool selection.

## Required Elements

Every tool description should include:

1. **Data Coverage**: Record counts, refresh frequency, history range
2. **When to Use**: 3+ specific query examples
3. **When NOT to Use**: 3+ anti-patterns with alternatives
4. **Query Tips**: Best practices for effective queries

## Cortex Analyst Tool Template

```yaml
Tool Name: quantitative_analyzer
Type: Cortex Analyst
Semantic View: SAM_DEMO.AI.SAM_PORTFOLIO_VIEW

Description: |
  Analyzes portfolio holdings, position weights, sector allocations, and mandate 
  compliance for SAM investment portfolios.
  
  Data Coverage:
  - Historical: 12 months of position and transaction history
  - Current: End-of-day holdings updated daily at 4 PM ET
  - Sources: DIM_SECURITY, DIM_PORTFOLIO, FACT_POSITION_DAILY_ABOR
  - Records: 14,000+ real securities, 10 portfolios, 27,000+ holdings
  
  When to Use:
  - Questions about portfolio holdings, weights, and composition
  - Concentration analysis and position-level risk metrics
  - Sector/geographic allocation and benchmark comparisons
  - Questions like: "What are my top holdings?", "Show sector allocation"
  
  When NOT to Use:
  - Real-time intraday positions (use market data feed)
  - Individual company financial analysis (use sec_financials)
  - Document content questions (use search_broker_research)
  
  Query Best Practices:
  1. Be specific about portfolio names:
     ✅ "SAM Technology & Infrastructure portfolio"
     ❌ "tech portfolio" (ambiguous)
  
  2. Filter to latest date for current holdings:
     ✅ "most recent holding date" or "latest positions"
     ❌ All dates without filter (returns historical duplicates)
```

## Cortex Search Tool Template

```yaml
Tool Name: search_broker_research
Type: Cortex Search
Service: SAM_DEMO.AI.SAM_BROKER_RESEARCH

Description: |
  Searches broker research reports and analyst notes for investment opinions, 
  ratings, price targets, and market commentary on securities.
  
  Data Sources:
  - Document Types: Broker research reports, analyst initiations, sector updates
  - Update Frequency: New reports added daily
  - Historical Range: Last 18 months of research coverage
  - Typical Count: ~200 reports covering major securities
  
  When to Use:
  - Questions about analyst views, investment ratings, price targets
  - Qualitative research synthesis and market commentary
  - Sector themes and investment thesis development
  - Queries like: "What do analysts say about Microsoft's AI strategy?"
  
  When NOT to Use:
  - Portfolio holdings questions (use quantitative_analyzer)
  - Financial statement data (use sec_financials)
  - Quantitative comparisons across securities (use Cortex Analyst)
  
  Search Query Best Practices:
  1. Use specific company names and topics:
     ✅ "NVIDIA artificial intelligence GPU data center growth"
     ❌ "tech growth" (too generic)
  
  2. Include investment-relevant keywords:
     ✅ "Apple iPhone revenue outlook analyst estimate rating"
     ❌ "Apple news" (too broad)
  
  3. Handle low relevance (<0.5):
     - Rephrase with more specific terms
     - Try synonyms and expand acronyms
```

## SEC Data Tools

### Stock Prices
```yaml
Tool Name: stock_prices
Semantic View: SAM_DEMO.AI.SAM_MARKET_VIEW

Description: |
  Analyzes daily stock prices (OHLCV) from Nasdaq.
  
  Data Coverage:
  - Records: 5.2M+ daily price records
  - Companies: ~50 with ticker linkage
  - History: 2 years of daily prices
  - Metrics: Open, High, Low, Close, Volume
  
  When to Use: Historical price analysis, trend visualization, volume analysis
  When NOT to Use: Portfolio holdings (use quantitative_analyzer)
```

### SEC Financials
```yaml
Tool Name: sec_financials
Semantic View: SAM_DEMO.AI.SAM_REAL_SEC_VIEW

Description: |
  Analyzes SEC financial metrics from 10-K and 10-Q filings.
  
  Data Coverage:
  - Records: 9,400+ financial data points
  - Companies: ~39 with CIK linkage
  - History: 5 years of SEC filings
  
  When to Use: SEC-reported financials, revenue segments, geographic breakdown
  When NOT to Use: Analyst estimates, companies without SEC filings
```

## Common Pitfalls

### Generic Descriptions (Bad)
```yaml
Bad: "Gets data from the database"
Bad: "Searches documents for information"
Bad: "Analyzes portfolios"
```
**Why it fails**: Agent can't distinguish between tools

### Missing Anti-Patterns (Bad)
```yaml
Bad: "Use this tool for portfolio analytics"
```
**Why it fails**: Agent uses wrong tool for edge cases

### No Query Guidance (Bad)
```yaml
Bad: "Use this tool for data analysis"
```
**Why it fails**: Agent generates poor queries

## Good Description Checklist

- [ ] Data coverage with counts and freshness
- [ ] 3+ "When to Use" examples with sample queries
- [ ] 3+ "When NOT to Use" with alternatives
- [ ] Query tips with ✅/❌ examples
- [ ] Specific to THIS tool's unique capabilities
