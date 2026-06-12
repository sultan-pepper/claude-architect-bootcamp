# bootcamp — contracts (single source of truth)

This document is included verbatim in every subagent prompt. Subagents share no
other context. If anything here conflicts with an ad-hoc instruction, this
document wins; report the conflict instead of improvising.

## 1. Repository layout

```
bootcamp/                    # repo root (the CWD)
├── CLAUDE.md
├── .claude/agents/ .claude/rules/
├── bootcamp_cli/            # runner package (runner-builder owns)
├── curriculum/
│   ├── manifest.json
│   └── modules/NN-name/
│       ├── lesson.md        # concept brief        (curriculum-author owns)
│       ├── lab.md           # lab brief + criteria (curriculum-author owns)
│       ├── rubric.md        # criteria/hints/etc.  (curriculum-author owns)
│       ├── starter/         # copied to labs/NN-name/workspace on `next`
│       ├── fixtures/        # mock backends etc.   (fixtures-builder owns)
│       └── checks/          # check_*.py           (checker-builder owns)
├── labs/NN-name/            # learner workspaces (gitignored, runner-materialised)
│   ├── lesson.md  lab.md    # copies
│   └── workspace/           # learner's code — runner NEVER writes here after `next`
├── tests/                   # pytest for the runner itself (mocked Anthropic)
├── docs/contracts.md        # this file
├── pyproject.toml           # already exists: entry point bootcamp = bootcamp_cli.main:app
└── requirements.txt
```

Module directories (id, dir name, track, depends_on):

```
01 01-agentic-loop          A  —
02 02-multi-agent           A  01
03 03-hooks                 A  01
04 04-claude-code-config    B  —
05 05-mcp-server            B  —
06 06-cicd                  B  04
07 07-structured-output     C  —
08 08-context-management    C  03
09 09-capstone-reliability  C  02,03,05,07,08
```

## 2. curriculum/manifest.json

```json
{
  "modules": [
    {"id": "01", "dir": "01-agentic-loop", "name": "agentic-loop",
     "title": "The agentic loop", "track": "A", "depends_on": []},
    {"id": "02", "dir": "02-multi-agent", "name": "multi-agent",
     "title": "Multi-agent orchestration", "track": "A", "depends_on": ["01"]},
    {"id": "03", "dir": "03-hooks", "name": "hooks",
     "title": "Hooks and lifecycle", "track": "A", "depends_on": ["01"]},
    {"id": "04", "dir": "04-claude-code-config", "name": "claude-code-config",
     "title": "Team-grade Claude Code config", "track": "B", "depends_on": []},
    {"id": "05", "dir": "05-mcp-server", "name": "mcp-server",
     "title": "MCP server design", "track": "B", "depends_on": []},
    {"id": "06", "dir": "06-cicd", "name": "cicd",
     "title": "CI/CD integration", "track": "B", "depends_on": ["04"]},
    {"id": "07", "dir": "07-structured-output", "name": "structured-output",
     "title": "Structured output & extraction", "track": "C", "depends_on": []},
    {"id": "08", "dir": "08-context-management", "name": "context-management",
     "title": "Context management", "track": "C", "depends_on": ["03"]},
    {"id": "09", "dir": "09-capstone-reliability", "name": "capstone-reliability",
     "title": "Capstone — escalation & reliability", "track": "C",
     "depends_on": ["02", "03", "05", "07", "08"]}
  ]
}
```

The runner discovers modules ONLY through this manifest. Within a track,
modules unlock in id order AND when all `depends_on` are passed; tracks are
independent of each other.

## 3. CLI command spec (Typer app: `bootcamp_cli/main.py`, `app`)

Global behaviour: exit code 0 = success / all pass; 1 = expected negative
(check failures, gated refusal, nothing available); 2 = usage or internal
error. Errors print to stderr. `--module / -m NN` overrides the "current
module" everywhere it appears. "Current module" = the most recently
`next`-ed module still in state `in_progress`.

- `bootcamp status [--json]` — table: id, title, track, state, check summary
  (last run pass/fail counts), assisted flag. States: `locked`, `available`,
  `in_progress`, `passed`. `--json` emits the same as JSON. Exit 0 always.
- `bootcamp next [--module NN]` — picks the lowest-id `available` module
  (or the named one if available), creates `labs/NN-name/`, copies lesson.md
  + lab.md there and `starter/` → `labs/NN-name/workspace/`, sets state
  `in_progress`, prints the lab path and brief intro. If the lab dir already
  exists, never overwrite workspace files — print path and exit 0. Exit 1 if
  nothing is available (with the reason: dependencies unmet).
- `bootcamp check [--module NN] [--json]` — runs the module's check suite
  (section 4). Prints one line per check: `PASS`/`FAIL`, criterion name,
  detail, `lesson_ref`. Records a row in `check_runs`. All pass → state
  `passed`, exit 0; any fail → exit 1; harness crash → exit 2.
- `bootcamp hint [--module NN]` — prints the next hint level from rubric.md.
  Gating: level N+1 unlocks only if there is a failed check run AFTER the
  unlock of level N (level 1 requires ≥1 failed run). Refusal prints how to
  unlock, exit 1.
- `bootcamp mentor "QUESTION" [--module NN]` — one-shot chat turn with the
  mentor (section 6). Persists both sides to `mentor_messages` and replays
  prior turns of that module's conversation as history. Exit 0; exit 2 if
  ANTHROPIC_API_KEY missing.
- `bootcamp solution [--module NN]` — requires ≥3 failed check runs for the
  module; prints rubric.md's "Reference solution sketch" section and sets
  `assisted=1`. Otherwise refuse with the count so far, exit 1.
- `bootcamp doctor` — verifies: python ≥3.12, ANTHROPIC_API_KEY set,
  curriculum manifest loads and all module dirs/required files exist, DB
  writable, `claude` CLI on PATH (warning only — needed for M4/M6),
  GROCERY_DB_PATH (optional; if set, file must exist). Exit 0 if no hard
  failures.

## 4. Check harness (`bootcamp_cli/checks.py`)

```python
@dataclass
class CheckResult:
    name: str          # rubric criterion id, e.g. "C3-no-iteration-cap"
    passed: bool
    detail: str        # what was observed; on failure NEVER the fix
    lesson_ref: str    # lesson.md section, e.g. "lesson.md §stop_reason"

@dataclass
class CheckContext:
    module_id: str
    workspace: Path    # labs/NN-name/workspace
    fixtures: Path     # curriculum/modules/NN-name/fixtures
    def run_learner(self, cmd: list[str], *, timeout: int = 120,
                    env: dict[str, str] | None = None,
                    stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        ...  # cwd=workspace, captured text output, no shell=True, kills on timeout
```

Discovery: every `check_*.py` file in the module's `checks/` dir is imported
(importlib, by path); every callable named `check_*` is invoked with a
CheckContext and must return `CheckResult | list[CheckResult]`. Checks run in
manifest file order, then definition order. An exception inside a check
becomes a failed CheckResult with detail `"check crashed: <exc>"` — the run
continues. Checks may import `bootcamp_cli` (it is installed). Checks never
write inside `workspace/`; temp artifacts go to a tempdir.

## 5. LLM judge (`bootcamp_cli/judge.py`)

```python
@dataclass
class Verdict:
    criterion: str
    passed: bool
    reasoning: str

def judge(criterion: str, rubric_excerpt: str, artifact: str) -> Verdict
```

Implementation requirements: `anthropic` SDK; model from env `JUDGE_MODEL`
default `claude-haiku-4-5`; temperature 0; max_tokens 1024; a single tool
`render_verdict` with input_schema
`{"criterion": str, "pass": bool, "reasoning": str}` and
`tool_choice={"type": "tool", "name": "render_verdict"}`; the verdict is read
from the tool_use block only — never parse free text. Raise `JudgeError` on
API failure; checks catch it and fail with "judge unavailable" detail.

## 6. Mentor (`bootcamp_cli/mentor.py`)

System prompt assembled per call from: the module's lab.md, the "Mentor
guardrails" section of rubric.md, and the latest check run report (if any).
Fixed instructions: teach via questions and pointers; never write the
learner's lab code; API-shape examples ≤5 lines allowed only if unrelated to
the specific solution; tie answers back to lesson sections. Model: env
`JUDGE_MODEL` default `claude-haiku-4-5`. History: prior `mentor_messages`
for the module, oldest first.

## 7. SQLite (`bootcamp_cli/db.py`)

Path from env `BOOTCAMP_DB`, default `./data/bootcamp.db` (create parent
dir). `row_factory = sqlite3.Row`, parameterised SQL only.

```sql
progress(module_id TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT 'locked',
         assisted INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL);
check_runs(id INTEGER PRIMARY KEY AUTOINCREMENT, module_id TEXT NOT NULL,
           ts TEXT NOT NULL, passed INTEGER NOT NULL, failed INTEGER NOT NULL,
           report_json TEXT NOT NULL);
hint_unlocks(module_id TEXT NOT NULL, level INTEGER NOT NULL, ts TEXT NOT NULL,
             PRIMARY KEY (module_id, level));
mentor_messages(id INTEGER PRIMARY KEY AUTOINCREMENT, module_id TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL, ts TEXT NOT NULL);
```

## 8. rubric.md required structure (curriculum-author MUST follow; the runner
and checker-builder parse these exact headings)

```markdown
# Rubric — NN module-name
## Criteria
1. **C1-slug** (deterministic|judge): <what is verified> — lesson_ref: <§>
...
## Hints
### Level 1
...conceptual nudge...
### Level 2
...names the mechanism...
### Level 3
...pseudocode shape...
## Mentor guardrails
- ...
## Reference solution sketch
...what `bootcamp solution` prints; enough shape to implement from, not a paste-able file...
```

`bootcamp hint` prints the matching `### Level N` body; `bootcamp solution`
prints the `## Reference solution sketch` body. Criterion ids (C1…Cn) are the
`CheckResult.name` values.

## 9. Fixture spec (fixtures-builder owns; document each in that module's
fixtures/README.md)

- **M1/M3/M8/M9 — mock support backend** (`fixtures/support_backend.py`,
  importable, stdlib only): in-process functions `get_customer(customer_id)`,
  `find_customers(name)` (M9 needs ambiguous duplicate names),
  `lookup_order(order_id)`, `process_refund(order_id, amount)`,
  `escalate_to_human(case_summary)`. Seeded deterministic data: ≥8 customers
  (two named "Alex Rivera" with different ids), ≥12 orders with 40+ fields
  each (ids, line items, shipping junk, internal flags), timestamps
  deliberately mixed Unix-epoch ints and ISO-8601 strings, statuses mixed
  case ("SHIPPED", "shipped", "Shipped"). `process_refund` records calls in a
  module-level log list (checkers inspect it) and raises `RefundError` above
  $1000 (hard backend cap; the M3 policy cap is $500 and must be enforced by
  the learner's hook, below the backend cap). One order priced exactly $700
  for the M3 adversarial test. An order priced $123.45 stated in a turn-3
  script line for M8's recall test.
- **M1/M8/M9 — scripted conversation drivers**
  (`fixtures/conversations.json`): named scripts of user turns with expected-
  outcome annotations. M1: a multi-concern message (refund status + address
  update). M8: 30 turns across 3 issues; turn 3 states an exact amount,
  turn 28 asks for it. M9: scenario battery — straightforward (no
  escalation), policy-gap (must escalate), explicit "give me a human"
  (immediate), ambiguous identity (clarify), subagent-timeout simulation.
- **M2 — research corpus** (`fixtures/corpus/*.md`): ~12 short documents on
  one broad topic spanning ≥4 clearly distinct sub-domains, plus
  `corpus_index.json` listing doc → sub-domain for the breadth check.
- **M4/M6 — sample monorepo** (`fixtures/sample-repo/`): a small messy
  monorepo (~15 files, 2 services + shared lib), test files deliberately
  scattered (`tests/`, `src/**/__tests__/`, `*_test.py` siblings), mixed
  conventions. For M6: 6 seeded bugs in specific files + 3 clean files;
  answer key at `fixtures/answer_key.json` (bug file/line/category) — the
  brief must tell the learner it exists but not its contents.
- **M7 — messy invoices** (`fixtures/invoices/*.txt`, 10 docs): informal
  measurements ("about two dozen"), absent fields (no invoice number, no
  date), one doc with line items summing ≠ stated total, one doc missing the
  required field entirely (the unretryable case), varied layouts.
  `fixtures/invoices_truth.json` = ground truth for checkers.
- **M5 — mock inventory DB** (`fixtures/inventory.sqlite3` + the script that
  generates it): products, stock_levels, suppliers tables, seeded rows
  including unicode names and zero-stock items (empty-result-≠-error probe).

All randomness seeded. No network. Nothing in fixtures imports anthropic.

## 10. Per-module learning objectives (verbatim; curriculum-author covers all)

- **01 agentic-loop**: loop lifecycle; stop_reason tool_use vs end_turn;
  appending tool results to history; model-driven tool selection vs hardcoded
  sequences; anti-patterns (text-parsing termination, iteration caps as
  primary stop, assistant-text-as-done)
- **02 multi-agent**: coordinator/subagent hub-and-spoke; Task spawning and
  allowedTools; isolated subagent context and explicit context passing;
  parallel dispatch in a single response; decomposition breadth vs narrow
  coverage; goals-and-quality-criteria prompts over step-by-step procedures
- **03 hooks**: PreToolUse-style interception for deterministic policy
  (refund cap → escalation redirect); PostToolUse normalization of
  heterogeneous formats; hooks-for-guarantees vs prompts-for-probabilistic;
  proving enforcement survives adversarial prompt edits
- **04 claude-code-config**: CLAUDE.md hierarchy user/project/directory;
  @import; .claude/rules/ YAML glob frontmatter vs directory CLAUDE.md;
  project vs user slash commands; skills frontmatter context: fork,
  allowed-tools, argument-hint; plan mode vs direct execution selection;
  /memory, /compact
- **05 mcp-server**: tools vs resources; description quality as the routing
  mechanism; splitting overlapping tools; structured errors
  isError/errorCategory/isRetryable; business vs transient vs validation vs
  permission; empty-result ≠ error; .mcp.json project scope with env-var
  expansion vs ~/.claude.json
- **06 cicd**: claude -p non-interactive; --output-format json +
  --json-schema; explicit categorical review criteria vs vague conservatism;
  false-positive cost to trust; dedup via prior-findings context; independent
  instance for review vs self-review; sync API for blocking checks vs Batches
  for overnight (50% cost, 24h window, custom_id, no multi-turn tools)
- **07 structured-output**: tool_use schemas for guaranteed syntax;
  tool_choice auto/any/forced; nullable fields prevent fabrication; enum +
  other/detail; few-shot for format variety and ambiguous cases;
  validation-retry with doc + failed output + specific error; recognising
  unretryable absence; semantic vs syntax validation (calculated vs stated
  totals, conflict_detected)
- **08 context-management**: persistent case-facts block outside summarised
  history; trimming tool outputs to relevant fields; lost-in-the-middle and
  position-aware ordering; scratchpads; structured handoff summaries
  (customer ID, root cause, amount, recommendation); structured data not
  prose between agents
- **09 capstone-reliability**: explicit escalation criteria with few-shot;
  honor explicit human requests immediately; policy-gap escalation; clarify
  on multiple matches vs heuristic pick; sentiment and self-confidence as bad
  proxies; structured error propagation with partial results and coverage
  annotation; independent-instance self-evaluation

## 11. Hard rules that apply to everyone (from CLAUDE.md)

Python 3.12, type hints everywhere, Typer, sqlite3 stdlib. Runner never edits
learner workspaces. Failure messages name criterion + lesson section, never
the fix. Anthropic calls mocked in tests/; curriculum checks/ may call the
real API. Files under 300 lines. Subprocess: timeout 120s, captured output,
no shell=True.
