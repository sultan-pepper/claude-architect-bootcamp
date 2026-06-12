"""M06 — CI/CD integration: automated code review pipeline skeleton.

Implement all TODOs. Do not change the CLI argument names or exit-code contract.

CLI:
  python ci_review.py --repo-path PATH --output FILE [--prior-findings FILE]

Exit 0 on success (including when findings is an empty list).
Exit 1 on harness error (API failure, bad arguments, schema error).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "claude-haiku-4-5"
SCHEMA_PATH = Path(__file__).parent / "findings_schema.json"
PROMPT_PATH = Path(__file__).parent / "review_prompt.md"


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------
def make_fingerprint(file: str, line: int, category: str) -> str:
    """Stable identifier for a finding. Hash (file, line, category) — NOT the explanation."""
    return hashlib.sha256(f"{file}:{line}:{category}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------
def build_prompt(
    repo_path: Path,
    prior_findings: list[dict],
) -> str:
    """Read review_prompt.md and fill template placeholders.

    TODO:
    - Read PROMPT_PATH to get the template.
    - Read the source files from repo_path that you want Claude to review.
      Embed their contents in the prompt (include the file path as a header
      so Claude can reference it in findings).
    - Inject prior_findings as JSON into the {{ prior_findings }} slot
      (if prior_findings is empty, inject an empty list or omit the section).
    - Return the filled prompt string.
    """
    # TODO: implement
    raise NotImplementedError("build_prompt not yet implemented")


# ---------------------------------------------------------------------------
# Claude invocation
# ---------------------------------------------------------------------------
def call_claude(prompt: str, model: str) -> list[dict]:
    """Call claude -p with --output-format json --json-schema and return findings list.

    TODO:
    - Run: claude -p PROMPT --output-format json --json-schema SCHEMA_PATH
      using subprocess.run with capture_output=True, text=True, timeout=120.
    - On non-zero exit: print stderr to sys.stderr and sys.exit(1).
    - Parse the JSON envelope from stdout:
        envelope = json.loads(result.stdout)
        findings = json.loads(envelope["result"])
    - Return the findings list.
    """
    # TODO: implement
    raise NotImplementedError("call_claude not yet implemented")


# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------
def deduplicate(findings: list[dict], prior_findings: list[dict]) -> list[dict]:
    """Remove any finding whose fingerprint matches a prior fingerprint.

    TODO:
    - Build a set of fingerprints from prior_findings.
    - Return only findings whose fingerprint is NOT in that set.
    - If a finding is missing a fingerprint field, keep it (don't crash).
    """
    # TODO: implement
    return findings  # placeholder — replace with actual dedup


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Claude-powered CI code review")
    parser.add_argument("--repo-path", required=True, type=Path,
                        help="Path to repository root to review")
    parser.add_argument("--output", required=True, type=Path,
                        help="Path to write findings JSON array")
    parser.add_argument("--prior-findings", type=Path, default=None,
                        help="Path to findings JSON from a previous run (for dedup)")
    parser.add_argument("--model", default=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
                        help="Anthropic model to use")
    args = parser.parse_args()

    if not args.repo_path.is_dir():
        sys.exit(f"--repo-path {args.repo_path} is not a directory")

    prior_findings: list[dict] = []
    if args.prior_findings is not None:
        if not args.prior_findings.is_file():
            sys.exit(f"--prior-findings {args.prior_findings} does not exist")
        prior_findings = json.loads(args.prior_findings.read_text())

    # Build prompt
    prompt = build_prompt(args.repo_path, prior_findings)

    # Call Claude
    findings = call_claude(prompt, args.model)

    # Ensure fingerprints are present and correct
    for finding in findings:
        if not finding.get("fingerprint"):
            finding["fingerprint"] = make_fingerprint(
                finding.get("file", ""),
                finding.get("line", 0),
                finding.get("category", ""),
            )

    # Deduplicate against prior findings
    findings = deduplicate(findings, prior_findings)

    # Write output
    args.output.write_text(json.dumps(findings, indent=2))
    print(f"Wrote {len(findings)} finding(s) to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
