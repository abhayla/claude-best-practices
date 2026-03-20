# STEP 7: Report

### Dashboard format

```
============================================================
                    TEST HEALTH REPORT
============================================================

SUITE OVERVIEW
  Framework:        <detected framework>
  Total tests:      <count>
  Unit:             <count>  |  Integration: <count>  |  E2E: <count>
  Unclassified:     <count>

EXECUTION
  Total time:       <duration>
  Slowest test:     <name> (<duration>)
  Tests > 5s:       <count>
  Tests > 30s:      <count>

SKIP RATE
  Skipped:          <count> (<percentage>%)
  Expected fail:    <count> (<percentage>%)
  Skip rate:        <OK | WARNING if >5% | CRITICAL if >10%>

DEAD TESTS
  Dead references:  <count>
  Orphaned fixtures:<count>
  Orphaned data:    <count>

DUPLICATES
  Duplicate tests:  <count> groups
  Redundant params: <count> cases
  Duplicate setup:  <count> blocks

SLOW TESTS (top 5)
  1. <test_name> — <duration> — <cause>
  2. <test_name> — <duration> — <cause>
  ...

RECOMMENDATIONS (by estimated impact)
  Priority  Action                           Est. Time Saved
  --------  ------                           ---------------
  HIGH      Mock HTTP calls in 12 tests      ~18s per run
  HIGH      Remove 5 dead tests              maintenance burden
  MEDIUM    Promote 3 fixtures to session     ~8s per run
  MEDIUM    Deduplicate 4 test groups         ~4s per run
  LOW       Rename 15 tests for consistency   readability
  LOW       Add pytest-xdist for parallelism  ~40% wall time

ESTIMATED TOTAL SAVINGS: <time> per CI run
============================================================
```

Present the report to the user. If `--apply` or `focus` was specified, offer to
execute the recommended changes interactively, one batch at a time.

---

