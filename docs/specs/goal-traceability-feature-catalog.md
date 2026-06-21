# Goal Traceability — Exhaustive Feature Catalog

- **Author:** Claude Code (systems architect)
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

---

## 3. Coverage matrix (proof of completeness)

| Scenario group | Covering features |
|---|---|
| S1–S8 bottom-up | F1–F7, F17, F21, F22, F25, F27, F28, F35, F44 |
| S9–S15 top-down | F9, F13–F19, F24, F26, F29–F32, F37, F45 |
| S16–S24 cross-cutting | F8, F11, F12, F20, F32–F34, F36, F39–F43, F46 |

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
