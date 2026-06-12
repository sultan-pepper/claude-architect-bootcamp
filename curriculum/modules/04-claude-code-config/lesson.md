# Lesson 04 — Team-grade Claude Code config

Claude Code's behavior in a project is controlled by a stack of configuration files that load by context. Setting them up correctly means Claude applies the right conventions in the right place without being told every time. Getting them wrong means Claude either applies stale conventions everywhere or ignores them entirely.

## claude_md_hierarchy

CLAUDE.md files load from three levels and merge:

1. **User** (`~/.claude/CLAUDE.md`) — active in every project. Use it for personal conventions that follow you across machines: communication style, language preferences, tools you always want available.
2. **Project** (`<project-root>/CLAUDE.md`) — active across the entire repo. Use it for architectural constraints, protected paths, CI requirements, and naming conventions that the team owns.
3. **Directory** (`any/subdir/CLAUDE.md`) — active only when Claude is operating within that subtree. Use it for services with divergent standards or generated directories where normal conventions don't apply.

All three levels are active simultaneously when a directory-level file exists — they merge, they do not override. The same instruction at user and project level both apply.

`@import <relative-path>` inside any CLAUDE.md inlines the referenced file at that position. Use this to pull in architecture documents or lengthy standards without duplicating them:

```markdown
# API service conventions

@import ../../docs/api-design-standards.md
```

The path is relative to the importing file. Circular imports are an error. Imported content is indistinguishable from inline content once loaded.

## rules_and_glob_frontmatter

The `.claude/rules/` directory holds scoped convention files. Each file is Markdown with a YAML frontmatter block that declares which file paths it applies to:

```markdown
---
globs:
  - "tests/**/*.py"
  - "src/**/__tests__/*.py"
  - "src/**/*_test.py"
---
# Test-file conventions

Prefer pytest fixtures over setUp/tearDown. Mock all external I/O. Never assert on
log output text — assert on behaviour. Each test function names the scenario it covers.
```

When Claude opens or edits a file, it evaluates every `globs` list across all rules files. If the file's path matches any pattern in a file, that rules file loads into context for the current operation. Non-matching files don't load.

This is the mechanism for "test conventions apply only in test files" without requiring a CLAUDE.md in every test directory. A single rules file can scope across scattered test files that span multiple service directories.

Glob patterns: `**` matches zero or more path segments; `*` matches within one path segment. Patterns are evaluated against the path relative to the project root. Three conventions in one repo — `tests/*.py`, `src/**/__tests__/*.py`, `src/**/*_test.py` — require three separate patterns (or one file with three entries in the `globs` list).

The difference from directory CLAUDE.md: rules files scope by file-path pattern, not by physical directory. A single rules file can match files in `tests/`, `src/api/__tests__/`, and `src/worker/worker_test.py` in one frontmatter block. A directory CLAUDE.md can only match within its subtree.

## slash_commands

Slash commands are Markdown files that Claude Code runs as a prompt when invoked from the slash-command menu. Two scopes:

- **Project** (`.claude/commands/<name>.md`) — committed to the repo and available to everyone who clones it. Use for shared team workflows: generating PR summaries, running service-specific test scripts, listing API endpoints.
- **User** (`~/.claude/commands/<name>.md`) — available in all projects for that user only. Use for personal utilities that are not team-relevant.

A command file is a Markdown prompt. The user's arguments are available as `$ARGUMENTS`. A file named `summarise-changes.md` is invoked as `/summarise-changes [args]`.

The contents are sent to Claude as the initial user message for that command session. Write commands as complete instructions — Claude does not have additional context about what the command is for.

## skills

Skills extend slash commands with metadata that controls execution context and tool access:

```markdown
---
description: Analyse test coverage gaps for a given service
context: fork
allowed-tools:
  - Read
  - Bash
argument-hint: "<service-name>"
---
Run `pytest --cov=$ARGUMENTS --cov-report=term-missing` and identify the three functions
with the lowest coverage. For each, write a pytest test stub that covers the primary path.
```

Key frontmatter fields:

**`context: fork`** — runs the skill in an isolated context, forked from the current session. The skill can read broadly without polluting the main conversation's context window or decision history. Use `context: fork` for analysis and audit tasks that need broad file access but should not influence subsequent commands.

**`allowed-tools`** — restricts which tools Claude can use inside the skill. A read-only analysis skill should list `[Read]` only; a skill that runs tests can include `Bash`. This limits blast radius: a coverage analysis skill cannot accidentally commit code or push to remote.

**`argument-hint`** — displayed in the slash-command menu. Makes the expected argument visible without opening the file.

Skills are invoked identically to commands: `/skill-name [argument]`.

## plan_vs_direct

Claude Code has two modes for task execution:

**Plan mode** — Claude produces a step-by-step plan and waits for explicit approval before executing. Use plan mode when:

- The change spans multiple files or multiple services, and executing steps out of order causes problems (schema migration before code change, shared library before service code).
- The scope is ambiguous — plan mode surfaces Claude's interpretation before it acts on it.
- A wrong first step is expensive to reverse (deleted files, overwritten migrations, broken imports).

**Direct execution** — Claude proceeds without a planning pause. Use direct execution when:

- The scope fits in one sentence and there is no ambiguity about what needs changing.
- The change is in a single file with a clear, narrow edit.
- The task is repetitive and mechanical (rename a constant, add a type hint, insert a docstring).

The decision is about information density and reversal cost, not about risk-aversion in the abstract. Plan mode adds a round-trip for every task. On a one-liner it is pure overhead. On a cross-service refactor it prevents acting on a misunderstood scope.

The failure mode: treating plan mode as universally safer and enabling it for everything. This produces approval-clicking behavior — the developer stops reading the plans because they are always routine. When a genuinely ambiguous task arrives, the habit of approving without scrutiny causes the problem that plan mode was supposed to prevent.

In CLAUDE.md, you can set explicit thresholds: "Use plan mode for any change touching more than one service" or "For single-file changes under 20 lines, proceed directly without a planning step." Claude respects these when they are explicit.

## memory_compact

Two commands for managing Claude Code's context across a session:

**`/memory`** — opens the user CLAUDE.md for direct editing in the active session. Use it to persist decisions that emerged from the conversation: a naming convention the team just agreed on, a file layout decision, an architectural constraint that came up mid-task. Edits take effect immediately for the rest of the session and persist to all subsequent sessions.

**`/compact`** — summarises the current conversation into a condensed context block and discards the raw turn history. Claude retains the decisions and current state; the back-and-forth that led there is dropped. Effective use: compact after each logical sub-task is complete, so Claude carries the conclusion forward without replaying every file read.

The failure mode for `/compact`: running it mid-task when Claude has partially modified files. The summary may not carry sufficient detail to continue correctly — "modified three files" in a summary is not the same as having the actual diff in context. Compact at stable checkpoints: after a feature works, not while it is half-built.
