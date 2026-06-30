# Agent Testing

Validation patterns and test queries for Snowflake Intelligence agents.

## Pre-Creation Checks

Before creating an agent, verify dependencies:

```sql
-- Semantic views exist
SHOW SEMANTIC VIEWS IN SAM_DEMO.AI;

-- Search services exist
SHOW CORTEX SEARCH SERVICES IN SAM_DEMO.AI;

-- Underlying tables have data
SELECT COUNT(*) FROM SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR;
SELECT COUNT(*) FROM SAM_DEMO.CURATED.BROKER_RESEARCH_CORPUS;
```

## Test Queries by Agent Type

### Portfolio Manager Co-Pilot
```
✅ "What are my top 10 holdings in SAM Global Thematic Growth?"
✅ "Show sector allocation for SAM Technology & Infrastructure"
✅ "Which positions exceed 6% concentration?"
✅ "Compare my technology holdings to benchmark"

❌ "top holdings" (missing portfolio name)
❌ "tech portfolio" (ambiguous name)
```

### Research Copilot
```
✅ "What is the latest research on Apple and Microsoft?"
✅ "Summarize analyst views on NVIDIA's AI business"
✅ "What did management say about margins in the last earnings call?"

❌ "research on tech" (too generic)
❌ "latest news" (not in corpus)
```

### Risk & Compliance
```
✅ "Check ESG risks in SAM ESG Leaders Global Equity"
✅ "Which holdings have ESG scores below BBB?"
✅ "Are there any environmental controversies in our portfolios?"

❌ "ESG check" (missing portfolio)
```

### Risk & Compliance
```
✅ "Are there any mandate breaches in SAM AI & Digital Innovation?"
✅ "Check concentration compliance across all portfolios"
✅ "What are our current policy violations?"
```

## Response Validation

### Required Elements

| Element | Check |
|---------|-------|
| Data freshness | "As of DD MMM YYYY" present |
| Tables | Used for >4 items |
| Citations | Source and date for documents |
| Warnings | ⚠️ for 6.5-7.0%, 🚨 for >7.0% |
| Disclaimer | Demo disclaimer at end |

### Example Valid Response
```
Your top 5 holdings in SAM Technology & Infrastructure:

| Ticker | Company | Weight | Value |
|--------|---------|--------|-------|
| AAPL   | Apple   | 8.2%   | £41M  |
| MSFT   | Microsoft | 7.4% | £37M  |
...

⚠️ CONCENTRATION: 2 positions exceed 6.5% threshold

As of 31 Dec 2024 market close.

---
*DEMO DISCLAIMER: Synthetic data for demonstration only.*
```

## Common Test Failures

### "Portfolio not found"
- **Cause**: Partial or wrong portfolio name
- **Fix**: Use full name with "SAM" prefix
- **Valid names**: SAM Technology & Infrastructure, SAM Global Thematic Growth, SAM ESG Leaders Global Equity

### "No results from semantic view"
- **Cause**: Empty underlying tables or broken relationships
- **Debug**:
  ```sql
  -- Check table has data
  SELECT COUNT(*) FROM SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR;
  
  -- Check semantic view directly
  SELECT * FROM SEMANTIC_VIEW(
      SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
      METRICS TOTAL_MARKET_VALUE
      DIMENSIONS PORTFOLIONAME
  ) LIMIT 5;
  ```

### "Search returns no relevant results"
- **Cause**: Empty corpus or poor search terms
- **Debug**:
  ```sql
  -- Check corpus has documents
  SELECT COUNT(*), DOCUMENT_TYPE FROM SAM_DEMO.CURATED.BROKER_RESEARCH_CORPUS
  GROUP BY DOCUMENT_TYPE;
  
  -- Test search directly
  SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
      'SAM_DEMO.AI.SAM_BROKER_RESEARCH',
      '{"query": "Apple technology", "limit": 3}'
  );
  ```

### "Duplicate holdings in response"
- **Cause**: Not filtering to latest date
- **Fix**: Ensure orchestration instructions include "filter to most recent date"

## Agent Health Check Script

```sql
-- 1. Check agent exists
SHOW AGENTS IN SNOWFLAKE_INTELLIGENCE.AGENTS;

-- 2. Verify tools
-- Semantic views
DESCRIBE SEMANTIC VIEW SAM_DEMO.AI.SAM_PORTFOLIO_VIEW;

-- Search services
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'SAM_DEMO.AI.SAM_BROKER_RESEARCH',
    '{"query": "test", "limit": 1}'
);

-- 3. Verify data freshness
SELECT MAX(HoldingDate) FROM SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR;
```

## Performance Benchmarks

| Query Type | Expected Time |
|------------|--------------|
| Simple holdings query | < 5 seconds |
| Sector allocation | < 10 seconds |
| Research synthesis | < 15 seconds |
| Multi-tool complex query | < 30 seconds |

If queries exceed these times, check warehouse size and query complexity.

## Formal Agent Evaluations

Automated evaluation datasets are created as part of the build pipeline. These use Snowflake's native Agent Evaluations with grounded questions and data-validated ground truth.

### Build Integration

Eval datasets are created automatically after agents during `--scope agents` or `--scope ai`:

```bash
python python/main.py --connection-name <conn> --scope agents --scenarios portfolio_copilot,research_copilot
```

To rebuild eval datasets only (without recreating agents):

```bash
python python/main.py --connection-name <conn> --scope eval --scenarios portfolio_copilot
```

### Evaluation Metrics

| Metric | Description | Requires Ground Truth |
|--------|-------------|----------------------|
| `answer_correctness` | Semantic match of final answer | Yes |
| `logical_consistency` | Internal consistency of response | No |

### Question Categories

| Category | % | Purpose |
|----------|---|---------|
| `core_use_case` | 40% | Primary agent capabilities |
| `tool_routing` | 25% | Correct tool selection |
| `edge_case` | 15% | Error handling, missing data |
| `ambiguous` | 10% | Vague or multi-tool queries |

### Ground Truth Types

- **Static**: Deterministic values from config (ESG overrides, supply chain, compliance rules)
- **Dynamic**: Hydrated at build time by querying actual data (holdings, prices, financials)

Dynamic questions use `{max_date}` placeholders and `validation_query` SQL that runs during build to populate ground truth with real values.

### Eval Dataset Tables

Located in `SAM_DEMO.AI`:

```sql
SELECT COUNT(*), CATEGORY
FROM SAM_DEMO.AI.EVAL_DATASET_AM_PORTFOLIO_COPILOT
GROUP BY CATEGORY;

SELECT INPUT_QUERY, GROUND_TRUTH
FROM SAM_DEMO.AI.EVAL_DATASET_AM_RESEARCH_COPILOT
LIMIT 5;
```

### Running an Evaluation

Use Cortex Code's agent evaluation skill or call programmatically:

```python
from ai.evaluations import run_evaluation
run_name = run_evaluation(session, 'portfolio_copilot', connection_name='my_conn')
```

### Viewing Results

```sql
SELECT *
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
    'SAM_DEMO', 'AI', 'AM_portfolio_manager_copilot', 'CORTEX AGENT', '<RUN_NAME>'
))
ORDER BY TIMESTAMP DESC;
```

### Adding Evaluations for a New Agent

1. Add entry to `AGENT_EVALUATIONS` in `config.py`
2. Run `python main.py --scope eval --scenarios <scenario_name>`
3. The framework handles table creation, question hydration, and dataset registration
