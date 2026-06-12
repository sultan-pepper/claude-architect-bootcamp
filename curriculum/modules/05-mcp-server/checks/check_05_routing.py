"""Check for module 05: Tool description routing quality."""

import importlib.util
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult
from bootcamp_cli.judge import judge, JudgeError

_spec = importlib.util.spec_from_file_location(
    "m05_mcp_probe", str(Path(__file__).parent / "mcp_probe.py"))
assert _spec is not None and _spec.loader is not None
_probe_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_probe_mod)
_probe_mcp_server = _probe_mod._probe_mcp_server


def check_c3_description_routing(ctx: CheckContext) -> CheckResult:
    """C3-description-routing: judge evaluates tool descriptions for routing quality."""
    results, error = _probe_mcp_server(ctx.workspace, ctx.fixtures)

    if error:
        return CheckResult(
            name="C3-description-routing",
            passed=False,
            detail=f"Failed to start server: {error}",
            lesson_ref="lesson.md §description_as_routing"
        )

    tools = results.get("tools", [])
    if len(tools) < 2:
        return CheckResult(
            name="C3-description-routing",
            passed=False,
            detail="Not enough tools to evaluate routing",
            lesson_ref="lesson.md §description_as_routing"
        )

    # Format tool descriptions for judge
    tools_text = "Tools:\n"
    for tool in tools:
        name = getattr(tool, "name", "unknown")
        desc = getattr(tool, "description", "") or ""
        tools_text += f"- {name}: {desc}\n"

    scenarios = """
Routing scenarios:
1. "Show me all products from supplier 1" → should route to list_supplier_products
2. "Find products with the name 'widget'" → should route to search_products
3. "What's the stock level for SKU GADGET-001?" → should route to get_stock_level
    """

    artifact = tools_text + "\n" + scenarios
    rubric = """Tool descriptions are clear and distinct enough that an LLM would correctly route these three scenarios without ambiguity. Each description states: which routing scenario(s) it handles, which scenario(s) it does NOT handle, whether empty results return a value (vs error)."""

    try:
        verdict = judge("C3-description-routing", rubric, artifact)
        if not verdict.passed:
            return CheckResult(
                name="C3-description-routing",
                passed=False,
                detail=f"Tool descriptions not sufficiently distinct: {verdict.reasoning}",
                lesson_ref="lesson.md §description_as_routing"
            )

        return CheckResult(
            name="C3-description-routing",
            passed=True,
            detail="Tool descriptions are clear and distinct for routing",
            lesson_ref="lesson.md §description_as_routing"
        )

    except JudgeError as e:
        return CheckResult(
            name="C3-description-routing",
            passed=False,
            detail=f"judge unavailable: {e}",
            lesson_ref="lesson.md §description_as_routing"
        )
