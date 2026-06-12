"""Tests for workspace materialization."""

import json
from pathlib import Path

import pytest

from bootcamp_cli.modules import load_manifest, materialize_workspace


@pytest.fixture
def tmp_curriculum(tmp_path: Path) -> Path:
    """Create a synthetic curriculum with manifest and modules."""
    curriculum_dir = tmp_path / "curriculum"
    modules_dir = curriculum_dir / "modules"
    modules_dir.mkdir(parents=True)

    # Write manifest.json
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
        ]
    }

    manifest_path = curriculum_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    # Create module directories with structure
    mod_data = manifest["modules"][0]
    mod_dir = modules_dir / mod_data["dir"]
    mod_dir.mkdir(parents=True, exist_ok=True)
    (mod_dir / "lesson.md").write_text("Lesson content\n")
    (mod_dir / "lab.md").write_text("Lab content\n")
    (mod_dir / "rubric.md").write_text("Rubric content\n")

    # Add starter dir with a sample file
    starter_dir = mod_dir / "starter"
    starter_dir.mkdir(exist_ok=True)
    (starter_dir / "sample.py").write_text("# Sample starter file\n")

    return curriculum_dir


class TestWorkspaceMaterialization:
    """Test workspace materialization."""

    def test_materialize_workspace_creates_structure(
        self, tmp_curriculum: Path, tmp_path: Path
    ) -> None:
        """Test that materialize_workspace creates lab_dir and workspace."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        labs_root = tmp_path / "labs"

        lab_dir = materialize_workspace(modules[0], labs_root)

        assert lab_dir.exists()
        assert lab_dir.name == "01-agentic-loop"
        assert (lab_dir / "lesson.md").exists()
        assert (lab_dir / "lab.md").exists()
        assert (lab_dir / "workspace").exists()

    def test_materialize_copies_starter_files(
        self, tmp_curriculum: Path, tmp_path: Path
    ) -> None:
        """Test that starter files are copied to workspace."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        labs_root = tmp_path / "labs"

        materialize_workspace(modules[0], labs_root)

        workspace = labs_root / "01-agentic-loop" / "workspace"
        assert (workspace / "sample.py").exists()
        assert (workspace / "sample.py").read_text() == "# Sample starter file\n"

    def test_materialize_never_overwrites_workspace(
        self, tmp_curriculum: Path, tmp_path: Path
    ) -> None:
        """Test that existing workspace files are never overwritten."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        labs_root = tmp_path / "labs"

        # First call
        materialize_workspace(modules[0], labs_root)
        workspace_file = labs_root / "01-agentic-loop" / "workspace" / "sample.py"
        original_content = workspace_file.read_text()

        # Modify the file
        workspace_file.write_text("# Modified content\n")
        assert workspace_file.read_text() == "# Modified content\n"

        # Second call to materialize
        materialize_workspace(modules[0], labs_root)

        # File should not be overwritten
        assert workspace_file.read_text() == "# Modified content\n"

    def test_materialize_overwrites_lesson_lab_files(
        self, tmp_curriculum: Path, tmp_path: Path
    ) -> None:
        """Test that lesson.md and lab.md are updated on re-materialize."""
        manifest_path = tmp_curriculum / "manifest.json"
        modules = load_manifest(manifest_path)
        labs_root = tmp_path / "labs"

        # First call
        materialize_workspace(modules[0], labs_root)
        lab_dir = labs_root / "01-agentic-loop"

        # Modify lesson.md
        (lab_dir / "lesson.md").write_text("# Modified lesson\n")

        # Update the source
        source_lesson = tmp_curriculum / "modules" / "01-agentic-loop" / "lesson.md"
        source_lesson.write_text("# Updated lesson\n")

        # Re-materialize
        materialize_workspace(modules[0], labs_root)

        # lesson.md should be updated
        assert (lab_dir / "lesson.md").read_text() == "# Updated lesson\n"

    def test_materialize_empty_starter_creates_empty_workspace(
        self, tmp_path: Path
    ) -> None:
        """Test that empty workspace is created if no starter dir exists."""
        curriculum_dir = tmp_path / "curriculum"
        modules_dir = curriculum_dir / "modules"
        modules_dir.mkdir(parents=True)

        manifest = {
            "modules": [
                {
                    "id": "01",
                    "dir": "01-empty",
                    "name": "empty",
                    "title": "Empty module",
                    "track": "A",
                    "depends_on": [],
                }
            ]
        }

        manifest_path = curriculum_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest))

        mod_dir = modules_dir / "01-empty"
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "lesson.md").write_text("Lesson\n")
        (mod_dir / "lab.md").write_text("Lab\n")
        (mod_dir / "rubric.md").write_text("Rubric\n")
        # No starter dir

        modules = load_manifest(manifest_path)
        labs_root = tmp_path / "labs"
        lab_dir = materialize_workspace(modules[0], labs_root)

        workspace = lab_dir / "workspace"
        assert workspace.exists()
        assert len(list(workspace.iterdir())) == 0
