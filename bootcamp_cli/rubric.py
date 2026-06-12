"""Parse rubric.md for hints and reference solutions."""

from pathlib import Path
from typing import Optional


def parse_rubric_hints(rubric_path: Path) -> dict[int, str]:
    """Extract hint levels from rubric.md.

    Returns a dict mapping level number to hint body.
    """
    if not rubric_path.exists():
        return {}

    with open(rubric_path) as f:
        content = f.read()

    hints: dict[int, str] = {}
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for ### Level N
        if line.startswith("### Level "):
            try:
                level = int(line.split()[-1])
                # Collect everything until next heading or end
                body_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("#"):
                        break
                    body_lines.append(next_line)
                    i += 1

                # Strip leading/trailing empty lines and join
                body = "\n".join(body_lines).strip()
                hints[level] = body
                continue
            except (ValueError, IndexError):
                pass

        i += 1

    return hints


def parse_reference_solution(rubric_path: Path) -> Optional[str]:
    """Extract Reference solution sketch from rubric.md."""
    if not rubric_path.exists():
        return None

    with open(rubric_path) as f:
        content = f.read()

    lines = content.split("\n")

    # Find "## Reference solution sketch"
    for i, line in enumerate(lines):
        if "## Reference solution sketch" in line:
            # Collect everything after until next ## heading or end
            body_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.startswith("##"):
                    break
                body_lines.append(next_line)
                i += 1

            body = "\n".join(body_lines).strip()
            return body if body else None

    return None
