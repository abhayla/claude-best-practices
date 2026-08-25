"""Self-tests for check_fleet_script_health.py.

Each test plants the EXACT known-bad construct from the 2026-07-20 GetWorkDone fleet audit and
asserts the gate fires on it, then plants the fixed form and asserts the gate goes quiet. A gate
that cannot be shown to fire on the defect it targets is not a gate (learning-to-gate doctrine).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from scripts.check_fleet_script_health import _is_pattern_source, manifest_digest, run

CHECKER = Path(__file__).resolve().parents[1] / "check_fleet_script_health.py"
# The dispatcher lives in the hub, outside the fleet dir, but is contract-lint.py's real caller.
_DISPATCHER_SKILL = (
    Path(__file__).resolve().parents[2] / ".claude" / "skills" / "get-work-done" / "SKILL.md"
)

# ------------------------------------------------------- T-208: locate the real fleet bus, not a stub
#
# Both fleet-gated ratchet tests used to hard-code `Path("C:/Abhay/GetWorkDone").exists()`. On the
# dev PC that path EXISTS but is a stray stub left over from 2026-07-30 (one empty heartbeats/
# dir, no settings.json, no queue/) — the real bus on that machine is D:\Abhay\GetWorkDone. A bare
# existence check cannot tell "I could not look" from "there is nothing to find", so every
# fleet-gated assertion silently scanned the stub, found zero findings, and reported all 11
# known-open ratchet entries as fixed (2026-08-19). `_resolve_fleet_dir` requires the marker only
# the real bus carries — settings.json with a `repo_registry` key, plus a queue/ directory — and
# tries known per-machine locations (an explicit env override first) instead of one hard-coded
# path. A candidate that exists but fails the marker check is rejected LOUDLY via a pytest
# warning, never silently folded into "absent".
_FLEET_ENV_VAR = "GETWORKDONE_FLEET_DIR"
_FLEET_MARKER_FILE = "settings.json"
_FLEET_MARKER_KEY = "repo_registry"
_FLEET_CANDIDATE_DIRS = (Path("D:/Abhay/GetWorkDone"), Path("C:/Abhay/GetWorkDone"))


def _is_real_fleet_dir(path: Path) -> bool:
    """True only for a directory carrying the bus markers — never for a merely-existing path."""
    settings = path / _FLEET_MARKER_FILE
    if not settings.is_file() or not (path / "queue").is_dir():
        return False
    try:
        doc = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(doc, dict) and _FLEET_MARKER_KEY in doc


def _resolve_fleet_dir() -> Path | None:
    """Return the live fleet bus directory, or None if genuinely absent on this host.

    Order: `GETWORKDONE_FLEET_DIR` env override (if set, it is the ONLY candidate — an explicit
    override that fails the marker check is a misconfiguration, not a fallthrough), then the
    known per-machine locations, first match wins. A candidate that exists but is not the real
    bus is reported via `warnings.warn` so pytest surfaces it instead of a silent skip.
    """
    override = os.environ.get(_FLEET_ENV_VAR)
    candidates = [Path(override)] if override else list(_FLEET_CANDIDATE_DIRS)
    for candidate in candidates:
        if not candidate.exists():
            continue
        if _is_real_fleet_dir(candidate):
            return candidate
        warnings.warn(
            f"T-208: rejected fleet candidate {candidate} — it exists but carries none of the "
            f"real bus's markers ({_FLEET_MARKER_FILE} with a '{_FLEET_MARKER_KEY}' key, plus a "
            "queue/ dir); treating it as ABSENT rather than silently scanning a stub",
            stacklevel=2,
        )
    return None


def _checks(findings, name):
    return [f for f in findings if f.check == name]


# Each check gates on file suffix, so the two fixtures must carry the right extension.
_FIXTURE_SUFFIX = {
    "ps-unchecked-call": "sweep.ps1",
    "offset-before-write": "read-answers.ps1",
    "unchecked-precondition": "worker-wrapper.ps1",
    "unlocked-global-rewrite": "rollup.py",
    "unmeasured-safe-delete": "janitor.ps1",
    "silent-staging": "tick.cmd",
    "unmeasured-reset": "bus-sync.sh",
    "clobbered-exit": "worker-wrapper-autosave.ps1",
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


# ------------------- ps-unchecked-call window (T-204: backtick-continued multi-line calls) -------
#
# The window used to look for a $LASTEXITCODE/try-catch guard was measured from the line the call
# STARTS on. A PowerShell call spread over several backtick-continued lines (named args one per
# line is routine style) can put its guard outside that window even though the guard is right
# after the call — flagging correct code. The four cases below are the full combination matrix:
# single-line/continued x guarded/unguarded. Each must produce the RIGHT verdict on its own, and
# a broken window would either flag test_continued_call_guarded_is_not_flagged (false positive,
# the live T-204 bug) or miss test_continued_call_unguarded_is_flagged (false negative — the check
# going blind is the "must not become blind in the process" DoD line).


def test_single_line_call_guarded_is_not_flagged(tmp_path: Path):
    """Baseline: a single-line call immediately followed by a $LASTEXITCODE test is clean."""
    _only_the_defect(
        tmp_path,
        "ps-unchecked-call",
        defective='& (Join-Path $StateRoot "notify-owner.ps1") -TaskId $taskId -Body $body\n',
        fixed=(
            '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId $taskId -Body $body\n'
            "if ($LASTEXITCODE -ne 0) { exit 1 }\n"
        ),
    )


def test_single_line_call_unguarded_is_flagged(tmp_path: Path):
    """Baseline: a single-line call with no guard anywhere nearby is flagged."""
    (tmp_path / "sweep.ps1").write_text(
        '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId $taskId -Body $body\n'
        'Write-Output "SWEEP-OK"\n',
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "ps-unchecked-call"), "unguarded single-line call must be flagged"


def test_continued_call_guarded_is_not_flagged(tmp_path: Path):
    """THE BUG BEING FIXED: a backtick-continued call guarded right after must NOT be flagged.

    This is the exact live shape from nginx-drift-check-alert.ps1 lines 88-93: the call spans
    5 lines via trailing backticks and $LASTEXITCODE is tested on the line right after the call
    ends. With the window anchored to the call's FIRST line, the guard fell outside it.
    """
    _only_the_defect(
        tmp_path,
        "ps-unchecked-call",
        defective=(
            '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId "x" -Severity "P2" `\n'
            '  -Title "some title" `\n'
            '  -Body ("a very long body string built across " + "several lines") `\n'
            '  -Settings $Settings\n'
        ),
        fixed=(
            '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId "x" -Severity "P2" `\n'
            '  -Title "some title" `\n'
            '  -Body ("a very long body string built across " + "several lines") `\n'
            '  -Settings $Settings\n'
            "if ($LASTEXITCODE -ne 0) {\n"
            '  Write-Output "NOTIFY-FAIL: notify-owner.ps1 exited $LASTEXITCODE"\n'
            "}\n"
        ),
    )


def test_continued_call_unguarded_is_flagged(tmp_path: Path):
    """The fix must NOT go blind: a genuinely unguarded multi-line call still fires."""
    (tmp_path / "sweep.ps1").write_text(
        '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId "x" -Severity "P2" `\n'
        '  -Title "some title" `\n'
        '  -Body ("a very long body string built across " + "several lines") `\n'
        '  -Settings $Settings\n'
        'Write-Output "SWEEP-OK"\n',
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "ps-unchecked-call"), (
        "an unguarded backtick-continued call must still be flagged — the fix must not blind the "
        "check to the defect class it exists to catch"
    )


def test_unclosed_paren_continuation_guarded_is_not_flagged(tmp_path: Path):
    """The OTHER live false positive: continuation via an unclosed paren, no backtick at all.

    nginx-drift-check-alert.ps1 line 104's CANNOT_CHECK call continues its `-Body (... + ...)`
    concatenation across lines 106-109 with no trailing backtick on line 106 — the parens stay
    open, which is itself a PowerShell continuation. A backtick-only fix still anchors the
    window to line 106 (the first non-backtick-terminated line) and misses the guard at 111.
    """
    _only_the_defect(
        tmp_path,
        "ps-unchecked-call",
        defective=(
            '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId "x" -Severity "P3" `\n'
            '  -Title "check is failing" `\n'
            '  -Body ("has failed for $streak " +\n'
            '         "consecutive runs. This does " +\n'
            '         "NOT mean the dependency is broken.") `\n'
            '  -Settings $Settings\n'
        ),
        fixed=(
            '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId "x" -Severity "P3" `\n'
            '  -Title "check is failing" `\n'
            '  -Body ("has failed for $streak " +\n'
            '         "consecutive runs. This does " +\n'
            '         "NOT mean the dependency is broken.") `\n'
            '  -Settings $Settings\n'
            "if ($LASTEXITCODE -ne 0) {\n"
            '  Write-Output "NOTIFY-FAIL"\n'
            "}\n"
        ),
    )


def test_unclosed_paren_continuation_unguarded_is_flagged(tmp_path: Path):
    """The fix must not go blind on the unclosed-paren continuation shape either."""
    (tmp_path / "sweep.ps1").write_text(
        '& (Join-Path $StateRoot "notify-owner.ps1") -TaskId "x" -Severity "P3" `\n'
        '  -Title "check is failing" `\n'
        '  -Body ("has failed for $streak " +\n'
        '         "consecutive runs. This does " +\n'
        '         "NOT mean the dependency is broken.") `\n'
        '  -Settings $Settings\n'
        'Write-Output "SWEEP-OK"\n',
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "ps-unchecked-call"), (
        "an unguarded unclosed-paren-continued call must still be flagged"
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


# --------------------------------------------------- unlocked-global-rewrite (T-167, 2026-08-17)


def test_unlocked_global_rewrite_is_flagged(tmp_path: Path):
    """The live trust-workspace.py shape: read whole shared JSON, mutate, truncate-write it back.

    The fixed form writes a temp file and os.replace()s it in — atomic, so a concurrent reader
    sees the old file or the new one, never a half-written one.
    """
    finding = _only_the_defect(
        tmp_path,
        "unlocked-global-rewrite",
        defective=(
            "import io, json, os\n"
            'claude_json_path = os.path.join(os.environ["USERPROFILE"], ".claude.json")\n'
            "with io.open(claude_json_path, encoding='utf-8') as f:\n"
            "    data = json.load(f)\n"
            'data["projects"][sys.argv[1]] = {"hasTrustDialogAccepted": True}\n'
            'with io.open(claude_json_path, "w", encoding="utf-8") as f:\n'
            "    json.dump(data, f, indent=2)\n"
        ),
        fixed=(
            "import io, json, os\n"
            'claude_json_path = os.path.join(os.environ["USERPROFILE"], ".claude.json")\n'
            "with io.open(claude_json_path, encoding='utf-8') as f:\n"
            "    data = json.load(f)\n"
            'data["projects"][sys.argv[1]] = {"hasTrustDialogAccepted": True}\n'
            'tmp = claude_json_path + ".tmp"\n'
            'with io.open(tmp, "w", encoding="utf-8") as f:\n'
            "    json.dump(data, f, indent=2)\n"
            "os.replace(tmp, claude_json_path)\n"
        ),
    )
    assert "no atomic replace" in finding.message


def test_append_to_shared_ledger_is_not_flagged(tmp_path: Path):
    """Mode "a" cannot erase another writer's bytes — only a truncating rewrite is the defect.

    cost-rollup.py's normal path appends; only its supersede path rewrites. Flagging the append
    would make the check fire on every ledger writer in the fleet and train the reader to ignore it.
    """
    (tmp_path / "appender.py").write_text(
        "import json, os\n"
        'LEDGER = os.path.join(os.path.dirname(__file__), "costs.jsonl")\n'
        'with open(LEDGER, "a", encoding="utf-8") as f:\n'
        '    f.write(json.dumps({"task": "T-1"}) + "\\n")\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "unlocked-global-rewrite")


def test_retry_helper_alone_does_not_clear_the_finding(tmp_path: Path):
    """A retry-on-sharing-violation is NOT a lock — it orders nothing.

    This is the exact trap cost-rollup.py falls into: `open_with_retry` reads as concurrency-aware
    but only retries past a transient lock, so two writers still interleave and lose an update. If
    the presence of that helper cleared the finding, the check would excuse the live defect.
    """
    (tmp_path / "rollup.py").write_text(
        "import json, os, time\n"
        'LEDGER = os.path.join(os.path.dirname(__file__), "costs.jsonl")\n'
        "def open_with_retry(path, mode, encoding='utf-8'):\n"
        "    for attempt in range(5):\n"
        "        try:\n"
        "            return open(path, mode, encoding=encoding)\n"
        "        except OSError:\n"
        "            time.sleep(1)\n"
        'with open_with_retry(LEDGER, "w") as f:\n'
        '    f.write("rewritten\\n")\n',
        encoding="utf-8",
    )
    found = _checks(run(tmp_path), "unlocked-global-rewrite")
    assert len(found) == 1, "a retry helper must not be mistaken for serialisation"


def test_locked_rewrite_is_not_flagged(tmp_path: Path):
    """A real inter-process lock serialises the writers, so the rewrite cannot interleave."""
    (tmp_path / "locked.py").write_text(
        "import json, os, msvcrt\n"
        'LEDGER = os.path.join(os.path.dirname(__file__), "costs.jsonl")\n'
        'with open(LEDGER, "w", encoding="utf-8") as f:\n'
        "    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)\n"
        '    f.write("safe\\n")\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "unlocked-global-rewrite")


def test_local_temp_file_rewrite_is_not_flagged(tmp_path: Path):
    """A truncating write to a script-local scratch path is ordinary, not shared-state corruption."""
    (tmp_path / "scratch.py").write_text(
        "import json\n"
        'out = "/tmp/my-scratch-output.json"\n'
        'with open(out, "w", encoding="utf-8") as f:\n'
        '    json.dump({"ok": True}, f)\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "unlocked-global-rewrite")


# ------------------------------------------------------------ silent-staging (T-167, 2026-08-17)


def test_silent_staging_is_flagged(tmp_path: Path):
    """The live keeper-tick.cmd:161 shape: `git add` into a sink, then a push that reports healthy."""
    finding = _only_the_defect(
        tmp_path,
        "silent-staging",
        defective=(
            # ONE unchecked mutation only: the helper asserts exactly one finding, and `git add`
            # plus `git commit` would (correctly) yield two.
            "git add -A >nul 2>&1\n"
            "git push --quiet origin main >nul 2>&1\n"
            "if errorlevel 1 ( echo PUSH_FAILED )\n"
        ),
        fixed=(
            "git add -A >nul 2>&1\n"
            "if errorlevel 1 ( echo ADD_FAILED & exit /b 1 )\n"
            "git push --quiet origin main >nul 2>&1\n"
            "if errorlevel 1 ( echo PUSH_FAILED )\n"
        ),
    )
    assert "git add" in finding.message


def test_unchecked_checkout_before_push_is_flagged(tmp_path: Path):
    """keeper-tick.cmd:160 — an unredirected `git checkout main` is just as silent when untested.

    A failed checkout leaves the clone on the sweep's stray branch; the tick then commits THERE and
    `git push origin main` pushes the untouched main ref and exits 0. Reproduced end-to-end for
    T-167. The verdict is lost by not being read, not by being redirected — so the check must not
    require a sink.
    """
    (tmp_path / "tick.cmd").write_text(
        "git checkout main --quiet\n"
        "git commit -m tick --quiet >nul 2>&1\n"
        "git push --quiet origin main >nul 2>&1\n",
        encoding="utf-8",
    )
    found = _checks(run(tmp_path), "silent-staging")
    assert any("checkout" in f.message for f in found), (
        "an unredirected but untested `git checkout` before a push must flag"
    )


def test_mutation_in_a_script_that_never_pushes_is_not_flagged(tmp_path: Path):
    """No push means no false 'healthy' report — the defect needs the push to launder the failure."""
    (tmp_path / "local.cmd").write_text(
        "git add -A >nul 2>&1\ngit commit -m local --quiet >nul 2>&1\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "silent-staging")


def test_bus_push_retry_loop_is_not_flagged(tmp_path: Path):
    """bus-sync.sh's bus_push() is the fleet's reference-correct shape and must stay clean.

    Its `git checkout main -q` is untested on its own line, but it sits in a retry loop whose push
    IS tested: a failed checkout fails that iteration's push, and exhaustion returns non-zero
    loudly. Flagging the known-good implementation is how a gate trains its readers to ignore it.
    """
    (tmp_path / "bus-sync.sh").write_text(
        "#!/bin/bash\n"
        "bus_push() {\n"
        "  local i\n"
        "  for i in 1 2 3; do\n"
        "    git checkout main -q 2>/dev/null\n"
        "    git pull -q --rebase origin main 2>/dev/null\n"
        "    if git push -q origin main 2>/dev/null; then return 0; fi\n"
        "    sleep 2\n"
        "  done\n"
        '  echo "BUS-SYNC: push failed after 3 rebase-retries" >&2\n'
        "  return 1\n"
        "}\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "silent-staging")


def test_set_e_shell_does_not_flag_silent_staging(tmp_path: Path):
    """`set -e` aborts on the failed mutation, so the push below never runs — loud, not silent."""
    (tmp_path / "strict.sh").write_text(
        "#!/bin/bash\nset -euo pipefail\ngit add -A\ngit commit -m x\ngit push origin main\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "silent-staging")


# ------------------------------------------------ content-assertion guard (T-207, 2026-08-19 audit)


def test_content_assertion_guard_clears_silent_staging(tmp_path: Path):
    """keeper-tick.cmd's T-207 shape: no errorlevel token anywhere, verdict read from CAPTURED
    output content instead — `for /f` lifts a follow-up query into a flag, an `if` on that flag
    gates the push. This is a DIFFERENT but equally valid way of reading the same verdict and must
    clear exactly like the errorlevel shape does.
    """
    finding = _only_the_defect(
        tmp_path,
        "silent-staging",
        # Captured (not `>nul`) but genuinely never read — the negative control that proves the
        # widened content-assertion window does not blindly clear every non-nul mutation.
        defective=(
            'git checkout main --quiet > "!KT_OUT!" 2>&1\n'
            "git push --quiet origin main >nul 2>&1\n"
            "if errorlevel 1 ( echo PUSH_FAILED )\n"
        ),
        fixed=(
            'git checkout main --quiet > "!KT_OUT!" 2>&1\n'
            'git rev-parse --abbrev-ref HEAD > "!KT_OUT!" 2>nul\n'
            "set KT_HEAD=\n"
            'for /f "usebackq delims=" %%b in ("!KT_OUT!") do set KT_HEAD=%%b\n'
            "set KT_ON_MAIN=0\n"
            'if "!KT_HEAD!"=="main" set KT_ON_MAIN=1\n'
            'if "!KT_ON_MAIN!"=="0" ( echo NOT ON MAIN )\n'
            "git push --quiet origin main >nul 2>&1\n"
            "if errorlevel 1 ( echo PUSH_FAILED )\n"
        ),
    )
    assert "checkout" in finding.message


def test_narration_echo_line_is_not_a_mutation(tmp_path: Path):
    """keeper-tick.cmd:258/272: an `echo ... git commit FAILED ...` narration line contains verb
    text but never executes anything — it must not be counted as a second, unguarded mutation
    alongside the real (and separately guarded) one it is narrating about.
    """
    (tmp_path / "tick.cmd").write_text(
        'git commit -m "keeper: tick" > "!KT_OUT!" 2>&1\n'
        'set KT_COMMIT_OK=0\n'
        'findstr /c:"keeper: tick" "!KT_OUT!" >nul && set KT_COMMIT_OK=1\n'
        'if "!KT_COMMIT_OK!"=="0" (\n'
        "  set KT_ABORT=1\n"
        "  echo %date% %time% keeper-tick: git commit FAILED - tick work NOT committed >> fail.log\n"
        ")\n"
        'if "!KT_ABORT!"=="1" goto skip\n'
        "git push --quiet origin main >nul 2>&1\n"
        "if errorlevel 1 ( echo PUSH_FAILED )\n"
        ":skip\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "silent-staging")


def test_echo_line_with_real_unguarded_mutation_still_flags(tmp_path: Path):
    """The narration exclusion is scoped to lines STARTING with echo — a real, unguarded mutation
    on its own line, elsewhere in the same file, must still fire.
    """
    (tmp_path / "tick.cmd").write_text(
        'git commit -m "keeper: tick" >nul 2>&1\n'
        "echo some unrelated narration\n"
        "git push --quiet origin main >nul 2>&1\n"
        "if errorlevel 1 ( echo PUSH_FAILED )\n",
        encoding="utf-8",
    )
    found = _checks(run(tmp_path), "silent-staging")
    assert any("commit" in f.message for f in found)


# ------------------------------------------- self-test/fixture harness exclusion (2026-08-19 audit)


def test_selftest_harness_with_temp_bare_repo_is_not_flagged(tmp_path: Path):
    """janitor-worktrees.ps1's -SelfTest shape: a throwaway `git init --bare` repo under $env:TEMP,
    mutated and pushed to ONLY inside a SelfTest-named function, can never lose real fleet work —
    there is no real work in its scope to lose.
    """
    (tmp_path / "janitor.ps1").write_text(
        "function Invoke-SelfTest {\n"
        '  $tempRoot = Join-Path $env:TEMP "janitor-selftest-x"\n'
        '  $originPath = Join-Path $tempRoot "origin.git"\n'
        '  $mainPath = Join-Path $tempRoot "main"\n'
        "  git init --bare -q $originPath *> $null\n"
        "  git init -q $mainPath *> $null\n"
        "  git -C $mainPath add -A *> $null\n"
        "  git -C $mainPath commit -q -m seed *> $null\n"
        "  git -C $mainPath push -q origin main *> $null\n"
        "}\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "silent-staging")


def test_selftest_named_function_without_temp_repo_still_flags(tmp_path: Path):
    """Naming a function SelfTest alone cannot game the exclusion — it must ALSO originate its own
    throwaway repo. A function that claims to be a self-test but mutates/pushes with no `git init`
    under a temp path anywhere is indistinguishable from real work and must still fire.
    """
    (tmp_path / "fake.ps1").write_text(
        "function Invoke-SelfTest {\n"
        "  git add -A *> $null\n"
        "  git commit -q -m x *> $null\n"
        "  git push -q origin main *> $null\n"
        "}\n",
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "silent-staging")


def test_non_selftest_ps1_mutation_still_flags(tmp_path: Path):
    """The exclusion is scoped to the self-test-harness shape, not to .ps1 files in general."""
    (tmp_path / "deploy.ps1").write_text(
        "git add -A *> $null\ngit commit -q -m x *> $null\ngit push -q origin main *> $null\n",
        encoding="utf-8",
    )
    assert _checks(run(tmp_path), "silent-staging")


# ----------------------------------------------------- unmeasured-safe-delete (T-167, 2026-08-17)


def test_unmeasured_safe_delete_is_flagged(tmp_path: Path):
    """The live janitor-worktrees.ps1:144 shape: a blind, untested status gating a deletion."""
    finding = _only_the_defect(
        tmp_path,
        "unmeasured-safe-delete",
        defective=(
            "$status = git -C $wtPath status --porcelain --untracked-files=all 2>$null\n"
            '$statusLines = @($status | Where-Object { $_ -ne "" })\n'
            'if ($statusLines.Count -gt 0) { return @{ Verdict = "KEPT-dirty" } }\n'
            "git -C $RepoPath worktree remove $e.Path *> $null\n"
        ),
        fixed=(
            "$status = git -C $wtPath status --porcelain --untracked-files=all --ignored 2>$null\n"
            'if ($LASTEXITCODE -ne 0) { return @{ Verdict = "KEPT-unmeasurable" } }\n'
            '$statusLines = @($status | Where-Object { $_ -ne "" })\n'
            'if ($statusLines.Count -gt 0) { return @{ Verdict = "KEPT-dirty" } }\n'
            "git -C $RepoPath worktree remove $e.Path *> $null\n"
        ),
    )
    assert "--ignored" in finding.message and "exit code" in finding.message


def test_status_without_a_deletion_is_not_flagged(tmp_path: Path):
    """Ordinary `git status --porcelain` is ubiquitous — only a DELETE predicate is in scope.

    Without this scoping the check would fire on every script that reports repo cleanliness, and a
    gate that cries wolf on normal code is one nobody reads.
    """
    (tmp_path / "reporter.ps1").write_text(
        "$status = git -C $repo status --porcelain --untracked-files=all 2>$null\n"
        '$lines = @($status | Where-Object { $_ -ne "" })\n'
        'Write-Output "dirty lines: $($lines.Count)"\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "unmeasured-safe-delete")


def test_ignored_flag_alone_does_not_clear_the_untested_exit_code(tmp_path: Path):
    """Half a fix is still a defect: seeing ignored files does not make a FAILED status safe.

    Both legs are independent — a status that can see everything still reports nothing when it
    exits 128, and empty output still authorises the delete.
    """
    (tmp_path / "half.ps1").write_text(
        "$status = git -C $wtPath status --porcelain --untracked-files=all --ignored 2>$null\n"
        '$statusLines = @($status | Where-Object { $_ -ne "" })\n'
        'if ($statusLines.Count -gt 0) { return @{ Verdict = "KEPT-dirty" } }\n'
        "git -C $RepoPath worktree remove $e.Path *> $null\n",
        encoding="utf-8",
    )
    found = _checks(run(tmp_path), "unmeasured-safe-delete")
    assert len(found) == 1, "an untested exit code must still flag even with --ignored present"
    # Only the UNSATISFIED leg may be diagnosed. (The remediation sentence names `--ignored`
    # regardless, so assert on the diagnosis clause, not on the whole message.)
    diagnosis = found[0].message.split("Unmeasured is being treated as safe")[0]
    assert "omits `--ignored`" not in diagnosis, "the satisfied leg must not be reported"
    assert "exit code" in diagnosis


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


def test_dead_gate_default_caller_wires_the_dispatcher_skill(tmp_path: Path):
    """preflight-guard.ps1's real shape (2026-08-19 audit): no shell call site anywhere, but it IS
    invoked by the hub's get-work-done dispatcher SKILL.md. The CLI with no --caller must not flag
    it dead-gate — the dispatcher SKILL.md is now wired in by default.
    """
    fleet = tmp_path / "fleet"
    fleet.mkdir()
    (fleet / "preflight-guard.ps1").write_text(
        "# Called before every worker launch; exit 0 = clean to dispatch, non-zero = BLOCK\n"
        "exit 0\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(CHECKER), str(fleet)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stdout
    assert "dead-gate" not in proc.stdout


def test_dead_gate_no_default_caller_flag_still_flags(tmp_path: Path):
    """--no-default-caller opts back out — the same unwired gate must still flag."""
    fleet = tmp_path / "fleet"
    fleet.mkdir()
    (fleet / "preflight-guard.ps1").write_text(
        "# Called before every worker launch; exit 0 = clean to dispatch, non-zero = BLOCK\n"
        "exit 0\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(CHECKER), str(fleet), "--no-default-caller"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "dead-gate" in proc.stdout


# ------------------------------------------------- regression: the gate must fire on the REAL fleet


# The two defects the 2026-08-03 audit CONFIRMED live on the fleet. Fixing them is a fleet-repo
# change (out of scope for this hub PR, which delivers the gates); until then they are the known
# ratchet floor. RULE: this set may only SHRINK. Adding to it is how a gate rots into a to-do list.
# T-167 (2026-08-17) moved the floor OUT of this file into fleet-ratchet-floor.json. It used to
# be a Python literal, which meant editing it was invisible to CI: the assertions below skip when
# the fleet checkout is absent, so a PR emptying the floor was "validated" by a run that could not
# see the fleet. Commit a5cde31 did exactly that on 2026-08-12 — emptied the floor claiming all
# six T-071 findings were fixed; on 2026-08-17 all six still reproduced, and a NEW keeper-tick.cmd
# defect had been hidden behind the empty floor for five days. The JSON carries the observation
# date so test_ratchet_floor_is_evidenced (which runs EVERYWHERE, fleet or not) can block an
# unevidenced shrink.
_FLOOR_FILE = Path(__file__).resolve().parent / "fleet-ratchet-floor.json"
_FLOOR_DOC = json.loads(_FLOOR_FILE.read_text(encoding="utf-8"))
KNOWN_OPEN_FLEET_FINDINGS: set = {(name, check) for name, check in _FLOOR_DOC["findings"]}


_KNOWN_RATCHET_CHECKS = {
    "grep-count", "interpreter", "dead-gate", "discarded", "shape-only", "silent-push",
    "stale-receipt", "unchecked-read", "ps-unchecked-call", "offset-before-write",
    "unchecked-precondition", "unlocked-global-rewrite", "unmeasured-safe-delete",
    "silent-staging",
}

_CLEAN_OUTPUT = "fleet-health: clean"


def _validate_zero_evidence(zero) -> str | None:
    """Shape-validate a zero_evidence block; return the failure reason or None if well-formed.

    Deliberately does NOT (cannot, host-independently) verify the digest is TRUE — only that it
    has the shape a genuine run would produce. Truth is checked separately, on a host that has the
    fleet, by test_zero_floor_evidence_matches_live_fleet.
    """
    if not isinstance(zero, dict):
        return "zero_evidence must be an object"
    if not zero.get("claim"):
        return "zero_evidence missing claim"
    if zero.get("checker_output") != _CLEAN_OUTPUT:
        return f"zero_evidence.checker_output must be the literal {_CLEAN_OUTPUT!r} the CLI prints"
    count = zero.get("scanned_script_count")
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        return "zero_evidence.scanned_script_count must be a positive integer"
    digest = zero.get("manifest_sha256")
    if not (isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)):
        return "zero_evidence.manifest_sha256 must be a 64-char lowercase hex sha256, not a placeholder"
    if not zero.get("manifest_command"):
        return "zero_evidence missing manifest_command"
    return None


def test_ratchet_floor_is_evidenced():
    """The floor artifact must carry re-derivable evidence — and this runs WITHOUT the fleet.

    This is the gate for T-167's HIGH-1. Every other fleet assertion in this file skips when the
    fleet bus is absent, which is always true on CI — so before this test, a PR could delete the
    entire floor and merge green, because "green" only ever meant "the assertions did not run".
    That is how six live defects plus one new one went unreported for five days.

    This assertion is host-independent by construction: it validates the ARTIFACT, not the fleet.
    T-212 extended it to the zero-findings case: findings CAN be empty (that is the sweep's
    success condition), but only paired with a well-formed zero_evidence block whose
    manifest_sha256 is later cross-checked against the live fleet by
    test_zero_floor_evidence_matches_live_fleet — a prose claim alone is still rejected.
    """
    reason = _floor_guard(_FLOOR_DOC)
    assert reason is None, (
        f"the committed ratchet floor failed its own evidence guard: {reason}. If you just fixed "
        f"the last known-open finding, re-run the checker on the fleet host with "
        f"--print-zero-evidence and paste its output into a zero_evidence block in "
        f"{_FLOOR_FILE.name}. If you are emptying it because CI was green, STOP: CI cannot see "
        "the fleet and skips every fleet-dependent assertion in this file (T-167 HIGH-1)."
    )


def _floor_guard(doc: dict) -> str | None:
    """Run test_ratchet_floor_is_evidenced's logic against an arbitrary doc; return the failure.

    Extracted so the negative controls below can prove the guard REJECTS bad floors. Without them
    the guard is vacuous — it would pass just as happily if it checked nothing at all, which is
    precisely the failure mode (a check that never fires) this whole file exists to prevent.
    """
    try:
        findings = doc.get("findings")
        if not findings:
            zero = doc.get("zero_evidence")
            if not zero:
                return "empty floor without zero_evidence"
            reason = _validate_zero_evidence(zero)
            if reason:
                return reason
        else:
            # Entries must be well-formed (name, check) pairs — a malformed floor silently
            # matches nothing and would excuse every finding, the same "looks handled, isn't"
            # shape this gate hunts.
            for entry in findings:
                if not (isinstance(entry, list) and len(entry) == 2 and all(entry)):
                    return f"malformed entry {entry!r}"
            unknown = {c for _, c in findings} - _KNOWN_RATCHET_CHECKS
            if unknown:
                return f"unknown check {sorted(unknown)}"
        # A date that never moves is the tell for an unevidenced edit. Required in both states.
        dt.date.fromisoformat(doc["observed_on"])
        if not doc.get("reproduce_with"):
            return "no reproduce_with"
    except (KeyError, ValueError, TypeError) as e:
        return f"{type(e).__name__}: {e}"
    return None


def test_floor_guard_rejects_empty_floor_without_evidence():
    """The negative control: the guard must REJECT an emptied floor with no attestation.

    This replays commit a5cde31 — the real 2026-08-12 change that emptied the floor on a bare
    claim and merged green because CI cannot see the fleet. If this test ever passes with the
    guard removed (or neutered to accept anything), the guard is decoration.
    """
    good = json.loads(_FLOOR_FILE.read_text(encoding="utf-8"))
    assert _floor_guard(good) is None, "the committed floor must itself be valid"

    emptied = {k: v for k, v in good.items() if k != "zero_evidence"}
    emptied["findings"] = []
    assert _floor_guard(emptied) == "empty floor without zero_evidence", (
        "emptying the floor with no attestation must be REJECTED — that is the defect that "
        "shipped in a5cde31"
    )


def test_floor_guard_accepts_empty_floor_with_valid_evidence():
    """The positive control: a well-formed zero_evidence block on an empty floor IS accepted.

    Without this, test_floor_guard_rejects_empty_floor_without_evidence alone would let a guard
    that rejects EVERY empty floor (evidenced or not) pass unnoticed — which would make T-212's
    whole point moot, since the sweep's actual success condition (genuinely zero, evidenced) could
    never be expressed. Uses a synthetic digest, not the committed one, so this proves the ACCEPT
    path is real rather than piggy-backing on the repo's own floor happening to be valid.
    """
    good = json.loads(_FLOOR_FILE.read_text(encoding="utf-8"))
    synthetic = dict(
        good,
        findings=[],
        zero_evidence={
            "claim": "the live fleet bus carries zero known silent-failure defects as of observed_on",
            "checker_output": _CLEAN_OUTPUT,
            "scanned_script_count": 7,
            "manifest_sha256": "0" * 64,
            "manifest_command": "PYTHONPATH=. python scripts/check_fleet_script_health.py X --print-zero-evidence",
        },
    )
    assert _floor_guard(synthetic) is None, "a well-formed zero_evidence attestation must be accepted"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda z: {k: v for k, v in z.items() if k != "claim"},
        lambda z: dict(z, claim=""),
        lambda z: dict(z, checker_output="all clean, trust me"),
        lambda z: {k: v for k, v in z.items() if k != "checker_output"},
        lambda z: dict(z, scanned_script_count=0),
        lambda z: dict(z, scanned_script_count="34"),
        lambda z: {k: v for k, v in z.items() if k != "scanned_script_count"},
        lambda z: dict(z, manifest_sha256="not-a-real-digest"),
        lambda z: dict(z, manifest_sha256="ZZ" * 32),
        lambda z: {k: v for k, v in z.items() if k != "manifest_sha256"},
        lambda z: {k: v for k, v in z.items() if k != "manifest_command"},
    ],
)
def test_floor_guard_rejects_malformed_zero_evidence(mutate):
    """Each required zero_evidence field is load-bearing — dropping or faking any one must fail.

    This is what makes the attestation harder to fake than a comment: a bare claim ('checker_output
    ="all clean, trust me"') or a placeholder digest is caught by SHAPE alone, before the deeper
    live-fleet cross-check even runs.
    """
    good = json.loads(_FLOOR_FILE.read_text(encoding="utf-8"))
    base_zero = good["zero_evidence"]
    bad = dict(good, findings=[], zero_evidence=mutate(base_zero))
    assert _floor_guard(bad) is not None, f"malformed zero_evidence must be rejected: {bad['zero_evidence']!r}"


def test_floor_guard_rejects_malformed_and_typoed_entries():
    """A malformed or misspelled entry matches nothing, silently excusing a real live defect."""
    good = json.loads(_FLOOR_FILE.read_text(encoding="utf-8"))
    assert _floor_guard(dict(good, findings=[["keeper-tick.cmd"]])) is not None
    assert _floor_guard(dict(good, findings=[["keeper-tick.cmd", ""]])) is not None
    typo = dict(good, findings=[["keeper-tick.cmd", "silent-stagin"]])
    assert "unknown check" in (_floor_guard(typo) or ""), (
        "a typo'd check name excuses nothing and hides the finding it was meant to record"
    )
    assert _floor_guard(dict(good, observed_on="not-a-date")) is not None


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
    fleet = _resolve_fleet_dir()
    if fleet is None:
        pytest.skip("fleet bus not present on this host")
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
    fleet = _resolve_fleet_dir()
    if fleet is None:
        pytest.skip("fleet bus not present on this host")
    seen = {(f.path.name, f.check) for f in run(fleet, extra_callers=[_DISPATCHER_SKILL])}
    stale = KNOWN_OPEN_FLEET_FINDINGS - seen
    assert not stale, (
        f"these known-open findings no longer reproduce — remove them from the ratchet: {stale}"
    )


def test_zero_floor_evidence_matches_live_fleet():
    """When the floor claims zero findings, its manifest digest must match the LIVE fleet content.

    This is the host-gated truth check that makes the zero_evidence attestation harder to fake
    than a comment. manifest_sha256 is a sha256 over every scanned script's (relative path,
    content sha256), sorted — nobody can produce a digest that matches the live fleet without
    actually reading the live fleet's real files. On any host that has the fleet, this test
    recomputes the digest fresh and fails loudly the instant it diverges from what is committed,
    whether the divergence is honest drift (the fleet changed since the evidence was taken) or a
    fabricated value that was never actually run. Mirrors test_known_open_fleet_findings_still_
    reproduce's pattern (host-gated ground truth) for the OPPOSITE state of the same floor.
    """
    if _FLOOR_DOC.get("findings"):
        pytest.skip("floor is not in the zero-findings state")
    fleet = _resolve_fleet_dir()
    if fleet is None:
        pytest.skip("fleet bus not present on this host")
    zero = _FLOOR_DOC.get("zero_evidence") or {}
    live_digest, live_count = manifest_digest(fleet)
    assert live_digest == zero.get("manifest_sha256"), (
        f"zero_evidence.manifest_sha256 ({zero.get('manifest_sha256')}) does not match the live "
        f"fleet's current manifest ({live_digest}) — the floor is stale or was never actually "
        "run; re-run `check_fleet_script_health.py <fleet> --print-zero-evidence` and refresh it"
    )
    assert live_count == zero.get("scanned_script_count"), (
        f"zero_evidence.scanned_script_count ({zero.get('scanned_script_count')}) does not match "
        f"the live fleet's current script count ({live_count})"
    )


def test_keeper_tick_checks_both_guard_exit_codes():
    """Regression: every guard invocation in keeper-tick.cmd is followed by an errorlevel test."""
    fleet = _resolve_fleet_dir()
    if fleet is None:
        pytest.skip("fleet bus not present on this host")
    tick = fleet / "keeper-tick.cmd"
    if not tick.exists():
        pytest.skip("keeper-tick.cmd not present in the fleet bus")
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
    fleet = _resolve_fleet_dir()
    if fleet is None:
        pytest.skip("fleet bus not present on this host")
    tick = fleet / "keeper-tick.cmd"
    if not tick.exists():
        pytest.skip("keeper-tick.cmd not present in the fleet bus")
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
    fleet = _resolve_fleet_dir()
    if fleet is None:
        pytest.skip("fleet bus not present on this host")
    tick = fleet / "keeper-tick.cmd"
    if not tick.exists():
        pytest.skip("keeper-tick.cmd not present in the fleet bus")
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


# --------------------------- T-208: prove _resolve_fleet_dir's three states by execution ---------


def test_resolve_fleet_dir_returns_none_when_absent(tmp_path: Path, monkeypatch):
    """(a) No candidate exists at all -> None, no warning (there was nothing to reject)."""
    monkeypatch.setenv(_FLEET_ENV_VAR, str(tmp_path / "does-not-exist"))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = _resolve_fleet_dir()
    assert result is None
    assert not caught, f"unexpected warning for a genuinely absent path: {[str(w.message) for w in caught]}"


def test_resolve_fleet_dir_rejects_a_stub_with_only_heartbeats(tmp_path: Path, monkeypatch):
    """(b) A directory exists but carries only an empty heartbeats/ dir (the live 2026-07-30 stub
    shape at C:\\Abhay\\GetWorkDone) -> None, WITH a loud warning naming the path and the reason.

    This is the exact defect T-208 fixes: the stub EXISTS, so a bare `.exists()` check treated it
    as the fleet and silently scanned nothing. The marker check must reject it, and the rejection
    must be visible, not another silent skip.
    """
    stub = tmp_path / "stub"
    (stub / "heartbeats").mkdir(parents=True)
    monkeypatch.setenv(_FLEET_ENV_VAR, str(stub))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = _resolve_fleet_dir()
    assert result is None, "a stub with no settings.json/queue/ must never resolve as the fleet"
    assert caught, "rejecting an existing-but-invalid candidate must emit a warning, not skip silently"
    msg = str(caught[0].message)
    assert str(stub) in msg and "queue" in msg.lower(), (
        f"warning must name the rejected path and the missing marker: {msg!r}"
    )


def test_resolve_fleet_dir_accepts_a_real_bus(tmp_path: Path, monkeypatch):
    """(c) A directory carrying both markers (settings.json#repo_registry + queue/) resolves."""
    real = tmp_path / "real-bus"
    (real / "queue").mkdir(parents=True)
    (real / _FLEET_MARKER_FILE).write_text(
        json.dumps({_FLEET_MARKER_KEY: {"claude-best-practices": "abhayla/claude-best-practices"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv(_FLEET_ENV_VAR, str(real))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = _resolve_fleet_dir()
    assert result == real, "a directory with both bus markers must resolve"
    assert not caught, f"a valid bus must never be warned about: {[str(w.message) for w in caught]}"

    # And the ratchet actually RUNS against it (rather than skipping) once resolved: plant one
    # known-bad construct and confirm `run()` sees it through the resolved path.
    (real / "bad.sh").write_text(
        "#!/bin/bash\n"
        'seen=$(grep -c "^k$" state 2>/dev/null || echo 0)\n'
        'if [ "$seen" -lt 1 ]; then echo k >> state; fi\n',
        encoding="utf-8",
    )
    findings = run(result)
    assert _checks(findings, "grep-count"), "the ratchet must actually scan the resolved real bus"


def test_resolve_fleet_dir_honours_env_override_even_off_known_locations(tmp_path: Path, monkeypatch):
    """An explicit override is authoritative — it must not silently fall back to D:/C: guesses."""
    real = tmp_path / "custom-bus"
    (real / "queue").mkdir(parents=True)
    (real / _FLEET_MARKER_FILE).write_text(json.dumps({_FLEET_MARKER_KEY: {}}), encoding="utf-8")
    monkeypatch.setenv(_FLEET_ENV_VAR, str(real))
    assert _resolve_fleet_dir() == real


# ------------------------------------------------------- unmeasured-reset (HIGH: bus-sync.sh, T-320)


def test_unmeasured_reset_is_flagged(tmp_path: Path):
    """The live bus-sync.sh:8 shape: `git log '@{u}..HEAD'` emptiness authorising a hard reset.

    The probe exits 128 with EMPTY stdout when the upstream cannot be resolved, so "I could not
    measure" is read as "there is nothing to lose" and the reset destroys committed work.
    """
    finding = _only_the_defect(
        tmp_path,
        "unmeasured-reset",
        defective=(
            "#!/bin/bash\n"
            'bus_pull() {\n'
            '  git checkout main -q 2>/dev/null || return 1\n'
            "  if [ -n \"$(git log '@{u}..HEAD' --oneline 2>/dev/null)\" ]; then\n"
            "    git pull -q --rebase origin main 2>/dev/null || return 2\n"
            "  else\n"
            "    git pull -q --rebase origin main 2>/dev/null || "
            "{ git fetch -q origin main && git reset -q --hard origin/main; }\n"
            "  fi\n"
            "}\n"
        ),
        fixed=(
            "#!/bin/bash\n"
            'bus_pull() {\n'
            '  git checkout main -q 2>/dev/null || return 1\n'
            # Fail closed: if the upstream cannot even be resolved, we CANNOT know whether there
            # are unpushed commits, so we must never take the reset branch.
            '  git rev-parse --abbrev-ref "@{u}" >/dev/null 2>&1 || {\n'
            '    echo "BUS-SYNC: upstream unresolvable — refusing to reset" >&2; return 3; }\n'
            "  if [ -n \"$(git log '@{u}..HEAD' --oneline 2>/dev/null)\" ]; then\n"
            "    git pull -q --rebase origin main 2>/dev/null || return 2\n"
            "  else\n"
            "    git pull -q --rebase origin main 2>/dev/null || "
            "{ git fetch -q origin main && git reset -q --hard origin/main; }\n"
            "  fi\n"
            "}\n"
        ),
    )
    assert "reset --hard" in finding.message and "exit code is never tested" in finding.message


def test_unpushed_probe_without_a_hard_reset_is_not_flagged(tmp_path: Path):
    """Reporting unpushed commits is ubiquitous and harmless — only a RESET puts work at risk.

    Without this scoping the check would fire on every status/report script, and a gate that cries
    wolf on normal code is one nobody reads.
    """
    (tmp_path / "report.sh").write_text(
        "#!/bin/bash\n"
        "ahead=$(git log '@{u}..HEAD' --oneline 2>/dev/null)\n"
        'if [ -n "$ahead" ]; then echo "unpushed commits present"; fi\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "unmeasured-reset")


def test_neighbouring_exit_test_does_not_clear_the_probe(tmp_path: Path):
    """A `|| return` on the NEXT line guards that line, not the probe — the live bus-sync.sh trap.

    bus-sync.sh's rebase carries `|| { ...; return 2; }` one line below the probe. A windowed
    failure-tested search reads that as "the probe is checked" and the real defect walks through.
    """
    (tmp_path / "windowed.sh").write_text(
        "#!/bin/bash\n"
        "if [ -n \"$(git log '@{u}..HEAD' --oneline 2>/dev/null)\" ]; then\n"
        "  git pull -q --rebase origin main 2>/dev/null || { git rebase --abort; return 2; }\n"
        "else\n"
        "  git reset -q --hard origin/main\n"
        "fi\n",
        encoding="utf-8",
    )
    found = _checks(run(tmp_path), "unmeasured-reset")
    assert len(found) == 1 and found[0].line == 2, (
        "the probe on line 2 must still be flagged despite the `|| return 2` on line 3, which "
        f"belongs to the rebase — got {[(f.path.name, f.line) for f in found]}"
    )


# ------------------------------------------- dead-convention-guard (HIGH: janitor-worktrees, T-320)


def _janitor(body: str) -> str:
    """A janitor-shaped script: a leaf-convention guard whose fall-through DELETES a worktree."""
    return (
        "function Test-WorktreeSafety {\n"
        "  $leaf = Split-Path $wtPath -Leaf\n"
        f"{body}"
        '  git -C $RepoPath worktree remove $e.Path *> $null\n'
        "}\n"
    )


def test_dead_convention_guard_is_flagged(tmp_path: Path):
    """The live janitor-worktrees.ps1:137 shape: `-wt-t<id>` vs real `T-320-repo` / `repo-T149`."""
    ws = tmp_path / "workspaces"
    ws.mkdir()
    for n in ("T-320-claude-best-practices", "gorefer-T149", "T-215-IPODhan", "gorefer-wt-t060"):
        (ws / n).mkdir()
    (tmp_path / "janitor.ps1").write_text(
        _janitor(
            "  if ($leaf -match '-wt-t(\\d+)$') {\n"
            '    if (Test-Path $hbPath) { return @{ Verdict = "KEPT-live" } }\n'
            "  }\n"
        ),
        encoding="utf-8",
    )
    found = _checks(run(tmp_path, None, [d for d in ws.iterdir() if d.is_dir()]), "dead-convention-guard")
    assert len(found) == 1, f"expected the dead guard to be flagged, got {found}"
    assert found[0].line == 3
    assert "1 of 4" in found[0].message


def test_live_convention_guard_is_not_flagged(tmp_path: Path):
    """The FIXED form: a convention that actually matches the fleet's names must stay silent.

    This is the half that proves the check discriminates — without it, a check that flagged every
    `-match` in a destructive script would pass the positive test above and be useless.
    """
    ws = tmp_path / "workspaces"
    ws.mkdir()
    for n in ("T-320-claude-best-practices", "gorefer-T149", "T-215-IPODhan", "gorefer-wt-t060"):
        (ws / n).mkdir()
    (tmp_path / "janitor.ps1").write_text(
        _janitor(
            "  if ($leaf -match '[-]?T-?(\\d+)') {\n"
            '    if (Test-Path $hbPath) { return @{ Verdict = "KEPT-live" } }\n'
            "  }\n"
        ),
        encoding="utf-8",
    )
    found = _checks(run(tmp_path, None, [d for d in ws.iterdir() if d.is_dir()]), "dead-convention-guard")
    assert not found, f"a convention matching the live names must not be flagged, got {found}"


def test_dead_convention_guard_stays_silent_without_ground_truth(tmp_path: Path):
    """No live directory listing => no verdict. The check must never GUESS.

    On a CI box the fleet is not on disk. Scoring "matches nothing" there would flag every healthy
    convention, which is the same unmeasurable-claim defect these gates exist to stamp out — so
    absent ground truth the check returns nothing rather than inventing a finding.
    """
    (tmp_path / "janitor.ps1").write_text(
        _janitor(
            "  if ($leaf -match '-wt-t(\\d+)$') {\n"
            '    if (Test-Path $hbPath) { return @{ Verdict = "KEPT-live" } }\n'
            "  }\n"
        ),
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "dead-convention-guard")


def test_non_leaf_match_is_not_a_convention_guard(tmp_path: Path):
    """`-match '^!!'` over git status output is not a naming convention — must not be flagged."""
    ws = tmp_path / "workspaces"
    ws.mkdir()
    (ws / "T-320-repo").mkdir()
    (tmp_path / "janitor.ps1").write_text(
        "function Test-WorktreeSafety {\n"
        "  $status = git -C $wtPath status --porcelain --ignored 2>$null\n"
        "  $ignoredLines = @($statusLines | Where-Object { $_ -match '^!!' })\n"
        "  git -C $RepoPath worktree remove $e.Path *> $null\n"
        "}\n",
        encoding="utf-8",
    )
    found = _checks(run(tmp_path, None, [d for d in ws.iterdir() if d.is_dir()]), "dead-convention-guard")
    assert not found, f"a status-output match is not a leaf convention, got {found}"


# --------------------------------------------------- clobbered-exit (HIGH: worker-wrapper, T-320)


def test_clobbered_exit_is_flagged(tmp_path: Path):
    """The live worker-wrapper.ps1:755-757 shape: `git add` clobbered by `git commit`.

    The FIXED form keeps the same two calls and the same test -- it only captures the first code
    before the second call runs. A check that cannot tell these apart is worthless, so this asserts
    exactly one finding, on the defective file.
    """
    finding = _only_the_defect(
        tmp_path,
        "clobbered-exit",
        defective=(
            "git checkout -b $branch *> $null\n"
            "if ($LASTEXITCODE -eq 0) {\n"
            "  git add -A *> $null\n"
            '  git commit -m "autosave" *> $null\n'
            "  if ($LASTEXITCODE -eq 0) {\n"
            '    Add-Content -Path $hb -Value "committed to rescue branch"\n'
            "  }\n"
            "}\n"
        ),
        fixed=(
            "git checkout -b $branch *> $null\n"
            "if ($LASTEXITCODE -eq 0) {\n"
            "  git add -A *> $null\n"
            "  $addRc = $LASTEXITCODE\n"
            '  git commit -m "autosave" *> $null\n'
            "  if ($addRc -eq 0 -and $LASTEXITCODE -eq 0) {\n"
            '    Add-Content -Path $hb -Value "committed to rescue branch"\n'
            "  }\n"
            "}\n"
        ),
    )
    assert "overwritten by the native call on the next line" in finding.message


def test_native_call_pair_with_no_exitcode_read_is_not_flagged(tmp_path: Path):
    """Two native calls nobody checks at all is the EXISTING unchecked-call shape, not this one.

    Without this scoping the check would double-report every unchecked pair the other gates
    already own, and duplicated findings train people to skim the report.
    """
    (tmp_path / "plain.ps1").write_text(
        "git add -A *> $null\n"
        'git commit -m "x" *> $null\n'
        'Write-Output "done"\n',
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "clobbered-exit")


def test_exitcode_tested_between_the_two_calls_is_not_flagged(tmp_path: Path):
    """A test BETWEEN the calls reads the first code while it is still live — correct code."""
    (tmp_path / "guarded.ps1").write_text(
        "git add -A *> $null\n"
        "if ($LASTEXITCODE -ne 0) { throw 'staging failed' }\n"
        'git commit -m "x" *> $null\n'
        "if ($LASTEXITCODE -eq 0) { Write-Output 'ok' }\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "clobbered-exit")


def test_differently_indented_calls_are_not_a_straight_line_sequence(tmp_path: Path):
    """Calls in different blocks do not necessarily execute back-to-back — do not guess."""
    (tmp_path / "branched.ps1").write_text(
        "git add -A *> $null\n"
        "  git commit -m 'x' *> $null\n"
        "if ($LASTEXITCODE -eq 0) { Write-Output 'ok' }\n",
        encoding="utf-8",
    )
    assert not _checks(run(tmp_path), "clobbered-exit")
