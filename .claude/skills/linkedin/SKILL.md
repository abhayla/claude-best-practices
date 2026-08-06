---
name: linkedin
description: >
  Fetch everything retrievable from a public LinkedIn post link — author,
  date, full post text, engagement counts, comments, and media — using an
  anonymous extraction ladder built on LinkedIn's server-rendered JSON-LD
  (no login, no partner API). Use when the user shares a linkedin.com/posts/
  or /feed/update/ URL and wants its information or content captured. Do NOT
  use for Instagram links (use the instagram skill), X/Twitter links (use
  twitter-x), or LinkedIn PROFILE pages (different surface, aggressive
  authwall — not covered here).
triggers:
  - linkedin link
  - linkedin post
  - fetch linkedin
  - linkedin article content
  - linkedin post details
allowed-tools: "Bash Read Write WebFetch ToolSearch"
argument-hint: "<linkedin-post-url>"
type: workflow
version: "1.0.0"
---

# LinkedIn — Anonymous Post-Extraction Ladder

Extract a public LinkedIn post's full information without logging in.
Codified from live-verified probes (2026-08-06, 3 different public posts:
person/article-share, person/text-with-emoji, company/video).

**Request:** $ARGUMENTS

## Prerequisites

| Item | Class | Check |
|---|---|---|
| `curl` | Tool | `curl --version` |
| Python 3 | Tool (JSON-LD parse) | `python --version` |
| Scratchpad directory | Path | listed in system prompt |
| LinkedIn login | **NOT needed** for public posts | ladder is anonymous |

No credentials, no partner API, no mid-run user decisions.

---

## STEP 0: Preflight + Read Learnings

1. Validate the URL: must match `linkedin.com/posts/<slug>-activity-<id>-`
   or `linkedin.com/feed/update/urn:li:activity:<id>`. Extract the numeric
   **activity ID** (`activity-(\d+)` from a /posts/ slug, or the urn digits)
   — Rung 2 needs it.
2. If the URL is a PROFILE (`/in/<name>`), company page, or job posting →
   HARD-STOP: this skill covers posts only; those surfaces authwall harder
   and have no verified anonymous path here.
3. **Read `LEARNINGS.md` in this skill's directory.** Apply recorded rung
   promotions/demotions and new dead ends before running the ladder.
4. Probe `curl --version` and `python --version` (side-effect-free).

## STEP 1: Rung 1 — curl the post URL, parse JSON-LD (the workhorse)

One anonymous GET returns server-rendered HTML containing a complete
schema.org JSON-LD block — full text, author, date, likes, comments.

```bash
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" \
  "<post-url>" -o li_post.html
```

Parse (ALWAYS `encoding="utf-8"` — post bodies contain emoji; Windows
cp1252 default throws `UnicodeEncodeError` on print, a parser-side trap,
not a data problem):

```python
import re, json
h = open('li_post.html', encoding='utf-8', errors='replace').read()
b = re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
d = json.loads(b.group(1))
```

**The JSON-LD `@type` VARIES by post kind — handle both (live-verified):**

| Post kind | `@type` | Fields present |
|---|---|---|
| Text / article share (person) | `SocialMediaPosting` | `articleBody` (full text), `author.name`, `author.url`, `author.interactionStatistic` (follower count), `datePublished`, `commentCount`, `comment[]` (full comment texts + authors + like counts), `image.url`, `interactionStatistic[]` (LikeAction count) |
| Video post (company/person) | `VideoObject` | text in `articleBody`/description fields, `datePublished`, `interactionStatistic[]` (likes + comments), `commentCount` — `author.name` may be ABSENT; fall back to og:title / page HTML |

Success check: JSON-LD parsed AND (`articleBody` or headline) non-empty.
Failure tells: HTTP 200 but final URL contains `/authwall`, or the HTML
contains a login form and NO `application/ld+json` block → record in
LEARNINGS (authwall lottery), drop to Rung 2.

## STEP 2: Rung 2 — the embed endpoint (fallback, needs activity ID)

```
https://www.linkedin.com/embed/feed/update/urn:li:activity:<id>
```

Anonymous, small (~20KB), server-rendered: post text, author headline,
og-meta. Less data than Rung 1 (no comments, no counts in some cases) but
a different code path that can survive when the post page authwalls.
Public-visibility posts only — LinkedIn only issues embeds for posts set
to "Anyone".

## STEP 3: Rung 3 — WebFetch og-meta (summary of last resort, anonymous)

WebFetch the post URL and ask for author/title/description. og:description
carries the post text (possibly truncated). Never quote og-meta output as
the verbatim full text without confirming it against Rung 1/2 output.

## STEP 4: Media download (when the post has images/documents)

`media.licdn.com` URLs from `image.url` / og:image download with plain
curl (verified 200). Save to the scratchpad and `Read` visually when the
image content matters (infographics, document carousels).

**UNTESTED (declared fallback, no user input needed):** multi-image posts
and document (PDF carousel) posts — their JSON-LD shape is unverified.
First real encounter: capture the raw HTML to the scratchpad, extract
what's available, and record the shape in LEARNINGS.md.

## STEP 5: Rung 4 — logged-in browser (LAST resort, UNTESTED)

If every anonymous rung authwalls (private post, or IP-level wall): the
user's own logged-in Chrome via browser automation is the only remaining
path. UNTESTED as of 2026-08-06. Constraints: read-only navigation, never
act on the user's LinkedIn account (no likes/follows/posts), and note that
the claude-in-chrome extension needs site permission for linkedin.com.
A private post is the author's audience choice — report that it is
login-gated rather than treating extraction as guaranteed.

## STEP 6: Compile the report

Locked output format:

```markdown
## Post details
| Field | Value |   <!-- author, headline/followers, date, type, likes, comments -->

## Full post text (verbatim)
> <articleBody exactly as parsed>

## Comments (N captured in page payload)
- <author>: <text> (<likes>)

## Media
<downloaded/described, or "none">

**Honest read:** <what the post actually is; inconsistencies>

<risk line: engagement numbers as-of fetch date; anonymous payload may
cap comment list — counts are from JSON-LD, not a full comment crawl>
```

## STEP 7: Capture Learnings (self-learning loop — MANDATORY)

Same contract as the instagram skill: after EVERY run —

| Event this run | Action |
|---|---|
| A rung failed that usually works (e.g., authwall hit) | Append dated lesson: rung, URL type, symptom |
| New post-kind JSON-LD shape encountered | Append the shape (fields present/absent) |
| A new technique worked better | Append as CANDIDATE |
| Lesson reaches 2+ occurrences | Promote: edit THIS SKILL.md, bump minor version, mark APPLIED |
| Clean run | Append nothing |

Entry format: same as `../instagram/LEARNINGS.md` (date, symptom,
rung, evidence, status CANDIDATE/CONFIRMED/APPLIED).

## Known dead ends (do NOT attempt first — verified or sourced)

- **Official API for reading others' posts**: partner-gated; the Marketing
  Activity Feed API version 202406 is sunset and access is no longer
  granted (Microsoft Learn, checked 2026-08-06). Not a viable rung.
- **Windows default codec on post bodies**: emoji in `articleBody` breaks
  cp1252 printing — always parse/print with UTF-8 (hub-wide known trap).
- **Authwall lottery**: NOT observed in 5/5 probes on 2026-08-06 (3 posts,
  3 repeats on one), but widely reported for datacenter IPs and high
  request rates — treat a `/authwall` redirect as expected behavior, not
  an error; drop a rung, don't retry-loop.

## MUST DO

- Always read `LEARNINGS.md` before running the ladder — Why: the ladder
  self-corrects there first; skipping repeats known-fixed failures
- Always branch on the JSON-LD `@type` (SocialMediaPosting vs VideoObject)
  — Why: assuming one shape silently drops author/text on the other kind
- Always parse with explicit UTF-8 encoding — Why: emoji in post bodies
  crash default-codec parsing on Windows
- Always quote `articleBody` verbatim in the report — Why: og-meta
  summaries are not the post text; a quote must be character-exact
- Always include the Honest read section — Why: owner standing rule;
  extraction without assessment is half the job
- Always run STEP 7 learning capture — Why: the self-improvement contract;
  especially record the first authwall hit and the first carousel/document
  post (both currently unverified territory)

## MUST NOT DO

- MUST NOT log in, ask for credentials, or drive the user's LinkedIn
  session for public posts — anonymous rungs 1-3 cover them
- MUST NOT act on the user's LinkedIn account in Rung 4 (no reactions,
  follows, comments, posts) — read-only navigation only
- MUST NOT retry an authwalled URL more than once per rung — move down
  the ladder instead
- MUST NOT use this skill for profile/company/job pages — HARD-STOP in
  STEP 0; those surfaces have no verified anonymous path here
- MUST NOT present comment lists as complete — the anonymous payload
  embeds a subset; only `commentCount` is authoritative
- MUST NOT edit SKILL.md on a single occurrence — LEARNINGS.md first,
  promote at 2+ (protects a live-verified ladder from one-off noise)
