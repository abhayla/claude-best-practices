# Agent-Team Compliance Audit — all workflows (2026-06-24)

**Question:** are all workflows *fully* agent-team compliant (the pipeline-upgrade goal claimed ✅)?
**Method:** static audit of each skill's `--team` section (is it wired to spawn a REAL team?) +
live tests via the psmux autonomous harness (ground truth: teammate-attributed events).
**Honest headline:** **WIRING-complete YES; fully-LIVE-verified NO.** All 9 have `--team` handling,
but only **2/9 are live-proven** to spawn real teammates; **1 diverges** to subagents in practice;
the rest are unverified-live (one confounded by an API outage). The tracker's all-✅ reflected
*wiring + partial validation*, not full live proof.

## Matrix

| Workflow | Tier | `--team` WIRED? | Live result (this session) | Verdict |
|---|---|---|---|---|
| **research-mode** | read-only research | ✅ modality teammates | ✅ REAL 3-modality team (`by=teammate-*`) | **LIVE-COMPLIANT** |
| **brainstorm** | read-only advisory | ✅ advisor panel | ✅ REAL 3-lens panel (simplicity/risk/maintainability, cross-challenged) | **LIVE-COMPLIANT** |
| **code-review-workflow** | read-only review | ✅ STEP 2-TEAM ("real team, not subagents") | ⚠️ live run invoked the **Workflow tool / subagent fan-out** (finder+verifier agents), NOT real teammates | **WIRED but DIVERGED live** — wiring says team, runtime used subagents |
| **review-gate** | read-only review | ✅ optional team; default flat | ❓ INCONCLUSIVE — run hit `API ConnectionRefused (attempt 7/10)` + lead went meta | **WIRED; live unverified** (needs clean re-run) |
| **auto-verify** | read-only verify | ✅ optional team; default flat tester-agent | not live-tested | **WIRED; live unverified** |
| **development-loop** | parallel-edit | ✅ STEP 4-TEAM real build team | not re-tested here; contract's prior run = mechanism OK but **1/3 autonomous completion** | **WIRED; partial prior validation (Execute stays supervised)** |
| **executing-plans** | parallel-edit | ✅ delegates to dev-loop STEP 4-TEAM | not live-tested | **WIRED by delegation; live unverified** |
| **implement** | parallel-edit | ✅ optional (conservative — single feature best flat) | not live-tested | **WIRED; live unverified** |
| **writing-plans** | planning | ✅ correctly STAYS single-owner (team-compatible only) | N/A (no team by design) | **COMPLIANT (correct non-team)** |

## Findings

1. **Not all `--team` modes spawn a real team at runtime.** code-review-workflow is *wired* for a real
   review team (STEP 2-TEAM explicitly says "a real agent team, not flat subagents — this is what
   subagents cannot do"), but the live invocation chose the native **Workflow tool** (subagent
   finder/verifier fan-out). Gap between documented intent and runtime behavior. Arguably fine for
   read-only review (subagent fan-out is a valid tool), but it means the ✅ is not "real teammates."
2. **Only research-mode + brainstorm are live-proven** to spawn real teammates (verified
   teammate-attributed events). These are the genuine cross-challenge / multi-source modes where a
   team adds value — consistent with the doctrine.
3. **review-gate test was confounded** by an API `ConnectionRefused` outage — inconclusive, not a fail.
4. **Parallel-edit tier (development-loop/executing-plans/implement)** is wired but only
   development-loop had a prior partial validation (1/3 autonomous completion → Execute stays
   human-supervised). executing-plans/implement inherit it by delegation; not independently live-tested.
5. **writing-plans is correctly non-team** by design (single-owner plan) — compliant.

## Honest answer to "are all workflows fully agent-team compliant?"

**No — not in the live, empirical sense.** They are **wiring-complete** (every workflow has the
correct `--team` handling, including the deliberate single-owner case), which is what the
pipeline-upgrade goal delivered. But "fully compliant" implies every `--team` mode demonstrably spawns
a real team, and that is **not** established: 2/9 live-proven, 1 diverges to subagents, 1 inconclusive
(API), 4 unverified-live, 1 correctly non-team.

## What remains to close it fully (cost + stable API permitting)
Live-run via `scripts/run_agent_team.sh`: auto-verify, executing-plans, implement (+ re-run
review-gate after the API outage, and development-loop in a scratch dir). Decide per code-review
whether the Workflow/subagent path is acceptable as "compliant" for read-only review or should be
changed to spawn real teammates.
