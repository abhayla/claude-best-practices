# Scope: global

# Environment Variable Validation — fail fast at boot, reject placeholders

version: "1.0.0"

Any service that reads configuration from environment variables MUST validate
the required ones **at boot, before binding a listener or accepting traffic**.
A missing or placeholder value MUST fail fast with a clear error — not surface
as a 500 three minutes into the first request. This extends `error-handling.md`
(Fail Fast) and `security-baseline.md` (secret management) with the specific
boot-time and placeholder-secret requirements neither currently covers.

## One validator, not scattered checks

- Required variables MUST be enforced in a **single** boot-time validator —
  do NOT scatter `process.env.X ?? throw` (or equivalent) across modules. One
  list is the SSOT for "what this service needs to run."
- The validator MUST run **before** the listener binds, in the startup path —
  never lazily on first request.
- Prod-only soft requirements (e.g. an OAuth client id, a CORS allow-list) MAY
  warn-and-degrade rather than hard-fail, but the degradation MUST be explicit
  and logged — never a silent fallback.

## Placeholder secrets are worse than missing ones

- Placeholder-secret detection MUST be preserved: values like `changeme`,
  `replace-me`, `your-secret-here`, or an obvious default MUST be rejected in
  production. A syntactically valid but placeholder secret passes presence
  checks silently — it is more dangerous than a missing one, because it hides
  the misconfiguration until something is compromised.
- This guards the common failure mode where an example env file is copied into
  production without substitution.

## Never log the bad value

- MUST log the variable **name** only, never its value: `Missing required env
  var: SESSION_SECRET` is correct; `Missing SESSION_SECRET (got: abcd1234)`
  leaks a live secret into logs.

## Adding a new required variable

1. Add the name to the validator's required list (or the prod-only warning list).
2. Add a placeholder-pattern entry if the value is a secret.
3. Update the committed example env file so first-time setup picks it up.
4. Confirm the service fails with a readable message when the var is missing.

## CRITICAL RULES

- MUST validate required env vars at boot, in one validator, before the
  listener binds.
- MUST reject placeholder secrets in production — presence is not validity.
- MUST log only the variable name on failure, never the value.
- MUST NOT scatter ad-hoc env checks across modules; one list is the SSOT.
- MUST make any prod soft-requirement degradation explicit and logged, never silent.
