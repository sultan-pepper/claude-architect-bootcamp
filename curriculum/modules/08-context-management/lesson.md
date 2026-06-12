# Lesson 08 — Context management

Every token in the messages list costs money and competes for the model's attention. A 30-turn conversation with raw tool outputs accumulates thousands of tokens of order records, shipping metadata, and internal flags — most of it never referenced again after the turn it first appeared. The model's effective recall degrades as irrelevant material pushes relevant facts toward the middle of the context window. This lesson covers the patterns that keep long agent conversations reliable: persistent fact blocks, output trimming, position-aware ordering, scratchpads, and structured handoff summaries.

## context_window_as_working_memory

The messages list is the model's only memory. It has no persistent state between API calls other than what appears in messages. This means:

- Information stated in turn 3 is only available in turn 28 if it is still in the messages list and the model attends to it.
- The model attends better to content near the beginning and end of the context (the "lost in the middle" effect). Content deep in the middle of a long context is recalled less reliably.
- Every tool result you append verbatim is a permanent addition. A 40-field order record that is only needed for two of its fields adds noise for the rest of the conversation.

Managing context is not optional past roughly 10 turns. It is the difference between a support agent that reliably recalls a customer's stated amount 25 turns later and one that guesses.

## persistent_facts_block

Facts that must survive the full conversation — customer identity, confirmed amounts, issue root causes — should live in a dedicated block that is immune to summarisation or trimming. The simplest implementation: a dict that you serialise and insert into every system prompt or into the first user message of each API call.

```python
case_facts = {
    "customer_id":   None,
    "confirmed_amount": None,
    "root_cause":    None,
}

# After turn 3 establishes the amount:
case_facts["confirmed_amount"] = 123.45

# Before each API call, inject facts into the system prompt:
system = BASE_SYSTEM + "\n\n## Current case facts\n" + json.dumps(case_facts, indent=2)
```

The facts block is never summarised away because it is reconstructed from the canonical `case_facts` dict, not derived from message history. It is small (a few fields), so it does not contribute meaningfully to token count. It is positioned at the beginning of the system prompt, which has high attention weight.

## trimming_tool_outputs

A `lookup_order` result from the support backend contains 40+ fields: line items, shipping coordinates, internal flags, audit timestamps, mixed-format dates. A typical support turn needs 5–8 of them: status, delivery date, total, items, tracking number. The rest are noise.

Before appending a tool result to history, trim it:

```python
KEEP_ORDER_FIELDS = {
    "order_id", "status", "total", "subtotal",
    "delivery_date", "tracking_number", "line_items",
}

def trim_order(raw: dict) -> dict:
    return {k: v for k, v in raw.items() if k in KEEP_ORDER_FIELDS}
```

Trimming is applied to the tool_result content string — the model sees the trimmed version. The raw result is never stored in history. The field whitelist is stable and defined by what questions the agent can actually be asked about an order.

Two failure modes to avoid:

**Over-trimming**: removing a field the model needs for a downstream calculation or answer. Keep fields that are semantically relevant to the domain, not just the fields you know the current turn needs.

**Keeping tool outputs verbatim**: each 40-field record is hundreds of tokens. Over 10 order lookups across a 30-turn conversation, that is thousands of tokens of noise accumulating in the middle of the context window.

## lost_in_the_middle

Research on transformer attention shows that recall accuracy drops for content positioned in the middle of a long context. The beginning (system prompt, first few turns) and the end (recent turns) have higher attention weight. Content added in turn 3 and not reinforced is at high risk of being recalled incorrectly by turn 28.

Mitigations:

**Persistent facts block** (see above): keeps critical facts in the system prompt (beginning of context), not buried in history.

**Recency re-injection**: when a fact stated early is needed later, re-state it in the current turn's context rather than relying on the model to reach back. The facts block handles this automatically if kept current.

**Avoid long middle sections**: if the conversation has many turns of low-density chit-chat between two important exchanges, consider whether those turns can be summarised before the next high-stakes question.

**Position-aware ordering**: when building a system prompt that includes multiple sections, put the highest-priority constraints and facts first, not last. Instructions buried at the end of a long system prompt are treated as lower priority.

## scratchpads

The model can produce intermediate reasoning — calculations, partial summaries, decision trees — in a response before committing to a final answer. You can direct this with a system prompt instruction like "Use a <scratchpad> block for intermediate reasoning before giving your final response."

Scratchpad content in an assistant turn is visible to the model on the next call (it is in the message history). However, scratchpad blocks are not the same as persisted facts: if history is summarised, the scratchpad content may be lost. Important conclusions from scratchpad reasoning should be extracted and stored in `case_facts`.

Scratchpads are most valuable for multi-step calculations (totals, policy threshold checks) and for decisions with multiple conditions (escalation criteria). They make the model's reasoning inspectable in the transcript.

## structured_handoff

When an agent escalates to a human or hands off to another system, the handoff payload must be machine-readable, not a prose summary. A prose summary requires the recipient to re-parse natural language. A structured dict is directly usable.

Required handoff fields for a support escalation:

```python
handoff = {
    "customer_id":        case_facts["customer_id"],
    "root_cause":         "Refund request of $768.99 exceeds $500 policy cap",
    "amount":             768.99,
    "recommended_action": "Approve refund exception or refer to supervisor",
}
```

The `run_conversation` return dict must include this as a `handoff` key when escalation occurs. The checker verifies all four fields are present and non-null.

The handoff is constructed by the agent's code, not by the model's prose. The model informs the code what happened (via tool call parameters and conversation content); the code assembles the structured dict. This separation guarantees the dict is always well-formed regardless of how the model phrases its response.

## structured_data_between_agents

In multi-agent architectures, agents communicate via the messages array. Prose between agents is lossy: a subagent that returns "I found that the customer has a gold tier account with $4,550 in lifetime spend" requires the orchestrator to parse natural language to extract the tier and amount. A subagent that returns `{"tier": "gold", "lifetime_spend": 4550.99}` is directly usable.

Apply the same rule that applies to tool outputs: anything that another agent (or your own next turn) needs to act on programmatically must be structured. Anything that is only for human reading can be prose.

For the handoff case specifically: when the M9 capstone agent spawns a self-evaluation subagent, it passes the main agent's transcript and structured outcome as data, not as a rendered prose summary. The self-evaluator inspects the structured outcome against the escalation criteria. This is only reliable because the outcome is a dict.
