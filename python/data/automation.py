# Copyright (c) 2025 Snowflake Inc.
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
"""Installs the weekly refresh automation: Code Bundle + scheduled task.

This is what makes the demo self-maintaining. After the build runs this, a task
executes `python/weekly_refresh_main.py --mode weekly` every Monday and nothing
needs to be triggered by hand.

The bundle source is a **stage**, not a workspace live path. A workspace path
needs the workspace name, and that cannot be discovered at build time - inside a
Workspace the working directory is only `/workspace/<hash>/`. Staging the files
behaves identically from a Workspace and from a local checkout, so one code path
covers both. `workspace_path=` overrides it for anyone who wants the bundle
linked to a live workspace instead.

Ownership follows the project's role split: FSI_DEMO_BUILD_ROLE owns and operates
the automation, SAM_DEMO_USER_ROLE only gets to watch it (granted in
scripts/workspace_setup.sql).
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from snowflake.snowpark import Session

import config
from utils.logging import log_detail, log_step, log_substep, log_warning


def _settings() -> Dict[str, Any]:
    return config.WEEKLY_REFRESH


def _fqn(name_key: str) -> str:
    database = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    return f"{database}.{ai_schema}.{_settings()[name_key]}"


def _stage_fqn() -> str:
    return _fqn('stage_name')


def _project_root() -> str:
    """Repo root, matching how config.py anchors PROJECT_ROOT."""
    return config.PROJECT_ROOT


# ---------------------------------------------------------------------------
# Stage
# ---------------------------------------------------------------------------

def ensure_bundle_stage(session: Session) -> str:
    """Create the stage that holds the bundle source. Idempotent."""
    stage = _stage_fqn()
    session.sql(f"""
        CREATE STAGE IF NOT EXISTS {stage}
        ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
        DIRECTORY = (ENABLE = TRUE)
        COMMENT = 'Source files for the SAM weekly refresh Code Bundle'
    """).collect()
    return stage


def _iter_bundle_files(root: str) -> List[Tuple[str, str]]:
    """Yield (local_path, stage_relative_dir) for every file to upload.

    `stage_relative_dir` preserves the repo layout, which is required: config.py
    resolves `data/reference_data` and `content_library` as siblings of `python/`,
    so a flattened upload would break template and reference-data loading at
    runtime rather than at build time.
    """
    settings = _settings()
    exclude_dirs = set(settings['bundle_exclude_dirs'])
    exclude_suffixes = tuple(settings['bundle_exclude_suffixes'])

    files: List[Tuple[str, str]] = []
    for entry in settings['bundle_paths']:
        local_entry = os.path.join(root, entry)

        if os.path.isfile(local_entry):
            # Top-level files (code_bundle.yml, requirements) sit at the root.
            files.append((local_entry, ''))
            continue

        if not os.path.isdir(local_entry):
            log_warning(f"  Bundle path missing, skipped: {entry}")
            continue

        for dirpath, dirnames, filenames in os.walk(local_entry):
            # Prune in place so os.walk does not descend into caches.
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            for filename in sorted(filenames):
                if filename.endswith(exclude_suffixes) or filename.startswith('.'):
                    continue
                rel_dir = os.path.relpath(dirpath, root)
                files.append((os.path.join(dirpath, filename), rel_dir))

    return files


def upload_bundle_source(session: Session) -> Tuple[int, int]:
    """PUT the bundle source onto the stage, preserving directory layout."""
    root = _project_root()
    stage = ensure_bundle_stage(session)
    stage_ref = f"@{stage}"

    files = _iter_bundle_files(root)
    if not files:
        raise RuntimeError(
            f"No bundle source files found under {root}. Check "
            "config.WEEKLY_REFRESH['bundle_paths']."
        )

    uploaded = 0
    failed = 0
    session.sql(f"REMOVE {stage_ref}").collect()
    for local_path, rel_dir in files:
        target = stage_ref if rel_dir in ('', '.') else f"{stage_ref}/{rel_dir}"
        try:
            session.file.put(
                local_path, target, overwrite=True, auto_compress=False
            )
            uploaded += 1
        except Exception as exc:
            log_warning(f"  Failed to upload {os.path.basename(local_path)}: {exc}")
            failed += 1

    log_detail(f"  Uploaded {uploaded} bundle source files ({failed} failed)")
    return uploaded, failed


# ---------------------------------------------------------------------------
# Bundle and task
# ---------------------------------------------------------------------------

def create_bundle(
    session: Session,
    workspace_path: Optional[str] = None,
    replace: bool = True,
) -> str:
    """Create (or add a version to) the Code Bundle.

    A bundle version is an immutable snapshot, so `CREATE OR REPLACE` is the
    default: on a rebuild the point is to pick up the current code. Using
    IF NOT EXISTS would silently keep serving whatever was staged the first time,
    which is the single most confusing failure mode of Code Bundles.
    """
    bundle = _fqn('bundle_name')
    source = workspace_path or f"@{_stage_fqn()}"
    ddl = (
        f"CREATE OR REPLACE CODE BUNDLE {bundle}" if replace
        else f"CREATE CODE BUNDLE IF NOT EXISTS {bundle}"
    )
    session.sql(
        f"{ddl} FROM '{source}' "
        f"COMMENT = 'SAM demo weekly incremental refresh'"
    ).collect()
    log_detail(f"  Code Bundle {bundle} <- {source}")
    return bundle


def add_bundle_version(session: Session, workspace_path: Optional[str] = None) -> str:
    """Add a new immutable version from the current source.

    Use after editing code when the bundle should keep its history rather than be
    replaced.
    """
    bundle = _fqn('bundle_name')
    source = workspace_path or f"@{_stage_fqn()}"
    session.sql(f"ALTER CODE BUNDLE {bundle} ADD VERSION FROM '{source}'").collect()
    log_detail(f"  Added version to {bundle} from {source}")
    return bundle


def create_task(session: Session, resume: bool = True) -> str:
    """Create the weekly task that executes the bundle.

    The task is owned by whichever role runs the build (FSI_DEMO_BUILD_ROLE), and
    that role needs EXECUTE TASK plus USAGE on the compute pool and USAGE +
    **MONITOR** on the query warehouse - see scripts/workspace_setup.sql.
    """
    settings = _settings()
    task = _fqn('task_name')
    bundle = _fqn('bundle_name')
    warehouse = config.WAREHOUSES['execution']['name']
    arguments = ", ".join(f"'{arg}'" for arg in settings['arguments'])

    # Opt-in failure notification. Without it, a failed Monday run is only
    # visible from `--mode status`, which someone has to remember to run. Must be
    # a QUEUE-type notification integration - an EMAIL one is rejected for tasks.
    error_integration = settings.get('error_integration')
    error_clause = (
        f"\n            ERROR_INTEGRATION = {error_integration}"
        if error_integration else ""
    )

    session.sql(f"""
        CREATE OR REPLACE TASK {task}
            WAREHOUSE = {warehouse}
            SCHEDULE = '{settings['schedule']}'{error_clause}
            COMMENT = 'Weekly incremental refresh of the SAM demo data and documents'
        AS
            EXECUTE CODE BUNDLE {bundle}
                ENTRYPOINT = '{settings['entrypoint']}'
                ARGUMENTS = ({arguments})
    """).collect()
    log_detail(f"  Task {task} scheduled: {settings['schedule']}")
    if not error_integration:
        log_detail(
            "  No ERROR_INTEGRATION set: check health with --mode status, or set "
            "config.WEEKLY_REFRESH['error_integration'] to be emailed on failure"
        )

    if resume:
        # CREATE OR REPLACE leaves a task suspended; without this the automation
        # is installed but never fires, which is exactly the silent failure the
        # user asked to avoid ("so I do not have to trigger anything").
        session.sql(f"ALTER TASK {task} RESUME").collect()
        log_detail(f"  Task {task} resumed")

    return task


def deploy(session: Session, workspace_path: Optional[str] = None) -> Dict[str, Any]:
    """Push the current local code to the running automation.

    This is the operation to run after editing any Python file. A bundle version
    is an immutable snapshot, so **the schedule keeps executing the last deployed
    version until this is called** - editing files and doing nothing else is a
    silent no-op, and the most likely way for someone to conclude the refresh is
    broken when it is simply running old code.

    Adds a version rather than replacing, so the deployment history is kept.
    """
    log_substep("Deploying current code to the weekly refresh bundle")

    result: Dict[str, Any] = {'uploaded': 0, 'upload_failed': 0}
    if workspace_path:
        result['source'] = workspace_path
    else:
        uploaded, failed = upload_bundle_source(session)
        result['uploaded'] = uploaded
        result['upload_failed'] = failed
        if failed:
            raise RuntimeError(
                f"{failed} file(s) failed to upload; not deploying a partial "
                "bundle version."
            )
        result['source'] = f"@{_stage_fqn()}"

    result['bundle'] = add_bundle_version(session, workspace_path=workspace_path)
    result['deployed'] = True
    return result


def _set_task_state(session: Session, action: str) -> Dict[str, Any]:
    task = _fqn('task_name')
    session.sql(f"ALTER TASK {task} {action}").collect()
    rows = session.sql(
        f"SHOW TASKS LIKE '{_settings()['task_name']}' "
        f"IN SCHEMA {config.DATABASE['name']}.{config.DATABASE['schemas']['ai']}"
    ).collect()
    state = rows[0].as_dict().get('state') if rows else 'NOT_FOUND'
    log_detail(f"  Task {task} is now {state}")
    return {'task': task, 'state': state}


def pause(session: Session) -> Dict[str, Any]:
    """Suspend the weekly schedule. Data stops advancing until resumed."""
    log_substep("Pausing the weekly refresh task")
    result = _set_task_state(session, 'SUSPEND')
    log_warning(
        "  The demo data will not advance while the task is suspended. Streams on "
        "shared Marketplace views also expire - four of the six have a 1-day "
        "horizon - so a long pause forces the date-windowed fallback on resume."
    )
    return result


def resume(session: Session) -> Dict[str, Any]:
    """Resume the weekly schedule."""
    log_substep("Resuming the weekly refresh task")
    return _set_task_state(session, 'RESUME')


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def setup_weekly_refresh(
    session: Session,
    workspace_path: Optional[str] = None,
    resume: bool = True,
    skip_upload: bool = False,
) -> Dict[str, Any]:
    """Install the whole automation. Idempotent - safe to re-run every build."""
    log_substep("Installing weekly refresh automation")

    result: Dict[str, Any] = {
        'uploaded': 0,
        'upload_failed': 0,
        'source': workspace_path or f"@{_stage_fqn()}",
    }

    if workspace_path:
        log_detail(f"  Using workspace source, skipping stage upload")
    elif skip_upload:
        log_detail("  Skipping source upload (skip_upload=True)")
    else:
        uploaded, failed = upload_bundle_source(session)
        result['uploaded'] = uploaded
        result['upload_failed'] = failed
        if failed:
            # A partial upload produces a bundle that imports cleanly and then
            # fails at runtime on a missing template. Refuse to publish it.
            raise RuntimeError(
                f"{failed} bundle source file(s) failed to upload; not creating "
                "the bundle from an incomplete source."
            )

    result['bundle'] = create_bundle(session, workspace_path=workspace_path)
    result['task'] = create_task(session, resume=resume)
    result['schedule'] = _settings()['schedule']
    result['resumed'] = resume

    log_detail(
        f"  Weekly refresh installed. Next run per schedule: {result['schedule']}"
    )
    return result


def status(session: Session) -> Dict[str, Any]:
    """Report whether the automation is installed, scheduled and running."""
    settings = _settings()
    database = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    out: Dict[str, Any] = {}

    try:
        bundles = session.sql(
            f"SHOW CODE BUNDLES LIKE '{settings['bundle_name']}' "
            f"IN SCHEMA {database}.{ai_schema}"
        ).collect()
        out['bundle_exists'] = len(bundles) > 0
    except Exception as exc:
        out['bundle_exists'] = None
        out['bundle_error'] = str(exc)

    try:
        tasks = session.sql(
            f"SHOW TASKS LIKE '{settings['task_name']}' "
            f"IN SCHEMA {database}.{ai_schema}"
        ).collect()
        if tasks:
            row = tasks[0].as_dict()
            out['task_state'] = row.get('state')
            out['task_schedule'] = row.get('schedule')
        else:
            out['task_state'] = 'NOT_FOUND'
    except Exception as exc:
        out['task_state'] = None
        out['task_error'] = str(exc)

    try:
        runs = session.sql(f"""
            SELECT SCHEDULED_TIME, STATE, ERROR_MESSAGE
            FROM TABLE({database}.INFORMATION_SCHEMA.TASK_HISTORY(
                TASK_NAME => '{settings['task_name']}',
                RESULT_LIMIT => 5))
            ORDER BY SCHEDULED_TIME DESC
        """).collect()
        out['recent_runs'] = [r.as_dict() for r in runs]
    except Exception as exc:
        out['recent_runs'] = []
        out['task_history_error'] = str(exc)

    # Bundle-level history. A task can be reported SUCCEEDED while the bundle
    # execution inside it failed, so this is the layer that actually shows
    # whether the Python ran - the plan calls for surfacing CODE_BUNDLE_HISTORY
    # failures for exactly that reason.
    try:
        execs = session.sql(f"""
            SELECT ENTRYPOINT, STATUS, START_TIME, END_TIME, ERROR_MESSAGE
            FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.CODE_BUNDLE_HISTORY(
                BUNDLE_NAME => '{settings['bundle_name']}',
                DATABASE => '{database}',
                SCHEMA => '{ai_schema}',
                RESULT_LIMIT => 10))
            ORDER BY START_TIME DESC
        """).collect()
        rows = [r.as_dict() for r in execs]
        out['recent_executions'] = rows
        failures = [r for r in rows if str(r.get('STATUS')).upper() == 'FAILED']
        out['failed_executions'] = len(failures)
        # Health keys off the LATEST execution, not any failure in the window. A
        # failure followed by a successful run is recovered, and counting any
        # failure would keep reporting unhealthy for ten more runs - a health
        # check that cries wolf gets ignored, which defeats the point.
        out['last_execution_status'] = (
            str(rows[0].get('STATUS')).upper() if rows else None
        )
        if failures:
            out['last_failure'] = failures[0].get('ERROR_MESSAGE')
    except Exception as exc:
        out['recent_executions'] = []
        out['code_bundle_history_error'] = str(exc)

    # A single verdict, so a reader does not have to correlate the sections.
    out['healthy'] = bool(
        out.get('bundle_exists')
        and out.get('task_state') == 'started'
        and out.get('last_execution_status') != 'FAILED'
    )
    if not out['healthy']:
        out['health_notes'] = _health_notes(out)

    return out


def _health_notes(out: Dict[str, Any]) -> List[str]:
    """Explain why the automation is not healthy, in operator terms."""
    notes = []
    if not out.get('bundle_exists'):
        notes.append(
            "Code Bundle missing - run the build with --scope automation."
        )
    state = out.get('task_state')
    if state == 'NOT_FOUND':
        notes.append("Task missing - run the build with --scope automation.")
    elif state == 'suspended':
        notes.append(
            "Task is suspended, so data is not advancing. Resume with "
            "--mode resume."
        )
    elif state and state != 'started':
        notes.append(f"Task is in an unexpected state: {state}.")
    if out.get('last_execution_status') == 'FAILED':
        notes.append(
            "The most recent bundle execution FAILED. Deploy current code with "
            "--mode deploy if this followed a code change, and see "
            "status()['last_failure'] for the reason."
        )
    elif out.get('failed_executions'):
        notes.append(
            f"{out['failed_executions']} earlier execution(s) failed but the "
            "latest succeeded - recovered, no action needed."
        )
    return notes
