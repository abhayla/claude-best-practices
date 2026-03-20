# STEP 7: Common Security Rule Patterns

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

