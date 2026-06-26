# Analytics Framework — Cross-Platform + Blanket Interaction Tracking

Status: in-progress (2026-06-25) · Owner directive: Abhay 2026-06-25
Goal served: G1 (distribute reusable patterns), G4 (thin layer on Google's platform)

## Context — what already exists (do NOT rebuild)

The hub ALREADY ships a web analytics framework, registered + enforced:

- **`analytics-setup` skill** — GA4 via GTM, Consent Mode v2, explicit CTA/affiliate
  events, verify-real-`g/collect`-hit, Search Console, inventory recording, BigQuery+Looker
  portfolio note. Per-framework injection (Next/Nuxt/Vue/Astro/Svelte/static).
- **`web-analytics-instrumentation` rule** — the path-scoped ship-gate standard (web files).

These match Google's official best practices (verified via web research 2026-06-25).
The owner's request ("track every visitor + every button/link, auto-included, all app
types, Google-official") is ~70% already met for WEB.

## Why the owner sees no data (the actual blocker)

Per `GLOBAL.md` §4 analytics inventory: **no GA4 account/properties exist yet.** The
framework has nothing to inject because no Measurement IDs were ever created — and GA4
property creation needs the owner's Google login (or a connected GA-Admin service account).
This is a credential gate, escalated separately. Live sites with ZERO analytics today:
realfuelpricesinindia.com, makepassiveincome.in (also DOWN), calculatekaro.in (watch).

## Gaps to close (this initiative)

1. **Blanket interaction tracking** ("every button and every link") — current skill does
   EXPLICIT CTA/affiliate events only (deliberately, to avoid noise). Add an OPT-IN blanket
   mode: GTM "All Elements" Click trigger + a `data-track`/`data-event` attribute convention
   + a delegated-listener snippet for SPAs + a standard data-layer event schema. Opt-in, not
   mandated — preserves the explicit-events default's rationale.
2. **Platform-agnostic standard** ("all app types") — current standard is web-only. Make the
   PRINCIPLE platform-agnostic; provide mobile (Firebase Analytics: Flutter/RN/Android) and
   desktop (GA4 Measurement Protocol: Electron/Windows) PROCEDURES as a skill reference.
   YAGNI: do NOT build heavy per-platform tooling until a real mobile/Windows app needs it —
   the procedures are ready; deep tooling waits for the first concrete caller.

## Automation path (researched, owner-gated — needs Google credentials once)

- GA4 **Admin API** + GTM **API v2** via a **service account** CAN create properties, data
  streams (→ Measurement IDs), and GTM containers programmatically. Scopes: `analytics.edit`,
  `tagmanager.edit.containers`, `tagmanager.publish`. SA must be granted Admin on the GA
  account once (owner's Google account).
- Google's **official read-only** GA4 MCP (`googleanalytics/google-analytics-mcp`, Apache-2.0)
  reads reports/realtime — wire with `analytics.readonly` to pull visitor numbers into sessions.
- No official Google GTM MCP; `paolobietolini/gtm-mcp-server` (BSD-3, service-account) is the
  best third-party if MCP-based GTM management is ever wanted.

## Decision the owner must make (credential-gated)

- **Option A (manual, fast):** owner creates GA4 properties in the UI per live site, pastes
  `G-…`/`GTM-…`; hub rolls the existing framework into each site + verifies + records. Unblocks
  data immediately, zero new infra.
- **Option B (automated):** owner provisions a Google service account (scopes above) +
  optionally connects the official GA4 MCP; hub then auto-creates properties/streams/containers
  for every new site. The "automatically covered" dream — but more one-time setup, still needs
  the owner's Google account to create the SA.

## Roadmap

- [x] Research (Google stack + MCP/skill landscape) — 2026-06-25
- [x] Build Gap 1: blanket interaction tracking (`/analytics-setup` STEP 4b + rule bullet + `ui_click` schema)
- [x] Build Gap 2: rule pointer to non-web + skill `references/cross-platform.md` (Firebase + Measurement Protocol)
- [x] Registry resync (4 hashes incl. 2 pre-existing drifts from ca2019d) + full local CI (1592 pass)
- [x] ESCALATE the Option A/B credential decision to owner — **owner chose Option B (automated SA) 2026-06-25**
- [ ] OWNER (credential gate): create a Google service account, grant scopes `analytics.edit` +
      `tagmanager.edit.containers` + `tagmanager.publish`, grant it **Administrator on the GA account**,
      download the JSON key → store path in `GLOBAL.env` as `GA_PROVISION_SA_KEY` (secret, never in repo)
- [ ] BUILD (after SA key lands, so it can be live-tested — do NOT ship untested API code): a hub
      auto-provisioning skill wrapping GA4 Admin API (create property + web data stream → Measurement ID)
      + GTM API v2 (create container + GA4 config tag + Consent Mode v2 + `ui_click` trigger + publish),
      then hand off to `/analytics-setup` STEP 6 verify + record IDs in GLOBAL.md §4
- [ ] WIRE official read-only GA4 MCP (`googleanalytics/google-analytics-mcp`, `analytics.readonly`) so
      sessions can pull live visitor numbers
- [ ] roll out to live web sites (RealFuelPrices, CalculateKaro, makepassiveincome once back up) + verify hits
- [ ] (deferred, YAGNI) deep mobile/desktop tooling when first such app appears
