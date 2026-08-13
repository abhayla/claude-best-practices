#!/usr/bin/env bash
# Shared SSOT for session git-landing — the single place the merge/reconcile logic lives.
# Called by /end-session (`land --wait`), /start-session (`reconcile`), and the auto-pr /
# auto-pr-reconcile hooks (`land` / `reconcile`). Keeping it here (instead of duplicating the
# shell in each skill + hook) means a landing fix is a ONE-file edit, correct everywhere.
#
# Usage:
#   session-git-landing.sh land [--wait]   # land the CURRENT branch
#   session-git-landing.sh reconcile       # sweep leftover open PRs (except the current branch)
#
# Design notes:
# - Arms GitHub's NATIVE auto-merge, which merges exactly when the REQUIRED status checks pass
#   (same gate as branch protection). Do NOT watch ALL checks (e.g. `gh pr checks --watch
#   --fail-fast`): a noisy NON-required workflow would false-fail while the required check passes.
# - `land --wait` then polls until the PR reaches MERGED, so the branch is CLOSED before the caller
#   returns (the root cause of "branch left open" was returning before the async merge happened).
#   The hooks call `land` WITHOUT --wait (a SessionEnd hook must not block for minutes).
# - Honors AUTO_MERGE=0 (off-switch) and skips on main/master/detached HEAD / no gh / no remote.
set -u

_guard() { command -v gh >/dev/null 2>&1; }   # gh present (AUTO_MERGE gates only the *arm*, below)

_hold_check() {
  # HOLD GATE (2026-08-13 incident, T-118): a PR contracted "held for owner review" self-landed
  # because no arming path here ever checked for a hold marker — every owner-gated PR was one
  # SessionStart away from merging itself. Call before EVERY `gh pr merge` in this file. Echoes
  # one observable line and returns 0 (SKIP) when the PR carries the 'hold' label or its body
  # matches "owner review required" (case-insensitive); returns 1 (proceed) otherwise.
  # FAIL-SAFE: unlike the rest of this file (which fails OPEN on a gh hiccup), this check fails
  # CLOSED — a gh error here means SKIP, never land un-reviewed content on an API blip.
  local pr="$1"
  local labels labels_rc body body_rc
  labels="$(gh pr view "$pr" --json labels --jq '.labels[].name' 2>/dev/null)"; labels_rc=$?
  body="$(gh pr view "$pr" --json body --jq '.body // ""' 2>/dev/null)"; body_rc=$?
  if [ "$labels_rc" -ne 0 ] || [ "$body_rc" -ne 0 ]; then
    echo "  (hold-check failed for '$pr' — failing safe, skipping)"
    return 0
  fi
  if printf '%s\n' "$labels" | grep -qix 'hold'; then
    echo "  (skipped '$pr' — held: label 'hold')"
    return 0
  fi
  if printf '%s' "$body" | grep -qi 'owner review required'; then
    echo "  (skipped '$pr' — held: body matches \"owner review required\")"
    return 0
  fi
  return 1
}

_sync_local_after_merge() {
  # ROOT-CAUSE fix for "the branch looks unmerged locally after /end-session": land --wait merged
  # the PR REMOTELY but never reconciled the LOCAL clone, leaving the caller ON the now-dead branch
  # with a stale local `main` and an un-pruned local branch. (Squash-merge compounds it: the local
  # commits are not ancestors of origin/main, so `git branch -d`/`merge-base` both say "unmerged".)
  # Called ONLY after the caller has CONFIRMED the PR state is MERGED, so pruning is safe.
  # Skips on a dirty tree so it can never clobber uncommitted work.
  local merged_branch="$1"
  case "$merged_branch" in main|master|HEAD|"") return 0;; esac
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "  (local NOT reconciled: working tree dirty — switch to main + prune '$merged_branch' manually)"; return 0
  fi
  git checkout main >/dev/null 2>&1 || { echo "  (local NOT reconciled: could not checkout main)"; return 0; }
  git fetch origin main >/dev/null 2>&1
  git merge --ff-only origin/main >/dev/null 2>&1
  # -D (not -d): a squash merge means the local branch is not an ancestor of main, so -d would
  # refuse. Safe because the caller already confirmed the PR is MERGED (content is on main).
  git branch -D "$merged_branch" >/dev/null 2>&1
  echo "  (local reconciled: on main, fast-forwarded to origin/main, pruned '$merged_branch')"
}

land() {
  local wait_mode="${1:-}"
  _guard || { echo "land: skipped (no gh)"; return 0; }
  local branch; branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  case "$branch" in main|master|HEAD|"") echo "land: skipped (on '$branch')"; return 0;; esac
  git push -u origin "HEAD:$branch" >/dev/null 2>&1 || { echo "land: push failed for '$branch' (creds/network?)"; return 0; }
  gh pr view "$branch" >/dev/null 2>&1 || gh pr create --base main --head "$branch" --fill >/dev/null 2>&1
  # AUTO_MERGE=0 -> open/refresh the PR but do NOT arm (you click merge yourself).
  if [ "${AUTO_MERGE:-1}" = "0" ]; then echo "AUTO_MERGE=0 — PR opened for '$branch', not armed"; return 0; fi
  if _hold_check "$branch"; then echo "land: '$branch' held — not armed"; return 0; fi
  # Arm native auto-merge (gated on the REQUIRED checks only).
  gh pr merge "$branch" --auto --squash --delete-branch >/dev/null 2>&1
  if [ "$wait_mode" != "--wait" ]; then
    echo "armed auto-merge on '$branch' (lands when required CI passes)"; return 0
  fi
  # --wait: block until the PR is actually MERGED (or terminally closed), so the branch is closed.
  local st="" i=0
  while [ "$i" -lt 90 ]; do                       # up to ~15 min (90 x 10s)
    st="$(gh pr view "$branch" --json state --jq '.state' 2>/dev/null)"
    if [ "$st" = "MERGED" ] || [ "$st" = "CLOSED" ]; then break; fi
    sleep 10; i=$((i + 1))
  done
  case "$st" in
    MERGED) echo "merged '$branch' -> main and CLOSED the branch (required CI passed)"; _sync_local_after_merge "$branch";;
    CLOSED) echo "NOT closed cleanly: the PR for '$branch' was closed without merging — investigate";;
    *)      echo "NOT CLOSED: '$branch' is still OPEN after waiting — the required check is failing or stuck; investigate and re-run, do NOT declare the session closed";;
  esac
}

merge_one() {
  # Land ONE specific branch — invoked by the branch-choice SKILL (option 4 "merge then new", and
  # the owner-approved landing of a reaper-reported stale branch). The current branch IS a valid
  # target (option 4 merges the branch you're on, then cuts a fresh one). Arms GitHub NATIVE
  # auto-merge, so the merge is still CI-GATED on the required checks (a red/stale branch can never
  # sneak in). Never switches the working tree. NOTE: the reaper hook never calls this — only the skill does.
  local br="${1:-}"
  _guard || { echo "merge-one: skipped (no gh)"; return 0; }
  [ -z "$br" ] && { echo "merge-one: no branch given"; return 0; }
  case "$br" in main|master) echo "merge-one: refusing to merge '$br' into itself"; return 0;; esac
  [ "${AUTO_MERGE:-1}" = "0" ] && { echo "merge-one: skipped (AUTO_MERGE=0)"; return 0; }
  gh pr view "$br" >/dev/null 2>&1 || { echo "merge-one: no PR for '$br' (push/open it first)"; return 0; }
  if _hold_check "$br"; then echo "merge-one: '$br' held — not armed"; return 0; fi
  if gh pr merge "$br" --auto --squash --delete-branch >/dev/null 2>&1; then
    echo "armed auto-merge on '$br' (lands when its REQUIRED CI passes; red/stale never merges)"
  else
    echo "merge-one: could not arm '$br' (already merged/closed, or no perms)"
  fi
}

reconcile() {
  _guard || { echo "reconcile: skipped (no gh)"; return 0; }
  [ "${AUTO_MERGE:-1}" = "0" ] && { echo "reconcile: skipped (AUTO_MERGE=0)"; return 0; }
  local cur; cur="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  local any=0
  # SECURITY (2026-07-14 composite-autonomy audit): do NOT auto-arm merge on BOT/scan-authored
  # PRs — the scan-internet cron opens PRs from external web content, and arming them here would
  # let external data reach main with no human review point anywhere on the path. A bot-authored
  # PR (or one carrying a scan/discovery label) is armed ONLY when a human adds the
  # 'approved-for-merge' label. Human-authored PRs are unchanged.
  while IFS='|' read -r num br isbot labels; do
    [ -z "$num" ] && continue
    [ "$br" = "$cur" ] && continue                # never the active branch
    if ! printf '%s' "$labels" | grep -q 'approved-for-merge'; then
      if [ "$isbot" = "true" ] || printf '%s' "$labels" | grep -qE '(^|,)(discovery|auto-scan|auto-telemetry)(,|$)'; then
        echo "skipped #$num ($br — bot/scan-authored; add 'approved-for-merge' label to auto-land)"; continue
      fi
    fi
    if _hold_check "$num"; then continue; fi
    gh pr merge "$num" --auto --squash --delete-branch >/dev/null 2>&1 && { echo "armed #$num ($br — lands when required CI passes)"; any=1; }
  done < <(gh pr list --state open --json number,headRefName,isDraft,autoMergeRequest,author,labels \
            --jq '.[] | select(.isDraft==false) | select(.autoMergeRequest==null) | "\(.number)|\(.headRefName)|\(.author.is_bot)|\([.labels[].name] | join(","))"' 2>/dev/null)
  # DOCS-UPDATE CARVE-OUT (2026-07-14, pileup #378-#399): update-docs.yml opens its PR with the
  # default GITHUB_TOKEN, and GitHub never triggers pull_request workflows for GITHUB_TOKEN-created
  # events — so the required `validate` check NEVER RUNS, the workflow's self-armed auto-merge
  # never fires, and one docs PR stacks up per main push. These PRs are OUR OWN deterministic
  # regeneration of already-merged main (no external content), so they get a NARROW exemption from
  # the bot-block above, keyed on the auto/docs-update-* head-branch prefix — still 100% CI-gated:
  # supersede all but the newest, kick CI on it (close+reopen under THIS session's user token —
  # user-token events DO trigger workflows), then arm auto-merge.
  local newest=0 n
  while read -r n; do [ "$n" -gt "$newest" ] 2>/dev/null && newest=$n; done \
    < <(gh pr list --state open --json number,headRefName \
         --jq '.[] | select(.headRefName | startswith("auto/docs-update-")) | .number' 2>/dev/null)
  if [ "$newest" -gt 0 ]; then
    while read -r n; do
      [ -z "$n" ] || [ "$n" = "$newest" ] && continue
      gh pr close "$n" --comment "Superseded by #$newest (newer docs regeneration of the same main state)." --delete-branch >/dev/null 2>&1 \
        && echo "closed superseded docs PR #$n"
    done < <(gh pr list --state open --json number,headRefName \
              --jq '.[] | select(.headRefName | startswith("auto/docs-update-")) | .number' 2>/dev/null)
    if [ "$(gh pr view "$newest" --json statusCheckRollup --jq '.statusCheckRollup | length' 2>/dev/null)" = "0" ]; then
      gh pr close "$newest" >/dev/null 2>&1 && gh pr reopen "$newest" >/dev/null 2>&1 \
        && echo "kicked CI on docs PR #$newest (no checks ran — GITHUB_TOKEN gap; close+reopen re-triggers)"
    fi
    if _hold_check "$newest"; then
      : # held: logged by _hold_check, skip arming
    else
      gh pr merge "$newest" --auto --squash --delete-branch >/dev/null 2>&1 \
        && { echo "armed docs PR #$newest (lands when validate passes)"; any=1; }
    fi
  fi
  [ "$any" = 0 ] && echo "reconcile: no leftover PRs to land"
  return 0
}

# Only dispatch when EXECUTED, not when SOURCED (tests source this file to call the helpers
# directly, e.g. _sync_local_after_merge, without triggering the usage/exit path).
if [ "${BASH_SOURCE[0]:-$0}" = "$0" ]; then
  case "${1:-}" in
    land)      shift; land "$@";;
    reconcile) reconcile;;
    merge-one) shift; merge_one "$@";;
    *) echo "usage: session-git-landing.sh {land [--wait]|reconcile|merge-one <branch>}" >&2; exit 2;;
  esac
fi
