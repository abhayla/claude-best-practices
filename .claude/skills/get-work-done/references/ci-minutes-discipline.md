# CI-minutes discipline (owner Decision 2, 2026-08-18)

Extracted from `SKILL.md` STEP 5 (T-353 lean-skill trim) — the SKILL.md body keeps the
verbatim WORKER PUSH RULE mandate line (it must be copy-pasted into every dispatch); this
file holds the full evidence and the SAME-REPO LANDING BATCHING rule.

The fleet-side half of the CI-quota fix (T-190 is the repo-side half) — two codified rules:

## 1. WORKER PUSH RULE

Every worker, checker, and fix-round prompt's standing mandates gain a THIRD verbatim line,
additive to (never replacing) the WORKER-MERGE GUARD and FOREGROUND-ONLY EXECUTION lines:
"Intermediate commits (WIP, docs-only, fix-round iterations) carry `[skip ci]` ANYWHERE in
the commit message — GitHub matches the whole message, headline or body, there is no safe
placement for a push that still needs CI. ONLY the final ready-for-verification push carries
the marker NOWHERE — not the headline, not the body, not even quoted while describing this
convention." Copy this line VERBATIM into every dispatch — dispatchers do not paraphrase it.

**Measured on PR #580, 2026-08-19, same branch, two consecutive pushes:** push 1 carried the
marker as the LAST LINE OF THE BODY (headline clean) — result: ZERO workflow runs started,
`gh pr checks` reported "no checks reported", PR BLOCKED. Push 2 was an empty commit with the
marker NOWHERE — result: `Validate PR` and `Tests` both started within 45s and passed. The
quota was not the cause (Validate PR runs had completed successfully the day before). **A
prior belief that "the marker is safe in the body, only the headline suppresses CI" is
FALSE** — GitHub's skip-ci match is a substring search over the ENTIRE commit message, not
the headline alone; a fleet convention that relied on that belief has been suppressing the CI
it was meant to preserve on every push that followed it. **The consequence is why this
matters:** this repo's `validate` check is REQUIRED — a push that carries the marker
anywhere, on a commit that was meant to be validated, leaves the PR with NO checks to ever
report; branch protection blocks the merge forever and auto-merge never fires. That is
exactly what stalled PRs #577/#579 under the T-191 incident, whose headline-only diagnosis
treated the symptom and left the substring-match cause in place. Without the push-rule line
at all, each fix-round push burns a full PR CI run on top of the eventual real one; applied
correctly (marker truly absent, not just absent from the headline, on the final push), a task
costs at most ONE CI run plus the merge's own check.

## 2. SAME-REPO LANDING BATCHING

Same-repo tasks whose contracts are written within the same calendar day default to ONE
shared branch/PR/CI-run — extending the existing TRIVIAL-TASK BATCHING (STEP 5) and
WAVE-CHAINING (STEP 5) conventions; the PRE-QUEUE DEDUP GATE's "overlapping/related" outcome
is the mechanism that merges them. Named exceptions: P1 break-fixes land solo (urgency beats
batching economics); tasks with conflicting file-scopes split into separate contracts (a
shared PR can't safely hold two workers editing the same files); a checker FAIL on one
batched task holds only that task's hunks if they are separable from the rest of the batch's
diff, otherwise the whole batch re-rounds together. **Projected effect (stated honestly, not
guaranteed):** fix-loops drop from 2-4 CI runs to 1 per task; same-repo same-day batching
further reduces the PR count itself, not just the per-PR run count.
