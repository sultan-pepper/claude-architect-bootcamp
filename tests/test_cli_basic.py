"""Tests for basic CLI commands using typer.testing.CliRunner."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bootcamp_cli.main import app
from bootcamp_cli.db import init_db


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
            {
                "id": "02",
                "dir": "02-test-2",
                "name": "test-2",
                "title": "Test Module 2",
                "track": "A",
                "depends_on": ["01"],
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


class TestCLIStatus:
    """Test the status command."""

    def test_status_exit_code_zero(self, cli_env):
        """Test that status command exits with code 0."""
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0

    def test_status_shows_modules_text(self, cli_env):
        """Test that status displays module information in table format."""
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "01" in result.stdout or "Test Module" in result.stdout

    def test_status_json_output(self, cli_env):
        """Test status with --json flag."""
        result = runner.invoke(app, ["status", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_status_json_structure(self, cli_env):
        """Test that JSON output has required fields."""
        result = runner.invoke(app, ["status", "--json"])

        data = json.loads(result.stdout)
        assert "id" in data[0]
        assert "title" in data[0]
        assert "track" in data[0]
        assert "state" in data[0]


class TestCLINext:
    """Test the next command."""

    def test_next_creates_lab_directory(self, cli_env, tmp_curriculum_full):
        """Test that next creates labs/01-test/ directory."""
        result = runner.invoke(app, ["next"])

        assert result.exit_code == 0
        lab_dir = tmp_curriculum_full.parent / "labs" / "01-test"
        assert lab_dir.exists()

    def test_next_copies_lesson_and_lab(self, cli_env, tmp_curriculum_full):
        """Test that next copies lesson.md and lab.md."""
        result = runner.invoke(app, ["next"])

        assert result.exit_code == 0
        lab_dir = tmp_curriculum_full.parent / "labs" / "01-test"
        assert (lab_dir / "lesson.md").exists()
        assert (lab_dir / "lab.md").exists()

    def test_next_creates_workspace(self, cli_env, tmp_curriculum_full):
        """Test that next creates workspace directory with starter files."""
        result = runner.invoke(app, ["next"])

        assert result.exit_code == 0
        workspace = tmp_curriculum_full.parent / "labs" / "01-test" / "workspace"
        assert workspace.exists()
        assert (workspace / "sample.py").exists()

    def test_next_prints_lab_path(self, cli_env, tmp_curriculum_full):
        """Test that next prints the lab directory path."""
        result = runner.invoke(app, ["next"])

        assert result.exit_code == 0
        assert "01-test" in result.stdout or "Lab path" in result.stdout

    def test_next_idempotent_no_overwrite(self, cli_env, tmp_curriculum_full):
        """Test that next does not overwrite existing workspace files."""
        result1 = runner.invoke(app, ["next"])
        assert result1.exit_code == 0

        workspace_file = tmp_curriculum_full.parent / "labs" / "01-test" / "workspace" / "sample.py"
        workspace_file.write_text("# Modified\n")

        result2 = runner.invoke(app, ["next"])
        assert result2.exit_code == 0

        assert workspace_file.read_text() == "# Modified\n"

    def test_next_exit_1_when_locked(self, cli_env, tmp_db_path):
        """Test that next exits with code 1 when module is locked."""
        result = runner.invoke(app, ["next", "-m", "02"])

        assert result.exit_code == 1
        output = result.stdout.lower() + (result.stderr or "").lower() if result.stderr else result.stdout.lower()
        assert "locked" in output or "depend" in output or "error" in output


class TestCLICheck:
    """Test the check command."""

    def test_check_exit_zero_all_pass(self, cli_env, tmp_curriculum_full):
        """Test that check exits 0 when all checks pass."""
        runner.invoke(app, ["next"])

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 0

    def test_check_shows_results(self, cli_env, tmp_curriculum_full):
        """Test that check displays check results."""
        runner.invoke(app, ["next"])
        result = runner.invoke(app, ["check"])

        assert result.exit_code == 0
        assert "PASS" in result.stdout or "check" in result.stdout.lower()

    def test_check_json_output(self, cli_env, tmp_curriculum_full):
        """Test check with --json flag."""
        runner.invoke(app, ["next"])
        result = runner.invoke(app, ["check", "--json"])

        assert result.exit_code == 0
        output = result.stdout
        start = output.find('[')
        end = output.rfind(']') + 1
        if start >= 0 and end > start:
            json_str = output[start:end]
            data = json.loads(json_str)
            assert isinstance(data, list)

    def test_check_exit_2_no_checks_dir(self, cli_env, tmp_curriculum_full):
        """Test that check exits 2 when no checks are found."""
        mod_dir = tmp_curriculum_full / "modules" / "03-no-checks"
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "lesson.md").write_text("# Lesson\n")
        (mod_dir / "lab.md").write_text("# Lab\n")
        (mod_dir / "rubric.md").write_text("# Rubric\n")
        (mod_dir / "starter").mkdir()
        (mod_dir / "fixtures").mkdir()

        with open(tmp_curriculum_full / "manifest.json") as f:
            manifest = json.load(f)

        manifest["modules"].append({
            "id": "03",
            "dir": "03-no-checks",
            "name": "no-checks",
            "title": "No Checks",
            "track": "B",
            "depends_on": [],
        })

        with open(tmp_curriculum_full / "manifest.json", "w") as f:
            json.dump(manifest, f)

        runner.invoke(app, ["next", "-m", "03"])

        result = runner.invoke(app, ["check"])
        assert result.exit_code == 2
