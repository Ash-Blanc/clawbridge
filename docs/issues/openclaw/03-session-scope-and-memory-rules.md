# Issue 03: Implement OpenClaw Session Scope and Memory Loading Rules

## Problem

OpenClaw treats direct chats, group chats, and multi-user inboxes differently. It also loads `MEMORY.md` only in main sessions while always using recent daily memory files. `clawbridge` currently has a generic key/value memory helper and no session-scope model.

That loses an important OpenClaw behavior boundary: what memory is safe to load where.

## Scope

- Introduce session classification concepts such as main session, shared session, DM session, and group session.
- Add memory loading rules that depend on session type.
- Support daily memory paths and long-term curated memory separately.
- Expose these rules to builders so backend integrations can assemble the right context for a run.

## Acceptance Criteria

- Main sessions load `MEMORY.md` plus recent daily memory files.
- Shared or group contexts do not load `MEMORY.md`.
- Session scope is explicit in the runtime API, not inferred ad hoc.
- Prompt builder tests cover the scope-sensitive memory behavior.

## Not In Scope

- Sandboxing.
- Skill precedence.
- Channel transport logic.

## References

- https://docs.openclaw.ai/reference/templates/AGENTS
- https://docs.openclaw.ai/sessions
- https://docs.openclaw.ai/context/
