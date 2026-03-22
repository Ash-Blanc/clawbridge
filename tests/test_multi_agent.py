from __future__ import annotations

from pathlib import Path

import pytest

from clawbridge.builders import load_agent_config
from clawbridge.core.skill import SkillLoadStatus


def test_load_agent_config_selects_default_agent_from_multi_yaml(
    tmp_path: Path,
) -> None:
    researcher_workspace = tmp_path / "researcher"
    writer_workspace = tmp_path / "writer"
    researcher_workspace.mkdir()
    writer_workspace.mkdir()
    (researcher_workspace / "AGENTS.md").write_text("Research rules", encoding="utf-8")
    (writer_workspace / "AGENTS.md").write_text("Writer rules", encoding="utf-8")

    config_path = tmp_path / "agents.yaml"
    config_path.write_text(
        """
default_agent_id: writer
agents:
  - id: researcher
    name: Researcher
    workspace_path: ./researcher
  - id: writer
    name: Writer
    workspace_path: ./writer
""".strip(),
        encoding="utf-8",
    )

    agent = load_agent_config(config_path)

    assert agent.name == "Writer"
    assert agent.workspace_path == writer_workspace.resolve()
    assert agent.workspace is not None
    assert agent.workspace.agents.content == "Writer rules"


def test_load_agent_config_selects_explicit_agent_id_from_multi_yaml(
    tmp_path: Path,
) -> None:
    researcher_workspace = tmp_path / "researcher"
    writer_workspace = tmp_path / "writer"
    researcher_workspace.mkdir()
    writer_workspace.mkdir()
    (researcher_workspace / "AGENTS.md").write_text("Research rules", encoding="utf-8")
    (writer_workspace / "AGENTS.md").write_text("Writer rules", encoding="utf-8")

    config_path = tmp_path / "agents.yaml"
    config_path.write_text(
        """
default_agent_id: writer
agents:
  researcher:
    name: Researcher
    workspace_path: ./researcher
  writer:
    name: Writer
    workspace_path: ./writer
""".strip(),
        encoding="utf-8",
    )

    agent = load_agent_config(config_path, agent_id="researcher")

    assert agent.name == "Researcher"
    assert agent.agent_id == "researcher"
    assert agent.workspace_path == researcher_workspace.resolve()
    assert agent.workspace is not None
    assert agent.workspace.agents.content == "Research rules"


def test_multi_agent_config_rejects_accidental_workspace_sharing(
    tmp_path: Path,
) -> None:
    shared_workspace = tmp_path / "shared"
    shared_workspace.mkdir()
    (shared_workspace / "AGENTS.md").write_text("Shared rules", encoding="utf-8")

    config_path = tmp_path / "agents.yaml"
    config_path.write_text(
        """
agents:
  - id: one
    name: One
    workspace_path: ./shared
  - id: two
    name: Two
    workspace_path: ./shared
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="same workspace path"):
        load_agent_config(config_path)


def test_multi_agent_shared_skill_paths_are_lower_than_workspace_skills(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "writer"
    workspace.mkdir()
    (workspace / "AGENTS.md").write_text("Writer rules", encoding="utf-8")

    workspace_skill = workspace / "skills" / "search"
    workspace_skill.mkdir(parents=True)
    (workspace_skill / "SKILL.md").write_text(
        """
---
name: search
description: Workspace search skill
---
# Skill: Search
Use workspace search.
""".strip(),
        encoding="utf-8",
    )

    shared_skills = tmp_path / "shared_skills"
    shared_skill = shared_skills / "search"
    shared_skill.mkdir(parents=True)
    (shared_skill / "SKILL.md").write_text(
        """
---
name: search
description: Shared search skill
---
# Skill: Search
Use shared search.
""".strip(),
        encoding="utf-8",
    )

    config_path = tmp_path / "agents.yaml"
    config_path.write_text(
        """
shared_skill_paths:
  - ./shared_skills
agents:
  - id: writer
    name: Writer
    workspace_path: ./writer
""".strip(),
        encoding="utf-8",
    )

    agent = load_agent_config(config_path)

    assert len(agent.skills) == 1
    assert agent.skills[0].name == "search"
    assert agent.skills[0].description == "Workspace search skill"
    assert any(
        record.status == SkillLoadStatus.SHADOWED
        and record.skill_name == "search"
        for record in agent.skill_resolution
    )


def test_multi_agent_config_resolves_per_agent_state_dir_and_auth_profile(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "assistant"
    workspace.mkdir()
    (workspace / "AGENTS.md").write_text("Assistant rules", encoding="utf-8")

    config_path = tmp_path / "agents.yaml"
    config_path.write_text(
        """
default_agent_id: assistant
agents:
  assistant:
    name: Assistant
    workspace_path: ./assistant
    state_dir: ./.clawbridge/assistant
    auth_profile: assistant
""".strip(),
        encoding="utf-8",
    )

    agent = load_agent_config(config_path)

    assert agent.agent_id == "assistant"
    assert agent.state_dir == (tmp_path / ".clawbridge" / "assistant").resolve()
    assert agent.auth_profile == "assistant"


def test_multi_agent_config_rejects_accidental_state_dir_sharing(
    tmp_path: Path,
) -> None:
    one_workspace = tmp_path / "one"
    two_workspace = tmp_path / "two"
    one_workspace.mkdir()
    two_workspace.mkdir()
    (one_workspace / "AGENTS.md").write_text("One rules", encoding="utf-8")
    (two_workspace / "AGENTS.md").write_text("Two rules", encoding="utf-8")

    config_path = tmp_path / "agents.yaml"
    config_path.write_text(
        """
agents:
  one:
    name: One
    workspace_path: ./one
    state_dir: ./.clawbridge/shared
  two:
    name: Two
    workspace_path: ./two
    state_dir: ./.clawbridge/shared
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="same state dir"):
        load_agent_config(config_path)
