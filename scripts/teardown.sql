-- ============================================================================
-- Agentic AI for Asset Management - Teardown
-- ============================================================================
-- Removes every object scripts/setup.sql and the build created. Run the whole
-- script as ACCOUNTADMIN. Every statement is IF EXISTS, so it is safe to re-run
-- and to run after a partial setup.
--
-- Kept deliberately:
--   - The Git workspace you created in Step 1. Delete it from Projects > Workspaces.
--
-- FSI_DEMO_BUILD_ROLE and the FSI_DEMO_CONFIG database are shared with the other
-- FSI demos. If another FSI demo uses this account, remove the statements that
-- drop them before running this script.
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ----------------------------------------------------------------------------
-- 1. Stop the weekly refresh so it cannot start while objects are dropped
-- ----------------------------------------------------------------------------
ALTER TASK IF EXISTS SAM_DEMO.AI.WEEKLY_REFRESH_TASK SUSPEND;

-- ----------------------------------------------------------------------------
-- 2. Databases
-- ----------------------------------------------------------------------------
-- SAM_DEMO holds all data, semantic views, search services, agents, tools, ML
-- models, stages, tasks and both Code Bundles.
DROP DATABASE IF EXISTS SAM_DEMO;
DROP DATABASE IF EXISTS FSI_DEMO_CONFIG;

-- Mounted from the Snowflake Public Data (Free) listing by setup.sql.
-- Drop only if you are sure no one else is using it
-- DROP DATABASE IF EXISTS SNOWFLAKE_PUBLIC_DATA_FREE;

-- ----------------------------------------------------------------------------
-- 3. Compute pools
-- ----------------------------------------------------------------------------
-- STOP ALL ends any notebook service or bundle run still using a pool, which
-- DROP COMPUTE POOL otherwise refuses.
ALTER COMPUTE POOL IF EXISTS SAM_DEMO_BUNDLE_POOL STOP ALL;
DROP COMPUTE POOL IF EXISTS SAM_DEMO_BUNDLE_POOL;
ALTER COMPUTE POOL IF EXISTS SAM_DEMO_ML_POOL STOP ALL;
DROP COMPUTE POOL IF EXISTS SAM_DEMO_ML_POOL;

-- ----------------------------------------------------------------------------
-- 4. Warehouses
-- ----------------------------------------------------------------------------
DROP WAREHOUSE IF EXISTS SAM_DEMO_EXECUTION_WH;
DROP WAREHOUSE IF EXISTS SAM_DEMO_CORTEX_WH;

-- ----------------------------------------------------------------------------
-- 5. Roles
-- ----------------------------------------------------------------------------
DROP ROLE IF EXISTS SAM_DEMO_USER_ROLE;
DROP ROLE IF EXISTS FSI_DEMO_BUILD_ROLE;
