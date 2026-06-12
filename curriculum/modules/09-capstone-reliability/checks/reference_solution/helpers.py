"""Helpers for M09 reference solution: tools, dispatch, normalisation, state.

Imported by agent.py. Not the entry point — use agent.py.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Import fixtures backend; FIXTURES_PATH must be set before agent.py is imported.
sys.path.insert(0, os.environ.get("FIXTURES_PATH", "."))
import support_backend  # noqa: E402


ESCALATION_CRITERIA = """
=== Escalation — call escalate_to_human ONLY when: ===
1. Refund exceeds $500 policy cap.
2. Customer explicitly requests a human agent — do this FIRST, no other tools.
3. Resolution requires authority beyond your tools.

What does NOT trigger escalation:
- Customer frustration or complaint sentiment
- Invalid order IDs or bad lookups
- Questions you can answer with available tools

Examples:
- "I need a $700 refund for order O004" → criterion 1, escalate
- "I want to talk to a real person right now" → criterion 2, escalate immediately
- "Where is my order O001?" → use lookup_order, do NOT escalate
- "This service is terrible" → address the issue, do NOT escalate
"""

BASE_SYSTEM = f"""You are a helpful customer support agent. Help customers with their orders, refunds, and account information.

{ESCALATION_CRITERIA}

Available tools:
- get_customer: Retrieve customer account information
- find_customers: Search for customers by name (may return multiple results)
- lookup_order: Look up order details
- process_refund: Process a refund for an order
- escalate_to_human: Escalate to a human supervisor

When find_customers returns multiple results, ask for clarification (email, tier, spend amount) before acting.
Do NOT heuristically pick a result."""

TRIM_ORDER_FIELDS = {
    "id", "status", "subtotal", "total", "delivery_date",
    "tracking_number", "items", "shipping_address", "tax", "shipping"
}

TOOLS = [
    {
        "name": "get_customer",
        "description": "Get customer account information by ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID (e.g., C001)"}
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "find_customers",
        "description": "Find customers by name (may return multiple results)",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Customer name to search for"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "lookup_order",
        "description": "Look up order details by order ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID (e.g., O001)"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "process_refund",
        "description": "Process a refund for an order",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
                "amount": {"type": "number", "description": "Refund amount"}
            },
            "required": ["order_id", "amount"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate issue to a human supervisor",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_summary": {"type": "string", "description": "Summary of the issue"}
            },
            "required": ["case_summary"]
        }
    }
]


def normalize_timestamp(ts):
    """Convert Unix timestamp or ISO string to consistent format."""
    if isinstance(ts, int):
        return datetime.utcfromtimestamp(ts).isoformat() + "Z"
    return ts


def normalize_status(status):
    """Normalize order status to uppercase."""
    if isinstance(status, str):
        return status.upper()
    return status


def trim_order(raw: dict) -> dict:
    """Trim order dict to relevant fields."""
    return {k: v for k, v in raw.items() if k in TRIM_ORDER_FIELDS}


def dispatch_tool(name: str, inputs: dict, state: dict) -> str:
    """Dispatch tool call to backend."""
    try:
        if name == "get_customer":
            result = support_backend.get_customer(inputs["customer_id"])
            return json.dumps(result)

        elif name == "find_customers":
            result = support_backend.find_customers(inputs["name"])
            if isinstance(result, list) and len(result) > 1:
                state["clarification_asked"] = True
            return json.dumps(result)

        elif name == "lookup_order":
            try:
                result = support_backend.lookup_order(inputs["order_id"])
                for field in ("delivery_date", "ship_date", "order_date"):
                    if field in result:
                        result[field] = normalize_timestamp(result[field])
                if "status" in result:
                    result["status"] = normalize_status(result["status"])
                state["successful_lookups"].append(inputs["order_id"])
                return json.dumps(trim_order(result))
            except KeyError:
                state["failed_lookups"].append(inputs["order_id"])
                return json.dumps({"error": f"Order {inputs['order_id']} not found"})

        elif name == "process_refund":
            amount = inputs["amount"]
            order_id = inputs["order_id"]
            if amount > 500:
                state["escalated"] = True
                return support_backend.escalate_to_human(
                    f"Refund request exceeds $500 policy cap: ${amount} for order {order_id}"
                )
            result = support_backend.process_refund(order_id, amount)
            return json.dumps(result)

        elif name == "escalate_to_human":
            state["escalated"] = True
            result = support_backend.escalate_to_human(inputs["case_summary"])
            return json.dumps(result)

        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})
