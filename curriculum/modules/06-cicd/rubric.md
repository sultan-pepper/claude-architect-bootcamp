# Rubric — 06 cicd

## Criteria

1. **C1-schema-valid** (deterministic): `python ci_review.py --repo-path <fixtures/sample-repo> --output <file>` exits 0; the output file is a JSON array; every element has all six required fields (`file`, `line`, `category`, `severity`, `explanation`, `fingerprint`); `severity` is one of `critical|high|medium|low`; `fingerprint` is a non-empty string — lesson_ref: lesson.md §noninteractive_invocation

2. **C2-bug-coverage** (deterministic): comparing findings against `fixtures/answer_key.json` by `(file, category, line ± 5)`, ≥4 of the 6 seeded bugs appear in the findings — lesson_ref: lesson.md §categorical_criteria

3. **C3-false-positive-rate** (deterministic): the count of findings whose `file` field matches one of the three clean files (`src/shared/__init__.py`, `src/shared/utils.py`, `config/config.py`) is ≤2 — lesson_ref: lesson.md §false_positive_cost

4. **C4-no-duplicate-fingerprints** (deterministic): a second run with `--prior-findings <first-run-output>` produces a findings array where no `fingerprint` value matches any `fingerprint` in the first-run output — lesson_ref: lesson.md §dedup_via_context

## Hints

### Level 1

There are two independent problems. First: does the output parse? Check that `ci_review.py` exits 0 and writes a valid JSON array — run it manually and inspect the file. Second: does the content meet the coverage and false-positive targets? These are prompt-design problems, not code bugs. If the output parses but C2 or C3 fails, the issue is in `review_prompt.md`, not `ci_review.py`.

### Level 2

For C2: if fewer than 4 bugs are found, the prompt's category definitions are too vague. "Find bugs" does not direct Claude to look for mutable default arguments or swallowed exceptions. Name each category with a one-line definition in the prompt. Categories in this repo's bugs: off-by-one, wrong-comparison, unhandled-none, resource-leak, swallowed-exception, mutable-default.

For C3: if more than 2 false positives appear on clean files, the prompt lacks a confidence threshold. Add: "Only report issues you are confident are real defects. Do not report style preferences, missing documentation, or speculative issues that could be improvements."

For C4: the fingerprint must be deterministic across runs. If the fingerprint includes the explanation text or a timestamp, it will differ between runs even for the same bug. Base the fingerprint on `(file, line, category)` only.

### Level 3

Prompt structure for `review_prompt.md`:

```markdown
Review the following code files for exactly these bug categories:

- off-by-one: incorrect range boundaries that miss the first or last element
- unhandled-none: method called on a value that could be None without a guard
- resource-leak: file/socket/connection opened and never closed
- swallowed-exception: except block that catches and then passes or discards silently
- mutable-default: mutable default argument (list, dict, or set) in a function signature
- wrong-comparison: field or value in a comparison that does not match the actual type schema

Only report issues you are confident are real defects. Do not report style preferences,
missing docstrings, or speculative "could be improved" observations.

{% if prior_findings %}
Previously reported findings — do not duplicate these (match by fingerprint):
{{ prior_findings }}
{% endif %}

Files to review:
{% for file_path, content in files %}
=== {{ file_path }} ===
{{ content }}
{% endfor %}

Output a JSON array. Each element must have:
  file (string), line (integer), category (string), severity (critical|high|medium|low),
  explanation (string), fingerprint (string — sha256 of "file:line:category", first 16 hex chars)
```

Script skeleton:

```python
import hashlib, json, os, subprocess, sys
from pathlib import Path

def make_fingerprint(file: str, line: int, category: str) -> str:
    return hashlib.sha256(f"{file}:{line}:{category}".encode()).hexdigest()[:16]

def run_review(repo_path: Path, prior_findings: list[dict], output: Path) -> None:
    prompt = build_prompt(repo_path, prior_findings)
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--output-format", "json",
         "--json-schema", str(Path(__file__).parent / "findings_schema.json")],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        sys.exit(f"claude error: {result.stderr}")
    envelope = json.loads(result.stdout)
    findings = json.loads(envelope["result"])  # inner JSON conforming to schema
    output.write_text(json.dumps(findings, indent=2))
```

## Mentor guardrails

- Do not write the `review_prompt.md` content for the learner.
- If the learner asks why they are missing bugs, ask: "Does your prompt name each category with a definition, or does it use a general instruction like 'find bugs'?"
- If the learner asks why they have false positives, ask: "Does your prompt include an explicit confidence threshold? What does it say about style preferences and speculative issues?"
- If the learner asks about fingerprint stability, point to lesson.md §dedup_via_context and ask: "What fields does your fingerprint hash over? Could any of those fields change between two runs of the same bug?"
- Do not reveal the contents of `fixtures/answer_key.json` or which specific lines contain bugs.
- API-shape examples (`subprocess.run` invocation, JSON envelope structure) are allowed at ≤5 lines provided they are not specific to the inventory solution.
- Do not confirm whether a specific prompt phrasing will pass C2 or C3.

## Reference solution sketch

**`review_prompt.md`**: Defines all 6 categories with one-line definitions each. Includes confidence threshold instruction ("only report if you are confident"). Includes a prior-findings injection block (template variable). Instructs output as JSON array with all 6 required fields including fingerprint construction (sha256 of file:line:category, 16 hex chars). Does not reference the answer key.

**`ci_review.py`**:

- `argparse` with `--repo-path`, `--output`, `--prior-findings` (optional), `--model` (default `claude-haiku-4-5`).
- Reads source files from `--repo-path` for the two known bug files + one or two more for coverage.
- Embeds file contents into the prompt using the template.
- Calls `claude -p "..." --output-format json --json-schema findings_schema.json` via `subprocess.run`.
- Parses the JSON envelope: `envelope = json.loads(stdout)`, `findings = json.loads(envelope["result"])`.
- Adds/overwrites fingerprints: `hashlib.sha256(f"{f}:{l}:{c}".encode()).hexdigest()[:16]`.
- If `--prior-findings` provided, injects into prompt template and filters any findings with matching fingerprints from the output as a second defense.
- Writes findings array to `--output`.
- Exit 0 on success; exit 1 on harness error.

**`findings_schema.json`**: exact schema from lab.md, committed in workspace.

**`.gitlab-ci.yml` template**: single stage `code-review`, image `python:3.12-slim`, installs `anthropic`, clones the Claude CLI or uses the Python SDK directly, runs `python ci_review.py --repo-path . --output findings.json`, archives `findings.json` as artifact. `ANTHROPIC_API_KEY` provided as CI secret variable.

Total: approximately 80–120 lines in ci_review.py.
