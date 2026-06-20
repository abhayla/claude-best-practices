"""Trust Score engine — the "approval score" for autonomous-factory pipeline runs.

A pipeline run hands in verification SIGNALS (each 0.0..1.0). The engine multiplies
each by its WEIGHT, sums to a 0-100 score, then applies HARD GATES (safety vetoes that
a good average can never out-vote) and SHADOW MODE (the engine only ever RECOMMENDS;
a human still acts) until calibration proves the score trustworthy.

Motto: don't build for autonomy — prove the trust score first.

CLI:
    python scripts/trust_score.py --signals run-signals.json [--stage deploy]
"""

import argparse
import json
from pathlib import Path

import yaml

# Mirrors config/trust-score.yml so the engine has a safe, importable default.
DEFAULT_CONFIG = {
    "weights": {
        "tests_pass": 0.30,
        "independent_verification": 0.25,
        "coverage": 0.15,
        "regression_clean": 0.10,
        "secret_scan_clean": 0.10,
        "production_health": 0.10,
    },
    "threshold": 85,
    "hard_gates": {"tests_pass": 1.0, "secret_scan_clean": 1.0},
    "irreversible_stages": ["deploy", "spend", "dns"],
    "shadow_mode": True,
    "calibration": {"min_runs": 30, "max_false_confidence_rate": 0.05},
}


def load_config(path: Path) -> dict:
    """Load the trust-score rulebook from YAML, falling back to DEFAULT_CONFIG."""
    if not path.exists():
        return DEFAULT_CONFIG
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or DEFAULT_CONFIG


def compute_trust_score(signals: dict, config: dict, stage: str | None = None) -> dict:
    """Score one pipeline run and decide AUTO vs ESCALATE.

    Args:
        signals: mapping of signal name -> value in [0.0, 1.0]. A signal absent from
            the mapping is treated as 0.0 (unknown == unproven), never skipped.
        config: the rulebook (see DEFAULT_CONFIG / config/trust-score.yml).
        stage: optional pipeline stage name; irreversible stages always escalate.

    Returns a dict with: score (0-100 int), recommended (AUTO|ESCALATE — what the score
    alone says, after gates), effective (what actually happens — always ESCALATE while
    shadow_mode is on), shadow_mode (bool), hard_gate_triggered (bool), reasons (list).
    """
    weights = config["weights"]
    threshold = config["threshold"]

    for name, value in signals.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"signal {name!r}={value} out of range [0.0, 1.0]")

    score_fraction = sum(weight * signals.get(name, 0.0) for name, weight in weights.items())
    score = int(round(score_fraction * 100))

    reasons: list[str] = []

    hard_gate_triggered = False
    for name, floor in config.get("hard_gates", {}).items():
        if signals.get(name, 0.0) < floor:
            hard_gate_triggered = True
            reasons.append(f"hard gate: {name} below safety floor {floor}")

    irreversible = stage in config.get("irreversible_stages", [])
    if irreversible:
        reasons.append(f"stage {stage!r} is irreversible — always escalate in crawl phase")

    if score >= threshold:
        reasons.append(f"score {score} >= threshold {threshold}")
    else:
        reasons.append(f"score {score} < threshold {threshold}")

    can_auto = score >= threshold and not hard_gate_triggered and not irreversible
    recommended = "AUTO" if can_auto else "ESCALATE"

    shadow_mode = config.get("shadow_mode", True)
    effective = "ESCALATE" if (shadow_mode or not can_auto) else "AUTO"

    return {
        "score": score,
        "recommended": recommended,
        "effective": effective,
        "shadow_mode": shadow_mode,
        "hard_gate_triggered": hard_gate_triggered,
        "reasons": reasons,
    }


def calibration_stats(runs: list[dict]) -> dict:
    """Measure whether the score is honest enough to graduate out of shadow mode.

    A "false confidence" is a run the engine would have AUTO-approved but where a human
    still had to fix something. The false-confidence RATE over AUTO runs is the number
    that must drop low before any stage is trusted to act unsupervised.
    """
    auto = [r for r in runs if r.get("recommended") == "AUTO"]
    false_confidence = sum(1 for r in auto if r.get("human_had_to_fix"))
    rate = (false_confidence / len(auto)) if auto else 0.0
    return {
        "total_runs": len(runs),
        "auto_runs": len(auto),
        "false_confidence": false_confidence,
        "false_confidence_rate": rate,
        "ready_to_graduate": len(runs) >= 30 and rate <= 0.05 and len(auto) > 0,
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description="Compute a trust score for a pipeline run.")
    parser.add_argument("--signals", required=True, type=Path, help="JSON file of signal values")
    parser.add_argument("--stage", default=None, help="pipeline stage name (optional)")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "config" / "trust-score.yml",
    )
    args = parser.parse_args()

    with open(args.signals, encoding="utf-8") as f:
        signals = json.load(f)
    config = load_config(args.config)
    result = compute_trust_score(signals, config, stage=args.stage)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
