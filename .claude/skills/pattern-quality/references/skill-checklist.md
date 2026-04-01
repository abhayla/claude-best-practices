# Skill Quality Checklist

## Frontmatter Contract

| Field | Required | Validation |
|-------|----------|------------|
| `name` | MUST | Kebab-case, matches directory name, max 64 chars |
| `description` | MUST | 1-3 sentences, starts with a verb, max 1024 chars. MUST describe WHEN to trigger, not just WHAT it does |
| `type` | MUST | `workflow` or `reference` — no other values |
| `allowed-tools` | MUST | Space-separated, minimal set. Read-only skills MUST NOT include Write/Edit/Bash |
| `argument-hint` | MUST | Show required and optional args: `"<required> [optional]"` |
| `version` | MUST | SemVer format `X.Y.Z` |

## Structure by Type

| Type | Required Structure |
|------|-------------------|
| `workflow` | Numbered `## STEP N:` sections with verb-phrase titles |
| `reference` | Organized `##` sections — no step numbering required |

## Content Quality

- MUST have a `## CRITICAL RULES` or `## MUST DO / MUST NOT DO` section
- Critical constraints MUST appear at TOP (preamble/description) AND BOTTOM (critical rules section)
- MUST NOT contain placeholder markers (`<!-- TODO: -->`, `<!-- FIXME: -->`)
- Content lines (excluding frontmatter and headings) MUST be >= 30 (no stubs)
- Total lines MUST be <= 500 (split overflow into `references/` subdirectory)

## Description Quality (Trigger Effectiveness)

- MUST start with an action verb (Run, Generate, Analyze, Validate, Create)
- MUST include at least one "when" or "use when" clause
- MUST NOT use vague words: helper, utility, tool, handler, manager, misc
- MUST NOT duplicate another skill's trigger scope

## Allowed-Tools Least-Privilege Audit

| Skill Type | Expected Tools | Red Flag |
|------------|---------------|----------|
| Analysis / read-only | `Read Grep Glob` | Write, Edit, or Bash listed |
| Workflow with modifications | `Bash Read Write Edit Grep Glob` | Agent listed without `Agent()` calls |
| Delegates to other skills | Add `Skill` | Skill listed but no `Skill()` calls in body |
| Spawns subagents | Add `Agent` | Agent listed but no `Agent()` calls in body |

## SemVer Policy

| Change Type | Version Bump |
|---|---|
| Breaking changes to output format, removed steps | MAJOR |
| New optional steps, added examples | MINOR |
| Typo fixes, wording clarifications | PATCH |
