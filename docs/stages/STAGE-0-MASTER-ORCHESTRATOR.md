# Stage 0: Master Pipeline Orchestrator — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to run a root pipeline coordinator that spawns and manages 11 stage-specific Claude Code context windows for fully autonomous PRD-to-Production delivery.
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

---

## Architecture

Each stage runs in its **own Claude Code context window**. Stages communicate via hybrid protocol: structured JSON returns to orchestrator + detailed docs on disk for audit trail. The orchestrator manages `.pipeline/state.json` for tracking.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 0: MASTER ORCHESTRATOR                           │
└──┬──────┬──────┬──────────────────────────────────────────────────────────┬──┘
   │      │      │                                                          │
   ▼      │      │     WAVE 1 (no deps)                                    │
 ST 1     │      │                                                          │
 PRD      │      │                                                          │
   │      ▼      ▼                                                          │
   │  ┌──────┐ ┌──────┐  WAVE 2 (after Stage 1)                           │
   ├─→│ ST 2 │ │ ST 3 │  Plan + Scaffold in parallel                      │
   │  │ PLAN │ │SCAFF │                                                     │
   │  └──┬───┘ └──┬───┘                                                    │
   │     │    ┌───┘                                                         │
   │     │    ▼                                                             │
   │     │  ST 4 DEMO     WAVE 3 (after Stages 1 + 3)                     │
   │     │    │                                                             │
   │     ▼    │                                                             │
   │  ST 5 SCHEMA         WAVE 4 (after Stages 2 + 3)                     │
   │     │                                                                  │
   │     ▼                                                                  │
   │  ST 6 PRE-TESTS      WAVE 5 (after Stages 2 + 5)                     │
   │     │                                                                  │
   │     ▼                                                                  │
   │  ST 7 IMPL           WAVE 6 (after Stage 6)                          │
   │     │                                                                  │
   │     ▼                                                                  │
   │  ST 8 POST-TESTS     WAVE 7 (after Stage 7)                          │
   │     │                                                                  │
   │     ▼                                                                  │
   │  ST 9 REVIEW         WAVE 8 (after Stage 8)                          │
   │     │                                                                  │
   │     ▼                                                                  │
   │  ST 10 DEPLOY        WAVE 9 (after Stage 9)                          │
   │     │                                                                  │
   │     ▼                                                                  │
   └─→ST 11 DOCS          WAVE 10 (after Stage 10)                        │
```

---

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Pipeline stage sequencing | `subagent-driven-dev` | ✅ Covered | — |
| 2 | Gate pass/fail evaluation | `subagent-driven-dev` (3-retry) | ✅ Covered | — |
| 3 | Artifact routing between stages | `subagent-driven-dev` (file ownership) | ⚠️ Partial — no typed contracts | **Design by Contract (Meyer)** |
| 4 | Failure recovery & retry | `executing-plans` (fix loops) | ⚠️ Partial — no stage-level rollback | **Saga Pattern** |
| 5 | Pipeline state persistence | `pipeline-orchestrator` (Step 1.5: state.json) | ✅ Covered | **Event Sourcing** |
| 6 | DAG visualization & dependency graph | `pipeline-orchestrator` (Step 2: wave computation) | ✅ Covered | **WBS (PMI PMBOK)** |
| 7 | Artifact contract validation | `pipeline-orchestrator` (Step 3.1: pre-dispatch validation) | ✅ Covered | **Design by Contract** |
| 8 | Conditional branching (skip/parallel) | `pipeline-orchestrator` (Step 1.4: skip_when conditions) | ✅ Covered | **Workflow Patterns (van der Aalst)** |
| 9 | Idempotency guarantees | `pipeline-orchestrator` (Step 6: idempotent re-run) | ✅ Covered | **Exactly-once semantics** |
| 10 | Pipeline observability (logs, metrics) | `pipeline-orchestrator` (Step 7: event log + dashboard) | ✅ Covered | **Observability (Charity Majors)** |
| 11 | Orchestration-wide rollback | `pipeline-orchestrator` (Step 5.2: compensating rollback) | ✅ Covered | **Saga Pattern / Compensating Transactions** |
| 12 | Parallel stage execution | `subagent-driven-dev` (waves) | ✅ Covered | — |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **PMI PMBOK** | WBS for stage decomposition, critical path analysis | ❌ No DAG or critical-path analysis |
| **Design by Contract (Meyer)** | Pre/post-conditions per stage, typed artifact schemas | ❌ No contract definitions |
| **Saga Pattern** | Compensating transactions on stage failure | ❌ No rollback mechanism |
| **Event Sourcing** | Immutable pipeline state log | ❌ No state persistence |
| **Workflow Patterns (van der Aalst)** | Exclusive/parallel/conditional routing | ⚠️ Parallel exists, no conditional |
| **Observability (Charity Majors)** | Structured logs, stage timing, error categorization | ❌ No pipeline-level telemetry |

## Gap Proposals

### Gap 0.1: `pipeline-orchestrator` skill (Priority: P0)

**Problem it solves:** No existing skill handles DAG-based multi-stage pipeline coordination with typed contracts, state persistence, conditional branching, rollback, and observability.

**What it needs:**
- DAG-based stage sequencing with critical-path identification
- Typed artifact contracts (JSON Schema) validated at gate boundaries
- Conditional branching: skip stages based on project type (e.g., skip Stage 4 HTML Demo for CLI tools)
- Idempotent stage execution: re-running a stage with same inputs produces same outputs
- State persistence: `.pipeline/state.json` with append-only event log
- Compensating transactions: on Stage N failure, orchestrator knows how to undo Stage N's partial artifacts
- Observability: structured log per stage with timing, token usage, retry count

**Existing coverage:** `subagent-driven-dev` covers parallel dispatch and retry. `executing-plans` covers sequential task execution. Neither handles typed contracts, state persistence, conditional routing, or rollback.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `pipeline-config.json` | All stages | `{stages: [{id, depends_on, skip_when, artifacts_in, artifacts_out}]}` |
| `.pipeline/state.json` | Orchestrator (self) | `{stages: {[id]: {status, started_at, completed_at, gate_result, retries}}}` |
| `.pipeline/event-log.jsonl` | Observability/Debug | Append-only structured events |

## Research Targets

- **GitHub**: `claude-code pipeline orchestrator`, `LLM agent workflow DAG`, `ai-agent-pipeline state machine`
- **Reddit**: r/ClaudeAI + r/LocalLLaMA — "multi-agent pipeline", "autonomous coding pipeline"
- **Twitter/X**: `claude code pipeline`, `AI agent orchestration pattern`

## Stack Coverage

Universal — no stack-specific variants needed for orchestration.

## Autonomy Verdict

**✅ Can run autonomously.** The `pipeline-orchestrator` skill now covers: DAG-based sequencing, typed artifact contracts, state persistence, conditional branching, idempotent execution, observability (event log + dashboard), and compensating rollback. Built on top of `subagent-driven-dev` (parallel dispatch) and `executing-plans` (sequential execution).

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial design — 12-stage architecture with 10 execution waves |
| 2026-03-13 | Rewritten as AUDIT prompt with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P0 gap resolved: `pipeline-orchestrator` skill created — all 7 missing capabilities now ✅ |
