---
name: auto-google-analytics
description: >
  Autonomously instrument THIS project with Google Analytics 4 end-to-end — detect stack &
  hosting type, provision the GA4 property + web stream (service-account, no browser login),
  inject the gtag + Consent Mode v2 + blanket ui_click snippet into source, verify a real hit
  reaches GA4 browser-free, and record the IDs in a project-local inventory. Use when setting
  up or auditing web VISITOR analytics on a project that has the auto-google-analytics plugin
  installed, or when a site is shipping with no measurement. This is the autonomous end-to-end
  orchestrator wrapping the bundled /analytics-setup engine — use that engine directly for
  manual/per-framework instrumentation with an already-known Measurement ID. Not for code
  metrics, test coverage, app/infra observability, or internal BI dashboards. The one-time
  service-account key is the only human prerequisite; without it the skill falls back to
  guided manual setup.
type: workflow
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[--audit] [--site \"Name=https://origin\"]"
version: "1.1.0"
triggers:
  - auto analytics
  - set up analytics
  - instrument analytics
  - add ga4
---

# auto-google-analytics — zero-touch GA4 for any project

The autonomous orchestrator. It wraps the bundled **analytics-setup** engine (the instrumentation
SSOT — read `skills/analytics-setup/SKILL.md` for per-framework detail and the consent/event
contract) and the three bundled scripts under `${CLAUDE_PLUGIN_ROOT}/scripts/`:
`provision_ga4.py` (create property → Measurement ID), `inject_analytics.py` (static HTML
injection), `verify_hit.py` (browser-free hit verification).

**Boundary:** this skill is the end-to-end ORCHESTRATOR (provision → inject → verify → record);
`/analytics-setup` is the per-framework instrumentation ENGINE it delegates to. A plain
"set up analytics" ask on a plugin-installed project lands HERE; invoke the engine directly only
for manual instrumentation against an already-known Measurement ID or GTM container.

**Definition of done:** a real hit is verified in GA4 realtime AND the Measurement ID is recorded
in `.claude/analytics-inventory.json` AND the tag lives in committed source (not only a transient
server-side injection). Snippet-on-page is NOT done.

## STEP 0 — Preflight (settings + credential)

1. The hooks export settings from `auto-google-analytics-settings.json` (see `_settings.sh`). If
   `enabled` is false, stop: "auto-google-analytics disabled in settings."
2. Locate the service-account key: `GA_PROVISION_SA_KEY` env (set from settings `sa_key_path`).
   - **Present** → fully autonomous path (STEP 1+).
   - **Absent** → GUIDED-MANUAL fallback: print the one-time setup from the README ("create a
     service account with `analytics.edit`, grant it Administrator at the GA account level,
     save the key, set `sa_key_path`"). Then either accept owner-supplied Measurement IDs and
     skip to STEP 4 — injection with the supplied ID (STEP 3 provisioning is impossible without
     the key; pass the ID explicitly, e.g. `inject_analytics.py --id G-XXX`, or use it in the
     framework edit) — or stop with `SETUP_REQUIRED`. Never fabricate IDs.

## STEP 1 — Detect stack & hosting type

Delegate detection to the bundled engine: `Skill("/analytics-setup")` STEP 1, or inline —
identify framework (Next/Nuxt/Vue/Astro/SvelteKit/static/non-web) and hosting (static webroot,
built `dist/`, dynamic/proxied, edge). For **non-web** (mobile/desktop) route to
`skills/analytics-setup/references/cross-platform.md` and stop the web flow. A repo containing
BOTH a web app and a mobile/desktop app gets BOTH tracks: run this web flow for the web app AND
route the non-web app to `cross-platform.md` — one does not replace the other.

## STEP 2 — Resolve the site origin

Use `--site "Display Name=https://origin"` if given; else derive: the production origin from the
project's deploy config / README / package homepage. If NO origin can be derived from any of
those sources, STOP and ask the owner for it — never guess an origin into a real GA4 property.
If a given `--site` origin conflicts with the origin in the deploy config, `--site` wins, but
FLAG the mismatch in one line before proceeding. One GA4 property per site — never reuse a
Measurement ID across sites.

## STEP 3 — Provision (autonomous)

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/provision_ga4.py" \
  --site "<Name>=<origin>" --out .claude/analytics-inventory.json
```
Idempotent (skips an existing property). On `NO_GA_ACCOUNT_VISIBLE` the SA grant is missing —
surface the one-time grant step and stop. The inventory now holds property + Measurement ID +
stream per origin.

## STEP 4 — Inject the tag into SOURCE (durable)

Prefer a committed source edit over a transient server-side injection (`sub_filter` is lost on
redeploy — record it as TEMP if it's the only option).

- **Static HTML / built `dist/`:**
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/inject_analytics.py" \
    --from-inventory .claude/analytics-inventory.json --webroot <dir>
  ```
  (writes `*.pre-ga.bak`, idempotent). For a single file use `--file <path> --id G-XXX`.
  **Multi-site inventory (≥2 Measurement IDs):** the bare `--from-inventory` form exits
  `INVENTORY_AMBIGUOUS` by design — loop per site instead, passing that site's ID explicitly:
  `--webroot <that-site's-dir> --id <its G-XXX>`.
- **Framework source (Next/Nuxt/Astro/Svelte):** follow `analytics-setup` STEP 3's per-framework
  mechanics, but wire the GA4 tag DIRECTLY with the `G-` Measurement ID from the inventory
  (e.g. `@next/third-parties` `<GoogleAnalytics gaId>` in `app/layout`, Nuxt config, shared
  layout) and SKIP the engine's GTM-container branch — this flow provisions only a `G-` ID,
  never a `GTM-` container. Add Consent Mode v2 default-deny and the blanket `ui_click`
  listener per the engine's contract. Edit SOURCE so the tag survives deploys.

## STEP 5 — Verify (browser-free)

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_hit.py" \
  --from-inventory .claude/analytics-inventory.json --origin <origin>
```
`VERIFIED` = a real event reached GA4 realtime. The verdict is written back to the inventory
(`last_verify` per origin) — that record is what `--audit` reports later. If a browser
(Playwright / Chrome DevTools MCP) IS available you may additionally capture a `g/collect`
request for a screenshot, but the browser-free check is sufficient and is the default so the
flow works in headless/any project.

## STEP 6 — Record & commit

1. Confirm `.claude/analytics-inventory.json` holds Measurement ID + `last_verify` status per
   origin.
2. Commit the SOURCE tag change (the injection / framework edit). The provisioning + inventory
   are reproducible; the committed tag is what makes tracking permanent.
3. Report: per-origin Measurement ID, injection mode (source vs TEMP server-side), verify verdict.

## `--audit` mode

Read-only: report which origins have a Measurement ID in the inventory, whether the tag is in
committed source, and the recorded `last_verify` verdict per origin — no provisioning or
injection. Caveat: the audit reads LOCAL state only — it cannot see a property deleted or
reconfigured server-side in the GA console; re-run STEP 5 when live confirmation matters.

## Hard rules (inherit analytics-setup)

- One GA4 property PER site; never reuse a Measurement ID — Why: cross-site reuse corrupts both
  sites' data irreversibly.
- Consent Mode v2 configured before tags fire (default-deny; jurisdiction override per region) —
  Why: firing tags pre-consent is a GDPR/DPDP compliance defect, not a cosmetic one.
- Fire explicit events for CTAs/affiliate links; blanket `ui_click` is the floor, not the
  ceiling — Why: enhanced measurement cannot distinguish revenue-bearing clicks.
- "Done" requires a VERIFIED real hit + recorded ID + committed source tag — never
  snippet-presence — Why: a snippet that never sends a hit ships the site blind while looking
  instrumented.
- The SA key is the ONLY irreducible human step (Google blocks automation login); everything else
  is autonomous — Why: asking the owner for anything else is over-ask; guessing the key path is
  under-ask.
