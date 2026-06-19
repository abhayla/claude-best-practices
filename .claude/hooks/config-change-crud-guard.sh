#!/usr/bin/env bash
# ConfigChange hook — resource-CRUD telemetry backstop. The resource-CRUD
# approval gate (prompt-auto-enhance-rule.md "Resource CRUD" + decision-authority)
# is advisory prose: "no Claude Code resource is created/updated/deleted without
# explicit user approval." A write-only rule loses to time pressure. This hook
# fires when a settings/skills/rule/agent config file changes mid-session and
# records it to an append-only telemetry log, so an UNAPPROVED resource CRUD is
# SEEN later (the same detector pattern no-overask-guard uses for the enhance
# banner). It is a backstop/observer, NOT a hard pre-gate — the change has already
# happened by the time ConfigChange fires; the value is making drift visible.
#
# Non-blocking: append to log, always exit 0. The log is gitignored runtime state.
# RUNTIME NOTE: unit-verified + wired, but whether ConfigChange fires in a given
# Claude Code version must be confirmed by a live config edit after a session
# restart (newly-wired hooks are not active mid-session).
exec 2>/dev/null
root=$(git rev-parse --show-toplevel 2>/dev/null) || root="."
log="$root/.claude/.config-changes.log"

# Event payload (JSON) arrives on stdin; pull the change kind + path if jq exists.
payload=$(cat 2>/dev/null)
kind=$(printf '%s' "$payload" | jq -r '.matcher // .hookSpecificOutput.configType // .config_type // "unknown"' 2>/dev/null || echo "unknown")
path=$(printf '%s' "$payload" | jq -r '.file_path // .path // "?"' 2>/dev/null || echo "?")
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "?")

printf '%s\tconfig-change\tkind=%s\tpath=%s\n' "$ts" "${kind:-unknown}" "${path:-?}" >> "$log"
exit 0
