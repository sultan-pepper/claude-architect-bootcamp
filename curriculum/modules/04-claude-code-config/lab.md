# Lab 04 — Team-grade Claude Code config

## Mission

Configure the provided sample monorepo for team-grade Claude Code usage. The repo uses three different test-file naming conventions scattered across the directory tree. Your task is to wire up Claude Code configuration so it applies the right conventions in the right context — glob-scoped rules for the test files, a project slash command, a skill with restricted tool access, and a written justification of when plan mode is appropriate versus direct execution.

## Workspace setup

`bootcamp next` copies the starter into your workspace. From there:

```bash
cd labs/04-claude-code-config/workspace
cp -r ../../../curriculum/modules/04-claude-code-config/fixtures/sample-repo ./sample-repo
```

All Claude Code deliverables live inside `workspace/sample-repo/`. The `decisions.md` deliverable lives at `workspace/decisions.md` (one level up from the repo).

## Deliverables

### 1. `workspace/sample-repo/CLAUDE.md`

Project-level CLAUDE.md at the repo root. Must be non-empty. Include at minimum: the project's language and structure, at least one architectural constraint or naming convention relevant to the actual code (read the source — this is real Python).

### 2. `workspace/sample-repo/.claude/rules/<name>.md`

One or more rules files with YAML glob frontmatter. The glob patterns across all your rules files must collectively match every test file in the repo:

- `tests/test_shared_utils.py`
- `tests/conftest.py`
- `tests/test_integration.py`
- `src/api-service/__tests__/test_main.py`
- `src/worker-service/worker_test.py`

Required frontmatter format:

```markdown
---
globs:
  - "tests/**/*.py"
  - "src/**/__tests__/*.py"
  - "src/**/*_test.py"
---
```

The patterns above are a hint — adapt them to actually match the paths above. The rules body must be substantive: conventions that would genuinely apply when editing test files in this repo.

### 3. `workspace/sample-repo/.claude/commands/<name>.md`

At least one project slash command. Name it something useful for this repo. Write a prompt that performs a real task — generating an endpoint summary, describing a service's responsibilities, or producing a PR description template. Placeholder text fails C4.

### 4. `workspace/sample-repo/.claude/skills/<name>.md`

At least one skill file with this exact frontmatter (values may vary; the keys are required):

```markdown
---
context: fork
allowed-tools:
  - Read
  - Bash
argument-hint: "<service-name>"
---
```

`context: fork` and `allowed-tools` are required keys. `allowed-tools` must be a non-empty list. `argument-hint` is required (any non-empty string). The skill body must describe a real workflow.

### 5. `workspace/decisions.md`

A written justification for two tasks. For each task, state whether you would invoke Claude Code in plan mode or direct execution, and explain why. The checker parses for the exact headings `## Task A` and `## Task B`.

**Task A**: Migrate both services from synchronous to `asyncio`. The change touches `src/api-service/main.py`, `src/worker-service/worker.py`, `src/worker-service/process.py`, and `src/shared/utils.py`, and requires updating the test files to use `pytest-asyncio`.

**Task B**: Change the default log level in `config/config.py` from `"INFO"` to `"WARNING"` inside `DevelopmentConfig`. One file, one line.

Required format:

```markdown
## Task A
[your decision and justification]

## Task B
[your decision and justification]
```

There is a defensible correct answer for each. Justify from the characteristics of the task, not from a general preference.

## Fixtures available

`fixtures/sample-repo/` is a small Python monorepo with two services and a shared library:

```
src/
  api-service/main.py, __init__.py, __tests__/test_main.py
  worker-service/worker.py, process.py, __init__.py, worker_test.py
  shared/utils.py, __init__.py
config/config.py
tests/conftest.py, test_integration.py, test_shared_utils.py
Makefile, requirements.txt
```

The repo is clean (no intentional bugs). Read the code before writing rules — your conventions should reflect what is actually there.

## What `bootcamp check` does

1. **C1-claudemd-exists**: verifies `workspace/sample-repo/CLAUDE.md` exists and contains more than 10 characters.

2. **C2-rules-frontmatter-valid**: verifies at least one `.md` file exists under `workspace/sample-repo/.claude/rules/` with a valid YAML frontmatter block (content between `---` delimiters) containing a `globs` key with a non-empty list.

3. **C3-globs-cover-tests**: expands every glob pattern from all rules files against the actual file tree under `workspace/sample-repo/` using `fnmatch` and verifies all five test file paths are matched. The checker reports which path was missed if the check fails.

4. **C4-command-exists**: verifies at least one `.md` file exists in `workspace/sample-repo/.claude/commands/` with more than 10 characters of content.

5. **C5-skill-frontmatter**: verifies at least one `.md` file in `workspace/sample-repo/.claude/skills/` has valid YAML frontmatter containing `context: fork` and an `allowed-tools` key with a non-empty list.

6. **C6-decisions-defensible** (judge): reads `workspace/decisions.md`, confirms both `## Task A` and `## Task B` sections are present, then passes each section to the judge for evaluation. The judge assesses whether each decision is defensible given the task's scope and reversibility characteristics.

7. **C7-claude-p-conventions** (skipped without `claude` CLI on PATH and `ANTHROPIC_API_KEY` set): invokes `claude -p "list the test files in this project"` inside `workspace/sample-repo/` and verifies the response references all three test-file locations. This confirms glob-scoped rules loaded correctly. If `claude` is not on PATH or the API key is missing, this check is skipped with status `SKIP` and does not affect pass/fail.

## Acceptance criteria

C1 through C6 must all pass. C7 is advisory (SKIP counts as pass).

The judge for C6 uses the rubric's criterion description, not a fixed answer key. A decision is defensible if it correctly identifies the scope and reversal risk of the task and maps them to the appropriate mode. Fence-sitting ("it depends") without stating the determining factors fails.
