# Issue 01: Add an OpenClaw Workspace File Model

## Problem

`clawbridge` currently models an agent as a Python config object plus skills and tools. OpenClaw is workspace-first. The runtime expects user-editable workspace files such as `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`, `MEMORY.md`, and daily memory files under `memory/YYYY-MM-DD.md`.

Without a first-class workspace model, `clawbridge` cannot accurately represent how OpenClaw agents are actually defined or customized.

## Scope

- Add a workspace loader that can read the standard OpenClaw file set from a directory.
- Define which files are required, optional, main-session-only, or one-time bootstrap files.
- Represent workspace state in core types without forcing one specific backend.
- Support loading from an explicit workspace path instead of only from `ClawAgent` fields.

## Acceptance Criteria

- A workspace directory can be loaded into a `clawbridge` object model.
- Missing optional files do not fail the load.
- Missing required files produce actionable errors.
- `BOOTSTRAP.md` is modeled as one-time startup state, not normal standing context.
- The loader distinguishes `MEMORY.md` from `memory/YYYY-MM-DD.md`.

## Not In Scope

- Prompt assembly details.
- Session scoping rules.
- Skill precedence and gating.

## References

- https://docs.openclaw.ai/reference/templates/AGENTS
- https://docs.openclaw.ai/reference/templates/BOOTSTRAP
- https://docs.openclaw.ai/agent-workspace
- https://docs.openclaw.ai/concepts/agent
