---
name: weakened-test-hunter
description: Verify a claimed fix did not go green by weakening its tests — re-run the claimed checks, diff every test change against the pre-change baseline, and classify each loosened/deleted assertion as legitimate (spec-backed) or weakening. Returns VERIFIED / CAVEATS / REFUTED (or INCONCLUSIVE when the baseline cannot be made to run). Use before accepting any "tests pass now" claim on a change that touches test files, and in review gates on fix PRs. Complements /auto-verify (which catches zero-test vacuous greens); this catches non-zero-but-defanged greens.
version: "1.0.0"
type: workflow
triggers:
  - /weakened-test-hunter
  - "did the fix weaken the tests"
  - "verify the tests weren't gutted"
  - "check for deleted assertions"
  - "did they nerf the checks to make it pass"
  - "audit the test changes in this diff before merge"
  - "why did the known-failures list grow"
argument-hint: "<pr-number | commit-range | 'working-tree'> [claimed-check-command]"
allowed-tools: Read, Grep, Glob, Bash
---

# Weakened-Test Hunter

A fix can turn CI green two ways: by repairing the code, or by reducing what the tests demand.
The second way survives every existing gate — the suite runs, counts are non-zero, exit code is 0 —
because the gate trusts the tests, and the tests were the thing edited. Recorded instances of the
class: a normalization helper that silently accepted a broken YAML form as equivalent (masking a
real discovery failure), and a grandfather list that quietly grew instead of shrinking. This skill
is the dedicated hunt for that class, run on a change AFTER its author claims "tests pass".
The non-negotiable that makes it work: **re-run every claimed check yourself — a pasted or
described test run is never evidence here**, because a misleading green is exactly what is being
hunted.

## STEP 1: Establish the Claim and the Diff Scope

1. Resolve the change under audit: a PR number (`gh pr diff <n>`), a commit range
   (`git diff <base>..<head>`), or `working-tree` (staged + unstaged vs `HEAD`).
   Fallbacks: if the ref/range does not resolve, STOP and report the unresolvable target —
   never guess a base. If `gh` is unavailable or unauthenticated for a PR target, ask for the
   equivalent commit range (or fetch the PR ref via plain git: `git fetch origin pull/<n>/head`).
2. Record the CLAIM being audited: what was said to be fixed, and what check was said to pass
   (exact command if given; otherwise the project's standard suite command). If a user-supplied
   check command differs from the project's CI gate command, run the PROJECT's command — and note
   the divergence in the output block.
3. Identify the pre-change baseline ref (`<base>`, or `HEAD` for working-tree). Every comparison
   below is against this baseline — never against memory of what the tests "used to" say.
4. Collect the spec sources the STEP 4 classification will cite: for a PR — `gh pr view <n>
   --json body,comments` plus any linked issue; for a commit range — the commit messages and any
   plan/issue they reference; for working-tree — the task's issue, plan file, or written
   requirement. If NO spec source exists at all, say so now: every changed assertion will then
   default to Weakening in STEP 4.

## STEP 2: Re-run the Claimed Check — and Compare Counts

1. Run the claimed check yourself at the head state. Record the exact command, exit code, and
   the collected / passed / failed / skipped counts. A reported transcript is not evidence; only
   your own run is.
2. Run the SAME check at the baseline ref — in a TEMPORARY WORKTREE, never by mutating the tree
   under audit: `git worktree add <tmpdir> <base>`, run there, then `git worktree remove <tmpdir>`.
   A worktree materializes only TRACKED files — replicate the runtime environment before trusting
   its result (run the project's install step, or link/copy untracked deps: `node_modules`, venv,
   `.env`, generated config). If worktree creation is impossible (e.g., not a git checkout), a
   `git stash` fallback is allowed ONLY with an immediately-verified restore: `git stash` → run →
   `git stash pop` → confirm `git status` matches the pre-stash state BEFORE the audit proceeds.
3. **Cost bound**: if the full suite is impractical to run twice (long-running, external deps),
   scope BOTH runs to (a) the test files touched by the diff PLUS (b) every test that imports or
   exercises the changed source modules — found via the import graph or a grep for the module
   names across the whole test tree, NOT just each module's dedicated test file. If a changed
   module is shared/widely-imported (lives on a common path, or more than ~10 test files reach
   it), scoping is NOT safe — fall back to the full run: collateral weakening through a shared
   helper surfaces only in tests outside the diff's neighborhood. State in the output block
   whether scoping was applied, the scope rule used, and what was excluded. An unbounded hang is
   not a more honest audit — but neither is a scope that cannot see the regression.
4. The count deltas are the first-order signal:
   - **Collected count dropped** → tests vanished; every disappearance must be located in STEP 3.
   - **Skipped count rose** → tests silenced; same requirement.
   - Distinguish HOW the baseline run ended: a test that RAN and asserted-failed is EXPECTED for
     a genuine fix (the bug's test should fail before the fix) — note which tests flipped
     red→green; those are the fix's claimed proof and get extra scrutiny. A baseline that FAILED
     TO EXECUTE (import/collection error, runner crash, missing deps, 0 tests collected) is
     INCONCLUSIVE, never "expected" — fix the environment (STEP 2.2) and re-run before any
     verdict; a VERIFIED/CAVEATS/REFUTED issued over an inconclusive baseline is itself a
     manufactured green. If the baseline genuinely cannot be made to execute after remediation
     (unavailable external service, missing credential, uninstallable toolchain), stop and
     report the STEP 5 INCONCLUSIVE outcome — same stop-and-report discipline as STEP 1.1.

## STEP 3: Assertion Archaeology on the Test Diff

Diff only the test surface (test files, fixtures, snapshots, suite/config lists, CI baselines).
Hunt each pattern; record every hit with `file:line`:

1. **Deleted** test files or test functions.
2. **Silenced** tests: skip/expected-failure/exclusive markers added (pytest `@pytest.mark.skip` /
   `xfail`, Jest/Mocha `.skip` / `.only`, JUnit `@Disabled`, Go `t.Skip`), or a test renamed/moved
   so the runner or a targeted command no longer collects it.
3. **Removed assertions** inside surviving tests (assert count per test dropped).
4. **Loosened expectations**: exact → range, equality → truthiness/containment
   (`toBe`→`toBeDefined`, `assertEqual`→`assertIn`), tolerance/delta widened, regex generalized.
5. **Error paths swallowed**: `raises`/`toThrow` assertions removed; try/except added around asserts.
6. **Real calls mocked out**: a previously-exercised integration point replaced by a stub/mock in
   the test path (the test now proves the mock, not the code).
7. **Snapshots regenerated in bulk**: for each changed snapshot hunk, verify the new content
   against the specified behavior of its source; any hunk that cannot be tied to an intended
   behavior change is a hit.
8. **Flakiness papered over**: retries, sleeps, or timeout increases that convert a failing signal
   into an eventually-green one.
9. **Baseline/grandfather growth**: an allowed-failures / known-flaky / grandfather list GAINED
   entries (these lists only ever shrink legitimately).
10. **Normalization widened**: a comparison helper or fixture-loader made MORE permissive, so
    previously-distinct wrong values now compare equal.

## STEP 4: Classify Each Hit — Legitimate or Weakening

For every hit, demand a SPEC CITATION from the sources collected in STEP 1.4: the issue, plan,
PR body, or requirement line that says the expected behavior itself changed. Apply the test:

- **Legitimate**: the assertion changed because the SPECIFIED behavior changed, and the hit points
  to that spec line. The new assertion is as strong as the old one against the new spec.
- **Weakening**: the only justification that exists is the previously-failing run itself
  ("updated test to match new behavior" with no spec behind the new behavior), or the new
  assertion accepts outputs the old one correctly rejected. No spec source found in STEP 1.4 →
  Weakening by default.

"The test was wrong" is a valid claim only with evidence the OLD assertion contradicted the spec —
otherwise it is the definition of weakening.

## STEP 5: Verdict

- **VERIFIED** — claimed check re-ran green under your own hands, count deltas fully explained,
  zero unexplained hits from STEP 3.
- **CAVEATS** — hits exist but every one classified Legitimate with its spec citation listed.
  Report each so a human can spot-check the citations.
- **REFUTED** — any hit classified Weakening: the green is manufactured and the underlying defect
  must be presumed alive. Name the specific weakened assertion(s) and the output the old test
  would have rejected. Route the change back through `/fix-loop` with the ORIGINAL assertions
  restored as the retest gate.
- **INCONCLUSIVE** — the baseline could not be made to EXECUTE after remediation (STEP 2.4), so
  no before/after comparison exists. Report what was attempted and what blocked it, escalate to
  a human, and issue NO pass/fail judgment — an audit that couldn't run is not an audit that
  passed.

Output block: `Claim:` / `Re-run:` (command, exit, counts before→after; note command divergence
and any cost-bound scoping from STEP 2) / `Hits:` (numbered, pattern class + file:line +
classification + citation) / `Verdict: VERIFIED|CAVEATS|REFUTED|INCONCLUSIVE` + one-line reason.

## CRITICAL RULES

- MUST re-run the claimed check yourself; MUST NOT accept a pasted or described test run as
  evidence — the class being hunted is precisely a misleading green.
- MUST diff against the pre-change baseline ref, and MUST explain every collected/skipped count
  delta between baseline and head — an unexplained disappearance is a REFUTED, not a shrug.
- MUST NOT mutate the tree under audit to obtain the baseline: temporary worktree first; stash
  fallback only with a verified same-turn restore.
- MUST bound the re-run cost (STEP 2.3) rather than hang on a slow suite — and MUST disclose the
  scoping applied. MUST NOT scope the re-run when a changed module is shared/widely-imported —
  full run only.
- MUST NOT issue VERIFIED/CAVEATS/REFUTED over a baseline that failed to EXECUTE (env/collection
  error) — an inconclusive baseline is resolved first, never classified as an expected pre-fix
  failure; if unresolvable after remediation, the verdict IS `INCONCLUSIVE` (STEP 5) — escalate,
  never force one of the other three.
- MUST NOT accept "updated test to match new behavior" without a spec citation for the new
  behavior; the failing run itself is never a spec.
- MUST treat growth of any allowed-failures / grandfather / known-flaky list as a hit.
- REFUTED verdicts MUST name the exact weakened assertion and what it would have caught — a
  refutation the author can act on, not a vibe.
- Read-only on the change under audit: this skill reports; restoring assertions and re-fixing
  belongs to `/fix-loop` / `/debugging-loop`.
