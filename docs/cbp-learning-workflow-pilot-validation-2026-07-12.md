# cbp-learning-workflow pilot validation — 2026-07-12

Evidence record for **#187 cluster 3** (owner-approved improvement-loop cycle 4):
`cbp-learning-workflow` v0.1.0, the hub's 8th marketplace plugin — the
`learning-self-improvement` workflow with its dispatch closure (`learn-n-improve`,
`skill-factory`, `test-knowledge`, `update-practices` + `context-reducer-agent`,
`session-summarizer-agent`).

## Boundary decisions

- **Companion, not duplicate:** `skill-authoring-workflow` (the learn → propose → author
  continuation) ships in `cbp-workflows`; declared as companion install, never re-shipped.
- **Shared sub-skill copies allowed:** `learn-n-improve` also ships in `loop-engineering` —
  included here per the cycle-1 self-containment rule (namespaced, direct dispatch target).
- **Process vs data:** the plugin brings the workflow; `.claude/learnings.json` and lesson
  files remain project-owned artifacts.
- No bundled config needed: the workflow's `workflow-contracts.yaml` read carries the
  "if absent, use the inline steps — self-contained" fallback in the core template already
  (unlike test-pipeline in cluster 2, no copy patch was required).

## Validation evidence (all gates green, 2026-07-12)

| Gate | Result |
|---|---|
| `claude plugin validate` | PASS |
| `validate_plugin_cleanroom.py cbp-learning-workflow` | **PASS** — all 5 skills served from the plugin alone |
| Full hub gate (dedup, secret scan, quality gate, pytest) | PASS — 1787 passed / 0 failed |
| **Real second-project install + E2E** | PASS — see method |

### Second-project method

Fresh throwaway project (`D:/Abhay/VibeCoding/cbp8-test`: a condensed real debugging-session
`notes.md`, own `git init`, **no `.claude/` at all**). Isolated `CLAUDE_CONFIG_DIR` →
marketplace add → `/plugin install cbp-learning-workflow@claude-best-practices` (v0.1.0,
enabled) → headless run of the installed `learn-n-improve` in session mode against the notes.

Observed: the skill created `.claude/learnings.json` from nothing and captured a fully
structured entry `L001` — error (message/file/context), fix (description + diff), lesson,
tags, `reuse_count`, `hub_pattern_link` — including the *wrong-first-fix* nuance from the
notes (bare try/except swallowing errors) folded into the lesson text. Step gating behaved
correctly for a 1-entry database (pattern detection @10 not triggered; constraint injection
skipped below reuse threshold; hub-pattern link null with no registry present). Final line:
`CAPTURED`.

Status vocabulary: **serve-validated AND second-project-install-exercised on day one**;
formal graduation-sweep entry (skeptic refutation pass) can be added at the next sweep.

## Remaining #187 expansion

1. Cluster 4 (final): `recommend.py` → plugin recommender (the #187 end-state), plus the
   session cluster remains covered by `branch-lifecycle`.
