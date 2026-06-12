# M02 workspace — Multi-agent orchestration

## Entry point

`pipeline.py` — this is the only file the checks interact with.

## Contract

Implement and export:

```python
def run_pipeline(topic: str) -> dict:
    ...
```

Returns:
```json
{
  "report": "string",
  "run_log": {
    "coordinator_turns": [{"tool_calls": [{"name": "...", "input": {...}}]}],
    "subagent_calls":    [{"sub_topic": "...", "system_prompt": "...", "result": "..."}],
    "synthesis_call":    {"user_prompt": "...", "result": "..."}
  }
}
```

When run as `__main__`, reads the topic from `sys.argv[1]` and writes the
result as JSON to stdout:

```bash
python pipeline.py "Containerization and Orchestration"
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model for all agent calls |
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `FIXTURES_PATH` | `../fixtures` | Absolute path to this module's fixtures/ dir |

## Fixtures

Corpus documents are at `$FIXTURES_PATH/corpus/*.md` (12 files, six sub-domains).
`corpus_index.json` in the same directory maps each doc to its sub-domain.
Your orchestrator code may read `corpus_index.json`; the coordinator model
prompt should not receive it — let the coordinator reason about decomposition.

## Dependencies

This module builds on the agentic loop pattern from M01. If you have not
completed M01, read `lesson.md §coordinator` and implement the standard
`while True / stop_reason` loop in your coordinator before adding subagents.

## Running manually

```bash
python pipeline.py "Containerization and Orchestration"
```

## Checks

```bash
bootcamp check   # runs all four criteria
bootcamp hint    # unlock hints one level at a time (requires a failed check run first)
```
