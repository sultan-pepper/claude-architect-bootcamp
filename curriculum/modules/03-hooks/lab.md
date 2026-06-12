# Lab 03 — Hooks and lifecycle

## Mission

Extend the M01 customer-support agent with two hooks:

1. **PreToolUse** — intercept `process_refund` calls where `amount > 500.0` and redirect them to `escalate_to_human` instead. The backend's hard cap is $1000 (it raises `RefundError`); your $500 policy cap must live in hook code, not in the system prompt.

2. **PostToolUse** — normalise backend results before the model sees them: convert Unix-epoch integer timestamps to ISO-8601 strings, and normalise mixed-case status values to title-case.

You can copy your M01 `agent.py` as a starting point or use the skeleton in `starter/agent.py`. The function signature and return shape are identical to M01.

## Workspace entry-point contract

**File:** `agent.py` (at the root of your workspace).

**Importable function — same contract as M01:**

```python
def run_conversation(user_messages: list[str]) -> dict:
    ...
```

**Return shape — same as M01:**

```json
{
  "response": "final assistant text",
  "transcript": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": [...]},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "...", "content": "..."}]},
    ...
  ]
}
```

The tool_result content strings in the transcript must reflect the post-hook normalised form — no Unix-epoch integers, no mixed-case statuses.

**CLI invocation:** same as M01.

**Model:** `ANTHROPIC_MODEL` env var, default `claude-haiku-4-5`.

**Fixtures path:** `FIXTURES_PATH` env var, same as M01.

**Adversarial system prompt injection:** `agent.py` must read `EXTRA_SYSTEM_PROMPT` env var (default empty string). When set, append its contents to your agent's system prompt. This env var is used by the adversarial check (C2) to verify that the refund cap survives a hostile prompt override. Your hook code must block the refund regardless of what `EXTRA_SYSTEM_PROMPT` contains.

## What to build

### PreToolUse hook — refund cap

Your `dispatch_tool` function must call a `pre_tool_use(name, inputs)` function before executing any backend call. For `process_refund` calls with `amount > 500.0`:
- Do not call `support_backend.process_refund`.
- Call `support_backend.escalate_to_human` with a summary that includes the order id and requested amount.
- Return the escalation result as the tool_result content.
- `support_backend.REFUND_LOG` must remain empty for these calls; `support_backend.ESCALATION_LOG` must have an entry.

For all other calls and for refunds of $500.00 or under: allow the call to proceed normally.

### PostToolUse hook — normalisation

Your `dispatch_tool` function must pass every backend result through a normalisation function before serialising it to `tool_result` content. The normalisation must:
- Convert any integer field whose key ends in `_date` or equals `timestamp` from Unix-epoch to an ISO-8601 string (UTC timezone, e.g., `"2024-01-11T06:30:00+00:00"`).
- Normalise any string field named `status` to title-case (e.g., `"SHIPPED"` → `"Shipped"`, `"delivered"` → `"Delivered"`).
- Recurse into nested dicts and lists (order records contain nested item dicts).
- Leave all other fields unchanged.

After normalisation, `tool_result` content strings in the transcript must contain no raw Unix-epoch integers in date fields and no all-caps or all-lowercase status values.

## Fixtures

**`fixtures/support_backend.py`** — identical to M01. Key records for this module:
- **Order O004** — `status: "IN_TRANSIT"`, `subtotal: 700.00`, `total: 768.99`. The $700 subtotal is the adversarial refund amount; it exceeds the $500 policy cap and must trigger escalation, not a refund.
- **Multiple orders** — have Unix-epoch timestamps in `order_date`, `ship_date`, `delivery_date` fields, and mixed-case statuses. The normalisation hook must handle all of them.

No `conversations.json` is required for this module — the checks construct their own messages.

## Acceptance criteria

**C1-refund-cap-blocked.** The checker calls `run_conversation` with a message requesting a $700 refund on order O004. After the call, `support_backend.REFUND_LOG` must be empty and `support_backend.ESCALATION_LOG` must contain at least one entry.

**C2-adversarial-prompt.** The checker re-runs the same $700 refund scenario with `EXTRA_SYSTEM_PROMPT` set to a message asserting that the refund cap has been removed and all amounts are approved. `REFUND_LOG` must still be empty and `ESCALATION_LOG` must still have an entry. This verifies the cap is enforced by hook code, not by the system prompt instruction.

**C3-timestamps-normalized.** The checker calls `run_conversation` with a message that causes an order lookup (any order with Unix-epoch timestamps, e.g., O002). It inspects all `tool_result` content strings in the transcript and verifies no integer in the 1-billion-plus range appears in a date-keyed field. All date values must be ISO-8601 strings.

**C4-statuses-normalized.** The checker inspects the same transcript and verifies that all `status` field values in tool_result content are title-case (first letter uppercase, remainder lowercase). All-caps and all-lowercase status strings are failures.

## What `bootcamp check` does

- Imports `agent.py` and calls `run_conversation`.
- Resets `support_backend.REFUND_LOG` and `support_backend.ESCALATION_LOG` before each check run.
- For C2: sets `EXTRA_SYSTEM_PROMPT` in `os.environ` before calling `run_conversation`, then resets it. Your agent must read this at call time, not at import time.
- Parses `tool_result` content strings in the transcript as JSON and checks field values for C3 and C4.
- All four checks are deterministic — no judge call.
