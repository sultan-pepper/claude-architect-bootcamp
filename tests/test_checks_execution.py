"""Tests for check execution and error handling."""

import subprocess
import sys
from pathlib import Path

import pytest

from bootcamp_cli.checks import CheckResult, CheckContext, run_checks


@pytest.fixture
def tmp_module_with_checks(tmp_path: Path) -> Path:
    """Create a module with checks."""
    module_dir = tmp_path / "module"
    checks_dir = module_dir / "checks"
    checks_dir.mkdir(parents=True)

    check_simple = checks_dir / "check_simple.py"
    check_simple.write_text(
        """
from bootcamp_cli.checks import CheckResult

def check_passes(context):
    return CheckResult(
        name="C1-simple",
        passed=True,
        detail="Check passed",
        lesson_ref="lesson.md §test"
    )
"""
    )

    (module_dir / "workspace").mkdir()
    (module_dir / "fixtures").mkdir()

    return module_dir


class TestCheckExecution:
    """Test check execution and result collection."""

    def test_run_checks_executes_all(self, tmp_module_with_checks: Path) -> None:
        """Test that run_checks executes all discovered checks."""
        workspace = tmp_module_with_checks / "workspace"
        fixtures = tmp_module_with_checks / "fixtures"
        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        results = run_checks(tmp_module_with_checks, context)

        assert len(results) >= 1
        assert all(isinstance(r, CheckResult) for r in results)

    def test_run_checks_flattens_list_results(
        self, tmp_path: Path
    ) -> None:
        """Test that list returns from checks are flattened."""
        module_dir = tmp_path / "module"
        checks_dir = module_dir / "checks"
        checks_dir.mkdir(parents=True)

        check_file = checks_dir / "check_multi.py"
        check_file.write_text(
            """
from bootcamp_cli.checks import CheckResult

def check_returns_list(context):
    return [
        CheckResult(
            name="C3-list-1",
            passed=True,
            detail="First",
            lesson_ref="lesson.md"
        ),
        CheckResult(
            name="C4-list-2",
            passed=False,
            detail="Second",
            lesson_ref="lesson.md"
        )
    ]
"""
        )

        (module_dir / "workspace").mkdir()
        (module_dir / "fixtures").mkdir()

        workspace = module_dir / "workspace"
        fixtures = module_dir / "fixtures"
        context = CheckContext(module_id="01", workspace=workspace, fixtures=fixtures)

        results = run_checks(module_dir, context)

        multi_results = [r for r in results if "C3-" in r.name or "C4-" in r.name]
        assert len(multi_results) == 2

    def test_run_learner_captures_output(self, tmp_module_with_checks: Path) -> None:
        """Test that run_learner captures stdout/stderr."""
        workspace = tmp_module_with_checks / "workspace"
        fixtures = tmp_module_with_checks / "fixtures"
        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        result = context.run_learner([sys.executable, "-c", "print('hello')"])

        assert result.stdout == "hello\n"
        assert result.returncode == 0

    def test_run_learner_enforces_timeout(self, tmp_module_with_checks: Path) -> None:
        """Test that run_learner enforces timeout."""
        workspace = tmp_module_with_checks / "workspace"
        fixtures = tmp_module_with_checks / "fixtures"
        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        with pytest.raises(subprocess.TimeoutExpired):
            context.run_learner(
                [sys.executable, "-c", "import time; time.sleep(2)"], timeout=1
            )

    def test_run_learner_with_env_vars(self, tmp_module_with_checks: Path) -> None:
        """Test that run_learner can pass env vars."""
        workspace = tmp_module_with_checks / "workspace"
        fixtures = tmp_module_with_checks / "fixtures"
        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        result = context.run_learner(
            [sys.executable, "-c", "import os; print(os.environ.get('TEST_VAR', 'none'))"],
            env={"TEST_VAR": "hello"},
        )

        assert "hello" in result.stdout

    def test_run_learner_with_stdin(self, tmp_module_with_checks: Path) -> None:
        """Test that run_learner can pass stdin."""
        workspace = tmp_module_with_checks / "workspace"
        fixtures = tmp_module_with_checks / "fixtures"
        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        result = context.run_learner(
            [sys.executable, "-c", "import sys; print(sys.stdin.read().upper())"],
            stdin="hello\n",
        )

        assert "HELLO" in result.stdout

    def test_run_learner_cwd_is_workspace(self, tmp_module_with_checks: Path) -> None:
        """Test that run_learner sets cwd to workspace."""
        workspace = tmp_module_with_checks / "workspace"
        fixtures = tmp_module_with_checks / "fixtures"

        (workspace / "test.txt").write_text("content")

        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        result = context.run_learner(
            [sys.executable, "-c", "import os; print(os.getcwd())"]
        )

        assert str(workspace) in result.stdout


class TestCheckErrors:
    """Test error handling in checks."""

    def test_check_exception_creates_failed_result(self, tmp_path: Path) -> None:
        """Test that exceptions in checks become failed results."""
        module_dir = tmp_path / "module"
        checks_dir = module_dir / "checks"
        checks_dir.mkdir(parents=True)

        check_file = checks_dir / "check_error.py"
        check_file.write_text(
            """
from bootcamp_cli.checks import CheckResult

def check_crashes(context):
    raise ValueError("Something went wrong")
"""
        )

        (module_dir / "workspace").mkdir()
        (module_dir / "fixtures").mkdir()

        workspace = module_dir / "workspace"
        fixtures = module_dir / "fixtures"
        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        results = run_checks(module_dir, context)

        assert any("crashed" in r.detail for r in results)
        assert any(not r.passed for r in results)

    def test_check_exception_includes_exception_type(self, tmp_path: Path) -> None:
        """Test that crash details include exception type."""
        module_dir = tmp_path / "module"
        checks_dir = module_dir / "checks"
        checks_dir.mkdir(parents=True)

        check_file = checks_dir / "check_error.py"
        check_file.write_text(
            """
def check_crashes(context):
    raise RuntimeError("Specific error message")
"""
        )

        (module_dir / "workspace").mkdir()
        (module_dir / "fixtures").mkdir()

        workspace = module_dir / "workspace"
        fixtures = module_dir / "fixtures"
        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        results = run_checks(module_dir, context)

        crash_results = [r for r in results if "crashed" in r.detail]
        assert len(crash_results) > 0
        assert any("RuntimeError" in r.detail for r in crash_results)
        assert any("Specific error message" in r.detail for r in crash_results)

    def test_run_checks_continues_after_error(self, tmp_path: Path) -> None:
        """Test that run_checks continues despite errors."""
        module_dir = tmp_path / "module"
        checks_dir = module_dir / "checks"
        checks_dir.mkdir(parents=True)

        check_file = checks_dir / "check_error.py"
        check_file.write_text(
            """
from bootcamp_cli.checks import CheckResult

def check_crashes(context):
    raise Exception("Boom")

def check_passes(context):
    return CheckResult(
        name="C-safe",
        passed=True,
        detail="This one is fine",
        lesson_ref="lesson.md §test"
    )
"""
        )

        (module_dir / "workspace").mkdir()
        (module_dir / "fixtures").mkdir()

        workspace = module_dir / "workspace"
        fixtures = module_dir / "fixtures"
        context = CheckContext(
            module_id="01", workspace=workspace, fixtures=fixtures
        )

        results = run_checks(module_dir, context)

        assert len(results) >= 2
        assert any(r.name == "C-safe" for r in results)
        assert any("crashed" in r.detail for r in results)
