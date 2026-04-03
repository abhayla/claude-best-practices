---
name: learn-n-improve
description: >
  Analyze session outcomes and update memory topics (testing-lessons, fix-patterns,
  skill-gaps) for continuous self-improvement. Four modes: session, deep, meta, test-run.
  Use when a session ends, after a fix succeeds, or when reviewing learning effectiveness.
  For full learning cycles (capture + pattern detection + skill proposals), use
  /learning-self-improvement instead. For one-off session saves, use /save-session.
  For full handover docs, use /handover.
type: workflow
triggers:
  - learn from session
  - capture learnings
  - record what we learned
  - session reflection
  - what did we learn
  - improve from mistakes
  - learn-n-improve
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode: session|deep|meta|test-run>"
version: "2.4.0"
---

# Learn & Improve — Session Reflection

Analyze session outcomes and update learning files for future sessions.

**Critical:** MUST NOT inject constraints into skills without user approval. MUST NOT modify learnings.json in `test-run` mode. If $ARGUMENTS is empty, default to `session` mode.

**Mode:** $ARGUMENTS

---

## Modes

| Mode | When to Use | What it Does |
|------|-------------|-------------|
| `session` | After completing work | Capture outcomes, update memory topics |
| `deep` | After recurring failures | Analyze patterns, suggest skill/rule modifications |
| `meta` | Periodically | Evaluate if learning system is effective |
| `test-run` | Before committing changes | Dry run — show what would be updated |

---

## STEP 1: Gather Session Evidence

In `test-run` mode: read-only throughout — skip all writes, print proposed changes only.

Collect evidence from these sources:

```bash
git log --oneline -20
```

```bash
ls test-results/*.json 2>/dev/null
```

Read `.claude/learnings.json` if it exists. Read any scratchpad or session files from `.claude/sessions/`.

| Source | What to extract |
|--------|----------------|
| `git log` | Commit messages, files changed, reverts (indicate failures) |
| `test-results/*.json` | Pass/fail counts, failure categories, flaky tests |
| `test-evidence/` | Fix-loop iteration count, screenshot evidence |
| Modified files | Which areas of codebase were touched |

## STEP 2: Analyze Outcomes

Categorize session work using this decision table:

| Evidence Signal | Category | Action |
|----------------|----------|--------|
| `git revert` in log | **Failure** | Record what was reverted and why |
| test-results `FAILED` | **Failure** | Extract root cause from failure entries |
| test-results `PASSED` after prior `FAILED` | **Success** | Record the fix pattern |
| Fix-loop iterations > 1 | **Workaround** | Check if the fix was minimal or structural |
| New files created with no test coverage | **Knowledge gap** | Flag for test creation |
| Repeated Grep/Read on same area | **Knowledge gap** | Record as area needing documentation |

## STEP 3: Build Error→Fix→Lesson Database

For each error encountered and fixed during the session, record a structured triple in `.claude/learnings.json`:

```json
{
  "learnings": [
    {
      "id": "L001",
      "date": "2026-03-12",
      "error": {
        "message": "TypeError: Cannot read property 'id' of undefined",
        "file": "src/services/user.py",
        "context": "Accessing user.id when user lookup returned None"
      },
      "fix": {
        "description": "Added null check before accessing user properties",
        "diff": "if user is None: raise UserNotFoundError(user_id)"
      },
      "lesson": "Always validate ORM query results before accessing attributes. Use Optional types.",
      "tags": ["null-handling", "orm", "python"],
      "reuse_count": 0,
      "hub_pattern_link": null
    }
  ]
}
```

### Hub Pattern Linkage (Effectiveness Telemetry)

For each new learning, determine which hub pattern — if any — should have
prevented or caught this error. This links errors to patterns, enabling
cross-project effectiveness measurement.

1. **Auto-suggest**: Match the learning's `tags` against `registry/patterns.json`
   tag fields. If a hub pattern's tags overlap >= 50% with the error's tags,
   suggest it as `hub_pattern_link`. Present top 1-3 candidates.
2. **User confirms**: Show the suggestion — the user picks one or skips.
   If skipped, set `hub_pattern_link: null`.
3. **Write the link**: Store the selected pattern name as `hub_pattern_link`.

Example:
```
Hub pattern link suggestion for L042:
  Error tags: ["security", "sql"]
  Candidates:
    1. security-audit (tags: security, audit — 50% overlap)
    2. fastapi-backend (tags: fastapi, backend — 0% overlap)
  → Link to: security-audit? [Y/n/skip]
```

This data feeds `aggregate_telemetry.py` to compute per-pattern error
prevention rates across enrolled projects.

For each error→fix pair from the session:
1. Search existing learnings for similar errors (match by error message, file path, tags)
2. If similar learning exists, increment `reuse_count` and update if the fix is better
3. If new, append with next sequential ID
4. Tag generously for future searchability

## STEP 4: Update Memory Topics

Update files in the project's memory directory:

| File | Content |
|------|---------|
| `fix-patterns.md` | Recurring fix patterns with file references |
| `testing-lessons.md` | Testing insights and fixture knowledge |
| `skill-gaps.md` | Areas where skills need improvement |
| `.claude/learnings.json` | Structured error→fix→lesson database (Step 3) |

For each update:
1. Read existing file
2. Check for duplicates
3. Append new entries with date stamps
4. Remove outdated entries

## STEP 5: Pattern Detection (every 10th learning)

After every 10th entry in `.claude/learnings.json`, scan for systemic patterns:

1. **Tag frequency analysis** — Which tags appear most often?
   - If a tag appears in 30%+ of learnings → systemic issue
   - Example: `null-handling` in 8 of 20 learnings → "80% of errors relate to null handling"

2. **File hotspot analysis** — Which files generate the most errors?
   - If a file appears in 3+ learnings → fragile code, consider refactoring

3. **Suggest project-wide fixes:**
   - Frequent null errors → suggest adding strict null checks as a lint rule
   - Frequent test failures → suggest testing rule enhancement
   - Frequent API errors → suggest validation middleware

4. **Propose rules** — For patterns that appear 5+ times, suggest a new rule for `.claude/rules/`. Every proposed rule MUST include:
   - A `description:` field in frontmatter
   - A `globs:` field scoping it to relevant file patterns, OR `# Scope: global` if it applies everywhere
   - Actionable content (not placeholder/TODO stubs)

   ```
   Pattern detected: "null-handling" appears in 8 learnings.
   Suggested rule:
   ---
   description: Enforce null-safety checks on ORM query results.
   globs: ["**/*.py", "**/*.ts"]
   ---
   # ORM Null Safety
   All ORM queries MUST check for None/null before accessing attributes.
   Use Optional types and guard clauses instead of bare attribute access.

   Add to: .claude/rules/ ? (requires user approval)
   ```

5. **Workflow pattern detection** — Delegate to `/skill-factory scan` for repeated tool sequence detection. Do NOT reimplement workflow fingerprinting here — skill-factory owns that capability. If tag frequency or file hotspot analysis suggests a recurring workflow, mention it in the report and suggest running `/skill-factory scan` to investigate.

## STEP 5.5: Inject Active Constraints into Skills

Close the feedback loop: take proven learnings and propose injecting them as
active constraints into the specific skills they relate to. This converts
passive knowledge (recorded in `learnings.json`) into active prevention
(embedded in skill CRITICAL RULES).

**Trigger**: Only activates when a learning has `reuse_count >= 2` — proven
recurring, not a one-off. Skip this step entirely if no learnings meet the
threshold.

### 5.5.1 Map Learnings to Skills

For each learning with `reuse_count >= 2`, identify the target skill:

| Learning Signal | Target Skill | Match Method |
|---|---|---|
| Tags match a skill name | That skill | `tags` contains skill name (e.g., `"fix-loop"`) |
| Error occurred during a skill run | That skill | `context` mentions `/skill-name` invocation |
| Error file matches a skill's `globs:` | That skill | File path matches skill's operational scope |
| No skill match found | Skip | Record as general learning, do not force-fit |

```bash
# Find learnings eligible for constraint injection
python3 -c "
import json
learnings = json.load(open('.claude/learnings.json'))
eligible = [l for l in learnings.get('learnings', []) if l.get('reuse_count', 0) >= 2]
for l in eligible:
    print(f\"  {l['id']}: reuse={l['reuse_count']} tags={l.get('tags', [])} lesson={l['lesson'][:80]}\")
print(f'Total eligible: {len(eligible)}')
"
```

### 5.5.2 Draft Constraint Proposal

For each mapped learning, draft a constraint in the target skill's voice:

```
Constraint Injection Proposal:
  Learning: L007 (reuse_count: 3)
  Lesson: "Always validate ORM query results before accessing attributes"
  Target skill: /systematic-debugging
  Proposed addition to CRITICAL RULES:

    - When diagnosing null/undefined errors on ORM objects, check query results
      FIRST — 60% of these are missing null guards, not logic bugs.
      Evidence: L007 (seen 3 times across sessions)

  Action: Add to systematic-debugging/SKILL.md MUST DO section? (requires user approval)
```

### 5.5.3 Approval Gate

MUST NOT modify any skill file without explicit user approval. Present all
proposals in a batch:

```
Active Constraint Proposals (N total):

| # | Learning | Target Skill | Proposed Constraint | Reuse Count |
|---|----------|-------------|-------------------|-------------|
| 1 | L007     | /systematic-debugging | Check ORM null guards first | 3 |
| 2 | L012     | /fix-loop | Skip retry if error is import-related | 2 |

Apply all / Select individually / Skip all?
```

If approved, append the constraint to the target skill's `MUST DO` or
`CRITICAL RULES` section with an evidence tag linking back to the learning ID.

### 5.5.4 Record Injection

After injection, update the learning entry:

```json
{
  "id": "L007",
  "injected_into": "systematic-debugging",
  "injected_date": "2026-03-23",
  "constraint_text": "Check ORM null guards first when diagnosing null errors"
}
```

This prevents re-proposing the same constraint in future sessions.

> **Reference:** See [references/self-improving-skill-design.md](references/self-improving-skill-design.md)
> for the design philosophy behind feedback-as-active-constraints.

## STEP 6: Report

```
Learning Update:
  Mode: [session/deep/meta/test-run]
  New learnings: N (error→fix→lesson triples)
  Updated learnings: M (reuse_count incremented)
  Topics affected: [list]
  Total learnings in database: X

  Pattern alerts (if any):
  - "null-handling" detected in 40% of learnings — consider project-wide fix

  Workflow patterns (if any):
  - WP001 seen 4 times: "TDD cycle" — consider creating skill via /writing-skills
```

---

## Semi-Automatic Invocation via Hook

To run `learn-n-improve` automatically after every skill invocation, add a PostToolUse hook:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Skill",
        "command": ".claude/hooks/auto-learn.sh"
      }
    ]
  }
}
```

```bash
#!/bin/bash
# .claude/hooks/auto-learn.sh — Trigger learning capture after skill runs
# Uses a counter to avoid running on every single skill invocation.
# Default: runs learn-n-improve in session mode every 5th skill call.

COUNTER_FILE="${TMPDIR:-/tmp}/claude-learn-counter.txt"
FREQUENCY=${LEARN_FREQUENCY:-5}

COUNT=0
if [[ -f "$COUNTER_FILE" ]]; then
  COUNT=$(cat "$COUNTER_FILE")
fi
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

if [[ $((COUNT % FREQUENCY)) -eq 0 ]]; then
  echo "Auto-learning: $COUNT skill invocations since last capture. Consider running /learn-n-improve session to record patterns."
fi
exit 0
```

This keeps learning semi-automatic — the hook reminds Claude to run the skill periodically rather than requiring the user to remember. Adjust `LEARN_FREQUENCY` via environment variable.

---

## CRITICAL RULES

- MUST NOT delete historical entries without evidence they're wrong — Why: learnings are training data for pattern detection; deleting breaks frequency analysis
- MUST date-stamp all new entries — Why: enables staleness detection and temporal pattern analysis
- MUST cross-reference with existing patterns before adding — Why: duplicate entries inflate frequency counts and produce false pattern alerts
- MUST NOT write any files in `test-run` mode — Why: test-run is for previewing changes without side effects; writing defeats its purpose
- MUST NOT inject constraints into skills without explicit user approval (Step 5.5.3) — Why: unsolicited skill modifications break trust and may conflict with user intent
- MUST NOT inject constraints from learnings with `reuse_count < 2` — Why: one-off errors are noise, not patterns; premature injection creates brittle rules
- MUST record injection metadata in the learning entry to prevent re-proposing (Step 5.5.4) — Why: without tracking, the same constraint gets proposed every session
- MUST default to `session` mode when $ARGUMENTS is empty — Why: asking for mode selection adds friction when the common case is always "session"
