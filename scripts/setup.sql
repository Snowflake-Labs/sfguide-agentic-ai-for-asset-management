-- ============================================================================
-- SAM Demo - Complete Setup (Single SQL Script)
-- ============================================================================
-- This script sets up the entire SAM demo environment in Snowflake
-- 
-- ARCHITECTURE:
-- 1. Git Integration pulls repo content (templates, Python files)
-- 2. Python Stored Procedures hydrate templates and generate data
-- 3. SQL DDL creates chunking, search services, semantic views, and agents
--
-- RESULT:
-- - 50+ CURATED dimension/fact tables with 14,000+ real securities
-- - 26 RAW document tables from 50+ templates  
-- - 26 corpus tables (document collections)
-- - 26 chunk tables (markdown-aware semantic chunks)
-- - 17 Cortex Search services (16 core + 1 real SEC filings)
-- - 12 Cortex Analyst semantic views (9 core + 3 for real data)
-- - 9 Cortex agents
--
-- RUN TIME: ~15-20 minutes
-- REQUIRES: ACCOUNTADMIN role
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- SECTION 1: Database and Schemas
-- ============================================================================

CREATE DATABASE IF NOT EXISTS SAM_DEMO
    COMMENT = 'Snowcrest Asset Management (SAM) - Agentic AI Demo Database';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.RAW
    COMMENT = 'Raw data layer - external data and unprocessed documents';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.CURATED
    COMMENT = 'Curated data layer - clean, validated, business-ready data';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.AI
    COMMENT = 'AI components - semantic views, search services, agents';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.PUBLIC
    COMMENT = 'Public schema for Git integration and notebooks';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.MARKET_DATA
    COMMENT = 'Market data layer - synthetic and real market data from external sources';

-- ============================================================================
-- SECTION 2: Role Creation and Grants
-- ============================================================================

CREATE ROLE IF NOT EXISTS SAM_DEMO_ROLE
    COMMENT = 'Dedicated role for SAM demo operations';

-- Grant database and schema usage
GRANT USAGE ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;
GRANT CREATE SCHEMA ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant all privileges on schemas
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on all existing and future tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant role to ACCOUNTADMIN
GRANT ROLE SAM_DEMO_ROLE TO ROLE ACCOUNTADMIN;

-- ============================================================================
-- SECTION 3: Warehouse (Single LARGE warehouse for all operations)
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS SAM_DEMO_WH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for SAM demo operations';

-- Ensure warehouse is LARGE (in case it already exists with different size)
ALTER WAREHOUSE SAM_DEMO_WH SET WAREHOUSE_SIZE = 'LARGE';

GRANT USAGE ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 4: Marketplace Data Access
-- ============================================================================

-- PREREQUISITE: Accept Marketplace listing terms first
-- https://app.snowflake.com/marketplace/listing/GZTSZ290BV255

GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 5: Snowflake Intelligence Setup
-- ============================================================================

CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;

GRANT CREATE SNOWFLAKE INTELLIGENCE ON ACCOUNT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE PUBLIC;

GRANT CREATE AGENT ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE SEMANTIC VIEW ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 6: Git Integration
-- ============================================================================

CREATE OR REPLACE SECRET SAM_DEMO.PUBLIC.GITHUB_SECRET
  TYPE = PASSWORD
  USERNAME = 'user_name'
  PASSWORD = 'pat_token'
  COMMENT = 'GitHub PAT for accessing private SAM demo repository';

-- Grant secret usage to role
GRANT USAGE ON SECRET SAM_DEMO.PUBLIC.GITHUB_SECRET TO ROLE SAM_DEMO_ROLE;

-- Create API integration for Git (must reference the secret in ALLOWED_AUTHENTICATION_SECRETS)
CREATE OR REPLACE API INTEGRATION GITHUB_INTEGRATION_SAM_DEMO
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/')
  ALLOWED_AUTHENTICATION_SECRETS = (SAM_DEMO.PUBLIC.GITHUB_SECRET)
  ENABLED = TRUE
  COMMENT = 'Git integration with GitHub for SAM Demo repository';

-- Create Git repository object pointing to the SAM demo repo (with authentication)
CREATE OR REPLACE GIT REPOSITORY SAM_DEMO.PUBLIC.sam_demo_repo
  API_INTEGRATION = GITHUB_INTEGRATION_SAM_DEMO
  GIT_CREDENTIALS = SAM_DEMO.PUBLIC.GITHUB_SECRET
  ORIGIN = 'https://github.com/sfc-gh-dshemsi/sfguide-agentic-ai-for-asset-management.git'
  COMMENT = 'Git repository for SAM demo setup files';

-- Fetch latest code from Git
ALTER GIT REPOSITORY SAM_DEMO.PUBLIC.sam_demo_repo FETCH;

-- ============================================================================
-- SECTION 7: Python Stored Procedures for Data Generation
-- ============================================================================

USE ROLE SAM_DEMO_ROLE;
USE WAREHOUSE SAM_DEMO_WH;
USE DATABASE SAM_DEMO;

-- Create stage for reports
CREATE STAGE IF NOT EXISTS SAM_DEMO.CURATED.SAM_REPORTS_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for generated PDF reports';

-- ============================================================================
-- SECTION 7.1: Master Setup Procedure
-- ============================================================================

CREATE OR REPLACE PROCEDURE SAM_DEMO.PUBLIC.SETUP_SAM_DEMO(TEST_MODE BOOLEAN DEFAULT FALSE)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'pyyaml', 'jinja2')
HANDLER = 'run_setup'
EXECUTE AS CALLER
AS
$$
import os
import sys

def run_setup(session, test_mode: bool = False) -> str:
    """
    Master setup procedure that orchestrates the entire SAM demo setup.
    Downloads Python modules from Git and runs all data generation steps.
    """
    import tempfile
    import shutil
    
    # Create temp directory for downloads
    tmp_dir = tempfile.mkdtemp(prefix='sam_demo_')
    python_dir = os.path.join(tmp_dir, 'python')
    content_dir = os.path.join(tmp_dir, 'content_library')
    os.makedirs(python_dir, exist_ok=True)
    os.makedirs(content_dir, exist_ok=True)
    
    results = []
    results.append(f"Temp directory: {tmp_dir}")
    
    # Step 1: Download Python files from Git
    results.append("\n=== Step 1: Downloading Python modules ===")
    git_stage = '@SAM_DEMO.PUBLIC.sam_demo_repo/branches/main'
    
    python_files = [
        'config.py', 'generate_structured.py', 'generate_unstructured.py',
        'generate_market_data.py', 'generate_real_transcripts.py', 'snowflake_io_utils.py',
        'build_ai.py', 'create_agents.py', 'create_semantic_views.py',
        'create_cortex_search.py', 'hydration_engine.py', 'extract_real_assets.py',
        'rules_loader.py'
    ]
    
    downloaded = 0
    for f in python_files:
        try:
            session.file.get(f"{git_stage}/python/{f}", python_dir + '/')
            downloaded += 1
        except Exception as e:
            results.append(f"  Warning: {f} - {e}")
    
    results.append(f"  Downloaded {downloaded}/{len(python_files)} Python files")
    
    # Step 2: Download content library templates
    results.append("\n=== Step 2: Downloading content library ===")
    try:
        content_files = session.sql(f"LIST {git_stage}/content_library/").collect()
        template_count = 0
        for row in content_files:
            file_path = row['name']
            if file_path.endswith('.md') or file_path.endswith('.yaml'):
                rel_path = file_path.split('/content_library/')[-1]
                local_dir = os.path.dirname(os.path.join(content_dir, rel_path))
                os.makedirs(local_dir, exist_ok=True)
                try:
                    session.file.get(f"@{file_path}", local_dir + '/')
                    template_count += 1
                except:
                    pass
        results.append(f"  Downloaded {template_count} template files")
    except Exception as e:
        results.append(f"  Warning: Could not list content library: {e}")
    
    # Step 3: Configure Python path
    sys.path.insert(0, python_dir)
    
    # Import and configure modules
    import config
    config.PROJECT_ROOT = tmp_dir
    config.CONTENT_LIBRARY_PATH = content_dir
    
    results.append(f"\n=== Configuration ===")
    results.append(f"  Database: {config.DATABASE['name']}")
    results.append(f"  Content library: {config.CONTENT_LIBRARY_PATH}")
    
    # Step 4: Generate structured data
    results.append("\n=== Step 3: Generating structured data ===")
    try:
        import generate_structured
        generate_structured.build_all(session, ['all'], test_mode=test_mode)
        results.append("  Structured data complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 5: Generate market data
    results.append("\n=== Step 4: Generating market data ===")
    try:
        import generate_market_data
        generate_market_data.build_all(session, test_mode=test_mode)
        results.append("  Market data complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 6: Generate real transcripts (optional)
    results.append("\n=== Step 5: Generating real transcripts ===")
    try:
        import generate_real_transcripts
        generate_real_transcripts.build_all(session, test_mode=test_mode)
        results.append("  Real transcripts complete!")
    except Exception as e:
        results.append(f"  Skipping real transcripts: {e}")
    
    # Step 7: Generate unstructured documents
    results.append("\n=== Step 6: Generating documents from templates ===")
    try:
        import generate_unstructured
        generate_unstructured.build_all(session, ['all'], test_mode=test_mode)
        results.append("  Document generation complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Clean up temp directory
    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    
    results.append("\n=== Data Generation Complete ===")
    return "\n".join(results)
$$;

-- ============================================================================
-- SECTION 7.2: AI Components Procedure (Search Services, Semantic Views)
-- ============================================================================

CREATE OR REPLACE PROCEDURE SAM_DEMO.PUBLIC.SETUP_AI_COMPONENTS()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'pyyaml')
HANDLER = 'run_ai_setup'
EXECUTE AS CALLER
AS
$$
import os
import sys

def run_ai_setup(session) -> str:
    """
    Creates AI components: semantic views and Cortex Search services.
    """
    import tempfile
    
    # Create temp directory and download modules
    tmp_dir = tempfile.mkdtemp(prefix='sam_ai_')
    python_dir = os.path.join(tmp_dir, 'python')
    os.makedirs(python_dir, exist_ok=True)
    
    results = []
    git_stage = '@SAM_DEMO.PUBLIC.sam_demo_repo/branches/main'
    
    # Download required Python files
    python_files = [
        'config.py', 'build_ai.py', 'create_semantic_views.py', 'create_cortex_search.py'
    ]
    
    for f in python_files:
        try:
            session.file.get(f"{git_stage}/python/{f}", python_dir + '/')
        except Exception as e:
            results.append(f"Warning: {f} - {e}")
    
    sys.path.insert(0, python_dir)
    
    import config
    config.PROJECT_ROOT = tmp_dir
    
    # Expand 'all' to all scenario names (required for semantic views creation)
    all_scenarios = [
        'portfolio_copilot', 'research_copilot', 'thematic_macro_advisor',
        'esg_guardian', 'sales_advisor', 'quant_analyst', 'compliance_advisor',
        'middle_office_copilot', 'executive_copilot'
    ]
    
    # Create semantic views
    results.append("=== Creating Semantic Views ===")
    try:
        import create_semantic_views
        create_semantic_views.create_semantic_views(session, all_scenarios)
        results.append("  Semantic views created!")
    except Exception as e:
        results.append(f"  ERROR creating semantic views: {e}")
        raise
    
    # Create search services
    results.append("\n=== Creating Cortex Search Services ===")
    try:
        import create_cortex_search
        create_cortex_search.create_search_services(session, all_scenarios)
        results.append("  Search services created!")
    except Exception as e:
        results.append(f"  ERROR creating search services: {e}")
        raise
    
    # Clean up
    import shutil
    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    
    results.append("\n=== AI Components Complete ===")
    return "\n".join(results)
$$;

-- ============================================================================
-- SECTION 7.3: Agent Creation Procedure
-- ============================================================================

CREATE OR REPLACE PROCEDURE SAM_DEMO.PUBLIC.SETUP_AGENTS()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'pyyaml')
HANDLER = 'run_agent_setup'
EXECUTE AS CALLER
AS
$$
import os
import sys

def run_agent_setup(session) -> str:
    """
    Creates all Cortex agents for the SAM demo.
    """
    import tempfile
    
    tmp_dir = tempfile.mkdtemp(prefix='sam_agents_')
    python_dir = os.path.join(tmp_dir, 'python')
    os.makedirs(python_dir, exist_ok=True)
    
    results = []
    git_stage = '@SAM_DEMO.PUBLIC.sam_demo_repo/branches/main'
    
    # Download required Python files
    python_files = ['config.py', 'create_agents.py']
    
    for f in python_files:
        try:
            session.file.get(f"{git_stage}/python/{f}", python_dir + '/')
        except Exception as e:
            results.append(f"Warning: {f} - {e}")
    
    sys.path.insert(0, python_dir)
    
    import config
    config.PROJECT_ROOT = tmp_dir
    
    # Create agents
    results.append("=== Creating Cortex Agents ===")
    try:
        import create_agents
        created, failed = create_agents.create_all_agents(session, ['all'])
        results.append(f"  Created: {created} agents")
        if failed > 0:
            results.append(f"  Failed: {failed} agents")
    except Exception as e:
        results.append(f"  ERROR creating agents: {e}")
        raise
    
    # Clean up
    import shutil
    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    
    results.append("\n=== Agent Creation Complete ===")
    return "\n".join(results)
$$;

-- ============================================================================
-- SECTION 8: Document Chunking for Cortex Search
-- ============================================================================

-- Create chunked document tables for enhanced semantic search
-- This uses SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER for markdown-aware chunking

CREATE OR REPLACE PROCEDURE SAM_DEMO.PUBLIC.CREATE_DOCUMENT_CHUNKS()
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    result STRING DEFAULT '';
    chunk_count INTEGER;
BEGIN
    -- Chunk Broker Research Documents
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.BROKER_RESEARCH_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.BROKER_RESEARCH_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.BROKER_RESEARCH_CHUNKS;
    result := result || 'BROKER_RESEARCH_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Earnings Transcripts
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.EARNINGS_TRANSCRIPTS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.EARNINGS_TRANSCRIPTS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.EARNINGS_TRANSCRIPTS_CHUNKS;
    result := result || 'EARNINGS_TRANSCRIPTS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Press Releases
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.PRESS_RELEASES_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.PRESS_RELEASES_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.PRESS_RELEASES_CHUNKS;
    result := result || 'PRESS_RELEASES_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk NGO Reports
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.NGO_REPORTS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.NGO_REPORTS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.NGO_REPORTS_CHUNKS;
    result := result || 'NGO_REPORTS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Engagement Notes
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.ENGAGEMENT_NOTES_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.ENGAGEMENT_NOTES_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.ENGAGEMENT_NOTES_CHUNKS;
    result := result || 'ENGAGEMENT_NOTES_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Policy Documents
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.POLICY_DOCS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.POLICY_DOCS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.POLICY_DOCS_CHUNKS;
    result := result || 'POLICY_DOCS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Internal Research
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.INTERNAL_RESEARCH_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.INTERNAL_RESEARCH_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.INTERNAL_RESEARCH_CHUNKS;
    result := result || 'INTERNAL_RESEARCH_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Investment Memos
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.INVESTMENT_MEMO_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.INVESTMENT_MEMO_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.INVESTMENT_MEMO_CHUNKS;
    result := result || 'INVESTMENT_MEMO_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Sales Templates
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.SALES_TEMPLATES_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.SALES_TEMPLATES_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.SALES_TEMPLATES_CHUNKS;
    result := result || 'SALES_TEMPLATES_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Philosophy Docs
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.PHILOSOPHY_DOCS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.PHILOSOPHY_DOCS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.PHILOSOPHY_DOCS_CHUNKS;
    result := result || 'PHILOSOPHY_DOCS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Macro Events
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.MACRO_EVENTS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.MACRO_EVENTS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.MACRO_EVENTS_CHUNKS;
    result := result || 'MACRO_EVENTS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Report Templates
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.REPORT_TEMPLATES_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.REPORT_TEMPLATES_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.REPORT_TEMPLATES_CHUNKS;
    result := result || 'REPORT_TEMPLATES_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Company Event Transcripts (real data - optional, may not exist)
    BEGIN
        CREATE OR REPLACE TABLE SAM_DEMO.CURATED.COMPANY_EVENT_TRANSCRIPTS_CHUNKS AS
        SELECT 
            r.DOCUMENT_ID,
            r.DOCUMENT_TITLE,
            r.SecurityID,
            r.IssuerID,
            r.DOCUMENT_TYPE,
            r.PUBLISH_DATE,
            r.LANGUAGE,
            r.EVENT_TYPE,
            ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
            chunks.value::STRING AS CHUNK_TEXT
        FROM SAM_DEMO.CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS r,
        LATERAL FLATTEN(
            SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
                r.DOCUMENT_TEXT,
                'markdown',
                1500,
                200
            )
        ) AS chunks;
        
        SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.COMPANY_EVENT_TRANSCRIPTS_CHUNKS;
        result := result || 'COMPANY_EVENT_TRANSCRIPTS_CHUNKS: ' || chunk_count || ' chunks\n';
    EXCEPTION
        WHEN OTHER THEN
            result := result || 'COMPANY_EVENT_TRANSCRIPTS_CHUNKS: skipped (real data not available)\n';
    END;
    
    -- Chunk IPS (Investment Policy Statements)
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.IPS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.IPS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.IPS_CHUNKS;
    result := result || 'IPS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Portfolio Reviews
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.PORTFOLIO_REVIEW_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.PORTFOLIO_REVIEW_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.PORTFOLIO_REVIEW_CHUNKS;
    result := result || 'PORTFOLIO_REVIEW_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Market Data Documents
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.MARKET_DATA_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.MARKET_DATA_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.MARKET_DATA_CHUNKS;
    result := result || 'MARKET_DATA_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Compliance Manual
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.COMPLIANCE_MANUAL_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.COMPLIANCE_MANUAL_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.COMPLIANCE_MANUAL_CHUNKS;
    result := result || 'COMPLIANCE_MANUAL_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Risk Framework
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.RISK_FRAMEWORK_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.RISK_FRAMEWORK_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.RISK_FRAMEWORK_CHUNKS;
    result := result || 'RISK_FRAMEWORK_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Form ADV
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FORM_ADV_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.FORM_ADV_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.FORM_ADV_CHUNKS;
    result := result || 'FORM_ADV_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Form CRS
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.FORM_CRS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.FORM_CRS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.FORM_CRS_CHUNKS;
    result := result || 'FORM_CRS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Regulatory Updates
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.REGULATORY_UPDATES_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.REGULATORY_UPDATES_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.REGULATORY_UPDATES_CHUNKS;
    result := result || 'REGULATORY_UPDATES_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Custodian Reports
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.CUSTODIAN_REPORTS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.CUSTODIAN_REPORTS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.CUSTODIAN_REPORTS_CHUNKS;
    result := result || 'CUSTODIAN_REPORTS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Reconciliation Notes
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.RECONCILIATION_NOTES_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.RECONCILIATION_NOTES_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.RECONCILIATION_NOTES_CHUNKS;
    result := result || 'RECONCILIATION_NOTES_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk SSI Documents
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.SSI_DOCUMENTS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.SSI_DOCUMENTS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.SSI_DOCUMENTS_CHUNKS;
    result := result || 'SSI_DOCUMENTS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Ops Procedures
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.OPS_PROCEDURES_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.OPS_PROCEDURES_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.OPS_PROCEDURES_CHUNKS;
    result := result || 'OPS_PROCEDURES_CHUNKS: ' || chunk_count || ' chunks\n';
    
    -- Chunk Strategy Documents
    CREATE OR REPLACE TABLE SAM_DEMO.CURATED.STRATEGY_DOCUMENTS_CHUNKS AS
    SELECT 
        r.DOCUMENT_ID,
        r.DOCUMENT_TITLE,
        r.SecurityID,
        r.IssuerID,
        r.DOCUMENT_TYPE,
        r.PUBLISH_DATE,
        r.LANGUAGE,
        ROW_NUMBER() OVER (PARTITION BY r.DOCUMENT_ID ORDER BY chunks.index) AS CHUNK_ID,
        chunks.value::STRING AS CHUNK_TEXT
    FROM SAM_DEMO.CURATED.STRATEGY_DOCUMENTS_CORPUS r,
    LATERAL FLATTEN(
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            r.DOCUMENT_TEXT,
            'markdown',
            1500,
            200
        )
    ) AS chunks;
    
    SELECT COUNT(*) INTO :chunk_count FROM SAM_DEMO.CURATED.STRATEGY_DOCUMENTS_CHUNKS;
    result := result || 'STRATEGY_DOCUMENTS_CHUNKS: ' || chunk_count || ' chunks\n';
    
    RETURN result;
END;
$$;

-- ============================================================================
-- SECTION 8.1: Custom Tools (PDF Generation, M&A Simulation)
-- ============================================================================

-- PDF Report Generation Tool
CREATE OR REPLACE PROCEDURE SAM_DEMO.AI.GENERATE_INVESTMENT_COMMITTEE_PDF(
    markdown_content VARCHAR,
    portfolio_name VARCHAR,
    security_ticker VARCHAR
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python','markdown','weasyprint')
HANDLER = 'generate_pdf'
AS
$$
from snowflake.snowpark import Session
from datetime import datetime
import re
import markdown
import tempfile
import os

def generate_pdf(session: Session, markdown_content: str, portfolio_name: str, security_ticker: str):
    """
    Generate PDF report from markdown content provided by the agent.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_portfolio = re.sub(r'[^a-zA-Z0-9_]', '_', portfolio_name)[:20]
    safe_ticker = re.sub(r'[^a-zA-Z0-9_]', '_', security_ticker)[:10]
    pdf_filename = f'mandate_compliance_{safe_portfolio}_{safe_ticker}_{timestamp}.pdf'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        html_body = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
        
        css_style = """
            @page { size: A4; margin: 2cm; }
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #2C3E50; }
            h1 { color: #1F4E79; border-bottom: 3px solid #1F4E79; padding-bottom: 10px; }
            h2 { color: #2E75B6; border-left: 4px solid #2E75B6; padding-left: 15px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th { background-color: #1F4E79; color: white; padding: 12px; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
        """
        
        sam_header = """
        <div style="text-align: center; background: linear-gradient(135deg, #1F4E79, #2E75B6); color: white; padding: 20px; margin-bottom: 30px;">
            <h1 style="margin: 0; color: white; border: none;">🏔️ SNOWCREST ASSET MANAGEMENT</h1>
            <p style="margin: 5px 0 0 0;">Investment Committee Decision Documentation</p>
        </div>
        """
        
        footer = f"""
        <div style="margin-top: 30px; padding-top: 15px; border-top: 2px solid #1F4E79; font-size: 12px;">
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}</p>
            <p><strong>By:</strong> Snowflake Intelligence - Portfolio Co-Pilot</p>
        </div>
        """
        
        html_content = f"""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><style>{css_style}</style></head>
        <body>{sam_header}{html_body}{footer}</body></html>
        """
        
        html_path = os.path.join(tmpdir, 'report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        import weasyprint
        pdf_path = os.path.join(tmpdir, pdf_filename)
        weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
        
        stage_path = '@SAM_DEMO.CURATED.SAM_REPORTS_STAGE'
        session.file.put(pdf_path, stage_path, overwrite=True, auto_compress=False)
        
        presigned_url = session.sql(
            f"SELECT GET_PRESIGNED_URL('{stage_path}', '{pdf_filename}') AS url"
        ).collect()[0]['URL']
        
        return f"[Investment Committee Decision - {portfolio_name} - {security_ticker}]({presigned_url})"
$$;

-- M&A Simulation Tool for Executive Scenario
CREATE OR REPLACE FUNCTION SAM_DEMO.AI.MA_SIMULATION_TOOL(
    target_aum FLOAT,
    target_revenue FLOAT,
    cost_synergy_pct FLOAT DEFAULT 0.20
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'simulate_acquisition'
AS
$$
def simulate_acquisition(target_aum: float, target_revenue: float, cost_synergy_pct: float = 0.20) -> dict:
    """
    Simulate the financial impact of an acquisition on Snowcrest Asset Management.
    """
    # SAM baseline assumptions
    sam_baseline_eps = 2.50
    sam_shares_outstanding = 50_000_000
    sam_current_aum = 12_500_000_000
    sam_operating_margin = 0.35
    
    # Integration assumptions
    integration_cost_one_time = 30_000_000
    year1_synergy_realization = 0.70
    revenue_synergy_pct = 0.02
    
    target_operating_income = target_revenue * sam_operating_margin
    cost_synergies_full = target_revenue * cost_synergy_pct
    cost_synergies_year1 = cost_synergies_full * year1_synergy_realization
    revenue_synergies = target_revenue * revenue_synergy_pct
    
    year1_contribution = (target_operating_income + cost_synergies_year1 + 
        (revenue_synergies * sam_operating_margin) - integration_cost_one_time)
    year2_contribution = (target_operating_income + cost_synergies_full + 
        (revenue_synergies * sam_operating_margin))
    
    eps_impact_year1 = year1_contribution / sam_shares_outstanding
    eps_impact_year2 = year2_contribution / sam_shares_outstanding
    eps_accretion_year1_pct = (eps_impact_year1 / sam_baseline_eps) * 100
    eps_accretion_year2_pct = (eps_impact_year2 / sam_baseline_eps) * 100
    
    combined_aum = sam_current_aum + target_aum
    aum_growth_pct = (target_aum / sam_current_aum) * 100
    
    risk_level = "Low" if target_aum < 5_000_000_000 else "Medium" if target_aum < 20_000_000_000 else "High"
    
    return {
        "simulation_summary": {
            "target_aum_billions": round(target_aum / 1_000_000_000, 1),
            "target_revenue_millions": round(target_revenue / 1_000_000, 1),
            "cost_synergy_assumption_pct": cost_synergy_pct * 100
        },
        "year1_projection": {
            "eps_accretion_pct": round(eps_accretion_year1_pct, 1),
            "eps_impact_usd": round(eps_impact_year1, 2),
            "net_contribution_millions": round(year1_contribution / 1_000_000, 1)
        },
        "year2_projection": {
            "eps_accretion_pct": round(eps_accretion_year2_pct, 1),
            "eps_impact_usd": round(eps_impact_year2, 2),
            "net_contribution_millions": round(year2_contribution / 1_000_000, 1)
        },
        "strategic_impact": {
            "combined_aum_billions": round(combined_aum / 1_000_000_000, 1),
            "aum_growth_pct": round(aum_growth_pct, 1)
        },
        "risk_assessment": {
            "integration_risk_level": risk_level,
            "timeline_months": 12 if risk_level == "Low" else 18 if risk_level == "Medium" else 24
        },
        "recommendation": f"Based on {round(eps_accretion_year1_pct, 1)}% Year 1 EPS accretion, this acquisition appears financially attractive."
    }
$$;

-- ============================================================================
-- SECTION 9: Execute Complete Setup
-- ============================================================================

-- Run the master setup procedure
CALL SAM_DEMO.PUBLIC.SETUP_SAM_DEMO(FALSE);

-- Create document chunks for semantic search
CALL SAM_DEMO.PUBLIC.CREATE_DOCUMENT_CHUNKS();

-- Create AI components (semantic views and search services)
CALL SAM_DEMO.PUBLIC.SETUP_AI_COMPONENTS();

-- Create Cortex agents
CALL SAM_DEMO.PUBLIC.SETUP_AGENTS();

-- ============================================================================
-- Setup Complete!
-- ============================================================================
-- 
-- Next Steps:
-- 1. Open Snowflake Intelligence UI
-- 2. Select an agent (e.g., Portfolio Copilot)
-- 3. Try demo prompts:
--    - 'What are my top 10 holdings in SAM Technology & Infrastructure?'
--    - 'Check for concentration breaches across all portfolios'
--    - 'What is the latest research on Microsoft?'
-- ============================================================================

