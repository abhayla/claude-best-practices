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
| 7 | G5 trust-score graduation | No one — accrues from every merged PR | **Nobody** | Automatic; watch `trust-score/dashboard.html` |
| 8 | Eval grandfather list shrink (165 skills) | **Sonnet**, opportunistic | Either — CI nags on every touched skill | Editing any listed skill forces `/skill-evaluator`; the list only shrinks |
| — | *Fable-only reserve:* unplanned novel design, adversarial strategic verification, Operating-Manual updates, twice-escalated incidents | **Fable 5** | **You**, when one appears | Open a Fable session and describe it |

## Future / to-be-discussed (owner decisions, nothing started)

- More stack packs (Android for KKB, Vue for AlgoChanakya) — parked until a workflow needs one (YAGNI).
- Re-run `/model-parity-test` after any major Operating-Manual revision (judgment-triggered) —
  DONE for v2.0 (2026-07-13 mini-reexam, PR #363); next trigger = next major revision.
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
