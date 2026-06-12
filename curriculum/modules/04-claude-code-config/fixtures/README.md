# M4 Fixtures Documentation

## sample-repo/

A small Python monorepo (~15 files) demonstrating team-scale code organization with two services and a shared library. This is the **canonical bug-free version**; M6 contains an identical copy with 6 seeded bugs.

### Repository Structure

```
sample-repo/
├── src/
│   ├── shared/                      # Shared library
│   │   ├── __init__.py
│   │   └── utils.py                 # Utility functions
│   ├── api-service/                 # REST API service
│   │   ├── __init__.py
│   │   ├── main.py                  # API server implementation
│   │   └── __tests__/
│   │       └── test_main.py          # Embedded test file
│   └── worker-service/              # Background worker service
│       ├── __init__.py
│       ├── worker.py                # Worker implementation
│       ├── process.py               # Task processing logic
│       └── worker_test.py            # Sibling test file
├── tests/                           # Integration tests
│   ├── conftest.py
│   ├── test_integration.py
│   └── test_shared_utils.py
├── config/
│   └── config.py                    # Configuration management
├── requirements.txt
├── Makefile
└── README.md
```

### File Descriptions

**Shared Library (`src/shared/utils.py`)**
- `parse_json(data: str) -> dict` — JSON parsing
- `format_error(code: int, message: str) -> dict` — Error formatting
- `validate_email(email: str) -> bool` — Email validation
- `calculate_total(items: list[float]) -> float` — Sum calculation
- `retry_exponential(func, max_retries=3)` — Retry decorator

**API Service (`src/api-service/main.py`)**
- `APIServer` class with `start()`, `stop()`, `handle_request()` methods
- Handles GET /health and POST /users endpoints
- Request counter tracking

**Worker Service (`src/worker-service/worker.py`)**
- `Worker` class with `start()`, `stop()`, `process_task()`, `get_stats()` methods
- Simulates background task processing

**Task Processing (`src/worker-service/process.py`)**
- `parse_task(task_json: str)` — Parse task from JSON
- `validate_task(task: dict) -> bool` — Validation (requires "id", "type", "payload" fields)
- `batch_tasks(tasks: list, batch_size=10)` — Group tasks
- `calculate_priority(task: dict) -> int` — Priority scoring

### Deliberate Messiness

Test files are scattered across multiple locations to exercise code discovery:
- `src/api-service/__tests__/test_main.py` — Embedded in service directory
- `src/worker-service/worker_test.py` — Sibling file with _test suffix
- `tests/conftest.py`, `tests/test_*.py` — Traditional test directory

Mixed naming conventions:
- `__tests__/` (JS/TS convention)
- `*_test.py` (Go convention)
- `tests/` (Python convention)

### Configuration

`config/config.py` provides `Config` class with environment-based profiles:
- Base settings: DEBUG, API_HOST, API_PORT, WORKER_THREADS, LOG_LEVEL
- DevelopmentConfig with DEBUG=True
- ProductionConfig with DEBUG=False
- `get_config(env)` factory function

### Build/Test

Makefile provides standard targets:
- `make install` — Install dependencies
- `make test` — Run pytest with coverage
- `make lint` — Run flake8
- `make format` — Run black
- `make clean` — Remove artifacts

---

## Testing Notes

- No external dependencies beyond test frameworks (pytest, black, flake8)
- All Python code is type-hinted
- Files deliberately kept under 300 lines (per spec)
- Monorepo structure tests Claude Code's file discovery and project understanding
