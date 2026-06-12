"""Checks for module 05: MCP server errors and validation."""

import importlib.util
import json
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult

_spec = importlib.util.spec_from_file_location(
    "m05_mcp_probe", str(Path(__file__).parent / "mcp_probe.py"))
assert _spec is not None and _spec.loader is not None
_probe_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_probe_mod)
_probe_mcp_server = _probe_mod._probe_mcp_server


def check_c4_empty_not_error(ctx: CheckContext) -> CheckResult:
    """C4-empty-not-error: get_stock_level(GADGET-001) returns non-error result with quantity 0."""
    results, error = _probe_mcp_server(ctx.workspace, ctx.fixtures)

    if error:
        return CheckResult(
            name="C4-empty-not-error",
            passed=False,
            detail=f"Failed to start server: {error}",
            lesson_ref="lesson.md §empty_result_not_error"
        )

    stock_error = results.get("stock_error")
    if stock_error:
        return CheckResult(
            name="C4-empty-not-error",
            passed=False,
            detail=f"get_stock_level call raised error: {stock_error}",
            lesson_ref="lesson.md §empty_result_not_error"
        )

    stock_result = results.get("stock_call")
    if not stock_result:
        return CheckResult(
            name="C4-empty-not-error",
            passed=False,
            detail="get_stock_level call produced no result",
            lesson_ref="lesson.md §empty_result_not_error"
        )

    # Check isError flag
    is_error = getattr(stock_result, "isError", False)
    if is_error:
        return CheckResult(
            name="C4-empty-not-error",
            passed=False,
            detail=f"get_stock_level returned isError=true",
            lesson_ref="lesson.md §empty_result_not_error"
        )

    # Check content for error key
    content = getattr(stock_result, "content", [])
    if isinstance(content, list) and len(content) > 0:
        content_item = content[0]
        if hasattr(content_item, "text"):
            text = content_item.text
            try:
                content_json = json.loads(text)
                if "error" in content_json:
                    return CheckResult(
                        name="C4-empty-not-error",
                        passed=False,
                        detail="Result content includes error key",
                        lesson_ref="lesson.md §empty_result_not_error"
                    )
            except json.JSONDecodeError:
                pass

    return CheckResult(
        name="C4-empty-not-error",
        passed=True,
        detail="get_stock_level returned non-error result for zero-stock item",
        lesson_ref="lesson.md §empty_result_not_error"
    )


def check_c5_timeout_structured_error(ctx: CheckContext) -> CheckResult:
    """C5-timeout-structured-error: with INVENTORY_SIMULATE=timeout, returns transient error."""
    results, error = _probe_mcp_server(ctx.workspace, ctx.fixtures,
                                       env_overrides={"INVENTORY_SIMULATE": "timeout"})

    if error:
        return CheckResult(
            name="C5-timeout-structured-error",
            passed=False,
            detail=f"Failed to start server: {error}",
            lesson_ref="lesson.md §structured_errors"
        )

    search_error = results.get("search_error")
    if search_error:
        return CheckResult(
            name="C5-timeout-structured-error",
            passed=False,
            detail=f"search_products call raised error: {search_error}",
            lesson_ref="lesson.md §structured_errors"
        )

    search_result = results.get("search_call")
    if not search_result:
        return CheckResult(
            name="C5-timeout-structured-error",
            passed=False,
            detail="search_products call produced no result",
            lesson_ref="lesson.md §structured_errors"
        )

    is_error = getattr(search_result, "isError", False)
    if not is_error:
        return CheckResult(
            name="C5-timeout-structured-error",
            passed=False,
            detail="search_products did not return isError=true on timeout simulation",
            lesson_ref="lesson.md §structured_errors"
        )

    content = getattr(search_result, "content", [])
    if isinstance(content, list) and len(content) > 0:
        content_item = content[0]
        if hasattr(content_item, "text"):
            text = content_item.text
            try:
                content_json = json.loads(text)
                error_cat = content_json.get("errorCategory")
                is_retryable = content_json.get("isRetryable")

                if error_cat != "transient":
                    return CheckResult(
                        name="C5-timeout-structured-error",
                        passed=False,
                        detail=f"errorCategory is {error_cat}; expected transient",
                        lesson_ref="lesson.md §structured_errors"
                    )

                if not is_retryable:
                    return CheckResult(
                        name="C5-timeout-structured-error",
                        passed=False,
                        detail=f"isRetryable is {is_retryable}; expected true",
                        lesson_ref="lesson.md §structured_errors"
                    )

                return CheckResult(
                    name="C5-timeout-structured-error",
                    passed=True,
                    detail="Timeout simulation returned transient/retryable error",
                    lesson_ref="lesson.md §structured_errors"
                )

            except json.JSONDecodeError as e:
                return CheckResult(
                    name="C5-timeout-structured-error",
                    passed=False,
                    detail=f"Could not parse error JSON: {e}",
                    lesson_ref="lesson.md §structured_errors"
                )

    return CheckResult(
        name="C5-timeout-structured-error",
        passed=False,
        detail="Could not extract error structure from result",
        lesson_ref="lesson.md §structured_errors"
    )


def check_c6_policy_structured_error(ctx: CheckContext) -> CheckResult:
    """C6-policy-structured-error: delete_supplier(1) returns business/non-retryable error."""
    results, error = _probe_mcp_server(ctx.workspace, ctx.fixtures)

    if error:
        return CheckResult(
            name="C6-policy-structured-error",
            passed=False,
            detail=f"Failed to start server: {error}",
            lesson_ref="lesson.md §structured_errors"
        )

    delete_error = results.get("delete_error")
    if delete_error:
        return CheckResult(
            name="C6-policy-structured-error",
            passed=False,
            detail=f"delete_supplier call raised error: {delete_error}",
            lesson_ref="lesson.md §structured_errors"
        )

    delete_result = results.get("delete_call")
    if not delete_result:
        return CheckResult(
            name="C6-policy-structured-error",
            passed=False,
            detail="delete_supplier call produced no result",
            lesson_ref="lesson.md §structured_errors"
        )

    is_error = getattr(delete_result, "isError", False)
    if not is_error:
        return CheckResult(
            name="C6-policy-structured-error",
            passed=False,
            detail="delete_supplier did not return isError=true for supplier with products",
            lesson_ref="lesson.md §structured_errors"
        )

    content = getattr(delete_result, "content", [])
    if isinstance(content, list) and len(content) > 0:
        content_item = content[0]
        if hasattr(content_item, "text"):
            text = content_item.text
            try:
                content_json = json.loads(text)
                is_retryable = content_json.get("isRetryable")

                if is_retryable:
                    return CheckResult(
                        name="C6-policy-structured-error",
                        passed=False,
                        detail=f"isRetryable is {is_retryable}; expected false",
                        lesson_ref="lesson.md §structured_errors"
                    )

                return CheckResult(
                    name="C6-policy-structured-error",
                    passed=True,
                    detail="delete_supplier returned policy/non-retryable error",
                    lesson_ref="lesson.md §structured_errors"
                )

            except json.JSONDecodeError as e:
                return CheckResult(
                    name="C6-policy-structured-error",
                    passed=False,
                    detail=f"Could not parse error JSON: {e}",
                    lesson_ref="lesson.md §structured_errors"
                )

    return CheckResult(
        name="C6-policy-structured-error",
        passed=False,
        detail="Could not extract error structure from result",
        lesson_ref="lesson.md §structured_errors"
    )
