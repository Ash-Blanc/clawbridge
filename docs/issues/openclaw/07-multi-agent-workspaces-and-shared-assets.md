# Issue 07: Support Multi-Agent Workspaces and Shared-vs-Per-Agent Assets

## Problem

OpenClaw can run one agent or many. Each agent has its own workspace, state dir, sessions, and auth profiles, while some skill locations remain shared. `clawbridge` currently centers one agent spec at a time and does not model agent-level workspace boundaries or shared assets clearly.

## Scope

- Add a multi-agent config shape that can describe agent id, workspace, and agent state dir separately.
- Distinguish per-agent assets from shared assets such as managed/local skills.
- Keep the single-agent path simple while allowing multi-agent builders to be added on top.
- Prepare the core types for per-agent overrides of sandbox, tools, and workspace settings.

## Acceptance Criteria

- Multiple agent definitions can coexist without sharing the same workspace by accident.
- Shared skill sources remain explicit and lower precedence than per-agent workspace skills.
- The config shape can represent OpenClaw's single-agent default and multi-agent override model.
- Builders can resolve the effective workspace and skill set for one selected agent id.

## Not In Scope

- Full routing layer for inbound messages.
- Agent-to-agent delegation.

## References

- https://docs.openclaw.ai/multi-agent
- https://docs.openclaw.ai/skills
