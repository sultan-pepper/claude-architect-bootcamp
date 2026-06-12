# Lesson 06 — CI/CD integration

Running Claude in a CI pipeline is different from running it interactively. The prompt must be complete and self-contained; the output must be structured for machine consumption; the same code will be reviewed on every commit. Getting these constraints right is the difference between a review tool that the team trusts and one they learned to ignore.

## noninteractive_invocation

`claude -p "PROMPT"` runs Claude non-interactively: one prompt in, one response out, process exits. The `-p` flag suppresses the interactive REPL.

Two output format flags:

**`--output-format json`**: Claude's response is wrapped in a JSON envelope:

```json
{
  "type": "result",
  "result": "<response text or JSON>",
  "cost_usd": 0.0012,
  "duration_ms": 3400
}
```

**`--output-format json --json-schema <schema-file>`**: Claude's response text itself must conform to the JSON Schema in the named file. The CLI validates the output and retries internally if the response is malformed. Use this to guarantee the findings list is a parseable array even when the model hedges or adds prose.

Invocation pattern:

```bash
claude -p "$(cat review_prompt.md)" \
       --output-format json \
       --json-schema findings_schema.json \
       < /dev/null
```

`< /dev/null` prevents stdin blocking when the process is launched without a terminal. Pass code content inside the prompt string rather than relying on Claude to find and open files — in CI, Claude runs without a project context unless you provide one.

The exit code is 0 on success and non-zero on error. In a pipeline, treat non-zero as a harness failure, not a "no findings" result — distinguish them.

## categorical_criteria

Vague review instructions produce noisy, inconsistent findings. "Find bugs and be conservative" is not a criterion — it is an instruction for the model to invent a standard on every run, and it will choose differently each time.

Write explicit category definitions:

```
Review the following code for exactly these issue categories:
- off-by-one: incorrect range boundaries, fencepost errors, loop counts that miss the last or first element
- unhandled-none: calling a method on a value that could be None without a None check
- resource-leak: file descriptors, DB connections, or sockets opened but not closed
- swallowed-exception: except blocks that catch and then pass or discard without logging or re-raising
- mutable-default: mutable default argument in a function definition (list, dict, set)
- wrong-comparison: comparing against a value or field name that doesn't exist in the expected type

For each finding output: file, line number, category (one of the above), severity (critical/high/medium/low),
a one-sentence explanation, and a stable fingerprint.

Only report issues you are confident are real bugs. Do not report style preferences, missing docstrings,
or speculative "could be improved" observations.
```

Why this works:

1. **Variance reduction**: the model classifies against a closed set rather than an open vocabulary. "Off-by-one" is the same category on every run.
2. **Downstream reliability**: the checker compares `category` to a fixed answer key. Open-vocabulary categories cannot be compared programmatically.
3. **Attention direction**: naming categories explicitly causes the model to look for each one in turn, improving recall for less obvious bugs (mutable default arguments are easy to miss on a casual read).

"Do not report style preferences" is load-bearing. Without it, a significant fraction of findings will be opinions about naming, whitespace, and docstring coverage.

## false_positive_cost

A false positive — flagging clean code as a bug — has compounding costs:

**Attention erosion.** Developers scan AI findings when they arrive, evaluate them against the code, and judge most of them wrong within the first few false positives. Once that pattern is established, they stop reading. A tool with a 20% false-positive rate trains developers to ignore it within a week.

**Trust damage.** A finding that appears on every run for code that was reviewed and accepted as correct tells the team: the tool does not know what it is doing. This perception is hard to reverse even after improving the prompt.

**Gate failure.** If the pipeline blocks a merge on any finding, false positives block real work. Developers then request exceptions or disable the gate entirely.

Design criteria to accept missed detections in exchange for fewer false positives. A pipeline that catches 4 of 6 real bugs with 0 false positives is operationally more valuable than one that catches all 6 with 4 false positives. The former is trusted and acted on; the latter is bypassed.

The quantitative target for this lab: ≥4 of 6 bugs caught, ≤2 false positives across 3 clean files. That is a deliberate trade-off in the criteria design, not a floor to minimize.

## dedup_via_context

On a second run over the same code, Claude must not re-report findings already surfaced in the previous run. The mechanism: inject the prior findings list into the prompt as context.

```
Previously reported findings (do not duplicate):
{{ prior_findings_json }}

Review the same code and report only NEW findings not already in the list above.
Match against prior findings by fingerprint — if the fingerprint matches, skip it.
```

**Fingerprint design**: a stable identifier for a finding derived from `(file, line ± tolerance, category)` rather than from the explanation text (which varies between runs). Hash these fields together. The fingerprint must be stable across runs for the same underlying bug — it is the dedup key, not a display value.

The workflow:

1. **Run 1**: no prior findings → full review → produce `findings.json`.
2. **Review**: team dismisses false positives, files tickets for real bugs.
3. **Run 2 (next commit)**: inject `findings.json` from run 1 as prior context → only findings with new fingerprints are reported.

Without this mechanism, every pipeline run produces the same list including acknowledged issues. The developer's response to the second run ("same findings as last time") is to stop reading the output.

The test: the checker runs the pipeline twice, providing the first run's findings as prior context for the second. No fingerprint from the second run may match any fingerprint from the first.

## independent_instance

Claude review of code it generated is less reliable than review by an independent instance. This is not bias in the philosophical sense — it is context. When Claude has the code in its conversation history, its review is informed by the reasoning it used when generating. It knows what it intended the code to do; it evaluates the code against that intent rather than against what the code actually does.

In CI, the review instance is always fresh: it receives the code file contents and the review prompt with no prior conversation. This is the correct setup. It matches human code-review norms: the author does not review their own PR.

The same principle applies to any self-evaluation:
- Structured output validation: don't validate with the same instance that generated the output.
- Test generation: don't evaluate test coverage with the instance that wrote the tests.
- Documentation review: don't assess correctness with the instance that wrote the documentation.

In a CI pipeline, the review instance is automatically independent because pipelines are stateless. In an interactive session, independence requires explicitly starting a new conversation or using a subagent context.

## sync_vs_batches

Two API modes for pipeline integration:

**Synchronous (`messages.create`)** blocks until the response arrives and is billed at standard rates. Use for blocking CI checks: the pipeline waits for the result, interprets pass/fail, and continues or halts. Typical latency: a few seconds for short prompts, 30–90 seconds for a code-review prompt covering multiple files. This is the correct mode for pre-merge gates.

**Batches API (`message_batches.create`)** is asynchronous with up to 24-hour completion and 50% cost reduction versus synchronous calls. Each request is submitted with a `custom_id` string. You poll for results or use a webhook. Constraints: each request is single-shot (no multi-turn tool use); polling is required; results arrive in batch, not individually.

```python
# Batches API shape (not for lab — lesson concept only)
batch = client.beta.messages.batches.create(
    requests=[
        MessageCreateParamsNonStreaming(
            custom_id="review-process-py",
            params={"model": ..., "messages": [...], "max_tokens": 1024},
        ),
    ]
)
# Poll: client.beta.messages.batches.retrieve(batch.id)
# Results: client.beta.messages.batches.results(batch.id)
```

When to use Batches:
- Nightly full-repository audits where results are consumed hours later.
- Historical analysis of a large commit range.
- Any pipeline where the developer will read results at their own cadence, not immediately.

When not to use Batches:
- Pre-merge gates that block the pipeline — the 24-hour window is incompatible with a synchronous CI step.
- Any task requiring multi-turn tool use — Batches supports single-shot requests only.

The lab uses the synchronous API for the blocking check. The Batches API is a lesson concept for overnight workflows.
