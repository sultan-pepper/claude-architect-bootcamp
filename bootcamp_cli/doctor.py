"""Doctor command implementation."""

import os
import sys
from pathlib import Path

import typer

from bootcamp_cli.commands import get_modules, get_conn
from bootcamp_cli.db import get_db_path, init_db


def cmd_doctor() -> None:
    """Verify system setup."""
    issues = []
    warnings = []

    if sys.version_info < (3, 12):
        issues.append("Python 3.12+ required")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        issues.append("ANTHROPIC_API_KEY not set")

    try:
        modules = get_modules()
        print(f"✓ Manifest loads ({len(modules)} modules)")
    except Exception as e:
        issues.append(f"Manifest load failed: {str(e)}")
        modules = []

    for mod in modules:
        if not mod.path.exists():
            issues.append(f"Module {mod.id} dir missing")
        else:
            for fname in ["lesson.md", "lab.md", "rubric.md"]:
                if not (mod.path / fname).exists():
                    warnings.append(f"Module {mod.id} missing {fname}")

    try:
        db_path = get_db_path()
        conn = init_db(db_path)
        conn.execute("SELECT COUNT(*) FROM progress")
        conn.close()
        print(f"✓ Database writable at {db_path}")
    except Exception as e:
        issues.append(f"Database error: {str(e)}")

    try:
        import shutil
        if shutil.which("claude"):
            print("✓ claude CLI on PATH")
        else:
            warnings.append("claude CLI not on PATH")
    except Exception:
        warnings.append("claude CLI not on PATH")

    grocery_path = os.environ.get("GROCERY_DB_PATH")
    if grocery_path and not Path(grocery_path).exists():
        issues.append("GROCERY_DB_PATH file missing")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  ⚠ {w}")

    if issues:
        print("\nErrors:")
        for issue in issues:
            print(f"  ✗ {issue}")
        raise typer.Exit(1)
    else:
        if not warnings:
            print("✓ All checks passed")
        raise typer.Exit(0)
