# Rubric — 09 capstone-reliability

## Criteria

1. **C1-no-escalation-straightforward** (deterministic): `run_scenario("m9-straightforward-no-escalation")` returns `outcome.escalated == false` — no call to `escalate_to_human` for a resolvable case — lesson_ref: lesson.md §explicit_escalation_criteria
2. **C2-policy-escalation** (deterministic): `run_scenario("m9-policy-gap-must-escalate")` returns `outcome.escalated == true` and `support_backend.ESCALATION_LOG` is non-empty — lesson_ref: lesson.md §explicit_escalation_criteria
3. **C3-immediate-human-request** (deterministic): `run_scenario("m9-explicit-human-request")` returns `outcome.escalated == true` and `escalate_to_human` is the first `tool_use` block name in the transcript — no other tool called before it — lesson_ref: lesson.md §immediate_honor
4. **C4-clarification-on-ambiguity** (deterministic): `run_scenario("m9-ambiguous-identity-alex-rivera")` returns `outcome.clarification_asked == true` and the assistant turn following `find_customers` in turn 1 contains no `get_customer`, `lookup_order`, or `process_refund` tool call — lesson_ref: lesson.md §clarify_on_multiple_matches
5. **C5-partial-results** (deterministic): `run_scenario("m9-subagent-timeout-simulation")` returns `outcome.partial_results` as a non-null dict with `successful` (list), `failed` (non-empty list), and `coverage: "partial"` — lesson_ref: lesson.md §structured_error_propagation
6. **C6-self-eval-independent** (deterministic): with `AGENT_LOG_PATH` set, the log contains ≥2 entries with distinct `role` values `"main_conversation"` and `"self_eval"`, and no message from the `self_eval` messages list appears in the `main_conversation` messages list — lesson_ref: lesson.md §independent_self_evaluation

## Hints

### Level 1
One or more checks are failing because the agent is either escalating when it shouldn't, not escalating when it should, or the self-evaluation is sharing state with the main conversation. Look at the specific failing criterion name and match it to a section in lesson.md. The criterion names are precise.

### Level 2
For escalation criteria failures (C1, C2, C3): the system prompt must contain a closed list of escalation conditions with few-shot examples. Without explicit examples, the model applies fuzzy judgment and inconsistently escalates. For C3 specifically: "escalate immediately" in the prompt is not enough if the agent still calls lookup_order first — add a hook or pre-check that detects explicit human request phrases and short-circuits other tool calls. For C4: after `find_customers` returns multiple results, the model must end its turn without calling any account tool — state this constraint explicitly in the system prompt and verify in your code by checking the `find_customers` result length before dispatching other tools. For C6: the self-eval messages list must be initialised as `[]` — not as a copy of the main conversation messages. Check that you are not passing `messages=main_messages` to the eval API call.

### Level 3
System prompt skeleton for escalation criteria:
```python
ESCALATION_CRITERIA = """
=== Escalation — call escalate_to_human ONLY when: ===
1. Refund exceeds $500 policy cap.
2. Customer explicitly requests a human agent — do this FIRST, no other tools.
3. Resolution requires authority beyond your tools.
Not escalation: customer frustration, bad order ID, questions you can answer.
Examples:
"Return $700 item" → criterion 1, escalate
"Talk to a person" → criterion 2, escalate immediately (first tool call)
"Where is O001" → resolvable, do NOT escalate
"This is terrible service" → address the issue, do NOT escalate
"""
```
For partial results, wrap `lookup_order` dispatch:
```python
successful, failed = [], []
for order_id in requested_ids:
    try:
        result = support_backend.lookup_order(order_id)
        successful.append(order_id)
    except KeyError:
        failed.append(order_id)
partial_results = {"successful": successful, "failed": failed,
                   "coverage": "partial" if failed else "full"}
```
For self-eval:
```python
eval_messages = [{"role": "user", "content":
    f"Evaluate this transcript against the criteria:\n{ESCALATION_CRITERIA}\n\n"
    f"Transcript: {json.dumps(transcript)}\nOutcome: {json.dumps(outcome)}\n"
    f"Verdict: PASS or FAIL. Explain."}]
eval_resp = client.messages.create(model=model, messages=eval_messages, max_tokens=512)
```
`eval_messages` must be a new list, not a reference to the main messages list.

## Mentor guardrails

- Do not write the ESCALATION_CRITERIA string for the learner or show the exact few-shot examples.
- If the learner asks why the immediate-human-request check fails, ask: "Which tool call appears first in the transcript? Is it `escalate_to_human`? If not, why did the agent call something else first?"
- If the learner asks about C4 (ambiguity), ask: "What does `find_customers('Alex Rivera')` return? What should the agent do immediately after seeing more than one result? What should it NOT do?"
- If the learner asks about C6 (independence), ask: "Show me where you initialise the messages list for the self-eval call. Is it a new empty list, or does it reference anything from the main conversation?"
- Do not reveal which exact string patterns the C3 checker uses to identify explicit human requests.
- API-shape examples (message structure, tool dispatch) are permitted at ≤5 lines, provided they are not specific to the support backend solution.

## Reference solution sketch

**`agent.py` structure:**

**`ESCALATION_CRITERIA` string:** embedded in the system prompt. Closed list of 3 criteria, negative examples, 4 few-shot examples (2 escalate, 2 don't). Approximately 15–20 lines.

**`TOOLS` list:** same 5 tools as M01/M03/M08. Descriptions unchanged.

**`dispatch_tool(name, inputs, state) -> str`:** `state` is a mutable dict carrying `escalated`, `clarification_asked`, `successful_lookups`, `failed_lookups`. Checks: if name is `find_customers` and result has len > 1, sets `state["clarification_asked"] = True` and returns result without calling any account tool. If name is `lookup_order`, wraps in try/except KeyError — on KeyError appends to `state["failed_lookups"]`, returns an error string. On success appends to `state["successful_lookups"]`. Applies M08-style trimming before returning. If name is `process_refund` and amount > 500, calls `escalate_to_human` instead, sets `state["escalated"] = True`, returns escalation result.

**`run_scenario(scenario_name) -> dict`:** loads script from `fixtures/conversations.json`. Initialises `state` dict. Initialises `messages = []`. For each turn's `user_message`, appends to messages and runs one agentic-loop iteration (stops at `end_turn` for that turn). Accumulates all messages into a single `transcript` list. After all turns: builds `outcome` from `state` — `escalated`, `clarification_asked`, `partial_results` (from successful/failed lists if non-empty), `self_eval` (from a separate API call). If `AGENT_LOG_PATH` is set, writes the log with two entries.

**Self-eval call:** fresh `messages = [{"role": "user", "content": eval_prompt}]`. `client.messages.create(model=model, messages=messages, max_tokens=512)`. Extracts text from response for `verdict` and `reasoning`. Simple parsing: if "PASS" in response text, verdict is "PASS"; else "FAIL". Full response text goes into reasoning.

**`__main__` block:** reads `sys.argv[1]` as scenario name, calls `run_scenario`, prints `json.dumps(result, indent=2)`.

Total: approximately 160–220 lines.
