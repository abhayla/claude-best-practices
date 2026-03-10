---
name: clean-pyc
description: >
  Remove .pyc files and __pycache__ directories from backend/.
  Use when backend tests show stale import errors, module-not-found after renames,
  or "ModuleNotFoundError" despite code existing. Also useful before commits to
  ensure no cached bytecode interferes.
allowed-tools: "Bash"
disable-model-invocation: true
---

# Clean Python Bytecode Cache

Remove all `.pyc` files and `__pycache__` directories from the backend to fix stale module issues.

**Request:** $ARGUMENTS

---

## STEP 1: Count Before

```bash
cd backend && echo "=== Before Cleanup ===" && \
find . -name "*.pyc" | wc -l | tr -d ' ' | xargs -I{} echo "  .pyc files: {}" && \
find . -name "__pycache__" -type d | wc -l | tr -d ' ' | xargs -I{} echo "  __pycache__ dirs: {}"
```

---

## STEP 2: Delete

```bash
cd backend && \
find . -name "*.pyc" -delete && \
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; \
echo "Cleanup complete."
```

---

## STEP 3: Report

```bash
cd backend && echo "=== After Cleanup ===" && \
find . -name "*.pyc" | wc -l | tr -d ' ' | xargs -I{} echo "  .pyc files remaining: {}" && \
find . -name "__pycache__" -type d | wc -l | tr -d ' ' | xargs -I{} echo "  __pycache__ dirs remaining: {}"
```

**Output Format:**
```
=== Before Cleanup ===
  .pyc files: N
  __pycache__ dirs: N
Cleanup complete.
=== After Cleanup ===
  .pyc files remaining: 0
  __pycache__ dirs remaining: 0
```
