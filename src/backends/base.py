"""Abstract backend protocol — every framework adapter implements this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory


class ClawBackend(ABC):
    """
    Protocol that each framework backend must implement.

    Responsibilities:
      1. compile() — turn a ClawAgent into a native agent object
      2. run()     — execute the agent with a user message
      3. serve()   — (optional) deploy as an API / service
    """

    name: str

    def __init__(self, agent: ClawAgent, memory: ClawMemory | None = None):
        self.agent = agent
        self.memory = memory or ClawMemory(agent.memory_config)
        self._native_agent: Any = None

    @abstractmethod
    def compile(self) -> Any:
        """
        Compile the universal ClawAgent into this framework's
        native agent representation.
        """
        ...

    @abstractmethod
    async def run(self, message: str, session_id: str = "default") -> str:
        """Send a message to the agent and get a response."""
        ...

    def run_sync(self, message: str, session_id: str = "default") -> str:
        """Synchronous convenience wrapper."""
        import asyncio
        return asyncio.run(self.run(message, session_id))

    async def serve(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Optional: serve the agent as an HTTP API."""
        raise NotImplementedError(
            f"{self.name} backend doesn't support serve() yet"
        )

    @property
    def native(self) -> Any:
        """Access the underlying framework-native agent object."""
        if self._native_agent is None:
            self._native_agent = self.compile()
        return self._native_agent