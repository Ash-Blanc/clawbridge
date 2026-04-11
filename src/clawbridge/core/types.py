"""Universal types for clawbridge."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    LITELLM = "litellm"
    LOCAL = "local"


class ModelConfig(BaseModel):
    """LLM model configuration for supported framework builders."""

    provider: str = LLMProvider.ANTHROPIC
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: str | None = None
    base_url: str | None = None     # for local / custom endpoints

    @field_validator("provider", mode="before")
    @classmethod
    def _normalize_provider(cls, value: str | LLMProvider) -> str:
        if isinstance(value, LLMProvider):
            return value.value
        normalized = str(value).strip().lower()
        if not normalized:
            raise ValueError("provider must not be empty")
        return normalized

    @property
    def provider_name(self) -> str:
        return self.provider

    @property
    def litellm_model_id(self) -> str:
        if "/" in self.model or self.provider_name == LLMProvider.LITELLM:
            return self.model
        return f"{self.provider_name}/{self.model}"


class ToolParameter(BaseModel):
    """A single parameter for a tool."""

    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None


class ToolDefinition(BaseModel):
    """Framework-agnostic tool definition."""

    name: str
    description: str
    parameters: list[ToolParameter] = Field(default_factory=list)
    callable: Any = None  # the actual Python callable
    # If the tool should be auto-invoked by the agent
    auto_invoke: bool = True


class StorageType(StrEnum):
    IN_MEMORY = "in_memory"
    SQLITE = "sqlite"
    POSTGRES = "postgres"


class StorageConfig(BaseModel):
    """Configuration for agent database/storage."""
    
    enabled: bool = False
    type: StorageType = StorageType.SQLITE
    db_url: str = "tmp/agent.db"  # Used for sqlite or postgres


class VectorDbType(StrEnum):
    LANCEDB = "lancedb"
    PGVECTOR = "pgvector"


class KnowledgeConfig(BaseModel):
    """Configuration for vector knowledge bases."""
    
    enabled: bool = False
    type: VectorDbType = VectorDbType.LANCEDB
    db_url: str = "tmp/lancedb"
    table_name: str = "agent_knowledge"
    search: bool = True
    add_to_context: bool = False
    max_results: int = 10
    embedder_model_id: str | None = None
    # Will typically contain paths or URLs to ingest
    sources: list[str] = Field(default_factory=list)


class ChannelType(StrEnum):
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"


class ChannelConfig(BaseModel):
    """Configuration for messaging interfaces (gateways)."""
    
    type: ChannelType
    token_env: str  # The environment variable holding the auth token
    bot_id_env: str | None = None
    verification_token_env: str | None = None  # Slack signing secret or WhatsApp verify token

    @property
    def token(self) -> str | None:
        import os
        return os.environ.get(self.token_env)


class MemoryConfig(BaseModel):
    """Memory / persistence configuration."""

    enabled: bool = True
    backend: str = "local"  # "local", "postgres", "redis"
    persist_path: str = ".clawbridge/memory"
    # Cross-session memory
    long_term: bool = True
    # Per-conversation context
    short_term: bool = True
    max_context_messages: int = 50


class AgentMemoryMode(StrEnum):
    """How the framework backend should handle native persistent memory.

    - OFF: Only use ClawMemory for prompt injection (current default behavior).
    - AUTOMATIC: Framework extracts and stores memories after each run.
    - AGENTIC: Agent gets memory tools and decides when to remember/forget.
    """
    OFF = "off"
    AUTOMATIC = "automatic"
    AGENTIC = "agentic"


class LearningConfig(BaseModel):
    """Self-improvement / learning configuration.

    When enabled, the framework backend stores learnings from agent runs
    and injects them into future sessions — similar to Hermes-agent's
    self-improvement loop.
    """
    enabled: bool = False
    add_learnings_to_context: bool = True


class SessionConfig(BaseModel):
    """Cross-session behavior configuration.

    Controls how the agent interacts with past sessions, manages context
    compression, and maintains continuity across conversations.
    """
    search_past_sessions: bool = False
    num_past_sessions_to_search: int = 3
    num_past_session_runs_in_search: int = 5
    enable_session_summaries: bool = False
    compress_tool_results: bool = False
    add_history_to_context: bool = True
    num_history_runs: int = 3
    reasoning: bool = False


class TeamMode(StrEnum):
    """Coordination mode for multi-agent teams.

    - COORDINATE: Leader decomposes work, delegates to members, synthesizes results.
    - ROUTE: Leader routes to a single specialist, returns their response directly.
    - BROADCAST: Delegates the same task to all members, leader synthesizes.
    - TASKS: Sequential task list execution until goal is complete.
    """
    COORDINATE = "coordinate"
    ROUTE = "route"
    BROADCAST = "broadcast"
    TASKS = "tasks"
