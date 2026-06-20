"""Tests for the trust-score engine (scripts/trust_score.py).

Written before the implementation (TDD). These pin the engine's contract:
weighted scoring, hard safety gates, irreversible-stage handling, shadow mode,
input validation, and calibration stats.
"""

import pytest

from scripts.trust_score import (
    DEFAULT_CONFIG,
    calibration_stats,
    compute_trust_score,
)


def _perfect_signals():
    return {
        "tests_pass": 1.0,
        "independent_verification": 1.0,
        "coverage": 1.0,
        "regression_clean": 1.0,
        "secret_scan_clean": 1.0,
        "production_health": 1.0,
    }


class TestScoring:
    def test_perfect_signals_score_100(self):
        result = compute_trust_score(_perfect_signals(), DEFAULT_CONFIG)
        assert result["score"] == 100

    def test_weighted_math_is_correct(self):
        # Only tests_pass perfect (weight 0.30), everything else 0 -> 30.
        signals = {k: 0.0 for k in _perfect_signals()}
        signals["tests_pass"] = 1.0
        result = compute_trust_score(signals, DEFAULT_CONFIG)
        assert result["score"] == 30

    def test_high_score_recommends_auto(self):
        result = compute_trust_score(_perfect_signals(), DEFAULT_CONFIG)
        assert result["recommended"] == "AUTO"

    def test_below_threshold_recommends_escalate(self):
        signals = _perfect_signals()
        signals["independent_verification"] = 0.0  # drops score to 75 (< 85)
        result = compute_trust_score(signals, DEFAULT_CONFIG)
        assert result["score"] == 75
        assert result["recommended"] == "ESCALATE"


class TestHardGates:
    def test_secret_leak_forces_escalate_despite_high_score(self):
        signals = _perfect_signals()
        signals["secret_scan_clean"] = 0.0
        result = compute_trust_score(signals, DEFAULT_CONFIG)
        assert result["recommended"] == "ESCALATE"
        assert result["hard_gate_triggered"] is True
        assert any("secret_scan_clean" in r for r in result["reasons"])

    def test_failing_test_forces_escalate(self):
        signals = _perfect_signals()
        signals["tests_pass"] = 0.99  # below the 1.0 floor
        result = compute_trust_score(signals, DEFAULT_CONFIG)
        assert result["recommended"] == "ESCALATE"
        assert result["hard_gate_triggered"] is True


class TestIrreversibleStages:
    def test_irreversible_stage_always_escalates(self):
        result = compute_trust_score(_perfect_signals(), DEFAULT_CONFIG, stage="deploy")
        assert result["recommended"] == "ESCALATE"
        assert any("irreversible" in r for r in result["reasons"])

    def test_reversible_stage_can_auto(self):
        result = compute_trust_score(_perfect_signals(), DEFAULT_CONFIG, stage="test")
        assert result["recommended"] == "AUTO"


class TestShadowMode:
    def test_shadow_mode_effective_decision_always_escalate(self):
        # shadow_mode true in DEFAULT_CONFIG: recommend AUTO but EFFECTIVE is ESCALATE.
        result = compute_trust_score(_perfect_signals(), DEFAULT_CONFIG)
        assert result["recommended"] == "AUTO"
        assert result["effective"] == "ESCALATE"
        assert result["shadow_mode"] is True

    def test_shadow_off_lets_auto_through(self):
        cfg = {**DEFAULT_CONFIG, "shadow_mode": False}
        result = compute_trust_score(_perfect_signals(), cfg)
        assert result["effective"] == "AUTO"


class TestValidation:
    def test_signal_out_of_range_raises(self):
        signals = _perfect_signals()
        signals["coverage"] = 1.5
        with pytest.raises(ValueError):
            compute_trust_score(signals, DEFAULT_CONFIG)

    def test_missing_signal_defaults_to_zero(self):
        # An absent signal is treated as 0.0 (unknown = unproven), not skipped.
        signals = _perfect_signals()
        del signals["coverage"]
        result = compute_trust_score(signals, DEFAULT_CONFIG)
        assert result["score"] == 85  # lost 0.15 * 100


class TestCalibration:
    def test_false_confidence_rate(self):
        # 4 runs the engine would AUTO; 1 of them the human had to fix -> 25%.
        runs = [
            {"recommended": "AUTO", "human_had_to_fix": False},
            {"recommended": "AUTO", "human_had_to_fix": False},
            {"recommended": "AUTO", "human_had_to_fix": False},
            {"recommended": "AUTO", "human_had_to_fix": True},
            {"recommended": "ESCALATE", "human_had_to_fix": True},
        ]
        stats = calibration_stats(runs)
        assert stats["auto_runs"] == 4
        assert stats["false_confidence"] == 1
        assert stats["false_confidence_rate"] == 0.25

    def test_empty_calibration_is_safe(self):
        stats = calibration_stats([])
        assert stats["auto_runs"] == 0
        assert stats["false_confidence_rate"] == 0.0
        assert stats["ready_to_graduate"] is False
