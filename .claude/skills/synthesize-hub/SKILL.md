---
name: synthesize-hub
description: >
  Collect synthesized patterns from bilateral-sync downstream projects, cluster them by similarity,
  classify as generalizable vs style vs divergent, draft generalized patterns for the hub,
  and create PRs. Run in the hub repo when you want to discover recurring conventions across projects.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[owner/repo]"
version: "1.0.0"
type: workflow
---

# Synthesize Hub — Harvest and Generalize Patterns

Collect synthesized patterns from downstream projects, find recurring conventions, and propose generalized patterns for the hub.

**Arguments:** $ARGUMENTS

If a specific `owner/repo` is provided, scan only that project. Otherwise, scan all bilateral-sync projects.

---

## STEP 1: Identify Eligible Projects

Determine which registered projects have bilateral consent for pattern sharing.

1. Read `config/repos.yml` to get the list of registered projects
2. For each project, check TWO consent flags:

   **Hub-side** — `share_synthesized: true` in `repos.yml`:
   ```yaml
   repos:
     - repo: owner/project-a
       stacks: [fastapi-python]
       share_synthesized: true    # Hub wants to scan this repo
   ```

   **Project-side** — fetch `.claude/synthesis-config.yml` from the project repo:
   ```bash
   gh api repos/{owner}/{repo}/contents/.claude/synthesis-config.yml \
     --jq '.content' | base64 -d
   ```
   Check that `allow_hub_sharing: true` is set.

3. **Both flags must be `true`.** If either is missing or `false`, skip the project silently.

4. If a specific `owner/repo` was provided as argument, only process that project (still check consent).

**Output:** A list of eligible projects with their consent settings (including `private_patterns` lists).

## STEP 2: Collect Synthesized Patterns

For each eligible project, fetch all patterns marked `synthesized: true`.

1. Clone or fetch the project's `.claude/` directory — **all three pattern types**:
   ```bash
   # Create temp directory for collection
   mkdir -p .synthesize-hub/collected

   # For each eligible project, fetch rules
   gh api repos/{owner}/{repo}/contents/.claude/rules --jq '.[].name' | while read f; do
     gh api repos/{owner}/{repo}/contents/.claude/rules/$f --jq '.content' | base64 -d \
       > .synthesize-hub/collected/{owner}__{repo}__rules__$f
   done

   # Fetch skills (each skill is a directory with SKILL.md)
   gh api repos/{owner}/{repo}/contents/.claude/skills --jq '.[].name' | while read d; do
     gh api repos/{owner}/{repo}/contents/.claude/skills/$d/SKILL.md --jq '.content' 2>/dev/null | base64 -d \
       > .synthesize-hub/collected/{owner}__{repo}__skills__${d}__SKILL.md
   done

   # Fetch agents
   gh api repos/{owner}/{repo}/contents/.claude/agents --jq '.[].name' | while read f; do
     gh api repos/{owner}/{repo}/contents/.claude/agents/$f --jq '.content' | base64 -d \
       > .synthesize-hub/collected/{owner}__{repo}__agents__$f
   done
   ```

2. Read each fetched file. Keep only patterns where frontmatter contains `synthesized: true`.

3. Exclude patterns listed in the project's `private_patterns` config.

4. Exclude patterns where frontmatter contains `private: true`.

5. For each kept pattern, record:
   - **Source project:** `owner/repo`
   - **File path:** original path in the project
   - **Frontmatter fields:** name, description, type, category, globs
   - **Content hash:** SHA256 of the full file content
   - **Content:** the full pattern text

**Output:** A collection of synthesized patterns with metadata, organized by source project.

## STEP 3: Level 1 — Hash Deduplication

Group identical patterns instantly.

1. Group collected patterns by their SHA256 content hash
2. Any group with 2+ patterns = exact duplicates across projects
3. Mark these as instant clusters — they need no further analysis
4. Record: cluster ID, member patterns, source projects

This is rare (projects customize their patterns) but handles exact copies from shared bootstrapping.

## STEP 4: Level 2 — Structural Grouping

Group remaining (non-duplicate) patterns by frontmatter signature.

1. For each pattern, create a signature from frontmatter: `(type, category, globs_scope)`
   - `type`: `rule` | `skill` | `agent`
   - `category`: extracted from description or frontmatter (correctness, safety, consistency, testing, deployment)
   - `globs_scope`: normalized file type scope (e.g., `python`, `typescript`, `all`)

2. Group patterns with matching signatures into structural groups

3. Skip any group with only 1 pattern (unique to one project — nothing to cluster)

**Output:** 10-20 structural groups, each containing 2-15 patterns from different projects.

## STEP 5: Level 3 — Semantic Classification

For each structural group, read all patterns and classify.

This is where the reasoning happens. For each group:

1. Read ALL patterns in the group
2. **GROUP** them into sub-clusters where patterns encode the same underlying convention — the same idea expressed in different project-specific terms
3. **CLASSIFY** each sub-cluster:

   | Classification | Criteria | Action |
   |---|---|---|
   | **GENERALIZABLE** | The principle is universal. Breaking it causes bugs, security issues, or test flakiness. | Draft a generalized version if 3+ projects |
   | **STYLE** | A legitimate preference that varies between projects (naming, file organization, syntax). | Skip — do not generalize |
   | **DIVERGENT** | Projects prescribe opposing approaches to the same problem. | Skip — do not generalize |
   | **TOO RARE** | Only 1-2 projects share the convention. | Skip — insufficient evidence |

4. **Use these signals** to determine classification:

   GENERALIZABLE signals:
   - Breaking the convention causes bugs or runtime errors
   - Breaking it causes security vulnerabilities
   - Breaking it causes test flakiness or false positives
   - Breaking it causes confusion across team members
   - The convention is about correctness, not preference

   STYLE signals:
   - It's about naming conventions (camelCase vs snake_case)
   - It's about file/directory organization preferences
   - It's about syntax preference (class vs function, OOP vs functional)
   - Multiple valid approaches exist, none is objectively superior

5. **Detect contradictions:** If any two patterns in a sub-cluster prescribe opposing approaches, classify the ENTIRE sub-cluster as DIVERGENT — even if 15 projects agree and only 2 disagree. The hub MUST NOT impose choices where reasonable disagreement exists.

6. **Flag contradictions explicitly** in the output so the hub maintainer can review them.

## STEP 6: Draft Generalized Patterns

For each GENERALIZABLE sub-cluster with 3+ contributing projects, draft a hub-ready pattern.

1. Read the pattern structure standards:
   - `core/.claude/rules/pattern-structure.md`
   - `core/.claude/rules/pattern-portability.md`
   - `core/.claude/rules/pattern-self-containment.md`

2. Draft the generalized pattern, adapting the approach by type:

   **For rules:** Strip project-specific details, preserve the universal constraint. Replace file paths, class names, env vars with generic placeholders.

   **For skills:** Generalize the workflow steps while preserving the procedure structure. Replace project-specific commands with parameterized alternatives (e.g., "run your migration tool" instead of "run `alembic upgrade head`"). Keep the step ordering and gotchas — those are the value.

   **For agents:** Generalize the domain focus while preserving the review structure. Replace project-specific decision criteria with parameterized ones (e.g., "check against configured dietary constraints" instead of "check for Jain/Sattvic violations").

   All types:
   - Use RFC 2119 language (MUST, MUST NOT, SHOULD)
   - Include `version: "1.0.0"` in frontmatter
   - Do NOT include `synthesized: true` — this is now a hub pattern, not a project-specific one
   - Include a provenance comment: `<!-- Generalized from N projects via /synthesize-hub -->`

3. Validate the draft follows all portability standards:
   - No hardcoded paths
   - No project-specific references
   - Proper `globs:` scope
   - Least-privilege `allowed-tools` (for skills)

4. Run `validate_patterns.py` on the draft:
   ```bash
   python scripts/validate_patterns.py [draft-file]
   ```

## STEP 7: Create PRs

For each generalized pattern that passes validation, create a PR on the hub repo.

1. Create a branch for the batch:
   ```bash
   git checkout -b synthesize-hub/$(date +%Y-%m-%d)
   ```

2. Write generalized patterns to the appropriate directory:
   - Rules → `core/.claude/rules/[name].md`
   - Skills → `core/.claude/skills/[name]/SKILL.md`
   - Agents → `core/.claude/agents/[name].md`

3. Update `registry/patterns.json` with the new patterns

4. Create a single PR with all generalized patterns:
   ```bash
   gh pr create --title "feat: generalized patterns from N projects" --body "$(cat <<'EOF'
   ## Summary

   Patterns generalized from synthesized conventions across downstream projects.

   ## Clusters

   [For each cluster:]
   ### [Convention Name] (N projects)
   - Classification: GENERALIZABLE
   - Type: rule | skill | agent
   - Contributing projects: [list]
   - Generated pattern: `core/.claude/{rules|skills|agents}/[name]`

   ## Skipped Clusters

   - [N] STYLE clusters (legitimate preference differences)
   - [N] DIVERGENT clusters (contradictory approaches)
   - [N] TOO RARE clusters (< 3 projects)

   ## Contradictions Detected

   [List any contradictions found, with the specific patterns that disagree]

   ---
   Generated by `/synthesize-hub`
   EOF
   )"
   ```

## STEP 8: Summary Report

Print a summary of the scan:

```
Synthesize Hub — Scan Complete

Projects scanned:      [N] (of [M] registered)
Projects skipped:      [N] (no bilateral consent)
Patterns collected:    [N]
Patterns excluded:     [N] (private)

Clustering:
  Level 1 (hash):      [N] exact duplicate groups
  Level 2 (structural):[N] structural groups
  Level 3 (semantic):  [N] sub-clusters analyzed

Classification:
  GENERALIZABLE:       [N] sub-clusters ([N] with 3+ projects → drafted)
  STYLE:               [N] sub-clusters (skipped)
  DIVERGENT:           [N] sub-clusters (skipped)
  TOO RARE:            [N] sub-clusters (skipped)

Output:
  Generalized patterns:[N]
  PR created:          [PR URL or "none — no generalizable clusters met threshold"]
```

## STEP 9: Generate Scan Logs

For each scanned project, check if `scan_log: true` in their `synthesis-config.yml`. If so, generate a `.claude/scan-log.yml` entry to include in the next sync PR to that project.

1. For each eligible project with `scan_log: true`:

   ```yaml
   # .claude/scan-log.yml — auto-generated, do not edit
   # Full history of hub scan interactions with this project

   scans:
     - date: "[today's date]"
       patterns_scanned: [N]
       picked_up:
         - file: rules/[name].md
           cluster: [cluster-name]
           cluster_size: [N]
       skipped_private:
         - [list of private pattern filenames]
       skipped_no_match: [N]
   ```

2. If the project already has a `scan-log.yml`, append the new scan entry to the `scans` list — do NOT overwrite previous entries.

3. The scan log is delivered via the same sync PR mechanism as pattern updates (in `sync_to_projects.py`). Write the generated log entries to `.synthesize-hub/scan-logs/{owner}__{repo}.yml` for `sync_to_projects.py` to pick up.

## STEP 10: Cleanup

Remove temporary files:
```bash
rm -rf .synthesize-hub/collected/
```

---

## CRITICAL RULES

- NEVER scan a project without bilateral consent. Both `share_synthesized: true` in `repos.yml` AND `allow_hub_sharing: true` in the project's `synthesis-config.yml` MUST be verified.
- NEVER include patterns marked `private: true` or listed in `private_patterns`.
- NEVER generalize STYLE or DIVERGENT clusters. Even with a strong majority (15 agree, 2 disagree), classify as DIVERGENT. The hub does not impose preferences.
- NEVER include project-specific details in generalized patterns. All file paths, class names, env vars, and internal references MUST be replaced with generic placeholders.
- NEVER skip the validation step. Every generalized pattern MUST pass `validate_patterns.py`.
- The PR is a proposal — it MUST be reviewed and merged by the hub maintainer. This skill creates the PR but does not merge it.
- Clean up `.synthesize-hub/collected/` after every run. Do not leave project patterns on disk.
