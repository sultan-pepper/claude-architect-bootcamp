# M09 workspace — Capstone: escalation & reliability

## Deliverables

One file: `agent.py`. The checks import it and call `run_scenario` directly.

## Entry point

```python
def run_scenario(scenario_name: str) -> dict:
    ...
```

Loads the named scenario from `fixtures/conversations.json`, drives the agent through each turn, and returns the result dict below.

## Return shape

```json
{
  "transcript": [...],
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

`partial_results` when non-null:
```json
{
  "successful": ["O001", "O007"],
  "failed":     ["O999"],
  "coverage":   "partial"
}
```

## Scenario names

| Scenario name | What it tests |
|---|---|
| `m9-straightforward-no-escalation` | Resolvable case — must NOT escalate |
| `m9-policy-gap-must-escalate` | $768.99 refund — must escalate |
| `m9-explicit-human-request` | "Talk to a real person" — escalate immediately, first tool call |
| `m9-ambiguous-identity-alex-rivera` | Two "Alex Rivera" — ask clarifying question, no account action |
| `m9-subagent-timeout-simulation` | Some order IDs fail — return partial_results with coverage annotation |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model for all API calls |
| `ANTHROPIC_API_KEY` | (required) | API key |
| `FIXTURES_PATH` | `../fixtures` | Path to this module's fixtures/ directory |
| `AGENT_LOG_PATH` | (unset) | When set, write JSON log with two entries: main_conversation and self_eval message histories |

## Running manually

```bash
python agent.py m9-straightforward-no-escalation
python agent.py m9-explicit-human-request
AGENT_LOG_PATH=/tmp/agent_log.json python agent.py m9-ambiguous-identity-alex-rivera
```

## Checks

```bash
bootcamp check   # runs all six criteria
bootcamp hint    # unlock hints one level at a time (requires a failed check run first)
```
