# Scope: global

# Security Baseline

Universal security constraints that apply to all code in this project, regardless of language or framework. Stack-specific rules (e.g., `fastapi-backend.md`, `firebase.md`) extend these with framework specifics — they do not replace them.

## Top-Level MUST NOTs

- MUST NOT commit secrets (API keys, tokens, passwords, certificates) to version control — if discovered, rotate before fixing history
- MUST NOT trust client-supplied data — the browser, mobile app, and SDK are all attacker-controllable
- MUST NOT disable security controls (CSRF, SSL verification, auth middleware, sandbox flags) to make tests or CI pass — fix the failing code instead

## Input Validation

MUST validate all data crossing a trust boundary (user input, external APIs, file I/O, queue messages, IPC) before it reaches business logic. Validation MUST check type, length, format, and range — not just presence.

- Use allow-lists over deny-lists (`^[a-zA-Z0-9_-]+$` is safer than "reject `<script>`")
- Reject at the edge — never sanitize-and-continue on malformed data
- Re-validate server-side even when the client already validated; client validation is UX, not security

## Secret Management

MUST NOT hard-code secrets in source, committed config, test fixtures, or documentation. Source secrets from environment variables, platform secret stores (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, Kubernetes Secrets), or CI-injected values.

- Redact secrets by field name before logging, telemetry, or error messages
- Assume git history is permanent and replicated — rotating the exposed secret is mandatory; rewriting history (`git filter-branch`, `git filter-repo`, force-push) is best-effort cleanup, not a substitute for rotation
- Separate dev/staging/prod secrets; never share credentials across environments

## Least Privilege

Every principal (code, service account, database user, CI token, deploy credential) MUST operate with the minimum permissions required for its function. Deny-by-default is the baseline; grants are explicit.

- Per-service database users, never a shared superuser
- CI tokens scoped to one repo and the minimum actions (read, not admin)
- Service accounts never granted `*` or `Admin` — enumerate the exact permissions needed
- Review granted permissions quarterly; revoke unused ones

## Dependency Hygiene

MUST run a dependency vulnerability scan on every pull request. MUST NOT add a dependency without evaluating maintenance activity, license compatibility, and transitive surface area.

- Pin direct dependencies and commit lockfiles (`package-lock.json`, `bun.lockb`, `poetry.lock`, `Cargo.lock`, `go.sum`)
- Use `/supply-chain-audit` or native tooling (`npm audit`, `pip-audit`, `cargo audit`, `gradle dependencyCheckAnalyze`)
- Remove unused dependencies — dead code still ships to production and still has CVEs
- Evaluate before adding: last release date, maintainers, downstream users, alternative with smaller surface

## Defense in Depth

MUST NOT rely on a single security control. Apply multiple independent layers so that any single bypass does not compromise the system.

- Authentication + authorization + input validation + output encoding + rate limiting — each layer independent of the others
- Encryption at rest AND in transit, not just one
- Logging and alerting independent of the control plane being compromised — if auth breaks, alerts must still fire

## Output Encoding

MUST encode data appropriately for the sink (HTML, SQL, shell, LDAP, JSON, XML, URL) — never concatenate untrusted strings into an interpreted context.

- Use parameterized queries / prepared statements — never string-concatenate SQL, even for "internal" queries
- Context-aware HTML escaping (element, attribute, URL, JavaScript, CSS contexts each need different encoding)
- Use argv arrays when invoking subprocesses, never a shell string built from user input

## CRITICAL RULES

- MUST NOT commit secrets — scan every PR with a secret detector
- MUST NOT trust any data crossing a trust boundary until validated
- MUST NOT disable security features to pass tests — fix the code or the test
- MUST NOT catch-and-ignore security exceptions — let them propagate to logging and alerting
- MUST run dependency vulnerability scans on every PR, not just on release
- MUST rotate any secret that appears in git history, even after force-push
