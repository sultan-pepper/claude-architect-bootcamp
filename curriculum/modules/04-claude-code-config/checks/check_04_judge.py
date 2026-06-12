"""Checks for module 04: judge-evaluated decisions and CLI tests."""

import os
import re
import shutil
import subprocess
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult
from bootcamp_cli.judge import judge, JudgeError


def check_c6_decisions_defensible(ctx: CheckContext) -> CheckResult:
    """C6-decisions-defensible: decisions.md has Task A & B sections, judge evaluates them."""
    decisions_file = ctx.workspace / "decisions.md"

    if not decisions_file.exists():
        return CheckResult(
            name="C6-decisions-defensible",
            passed=False,
            detail="workspace/decisions.md not found",
            lesson_ref="lesson.md §plan_vs_direct"
        )

    try:
        content = decisions_file.read_text()
    except Exception as e:
        return CheckResult(
            name="C6-decisions-defensible",
            passed=False,
            detail=f"Failed to read decisions.md: {e}",
            lesson_ref="lesson.md §plan_vs_direct"
        )

    # Check for both sections
    if "## Task A" not in content:
        return CheckResult(
            name="C6-decisions-defensible",
            passed=False,
            detail="decisions.md missing '## Task A' section",
            lesson_ref="lesson.md §plan_vs_direct"
        )

    if "## Task B" not in content:
        return CheckResult(
            name="C6-decisions-defensible",
            passed=False,
            detail="decisions.md missing '## Task B' section",
            lesson_ref="lesson.md §plan_vs_direct"
        )

    # Extract Task A and B sections
    task_a_match = re.search(r"## Task A\s*\n(.*?)(?=## Task B|$)", content, re.DOTALL)
    task_b_match = re.search(r"## Task B\s*\n(.*?)$", content, re.DOTALL)

    task_a_text = task_a_match.group(1).strip() if task_a_match else ""
    task_b_text = task_b_match.group(1).strip() if task_b_match else ""

    if not task_a_text or not task_b_text:
        return CheckResult(
            name="C6-decisions-defensible",
            passed=False,
            detail="Task A or Task B section is empty",
            lesson_ref="lesson.md §plan_vs_direct"
        )

    # Get rubric excerpt
    rubric_excerpt = """The decision (plan mode or direct execution) is correctly matched to the task's scope and reversal risk, and the justification names the deciding factor (multi-file scope and ordering dependency → plan mode; single-file, single-line, unambiguous → direct execution)."""

    # Judge both tasks
    try:
        verdict_a = judge(
            "C6-task-a",
            rubric_excerpt,
            f"Task A decision:\n\n{task_a_text}"
        )

        verdict_b = judge(
            "C6-task-b",
            rubric_excerpt,
            f"Task B decision:\n\n{task_b_text}"
        )

        # Both must pass
        if not verdict_a.passed:
            return CheckResult(
                name="C6-decisions-defensible",
                passed=False,
                detail=f"Task A decision not defensible: {verdict_a.reasoning}",
                lesson_ref="lesson.md §plan_vs_direct"
            )

        if not verdict_b.passed:
            return CheckResult(
                name="C6-decisions-defensible",
                passed=False,
                detail=f"Task B decision not defensible: {verdict_b.reasoning}",
                lesson_ref="lesson.md §plan_vs_direct"
            )

        return CheckResult(
            name="C6-decisions-defensible",
            passed=True,
            detail="Both Task A and Task B decisions are defensible",
            lesson_ref="lesson.md §plan_vs_direct"
        )

    except (JudgeError, Exception) as e:
        return CheckResult(
            name="C6-decisions-defensible",
            passed=False,
            detail=f"judge unavailable: {str(e)[:60]}",
            lesson_ref="lesson.md §plan_vs_direct"
        )


def check_c7_claude_p_conventions(ctx: CheckContext) -> CheckResult:
    """C7-claude-p-conventions: claude -p works and references all 3 test locations."""
    sample_repo = ctx.workspace / "sample-repo"

    # Check if claude CLI and ANTHROPIC_API_KEY are available
    if not shutil.which("claude"):
        return CheckResult(
            name="C7-claude-p-conventions",
            passed=False,
            detail="requires claude CLI and ANTHROPIC_API_KEY",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return CheckResult(
            name="C7-claude-p-conventions",
            passed=False,
            detail="requires claude CLI and ANTHROPIC_API_KEY",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )

    try:
        result = subprocess.run(
            ["claude", "-p", "list the test files in this project"],
            cwd=str(sample_repo),
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout + result.stderr

        # Check for references to all 3 test locations
        has_tests_dir = "tests" in output
        has_tests_subdir = "__tests__" in output
        has_test_suffix = "_test" in output

        if not (has_tests_dir and has_tests_subdir and has_test_suffix):
            return CheckResult(
                name="C7-claude-p-conventions",
                passed=False,
                detail="Output does not reference all three test-file locations (tests/, __tests__/, *_test.py)",
                lesson_ref="lesson.md §rules_and_glob_frontmatter"
            )

        return CheckResult(
            name="C7-claude-p-conventions",
            passed=True,
            detail="claude -p output references all test-file locations",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )

    except Exception as e:
        return CheckResult(
            name="C7-claude-p-conventions",
            passed=False,
            detail=f"claude -p failed: {e}",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )
