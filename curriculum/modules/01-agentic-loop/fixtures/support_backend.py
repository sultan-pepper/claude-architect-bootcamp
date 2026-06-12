"""Mock support backend for customer service agentic loop exercises.

Deterministic, seeded data. Stdlib only (no anthropic imports).
Functions: get_customer, find_customers, lookup_order, process_refund, escalate_to_human.

Seeded data lives in support_data.py (customers + orders).

Customers: ≥8 customers including two named "Alex Rivera" (different ids).
Orders: ≥12 orders with 40+ fields each. Timestamps mixed Unix-epoch ints
and ISO-8601 strings. Statuses mixed case ("SHIPPED", "shipped", "Shipped").
One order priced exactly $700.00, one priced $123.45.

process_refund records calls to module-level REFUND_LOG and raises RefundError
for > $1000. escalate_to_human appends to module-level ESCALATION_LOG.
"""

import random
from dataclasses import dataclass
from typing import Any

from support_data import _CUSTOMERS, _ORDERS

# Seeded randomness for determinism
random.seed(42)

# Module-level logs for backend state inspection
REFUND_LOG: list[dict[str, Any]] = []
ESCALATION_LOG: list[dict[str, Any]] = []


@dataclass
class RefundError(Exception):
    """Raised when refund exceeds backend cap ($1000)."""

    message: str


def get_customer(customer_id: str) -> dict[str, Any]:
    """Fetch a single customer by ID.

    Returns:
        Customer record as dict, or raises KeyError if not found.
    """
    for cust in _CUSTOMERS:
        if cust["id"] == customer_id:
            return dict(cust)
    raise KeyError(f"Customer not found: {customer_id}")


def find_customers(name: str) -> list[dict[str, Any]]:
    """Find customers by name (partial match, case-insensitive).

    Returns:
        List of matching customer records (may be empty or multiple results).
    """
    results = []
    name_lower = name.lower()
    for cust in _CUSTOMERS:
        if name_lower in cust["name"].lower():
            results.append(dict(cust))
    return results


def lookup_order(order_id: str) -> dict[str, Any]:
    """Fetch a single order by ID.

    Returns:
        Order record as dict, or raises KeyError if not found.
    """
    for order in _ORDERS:
        if order["id"] == order_id:
            return dict(order)
    raise KeyError(f"Order not found: {order_id}")


def process_refund(order_id: str, amount: float) -> dict[str, Any]:
    """Process a refund for an order.

    Records the refund to REFUND_LOG.
    Raises RefundError if amount > 1000 (backend cap).

    Returns:
        Refund confirmation dict with order_id, amount, refund_id, timestamp.

    Raises:
        RefundError: If amount > $1000 or order not found.
    """
    if amount > 1000.0:
        raise RefundError(f"Refund amount ${amount:.2f} exceeds maximum of $1000.00")

    # Verify order exists
    order = lookup_order(order_id)

    refund_record = {
        "refund_id": f"REF-{len(REFUND_LOG) + 1001}",
        "order_id": order_id,
        "amount": amount,
        "timestamp": 1706219400,  # Fixed for determinism
        "status": "processed",
    }
    REFUND_LOG.append(refund_record)

    return {
        "refund_id": refund_record["refund_id"],
        "order_id": order_id,
        "amount": amount,
        "status": "processed",
        "expected_delivery": "3-5 business days",
    }


def escalate_to_human(case_summary: str) -> dict[str, Any]:
    """Escalate a case to human support.

    Records escalation to ESCALATION_LOG.

    Returns:
        Escalation confirmation dict with case_id, queue_position, eta.
    """
    escalation_record = {
        "case_id": f"ESC-{len(ESCALATION_LOG) + 5001}",
        "summary": case_summary,
        "timestamp": 1706219400,  # Fixed for determinism
        "status": "queued",
    }
    ESCALATION_LOG.append(escalation_record)

    return {
        "case_id": escalation_record["case_id"],
        "status": "queued",
        "queue_position": len(ESCALATION_LOG),
        "estimated_wait": "5-10 minutes",
        "message": "A human agent will be with you shortly.",
    }
