"""Phase 5.1b — tests for the discovery -> GitHub issue selection logic.

Covers the *pure* migratable-filter (the load-bearing decision) + dry-run safety.
The `gh`-backed create/comment path is intentionally not exercised here (no network
in unit tests); dry-run is asserted to make ZERO gh calls.
"""

from scripts.discovery_to_issue import (
    select_migratable,
    migratable_signature,
    file_issues,
    issue_labels,
    migration_plan,
    _issue_body,
    AGENT_READY_LABEL,
    MIGRATABLE_MIN_CONFIDENCE,
)


def _entry(**kw):
    base = {
        "name": "native-thing", "type": "skill", "status": "pending",
        "confidence": 90, "source_trust": "high", "seen_count": 1,
        "sources": ["https://code.claude.com/docs/en/whats-new"],
    }
    base.update(kw)
    return base


NEVER_IN_REGISTRY = lambda name: False
ALWAYS_IN_REGISTRY = lambda name: True


def test_selects_a_confident_official_new_pattern():
    data = {"discoveries": [_entry()]}
    got = select_migratable(data, registry_check=NEVER_IN_REGISTRY)
    assert len(got) == 1 and got[0]["name"] == "native-thing"


def test_excludes_low_confidence():
    data = {"discoveries": [_entry(confidence=MIGRATABLE_MIN_CONFIDENCE - 1)]}
    assert select_migratable(data, registry_check=NEVER_IN_REGISTRY) == []


def test_excludes_low_trust():
    data = {"discoveries": [_entry(source_trust="low")]}
    assert select_migratable(data, registry_check=NEVER_IN_REGISTRY) == []


def test_excludes_non_pending():
    data = {"discoveries": [_entry(status="imported"), _entry(status="rejected")]}
    assert select_migratable(data, registry_check=NEVER_IN_REGISTRY) == []


def test_excludes_unknown_type():
    data = {"discoveries": [_entry(type="unknown")]}
    assert select_migratable(data, registry_check=NEVER_IN_REGISTRY) == []


def test_excludes_already_in_registry():
    """The whole point: don't file issues for patterns the hub already has."""
    data = {"discoveries": [_entry()]}
    assert select_migratable(data, registry_check=ALWAYS_IN_REGISTRY) == []


def test_empty_discoveries_is_safe():
    assert select_migratable({}, registry_check=NEVER_IN_REGISTRY) == []
    assert select_migratable({"discoveries": []}, registry_check=NEVER_IN_REGISTRY) == []


def test_signature_is_stable_and_typed():
    e = _entry(name="sub-agents-nesting", type="rule")
    assert migratable_signature(e) == "discovery:rule:sub-agents-nesting"


def test_issue_labels_marks_agent_ready():
    """S11: a migratable discovery is a ready-to-act item — must carry the agent label."""
    labels = issue_labels(_entry(type="agent"))
    assert AGENT_READY_LABEL in labels
    assert "discovery" in labels
    assert "discovery-type-agent" in labels


def test_migration_plan_is_executable_not_vague():
    """The plan must give concrete, decidable steps — not a bare 'evaluate this'."""
    plan = migration_plan(_entry(name="native-loop", type="skill"))
    # Names the discovery, the three adoption shapes, and the safety defaults.
    assert "native-loop" in plan
    for token in ("Adopt-by-pointer", "Migrate a hand-rolled", "Reject", "FULL local CI"):
        assert token in plan, f"migration plan missing decidable step: {token}"
    assert "default" in plan.lower(), "plan must preserve the keep-default-unchanged safety rule"


def test_issue_body_embeds_plan_and_dedup_marker():
    e = _entry(name="native-loop", type="skill")
    body = _issue_body(e)
    assert "Migration plan (agent-ready)" in body
    assert migratable_signature(e) in body  # dedup still intact after enrichment


def test_dry_run_makes_no_gh_calls_and_reports_plan(monkeypatch):
    # Spy: dry-run must NEVER invoke gh (the cron-safety guarantee). Fail loudly if it does.
    import scripts.discovery_to_issue as mod

    def _boom(*a, **k):
        raise AssertionError("dry-run must not call gh")

    monkeypatch.setattr(mod, "_gh", _boom)
    cands = [_entry(), _entry(name="another", type="agent")]
    report = file_issues(cands, apply=False)
    assert report["applied"] is False
    assert report["candidates"] == 2
    assert all(a["action"] == "DRY_RUN" for a in report["actions"])
