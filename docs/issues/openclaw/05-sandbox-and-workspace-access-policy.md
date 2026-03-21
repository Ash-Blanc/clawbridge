# Issue 05: Model OpenClaw Sandboxing and Workspace Access Policy

## Problem

OpenClaw has a real sandbox policy surface: mode, scope, workspace access, bind mounts, browser sandbox settings, and tool-policy interactions. `clawbridge` currently has no comparable model, so it cannot express one of OpenClaw's main customization axes.

## Scope

- Add core config types for sandbox mode, scope, and workspace access.
- Model the OpenClaw workspace access modes: `none`, `ro`, `rw`.
- Add builder-facing runtime metadata so prompt assembly and backends can reflect sandbox state.
- Keep the initial implementation declarative if full execution support is not ready yet.

## Acceptance Criteria

- The config layer can represent the documented OpenClaw sandbox modes and scopes.
- Prompt assembly can tell the model whether it is on host or in sandbox, and which workspace path it should treat as active.
- Agno and Agentica builders can consume the config even if runtime enforcement lands later.
- The model is explicit about unsupported combinations instead of silently ignoring them.

## Not In Scope

- Actual Docker orchestration.
- Browser container boot logic.
- Tool allow/deny enforcement.

## References

- https://docs.openclaw.ai/sandboxing
- https://docs.openclaw.ai/agent-workspace
