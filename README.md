<p align="center">
  <img src="https://raw.githubusercontent.com/clawbridge/clawbridge/main/assets/logo.png" alt="clawbridge logo" width="200"/>
</p>

<h1 align="center">clawbridge</h1>

<p align="center">
  <strong>Define OpenClaw-inspired agents once. Run them on supported backends.</strong>
</p>

<p align="center">
  <a href="#what-it-is">What It Is</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#core-model">Core Model</a> •
  <a href="#support-matrix">Support Matrix</a> •
  <a href="#app-mode">App Mode</a> •
  <a href="#development">Development</a>
</p>

## What It Is

`clawbridge` is a Python meta-framework for **portable agent definitions**.

It gives you a backend-neutral core built around:

- `ClawAgent` for identity, model config, skills, tools, memory, and behavior
- `ClawSkill` for OpenClaw-style `SKILL.md` or code-first skill directories
- `ClawMemory` for framework-independent memory
- `ClawBridge` for compiling and running the same agent on different runtimes

The main workflow is:

1. Define a `ClawAgent`
2. Load skills and tools
3. Run it through `ClawBridge` on a backend such as Agno or Agentica

`compile_to_agno()` and `ClawApp` still exist, but they are **backend-specific convenience layers**, not the center of the framework.

## Quickstart

### Install

```bash
uv sync --extra dev --extra all
```

### Define one agent and run it on a backend

```python
from clawbridge import ClawAgent, ClawBridge, ModelConfig

agent = ClawAgent(
    name="Molty",
    description="A portable personal assistant",
    personality="Helpful, direct, and concise.",
    model=ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        api_key_env="ANTHROPIC_API_KEY",
    ),
)

bridge = ClawBridge(agent, backend="agno")
print(bridge.chat("What can you help with?"))
```

### Load OpenClaw-style skills

```python
from pathlib import Path

from clawbridge import ClawAgent, ClawBridge, ClawSkill, ToolDefinition


def search_web(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"


skill = ClawSkill.from_skill_md(Path("./skills/web_search"))

agent = ClawAgent(
    name="Molty",
    skills=[skill],
    tools=[
        ToolDefinition(
            name="search_web",
            description="Search the web",
            callable=search_web,
        )
    ],
)

bridge = ClawBridge(agent, backend="agno")
print(bridge.chat("Search for recent agent tooling news"))
```

### Switch backends while keeping shared memory

```python
bridge.memory.remember("user_name", "Alice", category="preference")
bridge.switch_backend("agentica")
print(bridge.memory.recall("user_name"))
```

The memory object is shared across backend instances. The exact native behavior still depends on each backend's implementation.

## Core Model

### Portable core

These are the primary concepts `clawbridge` is built around:

- `ClawAgent`: the backend-neutral source of truth
- `ClawBridge`: runtime wrapper for supported backends
- `ClawSkill`: parsed skill package from `SKILL.md`, `tools.py`, or `main.py`
- `ClawMemory`: framework-independent memory store
- `ToolDefinition`: portable tool metadata plus optional Python callable

### Backend-specific helpers

- `compile_to_agno()`: compile a `ClawAgent` or YAML/JSON definition directly to Agno
- `ClawApp`: Agno app-mode compiler that scans `agents/`, `skills/`, and `claw.config.yaml`

### Current support boundaries

Some `ClawAgent` fields are portable today, while others are best understood as backend extensions:

- Portable and stable: identity, model config, skills, direct tools, prompt assembly, memory object
- Partially backend-specific: storage, knowledge, channels, serving
- Backend-dependent semantics: native memory/storage integration, knowledge ingestion, live-object execution in Agentica

## Support Matrix

| Capability | Agno | Agentica |
| --- | --- | --- |
| `ClawAgent` compile/run | Supported | Supported |
| `ClawBridge.chat()` / `achat()` | Supported | Supported |
| `ClawSkill` loading | Supported | Supported |
| Direct callable tools | Supported | Supported |
| Placeholder skill tools without callables | Supported | Supported |
| Shared `ClawMemory` object across backend switch | Supported in bridge layer | Supported in bridge layer |
| Native backend storage from `storage` config | Supported | Not implemented |
| Knowledge config | Partial | Not implemented |
| Channels / gateways | Partial | Not implemented |
| Native direct compile helper | `compile_to_agno()` | None |
| App-mode filesystem compiler | Agno only | None |

If you need native framework primitives, prefer the backend-specific helpers and read the backend docs before assuming feature parity.

## App Mode

`clawbridge` also includes an optional Agno-oriented app mode:

```text
agents/*.yaml
skills/*/SKILL.md
skills/*/tools.py
knowledge/
claw.config.yaml
```

This mode is useful if you want a filesystem-driven project layout and Agno `AgentOS` serving.

Use it when:

- you want local Agno app scaffolding
- your deployment target is Agno
- convention-over-configuration is more important than backend portability

Do not treat app mode as the portable core API. It is a convenience workflow layered on top of the core models.

## Development

### Install

```bash
uv sync --extra dev --extra all
```

### Tests

```bash
pytest
pytest tests/test_bridge_runtime.py
pytest tests/test_code_first_skill.py
```

### Lint and type-check

```bash
ruff check src tests
ruff format src tests
mypy src
```

## Project Status

This revamp intentionally prefers **strict truth over aspirational claims**.

The project already has a useful portable core. The main gap now is not the existence of the core, but making the docs and public story consistently reflect:

- what is portable today
- what is Agno-specific
- what is partial or roadmap

That is the standard the docs and tests in this repository now follow.
