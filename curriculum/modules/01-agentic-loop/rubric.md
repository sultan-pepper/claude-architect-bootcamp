# Rubric — 01 agentic-loop

## Criteria

1. **C1-stop-reason** (deterministic): `agent.py` source contains a check of `stop_reason == "end_turn"` (or equivalent) as the loop exit condition — no text-parsing exit, no iteration-counter-as-primary-stop — lesson_ref: lesson.md §stop_reason
2. **C2-tool-result-appended** (deterministic): every assistant turn with a `tool_use` block in the transcript is followed by a user turn containing a `tool_result` block with matching `tool_use_id` — lesson_ref: lesson.md §tool_results
3. **C3-no-iteration-cap** (deterministic): no `for i in range(N)` or equivalent numeric counter forms the outer loop driving the exit condition — lesson_ref: lesson.md §anti_patterns
4. **C4-multi-concern** (deterministic): running the `m1-multi-concern` script produces a transcript containing a `lookup_order` tool_use for order O001 and at least one other tool_use addressing the address-related concern — lesson_ref: lesson.md §model_driven_sequencing

## Hints

### Level 1
The loop needs a signal from the API response — not from the text the model writes — to know when to stop. Look at the fields returned in the response object rather than scanning the message content.

### Level 2
`response.stop_reason` controls the loop. When it is `"end_turn"`, the model is done — break. When it is `"tool_use"`, extract each tool block from `response.content`, call the function, and collect the results. Before the next API call, append two things: the assistant message containing the tool calls, and a user message containing all the `tool_result` blocks.

### Level 3
Outer loop skeleton:
```python
while True:
    response = client.messages.create(model=model, tools=tools, messages=messages)
    messages.append({"role": "assistant", "content": response.content})
    if response.stop_reason == "end_turn":
        break
    # collect results for all tool_use blocks in response.content
    # append {"role": "user", "content": [{"type": "tool_result",
    #          "tool_use_id": block.id, "content": json.dumps(result)}
    #         for each block]}
```
The `tool_results` list for one assistant turn all go in one user message. `tool_use_id` must match the block's `.id`.

## Mentor guardrails

- Do not write the loop body or tool dispatch function for the learner.
- If the learner describes checking response text for a "done" phrase, ask: what happens to that check when the model's phrasing changes on the next API version?
- If the learner asks about loop termination, point to `lesson.md §stop_reason` and ask them to list every `stop_reason` value the API can return.
- API-shape examples (message structure, type strings) are allowed at ≤5 lines, provided they are not specific to the support backend solution.
- Do not reveal which specific `ast` node patterns the checker targets.
- Do not confirm whether a particular loop structure passes the check — refer back to the criterion description in lab.md.

## Reference solution sketch

**`agent.py` structure:**

Imports: `anthropic`, `json`, `os`, `sys`; conditionally adds fixtures path to `sys.path` from `FIXTURES_PATH` env var, then `import support_backend`.

**`TOOLS` list:** five dicts, each with `"name"`, `"description"`, `"input_schema"`. Schemas: `get_customer` takes `customer_id: string`; `find_customers` takes `name: string`; `lookup_order` takes `order_id: string`; `process_refund` takes `order_id: string` and `amount: number`; `escalate_to_human` takes `case_summary: string`. Descriptions should be specific enough that the model routes correctly — e.g., `lookup_order` description should mention it returns shipping status and line items.

**`dispatch_tool(name, inputs) -> str`:** a dict keyed by tool name mapping to `support_backend` callables. Calls the function with `**inputs`. Wraps the return in `json.dumps`. Catches `support_backend.RefundError` and returns the error message string as content (not re-raised).

**`run_conversation(user_messages, *, system=None) -> dict`:** builds initial `messages` as `[{"role": "user", "content": user_messages[0]}]` for single-turn (or concatenates multi-turn as alternating messages for multi-turn). Reads `ANTHROPIC_MODEL` env var, defaults `"claude-haiku-4-5"`. Reads `ANTHROPIC_API_KEY` from env (standard SDK behaviour). Runs the `while True` loop described in lesson §Loop lifecycle. Appends both assistant turns and tool_result turns to `messages`. Breaks on `"end_turn"`. Returns `{"response": final_text, "transcript": messages}`.

**`__main__` block:** reads JSON from `sys.stdin` (list of strings), calls `run_conversation`, prints `json.dumps` of result.

Total: approximately 80–120 lines.
