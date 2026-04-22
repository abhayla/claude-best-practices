---
name: e2e-visual-run
description: >
  Run a full Playwright E2E suite with queue-based orchestration, per-test
  screenshot capture, dual-signal visual verification (ARIA snapshot +
  screenshot AI diff), and confidence-gated auto-healing. Thin skill wrapper —
  dispatches `e2e-conductor-agent` (T2) which coordinates `test-scout-agent`,
  `visual-inspector-agent`, and `test-healer-agent` (T3). Auto-detects the
  Playwright config and dev server for zero-config execution. Playwright-only —
  NOT for Cypress/Selenium/Detox/Flutter (use their native runners), one-off
  screenshot comparison (use /verify-screenshots), post-change targeted
  verification (use /auto-verify), or E2E best practices reference (use
  /e2e-best-practices).
triggers:
  - run e2e with screenshots
  - e2e visual verification
  - run e2e suite visually
  - visual e2e test run
  - e2e dual-signal verification
  - run e2e with auto-healing
type: workflow
allowed-tools: "Agent Read"
argument-hint: "[section-name] [--update-baselines]"
version: "4.0.0"
---

# /e2e-visual-run — Thin Wrapper

This skill is the user-facing slash-command entry point for the Playwright
E2E pipeline. All orchestration logic lives in `e2e-conductor-agent` (T2).

For the full queue model, dual-signal verdict matrix, healing strategy,
retry budget rules, baseline-update semantics, state schema, and first-run
artifact handling, **see `core/.claude/agents/e2e-conductor-agent.md`**.

## STEP 1: Parse Arguments

Extract from `$ARGUMENTS`:

| Argument | Meaning |
|----------|---------|
| *(none)* | Full pipeline over all tests |
| `<section-name>` | Full pipeline filtered to tests matching section (describe title / test title substring / @tag / file path) |
| `--update-baselines` | Baseline-update mode — capture screenshots + regenerate ARIA YAML; skip verification + healing |
| `<section-name> --update-baselines` | Baseline-update restricted to section |

Record the parsed arguments. If `--update-baselines` is present without a
section, the update applies to all tests.

## STEP 2: Dispatch `e2e-conductor-agent`

```
Agent("e2e-conductor-agent", prompt="
  Run the E2E pipeline in standalone mode.

  Mode: standalone
  Section filter: {section-name or null}
  Baseline update: {true | false}

  Read config/e2e-pipeline.yml for retry budget, batch size, confidence
  thresholds, and flakiness history settings.

  Drain test_queue → verify_queue → fix_queue (unless --update-baselines,
  which skips verify/heal). Write results to test-results/e2e-pipeline.json
  and evidence to test-evidence/{run_id}/.
")
```

## STEP 3: Translate Return Contract to User-Facing Report

The conductor returns a structured contract (see `e2e-conductor-agent.md`
"Return Contract" section). Render as:

```
E2E Pipeline: {result}
  Framework: playwright
  Mode: standalone
  Tests: {total} total | {passed} passed | {healed} healed | {known_issues} known issues
  Duration: {duration}
  Retries: {used}/{starting} used
  Evidence: test-evidence/{run_id}/

  {known_issues section if any}
  {expected_changes section if any}
  {first_run_artifacts section if any}
```

If the result is `NEEDS_REVIEW` (any `expected_changes`), the report MUST
surface the reminder:

> Run `/e2e-visual-run --update-baselines` to approve intentional visual changes.

If `first_run_artifacts` is non-empty (config edits, fixture creation, new
baselines), list the files and remind the user they are uncommitted:

> First-run artifacts have been created but not committed. Review via
> `git status` and commit intentionally.

## CRITICAL RULES

- MUST dispatch `e2e-conductor-agent` — do NOT reimplement queue logic here
- MUST pass `mode: standalone` in the dispatch prompt — the agent uses mode
  to pick the state-file path and cleanup policy
- MUST NOT modify test files, baselines, config, or state directly — only the
  agent (and its T3 workers) are authorized to mutate test-pipeline artifacts
- MUST surface `first_run_artifacts` and `expected_changes` in the final
  report — these are the two categories that need user review
