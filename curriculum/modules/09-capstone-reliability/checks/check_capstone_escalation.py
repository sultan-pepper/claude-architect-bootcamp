"""Checks for module 09: capstone-reliability (escalation criteria)."""

import os
import sys

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c1_no_escalation_straightforward(ctx: CheckContext) -> CheckResult:
    """C1-no-escalation-straightforward: straightforward case doesn't escalate."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C1-no-escalation-straightforward",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §explicit_escalation_criteria"
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
                agent.run_scenario, "m9-straightforward-no-escalation", timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C1-no-escalation-straightforward",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C1-no-escalation-straightforward",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §explicit_escalation_criteria"
                )
            return CheckResult(
                name="C1-no-escalation-straightforward",
                passed=False,
                detail=f"Failed to run scenario: {e}",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )

        if "outcome" not in result:
            return CheckResult(
                name="C1-no-escalation-straightforward",
                passed=False,
                detail="No outcome in result",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )

        outcome = result["outcome"]
        if outcome.get("escalated") is not False:
            return CheckResult(
                name="C1-no-escalation-straightforward",
                passed=False,
                detail=f"Straightforward case should not escalate, but got escalated={outcome.get('escalated')}",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )

        return CheckResult(
            name="C1-no-escalation-straightforward",
            passed=True,
            detail="Straightforward case correctly does not escalate",
            lesson_ref="lesson.md §explicit_escalation_criteria"
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


def check_c2_policy_escalation(ctx: CheckContext) -> CheckResult:
    """C2-policy-escalation: Policy gap case escalates."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C2-policy-escalation",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §explicit_escalation_criteria"
        )

    sys.path.insert(0, str(ctx.fixtures))
    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)

    try:
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
        import agent
        import support_backend

        support_backend.ESCALATION_LOG = []
        try:
            result = call_with_timeout(
                agent.run_scenario, "m9-policy-gap-must-escalate", timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C2-policy-escalation",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C2-policy-escalation",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §explicit_escalation_criteria"
                )
            return CheckResult(
                name="C2-policy-escalation",
                passed=False,
                detail=f"Failed to run scenario: {e}",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )

        if "outcome" not in result:
            return CheckResult(
                name="C2-policy-escalation",
                passed=False,
                detail="No outcome in result",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )

        outcome = result["outcome"]
        if outcome.get("escalated") is not True:
            return CheckResult(
                name="C2-policy-escalation",
                passed=False,
                detail=f"Policy gap case should escalate, but got escalated={outcome.get('escalated')}",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )

        if not support_backend.ESCALATION_LOG:
            return CheckResult(
                name="C2-policy-escalation",
                passed=False,
                detail="ESCALATION_LOG is empty — escalation was not recorded",
                lesson_ref="lesson.md §explicit_escalation_criteria"
            )

        return CheckResult(
            name="C2-policy-escalation",
            passed=True,
            detail="Policy gap case correctly escalates",
            lesson_ref="lesson.md §explicit_escalation_criteria"
        )

    finally:
        sys.path.pop(0)
        sys.path.pop(0)
        if old_fixtures_path:
            os.environ["FIXTURES_PATH"] = old_fixtures_path
        else:
            os.environ.pop("FIXTURES_PATH", None)
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)


def check_c3_immediate_human_request(ctx: CheckContext) -> CheckResult:
    """C3-immediate-human-request: Explicit request escalates immediately."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C3-immediate-human-request",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §immediate_honor"
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
                agent.run_scenario, "m9-explicit-human-request", timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C3-immediate-human-request",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §immediate_honor"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C3-immediate-human-request",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §immediate_honor"
                )
            return CheckResult(
                name="C3-immediate-human-request",
                passed=False,
                detail=f"Failed to run scenario: {e}",
                lesson_ref="lesson.md §immediate_honor"
            )

        if "outcome" not in result:
            return CheckResult(
                name="C3-immediate-human-request",
                passed=False,
                detail="No outcome in result",
                lesson_ref="lesson.md §immediate_honor"
            )

        outcome = result["outcome"]
        if outcome.get("escalated") is not True:
            return CheckResult(
                name="C3-immediate-human-request",
                passed=False,
                detail=f"Explicit human request should escalate, but got escalated={outcome.get('escalated')}",
                lesson_ref="lesson.md §immediate_honor"
            )

        if "transcript" not in result:
            return CheckResult(
                name="C3-immediate-human-request",
                passed=False,
                detail="No transcript in result",
                lesson_ref="lesson.md §immediate_honor"
            )

        transcript = result["transcript"]
        first_tool_name = None
        for msg in transcript:
            if msg.get("role") == "assistant" and "content" in msg:
                content = msg.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            first_tool_name = block.get("name")
                            break
            if first_tool_name is not None:
                break

        if first_tool_name != "escalate_to_human":
            return CheckResult(
                name="C3-immediate-human-request",
                passed=False,
                detail=f"First tool should be escalate_to_human, but got {first_tool_name}",
                lesson_ref="lesson.md §immediate_honor"
            )

        return CheckResult(
            name="C3-immediate-human-request",
            passed=True,
            detail="Explicit human request immediately escalates",
            lesson_ref="lesson.md §immediate_honor"
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
