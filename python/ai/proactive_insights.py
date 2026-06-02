"""
Proactive Agent Insights Infrastructure

Creates Snowflake objects for automated agent-driven insights:
- FACT_PROACTIVE_INSIGHTS: Stores all agent-generated insights
- FACT_PROACTIVE_ALERTS: HIGH severity items for notification
- DAILY_ATTRIBUTION_BRIEFING: Scheduled task (7am Mon-Fri)
- ANOMALY_ALERT_CHECK: Child task after briefing (CTE-based, no scripting)
- ANOMALY_ALERT_PROMOTE: Child task to copy HIGH items to alerts table
- POSITION_CHANGE_STREAM + POSITION_CHANGE_INSIGHT: Stream-triggered task

Architecture:
    DAILY_ATTRIBUTION_BRIEFING (cron 7am Mon-Fri)
        → ANOMALY_ALERT_CHECK (child — runs agent scan)
            → ANOMALY_ALERT_PROMOTE (child — copies HIGH to alerts)

    POSITION_CHANGE_STREAM (on FACT_POSITION_DAILY_ABOR)
        → POSITION_CHANGE_INSIGHT (stream-triggered, 5min poll)
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_info, log_step, log_substep, log_warning, log_error


def create_proactive_insights_tables(session: Session):
    """Create output tables for proactive agent insights."""
    database = config.DATABASE['name']
    schema = 'CURATED'

    log_substep("Creating FACT_PROACTIVE_INSIGHTS table")
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {database}.{schema}.FACT_PROACTIVE_INSIGHTS (
            InsightID BIGINT AUTOINCREMENT START 1 INCREMENT 1,
            GeneratedAt TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            InsightType VARCHAR(50) NOT NULL,
            PortfolioID BIGINT,
            PortfolioName VARCHAR(200),
            AgentName VARCHAR(100) NOT NULL,
            Prompt VARCHAR(4000),
            AgentResponseRaw VARIANT,
            AgentResponseText VARCHAR(16777216),
            Severity VARCHAR(10),
            IsRead BOOLEAN DEFAULT FALSE,
            ExpiresAt TIMESTAMP_NTZ,
            CONSTRAINT PK_PROACTIVE_INSIGHTS PRIMARY KEY (InsightID)
        )
    """).collect()

    log_substep("Creating FACT_PROACTIVE_ALERTS table")
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {database}.{schema}.FACT_PROACTIVE_ALERTS (
            AlertID BIGINT AUTOINCREMENT START 1 INCREMENT 1,
            GeneratedAt TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            PortfolioID BIGINT,
            PortfolioName VARCHAR(200),
            AlertType VARCHAR(50) NOT NULL,
            AlertDetail VARCHAR(4000),
            AgentResponseRaw VARIANT,
            IsAcknowledged BOOLEAN DEFAULT FALSE,
            CONSTRAINT PK_PROACTIVE_ALERTS PRIMARY KEY (AlertID)
        )
    """).collect()

    log_detail("  Created FACT_PROACTIVE_INSIGHTS + FACT_PROACTIVE_ALERTS")


def create_proactive_tasks(session: Session):
    """Create all proactive insight tasks (SUSPENDED by default)."""
    database = config.DATABASE['name']
    warehouse = config.WAREHOUSES['execution']['name']

    log_substep("Creating DAILY_ATTRIBUTION_BRIEFING task")
    session.sql(f"""
        CREATE OR REPLACE TASK {database}.AI.DAILY_ATTRIBUTION_BRIEFING
            WAREHOUSE = {warehouse}
            SCHEDULE = 'USING CRON 0 7 * * 1-5 Europe/London'
        AS
        INSERT INTO {database}.CURATED.FACT_PROACTIVE_INSIGHTS
            (GeneratedAt, InsightType, PortfolioID, PortfolioName, AgentName, Prompt, AgentResponseRaw, AgentResponseText, ExpiresAt)
        WITH portfolios AS (
            SELECT PORTFOLIOID, PORTFOLIONAME FROM {database}.CURATED.DIM_PORTFOLIO
        ),
        agent_calls AS (
            SELECT
                p.PORTFOLIOID,
                p.PORTFOLIONAME,
                'Generate a brief daily attribution update for ' || p.PORTFOLIONAME || '. Focus on: 1) Most recent month active return, 2) Top 3 sector contributors, 3) Any anomaly flags. Keep under 200 words.' AS prompt,
                TRY_PARSE_JSON(
                    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                        '{database}.AI.AM_portfolio_management_copilot',
                        '{{"messages": [{{"role": "user", "content": [{{"type": "text", "text": "Generate a brief daily attribution update for ' || p.PORTFOLIONAME || '. Focus on: 1) Most recent month active return, 2) Top 3 sector contributors, 3) Any anomaly flags. Keep under 200 words."}}]}}], "stream": false}}'
                    )
                ) AS resp
            FROM portfolios p
        ),
        with_text AS (
            SELECT
                ac.PORTFOLIOID, ac.PORTFOLIONAME, ac.prompt, ac.resp,
                f.value:text::VARCHAR AS response_text
            FROM agent_calls ac,
            LATERAL FLATTEN(input => ac.resp:content) f
            WHERE f.value:type::VARCHAR = 'text'
            QUALIFY ROW_NUMBER() OVER (PARTITION BY ac.PORTFOLIOID ORDER BY f.index DESC) = 1
        )
        SELECT
            CURRENT_TIMESTAMP(), 'DAILY_BRIEFING', PORTFOLIOID, PORTFOLIONAME,
            'AM_portfolio_management_copilot', prompt, resp, response_text,
            DATEADD('day', 7, CURRENT_TIMESTAMP())
        FROM with_text
    """).collect()

    log_substep("Creating ANOMALY_ALERT_CHECK child task")
    session.sql(f"""
        CREATE OR REPLACE TASK {database}.AI.ANOMALY_ALERT_CHECK
            WAREHOUSE = {warehouse}
            AFTER {database}.AI.DAILY_ATTRIBUTION_BRIEFING
        AS
        INSERT INTO {database}.CURATED.FACT_PROACTIVE_INSIGHTS
            (GeneratedAt, InsightType, AgentName, Prompt, AgentResponseRaw, AgentResponseText, Severity, ExpiresAt)
        WITH agent_response AS (
            SELECT TRY_PARSE_JSON(
                SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                    '{database}.AI.AM_portfolio_management_copilot',
                    '{{"messages": [{{"role": "user", "content": [{{"type": "text", "text": "Run a risk scan across ALL portfolios. List ONLY portfolios with HIGH severity anomalies. For each, state the portfolio name, which flags are triggered, and a 1-sentence recommended action. If no HIGH severity items exist, respond with just: No critical anomalies detected."}}]}}], "stream": false}}'
                )
            ) AS resp
        ),
        extract_text AS (
            SELECT resp, f.value:text::VARCHAR AS response_text
            FROM agent_response,
            LATERAL FLATTEN(input => resp:content) f
            WHERE f.value:type::VARCHAR = 'text'
            QUALIFY ROW_NUMBER() OVER (ORDER BY f.index DESC) = 1
        )
        SELECT
            CURRENT_TIMESTAMP(), 'ANOMALY_ALERT', 'AM_portfolio_management_copilot',
            'Run anomaly scan for HIGH severity', resp, response_text,
            CASE WHEN response_text ILIKE '%no critical%' THEN 'LOW' ELSE 'HIGH' END,
            DATEADD('day', 3, CURRENT_TIMESTAMP())
        FROM extract_text
    """).collect()

    log_substep("Creating ANOMALY_ALERT_PROMOTE child task")
    session.sql(f"""
        CREATE OR REPLACE TASK {database}.AI.ANOMALY_ALERT_PROMOTE
            WAREHOUSE = {warehouse}
            AFTER {database}.AI.ANOMALY_ALERT_CHECK
        AS
        INSERT INTO {database}.CURATED.FACT_PROACTIVE_ALERTS
            (GeneratedAt, PortfolioID, PortfolioName, AlertType, AlertDetail, AgentResponseRaw)
        SELECT
            i.GeneratedAt,
            i.PortfolioID,
            i.PortfolioName,
            'ANOMALY_HIGH',
            i.AgentResponseText,
            i.AgentResponseRaw
        FROM {database}.CURATED.FACT_PROACTIVE_INSIGHTS i
        WHERE i.InsightType = 'ANOMALY_ALERT'
            AND i.Severity = 'HIGH'
            AND i.GeneratedAt > DATEADD('minute', -30, CURRENT_TIMESTAMP())
            AND NOT EXISTS (
                SELECT 1 FROM {database}.CURATED.FACT_PROACTIVE_ALERTS a
                WHERE a.AlertDetail = i.AgentResponseText
                AND a.GeneratedAt > DATEADD('minute', -30, CURRENT_TIMESTAMP())
            )
    """).collect()

    log_detail("  Created task DAG: DAILY_ATTRIBUTION_BRIEFING → ANOMALY_ALERT_CHECK → ANOMALY_ALERT_PROMOTE (all SUSPENDED)")


def create_proactive_stream_task(session: Session):
    """Create stream on positions table and triggered insight task."""
    database = config.DATABASE['name']
    warehouse = config.WAREHOUSES['execution']['name']

    log_substep("Creating POSITION_CHANGE_STREAM")
    session.sql(f"""
        CREATE STREAM IF NOT EXISTS {database}.AI.POSITION_CHANGE_STREAM
            ON TABLE {database}.CURATED.FACT_POSITION_DAILY_ABOR
            APPEND_ONLY = TRUE
    """).collect()

    log_substep("Creating POSITION_CHANGE_INSIGHT task")
    session.sql(f"""
        CREATE OR REPLACE TASK {database}.AI.POSITION_CHANGE_INSIGHT
            WAREHOUSE = {warehouse}
            SCHEDULE = '5 MINUTE'
            WHEN SYSTEM$STREAM_HAS_DATA('{database}.AI.POSITION_CHANGE_STREAM')
        AS
        INSERT INTO {database}.CURATED.FACT_PROACTIVE_INSIGHTS
            (GeneratedAt, InsightType, PortfolioID, PortfolioName, AgentName, Prompt, AgentResponseRaw, AgentResponseText, ExpiresAt)
        WITH changed_portfolios AS (
            SELECT DISTINCT s.PORTFOLIOID, p.PORTFOLIONAME
            FROM {database}.AI.POSITION_CHANGE_STREAM s
            JOIN {database}.CURATED.DIM_PORTFOLIO p ON s.PORTFOLIOID = p.PORTFOLIOID
        ),
        agent_calls AS (
            SELECT
                cp.PORTFOLIOID, cp.PORTFOLIONAME,
                TRY_PARSE_JSON(
                    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                        '{database}.AI.AM_portfolio_management_copilot',
                        '{{"messages": [{{"role": "user", "content": [{{"type": "text", "text": "New positions loaded for ' || cp.PORTFOLIONAME || '. Check: 1) Any concentration breaches above 6.5 percent? 2) Sector allocation changes? 3) New positions? Keep under 150 words."}}]}}], "stream": false}}'
                    )
                ) AS resp
            FROM changed_portfolios cp
        ),
        with_text AS (
            SELECT ac.PORTFOLIOID, ac.PORTFOLIONAME, ac.resp,
                f.value:text::VARCHAR AS response_text
            FROM agent_calls ac,
            LATERAL FLATTEN(input => ac.resp:content) f
            WHERE f.value:type::VARCHAR = 'text'
            QUALIFY ROW_NUMBER() OVER (PARTITION BY ac.PORTFOLIOID ORDER BY f.index DESC) = 1
        )
        SELECT
            CURRENT_TIMESTAMP(), 'POSITION_CHANGE', PORTFOLIOID, PORTFOLIONAME,
            'AM_portfolio_management_copilot',
            'New positions loaded. Check concentration breaches, sector allocation changes, new positions.',
            resp, response_text, DATEADD('day', 1, CURRENT_TIMESTAMP())
        FROM with_text
    """).collect()

    log_detail("  Created POSITION_CHANGE_STREAM + POSITION_CHANGE_INSIGHT task (SUSPENDED)")


def create_all_proactive_infrastructure(session: Session):
    """Create all proactive insights infrastructure."""
    log_step("Building proactive agent insights infrastructure")

    create_proactive_insights_tables(session)
    create_proactive_tasks(session)
    create_proactive_stream_task(session)
    create_morning_briefing_task(session)

    log_info("  Proactive insights: 2 tables, 5 tasks, 1 stream created (all tasks SUSPENDED)")


def demo_run_single_briefing(session: Session, portfolio_name: str = None):
    """
    Run a single attribution briefing for demo purposes.
    Calls DATA_AGENT_RUN once and inserts the result.
    """
    database = config.DATABASE['name']

    if portfolio_name is None:
        result = session.sql(f"""
            SELECT PORTFOLIONAME FROM {database}.CURATED.DIM_PORTFOLIO LIMIT 1
        """).collect()
        portfolio_name = result[0]['PORTFOLIONAME']

    log_substep(f"Running demo briefing for: {portfolio_name}")

    session.sql(f"""
        INSERT INTO {database}.CURATED.FACT_PROACTIVE_INSIGHTS
            (GeneratedAt, InsightType, PortfolioName, AgentName, Prompt, AgentResponseRaw, AgentResponseText, Severity, ExpiresAt)
        WITH agent_call AS (
            SELECT TRY_PARSE_JSON(
                SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                    '{database}.AI.AM_portfolio_management_copilot',
                    '{{"messages": [{{"role": "user", "content": [{{"type": "text", "text": "Generate a brief daily attribution update for {portfolio_name}. Focus on: 1) Most recent month active return, 2) Top 3 sector contributors, 3) Any anomaly flags. Keep under 200 words."}}]}}], "stream": false}}'
                )
            ) AS resp
        ),
        extract_text AS (
            SELECT resp, f.value:text::VARCHAR AS response_text
            FROM agent_call,
            LATERAL FLATTEN(input => resp:content) f
            WHERE f.value:type::VARCHAR = 'text'
            QUALIFY ROW_NUMBER() OVER (ORDER BY f.index DESC) = 1
        )
        SELECT
            CURRENT_TIMESTAMP(), 'DAILY_BRIEFING', '{portfolio_name}',
            'AM_portfolio_management_copilot',
            'Generate a brief daily attribution update for {portfolio_name}.',
            resp, response_text, NULL, DATEADD('day', 7, CURRENT_TIMESTAMP())
        FROM extract_text
    """).collect()

    log_detail(f"  Demo briefing inserted for {portfolio_name}")


MORNING_BRIEF_PROMPTS = {
    'equity': (
        'AM_portfolio_management_copilot',
        'Generate a concise morning briefing for portfolio {name}. Cover: overnight market moves affecting our holdings, '
        'portfolio P&L estimate, top 3 developments requiring attention, and key events this week (earnings, macro). '
        'Use bullet points. Be specific about position impacts.'
    ),
    'credit': (
        'AM_private_credit_copilot',
        'Generate a concise morning briefing for our credit fund {name}. Cover: rate environment update (SOFR, spreads), '
        'borrower watchlist changes, any covenant test results approaching, deal pipeline status, and upcoming payment/maturity dates. '
        'Be specific about borrower-level impacts.'
    ),
    'pe': (
        'AM_private_equity_copilot',
        'Generate a concise morning briefing for PE fund {name}. Cover: portfolio company operational updates, '
        'any value creation plan milestones due this week, deal pipeline progress, public market comps changes '
        'affecting exit valuations, and upcoming board meetings.'
    ),
    'executive': (
        'AM_executive_leadership_copilot',
        'Generate a concise executive morning briefing for {name}. Cover: firm-wide AUM and net flow status, '
        'top performing and bottom performing strategies this week, any client retention concerns, '
        'compliance issues requiring attention, and key strategic items for the leadership agenda. '
        'Use bullet points. Focus on items requiring executive decision or attention.'
    ),
    'risk-compliance': (
        'AM_risk_compliance_copilot',
        'Generate a concise compliance morning briefing for {name}. Cover: overnight limit breaches or near-breaches, '
        'ESG alerts from overnight screening, approaching position limits, regulatory deadlines this week, '
        'and any new controversies flagged. Use bullet points. Be specific about thresholds and headroom.'
    ),
    'operations': (
        'AM_operations_copilot',
        'Generate a concise operations morning briefing for {name}. Cover: overnight settlement failures and pending items, '
        'reconciliation breaks requiring attention, NAV calculation status for all funds, corporate actions due today and this week, '
        'and cash position alerts. Use bullet points. Flag anything that could delay NAV deadlines.'
    ),
    'client-advisory': (
        'AM_client_advisory_copilot',
        'Generate a concise client advisory morning briefing for {name}. Cover: client meetings scheduled today, '
        'at-risk clients requiring proactive outreach, portfolio performance highlights to communicate to clients, '
        'any open RFP deadlines, and key talking points for upcoming reviews. Use bullet points.'
    ),
    'quant': (
        'AM_portfolio_management_copilot',
        'Generate a concise quantitative morning briefing for {name}. Cover: current market regime status and any transition signals, '
        'factor performance overnight, IC decay alerts, model drift metrics vs backtest, yield curve changes, '
        'and any signals requiring model recalibration. Use bullet points. Focus on quantitative signals.'
    ),
    'construction': (
        'AM_portfolio_management_copilot',
        'Generate a concise portfolio construction morning briefing for {name}. Cover: portfolios approaching IPS constraint limits, '
        'rebalance triggers fired overnight, goal probability degradation alerts from Monte Carlo monitoring, '
        'any proposals pending client approval, and tracking error drift. Use bullet points.'
    ),
}


def create_morning_briefing_task(session: Session):
    """Create a scheduled task to pre-generate morning briefings for all personas."""
    database = config.DATABASE['name']
    warehouse = config.WAREHOUSES['execution']['name']
    ai_schema = config.DATABASE['schemas']['ai']

    log_substep("Creating MORNING_BRIEFING_TASK")

    agent_name, prompt_template = MORNING_BRIEF_PROMPTS['equity']

    session.sql(f"""
        CREATE OR REPLACE TASK {database}.{ai_schema}.MORNING_BRIEFING_TASK
            WAREHOUSE = {warehouse}
            SCHEDULE = 'USING CRON 30 6 * * 1-5 Europe/London'
        AS
        INSERT INTO {database}.CURATED.FACT_PROACTIVE_INSIGHTS
            (GeneratedAt, InsightType, PortfolioID, PortfolioName, AgentName, Prompt, AgentResponseRaw, AgentResponseText, ExpiresAt)
        WITH portfolios AS (
            SELECT PORTFOLIOID, PORTFOLIONAME FROM {database}.CURATED.DIM_PORTFOLIO
        ),
        agent_calls AS (
            SELECT
                p.PORTFOLIOID,
                p.PORTFOLIONAME,
                '{prompt_template.replace("{name}", "' || p.PORTFOLIONAME || '")}' AS prompt,
                TRY_PARSE_JSON(
                    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                        '{database}.{ai_schema}.{agent_name}',
                        '{{"messages": [{{"role": "user", "content": [{{"type": "text", "text": "{prompt_template.replace('{name}', "' || p.PORTFOLIONAME || '")}"}}]}}], "stream": false}}'
                    )
                ) AS resp
            FROM portfolios p
        ),
        with_text AS (
            SELECT
                ac.PORTFOLIOID, ac.PORTFOLIONAME, ac.prompt, ac.resp,
                f.value:text::VARCHAR AS response_text
            FROM agent_calls ac,
            LATERAL FLATTEN(input => ac.resp:content) f
            WHERE f.value:type::VARCHAR = 'text'
            QUALIFY ROW_NUMBER() OVER (PARTITION BY ac.PORTFOLIOID ORDER BY f.index DESC) = 1
        )
        SELECT
            CURRENT_TIMESTAMP(), 'MORNING_BRIEFING', PORTFOLIOID, PORTFOLIONAME,
            '{agent_name}', prompt, resp, response_text,
            DATEADD('day', 1, CURRENT_TIMESTAMP())
        FROM with_text
    """).collect()

    log_detail("  Created MORNING_BRIEFING_TASK (SUSPENDED, schedule: 6:30am Mon-Fri)")


def seed_morning_briefings(session: Session, personas: list = None):
    """Generate morning briefings on demand for demo seeding. Uses async parallel pattern (collect_nowait)."""
    database = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    if personas is None:
        personas = ['equity']

    for persona in personas:
        if persona not in MORNING_BRIEF_PROMPTS:
            log_warning(f"  Unknown persona '{persona}', skipping")
            continue

        agent_name, prompt_template = MORNING_BRIEF_PROMPTS[persona]
        log_substep(f"Generating morning briefings for persona: {persona} (agent: {agent_name})")

        if persona == 'equity':
            entities = session.sql(f"SELECT PORTFOLIOID, PORTFOLIONAME FROM {database}.CURATED.DIM_PORTFOLIO").collect()
            entities = [(row['PORTFOLIOID'], row['PORTFOLIONAME']) for row in entities]
        elif persona == 'credit':
            entities = session.sql(f"SELECT FUNDID, FUNDNAME FROM {database}.CURATED.DIM_CREDIT_FUND").collect()
            entities = [(row['FUNDID'], row['FUNDNAME']) for row in entities]
        elif persona == 'pe':
            entities = session.sql(f"SELECT FUNDID, FUNDNAME FROM {database}.CURATED.DIM_PE_FUND").collect()
            entities = [(row['FUNDID'], row['FUNDNAME']) for row in entities]
        elif persona == 'executive':
            entities = [(0, 'Simulated Asset Management')]
        elif persona == 'risk-compliance':
            entities = [(0, 'Simulated Asset Management')]
        elif persona == 'operations':
            entities = [(0, 'Simulated Asset Management')]
        elif persona == 'client-advisory':
            entities = [(0, 'Simulated Asset Management')]
        elif persona == 'quant':
            entities = [(0, 'Simulated Asset Management')]
        elif persona == 'construction':
            entities = [(0, 'Simulated Asset Management')]
        else:
            entities = [(0, persona)]

        async_jobs = []
        for entity_id, entity_name in entities:
            prompt = prompt_template.replace('{name}', entity_name)
            escaped_prompt = prompt.replace("'", "''").replace('"', '\\\\"')
            escaped_name = entity_name.replace("'", "''")

            job = session.sql(f"""
                INSERT INTO {database}.CURATED.FACT_PROACTIVE_INSIGHTS
                    (GeneratedAt, InsightType, PortfolioID, PortfolioName, AgentName, Prompt, AgentResponseRaw, AgentResponseText, ExpiresAt)
                WITH agent_call AS (
                    SELECT TRY_PARSE_JSON(
                        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                            '{database}.{ai_schema}.{agent_name}',
                            '{{"messages": [{{"role": "user", "content": [{{"type": "text", "text": "{escaped_prompt}"}}]}}], "stream": false}}'
                        )
                    ) AS resp
                ),
                extract_text AS (
                    SELECT resp, f.value:text::VARCHAR AS response_text
                    FROM agent_call,
                    LATERAL FLATTEN(input => resp:content) f
                    WHERE f.value:type::VARCHAR = 'text'
                    QUALIFY ROW_NUMBER() OVER (ORDER BY f.index DESC) = 1
                )
                SELECT
                    CURRENT_TIMESTAMP(), 'MORNING_BRIEFING', {entity_id}, '{escaped_name}',
                    '{agent_name}', '{escaped_prompt}', resp, response_text,
                    DATEADD('day', 1, CURRENT_TIMESTAMP())
                FROM extract_text
            """).collect_nowait()
            async_jobs.append((entity_name, job))

        log_detail(f"  Submitted {len(async_jobs)} briefing jobs for {persona} — awaiting results...")

        succeeded = 0
        for entity_name, job in async_jobs:
            try:
                job.result()
                succeeded += 1
                log_detail(f"    Briefing generated for {entity_name}")
            except Exception as e:
                log_error(f"    Failed for {entity_name}: {e}")

        log_detail(f"  {persona}: {succeeded}/{len(async_jobs)} briefings generated")

    log_detail(f"  Morning briefings seeded for personas: {personas}")
