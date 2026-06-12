"""Check harness: discovery, execution, and result collection."""

import subprocess
import tempfile
import threading
import importlib.util
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
import sys


class CheckTimeout(Exception):
    """Raised when learner code run in-process exceeds its time budget."""


def call_with_timeout(fn: Callable[..., Any], *args: Any,
                      timeout: float = 120.0, **kwargs: Any) -> Any:
    """Run fn in a daemon thread; raise CheckTimeout if it doesn't finish.

    Used by checks that import learner code in-process so a hung learner
    module cannot stall the harness. The daemon thread cannot be killed, but
    it will not block harness progress or process exit.
    """
    holder: dict[str, Any] = {}

    def _target() -> None:
        try:
            holder["result"] = fn(*args, **kwargs)
        except BaseException as exc:  # propagate learner exceptions faithfully
            holder["error"] = exc

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise CheckTimeout(f"learner code timed out after {timeout:.0f}s")
    if "error" in holder:
        raise holder["error"]
    return holder.get("result")


@dataclass
class CheckResult:
    """Result of a single check."""

    name: str  # Criterion id, e.g. "C3-no-iteration-cap"
    passed: bool
    detail: str  # What was observed; never the fix
    lesson_ref: str  # Lesson section, e.g. "lesson.md §stop_reason"


@dataclass
class CheckContext:
    """Context provided to checks."""

    module_id: str
    workspace: Path  # labs/NN-name/workspace
    fixtures: Path  # curriculum/modules/NN-name/fixtures

    def run_learner(
        self,
        cmd: list[str],
        *,
        timeout: int = 120,
        env: Optional[dict[str, str]] = None,
        stdin: Optional[str] = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a command in the learner's workspace.

        Returns CompletedProcess with captured text output.
        Raises subprocess.TimeoutExpired if timeout exceeded.
        """
        return subprocess.run(
            cmd,
            cwd=str(self.workspace),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            input=stdin
        )


def discover_checks(module_path: Path) -> list[tuple[str, Callable]]:
    """Discover all check_* functions in check_*.py files in module's checks/ dir.

    Returns list of (name, callable) tuples in manifest file order, then
    definition order within each file.
    """
    checks_dir = module_path / "checks"
    if not checks_dir.exists():
        return []

    check_files = sorted(checks_dir.glob("check_*.py"))
    discovered: list[tuple[str, Callable]] = []

    for check_file in check_files:
        # Load module dynamically
        spec = importlib.util.spec_from_file_location(
            f"check_{check_file.stem}", check_file
        )
        if not spec or not spec.loader:
            continue

        module = importlib.util.module_from_spec(spec)
        # Add curriculum to path so checks can import from curriculum
        sys.path.insert(0, str(check_file.parent.parent.parent.parent))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)

        # Find all callables named check_*
        for name, obj in inspect.getmembers(module):
            if name.startswith("check_") and callable(obj):
                discovered.append((name, obj))

    return discovered


def run_checks(
    module_path: Path, context: CheckContext
) -> list[CheckResult]:
    """Discover and run all checks for a module.

    Returns list of CheckResult objects. Exceptions in checks produce failed
    results with detail "check crashed: ...".
    """
    checks = discover_checks(module_path)
    results: list[CheckResult] = []

    for check_name, check_func in checks:
        try:
            # Call the check with context
            result = check_func(context)

            # Handle both single result and list of results
            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)

        except Exception as e:
            # Check crashed; create a failed result
            exc_str = f"{type(e).__name__}: {str(e)}"
            results.append(
                CheckResult(
                    name=check_name,
                    passed=False,
                    detail=f"check crashed: {exc_str}",
                    lesson_ref="N/A"
                )
            )

    return results
