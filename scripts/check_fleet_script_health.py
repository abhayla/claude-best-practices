#!/usr/bin/env python3
"""check_fleet_script_health.py — static gate for the fleet's "detect then discard" defect class.

The GetWorkDone fleet runs unattended (Task Scheduler + VPS cron) against a git bus that has no
CI. The 2026-07-20 audit found four HIGH defects that all share one shape: a script correctly
DETECTS its failure condition and then throws the signal away, so the fleet reports healthy while
doing nothing. This gate catches that shape statically, because the runtime symptom is silence.

Checks:
  interpreter  — a script invokes an interpreter (python3/python) that may not exist on the host,
                 with stderr suppressed, so absence is indistinguishable from a clean sweep.
  grep-count   — `$(grep -c ... || echo 0)` emits TWO lines on no-match ("0\n0"), so the following
                 numeric `[ "$x" -lt N ]` throws and takes the WRONG branch (debounce inversion).
  dead-gate    — a script whose docstring claims it gates/blocks dispatch but which has no call
                 site anywhere in the fleet: enforcement that is actually prose.
  discarded    — a .cmd line runs a guard whose non-zero exit is the verdict, then redirects that
                 exit into a log and never tests errorlevel.

The 2026-07-27 audit added two more of the same family — a verdict IS produced, but the check
reads the wrong property of it, so a failure scores as a pass:

  shape-only   — a health guard over `claude -p --output-format json` asserts the output's SHAPE
                 (`{` + `"type":"result"`) without asserting its OUTCOME (`is_error` / `subtype`).
                 A worker that dies on `error_max_turns` emits BOTH markers, so the failed run is
                 recorded as a healthy tick. (T-015 — a fleet audit that ran out of turns — is the
                 live instance: its result JSON passes the guard verbatim.)
  silent-push  — `git push` with its exit code discarded (`>nul 2>&1`, `>/dev/null 2>&1`, `|| true`)
                 and no bus_push/errorlevel/`if` retry. bus-guard.sh already treats this class as
                 blocking, but only matched the `|| true` spelling, so the redirect spelling in the
                 fleet's own keeper went unseen: a rejected push looks exactly like a landed one.

The 2026-08-03 audit added two more. Both are the "checked nothing, reported clean" shape rather
than "read the wrong property", and both were live-reproduced against the running fleet:

  stale-receipt — an append-only ledger keyed by a MUTABLE artifact's id, where the id is recorded
                 as "already seen" but the artifact's CONTENT is never re-checked. A receipt that is
                 rewritten after its first roll-up (retry overwrites `<task>.result.json`) freezes
                 the ledger at the superseded numbers forever. Live instance: costs.jsonl records
                 T-037 as sonnet/109,494 tok/$1.98 while the real T-037.result.json is
                 opus/119,515 tok/$4.14 — the budget ceiling gates on the under-count.
  unchecked-read — a registry/config read via an unguarded `$(python ...)`/`$(gh ...)` command
                 substitution whose exit code is never captured, feeding a loop that iterates zero
                 times and a script that then exits 0. "Read nothing" is indistinguishable from
                 "nothing to do" — the same class break-detect.sh's empty-registry guard fixed,
                 still live in checkpoint-pr-merge.sh (which also lacks its siblings' Python PATH
                 hardening, so Task Scheduler's bare PATH is the exact trigger).

The 2026-08-10 audit (docs/fleet-script-audit-2026-08-10.md) added three more. All three are the
"the verdict was produced and nobody looked" shape, in surfaces the earlier checks did not cover:

  ps-unchecked-call — a PowerShell script invokes ANOTHER script with `&` and never reads
                 $LASTEXITCODE. `$ErrorActionPreference = "Stop"` does NOT trap a called script's
                 non-zero exit (verified on-host), so the caller prints its own success line and
                 exits 0. Live instance: all three notify-owner.ps1 callers — and because the two
                 weekly ones write their interval marker BEFORE delivering, a failed owner card
                 costs a whole interval with no retry and no log line.
  offset-before-write — a cursor/offset that CONSUMES remote state is persisted BEFORE the payload
                 it consumed is durably written. Telegram's getUpdates permanently discards updates
                 below a confirmed offset, so if the payload write then fails (Windows file locking
                 is live on this box — cost-rollup.py carries a retry helper for exactly that) the
                 owner's answers are unrecoverable, while the script exits 0 reporting "APPLIED n".
                 Live instances: read-answers.ps1 and bus-relay.sh's relay leg.
  unchecked-precondition — a script runs a documented LAUNCH PRECONDITION and ignores its exit
                 code, then launches anyway. Live instance: worker-wrapper.ps1 runs
                 trust-workspace.py (whose own comment says an untrusted workspace makes headless
                 `claude -p` hard-block instead of running) without testing it — and is the one
                 fleet script with no PATH-hardening preamble, so the missing-interpreter trigger
                 its siblings already fixed twice applies here in full.

The 2026-08-19 sweep found the silent-staging and dead-gate checks over-firing on the live fleet
(11 of the sweep's 12 findings, hand-verified false positives):

  - keeper-tick.cmd's T-207 fix (2026-08-18) replaced errorlevel testing with asserting each
    mutation's OUTCOME from CAPTURED OUTPUT CONTENT (`findstr`/`for /f` into a flag variable, then
    an `if` on that flag) — a DIFFERENT but equally valid way of reading the same verdict, which
    the check did not recognise because it only looked for errorlevel-shaped tokens in a 1-line
    window. See CONTENT_ASSERTION_READ/CONTENT_ASSERTION_GATE below.
  - janitor-worktrees.ps1's -SelfTest harness `git init --bare`s its OWN throwaway repo under
    $env:TEMP and only ever mutates/pushes to that — never the real bus — so the mutations inside
    it cannot cause the silent data loss this check exists to catch. See
    _selftest_harness_ranges below.
  - preflight-guard.ps1's dead-gate finding was correct in isolation (no shell call site exists)
    but wrong in context: it is invoked by the get-work-done dispatcher SKILL.md, which the CLI
    now includes as a default `--caller` unless the file is missing or `--no-default-caller` is
    passed.

The 2026-08-17 audit (docs/fleet-script-audit-2026-08-17.md) added three more, all reproduced
end-to-end on the host before being written down:

  silent-staging — a git STATE-MUTATING command (`add`/`commit`/`checkout`) whose exit code is
                 never read, in a script that pushes below. silent-push already covers the push
                 itself; these are the commands that BUILD what gets pushed, and pushing an
                 unchanged or wrong ref SUCCEEDS — so the tick's `if errorlevel 1` never fires.
                 Live instances at keeper-tick.cmd:14,29,160,161,162. Reproduced: a concurrent
                 `.git/index.lock` makes `git add -A` exit 128 into its sink and the tick prints
                 healthy while the bus item stays untracked; and a checkout aborted by a dirty
                 tracked file leaves the clone on the sweep's branch, where the tick's commit
                 lands, while `git push origin main` exits 0 — verbatim the stranded-clone
                 incident keeper-tick.cmd:5-6 designates a HARD INVARIANT.
  unmeasured-safe-delete — `git status --porcelain` used as the SAFETY PREDICATE for a
                 `git worktree remove`, where "I could not measure" scores as "measured safe".
                 Two independent legs at janitor-worktrees.ps1:144: it omits `--ignored`, so a
                 worker's gitignored output (build/, .env, *.log) is invisible and is deleted with
                 the worktree; and it never tests the status command's own exit code, so a FAILED
                 status (exit 128 on an unreadable gitdir under a concurrent prune/repair) prints
                 nothing and its EMPTY output reads as clean, deleting a DIRTY worktree.
  unlocked-global-rewrite — a whole-file rewrite of SHARED state with neither an atomic replace
                 nor an inter-process lock. `open(path, "w")` truncates before the first byte, so
                 two of the 16+ concurrent workers interleave into a LOST UPDATE (both exit 0) and
                 any failure mid-dump leaves the file corrupt. Live instances: trust-workspace.py
                 rewriting ~/.claude.json (the GLOBAL config — oauth plus every project's trust and
                 permissions, 113 KB on this host) and cost-rollup.py rewriting the bus-synced
                 costs.jsonl the daily token ceiling gates on. Note cost-rollup.py's
                 `open_with_retry` is NOT a lock: it retries past a sharing violation, which
                 orders nothing.

Exit 0 = clean; 1 = findings (printed to stdout). Read-only; changes nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SHELL_SUFFIXES = {".sh", ".cmd", ".ps1", ".py"}

# The dispatcher SSOT lives in THIS hub repo, outside the fleet dir being scanned — the hub's own
# get-work-done SKILL.md is preflight-guard.ps1's real caller (STEP 6.2). A CLI run against the
# live fleet with no --caller therefore flagged it dead-gate even though it IS wired in (verified
# 2026-08-19: 11 of 12 findings on that sweep were exactly this class of false positive). Auto-
# including it by default — resolved relative to this checker's OWN file, never the fleet root —
# means the common case (a human or the dispatcher itself running the checker) sees the honest
# answer without having to know to pass --caller; --no-default-caller opts back out for isolation
# (the test suite passes its own extra_callers explicitly and does not need this default).
DEFAULT_DISPATCHER_SKILL = (
    Path(__file__).resolve().parent.parent / ".claude" / "skills" / "get-work-done" / "SKILL.md"
)

# Directories that are NOT fleet machinery: per-task worker scratch checkouts, vendored deps, and
# runtime state. Scanning them buries the real findings in third-party noise — a gate nobody reads
# is the same silent failure this checker exists to prevent.
EXCLUDED_DIRS = {
    ".git",
    "workspaces",  # per-task worker checkouts (their own repos have their own CI)
    # Per-task git worktrees of the HUB, created by /get-work-done under the fleet root. Their
    # contents are copies of hub files that the hub's own CI already gates, so scanning them
    # reports the same hub file once per live worktree. Measured 2026-08-17 (T-167): 40 of 48
    # findings — 83% — were worktree copies, INCLUDING this checker and its tests matching their
    # own defect-defining regexes (`_is_pattern_source` only excludes the ONE resolved path it
    # runs from, so every copy defeats it). Burying 8 real fleet findings under 40 duplicates is
    # the same "signal thrown away" failure this gate exists to catch, one level up.
    "worktrees",
    "work",
    "node_modules",
    "venv",
    ".venv",
    "site-packages",
    "evidence",
    "heartbeats",
}

# `x=$(grep -c ...)` with a `|| echo N` fallback, later compared numerically. grep -c prints "0"
# AND exits 1 on no-match, so the fallback appends a second line and the numeric test throws.
GREP_COUNT_FALLBACK = re.compile(
    r"(?P<var>\w+)=\$\(\s*grep\s+-c\b[^)]*\|\|\s*echo\s+\d+\s*\)", re.I
)
NUMERIC_TEST = r'\[\s*"?\$\{{?{var}\b[^]]*?(-lt|-gt|-le|-ge|-eq|-ne)\s'

# An interpreter invocation whose stderr is discarded — absence looks identical to "nothing found".
INTERPRETER_SUPPRESSED = re.compile(
    r"\b(?P<interp>python3|python)\b(?P<rest>[^\n|]*?)2>\s*/dev/null"
)

# Docstring/comment language asserting this file is an enforcing DISPATCH gate. Deliberately
# narrow: it must name dispatch/launch/blocking-a-worker, not merely contain the word "block"
# (which matches unrelated things like a cipher's block-padding docs).
GATE_CLAIM = re.compile(
    r"(called before every (worker )?(launch|dispatch)|structurally impossible|"
    r"exit 0 = (clean to dispatch|ok to dispatch)|non-zero = BLOCK|"
    r"deterministic (pre-)?(dispatch|pre-dispatch) gate|may NOT be dispatched)",
    re.I,
)

# A .cmd line invoking a guard script, redirecting all output to a log.
CMD_GUARD_INVOKE = re.compile(
    r"^(?!\s*rem\b).*?(?P<script>[\w.-]+\.(?:sh|py|ps1))\b[^\n]*?>>?[^\n]*?\.log\b[^\n]*?2>&1",
    re.I,
)
ERRORLEVEL_TEST = re.compile(r"\b(errorlevel|%ERRORLEVEL%)\b", re.I)

# --- shape-only: a `claude -p --output-format json` health guard that never reads the outcome ---
# The guard is recognised by it searching the result file for the `"type":"result"` marker; the
# defect is that neither `is_error` nor `subtype` is examined anywhere in the same file.
RESULT_TYPE_PROBE = re.compile(r'\\?"type\\?"\s*:\s*\\?"result', re.I)
OUTCOME_PROBE = re.compile(r'\bis_error\b|\bsubtype\b|error_max_turns', re.I)
# Only files that actually consume a headless-claude result JSON can carry this defect.
CLAUDE_RESULT_CONSUMER = re.compile(r"--output-format\s+json|\.result\.json|keeper-last\.json", re.I)

# --- silent-push: `git push` whose exit code is thrown away -------------------------------------
# All three spellings discard the verdict: a rejected (non-fast-forward / auth-failed) push is
# indistinguishable from a landed one, which is the data-loss class bus-guard.sh already blocks.
SILENT_PUSH = re.compile(
    r"git\s+push\b(?P<rest>[^\n]*?)(?P<sink>>\s*(nul|/dev/null)\b[^\n]*?2>&1|\|\|\s*true\b)", re.I
)
# Evidence the verdict IS consumed: the safe helper, an explicit exit test, or a conditional.
PUSH_VERDICT_TESTED = re.compile(
    r"\bbus_push\b|\berrorlevel\b|\$\?|\bLASTEXITCODE\b|\bif\s+git\s+push\b|\|\|\s*(?!true\b)\S",
    re.I,
)


# --- stale-receipt: an append-only ledger keyed by a MUTABLE artifact's id -----------------------
# The dedup key is derived from a FILENAME (a task id), but the numbers come from that file's
# CONTENT. Once the id is in the ledger the content is never re-read, so a receipt rewritten after
# its first roll-up (a retry overwriting <task>.result.json) is accounted at the superseded values.
# Recognised by: a "seen" set built from the ledger, and a skip-if-seen guard in the roll-up loop.
SEEN_SET_BUILD = re.compile(r"\b(seen)\b\s*=\s*set\(\)|\bseen\.add\(", re.I)
SEEN_SKIP_GUARD = re.compile(r"\bif\s+\w+\s+in\s+seen\b")
# Evidence the CONTENT is part of the identity: a digest/mtime/size recorded per entry, or an
# explicit supersede/refresh path that rewrites an existing row.
RECEIPT_CONTENT_KEYED = re.compile(
    # Content folded into the IDENTITY: a digest, or an mtime compared against the value the
    # ledger already stored for this task. Deliberately narrow on two counts:
    #   - a `getsize(path) == 0` zero-byte skip is NOT content-identity (cost-rollup.py has one,
    #     and treating it as the fix silently cleared the real finding during development);
    #   - a bare `getmtime(path)` used only to DATE a row (cost-rollup.py does that too) changes
    #     nothing about which content was banked.
    r"\b(sha1|sha256|md5|hashlib|digest|checksum|content_hash|"
    r"supersede|resolve_duplicate|rewrite_entry|update_entry)\b"
    r"|\b(st_mtime|getmtime)\b[^\n]*(==|!=|<|>)[^\n]*\b(seen|ledger|recorded|prev|known)\b"
    r"|\b(seen|ledger|recorded|prev|known)\b[^\n]*(==|!=|<|>)[^\n]*\b(st_mtime|getmtime)\b",
    re.I,
)
# Only a ledger fed by per-task receipt files can carry this defect.
RECEIPT_LEDGER_CONSUMER = re.compile(r"\.result\.json|result\.json['\"]?\s*\)|costs\.jsonl", re.I)

# --- unchecked-read: a registry read whose failure is indistinguishable from "nothing to do" ------
# `x=$(python ...)` / `$(gh ...)` with no `$?` capture, feeding a loop, in a script that exits 0.
UNCHECKED_REGISTRY_READ = re.compile(
    r"^\s*(?P<var>\w+)=\$\(\s*(?P<cmd>python3?|gh|jq)\b(?![^\n]*\|\|)", re.I
)
# The read is GUARDED when its exit code is captured, or the result is emptiness-tested loudly.
READ_VERDICT_TESTED = r"(\b{var}_rc\b|\brc=\$\?|;\s*\w*rc=\$\?|\[\s*-z\s*\"?\$\{{?{var}\b[^]]*\]\s*(&&|\|\|)?[^\n]*(exit|fail|FATAL|>&2))"


# --- ps-unchecked-call: `& script.ps1 ...` whose exit code is never read --------------------------
# PowerShell's call operator on a .ps1/.py/.sh does NOT throw on a non-zero exit, and
# $ErrorActionPreference="Stop" does not change that (it governs error RECORDS, not exit codes).
# Matches `& (Join-Path ...) -Arg` and `& "C:\path\x.ps1"` alike; the invoked name is captured for
# the message. A `$(...)`/`@(...)` capture is excluded — that form consumes the OUTPUT, a different
# (and usually deliberate) shape than fire-and-forget delegation.
# `.\notify-owner.ps1 -Body $b` (no `&`) is the most common PowerShell spelling of this call and has
# identical exit-code semantics, so both the `&` and the dot-slash forms are matched. A leading
# `$x =` capture is excluded by requiring the invocation to START the statement.
PS_AMP_CALL = re.compile(
    r"^\s*(?:&\s*(?P<target>\(\s*Join-Path[^)]*\)|\"[^\"]+\"|'[^']+'|\$\w+|[A-Za-z]:[\\/][^\s|]+)"
    r"|(?P<dotslash>\.[\\/][^\s|]+\.ps1))"
)
# `.exe` deliberately EXCLUDED: invoking an external binary with `&` and not testing $LASTEXITCODE
# is ordinary, ubiquitous PowerShell, not the detect-then-discard class. Only a delegate SCRIPT
# (whose exit code is its verdict) is in scope.
PS_SCRIPT_TARGET = re.compile(r"[\w.-]+\.(ps1|py|sh|cmd)", re.I)
# Evidence the verdict IS consumed anywhere in the file: an explicit exit-code test, a try/catch
# around the invocation, or the caller propagating it.
PS_EXIT_TESTED = re.compile(r"\$LASTEXITCODE|\btry\s*\{|\$\?", re.I)
# A trailing backtick continues a PowerShell statement onto the next line. Real invocations are
# routinely spread over several lines this way (named args each on their own line); the window
# must be measured from where the statement ENDS, not where it begins, or a guard placed right
# after a multi-line call falls outside a window anchored to the first line.
PS_LINE_CONTINUES = re.compile(r"`\s*$")


def _ps_statement_end(lines: list[str], start: int) -> int:
    """Return the 1-based line where the statement beginning at `start` actually ends.

    Two independent PowerShell continuation mechanisms both spread one call across several
    lines: an explicit trailing backtick, and an UNCLOSED parenthesis (a multi-line `-Body
    ("..." + "...")` concatenation continues with no backtick at all until its parens balance —
    the live nginx-drift-check-alert.ps1 CANNOT_CHECK call uses exactly this shape). Naive
    per-line paren counting is not a real PowerShell parser, but it is the same class of
    heuristic PS_AMP_CALL already uses for `Join-Path`, and it is enough to find the statement's
    real last line so the guard-lookahead window is anchored there instead of at the first line.
    """
    depth = 0
    idx = start
    while True:
        line = lines[idx - 1]
        depth += line.count("(") - line.count(")")
        if (depth > 0 or PS_LINE_CONTINUES.search(line)) and idx < len(lines):
            idx += 1
            continue
        return idx

# --- offset-before-write: a consuming cursor persisted before its payload -------------------------
# An offset/cursor whose persistence CONSUMES remote state (Telegram getUpdates discards anything
# below a confirmed offset). Writing it before the payload write makes a failed payload write an
# unrecoverable loss rather than a retry.
OFFSET_WRITE = re.compile(
    r"(Set-Content[^\n]*\$?\w*[Oo]ffset\w*|open\(\s*['\"][^'\"]*\.?tg-offset['\"]\s*,\s*['\"]w)",
    re.I,
)
# The payload whose durability the offset is claiming: the questions/answers file.
PAYLOAD_WRITE = re.compile(
    r"(Set-Content[^\n]*\$?\w*(Questions|Answers)\w*|open\(\s*\w*qf\w*\s*,\s*['\"]w|"
    r"open\(\s*['\"][^'\"]*OWNER-QUESTIONS[^'\"]*['\"]\s*,\s*['\"]w)",
    re.I,
)
# Only a script that actually consumes a Telegram update cursor can carry this defect.
OFFSET_CONSUMER = re.compile(r"getUpdates|tg-offset|update_id", re.I)

# --- unchecked-precondition: a launch precondition whose failure does not stop the launch ---------
# A script that documents a precondition (trust/auth/provision) then runs it with no exit test, and
# goes on to LAUNCH the thing the precondition exists to protect.
# The script may be named by a LITERAL (`python trust-workspace.py`) or, as worker-wrapper.ps1
# does, via a VARIABLE assigned the path just above (`$trustScript = Join-Path ... ;
# python $trustScript`). Matching only literals missed the live instance entirely, so both the
# variable name and its assignment are treated as naming evidence.
# A trailing-letter boundary keeps bare `auth` from matching `authors-list.py`. It must NOT reject
# camelCase, though: the live instance is the VARIABLE `$trustScript`, so a following capital is
# ordinary spelling, not a different word. These regexes compile with re.I, under which `[a-z]`
# also matches uppercase — so a naive `(?![a-z])` silently killed the very finding this check
# exists for. `[a-rt-z]` omits `s`, admitting `trustScript`/`authScript` while still blocking
# `authors`. Verified against all four shapes before landing.
PRECONDITION_WORDS = r"(?:trust|auth|provision|precheck|preflight)(?![a-rt-z])"
# Names that describe REPORTING, not gating — `provision-report.py` is not a precondition.
PRECONDITION_NOT_A_GATE = re.compile(r"report|list|summary|digest", re.I)
# `set -e` already aborts the script when the precondition fails, so the launch below cannot run —
# the failure is loud, not silent. This is the same reasoning that clears bus-relay.sh in the
# audit; the gate must not contradict its own exculpatory logic.
SHELL_ABORTS_ON_ERROR = re.compile(r"^\s*set\s+-[a-z]*e", re.M)
PRECONDITION_INVOKE = re.compile(
    r"^\s*(?:&\s*)?(?:python3?|powershell|bash)\b[^\n]*?(?P<script>"
    rf"[\w.-]*{PRECONDITION_WORDS}[\w.-]*\.(?:py|ps1|sh)"
    rf"|\$\w*{PRECONDITION_WORDS}\w*)",
    re.I,
)
# Evidence the launch it guards actually happens in the same file.
LAUNCH_AFTER = re.compile(r"claude\s+-p\b|ProcessStartInfo|Process\]::Start", re.I)


# --- unlocked-global-rewrite: read-modify-write of SHARED state, truncating, with no lock ---------
# The fleet runs 16+ concurrent claude.exe on one box plus a keeper tick every few minutes, so two
# processes routinely hold the same shared file. `open(path, "w")` TRUNCATES before the first byte
# is written, which makes the whole-file rewrite BOTH lossy and destructive:
#   - lost update: A reads, B reads, B writes, A writes its stale snapshot -> B's change is erased
#     and both processes exit 0, so the fleet records a healthy launch that silently did nothing.
#   - corruption: any failure mid-dump (kill, disk-full, AV lock) leaves the file truncated. The
#     targets here are not scratch files — ~/.claude.json is the GLOBAL Claude Code config (113 KB
#     on this host: oauth account plus every project's trust + permissions) and costs.jsonl is the
#     bus-synced spend ledger the daily token ceiling gates on.
# Both were reproduced deterministically for T-167 (evidence/2026-08-17-T-167/repro_trust_race.py,
# repro_trust_truncate.py). Distinct from stale-receipt (which is about the ledger's dedup KEY);
# this is about the WRITE being non-atomic and unserialised.
#
# Only whole-file REWRITES qualify. An append (`"a"`) cannot lose a prior writer's bytes, and a
# write to a fresh temp path is the FIX being matched below, not the defect.
GLOBAL_REWRITE = re.compile(
    r"\bopen(?:_with_retry)?\s*\(\s*(?P<target>[^,)]+?)\s*,\s*(?P<mode>['\"]w[bt+]?['\"])", re.I
)
# The write must land on state SHARED across processes: the global CC config, or a bus-level
# ledger/registry/queue. A module-level CONSTANT (LEDGER, STATE_PATH) counts — that is exactly how
# cost-rollup.py names it. A local `tmp`/`out`/`dst` variable does not.
SHARED_STATE_TARGET = re.compile(
    r"\.claude\.json|claude_json|costs\.jsonl|"
    r"\b(LEDGER|REGISTRY|QUEUE|SETTINGS|STATE|COSTS|BUS)(_[A-Z]+)*\b",
)
# A temp-then-replace is the CORRECT shape and must never be flagged: the truncation happens on a
# throwaway path and `os.replace` swaps it in atomically, so a concurrent reader sees either the
# old file or the new one, never a half-written one.
ATOMIC_REPLACE = re.compile(r"\bos\.replace\b|\bos\.rename\b|\bshutil\.move\b|\bPath\.replace\b")
# Evidence the writer SERIALISES against other processes: a real lock. `open_with_retry` is NOT a
# lock — it retries past a sharing violation, which orders nothing and is precisely what
# cost-rollup.py already has while still losing updates.
PROCESS_LOCK = re.compile(
    r"\bmsvcrt\.locking\b|\bfcntl\.(flock|lockf)\b|\bportalocker\b|\bfilelock\b|"
    r"\bFileLock\b|\bO_EXCL\b|\bx['\"]\s*\)|\bLockFileEx\b",
    re.I,
)


# --- unmeasured-safe-delete: a destructive op gated on a predicate that cannot see / can fail -----
# The narrowest, highest-stakes shape in the fleet: `git status --porcelain` used as the SAFETY
# PREDICATE for deleting a worktree. Two independent ways it says "safe" without having measured
# anything (both reproduced on this host for T-167 against janitor-worktrees.ps1:144):
#   1. gitignored-blind — `--untracked-files=all` does NOT include ignored paths (`--ignored`
#      does). A worker's build/, dist/, *.log, .env output is invisible, so the veto passes and
#      `git worktree remove` (no --force needed, it shares the blindness) deletes it. Verified:
#      porcelain reported 0 lines with real files present; `--ignored` reported them.
#   2. failure-scores-clean — the capture discards stderr and never reads $LASTEXITCODE, so a
#      FAILED status (exit 128: unreadable gitdir link — a concurrent `worktree prune`/`repair`
#      from another of the 16+ workers, an AV lock, a half-finished move) prints nothing, the
#      emptiness of stdout reads as "clean", and a DIRTY worktree is deleted. Verified: exit 128,
#      0 lines, falls through to REMOVED.
# Deliberately scoped to files that actually DELETE a worktree — this must never fire on ordinary
# `git status` usage, only where emptiness authorises destruction.
DESTRUCTIVE_WORKTREE_OP = re.compile(r"worktree\s+remove\b", re.I)


# --- unmeasured-reset: `reset --hard` gated on an unpushed-commit probe that can itself fail ------
# T-320 HIGH-1 (bus-sync.sh:8-11). The sibling of unmeasured-safe-delete, on git HISTORY rather
# than the working tree, and the existing check cannot see it: there is no `worktree remove` here,
# the destructive verb is `reset --hard`.
#
#   if [ -n "$(git log '@{u}..HEAD' --oneline 2>/dev/null)" ]; then   <- the probe
#     ... rebase (protects unpushed commits)
#   else
#     git pull --rebase ... || { git fetch ... && git reset -q --hard origin/main; }  # "safe"
#
# `git log '@{u}..HEAD'` exits 128 with EMPTY stdout whenever the upstream cannot be resolved (no
# tracking ref after `git branch -M`, a renamed/deleted remote branch, a detached HEAD). Empty
# stdout is then read as "no unpushed commits to lose" and the code takes the branch whose own
# comment calls it safe -- destroying real unpushed commits. Reproduced end-to-end in
# evidence/2026-08-26-T-320/repro-bus-sync-dataloss.sh: the commit is destroyed and the function
# still returns 0, so the fleet records a healthy tick.
UNPUSHED_COMMIT_PROBE = re.compile(
    r"git\b[^\n]*\b(log|rev-list)\b[^\n]*@\{u(pstream)?\}|"
    r"git\b[^\n]*\bcherry\b",
    re.I,
)
# The probe's own failure must be distinguished from "nothing to report" BEFORE its emptiness is
# allowed to authorise a reset: test its exit code, or resolve the upstream first and fail closed.
PROBE_FAILURE_TESTED = re.compile(
    r"\$LASTEXITCODE|\berrorlevel\b|\$\?|"
    r"rev-parse\b[^\n]*@\{u|"
    r"\|\|\s*(return|exit)\b",
    re.I,
)
HISTORY_DESTRUCTIVE_OP = re.compile(r"\breset\b[^\n]*--hard\b", re.I)
# The one honest way to make the probe's emptiness trustworthy without testing it inline: resolve
# the upstream FIRST and bail when it cannot be resolved, so an unresolvable upstream can never
# reach the reset branch. Must appear BEFORE the probe (a later check is too late to matter).
UPSTREAM_RESOLVED_FAIL_CLOSED = re.compile(
    r"rev-parse\b[^\n]*@\{u[^\n]*(\|\||\bexit\b|\breturn\b|-ne\s*0|errorlevel)",
    re.I,
)



# --- silent-staging: a git STATE-MUTATING command whose verdict is discarded, before a push -------
# The existing silent-push check covers `git push`. But the commands that BUILD what gets pushed —
# `git add`, `git commit`, `git checkout` — sit above it in keeper-tick.cmd sending their exit
# codes to `>nul 2>&1`, and a push of an unchanged/wrong ref SUCCEEDS. So the tick's `if errorlevel
# 1` never fires and the bus silently stops receiving work while every tick reports healthy.
# Both live instances were reproduced end-to-end for T-167 (keeper-tick.cmd:160,161,162):
#   * `git add -A` blocked by a concurrent `.git/index.lock` (the sweep at line 129 commits to this
#     same clone — bus history shows a sweep commit and a `keeper: tick` in the same minute) exits
#     128 into the sink; the push then succeeds on the unchanged ref and the tick prints healthy
#     while the bus item stays untracked on disk.
#   * `git checkout main --quiet` aborted by a dirty tracked file (line 158's own comment concedes
#     "the sweep may have switched branches") leaves the clone on the stray branch; the tick's
#     commit lands THERE, `git push origin main` pushes the untouched main ref and exits 0. This
#     is verbatim the stranded-clone incident lines 5-6 designate a HARD INVARIANT.
# Scoped to files that actually push, so the discarded verdict is what makes a healthy report a lie.
# The verdict is lost whether it is redirected into a sink OR simply never tested: `git checkout
# main --quiet` (keeper-tick.cmd:160) has no redirect at all, yet its failure is equally invisible
# because nothing reads errorlevel. So the match is the MUTATION itself; the sink is not required.
GIT_STATE_MUTATION = re.compile(
    r"\bgit\s+(?:-C\s+\S+\s+)?(?P<verb>add|commit|checkout|switch|reset)\b", re.I
)
# A narration line (`echo ... git commit FAILED ...`) can contain the same verb text as a real
# invocation without running one — keeper-tick.cmd:258/272 log exactly this sentence about the
# real mutations at :251/:265, and the bare regex above cannot tell a git command from a git
# WORD inside a logged string. `echo`/`Write-Output`/`Write-Host` never execute anything they
# print, in any of the three shells this check scans, so a line that starts with one of them is
# narration, not a command, regardless of what verb-shaped text it contains.
NARRATION_LINE = re.compile(r"^\s*(echo\b|Write-Output\b|Write-Host\b)", re.I)
GIT_PUSHES_SOMEWHERE = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?push\b", re.I)
# Evidence the mutation's verdict IS consumed: an exit test near it, or an `if git ...` wrapper.
GIT_VERDICT_TESTED = re.compile(
    r"\berrorlevel\b|%ERRORLEVEL%|\$LASTEXITCODE|\$\?|\bif\s+git\b|\|\|\s*(?!true\b)\S|&&", re.I
)
# A retry loop whose push IS tested (`if git push ...; then return 0; fi` inside `for`/`while`)
# consumes the whole iteration's verdict: a failed mutation makes that iteration's push fail, and
# exhaustion returns non-zero loudly. This is bus-sync.sh's bus_push() — the reference-correct shape.
PUSH_RETRY_LOOP = re.compile(
    r"^\s*(for|while)\b[^\n]*\n(?:[^\n]*\n){0,6}?[^\n]*\bif\s+git\s+push\b", re.M | re.I
)

# --- content-assertion guard: T-207's errorlevel-free way of reading the same verdict -------------
# keeper-tick.cmd's own header (this file, not this checker) records SIX failed fixes proving
# errorlevel is unreliable after any call whose output is redirected into a log 12+ concurrent
# fleet processes also write to — so T-207 (2026-08-18) replaced errorlevel testing with asserting
# the mutation's OUTCOME from its CAPTURED OUTPUT CONTENT instead. Two shapes, both observed live:
#   (a) the mutation's own captured output is grepped for an error marker (`findstr /c:"fatal"`),
#   (b) a follow-up state-query command (`git rev-parse --abbrev-ref HEAD` after `git checkout`) is
#       captured and compared against the expected value.
# Either way the read feeds a flag variable, and that flag is GATED by a plain `if "<flag>"=="..."`
# — functionally identical to `if errorlevel 1`, just spelled in content instead of exit code. A
# mutation whose output is genuinely discarded to nul/dev-null can never have this shape (nobody
# could read what was thrown away), so that case is untouched and still requires the errorlevel
# shape above.
MUTATION_OUTPUT_DISCARDED = re.compile(r">\s*(nul|/dev/null)\b", re.I)
CONTENT_ASSERTION_READ = re.compile(r"\bfindstr\b|\bfor\s*/f\b", re.I)
CONTENT_ASSERTION_GATE = re.compile(r'if\s+(not\s+)?"?!?%?\w+%?!?"?\s*==\s*"', re.I)

STATUS_PREDICATE = re.compile(r"git\b[^\n]*\bstatus\b[^\n]*--porcelain", re.I)
STATUS_SEES_IGNORED = re.compile(r"--ignored\b", re.I)
# Evidence the capture's own failure is distinguished from "nothing to report": the exit code is
# read, or stderr is kept and inspected. `2>$null` + no $LASTEXITCODE is the defect.
STATUS_FAILURE_TESTED = re.compile(r"\$LASTEXITCODE|\berrorlevel\b|\$\?", re.I)


# --- self-test/fixture harness exclusion -----------------------------------------------------------
# janitor-worktrees.ps1's -SelfTest function `git init --bare`s its OWN throwaway repo under
# $env:TEMP, then mutates and pushes ONLY inside that scope — it never touches the real bus or any
# registered fleet repo, so none of the "reports healthy while real work is lost" checks can apply
# to it: there is no real work in scope to lose. Deliberately narrower than "skip anything named
# *test*" (which would blind the gate to a genuine defect a dev merely labelled a test): a function
# only qualifies when it BOTH (a) is named as a self-test/fixture harness AND (b) itself originates
# a bare repo under a temp path before mutating. Production fleet code has no reason to `git init
# --bare` a fresh throwaway remote moments before "pushing" to it — doing so cannot reach the real
# shared bus this checker exists to protect, so a script cannot game this exclusion by merely
# naming a real-work function SelfTest without also making that real work provably unreachable.
SELFTEST_FUNCTION = re.compile(r"^\s*function\s+[\w-]*(?:SelfTest|Self-Test)[\w-]*\b", re.I)
TEMP_REPO_INIT = re.compile(
    r"git\s+init\b[^\n]*(\$env:TEMP|\$tmp\w*|TemporaryDirectory|tempfile|mktemp)|"
    r"\$\w*[Tt]emp\w*\s*=\s*(Join-Path\s+\$env:TEMP|New-TemporaryFile|mktemp)",
    re.I,
)


def _selftest_harness_ranges(lines: list[str]) -> list[tuple[int, int]]:
    """1-based inclusive (start, end) line ranges of self-test functions that own a throwaway repo.

    A function only counts once BOTH its name matches the self-test/fixture convention and its body
    contains a `git init` targeting a temp-derived path — see SELFTEST_FUNCTION/TEMP_REPO_INIT.
    """
    ranges: list[tuple[int, int]] = []
    for i, line in enumerate(lines, start=1):
        if not SELFTEST_FUNCTION.search(line):
            continue
        depth = 0
        started = False
        end = i
        for j in range(i, len(lines) + 1):
            text = lines[j - 1]
            depth += text.count("{") - text.count("}")
            if "{" in text:
                started = True
            end = j
            if started and depth <= 0:
                break
        if TEMP_REPO_INIT.search("\n".join(lines[i - 1 : end])):
            ranges.append((i, end))
    return ranges


def _in_ranges(line: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= line <= end for start, end in ranges)


@dataclass(frozen=True)
class Finding:
    check: str
    path: Path
    line: int
    message: str

    def render(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        return f"{rel}:{self.line}: [{self.check}] {self.message}"


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _is_pattern_source(path: Path) -> bool:
    """True for THIS checker and its tests — files whose 'code' is defect patterns, not behaviour.

    Pointed at its own tree, a checker matching source text will match the regexes that DEFINE the
    defect and the fixtures that PLANT it, reporting the gate itself as defective. That noise is
    the failure mode this gate exists to prevent, so exclude the two files by identity (not by a
    generic "skip tests" rule, which would blind the gate to real defects in other test helpers).
    """
    here = Path(__file__).resolve()
    # The test file drops the `check_` prefix (test_fleet_script_health.py), so derive both
    # spellings rather than guessing one — an exclusion that silently misses its target is the
    # same "looks handled, isn't" shape this whole gate hunts.
    stems = {here.stem, here.stem.removeprefix("check_")}
    # Match by FILENAME, not resolved path. Identity-by-path only excused the single copy this
    # process happens to run from, so every per-task worktree/checkout of the hub carried a
    # second copy that flagged itself (T-167: `check_fleet_script_health.py` and
    # `test_fleet_script_health.py` reported as offset-before-write from six worktrees at once).
    # These two filenames are pattern SOURCE wherever they live — their "code" is the defect
    # regexes and the fixtures that plant them, never fleet behaviour.
    return path.name in {here.name} | {f"test_{s}.py" for s in stems}


def check_grep_count_fallback(path: Path) -> list[Finding]:
    """`x=$(grep -c ... || echo 0)` + a later numeric test on x = inverted branch."""
    if path.suffix != ".sh":
        return []
    out: list[Finding] = []
    lines = _lines(path)
    for i, line in enumerate(lines, start=1):
        m = GREP_COUNT_FALLBACK.search(line)
        if not m:
            continue
        var = re.escape(m.group("var"))
        window = "\n".join(lines[i - 1 : i + 6])
        if re.search(NUMERIC_TEST.format(var=var), window):
            out.append(
                Finding(
                    "grep-count",
                    path,
                    i,
                    f"`${m.group('var')}` from `grep -c ... || echo N` is TWO lines on no-match; "
                    "the numeric test below throws and takes the wrong branch. "
                    "Use `grep -c ... || true` then strip, or `grep -q`.",
                )
            )
    return out


def check_interpreter_suppressed(path: Path) -> list[Finding]:
    """An interpreter that may be absent, with stderr discarded, looks like a clean result."""
    if path.suffix != ".sh":
        return []
    out: list[Finding] = []
    for i, line in enumerate(_lines(path), start=1):
        if line.lstrip().startswith("#"):
            continue
        m = INTERPRETER_SUPPRESSED.search(line)
        if not m:
            continue
        out.append(
            Finding(
                "interpreter",
                path,
                i,
                f"`{m.group('interp')}` invoked with stderr suppressed — if the interpreter is "
                "absent the failure is indistinguishable from an empty/clean result. Resolve the "
                "interpreter once up front and abort loudly if missing.",
            )
        )
    return out


def check_dead_gate(
    path: Path, corpus: list[Path], extra_callers: list[Path] | None = None
) -> list[Finding]:
    """A file claiming to be an enforcing gate must actually be invoked somewhere.

    `extra_callers` lets a caller outside the fleet dir count as wiring — the dispatcher SSOT
    (the hub's get-work-done SKILL.md) legitimately invokes preflight-guard.ps1 from there.
    """
    if path.suffix not in {".py", ".ps1", ".sh"}:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    head = "\n".join(text.splitlines()[:40])
    if not GATE_CLAIM.search(head):
        return []
    name = path.name
    stem = path.stem
    for other in list(corpus) + list(extra_callers or []):
        if not other.is_file() or other.resolve() == path.resolve():
            continue
        body = other.read_text(encoding="utf-8", errors="replace")
        for line in body.splitlines():
            if line.lstrip().startswith(("#", "rem ", "REM ")):
                continue
            if name in line or (stem in line and other.suffix in {".cmd", ".sh", ".ps1"}):
                return []
    return [
        Finding(
            "dead-gate",
            path,
            1,
            f"{name} declares itself an enforcing gate but has no call site in the fleet — "
            "the enforcement is prose. Wire it into the dispatch path or drop the claim.",
        )
    ]


def check_discarded_exit(path: Path) -> list[Finding]:
    """A .cmd that runs a guard, logs its output, and never tests errorlevel discards the verdict."""
    if path.suffix != ".cmd":
        return []
    out: list[Finding] = []
    lines = _lines(path)
    for i, line in enumerate(lines, start=1):
        m = CMD_GUARD_INVOKE.search(line)
        if not m:
            continue
        window = "\n".join(lines[i : i + 3])
        if ERRORLEVEL_TEST.search(window):
            continue
        out.append(
            Finding(
                "discarded",
                path,
                i,
                f"`{m.group('script')}` exit code is the gate verdict, but output is redirected to "
                "a log and errorlevel is never tested — a real finding is silently ignored.",
            )
        )
    return out


def check_shape_only_result_guard(path: Path) -> list[Finding]:
    """A result-JSON health guard that checks SHAPE but never OUTCOME passes failed runs as healthy."""
    if path.suffix not in {".cmd", ".sh", ".ps1"}:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    if not CLAUDE_RESULT_CONSUMER.search(text):
        return []
    lines = _lines(path)
    # The outcome must be read by CODE. A `rem`/`#` line narrating a past bug (keeper-tick.cmd
    # explains a 2026-07-24 is_error fix in a comment) must never clear a live finding — that is
    # the same "prose counted as enforcement" mistake the dead-gate check exists to prevent.
    code = "\n".join(l for l in lines if not l.lstrip().startswith(("#", "rem ", "REM ")))
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("#", "rem ", "REM ")):
            continue
        if not RESULT_TYPE_PROBE.search(line):
            continue
        # The outcome must be read SOMEWHERE in this file's CODE — not necessarily the same line.
        if OUTCOME_PROBE.search(code):
            return []
        out.append(
            Finding(
                "shape-only",
                path,
                i,
                "the result-JSON guard asserts SHAPE (`\"type\":\"result\"`) but never reads the "
                "OUTCOME (`is_error` / `subtype`) — a run that ends in `error_max_turns` emits both "
                "shape markers and is recorded as a healthy tick. Also assert is_error is false.",
            )
        )
        break
    return out


def check_silent_push(path: Path) -> list[Finding]:
    """`git push` with its exit code discarded — a rejected push looks exactly like a landed one."""
    if path.suffix not in {".cmd", ".sh", ".ps1"}:
        return []
    out: list[Finding] = []
    lines = _lines(path)
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("#", "rem ", "REM ")):
            continue
        m = SILENT_PUSH.search(line)
        if not m:
            continue
        # A verdict test on the same line or the two after it clears the finding.
        window = "\n".join(lines[i - 1 : i + 3])
        if PUSH_VERDICT_TESTED.search(window):
            continue
        out.append(
            Finding(
                "silent-push",
                path,
                i,
                f"`git push` sends its verdict to `{m.group('sink').strip()}` and nothing tests it — "
                "a rejected/auth-failed push is indistinguishable from a landed one (the bus "
                "data-loss class). Use bus_push, or test the exit code and log loudly on failure.",
            )
        )
    return out


def check_stale_receipt_ledger(path: Path) -> list[Finding]:
    """An id-keyed ledger over MUTABLE receipts freezes at whatever content it saw first.

    The idempotency key ("task already in the ledger") is derived from the FILENAME, but every
    recorded number is read from that file's CONTENT. A receipt that is rewritten after its first
    roll-up — the fleet overwrites `<task>.result.json` when a task is retried — is therefore
    accounted forever at the SUPERSEDED values, and nothing ever re-reconciles it. The spend the
    daily ceiling gates on is silently wrong, which is the un-gated budget class.
    """
    if path.suffix != ".py":
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    if not RECEIPT_LEDGER_CONSUMER.search(text) or not SEEN_SET_BUILD.search(text):
        return []
    lines = _lines(path)
    code = "\n".join(l for l in lines if not l.lstrip().startswith("#"))
    # Content-derived identity (a digest, an mtime comparison, an explicit supersede path) means
    # a rewritten receipt is detectable — that is the fix, so it clears the finding.
    if RECEIPT_CONTENT_KEYED.search(code):
        return []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith("#"):
            continue
        if not SEEN_SKIP_GUARD.search(line):
            continue
        return [
            Finding(
                "stale-receipt",
                path,
                i,
                "the ledger dedups on a task id parsed from a MUTABLE receipt file, but never on "
                "that file's CONTENT — a receipt rewritten after its first roll-up (a retry "
                "overwriting <task>.result.json) is accounted forever at the superseded numbers "
                "and the daily ceiling gates on the under-count. Key on a content digest/mtime, "
                "or re-reconcile a changed receipt.",
            )
        ]
    return []


def check_unchecked_registry_read(path: Path) -> list[Finding]:
    """A registry read whose failure yields an empty loop and a clean exit 0.

    `repos=$(python -c ...)` with the exit code never captured: when the interpreter is missing
    (Task Scheduler's bare PATH — the fleet's own recurring trigger) the variable is empty, the
    `while read` body never runs, and the script exits 0. "Read zero repos" then renders exactly
    like "no repos needed work", which is the silent-failure shape this gate exists to prevent.
    """
    if path.suffix != ".sh":
        return []
    lines = _lines(path)
    text = "\n".join(lines)
    # Only fires for a read that actually FEEDS a loop — a bare assignment used inline is not
    # the "iterated over nothing and called it clean" shape.
    if not re.search(r"(while\s+(IFS=[^\s]*\s+)?read\b|\bfor\s+\w+\s+in\b)", text):
        return []
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith("#"):
            continue
        m = UNCHECKED_REGISTRY_READ.match(line)
        if not m:
            continue
        var = re.escape(m.group("var"))
        # A verdict test anywhere in the file clears it (the rc may be checked below the loop).
        if re.search(READ_VERDICT_TESTED.format(var=var), text, re.I):
            continue
        # The read must actually drive a loop for the empty result to masquerade as "nothing to do".
        if not re.search(rf"<<<\s*\"?\${{?{var}\b|\$\{{?{var}\b[^\n]*\|\s*while", text):
            continue
        out.append(
            Finding(
                "unchecked-read",
                path,
                i,
                f"`{m.group('cmd')}` registry read into `${m.group('var')}` never captures its exit "
                "code; on failure (missing interpreter / auth expiry) the variable is empty, the "
                "loop below iterates ZERO times and the script still exits 0 — 'read nothing' is "
                "indistinguishable from 'nothing to do'. Capture the rc and fail loudly on an "
                "empty registry.",
            )
        )
    return out


def check_ps_unchecked_call(path: Path) -> list[Finding]:
    """A PowerShell `& other-script.ps1` whose non-zero exit nobody reads.

    `$ErrorActionPreference = "Stop"` does NOT trap a called script's exit code — it governs
    PowerShell error records. So the caller sails past a failed delegate, prints its own success
    line and exits 0, and the keeper's `if errorlevel 1` never fires. When the caller has already
    advanced a self-gating interval marker (the fleet's weekly sweeps do), the failure additionally
    costs the whole interval: no retry, no log line, no card.
    """
    if path.suffix != ".ps1":
        return []
    lines = _lines(path)
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith("#"):
            continue
        m = PS_AMP_CALL.match(line)
        if not m:
            continue
        # It must be a SCRIPT invocation; `& $someScriptBlock` is a different construct. Match ONLY
        # the callee target — a whole-line fallback matched a script name appearing in an ARGUMENT
        # (`& $block -Config "notify-owner.ps1"`), flagging a call that never ran a delegate.
        target = m.group("target") or m.group("dotslash") or ""
        named = PS_SCRIPT_TARGET.search(target)
        if not named:
            continue
        # The verdict test must be NEAR the invocation. A whole-file search let an unrelated
        # try/catch elsewhere in the script (feature-adoption-sweep.ps1 wraps its Push-Location
        # 30 lines above) excuse a genuinely unchecked delivery call — the same "prose counted as
        # enforcement" mistake the dead-gate and shape-only checks each had to be narrowed against.
        # The call itself may be continued over several lines (backtick-continued named args, or
        # an unclosed-paren concatenation like `-Body ("..." + "...")`); measure the forward edge
        # of the window from the statement's LAST line, not its first, or a guard placed right
        # after a multi-line call falls outside a window anchored to where the call began.
        end = _ps_statement_end(lines, i)
        window = "\n".join(lines[max(0, i - 3) : end + 3])
        if PS_EXIT_TESTED.search(window):
            continue
        out.append(
            Finding(
                "ps-unchecked-call",
                path,
                i,
                f"`{named.group(0)}` is invoked with `&` and its exit code is never read "
                "($LASTEXITCODE / try-catch). $ErrorActionPreference='Stop' does NOT trap a called "
                "script's non-zero exit, so this caller reports success for a delegate that "
                "failed — and any interval marker written above is burned with no retry. Test "
                "$LASTEXITCODE and fail loudly (and write the marker only after delivery succeeds).",
            )
        )
    return out


def check_offset_before_write(path: Path) -> list[Finding]:
    """A consuming cursor persisted BEFORE the payload it consumed is durably written.

    Telegram's getUpdates permanently discards updates below a confirmed offset, so the offset
    write is a COMMIT POINT. Persisting it first turns any failure of the payload write (Windows
    file locking is live on this box) into unrecoverable loss of the owner's answers, while the
    script still exits 0 reporting how many it "applied".
    """
    if path.suffix not in {".ps1", ".sh", ".py"}:
        return []
    if _is_pattern_source(path):
        return []
    lines = _lines(path)
    text = "\n".join(lines)
    if not OFFSET_CONSUMER.search(text):
        return []
    offset_line = payload_line = None
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("#", "rem ", "REM ")):
            continue
        if offset_line is None and OFFSET_WRITE.search(line):
            offset_line = i
        if payload_line is None and PAYLOAD_WRITE.search(line):
            payload_line = i
    # Only an ORDERING defect: both writes must exist, with the offset committing first.
    if offset_line is None or payload_line is None or offset_line >= payload_line:
        return []
    return [
        Finding(
            "offset-before-write",
            path,
            offset_line,
            f"the update cursor is persisted at line {offset_line}, BEFORE the payload it consumed "
            f"is written at line {payload_line}. The offset is a commit point — getUpdates never "
            "returns a consumed update again — so a failed payload write loses the owner's answers "
            "permanently while the script exits 0. Write the payload first, advance the offset only "
            "after that write is confirmed.",
        )
    ]


def check_unchecked_precondition(path: Path) -> list[Finding]:
    """A documented launch precondition runs, fails, and the launch proceeds anyway.

    Distinct from ps-unchecked-call: this fires regardless of language whenever a trust/auth/
    provision step guards a launch that happens in the SAME file. If the precondition cannot fail
    the launch, it is not a precondition — it is a hopeful side effect.
    """
    if path.suffix not in {".ps1", ".sh", ".cmd"}:
        return []
    lines = _lines(path)
    text = "\n".join(lines)
    if not LAUNCH_AFTER.search(text):
        return []
    if path.suffix == ".sh" and SHELL_ABORTS_ON_ERROR.search(text):
        return []
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("#", "rem ", "REM ")):
            continue
        m = PRECONDITION_INVOKE.match(line)
        if not m:
            continue
        # A report/list/digest helper is named like a precondition but gates nothing.
        if PRECONDITION_NOT_A_GATE.search(m.group("script")):
            continue
        # A verdict test in the following 3 lines (or an `if`/`try` wrapping it) clears it.
        window = "\n".join(lines[i - 1 : i + 3])
        if re.search(r"\$LASTEXITCODE|errorlevel|\$\?|\btry\s*\{|\|\|", window, re.I):
            continue
        out.append(
            Finding(
                "unchecked-precondition",
                path,
                i,
                f"`{m.group('script')}` is a LAUNCH PRECONDITION but its exit code is discarded, and "
                "the launch below proceeds regardless — a failed precondition (missing interpreter "
                "on Task Scheduler's bare PATH, unset env var, locked state file) is "
                "indistinguishable from a satisfied one, and the worker then burns its dispatch on "
                "the wall the precondition existed to remove. Test the exit code and abort the "
                "launch on failure.",
            )
        )
    return out


def check_unlocked_global_rewrite(path: Path) -> list[Finding]:
    """A whole-file rewrite of SHARED state, truncating, with neither a lock nor an atomic replace.

    `open(shared, "w")` truncates before writing a byte, so two concurrent fleet processes produce
    a LOST UPDATE (the later writer's stale snapshot erases the earlier one's change, both exit 0)
    and any failure mid-dump leaves the file CORRUPT. Unlike stale-receipt — which is about the
    dedup KEY being wrong — this is about the write itself being neither serialised nor atomic.

    The fix is temp-file + `os.replace` (atomic swap) and, where two writers can genuinely
    interleave, a real inter-process lock. A retry-on-sharing-violation helper is NOT a lock: it
    orders nothing, and cost-rollup.py already has one while still losing updates.
    """
    if path.suffix != ".py":
        return []
    if _is_pattern_source(path):
        return []
    lines = _lines(path)
    code = "\n".join(l for l in lines if not l.lstrip().startswith("#"))
    # A correct writer anywhere in the file clears it: these scripts have ONE shared-state writer,
    # so an atomic replace or a real lock present means the shape has been fixed.
    if ATOMIC_REPLACE.search(code) or PROCESS_LOCK.search(code):
        return []
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith("#"):
            continue
        m = GLOBAL_REWRITE.search(line)
        if not m:
            continue
        if not SHARED_STATE_TARGET.search(m.group("target")):
            continue
        out.append(
            Finding(
                "unlocked-global-rewrite",
                path,
                i,
                f"`{m.group('target').strip()}` is SHARED fleet/global state rewritten with mode "
                f"{m.group('mode')} — the open TRUNCATES it, and there is no atomic replace and no "
                "inter-process lock. With 16+ concurrent workers on this box, an interleaved "
                "read-modify-write silently ERASES the other writer's change (both exit 0, so the "
                "fleet records a healthy run), and a failure mid-write leaves the file corrupt. "
                "Write a temp file and os.replace() it in; add a real lock if writers interleave.",
            )
        )
    return out


def check_silent_staging(path: Path) -> list[Finding]:
    """A git state-mutating command whose verdict nobody reads, in a script that then pushes.

    `git push` already has its own check. This one covers the commands that BUILD what gets
    pushed — a failed `add`/`commit`/`checkout` leaves the push with nothing (or the wrong ref) to
    send, and pushing an unchanged ref SUCCEEDS. So the tick's `if errorlevel 1` never fires: the
    bus silently stops receiving work while every tick reports healthy.
    """
    if path.suffix not in {".cmd", ".sh", ".ps1"}:
        return []
    lines = _lines(path)
    text = "\n".join(lines)
    if not GIT_PUSHES_SOMEWHERE.search(text):
        return []
    # `set -e` aborts the script on the failed mutation, so the push below never runs — loud.
    if path.suffix == ".sh" and SHELL_ABORTS_ON_ERROR.search(text):
        return []
    selftest_ranges = _selftest_harness_ranges(lines) if path.suffix == ".ps1" else []
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("#", "rem ", "REM ")) or NARRATION_LINE.match(line):
            continue
        m = GIT_STATE_MUTATION.search(line)
        if not m:
            continue
        # A mutation inside a throwaway self-test harness (its own `git init --bare` repo under
        # $env:TEMP) never touches the real bus — see _selftest_harness_ranges.
        if _in_ranges(i, selftest_ranges):
            continue
        # The verdict test must be on THIS line or the very next one. A wider window let an
        # `if errorlevel 1` belonging to an unrelated command five lines below excuse an unchecked
        # `git checkout` (keeper-tick.cmd:14 was cleared that way during development) — the same
        # "someone else's enforcement counted as mine" trap the dead-gate and ps-unchecked-call
        # checks each had to be narrowed against. errorlevel reflects the LAST command, so a test
        # after any intervening command is not this mutation's verdict.
        window = "\n".join(lines[i - 1 : i + 1])
        if GIT_VERDICT_TESTED.search(window):
            continue
        # T-207's content-assertion shape (no errorlevel token anywhere): the mutation's output
        # must be CAPTURED (not discarded to nul/dev-null) — nobody can read what was thrown away —
        # then a findstr/for-f READ of that capture, followed within a few lines by an `if` GATE on
        # the resulting flag, is the same verdict-testing this check already accepts, just spelled
        # in content instead of exit code. Both windows are kept tight (10 lines mutation->read, 5
        # read->gate — the widest observed real gap is 7 and 4 respectively) so an unrelated
        # findstr/if pair elsewhere in the file cannot falsely clear a genuinely unguarded mutation.
        if not MUTATION_OUTPUT_DISCARDED.search(line):
            read_at = None
            for j in range(i, min(i + 10, len(lines))):
                candidate = lines[j]
                if candidate.lstrip().startswith(("#", "rem ", "REM ")):
                    continue
                if CONTENT_ASSERTION_READ.search(candidate):
                    read_at = j
                    break
            if read_at is not None:
                gate_lines = [
                    l
                    for l in lines[read_at : min(read_at + 5, len(lines))]
                    if not l.lstrip().startswith(("#", "rem ", "REM "))
                ]
                gate_window = "\n".join(gate_lines)
                if CONTENT_ASSERTION_GATE.search(gate_window):
                    continue
        # A mutation inside a RETRY LOOP whose push is tested is already safe: if the mutation
        # fails, the guarded push in the same iteration fails too and the loop exhausts loudly.
        # bus_push() in bus-sync.sh is the fleet's reference-correct implementation and must never
        # flag — a gate that fires on the known-good shape is one readers learn to ignore.
        if PUSH_RETRY_LOOP.search("\n".join(lines[max(0, i - 4) : i + 4])):
            continue
        out.append(
            Finding(
                "silent-staging",
                path,
                i,
                f"`git {m.group('verb')}` mutates git state here and its exit code is never tested, "
                "in a script that pushes below. A failed add/commit (a concurrent .git/index.lock) "
                "leaves the work uncommitted, and a failed checkout leaves the clone on the wrong "
                "branch — either way the following `git push` SUCCEEDS on an unchanged or wrong "
                "ref, so the run reports healthy while the bus never received the work. Test the "
                "exit code and abort loudly before pushing.",
            )
        )
    return out


def check_unmeasured_safe_delete(path: Path) -> list[Finding]:
    """A worktree deletion gated on a `git status` predicate that can't see, or can silently fail.

    Fires only in a file that actually removes a worktree, so the emptiness of `git status` output
    is literally the authorisation to destroy someone's work. Two defects, same root cause —
    "I could not measure" scoring as "measured safe":

      * the predicate omits `--ignored`, so every gitignored worker artifact (build/, .env, *.log)
        is invisible and the veto passes over real uncommitted work;
      * the predicate's own exit code is never tested, so a FAILED status (unreadable gitdir under
        a concurrent prune/repair, an AV lock) yields empty stdout that reads as "clean".
    """
    if path.suffix not in {".ps1", ".sh", ".cmd"}:
        return []
    lines = _lines(path)
    text = "\n".join(lines)
    if not DESTRUCTIVE_WORKTREE_OP.search(text):
        return []
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("#", "rem ", "REM ")):
            continue
        if not STATUS_PREDICATE.search(line):
            continue
        problems = []
        if not STATUS_SEES_IGNORED.search(line):
            problems.append(
                "omits `--ignored`, so gitignored worker output (build/, dist/, .env, *.log) is "
                "invisible to the veto and is deleted with it"
            )
        # The exit code must be tested at the capture, not somewhere far below.
        window = "\n".join(lines[i - 1 : i + 3])
        if not STATUS_FAILURE_TESTED.search(window):
            problems.append(
                "never tests the status command's own exit code, so a FAILED status (exit 128 on "
                "an unreadable gitdir — a concurrent worktree prune/repair, an AV lock) prints "
                "nothing and its EMPTY output is read as 'clean'"
            )
        if not problems:
            continue
        out.append(
            Finding(
                "unmeasured-safe-delete",
                path,
                i,
                "this `git status --porcelain` is the SAFETY PREDICATE for a `git worktree remove` "
                "in the same file, but it " + "; and it ".join(problems) + ". Unmeasured is being "
                "treated as safe: add `--ignored` and test the exit code, and treat any failure to "
                "measure as DIRTY (refuse to delete), never as clean.",
            )
        )
    return out




def check_unmeasured_reset(path: Path) -> list[Finding]:
    """A `reset --hard` authorised by an unpushed-commit probe whose OWN failure reads as "none".

    T-320 HIGH-1, live in bus-sync.sh's `bus_pull`. The unmeasured-safe-delete sibling, one level
    up: there the emptiness of `git status` authorised deleting a working tree; here the emptiness
    of `git log '@{u}..HEAD'` authorises discarding COMMITTED history.

    `git log '@{u}..HEAD'` exits 128 and prints NOTHING when the upstream cannot be resolved -- a
    branch with no tracking ref (routine after `git branch -M main`), a deleted/renamed remote
    branch, a detached HEAD. With stderr sent to /dev/null and the exit code untested, that empty
    stdout is indistinguishable from the genuine "zero unpushed commits" answer, so the code takes
    the branch it documents as `safe: no unpushed commits to lose` and hard-resets over real work.

    The failure is doubly silent: the destroyed commit is only in the reflog, and the function
    RETURNS 0, so the caller records a healthy tick. Fail closed instead -- a probe that could not
    measure must be treated as "unpushed commits present" (refuse to reset), never as "none".
    """
    if path.suffix not in {".sh", ".ps1", ".cmd"}:
        return []
    if _is_pattern_source(path):
        return []
    lines = _lines(path)
    text = "\n".join(lines)
    # Only where a hard reset actually exists: elsewhere the probe's emptiness authorises nothing.
    if not HISTORY_DESTRUCTIVE_OP.search(text):
        return []
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("#", "rem ", "REM ")):
            continue
        if not UNPUSHED_COMMIT_PROBE.search(line):
            continue
        # Two ways the emptiness can be made trustworthy, and only two:
        #   (a) the probe line tests its OWN exit code, or
        #   (b) the upstream was resolved fail-closed BEFORE the probe, so an unresolvable
        #       upstream can never reach the reset branch at all.
        # A test on a FOLLOWING line does not count: it guards that line, not the probe. In the
        # live bus-sync.sh the `|| { ...; return 2; }` one line below belongs to the rebase, so a
        # symmetric window would read the shipped defect as handled.
        if PROBE_FAILURE_TESTED.search(line):
            continue
        preceding = "\n".join(lines[max(0, i - 6) : i - 1])
        if UPSTREAM_RESOLVED_FAIL_CLOSED.search(preceding):
            continue
        out.append(
            Finding(
                "unmeasured-reset",
                path,
                i,
                "this unpushed-commit probe is the SAFETY PREDICATE for a `reset --hard` in the "
                "same file, but its own exit code is never tested: `git log '@{u}..HEAD'` exits "
                "128 with EMPTY output when the upstream cannot be resolved (no tracking ref, a "
                "renamed/deleted remote branch, detached HEAD), and that emptiness is then read as "
                "'no unpushed commits to lose' -- hard-resetting over real committed work while "
                "returning success. Fail closed: treat a probe that could not measure as UNPUSHED "
                "COMMITS PRESENT and refuse to reset.",
            )
        )
    return out



def collect(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix in SHELL_SUFFIXES
        and not EXCLUDED_DIRS.intersection(p.parts)
    )


def manifest_digest(root: Path) -> tuple[str, int]:
    """sha256 over every scanned script's (relative path, content sha256), sorted, plus the count.

    This is the "zero floor" evidence primitive (T-212): producing a matching digest requires
    reading the ACTUAL bytes of every file `collect()` would scan on THIS host, in the same order
    the checker itself uses. A comment claiming "all fixed" costs nothing to write; a matching
    manifest_sha256 costs an actual run against the actual fleet checkout — nobody can hand-type a
    sha256 that happens to match dozens of real files' real content. The next run on a host that
    DOES have the fleet (scripts/tests/test_fleet_script_health.py's
    test_zero_floor_evidence_matches_live_fleet) recomputes this and fails loudly on any mismatch,
    whether the mismatch is honest drift or a fabricated digest.
    """
    corpus = collect(root)
    parts = [f"{p.relative_to(root).as_posix()}:{hashlib.sha256(p.read_bytes()).hexdigest()}" for p in corpus]
    manifest = "\n".join(sorted(parts))
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest(), len(corpus)


def run(root: Path, extra_callers: list[Path] | None = None) -> list[Finding]:
    corpus = collect(root)
    findings: list[Finding] = []
    for path in corpus:
        findings.extend(check_grep_count_fallback(path))
        findings.extend(check_interpreter_suppressed(path))
        findings.extend(check_discarded_exit(path))
        findings.extend(check_shape_only_result_guard(path))
        findings.extend(check_silent_push(path))
        findings.extend(check_stale_receipt_ledger(path))
        findings.extend(check_unchecked_registry_read(path))
        findings.extend(check_ps_unchecked_call(path))
        findings.extend(check_offset_before_write(path))
        findings.extend(check_unchecked_precondition(path))
        findings.extend(check_unlocked_global_rewrite(path))
        findings.extend(check_silent_staging(path))
        findings.extend(check_unmeasured_safe_delete(path))
        findings.extend(check_unmeasured_reset(path))
        findings.extend(check_dead_gate(path, corpus, extra_callers))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", help="fleet script directory (or a single script) to check")
    ap.add_argument(
        "--caller",
        action="append",
        default=[],
        metavar="FILE",
        help="extra file that may invoke a gate (e.g. the dispatcher SKILL.md); repeatable",
    )
    ap.add_argument(
        "--no-default-caller",
        action="store_true",
        help="do not auto-include this hub's get-work-done SKILL.md as a dead-gate caller",
    )
    ap.add_argument(
        "--print-zero-evidence",
        action="store_true",
        help=(
            "when the sweep is clean, print a ready-to-paste zero_evidence JSON block for "
            "scripts/tests/fleet-ratchet-floor.json's findings:[] state (refuses if not clean)"
        ),
    )
    args = ap.parse_args()
    root = Path(args.path)
    if not root.exists():
        sys.stderr.write(f"fleet-health: path not found: {root}\n")
        return 2
    extra_callers = [Path(c) for c in args.caller]
    if not args.no_default_caller and DEFAULT_DISPATCHER_SKILL.is_file():
        extra_callers.append(DEFAULT_DISPATCHER_SKILL)
    findings = run(root, extra_callers)
    for f in sorted(findings, key=lambda f: (str(f.path), f.line)):
        print(f.render(root if root.is_dir() else root.parent))
    if findings:
        print(f"\nfleet-health: {len(findings)} finding(s) — silent-failure class present")
        return 1
    print("fleet-health: clean")
    if args.print_zero_evidence:
        digest, count = manifest_digest(root)
        caller_args = " ".join(f'--caller "{c}"' for c in args.caller)
        command = (
            f"PYTHONPATH=. python scripts/check_fleet_script_health.py {args.path} "
            f"{caller_args}".rstrip() + " --print-zero-evidence"
        )
        print(json.dumps(
            {
                "claim": (
                    "the live fleet bus carries zero known silent-failure defects as of "
                    "observed_on"
                ),
                "checker_output": "fleet-health: clean",
                "scanned_script_count": count,
                "manifest_sha256": digest,
                "manifest_command": command,
            },
            indent=2,
        ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
