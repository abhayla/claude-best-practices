# Runbook — live-test the 4 read-only `--team` modes (run in a teams-enabled session)

**Prereq:** session launched with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (in-process is the
v2.1.186 Windows default). Confirm with: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` → `1`.
Optionally add `--settings .claude/.team-demo/settings.json` to also capture hook lines into
`.claude/.team-activity.log` + `.claude/.team-demo/payloads.log`.

## Verification gate (apply to EVERY mode — the hardened, firsthand-confirmed version)

A mode PASSES only if a REAL team formed AND produced usable output:
1. **Real team:** `~/.claude/teams/<session>/config.json` EXISTS with `members.length > 1`
   (lead + ≥1 teammate). A dir with only `inboxes/` and no `config.json` = NO real team.
2. **Teammate-attributed work:** `.claude/.team-activity.log` shows `TaskCompleted ... by=<teammate>`
   (NOT `by=lead/unattributed`). Hooks firing alone is NOT sufficient (a lead-only run fires them).
3. **Usable output:** the mode's deliverable shows genuine cross-challenge / multi-source / multi-area
   work — not the lead narrating teammate names.
4. **Cost:** sum `usage` across the lead + `subagents/*.jsonl` transcripts under
   `~/.claude/projects/<proj>/<session>...` (reuse the `sum_team_cost.py` approach).

Baseline before each run: `ls ~/.claude/teams/` and `wc -l .claude/.team-activity.log`.

## The four tests (each on a minimal REAL target)

| # | Mode | Invocation | Minimal real target | Expect (read-only tier) |
|---|---|---|---|---|
| 1 | `research-mode --team` | `/research-mode --team` | "Enumerate the v2.1.18x agent-teams constraints + cost levers" | 2–4 teammates, each a different modality (codebase / web / docs), lead synthesizes sources |
| 2 | `brainstorm --team` | `/brainstorm --team` | "Should the Execute `--team` tier auto-finalize or stay supervised?" | advisor panel (simplicity / risk / maintainability lenses) that cross-challenge |
| 3 | `code-review-workflow --team` (covers `review-gate`) | `/code-review-workflow --team` | review THIS branch's gate-hardening diff (`git diff main...HEAD -- core/.claude/skills/`) | correctness / security / tests reviewers share + challenge before synthesis |
| 4 | `auto-verify --team` | `/auto-verify --team` | the repo test suite split into disjoint areas | each teammate runs a disjoint test area, read-only, verdict re-checked |

## Per-test record (fill on execution)

For each: `members` count, teammate names, `by=<teammate>` completions seen (Y/N), usable-output (Y/N),
total tokens (lead + teammates), and PASS/FAIL against the gate. Roll up into the validation-attempt doc
(`2026-06-23-agent-teams-readonly-validation-attempt.md`).

## Guardrails
- Read-only tiers only here — no Execute parallel-edit (that stays supervised, prior 1/3 finding).
- If any run shows lead-only `members` / `lead/unattributed` completions → record FAIL (narrated fake team),
  do not count it as a pass.
- Keep targets small (cost is ~linear in teammates × context; start with 2–3 teammates).
