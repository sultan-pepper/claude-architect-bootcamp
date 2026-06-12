"""Tests for hint level parsing from rubric.md."""

from pathlib import Path

import pytest

from bootcamp_cli.rubric import parse_rubric_hints


@pytest.fixture
def sample_rubric(tmp_path: Path) -> Path:
    """Create a sample rubric.md file."""
    rubric_content = """# Rubric — 01 agentic-loop

## Criteria

1. **C1-stop-reason** (deterministic): Check stop_reason — lesson_ref: lesson.md §stop_reason

## Hints

### Level 1
The loop needs a signal from the API response, not from text.

### Level 2
`response.stop_reason` controls the loop. When it is `"end_turn"`, break.

### Level 3
Here is the outer loop skeleton with proper structure.

## Mentor guardrails

- Do not write the loop body

## Reference solution sketch

Sample solution
"""

    rubric_path = tmp_path / "rubric.md"
    rubric_path.write_text(rubric_content)
    return rubric_path


class TestHintParsing:
    """Test parsing of hint levels from rubric."""

    def test_parse_all_hint_levels(self, sample_rubric: Path) -> None:
        """Test that all hint levels are parsed."""
        hints = parse_rubric_hints(sample_rubric)

        assert len(hints) == 3
        assert 1 in hints
        assert 2 in hints
        assert 3 in hints

    def test_parse_hint_level_1_content(self, sample_rubric: Path) -> None:
        """Test that hint level 1 content is correct."""
        hints = parse_rubric_hints(sample_rubric)

        assert "signal from the API response" in hints[1]
        assert "not from text" in hints[1]

    def test_parse_hint_level_2_content(self, sample_rubric: Path) -> None:
        """Test that hint level 2 content is correct."""
        hints = parse_rubric_hints(sample_rubric)

        assert "stop_reason" in hints[2]
        assert "end_turn" in hints[2]

    def test_parse_hint_level_3_content(self, sample_rubric: Path) -> None:
        """Test that hint level 3 content is correct."""
        hints = parse_rubric_hints(sample_rubric)

        assert "outer loop skeleton" in hints[3]
        assert "structure" in hints[3]

    def test_parse_hints_strips_whitespace(self, sample_rubric: Path) -> None:
        """Test that hint content is stripped of leading/trailing whitespace."""
        hints = parse_rubric_hints(sample_rubric)

        for hint_text in hints.values():
            assert hint_text == hint_text.strip()

    def test_parse_hints_from_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that parse_rubric_hints returns empty dict for missing file."""
        nonexistent = tmp_path / "nonexistent.md"
        hints = parse_rubric_hints(nonexistent)

        assert hints == {}

    def test_parse_hints_empty_rubric(self, tmp_path: Path) -> None:
        """Test parsing a rubric with no hints."""
        rubric = tmp_path / "empty.md"
        rubric.write_text("# Rubric\n\n## Criteria\nNone\n")

        hints = parse_rubric_hints(rubric)

        assert hints == {}

    def test_parse_hints_malformed_level_header(self, tmp_path: Path) -> None:
        """Test that malformed level headers are skipped."""
        rubric = tmp_path / "malformed.md"
        rubric.write_text(
            """# Rubric

## Hints

### Level 1
Good content

### Level bad
This should be skipped

### Level 2
Also good
"""
        )

        hints = parse_rubric_hints(rubric)

        assert 1 in hints
        assert 2 in hints
        assert "bad" not in [h for h in hints.values()]

    def test_parse_hints_stops_at_next_heading(self, tmp_path: Path) -> None:
        """Test that hint body stops at next heading."""
        rubric = tmp_path / "stops.md"
        rubric.write_text(
            """# Rubric

## Hints

### Level 1
This is hint 1

### Level 2
This is hint 2

## Next section
Should not be included
"""
        )

        hints = parse_rubric_hints(rubric)

        assert "Next section" not in hints[1]
        assert "Next section" not in hints[2]

    def test_parse_hints_preserves_internal_structure(self, tmp_path: Path) -> None:
        """Test that internal markdown structure in hints is preserved."""
        rubric = tmp_path / "structure.md"
        rubric.write_text(
            """# Rubric

## Hints

### Level 1
- Point one
- Point two
  - Subpoint
"""
        )

        hints = parse_rubric_hints(rubric)

        assert "- Point one" in hints[1]
        assert "- Subpoint" in hints[1]

    def test_parse_empty_hint_body(self, tmp_path: Path) -> None:
        """Test parsing hint with no content."""
        rubric = tmp_path / "empty_hint.md"
        rubric.write_text(
            """# Rubric

## Hints

### Level 1


### Level 2
Content
"""
        )

        hints = parse_rubric_hints(rubric)

        assert 1 in hints
        assert hints[1] == ""

    def test_parse_consecutive_hint_levels(self, tmp_path: Path) -> None:
        """Test parsing consecutive hint levels."""
        rubric = tmp_path / "consecutive.md"
        rubric.write_text(
            """# Rubric

## Hints

### Level 1
First

### Level 2
Second

### Level 3
Third
"""
        )

        hints = parse_rubric_hints(rubric)

        assert len(hints) == 3
        assert hints[1] == "First"
        assert hints[2] == "Second"
        assert hints[3] == "Third"

    def test_parse_non_sequential_levels(self, tmp_path: Path) -> None:
        """Test parsing non-sequential level numbers."""
        rubric = tmp_path / "nonseq.md"
        rubric.write_text(
            """# Rubric

## Hints

### Level 1
First

### Level 5
Fifth

### Level 2
Second
"""
        )

        hints = parse_rubric_hints(rubric)

        assert 1 in hints
        assert 5 in hints
        assert 2 in hints
