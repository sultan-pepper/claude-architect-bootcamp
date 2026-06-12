"""M03 — Hooks and lifecycle: agent skeleton with hook stubs.

Extends the M01 agentic loop with PreToolUse and PostToolUse hooks.
Fill every TODO. Do not change run_conversation's signature or return shape.

You can also copy your completed M01 agent.py here instead of using this
skeleton — just add the hook functions described in lab.md.
"""

from __future__ import annotations

import datetime
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
import support_backend  # noqa: E402

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "claude-haiku-4-5"

# ---------------------------------------------------------------------------
# Tool schemas — same five tools as M01
# TODO: paste or re-implement your M01 TOOLS list here.
# ---------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    # TODO: get_customer
    # TODO: find_customers
    # TODO: lookup_order
    # TODO: process_refund
    # TODO: escalate_to_human
]


# ---------------------------------------------------------------------------
# PostToolUse — result normalisation
# ---------------------------------------------------------------------------
def normalise_result(value: Any, key: str = "") -> Any:
    """Normalise a backend result value before it reaches the model.

    TODO:
    - If value is a dict: recurse, passing the key for each child.
    - If value is a list: recurse over items.
    - If value is an int and key indicates a date field (key ends with "_date"
      or key == "timestamp"): convert from Unix-epoch to ISO-8601 UTC string
      using datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc).isoformat().
    - If key == "status" and value is a str: return value.capitalize().
    - Otherwise: return value unchanged.
    """
    # TODO: implement
    return value  # placeholder — remove once implemented


# ---------------------------------------------------------------------------
# PreToolUse — policy enforcement
# ---------------------------------------------------------------------------
def pre_tool_use(name: str, inputs: dict[str, Any]) -> Any | None:
    """Intercept tool calls before they reach the backend.

    Returns a result dict to short-circuit the call, or None to allow it.

    TODO:
    - If name == "process_refund" and inputs["amount"] > 500.0:
        * Build a case summary string with order_id and amount.
        * Call support_backend.escalate_to_human(summary).
        * Return the escalation result.
        * Do NOT call support_backend.process_refund.
    - For all other calls: return None.
    """
    # TODO: implement
    return None  # placeholder — allows all calls; replace with actual logic


# ---------------------------------------------------------------------------
# Tool dispatch (with hooks)
# ---------------------------------------------------------------------------
def dispatch_tool(name: str, inputs: dict[str, Any]) -> Any:
    """Dispatch a tool call through the hook pipeline.

    Order of operations:
    1. Call pre_tool_use — if it returns non-None, return that result.
    2. Call the backend function.
    3. Catch support_backend.RefundError — return the error message string.
    4. Call normalise_result on the return value.
    5. Return the normalised result.

    TODO: implement using pre_tool_use and normalise_result defined above.
    """
    # TODO: implement
    raise NotImplementedError("dispatch_tool not yet implemented")


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------
def run_conversation(user_messages: list[str]) -> dict[str, Any]:
    """Drive the agentic loop with hooks active.

    Same contract as M01. Additionally:
    - Reads EXTRA_SYSTEM_PROMPT from os.environ at call time (not import time).
    - Appends it to the base system prompt if non-empty.
    - All tool results in the transcript reflect normalised (post-hook) data.

    TODO:
    - Build system prompt from base + EXTRA_SYSTEM_PROMPT.
    - Run the standard M01 agentic loop using dispatch_tool (which applies hooks).
    - Return {"response": final_text, "transcript": messages}.
    """
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()

    # Read EXTRA_SYSTEM_PROMPT at call time — not at module load
    extra_system = os.environ.get("EXTRA_SYSTEM_PROMPT", "")
    base_system = "You are a helpful customer support agent."  # TODO: expand as needed
    system_prompt = base_system + ("\n\n" + extra_system if extra_system else "")

    # TODO: build initial messages list from user_messages
    messages: list[dict[str, Any]] = []

    # TODO: implement the agentic loop (same structure as M01)
    # Use dispatch_tool (above) for all tool calls — hooks apply automatically.

    return {"response": "", "transcript": messages}  # placeholder


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    raw = sys.stdin.read()
    turns: list[str] = json.loads(raw)
    result = run_conversation(turns)
    print(json.dumps(result))
