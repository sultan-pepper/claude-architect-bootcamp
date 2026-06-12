# Rubric — 04 claude-code-config

## Criteria

1. **C1-claudemd-exists** (deterministic): `workspace/sample-repo/CLAUDE.md` exists and contains more than 10 bytes of content — lesson_ref: lesson.md §claude_md_hierarchy

2. **C2-rules-frontmatter-valid** (deterministic): at least one `.md` file under `workspace/sample-repo/.claude/rules/` contains a valid YAML frontmatter block (between `---` delimiters) with a `globs` key whose value is a non-empty list — lesson_ref: lesson.md §rules_and_glob_frontmatter

3. **C3-globs-cover-tests** (deterministic): the union of all `globs` list entries across all rules files, matched via `fnmatch` against the repo's actual file tree, covers all five expected test paths (`tests/test_shared_utils.py`, `tests/conftest.py`, `tests/test_integration.py`, `src/api-service/__tests__/test_main.py`, `src/worker-service/worker_test.py`) — lesson_ref: lesson.md §rules_and_glob_frontmatter

4. **C4-command-exists** (deterministic): at least one `.md` file exists in `workspace/sample-repo/.claude/commands/` with more than 10 characters of body content — lesson_ref: lesson.md §slash_commands

5. **C5-skill-frontmatter** (deterministic): at least one `.md` file in `workspace/sample-repo/.claude/skills/` has valid YAML frontmatter containing `context: fork` (exact string) and an `allowed-tools` key whose value is a non-empty list — lesson_ref: lesson.md §skills

6. **C6-decisions-defensible** (judge): `workspace/decisions.md` contains both `## Task A` and `## Task B` headings; the judge evaluates each section against the criterion: "The decision (plan mode or direct execution) is correctly matched to the task's scope and reversal risk, and the justification names the deciding factor (multi-file scope and ordering dependency → plan mode; single-file, single-line, unambiguous → direct execution)" — lesson_ref: lesson.md §plan_vs_direct

7. **C7-claude-p-conventions** (judge, skipped without `claude` CLI and `ANTHROPIC_API_KEY`): `claude -p "list the test files in this project"` run inside `workspace/sample-repo/` produces output referencing all three test-file locations — lesson_ref: lesson.md §rules_and_glob_frontmatter

## Hints

### Level 1

The checks inspect two distinct layers: the YAML frontmatter block at the top of each rules file, and whether the glob patterns in that block actually match the test file paths in the repo. A rules file that has correct YAML but patterns that don't match the actual paths will fail C3 even if it passes C2. Check both layers separately.

### Level 2

For C3: `fnmatch` is used to expand the patterns. The pattern `tests/**/*.py` in Python's `fnmatch` does not behave the same as shell globbing — `**` is not recursive in `fnmatch`. Use `pathlib.Path.rglob` semantics or write patterns that match the exact path structure. For the three layouts in this repo the patterns `tests/*.py`, `src/**/__tests__/*.py`, and `src/**/*_test.py` cover all five paths when expanded with `pathlib.Path.glob` (which does support `**`). Verify your patterns against the actual paths listed in lab.md before submitting.

For C5: the frontmatter must contain `context: fork` as a scalar string value (not a list). `allowed-tools` must be a YAML list (one item per line with `- ` prefix). A dict or a scalar string for `allowed-tools` fails the check.

For C6: the judge is looking for a clear statement of the deciding factor, not for agreement with any particular decision. The relevant factors: Task A touches five files across two services and has ordering dependencies; Task B touches one file, one line, and has no dependencies. Map those characteristics to the mode and say so.

### Level 3

Rules file structure that satisfies C2 and C3:

```markdown
---
globs:
  - "tests/*.py"
  - "src/api-service/__tests__/*.py"
  - "src/worker-service/*_test.py"
---
# Test conventions for this repo
...body...
```

Skill file structure that satisfies C5:

```markdown
---
context: fork
allowed-tools:
  - Read
  - Bash
argument-hint: "<service-name>"
---
...body...
```

decisions.md structure that allows C6 to run:

```markdown
## Task A

Plan mode. Task A requires modifying five files across two services and the shared
library, with an ordering constraint (shared library before service code, service code
before tests). An error in the shared library propagates to both services; executing
without a plan risks partial migration that leaves the repo in a non-runnable state.

## Task B

Direct execution. Task B is a one-line change in one file with no dependencies.
The scope is unambiguous; there is no ordering constraint; reversal is a single undo.
Plan mode adds a round-trip with no benefit here.
```

## Mentor guardrails

- Do not write the CLAUDE.md, rules files, commands, or skills for the learner.
- If the learner asks whether a particular glob pattern will match a specific path, direct them to test it with `pathlib.Path.glob` in a Python REPL rather than confirming or denying.
- If the learner asks whether their decisions.md will pass C6, do not reveal the judge's rubric text. Ask: "What is the deciding characteristic of Task A that is absent from Task B?"
- If the learner asks what frontmatter fields are required for a skill, point to lesson.md §skills and ask them to list the three frontmatter keys described there.
- Do not reveal which specific frontmatter parsing code the checker uses (YAML library, key existence checks).
- The C7 check is advisory — do not encourage the learner to prioritise it over C1–C6.

## Reference solution sketch

**`CLAUDE.md`**: Two to four sections. Project overview (Python monorepo, two services, shared lib). Language and tooling (Python 3.12, pytest, black, flake8). At least one architectural constraint ("all API handlers must return a typed dict", "shared utils must have no service-specific imports"). One naming convention.

**`.claude/rules/test-conventions.md`**: Frontmatter with three patterns: `tests/*.py`, `src/api-service/__tests__/*.py`, `src/worker-service/*_test.py`. Body: pytest fixture preference, mock-IO requirement, no log-text assertions, test function naming convention (matches the real code's style).

**`.claude/commands/summarise-service.md`**: A prompt that lists the public functions and HTTP endpoints for `$ARGUMENTS` service, referencing the actual file paths. Example: "Read `src/$ARGUMENTS/main.py`. List all HTTP endpoints (method, path, handler function). List all public functions with their signatures. Summarise the service's responsibilities in two sentences."

**`.claude/skills/coverage-gaps.md`**: Frontmatter: `context: fork`, `allowed-tools: [Read, Bash]`, `argument-hint: "<service-name>"`. Body: runs pytest with coverage for the service, parses the output, lists uncovered functions.

**`decisions.md`**: Task A → plan mode; argument: five files, ordering dependency, partial migration leaves repo broken. Task B → direct execution; argument: one file, one line, no dependencies, unambiguous scope, trivially reversible.
