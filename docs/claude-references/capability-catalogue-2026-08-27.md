# Claude Code capability catalogue — verified 2026-08-27

Source of truth: `https://code.claude.com/docs/llms.txt` (202-page index) + ~30 live page fetches + raw CHANGELOG.md, all fetched 2026-08-27 by a web-research subagent. Rows marked `cache-only` come from older snapshots in this directory and were NOT re-verified. Purpose: the "available" side of `scripts/feature_utilization.py` — what exists, so "never used" can be computed against reality instead of memory.

| Capability | What it does | How invoked | Best used for | Source (code.claude.com/docs/en/…) | Status |
|---|---|---|---|---|---|
| Skills | `SKILL.md` procedures loaded on demand or auto-invoked from `description`; custom commands merged into skills | `/skill-name` or auto | Repeatable multi-step procedures | skills | verified |
| Subagents (custom agents) | Isolated-context agents: `name, description, tools, model, permissionMode, skills, memory, isolation, maxTurns, background` | auto-delegation, `@"name (agent)"`, `--agent`, `.claude/agents/*.md` | Delegated work where only the output matters | sub-agents | verified |
| Model-per-agent | `model: sonnet/opus/haiku/inherit`, `CLAUDE_CODE_SUBAGENT_MODEL` | frontmatter / CLI | Cheap vs expensive routing | sub-agents | verified |
| Agent teams (experimental) | Lead + teammates with shared task list + mailboxes | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` then natural language | Competing-hypothesis review, cross-layer parallel builds | agent-teams | verified |
| Dynamic workflows | Claude-authored JS orchestration fanning out many subagents outside your context, resumable | "use a workflow" / `ultracode` / `/effort ultracode` / `/deep-research`; `/workflows` | Codebase-wide audits, migrations, cross-checked research | workflows | verified |
| Plan mode | Read-only mode; plan before edits | `Shift+Tab`, `--permission-mode plan`, agent `permissionMode: plan` | Risky/complex changes | permission-modes | verified |
| Worktrees | Isolated git worktree per session/subagent | `claude --worktree`, `EnterWorktree`, agent `isolation: worktree` | Parallel edits without collisions | worktrees | verified |
| Hooks (31 events) | SessionStart, Setup, UserPromptSubmit, UserPromptExpansion, PreToolUse, PermissionRequest, PermissionDenied, PostToolUse, PostToolUseFailure, PostToolBatch, Notification, MessageDisplay, SubagentStart, SubagentStop, TaskCreated, TaskCompleted, Stop, StopFailure, TeammateIdle, InstructionsLoaded, ConfigChange, CwdChanged, DirectoryAdded, FileChanged, WorktreeCreate, WorktreeRemove, PreCompact, PostCompact, Elicitation, ElicitationResult, SessionEnd | `settings.json` hooks / plugin `hooks/hooks.json`; `/hooks` | Deterministic enforcement/logging | hooks | verified |
| Memory — CLAUDE.md tiers | managed → user → project → `CLAUDE.local.md`, concatenated; `.claude/rules/*.md` path-scoped | auto; `/init`, `/memory` | Standing instructions | memory | verified |
| Memory — auto memory | Claude writes user/feedback/project/reference notes to `~/.claude/projects/<p>/memory/` | on by default; `autoMemoryEnabled` | Cross-session corrections | memory | verified |
| Plugins | Dir with `.claude-plugin/plugin.json`; skills/agents/hooks/MCP/LSP/monitors/settings | `claude plugin init`, `--plugin-dir`, `/plugin install` | Versioned sharing | plugins | verified |
| Marketplaces | Plugin catalogs (`claude-plugins-official`, `claude-community`, git/local/URL) | `/plugin marketplace add`, `/plugin` | Discovering/installing plugin sets | discover-plugins | verified |
| MCP | External tools/data via open standard | `claude mcp add`, `.mcp.json`, `/mcp` | Live external systems | mcp | verified |
| Scheduled routines (cloud) | Recurring cloud-run tasks, min 1h, API/GitHub triggers | `/schedule` | Unattended automation, machine off | routines | cache-only 2026-06-27 |
| Desktop scheduled tasks | Local recurring tasks, min 1 min | Desktop app | Local-file recurring work | desktop-scheduled-tasks | unverified |
| `/loop` | Session-scoped repeating prompt, fixed or self-paced, 7-day expiry | `/loop [interval] [prompt]` | In-session polling | scheduled-tasks | verified |
| `/goal` | Work across turns toward a condition | `/goal <condition>` | Outcome pursuit | goal | cache-only 2026-06-23 |
| Remote Control | Phone/browser drives a local session | admin-enabled; connect from claude.ai/mobile | Continue from phone | remote-control | verified (partial) |
| Cross-session messaging | Sessions message each other w/o a team | `/list-agents`, SendMessage | Loose coordination | (cache) cross-session-messaging.md | cache-only 2026-07-10 |
| Background tasks / agent view | Detached subagents/sessions; `/tasks` | `run_in_background`, `background: true`, `/tasks`, `claude --bg` | Long work you don't babysit | (cache) agent-view.md | cache-only 2026-06-22 |
| Artifacts | Publish session output as live page on claude.ai | `/artifacts`; Artifact tool | Dashboards, shareable reports | artifacts | verified |
| Checkpoints / `/rewind` | Auto file-state snapshots per prompt (100 / 30 days); restore code/conversation | `/rewind`, double-Esc | Undo bad edits, free context | checkpointing | verified |
| Output styles | System-prompt personas: Default/Proactive/Concise/Explanatory/Learning + custom | `/config`, `outputStyle`, `.claude/output-styles/*.md` | Consistent voice | output-styles | verified |
| Effort controls | low/medium/high/xhigh/max/ultracode; ~6x cost swing medium→max | `/effort`, `--effort`, `Meta+T` | Cost vs capability per pass | cli-reference, workflows | verified |
| Fast mode | Opus-only, up to 2.5x faster, premium rate | `/fast` | Latency-bound iteration | fast-mode | verified |
| Headless `claude -p` + Agent SDK | Non-interactive CLI; TS/Python SDK | `claude -p`, `--output-format json` | CI, cron, products | cli-reference | verified |
| `--resume` / `--continue` / `--fork-session` / `--from-pr` | Resume/branch sessions | CLI flags | Returning to work | sessions | verified |
| Sessions: `/rename` `/branch` `/export` | Manage many sessions; picker Ctrl+A / Ctrl+W | slash cmds | Parallel long conversations | sessions | verified |
| Claude in Chrome | Drive a real logged-in Chrome tab; screenshots, console, GIF | `claude --chrome`, `/chrome` | Live web-app debugging | chrome | verified |
| Computer use (native apps) | Native macOS app control | — | Beyond-browser automation | computer-use | unverified |
| `/init` | Generate/improve CLAUDE.md; imports Cursor/Copilot/AGENTS.md | `/init`, `CLAUDE_CODE_NEW_INIT=1` | Bootstrapping memory | memory | verified |
| `/security-review` | Diff security scan | `/security-review` | Pre-commit | commands | verified |
| `/simplify` | Cleanup-only pass (bug hunting moved to `/code-review --fix`, v2.1.154+) | `/simplify` | Style/cleanup | code-review | verified |
| `/code-review` (+ `ultra`) | Background subagent diff/PR review; `ultra` = cloud multi-agent; `--fix/--comment/--post` | `/code-review [target]`, `/code-review ultra` | Correctness bugs pre-merge | code-review | verified |
| Code Review GitHub App | Org-level multi-agent PR review, ~$15-25/review, Team/Enterprise | `@claude review` | Always-on PR review | code-review | verified |
| `/fewer-permission-prompts` | Transcript-derived allowlist | slash cmd | Reduce friction | commands | verified |
| Keybindings | `~/.claude/keybindings.json`, contexts | `/keybindings` | Ergonomics | keybindings | verified |
| Vim mode | Modal prompt editing | `/config` | Vim users | keybindings | verified |
| Statusline | Custom bottom bar from shell script | `/statusline` | Cost/context glance | statusline | verified (partial) |
| Permissions | allow/ask/deny rules | `/permissions`, settings | Unattended control | permissions | verified (partial) |
| Permission modes | default/acceptEdits/plan/auto/dontAsk/bypassPermissions | `Shift+Tab`, `--permission-mode` | Oversight vs autonomy | permission-modes | verified (partial) |
| Sandbox (Bash) | OS-enforced FS/network isolation | `/sandbox` | Autonomous Bash with hard boundary | sandboxing | verified (partial) |
| Settings scopes | managed → user → project → local; `--settings` | files / `/config` | Layered config | settings-reference | unverified |
| Image/PDF input | Paste/attach images, PDFs | `Ctrl+V`, `@file` | Screenshots, specs | keybindings (imagePaste) | verified (partial) |
| Deep-links | Launch a session from a URL | link scheme | Embedding | deep-links | cache-only 2026-06-23 |

Not fetched this run (exist in the index): computer-use, sandbox-environments, cloud/self-hosted environments, settings-reference full text, CI integrations, analytics, costs, prompt-caching, context-window, large-codebases, multi-agent-best-practices, best-practices, model-config, auto-mode-config, headless, schedule-wakeup-tool (several cached June/July).

## Added / materially changed in the last ~60 days (CHANGELOG, tail only — file truncated)

- 2.1.247 — SendFeedback tool; `/claude-api cost-optimize`; subagent fallback-model chain on 404; Sonnet 5 auto-compact at full 1M; cross-session messages collapsed by default.
- 2.1.246 — Bash wildcard allow-rule warnings; auto-mode tab in `/permissions`; workflow subagent restart confirmation.
- 2.1.243 — loop metrics in `/usage`; `modelPicker` setting; org prompt-cache TTL; model+effort per subagent in `/tasks`.
- 2.1.238–241 — US-only-inference cost premium shown; `/claude-api upgrade`; cloud-session plugin sync (`@synced`); `keybindingFlavor`; marketplace `headersHelper`.
- 2.1.237 — prompt caching for gateways; built-in **Concise** output style.
- 2.1.236 — `ANTHROPIC_DEFAULT_MODEL`; cross-session `notify_when_idle`.
- Evolving: fast mode (Opus 5 default since 2.1.219), agent teams (TeamCreate/TeamDelete removed 2.1.178), dynamic workflows (`ultracode` 2.1.202+), `/code-review` background-by-default 2.1.218 + `ultra`/`--post` 2.1.227.
