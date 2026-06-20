# Goal Contract — The Autonomous Software-Development Machine

**Type:** Strategic north-star goal contract (not a `/goal` execution run)
**Status:** Active · Crawl phase (shadow mode)
**Created:** 2026-06-20
**Owner:** Abhay Kumar
**Anchors:** `core/.claude/rules/goal-anchored-decisions.md` · README goals 1–4 · `config/trust-score.yml`
**Supersedes:** nothing — this is the apex goal that the existing four README goals feed into.

---

## 1. North-star (one sentence)

> Build a **self-improving software-development machine** that takes an idea to a
> production-deployed, verified app **with minimal human intervention** — continuously
> absorbing the latest Claude Code platform features, the best patterns/repos surfaced on
> GitHub, and relevant new technology — where autonomy is **earned through a proven trust
> score**, never assumed.

Motto (inherited from the trust-score engine): **don't build for autonomy — prove the trust score first.**

## 2. Why now

- The hub already ships the four capabilities this goal composes: a pattern library (Goal 1),
  reusable workflows (Goal 2), an idea→production-deployed lifecycle (Goal 3), and a
  platform-migration loop that keeps the hub a thin layer on the latest Claude Code (Goal 4).
- The **trust-score engine** (`scripts/trust_score.py`, PR #163) already exists as the
  crawl-phase MVP — the safety mechanism that makes graduating to autonomy measurable rather
  than aspirational.
- What is missing is a **written charter** that names the machine as a single goal so every
  decision can be anchored to it (`goal-anchored-decisions.md` requires the goal to be
  documented, not implied). This contract is that charter.

## 3. What the machine IS

A closed loop with three **intake streams** feeding one **autonomous build pipeline**, gated by trust:

```
  ┌─ Intake (what to absorb) ───────────────┐
  │ A. Latest Claude Code / Anthropic        │      ┌─ Autonomous pipeline (per Goal 3) ─┐
  │    platform features  → /cc-adoption-scout│      │ BA → UX(approve) → build → test →   │
  │ B. Best repos/patterns on GitHub          │ ───▶ │ independent-verify → QA → deploy    │
  │    → /self-improve, /github               │      └────────────┬───────────────────────┘
  │ C. Relevant new technology / libraries    │                   │ each stage emits signals
  └───────────────────────────────────────────┘                   ▼
                                                    ┌─ Trust score (config/trust-score.yml) ─┐
                                                    │ weighted 0–100 · hard gates · shadow   │
                                                    │ mode · irreversible-stage escalation   │
                                                    │ → AUTO (earned) or ESCALATE (human)    │
                                                    └─────────────────────────────────────────┘
```

The machine is the **synthesis** of the existing goals — not a new silo:

| Existing goal | Role in the machine |
|---|---|
| 1 — Distribute patterns | The reusable building blocks the pipeline assembles from. |
| 2 — Reusable workflows | The orchestrated steps (test / debug / review / docs) each run executes. |
| 3 — Idea → deployed app | The pipeline body the machine drives end-to-end. |
| 4 — Thin layer on latest platform | Intake stream **A** — the machine rides new Claude Code primitives instead of reimplementing them. |

## 4. In-scope capabilities

- **Continuous adoption intake** — periodically scout new Claude Code releases, high-signal
  GitHub repos/patterns, and notable new tech; classify each as ADOPT / KEEP-hand-rolled /
  REJECT / MEASURE-FIRST (the existing `/cc-adoption-scout` doctrine) and file migration work.
- **Autonomous pipeline execution** — run the Goal-3 lifecycle with the right engineering role
  owning each stage, capturing learnings every stage (`/learning-self-improvement`).
- **Trust-gated decisioning** — every run produces a trust score; reversible/internal stages may
  earn AUTO once calibrated; irreversible stages (deploy/spend/DNS) escalate in the crawl phase.
- **Self-calibration** — record each run + the human's ground-truth ("did you have to fix it?")
  to the calibration ledger; report the false-confidence rate that gates leaving shadow mode.
- **Fold-back** — improvements discovered while building flow back into the hub as patterns
  (the synthesize flywheel), so the machine gets stronger each cycle.

## 5. Explicit NON-goals (YAGNI guardrails)

- **NOT** removing the human from irreversible decisions — deploy/spend/DNS stay human-gated
  until calibration proves otherwise, and product-fork / strategy calls are always human.
- **NOT** flipping `shadow_mode: false` before the calibration target is met (see §6).
- **NOT** adopting a platform feature, repo, or technology because it is new/shiny — every
  intake item must pass the goal-anchored test (does it serve this goal + the user?).
- **NOT** reimplementing what Claude Code ships natively (Goal 4 holds — retire, don't maintain).
- **NOT** building speculative autonomy infrastructure ahead of a calibrated need to crawl→walk→run.

## 6. Success criteria & exit gates (measurable)

Grounded in `config/trust-score.yml` — these are the numbers, not vibes:

- **Trust threshold:** a run scores **≥ 85 / 100** to be *recommended* for AUTO; below → ESCALATE.
- **Hard gates (never out-voted by a good average):** `tests_pass = 1.0` and
  `secret_scan_clean = 1.0` — any breach forces ESCALATE regardless of score.
- **Keystone signal:** `independent_verification` (a verifier that is **not** the doer) is
  weighted 0.25 — the machine never self-certifies.
- **Calibration exit (the gate to leave shadow mode):** ≥ **30** shadow-mode runs **and**
  false-confidence rate **≤ 5%** (`calibration.min_runs: 30`, `max_false_confidence_rate: 0.05`)
  before *any* stage graduates out of shadow mode.

The goal is **met** when a reversible/internal idea→deploy run completes start-to-finish at
AUTO (human only approves the design + the production deploy) with the calibration target
sustained — i.e. the trust score has been *earned*, in production, not green-locally.

## 7. Phased roadmap (crawl → walk → run)

| Phase | Trust posture | What the machine does | Human's role |
|---|---|---|---|
| **Crawl** (now) | `shadow_mode: true` — engine recommends, human acts on every stage. | Build the calibration ledger to ≥30 runs; prove the score honest. | Acts on every recommendation; records ground-truth. |
| **Walk** | Reversible/internal stages earn AUTO once calibrated; irreversible stages still escalate. | Auto-runs build/test/verify/docs; pauses at deploy/spend/DNS. | Approves design + irreversible stages only. |
| **Run** | Irreversible stages earn AUTO under sustained calibration. | Drives idea→deployed end-to-end; surfaces exceptions. | Sets direction, handles exceptions, owns strategy. |

Each graduation is **earned per-stage** by calibration evidence — never a global flag flip.

## 8. Guardrails (hard stops)

- **Shadow mode is the default** until §6's calibration gate is met; flipping it is a human decision.
- **Independent verification is mandatory** — the doer never certifies its own work.
- **Irreversible actions escalate** in crawl/walk regardless of score (`irreversible_stages`).
- **No synthetic/fake signals** — surface uncertainty as `**Assumption:** X`; a fabricated
  pass is worse than an honest escalation.
- **Human-approval gates** before build and before deploy persist (Goal 3 contract).

## 9. How decisions trace back to this goal

Per `goal-anchored-decisions.md`, every non-trivial build/defer/cut call on the machine MUST
name this goal + the user impact explicitly. Tie-breaks favor: (1) correctness/safety of the
generated software, then (2) raising the trust score's honesty, then (3) breadth of autonomy.
Feature-completeness or "the matrix has a hole" are not reasons to build.

## 10. Open questions (resolve as the machine matures)

- What cadence drives the adoption intake (on-release, weekly, on-demand) and who owns its spend?
- Does the calibration ledger need per-stage sub-scores before any single stage can graduate?
- What is the minimum production-health observation window before a deployed run counts as "verified"?

## References (load transitively)

- `config/trust-score.yml`, `scripts/trust_score.py` — the trust engine + calibration.
- README goals 1–4 — the capabilities this goal composes.
- `core/.claude/rules/goal-anchored-decisions.md` — how this goal becomes the decision anchor.
- `plans/idea-to-deploy-readiness.md` — the Goal-3 lifecycle the pipeline drives.
- `plans/platform-migration-2026H2.md` — Goal-4 intake stream A.
- `.claude/skills/cc-adoption-scout` · `.claude/skills/self-improve` — intake streams A/B.
