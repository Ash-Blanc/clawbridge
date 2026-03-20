"""CLI entrypoint for clawbridge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="clawbridge",
        description="🦞 Deploy OpenClaw-like agents to any framework",
    )
    sub = parser.add_subparsers(dest="command")

    # ── run ──
    run_p = sub.add_parser("run", help="Run an agent interactively")
    run_p.add_argument("--name", default="Claw")
    run_p.add_argument("--backend", default="agno", choices=["agno", "agentica"])
    run_p.add_argument("--model", default="claude-sonnet-4-20250514")
    run_p.add_argument("--provider", default="anthropic")
    run_p.add_argument("--skills-dir", type=Path, default=None)
    run_p.add_argument("--personality", default="")

    # ── skills ──
    skills_p = sub.add_parser("skills", help="List discovered skills")
    skills_p.add_argument("--dir", type=Path, default=Path("./skills"))

    # ── dev ──
    dev_p = sub.add_parser("dev", help="Start the local development server (Next.js style)")
    dev_p.add_argument("--host", default="127.0.0.1")
    dev_p.add_argument("--port", type=int, default=8000)

    # ── serve ──
    serve_p = sub.add_parser("serve", help="Serve agent as HTTP API")
    serve_p.add_argument("--backend", default="agno")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--host", default="0.0.0.0")

    # ── init ──
    init_p = sub.add_parser("init", help="Initialize a new OpenClaw/Agno project")
    init_p.add_argument("name", nargs="?", default="my-claw-app", help="Project directory name")

    args = parser.parse_args()

    match args.command:
        case "run":
            _cmd_run(args)
        case "skills":
            _cmd_skills(args)
        case "serve":
            _cmd_serve(args)
        case "dev":
            _cmd_dev(args)
        case "init":
            _cmd_init(args)
        case _:
            parser.print_help()


def _cmd_dev(args: argparse.Namespace) -> None:
    from clawbridge.app import ClawApp
    from rich.console import Console
    console = Console()
    
    app = ClawApp()
    console.print(f"🦞 Starting ClawBridge Dev Server on http://{args.host}:{args.port}")
    try:
        app.serve(host=args.host, port=args.port, reload=True)
    except Exception as e:
        console.print(f"[bold red]Failed to start server:[/bold red] {e}")


def _cmd_run(args: argparse.Namespace) -> None:
    from clawbridge.bridge import create_agent

    skill_paths = [str(args.skills_dir)] if args.skills_dir else []

    bridge = create_agent(
        name=args.name,
        backend=args.backend,
        model=args.model,
        provider=args.provider,
        skills=skill_paths,
        personality=args.personality,
    )

    console.print(Panel(
        f"🦞 [bold]{bridge.agent.name}[/bold] ready "
        f"([cyan]{args.backend}[/cyan] backend)\n"
        f"Model: {args.provider}/{args.model}\n"
        f"Skills: {len(bridge.agent.skills)} loaded\n"
        f"Type [bold red]quit[/bold red] to exit.",
        title="clawbridge",
    ))

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.strip().lower() in ("quit", "exit", "q"):
            break

        response = bridge.chat(user_input)
        console.print(f"[bold blue]{bridge.agent.name}:[/bold blue] {response}\n")


def _cmd_skills(args: argparse.Namespace) -> None:
    from clawbridge.skills.loader import SkillLoader

    loader = SkillLoader([args.dir])
    skills = loader.load_all()

    if not skills:
        console.print("[yellow]No skills found.[/yellow]")
        return

    table = Table(title="🦞 Discovered Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Version")
    table.add_column("Tools", justify="right")
    table.add_column("Description")

    for s in skills:
        table.add_row(
            s.name, s.category, s.version,
            str(len(s.tools)), s.description[:60],
        )

    console.print(table)


def _cmd_serve(args: argparse.Namespace) -> None:
    import asyncio
    from clawbridge.bridge import create_agent

    bridge = create_agent(backend=args.backend)
    console.print(
        f"🦞 Serving on http://{args.host}:{args.port} "
        f"({args.backend} backend)"
    )
    asyncio.run(bridge.serve(host=args.host, port=args.port))


def _cmd_init(args: argparse.Namespace) -> None:
    import os
    from pathlib import Path
    
    project_dir = Path(args.name)
    if project_dir.exists():
        console.print(f"[bold red]Error:[/bold red] Directory '{args.name}' already exists.")
        return

    project_dir.mkdir(parents=True)
    (project_dir / "agents").mkdir()
    (project_dir / "skills").mkdir()
    (project_dir / "knowledge").mkdir()
    
    # 1. Global config
    config_yaml = """name: My ClawBridge App
description: A multi-agent AI project.
server:
  host: 127.0.0.1
  port: 8000
"""
    (project_dir / "claw.config.yaml").write_text(config_yaml)

    # 2. Sample Agent
    agent_yaml = """name: Assistant
description: A personal OpenClaw agent powered by Agno.
personality: I am a helpful, concise, and capable AI assistant.
model:
  provider: openai
  model_id: gpt-4o
storage:
  enabled: true
  type: sqlite
  db_url: agent.db
"""
    (project_dir / "agents" / "assistant.yaml").write_text(agent_yaml)

    # 3. Sample skill
    skill_dir = project_dir / "skills" / "hello_world"
    skill_dir.mkdir(parents=True)
    
    skill_md = """---
name: hello-world
description: A simple hello world skill
version: 1.0.0
tools:
  - name: say_hello
    description: Returns a greeting message.
---
# Skill: Hello World
This skill provides a simple greeting capability.
"""
    (skill_dir / "SKILL.md").write_text(skill_md)
    
    tools_py = """def say_hello() -> str:
    \"\"\"Returns a greeting message.\"\"\"
    return "Hello from your new OpenClaw skill!"
"""
    (skill_dir / "tools.py").write_text(tools_py)
    
    # 4. Sample knowledge
    (project_dir / "knowledge" / "readme.md").write_text("# Knowledge Base\nDrop documents here to be ingested by agents.\n")

    console.print(f"🦞 [bold green]Successfully initialized '{args.name}'[/bold green]")
    console.print(f"\nNext steps:\n  cd {args.name}\n  clawbridge dev\n")


if __name__ == "__main__":
    main()