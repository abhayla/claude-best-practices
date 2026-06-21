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
3. **`/atlas scan`** — WALK (gitignore-aware + `.atlasignore`, skip binary/vendored) → CLASSIFY →
   DERIVE purpose (heuristic-first; LLM on low-confidence, secret-gated, budget-capped) → GRAPH
   (Python dependency edges; regex fallback else) → ANCHOR (propose a goal per file, `inferred`) →
   PERSIST (write the sharded `.atlas/` Index with a content-hash per file) → REPORT (coverage % +
   unconfirmed count). Re-running is **incremental** (hash-diff; only changed files re-derive).
4. **`/atlas explain <file>`** — render the **G1-approved Variant B layout** with REAL data: WHAT,
   GOAL (with a confidence bar + `inferred·unconfirmed`), HELPS, WIRING (→ calls / ← used by), and
   the `[c]onfirm [e]dit [m]ap` affordance.
5. **`/atlas goal <Gn>`** — list files mapped to a goal with `●/◐` confidence markers + a bus-factor
   flag when one file carries a disproportionate share of the goal's edges.
6. **`/atlas confirm <file>` / `/atlas correct <file> <Gn>`** — the human-confirm layer; confirmed
   beats inferred; confirmation is recorded in the Index (with a date).
7. **Uninstall contract** — removing the plugin + deleting `.atlas/` + `goals.yml` leaves the repo
   **byte-identical**.

## 5. OUT of MVP scope (defer — do NOT build now)

Dashboard (A5); adapters — trust-score / registry / PRD (A9/A10/C10); **embed mode** (F51); the full
goal-change handler (§6 taxonomy — design only); CI presence-gate (F22); languages beyond Python +
JS/TS-regex; auto-update hook (manual `/atlas scan` is acceptable for v0.1).

## 6. Definition of DONE (every item observable on the DEFAULT path — `output-plausibility-verification.md`)

DONE only when, dogfooded on the **hub repo itself** (`../claude-best-practices`, Python — immediate):
- `/atlas scan` builds `.atlas/` covering **every non-ignored Python file** with a purpose + a
  proposed goal-id valid in `goals.yml` + ≥0 dependency edges; prints coverage % and unconfirmed N.
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

## 9. Open questions

**None.** Every fork is resolved above. If the run hits a genuinely undecidable fork, it MUST stop and
record it in a `PROGRESS.md` under DONE/PENDING/BLOCKED/NEXT, not guess.
