"""Tests for hint and solution gating logic."""

import json
import sqlite3
from pathlib import Path

import pytest

from bootcamp_cli.db import (
    init_db,
    record_check_run,
    get_hint_unlock_ts,
    set_hint_unlock,
)
from bootcamp_cli.state_mgmt import check_hint_gating, check_solution_gating


@pytest.fixture
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    return init_db(db_path)


class TestHintGating:
    """Test hint level gating logic."""

    def test_hint_level_1_locked_without_failures(self, tmp_db: sqlite3.Connection) -> None:
        """Test that level 1 is locked until there's at least one failed run."""
        can_show, reason = check_hint_gating(tmp_db, "01", 1)

        assert not can_show
        assert "failed" in reason.lower() or "unlock" in reason.lower()

    def test_hint_level_1_unlocks_after_one_failure(
        self, tmp_db: sqlite3.Connection
    ) -> None:
        """Test that level 1 unlocks after one failed check run."""
        # Record a failed check run
        report = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report)

        can_show, reason = check_hint_gating(tmp_db, "01", 1)

        assert can_show

    def test_hint_level_1_already_shown(self, tmp_db: sqlite3.Connection) -> None:
        """Test that level 1 cannot be shown twice."""
        # Record a failure
        report = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report)

        # First unlock
        can_show, reason = check_hint_gating(tmp_db, "01", 1)
        assert can_show
        set_hint_unlock(tmp_db, "01", 1)

        # Second attempt
        can_show, reason = check_hint_gating(tmp_db, "01", 1)
        assert not can_show
        assert "already shown" in reason.lower() or "unlock" in reason.lower()

    def test_hint_level_2_locked_without_level_1(
        self, tmp_db: sqlite3.Connection
    ) -> None:
        """Test that level 2 requires level 1 to be unlocked first."""
        # Record a failure for level 1
        report = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report)

        # Try to get level 2 without unlocking level 1
        can_show, reason = check_hint_gating(tmp_db, "01", 2)

        assert not can_show
        assert "level 1" in reason.lower()

    def test_hint_level_2_unlocks_after_failure_post_level1(
        self, tmp_db: sqlite3.Connection
    ) -> None:
        """Test that level 2 unlocks after a failure following level 1 unlock."""
        # Record first failure for level 1
        report1 = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report1)

        # Unlock level 1
        set_hint_unlock(tmp_db, "01", 1)

        # Record another failure after level 1 unlock
        report2 = json.dumps([{"name": "C2", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report2)

        # Now level 2 should be available
        can_show, reason = check_hint_gating(tmp_db, "01", 2)

        assert can_show

    def test_hint_level_3_progression(self, tmp_db: sqlite3.Connection) -> None:
        """Test that level 3 requires failure after level 2 unlock."""
        # Get level 1
        report1 = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report1)
        set_hint_unlock(tmp_db, "01", 1)

        # Get level 2
        report2 = json.dumps([{"name": "C2", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report2)
        set_hint_unlock(tmp_db, "01", 2)

        # Try level 3 without additional failure
        can_show, reason = check_hint_gating(tmp_db, "01", 3)
        assert not can_show

        # Record failure after level 2
        report3 = json.dumps([{"name": "C3", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report3)

        # Now level 3 is available
        can_show, reason = check_hint_gating(tmp_db, "01", 3)
        assert can_show


class TestSolutionGating:
    """Test solution gating logic."""

    def test_solution_locked_without_failures(self, tmp_db: sqlite3.Connection) -> None:
        """Test that solution is locked without failed runs."""
        can_show, reason = check_solution_gating(tmp_db, "01")

        assert not can_show
        assert "3" in reason or "failed" in reason.lower()

    def test_solution_locked_with_one_failure(self, tmp_db: sqlite3.Connection) -> None:
        """Test that solution requires 3+ failed runs."""
        report = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report)

        can_show, reason = check_solution_gating(tmp_db, "01")

        assert not can_show
        assert "2" in reason  # 2 more needed

    def test_solution_locked_with_two_failures(
        self, tmp_db: sqlite3.Connection
    ) -> None:
        """Test that solution requires 3 failed runs (not 2)."""
        report1 = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report1)

        report2 = json.dumps([{"name": "C2", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report2)

        can_show, reason = check_solution_gating(tmp_db, "01")

        assert not can_show
        assert "1" in reason  # 1 more needed

    def test_solution_unlocked_with_three_failures(
        self, tmp_db: sqlite3.Connection
    ) -> None:
        """Test that solution unlocks at 3 failed runs."""
        for i in range(3):
            report = json.dumps([{"name": f"C{i}", "passed": False}])
            record_check_run(tmp_db, "01", 0, 1, report)

        can_show, reason = check_solution_gating(tmp_db, "01")

        assert can_show

    def test_solution_available_with_many_failures(
        self, tmp_db: sqlite3.Connection
    ) -> None:
        """Test that solution is available with more than 3 failures."""
        for i in range(5):
            report = json.dumps([{"name": f"C{i}", "passed": False}])
            record_check_run(tmp_db, "01", 0, 1, report)

        can_show, reason = check_solution_gating(tmp_db, "01")

        assert can_show

    def test_solution_logic_counts_total_failures(
        self, tmp_db: sqlite3.Connection
    ) -> None:
        """Test that solution gating counts total failed runs, not just ones with all fails."""
        # Record runs with mixed pass/fail
        report1 = json.dumps([{"name": "C1", "passed": True}, {"name": "C2", "passed": False}])
        record_check_run(tmp_db, "01", 1, 1, report1)

        report2 = json.dumps([{"name": "C1", "passed": False}, {"name": "C2", "passed": False}])
        record_check_run(tmp_db, "01", 0, 2, report2)

        report3 = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report3)

        # Should have 3+ failed check runs total
        can_show, reason = check_solution_gating(tmp_db, "01")

        assert can_show


class TestHintGatingTimestamps:
    """Test that gating respects unlock timestamps."""

    def test_hint_unlock_timestamp_stored(self, tmp_db: sqlite3.Connection) -> None:
        """Test that unlock timestamps are stored."""
        # Record a failure
        report = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report)

        # Unlock level 1
        set_hint_unlock(tmp_db, "01", 1)

        # Verify timestamp exists
        ts = get_hint_unlock_ts(tmp_db, "01", 1)
        assert ts is not None

    def test_hint_counts_failures_after_unlock(self, tmp_db: sqlite3.Connection) -> None:
        """Test that level N+1 counts failures after level N unlock."""
        import time

        # First failure
        report1 = json.dumps([{"name": "C1", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report1)

        # Unlock level 1
        set_hint_unlock(tmp_db, "01", 1)
        time.sleep(0.1)  # Ensure timestamp separation

        # Second failure (this one should count for level 2)
        report2 = json.dumps([{"name": "C2", "passed": False}])
        record_check_run(tmp_db, "01", 0, 1, report2)

        # Level 2 should be available (has failure after level 1 unlock)
        can_show, reason = check_hint_gating(tmp_db, "01", 2)
        assert can_show
