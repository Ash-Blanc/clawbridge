"""Tests for TeamConfig and build_agno_team."""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path

import pytest

from clawbridge.core.agent import ClawAgent
from clawbridge.core.team import TeamConfig
from clawbridge.core.types import (
    AgentMemoryMode,
    LearningConfig,
    ModelConfig,
    StorageConfig,
    StorageType,
    TeamMode,
)


def test_team_config_defaults():
    team = TeamConfig(name="Test Team")
    assert team.mode == TeamMode.COORDINATE
    assert team.members == []
    assert team.max_iterations == 10
    assert team.agent_memory_mode == AgentMemoryMode.OFF


def test_team_config_with_members():
    team = TeamConfig(
        name="Research Team",
        mode=TeamMode.ROUTE,
        members=[
            ClawAgent(name="Researcher", role="Find information"),
            ClawAgent(name="Writer", role="Summarize findings"),
        ],
    )
    assert len(team.members) == 2
    assert team.members[0].name == "Researcher"
    assert team.members[1].name == "Writer"
    assert team.mode == TeamMode.ROUTE


def test_team_config_from_yaml(tmp_path: Path):
    yaml_content = """
name: Research Team
mode: coordinate
members:
  - name: Researcher
    role: Find relevant information
    model:
      provider: openai
      model: gpt-4o
  - name: Writer
    role: Draft clear summaries
    model:
      provider: anthropic
      model: claude-sonnet-4-20250514
"""
    yaml_file = tmp_path / "team.yaml"
    yaml_file.write_text(yaml_content)

    team = TeamConfig.from_yaml(yaml_file)

    assert team.name == "Research Team"
    assert team.mode == TeamMode.COORDINATE
    assert len(team.members) == 2
    assert team.members[0].name == "Researcher"
    assert team.members[0].model.provider == "openai"
    assert team.members[1].name == "Writer"
    assert team.members[1].model.provider == "anthropic"


def test_team_config_from_yaml_with_hermes_features(tmp_path: Path):
    yaml_content = """
name: Learning Team
mode: broadcast
storage:
  enabled: true
  type: in_memory
agent_memory_mode: automatic
learning:
  enabled: true
session:
  search_past_sessions: true
members:
  - name: Agent A
    role: Do task A
  - name: Agent B
    role: Do task B
"""
    yaml_file = tmp_path / "team.yaml"
    yaml_file.write_text(yaml_content)

    team = TeamConfig.from_yaml(yaml_file)

    assert team.mode == TeamMode.BROADCAST
    assert team.agent_memory_mode == AgentMemoryMode.AUTOMATIC
    assert team.learning.enabled is True
    assert team.session.search_past_sessions is True


@pytest.mark.skipif(find_spec("agno") is None, reason="agno not installed")
class TestBuildAgnoTeam:

    def test_basic_team_compile(self):
        from clawbridge.builders import build_agno_team
        from agno.team import Team

        team_config = TeamConfig(
            name="Test Team",
            mode=TeamMode.COORDINATE,
            members=[
                ClawAgent(
                    name="Agent A",
                    role="Handle task A",
                    model=ModelConfig(provider="openai", model="gpt-4o"),
                ),
                ClawAgent(
                    name="Agent B",
                    role="Handle task B",
                    model=ModelConfig(provider="openai", model="gpt-4o"),
                ),
            ],
        )

        native_team = build_agno_team(team_config)

        assert isinstance(native_team, Team)
        assert native_team.name == "Test Team"
        assert len(native_team.members) == 2

    def test_team_mode_mapping(self):
        from clawbridge.builders import build_agno_team
        from agno.team.team import TeamMode as AgnoTeamMode

        for claw_mode, agno_mode in [
            (TeamMode.COORDINATE, AgnoTeamMode.coordinate),
            (TeamMode.ROUTE, AgnoTeamMode.route),
            (TeamMode.BROADCAST, AgnoTeamMode.broadcast),
            (TeamMode.TASKS, AgnoTeamMode.tasks),
        ]:
            team = build_agno_team(
                TeamConfig(
                    name="ModeTest",
                    mode=claw_mode,
                    members=[
                        ClawAgent(
                            name="A",
                            model=ModelConfig(provider="openai", model="gpt-4o"),
                        ),
                    ],
                )
            )
            assert team.mode == agno_mode

    def test_team_with_coordinator_model(self):
        from clawbridge.builders import build_agno_team
        from agno.models.openai import OpenAIChat

        team = build_agno_team(
            TeamConfig(
                name="Led Team",
                model=ModelConfig(provider="openai", model="gpt-4o"),
                members=[
                    ClawAgent(
                        name="Worker",
                        model=ModelConfig(provider="openai", model="gpt-4o"),
                    ),
                ],
            )
        )

        assert isinstance(team.model, OpenAIChat)
        assert team.model.id == "gpt-4o"

    def test_team_with_storage_and_memory(self):
        from clawbridge.builders import build_agno_team

        team = build_agno_team(
            TeamConfig(
                name="Memory Team",
                storage=StorageConfig(enabled=True, type=StorageType.IN_MEMORY),
                agent_memory_mode=AgentMemoryMode.AUTOMATIC,
                members=[
                    ClawAgent(
                        name="Agent",
                        model=ModelConfig(provider="openai", model="gpt-4o"),
                    ),
                ],
            )
        )

        assert team.update_memory_on_run is True

    def test_team_from_yaml(self, tmp_path: Path):
        from clawbridge.builders import build_agno_team
        from agno.team import Team

        yaml_content = """
name: YAML Team
mode: route
members:
  - name: Router Agent
    role: Route tasks
    model:
      provider: openai
      model: gpt-4o
"""
        yaml_file = tmp_path / "team.yaml"
        yaml_file.write_text(yaml_content)

        native_team = build_agno_team(yaml_file)

        assert isinstance(native_team, Team)
        assert native_team.name == "YAML Team"
        assert len(native_team.members) == 1

    def test_team_with_learning(self):
        from clawbridge.builders import build_agno_team

        team = build_agno_team(
            TeamConfig(
                name="Learning Team",
                learning=LearningConfig(enabled=True),
                storage=StorageConfig(enabled=True, type=StorageType.IN_MEMORY),
                members=[
                    ClawAgent(
                        name="Agent",
                        model=ModelConfig(provider="openai", model="gpt-4o"),
                    ),
                ],
            )
        )

        assert team.learning is True
