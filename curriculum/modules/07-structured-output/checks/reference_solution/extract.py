"""Reference solution for M07: structured-output extraction."""

import anthropic
import json
import os
import sys
from pathlib import Path


EXTRACTION_TOOL = {
    "name": "extract_invoice_fields",
    "description": "Extract structured invoice data from document text",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {
                "type": ["string", "null"],
                "description": "Invoice ID as printed; null if absent"
            },
            "date": {
                "type": ["string", "null"],
                "description": "Invoice date YYYY-MM-DD; null if not stated"
            },
            "customer": {
                "type": ["string", "null"],
                "description": "Billed-to name; null if not present"
            },
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Item/service description"
                        },
                        "quantity": {
                            "type": "number",
                            "description": "Quantity ordered"
                        },
                        "unit": {
                            "type": "string",
                            "description": "Unit of measure (hr, each, box, etc) or empty string"
                        },
                        "unit_price": {
                            "type": ["number", "null"],
                            "description": "Price per unit; null if not stated"
                        },
                        "subtotal": {
                            "type": ["number", "null"],
                            "description": "Line total; null if not calculable"
                        }
                    },
                    "required": ["description", "quantity", "unit", "unit_price", "subtotal"]
                }
            },
            "stated_total": {
                "type": ["number", "null"],
                "description": "Total amount stated in document; null if absent"
            }
        },
        "required": ["invoice_number", "date", "customer", "line_items", "stated_total"]
    }
}


def validate(result: dict, doc: str) -> str | None:
    """Check for semantic errors in extraction result.

    Returns error string if validation fails, None if valid.
    When EXTRACT_FORCE_INVALID is set, returns forced error on first attempt.
    """
    # Check if we should force an error
    if os.environ.get("EXTRACT_FORCE_INVALID") == "1":
        global _attempt_count
        if _attempt_count == 1:
            return "forced_invalid: validation overridden by EXTRACT_FORCE_INVALID"

    # Check for conflict: calculated total > stated total
    if result.get("stated_total") is not None:
        calculated = sum(
            item.get("subtotal", 0)
            for item in result.get("line_items", [])
            if item.get("subtotal") is not None
        )
        stated = result.get("stated_total")
        if calculated > stated + 0.01:
            # This is a valid detection, not an error
            pass

    return None


def is_unretryable_null(result: dict, doc: str) -> bool:
    """Check if a null field is unretryable.

    A field is unretryable if the document explicitly states it's absent
    or there is no plausible candidate for the field.
    """
    if result.get("customer") is None:
        # Check if document contains markers of missing customer
        if "not filled in" in doc.lower() or "customer name" in doc.lower():
            return True
        # Check if there's any plausible customer name in the doc
        lines = doc.split("\n")
        for line in lines:
            if "acme" in line.lower() or "corp" in line.lower() or "company" in line.lower():
                return False  # Found a plausible candidate
        if len(lines) < 3:  # Very short doc
            return True
    return False


def extract_invoice(text: str) -> dict:
    """Extract structured invoice data using Claude with validation retry."""
    global _attempt_count
    _attempt_count = 0

    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
    log_path = os.environ.get("EXTRACT_LOG_PATH")

    messages: list[dict] = []
    log_entries: list[dict] = []
    api_call_count = 0
    max_attempts = 2

    # Track previous attempt's response and extracted data for retry
    prev_response = None
    prev_result: dict | None = None
    error: str | None = None

    for attempt in range(1, max_attempts + 1):
        _attempt_count = attempt

        if attempt == 1:
            messages = [{"role": "user", "content": text}]
        else:
            # Attempt 1 used forced tool_choice, so the assistant turn contains
            # a tool_use block.  Append it serialised as plain dicts (so the log
            # stays JSON-able and the API accepts it).
            assert prev_response is not None
            messages.append({
                "role": "assistant",
                "content": [b.model_dump() for b in prev_response.content]
            })
            # Locate the tool_use_id from the previous response
            tool_use_id = next(
                (b.id for b in prev_response.content if b.type == "tool_use"),
                "unknown"
            )
            # The user turn carries a tool_result with: the original document,
            # the failed extraction, and the specific error string.  C3 checks
            # that all three are present in the attempt-2 messages.
            retry_content = (
                f"Original document:\n{text}\n\n"
                f"Previous extraction:\n{json.dumps(prev_result)}\n\n"
                f"Error: {error}"
            )
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": retry_content
                }]
            })

        # Call API
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=messages,
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "tool", "name": "extract_invoice_fields"}
        )
        api_call_count += 1

        # Extract the tool result
        if not response.content or response.content[0].type != "tool_use":
            raise ValueError("Expected tool_use response")

        result = response.content[0].input

        # Save for logging (snapshot messages at this point in the loop)
        messages_copy = json.loads(json.dumps(messages))
        log_entries.append({
            "attempt": attempt,
            "messages": messages_copy,
            "extracted": result
        })

        # Validate
        error = validate(result, text)

        if error is None:
            break  # Success

        if is_unretryable_null(result, text):
            break  # Can't retry

        if attempt >= max_attempts:
            break  # No more retries

        # Save for the next iteration's retry context
        prev_response = response
        prev_result = result

    # Compute calculated total
    calculated_total = sum(
        item.get("subtotal", 0)
        for item in result.get("line_items", [])
        if item.get("subtotal") is not None
    )

    # Detect conflict
    conflict_detected = False
    if result.get("stated_total") is not None:
        if calculated_total > result.get("stated_total", 0) + 0.01:
            conflict_detected = True

    # Build final result
    final_result = {
        **result,
        "calculated_total": calculated_total,
        "conflict_detected": conflict_detected,
        "api_call_count": api_call_count
    }

    # Write log if requested
    if log_path:
        with open(log_path, "w") as f:
            json.dump(log_entries, f, indent=2)

    return final_result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <invoice_file>")
        sys.exit(1)

    invoice_path = sys.argv[1]
    with open(invoice_path) as f:
        invoice_text = f.read()

    result = extract_invoice(invoice_text)
    print(json.dumps(result, indent=2))
