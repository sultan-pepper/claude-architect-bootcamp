"""Integration tests for the complete system."""

import sys
sys.path.insert(0, "/app/src")

from api_service.main import APIServer
from worker_service.worker import Worker


def test_server_and_worker_integration():
    """Test that server and worker can run together."""
    server = APIServer()
    worker = Worker(name="test")

    server.start()
    worker.start()

    # Process request
    response = server.handle_request("GET", "/health")
    assert response["status"] == "healthy"

    # Process task
    task_result = worker.process_task("task-1", {"data": "test"})
    assert task_result["status"] == "completed"

    server.stop()
    worker.stop()

    assert server.running is False
    assert worker.running is False
