"""M08 — Context management: extended customer-support agent skeleton.

Start from your M03 agent.py — copy it here and add the three changes described
in lab.md: persistent case_facts block, trimmed tool outputs, structured handoff.

Fill every TODO. Do not change run_conversation's signature or return shape.
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
import support_backend  # noqa: E402

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "claude-haiku-4-5"

# ---------------------------------------------------------------------------
# Tool schemas — copy from M03; no changes needed
# ---------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    # TODO: copy your M03 tool schemas here (get_customer, find_customers,
    #       lookup_order, process_refund, escalate_to_human)
]

# ---------------------------------------------------------------------------
# Field whitelist for trimming lookup_order results
# TODO: Define the set of fields to retain from the raw lookup_order dict.
#       The raw result has 40+ fields. Keep only what a support agent needs.
#       The trimmed key count must be strictly less than the raw key count.
# ---------------------------------------------------------------------------
KEEP_ORDER_FIELDS: set[str] = {
    # TODO: add field names here (e.g., "order_id", "status", "total", ...)
}


def trim_order(raw: dict[str, Any]) -> dict[str, Any]:
    """Return only the fields in KEEP_ORDER_FIELDS from a raw order dict."""
    # TODO: implement trimming
    return raw  # replace with filtered dict


# ---------------------------------------------------------------------------
# Hooks (from M03)
# ---------------------------------------------------------------------------
def pre_tool_use(
    name: str,
    inputs: dict[str, Any],
    case_facts: dict[str, Any],
    handoff_container: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """PreToolUse hook.

    TODO (M03 behaviour, preserved):
    - For process_refund with amount > 500.0: redirect to escalate_to_human.
      Return the escalation result as a tool_result content string.

    TODO (M08 addition):
    - When redirecting, also build a handoff dict and append it to
      handoff_container (a single-element list acting as a mutable output):
        {
            "customer_id": case_facts.get("customer_id"),
            "root_cause": f"Refund of ${amount} exceeds $500 policy cap",
            "amount": amount,
            "recommended_action": "Escalate to supervisor for refund exception approval",
        }
    - Return None to allow the tool call to proceed normally.
    """
    # TODO: implement pre-tool-use hook
    return None


def post_tool_use(name: str, result: Any) -> Any:
    """PostToolUse hook.

    TODO (M03 behaviour, preserved):
    - Convert Unix-epoch integer timestamps in date-keyed fields to ISO-8601.
    - Normalise status field values to title-case.
    - Recurse into nested dicts and lists.

    TODO (M08 addition):
    - For lookup_order results: apply trim_order() before returning.
      The trimming happens after normalisation.
    """
    # TODO: implement post-tool-use hook (normalise + trim)
    return result


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------
def dispatch_tool(
    name: str,
    inputs: dict[str, Any],
    case_facts: dict[str, Any],
    handoff_container: list[dict[str, Any]],
) -> str:
    """Call the backend function and return a JSON-serialised tool result.

    TODO:
    - Call pre_tool_use; if it returns a non-None value, return that as the
      tool result string (the actual backend function is not called).
    - Otherwise: call the backend function via a dispatch dict.
    - Pass the result through post_tool_use.
    - Return json.dumps of the processed result.
    - Catch support_backend.RefundError and return the error message as a string.
    """
    # TODO: implement dispatch
    raise NotImplementedError("dispatch_tool not yet implemented")


# ---------------------------------------------------------------------------
# Persistent case facts
# ---------------------------------------------------------------------------
def update_case_facts(
    case_facts: dict[str, Any],
    tool_name: str,
    tool_result_obj: Any,
    user_text: str,
) -> None:
    """Update case_facts from tool results and user messages.

    TODO:
    - When lookup_order returns a result, extract the customer_id from the
      order if available and store in case_facts["customer_id"].
    - When get_customer returns a result, store the customer_id.
    - When a confirmed amount is established (the checker drives this via
      conversation content), store it in case_facts["confirmed_amounts"].
    """
    # TODO: implement case fact extraction
    pass


def build_system(base_system: str, case_facts: dict[str, Any]) -> str:
    """Build the system prompt with injected case facts.

    TODO:
    - Append EXTRA_SYSTEM_PROMPT (from os.environ, default empty) to base_system.
    - Append a section containing json.dumps(case_facts) so the model always
      has current case facts at the top of context.
    """
    extra = os.environ.get("EXTRA_SYSTEM_PROMPT", "")
    # TODO: append case_facts section and extra system prompt
    return base_system


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------
BASE_SYSTEM = """You are a customer support agent. Help customers with their orders.
Be concise and accurate. When you recall a specific amount a customer mentioned,
state it exactly as they stated it."""


def run_conversation(user_messages: list[str]) -> dict[str, Any]:
    """Drive the agentic loop for a customer-support conversation.

    Args:
        user_messages: One or more user turn strings.

    Returns:
        {
            "response": str,           # final assistant text
            "transcript": list[dict],  # full messages list, in order
            "handoff": dict,           # present only when escalation occurs
        }

    TODO:
    - Initialise case_facts and handoff_container (a list to capture handoff
      data from the hook — use a list so the hook can write to it).
    - Build initial messages from user_messages.
    - Run the agentic loop: on each iteration, call build_system to inject
      current case_facts into the system prompt. After each tool result,
      call update_case_facts.
    - After the loop: if handoff_container is non-empty, include
      handoff_container[0] as the "handoff" key in the return dict.
    """
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()

    case_facts: dict[str, Any] = {
        "customer_id": None,
        "confirmed_amounts": {},
        "root_cause": None,
    }
    handoff_container: list[dict[str, Any]] = []

    messages: list[dict[str, Any]] = []
    # TODO: build initial messages from user_messages

    # TODO: implement the agentic loop (same structure as M01/M03, but:
    #   - rebuild system prompt each iteration using build_system
    #   - pass case_facts and handoff_container to dispatch_tool
    #   - call update_case_facts after each tool result)

    # Placeholder — remove once implemented
    result: dict[str, Any] = {"response": "", "transcript": messages}
    if handoff_container:
        result["handoff"] = handoff_container[0]
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    raw = sys.stdin.read()
    turns: list[str] = json.loads(raw)
    output = run_conversation(turns)
    print(json.dumps(output))
