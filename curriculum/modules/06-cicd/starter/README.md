# M06 workspace — CI/CD integration

## Entry points

| File | Role |
|---|---|
| `ci_review.py` | Review script — the checker runs this |
| `review_prompt.md` | Prompt template — read by `ci_review.py` |
| `findings_schema.json` | JSON Schema for the findings output — pass to `--json-schema` |
| `.gitlab-ci.yml` | GitLab CI template — adapt for your own pipeline (not checked) |

## CLI contract

```bash
python ci_review.py \
  --repo-path /path/to/sample-repo \
  --output findings.json \
  [--prior-findings prior_findings.json]
```

Exit 0 on success. Exit non-zero only on harness errors (API failure, bad arguments). Exit 0 even when findings are empty — empty is a valid result.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | All checks are skipped without this |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model for review calls |

## Checks

```bash
bootcamp check    # runs C1–C4 (skipped without ANTHROPIC_API_KEY)
bootcamp hint     # unlock hints one level at a time (requires a failed check run first)
```

## Key design points to get right

1. **Categorical criteria**: name each bug category explicitly in your prompt with a one-line definition. "Find bugs" is not enough.
2. **Confidence threshold**: include "only report issues you are confident are real defects" to suppress false positives.
3. **Fingerprint stability**: hash `(file, line, category)` — not the explanation. The fingerprint must be identical on every run for the same bug.
4. **Prior findings dedup**: when `--prior-findings` is provided, inject the prior findings into the prompt and filter any output that duplicates a prior fingerprint.

## Running manually

```bash
cp -r ../../../curriculum/modules/06-cicd/fixtures/sample-repo ./sample-repo

# First run
python ci_review.py --repo-path ./sample-repo --output findings.json

# Second run with dedup
python ci_review.py --repo-path ./sample-repo --prior-findings findings.json --output findings2.json

# Inspect
cat findings.json | python -m json.tool
```
