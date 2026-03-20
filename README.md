<p align="center">
  <img src="https://raw.githubusercontent.com/clawbridge/clawbridge/main/assets/logo.png" alt="clawbridge logo" width="200"/>
</p>

<h1 align="center">🦞 clawbridge</h1>

<p align="center">
  <strong>Define OpenClaw-style agents once. Deploy them to any framework.</strong>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> •
  <a href="#why-clawbridge">Why clawbridge?</a> •
  <a href="#installation">Installation</a> •
  <a href="#core-concepts">Core Concepts</a> •
  <a href="#backends">Backends</a> •
  <a href="#skills">Skills</a> •
  <a href="#cli">CLI</a> •
  <a href="#examples">Examples</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/clawbridge/"><img src="https://img.shields.io/pypi/v/clawbridge?color=blue&label=PyPI" alt="PyPI"></a>
  <a href="https://pypi.org/project/clawbridge/"><img src="https://img.shields.io/pypi/pyversions/clawbridge" alt="Python"></a>
  <a href="https://github.com/clawbridge/clawbridge/blob/main/LICENSE"><img src="https://img.shields.io/github/license/clawbridge/clawbridge" alt="License"></a>
  <a href="https://github.com/clawbridge/clawbridge/stargazers"><img src="https://img.shields.io/github/stars/clawbridge/clawbridge?style=social" alt="Stars"></a>
</p>

---

## What is clawbridge?

**clawbridge** is a Python meta-framework that lets you define AI agents using
[OpenClaw](https://github.com/openclaw/openclaw)-inspired patterns — skills,
persistent memory, SKILL.md files — and deploy them to mainstream agent
frameworks without rewriting anything.

Write your agent **once**. Run it on [Agno](https://github.com/agno-agi/agno),
[Agentica](https://github.com/symbolica-ai/agentica-python-sdk), or any
backend we support. Hot-swap frameworks at runtime. Keep your memory and skills
portable.

```python
from clawbridge import ClawAgent, ClawBridge, ModelConfig

agent = ClawAgent(
    name="Molty",
    personality="Helpful and witty 🦞",
    model=ModelConfig(provider="anthropic", model_id="claude-sonnet-4-20250514"),
)

# Deploy via Agno
bridge = ClawBridge(agent, backend="agno")
print(bridge.chat("What can you do?"))

# Hot-swap to Agentica — same agent, same memory
bridge.switch_backend("agentica")
print(bridge.chat("Remember anything from before?"))
```

---

## Why clawbridge?

The AI agent ecosystem is fragmented. OpenClaw pioneered a powerful pattern —
a personal AI assistant with a skills system, persistent memory, and messaging-
platform interfaces — but its architecture is tightly coupled to its own
runtime. Meanwhile, frameworks like Agno and Agentica offer excellent
infrastructure but have completely different paradigms:

| Challenge | How clawbridge solves it |
|---|---|
| **Framework lock-in** | Define agents once, compile to any backend |
| **Incompatible skill formats** | Universal `SKILL.md` parser works everywhere |
| **Lost context when switching** | Memory layer sits *above* backends, carries over |
| **Different tool paradigms** | Adapters translate tools → Agno callables, Agentica scope objects |
| **Boilerplate per framework** | One `ClawAgent` definition replaces N framework-specific configs |

### How the target frameworks differ

**OpenClaw** is a free, open-source autonomous AI agent created by Peter
Steinberger. It uses a skills system where skills are stored as directories
containing a `SKILL.md` file with metadata and instructions. It runs locally,
integrates with LLMs like Claude, DeepSeek, or GPT, and is accessed via
messaging services like WhatsApp, Telegram, Slack, and many more. Memory and
configuration are stored locally for persistent, adaptive behavior across
sessions.

**Agno** is a high-performance open-source Python framework for building
multi-modal agents. It provides a declarative `Agent` class with pluggable
models, tools, memory, knowledge stores, and team composition — all with a
clean Pythonic API. Agno emphasizes production readiness with features like
session-scoped FastAPI serving, AgentOS monitoring, and native tracing.

**Agentica** (by Symbolica) is a type-safe framework built on the premise that
code is the most expressive interface for model interaction. Instead of JSON
tool-calling, you pass live Python objects into an agent's scope — the agent
discovers capabilities through methods and the scope grows dynamically. It uses
`@agentic()` decorated functions with runtime type enforcement and sandboxed
code execution via remote object proxying.

clawbridge bridges all of these worlds.

---

## Installation

Requires **Python 3.12+**.

```bash
# Core only (no backend dependencies)
pip install clawbridge

# With Agno backend
pip install clawbridge[agno]

# With Agentica backend
pip install clawbridge[agentica]

# Everything
pip install clawbridge[all]

# Development
pip install clawbridge[dev]
```

Or with [`uv`](https://github.com/astral-sh/uv):

```bash
uv add clawbridge[all]
```

---

## Quickstart

### 1. One-liner agent

```python
from clawbridge import create_agent

agent = create_agent(name="Molty", backend="agno", provider="anthropic")
print(agent.chat("Hello! What are you?"))
```

### 2. Full control

```python
from pathlib import Path
from clawbridge import (
    ClawAgent, ClawBridge, ClawSkill,
    ModelConfig, MemoryConfig, ToolDefinition,
)

# Define a tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

# Load an OpenClaw-format skill
skill = ClawSkill.from_skill_md(Path("./skills/web_search"))

# Define the agent
agent = ClawAgent(
    name="Molty",
    description="A personal AI assistant inspired by OpenClaw",
    personality=(
        "You are Molty 🦞, a helpful and slightly witty personal AI "
        "assistant. You get things done efficiently and remember "
        "context across conversations."
    ),
    model=ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        api_key_env="ANTHROPIC_API_KEY",
    ),
    memory_config=MemoryConfig(enabled=True, long_term=True),
    skills=[skill],
    tools=[
        ToolDefinition(
            name="search_web",
            description="Search the web",
            callable=search_web,
        ),
    ],
)

# Deploy
bridge = ClawBridge(agent, backend="agno")
print(bridge)
# → ClawBridge(agent='Molty', backend='agno', skills=1, tools=1)

# Chat
response = bridge.chat("What's the latest on AI agents?")
print(response)

# Memory persists across sessions
bridge.memory.remember("user_name", "Alice", category="preference")
```

### 3. CLI

```bash
# Interactive chat
clawbridge run --name Molty --backend agno --provider anthropic

# List discovered skills
clawbridge skills --dir ./skills

# Serve as HTTP API
clawbridge serve --backend agno --port 8000
```

---

## Core Concepts

### `ClawAgent` — The Universal Agent Definition

A single, framework-agnostic Pydantic model that captures everything about your
agent: identity, personality, model config, skills, tools, memory settings, and
behavior flags.

```python
agent = ClawAgent(
    name="Molty",
    personality="Friendly, efficient, remembers everything.",
    role="Personal assistant with research capabilities",
    model=ModelConfig(provider="openai", model_id="gpt-4o"),
    skills=[...],          # OpenClaw SKILL.md skills
    tools=[...],           # Python callables as tools
    autonomous=True,       # Can act without explicit prompts
    human_in_loop=False,   # Require confirmation for actions
    max_iterations=10,     # Max tool-use loops per turn
    markdown_output=True,
)
```

Backends **compile** this definition into their native representation. You never
write framework-specific code.

### `ClawSkill` — Portable Skill System

clawbridge natively parses OpenClaw's `SKILL.md` format:

```markdown
---
name: web-search
description: Search the web for current information
category: research
version: 1.0.0
tools:
  - name: search_web
    description: Search using DuckDuckGo
    parameters:
      - name: query
        type: string
        required: true
---

# Skill: Web Search

## Overview
Use this skill when the user asks about recent events...

## Guidelines
- Always cite your sources
- Prefer recent results
```

Skills are loaded from disk, injected into system prompts, and their tool
definitions are translated to each backend's native format:

```python
from clawbridge import ClawSkill

skill = ClawSkill.from_skill_md(Path("./skills/web_search"))
print(skill.name)          # "web-search"
print(len(skill.tools))    # 1
print(skill.to_system_prompt_fragment())
```

### `ClawMemory` — Persistent Cross-Session Memory

Inspired by OpenClaw's design where configuration and interaction history are
stored locally for persistent, adaptive behavior, `ClawMemory` provides:

- **Long-term memory** — facts, preferences, learned behaviors (survives
  backend swaps)
- **Short-term memory** — per-session conversation history
- **Auto-persistence** — JSON-backed local storage by default
- **System prompt injection** — memories are automatically included in context

```python
bridge.memory.remember("user_name", "Alice", category="preference")
bridge.memory.remember("timezone", "US/Pacific", category="preference")

name = bridge.memory.recall("user_name")  # → "Alice"
prefs = bridge.memory.recall_by_category("preference")
# → {"user_name": "Alice", "timezone": "US/Pacific"}

# Auto-injected into the agent's system prompt:
# ## Agent Memory
# ### Preference
# - **user_name**: Alice
# - **timezone**: US/Pacific
```

### `ClawBridge` — The Orchestrator

The main API surface. It takes a `ClawAgent` + backend name, compiles the agent,
and provides a unified interface for chat, async chat, backend switching, and
serving.

```python
bridge = ClawBridge(agent, backend="agno")

# Sync chat
response = bridge.chat("Hello!")

# Async chat
response = await bridge.achat("Hello!")

# Hot-swap backend (memory carries over)
bridge.switch_backend("agentica")

# Serve as HTTP API
await bridge.serve(host="0.0.0.0", port=8000)

# Access the native framework agent
native = bridge.native_agent  # Agno Agent, Agentica config, etc.
```

---

## Backends

### Agno

Agno is a high-performance framework that provides ready-made components for
LLMs, memory, knowledge retrieval, and tool integrations, with a clean
declarative API.

clawbridge compiles `ClawAgent` → Agno's `Agent` class:

```python
bridge = ClawBridge(agent, backend="agno")

# What happens under the hood:
# Agent(
#     name="Molty",
#     model=Anthropic(id="claude-sonnet-4-20250514"),
#     tools=[search_web, read_file],
#     instructions=[compiled_system_prompt],
#     markdown=True,
# )

# You can always access the native object:
agno_agent = bridge.native_agent
```

**Features mapped:**

| ClawAgent property | Agno equivalent |
|---|---|
| `model` | `Anthropic(...)`, `OpenAI(...)`, etc. |
| `tools` (callables) | Direct function tools |
| `skills` → instructions | `instructions=[...]` |
| `memory_config` | `AgentMemory()` |
| `markdown_output` | `markdown=True` |
| `description` | `description=...` |

**Serving:** Agno has native FastAPI support. `bridge.serve()` uses Agno's
`Playground` when available, falling back to a manual FastAPI + Uvicorn server.

### Agentica

Agentica takes a fundamentally different approach: instead of JSON tool-calling,
agents interact with live Python objects through code execution in a sandboxed
REPL. clawbridge adapts to this by converting tools into scope objects:

```python
bridge = ClawBridge(agent, backend="agentica")

# What happens under the hood:
# scope = {
#     "search_web": <callable>,
#     "read_file": <callable>,
#     "memory": <_AgenticaMemoryBridge>,
# }
# agent = await spawn(system_prompt, **scope)

# The memory bridge lets the agent call:
#   memory.remember("key", "value")
#   memory.recall("key")
```

**Features mapped:**

| ClawAgent property | Agentica equivalent |
|---|---|
| `tools` (callables) | Scope objects (passed to `spawn()`) |
| `tools` (skill-defined) | Dynamic scope callables |
| `model` | Model string `"anthropic/claude-sonnet-4-20250514"` |
| `memory` | `_AgenticaMemoryBridge` scope object |
| `skills` → instructions | System prompt for `spawn()` |

**Type safety:** Agentica enforces types at runtime. clawbridge preserves this
by mapping `ToolParameter` types to Python annotations on generated scope
objects.

### Adding Your Own Backend

Implement the `ClawBackend` protocol:

```python
from clawbridge.backends.base import ClawBackend

class MyBackend(ClawBackend):
    name = "myframework"

    def compile(self):
        """Turn self.agent (ClawAgent) into your framework's native agent."""
        ...

    async def run(self, message: str, session_id: str = "default") -> str:
        """Send a message, get a response."""
        ...

# Register it
ClawBridge.register_backend("myframework", MyBackend)

# Use it
bridge = ClawBridge(agent, backend="myframework")
```

---

## Skills

### Directory Structure

Skills follow the OpenClaw convention — a directory with a `SKILL.md` file:

```
skills/
├── web_search/
│   └── SKILL.md
├── file_manager/
│   └── SKILL.md
└── code_runner/
    └── SKILL.md
```

### Loading Skills

```python
from clawbridge.skills.loader import SkillLoader

loader = SkillLoader([Path("./skills")])

# Discover all skills
all_skills = loader.load_all()

# Load by name
skill = loader.load_by_name("web-search")

# Load by category
research_skills = loader.load_by_category("research")
```

### Skill Registry

The registry combines local skills with optional ClawHub discovery:

```python
from clawbridge.skills.registry import SkillRegistry

registry = SkillRegistry(
    local_paths=[Path("./skills")],
    enable_clawhub=True,  # Enable remote skill search
)

# Load all local skills
registry.load_local()

# Search ClawHub
results = await registry.search_clawhub("data analysis")
```

### Writing Skills

Create `skills/my_skill/SKILL.md`:

```markdown
---
name: my-skill
description: What this skill does
category: utility
version: 1.0.0
tools:
  - name: my_tool
    description: What the tool does
    parameters:
      - name: input
        type: string
        description: The input to process
        required: true
---

# Skill: My Skill

Instructions for the AI agent on how and when to use this skill...
```

Then wire the tool implementation:

```python
def my_tool(input: str) -> str:
    return f"Processed: {input}"

agent = ClawAgent(
    skills=[ClawSkill.from_skill_md(Path("./skills/my_skill"))],
    tools=[ToolDefinition(name="my_tool", callable=my_tool, description="...")],
)
```

---

## CLI

```
$ clawbridge --help

🦞 Deploy OpenClaw-like agents to any framework

commands:
  run       Run an agent interactively
  skills    List discovered skills
  serve     Serve agent as HTTP API
```

### `clawbridge run`

```bash
clawbridge run \
  --name Molty \
  --backend agno \
  --model claude-sonnet-4-20250514 \
  --provider anthropic \
  --skills-dir ./skills \
  --personality "Friendly and concise"
```

```
┌─ clawbridge ───────────────────────────────────┐
│ 🦞 Molty ready (agno backend)                  │
│ Model: anthropic/claude-sonnet-4-20250514       │
│ Skills: 3 loaded                                │
│ Type quit to exit.                              │
└─────────────────────────────────────────────────┘
You: Hello!
Molty: Hey there! 🦞 I'm Molty, your personal assistant...
```

### `clawbridge skills`

```bash
clawbridge skills --dir ./skills
```

```
🦞 Discovered Skills
┌────────────┬──────────┬─────────┬───────┬──────────────────────────────┐
│ Name       │ Category │ Version │ Tools │ Description                  │
├────────────┼──────────┼─────────┼───────┼──────────────────────────────┤
│ web-search │ research │ 1.0.0   │     2 │ Search the web for current…  │
│ file-mgr   │ utility  │ 1.0.0   │     3 │ Read, write, and manage…     │
│ code-run   │ dev      │ 1.0.0   │     1 │ Execute code snippets…       │
└────────────┴──────────┴─────────┴───────┴──────────────────────────────┘
```

### `clawbridge serve`

```bash
clawbridge serve --backend agno --port 8000

# 🦞 Serving on http://0.0.0.0:8000 (agno backend)
```

Exposes a `/chat` POST endpoint (with Agno Playground support when available).

---

## Examples

### Agno Deployment

```python
# examples/agno_deploy.py
from clawbridge import ClawAgent, ClawBridge, ModelConfig, ToolDefinition

def search(query: str) -> str:
    return f"Results for: {query}"

agent = ClawAgent(
    name="Molty",
    personality="Helpful lobster assistant 🦞",
    model=ModelConfig(provider="openai", model_id="gpt-4o"),
    tools=[ToolDefinition(name="search", callable=search, description="Web search")],
)

bridge = ClawBridge(agent, backend="agno")
print(bridge.chat("Search for the latest AI news"))
```

### Agentica Deployment with Live Objects

```python
# examples/agentica_deploy.py
import asyncio
from clawbridge import ClawAgent, ClawBridge, ModelConfig, ToolDefinition

class DataAnalyzer:
    """Pass this live object into the agent's scope."""

    def analyze_csv(self, path: str) -> dict:
        return {"rows": 100, "columns": 5, "path": path}

    def plot(self, data: dict, chart_type: str = "bar") -> str:
        return f"Chart ({chart_type}) generated"

analyzer = DataAnalyzer()

agent = ClawAgent(
    name="DataClaw",
    model=ModelConfig(provider="anthropic", model_id="claude-sonnet-4-20250514"),
    tools=[ToolDefinition(name="analyzer", callable=analyzer, description="Data toolkit")],
)

bridge = ClawBridge(agent, backend="agentica")

async def main():
    print(await bridge.achat("Analyze data/sales.csv and plot the results"))

asyncio.run(main())
```

### Backend Comparison

```python
# examples/compare_backends.py
"""Run the same agent on multiple backends and compare."""

from clawbridge import ClawAgent, ClawBridge, ModelConfig

agent = ClawAgent(
    name="Molty",
    personality="Concise and helpful.",
    model=ModelConfig(provider="anthropic", model_id="claude-sonnet-4-20250514"),
)

for backend in ["agno", "agentica"]:
    bridge = ClawBridge(agent, backend=backend)
    response = bridge.chat("Explain quantum computing in one sentence.")
    print(f"[{backend:>10}] {response}\n")
```

### Persistent Memory Across Backends

```python
from clawbridge import ClawAgent, ClawBridge, ClawMemory, MemoryConfig

# Shared memory instance
memory = ClawMemory(MemoryConfig(persist_path=".clawbridge/molty_memory"))
memory.remember("user_name", "Alice", category="preference")

agent = ClawAgent(name="Molty")

# Start with Agno
bridge = ClawBridge(agent, backend="agno", memory=memory)
bridge.chat("Hi! Remember that my favorite color is blue.")

# Switch to Agentica — memory carries over
bridge.switch_backend("agentica")
response = bridge.chat("What's my name and favorite color?")
# Molty remembers Alice and blue, even on a different backend
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     clawbridge (Meta-Layer)                     │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  ClawAgent   │  │  ClawSkill   │  │     ClawMemory        │ │
│  │  (universal  │  │  (SKILL.md   │  │  (persistent, cross-  │ │
│  │   agent def) │  │   compat)    │  │   session context)    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬────────────┘ │
│         │                 │                      │              │
│  ┌──────▼─────────────────▼──────────────────────▼────────────┐ │
│  │                ClawBridge  (compile / emit)                │ │
│  └──────┬──────────────────────────────┬──────────────────────┘ │
│         │                              │                        │
│  ┌──────▼──────────┐          ┌────────▼─────────────┐         │
│  │  AgnoBackend    │          │  AgenticaBackend     │         │
│  │  (agno adapter) │          │  (agentica adapter)  │         │
│  └──────┬──────────┘          └────────┬─────────────┘         │
│         │                              │                        │
└─────────┼──────────────────────────────┼────────────────────────┘
          │                              │
    ┌─────▼─────┐                 ┌──────▼──────┐
    │  Agno SDK │                 │Agentica SDK │
    │  runtime  │                 │  runtime    │
    └───────────┘                 └─────────────┘
```

### Project Structure

```
clawbridge/
├── pyproject.toml
├── README.md
├── src/
│   └── clawbridge/
│       ├── __init__.py           # Public API exports
│       ├── core/
│       │   ├── agent.py          # ClawAgent definition
│       │   ├── skill.py          # ClawSkill + SKILL.md parser
│       │   ├── memory.py         # ClawMemory (persistent, cross-session)
│       │   ├── tool.py           # ClawTool (universal tool wrapper)
│       │   └── types.py          # Shared types & enums
│       ├── backends/
│       │   ├── base.py           # Abstract ClawBackend protocol
│       │   ├── agno.py           # Agno backend adapter
│       │   └── agentica.py       # Agentica backend adapter
│       ├── skills/
│       │   ├── loader.py         # Load skills from directories
│       │   └── registry.py       # Local + ClawHub skill registry
│       ├── bridge.py             # ClawBridge orchestrator + create_agent()
│       └── cli.py                # CLI entrypoint
├── skills/                       # Example OpenClaw-format skills
│   └── web_search/
│       └── SKILL.md
└── examples/
    ├── agno_deploy.py
    ├── agentica_deploy.py
    └── compare_backends.py
```

### Design Decisions

| Decision | Rationale |
|---|---|
| **Pydantic models everywhere** | Validation, serialization, and IDE autocomplete out of the box |
| **Lazy backend imports** | Installing `agno` isn't required to use the `agentica` backend |
| **SKILL.md compatibility** | Directly reuse OpenClaw's 5,400+ community skill ecosystem |
| **Memory above backends** | Hot-swap frameworks without losing conversational context |
| **`compile()` / `run()` split** | Inspect native agent objects before execution for debugging |
| **Scope objects for Agentica** | Respects Agentica's "live objects, not JSON tools" paradigm |
| **`ClawBackend` protocol** | Adding new frameworks is one file + one class |

---

## Supported Models

clawbridge delegates model resolution to each backend, but provides a unified
`ModelConfig`:

| Provider | Model Examples | Agno | Agentica |
|---|---|---|---|
| Anthropic | `claude-sonnet-4-20250514`, `claude-opus-4-20250514` | ✅ | ✅ |
| OpenAI | `gpt-4o`, `gpt-4.1`, `o3` | ✅ | ✅ |
| Groq | `llama-3.3-70b-versatile` | ✅ | ✅ |
| DeepSeek | `deepseek-chat`, `deepseek-reasoner` | ✅ | ✅ |
| Local | Any OpenAI-compatible endpoint | ✅ | ✅ |

```python
# Use any provider
ModelConfig(provider="openai", model_id="gpt-4o")
ModelConfig(provider="anthropic", model_id="claude-sonnet-4-20250514")
ModelConfig(provider="local", model_id="llama3", base_url="http://localhost:11434/v1")
```

---

## Roadmap

### Current (v0.1)

- [x] Core `ClawAgent` / `ClawSkill` / `ClawMemory` models
- [x] `SKILL.md` parser (OpenClaw compatible)
- [x] Agno backend
- [x] Agentica backend
- [x] CLI (run / skills / serve)
- [x] Persistent local memory
- [x] Hot-swap backends at runtime

### Next (v0.2)

- [ ] **CrewAI backend** — map `ClawAgent` → CrewAI `Agent` / `Task` / `Crew`
- [ ] **LangChain backend** — `ClawAgent` → LangChain `AgentExecutor`
- [ ] **Claude Agent SDK backend** — Anthropic's native agent SDK
- [ ] **OpenAI Agents SDK backend** — OpenAI's native agent SDK
- [ ] **Streaming support** — SSE / WebSocket for real-time responses
- [ ] **ClawHub integration** — install skills from OpenClaw's registry at runtime

### Future (v0.3+)

- [ ] **Messaging adapters** — Telegram, WhatsApp, Slack, Discord (like OpenClaw's Gateway)
- [ ] **Multi-agent teams** — define teams of ClawAgents with delegation
- [ ] **Evaluation harness** — benchmark the same agent across backends
- [ ] **Skill authoring CLI** — `clawbridge skill create my-skill`
- [ ] **Plugin system** — third-party backend + memory + skill plugins
- [ ] **SOUL.md support** — parse OpenClaw community agent templates

---

## FAQ

**Q: Is this an OpenClaw fork?**
No. clawbridge is a separate project. OpenClaw is a Node.js/TypeScript personal
AI assistant with its own Gateway runtime. clawbridge borrows its *patterns*
(SKILL.md, persistent memory, skill registry) and makes them portable across
Python agent frameworks.

**Q: Can I use my existing OpenClaw skills?**
Yes — any directory with a valid `SKILL.md` file can be loaded by clawbridge.
Tool implementations need to be wired separately in Python, but the skill
definitions, instructions, and metadata are fully compatible.

**Q: Why not just use one framework?**
Frameworks have different strengths. Agno excels at production deployment with
its AgentOS and monitoring. Agentica's code-mode approach with live scope
objects is uniquely powerful for complex integrations. clawbridge lets you
leverage each framework's strengths without rewriting your agent.

**Q: How does memory work across backends?**
`ClawMemory` is a framework-independent layer that sits above all backends. It
persists to local JSON by default. When you `switch_backend()`, the same memory
instance is passed to the new backend — nothing is lost.

**Q: Can I access the underlying framework's native agent?**
Yes: `bridge.native_agent` returns the compiled framework-specific object (e.g.,
an Agno `Agent` instance). You can use this for framework-specific features that
clawbridge doesn't abstract.

---

## Contributing

We welcome contributions! Here's how to get started:

```bash
# Clone
git clone https://github.com/clawbridge/clawbridge.git
cd clawbridge

# Install with dev dependencies
uv sync --extra dev --extra all

# Run tests
pytest

# Lint & format
ruff check src/
ruff format src/

# Type check
mypy src/
```

### Areas we'd love help with

- 🔌 **New backends** — CrewAI, LangChain, Claude Agent SDK, OpenAI Agents SDK
- 🧪 **Tests** — unit tests, integration tests, backend conformance tests
- 📝 **Skills** — example skills with real tool implementations
- 📖 **Docs** — tutorials, guides, API reference
- 🌐 **Messaging adapters** — Telegram, Slack, Discord, WhatsApp bridges

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  Built with 🦞 by the clawbridge community.
  <br>
  Inspired by <a href="https://github.com/openclaw/openclaw">OpenClaw</a> and
  the incredible AI agent ecosystem.
</p>

---