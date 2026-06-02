"""
Batch Earnings Insights Generator

Uses AI_COMPLETE on earnings call transcript text to generate structured
takeaways for portfolio companies. No agent needed — direct LLM call on
known input (transcript text).

Pattern: Single INSERT...SELECT with AI_COMPLETE processes all portfolio
companies in one SQL execution.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_substep, log_info, log_detail


def create_earnings_insights_table(session: Session):
    """Create the FACT_EARNINGS_INSIGHTS table."""
    database = config.DATABASE['name']
    schema = 'CURATED'

    log_substep("Creating FACT_EARNINGS_INSIGHTS table")
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {database}.{schema}.FACT_EARNINGS_INSIGHTS (
            INSIGHT_ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
            ISSUERID NUMBER NOT NULL,
            TICKER VARCHAR(20),
            COMPANY_NAME VARCHAR(200),
            TRANSCRIPT_DATE DATE,
            DOCUMENT_TITLE VARCHAR(500),
            FISCAL_PERIOD VARCHAR(10),
            FISCAL_YEAR NUMBER,
            INSIGHT_TEXT VARCHAR(16777216),
            MODEL_USED VARCHAR(50),
            GENERATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            CONSTRAINT PK_EARNINGS_INSIGHTS PRIMARY KEY (INSIGHT_ID)
        )
    """).collect()


def seed_earnings_insights(session: Session):
    """Generate earnings insights via AI_COMPLETE for portfolio companies."""
    database = config.DATABASE['name']
    schema = 'CURATED'
    model = config.AI_SIGNAL_EXTRACTION_MODEL

    create_earnings_insights_table(session)

    log_substep("Truncating existing earnings insights")
    session.sql(f"DELETE FROM {database}.{schema}.FACT_EARNINGS_INSIGHTS").collect()

    log_substep(f"Generating earnings insights via AI_COMPLETE (model: {model})")
    session.sql(f"""
        INSERT INTO {database}.{schema}.FACT_EARNINGS_INSIGHTS
            (ISSUERID, TICKER, COMPANY_NAME, TRANSCRIPT_DATE, DOCUMENT_TITLE,
             FISCAL_PERIOD, FISCAL_YEAR, INSIGHT_TEXT, MODEL_USED)
        WITH coverage_issuers AS (
            SELECT ISSUERID FROM {database}.{schema}.DIM_COVERAGE_UNIVERSE
        ),
        latest_calls AS (
            SELECT c.ISSUERID, c.TICKER, c.COMPANY_NAME, c.PUBLISH_DATE,
                   c.DOCUMENT_TITLE, c.FISCAL_PERIOD, c.FISCAL_YEAR
            FROM {database}.{schema}.COMPANY_EVENT_TRANSCRIPTS_CORPUS c
            JOIN coverage_issuers ci ON c.ISSUERID = ci.ISSUERID
            WHERE c.EVENT_TYPE = 'Earnings Call'
            QUALIFY ROW_NUMBER() OVER (PARTITION BY c.ISSUERID ORDER BY c.PUBLISH_DATE DESC) = 1
        ),
        transcript_text AS (
            SELECT lc.ISSUERID, lc.TICKER, lc.COMPANY_NAME, lc.PUBLISH_DATE,
                   lc.DOCUMENT_TITLE, lc.FISCAL_PERIOD, lc.FISCAL_YEAR,
                   LEFT(LISTAGG(t.DOCUMENT_TEXT, '\\n') WITHIN GROUP (ORDER BY
                       CASE t.SPEAKER_ROLE
                           WHEN 'CEO' THEN 1 WHEN 'CFO' THEN 2
                           WHEN 'Chief Executive Officer' THEN 1 WHEN 'Chief Financial Officer' THEN 2
                           ELSE 3 END,
                       LENGTH(t.DOCUMENT_TEXT) DESC
                   ), 1000000) AS combined_text
            FROM latest_calls lc
            JOIN {database}.{schema}.COMPANY_EVENT_TRANSCRIPTS_CORPUS t
              ON lc.ISSUERID = t.ISSUERID AND lc.PUBLISH_DATE = t.PUBLISH_DATE AND t.EVENT_TYPE = 'Earnings Call'
            WHERE t.SPEAKER_ROLE IN ('CEO', 'CFO', 'Unknown', 'Chief Executive Officer', 'Chief Financial Officer')
              AND LENGTH(t.DOCUMENT_TEXT) > 50
            GROUP BY lc.ISSUERID, lc.TICKER, lc.COMPANY_NAME, lc.PUBLISH_DATE, lc.DOCUMENT_TITLE, lc.FISCAL_PERIOD, lc.FISCAL_YEAR
        )
        SELECT
            tt.ISSUERID, tt.TICKER, tt.COMPANY_NAME, tt.PUBLISH_DATE, tt.DOCUMENT_TITLE,
            tt.FISCAL_PERIOD, tt.FISCAL_YEAR,
            SNOWFLAKE.CORTEX.COMPLETE(
                '{model}',
                CONCAT(
                    'You are an equity research analyst. Summarise the key takeaways from this earnings call transcript for ',
                    tt.COMPANY_NAME, ' (', tt.TICKER, ') ', COALESCE(tt.FISCAL_PERIOD, ''), ' ', COALESCE(TO_VARCHAR(tt.FISCAL_YEAR), ''), '.\\n\\n',
                    'Structure your response as:\\n',
                    '## Headline Metrics\\n- Revenue, EPS vs consensus estimates (beat/miss/inline)\\n\\n',
                    '## Key Management Quotes\\n- Top 3 most impactful quotes from management\\n\\n',
                    '## Guidance & Outlook\\n- Forward guidance changes (raised/maintained/lowered)\\n- Key strategic priorities mentioned\\n\\n',
                    '## Risks & Concerns\\n- Any risks or challenges highlighted\\n\\n',
                    'Keep under 300 words. Use bullet points.\\n\\n',
                    '---\\nTranscript excerpt:\\n', tt.combined_text
                )
            ) AS insight_text,
            '{model}'
        FROM transcript_text tt
        WHERE LENGTH(tt.combined_text) > 200
    """).collect()

    count = session.sql(f"SELECT COUNT(*) AS CNT FROM {database}.{schema}.FACT_EARNINGS_INSIGHTS").collect()[0]['CNT']
    log_info(f"Generated earnings insights for {count} companies")
