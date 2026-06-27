Source: https://code.claude.com/docs/en/permission-modes
Fetched: 2026-06-27

# Choose a permission mode

> Control whether Claude asks before editing files or running commands. Cycle modes with Shift+Tab in the CLI or use the mode selector in VS Code, Desktop, and claude.ai.

Permission modes control how often Claude pauses to approve an action (file edit, shell command, network request).

## Available modes

| Mode | What runs without asking | Best for |
| :--- | :--- | :--- |
| `default` | Reads only | Getting started, sensitive work |
| `acceptEdits` | Reads, file edits, common filesystem commands (`mkdir`, `touch`, `mv`, `cp`, etc.) | Iterating on code you're reviewing |
| `plan` | Reads only | Exploring a codebase before changing it |
| `auto` | Everything, with background safety checks | Long tasks, reducing prompt fatigue |
| `dontAsk` | Only pre-approved tools | Locked-down CI and scripts |
| `bypassPermissions` | Everything | Isolated containers and VMs only |

In every mode except `bypassPermissions`, writes to protected paths are never auto-approved. Modes set the baseline; layer permission rules on top. Deny rules and explicit ask rules apply in EVERY mode, including `bypassPermissions`.

## Switch permission modes

- **CLI during a session**: `Shift+Tab` cycles `default` → `acceptEdits` → `plan`. `auto` appears when account meets requirements (opt-in prompt); `bypassPermissions` after starting with `--permission-mode bypassPermissions` / `--dangerously-skip-permissions`; `dontAsk` never in cycle (set with `--permission-mode dontAsk`).
- **At startup**: `claude --permission-mode plan`.
- **As default**: `permissions.defaultMode` in settings. `--permission-mode` also works with `-p` for headless.

## acceptEdits mode

Create/edit files in the working dir without prompting; also auto-approves `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` (and safe env-var / `timeout`/`nice`/`nohup` wrappers) on in-scope paths. Paths outside scope, protected-path writes, and all other Bash still prompt.

## plan mode

Research and propose without making changes; reads + explores + writes a plan, no source edits. Enter with `Shift+Tab` or prefix a prompt with `/plan`. On approval, choose: start in auto mode / accept edits / review each edit / keep planning / refine with Ultraplan.

## Auto mode (eliminate prompts)

> **Note:** Auto mode requires Claude Code v2.1.83 or later.

Claude executes without routine permission prompts; a separate **classifier model** reviews actions before they run, blocking anything that escalates beyond your request, targets unrecognized infrastructure, or appears driven by hostile content Claude read. Explicit ask rules still force a prompt. Auto mode also nudges Claude to keep working without stopping for clarifying questions (still asks when the prompt/skill explicitly relies on it). For stronger autonomous behavior while KEEPING prompts, use the Proactive output style.

> **Warning:** Auto mode is a research preview. It reduces prompts but does not guarantee safety.

**Requirements (all):** All plans; on Team/Enterprise an Owner must enable it (or lock off via `permissions.disableAutoMode: "disable"`); **Model**: Anthropic API → Claude Opus 4.6+ or Sonnet 4.6 (on Bedrock/Vertex/Foundry only Opus 4.7 and Opus 4.8); older models (Sonnet 4.5, Opus 4.5, Haiku, claude-3) unsupported; Provider: default on Anthropic API, else set `CLAUDE_CODE_ENABLE_AUTO_MODE`.

`defaultMode: "auto"` is IGNORED from `.claude/settings.json` / `.claude/settings.local.json` (v2.1.142+) so a repo can't grant itself auto mode — set it in `~/.claude/settings.json`.

### What the classifier blocks by default

Trusts working dir + repo's configured remotes; everything else is external until you configure trusted infrastructure (see auto-mode-config.md).

**Blocked by default:** download-and-execute (`curl | bash`); sending sensitive data to external endpoints; production deploys/migrations; mass deletion on cloud storage; granting IAM/repo permissions; modifying shared infra; irreversibly destroying pre-session files; **force push, or pushing directly to `main`**; (v2.1.182+) `git reset --hard`, `git checkout -- .`, `git restore .`, `git clean -fd`, `git stash drop`, `git stash clear`; `git commit --amend` when HEAD wasn't created this session; `terraform/pulumi/cdk/terragrunt destroy` and applying a destroying plan.

**Allowed by default:** local file ops in working dir; installing declared dependencies; reading `.env` and sending creds to their matching API; read-only HTTP; pushing to the branch you started on or one Claude created.

### Boundaries you state in conversation
The classifier treats stated boundaries ("don't push", "wait until I review before deploying") as block signals; stays in force until lifted. NOT stored as rules — re-read from the transcript each check, so a boundary can be LOST if context compaction removes the message. For a hard guarantee, add a deny rule.

### When auto mode falls back
Denied actions appear in `/permissions` → Recently denied (press `r` to retry). **If the classifier blocks 3 times in a row OR 20 times total, auto mode pauses and resumes prompting** (thresholds not configurable; any allowed action resets the consecutive counter). In headless `-p` mode, repeated blocks abort the session (no user to prompt).

**How the classifier evaluates (decision order, first match wins):** (1) allow/deny rules resolve immediately except protected-path writes; (2) read-only + working-dir edits auto-approved except protected paths; (3) everything else → classifier; (4) on block, Claude gets the reason and tries an alternative. On entering auto mode, broad allow rules granting arbitrary code execution are DROPPED (`Bash(*)`, `PowerShell(*)`, wildcarded interpreters, package-manager run, `Agent` allow rules); narrow rules like `Bash(npm test)` carry over; dropped rules restored on leaving auto mode. The classifier sees user messages, tool calls, and CLAUDE.md — **tool RESULTS are stripped** (hostile file/web content can't manipulate it directly; a server-side probe scans incoming results). **Subagents**: classifier checks at 3 points — before spawn (task description; v2.1.178+), during (each action, ignoring the subagent's `permissionMode`), and on finish (full action history → may prepend a security warning). **Cost/latency**: classifier runs on a server-configured model independent of `/model`; calls count toward token usage; reads/working-dir edits skip it.

## dontAsk mode
Auto-denies every tool call that would otherwise prompt; only `permissions.allow` rules + read-only Bash execute. Fully non-interactive for CI.

## bypassPermissions mode
Disables prompts + safety checks (incl. protected paths as of v2.1.126). Explicit ask rules still prompt; `rm -rf /` / `rm -rf ~` still prompt as a circuit breaker. Containers/VMs only. Can't enter from a session not started with an enabling flag. Refuses to start as root/sudo (skipped inside a recognized sandbox). No protection against prompt injection — prefer auto mode for background safety with fewer prompts.

## Protected paths

Writes never auto-approved (every mode except `bypassPermissions`): `default`/`acceptEdits`/`plan` → prompted; `auto` → routed to classifier; `dontAsk` → denied; `bypassPermissions` → allowed. `permissions.allow` does NOT pre-approve protected-path writes (safety check runs first). Protected dirs include `.git`, `.config/git`, `.vscode`, `.idea`, `.husky`, `.cargo`, `.devcontainer`, `.yarn`, `.mvn`, `.claude` (except `.claude/worktrees`). Protected files include `.gitconfig`, shell rc/profile files, `.npmrc`/`.yarnrc`/lockfile-config, `.pre-commit-config.yaml`, wrapper.properties, `.mcp.json`, `.claude.json`, etc.

**Hub relevance:** The `auto` mode here IS the unattended-safety layer the hub's `/goal`+`/loop` autonomous runs lean on (S7 policy, `decision-authority.md`). Key facts for the brainstorm: auto mode needs **v2.1.83+** and **Opus 4.6+/Sonnet 4.6** (a downstream version/model floor); the **3-in-a-row / 20-total block → fallback** is the escalation behavior; **conversation boundaries are transcript-re-read, not stored** (compaction can drop them → prefer a `permissions.deny` rule for hard guarantees, which the hub already does for the git-gate-bypass class); and `.claude` is a PROTECTED path (relevant to the hub's `git add -f` for `.claude/` patterns). The default block-list (force-push, push-to-main, destructive git, prod deploy) maps onto the hub's `decision-authority.md` ESCALATE taxonomy.
