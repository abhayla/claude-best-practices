# Next-session contract — build+test a downstream "todo" app using AGENT TEAMS (no exceptions)

Owner-set goal (2026-06-24, carried to the next session). This is the authoritative brief; the pasted
kickoff prompt points here.

## The goal
Build a real downstream throwaway product — a **TODO tracker app** — in an **isolated sibling folder**
(`../todo/`, its own git, OUTSIDE this hub tree per `core/.claude/rules/product-incubation.md`), and in
doing so **exercise every hub workflow end-to-end DRIVEN BY REAL AGENT TEAMS**. This is the real-world
validation harness for the agent-team work that shipped in PR #201 (merge `2df5cb5`).

## THE HARD RULE (no exceptions)
- **Every workflow stage that has a `--team` mode MUST run as a REAL agent team** — verified by ground
  truth, not narration.
- **NO fallback, NO excuses.** "Agent teams aren't enabled," "I took an alternate path," "subagents are
  cheaper/sufficient," "the lead did it solo" → all UNACCEPTABLE. If a stage cannot form a real team,
  the **TEST IS FAILED — STOP and report the failure. Do NOT continue with a workaround.**
- Read-only review/research stages AND parallel-edit build stages all run as teams. `writing-plans` is the
  only legitimate non-team (single-owner plan by design) — everything else teams.

## The PROVEN setup (this is how agent teams actually work here — use it)
Agent teams need an interactive TTY; headless `claude -p` forms NO team. On this Windows box the proven
path (no WSL, no admin) is **psmux + the harness**:
- **psmux** (native Windows ConPTY tmux clone): `C:\Users\itsab\.local\psmux\psmux.exe` (installed).
- **Harness:** `scripts/run_agent_team.sh "<prompt>" <label> <timeout_sec> [workdir_win]` — launches a
  claude lead inside a psmux session, injects a TEAM-LEAD spawn-first system prompt, and verifies a real
  team formed via the durable `subagents/` transcript dir. Use it (or replicate its mechanism) for every
  team stage in the todo build.
- **Demo/settings rig:** `.claude/.team-demo/settings.json` (sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
  + `teammateMode: in-process` + the 3 team-* hooks that log to `.claude/.team-activity.log`).

## GROUND-TRUTH verification (how to know a team is REAL, not narrated)
A stage PASSES only with one of these DURABLE signals (config.json is EPHEMERAL — cleaned on exit — do
NOT rely on it):
1. The lead session's transcript has a `subagents/` dir with **≥2 teammate transcripts**
   (`~/.claude/projects/<proj-slug>/<session>/subagents/*.jsonl`) — catches agent-type + worktree teammates.
2. `.claude/.team-activity.log` shows teammate-attributed events for the session
   (`TaskCompleted by=<teammate>` or `TeammateIdle teammate=<name>`, NOT `by=lead/unattributed`).
3. The agent panel shows `◯ <teammate>` rows (lead + ≥1 real teammate).
A lead doing the work solo / via flat `Agent()` subagents / via the native Workflow tool = NOT a team = FAIL.
For parallel-edit (build) teams, also assert **zero file-collision** (disjoint files across worktrees).

## Load-bearing gotchas (learned the hard way — don't repeat)
- **Never redirect the lead's stdout** (`claude ... > file`) — that makes stdout non-tty → no team. Let it
  write to the psmux pane; read via `capture-pane`.
- **Clear `PSMUX_SESSION`/`TMUX`/`TMUX_PANE`** in the launched cmd (else agent-teams thinks it's nested →
  refuses). The harness already does this.
- **Pre-trust new folders** in `~/.claude.json` (`hasTrustDialogAccepted: true`) for the todo/scratch dir,
  else the lead blocks on a folder-trust prompt.
- **The `--append-system-prompt` TEAM-LEAD anti-deliberation injection is decisive** — without it, leads in
  this heavy-governance hub deliberate into solo/subagent paths instead of spawning.
- Teams cost ~4–7× tokens; give a generous timeout (≥560s) per team stage.

## Key references
- Compliance audit + full evidence matrix: `docs/contracts/2026-06-24-agent-team-compliance-audit.md`
- Read-only mode runbook: `docs/contracts/2026-06-23-agent-teams-readonly-test-runbook.md`
- Selection rule (subagent vs team vs worktree): `core/.claude/rules/agent-team-selection.md`
- Master tracker: `plans/agent-teams-incorporation.md`
- Feature reference (cached): `docs/claude-references/agent-teams.md`
- The 6 team-enabled build skills (all `--team` BINDING + spawn-first as of `2df5cb5`):
  code-review-workflow, review-gate, auto-verify, brainstorm, research-mode, development-loop,
  executing-plans, implement (+ writing-plans = correct non-team).

## Definition of done (next session)
The todo app is built through the hub workflows where **each team-capable stage formed a REAL,
ground-truth-verified agent team** (or the run STOPPED at the first stage that couldn't, reported FAILED).
Record per-stage team evidence (session id + subagents count / teammate events) as you go.
