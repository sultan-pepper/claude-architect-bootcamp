"""Tests for worker service (sibling location, not in tests/ dir)."""

import sys
sys.path.insert(0, "/app/src")

from worker_service.worker import Worker


def test_worker_init():
    """Test worker initialization."""
    worker = Worker(name="bg-worker")
    assert worker.name == "bg-worker"
    assert worker.running is False


def test_worker_process_task():
    """Test task processing."""
    worker = Worker()
    worker.start()

    result = worker.process_task("task-1", {"value": 42})
    assert result["status"] == "completed"
    assert result["task_id"] == "task-1"
    assert result["data_length"] == 1

    worker.stop()
