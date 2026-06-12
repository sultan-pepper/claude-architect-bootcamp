"""M09 — Capstone: escalation & reliability agent skeleton.

Implement run_scenario() according to the contract in README.md and lab.md.
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
import support_backend  # noqa: E402

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "claude-haiku-4-5"

# ---------------------------------------------------------------------------
# Escalation criteria — embedded in the system prompt
# TODO: Write a closed list of escalation criteria with few-shot examples.
#       Must include:
#       1. Refund > $500 → escalate.
#       2. Explicit human request → escalate IMMEDIATELY (first tool call, no others before).
#       3. Requires authority beyond tools → escalate.
#       Include negative examples: frustration, bad order ID, recoverable errors.
#       Include at least 4 few-shot examples (2 escalate, 2 do not).
# ---------------------------------------------------------------------------
ESCALATION_CRITERIA = """
# TODO: write escalation criteria here
"""

BASE_SYSTEM = f"""You are a customer support agent. Help customers with their orders accurately and efficiently.

{ESCALATION_CRITERIA}
"""

# ---------------------------------------------------------------------------
# Tool schemas
# TODO: copy your M01/M03/M08 tool schemas here.
# ---------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    # TODO: get_customer, find_customers, lookup_order, process_refund, escalate_to_human
]

# ---------------------------------------------------------------------------
# Field whitelist for trimming lookup_order results (from M08)
# ---------------------------------------------------------------------------
KEEP_ORDER_FIELDS: set[str] = {
    # TODO: copy from M08
}


def trim_order(raw: dict[str, Any]) -> dict[str, Any]:
    """Return only KEEP_ORDER_FIELDS from a raw order dict."""
    # TODO: implement
    return raw


# ---------------------------------------------------------------------------
# Tool dispatch with state tracking
# ---------------------------------------------------------------------------
def dispatch_tool(
    name: str,
    inputs: dict[str, Any],
    state: dict[str, Any],
) -> str:
    """Call the named backend function and return a JSON-serialised result.

    `state` is a mutable dict shared across the full scenario run:
        {
            "escalated": bool,
            "clarification_asked": bool,
            "successful_lookups": list[str],
            "failed_lookups": list[str],
        }

    TODO:
    - If name == "find_customers" and len(result) > 1:
        Set state["clarification_asked"] = True.
        Return the result (the agent must then ask for clarification, not call
        another account tool — enforce this via the system prompt).
    - If name == "lookup_order":
        Wrap in try/except KeyError. On success, append order_id to
        state["successful_lookups"] and apply trim_order. On KeyError,
        append order_id to state["failed_lookups"] and return an error string.
    - If name == "process_refund" and inputs["amount"] > 500.0:
        Call escalate_to_human instead. Set state["escalated"] = True.
        Return the escalation result.
    - If name == "escalate_to_human":
        Set state["escalated"] = True. Call the backend normally.
    - For all other tools: call backend normally.
    - Apply trim_order to lookup_order results before serialising.
    - Catch support_backend.RefundError and return the error message string.
    """
    # TODO: implement dispatch with state tracking
    raise NotImplementedError("dispatch_tool not yet implemented")


# ---------------------------------------------------------------------------
# Self-evaluation (independent API call)
# ---------------------------------------------------------------------------
def self_evaluate(
    transcript: list[dict[str, Any]],
    outcome_without_self_eval: dict[str, Any],
    model: str,
    client: anthropic.Anthropic,
) -> dict[str, str]:
    """Evaluate the main transcript against escalation criteria.

    This MUST be a separate API call with a fresh message history — no messages
    from the main conversation. Return {"verdict": "PASS"|"FAIL", "reasoning": str}.

    TODO:
    - Build eval_messages as a new list (do NOT reference or copy the main messages).
    - The user message should include ESCALATION_CRITERIA, the transcript as JSON,
      the outcome dict, and instructions to return a verdict and reasoning.
    - Call client.messages.create with eval_messages and a separate max_tokens.
    - Parse the response text for "PASS" or "FAIL"; put full response in reasoning.
    - If AGENT_LOG_PATH is set, you will log this separately in run_scenario.
    """
    # TODO: implement self-evaluation
    raise NotImplementedError("self_evaluate not yet implemented")


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------
def load_scenario(scenario_name: str, fixtures_path: str) -> list[dict[str, Any]]:
    """Load the named scenario's turns from conversations.json."""
    conversations_path = os.path.join(fixtures_path, "conversations.json")
    with open(conversations_path, encoding="utf-8") as fh:
        data = json.load(fh)
    for script in data["scripts"]:
        if script["id"] == scenario_name:
            return script["turns"]
    raise ValueError(f"Unknown scenario: {scenario_name!r}")


def run_scenario(scenario_name: str) -> dict[str, Any]:
    """Run the named scenario and return the structured result.

    Args:
        scenario_name: One of the m9-* scenario IDs.

    Returns:
        {
            "transcript": list[dict],  # full messages across all turns
            "outcome": {
                "escalated": bool,
                "clarification_asked": bool,
                "partial_results": dict | None,
                "self_eval": {"verdict": str, "reasoning": str},
            }
        }

    TODO:
    - Read ANTHROPIC_MODEL, FIXTURES_PATH, AGENT_LOG_PATH from os.environ.
    - Load the scenario turns from conversations.json.
    - Initialise state dict.
    - Initialise messages = [] (the full conversation history).
    - For each turn in the scenario:
        Append the turn's user_message as a user turn to messages.
        Run the agentic loop until stop_reason == "end_turn" for this turn.
        (The agentic loop drives tool calls and appends results; the outer loop
        advances to the next script turn.)
    - After all turns: build outcome dict from state.
    - Compute partial_results from state["successful_lookups"] and
      state["failed_lookups"]: null if no failures, a dict with coverage
      annotation if any failures exist.
    - Call self_evaluate() for outcome["self_eval"].
    - If AGENT_LOG_PATH is set, write the log with two entries:
        [
          {"role": "main_conversation", "messages": <main messages list>},
          {"role": "self_eval",         "messages": <eval_messages list>}
        ]
      (Pass eval_messages out of self_evaluate so you can log it here, or
       have self_evaluate accept a log_container list and write to it.)
    - Return {"transcript": messages, "outcome": outcome}.
    """
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    fixtures_path = os.environ.get("FIXTURES_PATH",
                                   os.path.join(os.path.dirname(__file__), "..", "fixtures"))
    log_path = os.environ.get("AGENT_LOG_PATH")
    client = anthropic.Anthropic()

    turns = load_scenario(scenario_name, fixtures_path)

    state: dict[str, Any] = {
        "escalated": False,
        "clarification_asked": False,
        "successful_lookups": [],
        "failed_lookups": [],
    }

    messages: list[dict[str, Any]] = []

    # TODO: iterate over turns, run agentic loop for each turn

    # TODO: build partial_results from state

    partial_results = None  # replace with computed value

    # TODO: call self_evaluate
    self_eval: dict[str, str] = {"verdict": "PASS", "reasoning": ""}  # replace

    outcome: dict[str, Any] = {
        "escalated": state["escalated"],
        "clarification_asked": state["clarification_asked"],
        "partial_results": partial_results,
        "self_eval": self_eval,
    }

    # TODO: write AGENT_LOG_PATH log if set

    return {"transcript": messages, "outcome": outcome}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python agent.py <scenario_name>", file=sys.stderr)
        sys.exit(2)
    result = run_scenario(sys.argv[1])
    print(json.dumps(result, indent=2))
