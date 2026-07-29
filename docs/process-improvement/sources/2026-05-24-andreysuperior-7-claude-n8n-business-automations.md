# Superior (@andreysuperior) — "Built 7 automations with Claude. They run the business while I sleep. Full breakdown."

- **Source:** https://x.com/andreysuperior/status/2058539604391735714 (X-native article, id 2058517001165795329)
- **Captured:** 2026-07-29 (delivered via `/remote-control CBP-Fable-291`; fetched via ADHX + fxtwitter; images OCR'd)
- **Author:** Superior (@andreysuperior), ~9.0k followers
- **Published:** 2026-05-24 (article last modified 2026-07-15)
- **Engagement at capture:** ~300k views · 225 likes · 40 RTs · 786 bookmarks · 15 replies

## One-line thesis

A 10-person ops team's judgment-free repetitive work (scheduling, follow-ups, reporting,
support, invoicing, lead qualification, data entry) replaced by **7 n8n workflows with Claude
as the reasoning node** — claimed ~$15k/month labor saved for <$200/month in tools.

⚠️ **Number check (re-derived at capture):** the article's own per-workflow breakdown image
totals **$12,332/month** (1,562+2,083+1,302+1,042+1,500+833+4,010), NOT the headline
$15,000/month. The headline is rounded-up marketing. All savings/run-count figures are the
author's unverified claims — do not propagate as fact.

## Stack

Claude API (the "AI brain": read, think, decide, write) + n8n (trigger/connect: "like Zapier
but more powerful, free self-hosted, no execution limits") + Zapier · Stripe · Airtable ·
HubSpot · Gmail · Slack · Typeform. Loop model (from infographic): TRIGGER (event fires) →
PROCESS (Claude thinks) → ACTION (task done), claimed 3-sec trigger-to-action, ~3,333
runs/month across all 7, "0% human involvement once activated".

## The 7 workflows (claimed savings + run volume from breakdown image)

| # | Workflow | What it does | Claimed saving | Claimed runs/mo |
|---|---|---|---|---|
| 1 | Lead Qualification & Follow-up | Form → webhook → Claude scores 1–10, IDs pain point/budget, writes personalized reply → CRM updated (HubSpot/Airtable) → reply sent from own domain in 60s (Gmail) → score ≥8 pings sales on Slack | $1,562/mo | 847 |
| 2 | Customer Support Automation | Handles ~80% of tickets (variations of the same 20 questions) automatically; escalates the rest with context | $2,083/mo | 1,240 |
| 3 | Invoice & Payment Automation | Creates invoices; 3-sequence follow-up for overdue accounts (Stripe) | $1,302/mo | 312 |
| 4 | Automated Weekly Reporting | Pulls 8 data sources, writes analysis + recommendations, ready Monday 8am | $1,042/mo | 52 |
| 5 | Content Repurposing Machine | 1 blog post → LinkedIn, Twitter thread, newsletter, Instagram, YouTube script (6 formats in ~3 min) | $1,500/mo | 620 |
| 6 | Competitor Intelligence | Tracks 5 competitors (site/blog/LinkedIn/job posts), weekly report, immediate alert on major changes | $833/mo | 168 |
| 7 | Meeting Prep & Follow-up | Brief before every meeting; action items + CRM update after; 100% of meetings | $4,010/mo | 94 |

(The per-workflow "How it works" / "The Claude prompt" bodies are image-only in the source;
only Workflow 1's step card was published in full — transcribed above. The prompts themselves
are NOT in the article text.)

## Speed-comparison card (human team vs Claude+n8n, author's claims)

Lead follow-up 3–6h → 60s · support reply 24–48h → instant 24/7 · weekly report Mon 11am
(3–4h work) → Mon 8am (zero human time) · invoicing 2.5h/day → automatic · meeting follow-ups
40% sent → 100% within 5 min · content repurposing 4h/post → 6 formats in 3 min. Claimed
payback: break-even week 3, "$200 vs $15,000/month".

## Advice sections (the transferable part)

- **Start with Workflow 1** (lead qualification): easiest build, most visible impact; working
  demo in ~2 hours; sell it before building the rest ("build without a client" is mistake 6).
- **Sell as a service:** "How many hours/week does your team spend on [process]? At their
  hourly rate that's $X/mo. Setup $Y, maintain $Z/mo. Payback: N weeks." Per-workflow
  productization.
- **6 mistakes to avoid:** (1) starting with the most complex workflow; (2) **no failure path —
  add a Slack error notification to every workflow, "silent failures kill trust"**; (3) using
  Claude for everything — **only where judgment/writing is required, simpler logic for data
  transformation**; (4) not testing edge cases — 20 different inputs before activating;
  (5) **automating a broken process — fix and map the process first**; (6) building without a
  client.

## Relevance to this hub — LOW-MODERATE

- **No new mechanism.** n8n-orchestrated business automation is outside the hub's Claude Code
  pattern surface; the hub's Notifier gateway + loop doctrine already cover the equivalents.
- **Independent corroboration of three existing hub rules:** (a) mistake 2 = the hub's
  fail-open-but-alert / no-silent-failure doctrine (`check_fleet_script_health.py`'s
  detect-then-discard class); (b) mistake 3 = `model-routing.md` cheapest-sufficient (LLM only
  where judgment is needed, deterministic logic elsewhere); (c) mistake 5 = process-before-
  automation (map first, then automate).
- **Capture-side lesson (meta):** the headline/itemized mismatch ($15k vs $12,332) is a live
  example of why carried-through numbers get re-derived (Operating Manual re-derivation rule).
- **Possible business-side reuse (outside hub scope):** workflows 1 (lead qualification +
  60-sec reply) and 7 (meeting prep/follow-up) rhyme with the PIFS Wati 24h-window follow-up
  engine already in progress — same trigger→judge→personalize→alert shape, via the Notifier
  gateway rather than n8n.

## Media on disk

- `img/andreysuperior-7-workflows-cover.jpg` (cover: "7 workflows. $15,000/month. Business runs alone." — $15k/mo · 7 workflows · $0 coding · 24/7 tiles; stack line "Claude API · n8n · Zapier · Stripe · Airtable")
- `img/andreysuperior-7-workflows-savings-breakdown.jpg` (per-workflow savings/run table; totals $12,332/month)
- Not saved (transcribed above): automation-loop infographic, workflow-1 step card, ROI/payback chart, human-vs-AI speed table.
