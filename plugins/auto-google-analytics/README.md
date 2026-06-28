# auto-google-analytics

**Autonomous Google Analytics 4 for any project.** Install it, enable it, run `/auto-google-analytics`, and
the plugin instruments the project end-to-end with **zero hand-holding** — detect → provision →
inject → verify → record — and only ever needs one human action, once.

## What it does (`/auto-google-analytics`)

1. **Detect** the stack (Next / Nuxt / Vue / Astro / SvelteKit / static / non-web) and hosting type.
2. **Provision** a GA4 property + web data stream via a Google **service-account key** (no browser
   login) → a Measurement ID. Idempotent; one property per site.
3. **Inject** the gtag + **Consent Mode v2** + blanket `ui_click` snippet into **source** (static
   HTML via the bundled injector; framework source via the bundled `analytics-setup` engine).
4. **Verify** — browser-free — that a real hit reaches GA4 (Measurement Protocol test event +
   GA4 realtime poll). No Playwright/Chrome required.
5. **Record** the Measurement ID + status in `.claude/analytics-inventory.json` and commit the
   source tag so tracking survives deploys.

"Done" means a **verified real hit** + a recorded ID + a **committed source tag** — never just
"the snippet is on the page."

## The one human prerequisite (once per Google account)

Google blocks automation-browser login, so a service account must be created **once** by a human:

1. In Google Cloud, create a service account and download its JSON key.
2. Grant it the `analytics.edit` scope and **Administrator at the GA *account* level** (GA Admin →
   Account Access Management).
3. Enable the two Google APIs once in that GCP project (provisioning + browser-free verification):
   ```
   gcloud services enable analyticsadmin.googleapis.com analyticsdata.googleapis.com --project=<your-project>
   ```
4. Make the key discoverable. Either set `sa_key_path` in `auto-google-analytics-settings.json`
   (or the `GA_PROVISION_SA_KEY` env var) per project — **or**, for a shared multi-project setup,
   put `GA_PROVISION_SA_KEY=<path>` (and optionally `GA_PROVISION_SA_EMAIL` / `GA_PROVISION_TZ` /
   `GA_PROVISION_CURRENCY`) once in a **GLOBAL.env** above your repos: the plugin walks up from the
   project, finds it, and reads those vars automatically, so every project under the same account
   is zero-config. Never commit the key.

The scripts auto-handle the GA4 **User Data Collection Acknowledgement** (required before a
property can collect data / mint Measurement-Protocol secrets) — no manual GA-UI step needed.

After that, **every project under that Google account is zero-touch.** Without a key, the skill
falls back to **guided manual** setup (you paste Measurement IDs); it never fabricates IDs.

## Requirements

- `python` 3.8+. Token minting prefers the `google-auth` library
  (`pip install google-auth`); if absent it falls back to the `gcloud` CLI (`gcloud_path` setting).
- `gh`/network only for the optional commit step — provisioning + verification use the Google APIs
  directly via stdlib `urllib`.

## Settings (`auto-google-analytics-settings.json`)

Copy `auto-google-analytics-settings.default.json` to `<project>/.claude/auto-google-analytics-settings.json`
(or `~/.claude/` for a global default). Re-read every session — no reinstall. A pre-set env var
always wins.

| Key | Effect |
|---|---|
| `enabled` | Master switch. `false` silences the reminder and the autopilot. |
| `web_analytics_reminder` | SessionStart nudge when a web project has no analytics yet. |
| `sa_key_path` | Path to the service-account JSON key (the one prerequisite). |
| `time_zone` / `currency` | Defaults for new GA4 properties. |
| `gcloud_path` | Optional gcloud path for token minting when `google-auth` is absent. |

## Components

- `skills/auto-google-analytics/` — the autonomous orchestrator.
- `skills/analytics-setup/` — the bundled instrumentation engine (framework detail, consent/event
  contract). Self-contained; works with no other hub files.
- `rules/web-analytics-instrumentation.md` — the "every web project must have GA4" mandate. There
  is no plugin-native rule loading yet (issue #187), so **copy this into your project's
  `.claude/rules/` if you want it auto-loaded** as a salience layer; the skill enforces the same
  hard rules regardless.
- `scripts/provision_ga4.py` · `scripts/inject_analytics.py` · `scripts/verify_hit.py` — the
  portable provisioning, injection, and browser-free verification tools.
- `hooks/web-analytics-reminder.sh` — the SessionStart nudge (advisory, fail-safe, off-switchable).

## Off switches

`enabled: false` in settings, or env `AUTO_GOOGLE_ANALYTICS_DISABLE=1`; silence only the nudge with
`AUTO_GOOGLE_ANALYTICS_REMINDER_DISABLE=1`.
