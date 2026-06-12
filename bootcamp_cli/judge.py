"""LLM judge for check result validation."""

from dataclasses import dataclass
import os
from typing import Any


@dataclass
class Verdict:
    """Verdict from the LLM judge."""

    criterion: str
    passed: bool
    reasoning: str


class JudgeError(Exception):
    """Error when judge API call fails."""

    pass


def judge(criterion: str, rubric_excerpt: str, artifact: str) -> Verdict:
    """Judge a check result using Claude.

    Args:
        criterion: Criterion id (e.g., "C3-no-iteration-cap")
        rubric_excerpt: Relevant section from rubric.md
        artifact: The artifact to judge (e.g., code, test output)

    Returns:
        Verdict with criterion, passed, and reasoning

    Raises:
        JudgeError if API call fails
    """
    import anthropic

    model = os.environ.get("JUDGE_MODEL", "claude-haiku-4-5")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise JudgeError("ANTHROPIC_API_KEY not set")

    try:
        client = anthropic.Anthropic()
    except Exception as e:
        raise JudgeError(f"Could not construct Anthropic client: {e}")

    # Define the verdict tool
    tools = [
        {
            "name": "render_verdict",
            "description": "Render the verdict about whether the criterion is met",
            "input_schema": {
                "type": "object",
                "properties": {
                    "criterion": {
                        "type": "string",
                        "description": "The criterion being evaluated"
                    },
                    "pass": {
                        "type": "boolean",
                        "description": "Whether the criterion is met"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of the verdict"
                    }
                },
                "required": ["criterion", "pass", "reasoning"]
            }
        }
    ]

    system_prompt = f"""You are an expert evaluator of code assignments.

Criterion: {criterion}

Rubric guidance:
{rubric_excerpt}

Evaluate the artifact against the criterion and rubric. Be fair but thorough.
Output your verdict using the render_verdict tool."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=0,
            system=system_prompt,
            tools=tools,
            tool_choice={"type": "tool", "name": "render_verdict"},
            messages=[
                {
                    "role": "user",
                    "content": f"Here is the artifact to evaluate:\n\n{artifact}"
                }
            ]
        )

        # Extract verdict from tool_use block
        for block in response.content:
            if block.type == "tool_use" and block.name == "render_verdict":
                input_data = block.input
                return Verdict(
                    criterion=input_data.get("criterion", criterion),
                    passed=input_data.get("pass", False),
                    reasoning=input_data.get("reasoning", "")
                )

        raise JudgeError("No render_verdict tool call in response")

    except JudgeError:
        raise
    except Exception as e:
        raise JudgeError(f"Judge API error: {str(e)}")
