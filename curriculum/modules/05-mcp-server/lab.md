# Lab 05 — MCP server design

## Mission

Build a real MCP server (stdio transport, Python `mcp` package) that exposes an inventory management backend as a set of tools and resources. The server must demonstrate: description quality sufficient for unambiguous routing, split tools with distinct descriptions, structured errors with correct categories and retryability, empty results returned correctly (not as errors), and project scoping via `.mcp.json` with env-var expansion.

## Workspace entry-point contract

**Files:**
- `workspace/server.py` — the MCP server; the checker launches it as `python server.py` from the workspace directory.
- `workspace/.mcp.json` — project MCP configuration.

**Server transport:** stdio. The server must read from stdin and write to stdout using the `mcp` package's `stdio_server` context manager. It must not print anything to stdout other than MCP protocol frames.

**Database path:** read from env `GROCERY_DB_PATH`; fall back to `fixtures/inventory.sqlite3` (relative to the workspace's `fixtures/` directory — the checker sets `FIXTURES_PATH` env var). Using your own SQLite database via `GROCERY_DB_PATH` is encouraged as the higher-value learning path; all checks run against the fixture DB when `GROCERY_DB_PATH` is not set.

**Fault injection:** when env `INVENTORY_SIMULATE=timeout` is set, every tool call must return a structured transient/retryable error (see C5). The server must check this env var on every call, not just at startup.

## Deliverables

### `workspace/server.py`

An async MCP server using the `mcp` package. Minimum surface:

**Tools (≥3 required, distinct descriptions required):**

Implement at minimum:

- `search_products(query: str)` — search products by name or SKU substring; return matching products with stock levels; return empty list on no match (never error)
- `get_stock_level(sku: str)` — return current stock level for an exact SKU; return zero-quantity record for out-of-stock items (never error for valid SKU)
- `list_supplier_products(supplier_id: int)` — list all products for a supplier by integer id
- `delete_supplier(supplier_id: int)` — delete a supplier; must return a business/non-retryable error if the supplier has any products associated with it

Tool descriptions must be precise enough that an LLM would route "find products with low stock" to `search_products` or a dedicated `list_low_stock` tool, and "show me all products from supplier 1" to `list_supplier_products`, not `search_products`.

**Resources (≥1 required):**

Expose at least one resource accessible via `resources/list`. Example: `inventory://products` returning the full product catalog as JSON, or `inventory://suppliers` returning the supplier list.

**Structured errors:**

For error returns, set `isError=True` at the MCP protocol level and include a JSON body in the content text with at minimum:

```json
{
  "error": "<human-readable message>",
  "errorCategory": "<business|transient|validation|permission>",
  "isRetryable": <true|false>
}
```

### `workspace/.mcp.json`

```json
{
  "mcpServers": {
    "inventory": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "GROCERY_DB_PATH": "${GROCERY_DB_PATH}"
      }
    }
  }
}
```

The `${GROCERY_DB_PATH}` env-var expansion syntax is required (C7 checks for it). Additional env vars (`INVENTORY_SIMULATE`, etc.) may be added.

## Fixtures available

`fixtures/inventory.sqlite3` — SQLite database with three tables:

**`suppliers`** (5 rows): id, name, country, contact_email. Supplier id=1 is "TechCorp Industries" (USA). Supplier id=2 is "Global Trade Ltd" (China).

**`products`** (15 rows): id, name, sku, category, price, supplier_id. Includes unicode names (Japanese, Chinese characters). Supplier id=1 has 4 products; supplier id=2 has 3 products.

**`stock_levels`** (15 rows): id, product_id, quantity_on_hand, reorder_point, last_updated. Four products have `quantity_on_hand=0`:
- SKU `GADGET-001` ("Deluxe Gadget (型号)") — quantity 0
- SKU `BELT-001` ("Industrial Belt (業務用)") — quantity 0
- SKU `COOL-001` ("Water Cooling Unit (冷却)") — quantity 0
- SKU `FILTER-001` ("Replacement Filter (フィルター)") — quantity 0

These zero-stock items are the probe for C4: a call for any of these must return a result (with quantity 0), not an error.

To use your own database, set `GROCERY_DB_PATH` to the path of an SQLite file with the same schema. The schema is in `fixtures/make_inventory.py`.

## What `bootcamp check` does

The checker starts `python server.py` as a subprocess and communicates with it using the MCP client protocol. The fixture database is used unless `GROCERY_DB_PATH` is set.

1. **C1-tools-registered**: sends `tools/list` to the server; verifies ≥3 tools are returned.

2. **C2-resources-registered**: sends `resources/list` to the server; verifies ≥1 resource is returned.

3. **C3-description-routing** (judge): passes the tool list (names + descriptions) to the judge with a set of routing scenarios (e.g., "user asks for products from a specific supplier", "user wants to find a product by partial name"). The judge evaluates whether the descriptions are distinct enough to route each scenario correctly.

4. **C4-empty-not-error**: calls `get_stock_level(sku="GADGET-001")` (quantity 0 in fixture); verifies the response has `isError` absent or false and the content includes a non-error result with quantity 0.

5. **C5-timeout-structured-error**: launches server with `INVENTORY_SIMULATE=timeout`; calls `search_products(query="widget")`; verifies the response has `isError=True` and the content JSON contains `errorCategory="transient"` and `isRetryable=true`.

6. **C6-policy-structured-error**: calls `delete_supplier(supplier_id=1)` (TechCorp Industries — has 4 active products); verifies the response has `isError=True` and the content JSON contains `isRetryable=false`.

7. **C7-mcp-json-valid**: parses `workspace/.mcp.json`; verifies it is valid JSON with a `mcpServers` key; verifies at least one server entry's `env` block contains a value with `${...}` env-var expansion syntax.

## Acceptance criteria

C1 through C7 must all pass.

The judge for C3 uses the tool descriptions you write — not fixed keywords. Descriptions that are generic ("search inventory", "get product") fail. Descriptions that state routing boundaries explicitly ("use when the user specifies a supplier by id", "returns empty list when no match — not an error") pass.

Recommended: read the fixture data before writing descriptions. The product and supplier names are in `fixtures/README.md`.
