"""Module state management operations."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from bootcamp_cli.db import (
    get_module_state as db_get_state,
    set_module_state,
    record_check_run,
    count_failed_check_runs,
    get_hint_unlock_ts,
    set_hint_unlock,
)
from bootcamp_cli.modules import (
    Module,
    get_module_state,
    materialize_workspace,
)


def resolve_module(
    module: Optional[str], all_modules: list[Module]
) -> tuple[Optional[Module], str]:
    """Resolve a module id to a Module object.

    Returns (module, error_message) or (None, error) if not found.
    """
    if not module:
        return None, ""

    mod = next((m for m in all_modules if m.id == module), None)
    if not mod:
        return None, f"Module {module} not found"

    return mod, ""


def check_module_available(
    conn: sqlite3.Connection, module: Module, all_modules: list[Module]
) -> tuple[bool, str]:
    """Check if module is available, return (available, reason).

    If not available, reason explains why.
    """
    state = get_module_state(conn, module, all_modules)

    if state == "available":
        return True, ""

    if state == "passed":
        return False, "Module already completed"

    if state == "in_progress":
        return False, "Module already started"

    # locked - explain why
    deps = module.depends_on
    missing = [
        m.title
        for m in all_modules
        if m.id in deps and db_get_state(conn, m.id) != "passed"
    ]
    if missing:
        return False, f"Dependencies not met: {', '.join(missing)}"

    return False, "Module is locked"


def get_lowest_available(
    conn: sqlite3.Connection, all_modules: list[Module]
) -> Optional[Module]:
    """Get the lowest-id available module."""
    candidates = [
        m for m in all_modules
        if get_module_state(conn, m, all_modules) == "available"
    ]
    return min(candidates, key=lambda m: m.id) if candidates else None


def process_check_results(
    conn: sqlite3.Connection,
    module_id: str,
    results: list
) -> tuple[int, int]:
    """Record check results and return (passed_count, failed_count)."""
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count

    report_json = json.dumps([
        {
            "name": r.name,
            "passed": r.passed,
            "detail": r.detail,
            "lesson_ref": r.lesson_ref
        }
        for r in results
    ])
    record_check_run(conn, module_id, passed_count, failed_count, report_json)

    return passed_count, failed_count


def check_hint_gating(
    conn: sqlite3.Connection, module_id: str, level: int
) -> tuple[bool, str]:
    """Check if a hint level is gated. Returns (can_show, reason)."""
    unlock_ts = get_hint_unlock_ts(conn, module_id, level)
    if unlock_ts:
        # Already unlocked
        return False, "Hint already shown"

    if level == 1:
        # Level 1 requires ≥1 failed run
        failed_count = count_failed_check_runs(conn, module_id)
        if failed_count < 1:
            return False, "Hint locked. Run checks and fail at least once to unlock."

    else:
        # Level N+1 requires failed run after level N unlock
        level_n_ts = get_hint_unlock_ts(conn, module_id, level - 1)
        if not level_n_ts:
            return False, f"Hint locked. Unlock level {level - 1} first."

        failed_after = count_failed_check_runs(conn, module_id, level_n_ts)
        if failed_after < 1:
            return False, f"Hint locked. Run checks and fail again to unlock level {level}."

    return True, ""


def check_solution_gating(
    conn: sqlite3.Connection, module_id: str
) -> tuple[bool, str]:
    """Check if solution is gated. Returns (can_show, reason)."""
    failed_count = count_failed_check_runs(conn, module_id)
    if failed_count >= 3:
        return True, ""

    remaining = 3 - failed_count
    return False, f"Solution locked. {remaining} more failed check run(s) needed."
