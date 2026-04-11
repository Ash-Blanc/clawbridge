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
from clawbridge.core.types import (
    AgentMemoryMode,
    ChannelConfig,
    KnowledgeConfig,
    LearningConfig,
    SessionConfig,
    StorageConfig,
)
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
    agent_memory_mode: AgentMemoryMode | None = None,
    learning: LearningConfig | None = None,
    session: SessionConfig | None = None,
) -> Any:
    """Build a native Agno agent from an OpenClaw-style agent spec."""
    agent = load_agent_config(agent_config, agent_id=agent_id)

    if storage is not None:
        agent.storage = storage
    if knowledge is not None:
        agent.knowledge = knowledge
    if channels is not None:
        agent.channels = list(channels)
    if agent_memory_mode is not None:
        agent.agent_memory_mode = agent_memory_mode
    if learning is not None:
        agent.learning = learning
    if session is not None:
        agent.session = session

    return AgnoBackend(agent, memory).compile()


def build_agno_team(
    team_config: "str | Path | Any",
    *,
    memory: ClawMemory | None = None,
) -> Any:
    """Build a native Agno Team from a TeamConfig or YAML file.

    Each member ClawAgent is compiled into a native Agno Agent via AgnoBackend.
    The resulting Team uses Agno's native coordination modes.
    """
    from clawbridge.core.team import TeamConfig

    if isinstance(team_config, (str, Path)):
        team_config = TeamConfig.from_yaml(team_config)

    if not isinstance(team_config, TeamConfig):
        raise TypeError(f"Expected TeamConfig, str, or Path, got {type(team_config)}")

    # Compile each member ClawAgent → Agno Agent
    compiled_members = []
    for member in team_config.members:
        loaded = load_agent_config(member)
        compiled_members.append(AgnoBackend(loaded, memory).compile())

    # Build Team kwargs
    try:
        from agno.team import Team
        from agno.team.team import TeamMode as AgnoTeamMode
    except ImportError:
        raise ImportError(
            "Agno is not installed. Run: pip install clawbridge[agno]"
        )

    team_kwargs: dict[str, Any] = {
        "name": team_config.name,
        "members": compiled_members,
        "mode": AgnoTeamMode(team_config.mode.value),
        "markdown": team_config.markdown,
        "max_iterations": team_config.max_iterations,
        "share_member_interactions": team_config.share_member_interactions,
    }

    if team_config.description:
        team_kwargs["description"] = team_config.description
    if team_config.role:
        team_kwargs["role"] = team_config.role
    if team_config.instructions:
        team_kwargs["instructions"] = team_config.instructions

    # Team coordinator model (optional — Agno falls back to member models)
    if team_config.model is not None:
        coordinator_backend = AgnoBackend(
            ClawAgent(name="_coordinator", model=team_config.model)
        )
        team_kwargs["model"] = coordinator_backend._resolve_model()

    # Storage / Db
    if team_config.storage.enabled:
        storage_backend = AgnoBackend(
            ClawAgent(name="_storage", storage=team_config.storage)
        )
        db = storage_backend._build_db()
        if db:
            team_kwargs["db"] = db

    # Hermes-like features on the Team
    _apply_team_memory_config(team_config, team_kwargs)
    _apply_team_learning_config(team_config, team_kwargs)
    _apply_team_session_config(team_config, team_kwargs)

    return Team(**team_kwargs)


def _apply_team_memory_config(
    config: Any,
    kwargs: dict[str, Any],
) -> None:
    """Apply memory config to team kwargs."""
    mode = config.agent_memory_mode
    if mode == AgentMemoryMode.AUTOMATIC:
        kwargs["update_memory_on_run"] = True
        kwargs["enable_user_memories"] = True
        kwargs["add_memories_to_context"] = True
    elif mode == AgentMemoryMode.AGENTIC:
        kwargs["enable_agentic_memory"] = True
        kwargs["enable_user_memories"] = True
        kwargs["add_memories_to_context"] = True


def _apply_team_learning_config(
    config: Any,
    kwargs: dict[str, Any],
) -> None:
    """Apply learning config to team kwargs."""
    if config.learning.enabled:
        kwargs["learning"] = True
        kwargs["add_learnings_to_context"] = config.learning.add_learnings_to_context


def _apply_team_session_config(
    config: Any,
    kwargs: dict[str, Any],
) -> None:
    """Apply session config to team kwargs."""
    sc = config.session
    if sc.search_past_sessions:
        kwargs["search_past_sessions"] = True
        kwargs["num_past_sessions_to_search"] = sc.num_past_sessions_to_search
    if sc.enable_session_summaries:
        kwargs["enable_session_summaries"] = True
    if sc.compress_tool_results:
        kwargs["compress_tool_results"] = True
    if sc.reasoning:
        kwargs["reasoning"] = True


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
