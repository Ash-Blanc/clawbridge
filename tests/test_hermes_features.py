"""Tests for Hermes-like features: native memory, learning, sessions."""

from __future__ import annotations

from importlib.util import find_spec

import pytest

from clawbridge.core.agent import ClawAgent
from clawbridge.core.types import (
    AgentMemoryMode,
    LearningConfig,
    ModelConfig,
    SessionConfig,
    StorageConfig,
    StorageType,
)


def test_agent_memory_mode_defaults_to_off():
    agent = ClawAgent(name="Test")
    assert agent.agent_memory_mode == AgentMemoryMode.OFF


def test_learning_defaults_to_disabled():
    agent = ClawAgent(name="Test")
    assert agent.learning.enabled is False


def test_session_config_defaults():
    agent = ClawAgent(name="Test")
    assert agent.session.search_past_sessions is False
    assert agent.session.enable_session_summaries is False
    assert agent.session.reasoning is False


def test_agent_memory_mode_from_yaml(tmp_path):
    yaml_content = """
name: HermesLike
agent_memory_mode: automatic
learning:
  enabled: true
session:
  search_past_sessions: true
  enable_session_summaries: true
  reasoning: true
"""
    yaml_file = tmp_path / "agent.yaml"
    yaml_file.write_text(yaml_content)

    from clawbridge.builders import load_agent_config
    agent = load_agent_config(yaml_file)

    assert agent.agent_memory_mode == AgentMemoryMode.AUTOMATIC
    assert agent.learning.enabled is True
    assert agent.session.search_past_sessions is True
    assert agent.session.enable_session_summaries is True
    assert agent.session.reasoning is True


@pytest.mark.skipif(find_spec("agno") is None, reason="agno not installed")
class TestAgnoMemoryMapping:
    """Verify AgnoBackend maps memory modes to correct Agno params."""

    def _compile_kwargs(self, agent: ClawAgent) -> dict:
        """Helper: compile and inspect the resulting Agno Agent."""
        from clawbridge.backends.agno import AgnoBackend
        backend = AgnoBackend(agent)
        native = backend.compile()
        return native

    def test_off_mode_skips_native_memory(self):
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
            agent_memory_mode=AgentMemoryMode.OFF,
        )
        native = self._compile_kwargs(agent)
        assert native.update_memory_on_run is False
        assert native.enable_agentic_memory is False

    def test_automatic_mode_enables_update_memory_on_run(self):
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
            agent_memory_mode=AgentMemoryMode.AUTOMATIC,
            storage=StorageConfig(enabled=True, type=StorageType.IN_MEMORY),
        )
        native = self._compile_kwargs(agent)
        assert native.update_memory_on_run is True
        assert native.enable_agentic_memory is False

    def test_agentic_mode_enables_agentic_memory(self):
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
            agent_memory_mode=AgentMemoryMode.AGENTIC,
            storage=StorageConfig(enabled=True, type=StorageType.IN_MEMORY),
        )
        native = self._compile_kwargs(agent)
        assert native.enable_agentic_memory is True
        assert native.update_memory_on_run is False


@pytest.mark.skipif(find_spec("agno") is None, reason="agno not installed")
class TestAgnoLearningMapping:

    def test_learning_disabled_by_default(self):
        from clawbridge.backends.agno import AgnoBackend
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
        )
        native = AgnoBackend(agent).compile()
        assert native.learning is None or native.learning is False

    def test_learning_enabled(self):
        from clawbridge.backends.agno import AgnoBackend
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
            learning=LearningConfig(enabled=True),
            storage=StorageConfig(enabled=True, type=StorageType.IN_MEMORY),
        )
        native = AgnoBackend(agent).compile()
        assert native.learning is True
        assert native.add_learnings_to_context is True


@pytest.mark.skipif(find_spec("agno") is None, reason="agno not installed")
class TestAgnoSessionMapping:

    def test_session_defaults_no_search(self):
        from clawbridge.backends.agno import AgnoBackend
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
        )
        native = AgnoBackend(agent).compile()
        assert native.search_past_sessions is False or native.search_past_sessions is None

    def test_session_search_enabled(self):
        from clawbridge.backends.agno import AgnoBackend
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
            session=SessionConfig(
                search_past_sessions=True,
                num_past_sessions_to_search=5,
            ),
            storage=StorageConfig(enabled=True, type=StorageType.IN_MEMORY),
        )
        native = AgnoBackend(agent).compile()
        assert native.search_past_sessions is True

    def test_reasoning_enabled(self):
        from clawbridge.backends.agno import AgnoBackend
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
            session=SessionConfig(reasoning=True),
        )
        native = AgnoBackend(agent).compile()
        assert native.reasoning is True

    def test_session_summaries_enabled(self):
        from clawbridge.backends.agno import AgnoBackend
        agent = ClawAgent(
            name="Test",
            model=ModelConfig(provider="openai", model="gpt-4o"),
            session=SessionConfig(enable_session_summaries=True),
            storage=StorageConfig(enabled=True, type=StorageType.IN_MEMORY),
        )
        native = AgnoBackend(agent).compile()
        assert native.enable_session_summaries is True
