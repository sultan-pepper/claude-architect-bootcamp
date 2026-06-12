# Rubric — 02 multi-agent

## Criteria

1. **C1-all-subdomains** (deterministic): the final report contains substantive mentions of all six sub-domains — Containers, Orchestration, Networking, Storage, Security, Operations — lesson_ref: lesson.md §decomposition
2. **C2-context-passing** (deterministic): `run_log.synthesis_call.user_prompt` is substantive (contains actual findings text from search subagents, not just sub-topic names) — lesson_ref: lesson.md §context_passing
3. **C3-parallel-dispatch** (deterministic): at least one `coordinator_turns` entry has `len(tool_calls) >= 2`, confirming multiple subagents were dispatched in a single coordinator response turn — lesson_ref: lesson.md §parallel_dispatch
4. **C4-report-quality** (judge): the report provides technically specific coverage of each of the six sub-domains — not just surface mentions; each section should contain facts from the corpus — lesson_ref: lesson.md §goals_criteria

## Hints

### Level 1
Think about information flow. The synthesis agent needs to know what each search agent found — where does that information live, and how does it travel from search agents to the synthesis agent? Also consider how many API calls can happen at the same time versus one after another.

### Level 2
Each subagent is an isolated API call with no access to other agents' history. The coordinator must explicitly pass search findings to the synthesis subagent in its prompt. For parallel dispatch: the coordinator's `spawn_search_agent` tool can be called multiple times in one model response — detect multiple `tool_use` blocks in a single assistant turn and dispatch them concurrently with `ThreadPoolExecutor` or `asyncio`.

### Level 3
Coordinator loop structure:
```python
# coordinator_response may have multiple tool_use blocks in one turn:
batch = [b for b in response.content if b.type == "tool_use"]
if len(batch) >= 2:
    with ThreadPoolExecutor() as ex:
        futures = {b.input["sub_topic"]: ex.submit(run_search, b.input) for b in batch}
    results = {topic: f.result() for topic, f in futures.items()}

# After all searches complete, build synthesis prompt:
synthesis_prompt = "\n\n".join(f"## {t}\n{r}" for t, r in results.items())
# pass synthesis_prompt as user content to synthesis subagent
```

## Mentor guardrails

- Do not write the coordinator system prompt or synthesis prompt for the learner.
- If the learner asks how to pass findings to the synthesis agent, point to `lesson.md §context_passing` and ask: "what does the synthesis agent's message list look like at the moment it is called?"
- If the learner's parallel dispatch is serial (one search at a time), ask them to look at what `run_log.coordinator_turns[*].tool_calls` contains — do multiple tool calls appear in one turn?
- Do not confirm whether a particular `run_log` structure passes C2 or C3 — describe what each criterion checks and let the learner inspect their own log.
- API-shape examples are allowed at ≤5 lines if they illustrate the message list structure rather than the specific pipeline solution.

## Reference solution sketch

**`pipeline.py` structure:**

`CORPUS_PATH`: derived from `FIXTURES_PATH` env var. Read all `*.md` files from `corpus/` at startup.

**`run_search_agent(sub_topic, relevant_docs) -> str`:** single `client.messages.create` call; system prompt is "You are a technical researcher covering {sub_topic}. Use only the documents provided."; user message contains the concatenated relevant doc text. Returns response text. This is not a loop — one call, one result.

**`run_synthesis_agent(findings: dict[str, str]) -> str`:** single call; user prompt contains all findings formatted as `## {sub_topic}\n{text}` blocks. Returns report text.

**`run_pipeline(topic) -> dict`:** builds `messages` and `TOOLS = [spawn_search_agent_schema]`. Runs coordinator loop (standard M01 pattern). In the tool dispatch for `spawn_search_agent`, does not call immediately — collects all tool_use blocks from the current turn, dispatches them with `ThreadPoolExecutor`, records the batch in `coordinator_turns`. After all searches complete, appends all tool_results, continues coordinator loop. When coordinator signals `end_turn` or calls synthesis tool, calls `run_synthesis_agent`. Records everything in `run_log`. Returns `{"report": ..., "run_log": ...}`.

**Coordinator system prompt key instruction:** "Identify all distinct sub-domains in the provided topic. Call spawn_search_agent for every sub-domain simultaneously in a single response."

Total: approximately 120–180 lines.
