"""OpenClaw-style team configuration for multi-agent coordination."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from clawbridge.core.agent import ClawAgent
from clawbridge.core.types import (
    AgentMemoryMode,
    KnowledgeConfig,
    LearningConfig,
    ModelConfig,
    SessionConfig,
    StorageConfig,
    TeamMode,
)


class TeamConfig(BaseModel):
    """Multi-agent team configuration that maps to Agno's Team primitive.

    Each member is a ClawAgent that gets compiled into a native Agno Agent.
    The team coordinator uses the specified mode to orchestrate members.
    """

    # ── Identity ──
    name: str = "Team"
    description: str = ""
    role: str = ""
    instructions: list[str] = Field(default_factory=list)

    # ── Coordination ──
    mode: TeamMode = TeamMode.COORDINATE
    model: ModelConfig | None = None
    members: list[ClawAgent] = Field(default_factory=list)
    max_iterations: int = 10
    share_member_interactions: bool = False
    enable_agentic_context: bool = False

    # ── Storage ──
    storage: StorageConfig = Field(default_factory=StorageConfig)

    # ── Hermes-like Features ──
    agent_memory_mode: AgentMemoryMode = Field(default=AgentMemoryMode.OFF)
    learning: LearningConfig = Field(default_factory=LearningConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)

    # ── Knowledge ──
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)

    # ── Rendering ──
    markdown: bool = True

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_yaml(cls, path: str | Path) -> TeamConfig:
        """Load a TeamConfig from a YAML file."""
        import yaml

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Team config not found: {p}")
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return cls._from_mapping(data)

    @classmethod
    def _from_mapping(cls, data: dict[str, Any]) -> TeamConfig:
        """Parse a TeamConfig from a dict, building ClawAgent members."""
        members_raw = data.pop("members", [])
        members = [ClawAgent(**m) if isinstance(m, dict) else m for m in members_raw]

        model_raw = data.pop("model", None)
        model = ModelConfig(**model_raw) if isinstance(model_raw, dict) else model_raw

        return cls(members=members, model=model, **data)
