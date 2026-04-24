# Phase 3 Doc-Pruning Checklist

**Generated:** 2026-04-24 (session 2, branch `docs/phase3-doc-pruning-audit`)
**Purpose:** Per-sub-PR list of documents that reference deprecated workflow-master agents + legacy tier terminology. Each Phase 3 sub-PR is responsible for pruning the docs tied to its workflow; no single "big bang" doc cleanup.

**Source data:** grep across `*.md` in the repo for 12 deprecated/deprecating agent/skill names. Cross-referenced against the expanded Phase 3 plan in `.claude/tasks/todo.md`.

---

## Category A — Auto-regenerate (zero manual work per PR)

These regenerate from `registry/patterns.json` + pattern frontmatter. Each Phase 3 sub-PR runs the generators at its end; no per-file manual edits.

| File | Generator |
|---|---|
| `docs/workflows/testing-pipeline.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/development-loop.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/debugging-loop.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/code-review.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/documentation.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/session-continuity.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/learning-self-improvement.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/skill-authoring.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/ops-quality.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/_needs-manual-review.md` | `scripts/generate_workflow_docs.py` |
| `docs/workflows/images/*.svg` | same (Mermaid → SVG pipeline) |
| `docs/DASHBOARD.md` | `scripts/generate_docs.py` |
| `docs/dashboard.html` | `scripts/generate_docs.py` |

**Action per Phase 3 sub-PR:** final commit of each sub-PR runs `python scripts/generate_docs.py && PYTHONPATH=. python scripts/generate_workflow_docs.py` and commits the diff as a single `docs(generated): regenerate after <workflow-id> refactor` commit.

---

## Category B — Runtime / tracking (self-managed, do not edit in sub-PR)

These are session artifacts, not shipped docs. They update organically during the relevant session; no PR-level intervention needed.

| File | Role |
|---|---|
| `.claude/tasks/prompts.md` | Live prompt log (gitignored per session notes) |
| `.claude/tasks/lessons.md` | Corrections + surprising outcomes (append-only per session) |
| `.claude/tasks/todo.md` | Current-task tracker |
| `.claude/skills/skill-evaluator/EVAL-LEARNINGS.md` | Hub-local eval notes (mirrored to `core/` but treated as log) |

---

## Phase 3.1 — Test pipeline doc prune

**Touches:** every file that describes the legacy tier dispatch model for the test pipeline, the deprecated T1/T2A/T2B agents, the three-lane spec v1, or the legacy `/testing-pipeline-workflow` skill.

### Must update in Phase 3.1 PR

| File | Why it needs editing | Scope |
|---|---|---|
| `README.md` | Describes `/test-pipeline` + workflow overview | Replace tier-model language with skill-at-T0; update slash command inventory |
| `docs/specs/test-pipeline-three-lane-spec.md` (v1.7) | Active v1 spec referenced throughout the codebase | Add top-of-file banner pointing at v2 (from PR #23); mark status SUPERSEDED. Do NOT delete — it's the canonical reference for v1 requirements that v2 preserves by ID |
| `docs/specs/test-pipeline-three-lane-spec-v2.md` | Current v2 draft | Promote status DRAFT → ACCEPTED once Phase 3.1 PR is approved |
| `docs/plans/test-pipeline-overhaul-plan.md` | Historical plan document | Add post-script noting Phase 3.1 rewrites §3.3/§3.5/§3.8; link forward to v2 spec |
| `docs/plans/test-pipeline-overhaul-findings.md` | Historical findings | Same as plan — add post-script |
| `docs/plans/test-pipeline-three-lane-pr2-plan.md` | PR2 plan (failure-triage) | Mark SUPERSEDED — T2B dissolved in Phase 3.1 |
| `docs/plans/test-pipeline-downstream-verification.md` | Downstream verification plan | Update `/testing-pipeline-workflow` → `/test-pipeline`; remove tier refs |
| `docs/sequence diagram testing-pipeline-workflow.md` | Sequence diagram of legacy flow | Either regenerate for new skill-at-T0 flow OR mark SUPERSEDED |
| `docs/stages/STAGE-7-IMPLEMENTATION.md` | Pipeline stage 7 doc that invokes `/test-pipeline` | Update invocation to reflect new semantics (no user-visible change, but documentation should match) |
| `docs/QA-AGENT-ECOSYSTEM-RESEARCH-2026-04-22.md` | Historical research doc | Add post-script: "findings on nested Agent dispatch invalidated by 2026-04-24 platform constraint" |

### Agent bodies that reference the deprecated agents (update in Phase 3.1 PR)

These are worker-agent descriptions that mention `testing-pipeline-master-agent` / `test-pipeline-agent` / `failure-triage-agent` / `e2e-conductor-agent` in their own body (tier declaration, dispatch context, etc.):

| File | Reference type | Action |
|---|---|---|
| `core/.claude/agents/test-scout-agent.md` | "dispatched by test-pipeline-agent" | Replace with "dispatched by /test-pipeline skill-at-T0" |
| `core/.claude/agents/tester-agent.md` | Lane-dispatch context references | Same |
| `core/.claude/agents/fastapi-api-tester-agent.md` | Same | Same |
| `core/.claude/agents/visual-inspector-agent.md` | Same | Same |
| `core/.claude/agents/test-healer-agent.md` | E2E conductor references | Same |
| `core/.claude/agents/test-failure-analyzer-agent.md` | T2B dispatch context | Replace with "dispatched directly by /test-pipeline at T0" |
| `core/.claude/agents/github-issue-manager-agent.md` | Same | Same |
| `core/.claude/agents/project-manager-agent.md` | Describes dispatching `testing-pipeline-master-agent` for stages 6-8 | Replace with "invokes `Skill(\"/test-pipeline\", …)` for stages 6-8" per Phase 1 §10 dual-mode rules |

### Skill bodies that reference the deprecated agents (update in Phase 3.1 PR)

| File | Reference type |
|---|---|
| `core/.claude/skills/test-pipeline/SKILL.md` | FULL REWRITE (this IS the Phase 3.1 work) |
| `core/.claude/skills/e2e-visual-run/SKILL.md` | FULL REWRITE — dispatches queue workers directly from T0 |
| `core/.claude/skills/auto-verify/SKILL.md` | References `testing-pipeline-master-agent` in some paths | Replace with skill-at-T0 language |
| `core/.claude/skills/fix-issue/SKILL.md` | Same | Same |
| `core/.claude/skills/create-github-issue/SKILL.md` | Same | Same |
| `core/.claude/skills/serialize-fixes/SKILL.md` | T2B dispatch references | Replace with "invoked inline by /test-pipeline at T0" |
| `core/.claude/skills/escalation-report/SKILL.md` | Same | Same |
| `core/.claude/skills/pipeline-fix-pr/SKILL.md` | Same | Same |
| `core/.claude/skills/agent-evaluator/SKILL.md` | References orchestrator evaluation | Update tier vocabulary if present |

### Rule files that mention legacy tier vocabulary (verify only)

| File | Action |
|---|---|
| `core/.claude/rules/testing.md` | Verify no leftover `T1/T2A/T2B dispatch` language (expect clean after Phase 1 rewrite, but double-check) |
| `core/.claude/skills/playwright/references/common-patterns.md` | May reference `e2e-conductor-agent`; update if found |

### Config

| File | Action |
|---|---|
| `config/workflow-contracts.yaml` → `testing-pipeline` | Empty `sub_orchestrators: []` (keep key for schema uniformity across workflows per Phase 3.1 spec v2.1 §7 Q2) |

---

## Phase 3.2 — Development-loop doc prune

| File | Action |
|---|---|
| `core/.claude/agents/development-loop-master-agent.md` | Add deprecation banner + `deprecated: true` frontmatter |
| `core/.claude/skills/development-loop/SKILL.md` | FULL REWRITE — skill-at-T0 |
| `config/workflow-contracts.yaml` → `development-loop` | Empty `sub_orchestrators: []` |
| `registry/patterns.json` | Hash + deprecation fields for master agent |

---

## Phase 3.3 — Debugging-loop doc prune

| File | Action |
|---|---|
| `core/.claude/agents/debugging-loop-master-agent.md` | Add deprecation banner |
| `core/.claude/skills/debugging-loop/SKILL.md` | FULL REWRITE — skill-at-T0 |
| `config/workflow-contracts.yaml` → `debugging-loop` | Empty `sub_orchestrators: []` |
| `registry/patterns.json` | Hash + deprecation |

---

## Phase 3.4 — Code-review doc prune

| File | Action |
|---|---|
| `core/.claude/agents/code-review-master-agent.md` | Add deprecation banner |
| `core/.claude/skills/code-review-workflow/SKILL.md` | FULL REWRITE — skill-at-T0 |
| `config/workflow-contracts.yaml` → `code-review` | Empty `sub_orchestrators: []` |
| `registry/patterns.json` | Hash + deprecation |

---

## Phase 3.5 — Documentation doc prune

| File | Action |
|---|---|
| `core/.claude/agents/documentation-master-agent.md` | Add deprecation banner; body has explicit `Agent(subagent_type=…)` calls to remove/relocate |
| `core/.claude/skills/documentation-workflow/SKILL.md` | FULL REWRITE — skill-at-T0 |
| `config/workflow-contracts.yaml` → `documentation` | Empty `sub_orchestrators: []` |
| `registry/patterns.json` | Hash + deprecation |

**Halfway eval checkpoint:** after Phase 3.5 lands, confirm the skill-at-T0 pattern is holding across 5 refactors. No pattern regression in any prior phase before proceeding.

---

## Phase 3.6 — Session-continuity doc prune

| File | Action |
|---|---|
| `core/.claude/agents/session-continuity-master-agent.md` | Add deprecation banner |
| `core/.claude/skills/session-continuity/SKILL.md` | FULL REWRITE — skill-at-T0 |
| `config/workflow-contracts.yaml` → `session-save` + `session-learn` entries | Empty `sub_orchestrators: []` |
| `registry/patterns.json` | Hash + deprecation |

---

## Phase 3.7 — Learning-self-improvement doc prune

| File | Action |
|---|---|
| `core/.claude/agents/learning-self-improvement-master-agent.md` | Add deprecation banner; body references `session-summarizer-agent` + `context-reducer-agent` sub_orchestrators — flatten to direct T0 dispatches in the replacement skill |
| `core/.claude/skills/learning-self-improvement/SKILL.md` | FULL REWRITE — skill-at-T0 |
| `config/workflow-contracts.yaml` → `learning-self-improvement` | Empty `sub_orchestrators: []` |
| `registry/patterns.json` | Hash + deprecation |

---

## Phase 3.8 — Skill-authoring doc prune

| File | Action |
|---|---|
| `core/.claude/agents/skill-authoring-master-agent.md` | Add deprecation banner |
| `core/.claude/skills/skill-authoring-workflow/SKILL.md` | FULL REWRITE — skill-at-T0 |
| `config/workflow-contracts.yaml` → `skill-authoring` | Empty `sub_orchestrators: []` |
| `registry/patterns.json` | Hash + deprecation |

---

## Phase 3.9 — Standalone orchestrators + cross-cutting sweep

| File | Action |
|---|---|
| `core/.claude/agents/project-manager-agent.md` | Already has `dispatched_from: T0` (Phase 2). Add explicit "T0-only — MUST NOT be dispatched via `Agent()` from another agent/skill" guardrail in the description |
| `core/.claude/agents/parallel-worktree-orchestrator-agent.md` | Same as above |
| `core/.claude/skills/pipeline-orchestrator/SKILL.md` | Verify body is already skill-at-T0 (dispatches `project-manager-agent` from the user's session). Document explicitly |
| `docs/specs/workflow-master-agents-spec.md` | Legacy spec describing the old workflow-master pattern. Mark SUPERSEDED by the Phase 3.0 template + Phase 3.1 v2 spec; add banner pointing at `core/.claude/agents/workflow-master-template.md` v2.0.0 |
| `docs/plans/workflow-master-agents-plan.md` | Legacy plan. Mark SUPERSEDED — point at `.claude/tasks/todo.md` expanded Phase 3 plan |

### Final cross-cutting grep check (must return empty at end of Phase 3.9)

After 3.9 lands, these searches MUST all return zero hits outside of deprecated agent files + `.claude/tasks/lessons.md` (which is historical record):

```
grep -r 'testing-pipeline-master-agent' --include='*.md' core/ docs/ README.md
grep -r 'test-pipeline-agent' --include='*.md' core/ docs/ README.md
grep -r 'failure-triage-agent' --include='*.md' core/ docs/ README.md
grep -r 'e2e-conductor-agent' --include='*.md' core/ docs/ README.md
grep -r '<workflow>-master-agent' --include='*.md' core/ docs/ README.md
grep -rE 'T[0-9] (dispatches|workflow master|sub-orchestrator)' --include='*.md' \
     core/ docs/ README.md
grep -rE 'sub_orchestrators:' --include='*.yaml' config/
  # above should return only empty lists like "sub_orchestrators: []"
```

Allowed exceptions:
- `.claude/tasks/lessons.md` (historical learnings — keep)
- `docs/specs/test-pipeline-three-lane-spec.md` v1.7 (SUPERSEDED but canonical v1 reference per Phase 3.1 plan — keep)
- `docs/specs/workflow-master-agents-spec.md` (SUPERSEDED — keep)
- Deprecated agent files themselves (they are the deprecation record — keep until post-window)

---

## Summary

| Category | File count | Work type |
|---|---|---|
| Auto-regenerated | 13 | Zero manual; one `generate_*` invocation per sub-PR |
| Runtime/tracking | 4 | No PR-level intervention |
| Phase 3.1 manual edits | ~20 | Biggest batch — test pipeline + transitive worker refs |
| Phase 3.2–3.8 manual edits (each) | ~4 | Small per-sub-PR scope |
| Phase 3.9 cross-cutting | ~5 | Standalones + SUPERSEDED banners + final grep check |

**Total deprecated-reference files found in grep:** 51 (test-pipeline stack) + 30 (other workflow-masters) with significant overlap. Estimated ~60 unique non-auto-generated files touched across Phase 3 in total, spread across 9 PRs, average ~7 file edits per sub-PR.

---

## Known residual debt (NOT addressed in Phase 3)

- `docs/QA-AGENT-ECOSYSTEM-RESEARCH-2026-04-22.md` — research doc citing peer architectures (nirarad, fugazi) that assume the old tier model. Phase 3 adds a post-script; full rewrite deferred to a future research refresh.
- Auto-generated Mermaid diagrams in `docs/workflows/images/` may need pattern template updates to the Mermaid generator to reflect skill-at-T0 topology (they currently render master-agent dispatching sub-orchestrators). Tracking as a separate post-Phase-3 cleanup.
- Downstream project `.claude/` directories (via `sync_to_projects.py`) will receive the updated patterns on next sync. No checklist entry because it's automated.
