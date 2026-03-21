---
name: workflow-doc-reviewer
description: >
  Review workflow health, audit cross-references, and regenerate workflow
  documentation in docs/workflows/. Default mode is read-only (status + gaps).
  Use --generate to write docs, --review for deep audit.
type: workflow
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[--generate] [--review] [--dry-run] [--workflow <name>]"
version: "1.0.0"
---

# Workflow Doc Reviewer

Single entry point for workflow documentation and health review. Traces how
skills, agents, and rules interconnect across development, testing, debugging,
learning, and authoring workflows.

**Arguments:** $ARGUMENTS

## Modes

| Mode | Flag | Writes Files? | Purpose |
|------|------|---------------|---------|
| **Status** | *(default)* | No | Show workflow summary, orphans, and cross-workflow connections |
| **Generate** | `--generate` | Yes | Regenerate `docs/workflows/*.md` from reference graph |
| **Review** | `--review` | No | Deep audit: broken refs, stale seeds, missing bidirectional edges |

Additional flags:
- `--dry-run` — preview generate output without writing
- `--workflow <name>` — focus on a single workflow group

---

## STEP 1: Parse Mode

Read `$ARGUMENTS` and determine mode:

- If `--generate` is present → Generate mode (Step 3)
- If `--review` is present → Review mode (Step 4)
- Otherwise → Status mode (Step 2)

---

## STEP 2: Status Mode (default, read-only)

Run the generator in dry-run to collect data without writing:

```bash
PYTHONPATH=. python scripts/generate_workflow_docs.py --dry-run
```

Then present:

1. **Workflow summary table** — name, skill count, agent count, rule count for each group
2. **Orphan patterns** — patterns not in any workflow group (suggest where they belong)
3. **Cross-workflow connections** — which workflows feed into which others
4. **Stale check** — compare `docs/workflows/*.md` timestamps against latest skill/agent/rule modification times

If `--workflow <name>` was specified, filter output to that workflow only.

STOP here — do not write any files.

---

## STEP 3: Generate Mode (writes files)

Run the generator:

```bash
PYTHONPATH=. python scripts/generate_workflow_docs.py
```

If `--dry-run` was also specified:

```bash
PYTHONPATH=. python scripts/generate_workflow_docs.py --dry-run
```

If `--workflow <name>` was specified:

```bash
PYTHONPATH=. python scripts/generate_workflow_docs.py --workflow <name>
```

After generation:

1. Show summary of created/updated files
2. Report orphan patterns and suggest workflow group assignments
3. Ask user if they want to add **manual annotations** to any workflow doc
   - If yes: read the doc, get annotation text, append below `<!-- MANUAL ANNOTATIONS -->` marker
   - Annotations survive future regeneration runs

Run validation:

```bash
PYTHONPATH=. python scripts/validate_patterns.py
```

---

## STEP 4: Review Mode (read-only deep audit)

Perform a comprehensive workflow health audit. Read `config/workflow-groups.yml`
and all pattern files. Check for issues using the checklist in
`references/audit-checklist.md`.

### 4A: Seed Existence Check

For every seed pattern listed in `config/workflow-groups.yml`, verify the
corresponding file exists:
- Skills: `core/.claude/skills/{name}/SKILL.md` or `.claude/skills/{name}/SKILL.md`
- Agents: `core/.claude/agents/{name}.md`
- Rules: `core/.claude/rules/{name}.md`

Report any seeds pointing to non-existent patterns as **BROKEN SEEDS**.

### 4B: Cross-Reference Integrity

For each pattern in a workflow group, read its body and extract all `Skill()`,
`Agent()`, and `/skill-name` references. Check that every referenced pattern
exists. Report broken references.

### 4C: Bidirectional Edge Audit

For each edge A→B in the reference graph, check if B also references A.
One-way edges are not necessarily bugs, but flag them for review — they
may indicate incomplete integration.

### 4D: Workflow Coverage Report

Count total patterns vs. assigned patterns. Report:
- Coverage percentage (assigned / total)
- Top 10 most-connected patterns (highest in-degree + out-degree)
- Isolated patterns (0 edges — may be stubs or standalone utilities)

Present findings as a structured report. Do NOT write any files.

---

## CRITICAL RULES

- Default mode MUST be read-only — NEVER write files without explicit `--generate`
- MUST NOT edit auto-generated sections of workflow docs — only annotations below the marker
- MUST run from repository root with PYTHONPATH=.
- `config/workflow-groups.yml` is the source of truth for grouping — MUST NOT hardcode groups
- `scripts/generate_workflow_docs.py` is the standalone script — this skill wraps it, does not replace it
- Orphan patterns MUST be reported with suggested group assignments
