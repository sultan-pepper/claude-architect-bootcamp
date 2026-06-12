# Rubric — 07 structured-output

## Criteria

1. **C1-null-not-fabricated** (deterministic): `extract_invoice` returns `null` for absent fields on `invoice_002` (invoice_number, date) and `invoice_010` (invoice_number, date, customer) — no invented strings — lesson_ref: lesson.md §nullable_vs_fabrication
2. **C2-conflict-detected** (deterministic): `extract_invoice` on `invoice_003` returns `conflict_detected: true` with `calculated_total` greater than `stated_total` — lesson_ref: lesson.md §semantic_validation
3. **C3-validation-retry** (deterministic): with `EXTRACT_FORCE_INVALID=1` set, `extract_invoice` makes exactly 2 API calls (`api_call_count == 2`), the log at `EXTRACT_LOG_PATH` contains 2 attempts, and attempt 2's `messages` contains the original doc text, the attempt-1 extracted output as JSON, and the injected error string — lesson_ref: lesson.md §validation_retry
4. **C4-no-retry-on-absence** (deterministic): `extract_invoice` on `invoice_004` with `EXTRACT_FORCE_INVALID` unset returns `api_call_count == 1` and `customer: null` — no retry issued for a genuinely absent field — lesson_ref: lesson.md §unretryable_absence

## Hints

### Level 1
The check is failing because of how fields with no value in the document are handled. Look at what happens in your tool schema when the model cannot find a piece of information — is it forced to produce something, or is absence a valid output?

### Level 2
In a JSON Schema, `"type": "string"` means the model must supply a string. `"type": ["string", "null"]` means the model can supply `null` when the value is absent. The model produces what the schema allows. If the schema demands a string, the model invents one. Check all fields that should be nullable in your `input_schema`.

### Level 3
Schema shape for nullable extraction fields:
```python
"invoice_number": {"type": ["string", "null"], "description": "Invoice ID as printed; null if absent"},
"date":           {"type": ["string", "null"], "description": "Invoice date YYYY-MM-DD; null if not stated"},
"customer":       {"type": ["string", "null"], "description": "Billed-to name; null if not present"},
```
For conflict detection, compute `calculated_total = sum(item["subtotal"] for item in line_items if item["subtotal"])` and compare against `stated_total`. Set `conflict_detected = calculated_total > stated_total + 0.01`. For the retry path: build a new user message containing `f"Original document:\n{doc}\n\nPrevious extraction:\n{json.dumps(result)}\n\nError: {error}"` and append it after the failed assistant turn before the second API call. For `invoice_004`, check whether the document text contains any plausible candidate for the customer name before deciding to retry — if the document says the field is missing, skip the retry and return `null`.

## Mentor guardrails

- Do not show the learner a complete `validate` function or write their retry loop.
- If the learner asks why fabrication is happening, ask them to look at the `type` declaration for the failing field in their `input_schema` and describe what values that type permits.
- If the learner asks how to detect unretryable absence, ask: "Does the document contain any text that could plausibly be the customer's name? If not, what does that tell you about whether a retry would help?"
- If the learner asks about the `conflict_detected` logic, ask them to state what condition makes a stated total inconsistent with line item arithmetic — prompt them to distinguish "total includes tax" (not a conflict) from "line items sum exceeds stated total" (a conflict).
- API-shape examples (schema snippets, type declarations) are permitted at ≤5 lines, provided they are not specific to the invoice schema solution.
- Do not reveal which specific invoice files the checker uses for C1 null checks beyond what lab.md states.

## Reference solution sketch

**`extract.py` structure:**

**Imports:** `anthropic`, `json`, `os`, `sys`, `pathlib`.

**`EXTRACTION_TOOL` dict:** tool name `"extract_invoice_fields"`, description names the document type, `input_schema` declares all output fields. Nullable fields use `"type": ["string", "null"]` or `"type": ["number", "null"]`. `line_items` is an array of objects with `description` (string), `quantity` (number), `unit` (string), `unit_price` (nullable number), `subtotal` (nullable number). All top-level fields in `required`.

**`validate(result: dict, doc: str) -> str | None`:** checks `conflict_detected` arithmetic (returns an error string if wrong); other semantic checks. When `EXTRACT_FORCE_INVALID == "1"` (read from `os.environ`) AND `_attempt == 1`, returns the injected error string `"forced_invalid: validation overridden by EXTRACT_FORCE_INVALID"` unconditionally.

**`is_unretryable_null(result: dict, doc: str) -> bool`:** returns `True` when the `customer` field (or other required field) is `null` and a scan of `doc` finds no plausible candidate text (e.g., the document contains the phrase "not filled in" or similar markers for the relevant field).

**`extract_invoice(text: str) -> dict`:** reads `EXTRACT_LOG_PATH` and `EXTRACT_FORCE_INVALID` from `os.environ`. Builds initial `messages` list. Runs a loop (max 2 iterations): calls API with `tool_choice={"type": "tool", "name": "extract_invoice_fields"}`, extracts `.content[0].input`, increments `api_call_count`. Calls `validate(result, text)`. If `error` is not None and `is_unretryable_null(result, text)` is False and `attempt < max_attempts`: appends assistant turn and a user message containing the original doc, previous extraction as JSON, and the error string; continues loop. Else: breaks. Computes `calculated_total` from `line_items`. Sets `conflict_detected`. If `EXTRACT_LOG_PATH` is set, appends `{"attempt": N, "messages": messages_copy, "extracted": result}` to the log file as a JSON array. Returns final result dict with `api_call_count`.

**`__main__` block:** reads filename from `sys.argv[1]`, reads file text, calls `extract_invoice`, prints `json.dumps(result, indent=2)`.

Total: approximately 100–140 lines.
