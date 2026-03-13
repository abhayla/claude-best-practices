---
name: architecture-fitness
description: >
  Automated architecture conformance checks: dependency direction validation,
  circular dependency detection, coupling/cohesion metrics, layer violation
  scanning, and architecture decision review. Use as a review gate.
triggers:
  - architecture check
  - fitness functions
  - dependency check
  - circular dependency
  - coupling metrics
  - architecture conformance
  - layer violations
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<directory to analyze, or 'all changed files'>"
---

# Architecture Fitness — Automated Conformance Checks

Run automated architecture fitness functions to verify structural integrity. Use as part of the review gate before merge.

**Scope:** $ARGUMENTS

---

## STEP 1: Detect Architecture Style

Identify the project's architecture by scanning the folder structure:

| Pattern | Architecture | Indicator |
|---------|-------------|-----------|
| `domain/`, `application/`, `infrastructure/` | Clean Architecture | Layer separation |
| `features/<name>/model/view/intent/` | MVI (Android) | Feature modules |
| `cmd/`, `internal/`, `pkg/` | Go Standard Layout | Go idioms |
| `app/`, `lib/`, `config/` | Rails-style | Convention over config |
| `src/modules/<name>/` | Modular Monolith | Module boundaries |
| Flat `src/` | No clear architecture | Flag for review |

Report the detected architecture and its expected dependency rules before proceeding.

---

## STEP 2: Dependency Direction Validation

### 2.1 Define Allowed Dependencies

Based on the detected architecture, define the dependency matrix:

**Clean Architecture:**
```
presentation → application → domain     ✅ ALLOWED
infrastructure → domain                 ✅ ALLOWED (implements interfaces)
infrastructure → application            ✅ ALLOWED (implements ports)

domain → application                    ❌ FORBIDDEN
domain → infrastructure                 ❌ FORBIDDEN
domain → presentation                   ❌ FORBIDDEN
application → infrastructure            ❌ FORBIDDEN (use ports)
application → presentation              ❌ FORBIDDEN
infrastructure → presentation           ❌ FORBIDDEN
```

**MVI / Feature Modules:**
```
feature_a → shared/common               ✅ ALLOWED
shared/common → feature_a               ❌ FORBIDDEN
feature_a → feature_b                   ❌ FORBIDDEN (no cross-feature deps)
```

### 2.2 Automated Scanning

**Python:**
```bash
# Check for forbidden imports
grep -rn "from.*infrastructure" src/domain/ src/application/ 2>/dev/null
grep -rn "from.*presentation" src/domain/ src/application/ src/infrastructure/ 2>/dev/null
grep -rn "import.*infrastructure" src/domain/ src/application/ 2>/dev/null
```

**TypeScript:**
```bash
# Check for forbidden imports
grep -rn "from.*infrastructure" src/domain/ src/application/ --include="*.ts" 2>/dev/null
grep -rn "from.*presentation" src/domain/ src/application/ --include="*.ts" 2>/dev/null
```

**Kotlin (Android):**
```bash
# Check for forbidden imports (cross-feature)
grep -rn "import.*feature_" app/src/main/java/**/domain/ --include="*.kt" 2>/dev/null
```

### 2.3 Report Violations

```markdown
## Dependency Direction Violations

| File | Line | Import | Violation |
|------|------|--------|-----------|
| src/domain/user.py | 5 | from src.infrastructure.db import Session | domain → infrastructure |
| src/application/auth.py | 12 | from src.infrastructure.smtp import send | application → infrastructure |

**Total:** 2 violations found
**Action:** Must fix before merge — define ports/interfaces in domain layer
```

---

## STEP 3: Circular Dependency Detection

### 3.1 Tools

| Language | Tool | Command |
|----------|------|---------|
| Python | pydeps / importlab | `pydeps src/ --no-output --reverse --cluster` |
| Python | manual | `python -c "import importlib; ..."` |
| TypeScript | madge | `npx madge --circular src/` |
| Go | built-in | `go vet ./...` (detects import cycles) |
| Kotlin | detekt | CircularDependency rule |

### 3.2 Manual Detection

If tools are unavailable, scan import chains:

```bash
# Python: Find all imports in each module, trace cycles
# Build import graph
for f in $(find src/ -name "*.py"); do
  echo "=== $f ==="
  grep "^from\|^import" "$f" | grep "src\." || true
done
```

Look for chains: `A imports B`, `B imports C`, `C imports A` → cycle.

### 3.3 Report

```markdown
## Circular Dependencies

| Cycle | Files Involved |
|-------|---------------|
| ❌ Cycle 1 | user_service.py → auth_service.py → user_service.py |

**Fix:** Extract shared logic to a new module both can depend on, or use dependency injection.
```

---

## STEP 4: Coupling & Cohesion Metrics

### 4.1 Afferent Coupling (Ca) — Who depends on me?

Count how many other modules import each module:

```bash
# Python: Count imports of each module
for module in $(find src/ -name "*.py" -not -name "__init__.py"); do
  module_name=$(echo $module | sed 's|/|.|g' | sed 's|.py||')
  count=$(grep -rl "$module_name" src/ --include="*.py" | wc -l)
  echo "$count $module"
done | sort -rn | head -20
```

### 4.2 Efferent Coupling (Ce) — What do I depend on?

Count how many imports each module has:

```bash
# Python: Count imports per file
for f in $(find src/ -name "*.py"); do
  count=$(grep -c "^from\|^import" "$f" 2>/dev/null || echo 0)
  echo "$count $f"
done | sort -rn | head -20
```

### 4.3 Instability Metric

```
Instability = Ce / (Ca + Ce)
```

| Instability | Meaning | Ideal For |
|-------------|---------|-----------|
| 0.0 | Maximally stable (many depend on it, it depends on nothing) | Domain layer, shared libs |
| 1.0 | Maximally unstable (depends on many, nothing depends on it) | Presentation, adapters |
| 0.5 | Balanced | Application layer |

**Rule:** Dependencies should flow toward stability (unstable → stable).

### 4.4 Report

```markdown
## Coupling Analysis

| Module | Ca (in) | Ce (out) | Instability | Expected | Status |
|--------|---------|----------|-------------|----------|--------|
| src/domain/user.py | 8 | 1 | 0.11 | ≤0.3 | ✅ Stable |
| src/application/auth.py | 3 | 5 | 0.63 | 0.3-0.7 | ✅ Balanced |
| src/presentation/routes.py | 0 | 7 | 1.0 | ≥0.7 | ✅ Unstable (expected) |
| src/domain/utils.py | 12 | 4 | 0.25 | ≤0.3 | ⚠️ High Ca — change risk |
```

---

## STEP 5: Module Size & Boundary Analysis

### 5.1 Module Size

Flag modules that are too large (potential God modules):

| Metric | Threshold | Tool |
|--------|-----------|------|
| Lines per file | ≤300 | `wc -l` |
| Functions per file | ≤15 | `grep -c "def \|function "` |
| Classes per file | ≤3 | `grep -c "class "` |
| Files per module | ≤20 | `find <module>/ -name "*.py" \| wc -l` |

### 5.2 Public API Surface

For each module, check that the public interface is minimal:

```bash
# Python: Check __init__.py exports
cat src/domain/__init__.py  # Should export only public types
```

| Module | Exported Symbols | Status |
|--------|-----------------|--------|
| domain | 5 (User, Order, ...) | ✅ Minimal |
| infrastructure | 12 (repos, adapters, ...) | ⚠️ Consider splitting |

---

## STEP 6: ADR Review

If ADRs exist, verify they are still valid:

```bash
# Find all ADRs
find docs/adr/ -name "ADR-*.md" 2>/dev/null
```

For each ADR, check:
- [ ] Status is current (not superseded without replacement)
- [ ] Decision is still reflected in the code
- [ ] Context hasn't changed (new constraints, new requirements)
- [ ] Consequences identified in ADR are observable in implementation

```markdown
## ADR Review

| ADR | Title | Status | Still Valid? |
|-----|-------|--------|-------------|
| ADR-001 | Use UUID for primary keys | Accepted | ✅ All tables use UUID |
| ADR-002 | Use Redis for caching | Accepted | ⚠️ Some endpoints bypass cache |
| ADR-003 | Monorepo structure | Proposed | ❌ Superseded — now multi-repo |
```

---

## STEP 7: Fitness Report

Present the comprehensive fitness report:

```markdown
## Architecture Fitness Report

**Date:** <date>
**Architecture:** Clean Architecture (detected)
**Scope:** <N> files analyzed

### Summary

| Check | Status | Details |
|-------|--------|---------|
| Dependency direction | ✅ Pass | 0 violations |
| Circular dependencies | ✅ Pass | 0 cycles |
| Coupling metrics | ⚠️ 1 issue | `utils.py` has Ca=12 (high change risk) |
| Module size | ✅ Pass | All modules ≤300 lines |
| ADR conformance | ⚠️ 1 issue | ADR-003 superseded, needs update |

### Gate Decision
- **PASS** — Architecture constraints maintained
- **WARN** — Minor issues flagged for review (non-blocking)
- **BLOCK** — Dependency violations or cycles detected (must fix)

### Recommendations
1. Split `src/domain/utils.py` (Ca=12) — too many dependents
2. Update ADR-003 status to "Superseded by ADR-005"
```

---

## MUST DO

- Always detect the architecture style before applying rules
- Always check dependency direction against the architecture's constraints
- Always scan for circular dependencies
- Always compute coupling metrics for changed modules
- Always review ADR validity if ADRs exist
- Always produce a structured fitness report (Step 7)

## MUST NOT DO

- MUST NOT apply Clean Architecture rules to projects with a different architecture style
- MUST NOT flag test files for architecture violations (tests can import from any layer)
- MUST NOT block on coupling metrics alone — they are directional indicators, not hard rules
- MUST NOT duplicate layer validation from `code-quality-gate` Step 5 — this skill provides deeper analysis (coupling, ADR review, boundary analysis)
- MUST NOT report generated code or third-party libraries as violations
