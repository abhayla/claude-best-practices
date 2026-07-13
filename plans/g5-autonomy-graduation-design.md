# G5 Autonomy Graduation — design: how shadow mode earns the right to act

**Status:** DESIGN (owner-approved to write, 2026-07-13). Activating any level beyond L1 is a
separate, explicit owner decision — this document defines the ladder and the evidence bars; it
does not switch anything on.

**Owner:** Abhay. **Author:** Claude Fable 5 (Fable-reserve task, session 2026-07-13).

**Motto (unchanged):** don't build for autonomy — prove the trust score first.

---

## 1. The honest starting state (2026-07-13, from the live ledger)

`trust-score/ledgers/atlas.jsonl`, 68 real runs (all shadow-mode; every effective decision was
human):

| Stage | Runs | AUTO recs | False-confidence (AUTO ∧ human_had_to_fix) | Over-caution (ESCALATE ∧ no fix needed) |
|---|---|---|---|---|
| build | 12 | 12 | 0 (0%) | — |
| reversible | 56 | 9 | 8 (**89%**) | 32/47 (**68%**) |

Calibration bar for graduation: ≥30 runs AND false-confidence ≤5% (`config/trust-score.yml`).

**Reading this honestly:**
- The G5 DoD's run-count proxy (≥30 ledger runs) is MET; the *real* bar is nowhere near met.
- `build` looks clean but is under-sampled (12 < 30) — no conclusion yet.
- `reversible` is miscalibrated in BOTH directions, which is a **measurement problem before it
  is a trust problem**: 47/56 runs score exactly 60 (signals defaulting rather than measuring),
  and the 89% false-confidence rate on 9 AUTOs almost certainly includes proxy noise —
  `human_had_to_fix` is derived from follow-up commits on the branch/PR, and a follow-up commit
  is not always a human correcting the machine (it is often the machine's own next step).
- Conclusion: **the bottleneck is calibration fidelity, not run volume.** Milestone 1 below is
  therefore data-quality work, and no stage can graduate on today's labels.

## 2. Design principles (carried forward, not renegotiable per-run)

1. **Hard gates are never out-voted** — a perfect weighted score cannot override a failed
   `tests_pass`/`secret_scan_clean` floor (existing `hard_gates`).
2. **Irreversible never auto** — `deploy`, `spend`, `dns` stay human-gated at every level of
   this design. Removing a stage from `irreversible_stages` is an owner-only config change.
3. **Graduation is per stage, and it is itself reversible** — de-graduation is automatic and
   instant on evidence (below), never a debate.
4. **Every autonomy level has a kill switch, an audit trail, and an owner notification path**
   (the shared Notifier gateway; see §6).
5. **The score never grades its own homework** — the keystone signal stays
   `independent_verification` (verifier ≠ doer), and calibration labels must come from evidence
   the scored system cannot influence.

## 3. The ladder — five levels per stage

| Level | Name | Who acts | What the engine does |
|---|---|---|---|
| **L0** | Shadow (today) | Human | Prints a recommendation; effective decision always ESCALATE |
| **L1** | Calibrated shadow | Human | Same as L0, but labels/signals are audited (Milestone 1) so its fc-rate is *trustworthy evidence* |
| **L2** | Recommend-with-veto | Human (one keystroke) | Engine proposes the action ready-to-execute; human acks or vetoes; vetoes are recorded as calibration labels |
| **L3** | Scoped auto | Engine | Graduated stage acts unattended; owner notified per action (Notifier, P3) with an undo window where the action supports it |
| **L4** | Standing auto | Engine | No per-action notification; weekly digest + dashboard only |

### Evidence bars per transition

| Transition | Evidence required | Who approves |
|---|---|---|
| L0 → L1 | Milestone 1 complete: label-fidelity audit passed; signal defaults eliminated (score variance restored); fc-rate recomputed on audited labels | Autonomous (it's measurement work) — landed CI-gated like any change |
| L1 → L2 | Per stage: ≥30 L1 runs on audited labels, fc ≤5%, over-caution ≤40% (an engine that escalates everything is not earning trust, it's hiding) | **Owner sign-off per stage** |
| L2 → L3 | Per stage: ≥30 L2 runs, human veto rate ≤5%, zero hard-gate breaches, zero secret-scan incidents in the window | **Owner sign-off per stage** (this is the real autonomy switch) |
| L3 → L4 | 60 consecutive days at L3 with zero de-graduation events for that stage | **Owner sign-off** |

### De-graduation (automatic, no approval needed to go DOWN)

- **One-strike at L3+:** any confirmed false-confidence event (the stage acted, a human had to
  fix the result) drops that stage to L2 immediately and alerts the owner (Notifier P2).
- **Hard-gate breach anywhere** (an action executed that a hard gate should have blocked):
  ALL stages drop one level, owner alert P1, post-mortem required before any re-climb.
- **Staleness:** a stage with no runs for 30 days drops one level (a graduation earned once is
  an assumption with a timestamp — manual §8.6 applied to the system itself).
- Re-climbing after de-graduation reuses the same bars (no shortcut for "it was graduated
  before").

## 4. Milestone plan (each PR-sized, in order)

| # | Work item | Why first/next |
|---|---|---|
| M1a | **Label-fidelity audit** of `human_had_to_fix`: sample the 8 reversible false-confidence rows + 10 clean rows, hand-classify against the real PR history, measure proxy precision/recall; redesign the proxy if precision <90% (candidate: only count post-merge fix commits/reverts referencing the PR, not same-branch iteration) | The 89% fc-rate is unusable as evidence either way until the label is trusted |
| M1b | **Signal-default elimination**: 47/56 runs at exactly 60 means `collect_signals`/`record_merged_prs` are filling constants (e.g. CI-rollup-only evidence). Make signals measure per-PR reality (tests run count, coverage delta when available) or explicitly mark the run `low-evidence` and exclude it from calibration | A score that is constant carries no information; graduating on it would be theater |
| M2 | **Per-skill/stage segmentation surfaced**: `stats_by()` exists — put per-skill fc-rates on the dashboard so graduation candidates are visible (e.g. `docs`-class branches may reach the bar long before `feat`) | Graduation will realistically happen per work-class, not globally |
| M3 | **L2 veto loop**: smallest real implementation — engine posts the ready action + one-keystroke ack via the existing session flow; every veto/ack appended to the ledger as a label | Turns human attention into calibration data instead of losing it |
| M4 | **`graduation_overrides` config + `walk_decision` wiring behind an owner flag** (`shadow_mode: false` stays the master switch; per-stage override map for L2/L3) | Only after M1–M3 produce trustworthy evidence |
| M5 | **Dashboard: ladder view** — level per stage, distance-to-next-bar, de-graduation history | Owner visibility for the sign-off decisions |

Non-goals (YAGNI until a bar is actually reached): multi-project graduation transfer, ML-tuned
weights, auto-adjusting thresholds. The `threshold`/`hard_gates`/`irreversible_stages` values
remain owner-edited config, never learned.

## 5. What stays owner-gated forever

- Any L1→L2 or L2→L3 stage promotion (the sign-offs above).
- Any edit to `hard_gates`, `threshold`, `irreversible_stages`, or this ladder's bars.
- Flipping `shadow_mode: false` (master switch).
- Anything in `irreversible_stages` acting without a human, at any level, ever.

## 6. Wiring notes

- Kill switch precedence: `shadow_mode: true` overrides every override (already the config's
  semantic — keep it).
- Notifications ride the shared Notifier gateway (`GLOBAL.md` §2): L3 per-action P3, de-graduation
  P2, hard-gate breach P1. No new sender.
- Audit trail: the ledger stays append-only JSONL; L2 acks/vetoes and de-graduation events get
  their own `event` rows in the same file (schema: `{"event": "veto"|"ack"|"degrade", ...}`) so
  one file remains the source of truth.
- The standing-goals sentinel gains a predicate per activated level (e.g. "L3 active ⇒
  de-graduation alerting verified daily") at activation time, per `goals/README.md` enrollment.

## 7. Risks

- **Proxy irreducibility:** if M1a shows `human_had_to_fix` can't reach usable precision from git
  history alone, L2's explicit ack/veto labels become the primary calibration source and the
  timeline lengthens (by design — never graduate on noisy labels).
- **Over-caution masking:** tightening signals (M1b) may push fc down while over-caution stays
  high; the L1→L2 bar deliberately includes an over-caution ceiling so "escalate everything"
  can't sneak through as safety.
- **Single-project evidence:** all 68 runs are this hub. Graduation evidence is per-project;
  downstream projects start at L0 with their own ledgers (`trust-score/ledgers/<project>.jsonl`
  already segments this).
