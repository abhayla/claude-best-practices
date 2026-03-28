---
name: ssot-workflow-audit
description: >
  Audit core/.claude/ patterns for workflow group coverage, stale seeds,
  and registry sync. Use when patterns are added to core/ or when
  reviewing workflow documentation completeness.
type: workflow
allowed-tools: "Read Grep Glob Bash"
argument-hint: "[--fix] [--strict]"
version: "1.0.0"
---

# SSOT Workflow Audit

Audit the hub's `core/.claude/` directory to ensure every distributable pattern is assigned to a workflow group, has a registry entry, and has up-to-date workflow documentation.

**Default mode is read-only.** Pass `--fix` to auto-assign orphans via `assign_workflow_groups.py`. Pass `--strict` to treat warnings as failures.

**Arguments:** $ARGUMENTS

---

## STEP 1: Inventory Core Patterns

Collect all patterns from `core/.claude/` and build a complete inventory.

### 1a. Collect Skills

- Glob for all `core/.claude/skills/*/SKILL.md` files
- For each, read frontmatter to extract: name, version, type, description
- Record: skill name, line count, has references/ subdirectory

### 1b. Collect Agents

- Glob for all `core/.claude/agents/*.md` files
- For each, read frontmatter to extract: name, model, description
- Record: agent name (filename without .md)

### 1c. Collect Rules

- Glob for all `core/.claude/rules/*.md` files
- For each, read first 10 lines to extract scope declaration
- Record: rule name (filename without .md), scope type

### 1d. Summary

Print inventory summary:

```
Core Inventory:
  Skills: X
  Agents: Y
  Rules: Z
  Total: N patterns
```

---

## STEP 2: Check Workflow Group Coverage

Load `config/workflow-groups.yml` and verify every core pattern is assigned.

### 2a. Load Workflow Groups

- Read `config/workflow-groups.yml`
- Extract all seeds across all groups (skills, agents, rules)
- Build a set of all assigned pattern names

### 2b. Identify Orphans

For each pattern found in Step 1, check if it appears in any workflow group's seeds.

| Pattern Status | Verdict | Severity |
|---|---|---|
| In at least one group | OK | — |
| In `_needs-manual-review` group | LOW_CONFIDENCE | WARN |
| Not in any group | ORPHAN | FAIL |

### 2c. Identify Stale Seeds

For each seed name in `workflow-groups.yml`, verify the pattern file exists on disk:

| Seed Status | Verdict | Severity |
|---|---|---|
| File exists | OK | — |
| File missing | STALE_SEED | FAIL |

---

## STEP 3: Check Registry Sync

Verify every core pattern has a matching entry in `registry/patterns.json`.

### 3a. Load Registry

- Read `registry/patterns.json`
- Build a set of all registered pattern names

### 3b. Cross-Reference

For each core pattern from Step 1:

| Registry Status | Verdict | Severity |
|---|---|---|
| Has matching registry entry | OK | — |
| Missing from registry | MISSING_REGISTRY | FAIL |

For each registry entry:

| Pattern Status | Verdict | Severity |
|---|---|---|
| File exists in core/ | OK | — |
| File missing from core/ | STALE_REGISTRY | WARN |

---

## STEP 4: Check Workflow Doc Freshness

Verify `docs/workflows/` is in sync with `config/workflow-groups.yml`.

### 4a. Compare Groups to Docs

For each workflow group in `config/workflow-groups.yml`:

| Doc Status | Verdict | Severity |
|---|---|---|
| Matching doc exists in `docs/workflows/` | OK | — |
| No doc file for this group | STALE_DOC | WARN |

### 4b. Check Doc Content

For each existing workflow doc, verify it references the current seeds:
- Read the Skills table from the doc
- Compare against the workflow group's current seed list
- If seeds were added/removed since last generation, flag as stale

---

## STEP 5: Apply Fixes (if --fix)

If `--fix` argument is provided, run the auto-assignment script:

```bash
PYTHONPATH=. python scripts/assign_workflow_groups.py
```

Then re-run Steps 2-4 to report remaining issues.

If `--fix` is NOT provided, skip this step.

---

## STEP 6: Generate Report

Compile all findings into a structured report.

### Report Template

```
## SSOT Workflow Audit Report

### Summary
| Metric | Value |
|---|---|
| Core patterns | X total (Y skills, Z agents, W rules) |
| Workflow groups | N groups |
| Assigned patterns | A of X |
| Orphans | B patterns |
| Stale seeds | C entries |
| Missing registry | D patterns |
| Stale docs | E docs |

### Violations

| # | Type | Severity | Pattern | Details |
|---|------|----------|---------|---------|
| 1 | ORPHAN | FAIL | redis-patterns | Not in any workflow group |
| 2 | STALE_SEED | FAIL | deleted-skill | Seed in testing-pipeline but file missing |
| 3 | MISSING_REGISTRY | FAIL | new-skill | No entry in registry/patterns.json |
| 4 | LOW_CONFIDENCE | WARN | mystery-skill | In _needs-manual-review group |
| 5 | STALE_DOC | WARN | hub-sync | Doc doesn't reflect current seeds |

### Verdict

| Mode | Result |
|---|---|
| Default | PASS (0 FAIL) / FAIL (N violations) |
| --strict | PASS (0 FAIL, 0 WARN) / FAIL (N violations + W warnings) |
```

---

## CRITICAL RULES

- MUST audit `core/.claude/` patterns only — this skill does NOT audit the hub's `.claude/` directory
- MUST NOT modify any files in default mode — default is read-only
- MUST NOT create registry entries — only report missing ones for manual action
- MUST run `assign_workflow_groups.py` only when `--fix` is explicitly passed
- MUST distinguish FAIL (blocking) from WARN (advisory) — see severity column in each step
- MUST report stale seeds (pointing to deleted patterns) as FAIL — these silently break workflow docs
- MUST check both directions: patterns without groups AND groups with missing patterns
- MUST treat `_needs-manual-review` entries as WARN, not FAIL — they were auto-assigned with low confidence
- In `--strict` mode, MUST treat all WARNs as FAILs
