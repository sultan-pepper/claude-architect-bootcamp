"""Background worker service."""

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Worker:
    """Background worker for processing tasks."""

    def __init__(self, name: str = "default"):
        """Initialize worker.

        Args:
            name: Worker name
        """
        self.name = name
        self.running = False
        self.tasks_processed = 0

    def start(self) -> None:
        """Start the worker."""
        self.running = True
        logger.info(f"Worker {self.name} started")

    def stop(self) -> None:
        """Stop the worker."""
        self.running = False
        logger.info(f"Worker {self.name} stopped")

    def process_task(self, task_id: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a single task.

        Args:
            task_id: Task identifier
            data: Task data

        Returns:
            Processing result
        """
        if not self.running:
            return {"status": "error", "message": "Worker not running"}

        logger.info(f"Processing task {task_id}")
        time.sleep(0.1)  # Simulate work

        self.tasks_processed += 1

        if data is None:
            data = {}

        return {
            "task_id": task_id,
            "status": "completed",
            "processed_count": self.tasks_processed,
            "data_length": len(data),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics.

        Returns:
            Worker statistics
        """
        return {
            "name": self.name,
            "running": self.running,
            "tasks_processed": self.tasks_processed,
        }
