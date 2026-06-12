# Lab 06 — CI/CD integration

## Mission

Build a CI code-review pipeline that uses Claude to find real bugs in the provided sample repository. The pipeline must emit schema-valid JSON findings, catch ≥4 of 6 seeded bugs, produce ≤2 false positives on clean files, and suppress previously-reported findings on a second run. Correct prompt design — explicit categorical criteria, no vague conservatism — is the central skill being evaluated.

## Workspace entry-point contract

**Files:**
- `workspace/ci_review.py` — the review script; the checker runs it as:
  ```bash
  python ci_review.py \
    --repo-path <path-to-sample-repo> \
    --output <output-file> \
    [--prior-findings <prior-findings-file>]
  ```
- `workspace/review_prompt.md` — your prompt template, read by `ci_review.py`

The script must exit 0 on success (regardless of whether findings were found) and non-zero on harness error (API failure, schema error, missing input). Do not exit non-zero simply because findings exist.

**Model:** read from env `ANTHROPIC_MODEL`, default `claude-haiku-4-5`.

**Required ANTHROPIC_API_KEY:** all checks in this module call the real API and are skipped with status `SKIP` if `ANTHROPIC_API_KEY` is not set.

## Findings JSON schema

Your script must output a JSON file conforming to this schema (also in `findings_schema.json`):

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["file", "line", "category", "severity", "explanation", "fingerprint"],
    "properties": {
      "file":        {"type": "string",  "description": "Relative path from repo root"},
      "line":        {"type": "integer", "description": "Line number of the issue"},
      "category":    {"type": "string",  "description": "Issue category (match your prompt's defined categories)"},
      "severity":    {"type": "string",  "enum": ["critical", "high", "medium", "low"]},
      "explanation": {"type": "string",  "description": "One-sentence explanation of the issue"},
      "fingerprint": {"type": "string",  "description": "Stable hash across runs for the same bug; used for dedup"}
    }
  }
}
```

All six fields are required. `severity` must be one of the four enum values. `fingerprint` must be non-empty and stable: the same bug at the same location must produce the same fingerprint on every run, even if the explanation text differs.

**Fingerprint construction**: hash `(file, line, category)` together. A simple approach:

```python
import hashlib
fingerprint = hashlib.sha256(f"{file}:{line}:{category}".encode()).hexdigest()[:16]
```

## Fixtures available

`fixtures/sample-repo/` is the repository to review. It contains **6 seeded bugs** and **3 clean files**. The bugs span two files; the clean files have no intentional defects.

An answer key exists at `fixtures/answer_key.json` — it is used by the checker and is off-limits for your prompt. Do not read or reference it. The checker compares your findings against it; you don't need to.

**Bug files:**
- `src/worker-service/process.py` — 3 bugs
- `src/api-service/main.py` — 2 bugs
- `src/worker-service/worker.py` — 1 bug

**Clean files (no intentional bugs):**
- `src/shared/__init__.py`
- `src/shared/utils.py`
- `config/config.py`

The 6 bug categories (seeded in the repo, not their locations — find those yourself): off-by-one, wrong-comparison, unhandled-none, resource-leak, swallowed-exception, mutable-default.

## What `bootcamp check` does

All four checks call the real API and are skipped without `ANTHROPIC_API_KEY`.

1. **C1-schema-valid**: runs `python ci_review.py --repo-path <fixtures/sample-repo> --output /tmp/findings.json`; parses the output file; validates it is a JSON array where every element satisfies the findings schema. Fails if any required field is missing, `severity` is not in the enum, or `fingerprint` is empty.

2. **C2-bug-coverage**: counts how many of the 6 seeded bugs appear in the findings, matched against `answer_key.json` by file path + category + line number within ±5 lines. Passes if ≥4 bugs are covered.

3. **C3-false-positive-rate**: counts findings whose `file` field is one of the three clean files. Passes if ≤2 such findings exist across all clean files.

4. **C4-no-duplicate-fingerprints**: runs the script a second time providing the first run's findings as prior: `python ci_review.py --repo-path <fixtures/sample-repo> --prior-findings /tmp/findings.json --output /tmp/findings2.json`; verifies no fingerprint in the second output matches any fingerprint from the first output.

## Recommended approach

### Prompt design (review_prompt.md)

Your prompt template should include:
- The exact category names you want Claude to use (these become the `category` field values)
- The instruction "only report issues you are confident are real bugs"
- The instruction "do not report style preferences, missing documentation, or speculative issues"
- The instruction to output JSON conforming to the schema (paste the schema into the prompt or reference the field names explicitly)
- A prior-findings section (templated with `{{ prior_findings }}`) that the script populates on subsequent runs

### Script design (ci_review.py)

The script:
1. Reads the files from `--repo-path` and embeds their content in the prompt.
2. Reads `--prior-findings` (if provided) and injects the prior findings JSON into the prompt at the `{{ prior_findings }}` slot.
3. Calls `claude -p "..."` with `--output-format json --json-schema findings_schema.json`.
4. Parses the JSON envelope from Claude's output to extract the findings array.
5. Writes the findings array to `--output`.

### GitLab CI (optional)

A starter `.gitlab-ci.yml` template is in your workspace. Adapt it to wire the review into your own GitLab pipeline. This is not checked — it is provided for teams who want to run the pipeline for real.

## Acceptance criteria

C1 through C4 must all pass (or be SKIP if `ANTHROPIC_API_KEY` is not set — SKIP does not count as fail).

The bug-coverage target (≥4/6) and false-positive cap (≤2 on clean files) are not tight — they reflect good prompt design, not model perfection. If you are catching fewer bugs, the prompt's category definitions are too vague. If you are generating too many false positives on clean files, the prompt lacks a "confidence threshold" instruction.
