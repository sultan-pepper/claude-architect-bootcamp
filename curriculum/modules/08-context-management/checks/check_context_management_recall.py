"""Checks for module 08: context-management (recall)."""

import json
import os
import sys
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c1_recall_amount(ctx: CheckContext) -> CheckResult:
    """C1-recall-amount: Turn 28 response contains "123.45"."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C1-recall-amount",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §persistent_facts_block"
        )

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)

    try:
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
        import agent

        # Load the conversation script
        conversations_path = ctx.fixtures / "conversations.json"
        if not conversations_path.exists():
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail="conversations.json not found in fixtures",
                lesson_ref="lesson.md §persistent_facts_block"
            )

        with open(conversations_path) as f:
            conversations = json.load(f)
        scripts = conversations["scripts"] if isinstance(conversations, dict) \
            else conversations

        # Find the m8-30-turns-3-issues script
        script = None
        for s in scripts:
            if s.get("id") == "m8-30-turns-3-issues":
                script = s
                break

        if script is None:
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail="m8-30-turns-3-issues script not found in conversations.json",
                lesson_ref="lesson.md §persistent_facts_block"
            )

        turns = script.get("turns", [])
        if len(turns) < 28:
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail=f"Script has only {len(turns)} turns, need at least 28",
                lesson_ref="lesson.md §persistent_facts_block"
            )

        # Build list of user messages
        user_messages = [t["user_message"] for t in turns]

        try:
            result = call_with_timeout(
                agent.run_conversation, user_messages, timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §persistent_facts_block"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C1-recall-amount",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §persistent_facts_block"
                )
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail=f"Failed to run conversation: {e}",
                lesson_ref="lesson.md §persistent_facts_block"
            )

        if "transcript" not in result:
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail="No transcript in result",
                lesson_ref="lesson.md §persistent_facts_block"
            )

        transcript = result["transcript"]

        # Find turn 28's assistant response
        user_turn_count = 0
        turn_28_response = None

        for msg in transcript:
            if msg.get("role") == "user":
                content = msg.get("content")
                # Check if this is a tool_result message (list) or a regular user message (string)
                if isinstance(content, str):
                    user_turn_count += 1
                    if user_turn_count == 28:
                        # Next assistant message is turn 28's response
                        # Find the next assistant message
                        idx = transcript.index(msg)
                        for i in range(idx + 1, len(transcript)):
                            if transcript[i].get("role") == "assistant":
                                turn_28_response = transcript[i]
                                break
                        break

        if turn_28_response is None:
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail="Could not find assistant response to turn 28",
                lesson_ref="lesson.md §persistent_facts_block"
            )

        # Check for "123.45" in the response
        response_content = turn_28_response.get("content", [])
        response_str = json.dumps(response_content)

        if "123.45" not in response_str:
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail="Turn 28 response does not contain '123.45'",
                lesson_ref="lesson.md §persistent_facts_block"
            )

        return CheckResult(
            name="C1-recall-amount",
            passed=True,
            detail="Turn 28 correctly recalls the $123.45 amount",
            lesson_ref="lesson.md §persistent_facts_block"
        )

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return CheckResult(
                name="C1-recall-amount",
                passed=False,
                detail="requires ANTHROPIC_API_KEY to run the learner agent",
                lesson_ref="lesson.md §persistent_facts_block"
            )
        return CheckResult(
            name="C1-recall-amount",
            passed=False,
            detail=f"Check crashed: {e}",
            lesson_ref="lesson.md §persistent_facts_block"
        )

    finally:
        sys.path.pop(0)
        if old_fixtures_path:
            os.environ["FIXTURES_PATH"] = old_fixtures_path
        else:
            os.environ.pop("FIXTURES_PATH", None)
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
