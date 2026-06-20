"""Tests for the real-signal adapter (scripts/collect_signals.py)."""

from scripts.collect_signals import assemble_signals, collect_and_record, default_ledger_for


class TestAssembleSignals:
    def test_tests_pass_is_a_ratio(self):
        sig = assemble_signals(90, 100, 0.8, 1.0, 1.0, 1.0, 1.0)
        assert sig["tests_pass"] == 0.9

    def test_zero_total_is_unproven_not_crash(self):
        sig = assemble_signals(0, 0, 0.0, 0.0, 1.0, 1.0, 1.0)
        assert sig["tests_pass"] == 0.0

    def test_values_are_clamped(self):
        sig = assemble_signals(100, 100, 1.5, -0.2, 1.0, 1.0, 1.0)
        assert sig["coverage"] == 1.0
        assert sig["independent_verification"] == 0.0


class TestCollectAndRecord:
    def test_full_pass_recommends_auto_but_shadow_escalates(self):
        sig = assemble_signals(100, 100, 0.95, 1.0, 1.0, 1.0, 1.0)
        result = collect_and_record(sig, stage="test", record=False)
        assert result["recommended"] == "AUTO"
        assert result["effective"] == "ESCALATE"  # shadow mode

    def test_records_to_ledger(self, tmp_path, monkeypatch):
        import scripts.collect_signals as cs

        ledger = tmp_path / "ledger.jsonl"
        monkeypatch.setattr(cs, "LEDGER_PATH", ledger)
        sig = assemble_signals(100, 100, 0.95, 1.0, 1.0, 1.0, 1.0)
        cs.collect_and_record(sig, stage="test", record=True, human_had_to_fix=False)
        from scripts.trust_score import load_ledger

        runs = load_ledger(ledger)
        assert len(runs) == 1
        assert runs[0]["human_had_to_fix"] is False

    def test_secret_leak_forces_escalate(self):
        sig = assemble_signals(100, 100, 0.95, 1.0, 1.0, 1.0, 0.0)  # secret scan dirty
        result = collect_and_record(sig, stage="test", record=False)
        assert result["recommended"] == "ESCALATE"
        assert result["hard_gate_triggered"] is True


class TestPerProjectLedger:
    def test_default_ledger_path_is_per_project(self):
        assert default_ledger_for("IPODhan").name == "IPODhan.jsonl"
        assert default_ledger_for("KKB").name == "KKB.jsonl"

    def test_records_to_explicit_project_ledger(self, tmp_path):
        from scripts.trust_score import load_ledger

        ledger = tmp_path / "IPODhan.jsonl"
        sig = assemble_signals(100, 100, 0.95, 1.0, 1.0, 1.0, 1.0)
        collect_and_record(sig, stage="test", record=True, human_had_to_fix=False, ledger_path=ledger)
        runs = load_ledger(ledger)
        assert len(runs) == 1 and runs[0]["stage"] == "test"
