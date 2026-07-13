# Plan — Convert plugin-superseded core/ skills to thin install-pointers (#346 stage 3)

**Status:** planned (stage B of the 2026-07-13 owner-approved backlog) · **Owner:** Abhay ·
**Driver:** Claude · **Precedent:** `plans/prompt-auto-enhance-core-retirement.md` (v4.0.0
pointer stub, `type: reference`, MAJOR bump, dual-home reclassified) — proven in production.

## Why

With all 5 enrolled repos plugins-first and the hub dogfooding its own plugins (PR #352),
the full-content `core/` copies of plugin-shipped skills are the last drift surface: two
sources of truth per skill (plugin = live, core template = shadow). Converting each core copy
to a thin "install the plugin" pointer makes the plugin the single source of truth while
provisioning still surfaces the capability (pointer explains where it went) instead of
silently dropping it.

## Scope (what converts, what stays)

- CONVERT: core skills whose full content ships in a marketplace plugin —
  cbp-workflows (16), cbp-build-test-workflows (17), cbp-learning-workflow (5),
  cbp-react-stack (6), cbp-python-stack (4), loop-engineering closure (13),
  branch-lifecycle set (6). De-duplicated union ≈ 55 core skills.
- STAYS full-content in core/: rules (plugins can't ship them), stack helpers with no pack,
  hooks templates, configs, project-owned templates, and any skill NOT plugin-shipped.

## Consumer classes that break naively (enumerated 2026-07-13 — the reason this is staged)

1. **Content-pinning tests** — e.g. `test_code_review_nested_verify.py`,
   `test_pipeline_integrity.py`, `test_workflow_closure_consistency.py` `_read()` core
   SKILL.md files and assert steps/closures. Each cluster's conversion must repoint these
   tests at the PLUGIN copy (new SSOT) — mechanical path swap, but per-test review required
   (the 2026-06-19 RETIRE lesson: verify consumers before touching).
2. **recommend.py closures** — `MUST_HAVE_AGENTS`/workflow closure sets reference these
   skill names for copy-provisioning; each converted cluster's names must move from the
   copy-closure to the plugin-recommendation path (config/plugin-recommendations.yml already
   carries the plugin side).
3. **Docs generation** — `generate_workflow_docs.py` + `config/workflow-groups.yml` seeds
   read core files; converted clusters must either repoint the generator at plugins/ or
   accept pointer-stub docs (decide per cluster; prompt-auto-enhance precedent accepted the
   stub).
4. **workflow-contracts.yaml** — `entry_skill:` names stay valid (plugin serves the same
   name); no change expected, verify per cluster.
5. **project-manager-agent** — dispatches workflows by bare name; plugin-served names
   resolve (proven in the cbp9 composition E2E); verify once in cluster 1.
6. **Registry** — each converted skill: MAJOR version bump + hash resync +
   `type: reference`; dual-home entries for any hub↔core pairs reclassified.
7. **Eval-coverage ratchet** — pointer stubs count as "changed skills"; they are
   grandfathered (they predate the gate) — no new evals needed for stubs.

## Staged execution (one cluster per loop cycle, full gate each)

- **Cluster 1:** quality trio (`code-review-workflow`, `documentation-workflow`,
  `skill-authoring-workflow`) — smallest test surface, validates the recipe end-to-end.
- **Cluster 2:** build-test (`test-pipeline`, `development-loop`) — heaviest test pinning
  (three-lane spec tests); do second with cluster-1 lessons.
- **Cluster 3:** learning + loop-engineering closure + branch-lifecycle set.
- **Cluster 4:** stack packs' skills + the sub-skill long tail.
- Each cluster: enumerate consumers (grep tests/configs/scripts) → convert stubs (precedent
  frontmatter: `type: reference`, MAJOR bump) → repoint tests to plugin copies → registry +
  dual-home + changelog → full gate → land → verify one downstream provision run shows the
  pointer, one plugin invocation still serves full content.

## Definition of done

All plugin-shipped core skills are pointers; full gate green; a fresh `recommend.py
--provision` run on a test project copies pointers + prints the plugin install set; the
dual-home gate carries no stale pairs; SYNC-ARCHITECTURE and CLAUDE.md reflect the end state.

## Log

- 2026-07-13 — Plan written; consumer classes enumerated; cluster 1 queued for a
  fresh-context session per context-management rule 7 (this session already carried the
  dogfood install, sync retirement, and eval ratchet to done).
