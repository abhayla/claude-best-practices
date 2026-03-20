# STEP 4: Write the Rule

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

