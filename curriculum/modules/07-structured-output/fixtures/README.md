# M7 Fixtures Documentation

## Messy Invoices

A collection of 10 plain-text invoice documents demonstrating real-world data extraction challenges with deliberately varied formats and quality issues.

### Files

```
invoices/
├── invoice_001.txt through invoice_010.txt     (10 documents)
└── invoices_truth.json                          (ground truth)
```

## Document Issues

Each invoice is intentionally messy to test extraction robustness:

### Informal Measurements
- **invoice_002:** "about two dozen items in bulk" (fuzzy quantity)
- **invoice_007:** "about 50 panels installed" (approximate, not exact)
- **invoice_009:** "roughly 3,000 copies" (informal measurement)

### Absent Required Fields

- **invoice_002:** No invoice number, no date
- **invoice_006:** No invoice number
- **invoice_007:** No invoice number
- **invoice_009:** Missing invoice number, date, customer name, address
- **invoice_010:** Missing invoice number, date, customer name

### Line Items ≠ Stated Total

- **invoice_003:** Line items sum to $13,000 but stated total is $12,800
  - Consulting: $6,000
  - Implementation: $6,000
  - Support: $1,000
  - **Expected line total: $13,000 + $1,300 tax = $14,300**
  - **Stated total: $12,800** (incorrect)

### Missing Required Field (Unretryable)

- **invoice_004:** Missing customer name entirely (marked as "[Customer name not filled in]")
  - This is an unretryable case — the data cannot be inferred

### Varied Layouts

- **invoice_001:** Standard structured format
- **invoice_002:** Markdown-style formatting
- **invoice_003:** Dense text layout
- **invoice_004:** Standard with explicit missing field note
- **invoice_005:** Decorative ASCII borders
- **invoice_006:** Simple key-value pairs
- **invoice_007:** Minimal structure
- **invoice_008:** Formatted with visual separators
- **invoice_009:** Draft status, very minimal
- **invoice_010:** STATEMENT format with informal wording

### Data Characteristics

- **Statuses:** Mix of complete, draft, and incomplete documents
- **Currencies:** All in USD (implied)
- **Customers:** Mix of companies and individuals
- **Service types:** Consultancy, manufacturing, retail, software, maintenance

## invoices_truth.json

Ground truth for all 10 invoices with:

```json
[
  {
    "invoice_id": "invoice_001",
    "invoice_number": "INV-2024-001",
    "customer_name": "John Smith",
    "vendor_name": "Acme Corp",
    "invoice_date": "2024-03-15",
    "total_amount": 113.40,
    "tax_amount": 8.40,
    "line_items": [...],
    "issues": []
  },
  ...
]
```

### Schema Details

- **invoice_id** — File identifier (invoice_001 to invoice_010)
- **invoice_number** — Number field (null if absent)
- **customer_name** — Billed-to name (null if absent)
- **vendor_name** — Billing entity
- **invoice_date** — YYYY-MM-DD format (null if missing)
- **total_amount** — Final total due (null if conflicting)
- **tax_amount** — Tax portion
- **line_items** — Array of:
  ```json
  {
    "description": "Item name",
    "quantity": number,
    "unit_price": number | null,
    "total": number
  }
  ```
- **issues** — Array of issue tags:
  - `missing_invoice_number`
  - `missing_date`
  - `missing_customer_name`
  - `informal_quantity_measurement`
  - `line_items_sum_mismatch`
  - `stated_total_conflicts_with_calculation`
  - `unretryable_absence`
  - `draft_status`

## Testing Notes

- Documents are plain text with no binary content
- All amounts are in USD (no currency conversion needed)
- Date formats: YYYY-MM-DD (parsed) or informal ("March 15, 2024")
- Numbers: Mix of integers, decimals, and written-out ("about two dozen")
- Required fields for a complete invoice:
  1. Invoice number
  2. Customer name
  3. Date
  4. Total amount
  5. Line items (with calculated subtotal)

- **Unretryable case:** invoice_004 — missing customer name is not inferable from context
- **Retryable cases:** All other documents can be extracted with appropriate parsing

## Example Extraction Challenge

**invoice_003** tests conflict detection:
- Line items clearly sum to $13,000 + $1,300 = $14,300
- Stated total is $12,800
- Extraction should detect this conflict and flag it
- Ground truth marks this as `line_items_sum_mismatch` and `stated_total_conflicts_with_calculation`
