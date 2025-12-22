-- ============================================================================
-- SAM Demo - Complete Setup (Single SQL Script)
-- ============================================================================
-- This script sets up the entire SAM demo environment in Snowflake
-- 
-- ARCHITECTURE:
-- 1. Git Integration pulls repo content (templates, Python files)
-- 2. Python Stored Procedures hydrate templates and generate data
-- 3. SQL DDL creates search services, semantic views, and agents
--
-- RESULT:
-- - 50+ CURATED dimension/fact tables with 14,000+ real securities
-- - 26 RAW document tables from 50+ templates  
-- - 26 corpus tables (document collections)
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

-- Grant database-level privileges
GRANT USAGE ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;
GRANT CREATE SCHEMA ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;

-- Grant schema usage
GRANT USAGE ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant all privileges on schemas (includes CREATE TABLE, VIEW, PROCEDURE, etc.)
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on TABLES (existing and future)
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

-- Grant privileges on VIEWS (existing and future)
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on PROCEDURES (existing and future)
GRANT ALL PRIVILEGES ON ALL PROCEDURES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL PROCEDURES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL PROCEDURES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL PROCEDURES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL PROCEDURES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

GRANT ALL PRIVILEGES ON FUTURE PROCEDURES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE PROCEDURES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE PROCEDURES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE PROCEDURES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE PROCEDURES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on FUNCTIONS (existing and future)
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

GRANT ALL PRIVILEGES ON FUTURE FUNCTIONS IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE FUNCTIONS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE FUNCTIONS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE FUNCTIONS IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE FUNCTIONS IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on STAGES (existing and future)
GRANT ALL PRIVILEGES ON ALL STAGES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL STAGES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL STAGES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL STAGES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL STAGES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

GRANT ALL PRIVILEGES ON FUTURE STAGES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE STAGES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE STAGES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE STAGES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE STAGES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on FILE FORMATS (existing and future)
GRANT ALL PRIVILEGES ON ALL FILE FORMATS IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL FILE FORMATS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL FILE FORMATS IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;

GRANT ALL PRIVILEGES ON FUTURE FILE FORMATS IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE FILE FORMATS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE FILE FORMATS IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on SEQUENCES (existing and future)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;

GRANT ALL PRIVILEGES ON FUTURE SEQUENCES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE SEQUENCES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE SEQUENCES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;

-- Grant role to ACCOUNTADMIN and current user
GRANT ROLE SAM_DEMO_ROLE TO ROLE ACCOUNTADMIN;
GRANT ROLE SAM_DEMO_ROLE TO ROLE SYSADMIN;

-- ============================================================================
-- SECTION 3: Warehouse (Single LARGE warehouse for all operations)
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS SAM_DEMO_WH
    WAREHOUSE_SIZE = '2X-LARGE'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for SAM demo operations';

-- Ensure warehouse is 2X-LARGE (in case it already exists with different size)
ALTER WAREHOUSE SAM_DEMO_WH SET WAREHOUSE_SIZE = '2X-LARGE';

-- Grant warehouse permissions
GRANT USAGE ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;
GRANT OPERATE ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 4: Marketplace Data Access
-- ============================================================================

-- PREREQUISITE: Accept Marketplace listing terms first
-- https://app.snowflake.com/marketplace/listing/GZTSZ290BV255

GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 5: Snowflake Intelligence and Cortex Setup
-- ============================================================================

-- Create Snowflake Intelligence object
CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;

-- Snowflake Intelligence grants
GRANT CREATE SNOWFLAKE INTELLIGENCE ON ACCOUNT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE PUBLIC;

-- AI/Cortex component creation grants
GRANT CREATE AGENT ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE SEMANTIC VIEW ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- Account-level Cortex privileges (required for LLM functions)
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE SAM_DEMO_ROLE;

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
GRANT READ ON SECRET SAM_DEMO.PUBLIC.GITHUB_SECRET TO ROLE SAM_DEMO_ROLE;

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

-- Grant Git repository usage to role
GRANT READ ON GIT REPOSITORY SAM_DEMO.PUBLIC.sam_demo_repo TO ROLE SAM_DEMO_ROLE;

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
    
    # All Python modules needed for SAM demo (from am_ai_demo source)
    python_files = [
        # Core configuration and utilities
        'config.py', 'config_accessors.py', 'db_helpers.py', 'demo_helpers.py',
        'logging_utils.py', 'scenario_utils.py', 'snowflake_io_utils.py',
        'sql_case_builders.py', 'sql_utils.py', 'rules_loader.py',
        # Data generation
        'generate_structured.py', 'generate_unstructured.py', 'generate_market_data.py',
        'generate_real_transcripts.py', 'hydration_engine.py',
        # AI component builders
        'build_ai.py', 'create_agents.py', 'create_semantic_views.py', 'create_cortex_search.py'
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
                    # LIST returns relative path - need to use full stage path for GET
                    full_stage_path = f"{git_stage}/content_library/{rel_path}"
                    session.file.get(full_stage_path, local_dir + '/')
                    template_count += 1
                except Exception as get_err:
                    results.append(f"    Warning: Could not download {rel_path}: {get_err}")
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
    
    # Import modules for data generation
    import generate_structured
    import generate_market_data
    
    # Step 3: Build dimension tables (do NOT depend on max_price_date)
    results.append("\n=== Step 3: Building dimension tables ===")
    try:
        generate_structured.create_database_structure(session, recreate_database=False)
        generate_structured.build_dimension_tables(session, test_mode=test_mode)
        results.append("  Dimension tables complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 4: Build FACT_STOCK_PRICES as date anchor (MUST happen before fact tables)
    results.append("\n=== Step 4: Building price anchor (FACT_STOCK_PRICES) ===")
    try:
        generate_market_data.build_price_anchor(session, test_mode=test_mode)
        results.append("  Price anchor established!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 5: Build fact tables (depend on max_price_date from stock prices)
    results.append("\n=== Step 5: Building fact tables ===")
    try:
        generate_structured.build_fact_tables(session, test_mode=test_mode)
        results.append("  Fact tables complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 6: Build scenario-specific data
    results.append("\n=== Step 6: Building scenario data ===")
    try:
        for scenario in config.AVAILABLE_SCENARIOS:
            generate_structured.build_scenario_data(session, scenario)
        generate_structured.validate_data_quality(session)
        results.append("  Scenario data complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 7: Build remaining market data (SEC filings, financials, estimates)
    results.append("\n=== Step 7: Building remaining market data ===")
    try:
        generate_market_data.build_all(session, test_mode=test_mode)
        results.append("  Market data complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 7.5: Build performance views (required by SAM_ANALYST_VIEW)
    # These depend on market data (FACT_STOCK_PRICES) and must be built before semantic views
    results.append("\n=== Step 7.5: Building performance views ===")
    try:
        # Build returns view and update enriched holdings
        generate_structured.build_security_returns_view(session)
        generate_structured.build_esg_latest_view(session)  # Rebuild to include returns
        results.append("  Security returns and ESG views complete!")
        
        # Build strategy performance
        generate_structured.build_fact_strategy_performance(session)
        results.append("  Strategy performance complete!")
        
        # Build benchmark performance (required by SAM_ANALYST_VIEW)
        generate_structured.build_fact_benchmark_performance(session)
        results.append("  Benchmark performance complete!")
        
        # Build portfolio vs benchmark comparison view (required by SAM_ANALYST_VIEW)
        generate_structured.build_portfolio_benchmark_comparison_view(session)
        results.append("  Portfolio vs benchmark view complete!")
    except Exception as e:
        results.append(f"  ERROR building performance views: {e}")
        raise
    
    # Step 8: Generate real transcripts (with fallback to synthetic)
    results.append("\n=== Step 8: Generating transcripts ===")
    real_transcripts_available = False
    try:
        import generate_real_transcripts
        # Check if real data source is available
        if generate_real_transcripts.verify_transcripts_available(session):
            generate_real_transcripts.build_all(session, test_mode=test_mode)
            results.append("  Real transcripts complete!")
            real_transcripts_available = True
        else:
            results.append("  Real transcript source not available - will use synthetic fallback")
    except Exception as e:
        results.append(f"  Real transcripts failed: {e} - will use synthetic fallback")
    
    # If real transcripts not available, log warning (synthetic requires templates that may not exist)
    if not real_transcripts_available:
        results.append("  INFO: Real transcripts not available. SAM_COMPANY_EVENTS search will use fallback logic.")
        results.append("  (Search service will fall back to EARNINGS_TRANSCRIPTS_CORPUS if available)")
    
    # Step 9: Generate unstructured documents
    results.append("\n=== Step 9: Generating documents from templates ===")
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

CREATE OR REPLACE PROCEDURE SAM_DEMO.PUBLIC.SETUP_AI_COMPONENTS(FORCE_REBUILD BOOLEAN DEFAULT TRUE)
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

def run_ai_setup(session, force_rebuild: bool = False) -> str:
    """
    Creates AI components: semantic views and Cortex Search services.
    
    Args:
        force_rebuild: If True, recreate all search services even if they exist.
                      If False (default), skip existing search services for faster setup.
    """
    import tempfile
    
    # Create temp directory and download modules
    tmp_dir = tempfile.mkdtemp(prefix='sam_ai_')
    python_dir = os.path.join(tmp_dir, 'python')
    os.makedirs(python_dir, exist_ok=True)
    
    results = []
    git_stage = '@SAM_DEMO.PUBLIC.sam_demo_repo/branches/main'
    
    # Download required Python files (includes all dependencies)
    python_files = [
        'config.py', 'config_accessors.py', 'db_helpers.py', 'demo_helpers.py',
        'logging_utils.py', 'scenario_utils.py',
        'build_ai.py', 'create_semantic_views.py', 'create_cortex_search.py'
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
    results.append(f"\n=== Creating Cortex Search Services (force_rebuild={force_rebuild}) ===")
    try:
        import create_cortex_search
        create_cortex_search.create_search_services(session, all_scenarios, force_rebuild=force_rebuild)
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
    
    # Download required Python files (includes all dependencies)
    python_files = [
        'config.py', 'config_accessors.py', 'db_helpers.py', 'demo_helpers.py',
        'logging_utils.py', 'create_agents.py'
    ]
    
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
-- SECTION 8: Custom Tools (PDF Generation, M&A Simulation)
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

-- ============================================================================
-- PDF Report Generator (used by all agents with pdf_generator tool)
-- ============================================================================
CREATE OR REPLACE PROCEDURE SAM_DEMO.AI.GENERATE_PDF_REPORT(
    MARKDOWN_CONTENT VARCHAR,
    REPORT_TITLE VARCHAR,
    DOCUMENT_AUDIENCE VARCHAR DEFAULT 'internal'
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'markdown', 'fpdf2')
HANDLER = 'generate_pdf_report'
EXECUTE AS CALLER
AS
$$
from snowflake.snowpark import Session
from datetime import datetime
import re
import markdown
import tempfile
import os

def generate_pdf_report(session: Session, markdown_content: str, report_title: str, document_audience: str = 'internal'):
    """
    Generate professional branded PDF report from markdown content.
    
    Args:
        markdown_content: Complete markdown document
        report_title: Title for the document header
        document_audience: 'internal', 'external_client', or 'external_regulatory'
    
    Returns:
        Markdown link to presigned URL for PDF download
    """
    from fpdf import FPDF
    import html
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', report_title)[:40]
    pdf_filename = f'{safe_title}_{timestamp}.pdf'
    
    # Audience-specific config
    audience_configs = {
        'internal': {'badge': 'INTERNAL DOCUMENT', 'color': (31, 78, 121)},
        'external_client': {'badge': 'CLIENT REPORT', 'color': (44, 62, 80)},
        'external_regulatory': {'badge': 'REGULATORY SUBMISSION', 'color': (52, 73, 94)}
    }
    config = audience_configs.get(document_audience, audience_configs['internal'])
    
    class PDFReport(FPDF):
        def __init__(self, title, badge, color):
            super().__init__()
            self.title_text = title
            self.badge_text = badge
            self.header_color = color
            
        def header(self):
            # Header background
            self.set_fill_color(*self.header_color)
            self.rect(0, 0, 210, 35, 'F')
            
            # Company name
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 16)
            self.set_xy(10, 8)
            self.cell(0, 8, 'SNOWCREST ASSET MANAGEMENT', align='C')
            
            # Report title
            self.set_font('Helvetica', '', 11)
            self.set_xy(10, 18)
            self.cell(0, 6, self.title_text[:60], align='C')
            
            # Badge
            self.set_font('Helvetica', 'B', 8)
            self.set_xy(10, 26)
            self.cell(0, 6, self.badge_text, align='C')
            
            self.set_text_color(0, 0, 0)
            self.ln(40)
            
        def footer(self):
            self.set_y(-20)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, f'Generated: {datetime.now().strftime("%B %d, %Y")} | Snowflake Intelligence', align='C')
            self.ln(4)
            self.cell(0, 5, f'Page {self.page_no()}', align='C')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create PDF
        pdf = PDFReport(report_title, config['badge'], config['color'])
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=25)
        
        # Demo disclaimer
        pdf.set_fill_color(255, 243, 205)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.multi_cell(0, 6, 'DEMO DISCLAIMER: This document uses synthetic data for demonstration only.', fill=True, align='C')
        pdf.ln(8)
        
        # Process markdown content
        lines = markdown_content.split('\\n')
        pdf.set_font('Helvetica', '', 10)
        
        for line in lines:
            line = line.strip()
            if not line:
                pdf.ln(3)
                continue
                
            # Headers
            if line.startswith('# '):
                pdf.set_font('Helvetica', 'B', 14)
                pdf.set_text_color(*config['color'])
                pdf.ln(5)
                pdf.multi_cell(0, 7, line[2:])
                pdf.set_text_color(0, 0, 0)
                pdf.ln(3)
            elif line.startswith('## '):
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(*config['color'])
                pdf.ln(4)
                pdf.multi_cell(0, 6, line[3:])
                pdf.set_text_color(0, 0, 0)
                pdf.ln(2)
            elif line.startswith('### '):
                pdf.set_font('Helvetica', 'B', 11)
                pdf.ln(3)
                pdf.multi_cell(0, 6, line[4:])
                pdf.ln(2)
            elif line.startswith('**') and line.endswith('**'):
                pdf.set_font('Helvetica', 'B', 10)
                pdf.multi_cell(0, 5, line.replace('**', ''))
                pdf.set_font('Helvetica', '', 10)
            elif line.startswith('- ') or line.startswith('* '):
                pdf.set_font('Helvetica', '', 10)
                pdf.cell(5, 5, chr(149))  # Bullet
                pdf.multi_cell(0, 5, line[2:])
            elif line.startswith('|'):
                # Simple table row handling
                pdf.set_font('Helvetica', '', 9)
                cells = [c.strip() for c in line.split('|') if c.strip() and c.strip() != '---']
                if cells and not all(c.startswith('-') for c in cells):
                    col_width = 180 / max(len(cells), 1)
                    for cell in cells:
                        pdf.cell(col_width, 6, cell[:25], border=1)
                    pdf.ln()
            else:
                pdf.set_font('Helvetica', '', 10)
                # Clean markdown formatting
                clean_line = re.sub(r'\\*\\*(.+?)\\*\\*', r'\\1', line)
                clean_line = re.sub(r'\\*(.+?)\\*', r'\\1', clean_line)
                clean_line = re.sub(r'`(.+?)`', r'\\1', clean_line)
                pdf.multi_cell(0, 5, clean_line)
        
        # Save PDF
        pdf_path = os.path.join(tmpdir, pdf_filename)
        pdf.output(pdf_path)
        
        # Upload to stage
        stage_path = '@SAM_DEMO.CURATED.SAM_REPORTS_STAGE'
        session.file.put(pdf_path, stage_path, overwrite=True, auto_compress=False)
        
        # Get presigned URL
        presigned_url = session.sql(
            f"SELECT GET_PRESIGNED_URL('{stage_path}', '{pdf_filename}') AS url"
        ).collect()[0]['URL']
        
        return f"📄 **Report Generated Successfully**\\n\\n[📥 Download: {report_title}]({presigned_url})\\n\\n*Document Type: {document_audience.replace('_', ' ').title()}*"
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
