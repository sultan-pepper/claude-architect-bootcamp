# Lesson 09 — Capstone: escalation & reliability

This module assembles M01–M08 patterns into a production-grade support agent and adds three reliability mechanisms left implicit until now: explicit criteria-based escalation with few-shot examples, structured error propagation when subagents fail, and independent-instance self-evaluation. It also names two escalation anti-patterns — sentiment and self-confidence — that appear correct but fail systematically.

## explicit_escalation_criteria

An agent that escalates based on the model's judgment without explicit criteria will escalate inconsistently: sometimes on easily-resolvable cases, sometimes not on cases that clearly require escalation. The variance grows as inputs deviate from training distribution.

The fix: state escalation criteria explicitly in the system prompt as a closed list, with few-shot examples showing cases that do and do not meet each criterion.

```python
ESCALATION_CRITERIA = """
ESCALATE — call escalate_to_human ONLY when:
1. Refund amount exceeds $500 (policy cap). Resolve under $500 without escalation.
2. Customer explicitly requests a human agent. Honour immediately, no investigation first.
3. Resolution requires authority beyond these tools (e.g., custom pricing, account deletion).

DO NOT escalate for:
- Technical questions you can answer from order data
- Recoverable errors (bad order ID, transient lookup failure)
- Customer frustration or complaints (address the underlying issue)

Examples:
User: "I need to return this $600 item." -> escalate (criterion 1)
User: "Where is my order?" -> do NOT escalate (resolvable with lookup_order)
User: "I want a real person NOW." -> escalate immediately (criterion 2)
User: "This is ridiculous!" -> do NOT escalate (address frustration, resolve issue)
"""
```

The few-shot examples are critical. Without them, the model applies fuzzy judgment to the criteria text. With them, the model has a demonstrated boundary between escalate and don't-escalate for the cases most likely to be ambiguous.

## immediate_honor

When a customer explicitly requests a human agent, the correct action is immediate escalation. No information gathering, no "let me try to help first," no investigation. The explicit request is the criterion.

Two failure modes:

**Investigation first**: the agent calls `lookup_order` or `find_customers` before calling `escalate_to_human`. This wastes time (the customer said they want a human) and may appear as stonewalling. The check for this is structural: in the transcript, `escalate_to_human` must be the first tool call. Any tool call appearing before it is a failure.

**Soft escalation**: the agent describes the situation without calling `escalate_to_human`. Only a tool call produces the `ESCALATION_LOG` entry.

The system prompt instruction alone does not always survive adversarial prompt conditions. Pair it with a pre-check in `dispatch_tool` that detects explicit human request phrases and gates other tool calls.

## clarify_on_multiple_matches

When `find_customers` returns multiple results for the same name, the agent must ask a clarifying question. It must not:

- Pick the first result heuristically
- Pick the result with higher tier or more spend
- Pick based on any other implicit signal

The reason: heuristic identity resolution silently operates on the wrong account. A customer whose name matches two records will get responses about another person's orders, amounts, and personal data — a privacy and correctness failure that is not observable from the agent's response alone.

The correct behaviour: state that multiple accounts match and ask for a disambiguating identifier (email, order number, phone number). Then wait for the customer's response before calling any account-specific tool (`get_customer`, `lookup_order`, `process_refund`).

In the transcript, this means: after `find_customers` returns two results, the next tool call in the same assistant turn must not be `get_customer` or any order tool. The assistant must produce an end_turn response asking for clarification.

## bad_escalation_proxies

Two proxies that appear to correlate with escalation need but systematically misfire:

**Sentiment**: negative sentiment (frustration, anger) is common in support conversations that resolve without escalation. A customer who says "this is ridiculous" and then gets their order status explained is not an escalation case. Escalating on negative sentiment produces unnecessary escalations and undermines the criteria-based approach. The criteria list explicitly covers this: "Customer frustration or complaints → do NOT escalate."

**Self-confidence**: the model's expressed uncertainty ("I'm not sure if I can help with this") is not a signal that escalation is needed. It is a signal that the model is being honest about its uncertainty, which is correct behaviour. If the model has the tools to resolve the issue, uncertainty in the phrasing does not change the escalation calculus. Treating model hedging language as an escalation signal escalates the majority of edge cases — exactly the cases where the agent should attempt resolution.

Neither sentiment nor self-confidence appears in the explicit escalation criteria. Any logic that checks for these before calling `escalate_to_human` is incorrect.

## structured_error_propagation

When a subagent or tool call fails (timeout, KeyError, upstream error), the outer agent must:

1. Record what succeeded and what failed.
2. Return a result that describes both, rather than either failing silently or escalating.
3. Annotate the result with coverage information so the caller knows how complete the data is.

```python
partial_results = {
    "successful": ["O001", "O007"],
    "failed":     ["O999"],
    "coverage":   "partial",
}
```

`coverage: "partial"` means the agent could not retrieve data for all requested items. The caller (or the next agent in a chain) can decide whether partial results are sufficient or whether to re-request the missing items.

A recoverable error (order ID not found, transient timeout) is not an escalation case. It is a data gap that the agent reports honestly. Only errors that require human judgment or authority trigger escalation — and those are covered by the explicit escalation criteria.

The coverage annotation is metadata about the result, not about the agent's confidence. It is factual: some lookups succeeded, some failed, the result is partial. Downstream consumers can rely on this field without interpreting the agent's prose.

## independent_self_evaluation

A self-evaluation pass where the same model instance evaluates its own output in the same conversation is not independent. The model has the same priors, the same biases, and — if the evaluation prompt is in the same message history — access to the same reasoning that produced the original output. It will tend to agree with itself.

An independent self-evaluation uses a separate API call with no shared message history:

```python
# After the main conversation completes:
eval_client = anthropic.Anthropic()   # same client is fine; new conversation
eval_messages = [
    {
        "role": "user",
        "content": (
            f"You are a quality evaluator. Review this support agent transcript "
            f"against the escalation criteria below and render a verdict.\n\n"
            f"## Escalation criteria\n{ESCALATION_CRITERIA}\n\n"
            f"## Transcript\n{json.dumps(main_transcript)}\n\n"
            f"## Outcome\n{json.dumps(main_outcome)}\n\n"
            f"Verdict: PASS if escalation decisions match criteria, FAIL otherwise. "
            f"Explain your reasoning."
        ),
    }
]
eval_response = eval_client.messages.create(
    model=model, messages=eval_messages, max_tokens=512,
)
```

The key properties:
- `eval_messages` is a fresh list — no turns from the main conversation.
- The evaluator sees the transcript and outcome as data, not as part of its own prior reasoning.
- The evaluator is asked to evaluate against the criteria, not against its general sense of quality.

The run log (when `AGENT_LOG_PATH` is set) records both the main conversation messages and the self-eval messages as separate entries. The checker verifies that two distinct message histories appear — evidence that the self-eval was not appended to the main conversation.
