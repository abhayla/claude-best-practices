---
name: ssot-audit
description: >
  Audit project's Claude Code configuration for Single Source of Truth violations.
  Detects duplicated constraints, misplaced config, bloated CLAUDE.md, and layer misuse.
  Use when editing CLAUDE.md or .claude/ files to catch configuration drift.
  NOT for placing individual rules (use /claude-guardian) or authoring new patterns (use /skill-authoring-workflow).
triggers:
  - ssot audit
  - config duplication check
  - CLAUDE.md bloat audit
  - configuration drift detection
  - layer misuse check
  - single source of truth violations
type: workflow
allowed-tools: "Read Grep Glob"
argument-hint: "[--fix]"
version: "1.2.0"
---

# SSOT Audit

Scan the project's `.claude/` directory and CLAUDE.md for Single Source of Truth violations: duplicated constraints, misplaced configuration, bloated files, and content that lives in the wrong layer.

**This skill is read-only** (allowed-tools: Read Grep Glob). It MUST NOT modify any files.
MUST distinguish intentional pointers (e.g., "see .claude/rules/X.md") from actual duplication.

**Default mode is read-only.** Pass `--fix` to get concrete edit suggestions for each violation.

**Arguments:** $ARGUMENTS

---

## Configuration Layer Reference

Each piece of Claude Code configuration has exactly one correct home:

| Content Type | Correct Location | Wrong Location |
|---|---|---|
| Multi-step workflows | `.claude/skills/*/SKILL.md` | CLAUDE.md |
| Path-specific constraints | `.claude/rules/*.md` with `globs:` | CLAUDE.md |
| Global behavioral rules | `.claude/rules/*.md` with `# Scope: global` | CLAUDE.md |
| Code style (indent, semicolons) | Linter config + hooks | CLAUDE.md or rules |
| Tool permissions | `.claude/settings.json` | CLAUDE.md |
| Project architecture + commands | CLAUDE.md | rules or skills |
| Personal preferences | CLAUDE.local.md | CLAUDE.md |
| Cross-references / pointers | CLAUDE.md (brief) | N/A |

---

## STEP 1: Gather Configuration Inventory

Build a complete map of all Claude Code configuration in the project.

### 1a. Read CLAUDE.md

- Read `CLAUDE.md` at project root
- Count total lines (record for health check in Step 2)
- Extract section headings (## level) and their line ranges
- Note any nested CLAUDE.md files in subdirectories (Glob for `**/CLAUDE.md`)

### 1b. Inventory Rules

- Glob for all `.claude/rules/*.md` files
- For each rule file, read the first 10 lines to extract:
  - `globs:` from YAML frontmatter (scoped rule)
  - `# Scope: global` declaration (global rule)
  - If neither found, flag as **UNSCOPED**
- Record: filename, scope type, line count

### 1c. Inventory Skills

- Glob for all `.claude/skills/*/SKILL.md` files
- For each skill, read frontmatter to extract: name, type, description
- Record: skill name, line count

### 1d. Inventory Settings

- Read `.claude/settings.json` if it exists (note: may not exist in all projects)
- Read `.claude/settings.local.json` if it exists
- Record which tool permissions and hooks are configured

### 1e. Check for CLAUDE.local.md

- Read `CLAUDE.local.md` at project root if it exists
- Check for `~/.claude/CLAUDE.md` (global config) -- note its existence but do not audit its content (out of project scope)

---

## STEP 2: Check CLAUDE.md Health

Evaluate CLAUDE.md against the configuration layer reference.

### 2a. Line Count Check

| Lines | Verdict | Action |
|---|---|---|
| <= 80 | OK | Within budget (per rule-writing-meta.md) |
| 81-120 | WARN | Review for content that belongs elsewhere |
| > 120 | CRITICAL | Guaranteed bloat -- extract aggressively |

### 2b. Detect Misplaced Content

Scan each CLAUDE.md section for content that belongs in a different layer:

**Multi-step workflows (should be skills):**
- Look for numbered step sequences (1. ... 2. ... 3. ...) describing procedures
- Look for "## Step" or "### Step" headings
- Look for decision trees or if/then workflows
- Threshold: 3+ sequential steps on the same topic = extract to a skill

**Path-specific constraints (should be scoped rules):**
- Look for phrases targeting specific file patterns: "When editing `*.py` files", "In the `src/auth/` directory", "For test files"
- Look for glob-like references: `**/*.ts`, `src/components/`
- These belong in `.claude/rules/*.md` with `globs:` frontmatter

**Code style enforcement (should be linter hooks):**
- Look for: indentation rules, semicolon preferences, import ordering, bracket style, line length limits, naming conventions for variables/functions
- These MUST be enforced by linters/formatters via hooks, not CLAUDE.md instructions

**Tool permissions (should be settings.json):**
- Look for: "do not use Bash", "only use Read and Grep", tool restriction language
- These belong in `.claude/settings.json` under `allowedTools` or `disallowedTools`

### 2c. Detect Bloat Patterns

- Inline code blocks longer than 15 lines (extract to skills or reference files)
- Tables longer than 10 rows (extract to reference material)
- Repeated phrases or near-identical instructions in different sections

---

## STEP 3: Detect Cross-Layer Duplication

This is the core SSOT check. A constraint MUST exist in exactly one location.

### 3a. Rule-to-CLAUDE.md Duplication

For each `.claude/rules/*.md` file:

1. Extract the key constraints (sentences containing MUST, MUST NOT, NEVER, ALWAYS)
2. Search CLAUDE.md for semantically similar constraints:
   - Same keywords in close proximity (e.g., both mention "test" + "commit" + "before")
   - Same concept expressed differently (e.g., rule says "MUST run tests before committing", CLAUDE.md says "Always run the test suite before creating a commit")
3. Distinguish **duplication** from **pointers**:
   - A pointer looks like: "See `.claude/rules/testing.md` for testing standards" -- this is fine
   - Duplication is restating the same constraint in both locations -- this is a violation

### 3b. Skill-to-CLAUDE.md Duplication

For each skill:

1. Extract the skill's core workflow steps
2. Check if CLAUDE.md contains similar procedural content
3. CLAUDE.md may reference a skill by name ("Use `/fix-issue` for bug fixes") -- this is a pointer, not duplication

### 3c. Settings-to-CLAUDE.md Duplication

If `.claude/settings.json` exists:

1. Check if CLAUDE.md also contains tool permission instructions
2. Check if CLAUDE.md duplicates hook configurations that exist in settings

### 3d. Rule-to-Rule Duplication

Compare each pair of rule files for overlapping constraints:

1. Extract key directives from each rule
2. Flag cases where two rule files enforce the same constraint
3. Exception: stack-prefixed rules (e.g., `android.md` and `flutter.md`) MAY have similar patterns if they apply to different stacks

---

## STEP 4: Validate Rule Scoping

Every rule file MUST declare its activation scope.

### 4a. Scope Declaration Check

For each rule in `.claude/rules/*.md`:

| Has `globs:` | Has `# Scope: global` | Verdict |
|---|---|---|
| Yes | No | OK -- scoped rule |
| No | Yes | OK -- global rule |
| Yes | Yes | WARN -- conflicting scope declarations |
| No | No | VIOLATION -- unscoped rule (context pollution) |

### 4b. Over-Broad Scope Check

For rules declared as `# Scope: global`, check if they contain stack-specific or path-specific content:

- References to specific frameworks (React, FastAPI, Android) in a global rule = should be scoped
- References to specific directories (`src/auth/`, `tests/`) in a global rule = should use `globs:`

### 4c. Rule Size Check

| Lines | Verdict | Action |
|---|---|---|
| <= 100 | OK | Within reasonable bounds |
| 101-200 | WARN | Review for extractable reference material |
| > 200 | VIOLATION | Split into focused rules or extract to skill with references |

---

## STEP 5: Check Skill Boundaries

Skills are workflows, not rules in disguise.

### 5a. Skill-as-Rule Detection

Flag skills that appear to be rules rather than workflows:

- Fewer than 50 lines of content (excluding frontmatter)
- No numbered steps or procedural flow
- Content is primarily "MUST" / "MUST NOT" directives without workflow steps
- These belong as `.claude/rules/*.md` files instead

### 5b. Skill Self-Containment

For each skill:

- Check if it references constraints from CLAUDE.md by restating them (duplication)
- Check if it contains content that contradicts a rule file (inconsistency)
- Skills SHOULD be self-contained -- they MAY cross-reference rules by name but MUST NOT copy rule content

---

## STEP 6: Generate Report

Compile all findings into a structured report.

### Report Template

```
## SSOT Audit Report

### Summary
| Metric | Value |
|---|---|
| CLAUDE.md | X lines (OK / WARN / CRITICAL) |
| Rules | X files (Y global, Z scoped, W unscoped) |
| Skills | X directories |
| Settings | present / missing |
| Nested CLAUDE.md | X found |

### Violations Found

| # | Type | Location | Issue | Suggested Fix |
|---|------|----------|-------|---------------|
| 1 | DUPLICATION | CLAUDE.md:15 + rules/testing.md:8 | Same "run tests before commit" constraint | Remove from CLAUDE.md; add pointer: "See .claude/rules/testing.md" |
| 2 | MISPLACED | CLAUDE.md:42-55 | Multi-step deployment workflow | Extract to .claude/skills/deploy/SKILL.md |
| 3 | UNSCOPED | rules/api-patterns.md | No globs or scope declaration | Add `globs: ["**/api/**"]` frontmatter |
| 4 | BLOAT | CLAUDE.md:80-120 | 40-line code block inlined | Move to skill or reference file |
| 5 | LAYER_MISUSE | CLAUDE.md:30 | Code style rule (semicolons) | Move to linter config + hook |

### Health Scores

| Category | Status | Count |
|---|---|---|
| CLAUDE.md bloat | OK / WARN / CRITICAL | line count |
| Cross-layer duplication | X violations | - |
| Unscoped rules | X rules without scope | - |
| Misplaced content | X items in wrong layer | - |
| Skill boundary issues | X skills need reclassification | - |

### Recommendations

[Ordered list of highest-impact fixes, starting with the easiest wins]

1. [Fix description -- estimated effort: low/medium/high]
2. ...
```

### If `--fix` Flag Is Present

For each violation, append a concrete fix section:

```
### Fix #1: Remove duplicated constraint from CLAUDE.md

**File:** CLAUDE.md
**Action:** Remove lines 15-17 (duplicated testing constraint)
**Replace with:** `> Testing standards: see .claude/rules/testing.md`

**File:** (no changes needed to rules/testing.md -- it is the SSOT)
```

Present fixes as suggestions only. Do not apply edits -- allowed-tools is read-only.

---

## CRITICAL RULES

- MUST NOT modify any files -- Why: this skill is read-only (allowed-tools: Read Grep Glob); edits would violate least-privilege and surprise the user
- MUST NOT report false positives for intentional pointers (e.g., "see .claude/rules/X.md" in CLAUDE.md is a cross-reference, not duplication) -- Why: pointers are correct SSOT behavior; flagging them erodes trust in the audit
- MUST distinguish between exact duplication and intentional cross-references -- Why: a one-line pointer to a rule file is the prescribed pattern per configuration-ssot.md; treating it as duplication would recommend removing correct config
- MUST use semantic comparison, not just string matching -- Why: the same concept expressed in different words counts as duplication; string-only matching misses the majority of real violations
- MUST provide a suggested fix for every violation -- Why: reports without actionable fixes waste the user's time and require a second pass to determine remediation
- MUST read the `configuration-ssot` rule (if present in `.claude/rules/`) to use as the authoritative reference for what belongs in which layer -- Why: the rule is the SSOT for layer taxonomy; hardcoding the taxonomy in this skill would itself be an SSOT violation
- MUST NOT flag stack-prefixed rule pairs (e.g., `android.md` and `react-nextjs.md`) as duplicates when they express similar patterns for different stacks -- Why: stack-specific rules legitimately restate similar concepts for different ecosystems
- MUST count content lines only (excluding frontmatter, blank lines, and headings) when assessing whether a skill is a stub -- Why: frontmatter and structural headings inflate line counts and mask genuinely thin content
