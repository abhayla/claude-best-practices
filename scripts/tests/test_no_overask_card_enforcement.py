"""Regression guard for the prompt-auto-enhance reviewer-grade-card enforcement.

Root cause this pins (investigated 2026-06-18): the #106 grade-card Stop-hook check only
fired when a MALFORMED card was rendered (`self-after` column present but `reviewer-after`
absent). The realistic failure mode is TOTAL OMISSION — a compact "what changed / final
prompt" block with no card at all — which has no `self-after` token, so the check was skipped
and the full independent-reviewer grade card went unenforced (the user's "it's not working").

Why tests missed it: the prior guard had no test exercising the card-ABSENT path; the only
signal asserted was the malformed-card token pair. This test fails if the enforcement narrows
back to detecting only a malformed card, or stops covering the total-omission case.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CORE_HOOK = ROOT / "core" / ".claude" / "hooks" / "no-overask-guard.sh"
HUB_HOOK = ROOT / ".claude" / "hooks" / "no-overask-guard.sh"
REGISTRY = ROOT / "registry" / "patterns.json"


def _body() -> str:
    return CORE_HOOK.read_text(encoding="utf-8")


def test_hook_present_in_core_and_hub():
    assert CORE_HOOK.exists() and HUB_HOOK.exists()


def test_hub_copy_matches_core():
    assert HUB_HOOK.read_text(encoding="utf-8") == _body(), "hub no-overask hook drifted from core"


def test_card_enforcement_covers_total_omission():
    body = _body()
    # The enforcement trigger MUST recognise a strengthened-prompt block by the
    # compact-block tokens too (final prompt / what changed), not only a "self-after"
    # card column — otherwise total omission of the card is invisible (the original hole).
    assert re.search(r'grep -qE "self-after\|final prompt\|what changed"', body), (
        "card-presence trigger must include 'final prompt'/'what changed', not only 'self-after' "
        "(total card omission would otherwise go unenforced)"
    )


def test_card_enforcement_blocks_on_missing_reviewer_column():
    body = _body()
    # Still gates on the absence of the independent reviewer's per-dimension column.
    assert 'grep -qE "reviewer-after"' in body, "must detect the Reviewer-after column"
    assert '"decision":"block"' in body.replace(" ", "") or "decision:\"block\"" in body, (
        "card check must emit a blocking decision when the reviewer card is missing"
    )


def test_card_enforcement_exempts_trivial_turns():
    body = _body()
    assert "ran (your )?input as-is|ran as-is|no change" in body, (
        "trivial 'ran as-is' turns must be exempt from the card requirement"
    )


def test_registry_hash_in_sync():
    content = CORE_HOOK.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in content.splitlines()]
    norm = re.sub(r"  +", " ", "\n".join(lines))
    actual = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert reg["no-overask-guard"]["type"] == "hook"
    assert reg["no-overask-guard"]["hash"] == actual, (
        "no-overask-guard registry hash drifted from the file — resync it"
    )
