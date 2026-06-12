"""Shared MCP client probe for module 05 checks. Not a check file."""
import asyncio
import os
import sys
from pathlib import Path
from typing import Any


async def _probe_async(workspace: Path, fixtures: Path,
                       env_overrides: dict[str, str] | None = None) -> dict[str, Any]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = os.environ.copy()
    env["FIXTURES_PATH"] = str(fixtures)
    env.pop("GROCERY_DB_PATH", None)  # checks always run against the fixture DB
    if env_overrides:
        env.update(env_overrides)

    params = StdioServerParameters(
        command=sys.executable, args=["server.py"], cwd=str(workspace), env=env)

    results: dict[str, Any] = {}
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            results["tools"] = list(tools.tools)
            try:
                resources = await session.list_resources()
                results["resources"] = list(resources.resources)
            except Exception:
                results["resources"] = []
            for key, name, args in (
                ("stock", "get_stock_level", {"sku": "GADGET-001"}),
                ("search", "search_products", {"query": "widget"}),
                ("delete", "delete_supplier", {"supplier_id": 1}),
            ):
                try:
                    results[f"{key}_call"] = await session.call_tool(name, args)
                except Exception as exc:
                    results[f"{key}_error"] = str(exc)
    return results


def _probe_mcp_server(workspace: Path, fixtures: Path,
                      env_overrides: dict[str, str] | None = None
                      ) -> tuple[dict[str, Any], Exception | None]:
    """Launch the learner's server.py over stdio and run the standard probes."""
    if not (workspace / "server.py").exists():
        return {}, Exception("server.py not found in workspace")
    try:
        return asyncio.run(
            asyncio.wait_for(_probe_async(workspace, fixtures, env_overrides),
                             timeout=45)), None
    except Exception as exc:
        return {}, exc
