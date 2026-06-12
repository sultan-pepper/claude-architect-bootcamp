"""Shared utility functions."""

import json
from typing import Any, Dict


def parse_json(data: str) -> Dict[str, Any]:
    """Parse JSON string to dict.

    Args:
        data: JSON string

    Returns:
        Parsed dictionary
    """
    return json.loads(data)


def format_error(code: int, message: str) -> Dict[str, Any]:
    """Format an error response.

    Args:
        code: Error code
        message: Error message

    Returns:
        Formatted error dict
    """
    return {"error": True, "code": code, "message": message}


def validate_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    return "@" in email and "." in email.split("@")[1]


def calculate_total(items: list[float]) -> float:
    """Calculate sum of items.

    Args:
        items: List of numeric values

    Returns:
        Sum of all items
    """
    return sum(items)


def retry_exponential(func, max_retries: int = 3):
    """Decorator for exponential backoff retry.

    Args:
        func: Function to wrap
        max_retries: Maximum number of retries

    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        attempt = 0
        while attempt < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                if attempt >= max_retries:
                    raise
    return wrapper
