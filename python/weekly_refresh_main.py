#!/usr/bin/env python3
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
"""Weekly refresh entrypoint.

The same file runs in three places unchanged:

  - inside Snowflake as a Code Bundle, driven by WEEKLY_REFRESH_TASK
  - in a Snowflake Workspace notebook service
  - locally against a named connection, for development

That works because `Session.builder.configs(...).getOrCreate()` attaches to the
ambient session when there is one and creates a connection when there is not.

    # in the bundle (an active session already exists)
    EXECUTE CODE BUNDLE SAM_DEMO.AI.SAM_WEEKLY_BUNDLE
        ENTRYPOINT = 'python/weekly_refresh_main.py'
        ARGUMENTS  = ('--mode', 'weekly');

    # locally
    python python/weekly_refresh_main.py --mode dry-run \\
        --connection-name my-connection

Modes:
    weekly    process the next week (the scheduled behaviour)
    catch-up  advance a week at a time until current, for a demo left idle
    dry-run   report what would happen, writing nothing
    status    watermark, stream health, vintage ledger and automation health
    deploy    push the current local code into the bundle (a bundle version is an
              immutable snapshot, so the schedule runs old code until you do this)
    pause     suspend the weekly schedule
    resume    restart the weekly schedule

Exit codes: 0 success, 1 status reported unhealthy, 2 refresh completed PARTIAL.
"""

import argparse
import json
import os
import sys

# Ensure python/ is importable. `__file__` is unreliable here: in a Workspace it
# is not defined at all, and under EXECUTE CODE BUNDLE the entrypoint is invoked
# from the bundle root. The working directory is the reliable anchor, which is
# the same reasoning as workspace_main.py.
_python_dir = os.path.join(os.getcwd(), 'python')
if not os.path.isdir(_python_dir):
    # Already inside python/ (e.g. invoked from that directory).
    _python_dir = os.getcwd()
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)


def build_session(connection_name=None):
    """Attach to the ambient session, or open one from a named connection.

    getOrCreate rather than create: inside a Code Bundle or a Workspace there is
    already an active session, and calling create would open a second, redundant
    one.
    """
    from snowflake.snowpark import Session

    configs = {'connection_name': connection_name} if connection_name else {}
    return Session.builder.configs(configs).getOrCreate()


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Weekly incremental refresh for the SAM AI demo.'
    )
    parser.add_argument(
        '--mode', default='weekly',
        choices=['weekly', 'catch-up', 'dry-run', 'status',
                 'deploy', 'pause', 'resume'],
        help='weekly: process the next week. catch-up: advance week by week until '
             'current. dry-run: report without writing. status: health snapshot. '
             'deploy: push current local code to the bundle. pause/resume: stop '
             'and restart the weekly schedule.'
    )
    parser.add_argument(
        '--weeks', type=int, default=12,
        help='Maximum weeks to process in catch-up mode (default: 12).'
    )
    parser.add_argument(
        '--as-of', default=None,
        help='Target date (YYYY-MM-DD). Defaults to the latest available price '
             'date, so the refresh follows the data rather than the wall clock.'
    )
    parser.add_argument(
        '--connection-name', default=None,
        help='Named connection for local runs. Omit inside Snowflake, where the '
             'active session is used.'
    )
    parser.add_argument(
        '--role', default=None,
        help='Role to run as. Defaults to the platform build role, which owns the '
             'DDL privileges the refresh needs.'
    )
    parser.add_argument(
        '--skip-pipelines', action='store_true',
        help='Skip PDF upload and parsing. Documents are generated but will not '
             'be searchable until a later run parses them.'
    )
    parser.add_argument(
        '--automation-workspace-path', default=None,
        help='For --mode deploy: build the bundle version from a Workspace live '
             'path instead of the stage.'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Detailed output.'
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)

    from utils.logging import set_verbosity
    set_verbosity(2 if args.verbose else 1)

    session = build_session(args.connection_name)
    try:
        # The refresh creates and merges into tables, so it needs the build role's
        # DDL privileges - a default of SYSADMIN fails on SAM_DEMO.RAW. Set the
        # role and warehouse explicitly rather than inheriting whatever the
        # session happens to have.
        import config

        role = args.role or config.RBAC['platform_build_role']
        try:
            session.sql(f"USE ROLE {role}").collect()
        except Exception as exc:
            # In a bundle the task already runs as its owner, which may not be
            # allowed to switch roles. Warn rather than fail: if the owning role
            # does have the privileges the refresh proceeds correctly.
            print(
                f"Warning: could not USE ROLE {role} ({exc}). Continuing with the "
                "session's current role.",
                file=sys.stderr,
            )

        try:
            session.sql(
                f"USE WAREHOUSE {config.WAREHOUSES['execution']['name']}"
            ).collect()
        except Exception as exc:
            print(f"Warning: could not set warehouse: {exc}", file=sys.stderr)

        from data import weekly_refresh

        if args.mode == 'status':
            # Both halves in one view: the data side (watermark, streams, vintage
            # ledger) and the automation side (bundle, task state, execution
            # failures). Reading them separately is how you miss that the task
            # has been suspended for a month while the data looks merely stale.
            from data import automation, incremental
            result = {
                'refresh': weekly_refresh.status(session),
                'automation': automation.status(session),
                'data_health': incremental.data_health(session),
            }
        elif args.mode == 'deploy':
            from data import automation
            result = automation.deploy(
                session, workspace_path=args.automation_workspace_path
            )
        elif args.mode == 'pause':
            from data import automation
            result = automation.pause(session)
        elif args.mode == 'resume':
            from data import automation
            result = automation.resume(session)
        elif args.mode == 'dry-run':
            result = weekly_refresh.run(session, as_of=args.as_of, dry_run=True)
        elif args.mode == 'catch-up':
            result = weekly_refresh.run_catch_up(
                session, max_weeks=args.weeks, skip_pipelines=args.skip_pipelines
            )
        else:
            result = weekly_refresh.run(
                session, as_of=args.as_of, skip_pipelines=args.skip_pipelines
            )

        # Printed as JSON so a task's run history carries a machine-readable
        # record of what happened, not just prose.
        print(json.dumps(result, indent=2, default=str))

        # A health command that always exits 0 is useless for monitoring, so
        # report an unhealthy automation as a failure. Reasons are in
        # result['automation']['health_notes'].
        if args.mode == 'status':
            unhealthy = False
            for section in ('automation', 'data_health'):
                health = (result.get(section) or {})
                if not health.get('healthy', True):
                    unhealthy = True
                    for note in health.get('health_notes', []):
                        print(f"UNHEALTHY ({section}): {note}", file=sys.stderr)
            return 1 if unhealthy else 0

        # Non-zero exit on a failed or partial outcome so the task is recorded as
        # failed rather than silently succeeding with an unsearchable corpus.
        statuses = (
            [r.get('status') for r in result]
            if isinstance(result, list) else [result.get('status')]
        )
        if any(s == 'PARTIAL' for s in statuses):
            print(
                'Refresh completed with PARTIAL status: documents were generated '
                'but at least one pipeline did not finish, so they are not yet '
                'searchable.',
                file=sys.stderr,
            )
            return 2
        return 0

    except Exception as exc:
        print(f"Weekly refresh failed: {exc}", file=sys.stderr)
        raise
    finally:
        # Only close a session we opened. Closing the ambient session inside a
        # bundle or notebook would break the surrounding environment.
        if args.connection_name:
            try:
                session.close()
            except Exception:
                pass


if __name__ == '__main__':
    # Deliberately NOT `sys.exit(main())`. Under EXECUTE CODE BUNDLE the entrypoint
    # is run as a notebook cell, and the runner treats ANY SystemExit as a failed
    # cell - including SystemExit(0). A successful run must therefore fall off the
    # end of the script rather than exit. Non-zero codes are still raised, because
    # that is what marks the task as failed.
    _exit_code = main()
    if _exit_code:
        sys.exit(_exit_code)
