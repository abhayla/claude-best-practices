---
name: synthesize-project
description: >
  Provision hub patterns AND generate project-specific .claude/ patterns for a TARGET PROJECT.
  Writes ONLY to the target project's .claude/ directory (local) or creates a PR on the target repo (remote).
  NEVER writes to core/.claude/ — that is the hub template. If running from the hub repo, --repo or --local is REQUIRED.
  Use --skip-hub for synthesis only, --skip-synthesis for hub patterns only.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[--repo owner/name] [--update] [--dry-run] [--skip-hub] [--skip-synthesis] [--only skills|rules|agents] [--tier must-have|improved|nice-to-have|all]"
version: "4.0.0"
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

**Skip this step if:** `--skip-hub` is set, OR `--update` is set (hub patterns were already provisioned on first run), OR `--dry-run` is set (preview mode — do not provision, just note that hub provisioning would run).

If `--dry-run`: Print "Would run: recommend.py --provision for [project]" and skip to Step 2. Do NOT execute recommend.py.

Run `recommend.py --provision --json` to copy matching hub patterns and generate CLAUDE.md/settings.json for the project. The `--json` flag outputs structured 5-category results (must-have, improved, nice-to-have, synthesized, skip) that this skill parses.

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

**Parse the JSON output** to capture the 5-category breakdown:
- **must-have**: New patterns to add (merge confidently)
- **improved**: Hub has newer versions of existing patterns (review diffs)
- **nice-to-have**: Optional patterns (checkbox PR in remote mode)
- **synthesized**: Placeholder for Step 7 (filled by this skill)
- **skip**: Patterns not relevant to this project

Also capture:
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

### Rules — conventions worth encoding as always-on constraints

A convention is worth a **rule** when:
- It's a consistent pattern followed across multiple files
- Breaking it would cause bugs, inconsistency, or confusion
- A new developer (or AI) working on the project might not know about it
- It's specific to THIS project, not a generic best practice

### Skills — workflows worth encoding as on-demand procedures

A convention is worth a **skill** when:
- It's a multi-step procedure that developers repeat (e.g., "add a new DB model", "create a new feature module", "run and debug E2E tests")
- The steps are project-specific — not just "run tests" but "run tests in this specific order with these specific fixtures and this specific setup"
- Getting the steps wrong causes subtle bugs (e.g., forgetting one of 5 locations when adding a model)
- It involves coordination across multiple files or modules

### Agents — tasks worth delegating to a specialized subagent

A convention is worth an **agent** when:
- It's a review or analysis task that benefits from a dedicated persona (e.g., "review this meal generation output for dietary constraint violations")
- It requires reading many files and producing a structured assessment
- It's a recurring quality gate specific to this project's domain

### NOT worth encoding (any type)

- Already enforced by a linter, formatter, or type checker
- A language/framework default documented in official docs
- A one-off implementation detail in a single file
- A generic best practice (e.g., "write tests", "use descriptive names")

### Identification checklist

For each candidate, note:
1. **Name** — short descriptive name
2. **Hypothesis** — what you believe the convention is
3. **Evidence needed** — which specific source files to read to confirm (max 5 per convention)
4. **Category** — `correctness` | `safety` | `consistency` | `testing` | `deployment`
5. **Pattern type** — choose using this decision table:

   | Signal | Type |
   |--------|------|
   | "Always do X when working on Y files" | **rule** |
   | "When you need to do X, follow these N steps" | **skill** |
   | "Review/analyze X and produce a structured report" | **agent** |
   | Multi-step procedure across 3+ files | **skill** |
   | A constraint that applies to every edit in scope | **rule** |
   | A task that benefits from a dedicated persona/focus | **agent** |

6. **Confidence** — `high` (seen in 5+ files) | `medium` (seen in 2-4 files) | `low` (seen in 1 file)

**Aim for a mix of types.** A project with only rules is missing workflow automation. A project with only skills is missing guardrails. Target roughly: 40-60% rules, 30-50% skills, 0-20% agents.

Drop any candidate with `low` confidence immediately. A missing pattern is better than a wrong one.

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

**Wait for user acknowledgment** before proceeding to Step 4. The user may want to add, remove, or reprioritize conventions.

### Dedup against hub patterns

Before proceeding, compare each candidate convention against the hub patterns copied in Step 1 (if Step 1 ran). If a hub pattern already covers the convention (even generically), check whether the project-specific version adds genuine value beyond what the hub provides. Drop conventions where the hub pattern is sufficient.

**Examples of "hub covers it":**
- Hub has `android-arch` skill covering clean architecture → don't generate `module-dependency-direction` rule unless project has non-standard dependency rules
- Hub has `testing.md` rule → don't generate test fixture rule unless project has unique fixture conventions

**Examples of "project-specific adds value":**
- Hub has generic `db-migrate` skill → project has 5-location model import rule (completely unique)
- Hub has generic `tdd` skill → project has specific `BaseViewModel<T : BaseUiState>` pattern

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

## STEP 4: Read Evidence and Confirm

For each remaining candidate convention, read the source files listed in "evidence needed."

1. Read the files using `Read` — deduplicate across conventions (if two conventions need the same file, you already have it in context). **Deep scan (default):** Read ALL evidence files needed to confirm conventions. Do NOT cap at an arbitrary number. If total evidence files exceed 15, delegate overflow to subagents to manage context — but NEVER skip evidence files entirely.
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

**Wait for user acknowledgment** before proceeding to Step 5. This is the last checkpoint before pattern generation begins.

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
argument-hint: "[required-arg] [--optional-flag]"
version: "1.0.0"
synthesized: true
private: false
---

# [Skill Title]

## STEP 1: [Verb Phrase]
[numbered instructions with concrete file paths and commands from THIS project]

## STEP 2: [Verb Phrase]
[numbered instructions]

## CRITICAL RULES
- [constraint 1]
- [constraint 2]
```

Skills MUST encode project-specific multi-step procedures. Each step should reference actual file paths, commands, or patterns from the codebase. Generic workflow skills (e.g., "run tests") add no value — the skill must capture the project-specific gotchas, ordering, and coordination.

### For agents (delegated review/analysis tasks):

```yaml
---
name: [agent-name]
description: >
  When and why to use this agent. [1-3 sentences]
tools: ["Read", "Grep", "Glob"]  # JSON array, least-privilege
model: inherit
synthesized: true
private: false
---

# [Agent Title]

## Core Responsibilities
- [what this agent analyzes or reviews]
- [what domain knowledge it applies]

## Input
[what to pass to this agent]

## Output Format
[structured output: checklist, report, verdict]

## Decision Criteria
[project-specific rules this agent applies]
```

Agents MUST have a clear domain focus specific to this project. A generic "code reviewer" agent adds no value — an agent that reviews meal generation output for dietary constraint violations does.

### Quality checks for each generated pattern:

**Structure (pattern-structure.md):**
- Does `version` field exist and follow SemVer format (e.g., `"1.0.0"`)?
- For skills: does it have `name`, `description`, `type`, `allowed-tools`, `argument-hint`, `version`?
- For skills: does it have a `## CRITICAL RULES` section at the end?
- For agents: does frontmatter include `tools` as a JSON array (e.g., `["Read", "Grep", "Glob"]`)?
- For agents: does body include `## Core Responsibilities` and `## Output Format` sections?
- For rules: does it have `globs:` in frontmatter OR `# Scope: global` in first 5 lines?

**Portability (pattern-portability.md):**
- Is it specific to THIS project (not generic advice)?
- Are `allowed-tools` least-privilege (read-only skills don't include Write/Edit/Bash)?
- Are project-specific file paths used as concrete examples (good) not as hardcoded assumptions (bad)?

**Self-containment (pattern-self-containment.md):**
- Does it contain at least 30 lines of actual content (not a stub)?
- Is it under 500 lines? If 500-1000, consider splitting. Over 1000 = must split.
- No placeholder markers (`<!-- TODO -->`, `<!-- FIXME -->`)?
- If it references another skill by name, does that skill exist in the project's `.claude/`?

**Language (rule-writing-meta.md):**
- Does it use RFC 2119 language (MUST, MUST NOT, NEVER) for critical constraints?
- For rules: does it provide alternatives, not just prohibitions?

### Sensitivity flagging:

Scan each generated pattern for keywords: `auth`, `secret`, `token`, `credential`, `billing`, `payment`, `session`, `encryption`, `API key`, `password`, `private key`. If found, **flag the pattern and ask the user** whether to mark it `private: true`. Do not auto-flag silently — the user may intend for auth-related patterns to be shareable.

## STEP 7: Validate and Write

1. **If `--dry-run` mode:** Print each generated pattern with its target path and stop. Do not write any files.

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

### Remote mode (`--repo`): create SEPARATE PRs per tier

**CRITICAL:** ALWAYS create separate PRs for each tier. NEVER combine tiers into a single PR. NEVER skip a tier. NEVER make arbitrary decisions about which resources to include or exclude. Every confirmed pattern MUST appear in exactly one PR based on its tier.

**Tier classification for synthesized patterns:**
- **Must-have (high confidence):** Patterns with `confidence: high` — correctness/safety conventions that prevent bugs
- **Nice-to-have (medium confidence):** Patterns with `confidence: medium` — consistency/style conventions
- **Enhanced (hub-improved):** Patterns where a hub pattern exists but the project-specific version adds value

3. **For EACH tier with patterns**, create a separate branch and PR:

   ```bash
   # Branches — one per tier
   # synthesize-project/must-have     — high-confidence patterns
   # synthesize-project/nice-to-have  — medium-confidence patterns
   # synthesize-project/enhanced      — project refinements of hub patterns

   DEFAULT_SHA=$(gh api repos/owner/name/git/refs/heads/main --jq '.object.sha')
   gh api repos/owner/name/git/refs \
     -f ref="refs/heads/synthesize-project/TIER_NAME" \
     -f sha="$DEFAULT_SHA"
   ```

4. **Push pattern files** to the appropriate tier branch.

5. **Push `synthesis-config.yml`** to the must-have branch if it doesn't exist.

6. **Create a PR for EACH tier** (must-have, nice-to-have, enhanced). Skip tiers with zero patterns. Each PR title MUST include the tier name and count. Nice-to-have PR should use checkboxes for individual pattern selection.

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
  Must-have:     [N] new patterns
  Improved:      [N] hub upgrades to existing patterns
  Nice-to-have:  [N] optional (checkbox PR created in remote mode)
  Skipped:       [N]
  CLAUDE.md:     created|updated|appended|skipped
  settings.json: created|merged|skipped

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
  Must-have:     [N] new patterns
  Improved:      [N] hub upgrades to existing patterns
  Nice-to-have:  [N] optional (checkbox PR created in remote mode)
  Skipped:       [N]
  CLAUDE.md:     created|updated|appended|skipped
  settings.json: created|merged|skipped

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

- NEVER write synthesized patterns to `core/.claude/`. That is the hub's distributable template. This skill writes ONLY to the TARGET PROJECT's `.claude/` (local mode) or creates a PR on the TARGET REPO (remote mode). If you find yourself writing to `core/.claude/`, you are doing it wrong — STOP immediately.
- NEVER generate generic best-practice patterns. Every pattern MUST reference specific conventions observed in THIS project's code. "Use consistent error handling" is useless. "All endpoints in `src/api/` must return through the `ApiResult[T]` wrapper" is useful.
- NEVER write patterns with `confidence: low`. Drop them. A wrong pattern actively harms — it teaches Claude Code incorrect conventions.
- NEVER overwrite `synthesis-config.yml` if it already exists. The user's consent settings are sacred.
- In local mode, this skill runs entirely in-session with no network requests (except for recommend.py which reads the hub registry locally). In remote mode (`--repo`), it fetches files from GitHub via `gh api` and creates a PR.
- If `--update` mode finds stale patterns, do NOT delete them automatically. Write them to the summary as "candidates for removal" and let the developer decide.
- Mark patterns as `private: true` if they mention auth, secrets, tokens, credentials, billing, payment, or similar sensitive topics. When in doubt, mark private.
- Each generated pattern MUST have at least 30 lines of actual content. No stubs.
- NEVER cap, limit, or prioritize a subset of confirmed conventions. Generate ALL of them. Do NOT pick "top 10" or defer to a follow-up run. The user expects complete, exhaustive coverage.
- ALWAYS create SEPARATE PRs for each tier (must-have, nice-to-have, enhanced) in remote mode. NEVER combine tiers into a single PR. NEVER skip a tier that has patterns. NEVER make arbitrary decisions about which resources to include or exclude from a PR.
- ALWAYS perform deep scan — read ALL evidence files needed to confirm conventions. Do NOT limit evidence reads to an arbitrary budget. If more than 15 files are needed, delegate to subagents, but NEVER skip evidence.
- When deduping against hub patterns in Step 3, err on the side of KEEPING the project-specific convention. Only drop it if the hub pattern genuinely covers the same ground. A project-specific pattern that adds even small value over the hub pattern is worth keeping.
