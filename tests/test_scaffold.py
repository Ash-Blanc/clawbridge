from __future__ import annotations

from pathlib import Path

import pytest

from clawbridge.builders import load_agent_config
from clawbridge.scaffold import STANDARD_WORKSPACE_FILES, create_openclaw_workspace


def test_create_openclaw_workspace_generates_standard_layout(
    tmp_path: Path,
) -> None:
    workspace_dir = create_openclaw_workspace(tmp_path / "workspace")

    for filename in STANDARD_WORKSPACE_FILES:
        assert (workspace_dir / filename).exists()
    assert (workspace_dir / "memory" / ".gitkeep").exists()
    assert (workspace_dir / "skills" / "hello_world" / "SKILL.md").exists()
    assert (workspace_dir / "skills" / "hello_world" / "tools.py").exists()
    assert (workspace_dir / "agent.yaml").exists()

    bootstrap_text = (workspace_dir / "BOOTSTRAP.md").read_text(encoding="utf-8")
    assert "remove this file" in bootstrap_text.lower()

    agent = load_agent_config(workspace_dir / "agent.yaml")
    assert agent.workspace is not None
    assert agent.workspace.agents.name == "AGENTS.md"


def test_create_openclaw_workspace_non_empty_requires_force(
    tmp_path: Path,
) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "existing.txt").write_text("content", encoding="utf-8")

    with pytest.raises(FileExistsError, match="not empty"):
        create_openclaw_workspace(workspace_dir)


def test_create_openclaw_workspace_can_emit_multi_agent_config(
    tmp_path: Path,
) -> None:
    workspace_dir = create_openclaw_workspace(
        tmp_path / "workspace",
        include_multi_agent=True,
    )
    agents_file = workspace_dir / "agents.yaml"
    assert agents_file.exists()

    reviewer = load_agent_config(agents_file, agent_id="reviewer")
    assert reviewer.name == "Reviewer"
    assert reviewer.agent_id == "reviewer"
    assert reviewer.workspace_path == workspace_dir
    assert reviewer.state_dir == workspace_dir / ".clawbridge" / "reviewer"
    assert reviewer.auth_profile == "reviewer"
    assert reviewer.workspace is not None
