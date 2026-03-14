---
name: security-audit
description: >
  Comprehensive security audit workflow: static analysis with CodeQL and Semgrep,
  SARIF triage, variant analysis, differential security review, insecure defaults
  detection, false-positive gating, GitHub Actions hardening, and regulatory
  compliance testing (GDPR, SOC2, HIPAA). Based on Trail of Bits security research
  patterns. Use for security audits, vulnerability discovery, code review, or
  compliance checks.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "security audit, vulnerability, codeql, semgrep, sarif, static analysis, security review, insecure defaults"
argument-hint: "<'full-audit' or 'diff-review' or 'variant <CVE/pattern>' or 'actions-audit'>"
version: "1.0.0"
type: workflow
---

# Security Audit

Run a structured security audit on the target codebase, combining automated static analysis with manual review patterns.

**Request:** $ARGUMENTS

---

## STEP 1: Reconnaissance

Map the attack surface before scanning.

### Inventory

```bash
# Identify languages and frameworks
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.java" -o -name "*.rb" -o -name "*.rs" \) | head -50

# Find entry points (routes, handlers, main files)
grep -rl "app\.route\|@app\.\|router\.\|@Controller\|@RequestMapping\|http\.Handle\|func main" --include="*.py" --include="*.go" --include="*.java" --include="*.js" --include="*.ts" . 2>/dev/null | head -30

# Find auth/crypto usage
grep -rl "password\|secret\|token\|api_key\|JWT\|bcrypt\|hashlib\|crypto" . --include="*.py" --include="*.js" --include="*.go" --include="*.java" 2>/dev/null | head -20

# Find configuration files
find . -name "*.env*" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" -o -name "*.ini" -o -name "*.cfg" -o -name "docker-compose*" -o -name "Dockerfile*" 2>/dev/null | head -20
```

### Attack Surface Checklist

| Surface | What to Look For |
|---------|-----------------|
| HTTP endpoints | Input validation, auth guards, rate limiting |
| Database queries | Parameterized queries vs string concatenation |
| File operations | Path traversal, unrestricted uploads |
| External calls | SSRF, command injection, deserialization |
| Auth/session | Token handling, session fixation, privilege escalation |
| Crypto | Weak algorithms, hardcoded keys, improper IV/nonce |
| Config | Secrets in code, debug modes, permissive CORS |

---

## STEP 2: Static Analysis

Run CodeQL and Semgrep. Always use `--metrics=off` with Semgrep.

### Semgrep Scan

```bash
# Check Semgrep availability
semgrep --version

# Run with OWASP and security rulesets
semgrep scan --config p/owasp-top-ten --config p/security-audit --metrics=off --sarif -o semgrep-results.sarif .

# Run Trail of Bits rules (if available)
semgrep scan --config p/trailofbits --metrics=off --sarif -o semgrep-tob.sarif . 2>/dev/null

# High-confidence only
semgrep scan --config p/security-audit --severity ERROR --severity WARNING --metrics=off --json -o semgrep-high.json .
```

### CodeQL Scan

```bash
# Create database (replace LANGUAGE with detected language)
codeql database create codeql-db --language=LANGUAGE --source-root=.

# Run security queries
codeql database analyze codeql-db --format=sarif-latest --output=codeql-results.sarif -- codeql/LANGUAGE-queries:codeql-suites/LANGUAGE-security-extended.qls
```

### SARIF Triage

Parse SARIF output to prioritize findings:

```bash
# Extract high-severity findings from SARIF
python3 -c "
import json, sys
with open('semgrep-results.sarif') as f:
    sarif = json.load(f)
for run in sarif.get('runs', []):
    for result in run.get('results', []):
        level = result.get('level', 'note')
        rule_id = result.get('ruleId', 'unknown')
        msg = result.get('message', {}).get('text', '')[:120]
        locs = result.get('locations', [])
        loc = locs[0]['physicalLocation'] if locs else {}
        uri = loc.get('artifactLocation', {}).get('uri', '?')
        line = loc.get('region', {}).get('startLine', '?')
        if level in ('error', 'warning'):
            print(f'[{level.upper()}] {rule_id} | {uri}:{line} | {msg}')
"
```

### Severity Classification

| Level | Criteria | Examples |
|-------|----------|---------|
| **Critical** | Remote code execution, auth bypass, data exfiltration | SQLi, RCE, SSRF to internal services |
| **High** | Significant data exposure, privilege escalation | XSS with session theft, path traversal, broken access control |
| **Medium** | Limited impact or requires specific conditions | CSRF, open redirect, information disclosure |
| **Low** | Minimal direct impact, defense-in-depth | Missing security headers, verbose errors, weak cookie flags |

---

## STEP 3: Variant Analysis

After finding one vulnerability, search for similar patterns across the entire codebase.

### Workflow

1. **Extract the pattern** from the confirmed finding (e.g., unsanitized user input passed to `subprocess.run`)
2. **Generalize** the pattern: identify the source (user input), the sink (dangerous function), and the missing sanitizer
3. **Search broadly** using Grep/Glob for all instances of the sink function
4. **Filter** results to those reachable from untrusted sources
5. **Verify** each candidate manually

### Example: Command Injection Variants

```bash
# Find all subprocess/exec calls
grep -rn "subprocess\.\|os\.system\|os\.popen\|exec(\|eval(\|child_process\|Runtime\.exec" --include="*.py" --include="*.js" --include="*.java" . 2>/dev/null

# Trace back: do any of these use request/user input?
grep -rn "request\.\|req\.\|argv\|stdin\|input()\|params\[" --include="*.py" --include="*.js" . 2>/dev/null
```

### Variant Checklist

- [ ] All instances of the same sink function reviewed
- [ ] Cross-language equivalents checked (e.g., `os.system` in Python, `exec` in JS)
- [ ] Similar but distinct patterns identified (e.g., `subprocess.run` vs `subprocess.Popen`)
- [ ] Data flow from source to sink verified for each candidate
- [ ] False positives documented with reasoning

---

## STEP 4: Differential Security Review

Review git diffs for security-relevant changes.

```bash
# Get recent changes (adjust range as needed)
git log --oneline -20
git diff HEAD~5..HEAD --stat

# Focus on security-sensitive areas
git diff HEAD~5..HEAD -- "*.py" "*.js" "*.ts" "*.go" "*.java" | head -500
```

### What to Flag in Diffs

| Change Type | Risk | What to Check |
|-------------|------|---------------|
| New HTTP endpoints | High | Auth middleware, input validation, rate limiting |
| Auth/permission changes | Critical | Bypass paths, default-allow vs default-deny |
| Input handling changes | High | New user inputs without sanitization |
| Crypto changes | Critical | Algorithm downgrades, key handling, IV reuse |
| Dependency additions | Medium | Known CVEs, typosquatting, excessive permissions |
| Config changes | Medium | Debug flags, CORS loosening, secret exposure |
| Error handling changes | Low | Stack trace exposure, error message information leak |
| SQL/query changes | High | Parameterization, ORM misuse, raw queries |

---

## STEP 5: Insecure Defaults Detection

Scan for common insecure default configurations.

### Patterns to Detect

```bash
# Default/hardcoded passwords
grep -rn "password.*=.*['\"]" --include="*.py" --include="*.js" --include="*.yaml" --include="*.yml" --include="*.env*" --include="*.json" . 2>/dev/null | grep -iv "test\|spec\|mock\|example\|placeholder\|TODO\|CHANGE_ME"

# Debug mode enabled
grep -rn "DEBUG.*=.*[Tt]rue\|debug.*:.*true\|FLASK_DEBUG\|NODE_ENV.*development" --include="*.py" --include="*.js" --include="*.env*" --include="*.yaml" . 2>/dev/null

# Permissive CORS
grep -rn "Access-Control-Allow-Origin.*\*\|cors.*origin.*\*\|allow_all_origins\|CORS_ALLOW_ALL" --include="*.py" --include="*.js" --include="*.ts" --include="*.yaml" . 2>/dev/null

# Verbose error messages in production
grep -rn "traceback\|stack_trace\|print_exc\|e\.printStackTrace\|console\.error.*err\." --include="*.py" --include="*.js" --include="*.java" . 2>/dev/null

# Disabled SSL verification
grep -rn "verify.*=.*False\|SSL_VERIFY.*false\|rejectUnauthorized.*false\|InsecureSkipVerify.*true" --include="*.py" --include="*.js" --include="*.go" . 2>/dev/null

# Weak crypto
grep -rn "MD5\|SHA1\|DES\|RC4\|ECB\|math\.random\|Math\.random" --include="*.py" --include="*.js" --include="*.java" --include="*.go" . 2>/dev/null
```

---

## STEP 6: GitHub Actions Security

Audit CI/CD workflow files for security issues.

```bash
# Find all workflow files
find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null
```

### Actions Audit Checklist

| Issue | Pattern | Fix |
|-------|---------|-----|
| **Script injection** | `${{ github.event.*.title }}` in `run:` blocks | Use environment variables instead of inline expressions |
| **Unpinned actions** | `uses: actions/checkout@main` | Pin to full SHA: `uses: actions/checkout@<sha>` |
| **Secrets in logs** | `echo ${{ secrets.TOKEN }}` | Use `::add-mask::` or avoid echoing secrets |
| **Excessive permissions** | No `permissions:` block or `permissions: write-all` | Add explicit minimal `permissions:` per job |
| **Pull request target** | `on: pull_request_target` with checkout of PR code | Use `on: pull_request` or avoid checking out PR HEAD |
| **Artifact poisoning** | Uploading/downloading artifacts across trust boundaries | Validate artifact contents, use separate workflows |

```bash
# Check for unpinned actions
grep -n "uses:.*@" .github/workflows/*.yml 2>/dev/null | grep -v "@[a-f0-9]\{40\}"

# Check for script injection patterns
grep -n '\${{.*github\.event' .github/workflows/*.yml 2>/dev/null

# Check for missing permissions
grep -L "permissions:" .github/workflows/*.yml 2>/dev/null
```

---

## STEP 7: False-Positive Gating

Every finding MUST pass this verification before reporting.

### Gated Review Process

For each finding, answer ALL of these questions:

1. **Is the code reachable?** Trace the call path from an entry point. Dead code is not a finding.
2. **Is the input attacker-controlled?** Identify the source. Internal-only inputs with no external exposure are lower risk.
3. **Is there an existing mitigation?** Check for sanitizers, validators, WAF rules, or framework-level protections upstream.
4. **Is the impact real?** Can an attacker actually exploit this to cause harm in the deployed context?
5. **Is this a test/example file?** Findings in `test/`, `spec/`, `examples/`, `fixtures/` are informational only.

If ANY answer disqualifies the finding, mark it as **false positive** with the specific reason. Do NOT report it as a vulnerability.

---

## STEP 8: OWASP Top 10 Checklist

Cross-reference findings against OWASP Top 10 (2021):

| # | Category | Key Checks |
|---|----------|------------|
| A01 | Broken Access Control | Missing auth on endpoints, IDOR, privilege escalation, CORS misconfiguration |
| A02 | Cryptographic Failures | Weak algorithms, hardcoded keys, plaintext secrets, missing encryption at rest/transit |
| A03 | Injection | SQLi, XSS, command injection, LDAP injection, template injection |
| A04 | Insecure Design | Missing rate limiting, no abuse case handling, excessive data exposure by design |
| A05 | Security Misconfiguration | Default credentials, unnecessary features enabled, missing security headers |
| A06 | Vulnerable Components | Outdated dependencies with known CVEs, unpatched libraries |
| A07 | Auth Failures | Weak passwords permitted, missing MFA, session fixation, credential stuffing exposure |
| A08 | Data Integrity Failures | Missing integrity checks on updates, insecure deserialization, unsigned CI/CD pipelines |
| A09 | Logging Failures | Missing audit logs, sensitive data in logs, no alerting on security events |
| A10 | SSRF | Unvalidated URL inputs, internal service access, cloud metadata endpoint access |

---

## STEP 9: Compliance Testing (GDPR / SOC2 / HIPAA)

Verify regulatory compliance requirements through automated checks and structured audits. Skip sections not applicable to the project's regulatory scope.

### 9.1 Detect Applicable Regulations

| Signal | Regulation | Trigger |
|--------|-----------|---------|
| Stores EU user data | GDPR | User location, `.eu` domains, EU payment processors |
| Handles payment/financial data | SOC2 | Stripe, payment endpoints, financial records |
| Stores health/medical data | HIPAA | Patient records, health APIs, medical terminology in schemas |
| Stores children's data | COPPA | Age gates, parental consent flows |
| Processes biometric data | BIPA / GDPR Art.9 | Face recognition, fingerprint, voice data |

### 9.2 GDPR Compliance Checklist

```bash
# Find personal data storage (PII columns)
grep -rn "email\|phone\|address\|birth\|ssn\|passport\|ip_address\|location" --include="*.py" --include="*.ts" --include="*.kt" --include="*.sql" src/ 2>/dev/null

# Check for consent collection
grep -rn "consent\|gdpr\|opt.in\|opt.out\|privacy.policy\|cookie.consent" --include="*.py" --include="*.ts" --include="*.kt" --include="*.html" src/ 2>/dev/null

# Check for data deletion endpoints
grep -rn "delete.*account\|delete.*user\|right.to.be.forgotten\|erasure\|anonymize\|purge" --include="*.py" --include="*.ts" --include="*.kt" src/ 2>/dev/null
```

| Requirement | Check | Pass Criteria |
|-------------|-------|---------------|
| **Lawful basis** | Consent collected before data processing | Consent endpoint exists, recorded in DB with timestamp |
| **Right to access** | Data export endpoint | User can download their data in machine-readable format (JSON/CSV) |
| **Right to erasure** | Account deletion endpoint | Hard-delete or anonymize all PII; cascade to backups within 30 days |
| **Data minimization** | Only necessary fields collected | No PII columns beyond what features require |
| **Purpose limitation** | Data used only for stated purpose | No PII in analytics, logs, or third-party calls without consent |
| **Breach notification** | Incident response process exists | Alert mechanism for data breaches within 72 hours |
| **Data portability** | Export in standard format | JSON/CSV export of user data |
| **Privacy by design** | PII encrypted at rest and in transit | Column encryption for PII, TLS enforced |

### 9.3 SOC2 Trust Principles Checklist

| Principle | Check | Verification |
|-----------|-------|-------------|
| **Security** | Access controls, encryption, vulnerability management | Auth on all endpoints, RBAC implemented, dependencies patched |
| **Availability** | Uptime monitoring, disaster recovery | Health check endpoint, backup/restore tested, SLA defined |
| **Processing integrity** | Input validation, error handling, audit logs | Validation on all inputs, structured error responses, audit trail |
| **Confidentiality** | Data classification, encryption, access logging | PII marked and encrypted, access logged, least privilege |
| **Privacy** | Notice, consent, collection limitation | Privacy policy, consent mechanism, data retention policy |

### 9.4 HIPAA Compliance Checklist (PHI — Protected Health Information)

| Safeguard | Check | Verification |
|-----------|-------|-------------|
| **Access control** | Unique user IDs, emergency access, auto-logoff | Per-user auth, session timeout ≤15min, break-glass procedure |
| **Audit controls** | All PHI access logged | Immutable audit log with user, timestamp, action, resource |
| **Integrity** | PHI not improperly altered | Checksums on PHI records, change tracking |
| **Transmission security** | PHI encrypted in transit | TLS 1.2+ enforced, no plaintext PHI in URLs/headers |
| **Encryption at rest** | PHI encrypted in storage | AES-256 for PHI columns, encrypted backups |
| **BAA** | Business Associate Agreements | All third-party services handling PHI have signed BAAs |
| **Minimum necessary** | Only required PHI accessed | Role-based PHI access, field-level permissions |

### 9.5 Automated Data Flow Mapping

For each PII/PHI field identified, trace the full data flow:

```markdown
## Data Flow: user.email

| Stage | Location | Protection | Compliant |
|-------|----------|------------|-----------|
| Collection | POST /api/register | TLS, input validation | ✅ |
| Storage | users.email column | AES-256 column encryption | ✅ |
| Processing | send_welcome_email() | In-memory only, not logged | ✅ |
| Sharing | Stripe API (payment) | BAA signed, encrypted | ✅ |
| Logging | app.log | ❌ Email appears in logs | ❌ FIX |
| Retention | No auto-delete policy | — | ❌ FIX |
| Deletion | DELETE /api/account | Cascades to all tables | ✅ |
```

### 9.6 Compliance Report Section

Add to the security report output:

```markdown
### Compliance Status

| Regulation | Applicable | Status | Issues |
|-----------|-----------|--------|--------|
| GDPR | ✅ Yes | ⚠️ 2 issues | Missing data export, PII in logs |
| SOC2 | ✅ Yes | ✅ Pass | — |
| HIPAA | ❌ N/A | — | — |

### Data Flow Audit
- PII fields found: 5 (email, phone, name, address, DOB)
- Fully traced: 4/5
- Issues: 1 field (email) appears in application logs — MUST mask
```

---

## Output Format: Security Report

Structure findings in this format:

```markdown
## Security Audit Report

**Scope:** [repository/directory audited]
**Date:** [audit date]
**Tools:** [Semgrep version, CodeQL version, manual review]

### Executive Summary
- Total findings: X (Y Critical, Z High, W Medium, V Low)
- False positives filtered: N

### Critical Findings
#### [FINDING-001] [Title]
- **Severity:** Critical
- **Category:** OWASP A03 — Injection
- **Location:** `src/api/users.py:45`
- **Description:** [What the vulnerability is]
- **Impact:** [What an attacker can do]
- **Evidence:** [Code snippet or tool output]
- **Remediation:** [Specific fix with code example]
- **Verification:** [How to confirm the fix works]

### High Findings
...

### Recommendations
1. [Priority-ordered remediation steps]
```

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| Semgrep returns no results | Wrong config or language not detected | Run `semgrep --show-supported-languages`; specify `--lang` explicitly |
| CodeQL database creation fails | Missing build dependencies | Install language-specific build tools; check `codeql resolve languages` |
| SARIF file is empty or malformed | Scan exited early with errors | Check stderr output; run scan with `--verbose` flag |
| Too many false positives | Overly broad rulesets | Use `--severity ERROR` filter; add `--exclude` for test directories |
| Variant search returns thousands of hits | Pattern too generic | Narrow with file type filters and path exclusions |
| GitHub Actions audit misses workflows | Non-standard workflow directory | Check for `.github/actions/` composite actions and reusable workflows |
| Git diff too large to review | Broad commit range | Narrow to specific paths or use `--diff-filter=M` for modified files only |
| Permission errors running tools | Missing tool installation | Install via `pip install semgrep`, `gh extension install` for CodeQL |

---

## CRITICAL RULES

### MUST DO

- Run `--metrics=off` on every Semgrep invocation to prevent telemetry leakage
- Verify every finding through the false-positive gating process (Step 7) before reporting
- Pin all actions to full commit SHAs in GitHub Actions audit recommendations
- Include OWASP category mapping for every confirmed finding
- Classify severity for every finding using the table in Step 2
- Search for variants after every confirmed vulnerability (Step 3)
- Provide specific, actionable remediation with code examples for each finding
- Exclude test/fixture/example files from vulnerability counts (flag as informational only)
- Run compliance checks (Step 9) when the project stores user PII, health data, or financial data
- Trace data flow for every PII/PHI field identified — collection through deletion

### MUST NOT DO

- Report unverified static analysis findings as confirmed vulnerabilities — use the gating process instead
- Use `--config auto` with Semgrep — it enables metrics collection
- Skip variant analysis after finding a vulnerability — similar bugs cluster in codebases
- Ignore GitHub Actions workflow files — CI/CD is a privileged execution environment
- Assume framework defaults are secure — verify each security-relevant configuration explicitly
- Run CodeQL or Semgrep without capturing SARIF output — raw console output is not auditable
- Report findings in test files at the same severity as production code — use informational severity instead
- Omit remediation steps from findings — every finding MUST include a specific fix
- MUST NOT skip compliance checks for projects that handle user data — regulatory fines far exceed technical debt costs
- MUST NOT mark compliance as "pass" without verifying data deletion and export endpoints actually work
