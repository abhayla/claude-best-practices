# Goal Contract — Atlas MVP (v0.1)

> **For:** Claude Code's built-in `/goal` autonomous executor, run in a fresh session.
> **Authored by:** `/goal-creator` (interview-first; every fork below is resolved — the run never pauses to ask).
> **Tracked from:** the hub design session (this repo's `docs/specs/atlas-*`).
> **Status:** DRAFT — awaiting the owner's "requirements final" approval before execution.

---

## 0. Product home (READ FIRST — `product-incubation.md`)

Atlas is a **product** (a deployable Claude Code plugin), NOT a hub pattern. Build it in an
**isolated sibling repo**: `../atlas/` with its **own `.git`**, OUTSIDE the hub tree. MUST NOT add
Atlas code to the `claude-best-practices` repo. The hub keeps only the design docs (the spec
sources below). Incubate small; graduate to its own remote per `product-incubation.md` when a
trigger trips.

## 1. Goal (one sentence)

Build the Atlas MVP: a Claude Code plugin that, installed into ANY repo, builds a **sidecar Index**
mapping every source file to its **purpose**, the **goal** it serves, and its **dependency edges** —
queryable bottom-up (`/atlas explain <file>`) and top-down (`/atlas goal <Gn>`) — **without editing
any existing file** in the host repo.

## 2. Spec sources (the run MUST read these first — they are the design SSOT)

All in the hub at `D:/Abhay/VibeCoding/claude-best-practices/docs/specs/`:
- `goal-traceability-spec.md` — the original approach + enforcement model.
- `goal-traceability-feature-catalog.md` — all 53 features (F-ids), sidecar verification, **12 edge
  cases**, the Embedded-vs-Sidecar decision, the install/scan design.
- `atlas-ba-discovery.md` — actors, value, lifecycle, **goal-change taxonomy (§6)**, audit resolutions
  (A12 cost/privacy actor, D2 confident-wrong-inference, D5 cost model).
- `atlas-g1-mockups.md` — the **G1-APPROVED layout: Variant B (Sectioned)** for `/atlas explain`.

## 3. Locked decisions (do NOT re-litigate)

- **Architecture:** sidecar-by-default — the Index lives in `./.atlas/`, host files are never edited.
- **Index persistence:** **committed** to the host repo, **per-file-sharded**, deterministically
  ordered (an LLM-inferred + human-confirmed map cannot be regenerated reproducibly — it MUST persist).
- **Parser:** **Python-first** real dependency-edge parser; JS/TS second; **regex + LLM fallback** for
  the long tail (marked lower-confidence).
- **Primary actors:** the **AI agent** and the **developer** (co-primary); design the bottom-up
  `explain` for both — programmatic output for the agent, the Variant B render for the human.
- **Inference is advisory (audit D2):** every goal mapping is `inferred` until a human confirms;
  Atlas NEVER auto-acts on an inferred value (no auto-delete, no hard PR block).
- **Cost (audit D5):** heuristic-first (path/name/docstring/imports classify the majority with ZERO
  LLM calls); LLM only on low-confidence files; a configurable **hard budget cap** — on hit, stop LLM
  derivation and log "N files left heuristic-only" (no silent overspend).

## 4. MVP scope — MUST build (DoD verbs are load-bearing)

1. **Plugin skeleton** (`.claude-plugin/`) installable into any repo; install creates ONLY `.atlas/`
   + a scaffolded `goals.yml`; **zero edits to existing host files**.
2. **`goals.yml` scaffolder** — generate the goal vocabulary from the host's `README` (Goals 1–N);
   if README is thin, write a TODO-stub and SUPPRESS goal-dependent outputs until ≥1 goal is real.
3. **Autonomous scan (ZERO manual effort — owner directive 2026-06-21).** The scan runs **automatically
   on install** and **re-runs on every change via a bundled hook** — the user NEVER types `/atlas scan`.
   Pipeline: WALK (gitignore-aware + `.atlasignore`, skip binary/vendored) → CLASSIFY → DERIVE purpose
   (heuristic-first; LLM on low-confidence, secret-gated, budget-capped) → GRAPH (Python edges; regex
   fallback) → ANCHOR (propose a goal per file, `inferred`; `G0`/infra allowed) → PERSIST (sharded
   `.atlas/` Index, content-hash per file) → run is **incremental** (hash-diff). `/atlas scan` still
   exists as a manual override but is never *required*.
4. **Proactive Goal Pulse (the core value — owner directive).** A bundled **SessionStart hook** auto-
   surfaces, with no command: per-goal status (on-track / drifting / orphan-goal), what the user is
   currently working on + which goal it serves, and the **next best action** to advance a goal. Atlas
   talks to the user; the user never has to ask. This is the always-reminding loop that ties every
   change back to the project's goal.
5. **`/atlas explain <file>`** — render the **G1-approved Variant B layout** with REAL data: WHAT, GOAL
   (confidence bar), HELPS, WIRING (→ calls / ← used by, each edge tagged `static`/`inferred` + a
   "graph may be incomplete" marker). The `[c]onfirm/[e]dit` affordance is an **optional** one-tap
   inline override — never a required step.
6. **`/atlas goal <Gn>`** — list files mapped to a goal with `●/◐` confidence markers + a bus-factor flag.
7. **Passive/optional confirmation (NOT a gate).** Confirmation is never required and never blocks. It
   accrues **passively** from normal work (the agent/user works on a file under a goal and doesn't
   correct it → soft signal) and via the optional one-tap inline `correct`. Inference is **advisory and
   never destructive** (no auto-delete, no hard-block) — so running on unconfirmed guesses is safe;
   reminders self-improve over time.
8. **Uninstall contract** — removing the plugin + deleting `.atlas/` + `goals.yml` leaves the repo
   **byte-identical**.

## 4c. STEERING CONTROL LOOP — PROMOTED TO CORE (owner directive 2026-06-21)

A re-audit found the MVP was SENSE-only (a map + a passive reminder) — missing the back half that makes
Atlas *steer*. Per the owner's "autonomous goal-steering" vision, the following move from deferred/catalog
INTO the MVP. Atlas without these is a monitor, not a controller.

9. **N1 — Rich goal model (the keystone).** `goals.yml` per-goal gains a machine-checkable
   **Definition-of-Done** (acceptance criteria / a measurable completion signal), priority, and status —
   not just a title. Promotes catalog **F10**. Everything below depends on this denominator.
10. **N2 — Goal % done + gap.** Compute each goal's completion vs its DoD (N1) and the remaining-work delta.
11. **N3 — Prioritization engine.** A defined scoring function ranks candidate next-actions by marginal
    goal-advancement (inputs: goal priority × gap-size × bus-factor × blast-radius). "Next best action"
    (item 4) becomes COMPUTED + ranked, not templated.
12. **N4 — Task-feed to the executor.** Atlas emits a structured next-task queue (`.atlas/next.json` or a
    `/goal`-consumable contract) that the agent / build loop PULLS from + injects goal+intent at
    SubagentStart/file-open. Promotes catalog **F21**. This is the "steer the *processes*" actuator.
13. **N6 — Convergence ledger.** Append-only per-goal %-done time-series → velocity + trend + ETA
    ("G3 +5%/wk, ETA 3wk"; "G2 stalled 0% in 14d"). Promotes catalog **F34**. The capability that *defines*
    steering.
14. **N7 — Work→goal attribution (close the loop).** On commit/PR/merge, attribute the change to a goal and
    auto-advance that goal's %-done in the ledger (N6). Promotes catalog **F32** from tag→credit. Without
    this the loop never closes.

## 4d. Atlas-Intelligence enhancements S1–S10 (owner-approved 2026-06-21)

The owner approved all 10 strategic suggestions. **S1 is promoted to MVP-CORE** (it upgrades N1/N2/N7
from *estimated* to *measured*). **S2–S10 form a named v0.2 "Atlas-Intelligence" tier** — incorporated
into the design (not deferred-and-forgotten), scheduled after the steering MVP proves out.

15. **S1 — Machine-checkable Definition-of-Done (CORE).** Each goal's DoD in `goals.yml` may be an
    *executable assertion* (a named test passes / a file exists / a command exits 0 / an endpoint 200s).
    Atlas evaluates these → **% done is MEASURED from reality, not inferred** (N2/N7 read real signals).
    DoD with no machine-check falls back to the inferred estimate. *Strengthens the keystone (N1).*

| ID | v0.2 feature | Strengthens | Note |
|---|---|---|---|
| S2 | **Goal dependency graph** — goals depend on goals (meta-Constellation); unblock-first ordering | ④ prioritize | "can't advance G3 until G1 ≥ X%" |
| S3 | **Active learning from corrections** — every `correct` retrains inference; `correction_rate`→signal | ① sense | self-improving accuracy |
| S4 | **Anti-goals / guardrails** — constraints as negative goals (security, perf budget, no-new-deps) | ⑥ drift | flag *violations*, not just neglect |
| S5 | **Confidence decay** — inferred mappings lose confidence over time until re-touched | ①⑩ | stale guesses self-flag |
| S6 | **Owner stall-alerts via Notifier** — goal-stall/drift → the hub's Notifier gateway, off-session | ⑦ converge | proactive when away |
| S7 | **Natural-language goal Q&A** — "what's left for G3 / riskiest file / what next?" | ⑨ query | human-steerer interface |
| S8 | **Goal-aware review + commit rationale** — PR annotates goal-delta; auto goal-tagged commits | ⑥⑧ | steers the review process |
| S9 | **Test→goal safety map** — which tests protect which goal; high-%-no-tests = fragile | ③ gap | surfaces *unsafe* progress |
| S10 | **Hub-machinery integration** — feed convergence into trust-score (`goal_delivery_confidence`) + PM agent | ⑧ close-loop | Atlas = goal-sensor for the autonomous factory (Goal-5) |

### v0.3 "Atlas-Foresight" tier — S11–S22 (owner-approved 2026-06-21; roadmap, not MVP)

| ID | Feature | Strengthens |
|---|---|---|
| S11 | **Project "Definition of Done" / north-star bar** — aggregate all goals into ONE top-level completion signal | ⑦ converge |
| S12 | **Auto-goal-discovery** — detect emergent goals from commit/file clusters not yet in `goals.yml` | ② goal-model |
| S13 | **Pre-edit blast-radius preview** — before a file changes, show which goals it touches + risk | ⑥ drift |
| S14 | **Drift root-cause diagnosis** — when a goal stalls, diagnose *why* + suggest the unblock | ⑥⑦ |
| S15 | **Goal ↔ issue-tracker sync** — bidirectional goals ↔ GitHub milestones/issues | ⑧ close-loop |
| S16 | **Goal health score** — composite per goal (coverage × test-safety × velocity × confidence) | ③ gap |
| S17 | **Effort × Impact backlog view** — plot ranked next-actions on an effort/impact quadrant | ④ prioritize |
| S18 | **Reusable goal templates** — standard DoD templates (deploy / coverage / security goals) | ② goal-model |
| S19 | **Goal ownership / RACI** — who owns each goal; routes stall-alerts | ⑤ steer |
| S20 | **What-if simulation** — projected convergence if you focus on goal X next | ④⑦ |
| S21 | **Rotting-goal alarm** — goals untouched N days auto-surface | ⑥ drift |
| S22 | **Goal-grouped release notes** — auto-changelog grouped by goal advanced (from N7 data) | ⑧ |

> **Scope guard (YAGNI):** S2–S22 are a *roadmap*, deliberately NOT in the v0.1 MVP. The MVP remains the
> steering loop (N1–N7) + S1 (machine-checkable DoD). Build that, prove it on the hub dogfood, then pull
> from this roadmap by real demand — do not expand v0.1 to chase the roadmap.

## 5. OUT of MVP scope (defer — do NOT build now)

**embed mode** (F51); the full goal-change handler (§6 taxonomy — design only); CI presence-gate (F22);
languages beyond Python + JS/TS-regex; **N5** real-time drift-interrupt hook, **N8** graduated
steering-action policy, **N9** goal-health dashboard (A5/F30), **N10** trust-score `goal_delivery_confidence`
(F33) — these are the *next* steering tier (v0.2), named not silently dropped.
*(NO LONGER deferred — promoted to CORE: auto-update + Goal Pulse (zero-manual-effort directive, items 3–4),
and the steering control loop N1–N7 (items 9–14) per the autonomous-goal-steering directive.)*

## 6. Definition of DONE (every item observable on the DEFAULT path — `output-plausibility-verification.md`)

DONE only when, dogfooded on the **hub repo itself** (`../claude-best-practices`, Python — immediate):
- **Install alone** (zero further commands) triggers a scan that builds `.atlas/` covering **every
  non-ignored Python file** with a purpose + a goal-id valid in `goals.yml` (incl. `G0`/infra) + edges
  tagged `static`/`inferred`; reports `mapped / scanned / ignored / total`.
- **Goal Pulse** auto-appears at the next session start with **no command** — per-goal status + the
  next-best-action — proving the proactive loop works hands-free.
- **Steering loop closes (N1–N7):** each goal in `goals.yml` has a Definition-of-Done; Atlas reports a
  **% done** per goal (not just coverage); the **next-best-action is RANKED** by the scoring function (not
  templated); a **`.atlas/next.json` task-queue** is emitted and an agent dispatch consumes ≥1 task from
  it; and after a commit that advances a goal, that goal's **% done moves in the convergence ledger** (a
  before/after delta is observable). If any of these can't be shown on the hub dogfood, the steering MVP
  is NOT done.
- `/atlas explain scripts/recommend.py` renders the **Variant B layout** with that file's real
  purpose, an `inferred` G1 goal + confidence bar, and its real `calls`/`used by` edges.
- `/atlas goal G1` lists ≥1 file, each with a confidence marker.
- `/atlas confirm scripts/recommend.py` flips that mapping to `confirmed` and persists it; re-running
  `explain` shows `● confirmed`.
- **Zero host files modified** by install/scan (verify `git status` shows only `.atlas/` + `goals.yml`);
  uninstall restores byte-identity.
- **Plausibility:** no file is rendered with an absurd goal (e.g., a test file mapped to "deploy");
  spot-check 5 files by hand.
- **Tests green** (TDD — written first): unit tests for WALK/CLASSIFY/DERIVE/GRAPH + the 3 commands;
  the suite passes; coverage on new code ≥80%.

## 7. Execution discipline (the run MUST honor)

- **Isolation:** work in `../atlas/` (own git); commit per sub-task as a checkpoint.
- **Plan-first + root-cause** (`plan-before-coding.md`): plan before the first edit; fix root causes.
- **Verify, don't claim** (`supervisor-verification.md`, `independent-test-verification.md`): reproduce
  every gate; an independent pass confirms the DoD before "done" — the builder is never the sole verifier.
- **Permission mode:** launch with `--permission-mode auto` (autonomous-run policy, `decision-authority.md`).
- **Secrets:** the scanner reads file contents — heuristic-first, secret-scan-gated; never send a file
  flagged by secret-scan to an LLM (`security-baseline.md`).

## 8. Approval gates (`human-approval-gates.md`)

- **G1 (design)** — ALREADY APPROVED: `/atlas explain` = Variant B (2026-06-21).
- **G2 (feature acceptance)** — after the DoD is met + independently verified, present the working
  `scan`/`explain`/`goal` on the hub repo for the owner's sign-off BEFORE declaring v0.1 done.
- **G3 (deploy/publish)** — not in MVP (no marketplace publish yet).

## 8b. Round-2 audit additions (2026-06-21) — MUST be built; resolve the 6 🔴 before "done"

A second adversarial audit (`atlas-ba-discovery.md` §10) found 6 build-blockers. These are now **in
MVP scope** (they are correctness/trust holes on the default path, not nice-to-haves):

- **`G0`/infra goal:** `goals.yml` MUST include a first-class `G0` (infra/build/test/config) entry.
  ANCHOR assigns `G0` to goal-less tooling files; `G0` files are NOT orphans and NOT plausibility-absurd.
  (Resolves the DoD ↔ "every file gets a valid Gn" vs plausibility contradiction.)
- **Graph partiality:** every Constellation edge is tagged `static` | `inferred`; `explain`/`goal` render
  a "graph may be incomplete" marker; bus-factor/blast-radius carry a partiality caveat. The graph is
  advisory like goals (D2) — never rendered as bare fact.
- **Confirmation safety:** move-detection uses git rename-detection first (survives rename-with-edit); a
  shard conflict resolves `confirmed`-wins (`/atlas resolve`); a `confirm` records actor + date; the agent
  trusts `confirmed` only when the Index is committed (advisory in a dirty tree).
- **Agent freshness:** each Index entry stamps the file's content-hash so `explain` SHOWS staleness; the
  agent calls `/atlas refresh <file>` after writing it.
- **Honest coverage:** REPORT `mapped / scanned / ignored / total` (never a single gameable %).
- **Windows-safe scan:** normalize + detect case-insensitive path collisions; don't follow symlinks; skip
  submodules. (The dogfood host is this Windows repo — exercised on run 1.)
- **D3 — Index schema versioning + migrate-on-upgrade (resolved BA blocker, restored):** `.atlas/` carries a
  schema version; when Atlas upgrades and the schema changes, a migration runs; a failed migration degrades
  to `rebuild --from-scratch`, never corrupts. (The Index is a committed artifact → a schema bump is a
  breaking change across every adopter; this MUST ship.)
- **D4 — Index recovery / resync (resolved BA blocker, restored):** `/atlas rebuild --from-scratch`; the Index
  is **advisory**, so a corrupt/partial/stale Index degrades gracefully (affected files read "unknown") rather
  than crashing; entries key off content-hash so a git history-rewrite re-matches by content, stale entries
  flagged not deleted.
- **F25 orphan-FILE detection (restored):** the Goal Pulse + coverage surface files that serve **no** goal
  (delete/review candidates) — not just orphan-*goals*. Advisory, never auto-deleted.
- **F26 scope-creep flag (restored, batch form):** the Goal Pulse "drifting" status flags a change that
  advances no stated goal / a non-priority goal. (The *real-time* interrupt is N5, v0.2.)

## 5b. Disposition of every remaining catalog feature (no silent drops — owner traceability check 2026-06-21)

A coverage audit found these were neither in-scope nor named-deferred. Each is now classified — nothing is
silently dropped:

| Feature | Disposition | Reason |
|---|---|---|
| F5 multi-goal | **CORE (lite)** | the Index maps a file to a goal **list**; *primary-designation + weighting* → v0.2 |
| F25 orphan-file · F26 scope-creep · F29 coverage-gaps | **CORE** | folded into Goal Pulse + coverage (§8b above) |
| F7 directory `_purpose` | **DEFER v0.2** | per-file mapping suffices for v0.1 |
| F9 goal decomposition (sub-goal/capability tree) | **DEFER v0.2** | MVP goal model is **flat** (goal + DoD via N1); hierarchy is a recorded v0.2 choice |
| F11 README↔goals drift guard | **DEFER v0.2** | scaffold-from-README is core; the drift guard is v0.2 |
| F19 goal-scoped search/filter | **DEFER v0.2** | `/atlas goal <Gn>` covers the core need |
| F23 sync gate · F28 new-file authoring gate | **DEFER v0.2** | companions to the CI presence-gate (F22), already deferred |
| F31 traceability-matrix export | **DEFER v0.2** | A9-auditor tier, ships with the adapters |
| F36 last-reviewed dates / re-review triggers | **DEFER v0.2** | content-hash staleness (§8b) covers the core staleness need |
| F13 registry mirror (`patterns.json` gains `goals`) | **SUPERSEDED** | the sidecar `.atlas/` Index IS the map; the hub-registry mirror was the pre-plugin model (F47 replaced it) |
| G-R7 cold-start "confirm-N-to-be-useful" | **DEFER v0.2 (named)** | documented as expected cold-start behavior; no MVP work |

## 9. Open questions

**None blocking** — every fork is resolved across §§1–8b. The 6 Round-2 🔴 items above are decided and in
scope (not open questions). 🟡/🟢 items (`correction_rate` metric, host pre-existing-traceability
integration, deterministic-under-budget, portfolio fleet view, watcher single-writer lock) are explicitly
**deferred past v0.1** and named in `atlas-ba-discovery.md` §10 — not silently dropped. If the run hits a
genuinely undecidable fork, it MUST stop and record it in `PROGRESS.md` (DONE/PENDING/BLOCKED/NEXT), not guess.
