"""OpenClaw-style system prompt composition."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field

from clawbridge.core.memory import ClawMemory
from clawbridge.core.sandbox import (
    SandboxExecutionEnvironment,
    SandboxRuntimeMetadata,
)
from clawbridge.core.session import OpenClawSessionContext
from clawbridge.core.workspace import OpenClawWorkspace, WorkspaceContextScope, WorkspaceDocument

if TYPE_CHECKING:
    from clawbridge.core.agent import ClawAgent


class OpenClawPromptMode(StrEnum):
    """Prompt profiles for different OpenClaw-style runs."""

    FULL = "full"
    MINIMAL = "minimal"
    NONE = "none"


class OpenClawPromptContext(BaseModel):
    """Runtime metadata injected into the prompt."""

    session: OpenClawSessionContext = Field(default_factory=OpenClawSessionContext)
    workspace_path: Path | None = None
    docs_path: Path | None = None
    docs_url: str | None = "https://docs.openclaw.ai"
    sandbox: SandboxRuntimeMetadata | None = None
    runtime_notes: list[str] = Field(default_factory=list)
    timezone_identifier: str = "Etc/UTC"
    current_datetime: datetime | None = None

    model_config = {"arbitrary_types_allowed": True}

    def resolve_now(self) -> datetime:
        if self.current_datetime is not None:
            return self.current_datetime
        try:
            tzinfo = ZoneInfo(self.timezone_identifier)
        except ZoneInfoNotFoundError:
            tzinfo = ZoneInfo("Etc/UTC")
        return datetime.now(tzinfo)


class OpenClawPromptBuilder:
    """Compose an OpenClaw-style system prompt."""

    WORKSPACE_FILE_ORDER = [
        "AGENTS.md",
        "SOUL.md",
        "TOOLS.md",
        "IDENTITY.md",
        "USER.md",
        "HEARTBEAT.md",
        "BOOTSTRAP.md",
        "MEMORY.md",
    ]
    MINIMAL_WORKSPACE_FILES = {"AGENTS.md", "TOOLS.md"}

    def build(
        self,
        agent: ClawAgent,
        *,
        memory: ClawMemory | None = None,
        context: OpenClawPromptContext | None = None,
        mode: OpenClawPromptMode = OpenClawPromptMode.FULL,
    ) -> str:
        if mode == OpenClawPromptMode.NONE:
            return agent.system_prompt.strip() if agent.system_prompt else ""

        prompt_context = self._normalize_context(agent, context)
        sections: list[str] = [
            self._render_identity(agent),
            self._render_tooling(agent),
            self._render_safety(agent),
            self._render_skills(agent, mode),
            self._render_self_update(agent, mode),
            self._render_workspace(agent, prompt_context),
            self._render_docs(prompt_context, mode),
            self._render_workspace_files(agent.workspace, prompt_context, mode),
            self._render_memory(memory),
            self._render_sandbox(prompt_context),
            self._render_current_time(prompt_context),
            self._render_runtime(agent, prompt_context),
            self._render_custom_instructions(agent),
        ]

        return "\n\n".join(section for section in sections if section)

    def _normalize_context(
        self,
        agent: ClawAgent,
        context: OpenClawPromptContext | None,
    ) -> OpenClawPromptContext:
        prompt_context = context.model_copy(deep=True) if context is not None else OpenClawPromptContext()
        if prompt_context.workspace_path is None and agent.workspace_path is not None:
            prompt_context.workspace_path = agent.workspace_path
        if prompt_context.docs_path is None and prompt_context.workspace_path is not None:
            candidate_docs = prompt_context.workspace_path / "docs"
            if candidate_docs.exists() and candidate_docs.is_dir():
                prompt_context.docs_path = candidate_docs
        if prompt_context.sandbox is None:
            prompt_context.sandbox = agent.sandbox.resolve_runtime(
                session=prompt_context.session,
                workspace_path=agent.workspace_path,
            )
        return prompt_context

    def _render_identity(self, agent: ClawAgent) -> str:
        lines = ["# Identity", f"- Name: {agent.name}"]
        if agent.agent_id:
            lines.append(f"- Agent id: {agent.agent_id}")
        if agent.description:
            lines.append(f"- Description: {agent.description}")
        if agent.personality:
            lines.append(f"- Personality: {agent.personality}")
        if agent.role:
            lines.append(f"- Role: {agent.role}")
        return "\n".join(lines)

    def _render_tooling(self, agent: ClawAgent) -> str:
        lines = [
            "# Tooling",
            "Use only the tools and skills available in this runtime.",
        ]
        tools = agent.get_all_tools()
        if not tools:
            lines.append("- No runtime tools are currently registered.")
            return "\n".join(lines)

        for tool in tools:
            param_parts = []
            for param in tool.parameters:
                required = "required" if param.required else "optional"
                param_parts.append(f"{param.name}:{param.type} ({required})")
            rendered_params = ", ".join(param_parts) if param_parts else "no params"
            lines.append(f"- {tool.name}: {rendered_params}")
        return "\n".join(lines)

    def _render_safety(self, agent: ClawAgent) -> str:
        lines = [
            "# Safety",
            "- Prefer accurate, minimal actions over speculative behavior.",
            "- Treat workspace files as user-owned source of truth.",
        ]
        if agent.markdown_output:
            lines.append("- Return markdown when the backend supports it.")
        return "\n".join(lines)

    def _render_skills(self, agent: ClawAgent, mode: OpenClawPromptMode) -> str:
        if not agent.skills:
            return "# Skills\n- No OpenClaw skills loaded."

        lines = ["# Skills"]
        for skill in agent.skills:
            lines.append(f"- {skill.name}: {skill.description or 'No description.'}")
            if mode == OpenClawPromptMode.FULL and skill.instructions:
                lines.append(f"  Instructions: {skill.instructions.strip()}")
        return "\n".join(lines)

    def _render_self_update(self, agent: ClawAgent, mode: OpenClawPromptMode) -> str:
        if mode == OpenClawPromptMode.MINIMAL:
            return "# Self-Update\n- Keep changes aligned with the active workspace and configured tools."
        return "\n".join(
            [
                "# Self-Update",
                "- Update standing behavior through workspace files, not hidden state.",
                "- Use skills, memory, and workspace notes as the persistent customization surface.",
            ]
        )

    def _render_workspace(self, agent: ClawAgent, context: OpenClawPromptContext) -> str:
        workspace_path = context.workspace_path or agent.workspace_path
        lines = ["# Workspace"]
        if workspace_path is None:
            lines.append("- No workspace path configured.")
        else:
            lines.append(f"- Active workspace: {workspace_path}")
        if agent.state_dir is not None:
            lines.append(f"- Agent state dir: {agent.state_dir}")
        if agent.auth_profile is not None:
            lines.append(f"- Auth profile: {agent.auth_profile}")
        lines.append(f"- Session scope: {context.session.scope}")
        lines.append(f"- Session trigger: {context.session.trigger}")
        if context.session.group_id is not None:
            lines.append(f"- Group id: {context.session.group_id}")
        lines.append(f"- Mentioned: {str(context.session.mentioned).lower()}")
        if context.sandbox is not None:
            lines.append(
                f"- Runtime workspace path: {context.sandbox.active_workspace_path or '[unavailable]'}"
            )
            if context.sandbox.mounted_agent_workspace_path is not None:
                lines.append(
                    "- Host workspace mount inside runtime: "
                    f"{context.sandbox.mounted_agent_workspace_path}"
                )
        if agent.workspace is not None:
            lines.append(f"- Loaded workspace documents: {self._count_workspace_documents(agent.workspace)}")
        return "\n".join(lines)

    def _render_docs(
        self,
        context: OpenClawPromptContext,
        mode: OpenClawPromptMode,
    ) -> str:
        if mode == OpenClawPromptMode.MINIMAL and context.docs_path is None and context.docs_url is None:
            return ""

        lines = ["# Docs"]
        if context.docs_path is not None:
            lines.append(f"- Local docs path: {context.docs_path}")
        if context.docs_url is not None:
            lines.append(f"- Reference docs: {context.docs_url}")
        if len(lines) == 1:
            lines.append("- No docs location configured.")
        return "\n".join(lines)

    def _render_workspace_files(
        self,
        workspace: OpenClawWorkspace | None,
        context: OpenClawPromptContext,
        mode: OpenClawPromptMode,
    ) -> str:
        lines = ["# Workspace Files"]
        if workspace is None:
            lines.append("- No workspace files loaded.")
            return "\n".join(lines)

        session_documents = workspace.get_documents_for_session(context.session)
        documents_by_name = {document.name: document for document in session_documents}
        for name in self.WORKSPACE_FILE_ORDER:
            if mode == OpenClawPromptMode.MINIMAL and name not in self.MINIMAL_WORKSPACE_FILES:
                continue
            if name == "BOOTSTRAP.md" and not context.session.include_bootstrap_files:
                continue
            document = documents_by_name.get(name)
            if document is None:
                if name == "MEMORY.md" and not context.session.loads_curated_memory():
                    continue
                if name == "HEARTBEAT.md" and not context.session.is_heartbeat():
                    continue
                lines.append(f"## {name}\n[missing]")
                continue
            lines.append(self._render_workspace_document(document))

        if mode == OpenClawPromptMode.FULL and context.session.loads_daily_memory():
            daily_memory = [document for document in session_documents if document.document_date is not None]
            if daily_memory:
                lines.append("## memory/*.md")
                for document in daily_memory:
                    lines.append(f"- {document.path.name}: {document.content.strip()}")
        return "\n\n".join(lines)

    def _render_memory(self, memory: ClawMemory | None) -> str:
        if memory is None:
            return ""
        summary = memory.get_context_summary()
        if not summary:
            return ""
        return f"# Runtime Memory\n{summary}"

    def _render_sandbox(self, context: OpenClawPromptContext) -> str:
        lines = ["# Sandbox"]
        sandbox = context.sandbox
        if sandbox is None:
            lines.append("- Running on the host with no sandbox metadata provided.")
            return "\n".join(lines)
        lines.append(f"- Mode: {sandbox.sandbox_mode}")
        lines.append(
            f"- Execution environment: {sandbox.execution_environment}"
        )
        if sandbox.sandbox_scope is not None:
            lines.append(f"- Scope: {sandbox.sandbox_scope}")
        if sandbox.workspace_access is not None:
            lines.append(f"- Workspace access: {sandbox.workspace_access}")
        if sandbox.active_workspace_path is not None:
            lines.append(
                f"- Active runtime workspace: {sandbox.active_workspace_path}"
            )
        if sandbox.sandbox_workspace_host_path is not None:
            lines.append(
                "- Sandbox workspace backing path: "
                f"{sandbox.sandbox_workspace_host_path}"
            )
        if sandbox.mounted_agent_workspace_path is not None:
            lines.append(
                "- Mounted host workspace path: "
                f"{sandbox.mounted_agent_workspace_path}"
            )
        if sandbox.bind_mounts:
            lines.append("- Additional bind mounts:")
            for bind_mount in sandbox.bind_mounts:
                lines.append(
                    "  "
                    f"- {bind_mount.host_path} -> {bind_mount.mount_path} ({bind_mount.mode})"
                )
        if sandbox.browser.enabled:
            lines.append("- Browser sandbox: enabled")
        else:
            lines.append("- Browser sandbox: disabled")
        for note in sandbox.notes:
            lines.append(f"- {note}")
        return "\n".join(lines)

    def _render_current_time(self, context: OpenClawPromptContext) -> str:
        now = context.resolve_now()
        return "\n".join(
            [
                "# Current Time",
                f"- Timezone: {context.timezone_identifier}",
                f"- Local time: {now.isoformat()}",
            ]
        )

    def _render_runtime(
        self,
        agent: ClawAgent,
        context: OpenClawPromptContext,
    ) -> str:
        lines = ["# Runtime"]
        lines.append(f"- Model: {agent.model.provider}/{agent.model.model}")
        if agent.agent_id is not None:
            lines.append(f"- Agent id: {agent.agent_id}")
        lines.append(f"- Session id: {context.session.session_id}")
        lines.append(f"- Trigger: {context.session.trigger}")
        if (
            context.sandbox is not None
            and context.sandbox.execution_environment
            == SandboxExecutionEnvironment.SANDBOX
        ):
            lines.append("- Runtime location: sandbox")
        if context.runtime_notes:
            for note in context.runtime_notes:
                lines.append(f"- {note}")
        return "\n".join(lines)

    def _render_custom_instructions(self, agent: ClawAgent) -> str:
        blocks: list[str] = []
        if agent.system_prompt:
            blocks.append("# System Prompt\n" + agent.system_prompt)
        if agent.additional_instructions:
            blocks.append(
                "# Additional Instructions\n" + "\n".join(f"- {item}" for item in agent.additional_instructions)
            )
        return "\n\n".join(blocks)

    def _workspace_documents_by_name(
        self,
        workspace: OpenClawWorkspace,
    ) -> dict[str, WorkspaceDocument]:
        documents: dict[str, WorkspaceDocument] = {workspace.agents.name: workspace.agents}
        for document in [
            workspace.soul,
            workspace.tools,
            workspace.identity,
            workspace.user,
            workspace.heartbeat,
            workspace.bootstrap,
            workspace.memory,
        ]:
            if document is not None:
                documents[document.name] = document
        return documents

    def _render_workspace_document(self, document: WorkspaceDocument) -> str:
        scope_suffix = ""
        if document.scope == WorkspaceContextScope.MAIN_SESSION_ONLY:
            scope_suffix = " [main session only]"
        elif document.scope == WorkspaceContextScope.BOOTSTRAP_ONLY:
            scope_suffix = " [bootstrap only]"
        elif document.scope == WorkspaceContextScope.HEARTBEAT_ONLY:
            scope_suffix = " [heartbeat only]"
        return f"## {document.name}{scope_suffix}\n{document.content.strip()}"

    def _count_workspace_documents(self, workspace: OpenClawWorkspace) -> int:
        count = 1
        for document in [
            workspace.soul,
            workspace.tools,
            workspace.identity,
            workspace.user,
            workspace.heartbeat,
            workspace.bootstrap,
            workspace.memory,
        ]:
            if document is not None:
                count += 1
        count += len(workspace.daily_memory)
        return count
