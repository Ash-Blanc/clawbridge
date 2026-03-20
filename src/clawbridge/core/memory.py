"""
Cross-session memory abstraction — a key OpenClaw pattern.

OpenClaw maintains persistent and adaptive behavior across sessions.
This module provides the same capability in a framework-agnostic way.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from clawbridge.core.types import MemoryConfig


class MemoryEntry(BaseModel):
    """A single memory record."""

    key: str
    value: Any
    category: str = "general"       # "fact", "preference", "context", etc.
    timestamp: float = Field(default_factory=time.time)
    session_id: str | None = None
    ttl: float | None = None        # time-to-live in seconds

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.time() - self.timestamp) > self.ttl


class ConversationMessage(BaseModel):
    """A single message in conversation history."""

    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: float = Field(default_factory=time.time)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClawMemory:
    """
    Persistent, cross-session memory store.

    Provides both:
    - Long-term memory (facts, preferences, learned behaviors)
    - Short-term memory (conversation context, recent interactions)
    """

    def __init__(self, config: MemoryConfig | None = None):
        self.config = config or MemoryConfig()
        self._long_term: dict[str, MemoryEntry] = {}
        self._conversations: dict[str, list[ConversationMessage]] = {}
        self._persist_path = Path(self.config.persist_path)

        if self.config.enabled:
            self._load_from_disk()

    # ── Long-term memory ──

    def remember(
        self,
        key: str,
        value: Any,
        category: str = "general",
        ttl: float | None = None,
    ) -> None:
        """Store a long-term memory."""
        entry = MemoryEntry(key=key, value=value, category=category, ttl=ttl)
        self._long_term[key] = entry
        self._persist()

    def recall(self, key: str) -> Any | None:
        """Retrieve a long-term memory."""
        entry = self._long_term.get(key)
        if entry is None or entry.is_expired:
            return None
        return entry.value

    def recall_by_category(self, category: str) -> dict[str, Any]:
        """Recall all memories in a category."""
        return {
            k: v.value
            for k, v in self._long_term.items()
            if v.category == category and not v.is_expired
        }

    def forget(self, key: str) -> None:
        """Remove a memory."""
        self._long_term.pop(key, None)
        self._persist()

    def get_context_summary(self) -> str:
        """Generate a summary of all memories for system prompt injection."""
        if not self._long_term:
            return ""
        lines = ["## Agent Memory"]
        by_cat: dict[str, list[tuple[str, Any]]] = {}
        for k, v in self._long_term.items():
            if not v.is_expired:
                by_cat.setdefault(v.category, []).append((k, v.value))
        for cat, items in sorted(by_cat.items()):
            lines.append(f"### {cat.title()}")
            for key, val in items:
                lines.append(f"- **{key}**: {val}")
        return "\n".join(lines)

    # ── Short-term / conversation memory ──

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        **metadata: Any,
    ) -> None:
        """Add a message to conversation history."""
        self._conversations.setdefault(session_id, []).append(
            ConversationMessage(role=role, content=content, metadata=metadata)
        )
        # Trim if needed
        max_msgs = self.config.max_context_messages
        if len(self._conversations[session_id]) > max_msgs:
            self._conversations[session_id] = (
                self._conversations[session_id][-max_msgs:]
            )

    def get_conversation(self, session_id: str) -> list[ConversationMessage]:
        """Get conversation history for a session."""
        return self._conversations.get(session_id, [])

    # ── Persistence ──

    def _persist(self) -> None:
        if not self.config.enabled:
            return
        self._persist_path.mkdir(parents=True, exist_ok=True)
        data = {k: v.model_dump() for k, v in self._long_term.items()}
        (self._persist_path / "long_term.json").write_text(
            json.dumps(data, indent=2, default=str)
        )

    def _load_from_disk(self) -> None:
        lt_path = self._persist_path / "long_term.json"
        if lt_path.exists():
            raw = json.loads(lt_path.read_text())
            self._long_term = {
                k: MemoryEntry(**v) for k, v in raw.items()
            }