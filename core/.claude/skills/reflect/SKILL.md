---
name: reflect
description: >
  Learning system analysis and self-modification. Analyzes session outcomes, updates
  memory topics (testing-lessons, fix-patterns, skill-gaps, meta-reflections), maintains
  failure index. Four modes: session (recent work), deep (modify skills/hooks), meta
  (learning effectiveness), test-run (dry run). Use after completing work or when
  learning system needs updates.
disable-model-invocation: true
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[session|deep|meta|test-run]"
---

# Reflect — Learning System Analysis & Self-Modification

Analyze skill outcomes, update memory, and optionally self-modify skills/hooks to close gaps.

**Arguments:** $ARGUMENTS

---

## MODE SELECTION

| Mode | Trigger | Modifies files? | Time |
|------|---------|-----------------|------|
| `session` (default) | Auto-invoked after skills, or `/reflect` with no args | Memory topic files only | <60s |
| `deep` | `/reflect deep` | Memory + Skills + Hooks | <120s |
| `meta` | `/reflect meta` | Memory only | <60s |
| `test-run` | `/reflect test-run` | No (dry-run analysis) | <90s |

Parse `$ARGUMENTS`:
- Empty or `session` -> session mode
- Contains `deep` -> deep mode
- Contains `meta` -> meta mode
- Contains `test-run` -> test-run mode
- `--depth N` -> set recursion depth (used internally by auto-invocation)

### Auto-Escalation to Deep Mode

After parsing arguments, check failure-index.json for recurring unresolved failures:

```bash
python -c "
import json
try:
    with open('.claude/logs/learning/failure-index.json') as f:
        d = json.load(f)
    for e in d.get('entries', []):
        # Count consecutive UNRESOLVED occurrences (most recent first)
        consecutive = 0
        for occ in reversed(e.get('occurrences', [])):
            if occ.get('outcome') in ('UNRESOLVED', 'PARTIALLY_RESOLVED', 'FAILED'):
                consecutive += 1
            else:
                break
        if consecutive >= 3:
            print(f'AUTO-DEEP: {e[\"skill\"]}/{e[\"issue_type\"]} has {consecutive} consecutive unresolved')
except FileNotFoundError:
    pass
"
```

**If any entry has 3+ consecutive unresolved occurrences:**
- Override mode to `deep` regardless of user arguments
- Set `target_skill` and `target_issue_type` for focused analysis in Steps 4-5
- Log: `"Auto-escalating to deep mode for {skill}/{issue_type} ({N} consecutive unresolved)"`

---

## SELF-SKIP RULE

This skill MUST NOT invoke itself. The `post-skill-learning.sh` hook already skips capturing `/reflect` invocations. If during recursion (deep mode) a re-run triggers `/reflect`, it must detect and break the cycle.

---

## STEP 0: PRE-EXECUTION KNOWLEDGE CHECK

Before any skill execution, check the failure index for known issues:

1. **Search failure-index.json** for matching `(skill, issue_type)`:
   ```bash
   python -c "
   import json
   try:
       with open('.claude/logs/learning/failure-index.json') as f:
           d = json.load(f)
       for e in d.get('entries', []):
           if e.get('known_workaround'):
               print(f\"KNOWN: {e['skill']}/{e['issue_type']} -> {e['known_workaround']}\")
           if e.get('threshold_reached'):
               print(f\"THRESHOLD: {e['skill']}/{e['issue_type']} ({len(e['occurrences'])} occurrences)\")
   except FileNotFoundError:
       print('No failure index found')
   "
   ```

2. **If known limitation found** -> apply documented workaround immediately
3. **If previous stall found** -> start with the strategy that eventually worked
4. **Log:** `"Pre-execution check: found/not-found, applying: {strategy}"`

---

## STEP 0.5: PRE-FLIGHT AUTO-FIX SCAN (all modes)

Before gathering data, scan fix-patterns.md for unfixed auto-fix eligible patterns:

```bash
python -c "
import re, os

import glob; fp = next(iter(glob.glob(os.path.expanduser('~/.claude/projects/*VibeCoding-KKB/memory/fix-patterns.md'))), '')
if not os.path.exists(fp):
    print('Step 0.5: No fix-patterns.md found')
    exit(0)
with open(fp) as f:
    content = f.read()
sections = re.split(r'(?=^### )', content, flags=re.MULTILINE)
unfixed = []
for s in sections:
    if 'Auto-fix eligible: Yes' not in s:
        continue
    title_m = re.match(r'### (.+)', s)
    if not title_m:
        continue
    title = title_m.group(1).strip()
    if title.endswith('FIXED'):
        continue
    files_m = re.search(r'\*\*Files?:\*\*\s*(.+)', s)
    files = files_m.group(1).strip() if files_m else 'unknown'
    unfixed.append((title, files))
if unfixed:
    for t, f in unfixed:
        print(f'UNFIXED: {t} -> {f}')
    print(f'Step 0.5: {len(unfixed)} unfixed auto-fix pattern(s) found')
else:
    print('Step 0.5: All auto-fix eligible patterns are resolved')
"
```

**Per-mode behavior:**
- **session mode:** Log warning — `"Unfixed auto-fix pattern: {name}"`
- **deep mode:** Auto-invoke `/fix-loop` for each unfixed pattern with files from the entry
- **meta / test-run mode:** Include in analysis tables as unresolved infrastructure gaps

Output: `"Step 0.5: {N} unfixed auto-fix patterns found, {M} auto-fixed"`

---

For detailed mode-specific instructions (Steps 1-7), see `references/learning-modes.md`.

---

## OUTPUT FORMAT

### Session Mode
```
## Reflect: Session Analysis

### Captures Analyzed: N (from {date_range})
### Skill Success Rates
{table from Step 2}

### New Insights
- {insight 1}
- {insight 2}

### Memory Updates
- testing-lessons.md: +{N} entries
- fix-patterns.md: +{N} entries
- skill-gaps.md: {N} gaps updated

### Duration: {seconds}s
```

### Deep Mode
```
## Reflect: Deep Analysis & Modification

### Analysis
{tables from Step 2}

### Modifications Applied
| # | File | Change | Lines | Validated | Result |
|---|------|--------|-------|-----------|--------|
{table}

### Recursion
- Depth: {N}/{maxDepth}
- Re-run skill: {name}
- Re-run result: IMPROVED | NEUTRAL | DEGRADED
- Action: KEPT | REVERTED

### Memory Updates
{same as session}

### Duration: {seconds}s
```

### Meta Mode
```
## Reflect: Meta-Analysis

### Historical Modifications: {N total}
### Improvement Rate: {X}%
### Best Strategies
1. {strategy}: {success_rate}%
2. ...

### Convergence: IMPROVING | PLATEAUED | OSCILLATING
### Recommendation: {action}

### Duration: {seconds}s
```

### Test-Run Mode
```
## Reflect: Test-Run (Dry Run)

### Analysis
{tables from Step 2}

### Proposed Modifications (NOT applied)
{table from Step 4}

### Would affect: {N} files, ~{N} lines

### Duration: {seconds}s
```

---

## QUICK REFERENCE

| Mode | Reads | Writes Memory | Modifies Skills/Hooks | Recurses |
|------|-------|---------------|----------------------|----------|
| session | captures, topics, log | Yes | No | No |
| deep | + skill/hook defs | Yes | Yes (with safety) | Yes (max 3) |
| meta | topics, modifications | Yes (meta only) | No | No |
| test-run | + skill/hook defs | No | No (dry-run) | No |

| Safety Guard | Description |
|-------------|-------------|
| Git stash | Before any modification |
| Deny list | CLAUDE.md, conftest.py, build files, .env |
| Uncommitted check | Skip files with local changes |
| Validation | bash -n for .sh, JSON parse for .json, size for .md |
| Limits | 5 files/session, 50 lines/file |
| Auto-revert | If re-run shows DEGRADED results |
| Depth limit | Max 3 recursive levels |
| Time limit | 10 minutes total |
