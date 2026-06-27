---
name: promote-to-core
description: Promote a hub-only pattern (a skill/agent/rule living only in .claude/) into the distributable core/.claude/ template so downstream projects can provision it. Codifies every convention — frontmatter standard, registry entry + hash + tier, dual-home classification, docs regen, the full CI gate, and landing — so the promotion is a 5-step recipe instead of a 30-step rediscovery. Use when the user says "promote X to core", "make X distributable", or "ship X to downstream projects".
type: workflow
version: 1.0.0
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
argument-hint: "<pattern-name> [--tier must-have|nice-to-have]"
---

# Promote a Hub-Only Pattern to Distributable `core/`

Moves a pattern from `.claude/` (hub-only operational) into `core/.claude/` (the template
downstream projects provision), registers it, and lands it — all gates green. This is the
INTERNAL hub-only→both flow; it is NOT `/synthesize-hub` (which pulls patterns FROM
downstream projects INTO the hub). Read `docs/HUB-CORE-SYNC.md` for the scoping doctrine.

> **Only promote what downstream projects can actually use.** Hub *machinery* (scan/synthesis/
> governance skills, this skill, the checks-runner agent) stays hub-only. A pattern is
> promotable only if it is self-contained and portable (no hub-only path/script dependency).

## STEP 1: Confirm it's promotable, pick the tier

- Verify the pattern currently lives ONLY in `.claude/` (not already in `core/.claude/`).
- Confirm it's portable: no reference to hub-only scripts (`dedup_check.py`, `collate.py`, …),
  `registry/`, `core/`, or hub-only paths. If it depends on those, it is machinery — stop.
- **Check for companion patterns.** If the skill references HOOKS (or other skills/agents) that
  are NOT yet in `core/`, the promotion is a BUNDLE: promote those companions too, or the
  distributed skill points at machinery that doesn't exist downstream. Each companion hook runs
  the same copy→register→dual-home pipeline AND must be wired into `core/.claude/settings.json`
  (STEP 3 — copy the hook + add its entry to the right event block in `core/.claude/settings.json`,
  matching the hub's wiring). Verify with: `comm -23 <(grep -o '[a-z-]*\.sh' SKILL.md|sort -u) <(ls core/.claude/hooks)`.
- Choose `tier`: `must-have` (core dev workflow) | `nice-to-have` (useful utility) | `skip`.

## STEP 2: Bring the pattern file up to the registered standard

For a **skill** (`SKILL.md`), the quality gate REQUIRES these frontmatter fields:
`name, description, type, allowed-tools, argument-hint, version`.
- `type` MUST be `workflow` or `reference`. **`workflow` REQUIRES `## STEP N:` sections** in
  the body (the validator fails a workflow with no steps). `reference` MUST be read-only — no
  `Write`/`Edit` in `allowed-tools`.
- `description` should start with an action verb and include a "Use when…" clause.
- SKILL.md must be ≤ 1000 lines (warns over 500).
For an **agent** (`*.md` in `agents/`): required frontmatter `name, description, model` (or
`tools`); match an existing core agent's shape.
Make the edits in the `.claude/` copy first; the `core/` copy will be identical.

## STEP 3: Copy into the `core/` tree

```bash
mkdir -p core/.claude/skills/<name>            # or core/.claude/agents, /rules, /hooks
cp -r .claude/skills/<name>/* core/.claude/skills/<name>/
```
Copy EVERY file in the pattern dir (SKILL.md + any scripts/references), not just SKILL.md.

## STEP 4: Register it in `registry/patterns.json` (minimal-diff!)

The registry hash is the normalized SHA256 of the file the locator resolves —
`core/.claude/skills/<name>/SKILL.md` for skills. Compute it with the repo's own function,
never by hand:

```bash
python -c "import sys;sys.path.insert(0,'scripts');from dedup_check import hash_pattern;print(hash_pattern('core/.claude/skills/<name>/SKILL.md'))"
```

Then add the entry. **Avoid the reformat trap:** the file uses `ensure_ascii=False` and `_meta`
is NOT the last key — so load with `OrderedDict`, APPEND the new key (do not move `_meta`), and
dump `ensure_ascii=False, indent=2`. A naive `json.load`+`json.dump` re-escapes every em-dash
and reorders `_meta`, producing a 150-line diff. Required entry fields (copy an existing skill
entry's shape): `hash, type:skill, category, version, source, discovered, last_updated,
dependencies, visibility, description, tags, changelog, tier`. Bump `_meta.total_patterns`
(+1) and `_meta.last_updated`. Confirm the diff is tight: `git diff --stat registry/patterns.json`.

## STEP 5: Classify the dual-home pair

The pattern now lives in BOTH `.claude/` and `core/.claude/` → it MUST be classified in
`config/dual-home-resources.yml` or the drift gate fails:
- `synced` — the two copies are normalized-identical (the common case for a clean promotion).
- `divergent` — they intentionally differ; add a one-line reason.
Add `<name>` under the right class (e.g. `synced: skills:`).

## STEP 6: Regenerate docs

```bash
PYTHONPATH=. PYTHONUTF8=1 python scripts/generate_docs.py
PYTHONPATH=. PYTHONUTF8=1 python scripts/generate_workflow_docs.py
```
This updates `docs/`, `README.md` counts, and may auto-add the pattern to
`config/workflow-groups.yml` (benign). An "orphan pattern" warning just means no workflow
group — non-blocking.

## STEP 7: Run the full gate (dispatch `checks-runner-agent`)

Run the entire local CI in an isolated context so its output never floods the session —
dispatch the **`pre-git-merge-checker-agent`** and act on its PASS/FAIL verdict. It runs:
`dedup_check.py --validate-all`, `--secret-scan`, `workflow_quality_gate_validate_patterns.py`,
`pytest scripts/tests/` (incl. `test_dual_home_sync.py`). Fix any failure before landing.

## STEP 8: Commit, push, land

`.claude/` is gitignored — stage its files with `git add -f`; `core/`, `registry/`, `config/`,
`docs/`, `README.md` stage normally.

```bash
git add core/.claude/... registry/patterns.json config/dual-home-resources.yml config/workflow-groups.yml README.md docs/
git add -f .claude/skills/<name>/SKILL.md
git commit -m "feat(skill): promote <name> to distributable core/"
git push -u origin <branch>
bash "$(git rev-parse --show-toplevel)/.claude/hooks/session-git-landing.sh" land --wait
```

## Conventions cheat-sheet (the things easy to rediscover)

- Hash = `dedup_check.hash_pattern(<core SKILL.md>)`; the locator prefers `core/.claude/...`.
- Every registry entry needs a `tier`. `category` is usually `core` (universal, no stack prefix).
- `type: workflow` ⇒ must have `## STEP N:` headings. `type: reference` ⇒ read-only tools.
- Registry edit: append key, keep `_meta` in place, `ensure_ascii=False` — or you get a giant diff.
- Hub-only patterns (machinery) are NOT registered and NOT promoted; only portable patterns are.
