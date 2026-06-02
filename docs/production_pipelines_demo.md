# Production-like Pipelines Demo Guide

This guide explains how to demonstrate the production-like unstructured data pipelines in the SAM demo.

## Overview

The SAM demo includes production-style Snowflake pipelines that show how real asset managers might process unstructured content:

- **PDF Ingestion Pipelines**: File-based processing using stages, directory tables, streams, and task DAGs
- **Corpus Build Pipelines**: Table transformation with intelligent chunking
- **Transcripts Pipeline**: Real earnings call processing with speaker identification
- **SEC Filings Pipeline**: Real 10-K/10-Q/8-K text refresh

All pipelines are created **SUSPENDED** by default, allowing you to:
1. Show the DAG structure in Snowsight without accidental execution
2. Execute on-demand for live demos
3. Explain scheduling and automation concepts

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PDF Ingestion Pipeline                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐ │
│  │  Stage   │────▶│  Stream  │────▶│  Parse   │────▶│   Chunk    │ │
│  │(RAW.PDF) │     │(on dir)  │     │  Task    │     │   Task     │ │
│  └──────────┘     └──────────┘     └──────────┘     └────────────┘ │
│       │                                                    │        │
│       │ PUT file.pdf                                       │        │
│       ▼                                                    ▼        │
│  ┌──────────┐                                       ┌────────────┐ │
│  │Directory │                                       │  CORPUS    │ │
│  │  Table   │                                       │  (chunked) │ │
│  └──────────┘                                       └────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Finding Pipelines in Snowsight

### View Task DAGs

1. Navigate to **Data** → **Databases** → **SAM_DEMO**
2. Expand **RAW** schema
3. Click on **Tasks** in the left panel
4. Look for tasks starting with:
   - `PDF_INTERNAL_PIPELINE_ROOT`
   - `PDF_EXTERNAL_PIPELINE_ROOT`
   - `TRANSCRIPTS_PIPELINE_ROOT`

5. Click on a root task to see the DAG visualization

### View Stages and Streams

1. In SAM_DEMO → RAW schema
2. Stages: `PDF_INTERNAL_STAGE`, `PDF_EXTERNAL_STAGE`
3. Streams: `PDF_INTERNAL_STREAM`, `PDF_EXTERNAL_STREAM`

## Demo Scenarios

### Scenario 1: Show Pipeline Structure (No Execution)

**Goal**: Explain the architecture without running anything

1. Open Snowsight → Data → Databases → SAM_DEMO → RAW → Tasks
2. Click on `PDF_INTERNAL_PIPELINE_ROOT`
3. Show the DAG diagram (Root → Parse → Chunk)
4. Explain:
   - "The root task checks for new files every 5 minutes"
   - "When files are detected via the stream, parsing begins"
   - "AI_PARSE_DOCUMENT extracts text from PDFs"
   - "Conditional chunking only splits documents > 512 tokens"
5. Show task is **Suspended** (no unintended execution)

### Scenario 2: Live Pipeline Execution

**Goal**: Demonstrate real-time document processing

```sql
-- Step 1: Check current state
SELECT * FROM SAM_DEMO.RAW.PDF_INTERNAL_RAW LIMIT 5;
SELECT COUNT(*) FROM SAM_DEMO.CURATED.PDF_INTERNAL_CORPUS;

-- Step 2: Upload a sample PDF (if needed)
-- PUT file:///path/to/sample.pdf @SAM_DEMO.RAW.PDF_INTERNAL_STAGE;

-- Step 3: Refresh the stage directory
ALTER STAGE SAM_DEMO.RAW.PDF_INTERNAL_STAGE REFRESH;

-- Step 4: Check stream for new files
SELECT * FROM SAM_DEMO.RAW.PDF_INTERNAL_STREAM;

-- Step 5: Enable the task graph
SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT');

-- Step 6: Execute the pipeline
EXECUTE TASK SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT;

-- Step 7: Monitor progress
SELECT NAME, STATE, SCHEDULED_TIME, COMPLETED_TIME, ERROR_MESSAGE
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE NAME LIKE 'PDF_INTERNAL%'
ORDER BY SCHEDULED_TIME DESC
LIMIT 10;

-- Step 8: Check results
SELECT * FROM SAM_DEMO.RAW.PDF_INTERNAL_RAW ORDER BY PARSED_AT DESC LIMIT 5;
SELECT * FROM SAM_DEMO.CURATED.PDF_INTERNAL_CORPUS ORDER BY CREATED_AT DESC LIMIT 10;

-- Step 9: Suspend the tasks
ALTER TASK SAM_DEMO.RAW.PDF_INTERNAL_CHUNK SUSPEND;
ALTER TASK SAM_DEMO.RAW.PDF_INTERNAL_PARSE SUSPEND;
ALTER TASK SAM_DEMO.RAW.PDF_INTERNAL_PIPELINE_ROOT SUSPEND;
```

### Scenario 3: Explain Chunking Strategy

**Goal**: Show why conditional chunking matters for RAG

```sql
-- Show documents with their token counts
SELECT 
    DOCUMENT_TITLE,
    TOKEN_COUNT,
    CASE WHEN TOKEN_COUNT > 512 THEN 'Chunked' ELSE 'Single' END as STRATEGY,
    LENGTH(DOCUMENT_TEXT) as TEXT_LENGTH
FROM SAM_DEMO.CURATED.BROKER_RESEARCH_CORPUS
ORDER BY TOKEN_COUNT DESC
LIMIT 20;

-- Show a chunked document
SELECT 
    SOURCE_DOCUMENT_ID,
    CHUNK_INDEX,
    DOCUMENT_TITLE,
    TOKEN_COUNT,
    LEFT(DOCUMENT_TEXT, 200) as PREVIEW
FROM SAM_DEMO.CURATED.BROKER_RESEARCH_CORPUS
WHERE SOURCE_DOCUMENT_ID IN (
    SELECT SOURCE_DOCUMENT_ID 
    FROM SAM_DEMO.CURATED.BROKER_RESEARCH_CORPUS 
    GROUP BY SOURCE_DOCUMENT_ID 
    HAVING COUNT(*) > 1
    LIMIT 1
)
ORDER BY CHUNK_INDEX;
```

**Talking points**:
- "Short documents stay as single chunks - no unnecessary fragmentation"
- "Long documents are split into ~512 token chunks with 200 char overlap"
- "Overlap ensures context continuity for semantic search"
- "This is the same pattern used by major RAG implementations"

### Scenario 4: Real Transcripts with Speaker Context

**Goal**: Show enriched transcript processing

```sql
-- Show transcript chunks with speaker metadata
SELECT 
    DOCUMENT_TITLE,
    SEGMENT_INDEX,
    CHUNK_INDEX,
    LEFT(DOCUMENT_TEXT, 500) as PREVIEW
FROM SAM_DEMO.CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS
WHERE DOCUMENT_TITLE LIKE '%Earnings Call%'
ORDER BY TRANSCRIPT_ID, SEGMENT_INDEX, CHUNK_INDEX
LIMIT 10;
```

**Talking points**:
- "Each chunk includes speaker context in the header"
- "AI_COMPLETE identifies speakers (CEO, CFO, Analyst, etc.)"
- "This enables questions like 'What did the CFO say about margins?'"

## Troubleshooting

### Tasks Won't Execute

```sql
-- Check task state
SHOW TASKS LIKE 'PDF_INTERNAL%' IN SCHEMA SAM_DEMO.RAW;

-- Check stream has data
SELECT SYSTEM$STREAM_HAS_DATA('SAM_DEMO.RAW.PDF_INTERNAL_STREAM');

-- Refresh stage directory
ALTER STAGE SAM_DEMO.RAW.PDF_INTERNAL_STAGE REFRESH;
```

### Parse Errors

```sql
-- Check for parse failures
SELECT FILE_PATH, PARSE_STATUS, PARSE_ERROR, PARSED_AT
FROM SAM_DEMO.RAW.PDF_INTERNAL_RAW
WHERE PARSE_STATUS != 'PARSED';
```

### Reset Pipeline State

```sql
-- Clear parsed data (start fresh)
TRUNCATE TABLE SAM_DEMO.RAW.PDF_INTERNAL_RAW;
TRUNCATE TABLE SAM_DEMO.CURATED.PDF_INTERNAL_CORPUS;

-- Refresh stage to re-process all files
ALTER STAGE SAM_DEMO.RAW.PDF_INTERNAL_STAGE REFRESH;
```

## SQL Scripts

Human-readable SQL scripts for all pipelines are available in:
`am_ai_demo/sql/pipelines/`

These can be opened in Snowsight worksheets for detailed walkthrough:
- `01_pdf_internal_pipeline.sql`
- `02_pdf_external_pipeline.sql`
- `03_corpus_build_example.sql`
- `04_transcripts_pipeline.sql`
- `05_sec_filings_pipeline.sql`
