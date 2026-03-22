from __future__ import annotations

import asyncio
from pathlib import Path

from clawbridge.backends.base import ClawBackend
from clawbridge.builders import load_agent_config
from clawbridge.core.agent import ClawAgent
from clawbridge.core.channel import (
    ChannelMessageContext,
    ChannelSessionPolicy,
    ChannelSurface,
    DirectChannelPolicy,
    GroupChannelPolicy,
    HeartbeatPolicy,
    build_heartbeat_message,
)
from clawbridge.core.session import OpenClawSessionScope, OpenClawSessionTrigger


class _StubBackend(ClawBackend):
    def compile(self) -> object:
        return object()

    async def run(self, message: str, session_id: str = "default") -> str:
        session = self.get_session_context(session_id)
        return (
            f"{message}|scope={session.scope}|trigger={session.trigger}|"
            f"mentioned={str(session.mentioned).lower()}"
        )


def test_channel_policy_group_allowlist_and_mention_gating() -> None:
    policy = ChannelSessionPolicy(
        groups=GroupChannelPolicy(
            allowlist=["eng"],
            require_mention=True,
        )
    )

    blocked_group = ChannelMessageContext(
        surface=ChannelSurface.GROUP,
        session_id="group-eng",
        group_id="eng",
        mentioned=False,
    )
    denied_group = ChannelMessageContext(
        surface=ChannelSurface.GROUP,
        session_id="group-random",
        group_id="random",
        mentioned=True,
    )
    allowed_group = ChannelMessageContext(
        surface=ChannelSurface.GROUP,
        session_id="group-eng",
        group_id="eng",
        mentioned=True,
    )

    blocked_decision = _StubBackend(
        ClawAgent(channel_policy=policy)
    ).evaluate_channel_policy(blocked_group)
    denied_decision = _StubBackend(
        ClawAgent(channel_policy=policy)
    ).evaluate_channel_policy(denied_group)
    allowed_decision = _StubBackend(
        ClawAgent(channel_policy=policy)
    ).evaluate_channel_policy(allowed_group)

    assert blocked_decision.allowed is False
    assert "mention is required" in (blocked_decision.reason or "")
    assert denied_decision.allowed is False
    assert "not in the allowed group list" in (denied_decision.reason or "")
    assert allowed_decision.allowed is True
    assert allowed_decision.session.scope == OpenClawSessionScope.GROUP
    assert allowed_decision.session.trigger == OpenClawSessionTrigger.MENTION


def test_channel_policy_dm_context_loads_curated_memory() -> None:
    backend = _StubBackend(
        ClawAgent(
            channel_policy=ChannelSessionPolicy(
                direct=DirectChannelPolicy(enabled=True),
            )
        )
    )

    decision = backend.evaluate_channel_policy(
        ChannelMessageContext(
            surface=ChannelSurface.DIRECT,
            session_id="dm-user-1",
        )
    )

    assert decision.allowed is True
    assert decision.session.scope == OpenClawSessionScope.DIRECT_MESSAGE
    assert decision.session.loads_curated_memory() is True


def test_build_heartbeat_message_uses_policy_defaults() -> None:
    policy = ChannelSessionPolicy(
        heartbeat=HeartbeatPolicy(
            enabled=True,
            prompt="Heartbeat: refresh standing tasks.",
            default_session_id="hb-default",
        )
    )

    heartbeat_message = build_heartbeat_message(policy)

    assert heartbeat_message.prompt == "Heartbeat: refresh standing tasks."
    assert heartbeat_message.context.is_heartbeat is True
    assert heartbeat_message.context.session_id == "hb-default"


def test_backend_run_direct_and_group_helpers_use_policy() -> None:
    backend = _StubBackend(
        ClawAgent(
            channel_policy=ChannelSessionPolicy(
                groups=GroupChannelPolicy(
                    allowlist=["eng"],
                    require_mention=True,
                )
            )
        )
    )

    direct_result = asyncio.run(
        backend.run_direct_message(
            "hello",
            session_id="dm-user-1",
        )
    )
    group_result = asyncio.run(
        backend.run_group_message(
            "status",
            session_id="group-eng",
            group_id="eng",
            mentioned=True,
        )
    )

    assert "scope=direct_message" in direct_result
    assert "trigger=user_message" in direct_result
    assert "scope=group" in group_result
    assert "trigger=mention" in group_result


def test_channel_policy_heartbeat_messages_are_distinguishable(
    tmp_path: Path,
) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    (workspace_dir / "HEARTBEAT.md").write_text("Heartbeat instructions", encoding="utf-8")
    (workspace_dir / "MEMORY.md").write_text("Curated memory", encoding="utf-8")

    backend = _StubBackend(
        load_agent_config(
            ClawAgent(
                workspace_path=workspace_dir,
                channel_policy=ChannelSessionPolicy(
                    heartbeat=HeartbeatPolicy(enabled=True),
                ),
            )
        )
    )

    heartbeat_context = ChannelMessageContext(
        surface=ChannelSurface.GROUP,
        session_id="heartbeat-group",
        group_id="eng",
        is_heartbeat=True,
    )
    result = asyncio.run(
        backend.run_channel_message(
            "pulse",
            context=heartbeat_context,
        )
    )

    assert "scope=shared" in result
    assert "trigger=heartbeat" in result

    prompt = backend.build_system_prompt(
        session_context=backend.evaluate_channel_policy(heartbeat_context).session
    )
    assert "## HEARTBEAT.md [heartbeat only]" in prompt
    assert "Heartbeat instructions" in prompt
    assert "## MEMORY.md" not in prompt


def test_backend_run_heartbeat_uses_configured_prompt(tmp_path: Path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("Agent rules", encoding="utf-8")

    backend = _StubBackend(
        load_agent_config(
            ClawAgent(
                workspace_path=workspace_dir,
                channel_policy=ChannelSessionPolicy(
                    heartbeat=HeartbeatPolicy(
                        enabled=True,
                        prompt="Heartbeat: review current task list.",
                        default_session_id="hb-default",
                    )
                ),
            )
        )
    )

    result = asyncio.run(backend.run_heartbeat())

    assert result.startswith("Heartbeat: review current task list.")
    assert "scope=shared" in result
    assert "trigger=heartbeat" in result
