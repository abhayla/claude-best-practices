# Contract template (fill, then save to `docs/contracts/YYYY-MM-DD-<slug>.md`)

Replace every `<…>` placeholder with a concrete, pre-made decision. The STEP 4.5
gate greps for leftover `<…>` / `decide whether` / `PASTE` — none may survive.
Paste the §0.1/§0.2/§0.3 blocks and the verification pointer block from
`baked-in-rules.md` where marked.

---

```markdown
# Contract: <mission in 5-8 words>

**Executor:** /goal (built-in autonomous run)   ·   **Created:** <YYYY-MM-DD>
**Mission:** <one paragraph: the objective + what "done" looks like>

## §0.1 Worktree isolation
<PASTE the §0.1 block from baked-in-rules.md — adapt <repo>/<slug>/<feature-branch>>

## §0.2 Idempotency preflight
<PASTE the §0.2 block — name this project's coverage/gap ledger doc explicitly>

## §0.3 Progress log
<PASTE the §0.3 block — progress path docs/contracts/.run/<slug>-PROGRESS.md>

## Scope boundary
- **In scope:** <dirs/files this run may touch>
- **Out of scope:** <dirs/files it must NOT touch; boundary contracts that apply>
- **Goal type:** <fresh build | propagation/refactor | bug-fix loop | migration | audit>

## Context to read first
- `<path>` — <why; any gotcha (e.g. a CWD trap, a generated file not to edit)>
- `<path>` — <why>

## Pre-made design decisions (the run must NOT pause on these)
1. <decision> — <chosen value + one-line why>
2. <decision> — <chosen value + one-line why>
(Each is a DECISION, not a menu. This is the bulk of a build contract.)

## Stages
### Stage A: <title>
- **Do:** <concrete steps with real paths/commands>
- **Acceptance:** <observable signal this stage is done — ACTION + COMPLETENESS BAR>
### Stage B: <title>
- **Do:** <…>
- **Acceptance:** <…>

## Verification gates
<PASTE the verification pointer block from baked-in-rules.md — adapt:
 - the static-gate commands for each tree the change touches
 - the persistence-verification signal (API read-back / storage round-trip / file re-read)
 - the screens/routes/consumers named for the cross-page sweep>

## Failure-recovery budget
<PASTE the failure-budget block from baked-in-rules.md — tune the numbers>

## Commit + push policy
- **Granularity:** <one commit per stage | per logical change>
- **Message format:** Conventional Commits (`core/.claude/rules/git-collaboration.md`)
- **Branch / push target:** <feature-branch> → <main? PR?> (per the project's git authority)
- **Do NOT stage:** <unrelated untracked items the working tree may carry>

## Definition of Done (DoD verbs are load-bearing — ACTION + COMPLETENESS BAR)
- [ ] <verb + completeness bar — e.g. "compute and display X on the default view; rendered value matches the API within 1%">
- [ ] <…>
- [ ] All baked-in verification gates passed (or each skip recorded with reason)
- [ ] Final report written (below)
- [ ] Run-end SUMMARY (DONE / PENDING / BLOCKED / NEXT) in PROGRESS.md + final report

## Guardrails (hard stops)
- No new dependencies without <explicit allowance>.
- No design reinvention — use the named existing components/patterns.
- No synthetic/fake data; surface uncertainty as `**Assumption:** X`.
- <project-specific boundary, e.g. never write outside the in-scope dirs>

## Final report (what the closing report must contain)
- What shipped, per stage, with commit SHAs.
- Skipped (already covered) list from the §0.2 preflight.
- LEARNINGS TO FOLD BACK (PROPOSE-only — routed per `learnings-routing.md`).
- The DONE / PENDING / BLOCKED / NEXT summary.

## Authorization trail (decisions resolved in the interview)
| Fork | Decision | Why |
|---|---|---|
| <fork> | <decision> | <reason> |

## References (load transitively)
- `core/.claude/rules/{supervisor-verification, independent-test-verification, output-plausibility-verification, e2e-persistence-verification, dod-verbs, bug-triage-discipline, testing, e2e-best-practices, git-worktrees, learnings-routing}`
- `<any project-specific rule/doc the run needs>`
```
