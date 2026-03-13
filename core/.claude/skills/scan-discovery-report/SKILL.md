---
name: scan-discovery-report
description: >
  Comprehensive report generator for scan results from GitHub, Reddit, X/Twitter,
  or any combination. Compares discovered patterns against the hub registry,
  classifies overlap vs new, scores replacement candidates, and outputs a
  structured multi-section report.
triggers:
  - scan report
  - scan results
  - discovery report
  - scan summary
  - what did the scan find
allowed-tools: "Bash Read Grep Glob Agent WebFetch"
argument-hint: "<workflow-run-ids or 'latest' or source filter: github|reddit|twitter|all>"
---

# Scan Discovery Report

Generate a comprehensive analysis report after any combination of GitHub, Reddit,
and X/Twitter scans. The report covers: what was found, what overlaps with existing
patterns, what is genuinely new, replacement candidates with pros/cons, and
actionable next steps.

**Input:** $ARGUMENTS

---

## STEP 1: Gather Scan Results

### 1.1 Identify Completed Scan Runs

```bash
# List recent scan-internet workflow runs (last 20)
gh run list --workflow=scan-internet.yml --limit=20 --json databaseId,status,conclusion,createdAt,headBranch

# List recent scan-projects workflow runs (last 20)
gh run list --workflow=scan-projects.yml --limit=20 --json databaseId,status,conclusion,createdAt,headBranch
```

If $ARGUMENTS is:
- **`latest`** — Use the most recent completed run(s) from the last 24 hours
- **`github`/`reddit`/`twitter`** — Filter to runs triggered with matching URL/topic keywords
- **`all`** — Use all completed runs from the last 7 days
- **Run ID(s)** — Use specific run IDs

### 1.2 Extract Scan Logs

For each identified run:

```bash
# Download run logs to inspect what was discovered
gh run view <RUN_ID> --log 2>&1 | head -500
```

Parse the logs for:
- URLs/topics that were scanned
- Number of patterns extracted per source
- Any dedup matches found
- PR created (if any)

### 1.3 Check for Auto-Created PRs

```bash
# Find PRs created by scan workflows
gh pr list --label "auto-scan" --state open --json number,title,createdAt,headBranch,body --limit=10
```

For each PR, read the diff to see exactly what patterns were added/modified:

```bash
gh pr diff <PR_NUMBER>
```

### 1.4 Build Discovery Dataset

From logs + PR diffs, assemble a list of discovered patterns:

```
For each discovered pattern:
  - name: string
  - type: skill | agent | rule | hook
  - source: URL or repo where found
  - source_platform: github | reddit | twitter | other
  - content_hash: SHA256 of normalized content
  - frontmatter: parsed YAML (name, description, version, tags)
  - content_snippet: first 10 lines of content
  - discovery_timestamp: ISO datetime
```

---

## STEP 2: Load Hub Baseline

### 2.1 Read Current Registry

```bash
cat registry/patterns.json
```

Parse the registry to get the full list of existing patterns with their hashes,
types, categories, versions, sources, and descriptions.

### 2.2 Read Hub File System

```bash
# Inventory all current patterns on disk
find core/.claude/skills/*/SKILL.md core/.claude/agents/*.md core/.claude/rules/*.md -type f 2>/dev/null
```

For each file, compute its content hash for comparison.

### 2.3 Build Baseline Index

```
Hub Baseline:
  total_patterns: N
  by_type: {skill: N, agent: N, rule: N, hook: N}
  by_category: {core: N, project: N, internet: N}
  hashes: {pattern_name: sha256, ...}
```

---

## STEP 3: Classify Each Discovery

For every discovered pattern, run a 4-level classification:

### 3.1 Level 1 — Exact Duplicate Check

Compare SHA256 hash against all hub pattern hashes.

```
If hash matches → classification: EXACT_DUPLICATE
  Record: matched_pattern_name, matched_source
```

### 3.2 Level 2 — Name/Structural Overlap Check

If not exact duplicate, check for structural similarity:

1. **Name match**: Does a hub pattern share the same name (accounting for stack prefixes)?
2. **Type match**: Same pattern type (skill/agent/rule/hook)?
3. **Tag overlap**: Shared tags between discovered and existing?
4. **Description similarity**: Do descriptions cover the same functionality?

```
Scoring:
  +3 points: name match (exact or prefix-normalized)
  +1 point:  type match
  +1 point:  category match
  +1 point:  per shared tag/dependency

  Score >= 3 → classification: STRUCTURAL_OVERLAP
  Record: overlapping_patterns[], overlap_score, shared_fields[]
```

### 3.3 Level 3 — Semantic/Functional Overlap Check

If structural score < 3, check if the discovered pattern covers functionality
already handled by an existing pattern with a different name:

Read the discovered pattern content and compare its purpose against existing
patterns in the same category. Look for:
- Same workflow steps with different names
- Same tools/commands used for the same purpose
- Overlapping trigger phrases

```
If functionality overlaps >= 50% → classification: FUNCTIONAL_OVERLAP
  Record: functionally_similar_patterns[], overlap_percentage, unique_parts[]
```

### 3.4 Level 4 — Genuinely New

If no overlap detected at any level:

```
classification: NEW
  Record: suggested_category, suggested_stack_prefix, uniqueness_summary
```

---

## STEP 4: Evaluate Replacement Candidates

For patterns classified as STRUCTURAL_OVERLAP or FUNCTIONAL_OVERLAP, determine
whether the discovered version is better than the existing one.

### 4.1 Comparison Criteria

| Criterion | How to Measure | Weight |
|-----------|---------------|--------|
| **Completeness** | Count workflow steps, tools used, edge cases handled | 25% |
| **Specificity** | Does it handle the target stack/domain more precisely? | 20% |
| **Recency** | Is it based on newer APIs, tools, or conventions? | 20% |
| **Error handling** | Does it handle failures, rollbacks, validation? | 15% |
| **Documentation** | Frontmatter quality, inline comments, examples | 10% |
| **Community signal** | Stars, forks, mentions, upvotes from source | 10% |

### 4.2 Score Each Candidate

For each overlap pair (discovered vs existing):

```
Comparison:
  discovered: <name> (from <source>)
  existing:   <name> (hub version <version>)

  Completeness:  discovered=7/10  existing=5/10  winner=discovered
  Specificity:   discovered=8/10  existing=6/10  winner=discovered
  Recency:       discovered=9/10  existing=7/10  winner=discovered
  Error handling: discovered=6/10  existing=8/10  winner=existing
  Documentation: discovered=5/10  existing=7/10  winner=existing
  Community:     discovered=8/10  existing=N/A   winner=discovered

  Overall: discovered=7.1  existing=6.4
  Verdict: REPLACE | MERGE | KEEP_EXISTING | KEEP_BOTH
```

### 4.3 Verdict Definitions

| Verdict | Condition | Action |
|---------|-----------|--------|
| **REPLACE** | Discovered scores >1.5 points higher overall AND covers all existing functionality | Replace hub pattern with discovered version |
| **MERGE** | Each version has unique strengths the other lacks | Merge best parts of both into an improved version |
| **KEEP_EXISTING** | Existing scores higher or is equivalent | No action; existing pattern is sufficient |
| **KEEP_BOTH** | Different enough to serve different use cases despite name overlap | Rename discovered with differentiating suffix |

---

## STEP 5: Generate the Report

Output the following structured report. Adapt section sizes based on findings
(skip empty sections, expand sections with many items).

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

## STEP 6: Output Format Selection

The report can be output in multiple formats:

| Flag | Format | Use Case |
|------|--------|----------|
| (default) | Formatted text | Terminal display, conversation output |
| `--json` | JSON | Programmatic consumption, CI pipelines |
| `--markdown` | Markdown file | Save to `docs/scan-reports/` for archival |
| `--pr-comment` | Condensed markdown | Post as comment on auto-scan PRs |

### JSON Output Structure

```json
{
  "report_version": "1.0.0",
  "generated_at": "2026-03-13T01:15:00Z",
  "scan_summary": {
    "sources_scanned": 7,
    "by_platform": {"github": 3, "reddit": 2, "twitter": 2},
    "total_discovered": 12,
    "by_type": {"skill": 8, "agent": 2, "rule": 1, "hook": 1}
  },
  "classifications": {
    "new": [
      {
        "name": "kotlin-coroutine-debug",
        "type": "skill",
        "source": "https://github.com/...",
        "platform": "github",
        "description": "...",
        "tags": ["android", "kotlin"],
        "stack_fit": ["android-compose"],
        "priority": 1
      }
    ],
    "exact_duplicates": [...],
    "structural_overlaps": [
      {
        "discovered": "android-run-tests",
        "hub_pattern": "android-run-tests",
        "overlap_score": 5,
        "verdict": "MERGE",
        "unique_to_discovered": ["..."],
        "unique_to_hub": ["..."],
        "comparison_scores": {
          "completeness": {"discovered": 7, "hub": 5},
          "specificity": {"discovered": 8, "hub": 6},
          "recency": {"discovered": 9, "hub": 7},
          "error_handling": {"discovered": 6, "hub": 8},
          "documentation": {"discovered": 5, "hub": 7},
          "community": {"discovered": 8, "hub": null}
        }
      }
    ],
    "functional_overlaps": [...],
    "replacements": [
      {
        "hub_pattern": "compose-ui",
        "replacement": "compose-ui-v2",
        "score_delta": 0.7,
        "verdict": "REPLACE",
        "risks": ["..."],
        "migration_path": ["..."]
      }
    ]
  },
  "stack_coverage": {
    "android-compose": {
      "covered": ["unit testing", "UI testing", ...],
      "upgraded": ["unit testing"],
      "new_coverage": ["gradle optimization", "coroutine debugging"],
      "open_gaps": ["ProGuard/R8", "baseline profiles"]
    }
  },
  "actions": {
    "import_now": [...],
    "merge": [...],
    "replace": [...],
    "evaluate": [...],
    "skip": [...],
    "remaining_gaps": [...]
  },
  "source_quality": [
    {
      "source": "https://github.com/...",
      "patterns_found": 5,
      "quality": "high",
      "recommendation": "add_to_watchlist"
    }
  ]
}
```

### PR Comment Format (Condensed)

```markdown
## Scan Discovery Report

**Sources:** 7 scanned (3 GitHub, 2 Reddit, 2 Twitter)
**Found:** 12 patterns (8 skills, 2 agents, 1 rule, 1 hook)

### New (3) — Ready to import
| Type | Name | Stack Fit |
|------|------|-----------|
| skill | kotlin-coroutine-debug | android-compose |
| agent | compose-preview-agent | android-compose |
| rule | gradle-kts-conventions | android-compose |

### Merge Candidates (2)
- **android-run-tests**: +3 new steps (Gradle cache, Compose helpers, Robolectric)
- **compose-ui**: +Material 3 adaptive layouts from discovered v2

### Duplicates (3) — No action
systematic-debugging, tdd, fix-loop

### Remaining Gaps
ProGuard/R8, baseline profiles, App Bundle optimization
```

---

## STEP 7: Archive the Report

If `--markdown` flag is used or the report contains actionable findings:

```bash
# Create reports directory if needed
mkdir -p docs/scan-reports

# Save report with timestamp
# Filename format: YYYY-MM-DD-{platforms}-scan.md
cat > docs/scan-reports/$(date +%Y-%m-%d)-github-reddit-twitter-scan.md << 'REPORT'
{full markdown report}
REPORT
```

Add to `.gitignore` if reports should not be committed, or commit them
for audit trail.

---

## STEP 8: Post-Report Actions

After presenting the report, offer interactive follow-ups:

```
NEXT STEPS — What would you like to do?

  1. Import all Priority 1 patterns now
  2. View full content of a specific discovered pattern
  3. Start a merge for overlap candidates
  4. Create a PR with all recommended changes
  5. Add high-quality sources to the permanent watchlist
  6. Re-scan specific sources with different parameters
  7. Save this report to docs/scan-reports/
  8. Nothing — review complete

  Choice? (1-8)
```

For each action:
- **1 (Import)**: Copy new patterns into `core/.claude/skills/`, update registry, run `generate_docs.py`
- **2 (View)**: Display full content of the selected discovered pattern
- **3 (Merge)**: Show side-by-side diff, let user pick sections from each version
- **4 (PR)**: Stage all changes, create a single PR with the report as description
- **5 (Watchlist)**: Append sources to `config/urls.yml` with appropriate trust levels
- **6 (Re-scan)**: Trigger new scan-internet.yml runs with refined parameters
- **7 (Save)**: Write report to `docs/scan-reports/` directory
- **8 (Done)**: End skill

---

## MUST DO

- Always compare discovered patterns against the FULL hub registry, not just a subset
- Always show the source platform (GitHub/Reddit/Twitter) for each discovered pattern
- Always provide both "unique to discovered" AND "unique to hub" for overlaps
- Always include risk assessment when recommending REPLACE
- Always show remaining gaps that NO source could fill
- Always offer post-report interactive actions
- Always classify by the 4-level system: exact duplicate → structural → functional → new

## MUST NOT DO

- MUST NOT recommend replacing a hub pattern without showing what would be lost
- MUST NOT skip the overlap analysis — it is the most valuable part of the report
- MUST NOT present raw diffs without interpretation and verdict
- MUST NOT ignore community signals (stars, upvotes, engagement) when scoring
- MUST NOT recommend importing patterns that conflict with existing stack prefixes
- MUST NOT generate empty sections — skip sections with 0 items
