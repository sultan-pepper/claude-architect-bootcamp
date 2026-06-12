# M01 workspace — The agentic loop

## Entry point

`agent.py` — this is the only file the checks interact with.

## Contract

Implement and export:

```python
def run_conversation(user_messages: list[str]) -> dict:
    ...
```

Returns `{"response": str, "transcript": list[dict]}` where `transcript` is the
full `messages` list accumulated during the loop (initial user turn through final
assistant turn, including all tool_use and tool_result turns).

When run as `__main__`, reads a JSON array of strings from stdin, calls
`run_conversation`, and writes the result dict as JSON to stdout.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model to use for API calls |
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `FIXTURES_PATH` | `../fixtures` | Absolute path to the module's fixtures/ dir |

## Fixtures

The mock backend is at `$FIXTURES_PATH/support_backend.py`. Import it by
inserting the fixtures path into `sys.path`:

```python
import os, sys
sys.path.insert(0, os.environ.get("FIXTURES_PATH", "../fixtures"))
import support_backend
```

## Running manually

```bash
echo '["I need help with order O001"]' | python agent.py
```

## Checks

```bash
bootcamp check   # runs all four criteria
bootcamp hint    # unlock hints one level at a time (requires a failed check run first)
```
