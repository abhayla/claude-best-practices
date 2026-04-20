# Spec: Hub-Managed File Provenance System

- **Status:** DRAFT
- **Author:** Claude Opus 4.7 (via `/brainstorm`)
- **Date:** 2026-04-21
- **Related:** `configuration-ssot.md`, `pattern-structure.md`, `scripts/recommend.py` (sync-manifest infrastructure)

---

## 1. Problem Statement

Files in `core/.claude/` are distributed verbatim into downstream projects via `recommend.py --provision`, `bootstrap.py`, and `/synthesize-project`. The hub ships updates (version bumps, new rules, refined content), and `recommend.py` already detects hub-vs-project drift via `registry/patterns.json` hashes and a 3-way `sync-manifest.json`.

**Gap:** a downstream user editing a hub-copied file has **no visible cue** that the file is hub-managed and will be overwritten on the next sync. The existing protection (`--on-conflict=interactive`) only fires at sync time — too late. Local customizations are lost, or users are surprised.

**Desired outcome:** every hub file declares its own provenance at the top. Human readers, LLM readers, and tooling can identify hub-managed files without consulting a sidecar manifest. Local customizations are routed into separate project-owned files so the hub retains clean ownership of its distributable content.

---

## 2. Chosen Approach — Scoped In-File Marker + Existing Manifest

Out of three approaches evaluated (full-file marker / manifest-only / scoped marker on loaded-as-instructions), the scoped approach wins on edge-case coverage and blast radius.

| Criteria | A: All loadable | B: Manifest only | **C: Scoped marker** (chosen) |
|---|---|---|---|
| Human visibility before edit | ✅ | ❌ | ✅ (where most-edited) |
| LLM-readable provenance | ✅ | ⚠️ | ✅ |
| Avoids polluting code examples | ⚠️ | ✅ | ✅ |
| Handles no-comment file types (JSON) | ❌ | ✅ | ✅ (manifest fallback) |
| Files touched | ~770 | 0 | ~200 |
| Validator load | High | Low | Moderate |

**Scope of marker injection** (~200 files, the ones Claude loads as instructions):

| Directory | Count | Marker format |
|---|---|---|
| `core/.claude/rules/*.md` | 24 | YAML frontmatter (add fields to existing or prepend new block) |
| `core/.claude/skills/*/SKILL.md` | 152 | YAML frontmatter (extend existing) |
| `core/.claude/agents/*.md` | 37 | YAML frontmatter (extend existing) |
| `core/.claude/hooks/*.sh` | 8 | `# hub_managed: ...` after shebang |
| `core/.claude/config/*.yml` | 2 | `# hub_managed: ...` at top |

**Explicitly NOT marked** (~570 files): skill `references/**` content (code samples, reference docs), `templates/*`, `.csv`, `.kt`, `.kts`, `.template`, `.json` configs. Drift on these is caught by the existing sync-manifest.

---

## 3. Design Sections

### 3.1 Data model — Marker fields

Every marked file carries these fields (YAML frontmatter for `.md`, `#` comments for `.sh` / `.yml`):

| Field | Type | Example | Required |
|---|---|---|---|
| `hub_managed` | bool | `true` | Yes |
| `hub_pattern` | string | `security-baseline` | Yes — matches `registry/patterns.json` key |
| `hub_version` | SemVer | `1.0.1` | Yes — matches registry `version` field |
| `hub_source` | string | `abhayla/claude-best-practices` | Yes |
| `hub_extension` | string | `.claude/rules/project-*.md` | Yes — points users to the correct local-extension location |

Hub-side validator rule (added to `workflow_quality_gate_validate_patterns.py`):
- Every file under the marker scope MUST declare all 5 fields
- `hub_version` MUST match `registry.patterns[hub_pattern].version`
- `hub_pattern` MUST be a key in `registry/patterns.json`

### 3.2 Marker syntax per file type

**.md with existing frontmatter** (scoped rules, SKILL.md, agents):
```markdown
---
name: code-reviewer-agent
description: ...
model: inherit
color: red
hub_managed: true
hub_pattern: code-reviewer-agent
hub_version: 1.2.0
hub_source: abhayla/claude-best-practices
hub_extension: ".claude/agents/project-*.md"
---
```

**.md without frontmatter** (global rules using `# Scope: global`): prepend frontmatter block:
```markdown
---
hub_managed: true
hub_pattern: security-baseline
hub_version: 1.0.1
hub_source: abhayla/claude-best-practices
hub_extension: ".claude/rules/project-*.md"
---

# Scope: global

# Security Baseline
...
```

**Shell scripts** (line 2 after shebang):
```bash
#!/bin/bash
# hub_managed: true | hub_pattern: auto-format | hub_version: 1.0.0 | hub_source: abhayla/claude-best-practices | hub_extension: "project-specific hooks registered in .claude/settings.json"
```

**YAML configs**:
```yaml
# hub_managed: true | hub_pattern: e2e-pipeline | hub_version: 1.0.0 | hub_source: abhayla/claude-best-practices | hub_extension: ".claude/config/<name>-project.yml"
<yaml body>
```

### 3.3 Extension convention (published in `configuration-ssot.md`)

| Hub file | Local extension convention |
|---|---|
| Rule (global) | New file `.claude/rules/project-<scope>.md` with `# Scope: global` — all global rules stack |
| Rule (scoped) | New file `.claude/rules/project-<scope>.md` with `globs:` frontmatter — may overlap |
| Skill | New skill directory `.claude/skills/<project-skill>/SKILL.md` — never edit hub SKILL.md |
| Agent | New file `.claude/agents/project-<name>.md` |
| Hook | Register additional hooks in `.claude/settings.json` — don't edit hub hook scripts |
| Numbered-rule extension (e.g., project-specific rule 22 in claude-behavior) | New rule file, not edit — e.g., `.claude/rules/project-behavior.md` |

### 3.4 Tooling changes

1. **Validator rule** in `scripts/workflow_quality_gate_validate_patterns.py`:
   - Every file under the marker scope (enumerated glob list) MUST have all 5 `hub_*` fields
   - `hub_version` MUST match registry
   - `hub_pattern` MUST exist in registry
2. **New script `scripts/check_hub_managed.py`**:
   - Scans a target project's `.claude/` for marked files
   - Compares content hash to `registry/patterns.json` hash
   - Compares in-file `hub_version` to registry version
   - Reports drift: `clean`, `locally-modified`, `version-behind`, `marker-missing`, `orphan` (registry has entry, no file carries marker)
   - Optional `--fix` flag re-syncs drift-free files; never overwrites locally-modified
3. **New hook `core/.claude/hooks/hub-managed-edit-warning.sh`** (Phase 3, optional):
   - PreToolUse on `Edit`/`Write`
   - Reads target's first 20 lines; if `hub_managed: true` found, prints a warning with `hub_extension` pointer
   - **Warns, does not block** — intentional edits proceed; user confirms by including `confirmed:hub-edit` in their prompt response
   - Auto-disabled when running inside the hub repo (detected by `core/.claude/` existing at repo root)

### 3.5 Migration — marker injection script

One-shot `scripts/add_hub_markers.py`:
1. Reads `registry/patterns.json`
2. For each entry in the marker scope, determines file path and injection strategy
3. Injects marker in the appropriate format
4. Idempotent: if marker already present with correct version, no-op
5. Updates `registry/patterns.json` `hash` field for each modified file
6. Dry-run mode (`--dry-run`) shows diffs without writing

### 3.6 Integration with existing sync-manifest

No breaking changes. The marker is additive information visible to humans and LLMs; `sync-manifest.json` remains the authoritative hash record at sync time. `check_hub_managed.py` consults both:
- Marker version → human/LLM-facing "what version do I have"
- Manifest hash → machine-facing "did the project modify this since last sync"

---

## 4. Requirement Tiers (MoSCoW)

### Must Have (Phase 1 — 1 PR)
- REQ-M001: Marker fields defined and documented in `pattern-structure.md`
- REQ-M002: Extension convention table added to `configuration-ssot.md`
- REQ-M003: Marker injection script (`scripts/add_hub_markers.py`) — run once to mark ~200 files
- REQ-M004: Validator enforces marker presence on marker-scope files
- REQ-M005: Registry hashes re-synced after marker injection
- REQ-M006: CI green after marker injection — no existing tests broken

### Should Have (Phase 2 — follow-up PR)
- REQ-S001: `scripts/check_hub_managed.py` drift-detection script
- REQ-S002: `sync-to-projects.yml` workflow integration — weekly drift report per enrolled repo
- REQ-S003: Downstream projects' `sync-manifest.json` format doc updated to reference marker fields

### Could Have (Phase 3 — future)
- REQ-C001: `core/.claude/hooks/hub-managed-edit-warning.sh` — PreToolUse advisory hook
- REQ-C002: Settings template opts-in the hook by default on provisioned projects
- REQ-C003: `scripts/check_hub_managed.py --fix` auto-resync mode

### Won't Have (explicitly out of scope)
- REQ-W001: Blocking hooks that prevent hub-file edits (warn-only by design — preserves flexibility)
- REQ-W002: Marker injection into skill `references/**` content (code samples would be polluted)
- REQ-W003: Marker injection into `.json` files (no-comment dialect — rely on manifest only)
- REQ-W004: Retroactive change to already-provisioned downstream projects beyond what `sync_to_projects.py` already pushes
- REQ-W005: Version-mismatch auto-repair (users decide via `--on-conflict=` flags; no silent overwrites)

---

## 5. Edge Cases & Mitigations

| Edge case | Mitigation |
|---|---|
| LLM accidentally deletes marker on edit | Validator rejects PR; LLM in downstream project sees hook warning |
| Hub self-editing triggers its own warning | Hook detects `core/.claude/` at repo root and no-ops |
| File renamed in hub | Registry key changes → sync-manifest detects orphan → `check_hub_managed.py` reports it |
| Downstream user intentionally wants to edit a hub file | Hook warns, user confirms with `confirmed:hub-edit` — not blocked |
| `.template` files render `{{VARIABLE}}` then get marker | Skip — not in marker scope |
| Stale marker version in file vs registry | `check_hub_managed.py` detects; `add_hub_markers.py --fix` resyncs |
| Project forks become their own hub | New hub updates `hub_source` field; marker injection re-runs |
| Deprecation fields (`deprecated: true`, `deprecated_by:`) | Coexist in same frontmatter; no conflict |
| Rule file that Claude loads every session | Marker adds ~5 lines of frontmatter — negligible context cost |

---

## 6. Success Criteria

- All ~200 files in marker scope carry valid `hub_managed: true` + 4 related fields
- `workflow_quality_gate_validate_patterns.py` passes
- `dedup_check.py --validate-all` passes
- `pytest scripts/tests/` remains 1024 passed / 57 skipped
- `generate_docs.py` runs clean
- `scripts/add_hub_markers.py --dry-run` on an unmarked file shows the correct diff
- `scripts/check_hub_managed.py` run against the hub itself reports `clean` for every file (no drift — markers match registry)
- A downstream `recommend.py --local <project> --provision` on a fresh project still produces identical behavior (markers flow through unchanged)
- A downstream `grep -l "hub_managed: true" <project>/.claude/` returns the expected ~200 files

---

## 7. Open Questions

1. **Marker in global rules conflicts with `# Scope: global` primacy** — the global rule convention puts `# Scope: global` in the first 5 lines for `pattern-structure.md` compliance. Adding a frontmatter block above it means the comment is no longer in the first 5 lines. Must update `pattern-structure.md` rule 2 to say "first 5 lines of content (after any frontmatter)".
2. **`hub_extension` for rules** — single pattern `project-*.md` covers most cases, but for `claude-behavior` (numbered rules), users might want `.claude/rules/project-behavior.md` specifically. Should `hub_extension` be a literal string (e.g., `.claude/rules/project-behavior.md`) or a glob pattern (e.g., `.claude/rules/project-*.md`)? Recommend: literal string pointing to a concrete suggested filename.
3. **Should Phase 1 include a starter `project-*.md` template** in `core/.claude/templates/` that downstream projects can copy when they want to add extensions? Makes the extension convention zero-friction. Cheap to add.
4. **Retroactive update for already-provisioned downstream projects** — do we push markers to existing downstream projects immediately via `sync_to_projects.py`, or only on their next explicit `recommend.py --provision` run? Recommend: push via next scheduled `sync-to-projects.yml` cron; no forced out-of-band update.

---

## 8. Handoff

Next step options:
- **`/writing-plans`** — break Phase 1 into bite-sized implementation tasks with verification commands
- **`/implement`** — execute Phase 1 directly (script + validator + docs)
- **`/adversarial-review`** — adversarial review of this spec before committing to build

Recommended next: `/writing-plans` to produce a task-level plan for Phase 1, then `/implement` the plan. This spec stays the authoritative reference throughout.
