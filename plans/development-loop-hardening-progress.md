# Progress: development-loop hardening

## Session Log
- 2026-06-15 — Analysis complete; plan + findings authored. Awaiting user approval of plan before execution.

## Decisions Made
- Validate via TWO real on-disk sandboxes (Node+TS/vitest primary, Python/pytest cross-check) created OUTSIDE the hub tree, provisioned through the REAL provisioning path — to prove genericity, not a single happy path.
- Fix all defects in the HUB (`core/`) and re-provision; never patch a sandbox `.claude/` directly (would hide the real defect).

- 2026-06-15 — User amendment: provision the sandbox via the `/synthesize-project` skill (the real downstream path), making synthesize-project a SECOND unit-under-test. Report all synthesize-project issues found (blocking fixed in-hub; non-blocking reported, not bundled). Plan updated (Tasks 0.2, 2.2, 4.1, DoD co-tested note, risk R5).

- 2026-06-15 — Plan review (user asked re: /synthesize-hub + other updates). DECIDED: do NOT add /synthesize-hub here — it's the project→hub reverse direction, unrelated to running development-loop downstream; would pollute a single-purpose PR; needs its own fixture. Deferred to the separate "verify each workflow/skill" backlog. ADDED instead: Phase 3.5 coverage matrix (complexity router + flags), 3.5.2 preflight-BLOCK negative test, 3.5.3 re-run idempotency, and Task 4.1b /update-practices upgrade-path check.

## Deferred / follow-up (not this PR)
- Validate `/synthesize-hub` (project→hub flywheel) separately — needs an enrolled downstream repo with `synthesized: true` patterns.
- Verify the other 7 workflows (testing-pipeline, debugging-loop, code-review, documentation, session-continuity, learning, skill-authoring).

- 2026-06-15 — EXECUTION started (user: "Go ahead"). Phase 0–1 committed (branch chore/harden-development-loop). Phase 2 sandbox (Node+TS, node --test) created + provisioned via /synthesize-project (recommend.py path).
- 2026-06-15 — DISCOVERY (Phase 2 real run): provisioning is NOT closure-aware. `plan-executor-agent` is tiered nice-to-have, so a must-have provision shipped /development-loop WITHOUT its EXECUTE worker. Root-cause fix: implemented `_provision_dependency_closure` in recommend.py — walks each provisioned pattern's registry `dependencies` transitively and copies them regardless of tier; seeds from BOTH newly-copied AND already-present patterns so re-provision/update also completes the closure. +4 closure tests. Verified: sandbox now has plan-executor-agent after (re-)provision. This generalizes to every workflow skill, not just development-loop.

## Blockers
- (none) — execution in progress.
