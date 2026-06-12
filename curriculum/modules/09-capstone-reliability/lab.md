# Lab 09 — Capstone: escalation & reliability

## Mission

Build a production-grade support agent that integrates structured output (M07), context management (M08), hooks (M03), and multi-agent patterns (M02) into a single system. Add explicit escalation criteria with few-shot examples, immediate honouring of human requests, identity clarification on ambiguous matches, structured partial-result propagation from failed lookups, and independent self-evaluation using a separate API conversation.

## Workspace entry-point contract

**File:** `agent.py` at the root of your workspace.

**Importable function:**

```python
def run_scenario(scenario_name: str) -> dict:
    ...
```

**Arguments:** `scenario_name` is one of the scenario ids in `fixtures/conversations.json`:
- `"m9-straightforward-no-escalation"`
- `"m9-policy-gap-must-escalate"`
- `"m9-explicit-human-request"`
- `"m9-ambiguous-identity-alex-rivera"`
- `"m9-subagent-timeout-simulation"`

The function loads the named script from `fixtures/conversations.json`, drives the agent through each turn in sequence, and returns:

```json
{
  "transcript": [
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": [...]},
    {"role": "user",      "content": [{"type": "tool_result", ...}]},
    ...
  ],
  "outcome": {
    "escalated":           false,
    "clarification_asked": false,
    "partial_results":     null,
    "self_eval": {
      "verdict":   "PASS",
      "reasoning": "..."
    }
  }
}
```

Field semantics:
- `transcript`: full messages list from the main agent conversation — all turns across all script turns, concatenated.
- `outcome.escalated`: `true` if `escalate_to_human` was called at any point during the scenario.
- `outcome.clarification_asked`: `true` if the agent asked a clarifying question to resolve identity ambiguity (set this flag in your code when the condition is met; the checker also verifies via transcript inspection for C4).
- `outcome.partial_results`: `null` when all lookups succeeded; otherwise a dict:
  ```json
  {
    "successful": ["O001", "O007"],
    "failed":     ["O999"],
    "coverage":   "partial"
  }
  ```
  Set `coverage: "full"` only when every requested lookup succeeded. Set `"partial"` when at least one failed.
- `outcome.self_eval`: always present — a second, independent API call that evaluates the main transcript against the escalation criteria. Must contain `verdict` (string: `"PASS"` or `"FAIL"`) and `reasoning` (non-empty string).

**CLI invocation:**

```bash
python agent.py <scenario_name>
```

Reads `scenario_name` from `sys.argv[1]`, calls `run_scenario`, prints result as JSON to stdout.

**Model:** `ANTHROPIC_MODEL` env var, default `claude-haiku-4-5`.

**Fixtures path:** `FIXTURES_PATH` env var, same as prior modules.

**Run log:** when `AGENT_LOG_PATH` env var is set to a file path, write a JSON array to that path with one entry per API conversation:
```json
[
  {"role": "main_conversation", "messages": [...]},
  {"role": "self_eval",         "messages": [...]}
]
```
The checker sets this env var to verify that two distinct message histories exist.

## What to build

### Escalation criteria in the system prompt

Define escalation criteria as a closed list with few-shot examples (see lesson §explicit_escalation_criteria). Include:
1. Refund amount exceeds $500 policy cap → escalate.
2. Customer explicitly requests a human agent → escalate immediately, no investigation first.
3. Resolution requires authority beyond available tools → escalate.

Include negative examples showing what does NOT trigger escalation (customer frustration, recoverable errors, resolvable questions).

### Identity clarification

When `find_customers` returns more than one result, ask for a disambiguating identifier before calling any account-specific tool. Do not pick a result heuristically. Your code (not just the model's prompt) should track whether clarification was asked and set `outcome.clarification_asked = True`.

### Structured partial results

When a `lookup_order` call raises a `KeyError` (order not found), record the order ID in a `failed` list. Record successful lookups in a `successful` list. After all lookups are attempted, set `outcome.partial_results` from these lists. If `failed` is non-empty, set `coverage: "partial"`.

### Self-evaluation

After the main scenario conversation completes, make a second API call with a fresh message history. Pass the main transcript and outcome as data in the user message. Ask the evaluator to assess whether the escalation decisions match the explicit criteria. Extract `verdict` and `reasoning` from the response. Store as `outcome.self_eval`.

The self-eval must not share message history with the main conversation. It must be a separate `client.messages.create` call with `messages` initialised to a new list.

## Fixtures

**`fixtures/support_backend.py`:** identical to M01/M03/M08. Key records:
- **Two "Alex Rivera" customers:** C009 (alex.r.1@example.com, gold tier, $4,550.99 spend) and C010 (alex.r.2@example.com, bronze tier, $650.25 spend). `find_customers("Alex Rivera")` returns both.
- **Order O004:** total $768.99, exceeds $500 policy cap — policy-gap scenario.
- **Order O001:** status DELIVERED — straightforward scenario.

**`fixtures/conversations.json`:** five scenario scripts. Each script has one or two turns with `user_message` and `expected_outcome` annotations. The `expected_outcome` annotations describe intent; the checks evaluate the structural outcome dict, not prose quality.

## Acceptance criteria

Six deterministic checks. All must pass.

**C1-no-escalation-straightforward.** Run `run_scenario("m9-straightforward-no-escalation")`. `outcome.escalated` must be `false`. Any call to `escalate_to_human` in this scenario is a failure — the case is resolvable.

**C2-policy-escalation.** Run `run_scenario("m9-policy-gap-must-escalate")`. `outcome.escalated` must be `true`. The checker also verifies that `support_backend.ESCALATION_LOG` contains at least one entry after the call.

**C3-immediate-human-request.** Run `run_scenario("m9-explicit-human-request")`. `outcome.escalated` must be `true`. Additionally: the checker inspects the transcript and verifies that `escalate_to_human` is the first `tool_use` block name in the transcript. Any other tool name appearing as a `tool_use` block before `escalate_to_human` is a failure.

**C4-clarification-on-ambiguity.** Run `run_scenario("m9-ambiguous-identity-alex-rivera")`. `outcome.clarification_asked` must be `true`. The checker also inspects the transcript for turn 1: after `find_customers` is called and returns two results, there must be no `get_customer`, `lookup_order`, or `process_refund` tool call in the same assistant turn. The agent must end turn 1 without acting on either account.

**C5-partial-results.** Run `run_scenario("m9-subagent-timeout-simulation")`. `outcome.partial_results` must be a non-null dict containing `successful` (list), `failed` (list), and `coverage` (string). The `failed` list must be non-empty (at least one order ID that raised KeyError during the scenario). The `coverage` value must be `"partial"` when `failed` is non-empty.

**C6-self-eval-independent.** Run any scenario with `AGENT_LOG_PATH` set. The checker reads the log file and verifies: (a) the log contains at least 2 entries; (b) one entry has `role == "main_conversation"` and one has `role == "self_eval"`; (c) the `messages` list in the `self_eval` entry does not contain any messages from the `main_conversation` messages list (no shared message objects). This verifies that the self-evaluation is a fresh conversation, not an extension of the main one.

## What `bootcamp check` does

- Imports `agent.py` from your workspace and calls `run_scenario` directly.
- Resets `support_backend.REFUND_LOG` and `support_backend.ESCALATION_LOG` before each check.
- For C3: scans `transcript` for `tool_use` blocks in definition order and checks the name of the first one.
- For C4: scans the assistant turn immediately following the `find_customers` tool call in turn 1 for any account-specific tool calls.
- For C6: sets `AGENT_LOG_PATH` to a temporary file, reads and parses the log after the call.
- Does not evaluate prose quality — only the structured `outcome` dict and transcript structure.
