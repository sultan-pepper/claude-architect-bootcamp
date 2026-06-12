"""Tests for CLI gating commands."""

import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bootcamp_cli.main import app
from bootcamp_cli.db import init_db, record_check_run


runner = CliRunner()


@pytest.fixture
def tmp_curriculum_full(tmp_path: Path) -> Path:
    """Create a full synthetic curriculum with modules and checks."""
    curriculum_dir = tmp_path / "curriculum"
    modules_dir = curriculum_dir / "modules"
    modules_dir.mkdir(parents=True)

    manifest = {
        "modules": [
            {
                "id": "01",
                "dir": "01-test",
                "name": "test",
                "title": "Test Module",
                "track": "A",
                "depends_on": [],
            },
        ]
    }

    manifest_path = curriculum_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    for mod_data in manifest["modules"]:
        mod_dir = modules_dir / mod_data["dir"]
        mod_dir.mkdir(parents=True, exist_ok=True)

        (mod_dir / "lesson.md").write_text(f"# Lesson {mod_data['id']}\n")
        (mod_dir / "lab.md").write_text(f"# Lab {mod_data['id']}\n")
        rubric_content = f"""# Rubric — {mod_data['id']} {mod_data['name']}

## Criteria

1. **C1-test** (deterministic): Test criterion — lesson_ref: lesson.md §test

## Hints

### Level 1
Test hint level 1

## Reference solution sketch

Sample solution
"""
        (mod_dir / "rubric.md").write_text(rubric_content)

        starter_dir = mod_dir / "starter"
        starter_dir.mkdir(exist_ok=True)
        (starter_dir / "sample.py").write_text("# Starter code\n")

        checks_dir = mod_dir / "checks"
        checks_dir.mkdir(exist_ok=True)
        check_file = checks_dir / "check_basic.py"
        check_file.write_text(
            """
from bootcamp_cli.checks import CheckResult

def check_passes(context):
    return CheckResult(
        name="C1-test",
        passed=True,
        detail="Check passed",
        lesson_ref="lesson.md §test"
    )
"""
        )

        (mod_dir / "fixtures").mkdir(exist_ok=True)

    return curriculum_dir


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


@pytest.fixture
def cli_env(tmp_curriculum_full: Path, tmp_db_path: Path, monkeypatch):
    """Set up environment for CLI testing."""
    monkeypatch.setenv("BOOTCAMP_DB", str(tmp_db_path))
    import bootcamp_cli.commands

    original_repo_root = bootcamp_cli.commands.REPO_ROOT
    original_manifest = bootcamp_cli.commands.MANIFEST_PATH
    original_labs = bootcamp_cli.commands.LABS_ROOT

    bootcamp_cli.commands.REPO_ROOT = tmp_curriculum_full.parent
    bootcamp_cli.commands.MANIFEST_PATH = tmp_curriculum_full / "manifest.json"
    bootcamp_cli.commands.LABS_ROOT = tmp_curriculum_full.parent / "labs"

    yield

    bootcamp_cli.commands.REPO_ROOT = original_repo_root
    bootcamp_cli.commands.MANIFEST_PATH = original_manifest
    bootcamp_cli.commands.LABS_ROOT = original_labs


class TestCLIHint:
    """Test the hint command."""

    def test_hint_gated_without_failures(self, cli_env, tmp_curriculum_full):
        """Test that hint is gated without failed runs."""
        runner.invoke(app, ["next"])

        result = runner.invoke(app, ["hint"])

        assert result.exit_code == 1
        output = (result.stdout or "") + (result.stderr or "")
        assert "unlock" in output.lower() or "fail" in output.lower() or "shown" in output.lower()

    def test_hint_available_after_check_failure(self, cli_env, tmp_curriculum_full):
        """Test that hint becomes available after check failure."""
        runner.invoke(app, ["next"])

        mod_dir = tmp_curriculum_full / "modules" / "01-test"
        checks_dir = mod_dir / "checks"
        check_file = checks_dir / "check_basic.py"
        check_file.write_text(
            """
from bootcamp_cli.checks import CheckResult

def check_passes(context):
    return CheckResult(
        name="C1-test",
        passed=False,
        detail="Check failed",
        lesson_ref="lesson.md §test"
    )
"""
        )

        runner.invoke(app, ["check"])

        result = runner.invoke(app, ["hint"])

        assert result.exit_code == 0
        assert "Hint" in result.stdout or "Level" in result.stdout


class TestCLISolution:
    """Test the solution command."""

    def test_solution_gated_without_failures(self, cli_env, tmp_curriculum_full):
        """Test that solution is gated without failures."""
        runner.invoke(app, ["next"])

        result = runner.invoke(app, ["solution"])

        assert result.exit_code == 1
        output = (result.stdout or "") + (result.stderr or "")
        assert "3" in output or "failed" in output.lower()

    def test_solution_available_after_three_failures(
        self, cli_env, tmp_curriculum_full, tmp_db_path
    ):
        """Test that solution unlocks at 3 failed runs."""
        runner.invoke(app, ["next"])

        conn = sqlite3.connect(str(tmp_db_path))
        for i in range(3):
            report = json.dumps([{"name": "C1", "passed": False}])
            record_check_run(conn, "01", 0, 1, report)
        conn.close()

        result = runner.invoke(app, ["solution"])

        assert result.exit_code == 0
        assert "solution" in result.stdout.lower() or "sketch" in result.stdout.lower()


class TestCLICheckModuleFlag:
    """Test the --module flag across commands."""

    def test_check_with_module_flag(self, cli_env, tmp_curriculum_full):
        """Test that check accepts --module flag."""
        runner.invoke(app, ["next"])

        result = runner.invoke(app, ["check", "-m", "01"])

        assert result.exit_code == 0

    def test_hint_with_module_flag(self, cli_env, tmp_curriculum_full):
        """Test that hint accepts --module flag."""
        runner.invoke(app, ["next"])

        result = runner.invoke(app, ["hint", "-m", "01"])

        assert result.exit_code in [0, 1]

    def test_next_with_module_flag(self, cli_env):
        """Test that next accepts --module flag."""
        result = runner.invoke(app, ["next", "-m", "01"])

        assert result.exit_code == 0

    def test_command_error_on_invalid_module(self, cli_env):
        """Test that invalid module id returns error."""
        result = runner.invoke(app, ["check", "-m", "99"])

        assert result.exit_code == 2
        output = (result.stdout or "") + (result.stderr or "")
        assert "not found" in output.lower() or "error" in output.lower()
