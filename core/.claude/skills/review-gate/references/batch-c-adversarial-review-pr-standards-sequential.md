# STEP 3: Batch C — Adversarial Review → PR Standards (Sequential)

### 3.1 Adversarial Review

```
Skill("adversarial-review", args="--mode code")
```

Record result:

```
BATCH C — Adversarial Review:
  Status: {PASSED / PASSED WITH CAVEATS / BLOCKED / UNKNOWN}
  Rounds completed: {1-3}
  Issues found: {total}
    Critical: {count} ({resolved} resolved)
    Major: {count} ({resolved} resolved)
    Minor: {count} ({resolved} resolved)
  Unresolved critical: {count}
  Deferred with tracking: {count}
  Blocking issues: {count}
```

### 3.2 PR Standards

```
Skill("pr-standards", args="")
```

Record result:

```
BATCH C — PR Standards:
  Status: {PASS / FAIL / WARN / UNKNOWN}
  Critical violations: {count}
  Warning violations: {count}
  Info violations: {count}
  Auto-fixable: {count}
```

If the result is FAIL and `--fix` is enabled:

```
Skill("pr-standards", args="--fix")
```

Then re-run to verify:

```
Skill("pr-standards", args="")
```

---

