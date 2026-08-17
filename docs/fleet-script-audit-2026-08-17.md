# GetWorkDone fleet-script adversarial audit — 2026-08-17 (T-167, wave 2)

Read-only audit of every fleet script at `C:\Abhay\GetWorkDone\*.{sh,ps1,py,cmd}` for the three
defect classes the contract names: **silent failures** (an error swallowed or redirected away
without a surfaced signal), **races** (unguarded concurrent file/state access), and **un-gated
defect classes** (a repeat of `check_fleet_script_health.py`'s "detect-then-discard" shape).

**Scope audited:** 27 scripts / 2,252 lines at the GWD root — 8 `.sh`, 10 `.ps1`, 7 `.py`,
2 `.cmd`. Nothing under `C:\Abhay\GetWorkDone` was modified. The prior audit
(`docs/fleet-script-audit-2026-08-10.md`, T-071) and its landed gates were read first; its
"Verified-correct" list was treated as closed and is not re-litigated.

| Severity | Count |
|---|---|
| HIGH | 4 |
| MEDIUM | 3 |
| LOW | 1 |

Every HIGH was reproduced empirically on this host before being written down, and every HIGH has
a gate landed in this PR with a self-test proving the gate fires on the defect shape and stays
quiet on the fixed shape. Repro scripts and raw output:
`C:\Abhay\GetWorkDone\evidence\2026-08-17-T-167\`.

**The headline finding is HIGH-1: the previous audit's own ratchet had been silently disabled**,
which is why HIGH-2 went unreported for five days despite a gate existing that detects it.

---

## HIGH-1 — the ratchet floor was emptied on a false-clean, because CI cannot see the fleet

**Files:** `scripts/tests/test_fleet_script_health.py:842` (pre-fix), commit `a5cde31` (2026-08-12)

Every fleet-dependent assertion in `test_fleet_script_health.py` is guarded by:

```python
fleet = Path("C:/Abhay/GetWorkDone")
if not fleet.exists():
    pytest.skip("fleet checkout not present on this host")
```

Six assertions carry that guard, including both halves of the ratchet
(`test_real_fleet_has_no_unknown_silent_failure_findings` and
`test_known_open_fleet_findings_still_reproduce`). CI runs on `ubuntu-latest`, where that path
never exists — so **on CI all six skip, and "validate green" means only "the assertions did not
run."**

Commit `a5cde31` ("test(fleet-health): empty the known-open ratchet — all six T-071 findings
fixed by 2026-08-12") deleted the entire floor on that basis. It merged green. The claim was
false: re-running the checker on the fleet host on 2026-08-17 reproduces **all six verbatim**,
same files, same checks:

```
T-071 six still reproducing: [('bus-relay.sh','offset-before-write'),
  ('feature-adoption-sweep.ps1','ps-unchecked-call'), ('gate-audit.ps1','ps-unchecked-call'),
  ('parked-digest.ps1','ps-unchecked-call'), ('read-answers.ps1','offset-before-write'),
  ('worker-wrapper.ps1','unchecked-precondition')]
MISSING (genuinely fixed): []
NEW since T-071: [('keeper-tick.cmd','discarded')]
```

Note the last line. Because the floor was empty *and* the assertion that would have caught a new
defect only runs on the fleet host, a **new** `keeper-tick.cmd` finding sat undetected from
2026-08-12 to 2026-08-17.

This is the checker's own defect class, one level up and inside the checker: the gate correctly
DETECTED the defects, and its bookkeeping threw the signal away. A ratchet whose only enforcement
runs where nobody looks is prose.

**Gate:** the floor moves out of the Python literal into a committed artifact,
`scripts/tests/fleet-ratchet-floor.json`, carrying `observed_on` / `observed_by` /
`reproduce_with`. The new `test_ratchet_floor_is_evidenced` validates the ARTIFACT, not the
fleet — so it is **host-independent and runs on CI**. Emptying the floor now fails there. Proven
by replaying `a5cde31` against it:

```
AssertionError: the ratchet floor is EMPTY. That is a strong claim ... If you are emptying it
because CI was green, STOP: CI cannot see the fleet and skips every fleet-dependent assertion in
this file (T-167 HIGH-1).
```

Negative controls (`test_floor_guard_rejects_the_shipped_defect`,
`test_floor_guard_rejects_malformed_and_typoed_entries`) prove the guard rejects an emptied,
malformed, or typo'd floor rather than merely accepting a good one.

---

## HIGH-2 — `git add` / `git commit` / `git checkout` verdicts discarded, then the push reports the tick healthy

**File:** `keeper-tick.cmd:14, 29, 160, 161, 162`

The existing `silent-push` gate covers line 168's `git push` — and that one is correctly retried
and logged. But the commands that *produce* what gets pushed are unchecked:

```bat
git checkout main --quiet          # line 160 — no redirect, and nothing reads errorlevel
git add -A >nul 2>&1               # line 161
git commit -m "keeper: tick" --quiet >nul 2>&1   # line 162
```

A push of an unchanged (or wrong) ref **succeeds**, so `if errorlevel 1` never fires. Two
distinct failures, both reproduced end-to-end against a real repo and remote:

**(a) failed `add` → work never lands.** A concurrent `.git/index.lock` — not hypothetical: the
sweep at line 129 runs `claude -p ... --add-dir C:\Abhay\GetWorkDone` against this same clone —
makes `git add -A` exit 128 into its sink:

```
TICK_REPORTED_HEALTHY
--- important.md present upstream? count: 0
--- still untracked locally: ?? important.md
```

**(b) failed `checkout` → work lands on the wrong branch.** Line 158's own comment concedes "the
sweep may have switched branches". With a dirty tracked file the checkout aborts:

```
error: Your local changes to the following files would be overwritten by checkout: f
TICK_REPORTED_HEALTHY
--- branch now: sweepwork
--- origin/main has bus-item.md? count: 0
--- bus-item.md actually committed onto: sweepwork
```

The tick commits onto the stray branch, `git push origin main` pushes the untouched `main` ref
and exits 0, and `keeper-tick-failures.log` stays empty. Lines 5-6 of the same file call the
clone staying on main a **HARD INVARIANT**, citing the live 2026-07-16 stranded-clone incident —
the enforcement of that invariant is this unchecked `checkout`.

Fixing (a) does not fix (b): with a clean-but-stray branch, `add` and `commit` both succeed and
only the branch is wrong.

**Gate:** `silent-staging`. Scoped to scripts that actually push (the push is what launders the
failure into a healthy report), and it clears `set -e` shells and `bus_push()`-style retry loops
whose push IS tested — `bus-sync.sh` is the fleet's reference-correct implementation and must
stay clean, verified by `test_bus_push_retry_loop_is_not_flagged`.

---

## HIGH-3 — the worktree-deletion safety predicate treats "could not measure" as "measured safe"

**File:** `janitor-worktrees.ps1:144` (the verdict feeds the `git worktree remove` at line 215)

```powershell
$status = git -C $wtPath status --porcelain --untracked-files=all 2>$null
$statusLines = @($status | Where-Object { $_ -ne "" })
if ($statusLines.Count -gt 0) { return @{ Verdict = "KEPT-dirty"; ... } }
```

This is the highest-blast-radius script in the fleet — it deletes things. Two independent legs,
both verified:

**(a) gitignored-blind.** `--untracked-files=all` does **not** include ignored paths (`--ignored`
does). Every worker artifact under `build/`, `dist/`, `*.log`, `.env`, `coverage/` is invisible
to the veto, and `git worktree remove` shares the blindness so it does not refuse either:

```
porcelain --untracked-files=all -> 0 lines          (verdict: CLEAN)
with --ignored                  -> !! build/artifact.txt, !! run.log
```

**(b) failure-scores-clean.** `$LASTEXITCODE` is never read and stderr is discarded, so a
**failed** status prints nothing, `Count -eq 0`, and the code falls through exactly as if the
tree were pristine:

```
git -C <unreadable> status ... -> LASTEXITCODE=128, statusLines.Count=0
VERDICT: falls through as CLEAN -> eligible for deletion
```

Realistic trigger: the `.git` gitdir link momentarily unreadable under a concurrent
`worktree prune`/`repair` from another of the 16+ workers, or an AV/OneDrive lock. The janitor
then reports `REMOVED | ancestor of origin/main` and deletes a worktree holding live uncommitted
work. The file's own header at lines 53-54 promises "Every native-command outcome below is
checked explicitly via `$LASTEXITCODE`" — this is the one call that is not.

**Gate:** `unmeasured-safe-delete`. Deliberately scoped to files containing `worktree remove`, so
it never fires on ordinary `git status` usage (`test_status_without_a_deletion_is_not_flagged`).
Each leg is reported independently
(`test_ignored_flag_alone_does_not_clear_the_untested_exit_code`).

---

## HIGH-4 — read-modify-write of shared global state, truncating, with no lock and no atomic replace

**Files:** `trust-workspace.py:52`, `cost-rollup.py:123`

```python
with io.open(claude_json_path, "w", encoding="utf-8") as f:   # truncates BEFORE writing
    json.dump(data, f, indent=2)
```

`worker-wrapper.ps1:29-31` runs `trust-workspace.py` on **every** worker launch, and the fleet
runs 16+ concurrent workers. The target is `~/.claude.json` — the **global** Claude Code config
(113,963 bytes on this host: oauth account plus every project's trust and permissions). Two
failure modes, both reproduced deterministically (5/5 runs):

**(a) lost update.** A reads, B reads, B writes, A writes its stale snapshot:

```
A (T-200, wrote last) trusted: True
B (T-201, wrote first) trusted: False
=> LOST UPDATE: B's trust entry was silently overwritten by A's stale snapshot.
=> B's worker then hits the trust wall; its result.json is the dialog text, 0 turns,
   and trust-workspace.py exited 0 -- the fleet records a healthy launch.
```

That is the exact T-021/T-017 class defect `trust-workspace.py` was written to prevent,
re-introduced by the way it writes.

**(b) corruption.** `open(path, "w")` truncates before the first byte, so any failure mid-dump
(process kill — the fleet kills workers; disk-full; AV lock) leaves the global config truncated:

```
size before=3433  after=420
=> CORRUPT: JSONDecodeError: Expecting property name enclosed in double quotes
=> Every Claude Code session on the box is now broken, not just the fleet worker.
```

`cost-rollup.py:123` is the same shape on the bus-synced `costs.jsonl` that the daily token
ceiling gates on. Note its `open_with_retry` helper is **not** a lock — it retries past a sharing
violation, which orders nothing; its own docstring documents the concurrency it does not solve.

**Gate:** `unlocked-global-rewrite`. Appends are excluded (mode `"a"` cannot erase another
writer's bytes), and both correct shapes clear it: temp-file + `os.replace`
(`test_unlocked_global_rewrite_is_flagged`'s fixed form) and a real inter-process lock
(`test_locked_rewrite_is_not_flagged`). `test_retry_helper_alone_does_not_clear_the_finding`
pins the trap that a retry helper must not be mistaken for serialisation.

---

## MEDIUM-1 — the checker buried 83% of its own signal in worktree noise

**File:** `scripts/check_fleet_script_health.py:85` (`EXCLUDED_DIRS`)

`EXCLUDED_DIRS` excluded `workspaces` and `work` but not `worktrees` — the per-task **hub**
worktrees `/get-work-done` creates under the fleet root. Measured before the fix:

```
total findings      : 48
from worktrees/ NOISE: 40   (83%)
real fleet findings :  8
```

The noise is hub files the hub's own CI already gates, reported once per live worktree —
**including the checker and its own test file matching their defect-defining regexes**, because
`_is_pattern_source()` excluded only the single resolved path the process runs from, so every
copy defeated it. A gate whose real findings sit under 40 duplicates is one nobody reads, which
is the same signal-discarded failure the gate exists to catch.

**Fixed** (not merely gated, since the defect is in the hub's own file): `worktrees` added to
`EXCLUDED_DIRS`, and `_is_pattern_source()` now matches by filename so no copy can defeat it.
Regression-covered by the pre-existing `test_checker_does_not_flag_itself`. 48 → 16 findings, all
real.

## MEDIUM-2 — `estate-conformance-check.ps1` reports "clean" when its checks could not run

**File:** `estate-conformance-check.ps1:10, 39-40`

`$ErrorActionPreference = "SilentlyContinue"` is set file-wide; line 39 dereferences `$fw.FullName`
one line **before** line 40's `$fw -and` null-guard. When no `5Wealths` dir is found, line 39
throws, the preference swallows it, check 3 is silently skipped, and the script prints
`ESTATE-CONFORMANCE: clean` and exits 0. The blanket preference covers checks 1 and 2 as well, so
a permission-denied `Get-ChildItem` is indistinguishable from a clean estate — on a detector whose
entire job is detection, and whose exit 0 tells the owner the estate is fine.

Ranked MEDIUM, not HIGH: on this host `$EstateRoot` resolves to `C:\Abhay` where the directories
do exist, so the null path is real but conditional (a VPS/PC divergence or a `5Wealths` rename
triggers it). Mechanically gateable (file-scope `SilentlyContinue` + a verdict-bearing exit code)
but **not gated in this PR** — one un-reproduced-in-situ finding does not yet justify a check that
would fire on every PowerShell script using the preference legitimately. Recorded for the
recurrence ratchet: if it fires a second time, it converts to a gate.

## MEDIUM-3 — the live-worker guard skips exactly the worktree class most likely to be deleted

**File:** `janitor-worktrees.ps1:132`

```powershell
if ($leaf -match '-wt-t(\d+)$') {
```

The `$` anchor requires the leaf to END in digits, so `-checker`-suffixed worktrees never match
the live-task guard at all. These names are real, from the fleet's own evidence tree:
`gorefer-wt-t104-checker`, `gorefer-wt-t098-checker`, `gorefer-wt-t046-check`. A second,
independent half: even where the guard is active it looks for `T-<id>.hb`, but checker heartbeats
on this box carry a `C` suffix — `T-143C.hb`, `T-146C.hb`, `T-149C.hb`, `T-156C.hb` all exist.

Scenario: a checker runs in `gorefer-wt-t104-checker` against already-merged work (the normal
case — checkers verify *landed* work, so the ancestor probe passes) and is clean because it only
reads. The guard never fires and the worktree is deleted out from under the running checker.

Ranked MEDIUM, not HIGH: **no sibling worktree exists on this host right now**, so there is no
live instance — the class is real and recurring but currently unexercised. Not cleanly gateable
by regex (it is a naming-convention mismatch between two directories); the honest form is a
convention ratchet asserting every live worktree leaf resolves to a heartbeat path the guard's
regex actually matches. Recorded, not gated.

## LOW-1 — `audit-pipeline.ps1` overwrites the previous report with an empty file and prints success

**File:** `audit-pipeline.ps1:12`

`try { ($r | ConvertFrom-Json).result | Out-File $out } catch { $r | Out-File $out }` — when
`claude` produces no stdout, `$r` is `$null`, `ConvertFrom-Json` throws, and the catch writes
`$null`, leaving a 3-byte BOM-only file that **overwrites** the prior run's report. Lines 19-25
then print `PIPELINE-DONE` and `RECONCILE-STATUS: consistent`. A total pipeline failure renders as
a consistent, completed pipeline. LOW because the byte count is printed (a human reading the
output can catch it) and this is a human-facing evidence tool with no keeper call site — not
unattended fleet control flow.

---

## Verified-correct (adversarially checked, no defect)

Recording these so a later audit does not re-open them:

- **`bus-sync.sh`** — `bus_pull`/`bus_push` are the reference-correct shape: exhaustion is loud
  and non-zero, and `reset --hard` is reachable only when `@{u}..HEAD` is empty. The `silent-staging`
  gate was explicitly narrowed so this file stays clean.
- **`bus-guard.sh`** — the awk windowed push scan, exclusion dirs and `exit $bad` are correct.
- **`checkpoint-pr-merge.sh`** — `repos_rc` capture, empty-registry abort and per-PR failure log
  all correct. `merged_any` never escapes its `while` subshell but is never read after the loop:
  dead, not harmful.
- **`keeper.cmd`** — its unchecked `git pull` folds into HIGH-2's fix; `keeper-tick.cmd:15`
  re-pulls, so the blast radius is a stale tick for one interval. Not a separate finding.
- **`notify-owner.ps1`** — `gate-audit.ps1`'s constant `TaskId` overwrites its ping file monthly,
  but the relay clears it within ~2 min and it fires every 27 days; not a realistic collision.
- **`break-detect.sh:92`** — `sed -i` replaces the inode, a real read-modify-write hazard, but
  `.break-state` has exactly one writer and one invoker under a scheduled task with
  `MultipleInstances: IgnoreNew`. **Not a defect today**; latent the moment a second invoker
  appears. Noted, deliberately not gated.
- **`worker-wrapper.ps1`**, **`read-answers.ps1`**, **`parked-digest.ps1`**, **`gate-audit.ps1`**,
  **`feature-adoption-sweep.ps1`** — their findings are the already-gated T-071 HIGHs, still open
  in the fleet repo and recorded in the ratchet floor.

---

## Gates landed (learning-to-gate doctrine, `docs/governance/learning-to-gate-doctrine.md`)

Each HIGH became a deterministic check in the existing `scripts/check_fleet_script_health.py` —
the established home for this defect family — with a fires-on-the-defect / quiet-on-the-fix
self-test pair.

| Finding | Gate | Self-test |
|---|---|---|
| HIGH-1 | `fleet-ratchet-floor.json` + `test_ratchet_floor_is_evidenced` (host-independent) | `test_floor_guard_rejects_the_shipped_defect` / `..._rejects_malformed_and_typoed_entries` |
| HIGH-2 | `silent-staging` | `test_silent_staging_is_flagged` / `test_unchecked_checkout_before_push_is_flagged` / `test_bus_push_retry_loop_is_not_flagged` / `test_set_e_shell_does_not_flag_silent_staging` / `test_mutation_in_a_script_that_never_pushes_is_not_flagged` |
| HIGH-3 | `unmeasured-safe-delete` | `test_unmeasured_safe_delete_is_flagged` / `test_status_without_a_deletion_is_not_flagged` / `test_ignored_flag_alone_does_not_clear_the_untested_exit_code` |
| HIGH-4 | `unlocked-global-rewrite` | `test_unlocked_global_rewrite_is_flagged` / `test_append_to_shared_ledger_is_not_flagged` / `test_retry_helper_alone_does_not_clear_the_finding` / `test_locked_rewrite_is_not_flagged` / `test_local_temp_file_rewrite_is_not_flagged` |
| MEDIUM-1 | fixed in-place (hub file) | `test_checker_does_not_flag_itself` |

MEDIUM-2, MEDIUM-3 and LOW-1 are deliberately **not** gated — each has one occurrence and no
in-situ reproduction, and a check built on a single unreproduced instance is how a gate becomes a
false-positive generator. They are recorded here for the doctrine's recurrence ratchet: a second
occurrence converts them to gates.

**The ratchet floor is 11 entries** (`scripts/tests/fleet-ratchet-floor.json`), all reproducing
as of 2026-08-17. Fixing them is fleet-repo work, out of scope for this hub PR which delivers the
gates — per the contract's artifact-placement rule, GWD is fleet runtime state, not a repo this
worker pushes PRs against.

**Reproducing the floor:** pass the dispatcher skill as an extra caller, as the tests do —
`python scripts/check_fleet_script_health.py C:/Abhay/GetWorkDone --caller .claude/skills/get-work-done/SKILL.md`.
Without the caller, `contract-lint.py` and `preflight-guard.ps1` additionally report as
`dead-gate`; those are invocation artifacts, not defects — both are wired into `/get-work-done`.
