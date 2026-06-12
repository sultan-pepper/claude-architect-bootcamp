"""M05 reference solution — inventory MCP server over stdio."""

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

_fixtures_path = Path(os.environ.get("FIXTURES_PATH", Path(__file__).parent.parent / "fixtures"))
_default_db = _fixtures_path / "inventory.sqlite3"
DB_PATH = Path(os.environ.get("GROCERY_DB_PATH", str(_default_db)))

SIMULATE = os.environ.get("INVENTORY_SIMULATE", "")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def ok(payload: Any) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(payload))],
        isError=False,
    )


def tool_error(message: str, error_category: str, is_retryable: bool,
               detail: str | None = None) -> types.CallToolResult:
    body: dict[str, Any] = {
        "error": message,
        "errorCategory": error_category,
        "isRetryable": is_retryable,
    }
    if detail:
        body["detail"] = detail
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(body))],
        isError=True,
    )


server = Server("inventory")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_products",
            description=(
                "Search the product catalog by free-text substring match against "
                "product name or SKU. Returns a list of matching products with their "
                "current stock levels. Returns an empty list when nothing matches — "
                "an empty result is a valid answer, not an error. Do NOT use this to "
                "filter by supplier (use list_supplier_products) or to look up one "
                "exact SKU's stock (use get_stock_level)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string",
                              "description": "Substring to match against product name or SKU."}
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_stock_level",
            description=(
                "Return the current stock record for ONE exact SKU. Use when the user "
                "names a specific SKU and wants its quantity on hand. A quantity of 0 "
                "is a valid in-catalog answer (out of stock), returned normally — not "
                "an error. Not for free-text search (use search_products)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Exact SKU, e.g. GADGET-001."}
                },
                "required": ["sku"],
            },
        ),
        types.Tool(
            name="list_supplier_products",
            description=(
                "List every product supplied by one supplier, identified by numeric "
                "supplier id. Use when the user specifies a supplier ('all products "
                "from supplier 1'). Returns an empty list for a supplier with no "
                "products — not an error. Not for name/SKU search (use search_products)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "supplier_id": {"type": "integer", "description": "Numeric supplier id."}
                },
                "required": ["supplier_id"],
            },
        ),
        types.Tool(
            name="delete_supplier",
            description=(
                "Permanently delete a supplier record by numeric id. Fails with a "
                "non-retryable business error if the supplier still has products "
                "associated with it — reassign or remove those products first. Only "
                "use when the user explicitly asks to remove a supplier."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "supplier_id": {"type": "integer", "description": "Numeric supplier id."}
                },
                "required": ["supplier_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
    if SIMULATE == "timeout":
        return tool_error(
            "Backend timed out while contacting the inventory database.",
            "transient", True,
            detail="The operation may succeed if retried.",
        )

    try:
        if name == "search_products":
            return handle_search_products(str(arguments["query"]))
        if name == "get_stock_level":
            return handle_get_stock_level(str(arguments["sku"]))
        if name == "list_supplier_products":
            return handle_list_supplier_products(int(arguments["supplier_id"]))
        if name == "delete_supplier":
            return handle_delete_supplier(int(arguments["supplier_id"]))
    except (KeyError, TypeError, ValueError) as exc:
        return tool_error(f"Invalid arguments: {exc}", "validation", False)
    except sqlite3.OperationalError as exc:
        return tool_error(f"Database unavailable: {exc}", "transient", True)

    return tool_error(f"Unknown tool: {name}", "validation", False)


def handle_search_products(query: str) -> types.CallToolResult:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT p.id, p.name, p.sku, p.category, p.price, p.supplier_id, "
            "s.quantity_on_hand FROM products p "
            "JOIN stock_levels s ON s.product_id = p.id "
            "WHERE p.name LIKE ? OR p.sku LIKE ? ORDER BY p.id",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
    finally:
        conn.close()
    return ok({"results": rows_to_dicts(rows), "count": len(rows)})


def handle_get_stock_level(sku: str) -> types.CallToolResult:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT p.sku, p.name, s.quantity_on_hand, s.reorder_point, s.last_updated "
            "FROM products p JOIN stock_levels s ON s.product_id = p.id "
            "WHERE p.sku = ?",
            (sku,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return tool_error(f"SKU {sku!r} is not in the catalog.", "validation", False)
    return ok(dict(row))


def handle_list_supplier_products(supplier_id: int) -> types.CallToolResult:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, sku, category, price FROM products "
            "WHERE supplier_id = ? ORDER BY id",
            (supplier_id,),
        ).fetchall()
    finally:
        conn.close()
    return ok({"supplier_id": supplier_id, "products": rows_to_dicts(rows),
               "count": len(rows)})


def handle_delete_supplier(supplier_id: int) -> types.CallToolResult:
    conn = get_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM products WHERE supplier_id = ?",
            (supplier_id,),
        ).fetchone()[0]
        if count > 0:
            return tool_error(
                f"Supplier {supplier_id} still has {count} product(s) associated; "
                "reassign or remove them before deleting the supplier.",
                "business", False,
            )
        conn.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
        conn.commit()
    finally:
        conn.close()
    return ok({"deleted_supplier_id": supplier_id})


@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="inventory://products",
            name="Product catalog",
            description="The full product catalog with stock levels, as JSON.",
            mimeType="application/json",
        ),
        types.Resource(
            uri="inventory://suppliers",
            name="Supplier list",
            description="All suppliers with contact details, as JSON.",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    conn = get_connection()
    try:
        if str(uri) == "inventory://products":
            rows = conn.execute(
                "SELECT p.id, p.name, p.sku, p.category, p.price, p.supplier_id, "
                "s.quantity_on_hand FROM products p "
                "JOIN stock_levels s ON s.product_id = p.id ORDER BY p.id"
            ).fetchall()
            return json.dumps(rows_to_dicts(rows))
        if str(uri) == "inventory://suppliers":
            rows = conn.execute(
                "SELECT id, name, country, contact_email FROM suppliers ORDER BY id"
            ).fetchall()
            return json.dumps(rows_to_dicts(rows))
    finally:
        conn.close()
    raise ValueError(f"Unknown resource: {uri}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
