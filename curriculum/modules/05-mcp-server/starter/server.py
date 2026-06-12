"""M05 — MCP server design: inventory management server skeleton.

Fill every TODO. Do not change the file name or the __main__ block.
Do not print anything to stdout other than MCP protocol frames.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_fixtures_path = Path(os.environ.get("FIXTURES_PATH", Path(__file__).parent.parent / "fixtures"))
_default_db = _fixtures_path / "inventory.sqlite3"
DB_PATH = Path(os.environ.get("GROCERY_DB_PATH", str(_default_db)))

# Fault injection: set INVENTORY_SIMULATE=timeout to force transient errors.
SIMULATE = os.environ.get("INVENTORY_SIMULATE", "")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """Open a read-write connection to the inventory database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert sqlite3.Row objects to plain dicts."""
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Structured error helper
# ---------------------------------------------------------------------------
def tool_error(
    message: str,
    error_category: str,
    is_retryable: bool,
    detail: str | None = None,
) -> list[types.TextContent]:
    """Build error content body. Return alongside isError=True in CallToolResult."""
    body: dict[str, Any] = {
        "error": message,
        "errorCategory": error_category,
        "isRetryable": is_retryable,
    }
    if detail:
        body["detail"] = detail
    return [types.TextContent(type="text", text=json.dumps(body))]


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
server = Server("inventory")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Register all tools. Write descriptions precise enough for unambiguous routing."""
    return [
        # TODO: define ≥3 tools with distinct, precise descriptions.
        #
        # Required tools (implement all four):
        #
        # types.Tool(
        #     name="search_products",
        #     description=(
        #         # TODO: write a description that:
        #         #   1. States what it does (search by name/SKU substring)
        #         #   2. States what is returned (list, possibly empty — NOT an error)
        #         #   3. States when to use it vs sibling tools (not for supplier filtering)
        #     ),
        #     inputSchema={
        #         "type": "object",
        #         "properties": {
        #             "query": {"type": "string", "description": "TODO"}
        #         },
        #         "required": ["query"],
        #     },
        # ),
        #
        # TODO: get_stock_level(sku: str)
        # TODO: list_supplier_products(supplier_id: int)
        # TODO: delete_supplier(supplier_id: int)
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
    """Dispatch tool calls. Handle fault injection and structured errors."""

    # Fault injection — check before any database access
    if SIMULATE == "timeout":
        # TODO: return a structured transient/retryable error
        # errorCategory must be "transient", isRetryable must be true
        raise NotImplementedError("TODO: return transient error when SIMULATE==timeout")

    # TODO: dispatch to individual handlers based on `name`
    # Each handler should return types.CallToolResult
    # Errors: use tool_error() + isError=True
    # Empty results: return normal result with empty list (never isError)

    raise NotImplementedError(f"Tool not implemented: {name}")


# ---------------------------------------------------------------------------
# Tool handlers — implement each one
# ---------------------------------------------------------------------------

def handle_search_products(query: str) -> types.CallToolResult:
    """Search products by name or SKU substring. Returns empty list on no match."""
    # TODO: SELECT products.*, stock_levels.quantity_on_hand
    #       FROM products JOIN stock_levels ON products.id = stock_levels.product_id
    #       WHERE products.name LIKE ? OR products.sku LIKE ?
    # Return CallToolResult with content=JSON list. Empty list is valid — NOT an error.
    raise NotImplementedError("TODO: implement search_products")


def handle_get_stock_level(sku: str) -> types.CallToolResult:
    """Get stock level for an exact SKU. Zero stock is a valid result, not an error."""
    # TODO: SELECT products.*, stock_levels.quantity_on_hand
    #       WHERE products.sku = ?
    # If quantity_on_hand = 0, return the record with quantity 0 — do NOT return isError.
    raise NotImplementedError("TODO: implement get_stock_level")


def handle_list_supplier_products(supplier_id: int) -> types.CallToolResult:
    """List all products for a given supplier id."""
    # TODO: SELECT * FROM products WHERE supplier_id = ?
    raise NotImplementedError("TODO: implement list_supplier_products")


def handle_delete_supplier(supplier_id: int) -> types.CallToolResult:
    """Delete a supplier. Fails with business error if the supplier has active products."""
    # TODO:
    # 1. Check: SELECT COUNT(*) FROM products WHERE supplier_id = ?
    # 2. If count > 0: return tool_error(..., "business", False) with isError=True
    # 3. If count == 0: DELETE FROM suppliers WHERE id = ?; return success
    raise NotImplementedError("TODO: implement delete_supplier")


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.list_resources()
async def list_resources() -> list[types.Resource]:
    """Register resources. At least one required."""
    return [
        # TODO: define ≥1 resource, e.g.:
        # types.Resource(
        #     uri="inventory://products",
        #     name="Product catalog",
        #     description="TODO: write a description",
        #     mimeType="application/json",
        # ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Return resource content for the given URI."""
    # TODO: dispatch on uri and return JSON string
    raise NotImplementedError(f"Resource not implemented: {uri}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
