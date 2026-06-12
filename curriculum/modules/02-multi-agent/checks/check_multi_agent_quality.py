"""Checks for module 02: multi-agent — quality criteria C3 and C4."""

import os
import sys
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout
from bootcamp_cli.judge import judge, JudgeError


def check_c3_parallel_dispatch(ctx: CheckContext) -> CheckResult:
    """C3-parallel-dispatch: Verify >=2 tool_calls in single coordinator turn."""
    workspace = ctx.workspace
    pipeline_py = workspace / "pipeline.py"

    if not pipeline_py.exists():
        return CheckResult(
            name="C3-parallel-dispatch",
            passed=False,
            detail="pipeline.py not found in workspace",
            lesson_ref="lesson.md §parallel_dispatch"
        )

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)
    try:
        sys.modules.pop("pipeline", None)
        import pipeline

        try:
            result = call_with_timeout(
                pipeline.run_pipeline, "Containerization and Orchestration", timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C3-parallel-dispatch",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §parallel_dispatch"
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return CheckResult(
                    name="C3-parallel-dispatch",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §parallel_dispatch"
                )
            return CheckResult(
                name="C3-parallel-dispatch",
                passed=False,
                detail=f"Failed to run pipeline: {e}",
                lesson_ref="lesson.md §parallel_dispatch"
            )
    finally:
        sys.path.pop(0)
        if old_fixtures_path:
            os.environ["FIXTURES_PATH"] = old_fixtures_path
        else:
            os.environ.pop("FIXTURES_PATH", None)

    if "run_log" not in result or "coordinator_turns" not in result["run_log"]:
        return CheckResult(
            name="C3-parallel-dispatch",
            passed=False,
            detail="No coordinator_turns in run_log",
            lesson_ref="lesson.md §parallel_dispatch"
        )

    coordinator_turns = result["run_log"]["coordinator_turns"]

    for i, turn in enumerate(coordinator_turns):
        tool_calls = turn.get("tool_calls", [])
        if len(tool_calls) >= 2:
            return CheckResult(
                name="C3-parallel-dispatch",
                passed=True,
                detail=(
                    f"Found parallel dispatch with {len(tool_calls)} tool_calls "
                    f"in coordinator_turns[{i}]"
                ),
                lesson_ref="lesson.md §parallel_dispatch"
            )

    return CheckResult(
        name="C3-parallel-dispatch",
        passed=False,
        detail="No coordinator turn with >=2 parallel tool_calls found",
        lesson_ref="lesson.md §parallel_dispatch"
    )


def check_c4_report_quality(ctx: CheckContext) -> CheckResult:
    """C4-report-quality: Judge evaluation of report technical depth."""
    workspace = ctx.workspace
    pipeline_py = workspace / "pipeline.py"

    if not pipeline_py.exists():
        return CheckResult(
            name="C4-report-quality",
            passed=False,
            detail="pipeline.py not found in workspace",
            lesson_ref="lesson.md §goals_criteria"
        )

    sys.path.insert(0, str(workspace))
    old_fixtures_path = os.environ.get("FIXTURES_PATH")
    os.environ["FIXTURES_PATH"] = str(ctx.fixtures)
    try:
        sys.modules.pop("pipeline", None)
        import pipeline

        try:
            result = call_with_timeout(
                pipeline.run_pipeline, "Containerization and Orchestration", timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C4-report-quality",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §goals_criteria"
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return CheckResult(
                    name="C4-report-quality",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §goals_criteria"
                )
            return CheckResult(
                name="C4-report-quality",
                passed=False,
                detail=f"Failed to run pipeline: {e}",
                lesson_ref="lesson.md §goals_criteria"
            )
    finally:
        sys.path.pop(0)
        if old_fixtures_path:
            os.environ["FIXTURES_PATH"] = old_fixtures_path
        else:
            os.environ.pop("FIXTURES_PATH", None)

    if "report" not in result:
        return CheckResult(
            name="C4-report-quality",
            passed=False,
            detail="No report in result",
            lesson_ref="lesson.md §goals_criteria"
        )

    report = result["report"]

    rubric_excerpt = (
        "The report must demonstrate technically specific coverage of each of the six "
        "sub-domains (Containers, Orchestration, Networking, Storage, Security, Operations), "
        "not just surface mentions. Each section should contain facts from the corpus, "
        "specific technical concepts, and domain-specific details rather than generic statements."
    )

    try:
        verdict = judge("C4-report-quality", rubric_excerpt, report)
        return CheckResult(
            name="C4-report-quality",
            passed=verdict.passed,
            detail=verdict.reasoning[:200] if verdict.reasoning else "Judge evaluation",
            lesson_ref="lesson.md §goals_criteria"
        )
    except JudgeError:
        return CheckResult(
            name="C4-report-quality",
            passed=False,
            detail="judge unavailable: ANTHROPIC_API_KEY not configured",
            lesson_ref="lesson.md §goals_criteria"
        )
    except Exception as e:
        return CheckResult(
            name="C4-report-quality",
            passed=False,
            detail=f"judge unavailable: {e}",
            lesson_ref="lesson.md §goals_criteria"
        )
