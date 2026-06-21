# Atlas — Goal Traceability Feature Catalog

> **Product name: `Atlas`** (renamed from Lodestar, 2026-06-21) — the project's goal-navigation
> "second brain": keeps every file traceable to the north-star goals. **On-disk store: `.atlas/`**;
> the persisted knowledge graph inside it is **the Index** (file → purpose → goal → connections),
> not a flat database; the dependency-graph view is the **Constellation**. Commands: `/atlas scan`,
> `/atlas explain <file>`, `/atlas goal <Gn>`, `/atlas map`. Delivered as a **Claude Code plugin**,
> **sidecar-by-default** (zero edits to host files), **auto-maintaining**, drop-in to any repo incl.
> the hub. Full BA discovery: `atlas-ba-discovery.md`.

- **Author:** Claude Code (systems / product architect)
- **Date:** 2026-06-21
- **Status:** DISCOVERY (companion to `goal-traceability-spec.md` — unfiltered feature list, not yet MVP-scoped)
- **Method:** features are *derived from scenarios* — every scenario must have a covering feature; every feature must trace to a scenario. This is completeness-by-construction, not a brainstorm dump.

This catalog answers: "to make every file know the goal it serves (bottom-up) AND to know
which files achieve a goal and how they connect (top-down), what is the COMPLETE set of
features?" It is deliberately unfiltered. Tiering into MVP/later happens in the spec.

---

## 1. Scenarios the system must answer (the questions, both frames)

### Bottom-up — standing on a file
- **S1** What is this file *for*? (purpose)
- **S2** Which goal(s) does it serve, and *how does it help*?
- **S3** If I break/delete it, which goal suffers? (downward impact)
- **S4** What does it depend on, and what depends on it? (the *connections*)
- **S5** Is its declared purpose still *accurate* vs the code? (drift)
- **S6** Does it serve *any* goal — or is it orphaned / dead / speculative?
- **S7** I just created/edited it — what must I *declare*? (authoring gate)
- **S8** I'm an agent told to edit it — what *intent* must I preserve?

### Top-down — standing on a goal
- **S9** To achieve Goal X, which files/modules are *involved*?
- **S10** How do those files *connect/collaborate* to deliver it? (wiring, not just the set)
- **S11** How well is Goal X *covered* — gaps, thin spots, single points of failure?
- **S12** What's the *status/progress* of Goal X vs its success criteria?
- **S13** If I reprioritize/cut/add a goal, what's the *blast radius*? (upward impact)
- **S14** Which files serve *no goal* or a *non-goal*? (waste / scope creep)
- **S15** Which goal does this *PR/feature/change* advance? (justify the work)

### Cross-cutting / lifecycle
- **S16** Onboarding — a new human/agent needs the whole map (vision→goals→modules→files).
- **S17** The taxonomy must stay in sync with README/charter (SSOT integrity).
- **S18** Goals *evolve* — versioning, history, re-review triggers.
- **S19** Downstream projects need the same, with *their own* goals.
- **S20** Reporting/audit/provenance — show how work mapped to goals over time.
- **S21** Multi-goal files — primary + secondary + weighting.
- **S22** Directory/module-level purpose, not just leaf files.
- **S23** Decisions tie to goals (already: `goal-anchored-decisions.md`).
- **S24** Requirement→goal→file traceability for the idea→deploy pipeline.

### Delivery model (added 2026-06-21 from owner suggestions)
- **S25** Drop into *any* repo (new or existing, incl. the hub) with one install — no per-project wiring.
- **S26** Install **without editing the host's existing files** and without adding runtime deps (zero-touch).
- **S27** Stay current **automatically** — re-derive on change; never a manual re-annotation chore.
- **S28** Survive as an **independent module** — versioned/tested/adopted on its own, decoupled from host internals.

---

## 2. Feature catalog (9 layers)

Direction tags: **↑** bottom-up · **↓** top-down · **↔** both.

### A. Declaration layer — make each file self-describing (↑)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F1 | `goals:` frontmatter on every pattern (valid taxonomy IDs) | S2,S7 |
| F2 | Purpose/`description` one-liner ("what is this file") | S1 |
| F3 | Optional `contribution` line ("how it helps the goal") — kept optional so it doesn't rot | S2 |
| F4 | Non-frontmatter coverage: scripts (module docstring), configs/fixtures/generated (sidecar/registry) | S1,S6 |
| F5 | Multi-goal + primary designation + optional weighting | S21 |
| F6 | Non-goal / infra tagging (serves goals indirectly; not flagged as orphan) | S6,S14 |
| F7 | Directory/module-level declaration (`_purpose` per significant folder) | S22 |

### B. The goal model — the taxonomy SSOT (↔)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F8 | Goal vocabulary SSOT (`config/goals.yml`, G1–G5) | S17 |
| F9 | Goal decomposition: Goal → sub-goal → capability (Backstage-style) | S9,S10,S24 |
| F10 | Goal metadata: owner, status, priority, success criteria, non-goals, last-reviewed | S12,S14 |
| F11 | Goal↔README drift guard (titles must match) | S17 |
| F12 | Goal versioning/changelog + re-review triggers | S18 |

### C. The link/graph layer — connective tissue (↔)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F13 | Registry mirror (`patterns.json` gains `goals`) — queryable index | S9 |
| F14 | Traceability graph: goal→module→file→test **+ dependency edges** | S4,S10 |
| F15 | Bidirectional resolver (one engine: file→goals AND goal→files) | S2,S9 |
| F16 | Relationship enrichment: real import/call edges so the graph shows collaboration | S4,S10 |

### D. Query & navigation — the "I want to know" UX (↔)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F17 | "What is this file for?" command → purpose + goals + how-it-helps + callers/callees | S1,S2,S4 |
| F18 | "Show everything serving Goal X" → listing + module tree | S9,S10 |
| F19 | Goal-scoped search/filter | S9 |
| F20 | Onboarding map ("repo organized by goal") for new human/agent | S16 |
| F21 | Agent context injection (SubagentStart/file-open → file's goal + intent) | S8 |

### E. Enforcement & gates — keep it honest (↔)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F22 | CI presence-gate (valid goal link required; fails PR) — binary invariant | S6,S7 |
| F23 | Sync gate (frontmatter ↔ registry ↔ README) | S17 |
| F24 | Orphan-goal detection (goals with no files) | S11 |
| F25 | Orphan-file / dead-code detection (files with no goal) | S6,S14 |
| F26 | Scope-creep / non-goal-violation check (change serving no/anti goal) | S14,S15 |
| F27 | Staleness/drift detection (LLM-assisted purpose-vs-code compare) | S5 |
| F28 | New-file authoring gate (no declaration → warn/block) | S7 |

### F. Reporting & observability — top-down visibility (↓)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F29 | Goal-coverage report in `generate_docs.py` (distribution, gaps, thin goals) | S11 |
| F30 | Goal-health dashboard (HTML, like trust dashboard) — count, coverage, progress vs criteria | S11,S12 |
| F31 | Traceability-matrix view (goal→capability→file→test) | S10,S24 |
| F32 | Provenance tagging (`[G3]` in commits/PRs/changelog) | S15,S20 |
| F33 | Trust-score integration: `goal_delivery_confidence` signal | S12,S20 |
| F34 | Trend-over-time (coverage growing/shrinking across releases) | S20 |

### G. Lifecycle & maintenance — keep it from rotting (↔)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F35 | Backfill helper (propose `goals:` per existing file for human confirm) | S7 |
| F36 | Last-reviewed dates + re-review triggers on goals & high-level docs | S5,S18 |
| F37 | Goal-change propagation (reprioritize/cut → flag/orphan affected files; impact preview) | S13,S18 |
| F38 | Migration/grandfather strategy (incremental gate + tracked backfill) | S7 |

### H. Downstream distribution — hub → projects (↔)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F39 | Distributable `goals.yml` template + convention in `core/.claude/` | S19 |
| F40 | Provision-time scaffold (starter goals + CLAUDE.md pointer from project vision) | S19 |
| F41 | Per-project taxonomy ownership + dual-home classification (`shared`) | S19 |
| F42 | Downstream self-audit (validator ships so projects gate themselves) | S19 |

### I. Integration with existing governance — don't reinvent (↔)
| ID | Feature | Scenarios |
|----|---------|-----------|
| F43 | CLAUDE.md "Vision & Goals" pointer section (anchor + index) | S16 |
| F44 | `goal-anchored-decisions.md` ties decisions→goals (reuse as-is) | S23 |
| F45 | Workflow-contract goal field (each of 9 workflows declares its goal) | S9,S15 |
| F46 | PRD/BA → goal → file thread (requirement carries goal; files inherit) | S24 |

### J. Delivery model — packaged, zero-touch, self-maintaining (↔) — added 2026-06-21
| ID | Feature | Scenarios |
|----|---------|-----------|
| F47 | Packaged as a **Claude Code plugin** (native primitive: `.claude-plugin/`, marketplace) — drop-in to any repo incl. hub | S25 |
| F48 | **Sidecar store** (`.atlas/` — the Index — or plugin data) — map/graph/assignments live OUTSIDE host files; zero edits, zero added deps | S26 |
| F49 | **Auto-derivation + auto-refresh** — infer purpose + graph + proposed goal on install and on change (hook/CI/watcher) | S27 |
| F50 | **Human-confirm/override layer** over inferred goal assignments (confirmed > inferred; inference never hard-gates CI) | S27 |
| F51 | **Opt-in embed mode** — a command writes an in-file pointer when a team WANTS file-visible declaration; OFF by default | S1,S26 |
| F52 | **Layered architecture: standalone core + optional adapters** that activate only when present (registry, trust-score, workflow-contracts, PRD) — preserves independence while keeping deep integration | S28 |
| F53 | **Goal-vocabulary scaffolder** — generates a starter `goals.yml` from README/prompt (the one near-dependency), so install stays near-zero-touch | S25,S19 |

---

## ARCHITECTURAL DECISION — Embedded vs Sidecar (the load-bearing fork)

The owner's "no dependency / no edits to existing files" (S26) **conflicts** with the bottom-up
requirement "standing on a file, instantly know its purpose" (S1) when taken literally — because the
strongest way a file announces its own purpose is *in-file* text, which means editing the file.

| | Embedded (in-file `goals:`) | Sidecar (external store) |
|---|---|---|
| Touches host files | Yes — violates S26 | **No** ✓ |
| File self-describes without the plugin | **Yes** ✓ | No — file is *mute* if plugin removed |
| Rot-resistance | High (visible on edit) | Depends fully on F49 auto-update |
| Goal assignment | Human-declared | Inferred → confirmed (F50) |

**Decision: Sidecar-by-default + opt-in embed (F48 + F51).** Bottom-up "what is this file for?" is
answered by a **command/hover (F17)**, not in-file text — the same way an IDE surfaces symbol info a
file never states. Accepted cost: **remove the plugin and the file goes mute again**, and goal
assignment is *inferred-then-confirmed* rather than declared. This is the right trade for portability
(S25–S28); teams that reject "mute without plugin" turn on F51 embed.

This decision **supersedes** the spec's `core/.claude/` distribution approach (old F39–F42): the CC
plugin (F47) is the cleaner native vehicle and serves Goal 1 (distribute) + Goal 4 (ride the platform).

---

## SIDECAR COVERAGE VERIFICATION (all 53 features) — 2026-06-21

Recommendation: **sidecar-by-default + opt-in embed.** All 53 features are covered. Breakdown:

| Class | Features | Note |
|---|---|---|
| Covered as-is | F8–F12, F14–F21, F24–F37, F47–F53 | read/write the Atlas; never needed in-file text |
| Mechanism shifts (file → Atlas) | **F1, F2, F3, F13, F22, F23** | same capability, declaration lives in the Atlas; embed (F51) restores in-file form |
| Sidecar *improves* | **F4** (uniform coverage of ALL file types), **F38** (mega-PR migration vanishes — scan just builds the Atlas) | — |
| Opt-in edit if wanted literal | **F43** (CLAUDE.md pointer), **F45** (workflow-contract field), **F46** (PRD field) | become opt-in adapters under zero-touch |

**F22 semantics change (noted):** the CI gate shifts from "did a human write frontmatter?" to "is any
file unmapped/unconfirmed in the Atlas?" — a better gate, but not the same gate.

## EDGE CASES — must-nail list (red-team pass)

🔴 = load-bearing design decision; 🟡 = important; 🟢 = handle-but-minor.

1. 🔴 **Atlas committed vs regenerated** — commit → staleness + merge conflicts; regenerate → must be
   deterministic. Lean: commit a deterministically-ordered, **per-file-sharded** Atlas (rare conflicts, reviewable diffs).
2. 🔴 **Scan scope** — gitignore-aware + skip vendored/build/binary via `.atlasignore`, else coverage lies.
3. 🔴 **Secrets/privacy** — scanner reads file contents; LLM derivation can leak secrets → heuristic-first, secret-gated, local-inference option.
4. 🔴 **Multi-language dependency edges (F16)** — pluggable per-language extractors + LLM fallback. Hardest piece.
5. 🟡 **Rename/move/delete reconciliation** — content-hash per entry → detect moves, not delete+add.
6. 🟡 **Scale/monorepo** — incremental hash-diff re-scan, parallelism, capped with honest "N deferred" logging.
7. 🟡 **Inference cost/quality** — heuristic-first; LLM only on low-confidence files.
8. 🟡 **Trend/history (F34)** — read git log of the Atlas or periodic snapshots.
9. 🟢 **`goals.yml` near-dependency** — scaffold from README; TODO stub if thin (never fail).
10. 🟢 **CLAUDE.md pointer (F43) is an edit** — keep opt-in; default surfaces via command.
11. 🟢 **Confidence display** — inferred vs confirmed visibly distinct everywhere.
12. 🟢 **Uninstall contract** — repo byte-identical after removing `.atlas/` + `goals.yml`.

## INSTALL / BOOTSTRAP SCAN (existing-project onboarding)

`/atlas scan` — runs on install, then incrementally on every change:

```
1. WALK      enumerate files; gitignore-aware; apply .atlasignore; skip binaries/vendored
2. CLASSIFY  code / config / doc / test / asset → derivation strategy per type
3. DERIVE    purpose per file: heuristic-first (path, name, docstring, imports, README);
             LLM only for low-confidence (secret-gated)
4. GRAPH     parse import/call edges per language → build the Constellation (dependency graph)
5. ANCHOR    load/scaffold goals.yml → propose a goal per file  [inferred · unconfirmed]
6. PERSIST   write the Atlas, with a content-hash per file (drift + rename tracking)
7. REPORT    coverage %, low-confidence/unmapped list for human confirm
8. WATCH     wire plugin hook + CI for incremental re-scan on change
```

Safety invariant: the scan **only ever writes the Atlas** — host files are read, never modified.

---

## 3. Coverage matrix (proof of completeness)

| Scenario group | Covering features |
|---|---|
| S1–S8 bottom-up | F1–F7, F17, F21, F22, F25, F27, F28, F35, F44, F51 |
| S9–S15 top-down | F9, F13–F19, F24, F26, F29–F32, F37, F45 |
| S16–S24 cross-cutting | F8, F11, F12, F20, F32–F34, F36, F39–F43, F46 |
| S25–S28 delivery model | F47–F53 |

Every scenario maps to ≥1 feature; every feature maps to ≥1 scenario. No gaps, no orphans.

## 4. The non-obvious gap vs spec v0.1
The spec's flat `goals: [G3]` answers "which goal" (S2,S9) but **not** "how are the files
*connected* to deliver the goal" (S4,S10). That requires the **graph + real dependency edges
(F14/F16)** and the **capability decomposition (F9)** — the difference between a *list* of files
and a *map* of how they collaborate. This is the single biggest capability the spec must absorb.

## 5. Cost-of-truth note (read before scoping)
Features split sharply by maintenance cost:
- **Cheap & durable** (declare once, machine-validated): F1,F2,F8,F11,F13,F22,F23,F29,F43 — the
  backbone. These survive because CI keeps them honest.
- **High-value, moderate cost**: F14,F16,F17,F18,F30,F35,F40 — the graph + query UX + dashboard.
  Worth it; this is what makes the system *useful* rather than merely *compliant*.
- **Powerful but rot-prone / debatable** (must stay ADVISORY, never hard-gate): F3,F26,F27,F33,F37
  — purpose prose, "is this the right goal", drift detection, delivery confidence. Hard-gating any
  of these is the documented enforcement-fatigue failure mode.

Scoping (MVP vs later) is decided in `goal-traceability-spec.md`, not here.
