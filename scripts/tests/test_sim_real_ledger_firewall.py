"""Firewall regression lock (#196 DoD): sandbox walk-phase SIMULATIONS must never
touch the REAL trust-score calibration ledgers that gate G5 graduation.

The walk-phase controller's entire value is HONESTY — the graduation count (N/30) must
reflect real completed tasks only. If fabricated simulation runs could reach the atlas /
calibration ledger, they would inflate the count and defeat the subsystem's purpose. These
tests pin the sim↔real firewall so a future refactor can't silently breach it.
"""

from pathlib import Path

import scripts.collect_signals as collect_signals
import scripts.generate_trust_dashboard as dashboard
import scripts.simulate_walk_phase as sim
from scripts.simulate_walk_phase import SIM_LEDGER, run_simulation
from scripts.trust_score import load_ledger


def test_sim_ledger_is_distinct_from_every_real_ledger():
    """The sandbox ledger path must differ from all real ledgers (static firewall)."""
    real_ledgers = {
        collect_signals.LEDGER_PATH.resolve(),  # default calibration ledger
        collect_signals.default_ledger_for("atlas").resolve(),  # per-project graduation ledger
        dashboard.ATLAS_LEDGER.resolve(),  # what the dashboard counts N/30 from
    }
    assert SIM_LEDGER.resolve() not in real_ledgers, (
        "sim ledger shares a path with a REAL calibration ledger — firewall breached"
    )
    assert SIM_LEDGER.name == "sim-ledger.jsonl"


def test_simulation_does_not_mutate_the_real_atlas_ledger(tmp_path):
    """Running a simulation leaves the REAL atlas ledger byte-identical (behavioral firewall)."""
    atlas = dashboard.ATLAS_LEDGER
    before = atlas.read_bytes() if atlas.exists() else None

    sandbox = tmp_path / "sim-ledger.jsonl"
    run_simulation(rounds=5, profile="realistic", stage="test", seed=1, ledger_path=sandbox)

    after = atlas.read_bytes() if atlas.exists() else None
    assert before == after, "a sandbox simulation mutated the REAL atlas ledger"
    # the fabricated runs must have landed in the sandbox, not vanished
    assert sandbox.exists() and len(load_ledger(sandbox)) == 5


def test_module_default_sim_target_is_the_sandbox_not_a_real_ledger():
    """The module-level default the CLI writes to must be the sandbox, never a real ledger."""
    assert sim.SIM_LEDGER != dashboard.ATLAS_LEDGER
    assert sim.SIM_LEDGER != collect_signals.default_ledger_for("atlas")
    assert sim.SIM_LEDGER != collect_signals.LEDGER_PATH


def test_dashboard_graduation_count_is_unaffected_by_a_simulation(tmp_path):
    """A sandbox simulation must not change the N/30 count the dashboard reads from atlas."""
    before = dashboard._read_calibration(dashboard.ATLAS_LEDGER)["runs"]
    run_simulation(rounds=7, profile="realistic", stage="test", seed=2, ledger_path=tmp_path / "s.jsonl")
    after = dashboard._read_calibration(dashboard.ATLAS_LEDGER)["runs"]
    assert before == after, "a sandbox simulation changed the REAL graduation count (N/30)"
