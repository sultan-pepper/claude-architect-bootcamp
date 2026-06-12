"""Reference solution for Module 01: agentic-loop."""

import anthropic
import json
import os
import sys


def get_fixtures_path() -> str:
    """Get fixtures path from environment or use default."""
    return os.getenv("FIXTURES_PATH", "./fixtures")


# Add fixtures to path
fixtures_path = get_fixtures_path()
if fixtures_path not in sys.path:
    sys.path.insert(0, fixtures_path)

import support_backend


# Tool definitions
TOOLS = [
    {
        "name": "get_customer",
        "description": "Fetch a customer record by ID (e.g., 'C001'). Returns customer name, email, phone, account info, and tier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID (e.g., 'C001')"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "find_customers",
        "description": "Search for customers by name (partial match, case-insensitive). Returns list of matching customers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer name or partial name to search for"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "lookup_order",
        "description": "Fetch order details by ID (e.g., 'O001'). Returns order status, shipping info, line items, and timeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID (e.g., 'O001')"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "process_refund",
        "description": "Process a refund for an order. Specify the order ID and refund amount.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to refund"
                },
                "amount": {
                    "type": "number",
                    "description": "Refund amount in USD"
                }
            },
            "required": ["order_id", "amount"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate a customer issue to a human support agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_summary": {
                    "type": "string",
                    "description": "Summary of the issue to escalate"
                }
            },
            "required": ["case_summary"]
        }
    }
]


def dispatch_tool(name: str, inputs: dict) -> str:
    """Dispatch a tool call to the appropriate backend function."""
    handlers = {
        "get_customer": support_backend.get_customer,
        "find_customers": support_backend.find_customers,
        "lookup_order": support_backend.lookup_order,
        "process_refund": support_backend.process_refund,
        "escalate_to_human": support_backend.escalate_to_human,
    }

    if name not in handlers:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        result = handlers[name](**inputs)
        return json.dumps(result)
    except support_backend.RefundError as e:
        return json.dumps({"error": str(e.message)})
    except KeyError as e:
        return json.dumps({"error": f"Not found: {e}"})


def run_conversation(user_messages: list[str]) -> dict:
    """Run the agentic conversation loop."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    # Build initial messages
    messages = []
    for msg in user_messages:
        messages.append({"role": "user", "content": msg})

    system_prompt = (
        "You are a helpful customer support agent. "
        "Use the available tools to help customers with their inquiries. "
        "Be friendly and efficient."
    )

    # Main agentic loop
    while True:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )

        # Append assistant response to messages (convert SDK objects to plain dicts)
        messages.append({
            "role": "assistant",
            "content": [b.model_dump() for b in response.content]
        })

        # Check if we should exit the loop
        if response.stop_reason == "end_turn":
            break

        # Process tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_result = dispatch_tool(
                        content_block.name,
                        content_block.input
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })

            # Append tool results as user message
            if tool_results:
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

    # Extract final response text
    final_response = ""
    for content_block in response.content:
        if hasattr(content_block, "text"):
            final_response = content_block.text
            break

    return {
        "response": final_response,
        "transcript": messages
    }


if __name__ == "__main__":
    user_input = sys.stdin.read()
    user_messages = json.loads(user_input)
    result = run_conversation(user_messages)
    print(json.dumps(result))
