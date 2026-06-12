"""M01 — The agentic loop: customer-support agent skeleton.

Implement run_conversation() according to the contract in README.md.
Fill every TODO. Do not change the function signature or return shape.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Fixtures import — do not change this block
# ---------------------------------------------------------------------------
_fixtures_path = os.environ.get("FIXTURES_PATH", os.path.join(os.path.dirname(__file__), "..", "fixtures"))
sys.path.insert(0, str(_fixtures_path))
import support_backend  # noqa: E402  (inserted path above)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "claude-haiku-4-5"

# ---------------------------------------------------------------------------
# Tool schemas
# TODO: Define tool schemas for all five backend functions.
#       Each entry must have "name", "description", and "input_schema".
#       Write descriptions specific enough that the model routes correctly.
# ---------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    # TODO: get_customer
    # TODO: find_customers
    # TODO: lookup_order
    # TODO: process_refund
    # TODO: escalate_to_human
]


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------
def dispatch_tool(name: str, inputs: dict[str, Any]) -> Any:
    """Call the named backend function and return a JSON-serialisable result.

    TODO:
    - Map name to the corresponding support_backend function.
    - Call it with **inputs.
    - Catch support_backend.RefundError and return the error message string
      (do not re-raise; let the model inform the user).
    - Return the result (will be json.dumps'd by the caller).
    """
    # TODO: implement dispatch
    raise NotImplementedError("dispatch_tool not yet implemented")


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------
def run_conversation(user_messages: list[str]) -> dict[str, Any]:
    """Drive the agentic loop for a customer-support conversation.

    Args:
        user_messages: One or more user turn strings. For M01 checks, this
                       is always a single-element list.

    Returns:
        {
            "response": str,           # final assistant text
            "transcript": list[dict],  # full messages list, in order
        }

    TODO:
    - Initialise messages from user_messages.
    - Run the agentic loop: call the API, append the assistant turn,
      check stop_reason, dispatch tools and append tool_result turn,
      repeat until stop_reason == "end_turn".
    - Do NOT use text parsing or an iteration counter as the exit condition.
    - Return response text and full transcript.
    """
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()

    # TODO: build initial messages list from user_messages

    messages: list[dict[str, Any]] = []  # replace with your initialisation

    # TODO: implement the agentic loop

    # Placeholder — remove once implemented
    return {"response": "", "transcript": messages}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    raw = sys.stdin.read()
    turns: list[str] = json.loads(raw)
    result = run_conversation(turns)
    print(json.dumps(result))
