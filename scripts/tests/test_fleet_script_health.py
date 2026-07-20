"""Self-tests for check_fleet_script_health.py.

Each test plants the EXACT known-bad construct from the 2026-07-20 GetWorkDone fleet audit and
asserts the gate fires on it, then plants the fixed form and asserts the gate goes quiet. A gate
that cannot be shown to fire on the defect it targets is not a gate (learning-to-gate doctrine).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.check_fleet_script_health import run

CHECKER = Path(__file__).resolve().parents[1] / "check_fleet_script_health.py"
# The dispatcher lives in the hub, outside the fleet dir, but is contract-lint.py's real caller.
_DISPATCHER_SKILL = (
    Path(__file__).resolve().parents[2] / ".claude" / "skills" / "get-work-done" / "SKILL.md"
)


def _checks(findings, name):
    return [f for f in findings if f.check == name]


# ---------------------------------------------------------------- grep-count (HIGH: break-detect)


def test_grep_count_fallback_is_flagged(tmp_path: Path):
    """`seen=$(grep -c ... || echo 0)` + numeric test = the inverted-debounce defect."""
    script = tmp_path / "break-detect.sh"
    script.write_text(
        "#!/bin/bash\n"
        'file_break () {\n'
        '  local seen; seen=$(grep -c "^$key$" "$STATE" 2>/dev/null || echo 0)\n'
        '  if [ "$seen" -lt 1 ]; then echo "$key" >> "$STATE"; return; fi\n'
        "}\n",
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "grep-count"), "gate missed the grep -c debounce inversion"


def test_grep_count_fixed_form_is_clean(tmp_path: Path):
    """The corrected form (no `|| echo`, count normalised) must NOT trip the gate."""
    script = tmp_path / "break-detect.sh"
    script.write_text(
        "#!/bin/bash\n"
        'file_break () {\n'
        '  local seen; seen=$(grep -c "^$key$" "$STATE" 2>/dev/null); seen=${seen:-0}\n'
        '  if [ "$seen" -lt 1 ]; then echo "$key" >> "$STATE"; return; fi\n'
        "}\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "grep-count")


def test_grep_count_defect_is_real_not_theoretical():
    """Prove the underlying shell behaviour: grep -c || echo 0 really does emit two lines."""
    bash = Path("C:/Program Files/Git/usr/bin/bash.exe")
    if not bash.exists():
        pytest.skip("Git bash not available on this host")
    proc = subprocess.run(
        [str(bash), "-c", 'seen=$(grep -c "^zzz$" /dev/null 2>/dev/null || echo 0); echo "[$seen]"'],
        capture_output=True,
        text=True,
    )
    assert proc.stdout.strip() == "[0\n0]".strip() or "\n" in proc.stdout.strip("[]\n "), (
        f"expected a two-line count, got {proc.stdout!r}"
    )


# -------------------------------------------------------------- interpreter (HIGH: break-detect)


def test_missing_interpreter_suppressed_is_flagged(tmp_path: Path):
    """python3 with stderr discarded: absence looks exactly like an empty sweep."""
    script = tmp_path / "break-detect.sh"
    script.write_text(
        "#!/bin/bash\n"
        'mapfile -t REPOS < <(python3 -c "import json;print(1)" 2>/dev/null | grep -v "^_")\n'
        'echo "swept ${#REPOS[@]} repos"\n',
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "interpreter")
    assert findings, "gate missed the suppressed-interpreter silent no-op"
    assert "indistinguishable" in findings[0].message


def test_resolved_interpreter_is_clean(tmp_path: Path):
    """Resolving the interpreter up front and aborting loudly must pass."""
    script = tmp_path / "break-detect.sh"
    script.write_text(
        "#!/bin/bash\n"
        'PY=$(command -v python3 || command -v python) || { echo "no python" >&2; exit 3; }\n'
        'mapfile -t REPOS < <("$PY" -c "import json;print(1)")\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "interpreter")


# ------------------------------------------------------------- dead-gate (HIGH: contract-lint.py)


def test_gate_with_no_call_site_is_flagged(tmp_path: Path):
    """A file claiming 'called before every worker launch' with no caller is prose, not a gate."""
    (tmp_path / "contract-lint.py").write_text(
        '"""contract-lint.py — deterministic dispatch gate.\n'
        "A contract may NOT be dispatched if it carries an unresolved assumption.\n"
        'Exit 0 = clean to dispatch; non-zero = BLOCK. Called before every worker launch.\n"""\n'
        "import sys\n",
        encoding="utf-8",
    )
    (tmp_path / "worker-wrapper.ps1").write_text(
        "param([string]$TaskId)\n$psi.Arguments = '/c claude -p'\n", encoding="utf-8"
    )
    findings = _checks(run(tmp_path), "dead-gate")
    assert findings, "gate missed the never-invoked dispatch gate"
    assert "no call site" in findings[0].message


def test_gate_with_call_site_is_clean(tmp_path: Path):
    """Once wired into the dispatch path, the same file must stop being flagged."""
    (tmp_path / "contract-lint.py").write_text(
        '"""contract-lint.py — deterministic dispatch gate.\n'
        'Exit 0 = clean to dispatch; non-zero = BLOCK. Called before every worker launch.\n"""\n',
        encoding="utf-8",
    )
    (tmp_path / "worker-wrapper.ps1").write_text(
        "param([string]$TaskId)\n"
        "& python contract-lint.py $ContractPath\n"
        'if ($LASTEXITCODE -ne 0) { exit 7 }\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "dead-gate")


def test_gate_claim_in_comment_only_file_without_caller(tmp_path: Path):
    """A commented-out reference is not a call site."""
    (tmp_path / "contract-lint.py").write_text(
        '"""deterministic pre-dispatch gate — exit 0 = clean to dispatch."""\n', encoding="utf-8"
    )
    (tmp_path / "keeper-tick.cmd").write_text(
        "@echo off\nrem contract-lint.py should run here one day\n", encoding="utf-8"
    )
    assert _checks(run(tmp_path), "dead-gate"), "a commented mention must not count as wiring"


# --------------------------------------------------------- discarded exit (HIGH: keeper-tick.cmd)


def test_discarded_guard_exit_is_flagged(tmp_path: Path):
    """bus-guard.sh's exit IS the verdict; redirecting it to a log throws the verdict away."""
    (tmp_path / "keeper-tick.cmd").write_text(
        "@echo off\n"
        '"C:\\Program Files\\Git\\usr\\bin\\bash.exe" bus-guard.sh C:/bus >> heartbeats/bus-guard.log 2>&1\n'
        "git pull --quiet\n",
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "discarded")
    assert findings, "gate missed the discarded guard verdict"
    assert "bus-guard.sh" in findings[0].message


def test_checked_guard_exit_is_clean(tmp_path: Path):
    """Testing errorlevel right after the invocation must pass."""
    (tmp_path / "keeper-tick.cmd").write_text(
        "@echo off\n"
        '"C:\\Program Files\\Git\\usr\\bin\\bash.exe" bus-guard.sh C:/bus >> heartbeats/bus-guard.log 2>&1\n'
        "if errorlevel 1 (\n"
        "  echo bus-guard FAILED >> heartbeats/failures.log\n"
        ")\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "discarded")


# --------------------------------------------------- precision: a noisy gate is an ignored gate


def test_worker_scratch_checkouts_are_not_scanned(tmp_path: Path):
    """workspaces/ holds per-task worker checkouts + vendored deps; scanning them buries findings."""
    noisy = tmp_path / "workspaces" / "T-009" / "backend" / "venv" / "site-packages"
    noisy.mkdir(parents=True)
    (noisy / "vendor.sh").write_text(
        '#!/bin/bash\nx=$(python -c "print(1)" 2>/dev/null)\n', encoding="utf-8"
    )
    assert not run(tmp_path), "vendored/worker-scratch files must not be scanned"


def test_unrelated_block_wording_is_not_a_dead_gate(tmp_path: Path):
    """`cryptography`'s block-padding docs must not read as a dispatch gate claim."""
    (tmp_path / "padding.py").write_text(
        '"""Block cipher padding. Data is padded to the block size; a BLOCK is 128 bits."""\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "dead-gate")


def test_caller_outside_the_fleet_dir_counts_as_wiring(tmp_path: Path):
    """preflight-guard.ps1 is invoked from the hub's dispatcher SSOT, not from a fleet script."""
    gate = tmp_path / "preflight-guard.ps1"
    gate.write_text(
        "# preflight-guard.ps1 — deterministic pre-dispatch gate\n"
        "# Exit 0 = OK to dispatch; non-zero = BLOCK.\n",
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "dead-gate"), "unwired gate should flag with no callers"

    skill = tmp_path.parent / "SKILL.md"
    skill.write_text(
        "Run `powershell -File GWD\\preflight-guard.ps1 -ContractPath <c>` before dispatch.\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path, extra_callers=[skill]), "dead-gate"), (
        "a real external call site must clear the dead-gate finding"
    )


# ------------------------------------------------------------------------------------- CLI shape


def test_cli_exits_nonzero_on_findings(tmp_path: Path):
    (tmp_path / "break-detect.sh").write_text(
        "#!/bin/bash\n"
        'seen=$(grep -c "^x$" f 2>/dev/null || echo 0)\n'
        'if [ "$seen" -lt 1 ]; then echo first; fi\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path)], capture_output=True, text=True
    )
    assert proc.returncode == 1
    assert "grep-count" in proc.stdout


def test_cli_exits_zero_when_clean(tmp_path: Path):
    (tmp_path / "ok.sh").write_text("#!/bin/bash\necho fine\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path)], capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "clean" in proc.stdout


def test_cli_missing_path_is_loud(tmp_path: Path):
    proc = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path / "nope")], capture_output=True, text=True
    )
    assert proc.returncode == 2
    assert "not found" in proc.stderr


# ------------------------------------------------- regression: the gate must fire on the REAL fleet


def test_real_fleet_has_no_silent_failure_findings():
    """The live fleet must stay clean of all four audited shapes.

    History: T-015 fixed grep-count + interpreter in break-detect.sh; T-020 fixed the last two
    (contract-lint.py dead-gate — wired into /get-work-done SKILL.md STEP 6.2; keeper-tick.cmd
    discarded exits — both guards' errorlevel now tested). This assertion is the ratchet: it was
    previously written to assert the defects were PRESENT, which meant the suite would have gone
    red the moment they were fixed. Direction matters — a regression test must fail on the
    DEFECT, never on the FIX.
    """
    fleet = Path("C:/Abhay/GetWorkDone")
    if not fleet.exists():
        pytest.skip("fleet checkout not present on this host")
    findings = run(fleet, extra_callers=[_DISPATCHER_SKILL])
    assert not findings, "silent-failure defects present on the live fleet:\n" + "\n".join(
        f"{f.path.name}:{f.line}: [{f.check}] {f.message}" for f in findings
    )


def test_keeper_tick_checks_both_guard_exit_codes():
    """Regression: every guard invocation in keeper-tick.cmd is followed by an errorlevel test."""
    tick = Path("C:/Abhay/GetWorkDone/keeper-tick.cmd")
    if not tick.exists():
        pytest.skip("fleet checkout not present on this host")
    lines = tick.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        if ".sh" not in line or "bash.exe" not in line:
            continue
        following = "\n".join(lines[i + 1 : i + 4]).lower()
        assert "errorlevel" in following, (
            f"keeper-tick.cmd:{i + 1} runs a guard but never tests its exit code:\n  {line.strip()}"
        )


def test_contract_lint_is_wired_into_the_dispatch_path():
    """Regression: the dispatcher must actually invoke contract-lint.py before launching a worker."""
    body = _DISPATCHER_SKILL.read_text(encoding="utf-8")
    assert "contract-lint.py" in body, (
        "contract-lint.py has no call site in the dispatcher — the gate is prose again"
    )
    step6 = body.split("## STEP 6")[1].split("## STEP 7")[0]
    assert "contract-lint.py" in step6, "contract-lint must be invoked in STEP 6 (the dispatch path)"
