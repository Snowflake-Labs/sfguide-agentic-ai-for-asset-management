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
Agent Evaluation Dataset Creator for SAM Demo

Creates and registers evaluation datasets for Cortex Agents using Snowflake's
native Agent Evaluations. Questions are grounded with actual data values
queried at build time for consistent, measurable results.
"""

from snowflake.snowpark import Session
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import config
from utils.logging import log_step, log_substep, log_detail, log_warning, log_error, log_phase_complete


def create_eval_datasets(session: Session, scenarios: List[str] = None) -> Tuple[int, int]:
    """
    Create evaluation datasets for agents that have evaluation configs.

    Queries actual data to hydrate date placeholders and dynamic ground truth,
    then creates tables and registers them with SYSTEM$CREATE_EVALUATION_DATASET.

    Args:
        session: Active Snowpark session
        scenarios: List of scenario names to create eval datasets for

    Returns:
        Tuple of (created_count, failed_count)
    """
    log_step("Creating agent evaluation datasets")

    eval_configs = config.AGENT_EVALUATIONS
    if not eval_configs:
        log_detail("  No evaluation configurations found")
        return 0, 0

    filtered_configs = {
        k: v for k, v in eval_configs.items()
        if scenarios is None or k in scenarios
    }

    if not filtered_configs:
        log_detail("  No evaluation configs match the specified scenarios")
        return 0, 0

    context = _get_build_context(session)

    created = 0
    failed = 0

    for scenario_key, eval_config in filtered_configs.items():
        try:
            log_substep(f"Creating eval dataset for {eval_config['agent_name']}")
            hydrated = _hydrate_questions(session, eval_config['questions'], context)
            success = _create_and_register_dataset(
                session, scenario_key, eval_config, hydrated, context
            )
            if success:
                created += 1
                log_detail(f"  Registered eval dataset: {len(hydrated)} questions")
            else:
                failed += 1
        except Exception as e:
            failed += 1
            log_error(f"  Failed to create eval dataset for {scenario_key}: {e}")

    log_phase_complete(f"Eval datasets: {created} created" + (f", {failed} failed" if failed else ""))
    return created, failed


def _get_build_context(session: Session) -> dict:
    """
    Query actual data for date anchors and key reference values.

    Returns dict with max_date, max_price_date, and database name.
    """
    database = config.DATABASE['name']

    max_holding_date = None
    try:
        result = session.sql(f"""
            SELECT MAX(HoldingDate) AS max_date
            FROM {database}.CURATED.FACT_POSITION_DAILY_ABOR
        """).collect()
        if result and result[0]['MAX_DATE']:
            max_holding_date = str(result[0]['MAX_DATE'])
    except Exception as e:
        log_warning(f"  Could not query max holding date: {e}")

    max_price_date = None
    try:
        result = session.sql(f"""
            SELECT MAX(PRICE_DATE) AS max_date
            FROM {database}.MARKET_DATA.FACT_STOCK_PRICES
        """).collect()
        if result and result[0]['MAX_DATE']:
            max_price_date = str(result[0]['MAX_DATE'])
    except Exception as e:
        log_warning(f"  Could not query max price date: {e}")

    max_date = max_holding_date or max_price_date or '2025-12-31'

    log_detail(f"  Build context: max_date={max_date}, max_price_date={max_price_date}")

    return {
        'database': database,
        'max_date': max_date,
        'max_price_date': max_price_date or max_date,
    }


def _hydrate_questions(session: Session, questions: list, context: dict) -> list:
    """
    Replace placeholders and run validation queries to build ground truth.

    For static questions: substitutes date placeholders in input_query and ground_truth_output.
    For dynamic questions: runs validation_query, formats results into ground_truth_template.
    """
    hydrated = []
    database = context['database']
    max_date = context['max_date']
    max_price_date = context['max_price_date']

    for q in questions:
        input_query = q['input_query'].format(
            max_date=max_date,
            max_price_date=max_price_date,
            database=database,
        )

        if q['ground_truth_type'] == 'static':
            ground_truth_output = q['ground_truth_output'].format(
                max_date=max_date,
                max_price_date=max_price_date,
                database=database,
            )
        elif q['ground_truth_type'] == 'dynamic':
            validation_sql = q['validation_query'].format(
                database=database,
                max_date=max_date,
                max_price_date=max_price_date,
            )
            try:
                rows = session.sql(validation_sql).collect()
                validation_result = _format_query_result(rows)
            except Exception as e:
                log_warning(f"  Validation query failed for: {q['input_query'][:60]}... - {e}")
                validation_result = "Data not available"

            ground_truth_output = q['ground_truth_template'].format(
                validation_result=validation_result,
                max_date=max_date,
                max_price_date=max_price_date,
                database=database,
            )
        else:
            ground_truth_output = q.get('ground_truth_output', 'No ground truth defined')

        hydrated.append({
            'input_query': input_query,
            'ground_truth_output': ground_truth_output,
            'category': q.get('category', 'core_use_case'),
            'expected_tools': q.get('expected_tools', []),
        })

    return hydrated


def _format_query_result(rows: list) -> str:
    """
    Format Snowpark Row objects into a readable summary string for ground truth.
    """
    if not rows:
        return "No data returned"

    if len(rows) == 1 and len(rows[0].as_dict()) == 1:
        val = list(rows[0].as_dict().values())[0]
        return str(val)

    parts = []
    for row in rows:
        row_dict = row.as_dict()
        fields = [f"{k}={v}" for k, v in row_dict.items()]
        parts.append(", ".join(fields))

    return "; ".join(parts)


def _build_ground_truth_invocations(scenario_key: str, expected_tools: list, database: str) -> list:
    tool_map = config.TOOL_SERVICE_MAP.get(scenario_key, {})
    invocations = []
    for tool_name in expected_tools:
        tool_info = tool_map.get(tool_name, {})
        tool_type = tool_info.get('type', 'generic')
        if tool_type == 'cortex_analyst':
            service = f"{database}.AI.{tool_info['service']}"
            invocations.append({'tool_name': 'cortex_analyst', 'service': service})
        elif tool_type == 'cortex_search':
            service = f"{database}.AI.{tool_info['service']}"
            invocations.append({'tool_name': tool_name, 'service': service})
        else:
            invocations.append({'tool_name': tool_name})
    return invocations


def _create_and_register_dataset(
    session: Session,
    scenario_key: str,
    eval_config: dict,
    hydrated_questions: list,
    context: dict,
) -> bool:
    """
    Create the eval dataset table, insert hydrated questions, and register with Snowflake.
    """
    database = context['database']
    ai_schema = config.DATABASE['schemas']['ai']
    agent_name = eval_config['agent_name']
    version = eval_config['dataset_version']
    table_name = f"{database}.{ai_schema}.EVAL_DATASET_{agent_name.upper()}"
    dataset_name = f"{agent_name}_eval_{version}"

    session.sql(f"USE DATABASE {database}").collect()
    session.sql(f"USE SCHEMA {ai_schema}").collect()

    session.sql(f"""
        CREATE OR REPLACE TABLE {table_name} (
            QUESTION_ID INT AUTOINCREMENT,
            INPUT_QUERY VARCHAR NOT NULL,
            GROUND_TRUTH VARIANT NOT NULL,
            CATEGORY VARCHAR,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
    """).collect()

    if not hydrated_questions:
        log_warning(f"  No questions to insert for {agent_name}")
        return False

    for q in hydrated_questions:
        escaped_query = q['input_query'].replace("'", "''")
        escaped_category = q['category'].replace("'", "''")

        invocations = _build_ground_truth_invocations(
            scenario_key, q['expected_tools'], database
        )
        ground_truth_obj = {
            'ground_truth_invocations': invocations,
            'ground_truth_output': q['ground_truth_output'],
        }
        escaped_json = json.dumps(ground_truth_obj).replace("'", "''")

        insert_sql = f"""
            INSERT INTO {table_name} (INPUT_QUERY, GROUND_TRUTH, CATEGORY)
            SELECT '{escaped_query}',
                   PARSE_JSON('{escaped_json}'),
                   '{escaped_category}'
        """
        session.sql(insert_sql).collect()

    try:
        session.sql(f"""
            ALTER DATASET IF EXISTS {dataset_name}
            DROP VERSION 'SYSTEM_AI_OBS_CORTEX_AGENT_DATASET_VERSION_DO_NOT_DELETE'
        """).collect()
    except Exception:
        pass

    try:
        session.sql(f"""
            CALL SYSTEM$CREATE_EVALUATION_DATASET(
                'Cortex Agent',
                '{table_name}',
                '{dataset_name}',
                OBJECT_CONSTRUCT('query_text', 'INPUT_QUERY', 'expected_tools', 'GROUND_TRUTH')
            )
        """).collect()
        log_detail(f"  Registered dataset: {dataset_name}")
    except Exception as e:
        log_warning(f"  Dataset registration failed (table still created): {e}")

    return True


def run_evaluation(
    session: Session,
    scenario_key: str,
    connection_name: str,
    metrics: List[str] = None,
    warehouse: str = None,
) -> Optional[str]:
    """
    Generate a YAML config and trigger an evaluation run for an agent.

    This is for on-demand use -- not called automatically during build
    since evaluations take several minutes to complete.

    Args:
        session: Active Snowpark session
        scenario_key: Key from AGENT_EVALUATIONS (e.g. 'portfolio_copilot')
        connection_name: Snowflake connection name for PUT upload
        metrics: List of metric names (default: ['answer_correctness', 'logical_consistency'])
        warehouse: Warehouse name (default: execution warehouse from config)

    Returns:
        Run name if started successfully, None otherwise
    """
    if scenario_key not in config.AGENT_EVALUATIONS:
        log_error(f"  No evaluation config found for {scenario_key}")
        return None

    eval_config = config.AGENT_EVALUATIONS[scenario_key]
    agent_name = eval_config['agent_name']
    version = eval_config['dataset_version']
    database = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    if metrics is None:
        metrics = ['answer_correctness', 'logical_consistency']
    if warehouse is None:
        warehouse = config.WAREHOUSES['execution']['name']

    dataset_name = f"{agent_name}_eval_{version}"
    run_name = f"{agent_name}_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    stage_name = f"{database}.{ai_schema}.EVAL_CONFIG_STAGE"

    metrics_yaml = "\n".join([f'  - "{m}"' for m in metrics])

    yaml_content = f"""dataset:
  dataset_type: "cortex agent"
  table_name: "{database}.{ai_schema}.EVAL_DATASET_{agent_name.upper()}"
  dataset_name: "{dataset_name}"
  column_mapping:
    query_text: "INPUT_QUERY"
    ground_truth: "GROUND_TRUTH"

evaluation:
  agent_params:
    agent_name: "{database}.{ai_schema}.{agent_name}"
    agent_type: "CORTEX AGENT"
  run_params:
    label: "evaluation"
    description: "SAM Demo agent evaluation for {agent_name}"
  source_metadata:
    type: "dataset"
    dataset_name: "{dataset_name}"

metrics:
{metrics_yaml}
"""

    import tempfile
    import os

    yaml_filename = f"{agent_name}_eval_config.yaml"

    try:
        session.sql(f"""
            CREATE STAGE IF NOT EXISTS {stage_name}
            FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = NONE)
        """).collect()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        session.sql(f"PUT 'file://{temp_path}' @{stage_name} AUTO_COMPRESS=FALSE OVERWRITE=TRUE").collect()
        os.unlink(temp_path)

        session.sql(f"""
            CALL SYSTEM$EXECUTE_AI_EVALUATION(
                '{run_name}',
                '@{stage_name}/{os.path.basename(temp_path)}',
                '{warehouse}'
            )
        """).collect()

        log_detail(f"  Started evaluation run: {run_name}")
        return run_name

    except Exception as e:
        log_error(f"  Failed to start evaluation: {e}")
        return None
