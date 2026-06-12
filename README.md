# bootcamp

A hands-on lab runner for the seven Claude Certified Architect – Foundations
competency areas. Not exam prep: nine build-it-yourself labs with automated
verification, escalating hints, and a Haiku mentor.

## Setup

```bash
python3 -m venv .venv                      # Python ≥3.12
.venv/bin/pip install -e ".[dev]"          # installs the `bootcamp` CLI
export ANTHROPIC_API_KEY=sk-ant-...        # required for labs and judge checks
.venv/bin/bootcamp doctor                  # verify the install
```

## Daily loop

```bash
bootcamp status      # progress across the 9 modules (3 tracks, gated by dependency)
bootcamp next        # materialise the next lab into labs/NN-name/ (lesson, brief, starter)
bootcamp check       # run the current lab's verification suite
bootcamp hint        # escalating hints — L1 nudge, L2 mechanism, L3 pseudocode
bootcamp mentor "why does my hook never fire?"   # Haiku chat, rubric + your last check run in context
bootcamp solution    # reference sketch; unlocks after 3 failed check runs, marks module "assisted"
```

Your code lives in `labs/NN-name/workspace/` — the runner never edits it.
`--module NN` targets a specific module on any command.

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required: your lab agents, the mentor, and judge-evaluated checks |
| `BOOTCAMP_DB` | `./data/bootcamp.db` | Progress/check-run/hint state |
| `JUDGE_MODEL` | `claude-haiku-4-5` | Mentor + LLM-judge model |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Model your lab agents use (keep Haiku while iterating; switch to Sonnet for final runs if behaviour differs) |
| `GROCERY_DB_PATH` | — | Optional: point module 05's MCP server at your own SQLite DB |

## Curriculum

- **Track A — Agent SDK**: 01 agentic loop → 02 multi-agent orchestration, 03 hooks
- **Track B — Claude Code & MCP**: 04 Claude Code config → 06 CI/CD; 05 MCP server
- **Track C — Prompting & reliability**: 07 structured output; 08 context management (needs 03); 09 capstone (needs 02/03/05/07/08)

Tracks interleave; modules within a track gate sequentially.

## Real-surface options (recommended)

The mocks keep checks deterministic, but the transferable experience is in
wiring real surfaces:

- **Module 05**: build the MCP server over your grocery tracker's SQLite
  instead of the mock inventory DB — set `GROCERY_DB_PATH` (same schema notes
  in the lab brief; checks still run against the fixture DB).
- **Module 06**: adapt `starter/.gitlab-ci.yml` and run the review pipeline in
  your real GitLab CI; the local CI-simulating script is the checkable default.

## How checks work

Each module ships a `checks/` suite the runner discovers and executes
(`curriculum/modules/NN-name/checks/check_*.py`). Checks are deterministic
wherever possible: they run your workspace code against fixtures, inspect the
actual API transcript your agent produced (tool_result placement, trimmed
fields, normalised formats), and parse your source with `ast` for named
anti-patterns. A small Haiku judge (temperature 0, forced tool_use verdict
schema) is used only where judgment is inherent — e.g. tool-description
routing quality. Every failure names the criterion and the lesson section it
maps back to; it never includes the fix. Some checks need `ANTHROPIC_API_KEY`
(they execute your live agent) and fail with that message until it's set.

Module 03's adversarial check is the heart of the course: your refund-cap
hook is re-tested with a hostile system prompt claiming refunds are
unlimited — proving policy-as-control beats policy-as-prompt.

## Maintainer notes

- `tests/` — runner test suite (Anthropic mocked): `.venv/bin/python -m pytest tests/ -q`
- `scripts/validate_references.py` — installs each module's reference
  solution into its workspace and runs the checks (destructive to `labs/`).
  With `ANTHROPIC_API_KEY` set, all nine modules should pass end-to-end.
- `docs/contracts.md` — the build contract (CLI spec, check harness,
  fixture shapes, rubric format).
