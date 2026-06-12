"""Tests for check discovery."""

from pathlib import Path

import pytest

from bootcamp_cli.checks import discover_checks


@pytest.fixture
def tmp_module_with_checks(tmp_path: Path) -> Path:
    """Create a synthetic module with check functions."""
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

def check_fails(context):
    return CheckResult(
        name="C2-fails",
        passed=False,
        detail="Check failed",
        lesson_ref="lesson.md §test"
    )
"""
    )

    check_multi = checks_dir / "check_multi.py"
    check_multi.write_text(
        """
from bootcamp_cli.checks import CheckResult

def check_returns_list(context):
    return [
        CheckResult(
            name="C3-list-1",
            passed=True,
            detail="First check",
            lesson_ref="lesson.md §test"
        ),
        CheckResult(
            name="C4-list-2",
            passed=False,
            detail="Second check",
            lesson_ref="lesson.md §test"
        )
    ]
"""
    )

    (module_dir / "workspace").mkdir()
    (module_dir / "fixtures").mkdir()

    return module_dir


class TestCheckDiscovery:
    """Test check function discovery."""

    def test_discover_checks_finds_functions(self, tmp_module_with_checks: Path) -> None:
        """Test that discover_checks finds check_* functions."""
        checks = discover_checks(tmp_module_with_checks)

        assert len(checks) >= 2
        check_names = [name for name, _ in checks]
        assert "check_passes" in check_names
        assert "check_fails" in check_names
        assert "check_returns_list" in check_names

    def test_discover_checks_empty_dir(self, tmp_path: Path) -> None:
        """Test that discover_checks returns empty list for module without checks."""
        module_dir = tmp_path / "empty_module"
        module_dir.mkdir()

        checks = discover_checks(module_dir)

        assert checks == []

    def test_discover_checks_returns_callables(
        self, tmp_module_with_checks: Path
    ) -> None:
        """Test that discovered items are callable."""
        checks = discover_checks(tmp_module_with_checks)

        for name, func in checks:
            assert callable(func)
            assert name.startswith("check_")

    def test_discover_checks_sorted_by_filename(
        self, tmp_module_with_checks: Path
    ) -> None:
        """Test that checks are returned in consistent order."""
        checks = discover_checks(tmp_module_with_checks)
        checks_again = discover_checks(tmp_module_with_checks)

        names_1 = [n for n, _ in checks]
        names_2 = [n for n, _ in checks_again]
        assert names_1 == names_2

    def test_discover_checks_multiple_files(self, tmp_path: Path) -> None:
        """Test discovery across multiple check files."""
        module_dir = tmp_path / "module"
        checks_dir = module_dir / "checks"
        checks_dir.mkdir(parents=True)

        for i in range(3):
            check_file = checks_dir / f"check_file{i}.py"
            check_file.write_text(
                f"""
from bootcamp_cli.checks import CheckResult

def check_file{i}(context):
    return CheckResult(
        name="C{i}",
        passed=True,
        detail="Check {i}",
        lesson_ref="lesson.md"
    )
"""
            )

        checks = discover_checks(module_dir)
        assert len(checks) == 3

    def test_discover_ignores_non_check_functions(self, tmp_path: Path) -> None:
        """Test that non-check functions are not discovered."""
        module_dir = tmp_path / "module"
        checks_dir = module_dir / "checks"
        checks_dir.mkdir(parents=True)

        check_file = checks_dir / "check_test.py"
        check_file.write_text(
            """
from bootcamp_cli.checks import CheckResult

def helper_function(context):
    return "not a check"

def check_real(context):
    return CheckResult(
        name="C1",
        passed=True,
        detail="Real check",
        lesson_ref="lesson.md"
    )

def another_helper():
    pass
"""
        )

        checks = discover_checks(module_dir)
        check_names = [n for n, _ in checks]

        assert "check_real" in check_names
        assert "helper_function" not in check_names
        assert "another_helper" not in check_names
