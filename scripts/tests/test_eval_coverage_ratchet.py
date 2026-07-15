"""The eval-coverage RATCHET (--enforce mode of check_eval_coverage.py, owner-approved
2026-07-13).

Pins: (1) a changed non-grandfathered skill without evals/ BLOCKS (exit 1, ::error::);
(2) a grandfathered skill only warns (exit 0); (3) a covered skill passes; (4) default
mode (no --enforce) stays advisory; (5) every grandfather entry is a real core skill that
still lacks evals — entries whose skill gained evals or vanished MUST be pruned
(shrink-only ratchet); (6) validate-pr.yml runs the gate with --enforce.
"""

from pathlib import Path

import scripts.check_eval_coverage as cec

ROOT = Path(__file__).resolve().parent.parent.parent


def _skill(tmp_root: Path, name: str, with_eval: bool) -> str:
    d = tmp_root / "core" / ".claude" / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\n---\nbody\n", encoding="utf-8")
    if with_eval:
        (d / "evals").mkdir()
        (d / "evals" / "report.md").write_text("eval report\n", encoding="utf-8")
    return f"core/.claude/skills/{name}/SKILL.md"


def _grandfather(tmp_root: Path, names: list):
    cfg = tmp_root / "config"
    cfg.mkdir(exist_ok=True)
    body = "grandfathered:\n" + "".join(f"  - {n}\n" for n in names)
    (cfg / "eval-coverage-grandfather.yml").write_text(body, encoding="utf-8")


def _run(monkeypatch, tmp_root: Path, changed: list, enforce: bool) -> int:
    """Exercise the gate's decision logic against a synthetic tree (the git/base plumbing
    is exercised by the real CI run; here we pin the enforce/grandfather semantics)."""
    uncovered = cec.uncovered_changed_skills(changed, tmp_root)
    grandfathered = cec._grandfathered(tmp_root) if enforce else set()
    blocking = [i for i in uncovered if enforce and i["skill"] not in grandfathered]
    return 1 if blocking else 0


def test_non_grandfathered_uncovered_blocks(tmp_path, monkeypatch):
    changed = [_skill(tmp_path, "new-skill", with_eval=False)]
    _grandfather(tmp_path, ["some-other-skill"])
    assert _run(monkeypatch, tmp_path, changed, enforce=True) == 1


def test_grandfathered_uncovered_warns_only(tmp_path, monkeypatch):
    changed = [_skill(tmp_path, "old-skill", with_eval=False)]
    _grandfather(tmp_path, ["old-skill"])
    assert _run(monkeypatch, tmp_path, changed, enforce=True) == 0


def test_covered_skill_passes(tmp_path, monkeypatch):
    changed = [_skill(tmp_path, "good-skill", with_eval=True)]
    _grandfather(tmp_path, [])
    assert _run(monkeypatch, tmp_path, changed, enforce=True) == 0


def test_default_mode_stays_advisory(tmp_path, monkeypatch):
    changed = [_skill(tmp_path, "new-skill", with_eval=False)]
    assert _run(monkeypatch, tmp_path, changed, enforce=False) == 0


def test_grandfather_entries_are_real_and_still_uncovered():
    names = cec._grandfathered(ROOT)
    assert names, "grandfather list must exist and be non-empty at introduction"
    skills = ROOT / "core" / ".claude" / "skills"
    for n in sorted(names):
        d = skills / n
        assert d.is_dir(), f"grandfather entry '{n}' is not a core skill — prune it"
        evals = d / "evals"
        has = evals.exists() and (any(evals.glob("*.md")) or any(evals.rglob("*.json")))
        assert not has, f"'{n}' now HAS evals — remove it from the grandfather list (shrink-only)"


def test_gate_wired_with_enforce():
    wf = (ROOT / ".github" / "workflows" / "validate-pr.yml").read_text(encoding="utf-8")
    assert "check_eval_coverage.py --enforce" in wf


class TestReferenceSkillExemption:
    """`type: reference` skills (lookup docs / #346 thin plugin pointers) need no evals —
    but only genuine reference skills are exempt; workflow skills still ratchet."""

    def _mk_skill(self, tmp_path, name, skill_type):
        d = tmp_path / "core" / ".claude" / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ntype: {skill_type}\nversion: \"1.0.0\"\n---\n\n# {name}\n",
            encoding="utf-8",
        )
        return d

    def test_reference_skill_is_exempt(self, tmp_path):
        from scripts.check_eval_coverage import uncovered_changed_skills

        self._mk_skill(tmp_path, "some-pointer", "reference")
        changed = ["core/.claude/skills/some-pointer/SKILL.md"]
        assert uncovered_changed_skills(changed, tmp_path) == []

    def test_workflow_skill_still_ratchets(self, tmp_path):
        from scripts.check_eval_coverage import uncovered_changed_skills

        self._mk_skill(tmp_path, "some-workflow", "workflow")
        changed = ["core/.claude/skills/some-workflow/SKILL.md"]
        flagged = uncovered_changed_skills(changed, tmp_path)
        assert [f["skill"] for f in flagged] == ["some-workflow"]
