#!/usr/bin/env bash
# run_agent_team_build.sh — like run_agent_team.sh but for LONG-RUNNING parallel-EDIT teams.
#
# The base harness kills the psmux session ~10s after first detecting a team (subagents/>=2),
# which is correct for fast read-only teams (design/research finish in ~20s) but would ABORT a
# multi-minute build mid-flight. This variant uses the IDENTICAL launch mechanism + the same
# universal subagents/>=2 team detection, but then KEEPS THE SESSION ALIVE until the build's
# expected output files are complete (exist, non-trivial, and size-stable across two polls) or a
# timeout, so the teammates can finish writing modules + tests. Records the real-team ground truth
# (lead session + subagents count) regardless.
#
# Usage: run_agent_team_build.sh "<prompt>" <label> <timeout_sec> <workdir_win> "<done_file1[:done_file2:...]>"
#   done_files are paths (relative to workdir) that must all exist & be >200 bytes & stable to finish.
set -u

HUB="D:/Abhay/VibeCoding/claude-best-practices"
SETTINGS_WIN='D:\Abhay\VibeCoding\claude-best-practices\.claude\.team-demo\settings.json'
CLAUDE_WIN='C:\Users\itsab\.local\bin\claude.exe'
PSMUX="$(command -v psmux 2>/dev/null || echo /c/Users/itsab/.local/psmux/psmux.exe)"
PROMPT="${1:?need a team prompt}"
case "$PROMPT" in *'"'*) echo "ERROR: prompt has a double-quote — rephrase without quotes."; exit 4 ;; esac
LABEL="${2:-build}"
TIMEOUT="${3:-560}"
WORKDIR_WIN="${4:?need a windows workdir}"
DONE_SPEC="${5:?need done-file list (colon-separated, relative to workdir)}"
export TMUX_TMPDIR=/tmp
cd "$HUB" || exit 3
[ -x "$PSMUX" ] || { echo "psmux not found at $PSMUX"; exit 2; }

# workdir in unix form for file checks
WORKDIR_UNIX="$(cygpath -u "$WORKDIR_WIN" 2>/dev/null || echo "$WORKDIR_WIN")"
IFS=':' read -r -a DONE_FILES <<< "$DONE_SPEC"

CMDFILE="$HUB/.claude/.team-cmd-${LABEL}.cmd"
printf '@echo off\r\ncd /d "%s"\r\nset "PSMUX_SESSION="\r\nset "TMUX="\r\nset "TMUX_PANE="\r\n"%s" --settings "%s" --permission-mode bypassPermissions --append-system-prompt "TEAM-LEAD MODE: this session runs an agent-team BUILD task. Your VERY FIRST tool call MUST spawn the teammates in parallel. Do NOT implement anything yourself, do NOT deliberate or review solo before spawning - the team is already warranted. Spawn immediately; only verify/run tests AFTER teammates return." "%s"\r\n' \
  "$WORKDIR_WIN" "$CLAUDE_WIN" "$SETTINGS_WIN" "$PROMPT" > "$CMDFILE"

sess="b_${LABEL}"
"$PSMUX" kill-session -t "$sess" 2>/dev/null
PROJDIR="$HOME/.claude/projects/$(echo "$WORKDIR_WIN" | sed 's#[:\\/]#-#g')"
pre_sessions=$(ls "$PROJDIR" 2>/dev/null | grep -E '\.jsonl$' | sort)
echo "=== run_agent_team_build [$LABEL]: launching in psmux (workdir=$WORKDIR_WIN, timeout=${TIMEOUT}s) ==="
"$PSMUX" new-session -d -s "$sess" -x 220 -y 50 "cmd /c \"$(cygpath -w "$CMDFILE")\"" \
  || { echo "psmux new-session failed"; exit 2; }

real_team_dir() {
  local f sid n
  for f in $(comm -13 <(echo "$pre_sessions") <(ls "$PROJDIR" 2>/dev/null | grep -E '\.jsonl$' | sort)); do
    sid="${f%.jsonl}"
    n=$(ls "$PROJDIR/$sid/subagents/" 2>/dev/null | grep -c '\.jsonl$')
    [ "$n" -ge 2 ] 2>/dev/null && { echo "$sid:$n"; return; }
  done
}

files_done() {  # all done-files exist, >200 bytes
  local rel sz
  for rel in "${DONE_FILES[@]}"; do
    [ -f "$WORKDIR_UNIX/$rel" ] || return 1
    sz=$(stat -c %s "$WORKDIR_UNIX/$rel" 2>/dev/null || echo 0)
    [ "$sz" -gt 200 ] 2>/dev/null || return 1
  done
  return 0
}

sig() {  # combined size signature of done-files, for stability check
  local rel s=0 sz
  for rel in "${DONE_FILES[@]}"; do sz=$(stat -c %s "$WORKDIR_UNIX/$rel" 2>/dev/null || echo 0); s=$((s+sz)); done
  echo "$s"
}

team_hit=""; waited=0; last_sig=""; stable=0
while [ "$waited" -lt "$TIMEOUT" ]; do
  sleep 8; waited=$((waited+8))
  [ -z "$team_hit" ] && team_hit=$(real_team_dir) && [ -n "$team_hit" ] && \
    echo "[t+${waited}s] REAL TEAM FORMED — lead ${team_hit%%:*} subagents=${team_hit##*:}"
  alive=$("$PSMUX" ls 2>/dev/null | grep -c "^${sess}:")
  if files_done; then
    cur=$(sig)
    if [ "$cur" = "$last_sig" ]; then stable=$((stable+1)); else stable=0; last_sig="$cur"; fi
    echo "[t+${waited}s] done-files present (sig=$cur, stable=$stable)"
    [ "$stable" -ge 2 ] && { echo "BUILD OUTPUTS COMPLETE & STABLE"; break; }
  fi
  [ "$alive" -eq 0 ] && { echo "[t+${waited}s] psmux session ended"; break; }
done

sleep 6
"$PSMUX" capture-pane -t "$sess" -p 2>/dev/null | tr -d '\000' > "$HUB/.claude/.team-out-${LABEL}.txt"
"$PSMUX" kill-session -t "$sess" 2>/dev/null
if [ -n "$team_hit" ]; then
  echo "RESULT: REAL TEAM [$LABEL] — lead ${team_hit%%:*}, ${team_hit##*:} teammate subagents. pane -> .claude/.team-out-${LABEL}.txt"
  files_done && echo "RESULT: build outputs present." || echo "RESULT: WARNING build outputs incomplete."
  exit 0
fi
echo "RESULT: FAILED to form a real team for [$LABEL] within ${TIMEOUT}s"
"$PSMUX" capture-pane -t "$sess" -p 2>/dev/null | tr -d '\000' | grep -avE '^[[:space:]]*$' | tail -15
exit 1
