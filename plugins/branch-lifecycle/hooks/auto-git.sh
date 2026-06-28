#!/usr/bin/env bash
# Autonomous git handler — so you never touch git. (branch-lifecycle PLUGIN version — self-contained.)
#
# Wired into SessionStart + Stop (see hooks.json). If the working tree has changes:
# secret-scan -> stage -> commit with a generated message -> push the current branch ->
# open a PR if one is missing and the branch is ahead of main (CREATE only).
# Companion: auto-pr.sh (SessionEnd) arms CI-gated auto-merge on that PR. Opening the PR
# per-turn (not arming) keeps long / `/clear`-reset sessions from leaving work un-PR'd.
#
# FAIL-SAFE: always exits 0 (a git hiccup must never block the session). The secret-scan abort
# path also exits 0 — it aborts the COMMIT (leaves changes staged), never the session.
# GUARDRAILS:
#   1. Never auto-commits onto main/master — moves the work to a fresh branch first.
#   1b. Never stacks new work onto an already-MERGED branch — rotates to a fresh branch off main.
#   2. Secret-scans the staged-added lines before committing; aborts if not clean.
#   3. Pushes the current branch only, never --force.
# OFF-SWITCHES (env, or branch-lifecycle-settings.json -> _settings.sh):
#   AUTO_GIT_DISABLE=1  -> do nothing at all.
#   AUTO_GIT_PUSH=0     -> commit locally but do not push.
# SECRET SCAN (pluggable, in priority order):
#   SECRET_SCAN_CMD="<cmd>"  -> run it; a non-zero exit aborts the commit (e.g.
#                               "gitleaks protect --staged --no-banner").
#   else the BUNDLED zero-dependency grep scan below runs (no hub script, no gitleaks needed).

set -uo pipefail

SELFDIR="${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/hooks}"
SELFDIR="${SELFDIR:-$(cd "$(dirname "$0")" && pwd)}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

# Map branch-lifecycle-settings.json -> env off-switches (a pre-set env var still wins).
PROJECT_ROOT="$ROOT"
# shellcheck source=/dev/null
[ -f "$SELFDIR/_settings.sh" ] && . "$SELFDIR/_settings.sh"

[ "${AUTO_GIT_DISABLE:-0}" = "1" ] && exit 0

mkdir -p "$ROOT/.claude" 2>/dev/null || true   # state dir may not exist in a downstream repo
LOG="$ROOT/.claude/.auto-git.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG" 2>/dev/null; }

# Bundled, zero-dependency secret scan over STAGED-ADDED lines. Returns 0 = clean, 1 = secret found.
# A line ending with the literal token `secret-scan:allow` is exempt. Flags: connection strings with
# an embedded password, PGPASSWORD=<value>, AWS access-key ids, private-key blocks, and hardcoded
# quoted api_key / auth_token / client_secret assignments of 20+ chars.
_bl_secret_scan() {
  local added
  added="$(git diff --cached --no-color -U0 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+ ')" || true
  [ -z "$added" ] && return 0
  added="$(printf '%s\n' "$added" | grep -vE 'secret-scan:allow[[:space:]]*$')" || true
  [ -z "$added" ] && return 0

  local patterns=(
    '(postgres(ql)?|mysql|mongodb(\+srv)?|redis|amqp)://[^:@/[:space:]]+:[^@/[:space:]]+@'
    'PGPASSWORD=[^[:space:]]'
    'AKIA[0-9A-Z]{16}'
    '-----BEGIN [A-Z ]*PRIVATE KEY-----'
    '(api_key|auth_token|client_secret)[[:space:]]*=[[:space:]]*["'\''][^"'\'']{20,}["'\'']'
  )
  local p
  for p in "${patterns[@]}"; do
    if printf '%s\n' "$added" | grep -Eiq -- "$p"; then
      return 1
    fi
  done
  return 0
}

# Nothing to do on a clean tree — this naturally limits commits to real changes.
[ -z "$(git status --porcelain 2>/dev/null)" ] && exit 0

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" || exit 0

# Guardrail 1: keep main/master clean — carry uncommitted work onto a new branch.
if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  newb="auto/work-$(date '+%Y%m%d-%H%M%S')"
  if git checkout -b "$newb" >/dev/null 2>&1; then
    log "moved uncommitted work off '$branch' onto '$newb'"
    branch="$newb"
  else
    log "on '$branch' but could not create a work branch; skipping (will not commit to $branch)"
    exit 0
  fi
fi

# Guardrail 1b: don't stack NEW work onto an already-MERGED branch — once its PR squash-merges
# (and the remote branch is deleted), commits here can never land cleanly. Detect this two ways,
# because `gh pr view <branch>` often CANNOT resolve a branch whose remote was pruned:
#   (a) gh still reports the PR as MERGED, OR
#   (b) the branch has commits ahead of origin/main by SHA but ZERO net content diff — the
#       signature of a squash-merge whose content already landed on main. This signal is
#       network-independent and catches the pruned-remote case (a) misses.
# Both are true-merged signals, so rotating the new work onto a fresh branch cut from latest main
# is always safe. A fresh branch has 0 commits ahead, so it never false-triggers.
if [ "$branch" != "main" ] && [ "$branch" != "master" ]; then
  git fetch origin main >/dev/null 2>&1 || true
  merged=""
  if command -v gh >/dev/null 2>&1 \
     && gh pr view "$branch" --json state --jq '.state' 2>/dev/null | grep -q MERGED; then
    merged="gh-reports-MERGED"
  elif git rev-parse --verify -q origin/main >/dev/null 2>&1; then
    ahead="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
    if [ "${ahead:-0}" -gt 0 ] && git diff --quiet origin/main..HEAD 2>/dev/null; then
      merged="content-already-on-main (squash-merged)"
    fi
  fi
  if [ -n "$merged" ]; then
    newb="auto/work-$(date '+%Y%m%d-%H%M%S')"
    if git checkout -b "$newb" origin/main >/dev/null 2>&1 || git checkout -b "$newb" >/dev/null 2>&1; then
      log "branch '$branch' already merged ($merged); moved new work onto fresh '$newb' off main"
      branch="$newb"
    fi
  fi
fi

# Stage everything, then secret-scan the staged-added content (scan must see the staged diff).
git add -A 2>/dev/null
staged="$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')"
[ "$staged" = "0" ] && exit 0

# Guardrail 2: secret-scan must confirm clean before committing (pluggable -> bundled). FAIL-CLOSED.
if [ -n "${SECRET_SCAN_CMD:-}" ]; then
  if ! eval "$SECRET_SCAN_CMD" >/dev/null 2>&1; then
    log "ABORT: SECRET_SCAN_CMD reported not clean — left changes staged, uncommitted."
    exit 0
  fi
elif ! _bl_secret_scan; then
  log "ABORT: bundled secret scan flagged a potential secret — left changes staged, uncommitted."
  exit 0
fi

msg="auto: checkpoint $(date '+%Y-%m-%d %H:%M') ($staged files on $branch)"
if git commit -q \
    -m "$msg" \
    -m "Autonomous checkpoint by the branch-lifecycle auto-git hook (commit gated by secret-scan)." 2>/dev/null; then
  log "committed $staged files: $msg"
else
  log "commit failed; changes remain staged"
  exit 0
fi

# Guardrail 3: push current branch (never --force, never main — handled above).
if [ "${AUTO_GIT_PUSH:-1}" = "1" ] && git remote get-url origin >/dev/null 2>&1; then
  if git push -u origin "HEAD:$branch" >/dev/null 2>&1; then
    log "pushed '$branch' to origin"
  else
    log "push failed (no creds/network?) — commit is safe locally on '$branch'"
  fi
fi

# Ensure a PR exists once the branch is ahead of main, so a long session (or one reset with
# `/clear`) never leaves work un-PR'd waiting on SessionEnd. CREATE only — NO `--auto` here:
# merge-arming stays owned by auto-pr.sh at SessionEnd, so work never merges mid-session.
if command -v gh >/dev/null 2>&1; then
  ahead="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
  if [ "${ahead:-0}" -gt 0 ] && ! gh pr view "$branch" --json number >/dev/null 2>&1; then
    gh pr create --base main --head "$branch" --fill >/dev/null 2>&1 \
      && log "opened PR for '$branch' (merge NOT armed — auto-pr.sh arms it at SessionEnd)"
  fi
fi

exit 0
