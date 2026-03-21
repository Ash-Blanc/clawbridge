# Issue 02: Replace the Current Prompt Builder with an OpenClaw-Style Prompt Composer

## Problem

`ClawAgent.build_system_prompt()` is a lightweight concatenation helper. OpenClaw builds a compact, OpenClaw-owned prompt with fixed sections for tooling, safety, skills, self-update, workspace, docs, injected workspace files, sandbox state, and current time.

The current builder is too simple to claim OpenClaw-style behavior.

## Scope

- Add a dedicated OpenClaw prompt builder that composes fixed sections in a stable order.
- Inject workspace file content from the workspace model rather than only from direct `ClawAgent` fields.
- Include runtime context such as workspace path, sandbox mode, and current local time.
- Make tool and skill rendering compact enough for prompt-budget awareness.

## Acceptance Criteria

- Prompt assembly order is explicit and tested.
- Workspace files are injected through the builder, not manually copied into freeform strings.
- The prompt builder can render different runtime contexts for host vs sandboxed runs.
- Existing backends can ask for the fully composed OpenClaw prompt without duplicating logic.

## Not In Scope

- Loading files from disk.
- Session memory rules.
- Channel-specific behavior.

## References

- https://docs.openclaw.ai/concepts/system-prompt
- https://docs.openclaw.ai/context/
- https://docs.openclaw.ai/reference/templates/AGENTS
