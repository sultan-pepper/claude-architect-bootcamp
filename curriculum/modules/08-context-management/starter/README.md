# M08 workspace — Context management

## Deliverables

One file: `agent.py`. Copy your M03 `agent.py` here as a starting point (or use the skeleton below). The checks import it and call `run_conversation` directly.

## Entry point

```python
def run_conversation(user_messages: list[str]) -> dict:
    ...
```

Same signature as M01/M03. Return shape is extended with an optional `handoff` field.

## Return shape

```json
{
  "response":  "final assistant text",
  "transcript": [...],
  "handoff": {
    "customer_id":        "C001",
    "root_cause":         "...",
    "amount":             768.99,
    "recommended_action": "..."
  }
}
```

`handoff` is present **only** when `escalate_to_human` is called. Absent (not null) when no escalation occurs.

`tool_result` content strings in the transcript must contain the trimmed (not raw) order records.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model for all API calls |
| `ANTHROPIC_API_KEY` | (required) | API key |
| `FIXTURES_PATH` | `../fixtures` | Path to this module's fixtures/ directory |
| `EXTRA_SYSTEM_PROMPT` | (empty) | Appended to system prompt (adversarial check from M03) |

## Running manually

```bash
echo '["Hi, I need to check on order O001"]' | python agent.py

# Drive one turn of the 30-turn script:
echo '["I need to return order O004 for a full refund"]' | python agent.py
```

## Checks

```bash
bootcamp check   # runs all three criteria
bootcamp hint    # unlock hints one level at a time (requires a failed check run first)
```
