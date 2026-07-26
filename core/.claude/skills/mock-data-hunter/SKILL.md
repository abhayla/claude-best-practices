---
name: mock-data-hunter
description: Sweep a codebase for hardcoded, demo, or seed data serving on PRODUCTION paths before ship — fabricated metrics, placeholder entities, future-dated records, "for MVP" fallbacks that shape-only checks never catch. Use before a deploy, when auditing a live site's data credibility, or after any incident where fake data reached users.
version: "1.1.0"
type: workflow
triggers:
  - /mock-data-hunter
  - "is any mock data shipping to prod"
  - "audit the site for fake data"
  - "hunt hardcoded demo data"
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "[path-or-url] [--include-db]"
---

# Mock Data Hunter

Shape-only verification (page renders, no console errors, tests green) is blind to the worst
data defect: content that is FABRICATED but well-formed. One audited production site was found
serving hardcoded 60/40 gain splits and 25%/15% metrics annotated `'For MVP, we'll use mock
calculations'`, demonstration trackers with fake companies and future dates, and ~28 seeded
dummy registrar rows — four sibling incidents, one class, all invisible to every automated check
the project ran. A blind reviewer's verdict on the result: "trust=2/10 — would not trust anything
else on this site."

## Prerequisites

- **Tools** — `grep` (or ripgrep).
- **Files/paths** — the `[path-or-url]` scope to sweep — defaults to the repo root when omitted.
- **Credentials/env & Services** — a DB connection (credentials + reachability) — required ONLY when `--include-db` is passed (STEP 3).
- **User inputs** — `[path-or-url]` and `--include-db` — already collectible from `$ARGUMENTS`; resolve them now rather than discovering mid-sweep.

## STEP 0: Preflight

Resolve the sweep scope from `$ARGUMENTS` (default: repo root) and confirm the path exists.
Confirm `grep` is available. If `--include-db` was passed, verify the DB connection
credentials/env vars are set and do one read-only reachability check (a cheap `SELECT 1`-style
ping) — the STEP 3 seeded-rows query needs a live connection, not a promise of one. Report any
missing path, tool, or DB credential in one consolidated list and ask the user to fix it now;
HARD-STOP only if the sweep path itself doesn't exist (a missing `--include-db` credential
degrades to skipping the DB check, noted in the STEP 5 scope line, not a hard stop).

## STEP 1: Grep Sweep the Source for Fabrication Markers

Run the marker sweep over application source (exclude `test/`, `__tests__/`, `*.test.*`,
`fixtures/`, `stories/`, `e2e/` — those are LEGITIMATE homes for fake data):

```bash
# Repeated --include flags — a quoted brace list ("*.{ts,tsx,...}") is NOT expanded by grep
# and silently matches nothing (false CLEAN). Verify the sweep finds a planted marker first.
grep -rniE "mock|demo|dummy|placeholder|fake|sample.?data|for (the )?mvp|hardcode|lorem" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.py" \
  --include="*.vue" --include="*.svelte" --include="*.dart" --include="*.kt" \
  --include="*.swift" --include="*.rb" --include="*.php" --include="*.html" <src-dirs>
```

Sanity-check the harness before trusting a clean result: plant `MOCKHUNT-CANARY` in a scratch
file inside the sweep scope and confirm the command finds it, then remove it. A sweep that can't
find the canary is broken, and its "clean" means nothing.

On large repos/monorepos, sweep per package/app directory (highest-traffic user-facing app
first) rather than the whole tree at once; record which packages were swept vs skipped in the
STEP 5 scope line — an unswept package is not a clean package.

Plus the structural suspects the word-grep misses:
- Literal metric constants in render paths (percent splits, counts, currency amounts assigned
  inline rather than fetched)
- Arrays of person/company-shaped objects in source files
- Seeded-name patterns: `Alpha|Beta|Test|Acme|Example|Foo` + entity nouns
- Future or frozen dates in data literals
- `catch`/fallback branches that substitute canned data on fetch failure (the silent demo-fallback)

## STEP 2: Trace Each Hit to Its Serving Path

For every hit, answer: does this value reach a PRODUCTION-rendered surface?

| Reaches | Verdict |
|---|---|
| Prod page/API response, presented as real | FINDING — proceed to STEP 4 classification |
| Prod surface but visibly labeled as demo/sample | FINDING (lower severity) — labels erode, and labeled fake data still pollutes scrapers/SEO/trust |
| Dev/test/storybook only | Clean — record and move on |

A fallback branch that is REACHABLE on a production path counts as reaching production even if
it has never fired — classify it as a silent demo-fallback (STEP 4), not as clean; "hasn't
happened yet" is exactly when it will.

## STEP 3: Verify Substance on Data-Backed Pages (the positive check)

The grep finds what's fake; this step proves what's real — run it EVEN WHEN STEP 1 came back
clean (fabricated constants need no suspicious vocabulary; the recorded P0s rendered perfectly
plausible numbers). With `--include-db`, extend the check into the live store itself: query for
seeded-name patterns and future-dated rows among production records (the seeded-rows class),
read-only. For each key user-facing metric/list/table, verify the rendered value JOINS to a
source-of-truth row:

1. Pick the value on the page (a metric, a top-N list entry, a directory row).
2. Locate its origin: trace the render → API/query → table/collection.
3. Confirm the row EXISTS in the live store and the value derives from it (run the query /
   call the API), not from a literal or a seeded fixture that shipped.

If a value's origin chain dead-ends in a constant, that is a STEP 4 finding even if no marker
matched — this catches fabrications the vocabulary sweep can't.

## STEP 4: Classify and File

| Class | Definition | Severity |
|---|---|---|
| Fabricated-as-real | Invented numbers/entities presented as live data | P0 — trust destroyer; file immediately, fix before any other polish |
| Seeded-rows-in-prod | Fixture/seed rows mixed into real records | P1 — pollutes real data; needs cleanup + a seed-guard |
| Labeled-demo-in-prod | Marked demo content on a production surface | P2 — schedule removal or gate behind a flag |
| Silent demo-fallback | Real fetch with canned-data fallback on error | P1 — an outage shows fake data instead of an error |

## STEP 5: Report

Locked output:

```
MOCK DATA SWEEP
Scope:    <dirs/URL swept, db included? y/n, packages skipped: [...]>
| # | Location | What it fabricates | Serving path | Class | Severity | Issue |
|---|---|---|---|---|---|---|
Substance checks: <N values traced to source-of-truth rows, M dead-ended>
Verdict: CLEAN | FINDINGS (P0: n, P1: n, P2: n)
```

Order findings by file path so repeat runs diff stably; a re-run references issues already filed
for unchanged findings instead of re-filing them.

## MUST DO

- Always run STEP 3's substance trace on the highest-trust surfaces (money, metrics, rankings)
  even when the grep sweep is clean — Why: fabricated constants need no suspicious vocabulary;
  the recorded P0s rendered perfectly plausible numbers
- Always check error/fallback branches for canned data — Why: silent demo-fallbacks pass every
  happy-path test and activate exactly when users are already having a bad time
- Always exclude test/fixture directories from findings but include them in seed-leak tracing
  (did a seed script run against prod?) — Why: the ~28 dummy prod rows came from fixtures that
  were legitimate in their own directory
- Always file P0 fabricated-as-real findings as individual issues before continuing other work —
  Why: each day fabricated data serves, measurable user trust burns ("trust=2/10")

## MUST NOT DO

- MUST NOT accept "the page renders correctly" as evidence of real data — run the STEP 3 join
  instead — Why: shape checks passed on all four recorded incidents
- MUST NOT delete suspicious data without provenance (is it a real row that looks odd, or a
  seeded fake?) — verify origin first — Why: aggressive cleanup of "obviously fake" rows has
  destroyed real records that merely matched a name pattern
- MUST NOT fix fabricated metrics by hiding the widget — replace with real data or an honest
  empty state — Why: hiding preserves the code path that fabricates, and it returns
- MUST NOT scope the sweep to the reported page only — sweep the app per STEP 1 — Why: the
  recorded incidents were four siblings of one class across different pages
