# Stage 0: Master Pipeline Orchestrator — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to run a root pipeline coordinator that spawns and manages 11 stage-specific Claude Code context windows for fully autonomous PRD-to-Production delivery.
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

---

## Architecture

Each stage runs in its **own Claude Code context window**. Stages communicate via hybrid protocol: structured JSON returns to orchestrator + detailed docs on disk for audit trail. The orchestrator manages `.pipeline/state.json` for tracking.

### Diagram 1 — What Stage 0 Is (Orchestrator Role)

```
                        ┌─────────────────────────┐
                        │    YOU (or CI trigger)   │
                        │   provide a PRD / idea   │
                        └────────────┬────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │              STAGE 0: MASTER ORCHESTRATOR              │
        │                                                        │
        │  • Reads pipeline-config.json (stage DAG)              │
        │  • Computes wave execution order                       │
        │  • Spawns each stage in its own Claude Code window     │
        │  • Validates artifact contracts at gate boundaries     │
        │  • Retries failed stages (up to 3x)                   │
        │  • Rolls back on unrecoverable failure                 │
        │  • Writes state.json + event-log.jsonl continuously    │
        └──┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬───┘
           │      │      │      │      │      │      │      │
           ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
        ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐  ...
        │ST 1││ST 2││ST 3││ST 4││ST 5││ST 6││ST 7│  (11 stages)
        │    ││    ││    ││    ││    ││    ││    │
        └────┘└────┘└────┘└────┘└────┘└────┘└────┘
         Each runs in an isolated Claude Code context window
```

> **Key insight:** Stage 0 never writes application code. It only coordinates — dispatching stages, checking gates, managing state.

### Diagram 2 — Wave Execution Order (DAG)

Stages run in **waves**. Stages within a wave execute in parallel. A wave starts only after all its dependencies complete.

```
 WAVE 1 ──────────────────────────────────────────────────────────
  │
  │  ┌───────────┐
  │  │  ST 1     │  Parse/normalize PRD
  │  │  PRD      │──────────────────────────────────────────┐
  │  └─────┬─────┘                                          │
  │        │                                                │
 WAVE 2 ───┼────────────────────────────────────────────────┼─
  │        │                                                │
  │   ┌────▼─────┐   ┌───────────┐                         │
  │   │  ST 2    │   │  ST 3     │  ◄── both need ST 1     │
  │   │  PLAN    │   │  SCAFFOLD │      run in parallel     │
  │   └────┬─────┘   └─────┬─────┘                         │
  │        │          ┌─────┘                               │
 WAVE 3 ───┼──────────┼────────────────────────────────────┼─
  │        │          │                                     │
  │        │     ┌────▼─────┐                               │
  │        │     │  ST 4    │  ◄── needs ST 1 + ST 3       │
  │        │     │  DEMO    │  (skippable for CLI projects) │
  │        │     └──────────┘                               │
  │        │          │                                     │
 WAVE 4 ───┼──────────┼────────────────────────────────────┼─
  │   ┌────▼─────┐    │                                     │
  │   │  ST 5    │    │  ◄── needs ST 2 + ST 3             │
  │   │  SCHEMA  │    │                                     │
  │   └────┬─────┘    │                                     │
  │        │          │                                     │
 WAVE 5 ───┼──────────┼─────────────────────────────────────
  │   ┌────▼─────┐                                          │
  │   │  ST 6    │  ◄── needs ST 2 + ST 5                  │
  │   │ PRE-TEST │  Write tests BEFORE implementation       │
  │   └────┬─────┘                                          │
  │        │                                                │
 WAVE 6 ───┼─────────────────────────────────────────────────
  │   ┌────▼─────┐                                          │
  │   │  ST 7    │  ◄── needs ST 6                         │
  │   │  IMPL    │  Write code to pass pre-written tests    │
  │   └────┬─────┘                                          │
  │        │                                                │
 WAVE 7 ───┼─────────────────────────────────────────────────
  │   ┌────▼─────┐                                          │
  │   │  ST 8    │  ◄── needs ST 7                         │
  │   │POST-TEST │  Integration, E2E, edge cases            │
  │   └────┬─────┘                                          │
  │        │                                                │
 WAVE 8 ───┼─────────────────────────────────────────────────
  │   ┌────▼─────┐                                          │
  │   │  ST 9    │  ◄── needs ST 8                         │
  │   │  REVIEW  │  Automated code review                   │
  │   └────┬─────┘                                          │
  │        │                                                │
 WAVE 9 ───┼─────────────────────────────────────────────────
  │   ┌────▼─────┐                                          │
  │   │  ST 10   │  ◄── needs ST 9                         │
  │   │  DEPLOY  │  CI/CD, infrastructure                   │
  │   └────┬─────┘                                          │
  │        │                                                │
 WAVE 10 ──┼─────────────────────────────────────────────────
  │   ┌────▼─────┐                                          │
  │   │  ST 11   │  ◄── needs ST 10 + ST 1 (for PRD refs) │
  │   │  DOCS    │  API docs, README, changelog             │
  │   └──────────┘                                          │
```

> **Critical path:** ST 1 → ST 2 → ST 5 → ST 6 → ST 7 → ST 8 → ST 9 → ST 10 → ST 11 (the longest chain determines minimum pipeline duration)

### Diagram 3 — Artifact Flow Between Stages

Each stage consumes artifacts from upstream and produces artifacts for downstream. Stage 0 validates contracts at every gate.

```
  ST 1 PRD
    │
    ├──produces──→  prd.md, requirements.json
    │
    ▼
  ST 2 PLAN                          ST 3 SCAFFOLD
    │                                   │
    ├──produces──→  plan.md,            ├──produces──→  project skeleton,
    │               task-breakdown.json │               config files
    │                                   │
    ▼                                   ▼
  ST 5 SCHEMA                        ST 4 DEMO
    │                                   │
    ├──produces──→  schema.sql,         ├──produces──→  demo.html
    │               models/*, migrations│
    │                                   │
    ▼
  ST 6 PRE-TESTS
    │
    ├──produces──→  test files (failing — no impl yet)
    │
    ▼
  ST 7 IMPLEMENTATION
    │
    ├──produces──→  source code (tests now pass)
    │
    ▼
  ST 8 POST-TESTS
    │
    ├──produces──→  integration/E2E tests, coverage report
    │
    ▼
  ST 9 REVIEW
    │
    ├──produces──→  review-report.md, fix commits
    │
    ▼
  ST 10 DEPLOY
    │
    ├──produces──→  deployment artifacts, health check results
    │
    ▼
  ST 11 DOCS
    │
    └──produces──→  API docs, README, CHANGELOG, architecture docs
```

### Diagram 4 — Failure Handling Lifecycle

What happens when a stage fails:

```
                 Stage N dispatched
                        │
                        ▼
               ┌─────────────────┐
               │  Execute Stage  │
               └────────┬────────┘
                        │
                   ┌────▼────┐
                   │  Gate   │
                   │  Check  │
                   └────┬────┘
                        │
              ┌─────────┼─────────┐
              │         │         │
           ✅ PASS   ⚠️ WARN   ❌ FAIL
              │         │         │
              ▼         ▼         ▼
         Record in   Record +   Retry (up to 3x)
         state.json  continue        │
              │         │        ┌───▼───┐
              ▼         │     Still fails?
         Dispatch       │        │       │
         next wave      │       NO      YES
              │         │        │       │
              │         │        ▼       ▼
              │         │     Continue  Compensating
              │         │     (retry    Rollback
              │         │      worked)     │
              │         │        │         ▼
              │         │        │    git revert to
              │         │        │    last checkpoint
              │         │        │         │
              │         │        │         ▼
              └─────────┴────────┴──→ Pipeline complete
                                      or halted
```

> **Idempotency:** Every stage can be safely re-run. The orchestrator tags git checkpoints before each stage, so rollback reverts to a known-good state.

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
| **PMI PMBOK** | WBS for stage decomposition, critical path analysis | ✅ `pipeline-orchestrator` builds DAG from stage dependencies, computes execution waves with topological ordering, and identifies critical path |
| **Design by Contract (Meyer)** | Pre/post-conditions per stage, typed artifact schemas | ✅ `pipeline-orchestrator` defines typed `artifacts_in`/`artifacts_out` per stage with schema definitions; pre-dispatch validation ensures all inputs exist before downstream stages run |
| **Saga Pattern** | Compensating transactions on stage failure | ✅ `pipeline-orchestrator` implements git-based compensating rollback with checkpoint tags for idempotent re-execution |
| **Event Sourcing** | Immutable pipeline state log | ✅ `pipeline-orchestrator` maintains `.pipeline/state.json` as single source of truth + append-only `.pipeline/event-log.jsonl` for immutable audit trail |
| **Workflow Patterns (van der Aalst)** | Exclusive/parallel/conditional routing | ✅ `pipeline-orchestrator` supports `skip_when` conditions for conditional execution, parallel wave dispatch, and dependency-aware routing |
| **Observability (Charity Majors)** | Structured logs, stage timing, error categorization | ✅ `pipeline-orchestrator` emits structured JSONL events with timestamps, duration, token usage, retry counts, and renders a progress dashboard |

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
