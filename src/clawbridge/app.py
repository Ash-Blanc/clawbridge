"""
The clawbridge Application Compiler (Meta-Framework layer).

Provides a Next.js/Nuxt.js style Developer Experience by scanning the file system:
  /agents/*.yaml    -> Compiles to Agno Agents
  /skills/*         -> Auto-wired Skills & Tools
  claw.config.yaml  -> AgentOS global configuration
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from clawbridge.bridge import compile_to_agno
from clawbridge.core.agent import ClawAgent
from clawbridge.skills.loader import SkillLoader


class ClawApp:
    """
    A meta-framework application instance that discovers agents,
    skills, and configuration from the filesystem to build an Agno AgentOS.
    """

    def __init__(self, root_dir: str | Path = "."):
        self.root_dir = Path(root_dir).resolve()
        self.agents_dir = self.root_dir / "agents"
        self.skills_dir = self.root_dir / "skills"
        self.knowledge_dir = self.root_dir / "knowledge"
        self.config_path = self.root_dir / "claw.config.yaml"

        self.config: dict[str, Any] = {}
        self.agents: list[Any] = []
        
    def _load_config(self) -> None:
        """Load the global claw.config.yaml if it exists."""
        if self.config_path.exists():
            self.config = yaml.safe_load(self.config_path.read_text()) or {}

    def _discover_agents(self) -> None:
        """Scan the agents/ directory and compile all YAML files."""
        if not self.agents_dir.exists():
            return

        skill_loader = None
        if self.skills_dir.exists():
            skill_loader = SkillLoader([self.skills_dir])

        for file_path in self.agents_dir.glob("*.yaml"):
            try:
                agent_def = ClawAgent.from_yaml(file_path)
                
                # Auto-wire skills requested by the agent if they exist in the global skills/ dir
                if skill_loader:
                    # In a real scenario, we might only load skills listed in the YAML,
                    # but for DX, if the YAML doesn't specify, we can auto-load all,
                    # or filter based on agent definition.
                    # Currently compile_to_agno handles this, but let's be explicit here:
                    available_skills = skill_loader.load_all()
                    
                    # If the agent explicitly requested skills by name in YAML, wire them.
                    # Alternatively, we just provide the skills_dir to the compiler.
                    pass

                # Compile to native Agno agent
                native_agent = compile_to_agno(file_path)
                self.agents.append(native_agent)
            except Exception as e:
                print(f"Failed to load agent from {file_path.name}: {e}")

    def build_os(self) -> Any:
        """
        Build and return the native Agno AgentOS instance.
        """
        try:
            from agno.os import AgentOS
        except ImportError:
            raise ImportError("Agno is not installed. Run: pip install clawbridge[agno]")

        self._load_config()
        self._discover_agents()

        if not self.agents:
            raise RuntimeError(
                f"No agents found in {self.agents_dir}. "
                "Create an agent YAML file to get started."
            )

        os_kwargs: dict[str, Any] = {
            "agents": self.agents,
        }

        # Apply global config settings
        if "name" in self.config:
            os_kwargs["name"] = self.config["name"]
        if "description" in self.config:
            os_kwargs["description"] = self.config["description"]

        return AgentOS(**os_kwargs)

    def serve(self, host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
        """Build and serve the AgentOS."""
        agent_os = self.build_os()
        
        # Override with config if present
        server_config = self.config.get("server", {})
        host = server_config.get("host", host)
        port = server_config.get("port", port)
        
        app = agent_os.get_app()
        agent_os.serve(app=app, host=host, port=port, reload=reload)
