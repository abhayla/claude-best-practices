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
