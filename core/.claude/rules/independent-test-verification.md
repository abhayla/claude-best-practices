# Scope: global

# Independent Test Verification — the blind second tester

version: "1.0.0"

Whenever an agent OR a process performs **testing** that emits a pass/fail
verdict (E2E, UI verification, a data-entry/persistence run, a browser-driven
check), that verdict MUST be independently re-checked by a **separate agent
that has NO context of how the first test ran** — given the **same inputs plus
the raw evidence** (not the first agent's conclusions). The first verdict is
**not accepted** until the blind verifier concurs.

This is the testing-specific, context-isolated form of the supervisor gate in
`supervisor-verification.md`. It does not replace it — it makes the
"independent reviewer in a fresh context" mandatory and automatic for every
non-trivial test run.

## Why (the principle)

An agent that ran a test is the worst judge of whether its own test was
adequate — it is anchored to its own plan, inherits its own blind spots, and
reads its own "PASS" as truth. Independent verification & validation
(IEEE-1012) separates *doer* from *checker* precisely to break that bias. A
verifier with a **clean context** and the **same raw inputs** catches: coverage
gaps (screens/controls the doer never exercised), evidence that does not
actually support the verdict (a green exit code over a blank screen), and
unjustified "PASS" claims.

## The two roles

| Role | Context | Gets | Produces |
|---|---|---|---|
| **Tester** (doer) | its own | the test scope / requirements | raw evidence (screenshots, ARIA, console, DOM, persisted data) **+** a verdict |
| **Blind Verifier** | **fresh — no knowledge of the tester's run, reasoning, or narrative** | the **same** scope/requirements **+** the tester's raw **evidence** (not its conclusions stated as fact) | an **independent** judgment: coverage-complete? evidence supports the verdict? + concur / dissent with specifics |

## How (single-level dispatch)

Hub workers stay flat by the single-level convention (`agent-orchestration.md`
§2), so the T0 orchestrator runs **both** waves itself:

1. **Tester wave** — run/dispatch the test; write evidence to disk; return a
   compact verdict contract.
2. **Blind-verifier wave** — dispatch a SEPARATE agent in a fresh context whose
   prompt is `{original requirements + evidence paths + rubric}` and explicitly
   **excludes** the tester's reasoning/verdict-as-fact. It returns
   `{coverage_complete, verdict_correct, dissents[], confidence}`.
3. **Reconcile** — accept only when the verifier concurs; otherwise re-run or
   widen coverage and repeat. Keep both returns compact (verdicts + evidence
   paths, not raw bytes) so the orchestrator context stays lean.

## CRITICAL RULES

- MUST have every non-trivial test verdict re-checked by a **separate,
  context-blind** agent given the same inputs + raw evidence — never the same
  agent, never the orchestrator's summary alone.
- MUST keep the verifier **isolated** from the tester's reasoning and
  **adversarial** — prompted to find what the test missed, not to bless it. A
  rubber-stamp "looks good" is verification theater and does not satisfy this rule.
- MUST judge **both** axes: coverage (did it exercise every required
  screen/control/scenario) AND verdict-correctness (does the evidence actually
  support pass/fail — see `output-plausibility-verification.md`).
- MUST apply this to the orchestrator's OWN test runs too — whoever ran the
  test is never its sole verifier.
- MUST NOT accept/report a test as passed while the verifier dissents —
  reconcile first. MUST surface any skip verbatim ("independent test
  verification SKIPPED because X"); a skip BLOCKS the verified claim.
