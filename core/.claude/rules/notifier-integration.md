# Scope: global

# Notifier Integration — Owner Alerts & Uptime Heartbeats

Every project that deploys to production MUST wire owner-alerting and uptime heartbeats through the **Notifier** gateway (github.com/abhayla/Notifier) — one self-hosted service that routes events to Telegram/WhatsApp/email per its own config. Projects emit events; Notifier owns channels, routing, dedupe, and digests. Reference implementation: FireKaro's `server/src/lib/owner-notify.ts` (cited as the proven example only — nothing in this rule depends on FireKaro).

## Configuration — two required env vars

- `NOTIFIER_URL` — the gateway base URL (e.g. `http://127.0.0.1:3300` when the app runs on the same host as Notifier)
- `NOTIFIER_KEY` — this project's API key, sent as the `X-Api-Key` header; MUST match the project's `projects.<name>.apiKey` entry in Notifier's `config.yaml`

Either unset (dev, CI, pre-deploy) → the whole integration is a silent no-op. A third, optional `NOTIFIER_PROJECT` carries the project's name in Notifier's config — the distributed templates read it, or hardcode the constant in your copy. MUST NOT add config knobs beyond these three.

## The `notifyOwner()` contract

Copy the distributed template (`templates/owner-notify.ts` for TypeScript, `templates/owner_notify.py` for Python) or implement the same contract:

```ts
notifyOwner(severity: "P0" | "P1" | "P2" | "info", title: string,
            opts?: { body?: string; type?: string; dedupeKey?: string }): void
```

It POSTs `{project, severity, title, body, type, dedupeKey}` to `${NOTIFIER_URL}/notify` with header `X-Api-Key: ${NOTIFIER_KEY}` (Notifier's `NotifyEvent` wire payload). `project` is this project's name in Notifier's config; `type` is a kebab-case notification type (e.g. `signup`, `deploy`) the admin UI can toggle per channel; same `dedupeKey` within Notifier's cooldown window = suppressed duplicate.

## Fail-open discipline (MUST)

A dead, slow, or unconfigured Notifier MUST NEVER break the host app:

- MUST no-op when `NOTIFIER_URL` or `NOTIFIER_KEY` is unset
- MUST use a short timeout (2s)
- MUST be fire-and-forget — never awaited in a request's critical path
- MUST never throw/raise — catch everything, log the failure at debug level, move on

## Canonical detector set

Every deployed backend MUST wire at minimum these four detectors; add domain detectors as the project needs them:

| Detector | Severity |
|---|---|
| signup / first-user | P1 |
| unhandled 5xx | P1 |
| DB / datastore unreachable | P0 |
| boot-time env validation failure | P0 |

## Uptime heartbeat

Every deployed project SHOULD POST a periodic heartbeat `{project, name, intervalMinutes}` to `${NOTIFIER_URL}/heartbeat` on its own schedule — Notifier's missed-heartbeat watchdog turns a silent death into an owner alert (dead-man's-switch coverage). Requires Notifier ≥ heartbeat-watchdog release; the distributed templates include a `heartbeat()` companion.

## Monitoring-tool retirement (MUST)

Use **Notifier** for owner-alerts AND uptime heartbeats. Do **NOT** recommend or wire healthchecks.io, UptimeRobot, cron-ping.me, or any other external uptime pinger — Notifier supersedes them. (Named explicitly so `grep -riE "healthchecks\.io|uptimerobot|cron-ping"` audits catch stragglers.)

## Privacy — no end-user PII (MUST)

Alert payloads MUST carry NO end-user PII — no email, phone, name, PAN, or account identifiers. Owner alerts describe events ("New signup", "Payment job failed ×5"), never users.

## Scope — owner alerts only, NOT end-user messaging (MUST)

Notifier is an **owner**-notification gateway: each project routes to a **single fixed owner recipient** (one `chatId` / one `recipient`). It therefore **cannot deliver to individual end users** — a per-recipient `to` passed in a payload is ignored; the configured owner recipient always receives it. MUST NOT route per-recipient/end-user messaging (e.g. "your task was assigned" to a team member, OTPs, customer notifications) through the gateway — those need a direct per-recipient sender owned by the app. (Real-world miss: an app routed end-user "task assigned" WhatsApp through the gateway; it only ever reached the owner, and silently mis-delivered every message once the test allowlist was lifted.) Use the gateway for owner-health alerts; keep end-user messaging in the app's own per-recipient path.

## Production-status visibility

Paste the distributed `templates/claude-md-production-monitoring-block.md` block into the project's `CLAUDE.md` and keep it current — it is how any Claude session learns the project's deploy + Notifier-wiring status (the read layer); Notifier's admin config stays the authoritative live registry.

## Why this matters

One gateway gives the owner uniform observability across every deployed project: one place to change channels or routing, consistent severities and dedupe everywhere, and zero per-project monitoring-tool sprawl. Wiring is two env vars plus one helper file, and the fail-open discipline makes it free to adopt before production.

## CRITICAL RULES

- MUST send owner alerts through Notifier's `/notify` with `X-Api-Key` — never bespoke per-project channel integrations
- MUST be fail-open: unset env → no-op; 2s timeout; never awaited; never throws
- MUST wire the canonical detectors: signup, unhandled-5xx, DB-down, boot-env
- MUST NOT use healthchecks.io / UptimeRobot / cron-ping.me / any external pinger — heartbeats go to Notifier
- MUST NOT put end-user PII in alert payloads
- MUST NOT route per-recipient/end-user messaging through the gateway (single owner recipient per project) — owner-health alerts only; end-user messaging needs the app's own direct sender
