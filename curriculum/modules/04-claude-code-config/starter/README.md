# M04 workspace — Team-grade Claude Code config

## Setup

Copy the fixture repo into your workspace before starting:

```bash
cp -r ../../../curriculum/modules/04-claude-code-config/fixtures/sample-repo ./sample-repo
```

This gives you `workspace/sample-repo/` — the monorepo you will configure.

## Deliverables

All Claude Code config files live **inside** `workspace/sample-repo/`:

| Path | Description |
|---|---|
| `sample-repo/CLAUDE.md` | Project-level CLAUDE.md |
| `sample-repo/.claude/rules/<name>.md` | At least one rules file with glob frontmatter |
| `sample-repo/.claude/commands/<name>.md` | At least one project slash command |
| `sample-repo/.claude/skills/<name>.md` | At least one skill with `context: fork` |

One file lives **at the workspace root** (one level above `sample-repo/`):

| Path | Description |
|---|---|
| `decisions.md` | Plan vs direct execution justification for Task A and Task B |

A skeleton `decisions.md` is provided in this workspace — fill in the two sections.

## Checks

```bash
bootcamp check    # runs C1–C7; C7 skipped without claude CLI + API key
bootcamp hint     # unlock hints one level at a time (requires a failed check run first)
```

## Test file paths to cover (C3)

Your glob patterns must collectively match all five:

- `tests/test_shared_utils.py`
- `tests/conftest.py`
- `tests/test_integration.py`
- `src/api-service/__tests__/test_main.py`
- `src/worker-service/worker_test.py`

Verify patterns with `pathlib.Path.glob` before submitting.
