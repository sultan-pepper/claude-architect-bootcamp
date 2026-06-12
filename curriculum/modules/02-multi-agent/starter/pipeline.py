"""M02 — Multi-agent orchestration: research pipeline skeleton.

Implement run_pipeline() according to the contract in README.md.
Fill every TODO. Do not change the function signature or return shape.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "claude-haiku-4-5"

_fixtures_path = Path(os.environ.get("FIXTURES_PATH", Path(__file__).parent / ".." / "fixtures"))
CORPUS_PATH = _fixtures_path / "corpus"


# ---------------------------------------------------------------------------
# Corpus loader
# ---------------------------------------------------------------------------
def load_corpus() -> dict[str, str]:
    """Load all .md files from the corpus directory.

    Returns a dict mapping filename (stem) to document text.
    """
    # TODO: read all *.md files from CORPUS_PATH
    # Return {stem: text} — e.g., {"doc_001_containers_basics": "..."}
    raise NotImplementedError("load_corpus not yet implemented")


# ---------------------------------------------------------------------------
# Search subagent
# ---------------------------------------------------------------------------
def run_search_agent(sub_topic: str, doc_texts: list[str]) -> str:
    """Run a single isolated search subagent for one sub-topic.

    Args:
        sub_topic: The sub-domain to research (e.g., "Networking").
        doc_texts: List of document text strings relevant to this subagent.
                   The caller selects which docs to pass; this function
                   passes them as-is to the model.

    Returns:
        Subagent response text (findings for this sub-topic).

    TODO:
    - Build a system prompt identifying this agent's role and sub-topic.
    - Build a user message containing the document texts.
    - Make a SINGLE client.messages.create call (not a loop).
    - Return the response text.
    - Record system_prompt and result in run_log (see run_pipeline).
    """
    # TODO: implement
    raise NotImplementedError("run_search_agent not yet implemented")


# ---------------------------------------------------------------------------
# Synthesis subagent
# ---------------------------------------------------------------------------
def run_synthesis_agent(findings: dict[str, str]) -> str:
    """Run the synthesis subagent with all collected findings.

    Args:
        findings: Dict mapping sub_topic -> search agent result text.
                  ALL findings must appear in the prompt passed to the model.

    Returns:
        Final report text.

    TODO:
    - Build a user prompt that includes the actual findings text for every
      sub-topic (not just the topic names).
    - Make a SINGLE client.messages.create call.
    - Return the response text.
    - Record user_prompt and result in run_log (see run_pipeline).
    """
    # TODO: implement
    raise NotImplementedError("run_synthesis_agent not yet implemented")


# ---------------------------------------------------------------------------
# Coordinator tool schema
# ---------------------------------------------------------------------------
# TODO: Define the tool schema for spawn_search_agent.
#       The coordinator calls this tool once per sub-topic it identifies.
COORDINATOR_TOOLS: list[dict[str, Any]] = [
    # TODO: spawn_search_agent tool with sub_topic: string parameter
]


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------
def run_pipeline(topic: str) -> dict[str, Any]:
    """Run the full multi-agent research pipeline.

    Args:
        topic: Research topic string (e.g., "Containerization and Orchestration").

    Returns:
        {
            "report": str,
            "run_log": {
                "coordinator_turns": list[dict],
                "subagent_calls":    list[dict],
                "synthesis_call":    dict,
            }
        }

    TODO:
    1. Load the corpus.
    2. Run the coordinator agentic loop (standard M01 pattern):
       - Give the coordinator a system prompt that instructs it to identify
         all sub-domains and call spawn_search_agent for each — simultaneously.
       - When the coordinator returns tool_use blocks, detect ALL blocks in
         that turn and dispatch them concurrently with ThreadPoolExecutor.
       - Record each turn's tool_calls in run_log["coordinator_turns"].
       - Collect all tool results and append them (as one user message) before
         continuing the coordinator loop.
    3. After all search agents complete, call run_synthesis_agent with all findings.
    4. Return the final report and run_log.

    Key invariant: run_log["synthesis_call"]["user_prompt"] must contain the
    actual text returned by the search subagents, not just their topic names.
    """
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()

    run_log: dict[str, Any] = {
        "coordinator_turns": [],
        "subagent_calls": [],
        "synthesis_call": {},
    }

    corpus = load_corpus()

    # TODO: implement coordinator loop with parallel subagent dispatch

    # TODO: call synthesis agent once all search results are collected

    report = ""  # replace with synthesis result
    return {"report": report, "run_log": run_log}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <topic>", file=sys.stderr)
        sys.exit(2)
    result = run_pipeline(sys.argv[1])
    print(json.dumps(result))
