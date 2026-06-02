-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--      http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--
-- Created by Mats Stellwall, Snowflake, and Snowflake CoCo

-- ============================================================================
-- SAM Demo — Infrastructure Setup (Workspace Prerequisites)
-- ============================================================================
--
-- Run this script ONCE in a Snowflake worksheet before using the Git Workspace.
-- It creates the database, schemas, roles, grants, and enables Cortex features.
--
-- After running this script:
--   1. Go to Projects > Workspaces
--   2. Create workspace "From Git repository":
--      https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management.git
--   3. Open python/workspace_main.py
--   4. Connect a notebook service (Python 3.11+, any compute pool)
--   5. Install packages: snowflake-snowpark-python, pyyaml, jinja2
--   6. Click "Run" — the full setup takes ~15-20 minutes
--
-- REQUIRES: ACCOUNTADMIN role
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Set query tag for tracking
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"agentic_ai_for_asset_management","version":{"major":2,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

-- ============================================================================
-- SECTION 1: Warehouse
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS SAM_DEMO_WH
    WAREHOUSE_SIZE = 'XLARGE'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = FALSE
    COMMENT = 'Warehouse for SAM demo operations';

USE WAREHOUSE SAM_DEMO_WH;

-- ============================================================================
-- SECTION 2: Marketplace Data (Snowflake Public Data - Free)
-- ============================================================================

-- Auto-install financial data share (14,000+ securities, SEC filings, etc.)
CALL SYSTEM$REQUEST_LISTING_AND_WAIT('GZTSZ290BV255');
CALL SYSTEM$ACCEPT_LEGAL_TERMS('DATA_EXCHANGE_LISTING', 'GZTSZ290BV255');
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_PUBLIC_DATA_FREE FROM LISTING 'GZTSZ290BV255';

-- ============================================================================
-- SECTION 3: Database and Schemas
-- ============================================================================

CREATE DATABASE IF NOT EXISTS SAM_DEMO
    COMMENT = 'Simulated Asset Management (SAM) - Agentic AI Demo Database';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.RAW
    COMMENT = 'Raw data layer - external data and unprocessed documents';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.CURATED
    COMMENT = 'Curated data layer - clean, validated, business-ready data';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.AI
    COMMENT = 'AI components - semantic views, search services, agents, tools';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.PUBLIC
    COMMENT = 'Public schema';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.MARKET_DATA
    COMMENT = 'Market data layer - real market data from external sources';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.ML
    COMMENT = 'Machine learning models, predictions, and feature store';

-- ============================================================================
-- SECTION 4: Role and Privileges
-- ============================================================================

CREATE ROLE IF NOT EXISTS SAM_DEMO_ROLE
    COMMENT = 'Dedicated role for SAM demo operations';

-- Database-level
GRANT USAGE ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;
GRANT CREATE SCHEMA ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;

-- Schema-level (covers all object types: tables, views, procedures, functions, stages)
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.ML TO ROLE SAM_DEMO_ROLE;

-- Role hierarchy
GRANT ROLE SAM_DEMO_ROLE TO ROLE ACCOUNTADMIN;
GRANT ROLE SAM_DEMO_ROLE TO ROLE SYSADMIN;

-- Warehouse privileges
GRANT USAGE ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;
GRANT OPERATE ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;

-- Marketplace data access
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 5: Cortex AI Privileges
-- ============================================================================

-- AI/Cortex component creation grants
GRANT CREATE AGENT ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE SEMANTIC VIEW ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- Account-level Cortex privileges (required for LLM functions)
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE SAM_DEMO_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE SAM_DEMO_ROLE;

-- Enable cross-region Cortex (required for accounts not in Cortex-enabled regions)
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- ============================================================================
-- SECTION 6: Task Privileges (Scheduling)
-- ============================================================================
-- Required for:
--   - Deploying notebooks as scheduled tasks
--   - Stream-triggered incremental data pipelines
--   - Periodic agent operations (morning briefings, signal extraction)

GRANT EXECUTE TASK ON ACCOUNT TO ROLE SAM_DEMO_ROLE;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE SAM_DEMO_ROLE;
GRANT CREATE TASK ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE TASK ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT CREATE TASK ON SCHEMA SAM_DEMO.ML TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 7: Snowflake Intelligence
-- ============================================================================

CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;
GRANT CREATE SNOWFLAKE INTELLIGENCE ON ACCOUNT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE PUBLIC;

-- ============================================================================
-- DONE — Next Steps
-- ============================================================================
--
-- Infrastructure is ready. Now set up the demo data and agents:
--
--   1. Go to Projects > Workspaces
--   2. Click "+" → "From Git repository"
--   3. Repository URL: https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management.git
--   4. Authentication: Public repository (no auth needed)
--   5. Open python/workspace_main.py
--   6. Connect a notebook service:
--      - Python version: 3.11
--      - Compute pool: any available pool
--   7. Install packages (via Packages panel):
--      - snowflake-snowpark-python
--      - pyyaml
--      - jinja2
--   8. Click "Run" — setup takes ~15-20 minutes
--
-- After completion:
--   - Open Snowflake Intelligence to interact with the agents
--   - Open the notebooks (factor_discovery, market_regime_detection, credit_risk_model)
--     for ML workflow demonstrations
--
-- ============================================================================

SELECT 'Infrastructure setup complete. Open a Git Workspace and run python/workspace_main.py' AS status;
