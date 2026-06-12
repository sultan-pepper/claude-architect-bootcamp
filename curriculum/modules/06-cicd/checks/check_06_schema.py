"""Checks for module 06: Schema validation and structure."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult


def _validate_findings_schema(findings: list) -> str | None:
    """Validate findings against schema. Returns error message or None if valid."""
    if not isinstance(findings, list):
        return "findings is not a list"

    required_fields = {"file", "line", "category", "severity", "explanation", "fingerprint"}
    severity_enum = {"critical", "high", "medium", "low"}

    for i, item in enumerate(findings):
        if not isinstance(item, dict):
            return f"item {i} is not a dict"

        # Check required fields
        missing = required_fields - set(item.keys())
        if missing:
            return f"item {i} missing fields: {missing}"

        # Validate field types
        if not isinstance(item.get("file"), str):
            return f"item {i}: file must be string"

        if not isinstance(item.get("line"), int):
            return f"item {i}: line must be integer"

        if not isinstance(item.get("category"), str):
            return f"item {i}: category must be string"

        if item.get("severity") not in severity_enum:
            return f"item {i}: severity must be one of {severity_enum}"

        if not isinstance(item.get("explanation"), str):
            return f"item {i}: explanation must be string"

        if not isinstance(item.get("fingerprint"), str) or not item.get("fingerprint"):
            return f"item {i}: fingerprint must be non-empty string"

    return None


def check_c1_schema_valid(ctx: CheckContext) -> CheckResult:
    """C1-schema-valid: ci_review.py exits 0 and outputs valid findings JSON."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return CheckResult(
            name="C1-schema-valid",
            passed=False,
            detail="requires ANTHROPIC_API_KEY",
            lesson_ref="lesson.md §noninteractive_invocation"
        )

    ci_review = ctx.workspace / "ci_review.py"
    if not ci_review.exists():
        return CheckResult(
            name="C1-schema-valid",
            passed=False,
            detail="workspace/ci_review.py not found",
            lesson_ref="lesson.md §noninteractive_invocation"
        )

    sample_repo = ctx.fixtures / "sample-repo"
    if not sample_repo.exists():
        return CheckResult(
            name="C1-schema-valid",
            passed=False,
            detail="fixtures/sample-repo not found",
            lesson_ref="lesson.md §noninteractive_invocation"
        )

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
                name="C1-schema-valid",
                passed=False,
                detail=f"ci_review.py exited with code {result.returncode}: {result.stderr}",
                lesson_ref="lesson.md §noninteractive_invocation"
            )

        if not output_file.exists():
            return CheckResult(
                name="C1-schema-valid",
                passed=False,
                detail="ci_review.py did not create output file",
                lesson_ref="lesson.md §noninteractive_invocation"
            )

        try:
            findings = json.loads(output_file.read_text())
        except json.JSONDecodeError as e:
            return CheckResult(
                name="C1-schema-valid",
                passed=False,
                detail=f"Output file is not valid JSON: {e}",
                lesson_ref="lesson.md §noninteractive_invocation"
            )

        schema_error = _validate_findings_schema(findings)
        if schema_error:
            return CheckResult(
                name="C1-schema-valid",
                passed=False,
                detail=f"Findings schema invalid: {schema_error}",
                lesson_ref="lesson.md §noninteractive_invocation"
            )

        return CheckResult(
            name="C1-schema-valid",
            passed=True,
            detail=f"ci_review.py produced {len(findings)} valid findings",
            lesson_ref="lesson.md §noninteractive_invocation"
        )

    finally:
        output_file.unlink(missing_ok=True)
