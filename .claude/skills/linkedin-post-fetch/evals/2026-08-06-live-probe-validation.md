# Eval — linkedin-post-fetch v1.0.0 (2026-08-06)

## Method

Live anonymous probes against 3 real public posts BEFORE authoring (the
skill documents only what was verified working), plus structural checks
per writing-skills Step 5. A full /skill-evaluator battery (20 trigger
queries × 3, stress matrix) has NOT been run — stated, not hidden.

## Live verification matrix

| Rung | Test | Result |
|---|---|---|
| 1: curl + JSON-LD | khuddell article-share post | PASS — SocialMediaPosting: full articleBody, author+2,763 followers, date, 13 likes, 2 comments with full texts |
| 1: curl + JSON-LD | schmarzo text post (emoji in body) | PASS — parsed with UTF-8; exposed the cp1252 print trap (documented) |
| 1: curl + JSON-LD | box company video post | PASS with variance — VideoObject shape, 310 likes/7 comments, author.name absent (branch table added) |
| 1: stability | same URL ×3 rapid repeats | PASS — 3/3 HTTP 200, identical size, no authwall |
| 2: embed endpoint | urn:li:activity:7485398684998803457 | PASS — 20KB, post text + author headline, no authwall |
| 3: og-meta | og:description/title/image present in all 3 captures | PASS (tags verified in HTML; WebFetch reads them) |
| Media | media.licdn.com og:image via plain curl | PASS — HTTP 200 |
| Dead end: official API | Activity Feed API sunset notice | CONFIRMED via learn.microsoft.com (202406 sunset, access no longer granted) |

## Explicitly untested (declared in the skill, not glossed)

- Authwall path (never triggered in 5 probes; residential IP)
- Multi-image and document/PDF-carousel post JSON-LD shapes
- Rung 4 logged-in browser fallback
- Trigger-rate eval battery

## Structural checks (writing-skills Step 5)

Frontmatter (name=dir, third-person description with 3 sibling-skill
boundaries, 5 triggers, minimal tools, SemVer) — PASS. Prerequisites +
STEP 0 preflight with profile-page hard-stop — PASS. Output format locked
(STEP 6) — PASS. MUST DO/MUST NOT with `— Why:` throughout — PASS.
Self-learning loop (LEARNINGS.md read gate STEP 0 / capture STEP 7,
2+ promotion rule) — PASS. References protocol intentionally exempt:
knowledge persists via LEARNINGS.md (writing-skills Step 2.6 skip rule),
exemption cited here per AUTHOR-LEARNINGS 2026-08-06.

## Verdict

PASS for hub-only use, on stronger evidence than instagram-post-fetch v1
(3 live targets vs 1, two JSON-LD shapes captured). Next eval targets:
a document-carousel post and a deliberately private post (authwall path).
