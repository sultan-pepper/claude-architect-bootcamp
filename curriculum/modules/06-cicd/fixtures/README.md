# M6 Fixtures Documentation

## sample-repo/ (with Seeded Bugs)

An **identical copy** of the M4 sample monorepo with 6 intentionally seeded bugs and 3 clean files. The structure and organization are identical to M4; only the bug content differs.

See `/home/kieran/Claude Cert/curriculum/modules/04-claude-code-config/fixtures/README.md` for full repo structure.

## Seeded Bugs

This fixture includes **6 real bugs** across specific files, designed to test code review and bug detection capabilities.

### Bug Categories

1. **Off-by-one error** — `src/worker-service/process.py:43`
   - Range calculation excludes the final batch
   
2. **Wrong comparison** — `src/worker-service/process.py:28`
   - Validating against incorrect field names
   
3. **Unhandled None** — `src/worker-service/process.py:61`
   - Calling .lower() on potentially None value
   
4. **Resource leak** — `src/api-service/main.py:30`
   - File descriptor opened but never closed
   
5. **Swallowed exception** — `src/api-service/main.py:68`
   - Exception caught but silently ignored
   
6. **Mutable default argument** — `src/worker-service/worker.py:33`
   - Dict default shared across function calls

## answer_key.json

Complete bug reference for checkers:

```json
{
  "bugs": [
    {
      "id": 1,
      "file": "src/worker-service/process.py",
      "line": 43,
      "category": "off-by-one",
      "description": "...",
      "current_code": "...",
      "correct_code": "..."
    },
    ...
  ],
  "clean_files": ["src/shared/__init__.py", "src/shared/utils.py", "config/config.py"]
}
```

Each bug entry includes:
- **id** — Bug identifier (1-6)
- **file** — Relative path from repo root
- **line** — Line number where bug appears
- **category** — Bug type (off-by-one, wrong-comparison, unhandled-none, resource-leak, swallowed-exception, mutable-default)
- **description** — Human-readable explanation
- **current_code** — The buggy code
- **correct_code** — What it should be

**clean_files** — List of files with no intentional bugs (3 files)

## Usage Notes

- **For learners:** The lab brief should mention that answer_key.json exists but not reveal its contents
- **For checkers:** Use answer_key.json to validate findings
- **Bug distribution:** Bugs span 3 files; 1 file has 3 bugs, 1 file has 2 bugs, 1 file has 1 bug
- **Severity:** Mix of obvious (resource leak) and subtle (mutable default) bugs

## Testing Notes

- Same structure as M4 for consistent project understanding
- All bugs are real and would cause issues in production
- Seeded bugs are deterministic (same across regenerations)
- Answer key provides ground truth for automated checking
