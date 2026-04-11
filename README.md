<p align="center">
  <img src="https://raw.githubusercontent.com/clawbridge/clawbridge/main/assets/logo.png" alt="clawbridge logo" width="200"/>
</p>

<h1 align="center">clawbridge</h1>

<p align="center">
  <strong>Build and deploy OpenClaw-style agents in frameworks like Agno and Agentica.</strong>
</p>

## What Is clawbridge?

`clawbridge` is not a meta-framework and it does not try to unify agent runtimes.

It helps you build and deploy OpenClaw-style agents inside frameworks you already want to use:

- Agno
- Agentica
- more adapters over time

With the Agno 2.5 integration, `clawbridge` also supports Hermes-like patterns: agents with persistent memory, self-improvement across sessions, and cross-session recall.

The shared value is OpenClaw conventions plus framework-native execution:

- `ClawAgent` for OpenClaw-style agent config
- OpenClaw workspace files like `AGENTS.md`, `BOOTSTRAP.md`, and `MEMORY.md`
- `ClawSkill` for `SKILL.md` packages and callable tools
- `ClawMemory` for lightweight memory helpers
- framework-native builders like `build_agno_agent()` and `build_agentica_agent()`
- deployment entrypoints like `clawbridge serve` where the target framework supports them

Model configuration is no longer limited to a fixed enum. `ModelConfig.provider` accepts known providers like `anthropic`, `openai`, and `mistral`, plus arbitrary LiteLLM-compatible provider strings when the target framework can route them.

## Install

```bash
uv sync --extra all
```

## Start With A Workspace

The default onboarding path is an OpenClaw workspace:

```bash
clawbridge scaffold ./my-workspace
cd ./my-workspace
clawbridge run --name Assistant --framework agno
```

If you want a starter multi-agent layout:

```bash
clawbridge scaffold ./my-workspace --multi-agent
```

Today, Agno has the most complete deployment path in the repo. Agentica support is strong for agent construction and runtime config, but not at Agno parity for deployment.

## Build A Native Agno Agent

```python
from clawbridge import ClawAgent, ModelConfig, build_agno_agent

agent = ClawAgent(
    name="Molty",
    description="A helpful assistant",
    personality="Helpful, clear, and concise.",
    model=ModelConfig(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        api_key="ANTHROPIC_API_KEY",
    ),
)

native_agent = build_agno_agent(agent)
response = native_agent.run("Say hello and tell me what you can do.")
print(getattr(response, "content", response))
```

For Mistral, use:

```python
ModelConfig(
    provider="mistral",
    model="mistral-large-latest",
    api_key="MISTRAL_API_KEY",
)
```

## Hermes-Like Features

Build agents with persistent memory, self-improvement, and cross-session recall — the patterns that make [Hermes-agent](https://github.com/nousresearch/hermes-agent) compelling, powered by Agno's native runtime.

### Persistent Memory

The agent automatically remembers user preferences and facts across sessions:

```python
from clawbridge import (
    ClawAgent, AgentMemoryMode, ModelConfig, StorageConfig, build_agno_agent,
)

agent = ClawAgent(
    name="Molty",
    description="A personal assistant that remembers you",
    personality="Helpful, concise, and learns from every interaction.",
    model=ModelConfig(provider="openai", model="gpt-4o"),
    storage=StorageConfig(enabled=True, type="sqlite", db_url="agent.db"),
    agent_memory_mode=AgentMemoryMode.AUTOMATIC,
)

native_agent = build_agno_agent(agent)

# First conversation — agent learns your preferences
native_agent.print_response("My name is Alice and I prefer email over Slack.")

# Later conversation — agent recalls without being told
native_agent.print_response("What's the best way to reach me?")
```

Use `AgentMemoryMode.AGENTIC` to give the agent full control over what it remembers.

### Self-Improvement (Learning)

The agent stores learnings from past runs and improves over time:

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

Search past conversations for relevant context:

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

### All Together

Combine everything for the full Hermes-like experience:

```python
agent = ClawAgent(
    name="Molty",
    description="A self-improving personal assistant",
    personality="Helpful and learns from every interaction.",
    model=ModelConfig(provider="anthropic", model="claude-sonnet-4-20250514"),
    storage=StorageConfig(enabled=True, type="sqlite", db_url="agent.db"),
    agent_memory_mode=AgentMemoryMode.AUTOMATIC,
    learning=LearningConfig(enabled=True),
    session=SessionConfig(
        search_past_sessions=True,
        enable_session_summaries=True,
        compress_tool_results=True,
        reasoning=True,
    ),
)

native_agent = build_agno_agent(agent)
```

## Deploy With Agno

If you want a native serving path, Agno is the first-class deployment target today:

```bash
clawbridge serve --port 8000
```

For filesystem-driven Agno deployment, the optional helper flow is still available:

```bash
clawbridge init my-agno-helper
cd my-agno-helper
clawbridge dev
```

## Build An Agentica Agent

```python
from clawbridge import ClawAgent, build_agentica_agent

agent = ClawAgent(
    name="Molty",
    personality="Helpful, clear, and concise.",
)

agentica_config = build_agentica_agent(agent)
```

`build_agentica_agent()` gives you an Agentica-ready config and runtime prompt/scope wiring. Deployment ergonomics there are still thinner than Agno.

## Add An OpenClaw Skill

Create a skill folder:

```text
skills/web_search/
  SKILL.md
  tools.py
```

Example `tools.py`:

```python
def search_web(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"
```

Then attach it to the agent:

```python
from pathlib import Path

from clawbridge import ClawAgent, ClawSkill, build_agno_agent

skill = ClawSkill.from_skill_md(Path("./skills/web_search"))
agent = ClawAgent(name="Molty", skills=[skill])
native_agent = build_agno_agent(agent)
```

## Memory Helpers

`ClawMemory` is a lightweight helper for OpenClaw-style memory injection. It is not a claim of cross-framework memory parity.

```python
from clawbridge import ClawMemory

memory = ClawMemory()
memory.remember("user_name", "Alice", category="preference")
print(memory.recall("user_name"))
```

## CLI

```bash
clawbridge scaffold ./my-workspace
clawbridge run --name Molty --framework agno --provider anthropic
clawbridge skills --dir ./skills
clawbridge serve --port 8000
```

Use `clawbridge scaffold` for OpenClaw-style workspace onboarding.

`clawbridge dev` and `clawbridge init` remain available as optional Agno deployment helpers.

## Migration From `init`

If you previously started with `clawbridge init`, the new split is:

1. Use `clawbridge scaffold` when you want an OpenClaw-style workspace with `AGENTS.md`, `BOOTSTRAP.md`, `MEMORY.md`, starter skills, and optional multi-agent config.
2. Use `clawbridge init` only when you specifically want the optional Agno deployment helper.

## Development

```bash
uv run ruff check src tests
uv run pytest
```
