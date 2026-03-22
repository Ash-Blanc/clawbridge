"""Multi-agent OpenClaw configuration models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from clawbridge.core.agent import ClawAgent


class MultiAgentDefinition(BaseModel):
    """A single agent entry in a multi-agent config."""

    agent_id: str
    agent: ClawAgent


class MultiAgentConfig(BaseModel):
    """Config container for selecting one agent from many definitions."""

    agents: list[MultiAgentDefinition] = Field(default_factory=list)
    default_agent_id: str | None = None
    shared_skill_paths: list[Path] = Field(default_factory=list)
    allow_shared_workspaces: bool = False
    allow_shared_state_dirs: bool = False

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_mapping(
        cls,
        data: dict[str, Any],
        *,
        base_dir: Path | None = None,
    ) -> MultiAgentConfig:
        """Parse a multi-agent config from a mapping payload."""
        shared_skill_paths = [
            _resolve_path(path, base_dir)
            for path in (data.get("shared_skill_paths") or [])
        ]
        allow_shared_workspaces = bool(data.get("allow_shared_workspaces", False))
        allow_shared_state_dirs = bool(data.get("allow_shared_state_dirs", False))
        default_agent_id = data.get("default_agent_id")

        raw_agents = data.get("agents")
        if raw_agents is None:
            raise ValueError("Multi-agent config requires an 'agents' section.")

        definitions: list[MultiAgentDefinition] = []
        if isinstance(raw_agents, dict):
            for agent_id, payload in raw_agents.items():
                definitions.append(
                    MultiAgentDefinition(
                        agent_id=agent_id,
                        agent=_build_agent(payload, base_dir=base_dir),
                    )
                )
        elif isinstance(raw_agents, list):
            for item in raw_agents:
                if not isinstance(item, dict):
                    raise ValueError(
                        "Each item in 'agents' must be a mapping with an 'id'."
                    )
                agent_id = item.get("id")
                if not agent_id:
                    raise ValueError("Each agent entry must define a non-empty 'id'.")
                payload = dict(item)
                payload.pop("id", None)
                if "agent" in payload and isinstance(payload["agent"], dict):
                    payload = payload["agent"]
                definitions.append(
                    MultiAgentDefinition(
                        agent_id=str(agent_id),
                        agent=_build_agent(payload, base_dir=base_dir),
                    )
                )
        else:
            raise ValueError("'agents' must be either a mapping or a list.")

        config = cls(
            agents=definitions,
            default_agent_id=default_agent_id,
            shared_skill_paths=shared_skill_paths,
            allow_shared_workspaces=allow_shared_workspaces,
            allow_shared_state_dirs=allow_shared_state_dirs,
        )
        config.validate_workspace_isolation()
        config.validate_state_dir_isolation()
        return config

    def select_agent(self, agent_id: str | None = None) -> ClawAgent:
        """Return a copy of the selected agent config."""
        if not self.agents:
            raise ValueError("Multi-agent config does not contain any agents.")

        selected_id = agent_id or self.default_agent_id or self.agents[0].agent_id
        for definition in self.agents:
            if definition.agent_id == selected_id:
                selected_agent = definition.agent.model_copy(deep=True)
                selected_agent.agent_id = definition.agent_id
                selected_agent.skill_paths = [
                    *self.shared_skill_paths,
                    *selected_agent.skill_paths,
                ]
                return selected_agent

        known_ids = ", ".join(sorted(definition.agent_id for definition in self.agents))
        raise ValueError(
            f"Unknown agent_id '{selected_id}'. Available agents: {known_ids}"
        )

    def validate_workspace_isolation(self) -> None:
        """Detect accidental shared workspace usage across agents."""
        if self.allow_shared_workspaces:
            return

        seen: dict[Path, str] = {}
        for definition in self.agents:
            workspace_path = definition.agent.workspace_path
            if workspace_path is None:
                continue
            resolved_path = workspace_path.expanduser().resolve()
            previous_agent = seen.get(resolved_path)
            if previous_agent is not None:
                raise ValueError(
                    "Multiple agents resolve to the same workspace path "
                    f"'{resolved_path}' ({previous_agent}, {definition.agent_id}). "
                    "Set allow_shared_workspaces=true to allow this explicitly."
                )
            seen[resolved_path] = definition.agent_id

    def validate_state_dir_isolation(self) -> None:
        """Detect accidental shared state dir usage across agents."""
        if self.allow_shared_state_dirs:
            return

        seen: dict[Path, str] = {}
        for definition in self.agents:
            state_dir = definition.agent.state_dir
            if state_dir is None:
                continue
            resolved_path = state_dir.expanduser().resolve()
            previous_agent = seen.get(resolved_path)
            if previous_agent is not None:
                raise ValueError(
                    "Multiple agents resolve to the same state dir "
                    f"'{resolved_path}' ({previous_agent}, {definition.agent_id}). "
                    "Set allow_shared_state_dirs=true to allow this explicitly."
                )
            seen[resolved_path] = definition.agent_id


def looks_like_multi_agent_config(data: dict[str, Any]) -> bool:
    """Return True when a payload should be parsed as multi-agent config."""
    if "agents" not in data:
        return False
    agents = data.get("agents")
    return isinstance(agents, (list, dict))


def _build_agent(data: dict[str, Any], *, base_dir: Path | None) -> ClawAgent:
    payload = dict(data)
    if "workspace_path" in payload and payload["workspace_path"] is not None:
        payload["workspace_path"] = _resolve_path(payload["workspace_path"], base_dir)
    if "state_dir" in payload and payload["state_dir"] is not None:
        payload["state_dir"] = _resolve_path(payload["state_dir"], base_dir)
    if "skill_paths" in payload and payload["skill_paths"] is not None:
        payload["skill_paths"] = [
            _resolve_path(path, base_dir) for path in payload["skill_paths"]
        ]
    return ClawAgent(**payload)


def _resolve_path(value: str | Path, base_dir: Path | None) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    if base_dir is None:
        return path.resolve()
    return (base_dir / path).resolve()
