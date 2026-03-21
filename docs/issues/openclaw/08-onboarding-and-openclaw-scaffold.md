# Issue 08: Add an OpenClaw Workspace Scaffold and Onboarding Flow

## Problem

OpenClaw has a clear bootstrap and onboarding path: create a workspace, lay down starter files, optionally run a first-run ritual, and configure skills/channels/models. `clawbridge` currently has framework-centric scaffolding, but not an OpenClaw-style workspace scaffold.

That makes it harder to start from the thing OpenClaw users actually recognize.

## Scope

- Add a scaffold command or helper that generates an OpenClaw-style workspace skeleton.
- Include the standard workspace files with safe starter content.
- Make bootstrap behavior explicit, including the expectation that `BOOTSTRAP.md` disappears after first-run setup.
- Keep Agno/Agentica-specific project scaffolds secondary to the workspace scaffold.

## Acceptance Criteria

- A user can generate a workspace with the standard OpenClaw file set.
- The scaffold can target a chosen workspace directory.
- The generated layout is compatible with the workspace loader from Issue 01.
- Docs explain when to use the workspace scaffold versus backend-specific extras.

## Not In Scope

- Interactive wizard parity with OpenClaw.
- Channel credential setup.
- ClawHub installation flows.

## References

- https://docs.openclaw.ai/reference/templates/BOOTSTRAP
- https://docs.openclaw.ai/reference/templates/AGENTS
- https://docs.openclaw.ai/wizard
- https://docs.openclaw.ai/agent-workspace
