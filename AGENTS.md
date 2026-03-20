# Agent Guidelines for clawbridge

This file provides guidelines for agents working on the clawbridge codebase.

## Project Overview

clawbridge is a Python meta-framework for deploying OpenClaw-style agents to any AI agent framework (Agno, Agentica, etc.). Requires Python 3.12+.

## Build/Lint/Test Commands

### Installation
```bash
uv sync --extra dev --extra all           # Using uv (recommended)
pip install clawbridge[dev,all]          # Or using pip
```

### Running Tests
```bash
pytest                                    # Run all tests
pytest tests/test_file.py                 # Single test file
pytest tests/test_file.py::test_func      # Single test function
pytest -k "pattern"                      # Tests matching pattern
pytest -v                                 # Verbose output
pytest --cov=src/clawbridge               # With coverage
```

### Linting & Formatting
```bash
ruff check src/                           # Lint
ruff check src/ --fix                     # Auto-fix issues
ruff format src/                          # Format code
mypy src/                                 # Type check
```

### CLI Commands
```bash
clawbridge run --name Molty --backend agno --provider anthropic
clawbridge skills --dir ./skills
clawbridge serve --backend agno --port 8000
```

## Code Style Guidelines

### General Principles
- **KISS**: Prefer simple, readable solutions over clever ones
- **Pydantic everywhere**: Use Pydantic models for all data structures and configuration
- **Type hints required**: All functions must have type hints
- **Python 3.12+**: Use modern features (pattern matching, built-in types as type hints)

### Imports
- Use absolute imports: `from clawbridge.core.agent import ClawAgent`
- Group: stdlib, third-party, local — sorted alphabetically
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
- **Classes**: `PascalCase` (e.g., `ClawAgent`, `AgnoBackend`)
- **Functions/methods**: `snake_case` (e.g., `build_system_prompt`)
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Type variables**: `PascalCase` (e.g., `T`, `AgentT`)

### File Organization
```
src/clawbridge/
├── __init__.py          # Public API exports only
├── bridge.py            # Main orchestrator
├── cli.py               # CLI entrypoint
├── core/                # Domain models
│   ├── agent.py, memory.py, skill.py, tool.py, types.py
├── backends/            # Framework adapters
│   ├── base.py, agno.py, agentica.py
└── skills/             # Skill loading
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
Use Google-style docstrings with Description, Args, Returns, Raises:

```python
def compile(self) -> Any:
    """Compile the universal ClawAgent into native agent.
    
    Returns:
        The compiled native agent object.
    
    Raises:
        ValueError: If configuration is invalid.
    """
```

### Error Handling
- Use specific exceptions when available
- Raise descriptive errors with context
- Don't catch silently without documentation

```python
if backend.value not in self._backend_registry:
    raise ValueError(f"Unknown backend: {backend.value}. Valid: {list(Backend)}")
```

### Async Patterns
Provide both sync and async versions; use `run_sync()` for async backends:

```python
async def achat(self, message: str) -> str:
    return await self._backend.run(message)

def chat(self, message: str) -> str:
    return asyncio.run(self.achat(message))
```

### Backend Protocol
All backends must implement `ClawBackend`:

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

### Lazy Backend Imports
Import backends inside methods to avoid requiring unused dependencies:

```python
def _create_backend(self, backend: Backend) -> ClawBackend:
    match backend:
        case Backend.AGNO:
            from clawbridge.backends.agno import AgnoBackend
            return AgnoBackend(self.agent, self._memory)
        case Backend.AGENTICA:
            from clawbridge.backends.agentica import AgenticaBackend
            return AgenticaBackend(self.agent, self._memory)
```

### Testing Guidelines
- Tests in `tests/` directory at root
- Use `pytest` — name files `test_*.py`, functions `test_*`
- Mock external API calls (LLM providers)

### Adding a New Backend
1. Create `src/clawbridge/backends/<name>.py` implementing `ClawBackend`
2. Add to `Backend` enum in `core/types.py`
3. Add case in `bridge.py::_create_backend()`
4. Add tests

### Public API Exports
Only export stable APIs in `__init__.py`:

```python
__all__ = [
    "ClawAgent", "ClawBridge", "ClawMemory", "ClawSkill",
    "Backend", "LLMProvider", "MemoryConfig", "ModelConfig",
    "ToolDefinition", "ToolParameter", "create_agent",
]
```
