"""Load and resolve OpenClaw skills from disk."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, Field

from clawbridge.core.skill import (
    ClawSkill,
    SkillLoadRecord,
    SkillLoadStatus,
    SkillSourceKind,
)


class SkillSource(BaseModel):
    """A directory searched for OpenClaw skills."""

    kind: SkillSourceKind
    path: Path

    model_config = {"arbitrary_types_allowed": True}


class SkillResolution(BaseModel):
    """Resolved skill set plus per-skill load metadata."""

    skills: list[ClawSkill] = Field(default_factory=list)
    records: list[SkillLoadRecord] = Field(default_factory=list)


class _SkillCandidate(BaseModel):
    """Internal representation of a discovered skill candidate."""

    skill: ClawSkill
    source_kind: SkillSourceKind
    source_path: Path | None = None
    discovery_index: int

    model_config = {"arbitrary_types_allowed": True}


class SkillLoader:
    """Discovers, gates, and resolves ClawSkill instances from disk."""

    BUNDLED_SKILLS_DIR = Path(__file__).resolve().parent / "bundled"
    MANAGED_SKILLS_DIR = Path.home() / ".clawbridge" / "skills"

    _PRECEDENCE = {
        SkillSourceKind.EXTRA: 0,
        SkillSourceKind.BUNDLED: 1,
        SkillSourceKind.MANAGED: 2,
        SkillSourceKind.WORKSPACE: 3,
        SkillSourceKind.INLINE: 4,
    }

    def __init__(
        self,
        search_paths: list[Path] | None = None,
        *,
        sources: list[SkillSource] | None = None,
        config: Mapping[str, Any] | None = None,
    ):
        if sources is None:
            normalized_paths = search_paths or [
                Path("./skills"),
                self.MANAGED_SKILLS_DIR,
            ]
            sources = [
                SkillSource(kind=SkillSourceKind.EXTRA, path=Path(path))
                for path in normalized_paths
            ]

        self.sources = [
            SkillSource(kind=source.kind, path=source.path.expanduser())
            for source in sources
        ]
        self.config = dict(config or {})

    @classmethod
    def default_sources(
        cls,
        *,
        workspace_path: Path | None = None,
        extra_paths: list[Path] | None = None,
        adjacent_path: Path | None = None,
    ) -> list[SkillSource]:
        """Build the standard OpenClaw skill source stack."""
        sources: list[SkillSource] = [
            SkillSource(kind=SkillSourceKind.BUNDLED, path=cls.BUNDLED_SKILLS_DIR),
            SkillSource(kind=SkillSourceKind.MANAGED, path=cls.MANAGED_SKILLS_DIR),
        ]

        seen_paths = {
            source.path.expanduser().resolve(strict=False) for source in sources
        }

        def add_source(kind: SkillSourceKind, path: Path) -> None:
            resolved_path = path.expanduser().resolve(strict=False)
            if resolved_path in seen_paths:
                return
            seen_paths.add(resolved_path)
            sources.append(SkillSource(kind=kind, path=path))

        if workspace_path is not None:
            add_source(SkillSourceKind.WORKSPACE, workspace_path / "skills")

        if (
            adjacent_path is not None
            and adjacent_path.expanduser().resolve(strict=False)
            != (workspace_path.expanduser().resolve(strict=False) if workspace_path is not None else None)
        ):
            add_source(SkillSourceKind.EXTRA, adjacent_path / "skills")

        for path in extra_paths or []:
            add_source(SkillSourceKind.EXTRA, path)

        return sources

    def discover(self) -> list[Path]:
        """Find all directories containing SKILL.md, tools.py, or main.py."""
        found: list[Path] = []
        for source in self.sources:
            found.extend(self._discover_in_source(source))
        return found

    def resolve(
        self,
        *,
        existing_skills: list[ClawSkill] | None = None,
    ) -> SkillResolution:
        """Resolve skills across sources using precedence and gating rules."""
        candidates: list[_SkillCandidate] = []
        discovery_index = 0

        for skill in existing_skills or []:
            copied = skill.model_copy(deep=True)
            if copied.source_kind is None:
                copied.source_kind = SkillSourceKind.INLINE
            candidates.append(
                _SkillCandidate(
                    skill=copied,
                    source_kind=copied.source_kind,
                    source_path=copied.source_path,
                    discovery_index=discovery_index,
                )
            )
            discovery_index += 1

        for source in self.sources:
            for path in self._discover_in_source(source):
                skill = ClawSkill.from_dir(path)
                skill.source_kind = source.kind
                candidates.append(
                    _SkillCandidate(
                        skill=skill,
                        source_kind=source.kind,
                        source_path=path.resolve(),
                        discovery_index=discovery_index,
                    )
                )
                discovery_index += 1

        grouped: dict[str, list[_SkillCandidate]] = {}
        for candidate in candidates:
            grouped.setdefault(candidate.skill.name, []).append(candidate)

        records: list[SkillLoadRecord] = []
        selected: list[_SkillCandidate] = []
        for name in sorted(grouped):
            allowed: list[_SkillCandidate] = []
            for candidate in grouped[name]:
                gating_reason = self._get_gating_reason(candidate.skill)
                if gating_reason is not None:
                    records.append(
                        SkillLoadRecord(
                            skill_name=candidate.skill.name,
                            source_kind=candidate.source_kind,
                            source_path=candidate.source_path,
                            status=SkillLoadStatus.GATED,
                            reason=gating_reason,
                        )
                    )
                    continue
                allowed.append(candidate)

            if not allowed:
                continue

            allowed.sort(
                key=lambda candidate: (
                    -self._PRECEDENCE[candidate.source_kind],
                    candidate.discovery_index,
                )
            )
            winner = allowed[0]
            selected.append(winner)
            records.append(
                SkillLoadRecord(
                    skill_name=winner.skill.name,
                    source_kind=winner.source_kind,
                    source_path=winner.source_path,
                    status=SkillLoadStatus.LOADED,
                )
            )

            for loser in allowed[1:]:
                records.append(
                    SkillLoadRecord(
                        skill_name=loser.skill.name,
                        source_kind=loser.source_kind,
                        source_path=loser.source_path,
                        status=SkillLoadStatus.SHADOWED,
                        reason=(
                            f"Shadowed by {winner.skill.name} from "
                            f"{winner.source_kind.value}:{winner.source_path}"
                        ),
                    )
                )

        selected.sort(key=lambda candidate: candidate.discovery_index)
        return SkillResolution(
            skills=[candidate.skill for candidate in selected],
            records=records,
        )

    def load_all(self) -> list[ClawSkill]:
        """Load all discovered skills after precedence and gating."""
        return self.resolve().skills

    def load_by_name(self, name: str) -> ClawSkill | None:
        """Load a specific skill by name."""
        for skill in self.load_all():
            if skill.name == name:
                return skill
        return None

    def load_by_category(self, category: str) -> list[ClawSkill]:
        """Load all skills matching a category."""
        return [skill for skill in self.load_all() if skill.category == category]

    def _discover_in_source(self, source: SkillSource) -> list[Path]:
        base = source.path.expanduser()
        if not base.exists():
            return []

        found: list[Path] = []
        if self._looks_like_skill_dir(base):
            return [base.resolve()]

        for child in sorted(base.iterdir()):
            if child.is_dir() and self._looks_like_skill_dir(child):
                found.append(child.resolve())
        return found

    @staticmethod
    def _looks_like_skill_dir(path: Path) -> bool:
        return any((path / filename).exists() for filename in ["SKILL.md", "tools.py", "main.py"])

    def _get_gating_reason(self, skill: ClawSkill) -> str | None:
        missing_env = [
            env_var for env_var in skill.requirements.env_vars
            if not os.environ.get(env_var)
        ]
        missing_binaries = [
            binary for binary in skill.requirements.binaries
            if shutil.which(binary) is None
        ]
        missing_config = [
            key for key in skill.requirements.config_keys
            if not self._config_value_present(key)
        ]

        reason_parts: list[str] = []
        if missing_env:
            reason_parts.append(f"missing env vars: {', '.join(sorted(missing_env))}")
        if missing_binaries:
            reason_parts.append(f"missing binaries: {', '.join(sorted(missing_binaries))}")
        if missing_config:
            reason_parts.append(f"missing config keys: {', '.join(sorted(missing_config))}")

        if not reason_parts:
            return None
        return "; ".join(reason_parts)

    def _config_value_present(self, key: str) -> bool:
        current: Any = self.config
        for part in key.split("."):
            if isinstance(current, Mapping):
                if part not in current:
                    return False
                current = current[part]
                continue
            return False
        return current not in (None, "", [], {}, False)
