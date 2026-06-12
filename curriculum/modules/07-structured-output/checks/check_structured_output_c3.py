"""Checks for module 07: structured-output — C3-validation-retry."""

import json
import os
import sys
import tempfile
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def _accumulate_message_text(messages: list) -> str:
    """Collect plain text content from all messages without re-serialising.

    Handles str content, list-of-blocks with 'text' key, and tool_result
    blocks whose 'content' field is a plain string.
    """
    parts: list[str] = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif isinstance(block.get("content"), str):
                    parts.append(block["content"])
    return "\n".join(parts)


def check_c3_validation_retry(ctx: CheckContext) -> CheckResult:
    """C3-validation-retry: With EXTRACT_FORCE_INVALID=1, makes exactly 2 API calls."""
    workspace = ctx.workspace
    extract_py = workspace / "extract.py"

    if not extract_py.exists():
        return CheckResult(
            name="C3-validation-retry",
            passed=False,
            detail="extract.py not found in workspace",
            lesson_ref="lesson.md §validation_retry"
        )

    sys.path.insert(0, str(workspace))
    old_env_force = os.environ.get("EXTRACT_FORCE_INVALID")
    old_env_log = os.environ.get("EXTRACT_LOG_PATH")

    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            log_path = f.name

        sys.modules.pop("extract", None)
        import extract

        os.environ["EXTRACT_FORCE_INVALID"] = "1"
        os.environ["EXTRACT_LOG_PATH"] = log_path

        invoice_001_path = ctx.fixtures / "invoices" / "invoice_001.txt"
        if not invoice_001_path.exists():
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail="invoice_001.txt not found",
                lesson_ref="lesson.md §validation_retry"
            )

        with open(invoice_001_path) as f:
            invoice_001_text = f.read()

        try:
            result = call_with_timeout(
                extract.extract_invoice, invoice_001_text, timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §validation_retry"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C3-validation-retry",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §validation_retry"
                )
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail=f"Failed to extract invoice_001: {e}",
                lesson_ref="lesson.md §validation_retry"
            )

        if result.get("api_call_count") != 2:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail=f"Expected api_call_count == 2, got {result.get('api_call_count')}",
                lesson_ref="lesson.md §validation_retry"
            )

        if not os.path.exists(log_path):
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail="EXTRACT_LOG_PATH file was not created",
                lesson_ref="lesson.md §validation_retry"
            )

        try:
            with open(log_path) as f:
                log_data = json.load(f)
        except Exception as e:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail=f"Failed to parse EXTRACT_LOG_PATH: {e}",
                lesson_ref="lesson.md §validation_retry"
            )

        if not isinstance(log_data, list) or len(log_data) != 2:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail=f"Log should contain 2 attempts, got "
                       f"{len(log_data) if isinstance(log_data, list) else 'not a list'}",
                lesson_ref="lesson.md §validation_retry"
            )

        attempt2 = log_data[1]
        if "messages" not in attempt2:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail="Attempt 2 missing 'messages' field",
                lesson_ref="lesson.md §validation_retry"
            )

        messages = attempt2["messages"]
        messages_plain = _accumulate_message_text(messages)

        if invoice_001_text not in messages_plain:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail="Attempt 2 messages do not contain original document text",
                lesson_ref="lesson.md §validation_retry"
            )

        if "forced_invalid" not in messages_plain:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail=(
                    "Attempt 2 messages do not contain the injected error "
                    "string 'forced_invalid'"
                ),
                lesson_ref="lesson.md §validation_retry"
            )

        attempt1_extracted = log_data[0].get("extracted")
        if attempt1_extracted is None:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail="Attempt 1 missing 'extracted' field",
                lesson_ref="lesson.md §validation_retry"
            )

        attempt1_json_str = json.dumps(attempt1_extracted)
        found_attempt1 = attempt1_json_str in messages_plain
        if not found_attempt1:
            for val in attempt1_extracted.values():
                if isinstance(val, (str, int, float)) and val is not None:
                    if str(val) in messages_plain:
                        found_attempt1 = True
                        break

        if not found_attempt1:
            return CheckResult(
                name="C3-validation-retry",
                passed=False,
                detail="Attempt 2 messages do not contain attempt 1's extracted output",
                lesson_ref="lesson.md §validation_retry"
            )

        return CheckResult(
            name="C3-validation-retry",
            passed=True,
            detail="Validation-retry correctly makes 2 API calls with proper logging",
            lesson_ref="lesson.md §validation_retry"
        )

    finally:
        sys.path.pop(0)
        if old_env_force is not None:
            os.environ["EXTRACT_FORCE_INVALID"] = old_env_force
        else:
            os.environ.pop("EXTRACT_FORCE_INVALID", None)

        if old_env_log is not None:
            os.environ["EXTRACT_LOG_PATH"] = old_env_log
        else:
            os.environ.pop("EXTRACT_LOG_PATH", None)

        sys.modules.pop("extract", None)

        if os.path.exists(log_path):
            os.unlink(log_path)
