---
paths: ["bootcamp_cli/**/*.py", "curriculum/**/checks/**/*.py", "tests/**/*.py"]
---
- Checks are plain functions returning CheckResult(name, passed, detail, lesson_ref);
  the harness in bootcamp_cli/checks.py discovers and runs them
- LLM-judge calls go through bootcamp_cli/judge.py only: tool_use with a verdict
  schema {criterion, pass, reasoning}; temperature 0; never free-text parsing
- Subprocess execution of learner code: timeout 120s, captured output, no shell=True
- Parameterised SQL only; row_factory = sqlite3.Row
