"""Mentor chat functionality."""

import json
import os
from pathlib import Path
from typing import Optional
import sqlite3


class MentorError(Exception):
    """Error in mentor interaction."""

    pass


def mentor_chat(
    question: str,
    module_id: str,
    module_path: Path,
    conn: sqlite3.Connection
) -> str:
    """Have a one-turn conversation with the mentor.

    Args:
        question: The learner's question
        module_id: Module id
        module_path: Path to module directory
        conn: Database connection for history

    Returns:
        Mentor's response

    Raises:
        MentorError if API key missing or API call fails
    """
    import anthropic
    from bootcamp_cli.db import (
        get_mentor_messages, add_mentor_message, get_last_check_run
    )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise MentorError("ANTHROPIC_API_KEY not set")

    model = os.environ.get("JUDGE_MODEL", "claude-haiku-4-5")

    # Build system prompt from lab.md, rubric.md, and last check report
    system_parts = []

    # Add lab.md if it exists
    lab_path = module_path / "lab.md"
    if lab_path.exists():
        with open(lab_path) as f:
            lab_content = f.read()
        system_parts.append(f"Lab brief:\n{lab_content}")

    # Add Mentor guardrails section from rubric.md
    rubric_path = module_path / "rubric.md"
    if rubric_path.exists():
        with open(rubric_path) as f:
            rubric_content = f.read()

        # Extract "## Mentor guardrails" section
        lines = rubric_content.split("\n")
        for i, line in enumerate(lines):
            if "## Mentor guardrails" in line:
                guardrail_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("##"):
                        break
                    guardrail_lines.append(next_line)
                    i += 1
                guardrails = "\n".join(guardrail_lines).strip()
                if guardrails:
                    system_parts.append(f"Mentor guardrails:\n{guardrails}")
                break

    # Add latest check run report if available (contract §6)
    last_run = get_last_check_run(conn, module_id)
    if last_run and last_run["report_json"]:
        try:
            report_data = json.loads(last_run["report_json"])
            report_lines = []
            for check in report_data:
                status = "PASS" if check.get("passed") else "FAIL"
                name = check.get("name", "unknown")
                detail = check.get("detail", "")
                report_lines.append(f"{status}: {name} — {detail}")
            if report_lines:
                report_text = "\n".join(report_lines)
                system_parts.append(f"Latest check run report:\n{report_text}")
        except (json.JSONDecodeError, KeyError):
            pass

    # Add teaching guidelines
    teaching_guidelines = """Teaching approach:
- Teach via questions and pointers, not direct answers
- Never write the learner's lab code for them
- API-shape examples ≤5 lines are acceptable only if unrelated to the specific solution
- Tie answers back to lesson sections"""

    system_parts.append(teaching_guidelines)

    system_prompt = "\n\n".join(system_parts)

    # Get prior message history
    prior_messages = get_mentor_messages(conn, module_id)
    messages = []
    for msg in prior_messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add the new question
    messages.append({
        "role": "user",
        "content": question
    })

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )

        # Extract text response
        answer = ""
        for block in response.content:
            if hasattr(block, "text"):
                answer += block.text

        if not answer:
            raise MentorError("No text in response")

        # Record both sides in history
        add_mentor_message(conn, module_id, "user", question)
        add_mentor_message(conn, module_id, "assistant", answer)

        return answer

    except Exception as e:
        if isinstance(e, MentorError):
            raise
        raise MentorError(f"Mentor API error: {str(e)}")
