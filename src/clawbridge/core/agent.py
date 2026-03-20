"""
ClawAgent — the universal, framework-agnostic agent definition.

Define once, deploy to Agno, Agentica, CrewAI, LangChain, etc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from clawbridge.core.memory import ClawMemory
from clawbridge.core.skill import ClawSkill
from clawbridge.core.types import (
    Backend,
    MemoryConfig,
    ModelConfig,
    ToolDefinition,
)


class ClawAgent(BaseModel):
    """
    A universal agent definition inspired by OpenClaw's architecture.

    This is the single source of truth — backends compile this into
    their native agent representations.
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
    tools: list[ToolDefinition] = Field(default_factory=list)
    skill_paths: list[Path] = Field(default_factory=list)

    # ── Memory ──
    memory_config: MemoryConfig = Field(default_factory=MemoryConfig)

    # ── System Prompt ──
    system_prompt: str = ""
    # Additional instructions appended after skills
    additional_instructions: list[str] = Field(default_factory=list)

    # ── Behavior ──
    autonomous: bool = True        # can act without explicit prompts
    human_in_loop: bool = False    # require confirmation for actions
    max_iterations: int = 10       # max tool-use loops per turn
    markdown_output: bool = True

    # ── Metadata ──
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    def build_system_prompt(self, memory: ClawMemory | None = None) -> str:
        """
        Compose the full system prompt from all components.

        Order (mirrors OpenClaw's prompt assembly):
          1. Base identity / personality
          2. Role instructions
          3. Memory context
          4. Skill instructions (each skill's SKILL.md body)
          5. Additional instructions
        """
        parts: list[str] = []

        # 1. Identity
        if self.personality:
            parts.append(f"# Personality\n{self.personality}")
        elif self.description:
            parts.append(f"# About You\n{self.description}")

        # 2. Role
        if self.role:
            parts.append(f"# Your Role\n{self.role}")

        # 3. Custom system prompt
        if self.system_prompt:
            parts.append(self.system_prompt)

        # 4. Memory context
        if memory:
            ctx = memory.get_context_summary()
            if ctx:
                parts.append(ctx)

        # 5. Skills
        if self.skills:
            parts.append("# Skills")
            for skill in self.skills:
                parts.append(skill.to_system_prompt_fragment())

        # 6. Additional instructions
        for instr in self.additional_instructions:
            parts.append(instr)

        return "\n\n".join(parts)

    def get_all_tools(self) -> list[ToolDefinition]:
        """Collect tools from both direct definitions and skills."""
        all_tools = list(self.tools)
        for skill in self.skills:
            all_tools.extend(skill.tools)
        return all_tools