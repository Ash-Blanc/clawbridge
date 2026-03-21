"""OpenClaw channel/session policy primitives."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from clawbridge.core.session import (
    OpenClawSessionContext,
    OpenClawSessionScope,
    OpenClawSessionTrigger,
)


class ChannelSurface(StrEnum):
    """Conversation surface for an inbound channel event."""

    DIRECT = "direct"
    GROUP = "group"


class HeartbeatPolicy(BaseModel):
    """Declarative heartbeat behavior used by schedulers/transports."""

    enabled: bool = False
    interval_seconds: int = 300
    prompt: str = "Run heartbeat checks and continue proactive maintenance."
    default_session_id: str = "heartbeat"


class GroupChannelPolicy(BaseModel):
    """Group-specific policy controls."""

    allowlist: list[str] = Field(default_factory=list)
    require_mention: bool = True


class DirectChannelPolicy(BaseModel):
    """Direct-message policy controls."""

    enabled: bool = True
    secure_mode: bool = True


class ChannelSessionPolicy(BaseModel):
    """Framework-neutral OpenClaw policy for DM/group/heartbeat traffic."""

    direct: DirectChannelPolicy = Field(default_factory=DirectChannelPolicy)
    groups: GroupChannelPolicy = Field(default_factory=GroupChannelPolicy)
    heartbeat: HeartbeatPolicy = Field(default_factory=HeartbeatPolicy)


class ChannelMessageContext(BaseModel):
    """Inbound channel metadata used to derive session semantics."""

    surface: ChannelSurface = ChannelSurface.DIRECT
    session_id: str = "default"
    group_id: str | None = None
    mentioned: bool = False
    is_heartbeat: bool = False


class ChannelPolicyDecision(BaseModel):
    """Result of evaluating channel/session policy."""

    allowed: bool
    reason: str | None = None
    session: OpenClawSessionContext = Field(default_factory=OpenClawSessionContext)


class HeartbeatMessage(BaseModel):
    """Heartbeat poll payload for runtime schedulers."""

    prompt: str
    context: ChannelMessageContext


def build_heartbeat_message(
    policy: ChannelSessionPolicy,
    *,
    session_id: str | None = None,
    group_id: str | None = None,
) -> HeartbeatMessage:
    """Build a heartbeat poll message/context from policy defaults."""
    return HeartbeatMessage(
        prompt=policy.heartbeat.prompt,
        context=ChannelMessageContext(
            surface=ChannelSurface.GROUP if group_id else ChannelSurface.DIRECT,
            session_id=session_id or policy.heartbeat.default_session_id,
            group_id=group_id,
            mentioned=False,
            is_heartbeat=True,
        ),
    )


def evaluate_channel_policy(
    policy: ChannelSessionPolicy,
    context: ChannelMessageContext,
) -> ChannelPolicyDecision:
    """Evaluate inbound channel context and return session policy decision."""
    if context.is_heartbeat:
        if not policy.heartbeat.enabled:
            return ChannelPolicyDecision(
                allowed=False,
                reason="Heartbeat handling is disabled.",
            )
        heartbeat_session_id = context.session_id or policy.heartbeat.default_session_id
        return ChannelPolicyDecision(
            allowed=True,
            session=OpenClawSessionContext(
                session_id=heartbeat_session_id,
                scope=OpenClawSessionScope.SHARED,
                trigger=OpenClawSessionTrigger.HEARTBEAT,
                mentioned=False,
                group_id=context.group_id,
            ),
        )

    if context.surface == ChannelSurface.DIRECT:
        if not policy.direct.enabled:
            return ChannelPolicyDecision(
                allowed=False,
                reason="Direct-message handling is disabled.",
            )
        return ChannelPolicyDecision(
            allowed=True,
            session=OpenClawSessionContext(
                session_id=context.session_id,
                scope=OpenClawSessionScope.DIRECT_MESSAGE,
                trigger=OpenClawSessionTrigger.USER_MESSAGE,
                mentioned=context.mentioned,
            ),
        )

    if policy.groups.allowlist and (context.group_id not in policy.groups.allowlist):
        return ChannelPolicyDecision(
            allowed=False,
            reason=f"Group '{context.group_id}' is not in the allowed group list.",
        )
    if policy.groups.require_mention and not context.mentioned:
        return ChannelPolicyDecision(
            allowed=False,
            reason="Group message ignored because mention is required.",
        )
    return ChannelPolicyDecision(
        allowed=True,
        session=OpenClawSessionContext(
            session_id=context.session_id,
            scope=OpenClawSessionScope.GROUP,
            trigger=(
                OpenClawSessionTrigger.MENTION
                if context.mentioned
                else OpenClawSessionTrigger.USER_MESSAGE
            ),
            mentioned=context.mentioned,
            group_id=context.group_id,
        ),
    )
