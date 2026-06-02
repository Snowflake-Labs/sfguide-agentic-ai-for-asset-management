# Cortex Search Services

Creating and testing document search services for AI agents.

## Service Creation Syntax

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE <service_name>
    ON <content_column>
    ATTRIBUTES <attr1>, <attr2>, <attr3>
    WAREHOUSE = <warehouse_name>
    TARGET_LAG = '<time_period>'
    AS 
    SELECT 
        <id_column>,
        <title_column>,
        <content_column>,
        <attribute_columns>
    FROM <corpus_table>;
```

**Critical Requirements**:
- ATTRIBUTES must match SELECT columns exactly
- ON specifies the searchable content column
- WAREHOUSE is mandatory
- TARGET_LAG: '5 minutes' for demos, '1 day' for production

## Complete Example

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE SAM_DEMO.AI.SAM_BROKER_RESEARCH
    ON DOCUMENT_TEXT
    ATTRIBUTES DOCUMENT_TITLE, SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE
    WAREHOUSE = SAM_DEMO_CORTEX_WH
    TARGET_LAG = '5 minutes'
    AS 
    SELECT 
        DOCUMENT_ID,
        DOCUMENT_TITLE,
        DOCUMENT_TEXT,
        SecurityID,
        IssuerID,
        DOCUMENT_TYPE,
        PUBLISH_DATE,
        LANGUAGE
    FROM SAM_DEMO.CURATED.BROKER_RESEARCH_CORPUS;
```

## Attribute Patterns by Document Type

**Security-Specific**:
```sql
ATTRIBUTES DOCUMENT_TITLE, SecurityID, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE
```

**Global Documents**:
```sql
ATTRIBUTES DOCUMENT_TITLE, DOCUMENT_TYPE, PUBLISH_DATE, LANGUAGE
```

**ESG Documents**:
```sql
ATTRIBUTES DOCUMENT_TITLE, IssuerID, DOCUMENT_TYPE, PUBLISH_DATE, SEVERITY_LEVEL
```

## Prerequisites Check

```python
def verify_corpus_table(session, corpus_table):
    """Verify corpus table exists and has required columns."""
    columns = session.sql(f"DESCRIBE TABLE {corpus_table}").collect()
    column_names = [row['name'] for row in columns]
    
    required = ['DOCUMENT_ID', 'DOCUMENT_TITLE', 'DOCUMENT_TEXT']
    missing = [c for c in required if c not in column_names]
    
    if missing:
        print(f"❌ Missing columns: {missing}")
        return False
    return True
```

```sql
-- Check content quality
SELECT 
    COUNT(*) as total_docs,
    COUNT(CASE WHEN LENGTH(DOCUMENT_TEXT) > 100 THEN 1 END) as docs_with_content,
    AVG(LENGTH(DOCUMENT_TEXT)) as avg_content_length
FROM {corpus_table};
```

## Validation

```sql
-- 1. Verify service created
SHOW CORTEX SEARCH SERVICES IN SAM_DEMO.AI;

-- 2. Basic search test
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'SAM_DEMO.AI.SAM_BROKER_RESEARCH',
    '{"query": "technology investment outlook", "limit": 3}'
);

-- 3. Filter test
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'SAM_DEMO.AI.SAM_BROKER_RESEARCH',
    '{"query": "AI growth", "filter": {"DOCUMENT_TYPE": "broker_research"}, "limit": 2}'
);
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "Missing option WAREHOUSE" | No warehouse specified | Add `WAREHOUSE = <name>` |
| "invalid identifier" | ATTRIBUTES don't match SELECT | Align column names |
| "table not found" | Corpus table missing | Verify table exists |
| "syntax error" | Wrong AS SELECT pattern | Check column aliases |

### Search Returns No Results

1. Check corpus has content: `SELECT COUNT(*) FROM {corpus_table}`
2. Verify DOCUMENT_TEXT is populated
3. Try simpler queries first

### Poor Search Relevance

1. Ensure DOCUMENT_TEXT is clean, readable text
2. Check for encoding issues
3. Verify document language

## Agent Configuration

For Snowflake Intelligence agents:
- **Service Name**: Full path (`SAM_DEMO.AI.SAM_BROKER_RESEARCH`)
- **ID Column**: `DOCUMENT_ID`
- **Title Column**: Use SELECT alias (`DOCUMENT_TITLE`)
- **Max Results**: 3-5 for agents (balance relevance vs context)
