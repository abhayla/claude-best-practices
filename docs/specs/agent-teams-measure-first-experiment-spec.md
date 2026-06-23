# Spec: Agent-Teams Measure-First Experiment

> **Status:** DRAFT (brainstorm output, 2026-06-23). Discussion/spec only — NOT an
> implementation. Running the experiment is spend-gated and owner-triggered.
> **Source discussion:** `/brainstorm` session 2026-06-23. **Companion:** the team-readiness
> tracker in `plans/agent-teams-incorporation.md` §12.

## 1. Problem statement

The hub has built the *scaffolding* for agent teams (the `agent-team-selection` rule + 3
`team-*` governance hooks) and validated that a team *forms* via `claude --bg`. But **no
agent team has reliably completed a real task here** — every run so far was a throwaway
read-only analysis. Before investing in the §12 tracker (making ~13 SAFE-FIT + ~4 RISKY-FIT
resources team-ready), we must prove teams are worth it. Building that scaffolding on an
unvalidated bet would violate the hub's own doctrine ("don't build for autonomy — prove the
trust score first").

## 2. Chosen approach (converged in brainstorm)

| Decision | Value | Why |
|---|---|---|
| End-goal | **C — Measure-first** | Prove measured value on one concrete experiment before investing further |
| Win condition | **D > B** | Primary: a team **reliably completes a real task end-to-end**. Secondary: it does so with **cost-bounded quality** |
| Experiment shape | **A — Staged** | Stage 1 (read-only, cheap) de-risks the *mechanism* before Stage 2 bets on the risky parallel-edit path |
| Reliability bar | **≥ 2 of 3 runs complete end-to-end, no rescue** | Repeatable, not a one-off fluke (proposed default) |

Rejected: going straight to the parallel-edit build (B) — highest chance of an unreliable
first run; read-only-only (C) — doesn't prove a team can *build*.

## 3. Design — the two stages

### Stage 1 — Mechanism proof (read-only, SAFE-FIT)
- **Task (ASSUMPTION):** a **team code-review of a real recent PR** — spawn reviewers
  (security / correctness / tests lenses) who share + challenge findings; lead synthesizes.
  Strongest SAFE-FIT, Anthropic's flagship team use case, **zero merge risk**.
- **Pass:** ≥2/3 runs complete end-to-end with no rescue; all 3 governance hooks fire clean
  (honest audit log, no errors); a usable synthesized review is produced.
- **Purpose:** prove the team + hooks *mechanism* is reliable before any file edits.

### Stage 2 — Real build (RISKY-FIT, parallel edits)
- **Task:** the team builds the **small TODO web app** end-to-end (frontend / backend API /
  tests — a clean 3-way file partition), in an **isolated sibling folder** (`../todo-team-test/`,
  own `.git`, outside the hub — per `product-incubation`).
- **Pass:** ≥2/3 runs complete end-to-end, no rescue; the app runs and its tests pass;
  **no unresolved merge collisions** between teammates' files.
- **Purpose:** the true D test — can a team *reliably build a real thing* on the parallel-edit path.

### Gating
Stage 1 PASS → run Stage 2. Stage 2 PASS → invest in the §12 tracker (SAFE-FIT cluster first).
Any stage FAIL → stop, record why; do **not** invest in tracker work on an unproven mechanism.

## 3a. Optionality — agent teams is fully optional for BOTH hub and downstream (Must)

Agent teams MUST be a **default-OFF, fully optional** capability, controlled at two
independent layers, symmetric for the hub and downstream projects:

| Layer | Controls | Mechanism | Default |
|---|---|---|---|
| **Provisioning** | Whether a project *receives* the resources | Agent-team patterns (`agent-team-selection` rule, `team-*` hooks, future team skills) = a **tagged optional bundle**; `synthesize-project` / `recommend.py` offer it as an opt-in selection. Unselected → files never copied. | Not auto-included |
| **Activation — platform** | Whether teams *form* | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Without it, no team forms; all team resources are inert. | OFF |
| **Activation — workflow** | Whether the *default path* uses teams | Team-variant workflows are opt-in per call (`--team`) or a project config flag; default stays flat-subagent even with the platform flag on. | Non-team |

**Invariant:** when off (the default), there is **zero token cost, zero merge risk, zero
hook firing** — the project behaves exactly as if agent teams did not exist. Same opt-out
pattern as the hub's existing `AUTO_MERGE=0` / pluggable `SECRET_SCAN_CMD`.

**Hub symmetry:** the hub keeps the resources in `.claude/`/`core/` but teams are off unless
a hub session opts in — identical control to downstream. The hub can dogfood teams or not.

This reinforces measure-first: off everywhere by default until the experiment proves value,
then any project (or the hub) flips it on.

## 4. What we measure (per run → calibration note / trust-score ledger)
- **Reliability (D, primary):** completed end-to-end? rescues needed? hook errors?
- **Cost (B, secondary):** total tokens vs. a flat-subagent/single-context baseline on the same task.
- **Quality delta (B, secondary):** did peer-challenge surface anything the baseline missed?
- **Coordination failures:** teammates not receiving messages, tasks not marked complete, merge collisions.

## 5. Requirement tiers (MoSCoW)
**Must**
- Staged execution with the Stage-1→Stage-2 gate.
- The ≥2/3 no-rescue reliability bar applied per stage.
- Per-run measurement of reliability + token cost vs. a baseline.
- Stage 2 runs in an isolated sibling folder (never the hub tree).
- **Optionality (§3a):** agent teams ships as a default-OFF, fully optional capability for
  BOTH hub and downstream, controllable at the provisioning + activation layers; "off" is a
  zero-cost / zero-behavior-change invariant.

**Nice**
- Quality-delta capture (did the team beat the baseline?).
- Trust-score-ledger integration for the calibration data.
- A baseline run with flat subagents for an apples-to-apples cost comparison.

**Out of scope**
- Making any §12 resource team-ready (that's *after* the experiment passes).
- Wiring the hooks into the hub's own settings.json beyond the experiment harness.
- Any interactive-terminal-only flow (the experiment uses `claude --bg`, which forms teams).

## 6. Open questions (proposed defaults in brackets — owner to confirm/correct)
- **Stage-1 task:** team code-review of a real PR [assumed] — or a five-advisors-style debate, or a research task?
- **Reliability bar:** ≥2/3 no rescue [proposed] — or stricter (3/3) / looser (1/1 proof-of-mechanism)?
- **Token budget ceiling** per stage [to propose] — the experiment is spend-gated; owner triggers the runs.
- **Baseline comparison:** run a flat-subagent baseline for cost delta (Nice), or skip for v1?
- **Toggle granularity (§3a):** is the platform env var enough as the activation master, or
  add a hub/project config flag (e.g. `agent_teams: enabled`) on top? [proposed: env var as
  master + per-call `--team` opt-in; a config flag is a Nice add]
- **Provisioning default:** ship the resources to all downstream as inert-but-present, or
  only when opted in at provision time? [proposed: opt-in to receive AND off-by-default once received]

## 7. Success criteria (the bet pays off if…)
- **Stage 1 passes** → the team+hooks mechanism is reliable (D satisfied for read-only).
- **Stage 2 passes** → a team can reliably build a real thing end-to-end (D satisfied for builds).
- **Then** the §12 SAFE-FIT cluster becomes worth building; if either stage fails, teams stay a
  manual ad-hoc tool and the tracker work is shelved with the failure recorded.

## 8. Handoff
Next step when the owner chooses to proceed: convert this to a runnable plan via
`/writing-plans`, or trigger Stage 1 directly (spend-gated). No implementation until then.
