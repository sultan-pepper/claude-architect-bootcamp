"""Tests for module state gating and current module logic."""

import json
import sqlite3
from pathlib import Path

import pytest

from bootcamp_cli.modules import (
    load_manifest,
    get_module_state,
    get_current_module,
)
from bootcamp_cli.db import init_db, set_module_state


@pytest.fixture
def tmp_curriculum(tmp_path: Path) -> Path:
    """Create a synthetic curriculum with manifest and modules."""
    curriculum_dir = tmp_path / "curriculum"
    modules_dir = curriculum_dir / "modules"
    modules_dir.mkdir(parents=True)

    manifest = {
        "modules": [
            {
                "id": "01",
                "dir": "01-agentic-loop",
                "name": "agentic-loop",
                "title": "The agentic loop",
                "track": "A",
                "depends_on": [],
            },
            {
                "id": "02",
                "dir": "02-multi-agent",
                "name": "multi-agent",
                "title": "Multi-agent orchestration",
                "track": "A",
                "depends_on": ["01"],
            },
            {
                "id": "03",
                "dir": "03-hooks",
                "name": "hooks",
                "title": "Hooks and lifecycle",
                "track": "A",
                "depends_on": ["01"],
            },
            {
                "id": "04",
                "dir": "04-claude-code-config",
                "name": "claude-code-config",
                "title": "Team-grade Claude Code config",
                "track": "B",
                "depends_on": [],
            },
            {
                "id": "07",
                "dir": "07-structured-output",
                "name": "structured-output",
                "title": "Structured output & extraction",
                "track": "C",
                "depends_on": [],
            },
            {
                "id": "09",
                "dir": "09-capstone-reliability",
                "name": "capstone-reliability",
                "title": "Capstone — escalation & reliability",
                "track": "C",
                "depends_on": ["02", "03"],
            },
        ]
    }

    manifest_path = curriculum_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    for mod_data in manifest["modules"]:
        mod_dir = modules_dir / mod_data["dir"]
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "lesson.md").write_text(f"Lesson for {mod_data['name']}\n")
        (mod_dir / "lab.md").write_text(f"Lab for {mod_data['name']}\n")
        (mod_dir / "rubric.md").write_text(f"Rubric for {mod_data['name']}\n")

        starter_dir = mod_dir / "starter"
        starter_dir.mkdir(exist_ok=True)
        (starter_dir / "sample.py").write_text("# Sample starter file\n")

    return curriculum_dir


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Create a temporary database."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


class TestModuleStateGating:
    """Test module state gating logic."""

    def test_fresh_db_initial_state(
        self, tmp_curriculum: Path, tmp_db: Path
    ) -> None:
        """Test that fresh DB has 01, 04, 07 available (track leaders)."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        assert get_module_state(conn, modules[0], modules) == "available"  # 01
        assert get_module_state(conn, modules[3], modules) == "available"  # 04
        assert get_module_state(conn, modules[4], modules) == "available"  # 07

        assert get_module_state(conn, modules[1], modules) == "locked"  # 02
        assert get_module_state(conn, modules[2], modules) == "locked"  # 03

        assert get_module_state(conn, modules[5], modules) == "locked"  # 09

    def test_passing_01_unlocks_02_and_03(
        self, tmp_curriculum: Path, tmp_db: Path
    ) -> None:
        """Test that passing 01 unlocks 02 and 03."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        set_module_state(conn, "01", "passed")

        assert get_module_state(conn, modules[1], modules) == "available"  # 02

        assert get_module_state(conn, modules[2], modules) == "locked"  # 03

        set_module_state(conn, "02", "passed")
        assert get_module_state(conn, modules[2], modules) == "available"  # 03

    def test_09_needs_02_03_plus_others(
        self, tmp_curriculum: Path, tmp_db: Path
    ) -> None:
        """Test that 09 requires 02, 03."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        assert get_module_state(conn, modules[5], modules) == "locked"

        set_module_state(conn, "01", "passed")
        set_module_state(conn, "04", "passed")
        set_module_state(conn, "07", "passed")

        assert get_module_state(conn, modules[5], modules) == "locked"

        set_module_state(conn, "02", "passed")
        assert get_module_state(conn, modules[5], modules) == "locked"

        set_module_state(conn, "03", "passed")
        # Still locked because 05 and 08 are missing

    def test_in_progress_stays_in_progress(
        self, tmp_curriculum: Path, tmp_db: Path
    ) -> None:
        """Test that in_progress state persists."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        set_module_state(conn, "01", "in_progress")
        assert get_module_state(conn, modules[0], modules) == "in_progress"

    def test_passed_stays_passed(self, tmp_curriculum: Path, tmp_db: Path) -> None:
        """Test that passed state persists."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        set_module_state(conn, "01", "passed")
        assert get_module_state(conn, modules[0], modules) == "passed"

    def test_track_independence(self, tmp_curriculum: Path, tmp_db: Path) -> None:
        """Test that tracks A, B, C are independent."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        assert get_module_state(conn, modules[0], modules) == "available"  # 01 (A)
        assert get_module_state(conn, modules[3], modules) == "available"  # 04 (B)
        assert get_module_state(conn, modules[4], modules) == "available"  # 07 (C)

        set_module_state(conn, "01", "passed")
        assert get_module_state(conn, modules[3], modules) == "available"
        assert get_module_state(conn, modules[4], modules) == "available"


class TestCurrentModule:
    """Test get_current_module logic."""

    def test_get_current_module_returns_in_progress(
        self, tmp_curriculum: Path, tmp_db: Path
    ) -> None:
        """Test that get_current_module returns the in_progress module."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        set_module_state(conn, "01", "in_progress")
        current = get_current_module(conn, modules)

        assert current is not None
        assert current.id == "01"

    def test_get_current_module_returns_none_when_all_passed(
        self, tmp_curriculum: Path, tmp_db: Path
    ) -> None:
        """Test that get_current_module returns None when all modules passed."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        set_module_state(conn, "01", "passed")
        current = get_current_module(conn, modules)

        assert current is None

    def test_get_current_module_returns_latest_in_progress(
        self, tmp_curriculum: Path, tmp_db: Path
    ) -> None:
        """Test that get_current_module returns the highest-id in_progress module."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row

        set_module_state(conn, "01", "passed")
        set_module_state(conn, "02", "in_progress")
        set_module_state(conn, "03", "in_progress")
        current = get_current_module(conn, modules)

        assert current is not None
        assert current.id == "03"
