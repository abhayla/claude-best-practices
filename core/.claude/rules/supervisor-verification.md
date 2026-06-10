# Scope: global

# Supervisor Verification — reading a worker's claim is not verifying it

version: "1.0.0"

The T0 orchestrator is the **supervisor** of every output it dispatches.
Reading a worker's return contract is necessary but **NOT sufficient** — the
orchestrator MUST independently **reproduce the gate and inspect the output
substance** before accepting it, building on it, or committing it. A worker's
self-reported "done / clean / tests pass" is a **claim, not proof**, until the
supervisor reproduces it.

This extends `agent-orchestration.md` §2 ("MUST read the return") with the
missing step: reading the claim ≠ verifying the claim.

## Who supervises whom

The platform allows a single dispatch level (`agent-orchestration.md` §2): T0
dispatches workers and they return; there is no higher checker. Therefore **T0
IS the supervisor** and owns the quality of every output that flows back.
"I delegated it" never transfers the validation duty.

## The supervisor gate — for every dispatched worker output

Before accepting / committing / building on ANY output:

1. **Read** the structured return contract (gate / artifacts / summary) — the
   floor, not the ceiling.
2. **Reproduce the gate** — re-run the worker's claimed check yourself (lint /
   type-check / tests). If the worker reports "lint exits 0", run lint. Never
   accept a reported exit code as proof.
3. **Inspect the substance** — read the actual diff / artifact for semantic
   drift, scope creep, and shape-vs-substance: did it change behavior it
   shouldn't, or touch files outside the brief?
4. **Cross-check the contract** — does the output match what was ASKED (scope
   honored, constraints respected, files confined to the brief)?
5. **Only then accept.** On ANY divergence: return the work to the worker or
   fix at T0 — never accept-and-hope.

## Outputs that change a running UI — verify by driving it

For any output that changes rendered UI, the "reproduce + inspect" steps MUST
include **driving the actual app** (a browser-automation loop via the project's
available tooling — Playwright/Chrome DevTools MCP, or the `/run` skill), NEVER
accepted on code inspection alone:

1. Navigate to the affected screen (self-heal: start the dev server if down).
2. **Screenshot** — does it LOOK the way it was implemented?
3. **Structural/ARIA snapshot** — is the intended element present?
4. **Console** — no NEW errors/warnings from the change?
5. **Interact** — does it WORK the way it was implemented?
6. **Compare to implemented intent** (look AND behavior), not just "renders
   without error." On any mismatch, fix the root cause and re-run; iterate
   until it matches intent (cap in-loop attempts, then escalate to `/fix-loop`).

"It builds / no console error" is a claim about the UI; the screenshot +
interaction are the proof.

## Relationship to the other gates (no duplication)

- `agent-orchestration.md` §2 says READ the return; this rule says reproduce +
  inspect the substance.
- An **independent reviewer** of the *author's* work (a separate agent) is a
  distinct, composing step: worker returns → T0 supervisor-validates (this
  rule) → for non-trivial changes T0 also dispatches an independent reviewer →
  T0 commits. For test verdicts specifically, see `independent-test-verification.md`.

## CRITICAL RULES

- MUST independently reproduce a worker's claimed gate (re-run lint /
  type-check / tests) — never accept the self-reported result as proof.
- MUST inspect the actual output substance (diff / artifact) for semantic
  drift, scope creep, and out-of-brief file changes, before accepting.
- MUST verify UI-changing output by driving the running app (screenshot +
  interaction), not by reading code alone.
- MUST NOT proceed / commit on a worker return until the supervisor gate
  passes; on divergence, return the work or fix at T0.
- MUST NOT treat delegation as transferring the validation duty.
