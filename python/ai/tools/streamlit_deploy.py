# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Created by Mats Stellwall, Snowflake, and Snowflake CoCo

"""
Streamlit Deployment Module for SAM Demo

Handles deployment of the Portfolio Modelling Streamlit application:
- Validates prerequisites (compute pool, tools, data objects)
- Creates Container Runtime resources (compute pool, network rule, EAI)
- Uploads application files to stage
- Creates the Streamlit app with Container Runtime
"""

import os
from snowflake.snowpark import Session
import config
from utils.logging import log_info, log_detail, log_warning, log_error


def validate_streamlit_prerequisites(session) -> tuple:
    """
    Validate that required components exist for Streamlit deployment.
    
    Returns:
        tuple: (all_valid: bool, list_of_missing_components: list)
    """
    missing = []
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    curated_schema = config.DATABASE['schemas']['curated']
    
    compute_pool = config.STREAMLIT.get('compute_pool')
    if compute_pool:
        try:
            result = session.sql(f"SHOW COMPUTE POOLS LIKE '{compute_pool}'").collect()
            if not result:
                missing.append(f"Compute pool '{compute_pool}'")
        except Exception:
            missing.append(f"Compute pool '{compute_pool}' (cannot verify)")
    
    tool_signatures = {
        'RUN_BACKTEST_TOOL': '(VARCHAR, VARCHAR, VARCHAR, VARCHAR)',
        'RUN_MONTE_CARLO_TOOL': '(VARCHAR, FLOAT, FLOAT, FLOAT, FLOAT, FLOAT, FLOAT)',
        'RUN_ATTRIBUTION_TOOL': '(VARCHAR, VARCHAR, VARCHAR, VARCHAR)',
    }
    for tool, sig in tool_signatures.items():
        try:
            session.sql(f"DESCRIBE PROCEDURE {database_name}.{ai_schema}.{tool}{sig}").collect()
        except Exception:
            missing.append(f"Procedure {tool}")
    
    for obj in ['V_SECURITY_RETURNS', 'DIM_SECURITY']:
        try:
            session.sql(f"SELECT 1 FROM {database_name}.{curated_schema}.{obj} LIMIT 1").collect()
        except Exception:
            missing.append(f"View/Table {obj}")
    
    return (len(missing) == 0, missing)


def create_container_runtime_resources(session, compute_pool: str):
    """
    Create Container Runtime resources (compute pool, network rule, external access integration).
    
    Required permissions:
    - CREATE COMPUTE POOL ON ACCOUNT
    - CREATE NETWORK RULE ON SCHEMA
    - CREATE EXTERNAL ACCESS INTEGRATION ON ACCOUNT
    
    Args:
        session: Active Snowpark session
        compute_pool: Compute pool name to create
    """
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    streamlit_config = config.STREAMLIT
    instance_family = streamlit_config.get('compute_pool_instance_family', 'CPU_X64_S')
    min_nodes = streamlit_config.get('compute_pool_min_nodes', 1)
    max_nodes = streamlit_config.get('compute_pool_max_nodes', 1)
    eai_name = streamlit_config.get('external_access_integration')
    
    log_detail("  Creating Container Runtime resources...")
    
    if compute_pool:
        try:
            session.sql(f"""
                CREATE COMPUTE POOL IF NOT EXISTS {compute_pool}
                MIN_NODES = {min_nodes}
                MAX_NODES = {max_nodes}
                INSTANCE_FAMILY = {instance_family}
                AUTO_RESUME = TRUE
                AUTO_SUSPEND_SECS = 300
                COMMENT = 'Compute pool for SAM Demo Streamlit apps (Container Runtime)'
            """).collect()
            log_detail(f"  Created compute pool: {compute_pool}")
        except Exception as e:
            log_warning(f"  Could not create compute pool: {e}")
            log_info("  You may need CREATE COMPUTE POOL ON ACCOUNT privilege")
    
    network_rule_name = f"{database_name}.{ai_schema}.PYPI_NETWORK_RULE"
    if eai_name:
        try:
            session.sql(f"""
                CREATE OR REPLACE NETWORK RULE {network_rule_name}
                MODE = EGRESS
                TYPE = HOST_PORT
                VALUE_LIST = ('pypi.org:443', 'files.pythonhosted.org:443')
                COMMENT = 'Network rule for PyPI package access'
            """).collect()
            log_detail(f"  Created network rule: {network_rule_name}")
        except Exception as e:
            log_warning(f"  Could not create network rule: {e}")
        
        try:
            session.sql(f"""
                CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION {eai_name}
                ALLOWED_NETWORK_RULES = ({network_rule_name})
                ENABLED = TRUE
                COMMENT = 'External access integration for PyPI packages in Streamlit apps'
            """).collect()
            log_detail(f"  Created external access integration: {eai_name}")
        except Exception as e:
            log_warning(f"  Could not create external access integration: {e}")
            log_info("  You may need CREATE INTEGRATION ON ACCOUNT privilege")


def deploy_streamlit_app(session, compute_pool: str = None, auto_create: bool = None, skip_validation: bool = False):
    """
    Deploy the Portfolio Modelling Streamlit application using Container Runtime.
    
    Args:
        session: Active Snowpark session
        compute_pool: Compute pool name (defaults to config.STREAMLIT['compute_pool'])
        auto_create: Auto-create compute pool and EAI if missing (defaults to config.STREAMLIT['auto_create_resources'])
        skip_validation: Skip prerequisite validation (used when called from build_all after tools created)
    
    This function:
    1. Validates prerequisites exist (unless skip_validation=True)
    2. Creates Container Runtime resources (compute pool, external access integration) if auto_create=True
    3. Creates a stage for Streamlit files
    4. Uploads application files to the stage
    5. Creates the Streamlit app with Container Runtime enabled
    """
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    
    if compute_pool is None:
        compute_pool = config.STREAMLIT.get('compute_pool')
    if auto_create is None:
        auto_create = config.STREAMLIT.get('auto_create_resources', False)
    
    if not skip_validation:
        valid, missing = validate_streamlit_prerequisites(session)
        if not valid:
            log_warning("Cannot deploy Streamlit app - missing prerequisites:")
            for item in missing:
                log_warning(f"  - {item}")
            log_warning("Run full setup first or create missing components manually.")
            return False
    
    log_info("Deploying Portfolio Modelling Streamlit application...")
    
    if auto_create:
        create_container_runtime_resources(session, compute_pool)
    
    try:
        session.sql(f"""
            CREATE STAGE IF NOT EXISTS {database_name}.{ai_schema}.STREAMLIT_PORTFOLIO_MODELLING
            DIRECTORY = (ENABLE = TRUE)
            ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
        """).collect()
        log_detail("  Created stage: STREAMLIT_PORTFOLIO_MODELLING")
    except Exception as e:
        log_error(f"  Failed to create Streamlit stage: {e}")
        return False
    
    this_file = os.path.abspath(__file__)
    tools_dir = os.path.dirname(this_file)
    ai_dir = os.path.dirname(tools_dir)
    python_dir = os.path.dirname(ai_dir)
    project_root = os.path.dirname(python_dir)
    streamlit_dir = os.path.join(project_root, 'streamlit_app')
    stage_path = f"@{database_name}.{ai_schema}.STREAMLIT_PORTFOLIO_MODELLING"
    
    try:
        for filename in ['streamlit_app.py', 'pyproject.toml']:
            file_path = os.path.join(streamlit_dir, filename)
            if os.path.exists(file_path):
                session.file.put(file_path, stage_path, overwrite=True, auto_compress=False)
                log_detail(f"  Uploaded: {filename}")
            else:
                log_warning(f"  File not found: {file_path}")
        
        pages_dir = os.path.join(streamlit_dir, 'pages')
        if os.path.exists(pages_dir):
            pages_stage = f"{stage_path}/pages"
            for filename in os.listdir(pages_dir):
                if filename.endswith('.py'):
                    file_path = os.path.join(pages_dir, filename)
                    session.file.put(file_path, pages_stage, overwrite=True, auto_compress=False)
                    log_detail(f"  Uploaded: pages/{filename}")
        
        components_dir = os.path.join(streamlit_dir, 'components')
        if os.path.exists(components_dir):
            components_stage = f"{stage_path}/components"
            for filename in os.listdir(components_dir):
                if filename.endswith('.py'):
                    file_path = os.path.join(components_dir, filename)
                    session.file.put(file_path, components_stage, overwrite=True, auto_compress=False)
                    log_detail(f"  Uploaded: components/{filename}")
        
        streamlit_config_dir = os.path.join(streamlit_dir, '.streamlit')
        if os.path.exists(streamlit_config_dir):
            config_stage = f"{stage_path}/.streamlit"
            for filename in os.listdir(streamlit_config_dir):
                if filename.endswith('.toml'):
                    file_path = os.path.join(streamlit_config_dir, filename)
                    session.file.put(file_path, config_stage, overwrite=True, auto_compress=False)
                    log_detail(f"  Uploaded: .streamlit/{filename}")
        
        log_detail("  All Streamlit files uploaded to stage")
        
    except Exception as e:
        log_error(f"  Failed to upload Streamlit files: {e}")
        return False
    
    external_access = config.STREAMLIT.get('external_access_integration')
    
    create_sql = f"""
        CREATE OR REPLACE STREAMLIT {database_name}.{ai_schema}.PORTFOLIO_MODELLING_APP
            FROM '@{database_name}.{ai_schema}.STREAMLIT_PORTFOLIO_MODELLING'
            MAIN_FILE = 'streamlit_app.py'
            RUNTIME_NAME = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'
            QUERY_WAREHOUSE = '{config.WAREHOUSES['execution']['name']}'
            TITLE = 'Portfolio Modelling'
            COMMENT = 'Interactive portfolio analysis with Container Runtime. Part of SAM Demo.'"""
    
    if compute_pool:
        create_sql += f"\n            COMPUTE_POOL = '{compute_pool}'"
    
    if external_access:
        create_sql += f"\n            EXTERNAL_ACCESS_INTEGRATIONS = ('{external_access}')"
    
    try:
        session.sql(create_sql).collect()
        log_detail("  Created Streamlit app: PORTFOLIO_MODELLING_APP")
        if compute_pool:
            log_detail(f"  Set compute pool: {compute_pool}")
        if external_access:
            log_detail(f"  Set external access integration: {external_access}")
        
        try:
            app_info = session.sql(f"""
                SHOW STREAMLITS LIKE 'PORTFOLIO_MODELLING_APP' IN SCHEMA {database_name}.{ai_schema}
            """).collect()
            if app_info:
                log_info(f"  Streamlit app deployed successfully")
        except Exception:
            pass
        
        return True
        
    except Exception as e:
        log_error(f"  Failed to create Streamlit app: {e}")
        log_warning("  Note: Streamlit in Snowflake with Container Runtime requires appropriate account permissions")
        return False
