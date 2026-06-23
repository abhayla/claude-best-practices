Source: https://code.claude.com/docs/en/worktrees
Fetched: 2026-06-23

# Run parallel sessions with worktrees

> Isolate parallel Claude Code sessions in separate git worktrees so changes don't collide. Covers the `--worktree` flag, subagent isolation, `.worktreeinclude`, cleanup, and non-git VCS hooks.

A [git worktree](https://git-scm.com/docs/git-worktree) is a separate working directory with its own files and branch, sharing the same repository history and remote as your main checkout. Running each Claude Code session in its own worktree means edits in one session never touch files in another — Claude can build a feature in one terminal while fixing a bug in a second.

This page covers worktree isolation in the CLI (assumes a git repo; for other VCS see Non-git below). The desktop app creates a worktree for every new session automatically.

Worktrees are one of several ways to run Claude in parallel. They **isolate file edits**, while subagents and agent teams **coordinate the work itself**.

## Start Claude in a worktree

Pass `--worktree` or `-w` to create an isolated worktree and start Claude in it. By default the worktree is created under `.claude/worktrees/<value>/` at your repo root, on a new branch `worktree-<value>`:

```bash
claude --worktree feature-auth
```

Run again with a different name in another terminal for a second isolated session: `claude --worktree bugfix-123`. Omit the name and Claude generates one (e.g. `bright-running-fox`): `claude --worktree`.

You can also ask Claude to "work in a worktree" during a session — it creates one with the `EnterWorktree` tool. Once in a worktree, Claude can switch directly to another under `.claude/worktrees/` by calling `EnterWorktree` with the target path; the previous worktree stays on disk untouched.

Before using `--worktree` interactively in a directory for the first time, accept the workspace trust dialog by running `claude` once there. If trust isn't accepted, `--worktree` exits with an error. Non-interactive `-p` runs skip the trust check, so `claude -p --worktree` proceeds.

**Tip:** add `.claude/worktrees/` to your `.gitignore` so worktree contents don't appear as untracked files in your main checkout.

### Choose the base branch
Worktrees branch from your repo's default branch, `origin/HEAD` (clean tree matching the remote). If no remote / fetch fails, they fall back to current local `HEAD`. To always branch from local `HEAD`, set `worktree.baseRef` to `"head"` in settings — new worktrees then carry your unpushed commits + feature-branch state (useful when isolating subagents that operate on in-progress work). The setting accepts only `"fresh"` or `"head"`:

```json
{ "worktree": { "baseRef": "head" } }
```

To branch from a specific PR, pass the number prefixed with `#` (or a full GitHub PR URL): `claude --worktree "#1234"` — fetches `pull/<number>/head` from `origin`, creates the worktree at `.claude/worktrees/pr-<number>`. For full control, configure a `WorktreeCreate` hook (replaces the default `git worktree` logic entirely).

## Copy gitignored files into worktrees
A worktree is a fresh checkout, so untracked files like `.env`/`.env.local` aren't present. Add a `.worktreeinclude` file (`.gitignore` syntax) to your project root to copy them automatically. Only files that match a pattern **and** are gitignored are copied (tracked files are never duplicated):

```
.env
.env.local
config/secrets.json
```

Applies to `--worktree`, subagent worktrees, and desktop-app parallel sessions.

## Isolate subagents with worktrees
Subagents can run in their own worktrees so parallel edits don't conflict. Ask Claude to "use worktrees for your agents", or set it permanently on a custom subagent via `isolation: worktree` in frontmatter. Each subagent gets a temporary worktree, removed automatically when the subagent finishes without changes. Subagent worktrees use the same base branch as `--worktree` (default branch unless `worktree.baseRef: "head"`).

## Clean up worktrees
On exiting a worktree session, cleanup depends on changes:
- **No uncommitted changes / untracked files / new commits:** worktree + branch removed automatically. If the session has a name, Claude prompts so you can keep it.
- **Uncommitted changes / untracked files / new commits exist:** Claude prompts to keep or remove. Keeping preserves the directory + branch; removing deletes them (discarding uncommitted changes, untracked files, commits).
- **Non-interactive runs:** `--worktree` + `-p` worktrees are NOT auto-cleaned (no exit prompt) — remove with `git worktree remove`.

Worktrees Claude created for subagents and background sessions are auto-removed once older than your `cleanupPeriodDays`, provided no uncommitted changes / untracked files / unpushed commits. Worktrees you create with `--worktree` are never removed by this sweep. While an agent runs, Claude `git worktree lock`s its worktree so concurrent cleanup can't remove it (released when the agent finishes). To clean one the sweep keeps: `git worktree remove` (add `--force` for uncommitted/untracked).

## Manage worktrees manually
Full control via Git directly (specific existing branch, or location outside the repo):
```bash
git worktree add ../project-feature-a -b feature-a   # new branch
git worktree add ../project-bugfix bugfix-123        # existing branch
cd ../project-feature-a && claude                    # start Claude in it
git worktree list                                    # list
git worktree remove ../project-feature-a             # remove when done
```
Remember to initialize your dev environment in each new worktree (install deps, venvs, project setup).

## Non-git version control
Worktree isolation uses git by default. For SVN/Perforce/Mercurial/other, configure `WorktreeCreate` + `WorktreeRemove` hooks for custom create/cleanup. Because the hook replaces default git behavior, `.worktreeinclude` is NOT processed with `--worktree` — copy local config files inside your hook script. Example `WorktreeCreate` (reads the name from stdin, checks out a fresh SVN copy, prints the dir path):

```json
{
  "hooks": {
    "WorktreeCreate": [
      { "hooks": [ { "type": "command",
        "command": "bash -c 'NAME=$(jq -r .name); DIR=\"$HOME/.claude/worktrees/$NAME\"; svn checkout https://svn.example.com/repo/trunk \"$DIR\" >&2 && echo \"$DIR\"'" } ] }
    ]
  }
}
```
Pair with a `WorktreeRemove` hook to clean up on session end.

## See also
- Subagents (/en/sub-agents): delegate work to isolated agents within a session
- Agent teams (/en/agent-teams): coordinate multiple Claude sessions automatically
- Manage sessions (/en/sessions): name, resume, switch between conversations
- Desktop parallel sessions (/en/desktop)

---
**Hub relevance:** worktree isolation is the mechanism behind the **no-concurrent-same-file-edits** best practice for agent teams/parallel agents (see `multi-agent-best-practices.md` §B and `core/.claude/skills/git-worktrees`). The agent-teams pipeline-upgrade contract uses a dedicated worktree (§0.1) for autonomous-run isolation; `isolation: worktree` on a subagent partitions parallel build work.
