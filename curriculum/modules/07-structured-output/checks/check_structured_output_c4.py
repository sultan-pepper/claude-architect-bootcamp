"""Checks for module 07: structured-output — C4-no-retry-on-absence."""

import os
import sys

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c4_no_retry_on_absence(ctx: CheckContext) -> CheckResult:
    """C4-no-retry-on-absence: invoice_004 (missing customer) makes only 1 API call."""
    workspace = ctx.workspace
    extract_py = workspace / "extract.py"

    if not extract_py.exists():
        return CheckResult(
            name="C4-no-retry-on-absence",
            passed=False,
            detail="extract.py not found in workspace",
            lesson_ref="lesson.md §unretryable_absence"
        )

    sys.path.insert(0, str(workspace))
    old_env_force = os.environ.get("EXTRACT_FORCE_INVALID")

    try:
        os.environ.pop("EXTRACT_FORCE_INVALID", None)

        sys.modules.pop("extract", None)
        import extract

        invoice_004_path = ctx.fixtures / "invoices" / "invoice_004.txt"
        if not invoice_004_path.exists():
            return CheckResult(
                name="C4-no-retry-on-absence",
                passed=False,
                detail="invoice_004.txt not found",
                lesson_ref="lesson.md §unretryable_absence"
            )

        with open(invoice_004_path) as f:
            invoice_004_text = f.read()

        try:
            result = call_with_timeout(
                extract.extract_invoice, invoice_004_text, timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C4-no-retry-on-absence",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §unretryable_absence"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CheckResult(
                    name="C4-no-retry-on-absence",
                    passed=False,
                    detail="requires ANTHROPIC_API_KEY to run the learner agent",
                    lesson_ref="lesson.md §unretryable_absence"
                )
            return CheckResult(
                name="C4-no-retry-on-absence",
                passed=False,
                detail=f"Failed to extract invoice_004: {e}",
                lesson_ref="lesson.md §unretryable_absence"
            )

        if result.get("api_call_count") != 1:
            return CheckResult(
                name="C4-no-retry-on-absence",
                passed=False,
                detail=f"Expected api_call_count == 1, got {result.get('api_call_count')}",
                lesson_ref="lesson.md §unretryable_absence"
            )

        if result.get("customer") is not None:
            return CheckResult(
                name="C4-no-retry-on-absence",
                passed=False,
                detail=f"invoice_004: customer should be null but got "
                       f"{repr(result.get('customer'))}",
                lesson_ref="lesson.md §unretryable_absence"
            )

        return CheckResult(
            name="C4-no-retry-on-absence",
            passed=True,
            detail=(
                "invoice_004 correctly identifies unretryable absence "
                "and makes only 1 API call"
            ),
            lesson_ref="lesson.md §unretryable_absence"
        )

    finally:
        sys.path.pop(0)
        if old_env_force is not None:
            os.environ["EXTRACT_FORCE_INVALID"] = old_env_force
        else:
            os.environ.pop("EXTRACT_FORCE_INVALID", None)

        sys.modules.pop("extract", None)
