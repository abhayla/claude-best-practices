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
