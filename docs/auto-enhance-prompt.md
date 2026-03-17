# Auto-Enhance Workflow

## Purpose
A global rule that automatically triggers on every user prompt — no slash
command needed. It enriches the user's raw prompt with project-specific
context, fills knowledge gaps via web search when needed, and proposes
Claude Code resource changes (skills, agents, rules, hooks) with batch
user approval before any CRUD.

## Mechanism
- **Primary:** Global rule (`.claude/rules/prompt-auto-enhance.md`, `# Scope: global`)
  — loaded into every conversation automatically
- **Supporting:** Reference skill (`/prompt-auto-enhance`) — holds detailed procedures
  the rule points to for complex operations (resource CRUD, web search decisions)
- **Delegates to:** `/writing-skills` (skill creation), `/claude-guardian` (rule
  creation), `skill-author` agent (routing + agent creation), manual hook
  workflow (hook creation/update)

## Behavior Modes
- **Silent mode** (default): Enhances understanding internally, acts on enriched
  context without showing the user what was gathered. User just sees better results.
- **Visible mode** (resource CRUD): When the workflow detects a need to create,
  update, or delete any Claude Code resource, it surfaces the enhancement summary
  — interpreted intent, gathered context, proposed changes — before asking for
  batch approval.

---

## Context Gathering

The workflow gathers project context in two tiers before enhancing any prompt.

### Tier 1 — Always (every prompt)
Cheap, fast reads that ground every response in current project state:

1. **Existing `.claude/` patterns** — scan rules, skills, agents, hooks to
   understand what's already defined and avoid duplicating or contradicting them
2. **CLAUDE.md** — project architecture, commands, conventions, key directories
3. **Git state** — current branch, recent commits, uncommitted changes to
   understand what the user is actively working on

### Tier 2 — Conditional (only when relevant)
Triggered when the prompt involves code changes or pattern work:

4. **File structure near the prompt's subject** — if the user mentions a
   feature, module, or file, read surrounding files for structural context
   (imports, dependencies, tests, related modules)
5. **`registry/patterns.json`** — check whether relevant patterns already exist
   before suggesting new ones, verify registry-to-file sync status

### Tier Selection Logic
- Tier 1 runs on every prompt unconditionally
- Tier 2 triggers when the prompt references specific files, features, code
  changes, or pattern/resource work
- The workflow MUST NOT read more than necessary — if Tier 1 provides
  sufficient context, skip Tier 2

---

## Web Search Strategy

Local context first, web search as fallback — with one exception for resource
creation targeting external technologies.

### TRIGGER web search when:
1. **External library/API/tool not in codebase** — the prompt references a
   technology with no existing code, config, or dependency entry locally
   (e.g., "add Stripe webhooks" but no Stripe code exists)
2. **Version, compatibility, or deprecation questions** — local code cannot
   answer "what's the latest version of X" or "is Y deprecated"
3. **Authoritative convention needed** — the prompt asks to follow an
   official framework convention that Claude should not guess at
   (e.g., "follow the official Next.js app router pattern")
4. **Resource creation for unfamiliar stack** — creating a new skill, rule,
   or agent targeting a technology where loaded context is insufficient to
   produce accurate, current guidance

### DO NOT web search when:
1. The prompt is about existing code — read the code instead
2. The prompt is about project conventions — read CLAUDE.md and existing
   patterns instead
3. The information is already in a loaded rule, skill, or agent
4. General programming knowledge within Claude's training data suffices

### Exception: Resource CRUD for External Tech
When creating or updating a resource that targets a specific external
technology (library, framework, API), ALWAYS verify against current
documentation via web search — even if Claude has general knowledge.
Libraries evolve faster than training data.

---

## Resource CRUD Detection & Permission Flow

### Detection
After enhancing the prompt with gathered context, the workflow evaluates
whether the user's intent implies creating, updating, or deleting Claude
Code resources:

- **CREATE** — the prompt describes a repeatable workflow, convention, or
  review pattern not covered by existing patterns
- **UPDATE** — the prompt corrects, extends, or refines behavior that an
  existing skill, rule, agent, or hook already partially covers
- **DELETE** — the prompt explicitly or implicitly obsoletes an existing
  resource (e.g., "we no longer use X convention")

If no resource CRUD is detected, the workflow stays in silent mode and
proceeds with the enhanced prompt normally.

### Batch Approval Flow
When resource changes are detected, the workflow switches to visible mode:

1. **Show enhancement summary** — interpreted intent, context gathered,
   reasoning for why resources are needed
2. **Present proposed changes as a batch table:**
   ```
   Proposed resource changes:
     [1] CREATE rule:  auto-format-imports  — enforce import ordering convention
     [2] UPDATE skill: implement            — add new pre-check step
     [3] CREATE hook:  lint-on-save         — auto-lint after file edits

   Approve which? (all / none / 1,3 / ...)
   ```
3. **User selects** which items to approve — can approve all, none, or a
   specific subset by number
4. **Execute approved items only** — delegate to the appropriate tool:
   - Skills → `/writing-skills`
   - Rules → `/claude-guardian`
   - Agents → `skill-author` agent
   - Hooks → create shell script + update `settings.json`
5. **Skip rejected items** with no further prompting about them

### Constraints
- NEVER create, update, or delete any resource without batch approval
- NEVER re-prompt for rejected items in the same session
- NEVER proceed with partial information — if the workflow cannot determine
  the resource's purpose or content with confidence, include it in the
  batch table with a note asking the user to clarify
- Resource creation MUST follow existing quality standards:
  `pattern-structure.md`, `pattern-portability.md`, `pattern-self-containment.md`

---

## Implementation Guidance

### Files to Create
1. `.claude/rules/prompt-auto-enhance.md` — Global rule containing the behavioral
   directives (Tier 1 gathering, silent/visible mode logic, web search
   triggers, CRUD detection). This is the always-on engine.
2. `core/.claude/skills/prompt-auto-enhance/SKILL.md` — Reference skill containing
   the detailed procedures for resource CRUD batch flow, delegation routing,
   and web search decision tree. Invoked by the rule when needed, also
   available as explicit `/prompt-auto-enhance` command.

### Orchestration Compliance
Per `agent-orchestration.md`:
- The rule dispatches to existing skills/agents (max 2 nesting levels)
- No subagent-spawning-subagents — worker skills call `Skill()` but not `Agent()`
- Resource CRUD delegates to `skill-author` agent which routes to
  `/writing-skills` or `/claude-guardian` (this is the existing 2-level chain)

### Quality Compliance
Per `pattern-structure.md`:
- Rule: `# Scope: global`, description in frontmatter
- Skill: `type: reference`, `version: "1.0.0"`, `allowed-tools` minimal set,
  `argument-hint` for explicit invocation mode
