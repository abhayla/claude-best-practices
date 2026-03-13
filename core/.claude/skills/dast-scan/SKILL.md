---
name: dast-scan
description: >
  Dynamic Application Security Testing against a running application.
  OWASP ZAP / Nuclei scanning, header security checks, session management
  testing, API fuzzing, and DAST CI integration. Use after deployment to dev/staging.
triggers:
  - dast scan
  - runtime security
  - dynamic security
  - zap scan
  - nuclei scan
  - header security
  - session security
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<target URL (http://localhost:8000), or 'all endpoints' with base URL>"
---

# DAST Scan — Dynamic Application Security Testing

Run runtime security scans against a live application to find vulnerabilities that static analysis cannot detect.

**Target:** $ARGUMENTS

---

## STEP 1: Pre-flight Checks

Before scanning, verify:

1. **Target is reachable** — `curl -s -o /dev/null -w "%{http_code}" <target>/health`
2. **Target is NOT production** — Confirm the URL is localhost, staging, or a test environment
3. **Auth credentials available** — If the app requires auth, obtain test credentials
4. **Scan scope defined** — List the endpoints/paths to scan (or "all")

```markdown
## DAST Pre-flight

| Check | Status |
|-------|--------|
| Target reachable | ✅ HTTP 200 at <url>/health |
| Non-production | ✅ localhost:8000 |
| Auth configured | ✅ Test user: test@example.com |
| Scope | All API endpoints (/api/*) |
```

**WARNING:** NEVER run DAST scans against production without explicit authorization.

---

## STEP 2: Header Security Audit

Check HTTP security headers on every response:

### 2.1 Required Headers

```bash
# Quick header check
curl -sI <target>/ | grep -iE "^(strict|x-frame|x-content|content-security|referrer|permissions)"
```

| Header | Expected Value | Risk if Missing |
|--------|---------------|-----------------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | MITM attacks, SSL stripping |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` | Clickjacking |
| `X-Content-Type-Options` | `nosniff` | MIME-type sniffing attacks |
| `Content-Security-Policy` | Restrictive policy | XSS, data injection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Information leakage |
| `Permissions-Policy` | Restrict camera, mic, geolocation | Feature abuse |
| `X-XSS-Protection` | `0` (rely on CSP instead) | Legacy — CSP supersedes |
| `Cache-Control` | `no-store` on sensitive endpoints | Cached credentials |

### 2.2 Headers That Must NOT Exist

| Header | Risk |
|--------|------|
| `Server: Apache/2.4.x` | Version disclosure → targeted attacks |
| `X-Powered-By: Express` | Framework disclosure |
| `X-AspNet-Version` | Runtime version disclosure |

Report each missing/incorrect header with severity:

```markdown
| Header | Status | Severity |
|--------|--------|----------|
| Strict-Transport-Security | ❌ Missing | HIGH |
| X-Frame-Options | ✅ DENY | — |
| Content-Security-Policy | ⚠️ Too permissive (unsafe-inline) | MEDIUM |
| Server | ❌ Version disclosed: nginx/1.25 | LOW |
```

---

## STEP 3: OWASP ZAP Scan

### 3.1 Setup

```bash
# Run ZAP in Docker (headless)
docker run -d --name zap --network host \
  ghcr.io/zaproxy/zaproxy:stable \
  zap.sh -daemon -host 0.0.0.0 -port 8090 \
  -config api.disablekey=true

# Wait for ZAP to start
sleep 10
curl -s http://localhost:8090/JSON/core/view/version/
```

### 3.2 API Scan (OpenAPI spec available)

```bash
# Import OpenAPI spec and scan
docker run --network host ghcr.io/zaproxy/zaproxy:stable \
  zap-api-scan.py \
  -t <target>/openapi.json \
  -f openapi \
  -r zap-report.html \
  -w zap-report.md \
  -z "-config replacer.full_list(0).description=auth \
      -config replacer.full_list(0).enabled=true \
      -config replacer.full_list(0).matchtype=REQ_HEADER \
      -config replacer.full_list(0).matchstring=Authorization \
      -config replacer.full_list(0).replacement='Bearer <test-token>'"
```

### 3.3 Baseline Scan (no spec)

```bash
# Spider + passive scan
docker run --network host ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
  -t <target> \
  -r zap-baseline-report.html \
  -w zap-baseline-report.md
```

### 3.4 Interpret Results

| ZAP Risk Level | Severity | Action |
|---------------|----------|--------|
| High | CRITICAL | ❌ BLOCK — must fix before merge |
| Medium | HIGH | ❌ BLOCK — must fix or document accepted risk |
| Low | MEDIUM | ⚠️ Review — fix if feasible |
| Informational | LOW | 📝 Note — no action required |

---

## STEP 4: Nuclei Scan

### 4.1 Run Nuclei Templates

```bash
# Install nuclei
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Run with default + OWASP templates
nuclei -u <target> \
  -t http/ \
  -t cves/ \
  -t vulnerabilities/ \
  -t misconfiguration/ \
  -t exposures/ \
  -severity critical,high,medium \
  -o nuclei-results.txt \
  -json -o nuclei-results.json
```

### 4.2 Custom Checks

Run targeted checks for common web vulnerabilities:

```bash
# Check for exposed sensitive files
nuclei -u <target> -t exposures/files/ -o exposed-files.txt

# Check for misconfigurations
nuclei -u <target> -t misconfiguration/ -o misconfigs.txt

# Check for known CVEs
nuclei -u <target> -t cves/ -severity critical,high -o cves.txt
```

---

## STEP 5: Session Management Testing

### 5.1 Cookie Security

```bash
# Check cookie attributes
curl -sI <target>/login -c - | grep -i "set-cookie"
```

| Attribute | Expected | Risk if Missing |
|-----------|----------|-----------------|
| `Secure` | Present | Cookie sent over HTTP (interceptable) |
| `HttpOnly` | Present | XSS can steal session cookie |
| `SameSite` | `Strict` or `Lax` | CSRF attacks |
| `Path` | Restricted | Cookie available on unintended paths |
| `Max-Age` / `Expires` | Set (not session-only for sensitive) | Session fixation |

### 5.2 Session Fixation

```bash
# Get session before login
SESSION_BEFORE=$(curl -sI <target>/login -c - | grep session | awk '{print $NF}')

# Login and check if session changes
SESSION_AFTER=$(curl -s <target>/login -d 'email=test@example.com&password=test' -c - | grep session | awk '{print $NF}')

# Sessions MUST differ (new session after auth)
[ "$SESSION_BEFORE" != "$SESSION_AFTER" ] && echo "✅ Session regenerated" || echo "❌ SESSION FIXATION VULNERABILITY"
```

### 5.3 Token Security

For JWT/API token authentication:

| Check | Pass Criteria |
|-------|--------------|
| Token expiry | Expires within reasonable time (≤1h for access, ≤7d for refresh) |
| Token revocation | Logout invalidates token server-side |
| Token storage | Not in URL params, not in localStorage for sensitive apps |
| CORS policy | `Access-Control-Allow-Origin` not `*` for auth endpoints |
| Rate limiting | Login endpoint rate-limited (≤10 attempts/min) |

---

## STEP 6: API Fuzz Testing

### 6.1 Input Fuzzing

Test each API endpoint with malicious inputs:

```bash
# SQL Injection payloads
curl -s <target>/api/users?search=' OR 1=1-- -w "%{http_code}"
curl -s <target>/api/users -d '{"email": "\" OR 1=1--"}' -w "%{http_code}"

# XSS payloads
curl -s <target>/api/users -d '{"name": "<script>alert(1)</script>"}' -w "%{http_code}"

# Path traversal
curl -s <target>/api/files/../../etc/passwd -w "%{http_code}"

# Command injection
curl -s <target>/api/process -d '{"cmd": "test; cat /etc/passwd"}' -w "%{http_code}"

# SSRF
curl -s <target>/api/fetch?url=http://169.254.169.254/ -w "%{http_code}"
```

### 6.2 Expected Results

All injection attempts MUST return:
- 400/422 (bad input) or be safely escaped in response
- NEVER return 200 with injected content executed
- NEVER return internal error messages or stack traces

### 6.3 Automated Fuzzing (optional)

```bash
# Using ffuf for endpoint discovery
ffuf -u <target>/api/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,302

# Using RESTler for stateful API fuzzing (if OpenAPI spec available)
dotnet RESTler/restler/Restler.dll fuzz-lean \
  --grammar_file grammar.py \
  --dictionary_file dict.json
```

---

## STEP 7: CI Integration

Add DAST to the CI pipeline (runs on deployed staging):

```yaml
# .github/workflows/dast.yml
name: DAST Security Scan
on:
  deployment_status:
    types: [success]

jobs:
  dast:
    if: github.event.deployment_status.state == 'success'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: ZAP API Scan
        uses: zaproxy/action-api-scan@v0.9.0
        with:
          target: ${{ github.event.deployment_status.target_url }}/openapi.json
          rules_file_name: zap-rules.tsv
          fail_action: true

      - name: Upload Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: dast-report
          path: report_html.html
```

### ZAP Rules File (zap-rules.tsv)

```tsv
10010	IGNORE	# Cookie without Secure flag (dev only)
10011	IGNORE	# Cookie without HttpOnly flag (dev only)
10015	FAIL	# Incomplete or no CSP
10021	FAIL	# X-Content-Type-Options missing
10038	FAIL	# Content-Security-Policy missing
40012	FAIL	# XSS Reflected
40014	FAIL	# XSS Persistent
40018	FAIL	# SQL Injection
90033	FAIL	# Loosely Scoped Cookie
```

---

## STEP 8: DAST Report

Present findings as a structured security report:

```markdown
## DAST Security Report

**Target:** <URL>
**Date:** <date>
**Tools:** ZAP + Nuclei + Manual

### Summary

| Severity | Count | Action |
|----------|-------|--------|
| CRITICAL | 0 | — |
| HIGH | 1 | ❌ Must fix |
| MEDIUM | 3 | ⚠️ Review |
| LOW | 5 | 📝 Noted |

### Findings

#### [HIGH] Missing Content-Security-Policy
- **URL:** All responses
- **Risk:** XSS attacks not mitigated by CSP
- **Fix:** Add CSP header in middleware:
  ```python
  response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
  ```
- **Ref:** OWASP A05:2021 Security Misconfiguration

#### [MEDIUM] Session cookie without SameSite
- **URL:** POST /login
- **Risk:** CSRF attacks possible
- **Fix:** Set `SameSite=Lax` on session cookie
- **Ref:** OWASP A07:2021 Identification and Authentication Failures

### Gate Decision
- **PASS** — No CRITICAL/HIGH findings (or all accepted with documented risk)
- **BLOCK** — N CRITICAL/HIGH findings must be resolved
```

---

## MUST DO

- Always verify target is NOT production before scanning
- Always check HTTP security headers (Step 2)
- Always test session management (cookie attributes, fixation, token security)
- Always test for OWASP Top 10 injection attacks (SQL, XSS, SSRF)
- Always map findings to OWASP Top 10 categories
- Always produce a structured severity report (Step 8)
- Always recommend specific fixes with code examples

## MUST NOT DO

- MUST NOT scan production environments without explicit written authorization
- MUST NOT run active scanning (ZAP active scan, nuclei aggressive) against shared environments without coordination
- MUST NOT report informational findings as blockers
- MUST NOT duplicate SAST findings — this skill covers RUNTIME issues only
- MUST NOT skip header checks even if ZAP is not available — manual curl checks are always possible
- MUST NOT leave ZAP Docker container running after scan completes
