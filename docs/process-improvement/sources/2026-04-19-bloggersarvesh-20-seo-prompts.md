Source: https://x.com/bloggersarvesh/status/2045854745676697822
Captured: 2026-07-08

# bloggersarvesh — "Top 20 SEO Prompts that make your Claude 100x more powerful (full Stack)"

**Author:** Sarvesh ([@bloggersarvesh](https://x.com/bloggersarvesh)), owner of Alventra Marketing — a local-SEO agency for home-services businesses (plumbers, HVAC, lawyers, cleaners).
**Posted:** 2026-04-19 · **Engagement at capture:** 147 likes, 13 RTs, 2 replies, 694,566 views.
**Format:** Single long-form X-native article (~44k chars) — a numbered prompt library + a rollout schedule, ending in an agency-services CTA.
**Nature:** **Marketing prompt-pack, not a Claude Code / engineering pattern.** It targets `claude.ai` / Claude Cowork used as a browser-driving research assistant for **local SEO** (Google Business Profile, website content, backlinks, tracking) for home-services businesses. Contains an explicit soft-sell for the author's agency at the end. The headline **"100x more powerful"** and "90 days ... outrank businesses established for years" claims are **UNVERIFIED marketing copy** — no benchmark, before/after data, or methodology is shown, only anecdote ("I've watched it happen dozens of times").

---

## What it is

A library of 20 copy-paste prompts, each instructing Claude (via a browser-use / Cowork-style session) to open Chrome, navigate to Google Maps, a competitor's Google Business Profile (GBP), Google Search Console, SEMrush, or Ahrefs, scrape/extract data, and produce a spreadsheet-style competitive analysis plus a written deliverable (descriptions, page copy, outreach emails, posting calendars). It opens with a **"load once" business-context block** — a long fill-in-the-blank prompt (business basics, services, target keywords, current standings, competitors, past SEO attempts, and explicit output-format preferences) meant to be pasted once so Claude never has to re-ask for the same facts across sessions.

## The 20 prompts, by section

**Part 1 — Google Business Profile (prompts 1–8):** category audit (which secondary categories competitors have that you don't), attributes audit (tags like "veteran-owned," "24/7"), competitor review teardown (velocity, not just star rating), review-response strategy (templated replies per star rating that embed keywords), GBP posts strategy (competitor posting cadence → an 8-week content calendar), services-section optimization, GBP description rewrite (3 versions: keyword/conversion/trust-focused), photo audit + 8-week upload plan with geotagging guidance.

**Part 2 — Website (prompts 9–13):** keyword-gap audit (via SEMrush, filtered to local-intent volume/difficulty bands), "money page" audit (via Search Console: pages one push from page 1, title/CTR problems, cannibalization), service+city page builder (full on-page copy per service×city combination), Search Console "page-2 goldmine" 30-day optimization sprint (writes the actual title/H1/meta copy, not just instructions), review sentiment analysis (mines competitor reviews for the emotional language customers use, then rewrites the site's own copy in that language).

**Part 3 — Backlinks + authority (prompts 14–16):** competitor backlink audit via Ahrefs (finds link targets that back multiple competitors but not you, with ready-to-send outreach emails), local citation audit across ~15 directories (NAP consistency), local search-intent mapping (buckets keywords into a 4-stage buyer journey — problem-unaware → problem-aware → solution-aware → ready-to-hire — and routes each stage to a content type).

**Part 4 — Content + tracking (prompts 17–20):** content-gap analysis (SEMrush Content Gap tool → content briefs for top 20 gaps), "entity optimization" (LocalBusiness JSON-LD schema, Wikidata/Knowledge-Panel presence, entity-building outreach — flagged by the author as "most advanced" and least-adopted), competitor GBP posting-pattern forensic analysis (day/time/format patterns → a matching posting cadence), and a monthly SEO report template pulling GSC + GBP + GA4 into a one-page read.

**Rollout schedule:** a 12-week sequencing (load context → weeks 1–3 GBP → weeks 4–6 website → weeks 7–8 backlinks/citations → weeks 9–10 content/entity/posting patterns → weeks 11–12 reporting), explicitly framed as "don't run all 20 at once."

## Overall method / technique

Every prompt follows the same shape: **(1)** have Claude browse to a live source (own listing + 2–3 named competitors), **(2)** extract a defined column set into a comparison spreadsheet, **(3)** derive a prioritized gap list (what competitors share that you're missing = non-negotiable; what only one has = differentiation), **(4)** turn the gap list directly into finished deliverables (copy, calendars, outreach emails) rather than mere recommendations. The recurring technique worth naming: **competitor-differential extraction** — always three-way diffing against named competitors instead of asking Claude to "audit my SEO" in the abstract, which is generically the same "give the model comparison anchors and demand a finished artifact, not advice" prompting pattern that shows up across other captured practitioner content, just applied narrowly to local SEO/GBP data.

## Why this is logged

`docs/process-improvement/INBOX.md` policy is to log all externally-surfaced practitioner content for later triage, even when out of scope for this hub. This is a browser-driving marketing/content-ops prompt-pack for a non-technical, single-purpose vertical (local SEO for home-services businesses) — a use-case with no engineering-pattern surface (no code, no agent/skill/rule/hook mechanic, no verification technique).

---

## Relevance to this hub — LOW (logged for completeness, no hub action)

This hub is a Claude Code engineering-patterns factory (agents/skills/rules/hooks for software delivery pipelines). Nothing here maps to that surface:

| Prompt-pack element | Hub analogue? |
|---|---|
| One-time "business context" block pasted so Claude "never asks again" | Superficially resembles `CLAUDE.md` as a standing brief, but it's a single mega-prompt pasted per-chat, not a file-based, versioned, auto-loaded system — no transferable mechanic |
| 20 individual task prompts, each with a fixed procedure + output spec | Analogous in *shape* to a skill library, but each "prompt" is a one-off instruction string with no frontmatter, no trigger logic, no test/eval, no reuse across projects — not a skill in this hub's sense |
| Competitor-differential extraction (3-way diff → gap list → deliverable) | A generically sound prompting technique, but already implicit in how the hub's own workflows compare against baselines (e.g. `code-review`, `pattern-quality`) — nothing new to adopt |
| "100x more powerful" / "outrank in 90 days" claims | Unverified marketing; explicitly flagged, not something to act on |

**Verdict:** no hub action. This is a vertical-specific (local SEO) prompt library for a non-Claude-Code product surface, with unverified outcome claims. Logged for completeness per the capture-on-sight INBOX policy; no rule, skill, or pattern change follows from it.
