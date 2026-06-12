"""Checks for module 02: multi-agent — coverage criteria C1 and C2."""

import os
import sys
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c1_all_subdomains(ctx: CheckContext) -> CheckResult:
    """C1-all-subdomains: Verify report covers all 6 subdomains."""
    workspace = ctx.workspace
    pipeline_py = workspace / "pipeline.py"

    if not pipeline_py.exists():
        return CheckResult(
            name="C1-all-subdomains",
            passed=False,
            detail="pipeline.py not found in workspace",
            lesson_ref="lesson.md §decomposition"
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
                name="C1-all-subdomains",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §decomposition"
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return CheckResult(
                    name="C1-all-subdomains",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §decomposition"
                )
            return CheckResult(
                name="C1-all-subdomains",
                passed=False,
                detail=f"Failed to run pipeline: {e}",
                lesson_ref="lesson.md §decomposition"
            )
    finally:
        sys.path.pop(0)
        if old_fixtures_path:
            os.environ["FIXTURES_PATH"] = old_fixtures_path
        else:
            os.environ.pop("FIXTURES_PATH", None)

    if "report" not in result:
        return CheckResult(
            name="C1-all-subdomains",
            passed=False,
            detail="No report in result",
            lesson_ref="lesson.md §decomposition"
        )

    report = result["report"].lower()

    required_subdomains = [
        "containers", "orchestration", "networking",
        "storage", "security", "operations"
    ]

    missing = [sd for sd in required_subdomains if sd not in report]

    if missing:
        return CheckResult(
            name="C1-all-subdomains",
            passed=False,
            detail=f"Report missing subdomains: {', '.join(missing)}",
            lesson_ref="lesson.md §decomposition"
        )

    return CheckResult(
        name="C1-all-subdomains",
        passed=True,
        detail="Report covers all 6 required subdomains",
        lesson_ref="lesson.md §decomposition"
    )


def check_c2_context_passing(ctx: CheckContext) -> CheckResult:
    """C2-context-passing: Verify synthesis prompt contains findings."""
    workspace = ctx.workspace
    pipeline_py = workspace / "pipeline.py"

    if not pipeline_py.exists():
        return CheckResult(
            name="C2-context-passing",
            passed=False,
            detail="pipeline.py not found in workspace",
            lesson_ref="lesson.md §context_passing"
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
                name="C2-context-passing",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §context_passing"
            )
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return CheckResult(
                    name="C2-context-passing",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §context_passing"
                )
            return CheckResult(
                name="C2-context-passing",
                passed=False,
                detail=f"Failed to run pipeline: {e}",
                lesson_ref="lesson.md §context_passing"
            )
    finally:
        sys.path.pop(0)
        if old_fixtures_path:
            os.environ["FIXTURES_PATH"] = old_fixtures_path
        else:
            os.environ.pop("FIXTURES_PATH", None)

    if "run_log" not in result or "synthesis_call" not in result["run_log"]:
        return CheckResult(
            name="C2-context-passing",
            passed=False,
            detail="No synthesis_call in run_log",
            lesson_ref="lesson.md §context_passing"
        )

    synthesis_call = result["run_log"]["synthesis_call"]
    if "user_prompt" not in synthesis_call:
        return CheckResult(
            name="C2-context-passing",
            passed=False,
            detail="No user_prompt in synthesis_call",
            lesson_ref="lesson.md §context_passing"
        )

    user_prompt = synthesis_call["user_prompt"]

    if not user_prompt:
        return CheckResult(
            name="C2-context-passing",
            passed=False,
            detail="synthesis_call.user_prompt is empty",
            lesson_ref="lesson.md §context_passing"
        )

    lines = user_prompt.strip().split("\n")
    if len(lines) < 10:
        return CheckResult(
            name="C2-context-passing",
            passed=False,
            detail="synthesis_call.user_prompt is too short to contain substantive findings",
            lesson_ref="lesson.md §context_passing"
        )

    keywords = [
        "container", "docker", "kubernetes", "pod", "deployment",
        "networking", "ingress", "storage", "volume", "security",
        "monitoring", "observability", "config", "resource"
    ]
    found_keywords = sum(1 for kw in keywords if kw.lower() in user_prompt.lower())

    if found_keywords < 5:
        return CheckResult(
            name="C2-context-passing",
            passed=False,
            detail="synthesis_call.user_prompt lacks substantive technical content from corpus",
            lesson_ref="lesson.md §context_passing"
        )

    return CheckResult(
        name="C2-context-passing",
        passed=True,
        detail=(
            f"synthesis_call.user_prompt contains substantive findings "
            f"({len(lines)} lines, {found_keywords} keywords)"
        ),
        lesson_ref="lesson.md §context_passing"
    )
