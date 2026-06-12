# M9 Fixtures Documentation

## support_backend.py and support_data.py

The mock backend is split across two files to stay within the 300-line limit:

- **support_data.py** — seeded `_CUSTOMERS` and `_ORDERS` data literals only.
  Do not import this directly from checks; import `support_backend` instead.
- **support_backend.py** — public API (`get_customer`, `find_customers`,
  `lookup_order`, `process_refund`, `escalate_to_human`) plus module-level
  `REFUND_LOG`, `ESCALATION_LOG`, and `RefundError`. Imports data from
  `support_data`.

When clearing module cache in checks, pop **both** names:
```python
sys.modules.pop("support_backend", None)
sys.modules.pop("support_data", None)
```

## support_backend.py

Mock support backend providing in-process customer service functions. Deterministic, seeded data with no external dependencies (stdlib only).

### Functions

#### `get_customer(customer_id: str) -> dict[str, Any]`
Fetches a single customer by ID. Returns a copy of the customer record or raises `KeyError`.

**Customer record schema:**
```python
{
    "id": str,              # e.g., "C001"
    "name": str,
    "email": str,
    "phone": str,
    "account_created": int | str,  # Mixed: Unix timestamp or ISO-8601
    "tier": str,            # e.g., "gold", "silver", "bronze"
    "total_spend": float
}
```

#### `find_customers(name: str) -> list[dict[str, Any]]`
Finds customers by name (partial match, case-insensitive). Returns list of matching records (may be empty).
**Important:** Two customers named "Alex Rivera" exist with ids C009 and C010.

#### `lookup_order(order_id: str) -> dict[str, Any]`
Fetches a single order by ID or raises `KeyError`.

**Order record schema:**
```python
{
    "id": str,              # e.g., "O001"
    "customer_id": str,
    "order_date": int | str,        # Mixed: Unix timestamp or ISO-8601
    "ship_date": int | str,
    "delivery_date": int | str,
    "status": str,          # Mixed case: "SHIPPED", "shipped", "Shipped", etc.
    "subtotal": float,
    "tax": float,
    "shipping": float,
    "total": float,
    "currency": str,        # Always "USD"
    "items": [              # Line items (40+ fields total with nested data)
        {
            "sku": str,
            "name": str,
            "quantity": int | float,
            "unit_price": float,
            "subtotal": float
        }
    ],
    "shipping_address": str,
    "tracking_number": str | None,
    "payment_method": str,
    "order_notes": str,
    "internal_flags": list[str],
    "status": str,
    ... # Additional fields like return_date, return_reason, cancellation_date, etc.
}
```

#### `process_refund(order_id: str, amount: float) -> dict[str, Any]`
Processes a refund for an order. Records to module-level `REFUND_LOG` list.

**Raises:** `RefundError` if `amount > 1000.0` (backend hard cap).

**Return schema:**
```python
{
    "refund_id": str,       # e.g., "REF-1001"
    "order_id": str,
    "amount": float,
    "status": str,          # Always "processed"
    "expected_delivery": str
}
```

#### `escalate_to_human(case_summary: str) -> dict[str, Any]`
Escalates a case to human support. Records to module-level `ESCALATION_LOG` list.

**Return schema:**
```python
{
    "case_id": str,         # e.g., "ESC-5001"
    "status": str,          # Always "queued"
    "queue_position": int,
    "estimated_wait": str,
    "message": str
}
```

### Module-level State

- **REFUND_LOG**: `list[dict]` recording all refund calls. Inspectable by checkers.
- **ESCALATION_LOG**: `list[dict]` recording all escalations. Inspectable by checkers.
- **RefundError**: Exception raised by `process_refund()` for amounts > $1000.

### Data Characteristics

- **Customers:** 10 total (8 unique names + "Alex Rivera" × 2)
- **Orders:** 12 total
- **Timestamps:** Deliberately mixed Unix-epoch ints (e.g., 1704955800) and ISO-8601 strings (e.g., "2024-01-10T09:15:00Z")
- **Statuses:** Mixed case ("DELIVERED", "shipped", "Shipped", "IN_TRANSIT", "pending", etc.)
- **Special amounts:**
  - One order (O004) totals exactly $768.99 (triggers adversarial tests)
  - One order (O002) subtotal exactly $123.45 (used in recall tests)

## conversations.json

Scripted multi-turn conversation drivers for testing agentic behavior.

### Script Structure

```json
{
  "scripts": [
    {
      "id": "script-id",
      "description": "Human-readable description",
      "turns": [
        {
          "turn": 1,
          "user_message": "User input text",
          "expected_outcome": "What the agent should do"
        }
      ]
    }
  ]
}
```

### Available Scripts

**m1-multi-concern:** Single turn combining two concerns (refund status lookup + address change). Tests multi-domain tool selection in a single turn.

---

## Testing Notes

- All functions are importable and runnable with no external dependencies.
- Seeding ensures deterministic behavior across runs.
- Customer lookup edge case: finding "Alex Rivera" returns both C009 and C010 (identity disambiguation test).
- Order O004 ($700) designed for adversarial policy tests (exceeds typical $500 refund caps).
