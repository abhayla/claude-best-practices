# Docs-Only CI Short-Circuit (GitHub Actions)

Skip the heavy test/build jobs on a docs-only PR without ever leaving a REQUIRED status check
missing. Reference contract: `T-351`/`T-353` fast-lane mechanism, `plans/get-work-done-fast-lane.md`.

## The design rule (read this before copying the snippet)

**NEVER use workflow-level `paths-ignore` on a job that is a REQUIRED status check.**
`paths-ignore` prevents the *workflow run itself* from starting — GitHub's branch protection
then has no run to report a status from, so the required check sits in "Expected" forever and
the PR is blocked. A **SKIPPED job**, by contrast, still reports a conclusion (`skipped`) and
satisfies a required check — see the GitHub Actions docs: *"If a job is skipped due to a
conditional, it will report its status as 'Skipped', ... a skipped check will satisfy a branch
protection rule."* Use a first job that always runs and gates the heavy jobs with `if:`, never
`paths-ignore` on the workflow trigger.

## The snippet

```yaml
name: validate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  changes:
    runs-on: ubuntu-latest
    timeout-minutes: 1  # <60s in practice — one git diff, no checkout of history beyond fetch-depth 0
    outputs:
      docs_only: ${{ steps.check.outputs.docs_only }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # need history to diff against base/before
      - id: check
        run: |
          BASE="${{ github.event.pull_request.base.sha || github.event.before }}"
          FILES=$(git diff --name-only "$BASE"...${{ github.sha }})
          DOCS_ONLY=true
          for f in $FILES; do
            case "$f" in
              *.md|docs/*|.claude/*|LICENSE*) ;;
              *) DOCS_ONLY=false ;;
            esac
          done
          echo "docs_only=$DOCS_ONLY" >> "$GITHUB_OUTPUT"

  test:
    needs: changes
    if: needs.changes.outputs.docs_only != 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "full test suite"

  build:
    needs: changes
    if: needs.changes.outputs.docs_only != 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "full build"
```

No third-party action is required — `git diff --name-only` against the PR base SHA (or
`github.event.before` for a push) is enough. Every heavy job declares `needs: changes` +
`if: needs.changes.outputs.docs_only != 'true'` — the `changes` job itself always runs and
always reports a status, so it (not the heavy jobs) is what a required-check rule should target
if only one check can be required; if the heavy jobs are individually required, their `skipped`
conclusion still satisfies the rule per the docs sentence above.

## Two-run verification recipe

1. Push a commit that touches a code file → `changes` reports `docs_only=false` → `test` and
   `build` run in full.
2. Push a commit that touches ONLY `*.md` / `docs/**` / `.claude/**` / `LICENSE*` → `changes`
   reports `docs_only=true` and completes in under a minute → `test` and `build` show
   `Skipped`, and the PR is NOT blocked (their required-check conclusion is `skipped`, not
   missing).

Run both once per adoption to confirm the required-check name still resolves after the change —
a required check that changed job name silently un-configures the branch protection rule.
