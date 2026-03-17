---
name: synthesize-project
description: >
  Provision hub patterns AND generate project-specific .claude/ patterns for a TARGET PROJECT.
  Writes ONLY to the target project's .claude/ directory (local) or creates a PR on the target repo (remote).
  NEVER writes to core/.claude/ — that is the hub template. If running from the hub repo, --repo or --local is REQUIRED.
  Use --skip-hub for synthesis only, --skip-synthesis for hub patterns only.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[--repo owner/name] [--update] [--dry-run] [--skip-hub] [--skip-synthesis] [--only skills|rules|agents] [--tier must-have|improved|nice-to-have|all]"
version: "3.2.0"
type: workflow
---

# Synthesize Project Patterns

Provision hub patterns and generate project-specific `.claude/` patterns by reading the actual codebase.

**Arguments:** $ARGUMENTS

---

## Mode Detection

| Flag | Effect |
|------|--------|
| (none) | Full flow: hub provision + code synthesis |
| `--repo owner/name` | Remote mode — fetch via GitHub API, create PR |
| `--update` | Delta only — skip hub provision, synthesize only new/stale conventions |
| `--dry-run` | Preview only, no writes |
| `--skip-hub` | Skip Steps 1-2 (no hub patterns or CLAUDE.md audit, synthesis only — old behavior) |
| `--skip-synthesis` | Skip Steps 3-8 (hub patterns + CLAUDE.md audit only — equivalent to `recommend.py --provision` plus section audit) |

`--repo` can be combined with `--update`, `--dry-run`, `--skip-hub`, or `--skip-synthesis`.

---

## STEP 0: Determine Source (Local vs Remote)

### Hub repo guard (CRITICAL)

Before anything else, detect whether you are currently running inside the claude-best-practices hub repo (the repo that contains `core/.claude/`, `registry/patterns.json`, and `scripts/recommend.py`). Check:

```bash
# If ALL of these exist, you are in the hub repo
test -d core/.claude && test -f registry/patterns.json && test -f scripts/recommend.py
```

**If you ARE in the hub repo:**
- `--repo owner/name` is REQUIRED. You MUST be targeting a different repo.
- If `--repo` was NOT provided and no `--local /path` was given, STOP and ask: "You're running inside the hub repo. Which project should I synthesize patterns for? Use `--repo owner/name` or `--local /path/to/project`."
- NEVER write synthesized patterns to `core/.claude/`. That directory is the hub's distributable template — only curated, generic patterns belong there. Project-specific patterns go to the TARGET project's `.claude/`.
- NEVER treat scanning a downstream repo as "adding patterns to the hub." That is the job of `collate.py` and `/synthesize-hub`, NOT this skill.

**If you are NOT in the hub repo:** Proceed normally — local mode targets the current directory.

### Hub freshness check

If running from the hub repo (local mode), check for uncommitted changes that could affect provision accuracy:

```bash
# Check for uncommitted changes in core/.claude/ or registry/
git status --porcelain core/.claude/ registry/ scripts/recommend.py
```

If there are uncommitted changes in these paths, warn:
```
⚠ Hub repo has uncommitted changes in core/.claude/ or registry/.
  Provisioned patterns may not reflect the latest state.
  Continue anyway? (y/n)
```

---

If `--repo owner/name` is provided, set up remote file access. Otherwise, use local tools.

**Remote mode setup:**

1. Verify the repo exists and you have access:
   ```bash
   gh repo view owner/name --json name,defaultBranchRef
   ```

2. Fetch the repository file tree:
   ```bash
   gh api repos/owner/name/git/trees/HEAD?recursive=1 --jq '.tree[] | select(.type=="blob") | .path'
   ```

3. Define a helper function for reading remote files (use throughout all subsequent steps instead of `Read`):
   ```bash
   # Fetch a single file's content from the repo
   gh api repos/owner/name/contents/PATH --jq '.content' | base64 -d
   ```

4. For `--update` mode, also fetch existing `.claude/` patterns from the repo:
   ```bash
   gh api repos/owner/name/contents/.claude/rules --jq '.[].name'
   gh api repos/owner/name/contents/.claude/skills --jq '.[].name'
   ```

**Local mode:** No setup needed. Use `Glob`, `Read`, `Grep` as normal throughout all steps.

**For all subsequent steps:** When this document says "read a file" or "use Read/Glob", use the appropriate method based on mode — local tools for local mode, `gh api` for remote mode.

---

## STEP 1: Provision Hub Patterns

**Skip this step if:** `--skip-hub` is set, OR `--update` is set (hub patterns were already provisioned on first run).

**If `--dry-run`:** Run recommend.py with `--json` only (WITHOUT `--provision`) to get gap analysis data without writing files. Print "DRY RUN: analysis only — no files will be written." Store the gaps output for use in Steps 3-8. In Step 8, print generated patterns with their target paths but do NOT write any files.

**If recommend.py exits non-zero:** Capture stderr output. Print: "recommend.py failed (exit code [N]): [stderr]". Proceed to Step 2 with an empty gaps dict — treat all subsequent hub-related steps as if `--skip-hub` was set.

Run `recommend.py --provision --json` to copy matching hub patterns and generate CLAUDE.md/settings.json for the project. The `--json` flag outputs a combined JSON object with `gaps` (4-category: must-have, improved, nice-to-have, skip) and `provision` (copied_files, config statuses).

**Local mode:**

```bash
# Run from the hub repo root (where recommend.py lives)
PYTHONPATH=. python scripts/recommend.py --local "$PROJECT_DIR" --provision --json
```

Where `$PROJECT_DIR` is the target project's absolute path. If the user is running this in the target project directory and the hub repo is at a known location, adjust the command accordingly.

**Remote mode:**

```bash
PYTHONPATH=. python scripts/recommend.py --repo owner/name --provision --json
```

**Parse the JSON output** to capture the 4-category gap breakdown:
- **must-have**: New patterns to add (merge confidently)
- **improved**: Hub has newer versions of existing patterns (review diffs)
- **nice-to-have**: Optional patterns (checkbox PR in remote mode)
- **skip**: Patterns not relevant to this project

The synthesized pattern counts in the Step 10 summary come from Step 8, not from recommend.py.

Also capture:
- Number of files copied
- Which patterns were added (rules, skills, agents)
- CLAUDE.md status (created / updated / already existed)
- settings.json status (created / merged / already existed)
- Number of patterns skipped (already existed in project)

Store these counts for the summary in Step 10.

**Also capture warnings:** If recommend.py emits lines containing `WARNING:` (e.g., "WARNING: hub skill 'X' not found"), collect them and include in the Step 10 summary under the Warnings section. These indicate registry/disk mismatches in the hub itself.

**If recommend.py is not available** (e.g., this skill is running in a project that doesn't have the hub repo locally), skip this step gracefully and proceed to Step 2. Print a note: "Hub repo not found — skipping hub provisioning. Use --skip-hub to suppress this message."

**If `--skip-synthesis` is set:** After this step, proceed to Step 2 (Audit CLAUDE.md Sections), then jump directly to Step 9 (generate synthesis-config.yml) and Step 10 (summary). Skip Steps 3-8.

---

## STEP 2: Audit CLAUDE.md Sections

**Skip this step if:** `--skip-hub` is set (no hub template available), OR the project has no CLAUDE.md yet (Step 1 just created it from the template — it already has all sections).

**Purpose:** When the hub template (`core/.claude/CLAUDE.md.template`) evolves with new sections (e.g., "Troubleshooting", "Patterns We DON'T Use"), existing projects that were provisioned earlier never learn about them. This step compares the template's section structure against the project's existing CLAUDE.md and reports gaps.

### 2a. Read both files

1. Read the hub template:
   - **Local mode:** `Read core/.claude/CLAUDE.md.template`
   - **Remote mode (running from hub repo):** The template is already local at `core/.claude/CLAUDE.md.template`

2. Read the project's existing CLAUDE.md:
   - **Local mode:** `Read $PROJECT_DIR/CLAUDE.md`
   - **Remote mode:** `gh api repos/owner/name/contents/CLAUDE.md --jq '.content' | base64 -d`

If either file doesn't exist, skip this step.

### 2b. Extract and compare section headings

Extract all `##` headings from both files. Ignore:
- Content inside `<!-- hub:best-practices:start -->` ... `<!-- hub:best-practices:end -->` markers (hub-managed section is handled by `recommend.py`, not this audit)
- Template variable lines (`{{...}}`) — these are placeholders, not real content
- HTML comments (`<!-- TODO: ... -->`) — these are guidance for the user

Compare the template's `##` headings against the project's `##` headings. Match by normalized heading text (lowercase, strip punctuation).

### 2c. Report missing sections

Print a section audit report:

```
CLAUDE.md Section Audit:

Template sections present in project CLAUDE.md:
  [check] Project Overview
  [check] Architecture
  [check] Development Commands
  [check] Testing

Template sections MISSING from project CLAUDE.md:
  [missing] Troubleshooting — common issues & solutions table
  [missing] Patterns We DON'T Use — explicitly list avoided patterns with alternatives
  [missing] Environment Setup — local dev setup steps

No action needed for [N] sections already present.
```

### 2d. Offer to append missing sections

For each missing section, extract the corresponding section content from the template (including its TODO comments — these serve as guidance for the user to fill in).

**If `--dry-run`:** Print what would be appended and stop.

**If missing sections exist:** Ask the user:

```
[N] template sections are missing from your CLAUDE.md.
Would you like to append them as TODO stubs? (y/n/select)
  - y: append all missing sections before the hub-managed section
  - n: skip (no changes to CLAUDE.md)
  - select: choose which sections to add
```

**If user approves (y or select):**

1. Read the project's CLAUDE.md
2. Find the `<!-- hub:best-practices:start -->` marker (if present). **If multiple markers found:** Warn "Found [N] hub-managed section markers — expected exactly 1. Using the FIRST occurrence. Remove duplicate markers manually." Do not insert between duplicate markers.
3. Insert the missing sections BEFORE the marker (so they appear in the user-editable area, not inside the hub-managed section)
4. If no marker exists, append the sections at the end of the file
5. Write the updated CLAUDE.md

**In remote mode (`--repo`):** Add the CLAUDE.md changes to the PR branch created in Step 7 (or the provision branch from Step 1). Do not create a separate PR for CLAUDE.md section updates.

### 2e. Store audit results for summary

Record for Step 10:
- Number of template sections checked
- Number already present
- Number missing
- Number appended (if user approved)

### 2f. Validate rules table against filesystem

Extract all file paths from the rules table in the hub-managed section (rows matching `` `rules/<name>.md` ``). For each path, check if the file exists in the project's `.claude/` directory.

**Report:**
```
Rules table integrity:
  [check] rules/workflow.md — exists
  [check] rules/context-management.md — exists
  [missing] rules/rule-writing-meta.md — referenced in table but NOT on disk

  Action: Remove 1 dangling reference(s) from CLAUDE.md rules table? (y/n)
```

**If dangling references found and user approves:** Remove the stale rows from the rules table. If no rows remain, remove the entire "Rules Reference" section.

**In `--update` mode:** Dangling references are automatically removed without prompting (the user expects a cleanup pass). Still report what was removed in the summary.

**Also check the inverse:** scan `.claude/rules/*.md` for rule files NOT listed in the table. Report them as candidates to add.

### 2g. Store validation results for summary

Record for Step 10:
- Number of rules table entries checked
- Number of dangling references removed
- Number of unlisted rule files found

---

## STEP 3: Map the Project

Gather project structure and configuration to understand what this project is and how it's built.

1. Map the file tree — capture the top 3 levels of directory structure
   - **Local:** Use `Glob`
   - **Remote:** Already fetched in Step 0 — filter the tree output

2. Read **config files** (read whichever exist):
   - Package configs: `pyproject.toml`, `package.json`, `build.gradle`, `build.gradle.kts`, `Cargo.toml`, `go.mod`, `pom.xml`, `Gemfile`
   - CI configs: `.github/workflows/*.yml`, `Jenkinsfile`, `.gitlab-ci.yml`, `Dockerfile`, `docker-compose.yml`
   - Linter/formatter configs: `.eslintrc*`, `ruff.toml`, `pyproject.toml [tool.ruff]`, `.prettierrc*`, `biome.json`
   - Project CLAUDE.md or README.md (if they exist — these reveal stated conventions)

   **Reuse Step 1 data:** If Step 1 ran, the project's stacks and dependencies are already known from recommend.py's JSON output. Do NOT re-read package configs for stack detection. Only read files NOT covered by Step 1: entry points, test files, CI configs, linter configs, README.md.

3. Read **entry points** — files matching: `main.*`, `app.*`, `index.*`, `server.*`, `manage.py`, `wsgi.py`

4. Find the test directory, then read one representative test file (pick the largest test file — it likely demonstrates the most conventions)

5. **Check for monolithic rules file** — look for `.claude/rules.md` (a single flat file containing all rules, as opposed to individual `.claude/rules/*.md` files). **In `--update` mode:** Skip this warning if `.claude/rules/*.md` files already exist from a prior synthesis run. If found:

   ```
   ⚠ SSOT Warning: Found monolithic .claude/rules.md ([N] lines).

   This project has a single rules.md file instead of (or in addition to)
   individual rules/*.md files. Generating individual rule files will create
   duplication and drift risk.

   Options:
     1. Split — decompose rules.md into individual rules/*.md files first, then synthesize
     2. Skip rules — only synthesize skills and agents, leave rules.md as-is
     3. Proceed anyway — generate individual files (will duplicate some content)
   ```

   **Wait for user choice** before proceeding. If the user chooses "split", help decompose the monolithic file into individual rule files before continuing. If "skip rules", set `--only skills,agents` for the remaining steps.

**If `--update` mode:** Also read all existing `.claude/rules/*.md`, `.claude/skills/*/SKILL.md`, `.claude/agents/*.md`, and `CLAUDE.md` to understand what patterns and sections already exist.

**Output of this step:** A mental model of the project's stack, structure, dependencies, and testing approach.

## STEP 4: Identify Conventions (with Dedup Against Hub)

Based on what you learned in Step 3, identify 10-20 candidate conventions worth encoding as patterns.

**Read `references/convention-criteria.md`** for the full decision framework (rules vs skills vs agents, identification checklist, confidence thresholds). Key points:
- **Rules** = consistent patterns across multiple files that new developers might miss
- **Skills** = multi-step project-specific procedures across 3+ files
- **Agents** = recurring review/analysis tasks with a domain focus
- Drop `low` confidence candidates immediately
- Target mix: 40-60% rules, 30-50% skills, 0-20% agents

### Present findings to user

Before proceeding, print the full candidate list as a table for the user to review:

```
Candidate Conventions ([N] identified):

| # | Name | Type | Category | Confidence | Hypothesis |
|---|------|------|----------|------------|------------|
| 1 | ... | rule | correctness | high | ... |
| 2 | ... | skill | consistency | medium | ... |
| 3 | ... | agent | testing | medium | ... |

Type mix: [N] rules, [N] skills, [N] agents
```

Then list which conventions were dropped and why:

```
Dropped ([N]):
- [name]: low confidence (seen in 1 file only)
- [name]: already enforced by [linter/formatter]
- [name]: generic best practice, not project-specific
```

**Wait for user acknowledgment** before proceeding to Step 5. The user may want to add, remove, or reprioritize conventions.

### Dedup against hub patterns

Compare each candidate against hub patterns from Step 1 and CLAUDE.md sections from Step 2. Drop conventions where the hub pattern is sufficient. Keep project-specific conventions that add genuine value. See `references/convention-criteria.md` for dedup examples.

**Important:** Only count a hub pattern as "covering" a candidate if it was actually copied to the project in Step 1. Check the `copied_files` list from the Step 1 JSON output (under `provision.copied_files`). If a hub pattern exists in the registry but was NOT copied (e.g., it was in the nice-to-have tier and the user chose must-have only), it does NOT suppress the candidate — the project needs its own version.

**If `--skip-hub` was set:** Skip hub dedup entirely. All candidates proceed to Step 5 — there are no hub patterns to compare against.

Print the dedup results:

```
Hub dedup: [N] conventions dropped (already covered by hub patterns):
- [name]: covered by hub's [pattern-name] ([reason])
- [name]: covered by hub's [pattern-name] ([reason])

Remaining after dedup: [N] conventions to investigate
```

**If `--update` mode:** Compare candidates against existing patterns. Only keep:
- New conventions not covered by existing patterns
- Existing patterns that are now stale (code changed, pattern didn't)

## STEP 5: Read Evidence and Confirm

For each remaining candidate convention, read the source files listed in "evidence needed."

1. Read the files using `Read` — deduplicate across conventions (if two conventions need the same file, you already have it in context). **File budget:** Read a maximum of 15 evidence files directly. If total evidence files exceed 15, delegate to a subagent: pass the file list and convention hypothesis, and have the subagent return a confirmation/rejection summary.
2. For each convention, confirm or reject:
   - **Confirmed** — the convention holds across the evidence files with no major counter-examples
   - **Rejected** — the evidence is inconsistent, or the convention is weaker than hypothesized
   - **Refined** — the convention exists but needs to be stated differently than hypothesized
3. Note any **counter-evidence** — files that deviate from the convention. If more than 30% of evidence files deviate, reject the convention
4. Assess **sensitivity** — does the pattern reveal auth flows, secrets handling, billing logic, or internal architecture that the team might want private?

Drop rejected conventions. Refine any that need it.

### Present evidence results

Print the confirmation report:

```
Evidence Review ([N] conventions investigated):

CONFIRMED ([N]):
| # | Name | Type | Evidence files read | Key finding |
|---|------|------|--------------------:|-------------|
| 1 | ... | rule | 5 | [1-line summary of what was confirmed] |
| 2 | ... | skill | 3 | [1-line summary] |

REFINED ([N]):
| # | Name | Original hypothesis → Refined to |
|---|------|-----------------------------------|
| 1 | ... | [was X] → [now Y because Z] |

REJECTED ([N]):
| # | Name | Reason |
|---|------|--------|
| 1 | ... | [counter-evidence in N/M files] |

SENSITIVE ([N] — will ask before marking private):
- [name]: mentions [keyword], may contain [concern]

Proceeding to generate [N] patterns ([N] rules, [N] skills, [N] agents).
```

**Wait for user acknowledgment** before proceeding to Step 6. This is the last checkpoint before pattern generation begins.

## STEP 6: Load Reference Material

Before generating patterns, load the format standards and examples that guide generation quality.

1. Read the pattern structure standards (these define required format). Use the path appropriate to your context:
   - **If running from the hub repo** (Step 0 detected hub): read from `core/.claude/rules/`
   - **If running in a provisioned project**: read from `.claude/rules/` (copied by Step 1)

   Files to read:
   - `pattern-structure.md`
   - `pattern-portability.md`
   - `pattern-self-containment.md`

2. Read 2-3 existing patterns from `core/.claude/` as format examples — pick patterns that match the project's detected stack. If no stack match, use universal patterns like `workflow.md`, `context-management.md`, or `claude-behavior.md`. These show what good output looks like.

   If hub patterns were copied in Step 1, you can read examples from the project's own `.claude/` directory — they're now local.

If the hub patterns are not available locally (project was not bootstrapped from the hub), skip this step and use the format requirements embedded in Step 7 below.

## STEP 7: Generate Patterns

For each confirmed convention, generate a complete pattern file.

**Read `references/pattern-templates.md`** for the full YAML templates (rule, skill, agent), quality checklists (structure, portability, self-containment, language), and sensitivity flagging keywords.

Key requirements per type:
- **Rules**: `globs:` in frontmatter, `synthesized: true`, MUST/MUST NOT language, provide alternatives
- **Skills**: full frontmatter (`name`, `description`, `type`, `allowed-tools`, `argument-hint`, `version`), numbered steps, `## CRITICAL RULES` section
- **Agents**: `tools` as JSON array, `model: inherit`, `## Core Responsibilities` and `## Output Format` sections

All patterns MUST: have 30+ lines of content, be under 500 lines, use project-specific examples (not generic advice), and pass sensitivity scan for auth/secret/token keywords.

**Source hash:** For all generated patterns, include `source_hash` in frontmatter — a SHA256 hash of the concatenated evidence files used to derive the pattern. In `--update` mode, compare this hash against existing patterns' `source_hash` to detect staleness.

**Soft cap:** Generate a maximum of 10 patterns per synthesis run. If more than 10 conventions are confirmed, prioritize by confidence (high before medium) and type mix (maintain 40-60% rules target). Defer remainder to a follow-up `--update` run.

**Note:** Hooks (`.claude/hooks/`) are not synthesized by this skill. Hooks require shell scripting and CI integration. Hub hooks are provisioned in Step 1 if available. Project-specific hooks should be created manually.

## STEP 8: Validate and Write

1. **If `--dry-run` mode:** Print each generated pattern with its target path and stop. Do not write any files.

**Validate-then-write:** Validate ALL generated patterns before writing ANY of them. If any pattern fails validation, report all failures and ask the user whether to (a) write only the passing patterns, or (b) fix and retry. Do not partially write and leave the project in an inconsistent state.

2. **Validate** — For each generated pattern, write it to a temp file and run validators:
   ```bash
   # Structural validation (required)
   PYTHONPATH=. python scripts/validate_patterns.py [temp-pattern-file]

   # Dedup check against existing patterns (required)
   PYTHONPATH=. python scripts/dedup_check.py --check [temp-pattern-file]
   ```
   If `validate_patterns.py` or `dedup_check.py` are not available (running outside the hub repo), perform manual validation against the quality checks above. Drop any pattern that fails.

### Local mode: write directly

3. **Write patterns** to the project's `.claude/` directory:
   - Rules → `.claude/rules/[convention-name].md`
   - Skills → `.claude/skills/[skill-name]/SKILL.md`
   - Agents → `.claude/agents/[agent-name].md`

4. **Reconcile CLAUDE.md rules table** — After all patterns are written:
   - Read the project's CLAUDE.md
   - Find the rules table in the hub-managed section
   - Add rows for any synthesized rules not already listed
   - Remove rows for any rules no longer on disk
   - Write the updated CLAUDE.md

### Remote mode (`--repo`): create a PR

3. **Create a branch** on the remote repo:
   ```bash
   # Get default branch SHA
   DEFAULT_SHA=$(gh api repos/owner/name/git/refs/heads/main --jq '.object.sha')

   # Create branch
   gh api repos/owner/name/git/refs -f ref="refs/heads/synthesize-project/$(date +%Y-%m-%d-%H%M%S)" -f sha="$DEFAULT_SHA"
   ```

4. **Push each pattern file** to the branch:
   ```bash
   # For each generated pattern, create/update the file on the branch
   echo "PATTERN_CONTENT" | base64 | gh api repos/owner/name/contents/.claude/rules/[name].md \
     -X PUT \
     -f message="feat: add synthesized pattern [name]" \
     -f content="$(echo 'PATTERN_CONTENT' | base64)" \
     -f branch="synthesize-project/$(date +%Y-%m-%d-%H%M%S)"
   ```

5. **Push `synthesis-config.yml`** if it doesn't exist in the repo (check first via `gh api`).

6. **Create a PR:**
   ```bash
   gh pr create --repo owner/name \
     --head "synthesize-project/$(date +%Y-%m-%d-%H%M%S)" \
     --title "feat: synthesized .claude/ patterns for this project" \
     --body "$(cat <<'EOF'
   ## Summary

   Auto-generated `.claude/` patterns by analyzing this project's codebase.
   These patterns encode conventions specific to this project.

   ## Generated Patterns

   [List each pattern with name, type, and one-line description]

   ## Review Checklist

   - [ ] Patterns accurately reflect project conventions
   - [ ] No sensitive information exposed (check `private: true` patterns)
   - [ ] No generic advice — each pattern is project-specific

   ---
   Generated by `/synthesize-project` from the [claude-best-practices](https://github.com/abhayla/claude-best-practices) hub.
   EOF
   )"
   ```

## STEP 9: Generate synthesis-config.yml

**Generate `synthesis-config.yml`** if it doesn't exist — create with sharing OFF:

```yaml
# .claude/synthesis-config.yml
#
# Synthesize Flywheel — consent configuration
#
# Sharing is bilateral: turn it ON to both contribute your synthesized
# patterns to the hub AND receive new/improved patterns from the hub.
# Turn it OFF (default) to keep everything local — synthesis still works,
# but you won't receive hub updates.
#
# You can change this at any time. Changes take effect on the next scan cycle.

allow_hub_sharing: false

# Patterns listed here are NEVER shared, even when allow_hub_sharing is true.
private_patterns: []

# Project-specific details to strip from patterns before they leave.
strip_before_sharing:
  - file_paths
  - class_names
  - env_vars

# Set to true to receive a .claude/scan-log.yml with full scan history.
scan_log: false
```

**If `synthesis-config.yml` already exists:** Do not overwrite it. Respect existing consent settings.

## STEP 10: Summary

**Read `references/summary-format.md`** for the full output format templates (sharing ON/OFF variants, conditional sections for `--skip-hub`, `--skip-synthesis`, `--update`, `--repo`).

Print a summary showing hub provisioning, CLAUDE.md section audit, and synthesis results. Read `synthesis-config.yml` to determine sharing status and select the appropriate format variant.

---

## CRITICAL RULES

- NEVER write synthesized patterns to `core/.claude/`. That is the hub's distributable template. This skill writes ONLY to the TARGET PROJECT's `.claude/` (local mode) or creates a PR on the TARGET REPO (remote mode). If you find yourself writing to `core/.claude/`, you are doing it wrong — STOP immediately.
- NEVER generate generic best-practice patterns. Every pattern MUST reference specific conventions observed in THIS project's code. "Use consistent error handling" is useless. "All endpoints in `src/api/` must return through the `ApiResult[T]` wrapper" is useful.
- NEVER write patterns with `confidence: low`. Drop them. A wrong pattern actively harms — it teaches Claude Code incorrect conventions.
- NEVER overwrite `synthesis-config.yml` if it already exists. The user's consent settings are sacred.
- In local mode, this skill runs entirely in-session with no network requests (except for recommend.py which reads the hub registry locally). In remote mode (`--repo`), it fetches files from GitHub via `gh api` and creates a PR.
- If `--update` mode finds stale patterns, do NOT delete them automatically. Write them to the summary as "candidates for removal" and let the developer decide.
- Mark patterns as `private: true` if they mention auth, secrets, tokens, credentials, billing, payment, or similar sensitive topics. When in doubt, mark private.
- Each generated pattern MUST have at least 30 lines of actual content. No stubs.
- When deduping against hub patterns in Step 3, err on the side of KEEPING the project-specific convention. Only drop it if the hub pattern genuinely covers the same ground. A project-specific pattern that adds even small value over the hub pattern is worth keeping.
- STEP 2 (CLAUDE.md Section Audit) MUST insert missing sections BEFORE the `<!-- hub:best-practices:start -->` marker, never inside or after the hub-managed section. Never remove or reorganize the hub-managed markers — they are the boundary between user-editable and hub-managed content.
- STEP 2 MUST validate that every file path in the CLAUDE.md rules table exists on disk. Dangling references mislead developers and agents. Remove stale entries, add missing ones.
- STEP 3 MUST check for a monolithic `.claude/rules.md` before generating individual `rules/*.md` files. Generating both creates SSOT violations and content drift. Always ask the user how to proceed.
