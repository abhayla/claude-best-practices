#!/usr/bin/env bash
# Autonomous PR + auto-merge handler — so closing a session lands the work without touching git.
#
# Wired into SessionEnd (fires when the session closes). Companion to auto-git.sh:
#   auto-git.sh (SessionStart+Stop) — commits + pushes each turn's work to a task branch.
#   auto-pr.sh  (SessionEnd)        — opens a PR for that branch and ARMS native auto-merge,
#                                     so GitHub squash-merges it the moment the project's required
#                                     CI checks go green, then deletes the remote branch.
#
# PREREQUISITES (configure once, per repo): GitHub branch protection on main with required
# status checks, repo-level auto-merge enabled, and delete-branch-on-merge enabled. Without a
# required check, `--auto` merges immediately (no green-gate) — so set at least one required check.
#
# Why SessionEnd, not Stop: arming auto-merge after every turn would merge work mid-session.
# Arming on close matches "close the session and forget about the branch".
#
# FAIL-SAFE: always exits 0 (a gh/network hiccup must never block session close).
# GUARDRAILS:
#   1. Never opens a PR for main/master or a detached HEAD.
#   2. Only arms auto-merge — GitHub still gates the actual merge on the required CI checks.
#      A red or pending CI leaves the PR open and unmerged (no lost work, nothing forced).
#   3. Idempotent — re-running reuses the existing PR; never opens duplicates.
# OFF-SWITCHES:
#   AUTO_PR_DISABLE=1 -> do nothing at all.
#   AUTO_MERGE=0      -> open/refresh the PR but do NOT arm auto-merge (you click merge yourself).
#                       Set this for repos where a human must approve every merge to main.

set -uo pipefail

[ "${AUTO_PR_DISABLE:-0}" = "1" ] && exit 0

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

LOG="$ROOT/.claude/.auto-git.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] auto-pr: $*" >> "$LOG" 2>/dev/null; }

command -v gh >/dev/null 2>&1 || { log "gh not installed; skipping"; exit 0; }

# Prune merged branches so they never accumulate. `fetch --prune` drops stale remote refs (safe);
# a LOCAL branch is hard-deleted ONLY when gh confirms its PR is MERGED — its content is already on
# main, so this can never lose work (squash-merge hides it from `git branch -d`, hence the gh check).
git fetch --prune >/dev/null 2>&1 || true
cur_for_prune="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
git for-each-ref --format '%(refname:short) %(upstream:track)' refs/heads/ 2>/dev/null \
  | awk '$2=="[gone]"{print $1}' \
  | while read -r b; do
      [ "$b" = "$cur_for_prune" ] && continue
      if gh pr view "$b" --json state --jq '.state' 2>/dev/null | grep -q MERGED; then
        git branch -D "$b" >/dev/null 2>&1 && log "pruned merged branch '$b'"
      fi
    done

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" || exit 0
if [ "$branch" = "main" ] || [ "$branch" = "master" ] || [ "$branch" = "HEAD" ]; then
  log "on '$branch' (no task branch); nothing to PR"
  exit 0
fi

# The branch must exist on origin before a PR can reference it. auto-git normally pushes it;
# push here too so SessionEnd is self-sufficient even if the last turn's push was skipped.
if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin "HEAD:$branch" >/dev/null 2>&1 || log "push of '$branch' failed (creds/network?) — continuing"
fi

# Idempotent PR: reuse an existing open PR for this branch, else create one.
if gh pr view "$branch" --json number >/dev/null 2>&1; then
  log "PR already exists for '$branch'"
else
  if gh pr create --base main --head "$branch" --fill >/dev/null 2>&1; then
    log "opened PR for '$branch'"
  else
    log "could not open PR for '$branch' (no commits ahead of main, or gh error); skipping merge-arm"
    exit 0
  fi
fi

# Arm native auto-merge: GitHub merges when the required CI checks pass, then deletes the branch
# (delete_branch_on_merge is enabled repo-side). Squash keeps main's history one-commit-per-PR.
if [ "${AUTO_MERGE:-1}" = "0" ]; then
  log "AUTO_MERGE=0 — PR left open for manual merge of '$branch'"
  exit 0
fi

# Merge NOW if the PR is already green + mergeable (CLEAN); otherwise arm native auto-merge
# (GitHub lands it when the required checks pass). Either way it stays CI-gated.
mss="$(gh pr view "$branch" --json mergeStateStatus --jq '.mergeStateStatus' 2>/dev/null)"
if [ "$mss" = "CLEAN" ] && gh pr merge "$branch" --squash --delete-branch >/dev/null 2>&1; then
  log "merged '$branch' immediately (was CLEAN/green)"
elif gh pr merge "$branch" --auto --squash >/dev/null 2>&1; then
  log "armed auto-merge (squash) for '$branch' — will land when CI is green"
else
  log "could not merge/arm '$branch' (already merged, or no required checks pending) — PR left open"
fi

exit 0
