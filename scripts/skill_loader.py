"""Skill loader for Problem-Based SRS skills.

Supports loading skills from:
1. GitHub repository (default - ensures latest version)
2. Local file system (override via SKILL_DIR for development)

By default, skills are cloned from GitHub to a temporary folder at test
setup time to ensure we're always testing against the latest published version.
Set SKILL_DIR environment variable to point to a local folder for development.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Default GitHub repository (always used unless SKILL_DIR is set)
DEFAULT_GITHUB_REPO = "https://github.com/RafaelGorski/Problem-Based-SRS"

# Skills available in the repository
AVAILABLE_SKILLS = [
    "customer-problems",
    "software-glance",
    "customer-needs",
    "software-vision",
    "functional-requirements",
    "zigzag-validator",
    "complexity-analysis",
    "problem-based-srs",
]


@dataclass
class SkillInfo:
    """Information about a loaded skill."""

    name: str
    path: Path
    skill_md_path: Path
    command: str
    description: str = ""
    version: str = ""


class SkillLoader:
    """Load skills from GitHub or local path.
    
    Default behavior: Clone from GitHub to ensure latest version.
    Override: Set SKILL_DIR env var to use a local folder instead.
    """

    def __init__(
        self,
        source: str | None = None,
        use_local: bool | None = None,
    ):
        """Initialize the skill loader.

        Args:
            source: Path or URL to skills. If None, uses environment.
            use_local: If True, use local path. If False, clone from GitHub.
                      If None, auto-detected: uses local if SKILL_DIR is set,
                      otherwise clones from GitHub (default).
        """
        # Check if SKILL_DIR is set - if so, use local mode
        local_dir = os.environ.get("SKILL_DIR")
        
        if use_local is None:
            # Default: use GitHub unless SKILL_DIR is explicitly set
            use_local = local_dir is not None

        if source is None:
            if use_local:
                if local_dir is None:
                    raise ValueError(
                        "use_local=True but SKILL_DIR environment variable is not set"
                    )
                source = local_dir
            else:
                source = os.environ.get("SKILL_REPO", DEFAULT_GITHUB_REPO)

        self.source = source
        self.use_local = use_local
        self._skill_dir: Path | None = None
        self._temp_dir: tempfile.TemporaryDirectory | None = None

    @property
    def skill_dir(self) -> Path:
        """Get the skills directory path."""
        if self._skill_dir is None:
            raise RuntimeError("Skills not loaded. Call load() first.")
        return self._skill_dir

    def load(self) -> Path:
        """Load skills from source.

        Returns:
            Path to the skills directory.
        """
        if self.use_local:
            self._skill_dir = Path(self.source)
            if not self._skill_dir.exists():
                raise FileNotFoundError(f"Local skill directory not found: {self.source}")
        else:
            self._clone_from_github()

        return self._skill_dir

    def _clone_from_github(self) -> None:
        """Clone skills repository from GitHub."""
        self._temp_dir = tempfile.TemporaryDirectory(prefix="pbsrs_skills_")
        clone_path = Path(self._temp_dir.name)

        subprocess.run(
            ["git", "clone", "--depth", "1", self.source, str(clone_path)],
            check=True,
            capture_output=True,
        )

        self._skill_dir = clone_path

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
            self._skill_dir = None

    def __enter__(self) -> SkillLoader:
        """Context manager entry."""
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.cleanup()

    def get_skill_path(self, skill_name: str) -> Path:
        """Get the path to a specific skill.

        Args:
            skill_name: Name of the skill (e.g., "customer-problems").

        Returns:
            Path to the skill directory.
        """
        skill_path = self.skill_dir / "skills" / skill_name
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_name}")
        return skill_path

    def get_skill_info(self, skill_name: str) -> SkillInfo:
        """Get information about a skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            SkillInfo with skill details.
        """
        skill_path = self.get_skill_path(skill_name)
        skill_md_path = skill_path / "SKILL.md"

        if not skill_md_path.exists():
            raise FileNotFoundError(f"SKILL.md not found for: {skill_name}")

        # Parse YAML frontmatter
        description = ""
        version = ""
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
            if content.startswith("---"):
                # Extract frontmatter
                end_idx = content.find("---", 3)
                if end_idx > 0:
                    frontmatter = content[3:end_idx]
                    for line in frontmatter.split("\n"):
                        if line.startswith("description:"):
                            description = line.split(":", 1)[1].strip()
                        elif line.strip().startswith("version:"):
                            version = line.split(":", 1)[1].strip().strip('"')

        # Map skill names to commands
        command_map = {
            "customer-problems": "/cp",
            "software-glance": "/glance",
            "customer-needs": "/cn",
            "software-vision": "/vision",
            "functional-requirements": "/fr",
            "zigzag-validator": "/zigzag",
            "complexity-analysis": "/complexity",
            "problem-based-srs": "/problem-based-srs",
        }

        return SkillInfo(
            name=skill_name,
            path=skill_path,
            skill_md_path=skill_md_path,
            command=command_map.get(skill_name, f"/{skill_name}"),
            description=description,
            version=version,
        )

    def list_skills(self) -> list[str]:
        """List all available skills.

        Returns:
            List of skill names.
        """
        skills_dir = self.skill_dir / "skills"
        if not skills_dir.exists():
            return []

        return [
            d.name
            for d in skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        ]

    def read_skill_content(self, skill_name: str) -> str:
        """Read the SKILL.md content for a skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            Full content of SKILL.md.
        """
        info = self.get_skill_info(skill_name)
        return info.skill_md_path.read_text(encoding="utf-8")


def get_default_skill_loader() -> SkillLoader:
    """Get a skill loader configured from environment.

    Environment variables:
        SKILL_DIR: Local path to skills (if set, uses local instead of GitHub)
        SKILL_REPO: GitHub URL (default: RafaelGorski/Problem-Based-SRS)

    By default, skills are cloned from GitHub to ensure the latest version.
    Set SKILL_DIR to use a local folder for development/offline testing.

    Returns:
        Configured SkillLoader instance.
    """
    return SkillLoader()
