# Eval — instagram-post-fetch v1.0.0 (2026-08-06)

## Method

Ground-truth validation against the live run the skill was extracted from
(same-session, real target), plus structural self-checks per
writing-skills Step 5. This is an authoring-time eval; a full
/skill-evaluator run (20 trigger queries × 3, stress matrix) has not been
executed — flagged honestly, not claimed.

## Ground truth: live run vs skill procedure

Target: `instagram.com/p/Dboe2qqEnPM/` (seb.ai, 8-slide carousel).

| Skill step | Live-run result | Match |
|---|---|---|
| STEP 1 WebFetch og-meta | author/likes/comments/summary returned | PASS |
| STEP 2 embed snapshot | verbatim caption + counts captured | PASS |
| STEP 2 carousel walk JS | 8/8 unique slide URLs, correct order (06/08 stamp check) | PASS |
| STEP 3 curl download | 8/8 files, 130–224KB each | PASS |
| STEP 3 visual read | all 8 slides' content extracted | PASS |
| STEP 4 report format | delivered incl. Honest read | PASS |
| Dead-end list accuracy | all 4 dead ends hit exactly as documented this run | PASS |

## Structural checks (writing-skills Step 5)

- Frontmatter: name matches dir, third-person description with boundary
  (twitter-x, youtube-transcript), 6 triggers, minimal allowed-tools,
  SemVer version — PASS
- Prerequisites section + STEP 0 preflight present — PASS
- Output format locked (STEP 4 template) — PASS
- MUST DO / MUST NOT DO with `— Why:` on every item — PASS
- Self-learning loop: LEARNINGS.md exists, read gate in STEP 0, capture
  contract in STEP 5 with promotion threshold (2+ occurrences) — PASS
- References self-update protocol: intentionally skipped — the skill
  persists knowledge through LEARNINGS.md (allowed per writing-skills
  Step 2.6 "When to Skip")

## Verdict

PASS for hub-only use. Known limits: single live target so far (one
carousel post; reels and single-image posts exercise Rungs 1–2 only and
are untested end-to-end); trigger-rate eval not yet run. Next eval should
target a reel URL and a single-image post.
