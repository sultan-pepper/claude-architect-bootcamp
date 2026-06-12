# Lesson 01 — The agentic loop

The Anthropic API is a request/response interface: one call in, one response out. An agent is a loop around that call. The SDK does not run the loop for you. Understanding what drives the loop's exit condition — and what does not — is the foundation of every module in this bootcamp.

## Loop lifecycle

Each iteration of the loop is one round-trip to the API:

1. Call `client.messages.create(model=..., tools=..., messages=messages)`.
2. Append the response to the messages list as an assistant turn: `messages.append({"role": "assistant", "content": response.content})`.
3. Inspect `response.stop_reason`.
4. If `stop_reason == "tool_use"`: extract the tool use blocks from `response.content`, call each tool, build `tool_result` blocks, append a user message containing all results, then return to step 1.
5. If `stop_reason == "end_turn"`: the model has decided the task is complete. Exit the loop. Return the final response text.

```python
while True:
    response = client.messages.create(
        model=model,
        tools=tools,
        messages=messages,
    )
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        break
    if response.stop_reason != "tool_use":
        raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = dispatch_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })
    messages.append({"role": "user", "content": tool_results})
```

This is the canonical form. The loop has exactly one exit condition: `stop_reason == "end_turn"`. Everything else is iteration.

## stop_reason

`response.stop_reason` is a string. The two values relevant to a functional agent:

- `"tool_use"`: the model wants to call one or more tools. The blocks are in `response.content`.
- `"end_turn"`: the model considers the task complete. Exit.

Other values (`"max_tokens"`, `"stop_sequence"`) indicate a problem. Handle them explicitly — do not fall through to the same branch as `"end_turn"`.

The key implication: you do not decide when the agent is done. The model does, through this field. Any code that makes the exit decision based on something else — response text content, iteration count, elapsed time — is bypassing the model's reasoning and will fail when that heuristic diverges from the model's intent.

## tool_results

When `stop_reason == "tool_use"`, `response.content` is a list that includes one or more `ToolUseBlock` objects. Each has:

- `.id` — a unique identifier you must echo back in the result
- `.name` — the tool function name
- `.input` — dict of arguments

After calling each tool, you wrap the result and append all results as a **single** user message with `type: "tool_result"`:

```python
tool_results = []
for block in response.content:
    if block.type == "tool_use":
        result = dispatch_tool(block.name, block.input)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,    # must match the tool_use block's id
            "content": json.dumps(result),
        })

messages.append({"role": "user", "content": tool_results})
```

Two structural errors to avoid:

**Forgetting to append the assistant turn first.** You must append `{"role": "assistant", "content": response.content}` before appending the tool results. If you skip this, the model's tool call disappears from history and the API rejects the malformed message sequence.

**Appending one user message per tool result.** All tool results for a given assistant turn must be batched into one user message. Splitting them creates invalid role alternation (user/user).

After appending the tool results, the next API call gives the model its own tool calls followed by all their results. The model then decides what to do next — more tools, more text, or `end_turn`.

## model_driven_sequencing

The model decides which tools to call and in what order. Your loop must not encode a fixed sequence. Do not write logic like "call `get_customer` first, then `lookup_order`, then decide about refund". Reasons:

- A message with two unrelated concerns (refund status and an address update) requires both to be addressed, in whatever order serves the user. The model routes this correctly if you give it complete, accurate tool schemas.
- The model can call multiple tools in a single response. Forcing serial one-tool-at-a-time behavior wastes latency and may not match the model's intent.
- Hardcoded sequences break whenever a real input deviates from the assumed scenario.

Your job in the loop: define the tool schemas accurately, pass the full message history, and let the model drive.

## anti_patterns

Three patterns that appear to work in simple tests but fail in production:

**Text-parsing termination.** Scanning response text for phrases like "Is there anything else?" or "I've resolved your issue" to decide when to exit. Fails as soon as model phrasing varies — which happens with model updates, temperature, or slightly different input. The correct exit signal is `stop_reason == "end_turn"`, always.

**Iteration cap as primary stop.** Writing `for i in range(20):` as the outer loop and relying on the range exhausting to exit. An iteration cap is a safety rail against infinite loops due to bugs; it must not be the intended exit path. The primary exit must be `stop_reason == "end_turn"`. If you reach the cap during normal operation, the loop is broken and needs fixing.

**Assistant-text-as-done.** Treating any assistant turn that contains text content as completion, even if `response.content` also includes tool_use blocks. A single response can have both text and tool_use blocks — the model may explain what it is about to do and then use a tool. Always check `stop_reason`, not whether text is present.
