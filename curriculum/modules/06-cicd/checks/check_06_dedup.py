"""Checks for module 06: Deduplication across runs."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult


def check_c4_no_duplicate_fingerprints(ctx: CheckContext) -> CheckResult:
    """C4-no-duplicate-fingerprints: second run with --prior-findings has disjoint fingerprints."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return CheckResult(
            name="C4-no-duplicate-fingerprints",
            passed=False,
            detail="requires ANTHROPIC_API_KEY",
            lesson_ref="lesson.md §dedup_via_context"
        )

    ci_review = ctx.workspace / "ci_review.py"
    sample_repo = ctx.fixtures / "sample-repo"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output1_file = Path(f.name)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output2_file = Path(f.name)

    try:
        # First run
        result1 = subprocess.run(
            ["python", "ci_review.py", "--repo-path", str(sample_repo), "--output", str(output1_file)],
            cwd=str(ctx.workspace),
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "ANTHROPIC_API_KEY": api_key}
        )

        if result1.returncode != 0:
            return CheckResult(
                name="C4-no-duplicate-fingerprints",
                passed=False,
                detail=f"First ci_review.py run failed: {result1.stderr}",
                lesson_ref="lesson.md §dedup_via_context"
            )

        try:
            findings1 = json.loads(output1_file.read_text())
        except json.JSONDecodeError:
            return CheckResult(
                name="C4-no-duplicate-fingerprints",
                passed=False,
                detail="First output file is not valid JSON",
                lesson_ref="lesson.md §dedup_via_context"
            )

        # Second run with --prior-findings
        result2 = subprocess.run(
            ["python", "ci_review.py", "--repo-path", str(sample_repo),
             "--prior-findings", str(output1_file), "--output", str(output2_file)],
            cwd=str(ctx.workspace),
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "ANTHROPIC_API_KEY": api_key}
        )

        if result2.returncode != 0:
            return CheckResult(
                name="C4-no-duplicate-fingerprints",
                passed=False,
                detail=f"Second ci_review.py run failed: {result2.stderr}",
                lesson_ref="lesson.md §dedup_via_context"
            )

        try:
            findings2 = json.loads(output2_file.read_text())
        except json.JSONDecodeError:
            return CheckResult(
                name="C4-no-duplicate-fingerprints",
                passed=False,
                detail="Second output file is not valid JSON",
                lesson_ref="lesson.md §dedup_via_context"
            )

        # Extract fingerprints
        fingerprints1 = {f.get("fingerprint") for f in findings1}
        fingerprints2 = {f.get("fingerprint") for f in findings2}

        # Check for overlap
        overlap = fingerprints1 & fingerprints2
        if overlap:
            return CheckResult(
                name="C4-no-duplicate-fingerprints",
                passed=False,
                detail=f"Found {len(overlap)} duplicate fingerprints between runs",
                lesson_ref="lesson.md §dedup_via_context"
            )

        return CheckResult(
            name="C4-no-duplicate-fingerprints",
            passed=True,
            detail="Fingerprints are disjoint between runs",
            lesson_ref="lesson.md §dedup_via_context"
        )

    finally:
        output1_file.unlink(missing_ok=True)
        output2_file.unlink(missing_ok=True)
