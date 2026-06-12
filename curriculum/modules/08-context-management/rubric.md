# Rubric — 08 context-management

## Criteria

1. **C1-recall-amount** (deterministic): the agent's response to turn 28 of the `m8-30-turns-3-issues` script contains the string `"123.45"` — lesson_ref: lesson.md §persistent_facts_block
2. **C2-trimmed-tool-output** (deterministic): the top-level key count of the `lookup_order` `tool_result` content in the transcript is strictly less than the key count of the raw `support_backend.lookup_order` return value — lesson_ref: lesson.md §trimming_tool_outputs
3. **C3-structured-handoff** (deterministic): when `run_conversation` triggers escalation (O004 refund request), the returned dict contains `handoff` with all four fields — `customer_id`, `root_cause`, `amount`, `recommended_action` — all non-null — lesson_ref: lesson.md §structured_handoff

## Hints

### Level 1
The check is failing because information stated early in a long conversation is not available when needed later. The model's message history is long and the relevant fact is in the middle of it. Consider where critical facts are stored — in the rolling message history alone, or somewhere more reliable.

### Level 2
Critical facts (amounts, customer IDs, root causes) should live in a `case_facts` dict that you re-inject into the system prompt on every API call. The system prompt is at the beginning of the context window, where attention is highest. The model will reliably recall facts that are in the system prompt rather than facts buried 25 turns back in history. Update `case_facts` when a fact is established (e.g., when order O002's subtotal is mentioned), not just at the end.

### Level 3
Skeleton for persistent facts:
```python
case_facts: dict = {"confirmed_amounts": {}, "customer_id": None, "root_cause": None}

def build_system(base_system: str, facts: dict) -> str:
    return base_system + "\n\n## Case facts (always current)\n" + json.dumps(facts, indent=2)

# In run_conversation loop — rebuild system prompt each API call:
response = client.messages.create(
    model=model,
    system=build_system(BASE_SYSTEM, case_facts),
    tools=TOOLS,
    messages=messages,
)
# After each assistant turn, scan for amounts to capture:
# (or update case_facts when tool results establish facts)
```
For trimming, wrap `dispatch_tool` to strip the raw dict before serialising:
```python
KEEP = {"order_id", "status", "total", "subtotal", "delivery_date",
        "tracking_number", "line_items", "shipping_address"}
def trim_order(raw: dict) -> dict:
    return {k: v for k, v in raw.items() if k in KEEP}
```
For the handoff: capture `amount` in your PreToolUse hook (it is in the `inputs` dict for `process_refund`), build the handoff dict there, and store it in a variable accessible to the outer `run_conversation` function (e.g., a mutable container or nonlocal).

## Mentor guardrails

- Do not write the `case_facts` update logic for the learner or show which specific turns update which fields.
- If the learner asks why turn 28 recall fails, ask: "Where does the model find the $123.45 amount when constructing the turn-28 response? Is it in the system prompt, in recent history, or buried 25 turns back?"
- If the learner asks about trimming, ask: "How many fields does `support_backend.lookup_order` return? How many does a support agent actually need? What is the cost of keeping all of them?"
- If the learner asks about the handoff, ask: "When does your agent know the escalation amount? Where in the code does that happen, and how do you get that value into the return dict?"
- API-shape examples (system prompt assembly, messages structure) are permitted at ≤5 lines, provided they are not specific to the support backend solution.
- Do not reveal the exact field names checked by C3 beyond what lab.md states.

## Reference solution sketch

**`agent.py` structure:** extends M03 `agent.py` with three additions.

**`case_facts` dict:** module-level or closure-scoped dict with keys `customer_id`, `confirmed_amounts` (nested dict), `root_cause`. Initialised at the start of `run_conversation`. Updated when tool results or user messages establish key facts (at minimum, when `lookup_order("O002")` result is processed, extract and store `subtotal` under `confirmed_amounts["O002_subtotal"]`).

**`build_system(base: str, facts: dict) -> str`:** concatenates the base system prompt with `"\n\n## Case facts\n" + json.dumps(facts, indent=2)`. Called on every API call inside the loop, not once at the start.

**`TRIM_ORDER_FIELDS` set:** the whitelist of keys to retain from raw `lookup_order` results. Applied in the PostToolUse hook (or in `dispatch_tool`) for any tool named `lookup_order`. Trimming produces a dict with fewer than the raw key count (raw is 40+; trimmed should be 8–12 fields).

**Handoff capture:** the PreToolUse hook that redirects over-$500 refunds now also captures `amount` from inputs and constructs a `handoff` dict:
```python
handoff = {
    "customer_id": case_facts.get("customer_id"),
    "root_cause": f"Refund of ${amount} exceeds $500 policy cap",
    "amount": amount,
    "recommended_action": "Escalate to supervisor for refund exception approval",
}
```
This dict is stored in a mutable variable (e.g., `handoff_info = {}` initialised before the loop; hook writes to it). After the loop, `run_conversation` includes `"handoff": handoff_info` in the return dict only if `handoff_info` is non-empty.

Total additions over M03: approximately 40–60 lines.
