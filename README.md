<p align="center">
  <img src="https://raw.githubusercontent.com/clawbridge/clawbridge/main/assets/logo.png" alt="clawbridge logo" width="200"/>
</p>

<h1 align="center">clawbridge</h1>

<p align="center">
  <strong>OpenClaw-style skills, prompts, and helpers for Agno and Agentica.</strong>
</p>

## What Is clawbridge?

`clawbridge` is not a meta-framework and it does not try to unify agent runtimes.

It helps you build OpenClaw-style agents inside frameworks you already want to use:

- Agno
- Agentica
- more adapters over time

The shared value is OpenClaw conventions:

- `ClawAgent` for OpenClaw-style agent config
- `ClawSkill` for `SKILL.md` packages and callable tools
- `ClawMemory` for lightweight memory helpers
- framework-native builders like `build_agno_agent()` and `build_agentica_agent()`

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

## Build A Native Agno Agent

```python
from clawbridge import ClawAgent, ModelConfig, build_agno_agent

agent = ClawAgent(
    name="Molty",
    description="A helpful assistant",
    personality="Helpful, clear, and concise.",
    model=ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        api_key_env="ANTHROPIC_API_KEY",
    ),
)

native_agent = build_agno_agent(agent)
response = native_agent.run("Say hello and tell me what you can do.")
print(getattr(response, "content", response))
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
