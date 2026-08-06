# linkedin — Learnings Log

> Renamed from `linkedin-post-fetch` on 2026-08-06 (owner directive).
> Entries below predating the rename use the old name — historically accurate.

The living correction layer for the extraction ladder. Read at STEP 0 of
every run; append per STEP 7. Promote at 2+ occurrences (CONFIRMED), then
mark APPLIED with the version.

---

## 2026-08-06 — Founding probes (3 public posts, ladder established)

- Symptom: n/a — research + live verification run.
- Rung affected: all (baseline)
- Evidence: 3 posts probed anonymously with plain curl, all HTTP 200 with
  full JSON-LD, zero authwalls (khuddell article-share, schmarzo text post
  with emoji, box company video). Repeat-probe 3× on one URL: stable.
  Embed endpoint `urn:li:activity:<id>` returned post text + author
  headline (20KB). media.licdn.com image downloaded with plain curl (200).
  Activity Feed API confirmed sunset (Microsoft Learn 202406 notice).
- Status: APPLIED (SKILL.md v1.0.0)

## 2026-08-06 — JSON-LD @type varies by post kind

- Symptom: company video post parsed with no author name.
- Rung affected: 1
- Evidence: person posts → `SocialMediaPosting` (articleBody, author.name,
  comment[]); company video post → `VideoObject` (stats present, author
  absent). One sample per shape.
- Status: CONFIRMED (two shapes each seen once, both live-captured); baked
  into SKILL.md STEP 1 as a branch table.

## 2026-08-06 — UTF-8 parse trap on Windows

- Symptom: `'charmap' codec can't encode character '\U0001f916'` printing
  a post body containing 🤖.
- Rung affected: 1 (parse side)
- Evidence: schmarzo post probe; matches the hub-wide cp1252 lesson in
  CLAUDE.md (Environment section).
- Status: APPLIED (SKILL.md v1.0.0 — explicit UTF-8 in the parse snippet)

## Open unknowns (watch for on future runs)

- Authwall never observed (5/5 probes clean) — first hit should be
  recorded with IP context and which rung survived.
- Multi-image and document (PDF carousel) posts — JSON-LD shape unknown.
- Rung 4 (logged-in browser) — never exercised.
