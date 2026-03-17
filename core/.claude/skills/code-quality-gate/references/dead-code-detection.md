# Dead Code Detection — Reference

Extracted from `/code-quality-gate` Step 10 for size management.
This file is loaded on-demand when Step 10 executes.

## STEP 10: Dead Code Detection

Detect unused code in changed files to surface maintenance risks. Dead code findings are informational (non-blocking).

### 10.1 Detect Language and Tool

| Stack | Tool | Install Command |
|-------|------|-----------------|
| Python | vulture | `pip install vulture` |
| JavaScript/TS | ts-prune | `npm install -g ts-prune` |

Check if the tool is available before running. If not installed, install it:

```bash
# Python
command -v vulture >/dev/null 2>&1 || pip install vulture

# JavaScript/TypeScript
command -v ts-prune >/dev/null 2>&1 || npm install -g ts-prune
```

### 10.2 Run on Changed Files Only

Scope dead code detection to files changed in the current branch — do not scan the entire codebase:

**Python (vulture):**
```bash
# Get changed Python files
CHANGED_PY=$(git diff --name-only origin/main...HEAD -- '*.py' | grep -v test | grep -v __pycache__)

# Run vulture with 80% minimum confidence to reduce false positives
if [ -n "$CHANGED_PY" ]; then
  vulture $CHANGED_PY --min-confidence 80
fi
```

**JavaScript/TypeScript (ts-prune):**
```bash
# Get changed JS/TS files
CHANGED_TS=$(git diff --name-only origin/main...HEAD -- '*.ts' '*.tsx' '*.js' '*.jsx' | grep -v test | grep -v spec | grep -v node_modules)

# Run ts-prune and filter output to changed files only
if [ -n "$CHANGED_TS" ]; then
  ts-prune --project tsconfig.json 2>/dev/null | while read line; do
    for f in $CHANGED_TS; do
      echo "$line" | grep -q "$f" && echo "$line"
    done
  done
fi
```

### 10.3 Classify Findings

Report unused exports, functions, variables, and classes found in changed files:

```markdown
## Dead Code Report

**Tool:** vulture / ts-prune
**Files scanned:** <count>
**Dead code items found:** <count>

| File | Line | Type | Name | Confidence |
|------|------|------|------|------------|
| src/services/<module>.py | 34 | function | `old_calculate()` | 90% |
| src/domain/<module>.py | 78 | variable | `LEGACY_FLAG` | 85% |
| src/utils/<module>.ts | 12 | export | `deprecatedHelper` | — |
```

### 10.4 Gate Behavior

Dead code detection is **WARN only** — it does not block the gate. Dead code is informational and may include false positives (e.g., dynamically referenced symbols, plugin entry points).

| Dead Code Items | Status | Action |
|----------------|--------|--------|
| 0 | ✅ Pass | No dead code detected |
| 1+ | ⚠️ Warn | Review flagged items — remove if genuinely unused |

Include the dead code count in the structured output (Step 12).
