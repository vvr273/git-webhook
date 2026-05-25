---
name: project-context-updater
description: Update docs/context/project_context.md after feature additions, feature changes, new documentation, new commands, dashboard changes, or scope clarifications in this repository. Use when the user asks to preserve project progress or maintain context for future chats.
---

# Project Context Updater

Update [docs/context/project_context.md](../../docs/context/project_context.md) whenever meaningful project state changes.

## Use This Skill When

- a feature was added
- a feature was modified
- a dashboard capability changed
- a new document was added
- commands changed
- scope or architecture meaning changed
- the user asks to preserve progress for future chats

## Update Rules

Keep the file concise and high signal.

Always update these parts if relevant:
- `What Has Been Built`
- `What Has Been Proven`
- `Main Documentation Available`
- `Commands Commonly Used`
- `Expected Future Work`

Add or adjust:
- important files created
- new capabilities
- major caveats discovered
- changes in operating model

Do not turn it into a changelog.
Summarize current truth, not every historical step.

## Workflow

1. Read [docs/context/project_context.md](../../docs/context/project_context.md).
2. Inspect the files changed in the current task.
3. Update the context file to reflect the new current state.
4. Keep wording repository-specific and concrete.
5. Prefer short bullets and stable facts.

## Scope

This skill is only for maintaining the durable context summary in:
- [docs/context/project_context.md](../../docs/context/project_context.md)

If broader user-facing docs also need updates, do that separately.
