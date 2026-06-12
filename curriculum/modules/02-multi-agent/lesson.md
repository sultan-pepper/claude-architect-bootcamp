# Lesson 02 — Multi-agent orchestration

A single agent loop handles sequential tasks well. Multi-agent architectures exist to do three things that a single loop cannot do cleanly: parallelize independent work, isolate context between specialized workers, and keep the coordinator's context window from growing unboundedly. The cost is that you must pass context explicitly — nothing is shared between agents by default.

## coordinator

The coordinator is the agent that receives the top-level task and breaks it down. It does not perform the work directly; it delegates to subagents. The canonical pattern is hub-and-spoke: one coordinator, N subagents, coordinator aggregates results.

```python
# Coordinator receives task, selects tools for subagents
response = client.messages.create(
    model=model,
    system="You are a research coordinator. Decompose the topic into sub-domains "
           "and spawn search agents for each. Then synthesise all findings.",
    tools=[spawn_search_agent_tool, spawn_synthesis_tool],
    messages=[{"role": "user", "content": topic}],
)
```

The coordinator runs its own agentic loop, using subagent-spawn as its tools. It reasons about what to delegate and aggregates the results into a final output.

Why a coordinator rather than a flat sequence of API calls? The coordinator's model decides the decomposition strategy based on the input. A hardcoded sequence decides it based on programmer assumptions. When the input changes, the coordinator adapts; the hardcoded sequence does not.

## subagent_context

Each subagent is an isolated API call with its own `messages` list and system prompt. It has no access to the coordinator's history, the user's original message, or any other subagent's context.

This isolation is a feature, not a limitation:
- Subagents do not accumulate irrelevant history. A search agent for "container networking" does not need to know what the coordinator said to the "container security" search agent.
- Smaller context windows mean lower latency and token cost.
- Subagent behaviour is reproducible given the same inputs.

The implication: anything a subagent needs must be in its system prompt or user message. There is no implicit shared state.

## context_passing

Because subagents have no shared context, the coordinator must pass findings explicitly when a downstream agent needs them.

A search subagent returns its findings as text. The coordinator must include that text in the synthesis subagent's prompt. It cannot refer to it indirectly ("use the findings from earlier").

```python
# After collecting all search results:
synthesis_prompt = f"""You have received the following research findings:

{chr(10).join(f"## {topic}\\n{result}" for topic, result in findings.items())}

Write a comprehensive report covering all sub-domains above."""

synthesis_response = client.messages.create(
    model=model,
    system="You are a technical writer. Synthesise research findings into a report.",
    messages=[{"role": "user", "content": synthesis_prompt}],
)
```

The common failure mode: the coordinator passes topic names to the synthesis agent ("topics: networking, storage, security") and assumes the synthesis agent already has access to the content. It does not. The synthesis agent will hallucinate or produce a generic report. Pass the actual findings.

Structured data passes more reliably between agents than prose summaries. A JSON dict of `{sub_topic: findings_text}` is unambiguous; a flowing summary may lose boundaries between topics.

## parallel_dispatch

The Anthropic API allows a model to call multiple tools in a single response. A coordinator that has a `spawn_search_agent` tool can call it six times in one assistant turn — once per sub-domain — and the orchestrator code dispatches all six concurrently.

```python
# Coordinator response may contain multiple tool_use blocks:
for block in coordinator_response.content:
    if block.type == "tool_use" and block.name == "spawn_search_agent":
        futures.append(executor.submit(run_search_agent, block.input["sub_topic"]))
```

This is not automatic. You must write the orchestrator to detect multiple tool_use blocks in a single turn and dispatch them concurrently (using `concurrent.futures` or `asyncio`). If you dispatch them serially, you lose the latency benefit.

The alternative approach (always call tools one at a time) still produces correct results but takes 6× longer for 6 independent searches. The coordinator's system prompt should encourage broad parallel decomposition.

## decomposition

The coordinator's decomposition determines coverage. A narrow decomposition — "search for Docker basics" — misses Kubernetes, networking, storage, security, and operations. A broad decomposition — "identify all distinct sub-domains in the corpus and search each" — covers everything.

The decomposition failure mode: the coordinator picks the most obvious or most prominent topics and ignores the rest. This produces a report that reads well but has gaps. The defense is in the coordinator's prompt: explicitly instruct it to identify *all* sub-domains before dispatching, not just the ones it already knows about.

Do not hardcode the sub-domain list in your orchestrator. If you hardcode it, the coordinator becomes brittle — it stops adapting when the corpus changes. Let the coordinator model decide the decomposition.

## goals_criteria

Give subagents goals and quality criteria, not step-by-step procedures. A procedure like "first read doc_001, then read doc_002, summarise each" constrains the model to one strategy and breaks if the documents don't follow the assumed structure.

A goals-and-criteria prompt:
```
Search the provided corpus for all content about "{sub_topic}".
Return: key concepts, critical technical details, and any caveats or known limitations.
Coverage criterion: your response should leave no significant point from the corpus unaddressed.
```

This approach lets the model adapt its search strategy to the actual document content, produces better results when documents vary in structure, and remains valid as the corpus grows.
