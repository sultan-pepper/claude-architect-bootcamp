"""Pytest configuration and fixtures."""

import sys
import pytest


@pytest.fixture
def sample_user():
    """Fixture providing sample user data."""
    return {"email": "test@example.com", "name": "Test User"}


@pytest.fixture
def sample_task():
    """Fixture providing sample task data."""
    return {"id": 1, "type": "process", "payload": {"action": "test"}}
