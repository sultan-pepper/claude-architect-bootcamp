# Lab 02 — Multi-agent orchestration

## Mission

Build a multi-agent research pipeline that reads the corpus in `fixtures/corpus/` and produces a comprehensive report on "Containerization and Orchestration". The pipeline must use a coordinator agent, parallel search subagents (one per sub-domain), and a synthesis subagent. The coordinator drives decomposition; you must not hardcode the sub-domain list.

## Workspace entry-point contract

**File:** `pipeline.py` (at the root of your workspace).

**Importable function:**

```python
def run_pipeline(topic: str) -> dict:
    ...
```

**Return shape:**

```json
{
  "report": "final synthesis report text",
  "run_log": {
    "coordinator_turns": [
      {
        "tool_calls": [
          {"name": "spawn_search_agent", "input": {"sub_topic": "..."}}
        ]
      }
    ],
    "subagent_calls": [
      {
        "sub_topic": "string",
        "system_prompt": "full system prompt given to this subagent",
        "result": "subagent response text"
      }
    ],
    "synthesis_call": {
      "user_prompt": "full user prompt given to synthesis subagent",
      "result": "synthesis response text"
    }
  }
}
```

`coordinator_turns` records each assistant turn in the coordinator's loop — specifically which tool calls appeared in that turn. If the coordinator dispatches six search subagents in one turn, that one entry has six items in `tool_calls`. This is how the parallel-dispatch check is verified.

`subagent_calls` records every search subagent invocation: the sub-topic, the full system prompt sent to it, and its result.

`synthesis_call` records the full user prompt sent to the synthesis subagent (must include the actual findings from all search subagents) and the synthesis result.

**CLI invocation:** when run as `__main__`, `pipeline.py` reads the topic string from `sys.argv[1]` and writes the return dict as JSON to stdout:

```bash
python pipeline.py "Containerization and Orchestration"
```

**Model:** read from env `ANTHROPIC_MODEL`, default `claude-haiku-4-5`.

**Fixtures path:** the checks set `FIXTURES_PATH` env var. Your pipeline reads corpus documents from `$FIXTURES_PATH/corpus/`.

## What to build

### Coordinator agent

A standard agentic loop (from M01) with one tool: `spawn_search_agent(sub_topic: str)`. The coordinator receives the topic, reasons about what sub-domains exist, and calls `spawn_search_agent` for each. It should call multiple tools in a single response to enable parallel dispatch. After receiving all search results, it calls `spawn_synthesis_agent(findings: dict)` or equivalent to produce the final report.

Your coordinator should not dictate *how* to search — instruct it to identify sub-domains and delegate.

### Search subagent

Each search subagent is an isolated `client.messages.create` call (not a loop — a single call is enough for document search). It receives:
- A system prompt identifying its role and the sub-topic it covers
- A user message containing the relevant corpus documents

It returns a text summary of the sub-domain. The corpus documents are plain markdown; read them from `fixtures/corpus/*.md`.

The search subagent should not receive any context from other search agents or from the coordinator's history. Its system prompt is constructed entirely by your orchestrator code.

### Parallel dispatch

When the coordinator's response contains multiple `spawn_search_agent` tool_use blocks in a single turn, dispatch all of them concurrently. Use `concurrent.futures.ThreadPoolExecutor` or `asyncio`. Record each batch in `run_log.coordinator_turns`.

### Synthesis subagent

A single API call that receives all search findings and writes the final report. The user prompt must include the actual text returned by every search subagent — not just topic names. Record the full user prompt in `run_log.synthesis_call.user_prompt`.

## Fixtures

**`fixtures/corpus/`** — 12 markdown documents covering the topic "Containerization and Orchestration" across six sub-domains:
- **Containers** — docs 001, 002 (fundamentals, Docker images)
- **Orchestration** — docs 003, 004, 012 (Kubernetes basics, deployments, multi-container patterns)
- **Networking** — docs 005, 006 (container networking, Kubernetes ingress)
- **Storage** — doc 007 (persistent volumes)
- **Security** — doc 008 (container security)
- **Operations** — docs 009, 010, 011 (monitoring, config management, resource management)

**`fixtures/corpus/corpus_index.json`** — maps each document filename to its sub-domain. Your orchestrator may use this to load documents; the coordinator model should not see it (the coordinator should reason about decomposition, not read a ground-truth list).

## Acceptance criteria

**C1-all-subdomains.** The final report covers all six sub-domains: Containers, Orchestration, Networking, Storage, Security, Operations. The checker searches the report text for substantive mentions of each.

**C2-context-passing.** `run_log.synthesis_call.user_prompt` contains actual findings text from the search subagents — not just sub-topic names. The checker verifies the prompt length exceeds a minimum threshold and contains text derived from the corpus.

**C3-parallel-dispatch.** At least one entry in `run_log.coordinator_turns` has `len(tool_calls) >= 2`. The coordinator dispatched multiple search tasks in a single API response turn.

**C4-report-quality** (judge). The report demonstrates substantive coverage of each of the six sub-domains with specific technical content. A thin report that mentions each topic in one sentence does not pass.

## What `bootcamp check` does

- Calls `run_pipeline("Containerization and Orchestration")` imported from `pipeline.py`.
- Inspects `run_log.coordinator_turns` for parallel dispatch (C3).
- Inspects `run_log.synthesis_call.user_prompt` for content from search results (C2).
- Searches report text for each of the six subdomain names (C1).
- Passes the report to the LLM judge with the C4 rubric excerpt (C4).
