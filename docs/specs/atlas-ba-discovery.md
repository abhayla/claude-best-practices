# Atlas — BA Discovery (full-space, pre-G1)

- **Author:** Claude Code (Business Analyst)
- **Date:** 2026-06-21
- **Status:** DISCOVERY — pending independent completeness audit before G1 (mockup)
- **Method:** `ba-discovery-checklist.md` six items + ACTORS×COMPONENTS×LIFECYCLE matrix discipline.
- **Product:** Atlas — a Claude Code plugin that gives any repo a self-maintaining, goal-anchored
  "second brain": every file traceable to a goal (bottom-up) and every goal traceable to its files +
  how they connect (top-down). Sidecar-by-default, auto-updating, zero edits to host files.

> **Goal anchor (`goal-anchored-decisions.md`):** Atlas serves Goal 1 (distribute — it ships as a
> plugin), Goal 4 (thin layer — rides the native plugin primitive), and the Goal 5 north-star
> (autonomous, self-improving machine — an agent that knows *why* every file exists and whether work
> serves a goal is more trustworthy and more autonomous). Primary value: making intent legible to the
> machine and the human at once.

---

## 1. ACTORS (the full space — not the obvious two)

| # | Actor | Human/Machine | Primary? |
|---|---|---|---|
| A1 | **AI coding agent** (Claude Code working in the repo) | Machine | **CO-PRIMARY** — Atlas is literally its second brain; the north-star is agent autonomy |
| A2 | **Developer / maintainer** (working in their own repo) | Human | **CO-PRIMARY** — "on a file, know its purpose"; "for a goal, know the files" |
| A3 | **New contributor / onboarding dev** | Human | secondary |
| A4 | **Code reviewer** (human or agent) | Both | secondary — "does this PR serve a goal? scope creep?" |
| A5 | **Project lead / PM / product owner** | Human | secondary — goal coverage, progress, bus-factor |
| A6 | **Downstream project maintainer** (adopts Atlas via plugin) | Human | secondary — Goal 1 distribution target |
| A7 | **CI / automation** (the gate) | Machine | secondary — consumes the presence-check verdict |
| A8 | **Future-self** (same dev, months later) | Human | secondary — "why does this file exist?" |
| A9 | **Auditor / compliance** (regulated downstream repos) | Human | niche — traceability evidence |
| A10 | **Trust-score / autonomous-factory** (Goal 5 engine) | Machine | niche — consumes a goal-delivery signal |
| A11 | **The hub itself** (Atlas runs on the hub as dogfood) | Machine/Human | the first adopter |

**Why A1 is co-primary and easy to miss:** the obvious framing is "a tool for developers." But the
prompt's own words — "an additional brain to the project" — and the hub's autonomy north-star make
the **agent** the heaviest user: it reads the Index on every file it touches and every goal-anchored
decision. Modeling only A2 would repeat the checklist's canonical miss (modeled 2, the space was 9).

## 2. VALUE per actor (the benefit each can't easily get elsewhere)

| Actor | Concrete value | Drop if no value? |
|---|---|---|
| A1 agent | Instant per-file intent + the goal it serves → fewer wrong edits, scope-aware changes, goal-anchored decisions grounded in real data not guesses | keep — core |
| A2 developer | "What is this file for / what breaks if I touch it" (bottom-up) + "which files deliver Goal X and how wired" (top-down), without reading the whole tree | keep — core |
| A3 onboarder | A goal-organized map of the repo in minutes vs days of code-archaeology | keep |
| A4 reviewer | Automated scope-creep / non-goal flag: "this PR advances no stated goal" | keep |
| A5 lead/PM | Goal coverage + bus-factor ("Goal 3 rests on 1 file") + progress vs success criteria | keep |
| A6 downstream | The same brain in their repo, with their own goals, one install | keep — Goal 1 |
| A7 CI | A deterministic "every file is mapped / no new orphan" gate | keep |
| A8 future-self | Mapping history: "why does this map to G3, and since when" | keep |
| A9 auditor | Exportable traceability matrix (requirement→goal→file→test) | keep (niche) |
| A10 trust-score | A `goal_delivery_confidence` signal feeding autonomy graduation | keep (niche, deferred) |
| A11 hub | Dogfood proof before distributing (the "prove it first" doctrine) | keep |

No actor is value-less → none dropped. (If one had been, the checklist says drop it.)

## 3. LIFECYCLE (the full usage/ownership horizon — not just install)

The "economic lifecycle" analog for a dev tool = the **cost/benefit stream over the repo's life with
Atlas installed**, with the maintenance burden as the recurring "cost" and legibility as the benefit.

| Stage | What happens | Cost | Benefit |
|---|---|---|---|
| L1 **Install** | plugin added; `goals.yml` scaffolded from README | near-zero (one new file) | brain available |
| L2 **Initial scan** | `/atlas scan` builds the Index (purpose+graph+proposed goals) | scan time + LLM inference cost (one-time) | full map exists |
| L3 **Confirm** | human reviews low-confidence mappings | review effort (front-loaded) | inferred → trusted |
| L4 **Daily use** | `/atlas explain`, `/atlas goal`, agent context injection | ~0 | the whole value stream |
| L5 **Auto-update** | on every change, incremental re-scan keeps the Index fresh | re-scan compute + possible Index merge-conflicts | never rots |
| L6 **Goal change** | rename/reprioritize/split/merge/add/remove a goal (see §6) | re-derivation + re-confirm of affected files | intent stays current |
| L7 **Scale / growth** | repo grows; monorepo; more languages | bigger scans; parser coverage | still complete |
| L8 **Onboard / handoff** | new dev/agent reads the map | ~0 | days→minutes |
| L9 **Uninstall** | remove plugin → repo byte-identical | none (clean) | reversible by design |

**The lifecycle miss this avoids:** treating Atlas as "install + scan" (the one-time transaction) and
ignoring L5/L6 — the *recurring* cost of keeping the Index honest as code AND goals change is where a
naive design rots. Auto-update (L5) and the goal-change handler (L6) are the load-bearing recurring
features, exactly as a TCO model must include years of operation, not just the purchase.

## 4. COMPONENT × ACTOR MATRIX (asymmetries = the value)

Components: C1 Index/store · C2 initial scan · C3 auto-update · C4 explain/query (bottom-up) ·
C5 goal-map (top-down) · C6 enforcement gate · C7 dashboard · C8 goal-change handler · C9 embed mode ·
C10 adapters (trust-score/registry/PRD). Cells: ✓benefit · ·=N/A · $=bears cost.

| Actor \ Comp | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 agent | ✓ | · | ✓ | ✓✓ | ✓ | ✓ | · | ✓ | ✓ | ✓ |
| A2 dev | ✓ | $ (scan time) | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ (opt) | · |
| A3 onboarder | · | · | · | ✓ | ✓✓ | · | ✓ | · | · | · |
| A4 reviewer | · | · | · | ✓ | ✓ | ✓✓ | · | · | · | · |
| A5 lead/PM | · | · | · | · | ✓✓ | · | ✓✓ | ✓ | · | · |
| A6 downstream | ✓ | $ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| A7 CI | · | · | ✓ | · | · | ✓✓ | · | · | · | · |
| A8 future-self | ✓ (history) | · | · | ✓ | ✓ | · | · | ✓ (history) | · | · |
| A9 auditor | ✓ | · | · | · | ✓ | ✓ | ✓ | ✓ (log) | · | ✓ |
| A10 trust-score | · | · | · | · | · | · | · | · | · | ✓✓ |

**Asymmetries (the differentiated value):**
- **C2 initial scan is a COST for A2/A6 but invisible to everyone else** → the install experience must
  minimize it (heuristic-first, async, progress-reported) or adoption stalls at L2.
- **C4 explain is the agent's (A1) heaviest-use component but only occasional for humans** → C4 must be
  callable programmatically (agent hook), not just an interactive command.
- **C6 gate benefits CI/reviewer (A4/A7) but is friction for the committing dev (A2)** → gate presence
  only (binary), keep categorization advisory, or A2 disables it (enforcement-fatigue).
- **C7 dashboard is high-value for lead/PM (A5) and near-useless for the agent (A1)** → don't gate the
  agent path on dashboard generation.
- **C10 adapters matter only to A6/A9/A10** → must be opt-in, off by default, so the core stays light.

## 5. VARIANTS / AXES (what changes the answer)

- **Repo size:** small / large / monorepo → scan cost + incremental strategy.
- **Language mix:** single vs polyglot → C2/graph parser coverage (the hard edge case).
- **Index persistence:** committed vs regenerated-in-CI → staleness vs merge-conflict trade.
- **Mapping confidence:** inferred vs human-confirmed → what the gate/dashboard may trust.
- **Mode:** sidecar (default) vs embed (opt-in) → does the file self-describe.
- **Host:** hub vs downstream → own goal taxonomy each; no cross-coupling.
- **Goals source:** README-derivable vs thin → scaffold vs TODO stub.
- **Goal stability:** static vs frequently-changing taxonomy → §6 weight.

## 6. GOAL CHANGE over the lifecycle (the owner's explicit question — L6 detail)

Goals are **not** static; Atlas treats the goal taxonomy as **versioned** (`goals.yml` carries
`version` + a changelog; every change is dated with a reason — feature F12). **Goal IDs are stable
handles**: display labels may change without touching mappings; structural changes use
deprecate-and-redirect, never silent ID reuse. Six mutation types:

| Mutation | Example | What Atlas does | Cost |
|---|---|---|---|
| **Rename** | "G3 label → 'Idea→Deploy'" (ID `G3` unchanged) | relabel only; all file→`G3` mappings untouched; dashboards re-title | trivial |
| **Reprioritize** | priority order G3 ↑ above G2 | no remapping; decisions re-anchor; dashboard re-sorts | trivial |
| **Re-scope / redefine** | `G3` keeps ID but its *meaning* shifts | **flag every file mapped to G3 as stale-confidence** → incremental re-derive + re-confirm | medium |
| **Split** | `G3 → G3a + G3b` | propose reassignment of each G3 file to one/both children (human confirms); deprecate `G3` with redirect; keep history | medium-high |
| **Merge** | `G2 + G3 → G2` | files mapped to either now map to merged ID (mechanical); preserve original-mapping history | low-medium |
| **Add** | new `G6` | no existing files affected; `G6` starts as an **orphan goal** (0 files) surfaced in the coverage report until populated | trivial |
| **Remove / retire** | drop `G4` | files mapped **only** to G4 become orphaned → flagged for re-anchor; never silently deleted; mapping kept in history as "served retired G4" | medium |

**Cross-cutting goal-change machinery (so multiple changes over the lifecycle stay sane):**
- **Impact preview before apply (F37):** "G3 split affects 47 files — review reassignment" — the
  blast radius is shown before the change commits, never discovered after.
- **Mapping history per file (F34/C1):** every file's goal-mapping is time-stamped, so "why does this
  map to G3, and since when" is answerable across every prior taxonomy version.
- **Confidence reset:** redefine/split/merge resets affected mappings to *inferred-unconfirmed* until a
  human re-confirms — a goal change never silently leaves a now-wrong mapping marked "confirmed."
- **Decision/ADR re-anchor:** `goal-anchored-decisions.md` records referencing a changed goal get
  flagged for review (the decision's anchor moved).
- **Downstream isolation:** the hub changing *its* goals does not touch any downstream project — each
  owns its own `goals.yml` and its own change lifecycle.

> **Net answer to "what happens when the goal changes, multiple times":** because IDs are stable and
> the taxonomy is versioned with history, repeated changes accumulate as an auditable trail rather than
> corrupting the map. Only *redefine/split/merge/remove* touch existing mappings — and each triggers a
> bounded re-derive + human re-confirm of just the affected files, with an impact preview first.

## 7. AHA OUTPUTS (the high-value insights the tool surfaces)

- **Orphan file** — "this file serves no goal" → delete-candidate or a missing goal.
- **Bus-factor goal** — "Goal 3 is delivered by only 1 file" → single point of failure.
- **Scope-creep PR** — "this change advances no stated goal / touches a non-goal."
- **Goal home** — "these 12 files all serve G3 and cluster in `scripts/deploy/`" → the goal's center.
- **Orphan goal** — "G6 has 0 files" → an unstarted/aspirational goal.
- **Onboarding map** — vision → goals → modules → files, navigable in minutes.
- **Coverage trend** — Goal X's file-set growing or shrinking across releases.
- **Connection map (Constellation)** — not just *which* files serve a goal but *how they call each other* to deliver it.

## 8. Open discovery questions (must be empty/answered before G1)
- Index commit-vs-regenerate (edge case #1 in the catalog) — a design decision, not a discovery gap.
- Multi-language parser coverage depth (edge case #4) — scope decision for MVP.
- Primary-actor confirmation: is the **agent (A1)** or the **developer (A2)** the lead persona for the
  first mockup? (Recommended: design the bottom-up `explain` for BOTH, dashboard for A5 later.)

---

## 9. Independent completeness audit — result + resolutions (2026-06-21)

A fresh-context auditor (`independent-test-verification.md` pattern) audited §§1–8 and returned
**BLOCKS-G1** with 5 blocking dissents (D1–D5) + 6 weaknesses (W1–W6). All blockers are resolved below;
the discovery is now G1-ready. Resolutions are authoritative additions to the sections they amend.

### D1 (resolved) — A12: the cost/privacy/budget owner
**MISSING actor:** every A1–A11 *consumes* value; none *bears* the confidentiality + spend risk of the
LLM scan. Add **A12 — Repo owner / security-and-budget authority** (human, **veto power**): decides
whether proprietary file contents may be sent to an inference endpoint, and owns the per-token bill.
- **Value/anti-value (§2):** Atlas must give A12 a *control surface* (local-inference option, scan
  allow/deny scope, a hard budget cap) or A12 vetoes adoption. This is the #1 adoption-killer.
- **Matrix (§4):** A12 bears `$$` on C2 (scan) and C3 (auto-update); benefits from C6/C7 (oversight).

### D2 (resolved) — confidently-wrong inference is a first-class failure mode
The map is LLM-**inferred**; §7's AHAs are *acted on*. A wrong inference turns "orphan file →
delete-candidate" into "delete a load-bearing file" and "scope-creep → block PR" into blocking a
legitimate change. **Resolution (binds §7 + adds a §5 axis):**
- **Every AHA output is ADVISORY, shows its confidence, and is reversible** — never an auto-action.
  "Orphan file" = *review candidate*, never auto-delete; "scope-creep" = a *flag*, never a hard block.
- The **G1 mockup MUST render confidence + a "this may be inferred / confirm-or-correct" affordance** —
  not a clean verdict. (This changes the design, which is why it blocked G1.)
- New §5 axis: **mapping trust state** (inferred · confirmed · stale).

### D3 (resolved) — L10: Atlas self-upgrade / Index schema migration
The Index is a **committed** artifact (edge #1), so when Atlas itself ships a new version with a changed
`.atlas/` schema, **every adopter's Index must migrate at once** — a Goal-1 distribution risk. Add
lifecycle **L10 "Atlas self-upgrade / Index migration"**: versioned Index schema + a migration step on
plugin upgrade; a failed migration degrades to "rebuild from scratch," never corrupts.

### D4 (resolved) — L11: Index recovery + git history-rewrite
Add lifecycle **L11 "Index recovery / resync"**: `/atlas rebuild --from-scratch`; the Index is
**advisory**, so a corrupt/partial/stale Index **degrades gracefully** (Atlas falls back to "unknown"
for affected files) rather than crashing. **git rebase / history-rewrite:** Index entries key off
*content hashes*, not SHAs, so a rewrite re-matches by content on next scan; entries that no longer
match are marked stale, not deleted. New §5 axis: **Index trust state** (valid · stale · corrupt).

### D5 (resolved) — explicit cost model + budget cap
"One-time scan" / "re-scan compute" is quantified, not hand-waved:
- **Heuristic-first:** path/name/docstring/imports classify the majority with **zero** LLM calls; LLM
  fires only on low-confidence files → the per-token bill scales with *ambiguous* files, not *all* files.
- **Hard budget cap (A12-owned knob):** a configurable ceiling; on reaching it Atlas stops LLM
  derivation and logs "N files left heuristic-only" (no silent overspend, no silent truncation).
- **Recurring (L5) cost** is bounded by incremental hash-diff — only *changed* files re-derive.

### Weaknesses folded in
- **W1 — 7th goal mutation: RE-PARENT.** The taxonomy is a tree (F9), so moving a sub-goal under a
  different parent is a distinct mutation: file→goal mappings untouched, but every roll-up (coverage,
  dashboard aggregation, parent-level bus-factor) recomputes. Added to §6.
- **W2 — concurrent goal changes:** `goals.yml` is the **human-owned SSOT**; concurrent edits resolve
  last-writer-wins with changelog reconciliation (the goals-level analog of the Index merge rule).
- **W3 — day-one degraded mode:** with only a TODO-stub taxonomy, every file infers to "no goal," so the
  orphan-file AHA would fire on *everything*. Atlas **suppresses goal-dependent AHAs until the taxonomy
  is real** (≥1 confirmed goal with ≥1 mapping) — first-run is never a wall of false orphans.
- **W4 — matrix fix:** A2/A5 now carry `$` under C8 (goal-change re-confirm effort).
- **W5 — G1 scope fence:** C10 adapters (A9 auditor, A10 trust-score) are explicitly **OUT of the G1
  mockup**; the first design covers the bottom-up `explain` + top-down `goal` for A1/A2 only.
- **W6 — variant axis:** **host without inference** (air-gapped / CI-only / non-CC IDE) → Atlas degrades
  to heuristics-only (lower confidence everywhere). Added to §5.

### Audit verdict after resolutions
D1–D5 addressed in §§1–7 above; W1–W6 folded. **Discovery is G1-ready.** Primary-actor recommendation
stands: design the bottom-up `explain` for BOTH A1 (agent) and A2 (developer); dashboard (A5) and
adapters (A9/A10) are post-G1.
