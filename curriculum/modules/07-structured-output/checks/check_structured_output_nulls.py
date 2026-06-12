"""Checks for module 07: structured-output (nulls and conflict detection)."""

import json
import os
import sys
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult, call_with_timeout, CheckTimeout


def check_c1_null_not_fabricated(ctx: CheckContext) -> CheckResult:
    """C1-null-not-fabricated: Absent fields return null, not fabricated strings."""
    workspace = ctx.workspace
    extract_py = workspace / "extract.py"

    if not extract_py.exists():
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail="extract.py not found in workspace",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    sys.path.insert(0, str(workspace))
    try:
        sys.modules.pop("extract", None)
        import extract
    except SyntaxError as e:
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"extract.py syntax error: {e}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )
    finally:
        sys.path.pop(0)

    if not hasattr(extract, "extract_invoice"):
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail="extract_invoice function not found in extract.py",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    # Load ground truth
    truth_file = ctx.fixtures / "invoices" / "invoices_truth.json"
    if not truth_file.exists():
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail="invoices_truth.json not found in fixtures",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    try:
        with open(truth_file) as f:
            truth_data = json.load(f)
    except Exception as e:
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"Failed to load invoices_truth.json: {e}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    # Test invoice_002: should have null invoice_number and date
    invoice_002_path = ctx.fixtures / "invoices" / "invoice_002.txt"
    if not invoice_002_path.exists():
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail="invoice_002.txt not found",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    try:
        with open(invoice_002_path) as f:
            invoice_002_text = f.read()
        try:
            result_002 = call_with_timeout(
                extract.extract_invoice, invoice_002_text, timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C1-null-not-fabricated",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §nullable_vs_fabrication"
            )
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return CheckResult(
                name="C1-null-not-fabricated",
                passed=False,
                detail="requires ANTHROPIC_API_KEY to run the learner agent",
                lesson_ref="lesson.md §nullable_vs_fabrication"
            )
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"Failed to extract invoice_002: {e}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    if result_002.get("invoice_number") is not None:
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"invoice_002: invoice_number should be null but got {repr(result_002.get('invoice_number'))}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    if result_002.get("date") is not None:
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"invoice_002: date should be null but got {repr(result_002.get('date'))}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    # Test invoice_010: should have null invoice_number, date, and customer
    invoice_010_path = ctx.fixtures / "invoices" / "invoice_010.txt"
    if not invoice_010_path.exists():
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail="invoice_010.txt not found",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    try:
        with open(invoice_010_path) as f:
            invoice_010_text = f.read()
        try:
            result_010 = call_with_timeout(
                extract.extract_invoice, invoice_010_text, timeout=120
            )
        except CheckTimeout:
            return CheckResult(
                name="C1-null-not-fabricated",
                passed=False,
                detail="learner code timed out after 120s",
                lesson_ref="lesson.md §nullable_vs_fabrication"
            )
    except Exception as e:
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"Failed to extract invoice_010: {e}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    if result_010.get("invoice_number") is not None:
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"invoice_010: invoice_number should be null but got {repr(result_010.get('invoice_number'))}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    if result_010.get("date") is not None:
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"invoice_010: date should be null but got {repr(result_010.get('date'))}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    if result_010.get("customer") is not None:
        return CheckResult(
            name="C1-null-not-fabricated",
            passed=False,
            detail=f"invoice_010: customer should be null but got {repr(result_010.get('customer'))}",
            lesson_ref="lesson.md §nullable_vs_fabrication"
        )

    return CheckResult(
        name="C1-null-not-fabricated",
        passed=True,
        detail="invoice_002 and invoice_010 correctly return null for absent fields",
        lesson_ref="lesson.md §nullable_vs_fabrication"
    )


def check_c2_conflict_detected(ctx: CheckContext) -> CheckResult:
    """C2-conflict-detected: invoice_003 returns conflict_detected: true."""
    workspace = ctx.workspace
    extract_py = workspace / "extract.py"

    if not extract_py.exists():
        return CheckResult(
            name="C2-conflict-detected",
            passed=False,
            detail="extract.py not found in workspace",
            lesson_ref="lesson.md §semantic_validation"
        )

    sys.path.insert(0, str(workspace))
    try:
        sys.modules.pop("extract", None)
        import extract
    except SyntaxError as e:
        return CheckResult(
            name="C2-conflict-detected",
            passed=False,
            detail=f"extract.py syntax error: {e}",
            lesson_ref="lesson.md §semantic_validation"
        )
    finally:
        sys.path.pop(0)

    if not hasattr(extract, "extract_invoice"):
        return CheckResult(
            name="C2-conflict-detected",
            passed=False,
            detail="extract_invoice function not found in extract.py",
            lesson_ref="lesson.md §semantic_validation"
        )

    invoice_003_path = ctx.fixtures / "invoices" / "invoice_003.txt"
    if not invoice_003_path.exists():
        return CheckResult(
            name="C2-conflict-detected",
            passed=False,
            detail="invoice_003.txt not found",
            lesson_ref="lesson.md §semantic_validation"
        )

    try:
        with open(invoice_003_path) as f:
            invoice_003_text = f.read()
        result_003 = extract.extract_invoice(invoice_003_text)
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return CheckResult(
                name="C2-conflict-detected",
                passed=False,
                detail="requires ANTHROPIC_API_KEY to run the learner agent",
                lesson_ref="lesson.md §semantic_validation"
            )
        return CheckResult(
            name="C2-conflict-detected",
            passed=False,
            detail=f"Failed to extract invoice_003: {e}",
            lesson_ref="lesson.md §semantic_validation"
        )

    if result_003.get("conflict_detected") is not True:
        return CheckResult(
            name="C2-conflict-detected",
            passed=False,
            detail=f"invoice_003: conflict_detected should be true but got {result_003.get('conflict_detected')}",
            lesson_ref="lesson.md §semantic_validation"
        )

    calculated = result_003.get("calculated_total")
    stated = result_003.get("stated_total")

    if calculated is None or stated is None:
        return CheckResult(
            name="C2-conflict-detected",
            passed=False,
            detail=f"invoice_003: calculated_total or stated_total is null",
            lesson_ref="lesson.md §semantic_validation"
        )

    if calculated <= stated:
        return CheckResult(
            name="C2-conflict-detected",
            passed=False,
            detail=f"invoice_003: calculated_total ({calculated}) should exceed stated_total ({stated})",
            lesson_ref="lesson.md §semantic_validation"
        )

    return CheckResult(
        name="C2-conflict-detected",
        passed=True,
        detail="invoice_003 correctly detects arithmetic conflict",
        lesson_ref="lesson.md §semantic_validation"
    )
