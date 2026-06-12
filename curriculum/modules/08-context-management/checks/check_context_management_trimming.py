"""Checks for module 08: context-management (trimming and handoff)."""

import json
import os
import sys
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c2_trimmed_tool_output(ctx: CheckContext) -> CheckResult:
    """C2-trimmed-tool-output: lookup_order result in transcript has fewer keys than raw."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C2-trimmed-tool-output",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §trimming_tool_outputs"
        )

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)

    try:
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
        import agent
        import support_backend

        # Get raw backend result
        try:
            raw_result = support_backend.lookup_order("O001")
        except Exception as e:
            return CheckResult(
                name="C2-trimmed-tool-output",
                passed=False,
                detail=f"Failed to get raw backend result: {e}",
                lesson_ref="lesson.md §trimming_tool_outputs"
            )

        raw_key_count = len(raw_result.keys())

        # Run agent to get transcript
        try:
            result = call_with_timeout(
                agent.run_conversation, ["I need help with order O001"], timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C2-trimmed-tool-output",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §trimming_tool_outputs"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C2-trimmed-tool-output",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §trimming_tool_outputs"
                )
            return CheckResult(
                name="C2-trimmed-tool-output",
                passed=False,
                detail=f"Failed to run agent: {e}",
                lesson_ref="lesson.md §trimming_tool_outputs"
            )

        if "transcript" not in result:
            return CheckResult(
                name="C2-trimmed-tool-output",
                passed=False,
                detail="No transcript in result",
                lesson_ref="lesson.md §trimming_tool_outputs"
            )

        transcript = result["transcript"]

        # Build a tool_use_id → tool_name map from assistant turns.
        # tool_result blocks carry no name — only tool_use blocks do.
        tool_id_to_name: dict[str, str] = {}
        for msg in transcript:
            if msg.get("role") == "assistant":
                content = msg.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            bid = block.get("id")
                            bname = block.get("name")
                            if bid and bname:
                                tool_id_to_name[bid] = bname

        # Find the lookup_order tool_result using the id→name map
        trimmed_result = None
        for msg in transcript:
            if msg.get("role") == "user" and "content" in msg:
                content = msg.get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            bid = block.get("tool_use_id")
                            if tool_id_to_name.get(bid) == "lookup_order":
                                raw_content = block.get("content", "{}")
                                try:
                                    if isinstance(raw_content, str):
                                        trimmed_result = json.loads(raw_content)
                                    elif isinstance(raw_content, list):
                                        for rb in raw_content:
                                            if (isinstance(rb, dict)
                                                    and rb.get("type") == "text"):
                                                trimmed_result = json.loads(
                                                    rb.get("text", "{}")
                                                )
                                                break
                                except json.JSONDecodeError:
                                    pass
                                break
            if trimmed_result is not None:
                break

        if trimmed_result is None:
            return CheckResult(
                name="C2-trimmed-tool-output",
                passed=False,
                detail="lookup_order tool_result not found in transcript",
                lesson_ref="lesson.md §trimming_tool_outputs"
            )

        trimmed_key_count = len(trimmed_result.keys())

        if trimmed_key_count >= raw_key_count:
            return CheckResult(
                name="C2-trimmed-tool-output",
                passed=False,
                detail=f"Trimmed result has {trimmed_key_count} keys, raw has {raw_key_count} — no trimming occurred",
                lesson_ref="lesson.md §trimming_tool_outputs"
            )

        return CheckResult(
            name="C2-trimmed-tool-output",
            passed=True,
            detail=f"lookup_order trimmed from {raw_key_count} keys to {trimmed_key_count}",
            lesson_ref="lesson.md §trimming_tool_outputs"
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


def check_c3_structured_handoff(ctx: CheckContext) -> CheckResult:
    """C3-structured-handoff: Escalation produces handoff with all required fields."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C3-structured-handoff",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §structured_handoff"
        )

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)

    try:
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
        import agent
        import support_backend

        # Reset logs
        support_backend.REFUND_LOG = []
        support_backend.ESCALATION_LOG = []

        # Run agent with escalation trigger (O004 refund request)
        try:
            result = call_with_timeout(
                agent.run_conversation,
                ["I need to return order O004 for a full refund. "
                 "There's a manufacturing defect."],
                timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C3-structured-handoff",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §structured_handoff"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C3-structured-handoff",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §structured_handoff"
                )
            return CheckResult(
                name="C3-structured-handoff",
                passed=False,
                detail=f"Failed to run agent: {e}",
                lesson_ref="lesson.md §structured_handoff"
            )

        if "handoff" not in result:
            return CheckResult(
                name="C3-structured-handoff",
                passed=False,
                detail="No 'handoff' key in result — escalation did not occur",
                lesson_ref="lesson.md §structured_handoff"
            )

        handoff = result["handoff"]

        if not isinstance(handoff, dict):
            return CheckResult(
                name="C3-structured-handoff",
                passed=False,
                detail=f"handoff is not a dict: {type(handoff)}",
                lesson_ref="lesson.md §structured_handoff"
            )

        required_fields = ["customer_id", "root_cause", "amount", "recommended_action"]
        for field in required_fields:
            if field not in handoff:
                return CheckResult(
                    name="C3-structured-handoff",
                    passed=False,
                    detail=f"handoff missing required field '{field}'",
                    lesson_ref="lesson.md §structured_handoff"
                )

            if handoff[field] is None:
                return CheckResult(
                    name="C3-structured-handoff",
                    passed=False,
                    detail=f"handoff field '{field}' is null",
                    lesson_ref="lesson.md §structured_handoff"
                )

            if not isinstance(handoff[field], (str, int, float)):
                return CheckResult(
                    name="C3-structured-handoff",
                    passed=False,
                    detail=f"handoff field '{field}' has unexpected type: {type(handoff[field])}",
                    lesson_ref="lesson.md §structured_handoff"
                )

        return CheckResult(
            name="C3-structured-handoff",
            passed=True,
            detail="Escalation produces properly structured handoff",
            lesson_ref="lesson.md §structured_handoff"
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
