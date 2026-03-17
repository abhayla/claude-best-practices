---
name: prompt-auto-enhance
description: >
  Detailed procedures for auto-enhance resource CRUD: batch approval flow,
  delegation routing to existing authoring tools, and web search decision tree.
  Invoked by the prompt-auto-enhance rule when resource changes are detected,
  or explicitly via /prompt-auto-enhance for manual enhancement.
triggers:
  - prompt-auto-enhance
  - auto-enhance
  - enhance prompt
  - enrich prompt
allowed-tools: "Read Grep Glob WebFetch WebSearch Skill Agent"
argument-hint: "[prompt text to enhance manually]"
type: reference
version: "1.0.0"
---

# Prompt Auto-Enhance — Resource CRUD Procedures

This skill contains the detailed procedures referenced by the `prompt-auto-enhance`
global rule. The rule handles silent enhancement automatically. This skill handles
the **visible mode** workflow when resource CRUD is detected.

**Arguments:** $ARGUMENTS

---

## Batch Approval Flow

When the global rule detects that a user's prompt implies creating, updating, or
deleting Claude Code resources (skills, agents, rules, hooks), execute this flow:

### Step 1: Show Enhancement Summary

Present the user with what was understood and gathered:

```
Enhancement Summary:
  Intent: [interpreted user intent in one sentence]
  Context gathered:
    - [Tier 1/2 sources read, e.g., "CLAUDE.md", "git status", ".claude/rules/"]
    - [Web sources fetched, if any]
  Reasoning: [why resource changes are needed]
```

### Step 2: Present Batch Table

List ALL proposed resource changes in a single table:

```
Proposed resource changes:
  [1] CREATE rule:  <name>  — <one-line description>
  [2] UPDATE skill: <name>  — <what changes>
  [3] DELETE hook:  <name>  — <why obsolete>
  [4] CREATE agent: <name>  — <one-line description>

Approve which? (all / none / 1,3 / ...)
```

Rules for the batch table:
- Group related changes together (e.g., a skill + its supporting rule)
- For items where purpose or content cannot be determined with confidence,
  append `[NEEDS CLARIFICATION: <question>]` and let the user clarify
- Show the action verb (CREATE / UPDATE / DELETE) and resource type for each

### Step 3: Wait for User Selection

The user responds with one of:
- `all` — approve every item
- `none` — reject everything, proceed with the original prompt normally
- `1,3` — approve only items 1 and 3 (comma-separated numbers)
- Clarification text — if they answer a `[NEEDS CLARIFICATION]` question,
  update the batch table and re-present

### Step 4: Execute Approved Items

For each approved item, delegate to the appropriate authoring tool:

| Resource Type | Delegate To | How |
|---------------|-------------|-----|
| **Skill** | `/writing-skills` | `Skill(skill="writing-skills")` with the skill name and description |
| **Rule** | `/claude-guardian` | `Skill(skill="claude-guardian")` with the rule text |
| **Agent** | `skill-author` agent | `Agent(prompt="Create agent: <description>", subagent_type="skill-author")` |
| **Hook** | Manual workflow | Create shell script in `.claude/hooks/`, update `settings.json` |

Execute items sequentially — each resource may depend on the previous one
(e.g., a skill might reference a rule created in the same batch).

### Step 5: Skip Rejected Items

Items the user did not approve are dropped silently. MUST NOT re-prompt for
rejected items later in the same session.

---

## Web Search Decision Tree

Use this decision tree when evaluating whether to search the web:

```
Is the prompt about existing code in this project?
  YES → Read the code. DO NOT web search.
  NO  ↓

Is the answer in CLAUDE.md or existing .claude/ patterns?
  YES → Reference those. DO NOT web search.
  NO  ↓

Is this general programming knowledge Claude already has?
  YES → Use training knowledge. DO NOT web search.
  NO  ↓

Does the prompt reference an external library/API/tool?
  YES → Is there existing code/config for it locally?
    YES → Read local code first. Web search only if insufficient.
    NO  → WEB SEARCH: fetch official docs for the technology.
  NO  ↓

Does the prompt ask about versions, compatibility, or deprecations?
  YES → WEB SEARCH: local code cannot answer these.
  NO  ↓

Does the prompt ask to follow an official framework convention?
  YES → WEB SEARCH: fetch authoritative source, do not guess.
  NO  → DO NOT web search. Proceed with available context.
```

### Resource CRUD Exception

When creating or updating a resource that targets a specific external technology:
ALWAYS web search for current documentation regardless of other conditions.
Training data may be outdated for fast-evolving libraries.

---

## Context Gathering Reference

### Tier 1 — Always (every prompt)

| Source | What to Read | Why |
|--------|-------------|-----|
| `.claude/` patterns | `Glob("core/.claude/{rules,skills,agents,hooks}/**")` and `Glob(".claude/{rules,skills,agents,hooks}/**")` | Know what exists to avoid duplication |
| CLAUDE.md | Already loaded by system | Architecture, commands, conventions |
| Git state | `git status`, `git log --oneline -5` | Current branch, recent work, uncommitted changes |

### Tier 2 — Conditional

| Source | When to Read | What to Read |
|--------|-------------|-------------|
| Nearby files | Prompt mentions a specific file/feature/module | Imports, dependencies, tests, related modules |
| `registry/patterns.json` | Prompt involves pattern creation or comparison | Check if pattern already exists, verify sync |

---

## CRUD Detection Signals

### CREATE signals
- User describes a repeated workflow they do manually
- User states a convention that should always be followed
- User asks "can we enforce X" or "how do I make Claude always do Y"
- User describes a review persona or specialized analysis task

### UPDATE signals
- User corrects Claude's behavior that an existing rule/skill should have caught
- User says "also do X when running /skill-name"
- User extends a convention beyond what the current rule covers
- Existing pattern is outdated or incomplete for the user's needs

### DELETE signals
- User says "we no longer use X" or "remove the X rule"
- User's codebase has migrated away from a technology a pattern targets
- A pattern contradicts a newer pattern the user approved

### NO CRUD signals
- User asks a question (just answer it)
- User asks to implement a feature (just implement it)
- User asks to fix a bug (just fix it)
- User asks to run tests (just run them)

When in doubt, default to NO CRUD — do not suggest resource changes unless
the signals are clear.

---

## MUST DO

- ALWAYS gather Tier 1 context before responding to any prompt
- ALWAYS present the batch table when resource CRUD is detected
- ALWAYS wait for explicit user approval before creating/updating/deleting
- ALWAYS delegate to existing authoring tools — never generate patterns ad-hoc
- ALWAYS follow quality standards from `pattern-structure.md`,
  `pattern-portability.md`, `pattern-self-containment.md`
- ALWAYS stay silent (no enhancement summary) when no CRUD is detected

## MUST NOT DO

- MUST NOT create, update, or delete resources without batch approval
- MUST NOT re-prompt for rejected items in the same session
- MUST NOT web search when local context is sufficient
- MUST NOT show enhancement details for non-CRUD prompts
- MUST NOT generate patterns directly — use `/writing-skills`, `/claude-guardian`,
  or `skill-author` agent
- MUST NOT suggest resource changes when signals are ambiguous — default to
  no CRUD and proceed normally
