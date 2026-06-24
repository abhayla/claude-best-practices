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

## COMPLETED live sweep (2026-06-24, API restored) — final results

Ran the 4 deferred modes via the psmux harness (read-only in the hub; executing-plans + implement in
an isolated scratch git repo). **All 4 FAILED to spawn real teammates** (zero new teammate-attributed
events; scratch repo got no files):

- **review-gate** — the lead asked a Sync-check ("subagents vs real teammate sessions?") and used the
  flat path; no team.
- **auto-verify** — the lead ran **3 background SUBAGENTS** (explicitly noting "subagents ≠ teams"),
  not peer teammates; no team.
- **executing-plans** / **implement** — no real team formed, no partitioned files created.

### Important methodological caveat (honest)
These "no team" outcomes are partly **by design + environment**, not pure failure:
1. The skills themselves frame `--team` as an **opt-in path with flat subagents as the DEFAULT**
   ("self-gates to the flat path", "cheaper, the default", "stay flat"). A lead following the skill
   faithfully picks flat unless strongly forced to teams.
2. The test leads also **read this very audit + the agent-teams docs** ("subagents ≠ teams",
   "code-review diverges", "Execute autonomy 1/3") and reasonably chose the safer flat/subagent path
   or paused to confirm. My own documentation biased the subjects toward NOT teaming.

So the result is better stated as: **`--team` does NOT reliably auto-produce a real team** — only
research-mode + brainstorm did (their framing + prompt aligned to spawning teammates). The rest treat
flat subagents as the default and only team up under stronger, unambiguous direction.

### FINAL verdict (all 9, empirical)
| Workflow | Forms a REAL team live? |
|---|---|
| research-mode | ✅ yes |
| brainstorm | ✅ yes |
| code-review-workflow | ❌ no — Workflow/subagent fan-out |
| review-gate | ❌ no — flat subagents (lead chose) |
| auto-verify | ❌ no — background subagents |
| executing-plans | ❌ no — no team formed |
| implement | ❌ no — no team formed |
| development-loop | ⚠️ prior partial only (1/3 autonomous; not re-tested) |
| writing-plans | ✅ correct non-team (by design) |

**Bottom line: 2/9 reliably form real teams; 5 `--team` modes fall back to flat subagents; 1 partial;
1 correctly non-team. NOT "fully agent-team compliant" in the live sense — wiring exists everywhere,
but flat-subagent is the de-facto default for most modes.**

## What remains to close it fully (cost + stable API permitting)
Live-run via `scripts/run_agent_team.sh`: auto-verify, executing-plans, implement (+ re-run
review-gate after the API outage, and development-loop in a scratch dir). Decide per code-review
whether the Workflow/subagent path is acceptable as "compliant" for read-only review or should be
changed to spawn real teammates.
