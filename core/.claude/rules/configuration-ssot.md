# Scope: global

# Configuration Single Source of Truth (SSOT)

version: "1.0.0"

Every piece of Claude Code configuration MUST live in exactly one canonical layer. Duplication across layers causes contradictions, stale copies, and wasted context tokens.

## The Four Layers

| Layer | SSOT For | NOT For |
|-------|----------|---------|
| `CLAUDE.md` | Project-wide context loaded every session: build/test commands, architecture pointers, non-obvious gotchas | Multi-step workflows, path-scoped constraints, code style enforcement, tool permissions |
| `.claude/rules/*.md` | Domain constraints scoped to file paths via `globs:` frontmatter, or global behavioral standards | Workflows/procedures, project-wide context, tool permissions |
| `.claude/skills/*/SKILL.md` | Multi-step workflows and procedures, loaded on demand via slash commands | Constraints, project context, permissions |
| `.claude/settings.json` + hooks | Tool permissions, deterministic enforcement (linting, formatting, secret scanning) | Documentation, constraints Claude should "know", workflows |

### Choosing the Right Layer

- If it is context Claude needs **every session** (commands, architecture, gotchas) --> `CLAUDE.md`
- If it is a constraint scoped to **specific file types** --> `.claude/rules/` with `globs:`
- If it is a **multi-step procedure** invoked by name --> `.claude/skills/`
- If it must be enforced with **zero exceptions** (deterministic) --> hook in `.claude/settings.json`

## Anti-Duplication Rules

1. **No shadow copies.** MUST NOT duplicate the same constraint in both `CLAUDE.md` and a rules file. Place the constraint in the rules file and add a one-line pointer in `CLAUDE.md` (see Pointer Pattern below).

2. **No inline workflows.** MUST NOT embed multi-step procedures in `CLAUDE.md` or rules files. Extract them into a skill in `.claude/skills/` and reference the slash command instead.

3. **No style rules in CLAUDE.md.** MUST NOT use `CLAUDE.md` for code style enforcement (indentation, semicolons, import order, naming conventions). Configure linters and formatters via hooks in `.claude/settings.json` instead -- hooks are deterministic; CLAUDE.md instructions are advisory.

4. **No permission echoing.** MUST NOT duplicate tool permissions across `.claude/settings.json` and `CLAUDE.md`. Settings control what Claude CAN do; `CLAUDE.md` controls what Claude SHOULD know. These domains MUST NOT overlap.

5. **Path-scoped constraints go in rules.** When a constraint applies only to specific file types or directories, MUST use a `.claude/rules/*.md` file with `globs:` frontmatter. MUST NOT place path-specific constraints in `CLAUDE.md` where they consume tokens on every prompt regardless of relevance.

## The Pointer Pattern

When `CLAUDE.md` needs to reference domain-specific details owned by another layer, use a pointer -- not a copy:

```markdown
# API conventions: see `.claude/rules/api-patterns.md`
# Testing workflow: run `/auto-verify` (see `.claude/skills/auto-verify/`)
# Allowed tools: configured in `.claude/settings.json`
```

A pointer is a single line that names the authoritative source. It MUST NOT reproduce the content it points to. If the pointer exceeds 2 lines of explanation, the content belongs in the target file, not in `CLAUDE.md`.

## Settings vs Instructions

Anthropic's design principle: **Settings control what Claude CAN do. Instructions control what Claude SHOULD know.** Mixing these causes confusion and silent conflicts.

| Need | Correct Layer | Wrong Layer |
|------|--------------|-------------|
| Block a tool entirely | `settings.json` `deny` list | `CLAUDE.md` "never use X" |
| Run linter on every save | Hook in `settings.json` | `CLAUDE.md` "always run linter" |
| Explain why an API is designed a certain way | `CLAUDE.md` or rule | `settings.json` (no prose support) |
| Enforce test-before-commit | Hook (deterministic) | `CLAUDE.md` (advisory, skippable) |

**Rule of thumb:** If the enforcement must happen with zero exceptions, it is a hook. If Claude needs judgment to apply it, it is an instruction (CLAUDE.md or rule).

## How to Migrate a Bloated CLAUDE.md

When a `CLAUDE.md` file exceeds its budget (~80 lines for project root), extract content to the proper layers:

1. **Identify multi-step procedures** (numbered steps, if/then flows). Move each to `.claude/skills/<name>/SKILL.md`. Replace with a pointer: `# Deploy workflow: run /deploy`

2. **Identify path-scoped constraints** (rules that mention specific file extensions, directories, or frameworks). Move each to `.claude/rules/<name>.md` with appropriate `globs:`. Replace with a pointer.

3. **Identify deterministic enforcement** (style rules, formatting, "always run X"). Convert to hooks in `.claude/settings.json`. Remove from `CLAUDE.md` entirely -- hooks do not need pointers since they run automatically.

4. **Identify tool permission statements** ("never use tool X", "always allow Y"). Move to `.claude/settings.json` allow/deny lists. Remove from `CLAUDE.md`.

5. **What remains** should be project context: architecture overview, build/test commands, key gotchas, and pointers to the extracted content. This is the correct use of `CLAUDE.md`.

## CRITICAL RULES

- MUST NOT duplicate configuration across layers -- each fact lives in exactly one place
- MUST NOT use CLAUDE.md as a catch-all -- respect layer boundaries
- MUST use pointers (not copies) when CLAUDE.md references another layer's content
- MUST use hooks for deterministic enforcement; use instructions for advisory guidance
- MUST scope path-specific constraints to rules with `globs:`, not global CLAUDE.md
