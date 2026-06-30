# Unstructured Data Generation

Template-based document generation for SAM demo corpus tables.

## Architecture

**Pipeline-Only Architecture**:
- PDF types: Templates → Export PDFs → Upload to stages → Pipeline parses/chunks
- Non-PDF types: Templates → Write to RAW tables → Stream triggers corpus build
- Real data (transcripts): Load to RAW → Stream triggers processing pipeline

**No LLM generation** - all content from curated templates in `content_library/`.

## Document Types

| Document Type | Linkage | Word Count | Corpus Table |
|---------------|---------|------------|--------------|
| **Security-Level** ||||
| broker_research | SecurityID + IssuerID | 700-1,200 | BROKER_RESEARCH_CORPUS |
| press_releases | SecurityID + IssuerID | 250-400 | PRESS_RELEASES_CORPUS |
| **Security-Level (Real)** ||||
| company_event_transcripts | PRIMARY_TICKER + CIK | ~512 tokens | COMPANY_EVENT_TRANSCRIPTS_CORPUS |
| **Issuer-Level** ||||
| ngo_reports | IssuerID only | 400-800 | NGO_REPORTS_CORPUS |
| engagement_notes | IssuerID only | 150-300 | ENGAGEMENT_NOTES_CORPUS |
| **Global** ||||
| policy_docs | None | 800-1,500 | POLICY_DOCS_CORPUS |
| sales_templates | None | 800-1,500 | SALES_TEMPLATES_CORPUS |

## Entity Selection Pattern

```python
from demo_helpers import get_demo_company_priority_sql

def get_entities_for_doc_type(session, doc_type, test_mode=False):
    """Get entities prioritized to match portfolio holdings."""
    
    # ✅ CORRECT: Use config-driven priority
    securities = session.sql(f"""
        SELECT s.SecurityID as id, s.Ticker
        FROM SAM_DEMO.CURATED.DIM_SECURITY s
        JOIN SAM_DEMO.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
        WHERE s.AssetClass = 'Equity'
        ORDER BY 
            CASE 
                {get_demo_company_priority_sql()}
                ELSE 10
            END,
            s.Ticker
        LIMIT {coverage_count}
    """).collect()
    return [{'id': s['ID']} for s in securities]
```

**Never hardcode tickers in SQL**:
```python
# ❌ WRONG
CASE WHEN s.Ticker = 'AAPL' THEN 1 END

# ✅ CORRECT
CASE {get_demo_company_priority_sql()} END
```

## Real Data: Company Event Transcripts

**Source**: `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES`

**Event Types**:
- Earnings Calls
- Annual General Meetings
- M&A Announcements
- Investor / Analyst Days

**Pipeline Flow**:
1. `load_raw_table()` → `COMPANY_EVENT_TRANSCRIPTS_RAW`
2. `TRANSCRIPTS_SPEAKER_STREAM` + `TRANSCRIPTS_CORPUS_STREAM` detect inserts (one per consumer)
3. `TRANSCRIPTS_SPEAKER_MAPPING` task runs AI_COMPLETE
4. `TRANSCRIPTS_CORPUS_BUILD` task chunks and enriches

## AI_COMPLETE Syntax

```sql
AI_COMPLETE(
    model => 'claude-3-5-sonnet',
    prompt => CONCAT('Identify speakers in: ', transcript_text),
    response_format => {
        'type': 'json',
        'schema': {
            'type': 'object',
            'properties': {
                'speakers': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'role': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
):speakers
```

**Key Syntax**:
- Named parameters: `model =>`, `prompt =>`, `response_format =>`
- Access nested results: `:speakers`, `:result_array`
- In Python f-strings, escape braces: `{{` and `}}`

## Corpus Table Schema

All corpus tables use standardized columns:

```sql
CREATE TABLE {TYPE}_CORPUS (
    DOCUMENT_ID VARCHAR(100) PRIMARY KEY,
    DOCUMENT_TITLE VARCHAR(500),
    DOCUMENT_TYPE VARCHAR(50),
    SecurityID BIGINT,           -- NULL for global docs
    IssuerID BIGINT,             -- NULL for global docs
    PUBLISH_DATE DATE,
    LANGUAGE VARCHAR(10) DEFAULT 'en',
    DOCUMENT_TEXT TEXT
);
```

## Agent-Document Alignment

| Agent | Primary Documents |
|-------|-------------------|
| pm_cockpit | broker_research, company_events, press_releases |
| research_copilot | broker_research, company_events |
| risk_compliance | ngo_reports, engagement_notes, policy_docs |
| sales_advisor | sales_templates, philosophy_docs |

## Quality Standards

- Realistic industry language (UK English)
- Word counts within specified ranges
- Proper SecurityID/IssuerID linkage
- Clean titles, consistent formatting
- Content supports specific agent scenarios
