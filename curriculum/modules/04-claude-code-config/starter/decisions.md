# Plan vs Direct Execution — Decisions

## Task A

Task: Migrate both services from synchronous request handling to `asyncio`. This change
touches `src/api-service/main.py`, `src/worker-service/worker.py`,
`src/worker-service/process.py`, and `src/shared/utils.py`, and requires updating the
test files to use `pytest-asyncio`.

**Decision:**
<!-- TODO: state "plan mode" or "direct execution" -->

**Justification:**
<!-- TODO: explain why. Name the specific characteristics of Task A that drove your
     decision. What would go wrong if you chose the other mode? -->

## Task B

Task: Change the default log level in `config/config.py` from `"INFO"` to `"WARNING"`
inside `DevelopmentConfig`. One file, one line.

**Decision:**
<!-- TODO: state "plan mode" or "direct execution" -->

**Justification:**
<!-- TODO: explain why. What characteristic of Task B makes this mode the right choice? -->
