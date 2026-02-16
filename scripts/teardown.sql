-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- ============================================================================
-- SAM Demo - Teardown Script
-- ============================================================================
-- This script removes all SAM demo components from your Snowflake account.
--
-- WARNING: This will permanently delete all data and AI components!
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- Step 1: Drop Cortex Agents
-- ============================================================================
-- Note: Agents are automatically unregistered from Snowflake Intelligence when dropped

DROP AGENT IF EXISTS SAM_DEMO.AI.AM_PORTFOLIO_COPILOT;
DROP AGENT IF EXISTS SAM_DEMO.AI.AM_RESEARCH_COPILOT;
DROP AGENT IF EXISTS SAM_DEMO.AI.AM_THEMATIC_MACRO_ADVISOR;
DROP AGENT IF EXISTS SAM_DEMO.AI.AM_ESG_GUARDIAN;
DROP AGENT IF EXISTS SAM_DEMO.AI.AM_COMPLIANCE_ADVISOR;
DROP AGENT IF EXISTS SAM_DEMO.AI.AM_SALES_ADVISOR;
DROP AGENT IF EXISTS SAM_DEMO.AI.AM_QUANT_ANALYST;
DROP AGENT IF EXISTS SAM_DEMO.AI.AM_MIDDLE_OFFICE_COPILOT;
DROP AGENT IF EXISTS SAM_DEMO.AI.AM_EXECUTIVE_COPILOT;

-- ============================================================================
-- Step 2: Drop Cortex Search Services (16 services)
-- ============================================================================

DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_BROKER_RESEARCH;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_COMPANY_EVENTS;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_PRESS_RELEASES;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_NGO_REPORTS;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_ENGAGEMENT_NOTES;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_POLICY_DOCS;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_SALES_TEMPLATES;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_PHILOSOPHY_DOCS;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_REPORT_TEMPLATES;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_MACRO_EVENTS;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_CUSTODIAN_REPORTS;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_RECONCILIATION_NOTES;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_SSI_DOCUMENTS;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_OPS_PROCEDURES;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_STRATEGY_DOCUMENTS;
DROP CORTEX SEARCH SERVICE IF EXISTS SAM_DEMO.AI.SAM_REAL_SEC_FILINGS;

-- ============================================================================
-- Step 3: Drop Semantic Views (10 views)
-- ============================================================================

DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_ANALYST_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_IMPLEMENTATION_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_SUPPLY_CHAIN_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_MIDDLE_OFFICE_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_COMPLIANCE_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_EXECUTIVE_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_FUNDAMENTALS_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_STOCK_PRICES_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_SEC_FINANCIALS_VIEW;
DROP SEMANTIC VIEW IF EXISTS SAM_DEMO.AI.SAM_SEC_SEGMENTS_VIEW;

-- ============================================================================
-- Step 4: Drop Git Integration
-- ============================================================================

DROP GIT REPOSITORY IF EXISTS SAM_DEMO.PUBLIC.sam_demo_repo;
DROP SECRET IF EXISTS SAM_DEMO.PUBLIC.GITHUB_SECRET;
DROP API INTEGRATION IF EXISTS GITHUB_INTEGRATION_SAM_DEMO;

-- ============================================================================
-- Step 5: Drop Database (includes all tables, views, procedures, stages)
-- ============================================================================

DROP DATABASE IF EXISTS SAM_DEMO CASCADE;

-- ============================================================================
-- Step 6: Drop Warehouses
-- ============================================================================

DROP WAREHOUSE IF EXISTS SAM_DEMO_WH;

-- ============================================================================
-- Step 7: Drop Role
-- ============================================================================

REVOKE ROLE SAM_DEMO_ROLE FROM ROLE ACCOUNTADMIN;
REVOKE ROLE SAM_DEMO_ROLE FROM ROLE SYSADMIN;
DROP ROLE IF EXISTS SAM_DEMO_ROLE;

-- ============================================================================
-- Complete
-- ============================================================================

SELECT 'Teardown complete - all SAM demo components removed' AS status;
