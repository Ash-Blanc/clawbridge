"""OpenClaw workspace file model and loader."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from clawbridge.core.session import OpenClawSessionContext


class WorkspaceContextScope(StrEnum):
    ALWAYS = "always"
    MAIN_SESSION_ONLY = "main_session_only"
    BOOTSTRAP_ONLY = "bootstrap_only"
    HEARTBEAT_ONLY = "heartbeat_only"


class WorkspaceDocument(BaseModel):
    """A single OpenClaw workspace document."""

    name: str
    path: Path
    content: str
    required: bool = False
    scope: WorkspaceContextScope = WorkspaceContextScope.ALWAYS
    ephemeral: bool = False
    document_date: date | None = None

    model_config = {"arbitrary_types_allowed": True}


class OpenClawWorkspace(BaseModel):
    """Structured view of an OpenClaw workspace directory."""

    root_dir: Path
    agents: WorkspaceDocument
    soul: WorkspaceDocument | None = None
    tools: WorkspaceDocument | None = None
    identity: WorkspaceDocument | None = None
    user: WorkspaceDocument | None = None
    heartbeat: WorkspaceDocument | None = None
    bootstrap: WorkspaceDocument | None = None
    memory: WorkspaceDocument | None = None
    daily_memory: list[WorkspaceDocument] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_dir(cls, path: str | Path) -> OpenClawWorkspace:
        """Load the standard OpenClaw workspace files from a directory."""
        root_dir = Path(path).expanduser().resolve()
        if not root_dir.exists() or not root_dir.is_dir():
            raise FileNotFoundError(f"Workspace directory not found: {root_dir}")

        agents_path = root_dir / "AGENTS.md"
        if not agents_path.exists():
            raise FileNotFoundError(
                f"OpenClaw workspace requires AGENTS.md at: {agents_path}"
            )

        return cls(
            root_dir=root_dir,
            agents=_read_document(agents_path, required=True),
            soul=_read_optional_document(root_dir / "SOUL.md"),
            tools=_read_optional_document(root_dir / "TOOLS.md"),
            identity=_read_optional_document(root_dir / "IDENTITY.md"),
            user=_read_optional_document(root_dir / "USER.md"),
            heartbeat=_read_optional_document(
                root_dir / "HEARTBEAT.md",
                scope=WorkspaceContextScope.HEARTBEAT_ONLY,
            ),
            bootstrap=_read_optional_document(
                root_dir / "BOOTSTRAP.md",
                scope=WorkspaceContextScope.BOOTSTRAP_ONLY,
                ephemeral=True,
            ),
            memory=_read_optional_document(
                root_dir / "MEMORY.md",
                scope=WorkspaceContextScope.MAIN_SESSION_ONLY,
            ),
            daily_memory=_load_daily_memory(root_dir / "memory"),
        )

    @classmethod
    def has_workspace(cls, path: str | Path) -> bool:
        """Return True when the directory looks like an OpenClaw workspace."""
        root_dir = Path(path).expanduser().resolve()
        return (root_dir / "AGENTS.md").exists()

    def get_documents_for_session(
        self,
        session: OpenClawSessionContext,
    ) -> list[WorkspaceDocument]:
        """Return workspace documents that should be injected for a session."""
        documents: list[WorkspaceDocument] = [self.agents]
        for document in [
            self.soul,
            self.tools,
            self.identity,
            self.user,
            self.heartbeat,
            self.bootstrap,
            self.memory,
        ]:
            if document is None:
                continue
            if document.scope == WorkspaceContextScope.MAIN_SESSION_ONLY and not session.loads_curated_memory():
                continue
            if document.scope == WorkspaceContextScope.BOOTSTRAP_ONLY and not session.include_bootstrap_files:
                continue
            if document.scope == WorkspaceContextScope.HEARTBEAT_ONLY and not session.is_heartbeat():
                continue
            documents.append(document)
        if session.loads_daily_memory():
            documents.extend(self.daily_memory)
        return documents


def _read_document(
    path: Path,
    *,
    required: bool = False,
    scope: WorkspaceContextScope = WorkspaceContextScope.ALWAYS,
    ephemeral: bool = False,
    document_date: date | None = None,
) -> WorkspaceDocument:
    return WorkspaceDocument(
        name=path.name,
        path=path,
        content=path.read_text(encoding="utf-8"),
        required=required,
        scope=scope,
        ephemeral=ephemeral,
        document_date=document_date,
    )


def _read_optional_document(
    path: Path,
    *,
    scope: WorkspaceContextScope = WorkspaceContextScope.ALWAYS,
    ephemeral: bool = False,
) -> WorkspaceDocument | None:
    if not path.exists():
        return None
    return _read_document(path, scope=scope, ephemeral=ephemeral)


def _load_daily_memory(memory_dir: Path) -> list[WorkspaceDocument]:
    if not memory_dir.exists() or not memory_dir.is_dir():
        return []

    documents: list[WorkspaceDocument] = []
    for file_path in sorted(memory_dir.glob("*.md")):
        try:
            doc_date = date.fromisoformat(file_path.stem)
        except ValueError:
            continue
        documents.append(
            _read_document(
                file_path,
                scope=WorkspaceContextScope.ALWAYS,
                document_date=doc_date,
            )
        )
    return documents
