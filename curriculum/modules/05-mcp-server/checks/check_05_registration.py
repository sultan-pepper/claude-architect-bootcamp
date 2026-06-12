"""Checks for module 05: MCP server registration."""

import importlib.util
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult

_spec = importlib.util.spec_from_file_location(
    "m05_mcp_probe", str(Path(__file__).parent / "mcp_probe.py"))
assert _spec is not None and _spec.loader is not None
_probe_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_probe_mod)
_probe_mcp_server = _probe_mod._probe_mcp_server


def check_c1_tools_registered(ctx: CheckContext) -> CheckResult:
    """C1-tools-registered: tools/list returns ≥3 tools."""
    results, error = _probe_mcp_server(ctx.workspace, ctx.fixtures)

    if error:
        return CheckResult(
            name="C1-tools-registered",
            passed=False,
            detail=f"Failed to start server: {error}",
            lesson_ref="lesson.md §splitting_tools"
        )

    tools = results.get("tools", [])
    if len(tools) < 3:
        return CheckResult(
            name="C1-tools-registered",
            passed=False,
            detail=f"Server returned {len(tools)} tools; need ≥3",
            lesson_ref="lesson.md §splitting_tools"
        )

    return CheckResult(
        name="C1-tools-registered",
        passed=True,
        detail=f"Server registered {len(tools)} tools",
        lesson_ref="lesson.md §splitting_tools"
    )


def check_c2_resources_registered(ctx: CheckContext) -> CheckResult:
    """C2-resources-registered: resources/list returns ≥1 resource."""
    results, error = _probe_mcp_server(ctx.workspace, ctx.fixtures)

    if error:
        return CheckResult(
            name="C2-resources-registered",
            passed=False,
            detail=f"Failed to start server: {error}",
            lesson_ref="lesson.md §tools_vs_resources"
        )

    resources = results.get("resources", [])
    if len(resources) < 1:
        return CheckResult(
            name="C2-resources-registered",
            passed=False,
            detail="Server returned no resources; need ≥1",
            lesson_ref="lesson.md §tools_vs_resources"
        )

    return CheckResult(
        name="C2-resources-registered",
        passed=True,
        detail=f"Server registered {len(resources)} resource(s)",
        lesson_ref="lesson.md §tools_vs_resources"
    )
