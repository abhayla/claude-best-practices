# #346 Stage 2 — retire superseded `core/` workflow skills to thin plugin pointers

Owner-approved 2026-07-14 ("go ahead with your recommendation", queue item 2). Template:
`plans/prompt-auto-enhance-core-retirement.md` (the first core→plugin-as-SSOT graduation).
Stage 1 (all 5 downstream repos plugins-first) and the stage-3 first slice (recommend cron
retired, PR #406) are DONE; this plan covers the remaining conversions.

## Design decision (resolved here, applies to every conversion)

**A provisioned copy SHADOWS an installed plugin's same-named skill** (verified during the
loop-engineering plugin validation). So a thin pointer must NEVER be provisioned alongside the
plugin. Resolution: `config/plugin-recommendations.yml` is already the SSOT `recommend.py`
consults — plugin-covered skills are excluded from copy-provision, and the 2026-07-13 migration
pruned existing copies downstream. Therefore:

- The `core/` SKILL.md becomes a **pointer** (type `reference`, MAJOR version bump) whose body
  says "install `<plugin>@claude-best-practices`" — it exists ONLY as the provisioning-surface
  redirect so the capability is never silently dropped, mirroring prompt-auto-enhance v4.0.0.
- `config/workflow-contracts.yaml` and `config/workflow-groups.yml` keep the SHORT skill name
  (the plugin serves the real skill under that name once installed; the pointer never ships to
  a plugin-covered project).
- Registry entry survives (hash + MAJOR bump + changelog line); dual-home: these are core-only
  (no hub `.claude/skills/` copy), so no reclassification — VERIFY per skill before assuming.

## Conversion recipe (per skill — one PR per cluster)

1. Rewrite `core/.claude/skills/<name>/SKILL.md` as the pointer (~45 lines): frontmatter kept
   (name, `type: reference`, `allowed-tools: "Read"`, MAJOR bump), body = what moved, install
   commands, why (single SSOT), namespaced invocation note.
2. Delete the skill's `references/` + `evals/` subdirectories (content lives in the plugin now);
   remove the skill from `config/eval-coverage-grandfather.yml` (ratchet shrinks — pointer needs
   no evals, and the entry may only be REMOVED).
3. Registry: resync `hash` via `dedup_check.hash_pattern()`, MAJOR bump, `last_updated`,
   changelog line, description → pointer description.
4. Regen docs (`generate_docs.py` + `generate_workflow_docs.py`); expect workflow docs to shrink.
5. Full local gate (all 6 CI checks). Watch specifically: `test_workflow_closure_consistency.py`
   (closure assertions vs a body with no dispatches) and `check_eval_coverage --enforce`.
6. Update the `#346` issue comment with the conversion's PR.

## Inventory (converted when its plugin is the proven SSOT)

| Cluster (plugin) | Core skills to convert | Status |
|---|---|---|
| `cbp-learning-workflow` | `learning-self-improvement`, `learn-n-improve`, `skill-factory`, `test-knowledge` | **PILOT: `learning-self-improvement` — this PR** |
| `cbp-workflows` | `code-review-workflow`, `documentation-workflow`, `skill-authoring-workflow` + their 13 sub-skills | pending pilot verdict |
| `cbp-build-test-workflows` | `development-loop`, `test-pipeline` + their 15 sub-skills | pending pilot verdict |
| `loop-engineering` | `loop-engineering` + its 13-skill closure | pending pilot verdict |

Sub-skills convert ONLY when no non-plugin consumer remains (grep the full repo per skill —
several sub-skills like `fix-loop`/`systematic-debugging` are referenced by rules
(`claude-behavior.md` rule 15) and stack skills, so they may need to stay full copies far
longer; the "declare unused" bar of the verify-before-suggest rule applies).

## Cluster-1 sweep verdicts (2026-07-14 — recorded so the next session doesn't re-derive)

All three remaining cbp-learning-workflow sub-skills **STAY full copies** under the strict
no-non-plugin-consumer rule:

- `learn-n-improve` — consumed by RULES (`claude-behavior.md` rule 15, `continuous-improvement.md`,
  `learnings-routing.md`), `project-manager-agent`, and many stack skills (android-run-*, …).
- `skill-factory` — consumed by `skill-master`, `writing-skills` references.
- `test-knowledge` — consumed by `fix-loop`, `systematic-debugging`.

**Design finding this forces (stage-4 fork, OWNER decision):** the workflows cross-reference each
other and are referenced by global rules pervasively, so under the strict rule the safely
convertible set beyond entry-skill pointers is ~empty. The refined criterion — convert when every
consumer resolves at runtime via the universally-recommended plugin — converts everything, but
degrades any project that copy-provisions WITHOUT installing plugins (e.g. rule 15's `/fix-loop` /
`/learn-n-improve` would hit pointers). That is exactly #346's endgame question: declare
plugins-first the ONLY supported distribution for workflow capabilities (copy-provision keeps only
path-scoped rules + stack helpers), or keep dual distribution and stop converting here. Until the
owner picks, conversions beyond already-landed pointers are BLOCKED-BY-DESIGN-DECISION, not
mechanical work.

## Risks / open questions

- **Closure guard semantics** after a workflow's entry skill becomes a pointer — the pilot
  answers this empirically; if the guard needs a `pointer: true` exemption, add it in the same
  PR as the first failing conversion, never weaken assertions for full skills.
- **`update-practices`** already excludes plugin-covered content (hub #346 stage 2 note in its
  description); verify its exclusion list matches the converted set as conversions land.
- **Rollback**: every conversion is a single revertable PR; the plugin content is untouched.
