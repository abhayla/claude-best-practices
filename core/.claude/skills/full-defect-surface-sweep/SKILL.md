---
name: full-defect-surface-sweep
description: Enumerate every sibling instance of a just-diagnosed root cause repo-wide BEFORE closing the bug — fix them or file explicitly-linked residual issues. Use after any root-cause diagnosis and before declaring a bug fixed; a fix without a surface sweep is a partial fix. This is the executable sweep procedure behind the bug-triage-discipline rule's sibling-audit requirement — invoke it even when no formal issue is being filed (pre-issue sweeps, data defects, config classes).
version: "1.1.0"
type: workflow
triggers:
  - /full-defect-surface-sweep
  - "are there other places with this bug"
  - "sweep for siblings of this root cause"
  - "did we fix all instances"
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "<root-cause-description> [fix-pr-or-commit]"
---

# Full Defect Surface Sweep

First fixes reliably under-cover: a harness fix that unblocked a CI sweep only to expose the same
root cause from a second angle; a data fix that repaired 85% of rows and left older edge cases;
a dependency fix that took four sequential PR waves because sibling failure classes were
discovered one at a time. The pattern is constant — the fix treats the INSTANCE that was
reported, while the CLASS lives on elsewhere. This skill runs between "root cause found" and
"bug closed".

## Prerequisites

- **Tools/CLIs:** none beyond `Read`/`Grep`/`Glob`/`Bash` — all built-in; `gh` only if STEP 4
  files a residual GitHub issue
- **Credentials/env:** an authenticated `gh` session, needed only when STEP 4 files a residual
  issue — not needed for a fix-and-sweep with no issue filing
- **User inputs & decisions:** `<root-cause-description>` and the optional
  `[fix-pr-or-commit]` reference, both supplied at invocation

## STEP 0: Preflight + Confirm the Root Cause Is Actually Isolated

**Preflight:** if this sweep is expected to file residual issues, confirm `gh auth status`
succeeds now. A missing `gh` session blocks STEP 4's issue-filing alone, never the sweep itself —
fall back to listing residuals for the user to file by hand.

This skill consumes a DIAGNOSED root cause; it cannot rescue an undiagnosed one. If the root
cause is still a hypothesis (symptoms observed, mechanism unconfirmed), run `/systematic-debugging`
first — sweeping on a misdiagnosis produces a confident "CLASS CLOSED" verdict about the wrong
class, which is worse than no sweep. Proceed only when you can state the mechanism in one
sentence and point at the `file:line` (or data predicate) that embodies it.

## STEP 1: Abstract the Instance Into a Class

Write the root cause as a class statement, stripped of the reported instance's specifics:

```
CLASS: <the mistaken assumption or defective pattern>            (not "test X fails")
DETECTABLE BY: <grep pattern / structural query / data predicate that finds candidates>
```

Example: instance = "prod-verify boots a local dev server"; class = "any Playwright project
inherits the global webServer/baseUrl block" — detectable by grepping the config for projects
lacking an override.

## STEP 2: Sweep the Whole Repo for the Class

Run the detection across ALL surfaces, not just the one that surfaced the report:

- Source code AND tests AND configs AND scripts AND CI workflows — the class does not respect
  the directory the bug was found in.
- Other CONSUMERS of the defective component: `grep` for imports/callers/config keys referencing
  it; each consumer is a candidate sibling.
- For data defects: run the predicate over the full dataset (all partitions/years/statuses),
  not the sample that exposed it.

Record every hit — zero-hit sweeps are a legitimate result and get reported as such.

## STEP 3: Classify Each Hit

| Classification | Meaning | Action |
|---|---|---|
| Same defect | The class manifests here today | Fix now if in scope, else residual issue |
| Same risk | The pattern is present but not yet failing (edge input not seen yet) | Residual issue or hardening note |
| Clean | Matches the grep but not the class on inspection | Record as inspected-clean |

## STEP 4: Fix In-Scope, File Residuals for the Rest

- Siblings cheap to fix inside the current change: fix them in the same PR.
- Siblings needing separate work: file one issue per coherent residual, each titled
  `residual: <class> — <specific surface>` and cross-linked to the fix PR — the residual list
  is part of the fix, not optional housekeeping.
- Before filing, search existing issues (open AND closed) for the same residual title/class — a
  re-run of the sweep must comment on or reference the existing residual, never file a duplicate.
- At scale (10+ hits in one class), file ONE class-level issue carrying the full hit checklist
  instead of N near-identical issues — per-surface issues are for genuinely distinct work items.
- Never silently skip a hit: unfixed + unfiled is how the class resurfaces as a "new" bug.

## STEP 5: Attach the Sweep Table to the Fix

Locked output — include this block in the fix PR/report:

```
SURFACE SWEEP
Class:      <one line>
Detection:  <the grep/query used>
Hits:       <N total>
  fixed here:      <list or count>
  residual issues: <#123, #124 ...>
  inspected-clean: <count>
Verdict:    CLASS CLOSED | CLASS PARTIALLY TREATED (residuals filed) | NO SIBLINGS FOUND
```

## MUST DO

- Always sweep before closing, not after the class re-surfaces — Why: post-hoc sweeps cost a
  full re-diagnosis; the second report of a known class is pure rework
- Always check every consumer of the defective component, not just the reporting call site —
  Why: a shared fixture/config defect fixed at one consumer kept failing at the other four
- Always run data-defect predicates over the FULL dataset — Why: an 85%-fixed dataset read as
  "fixed" until the older partitions were queried
- Always cross-link residual issues to the fix PR bidirectionally — Why: unlinked residuals
  lose their diagnosis context and get re-investigated from scratch

## MUST NOT DO

- MUST NOT declare a bug fixed from the reported instance alone — run STEP 2 first — Why:
  four documented multi-wave fix chains started exactly this way
- MUST NOT batch unrelated sibling fixes into one opaque commit — group by class with the sweep
  table instead — Why: reviewers cannot verify class closure without seeing the sweep
- MUST NOT let "same risk" hits pass without a record — file or note them — Why: today's
  not-yet-failing sibling is the next report, minus the context you have right now
- MUST NOT skip the sweep because the fix is urgent — do the fix, then sweep before closing the
  incident — Why: urgency is when partial fixes ship; the sweep is cheap relative to recurrence
