---
name: debugging-loop
description: >
  Orchestrate the full bug resolution cycle as a skill-at-T0 orchestrator
  (Phase 3.3 of subagent-dispatch-platform-limit remediation). The skill
  body IS the orchestrator — it runs in the user's T0 session and drives:
  diagnose → fix → verify → learn. Dispatches worker agents
  (test-failure-analyzer-agent for classification, debugger-agent for
  targeted diagnosis) via Agent() at T0. Invokes sub-skills
  (/systematic-debugging, /fix-loop, /auto-verify, /learn-n-improve) via
  Skill(). For diagnosis only without fix, use /systematic-debugging
  directly; for the full loop with mandatory learning capture, use this.
type: workflow
triggers:
  - debug and fix
  - full debugging pipeline
  - resolve bug end to end
  - diagnose fix verify
  - own this bug
  - take over debugging
  - complete debug cycle
  - debug fix and verify
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<bug description, error output, or issue URL>"
version: "2.0.0"
---

# /debugging-loop — Skill-at-T0 Orchestrator

This skill's body is injected into the user's T0 session and executed there.
The retired `debugging-loop-master-agent` is NOT dispatched (deprecated
Phase 3.3, 2026-04-25); its orchestration lives here.

**Why skill-at-T0:** Same platform constraint Phase 3.1 + 3.2 documented —
dispatched subagents don't receive the `Agent` tool
([Anthropic docs](https://code.claude.com/docs/en/sub-agents),
[GH #19077](https://github.com/anthropics/claude-code/issues/19077)).
Legacy `debugging-loop-master-agent` → `debugger-agent` (T2) /
`test-failure-analyzer-agent` (T2) dispatch would silently inline.
Canonical pattern: `workflow-master-template.md` v2.0.0.

**Critical:** Full-cycle orchestrator. For diagnosis only, use
`/systematic-debugging`. Learning capture is MANDATORY — never skip.

**Input:** `$ARGUMENTS` — bug description, error output, or issue URL.

---

## CLI Signature

```
/debugging-loop <bug description | error output | issue URL>
                [--skip-verify] [--skip-learn]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--skip-verify` | off | Skip STEP 3 VERIFY (fix is trusted; e.g., trivial typo) |
| `--skip-learn` | off | Skip STEP 4 LEARN (rare; learning is normally mandatory) |

---

## STEP 1: INIT

1. **Parse args.** If empty, ask for bug description + error output.
2. **Read config.** `config/workflow-contracts.yaml` → `workflows.debugging-loop`.
   `master_agent` should be null; `sub_orchestrators` empty (Phase 3.3 shape).
3. **Generate `run_id`.** `{ISO-8601}_{7-char git sha}` with `:` → `-`.
4. **Detect input type.**
   - Issue URL (`github.com/.../issues/N`) → fetch via `gh issue view`
   - Test failure output (stack trace + test ID) → route to `test-failure-analyzer-agent`
   - Free-form description → send directly to `/systematic-debugging`
5. **Initialize state** at `.workflows/debugging-loop/state.json` (schema 2.0.0)
   with `step_status: {INIT: done, DIAGNOSE: pending, FIX: pending,
   VERIFY: pending, LEARN: pending}`, `dispatches_used: 0`, hypothesis_trail: [].
6. Append INIT event to `events.jsonl`.

---

## STEP 2: DIAGNOSE

### 2a: Failure classification (optional — only for test failures)

If input is a test failure (stack trace + test ID detected in STEP 1):

```
Agent(subagent_type="test-failure-analyzer-agent", prompt="""
## Test failure output: <raw output>
## Mode: classify
Classify into category (SELECTOR, TIMEOUT, ASSERTION_FAILURE, ...) with
recommended_action and confidence. Return analyzer contract.
""")
```

Increment `dispatches_used` by 1.

### 2b: Root-cause diagnosis

```
Skill("/systematic-debugging", args="<bug context from step 2a if any, plus original input>")
```

`/systematic-debugging` runs reproduce → isolate → hypothesize → evidence →
root cause → targeted fix proposal (but does NOT apply it). It writes
`.workflows/debugging-loop/diagnosis.json` with root_cause classification
(TIMING | STATE | CONFIG | LOGIC | EXTERNAL), confidence, hypothesis_trail,
and a proposed fix approach. Capture path into `state.artifacts.diagnosis`.

### 2c: Optional targeted diagnosis escalation

If `/systematic-debugging` returns `confidence: LOW` OR `hypothesis_trail`
has 3+ failed hypotheses:

```
Agent(subagent_type="debugger-agent", prompt="""
## Workflow: debugging-loop
## Mode: targeted_diagnosis
## Upstream: <diagnosis.json path>
## Original input: <user input>

Apply structured debugging methodology to narrow down the root cause.
Return diagnosis contract with confidence upgrade or blocker.
""")
```

Increment `dispatches_used` by 1. Merge its contract into state.

Mark `step_status.DIAGNOSE = done`.

---

## STEP 3: FIX

```
Skill("/fix-loop", args="<error output>, diagnosis=<path>")
```

`/fix-loop` iterates analyze → fix → retest up to 5 times. Each iteration
MUST try a different approach per claude-behavior.md rule 15. Reads
diagnosis.json for hints. Writes `test-results/fix-loop.json`.

Gate: `fix_result.result IN ("PASSED", "FIXED")`. If the gate fails after
5 iterations, transition to `step_status.FIX = blocked` and jump to STEP 5
with BLOCKED verdict (no VERIFY attempted on unfixed bug).

Capture fix result into `state.artifacts.fix_result`.

---

## STEP 4: VERIFY

Skip if `--skip-verify` OR fix was BLOCKED.

```
Skill("/auto-verify", args="--strict-gates")
```

Reads `test-results/auto-verify.json`. Gate: `verification.result == "PASSED"`.
If verify fails, surface the regression (means the fix introduced new issues)
and transition to `step_status.VERIFY = failed`. Don't automatically re-loop —
that's what `/test-pipeline` is for. Ask user whether to re-dispatch `/fix-loop`
with the new failure, or give up and roll back.

Capture into `state.artifacts.verification`.

---

## STEP 5: LEARN (mandatory)

Skip only if `--skip-learn`. Otherwise MUST execute even on BLOCKED outcomes —
recording what failed is as valuable as recording what worked.

```
Skill("/learn-n-improve", args="session, run_id=<run_id>, diagnosis=<path>, fix=<path>, verification=<path>, outcome=<PASSED|FAILED|BLOCKED>")
```

`/learn-n-improve` appends to `.claude/tasks/lessons.md` and/or
`.claude/learnings.json` with the error→fix→lesson pattern (per
claude-behavior.md rule 15 "After successful fix → /learn-n-improve session
to capture the error→fix→lesson pattern").

Capture learning reference into `state.artifacts.learning`.

---

## STEP 6: REPORT

1. **Finalize state.** Write `test-results/debugging-loop-verdict.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "result": "PASSED | FAILED | BLOCKED",
     "diagnosis": { "root_cause": "<category>", "confidence": "HIGH|MEDIUM|LOW",
                    "hypotheses_tested": <int> },
     "fix": { "iterations": <int>, "result": "<PASSED|FIXED|FAILED>" },
     "verification": { "result": "<PASSED|FAILED|SKIPPED>" },
     "learning": { "recorded": <bool>, "path": "<file>" },
     "budget_used": { "dispatches_used": <n> },
     "finalized_at": "<iso>"
   }
   ```
2. **Dashboard:**
   ```
   ============================================================
   Debugging Loop: <PASSED | FAILED | BLOCKED>
     Run ID: <run_id>
     Root cause: <category> (<confidence>)
     Hypotheses tested: <N>
     Fix iterations: <N>
     Verification: <PASSED | FAILED | SKIPPED>
     Learning recorded: <path>
   ============================================================
   ```
3. **Handoff suggestions** (only if PASSED):
   - `Next: /test-pipeline` — regression check across the suite
   - `Next: /code-review-workflow` — if the fix was substantive

---

## CRITICAL RULES

- MUST run at T0 — skill body is injected into user's session. Dispatching
  this as a worker strips `Agent` at runtime and the STEP 2 / 3 / 4
  dispatches silently inline (2026-04-24 platform failure mode).
- MUST NOT dispatch `debugging-loop-master-agent` (deprecated 2026-04-25,
  2-version-cycle window). Its orchestration is inlined here.
- MUST execute STEP 5 LEARN unless `--skip-learn` is explicitly set. Every
  fix, even failed or blocked ones, contributes to the shared lessons file.
  Unrecorded bugs tend to recur (claude-behavior.md rule 15).
- MUST NOT retry the same fix approach more than twice — escalate to
  `debugger-agent` via STEP 2c or transition to BLOCKED.
- MUST NOT skip VERIFY (STEP 4) on non-trivial fixes. Unverified fixes
  reaching the learning step corrupt the knowledge base with false wins.
- MUST pass upstream artifacts (diagnosis + hypothesis trail) into every
  downstream skill/agent dispatch. No step starts from scratch.
- MUST write `.workflows/debugging-loop/state.json` + `events.jsonl` after
  every step transition. Single consolidated state file per spec v2.2 §3.4.
