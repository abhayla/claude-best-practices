---
name: learning-self-improvement
description: >
  Capture session learnings, detect recurring patterns, and generate skill
  proposals from accumulated knowledge as a skill-at-T0 orchestrator
  (Phase 3.7 of subagent-dispatch-platform-limit remediation). The skill body
  IS the orchestrator — runs in the user's T0 session and drives: capture →
  detect-patterns → knowledge-test. Invokes sub-skills (/learn-n-improve,
  /skill-factory, /test-knowledge) via Skill(); optionally dispatches
  session-summarizer-agent and context-reducer-agent via Agent() at T0 when
  deep session analysis is needed.
type: workflow
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<'session' | 'detect-patterns' | 'full' | specific topic>"
version: "2.1.1"
---

# /learning-self-improvement — Skill-at-T0 Orchestrator

This skill's body is injected into the user's T0 session and executed there.
The retired `learning-self-improvement-master-agent` is NOT dispatched
(deprecated Phase 3.7, 2026-04-25); its orchestration lives here.

**Why skill-at-T0:** Same platform constraint Phases 3.1–3.6 — dispatched
subagents don't receive the `Agent` tool
([Anthropic docs](https://code.claude.com/docs/en/sub-agents)). Legacy
master → session-summarizer-agent (T2) + context-reducer-agent (T2)
dispatch chain silently inlined.

**Critical:** Skill proposals require **3+ evidence occurrences** — never
propose from a single incident. Reactive curation, not speculative.

**Input:** `$ARGUMENTS` — mode keyword or specific learning topic.

---

## CLI Signature

```
/learning-self-improvement <mode | topic>
                           [--deep-analysis] [--no-propose]
```

| Argument / Flag | Default | Meaning |
|-----------------|---------|---------|
| `mode` | `session` | `session` (capture only) \| `detect-patterns` (pattern detection only) \| `full` (all 3 steps) \| `<topic>` (targeted for that topic) |
| `--deep-analysis` | off | Dispatch session-summarizer-agent + context-reducer-agent for richer analysis |
| `--no-propose` | off | Skip STEP 3 skill-factory — just capture, don't propose new skills |

---

## STEP 1: INIT

1. **Parse args.** Normalize mode.
2. **Read config.** `.claude/config/workflow-contracts.yaml (hub repo: config/workflow-contracts.yaml; if absent, use the inline steps below — this skill is self-contained)` → `workflows.learning-self-improvement`.
   `master_agent` should be null; `sub_orchestrators` empty (Phase 3.7).
3. **Generate `run_id`.** `{ISO-8601}_{7-char git sha}` with `:` → `-`.
4. **Initialize state** at `.workflows/learning-self-improvement/state.json`
   (schema 2.0.0): `mode`, step_status, `dispatches_used: 0`,
   `evidence_threshold: 3` (hard gate for pattern → skill proposal).
5. Append INIT event.

---

## STEP 1.5: PREFLIGHT (dependency-closure gate — BLOCK on missing workers)

Before any dispatch, verify the runtime closure this workflow needs is present
AND dispatchable. Pattern provisioning copies by tier and may not resolve a
skill's full closure, so a project can have this skill without its workers — a
silent inline run or a mid-dispatch crash is the failure this gate prevents.

- **Required sub-skills** (invoked via `Skill()`): `learn-n-improve`, `skill-factory`, `test-knowledge`. Check each exists at
  `.claude/skills/<name>/SKILL.md` (only those on the path you will actually run).
- **Required worker agents** (dispatched via `Agent()`): `context-reducer-agent`, `session-summarizer-agent` (when deep analysis runs). File presence
  (`.claude/agents/<name>.md`) is necessary but NOT sufficient — the agent registry
  is pinned at session start (`pattern-structure.md` → "registry session-pinning"),
  so probe runtime dispatchability for any agent on the path about to run.
- **On any missing/undispatchable dependency → BLOCK** with verdict
  `WORKER_REGISTRY_NOT_LOADED`, list what is missing, and emit: "run
  `/update-practices` to provision the closure, then RESTART the session (agent
  registry is pinned at session start), then re-run." Write the BLOCKED verdict to
  this workflow's report artifact and STOP.

Only when the required closure is present and dispatchable, continue.

---

## STEP 2: CAPTURE (runs in all modes)

### 2a: Optional deep session analysis (--deep-analysis)

```
Agent(subagent_type="session-summarizer-agent", prompt="""
## Workflow: learning-self-improvement
## Mode: deep-session-analysis
## Session transcript: <path or in-context>

Extract non-obvious learnings, decision patterns, and correction patterns.
Return structured findings JSON.
""")
```

Increment `dispatches_used` by 1.

### 2b: Capture learnings

```
Skill("/learn-n-improve", args="session <topic if provided> [deep-findings=<path>]")
```

`/learn-n-improve session` appends to `.claude/learnings.json` with structured
learning entries: category, trigger, pattern, evidence_count, first_seen,
last_seen. If topic provided, scopes to that topic.

Capture path + new-entry count into `state.artifacts.learnings`.

---

## STEP 3: DETECT_PATTERNS (skip if mode == session OR --no-propose)

### 3a: Optional context reduction for large learnings files

If `learnings.json` has >500 entries OR `--deep-analysis`:

```
Agent(subagent_type="context-reducer-agent", prompt="""
## Workflow: learning-self-improvement
## Mode: compress-for-pattern-detection
## Learnings file: .claude/learnings.json
## Target size: <budget>

Cluster similar learnings, distill recurring patterns, return compressed
representation for downstream pattern detector.
""")
```

Increment `dispatches_used` by 1.

### 3b: Skill factory

```
Skill("/skill-factory", args="propose --evidence-threshold=3 <learnings-file-or-compressed>")
```

`/skill-factory` clusters learnings by recurring pattern, enforces the
3+-occurrence threshold, generates skill proposals with:
- Proposal name + description
- Evidence citations (N occurrences across sessions)
- Scope + trigger specification
- Confidence score

Proposals go to `.claude/skill-proposals/` (staging — NOT automatically
promoted to `.claude/skills/`). User review required before promotion.

Capture proposals path into `state.artifacts.proposals`.

Patterns below the 3-occurrence threshold: tracked in state as "emerging"
but not proposed. Re-evaluated on next run.

---

## STEP 4: KNOWLEDGE_TEST (skip if mode == session)

```
Skill("/test-knowledge", args="validate-freshness --stale-threshold-days=90")
```

`/test-knowledge` validates accumulated knowledge:
- Flags stale learnings (> 90 days without refresh)
- Tests each piece of knowledge against current codebase state (e.g., does
  the flagged file still exist, does the named pattern still match code)
- Reports dead references, obsolete lessons, patterns superseded by newer
  conventions

Gate: if `stale_count > healthy_threshold`, transition to
`step_status.KNOWLEDGE_TEST = warned`. Not BLOCKED — stale knowledge is
normal; surface for pruning but don't halt.

---

## STEP 5: REPORT

1. **Finalize state.** Write `test-results/learning-verdict.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "result": "COMPLETED | WARNED",
     "mode": "<session|detect-patterns|full|topic>",
     "learnings": { "new_entries": <n>, "total_entries": <n> },
     "patterns": { "detected": <n>, "below_threshold": <n> },
     "proposals": { "count": <n>, "path": "<dir>" },
     "knowledge_health": { "fresh": <n>, "stale": <n>, "obsolete": <n> },
     "budget_used": { "dispatches_used": <n> },
     "finalized_at": "<iso>"
   }
   ```
2. **Dashboard:**
   ```
   ============================================================
   Learning & Self-Improvement: <COMPLETED | WARNED>
     Run ID: <run_id>
     Mode: <mode>
     Learnings captured: <N> new (<total> total)
     Patterns detected: <N> (≥3 evidence) + <M> emerging
     Skill proposals: <N> awaiting review
     Knowledge health: <fresh>/<stale>/<obsolete>
   ============================================================
   ```
3. **Handoff suggestions:**
   - If proposals exist: `Next: /skill-authoring-workflow` to review + author
   - If stale > threshold: `Consider: manual prune of .claude/learnings.json`

---

## CRITICAL RULES

- MUST run STEP 1.5 PREFLIGHT before any dispatch and BLOCK with `WORKER_REGISTRY_NOT_LOADED` if a required sub-skill or worker agent (on the path being run) is missing/undispatchable. Provisioning does not always resolve dependency closures, so this skill can be present without its workers.
- MUST run at T0 — skill body is injected into user's session. Dispatching
  this as a worker strips `Agent` at runtime and the STEP 2a/3a worker
  dispatches silently inline (2026-04-24 platform failure mode).
- MUST NOT dispatch `learning-self-improvement-master-agent` (deprecated
  2026-04-25, 2-cycle window).
- MUST enforce 3+ evidence threshold for skill proposals — reactive
  curation policy (rule-curation.md). A single correction is NOT a pattern.
- MUST NOT auto-promote proposals into `.claude/skills/` — all proposals
  go to `.claude/skill-proposals/` for user review.
- MUST surface stale knowledge (> 90 days) in the report — untreated stale
  knowledge actively misleads future sessions.
- MUST NOT skip STEP 4 knowledge_test in `full` mode — stale knowledge is
  worse than no knowledge.
- MUST write `.workflows/learning-self-improvement/state.json` +
  `events.jsonl` after every step transition.
