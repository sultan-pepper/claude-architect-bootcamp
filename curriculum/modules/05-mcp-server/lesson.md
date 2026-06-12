# Lesson 05 — MCP server design

MCP (Model Context Protocol) is a protocol for connecting Claude to external data sources and capabilities. A server exposes a typed interface; Claude discovers it at session start and uses it at runtime. Getting the design right — what to expose as a tool versus a resource, how to write descriptions, how to signal errors — determines whether Claude routes correctly without additional instructions.

## tools_vs_resources

MCP exposes two primitives:

**Tools** are callable functions with typed input schemas. Claude selects a tool based on its name and description, provides arguments, and the server executes the operation and returns content. Tools are appropriate for:

- Data retrieval that requires parameters (search by name fragment, lookup by id, list by threshold)
- Operations with side effects (insert, delete, update)
- Derived computations (stock valuation, reorder recommendation)

**Resources** are URI-addressed content served on request. A resource is a stable content reference: a product catalog, a supplier list, a configuration document. Resources appear in Claude's resource browser and can be attached to context explicitly. Resources are appropriate for:

- Read-only content that is stable between calls
- Catalog-style data useful as ambient reference (full product list, supplier directory)
- Large context blobs that a user might drag into a conversation

The split matters because tools add to Claude's action space and resources add to its information space. "List all suppliers" is better as a resource `inventory://suppliers` — the content is stable and the model can reference it without deciding when to call a function. "Find products below reorder point" is better as a tool — it takes a threshold parameter and returns derived state that varies by call.

Do not expose everything as a tool. A tool that takes no parameters and returns static content is a resource wearing tool clothing: it wastes the model's action space and produces inconsistent routing.

## description_as_routing

Claude selects which tool to call based solely on the tool's description. There is no hardcoded routing and no disambiguation step. If two tools have overlapping descriptions, routing is ambiguous.

A good tool description does four things:

1. States what the tool does in one sentence.
2. Specifies what the parameters mean in domain terms, not implementation terms.
3. States what is returned, including the empty case.
4. Distinguishes from sibling tools if the boundary is not obvious.

```python
# Bad description — ambiguous and underdetermined
types.Tool(
    name="search_inventory",
    description="Search the inventory",
    inputSchema={...}
)

# Good description — routes correctly, handles the empty case explicitly
types.Tool(
    name="search_products",
    description=(
        "Search products by name or SKU substring. "
        "Returns a list of matching products with current stock levels. "
        "Use when the user provides a product name or partial SKU. "
        "Returns an empty list when no products match — this is not an error. "
        "Do not use for filtering by supplier; use list_supplier_products instead."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Name or SKU fragment to search for"}
        },
        "required": ["query"]
    }
)
```

The sentence "Use when..." is explicit routing guidance. Write it when the boundary between tools could be misread. The sentence "Do not use for..." is negative routing guidance — write it when a sibling tool handles a case that looks similar.

## splitting_tools

A single `query(text: str)` tool that does everything is wrong. It forces the model to encode domain semantics into a freeform string, which it does inconsistently. It also produces descriptions that cannot avoid ambiguity because the ambiguity is in the tool itself.

Split tools on what varies structurally in the operation:

- **Different identifier types**: a lookup by exact SKU is structurally distinct from a fuzzy name search. Split them.
- **Different return shapes**: a function that returns a product's metadata is different from one that returns its stock level. If callers always want both together, merge them; if they often want only one, split them.
- **Different scope of traversal**: searching across all products is different from listing products for a specific supplier. Split them.

After splitting, each tool is narrow, its description is precise, and routing is deterministic because there is nothing to misroute.

When two tools could plausibly serve the same query — "show me products from TechCorp" could go to `list_supplier_products` or `search_products` — both descriptions must state the boundary explicitly. `list_supplier_products` description: "Use when the user specifies a supplier by name and wants all products associated with that supplier." `search_products` description: "Use when the user provides a product name or SKU fragment; does not filter by supplier."

## structured_errors

When a tool call fails, the response must convey: what failed, why, and whether the caller should try again. MCP uses the `isError` flag on the tool result to signal failure at the protocol level. The content body carries the structured detail:

```python
def error_response(
    message: str,
    error_category: str,   # "business" | "transient" | "validation" | "permission"
    is_retryable: bool,
    detail: str | None = None,
) -> dict:
    return {
        "error": message,
        "errorCategory": error_category,
        "isRetryable": is_retryable,
        "detail": detail,
    }
```

Return this dict as the text content of the tool result with `isError=True` set at the MCP level so protocol consumers see the failure without parsing the content body.

Four error categories:

- **`business`**: the operation violates a domain rule. Not retryable. Example: deleting a supplier that has active products. The constraint is in the domain; retrying the same request produces the same failure. The fix requires a different operation (reassign or remove the supplier's products first).
- **`transient`**: infrastructure-level failure — timeout, connection error, temporary lock. Always `isRetryable: true`. The same request may succeed on the next attempt.
- **`validation`**: the input does not conform to the schema — negative quantity, malformed SKU, missing required field. Not retryable without input correction.
- **`permission`**: the caller lacks authorization. `isRetryable: false` unless the permission can be obtained externally.

`isRetryable` is a machine-readable signal. Orchestrators and Claude use it to decide whether to retry automatically, surface the error to the user, or request a different operation. Getting it wrong produces incorrect orchestration: a `business` error marked `isRetryable: true` will be retried indefinitely.

## empty_result_not_error

An empty query result is not an error. If a product search returns no matches, the correct response is an empty list with `isError` absent or false. If a product exists but has zero stock, the correct response is the product record with `quantity_on_hand: 0`.

```python
# Correct: zero-stock product found, query valid
return [types.TextContent(type="text", text=json.dumps({
    "products": [{"sku": "GADGET-001", "name": "Deluxe Gadget", "quantity_on_hand": 0}]
}))]

# Wrong: treating empty result as error
return CallToolResult(
    content=[types.TextContent(type="text", text=json.dumps({
        "error": "No stock found",
        "errorCategory": "business",
        "isRetryable": False,
    }))],
    isError=True  # WRONG — query was valid
)
```

The failure mode is returning an error when the query ran correctly and simply produced an empty result. This breaks orchestration because the caller cannot distinguish "query failed" from "query succeeded, nothing matched". An empty list or a zero-quantity record tells the model exactly what happened: the operation completed, the answer is empty.

Reserve `isError: True` for genuine failures: database unreachable, malformed input, prohibited operation. A valid query returning zero results is not a failure.

## mcp_json

`.mcp.json` scopes an MCP server to the project:

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

The `"command"` and `"args"` specify how Claude Code launches the server process. The server runs as a child process; Claude communicates with it over stdio.

`"${GROCERY_DB_PATH}"` expands the environment variable at Claude Code launch time. This allows the database path to vary per developer or environment without editing the config file. If the variable is unset, the server should fall back to a default (e.g., the fixture DB path). Document the expected env vars in the server's help text or README.

Contrast with `~/.claude.json` — a user-level config that applies to every Claude Code session on the machine, regardless of project. Use `.mcp.json` (committed to the repo) for servers that are part of this project's development workflow. Use `~/.claude.json` for personal servers: a note-taking integration, a calendar lookup, a personal reference database. Project servers belong in the project; personal servers belong to the user.

The `env` block in `.mcp.json` is the correct place for env-var expansion. Hardcoding paths in `args` makes the config non-portable across developer machines.
