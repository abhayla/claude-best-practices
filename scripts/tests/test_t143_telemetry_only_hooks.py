"""T-143 (owner-approved 2026-08-16, review Fix 3) — dedicated fixture-driven proof that
no-overask-guard.sh and the plugin's enhance-process-guard.sh ("the enhance-card Stop gate")
are TELEMETRY-ONLY.

HOOK EXIT-SEMANTICS CONTRACT pinned by this file:
  1. Exit code is always 0 (a Stop hook that exits non-zero is itself a form of interruption;
     these hooks must be inert on that axis too).
  2. Stdout is either empty OR valid JSON that never contains {"decision":"block"} — there is
     no other decision value these hooks may emit that re-opens/interrupts a turn.
  3. Every miss class the hook detects still appends exactly one line to its designated log
     file (.claude/.overask-violations.log or .claude/.enhance-misses.log), in the SAME format
     used before T-143, so scripts/lint_rule_compliance.py keeps working unmodified.

Each test below feeds a synthetic fixture transcript that — before T-143 — would have
triggered a real {"decision":"block"} from at least one of the two guards, and asserts both
halves of the contract: the miss is logged, and the turn is never blocked.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
HUB_GUARD = ROOT / ".claude" / "hooks" / "no-overask-guard.sh"
CORE_GUARD = ROOT / "core" / ".claude" / "hooks" / "no-overask-guard.sh"
PLUGIN_GUARD = ROOT / "plugins" / "prompt-auto-enhance" / "hooks" / "enhance-process-guard.sh"

BASH = shutil.which("bash")
JQ = shutil.which("jq")
GIT = shutil.which("git")
pytestmark = pytest.mark.skipif(
    not (BASH and JQ and GIT), reason="bash+jq+git required for behavioral hook tests"
)


def _scratch_repo(tmp_path_factory) -> Path:
    scratch = tmp_path_factory.mktemp("t143-scratch")
    subprocess.run([GIT, "init", "-q"], cwd=str(scratch), check=True)
    return scratch


def _run(hook: Path, transcript: list, cwd: Path):
    tp = cwd / "transcript.jsonl"
    tp.write_text("\n".join(json.dumps(e) for e in transcript) + "\n", encoding="utf-8")
    payload = json.dumps({"transcript_path": str(tp).replace("\\", "/")})
    return subprocess.run(
        [BASH, str(hook)], input=payload, capture_output=True, text=True, cwd=str(cwd)
    )


def _assert_never_blocks(result: subprocess.CompletedProcess, hook_name: str):
    assert result.returncode == 0, (
        f"{hook_name} must exit 0 — a non-zero exit is itself a form of interruption: "
        f"rc={result.returncode}, stderr={result.stderr!r}"
    )
    out = result.stdout.strip()
    if out:
        try:
            parsed = json.loads(out)
        except json.JSONDecodeError:
            pytest.fail(f"{hook_name} emitted non-JSON stdout: {out!r}")
        assert parsed.get("decision") != "block", (
            f"{hook_name} emitted a block decision — telemetry-only contract violated: {out!r}"
        )


def _log_text(scratch: Path, name: str) -> str:
    p = scratch / ".claude" / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ── Fixture 1: a substantive human turn with NO card at all (the strongest miss shape;
# pre-T-143 this was G7's textbook block). ──
_NO_CARD_TEXT = "I made the change and verified it works end to end. " * 12
assert len(_NO_CARD_TEXT) >= 300

_NO_CARD_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "add the retry logic to the sender"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _NO_CARD_TEXT}]}},
]


@pytest.mark.parametrize("hook,hook_name,log_name,expected_token", [
    (HUB_GUARD, "hub no-overask-guard.sh", ".overask-violations.log", "reviewer-card-miss"),
    (CORE_GUARD, "core no-overask-guard.sh", ".overask-violations.log", "reviewer-card-miss"),
])
def test_no_card_miss_is_logged_and_never_blocks(tmp_path_factory, hook, hook_name, log_name, expected_token):
    scratch = _scratch_repo(tmp_path_factory)
    result = _run(hook, _NO_CARD_TRANSCRIPT, scratch)
    _assert_never_blocks(result, hook_name)
    log = _log_text(scratch, log_name)
    assert expected_token in log, f"{hook_name} must log a '{expected_token}' line: got {log!r}"


def test_plugin_guard_no_card_miss_never_blocks(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    result = _run(PLUGIN_GUARD, _NO_CARD_TRANSCRIPT, scratch)
    _assert_never_blocks(result, "plugin enhance-process-guard.sh")


# ── Fixture 2: a card that renders but omits diagnose->fix substance (pre-T-143: the
# second, distinct block path in no-overask-guard.sh). Deliberately does NOT open with the
# *Enhanced: banner (the T-116 banner-present short-circuit exempts BOTH the card and
# substance checks — this fixture must exercise the substance check specifically, so the
# card table appears mid-turn instead of as the first line). ──
_CARD_NO_SUBSTANCE_TEXT = (
    "Here is the review:\n\n"
    "| Dim | Before | Self-after | Reviewer-after |\n"
    "|---|---|---|---|\n"
    "| Role | 2 | 8 | 8 |\n"
    "Overall: F -> B\n\n"
    + ("The change is applied and the tests pass locally. " * 8)
)
assert len(_CARD_NO_SUBSTANCE_TEXT) >= 300
assert not _CARD_NO_SUBSTANCE_TEXT.lower().startswith("*enhanced")

_CARD_NO_SUBSTANCE_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "fix the flaky test"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _CARD_NO_SUBSTANCE_TEXT}]}},
]


def test_diagnosis_substance_miss_is_logged_and_never_blocks(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    result = _run(HUB_GUARD, _CARD_NO_SUBSTANCE_TRANSCRIPT, scratch)
    _assert_never_blocks(result, "hub no-overask-guard.sh")
    log = _log_text(scratch, ".overask-violations.log")
    assert "diagnosis-substance-miss" in log, f"must log diagnosis-substance-miss: got {log!r}"


# ── Fixture 3: classic over-ask ending (pre-T-143: the third, distinct block path — the
# over-ask/narrate-and-stop guard at the tail of the file). ──
_OVER_ASK_TEXT = (
    "*Enhanced: checked stuff — Grade A, no strengthening needed*\n\n"
    + ("I finished the migration and verified the rollback path. " * 8)
    + "\n\nWant me to also update the docs, or should I leave it as is?"
)
assert len(_OVER_ASK_TEXT) >= 300

_OVER_ASK_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "run the migration"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _OVER_ASK_TEXT}]}},
]


def test_over_ask_stop_violation_is_logged_and_never_blocks(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    result = _run(HUB_GUARD, _OVER_ASK_TRANSCRIPT, scratch)
    _assert_never_blocks(result, "hub no-overask-guard.sh")
    log = _log_text(scratch, ".overask-violations.log")
    assert "stop-violation" in log and "over-ask" in log, f"must log an over-ask stop-violation: got {log!r}"


# ── Fixture 4: narrate-and-stop ending. ──
_NARRATE_TEXT = (
    "*Enhanced: checked stuff — Grade A, no strengthening needed*\n\n"
    + ("Implemented the change and confirmed the fixture passes. " * 8)
    + "\n\nNext step is to wire the second call site — I'll tackle that next."
)
assert len(_NARRATE_TEXT) >= 300

_NARRATE_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "wire up the new field"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": _NARRATE_TEXT}]}},
]


def test_narrate_and_stop_is_logged_and_never_blocks(tmp_path_factory):
    scratch = _scratch_repo(tmp_path_factory)
    result = _run(HUB_GUARD, _NARRATE_TRANSCRIPT, scratch)
    _assert_never_blocks(result, "hub no-overask-guard.sh")
    log = _log_text(scratch, ".overask-violations.log")
    assert "stop-violation" in log and "narrate-and-stop" in log, f"must log narrate-and-stop: got {log!r}"


# ── Static contract lock: none of the three guard sources may contain a live block emission. ──
def test_no_guard_source_contains_a_live_block_emission():
    import re

    for name, fp in [("hub", HUB_GUARD), ("core", CORE_GUARD), ("plugin", PLUGIN_GUARD)]:
        body = fp.read_text(encoding="utf-8")
        collapsed = re.sub(r"\s+", "", body)
        assert 'decision:"block"' not in collapsed, (
            f"{name} guard still contains a live {{decision:\"block\"}} code path — T-143 requires "
            f"telemetry-only hooks"
        )


def test_wired_as_loggers_in_hub_settings():
    """DoD: the hooks stay WIRED in .claude/settings.json (as loggers, not enforcers)."""
    settings_text = (ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert "no-overask-guard.sh" in settings_text, (
        "no-overask-guard.sh must remain wired in .claude/settings.json"
    )
