"""Internal adapter protocol used by framework builders."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from clawbridge.core.agent import ClawAgent
from clawbridge.core.channel import (
    ChannelMessageContext,
    ChannelPolicyDecision,
    evaluate_channel_policy,
)
from clawbridge.core.memory import ClawMemory
from clawbridge.core.prompt import OpenClawPromptContext
from clawbridge.core.sandbox import SandboxRuntimeMetadata
from clawbridge.core.session import OpenClawSessionContext, OpenClawSessionScope


class ClawBackend(ABC):
    """
    Internal protocol implemented by each framework adapter.

    Responsibilities:
      1. compile() — turn a ClawAgent into a framework-native object/config
      2. run()     — execute the agent with a user message
      3. serve()   — (optional) deploy as a framework-native service
    """

    name: str

    def __init__(self, agent: ClawAgent, memory: ClawMemory | None = None):
        self.agent = agent
        self.memory = memory or ClawMemory(agent.memory_config)
        self._native_agent: Any = None
        self._session_context_overrides: dict[str, OpenClawSessionContext] = {}

    @abstractmethod
    def compile(self) -> Any:
        """
        Compile a ClawAgent into this framework's native representation.
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

    async def run_channel_message(
        self,
        message: str,
        *,
        context: ChannelMessageContext,
    ) -> str:
        """Run a channel event through policy evaluation and session mapping."""
        decision = self.evaluate_channel_policy(context)
        if not decision.allowed:
            raise PermissionError(decision.reason or "Channel message blocked by policy.")
        self._session_context_overrides[decision.session.session_id] = decision.session
        try:
            return await self.run(message, session_id=decision.session.session_id)
        finally:
            self._session_context_overrides.pop(decision.session.session_id, None)

    def run_channel_message_sync(
        self,
        message: str,
        *,
        context: ChannelMessageContext,
    ) -> str:
        """Synchronous wrapper for channel-policy execution."""
        import asyncio
        return asyncio.run(self.run_channel_message(message, context=context))

    def evaluate_channel_policy(
        self,
        context: ChannelMessageContext,
    ) -> ChannelPolicyDecision:
        """Evaluate channel context against the agent's policy model."""
        return evaluate_channel_policy(self.agent.channel_policy, context)

    def get_session_context(self, session_id: str = "default") -> OpenClawSessionContext:
        """Infer a session scope from a framework session id."""
        normalized_session_id = session_id.strip() or "default"
        if normalized_session_id in self._session_context_overrides:
            return self._session_context_overrides[normalized_session_id]
        if normalized_session_id in {"default", "main"}:
            scope = OpenClawSessionScope.MAIN
        else:
            scope = OpenClawSessionScope.SHARED
        return OpenClawSessionContext(
            session_id=normalized_session_id,
            scope=scope,
        )

    def get_sandbox_runtime(
        self,
        session_context: OpenClawSessionContext | None = None,
    ) -> SandboxRuntimeMetadata:
        """Resolve sandbox runtime metadata for a session."""
        effective_session = session_context or self.get_session_context()
        return self.agent.sandbox.resolve_runtime(
            session=effective_session,
            workspace_path=self.agent.workspace_path,
        )

    def build_prompt_context(
        self,
        session_context: OpenClawSessionContext | None = None,
    ) -> OpenClawPromptContext:
        """Build prompt metadata for a concrete runtime session."""
        effective_session = session_context or self.get_session_context()
        return OpenClawPromptContext(
            session=effective_session,
            workspace_path=self.agent.workspace_path,
            sandbox=self.get_sandbox_runtime(effective_session),
        )

    def build_system_prompt(
        self,
        memory: ClawMemory | None = None,
        *,
        session_context: OpenClawSessionContext | None = None,
    ) -> str:
        """Compose the OpenClaw prompt for a concrete runtime session."""
        return self.agent.build_system_prompt(
            memory,
            prompt_context=self.build_prompt_context(session_context),
            session_context=session_context,
        )

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
