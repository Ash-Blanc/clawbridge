# GEMINI.md - clawbridge Project Context

## Project Overview
**clawbridge** is a Python toolkit for building OpenClaw-style agents inside existing frameworks such as Agno and Agentica. It supports portable skills (`SKILL.md`), persistent cross-session memory, and standardized agent definitions that compile into framework-native objects via builder functions.

### Key Technologies
- **Python 3.12+**: Utilizes modern Python features and type hinting.
- **Pydantic v2**: Core data modeling and validation for agents, skills, and memory.
- **Backends**: 
    - **Agno**: High-performance declarative agent framework.
    - **Agentica**: Code-centric framework using live Python scope objects.
- **OpenClaw Patterns**: Native support for `SKILL.md` parsing and local persistent memory.
- **CLI**: Built with `rich` for a polished terminal experience.

### Architecture
- `ClawAgent`: An OpenClaw-style Pydantic model defining the agent's identity, model, skills, tools, and behavior.
- `builders.py`: Framework-native entry points (`build_agno_agent()`, `build_agentica_agent()`, `load_agent_config()`) that compile a `ClawAgent` into a backend-specific native object.
- `ClawSkill`: Handles parsing of `SKILL.md` files (YAML frontmatter + Markdown instructions) and extracts tool definitions.
- `ClawMemory`: A framework-independent persistence layer providing long-term facts/preferences and short-term conversation history, backed by local JSON storage.
- `ClawBackend`: An abstract protocol implemented by framework adapters (`AgnoBackend`, `AgenticaBackend`).

---

## Building and Running

### Installation
The project uses `uv` for dependency management.
```bash
# Install all dependencies including backends
uv sync --extra all
```

### Key Commands
- **Interactive Chat**: 
  ```bash
  clawbridge run --name Molty --backend agno --provider anthropic --model claude-sonnet-4-20250514
  ```
- **List Skills**:
  ```bash
  clawbridge skills --dir ./skills
  ```
- **Serve as API**:
  ```bash
  clawbridge serve --backend agno --port 8000
  ```

### Development & Testing
- **Run Tests**: `pytest`
- **Linting**: `ruff check src/`
- **Formatting**: `ruff format src/`
- **Type Checking**: `mypy src/`

---

## Development Conventions

### Coding Style
- **Type Safety**: Mandatory type hints for all public APIs. Use `from __future__ import annotations`.
- **Validation**: Use Pydantic models for all configuration and state objects (`ClawAgent`, `ModelConfig`, etc.).
- **Lazy Imports**: Backend-specific dependencies (like `agno` or `agentica`) must be lazily imported within backend classes to avoid requiring all users to install every framework.
- **Extensibility**: Follow the `ClawBackend` protocol when adding new frameworks.

### Project Structure
- `src/clawbridge/core/`: Core universal models (agent, memory, skill, tool).
- `src/clawbridge/backends/`: Framework-specific adapters.
- `src/clawbridge/skills/`: Logic for loading and registering skills from disk or remote sources.
- `examples/`: Deployment scripts for various frameworks.

### Skill System
Skills are stored in directories containing a `SKILL.md` file. 
- Frontmatter defines the tool schema (parameters, types).
- Markdown body provides the natural language instructions injected into the system prompt.
- Implementation for tools defined in skills must be provided via the `ClawAgent.tools` list with matching names.

### Memory Persistence
- Long-term memory is stored in `.clawbridge/long_term.json` (default path).
- Memory categories (e.g., `preference`, `fact`) are automatically injected into system prompts as Markdown headers.
- Conversation history is maintained in-memory and trimmed based on `max_context_messages`.
