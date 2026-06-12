"""Checks for module 09: capstone-reliability (self-evaluation)."""

import json
import os
import sys
import tempfile
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c6_self_eval_independent(ctx: CheckContext) -> CheckResult:
    """C6-self-eval-independent: Self-eval is separate from main conversation."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C6-self-eval-independent",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §independent_self_evaluation"
        )

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    old_agent_log_path = os.environ.get("AGENT_LOG_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)

    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            log_path = f.name

        os.environ["AGENT_LOG_PATH"] = log_path

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
                name="C6-self-eval-independent",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §independent_self_evaluation"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C6-self-eval-independent",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §independent_self_evaluation"
                )
            return CheckResult(
                name="C6-self-eval-independent",
                passed=False,
                detail=f"Failed to run scenario: {e}",
                lesson_ref="lesson.md §independent_self_evaluation"
            )

        # Check log file
        if not os.path.exists(log_path):
            return CheckResult(
                name="C6-self-eval-independent",
                passed=False,
                detail="AGENT_LOG_PATH file was not created",
                lesson_ref="lesson.md §independent_self_evaluation"
            )

        try:
            with open(log_path) as f:
                log_data = json.load(f)
        except Exception as e:
            return CheckResult(
                name="C6-self-eval-independent",
                passed=False,
                detail=f"Failed to parse AGENT_LOG_PATH: {e}",
                lesson_ref="lesson.md §independent_self_evaluation"
            )

        if not isinstance(log_data, list) or len(log_data) < 2:
            return CheckResult(
                name="C6-self-eval-independent",
                passed=False,
                detail=f"Log should have ≥2 entries, got {len(log_data) if isinstance(log_data, list) else 'not a list'}",
                lesson_ref="lesson.md §independent_self_evaluation"
            )

        # Find main_conversation and self_eval entries
        main_entry = None
        eval_entry = None

        for entry in log_data:
            if isinstance(entry, dict):
                role = entry.get("role")
                if role == "main_conversation":
                    main_entry = entry
                elif role == "self_eval":
                    eval_entry = entry

        if main_entry is None or eval_entry is None:
            return CheckResult(
                name="C6-self-eval-independent",
                passed=False,
                detail="Log missing 'main_conversation' or 'self_eval' entry",
                lesson_ref="lesson.md §independent_self_evaluation"
            )

        main_messages = main_entry.get("messages", [])
        eval_messages = eval_entry.get("messages", [])

        if not isinstance(main_messages, list) or not isinstance(eval_messages, list):
            return CheckResult(
                name="C6-self-eval-independent",
                passed=False,
                detail="messages should be lists",
                lesson_ref="lesson.md §independent_self_evaluation"
            )

        # Check that no message from eval appears in main
        for eval_msg in eval_messages:
            if eval_msg in main_messages:
                return CheckResult(
                    name="C6-self-eval-independent",
                    passed=False,
                    detail="Self-eval messages are shared with main conversation",
                    lesson_ref="lesson.md §independent_self_evaluation"
                )

        return CheckResult(
            name="C6-self-eval-independent",
            passed=True,
            detail="Self-eval is independent from main conversation",
            lesson_ref="lesson.md §independent_self_evaluation"
        )

    finally:
        sys.path.pop(0)
        if old_fixtures_path:
            os.environ["FIXTURES_PATH"] = old_fixtures_path
        else:
            os.environ.pop("FIXTURES_PATH", None)

        if old_agent_log_path is not None:
            os.environ["AGENT_LOG_PATH"] = old_agent_log_path
        else:
            os.environ.pop("AGENT_LOG_PATH", None)

        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)

        if os.path.exists(log_path):
            os.unlink(log_path)
