# Pipeline Patterns

Snowflake Tasks, Streams, and pipeline architecture for unstructured data processing.

## Architecture Overview

**Pipeline-Only Architecture**: All unstructured data flows through pipelines. No direct SQL corpus creation.

```
PDF Pipelines:    Stage → Directory Stream → Parse Task → Chunk Task → Corpus
RAW Pipelines:    RAW Table → Stream → Processing Task → Corpus/Target Table
```

## Pipeline Objects

### PDF Pipelines (by audience)

| Object | Internal Pipeline | External Pipeline |
|--------|-------------------|-------------------|
| Stage | `RAW.PDF_INTERNAL_STAGE` | `RAW.PDF_EXTERNAL_STAGE` |
| Stream | `RAW.PDF_INTERNAL_STREAM` | `RAW.PDF_EXTERNAL_STREAM` |
| Parse Task | `RAW.PDF_INTERNAL_PARSE` | `RAW.PDF_EXTERNAL_PARSE` |
| Chunk Task | `RAW.PDF_INTERNAL_CHUNK` | `RAW.PDF_EXTERNAL_CHUNK` |
| Corpus | `CURATED.PDF_INTERNAL_CORPUS` | `CURATED.PDF_EXTERNAL_CORPUS` |

### Real Data Pipelines

| Object | Transcripts | SEC Filings |
|--------|-------------|-------------|
| RAW Table | `RAW.COMPANY_EVENT_TRANSCRIPTS_RAW` | `RAW.SEC_FILING_TEXT_RAW` |
| Stream | `RAW.TRANSCRIPTS_SPEAKER_STREAM` / `RAW.TRANSCRIPTS_CORPUS_STREAM` | `RAW.SEC_FILINGS_RAW_STREAM` |
| Processing | `RAW.TRANSCRIPTS_SPEAKER_MAPPING` | `RAW.SEC_FILINGS_CHUNK` |
| Corpus | `CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS` | - |

## SQL Syntax Patterns

### Stage with Directory Table

```sql
-- CRITICAL: ENCRYPTION before DIRECTORY, no COMMENT
CREATE STAGE IF NOT EXISTS SAM_DEMO.RAW.PDF_INTERNAL_STAGE
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    DIRECTORY = (ENABLE = TRUE);
```

### Stream on Stage

```sql
-- No COMMENT clause supported
CREATE OR REPLACE STREAM SAM_DEMO.RAW.PDF_INTERNAL_STREAM
    ON STAGE SAM_DEMO.RAW.PDF_INTERNAL_STAGE;
```

### Task with Schedule

```sql
-- No COMMENT clause in CREATE TASK
-- Schedule must be 'N MINUTE' format
CREATE OR REPLACE TASK SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT
    WAREHOUSE = SAM_DEMO_EXECUTION_WH
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('SAM_DEMO.RAW.PDF_INTERNAL_STREAM')
    AS
    SELECT 'Pipeline triggered' AS status;
```

### Child Task (AFTER clause)

```sql
CREATE OR REPLACE TASK SAM_DEMO.RAW.PDF_INTERNAL_PARSE
    WAREHOUSE = SAM_DEMO_EXECUTION_WH
    AFTER SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT
    AS
    -- Parse logic here
```

## Valid Schedule Formats

```sql
-- ✅ Valid
SCHEDULE = '5 MINUTE'
SCHEDULE = '60 MINUTE'
SCHEDULE = '1440 MINUTE'  -- 24 hours
SCHEDULE = 'USING CRON 0 9 * * * America/New_York'

-- ❌ Invalid
SCHEDULE = '1 DAY'
SCHEDULE = '24 HOUR'
```

## Conditional Chunking

Documents chunked only if >512 tokens:

```sql
WITH docs_with_tokens AS (
    SELECT *,
        AI_COUNT_TOKENS('ai_embed', 'snowflake-arctic-embed-m-v1.5', text_column) as TOKEN_COUNT
    FROM source_table
),
short_docs AS (
    SELECT *, text_column as DOCUMENT_TEXT, 0 as CHUNK_INDEX
    FROM docs_with_tokens WHERE TOKEN_COUNT <= 512
),
long_docs AS (
    SELECT *, c.value::VARCHAR as DOCUMENT_TEXT, c.index as CHUNK_INDEX
    FROM docs_with_tokens,
    LATERAL FLATTEN(
        input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            text_column, 'markdown', 2000, 200
        )
    ) c
    WHERE TOKEN_COUNT > 512
)
SELECT * FROM short_docs UNION ALL SELECT * FROM long_docs;
```

## Task Orchestration

### Python (recommended)

```python
from create_unstructured_pipelines import run_task_graph_once

# Enable → Execute → Wait → Suspend
run_task_graph_once(session, 'SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT')
```

### Manual SQL

```sql
-- 1. Enable task graph
SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT');

-- 2. Execute root (triggers cascade)
EXECUTE TASK SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT;

-- 3. Monitor
SELECT NAME, STATE, SCHEDULED_TIME, COMPLETED_TIME
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE NAME LIKE 'PDF_INTERNAL%' ORDER BY SCHEDULED_TIME DESC;

-- 4. Suspend (children first)
ALTER TASK SAM_DEMO.RAW.PDF_INTERNAL_CHUNK SUSPEND;
ALTER TASK SAM_DEMO.RAW.PDF_INTERNAL_PARSE SUSPEND;
ALTER TASK SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT SUSPEND;
```

## Troubleshooting

### Tasks Won't Execute

```sql
-- Check task state
SHOW TASKS LIKE 'PDF_INTERNAL%' IN SCHEMA SAM_DEMO.RAW;

-- Check stream has data
SELECT SYSTEM$STREAM_HAS_DATA('SAM_DEMO.RAW.PDF_INTERNAL_STREAM');

-- Refresh stage directory (required after uploads)
ALTER STAGE SAM_DEMO.RAW.PDF_INTERNAL_STAGE REFRESH;
```

### SQL Compilation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `unexpected 'COMMENT'` | COMMENT in CREATE STAGE/STREAM/TASK | Remove COMMENT |
| `Invalid schedule` | Using 'N DAY' | Use 'N MINUTE' |
| `DIRECTORY must come after ENCRYPTION` | Wrong order | ENCRYPTION first |
