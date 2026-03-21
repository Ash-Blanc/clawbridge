# Issue 06: Add OpenClaw Channel Semantics for Group Policy, Mention Gating, and Heartbeats

## Problem

OpenClaw's channel behavior is not just transport adapters. It includes DM scoping, group allowlists, mention gating, secure DM behavior, and heartbeat polls that drive proactive work. `clawbridge` currently exposes only low-level channel objects on the Agno path.

That is not enough to build OpenClaw-style agents that behave correctly on messaging surfaces.

## Scope

- Introduce channel/session policy types for direct chats, groups, and mention-triggered behavior.
- Add heartbeat configuration and runtime handling primitives.
- Keep the first implementation framework-neutral at the policy layer, then let builders map into backend-specific interfaces.
- Ensure session scope and memory rules can consume the same channel context.

## Acceptance Criteria

- The runtime model can represent group allowlists, mention requirements, and heartbeat prompts.
- Heartbeat polls are distinguishable from ordinary user messages.
- DM vs group context can influence session and memory loading.
- The Agno integration can consume the policy model even if transport-specific execution remains partial.

## Not In Scope

- Full Slack/WhatsApp production support.
- UI for configuring channel policies.

## References

- https://docs.openclaw.ai/channels/groups
- https://docs.openclaw.ai/sessions
- https://docs.openclaw.ai/reference/templates/AGENTS
