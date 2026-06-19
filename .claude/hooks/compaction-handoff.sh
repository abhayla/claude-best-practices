#!/usr/bin/env bash
# PreCompact hook — deterministic compaction-survival breadcrumb.
# context-management.md rule 6 ("Compaction Survival") requires preserving the
# full list of modified files + current task objective + test commands across a
# compaction — but that is advisory prose the model must remember to do. A shell
# hook cannot see the conversation (so it cannot capture the task objective or
# reasoning), but it CAN deterministically snapshot the MECHANICAL slice — git
# state + the exact set of modified files + a timestamp — to a handoff file that
# survives compaction on disk. The model still owns writing the task objective to
# the scratchpad; this guarantees the file/git breadcrumb is never lost.
#
# Non-blocking: write the snapshot, always exit 0.
# RUNTIME NOTE: unit-verified + wired, but whether PreCompact fires in the
# installed Claude Code version is session-pinned — confirm via a live compaction
# after a session restart (newly-wired hooks are not active mid-session).
exec 2>/dev/null
root=$(git rev-parse --show-toplevel 2>/dev/null) || root="."
out="$root/.claude/.compaction-handoff.md"
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "?")
branch=$(git -C "$root" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")

{
  echo "# Compaction handoff breadcrumb — $ts"
  echo "branch: $branch"
  echo "head: $(git -C "$root" rev-parse --short HEAD 2>/dev/null || echo '?')"
  echo
  echo "## Modified / staged files at compaction (mechanical slice — write the task"
  echo "## objective + test commands to your scratchpad yourself; a hook can't see them):"
  git -C "$root" status --short 2>/dev/null || echo "(git status unavailable)"
} > "$out"
exit 0
