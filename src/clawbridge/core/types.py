"""Universal types for clawbridge."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Backend(StrEnum):
    AGNO = "agno"
    AGENTICA = "agentica"


class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    LOCAL = "local"


class ModelConfig(BaseModel):
    """LLM model configuration — framework-agnostic."""

    provider: LLMProvider = LLMProvider.ANTHROPIC
    model_id: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key_env: str | None = None  # e.g. "ANTHROPIC_API_KEY"
    base_url: str | None = None     # for local / custom endpoints

    @property
    def api_key(self) -> str | None:
        import os
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return None


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