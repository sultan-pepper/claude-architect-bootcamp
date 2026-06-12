# bootcamp

CLI lab-runner teaching Claude Agent SDK / Claude Code / MCP / structured output /
context management / CI/CD / reliability through verified hands-on labs.

## Hard rules
- Python 3.12, type hints everywhere, Typer for CLI, sqlite3 stdlib (no ORM)
- DB path from env BOOTCAMP_DB, default ./data/bootcamp.db
- ANTHROPIC_API_KEY from env only. Mentor/judge model from env JUDGE_MODEL,
  default claude-haiku-4-5
- The runner NEVER edits learner workspace files. Checks read and execute only.
- Every check failure message must name the failed criterion AND the lesson
  section it maps to. Never include the fix.
- Mentor system prompt: teach via questions and pointers; refuse to write the
  learner's lab code; may show API-shape examples ≤5 lines unrelated to the
  specific solution.
- Hints: 3 levels per lab stored in rubric.md. Level unlocks only after a failed
  check run since the last unlock. `bootcamp solution` requires 3 failed runs
  and flags the module "assisted" in progress.
- All Anthropic calls mocked in tests/ (runner tests). Curriculum checks/ MAY
  call the real API when run by the learner — that is the point.
- Files under 300 lines; split modules rather than grow them.

## Module registry (id, name, track, depends_on)
01 agentic-loop A —
02 multi-agent A 01
03 hooks A 01
04 claude-code-config B —
05 mcp-server B —
06 cicd B 04
07 structured-output C —
08 context-management C 03
09 capstone-reliability C 02,03,05,07,08
