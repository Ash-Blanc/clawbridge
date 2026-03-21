from __future__ import annotations

from pathlib import Path

from clawbridge.builders import load_agent_config
from clawbridge.core.agent import ClawAgent
from clawbridge.core.skill import SkillLoadStatus, SkillSourceKind
from clawbridge.skills.loader import SkillLoader, SkillSource


def test_skill_loader_applies_openclaw_precedence(tmp_path: Path) -> None:
    bundled_dir = tmp_path / "bundled"
    managed_dir = tmp_path / "managed"
    workspace_dir = tmp_path / "workspace"
    extra_dir = tmp_path / "extra"

    _write_skill(bundled_dir / "lookup", name="lookup", description="bundled")
    _write_skill(managed_dir / "lookup", name="lookup", description="managed")
    _write_skill(workspace_dir / "lookup", name="lookup", description="workspace")
    _write_skill(extra_dir / "lookup", name="lookup", description="extra")

    loader = SkillLoader(
        sources=[
            SkillSource(kind=SkillSourceKind.BUNDLED, path=bundled_dir),
            SkillSource(kind=SkillSourceKind.MANAGED, path=managed_dir),
            SkillSource(kind=SkillSourceKind.WORKSPACE, path=workspace_dir),
            SkillSource(kind=SkillSourceKind.EXTRA, path=extra_dir),
        ]
    )

    resolution = loader.resolve()

    assert len(resolution.skills) == 1
    assert resolution.skills[0].name == "lookup"
    assert resolution.skills[0].description == "workspace"
    assert resolution.skills[0].source_kind == SkillSourceKind.WORKSPACE

    shadowed_kinds = {
        record.source_kind
        for record in resolution.records
        if record.status == SkillLoadStatus.SHADOWED
    }
    assert shadowed_kinds == {
        SkillSourceKind.BUNDLED,
        SkillSourceKind.MANAGED,
        SkillSourceKind.EXTRA,
    }


def test_skill_loader_gates_skills_with_clear_reasons(tmp_path: Path) -> None:
    gated_dir = tmp_path / "gated"
    _write_skill(
        gated_dir / "needs-env",
        name="needs-env",
        description="Requires runtime integration",
        requires_block="""
requires:
  env:
    - CLAWBRIDGE_REQUIRED_TOKEN
  binaries:
    - definitely_missing_binary
  config:
    - integrations.slack.token
""".strip(),
    )

    loader = SkillLoader(
        sources=[SkillSource(kind=SkillSourceKind.EXTRA, path=gated_dir)]
    )

    resolution = loader.resolve()

    assert resolution.skills == []
    assert len(resolution.records) == 1
    record = resolution.records[0]
    assert record.status == SkillLoadStatus.GATED
    assert "CLAWBRIDGE_REQUIRED_TOKEN" in (record.reason or "")
    assert "definitely_missing_binary" in (record.reason or "")
    assert "integrations.slack.token" in (record.reason or "")


def test_load_agent_config_prefers_workspace_skills_over_extra_paths(
    tmp_path: Path,
) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    _write_skill(
        workspace_dir / "skills" / "search",
        name="search",
        description="workspace",
    )

    extra_dir = tmp_path / "extra-skills"
    _write_skill(extra_dir / "search", name="search", description="extra")

    agent = load_agent_config(
        ClawAgent(
            name="Skillful",
            workspace_path=workspace_dir,
            skill_paths=[extra_dir],
        )
    )

    assert len(agent.skills) == 1
    assert agent.skills[0].name == "search"
    assert agent.skills[0].description == "workspace"
    assert agent.skills[0].source_kind == SkillSourceKind.WORKSPACE
    assert any(
        record.status == SkillLoadStatus.SHADOWED
        and record.source_kind == SkillSourceKind.EXTRA
        for record in agent.skill_resolution
    )


def _write_skill(
    directory: Path,
    *,
    name: str,
    description: str,
    requires_block: str | None = None,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
    ]
    if requires_block:
        lines.append(requires_block)
    lines.extend(
        [
            "---",
            f"# Skill: {name}",
            f"Use the {name} skill.",
            "",
        ]
    )
    (directory / "SKILL.md").write_text("\n".join(lines), encoding="utf-8")
