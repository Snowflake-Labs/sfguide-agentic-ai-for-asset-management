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
-- SAM Demo — Full Setup (Infrastructure + Build)
-- ============================================================================
--
-- Run this script ONCE to stand up the whole demo. It:
--   1. Creates the warehouses, database, schemas, roles, grants and compute
--      pools, and enables the Cortex features (Sections 1-8)
--   2. Creates the build Code Bundle and runs it (Section 9), which generates
--      the data, semantic views, Cortex Search services, agents and skills
--
-- BEFORE YOU START: create a Snowflake Workspace from this Git repository, then
-- set its name in $ws_name immediately below. That is the only value you need to
-- edit, and it is at the top so that running the whole script in one go works.
--
-- The build is installed and run from here, so there is no pip install, no
-- kernel restart and no "click Run" step.
--
-- REQUIRES: ACCOUNTADMIN role
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Set query tag for tracking
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"agentic_ai_for_asset_management","version":{"major":2,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

-- ============================================================================
-- SECTION 0: Configuration — THE ONLY VALUE YOU NEED TO CHANGE
-- ============================================================================
-- The name of the Workspace you created from this repository. Section 9 builds
-- the Code Bundle from it. Set here rather than next to its use in Section 9, so
-- that running the entire script top to bottom works without editing mid-file.
--
-- Run this to see the workspaces you have and where they live:
--     SHOW WORKSPACES IN ACCOUNT;

SET ws_name = 'SAM_DEMO_WORKSPACE';

-- Git-backed workspaces live in your personal database, USER$<your_user>.PUBLIC.
-- If SHOW WORKSPACES IN ACCOUNT lists yours in a different database or schema,
-- replace this expression with that path, for example:
--   SET bundle_src = 'snow://workspace/"MY_DB"."MY_SCHEMA"."MY_WS"/versions/live';
SET bundle_src = 'snow://workspace/"USER$' || CURRENT_USER() || '"."PUBLIC"."' || $ws_name || '"/versions/live';

-- ============================================================================
-- SECTION 1: Warehouses
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS SAM_DEMO_EXECUTION_WH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = FALSE
    COMMENT = 'Warehouse for SAM demo data generation and agent execution';

CREATE WAREHOUSE IF NOT EXISTS SAM_DEMO_CORTEX_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = FALSE
    COMMENT = 'Warehouse for SAM demo Cortex Search services';

USE WAREHOUSE SAM_DEMO_EXECUTION_WH;

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

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.MARKET_DATA
    COMMENT = 'Market data layer - real market data from external sources';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.ML
    COMMENT = 'Machine learning models, predictions, and feature store';

-- ============================================================================
-- SECTION 3.5: Shared FSI Demo Infrastructure
-- ============================================================================
-- These objects are shared across FSI demos rather than owned by SAM_DEMO, and
-- they are created here because later sections GRANT on them: Section 4 grants
-- USAGE on FSI_DEMO_STREAMLIT_COMPUTE_POOL and Section 6 grants USAGE on
-- FSI_DEMO_PYPI_ACCESS. Previously both were assumed to already exist, so on a
-- fresh account this script aborted with "does not exist or not authorized".
--
-- All are IF NOT EXISTS, so accounts that already have them are unaffected and
-- the existing definitions are left exactly as they are.

-- FSI_DEMO_CONFIG is also created in Section 4 for the APP schema. Creating it
-- here as well is harmless and idempotent, and is required because the PyPI
-- network rule lives in it.
CREATE DATABASE IF NOT EXISTS FSI_DEMO_CONFIG;
CREATE SCHEMA IF NOT EXISTS FSI_DEMO_CONFIG.NETWORK_RULES
    COMMENT = 'Network rules for FSI demo external access';

-- Egress to PyPI, used by the Streamlit container-runtime deployment, which
-- passes this integration in CREATE STREAMLIT (see
-- python/ai/tools/streamlit_deploy.py).
--
-- NOTE: the Code Bundles deliberately do NOT use this. They install packages
-- from Snowflake's shared PyPI artifact repository instead, declared as
-- artifact_repositories in code_bundle.yml, which needs no network rule and no
-- ACCOUNTADMIN-created integration. Verified empirically: a bundle with neither
-- fails with "Failed to install packages from the requirements file", and one
-- with only the artifact repository succeeds.
CREATE NETWORK RULE IF NOT EXISTS FSI_DEMO_CONFIG.NETWORK_RULES.PYPI_NETWORK_RULE
    TYPE = HOST_PORT
    MODE = EGRESS
    VALUE_LIST = ('pypi.org:443', 'files.pythonhosted.org:443')
    COMMENT = 'Network rule for PyPI package access';

CREATE EXTERNAL ACCESS INTEGRATION IF NOT EXISTS FSI_DEMO_PYPI_ACCESS
    ALLOWED_NETWORK_RULES = (FSI_DEMO_CONFIG.NETWORK_RULES.PYPI_NETWORK_RULE)
    ENABLED = TRUE
    COMMENT = 'External access integration for PyPI packages';

-- Serves the Streamlit apps. GEN_X64_G2_4 is the current-generation equivalent
-- of CPU_X64_S: identical 3 vCPU / 13 GiB, better price-performance.
--
-- NOTE: on an account where this pool already exists, IF NOT EXISTS is a no-op
-- and the pool keeps its original instance family. Changing it is deliberate
-- manual work, because INSTANCE_FAMILY can only be altered while the pool is
-- fully suspended, which stops any service running on it:
--   ALTER COMPUTE POOL FSI_DEMO_STREAMLIT_COMPUTE_POOL SUSPEND;
--   ALTER COMPUTE POOL FSI_DEMO_STREAMLIT_COMPUTE_POOL SET INSTANCE_FAMILY = GEN_X64_G2_4;
--   ALTER COMPUTE POOL FSI_DEMO_STREAMLIT_COMPUTE_POOL RESUME;
CREATE COMPUTE POOL IF NOT EXISTS FSI_DEMO_STREAMLIT_COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 4
    INSTANCE_FAMILY = GEN_X64_G2_4
    AUTO_SUSPEND_SECS = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'CPU based compute pool for streamlit applications in FSI Demos';

-- ============================================================================
-- SECTION 4: Role and Privileges
-- ============================================================================

CREATE ROLE IF NOT EXISTS FSI_DEMO_BUILD_ROLE
    COMMENT = 'Shared build and platform role for FSI demos';

CREATE ROLE IF NOT EXISTS SAM_DEMO_USER_ROLE
    COMMENT = 'Runtime role for consuming the SAM demo';

-- Database-level
GRANT CREATE DATABASE ON ACCOUNT TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON DATABASE SAM_DEMO TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_USER_ROLE;
GRANT CREATE SCHEMA ON DATABASE SAM_DEMO TO ROLE FSI_DEMO_BUILD_ROLE;

-- Schema-level (covers all object types: tables, views, procedures, functions, stages)
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.RAW TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.CURATED TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.AI TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.ML TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON SCHEMA SAM_DEMO.ML TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA SAM_DEMO.ML TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA SAM_DEMO.ML TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA SAM_DEMO.ML TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA SAM_DEMO.ML TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON ALL STAGES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON FUTURE STAGES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
-- READ on the PDF source stages lets Snowflake CoWork open the cited document from a
-- Cortex Search citation (agent search tools set stage_path / relative_path_column).
GRANT READ ON ALL STAGES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_USER_ROLE;
GRANT READ ON FUTURE STAGES IN SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON ALL FUNCTIONS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON FUTURE FUNCTIONS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON ALL PROCEDURES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;

-- Role hierarchy
GRANT ROLE FSI_DEMO_BUILD_ROLE TO ROLE ACCOUNTADMIN;
GRANT ROLE FSI_DEMO_BUILD_ROLE TO ROLE SYSADMIN;
GRANT ROLE SAM_DEMO_USER_ROLE TO ROLE FSI_DEMO_BUILD_ROLE;
SET current_username = CURRENT_USER();
GRANT ROLE FSI_DEMO_BUILD_ROLE TO USER IDENTIFIER($current_username);

-- Warehouse privileges
GRANT USAGE ON WAREHOUSE SAM_DEMO_EXECUTION_WH TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT OPERATE ON WAREHOUSE SAM_DEMO_EXECUTION_WH TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT MODIFY ON WAREHOUSE SAM_DEMO_EXECUTION_WH TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON WAREHOUSE SAM_DEMO_EXECUTION_WH TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON WAREHOUSE SAM_DEMO_CORTEX_WH TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT OPERATE ON WAREHOUSE SAM_DEMO_CORTEX_WH TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT MODIFY ON WAREHOUSE SAM_DEMO_CORTEX_WH TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON WAREHOUSE SAM_DEMO_CORTEX_WH TO ROLE SAM_DEMO_USER_ROLE;
-- FSI_DEMO_STREAMLIT_COMPUTE_POOL is a COMPUTE POOL, not a warehouse. Granting it
-- as a warehouse fails ("does not exist or not authorized") and aborts the script.
GRANT USAGE ON COMPUTE POOL FSI_DEMO_STREAMLIT_COMPUTE_POOL TO ROLE FSI_DEMO_BUILD_ROLE;

-- Marketplace data access
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE SAM_DEMO_USER_ROLE;

CREATE DATABASE IF NOT EXISTS FSI_DEMO_CONFIG;
GRANT CREATE SCHEMA ON DATABASE FSI_DEMO_CONFIG TO ROLE FSI_DEMO_BUILD_ROLE;
CREATE SCHEMA IF NOT EXISTS FSI_DEMO_CONFIG.APP;
GRANT USAGE ON DATABASE FSI_DEMO_CONFIG TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON DATABASE FSI_DEMO_CONFIG TO ROLE SAM_DEMO_USER_ROLE;
GRANT USAGE ON SCHEMA FSI_DEMO_CONFIG.APP TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE TABLE ON SCHEMA FSI_DEMO_CONFIG.APP TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON SCHEMA FSI_DEMO_CONFIG.APP TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA FSI_DEMO_CONFIG.APP TO ROLE SAM_DEMO_USER_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA FSI_DEMO_CONFIG.APP TO ROLE SAM_DEMO_USER_ROLE;

-- ============================================================================
-- SECTION 5: Cortex AI Privileges
-- ============================================================================

-- AI/Cortex component creation grants
GRANT CREATE AGENT ON SCHEMA SAM_DEMO.AI TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA SAM_DEMO.AI TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE SEMANTIC VIEW ON SCHEMA SAM_DEMO.AI TO ROLE FSI_DEMO_BUILD_ROLE;

-- Account-level Cortex privileges (required for LLM functions)
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE SAM_DEMO_USER_ROLE;

-- Enable cross-region Cortex (required for accounts not in Cortex-enabled regions)
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- ============================================================================
-- SECTION 6: Task Privileges (Scheduling)
-- ============================================================================
-- Required for:
--   - Deploying notebooks as scheduled tasks
--   - Stream-triggered incremental data pipelines
--   - Periodic agent operations (morning briefings, signal extraction)

GRANT EXECUTE TASK ON ACCOUNT TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE FSI_DEMO_BUILD_ROLE;
-- For the Streamlit container-runtime deployment. The Code Bundles use the
-- shared PyPI artifact repository instead - see the note in Section 3.5.
GRANT USAGE ON INTEGRATION FSI_DEMO_PYPI_ACCESS TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE TASK ON SCHEMA SAM_DEMO.RAW TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE TASK ON SCHEMA SAM_DEMO.CURATED TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE TASK ON SCHEMA SAM_DEMO.AI TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE TASK ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT CREATE TASK ON SCHEMA SAM_DEMO.ML TO ROLE FSI_DEMO_BUILD_ROLE;


-- ============================================================================
-- SECTION 7: Weekly Refresh Automation (Code Bundle)
-- ============================================================================
-- The weekly incremental refresh runs as a Code Bundle on a dedicated compute
-- pool, driven by SAM_DEMO.AI.WEEKLY_REFRESH_TASK (created by the Python build).
--
-- Role split: FSI_DEMO_BUILD_ROLE owns, executes and operates the automation.
-- SAM_DEMO_USER_ROLE is the demo *consumer* and deliberately gets visibility
-- only - a demo user triggering a refresh mid-demo would mutate the very data
-- they are presenting.

-- A dedicated pool rather than sharing SAM_DEMO_COMPUTE_POOL: that pool serves
-- the Streamlit apps, and a weekly batch job should neither contend with them
-- nor keep them warm. MAX_NODES = 1 because exactly one job runs per week.
--
-- GEN_X64_G2_4 is the current-generation equivalent of CPU_X64_S: identical
-- 3 vCPU / 13 GiB, better price-performance. See the note in Section 3.5 for how
-- to migrate a pool that already exists, since IF NOT EXISTS will not change it.
CREATE COMPUTE POOL IF NOT EXISTS SAM_DEMO_BUNDLE_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = GEN_X64_G2_4
    AUTO_SUSPEND_SECS = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Dedicated pool for the SAM demo weekly refresh Code Bundle';

GRANT USAGE ON COMPUTE POOL SAM_DEMO_BUNDLE_POOL TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT MONITOR ON COMPUTE POOL SAM_DEMO_BUNDLE_POOL TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT OPERATE ON COMPUTE POOL SAM_DEMO_BUNDLE_POOL TO ROLE FSI_DEMO_BUILD_ROLE;

-- Pool for the ML notebooks (factor_discovery, market_regime_detection,
-- credit_risk_model). Attach the notebook service to this pool rather than
-- picking an arbitrary one, so the ML demos have a predictable environment.
--
-- Memory-optimised rather than general purpose: xgboost and especially SHAP are
-- memory-bound, not CPU-bound. MEM_X64_G2_8 gives 6 vCPU / 58 GiB, versus
-- 6 vCPU / 28 GiB for the general-purpose GEN_X64_G2_8 at the same vCPU count.
CREATE COMPUTE POOL IF NOT EXISTS SAM_DEMO_ML_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = MEM_X64_G2_8
    AUTO_SUSPEND_SECS = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Pool for the SAM demo ML notebooks';

GRANT USAGE ON COMPUTE POOL SAM_DEMO_ML_POOL TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT MONITOR ON COMPUTE POOL SAM_DEMO_ML_POOL TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT OPERATE ON COMPUTE POOL SAM_DEMO_ML_POOL TO ROLE FSI_DEMO_BUILD_ROLE;

-- Lets the build role create the bundle. Note: Snowflake still reports this
-- privilege under its pre-rename name, CREATE NOTEBOOK PROJECT, in SHOW GRANTS.
GRANT CREATE CODE BUNDLE ON SCHEMA SAM_DEMO.AI TO ROLE FSI_DEMO_BUILD_ROLE;

-- EXECUTE CODE BUNDLE on a compute pool requires USAGE *and MONITOR* on the
-- query warehouse. Section 4 grants USAGE/OPERATE/MODIFY but not MONITOR, and
-- without it the scheduled task fails at execution time, not at creation - so
-- the automation would look correctly installed and never actually run.
GRANT MONITOR ON WAREHOUSE SAM_DEMO_EXECUTION_WH TO ROLE FSI_DEMO_BUILD_ROLE;

-- Visibility only. The demo narrative is "this refreshes itself every week", so
-- the demo role can inspect the task and its run history. Deliberately no
-- OPERATE on the task and no USAGE on the Code Bundle, so it cannot start one.
GRANT MONITOR ON ALL TASKS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;
GRANT MONITOR ON FUTURE TASKS IN SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_USER_ROLE;

-- ============================================================================
-- SECTION 8: Snowflake CoWork
-- ============================================================================

CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;
GRANT CREATE SNOWFLAKE INTELLIGENCE ON ACCOUNT TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT MODIFY ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE FSI_DEMO_BUILD_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_USER_ROLE;

-- ============================================================================
-- SECTION 9: Build the Demo (Code Bundle)
-- ============================================================================
-- The full build runs as a Code Bundle rather than by opening a file and
-- clicking "Run". Packages are installed declaratively from code_bundle.yml, so
-- there is no manual pip step, and every run is recorded in CODE_BUNDLE_HISTORY.
--
-- Source is the workspace live path, not a stage. That resolves a bootstrap
-- problem: staging files needs a Python client, but this bundle IS how the
-- Python runs, so it cannot stage its own source. The workspace already holds
-- the files, so no upload is needed. (The weekly refresh bundle, created later
-- by the build itself, deliberately uses a stage instead - a scheduled task must
-- not depend on a user's workspace continuing to exist.)
--
-- PREREQUISITE: $ws_name and $bundle_src are set in Section 0 at the top of this
-- script. If you have not set $ws_name yet, go back and do that now.

USE ROLE FSI_DEMO_BUILD_ROLE;
USE DATABASE SAM_DEMO;
USE SCHEMA AI;
USE WAREHOUSE SAM_DEMO_EXECUTION_WH;

-- Confirm what Section 0 resolved to before creating anything from it.
SELECT $ws_name AS workspace_name, $bundle_src AS bundle_source;

SET create_bundle_stmt =
    'CREATE OR REPLACE CODE BUNDLE SAM_DEMO.AI.SAM_BUILD_BUNDLE FROM ''' || $bundle_src ||
    ''' COMMENT = ''SAM demo full environment build''';

EXECUTE IMMEDIATE $create_bundle_stmt;

-- IMPORTANT: check the result of the statement above. A wrong workspace name does
-- NOT fail here - the bundle is created and you get only a warning:
--   "source directory ... does not exist or contains no files"
-- If you see that warning, fix $ws_name and re-run before continuing, otherwise
-- the build below fails with a missing entrypoint.

-- ----------------------------------------------------------------------------
-- Run the build. Takes roughly 45-60 minutes and runs synchronously, so leave
-- the worksheet open. Progress is visible in the query result.
--
-- Measured: 56 minutes on SAM_DEMO_BUNDLE_POOL with a single CPU_X64_S node.
-- Most of that is Python-side document generation, which is CPU-bound on the
-- compute pool rather than warehouse work, so INSTANCE_FAMILY on that pool is
-- the lever if you need it faster. Section 7 declares GEN_X64_G2_4 for new
-- accounts; an account where the pool already exists keeps its old family,
-- because IF NOT EXISTS is a no-op (see the note in Section 3.5 for how to
-- change it).
-- ----------------------------------------------------------------------------
EXECUTE CODE BUNDLE SAM_DEMO.AI.SAM_BUILD_BUNDLE
    ENTRYPOINT = 'python/workspace_main.py'
    ARGUMENTS  = ('--skip-automation');

-- This builds WITHOUT the weekly refresh automation, so the demo data stays
-- frozen at the build date. To also install the weekly refresh task, which
-- advances prices, documents and briefings every Monday, run afterwards:
--
--   EXECUTE CODE BUNDLE SAM_DEMO.AI.SAM_BUILD_BUNDLE
--       ENTRYPOINT = 'python/workspace_main.py'
--       ARGUMENTS  = ('--scope', 'automation');
--
-- Other useful scopes for rebuilding part of the demo later, without a full
-- rebuild:
--
--   ARGUMENTS = ('--scope', 'agents')      -- redeploy the 8 agents only (~4 min)
--   ARGUMENTS = ('--scope', 'semantic')    -- semantic views only
--   ARGUMENTS = ('--scope', 'search')      -- Cortex Search services only
--   ARGUMENTS = ('--scope', 'ai')          -- semantic + search + agents
--   ARGUMENTS = ('--scope', 'data')        -- data layers only (includes ML models)
--   ARGUMENTS = ('--scope', 'ml')          -- train, register (PRODUCTION alias) and score the
--                                          -- regime and credit PD models, plus the PD what-if procedure
--   ARGUMENTS = ('--scope', 'automation')  -- weekly refresh task only
--
-- AFTER EDITING ANY PYTHON FILE: a bundle version is an immutable snapshot, so
-- the bundle keeps running the code it was created from until you refresh it.
-- Commit and push, pull into the Workspace, then either re-run the
-- CREATE OR REPLACE above or add a version:
--
--   ALTER CODE BUNDLE SAM_DEMO.AI.SAM_BUILD_BUNDLE ADD VERSION FROM <$bundle_src>;
--
-- Check run history at any time:
--
--   SELECT ENTRYPOINT, STATUS, START_TIME, END_TIME, ERROR_MESSAGE
--   FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.CODE_BUNDLE_HISTORY(
--       BUNDLE_NAME => 'SAM_BUILD_BUNDLE', DATABASE => 'SAM_DEMO', SCHEMA => 'AI'));

-- ============================================================================
-- DONE — Next Steps
-- ============================================================================
--
-- The build above created the data, semantic views, search services and agents.
--
-- After completion:
--   - Open Snowflake CoWork to interact with the agents
--   - Open the notebooks (factor_discovery, market_regime_detection, credit_risk_model)
--     for ML workflow demonstrations. Attach the notebook service to
--     SAM_DEMO_ML_POOL, which is sized for them (memory-optimised, 6 vCPU /
--     58 GiB) rather than picking an arbitrary pool. Select
--     SNOWFLAKE.SNOWPARK.PYPI_SHARED_REPOSITORY as the Artifact Repository so
--     the notebook can install its ML packages.
--
-- Prefer to iterate interactively instead of via the bundle? Open
-- python/workspace_main.py in the Workspace, install packages once from the
-- terminal with:
--     pip install -r "$PWD/requirements-workspace.txt"
-- restart the kernel, and click "Run". With no arguments that is equivalent to a
-- full build. This avoids having to refresh a bundle version after every edit.
--
-- ============================================================================
-- Weekly refresh — ongoing operations
-- ============================================================================
-- The build installs SAM_DEMO.AI.WEEKLY_REFRESH_TASK, which runs every Monday
-- at 06:00 UTC and advances the demo a week: new prices, trades, positions,
-- recommendations and any documents whose cadence is due. Nothing needs to be
-- triggered by hand.
--
-- Operator commands (run from a checkout or a Workspace terminal):
--
--   Check health     python python/weekly_refresh_main.py --mode status
--                    Exits non-zero and explains why if the automation is
--                    unhealthy (task suspended, bundle missing, runs failing).
--
--   Deploy changes   python python/weekly_refresh_main.py --mode deploy
--                    REQUIRED after editing any Python file. A bundle version is
--                    an immutable snapshot, so until you deploy, the schedule
--                    keeps executing the previously deployed code.
--
--   Fill a gap       python python/weekly_refresh_main.py --mode catch-up --weeks N
--                    Advances one week at a time, so a demo left idle rebuilds
--                    week-by-week history rather than jumping to today.
--
--   Pause / resume   python python/weekly_refresh_main.py --mode pause
--                    python python/weekly_refresh_main.py --mode resume
--
-- Add --connection-name <conn> to any of the above when running locally.
--
-- Note: four of the six Marketplace streams have a 1-day staleness horizon, so
-- after a long pause the refresh automatically falls back to a date-windowed
-- read. That is expected, not an error.
--
-- ============================================================================

SELECT 'Setup complete - infrastructure created and demo built by the Code Bundle above.' AS status;
