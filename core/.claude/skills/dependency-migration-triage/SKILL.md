---
name: dependency-migration-triage
description: Triage the TEST-SUITE failures a dependency upgrade, removal, or framework migration surfaces — snapshot the failure set, cluster by error signature, classify each cluster (masked quirk vs latent real bug vs genuine incompatibility), and fix in waves with full-suite re-runs. Use when a dep bump/removal/migration turns tests red at scale (5+ failures), before fixing anything test-by-test. NOT for production incidents or runtime outages (use /incident-response or /systematic-debugging); a single known failure with a retest command goes to /fix-loop.
version: "1.0.0"
type: workflow
triggers:
  - /dependency-migration-triage
  - "the upgrade broke a bunch of tests"
  - "test failures after removing the mocking library"
  - "triage the migration failures"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
argument-hint: "<dependency-change> [test-command]"
---

# Dependency Migration Triage

A dependency change fails tests in CLASSES, not instances — but the classes reveal themselves in
waves. One recorded migration (removing a mocking framework) took four sequential PRs because
each wave's fix uncovered the next class: first the below-fold UI assertions the old framework
had tolerated, then 13 test classes structurally coupled to it, then 29 latent test bugs the old
framework's quirks had been masking. Triage first, and the waves become a plan instead of four
surprises.

## STEP 1: Snapshot the Failure Set Before Touching Anything

Run the FULL suite once and capture the complete failure inventory:

```
BASELINE SNAPSHOT
Change:          <dep + from→to version, or removal>
Command:         <the full-suite command>
Failures:        <N> failing / <M> errors (collection/import errors counted separately)
Signature list:  <error-type × count, e.g. "MockNotFoundError × 13, AssertionError(scroll) × 9">
```

Collection/import errors mask everything behind them — a file that fails to import hides all its
tests, so the true failure count is unknown until those clear. Note this in the snapshot.

Fewer than ~5 failures? Skip the ceremony — route straight to `/fix-loop` (known retest command)
or `/systematic-debugging` (unclear cause); this skill's clustering pays off only at scale.

## STEP 2: Cluster by Error Signature, Not by Test File

Group failures by the ERROR (exception type + message shape + failing layer), not by where they
live. One signature ≈ one root cause ≈ one fix pattern. A file-by-file pass fixes the same cause
twenty times and misclassifies the stragglers.

When traces are opaque (minified bundles, swallowed exceptions, bare timeouts), fall back to
coarser signatures — group by test file/module + failure phase (setup vs assertion vs teardown) —
and un-opaque the top cluster first (sourcemaps on, verbose flag) before classifying it.

## STEP 3: Classify Each Cluster

| Class | Meaning | Treatment |
|---|---|---|
| **Masked quirk** | The OLD dependency's behavior (lenient mock, auto-scroll, silent coercion) let a wrong test pass; the test was never valid | Fix the TEST to assert reality — the failure is the truth arriving |
| **Latent real bug** | The old dep masked a genuine product defect that now shows | Fix the PRODUCT code; the migration gets credit for the find — file it as its own bug, don't bury it in the migration PR |
| **Genuine incompatibility** | The new version's API/semantics differ; code or test needs migration | Apply the documented migration pattern cluster-wide in one pass |
| **Structural coupling** | Tests are architecturally bound to the old dep (base classes, shared fixtures) | Refactor the shared layer once; the cluster's tests follow |

The classification decides WHO gets edited (test vs product vs shared infra) — misclassifying a
latent real bug as a quirk "fixes" it by weakening the test.

## STEP 4: Fix in Waves, Full Suite Between Waves

Work clusters in dependency order: import/collection errors first (they unmask the rest), then
shared-infra refactors, then leaf clusters. After EACH wave, re-run the FULL suite — expect new
clusters to surface as blockers clear (plan for waves; the recorded case had four). Update the
snapshot's signature list each wave so progress is measurable.

A large wave (e.g. 30+ unmasked collection errors) gets sub-clustered by the same STEP 2 rule
before fixing — one wave can legitimately contain several signatures. Termination rule: the loop
ends when a full-suite run surfaces ZERO new signatures AND every known cluster is classified
and either fixed or filed; a wave that only shrinks counts within known clusters is progress,
not a new wave.

## STEP 5: Report Per-Cluster Outcomes

Locked output — end the migration with:

```
MIGRATION TRIAGE RESULT
Change:    <dep change>
Waves run: <N>
| Cluster (signature) | Count | Class | Treatment | Status |
|---|---|---|---|---|
Latent real bugs found: <list of filed issues — these outlive the migration>
Suite state: <final full-suite result>
```

## MUST DO

- Always run the FULL suite for the baseline and between waves, not the failing subset — Why:
  clusters surface in waves; a subset re-run declares victory one wave early
- Always separate collection/import errors from assertion failures in the snapshot — Why: they
  hide unknown failures behind them and must clear first
- Always file latent real bugs as standalone issues even when fixed in the migration PR — Why:
  a product defect recorded only as a test-migration commit is invisible to future diagnosis
- Always fix a cluster with ONE pattern applied cluster-wide — Why: per-test improvisation on a
  shared root cause produced inconsistent fixes that themselves became test debt

## MUST NOT DO

- MUST NOT classify or fix any cluster before the STEP 1 full-suite baseline snapshot exists —
  Why: without the baseline, wave progress is unmeasurable and "new" failures can't be told from
  pre-existing ones
- MUST NOT weaken or delete a failing assertion to make a cluster pass — classify it first via
  STEP 3 — Why: a "masked quirk" misread as noise deletes the only signal of a latent real bug
- MUST NOT fix test-by-test in file order — cluster first — Why: the recorded 4-PR chain is the
  cost of discovering classes one straggler at a time
- MUST NOT mix product-code fixes and test-migration fixes in one opaque commit — separate or
  label them — Why: reviewers cannot audit whether a "test fix" actually changed product behavior
- MUST NOT declare the migration done while any cluster is unclassified — Why: an unclassified
  cluster is by definition an unknown risk, not a residual detail
