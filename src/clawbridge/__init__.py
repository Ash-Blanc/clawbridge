"""
clawbridge — OpenClaw-style skills, prompts, and builders for agent frameworks.

Usage:
    from clawbridge import ClawAgent, build_agno_agent

    agent = ClawAgent(
        name="Molty",
        personality="Helpful and witty",
    )
    native_agent = build_agno_agent(agent)
"""

from clawbridge.builders import build_agno_agent, build_agentica_agent, load_agent_config
from clawbridge.core.agent import ClawAgent
from clawbridge.core.channel import (
    ChannelMessageContext,
    ChannelPolicyDecision,
    ChannelSessionPolicy,
    ChannelSurface,
    DirectChannelPolicy,
    GroupChannelPolicy,
    HeartbeatMessage,
    HeartbeatPolicy,
    build_heartbeat_message,
    evaluate_channel_policy,
)
from clawbridge.core.memory import ClawMemory
from clawbridge.core.multi_agent import MultiAgentConfig, MultiAgentDefinition
from clawbridge.core.prompt import OpenClawPromptBuilder, OpenClawPromptContext, OpenClawPromptMode
from clawbridge.core.sandbox import (
    BrowserSandboxConfig,
    SandboxBindMount,
    SandboxBindMountMode,
    SandboxConfig,
    SandboxExecutionEnvironment,
    SandboxMode,
    SandboxRuntimeMetadata,
    SandboxScope,
    WorkspaceAccess,
)
from clawbridge.core.session import (
    OpenClawSessionContext,
    OpenClawSessionScope,
    OpenClawSessionTrigger,
)
from clawbridge.core.skill import (
    ClawSkill,
    SkillLoadRecord,
    SkillLoadStatus,
    SkillRequirements,
    SkillSourceKind,
)
from clawbridge.scaffold import create_openclaw_workspace
from clawbridge.core.workspace import OpenClawWorkspace, WorkspaceContextScope, WorkspaceDocument
from clawbridge.core.types import (
    LLMProvider,
    MemoryConfig,
    ModelConfig,
    ToolDefinition,
    ToolParameter,
)

__all__ = [
    "ClawAgent",
    "ClawMemory",
    "MultiAgentConfig",
    "MultiAgentDefinition",
    "ChannelMessageContext",
    "ChannelPolicyDecision",
    "ChannelSessionPolicy",
    "ChannelSurface",
    "DirectChannelPolicy",
    "GroupChannelPolicy",
    "HeartbeatMessage",
    "HeartbeatPolicy",
    "build_heartbeat_message",
    "evaluate_channel_policy",
    "OpenClawPromptBuilder",
    "OpenClawPromptContext",
    "OpenClawPromptMode",
    "SandboxBindMount",
    "SandboxBindMountMode",
    "SandboxConfig",
    "SandboxExecutionEnvironment",
    "SandboxMode",
    "SandboxRuntimeMetadata",
    "SandboxScope",
    "WorkspaceAccess",
    "BrowserSandboxConfig",
    "OpenClawSessionContext",
    "OpenClawSessionScope",
    "OpenClawSessionTrigger",
    "ClawSkill",
    "SkillLoadRecord",
    "SkillLoadStatus",
    "SkillRequirements",
    "SkillSourceKind",
    "OpenClawWorkspace",
    "WorkspaceContextScope",
    "WorkspaceDocument",
    "LLMProvider",
    "MemoryConfig",
    "ModelConfig",
    "ToolDefinition",
    "ToolParameter",
    "create_openclaw_workspace",
    "build_agno_agent",
    "build_agentica_agent",
    "load_agent_config",
]

__version__ = "0.1.0"
