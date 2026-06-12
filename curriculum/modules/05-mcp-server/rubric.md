# Rubric — 05 mcp-server

## Criteria

1. **C1-tools-registered** (deterministic): `tools/list` response from the running server contains ≥3 tool entries — lesson_ref: lesson.md §splitting_tools

2. **C2-resources-registered** (deterministic): `resources/list` response from the running server contains ≥1 resource entry — lesson_ref: lesson.md §tools_vs_resources

3. **C3-description-routing** (judge): the judge receives the full tool list (names + descriptions) and evaluates whether the descriptions distinguish the tools clearly enough that a routing scenario ("user wants products from a specific supplier by id", "user searches by partial product name", "user asks about stock for a specific SKU") would route to the correct tool without ambiguity — lesson_ref: lesson.md §description_as_routing

4. **C4-empty-not-error** (deterministic): calling `get_stock_level(sku="GADGET-001")` against the fixture DB returns a result with `isError` absent or false and includes a content body that does not contain an `"error"` key — lesson_ref: lesson.md §empty_result_not_error

5. **C5-timeout-structured-error** (deterministic): with env `INVENTORY_SIMULATE=timeout`, any tool call returns a result with `isError=True` and content body JSON containing `"errorCategory": "transient"` and `"isRetryable": true` — lesson_ref: lesson.md §structured_errors

6. **C6-policy-structured-error** (deterministic): calling `delete_supplier(supplier_id=1)` returns a result with `isError=True` and content body JSON containing `"isRetryable": false` — lesson_ref: lesson.md §structured_errors

7. **C7-mcp-json-valid** (deterministic): `workspace/.mcp.json` is valid JSON, has a `mcpServers` object key, and at least one server entry's `env` block contains a string value matching the pattern `\$\{[A-Z_]+\}` — lesson_ref: lesson.md §mcp_json

## Hints

### Level 1

There are two distinct problem areas. First: the server structure — does it register tools and resources correctly, does it start and respond to the MCP protocol? Second: the behavior on specific inputs — does a zero-stock lookup return an empty result (not error), does the timeout env var produce a structured error? Isolate which area is failing before diving into either. A server that doesn't start fails all checks; a server that starts but returns wrong error shapes fails C4–C6.

### Level 2

For C4 and C5: the shape of a correct error response in the `mcp` Python SDK is a `CallToolResult` with `isError=True` and content that is a JSON-encoded dict with `errorCategory` and `isRetryable` keys. For a correct non-error response (zero-stock case): return a `CallToolResult` with `isError` absent (or `False`) and content that is a JSON-encoded dict containing the product record including `quantity_on_hand: 0`. Do not raise an exception for the zero-stock case — exceptions become protocol-level errors.

For C6: the `delete_supplier` tool must query the database for products with `supplier_id = <arg>` before deleting. If any products exist, return a business error (`errorCategory: "business"`, `isRetryable: false`) with a human-readable message explaining the constraint.

For C7: the value `"${GROCERY_DB_PATH}"` in the `env` block is the correct syntax. The value must be a string literal containing `${...}`.

### Level 3

Structured error helper:

```python
import json
import mcp.types as types

def tool_error(message: str, category: str, retryable: bool) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({
        "error": message,
        "errorCategory": category,
        "isRetryable": retryable,
    }))]
```

Return this from the `call_tool` handler together with `isError=True` on the result.

Timeout simulation:

```python
import os

SIMULATE = os.environ.get("INVENTORY_SIMULATE", "")

async def call_tool_handler(name: str, arguments: dict):
    if SIMULATE == "timeout":
        return types.CallToolResult(
            content=tool_error("Database timeout", "transient", True),
            isError=True,
        )
    # ... normal dispatch
```

`delete_supplier` policy check:

```python
cursor.execute("SELECT COUNT(*) FROM products WHERE supplier_id = ?", (supplier_id,))
count = cursor.fetchone()[0]
if count > 0:
    return types.CallToolResult(
        content=tool_error(
            f"Supplier {supplier_id} has {count} active product(s). "
            "Reassign or delete them before removing the supplier.",
            "business",
            False,
        ),
        isError=True,
    )
```

## Mentor guardrails

- Do not write the server.py tool handlers for the learner.
- If the learner asks whether their tool descriptions are good enough, do not evaluate them directly. Ask: "Does each description state which routing scenario it handles and which it does not? Does it state what happens on an empty result?"
- If the learner asks about the MCP Python SDK API for returning errors, point to lesson.md §structured_errors and show the shape of the error dict — not the SDK call syntax.
- API-shape examples (the `types.TextContent` signature, the `CallToolResult` constructor) are allowed at ≤5 lines provided they are not specific to the inventory solution.
- Do not confirm whether a specific tool description will pass C3 — that is the judge's function, not a yes/no from the mentor.
- Do not reveal which supplier_id or SKU the checker uses for C4 and C6 (they are in the fixture README, which the learner should read).

## Reference solution sketch

**`server.py` structure:**

Imports: `asyncio`, `json`, `os`, `sqlite3`, `mcp.server`, `mcp.server.stdio`, `mcp.types`. DB connection opened per-call (or a module-level connection with WAL mode). `SIMULATE = os.environ.get("INVENTORY_SIMULATE", "")`.

**Tools (5 total):**

- `search_products(query: str)` — `SELECT products.*, stock_levels.quantity_on_hand FROM products JOIN stock_levels ON ... WHERE name LIKE ? OR sku LIKE ?`; returns list (may be empty); never errors.
- `get_stock_level(sku: str)` — exact SKU lookup including quantity; returns single record with `quantity_on_hand: 0` for zero-stock items; returns empty dict (not error) for unknown SKU if desired.
- `list_supplier_products(supplier_id: int)` — `SELECT FROM products WHERE supplier_id = ?`; returns list.
- `list_low_stock(threshold: int)` — `WHERE quantity_on_hand <= ?`; returns list; used to distinguish from `search_products`.
- `delete_supplier(supplier_id: int)` — checks `COUNT(*) WHERE supplier_id = ?`; if > 0, returns business/non-retryable error; otherwise `DELETE FROM suppliers WHERE id = ?`.

**Resources:**

- `inventory://products` — `SELECT * FROM products JOIN stock_levels ON ...`; returns full catalog as JSON.
- `inventory://suppliers` — `SELECT * FROM suppliers`; returns supplier list as JSON.

**Timeout simulation:** check `SIMULATE == "timeout"` at top of `call_tool` handler; return transient/retryable error before any DB access.

**`.mcp.json`:** `mcpServers.inventory.command = "python"`, `args = ["server.py"]`, `env = {"GROCERY_DB_PATH": "${GROCERY_DB_PATH}"}`.

Total: approximately 150–220 lines.
