"""Guard for T-209: GitHub's [skip ci] marker matches ANYWHERE in a commit
message (headline or body) — there is no safe placement for a push that
still needs CI. Measured on PR #580 (2026-08-19): a marker as the last line
of the commit BODY (headline clean) produced ZERO workflow runs and left the
PR permanently BLOCKED with no required check to report.

The T-191-era fix mistakenly believed the marker was safe in the body as
long as it avoided the headline. This test fails if the fleet's own
guidance regresses to that false claim, or drops the corrected claim /
PR #580 evidence citation.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

SKILL_MD = REPO / ".claude/skills/get-work-done/SKILL.md"
DISPATCHER_PLAN = REPO / "plans/get-work-done-dispatcher.md"


# T-371 (SKILL.md v0.10, 2026-08-27): the skill split into PROCEDURE (SKILL.md) + verbatim
# INCIDENT NARRATIVES (references/incident-log.md). The corrected RULE stays in SKILL.md; the
# PR #580 / #577 / #579 EVIDENCE lives in the log. Evidence assertions read the package, the
# false-claim guard still reads each file on its own (a regression anywhere is a failure).
def _package(path: Path) -> str:
    if path != SKILL_MD:
        return path.read_text(encoding="utf-8")
    refs = sorted((SKILL_MD.parent / "references").glob("*.md"))
    parts = [SKILL_MD.read_text(encoding="utf-8")]
    parts += [r.read_text(encoding="utf-8") for r in refs]
    return (chr(10)).join(parts)

# A commit message that would only avoid the marker in the *headline*,
# while implying the body is a safe place to put it, is the exact false
# claim T-209 corrected.
FALSE_SAFETY_CLAIM = re.compile(
    r"body[^.]{0,80}(is safe|never (triggers|suppress)|does not suppress)",
    re.IGNORECASE,
)


@pytest.mark.parametrize("path", [SKILL_MD, DISPATCHER_PLAN])
def test_skip_ci_guidance_does_not_claim_body_is_safe(path):
    body = path.read_text(encoding="utf-8")
    match = FALSE_SAFETY_CLAIM.search(body)
    assert match is None, (
        f"{path} still claims the [skip ci] marker is safe in the commit body — "
        f"FALSE per the PR #580 experiment (2026-08-19), matched: {match.group(0)!r}"
    )


@pytest.mark.parametrize("path", [SKILL_MD, DISPATCHER_PLAN])
def test_skip_ci_guidance_states_marker_matches_anywhere(path):
    body = path.read_text(encoding="utf-8")
    assert "anywhere" in body.lower(), (
        f"{path} must state the marker is matched ANYWHERE in the commit message "
        "(headline or body), not just the headline"
    )
    assert "headline" in body.lower() and "body" in body.lower(), (
        f"{path} must explicitly name both the headline and the body when "
        "describing where the marker can/cannot appear"
    )


@pytest.mark.parametrize("path", [SKILL_MD, DISPATCHER_PLAN])
def test_skip_ci_guidance_cites_pr_580_evidence(path):
    body = _package(path)
    assert "#580" in body, (
        f"{path} must cite the PR #580 experiment as evidence for the corrected rule"
    )


def test_skip_ci_guidance_states_required_check_consequence():
    body = _package(SKILL_MD)
    assert "REQUIRED" in body or "required" in body, (
        "SKILL.md must explain that a required status check never reporting "
        "leaves the PR permanently blocked — the consequence that makes this urgent"
    )
    assert "577" in body and "579" in body, (
        "SKILL.md must cite the T-191 incident PRs (#577/#579) this rule is meant to prevent"
    )
