"""M07 — Structured output & extraction: invoice extraction pipeline skeleton.

Implement extract_invoice() according to the contract in README.md and lab.md.
Fill every TODO. Do not change the function signature or return shape.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "claude-haiku-4-5"

# ---------------------------------------------------------------------------
# Extraction tool schema
# TODO: Define the input_schema for the extraction tool.
#       All output fields must be present in the schema.
#       Nullable fields (invoice_number, date, customer, unit_price, subtotal,
#       stated_total) must use {"type": ["<type>", "null"]} — non-null types
#       create fabrication pressure when the value is absent.
# ---------------------------------------------------------------------------
EXTRACTION_TOOL: dict[str, Any] = {
    "name": "extract_invoice_fields",
    "description": (
        # TODO: Write a description that tells the model what this tool does
        # and what kind of document it is processing.
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            # TODO: invoice_number — nullable string
            # TODO: date — nullable string, YYYY-MM-DD
            # TODO: customer — nullable string
            # TODO: line_items — array of objects with:
            #         description (string), quantity (number), unit (string),
            #         unit_price (nullable number), subtotal (nullable number)
            # TODO: stated_total — nullable number
        },
        "required": [
            # TODO: list all property names here
        ],
    },
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(result: dict[str, Any], doc: str, attempt: int) -> str | None:
    """Return an error string if result fails validation, or None if it passes.

    TODO:
    - When os.environ.get("EXTRACT_FORCE_INVALID") == "1" and attempt == 1:
      return the exact string
      "forced_invalid: validation overridden by EXTRACT_FORCE_INVALID"
      This simulates a validation failure so the retry path can be tested.
    - Otherwise: check semantic correctness. At minimum, verify that
      conflict_detected is set correctly based on calculated_total vs stated_total.
    - Return None if the result is valid.
    """
    # TODO: implement validation
    return None


def is_unretryable_null(result: dict[str, Any], doc: str) -> bool:
    """Return True if a null required field is genuinely absent from the document.

    When True, the caller must NOT retry — the missing data cannot be recovered
    by sending the same document again.

    TODO:
    - Check if any required field (e.g., customer) is null.
    - If null: scan doc for text that could plausibly be that field's value.
    - If no plausible candidate exists (e.g., the document says the field is
      "not filled in"), return True.
    - If a plausible candidate exists, the model may have missed it — return False
      so the caller retries with a correction hint.
    """
    # TODO: implement absence classification
    return False


# ---------------------------------------------------------------------------
# Extraction pipeline
# ---------------------------------------------------------------------------
def extract_invoice(text: str) -> dict[str, Any]:
    """Extract structured fields from a plain-text invoice.

    Args:
        text: Full text of the invoice document.

    Returns:
        Dict matching the schema defined in lab.md. Always contains all keys.
        api_call_count reflects the number of API calls made.

    TODO:
    - Read ANTHROPIC_MODEL and EXTRACT_LOG_PATH from os.environ at call time.
    - Build the initial messages list with a user turn containing the document.
    - Run a retry loop (max 2 attempts):
        1. Call the API with tool_choice forced to "extract_invoice_fields".
        2. Extract result from response.content[0].input.
        3. Increment api_call_count.
        4. Call validate(result, text, attempt).
        5. If validation fails and is_unretryable_null is False and attempts remain:
             append the assistant turn and a user turn containing the original doc,
             the failed output as JSON, and the specific error string, then continue.
           Otherwise: break.
    - After the loop:
        - Compute calculated_total from line_items subtotals.
        - Set conflict_detected based on calculated_total vs stated_total.
        - Add api_call_count to the result dict.
    - If EXTRACT_LOG_PATH is set: write (or overwrite) the log file as a JSON
      array where each element is {"attempt": N, "messages": [...], "extracted": {...}}.
      The messages list is the full messages list passed to the API for that attempt.
    - Return the result dict.
    """
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()
    log_path = os.environ.get("EXTRACT_LOG_PATH")

    api_call_count = 0
    log_entries: list[dict[str, Any]] = []

    # TODO: build initial messages list
    messages: list[dict[str, Any]] = []

    result: dict[str, Any] = {}

    # TODO: implement the retry loop

    # TODO: compute calculated_total and conflict_detected

    result["api_call_count"] = api_call_count

    # TODO: write log file if EXTRACT_LOG_PATH is set

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract.py <invoice-file>", file=sys.stderr)
        sys.exit(2)
    invoice_path = sys.argv[1]
    with open(invoice_path, encoding="utf-8") as fh:
        invoice_text = fh.read()
    output = extract_invoice(invoice_text)
    print(json.dumps(output, indent=2))
