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

    # ── serve ──
    serve_p = sub.add_parser("serve", help="Serve agent as HTTP API")
    serve_p.add_argument("--backend", default="agno")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--host", default="0.0.0.0")

    args = parser.parse_args()

    match args.command:
        case "run":
            _cmd_run(args)
        case "skills":
            _cmd_skills(args)
        case "serve":
            _cmd_serve(args)
        case _:
            parser.print_help()


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


if __name__ == "__main__":
    main()