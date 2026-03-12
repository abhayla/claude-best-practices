---
name: semgrep-rules
description: >
  Create, test, and optimize custom Semgrep rules for vulnerability detection
  and code pattern enforcement. Covers rule anatomy, metavariables, taint mode,
  cross-language porting, false-positive reduction, and CI integration. Based on
  Trail of Bits Semgrep rule creation patterns. Use when writing custom static
  analysis rules or porting rules between languages.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "semgrep, semgrep rule, custom rule, code pattern, linter rule, security pattern"
argument-hint: "<'create <pattern-description>' or 'port <rule-id> to <language>' or 'optimize <rule-file>' or 'test <rule-file>'>"
---

# Semgrep Rule Development

Create production-quality Semgrep rules for detecting security vulnerabilities, bug patterns, and code standards violations.

**Request:** $ARGUMENTS

---

## STEP 1: Analyze the Target Pattern

Before writing any rule, understand the vulnerability or pattern thoroughly.

### Questions to Answer

1. **What is the bug?** Describe the vulnerability class (e.g., SQL injection, hardcoded secret, insecure deserialization)
2. **What does vulnerable code look like?** Write 2-3 concrete examples
3. **What does safe code look like?** Write 2-3 examples that should NOT match
4. **Is this a data flow problem or a syntactic pattern?** Data flow (taint source to sink) requires taint mode; syntactic patterns use pattern matching
5. **Which languages?** List all target languages

### Approach Selection

| Approach | When to Use | Example |
|----------|-------------|---------|
| **Pattern matching** | Syntactic patterns without data flow | Hardcoded passwords, insecure function calls |
| **Taint mode** | Untrusted input reaches dangerous sink | SQLi, XSS, command injection, SSRF |
| **Pattern + metavariable** | Pattern with constraints on matched values | Weak crypto with specific algorithm names |
| **Join mode** | Cross-function or cross-file patterns | Config set in one file, used insecurely in another |

---

## STEP 2: Write Tests First

Create the test file BEFORE the rule. This is mandatory.

### Test File Format

Test files use comment annotations to mark expected matches:

```python
# === Python test file: hardcoded-password.py ===

# ruleid: hardcoded-password
password = "admin123"

# ruleid: hardcoded-password
db_config = {"password": "secret"}

# ok: hardcoded-password
password = os.environ.get("DB_PASSWORD")

# ok: hardcoded-password
password = get_secret("password")

# ok: hardcoded-password
password = ""  # Empty string, not a hardcoded secret
```

```javascript
// === JavaScript test file: hardcoded-password.js ===

// ruleid: hardcoded-password
const password = "admin123";

// ok: hardcoded-password
const password = process.env.DB_PASSWORD;
```

### Annotation Reference

| Annotation | Meaning |
|------------|---------|
| `# ruleid: <id>` | This line MUST trigger the rule |
| `# ok: <id>` | This line MUST NOT trigger the rule |
| `# todoruleid: <id>` | Known false negative — do NOT use, fix the rule instead |
| `# todook: <id>` | Known false positive — do NOT use, fix the rule instead |

### Run Tests

```bash
# Test a single rule
semgrep --test --config <rule-file>.yaml <test-file>

# Test all rules in a directory
semgrep --test --config rules/ tests/

# Validate rule syntax without running
semgrep --validate --config <rule-file>.yaml
```

---

## STEP 3: Examine AST Structure

Understand how Semgrep parses the target code to write precise patterns.

```bash
# Show the AST for a code snippet (helps understand what Semgrep "sees")
semgrep --dump-ast --lang python -e 'password = "admin123"'

# Show pattern match details
semgrep --config <rule>.yaml --debug <test-file> 2>&1 | grep -A5 "matched\|not matched"
```

---

## STEP 4: Write the Rule

### Rule Anatomy

```yaml
rules:
  - id: hardcoded-password
    patterns:
      - pattern: $VAR = "..."
      - metavariable-regex:
          metavariable: $VAR
          regex: (?i)(password|passwd|secret|api_key|token|auth)
      - pattern-not: $VAR = ""
    message: >
      Hardcoded credential detected in variable '$VAR'.
      Use environment variables or a secrets manager instead.
      See https://owasp.org/Top10/A07_2021/
    severity: ERROR
    languages:
      - python
      - javascript
      - typescript
    metadata:
      category: security
      subcategory:
        - audit
      confidence: MEDIUM
      impact: HIGH
      cwe:
        - "CWE-798: Use of Hard-coded Credentials"
      owasp:
        - A07:2021 - Identification and Authentication Failures
      references:
        - https://owasp.org/Top10/A07_2021/
```

### Pattern Operators Reference

| Operator | Purpose | Example |
|----------|---------|---------|
| `pattern` | Match exact code structure | `pattern: os.system($CMD)` |
| `patterns` | AND — all must match | Combine `pattern` + `pattern-not` |
| `pattern-either` | OR — any can match | Multiple sink functions |
| `pattern-not` | Exclude matches | `pattern-not: os.system("literal")` |
| `pattern-inside` | Match only within context | `pattern-inside: \|def $FUNC(...): ...` |
| `pattern-not-inside` | Exclude matches within context | `pattern-not-inside: \|if validate($X): ...` |
| `metavariable-regex` | Constrain metavariable by regex | Filter variable names |
| `metavariable-comparison` | Numeric/string comparison | `metavariable-comparison: $SIZE > 1024` |
| `...` (ellipsis) | Match zero or more arguments/statements | `func($X, ..., $Y)` |
| `$VAR` | Metavariable — captures any expression | `$FUNC($INPUT)` |

### Taint Mode Rule

Use for data flow vulnerabilities (source to sink):

```yaml
rules:
  - id: sql-injection
    mode: taint
    message: >
      User input flows into SQL query without parameterization.
      Use parameterized queries or an ORM instead.
    severity: ERROR
    languages:
      - python
    metadata:
      category: security
      cwe:
        - "CWE-89: SQL Injection"
    pattern-sources:
      - patterns:
          - pattern: flask.request.$ATTR
      - patterns:
          - pattern: request.args.get(...)
      - patterns:
          - pattern: request.form[...]
    pattern-sinks:
      - patterns:
          - pattern: cursor.execute($QUERY, ...)
          - focus-metavariable: $QUERY
      - patterns:
          - pattern: db.execute($QUERY)
          - focus-metavariable: $QUERY
    pattern-sanitizers:
      - patterns:
          - pattern: sqlalchemy.text(...)
      - patterns:
          - pattern: bleach.clean(...)
```

---

## STEP 5: Iterate Until All Tests Pass

```bash
# Run tests — ALL must pass
semgrep --test --config hardcoded-password.yaml hardcoded-password.py

# If tests fail, check:
# 1. Pattern syntax (use --validate)
# 2. Language specification
# 3. Metavariable bindings (use --debug)
# 4. Operator logic (AND vs OR)
```

### Debugging Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| Rule matches nothing | Pattern does not reflect actual AST | Use `--dump-ast` to check structure |
| Rule matches too broadly | Missing `pattern-not` constraints | Add exclusions for safe patterns |
| `ruleid` line not matched | Pattern too specific or wrong language | Generalize with `...` or metavariables |
| `ok` line incorrectly matched | Missing sanitizer or exclusion | Add `pattern-not` or `pattern-not-inside` |
| Metavariable not binding | Metavariable name typo or scope issue | Check `$VAR` spelling and nesting level |

100% test passage is required. Do not proceed with partial passes.

---

## STEP 6: Optimize for Precision

After all tests pass, reduce false positives without losing true positives.

### Optimization Techniques

**Exclude safe contexts:**

```yaml
# Exclude test files by path
paths:
  exclude:
    - "test_*"
    - "*_test.py"
    - "tests/"
    - "spec/"
```

**Narrow with `pattern-not-inside`:**

```yaml
# Only match outside of try/except error handlers
pattern-not-inside: |
  try:
      ...
  except $E:
      ...
```

**Constrain metavariables:**

```yaml
# Only flag if the value looks like a real secret (not a placeholder)
metavariable-regex:
  metavariable: $VALUE
  regex: ^(?!.*(?:TODO|CHANGEME|placeholder|example|xxxx)).*[a-zA-Z0-9]{8,}
```

**Add `focus-metavariable` for precise reporting:**

```yaml
# Report the specific dangerous argument, not the entire call
patterns:
  - pattern: subprocess.run($CMD, shell=True, ...)
  - focus-metavariable: $CMD
```

---

## STEP 7: Common Security Rule Patterns

### SQL Injection

```yaml
- id: sql-injection-string-format
  patterns:
    - pattern-either:
        - pattern: $CURSOR.execute("..." % $VAR)
        - pattern: $CURSOR.execute("...".format(...))
        - pattern: $CURSOR.execute(f"...{$VAR}...")
        - pattern: $CURSOR.execute("..." + $VAR + "...")
  message: "SQL query built with string formatting. Use parameterized queries."
  severity: ERROR
  languages: [python]
```

### Cross-Site Scripting (XSS)

```yaml
- id: flask-xss-response
  patterns:
    - pattern: flask.make_response($CONTENT)
    - pattern-not-inside: |
        $CONTENT = bleach.clean(...)
        ...
  message: "Response content may not be sanitized. Use template auto-escaping or bleach.clean()."
  severity: WARNING
  languages: [python]
```

### Hardcoded Secrets

```yaml
- id: hardcoded-api-key
  patterns:
    - pattern: $VAR = "..."
    - metavariable-regex:
        metavariable: $VAR
        regex: (?i)(api_key|apikey|api_secret|aws_secret|auth_token)
    - metavariable-regex:
        metavariable: $...EXPR
        regex: ^.{8,}$
    - pattern-not: $VAR = ""
    - pattern-not: $VAR = "..."  # test/example placeholder
  message: "Potential hardcoded API key in '$VAR'. Use environment variables or a secrets manager."
  severity: ERROR
  languages: [python, javascript, typescript, go, java, ruby]
```

### Command Injection

```yaml
- id: command-injection-subprocess
  mode: taint
  pattern-sources:
    - pattern: flask.request.$ATTR
    - pattern: input(...)
    - pattern: sys.argv[...]
  pattern-sinks:
    - pattern: subprocess.run($CMD, ..., shell=True, ...)
      focus-metavariable: $CMD
    - pattern: os.system($CMD)
      focus-metavariable: $CMD
    - pattern: os.popen($CMD)
      focus-metavariable: $CMD
  pattern-sanitizers:
    - pattern: shlex.quote(...)
    - pattern: shlex.split(...)
  message: "User input flows into shell command. Use shlex.quote() or avoid shell=True."
  severity: ERROR
  languages: [python]
```

### Path Traversal

```yaml
- id: path-traversal
  mode: taint
  pattern-sources:
    - pattern: request.$ATTR
  pattern-sinks:
    - pattern: open($PATH, ...)
      focus-metavariable: $PATH
    - pattern: pathlib.Path($PATH)
      focus-metavariable: $PATH
  pattern-sanitizers:
    - pattern: os.path.basename(...)
    - pattern: werkzeug.utils.secure_filename(...)
  message: "User input used in file path. Use secure_filename() or os.path.basename()."
  severity: ERROR
  languages: [python]
```

### SSRF

```yaml
- id: ssrf-requests
  mode: taint
  pattern-sources:
    - pattern: request.args.get(...)
    - pattern: request.form[...]
    - pattern: request.json[...]
  pattern-sinks:
    - pattern: requests.get($URL, ...)
      focus-metavariable: $URL
    - pattern: requests.post($URL, ...)
      focus-metavariable: $URL
    - pattern: urllib.request.urlopen($URL)
      focus-metavariable: $URL
  pattern-sanitizers:
    - pattern: validate_url(...)
    - pattern: urlparse(...)
  message: "User input flows into outbound HTTP request. Validate and allowlist target URLs."
  severity: ERROR
  languages: [python]
```

---

## STEP 8: Cross-Language Porting

When porting a rule to another language, adapt the syntax while preserving the detection logic.

### Language-Specific Syntax Mapping

| Concept | Python | JavaScript | Java | Go |
|---------|--------|------------|------|-----|
| String format | `f"...{x}..."` | `` `...${x}...` `` | `"..." + x` | `fmt.Sprintf("...%s...", x)` |
| Function def | `def f(x):` | `function f(x) {` | `void f(String x) {` | `func f(x string) {` |
| HTTP input | `request.args` | `req.query` | `request.getParameter()` | `r.URL.Query()` |
| SQL execute | `cursor.execute()` | `db.query()` | `stmt.executeQuery()` | `db.Query()` |
| Shell exec | `os.system()` | `child_process.exec()` | `Runtime.exec()` | `exec.Command()` |
| File open | `open(path)` | `fs.readFile(path)` | `new FileReader(path)` | `os.Open(path)` |

### Porting Workflow

1. Read the original rule and extract: sources, sinks, sanitizers, pattern logic
2. Map each element to the target language's equivalent API
3. Write target-language test cases (both positive and negative)
4. Write the ported rule
5. Run `semgrep --test` — all tests must pass
6. Test on a real codebase in the target language to check for false positives

---

## STEP 9: CI/CD Integration

### Pre-Commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/semgrep/semgrep
    rev: v1.56.0  # pin to specific version
    hooks:
      - id: semgrep
        args: ["--config", "rules/", "--error", "--metrics=off"]
```

### GitHub Actions

```yaml
# .github/workflows/semgrep.yml
name: Semgrep
on: [pull_request]
permissions:
  contents: read
  security-events: write
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<pin-to-sha>
      - name: Run Semgrep
        run: |
          pip install semgrep
          semgrep scan --config rules/ --sarif -o semgrep.sarif --metrics=off --error
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@<pin-to-sha>
        with:
          sarif_file: semgrep.sarif
        if: always()
```

### Rule Repository Structure

```
rules/
  python/
    sql-injection.yaml
    command-injection.yaml
    hardcoded-secrets.yaml
  javascript/
    xss.yaml
    prototype-pollution.yaml
  shared/
    hardcoded-passwords.yaml   # multi-language rules
tests/
  python/
    sql-injection.py
    command-injection.py
  javascript/
    xss.js
```

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| `semgrep --test` reports "no tests found" | Test file missing annotations or wrong file extension | Add `# ruleid:` and `# ok:` comments; match language extension |
| Rule validates but matches nothing | Pattern does not match AST structure | Run `semgrep --dump-ast` on target code; adjust pattern |
| Taint rule has false negatives | Missing source or sink patterns | Add more source/sink variants; check if sanitizer is too broad |
| Taint rule has false positives | Missing sanitizer patterns | Add `pattern-sanitizers` for legitimate sanitization functions |
| `--test` passes but real scan has false positives | Test cases did not cover edge cases | Add more `# ok:` test cases for common safe patterns |
| Cross-language port misses matches | Language-specific syntax differences | Use `--dump-ast` in target language; check operator precedence |
| Rule is extremely slow | Overly broad `pattern-inside` with deep nesting | Narrow the `pattern-inside` scope; use `paths.include` to limit files |
| `metavariable-regex` does not filter | Regex anchoring issue | Add `^` and `$` anchors; test regex independently |

---

## CRITICAL RULES

### MUST DO

- Write test cases BEFORE writing the rule — test-first development is mandatory
- Include both positive (`# ruleid:`) and negative (`# ok:`) test cases for every rule
- Achieve 100% test passage before considering a rule complete
- Use taint mode for data flow vulnerabilities — pattern matching alone produces false positives for injection bugs
- Include `metadata` with `category`, `cwe`, `confidence`, and `impact` fields in every rule
- Run `semgrep --validate` to check syntax before testing
- Use `--metrics=off` on every Semgrep invocation
- Examine the AST with `--dump-ast` when a pattern does not match as expected
- Pin Semgrep version in CI/CD configurations

### MUST NOT DO

- Skip writing test cases — untested rules produce unpredictable results in production
- Use `# todoruleid:` or `# todook:` annotations — fix the rule to handle the case correctly instead
- Write overly broad patterns that match safe code — add `pattern-not` exclusions for known safe patterns
- Use `languages: generic` unless no language-specific grammar exists — generic mode loses AST precision
- Hardcode file paths in rules — use `paths.include`/`paths.exclude` for path filtering
- Ship rules with less than 3 positive and 3 negative test cases — insufficient coverage misses edge cases
- Use `--config auto` — it enables telemetry; use explicit config paths instead
- Merge rules that fail any test case — 100% passage is the deployment gate
