---
name: skill-master
description: >
  Route user requests to the right skill by dynamically discovering all available
  skills at runtime. Scans the filesystem for SKILL.md files, reads their frontmatter
  to build a live catalog, matches intent, suggests workflows, and chains skills
  in sequence. Use as the universal entry point when unsure which skill to invoke.
triggers:
  - skill-master
  - master
  - route
  - which skill
  - what skills are available
  - list skills
  - skill catalog
  - help me pick a skill
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "<request or 'list'|'catalog'|'help'> [--workflow] [--chain]"
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

Search for all SKILL.md files in the skills directory:

```bash
# Find all skill definitions relative to the project root
# Try both paths — hub layout and user-project layout
find core/.claude/skills/*/SKILL.md .claude/skills/*/SKILL.md 2>/dev/null
```

Use `Glob` to find all matching files:
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

### 3.1 Generate Catalog Output

For each category inferred in Step 1.3, list the skills belonging to it:

```
=== SKILL CATALOG ===
Discovered {N} skills across {M} categories.

--- Architecture ---
  /brainstorm          — Socratic questioning phase before planning or implementation
  /strategic-architect — <description from frontmatter>

--- Workflow ---
  /implement           — Implement a feature or fix following a structured workflow
  /executing-plans     — <description from frontmatter>
  /writing-plans       — <description from frontmatter>
  /fix-loop            — <description from frontmatter>
  /fix-issue           — <description from frontmatter>

--- Quality ---
  /systematic-debugging — <description from frontmatter>
  /security-audit       — <description from frontmatter>
  /supply-chain-audit   — <description from frontmatter>
  /auto-verify          — <description from frontmatter>

--- Collaboration ---
  /request-code-review  — <description from frontmatter>
  /receive-code-review  — <description from frontmatter>
  /branching        — <description from frontmatter>
  /contribute-practice  — <description from frontmatter>

--- Stack-Specific ---
  /fastapi-db-migrate   — <description from frontmatter>
  /android-run-tests    — <description from frontmatter>
  /flutter-dev          — <description from frontmatter>
  ... (all stack-prefixed skills)

--- Meta ---
  /writing-skills       — Guide for authoring new skills
  /skill-master         — This skill (dynamic router)
  /skill-factory        — <description from frontmatter>

--- Utility ---
  ... (remaining skills)

=== END CATALOG ===
```

Every description shown MUST come from the actual frontmatter read in Step 1.2 — never
from memory or hardcoded text.

### 3.2 Show Usage Hints

After the catalog, display:

```
USAGE:
  /skill-master <describe what you want>    — Route to the best skill
  /skill-master list                        — Show this catalog
  /skill-master --workflow <task>           — Suggest a multi-skill workflow
  /skill-master --chain <skill1,skill2>     — Execute skills in sequence
```

### 3.3 Show Quick Workflows

Scan all skill descriptions for handoff hints (phrases like "proceed with", "next step",
"feeds into", "then invoke", "follow up with"). Build a list of detected workflows:

```
DETECTED WORKFLOWS:
  Feature Development: /brainstorm -> /writing-plans -> /executing-plans -> /implement -> /branching
  Bug Fix: /systematic-debugging -> /fix-loop -> /auto-verify -> /branching
  Code Review: /request-code-review -> /receive-code-review -> /branching
  (workflows above are derived from skill descriptions — they update automatically)
```

These workflows MUST be derived by reading skill descriptions for handoff references,
not from a hardcoded list. If a new skill mentions "after this, invoke /deploy", that
link appears automatically.

---

## STEP 4: Match Intent to Skill

Score each discovered skill against the user's request and route to the best match.

### 4.1 Scoring Algorithm

For each skill in the catalog, calculate a match score:

| Signal | Points | How to Detect |
|--------|--------|---------------|
| Exact trigger match | 100 | User input exactly matches a trigger string from frontmatter |
| Slash command match | 90 | User typed `/<name>` and it matches a skill name |
| Trigger substring match | 60 | A trigger from frontmatter appears as a substring in the user's input |
| Description keyword match | 40 | 2+ key phrases from user input appear in the skill's description |
| Single keyword match | 20 | 1 key phrase from user input appears in the skill's description |
| Stack prefix match | 30 | User mentions a technology and a skill has the matching stack prefix |
| Category alignment | 10 | User's action verb maps to the skill's inferred category |

Sum the points for each skill. Rank by total score descending.

### 4.2 Present Results

Based on the scoring results:

| Scenario | Action |
|----------|--------|
| Top skill scores >= 80 and is 20+ points ahead of #2 | **Strong match** — Route directly. Present: "Routing to `/skill-name` — {description}. Invoke now? (Y/n)" |
| Top 2-3 skills score >= 40 with < 20 point spread | **Ambiguous match** — Present top 3 with scores and let user pick |
| No skill scores >= 40 | **No match** — Go to Step 4.3 |

#### Strong Match Example

```
MATCH FOUND (confidence: high)
  Skill: /systematic-debugging
  Description: Structured debugging methodology with hypothesis testing
  Match reason: Your request mentions "debug" and "failing test" — exact trigger match

  Invoke /systematic-debugging now? (Y/n)
```

#### Ambiguous Match Example

```
MULTIPLE MATCHES — please pick one:

  1. /implement (score: 65)
     Implement a feature or fix following a structured workflow
     Match: "build" keyword in your request matches description

  2. /executing-plans (score: 55)
     Execute tasks from a pre-written plan
     Match: "build" keyword, but requires a plan as input

  3. /brainstorm (score: 45)
     Explore approaches before committing to implementation
     Match: "feature" keyword in your request

  Which skill? (1/2/3 or describe your task in more detail)
```

### 4.3 Handle No Match

When no skill scores above the threshold:

1. Show the closest match (highest score even if below threshold) with an explanation of the gap:
   ```
   CLOSEST MATCH (low confidence):
     Skill: /implement (score: 25)
     Gap: Your request mentions "refactor database schema" but no skill
          specifically handles schema refactoring.
   ```

2. Suggest alternatives:
   ```
   SUGGESTIONS:
     - Rephrase your request with different keywords
     - Use /writing-skills to create a new skill for this task
     - Use /brainstorm to explore the problem space first
     - Browse the full catalog: /skill-master list
   ```

3. Offer a keyword-based search across all skill descriptions:
   ```
   SEARCH RESULTS for "database schema":
     /fastapi-db-migrate  — mentions "database" and "migration" in description
     /pg-query            — mentions "database" and "query" in description
   ```

### 4.4 Route to Selected Skill

Once the user confirms (or the match is strong enough for auto-routing):

1. Read the full SKILL.md content of the selected skill (not just frontmatter)
2. Invoke the skill using the Skill tool:
   ```
   Skill("<skill-name>", args="<user's original request>")
   ```
3. Record the invocation in session state (Step 7)

---

## STEP 5: Suggest Adaptive Workflow

Analyze the user's task and recommend a multi-skill workflow.

### 5.1 Classify Task Type

Read the user's description and classify the task:

| Task Signal | Detected Type | Notes |
|-------------|--------------|-------|
| "bug", "error", "failing", "broken", "crash" | Bug Fix | Start with diagnosis |
| "new feature", "add", "build", "create" (large scope) | New Feature | Full planning pipeline |
| "quick fix", "small change", "tweak", "typo" | Quick Fix | Minimal pipeline |
| "review", "PR", "pull request", "feedback" | Code Review | Review pipeline |
| "security", "vulnerability", "CVE", "audit" | Security | Audit pipeline |
| "deploy", "ship", "release", "publish" | Deployment | Deploy pipeline |
| "refactor", "clean up", "restructure" | Refactoring | Analysis + implementation |
| "test", "coverage", "failing tests" | Testing | Test-focused pipeline |
| Stack-specific technology mentioned | Stack Task | Route to stack skill |

### 5.2 Build Workflow from Discovered Skills

For the detected task type, scan the catalog built in Step 1 and assemble a workflow.

**Algorithm:**
1. Identify the "entry" skill — the one whose description best matches the starting action for this task type
2. Read that skill's full content and look for handoff suggestions (references to other skills like "proceed with `/implement`" or "next step: `/branching`")
3. Follow the handoff chain, reading each referenced skill to find the next link
4. If the chain breaks (a skill has no handoff), fill gaps by matching category to task phase:
   - Analysis phase: look for Quality/Architecture category skills
   - Implementation phase: look for Workflow category skills
   - Verification phase: look for Quality category skills
   - Delivery phase: look for Collaboration category skills

### 5.3 Define Entry/Exit Criteria

For each step in the workflow, define what must be true before starting (entry) and what the step must produce (exit). This prevents skipping phases or moving forward prematurely.

| Phase | Entry Criteria | Exit Criteria |
|-------|---------------|---------------|
| Research/Brainstorm | Clear problem statement from user | Research brief + spec document with chosen approach |
| Planning | Approved spec/approach | Plan with tasks, verification commands, dependency graph |
| Execution | Approved plan saved to file | All tasks completed, tests passing, code committed |
| Standards check | Implementation complete, tests green | Standards report with 0 critical violations |
| Code review | Standards check passed | PR created with risk analysis and review questions |
| Review feedback | Review comments received | All must-fix addressed, re-review requested |
| Finish | PR approved, CI green | Merged, verified, branch cleaned up |

When presenting a workflow, include entry/exit criteria so the user knows what each phase requires and produces.

**Present the workflow:**

```
SUGGESTED WORKFLOW for: "{user's task description}"
Task type: New Feature

  Step 1: /brainstorm — Explore approaches and write a spec
    Entry: clear problem statement | Exit: spec document with chosen approach
  Step 2: /writing-plans — Break the spec into a task plan
    Entry: approved spec | Exit: plan with tasks + verification commands
  Step 3: /executing-plans — Execute each task in the plan
    Entry: approved plan | Exit: all tasks done, tests passing
  Step 4: /pr-standards — Check against team standards
    Entry: implementation complete | Exit: 0 critical violations
  Step 5: /request-code-review — Get review feedback
    Entry: standards passed | Exit: PR created with risk analysis
  Step 6: /receive-code-review — Apply review feedback
    Entry: review comments | Exit: all must-fix addressed
  Step 7: /branching finish — Merge and cleanup
    Entry: PR approved, CI green | Exit: merged, verified, cleaned up

  Estimated steps: 7
  Note: Steps were derived from skill handoff hints in descriptions.
        This workflow updates automatically when skills change.

  Start this workflow? (Y/n/modify)
```

### 5.3 Allow Workflow Modification

If the user says "modify" or suggests changes:

1. Show the full catalog filtered to relevant categories
2. Let the user add, remove, or reorder skills
3. Validate the modified workflow: check that each skill exists in the catalog
4. Confirm the final workflow before starting

---

## STEP 6: Chain Skills in Sequence

Execute multiple skills one after another, passing context forward.

### 6.1 Parse the Chain

Accept chain input in these formats:

| Format | Example |
|--------|---------|
| Comma-separated names | `brainstorm,writing-plans,executing-plans` |
| Slash-command list | `/brainstorm /writing-plans /executing-plans` |
| Workflow from Step 5 | User confirmed a suggested workflow |

Validate every skill name against the catalog from Step 1. If any skill is not found:

```
ERROR: Skill "{name}" not found in catalog.
Available skills: {list of all discovered skill names}
Did you mean: {closest name match}?
```

### 6.2 Initialize Progress Tracker

Create a progress display:

```
WORKFLOW PROGRESS: {workflow-name or "Custom Chain"}
  [x] /brainstorm — completed (output: spec written to docs/specs/feature-spec.md)
  [ ] /writing-plans — in progress
  [ ] /executing-plans — pending
  [ ] /request-code-review — pending
  [ ] /branching — pending

  Current: Step 2 of 5
```

### 6.3 Execute Each Skill

For each skill in the chain:

1. **Pre-check** — Read the skill's frontmatter to verify prerequisites
2. **Invoke** — Call `Skill("<name>", args="<context from previous skill>")`:
   - For the first skill: pass the user's original request as args
   - For subsequent skills: pass a summary of the previous skill's output as args
3. **Capture output** — Record what the skill produced (files created, decisions made, artifacts)
4. **Update progress** — Mark the skill as completed in the tracker
5. **Checkpoint** — Between skills, ask the user:
   ```
   /brainstorm completed. Output: spec written to docs/specs/feature-spec.md
   Next: /writing-plans — Break spec into task plan
   Continue? (Y/skip/stop)
   ```

| User Response | Action |
|---------------|--------|
| Y / yes / enter | Proceed to next skill |
| skip | Skip this skill, move to the next one |
| stop | Halt the chain, preserve progress state |
| modify | Show remaining skills, allow reordering |

### 6.4 Handle Chain Failures

If a skill fails or produces an error during chaining:

| Failure Type | Action |
|-------------|--------|
| Skill not found at runtime | Re-scan filesystem (skill may have been deleted), report if still missing |
| Skill errors during execution | Capture error, ask user: retry / skip / stop |
| User cancels mid-chain | Save progress state, offer to resume later |
| Context too large | Summarize previous outputs, trim to essential context |

### 6.5 Chain Completion Report

After all skills in the chain complete (or the chain is stopped):

```
WORKFLOW COMPLETE
  Skills executed: 5/6
  Skills skipped: 1 (request-code-review — skipped by user)

  Artifacts produced:
    - docs/specs/feature-spec.md (from /brainstorm)
    - docs/plans/feature-plan.md (from /writing-plans)
    - 3 files modified (from /executing-plans)
    - Branch ready for PR (from /branching)

  Suggested follow-up:
    - /request-code-review (was skipped — run when ready)
    - /learn-n-improve session (capture learnings)
```

---

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

Search across all discovered skill descriptions, triggers, and step content:

```bash
# Search all SKILL.md files for the user's keywords
grep -r -l "{keyword}" core/.claude/skills/*/SKILL.md
```

Use `Grep` to search all SKILL.md files for the user's keywords. Report matches with
the relevant context line.

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

### Example 1: Direct Trigger Match

```
User: "I need to debug a failing test"
Scan: Found skill with trigger "debug" → /systematic-debugging (score: 100)
Route: Direct match, high confidence
Action: Invoke /systematic-debugging with args "failing test"
```

### Example 2: Stack-Specific Routing

```
User: "Run my Android unit tests"
Scan: Found skill with prefix "android-" and "test" in name → /android-run-tests (score: 90)
Also matched: /auto-verify (score: 30, generic testing)
Route: Stack-specific match wins
Action: Invoke /android-run-tests
```

### Example 3: Ambiguous Request

```
User: "Help me with this code"
Scan: Multiple low-confidence matches:
  /implement (score: 25) — "code" appears in description
  /request-code-review (score: 25) — "code" appears in description
  /systematic-debugging (score: 20) — general development tool
Route: Ambiguous — ask user to clarify
Action: Present top 3, ask "Are you trying to: build something, review code, or fix a bug?"
```

### Example 4: Workflow Request

```
User: "I want to build a new authentication system"
Scan: "new" + "build" + large scope → Task type: New Feature
Workflow suggestion:
  1. /brainstorm — Explore auth approaches (OAuth, JWT, session-based)
  2. /writing-plans — Break chosen approach into tasks
  3. /executing-plans — Implement each task
  4. /security-audit — Verify auth security
  5. /request-code-review — Get team feedback
  6. /branching — Prepare PR
Action: Present workflow, ask user to confirm or modify
```

### Example 5: No Match with Search Fallback

```
User: "Generate API documentation from my code"
Scan: No skill scores above 40
Closest: /brainstorm (score: 15) — "documentation" is not a trigger
Search: Grep "documentation" across all SKILL.md files → 0 results
Action: Report no match, suggest /writing-skills to create an api-docs skill
```

### Example 6: Conflict Resolution

```
User: "I have a plan, help me build it"
Scan: Two strong matches:
  /implement (score: 65) — "build" trigger
  /executing-plans (score: 60) — "plan" + "execute" in description
Action: Present comparison table, recommend /executing-plans because user said "I have a plan"
```

---

## MUST DO

- Always re-scan the filesystem on every invocation — never serve a stale catalog
- Always read actual YAML frontmatter from SKILL.md files — never guess or assume skill metadata
- Always present match confidence and reasoning — users need to understand why a skill was chosen
- Always offer alternatives when confidence is below "high" — do not force a weak match
- Always persist session state to `.skill-master-state.json` — context compaction will erase in-memory state
- Always validate that a skill exists on disk before invoking it — the catalog may reference a deleted skill
- Always derive categories from skill descriptions — never maintain a hardcoded category-to-skill mapping
- Always build workflows by reading skill handoff hints — never assume a fixed pipeline sequence

## MUST NOT DO

- MUST NOT hardcode any skill names, descriptions, or categories — always discover from disk. Hardcoding defeats the purpose of dynamic discovery.
- MUST NOT cache the skill catalog between invocations — always re-scan. Skills may be added or removed at any time.
- MUST NOT route to a skill without presenting the match reasoning — users must understand why a skill was chosen so they can correct misroutes.
- MUST NOT execute a full workflow chain without user confirmation at each step — always checkpoint between skills.
- MUST NOT assume a fixed workflow sequence — derive workflows from skill descriptions and handoff hints.
- MUST NOT invoke a skill that was not found during the filesystem scan — validate existence before routing.
- MUST NOT present the catalog from memory — every catalog display must reflect a fresh filesystem scan.
- MUST NOT skip Step 1 (discovery) under any circumstance — it is the foundation of every other step.
