from __future__ import annotations

from typing import Any

import pytest

from clawbridge.backends.base import ClawBackend
from clawbridge.bridge import ClawBridge
from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
from clawbridge.core.types import MemoryConfig


class _AlphaBackend(ClawBackend):
    name = "alpha"

    def compile(self) -> Any:
        return {"backend": self.name}

    async def run(self, message: str, session_id: str = "default") -> str:
        user_name = self.memory.recall("user_name")
        return f"{self.name}:{message}:{user_name}"


class _BetaBackend(ClawBackend):
    name = "beta"

    def compile(self) -> Any:
        return {"backend": self.name}

    async def run(self, message: str, session_id: str = "default") -> str:
        user_name = self.memory.recall("user_name")
        return f"{self.name}:{message}:{user_name}"


@pytest.fixture(autouse=True)
def _restore_backend_registry() -> Any:
    original = ClawBridge._backend_registry.copy()
    yield
    ClawBridge._backend_registry = original


def test_clawbridge_supports_registered_custom_backends() -> None:
    ClawBridge.register_backend("alpha-test", _AlphaBackend)

    bridge = ClawBridge(
        ClawAgent(name="Portable", memory_config=MemoryConfig(enabled=False)),
        backend="alpha-test",
    )

    assert isinstance(bridge.backend, _AlphaBackend)
    assert bridge.chat("ping") == "alpha:ping:None"


def test_switch_backend_preserves_shared_memory() -> None:
    ClawBridge.register_backend("alpha-test", _AlphaBackend)
    ClawBridge.register_backend("beta-test", _BetaBackend)

    memory = ClawMemory(MemoryConfig(enabled=False))
    memory.remember("user_name", "Alice", category="preference")

    bridge = ClawBridge(
        ClawAgent(name="Portable", memory_config=MemoryConfig(enabled=False)),
        backend="alpha-test",
        memory=memory,
    )
    assert bridge.chat("hello") == "alpha:hello:Alice"

    bridge.switch_backend("beta-test")

    assert isinstance(bridge.backend, _BetaBackend)
    assert bridge.backend.memory is bridge.memory
    assert bridge.memory.recall("user_name") == "Alice"
    assert bridge.chat("hello") == "beta:hello:Alice"


def test_build_system_prompt_keeps_portable_section_order() -> None:
    memory = ClawMemory(MemoryConfig(enabled=False))
    memory.remember("timezone", "UTC", category="preference")

    agent = ClawAgent(
        name="Portable",
        personality="Helpful and direct.",
        role="Research assistant",
        system_prompt="Follow the operating rules.",
        additional_instructions=["Always cite uncertainty."],
    )

    prompt = agent.build_system_prompt(memory)

    personality_index = prompt.index("# Personality")
    role_index = prompt.index("# Your Role")
    system_prompt_index = prompt.index("Follow the operating rules.")
    memory_index = prompt.index("## Agent Memory")
    extra_index = prompt.index("Always cite uncertainty.")

    assert personality_index < role_index < system_prompt_index < memory_index < extra_index
