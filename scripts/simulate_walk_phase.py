"""Walk-phase SIMULATION harness — fabricates realistic runs to stress-test the machinery.

This is a SANDBOX. It writes only to a separate simulation ledger so fabricated data can
NEVER contaminate the real calibration that governs real autonomy. Its purpose is to
(a) surface defects in the walk-phase controller and (b) show how graduation is earned.

Each fabricated round invents a finished task with a hidden ground-truth quality, derives
realistic signals from it, scores it with the trust engine, and records the run. After N
rounds it asks the graduation controller whether the stage earned autonomy.

    python scripts/simulate_walk_phase.py --rounds 30 --profile realistic --seed 7

Real graduation still requires REAL runs — see scripts/collect_signals.py.
"""

import argparse
import random
from pathlib import Path

from scripts.trust_score import (
    compute_trust_score,
    graduation_status,
    load_config,
    record_run,
)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "trust-score.yml"
SIM_LEDGER = ROOT / "trust-score" / "sim-ledger.jsonl"

# How often each hidden quality class appears, per profile.
#   good          -> genuinely fine; signals high; no human fix needed.
#   subtly_broken -> LOOKS fine (high score, AUTO) but a human had to fix it later.
#                    These are the dangerous FALSE-CONFIDENCE cases.
#   broken        -> a visible failure (test fail or secret leak); correctly escalated.
PROFILES = {
    "realistic": {"good": 0.75, "subtly_broken": 0.15, "broken": 0.10},
    "mature": {"good": 0.95, "subtly_broken": 0.02, "broken": 0.03},
}


def fabricate_round(rng: random.Random, profile: str, stage: str) -> dict:
    """Invent one realistic finished-task event: signals + hidden ground truth."""
    weights = PROFILES[profile]
    klass = rng.choices(list(weights), weights=list(weights.values()))[0]

    if klass == "good":
        signals = {
            "tests_pass": 1.0,
            "independent_verification": 1.0,
            "coverage": round(rng.uniform(0.85, 0.99), 2),
            "regression_clean": 1.0,
            "secret_scan_clean": 1.0,
            "production_health": 1.0,
        }
        human_had_to_fix = False
    elif klass == "subtly_broken":
        # Everything the automated checks see looks fine -> high score, AUTO -> but a
        # latent bug the tests didn't cover means a human still had to step in.
        signals = {
            "tests_pass": 1.0,
            "independent_verification": 1.0,
            "coverage": round(rng.uniform(0.82, 0.95), 2),
            "regression_clean": 1.0,
            "secret_scan_clean": 1.0,
            "production_health": 1.0,
        }
        human_had_to_fix = True
    else:  # broken — a visible failure the gates should catch
        if rng.random() < 0.5:
            signals = {
                "tests_pass": round(rng.uniform(0.7, 0.95), 2),  # some tests failed
                "independent_verification": 0.0,
                "coverage": round(rng.uniform(0.5, 0.8), 2),
                "regression_clean": 0.0,
                "secret_scan_clean": 1.0,
                "production_health": 1.0,
            }
        else:
            signals = {  # a leaked secret -> hard gate
                "tests_pass": 1.0,
                "independent_verification": 1.0,
                "coverage": round(rng.uniform(0.85, 0.95), 2),
                "regression_clean": 1.0,
                "secret_scan_clean": 0.0,
                "production_health": 1.0,
            }
        human_had_to_fix = True

    return {"class": klass, "signals": signals, "human_had_to_fix": human_had_to_fix, "stage": stage}


def run_simulation(rounds: int, profile: str, stage: str, seed: int, ledger_path: Path) -> dict:
    """Fabricate `rounds` runs into a fresh sim ledger and return the graduation report."""
    if ledger_path.exists():
        ledger_path.unlink()  # each simulation starts from an empty sandbox ledger

    config = load_config(CONFIG_PATH)
    rng = random.Random(seed)
    log = []
    for i in range(1, rounds + 1):
        ev = fabricate_round(rng, profile, stage)
        result = compute_trust_score(ev["signals"], config, stage=stage)
        record_run(result, ledger_path, human_had_to_fix=ev["human_had_to_fix"], stage=stage)
        false_confidence = result["recommended"] == "AUTO" and ev["human_had_to_fix"]
        log.append(
            {
                "round": i,
                "class": ev["class"],
                "score": result["score"],
                "recommended": result["recommended"],
                "human_had_to_fix": ev["human_had_to_fix"],
                "false_confidence": false_confidence,
            }
        )

    from scripts.trust_score import load_ledger

    grad = graduation_status(load_ledger(ledger_path), config)
    return {"profile": profile, "stage": stage, "rounds": rounds, "log": log, "graduation": grad}


def _print_report(report: dict) -> None:
    print(f"\n=== SIMULATION: {report['rounds']} rounds, profile='{report['profile']}', "
          f"stage='{report['stage']}' (SANDBOX -- does not affect real calibration) ===")
    for row in report["log"]:
        flag = "  <-- FALSE CONFIDENCE" if row["false_confidence"] else ""
        print(f"  r{row['round']:>2} | {row['class']:<14} | score {row['score']:>3} | "
              f"{row['recommended']:<8} | human_fix={str(row['human_had_to_fix']):<5}{flag}")
    st = report["graduation"]["stages"].get(report["stage"], {})
    print(f"\n  total_runs={st.get('total_runs')} auto_runs={st.get('auto_runs')} "
          f"false_confidence={st.get('false_confidence')} "
          f"rate={st.get('false_confidence_rate', 0):.3f} "
          f"graduated={st.get('graduated')}")
    print(f"  graduated stages: {report['graduation']['graduated_stages'] or 'NONE -- autonomy not earned'}")


def _main() -> int:
    p = argparse.ArgumentParser(description="Simulate walk-phase runs in a sandbox.")
    p.add_argument("--rounds", type=int, default=30)
    p.add_argument("--profile", choices=list(PROFILES), default="realistic")
    p.add_argument("--stage", default="test")
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args()
    report = run_simulation(args.rounds, args.profile, args.stage, args.seed, SIM_LEDGER)
    _print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
