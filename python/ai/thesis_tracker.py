"""
Research Thesis Tracker Infrastructure

Creates and seeds:
- FACT_RESEARCH_THESES: Stores active and historical investment theses
- SP_UPSERT_RESEARCH_THESIS: Stored procedure for agent write-back

Pipeline stages: SCREENING -> RESEARCH -> THESIS_DRAFT -> ACTIVE -> CLOSED
Health status: GREEN (thesis intact) / AMBER (assumptions challenged) / RED (invalidated)
"""

import json
from datetime import datetime, timedelta
from snowflake.snowpark import Session
import config
from utils.logging import log_substep, log_info


def create_research_theses_table(session: Session):
    """Create the FACT_RESEARCH_THESES table."""
    database = config.DATABASE['name']
    schema = 'CURATED'

    log_substep("Creating FACT_RESEARCH_THESES table")
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {database}.{schema}.FACT_RESEARCH_THESES (
            THESIS_ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
            ISSUERID NUMBER NOT NULL,
            TICKER VARCHAR(20),
            COMPANY_NAME VARCHAR(200),
            THESIS_TITLE VARCHAR(500) NOT NULL,
            THESIS_SUMMARY VARCHAR(5000),
            RECOMMENDATION VARCHAR(20),
            CONVICTION VARCHAR(10),
            KEY_ASSUMPTIONS VARIANT,
            STAGE VARCHAR(20) NOT NULL DEFAULT 'RESEARCH',
            HEALTH_STATUS VARCHAR(10) DEFAULT 'GREEN',
            LAST_VALIDATED DATE,
            VALIDATION_NOTES VARCHAR(2000),
            ANALYST_NAME VARCHAR(100) DEFAULT 'David Chen',
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            CLOSED_REASON VARCHAR(200),
            ENTRY_PRICE NUMBER(12,2),
            TARGET_PRICE NUMBER(12,2),
            STOP_LOSS NUMBER(12,2),
            SUPPORTING_DOCS VARIANT,
            CONSTRAINT PK_RESEARCH_THESES PRIMARY KEY (THESIS_ID)
        )
    """).collect()


def create_upsert_procedure(session: Session):
    """Create stored procedure for agent write-back."""
    database = config.DATABASE['name']

    log_substep("Creating SP_UPSERT_RESEARCH_THESIS procedure")
    session.sql(f"""
        CREATE OR REPLACE PROCEDURE {database}.AI.SP_UPSERT_RESEARCH_THESIS(
            p_issuerid NUMBER,
            p_ticker VARCHAR,
            p_company_name VARCHAR,
            p_thesis_title VARCHAR,
            p_thesis_summary VARCHAR,
            p_recommendation VARCHAR,
            p_conviction VARCHAR,
            p_key_assumptions VARCHAR,
            p_stage VARCHAR,
            p_health_status VARCHAR,
            p_entry_price NUMBER,
            p_target_price NUMBER,
            p_stop_loss NUMBER
        )
        RETURNS VARCHAR
        LANGUAGE SQL
        EXECUTE AS CALLER
        AS
        $$
        DECLARE
            v_thesis_id NUMBER;
            v_assumptions VARIANT;
        BEGIN
            v_assumptions := TRY_PARSE_JSON(p_key_assumptions);
            
            SELECT THESIS_ID INTO v_thesis_id
            FROM {database}.CURATED.FACT_RESEARCH_THESES
            WHERE ISSUERID = p_issuerid AND THESIS_TITLE = p_thesis_title
            LIMIT 1;

            IF (v_thesis_id IS NOT NULL) THEN
                UPDATE {database}.CURATED.FACT_RESEARCH_THESES
                SET THESIS_SUMMARY = p_thesis_summary,
                    RECOMMENDATION = COALESCE(p_recommendation, RECOMMENDATION),
                    CONVICTION = COALESCE(p_conviction, CONVICTION),
                    KEY_ASSUMPTIONS = COALESCE(v_assumptions, KEY_ASSUMPTIONS),
                    STAGE = COALESCE(p_stage, STAGE),
                    HEALTH_STATUS = COALESCE(p_health_status, HEALTH_STATUS),
                    ENTRY_PRICE = COALESCE(p_entry_price, ENTRY_PRICE),
                    TARGET_PRICE = COALESCE(p_target_price, TARGET_PRICE),
                    STOP_LOSS = COALESCE(p_stop_loss, STOP_LOSS),
                    UPDATED_AT = CURRENT_TIMESTAMP()
                WHERE THESIS_ID = v_thesis_id;
                RETURN 'Updated thesis ' || v_thesis_id::VARCHAR;
            ELSE
                INSERT INTO {database}.CURATED.FACT_RESEARCH_THESES
                    (ISSUERID, TICKER, COMPANY_NAME, THESIS_TITLE, THESIS_SUMMARY,
                     RECOMMENDATION, CONVICTION, KEY_ASSUMPTIONS, STAGE, HEALTH_STATUS,
                     ENTRY_PRICE, TARGET_PRICE, STOP_LOSS)
                VALUES
                    (p_issuerid, p_ticker, p_company_name, p_thesis_title, p_thesis_summary,
                     p_recommendation, p_conviction, v_assumptions, COALESCE(p_stage, 'RESEARCH'),
                     COALESCE(p_health_status, 'GREEN'), p_entry_price, p_target_price, p_stop_loss);
                RETURN 'Created new thesis for ' || p_company_name;
            END IF;
        END;
        $$
    """).collect()


def seed_research_theses(session: Session):
    """Seed realistic investment theses from reference_data/research_theses.yaml."""
    database = config.DATABASE['name']
    schema = 'CURATED'

    log_substep("Truncating existing theses")
    session.sql(f"DELETE FROM {database}.{schema}.FACT_RESEARCH_THESES").collect()

    today = datetime.now().date()
    theses = config.REF_DATA['research_theses']['theses']

    log_substep(f"Inserting {len(theses)} research theses")
    rows = []
    for t in theses:
        assumptions_json = json.dumps(t.get("assumptions", [])).replace("'", "''")
        docs_json = json.dumps(t.get("docs", [])).replace("'", "''")
        days_ago = t.get("validated_days_ago")
        validated = f"'{(today - timedelta(days=days_ago)).isoformat()}'" if days_ago else "NULL"
        entry = t.get("entry_price") or "NULL"
        target = t.get("target_price") or "NULL"
        stop = t.get("stop_loss") or "NULL"
        rec = f"'{t['recommendation']}'" if t.get("recommendation") else "NULL"
        conv = f"'{t['conviction']}'" if t.get("conviction") else "NULL"
        validation_notes = t.get("validation_notes", "").replace("'", "''")
        created_offset = 30 + abs(hash(t['title'])) % 60
        updated_offset = abs(hash(t['title'])) % 15

        rows.append(f"""
            ({t['issuerid']}, '{t['ticker']}', '{t['company_name'].replace("'", "''")}',
             '{t['title'].replace("'", "''")}', '{t['summary'].replace("'", "''")}',
             {rec}, {conv},
             '{assumptions_json}',
             '{t['stage']}', '{t['health']}',
             {validated}, '{validation_notes}',
             {entry}, {target}, {stop},
             '{docs_json}',
             {created_offset}, {updated_offset})""")

    session.sql(f"""
        INSERT INTO {database}.{schema}.FACT_RESEARCH_THESES
            (ISSUERID, TICKER, COMPANY_NAME, THESIS_TITLE, THESIS_SUMMARY,
             RECOMMENDATION, CONVICTION, KEY_ASSUMPTIONS, STAGE, HEALTH_STATUS,
             LAST_VALIDATED, VALIDATION_NOTES, ENTRY_PRICE, TARGET_PRICE, STOP_LOSS,
             SUPPORTING_DOCS, CREATED_AT, UPDATED_AT)
        SELECT $1,$2,$3,$4,$5,$6,$7,
               PARSE_JSON($8),
               $9,$10,$11,$12,$13,$14,$15,
               PARSE_JSON($16),
               DATEADD('day', -$17, CURRENT_TIMESTAMP()),
               DATEADD('day', -$18, CURRENT_TIMESTAMP())
        FROM VALUES {','.join(rows)}
    """).collect()

    log_info(f"Seeded {len(theses)} research theses across pipeline stages")


def setup_thesis_tracker(session: Session):
    """Full setup: table + procedure + seed data."""
    create_research_theses_table(session)
    create_upsert_procedure(session)
    seed_research_theses(session)
