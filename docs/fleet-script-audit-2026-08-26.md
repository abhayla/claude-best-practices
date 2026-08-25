# GetWorkDone fleet-script adversarial audit — 2026-08-26 (T-320, wave 3)

Third adversarial pass over the GetWorkDone fleet scripts, hunting the three defect classes the
contract names: **silent failures** (an error swallowed with no surfaced signal), **race
conditions** (unguarded concurrent access to shared state), and **un-gated defect classes** —
anything that repeats `check_fleet_script_health.py`'s founding pattern, *detect-then-discard*: a
script correctly detects a failure condition and then throws the signal away, so the unattended
fleet reports healthy while doing nothing.

Prior waves and their landed gates were read FIRST (`docs/fleet-script-audit-2026-08-10.md` /
T-071, `docs/fleet-script-audit-2026-08-17.md` / T-167, plus the 14 checks already in
`scripts/check_fleet_script_health.py`), so this report covers **new or previously-invisible
ground** rather than re-litigating findings already gated.

**Scripts audited:** 34 (every `.sh` / `.ps1` / `.py` / `.cmd` under `C:\Abhay\GetWorkDone`,
its `scripts/` and `hooks/` subdirectories).

| Severity | Count |
|---|---|
| HIGH | 4 |
| MEDIUM | 4 |
| LOW | 2 |

Every HIGH was **verified at source and reproduced empirically before being written down**, and
every HIGH has a deterministic gate landed in this PR with self-tests that fail when the check is
stubbed to `return []` (the non-vacuity bar from `docs/governance/learning-to-gate-doctrine.md`).

## Why the checker was clean before this audit

The baseline run of the 14 existing checks against the live fleet reported `fleet-health: clean`.
That was true and not reassuring: **all four HIGHs below were invisible to every existing check**,
each for a structural reason.

The existing PowerShell/batch checks ask a **presence** question — *is there an exit-code test near
this call?* Three of the four HIGHs answer that question truthfully and are still broken:

- HIGH-1 tests something, but the probe it tests **cannot fail loudly** (empty output on error).
- HIGH-2's guard is not skipped, swallowed or unchecked — it is **never armed**.
- HIGH-3 has a `$LASTEXITCODE` test two lines down; it just reads a **different command's** code.

So the shared root cause across this wave is: *the gates verified that a check EXISTS, not that its
RESULT is reachable and meaningful.* The four new gates ask the reachability question.

---

## HIGH-1 — `bus_pull` hard-resets over unpushed commits when its own safety probe fails

**File:** `bus-sync.sh:8-11` · **Class:** silent failure + detect-then-discard · **Gate:** `unmeasured-reset`

```bash
if [ -n "$(git log '@{u}..HEAD' --oneline 2>/dev/null)" ]; then
  git pull -q --rebase origin main 2>/dev/null || { git rebase --abort ...; return 2; }
else
  git pull -q --rebase origin main 2>/dev/null || { git fetch -q origin main && git reset -q --hard origin/main; }  # safe: no unpushed commits to lose
fi
```

`git log '@{u}..HEAD'` exits **128 with empty stdout** whenever the upstream cannot be resolved — a
branch with no tracking ref (routine after `git branch -M main`), a renamed or deleted remote
branch, a detached HEAD. stderr goes to `/dev/null` and the exit code is never tested, so that
empty output is indistinguishable from the genuine "zero unpushed commits" answer. The code then
takes the branch its own comment calls `safe: no unpushed commits to lose` and hard-resets over
real committed work.

The failure is doubly silent: the destroyed commit survives only in the reflog, and **`bus_pull`
returns 0**, so the caller records a healthy tick.

This is the direct sibling of T-167's `unmeasured-safe-delete`, one level up — there the emptiness
of `git status` authorised deleting a *working tree*; here the emptiness of a probe authorises
discarding *committed history*. The existing check cannot see it: there is no `worktree remove`,
the destructive verb is `reset --hard`.

**Reproduced end-to-end** (`evidence/2026-08-26-T-320/repro-bus-sync-dataloss.sh`, self-contained,
exits 0 only when the defect reproduces):

```
BEFORE: 0597760 PRECIOUS local work
measurement: out='' rc=128
CONFLICT (add/add): Merge conflict in conflict.txt
bus_pull rc=0   <-- 0 (success) even though work was destroyed
AFTER:  3e9b49e remote conflicting
RESULT: *** PRECIOUS commit DESTROYED, bus_pull rc=0 -- defect reproduced ***
```

Three conditions must coincide: an unpushed commit, an unresolvable upstream, and a `pull --rebase`
that then fails (here an add/add conflict). Note the guarded path is genuinely safe — with tracking
intact the probe returns non-empty and the rebase protects the commit — so the defect is precisely
the *unmeasurable* case.

**Fix (GetWorkDone repo):** resolve the upstream fail-closed before the probe; treat "could not
measure" as *unpushed commits present* and refuse to reset.

---

## HIGH-2 — the janitor's live-worker guard is armed for a naming convention the fleet abandoned

**File:** `janitor-worktrees.ps1:137` (verdict feeds `git worktree remove`) · **Class:** detect-then-discard · **Gate:** `dead-convention-guard`

```powershell
$leaf = Split-Path $wtPath -Leaf
if ($leaf -match '-wt-t(\d+)$') {
  $hbPath = Join-Path $HeartbeatDir "T-$($Matches[1]).hb"
  ...  return @{ Verdict = "KEPT-live" }
}
```

The live-task guard is the only thing standing between a *running* worker and deletion of its
worktree — clean+landed is not sufficient protection, because a worker that has just pushed and had
its PR merged is still running in that directory, writing STATUS.md and running its checker.

Measured against the live host, the literal matches **1 of 40** worktree directories:

```
GUARD-DISARMED T-320-claude-best-practices     GUARD-DISARMED gorefer-T149
GUARD-DISARMED T-215-IPODhan                   GUARD-DISARMED IPODhan-T179
GUARD-ARMED    gorefer-wt-t060                 ... (39 disarmed in total)
```

For those 39, `Test-WorktreeSafety` never opens a heartbeat, never returns `KEPT-live`, and falls
straight through to the clean/landed predicate. The production log already records a removal
decided with **zero heartbeat consultation** (`SiteWatchdog-T227 | REMOVED | gh PR MERGED`) — that
one happened to be safe; nothing in the code made it so.

This is the quietest face of detect-then-discard: the guard is not swallowed, not redirected, not
unchecked — it is **never armed**. Nothing errors, so no runtime signal exists for any check to
find. `unmeasured-safe-delete` looks for a *measurement whose failure* falls through; here no
measurement is ever attempted, because a pure-PowerShell `-match` on a string simply returns false.

**Fix (GetWorkDone repo):** derive the convention from the same SSOT that *names* the directories,
or fail closed when a leaf is unrecognised.

---

## HIGH-3 — the autosave reports a rescue branch that may hold only part of the work

**File:** `worker-wrapper.ps1:755-757` · **Class:** detect-then-discard · **Gate:** `clobbered-exit`

```powershell
git add -A *> $null
git commit -m "autosave: $TaskId uncommitted work at worker exit (turn cap or crash)" *> $null
if ($LASTEXITCODE -eq 0) {
  ... "dirty tree committed to rescue branch '$branch' ... Dispatcher: review and land manually."
```

`git add -A`'s exit code lands in `$LASTEXITCODE` and is **destroyed by `git commit` on the very
next line, before anything reads it**. The test on line 757 therefore reports on the commit alone;
the add's failure is structurally unobservable.

Why that matters: `git add -A` can fail while *partially* staging — a file still locked by a
descendant the wrapper force-killed moments earlier (this block runs immediately after a process-
tree kill), or a MAX_PATH overrun under `node_modules`. The commit then succeeds on the partial
staging, returns 0, and the wrapper writes a confident *"dirty tree committed to rescue branch"*
line to both the stderr log and the heartbeat. The dispatcher is told the rescue branch holds the
worker's work; it holds a fragment, and nobody rechecks because the run reported success.

This defeats T-231's entire purpose (eight workers that lost uncommitted engineering at their turn
cap), in the code written to prevent it.

**Fix (GetWorkDone repo):** `$addRc = $LASTEXITCODE` immediately after the add, and test both.

---

## HIGH-4 — an unchecked `cd /d` lets the keeper commit and push the wrong repository

**File:** `keeper-tick.cmd:26, :212, :256` · **Class:** silent failure + detect-then-discard · **Gate:** `unchecked-chdir`

```bat
cd /d C:\Abhay\Ventures\claude-best-practices
```

Reproduced on this host with a real `cmd.exe`:

```
BEFORE cwd=C:\Abhay\GetWorkDone
The system cannot find the path specified.
AFTER  cwd=C:\Abhay\GetWorkDone  errorlevel=1
SCRIPT CONTINUED
```

A failed `cd /d` sets `errorlevel 1`, **does not abort the script**, and leaves the working
directory unchanged. Every subsequent `git add -A` / `git commit` / `git push` therefore runs
against whichever repository the script was already in. Line 212 is the single hardcoded absolute
path in a file whose own header records that exactly this class of hardcoding was *"dead on the PC
and only working by coincidence on the VPS"* — the one path never migrated to `%~dp0`. Its failure
would commit the bus checkout's entire working tree under a `"keeper: tick"` message; the
symmetric failure at :256 would push the hub clone to the hub's own `main`.

What makes it *silent* rather than loud: **none of the tick's existing guards can see it.** The
`KT_ON_MAIN` assertion is true in the wrong repo too, and the commit guard matches on message text
the wrong repo also produces. Every guard passes and the tick is logged healthy.

**Fix (GetWorkDone repo):** `if errorlevel 1 ( alert & exit /b 1 )` immediately after each chdir.

---

## MEDIUM findings (reported, not gated)

Real defects with a narrower blast radius; recorded here so a later wave can pick them up. Per the
learning-to-gate doctrine they carry no gate yet — the recurrence ratchet escalates any of these to
a gate on a second occurrence.

**MEDIUM-1 — the host-memory gate degrades to "healthy" when it cannot measure.**
`preflight-guard.ps1:182` with `:61-63` and `:73-75`. `Get-HostCommitPercent` returns `$null` on a
WMI failure and is then coerced to `0.0`; `Get-LiveWorkerCount` returns `0` on a WMI failure. Both
sentinels sit on the *non-blocking* side of their thresholds, so the gate that exists to prevent
the 2026-08-24 dispatcher-killing OOM opens wide exactly when the host is sickest (WMI is *more*
likely to fail under memory pressure, and both halves use the same subsystem, so they fail
together). Contradicts the file's own stated design at `:19` ("BLOCKS the launch loud — never a
silent skip"). Note this is an *input-laundering* defect, not an unread-verdict one, which is why
T-071's `unchecked-precondition` does not catch it.

**MEDIUM-2 — the terminal heartbeat is written before the autosave it attests to.**
`worker-wrapper.ps1:709` writes `EXITED <code>` to the heartbeat; the autosave block (725-772) then
runs for potentially many seconds (`git status` over a large tree, `git add -A` over
`node_modules`) and *appends* prose to that same file at `:743`/`:760`. Two consequences: a keeper
or janitor reading `EXITED` may reclaim the workspace while `git add -A` is still writing inside
it; and the append both violates the heartbeat's documented two-line PID/timestamp contract and
refreshes its `LastWriteTime`, resetting the janitor's freshness clock.

**MEDIUM-3 — the orphan-process kill selector matches none of the live workspace shapes.**
`janitor-worktrees.ps1:319`. The regex is case-sensitive on `-t` while real directories use `-T149`,
and the `T-<id>-<repo>` prefix form is not covered, so the OOM-remediation sweep's kill path is
unreachable for the processes on this host — and `SKIPPED-not-worktree` results are filtered out of
the report, so nothing surfaces. Same root cause as HIGH-2 (a hardcoded convention literal never
validated against what is on disk); the `dead-convention-guard` gate is scoped to leaf guards on a
destructive path and does not currently cover command-line selectors.

**MEDIUM-4 — the janitor's freshness stamp is written unconditionally.**
`janitor-worktrees.ps1:818`. The stamp is written on every path that reaches the end of the script,
including one where every repo threw and was caught. Because the stamp is the self-gate, a run in
which all repos errored writes a fresh "I ran successfully" marker and suppresses the next
`$IntervalDays` of attempts, exiting 0.

## LOW findings

**LOW-1 — `bus-guard.sh:8` repairs `PATH` from a hardcoded directory without verifying the tools
resolve.** `[ -d "/c/Program Files/Git/usr/bin" ] && PATH=...` — the guard's whole purpose is to
survive Task Scheduler's bare Windows `PATH` (its header documents the 2026-07-20 incident where
`grep` was silently "not found" while the script still reported clean), but it tests for a
*directory* rather than confirming `grep`/`awk`/`find` are callable. On this host the control case
passes (a planted secret is caught) and the stripped-PATH case still resolved via Git Bash
builtins, so this is a latent risk rather than a currently-reproducing defect — recorded at LOW for
that reason.

**LOW-2 — `bus-relay.sh:68` sets `changed=1` from a file's existence, not from this run's work.**
`[ -f heartbeats/.tg-offset ] && changed=1` is true on every run after the first, so the commit
path is entered even when nothing changed. Harmless today (the commit is a no-op and its failure is
tolerated), but it is the same `changed=1`-from-existence shape T-071 recorded as MEDIUM-1.

## Verified-correct (adversarially checked, no defect)

Recorded so the report does not read as "everything is broken", and so a later wave does not
re-spend effort here:

- `trust-workspace.py` — genuinely hardened. `O_CREAT|O_EXCL` lock, bounded wait that *raises*
  rather than falling through to an unlocked write, and `os.replace()` atomic write. Its non-zero
  exit is properly consumed by `worker-wrapper.ps1:507-529` (T-071 HIGH-3's gate did its job).
- `janitor-worktrees.ps1:153-157` — T-167's `KEPT-status-failed` veto is correct; `$statusExit` is
  captured before any other native call can clobber it.
- `janitor-worktrees.ps1:172-173` — `merge-base --is-ancestor` fails **closed** (128, not 1), so an
  unresolvable ref keeps the worktree.
- `janitor-worktrees.ps1:234-240` — `git worktree remove`'s exit code is checked and surfaced.
- `preflight-guard.ps1:200-203, 234-236` — repo-identity guard fails closed on a `$null` remote;
  self-identity uses `Resolve-Path` on both sides.
- `keeper-tick.cmd:311` — the nested `if errorlevel 1` correctly reads the *inner* push's code
  (batch evaluates `if errorlevel` at execution time); `:273/:283/:297` delayed expansion is sound;
  `:328`'s `set KT_CONF_RC=!errorlevel!` is correctly placed *before* the intervening `type`;
  `:44/:78/:269` `for /f` sites each clear the variable first, so a failed capture fails safe.
- `bus-sync.sh:14-23` — `bus_push` is correct: rebase-retry ×3 with a loud non-zero on exhaustion.

## Gates landed (learning-to-gate doctrine)

Each HIGH became a deterministic check in `scripts/check_fleet_script_health.py`, landed as its own
commit with its own self-tests. Every positive test was verified to **fail when the check is stubbed
to `return []`**, so none of them is vacuous.

| Finding | Gate | Self-tests |
|---|---|---|
| HIGH-1 | `unmeasured-reset` | `test_unmeasured_reset_is_flagged` / `test_unpushed_probe_without_a_hard_reset_is_not_flagged` / `test_neighbouring_exit_test_does_not_clear_the_probe` |
| HIGH-2 | `dead-convention-guard` | `test_dead_convention_guard_is_flagged` / `test_live_convention_guard_is_not_flagged` / `test_dead_convention_guard_stays_silent_without_ground_truth` / `test_non_leaf_match_is_not_a_convention_guard` |
| HIGH-3 | `clobbered-exit` | `test_clobbered_exit_is_flagged` / `test_native_call_pair_with_no_exitcode_read_is_not_flagged` / `test_exitcode_tested_between_the_two_calls_is_not_flagged` / `test_differently_indented_calls_are_not_a_straight_line_sequence` |
| HIGH-4 | `unchecked-chdir` | `test_unchecked_chdir_is_flagged` / `test_chdir_without_git_mutation_is_not_flagged` / `test_chdir_guarded_by_a_later_line_is_not_flagged` |

Two design decisions worth carrying forward:

- **`dead-convention-guard` refuses to guess.** It fires only when real directory names are supplied
  via `--workspace-dir`; on CI, where the fleet is not on disk, it returns nothing rather than
  inventing a verdict. Scoring an unmeasurable claim is the very defect these gates exist to stamp
  out, so the gate must not commit it. It also tests **coverage, not zero-match**: one legacy
  directory still matches the janitor's literal, so a strict "matches nothing" rule would score a
  guard protecting 2.5% of the fleet as healthy.
- **`unmeasured-reset` tests the probe line, not a window.** In the live file a `|| { ...; return
  2; }` sits one line below the probe and belongs to the *rebase* — a symmetric window would read
  the shipped defect as already handled. A fail-closed upstream resolution *before* the probe does
  clear it.

## Ratchet floor

`scripts/tests/fleet-ratchet-floor.json` had legitimately reached zero on 2026-08-19. This PR
repopulates it with three entries (`bus-sync.sh/unmeasured-reset`,
`keeper-tick.cmd/unchecked-chdir`, `worker-wrapper.ps1/clobbered-exit`) and removes the now-false
`zero_evidence` block.

This is **not** the forbidden "add a line to excuse a new defect". Those defects were invisible on
2026-08-19 because no check for their classes existed; they became visible only when this wave built
the gates. The defects live in the **GetWorkDone fleet repo**, which this hub PR cannot modify — so
the honest outcome is to make them visible and hold the line, with per-entry fix notes recorded in
`open_finding_notes` for whoever lands the fleet-side fixes. Shrinking the floor still requires the
same evidence contract as before.

`dead-convention-guard` is deliberately **absent** from the floor: it needs `--workspace-dir` ground
truth that the default checker invocation does not supply, so it does not fire in the ratchet run.
