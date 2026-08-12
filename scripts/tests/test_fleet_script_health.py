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

from scripts.check_fleet_script_health import _is_pattern_source, run

CHECKER = Path(__file__).resolve().parents[1] / "check_fleet_script_health.py"
# The dispatcher lives in the hub, outside the fleet dir, but is contract-lint.py's real caller.
_DISPATCHER_SKILL = (
    Path(__file__).resolve().parents[2] / ".claude" / "skills" / "get-work-done" / "SKILL.md"
)


def _checks(findings, name):
    return [f for f in findings if f.check == name]


# Each check gates on file suffix, so the two fixtures must carry the right extension.
_FIXTURE_SUFFIX = {
    "ps-unchecked-call": "sweep.ps1",
    "offset-before-write": "read-answers.ps1",
    "unchecked-precondition": "worker-wrapper.ps1",
}


def defective_name(check: str) -> str:
    return _FIXTURE_SUFFIX[check]


def _only_the_defect(tmp_path: Path, check: str, defective: str, fixed: str):
    """Assert the check fires on `defective` and NOT on `fixed` — in ONE run, as a positive control.

    A bare `assert not _checks(...)` on a fixed-form fixture is VACUOUS: it passes against a
    deleted/neutered check, so it proves nothing about the fix. (Verified during T-071 review: all
    six clean-side tests passed with the three new checks stubbed to `return []`.) Planting both
    forms and asserting EXACTLY ONE finding, anchored to the defective file, makes the negative
    half meaningful — a no-op implementation now fails the same assertion.
    """
    (tmp_path / f"bad_{defective_name(check)}").write_text(defective, encoding="utf-8")
    (tmp_path / f"good_{defective_name(check)}").write_text(fixed, encoding="utf-8")
    found = _checks(run(tmp_path), check)
    assert len(found) == 1, (
        f"expected exactly 1 {check} finding (the defective form only), got "
        f"{[(f.path.name, f.line) for f in found]} — a no-op check yields 0, an over-firing one >1"
    )
    assert found[0].path.name.startswith("bad_"), (
        f"{check} fired on the FIXED form ({found[0].path.name}) — the check cannot tell them apart"
    )
    return found[0]


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


# ------------------------------- ps-unchecked-call (HIGH 2026-08-10: notify-owner.ps1's callers)


def test_ps_unchecked_script_call_is_flagged(tmp_path: Path):
    """`& notify-owner.ps1` with no $LASTEXITCODE test reports success for a failed delivery."""
    (tmp_path / "feature-adoption-sweep.ps1").write_text(
        '$ErrorActionPreference = "Stop"\n'
        "Get-Date -Format o | Set-Content -Path $marker -Encoding ascii\n"
        '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId $taskId -Body $body\n'
        'Write-Output "SWEEP-OK"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "ps-unchecked-call")
    assert findings, "gate missed the unchecked PowerShell delegate call"
    assert "notify-owner.ps1" in findings[0].message


def test_ps_call_with_lastexitcode_tested_is_clean(tmp_path: Path):
    """Testing $LASTEXITCODE right after the call is the fix — POSITIVE CONTROL.

    Both forms are planted in one run and exactly one finding must come back, from the defective
    file. A neutered check returns 0 findings and fails here, so this negative assertion is real.
    """
    _only_the_defect(
        tmp_path,
        "ps-unchecked-call",
        defective=(
            '$ErrorActionPreference = "Stop"\n'
            '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId $taskId -Body $body\n'
            'Write-Output "SWEEP-OK"\n'
        ),
        fixed=(
            '$ErrorActionPreference = "Stop"\n'
            '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId $taskId -Body $body\n'
            "if ($LASTEXITCODE -ne 0) {\n"
            '  Write-Output "DELIVERY FAILED - retry tomorrow"; Set-RetryTomorrow; exit 1\n'
            "}\n"
            'Write-Output "SWEEP-OK"\n'
        ),
    )


def test_unrelated_try_block_does_not_clear_an_unchecked_call(tmp_path: Path):
    """A try/catch 30 lines away must NOT excuse the delivery call.

    feature-adoption-sweep.ps1 really does wrap its Push-Location/claude -p in a try/finally far
    above the notify-owner call; a whole-file search for `try {` reported the file clean while the
    delivery verdict was still discarded. Prose-at-a-distance is not enforcement.
    """
    (tmp_path / "sweep.ps1").write_text(
        '$ErrorActionPreference = "Stop"\n'
        "Push-Location $HubPath\n"
        "try {\n"
        "  Get-Content $promptFile | claude -p --output-format json | Set-Content $resultFile\n"
        "} finally { Pop-Location }\n"
        "\n\n\n\n\n"
        '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId $taskId -Body $body\n'
        'Write-Output "SWEEP-OK"\n',
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "ps-unchecked-call"), (
        "a distant unrelated try/catch must not clear the unchecked-call finding"
    )


def test_ps_output_capturing_call_is_not_flagged(tmp_path: Path):
    """`$x = & script.ps1` CONSUMES the output — a deliberate shape. POSITIVE-CONTROL precision guard."""
    _only_the_defect(
        tmp_path,
        "ps-unchecked-call",
        defective='& (Join-Path $StateRoot "notify-owner.ps1") -Body $body\n',
        fixed=(
            '$result = & (Join-Path $StateRoot "list-things.ps1")\n'
            "Write-Output $result\n"
        ),
    )


def test_ps_exit_code_semantics_are_real_not_theoretical(tmp_path: Path):
    """Ground truth: $ErrorActionPreference='Stop' really does NOT trap a called script's exit.

    This is the whole premise of the finding — if PowerShell DID throw here, the live scripts
    would already be safe and the gate would be noise.
    """
    if sys.platform != "win32":
        pytest.skip("PowerShell exit-code semantics probe is Windows-only")
    child = tmp_path / "child.ps1"
    child.write_text('Write-Output "child ran"\nexit 3\n', encoding="utf-8")
    parent = tmp_path / "parent.ps1"
    parent.write_text(
        '$ErrorActionPreference = "Stop"\n'
        f'& "{child}"\n'
        'Write-Output "PARENT CONTINUED"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(parent)],
        capture_output=True,
        text=True,
    )
    assert "PARENT CONTINUED" in proc.stdout, (
        "premise broken: PowerShell trapped the child's exit — re-examine the finding"
    )
    assert proc.returncode == 0, "the caller reports success despite the child failing"


# ----------------------------- offset-before-write (HIGH 2026-08-10: read-answers.ps1, bus-relay)


def test_offset_advanced_before_payload_write_is_flagged(tmp_path: Path):
    """Committing the getUpdates cursor before writing the answers risks unrecoverable loss."""
    (tmp_path / "read-answers.ps1").write_text(
        '$resp = Invoke-RestMethod -Uri "https://api.telegram.org/bot$bot/getUpdates?offset=$offset"\n'
        "foreach ($u in $resp.result) { $maxUpdate = $u.update_id + 1 }\n"
        "Set-Content -Path $OffsetFile -Value $maxUpdate -Encoding ascii\n"
        "if ($applied -gt 0) { Set-Content -Path $Questions -Value $q -Encoding utf8 }\n",
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "offset-before-write")
    assert findings, "gate missed the offset-committed-before-payload ordering"
    assert "commit point" in findings[0].message


def test_offset_advanced_after_payload_write_is_clean(tmp_path: Path):
    """Payload first, offset second, is the fix — POSITIVE CONTROL (see _only_the_defect)."""
    header = (
        '$resp = Invoke-RestMethod -Uri "https://api.telegram.org/bot$bot/getUpdates?offset=$offset"\n'
        "foreach ($u in $resp.result) { $maxUpdate = $u.update_id + 1 }\n"
    )
    offset_write = "Set-Content -Path $OffsetFile -Value $maxUpdate -Encoding ascii\n"
    payload_write = "if ($applied -gt 0) { Set-Content -Path $Questions -Value $q -Encoding utf8 }\n"
    _only_the_defect(
        tmp_path,
        "offset-before-write",
        defective=header + offset_write + payload_write,
        fixed=header + payload_write + offset_write,
    )


def test_offset_defect_in_the_python_relay_leg_is_flagged(tmp_path: Path):
    """bus-relay.sh carries the same ordering in Python — the check must not be PowerShell-only."""
    (tmp_path / "bus-relay.sh").write_text(
        "#!/bin/bash\n"
        'RESP=$(curl -s "https://api.telegram.org/bot$BOT/getUpdates?offset=$OFF")\n'
        "python3 - \"$RESP\" << 'PYEOF'\n"
        "for u in d.get('result',[]):\n"
        "    mx=max(mx,u['update_id']+1)\n"
        "if mx: open('heartbeats/.tg-offset','w').write(str(mx))\n"
        "if applied: open(qf,'w').write(q)\n"
        "PYEOF\n",
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "offset-before-write")


def test_non_offset_script_is_not_flagged(tmp_path: Path):
    """Ordinary writes with no update cursor are not this defect — POSITIVE-CONTROL precision guard."""
    _only_the_defect(
        tmp_path,
        "offset-before-write",
        defective=(
            '$resp = Invoke-RestMethod -Uri "https://api.telegram.org/bot$b/getUpdates?offset=$o"\n'
            "Set-Content -Path $OffsetFile -Value $maxUpdate\n"
            "Set-Content -Path $Questions -Value $q\n"
        ),
        fixed="Set-Content -Path $LogFile -Value $line\nSet-Content -Path $Questions -Value $q\n",
    )


# ------------------------------ unchecked-precondition (HIGH 2026-08-10: worker-wrapper.ps1)


def test_unchecked_precondition_call_is_flagged(tmp_path: Path):
    """A trust step whose failure cannot stop the launch is not a precondition."""
    (tmp_path / "worker-wrapper.ps1").write_text(
        '$trustScript = Join-Path $StateRoot "trust-workspace.py"\n'
        "if (Test-Path $trustScript) {\n"
        "  python $trustScript $RepoPath\n"
        "}\n"
        "$psi = New-Object System.Diagnostics.ProcessStartInfo\n"
        '$psi.Arguments = "/c claude -p --model $Model --output-format json"\n'
        "$proc = [System.Diagnostics.Process]::Start($psi)\n",
        encoding="utf-8",
    )
    findings = _checks(run(tmp_path), "unchecked-precondition")
    assert findings, "gate missed the unchecked launch precondition"
    assert "LAUNCH PRECONDITION" in findings[0].message


def test_checked_precondition_is_clean(tmp_path: Path):
    """Testing the precondition's exit code aborts the launch — POSITIVE CONTROL."""
    head = '$trustScript = Join-Path $StateRoot "trust-workspace.py"\nif (Test-Path $trustScript) {\n'
    call = "  python $trustScript $RepoPath\n"
    guard = "  if ($LASTEXITCODE -ne 0) { Write-Error 'trust failed'; exit 9 }\n"
    tail = (
        "}\n"
        "$psi = New-Object System.Diagnostics.ProcessStartInfo\n"
        "$proc = [System.Diagnostics.Process]::Start($psi)\n"
    )
    _only_the_defect(
        tmp_path,
        "unchecked-precondition",
        defective=head + call + tail,
        fixed=head + call + guard + tail,
    )


def test_precondition_named_by_literal_is_also_flagged(tmp_path: Path):
    """The literal spelling (`python trust-workspace.py`) is covered as well as the variable one."""
    (tmp_path / "launcher.sh").write_text(
        "#!/bin/bash\n"
        "python trust-workspace.py \"$REPO\"\n"
        "claude -p --output-format json < prompt.txt\n",
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "unchecked-precondition")


def test_precondition_without_a_launch_is_not_flagged(tmp_path: Path):
    """A trust helper that launches nothing is not this defect — POSITIVE-CONTROL precision guard."""
    _only_the_defect(
        tmp_path,
        "unchecked-precondition",
        defective=(
            "python trust-workspace.py $RepoPath\n"
            "$proc = [System.Diagnostics.Process]::Start($psi)\n"
        ),
        fixed='python trust-workspace.py $RepoPath\nWrite-Output "workspace pre-trusted"\n',
    )


# --------------------------------------------------- precision: a noisy gate is an ignored gate


def test_worker_scratch_checkouts_are_not_scanned(tmp_path: Path):
    """workspaces/ holds per-task worker checkouts + vendored deps; scanning them buries findings."""
    noisy = tmp_path / "workspaces" / "T-009" / "backend" / "venv" / "site-packages"
    noisy.mkdir(parents=True)
    (noisy / "vendor.sh").write_text(
        '#!/bin/bash\nx=$(python -c "print(1)" 2>/dev/null)\n', encoding="utf-8"
    )
    assert not run(tmp_path), "vendored/worker-scratch files must not be scanned"


def test_the_gate_does_not_flag_its_own_pattern_source():
    """Pointed at scripts/, the checker must not report ITSELF or its fixtures as defective.

    The offset-before-write patterns necessarily contain the very strings they hunt for, and the
    self-tests plant the defect verbatim — so a naive scan flagged both files. A gate whose first
    output is two false positives about itself is a gate nobody reads.
    """
    # Assert the exclusion RESOLVES to the real files. The first version of this test compared
    # against Path(__file__) directly, which passed while the checker's derived filename was
    # wrong (test_check_fleet_script_health.py) — a test that cannot fail on the bug it guards.
    assert _is_pattern_source(CHECKER), "the checker must exclude itself"
    assert _is_pattern_source(Path(__file__)), (
        "the checker must exclude THIS test file by its real name, not a derived guess"
    )
    findings = run(CHECKER.parent)
    noise = [f for f in findings if f.path.resolve() in {CHECKER.resolve(), Path(__file__).resolve()}]
    assert not noise, "the gate flagged its own pattern source:\n" + "\n".join(
        f"{f.path.name}:{f.line}: [{f.check}]" for f in noise
    )


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
# T-071 (2026-08-10) ratcheted six known-open findings here. All six stopped reproducing by
# 2026-08-12 (fleet-script fixes landed via the estate/parity work: worker-wrapper stdin
# regression rewrite, read-answers/feature-adoption-sweep path+default hardening, and the
# T-110 janitor sweep touching the same guard shapes) — the ratchet's own staleness assertion
# ordered their removal. Ratchet is now EMPTY: any finding the detector reports is a failure.
KNOWN_OPEN_FLEET_FINDINGS: set = set()


def test_real_fleet_has_no_unknown_silent_failure_findings():
    """The live fleet must carry no silent-failure shape beyond the known-open ratchet floor.

    History: T-015 fixed grep-count + interpreter in break-detect.sh; T-020 fixed the last two
    (contract-lint.py dead-gate — wired into /get-work-done SKILL.md STEP 6.2; keeper-tick.cmd
    discarded exits — both guards' errorlevel now tested). This assertion is the ratchet: it was
    previously written to assert the defects were PRESENT, which meant the suite would have gone
    red the moment they were fixed. Direction matters — a regression test must fail on the
    DEFECT, never on the FIX. T-027 (2026-07-27) added the next two: keeper-tick.cmd's result
    guard now asserts `is_error:false` (not just the JSON shape), and its bus push now tests its
    own exit code. T-039 (2026-08-03) added stale-receipt + unchecked-read; the fleet repo has
    since landed BOTH fixes (cost-rollup.py keys on receipt mtime and rewrites superseded rows;
    checkpoint-pr-merge.sh captures repos_rc and aborts loudly on an empty registry), so T-071
    removed them from the floor. T-071 (2026-08-10) added the three HIGHs it found.
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
