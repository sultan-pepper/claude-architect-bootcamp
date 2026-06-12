"""Tests for module manifest loading."""

import json
from pathlib import Path

import pytest

from bootcamp_cli.modules import load_manifest


@pytest.fixture
def tmp_curriculum(tmp_path: Path) -> Path:
    """Create a synthetic curriculum with manifest and modules."""
    curriculum_dir = tmp_path / "curriculum"
    modules_dir = curriculum_dir / "modules"
    modules_dir.mkdir(parents=True)

    manifest = {
        "modules": [
            {
                "id": "01",
                "dir": "01-agentic-loop",
                "name": "agentic-loop",
                "title": "The agentic loop",
                "track": "A",
                "depends_on": [],
            },
            {
                "id": "02",
                "dir": "02-multi-agent",
                "name": "multi-agent",
                "title": "Multi-agent orchestration",
                "track": "A",
                "depends_on": ["01"],
            },
            {
                "id": "03",
                "dir": "03-hooks",
                "name": "hooks",
                "title": "Hooks and lifecycle",
                "track": "A",
                "depends_on": ["01"],
            },
            {
                "id": "04",
                "dir": "04-claude-code-config",
                "name": "claude-code-config",
                "title": "Team-grade Claude Code config",
                "track": "B",
                "depends_on": [],
            },
            {
                "id": "07",
                "dir": "07-structured-output",
                "name": "structured-output",
                "title": "Structured output & extraction",
                "track": "C",
                "depends_on": [],
            },
            {
                "id": "09",
                "dir": "09-capstone-reliability",
                "name": "capstone-reliability",
                "title": "Capstone — escalation & reliability",
                "track": "C",
                "depends_on": ["02", "03"],
            },
        ]
    }

    manifest_path = curriculum_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    for mod_data in manifest["modules"]:
        mod_dir = modules_dir / mod_data["dir"]
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "lesson.md").write_text(f"Lesson for {mod_data['name']}\n")
        (mod_dir / "lab.md").write_text(f"Lab for {mod_data['name']}\n")
        (mod_dir / "rubric.md").write_text(f"Rubric for {mod_data['name']}\n")

        starter_dir = mod_dir / "starter"
        starter_dir.mkdir(exist_ok=True)
        (starter_dir / "sample.py").write_text("# Sample starter file\n")

    return curriculum_dir


class TestModuleManifestLoading:
    """Test loading and parsing the manifest."""

    def test_load_manifest(self, tmp_curriculum: Path) -> None:
        """Test that manifest loads correctly."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)

        assert len(modules) == 6
        assert modules[0].id == "01"
        assert modules[0].name == "agentic-loop"
        assert modules[0].track == "A"
        assert modules[0].depends_on == []

        assert modules[1].id == "02"
        assert modules[1].depends_on == ["01"]

        assert modules[5].id == "09"
        assert modules[5].depends_on == ["02", "03"]

    def test_manifest_module_paths(self, tmp_curriculum: Path) -> None:
        """Test that module paths are correctly resolved."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)

        assert modules[0].path == tmp_curriculum / "modules" / "01-agentic-loop"
        assert modules[0].path.exists()
        assert (modules[0].path / "lesson.md").exists()

    def test_manifest_track_fields(self, tmp_curriculum: Path) -> None:
        """Test that all module fields are loaded."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)

        mod = modules[0]
        assert hasattr(mod, "id")
        assert hasattr(mod, "dir")
        assert hasattr(mod, "name")
        assert hasattr(mod, "title")
        assert hasattr(mod, "track")
        assert hasattr(mod, "depends_on")
        assert hasattr(mod, "path")

    def test_manifest_dependency_chain(self, tmp_curriculum: Path) -> None:
        """Test that dependencies are correctly parsed."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)

        # 09 depends on 02 and 03
        capstone = next((m for m in modules if m.id == "09"), None)
        assert capstone is not None
        assert set(capstone.depends_on) == {"02", "03"}
