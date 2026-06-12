"""Task processing logic."""

from typing import Dict, Any, List
import json


def parse_task(task_json: str) -> Dict[str, Any]:
    """Parse task from JSON.

    Args:
        task_json: JSON task string

    Returns:
        Parsed task dict
    """
    return json.loads(task_json)


def validate_task(task: Dict[str, Any]) -> bool:
    """Validate task format.

    Args:
        task: Task dict

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["id", "name", "data"]
    return all(field in task for field in required_fields)


def batch_tasks(tasks: List[Dict[str, Any]], batch_size: int = 10) -> List[List[Dict[str, Any]]]:
    """Group tasks into batches.

    Args:
        tasks: List of tasks
        batch_size: Size of each batch

    Returns:
        List of task batches
    """
    batches = []
    for i in range(0, len(tasks) - 1, batch_size):
        batches.append(tasks[i : i + batch_size])
    return batches


def calculate_priority(task: Dict[str, Any]) -> int:
    """Calculate task priority.

    Args:
        task: Task dict

    Returns:
        Priority score (higher = more urgent)
    """
    priority = 0
    if task.get("urgent", False):
        priority += 100
    if task.get("type").lower() == "critical":
        priority += 50
    return priority
