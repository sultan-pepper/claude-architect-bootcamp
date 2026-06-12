"""Bootcamp CLI main app and command definitions."""

from typing import Optional
import typer
from bootcamp_cli.commands import (
    cmd_status,
    cmd_next,
    cmd_check,
    cmd_hint,
    cmd_mentor,
    cmd_solution,
)
from bootcamp_cli.doctor import cmd_doctor

app = typer.Typer()


@app.command()
def status(json_output: bool = typer.Option(False, "--json")) -> None:
    """Show progress across all modules. Exit 0 always."""
    cmd_status(json_output)


@app.command(name="next")
def next_module(module: Optional[str] = typer.Option(None, "-m", "--module")) -> None:
    """Start the next available module. Exit 0 on success, 1 if locked, 2 on error."""
    cmd_next(module)


@app.command()
def check(
    module: Optional[str] = typer.Option(None, "-m", "--module"),
    json_output: bool = typer.Option(False, "--json")
) -> None:
    """Run checks. Exit 0 all pass, 1 if any fail, 2 on error."""
    cmd_check(module, json_output)


@app.command()
def hint(module: Optional[str] = typer.Option(None, "-m", "--module")) -> None:
    """Print next hint level. Exit 0 if printed, 1 if gated, 2 on error."""
    cmd_hint(module)


@app.command()
def mentor(
    question: str = typer.Argument(...),
    module: Optional[str] = typer.Option(None, "-m", "--module")
) -> None:
    """Chat with mentor. Exit 0 on success, 2 on API error."""
    cmd_mentor(question, module)


@app.command()
def solution(module: Optional[str] = typer.Option(None, "-m", "--module")) -> None:
    """Print reference solution. Exit 0 on success, 1 if gated, 2 on error."""
    cmd_solution(module)


@app.command()
def doctor() -> None:
    """Verify system setup. Exit 0 if no hard failures."""
    cmd_doctor()


if __name__ == "__main__":
    app()
