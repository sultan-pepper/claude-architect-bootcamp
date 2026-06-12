"""Tests for shared utility functions."""

import sys
sys.path.insert(0, "/app/src")

from shared.utils import validate_email, calculate_total, parse_json, format_error


def test_validate_email():
    """Test email validation."""
    assert validate_email("test@example.com") is True
    assert validate_email("invalid") is False
    assert validate_email("@example.com") is True  # Minimal but valid


def test_calculate_total():
    """Test total calculation."""
    assert calculate_total([1.0, 2.0, 3.0]) == 6.0
    assert calculate_total([]) == 0.0
    assert calculate_total([10.5, 20.3]) == 30.8


def test_parse_json():
    """Test JSON parsing."""
    result = parse_json('{"key": "value"}')
    assert result["key"] == "value"


def test_format_error():
    """Test error formatting."""
    error = format_error(500, "Server error")
    assert error["error"] is True
    assert error["code"] == 500
    assert error["message"] == "Server error"
