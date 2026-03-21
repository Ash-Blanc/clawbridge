from __future__ import annotations

from pathlib import Path

from clawbridge.builders import build_agentica_agent, load_agent_config
from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
from clawbridge.core.prompt import OpenClawPromptContext, OpenClawPromptMode
from clawbridge.core.session import OpenClawSessionContext, OpenClawSessionScope
from clawbridge.core.types import MemoryConfig
from clawbridge.core.types import ToolDefinition


def test_build_system_prompt_keeps_openclaw_section_order() -> None:
    memory = ClawMemory(MemoryConfig(enabled=False))
    memory.remember("timezone", "UTC", category="preference")

    agent = ClawAgent(
        name="Assistant",
        personality="Helpful and direct.",
        role="Research assistant",
        tools=[ToolDefinition(name="search_web", description="Search the web.")],
        system_prompt="Follow the operating rules.",
        additional_instructions=["Always cite uncertainty."],
    )

    prompt = agent.build_system_prompt(
        memory,
        prompt_context=OpenClawPromptContext(timezone_identifier="Etc/UTC"),
    )

    identity_index = prompt.index("# Identity")
    tooling_index = prompt.index("# Tooling")
    safety_index = prompt.index("# Safety")
    skills_index = prompt.index("# Skills")
    workspace_index = prompt.index("# Workspace")
    current_time_index = prompt.index("# Current Time")
    system_prompt_index = prompt.index("Follow the operating rules.")
    memory_index = prompt.index("# Runtime Memory")
    extra_index = prompt.index("Always cite uncertainty.")

    assert identity_index < tooling_index < safety_index < skills_index < workspace_index
    assert workspace_index < memory_index < current_time_index < system_prompt_index < extra_index


def test_build_system_prompt_injects_workspace_files_and_markers(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    (tmp_path / "TOOLS.md").write_text("Tool rules", encoding="utf-8")
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "2026-03-21.md").write_text("Recent memory", encoding="utf-8")

    agent = load_agent_config(
        ClawAgent(
            name="WorkspaceAgent",
            workspace_path=tmp_path,
        )
    )

    prompt = agent.build_system_prompt(
        prompt_mode=OpenClawPromptMode.FULL,
        prompt_context=OpenClawPromptContext(timezone_identifier="Etc/UTC"),
    )

    assert "## AGENTS.md" in prompt
    assert "Agent rules" in prompt
    assert "## TOOLS.md" in prompt
    assert "Tool rules" in prompt
    assert "## SOUL.md\n[missing]" in prompt
    assert "## memory/*.md" in prompt
    assert "Recent memory" in prompt


def test_build_system_prompt_minimal_mode_limits_workspace_injection(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    (tmp_path / "TOOLS.md").write_text("Tool rules", encoding="utf-8")
    (tmp_path / "SOUL.md").write_text("Soul rules", encoding="utf-8")

    agent = load_agent_config(ClawAgent(name="MinimalAgent", workspace_path=tmp_path))

    prompt = agent.build_system_prompt(
        prompt_mode=OpenClawPromptMode.MINIMAL,
        prompt_context=OpenClawPromptContext(timezone_identifier="Etc/UTC"),
    )

    assert "## AGENTS.md" in prompt
    assert "## TOOLS.md" in prompt
    assert "## SOUL.md" not in prompt


def test_build_system_prompt_shared_session_skips_curated_memory(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    (tmp_path / "MEMORY.md").write_text("Curated memory", encoding="utf-8")
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "2026-03-21.md").write_text("Recent memory", encoding="utf-8")

    agent = load_agent_config(ClawAgent(name="SharedAgent", workspace_path=tmp_path))

    prompt = agent.build_system_prompt(
        prompt_mode=OpenClawPromptMode.FULL,
        prompt_context=OpenClawPromptContext(timezone_identifier="Etc/UTC"),
        session_context=OpenClawSessionContext(
            scope=OpenClawSessionScope.SHARED,
            session_id="group-123",
        ),
    )

    assert "## MEMORY.md" not in prompt
    assert "Curated memory" not in prompt
    assert "## memory/*.md" in prompt
    assert "Recent memory" in prompt
    assert "Session scope: shared" in prompt
    assert "Session id: group-123" in prompt


def test_build_agentica_agent_returns_agentica_ready_config() -> None:
    memory = ClawMemory(MemoryConfig(enabled=False))
    agent = ClawAgent(name="Assistant")

    compiled = build_agentica_agent(agent, memory=memory)

    assert compiled.model == "anthropic/claude-sonnet-4-20250514"
    assert "memory" in compiled.scope
    assert compiled.system_prompt


def test_load_agent_config_loads_adjacent_skills(tmp_path: Path) -> None:
    agent_file = tmp_path / "agent.yaml"
    agent_file.write_text(
        """
name: Skillful
description: Uses local skills
""".strip()
    )

    skill_dir = tmp_path / "skills" / "hello_world"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: hello-world
description: A simple hello world skill
tools:
  - name: say_hello
    description: Returns a greeting message.
---
# Skill: Hello World
Use the greeting tool when helpful.
"""
    )
    (skill_dir / "tools.py").write_text(
        """def say_hello() -> str:
    \"\"\"Returns a greeting message.\"\"\"
    return "Hello"
"""
    )

    agent = load_agent_config(agent_file)

    assert len(agent.skills) == 1
    assert agent.skills[0].name == "hello-world"
