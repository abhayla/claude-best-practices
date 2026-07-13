# Fable failure archaeology — 2026-07-13 (Harvest Session B, Phase 1+2 record)

**What this is:** the discovery + fork-resolution record of Fable-harvest Session B
(`plans/fable-harvest-window.md` §Session B). Phase 1 mined the hub's full failure record via
three parallel research agents; Phase 2 clustered the ~24 raw findings into 9 failure classes and
resolved the four authoring forks with the owner (interview 2026-07-13). Phase 3 (skill authoring)
executes from this document — any model can continue from here.

**Sources mined (all read 2026-07-13):**
- Hub git history: reverts, fix-the-fix chains, churn hotspots (top-30), abandoned branches, CI-fix commits
- `.claude/tasks/lessons.md` (~40 dated entries, 2026-04-22→2026-07-13), `.remember/` history,
  telemetry logs (`.enhance-misses.log` 430 entries / `.overask-violations.log` 578 / `.verifier-misses.log` 45),
  `docs/governance/fable-rule-stack-audit-2026-07-13.md`, `trust-score/ledgers/atlas.jsonl` (75 runs, 23 `human_had_to_fix`)
- Downstream issue/PR history (live `gh` reads): IPODhan, AlgoChanakya, KKB, RealFuelPricesinIndia, calculatekaro

---

## The 9 failure classes

| # | Class | Key evidence (real citations) | Coverage today | Session B action |
|---|---|---|---|---|
| A | **Effect-never-landed** — wiring passes syntax/CI but the consumer never receives the effect | SubagentStop arc `8398aaa`→`9b58cb9`→`330282c` ("governance theater"); G6 pilot same-day revert `d967def`→`437af4c`; ≥4 plugin version-bump misses before CI gate #349; hook `additionalContext` silently dropped (lesson 2026-07-10) | Version-bump CI-gated; general discipline = Manual prose only | **Author 2 hub-only skills** |
| B | **Shape-vs-substance verification** — checks assert *something renders/passes*, not that it's real | IPODhan #94/#96/#97/#98 (mock data in prod, self-named "shape-vs-substance miss"); lessons 2026-06-17/19 "RECURRENCE" (red PR by skipping full pytest); 45 verifier-miss telemetry entries | Rules exist (supervisor-verification), violated anyway; nothing downstream | **Author 1 core skill + auto-verify upgrade** |
| C | **Partial-fix under-coverage** — fix covers the common case, siblings survive | IPODhan #101→#81 (fix exposed same root cause from new angle); #74→#72/#73 (explicit residuals); KKB #90→#93 (4-PR mockk chain); eval findings N1–N15/F1–F11 post-ship | None (residual-filing is ad-hoc) | **Author 2 core skills** |
| D | **Hook/turn-type detection fragility** — enforcement mis-reads transcript shapes/turn origins | ~13-commit enhance-guard fix chain (#106→#348); 430+578 telemetry misses; audit C5/C6; BA-gate misfired twice on THIS session's machine notifications | Rule rewrite owner-gated (queue #13); the *testing discipline* is only a lesson | **Author 1 hub-only skill** (fixture-testing only; skip the rewrite) |
| E | **Silent test debt** — full suite never runs until a migration forces it | IPODhan #108/#109 (42 failing) + AlgoChanakya #89 (~60 collection errors), both surfaced same day by pipeline install | None | **test-pipeline upgrade** (baseline-on-install) |
| F | **Duplicate-issue filing** — pipeline re-files an already-treated root cause | KKB #51→#60 (same conftest override, same 4 tests, two issues) | None in `/create-github-issue` | **create-github-issue upgrade** (dedup step) |
| G | **Dual-copy/derived drift** (hub↔core, registry↔docs) | `registry/patterns.json` 103 touches; fix commits `519bbc6`/`d9e6a93`/`c769b1e`; gate #171 | Gated: `test_dual_home_sync.py`, README count guard, 4-step SOP | **Skip** (owner-confirmed) |
| H | **Git lifecycle edges** (squash-merge "looks unmerged", stale branches, concurrency) | `9a7610a` (#223) + 6-test suite; ~7 lesson incidents, each closed; 2 stale branches found+pruned this session | Gated: reconcile hook, reaper, landing tests | **Skip** (owner-confirmed) |
| I | **Rule-vs-rule contradiction** (claude-behavior.md vs decision-authority SSOT) | Audit C1–C11; C1/C2/C9 are the rules class-D's hook must override every firing | Owner-gated = queue #13 | **Skip** (owner-confirmed) |

**Meta-finding:** no reverts of business/script logic were found — the hub's failure mass concentrates
in *self-referential governance tooling* (hooks governing Claude's own behavior). The dominant classes
(A, D) share one root: **building against an assumed platform/transcript shape instead of a captured
real one, and claiming done without probing the consumer end.**

Trust-ledger note: the 23 `human_had_to_fix=true` runs are a branch-prefix proxy (all `fix/*`/`chore/*`
branches, mechanically flagged) — corroborating context, not independent evidence. Feeds G5 milestone M1a.

---

## Phase 2 — owner interview resolution (4 forks, answered 2026-07-13)

1. **Audience:** split — downstream-facing classes (B, C, E, F) → distributable `core/`;
   hub-governance classes (A, D) → hub-only `.claude/skills/`, promotable later.
2. **Overlap:** skip I, G, H and class D's rule-rewrite side (queue #13 / already gated);
   keep D's untreated testing discipline as one skill.
3. **Fix in place:** E, F, and B's pipeline-side land as UPGRADES to existing workflow skills
   (test-pipeline, create-github-issue, auto-verify), version-bumped so they propagate.
   Standalone skills only for classes with no existing home.
4. **Volume:** quality-first ~8–12; every candidate needs ≥2 evidenced incidents; count is an
   output, not a quota. Landing = one PR per class-cluster (prior owner directive).

## Phase 3 — authoring plan (9 candidates)

Standalone skills (each through `/writing-skills` + `/skill-evaluator`, one at a time):

| Skill | Class | Home | Core content |
|---|---|---|---|
| `verify-effect-at-destination` | A | hub-only | After wiring any hook/config/integration: probe the CONSUMER end (injected context, delivered message, written row, served version) before claiming done; "accepted ≠ delivered ≠ done" as an executable checklist |
| `platform-event-live-probe` | A | hub-only | BEFORE building on a platform event/API surface: live-verify the payload actually arrives where you'll consume it (the SubagentStop lesson); a documented event name is not delivery |
| `hook-transcript-fixture-test` | D | hub-only | Any hook parsing transcripts/turn state ships with fixture tests against CAPTURED REAL transcript samples (the shapes memory: slash = TWO entries, mid-turn text may not persist); never assume the shape |
| `full-defect-surface-sweep` | C | core/ | After root-causing a bug: enumerate ALL sibling instances repo-wide before closing; fix or file explicit residual issues (IPODhan #72/#73 pattern); a fix without a surface sweep is a partial fix |
| `dependency-migration-triage` | C | core/ | When a dep bump/removal surfaces test failures: classify each (framework quirk masked vs latent real bug), work classes not instances (KKB 4-PR chain) |
| `mock-data-hunter` | B | core/ | Pre-ship sweep for hardcoded/demo/seed data on prod paths (grep fabricated constants, seeded rows, future dates, "For MVP" comments); substance beats shape |

Workflow upgrades (version-bumped; plugin propagation via /plugin-lifecycle):

| Target | Class | Upgrade |
|---|---|---|
| `test-pipeline` (core + cbp-build-test-workflows) | E | STEP: on first install/run in a repo, run the FULL suite and baseline pre-existing failures as issues BEFORE any new work is judged against it |
| `create-github-issue` (cbp-build-test-workflows closure) | F | STEP: search open+closed issues for the same root cause before filing; link recurrence (a reopened root cause is a finding) instead of duplicating |
| `auto-verify` (core + cbp-build-test-workflows) | B | Substance-assertion guidance: prod verification must assert real data joined to source-of-truth rows, never render-shape only; "verified" = the project's full gate |

Authoring order: A-class skills first (highest window value), then D, then C, then B standalone,
then the three workflow upgrades (most mechanical). Each cluster lands as its own CI-gated PR.
