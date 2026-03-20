"""Load skills from local directories or remote registries."""

from __future__ import annotations

from pathlib import Path

from clawbridge.core.skill import ClawSkill


class SkillLoader:
    """Discovers and loads ClawSkill instances from disk."""

    def __init__(self, search_paths: list[Path] | None = None):
        self.search_paths = search_paths or [
            Path("./skills"),
            Path.home() / ".clawbridge" / "skills",
        ]

    def discover(self) -> list[Path]:
        """Find all directories containing SKILL.md, tools.py, or main.py."""
        found: list[Path] = []
        for base in self.search_paths:
            if not base.exists():
                continue
            # Direct match
            if any((base / f).exists() for f in ["SKILL.md", "tools.py", "main.py"]):
                found.append(base)
                continue
            # Subdirectories
            for child in sorted(base.iterdir()):
                if child.is_dir() and any((child / f).exists() for f in ["SKILL.md", "tools.py", "main.py"]):
                    found.append(child)
        return found

    def load_all(self) -> list[ClawSkill]:
        """Load all discovered skills."""
        return [ClawSkill.from_dir(p) for p in self.discover()]

    def load_by_name(self, name: str) -> ClawSkill | None:
        """Load a specific skill by name."""
        for skill in self.load_all():
            if skill.name == name:
                return skill
        return None

    def load_by_category(self, category: str) -> list[ClawSkill]:
        """Load all skills matching a category."""
        return [s for s in self.load_all() if s.category == category]