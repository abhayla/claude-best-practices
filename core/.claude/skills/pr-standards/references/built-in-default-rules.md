# STEP 3: Built-in Default Rules

### 3.1 Debug and Development Artifacts

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `no-console-log` | Warning | `console\.log\(` | Yes: remove line |
| `no-print-debug` | Warning | `^\s*print\(` (in non-test Python files) | Yes: replace with `logger.debug(` |
| `no-debugger` | Critical | `debugger;` or `debugger\b` | Yes: remove line |
| `no-pdb` | Critical | `pdb\.set_trace\(\)` or `breakpoint\(\)` | Yes: remove line |
| `no-binding-pry` | Critical | `binding\.pry` | Yes: remove line |
| `no-var-dump` | Warning | `var_dump\(` or `dd\(` | Yes: remove line |

### 3.2 Code Quality

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `no-todo-without-ticket` | Warning | `TODO\|FIXME\|HACK\|XXX` without `(#\d+)` or `([A-Z]+-\d+)` | No |
| `no-commented-code` | Info | 3+ consecutive commented-out lines that look like code | No |
| `no-magic-numbers` | Info | Numeric literals > 1 in logic (excluding 0, 1, common HTTP codes) | No |
| `no-empty-catch` | Warning | `catch.*\{[\s]*\}` or `except.*:[\s]*pass` | No |
| `no-swallowed-errors` | Warning | Catch/except blocks without logging or re-raising | No |

### 3.3 Security

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `no-hardcoded-secrets` | Critical | `(api_key\|password\|secret\|token\|private_key)\s*=\s*["'][^"']+["']` | No |
| `no-hardcoded-ip` | Warning | `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` (not in tests/config) | No |
| `no-eval` | Critical | `eval\(` (in JS/Python) | No |
| `no-inner-html` | Warning | `innerHTML\s*=` or `dangerouslySetInnerHTML` | No |
| `no-sql-injection` | Critical | String concatenation/interpolation in SQL queries | No |
| `no-disabled-security` | Critical | `verify=False`, `checkServerIdentity: null`, `rejectUnauthorized: false` | No |

### 3.4 Test Coverage

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `new-function-needs-test` | Warning | New `def`/`function`/`func` declaration in non-test file without corresponding test | No |
| `new-endpoint-needs-test` | Warning | New route/endpoint without corresponding test | No |
| `no-skip-test` | Info | `@skip`, `@ignore`, `xit(`, `xdescribe(`, `test.skip(` without issue reference | No |

### 3.5 Import and Dependency Hygiene

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `no-wildcard-import` | Warning | `from X import *` or `import * from` | No |
| `no-relative-parent-import` | Info | `from ../../` deep relative imports (3+ levels) | No |
| `no-unused-import` | Info | Import statement where the imported name does not appear in the file | No |

---

