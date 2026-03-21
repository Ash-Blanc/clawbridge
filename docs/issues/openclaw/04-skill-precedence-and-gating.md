# Issue 04: Add OpenClaw Skill Precedence, Shared Skill Locations, and Gating

## Problem

OpenClaw does not just load skills from one local folder. It has bundled skills, managed local skills, workspace skills, extra skill dirs, and precedence rules. It also filters skills based on environment and binary presence. `clawbridge` currently loads from explicit paths and does not model the real precedence stack.

That makes its skill story materially weaker than OpenClaw's actual behavior.

## Scope

- Add skill source locations for bundled, managed/local, workspace, and extra directories.
- Implement precedence rules where workspace wins over managed/local, which wins over bundled.
- Add lightweight gating hooks for env vars, binaries, and config requirements.
- Surface enough metadata so builders can explain why a skill was or was not loaded.

## Acceptance Criteria

- Skill conflict resolution is deterministic and tested.
- Workspace skill overrides beat shared/local and bundled skills by name.
- Extra skill dirs are supported at lowest precedence.
- Gated skills can be excluded with a clear reason.

## Not In Scope

- ClawHub publishing and sync.
- Prompt composition details.
- Sandboxed skill mirroring.

## References

- https://docs.openclaw.ai/skills
- https://docs.openclaw.ai/tools/clawhub
