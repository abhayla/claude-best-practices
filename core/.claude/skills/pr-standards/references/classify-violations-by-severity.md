# STEP 5: Classify Violations by Severity

### 5.1 Severity Definitions

| Severity | Icon | Action Required | Blocks PR | Examples |
|----------|------|----------------|-----------|----------|
| **Critical** | `[C]` | MUST fix before merge | Yes | Security vulnerability, debugger statement, hardcoded secret, broken API contract, disabled security check |
| **Warning** | `[W]` | Should fix, flag to author | Only in `--strict` mode | Missing error handling, no test for new function, TODO without ticket, debug print statement |
| **Info** | `[I]` | Optional improvement | No | Naming suggestion, missing docstring, magic number, deep relative import |

### 5.2 PR Verdict Logic

```
IF critical_count > 0:
  verdict = "FAIL"
  message = "PR has {critical_count} critical violation(s) that must be fixed."
ELIF strict_mode AND warning_count > 0:
  verdict = "FAIL"
  message = "Strict mode: PR has {warning_count} warning(s) that must be fixed."
ELIF warning_count > 10:
  verdict = "WARN"
  message = "PR has many warnings ({warning_count}). Consider addressing before review."
ELSE:
  verdict = "PASS"
  message = "PR meets team standards."
```

### 5.3 Violation Summary

```
VIOLATION SUMMARY
=================

Critical: {count} — MUST fix before merge
Warning:  {count} — Should fix before review
Info:     {count} — Optional improvements

Auto-fixable: {count} of {total} violations
```

---

