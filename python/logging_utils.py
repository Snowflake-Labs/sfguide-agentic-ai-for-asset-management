# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# =============================================================================
# LOGGING & OUTPUT CONTROL
# =============================================================================
"""
Logging utilities for SAM Demo build process.
Provides verbosity-controlled output for phases, steps, and details.
"""

# Verbosity levels: 0=minimal (phases only), 1=normal (steps), 2=verbose (all details)
VERBOSITY = 0  # Default to minimal output

# Progress indicators for minimal output
_current_phase = None
_step_count = 0
_last_step_name = None


def set_verbosity(level: int):
    """Set output verbosity level: 0=minimal, 1=normal, 2=verbose"""
    global VERBOSITY
    VERBOSITY = level


def log_phase(phase_name: str):
    """Log a major phase (always shown). E.g., 'Structured Data', 'AI Components'"""
    global _current_phase, _step_count, _last_step_name
    _current_phase = phase_name
    _step_count = 0
    _last_step_name = None
    print(f"\n{'='*60}")
    print(f"  {phase_name}")
    print(f"{'='*60}")


def log_step(step_name: str):
    """Log a step within a phase - shows step name in minimal mode"""
    global _step_count, _last_step_name
    _step_count += 1
    _last_step_name = step_name
    if VERBOSITY >= 1:
        print(f"  [{_step_count}] {step_name}")
    else:
        # Minimal mode: show step name with progress indicator
        print(f"  → {step_name}...", flush=True)


def log_substep(step_name: str):
    """Log a sub-step within a step (shown at verbosity >= 1).
    
    Use for detailed progress like individual table builds, 
    while log_step() is for high-level progress visible at level 0.
    """
    if VERBOSITY >= 1:
        print(f"    → {step_name}...")


def log_detail(message: str):
    """Log detailed info (shown at verbosity >= 2)"""
    if VERBOSITY >= 2:
        print(f"      {message}")


def log_info(message: str):
    """Log informational message (shown at verbosity >= 1)"""
    if VERBOSITY >= 1:
        print(f"      {message}")


def log_success(message: str):
    """Log success message (shown at verbosity >= 1)"""
    if VERBOSITY >= 1:
        print(f"    ✅ {message}")


def log_warning(message: str):
    """Log warning message (always shown)"""
    print(f"    ⚠️  {message}")


def log_error(message: str):
    """Log error message (always shown)"""
    print(f"    ❌ {message}")


def log_phase_complete(summary: str = None):
    """Mark phase complete with optional summary"""
    if summary:
        print(f"  ✅ {summary}")

