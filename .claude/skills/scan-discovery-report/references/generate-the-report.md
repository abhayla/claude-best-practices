# STEP 5: Generate the Report

### Report Template

```
================================================================
        SCAN DISCOVERY REPORT
        Generated: {YYYY-MM-DD HH:MM UTC}
================================================================

SCAN SUMMARY
----------------------------------------------------------------
Sources scanned:        {N sources}
  - GitHub:             {N} URLs/repos
  - Reddit:             {N} URLs/subreddits
  - X/Twitter:          {N} URLs/topics
  - Other:              {N} URLs

Patterns discovered:    {total_discovered}
  - Skills:             {N}
  - Agents:             {N}
  - Rules:              {N}
  - Hooks:              {N}

Scan runs analyzed:     {N workflow runs}
Auto-PRs created:       {N} (PR #{numbers})


================================================================
SECTION 1: NEW PATTERNS (not in hub)
================================================================

These patterns are genuinely new — no overlap with existing
hub content at any level (hash, structural, or functional).

  #  | Type   | Name                    | Source        | Platform
  ---|--------|-------------------------|---------------|----------
  1  | skill  | kotlin-coroutine-debug  | github.com/x  | GitHub
  2  | agent  | compose-preview-agent   | reddit.com/r/x| Reddit
  3  | rule   | gradle-kts-conventions  | x.com/user    | Twitter
  ...

  DETAILS:

  1. [skill] kotlin-coroutine-debug
     Source:      https://github.com/user/repo/.claude/skills/...
     Platform:    GitHub
     Description: Debug Kotlin coroutine deadlocks and cancellation issues
     Tags:        android, kotlin, coroutines, debugging
     Stack fit:   android-compose (direct match)
     Suggested category: stack-specific
     Content preview:
       | Step 1: Attach coroutine debugger agent
       | Step 2: Capture coroutine dump via DebugProbes
       | Step 3: Analyze suspension points and job hierarchy
       | ...

  2. [agent] compose-preview-agent
     ...

  RECOMMENDATION: {N} new patterns ready for import.
  Priority: {count} match your registered project stacks.


================================================================
SECTION 2: OVERLAPPING PATTERNS (exists in hub)
================================================================

These patterns overlap with existing hub content. Classified by
overlap type and replacement potential.

--- 2A: EXACT DUPLICATES ({N}) ---

  Already in hub, identical content. No action needed.

  #  | Discovered Name         | Matches Hub Pattern     | Source
  ---|-------------------------|-------------------------|--------
  1  | systematic-debugging    | systematic-debugging    | github
  ...

--- 2B: STRUCTURAL OVERLAPS ({N}) ---

  Same name/type/category but different content.

  #  | Discovered              | Hub Pattern             | Score | Verdict
  ---|-------------------------|-------------------------|-------|--------
  1  | android-run-tests       | android-run-tests       | 5/7   | MERGE
  2  | tdd-workflow            | tdd                     | 4/7   | KEEP_EXISTING
  ...

  OVERLAP DETAILS:

  1. android-run-tests (MERGE recommended)
     ┌─────────────────────────────────────────────────────────┐
     │  DISCOVERED (from github.com/x)  │  HUB (current v1.2) │
     ├─────────────────────────────────────────────────────────┤
     │  Lines: 180                      │  Lines: 120          │
     │  Steps: 8                        │  Steps: 5            │
     │  Tools: Bash,Read,Agent          │  Tools: Bash,Read    │
     │  Covers: unit+integration+e2e    │  Covers: unit+integ  │
     │  Has: Gradle cache optimization  │  Missing this        │
     │  Has: Compose UI test helpers    │  Missing this        │
     │  Missing: screenshot compare     │  Has this            │
     │  Missing: flaky test retry       │  Has this            │
     └─────────────────────────────────────────────────────────┘

     Unique to DISCOVERED:
       + Gradle cache optimization for faster CI runs
       + Compose UI test helper utilities
       + Robolectric configuration for headless tests

     Unique to HUB:
       + Screenshot comparison workflow
       + Flaky test retry with exponential backoff

     VERDICT: MERGE — Combine both versions. Discovered adds
     valuable CI optimization; hub has better flaky-test handling.

--- 2C: FUNCTIONAL OVERLAPS ({N}) ---

  Different names but cover the same functionality.

  #  | Discovered              | Functionally Similar To | Overlap %
  ---|-------------------------|-------------------------|----------
  1  | kotlin-test-runner      | android-run-tests       | 65%
  ...

  DETAILS:

  1. kotlin-test-runner vs android-run-tests
     What's shared (65%):
       - Both run `./gradlew test` and parse output
       - Both handle test filtering by class/method
       - Both capture and format test results

     What's unique to kotlin-test-runner:
       + Kotest framework support (property-based testing)
       + Kotlin multiplatform test execution
       + Turbine flow testing integration

     What's unique to android-run-tests:
       + ADB device management
       + Instrumented test execution
       + Compose UI testing

     VERDICT: KEEP_BOTH — Different enough for separate use cases.
     Suggest renaming discovered to "kotlin-multiplatform-tests".


================================================================
SECTION 3: REPLACEMENT ANALYSIS
================================================================

Patterns where the discovered version may be better than the
current hub version. Ranked by improvement potential.

  Rank | Hub Pattern        | Replacement        | Score Delta | Verdict
  -----|--------------------|--------------------|-------------|--------
  1    | android-run-tests  | android-run-tests* | +1.8        | MERGE
  2    | compose-ui         | compose-ui-v2      | +0.7        | REPLACE
  3    | fix-loop           | smart-fix-loop     | -0.3        | KEEP_EXISTING
  ...

  DETAILED COMPARISON (top candidates):

  1. compose-ui → compose-ui-v2 (REPLACE recommended)

     ┌─────────────────────────────────────────────────────────┐
     │ Criterion       │ Hub (v1.0) │ Discovered │ Winner     │
     ├─────────────────────────────────────────────────────────┤
     │ Completeness    │  5/10      │  8/10      │ Discovered │
     │ Specificity     │  6/10      │  9/10      │ Discovered │
     │ Recency         │  7/10      │  9/10      │ Discovered │
     │ Error handling  │  7/10      │  7/10      │ Tie        │
     │ Documentation   │  6/10      │  8/10      │ Discovered │
     │ Community signal│  N/A       │  42 stars  │ Discovered │
     ├─────────────────────────────────────────────────────────┤
     │ OVERALL         │  6.2       │  8.2       │ Discovered │
     └─────────────────────────────────────────────────────────┘

     Why replace:
       - Discovered covers Material 3 adaptive layouts (hub doesn't)
       - Discovered has Compose Multiplatform snippets
       - Discovered includes preview annotation best practices
       - 42 GitHub stars indicate community validation

     Risk of replacing:
       - Hub version has project-specific customizations
       - 3 downstream projects currently use hub version
       - Breaking change: renamed step "Layout Setup" → "Scaffold Config"

     Migration path:
       1. Copy discovered version to core/.claude/skills/compose-ui/
       2. Preserve hub's screenshot comparison step (lines 45-62)
       3. Update registry hash and version to 2.0.0
       4. Notify downstream projects via sync workflow


================================================================
SECTION 4: PLATFORM-SPECIFIC INSIGHTS
================================================================

Patterns and signals grouped by discovery source.

--- GitHub ({N} patterns) ---
  Repos scanned: {list}
  Hit rate: {N}/{total} repos had .claude/ directories
  Top pattern types: skills ({N}), agents ({N}), rules ({N})
  Notable repos: {repos with most/best patterns}

--- Reddit ({N} patterns) ---
  Subreddits: r/ClaudeAI, r/androiddev, r/kotlin
  Threads analyzed: {N}
  Patterns extracted: {N}
  Community sentiment: {positive/mixed/negative}
  Top upvoted patterns: {list with vote counts}

--- X/Twitter ({N} patterns) ---
  Accounts: {list of source accounts}
  Posts analyzed: {N}
  Patterns extracted: {N}
  Engagement signals: {likes, retweets on pattern posts}
  Trending topics: {relevant hashtags/topics}


================================================================
SECTION 5: STACK RELEVANCE (Android/Kotlin Focus)
================================================================

How discovered patterns map to registered project stacks.

  Stack: android-compose
  ┌──────────────────────────────────────────────────────────┐
  │ Coverage Area           │ Hub Has │ Discovered │ Gap?    │
  ├──────────────────────────────────────────────────────────┤
  │ Unit testing            │ Yes     │ Yes (better)│ Upgrade│
  │ UI testing (Compose)    │ Yes     │ Yes         │ No     │
  │ E2E testing             │ Yes     │ No          │ No     │
  │ ADB debugging           │ Yes     │ Yes (same)  │ No     │
  │ Gradle optimization     │ No      │ Yes         │ NEW    │
  │ Coroutine debugging     │ No      │ Yes         │ NEW    │
  │ Compose previews        │ No      │ Yes         │ NEW    │
  │ Kotlin multiplatform    │ No      │ Yes         │ NEW    │
  │ ProGuard/R8 rules       │ No      │ No          │ OPEN   │
  │ Baseline profiles       │ No      │ No          │ OPEN   │
  │ App Bundle optimization │ No      │ No          │ OPEN   │
  └──────────────────────────────────────────────────────────┘

  Gaps filled by this scan:  4 new areas covered
  Remaining open gaps:       3 areas still uncovered


================================================================
SECTION 6: RECOMMENDED ACTIONS
================================================================

Prioritized list of actions to take based on this scan.

  PRIORITY 1 — IMPORT NOW (high value, no conflicts)
  ─────────────────────────────────────────────────────
  [ ] Import [skill] kotlin-coroutine-debug (NEW, matches stack)
  [ ] Import [agent] compose-preview-agent (NEW, matches stack)
  [ ] Import [rule] gradle-kts-conventions (NEW, matches stack)

  PRIORITY 2 — MERGE (both versions have unique value)
  ─────────────────────────────────────────────────────
  [ ] Merge android-run-tests (hub + discovered, +3 new steps)
  [ ] Merge compose-ui with discovered v2 (+Material3 support)

  PRIORITY 3 — REPLACE (discovered is strictly better)
  ─────────────────────────────────────────────────────
  [ ] Replace compose-ui with compose-ui-v2 (score: 8.2 vs 6.2)
      ⚠ Notify 3 downstream projects before replacing

  PRIORITY 4 — EVALUATE LATER (needs human judgment)
  ─────────────────────────────────────────────────────
  [ ] Review kotlin-test-runner vs android-run-tests overlap
  [ ] Assess community skill "gradle-doctor" (low signal, 2 stars)

  PRIORITY 5 — NO ACTION (duplicates or irrelevant)
  ─────────────────────────────────────────────────────
  [x] Skip systematic-debugging (exact duplicate)
  [x] Skip vue-component-gen (wrong stack)
  [x] Skip react-hooks-lint (wrong stack)

  REMAINING GAPS (not found in any source)
  ─────────────────────────────────────────────────────
  [ ] ProGuard/R8 configuration skill — still missing
  [ ] Baseline profile generation agent — still missing
  [ ] App Bundle optimization workflow — still missing
  → Consider creating these manually or adding targeted scan URLs


================================================================
SECTION 7: SOURCE QUALITY & WATCHLIST
================================================================

  Source Reliability:
  ┌──────────────────────────────────────────────────────────┐
  │ Source URL/Topic          │ Patterns │ Quality │ Action  │
  ├──────────────────────────────────────────────────────────┤
  │ github.com/user/repo-a   │ 5        │ High    │ Watch   │
  │ reddit.com/r/ClaudeAI/t1 │ 2        │ Medium  │ Watch   │
  │ x.com/user/status/123    │ 1        │ Low     │ Skip    │
  │ github.com/topics/claude  │ 0        │ N/A     │ Drop    │
  └──────────────────────────────────────────────────────────┘

  Suggested watchlist updates:
  + Add github.com/user/repo-a to config/urls.yml (trust: high)
  + Add reddit.com/r/androiddev to config/urls.yml (trust: medium)
  - Drop github.com/topics/claude from config/urls.yml (0 results)


================================================================
METADATA
================================================================
Report version:     1.0.0
Hub registry:       v{registry_version} ({total_patterns} patterns)
Scan window:        {start_date} to {end_date}
Workflow runs:      {run_ids}
Time to generate:   {duration}
================================================================
```

---

