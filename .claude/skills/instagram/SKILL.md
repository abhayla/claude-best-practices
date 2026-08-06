---
name: instagram
description: >
  Fetch everything retrievable from a public Instagram post link — author,
  engagement, verbatim caption, and the full content of every carousel slide
  (read visually from downloaded images) — using an anonymous extraction
  ladder that needs no Instagram login. Use when the user shares an
  instagram.com/p/ or /reel/ URL and wants its information, content, or
  slides captured. Do NOT use for X/Twitter links (use the twitter-x skill)
  or YouTube links (use youtube-transcript).
triggers:
  - instagram link
  - instagram post
  - fetch instagram
  - instagram carousel
  - ig post content
  - instagram reel info
allowed-tools: "Bash Read Write WebFetch ToolSearch"
argument-hint: "<instagram-post-url>"
type: workflow
version: "1.0.0"
---

# Instagram — Anonymous Post-Extraction Ladder

Extract a public Instagram post's full information without logging in.
Codified from a real successful run (2026-08-06, 8-slide carousel captured
end-to-end after 3 dead ends).

**Request:** $ARGUMENTS

## Prerequisites

| Item | Class | Check |
|---|---|---|
| `curl` | Tool | `curl --version` |
| Playwright MCP (`mcp__playwright__*`) | Service (rung 2+) | ToolSearch loads the tools |
| Scratchpad directory | Path | listed in system prompt |
| Instagram login | **NOT needed** | ladder is anonymous by design |

No credentials, no paid endpoints, no user decisions needed mid-run.

---

## STEP 0: Preflight + Read Learnings

1. Validate the URL: must match `instagram.com/p/<shortcode>` or
   `instagram.com/reel/<shortcode>`. Strip query params (`?img_index=`,
   `?igsh=`) but NOTE `img_index=N` — the user linked slide N; call it out
   in the report.
2. **Read `LEARNINGS.md` in this skill's directory.** Apply any rung
   promotions/demotions and new dead-ends recorded there — the ladder below
   is the baseline; LEARNINGS.md is the living correction layer.
3. Probe `curl --version` (side-effect-free).

If the URL is not an Instagram post/reel link → HARD-STOP and say which
skill fits instead (twitter-x for X, youtube-transcript for YouTube).

## STEP 1: Rung 1 — WebFetch the post URL (metadata + caption summary)

Run WebFetch on the cleaned post URL asking for: author, verified status,
date, likes, comments, caption, image alt text.

- **What this reliably gives:** author handle, approximate date, like/comment
  counts, a SUMMARY of the caption (og-meta description).
- **What it does NOT give:** verbatim caption, carousel slides beyond #1.
- If it returns a login wall: note it in LEARNINGS (rung demotion candidate)
  and continue — later rungs don't depend on this one.

If the user only wanted "what is this post about", STOP here and report.
Otherwise continue — "all information" means the full ladder.

## STEP 2: Rung 2 — Playwright on the embed page (verbatim caption + slide URLs)

The embed page `https://www.instagram.com/p/<shortcode>/embed/captioned/`
renders anonymously with the FULL caption and a navigable carousel — but
only when real JavaScript runs.

1. Load Playwright tools via ToolSearch (`browser_navigate`,
   `browser_snapshot`, `browser_evaluate`, `browser_close`).
2. `browser_navigate` to the embed URL, then `browser_snapshot` — the
   snapshot contains the **verbatim caption**, author, follower count,
   likes, and comment count. Capture them.
3. Carousel: slides lazy-load. Run ONE `browser_evaluate` with an async
   function that (a) collects `document.images` with `naturalWidth >= 500`,
   (b) clicks the "Next" button, waits ~1200ms, re-collects, repeated up to
   10×, (c) returns the deduped `{src, alt, w, h}` list **in insertion
   order** — insertion order == carousel order (verified: a slide stamped
   "06/08" landed at position 6).

```js
async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const urls = new Map();
  const collect = () => { for (const i of Array.from(document.images)) {
    const s = i.currentSrc || i.src;
    if (i.naturalWidth >= 500 && !urls.has(s)) urls.set(s, {alt: i.alt}); } };
  collect();
  for (let k = 0; k < 10; k++) {
    const b = Array.from(document.querySelectorAll('button'))
      .filter(x => ((x.getAttribute('aria-label')||x.textContent||'')).match(/next/i));
    if (!b.length) break;
    b[0].click(); await sleep(1200); collect();
  }
  return Array.from(urls.entries()).map(([src, m]) => ({src, ...m}));
}
```

4. `browser_close` when done.

Single images (no "Next" button) are already complete after step 2.

## STEP 3: Rung 3 — Download slides and read them visually

Slide graphics carry the actual content; alt text is auto-generated junk.

1. Write the collected URLs to `<scratchpad>/ig_slide_urls.txt` (one per
   line, exact — the query params are signed and required).
2. Download: `while IFS= read -r u; do curl -s -A "Mozilla/5.0" "$u" -o
   "slide_$n.jpg"; ...` into the scratchpad. Verify non-trivial file sizes
   (>50KB each; a tiny file = expired/blocked URL → re-collect in Rung 2).
3. `Read` each `slide_N.jpg` (the Read tool renders images) and extract the
   text/diagram content of every slide.

## STEP 4: Compile the report

Locked output format:

```markdown
## Post details
| Field | Value |   <!-- author, verified, followers, date, type, likes, comments, hashtags -->

## Full caption (verbatim)
> <caption exactly as captured in STEP 2>

## All N slides
1. **<slide title>**: <content extracted visually>
...

**Honest read:** <what the post actually is — lead magnet? real content?
inconsistencies between caption promises and slide content>

<risk line: engagement numbers are as-of fetch time>
```

The **Honest read** section is mandatory — extraction without assessment
is half the job (owner standing rule: no sugar-coating).

## STEP 5: Capture Learnings (self-learning loop — MANDATORY)

After EVERY run, compare what happened against the ladder:

| Event this run | Action |
|---|---|
| A rung failed that usually works | Append a dated lesson: rung, URL type, exact error |
| A dead end was hit (new blocker) | Append it under "Known dead ends" with the tell-tale symptom |
| A new technique worked better | Append it as a CANDIDATE rung with evidence |
| Same lesson now has 2+ occurrences | Promote: edit THIS SKILL.md (reorder/replace the rung), bump minor version, note the edit in LEARNINGS.md |
| Clean run, nothing new | Append nothing — no ritual entries |

Entry format (append to `LEARNINGS.md`):

```markdown
## YYYY-MM-DD — <one-line summary>
- Symptom: <exact error / behavior>
- Rung affected: <0-3 / new>
- Evidence: <URL type, what was tried>
- Status: CANDIDATE | CONFIRMED (2+ runs) | APPLIED (SKILL.md edited vN)
```

## Known dead ends (do NOT retry these first — from real runs)

- **claude-in-chrome extension on instagram.com**: script injection times
  out (`waited 45000ms for document_idle`) — Instagram never goes idle.
  Affects screenshot, read_page, get_page_text. Don't burn retries.
- **`curl` on `/embed/captioned/`**: returns a 600KB JS shell with ZERO
  media URLs and no caption — the embed hydrates client-side. curl is fine
  for CDN image downloads (Rung 3), useless for the embed page itself.
- **`?__a=1&__d=dis` JSON endpoint**: returns "Page Not Found" anonymously.
- **og-meta via WebFetch**: works, but the "caption" is a paraphrased
  summary, not verbatim — never present it as a quote.

## MUST DO

- Always read `LEARNINGS.md` before running the ladder — Why: the ladder
  self-corrects there first; skipping it repeats known-fixed failures
- Always capture the caption VERBATIM from the embed snapshot before
  paraphrasing anything — Why: og-meta summaries have been mistaken for
  real captions; a quote must be character-exact
- Always verify downloaded slide file sizes before reading — Why: expired
  signed URLs produce tiny error bodies that waste visual-read calls
- Always include the Honest read section in the report — Why: the owner's
  standing rule requires assessment, not just extraction
- Always run STEP 5 (learning capture) — Why: this is the skill's
  self-improvement contract; a skipped capture is lost evidence

## MUST NOT DO

- MUST NOT log in to Instagram or ask for credentials — the ladder is
  anonymous by design; if a rung demands login, record it and move on
- MUST NOT retry a "Known dead ends" path more than once — go to the next
  rung instead
- MUST NOT trust alt text for slide content — read the downloaded image
- MUST NOT edit SKILL.md on a single occurrence — record in LEARNINGS.md
  first; promote at 2+ occurrences (prevents one-off noise from rewriting
  a proven ladder)
- MUST NOT present engagement numbers without their fetch date
