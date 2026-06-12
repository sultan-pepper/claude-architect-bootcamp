# Rubric — 03 hooks

## Criteria

1. **C1-refund-cap-blocked** (deterministic): a $700 refund request on order O004 results in `ESCALATION_LOG` having an entry and `REFUND_LOG` remaining empty — lesson_ref: lesson.md §pre_tool_use
2. **C2-adversarial-prompt** (deterministic): the $700 refund block survives when `EXTRA_SYSTEM_PROMPT` asserts the cap has been removed — `REFUND_LOG` still empty, `ESCALATION_LOG` still populated — lesson_ref: lesson.md §hooks_vs_prompts
3. **C3-timestamps-normalized** (deterministic): all `tool_result` content in the transcript contains no Unix-epoch integers in date-keyed fields; all such values are ISO-8601 strings — lesson_ref: lesson.md §post_tool_use
4. **C4-statuses-normalized** (deterministic): all `status` field values in `tool_result` content are title-case (first letter uppercase, remainder lowercase) — lesson_ref: lesson.md §post_tool_use

## Hints

### Level 1
The refund cap check needs to run before the backend function is called — if `process_refund` is ever invoked with a large amount, the hook has already failed. Think about where in the code execution path you can intercept a tool call before it reaches the backend. For normalisation, the backend data contains a mix of formats; the model should only ever receive one consistent format.

### Level 2
Add a `pre_tool_use(name, inputs)` function to your `dispatch_tool` logic. It runs before any backend call. If name is `"process_refund"` and `inputs["amount"] > 500`, call `escalate_to_human` yourself and return that result — `process_refund` is never called. For normalisation, add a `post_tool_use` step that walks the result dict and converts integer timestamps and mixed-case statuses before the result is passed to `json.dumps`.

### Level 3
PreToolUse skeleton:
```python
def pre_tool_use(name: str, inputs: dict) -> Any | None:
    if name == "process_refund" and inputs.get("amount", 0) > 500.0:
        summary = f"Refund ${inputs['amount']} on {inputs['order_id']} exceeds cap"
        return support_backend.escalate_to_human(summary)
    return None  # proceed normally

def dispatch_tool(name, inputs):
    override = pre_tool_use(name, inputs)
    if override is not None:
        return override
    result = _call_backend(name, inputs)
    return normalise_result(result)
```

PostToolUse normalisation skeleton:
```python
def normalise_result(v, key=""):
    if isinstance(v, dict):
        return {k: normalise_result(val, k) for k, val in v.items()}
    if isinstance(v, list):
        return [normalise_result(i) for i in v]
    if isinstance(v, int) and (key.endswith("_date") or key == "timestamp"):
        return datetime.datetime.fromtimestamp(v, tz=datetime.timezone.utc).isoformat()
    if key == "status" and isinstance(v, str):
        return v.capitalize()
    return v
```

## Mentor guardrails

- Do not write the `pre_tool_use` condition or the `normalise_result` traversal for the learner.
- If the learner's refund cap is implemented as a system prompt instruction, ask: "what happens if a message later in the conversation contradicts that instruction?" Then point to `lesson.md §hooks_vs_prompts`.
- If the learner asks why C2 fails even though C1 passes, ask them to explain the difference between where the model reads its instructions and where the hook executes.
- Do not confirm whether a particular normalise implementation handles nested dicts — ask the learner to trace what happens when `normalise_result` receives an order dict with an `items` list.
- Do not reveal the exact `EXTRA_SYSTEM_PROMPT` string the checker uses.

## Reference solution sketch

**`agent.py` structure (extending M01):**

Add `import datetime` and `import re`.

**`normalise_result(value, key="")`:** recursive function. If `value` is a dict: return `{k: normalise_result(v, k) for k, v in value.items()}`. If list: map recursively. If int and `key` matches date fields: convert with `datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc).isoformat()`. If `key == "status"` and str: return `value.capitalize()`. Otherwise return `value` unchanged.

**`pre_tool_use(name, inputs)`:** single conditional — `name == "process_refund"` and `inputs.get("amount", 0) > 500.0` — calls `support_backend.escalate_to_human` with a summary string containing order_id and amount, returns the result dict. Otherwise returns `None`.

**`dispatch_tool(name, inputs)`:** calls `pre_tool_use` first. If result is not None, return it (skip backend). Otherwise: look up and call the backend function, catch `RefundError`, call `normalise_result` on the return value, return it.

**`run_conversation`:** reads `EXTRA_SYSTEM_PROMPT` from `os.environ` at call time (not at import time). Appends it to the base system prompt string if non-empty. System prompt must be passed as the `system` parameter to `client.messages.create`. Rest of the loop is identical to M01.

Total: approximately 130–160 lines (M01 base plus ~40 lines of hook logic).
