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

## 5. OUT of MVP scope (defer — do NOT build now)

Dashboard (A5); adapters — trust-score / registry / PRD (A9/A10/C10); **embed mode** (F51); the full
goal-change handler (§6 taxonomy — design only); CI presence-gate (F22); languages beyond Python +
JS/TS-regex. *(Auto-update + the proactive Goal Pulse are NO LONGER deferred — the owner's zero-manual-
effort directive makes them CORE MVP, items 3–4 above.)*

## 6. Definition of DONE (every item observable on the DEFAULT path — `output-plausibility-verification.md`)

DONE only when, dogfooded on the **hub repo itself** (`../claude-best-practices`, Python — immediate):
- **Install alone** (zero further commands) triggers a scan that builds `.atlas/` covering **every
  non-ignored Python file** with a purpose + a goal-id valid in `goals.yml` (incl. `G0`/infra) + edges
  tagged `static`/`inferred`; reports `mapped / scanned / ignored / total`.
- **Goal Pulse** auto-appears at the next session start with **no command** — per-goal status + the
  next-best-action — proving the proactive loop works hands-free.
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

## 9. Open questions

**None blocking** — every fork is resolved across §§1–8b. The 6 Round-2 🔴 items above are decided and in
scope (not open questions). 🟡/🟢 items (`correction_rate` metric, host pre-existing-traceability
integration, deterministic-under-budget, portfolio fleet view, watcher single-writer lock) are explicitly
**deferred past v0.1** and named in `atlas-ba-discovery.md` §10 — not silently dropped. If the run hits a
genuinely undecidable fork, it MUST stop and record it in `PROGRESS.md` (DONE/PENDING/BLOCKED/NEXT), not guess.
