# T-391 freshness note (2026-08-27, SCOPE block — owner-present = in-session)

Owner decision 2026-08-27 18:03/18:20 IST (global `~/.claude/CLAUDE.md` "Where work runs" rules
1-5, supersedes the 2026-08-15 "never inline" rule): owner-present work runs IN-SESSION (a
worktree of the target repo, T-id + contract still required, Opus/Sonnet `Agent` implements, a
fresh Opus reviews, Fable lands); `/get-work-done` is now ONLY for unattended/hands-off app-repo
work; fleet-core (bus scripts, this skill/tests) is FROZEN; a weekly app÷fleet-landed ratio
(`fleet-ratio.py`) decides whether GWD becomes a thin launcher by 2026-09-10.

## What changed in SKILL.md

- New `## SCOPE (owner 2026-08-27)` section right after the Mode router, stating the four rules
  above in plain English plus "Every task keeps its T-id + contract + LEDGER line + registry
  flips regardless of mode."
- STEP 3's `### FAST LANE` heading and intro reframed: session-executed work in a worktree of the
  target repo is now described as the DEFAULT whenever the owner is present (not a size-gated
  exception), with STEP 6's background dispatch named as the unattended path. The ELIGIBILITY
  criteria, FLOW, gate scripts and preflight exit codes are all unchanged byte-for-byte in
  substance — no gate or exit code was removed.
- No procedure, MUST bullet, or gate:id was removed; PROSE-ONLY MUST count did not grow (verified
  against `origin/main` via `scripts/gwd_skill_conformance.ratchet_violations_vs_ref`).

## Byte budget

SKILL.md was 29,989 B before this change (11 B under the 30,000 B ratchet ceiling). Adding the
~660 B SCOPE block plus the FAST LANE reframe required trimming non-normative prose elsewhere
(intro paragraph, STEP 1/2/6/7 wording, exit-code table descriptions, ARTIFACT PLACEMENT) — no
`MUST` text, gate id, exit code, settings key, or pinned test phrase was touched. Final size:
29,984 B (16 B headroom).

## Verification

- Targeted guards green: `test_gwd_skill_conformance.py`, `test_gwd_skill_conformance_grandfather_ratchet.py`,
  `test_gwd_skill_musts_have_gates.py`, `test_get_work_done_fast_lane.py`,
  `test_owner_status_cadence_guidance.py`, `test_root_cause_gate_guidance.py`,
  `test_skip_ci_guidance.py` — 46/46 passed (`GWD_ROOT` set, conformance ratchet exercised against
  the live fleet checkout).
- Full local suite + the four CI validators re-run per the contract's DoD before landing (see PR
  body for the exact counts).

This note satisfies the eval-coverage freshness ratchet for a scope/framing change with no new
behavior to scenario-test — the existing `2026-08-27-v010-rewrite.md` eval already exercises the
procedure this note's diff sits inside.
