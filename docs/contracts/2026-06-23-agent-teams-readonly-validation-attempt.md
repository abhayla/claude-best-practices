# Agent-teams read-only modes — validation attempt + firsthand findings (2026-06-23)

**Goal:** test path B — live-exercise the 4 never-tested read-only `--team` modes
(`review-gate`, `auto-verify`, `brainstorm` panel, `research-mode`) + instrument token cost,
with anti-fake-team ground-truth checks. Run by QA from the interactive hub session.

## Outcome: blocked on a real environmental boundary — but produced a valuable confirmed finding

The 4 read-only modes were **NOT** live-validated this pass, because **real agent teams cannot be
formed from a headless `claude -p` invocation** (the only non-interactive path drivable from a
Bash tool). This was the last session's claim; it is now **confirmed firsthand on CC v2.1.186** — and
the way it fails is itself the important result.

## The firsthand probe (the evidence)

Ran (env teams ON, demo settings, in-process):
```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude --settings .claude/.team-demo/settings.json \
  -p "Form a team. Spawn 2 teammates alpha and beta ... use the shared task list ... synthesize." \
  --output-format json
```

What happened — the run **looked like a passing team** but was not one:
- The `-p` lead created a shared task list: `TaskCreated`×2 + `TaskCompleted`×2 fired (real hook
  events, correct payload schema, captured in `.claude/.team-demo/payloads.log`).
- The JSON result **narrated** teammate output: *"Both shared-list tasks now show completed
  (alpha → #1, beta → #2) … alpha (unit tests): … beta (integration tests): …"* — `subtype:success`,
  `num_turns:8`.
- **BUT the anti-fake-team ground-truth check failed:** the new team dir
  `~/.claude/teams/84490178-…/` contains **only an empty `inboxes/` and NO `config.json`** — whereas
  a real team (`session-beb56590` from the prior parallel-build run) has a 7749-byte `config.json`
  with `members:[team-lead, ops, stats]`. The activity-log completions were `by=lead/unattributed`,
  not `by=alpha`/`by=beta`. **No teammate sessions ever spawned** — the lead did both tasks itself.

## Why this matters (3 confirmed lessons)

1. **`-p` confirmed no-team on v2.1.186.** Headless `-p` runs the task-list + hook machinery and
   will *narrate* teammates, but spawns **no real teammate sessions**. Real teams need an
   **interactive** (or agent-view-dispatched) session with the env var set — exactly the prior
   session's `claude --bg` executor note. (`claude --bg` is not a literal flag in v2.1.186; the
   mechanism is the interactive/agent-view background dispatch — `claude agents` is a TTY TUI.)
2. **The "narrated fake team" trap is REAL and easy to fall for.** A naive observer reading the
   `-p` result would have recorded a PASS. The `members > 1` / `config.json` check is the
   **necessary** defense — it caught a false positive here. The anti-fake-team gate in the `--team`
   skills is validated as load-bearing.
3. **The cost-instrumentation gap is STRUCTURAL, not an oversight.** `--output-format json`
   (which yields `total_cost_usd`) only works with `-p`; `-p` forms no real team. Therefore you
   **cannot** capture clean JSON cost for a *real* team via `-p`. Real-team cost must be summed from
   the lead + teammate session transcript `.jsonl` files under
   `~/.claude/projects/<proj>/<session>.jsonl` (each carries per-message `usage`). Document this as
   the cost method; the last session's "we forgot `--output-format json`" framing was incomplete —
   it would not have worked anyway.

## How to actually run test B (the unblock)

Real-team validation needs a **team-enabled interactive session**, which this QA session is not
(launched without the env var). Two ways:
- **(a)** Relaunch Claude Code with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (e.g. point it at
  `.claude/.team-demo/settings.json`), then invoke each read-only mode (`/brainstorm --team`,
  `/research-mode --team`, `/review-gate`, `/auto-verify --team`) on a real target. For each, verify
  ground truth: `~/.claude/teams/<session>/config.json` `members.length > 1` AND fresh
  `.claude/.team-activity.log` lines attributed `by=<teammate>` (not `lead/unattributed`).
- **(b)** Use the agent view (`claude agents`) interactively to dispatch a team-enabled background run.

Either way the verification rubric is the same: **config.json members > 1 + teammate-attributed
hook events = real; lead-only + narrated names = fake (reject).**

## First MEASURED real-team cost (the gap, now closed from existing data)

Applied the documented cost method to the prior REAL 4-member build team (lead + `ops`+`stats`+`verify`,
the mathkit Stage-C run) by summing per-message `usage` across the lead + teammate transcript `.jsonl`
files under `~/.claude/projects/.../subagents/`:

| Role | Total tokens (in+out+cache) | Output tokens |
|---|---|---|
| Lead | 3,111,584 (2.48M cache-read) | 56,913 |
| 3 teammates | 1,988,077 | 4,099 |
| **Grand total** | **5,099,661** | — |

- **Teammates added ~64% on top of the lead** (≈**1.64× total tokens** vs the lead's own consumption).
- This is **well below the 4–7× literature figure** — BUT this was a trivial 3-task build where teammates
  did little work; the multiplier scales with task/teammate count + context size, so 1.64× is a **floor for
  a tiny job**, not a refutation of 4–7× for real work. Most teammate cost is cache-reads (each reloading
  project context — the documented "≈4× at init" effect, smaller here because the job was tiny).
- Caveat: this is "team total vs the lead's tokens IN the team run," not vs a true solo-build baseline of
  the same task (no counterfactual captured). It is a real cost-SHAPE data point, not a clean A/B.
- **The method works** — `sum(usage)` over transcripts is the reliable way to instrument real-team cost
  (the `-p --output-format json` path can't, since `-p` forms no real team). Script:
  scratchpad `sum_team_cost.py` (ephemeral).

## Status

- 4 read-only modes: **NOT yet live-validated** (boundary above).
- Anti-fake-team gate: **validated** (caught a real false positive).
- `-p` no-team on v2.1.186: **confirmed firsthand.**
- Cost method for real teams: **documented** (sum transcript `.jsonl` usage; not `-p --output-format json`).
- Execute parallel-edit tier: unchanged — stays supervised (prior 1/3 finding).
