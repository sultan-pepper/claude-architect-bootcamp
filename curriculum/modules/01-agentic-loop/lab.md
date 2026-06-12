# Lab 01 — The agentic loop

## Mission

Build a customer-support agent using the Anthropic SDK against the mock backend in `fixtures/support_backend.py`. The agent accepts one or more user messages, drives the agentic loop to completion using the backend's tools, and returns the final response plus a full transcript of the API turns.

## Workspace entry-point contract

**File:** `agent.py` (at the root of your workspace).

**Importable function:**

```python
def run_conversation(user_messages: list[str]) -> dict:
    ...
```

**Return shape:**

```json
{
  "response": "final assistant text (string)",
  "transcript": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": [...]},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "...", "content": "..."}]},
    {"role": "assistant", "content": [{"type": "text", "text": "..."}]}
  ]
}
```

`transcript` is the full `messages` list at the end of the loop — every message that was appended in order, including the initial user turn(s), all assistant turns (with tool_use blocks), and all tool_result turns. `response` is the text content of the final assistant message.

**CLI invocation:** when run as `__main__`, `agent.py` reads a JSON array of strings from stdin and writes the return dict as JSON to stdout:

```bash
echo '["I need help with order O001"]' | python agent.py
```

**Model:** read from env `ANTHROPIC_MODEL`, default `claude-haiku-4-5`. Use this default so check runs stay cheap.

**Fixtures path:** the checks set `FIXTURES_PATH` env var to the absolute path of `fixtures/`. Your agent must use this env var (or a sensible default) when importing `support_backend`.

## What to build

Your agent must expose all five backend functions as tools:

- `get_customer(customer_id: str)` — fetch a customer record by id (e.g., "C001")
- `find_customers(name: str)` — search by partial name (case-insensitive)
- `lookup_order(order_id: str)` — fetch an order record by id (e.g., "O001")
- `process_refund(order_id: str, amount: float)` — initiate a refund; raises `RefundError` if `amount > 1000`
- `escalate_to_human(case_summary: str)` — hand off to human agent

Write accurate JSON schemas for each tool (parameter names, types, descriptions). The model uses the descriptions to decide which tool fits — vague descriptions produce wrong tool selection.

Handle exceptions: catch `RefundError` from `process_refund` and return the error message as the `tool_result` content string so the model can inform the user gracefully. Do not let exceptions propagate out of `dispatch_tool`.

## Fixtures

**`fixtures/support_backend.py`** — importable Python module, stdlib only, no Anthropic dependency. Contains 10 customers (including two named "Alex Rivera" with ids C009 and C010), 12 orders with mixed-format timestamps (Unix-epoch ints and ISO-8601 strings) and mixed-case statuses. Import it by inserting the fixtures path into `sys.path`.

**`fixtures/conversations.json`** — scripted test scenarios. The `m1-multi-concern` script drives a single user turn: the user asks about the refund status on order O001 and also requests an address update. Your agent must address both concerns. Note: `support_backend` has no `update_address` function — the agent should acknowledge this limitation rather than silently dropping the request.

## Acceptance criteria

`bootcamp check` verifies all four of the following. Match them exactly — partial credit does not exist.

**C1-stop-reason.** The loop exits when `stop_reason == "end_turn"`. The checker parses your `agent.py` source with Python's `ast` module and verifies that `"end_turn"` appears as a comparison target for `stop_reason` (or equivalent). Text-parsing exit and iteration-cap-as-primary-stop are both failures.

**C2-tool-result-appended.** After calling a tool, the result is appended to `messages` as a user-role message with `type: "tool_result"` before the next API call. The checker inspects the returned `transcript` and verifies that every assistant turn containing a `tool_use` block is followed by a user turn containing a matching `tool_result` block.

**C3-no-iteration-cap.** No hardcoded numeric loop limit acts as the primary exit condition. An iteration cap for safety (e.g., raising an error if N > 50) is acceptable, provided `end_turn` drives the normal exit. The checker uses `ast` to detect patterns like `for i in range(N)` as the outer loop.

**C4-multi-concern.** When the `m1-multi-concern` conversation script is run, the transcript must include tool calls that address both concerns — an order lookup (order O001) and at minimum an acknowledgement of the address request. The checker inspects `tool_use` block names and inputs in the transcript.

## What `bootcamp check` does

- Imports `agent.py` from your workspace directory and calls `run_conversation` directly.
- Inspects the returned `transcript` for structural correctness (tool_use/tool_result pairing, role alternation).
- Parses your `agent.py` source with `ast` to detect stop-condition anti-patterns.
- Runs the `m1-multi-concern` script from `conversations.json` and checks which tools were called and with which arguments.

The checker does not evaluate prose quality — it checks loop structure and tool call coverage only.
