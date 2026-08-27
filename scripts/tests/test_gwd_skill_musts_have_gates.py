"""T-370 dod item 3: MUST<->gate manifest.

Every `MUST`/`MUST NOT` bullet in .claude/skills/get-work-done/SKILL.md's CRITICAL
RULES block should carry a trailing `gate:<id>` token that resolves into
config/gwd-gates.yml (id -> script + exit code, or a test name). A bullet with no
gate: token is only acceptable up to the shrink-only ceiling in
config/gwd-skill-conformance-grandfather.yml (`max_ungated_musts`) — those are
implicitly `gate:PROSE-ONLY`. Wiring the remaining MUSTs to real gates is T-371;
this test just proves the count never grows and no cited id is unknown.
"""
from pathlib import Path

import scripts.gwd_skill_conformance as gc

HUB = Path(__file__).resolve().parents[2]


def _skill_text():
    return gc.load_skill_text(HUB)


def test_critical_rules_block_has_must_bullets():
    entries = gc.must_gate_tokens(_skill_text())
    assert len(entries) >= 1, "CRITICAL RULES block should contain MUST/MUST NOT bullets"


def test_gates_manifest_exists_with_prose_only_placeholder():
    gates = gc.load_gates(HUB)
    assert gates, "config/gwd-gates.yml must exist and define at least one gate"
    assert "PROSE-ONLY" in gates, (
        "config/gwd-gates.yml must define the PROSE-ONLY placeholder gate for "
        "grandfathered ungated MUSTs"
    )


def test_every_cited_gate_id_resolves():
    gates = gc.load_gates(HUB)
    entries = gc.must_gate_tokens(_skill_text())
    unknown = sorted({e["gate"] for e in entries if e["gate"] and e["gate"] not in gates})
    assert not unknown, f"MUST bullet(s) cite gate:<id> not defined in config/gwd-gates.yml: {unknown}"


def test_ungated_must_count_never_exceeds_grandfathered_ceiling():
    entries = gc.must_gate_tokens(_skill_text())
    ungated = sum(1 for e in entries if e["gate"] is None)
    grandfather = gc.load_grandfather(HUB)
    ceiling = grandfather.get("max_ungated_musts")
    assert ceiling is not None, (
        "config/gwd-skill-conformance-grandfather.yml must seed max_ungated_musts "
        "(shrink-only ratchet)"
    )
    assert ungated <= ceiling, (
        f"SKILL.md has {ungated} MUST/MUST NOT bullets with no gate:<id> token, over "
        f"the shrink-only ceiling of {ceiling} "
        f"(config/gwd-skill-conformance-grandfather.yml max_ungated_musts)"
    )
