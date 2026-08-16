"""Behavioral regression tests for the no-overask-guard Stop hook's slash/origin exemption
(issue #331 — live false-block repro, session 889094c3 2026-07-12).

The harness writes a slash invocation as TWO consecutive user entries: the <command-name>
marker entry AND the fully-expanded command BODY as a separate marker-less plain-text entry.
The guard used to inspect only the LAST user entry (`tail -1`), saw the marker-less body, and
false-blocked slash turns ("enhance: full process not rendered" on /init). After a block, the
"Stop hook feedback:" entry became the last entry, stripping the origin again -> double-block.

T-143 (owner-approved 2026-08-16, review Fix 3): the guard is now TELEMETRY-ONLY — it never
emits {"decision":"block"} or re-opens a turn on ANY shape below, including the ones that used
to legitimately block (a plain human prompt with no card, true narrate-and-stop, etc.). These
tests now pin: (a) the guard never blocks, on any transcript shape, and (b) the exemption
logic itself (still meaningful for the LOG side — an exempt turn must not even be logged) is
unchanged.

These tests run the real bash hook against synthetic transcript fixtures in an isolated tmp
git repo (so its counters/telemetry never touch the real .claude/ state) and pin:
  1. two-entry slash submission (marker + expanded body) -> exempt, no block, no log
  2. plain human prompt with no card -> never blocked, but STILL logged (enforcement not weakened)
  3. stop-feedback retry turn after a slash turn -> origin inherited, still exempt
  4. stop-feedback retry turn after a HUMAN turn -> still logged (feedback-skip is not a hole)
  5. trivial "no change - .../ran as-is" first-line variants -> exempt (regex was too narrow)
"""

import json
import shutil
import subprocess

import pytest

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / ".claude" / "hooks" / "no-overask-guard.sh"
CORE_HOOK = ROOT / "core" / ".claude" / "hooks" / "no-overask-guard.sh"
PLUGIN_GUARD = ROOT / "plugins" / "prompt-auto-enhance" / "hooks" / "enhance-process-guard.sh"
TURN_ORIGIN = ROOT / ".claude" / "hooks" / "turn-origin.sh"

BASH = shutil.which("bash")
JQ = shutil.which("jq")
GIT = shutil.which("git")

pytestmark = pytest.mark.skipif(
    not (BASH and JQ and GIT), reason="bash+jq+git required for behavioral hook tests"
)

# Neutral substantive assistant text: >=300 chars, no banner/card, and deliberately free of
# over-ask / narrate-and-stop / blocker-exemption trigger phrases.
SUBSTANTIVE = (
    "The parser change is in place and both readers now accept the new record format. "
    "All twelve unit checks pass locally and the fixture corpus round-trips byte-for-byte. "
    "The config loader keeps its previous defaults and the migration path stays unchanged. "
    "Everything the request covered is done and verified against the sample inputs."
)
assert len(SUBSTANTIVE) >= 300

SLASH_MARKER = "<command-message>init</command-message>\n<command-name>/init</command-name>"
SLASH_BODY = (
    "Please analyze this codebase and create a CLAUDE.md file, which will be given to future "
    "instances of Claude Code to operate in this repository. Include build commands and the "
    "high-level architecture so future instances can be productive quickly."
)
STOP_FEEDBACK = (
    "Stop hook feedback:\nSTOP BLOCKED (enhance: full process not rendered). This substantive "
    "turn did NOT render the full prompt-auto-enhance process."
)
HUMAN_PROMPT = "Review this project and tell me what one thing you would improve in it."


def _user(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}}


def _assistant(text: str) -> dict:
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def _attachment() -> dict:
    return {"type": "attachment"}


@pytest.fixture()
def tmp_repo(tmp_path):
    subprocess.run([GIT, "init", "-q"], cwd=tmp_path, check=True)
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    shutil.copy(TURN_ORIGIN, hooks / "turn-origin.sh")
    return tmp_path


def _run_guard(tmp_repo: Path, entries: list, hook: Path = HOOK) -> str:
    tp = tmp_repo / "transcript.jsonl"
    tp.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    payload = json.dumps({"transcript_path": str(tp).replace("\\", "/")})
    res = subprocess.run(
        [BASH, str(hook)], input=payload, capture_output=True, text=True, cwd=str(tmp_repo)
    )
    return res.stdout


def _violations_log_text(tmp_repo: Path) -> str:
    p = tmp_repo / ".claude" / ".overask-violations.log"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def test_two_entry_slash_submission_is_exempt(tmp_repo):
    """Marker entry + expanded-body entry (the /init shape) must NOT be card-blocked or logged."""
    out = _run_guard(
        tmp_repo,
        [_user(SLASH_MARKER), _attachment(), _user(SLASH_BODY), _assistant(SUBSTANTIVE)],
    )
    assert '"decision":"block"' not in out, f"slash turn must never block (T-143): {out}"
    assert _violations_log_text(tmp_repo) == "", "a genuinely exempt slash turn must not be logged"


def test_human_prompt_without_card_never_blocks_but_is_logged(tmp_repo):
    """Control: the guard must never block (T-143) — but a genuine human turn with no card
    must still be LOGGED, or telemetry silently went dark."""
    out = _run_guard(tmp_repo, [_user(HUMAN_PROMPT), _assistant(SUBSTANTIVE)])
    assert '"decision":"block"' not in out, f"guard must never block (T-143): {out}"
    assert "reviewer-card-miss" in _violations_log_text(tmp_repo), (
        "a human turn with no card must still be logged as a miss"
    )


def test_stop_feedback_retry_inherits_slash_origin(tmp_repo):
    """After a would-have-blocked turn, the feedback entry must not strip the slash exemption."""
    out = _run_guard(
        tmp_repo,
        [
            _user(SLASH_MARKER),
            _user(SLASH_BODY),
            _assistant(SUBSTANTIVE),
            _user(STOP_FEEDBACK),
            _assistant(SUBSTANTIVE),
        ],
    )
    assert '"decision":"block"' not in out, f"slash retry turn must never block (T-143): {out}"


def test_stop_feedback_retry_after_human_prompt_is_still_logged(tmp_repo):
    """Walking back past feedback entries must land on the HUMAN prompt, keeping telemetry —
    never blocking (T-143)."""
    out = _run_guard(
        tmp_repo,
        [
            _user(HUMAN_PROMPT),
            _assistant(SUBSTANTIVE),
            _user(STOP_FEEDBACK),
            _assistant(SUBSTANTIVE),
        ],
    )
    assert '"decision":"block"' not in out, f"guard must never block (T-143): {out}"
    assert "reviewer-card-miss" in _violations_log_text(tmp_repo)


# Narrate-and-stop substring false positive (live incident 2026-07-23, session 7dab66ac):
# `one (narrow|thin)` matched the ordinary phrase "one thing" as the substring "one thin",
# false-flagging a turn that legitimately ended at a user-gated blocker. Fixed with a boundary
# (`([^a-z]|$)`) plus new blocker-exemption tokens ("gated on your", "yours to do").
GRADEA_LINE = "*Enhanced: checked against the change — Grade A, no strengthening needed*\n"


def test_one_thing_phrase_is_not_narrate_and_stop(tmp_repo):
    """'one thing' must not match the 'one (narrow|thin)' narrate pattern as a substring —
    still not logged as a stop-violation, since it isn't one."""
    text = GRADEA_LINE + SUBSTANTIVE + (
        " That flag check is the one thing the second reviewer looked at, and it holds."
    )
    out = _run_guard(tmp_repo, [_user(HUMAN_PROMPT), _assistant(text)])
    assert '"decision":"block"' not in out, f"guard must never block (T-143): {out}"
    assert "stop-violation" not in _violations_log_text(tmp_repo), (
        "'one thing' false-matched as narrate-and-stop"
    )


def test_true_narrate_and_stop_is_never_blocked_but_is_logged(tmp_repo):
    """Control: genuine deferred-next-step language must never block (T-143) but must still
    be logged as a stop-violation."""
    text = GRADEA_LINE + SUBSTANTIVE + (
        " From here: one thin layer remains and next I'll wire the sender."
    )
    out = _run_guard(tmp_repo, [_user(HUMAN_PROMPT), _assistant(text)])
    assert '"decision":"block"' not in out, f"guard must never block (T-143): {out}"
    log = _violations_log_text(tmp_repo)
    assert "stop-violation" in log and "narrate-and-stop" in log, (
        f"genuine narrate-and-stop must still be logged: {log!r}"
    )


def test_user_gated_closing_is_exempt(tmp_repo):
    """A turn ending at an explicitly user-gated remainder is a legitimate stop — exempt from
    telemetry entirely, and never blocked."""
    text = GRADEA_LINE + SUBSTANTIVE + (
        " The remaining item stays yours to do later — it is gated on your dashboard approval."
    )
    out = _run_guard(tmp_repo, [_user(HUMAN_PROMPT), _assistant(text)])
    assert '"decision":"block"' not in out, f"guard must never block (T-143): {out}"
    assert "stop-violation" not in _violations_log_text(tmp_repo), (
        "user-gated stop must not be logged as a stop-violation"
    )


@pytest.mark.parametrize(
    "first_line",
    [
        "*Enhanced: no change — slash-command turn, ran as-is*",
        "*Enhanced: no change — continuation, nothing to strengthen*",
    ],
)
def test_trivial_first_line_variants_exempt(tmp_repo, first_line):
    """The trivial regex accepts natural 'no change — …' / 'ran as-is' wording (was too narrow)."""
    body = first_line + "\n" + "Applied the rename across both call sites and verified. " * 6
    body = body[:560]
    assert 300 <= len(body) < 600
    out = _run_guard(tmp_repo, [_user(HUMAN_PROMPT), _assistant(body)])
    assert '"decision":"block"' not in out, f"guard must never block (T-143): {out}"


def test_hub_and_core_guard_identical():
    assert HOOK.read_text(encoding="utf-8") == CORE_HOOK.read_text(encoding="utf-8"), (
        "hub and core no-overask-guard.sh must stay byte-identical (dual-home synced tier)"
    )


def test_plugin_guard_uses_submission_extraction():
    """The plugin's enhance-process-guard must carry the same submission-run fix (no tail -1
    on the exemption path)."""
    text = PLUGIN_GUARD.read_text(encoding="utf-8")
    assert "Stop hook feedback:" in text and "last_sub" in text, (
        "plugin guard missing the final-user-submission extraction (issue #331)"
    )


def test_neither_guard_source_contains_a_block_emission():
    """T-143 static lock: no guard may contain a live {"decision":"block"} code path."""
    import re

    for name, fp in [("hub", HOOK), ("core", CORE_HOOK), ("plugin", PLUGIN_GUARD)]:
        body = fp.read_text(encoding="utf-8")
        assert 'decision:"block"' not in re.sub(r"\s+", "", body), (
            f"{name} guard still contains a live block emission — must be telemetry-only (T-143)"
        )
