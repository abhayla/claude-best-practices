# Learning Modes — Detailed Instructions

Detailed step-by-step instructions for each reflect mode. Referenced from the main `reflect` SKILL.md.

---

## STEP 1: GATHER

Read the following data sources (adjust scope by mode):

### All Modes
1. **Learning captures** — Read all JSON files from `.claude/logs/learning/` (most recent 7 days):
   ```bash
   find .claude/logs/learning/ -name "capture-*.json" -newer .claude/logs/learning/ -mtime -7 2>/dev/null | sort -r | head -50
   ```
   Parse each capture for: skillName, outcome, issuesFound, issuesResolved, fixesApplied, unresolvedItems.

2. **Memory topic files** — Read all 4 topic files:
   - `memory/testing-lessons.md`
   - `memory/fix-patterns.md`
   - `memory/skill-gaps.md`
   - `memory/meta-reflections.md`

3. **Workflow session log** — Read last 200 lines of `.claude/logs/workflow-sessions.log`

4. **Modification history** — Read `.claude/logs/learning/modifications.json`

### Test Map Staleness Check
If `.claude/test-map.json` exists and is >7 days old:
  Log warning: "Test map is stale (>7 days). Consider regenerating: `python .claude/scripts/generate_test_map.py`"
  Offer regeneration as a proposed modification.

### Deep & Test-Run Modes (additional)
5. **Skill definitions** — Read all `.claude/skills/*/SKILL.md` files
6. **Hook definitions** — Read all `.claude/hooks/*.sh` files
7. **Recursion state** — Read `.claude/logs/learning/recursion-state.json`

---

## STEP 2: ANALYZE

Produce a structured analysis table:

### Per-Skill Success Rates
```
| Skill | Invocations | Resolved | Partial | Unresolved | Success Rate |
|-------|-------------|----------|---------|------------|--------------|
| adb-test | 5 | 3 | 1 | 1 | 60% |
| fix-loop | 12 | 9 | 2 | 1 | 75% |
| ...
```

### Recurring Root Causes
Identify root causes that appear 2+ times across captures:
```
| Root Cause | Occurrences | Skills Affected | Last Seen |
|------------|-------------|-----------------|-----------|
| HTTP 500 recipe not found | 3 | adb-test, fix-loop | 2026-02-13 |
| ...
```

### Fix Pattern Frequency
Which fix patterns are applied most often:
```
| Pattern | Count | Example File | Success After Fix |
|---------|-------|-------------|-------------------|
| Missing null check | 4 | RecipeRepository.kt | 100% |
| ...
```

### Persistent Gaps
Issues in `skill-gaps.md` that remain open across 2+ sessions:
```
| Gap | Sessions Open | Skill | Severity |
|-----|---------------|-------|----------|
| No auto-file for UNRESOLVED | 3 | adb-test | High |
| ...
```

### Hook Effectiveness Audit

Cross-reference `workflow-sessions.log` to detect enforcement gaps:

1. Find all `STEP_4_COMPLETE` events where `tests=failed` and `testFailuresPending=true`
2. For each, check if `SKILL_INVOKED name=fix-loop` followed within the same session
3. If failures exist without fix-loop invocation -> flag as **ENFORCEMENT_GAP**

```bash
python -c "
import re
with open('.claude/logs/workflow-sessions.log') as f:
    lines = f.readlines()
sessions = {}
current_session = None
for line in lines:
    if 'SESSION_START' in line:
        m = re.search(r'id=(\S+)', line)
        current_session = m.group(1) if m else 'unknown'
        sessions[current_session] = {'failures': [], 'fixloops': []}
    if current_session and 'tests=failed' in line:
        sessions[current_session]['failures'].append(line.strip())
    if current_session and 'SKILL_INVOKED' in line and 'fix-loop' in line:
        sessions[current_session]['fixloops'].append(line.strip())
print('| Session | Test Failures | Fix-Loop Followed? | Gap? |')
print('|---------|---------------|-------------------|------|')
for sid, data in sessions.items():
    if data['failures']:
        has_fixloop = 'YES' if data['fixloops'] else 'NO'
        gap = 'ENFORCEMENT_GAP' if not data['fixloops'] else '-'
        print(f'| {sid[:20]} | {len(data[\"failures\"])} | {has_fixloop} | {gap} |')
"
```

**Per-mode behavior:**
- **session**: Log warning + add to `skill-gaps.md` if gaps found
- **deep**: Propose hook modifications to close the gap
- **meta**: Track as meta-pattern (system failing to enforce its own rules)

### Knowledge DB Analysis (if .claude/knowledge.db exists)
```bash
python .claude/scripts/knowledge_db.py top-errors --limit 10
```
Add table to analysis output:
```
| Error Pattern | Occurrences | Best Strategy | Success Rate |
|---|---|---|---|
| IntegrityError: duplicate key | 5 | add_upsert | 0.72 |
| ...
```
Cross-reference with `fix-patterns.md` to identify patterns tracked in memory but not in KB (and vice versa).

### Duration Trends
Average skill execution time trending up or down.

---

## STEP 3: UPDATE MEMORY

Based on the analysis, update memory topic files:

1. **testing-lessons.md** — Append new patterns discovered (e.g., "HTTP 500 on recipe detail is a backend data issue, not Android")
2. **fix-patterns.md** — Add newly confirmed fix patterns with success rate
3. **skill-gaps.md** — Update gap statuses (mark resolved gaps, add new ones)
4. **meta-reflections.md** — (meta mode only) Append meta-insight

**MEMORY.md** — Only touch for critical cross-session insights that should be in the system prompt. Keep under 200 lines. Check current line count before editing.

Use the `append_memory_topic()` pattern: timestamped entries, 500-line limit per topic file.

---

## STEP 4: PROPOSE MODIFICATIONS (deep & test-run modes only)

For each identified gap or recurring failure, propose a specific modification:

```
| # | Target File | Reason | Change Description | Lines | Risk |
|---|-------------|--------|--------------------|-------|------|
| 1 | .claude/skills/adb-test/SKILL.md | Missing auto-file for UNRESOLVED | Add F5.5 section for gh issue create | +25 | Low |
| 2 | .claude/hooks/post-test-update.sh | Test result not captured for backend | Add pytest output parsing | +10 | Low |
| ...
```

**Prioritization:** Impact (high -> low) then Risk (low -> high).

**test-run mode:** Output the table and STOP. Do not apply modifications.

---

## STEP 5: APPLY MODIFICATIONS (deep mode only)

### Safety Protocol (MANDATORY)

Before applying ANY modification:

1. **Git stash** — Save current uncommitted changes:
   ```bash
   STASH_REF=$(git stash push -m "reflect-deep-$(date +%Y%m%d%H%M%S)" 2>&1)
   ```
   Record `stashRef` in recursion-state.json.

2. **Deny list check** — NEVER modify these files:
   - `CLAUDE.md` (protected section or any part)
   - `backend/tests/conftest.py`
   - `android/build.gradle.kts` or `android/app/build.gradle.kts`
   - `.claude/settings.json` (hook registration is separate from skill content)
   - Any `*.env` file
   - Any file in `backend/alembic/versions/`

   If a proposed modification targets a deny-listed file -> SKIP it.

3. **Uncommitted changes check** — For each target file:
   ```bash
   git diff --name-only | grep -q "{file}"
   ```
   If the file has uncommitted changes -> SKIP it to avoid conflict.

4. **Limits:**
   - Maximum 5 files per session
   - Maximum 50 lines changed per file
   - If a modification exceeds these limits -> SKIP it, log reason

### Apply Each Modification

For each approved modification (up to 5):
1. Read the target file
2. Apply the edit using Edit tool
3. Validate:
   - `.sh` files: `bash -n {file}` — must exit 0
   - `.md` files: check heading structure preserved, file size < 50KB
   - `.json` files: `python -c "import json; json.load(open('{file}'))"` — must succeed
4. If validation fails -> `git checkout -- {file}` and skip

### Record Modifications

Append to `.claude/logs/learning/modifications.json`:
```json
{
  "sessionId": "reflect-{timestamp}",
  "timestamp": "ISO8601",
  "file": "{path}",
  "reason": "{gap description}",
  "linesAdded": N,
  "linesRemoved": N,
  "validated": true,
  "result": "APPLIED|REVERTED|SKIPPED"
}
```

---

## STEP 6: RECURSE (deep mode, if modifications applied)

### Recursion Protocol

1. **Read recursion state:**
   ```bash
   cat .claude/logs/learning/recursion-state.json
   ```

2. **Check depth:**
   - If `currentDepth >= maxDepth` (3) -> go to STEP 7 (meta-reflect), do NOT recurse
   - If no modifications were applied -> STOP (converged)

3. **Update recursion state:**
   ```json
   {
     "currentDepth": N+1,
     "sessionId": "reflect-{timestamp}",
     "stashRef": "{from step 5}",
     "chain": [ ...previous, { "depth": N, "action": "reflect", "mode": "deep", "modifications_applied": M, "result": "MODIFICATIONS_APPLIED" } ]
   }
   ```

4. **Re-run the most affected skill** — Identify which skill had the worst success rate. Invoke it via Skill tool:
   ```
   Skill("{skill_name}", args="{minimal args to trigger a representative test}")
   ```
   This generates a new capture via post-skill-learning.sh.

5. **Evaluate re-run results:**
   - Read the new capture JSON
   - Compare outcome to the pre-modification baseline
   - Classify: **IMPROVED** (better success rate), **NEUTRAL** (same), **DEGRADED** (worse)

6. **Decision:**
   - **IMPROVED or NEUTRAL:** Keep modifications. Invoke `/reflect session --depth {N+1}` to capture the result.
   - **DEGRADED:** Auto-revert ALL modifications from this session:
     ```bash
     git checkout -- {file1} {file2} ...
     ```
     Log revert in modifications.json. Reset recursion depth.

### Termination Conditions
- `currentDepth >= maxDepth` -> go to meta-reflect
- No modifications proposed -> converged, stop
- Re-run shows no change -> converged, stop
- Re-run shows DEGRADED -> revert + stop
- Total elapsed time > 10 minutes -> stop
- Consecutive NEUTRAL results >= 2 -> converged, stop

---

## STEP 7: META-REFLECT (meta mode, or depth=3 in deep mode)

### Meta-Analysis

1. **Read meta-reflections.md** history
2. **Read modifications.json** — all historical modifications

3. **Analyze:**
   - **Improvement rate:** What % of modifications led to IMPROVED outcomes?
   - **Best modification types:** Which categories of changes (skill updates, hook fixes, memory additions) have highest success?
   - **Convergence:** Is the system improving over time, or oscillating?
   - **Diminishing returns:** Are recent modifications having less impact than earlier ones?

4. **Output meta-insight:**
   ```
   ### Meta-Reflection: {session_id}

   **Improvement rate:** X% of modifications improved outcomes
   **Best strategies:** {list top 3 modification types by effectiveness}
   **Convergence:** IMPROVING | PLATEAUED | OSCILLATING
   **Recommendation:** {next action — e.g., "Focus on backend error handling patterns" or "System is converged, no deep reflect needed"}
   ```

5. **Append to meta-reflections.md** via `append_memory_topic()`

6. **Reset recursion state:**
   ```json
   { "currentDepth": 0, "maxDepth": 3, "sessionId": null, "stashRef": null, "chain": [] }
   ```
