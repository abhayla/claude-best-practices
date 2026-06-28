---
name: auto-analytics
description: >
  Autonomously instrument THIS project with Google Analytics 4 end-to-end — detect stack &
  hosting type, provision the GA4 property + web stream (service-account, no browser login),
  inject the gtag + Consent Mode v2 + blanket ui_click snippet into source, verify a real hit
  reaches GA4 browser-free, and record the IDs in a project-local inventory. Use when setting
  up or auditing web analytics on a project that has the auto-analytics plugin installed, or
  when a site is shipping with no measurement. The one-time service-account key is the only
  human prerequisite; without it the skill falls back to guided manual setup.
type: workflow
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[--audit] [--site \"Name=https://origin\"]"
version: "1.0.0"
triggers:
  - auto analytics
  - set up analytics
  - instrument analytics
  - add ga4
---

# auto-analytics — zero-touch GA4 for any project

The autonomous orchestrator. It wraps the bundled **analytics-setup** engine (the instrumentation
SSOT — read `skills/analytics-setup/SKILL.md` for per-framework detail and the consent/event
contract) and the three bundled scripts under `${CLAUDE_PLUGIN_ROOT}/scripts/`:
`provision_ga4.py` (create property → Measurement ID), `inject_analytics.py` (static HTML
injection), `verify_hit.py` (browser-free hit verification).

**Definition of done:** a real hit is verified in GA4 realtime AND the Measurement ID is recorded
in `.claude/analytics-inventory.json` AND the tag lives in committed source (not only a transient
server-side injection). Snippet-on-page is NOT done.

## STEP 0 — Preflight (settings + credential)

1. The hooks export settings from `auto-analytics-settings.json` (see `_settings.sh`). If
   `enabled` is false, stop: "auto-analytics disabled in settings."
2. Locate the service-account key: `GA_PROVISION_SA_KEY` env (set from settings `sa_key_path`).
   - **Present** → fully autonomous path (STEP 1+).
   - **Absent** → GUIDED-MANUAL fallback: print the one-time setup from the README ("create a
     service account with `analytics.edit`, grant it Administrator at the GA account level,
     save the key, set `sa_key_path`"). Then either accept owner-supplied Measurement IDs and
     skip to STEP 3, or stop with `SETUP_REQUIRED`. Never fabricate IDs.

## STEP 1 — Detect stack & hosting type

Delegate detection to the bundled engine: `Skill("/analytics-setup")` STEP 1, or inline —
identify framework (Next/Nuxt/Vue/Astro/SvelteKit/static/non-web) and hosting (static webroot,
built `dist/`, dynamic/proxied, edge). For **non-web** (mobile/desktop) route to
`skills/analytics-setup/references/cross-platform.md` and stop the web flow.

## STEP 2 — Resolve the site origin

Use `--site "Display Name=https://origin"` if given; else derive: the production origin from the
project's deploy config / README / package homepage. One GA4 property per site — never reuse a
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
- **Framework source (Next/Nuxt/Astro/Svelte):** follow `analytics-setup` STEP 3 for that
  framework (e.g. `@next/third-parties` `<GoogleAnalytics>` in `app/layout`, Nuxt config, shared
  layout) with the Measurement ID from the inventory, plus Consent Mode v2 default-deny and the
  blanket `ui_click` listener. Edit SOURCE so the tag survives deploys.

## STEP 5 — Verify (browser-free)

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_hit.py" \
  --from-inventory .claude/analytics-inventory.json --origin <origin>
```
`VERIFIED` = a real event reached GA4 realtime. If a browser (Playwright / Chrome DevTools MCP)
IS available you may additionally capture a `g/collect` request for a screenshot, but the
browser-free check is sufficient and is the default so the flow works in headless/any project.

## STEP 6 — Record & commit

1. Confirm `.claude/analytics-inventory.json` holds Measurement ID + status per origin.
2. Commit the SOURCE tag change (the injection / framework edit). The provisioning + inventory
   are reproducible; the committed tag is what makes tracking permanent.
3. Report: per-origin Measurement ID, injection mode (source vs TEMP server-side), verify verdict.

## `--audit` mode

Read-only: report which origins have a Measurement ID in the inventory, whether the tag is in
committed source, and the last verify verdict — no provisioning or injection.

## Hard rules (inherit analytics-setup)

- One GA4 property PER site; never reuse a Measurement ID.
- Consent Mode v2 configured before tags fire (default-deny; jurisdiction override per region).
- Fire explicit events for CTAs/affiliate links; blanket `ui_click` is the floor, not the ceiling.
- "Done" requires a VERIFIED real hit + recorded ID + committed source tag — never snippet-presence.
- The SA key is the ONLY irreducible human step (Google blocks automation login); everything else
  is autonomous.
