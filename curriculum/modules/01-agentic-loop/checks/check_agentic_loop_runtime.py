"""Checks for module 01: agentic-loop — runtime criteria C2 and C4."""

import os
import sys
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c2_tool_result_appended(ctx: CheckContext) -> CheckResult:
    """C2-tool-result-appended: Verify tool_use blocks are followed by tool_result."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C2-tool-result-appended",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §tool_results"
        )

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)
    try:
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
        import agent

        try:
            result = call_with_timeout(
                agent.run_conversation, ["I need help with order O001"], timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C2-tool-result-appended",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §tool_results"
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return CheckResult(
                    name="C2-tool-result-appended",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §tool_results"
                )
            return CheckResult(
                name="C2-tool-result-appended",
                passed=False,
                detail=f"Failed to run agent: {e}",
                lesson_ref="lesson.md §tool_results"
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

    if "transcript" not in result:
        return CheckResult(
            name="C2-tool-result-appended",
            passed=False,
            detail="No transcript in result",
            lesson_ref="lesson.md §tool_results"
        )

    transcript = result["transcript"]

    i = 0
    while i < len(transcript):
        msg = transcript[i]

        if msg.get("role") == "assistant" and "content" in msg:
            content = msg["content"]
            if isinstance(content, list):
                tool_use_ids = set()
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_use_ids.add(block.get("id"))

                if tool_use_ids:
                    if i + 1 >= len(transcript):
                        return CheckResult(
                            name="C2-tool-result-appended",
                            passed=False,
                            detail=(
                                f"Assistant turn at index {i} has tool_use "
                                "blocks but no following user turn"
                            ),
                            lesson_ref="lesson.md §tool_results"
                        )

                    next_msg = transcript[i + 1]
                    if next_msg.get("role") != "user":
                        return CheckResult(
                            name="C2-tool-result-appended",
                            passed=False,
                            detail=f"Tool_use blocks at index {i} not followed by user message",
                            lesson_ref="lesson.md §tool_results"
                        )

                    next_content = next_msg.get("content", [])
                    if not isinstance(next_content, list):
                        return CheckResult(
                            name="C2-tool-result-appended",
                            passed=False,
                            detail=f"User message at index {i+1} has non-list content",
                            lesson_ref="lesson.md §tool_results"
                        )

                    result_ids = set()
                    for block in next_content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            result_ids.add(block.get("tool_use_id"))

                    if tool_use_ids != result_ids:
                        return CheckResult(
                            name="C2-tool-result-appended",
                            passed=False,
                            detail=(
                                f"Tool_use ids {tool_use_ids} do not match "
                                f"tool_result ids {result_ids}"
                            ),
                            lesson_ref="lesson.md §tool_results"
                        )

        i += 1

    saw_tool_use = any(
        isinstance(block, dict) and block.get("type") == "tool_use"
        for msg in transcript
        for block in (msg.get("content") if isinstance(msg.get("content"), list) else [])
    )
    if not saw_tool_use:
        return CheckResult(
            name="C2-tool-result-appended",
            passed=False,
            detail=(
                "No tool_use blocks observed in the transcript — "
                "the agent never called a tool"
            ),
            lesson_ref="lesson.md §tool_results"
        )

    return CheckResult(
        name="C2-tool-result-appended",
        passed=True,
        detail="All tool_use blocks are followed by matching tool_result blocks",
        lesson_ref="lesson.md §tool_results"
    )


def check_c4_multi_concern(ctx: CheckContext) -> CheckResult:
    """C4-multi-concern: Verify both concerns are addressed in response."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C4-multi-concern",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §model_driven_sequencing"
        )

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)
    try:
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
        import agent

        msg = (
            "Hi, I need to check on my refund for order O001, and also my address "
            "has changed. Can you help me update it? My new address is "
            "999 New Street, Portland, OR 97999."
        )
        try:
            result = call_with_timeout(
                agent.run_conversation, [msg], timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C4-multi-concern",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §model_driven_sequencing"
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return CheckResult(
                    name="C4-multi-concern",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §model_driven_sequencing"
                )
            return CheckResult(
                name="C4-multi-concern",
                passed=False,
                detail=f"Failed to run agent: {e}",
                lesson_ref="lesson.md §model_driven_sequencing"
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

    if "transcript" not in result:
        return CheckResult(
            name="C4-multi-concern",
            passed=False,
            detail="No transcript in result",
            lesson_ref="lesson.md §model_driven_sequencing"
        )

    transcript = result["transcript"]

    found_lookup_order = False
    found_other_tool = False

    for msg in transcript:
        if msg.get("role") == "assistant" and "content" in msg:
            content = msg["content"]
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        if tool_name == "lookup_order":
                            inputs = block.get("input", {})
                            if inputs.get("order_id") == "O001":
                                found_lookup_order = True
                        elif tool_name in [
                            "get_customer", "process_refund",
                            "escalate_to_human", "find_customers"
                        ]:
                            found_other_tool = True

    if not found_lookup_order:
        return CheckResult(
            name="C4-multi-concern",
            passed=False,
            detail="No lookup_order call found for order O001",
            lesson_ref="lesson.md §model_driven_sequencing"
        )

    if not found_other_tool:
        return CheckResult(
            name="C4-multi-concern",
            passed=False,
            detail="No other tool call found to address address-related concern",
            lesson_ref="lesson.md §model_driven_sequencing"
        )

    return CheckResult(
        name="C4-multi-concern",
        passed=True,
        detail="Both order lookup and address concern tools called",
        lesson_ref="lesson.md §model_driven_sequencing"
    )
