---
name: skill-master
description: >
  Route user requests to the right skill by dynamically discovering all available
  skills at runtime. Scans the filesystem for SKILL.md files, reads their frontmatter
  to build a live catalog, matches intent, suggests workflows, and chains skills
  in sequence. Use as the universal entry point when unsure which skill to invoke.
  NOT for prompt strengthening or quality grading (use /prompt-auto-enhance),
  NOT for detecting repeated patterns (use /skill-factory),
  NOT for full development lifecycle orchestration (use /development-loop).
triggers:
  - skill-master
  - which skill
  - what skills are available
  - list skills
  - skill catalog
  - help me pick a skill
allowed-tools: "Read Grep Glob Skill"
argument-hint: "<request or 'list'|'catalog'|'help'> [--workflow] [--chain]"
version: "1.1.0"
type: workflow
---

# Skill Master — Dynamic Skill Router & Orchestrator

Discover all available skills at runtime, match user intent to the best skill, suggest
workflows, and chain skills in sequence. Never hardcodes skill lists — always scans
the filesystem for what is currently available.

**Request:** $ARGUMENTS

---

## STEP 1: Discover All Available Skills

Scan the filesystem to build a live catalog of every skill that exists right now.

### 1.1 Locate Skill Directories

Search for all SKILL.md files in the skills directory using `Glob`:

- Pattern: `core/.claude/skills/*/SKILL.md`
- Fallback pattern: `.claude/skills/*/SKILL.md`

Collect every path found. If zero skills are found, report the error and stop:
```
ERROR: No skills found. Expected SKILL.md files in:
  - core/.claude/skills/*/SKILL.md
  - .claude/skills/*/SKILL.md
Verify the skills directory exists and contains skill subdirectories.
```

### 1.2 Read Frontmatter from Each Skill

For every SKILL.md file discovered, read the YAML frontmatter (the block between `---` delimiters at the top of the file). Extract these fields:

| Field | Required | Use |
|-------|----------|-----|
| `name` | Yes | Unique identifier, used for invocation |
| `description` | Yes | Natural language summary for intent matching |
| `triggers` | No | Explicit activation phrases and slash commands |
| `argument-hint` | No | Shows users what input the skill expects |
| `allowed-tools` | No | Indicates skill capabilities (read-only vs. read-write) |

Store the extracted data in an in-memory catalog structure:

```
Catalog Entry:
  name: "brainstorm"
  description: "Socratic questioning phase before planning..."
  triggers: ["brainstorm", "explore ideas", "design", "spec", ...]
  argument_hint: "<feature or problem description>"
  tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob", "Agent"]
  path: "core/.claude/skills/brainstorm/SKILL.md"
  category: <inferred in Step 1.3>
```

### 1.3 Infer Categories from Descriptions

Classify each skill into a category based on keywords found in its `name` and `description`.
Do NOT hardcode category assignments — derive them dynamically using these keyword rules:

| Category | Detection Keywords in Name or Description |
|----------|------------------------------------------|
| Workflow | "implement", "plan", "execute", "workflow", "feature", "fix", "build" |
| Quality | "debug", "test", "audit", "security", "verify", "lint", "review" |
| Collaboration | "review", "branch", "PR", "code review", "finish", "contribute" |
| Architecture | "architect", "design", "brainstorm", "spec", "explore", "strategy" |
| DevOps | "deploy", "migrate", "CI", "pipeline", "docker", "infrastructure" |
| Stack-Specific | Skill name starts with a known stack prefix (`fastapi-`, `android-`, `flutter-`, `expo-`, `vue-`, `nuxt-`, `firebase-`, `ai-gemini-`, `react-`) |
| Meta | "skill", "learn", "improve", "update", "write-skill", "factory" |
| Utility | Anything that does not match the above categories |

If a skill matches multiple categories, assign the most specific one (Stack-Specific > others).

**Key principle:** If a new skill is added with a description containing "deploy", it automatically
lands in the DevOps category without any code change to skill-master. The category detection
is keyword-driven, not name-driven.

### 1.4 Build the Final Catalog

Assemble all entries into a structured catalog grouped by category. Count totals:

```
Skill Catalog Built:
  Total skills discovered: {N}
  Categories: {list of categories with counts}
  Last scanned: {timestamp}
```

---

## STEP 2: Parse User Intent

Determine what the user wants based on `$ARGUMENTS`.

### 2.1 Detect Mode

| Input Pattern | Mode | Action |
|---------------|------|--------|
| Empty, `list`, `catalog`, `help`, `what skills`, `show all` | **Catalog Display** | Go to Step 3 |
| `--workflow` flag or "suggest a workflow for..." | **Workflow Suggestion** | Go to Step 5 |
| `--chain` flag or "run these in order..." | **Skill Chaining** | Go to Step 6 |
| A natural language request describing a task | **Intent Matching** | Go to Step 4 |
| A specific slash command like `/brainstorm` | **Direct Route** | Go to Step 4 (fast path) |

### 2.2 Assess Task Complexity

Before routing, classify the task complexity to determine the appropriate workflow depth:

| Complexity | Signals | Workflow Depth |
|-----------|---------|----------------|
| **Simple** | Single file, typo fix, config change, "quick", "just" | Skip planning/docs. Route directly to `/implement` or stack-specific skill. |
| **Medium** | 2-5 files, single feature, clear scope, "add", "update" | Standard workflow. Route to `/implement` or `/writing-plans` → `/executing-plans`. |
| **Complex** | 6+ files, cross-layer changes, architecture decisions, "redesign", "migrate", "refactor" | Full pipeline. Route to `/brainstorm` → `/writing-plans` → `/executing-plans` → `/request-code-review`. |

Detection heuristics:
- Count affected files/components mentioned in the request
- Check for cross-layer keywords: "frontend AND backend", "API AND database", "migration"
- Check for scope keywords: "across all", "everywhere", "codebase-wide"
- If uncertain, default to **Medium** and let the routed skill escalate if needed

### 2.3 Extract Key Phrases

From the user's natural language input, extract:
1. **Action verbs** — what they want to do (debug, build, review, deploy, test, migrate)
2. **Object nouns** — what they want to act on (API, database, UI, tests, branch)
3. **Stack references** — technology mentions (FastAPI, Android, Flutter, React, Firebase)
4. **Qualifiers** — urgency, scope, complexity hints (quick, full, deep, all)

These key phrases, combined with the complexity assessment from 2.2, feed into the scoring algorithm in Step 4.

---

## STEP 3: Display Skill Catalog

Present all discovered skills organized by dynamically-inferred category.


**Read:** `references/display-skill-catalog.md` for detailed step 3: display skill catalog reference material.

## STEP 4: Match Intent to Skill

Score each discovered skill against the user's request and route to the best match.


**Read:** `references/match-intent-to-skill.md` for detailed step 4: match intent to skill reference material.

## STEP 5: Suggest Adaptive Workflow

Analyze the user's task and recommend a multi-skill workflow.


**Read:** `references/suggest-adaptive-workflow.md` for detailed step 5: suggest adaptive workflow reference material.

## STEP 6: Chain Skills in Sequence

Execute multiple skills one after another, passing context forward.


**Read:** `references/chain-skills-in-sequence.md` for detailed step 6: chain skills in sequence reference material.

## STEP 7: Manage Session State

Track skill invocations and workflow progress across the session.

### 7.1 State Structure

Maintain a session state that tracks:

```
Session State:
  skills_invoked:
    - name: "brainstorm"
      timestamp: "2024-01-15T10:30:00"
      args: "new auth system"
      output_summary: "Spec written to docs/specs/auth-spec.md"
      status: "completed"
    - name: "writing-plans"
      timestamp: "2024-01-15T10:45:00"
      args: "from docs/specs/auth-spec.md"
      output_summary: "Plan with 8 tasks"
      status: "completed"
  active_workflow:
    name: "New Feature"
    skills: ["brainstorm", "writing-plans", "executing-plans", "branching"]
    current_index: 2
    started_at: "2024-01-15T10:30:00"
  catalog_snapshot:
    total_skills: 45
    last_scanned: "2024-01-15T10:30:00"
```

### 7.2 Persist State to Disk

Write the session state to a scratch file so it survives context compaction:

```bash
# Write state to a scratch file in the project root
cat > .skill-master-state.json << 'EOF'
{
  "skills_invoked": [...],
  "active_workflow": {...},
  "last_catalog_scan": "..."
}
EOF
```

On each invocation of skill-master, check if `.skill-master-state.json` exists:
- If yes: read it to restore session context
- If no: start fresh

### 7.3 State-Aware Suggestions

Use session state to make smarter suggestions:

| State | Suggestion |
|-------|-----------|
| Just completed `/brainstorm` | "You have a spec ready. Continue with `/writing-plans`?" |
| Completed `/implement` but no review | "Implementation done. Ready for `/request-code-review`?" |
| Multiple debugging sessions | "You have debugged 3 issues. Consider `/security-audit` for a broader check." |
| No skills invoked yet | "Welcome! Describe what you want to do, or type `/skill-master list`." |
| Workflow partially complete | "You have an active workflow. Resume from Step {N}?" |

---

## STEP 8: Handle Skill Conflicts and Overlap

When multiple skills could handle the same request, help the user choose.

### 8.1 Detect Overlap

During intent matching (Step 4), if two or more skills score within 10 points of each other,
flag a conflict. Read both skills' full descriptions to understand their differences.

### 8.2 Present Comparison

```
SKILL OVERLAP DETECTED

  /implement vs /executing-plans

  | Aspect | /implement | /executing-plans |
  |--------|-----------|-----------------|
  | Input | Feature description (freeform) | Pre-written plan document |
  | Approach | Analyzes requirements from scratch | Follows existing plan step by step |
  | Best for | Ad-hoc features and bug fixes | Planned work from /writing-plans |
  | Includes testing | Yes (built-in TDD) | Depends on plan content |

  RECOMMENDATION: Use /implement for standalone tasks.
                   Use /executing-plans when you have a plan from /writing-plans.

  Your choice? (1: /implement, 2: /executing-plans)
```

### 8.3 Build Comparison from Frontmatter

The comparison table MUST be built by reading the actual skill descriptions and
extracting differences — not from hardcoded knowledge. For any two skills:

1. Read both full SKILL.md files
2. Extract: input expectations, step count, tools used, output produced
3. Compare along these axes and present the differences
4. Make a recommendation based on the user's stated task

---

## STEP 9: Search Skills by Keyword

When the user's request does not match any skill well, provide a keyword search.

### 9.1 Full-Text Search

Search across all discovered skill descriptions, triggers, and step content using `Grep`
with the user's keywords against all SKILL.md files. Report matches with the relevant
context line.

### 9.2 Present Search Results

```
SEARCH RESULTS for "database migration":

  1. /fastapi-db-migrate (3 matches)
     - Description: "...database migration..."
     - Step 2: "Run alembic to generate migration..."
     - Trigger: "migrate database"

  2. /pg-query (1 match)
     - Description: "...PostgreSQL query patterns..."

  No exact match? Consider:
    - /writing-skills to create a custom skill for this workflow
    - /brainstorm to explore the problem before choosing a skill
```

### 9.3 Fuzzy Matching

When exact keyword search yields no results, try partial matches:

1. Split multi-word keywords and search each word independently
2. Search for synonyms: "test" also matches "verify", "check", "validate"
3. Search skill names (not just descriptions) for partial prefix matches

---

## STEP 10: Self-Update and Re-Scan

Ensure the catalog is always fresh.

### 10.1 Re-Scan on Every Invocation

Every time skill-master is invoked, re-run Step 1 in full. Do NOT cache or reuse
a previous catalog. Skills may have been added, removed, or modified since the
last invocation.

### 10.2 Detect Changes

If session state exists from a previous invocation, compare the new catalog against
the stored snapshot:

```
CATALOG CHANGES SINCE LAST SCAN:
  + /new-skill-name (added — description: "...")
  - /removed-skill (no longer found on disk)
  ~ /modified-skill (description changed)
  = {N} skills unchanged
```

### 10.3 Handle Missing Skills in Active Workflows

If a skill that is part of an active workflow (Step 6) has been removed from disk:

1. Alert the user: "Skill `/removed-skill` is no longer available on disk."
2. Suggest a replacement by searching the catalog for similar descriptions
3. Offer to skip the removed skill and continue the workflow

---

## Routing Decision Examples

These examples show how the scoring algorithm routes requests. The specific skills
mentioned are illustrative — actual routing always uses the live catalog from Step 1.


**Read:** `references/routing-decision-examples.md` for detailed routing decision examples reference material.

## MUST DO

- Always re-scan the filesystem on every invocation — never serve a stale catalog — Why: skills may be added, removed, or modified between invocations
- Always read actual YAML frontmatter from SKILL.md files — never guess or assume skill metadata — Why: descriptions and triggers change; stale metadata causes misroutes
- Always present match confidence and reasoning — Why: users need to understand why a skill was chosen so they can correct misroutes
- Always offer alternatives when confidence is below "high" — Why: forcing a weak match wastes time if the wrong skill runs
- Always persist session state to `.skill-master-state.json` — Why: context compaction erases in-memory state; disk state survives
- Always validate that a skill exists on disk before invoking it — Why: the catalog may reference a skill that was deleted mid-session
- Always derive categories from skill descriptions — Why: hardcoded mappings break when skills are added or renamed
- Always build workflows by reading skill handoff hints — Why: fixed pipeline sequences become stale when skills change

## MUST NOT DO

- MUST NOT hardcode any skill names, descriptions, or categories — always discover from disk. Hardcoding defeats the purpose of dynamic discovery.
- MUST NOT cache the skill catalog between invocations — always re-scan. Skills may be added or removed at any time.
- MUST NOT route to a skill without presenting the match reasoning — users must understand why a skill was chosen so they can correct misroutes.
- MUST NOT execute a full workflow chain without user confirmation at each step — always checkpoint between skills.
- MUST NOT assume a fixed workflow sequence — derive workflows from skill descriptions and handoff hints.
- MUST NOT invoke a skill that was not found during the filesystem scan — validate existence before routing.
- MUST NOT present the catalog from memory — every catalog display must reflect a fresh filesystem scan.
- MUST NOT skip Step 1 (discovery) under any circumstance — it is the foundation of every other step.
