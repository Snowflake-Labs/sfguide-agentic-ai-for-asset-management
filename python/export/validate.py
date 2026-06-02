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
Validate scenario data exists before export.

Checks that all required tables, semantic views, and search services
exist and have data in the current SAM_DEMO installation.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_error, log_info


def validate_scenario_data(session, scenario_name, requirements):
    """
    Validate all required tables, views, and services exist and have data.
    
    Args:
        session: Active Snowpark session
        scenario_name: Name of scenario being validated
        requirements: Dict from manifest.get_requirements()
        
    Returns:
        tuple: (is_valid, errors) where is_valid is bool and errors is list of strings
    """
    errors = []
    database_name = config.DATABASE['name']
    
    log_info(f"Validating data for scenario: {scenario_name}")
    
    errors.extend(_validate_tables(session, database_name, requirements['tables']))
    errors.extend(_validate_corpus_tables(session, database_name, requirements.get('corpus_tables', [])))
    errors.extend(_validate_semantic_views(session, database_name, requirements.get('semantic_views', [])))
    errors.extend(_validate_search_services(session, database_name, requirements.get('search_services', [])))
    
    return len(errors) == 0, errors


def _validate_tables(session, database_name, tables_by_schema):
    """Validate tables exist and have data."""
    errors = []
    
    for schema, tables in tables_by_schema.items():
        for table_name in tables:
            full_name = f"{database_name}.{schema}.{table_name}"
            try:
                result = session.sql(f"SELECT COUNT(*) as CNT FROM {full_name}").collect()
                row_count = result[0]['CNT']
                if row_count == 0:
                    errors.append(f"Table {full_name} exists but is empty")
                else:
                    log_detail(f"  {table_name}: {row_count:,} rows")
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                    errors.append(f"Table {full_name} does not exist")
                else:
                    errors.append(f"Table {full_name} error: {error_msg[:100]}")
    
    return errors


def _validate_corpus_tables(session, database_name, corpus_tables):
    """Validate corpus tables for search services exist (empty is OK - warning only)."""
    errors = []
    
    for table_name in corpus_tables:
        full_name = f"{database_name}.CURATED.{table_name}"
        try:
            result = session.sql(f"SELECT COUNT(*) as CNT FROM {full_name}").collect()
            row_count = result[0]['CNT']
            if row_count == 0:
                from utils.logging import log_warning
                log_warning(f"  {table_name}: empty (search service may have limited results)")
            else:
                log_detail(f"  {table_name}: {row_count:,} documents")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                errors.append(f"Corpus {full_name} does not exist")
            else:
                errors.append(f"Corpus {full_name} error: {error_msg[:100]}")
    
    return errors


def _validate_semantic_views(session, database_name, semantic_views):
    """Validate semantic views exist."""
    errors = []
    
    for view_name in semantic_views:
        full_name = f"{database_name}.AI.{view_name}"
        try:
            session.sql(f"DESCRIBE SEMANTIC VIEW {full_name}").collect()
            log_detail(f"  Semantic view {view_name}: OK")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                errors.append(f"Semantic view {full_name} does not exist")
            else:
                errors.append(f"Semantic view {full_name} error: {error_msg[:100]}")
    
    return errors


def _validate_search_services(session, database_name, search_services):
    """Validate Cortex Search services exist."""
    errors = []
    
    for service_name in search_services:
        full_name = f"{database_name}.AI.{service_name}"
        try:
            session.sql(f"DESCRIBE CORTEX SEARCH SERVICE {full_name}").collect()
            log_detail(f"  Search service {service_name}: OK")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                errors.append(f"Search service {full_name} does not exist")
            else:
                errors.append(f"Search service {full_name} error: {error_msg[:100]}")
    
    return errors
