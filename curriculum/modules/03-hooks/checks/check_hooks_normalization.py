"""Checks for module 03: hooks — normalization criteria C3 and C4."""

import importlib.util
import json
import os
import sys
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout

# Load shared helpers from sibling (non-check) module
_spec = importlib.util.spec_from_file_location(
    "m03_hooks_helpers", str(Path(__file__).parent / "hooks_helpers.py")
)
assert _spec is not None and _spec.loader is not None
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)

_reset_backend_logs = _helpers.reset_backend_logs
_has_unix_epoch_in_date_field = _helpers.has_unix_epoch_in_date_field
_check_status_case = _helpers.check_status_case


def check_c3_timestamps_normalized(ctx: CheckContext) -> CheckResult:
    """C3-timestamps-normalized: All date fields are ISO-8601, not Unix-epoch."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C3-timestamps-normalized",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §post_tool_use"
        )

    _reset_backend_logs(ctx)

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)
    try:
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
        import agent

        msg = "Can you look up order O002 for me?"
        try:
            result = call_with_timeout(
                agent.run_conversation, [msg], timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C3-timestamps-normalized",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §post_tool_use"
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return CheckResult(
                    name="C3-timestamps-normalized",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §post_tool_use"
                )
            return CheckResult(
                name="C3-timestamps-normalized",
                passed=False,
                detail=f"Failed to run agent: {e}",
                lesson_ref="lesson.md §post_tool_use"
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
            name="C3-timestamps-normalized",
            passed=False,
            detail="No transcript in result",
            lesson_ref="lesson.md §post_tool_use"
        )

    transcript = result["transcript"]
    for msg in transcript:
        if msg.get("role") == "user" and "content" in msg:
            content = msg["content"]
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_content = block.get("content", "")
                        if isinstance(tool_content, str):
                            try:
                                parsed = json.loads(tool_content)
                                if _has_unix_epoch_in_date_field(parsed):
                                    return CheckResult(
                                        name="C3-timestamps-normalized",
                                        passed=False,
                                        detail=(
                                            "Found Unix-epoch integer in date field "
                                            "of tool_result"
                                        ),
                                        lesson_ref="lesson.md §post_tool_use"
                                    )
                            except json.JSONDecodeError:
                                pass

    return CheckResult(
        name="C3-timestamps-normalized",
        passed=True,
        detail="All date fields in tool_results are normalized to ISO-8601 strings",
        lesson_ref="lesson.md §post_tool_use"
    )


def check_c4_statuses_normalized(ctx: CheckContext) -> CheckResult:
    """C4-statuses-normalized: All status fields are title-case."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C4-statuses-normalized",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §post_tool_use"
        )

    _reset_backend_logs(ctx)

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)
    try:
        sys.modules.pop("agent", None)
        sys.modules.pop("support_backend", None)
        sys.modules.pop("support_data", None)
        import agent

        msg = "Can you look up order O001 for me?"
        try:
            result = call_with_timeout(
                agent.run_conversation, [msg], timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C4-statuses-normalized",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §post_tool_use"
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return CheckResult(
                    name="C4-statuses-normalized",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §post_tool_use"
                )
            return CheckResult(
                name="C4-statuses-normalized",
                passed=False,
                detail=f"Failed to run agent: {e}",
                lesson_ref="lesson.md §post_tool_use"
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
            name="C4-statuses-normalized",
            passed=False,
            detail="No transcript in result",
            lesson_ref="lesson.md §post_tool_use"
        )

    transcript = result["transcript"]
    for msg in transcript:
        if msg.get("role") == "user" and "content" in msg:
            content = msg["content"]
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_content = block.get("content", "")
                        if isinstance(tool_content, str):
                            try:
                                parsed = json.loads(tool_content)
                                if _check_status_case(parsed):
                                    return CheckResult(
                                        name="C4-statuses-normalized",
                                        passed=False,
                                        detail=(
                                            "Found non-title-case status field "
                                            "in tool_result"
                                        ),
                                        lesson_ref="lesson.md §post_tool_use"
                                    )
                            except json.JSONDecodeError:
                                pass

    return CheckResult(
        name="C4-statuses-normalized",
        passed=True,
        detail="All status fields in tool_results are normalized to title-case",
        lesson_ref="lesson.md §post_tool_use"
    )
