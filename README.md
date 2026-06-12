# bootcamp

> 🤖 **Vibe-coded by Claude.** This entire app — the runner, all nine labs,
> the fixtures, the verification suites, and these docs — was built end-to-end
> by [Claude](https://claude.com/claude-code) (Fable 5, running in Claude
> Code) from a single design brief: Claude scaffolded the project, dispatched
> its own builder/curriculum/checker subagents, reviewed its own output with
> an independent agent, fixed the findings, and pushed this repo. A human
> (hi, Kieran) supplied the brief and the GitHub login.

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

## Your first lab (concrete walkthrough)

```bash
# 1. Install and point at your API key
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-haiku-4-5   # keep Haiku while you iterate

# 2. Materialise module 01 into your workspace
.venv/bin/bootcamp next
# → creates  labs/01-agentic-loop/
#               lesson.md      read this first — concept + API reference
#               lab.md         the task spec + acceptance criteria
#               workspace/
#                 agent.py     starter skeleton — THIS is the file you edit
#                 README.md    quick contract reminder

# 3. Read the brief, then open your editor
#    labs/01-agentic-loop/workspace/agent.py has TODO comments guiding every step.
#    Fill them in. The runner never touches this file — it's yours.

# 4. Run the checker
.venv/bin/bootcamp check
# Each failing criterion prints: [FAIL] <criterion-name>  (<lesson section>)
# Each passing criterion prints: [PASS] <criterion-name>

# 5. If you're stuck — escalate through hints
.venv/bin/bootcamp hint        # L1: a nudge (requires at least one failed check run)
.venv/bin/bootcamp hint        # L2: the mechanism explained
.venv/bin/bootcamp hint        # L3: pseudocode

# 6. Ask the mentor a question
.venv/bin/bootcamp mentor "why does my loop exit before the tool result is appended?"
# Haiku chat with the lesson + your last check run in context.
# It will ask you questions and point you at docs — it won't write your code.

# 7. Once all checks pass
.venv/bin/bootcamp status      # shows module 01 as passed, unlocks module 02
.venv/bin/bootcamp next        # materialises the next module
```

**What the workspace looks like** after `bootcamp next` for module 01:

```
labs/
└── 01-agentic-loop/
    ├── lesson.md          ← read this first
    ├── lab.md             ← task spec, acceptance criteria, fixture docs
    └── workspace/
        ├── agent.py       ← edit this (and only this for M01)
        └── README.md      ← quick contract ref
```

The `curriculum/` directory is read-only source — the runner copies starter files into `labs/` when you run `bootcamp next`. Your workspace is never touched by the runner again.

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
