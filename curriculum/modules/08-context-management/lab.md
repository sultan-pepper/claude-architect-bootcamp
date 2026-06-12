# Lab 08 — Context management

## Mission

Extend the M01/M03 customer-support agent to survive a 30-turn scripted conversation without losing critical information. Your agent must recall an exact dollar amount stated in turn 3 when asked again in turn 28, trim the verbose 40-field order records before they enter message history, and produce a structured handoff dict when escalation occurs.

You may copy your M03 `agent.py` as a starting point or use the skeleton in `starter/agent.py`. The M03 hooks (refund cap, timestamp/status normalisation) carry forward — do not remove them.

## Workspace entry-point contract

**File:** `agent.py` at the root of your workspace.

**Importable function — identical signature to M01/M03:**

```python
def run_conversation(user_messages: list[str]) -> dict:
    ...
```

**Return shape:**

```json
{
  "response": "final assistant text",
  "transcript": [
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": [...]},
    {"role": "user",      "content": [{"type": "tool_result", ...}]},
    ...
  ],
  "handoff": {
    "customer_id":        "C001",
    "root_cause":         "...",
    "amount":             768.99,
    "recommended_action": "..."
  }
}
```

`handoff` is present only when escalation occurs (i.e., `escalate_to_human` was called during the conversation). When no escalation occurs, the key must be absent from the return dict (not `null`, not an empty dict — absent).

`transcript` is the full messages list accumulated during the loop — same as M01/M03. The `tool_result` content strings in the transcript must contain the **trimmed** (not raw) order records.

**CLI invocation:** same as M01/M03 — reads a JSON array of strings from stdin, writes the result dict as JSON to stdout.

**Model:** `ANTHROPIC_MODEL` env var, default `claude-haiku-4-5`.

**Fixtures path:** `FIXTURES_PATH` env var, same as M01/M03.

**Adversarial system prompt:** `EXTRA_SYSTEM_PROMPT` env var (from M03) — still honoured; your refund cap hook must still block amounts over $500 regardless of this env var's content.

## What to build

### Persistent case-facts block

Maintain a `case_facts` dict tracking information that must survive the full conversation:

```python
case_facts: dict = {
    "customer_id":       None,
    "confirmed_amounts": {},   # maps description -> amount, e.g. {"O002_subtotal": 123.45}
    "root_cause":        None,
}
```

Update `case_facts` as the conversation progresses (e.g., when an order subtotal is mentioned). Re-inject it into the system prompt on every API call so it is always at the beginning of context. Do not rely on the model to recall facts from message history alone.

### Trimmed tool outputs

Before serialising any `lookup_order` result to a `tool_result` content string, trim the raw dict to the fields a support agent actually needs. The raw result has 40+ fields; your trimmed version must have strictly fewer than the raw field count.

Suggested fields to keep: `order_id`, `status`, `total`, `subtotal`, `delivery_date`, `tracking_number`, `line_items`, `shipping_address`. Omit internal flags, audit timestamps, and any field not needed to answer a customer support question.

Apply trimming in your PostToolUse hook (from M03) or in `dispatch_tool` after the backend call. The trimmed result is what gets serialised to the `tool_result` content string.

### Structured handoff on escalation

When your PreToolUse hook redirects a refund above $500 to `escalate_to_human`, construct a `handoff` dict using the information already gathered:

```python
handoff = {
    "customer_id":        case_facts.get("customer_id"),
    "root_cause":         f"Refund of ${amount} exceeds $500 policy cap",
    "amount":             amount,
    "recommended_action": "Escalate to supervisor for refund exception approval",
}
```

Store this dict in a variable accessible to `run_conversation`, then include it in the return dict.

## Fixtures

**`fixtures/support_backend.py`:** identical to M01/M03. Key records:
- **Order O002:** `subtotal: 123.45`. Turn 3 of the 30-turn script states this amount; turn 28 asks for it.
- **Order O004:** `subtotal: 700.00`, `total: 768.99`. Exceeds the $500 policy cap — triggers escalation and tests the handoff check.
- All orders have 40+ fields including Unix-epoch timestamps (normalised by your M03 PostToolUse hook) and mixed-case statuses.

**`fixtures/conversations.json`:** contains the script `m8-30-turns-3-issues`. 30 user turns spanning 3 orders and multiple follow-up questions. Turn 3 states "$123.45" as the O002 subtotal; turn 28 asks for the exact dollar amount.

## Acceptance criteria

All three checks are deterministic. All must pass.

**C1-recall-amount.** The checker drives the full `m8-30-turns-3-issues` script by calling `run_conversation` with each turn's `user_message` sequentially, maintaining conversation state across turns (or by calling with the full 30-message list — see note below). It extracts the agent's response to turn 28 and verifies the string `"123.45"` appears in it. Any response to turn 28 that does not contain `"123.45"` is a failure.

Note on multi-turn driving: the checker calls `run_conversation` once per turn, passing the accumulated conversation history. Your function must accept `user_messages` as a list where previous assistant responses are interleaved, or the checker will call `run_conversation` with the full 30-message sequence as a flat list. Consult the checker-builder's implementation — the simplest approach is to accept a list of strings and treat each as a new user turn, managing full conversation history internally across turns via a session dict or by accepting the conversation history directly.

**C2-trimmed-tool-output.** The checker calls `support_backend.lookup_order("O001")` directly and counts the number of top-level keys in the result. It then calls `run_conversation(["I need help with order O001"])` and finds the `tool_result` content string in the transcript corresponding to the `lookup_order` call. It parses that string as JSON and counts its top-level keys. The trimmed count must be strictly less than the raw count. If the counts are equal (full raw output in history), the check fails.

**C3-structured-handoff.** The checker calls `run_conversation(["I need to return order O004 for a full refund. There's a manufacturing defect."])`. The returned dict must contain a `handoff` key. That `handoff` value must be a dict containing all four required fields: `customer_id` (non-null string or derivable), `root_cause` (non-null string), `amount` (non-null number), `recommended_action` (non-null string). Any missing or null field is a failure.

## What `bootcamp check` does

- Imports `agent.py` from your workspace and calls `run_conversation` directly.
- For C2: calls `support_backend.lookup_order("O001")` in-process to get the raw field count.
- For C3: resets `support_backend.REFUND_LOG` and `support_backend.ESCALATION_LOG` before the call.
- Parses `tool_result` content strings from the transcript as JSON.
- All checks are deterministic — no judge call.
