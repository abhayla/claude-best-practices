"""Guard for S9: the native security-guidance plugin + /security-review are
documented as additive opt-in layers in the Security role (2026-06-20)."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROLES = REPO / "core/.claude/rules/engineering-roles.md"


def test_security_guidance_documented_as_additive():
    body = ROLES.read_text(encoding="utf-8")
    assert "security-guidance" in body, "native security-guidance plugin not referenced"
    assert "/security-review" in body, "native /security-review not referenced"
    # Must be framed as ADDITIVE, not a replacement of existing security tooling.
    assert "additive opt-in" in body, (
        "the native plugin must be framed as additive, not a replacement"
    )


def test_existing_security_tooling_preserved():
    """The adoption must not drop the hub's existing security chain."""
    body = ROLES.read_text(encoding="utf-8")
    for token in ("/security-audit", "security-auditor-agent", "/supply-chain-audit"):
        assert token in body, f"existing security tool {token} was dropped"
