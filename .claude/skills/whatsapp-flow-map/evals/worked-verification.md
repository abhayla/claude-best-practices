# Worked verification — 2026-07-28 (skill's RED/GREEN evidence)

**Subject:** PIFS map rebuild (artifact 18a28208), 80 cards, 6 columns.

**RED (baseline, before the skill's audit layer existed):** the live SSOT map contained
12 buttons with ids but no outgoing edge and 5 buttons with no id at all — invisible
defects; nothing on the page surfaced them.

**Build-time audit:** the SKILL.md §3 audit found all 17. 15 were rule-resolvable
(universal Know More → KM menu; Talk to advisor → advisor handoff; Call me → F4;
Share-on-WhatsApp URL button → /share endpoint per gorefer §6f; sibling-button parity)
and were wired as `design` edges. 2 (leads-template "Share", R1 "Open account") had no
clear instruction → left UNWIRED, surfaced to the owner as questions. None invented.

**GREEN (Playwright, real browser):**
- 76/80 nodes phone-stamped; the 4 `.ext` cards correctly excluded.
- 92 tap elements; click `f0a` → `f1a` centered + `.rx` pulse (single target);
  click `fbrate` → both `fbthanks`+`fbgoogle` pulsed (multi-target);
  click `.out` card `inhi` → `f0` (node-level tap).
- Audit pill rendered "⚠ 2 unwired taps" — count matches the build-time audit exactly.
- 95 wires + 95 packets drawn; zero broken-wire warnings; zero JS errors.

**Charset lesson:** artifact content lacking its own `<meta charset>` renders mojibake
when served outside the claude.ai wrapper — the build now embeds it in the content.
