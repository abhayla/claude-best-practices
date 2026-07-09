Source: https://x.com/Durektor97/status/2073672096304058655
Captured: 2026-07-08

# Durektor97 — "Agencies Charge $10,000 for This. Claude Does It in an Afternoon"

**Author:** Durektor97 ([@Durektor97](https://x.com/Durektor97))
**Posted:** 2026-07-05 · **Engagement at capture:** 26 likes, 1 RT, 54,715 views
**Format:** Short X thread/image-carousel walkthrough (~2.8k chars across 6 image+caption steps).
**Nature:** **Consumer "build a website with Claude" tutorial thread, framed with a marketing headline.** No product, no code sample beyond prose description, no linked deliverable. **No transferable Claude Code / hub engineering mechanic** — captured for completeness only.

---

## ⚠️ Verification gate (read before propagating anything)

The **"$10,000" agency-price claim appears only in the post's title/hook — it is never substantiated, sourced, or repeated anywhere in the thread body.** Treat it as an unverified marketing framing device, not a researched pricing figure. No income, revenue, or client-count claims appear in the body text itself (unlike other captures in this store that carry anonymized dollar figures) — the only unverified element here is the headline's price comparison.

---

## What it actually shows — a 6-step "build a site with Claude, no-code" walkthrough

1. **Brief first** — write a specific brief before asking Claude to build anything (type of site, style, every section needed) — "the more specific you are, the better the result."
2. **Ask for one complete, working HTML file** — not a template with placeholders; a single copy-paste-ready `index.html` with HTML/CSS/content inline, opens directly in a browser.
3. **Iterate on visual style in plain English** — describe colors/fonts/spacing/animations, paste the current file back, Claude rewrites the CSS; repeat until it looks right.
4. **Add interactivity one feature at a time** — smooth scrolling, mobile menu, form validation, scroll animations — one prompt per feature, Claude writes and integrates the JS.
5. **Responsive QA by precise description** — check mobile + desktop, describe issues precisely ("the hero heading wraps to 3 lines on iPhone" vs. "it looks weird on mobile") for faster fixes.
6. **Deploy via Netlify drag-and-drop** — live URL in under a minute, no account needed for the first deploy; optional free custom domain, with Claude walking through DNS if needed.

---

## Relevance to this hub — LOW (consumer no-code tutorial; no transferable hub mechanic)

This is a beginner-facing "how to vibe-code a website with Claude.ai chat" thread, not a Claude Code engineering pattern. Everything it describes is already handled more rigorously by this hub's own tooling:

| Durektor97 step | Existing hub analogue (already more rigorous) |
|---|---|
| "Write a specific brief first" | `.claude/skills/brainstorm`, `writing-plans` — structured requirements-gathering before any build |
| "Ask for one complete working file" | Not applicable — the hub builds multi-file, tested, version-controlled projects, not single-file demos |
| "Iterate on style/JS one feature at a time, paste file back" | `workflow.md` 7-step loop (test → implement → fix-loop → verify) — a governed loop vs. manual copy-paste |
| "Describe mobile issues precisely" | `web-deploy-readiness.md` rule — actual breakpoint screenshots at 390/768/1280, not prose description |
| "Deploy via Netlify drag-and-drop" | `/vps-deploy` skill, `web-deploy-readiness.md`, Cloudflare/Vercel plugin skills — CI-gated, repeatable deploys |

**No hub action.** No pattern, rule, or workflow change is warranted. Logged only for completeness per the capture directive; the "$10,000 agency" comparison in the title is unverified and must not be cited or reused as a researched figure.
