# Claude Code Configuration

## Project Overview

A Python monorepo containing two microservices (API service and worker service) and a shared utility library. The project uses pytest for testing with test files scattered across multiple locations.

## Language and Tooling

- **Python 3.12** with type hints throughout
- **pytest** for testing with coverage measurement
- **black** for code formatting
- **flake8** for linting
- **make** for common tasks

## Architectural Constraints

All API handlers must return a typed dictionary with consistent structure. Shared utilities must have no service-specific imports. Worker task processing must validate input before execution.

## Naming Conventions

Test files follow three conventions:
- Traditional: `tests/test_*.py`
- Embedded: `src/service/__tests__/test_*.py`
- Sibling: `src/service/*_test.py`
