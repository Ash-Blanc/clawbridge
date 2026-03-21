from __future__ import annotations

from pathlib import Path

import pytest

from clawbridge.backends.agentica import AgenticaBackend
from clawbridge.core.agent import ClawAgent
from clawbridge.core.sandbox import (
    SandboxConfig,
    SandboxExecutionEnvironment,
    SandboxMode,
    SandboxScope,
    WorkspaceAccess,
)
from clawbridge.core.session import OpenClawSessionContext, OpenClawSessionScope


def test_sandbox_runtime_for_main_session_stays_on_host(tmp_path: Path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("Agent rules", encoding="utf-8")

    agent = ClawAgent(
        name="Sandboxed",
        workspace_path=workspace_dir,
        sandbox=SandboxConfig(
            mode=SandboxMode.NON_MAIN,
            scope=SandboxScope.SESSION,
            workspace_access=WorkspaceAccess.RO,
        ),
    )

    prompt = agent.build_system_prompt()

    assert "Execution environment: host" in prompt
    assert "Workspace access: ro" in prompt
    assert "Tools run on the host." in prompt


def test_sandbox_runtime_for_shared_session_uses_isolated_workspace(
    tmp_path: Path,
) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("Agent rules", encoding="utf-8")

    agent = ClawAgent(
        name="Sandboxed",
        workspace_path=workspace_dir,
        sandbox=SandboxConfig(
            mode=SandboxMode.NON_MAIN,
            scope=SandboxScope.SESSION,
            workspace_access=WorkspaceAccess.RO,
        ),
    )

    prompt = agent.build_system_prompt(
        session_context=OpenClawSessionContext(
            session_id="group-9",
            scope=OpenClawSessionScope.SHARED,
        )
    )

    assert "Execution environment: sandbox" in prompt
    assert "Workspace access: ro" in prompt
    assert "Active runtime workspace: /workspace" in prompt
    assert "Mounted host workspace path: /agent" in prompt
    assert "Sandbox workspace backing path:" in prompt


def test_sandbox_rw_requires_workspace_path() -> None:
    sandbox = SandboxConfig(
        mode=SandboxMode.ALL,
        workspace_access=WorkspaceAccess.RW,
    )

    with pytest.raises(ValueError, match="requires an agent workspace path"):
        sandbox.resolve_runtime(
            session=OpenClawSessionContext(),
            workspace_path=None,
        )


def test_agentica_backend_exposes_runtime_metadata(tmp_path: Path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("Agent rules", encoding="utf-8")

    agent = ClawAgent(
        name="AgenticaSandbox",
        workspace_path=workspace_dir,
        sandbox=SandboxConfig(
            mode=SandboxMode.ALL,
            scope=SandboxScope.SHARED,
            workspace_access=WorkspaceAccess.NONE,
        ),
    )

    backend = AgenticaBackend(agent)
    config = backend.compile()

    assert config.runtime.execution_environment == SandboxExecutionEnvironment.SANDBOX
    assert config.runtime.sandbox_scope == SandboxScope.SHARED
    assert config.runtime.workspace_access == WorkspaceAccess.NONE
    assert config.runtime.active_workspace_path == "/workspace"
