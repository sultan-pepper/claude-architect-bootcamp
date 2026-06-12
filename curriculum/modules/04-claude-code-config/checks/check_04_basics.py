"""Checks for module 04: Basic file existence checks."""

import re
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult


def check_c1_claudemd_exists(ctx: CheckContext) -> CheckResult:
    """C1-claudemd-exists: CLAUDE.md exists with >10 bytes."""
    sample_repo = ctx.workspace / "sample-repo"
    claude_md = sample_repo / "CLAUDE.md"

    if not claude_md.exists():
        return CheckResult(
            name="C1-claudemd-exists",
            passed=False,
            detail="workspace/sample-repo/CLAUDE.md not found",
            lesson_ref="lesson.md §claude_md_hierarchy"
        )

    try:
        content = claude_md.read_text()
    except Exception as e:
        return CheckResult(
            name="C1-claudemd-exists",
            passed=False,
            detail=f"Failed to read CLAUDE.md: {e}",
            lesson_ref="lesson.md §claude_md_hierarchy"
        )

    if len(content) <= 10:
        return CheckResult(
            name="C1-claudemd-exists",
            passed=False,
            detail=f"CLAUDE.md has {len(content)} bytes; need >10",
            lesson_ref="lesson.md §claude_md_hierarchy"
        )

    return CheckResult(
        name="C1-claudemd-exists",
        passed=True,
        detail=f"CLAUDE.md found with {len(content)} bytes",
        lesson_ref="lesson.md §claude_md_hierarchy"
    )
