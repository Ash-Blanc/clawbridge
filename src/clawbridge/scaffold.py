"""Project scaffolding helpers for OpenClaw-style workspaces."""

from __future__ import annotations

from pathlib import Path


STANDARD_WORKSPACE_FILES = [
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "IDENTITY.md",
    "USER.md",
    "HEARTBEAT.md",
    "BOOTSTRAP.md",
    "MEMORY.md",
]


def create_openclaw_workspace(
    target_dir: str | Path,
    *,
    agent_name: str = "Assistant",
    include_multi_agent: bool = False,
    force: bool = False,
) -> Path:
    """Create an OpenClaw workspace scaffold with starter files."""
    workspace_dir = Path(target_dir).expanduser().resolve()

    if workspace_dir.exists():
        if not workspace_dir.is_dir():
            raise FileExistsError(
                f"Cannot scaffold workspace because target is not a directory: {workspace_dir}"
            )
        if not force and any(workspace_dir.iterdir()):
            raise FileExistsError(
                "Workspace directory already exists and is not empty. "
                "Use force=True to scaffold anyway."
            )
    else:
        workspace_dir.mkdir(parents=True)

    _write_file(
        workspace_dir / "AGENTS.md",
        f"""# AGENTS

You are {agent_name}, operating in an OpenClaw-style workspace.

Core directives:
- Use skills and tools before improvising.
- Keep actions auditable and concise.
- Treat files in this workspace as the source of truth.
""",
    )
    _write_file(
        workspace_dir / "SOUL.md",
        """# SOUL

Default posture:
- Be pragmatic and direct.
- Avoid speculative claims.
- Prefer small, verifiable steps.
""",
    )
    _write_file(
        workspace_dir / "TOOLS.md",
        """# TOOLS

Tool usage policy:
- Use available tools when they reduce guesswork.
- Explain critical tool outputs briefly.
- If a tool is unavailable, state that clearly.
""",
    )
    _write_file(
        workspace_dir / "IDENTITY.md",
        f"""# IDENTITY

Agent name: {agent_name}
Role: General assistant
""",
    )
    _write_file(
        workspace_dir / "USER.md",
        """# USER

Add persistent user preferences and context here.
""",
    )
    _write_file(
        workspace_dir / "HEARTBEAT.md",
        """# HEARTBEAT

When heartbeat-triggered:
- Review pending tasks.
- Suggest next safe action if nothing is urgent.
""",
    )
    _write_file(
        workspace_dir / "BOOTSTRAP.md",
        """# BOOTSTRAP

First-run setup checklist:
1. Confirm your core role and constraints.
2. Verify available skills and tools.
3. Write any long-lived defaults to MEMORY.md.

After completing first-run setup, remove this file.
""",
    )
    _write_file(
        workspace_dir / "MEMORY.md",
        """# MEMORY

Store curated long-term context here.
Keep this file concise and high-signal.
""",
    )

    memory_dir = workspace_dir / "memory"
    memory_dir.mkdir(exist_ok=True)
    _write_file(memory_dir / ".gitkeep", "")

    skills_dir = workspace_dir / "skills" / "hello_world"
    skills_dir.mkdir(parents=True, exist_ok=True)
    _write_file(
        skills_dir / "SKILL.md",
        """---
name: hello-world
description: A starter skill to verify tool loading.
version: 1.0.0
tools:
  - name: say_hello
    description: Returns a greeting.
---
# Skill: Hello World
Use this skill when a quick confirmation message is useful.
""",
    )
    _write_file(
        skills_dir / "tools.py",
        '''def say_hello(name: str = "there") -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}!"
''',
    )

    _write_file(
        workspace_dir / "agent.yaml",
        f"""name: {agent_name}
description: OpenClaw workspace starter agent.
workspace_path: .
personality: Pragmatic, concise, and reliable.
model:
  provider: anthropic
  model_id: claude-sonnet-4-20250514
""",
    )

    if include_multi_agent:
        _write_file(
            workspace_dir / "agents.yaml",
            """default_agent_id: assistant
shared_skill_paths:
  - ./skills
agents:
  assistant:
    name: Assistant
    description: Workspace primary agent
    workspace_path: .
  reviewer:
    name: Reviewer
    description: Secondary reviewer agent
    workspace_path: .
allow_shared_workspaces: true
""",
        )

    return workspace_dir


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
