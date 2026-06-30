---
name: data-lineage-explanation
description: Explains where data comes from, how metrics are calculated, and traces data lineage through the pipeline. Use when the user asks "where does this data come from?", "how is X calculated?", or "what does this metric mean?".
---

# Data Lineage Explanation

## When to Activate

Trigger when the user asks:
- "Where does this data come from?"
- "How is [metric] calculated?"
- "What does [field] mean?"
- "Explain the data source for..."
- "What's the lineage of..."

## Workflow

1. Identify the semantic field name from the previous query (e.g., TOTAL_MARKET_VALUE, FIRM_AUM, AVG_RATING)

2. Map the Cortex Analyst tool that produced the data to its semantic view:

| Tool Name | Semantic View |
|-----------|--------------|
| quantitative_analyzer | SAM_DEMO.AI.SAM_ANALYST_VIEW |
| financial_analyzer | SAM_DEMO.AI.SAM_SEC_FINANCIALS_VIEW |
| implementation_analyzer | SAM_DEMO.AI.SAM_IMPLEMENTATION_VIEW |
| supply_chain_analyzer | SAM_DEMO.AI.SAM_SUPPLY_CHAIN_VIEW |
| stock_prices | SAM_DEMO.AI.SAM_STOCK_PRICES_VIEW |
| sec_financials | SAM_DEMO.AI.SAM_SEC_FINANCIALS_VIEW |
| executive_kpi_analyzer | SAM_DEMO.AI.SAM_EXECUTIVE_VIEW |
| factor_model_analyzer | SAM_DEMO.AI.SAM_FACTOR_MODEL_VIEW |
| regime_analyzer | SAM_DEMO.AI.SAM_REGIME_VIEW |

3. Call `explain_data_origin` with the semantic view name and field name

4. Your response MUST use ONLY information from the tool output:
   - Describe sources in business-friendly terms with the fully qualified object name in parentheses
   - If the tool returns view_definitions with SQL, summarise the transformation logic in plain language
   - Do NOT add refresh times, calculation details, currency, units, or any other facts from your own knowledge

## Response Template

**[FIELD_NAME]** is calculated as [plain language description of semantic_expression], drawn from [business description of physical_table] ([fully qualified table name]).

**Data lineage** ([N] levels upstream):
- [Description of depth 1 source] ([table name]) feeds into the [primary table]
- [Description of depth 2 sources] feed into [depth 1 table]
- [Continue for available depths]

## Stopping Points

- This is a utility skill. No stopping points needed — the response is generated in a single pass from tool output.

## Output

A structured lineage explanation following the Response Template above, using ONLY data from `explain_data_origin` tool output.
