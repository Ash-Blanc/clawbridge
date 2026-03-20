"""
ClawBridge — the main orchestrator.

This is the primary API surface. Users define a ClawAgent and
the bridge compiles + deploys it to any supported backend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from clawbridge.backends.base import ClawBackend
from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
from clawbridge.core.types import Backend, MemoryConfig, ModelConfig
from clawbridge.skills.loader import SkillLoader


class ClawBridge:
    """
    Main entry point for clawbridge.

    Usage:
        agent = ClawAgent(name="Molty", ...)
        bridge = ClawBridge(agent, backend="agno")
        response = bridge.chat("What's the weather?")

        # Or switch backends:
        bridge.switch_backend("agentica")
        response = bridge.chat("Analyze this data")

        # Or deploy:
        await bridge.serve(port=8000)
    """

    _backend_registry: dict[str, type[ClawBackend]] = {}

    def __init__(
        self,
        agent: ClawAgent,
        backend: str | Backend = Backend.AGNO,
        memory: ClawMemory | None = None,
        auto_load_skills: bool = True,
    ):
        self.agent = agent
        self._memory = memory or ClawMemory(agent.memory_config)

        # Auto-load skills from paths
        if auto_load_skills and agent.skill_paths:
            self._load_skills_from_paths()

        # Initialize backend
        self._backend_name = Backend(backend)
        self._backend = self._create_backend(self._backend_name)

    @classmethod
    def register_backend(cls, name: str, backend_cls: type[ClawBackend]) -> None:
        """Register a custom backend (for extensibility)."""
        cls._backend_registry[name] = backend_cls

    def _create_backend(self, backend: Backend) -> ClawBackend:
        """Create the appropriate backend instance."""
        # Check custom registry first
        if backend.value in self._backend_registry:
            cls = self._backend_registry[backend.value]
            return cls(self.agent, self._memory)

        match backend:
            case Backend.AGNO:
                from clawbridge.backends.agno import AgnoBackend
                return AgnoBackend(self.agent, self._memory)
            case Backend.AGENTICA:
                from clawbridge.backends.agentica import AgenticaBackend
                return AgenticaBackend(self.agent, self._memory)
            case _:
                raise ValueError(f"Unknown backend: {backend}")

    def _load_skills_from_paths(self) -> None:
        """Load skills from the agent's configured skill paths."""
        loader = SkillLoader(self.agent.skill_paths)
        loaded = loader.load_all()
        self.agent.skills.extend(loaded)

    # ── Public API ──

    def chat(self, message: str, session_id: str = "default") -> str:
        """Send a message and get a response (sync)."""
        return self._backend.run_sync(message, session_id)

    async def achat(self, message: str, session_id: str = "default") -> str:
        """Send a message and get a response (async)."""
        return await self._backend.run(message, session_id)

    def switch_backend(self, backend: str | Backend) -> None:
        """Hot-swap the backend framework (preserving memory)."""
        self._backend_name = Backend(backend)
        self._backend = self._create_backend(self._backend_name)

    async def serve(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Deploy the agent as an HTTP API."""
        await self._backend.serve(host, port)

    @property
    def native_agent(self) -> Any:
        """Access the underlying framework's native agent object."""
        return self._backend.native

    @property
    def memory(self) -> ClawMemory:
        """Access the shared memory store."""
        return self._memory

    @property
    def backend(self) -> ClawBackend:
        """Access the current backend."""
        return self._backend

    def __repr__(self) -> str:
        return (
            f"ClawBridge(agent='{self.agent.name}', "
            f"backend='{self._backend_name}', "
            f"skills={len(self.agent.skills)}, "
            f"tools={len(self.agent.get_all_tools())})"
        )


# ── Convenience factory ──

def create_agent(
    name: str = "Claw",
    backend: str = "agno",
    model: str = "claude-sonnet-4-20250514",
    provider: str = "anthropic",
    skills: Sequence[str | Path] | None = None,
    personality: str = "",
    **kwargs: Any,
) -> ClawBridge:
    """
    Quick factory to create a ClawBridge agent in one call.

    Usage:
        agent = create_agent(
            name="Molty",
            backend="agno",
            model="gpt-4o",
            provider="openai",
            skills=["./skills/web_search"],
            personality="Friendly and concise.",
        )
        print(agent.chat("Hello!"))
    """
    from clawbridge.core.skill import ClawSkill

    # Load skills
    loaded_skills = []
    for s in (skills or []):
        path = Path(s)
        if path.exists():
            loaded_skills.append(ClawSkill.from_skill_md(path))

    agent = ClawAgent(
        name=name,
        model=ModelConfig(
            provider=provider,  # type: ignore[arg-type]
            model_id=model,
        ),
        skills=loaded_skills,
        personality=personality,
        **kwargs,
    )

    return ClawBridge(agent, backend=backend)