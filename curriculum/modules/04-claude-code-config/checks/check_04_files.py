"""Checks for module 04: file existence and frontmatter validation."""

import re
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult


def _parse_yaml_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter between --- delimiters. Returns dict or empty dict."""
    if not content.startswith("---"):
        return {}

    # Find closing delimiter
    match = re.match(r"^---\s*\n(.*?)\n---\s*", content, re.DOTALL)
    if not match:
        return {}

    frontmatter = match.group(1)
    result = {}
    lines = frontmatter.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for key: value pair
        if ":" in line and not line.startswith(" "):
            key, value_str = line.split(":", 1)
            key = key.strip()
            value_str = value_str.strip()

            # If value is empty, check for list on next lines
            if not value_str:
                # Collect list items (lines starting with -)
                list_items = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("  - "):
                        item = next_line[4:].strip().strip("'\"")
                        list_items.append(item)
                        i += 1
                    elif not next_line.strip():
                        i += 1
                    else:
                        break
                result[key] = list_items
                continue
            elif value_str.startswith("["):
                # Inline list [item1, item2]
                list_match = re.match(r"\[(.*?)\]", value_str)
                if list_match:
                    items = [item.strip().strip("'\"")
                            for item in list_match.group(1).split(",")]
                    result[key] = [item for item in items if item]
                else:
                    result[key] = []
            elif value_str.startswith('"') or value_str.startswith("'"):
                result[key] = value_str.strip("'\"")
            else:
                result[key] = value_str

        i += 1

    return result


def check_c2_rules_frontmatter_valid(ctx: CheckContext) -> CheckResult:
    """C2-rules-frontmatter-valid: at least one .md in .claude/rules/ with valid YAML frontmatter containing globs."""
    sample_repo = ctx.workspace / "sample-repo"
    rules_dir = sample_repo / ".claude" / "rules"

    if not rules_dir.exists():
        return CheckResult(
            name="C2-rules-frontmatter-valid",
            passed=False,
            detail=f"workspace/sample-repo/.claude/rules/ directory does not exist",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )

    md_files = list(rules_dir.glob("*.md"))
    if not md_files:
        return CheckResult(
            name="C2-rules-frontmatter-valid",
            passed=False,
            detail="No .md files found in .claude/rules/",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )

    for md_file in md_files:
        try:
            content = md_file.read_text()
            frontmatter = _parse_yaml_frontmatter(content)

            if "globs" in frontmatter:
                globs = frontmatter["globs"]
                if isinstance(globs, list) and len(globs) > 0:
                    return CheckResult(
                        name="C2-rules-frontmatter-valid",
                        passed=True,
                        detail=f"Found valid frontmatter with globs in {md_file.name}",
                        lesson_ref="lesson.md §rules_and_glob_frontmatter"
                    )
        except Exception:
            continue

    return CheckResult(
        name="C2-rules-frontmatter-valid",
        passed=False,
        detail="No rules file has valid YAML frontmatter with globs list",
        lesson_ref="lesson.md §rules_and_glob_frontmatter"
    )


def check_c3_globs_cover_tests(ctx: CheckContext) -> CheckResult:
    """C3-globs-cover-tests: glob patterns cover all 5 test file paths."""
    sample_repo = ctx.workspace / "sample-repo"
    rules_dir = sample_repo / ".claude" / "rules"

    expected_tests = {
        "tests/test_shared_utils.py",
        "tests/conftest.py",
        "tests/test_integration.py",
        "src/api-service/__tests__/test_main.py",
        "src/worker-service/worker_test.py",
    }

    if not rules_dir.exists():
        return CheckResult(
            name="C3-globs-cover-tests",
            passed=False,
            detail=".claude/rules/ directory does not exist",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )

    all_globs = []
    md_files = list(rules_dir.glob("*.md"))

    for md_file in md_files:
        try:
            content = md_file.read_text()
            frontmatter = _parse_yaml_frontmatter(content)

            if "globs" in frontmatter:
                globs = frontmatter["globs"]
                if isinstance(globs, list):
                    all_globs.extend(globs)
        except Exception:
            continue

    if not all_globs:
        return CheckResult(
            name="C3-globs-cover-tests",
            passed=False,
            detail="No glob patterns found in any rules file",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )

    # Use fnmatch to expand patterns
    from fnmatch import fnmatch
    matched_tests = set()

    for test_path in expected_tests:
        for glob_pattern in all_globs:
            if fnmatch(test_path, glob_pattern):
                matched_tests.add(test_path)
                break

    missing = expected_tests - matched_tests
    if missing:
        return CheckResult(
            name="C3-globs-cover-tests",
            passed=False,
            detail=f"These test paths not covered by globs: {', '.join(sorted(missing))}",
            lesson_ref="lesson.md §rules_and_glob_frontmatter"
        )

    return CheckResult(
        name="C3-globs-cover-tests",
        passed=True,
        detail=f"All 5 test paths covered by glob patterns",
        lesson_ref="lesson.md §rules_and_glob_frontmatter"
    )


def check_c4_command_exists(ctx: CheckContext) -> CheckResult:
    """C4-command-exists: at least one .md file in .claude/commands/ with >10 chars of body."""
    sample_repo = ctx.workspace / "sample-repo"
    commands_dir = sample_repo / ".claude" / "commands"

    if not commands_dir.exists():
        return CheckResult(
            name="C4-command-exists",
            passed=False,
            detail="workspace/sample-repo/.claude/commands/ directory does not exist",
            lesson_ref="lesson.md §slash_commands"
        )

    md_files = list(commands_dir.glob("*.md"))
    if not md_files:
        return CheckResult(
            name="C4-command-exists",
            passed=False,
            detail="No .md files found in .claude/commands/",
            lesson_ref="lesson.md §slash_commands"
        )

    for md_file in md_files:
        try:
            content = md_file.read_text()
            # Extract body after frontmatter
            if content.startswith("---"):
                match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
                if match:
                    body = match.group(2)
                else:
                    body = content
            else:
                body = content

            body = body.strip()
            if len(body) > 10:
                return CheckResult(
                    name="C4-command-exists",
                    passed=True,
                    detail=f"Found command in {md_file.name} with {len(body)} bytes of body",
                    lesson_ref="lesson.md §slash_commands"
                )
        except Exception:
            continue

    return CheckResult(
        name="C4-command-exists",
        passed=False,
        detail="No command file has >10 characters of body content",
        lesson_ref="lesson.md §slash_commands"
    )


def check_c5_skill_frontmatter(ctx: CheckContext) -> CheckResult:
    """C5-skill-frontmatter: at least one .md in .claude/skills/ with context: fork and allowed-tools list."""
    sample_repo = ctx.workspace / "sample-repo"
    skills_dir = sample_repo / ".claude" / "skills"

    if not skills_dir.exists():
        return CheckResult(
            name="C5-skill-frontmatter",
            passed=False,
            detail="workspace/sample-repo/.claude/skills/ directory does not exist",
            lesson_ref="lesson.md §skills"
        )

    md_files = list(skills_dir.glob("*.md"))
    if not md_files:
        return CheckResult(
            name="C5-skill-frontmatter",
            passed=False,
            detail="No .md files found in .claude/skills/",
            lesson_ref="lesson.md §skills"
        )

    for md_file in md_files:
        try:
            content = md_file.read_text()
            frontmatter = _parse_yaml_frontmatter(content)

            # Check for context: fork
            if frontmatter.get("context") != "fork":
                continue

            # Check for allowed-tools as non-empty list
            allowed_tools = frontmatter.get("allowed-tools")
            if not isinstance(allowed_tools, list) or len(allowed_tools) == 0:
                continue

            return CheckResult(
                name="C5-skill-frontmatter",
                passed=True,
                detail=f"Found skill with context: fork and allowed-tools list in {md_file.name}",
                lesson_ref="lesson.md §skills"
            )
        except Exception:
            continue

    return CheckResult(
        name="C5-skill-frontmatter",
        passed=False,
        detail="No skill file has context: fork and non-empty allowed-tools list",
        lesson_ref="lesson.md §skills"
    )
