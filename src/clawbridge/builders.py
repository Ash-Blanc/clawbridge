"""Framework-native builders for OpenClaw-style agent specs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from clawbridge.backends.agno import AgnoBackend
from clawbridge.backends.agentica import AgenticaBackend
from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
from clawbridge.core.multi_agent import (
    MultiAgentConfig,
    looks_like_multi_agent_config,
)
from clawbridge.core.workspace import OpenClawWorkspace
from clawbridge.core.types import ChannelConfig, KnowledgeConfig, StorageConfig
from clawbridge.skills.loader import SkillLoader


AgentSource = str | Path | ClawAgent | MultiAgentConfig


def load_agent_config(
    agent_config: AgentSource,
    *,
    agent_id: str | None = None,
) -> ClawAgent:
    """Load and normalize an OpenClaw-style agent spec."""
    if isinstance(agent_config, MultiAgentConfig):
        agent = agent_config.select_agent(agent_id=agent_id)
        _load_workspace(agent)
        _resolve_skills(agent)
        return agent

    if isinstance(agent_config, ClawAgent):
        agent = agent_config.model_copy(deep=True)
        _load_workspace(agent)
        _resolve_skills(agent)
        return agent

    path = Path(agent_config)
    if path.suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    elif path.suffix == ".json":
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Config file must be .yaml, .yml, or .json")

    if isinstance(data, dict) and looks_like_multi_agent_config(data):
        multi_agent = MultiAgentConfig.from_mapping(data, base_dir=path.parent)
        agent = multi_agent.select_agent(agent_id=agent_id)
        _load_workspace(agent, base_dir=path.parent)
        _resolve_skills(agent, base_dir=path.parent)
        return agent

    if not isinstance(data, dict):
        raise ValueError("Agent config must deserialize to a mapping.")
    agent = ClawAgent(**data)
    _load_workspace(agent, base_dir=path.parent)
    _resolve_skills(agent, base_dir=path.parent)
    return agent


def build_agno_agent(
    agent_config: AgentSource,
    *,
    agent_id: str | None = None,
    memory: ClawMemory | None = None,
    storage: StorageConfig | None = None,
    knowledge: KnowledgeConfig | None = None,
    channels: Sequence[ChannelConfig] | None = None,
) -> Any:
    """Build a native Agno agent from an OpenClaw-style agent spec."""
    agent = load_agent_config(agent_config, agent_id=agent_id)

    if storage is not None:
        agent.storage = storage
    if knowledge is not None:
        agent.knowledge = knowledge
    if channels is not None:
        agent.channels = list(channels)

    return AgnoBackend(agent, memory).compile()


def build_agentica_agent(
    agent_config: AgentSource,
    *,
    agent_id: str | None = None,
    memory: ClawMemory | None = None,
) -> Any:
    """Build an Agentica-ready config from an OpenClaw-style agent spec."""
    agent = load_agent_config(agent_config, agent_id=agent_id)
    return AgenticaBackend(agent, memory).compile()


def _resolve_skills(agent: ClawAgent, *, base_dir: Path | None = None) -> None:
    sources = SkillLoader.default_sources(
        workspace_path=agent.workspace_path,
        extra_paths=agent.skill_paths,
        adjacent_path=base_dir,
    )
    loader = SkillLoader(sources=sources, config=agent.metadata)
    resolution = loader.resolve(existing_skills=agent.skills)
    agent.skills = resolution.skills
    agent.skill_resolution = resolution.records


def _load_workspace(agent: ClawAgent, *, base_dir: Path | None = None) -> None:
    if agent.workspace is not None:
        if agent.workspace_path is None:
            agent.workspace_path = agent.workspace.root_dir
        return

    workspace_path = agent.workspace_path
    if workspace_path is not None:
        candidate = workspace_path.expanduser()
        if not candidate.is_absolute():
            if base_dir is None:
                candidate = candidate.resolve()
            else:
                candidate = (base_dir / candidate).resolve()
        agent.workspace_path = candidate
        agent.workspace = OpenClawWorkspace.from_dir(candidate)
        return

    if base_dir is not None and OpenClawWorkspace.has_workspace(base_dir):
        agent.workspace_path = base_dir.resolve()
        agent.workspace = OpenClawWorkspace.from_dir(base_dir)
