"""
Agno backend — compiles ClawAgent into Agno's Agent primitive.

Agno uses a declarative Agent class with modular tools, memory,
knowledge, and team composition.
"""

from __future__ import annotations

from typing import Any

from clawbridge.backends.base import ClawBackend
from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
from clawbridge.core.types import LLMProvider, ToolDefinition


class AgnoBackend(ClawBackend):
    """Compile and run ClawAgents using the Agno framework."""

    name = "agno"

    def __init__(self, agent: ClawAgent, memory: ClawMemory | None = None):
        super().__init__(agent, memory)
        # Lazy imports to avoid hard dependency
        self._agno_mod: Any = None

    def _ensure_imports(self) -> None:
        """Lazy-import Agno modules."""
        if self._agno_mod is not None:
            return
        try:
            import agno.agent
            import agno.models
            import agno.tools
            from agno.os import AgentOS
            self._agno_mod = {
                "Agent": agno.agent.Agent,
                "models": agno.models,
                "tools": agno.tools,
                "AgentOS": AgentOS,
            }
        except ImportError:
            raise ImportError(
                "Agno is not installed. Run: pip install clawbridge[agno]"
            )

    def _resolve_model(self) -> Any:
        """Map ClawAgent's ModelConfig to an Agno model instance."""
        self._ensure_imports()
        cfg = self.agent.model

        model_map: dict[LLMProvider, tuple[str, str]] = {
            LLMProvider.OPENAI: ("agno.models.openai", "OpenAI"),
            LLMProvider.ANTHROPIC: ("agno.models.anthropic", "Claude"),
            LLMProvider.GROQ: ("agno.models.groq", "Groq"),
            LLMProvider.DEEPSEEK: ("agno.models.deepseek", "DeepSeek"),
        }

        if cfg.provider not in model_map:
            raise ValueError(f"Unsupported Agno model provider: {cfg.provider}")

        module_path, class_name = model_map[cfg.provider]
        import importlib
        mod = importlib.import_module(module_path)
        model_cls = getattr(mod, class_name)

        kwargs: dict[str, Any] = {"id": cfg.model_id}
        if cfg.api_key:
            kwargs["api_key"] = cfg.api_key
        if cfg.base_url:
            kwargs["base_url"] = cfg.base_url

        return model_cls(**kwargs)

    def _build_tools(self) -> list[Any]:
        """
        Convert ClawAgent tools into Agno tool instances.

        For tools with callables, wrap them. For skill-defined tools
        without callables, create placeholder function-tools.
        """
        agno_tools: list[Any] = []

        for tool_def in self.agent.get_all_tools():
            if tool_def.callable is not None:
                # Agno can accept raw callables as tools
                agno_tools.append(tool_def.callable)
            else:
                # Create a dynamic tool function from the definition
                agno_tools.append(
                    self._make_placeholder_tool(tool_def)
                )

        return agno_tools

    @staticmethod
    def _make_placeholder_tool(tool_def: ToolDefinition) -> Any:
        """
        Create a callable that represents a skill-defined tool.
        In practice, these would be wired to actual implementations.
        """
        def tool_fn(**kwargs: Any) -> str:
            return (
                f"[Tool '{tool_def.name}' called with {kwargs}. "
                f"Connect an implementation via ClawAgent.tools]"
            )

        tool_fn.__name__ = tool_def.name
        tool_fn.__doc__ = tool_def.description
        return tool_fn

    def _build_memory(self) -> Any | None:
        """Build Agno-native memory (Db) from ClawMemory state."""
        if not self.agent.memory_config.enabled:
            return None
        try:
            from agno.db.in_memory import InMemoryDb
            return InMemoryDb()
        except ImportError:
            return None

    def compile(self) -> Any:
        """
        Compile ClawAgent → Agno Agent.

        Agno agent structure (from their SDK):
            Agent(
                name=...,
                model=OpenAI(id="gpt-4o"),
                tools=[...],
                db=InMemoryDb(),
                add_history_to_context=True,
                read_chat_history=True,
                instructions=[...],
                description=...,
                markdown=True,
            )
        """
        self._ensure_imports()
        Agent = self._agno_mod["Agent"]

        system_prompt = self.agent.build_system_prompt(self.memory)

        agent_kwargs: dict[str, Any] = {
            "name": self.agent.name,
            "model": self._resolve_model(),
            "description": self.agent.description,
            "instructions": [system_prompt],
            "markdown": self.agent.markdown_output,
        }

        # Tools
        tools = self._build_tools()
        if tools:
            agent_kwargs["tools"] = tools

        # Memory
        agno_db = self._build_memory()
        if agno_db:
            agent_kwargs["db"] = agno_db
            agent_kwargs["add_history_to_context"] = True
            agent_kwargs["read_chat_history"] = True

        self._native_agent = Agent(**agent_kwargs)
        return self._native_agent

    async def run(self, message: str, session_id: str = "default") -> str:
        """Run a message through the Agno agent."""
        agent = self.native

        # Track in our memory
        self.memory.add_message(session_id, "user", message)

        # Agno supports both sync and async via the same API
        response = agent.run(message)

        # Extract content from Agno's response
        content = self._extract_content(response)

        self.memory.add_message(session_id, "assistant", content)
        return content

    @staticmethod
    def _extract_content(response: Any) -> str:
        """Extract text content from Agno's RunResponse."""
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)

    async def serve(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """
        Serve as a FastAPI endpoint using Agno's AgentOS.
        """
        self._ensure_imports()
        AgentOS = self._agno_mod["AgentOS"]

        agent = self.native
        agent_os = AgentOS(agents=[agent])
        app = agent_os.get_app()

        # AgentOS.serve uses uvicorn.run which is blocking.
        import asyncio
        import functools

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            functools.partial(agent_os.serve, app=app, host=host, port=port),
        )