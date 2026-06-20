"""Tests for the walk-phase graduation controller and the simulation harness."""

from scripts.trust_score import DEFAULT_CONFIG, graduation_status, walk_decision
from scripts.simulate_walk_phase import run_simulation


def _runs(n, recommended="AUTO", human_had_to_fix=False, stage="test"):
    return [
        {"score": 98, "recommended": recommended, "human_had_to_fix": human_had_to_fix, "stage": stage}
        for _ in range(n)
    ]


class TestGraduation:
    def test_reversible_stage_graduates_with_clean_history(self):
        status = graduation_status(_runs(30, human_had_to_fix=False), DEFAULT_CONFIG)
        assert status["stages"]["test"]["graduated"] is True
        assert "test" in status["graduated_stages"]

    def test_irreversible_stage_never_graduates(self):
        # Even 30 perfect AUTO runs on deploy must NOT graduate.
        status = graduation_status(_runs(30, stage="deploy"), DEFAULT_CONFIG)
        assert status["stages"]["deploy"]["reversible"] is False
        assert status["stages"]["deploy"]["graduated"] is False

    def test_too_few_runs_does_not_graduate(self):
        status = graduation_status(_runs(10), DEFAULT_CONFIG)
        assert status["stages"]["test"]["graduated"] is False

    def test_high_false_confidence_blocks_graduation(self):
        runs = _runs(24, human_had_to_fix=False) + _runs(6, human_had_to_fix=True)
        status = graduation_status(runs, DEFAULT_CONFIG)
        assert status["stages"]["test"]["false_confidence_rate"] == 0.2
        assert status["stages"]["test"]["graduated"] is False


class TestWalkDecision:
    def test_graduated_stage_autos(self):
        result = {"recommended": "AUTO"}
        assert walk_decision(result, ["test"], "test") == "AUTO"

    def test_ungraduated_stage_escalates(self):
        result = {"recommended": "AUTO"}
        assert walk_decision(result, [], "test") == "ESCALATE"

    def test_escalate_recommendation_never_autos(self):
        result = {"recommended": "ESCALATE"}
        assert walk_decision(result, ["test"], "test") == "ESCALATE"


class TestSimulation:
    def test_is_deterministic_for_a_seed(self, tmp_path):
        a = run_simulation(30, "realistic", "test", seed=7, ledger_path=tmp_path / "a.jsonl")
        b = run_simulation(30, "realistic", "test", seed=7, ledger_path=tmp_path / "b.jsonl")
        fc_a = sum(1 for r in a["log"] if r["false_confidence"])
        fc_b = sum(1 for r in b["log"] if r["false_confidence"])
        assert fc_a == fc_b

    def test_mature_profile_graduates_realistic_does_not(self, tmp_path):
        realistic = run_simulation(30, "realistic", "test", seed=7, ledger_path=tmp_path / "r.jsonl")
        mature = run_simulation(30, "mature", "test", seed=7, ledger_path=tmp_path / "m.jsonl")
        assert realistic["graduation"]["stages"]["test"]["graduated"] is False
        assert mature["graduation"]["stages"]["test"]["graduated"] is True

    def test_sim_writes_only_to_its_own_ledger(self, tmp_path):
        sim = tmp_path / "sim.jsonl"
        run_simulation(5, "realistic", "test", seed=1, ledger_path=sim)
        assert sim.exists()  # sandbox ledger, isolated from the real one
