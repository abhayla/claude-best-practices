# G6 graduation validation — 2026-07-12 (plugins 6–9)

Second formal graduation sweep (method per `docs/g6-graduation-2026-07-10.md`), covering the
four plugins shipped in the 2026-07-12 improvement-loop cycles: `cbp-workflows`,
`cbp-build-test-workflows`, `cbp-learning-workflow`, `cbp-react-stack`. Bar: *"In a
clean-room second project, the INSTALLED plugin ALONE (no provisioned `.claude/` copies, no
hub tree) serves its skills/agents through a real exercise of its primary capability"* —
plus a context-isolated skeptic dispatched per plugin with a brief to REFUTE graduation.

## Method

Each plugin's original day-one exercise ran in a fresh throwaway project OUTSIDE the hub tree
with a fully **isolated `CLAUDE_CONFIG_DIR`** (stronger than the 2026-07-10 sweep, which used
the machine's registered marketplace): `claude plugin marketplace add <hub>/plugins` → real
`/plugin install` → headless capped session exercising the primary capability. Four skeptic
subagents (sonnet, context-isolated, briefed to refute; default refuted=true) then inspected
the surviving on-disk evidence.

**The sweep worked as designed — one refutation.** The learning plugin's first audit was
REFUTED (high confidence): the artifact was schema-perfect, but the isolated install config
had been deleted during cleanup, so nothing on disk proved the *installed plugin* (vs. the
machine's ubiquitous provisioned copies of the same skill) produced it. Both weak cases were
re-run with **preserved deterministic evidence**: the stream-json transcript (whose `init`
event lists the plugin + marketplace source + path), the preserved install config
(`installed_plugins.json` with `installedAt` + `gitCommitSha`), and the namespaced Skill
invocations in the transcript. Skeptics re-audited against the new evidence — and one skeptic
independently verified the recorded `gitCommitSha` against github.com via a live API call
(external ground truth a fabricated transcript could not produce).

## Verdict table

| Plugin | Verdict | Confidence | Key evidence |
|---|---|---|---|
| `cbp-workflows` | **GRADUATED** | high (re-audit; first pass medium) | Transcript init lists plugin@marketplace; namespaced `cbp-workflows:code-review-workflow` Skill tool_use; findings match the real calc.py diff (ZeroDivisionError); preserved config `installedAt` 10:55:47Z clusters with transcript 10:55:56Z; installed `gitCommitSha` (PR #342 merge) externally verified |
| `cbp-build-test-workflows` | **GRADUATED** | high (first pass) | Full two-run event trail on disk (`events.jsonl`: LOCK_ACQUIRED → PIPELINE_IN_PROGRESS_REFUSED → LOCK_OVERRIDE_FORCED → SCOUT → WAVE1 → JOIN → DONE); verdict JSON records `config_source: bundled_default`; 3/3 pytest evidence; no `.claude/` anywhere in project |
| `cbp-learning-workflow` | **GRADUATED** | high (re-run after refutation) | Transcript init lists plugin; 3 namespaced `cbp-learning-workflow:learn-n-improve` invocations; L001 derives from notes.md; preserved config `installedAt` 10:52:32Z; `gitCommitSha` d2d205f live-verified as ancestor of origin/main |
| `cbp-react-stack` | **GRADUATED** | high (first pass) | Git history proves failing-then-fixed sequence (HEAD lacks setupFiles/setup.ts; working tree has the canonical RTL-cleanup fix); live `npx vitest run` re-verified 2/2; composition with `cbp-build-test-workflows` proven (cross-plugin namespaced skill use) |

## Preserved evidence locations

- `D:/Abhay/VibeCoding/cbp8-test2/graduation-transcript.jsonl` + `.claude/learnings.json` (learning re-run)
- `D:/Abhay/VibeCoding/cbp-plugin-test/graduation-transcript.jsonl` + `test-results/code-review-verdict.json` (workflows re-run)
- `D:/Abhay/VibeCoding/cbp7-test/.workflows/testing-pipeline/events.jsonl` + `test-results/` + `test-evidence/` (build-test)
- `D:/Abhay/VibeCoding/cbp9-test/` git history + `src/test/setup.ts` (react composition)
- Preserved isolated configs: `%LOCALAPPDATA%/Temp/claude/grad-learning-cfg`, `grad-review-cfg` (credentials removed on next cleanup; plugin registrations retained)

## Outcome

**All 9 marketplace plugins are now G6-graduated** (5 from the 2026-07-10 sweep + these 4).
The G6 DoD count bar (≥9 validated, multi-project-tested) is met with the graduation
vocabulary satisfied, not just the count.

## Lesson (fed to the process)

Cleanup destroyed evidence: deleting the isolated install config immediately after an
exercise erased the only install trace, causing a justified refutation. Rule going forward —
**graduation exercises preserve their transcript + install config until the skeptic pass is
complete**; the transcript's `init` plugins array + `installed_plugins.json` `gitCommitSha`
(externally verifiable) are the canonical proof pair.
