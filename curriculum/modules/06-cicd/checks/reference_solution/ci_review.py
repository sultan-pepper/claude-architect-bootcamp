#!/usr/bin/env python3
"""Code review script using Claude API."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def make_fingerprint(file: str, line: int, category: str) -> str:
    """Create stable fingerprint for a finding."""
    content = f"{file}:{line}:{category}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def read_files(repo_path: Path, files: list[str]) -> dict[str, str]:
    """Read source files from repo."""
    result = {}
    for file_path in files:
        full_path = repo_path / file_path
        if full_path.exists():
            result[file_path] = full_path.read_text()
    return result


def build_prompt(repo_path: Path, prior_findings: list[dict] | None) -> str:
    """Build the review prompt."""
    # Files to review
    files_to_review = [
        "src/worker-service/process.py",
        "src/api-service/main.py",
        "src/worker-service/worker.py",
        "src/shared/utils.py",
        "config/config.py",
    ]

    files = read_files(repo_path, files_to_review)

    files_section = ""
    for file_path, content in files.items():
        files_section += f"=== {file_path} ===\n{content}\n\n"

    prior_findings_section = ""
    if prior_findings:
        prior_findings_section = f"""Previously reported findings — do not duplicate these (match by fingerprint):
{json.dumps(prior_findings, indent=2)}

"""

    schema_text = """{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["file", "line", "category", "severity", "explanation", "fingerprint"],
    "properties": {
      "file": {"type": "string", "description": "Relative path from repo root"},
      "line": {"type": "integer", "description": "Line number of the issue"},
      "category": {"type": "string", "description": "Issue category"},
      "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
      "explanation": {"type": "string", "description": "One-sentence explanation"},
      "fingerprint": {"type": "string", "description": "Stable hash for dedup"}
    }
  }
}"""

    prompt = f"""Review the following code files for exactly these bug categories:

- off-by-one: incorrect range boundaries that miss the first or last element
- wrong-comparison: field or value in a comparison that does not match the actual type schema
- unhandled-none: method called on a value that could be None without a guard
- resource-leak: file/socket/connection opened and never closed
- swallowed-exception: except block that catches and then passes or discards silently
- mutable-default: mutable default argument (list, dict, or set) in a function signature

Only report issues you are confident are real defects. Do not report style preferences,
missing docstrings, or speculative "could be improved" observations.

{prior_findings_section}Files to review:

{files_section}

Output a JSON array. Each element must have:
  file (string), line (integer), category (string), severity (critical|high|medium|low),
  explanation (string), fingerprint (string — sha256 of "file:line:category", first 16 hex chars)

Schema:
{schema_text}
"""

    return prompt


def run_review(repo_path: Path, prior_findings: list[dict] | None, output: Path, model: str) -> None:
    """Run code review using Claude."""
    prompt = build_prompt(repo_path, prior_findings)

    # Create temp file for schema
    schema_path = Path(__file__).parent / "findings_schema.json"
    if not schema_path.exists():
        # Use inline schema
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["file", "line", "category", "severity", "explanation", "fingerprint"],
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "category": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "explanation": {"type": "string"},
                    "fingerprint": {"type": "string"}
                }
            }
        }
        schema_path = Path("/tmp/findings_schema.json")
        schema_path.write_text(json.dumps(schema))

    # Call Claude
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--output-format", "json",
         "--json-schema", str(schema_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Parse response
    try:
        envelope = json.loads(result.stdout)
        findings = json.loads(envelope.get("result", "[]"))
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing response: {e}", file=sys.stderr)
        sys.exit(1)

    # Add/fix fingerprints
    for finding in findings:
        finding["fingerprint"] = make_fingerprint(
            finding.get("file", ""),
            finding.get("line", 0),
            finding.get("category", "")
        )

    # Filter out duplicates of prior findings
    if prior_findings:
        prior_fingerprints = {f.get("fingerprint") for f in prior_findings}
        findings = [f for f in findings if f.get("fingerprint") not in prior_fingerprints]

    # Write output
    output.write_text(json.dumps(findings, indent=2))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Code review using Claude")
    parser.add_argument("--repo-path", type=Path, required=True, help="Path to repository")
    parser.add_argument("--output", type=Path, required=True, help="Output file for findings")
    parser.add_argument("--prior-findings", type=Path, help="Prior findings file for dedup")
    parser.add_argument("--model", default="claude-haiku-4-5", help="Claude model to use")

    args = parser.parse_args()

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Load prior findings
    prior_findings = None
    if args.prior_findings and args.prior_findings.exists():
        prior_findings = json.loads(args.prior_findings.read_text())

    # Run review
    run_review(args.repo_path, prior_findings, args.output, args.model)


if __name__ == "__main__":
    main()
