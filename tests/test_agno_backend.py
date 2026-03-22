import sys
from types import ModuleType
from importlib.util import find_spec

import pytest
from clawbridge.backends.agno import AgnoBackend
from clawbridge.core.agent import ClawAgent
from clawbridge.core.skill import ClawSkill
from clawbridge.core.types import (
    ChannelConfig,
    ChannelType,
    LLMProvider,
    ModelConfig,
    ToolDefinition,
)


def test_agno_backend_compile():
    # Only run if agno is installed
    if find_spec("agno") is None:
        pytest.skip("agno not installed")

    from clawbridge.core.types import ToolDefinition
    
    def my_tool(x: int) -> str:
        """My tool."""
        return str(x)
        
    from clawbridge.core.types import StorageConfig, StorageType

    agent = ClawAgent(
        name="TestAgent",
        model=ModelConfig(provider=LLMProvider.OPENAI, model="gpt-4o"),
        tools=[ToolDefinition(name="my_tool", description="My tool.", callable=my_tool)],
        storage=StorageConfig(enabled=True, type=StorageType.IN_MEMORY)
    )
    backend = AgnoBackend(agent)
    
    # Trigger lazy imports
    backend._ensure_imports()
    
    native_agent = backend.compile()
    
    assert len(native_agent.tools) == 1
    assert native_agent.tools[0] == my_tool
    # Check model
    from agno.models.openai import OpenAIChat
    assert isinstance(native_agent.model, OpenAIChat)
    assert native_agent.model.id == "gpt-4o"
    assert native_agent.model.temperature == 0.7
    assert native_agent.model.max_tokens == 4096
    
    # Check memory/db
    from agno.db.in_memory import InMemoryDb
    assert isinstance(native_agent.db, InMemoryDb)


def test_agno_backend_rejects_tools_without_callables() -> None:
    agent = ClawAgent(
        name="TestAgent",
        skills=[
            ClawSkill(
                name="web",
                tools=[
                    ToolDefinition(
                        name="search_web",
                        description="Search the web.",
                    )
                ],
            )
        ],
    )

    backend = AgnoBackend(agent)

    with pytest.raises(ValueError, match="Missing implementations for: search_web"):
        backend._build_tools()


def test_agno_backend_uses_native_mistral_target() -> None:
    agent = ClawAgent(
        name="MistralAgent",
        model=ModelConfig(
            provider=LLMProvider.MISTRAL,
            model="mistral-large-latest",
        ),
    )

    backend = AgnoBackend(agent)

    assert backend._resolve_model_target() == (
        "agno.models.mistral",
        "MistralChat",
        "mistral-large-latest",
    )


def test_agno_backend_falls_back_to_litellm_for_arbitrary_provider() -> None:
    agent = ClawAgent(
        name="GeminiAgent",
        model=ModelConfig(provider="vertex_ai", model="gemini-2.5-pro"),
    )

    backend = AgnoBackend(agent)

    assert backend._resolve_model_target() == (
        "agno.models.litellm",
        "LiteLLM",
        "vertex_ai/gemini-2.5-pro",
    )


def test_agno_backend_keeps_fully_qualified_litellm_models() -> None:
    agent = ClawAgent(
        name="OpenRouterAgent",
        model=ModelConfig(
            provider=LLMProvider.LITELLM,
            model="openrouter/openai/gpt-4.1-mini",
        ),
    )

    backend = AgnoBackend(agent)

    assert backend._resolve_model_target() == (
        "agno.models.litellm",
        "LiteLLM",
        "openrouter/openai/gpt-4.1-mini",
    )


def test_agno_backend_builds_interfaces_with_native_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeSlack:
        def __init__(self, **kwargs):
            captured["slack"] = kwargs

    class FakeWhatsapp:
        def __init__(self, **kwargs):
            captured["whatsapp"] = kwargs

    slack_module = ModuleType("agno.os.interfaces.slack")
    slack_module.Slack = FakeSlack
    whatsapp_module = ModuleType("agno.os.interfaces.whatsapp")
    whatsapp_module.Whatsapp = FakeWhatsapp

    monkeypatch.setitem(sys.modules, "agno.os.interfaces.slack", slack_module)
    monkeypatch.setitem(sys.modules, "agno.os.interfaces.whatsapp", whatsapp_module)
    monkeypatch.setenv("SLACK_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "secret")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "wa-token")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "wa-verify")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "wa-phone")

    agent = ClawAgent(
        name="Interfaces",
        channels=[
            ChannelConfig(
                type=ChannelType.SLACK,
                token_env="SLACK_TOKEN",
                verification_token_env="SLACK_SIGNING_SECRET",
            ),
            ChannelConfig(
                type=ChannelType.WHATSAPP,
                token_env="WHATSAPP_ACCESS_TOKEN",
                verification_token_env="WHATSAPP_VERIFY_TOKEN",
                bot_id_env="WHATSAPP_PHONE_NUMBER_ID",
            ),
        ],
    )

    backend = AgnoBackend(agent)
    sentinel_agent = object()
    backend._native_agent = sentinel_agent

    interfaces = backend._build_interfaces()

    assert len(interfaces) == 2
    assert captured["slack"]["agent"] is sentinel_agent
    assert captured["slack"]["token"] == "xoxb-test"
    assert captured["slack"]["signing_secret"] == "secret"
    assert captured["whatsapp"]["agent"] is sentinel_agent
    assert captured["whatsapp"]["access_token"] == "wa-token"
    assert captured["whatsapp"]["verify_token"] == "wa-verify"
    assert captured["whatsapp"]["phone_number_id"] == "wa-phone"


def test_agno_backend_rejects_missing_channel_env() -> None:
    agent = ClawAgent(
        name="BrokenSlack",
        channels=[
            ChannelConfig(
                type=ChannelType.SLACK,
                token_env="MISSING_SLACK_TOKEN",
                verification_token_env="SLACK_SIGNING_SECRET",
            )
        ],
    )

    backend = AgnoBackend(agent)

    with pytest.raises(ValueError, match="requires token_env='MISSING_SLACK_TOKEN'"):
        backend._build_interfaces()


def test_agno_backend_rejects_incomplete_whatsapp_channel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "wa-token")

    agent = ClawAgent(
        name="BrokenWhatsapp",
        channels=[
            ChannelConfig(
                type=ChannelType.WHATSAPP,
                token_env="WHATSAPP_ACCESS_TOKEN",
            )
        ],
    )

    backend = AgnoBackend(agent)

    with pytest.raises(ValueError, match="requires verification_token_env"):
        backend._build_interfaces()
