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

Exit 0 = clean; 1 = findings (printed to stdout). Read-only; changes nothing.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SHELL_SUFFIXES = {".sh", ".cmd", ".ps1", ".py"}

# Directories that are NOT fleet machinery: per-task worker scratch checkouts, vendored deps, and
# runtime state. Scanning them buries the real findings in third-party noise — a gate nobody reads
# is the same silent failure this checker exists to prevent.
EXCLUDED_DIRS = {
    ".git",
    "workspaces",  # per-task worker checkouts (their own repos have their own CI)
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
PS_AMP_CALL = re.compile(
    r"^\s*&\s*(?P<target>\(\s*Join-Path[^)]*\)|\"[^\"]+\"|'[^']+'|\$\w+)"
)
PS_SCRIPT_TARGET = re.compile(r"[\w.-]+\.(ps1|py|sh|cmd|exe)", re.I)
# Evidence the verdict IS consumed anywhere in the file: an explicit exit-code test, a try/catch
# around the invocation, or the caller propagating it.
PS_EXIT_TESTED = re.compile(r"\$LASTEXITCODE|\btry\s*\{|\$\?", re.I)

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
PRECONDITION_WORDS = r"(?:trust|auth|provision|precheck|preflight)"
PRECONDITION_INVOKE = re.compile(
    r"^\s*(?:&\s*)?(?:python3?|powershell|bash)\b[^\n]*?(?P<script>"
    rf"[\w.-]*{PRECONDITION_WORDS}[\w.-]*\.(?:py|ps1|sh)"
    rf"|\$\w*{PRECONDITION_WORDS}\w*)",
    re.I,
)
# Evidence the launch it guards actually happens in the same file.
LAUNCH_AFTER = re.compile(r"claude\s+-p\b|ProcessStartInfo|Process\]::Start", re.I)


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
    tests = here.parent / "tests"
    stems = {here.stem, here.stem.removeprefix("check_")}
    return path.resolve() in {here} | {tests / f"test_{s}.py" for s in stems}


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
        # It must be a SCRIPT invocation; `& $someScriptBlock` is a different construct.
        target = m.group("target")
        named = PS_SCRIPT_TARGET.search(target) or PS_SCRIPT_TARGET.search(line)
        if not named:
            continue
        # The verdict test must be NEAR the invocation. A whole-file search let an unrelated
        # try/catch elsewhere in the script (feature-adoption-sweep.ps1 wraps its Push-Location
        # 30 lines above) excuse a genuinely unchecked delivery call — the same "prose counted as
        # enforcement" mistake the dead-gate and shape-only checks each had to be narrowed against.
        window = "\n".join(lines[max(0, i - 3) : i + 3])
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
    out: list[Finding] = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("#", "rem ", "REM ")):
            continue
        m = PRECONDITION_INVOKE.match(line)
        if not m:
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
    args = ap.parse_args()
    root = Path(args.path)
    if not root.exists():
        sys.stderr.write(f"fleet-health: path not found: {root}\n")
        return 2
    findings = run(root, [Path(c) for c in args.caller])
    for f in sorted(findings, key=lambda f: (str(f.path), f.line)):
        print(f.render(root if root.is_dir() else root.parent))
    if findings:
        print(f"\nfleet-health: {len(findings)} finding(s) — silent-failure class present")
        return 1
    print("fleet-health: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
