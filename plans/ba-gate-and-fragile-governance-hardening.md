# Plan: BA-Gate + Fragile Advisory-Governance Hardening

**Created:** 2026-06-18
**Branch:** feat/web-analytics-instrumentation (or new: fix/ba-gate-hardening)
**Trigger:** BA discovery silently skipped in a working session ("asked it to work on
things → got basic data, no BA"). Root-cause investigation found the BA trigger hook
exists in `core/` but is (a) unwired in the hub, (b) mis-gated on keywords, (c) stale
downstream, (d) behaves as a mandate not an offer.

**User decisions (2026-06-18):**
1. Trigger behavior → **ask the user** whether to invoke BA / deep research (offer gate,
   not silent mandate). Recommended-on for domain/user-facing builds.
2. Mechanism → **hook + rule sharpening** (defense in depth).
3. Blast radius → **whole fragile-governance class**, not just BA.

---

## Root cause (evidence-grounded)

The BA process is the *advisory-only, model-self-classified, positionally-buried* class
of governance — the weakest kind per the hub's own `rule-writing-meta.md` ("convert
zero-exception rules to hooks"). Specifics:

- `core/.claude/hooks/ba-usecase-discovery-reminder.sh` exists + wired in
  `core/.claude/settings.json`, BUT **not present/wired in the hub's `.claude/`** → hub
  sessions get zero BA salience.
- Keyword gate (hook line 32) omits `add`, `work on`, `extend`, `set up`, `I need`,
  `help me` → the most common build phrasings miss.
- Downstream projects only have it if re-provisioned after it landed.
- It injects a "do the BA order" reminder; user wants an **offer** ("run BA/deep research?").
- The same fragile pattern affects sibling gates with no deterministic salience:
  G1/G2 human-approval, supervisor/independent blind-verify, output-plausibility,
  the never-skip-the-reviewer-edge.

## Finalized BA-GATE criteria

- **Fires** on build/add/extend/work-on intent for product/feature/tool/screen/flow/
  calculator/domain-or-business logic (broadened verb+noun + domain signals:
  finance/tax/pricing/decision-tool/calculation).
- **Excludes** refactor, bugfix, mechanical edit, infra/config, pure-technical (no domain/
  user surface), trivial/continuation.
- **Behavior:** inject a `*Sync-check:*` OFFER to run BA discovery / deep research
  (recommended for domain/user-facing). Opt-in → ba-discovery-checklist + full-space-first
  + G1. Decline → proceed, state assumption. Offer is over-ask-guard-exempt.
- **Where:** hub `.claude/` AND `core/.claude/` (distributable).

---

## Work items (sequenced, checkpoint-committed)

### Phase 1 — BA-gate (the reported miss) — DONE 2026-06-18
- [x] **1.1** Broadened the keyword gate (added `add|extend|work on|set up|i need|i want|help me|improve`
      + domain signals finance/tax/pricing/loan/invest/decision/calculation). Trivial/continuation skip kept.
- [x] **1.2** Reframed injection from *mandate* to **offer**: opens with a `*Sync-check:*` line offering
      BA discovery / deep research, recommended-on for domain/user-facing; opt-in → checklist, decline → assumption.
- [x] **1.3** Copied the hook into hub `.claude/hooks/` and wired it into hub `.claude/settings.json` UserPromptSubmit.
- [x] **1.4** Added the three BA rules to the hub `CLAUDE.md` governance-SSOT read-exception.
- [x] **1.5** Sharpened `engineering-roles.md`: replaced `[PM if scope unclear]` with a mandatory PM/BA OFFER.
- [x] **CI:** registry resynced (hook v1.3.0, engineering-roles v1.4.1); 4 validators + 1469 tests green.
- [x] **Guard:** `scripts/tests/test_ba_gate_wiring.py` (6 tests) pins hub-wiring + offer-behavior + keyword coverage.
- [x] **Functional:** "work on the loan calculator" fires; refactor/bugfix/continuation stay silent.

### Phase 2 — whole-class salience (sibling fragile gates)
- [ ] **2.1** Inventory the class: G1/G2 approval, supervisor-verification,
      independent-test-verification, output-plausibility-verification, reviewer-edge.
- [ ] **2.2** For each, decide hook-able vs rule-only; add a deterministic salience trigger
      (PostToolUse/Stop reminder) where a clean signal exists; sharpen rule wording where not.
- [ ] **2.3** Avoid reminder-fatigue: gate each injection on its real signal (e.g. plausibility
      reminder only on computed-value/UI output turns), not every prompt.

### Phase 3 — CI + distribution
- [ ] **3.1** Update `registry/patterns.json` if any pattern frontmatter/version changes;
      resync hash; respect ≤100-line budget on edited patterns.
- [ ] **3.2** Run full local CI: `dedup_check --validate-all`, `--secret-scan`,
      `workflow_quality_gate_validate_patterns`, `pytest scripts/tests/ -v`.
- [ ] **3.3** Add a hub regression test asserting the BA hook is wired in BOTH
      `core/.claude/settings.json` and `.claude/settings.json` (prevents re-drift).
- [ ] **3.4** Note: downstream projects need `/update-practices` + session restart to pick up
      the new/changed hook (agent/hook registry is session-pinned).

## Verification
- Hub session: a "work on the loan calculator" prompt fires the BA offer (manual check).
- A "fix the failing test" prompt does NOT fire it (exclusion check).
- CI green; regression test pins the wiring.

## Risks / assumptions
- **Assumption:** the reported miss was a build/domain prompt that the narrow gate or the
  hub-unwiring dropped — consistent with "work on" phrasing. If the session was a downstream
  with the hook present, root cause narrows to keyword-gate + mandate-vs-offer (still fixed here).
- Reminder-fatigue is the main risk of "whole class now" — Phase 2.3 mitigates by signal-gating.
