---
description: >
  Auto-enhance every user prompt with project-specific context before acting.
  Gathers tiered context (patterns, CLAUDE.md, git state, nearby files, registry),
  triggers web search when local context is insufficient, and detects when Claude Code
  resources (skills, agents, rules, hooks) need to be created, updated, or deleted —
  presenting batch approval before any CRUD.
globs: ["**/*"]
---
# Scope: global

# Prompt Auto-Enhance

On every user prompt, BEFORE responding or taking action, silently enrich your
understanding with project-specific context. This rule fires automatically — the
user never needs to invoke a command.

---

## Behavior Modes

- **Silent mode** (default): Gather context internally, produce better results.
  MUST include a brief italic indicator at the top of the response showing what
  context was gathered. Keep it under 15 words. Format:
  `*Enhanced: <what was checked>*`
  Examples:
  - *Enhanced: git state, 3 rules, scanned skills/*
  - *Enhanced: git state, registry check, read 2 source files*
  - *Enhanced: git state, CLAUDE.md, Tier 2 skipped*
- **Visible mode** (resource CRUD only): When you detect a need to CREATE, UPDATE,
  or DELETE a Claude Code resource (skill, agent, rule, hook), switch to visible
  mode — show the enhancement summary, interpreted intent, and proposed changes
  before asking for batch approval.

---

## Tier 1 Context — Always (every prompt)

Perform these cheap reads on every prompt to ground your response in current
project state:

1. **Existing `.claude/` patterns** — Scan rules, skills, agents, hooks to know
   what is already defined. MUST NOT duplicate or contradict existing patterns.
2. **CLAUDE.md** — Project architecture, commands, conventions, key directories.
   Already loaded by the system — reference it, do not re-read unless modified.
3. **Git state** — Current branch, recent commits, uncommitted changes. Understand
   what the user is actively working on right now.

## Tier 2 Context — Conditional

Trigger ONLY when the prompt references specific files, features, code changes,
or pattern/resource work:

4. **File structure near the prompt's subject** — If the user mentions a feature,
   module, or file, read surrounding files for structural context (imports,
   dependencies, tests, related modules).
5. **`registry/patterns.json`** — Check whether relevant patterns already exist
   before suggesting new ones. Verify registry-to-file sync status.

**Selection logic:** If Tier 1 provides sufficient context, skip Tier 2. MUST NOT
read more than necessary.

---

## Web Search Strategy

Attempt local context first. Web search is a fallback, not a default.

### TRIGGER web search when:
1. The prompt references an external library/API/tool with no existing code,
   config, or dependency entry locally
2. The prompt asks about current versions, compatibility, or deprecations that
   local code cannot answer
3. The prompt asks to follow an official framework convention that MUST NOT be
   guessed (e.g., "follow the official Next.js app router pattern")
4. Creating a resource for a stack where loaded context is insufficient for
   accurate, current guidance

### DO NOT web search when:
1. The prompt is about existing code — read the code instead
2. The prompt is about project conventions — read CLAUDE.md and existing patterns
3. The information is already in a loaded rule, skill, or agent
4. General programming knowledge within training data suffices

### Exception: Resource CRUD for External Tech
When creating or updating a resource targeting a specific external technology
(library, framework, API), ALWAYS verify against current documentation via web
search — even if you have general knowledge. Libraries evolve faster than
training data.

---

## Resource CRUD Detection

After enriching context, evaluate whether the user's intent implies creating,
updating, or deleting Claude Code resources:

- **CREATE** — The prompt describes a repeatable workflow, convention, or review
  pattern not covered by existing patterns
- **UPDATE** — The prompt corrects, extends, or refines behavior that an existing
  skill, rule, agent, or hook already partially covers
- **DELETE** — The prompt explicitly or implicitly obsoletes an existing resource

If NO resource CRUD is detected, stay in silent mode and proceed normally.

If resource CRUD IS detected, switch to visible mode and follow the batch
approval flow in `/prompt-auto-enhance`.

---

## CRITICAL RULES

- NEVER create, update, or delete any Claude Code resource without user approval
- NEVER re-prompt for items the user rejected in the same session
- NEVER show the full enhancement summary for non-CRUD prompts — only the brief indicator line
- NEVER skip Tier 1 context gathering
- NEVER web search when local context suffices
- Resource creation MUST follow `pattern-structure.md`, `pattern-portability.md`,
  and `pattern-self-containment.md`
- Delegate resource CRUD to existing tools: `/writing-skills` (skills),
  `/claude-guardian` (rules), `skill-author` agent (agents), manual workflow (hooks)
