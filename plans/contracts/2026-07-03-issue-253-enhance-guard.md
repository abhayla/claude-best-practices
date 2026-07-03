# Contract: Fix guard hooks that re-block a grade card rendered before tool calls (issue #253)

**Executor:** `/loop-engineering` (first hub self-improvement run)   ·   **Created:** 2026-07-03
**Mission:** The Stop-hook guard(s) enforcing the prompt-auto-enhance grade card scan only the
LAST assistant text block of a turn. A turn that renders the full card UP FRONT, then makes tool
calls, then ends with a short summary, is wrongly judged "card missing" and blocked — forcing a
duplicate render. Fix the guard(s) to credit a card rendered ANYWHERE in the turn's assistant
output. Build + verify + commit on a branch; do NOT merge (owner lands via CI-gated PR).

## Definition of Done (ACTION + COMPLETENESS BAR — machine-checkable)
- [ ] A test in `scripts/tests/test_no_overask_card_enforcement.py` reproduces the mid-turn-card
      scenario (card in an EARLY assistant text block + a `tool_use` + a final short summary block)
      and asserts the guard does NOT block. It must demonstrably FAIL on current code and PASS after
      the fix (write it failing FIRST — TDD).
- [ ] Each guard's card-detection runs over the CONCATENATION of every assistant `text` block emitted
      since the last real (non-tool-result) user message — not just the final block.
- [ ] Both guard copies that actually have the last-block-only defect are fixed and kept in sync:
      `.claude/hooks/no-overask-guard.sh` (hub; dual-home in `config/dual-home-resources.yml`) and
      `plugins/prompt-auto-enhance/hooks/enhance-process-guard.sh` (plugin). If a copy is already
      correct (the hub copy comments "Aggregate ALL assistant text of the FINAL turn" — VERIFY),
      record that and leave it untouched.
- [ ] `plugins/prompt-auto-enhance/.claude-plugin/plugin.json` version bumped PATCH (cache propagation).
- [ ] Dual-home sync test (`scripts/tests/test_dual_home_sync.py`) passes.
- [ ] Full local gate GREEN: `dedup_check.py --validate-all`, `dedup_check.py --secret-scan`,
      `workflow_quality_gate_validate_patterns.py`, and the FULL `pytest scripts/tests/` suite
      (baseline 1631 passing — must not regress).
- [ ] Work committed on `fix/issue-253-enhance-guard` (local). NOT pushed, NOT merged.
- [ ] Terminal signal (`shipped`, or a clean `escalated`) in `.claude/learnings.json` with
      `hub_pattern_link: "prompt-auto-enhance"`.

## Pre-made decisions (do NOT pause on these)
1. **Root-cause first.** Read each guard's `jq` extraction. Determine whether it aggregates ALL
   assistant text blocks since the last real user turn, or only the last block. Fix wherever the
   last-block-only behavior exists.
2. **The fix shape.** Extract + concatenate EVERY assistant `text` block after the last real user
   message; run the existing card-detection regexes over that concatenation. Keep all other guard
   logic (trivial-path, slash-exemption, thresholds) unchanged.
3. **Minimal, surgical `jq` change** — do not rewrite the hooks; change only the extraction step.
4. **TDD** — the failing test comes before the code change.

## Scope
- **In:** the two guard hooks above · `scripts/tests/test_no_overask_card_enforcement.py` ·
  `plugins/prompt-auto-enhance/.claude-plugin/plugin.json` (version) · `registry/patterns.json`
  (resync `no-overask-guard` hash if it is a registered pattern).
- **OUT (do NOT touch this run):** the trivial-path `<600`-char rule and the `/init`-expanded-text
  sub-issues (issue #253 lists these as "related" — leave a one-line note, fix separately) · the
  prompt-auto-enhance rule text · any other hook · anything under `core/` unless dual-home sync
  requires it.

## Guardrails
- No new dependencies. No push, no PR, no merge, no deploy. Conventional commits only.
- No synthetic verification — a "PASS" without the failing-then-passing test is a gate failure.
- Respect the two-`.claude/` boundary and the dual-home fences; keep shared logic identical.
- Budget: `--max-cycles 2`, default retry budget. Surface uncertainty as `**Assumption:** X`.

## References (load transitively)
- `.claude/rules/` (hub rules) · `config/dual-home-resources.yml` · `docs/HUB-CORE-SYNC.md`
- The `/plugin-lifecycle` version→cache contract (a plugin hook edit needs the version bump).
