"""Reference solution for Module 02: multi-agent."""

import anthropic
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def get_fixtures_path() -> str:
    """Get fixtures path from environment or use default."""
    return os.getenv("FIXTURES_PATH", "./fixtures")


def load_corpus() -> dict[str, str]:
    """Load all corpus documents."""
    fixtures_path = Path(get_fixtures_path())
    corpus_dir = fixtures_path / "corpus"

    corpus_docs = {}
    for doc_file in sorted(corpus_dir.glob("doc_*.md")):
        with open(doc_file) as f:
            corpus_docs[doc_file.stem] = f.read()

    return corpus_docs


def get_relevant_docs(topic: str, corpus_index: dict, corpus_docs: dict) -> dict[str, list[str]]:
    """Map each subdomain to its relevant corpus documents."""
    relevant = {}
    for doc in corpus_index["documents"]:
        subdomain = doc["subdomain"]
        filename_stem = doc["filename"].replace(".md", "")
        if subdomain not in relevant:
            relevant[subdomain] = []
        if filename_stem in corpus_docs:
            relevant[subdomain].append(corpus_docs[filename_stem])

    return relevant


def run_search_agent(sub_topic: str, docs: list[str]) -> str:
    """Run a single search agent call."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    system_prompt = (
        f"You are a technical researcher specializing in {sub_topic}. "
        f"Use only the documents provided to write a comprehensive summary "
        f"of the {sub_topic} domain. Focus on technical details and best practices."
    )

    combined_docs = "\n\n".join(docs)

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Please provide a comprehensive summary of {sub_topic} based on these documents:\n\n{combined_docs}"
        }]
    )

    # Extract text from response
    for content_block in response.content:
        if hasattr(content_block, "text"):
            return content_block.text

    return ""


def run_synthesis_agent(findings: dict[str, str]) -> str:
    """Run the synthesis agent."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    # Build synthesis prompt with all findings
    synthesis_content = "\n\n".join(
        f"## {topic}\n{content}"
        for topic, content in findings.items()
    )

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system="You are a technical synthesis expert. Combine the provided research findings into a comprehensive, well-organized report.",
        messages=[{
            "role": "user",
            "content": f"Please synthesize the following research findings into a comprehensive report on Containerization and Orchestration:\n\n{synthesis_content}"
        }]
    )

    # Extract text from response
    for content_block in response.content:
        if hasattr(content_block, "text"):
            return content_block.text

    return ""


def run_pipeline(topic: str) -> dict:
    """Run the multi-agent research pipeline."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    # Load corpus and index
    corpus_docs = load_corpus()
    fixtures_path = Path(get_fixtures_path())
    with open(fixtures_path / "corpus" / "corpus_index.json") as f:
        corpus_index = json.load(f)

    # Map subdomains to documents
    relevant_docs = get_relevant_docs(topic, corpus_index, corpus_docs)

    # Define coordinator tools
    tools = [{
        "name": "spawn_search_agent",
        "description": "Spawn a search agent to research a specific subdomain",
        "input_schema": {
            "type": "object",
            "properties": {
                "sub_topic": {
                    "type": "string",
                    "description": "The subdomain to research (e.g., 'Containers', 'Networking')"
                }
            },
            "required": ["sub_topic"]
        }
    }]

    # Initialize coordinator
    messages = [{
        "role": "user",
        "content": f"I need a comprehensive report on: {topic}. Identify all distinct sub-domains and research each one thoroughly."
    }]

    system_prompt = (
        "You are a research coordinator. Your job is to identify all distinct sub-domains "
        "in the provided topic and dispatch search agents to research each one. "
        "Call spawn_search_agent for every distinct sub-domain simultaneously in a single response to enable parallel research. "
        "Once all research is complete, compile the findings into a final report."
    )

    # Coordinator loop
    coordinator_turns = []
    subagent_calls = []
    findings = {}
    synthesis_prompt = None

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        # Append coordinator response
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # Check if coordinator is done
        if response.stop_reason == "end_turn":
            break

        # Collect tool calls for parallel dispatch
        if response.stop_reason == "tool_use":
            tool_calls_batch = []
            tool_use_blocks = []

            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_calls_batch.append({
                        "name": content_block.name,
                        "input": content_block.input
                    })
                    tool_use_blocks.append(content_block)

            # Record coordinator turn
            coordinator_turns.append({
                "tool_calls": tool_calls_batch
            })

            # Execute all search agents in parallel
            if tool_use_blocks:
                results = {}
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = {}
                    for block in tool_use_blocks:
                        sub_topic = block.input["sub_topic"]
                        docs = relevant_docs.get(sub_topic, [])
                        future = executor.submit(run_search_agent, sub_topic, docs)
                        futures[sub_topic] = future

                    # Collect results
                    for sub_topic, future in futures.items():
                        try:
                            result_text = future.result()
                            results[sub_topic] = result_text
                            findings[sub_topic] = result_text
                            subagent_calls.append({
                                "sub_topic": sub_topic,
                                "system_prompt": f"You are a technical researcher specializing in {sub_topic}. Use only the documents provided.",
                                "result": result_text
                            })
                        except Exception as e:
                            results[sub_topic] = f"Error: {e}"

                # Append tool results
                tool_results = []
                for sub_topic, result_text in results.items():
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": next(
                            (b.id for b in tool_use_blocks if b.input["sub_topic"] == sub_topic),
                            ""
                        ),
                        "content": result_text
                    })

                messages.append({
                    "role": "user",
                    "content": tool_results
                })

    # Run synthesis agent
    synthesis_response_text = run_synthesis_agent(findings)
    synthesis_prompt = "\n\n".join(
        f"## {topic}\n{content}"
        for topic, content in findings.items()
    )

    return {
        "report": synthesis_response_text,
        "run_log": {
            "coordinator_turns": coordinator_turns,
            "subagent_calls": subagent_calls,
            "synthesis_call": {
                "user_prompt": synthesis_prompt,
                "result": synthesis_response_text
            }
        }
    }


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "Containerization and Orchestration"
    result = run_pipeline(topic)
    print(json.dumps(result, indent=2))
