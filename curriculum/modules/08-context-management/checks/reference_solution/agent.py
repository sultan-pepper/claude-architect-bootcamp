"""Reference solution for M08: context-management agent."""

import anthropic
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Import fixtures backend
sys.path.insert(0, os.environ.get("FIXTURES_PATH", "."))
import support_backend


BASE_SYSTEM = """You are a helpful customer support agent. Help customers with their orders, refunds, and account information.
You have access to the following tools:
- get_customer: Retrieve customer account information
- find_customers: Search for customers by name
- lookup_order: Look up order details
- process_refund: Process a refund for an order
- escalate_to_human: Escalate to a human supervisor

Use these tools to help resolve customer issues."""

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


def dispatch_tool(name: str, inputs: dict, case_facts: dict, handoff_info: dict) -> str:
    """Dispatch tool call to backend, applying post-processing hooks."""
    try:
        if name == "get_customer":
            result = support_backend.get_customer(inputs["customer_id"])
            case_facts["customer_id"] = inputs["customer_id"]
            return json.dumps(result)

        elif name == "find_customers":
            result = support_backend.find_customers(inputs["name"])
            return json.dumps(result)

        elif name == "lookup_order":
            result = support_backend.lookup_order(inputs["order_id"])
            # Normalize timestamps and status
            if "delivery_date" in result:
                result["delivery_date"] = normalize_timestamp(result["delivery_date"])
            if "ship_date" in result:
                result["ship_date"] = normalize_timestamp(result["ship_date"])
            if "order_date" in result:
                result["order_date"] = normalize_timestamp(result["order_date"])
            if "status" in result:
                result["status"] = normalize_status(result["status"])
            # Update case facts
            if "subtotal" in result:
                case_facts["confirmed_amounts"][f"{inputs['order_id']}_subtotal"] = result["subtotal"]
            # Trim for history
            trimmed = trim_order(result)
            return json.dumps(trimmed)

        elif name == "process_refund":
            amount = inputs["amount"]
            order_id = inputs["order_id"]
            # Check if over $500 policy cap
            if amount > 500:
                # Escalate instead
                handoff_info["customer_id"] = case_facts.get("customer_id")
                handoff_info["root_cause"] = f"Refund of ${amount} exceeds $500 policy cap"
                handoff_info["amount"] = amount
                handoff_info["recommended_action"] = "Escalate to supervisor for refund exception approval"
                return support_backend.escalate_to_human(f"Refund request exceeds policy: ${amount} for {order_id}")

            result = support_backend.process_refund(order_id, amount)
            return json.dumps(result)

        elif name == "escalate_to_human":
            result = support_backend.escalate_to_human(inputs["case_summary"])
            return json.dumps(result)

        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})


def build_system(base: str, facts: dict) -> str:
    """Build system prompt with case facts."""
    return base + "\n\n## Case facts (always current)\n" + json.dumps(facts, indent=2)


def run_conversation(user_messages: list[str]) -> dict:
    """Run multi-turn conversation with persistent case facts."""
    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

    case_facts = {
        "customer_id": None,
        "confirmed_amounts": {},
        "root_cause": None
    }
    handoff_info = {}

    messages = []
    transcript = []

    for user_msg in user_messages:
        # Add user message
        messages.append({"role": "user", "content": user_msg})
        transcript.append({"role": "user", "content": user_msg})

        # Run agentic loop for this turn
        while True:
            # Rebuild system with current facts
            system = build_system(BASE_SYSTEM, case_facts)

            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=system,
                tools=TOOLS,
                messages=messages
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                # End of turn, extract text response
                for block in response.content:
                    if hasattr(block, "text"):
                        final_response = block.text
                        break
                content_dicts = [b.model_dump() for b in response.content]
                messages.append({"role": "assistant", "content": content_dicts})
                transcript.append({"role": "assistant", "content": content_dicts})
                break

            if response.stop_reason == "tool_use":
                # Process tool calls
                content_dicts = [b.model_dump() for b in response.content]
                messages.append({"role": "assistant", "content": content_dicts})
                transcript.append({"role": "assistant", "content": content_dicts})

                # Dispatch tools
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_tool(block.name, block.input, case_facts, handoff_info)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})
                transcript.append({"role": "user", "content": tool_results})
                continue

    result = {
        "response": final_response,
        "transcript": transcript
    }

    # Add handoff if it exists
    if handoff_info:
        result["handoff"] = handoff_info

    return result


if __name__ == "__main__":
    import sys
    user_messages = json.loads(sys.stdin.read())
    result = run_conversation(user_messages)
    print(json.dumps(result, indent=2))
