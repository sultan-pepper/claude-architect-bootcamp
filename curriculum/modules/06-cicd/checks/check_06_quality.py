"""Checks for module 06: Quality metrics (coverage, false positives)."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult


def check_c2_bug_coverage(ctx: CheckContext) -> CheckResult:
    """C2-bug-coverage: ≥4 of 6 seeded bugs appear in findings."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return CheckResult(
            name="C2-bug-coverage",
            passed=False,
            detail="requires ANTHROPIC_API_KEY",
            lesson_ref="lesson.md §categorical_criteria"
        )

    # Load answer key
    answer_key_file = ctx.fixtures / "answer_key.json"
    try:
        answer_key = json.loads(answer_key_file.read_text())
        bugs = answer_key.get("bugs", [])
    except Exception as e:
        return CheckResult(
            name="C2-bug-coverage",
            passed=False,
            detail=f"Failed to load answer_key.json: {e}",
            lesson_ref="lesson.md §categorical_criteria"
        )

    ci_review = ctx.workspace / "ci_review.py"
    sample_repo = ctx.fixtures / "sample-repo"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_file = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "ci_review.py", "--repo-path", str(sample_repo), "--output", str(output_file)],
            cwd=str(ctx.workspace),
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "ANTHROPIC_API_KEY": api_key}
        )

        if result.returncode != 0:
            return CheckResult(
                name="C2-bug-coverage",
                passed=False,
                detail=f"ci_review.py failed: {result.stderr}",
                lesson_ref="lesson.md §categorical_criteria"
            )

        try:
            findings = json.loads(output_file.read_text())
        except json.JSONDecodeError:
            return CheckResult(
                name="C2-bug-coverage",
                passed=False,
                detail="Output file is not valid JSON",
                lesson_ref="lesson.md §categorical_criteria"
            )

        # Match findings against answer key bugs
        matched_bugs = set()

        for bug in bugs:
            bug_file = bug.get("file")
            bug_line = bug.get("line")
            bug_category = bug.get("category")

            # Look for finding with matching file, category, and line within ±5
            for finding in findings:
                if (finding.get("file") == bug_file and
                    finding.get("category") == bug_category and
                    abs(finding.get("line", 0) - bug_line) <= 5):
                    matched_bugs.add(bug.get("id"))
                    break

        if len(matched_bugs) < 4:
            return CheckResult(
                name="C2-bug-coverage",
                passed=False,
                detail=f"Found {len(matched_bugs)}/6 bugs; need ≥4",
                lesson_ref="lesson.md §categorical_criteria"
            )

        return CheckResult(
            name="C2-bug-coverage",
            passed=True,
            detail=f"Found {len(matched_bugs)}/6 bugs",
            lesson_ref="lesson.md §categorical_criteria"
        )

    finally:
        output_file.unlink(missing_ok=True)


def check_c3_false_positive_rate(ctx: CheckContext) -> CheckResult:
    """C3-false-positive-rate: ≤2 findings on clean files."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return CheckResult(
            name="C3-false-positive-rate",
            passed=False,
            detail="requires ANTHROPIC_API_KEY",
            lesson_ref="lesson.md §false_positive_cost"
        )

    clean_files = {
        "src/shared/__init__.py",
        "src/shared/utils.py",
        "config/config.py"
    }

    ci_review = ctx.workspace / "ci_review.py"
    sample_repo = ctx.fixtures / "sample-repo"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_file = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "ci_review.py", "--repo-path", str(sample_repo), "--output", str(output_file)],
            cwd=str(ctx.workspace),
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "ANTHROPIC_API_KEY": api_key}
        )

        if result.returncode != 0:
            return CheckResult(
                name="C3-false-positive-rate",
                passed=False,
                detail=f"ci_review.py failed: {result.stderr}",
                lesson_ref="lesson.md §false_positive_cost"
            )

        try:
            findings = json.loads(output_file.read_text())
        except json.JSONDecodeError:
            return CheckResult(
                name="C3-false-positive-rate",
                passed=False,
                detail="Output file is not valid JSON",
                lesson_ref="lesson.md §false_positive_cost"
            )

        # Count findings on clean files
        false_positives = sum(
            1 for finding in findings
            if finding.get("file") in clean_files
        )

        if false_positives > 2:
            return CheckResult(
                name="C3-false-positive-rate",
                passed=False,
                detail=f"Found {false_positives} findings on clean files; allow ≤2",
                lesson_ref="lesson.md §false_positive_cost"
            )

        return CheckResult(
            name="C3-false-positive-rate",
            passed=True,
            detail=f"Found {false_positives} false positives on clean files (≤2)",
            lesson_ref="lesson.md §false_positive_cost"
        )

    finally:
        output_file.unlink(missing_ok=True)
