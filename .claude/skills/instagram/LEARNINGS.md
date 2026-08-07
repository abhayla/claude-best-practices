# instagram — Learnings Log

> Renamed from `instagram-post-fetch` on 2026-08-06 (owner directive).
> Entries below predating the rename use the old name — historically accurate.

The living correction layer for the extraction ladder. Read at STEP 0 of
every run; append per STEP 5. Promote a lesson into SKILL.md only at 2+
occurrences (CONFIRMED), then mark it APPLIED with the version.

---

## 2026-08-06 — Founding run (seb.ai 8-slide carousel, full capture)

- Symptom: n/a — this run built the ladder.
- Rung affected: all (baseline established)
- Evidence: `instagram.com/p/Dboe2qqEnPM/` — WebFetch og-meta gave summary
  only; claude-in-chrome injection timed out on instagram.com (page never
  reaches document_idle); curl on /embed/captioned/ returned a JS shell
  (609KB, zero media URLs); `?__a=1&__d=dis` returned Page Not Found;
  Playwright on /embed/captioned/ rendered verbatim caption + navigable
  carousel; scripted Next-click walk collected all 8 signed CDN URLs in
  carousel order; curl downloaded each (130-224KB); visual Read extracted
  every slide.
- Status: APPLIED (SKILL.md v1.0.0 — ladder + dead-ends section seeded)

## 2026-08-06 — Carousel order == image insertion order

- Symptom: needed slide order without trusting collection heuristics.
- Rung affected: 2
- Evidence: slide graphic stamped "06/08" landed at position 6 of the
  collected list; user's `img_index=6` link matched the same slide.
- Status: CONFIRMED (single run but internally double-verified); baked
  into SKILL.md STEP 2.

## 2026-08-07 — Rung 1 (WebFetch og-meta) returned an empty shell

- Symptom: WebFetch on the post URL got a page containing only the word
  "Instagram" — no og-meta, no author, no counts. Rungs 2-3 unaffected.
- Rung affected: 1
- Evidence: `instagram.com/p/DbRZ68ViMNF/` (charliehills 6-slide carousel).
  Founding run 2026-08-06 DID get og-meta from Rung 1, so this is
  intermittent (server-side rendering withheld), not a hard block.
- Status: CANDIDATE (demote Rung 1 to "best-effort, skip fast" at 2+)

## 2026-08-07 — 50KB size floor false-alarms on webp slides

- Symptom: valid p1080 carousel slides downloaded as 33-54KB .webp files,
  under the SKILL.md ">50KB each" validity floor; all 6 rendered fine.
- Rung affected: 3
- Evidence: same run; founding run's slides were larger jpgs (130-224KB).
  Better validity check: file is a real image (magic bytes / Read renders)
  rather than a byte-size threshold; error bodies are typically <5KB.
- Status: CANDIDATE

## 2026-08-07 — First slide collected twice at two resolutions

- Symptom: collection returned 7 URLs for a 6-slide carousel — slide 1
  appeared as both full-res and `stp=dst-webp_p1080x1080` variants (same
  `75…_n.webp` file ID).
- Rung affected: 2
- Evidence: same run; deduping by the file-ID segment of the CDN path (not
  the full URL) gives the true slide count, matching the embed's dot count.
- Status: CANDIDATE (add file-ID dedupe to the collector at 2+)
