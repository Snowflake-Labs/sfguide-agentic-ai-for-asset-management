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
Main export package builder.

Orchestrates validation, CSV export, SQL generation, and packaging
for scenario exports.
"""

import shutil
from pathlib import Path
import config
from utils.logging import log_info, log_error, log_phase_complete, log_detail
from export.manifest import get_requirements, get_all_scenarios
from export.validate import validate_scenario_data
from export.to_csv import export_tables, get_all_table_schemas
from export import sql_scripts


def export_scenario(session, scenario_name, output_base='./exports'):
    """
    Export a scenario to a deployable package.
    
    Validates data exists, exports CSVs, generates SQL scripts,
    creates README, and packages into ZIP.
    
    Args:
        session: Active Snowpark session (connected to existing SAM_DEMO)
        scenario_name: Name of scenario from config.AVAILABLE_SCENARIOS
        output_base: Base directory for exports
        
    Returns:
        Path to the created ZIP file
        
    Raises:
        RuntimeError: If validation fails (missing data)
    """
    log_info(f"Exporting scenario: {scenario_name}")
    
    requirements = get_requirements(scenario_name)
    
    log_info("Validating data exists...")
    is_valid, errors = validate_scenario_data(session, scenario_name, requirements)
    
    if not is_valid:
        log_error("Export failed - missing data:")
        for err in errors:
            log_error(f"  {err}")
        raise RuntimeError(f"Cannot export {scenario_name}: missing required data. Run full build first.")
    
    log_info("Validation passed")
    
    output_dir = Path(output_base) / scenario_name
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    log_info("Exporting data to CSV...")
    exported = export_tables(session, requirements, output_dir)
    
    log_info("Getting table schemas...")
    table_schemas = get_all_table_schemas(session, requirements)
    
    log_info("Generating SQL scripts...")
    sql_scripts.generate_all_scripts(session, scenario_name, requirements, table_schemas, output_dir)
    
    log_info("Generating README...")
    generate_readme(scenario_name, requirements, exported, output_dir)
    
    log_info("Creating ZIP archive...")
    zip_path = shutil.make_archive(str(output_dir), 'zip', output_dir)
    
    log_phase_complete(f"Package created: {zip_path}")
    return zip_path


def generate_readme(scenario_name, requirements, exported, output_dir):
    """
    Generate README.md with setup instructions.
    
    Args:
        scenario_name: Name of scenario
        requirements: Dict from manifest.get_requirements()
        exported: Dict of table_name -> row_count
        output_dir: Path to output directory
    """
    agent_info = config.SCENARIO_AGENTS.get(scenario_name, {})
    display_name = agent_info.get('display_name', scenario_name)
    description = agent_info.get('description', 'Demo scenario package')
    agent_name = agent_info.get('agent_name', f'AM_{scenario_name}')
    
    readme = f"""# SAM AI Demo - {display_name}

## Overview
{description}

## Contents
- `01_create_objects.sql` - Creates database, schemas, stages, and tables
- `02_load_data.sql` - Loads CSV data into tables
- `03_semantic_views.sql` - Creates semantic views for Cortex Analyst
- `04_search_services.sql` - Creates Cortex Search services
- `05_custom_tools.sql` - Creates custom tool procedures
- `06_create_agents.sql` - Creates the Cortex Agent
- `data/` - CSV files with demo data
- `semantic_views/` - YAML files for semantic views (reference)

## Prerequisites
- Snowflake account with ACCOUNTADMIN role (or equivalent privileges)
- Snowflake CLI installed (`pip install snowflake-cli`)
- Warehouse: MEDIUM or larger recommended
- Cortex AI features enabled on your account

## Installation

### Quick Start (Snowflake CLI)
```bash
# Navigate to the package directory
cd {scenario_name}

# Run scripts in order (using your connection)
# NOTE: --enable-templating NONE prevents SQL template parsing errors
snow sql -f 01_create_objects.sql -c <your-connection> --enable-templating NONE
snow sql -f 02_load_data.sql -c <your-connection> --enable-templating NONE
snow sql -f 03_semantic_views.sql -c <your-connection> --enable-templating NONE
snow sql -f 04_search_services.sql -c <your-connection> --enable-templating NONE
snow sql -f 05_custom_tools.sql -c <your-connection> --enable-templating NONE
snow sql -f 06_create_agents.sql -c <your-connection> --enable-templating NONE
```

### Alternative: Snowsight
1. Upload the `data/` folder contents to a Snowflake stage
2. Open each SQL script in a Snowsight worksheet
3. Modify the PUT file paths to match your stage location
4. Execute scripts in order (01 through 06)

## Configuration

Before running, you may need to find/replace 'SAM_DEMO' with your target database name in each script.
Also update the warehouse name if needed (default: 'COMPUTE_WH').

## Data Summary

| Table | Rows |
|-------|------|
"""
    
    for table_name in sorted(exported.keys()):
        row_count = exported[table_name]
        readme += f"| {table_name} | {row_count:,} |\n"
    
    readme += f"""
## Semantic Views
"""
    for view_name in requirements.get('semantic_views', []):
        readme += f"- `{view_name}`\n"
    
    readme += f"""
## Search Services
"""
    for service_name in requirements.get('search_services', []):
        readme += f"- `{service_name}`\n"
    
    readme += f"""
## Test the Agent

After installation, test the agent:

```sql
-- In Snowsight or SnowSQL
SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
    'SAM_DEMO.AI.{agent_name}',
    'What are the top holdings in our portfolios?'
);
```

Or use through Snowflake Intelligence if registered.

## Troubleshooting

### Script fails with "object does not exist"
Ensure you run scripts in order (01 through 06). Each script depends on objects created by previous scripts.

### PUT command fails
The PUT command requires local file access. Ensure you're running from the package directory or update the file paths.

### Semantic view creation fails
Semantic views require specific underlying tables. Verify all tables were created successfully in script 01 and loaded in script 02.

### Search service creation fails
Cortex Search services require a warehouse. Ensure your warehouse is running and has sufficient size (MEDIUM recommended).

---
*Generated by SAM AI Demo Export*
"""
    
    readme_path = Path(output_dir) / "README.md"
    readme_path.write_text(readme)
    return readme_path


def list_exportable_scenarios():
    """List all scenarios that can be exported."""
    return get_all_scenarios()
