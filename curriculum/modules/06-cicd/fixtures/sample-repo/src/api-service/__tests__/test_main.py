"""Tests for API service main module."""

import sys
sys.path.insert(0, "/app/src")

from api_service.main import APIServer


def test_server_initialization():
    """Test server initialization."""
    server = APIServer(host="127.0.0.1", port=9000)
    assert server.host == "127.0.0.1"
    assert server.port == 9000
    assert server.running is False


def test_server_start_stop():
    """Test server start and stop."""
    server = APIServer()
    server.start()
    assert server.running is True
    server.stop()
    assert server.running is False


def test_health_check():
    """Test health check endpoint."""
    server = APIServer()
    server.start()
    response = server.handle_request("GET", "/health")
    assert response["status"] == "healthy"
    assert response["requests"] == 1
    server.stop()


def test_not_found():
    """Test 404 response."""
    server = APIServer()
    server.start()
    response = server.handle_request("GET", "/invalid")
    assert response["error"] is True
    assert response["code"] == 404
    server.stop()
