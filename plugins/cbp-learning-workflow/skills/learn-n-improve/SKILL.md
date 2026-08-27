---
name: learn-n-improve
description: >
  Analyze session outcomes and update memory topics (testing-lessons, fix-patterns,
  success-patterns, skill-gaps) for continuous self-improvement. Captures both failure
  lessons (error→fix→lesson) and success patterns (what worked + when to reuse it). Four
  modes: session, deep, meta, test-run. Use when a session ends, after a fix succeeds,
  after a verified success worth repeating, or when reviewing learning effectiveness.
  For full learning cycles (capture + pattern detection + skill proposals), use
  /learning-self-improvement instead. For one-off session saves, use /end-session.
  For full handover docs, use /handover.
type: workflow
triggers:
  - learn from session
  - capture learnings
  - record what we learned
  - session reflection
  - what did we learn
  - improve from mistakes
  - capture what worked
  - record a success pattern
  - learn-n-improve
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode: session|deep|meta|test-run>"
version: "2.5.0"
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

Read `.claude/learnings.json` if it exists; if absent (fresh install / first run), CREATE it as `{"learnings": [], "success_patterns": []}` before proceeding. Read any scratchpad or session files from `.claude/sessions/`.

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
| test-results `PASSED` after prior `FAILED` | **Fix Success** | Record the fix pattern (STEP 3) |
| test-results `PASSED` with no prior failure, on a genuinely new/verified capability | **Success Pattern** | Record what worked + when to reuse it (STEP 3.5) |
| A verified approach/tool/sequence that clearly outperformed the alternative (e.g. an authoritative preflight probe, a reusable checkpoint strategy) | **Success Pattern** | Record what worked + when to reuse it (STEP 3.5) |
| Fix-loop iterations > 1 | **Workaround** | Check if the fix was minimal or structural |
| New files created with no test coverage | **Knowledge gap** | Flag for test creation |
| Repeated Grep/Read on same area | **Knowledge gap** | Record as area needing documentation |

**Capture triggers (not only "after a fix succeeds"):** run this analysis after ANY verified
success worth repeating — not just after fixing a failure. Concretely: a pilot/loop run that
shipped clean (zero heals), a tool/technique that proved reliable enough to become the default
next time, or a verified outcome the session would want to repeat as-is. See the `session` mode
row in the Modes table above — "after completing work" includes a clean, fix-free success, not
only a post-fix capture.

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

## STEP 3.5: Build Success-Pattern Database (memory of wins)

Failures aren't the only thing worth remembering — a win that isn't captured evaporates just
as fast, and gets rediscovered (or missed) next time instead of reused. This step mirrors
STEP 3's error→fix→lesson triple with a success-pattern equivalent: **what was attempted →
what worked → why it worked → when to apply it again**.

For each success signal identified in STEP 2 (a verified, genuinely successful outcome — a
clean pilot run, a technique that proved reliably better than the alternative, a checkpoint
strategy that avoided rework), record a structured entry in the SAME `.claude/learnings.json`
file, under a `success_patterns` array (one canonical home per `learnings-routing.md` — success
patterns are learnings too, not a parallel system):

```json
{
  "success_patterns": [
    {
      "id": "S001",
      "date": "2026-07-03",
      "type": "GENERIC",
      "attempted": "Verifying an agent is dispatchable before relying on it mid-pipeline",
      "worked": "Listed the live agent registry (`.claude/agents/*.md` scan) as the preflight probe, instead of assuming a named agent exists because its file is on disk",
      "mechanism": "Claude Code loads the agent registry at session start, not per-call — a file existing on disk does not guarantee it's dispatchable this session (see pattern-structure.md 'Agent registry session-pinning'). An explicit registry-listing probe catches the gap file-existence checks miss.",
      "reuse_trigger": "Before any pipeline dispatches a named worker agent it did not just create/sync itself in-session — probe the live registry first, not just the filesystem",
      "evidence": "noter-app loop pilot: 1 cycle, 0 heals, agent dispatch never failed after adopting the registry-listing preflight",
      "tags": ["agent-dispatch", "preflight", "loop-engineering"],
      "reuse_count": 0,
      "hub_pattern_link": "pattern-structure"
    }
  ]
}
```

### Schema fields

| Field | Meaning |
|---|---|
| `attempted` | What was tried (the situation/approach at hand) |
| `worked` | The concrete technique/sequence/tool that succeeded |
| `mechanism` | WHY it worked — the causal reason, not just the observation (mirrors STEP 3's `fix.description`) |
| `reuse_trigger` | The condition under which to apply this again — a future session must be able to pattern-match on this |
| `evidence` | The verified outcome that proves this was a real success, not a guess (a passing pilot, a metric, a clean run) |
| `type` | `GENERIC` (true regardless of this product — process/tooling/craft) or `PRODUCT-SPECIFIC` (true only for this codebase's domain). Classify per `learnings-routing.md` BEFORE filing — a product-specific win filed as generic pollutes every project that reuses this skill's patterns |

### Typing and routing (do not skip)

1. **Type first.** Decide GENERIC vs PRODUCT-SPECIFIC per `learnings-routing.md` before writing
   the entry. GENERIC success patterns are eligible for the same Hub Pattern Linkage step used
   for failure learnings (suggest a `hub_pattern_link` by tag overlap, same 50% threshold, same
   user-confirms flow as STEP 3's Hub Pattern Linkage). PRODUCT-SPECIFIC success patterns are
   recorded here for this project's own reuse but MUST NOT be proposed as a hub pattern link.
2. **Dedup first.** Search `success_patterns` for a similar `attempted`/`worked` pair (by tags,
   by mechanism) before appending — if one exists, increment its `reuse_count` and refine the
   `reuse_trigger` if this occurrence sharpens it, same discipline as STEP 3.
3. **Reuse count feeds STEP 5.5.** A success pattern with `reuse_count >= 2` is eligible for the
   SAME active-constraint-injection flow as a failure lesson (STEP 5.5) — a proven win can be
   proposed as a positive constraint ("prefer X because...") in the skill it relates to, gated by
   the same explicit-approval requirement.

## STEP 4: Update Memory Topics

Update files in the project's memory directory:

| File | Content |
|------|---------|
| `fix-patterns.md` | Recurring fix patterns with file references |
| `testing-lessons.md` | Testing insights and fixture knowledge |
| `success-patterns.md` | Reusable wins — what worked + when to reuse it (human-readable digest of Step 3.5) |
| `skill-gaps.md` | Areas where skills need improvement |
| `.claude/learnings.json` | Structured error→fix→lesson database (Step 3) + success-pattern database (Step 3.5) |

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
   - A `paths:` field scoping it to relevant file patterns, OR `# Scope: global` if it applies everywhere
   - Actionable content (not placeholder/TODO stubs)

   ```
   Pattern detected: "null-handling" appears in 8 learnings.
   Suggested rule:
   ---
   description: Enforce null-safety checks on ORM query results.
   paths: ["**/*.py", "**/*.ts"]
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

**Trigger**: Only activates when a learning OR a success pattern has `reuse_count >= 2` —
proven recurring, not a one-off. Skip this step entirely if nothing meets the threshold.

### 5.5.1 Map Learnings (and Success Patterns) to Skills

For each learning OR success pattern with `reuse_count >= 2`, identify the target skill:

| Learning Signal | Target Skill | Match Method |
|---|---|---|
| Tags match a skill name | That skill | `tags` contains skill name (e.g., `"fix-loop"`) |
| Error occurred during a skill run | That skill | `context` mentions `/skill-name` invocation |
| Error file matches a skill's `paths:` | That skill | File path matches skill's operational scope |
| No skill match found | Skip | Record as general learning, do not force-fit |

```bash
# Find learnings + success patterns eligible for constraint injection
python3 -c "
import json
data = json.load(open('.claude/learnings.json'))
eligible_failures = [l for l in data.get('learnings', []) if l.get('reuse_count', 0) >= 2]
eligible_successes = [s for s in data.get('success_patterns', []) if s.get('reuse_count', 0) >= 2]
for l in eligible_failures:
    print(f\"  {l['id']}: reuse={l['reuse_count']} tags={l.get('tags', [])} lesson={l['lesson'][:80]}\")
for s in eligible_successes:
    print(f\"  {s['id']}: reuse={s['reuse_count']} tags={s.get('tags', [])} worked={s['worked'][:80]}\")
print(f'Total eligible: {len(eligible_failures) + len(eligible_successes)} ({len(eligible_failures)} failures, {len(eligible_successes)} successes)')
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
  New success patterns: P (what-worked→why→reuse-trigger entries)
  Updated success patterns: Q (reuse_count incremented)
  Topics affected: [list]
  Total learnings in database: X
  Total success patterns in database: Y

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
- MUST NOT inject constraints from learnings OR success patterns with `reuse_count < 2` — Why: one-off occurrences are noise, not patterns; premature injection creates brittle rules
- MUST record injection metadata in the learning/success-pattern entry to prevent re-proposing (Step 5.5.4) — Why: without tracking, the same constraint gets proposed every session
- MUST default to `session` mode when $ARGUMENTS is empty — Why: asking for mode selection adds friction when the common case is always "session"
- MUST capture success patterns in the SAME `.claude/learnings.json` file as failure learnings, under `success_patterns` (Step 3.5) — Why: one canonical home per `learnings-routing.md`; a parallel success-tracking file would duplicate infrastructure and fragment reuse
- MUST type every success pattern GENERIC or PRODUCT-SPECIFIC before filing (Step 3.5) — Why: an untyped or mistyped entry either pollutes hub-pattern suggestions with product-specific noise, or buries a reusable craft lesson in product-only docs (`learnings-routing.md`)
- MUST record a success pattern's `mechanism` (why it worked) and `reuse_trigger` (when to apply it again), not just the observation that it worked — Why: "it worked" without the causal reason and the reuse condition is not reusable knowledge, it's a fact nobody can act on
