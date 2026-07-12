"""Behavioral regression tests for the no-overask-guard Stop hook's slash/origin exemption
(issue #331 — live false-block repro, session 889094c3 2026-07-12).

The harness writes a slash invocation as TWO consecutive user entries: the <command-name>
marker entry AND the fully-expanded command BODY as a separate marker-less plain-text entry.
The guard used to inspect only the LAST user entry (`tail -1`), saw the marker-less body, and
false-blocked slash turns ("enhance: full process not rendered" on /init). After a block, the
"Stop hook feedback:" entry became the last entry, stripping the origin again → double-block.

These tests run the real bash hook against synthetic transcript fixtures in an isolated tmp
git repo (so its counters/telemetry never touch the real .claude/ state) and pin:
  1. two-entry slash submission (marker + expanded body) → exempt, no block
  2. plain human prompt with no card → still BLOCKED (enforcement not weakened)
  3. stop-feedback retry turn after a slash turn → origin inherited, still exempt
  4. stop-feedback retry turn after a HUMAN turn → still blocked (feedback-skip is not a hole)
  5. trivial "no change — …/ran as-is" first-line variants → exempt (regex was too narrow)
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


def test_two_entry_slash_submission_is_exempt(tmp_repo):
    """Marker entry + expanded-body entry (the /init shape) must NOT be card-blocked."""
    out = _run_guard(
        tmp_repo,
        [_user(SLASH_MARKER), _attachment(), _user(SLASH_BODY), _assistant(SUBSTANTIVE)],
    )
    assert '"decision":"block"' not in out, f"slash turn false-blocked: {out}"


def test_human_prompt_without_card_still_blocked(tmp_repo):
    """Control: the fix must not weaken enforcement on genuine human turns."""
    out = _run_guard(tmp_repo, [_user(HUMAN_PROMPT), _assistant(SUBSTANTIVE)])
    assert '"decision":"block"' in out and "full process not rendered" in out


def test_stop_feedback_retry_inherits_slash_origin(tmp_repo):
    """After a block, the feedback entry must not strip the slash exemption (double-block bug)."""
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
    assert '"decision":"block"' not in out, f"slash retry turn false-blocked: {out}"


def test_stop_feedback_retry_after_human_prompt_still_blocked(tmp_repo):
    """Walking back past feedback entries must land on the HUMAN prompt, keeping enforcement."""
    out = _run_guard(
        tmp_repo,
        [
            _user(HUMAN_PROMPT),
            _assistant(SUBSTANTIVE),
            _user(STOP_FEEDBACK),
            _assistant(SUBSTANTIVE),
        ],
    )
    assert '"decision":"block"' in out


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
    assert '"decision":"block"' not in out, f"trivial variant false-blocked: {out}"


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
