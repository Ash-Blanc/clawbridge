"""OpenClaw-style agent spec used by framework builders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from clawbridge.core.channel import ChannelSessionPolicy
from clawbridge.core.memory import ClawMemory
from clawbridge.core.prompt import OpenClawPromptBuilder, OpenClawPromptContext, OpenClawPromptMode
from clawbridge.core.sandbox import SandboxConfig
from clawbridge.core.session import OpenClawSessionContext
from clawbridge.core.skill import ClawSkill, SkillLoadRecord
from clawbridge.core.workspace import OpenClawWorkspace
from clawbridge.core.types import (
    ChannelConfig,
    KnowledgeConfig,
    MemoryConfig,
    ModelConfig,
    StorageConfig,
    ToolDefinition,
)


class ClawAgent(BaseModel):
    """
    OpenClaw-style agent configuration shared by supported builders.

    This model owns prompt structure, skills, tools, and lightweight memory.
    Framework-specific integrations may consume additional builder options.
    """

    # ── Identity ──
    name: str = "Claw"
    description: str = "A personal AI assistant"
    personality: str = ""  # OpenClaw-style personality instructions
    role: str = ""         # e.g. "research assistant", "DevOps helper"

    # ── Model ──
    model: ModelConfig = Field(default_factory=ModelConfig)

    # ── Skills & Tools ──
    skills: list[ClawSkill] = Field(default_factory=list)
    skill_resolution: list[SkillLoadRecord] = Field(default_factory=list)
    tools: list[ToolDefinition] = Field(default_factory=list)
    skill_paths: list[Path] = Field(default_factory=list)
    workspace_path: Path | None = None
    workspace: OpenClawWorkspace | None = None

    # ── Memory ──
    memory_config: MemoryConfig = Field(default_factory=MemoryConfig)

    # ── Sandbox ──
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    channel_policy: ChannelSessionPolicy = Field(default_factory=ChannelSessionPolicy)

    # ── Agno-specific Extensions ──
    storage: StorageConfig = Field(default_factory=StorageConfig)
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    channels: list[ChannelConfig] = Field(default_factory=list)

    # ── System Prompt ──
    prompt_mode: OpenClawPromptMode = OpenClawPromptMode.FULL
    system_prompt: str = ""
    # Additional instructions appended after skills
    additional_instructions: list[str] = Field(default_factory=list)

    # ── Rendering ──
    markdown_output: bool = True

    # ── Metadata ──
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True, "extra": "ignore"}

    @classmethod
    def from_yaml(cls, path: str | Path) -> ClawAgent:
        """Load a ClawAgent configuration from a YAML file."""
        import yaml
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"YAML config not found: {p}")

        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return cls(**data)

    @classmethod
    def from_json(cls, path: str | Path) -> ClawAgent:
        """Load a ClawAgent configuration from a JSON file."""
        import json
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"JSON config not found: {p}")

        data = json.loads(p.read_text(encoding="utf-8"))
        return cls(**data)

    def build_system_prompt(
        self,
        memory: ClawMemory | None = None,
        *,
        prompt_context: OpenClawPromptContext | None = None,
        prompt_mode: OpenClawPromptMode | None = None,
        session_context: OpenClawSessionContext | None = None,
    ) -> str:
        """Compose an OpenClaw-style system prompt."""
        builder = OpenClawPromptBuilder()
        effective_prompt_context = prompt_context
        if session_context is not None:
            effective_prompt_context = (
                prompt_context.model_copy(deep=True)
                if prompt_context is not None
                else OpenClawPromptContext()
            )
            effective_prompt_context.session = session_context
        return builder.build(
            self,
            memory=memory,
            context=effective_prompt_context,
            mode=prompt_mode or self.prompt_mode,
        )

    def get_all_tools(self) -> list[ToolDefinition]:
        """Collect tools from both direct definitions and skills, deduplicating by name."""
        tools_by_name: dict[str, ToolDefinition] = {t.name: t for t in self.tools}
        for skill in self.skills:
            for skill_tool in skill.tools:
                if skill_tool.name not in tools_by_name:
                    tools_by_name[skill_tool.name] = skill_tool
                elif tools_by_name[skill_tool.name].callable is None and skill_tool.callable is not None:
                    # Prioritize the definition that has a callable
                    tools_by_name[skill_tool.name] = skill_tool
        return list(tools_by_name.values())
