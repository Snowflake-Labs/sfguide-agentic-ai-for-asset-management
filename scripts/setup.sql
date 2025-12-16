-- ============================================================================
-- SAM Demo - Infrastructure Setup
-- ============================================================================
-- This file creates the foundational database infrastructure
-- Purpose: Database, schemas, role, and warehouse setup
-- Requires: ACCOUNTADMIN role
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

-- Grant privileges on all existing tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant privileges on all future tables
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Grant role to ACCOUNTADMIN
GRANT ROLE SAM_DEMO_ROLE TO ROLE ACCOUNTADMIN;

-- ============================================================================
-- SECTION 3: Warehouse
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS SAM_DEMO_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for SAM demo operations';

-- Grant warehouse usage
GRANT USAGE ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 4: Marketplace Data Access
-- ============================================================================

-- PREREQUISITE: Accept Marketplace listing terms first (see README Step 1)
-- https://app.snowflake.com/marketplace/listing/GZTSZ290BV255

-- Grant privileges on Snowflake Public Data database
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 5: Snowflake Intelligence Setup (Required for Agents)
-- ============================================================================

-- Create Snowflake Intelligence object if it doesn't exist
CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;

-- Grant permissions to create Snowflake Intelligence objects
GRANT CREATE SNOWFLAKE INTELLIGENCE ON ACCOUNT TO ROLE SAM_DEMO_ROLE;

-- Grant usage and modify permissions on Snowflake Intelligence
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;

-- Grant public access to Snowflake Intelligence (for agent invocation)
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE PUBLIC;

-- Grant permissions to create agents in AI schema
GRANT CREATE AGENT ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- Grant permissions to create Cortex Search services in AI schema
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- Grant permissions to create semantic views in AI schema
GRANT CREATE SEMANTIC VIEW ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 6: Git Integration & Notebook Setup
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
  ORIGIN = 'https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management.git'
  COMMENT = 'Git repository for SAM demo setup files';

-- Fetch latest code from Git
ALTER GIT REPOSITORY SAM_DEMO.PUBLIC.sam_demo_repo FETCH;

-- Create notebook from Git repository (FROM must be a directory, MAIN_FILE specifies the notebook)
CREATE OR REPLACE NOTEBOOK SAM_DEMO.PUBLIC.SAM_Demo_Complete_Setup
  FROM '@SAM_DEMO.PUBLIC.sam_demo_repo/branches/main/notebooks/'
  QUERY_WAREHOUSE = SAM_DEMO_WH
  MAIN_FILE = '0_start_here.ipynb'
  COMMENT = 'Complete SAM demo setup - creates data model, documents, search services, semantic views, and agents';

-- Note: Notebook ownership is automatically assigned to the creating role

-- ============================================================================
-- SECTION 7: Execute Complete Setup
-- ============================================================================

-- Switch to SAM_DEMO_ROLE for notebook execution
USE ROLE SAM_DEMO_ROLE;
USE WAREHOUSE SAM_DEMO_WH;

-- Create a live version of the notebook 
ALTER NOTEBOOK SAM_DEMO.PUBLIC.SAM_Demo_Complete_Setup ADD LIVE VERSION FROM LAST;
EXECUTE NOTEBOOK SAM_DEMO.PUBLIC.SAM_Demo_Complete_Setup();

-- ============================================================================
-- Setup Complete!
-- ============================================================================
