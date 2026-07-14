# BA → Architect → Loop-Engineering — the idea→production handoff

**Status:** design APPROVED + wiring BUILT & verified 2026-07-14. Canonical flow (owner-confirmed):
`interactive requirements (owner + BA) → owner approval → press button → automated
architect + build + test with quick approval pauses → owner accepts → owner ships`.
Runbook is usable TODAY (zero code). Pipeline wiring landed: `stage_7_impl: loop-engineering`
(+ `--no-ship`), A1 design-approval pause added, T0 BA-grilling precondition documented, full
suite green (1825 passed). **Remaining (owner-gated):** validate on the first real feature run;
then decide whether to trim `stage_8_post_tests` (double-verify) — see §5 risks.

**Owner decision context:** loop-engineering is deliberately NOT part of the PRD-to-Production
pipeline today (KISS convention — the PM agent runs 8 workflows; loop-engineering is a 9th
standalone meta-loop). This plan relates them via a **clean handoff**, not a merge: the
human-gated product front-end (BA + Architect) produces a contract; the autonomous
self-healing loop grinds it to *verified*; humans keep the accept + ship gates.

---

## 1. The doctrine — autonomous between the human gates

```
 idea ─▶ 1.BA discovery ─▶ [G1 design] ─▶ 2.Architect+contract ─▶ 3.loop-engineering ─▶ [G2 accept] ─▶ [G3 deploy]
          (human)           HUMAN            (human)                  (MACHINE, --no-ship)   HUMAN         HUMAN
```

Three human decisions bracket one autonomous run. Everything between **G1** and **G2** is
loop-engineering. The owner only decides: *build this design (G1)*, *this is what I asked (G2)*,
*ship it (G3)*.

**Why handoff, not merge (the three things never to flatten):**
1. **Human gates survive.** loop-engineering has no product gates by design (so it runs
   unattended). `--no-ship` is the seam — it stops at "verified, not shipped" so G2/G3 stay human.
   Governing rule: `human-approval-gates.md` (G1/G2/G3).
2. **No duplicate discovery.** The Architect's contract IS the loop's unit — loop-engineering
   STEP 2 rule 1 ("if `$ARGUMENTS` names a concrete task, that's the unit; skip scanning") is the seam.
3. **maker ≠ checker independence preserved** — the loop's core value; never collapse it into
   "the PM agent runs a loop itself."

## 1a. Human touchpoints that must NEVER be automated away (owner directive 2026-07-14)

Even in the fully-wired one-button pipeline, these human interactions are MANDATORY — the
automation runs *around* them, never *through* them:

| # | Touchpoint | Kind | Why it can't be skipped |
|---|---|---|---|
| **T0** | **BA requirements grilling** | Interactive conversation (front) | Requirements live in the owner's head — the machine cannot generate its own input. BA MUST grill one question at a time (`ba-discovery-checklist.md`) until the full space is captured, then get **feature-set approval**. The button only starts the run AFTER this. NEVER auto-generate a PRD from a one-line input. |
| **A1** | **Architect design approval** | Quick review/approve gate (NEW) | After the Architect proposes the technical approach (data model, API, key decisions), the owner does a fast review + yes before build starts. Distinct from G1 (which is the UI/UX mockup). |
| **G1** | Design / UI mockup | Approve gate | "Build this look." |
| **G2** | Feature acceptance | Approve gate | "This is what I asked." |
| **G3** | Production deploy | Approve gate | "Ship it." |

**Consequence for the wiring change:** it is TWO parts, not one — (a) swap the build engine to
loop-engineering, AND (b) guarantee T0 (interactive BA grilling) + A1 (architect approval) fire.
Flipping only (a) risks the pipeline guessing requirements from a thin input — the exact failure
the owner rejects. Both land together.

---

## 2. Runbook — the owner operating procedure (usable NOW, no code changes)

Run this on ONE real feature to prove the flow before any wiring.

**Stage 1 — BA discovery**
```
I want to build <idea>. Act as the Business Analyst — run full use-case discovery first.
```
→ 6-item checklist (actors → value → lifecycle → component×actor matrix → variants → aha-outputs),
domain web-research, one-question-at-a-time clarification, independent completeness audit.
→ Present feature set + scope for explicit sign-off. Then present UI/UX mockup = **G1** approval.
(Governed by `ba-discovery-checklist.md` + `engineering-roles.md` PM mandate.)

**Stage 2 — Architect → contract**
```
Act as the Systems Architect — design this, then author a /goal-creator contract
(DoD + file plan + full consumer/surface map) for an autonomous run.
```
→ Architecture + ADR for non-trivial calls (`/adr`) → `/goal-creator` writes a zero-open-questions
contract at `docs/plans/<feature>-contract.md`. That file is the baton.

**Stage 3 — autonomous build+verify**
```
/loop-engineering docs/plans/<feature>-contract.md --no-ship
```
→ PREFLIGHT (maker/checker present) → consume contract as the unit (skip re-discovery) →
PLAN → EXECUTE (maker, isolated worktree) → VERIFY (independent checker + mechanical gate +
supervisor reproduction) → self-heal on failure (bounded, §6a strategy mutation) → stop at
*verified*. Returns a PASSED/ESCALATED verdict dashboard.

**Stage 4 — human accept + ship**
- **G2** — review the verified feature driven in the running app (screenshots) → confirm intent.
- **G3** — approve deploy → `/vps-deploy` (or the project's deploy skill) ships.

> Keep `--no-ship` until several runs land cleanly. Even then, G3 (deploy) stays the owner's
> call (`decision-authority.md`: irreversible/outward).

---

## 3. The pipeline-wiring change (deferred — gated on one clean validation run)

**Goal:** make the one-shot `project-manager-agent` pipeline use loop-engineering as its build
engine, so every future run gets self-healing + strategy-mutation + escalation for free — instead
of the raw `development-loop` at `stage_7_impl`.

**Current mapping** (`config/workflow-contracts.yaml` → `stage_to_workflow`):
```
stage_4_demo:   null            # G1 here
stage_6_pre_tests: testing-pipeline
stage_7_impl:   development-loop  # ← THE BUILD MIDDLE
stage_8_post_tests: testing-pipeline
stage_9_review: code-review       # G2 after
stage_10_deploy: null             # G3 before
```

**Pilot change (smallest viable):**
1. `config/workflow-contracts.yaml` — remap `stage_7_impl: loop-engineering`.
   - The stage passes the plan artifact path as the loop's `$ARGUMENTS` unit and adds `--no-ship`
     (the pipeline's own stage_10 owns deploy; the loop must not ship past G2/G3).
   - Confirm `/loop-engineering` is invocable via the same `Skill("/<workflow-name>", ...)` path the
     PM agent uses for mapped workflows (it is a skill-at-T0, same as the others).
2. `core/.claude/agents/project-manager-agent.md` — note that `stage_7_impl` now runs the
   self-healing meta-loop; its internal VERIFY overlaps `stage_8_post_tests`, so evaluate whether
   stage_8 (testing-pipeline) is redundant for the loop path or stays as an independent
   pipeline-level gate (recommend: KEEP stage_8 initially as the independent blind re-check —
   `independent-test-verification.md` — measure before removing).
3. Add a `stage_to_workflow` regression-test expectation if one exists; run the full local CI gate
   (dedup-validate + secret-scan + quality-gate + pytest) before landing.
4. Registry/docs: no new pattern (loop-engineering already registered); regenerate workflow docs if
   the mapping surfaces there.

**Contract seam to verify at pilot time:** loop-engineering's PREFLIGHT BLOCK
(`WORKER_REGISTRY_NOT_LOADED`) must be handled by the PM agent's stage failure/retry path, not
crash the pipeline.

---

## 4. Rollout sequencing (prove-first — do NOT skip)

1. **Run the Section-2 runbook by hand on one real feature.** Confirm the BA→contract→loop handoff
   feels right and the loop consumes the contract cleanly.
2. If clean → make the Section-3 pilot wiring change (stage_7 remap only), land CI-gated.
3. Run the one-shot pipeline (`Act as the project manager — run the full PRD-to-Production pipeline
   for <idea>`) on a second feature; confirm G1/G2/G3 still pause and the loop drives stage_7.
4. Only then decide whether to absorb `stage_8_post_tests` into the loop path (measure double-verify
   cost first).

---

## 5. Risks / open items

- **Double verification** (loop's internal VERIFY + stage_8 testing-pipeline) — intentional at
  first (independent re-check); revisit after measuring.
- **Redundant PLAN/DISCOVER** — loop STEP 3 PLAN partly duplicates the Architect's plan; the
  contract-as-unit seam should make the loop skip re-planning. Verify at pilot.
- **Doctrine change** — this makes loop-engineering part of the PM pipeline, reversing the current
  KISS convention (CLAUDE.md "the count of workflow skills the PM agent invokes remains 8"). Update
  that doctrine note in the same change set if the pilot is adopted.
- The wiring is a **strategic hub-doctrine change** — land it as its own CI-gated PR with an ADR
  (`/adr`) recording the decision.
