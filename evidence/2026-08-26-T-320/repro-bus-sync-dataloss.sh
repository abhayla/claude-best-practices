#!/bin/bash
# T-320 HIGH-1 repro: bus_pull() silently destroys unpushed bus commits when the
# unpushed-commit MEASUREMENT itself fails (`git log '@{u}..HEAD'` -> rc=128, empty stdout).
# bus-sync.sh:8 reads empty stdout as "no unpushed commits to lose" and takes the
# `git fetch && git reset -q --hard origin/main` branch on line 11.
# Outcome: the unpushed commit is destroyed AND bus_pull returns rc=0 (fleet sees a healthy tick).
#
# Trigger conditions (all three required):
#   1. local HEAD has an unpushed commit
#   2. upstream tracking is absent/broken, so `git log '@{u}..HEAD'` fails (rc=128, empty)
#   3. `git pull --rebase` then FAILS (here: an add/add conflict on the same path)
set -u
T=$(mktemp -d); cd "$T"
mkdir remote && git -C remote init -q --bare . && git -C remote symbolic-ref HEAD refs/heads/main
git clone -q remote seed 2>/dev/null && cd seed
git config user.email t@t; git config user.name t
echo base > f.txt; git add -A; git commit -qm base; git branch -M main; git push -q origin main

# LOCAL clone (still at 'base') makes a conflicting unpushed commit
cd "$T" && git clone -q remote work && cd work
git config user.email t@t; git config user.name t
echo LOCAL-VERSION > conflict.txt; git add -A; git commit -qm "PRECIOUS local work"

# REMOTE independently adds the SAME path (=> add/add conflict on rebase)
cd "$T" && git clone -q remote other && cd other
git config user.email t@t; git config user.name t
echo REMOTE-VERSION > conflict.txt; git add -A; git commit -qm "remote conflicting"; git push -q origin main

cd "$T/work"
git branch --unset-upstream 2>/dev/null   # condition 2: measurement now fails
echo "BEFORE: $(git log --oneline -1)"
echo "measurement: out='$(git log '@{u}..HEAD' --oneline 2>/dev/null)' rc=$(git log '@{u}..HEAD' --oneline >/dev/null 2>&1; echo $?)"
source "${BUS_SYNC:-/c/Abhay/GetWorkDone/bus-sync.sh}"
bus_pull; rc=$?
echo "bus_pull rc=$rc   <-- 0 (success) even though work was destroyed"
echo "AFTER:  $(git log --oneline -1)"
if git log --oneline | grep -q PRECIOUS; then
  echo "RESULT: commit survived (defect NOT reproduced)"; exit 1
else
  echo "RESULT: *** PRECIOUS commit DESTROYED, bus_pull rc=$rc -- defect reproduced ***"; exit 0
fi
