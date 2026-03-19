---
description: Meta-guidance for writing effective CLAUDE.md rules, choosing config file placement, and structuring project instructions.
globs: [".claude/**/*.md", "CLAUDE.md", "CLAUDE.local.md"]
---

# Rule Writing Meta-Guide

## How to Write Rules

1. **Be Directive**: Use RFC 2119 language for critical rules — "MUST", "NEVER", "MUST NOT". Avoid vague phrasing like "prefer", "try to", "consider".
2. **Always Provide Alternatives**: Never use negative-only constraints like "Never use X". Always provide an alternative: "Use Y instead of X".
3. **Structured Tracking**: For feature tracking / task lists, use JSON with structured fields (e.g., `"status": "pending"`) — LLMs prioritize structured data over prose markdown.
4. **Critical Rules First**: Place your most critical rules in the first 20 lines of any CLAUDE.md file. LLMs have a positional bias toward the beginning and end of prompts — instructions buried in the middle get deprioritized.

## Instruction Budget

All loaded CLAUDE.md files share one context window (~150 usable instruction slots). Budget per file:

| File | Max Lines | Scope |
|------|-----------|-------|
| `~/.claude/CLAUDE.md` | ≤30 | Personal preferences across all projects |
| `./CLAUDE.md` (project root) | ≤80 | Team conventions, architecture, commands |
| `./CLAUDE.local.md` | ≤20 | Personal project overrides (gitignored) |
| Folder-level `CLAUDE.md` | ≤15 | Directory-specific safety guards |

Move task-specific knowledge to `.claude/skills/` (loaded on-demand, zero cost when unused). Move path-scoped standards to `.claude/rules/` with `globs:` frontmatter (loaded only when path matches). Deletion test: "Would removing this line cause Claude to make mistakes?" If not, cut it.

## Where to Put Rules

4. **Use Hooks for Guarantees**: If a rule MUST be followed with zero exceptions (e.g., "run linter after every edit"), convert it to a hook instead of a CLAUDE.md instruction. Hooks are deterministic; CLAUDE.md instructions are advisory. In particular, NEVER use CLAUDE.md for code style (indentation, semicolons, import order) — delegate to linters and formatters via hooks instead. Prefer commit-time validation over write-time — mid-plan hook interruptions confuse agent reasoning.
5. **Skills for Workflows**: CLAUDE.md is for "nouns" (architecture, standards, locations). Use skills (`.claude/skills/`) for "verbs" (tasks, workflows, multi-step procedures).
6. **Nested Safety Guards**: Place local CLAUDE.md files in risky directories (e.g., `src/auth/`, `migrations/`) with specific warnings that auto-load when working there.
