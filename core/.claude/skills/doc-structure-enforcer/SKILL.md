---
name: doc-structure-enforcer
description: >
  Enforce a stage-based documentation folder structure via config-driven rules.
  Two modes: audit (report misplaced files) or enforce (git mv + update all path
  references). Auto-generates .doc-structure.yml on first run if missing. Aligns
  with project-manager-agent's 11-stage artifact layout.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "--audit | --enforce [--config <path>]"
version: "1.0.0"
---

# Doc Structure Enforcer

Audit and enforce a stage-based documentation folder structure. Config-driven via
`.doc-structure.yml` at project root.

**Arguments:** $ARGUMENTS

---

## MODE SELECTION

- `$ARGUMENTS` contains `--enforce` → **Enforce mode** (move files + update references)
- `$ARGUMENTS` contains `--audit` or no flag → **Audit mode** (report only, read-only)
- `--config <path>` overrides default config location (`.doc-structure.yml`)

---

## Expected Folder Structure

```
docs/
├── index.md                          # Auto-generated cross-cutting navigation
├── api/                              # API docs (OpenAPI specs, endpoint refs)
├── architecture/                     # Architecture & design docs
├── stages/
│   ├── stage-1-prd/
│   │   ├── input/                    # Raw requirements
│   │   └── output/                   # Finalized PRD
│   ├── stage-2-plan/
│   │   ├── input/
│   │   └── output/                   # Plan, ADRs
│   ├── stage-3-scaffold/
│   │   ├── input/
│   │   └── output/
│   ├── stage-4-demo/
│   │   ├── input/
│   │   └── output/                   # Screenshots, IMPL-MAPPING
│   ├── stage-5-schema/
│   │   ├── input/
│   │   └── output/                   # ERD, migration docs
│   ├── stage-6-pre-tests/
│   │   ├── input/
│   │   └── output/                   # Test matrix
│   ├── stage-7-impl/
│   │   ├── input/
│   │   └── output/                   # Progress tracking
│   ├── stage-8-post-tests/
│   │   ├── input/
│   │   └── output/                   # E2E, perf, security reports
│   ├── stage-9-review/
│   │   ├── input/
│   │   └── output/                   # Review report
│   ├── stage-10-deploy/
│   │   ├── input/
│   │   └── output/                   # Runbooks, DR-RUNBOOK
│   └── stage-11-docs/
│       ├── input/
│       └── output/                   # Handover, architecture, summary
└── PIPELINE-SUMMARY.md               # Generated on pipeline completion
```

---

## STEP 1: Load or Generate Config

Check if `.doc-structure.yml` exists at the project root (or `--config` path).

### If config exists:

Parse and validate the YAML. Required top-level keys: `doc_root`, `structure`. Each entry in `structure` must have `path` and `description`. Warn on missing optional keys (`patterns`, `content_signals`).

### If config is missing:

1. Scan the existing `docs/` directory to understand current layout
2. Copy the default template from this skill's `templates/.doc-structure.yml`
3. Adapt it based on what was found (remove stage folders if no pipeline state exists, keep only relevant entries)
4. Write it to `.doc-structure.yml` at project root
5. Print:
   ```
   No .doc-structure.yml found.
   Generated default config at .doc-structure.yml
   Review the config, then re-run:
     /doc-structure-enforcer --audit    (to check compliance)
     /doc-structure-enforcer --enforce  (to move misplaced files)
   ```
6. **STOP** — first run is always config-generation only

---

## STEP 2: Scan Documentation Files

Find all documentation files in the project:

```bash
find . -type f \( -name "*.md" -o -name "*.rst" -o -name "*.txt" \) \
  | grep -iv "node_modules\|vendor\|\.git\|dist\|build\|\.next\|__pycache__"
```

For each file, record:
- File path (relative to project root)
- Filename
- Line count
- Whether it matches an `ignore` pattern from config
- Whether it matches a `generated` entry from config
- Whether it's in the `root_docs.allowed` list

Build the file manifest:

```markdown
## File Manifest

| File | Lines | Status |
|------|-------|--------|
| README.md | 104 | Root doc (allowed) |
| docs/ARCHITECTURE.md | 230 | Needs classification |
| docs/DASHBOARD.md | 150 | Generated (skip) |
| docs/stages/STAGE-1-PRD.md | 85 | Needs classification |
```

Skip files matching `ignore`, `generated`, or `root_docs.allowed` patterns.

---

## STEP 3: Classify Files

For each file needing classification, apply the 3-tier strategy:

### Tier 1: Filename Pattern Match

Match the filename against `patterns` in each `structure` entry from config. Use glob matching. First match wins.

Example: `feature-prd.md` matches `**/*-prd.md` → target: `docs/stages/stage-1-prd/output/`

### Tier 2: Content Signal Fallback

If no pattern matched, read the first 50 lines and check for `content_signals`:

| Content signal found | Target folder |
|---------------------|---------------|
| `"openapi:"` or `"## API Reference"` | `docs/api/` |
| `"## Architecture"` or `"## System Design"` | `docs/architecture/` |
| `"## Product Requirements"` or `"## User Stories"` | `docs/stages/stage-1-prd/output/` |
| `"## Implementation Plan"` or `"## Task Breakdown"` | `docs/stages/stage-2-plan/output/` |
| `"## Entity Relationship"` or `"## Database Schema"` | `docs/stages/stage-5-schema/output/` |
| `"## Test Matrix"` or `"## Test Plan"` | `docs/stages/stage-6-pre-tests/output/` |
| `"## Code Review"` | `docs/stages/stage-9-review/output/` |
| `"## Runbook"` or `"## Disaster Recovery"` | `docs/stages/stage-10-deploy/output/` |
| `"## Handover"` or `"## Final Documentation"` | `docs/stages/stage-11-docs/output/` |

First match wins. All signals come from the config file — this table is the default set.

### Tier 3: Unclassified

If neither pattern nor content matched, mark as **unclassified** and report for user decision.

Output:

```markdown
## Classification Results

| File | Current | Target | Method | Confidence |
|------|---------|--------|--------|------------|
| docs/feature-prd.md | docs/ | docs/stages/stage-1-prd/output/ | Pattern | High |
| docs/ARCHITECTURE.md | docs/ | docs/architecture/ | Content | High |
| docs/random-notes.md | docs/ | ? | Unclassified | — |
```

---

## STEP 4: Compute Misplacements

Compare each classified file's current path against its target path:

- **Correctly placed** — current path is inside the target directory
- **Misplaced** — current path differs from target directory
- **Unclassified** — no target could be determined

Also check for **missing directories** — target folders from config that don't exist yet.

---

## STEP 5: Report

Print the structured audit report:

```markdown
## Doc Structure Audit Report

**Config:** .doc-structure.yml
**Files scanned:** N
**Timestamp:** YYYY-MM-DD HH:MM

### Correctly Placed (N files)
| File | Location | Category |
|------|----------|----------|
| docs/stages/stage-1-prd/output/feature-prd.md | stage-1 output | PRD |

### Misplaced (N files)
| File | Current Location | Expected Location | Method |
|------|-----------------|-------------------|--------|
| docs/ARCHITECTURE.md | docs/ | docs/architecture/ | Content signal |

### Unclassified (N files)
| File | Current Location | Reason |
|------|-----------------|--------|
| docs/random-notes.md | docs/ | No pattern or content match |

### Missing Directories
| Expected Directory | Status |
|-------------------|--------|
| docs/stages/stage-1-prd/input/ | Missing |

### Summary
| Status | Count |
|--------|-------|
| Correctly placed | N |
| Misplaced | N |
| Unclassified | N |
| Missing dirs | N |
```

**If mode is `--audit`, STOP HERE.**

---

## STEP 6: Plan Moves (Enforce Mode Only)

For each misplaced file, compute the move:

1. Determine `mkdir -p` commands for missing target directories
2. Compute `git mv <source> <target>` for each file
3. Check for conflicts — if a file with the same name already exists at the target, report as conflict and skip

Print the move plan:

```markdown
## Move Plan

### Directories to Create
mkdir -p docs/architecture
mkdir -p docs/stages/stage-1-prd/input
mkdir -p docs/stages/stage-1-prd/output

### Files to Move
| # | Command | Reason |
|---|---------|--------|
| 1 | git mv docs/ARCHITECTURE.md docs/architecture/ARCHITECTURE.md | Content: "## Architecture" |
| 2 | git mv docs/feature-prd.md docs/stages/stage-1-prd/output/feature-prd.md | Pattern: *-prd.md |

### Conflicts (skipped)
| File | Target | Conflict |
|------|--------|----------|
| (none) | | |
```

**ASK USER FOR CONFIRMATION before proceeding.**

---

## STEP 7: Scan References (Enforce Mode Only)

For each file to be moved, scan the entire repo for references to the old path:

```bash
grep -rn "docs/ARCHITECTURE.md" \
  --include="*.md" --include="*.yml" --include="*.yaml" \
  --include="*.py" --include="*.json" --include="*.ts" \
  --include="*.js" --include="*.toml" --include="*.cfg"
```

Build the reference update plan:

```markdown
## Reference Update Plan

| Source File | Line | Old Reference | New Reference |
|------------|------|---------------|---------------|
| README.md | 42 | docs/ARCHITECTURE.md | docs/architecture/ARCHITECTURE.md |
| CLAUDE.md | 101 | docs/ARCHITECTURE.md | docs/architecture/ARCHITECTURE.md |
| config/pipeline-stages.yaml | 189 | docs/ARCHITECTURE.md | docs/architecture/ARCHITECTURE.md |
```

Exclude matches inside:
- `.git/` directory
- `node_modules/`, `vendor/`, `dist/`, `build/`
- Binary files
- The `.doc-structure.yml` config itself (paths there are patterns, not references)

**ASK USER FOR CONFIRMATION before applying reference updates.**

---

## STEP 8: Execute Moves and Update References (Enforce Mode Only)

### 8.1 Create Directories

```bash
mkdir -p <each missing target directory>
```

### 8.2 Move Files

```bash
git mv <source> <target>
```

If `git mv` fails (file not tracked), fall back to `mv` and `git add`.

### 8.3 Update References

For each reference in the update plan, use Edit to replace the old path with the new path in the source file.

### 8.4 Generate Index

Create or update `docs/index.md` with cross-cutting navigation:

```markdown
# Documentation Index

Auto-generated by `/doc-structure-enforcer`. Links to all documentation organized by category.

## API
- [API Reference](api/api-reference.md)

## Architecture
- [System Architecture](architecture/ARCHITECTURE.md)

## Pipeline Stages
| Stage | Input | Output |
|-------|-------|--------|
| 1. PRD | [input](stages/stage-1-prd/input/) | [feature-prd.md](stages/stage-1-prd/output/feature-prd.md) |
| 2. Plan | [input](stages/stage-2-plan/input/) | [feature-plan.md](stages/stage-2-plan/output/feature-plan.md) |
```

### 8.5 Verify

Re-scan for broken references to confirm all old paths have been updated:

```bash
# Check each old path no longer appears
grep -rn "<old-path>" --include="*.md" --include="*.yml" --include="*.py" --include="*.json"
```

### 8.6 Execution Report

```markdown
## Execution Report

### Moves Completed
| File | From | To | Status |
|------|------|----|--------|
| ARCHITECTURE.md | docs/ | docs/architecture/ | Moved |

### References Updated
| File | Updates | Status |
|------|---------|--------|
| README.md | 1 | Updated |
| CLAUDE.md | 1 | Updated |

### Index
- docs/index.md: Generated / Updated

### Verification
- Broken references remaining: 0
- All moves successful: Yes
```

---

## MUST DO

- MUST auto-generate `.doc-structure.yml` on first run if missing, then STOP for user review
- MUST use `git mv` (not plain `mv`) to preserve git history
- MUST preview all moves and reference changes before executing
- MUST ask for user confirmation before any file moves in enforce mode
- MUST scan for references across all common file types (md, yml, yaml, py, json, ts, js, toml)
- MUST create target directories before moving files
- MUST report unclassified files separately — never force-classify ambiguous docs
- MUST re-verify references after moves to catch any missed updates
- MUST generate `docs/index.md` after enforcing to provide cross-cutting navigation

## MUST NOT DO

- MUST NOT move files without user confirmation in enforce mode
- MUST NOT modify any files in audit mode — audit is strictly read-only
- MUST NOT delete any files — only move them to correct locations
- MUST NOT overwrite existing files at the target location — report conflicts instead
- MUST NOT move files listed in `root_docs.allowed` out of the project root
- MUST NOT move files listed in `generated` — these are managed by scripts
- MUST NOT update references inside `.git/`, `node_modules/`, `vendor/`, or `dist/`
- MUST NOT assume the stage folder structure exists — create directories as needed

## See Also

- `/diataxis-docs` — Alternative docs organization using the Diataxis framework (tutorials, how-to, reference, explanation)
- `/doc-staleness` — Detect stale references after restructuring; run after enforce to verify integrity
- `/adr` — Create Architecture Decision Records; routed to `docs/stages/stage-2-plan/output/` by default config
- `/api-docs-generator` — Generate API docs that belong in `docs/api/`
- `/changelog-contributing` — Generate CHANGELOG.md and CONTRIBUTING.md; these are root docs, not enforced by this skill
- `docs-manager` agent — Orchestrates documentation updates, delegates structure enforcement to this skill
