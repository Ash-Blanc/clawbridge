from importlib.util import find_spec

import pytest
from clawbridge.core.agent import ClawAgent
from clawbridge.core.types import ModelConfig, LLMProvider
from clawbridge.backends.agno import AgnoBackend


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
        model=ModelConfig(provider=LLMProvider.OPENAI, model_id="gpt-4o"),
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
    
    # Check memory/db
    from agno.db.in_memory import InMemoryDb
    assert isinstance(native_agent.db, InMemoryDb)
