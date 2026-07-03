"""Honest per-task trust-score accrual (#196) — auto-appends ONE calibration run to the
ATLAS ledger per completed task, so N/30 grows from real work instead of staying at the
floor forever. Shadow-mode only: this script NEVER auto-lands anything — it records a
run for later calibration review (see scripts/trust_score.py graduation_status()).

Real signals:
    tests_pass              -> parsed from a live `pytest scripts/tests/ -q` run
    secret_scan_clean       -> collect_signals.run_secret_scan() (live scan)
    independent_verification-> 1.0 only if --reviewed is passed (an agent/human actually
                                reviewed the branch), else 0.0 (honest unknown, not a guess)
    regression_clean        -> 1.0 only if the full suite passed, else 0.0
    coverage                -> --coverage value if supplied, else 0.0 (honest unknown)
    production_health       -> 1.0 default (a hub task has no production surface to break)

human_had_to_fix (the ground-truth label calibration_stats() needs) is DERIVED from an
honest git proxy — never silently defaulted to False:
    - commit_count (current branch vs merge-base with origin/main) > 1, OR
    - any commit subject (beyond the first) matches a "this needed a correction round"
      pattern (fix|resync|follow-up|review|hash|drift|address)
      -> True
    - exactly one clean commit, no matching subject -> False
    - merge-base/commit history can't be determined -> None (honest unknown)
A `--human-had-to-fix yes|no` override always wins over the proxy (supervisor ground truth).

Idempotent per branch: records at most once per branch name, tracked in a marker file
(trust-score/.recorded-branches, gitignored) so re-running `finish` on the same branch
doesn't inflate the ledger.

CLI:
    python scripts/record_task_run.py [--stage reversible] [--reviewed] [--coverage 0.9]
        [--human-had-to-fix yes|no]
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

from scripts.collect_signals import assemble_signals, collect_and_record, default_ledger_for, run_secret_scan

ROOT = Path(__file__).resolve().parent.parent
MARKER_PATH = ROOT / "trust-score" / ".recorded-branches"

_FIX_PATTERN = re.compile(r"(?i)fix|resync|follow-up|review|hash|drift|address")


def current_branch(cwd: Path | None = None) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = out.stdout.strip()
        return branch or None
    except Exception:
        return None


def _merge_base(cwd: Path | None = None) -> str | None:
    for ref in ("origin/main", "main"):
        try:
            out = subprocess.run(
                ["git", "merge-base", ref, "HEAD"],
                cwd=cwd or ROOT,
                capture_output=True,
                text=True,
            )
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except Exception:
            continue
    return None


def derive_human_had_to_fix(cwd: Path | None = None) -> bool | None:
    """Honest git proxy for whether this task's work needed a correction round.

    Returns None (not False) whenever the history can't be determined — an
    indeterminate proxy must never masquerade as a clean pass.
    """
    base = _merge_base(cwd)
    if base is None:
        return None

    out = subprocess.run(
        ["git", "log", "--oneline", f"{base}..HEAD"],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return None

    lines = [line for line in out.stdout.splitlines() if line.strip()]
    if not lines:
        return None  # no commits ahead of base — nothing to judge

    if len(lines) > 1:
        return True

    subject = lines[0].split(" ", 1)[1] if " " in lines[0] else ""
    return bool(_FIX_PATTERN.search(subject))


def _parse_pytest_summary(output: str) -> tuple[int, int]:
    """Parse `N passed[, M failed][, ...] in Xs` from pytest -q output. Returns (passed, total)."""
    passed = len(re.findall(r"(\d+) passed", output))
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    error_match = re.search(r"(\d+) error", output)
    passed_n = int(passed_match.group(1)) if passed_match else 0
    failed_n = int(failed_match.group(1)) if failed_match else 0
    error_n = int(error_match.group(1)) if error_match else 0
    total = passed_n + failed_n + error_n
    return passed_n, total


def run_tests() -> tuple[int, int, bool]:
    """Run the full test suite live; return (passed, total, all_passed)."""
    import os

    result = subprocess.run(
        ["python", "-m", "pytest", "scripts/tests/", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "."},
    )
    passed, total = _parse_pytest_summary(result.stdout + result.stderr)
    return passed, total, result.returncode == 0


def already_recorded(branch: str, marker_path: Path) -> bool:
    if not marker_path.exists():
        return False
    recorded = {line.strip() for line in marker_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    return branch in recorded


def mark_recorded(branch: str, marker_path: Path) -> None:
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(marker_path, "a", encoding="utf-8") as f:
        f.write(branch + "\n")


def record_task_run(
    stage: str = "reversible",
    reviewed: bool = False,
    coverage: float = 0.0,
    human_had_to_fix_override: bool | None = None,
    cwd: Path | None = None,
    marker_path: Path | None = None,
    ledger_path: Path | None = None,
) -> dict:
    """Assemble real signals for the current branch's task and record one honest run.

    Returns a dict describing the outcome: {"status": "recorded"|"already_recorded",
    "branch": ..., "signals": ..., "result": ..., "human_had_to_fix": ...}. Never lands
    or merges anything — shadow-mode recording only.
    """
    marker_path = marker_path or MARKER_PATH
    branch = current_branch(cwd)

    if branch and already_recorded(branch, marker_path):
        return {"status": "already_recorded", "branch": branch}

    passed, total, all_passed = run_tests()
    tests_pass_signals = assemble_signals(
        tests_passed=passed,
        tests_total=total,
        coverage=coverage,
        independent_verification=1.0 if reviewed else 0.0,
        regression_clean=1.0 if all_passed else 0.0,
        production_health=1.0,
        secret_scan_clean=run_secret_scan(),
    )

    human_had_to_fix = (
        human_had_to_fix_override if human_had_to_fix_override is not None else derive_human_had_to_fix(cwd)
    )

    ledger = ledger_path or default_ledger_for("atlas")
    result = collect_and_record(
        tests_pass_signals,
        stage,
        record=True,
        human_had_to_fix=human_had_to_fix,
        ledger_path=ledger,
    )

    if branch:
        mark_recorded(branch, marker_path)

    from scripts.trust_score import load_ledger

    return {
        "status": "recorded",
        "branch": branch,
        "signals": tests_pass_signals,
        "result": result,
        "human_had_to_fix": human_had_to_fix,
        "ledger": str(ledger),
        "total_runs": len(load_ledger(ledger)),
    }


def _main() -> int:
    p = argparse.ArgumentParser(description="Record one honest calibration run for the current task (#196).")
    p.add_argument("--stage", default="reversible", choices=["reversible", "build", "irreversible"])
    p.add_argument("--reviewed", action="store_true", help="an agent/human reviewed the branch")
    p.add_argument("--coverage", type=float, default=0.0)
    p.add_argument("--human-had-to-fix", choices=["yes", "no"], default=None)
    args = p.parse_args()

    override = {"yes": True, "no": False, None: None}[args.human_had_to_fix]
    outcome = record_task_run(
        stage=args.stage,
        reviewed=args.reviewed,
        coverage=args.coverage,
        human_had_to_fix_override=override,
    )

    if outcome["status"] == "already_recorded":
        print(f"already recorded for branch {outcome['branch']!r} — skipping (idempotent)")
        return 0

    print(json.dumps(outcome, indent=2))
    print(f"\nrecorded to {outcome['ledger']} — N/30 = {outcome['total_runs']}/30")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
