"""Checks for module 01: agentic-loop — static (AST) criteria C1 and C3."""

import ast
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult


def check_c1_stop_reason(ctx: CheckContext) -> CheckResult:
    """C1-stop-reason: Verify loop exits on stop_reason == 'end_turn'."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C1-stop-reason",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §stop_reason"
        )

    try:
        with open(agent_py) as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError as e:
        return CheckResult(
            name="C1-stop-reason",
            passed=False,
            detail=f"agent.py syntax error: {e}",
            lesson_ref="lesson.md §stop_reason"
        )

    # Look for comparison of stop_reason with "end_turn"
    found_stop_reason_check = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            left_str = ast.unparse(node.left)
            if "stop_reason" in left_str:
                for comparator in node.comparators:
                    comp_str = ast.unparse(comparator)
                    if "end_turn" in comp_str:
                        found_stop_reason_check = True
                        break

    if not found_stop_reason_check:
        return CheckResult(
            name="C1-stop-reason",
            passed=False,
            detail="No comparison of stop_reason with 'end_turn' found in source",
            lesson_ref="lesson.md §stop_reason"
        )

    return CheckResult(
        name="C1-stop-reason",
        passed=True,
        detail="Found stop_reason == 'end_turn' check in loop",
        lesson_ref="lesson.md §stop_reason"
    )


def check_c3_no_iteration_cap(ctx: CheckContext) -> CheckResult:
    """C3-no-iteration-cap: Verify no numeric counter forms outer loop."""
    workspace = ctx.workspace
    agent_py = workspace / "agent.py"

    if not agent_py.exists():
        return CheckResult(
            name="C3-no-iteration-cap",
            passed=False,
            detail="agent.py not found in workspace",
            lesson_ref="lesson.md §anti_patterns"
        )

    try:
        with open(agent_py) as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError as e:
        return CheckResult(
            name="C3-no-iteration-cap",
            passed=False,
            detail=f"agent.py syntax error: {e}",
            lesson_ref="lesson.md §anti_patterns"
        )

    # The agent must contain a loop at all; the starter skeleton has none.
    loops = [n for n in ast.walk(tree) if isinstance(n, (ast.While, ast.For))]
    if not loops:
        return CheckResult(
            name="C3-no-iteration-cap",
            passed=False,
            detail="No agentic loop found in agent.py",
            lesson_ref="lesson.md §anti_patterns"
        )

    # A for-range loop that wraps the API call is an iteration cap as primary stop
    for node in loops:
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call) \
                and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
            calls_api = any(
                isinstance(c, ast.Attribute) and c.attr == "create"
                for c in ast.walk(node)
            )
            if calls_api:
                return CheckResult(
                    name="C3-no-iteration-cap",
                    passed=False,
                    detail=(
                        "The API-calling loop is a for-range loop — "
                        "iteration count is the primary stop"
                    ),
                    lesson_ref="lesson.md §anti_patterns"
                )

    # Find while True loops that contain a nested for-range
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        if isinstance(child.iter, ast.Call):
                            if (isinstance(child.iter.func, ast.Name)
                                    and child.iter.func.id == "range"):
                                return CheckResult(
                                    name="C3-no-iteration-cap",
                                    passed=False,
                                    detail=(
                                        "Found for i in range(N) loop "
                                        "inside while True loop"
                                    ),
                                    lesson_ref="lesson.md §anti_patterns"
                                )

    return CheckResult(
        name="C3-no-iteration-cap",
        passed=True,
        detail="No numeric counter-based outer loop detected",
        lesson_ref="lesson.md §anti_patterns"
    )
