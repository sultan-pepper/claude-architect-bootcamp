"""Checks for module 05: MCP configuration validation."""

import json
from pathlib import Path

from bootcamp_cli.checks import CheckContext, CheckResult


def check_c7_mcp_json_valid(ctx: CheckContext) -> CheckResult:
    """C7-mcp-json-valid: .mcp.json is valid JSON with env-var expansion."""
    mcp_json = ctx.workspace / ".mcp.json"

    if not mcp_json.exists():
        return CheckResult(
            name="C7-mcp-json-valid",
            passed=False,
            detail="workspace/.mcp.json not found",
            lesson_ref="lesson.md §mcp_json"
        )

    try:
        content = mcp_json.read_text()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return CheckResult(
            name="C7-mcp-json-valid",
            passed=False,
            detail=f".mcp.json is not valid JSON: {e}",
            lesson_ref="lesson.md §mcp_json"
        )
    except Exception as e:
        return CheckResult(
            name="C7-mcp-json-valid",
            passed=False,
            detail=f"Failed to read .mcp.json: {e}",
            lesson_ref="lesson.md §mcp_json"
        )

    if "mcpServers" not in data:
        return CheckResult(
            name="C7-mcp-json-valid",
            passed=False,
            detail=".mcp.json missing 'mcpServers' key",
            lesson_ref="lesson.md §mcp_json"
        )

    # Check for env-var expansion syntax ${...}
    mcp_servers = data.get("mcpServers", {})
    if not isinstance(mcp_servers, dict) or len(mcp_servers) == 0:
        return CheckResult(
            name="C7-mcp-json-valid",
            passed=False,
            detail="mcpServers is empty or not a dict",
            lesson_ref="lesson.md §mcp_json"
        )

    for server_name, server_config in mcp_servers.items():
        if not isinstance(server_config, dict):
            continue

        env_block = server_config.get("env", {})
        if not isinstance(env_block, dict):
            continue

        for env_key, env_val in env_block.items():
            if isinstance(env_val, str) and "${" in env_val and "}" in env_val:
                return CheckResult(
                    name="C7-mcp-json-valid",
                    passed=True,
                    detail=f"Found env-var expansion in {server_name}: {env_val}",
                    lesson_ref="lesson.md §mcp_json"
                )

    return CheckResult(
        name="C7-mcp-json-valid",
        passed=False,
        detail="No env-var expansion syntax found (${...})",
        lesson_ref="lesson.md §mcp_json"
    )
