"""
OpenClaw SKILL.md parser and skill model.

OpenClaw skills are directories containing a SKILL.md file with YAML
frontmatter and markdown instructions. This module parses them into a
framework-agnostic ClawSkill model.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from clawbridge.core.types import ToolDefinition, ToolParameter


class ClawSkill(BaseModel):
    """
    A parsed OpenClaw skill — the universal skill representation.

    Mirrors the SKILL.md format:
      ---
      name: skill-name
      description: What this skill does
      category: utility
      version: 1.0.0
      tools:
        - name: tool_name
          description: What the tool does
          parameters:
            - name: param1
              type: string
              required: true
      ---
      # Skill: Skill Name
      ## Overview
      Instructions for the AI agent...
    """

    name: str
    description: str = ""
    category: str = "general"
    version: str = "1.0.0"
    author: str = ""
    tags: list[str] = Field(default_factory=list)

    # The full markdown instructions (body of SKILL.md)
    instructions: str = ""
    # Parsed tool definitions from frontmatter
    tools: list[ToolDefinition] = Field(default_factory=list)
    # Raw frontmatter for extensions
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Source path
    source_path: Path | None = None

    @classmethod
    def from_skill_md(cls, path: Path) -> ClawSkill:
        """Parse a SKILL.md file into a ClawSkill."""
        skill_file = path / "SKILL.md" if path.is_dir() else path
        if not skill_file.exists():
            raise FileNotFoundError(f"SKILL.md not found at {skill_file}")

        content = skill_file.read_text(encoding="utf-8")
        frontmatter, body = cls._parse_frontmatter(content)

        # Parse tools from frontmatter
        raw_tools = frontmatter.pop("tools", []) or []
        tools = []
        for t in raw_tools:
            params = [
                ToolParameter(**p) for p in (t.get("parameters") or [])
            ]
            tools.append(
                ToolDefinition(
                    name=t["name"],
                    description=t.get("description", ""),
                    parameters=params,
                )
            )

        return cls(
            name=frontmatter.get("name", path.stem),
            description=frontmatter.get("description", ""),
            category=frontmatter.get("category", "general"),
            version=frontmatter.get("version", "1.0.0"),
            author=frontmatter.get("author", ""),
            tags=frontmatter.get("tags", []),
            instructions=body.strip(),
            tools=tools,
            metadata=frontmatter,
            source_path=path,
        )

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
        """Split YAML frontmatter from markdown body."""
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        if match:
            fm = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
            return fm, body
        return {}, content

    def to_system_prompt_fragment(self) -> str:
        """Convert skill into a system prompt fragment for injection."""
        parts = [f"## Skill: {self.name}"]
        if self.description:
            parts.append(f"**Description:** {self.description}")
        if self.instructions:
            parts.append(self.instructions)
        if self.tools:
            parts.append("### Available Tools")
            for tool in self.tools:
                param_str = ", ".join(
                    f"{p.name}: {p.type}" for p in tool.parameters
                )
                parts.append(f"- **{tool.name}**({param_str}): {tool.description}")
        return "\n\n".join(parts)