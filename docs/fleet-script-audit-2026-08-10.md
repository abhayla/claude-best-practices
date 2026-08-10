# GetWorkDone fleet-script adversarial audit — 2026-08-10 (T-071)

Read-only audit of every fleet script at `C:\Abhay\GetWorkDone\*.{sh,ps1,py,cmd}` for the three
defect classes the contract names: **silent failures** (an error swallowed or redirected away
without a surfaced signal), **races** (unguarded concurrent file/state access), and **un-gated
defect classes** (a repeat of `check_fleet_script_health.py`'s "detect-then-discard" shape — a
script correctly detects its failure condition, then throws the signal away).

**Scope audited:** 24 scripts / 1,654 lines — 8 `.sh`, 10 `.ps1`, 4 fleet `.py` (+ the fleet's own
`test_fleet_script_fixes.py`), 2 `.cmd`. Nothing under `C:\Abhay\GetWorkDone` was modified.

| Severity | Count |
|---|---|
| HIGH | 3 |
| MEDIUM | 2 |
| LOW | 2 |

Every HIGH was reproduced empirically on this host before being written down (repro commands in
each finding), and every HIGH has a gate landed in this PR with a self-test that proves the gate
fires on the defect shape and stays quiet on the fixed shape.

---

## HIGH-1 — a called PowerShell script's non-zero exit is invisible to its caller, *after* the caller has already burned the interval marker

**Files:** `feature-adoption-sweep.ps1:85`, `parked-digest.ps1:50`, `gate-audit.ps1:42`
(all three callers of `notify-owner.ps1`; zero of the three test the result)

`$ErrorActionPreference = "Stop"` — set at the top of all three — does **not** trap a non-zero
exit from a script invoked with the call operator `&`. It governs PowerShell *error records*, not
a child script's exit code. Verified on this host:

```
$ErrorActionPreference = "Stop"
& child.ps1          # child does `exit 3`
→ child running
→ PARENT CONTINUED after child exit 3 (LASTEXITCODE=3)
→ parent exit=0
```

So when owner delivery fails, the caller prints its success line (`SWEEP-OK` / `DIGEST-OK`) and
exits 0. The keeper's `if errorlevel 1` check in `keeper-tick.cmd:93,99` therefore never fires —
the tick records a healthy delivery that did not happen.

The self-gating interval marker makes this **lossy, not merely silent**. Both weekly scripts
write the marker *before* delivery:

- `feature-adoption-sweep.ps1:60` — `Set-Content -Path $marker` … delivery at line 85
- `parked-digest.ps1:48` — `Set-Content -Path $marker` … delivery at line 50

`feature-adoption-sweep.ps1` additionally advances `$baselineFile` at line 79, so the *next* run
reports only features newer than a baseline whose card the owner never received. A failed
delivery costs the owner that entire interval's card, with no retry and no log line. This is
exactly the class `Set-RetryTomorrow` (line 66) was built for — but that recovery path only
covers the `claude -p` sweep failing, not the delivery failing.

`gate-audit.ps1` shares the un-checked call; its stamp is written after delivery (line 44), so it
loses the card but not the window — a smaller blast radius, same root cause.

**Gate:** `ps-unchecked-call` in `check_fleet_script_health.py`.

---

## HIGH-2 — the Telegram offset is advanced before the answers it consumed are durably written

**Files:** `read-answers.ps1:49`, `bus-relay.sh:41` (same shape, both transports)

`read-answers.ps1` writes the new `getUpdates` offset unconditionally at line 49, then writes the
parsed answers into `OWNER-QUESTIONS.md` at line 50:

```powershell
Set-Content -Path $OffsetFile -Value $maxUpdate -Encoding ascii      # line 49 — consumes updates
if ($applied -gt 0) { Set-Content -Path $Questions -Value $q ... }   # line 50 — may fail
```

Telegram's `getUpdates` **permanently discards** any update below a confirmed offset. If the
second write fails, the answers are unrecoverable — not delayed, gone. The owner replied and the
fleet will never see it, while the script exits 0 and prints `APPLIED n owner answer(s)`.

This is not hypothetical on this box: `cost-rollup.py:38-49` documents live concurrent
file-locking here ("16+ concurrent claude.exe on this box") and carries a retry helper for exactly
that reason. `read-answers.ps1` has no such retry. Reproduced with a real exclusive lock:

```
offset advanced to 999
questions write FAILED: IOException
questions file still contains: old
=> offset consumed the updates, answers were never written: PERMANENT LOSS
```

`bus-relay.sh:41` is the same ordering in the relay's Python leg (`if mx: open('.tg-offset','w')`
precedes `if applied: open(qf,'w')`), so the Hostinger path can lose answers identically.

**Correct shape:** write the payload first, and advance the offset only after that write is
confirmed — the offset is a commit point, so it must be last.

**Gate:** `offset-before-write` in `check_fleet_script_health.py`.

---

## HIGH-3 — a launch precondition runs, fails, and the launch proceeds anyway

**File:** `worker-wrapper.ps1:30-32`

```powershell
$trustScript = Join-Path $StateRoot "trust-workspace.py"
if (Test-Path $trustScript) {
  python $trustScript $RepoPath      # exit code never examined
}
```

The file's own comment (lines 24-28) states the purpose: a fresh clone-on-demand workspace is
untrusted, and headless `claude -p` **hard-blocks on the trust dialog instead of running** — the
T-021/T-017 class defect. That makes this a *precondition*, not a nicety: if it fails, the worker
launched 9 lines later cannot succeed.

Every realistic failure is silent here — `python` absent from Task Scheduler's bare PATH (the
fleet's own recurring trigger, fixed twice already in `break-detect.sh` and
`checkpoint-pr-merge.sh` but never here), `USERPROFILE` unset (`trust-workspace.py:24` raises
`KeyError`), or `.claude.json` locked by a concurrent worker. Verified:

```
python nonexistent-trust.py C:\x
→ can't open file ... [Errno 2] No such file or directory
→ WRAPPER CONTINUED to launch worker (LASTEXITCODE=2)
```

The worker then burns its dispatch on the trust wall and writes a `result.json` containing the
dialog text. `worker-wrapper.ps1` is also the one fleet script with **no** PATH-hardening preamble,
so it is the most exposed to the failure mode its siblings already fixed.

**Gate:** `unchecked-precondition` in `check_fleet_script_health.py`.

---

## MEDIUM-1 — `changed=1` is set from a file's existence, not from this run's work

**File:** `bus-relay.sh:44`

```bash
[ -f heartbeats/.tg-offset ] && changed=1
```

`.tg-offset` persists from the first run onward, so after that first run this is unconditionally
true whenever `$BOT` is set. Every relay invocation then reaches the `git add -A` / commit / push
block at lines 46-47 and pushes a "bus-relay: outbound pings sent + inbound answers" commit
regardless of whether anything was sent or applied. Confirmed:

```
changed=1  (1 means it will commit+push as if answers were applied)
```

Not a data-loss defect — the commit is a no-op when the tree is clean (`git commit` fails, the
`&&` short-circuits, `bus_push` never runs). The cost is a misleading signal: the commit message
asserts work that may not have happened, and the fleet's own audit trail is the thing being
polluted. Should be set from the Python leg's `applied` count.

## MEDIUM-2 — `contract-lint.py` blocks on assumption words appearing anywhere, including inside a fix that names the class

**File:** `contract-lint.py:11-13, 92-93`

`ASSUMPTION_MARKERS` is searched against the whole contract text with no field scoping, so the
words `assume`, `probably`, `not sure`, `tbd` block a dispatch even when they appear in a
`status_log` entry, a quoted prior finding, or a DoD that says "do not assume X". A contract
describing this very audit ("scripts that assume the interpreter exists") would be blocked.

This is a false-positive/availability defect rather than a silent failure — it fails loud and
closed, which is the safe direction. Flagged for scoping to the body/DoD, not gated.

## LOW-1 — health-poll episode key degrades to a fallback on a short parse

**File:** `break-detect.sh:141-144`

`read -r hdays hdate hcount <<< "$hparsed"` leaves `hdate`/`hcount` empty when the Python leg
prints fewer than three fields, and the episode signature falls back to `${ep_start:-$hdate}`
(also empty). Confirmed: `hdays=[2] hdate=[] hcount=[]` → "WOULD FILE with empty date". The card
is still filed (loud, not silent) but its episode key degrades, weakening the
one-card-per-episode dedup. Low blast radius; noted, not gated.

## LOW-2 — `ipo-audit.py` bare `except:` swallows the comparison error

**File:** `ipo-audit.py:56-57`

`try: match = ... except: match = None` renders `N/A` for a genuine parse/type error exactly as it
does for legitimately-absent data, so a systematic comparison bug reads as missing upstream data.
Read-only reporting script, not fleet control flow — noted, not gated.

---

## Verified-correct (adversarially checked, no defect)

Recording these so a later audit does not re-open them:

- **`keeper-tick.cmd:161-166`** — nested `if errorlevel` inside an `if` block. Suspected stale-value
  read; **disproved on this host**: `if errorlevel` is evaluated at execution time (unlike
  `%ERRORLEVEL%`, which expands at parse time), so the retry's verdict is read correctly. Test:
  outer `call fail.cmd` → inner `call ok.cmd` → correctly printed "nested block correctly saw the
  retry succeed".
- **`bus-relay.sh:23`** — bare `python3` with no interpreter resolution. Under `set -e` (line 4) a
  missing interpreter aborts the script with exit 127, loudly. Not the silent shape.
- **`break-detect.sh`** — every external call (`gh api` line 66, `curl` line 127, the Python parse
  line 132) captures its exit code separately and `continue`s loudly rather than treating failure
  as "healthy". This is the reference implementation of the correct shape.
- **`cost-rollup.py`**, **`checkpoint-pr-merge.sh`** — both 2026-08-03 findings are genuinely fixed
  (mtime-keyed supersede path; `repos_rc` capture + loud empty-registry abort). The stale ratchet
  entries in `test_fleet_script_health.py` are removed in this PR.

---

## Gates landed (learning-to-gate doctrine, `docs/governance/learning-to-gate-doctrine.md`)

Each HIGH became a deterministic check in the existing `scripts/check_fleet_script_health.py` —
the established home for this defect family — rather than a parallel gate. Each ships with a
fires-on-the-defect / quiet-on-the-fix self-test pair, plus a live-fleet regression assertion.

| Finding | Check | Self-test |
|---|---|---|
| HIGH-1 | `ps-unchecked-call` | `test_ps_unchecked_script_call_is_flagged` / `..._lastexitcode_tested_is_clean` |
| HIGH-2 | `offset-before-write` | `test_offset_advanced_before_payload_write_is_flagged` / `..._after_payload_write_is_clean` |
| HIGH-3 | `unchecked-precondition` | `test_unchecked_precondition_call_is_flagged` / `..._checked_precondition_is_clean` |

All three are confirmed to fire against the live fleet and are recorded in
`KNOWN_OPEN_FLEET_FINDINGS` as the ratchet floor — that set may only shrink as the fleet repo
lands the fixes (fleet-repo edits are out of scope for this hub PR, which delivers the gates).
