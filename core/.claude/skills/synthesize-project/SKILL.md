---
name: synthesize-project
description: >
  Provision hub patterns AND generate project-specific .claude/ patterns from a codebase.
  Combines hub provisioning (recommend.py --provision) with code-driven synthesis in one command.
  Supports local projects (current directory) and remote GitHub repos (--repo owner/name).
  Use --skip-hub for synthesis only, --skip-synthesis for hub patterns only.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[--repo owner/name] [--update] [--dry-run] [--skip-hub] [--skip-synthesis]"
version: "2.0.0"
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
| `--skip-hub` | Skip Step 1 (no hub patterns, synthesis only — old behavior) |
| `--skip-synthesis` | Skip Steps 2-8 (hub patterns only — equivalent to `recommend.py --provision`) |

`--repo` can be combined with `--update`, `--dry-run`, `--skip-hub`, or `--skip-synthesis`.

---

## STEP 0: Determine Source (Local vs Remote)

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

Run `recommend.py --provision` to copy matching hub patterns and generate CLAUDE.md/settings.json for the project.

**Local mode:**

```bash
# Run from the hub repo root (where recommend.py lives)
PYTHONPATH=. python scripts/recommend.py --local "$PROJECT_DIR" --provision
```

Where `$PROJECT_DIR` is the target project's absolute path. If the user is running this in the target project directory and the hub repo is at a known location, adjust the command accordingly.

**Remote mode:**

```bash
PYTHONPATH=. python scripts/recommend.py --repo owner/name --provision
```

**Parse the output** to capture:
- Number of files copied
- Which patterns were added (rules, skills, agents)
- CLAUDE.md status (created / updated / already existed)
- settings.json status (created / merged / already existed)
- Number of patterns skipped (already existed in project)

Store these counts for the summary in Step 9.

**If recommend.py is not available** (e.g., this skill is running in a project that doesn't have the hub repo locally), skip this step gracefully and proceed to Step 2. Print a note: "Hub repo not found — skipping hub provisioning. Use --skip-hub to suppress this message."

**If `--skip-synthesis` is set:** After this step, jump directly to Step 8 (generate synthesis-config.yml) and then Step 9 (summary). Skip Steps 2-7.

---

## STEP 2: Map the Project

Gather project structure and configuration to understand what this project is and how it's built.

1. Map the file tree — capture the top 3 levels of directory structure
   - **Local:** Use `Glob`
   - **Remote:** Already fetched in Step 0 — filter the tree output

2. Read **config files** (read whichever exist):
   - Package configs: `pyproject.toml`, `package.json`, `build.gradle`, `build.gradle.kts`, `Cargo.toml`, `go.mod`, `pom.xml`, `Gemfile`
   - CI configs: `.github/workflows/*.yml`, `Jenkinsfile`, `.gitlab-ci.yml`, `Dockerfile`, `docker-compose.yml`
   - Linter/formatter configs: `.eslintrc*`, `ruff.toml`, `pyproject.toml [tool.ruff]`, `.prettierrc*`, `biome.json`
   - Project CLAUDE.md or README.md (if they exist — these reveal stated conventions)

3. Read **entry points** — files matching: `main.*`, `app.*`, `index.*`, `server.*`, `manage.py`, `wsgi.py`

4. Find the test directory, then read one representative test file (pick the largest test file — it likely demonstrates the most conventions)

**If `--update` mode:** Also read all existing `.claude/rules/*.md`, `.claude/skills/*/SKILL.md`, and `.claude/agents/*.md` to understand what patterns already exist.

**Output of this step:** A mental model of the project's stack, structure, dependencies, and testing approach.

## STEP 3: Identify Conventions (with Dedup Against Hub)

Based on what you learned in Step 2, identify 10-20 candidate conventions worth encoding as patterns.

A convention is **WORTH** encoding when:
- It's a consistent pattern followed across multiple files
- Breaking it would cause bugs, inconsistency, or confusion
- A new developer (or AI) working on the project might not know about it
- It's specific to THIS project, not a generic best practice

A convention is **NOT** worth encoding when:
- It's already enforced by a linter, formatter, or type checker
- It's a language/framework default documented in official docs
- It's a one-off implementation detail in a single file
- It's a generic best practice (e.g., "write tests", "use descriptive names")

For each candidate convention, note:
1. **Name** — short descriptive name
2. **Hypothesis** — what you believe the convention is
3. **Evidence needed** — which specific source files to read to confirm (max 5 per convention)
4. **Category** — `correctness` | `safety` | `consistency` | `testing` | `deployment`
5. **Pattern type** — `rule` (always-on constraint) | `skill` (on-demand workflow) | `agent` (delegated task)
6. **Confidence** — `high` (seen in 5+ files) | `medium` (seen in 2-4 files) | `low` (seen in 1 file)

Drop any candidate with `low` confidence immediately. A missing pattern is better than a wrong one.

### Dedup against hub patterns

Before proceeding, compare each candidate convention against the hub patterns copied in Step 1 (if Step 1 ran). If a hub pattern already covers the convention (even generically), check whether the project-specific version adds genuine value beyond what the hub provides. Drop conventions where the hub pattern is sufficient.

**Examples of "hub covers it":**
- Hub has `android-arch` skill covering clean architecture → don't generate `module-dependency-direction` rule unless project has non-standard dependency rules
- Hub has `testing.md` rule → don't generate test fixture rule unless project has unique fixture conventions

**Examples of "project-specific adds value":**
- Hub has generic `db-migrate` skill → project has 5-location model import rule (completely unique)
- Hub has generic `tdd` skill → project has specific `BaseViewModel<T : BaseUiState>` pattern

Track how many conventions were dropped due to hub overlap — report this in the summary.

**If `--update` mode:** Compare candidates against existing patterns. Only keep:
- New conventions not covered by existing patterns
- Existing patterns that are now stale (code changed, pattern didn't)

## STEP 4: Read Evidence and Confirm

For each remaining candidate convention, read the source files listed in "evidence needed."

1. Read the files using `Read` — deduplicate across conventions (if two conventions need the same file, you already have it in context)
2. For each convention, confirm or reject:
   - **Confirmed** — the convention holds across the evidence files with no major counter-examples
   - **Rejected** — the evidence is inconsistent, or the convention is weaker than hypothesized
   - **Refined** — the convention exists but needs to be stated differently than hypothesized
3. Note any **counter-evidence** — files that deviate from the convention. If more than 30% of evidence files deviate, reject the convention
4. Assess **sensitivity** — does the pattern reveal auth flows, secrets handling, billing logic, or internal architecture that the team might want private?

Drop rejected conventions. Refine any that need it.

## STEP 5: Load Reference Material

Before generating patterns, load the format standards and examples that guide generation quality.

1. Read the pattern structure standards (these define required format):
   - `core/.claude/rules/pattern-structure.md` (or the project's local copy if it exists)
   - `core/.claude/rules/pattern-portability.md`
   - `core/.claude/rules/pattern-self-containment.md`

2. Read 2-3 existing patterns from `core/.claude/` as format examples — pick patterns that match the project's detected stack. If no stack match, use any well-structured universal pattern. These show what good output looks like.

   If hub patterns were copied in Step 1, you can read examples from the project's own `.claude/` directory — they're now local.

If the hub patterns are not available locally (project was not bootstrapped from the hub), skip this step and use the format requirements embedded in Step 6 below.

## STEP 6: Generate Patterns

For each confirmed convention, generate a complete pattern file.

### For rules (always-on constraints):

```yaml
---
description: >
  [1-2 sentence description of what this rule enforces and why]
globs: ["**/*.py", "**/*.ts"]  # Scope to relevant file types
synthesized: true
private: false  # Set to true if sensitive (auth, billing, secrets)
---

# [Convention Name]

[Body: what the convention is, why it matters, what to do and not do.
Include concrete examples from the project's actual code patterns.
Use MUST/MUST NOT for critical constraints.]
```

### For skills (on-demand workflows):

```yaml
---
name: [kebab-case-name]
description: >
  [1-3 sentences starting with a verb]
type: workflow
allowed-tools: "[minimal tool set]"
version: "1.0.0"
synthesized: true
private: false
---

# [Skill Title]

## STEP 1: [Verb Phrase]
[numbered instructions]

## STEP 2: [Verb Phrase]
[numbered instructions]

## CRITICAL RULES
- [constraint 1]
- [constraint 2]
```

### Quality checks for each generated pattern:

- Does it follow the frontmatter format exactly?
- Is it specific to THIS project (not generic advice)?
- Does it contain at least 30 lines of actual content (not a stub)?
- Does the `globs` scope match the relevant file types?
- Are sensitive patterns marked `private: true`?

### Sensitivity auto-flagging:

Scan each generated pattern's content for these keywords: `auth`, `secret`, `token`, `credential`, `billing`, `payment`, `session`, `encryption`, `API key`, `password`, `private key`. If any are found, set `private: true` in frontmatter.

## STEP 7: Validate and Write

1. **If `--dry-run` mode:** Print each generated pattern with its target path and stop. Do not write any files.

2. **Validate** — For each generated pattern, write it to a temp file and run `validate_patterns.py` via Bash (if the script exists):
   ```bash
   python scripts/validate_patterns.py [temp-pattern-file]
   ```
   Drop any pattern that fails validation.

### Local mode: write directly

3. **Write patterns** to the project's `.claude/` directory:
   - Rules → `.claude/rules/[convention-name].md`
   - Skills → `.claude/skills/[skill-name]/SKILL.md`
   - Agents → `.claude/agents/[agent-name].md`

### Remote mode (`--repo`): create a PR

3. **Create a branch** on the remote repo:
   ```bash
   # Get default branch SHA
   DEFAULT_SHA=$(gh api repos/owner/name/git/refs/heads/main --jq '.object.sha')

   # Create branch
   gh api repos/owner/name/git/refs -f ref="refs/heads/synthesize-project/$(date +%Y-%m-%d)" -f sha="$DEFAULT_SHA"
   ```

4. **Push each pattern file** to the branch:
   ```bash
   # For each generated pattern, create/update the file on the branch
   echo "PATTERN_CONTENT" | base64 | gh api repos/owner/name/contents/.claude/rules/[name].md \
     -X PUT \
     -f message="feat: add synthesized pattern [name]" \
     -f content="$(echo 'PATTERN_CONTENT' | base64)" \
     -f branch="synthesize-project/$(date +%Y-%m-%d)"
   ```

5. **Push `synthesis-config.yml`** if it doesn't exist in the repo (check first via `gh api`).

6. **Create a PR:**
   ```bash
   gh pr create --repo owner/name \
     --head "synthesize-project/$(date +%Y-%m-%d)" \
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

## STEP 8: Generate synthesis-config.yml

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

## STEP 9: Summary

Print a summary showing both hub provisioning and synthesis results.

**Read `synthesis-config.yml`** to determine sharing status.

**If sharing is OFF (default):**

```
Provision complete:

Hub patterns:
  Copied from hub:    [N] (rules: X, skills: Y, agents: Z)
  CLAUDE.md:          created|updated|appended|skipped
  settings.json:      created|merged|skipped
  Skipped (existing): [N]

Synthesized patterns:
  Rules generated:    [N]
  Skills generated:   [N]
  Agents generated:   [N]
  Skipped (overlap):  [N] (covered by hub patterns)
  Skipped (low conf): [N]

All patterns are local — nothing has been shared.

╭─ Synthesize Flywheel ──────────────────────────────────────────╮
│                                                                 │
│  Your patterns can improve over time via the hub, but it's a    │
│  two-way exchange:                                              │
│                                                                 │
│  • Share ON  → hub can learn from your patterns, AND you        │
│                receive new/improved patterns from the hub        │
│  • Share OFF → fully standalone, no data leaves, no updates     │
│                arrive (this is the default)                      │
│                                                                 │
│  To opt in:                                                     │
│    Set allow_hub_sharing: true in .claude/synthesis-config.yml  │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯
```

**If sharing is ON:**

```
Provision complete:

Hub patterns:
  Copied from hub:    [N] (rules: X, skills: Y, agents: Z)
  CLAUDE.md:          created|updated|appended|skipped
  settings.json:      created|merged|skipped
  Skipped (existing): [N]

Synthesized patterns:
  Rules generated:    [N]
  Skills generated:   [N]
  Agents generated:   [N]
  Skipped (overlap):  [N] (covered by hub patterns)
  Skipped (low conf): [N]

Hub sharing is ON — your patterns contribute to the hub, and you receive updates.
```

**If `--skip-hub` was set,** omit the "Hub patterns" section entirely.

**If `--skip-synthesis` was set,** omit the "Synthesized patterns" section entirely.

**If `--update` mode, also show:**

```
  Updated: [N] (stale patterns refreshed)
  New:     [N] (new conventions detected)
  Removed: [N] (conventions no longer present in codebase — files left for manual review)
```

**If `--repo` mode, also show:**

```
  PR created: https://github.com/owner/name/pull/[N]
  Branch:     synthesize-project/[date]

  The project owner should review the PR and merge patterns they agree with.
```

---

## CRITICAL RULES

- NEVER generate generic best-practice patterns. Every pattern MUST reference specific conventions observed in THIS project's code. "Use consistent error handling" is useless. "All endpoints in `src/api/` must return through the `ApiResult[T]` wrapper" is useful.
- NEVER write patterns with `confidence: low`. Drop them. A wrong pattern actively harms — it teaches Claude Code incorrect conventions.
- NEVER overwrite `synthesis-config.yml` if it already exists. The user's consent settings are sacred.
- In local mode, this skill runs entirely in-session with no network requests (except for recommend.py which reads the hub registry locally). In remote mode (`--repo`), it fetches files from GitHub via `gh api` and creates a PR.
- If `--update` mode finds stale patterns, do NOT delete them automatically. Write them to the summary as "candidates for removal" and let the developer decide.
- Mark patterns as `private: true` if they mention auth, secrets, tokens, credentials, billing, payment, or similar sensitive topics. When in doubt, mark private.
- Each generated pattern MUST have at least 30 lines of actual content. No stubs.
- When deduping against hub patterns in Step 3, err on the side of KEEPING the project-specific convention. Only drop it if the hub pattern genuinely covers the same ground. A project-specific pattern that adds even small value over the hub pattern is worth keeping.
