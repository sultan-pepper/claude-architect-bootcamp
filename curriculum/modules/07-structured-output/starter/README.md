# M07 workspace — Structured output & extraction

## Deliverables

One file: `extract.py`. The checks import it and call `extract_invoice` directly.

## Entry point

```python
def extract_invoice(text: str) -> dict:
    ...
```

Returns the extraction schema dict defined in `lab.md`. When run as `__main__`, reads a file path from `sys.argv[1]` and prints the result as JSON to stdout.

## Contract summary

| Field | Type | Notes |
|---|---|---|
| `invoice_number` | `string \| null` | null when absent — do not fabricate |
| `date` | `string \| null` | YYYY-MM-DD; null when absent |
| `customer` | `string \| null` | null when absent |
| `line_items` | array | see schema in lab.md |
| `stated_total` | `number \| null` | total as written in document |
| `calculated_total` | `number` | sum of line item subtotals |
| `conflict_detected` | `boolean` | true when calculated > stated + $0.01 |
| `api_call_count` | `integer` | 1 = no retry; 2 = one retry |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model for all API calls |
| `ANTHROPIC_API_KEY` | (required) | API key |
| `EXTRACT_FORCE_INVALID` | (unset) | Set to `1` to force the first validation to fail (tests retry path) |
| `EXTRACT_LOG_PATH` | (unset) | File path; when set, write per-attempt log as JSON array |

## Running manually

```bash
python extract.py ../fixtures/invoices/invoice_001.txt
python extract.py ../fixtures/invoices/invoice_003.txt   # should show conflict_detected: true
python extract.py ../fixtures/invoices/invoice_004.txt   # should show api_call_count: 1
EXTRACT_FORCE_INVALID=1 EXTRACT_LOG_PATH=/tmp/log.json python extract.py ../fixtures/invoices/invoice_001.txt
```

## Checks

```bash
bootcamp check   # runs all four criteria
bootcamp hint    # unlock hints one level at a time (requires a failed check run first)
```
