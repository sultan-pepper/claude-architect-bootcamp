# M05 workspace — MCP server design

## Entry points

| File | Role |
|---|---|
| `server.py` | MCP server — the checker launches this as `python server.py` |
| `.mcp.json` | Project MCP config — project-scopes the server for Claude Code |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `GROCERY_DB_PATH` | `$FIXTURES_PATH/inventory.sqlite3` | Path to inventory SQLite database |
| `INVENTORY_SIMULATE` | `""` | Set to `timeout` to force transient error responses |
| `FIXTURES_PATH` | set by checker | Absolute path to `fixtures/` directory |

Using your own SQLite database via `GROCERY_DB_PATH` is the higher-value learning path —
the fixture database is the fallback for checks, not the ceiling for your design.

## Implementing the server

Fill every `# TODO` in `server.py`. Do not change the file name or the `__main__` block.

The server must:
- Register ≥3 tools with distinct, precise descriptions (see lesson.md §description_as_routing)
- Register ≥1 resource listable via `resources/list`
- Return structured errors with `errorCategory` and `isRetryable` in the JSON content body, `isError=True` at protocol level
- Return an empty result (NOT an error) for zero-stock products
- Honour `INVENTORY_SIMULATE=timeout` with a transient/retryable error
- Enforce the policy: cannot delete a supplier with active products (business/non-retryable error)

## Running manually

```bash
# Start the server (blocks on stdin waiting for MCP protocol frames)
python server.py

# Or test via the MCP inspector (if installed)
npx @modelcontextprotocol/inspector python server.py
```

## Installing the mcp package

```bash
pip install mcp
```

## Checks

```bash
bootcamp check    # runs C1–C7
bootcamp hint     # unlock hints one level at a time (requires a failed check run first)
```
