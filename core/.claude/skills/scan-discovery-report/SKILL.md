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
version: "1.0.0"
type: workflow
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


**Read:** `references/generate-the-report.md` for detailed step 5: generate the report reference material.

## STEP 6: Output Format Selection

The report can be output in multiple formats:

| Flag | Format | Use Case |
|------|--------|----------|
| (default) | Formatted text | Terminal display, conversation output |
| `--json` | JSON | Programmatic consumption, CI pipelines |
| `--markdown` | Markdown file | Save to `docs/scan-reports/` for archival |
| `--pr-comment` | Condensed markdown | Post as comment on auto-scan PRs |


**Read:** `references/output-format-selection.md` for detailed step 6: output format selection reference material.

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
