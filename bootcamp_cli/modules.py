"""Module manifest loading and state derivation."""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import sqlite3


@dataclass
class Module:
    """A module in the curriculum."""

    id: str
    dir: str
    name: str
    title: str
    track: str
    depends_on: list[str]
    path: Path  # Full path to module dir


def load_manifest(manifest_path: Path) -> list[Module]:
    """Load modules from curriculum/manifest.json."""
    with open(manifest_path) as f:
        data = json.load(f)

    modules: list[Module] = []
    manifest_dir = manifest_path.parent

    for mod_data in data["modules"]:
        mod = Module(
            id=mod_data["id"],
            dir=mod_data["dir"],
            name=mod_data["name"],
            title=mod_data["title"],
            track=mod_data["track"],
            depends_on=mod_data["depends_on"],
            path=manifest_dir / "modules" / mod_data["dir"]
        )
        modules.append(mod)

    return modules


def get_module_state(
    conn: sqlite3.Connection, module: Module, all_modules: list[Module]
) -> str:
    """Derive module state: locked/available/in_progress/passed."""
    from bootcamp_cli.db import get_module_state as db_get_state

    current = db_get_state(conn, module.id)

    # If already passed, stay passed
    if current == "passed":
        return "passed"

    # If in progress, stay in progress
    if current == "in_progress":
        return "in_progress"

    # Check dependencies: all must be passed for availability
    if module.depends_on:
        for dep_id in module.depends_on:
            dep_module = next((m for m in all_modules if m.id == dep_id), None)
            if not dep_module or db_get_state(conn, dep_id) != "passed":
                return "locked"

    # Check track order: all lower-id modules in same track must be passed
    same_track = [m for m in all_modules if m.track == module.track]
    for earlier in same_track:
        if earlier.id < module.id:
            if db_get_state(conn, earlier.id) != "passed":
                return "locked"

    # All conditions met: available
    return "available"


def materialize_workspace(module: Module, labs_root: Path) -> Path:
    """Create labs/NN-name/ and populate it. Never overwrite existing workspace."""
    from bootcamp_cli.db import init_db

    lab_dir = labs_root / module.dir
    lab_dir.mkdir(parents=True, exist_ok=True)

    workspace_dir = lab_dir / "workspace"

    # Copy lesson.md and lab.md if they exist
    lesson_src = module.path / "lesson.md"
    if lesson_src.exists():
        shutil.copy2(lesson_src, lab_dir / "lesson.md")

    lab_src = module.path / "lab.md"
    if lab_src.exists():
        shutil.copy2(lab_src, lab_dir / "lab.md")

    # Only materialize workspace if it doesn't exist
    if not workspace_dir.exists():
        starter_src = module.path / "starter"
        if starter_src.exists():
            shutil.copytree(starter_src, workspace_dir)
        else:
            # Create empty workspace if no starter
            workspace_dir.mkdir(parents=True, exist_ok=True)

    return lab_dir


def get_current_module(
    conn: sqlite3.Connection, all_modules: list[Module]
) -> Optional[Module]:
    """Get the most recently next-ed module still in_progress."""
    from bootcamp_cli.db import get_module_state as db_get_state

    # Find all in_progress modules, return the one with latest id
    candidates = [m for m in all_modules if db_get_state(conn, m.id) == "in_progress"]
    if not candidates:
        return None

    # Return the one that was most recently moved to in_progress
    # For now, just return highest id (simple heuristic)
    return max(candidates, key=lambda m: m.id)
