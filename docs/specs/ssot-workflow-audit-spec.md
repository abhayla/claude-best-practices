# Spec: SSOT Workflow Audit & Auto-Assignment

## Problem Statement

When new patterns are added to `core/.claude/`, they often aren't added to `config/workflow-groups.yml`, making them invisible in `docs/workflows/` documentation. Currently ~93 of 143 skills are orphans. There's no mechanism to automatically assign patterns to workflow groups or audit this coverage gap.

## Chosen Approach

**Approach B: New standalone script + hub-only audit skill**

Three deliverables:
1. `scripts/assign_workflow_groups.py` — auto-assigns orphan patterns to workflow groups
2. `.claude/skills/ssot-workflow-audit/SKILL.md` — hub-only audit skill (renamed from `ssot-audit`)
3. Minor changes to `generate_workflow_docs.py` and `update-docs.yml`

## Design

### 1. assign_workflow_groups.py

**Input:** `core/.claude/` patterns + `config/workflow-groups.yml`
**Output:** Updated `workflow-groups.yml` (only if changed)

**Algorithm:**
- Collect all patterns from `core/.claude/` (skills, agents, rules)
- Build reference graph (reuse helpers from `generate_workflow_docs.py`)
- For each orphan pattern, score against each workflow group:
  - `Score = (reference_graph_matches * 3) + (keyword_matches * 1)`
- Assignment thresholds:
  - Score >= 4: auto-assign (multiple groups if scores within 1 point)
  - Score 1-3: auto-assign with `# AUTO-ASSIGNED: low-confidence` comment
  - Score 0: assign to `_needs-manual-review` group
- Write seeds in sorted order within each group (merge-conflict friendly)
- Only write file if content actually changed (prevents CI loop)

**CLI:**
```bash
PYTHONPATH=. python scripts/assign_workflow_groups.py [--dry-run]
```

### 2. ssot-workflow-audit skill

**Location:** `.claude/skills/ssot-workflow-audit/SKILL.md` (hub-only, NO registry entry)
**Replaces:** `.claude/skills/ssot-audit/` (renamed)

**Checks:**

| Check | Type | Severity |
|---|---|---|
| Pattern in `core/` not in any workflow group | ORPHAN | FAIL |
| Pattern in `_needs-manual-review` group | LOW_CONFIDENCE | WARN |
| Seed pointing to deleted pattern | STALE_SEED | FAIL |
| Pattern missing from `registry/patterns.json` | MISSING_REGISTRY | FAIL |
| Workflow doc out of sync with groups | STALE_DOC | WARN |
| Low-confidence entries older than 2 weeks | UNREVIEWED | WARN |

**Modes:**
- Default: read-only report
- `--fix`: runs `assign_workflow_groups.py`, then reports remaining issues
- `--strict`: WARNs become FAILs

**allowed-tools:** `Read Grep Glob Bash`

### 3. generate_workflow_docs.py change

Add to top of `main()`:
```python
subprocess.run([sys.executable, "scripts/assign_workflow_groups.py"], check=True)
```

Ensures assignment always runs before doc generation, whether invoked locally or via CI.

### 4. update-docs.yml change

Add bot-commit filter to prevent CI loop:
```yaml
if: github.actor != 'github-actions[bot]'
```

No other changes needed — `generate_workflow_docs.py` already called, and it now calls the assignment script internally.

### 5. Cleanup

- Delete `.claude/skills/ssot-audit/` directory
- Create `.claude/skills/ssot-workflow-audit/` directory with new SKILL.md
- `core/.claude/skills/ssot-audit/` stays untouched (downstream projects keep it)

## Requirement Tiers

### Must Have
- `assign_workflow_groups.py` with scoring algorithm and threshold logic
- `ssot-workflow-audit` skill with all 6 checks
- `generate_workflow_docs.py` calls assignment script before generation
- CI loop prevention in `update-docs.yml`
- Sorted seed output for merge-conflict mitigation
- Rename `.claude/skills/ssot-audit/` to `.claude/skills/ssot-workflow-audit/`

### Nice to Have
- `--dry-run` flag on `assign_workflow_groups.py`
- `--strict` mode on the audit skill
- Timestamp tracking for `# AUTO-ASSIGNED` comments (for UNREVIEWED check)

### Out of Scope
- Modifying `core/.claude/skills/ssot-audit/` (stays as-is for downstream)
- Changes to `validate-pr.yml` (no PR blocking for now)
- Creating new workflow groups (use existing 9 + `_needs-manual-review`)

## Success Criteria

1. Running `assign_workflow_groups.py` reduces orphans from ~93 to <10 (the `_needs-manual-review` bucket)
2. Running `/ssot-workflow-audit` produces a clear report with zero false positives for FAIL-severity checks
3. Adding a new pattern to `core/` and pushing to `main` automatically assigns it and regenerates docs
4. No CI infinite loop when `workflow-groups.yml` is auto-modified

## Open Questions

- None — all gaps addressed in design.
