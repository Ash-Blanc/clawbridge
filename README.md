<p align="center">
  <img src="https://raw.githubusercontent.com/clawbridge/clawbridge/main/assets/logo.png" alt="clawbridge logo" width="200"/>
</p>

<h1 align="center">clawbridge</h1>

<p align="center">
  <strong>Build AI agents in Python with skills, memory, and a clean starting point.</strong>
</p>

## What Is clawbridge?

`clawbridge` is a Python framework for building OpenClaw-style agents without forcing you to learn a large runtime up front.

It gives you a small set of beginner-friendly building blocks:

- `ClawAgent` for the agent itself
- `ClawBridge` for running it
- `ClawSkill` for reusable skills
- `ClawMemory` for remembering things between chats

The first goal is simple: get a working agent running quickly.

## Start Here

If you are new, use this order:

1. Install the project
2. Build your first agent
3. Add one skill
4. Add memory
5. Explore advanced runtime details later

## Install

```bash
uv sync --extra all
```

## Your First Agent

What you will build:

- one runnable agent
- one backend-backed chat loop
- one place to add skills and memory later

```python
from clawbridge import ClawAgent, ClawBridge, ModelConfig

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

bridge = ClawBridge(agent, backend="agno")
print(bridge.chat("Say hello and tell me what you can do."))
```

What you just built:

- a `ClawAgent`
- a `ClawBridge`
- a minimal working agent you can extend

## Add A Skill

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

Then load it:

```python
from pathlib import Path

from clawbridge import ClawAgent, ClawBridge, ClawSkill

skill = ClawSkill.from_skill_md(Path("./skills/web_search"))

agent = ClawAgent(name="Molty", skills=[skill])
bridge = ClawBridge(agent, backend="agno")
```

## Add Memory

```python
bridge.memory.remember("user_name", "Alice", category="preference")
print(bridge.memory.recall("user_name"))
```

## CLI

```bash
clawbridge run --name Molty --backend agno --provider anthropic
clawbridge skills --dir ./skills
clawbridge serve --backend agno --port 8000
```

## Learn Next

If you are new, this is the order to follow:

1. Build your first agent
2. Add one skill
3. Add memory
4. Try the CLI
5. Only then look at advanced topics like backend-specific behavior or app mode

## Advanced Notes

`clawbridge` also supports:

- loading OpenClaw-style `SKILL.md` packages
- switching between supported backends
- Agno-specific compile and app-mode helpers

Those are useful, but they are not the first thing a new user needs to understand.

## Development

```bash
uv run ruff check src tests
uv run pytest
```
