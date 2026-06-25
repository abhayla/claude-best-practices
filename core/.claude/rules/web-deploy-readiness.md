---
description: Web ship-readiness DoD — a web app is not "done" until it is visually verified at mobile/tablet/laptop breakpoints, static hosting sets cache headers (HTML revalidate, hashed assets immutable), every serving host/origin is added to the auth provider's authorized domains, a shared-host deploy is gated on a config-validity check that leaves co-located sites untouched, and owner-alerting + an uptime heartbeat are wired through the Notifier gateway.
globs: ["**/*.html", "**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.svelte", "**/*.astro", "**/app/**", "**/pages/**", "**/firebase.json", "**/nginx*.conf", "**/*.nginx", "**/sites-available/**"]
version: "1.0.0"
---

# Web Deploy-Readiness — the DoD a web app must pass before it ships

A web app that builds, passes unit/functional tests, and renders on the developer's laptop can
still be broken for real users — crushed on a phone, serving a stale bundle, locked out of sign-in
on its new domain, quietly taking down a co-located site, or failing silently in production with no
owner-alert. These five gates are the ship-readiness DoD. They are REACTIVE (each codifies a real
shipped-then-caught miss), and they COMPOSE with — never duplicate — the verification rules:
`supervisor-verification.md` (drive the running UI), `independent-test-verification.md` (blind
re-check), `e2e-persistence-verification.md` (backend read-back), `decision-authority.md` (the deploy
gate is the user's), `notifier-integration.md` (the owner-alerting contract), and the `/vps-deploy`
skill (the deploy mechanics).

## Gate 1 — Visual responsive verification at real breakpoints (NOT just functional)

A functional pass (a click works, a drag persists, data round-trips) is NOT visual verification.
Any UI claimed to work on multiple form factors MUST be **screenshotted and inspected at mobile
(~390px), tablet (~768px), and laptop (~1280px)** on the actually-served build, looking for crushed
labels, overflow, clipped controls, and unreachable navigation — before "done".

- MUST capture + visually inspect the changed screens at the three breakpoints; a green functional
  suite on a touch viewport does NOT satisfy this (the suite can pass while the layout is broken).
- MUST treat inline `display:flex; justify-content:space-between` rows with fixed-width controls as
  a red flag — inline styles cannot express media queries, so they crush labels on narrow screens;
  use a CSS class with a `@media` stack rule instead.
- This is the breakpoint-specific extension of `supervisor-verification.md`'s "drive the UI" gate.

## Gate 2 — Cache headers on static hosting (or new deploys silently don't show up)

Static-export bundles hash their JS/CSS filenames (safe to cache forever) but the HTML references
them — a cached HTML keeps users on an OLD bundle, hiding the deploy.

- MUST set `Cache-Control: no-cache` (revalidate) on HTML / the app shell, and
  `public, max-age=31536000, immutable` on content-hashed asset paths (e.g. `/_next/static/**`).
- On Firebase Hosting the **last matching `headers` glob wins** (order the broad `no-cache` first,
  the immutable asset glob last); on nginx, an asset `location` block + a default `no-cache`.
- MUST verify the live headers after deploy (`curl -I`), not assume them — a stale `index.html` is
  the root cause of "my fix isn't showing" / "the button vanished".

## Gate 3 — Authorized domains per serving host (or sign-in breaks on the new origin)

Auth providers gate redirect/popup flows to an **origin allow-list**. Serving an authenticated app
from a new domain without adding it breaks SSO + magic-link (e.g. Firebase `auth/unauthorized-domain`);
password sign-in keeps working, so the break is easy to miss.

- MUST add EVERY serving origin (apex + `www` + any preview host) to the auth provider's authorized
  domains as part of the deploy — not as a follow-up. For Firebase this is Auth → Settings →
  Authorized domains (see `firebase.md` for the provider specifics).
- MUST verify a real SSO / magic-link sign-in reaches the provider from the new origin before
  declaring auth done — a password-only check hides this class.

## Gate 4 — Shared-host deploys MUST NOT disrupt co-located sites

When a target host serves multiple sites (a shared VPS), a careless deploy can take the others down.

- MUST scope a new site to its own webroot + vhost and gate any web-server reload on a
  **config-validity check that aborts on error** (`nginx -t && systemctl reload`), so a bad config
  never goes live and the other vhosts are untouched. The `/vps-deploy` skill encodes this.
- MUST confirm the co-located sites still serve (smoke each) after the deploy — and TLS for the new
  host (Let's Encrypt) plus DNS are part of the same checklist.

## Gate 5 — Owner-alerting + uptime wired through Notifier (or a production break is silent)

A deployed app with no owner-alerting fails silently — a 5xx spike, a dead datastore, or the whole
process dying goes unnoticed until a user complains. Every production deploy MUST report through the
shared **Notifier** gateway.

- MUST onboard the app to Notifier (register the project + a thin client + `NOTIFIER_URL` /
  `NOTIFIER_KEY`) and emit at least the canonical detectors — signup (P1), unhandled-5xx (P1),
  DB-down (P0), boot-env (P0) — plus a periodic `/heartbeat` for dead-man's-switch coverage. The
  contract is `notifier-integration.md`; the recipe is `Notifier/docs/ONBOARDING.md`.
- MUST be fail-open (unset env → no-op, 2s timeout, never awaited, never throws) and carry NO
  end-user PII; MUST NOT wire healthchecks.io / UptimeRobot / any external pinger instead.

## Definition of DONE (all five — none optional)

A web app's deploy is DONE only when: (1) it is visually verified at 390/768/1280; (2) cache headers
are set AND verified live; (3) every serving origin is in the auth provider's authorized domains AND
a real SSO/magic-link sign-in is verified from it; (4) a shared-host deploy left co-located sites
serving, behind a `-t`-gated reload, with TLS + DNS confirmed; (5) owner-alerting + a heartbeat are
wired through the Notifier gateway (Gate 5). A green build + functional suite is NOT proof of any of
the five.

## CRITICAL RULES

- MUST visually verify changed UI at mobile/tablet/laptop breakpoints (screenshots) before "done" —
  a functional/touch test is NOT visual verification.
- MUST set + live-verify cache headers on static hosting (HTML revalidate, hashed assets immutable)
  so a deploy is not hidden behind a stale bundle.
- MUST add every serving origin to the auth provider's authorized domains and verify a real
  SSO/magic-link sign-in from the new host — never ship auth verified only by password.
- MUST gate a shared-host web-server reload on a config-validity check and confirm co-located sites
  still serve; MUST NOT deploy in a way that can disrupt them.
- MUST wire owner-alerting + a heartbeat through the Notifier gateway (Gate 5) before "done" — a VPS
  deploy with no owner-alerting is not shippable; MUST NOT substitute an external uptime pinger.
- MUST cross-reference (never duplicate) `supervisor-verification.md`, `independent-test-verification.md`,
  `decision-authority.md`, `firebase.md`, `notifier-integration.md`, and the `/vps-deploy` skill
  (`configuration-ssot.md`).
