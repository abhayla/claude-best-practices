---
description: Rules for managing context window, token usage, and documentation references.
---

# Context Management Rules

1. **Progressive Disclosure**: Don't inline large documentation blocks. Use pointers like "When modifying [feature], read: `docs/ARCHITECTURE.md`" instead.
2. **Minimize Context Imports**: Never use `@file` imports for entire documentation files — reference the path and explain when/why to read it. Each import consumes tokens on every session.
3. **Scratchpad for Complex Tasks**: For multi-step tasks, maintain a `scratchpad.md` as an APPEND-ONLY log with: gotchas, judgment calls, files discovered, questions, and answers. When the session ends, scratchpad contents feed into `/handover` for a structured summary.
4. **Reference Canonical Examples**: Instead of explaining patterns in prose, point to real files: "See `src/services/UserService.ts` for the service pattern." Code examples are always up-to-date and Claude can pattern-match from them directly.
5. **Delegate Bulk Reading**: When a task requires reading more than 5 files for research or exploration, delegate to a subagent. Subagents operate in separate context windows — their file reads don't consume the main conversation's token budget. After receiving subagent summaries, read the full content of key files identified as critical before making implementation decisions.
6. **Compaction Survival**: When context is compacted, always preserve: the full list of modified files, current task objective, and any test/build commands needed. Write critical working state to the scratchpad file (rule #3) so it survives compaction on disk rather than relying solely on in-context memory. For cross-session continuity (not just compaction), use `/handover` to generate a structured handover document instead.
7. **Context Rot Prevention**: Long sessions degrade output quality. For tasks requiring more than 5 sub-tasks, break work into atomic plans of 2-3 tasks each. Execute each atomic plan in a fresh subagent context rather than continuing in the main (degrading) context. Pass only the scratchpad + relevant file paths between atomic plans — not the full conversation history.
