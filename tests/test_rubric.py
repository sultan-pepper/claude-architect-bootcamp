"""Tests for reference solution parsing from rubric.md."""

from pathlib import Path

import pytest

from bootcamp_cli.rubric import parse_reference_solution


@pytest.fixture
def sample_rubric(tmp_path: Path) -> Path:
    """Create a sample rubric.md file."""
    rubric_content = """# Rubric — 01 agentic-loop

## Criteria

1. **C1-stop-reason** (deterministic): Check stop_reason — lesson_ref: lesson.md §stop_reason

## Hints

### Level 1
The loop needs a signal from the API response, not from text.

## Reference solution sketch

The agent.py should:
- Import anthropic
- Define TOOLS list
- Implement dispatch_tool function
- Run the while True loop

Total: approximately 80–120 lines.
"""

    rubric_path = tmp_path / "rubric.md"
    rubric_path.write_text(rubric_content)
    return rubric_path


class TestReferenceSolutionParsing:
    """Test parsing of reference solution sketch."""

    def test_parse_reference_solution(self, sample_rubric: Path) -> None:
        """Test that reference solution is parsed."""
        solution = parse_reference_solution(sample_rubric)

        assert solution is not None
        assert "agent.py" in solution

    def test_parse_reference_solution_content(self, sample_rubric: Path) -> None:
        """Test that reference solution contains expected content."""
        solution = parse_reference_solution(sample_rubric)

        assert "anthropic" in solution
        assert "TOOLS" in solution
        assert "dispatch_tool" in solution
        assert "while True" in solution

    def test_parse_reference_solution_from_nonexistent_file(
        self, tmp_path: Path
    ) -> None:
        """Test that parse_reference_solution returns None for missing file."""
        nonexistent = tmp_path / "nonexistent.md"
        solution = parse_reference_solution(nonexistent)

        assert solution is None

    def test_parse_reference_solution_missing_section(self, tmp_path: Path) -> None:
        """Test that parse_reference_solution returns None if section missing."""
        rubric = tmp_path / "no_solution.md"
        rubric.write_text(
            """# Rubric

## Criteria
Some criteria

## Hints
Some hints
"""
        )

        solution = parse_reference_solution(rubric)

        assert solution is None

    def test_parse_reference_solution_strips_whitespace(
        self, sample_rubric: Path
    ) -> None:
        """Test that solution text is stripped."""
        solution = parse_reference_solution(sample_rubric)

        assert solution is not None
        assert solution == solution.strip()

    def test_parse_reference_solution_stops_at_next_section(
        self, tmp_path: Path
    ) -> None:
        """Test that solution section stops at next ## heading."""
        rubric = tmp_path / "solution_stop.md"
        rubric.write_text(
            """# Rubric

## Reference solution sketch

Here is the solution body.

## Next section
This should not be included.
"""
        )

        solution = parse_reference_solution(rubric)

        assert solution is not None
        assert "Next section" not in solution

    def test_parse_reference_solution_with_code_blocks(
        self, tmp_path: Path
    ) -> None:
        """Test that code blocks in solution are preserved."""
        rubric = tmp_path / "with_code.md"
        rubric.write_text(
            """# Rubric

## Reference solution sketch

Here is code:

```python
def example():
    pass
```

More text.
"""
        )

        solution = parse_reference_solution(rubric)

        assert "def example" in solution
        assert "```python" in solution

    def test_parse_reference_solution_case_sensitive(self, tmp_path: Path) -> None:
        """Test that section heading matching is case-sensitive."""
        rubric = tmp_path / "case.md"
        rubric.write_text(
            """# Rubric

## reference solution sketch
This heading is lowercase and should NOT match.

## Reference solution sketch
This one should match.
"""
        )

        solution = parse_reference_solution(rubric)

        assert solution is not None
        assert "This one should match" in solution
        assert "lowercase" not in solution

    def test_parse_reference_solution_multiple_paragraphs(
        self, tmp_path: Path
    ) -> None:
        """Test that multi-paragraph solutions are parsed."""
        rubric = tmp_path / "multi_para.md"
        rubric.write_text(
            """# Rubric

## Reference solution sketch

First paragraph with content.

Second paragraph with more details.

Third paragraph wraps up.
"""
        )

        solution = parse_reference_solution(rubric)

        assert solution is not None
        assert "First paragraph" in solution
        assert "Second paragraph" in solution
        assert "Third paragraph" in solution

    def test_parse_solution_with_lists(self, tmp_path: Path) -> None:
        """Test that lists in solution are preserved."""
        rubric = tmp_path / "with_lists.md"
        rubric.write_text(
            """# Rubric

## Reference solution sketch

Key components:
- Component A
- Component B
  - Subcomponent
- Component C
"""
        )

        solution = parse_reference_solution(rubric)

        assert "- Component A" in solution
        assert "- Subcomponent" in solution
