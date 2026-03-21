---
description: Enforces uniform quality standards across all workflow patterns (skills, agents, rules) — triggers on any pattern file write/edit.
globs:
  - "core/.claude/skills/*/SKILL.md"
  - "core/.claude/agents/*.md"
  - "core/.claude/rules/*.md"
  - ".claude/skills/*/SKILL.md"
  - ".claude/agents/*.md"
  - ".claude/rules/*.md"
---

# Workflow Quality Gate

Uniform quality standard for all patterns. Applies to every skill, agent, and
rule — existing and new. Autonomously triggered when pattern files are
written or edited. No dependency on other workflows.

## Core Principle: Every Pattern Must Be Independently Verifiable

A pattern MUST pass all quality checks on its own — without relying on another
skill, agent, or rule to compensate for missing structure, incomplete content,
or ambiguous scope.

## Skill Quality Checklist

Every skill in `skills/*/SKILL.md` MUST satisfy ALL of the following:

### Frontmatter Contract

| Field | Required | Validation |
|-------|----------|------------|
| `name` | MUST | Kebab-case, matches directory name, max 64 chars |
| `description` | MUST | 1-3 sentences, starts with a verb, max 1024 chars. MUST describe WHEN to trigger, not just WHAT it does. Bad: "A tool for testing." Good: "Run targeted regression tests when code changes affect critical paths." |
| `type` | MUST | `workflow` or `reference` — no other values |
| `allowed-tools` | MUST | Space-separated, minimal set. Read-only skills MUST NOT include Write/Edit/Bash |
| `argument-hint` | MUST | Show required and optional args: `"<required> [optional]"` |
| `version` | MUST | SemVer format `X.Y.Z` — bump per `pattern-structure.md` policy |

### Structure by Type

| Type | Required Structure |
|------|-------------------|
| `workflow` | Numbered `## STEP N:` sections with verb-phrase titles |
| `reference` | Organized `##` sections — no step numbering required |

### Content Quality

- MUST have a `## CRITICAL RULES` or `## MUST DO / MUST NOT DO` section
- Critical constraints MUST appear at TOP (preamble/description) AND BOTTOM
  (critical rules section) for primacy + recency reinforcement
- MUST NOT contain placeholder markers (`<!-- TODO: -->`, `<!-- FIXME: -->`)
- Content lines (excluding frontmatter and headings) MUST be >= 30 (no stubs)
- Total lines MUST be <= 500 (split overflow into `references/` subdirectory)
- Lines > 500 and <= 1000: WARNING — consider splitting
- Lines > 1000: MUST split

### Description Quality (Trigger Effectiveness)

The `description` field determines whether Claude discovers and triggers the
skill. Audit against these criteria:

- MUST start with an action verb (Run, Generate, Analyze, Validate, Create)
- MUST include at least one "when" or "use when" clause
- MUST NOT use vague words: helper, utility, tool, handler, manager, misc
- MUST NOT duplicate another skill's trigger scope — check for overlap

## Agent Quality Checklist

Every agent in `agents/*.md` MUST satisfy ALL of the following:

### Frontmatter Contract

| Field | Required | Validation |
|-------|----------|------------|
| `name` | MUST | Kebab-case, matches filename (without `.md`) |
| `description` | MUST | MUST explain WHEN to use, not just WHAT it does |
| `model` | MUST | One of: `inherit`, `sonnet`, `haiku`, `opus` |

### Body Structure

- MUST have `## Core Responsibilities` section
- MUST have `## Output Format` section
- Description MUST include a "use when" clause so the orchestrator knows
  when to dispatch this agent vs another

## Rule Quality Checklist

Every rule in `rules/*.md` MUST satisfy ALL of the following:

### Scope Declaration (exactly one)

| Scope Type | Declaration | When to Use |
|------------|-------------|-------------|
| Global | `# Scope: global` in first 5 lines | Applies to all files regardless of path |
| Path-scoped | `globs:` or `paths:` in YAML frontmatter | Applies only when working with matching files |

MUST NOT leave scope undefined — unscoped rules cause context pollution.

### Content Quality

- MUST use directive language (MUST, MUST NOT, NEVER) for critical rules —
  not "prefer", "try to", "consider"
- MUST provide alternatives for every prohibition — "Use Y instead of X",
  never just "Don't use X"
- Content lines MUST be >= 5 (no stub rules)

## Allowed-Tools Least-Privilege Audit

Every skill's `allowed-tools` MUST match its actual tool usage. Over-permissioned
skills are a quality defect, not just a security risk.

| Skill Type | Expected Tools | Red Flag |
|------------|---------------|----------|
| Analysis / read-only | `Read Grep Glob` | Write, Edit, or Bash listed |
| Workflow with file modifications | `Bash Read Write Edit Grep Glob` | Agent listed without `Agent()` calls in steps |
| Skill that delegates to other skills | Add `Skill` | Skill listed but no `Skill()` calls in body |
| Skill that spawns subagents | Add `Agent` | Agent listed but no `Agent()` calls in body |

### Verification Process

For each tool in `allowed-tools`:
1. Search the skill body for actual usage of that tool
2. If a tool is listed but never used in any step — flag as over-permissioned
3. If a tool is used in steps but not listed — flag as under-permissioned

## Placement Verification

Before writing any pattern file, confirm its destination:

| Question | YES | NO |
|----------|-----|-----|
| Would a downstream project need this? | `core/.claude/` + registry entry in `patterns.json` | `.claude/` (hub-only, NO registry entry) |
| Does it manage hub infrastructure (scanning, syncing, doc generation)? | `.claude/` (hub-only) | `core/.claude/` (distributable) |

### Registry Sync

When modifying patterns in `core/.claude/`:
- MUST have a matching entry in `registry/patterns.json`
- Version in frontmatter MUST match registry version
- Bump version in BOTH locations together

When modifying patterns in `.claude/`:
- MUST NOT have an entry in `registry/patterns.json`

## Validation Process

When this rule triggers (pattern file written or edited), verify in order:

### Step 1: Identify Pattern Type

| Path Pattern | Type |
|-------------|------|
| `skills/*/SKILL.md` | Skill — apply Skill Quality Checklist |
| `agents/*.md` | Agent — apply Agent Quality Checklist |
| `rules/*.md` | Rule — apply Rule Quality Checklist |

### Step 2: Run Checklist

Apply the appropriate checklist from above. For each item:
- **PASS** — requirement met
- **FAIL** — requirement violated, MUST fix before committing
- **WARN** — non-blocking but should be addressed (e.g., lines 500-1000)

### Step 3: Cross-Reference Integrity

If the pattern references other patterns via `Skill()`, `Agent()`, or
`/skill-name`:
- Verify every referenced skill directory exists on disk
- Verify every referenced agent file exists on disk
- If a reference target is missing — FAIL, do not silently skip

### Step 4: Run Validator

Before committing any pattern change:

```bash
PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py
```

Do not commit if the validator fails.

## Incremental Adoption

Existing patterns that predate this rule MAY have violations. When editing
an older pattern:
- Fix violations in the section you are modifying
- Do not rewrite the entire file just to fix pre-existing violations
- When a pattern is modified for any reason, bring the ENTIRE file up to
  this standard before committing

New patterns MUST pass all checks with zero violations from the start.

## Quality Score (Advisory)

Rate each pattern 0-100 based on checklist compliance:

| Score | Grade | Meaning |
|-------|-------|---------|
| 90-100 | A | Fully compliant, exemplary |
| 75-89 | B | Minor gaps (warnings, not failures) |
| 60-74 | C | Multiple warnings, needs attention |
| 40-59 | D | Has FAIL items, must not ship |
| 0-39 | F | Fundamentally non-compliant |

The score is advisory — the pass/fail checks above are authoritative.
New patterns MUST score >= 75 (Grade B or higher).
