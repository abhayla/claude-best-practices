"""Collect REAL verification signals from a finished task and record a calibration run.

This is the "wire real signals" adapter: instead of hand-typing the signals JSON, it
assembles the signals from actual evidence (test results, coverage, a live secret-scan),
scores them with the trust engine, and records the run to the calibration ledger — so
walk-phase honesty data accumulates automatically as real tasks complete.

    python scripts/collect_signals.py --tests-passed 1494 --tests-total 1494 \
        --coverage 0.9 --independent-verification 1 --stage test --record
"""

import argparse
import os
import subprocess
from pathlib import Path

from scripts.trust_score import (
    compute_trust_score,
    load_config,
    record_run,
)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "trust-score.yml"
LEDGER_PATH = ROOT / "trust-score" / "calibration-ledger.jsonl"


def default_ledger_for(project: str) -> Path:
    """Per-project ledger path. Calibration is per-project — IPODhan's trust history
    can never vouch for another app — so each project gets its own ledger file."""
    return ROOT / "trust-score" / "ledgers" / f"{project}.jsonl"


def run_secret_scan() -> float:
    """Run the repo's secret-scan live; return 1.0 if confirmed clean, else 0.0."""
    try:
        out = subprocess.run(
            ["python", "scripts/dedup_check.py", "--secret-scan"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "."},
        ).stdout
    except Exception:
        return 0.0  # unknown == unproven
    return 1.0 if "No secrets found" in out else 0.0


def assemble_signals(
    tests_passed: int,
    tests_total: int,
    coverage: float,
    independent_verification: float,
    regression_clean: float,
    production_health: float,
    secret_scan_clean: float,
) -> dict:
    """Build the signals dict from measured evidence. Each value is clamped to [0,1]."""
    tests_pass = (tests_passed / tests_total) if tests_total else 0.0

    def clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    return {
        "tests_pass": clamp(tests_pass),
        "independent_verification": clamp(independent_verification),
        "coverage": clamp(coverage),
        "regression_clean": clamp(regression_clean),
        "secret_scan_clean": clamp(secret_scan_clean),
        "production_health": clamp(production_health),
    }


def collect_and_record(
    signals: dict,
    stage: str | None,
    record: bool,
    human_had_to_fix=None,
    ledger_path: Path | None = None,
    config_path: Path | None = None,
) -> dict:
    """Score assembled signals and (optionally) record the run to a chosen ledger.

    Paths resolve at call time (not import time) so the module-level LEDGER_PATH /
    CONFIG_PATH stay overridable — passing None uses the current module defaults.
    """
    config = load_config(config_path or CONFIG_PATH)
    result = compute_trust_score(signals, config, stage=stage)
    if record:
        record_run(result, ledger_path or LEDGER_PATH, human_had_to_fix=human_had_to_fix, stage=stage)
    return result


def _main() -> int:
    p = argparse.ArgumentParser(description="Assemble real signals, score, and record a run.")
    p.add_argument("--tests-passed", type=int, default=0)
    p.add_argument("--tests-total", type=int, default=0)
    p.add_argument("--coverage", type=float, default=0.0)
    p.add_argument("--independent-verification", type=float, default=0.0)
    p.add_argument("--regression-clean", type=float, default=1.0)
    p.add_argument("--production-health", type=float, default=1.0)
    p.add_argument(
        "--secret-scan-clean",
        choices=["yes", "no"],
        default=None,
        help="per-project secret-scan result; if omitted, the hub's own scan runs "
        "(only meaningful when scoring the hub itself)",
    )
    p.add_argument("--stage", default=None)
    p.add_argument("--record", action="store_true")
    p.add_argument("--human-had-to-fix", choices=["yes", "no"], default=None)
    p.add_argument("--project", default=None, help="per-project ledger name (e.g. IPODhan)")
    p.add_argument("--ledger", type=Path, default=None, help="explicit ledger path (overrides --project)")
    p.add_argument("--config", type=Path, default=CONFIG_PATH, help="trust-score rulebook")
    args = p.parse_args()

    ledger_path = args.ledger or (default_ledger_for(args.project) if args.project else LEDGER_PATH)

    signals = assemble_signals(
        tests_passed=args.tests_passed,
        tests_total=args.tests_total,
        coverage=args.coverage,
        independent_verification=args.independent_verification,
        regression_clean=args.regression_clean,
        production_health=args.production_health,
        secret_scan_clean=(
            {"yes": 1.0, "no": 0.0}[args.secret_scan_clean]
            if args.secret_scan_clean is not None
            else run_secret_scan()
        ),
    )
    fix = {"yes": True, "no": False, None: None}[args.human_had_to_fix]
    result = collect_and_record(
        signals, args.stage, args.record, human_had_to_fix=fix,
        ledger_path=ledger_path, config_path=args.config,
    )
    import json

    out = {"signals": signals, "result": result}
    if args.record:
        out["recorded_to"] = str(ledger_path)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
