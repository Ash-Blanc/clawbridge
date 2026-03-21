# Agent Guidelines for clawbridge

This file provides guidance for agents working on the `clawbridge` codebase.

## Project Overview

`clawbridge` is a Python toolkit for building OpenClaw-style agents inside existing frameworks such as Agno and Agentica. It is workspace-first, builder-based, and does not use a universal runtime abstraction. Requires Python 3.12+.

The main product surfaces are:

- OpenClaw workspace loading and prompt composition
- skill loading and precedence resolution
- framework-native builders such as `build_agno_agent()` and `build_agentica_agent()`
- optional Agno deployment helpers like `clawbridge dev` and `clawbridge init`

## Build/Lint/Test Commands

### Installation

```bash
uv sync --extra dev --extra all
pip install clawbridge[dev,all]
```

### Running Tests

```bash
pytest
pytest tests/test_file.py
pytest tests/test_file.py::test_func
pytest -k "pattern"
pytest -v
pytest --cov=src/clawbridge
```

### Linting & Formatting

```bash
ruff check src tests
ruff check src tests --fix
ruff format src tests
mypy src
```

### CLI Commands

```bash
clawbridge scaffold ./my-workspace
clawbridge run --name Molty --framework agno --provider anthropic
clawbridge skills --dir ./skills
clawbridge serve --port 8000
```

## Code Style Guidelines

### General Principles

- **KISS**: prefer simple, readable solutions over clever abstractions
- **Pydantic everywhere**: use Pydantic models for structured config and runtime state
- **Type hints required**: all functions should have type hints
- **Python 3.12+**: use modern Python features where they improve clarity

### Imports

- Use absolute imports: `from clawbridge.core.agent import ClawAgent`
- Group imports as stdlib, third-party, local
- Use `from __future__ import annotations` in all files

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
```

### Naming Conventions

- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### File Organization

```text
src/clawbridge/
├── __init__.py          # Public API exports
├── builders.py          # Framework-native entrypoints
├── cli.py               # CLI entrypoint
├── scaffold.py          # Workspace scaffold helpers
├── app.py               # Optional Agno deployment helper
├── backends/            # Framework adapters
│   ├── base.py, agno.py, agentica.py
├── core/                # OpenClaw models and runtime semantics
│   ├── agent.py, workspace.py, prompt.py, skill.py
│   ├── session.py, sandbox.py, channel.py, multi_agent.py
│   ├── memory.py, tool.py, types.py
└── skills/              # Skill discovery and registry helpers
    ├── loader.py, registry.py
```

### Pydantic Models

```python
class MyModel(BaseModel):
    """Docstring for the model."""

    name: str = "default"
    count: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}
```

### Docstrings

Use concise Google-style docstrings for non-trivial functions:

```python
def compile(self) -> Any:
    """Compile a ClawAgent into a framework-native object.

    Returns:
        The compiled native agent object or config.

    Raises:
        ValueError: If configuration is invalid.
    """
```

### Error Handling

- Use specific exceptions when available
- Raise descriptive errors with context
- Do not silently swallow invalid config

```python
if not isinstance(data, dict):
    raise ValueError("Agent config must deserialize to a mapping.")
```

### Async Patterns

Provide both async and sync convenience paths where useful:

```python
async def run(self, message: str, session_id: str = "default") -> str:
    ...

def run_sync(self, message: str, session_id: str = "default") -> str:
    import asyncio
    return asyncio.run(self.run(message, session_id))
```

### Backend Protocol

Framework adapters implement `ClawBackend` and work from `ClawAgent` plus `ClawMemory`:

```python
class ClawBackend(ABC):
    name: str

    def __init__(self, agent: ClawAgent, memory: ClawMemory | None = None):
        self.agent = agent
        self.memory = memory or ClawMemory(agent.memory_config)

    @abstractmethod
    def compile(self) -> Any: ...

    @abstractmethod
    async def run(self, message: str, session_id: str = "default") -> str: ...
```

### Builder Entry Points

The main load/build flow is:

1. `load_agent_config(...)` normalizes a `ClawAgent`, YAML/JSON config, or `MultiAgentConfig`
2. workspace files are loaded from `workspace_path` or an adjacent workspace
3. skills are resolved with precedence and gating
4. `build_agno_agent(...)` or `build_agentica_agent(...)` returns the native runtime object/config

### Adding a New Framework Adapter

1. Create `src/clawbridge/backends/<name>.py` implementing `ClawBackend`
2. Add a public builder in `src/clawbridge/builders.py`
3. Export the builder from `src/clawbridge/__init__.py` if it is part of the public API
4. Add tests for compile/runtime behavior and config mapping

### Testing Guidelines

- Tests live in `tests/`
- Use `pytest`
- Name files `test_*.py` and functions `test_*`
- Mock external API calls and optional integrations where possible
- Prefer coverage for workspace loading, prompt composition, skill resolution, and builder behavior

### Public API Exports

Keep `__init__.py` focused on stable surfaces:

- `ClawAgent`, `ClawSkill`, `ClawMemory`
- workspace, prompt, session, sandbox, and channel policy types
- `MultiAgentConfig`
- `create_openclaw_workspace`
- `build_agno_agent()`, `build_agentica_agent()`, `load_agent_config()`

When editing docs or code comments, prefer the current product language:

- say **OpenClaw-style workspace**, **builder**, **framework-native object**, **optional Agno deployment helper**
- do not reintroduce **ClawBridge**, **portable runtime**, **meta-framework**, or backend-switching language
