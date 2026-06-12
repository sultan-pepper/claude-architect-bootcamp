"""Reference solution for M09: capstone-reliability agent.

Entry point: run_scenario(scenario_name) → dict
Shared helpers (tools, dispatch, normalisation) live in helpers.py.
"""

import anthropic
import json
import os
import sys
from pathlib import Path

from helpers import (
    BASE_SYSTEM, ESCALATION_CRITERIA, TOOLS,
    dispatch_tool,
)


def run_scenario(scenario_name: str) -> dict:
    """Run a scenario and return structured outcome."""
    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
    log_path = os.environ.get("AGENT_LOG_PATH")

    # Load scenario from fixtures
    fixtures_path = Path(os.environ.get("FIXTURES_PATH", "."))
    conversations_file = fixtures_path / "conversations.json"

    with open(conversations_file) as f:
        conversations = json.load(f)
    scripts = conversations["scripts"] if isinstance(conversations, dict) \
        else conversations

    scenario = next(
        (c for c in scripts if c.get("id") == scenario_name), None
    )
    if scenario is None:
        raise ValueError(f"Scenario {scenario_name} not found")

    turns = scenario.get("turns", [])

    # Track run state
    state = {
        "escalated": False,
        "clarification_asked": False,
        "successful_lookups": [],
        "failed_lookups": []
    }

    messages: list[dict] = []
    transcript: list[dict] = []
    main_conversation_messages: list[dict] = []

    for turn in turns:
        user_msg = turn.get("user_message")
        messages.append({"role": "user", "content": user_msg})
        transcript.append({"role": "user", "content": user_msg})
        main_conversation_messages.append({"role": "user", "content": user_msg})

        while True:
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=BASE_SYSTEM,
                tools=TOOLS,
                messages=messages
            )

            if response.stop_reason == "end_turn":
                content_dicts = [b.model_dump() for b in response.content]
                messages.append({"role": "assistant", "content": content_dicts})
                transcript.append({"role": "assistant", "content": content_dicts})
                main_conversation_messages.append(
                    {"role": "assistant", "content": content_dicts}
                )
                break

            if response.stop_reason == "tool_use":
                content_dicts = [b.model_dump() for b in response.content]
                messages.append({"role": "assistant", "content": content_dicts})
                transcript.append({"role": "assistant", "content": content_dicts})
                main_conversation_messages.append(
                    {"role": "assistant", "content": content_dicts}
                )

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_result = dispatch_tool(block.name, block.input, state)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result,
                            "name": block.name
                        })

                messages.append({"role": "user", "content": tool_results})
                transcript.append({"role": "user", "content": tool_results})
                main_conversation_messages.append(
                    {"role": "user", "content": tool_results}
                )
                continue

    # Build partial-results annotation
    partial_results = None
    if state["failed_lookups"]:
        partial_results = {
            "successful": state["successful_lookups"],
            "failed": state["failed_lookups"],
            "coverage": "partial"
        }
    elif state["successful_lookups"]:
        partial_results = {
            "successful": state["successful_lookups"],
            "failed": [],
            "coverage": "full"
        }

    # Independent self-evaluation call
    eval_messages = [{
        "role": "user",
        "content": (
            f"Evaluate this support interaction against the escalation criteria:\n\n"
            f"{ESCALATION_CRITERIA}\n\n"
            f"Transcript:\n{json.dumps(transcript, indent=2)}\n\n"
            f"Outcome:\n{json.dumps({'escalated': state['escalated'], 'clarification_asked': state['clarification_asked'], 'partial_results': partial_results})}\n\n"
            f"Verdict: PASS or FAIL. Explain."
        )
    }]

    eval_response = client.messages.create(
        model=model,
        max_tokens=512,
        messages=eval_messages
    )

    eval_text = "".join(
        b.text for b in eval_response.content if hasattr(b, "text")
    )
    verdict = "PASS" if "PASS" in eval_text else "FAIL"

    outcome = {
        "escalated": state["escalated"],
        "clarification_asked": state["clarification_asked"],
        "partial_results": partial_results,
        "self_eval": {"verdict": verdict, "reasoning": eval_text}
    }

    result = {"transcript": transcript, "outcome": outcome}

    if log_path:
        log_data = [
            {"role": "main_conversation", "messages": main_conversation_messages},
            {"role": "self_eval", "messages": eval_messages}
        ]
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

    return result


if __name__ == "__main__":
    scenario_name = sys.argv[1] if len(sys.argv) > 1 else "m9-straightforward-no-escalation"
    result = run_scenario(scenario_name)
    print(json.dumps(result, indent=2))
