"""OpenClaw sandbox policy and runtime metadata."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from clawbridge.core.session import OpenClawSessionContext, OpenClawSessionScope


class SandboxMode(StrEnum):
    """High-level sandbox activation policy."""

    OFF = "off"
    NON_MAIN = "non_main"
    ALL = "all"


class SandboxScope(StrEnum):
    """Isolation boundary for sandbox execution."""

    SESSION = "session"
    AGENT = "agent"
    SHARED = "shared"


class WorkspaceAccess(StrEnum):
    """How the host workspace is exposed inside the sandbox."""

    NONE = "none"
    RO = "ro"
    RW = "rw"


class SandboxExecutionEnvironment(StrEnum):
    """Where tool execution happens for a session."""

    HOST = "host"
    SANDBOX = "sandbox"


class SandboxBindMountMode(StrEnum):
    """Bind-mount access mode."""

    RO = "ro"
    RW = "rw"


class SandboxBindMount(BaseModel):
    """Declarative bind mount configuration."""

    host_path: Path
    mount_path: str
    mode: SandboxBindMountMode = SandboxBindMountMode.RO

    model_config = {"arbitrary_types_allowed": True}


class BrowserSandboxConfig(BaseModel):
    """Declarative browser sandbox settings."""

    enabled: bool = False
    isolated_profile: bool = True
    headless: bool = True


class SandboxRuntimeMetadata(BaseModel):
    """Resolved runtime metadata exposed to prompts and builders."""

    execution_environment: SandboxExecutionEnvironment
    sandbox_mode: SandboxMode
    sandbox_scope: SandboxScope | None = None
    workspace_access: WorkspaceAccess | None = None
    active_workspace_path: str | None = None
    host_workspace_path: Path | None = None
    sandbox_workspace_host_path: Path | None = None
    mounted_agent_workspace_path: str | None = None
    bind_mounts: list[SandboxBindMount] = Field(default_factory=list)
    browser: BrowserSandboxConfig = Field(default_factory=BrowserSandboxConfig)
    notes: list[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}


class SandboxConfig(BaseModel):
    """Declarative OpenClaw-style sandbox policy."""

    mode: SandboxMode = SandboxMode.OFF
    scope: SandboxScope = SandboxScope.SESSION
    workspace_access: WorkspaceAccess = WorkspaceAccess.NONE
    workspace_root: Path = Path.home() / ".openclaw" / "sandboxes"
    bind_mounts: list[SandboxBindMount] = Field(default_factory=list)
    browser: BrowserSandboxConfig = Field(default_factory=BrowserSandboxConfig)

    model_config = {"arbitrary_types_allowed": True}

    def resolve_runtime(
        self,
        *,
        session: OpenClawSessionContext,
        workspace_path: Path | None,
    ) -> SandboxRuntimeMetadata:
        """Resolve runtime metadata for a concrete session."""
        if not self._uses_sandbox(session):
            notes = ["Tools run on the host."]
            if self.mode != SandboxMode.OFF:
                notes.append(
                    "Sandbox policy is configured but inactive for this session."
                )
            return SandboxRuntimeMetadata(
                execution_environment=SandboxExecutionEnvironment.HOST,
                sandbox_mode=self.mode,
                sandbox_scope=self.scope,
                workspace_access=self.workspace_access,
                active_workspace_path=str(workspace_path) if workspace_path else None,
                host_workspace_path=workspace_path,
                bind_mounts=self.bind_mounts,
                browser=self.browser,
                notes=notes,
            )

        if workspace_path is None and self.workspace_access != WorkspaceAccess.NONE:
            raise ValueError(
                "Sandbox workspace access requires an agent workspace path. "
                f"Got workspace_access={self.workspace_access.value} with no workspace."
            )

        sandbox_workspace_host_path = self._sandbox_workspace_host_path(
            session=session
        )
        active_workspace_path = "/workspace"
        mounted_agent_workspace_path: str | None = None
        notes = ["Tools run inside the sandbox."]

        if self.workspace_access == WorkspaceAccess.NONE:
            notes.append(
                "Host workspace is not mounted into the sandbox."
            )
        elif self.workspace_access == WorkspaceAccess.RO:
            mounted_agent_workspace_path = "/agent"
            notes.append(
                "Host workspace is mounted read-only at /agent; write/edit/apply_patch should be treated as unavailable."
            )
        elif self.workspace_access == WorkspaceAccess.RW:
            mounted_agent_workspace_path = "/workspace"
            notes.append(
                "Host workspace is mounted read/write at /workspace."
            )

        return SandboxRuntimeMetadata(
            execution_environment=SandboxExecutionEnvironment.SANDBOX,
            sandbox_mode=self.mode,
            sandbox_scope=self.scope,
            workspace_access=self.workspace_access,
            active_workspace_path=active_workspace_path,
            host_workspace_path=workspace_path,
            sandbox_workspace_host_path=sandbox_workspace_host_path,
            mounted_agent_workspace_path=mounted_agent_workspace_path,
            bind_mounts=self.bind_mounts,
            browser=self.browser,
            notes=notes,
        )

    def _uses_sandbox(self, session: OpenClawSessionContext) -> bool:
        if self.mode == SandboxMode.OFF:
            return False
        if self.mode == SandboxMode.ALL:
            return True
        return session.scope != OpenClawSessionScope.MAIN

    def _sandbox_workspace_host_path(
        self,
        *,
        session: OpenClawSessionContext,
    ) -> Path:
        root = self.workspace_root.expanduser()
        if self.scope == SandboxScope.SHARED:
            return root / "shared"
        if self.scope == SandboxScope.AGENT:
            return root / "agent"
        return root / session.session_id
