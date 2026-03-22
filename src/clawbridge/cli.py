"""CLI entrypoint for clawbridge."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="clawbridge",
        description=(
            "Build and deploy OpenClaw-style agents inside Agno or Agentica. "
            "Start with `clawbridge scaffold` for a workspace-first flow."
        ),
        epilog=(
            "Examples:\n"
            "  clawbridge scaffold ./my-workspace\n"
            "  clawbridge scaffold ./my-workspace --multi-agent\n"
            "  clawbridge init my-claw-app  # optional Agno deployment helper\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # ── run ──
    run_p = sub.add_parser("run", help="Run an OpenClaw-style agent inside a framework")
    run_p.add_argument("--name", default="Claw")
    run_p.add_argument("--framework", default="agno", choices=["agno", "agentica"])
    run_p.add_argument("--model", default="claude-sonnet-4-20250514")
    run_p.add_argument("--provider", default="anthropic")
    run_p.add_argument("--skills-dir", type=Path, default=None)
    run_p.add_argument("--personality", default="")

    # ── skills ──
    skills_p = sub.add_parser("skills", help="List discovered skills")
    skills_p.add_argument("--dir", type=Path, default=Path("./skills"))

    # ── dev ──
    dev_p = sub.add_parser("dev", help="Start the optional Agno deployment helper server")
    dev_p.add_argument("--host", default="127.0.0.1")
    dev_p.add_argument("--port", type=int, default=8000)

    # ── serve ──
    serve_p = sub.add_parser("serve", help="Build and serve a native Agno agent")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--host", default="0.0.0.0")

    # ── init ──
    scaffold_p = sub.add_parser(
        "scaffold",
        help="Create an OpenClaw workspace scaffold (recommended)",
    )
    scaffold_p.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Workspace directory to create",
    )
    scaffold_p.add_argument("--agent-name", default="Assistant")
    scaffold_p.add_argument(
        "--multi-agent",
        action="store_true",
        help="Also create a sample multi-agent config (agents.yaml)",
    )
    scaffold_p.add_argument(
        "--force",
        action="store_true",
        help="Allow scaffolding into a non-empty directory",
    )

    # ── init ──
    init_p = sub.add_parser(
        "init",
        help="Initialize an optional Agno deployment helper project",
    )
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
        case "scaffold":
            _cmd_scaffold(args)
        case "init":
            _cmd_init(args)
        case _:
            parser.print_help()


def _cmd_dev(args: argparse.Namespace) -> None:
    from clawbridge.app import ClawApp
    from rich.console import Console
    console = Console()
    
    app = ClawApp()
    console.print(f"🦞 Starting optional Agno helper on http://{args.host}:{args.port}")
    try:
        app.serve(host=args.host, port=args.port, reload=True)
    except Exception as e:
        console.print(f"[bold red]Failed to start server:[/bold red] {e}")


def _cmd_scaffold(args: argparse.Namespace) -> None:
    from clawbridge.scaffold import create_openclaw_workspace

    try:
        workspace_dir = create_openclaw_workspace(
            args.path,
            agent_name=args.agent_name,
            include_multi_agent=args.multi_agent,
            force=args.force,
        )
    except FileExistsError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        return

    console.print(
        f"[bold green]OpenClaw workspace scaffolded at:[/bold green] {workspace_dir}"
    )
    console.print(
        "\nNext steps:\n"
        f"  cd {workspace_dir}\n"
        "  clawbridge run --framework agno --name Assistant\n"
        "  # or: clawbridge run --framework agentica --name Assistant\n"
    )


def _cmd_run(args: argparse.Namespace) -> None:
    from clawbridge.builders import build_agno_agent, build_agentica_agent, load_agent_config
    from clawbridge.core.agent import ClawAgent
    from clawbridge.core.types import ModelConfig

    skill_paths = [args.skills_dir] if args.skills_dir else []

    agent = ClawAgent(
        name=args.name,
        model=ModelConfig(provider=args.provider, model_id=args.model),  # type: ignore[arg-type]
        skill_paths=skill_paths,
        personality=args.personality,
    )
    prepared_agent = load_agent_config(agent)
    if args.framework == "agno":
        native_agent = build_agno_agent(agent)
    else:
        native_agent = build_agentica_agent(agent)

    console.print(Panel(
        f"🦞 [bold]{agent.name}[/bold] ready "
        f"([cyan]{args.framework}[/cyan] framework)\n"
        f"Model: {args.provider}/{args.model}\n"
        f"Skills: {len(prepared_agent.skills)} loaded\n"
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

        if args.framework == "agno":
            response = asyncio.run(native_agent.arun(user_input))
            content = getattr(response, "content", response)
        else:
            try:
                from agentica import spawn  # type: ignore[import-untyped]
            except ImportError as exc:
                raise ImportError(
                    "Agentica runtime support requires the agentica package. "
                    "Install clawbridge[agentica]."
                ) from exc

            spawned = asyncio.run(
                spawn(
                    native_agent.system_prompt,
                    native_agent.scope,
                    model=native_agent.model,
                )
            )
            content = asyncio.run(spawned(user_input)) if callable(spawned) else str(spawned)

        console.print(f"[bold blue]{agent.name}:[/bold blue] {content}\n")


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
    from clawbridge.backends.agno import AgnoBackend
    from clawbridge.core.agent import ClawAgent

    backend = AgnoBackend(ClawAgent())
    console.print(f"🦞 Serving native Agno agent on http://{args.host}:{args.port}")
    asyncio.run(backend.serve(host=args.host, port=args.port))


def _cmd_init(args: argparse.Namespace) -> None:
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
    config_yaml = """name: My ClawBridge Agno Deployment
description: An optional Agno deployment helper using OpenClaw-style skills and prompts.
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

    console.print(
        f"🦞 [bold green]Initialized optional Agno deployment helper '{args.name}'[/bold green]"
    )
    console.print(f"\nNext steps:\n  cd {args.name}\n  clawbridge dev\n")


if __name__ == "__main__":
    main()
