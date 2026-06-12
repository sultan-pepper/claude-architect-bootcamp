"""Output formatting helpers."""

import json
from typing import Any


def format_status_table(status_data: list[dict[str, Any]]) -> str:
    """Format status data as a table."""
    lines = []
    lines.append(f"{'ID':<4} {'Title':<40} {'Track':<6} {'State':<12} {'Checks':<8} {'Assisted':<8}")
    lines.append("-" * 80)

    for item in status_data:
        assisted_str = "yes" if item["assisted"] else "no"
        lines.append(
            f"{item['id']:<4} {item['title']:<40} {item['track']:<6} "
            f"{item['state']:<12} {item['check_summary']:<8} {assisted_str:<8}"
        )

    return "\n".join(lines)


def format_status_json(status_data: list[dict[str, Any]]) -> str:
    """Format status data as JSON."""
    return json.dumps(status_data, indent=2)


def format_check_results_json(results: list) -> str:
    """Format check results as JSON."""
    output = [
        {"name": r.name, "passed": r.passed, "detail": r.detail,
         "lesson_ref": r.lesson_ref}
        for r in results
    ]
    return json.dumps(output, indent=2)


def format_check_results_text(results: list) -> str:
    """Format check results as text."""
    lines = []
    for r in results:
        status_str = "PASS" if r.passed else "FAIL"
        lines.append(f"{status_str} {r.name} — {r.detail} ({r.lesson_ref})")
    return "\n".join(lines)
