---
name: analytics-setup
description: >
  Set up Google Analytics 4 (one property per site) via GTM, add explicit GA4
  events for CTAs and affiliate links, configure Consent Mode v2, verify
  per-domain Search Console, and VERIFY a real hit reaches GA before marking
  done. Use when setting up or auditing web analytics, adding GA4/GTM tracking,
  instrumenting CTA/affiliate conversions, or when a site is shipping without
  measurement. For web visitor/marketing measurement ONLY — not application or
  infra observability (metrics, logs, traces, uptime/error alerting), which is
  /monitoring-setup.
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[site-url-or-path] [--ga G-XXXXXXXXXX] [--gtm GTM-XXXXXXX]"
version: "1.1.0"
type: workflow
triggers:
  - analytics setup
  - google analytics
  - ga4 setup
  - gtm setup
  - tag manager
  - conversion tracking
  - affiliate tracking
---

# Analytics Setup (GA4 + GTM + Search Console)

Install and VERIFY web analytics so the site is never shipped blind. The bar is
a captured network hit to `google-analytics.com/g/collect` (or a GA Realtime
entry) — not "the snippet is on the page."

NEVER mark this skill done without a verified hit. ALWAYS use one GA4 property
PER SITE. ALWAYS fire explicit events for CTAs/affiliate links — enhanced
measurement does not distinguish them.

**Known limitation (client-side GA4/GTM):** ad-blockers drop 15–50% of hits,
heavier for tech/finance audiences. If that loss becomes material, the optional
mitigation is **server-side GTM** (a GCP Cloud Run container on a first-party
subdomain) — added infrastructure, out of scope for the default client-side setup.

**Request:** $ARGUMENTS

---

## STEP 1: Detect the Stack and Injection Strategy

Identify the project so the injection method is correct:

1. Look for framework markers:
   - `next.config.*` / `app/` or `pages/` directory → **Next.js / React**
   - `nuxt.config.*` → **Nuxt**; `vue` + `vite.config.*` → **Vue SPA**
   - `astro.config.*` → **Astro**; `svelte.config.*` → **SvelteKit**
   - bare `index.html` with no build tool → **pure-static HTML**
   - **Non-web** — `pubspec.yaml` (Flutter), `android/` Gradle, RN/Expo, or an
     `electron`/desktop app → this web GTM path does NOT apply; follow
     `references/cross-platform.md` (Firebase Analytics for mobile, GA4
     Measurement Protocol for desktop — same GA4 backend) and skip to its steps.
2. Decide the loader:
   - Default to **GTM** (a `GTM-XXXXXXX` container) for every framework and for
     static sites that can edit a shared layout/`<head>`.
   - Use the **`gtag.js` direct snippet as a FALLBACK ONLY** for a pure-static
     site where maintaining a GTM container is impractical.
3. Check for an existing install (avoid double-tagging): grep the repo for
   `googletagmanager.com/gtm.js`, `gtag(`, `G-`, and `GTM-`. If GA4/GTM is
   already present, switch to **audit mode** — confirm the property is
   one-per-site, events fire, consent is wired, then jump to STEP 6 (verify).

**Already-deployed site, no source rebuild available?** A "dynamic" app is NOT a
barrier to analytics — only your *method* is. When you can't (or won't) rebuild
from source, inject server-side WITHOUT touching the app:
- **Static webroot** (`root /var/www/X`): edit the live `index.html` directly
  (backup first). A Next.js **static export** (`*.html` per route) needs the
  snippet in EVERY route HTML, not just `index.html`, or deep-link landings miss.
- **Dynamic/proxied app** (`proxy_pass http://127.0.0.1:PORT`): inject at nginx
  with **`sub_filter`** — host the GA logic as a static `.js` file and add
  `sub_filter '</head>' '<script src="/ga/x.js"></script></head>'` plus
  `proxy_set_header Accept-Encoding ""` (so upstream HTML is uncompressed, else
  sub_filter no-ops) to the proxy `location`; **`nginx -t` before reload** (shared
  host). Edge injection (Cloudflare Workers) is the same idea one layer out.
- These server-side edits are **non-durable** — lost on the next source redeploy.
  Also update the SOURCE for persistence; if both are present, remove one to avoid
  double-tagging. SMOKE-TEST OVER HTTPS (`:80` redirects), and verify a real hit.

State the detected stack and chosen loader before editing anything.

## STEP 2: Confirm the GA4 Property + Measurement ID

Each site needs its OWN GA4 property and measurement ID.

1. If `--ga`/`--gtm` were passed, use those IDs.
2. Otherwise look for IDs already recorded in the project/owner analytics
   inventory or env (`NEXT_PUBLIC_GA_ID`, `GTM_ID`, etc.).
3. If still unknown: **GA4 property creation requires the owner's Google
   account.** Without a GA Admin API / MCP integration, you cannot create the
   property yourself — STOP and instruct the human:
   > "Create a GA4 property for THIS site at https://analytics.google.com
   > (Admin → Create Property → add a Web data stream for the domain), create a
   > GTM container at https://tagmanager.google.com, and paste the `G-…`
   > measurement ID and the `GTM-…` container ID here."
4. Record both IDs as variables for the steps below. MUST NOT reuse another
   site's property — one property per site (see `web-analytics-instrumentation`).

## STEP 3: Inject the GTM Container (head + body)

GTM needs BOTH a `<head>` script and a `<body>` `<noscript>` iframe. Replace
`GTM-XXXXXXX` with the real container ID.

**Head snippet** (as high in `<head>` as possible):

```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->
```

**Body snippet** (immediately after the opening `<body>`):

```html
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
```

Per-framework injection:

- **Next.js (App Router) — preferred:** use `@next/third-parties`:
  ```tsx
  // app/layout.tsx
  import { GoogleTagManager } from '@next/third-parties/google'
  export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
      <html lang="en">
        <GoogleTagManager gtmId="GTM-XXXXXXX" />
        <body>{children}</body>
      </html>
    )
  }
  ```
  If `@next/third-parties` is unavailable, inject the raw head snippet via
  `next/script` with `strategy="afterInteractive"` and the `<noscript>` in `body`.
- **Vue / Nuxt:** Nuxt → add the head script in `nuxt.config.ts` `app.head.script`
  and the `<noscript>` in `app.vue`. Vue SPA → put both snippets in the root
  `index.html` (`<head>` and top of `<body>`).
- **Astro / SvelteKit:** put the head snippet in the shared layout's `<head>`
  and the `<noscript>` at the top of the layout `<body>`.
- **Pure-static HTML:** paste both snippets directly; if no GTM container,
  fall back to the `gtag.js` direct snippet for `G-XXXXXXXXXX`:
  ```html
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
  gtag('js',new Date());gtag('config','G-XXXXXXXXXX');</script>
  ```

Inside GTM, add a **GA4 Configuration tag** bound to the measurement ID firing
on All Pages, and enable **enhanced measurement** on the GA4 data stream
(pageviews + outbound clicks come free — do NOT hand-roll them).

## STEP 4: Wire Explicit CTA & Affiliate Events

Enhanced measurement does NOT distinguish affiliate conversions — fire named
events. Push to `dataLayer` (GTM path) or call `gtag` directly (gtag fallback).

For a Zerodha open-account button (`c=ZMPHZC`) and an AngelOne button:

```html
<a href="https://zerodha.com/open-account?c=ZMPHZC"
   onclick="dataLayer.push({event:'cta_click',cta_type:'affiliate',
   partner:'zerodha',ref_code:'ZMPHZC',placement:'hero'});">
  Open a Zerodha account
</a>

<a href="https://angelone.in/signup?..."
   onclick="dataLayer.push({event:'cta_click',cta_type:'affiliate',
   partner:'angelone',placement:'sidebar'});">
  Open an AngelOne account
</a>
```

In GTM: create a **Custom Event trigger** on `cta_click` and a **GA4 Event tag**
(event name `cta_click`) mapping `partner`, `ref_code`, `placement` to event
parameters. For the gtag fallback, replace the `dataLayer.push` with
`gtag('event','cta_click',{cta_type:'affiliate',partner:'zerodha',ref_code:'ZMPHZC',placement:'hero'})`.

**Affiliate scope (be honest):** GA4 captures the affiliate **click** only. The
actual **conversion** (account opened/funded) lives in the affiliate partner's
dashboard (Zerodha `c=ZMPHZC`, AngelOne) — reconcile clicks → conversions there.
Do NOT report GA4 as measuring funded accounts unless the partner provides a
server-to-server postback (most retail broker programs do not).

In React/Vue, attach the same payload in the click handler rather than inline
`onclick`. **CSP caveat:** inline `onclick` is blocked by any `script-src` CSP
without `'unsafe-inline'` — if the site ships a CSP (it should), bind the handler
in JS (`addEventListener`) instead of the inline attribute shown above. Every
revenue-bearing CTA on the site gets one — sweep the codebase for affiliate
links and instrument each.

## STEP 4b: Blanket Interaction Tracking (OPT-IN — "every button & link")

STEP 4 covers the revenue-bearing CTAs explicitly. When the owner wants to know
**which of ALL buttons/links visitors click** (not just CTAs), add blanket
interaction tracking. This is **opt-in** — it is noisier than explicit events, so
enable it only when broad interaction insight is wanted, and keep STEP 4's named
events for anything revenue-bearing (you want clean, intent-named events there).

Two interchangeable mechanisms — pick ONE per site:

**A. GTM "All Elements" click trigger (no per-element code — preferred for GTM sites).**
In GTM: create a **Click trigger → All Elements**, then a single **GA4 Event tag**
(event name `ui_click`) firing on it, mapping GTM's built-in click variables to
parameters: `link_text → {{Click Text}}`, `link_url → {{Click URL}}`,
`element_id → {{Click ID}}`, `element_classes → {{Click Classes}}`. One tag now
records every click site-wide. Enable the **Clicks → All Elements** built-in
variables first (Variables → Configure). Refine later with a trigger condition
(e.g. only `Click Element matches CSS a, button, [role="button"]`) to drop noise.

**B. Data-attribute + delegated listener (for gtag-fallback / code-controlled SPAs).**
Annotate elements declaratively and capture with ONE delegated listener — no
per-button wiring, CSP-safe (bound in JS, not inline):

```html
<button data-track="signup" data-section="hero">Sign Up</button>
<a href="/pricing" data-track="nav_pricing">Pricing</a>
```

```js
// one listener for the whole document — survives SPA re-renders
document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-track], a, button, [role="button"]');
  if (!el) return;
  const payload = {
    event: 'ui_click',
    interaction_id: el.dataset.track || null,        // explicit name when annotated
    link_text: (el.textContent || '').trim().slice(0, 100),
    link_url: el.getAttribute('href') || null,
    element_id: el.id || null,
    page_section: el.dataset.section || null,
  };
  // GTM path → dataLayer; gtag fallback → gtag('event','ui_click',payload)
  (window.dataLayer = window.dataLayer || []).push(payload);
}, { capture: true });
```

For SPAs, also push a `page_view` on every client route change (client navigations
do not reload the page, so GA4 enhanced measurement misses them) — wire it into the
router's after-each hook.

**Standard event schema (keep consistent across ALL sites — snake_case):**
`event: ui_click` · `interaction_id` · `link_text` · `link_url` · `element_id` ·
`page_section`. Verify a blanket click the same way as STEP 6 (assert an
`en=ui_click` collect request fires on an ordinary button). Do NOT also hand-roll
ordinary outbound-link tracking — GA4 enhanced measurement already covers outbound
links and downloads; `ui_click` is for the INTERNAL buttons/links it misses.

**Owner-readable labels (plain simple English — NOT codes).** Everything an owner
SEES in GA reports must read as plain English. GA4 forces event *names* to be
`snake_case` (a Google constraint), so keep the name technical-but-clear
(`ui_click`) and put the human-readable label in a *parameter value*: prefer the
element's **visible text** (`link_text`), and when annotating with `data-track`,
use a plain-English value (`data-track="Open a Zerodha account"`, not
`data-track="cta_zmphzc"`). Also register the surfaced parameters as GA4 **custom
dimensions with friendly display names** ("Button label", "Link destination") so
the report columns read in plain English too. The GA4 **property displayName** is
free-form — name it the way the owner thinks of the site ("Real Fuel Prices
India"), never a slug.

## STEP 5: Configure Google Consent Mode v2 Defaults

Set Consent Mode defaults BEFORE GTM/GA tags fire (place above the GTM head
snippet, or as a Consent Initialization tag in GTM). India DPDP-aware,
non-blocking for info/lead-gen sites:

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('consent','default',{
    ad_storage:'denied', ad_user_data:'denied', ad_personalization:'denied',
    analytics_storage:'denied', wait_for_update:500
  });
</script>
```

**Default `analytics_storage:'denied'`** (privacy-correct): Consent Mode v2's
cookieless **modeling** still preserves basic, aggregate measurement while no
cookie is set, so you do NOT lose visibility by denying-by-default. Call
`gtag('consent','update',{analytics_storage:'granted'})` when the user accepts.
Flipping the default to `'granted'` is a **per-jurisdiction judgment the owner
must confirm** (e.g. an info/lead-gen site under a permissive reading) — do NOT
bake `granted`-by-default silently. IP handling stays on GA4 defaults — add no
bespoke IP logging.

## STEP 6: VERIFY a Real Hit (do NOT skip)

Verification is the point of this skill. Drive the running site and confirm a
collect request actually fires. **This step needs browser automation** — the
Playwright or Chrome DevTools MCP tools if available in the environment, else
dispatch the project's browser skill (`/playwright` or `/verify-screenshots`)
via `Skill`. If no browser automation is reachable, STOP and report
`VERIFY_BLOCKED: no browser tooling` rather than declaring done on inspection.

1. Start/serve the site (self-heal: start the dev server if down).
2. Open a page in a **clean, ad-blocker-free browser profile** (a blocker in the
   test profile produces a false negative — the install is fine, the *test* is
   wrong). Record network requests.
3. Navigate, then click a CTA from STEP 4.
4. Assert a request hit `https://www.google-analytics.com/g/collect` (or
   `region1.google-analytics.com/g/collect`) — and that a `cta_click` collect
   request fired on the CTA. Inspect the query string for `en=cta_click` /
   `en=page_view` to confirm the event name. For SPA/App-Router targets, also
   trigger a client-side route change and assert a fresh `page_view` collect
   fires (client navigations don't reload the page).
5. Cross-check GA **Realtime** shows the visit/event if account access exists.
6. If NO collect request appears, FIRST distinguish the two causes before acting:
   - **Test wrong (false negative):** an ad-blocker/privacy extension or denied
     `analytics_storage` in the test profile → re-run in a clean profile / with
     consent granted; the install may be fine.
   - **Install broken (real):** container not published, wrong ID, snippet absent
     → diagnose root cause and fix; re-run until a hit lands.

Write a short evidence note (the captured collect URL or a Realtime screenshot).
A green page-load with no collect request is a FAIL, not a pass.

## STEP 7: Record in the Analytics Inventory

Record, in the project/owner analytics inventory (in Abhay's setup this is
`GLOBAL-CONTEXT.md` Section 4 — reference it generically as the project/owner
analytics inventory, do not hardcode a path):

- Site domain/URL
- GA4 measurement ID (`G-…`) and GTM container ID (`GTM-…`)
- Search Console verification status for the domain
- Verification status: VERIFIED (with the captured hit) or BLOCKED (why)

Also verify the domain in **Google Search Console** (DNS TXT, or the GTM/GA
verification method) and note it. The inventory is how every future session
learns the site is measured — an unrecorded ID is a future re-discovery cost.

**Portfolio view (many sites):** one-GA4-property-per-site gives no native
cross-site rollup. For a unified view across a portfolio, enable GA4 **BigQuery
export** (free tier) on each property and build one **Looker Studio** dashboard
over the combined datasets.

---

## CRITICAL RULES

### MUST DO
- MUST use one GA4 property PER SITE with its own measurement ID — Why: shared properties cross-contaminate per-site reporting and attribution
- MUST install via GTM; `gtag.js` direct only as a pure-static fallback — Why: a container is the single managed place for tags, triggers, and consent
- MUST fire explicit, parameterized GA4 events for every CTA and affiliate link (Zerodha `c=ZMPHZC`, AngelOne) — Why: enhanced measurement cannot distinguish the conversions the site exists for
- MUST configure Consent Mode v2 defaults before tags fire; keep non-blocking for info/lead-gen — Why: respects user choice without losing basic measurement
- MUST verify a real hit to `google-analytics.com/g/collect` (or GA Realtime) before done — Why: a rendered snippet that never reaches GA is a silent failure
- MUST verify per-domain Search Console and record the IDs + status in the analytics inventory — Why: unrecorded measurement is re-discovered at cost every session

### MUST NOT DO
- MUST NOT funnel multiple unrelated sites into one GA4 property as separate streams — Why: breaks per-site retention and attribution
- MUST NOT hand-roll pageview or ordinary outbound-click listeners — Why: GA4 enhanced measurement already captures them; duplicates double-count
- MUST NOT mark analytics complete on "the snippet is on the page" — Why: that is shape, not the verified collect hit this skill requires
- MUST NOT invent or reuse a measurement ID — Why: GA4 property creation needs the owner's Google account; ask for the real `G-…` / `GTM-…`
- MUST NOT add bespoke IP logging alongside GA4 — Why: GA4 defaults already handle IPs; extra logging is a privacy liability
