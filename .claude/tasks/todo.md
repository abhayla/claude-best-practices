# The Work Queue — the one place to look

<!-- Owner-facing board (established 2026-07-13, owner question: "where is your list of todos,
     which model, who initiates, how"). Claude keeps this current at every session close.
     Pre-2026-07-13 task blocks (all completed: TODO-app rebuild, karpathy-advisor, platform
     migration, loop-engineering, firekaro promotion) live in git history of this file. -->

**How to read this:** every open piece of work, who runs it (model), who presses start, and
the exact way to start it. Feeder systems below the table add items automatically.

## Queue (2026-07-13)

| # | Work item | Model to use | Who starts it | How to start |
|---|---|---|---|---|
| 1 | Thin-pointer conversion, cluster 1 (quality trio) — plan: `plans/core-skills-thin-pointer-conversion.md` | **Opus driver** (or Sonnet maker + Opus checker via loop) | **You** — open a session on Opus | Type `/continue` — the handoff loads the plan and instructions |
| 2 | Clusters 2–4 (same plan, one per cycle) | Same as #1 | **You**, after each cluster lands | `/continue` in a fresh Opus session |
| 3 | IPODhan test debt — 42 failing tests (IPODhan #109) | **Sonnet** | **You**, whenever | In the IPODhan folder: `/debugging-loop` pointing at issue #109 |
| 4 | AlgoChanakya test debt — fixture-chain errors (algochanakya #89) | **Sonnet** | **You**, whenever | In the algochanakya folder: `/debugging-loop` pointing at issue #89 |
| 5 | Sync retirement stage 2 — final form of the residual copy surface | **Opus** frames options; **you decide** | **You**, after clusters finish | Ask "frame sync stage 2" in any session |
| 6 | Monthly release-scout findings | **Sonnet** (routine runs itself) | **Nobody** — self-starts Aug 1, 13:30 IST | Automatic; filed issues appear titled `new-claude-features:` — approve/decline in any session |
| 7 | G5 trust-score graduation — **design landed** (`plans/g5-autonomy-graduation-design.md`, PR #365): L0–L4 ladder, evidence bars; runs keep accruing per merged PR | No one — accrues from every merged PR | **Nobody** | Automatic; watch `trust-score/dashboard.html`; ladder milestones are items 9–10 |
| 8 | Eval grandfather list shrink (165 skills) | **Sonnet**, opportunistic | Either — CI nags on every touched skill | Editing any listed skill forces `/skill-evaluator`; the list only shrinks |
| 9 | G5 milestone **M1a** — label-fidelity audit of `human_had_to_fix` (89% fc on reversible AUTO is likely proxy noise; hand-classify a sample vs real PR history) | **Opus** | **You**, whenever | Point any Opus session at plan §4 M1a |
| 10 | G5 milestone **M1b** — kill the constant-60 default signals in merged-PR scoring (47/56 runs carry no information) | **Sonnet** (mechanical, plan-scoped) | **You**, after M1a | `/debugging-loop` on `record_merged_prs.py`/`collect_signals.py` per plan §4 M1b |
| 11 | **Fable-harvest Session B** — ✅ MERGED 2026-07-13 (PR #371, `validate` SUCCESS, verified landed): 6 evaluator-PASSED skills (3 core registered + 3 hub-only) + test-pipeline 3.1.0 / create-github-issue 1.1.0 / auto-verify 4.5.0 / plugin 0.2.0; record: `docs/governance/fable-failure-archaeology-2026-07-13.md` | — | — | Done — Session C (item 12) is next |
| 12 | **Fable-harvest Session C** — rubric-mining from ledgers + weakened-test hunter skill (same plan) | **Fable 5** (window-sensitive) | **You**, after B | `/continue` in a Fable session |
| 13 | Rule-stack audit follow-ups — 2 hook bugs (machine-origin exemption, BA-gate precision) + claude-behavior cleanup + enhance-ceremony rewrite, per `docs/governance/fable-rule-stack-audit-2026-07-13.md` §4. Fresh live evidence 2026-07-13 (Session B): BA-gate banner misfired on 2 task-notifications; enhance Stop hook blocked a machine-notification turn whose only human input was "continue". Fix recipe now exists: `/hook-transcript-fixture-test` (Session B skill) — capture these exact shapes as fixtures first; the misfire transcripts live in session `364b8588-6acc-4891-95bb-695cf5fe2808` under `~/.claude/projects/D--Abhay-VibeCoding-claude-best-practices/`. Also noted 2026-07-13: the prompts.md secret-scan hit was a FALSE POSITIVE (the scanner re-flagged its own quoted secret-assignment example inside logged prose) — recurring-noise class; owner may want the scanner to skip gitignored local logs (security-gate scope change, owner-gated) | **Opus** (bugs/cleanup); **you** approve each rule change | **You** — approve the audit's proposals | Point any session at the audit doc §4 |
| 14 | Scan items #7–#10 (audit-subagent surface, pre-install skill security scan, novelty tracking, doc citations) — not window-sensitive | **Sonnet/Opus** | **You**, whenever | Scan report `sources/2026-07-13-fable-window-external-scan-report.md` has the briefs |
| — | *Fable-only reserve:* unplanned novel design, adversarial strategic verification, Operating-Manual updates, twice-escalated incidents | **Fable 5** | **You**, when one appears | Open a Fable session and describe it |

## Future / to-be-discussed (owner decisions, nothing started)

- More stack packs (Android for KKB, Vue for AlgoChanakya) — parked until a workflow needs one (YAGNI).
- Re-run `/model-parity-test` after any major Operating-Manual revision (judgment-triggered) —
  DONE for v2.0 (2026-07-13 mini-reexam, PR #363); next trigger = next major revision.
- Operating-Manual v2.1 candidate (evidence-gated, owner-approved 2026-07-13): add a
  **contradictory-instructions check** to §1 — "if two instructions cannot both hold (e.g.
  'be exhaustive' + 'under 100 words'), serve the operating intent and state the tradeoff in
  one line, never silently sacrifice one" — plus a matching distilled-core line. Sourced from
  an external manual variant compared 2026-07-13 (only real gap found; v2.0 is otherwise a
  superset). Per the manual's revision policy, fold in ONLY at the next evidence-driven bump
  (a failed exam case or documented incident of this class) — never as a standalone edit.
- REWRITE candidate in prompt-auto-enhance rule — re-measure telemetry ~2026-07-19 (post-#332 week).

## Where items come from (the feeders — automatic)

1. **GitHub issues** (`gh issue list`) — anything filed becomes queue material.
2. **The monthly scout** — files `new-claude-features:` issues on the 1st.
3. **`.remember/remember.md`** — the session-to-session handoff buffer; `/continue` reads it.
4. **`plans/*.md`** — multi-session work carries its own plan file.
5. **This session's live tasks** — mirrored here at close by `/end-session`.

## The rule that keeps this honest

Every `/end-session` updates this file; every `/continue` reads it. If this board and reality
disagree, reality wins and the board gets fixed in the same turn.

---

## Durable local gotchas (kept from prior sessions)

- test_prompt_logger fails locally on Windows (bash hook invocation) on a CLEAN tree
  too — not a regression; passes in Linux CI. Deselect locally, trust CI.
- registry/patterns.json is NOT alphabetical — append entries, never re-sort.
- gh pr create --body with embedded double quotes breaks PS 5.1 arg passing — use
  --body-file.

## Archive

### Subagent Dispatch Platform Limit Remediation (2026-04-24) — ✅ COMPLETE
Resolved as Option A (T0-only orchestrator, skill-at-T0). See CLAUDE.md
"Workflow Orchestration (skill-at-T0)" + docs/WORKFLOW-DIAGRAM.md for the
shipped model; lessons captured in .claude/tasks/lessons.md.
