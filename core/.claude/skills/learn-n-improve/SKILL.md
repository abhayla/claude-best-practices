---
name: learn-n-improve
description: >
  Analyze session outcomes and update memory topics (testing-lessons, fix-patterns,
  skill-gaps) for continuous self-improvement. Four modes: session, deep, meta, test-run.
  Use when a session ends, after a fix succeeds, or when reviewing learning effectiveness.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode: session|deep|meta|test-run>"
version: "2.2.0"
type: workflow
---

# Learn & Improve — Session Reflection

Analyze session outcomes and update learning files for future sessions.

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

Read recent session artifacts:
- Git log (recent commits)
- Test results (if any)
- Fix-loop outcomes (if any)
- Files modified

## STEP 2: Analyze Outcomes

Categorize session work:
- **Successes** — What worked well, patterns to reinforce
- **Failures** — What went wrong, root causes identified
- **Workarounds** — Temporary fixes that should become permanent
- **Knowledge gaps** — Areas where more context was needed

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
      "reuse_count": 0
    }
  ]
}
```

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

5. **Workflow pattern detection** — Scan session transcripts for repeated tool call sequences that could become skills:

   a. **Fingerprint tool sequences** — Identify recurring multi-step patterns:
      - Extract tool call sequences from the session (e.g., Read→Grep→Edit→Bash(test))
      - Compare against previously recorded sequences in `.claude/workflow-patterns.json`
      - A "match" is 3+ identical tool steps in the same order on similar file types

   b. **Track frequency** — Record each workflow pattern with a count:
      ```json
      {
        "patterns": [
          {
            "id": "WP001",
            "sequence": ["Read(test file)", "Edit(test file)", "Bash(run test)", "Edit(source)", "Bash(run test)"],
            "description": "TDD cycle: read test, update test, run, fix source, run again",
            "seen_count": 4,
            "first_seen": "2026-03-01",
            "last_seen": "2026-03-12"
          }
        ]
      }
      ```

   c. **Promotion threshold** — When a workflow pattern is seen 3+ times:
      ```
      Workflow pattern detected: "WP001" seen 3 times.
      Sequence: Read(test) → Edit(test) → Bash(test) → Edit(source) → Bash(test)
      Description: TDD cycle

      This repeated workflow could be a skill.
      Suggested action: Run /writing-skills to create a skill from this pattern.
      Promote to skill? (requires user approval)
      ```

   d. **Noise filtering** — Do NOT flag as workflow patterns:
      - Simple read→edit sequences (too generic)
      - Single-tool repetition (e.g., Read, Read, Read)
      - Sequences shorter than 3 steps
      - Sequences that match an existing skill's workflow

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

## RULES

- Never delete historical entries without evidence they're wrong
- Date-stamp all new entries
- Cross-reference with existing patterns before adding
- In `test-run` mode, only show what would change — don't write
- MUST NOT inject constraints into skills without explicit user approval (Step 5.5.3)
- MUST NOT inject constraints from learnings with `reuse_count < 2` — one-off errors are not patterns
- MUST record injection metadata in the learning entry to prevent re-proposing (Step 5.5.4)
