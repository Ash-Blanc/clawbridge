<p align="center">
  <img src="https://raw.githubusercontent.com/clawbridge/clawbridge/main/assets/logo.png" alt="clawbridge logo" width="200"/>
</p>

<h1 align="center">clawbridge</h1>

<p align="center">
  <strong>Build and deploy OpenClaw-style agents in frameworks like Agno and Agentica.</strong>
</p>

## What Is clawbridge?

`clawbridge` is a Python toolkit for building [OpenClaw](https://github.com/openclawai/openclaw)-style agents inside frameworks like [Agno](https://agno.com) and Agentica. Define agents in YAML, organize skills in directories, enable persistent memory and learning — then compile to framework-native objects.

Key capabilities:
- **OpenClaw workspaces** — `AGENTS.md`, `MEMORY.md`, `BOOTSTRAP.md`, skills directories
- **Hermes-like features** — persistent memory, self-improvement, cross-session recall
- **Multi-agent teams** — coordinate, route, broadcast, or run task lists
- **Framework-native execution** — `build_agno_agent()` and `build_agno_team()` return real Agno objects

## Install

```bash
pip install clawbridge[agno]
```

For development:

```bash
git clone https://github.com/Ash-Blanc/clawbridge.git
cd clawbridge
uv sync --extra dev --extra all
```

## Quick Start

```bash
clawbridge scaffold ./my-workspace
cd my-workspace
```

```python
from clawbridge import build_agno_agent, load_agent_config

agent = load_agent_config("./agent.yaml")
native_agent = build_agno_agent(agent)
native_agent.print_response("What can you do?")
```

## Build An Agent

```python
from clawbridge import ClawAgent, ModelConfig, build_agno_agent

agent = ClawAgent(
    name="Molty",
    description="A helpful assistant",
    personality="Helpful, clear, and concise.",
    model=ModelConfig(provider="anthropic", model="claude-sonnet-4-20250514"),
)

native_agent = build_agno_agent(agent)
native_agent.print_response("Say hello and tell me what you can do.")
```

Agno reads `ANTHROPIC_API_KEY` from the environment automatically.

## Hermes-Like Features

Build agents with persistent memory, self-improvement, and cross-session recall — the patterns that make [Hermes-agent](https://github.com/nousresearch/hermes-agent) compelling, powered by Agno's native runtime.

### Persistent Memory

```python
from clawbridge import (
    ClawAgent, AgentMemoryMode, ModelConfig, StorageConfig, build_agno_agent,
)

agent = ClawAgent(
    name="Molty",
    description="A personal assistant that remembers you",
    model=ModelConfig(provider="openai", model="gpt-4o"),
    storage=StorageConfig(enabled=True, type="sqlite", db_url="agent.db"),
    agent_memory_mode=AgentMemoryMode.AUTOMATIC,
)

native_agent = build_agno_agent(agent)
native_agent.print_response("My name is Alice and I prefer email over Slack.")
native_agent.print_response("What's the best way to reach me?")
```

### Self-Improvement (Learning)

```python
from clawbridge import ClawAgent, LearningConfig, SessionConfig, StorageConfig, build_agno_agent

agent = ClawAgent(
    name="Molty",
    learning=LearningConfig(enabled=True),
    session=SessionConfig(search_past_sessions=True),
    storage=StorageConfig(enabled=True, type="sqlite", db_url="agent.db"),
)
```

### Cross-Session Recall

```python
agent = ClawAgent(
    name="Molty",
    session=SessionConfig(
        search_past_sessions=True,
        num_past_sessions_to_search=5,
        enable_session_summaries=True,
    ),
)
```

For full details, see the [Hermes Features guide](https://clawbridge.dev/docs/guides/hermes-features).

## Multi-Agent Teams

Coordinate specialized agents with `build_agno_team()`:

```python
from clawbridge import ClawAgent, TeamConfig, TeamMode, ModelConfig, build_agno_team

team = TeamConfig(
    name="Research Team",
    mode=TeamMode.COORDINATE,
    members=[
        ClawAgent(name="Researcher", role="Find information", model=ModelConfig(provider="openai", model="gpt-4o")),
        ClawAgent(name="Writer", role="Summarize findings", model=ModelConfig(provider="openai", model="gpt-4o")),
    ],
)

native_team = build_agno_team(team)
native_team.print_response("Research the latest AI agent frameworks")
```

Four modes: `coordinate`, `route`, `broadcast`, `tasks`. See the [Teams guide](https://clawbridge.dev/docs/guides/teams) for details.

## Add An OpenClaw Skill

Create a skill folder:

```text
skills/web_search/
  SKILL.md
  tools.py
```

```python
def search_web(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"
```

Then attach it:

```python
from pathlib import Path
from clawbridge import ClawAgent, ClawSkill, build_agno_agent

skill = ClawSkill.from_skill_md(Path("./skills/web_search"))
agent = ClawAgent(name="Molty", skills=[skill])
native_agent = build_agno_agent(agent)
```

## Memory Helpers

`ClawMemory` is a lightweight helper for OpenClaw-style memory injection:

```python
from clawbridge import ClawMemory

memory = ClawMemory()
memory.remember("user_name", "Alice", category="preference")
print(memory.recall("user_name"))
```

For persistent cross-session memory, use the Hermes-like features above.

## CLI

```bash
clawbridge scaffold ./my-workspace
clawbridge run --name Molty --framework agno --provider anthropic
clawbridge skills --dir ./skills
clawbridge serve --port 8000
```

## Development

```bash
uv run ruff check src tests
uv run pytest
```
