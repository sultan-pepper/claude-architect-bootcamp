"""Main API service application."""

import sys
import logging
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, "/app/src")

from shared.utils import validate_email, format_error, parse_json

logger = logging.getLogger(__name__)


class APIServer:
    """Simple API server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """Initialize API server.

        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.running = False
        self.requests_handled = 0
        self.log_file = open("/tmp/api.log", "w")

    def start(self) -> None:
        """Start the API server."""
        self.running = True
        logger.info(f"API server started on {self.host}:{self.port}")

    def stop(self) -> None:
        """Stop the API server."""
        self.running = False
        logger.info("API server stopped")

    def handle_request(self, method: str, path: str, body: Optional[str] = None) -> Dict[str, Any]:
        """Handle incoming request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body

        Returns:
            Response dict
        """
        if not self.running:
            return format_error(503, "Server not running")

        self.requests_handled += 1

        if path == "/health":
            return {"status": "healthy", "requests": self.requests_handled}

        if path == "/users" and method == "POST":
            if body is None:
                return format_error(400, "Missing request body")
            try:
                user_data = parse_json(body)
                if not validate_email(user_data.get("email", "")):
                    return format_error(400, "Invalid email format")
                return {"id": 1, "email": user_data["email"], "created": True}
            except Exception as e:
                pass

        return format_error(404, "Not found")


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    server = APIServer()
    server.start()
    return server


if __name__ == "__main__":
    main()
