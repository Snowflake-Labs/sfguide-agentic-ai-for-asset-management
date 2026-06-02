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
YAML-based Semantic View Loader

Loads semantic view definitions from YAML template files and creates them
in Snowflake using SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML.

YAML files use {{VARIABLE}} template syntax for config substitution.
"""

import re
from pathlib import Path
from snowflake.snowpark import Session
from typing import List, Optional
import config
from utils.logging import log_detail, log_warning, log_error, log_info

DEFINITIONS_DIR = Path(__file__).parent / "semantic_view_definitions"

TEMPLATE_VARIABLES = {
    "DATABASE": config.DATABASE["name"],
}


def render_template(yaml_content: str, variables: dict = None) -> str:
    if variables is None:
        variables = TEMPLATE_VARIABLES
    def replacer(match):
        key = match.group(1)
        if key not in variables:
            raise ValueError(f"Unknown template variable: {{{{{key}}}}}")
        return variables[key]
    return re.sub(r"\{\{(\w+)\}\}", replacer, yaml_content)


def load_view_yaml(view_name: str, variables: dict = None) -> str:
    yaml_path = DEFINITIONS_DIR / f"{view_name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"YAML definition not found: {yaml_path}")
    raw = yaml_path.read_text(encoding="utf-8")
    return render_template(raw, variables)


def create_view_from_yaml(
    session: Session,
    yaml_content: str,
    schema: str,
    verify_only: bool = False,
) -> str:
    escaped = yaml_content.replace("'", "''")
    verify_flag = "TRUE" if verify_only else "FALSE"
    sql = f"""CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
  '{schema}',
  $${yaml_content}$$,
  {verify_flag}
)"""
    result = session.sql(sql).collect()
    if result and len(result) > 0:
        return result[0][0]
    return "No response"


def create_semantic_view(
    session: Session,
    view_name: str,
    verify_only: bool = False,
    variables: dict = None,
) -> str:
    schema = f"{config.DATABASE['name']}.AI"
    yaml_content = load_view_yaml(view_name, variables)
    return create_view_from_yaml(session, yaml_content, schema, verify_only)


def verify_all_views(session: Session, view_names: List[str] = None) -> dict:
    if view_names is None:
        view_names = [p.stem for p in sorted(DEFINITIONS_DIR.glob("*.yaml"))]

    results = {"passed": [], "failed": []}
    for name in view_names:
        try:
            msg = create_semantic_view(session, name, verify_only=True)
            results["passed"].append(name)
            log_detail(f"  VALID  {name}")
        except Exception as e:
            results["failed"].append((name, str(e)))
            log_error(f"  INVALID  {name}: {e}")
    return results


def get_all_view_names() -> List[str]:
    return sorted(p.stem for p in DEFINITIONS_DIR.glob("*.yaml"))
