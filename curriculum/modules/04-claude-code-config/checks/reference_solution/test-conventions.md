---
globs:
  - "tests/*.py"
  - "src/api-service/__tests__/*.py"
  - "src/worker-service/*_test.py"
---

# Test File Conventions

## Fixture Usage

Use pytest fixtures for setup and teardown. Avoid module-level setup that affects test independence.

## Mocking Requirements

Mock external service calls and file I/O. Tests must not depend on network availability or filesystem state.

## Assertions

Do not assert on log text. Verify behavior through return values and state changes instead.

## Test Function Naming

Follow the pattern `test_<function>_<scenario>`, matching the actual code's naming convention (snake_case for functions).
