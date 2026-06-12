"""Checks for module 09: capstone-reliability (clarification and partial results)."""

import json
import os
import sys
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c4_clarification_on_ambiguity(ctx: CheckContext) -> CheckResult:
    """C4-clarification-on-ambiguity: Ambiguous identity asks for clarification."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C4-clarification-on-ambiguity",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §clarify_on_multiple_matches"
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
                agent.run_scenario, "m9-ambiguous-identity-alex-rivera", timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C4-clarification-on-ambiguity",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §clarify_on_multiple_matches"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C4-clarification-on-ambiguity",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §clarify_on_multiple_matches"
                )
            return CheckResult(
                name="C4-clarification-on-ambiguity",
                passed=False,
                detail=f"Failed to run scenario: {e}",
                lesson_ref="lesson.md §clarify_on_multiple_matches"
            )

        if "outcome" not in result:
            return CheckResult(
                name="C4-clarification-on-ambiguity",
                passed=False,
                detail="No outcome in result",
                lesson_ref="lesson.md §clarify_on_multiple_matches"
            )

        outcome = result["outcome"]
        if outcome.get("clarification_asked") is not True:
            return CheckResult(
                name="C4-clarification-on-ambiguity",
                passed=False,
                detail=f"Ambiguous identity should ask for clarification, but got clarification_asked={outcome.get('clarification_asked')}",
                lesson_ref="lesson.md §clarify_on_multiple_matches"
            )

        # Check transcript: after find_customers in turn 1, no get_customer, lookup_order, or process_refund
        if "transcript" not in result:
            return CheckResult(
                name="C4-clarification-on-ambiguity",
                passed=False,
                detail="No transcript in result",
                lesson_ref="lesson.md §clarify_on_multiple_matches"
            )

        transcript = result["transcript"]

        # Find find_customers in turn 1 (first assistant message)
        find_customers_idx = None
        turn_1_assistant_idx = None

        for i, msg in enumerate(transcript):
            if msg.get("role") == "assistant" and turn_1_assistant_idx is None:
                turn_1_assistant_idx = i
                content = msg.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            if block.get("name") == "find_customers":
                                find_customers_idx = i
                break

        if find_customers_idx is None:
            return CheckResult(
                name="C4-clarification-on-ambiguity",
                passed=False,
                detail="find_customers not found in turn 1 assistant message",
                lesson_ref="lesson.md §clarify_on_multiple_matches"
            )

        # Check the assistant turn after find_customers for forbidden tools
        # The next assistant turn after the tool_result for find_customers
        next_assistant_idx = None
        for i in range(find_customers_idx + 1, len(transcript)):
            if transcript[i].get("role") == "assistant":
                next_assistant_idx = i
                break

        if next_assistant_idx is None:
            # No next assistant turn — which is actually fine (clarification was asked)
            return CheckResult(
                name="C4-clarification-on-ambiguity",
                passed=True,
                detail="Ambiguous identity correctly asks for clarification",
                lesson_ref="lesson.md §clarify_on_multiple_matches"
            )

        next_assistant_msg = transcript[next_assistant_idx]
        content = next_assistant_msg.get("content", [])

        forbidden_tools = {"get_customer", "lookup_order", "process_refund"}
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_name = block.get("name")
                if tool_name in forbidden_tools:
                    return CheckResult(
                        name="C4-clarification-on-ambiguity",
                        passed=False,
                        detail=f"After find_customers returns multiple results, agent should not call {tool_name}",
                        lesson_ref="lesson.md §clarify_on_multiple_matches"
                    )

        return CheckResult(
            name="C4-clarification-on-ambiguity",
            passed=True,
            detail="Ambiguous identity correctly asks for clarification without acting",
            lesson_ref="lesson.md §clarify_on_multiple_matches"
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


def check_c5_partial_results(ctx: CheckContext) -> CheckResult:
    """C5-partial-results: Timeout scenario has structured partial results."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C5-partial-results",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §structured_error_propagation"
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
                agent.run_scenario, "m9-subagent-timeout-simulation", timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §structured_error_propagation"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C5-partial-results",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §structured_error_propagation"
                )
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail=f"Failed to run scenario: {e}",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        if "outcome" not in result:
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail="No outcome in result",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        outcome = result["outcome"]
        partial_results = outcome.get("partial_results")

        if partial_results is None:
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail="partial_results should be non-null, got null",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        if not isinstance(partial_results, dict):
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail=f"partial_results should be dict, got {type(partial_results)}",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        # Check required fields
        if "successful" not in partial_results:
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail="partial_results missing 'successful' field",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        if "failed" not in partial_results:
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail="partial_results missing 'failed' field",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        if "coverage" not in partial_results:
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail="partial_results missing 'coverage' field",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        # Check that failed is non-empty
        failed = partial_results.get("failed", [])
        if not isinstance(failed, list) or len(failed) == 0:
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail=f"'failed' list should be non-empty, got {failed}",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        # Check coverage is "partial"
        coverage = partial_results.get("coverage")
        if coverage != "partial":
            return CheckResult(
                name="C5-partial-results",
                passed=False,
                detail=f"coverage should be 'partial', got {repr(coverage)}",
                lesson_ref="lesson.md §structured_error_propagation"
            )

        return CheckResult(
            name="C5-partial-results",
            passed=True,
            detail="Timeout scenario correctly reports partial results",
            lesson_ref="lesson.md §structured_error_propagation"
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
