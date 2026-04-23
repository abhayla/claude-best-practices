# Sequence Diagram — /testing-pipeline-workflow

Synthesized from:
- `core/.claude/skills/testing-pipeline-workflow/SKILL.md` (dispatch wrapper)
- `config/workflow-contracts.yaml` → `workflows.testing-pipeline` (step DAG, gates, artifacts)
- `core/.claude/agents/testing-pipeline-master-agent.md` (T1 orchestration protocol)
- `core/.claude/agents/test-pipeline-agent.md` (T2 sub-orchestrator)
- `core/.claude/agents/e2e-conductor-agent.md` (T2 sub-orchestrator, post PR #10)
- `core/.claude/agents/test-failure-analyzer-agent.md` (T3 leaf, post PR #9)
- `core/.claude/rules/agent-orchestration.md` (tier model, context passing)

Last verified against merged PRs #3–#11.

---

## Mermaid sequence diagram

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant SK as Skill: testing-pipeline-workflow
    participant T1 as T1: testing-pipeline-master-agent
    participant CFG as config/workflow-contracts.yaml
    participant ST as .workflows/testing-pipeline/state.json
    participant TDD as Skill: /tdd-failing-test-generator
    participant FL as Skill: /fix-loop
    participant AN as T3: test-failure-analyzer-agent
    participant AV as Skill: /auto-verify
    participant TE as T3: tester-agent
    participant VI as T3: visual-inspector-agent
    participant T2 as T2: e2e-conductor-agent
    participant SC as T3: test-scout-agent
    participant HE as T3: test-healer-agent (MCP)
    participant MCP as @playwright/mcp
    participant QG as Skill: /code-quality-gate
    participant PF as Skill: /post-fix-pipeline
    participant FS as test-results/*.json
    participant GH as GitHub Issues

    U->>SK: /testing-pipeline-workflow $ARGS
    SK->>T1: Agent(testing-pipeline-master-agent,<br/>Workflow=testing-pipeline, Mode=standalone)

    rect rgb(240,245,255)
    Note over T1,ST: INIT (T1 owns, standalone mode only)
    T1->>CFG: read steps, depends_on, artifacts, gates
    T1->>T1: generate run_id = ISO-8601_git-sha
    T1->>T1: rm -rf test-results/ test-evidence/<br/>.workflows/testing-pipeline/
    T1->>ST: write schema_version, run_id,<br/>global_retry_budget=15
    end

    rect rgb(245,255,245)
    Note over T1,TDD: Step tdd_red (depends_on: [])
    T1->>TDD: Skill(/tdd-failing-test-generator,<br/>ctx=user_request)
    TDD-->>T1: tests/ failing (artifact: failing_tests)
    T1->>ST: mark tdd_red PASSED
    end

    rect rgb(255,250,240)
    Note over T1,AN: Step fix_loop (depends_on: [tdd_red])
    T1->>FL: Skill(/fix-loop, ctx={<br/>failing_tests, remaining_budget})
    FL->>AN: Agent(test-failure-analyzer-agent,<br/>test_output + enriched_context*)
    AN->>AN: Pass A: regex vs test_output<br/>Pass B: regex vs enriched fields<br/>Pass C: LLM fallback
    AN-->>FL: {category, healer_category,<br/>classification_source, confidence}
    FL->>FL: apply fix, retest (≤3 iterations)
    FL-->>FS: write fix-loop.json
    FL-->>T1: result: PASSED | FIXED | FAILED
    T1->>T1: gate: result IN (PASSED, FIXED)<br/>— BLOCK if FAILED
    T1->>ST: mark fix_loop, decrement budget
    end

    par auto_verify (depends_on: [fix_loop])
        rect rgb(255,245,250)
        Note over T1,VI: Step auto_verify
        T1->>AV: Skill(/auto-verify, ctx={<br/>fix_result, remaining_budget,<br/>capture_proof: true})
        AV->>TE: dispatch tester-agent<br/>(test suite + screenshots)
        TE-->>AV: manifest.json<br/>(screenshots keyed by test)
        AV->>VI: dispatch visual-inspector-agent<br/>(dual-signal review)
        VI-->>AV: visual-review.json<br/>(overrides, flags)
        AV-->>FS: write auto-verify.json
        AV-->>T1: result + ui_tests_screenshot_verified
        T1->>T1: gate: result == PASSED
        end
    and e2e (depends_on: [fix_loop], skip_when: no_ui_tests)
        rect rgb(245,240,255)
        Note over T1,MCP: Step e2e (T1 → T2 → T3 chain)
        T1->>T2: Agent(e2e-conductor-agent, ctx={<br/>Pipeline ID, run_id, mode=dispatched,<br/>remaining_budget, state_path})
        T2->>T2: STEP 0-1: discover Playwright,<br/>start dev-server, init e2e-state.json
        T2->>T2: STEP 2: queue tests (longest-first)
        loop until queues drain or budget=0
            T2->>SC: Agent(test-scout-agent,<br/>batch of tests)
            SC-->>T2: run + screenshot + ARIA →<br/>verify_queue items
            T2->>VI: Agent(visual-inspector-agent,<br/>verify_queue)
            VI-->>T2: completed | expected_changes |<br/>fix_queue (dual-signal verdict)
            alt fix_queue non-empty
                T2->>HE: Agent(test-healer-agent,<br/>fix_queue + pre-captured errors)
                HE->>MCP: browser_snapshot,<br/>browser_console_messages,<br/>browser_network_requests
                MCP-->>HE: live enriched context
                HE->>HE: classify (regex gate → LLM),<br/>apply fix if confidence ≥ 0.85
                HE-->>T2: test_queue (re-run) | known_issues
            end
        end
        T2->>T2: STEP 4.5: archive state to<br/>.workflows/.../runs/{run_id}/
        T2-->>FS: write e2e-pipeline.json
        T2-->>T1: return contract {gate, artifacts,<br/>retry_budget_consumed, summary}
        T1->>T1: gate: status == completed
        end
    end

    rect rgb(250,255,240)
    Note over T1,QG: Step quality_gate (depends_on: [auto_verify, e2e])
    T1->>QG: Skill(/code-quality-gate, ctx=all prior artifacts)
    QG-->>FS: write code-quality-gate.json
    QG-->>T1: result: PASSED | FAILED
    T1->>T1: gate: result == PASSED
    end

    rect rgb(255,240,240)
    Note over T1,GH: T1 Aggregation (T2 agents MUST NOT duplicate)
    T1->>FS: glob test-results/*.json
    T1->>T1: union failures,<br/>screenshot verdict authority,<br/>detect contradictions
    T1->>GH: for each LOGIC_BUG / VISUAL_REGRESSION<br/>in known_issues: dedup sig, create/comment
    GH-->>T1: issue numbers
    T1->>FS: write pipeline-verdict.json
    end

    rect rgb(240,250,240)
    Note over T1,PF: Step post_fix (skip_when: mode=dispatched)
    T1->>PF: Skill(/post-fix-pipeline,<br/>only if standalone)
    PF->>PF: pre-commit guards,<br/>screenshot overrides check,<br/>commit if clean
    PF-->>T1: commit_sha
    end

    T1-->>SK: unified verdict + per-step results +<br/>UI summary + flaky report
    SK-->>U: PASSED/FAILED report with<br/>handoff to /code-review-workflow
```

---

## Supporting DAG view (parallel branches)

```mermaid
flowchart LR
    INIT[INIT: cleanup + state + run_id] --> TR[tdd_red]
    TR --> FL[fix_loop<br/>gate: PASSED or FIXED]
    FL --> AV[auto_verify<br/>gate: PASSED]
    FL --> E2E[e2e<br/>skip_when: no_ui_tests<br/>gate: completed]
    AV --> QG[quality_gate<br/>gate: PASSED]
    E2E --> QG
    QG --> AGG[Aggregate + GH Issues]
    AGG --> PF[post_fix<br/>skip_when: dispatched]
    PF --> DONE[pipeline-verdict.json]
```

---

## Key contracts (non-obvious behavior)

- **Tier rule:** T1 dispatches T2 via `Agent()`, T2 dispatches T3 via `Agent()`, T3 leaves use `Skill()` only. Max depth 4 per `agent-orchestration.md` rule #2.
- **Retry budget:** T1 owns the shared `global_retry_budget` (default 15). Every `Agent()` dispatch context includes `remaining_budget`; T2 decrements and returns `retry_budget_consumed`.
- **Screenshot authority:** Any UI test with `verdict_source: "screenshot"` + `FAILED` is blocking regardless of exit code. Applies at T1 aggregation AND at T2 conductor gate.
- **Cleanup ownership:** T1 wipes `test-results/` + `test-evidence/` at INIT in **standalone only**. Dispatched mode leaves that to T0.
- **Aggregation ownership:** Only T1 runs `pipeline_aggregator.py`. T2 agents write per-stage JSON but MUST NOT union-aggregate.
- **Enriched context (PR #9):** T2 conductor / T3 healer capture `browser_console_messages`, `browser_network_requests`, `dom_snapshot` via `@playwright/mcp` and pass them to `test-failure-analyzer-agent` in the dispatch prompt — the analyzer stays a T3 leaf with no MCP grants.
- **State archive (PR #10):** After step completion, canonical state is copied to `runs/{run_id}/` for audit; canonical path stays.

---

## Step-by-step mapping to `workflow-contracts.yaml`

| Step        | Skill / Agent                     | depends_on            | Gate expression                       | skip_when              |
|-------------|-----------------------------------|-----------------------|---------------------------------------|------------------------|
| tdd_red     | `/tdd-failing-test-generator`     | —                     | —                                     | —                      |
| fix_loop    | `/fix-loop` (dispatches analyzer) | [tdd_red]             | `fix_result.result IN (PASSED, FIXED)`| —                      |
| auto_verify | `/auto-verify`                    | [fix_loop]            | `verification.result == PASSED`       | —                      |
| e2e         | `e2e-conductor-agent` (T2)        | [fix_loop]            | `e2e_state.status == completed`       | `no_ui_tests == true`  |
| quality_gate| `/code-quality-gate`              | [auto_verify, e2e]    | `quality.result == PASSED`            | —                      |
| post_fix    | `/post-fix-pipeline`              | [quality_gate]        | —                                     | `mode == 'dispatched'` |

---

## Artifacts written per step

| Step        | Path                                                   | Schema            |
|-------------|--------------------------------------------------------|-------------------|
| tdd_red     | `tests/`                                               | `test_files_v1`   |
| fix_loop    | `test-results/fix-loop.json`                           | `test_result_v1`  |
| auto_verify | `test-results/auto-verify.json`                        | `test_result_v1`  |
| e2e         | `.workflows/testing-pipeline/e2e-state.json` (+ archive under `runs/{run_id}/`) | `e2e_v1` |
| quality_gate| `test-results/code-quality-gate.json`                  | `quality_gate_v1` |
| post_fix    | commit SHA (git only)                                  | `git_sha`         |
| Final       | `test-results/pipeline-verdict.json`                   | unified verdict   |

---

## Handoff

On `quality_gate == PASSED` the master agent suggests `/code-review-workflow` per the contract's `handoff_suggestions` — tests passing + quality verified means ready for review.
