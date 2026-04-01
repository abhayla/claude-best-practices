---
name: pattern-quality
description: >
  Validate pattern files (skills, agents, rules) against quality, portability,
  structure, and curation standards. Run when editing or creating files in
  core/.claude/ or .claude/ pattern directories. Consolidates all pattern
  quality checks into one on-demand workflow.
type: workflow
allowed-tools: "Read Grep Glob Bash"
argument-hint: "[path/to/pattern.md]"
version: "1.0.0"
---

# Pattern Quality Gate

Validate patterns against portability, structure, self-containment, curation,
and workflow integrity standards. Run this skill when creating or modifying
any file in `core/.claude/` or `.claude/` pattern directories.

**Request:** $ARGUMENTS

---

## STEP 1: Identify Pattern Type and Load Checklist

Determine the pattern type from the file path:

| Path Pattern | Type | Checklist |
|-------------|------|-----------|
| `skills/*/SKILL.md` | Skill | Read `references/skill-checklist.md` |
| `agents/*.md` | Agent | Read `references/agent-checklist.md` |
| `rules/*.md` | Rule | Read `references/rule-checklist.md` |

Read the appropriate checklist reference file for the detailed requirements.

## STEP 2: Validate Frontmatter and Structure

1. Parse YAML frontmatter — verify all required fields present
2. Check `name` matches directory/filename (kebab-case)
3. Check `version` is valid SemVer
4. For skills: verify numbered `## STEP N:` sections (workflow type) or organized `##` sections (reference type)
5. For agents: verify `model`, `color`, `## Core Responsibilities`, `## Output Format`
6. For rules: verify scope declaration (`globs:` or `# Scope: global`)

## STEP 3: Check Content Quality

1. Count content lines (excluding frontmatter, headings) — must be >= 30 for skills, >= 5 for rules
2. Check total lines <= 500 (WARN at 500, FAIL at 1000)
3. Scan for placeholder markers (`<!-- TODO: -->`, `<!-- FIXME: -->`)
4. Verify `## CRITICAL RULES` section exists (skills)
5. Check description starts with verb and includes "when" clause

## STEP 4: Validate Portability

Read `references/portability-rules.md` and check:

1. No hardcoded absolute paths (`C:\`, `/home/`, `/Users/`)
2. No project-specific references (specific class names, module paths)
3. Stack-prefixed patterns only assume their stack's standard tools
4. `allowed-tools` follows least-privilege per skill type

## STEP 5: Verify Cross-References and Registry

1. If pattern references other skills/agents via `Skill()`, `Agent()`, or `/skill-name` — verify targets exist on disk
2. If in `core/.claude/` — verify matching entry in `registry/patterns.json` with matching version
3. If in `.claude/` (hub-only) — verify NO entry in `registry/patterns.json`
4. Check `config/workflow-groups.yml` for stale seeds if renaming/deleting

## STEP 6: Validate Workflow Integrity

When the pattern change affects workflow connections:

1. Read `references/workflow-verification.md` for full verification checklist
2. Verify placement: distributable → `core/.claude/` + registry; hub-only → `.claude/` only
3. Check artifact convention compliance (`test-results/{skill-name}.json`)
4. Run the validator:

```bash
PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py
```

## STEP 7: Regenerate Documentation

After changes pass validation:

```bash
# Regenerate workflow docs (picks up new connections)
PYTHONPATH=. python scripts/generate_workflow_docs.py

# Regenerate dashboard (after core/.claude/ changes only)
python scripts/generate_docs.py
```

## STEP 8: Report

Output a structured quality report:

```
Pattern: <name>
Type: <skill|agent|rule>
Location: <core/.claude/ or .claude/>
Score: <0-100>
Grade: <A-F>

Checks:
  Frontmatter:    PASS/FAIL
  Structure:      PASS/FAIL
  Content:        PASS/FAIL
  Portability:    PASS/FAIL
  Cross-refs:     PASS/FAIL
  Registry sync:  PASS/FAIL

Issues: <list any failures>
```

## CRITICAL RULES

- MUST run this skill when creating or modifying ANY pattern file
- MUST NOT commit if the validator script fails
- MUST verify cross-references exist on disk — do not assume from memory
- MUST check registry sync for core/.claude/ patterns
- MUST regenerate docs after changes pass validation
- Patterns in core/.claude/ are for downstream projects only — never use them in this hub repo
- Every pattern must be independently verifiable without relying on other patterns
