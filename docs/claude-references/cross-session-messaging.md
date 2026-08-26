# Cross-Session Messaging (Claude Code v2.1.224+)

> Docs-cache capture, fetched 2026-08-09 from code.claude.com/docs/en/cross-session-messaging.md
> + changelog (v2.1.224 2026-08-07, v2.1.225 2026-08-08). Announcement: @ClaudeDevs X post 2085817074816070014.

## What it is

Sessions message each other via two tools: `ListAgents` (discover reachable sessions) and
`SendMessage` (deliver plain text to a session addressed by NAME — `/rename`, `--name`, or
auto-derived from the cwd folder). Invoked by natural language, not a slash command;
`/list-agents` (alias `/peers`) is inspection only. The message is a fresh summary written by
the sending Claude — never conversation history or files (resume the session for full context).

## Key facts

- **Platform: macOS + Linux (incl. WSL2) ONLY. NOT native Windows.**
- Same-machine transport = per-session Unix socket (never Anthropic servers), requires shared
  filesystem visibility. Cross-machine routes via Remote Control; v2.1.225 added
  open-by-name to remote sessions (before that, remote could only reply).
- Headless `claude -p`: receives (appears in ListAgents) unless bare mode, BUT cannot render the
  approval dialog — unattended acceptance requires `crossSessionInbound: "accept"` in its
  settings, else held messages expire (default 5 min). Headless-as-SENDER: UNVERIFIED in docs.
- Inbound control: `crossSessionInbound` accept/hold/refuse; incoming text can never approve
  permission prompts, change config, or execute command-like text; dedup + rate-limit built in.
- Disabled when feature-flag traffic is suppressed (`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`,
  `DO_NOT_TRACK`, etc.).

## Hub adoption decision (2026-08-09)

**REJECT-for-now — platform-blocked.** The owner's interactive sessions run on native Windows
(PC + Windows VPS), where the feature does not exist (installed CC 2.1.226 confirms version is
current; OS is the blocker). The Hostinger Linux VPS could use it, but no owner-facing session
runs there. Assessed value when unblocked: convenience layer for owner-context handoff between
interactive sessions (e.g. project session → `/get-work-done` intake session, and completion
pings back) — worth a MEASURE-FIRST trial then. Explicitly NOT fleet plumbing: the GetWorkDone
bus (durable files + git + evidence) beats ephemeral messages for queue/worker coordination on
crash-survival and auditability, and held-message expiry makes unattended delivery fragile.

**Revisit trigger:** a Claude Code changelog entry adding native-Windows support for
cross-session messaging → re-run the intake-handoff trial (/review-new-claude-features).

## Revisit (2026-08-26, /review-new-claude-features dry-run)

**Trigger fired.** v2.1.239 (2026-08-21) changelog: "Windows: cross-session messaging is now
available, so Claude Code sessions across your machines can message each other with
`SendMessage` and find each other with `ListAgents`, as on macOS and Linux." The platform
blocker this REJECT-for-now was keyed on is resolved.

**Updated verdict: MEASURE-FIRST** (was REJECT-for-now). Per the 2026-08-09 assessment above,
the plausible value was already scoped as a convenience layer for owner-context handoff between
interactive sessions (project session → `/get-work-done` intake session, completion pings back)
— never as fleet plumbing (the GetWorkDone durable-file/git bus still wins on crash-survival and
auditability for queue/worker coordination; held-message expiry keeps unattended delivery
fragile). Next step before flipping to ADOPT: run one live intake-handoff trial on this Windows
VPS and confirm `SendMessage`/`ListAgents` actually reach across the two sessions this session's
own SessionStart banner reported sharing a working tree with. Not run in this dry-run pass
(report-only; no code/config changes beyond this doc per the skill's `--dry-run` contract).
