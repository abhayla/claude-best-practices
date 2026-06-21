---
name: git-branch-lifecycle
description: >
  The model-driven control layer over the autonomous branch automation (auto-git.sh +
  auto-pr.sh hooks). Use to start an isolated parallel workstream in its own git worktree
  (`work`), to finish a branch NOW with an agent code-review before arming auto-merge
  (`finish`), to RECONCILE every branch (`cleanup` — merged→prune, unmerged→auto-PR+merge-on-green,
  escalate only CI-red/strategic), or to see the live branch/PR/merge state (`status`). The
  hooks handle the unattended path automatically; this skill is the judgment layer for parallel
  isolation, in-session review, and conflict handling.
type: workflow
allowed-tools: "Bash Read Grep Glob Agent"
argument-hint: "status | work <name> | finish [branch] | cleanup"
version: "1.1.0"
---

# Git Branch Lifecycle — the control layer over autonomous git

Two layers run the branch lifecycle. Know which owns what before acting:

| Layer | Trigger | Does |
|---|---|---|
| **`auto-git.sh`** hook | SessionStart + Stop (automatic) | commit + push each turn's work to a task branch; keep `main` clean; never stack onto a merged branch |
| **`auto-pr.sh`** hook | SessionEnd (automatic) | open the PR, arm CI-gated auto-merge (squash), prune merged branches |
| **this skill** | you invoke it | parallel worktrees, in-session agent review before merge, conflict handling, manual finish/cleanup |

The hooks already make the unattended path work — you can close any session and the work lands when CI is green. Use this skill only when you want the judgment layer.

**Command:** $ARGUMENTS

---

## STEP 0: Route on the sub-command

- starts with `status` → STEP 1
- starts with `work` → STEP 2
- starts with `finish` → STEP 3
- starts with `cleanup` → STEP 4
- empty / unknown → run STEP 1 (status) and show this command list.

---

## STEP 1: `status` — show the live picture

```bash
echo "== current branch =="; git rev-parse --abbrev-ref HEAD
echo "== open PRs (head : state : auto-merge) =="
gh pr list --state open --json number,headRefName,autoMergeRequest \
  --jq '.[] | "#\(.number) \(.headRefName) auto-merge:\(if .autoMergeRequest then "ARMED" else "off" end)"' 2>/dev/null
echo "== local branches with a gone (merged+deleted) upstream — prune candidates =="
git for-each-ref --format '%(refname:short) %(upstream:track)' refs/heads/ | awk '$2=="[gone]"{print $1}'
echo "== worktrees =="; git worktree list
```

Summarize: which branch is active, which PRs are armed for auto-merge, what is prunable.

---

## STEP 2: `work <name>` — isolated parallel workstream (own worktree)

Two sessions in the SAME folder share one `HEAD` and CANNOT be on different branches. For
TRUE parallel work, give each workstream its own **worktree** (a separate folder with its
own checked-out branch). This is the only real multi-session isolation.

```bash
NAME="$2"                                   # the <name> argument
[ -z "$NAME" ] && { echo "usage: /git-branch-lifecycle work <name>"; exit 1; }
SLUG="$(echo "$NAME" | tr ' /' '--' | tr -cd '[:alnum:]-' | tr '[:upper:]' '[:lower:]')"
ROOT="$(git rev-parse --show-toplevel)"
git fetch origin main >/dev/null 2>&1 || true
WT="$ROOT/../$(basename "$ROOT")-wt-$SLUG"   # sibling folder, never nested inside the repo
git worktree add -b "feat/$SLUG" "$WT" origin/main
echo "Worktree ready: $WT  (branch feat/$SLUG, based on latest main)"
echo "Open a NEW Claude session in that folder to work on it in parallel."
```

Tell the user the exact folder path and that the auto-git/auto-pr hooks operate per-worktree, so that workstream lands independently when its session closes.

---

## STEP 3: `finish [branch]` — land it NOW, with an independent agent review first

Use when you want the work merged immediately rather than waiting for SessionEnd, AND you
want a real code review (the unattended path is CI-gated only — a bash hook cannot dispatch
a reviewer; this skill can).

1. **Resolve target.** `BR="${2:-$(git rev-parse --abbrev-ref HEAD)}"`. Refuse if `main`/`master`.
2. **Independent review (mandatory before arming merge).** Dispatch `code-reviewer-agent`
   on the branch diff vs `main`:
   ```
   Agent(code-reviewer-agent): "Review the diff of branch <BR> against main
   (`git diff main...<BR>`). Report blocking issues (correctness, security, scope creep,
   out-of-brief files) vs non-blocking. Return a structured verdict."
   ```
   Per `independent-test-verification.md` / `supervisor-verification.md`, the author is never
   the sole verifier. If the reviewer reports **blocking** issues → STOP, fix them, re-review.
   Do NOT arm merge over a dissent.
3. **Ensure committed + pushed.** If the tree is dirty, let auto-git commit, or commit here.
   `git push -u origin "HEAD:$BR"`.
4. **Open PR + arm auto-merge** (idempotent — reuse existing PR):
   ```bash
   gh pr view "$BR" >/dev/null 2>&1 || gh pr create --base main --head "$BR" --fill
   gh pr merge "$BR" --auto --squash
   ```
<!-- DUAL-SYNC:HUB-ONLY -->
   GitHub merges when the required CI checks (`validate`, `test`) pass, then deletes the branch.
<!-- DUAL-SYNC:END -->
5. **Report** the PR URL and that it is armed. Do not block waiting for CI.

---

## STEP 4: `cleanup` — RECONCILE every branch (merged→prune, unmerged→land-or-escalate)

"Clean up" MUST leave zero dangling branches WITHOUT losing work AND without handing the
human a mechanical decision. So cleanup is a full reconcile, not just a prune. For EACH local
branch (skip `main`/`master` and the current branch), classify by `commits ahead of main` +
PR state, and act:

| Branch state | Action (autonomous) |
|---|---|
| `gh` confirms a **MERGED** PR | `git branch -D` — content is on main, safe |
| **0 commits** ahead of main | `git branch -D` — empty/stale, nothing to lose |
| Commits ahead, **no PR / open PR** | **open a PR (idempotent) + arm `--auto --squash`** → CI-green lands it automatically; CI-red leaves it open |

Only **escalate** (leave open, report for a human) a branch whose auto-PR is **CI-RED** (e.g.
breaks a required gate) OR whose diff asserts a **public/strategic** surface (README
positioning, a NEW governance rule). Even then, prefer opening the PR and letting the human
**veto via the open PR** over blocking on a question — do NOT ask the human a land-or-delete
question for content CI can adjudicate.

```bash
git fetch --prune >/dev/null 2>&1
cur="$(git rev-parse --abbrev-ref HEAD)"
for b in $(git for-each-ref --format '%(refname:short)' refs/heads/ | grep -vxE 'main|master'); do
  [ "$b" = "$cur" ] && continue
  state="$(gh pr view "$b" --json state --jq '.state' 2>/dev/null)"
  if [ "$state" = "MERGED" ]; then
    git branch -D "$b" && echo "PRUNED (merged): $b"; continue
  fi
  ahead="$(git rev-list --count origin/main..$b 2>/dev/null)"
  if [ "${ahead:-0}" = "0" ]; then
    git branch -D "$b" && echo "PRUNED (empty): $b"; continue
  fi
  git push -u origin "$b" >/dev/null 2>&1
  gh pr view "$b" >/dev/null 2>&1 || gh pr create --base main --head "$b" --fill >/dev/null 2>&1
  gh pr merge "$b" --auto --squash >/dev/null 2>&1 \
    && echo "PR'D + auto-merge armed: $b (lands on green CI)" \
    || echo "ESCALATE: $b — PR open but auto-merge could not arm (CI red / conflict); human decides"
done
```

After it runs, report the disposition per branch. The ONLY branches left for the human are
CI-red or strategic ones — never a branch whose content CI could have adjudicated.

A branch is hard-deleted ONLY when `gh` confirms MERGED or it has zero commits ahead — never
guess. Unmerged work is never deleted; it is PR'd so CI (not a human, not a guess) decides.

---

## MUST DO

- Always run the `code-reviewer-agent` review in `finish` BEFORE arming auto-merge — the author is never the sole verifier.
- Always base a new `work` worktree on the latest `origin/main`, in a SIBLING folder (never nested in the repo).
- Always confirm a MERGED PR via `gh` before deleting any local branch (or that it has 0 commits ahead).
- In `cleanup`, always AUTO-PR an unmerged branch and let CI decide — never ask the human a land-or-delete question that CI can adjudicate. Escalate ONLY CI-red or genuinely-strategic (public/governance) branches, and prefer a veto-via-open-PR over a blocking question.
- Always treat the hooks as the SSOT for the unattended path — this skill complements, never duplicates, them.

## MUST NOT DO

- MUST NOT arm auto-merge over a reviewer dissent or failing CI — a stalled PR is safe; a wrong merge is not.
- MUST NOT `git branch -D` a branch that has unmerged commits and no merged PR — PR it instead (let CI decide); only hard-delete on a confirmed MERGED PR or 0 commits ahead.
- MUST NOT bounce a mechanical land-or-delete decision to the human when an auto-PR + CI gate can decide it — that is the gap this skill exists to close.
- MUST NOT create a worktree inside the repo working tree — it pollutes status and git operations.
- MUST NOT push to or merge into `main` directly — everything lands via a PR + CI gate.
