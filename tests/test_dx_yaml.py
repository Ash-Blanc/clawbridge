import pytest
import os
from pathlib import Path
from clawbridge.bridge import compile_to_agno
from clawbridge.core.agent import ClawAgent

def test_compile_to_agno_from_yaml(tmp_path: Path):
    try:
        import agno
    except ImportError:
        pytest.skip("agno not installed")

    yaml_content = """
name: YamlAgent
description: A test agent from yaml
personality: Be very concise
model:
  provider: openai
  model_id: gpt-4o
storage:
  enabled: true
  type: in_memory
"""
    yaml_file = tmp_path / "agent.yaml"
    yaml_file.write_text(yaml_content)

    # Compile directly to an agno agent
    native_agent = compile_to_agno(yaml_file)

    assert native_agent is not None
    assert native_agent.name == "YamlAgent"
    assert native_agent.description == "A test agent from yaml"

    from agno.models.openai import OpenAIChat
    assert isinstance(native_agent.model, OpenAIChat)
    assert native_agent.model.id == "gpt-4o"

    from agno.db.in_memory import InMemoryDb
    assert isinstance(native_agent.db, InMemoryDb)
