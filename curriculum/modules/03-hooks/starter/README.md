# M03 workspace — Hooks and lifecycle

## Entry point

`agent.py` — same contract as M01.

## Contract

Implement and export (same signature as M01):

```python
def run_conversation(user_messages: list[str]) -> dict:
    ...
```

Returns `{"response": str, "transcript": list[dict]}` where all `tool_result`
content strings in the transcript reflect post-hook normalised backend data
(ISO-8601 timestamps, title-case statuses).

## Starting point

Option A: copy your completed M01 `agent.py` here and add hooks.
Option B: use this skeleton, which has the same structure as M01 plus hook stubs.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model for API calls |
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `FIXTURES_PATH` | `../fixtures` | Absolute path to this module's fixtures/ dir |
| `EXTRA_SYSTEM_PROMPT` | `""` | Appended to base system prompt at call time (used by adversarial check) |

`EXTRA_SYSTEM_PROMPT` must be read inside `run_conversation`, not at module
import time, so the checker can set it between calls.

## What this module adds to M01

1. **`pre_tool_use(name, inputs)`** — called before every backend invocation.
   Must intercept `process_refund` calls with `amount > 500.0` and redirect to
   `escalate_to_human`. Must return `None` for all other calls to allow them.

2. **`normalise_result(value, key="")`** — called on every backend return value
   before it is serialised into `tool_result` content. Must convert Unix-epoch
   integer timestamps to ISO-8601 and normalise `status` strings to title-case.
   Must recurse into dicts and lists.

## Fixtures

`$FIXTURES_PATH/support_backend.py` — same as M01. Order O004 has
`subtotal: 700.00` — the adversarial refund test order.

Module-level `support_backend.REFUND_LOG` and `support_backend.ESCALATION_LOG`
are reset by the checker before each test run.

## Checks

```bash
bootcamp check   # runs all four criteria
bootcamp hint    # unlock hints one level at a time (requires a failed check run first)
```
