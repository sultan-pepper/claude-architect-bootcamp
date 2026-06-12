# Lab 07 — Structured output & extraction

## Mission

Build an extraction pipeline that processes 10 messy plain-text invoices from `fixtures/invoices/`. You will use tool_use schemas to guarantee output structure, nullable fields to prevent fabrication, semantic validation to detect arithmetic conflicts, retry on correctable failures, and correct classification of unretryable absence.

## Workspace entry-point contract

**File:** `extract.py` at the root of your workspace.

**Importable function:**

```python
def extract_invoice(text: str) -> dict:
    ...
```

**CLI invocation:**

```bash
python extract.py fixtures/invoices/invoice_001.txt
```

Reads the named file, calls `extract_invoice` on its text content, prints the result as a single JSON object to stdout.

**Output schema — every key always present:**

```json
{
  "invoice_number":  "string | null",
  "date":            "string | null",
  "customer":        "string | null",
  "line_items": [
    {
      "description": "string",
      "quantity":    "number",
      "unit":        "string",
      "unit_price":  "number | null",
      "subtotal":    "number | null"
    }
  ],
  "stated_total":    "number | null",
  "calculated_total": "number",
  "conflict_detected": "boolean",
  "api_call_count":  "integer"
}
```

Field notes:
- `date`: YYYY-MM-DD format when extractable; `null` when absent.
- `unit` in `line_items`: unit of measure as written (e.g., `"hr"`, `"each"`, `"box"`); empty string if not stated.
- `calculated_total`: sum of `subtotal` for all line items where `subtotal` is not null; `0.0` if no computable subtotals.
- `conflict_detected`: `true` when `stated_total` is not null and `calculated_total` exceeds `stated_total` by more than `$0.01`. This captures the case where line items sum to more than the document's stated figure — an arithmetic error in the source. It does not trigger when `stated_total > calculated_total` (which is normal when tax or shipping is added on top).
- `api_call_count`: total number of Anthropic API calls made during this extraction. `1` means no retry occurred; `2` means one retry.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model for extraction calls |
| `ANTHROPIC_API_KEY` | (required) | API key |
| `EXTRACT_FORCE_INVALID` | (unset) | When set to `1`, the validator treats the first extraction response as failed regardless of its content, injecting the error string `"forced_invalid: validation overridden by EXTRACT_FORCE_INVALID"`. Use this to exercise the retry path without needing a real error. |
| `EXTRACT_LOG_PATH` | (unset) | When set to a file path, write a JSON array to that path recording each extraction attempt: `[{"attempt": 1, "messages": [...], "extracted": {...}}, {"attempt": 2, "messages": [...], "extracted": {...}}]`. The `messages` field is the full list of messages passed to the API for that attempt. |

Read both env vars at call time inside `extract_invoice`, not at module import time — the checker sets and resets them between calls.

## Fixtures

**`fixtures/invoices/invoice_001.txt` — `invoice_010.txt`:** 10 plain-text invoices with varied formats and deliberate quality issues. Highlights:
- `invoice_002`: no invoice number, no date; fuzzy quantity ("about two dozen items in bulk").
- `invoice_003`: line items sum to $13,000; stated total is $12,800 — the line sum exceeds the stated total, a real arithmetic conflict.
- `invoice_004`: customer field explicitly marked "[Customer name not filled in]" — the required information is genuinely absent and cannot be inferred. This is the unretryable case.
- `invoice_009`, `invoice_010`: multiple absent fields; informal language.

**`fixtures/invoices/invoices_truth.json`:** ground truth for all 10 invoices. **Checker-only — do not import or read this file from your pipeline.** It is not present in your workspace.

## Acceptance criteria

All four checks are deterministic. All must pass.

**C1-null-not-fabricated.** The checker runs `extract_invoice` on invoices with absent fields and compares results against `invoices_truth.json`. Specifically: `invoice_002` must return `invoice_number: null` and `date: null`; `invoice_010` must return `invoice_number: null`, `date: null`, and `customer: null`. A non-null value for any of these absent fields is a failure — this indicates fabrication.

**C2-conflict-detected.** The checker runs `extract_invoice` on `invoice_003`. The result must have `conflict_detected: true`. The `calculated_total` must be greater than `stated_total` (reflecting that line items sum to more than the stated figure). Both `stated_total` and `calculated_total` must be present and non-null.

**C3-validation-retry.** The checker sets `EXTRACT_FORCE_INVALID=1` and `EXTRACT_LOG_PATH` to a temporary file path, then calls `extract_invoice` on `invoice_001` (a clean, fully extractable document). Three assertions: (a) the returned dict has `api_call_count == 2`; (b) the log file at `EXTRACT_LOG_PATH` contains two attempt entries; (c) the second attempt's `messages` list includes the original document text, the `extracted` dict from attempt 1 serialised as JSON, and the injected error string `"forced_invalid: validation overridden by EXTRACT_FORCE_INVALID"`. All three must hold.

**C4-no-retry-on-absence.** The checker ensures `EXTRACT_FORCE_INVALID` is not set, then calls `extract_invoice` on `invoice_004`. The result must have `api_call_count == 1`. The `customer` field must be `null`. A second API call on this document indicates incorrect retry logic — the information is declared absent in the document text and retrying is wrong.

## What `bootcamp check` does

- Imports `extract.py` from your workspace directory (inserts workspace into `sys.path`) and calls `extract_invoice` directly.
- For C3: sets `os.environ["EXTRACT_FORCE_INVALID"] = "1"` and `os.environ["EXTRACT_LOG_PATH"] = <tempfile>` before calling `extract_invoice`, then unsets both. Your function must read these at call time.
- For C4: explicitly ensures both env vars are unset before calling.
- Parses the `EXTRACT_LOG_PATH` output as JSON and inspects attempt entries.
- Compares extracted fields against `invoices_truth.json` (which is in the fixtures directory, not your workspace).
- Does not evaluate prose quality or description text — only the specified fields.
