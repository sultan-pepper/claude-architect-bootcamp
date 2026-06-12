# Lesson 07 — Structured output & extraction

Two ways to get structured data from the API: ask for JSON in prose and parse the response, or declare a tool schema and force the model to call it. The prose approach works until it doesn't — markdown fences appear, numeric precision drifts, field names vary. Tool use eliminates syntax errors by construction. This lesson covers the full extraction pattern: schema design, tool_choice modes, nullable fields, validation with retry, when not to retry, and semantic consistency checks.

## tool_use_for_syntax

When you ask the model to "respond with a JSON object," you get JSON most of the time. When you declare a tool and force the model to call it, you get a Python dict every time. The difference is that `tool_use_block.input` is already parsed and schema-validated by the API. There is no string to parse, no fence to strip, no guessing whether the model added a preamble.

Minimum pattern for forced extraction:

```python
TOOL = {
    "name": "extract_fields",
    "description": "Extract structured invoice fields from the provided document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": ["string", "null"]},
            "stated_total":   {"type": ["number", "null"]},
        },
        "required": ["invoice_number", "stated_total"],
    },
}

response = client.messages.create(
    model=model,
    tools=[TOOL],
    tool_choice={"type": "tool", "name": "extract_fields"},
    messages=[{"role": "user", "content": f"Extract:\n\n{document_text}"}],
)
extracted: dict = response.content[0].input   # already a dict — no json.loads needed
```

With `type: "tool"`, the response always has exactly one `ToolUseBlock` as `content[0]`. The API rejects the call if the model cannot produce a conforming response.

## tool_choice

Three modes:

- `{"type": "auto"}` — model decides whether to call a tool. Correct in agentic routing. Wrong for extraction — the model may answer in text and skip the tool.
- `{"type": "any"}` — model must call one of the declared tools but picks which. Useful when you have multiple schemas and want the model to select the right format.
- `{"type": "tool", "name": "..."}` — model must call this specific tool. Correct for single-schema extraction. No optionality.

Use `type: "tool"` any time you have exactly one output schema. Save `auto` for routing and `any` for schema-selection.

## nullable_vs_fabrication

A JSON Schema field declared as `"type": "string"` (non-null, required) creates pressure to fill it. If the source document does not contain that information, the model invents a plausible-looking value: a made-up invoice number that follows the right format, a date that falls within a plausible range, a customer name borrowed from another field. This is fabrication — syntactically valid, semantically wrong, and silent.

The fix: declare any field that may be absent as nullable. JSON Schema syntax:

```json
"invoice_number": {"type": ["string", "null"]}
```

The field is still `required` in the schema (it must appear in every response). Its value is `null` when absent, not a fabricated string. You then handle nulls explicitly in downstream code rather than discovering fabricated values at audit time.

Non-nullable required fields signal to the model that the information must exist. Use them only when the document type guarantees the field is always present.

## enum_and_other

Enums constrain a field to a fixed set of values. When a real value falls outside that set, the model picks the closest member — fabrication of a different kind. The escape hatch:

```json
"payment_method": {"enum": ["CREDIT_CARD", "WIRE", "CHECK", "OTHER"]},
"payment_method_detail": {"type": ["string", "null"]}
```

When the document shows an out-of-set value, the model returns `"OTHER"` and puts the raw value in `payment_method_detail`. The sentinel is machine-readable; the detail is human-readable. Apply to any categorical field where real-world values can fall outside your known set.

## few_shot

The schema defines what fields to extract. It does not teach the model how to handle format variation: a quantity written as "about two dozen," a date as "15th of March," a total buried in a narrative paragraph. Few-shot examples in the conversation history show the model the mapping from messy input to clean output.

Include 1–2 user/assistant turn pairs before the actual extraction request. The assistant turn in each pair is a `tool_use` block with the correct extracted output. Show the messiest format variants you expect, not the clean case. Include at least one example where a field is absent and the correct output has `null`. Do not show only clean input — that trains for the easy case and leaves edge cases unhandled.

## validation_retry

Tool schemas enforce syntax. They do not enforce semantic correctness: a date field can be syntactically valid (`"2024-03-15"`) and factually wrong (the date does not appear anywhere in the document). Semantic validation runs after extraction.

When validation fails, the retry must include three things:

1. **The original document** — the model cannot correct what it cannot see.
2. **The failed extracted output** — the model needs to know what it produced.
3. **The specific error** — "calculated subtotals exceed stated total by $200" is actionable; "try again" produces the same wrong output.

Skeleton:

```python
messages = [{"role": "user", "content": f"Extract:\n\n{doc}"}]
for attempt in range(1, max_attempts + 1):
    response = client.messages.create(model=model, tools=[TOOL],
                                      tool_choice={"type": "tool", "name": "extract_fields"},
                                      messages=messages)
    result = response.content[0].input
    error = validate(result, doc)
    if error is None:
        break
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content":
        f"Validation failed: {error}\n\nOriginal document:\n{doc}\n\n"
        f"Your previous extraction:\n{json.dumps(result)}\n\nCorrect and extract again."})
```

One retry is sufficient for correctable errors; two at most before classifying the document as unprocessable.

## unretryable_absence

Retrying when a required field is genuinely absent from the document wastes API calls and increases fabrication probability — each retry applies pressure to fill the field, and the model may invent a plausible value on the second attempt where it correctly returned `null` on the first.

Before retrying on a null required field, classify the null:

- **Extractable but missed**: the information exists in the document but the model failed to parse it (unusual prefix, buried paragraph). Retry with a format hint.
- **Genuinely absent**: the document explicitly states the field is missing or inapplicable. The correct result is `null`. Do not retry.

The validator makes this classification. Check whether the document text contains any string that could plausibly be the missing field's value. If nothing plausible exists, record `null` and move on.

## semantic_validation

Two categories of post-extraction check:

**Syntax validation**: type correctness, format compliance (e.g., date matches `YYYY-MM-DD`), enum membership. Handle via schema where possible; supplement the validator for constraints JSON Schema cannot express (date range, non-negative amounts).

**Semantic validation**: computed consistency checks. For invoices, the critical check is whether line item arithmetic agrees with the stated total:

```python
calculated = sum(item["subtotal"] for item in result["line_items"]
                 if item["subtotal"] is not None)
stated = result["stated_total"]
if stated is not None and calculated > stated + 0.01:
    result["conflict_detected"] = True
```

This catches the case where line items sum to *more* than the stated total — an arithmetic error in the source document. It does not falsely trigger when `stated_total > calculated` (which is expected whenever tax or shipping is added on top of line item subtotals).

When a conflict is detected, both values are factual: `stated_total` is what the document says; `calculated_total` is what the arithmetic produces. Return both. Setting `conflict_detected = True` is not a validation failure requiring retry — it is accurate reporting of a source data quality problem. Downstream consumers decide what to do with it.
