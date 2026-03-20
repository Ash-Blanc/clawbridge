"""
Agentica backend — compiles ClawAgent into Symbolica's Agentica primitives.

Agentica is fundamentally different: it uses a persistent Python REPL
where agents execute code against live objects. Instead of JSON tool-calling,
you pass real Python objects into the agent's scope.
"""

from __future__ import annotations

from typing import Any

from clawbridge.backends.base import ClawBackend
from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
from clawbridge.core.types import LLMProvider, ToolDefinition


class AgenticaBackend(ClawBackend):
    """
    Compile and run ClawAgents using Symbolica's Agentica framework.

    Key Agentica concepts:
    - @agentic() decorated functions with type-safe returns
    - spawn() to create agents with objects in scope
    - Persistent REPL with live objects
    - Recursive agent delegation via call_agent
    """

    name = "agentica"

    def __init__(self, agent: ClawAgent, memory: ClawMemory | None = None):
        super().__init__(agent, memory)
        self._agentica_mod: Any = None

    def _ensure_imports(self) -> None:
        """Lazy-import Agentica SDK."""
        if self._agentica_mod is not None:
            return
        try:
            import agentica
            self._agentica_mod = agentica
        except ImportError:
            raise ImportError(
                "Agentica is not installed. Run: pip install clawbridge[agentica]"
            )

    def _resolve_model_string(self) -> str:
        """
        Agentica uses model strings like 'anthropic/claude-sonnet-4-20250514'
        or 'openai/gpt-4o'.
        """
        cfg = self.agent.model
        provider_prefix = {
            LLMProvider.OPENAI: "openai",
            LLMProvider.ANTHROPIC: "anthropic",
            LLMProvider.GROQ: "groq",
            LLMProvider.DEEPSEEK: "deepseek",
        }
        prefix = provider_prefix.get(cfg.provider, cfg.provider.value)
        return f"{prefix}/{cfg.model_id}"

    def _build_scope(self) -> dict[str, Any]:
        """
        Build the scope dictionary for the Agentica agent.

        In Agentica, instead of 'tools', you pass live Python objects
        into the agent's scope. The agent can then call methods on
        these objects directly via code execution.
        """
        scope: dict[str, Any] = {}

        # Inject tools as callable objects in scope
        for tool_def in self.agent.get_all_tools():
            if tool_def.callable is not None:
                scope[tool_def.name] = tool_def.callable
            else:
                # Create a scope object that represents the skill tool
                scope[tool_def.name] = self._make_scope_object(tool_def)

        # Inject memory as a scope object so the agent can use it
        scope["memory"] = _AgenticaMemoryBridge(self.memory)

        return scope

    @staticmethod
    def _make_scope_object(tool_def: ToolDefinition) -> Any:
        """
        Create a typed callable for Agentica's scope.
        Agentica discovers capabilities through methods and type annotations.
        """

        class SkillTool:
            """Dynamically created tool for Agentica scope."""

            def __call__(self, **kwargs: Any) -> str:
                return (
                    f"[Tool '{tool_def.name}' invoked with {kwargs}. "
                    f"Wire an implementation via ClawAgent.tools]"
                )

        obj = SkillTool()
        param_docs = "\n".join(
            f"  {p.name} ({p.type}): {p.description}"
            for p in tool_def.parameters
        )
        obj.__doc__ = f"{tool_def.description}\n\nParameters:\n{param_docs}"
        obj.__name__ = tool_def.name  # type: ignore[attr-defined]
        return obj

    def compile(self) -> Any:
        """
        Compile ClawAgent → Agentica agent config.

        Returns a dict that can be passed to agentica.spawn():
            agent = await spawn(system_prompt, scope_objects)

        Since Agentica agents are created asynchronously via spawn(),
        we return the config and lazily create on first run().
        """
        self._ensure_imports()

        system_prompt = self.agent.build_system_prompt(self.memory)
        scope = self._build_scope()

        # Store the compilation result as a config dict
        self._native_agent = _AgenticaAgentConfig(
            system_prompt=system_prompt,
            scope=scope,
            model=self._resolve_model_string(),
        )
        return self._native_agent

    async def run(self, message: str, session_id: str = "default") -> str:
        """
        Run a message through an Agentica agent.

        Agentica uses spawn() + agent interaction patterns.
        """
        config = self.native
        self.memory.add_message(session_id, "user", message)

        try:
            from agentica import agentic, spawn

            # Spawn an agent with our scope
            agent = await spawn(
                config.system_prompt,
                config.scope,
                model=config.model,
            )

            # In Agentica, you interact by calling the agent
            # The exact API depends on whether it's a function or agent
            if callable(agent):
                result = await agent(message)
            else:
                result = str(agent)

        except ImportError:
            # Fallback: simulate for development
            result = (
                f"[Agentica agent '{self.agent.name}' would process: "
                f"{message}]"
            )

        content = str(result)
        self.memory.add_message(session_id, "assistant", content)
        return content

    async def run_agentic_function(
        self, message: str, return_type: type | None = None
    ) -> Any:
        """
        Run as an @agentic() function — Agentica's core pattern.

        This leverages Agentica's type-safe return enforcement.
        """
        self._ensure_imports()
        from agentica import agentic

        config = self.native

        # Dynamically create an agentic function
        @agentic(model=config.model)
        async def agent_fn(prompt: str) -> str:
            """Process user request."""
            return ""

        return await agent_fn(message)


class _AgenticaAgentConfig:
    """Internal config holder for lazy Agentica agent creation."""

    def __init__(
        self, system_prompt: str, scope: dict[str, Any], model: str
    ):
        self.system_prompt = system_prompt
        self.scope = scope
        self.model = model


class _AgenticaMemoryBridge:
    """
    Expose ClawMemory as a Python object in Agentica's scope.

    The agent can call methods like:
      memory.remember("user_name", "Alice")
      memory.recall("user_name")
    """

    def __init__(self, memory: ClawMemory):
        self._mem = memory

    def remember(self, key: str, value: Any, category: str = "general") -> str:
        """Store something in long-term memory."""
        self._mem.remember(key, value, category)
        return f"Remembered: {key} = {value}"

    def recall(self, key: str) -> Any:
        """Recall something from memory."""
        return self._mem.recall(key)

    def recall_category(self, category: str) -> dict[str, Any]:
        """Recall all memories in a category."""
        return self._mem.recall_by_category(category)

    def forget(self, key: str) -> str:
        """Forget something."""
        self._mem.forget(key)
        return f"Forgot: {key}"

    def summary(self) -> str:
        """Get a summary of all memories."""
        return self._mem.get_context_summary()