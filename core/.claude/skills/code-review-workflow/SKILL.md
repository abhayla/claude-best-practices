---
name: code-review-workflow
description: >
  Run pre-merge quality gates, create PR, and handle review feedback as a
  skill-at-T0 orchestrator (Phase 3.4 of subagent-dispatch-platform-limit
  remediation). The skill body IS the orchestrator — it runs in the user's T0
  session, invokes quality sub-skills (/review-gate, /request-code-review,
  /receive-code-review) via Skill(), and optionally dispatches
  code-reviewer-agent + security-auditor-agent workers via Agent() at T0
  when the run needs agent-level audits. For just quality gates without PR,
  use /review-gate. For just PR creation, use /request-code-review.
type: workflow
triggers:
  - code review
  - prepare for review
  - pre-merge review
  - review and create PR
  - run quality gates and PR
  - full review pipeline
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<branch name, 'current', or review scope description>"
version: "2.3.0"
---

# /code-review-workflow — Skill-at-T0 Orchestrator

This skill's body is injected into the user's T0 session and executed there.
The retired `code-review-master-agent` is NOT dispatched (deprecated
Phase 3.4, 2026-04-25); its orchestration lives here.

**Why skill-at-T0:** Same platform constraint as Phases 3.1–3.3 — dispatched
subagents don't receive the `Agent` tool
([Anthropic docs](https://code.claude.com/docs/en/sub-agents)). The legacy
master agent's chain would silently inline agent-level audits.

**Critical:** Quality gates MUST NOT be bypassed. Auto-fix for blocking
findings requires explicit user confirmation.

**Input:** `$ARGUMENTS` — branch name, `current`, or review scope.

---

## CLI Signature

```
/code-review-workflow <branch | 'current' | scope description>
                      [--no-pr] [--auto-fix] [--deep-audit]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--no-pr` | off | Stop after STEP 2 QUALITY_GATES; don't create PR |
| `--auto-fix` | off | Attempt auto-fix for blocking findings before escalating to user |
| `--deep-audit` | off | Dispatch code-reviewer-agent + security-auditor-agent in STEP 2b for agent-level audit beyond the /review-gate skill's checks |
| `--nested-verify` | off | (Requires `--deep-audit`.) Run STEP 2b dimension audits as **dual-mode nested orchestrators**: each audit spawns one adversarial verifier subagent per finding (depth-2) to refute-or-confirm BEFORE returning, so only confirmed findings reach T0. Default keeps the flat single-level parallel-sibling dispatch. See STEP 2b "Nested-verify mode". |

---

## STEP 1: INIT

1. **Parse args.** Default scope is `current` branch vs `main`.
2. **Read config.** `.claude/config/workflow-contracts.yaml (hub repo: config/workflow-contracts.yaml; if absent, use the inline steps below — this skill is self-contained)` → `workflows.code-review`.
   `master_agent` should be null; `sub_orchestrators` empty (Phase 3.4 shape).
3. **Generate `run_id`.** `{ISO-8601}_{7-char git sha}` with `:` → `-`.
4. **Initialize state** at `.workflows/code-review/state.json` (schema 2.0.0):
   `step_status: {INIT: done, QUALITY_GATES: pending, DEEP_AUDIT: pending,
   CREATE_PR: pending, HANDLE_FEEDBACK: pending}`, `dispatches_used: 0`,
   `deferred_items: []`.
5. Append INIT event to `events.jsonl`.

---

## STEP 1.5: PREFLIGHT (dependency-closure gate — BLOCK on missing workers)

Before any dispatch, verify the runtime closure this workflow needs is present
AND dispatchable. Pattern provisioning copies by tier and may not resolve a
skill's full closure, so a project can have this skill without its workers — a
silent inline run or a mid-dispatch crash is the failure this gate prevents.

- **Required sub-skills** (invoked via `Skill()`): `review-gate`, `request-code-review`, `receive-code-review`. Check each exists at
  `.claude/skills/<name>/SKILL.md` (only those on the path you will actually run).
- **Required worker agents** (dispatched via `Agent()`): `code-reviewer-agent`, `security-auditor-agent` (when `--deep-audit` runs). File presence
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

## STEP 2: QUALITY_GATES

```
Skill("/review-gate", args="<branch or scope>")
```

`/review-gate` runs code-quality-gate, architecture-fitness, security-audit,
adversarial-review, change-risk-scoring, pr-standards. Writes
`test-results/review-gate.json` with consolidated verdict:
`APPROVED | APPROVED_WITH_CAVEATS | REJECTED`.

Gate: `verdict != "REJECTED"` — if REJECTED, transition to `step_status.QUALITY_GATES = blocked`.

If blocked AND `--auto-fix` set: attempt auto-fix for each blocking finding
via `/fix-github-issue --diff-only` OR `/fix-loop` depending on finding type.
Re-run `/review-gate` after auto-fix applies. If still REJECTED after
one auto-fix pass, escalate to user (don't loop further).

If blocked AND `--auto-fix` NOT set: surface findings + ask user how to
proceed. Do NOT proceed to STEP 3 without explicit override.

Capture verdict + deferred items into state.

---

## STEP 2b: DEEP_AUDIT (optional, `--deep-audit` flag)

Dispatch agent-level audits in parallel (one T0 message, two Agent() calls):

```
Agent(subagent_type="code-reviewer-agent", prompt="""
## Workflow: code-review deep audit
## Branch: <branch>
## Upstream: <review-gate.json path>
Audit for code smells, architectural drift, edge cases the static
analyzers miss. Return audit contract with severity-ranked findings.
""")

Agent(subagent_type="security-auditor-agent", prompt="""
## Workflow: code-review deep audit
## Branch: <branch>
## Upstream: <review-gate.json path>
Audit for security vulnerabilities (OWASP Top 10, auth flow regressions,
secret leakage, injection vectors). Return audit contract.
""")
```

Parallel via single-message dispatch. Increment `dispatches_used` by 2.
Merge findings into the state's `deep_audit` block. Re-evaluate the
APPROVED / WITH_CAVEATS / REJECTED verdict incorporating the new findings.

### Nested-verify mode (opt-in, `--nested-verify` — requires `--deep-audit`)

The DEFAULT dispatch above is flat (two parallel-sibling audits return raw findings to T0).
The known weakness: raw audit findings include false positives, and T0 must then either accept
them or serialize a second verification wave itself. `--nested-verify` adopts GA **recursive
subagents** (Claude Code v2.1.172, ≤5-level cap) to push per-finding adversarial verification
DOWN into each dimension audit — the first concrete nested-dispatch consumer in the hub
(`agent-orchestration.md` nested-consumer note).

When `--nested-verify` is set, dispatch the SAME two audits, but append `mode: nested-verify`
to each dispatch prompt. In this mode each dual-mode audit agent (depth-1):

1. Produces its raw findings (as today).
2. For EACH finding, spawns ONE adversarial verifier subagent (depth-2) prompted to **refute**
   the finding — default-to-refuted on uncertainty (`independent-test-verification.md` adversarial
   posture). Per-finding verifiers run as a single-message batch.
3. Returns ONLY findings the verifier could not refute, each tagged `verified: true` + the
   verifier's one-line rationale. Refuted findings are dropped (logged in the return as
   `refuted: <n>`).

```
Agent(subagent_type="code-reviewer-agent", prompt="""
## Workflow: code-review deep audit
## mode: nested-verify          # ← spawns depth-2 per-finding verifiers; flat if absent
## Branch: <branch>
## Upstream: <review-gate.json path>
Audit for code smells, architectural drift, edge cases. For EACH finding, spawn one
adversarial verifier subagent (depth-2) to refute it; return only the confirmed findings
with `verified: true`. Design for the 5-level cap — if Agent dispatch fails or you are at
the cap, fall back to the flat path and set `nested_verify: "fell-back-flat"` in your return.
""")
```

**Guard rails (MUST):** (a) the default (no flag) path is byte-for-byte unchanged — flat, no
nesting; (b) the audit agent's worker path MUST degrade to flat if `Agent` is unavailable
(depth-5 cap) — never silently inline; (c) increment `dispatches_used` by 2 + the count of
per-finding verifiers actually spawned, and honor the global retry budget
(`agent-orchestration.md` §5); (d) T0 still supervises the confirmed findings
(`supervisor-verification.md`) — nesting moves verification earlier, it does not remove the T0 gate.

> **Verification status:** this mode is **structurally** integrated + CI-validated; its empirical
> "does it produce better reviews / lower false-positive rate" is a SEPARATE live-run measurement,
> not yet performed. Treat the false-positive-reduction benefit as designed-for, not yet measured.

**Native cloud alternative (optional):** for an even deeper, independent pass,
the user MAY run Claude Code's native **`/code-review ultra`** (or
`/code-review ultra <PR#>` for a GitHub PR) — a multi-agent review that runs in
the cloud. It is **user-triggered and billed**, needs the Claude GitHub App, and
**cannot be launched by this workflow itself** — surface it as a recommendation,
never auto-invoke it. The local `/review-gate` (STEP 2) + this agent dispatch
remain the free, default deep audit; `/code-review ultra` is an opt-in escalation
for high-stakes changes.

---

## STEP 3: CREATE_PR

Skip if `--no-pr` OR if a PR already exists for the branch OR if STEP 2
verdict remains REJECTED.

```
Skill("/request-code-review", args="<branch>, review-report=<path>")
```

`/request-code-review` creates the PR via `gh pr create`, annotates the
diff with intent, generates review questions. Captures `pr_url` into state.

Standalone mode only — don't create PRs when the skill is invoked from a
deeper pipeline (the invoking skill can set `--no-pr` to suppress).

---

## STEP 4: HANDLE_FEEDBACK

Skip if STEP 3 was skipped (no PR).

```
Skill("/receive-code-review", args="<pr_url>")
```

`/receive-code-review` fetches review comments, categorizes by severity,
generates fix patches for batched application. This step can be long-lived
(reviewers need time to comment); the skill returns the feedback resolution
status (OPEN | PARTIAL | RESOLVED) without blocking on full resolution.

Capture resolution status + outstanding comment count into state.

---

## STEP 5: REPORT

1. **Finalize state.** Write `test-results/code-review-verdict.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "result": "APPROVED | APPROVED_WITH_CAVEATS | REJECTED | PENDING_FEEDBACK",
     "quality_gates": { "verdict": "<...>", "risk_score": <0-100>,
                        "deferred_items": <n> },
     "deep_audit": { "executed": <bool>, "additional_findings": <n> },
     "pr": { "created": <bool>, "url": "<or null>" },
     "feedback": { "status": "<OPEN|PARTIAL|RESOLVED|NONE>",
                   "outstanding_comments": <n> },
     "budget_used": { "dispatches_used": <n> },
     "finalized_at": "<iso>"
   }
   ```
2. **Dashboard:**
   ```
   ============================================================
   Code Review Workflow: <verdict>
     Run ID: <run_id>
     Quality gates: <APPROVED | APPROVED_WITH_CAVEATS | REJECTED>
     Risk score: <N>/100
     Deferred items: <N> (<list if any>)
     Deep audit: <YES | SKIPPED>
     PR: <url | SKIPPED | NOT_CREATED>
     Feedback: <status> (<N> outstanding)
   ============================================================
   ```
3. **Handoff suggestions:**
   - If verdict APPROVED + PR created: `Next: wait for reviewers, then /receive-code-review` to process comments
   - If WITH_CAVEATS: `Consider: /documentation-workflow` to surface the caveats in release notes

---

## CRITICAL RULES

- MUST run STEP 1.5 PREFLIGHT before any dispatch and BLOCK with `WORKER_REGISTRY_NOT_LOADED` if a required sub-skill or worker agent (on the path being run) is missing/undispatchable. Provisioning does not always resolve dependency closures, so this skill can be present without its workers.
- MUST run at T0 — skill body is injected into the user's session.
  Dispatching this as a worker strips `Agent` at runtime and STEP 2b
  `--deep-audit` parallel dispatch would silently inline.
- MUST NOT dispatch `code-review-master-agent` (deprecated 2026-04-25,
  2-version-cycle window). Orchestration inlined here.
- MUST NOT bypass quality gates. REJECTED verdict stops the workflow at
  STEP 2 unless `--auto-fix` resolves the findings OR user explicitly
  overrides. No silent "proceed anyway" path.
- MUST NOT auto-fix blocking findings without user confirmation when
  `--auto-fix` is not set. The flag is opt-in, not default.
- MUST emit both parallel Agent() calls in STEP 2b in a SINGLE T0 message.
  Splitting across messages serializes the dispatch.
- MUST keep the DEFAULT (no `--nested-verify`) STEP 2b path flat and single-level —
  `--nested-verify` is opt-in and MUST NOT change behavior when absent. When the flag IS
  set, the dual-mode audit agents MUST degrade to the flat path if `Agent` is unavailable
  (depth-5 cap) rather than silently inline, and T0 still supervises the confirmed findings
  (`supervisor-verification.md`).
- MUST preserve deferred-item TTL (14-day auto-promotion to blocker) — the
  /review-gate skill handles this; don't override.
- MUST write `.workflows/code-review/state.json` + `events.jsonl` after
  every step transition.
