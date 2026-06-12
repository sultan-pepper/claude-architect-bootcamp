"""Command implementations for bootcamp CLI."""

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional

import typer

from bootcamp_cli.db import (
    get_db_path, init_db, get_module_state as db_get_state,
    get_last_check_run, set_module_state, get_module_assisted,
    set_hint_unlock,
)
from bootcamp_cli.modules import (
    load_manifest, get_current_module, get_module_state, materialize_workspace, Module
)
from bootcamp_cli.checks import run_checks, CheckContext
from bootcamp_cli.rubric import parse_rubric_hints, parse_reference_solution
from bootcamp_cli.state_mgmt import (
    resolve_module,
    check_module_available,
    get_lowest_available,
    process_check_results,
    check_hint_gating,
    check_solution_gating,
)
from bootcamp_cli.output import (
    format_status_table,
    format_status_json,
    format_check_results_json,
    format_check_results_text,
)

REPO_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = REPO_ROOT / "curriculum" / "manifest.json"
LABS_ROOT = REPO_ROOT / "labs"


def get_modules():
    return load_manifest(MANIFEST_PATH)


def get_conn():
    db_path = get_db_path()
    return init_db(db_path)


def cmd_status(json_output: bool) -> None:
    """Print status of all modules."""
    conn = get_conn()
    modules = get_modules()

    status_data = []
    for module in modules:
        state = get_module_state(conn, module, modules)
        assisted = get_module_assisted(conn, module.id)
        last_run = get_last_check_run(conn, module.id)
        check_summary = f"{last_run['passed']}p/{last_run['failed']}f" if last_run else "-"

        status_data.append({
            "id": module.id,
            "title": module.title,
            "track": module.track,
            "state": state,
            "check_summary": check_summary,
            "assisted": assisted
        })

    if json_output:
        typer.echo(format_status_json(status_data))
    else:
        print(format_status_table(status_data))


def cmd_next(module: Optional[str]) -> None:
    """Start next available module."""
    try:
        conn = get_conn()
        all_modules = get_modules()

        if module:
            mod, err = resolve_module(module, all_modules)
            if not mod:
                typer.echo(f"Error: {err}", err=True)
                raise typer.Exit(2)
            target = mod
        else:
            target = get_lowest_available(conn, all_modules)
            if not target:
                in_progress = [m for m in all_modules
                               if db_get_state(conn, m.id) == "in_progress"]
                target = min(in_progress, key=lambda m: m.id) if in_progress else None
                if not target:
                    typer.echo("Error: No modules available.", err=True)
                    raise typer.Exit(1)
        lab_dir = LABS_ROOT / target.dir
        if lab_dir.exists() and db_get_state(conn, target.id) == "in_progress":
            typer.echo(f"Lab path: {lab_dir}")
            raise typer.Exit(0)

        # Check if module is available or in_progress
        available, reason = check_module_available(conn, target, all_modules)
        if not available and db_get_state(conn, target.id) != "in_progress":
            typer.echo(f"Error: {reason}", err=True)
            raise typer.Exit(1)

        lab_dir = materialize_workspace(target, LABS_ROOT)
        set_module_state(conn, target.id, "in_progress")

        typer.echo(f"Module {target.id}: {target.title}")
        typer.echo(f"Lab path: {lab_dir}")
        typer.echo("Started. Run `bootcamp check` to test your work.")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(2)


def cmd_check(module: Optional[str], json_output: bool) -> None:
    """Run checks for a module."""
    try:
        conn = get_conn()
        all_modules = get_modules()

        if module:
            mod, err = resolve_module(module, all_modules)
            if not mod:
                typer.echo(f"Error: {err}", err=True)
                raise typer.Exit(2)
        else:
            current = get_current_module(conn, all_modules)
            if not current:
                typer.echo("Error: No module in progress.", err=True)
                raise typer.Exit(1)
            mod = current

        workspace_dir = LABS_ROOT / mod.dir / "workspace"
        context = CheckContext(
            module_id=mod.id,
            workspace=workspace_dir,
            fixtures=mod.path / "fixtures"
        )

        results = run_checks(mod.path, context)
        if not results:
            typer.echo(
                f"Error: no checks discovered for module {mod.id} "
                f"(checks/ is empty or has no check_* functions).", err=True)
            raise typer.Exit(2)
        passed, failed = process_check_results(conn, mod.id, results)

        if json_output:
            typer.echo(format_check_results_json(results))
        else:
            print(format_check_results_text(results))

        if failed == 0:
            set_module_state(conn, mod.id, "passed")
            typer.echo(f"\n✓ All checks passed! Module {mod.id} complete.")
            raise typer.Exit(0)
        else:
            typer.echo(f"\n✗ {failed} check(s) failed.")
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(2)


def cmd_hint(module: Optional[str]) -> None:
    """Print next hint level."""
    try:
        conn = get_conn()
        all_modules = get_modules()

        if module:
            mod, err = resolve_module(module, all_modules)
            if not mod:
                typer.echo(f"Error: {err}", err=True)
                raise typer.Exit(2)
        else:
            current = get_current_module(conn, all_modules)
            if not current:
                typer.echo("Error: No module in progress.", err=True)
                raise typer.Exit(1)
            mod = current

        rubric_path = mod.path / "rubric.md"
        hints = parse_rubric_hints(rubric_path)

        if not hints:
            typer.echo("No hints available for this module.", err=True)
            raise typer.Exit(1)

        for level in range(1, max(hints.keys()) + 1):
            can_show, reason = check_hint_gating(conn, mod.id, level)
            if can_show:
                set_hint_unlock(conn, mod.id, level)
                if level in hints:
                    print(f"Hint Level {level}:")
                    print(hints[level])
                    raise typer.Exit(0)
            elif reason != "Hint already shown":
                # First locked level: tell the learner how to unlock it.
                typer.echo(reason, err=True)
                raise typer.Exit(1)

        typer.echo("All hints have been shown.", err=True)
        raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(2)


def cmd_mentor(question: str, module: Optional[str]) -> None:
    """Chat with mentor."""
    try:
        from bootcamp_cli.mentor import mentor_chat, MentorError

        conn = get_conn()
        all_modules = get_modules()

        if module:
            mod, err = resolve_module(module, all_modules)
            if not mod:
                typer.echo(f"Error: {err}", err=True)
                raise typer.Exit(2)
        else:
            current = get_current_module(conn, all_modules)
            if not current:
                typer.echo("Error: No module in progress.", err=True)
                raise typer.Exit(1)
            mod = current

        response = mentor_chat(question, mod.id, mod.path, conn)
        print(response)

    except MentorError as e:
        typer.echo(f"Mentor error: {str(e)}", err=True)
        raise typer.Exit(2)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(2)


def cmd_solution(module: Optional[str]) -> None:
    """Print reference solution."""
    try:
        conn = get_conn()
        all_modules = get_modules()

        if module:
            mod, err = resolve_module(module, all_modules)
            if not mod:
                typer.echo(f"Error: {err}", err=True)
                raise typer.Exit(2)
        else:
            current = get_current_module(conn, all_modules)
            if not current:
                typer.echo("Error: No module in progress.", err=True)
                raise typer.Exit(1)
            mod = current

        can_show, reason = check_solution_gating(conn, mod.id)
        if not can_show:
            typer.echo(reason, err=True)
            raise typer.Exit(1)

        rubric_path = mod.path / "rubric.md"
        solution_text = parse_reference_solution(rubric_path)

        if not solution_text:
            typer.echo("No reference solution available.", err=True)
            raise typer.Exit(1)

        print("Reference Solution Sketch:")
        print(solution_text)

        state = db_get_state(conn, mod.id)
        set_module_state(conn, mod.id, state, assisted=True)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(2)
