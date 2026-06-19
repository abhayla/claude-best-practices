"""Phase 3.2 — governance prose → harness: assert the deterministic deny rules ship.

`decision-authority.md` lists irreversible/destructive actions as advisory prose.
This test pins the *harness* slice: the git-gate-bypass class that
`git-collaboration.md` forbids (force-push, --no-verify) MUST be encoded as
`permissions.deny` rules in BOTH the distributable template (`core/.claude/`)
and the hub's own config (`.claude/`), so a forgotten prose rule is *blocked*,
not just discouraged.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# The git-gate-bypass invocations that MUST be denied (map to git-collaboration.md
# "MUST NOT use --no-verify" + "MUST NOT force-push main").
REQUIRED_DENY = [
    "Bash(git push --force:*)",
    "Bash(git push -f:*)",
    "Bash(git push --no-verify:*)",
    "Bash(git commit --no-verify:*)",
    "Bash(git commit -n:*)",
]

SETTINGS_FILES = [
    REPO_ROOT / "core" / ".claude" / "settings.json",   # distributable template
    REPO_ROOT / ".claude" / "settings.json",            # hub dogfoods its own rules
]


@pytest.mark.parametrize("settings_path", SETTINGS_FILES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_irreversible_action_deny_rules_present(settings_path):
    assert settings_path.exists(), f"missing {settings_path}"
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    deny = data.get("permissions", {}).get("deny", [])
    missing = [r for r in REQUIRED_DENY if r not in deny]
    assert missing == [], (
        f"{settings_path.relative_to(REPO_ROOT)} is missing required deny rules "
        f"(Phase 3.2 governance-harness): {missing}"
    )


def test_decision_authority_documents_harness_layer():
    """decision-authority.md must point prose → harness (the deny rules + Auto mode)."""
    body = (REPO_ROOT / "core" / ".claude" / "rules" / "decision-authority.md").read_text(encoding="utf-8")
    assert "Harness enforcement" in body
    assert "permissions.deny" in body
    assert "--no-verify" in body and "--force" in body
