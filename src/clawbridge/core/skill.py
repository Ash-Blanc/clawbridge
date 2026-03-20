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
    def from_dir(cls, path: Path) -> ClawSkill:
        """Parse a skill directory into a ClawSkill."""
        skill_file = path / "SKILL.md" if path.is_dir() else path
        
        # Discover dynamic callables first
        callables: dict[str, Any] = {}
        if path.is_dir():
            callables = cls._load_callables_from_dir(path)

        # If SKILL.md exists, use it as the source of truth
        if skill_file.exists():
            content = skill_file.read_text(encoding="utf-8")
            frontmatter, body = cls._parse_frontmatter(content)
            
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
                        callable=callables.get(t["name"])
                    )
                )

            return cls(
                name=frontmatter.get("name", path.name),
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
        
        # Otherwise, auto-generate from Python callables
        tools = []
        import inspect
        from typing import get_type_hints
        
        for name, func in callables.items():
            doc = inspect.getdoc(func) or f"Tool for {name}."
            hints = get_type_hints(func)
            sig = inspect.signature(func)
            
            params = []
            for param_name, param in sig.parameters.items():
                if param_name == "return":
                    continue
                param_type = hints.get(param_name, Any)
                type_name = getattr(param_type, "__name__", str(param_type))
                required = param.default is inspect.Parameter.empty
                params.append(
                    ToolParameter(
                        name=param_name,
                        type=type_name,
                        required=required,
                        description=f"Parameter {param_name}"
                    )
                )
            
            tools.append(
                ToolDefinition(
                    name=name,
                    description=doc.strip().split("\n")[0], # First line of docstring
                    parameters=params,
                    callable=func
                )
            )

        return cls(
            name=path.name,
            description="Auto-generated from Python callables.",
            instructions="Use the provided tools as necessary.",
            tools=tools,
            source_path=path,
        )

    @classmethod
    def from_skill_md(cls, path: Path) -> ClawSkill:
        """Legacy alias."""
        return cls.from_dir(path)

    @staticmethod
    def _load_callables_from_dir(path: Path) -> dict[str, Any]:
        """Attempt to load python callables from main.py or tools.py."""
        import importlib.util
        import sys
        
        callables = {}
        for py_file in ["tools.py", "main.py"]:
            file_path = path / py_file
            if file_path.exists():
                module_name = f"skill_module_{path.name}_{py_file.split('.')[0]}"
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = mod
                    spec.loader.exec_module(mod)
                    
                    # Extract callables
                    for name in dir(mod):
                        if not name.startswith("_"):
                            obj = getattr(mod, name)
                            if callable(obj):
                                callables[name] = obj
        return callables

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