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


# ------------------------------------------------- shape-only (HIGH 2026-07-27: keeper-tick.cmd)


def test_shape_only_result_guard_is_flagged(tmp_path: Path):
    """Asserting `"type":"result"` without asserting the OUTCOME passes a failed sweep as healthy."""
    (tmp_path / "keeper-tick.cmd").write_text(
        "@echo off\n"
        "claude -p --output-format json \"/sweep\" > heartbeats\\keeper-last.json 2>&1\n"
        "set GUARD_FAIL=0\n"
        'findstr /b /c:"{" heartbeats\\keeper-last.json >nul\n'
        "if errorlevel 1 set GUARD_FAIL=1\n"
        'findstr /c:"\\"type\\":\\"result\\"" heartbeats\\keeper-last.json >nul\n'
        "if errorlevel 1 set GUARD_FAIL=1\n",
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "shape-only")
    assert findings, "gate missed the shape-without-outcome result guard"
    assert "is_error" in findings[0].message


def test_outcome_checked_result_guard_is_clean(tmp_path: Path):
    """Adding the `is_error:false` assertion must silence the finding."""
    (tmp_path / "keeper-tick.cmd").write_text(
        "@echo off\n"
        "claude -p --output-format json \"/sweep\" > heartbeats\\keeper-last.json 2>&1\n"
        'findstr /c:"\\"type\\":\\"result\\"" heartbeats\\keeper-last.json >nul\n'
        "if errorlevel 1 set GUARD_FAIL=1\n"
        'findstr /c:"\\"is_error\\":false" heartbeats\\keeper-last.json >nul\n'
        "if errorlevel 1 set GUARD_FAIL=1\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "shape-only")


def test_outcome_mentioned_only_in_a_comment_still_flags(tmp_path: Path):
    """A `rem` narrating a past is_error fix is prose — it must not clear a live finding.

    keeper-tick.cmd really does carry such a comment, so a naive whole-file search for `is_error`
    reported the file clean while the code checked only the shape. Prose is not enforcement.
    """
    (tmp_path / "keeper-tick.cmd").write_text(
        "@echo off\n"
        "claude -p --output-format json \"/sweep\" > heartbeats\\keeper-last.json 2>&1\n"
        "rem NOTE: claude -p keys \"is_error\" first, so an old subtype anchor false-positived.\n"
        'findstr /c:"\\"type\\":\\"result\\"" heartbeats\\keeper-last.json >nul\n'
        "if errorlevel 1 set GUARD_FAIL=1\n",
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "shape-only"), "a comment mentioning is_error must not count"


def test_error_max_turns_payload_defeats_a_shape_only_guard():
    """Ground truth: T-015's REAL failed-run JSON satisfies both shape markers.

    This is the defect's proof-of-harm — the previous occurrence of this very fleet audit died on
    error_max_turns and its output was recorded as a healthy tick.
    """
    payload = (
        '{"type":"result","subtype":"error_max_turns","is_error":true,"num_turns":41}'
    )
    assert payload.startswith("{")
    assert '"type":"result"' in payload
    assert '"is_error":false' not in payload, (
        "the outcome assertion is what separates a failed run from a healthy one"
    )


# -------------------------------------------------- silent-push (HIGH 2026-07-27: keeper-tick.cmd)


def test_silent_push_redirect_is_flagged(tmp_path: Path):
    """`git push ... >nul 2>&1` discards the verdict exactly like `|| true` does."""
    (tmp_path / "keeper-tick.cmd").write_text(
        "@echo off\ngit add -A >nul 2>&1\ngit push --quiet origin main >nul 2>&1\n",
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "silent-push")
    assert findings, "gate missed the redirect spelling of the discarded-push verdict"
    assert "rejected" in findings[0].message


def test_silent_push_or_true_is_flagged(tmp_path: Path):
    """The original `|| true` spelling stays covered."""
    (tmp_path / "writer.sh").write_text(
        "#!/bin/bash\ngit push origin main || true\n", encoding="utf-8"
    )
    assert _checks(run(tmp_path), "silent-push")


def test_push_with_errorlevel_test_is_clean(tmp_path: Path):
    """Testing the exit code on the following line must clear the finding."""
    (tmp_path / "keeper-tick.cmd").write_text(
        "@echo off\n"
        "git push --quiet origin main >nul 2>&1\n"
        "if errorlevel 1 (\n"
        "  echo push FAILED >> heartbeats\\keeper-tick-failures.log\n"
        ")\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "silent-push")


def test_push_via_bus_push_helper_is_clean(tmp_path: Path):
    """The safe helper is the sanctioned form and must never be flagged."""
    (tmp_path / "bus-relay.sh").write_text(
        "#!/bin/bash\ngit commit -q -m x 2>/dev/null && bus_push\n", encoding="utf-8"
    )
    assert not _checks(run(tmp_path), "silent-push")


# ------------------------------------------------ stale-receipt (HIGH 2026-08-03: cost-rollup.py)


def _ledger_script(body: str) -> str:
    """A minimal roll-up over per-task result.json receipts appending to costs.jsonl."""
    return (
        "import glob, json, os, re\n"
        "LEDGER = 'costs.jsonl'\n"
        "def load_seen():\n"
        "    seen = set()\n"
        "    for line in open(LEDGER):\n"
        "        seen.add(json.loads(line)['task'])\n"
        "    return seen\n"
        "def rollup():\n"
        "    seen = load_seen()\n"
        "    for path in sorted(glob.glob('heartbeats/*.result.json')):\n"
        "        task = re.sub(r'\\.result\\.json$', '', os.path.basename(path))\n" + body
    )


def test_stale_receipt_ledger_is_flagged(tmp_path: Path):
    """Dedup on the task id alone lets a REWRITTEN receipt keep its superseded numbers forever."""
    (tmp_path / "cost-rollup.py").write_text(
        _ledger_script(
            "        if task in seen:\n"
            "            continue\n"
            "        data = json.load(open(path))\n"
            "        print(data['modelUsage'])\n"
        ),
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "stale-receipt")
    assert findings, "gate missed the id-keyed ledger over mutable receipts"
    assert "superseded" in findings[0].message


def test_content_keyed_ledger_is_clean(tmp_path: Path):
    """Folding a content digest into the identity makes a rewritten receipt detectable."""
    (tmp_path / "cost-rollup.py").write_text(
        _ledger_script(
            "        data = json.load(open(path))\n"
            "        import hashlib\n"
            "        digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()\n"
            "        if task in seen and seen[task] == digest:\n"
            "            continue\n"
            "        print(data['modelUsage'], digest)\n"
        ),
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "stale-receipt")


def test_mtime_reconciled_ledger_is_clean(tmp_path: Path):
    """Comparing the receipt's mtime against the recorded one is an equally valid fix."""
    (tmp_path / "cost-rollup.py").write_text(
        _ledger_script(
            "        if task in seen and os.path.getmtime(path) == seen[task]:\n"
            "            continue\n"
            "        data = json.load(open(path))\n"
            "        print(data['modelUsage'])\n"
        ),
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "stale-receipt")


def test_non_receipt_seen_set_is_not_flagged(tmp_path: Path):
    """A dedup set over IMMUTABLE inputs is not this defect — precision guard."""
    (tmp_path / "dedupe.py").write_text(
        "import json\n"
        "seen = set()\n"
        "for line in open('urls.txt'):\n"
        "    if line in seen:\n"
        "        continue\n"
        "    seen.add(line)\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "stale-receipt")


def test_rewritten_receipt_defect_is_real_not_theoretical():
    """Ground truth from the live fleet: T-037's ledger row contradicts its own receipt.

    costs.jsonl records T-037 as sonnet/109,494 tok/$1.9766 — byte-identical to the row for
    T-037.2nd-attempt-error_max_turns — while heartbeats/T-037.result.json is an opus run of
    119,515 tok/$4.1413. The roll-up saw the retry's content first, banked the task id, and never
    re-read the file after it was overwritten with the real run.
    """
    import json as _json

    ledger = Path("C:/Abhay/GetWorkDone/costs.jsonl")
    receipt = Path("C:/Abhay/GetWorkDone/heartbeats/T-037.result.json")
    if not ledger.exists() or not receipt.exists():
        pytest.skip("fleet checkout not present on this host")
    rows = [
        _json.loads(l)
        for l in ledger.read_text(encoding="utf-8").splitlines()
        if l.strip() and _json.loads(l).get("task") == "T-037"
    ]
    if not rows:
        pytest.skip("T-037 no longer in the ledger")
    usage = _json.loads(receipt.read_text(encoding="utf-8")).get("modelUsage") or {}
    if not usage:
        pytest.skip("receipt carries no modelUsage")
    truth = sum(
        u.get("inputTokens", 0) + u.get("outputTokens", 0) + u.get("cacheCreationInputTokens", 0)
        for u in usage.values()
    )
    assert rows[0]["total_tokens"] != truth, (
        "the live divergence this gate exists for has been reconciled — if the ledger was "
        "repaired, keep the gate but retire this ground-truth assertion"
    )


# -------------------------------------- unchecked-read (HIGH 2026-08-03: checkpoint-pr-merge.sh)


def test_unchecked_registry_read_is_flagged(tmp_path: Path):
    """A python registry read with no rc capture turns "no interpreter" into "nothing to do"."""
    (tmp_path / "checkpoint-pr-merge.sh").write_text(
        "#!/bin/bash\n"
        'repos=$(python -c "\n'
        "import json\n"
        "print('a/b')\n"
        '")\n'
        "while IFS= read -r nwo; do\n"
        '  [ -z "$nwo" ] && continue\n'
        '  echo "$nwo"\n'
        'done <<< "$repos"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "unchecked-read")
    assert findings, "gate missed the unguarded registry read feeding an empty loop"
    assert "indistinguishable" in findings[0].message


def test_registry_read_with_rc_capture_is_clean(tmp_path: Path):
    """Capturing the exit code and failing loudly on an empty registry must pass."""
    (tmp_path / "checkpoint-pr-merge.sh").write_text(
        "#!/bin/bash\n"
        'repos=$(python -c "print(1)"); repos_rc=$?\n'
        "if [ $repos_rc -ne 0 ]; then\n"
        '  echo "registry read FAILED — not a clean sweep" >&2; exit 4\n'
        "fi\n"
        "while IFS= read -r nwo; do\n"
        '  echo "$nwo"\n'
        'done <<< "$repos"\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "unchecked-read")


def test_registry_read_with_loud_empty_test_is_clean(tmp_path: Path):
    """An explicit loud emptiness test is an equally valid fix for the same class."""
    (tmp_path / "checkpoint-pr-merge.sh").write_text(
        "#!/bin/bash\n"
        'repos=$(python -c "print(1)")\n'
        '[ -z "$repos" ] && { echo "registry empty — FATAL, not a clean sweep" >&2; exit 4; }\n'
        "while IFS= read -r nwo; do\n"
        '  echo "$nwo"\n'
        'done <<< "$repos"\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "unchecked-read")


def test_read_not_feeding_a_loop_is_not_flagged(tmp_path: Path):
    """A one-off value read is not the "iterated over nothing" shape — precision guard."""
    (tmp_path / "helper.sh").write_text(
        "#!/bin/bash\n"
        'ignore=$(python -c "print(1)")\n'
        'for f in a b; do echo "$f $ignore"; done\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "unchecked-read")


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


# The two defects the 2026-08-03 audit CONFIRMED live on the fleet. Fixing them is a fleet-repo
# change (out of scope for this hub PR, which delivers the gates); until then they are the known
# ratchet floor. RULE: this set may only SHRINK. Adding to it is how a gate rots into a to-do list.
KNOWN_OPEN_FLEET_FINDINGS = {
    ("cost-rollup.py", "stale-receipt"),
    ("checkpoint-pr-merge.sh", "unchecked-read"),
}


def test_real_fleet_has_no_unknown_silent_failure_findings():
    """The live fleet must carry no silent-failure shape beyond the known-open ratchet floor.

    History: T-015 fixed grep-count + interpreter in break-detect.sh; T-020 fixed the last two
    (contract-lint.py dead-gate — wired into /get-work-done SKILL.md STEP 6.2; keeper-tick.cmd
    discarded exits — both guards' errorlevel now tested). This assertion is the ratchet: it was
    previously written to assert the defects were PRESENT, which meant the suite would have gone
    red the moment they were fixed. Direction matters — a regression test must fail on the
    DEFECT, never on the FIX. T-027 (2026-07-27) added the next two: keeper-tick.cmd's result
    guard now asserts `is_error:false` (not just the JSON shape), and its bus push now tests its
    own exit code. T-039 (2026-08-03) added stale-receipt + unchecked-read; both are confirmed
    live and listed above until the fleet repo lands their fixes.
    """
    fleet = Path("C:/Abhay/GetWorkDone")
    if not fleet.exists():
        pytest.skip("fleet checkout not present on this host")
    findings = run(fleet, extra_callers=[_DISPATCHER_SKILL])
    unexpected = [
        f for f in findings if (f.path.name, f.check) not in KNOWN_OPEN_FLEET_FINDINGS
    ]
    assert not unexpected, "NEW silent-failure defects present on the live fleet:\n" + "\n".join(
        f"{f.path.name}:{f.line}: [{f.check}] {f.message}" for f in unexpected
    )


def test_known_open_fleet_findings_still_reproduce():
    """The ratchet floor must be real: each known-open entry still fires, or it should be removed.

    Guards the opposite rot — a stale allowlist that silently excuses defects already fixed.
    """
    fleet = Path("C:/Abhay/GetWorkDone")
    if not fleet.exists():
        pytest.skip("fleet checkout not present on this host")
    seen = {(f.path.name, f.check) for f in run(fleet, extra_callers=[_DISPATCHER_SKILL])}
    stale = KNOWN_OPEN_FLEET_FINDINGS - seen
    assert not stale, (
        f"these known-open findings no longer reproduce — remove them from the ratchet: {stale}"
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


def test_keeper_tick_asserts_sweep_outcome_not_just_shape():
    """Regression (T-027): the tick guard must assert is_error:false, not only the JSON shape."""
    tick = Path("C:/Abhay/GetWorkDone/keeper-tick.cmd")
    if not tick.exists():
        pytest.skip("fleet checkout not present on this host")
    code = "\n".join(
        l
        for l in tick.read_text(encoding="utf-8", errors="replace").splitlines()
        if not l.lstrip().lower().startswith("rem ")
    )
    assert "is_error" in code, (
        "keeper-tick.cmd checks the sweep JSON's shape but not its outcome — an error_max_turns "
        "run (like T-015) emits `type\":\"result\"` too and would score as a healthy tick"
    )


def test_keeper_tick_push_verdict_is_tested():
    """Regression (T-027): every git push in the tick must have its exit code tested."""
    tick = Path("C:/Abhay/GetWorkDone/keeper-tick.cmd")
    if not tick.exists():
        pytest.skip("fleet checkout not present on this host")
    lines = tick.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        # An actual invocation starts the statement; `echo ... git push FAILED ...` is a log
        # message, not a push, and must not be mistaken for one.
        if not line.strip().lower().startswith("git push"):
            continue
        window = "\n".join(lines[i : i + 3]).lower()
        assert "errorlevel" in window or "bus_push" in window, (
            f"keeper-tick.cmd:{i + 1} pushes without testing the verdict — a rejected push is "
            f"indistinguishable from a landed one:\n  {line.strip()}"
        )


def test_contract_lint_is_wired_into_the_dispatch_path():
    """Regression: the dispatcher must actually invoke contract-lint.py before launching a worker."""
    body = _DISPATCHER_SKILL.read_text(encoding="utf-8")
    assert "contract-lint.py" in body, (
        "contract-lint.py has no call site in the dispatcher — the gate is prose again"
    )
    step6 = body.split("## STEP 6")[1].split("## STEP 7")[0]
    assert "contract-lint.py" in step6, "contract-lint must be invoked in STEP 6 (the dispatch path)"
