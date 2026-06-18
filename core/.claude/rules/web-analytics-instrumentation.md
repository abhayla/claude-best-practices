---
description: Web analytics instrumentation standard — every site ships GA4 (one property per site) via GTM, with verified CTA/affiliate events and Search Console.
globs: ["**/*.html", "**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.astro", "**/*.svelte", "**/app/**", "**/pages/**"]
---

# Web Analytics Instrumentation

Every public website or web app MUST ship analytics by default — not as a
follow-up task. A site with no measurement is shipped blind: you cannot tell
whether anyone arrives, what they do, or which call-to-action converts. This
rule is the standard; the setup procedure is the analytics-setup skill (only
ever referenced inside a fenced block below, never inline).

## The Standard

- **GA4, one property PER SITE.** Each distinct domain/app gets its own GA4
  property and its own measurement ID (`G-XXXXXXXXXX`). MUST NOT funnel
  multiple unrelated sites into one property as separate data streams — that
  cross-contaminates reporting and breaks per-site retention/attribution.
- **Install via Google Tag Manager (GTM).** Load GA4 through a GTM container
  (`GTM-XXXXXXX`), not a hand-maintained tag soup. The container is the one
  place tags, triggers, and consent wiring are managed.
- **`gtag.js` direct snippet is a FALLBACK ONLY** for pure-static sites where a
  GTM container is impractical. When GTM is available, use GTM.
- **Google Search Console verified per domain.** Each production domain MUST be
  a verified Search Console property (DNS TXT or the GTM/GA verification method)
  so indexing, coverage, and search-query data are captured.

## Required Measurement

- **Pageviews / visitors** via GA4 **enhanced measurement** (page_view,
  scrolls, site search) — enabled on the data stream.
- **Outbound link clicks** captured automatically by GA4 enhanced measurement —
  do NOT hand-roll a click listener for ordinary outbound links.
- **EXPLICIT GA4 events for CTAs**, above all **affiliate links**, which
  enhanced measurement does not meaningfully distinguish. Every revenue-bearing
  CTA fires a named event with parameters identifying the partner and placement,
  e.g. a Zerodha open-account link (`c=ZMPHZC`) and an AngelOne link each emit a
  distinct `cta_click` / affiliate event. Affiliate conversions are the point of
  the site — they MUST be measured explicitly, not inferred.

## Consent & Privacy (India DPDP-aware)

- **Google Consent Mode v2 defaults MUST be configured** (`ad_storage`,
  `analytics_storage`, `ad_user_data`, `ad_personalization`) before tags fire.
- For informational / lead-generation sites, consent is configured but
  **non-blocking** — analytics may run under Consent Mode's default/denied
  modeling so basic measurement is never lost while still honoring user choice.
- **IP handling follows GA4 defaults** (GA4 does not store raw IPs) — do NOT add
  bespoke IP logging alongside it.

## Definition of DONE (all five — none optional)

A site's analytics is DONE only when:

1. GTM container is installed (head + body snippets present and loading).
2. The GA4 property is linked through the container with the site's measurement ID.
3. CTA / affiliate events fire on interaction (verified, not assumed).
4. **A real hit is VERIFIED** to reach GA — confirmed by an actual network
   request to `https://www.google-analytics.com/g/collect` (or the event
   appearing in GA Realtime). Mechanical "the snippet is on the page" is NOT
   verification; a captured collect request or Realtime entry is.
5. The measurement ID (and GTM container ID) is RECORDED in the project/owner
   analytics inventory.

MUST NOT mark analytics complete without a verified hit. A snippet that renders
but never reaches `google-analytics.com/g/collect` is the silent-failure mode
this rule exists to prevent.

## CRITICAL RULES

- MUST provision GA4 (one property per site) via a GTM container; `gtag.js`
  direct only as a pure-static fallback.
- MUST verify per-domain Google Search Console.
- MUST fire explicit, parameterized GA4 events for every CTA and affiliate link
  (Zerodha `c=ZMPHZC`, AngelOne, etc.) — never rely on enhanced measurement alone.
- MUST configure Google Consent Mode v2 defaults; keep non-blocking for
  info/lead-gen sites.
- MUST verify a real collect hit (network request or GA Realtime) AND record the
  measurement ID before declaring DONE — a rendered snippet is not proof.

To run the guided setup + verification:

```
/analytics-setup
```
