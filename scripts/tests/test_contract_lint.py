"""Regression tests for the bus-side contract-lint.py `READS_DATA` scope (T-021).

contract-lint.py is fleet machinery that lives on the bus (C:/Abhay/GetWorkDone), not in this
hub's PR diff — see scripts/tests/test_fleet_script_health.py for the same skip-if-absent pattern
used for other bus-side scripts. It is invoked as a CLI subprocess (its `main()` runs at import
time and calls sys.exit(), so it cannot be imported as a library).

T-020 wired contract-lint.py into the dispatch path; T-013 gave it a `data_source:` requirement
for any contract that reads external data. The requirement's original regex matched bare
audit/verify/compare/cross-check verbs anywhere in the contract, so it also blocked purely
code-only contracts that happen to use those words about the CODE (e.g. "audit the fleet
scripts"). These tests pin both directions so neither regresses:
  - a code-only contract with no external-data signal must PASS (the false positive this task
    fixes)
  - a contract that genuinely reads/compares external data with no declared `data_source:` must
    still BLOCK (the T-013 hole the gate exists to close)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

CONTRACT_LINT = Path("C:/Abhay/GetWorkDone/contract-lint.py")

REQUIRED_FIELDS = "repo: r\nmodel: m\npriority: P2\nevidence: required\n"

pytestmark = pytest.mark.skipif(
    not CONTRACT_LINT.exists(), reason="bus checkout not present on this host"
)


def _lint(tmp_path: Path, body: str, extra_frontmatter: str = "") -> subprocess.CompletedProcess:
    contract = tmp_path / "contract.md"
    contract.write_text(
        f"---\n{REQUIRED_FIELDS}{extra_frontmatter}---\n\n{body}\n", encoding="utf-8"
    )
    return subprocess.run(
        [sys.executable, str(CONTRACT_LINT), str(contract)],
        capture_output=True,
        text=True,
    )


def test_code_only_audit_contract_passes(tmp_path: Path):
    """'audit the fleet scripts for dead gates' reads no external data — must not block."""
    proc = _lint(
        tmp_path,
        "# Task\n\n"
        "Audit the fleet scripts for dead gates and verify each guard's exit code is "
        "checked. Compare the current keeper-tick.cmd to the fixed form and "
        "cross-check every guard invocation.\n",
    )
    assert proc.returncode == 0, proc.stderr
    assert "CONTRACT-OK" in proc.stdout


def test_external_data_comparison_without_source_still_blocks(tmp_path: Path):
    """Comparing app data against a CRM export with no data_source: must still block (T-013)."""
    proc = _lint(
        tmp_path,
        "# Task\n\n"
        "Reconcile the app's contact records against the Zoho CRM export and cross-check "
        "counts for drift.\n",
    )
    assert proc.returncode == 1
    assert "data_source" in proc.stderr


def test_external_data_comparison_with_source_passes(tmp_path: Path):
    """The same external-data task passes once data_source: is declared."""
    proc = _lint(
        tmp_path,
        "# Task\n\nReconcile the app's contact records against the Zoho CRM export.\n",
        extra_frontmatter="data_source: Zoho CRM COQL export (org 60019670093)\n",
    )
    assert proc.returncode == 0, proc.stderr
