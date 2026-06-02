"""
Semantic Views Builder for SAM Demo

Creates Cortex Analyst semantic views from YAML template files stored in
semantic_view_definitions/. Uses SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML for
creation and template variable substitution for config values.

Views are resolved from config.SCENARIOS — each scenario declares its required_views.
Build order guarantee: all required tables are created before this runs.
"""

from snowflake.snowpark import Session
from typing import List
import config
from .yaml_loader import create_semantic_view, get_all_view_names
from utils.logging import log_detail, log_warning, log_error, log_step

CRITICAL_VIEWS = {'SAM_PORTFOLIO_VIEW'}


def create_semantic_views(session: Session, scenarios: List[str] = None):
    """Create all semantic views for the given scenarios."""
    if not scenarios:
        return

    views = config.get_required_views(scenarios)
    if not views:
        return

    log_step(f"Creating {len(views)} semantic views from YAML definitions")

    for view_name in views:
        try:
            msg = create_semantic_view(session, view_name)
            log_detail(f"  OK  {view_name}")
        except Exception as e:
            if view_name in CRITICAL_VIEWS:
                log_error(f" Failed to create {view_name}: {e}")
                raise
            else:
                log_warning(f"  Warning: Could not create {view_name}: {e}")


def create_ml_semantic_views(session: Session, scenarios: List[str] = None):
    """No-op — ML views are now created in the main create_semantic_views pass."""
    pass
