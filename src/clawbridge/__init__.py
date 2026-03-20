"""
clawbridge — Deploy OpenClaw-like agents to any framework. 🦞

Usage:
    from clawbridge import ClawAgent, ClawBridge, ClawSkill, create_agent

    # Quick start
    agent = create_agent(name="Molty", backend="agno")
    print(agent.chat("Hello!"))

    # Full control
    agent_def = ClawAgent(
        name="Molty",
        personality="Helpful and witty",
        skills=[ClawSkill.from_skill_md("./skills/web_search")],
    )
    bridge = ClawBridge(agent_def, backend="agentica")
"""

from clawbridge.bridge import ClawBridge, create_agent
from clawbridge.core.agent import ClawAgent
from clawbridge.core.memory import ClawMemory
from clawbridge.core.skill import ClawSkill
from clawbridge.core.types import (
    Backend,
    LLMProvider,
    MemoryConfig,
    ModelConfig,
    ToolDefinition,
    ToolParameter,
)

__all__ = [
    "ClawAgent",
    "ClawBridge",
    "ClawMemory",
    "ClawSkill",
    "Backend",
    "LLMProvider",
    "MemoryConfig",
    "ModelConfig",
    "ToolDefinition",
    "ToolParameter",
    "create_agent",
]

__version__ = "0.1.0"