from __future__ import annotations

from pathlib import Path

import pytest

from clawbridge.builders import load_agent_config
from clawbridge.core.agent import ClawAgent
from clawbridge.core.session import OpenClawSessionContext, OpenClawSessionScope
from clawbridge.core.workspace import OpenClawWorkspace, WorkspaceContextScope


def test_workspace_loader_reads_standard_files(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    (tmp_path / "SOUL.md").write_text("Core identity", encoding="utf-8")
    (tmp_path / "HEARTBEAT.md").write_text("Heartbeat note", encoding="utf-8")
    (tmp_path / "BOOTSTRAP.md").write_text("One time setup", encoding="utf-8")
    (tmp_path / "MEMORY.md").write_text("Long-term memory", encoding="utf-8")
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "2026-03-20.md").write_text("Yesterday", encoding="utf-8")
    (memory_dir / "notes.md").write_text("Ignore me", encoding="utf-8")

    workspace = OpenClawWorkspace.from_dir(tmp_path)

    assert workspace.agents.required is True
    assert workspace.soul is not None
    assert workspace.bootstrap is not None
    assert workspace.bootstrap.scope == WorkspaceContextScope.BOOTSTRAP_ONLY
    assert workspace.bootstrap.ephemeral is True
    assert workspace.heartbeat is not None
    assert workspace.heartbeat.scope == WorkspaceContextScope.HEARTBEAT_ONLY
    assert workspace.memory is not None
    assert workspace.memory.scope == WorkspaceContextScope.MAIN_SESSION_ONLY
    assert len(workspace.daily_memory) == 1
    assert workspace.daily_memory[0].document_date is not None


def test_workspace_loader_requires_agents_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="AGENTS.md"):
        OpenClawWorkspace.from_dir(tmp_path)


def test_load_agent_config_loads_explicit_workspace_path(tmp_path: Path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    (workspace_dir / "USER.md").write_text("User context", encoding="utf-8")

    config_path = tmp_path / "agent.yaml"
    config_path.write_text(
        """
name: WorkspaceBacked
workspace_path: ./workspace
""".strip(),
        encoding="utf-8",
    )

    agent = load_agent_config(config_path)

    assert agent.workspace_path == workspace_dir.resolve()
    assert agent.workspace is not None
    assert agent.workspace.user is not None


def test_load_agent_config_auto_detects_adjacent_workspace(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    config_path = tmp_path / "agent.yaml"
    config_path.write_text("name: AutoWorkspace", encoding="utf-8")

    agent = load_agent_config(config_path)

    assert agent.workspace_path == tmp_path.resolve()
    assert agent.workspace is not None


def test_load_agent_config_preserves_existing_workspace_instance(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    workspace = OpenClawWorkspace.from_dir(tmp_path)
    agent = ClawAgent(name="Direct", workspace=workspace)

    loaded = load_agent_config(agent)

    assert loaded.workspace is not None
    assert loaded.workspace.root_dir == workspace.root_dir


def test_workspace_documents_for_shared_sessions_skip_curated_memory(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("Agent rules", encoding="utf-8")
    (tmp_path / "MEMORY.md").write_text("Long-term memory", encoding="utf-8")
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "2026-03-20.md").write_text("Recent note", encoding="utf-8")

    workspace = OpenClawWorkspace.from_dir(tmp_path)

    shared_documents = workspace.get_documents_for_session(
        OpenClawSessionContext(scope=OpenClawSessionScope.SHARED)
    )

    assert all(document.name != "MEMORY.md" for document in shared_documents)
    assert any(document.document_date is not None for document in shared_documents)
