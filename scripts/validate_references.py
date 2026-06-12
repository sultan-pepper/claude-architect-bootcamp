"""Acceptance: install each module's reference solution and run its checks.

Usage:  python scripts/validate_references.py [NN ...]
        (default: all nine modules)

Without ANTHROPIC_API_KEY only the static/protocol checks can pass; checks
that execute live agents or the judge report "requires ANTHROPIC_API_KEY".
With the key set, every check should pass for every module.

Uses a throwaway DB and rebuilds labs/NN-name/workspace from scratch each
run. Learner workspaces in labs/ are DELETED for the modules validated —
do not run this against labs you care about.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = json.loads((ROOT / "curriculum" / "manifest.json").read_text())["modules"]
BOOTCAMP = ROOT / ".venv" / "bin" / "bootcamp"


def install_reference(mod: dict[str, str]) -> Path:
    """Copy the module's reference solution into a fresh lab workspace."""
    module_dir = ROOT / "curriculum" / "modules" / mod["dir"]
    ref = module_dir / "checks" / "reference_solution"
    lab = ROOT / "labs" / mod["dir"]
    workspace = lab / "workspace"
    if lab.exists():
        shutil.rmtree(lab)
    workspace.mkdir(parents=True)

    if mod["id"] == "04":
        repo = workspace / "sample-repo"
        shutil.copytree(module_dir / "fixtures" / "sample-repo", repo)
        shutil.copy(ref / "CLAUDE.md", repo / "CLAUDE.md")
        for sub, name in (("rules", "test-conventions.md"),
                          ("commands", "summarise-service.md"),
                          ("skills", "coverage-gaps.md")):
            dest = repo / ".claude" / sub
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy(ref / name, dest / name)
        shutil.copy(ref / "decisions.md", workspace / "decisions.md")
    else:
        for item in ref.iterdir():
            if item.name == "__pycache__":
                continue
            if item.is_dir():
                shutil.copytree(item, workspace / item.name)
            else:
                shutil.copy(item, workspace / item.name)
    return workspace


def main() -> int:
    wanted = set(sys.argv[1:]) or {m["id"] for m in MODULES}
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["BOOTCAMP_DB"] = str(Path(tmp) / "acceptance.db")
        for mod in MODULES:
            if mod["id"] not in wanted:
                continue
            install_reference(mod)
            print(f"\n=== module {mod['id']} ({mod['name']}) ===")
            proc = subprocess.run(
                [str(BOOTCAMP), "check", "--module", mod["id"]],
                cwd=ROOT, env=env, capture_output=True, text=True)
            print(proc.stdout.strip())
            if proc.stderr.strip():
                print(proc.stderr.strip(), file=sys.stderr)
            if proc.returncode != 0:
                failures += 1
    print(f"\n{'ALL MODULES PASSED' if failures == 0 else f'{failures} module(s) had failing checks'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
