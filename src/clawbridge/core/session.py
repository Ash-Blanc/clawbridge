"""OpenClaw session scope metadata."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class OpenClawSessionScope(StrEnum):
    """Session scope categories used for prompt and memory loading."""

    MAIN = "main"
    DIRECT_MESSAGE = "direct_message"
    SHARED = "shared"
    GROUP = "group"


class OpenClawSessionTrigger(StrEnum):
    """What caused the current session execution."""

    USER_MESSAGE = "user_message"
    MENTION = "mention"
    HEARTBEAT = "heartbeat"


class OpenClawSessionContext(BaseModel):
    """Runtime session context for OpenClaw-style runs."""

    session_id: str = "default"
    scope: OpenClawSessionScope = OpenClawSessionScope.MAIN
    include_bootstrap_files: bool = False
    trigger: OpenClawSessionTrigger = OpenClawSessionTrigger.USER_MESSAGE
    mentioned: bool = False
    group_id: str | None = None

    def loads_curated_memory(self) -> bool:
        """Return True when `MEMORY.md` should be injected."""
        if self.trigger == OpenClawSessionTrigger.HEARTBEAT:
            return False
        return self.scope in {
            OpenClawSessionScope.MAIN,
            OpenClawSessionScope.DIRECT_MESSAGE,
        }

    def loads_daily_memory(self) -> bool:
        """Return True when dated memory notes should be injected."""
        return True

    def is_heartbeat(self) -> bool:
        """Return True for heartbeat-triggered runs."""
        return self.trigger == OpenClawSessionTrigger.HEARTBEAT
